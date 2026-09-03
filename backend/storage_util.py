"""AO-360 Object Storage + Photo processing (bagian 43a, 45, 46).
Watermark otomatis, kompresi, konversi HEIC->JPEG, ekstraksi EXIF + fallback.
"""
import io
import os
import uuid
from datetime import datetime, timezone

import requests
from PIL import Image, ImageDraw, ImageFont, ExifTags

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_OK = True
except Exception:
    HEIC_OK = False

STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = os.environ.get("APP_NAME", "ao360")

_storage_key = None


def init_storage(force: bool = False):
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    return _storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                        headers={"X-Storage-Key": key, "Content-Type": content_type},
                        data=data, timeout=120)
    if resp.status_code == 404:
        key = init_storage(force=True)
        resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key, "Content-Type": content_type},
                            data=data, timeout=120)
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    key = init_storage()
    resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                        headers={"X-Storage-Key": key}, timeout=60)
    if resp.status_code == 404:
        key = init_storage(force=True)
        resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": key}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "image/jpeg")


def _get_font(size: int):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def extract_exif(img: Image.Image):
    """Return dict {tanggal_foto, timestamp_foto, latitude, longitude, exif_available}."""
    result = {"tanggal_foto": None, "timestamp_foto": None,
              "latitude": None, "longitude": None, "exif_available": False}
    try:
        exif = img._getexif()
    except Exception:
        exif = None
    if not exif:
        return result

    tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    dt = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
    if dt:
        try:
            parsed = datetime.strptime(str(dt), "%Y:%m:%d %H:%M:%S")
            result["timestamp_foto"] = parsed.replace(tzinfo=timezone.utc).isoformat()
            result["tanggal_foto"] = parsed.strftime("%Y-%m-%d")
            result["exif_available"] = True
        except Exception:
            pass

    gps = tag_map.get("GPSInfo")
    if gps:
        try:
            gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}

            def to_deg(v):
                d, m, s = v
                return float(d) + float(m) / 60.0 + float(s) / 3600.0

            if "GPSLatitude" in gps_tags and "GPSLongitude" in gps_tags:
                lat = to_deg(gps_tags["GPSLatitude"])
                if gps_tags.get("GPSLatitudeRef") == "S":
                    lat = -lat
                lon = to_deg(gps_tags["GPSLongitude"])
                if gps_tags.get("GPSLongitudeRef") == "W":
                    lon = -lon
                result["latitude"] = round(lat, 6)
                result["longitude"] = round(lon, 6)
                result["exif_available"] = True
        except Exception:
            pass
    return result


def process_photo(raw: bytes, filename: str, pic_name: str, activity_date: str,
                  gps_lat=None, gps_lon=None):
    """Konversi HEIC, ekstrak EXIF, kompresi, watermark. Return (jpeg_bytes, meta)."""
    img = Image.open(io.BytesIO(raw))
    meta = extract_exif(img)

    # GPS dari client (browser) menang jika EXIF tak ada
    lat = meta["latitude"] if meta["latitude"] is not None else gps_lat
    lon = meta["longitude"] if meta["longitude"] is not None else gps_lon

    now_iso = datetime.now(timezone.utc).isoformat()
    if not meta["exif_available"] or not meta["timestamp_foto"]:
        meta["timestamp_foto"] = now_iso
        meta["tanggal_foto"] = meta["tanggal_foto"] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        meta["waktu_upload_fallback"] = True
    else:
        meta["waktu_upload_fallback"] = False

    meta["latitude"] = round(float(lat), 6) if lat is not None else None
    meta["longitude"] = round(float(lon), 6) if lon is not None else None

    # status validasi (bagian 46)
    if meta["latitude"] is None or meta["longitude"] is None:
        meta["status_validasi"] = "Lokasi Tidak Tersedia"
    elif meta["exif_available"] and meta["tanggal_foto"] and activity_date and meta["tanggal_foto"] != activity_date:
        meta["status_validasi"] = "Perlu Verifikasi Admin"
    else:
        meta["status_validasi"] = "Valid"

    # convert & resize
    img = img.convert("RGB")
    max_dim = 1600
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)))

    # watermark (bagian 45)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    ts = datetime.fromisoformat(meta["timestamp_foto"])
    lines = [
        "PT BPRS HAJI MISKIN",
        "Collection Activity",
        f"Tanggal: {ts.strftime('%d-%m-%Y')}  Jam: {ts.strftime('%H:%M')} WIB",
        f"PIC: {pic_name}",
    ]
    if meta["latitude"] is not None:
        lines.append(f"Lokasi: {meta['latitude']}, {meta['longitude']}")
    else:
        lines.append("Lokasi: Tidak tersedia")

    fsize = max(14, int(w * 0.022))
    font = _get_font(fsize)
    pad = int(fsize * 0.5)
    line_h = fsize + int(fsize * 0.35)
    box_h = line_h * len(lines) + pad * 2
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, h - box_h, w, h], fill=(4, 78, 55, 180))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    y = h - box_h + pad
    for i, ln in enumerate(lines):
        color = (245, 200, 90) if i == 0 else (255, 255, 255)
        draw.text((pad, y), ln, font=font, fill=color)
        y += line_h

    # compress
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82, optimize=True)
    return out.getvalue(), meta


def upload_photo(raw: bytes, filename: str, user_id: str, pic_name: str,
                 activity_date: str, gps_lat=None, gps_lon=None):
    jpeg, meta = process_photo(raw, filename, pic_name, activity_date, gps_lat, gps_lon)
    path = f"{APP_NAME}/collection/{user_id}/{uuid.uuid4()}.jpg"
    put_object(path, jpeg, "image/jpeg")
    meta["foto_url"] = path
    return meta

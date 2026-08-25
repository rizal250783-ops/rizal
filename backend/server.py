import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Annotated

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict, field_validator
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from emails import send_email, reminder_html, EmailNotConfigured, EmailDeliveryError

load_dotenv()

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "")
OWNER_WHATSAPP = os.environ.get("OWNER_WHATSAPP", "")

WIB = timezone(timedelta(hours=7))

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="ROSADAH KOST API")
api = app  # placeholder

from fastapi import APIRouter
router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Models -----------------
def _to_str(v):
    if isinstance(v, ObjectId):
        return str(v)
    return v


PyObjectId = Annotated[str, BeforeValidator(_to_str)]


def now_wib_iso():
    return datetime.now(WIB).isoformat()


def to_oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")


# ----------------- Seed -----------------
SEED_LOCATIONS = [
    {"nama": "Kost Kampung Bali XXV", "alamat": "Jalan Kampung Bali XXV No. 14A", "jumlah_kamar": 15},
    {"nama": "Kost Kampung Bali VII", "alamat": "Jalan Kampung Bali VII No. 2", "jumlah_kamar": 15},
    {"nama": "Kost Kampung Bali XI", "alamat": "Jalan Kampung Bali XI No. 2", "jumlah_kamar": 27},
    {"nama": "Kost Kota Bambu Utara", "alamat": "Jalan Kota Bambu Utara No. 10", "jumlah_kamar": 5},
]

# Billing starts September 2026
BILLING_START = "2026-09"


def current_billing_month() -> str:
    now = datetime.now(WIB)
    cur = f"{now.year:04d}-{now.month:02d}"
    return cur if cur > BILLING_START else BILLING_START


async def seed_data():
    count = await db.locations.count_documents({})
    if count > 0:
        return
    for loc in SEED_LOCATIONS:
        res = await db.locations.insert_one({"nama": loc["nama"], "alamat": loc["alamat"]})
        loc_id = res.inserted_id
        rooms = []
        for i in range(1, loc["jumlah_kamar"] + 1):
            rooms.append({
                "location_id": loc_id,
                "nomor_kamar": str(i),
                "status": "kosong",
                "tenant_id": None,
            })
        if rooms:
            await db.rooms.insert_many(rooms)
    # settings with seeded logo
    settings = await db.settings.find_one({"key": "app"})
    if not settings:
        logo_data = ""
        try:
            with open(os.path.join(os.path.dirname(__file__), "logo_seed.txt")) as f:
                logo_data = f.read().strip()
        except Exception:
            logo_data = ""
        await db.settings.insert_one({
            "key": "app",
            "logo": logo_data,
            "nama_app": "ROSADAH KOST",
            "owner_email": OWNER_EMAIL,
            "owner_whatsapp": OWNER_WHATSAPP,
        })


@app.on_event("startup")
async def on_startup():
    await seed_data()
    # ensure settings exists even if locations were seeded before
    if not await db.settings.find_one({"key": "app"}):
        logo_data = ""
        try:
            with open(os.path.join(os.path.dirname(__file__), "logo_seed.txt")) as f:
                logo_data = f.read().strip()
        except Exception:
            pass
        await db.settings.insert_one({
            "key": "app", "logo": logo_data, "nama_app": "ROSADAH KOST",
            "owner_email": OWNER_EMAIL, "owner_whatsapp": OWNER_WHATSAPP,
        })


# ----------------- Helpers -----------------
async def next_receipt_number(period: str) -> str:
    res = await db.counters.find_one_and_update(
        {"_id": "receipt"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = res["seq"]
    return f"ROSADAH_KOST-{period}-{seq:05d}"


def loc_out(doc):
    return {"id": str(doc["_id"]), "nama": doc["nama"], "alamat": doc["alamat"]}


async def tenant_out(t):
    room = await db.rooms.find_one({"_id": t["room_id"]}) if t.get("room_id") else None
    location = None
    if room:
        location = await db.locations.find_one({"_id": room["location_id"]})
    return {
        "id": str(t["_id"]),
        "nama": t["nama"],
        "nomor_hp": t.get("nomor_hp", ""),
        "harga_sewa": t.get("harga_sewa", 0),
        "tanggal_jatuh_tempo": t.get("tanggal_jatuh_tempo", ""),
        "room_id": str(t["room_id"]) if t.get("room_id") else None,
        "nomor_kamar": room["nomor_kamar"] if room else None,
        "location_id": str(room["location_id"]) if room else (str(t["last_location_id"]) if t.get("last_location_id") else None),
        "lokasi": location["nama"] if location else (t.get("last_location_nama") or "-"),
        "alamat": location["alamat"] if location else (t.get("last_location_alamat") or "-"),
        "status": t.get("status", "aktif"),
    }


async def payment_out(p):
    t = await db.tenants.find_one({"_id": p["tenant_id"]})
    room = None
    location = None
    if t and t.get("room_id"):
        room = await db.rooms.find_one({"_id": t["room_id"]})
        if room:
            location = await db.locations.find_one({"_id": room["location_id"]})
    if not location and t and t.get("last_location_nama"):
        location = {"nama": t["last_location_nama"], "alamat": t.get("last_location_alamat", "-")}
    location_id = None
    if room:
        location_id = str(room["location_id"])
    elif t and t.get("last_location_id"):
        location_id = str(t["last_location_id"])
    return {
        "id": str(p["_id"]),
        "tenant_id": str(p["tenant_id"]),
        "nama": t["nama"] if t else "-",
        "nomor_hp": t.get("nomor_hp", "") if t else "",
        "nomor_kamar": (room["nomor_kamar"] if room else (p.get("nomor_kamar_snapshot") or "-")),
        "lokasi": location["nama"] if location else "-",
        "alamat": location["alamat"] if location else "-",
        "location_id": location_id,
        "tanggal_jatuh_tempo": (t.get("tanggal_jatuh_tempo", "") if t else ""),
        "bulan": p["bulan"],
        "jumlah": p["jumlah"],
        "status": p["status"],
        "tanggal_bayar": p.get("tanggal_bayar"),
        "nomor_kwitansi": p.get("nomor_kwitansi"),
    }


# ----------------- Schemas -----------------
class TenantCreate(BaseModel):
    room_id: str
    nama: str
    nomor_hp: str = ""
    harga_sewa: float = 0
    tanggal_jatuh_tempo: str = ""

    @field_validator("tanggal_jatuh_tempo")
    @classmethod
    def _valid_date(cls, v):
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Format tanggal harus yyyy-mm-dd")
        return v


class LogoUpdate(BaseModel):
    logo: str


# ----------------- Routes -----------------
@router.get("/")
async def root():
    return {"app": "ROSADAH KOST", "status": "ok"}


@router.get("/settings")
async def get_settings():
    s = await db.settings.find_one({"key": "app"})
    if not s:
        return {"logo": "", "nama_app": "ROSADAH KOST", "owner_email": OWNER_EMAIL, "owner_whatsapp": OWNER_WHATSAPP}
    return {
        "logo": s.get("logo", ""),
        "nama_app": s.get("nama_app", "ROSADAH KOST"),
        "owner_email": s.get("owner_email", OWNER_EMAIL),
        "owner_whatsapp": s.get("owner_whatsapp", OWNER_WHATSAPP),
    }


@router.put("/settings/logo")
async def update_logo(payload: LogoUpdate):
    await db.settings.update_one({"key": "app"}, {"$set": {"logo": payload.logo}}, upsert=True)
    return {"ok": True}


@router.get("/locations")
async def get_locations():
    out = []
    async for doc in db.locations.find():
        loc = loc_out(doc)
        total = await db.rooms.count_documents({"location_id": doc["_id"]})
        terisi = await db.rooms.count_documents({"location_id": doc["_id"], "status": "terisi"})
        loc.update({"total_kamar": total, "kamar_terisi": terisi, "kamar_kosong": total - terisi})
        out.append(loc)
    return out


@router.get("/locations/{location_id}/rooms")
async def get_location_rooms(location_id: str):
    oid = to_oid(location_id)
    loc = await db.locations.find_one({"_id": oid})
    if not loc:
        raise HTTPException(404, "Lokasi tidak ditemukan")
    rooms = []
    cursor = db.rooms.find({"location_id": oid}).sort("nomor_kamar", 1)
    docs = await cursor.to_list(length=1000)
    docs.sort(key=lambda r: int(r["nomor_kamar"]) if r["nomor_kamar"].isdigit() else 9999)
    for r in docs:
        item = {
            "id": str(r["_id"]),
            "nomor_kamar": r["nomor_kamar"],
            "status": r["status"],
            "tenant": None,
        }
        if r.get("tenant_id"):
            t = await db.tenants.find_one({"_id": r["tenant_id"]})
            if t:
                # latest payment status
                latest = await db.payments.find({"tenant_id": t["_id"]}).sort("bulan", -1).to_list(1)
                pstat = latest[0]["status"] if latest else "-"
                item["tenant"] = {
                    "id": str(t["_id"]),
                    "nama": t["nama"],
                    "nomor_hp": t.get("nomor_hp", ""),
                    "harga_sewa": t.get("harga_sewa", 0),
                    "tanggal_jatuh_tempo": t.get("tanggal_jatuh_tempo", ""),
                    "status_pembayaran": pstat,
                }
        rooms.append(item)
    total = len(docs)
    terisi = sum(1 for r in docs if r["status"] == "terisi")
    return {
        "lokasi": loc_out(loc),
        "total_kamar": total,
        "kamar_terisi": terisi,
        "kamar_kosong": total - terisi,
        "rooms": rooms,
    }


@router.post("/tenants")
async def create_tenant(payload: TenantCreate):
    room = await db.rooms.find_one({"_id": to_oid(payload.room_id)})
    if not room:
        raise HTTPException(404, "Kamar tidak ditemukan")
    if room["status"] == "terisi":
        raise HTTPException(400, "Kamar sudah terisi")
    location = await db.locations.find_one({"_id": room["location_id"]})
    tenant_doc = {
        "room_id": room["_id"],
        "nama": payload.nama,
        "nomor_hp": payload.nomor_hp,
        "harga_sewa": payload.harga_sewa,
        "tanggal_jatuh_tempo": payload.tanggal_jatuh_tempo,
        "status": "aktif",
        "created_at": now_wib_iso(),
        "last_location_id": room["location_id"],
        "last_location_nama": location["nama"] if location else "-",
        "last_location_alamat": location["alamat"] if location else "-",
    }
    res = await db.tenants.insert_one(tenant_doc)
    tenant_id = res.inserted_id
    await db.rooms.update_one({"_id": room["_id"]}, {"$set": {"status": "terisi", "tenant_id": tenant_id}})
    # create first payment
    period = current_billing_month()
    await db.payments.insert_one({
        "tenant_id": tenant_id,
        "bulan": period,
        "jumlah": payload.harga_sewa,
        "status": "tunggakan",
        "tanggal_bayar": None,
        "nomor_kwitansi": None,
        "nomor_kamar_snapshot": room["nomor_kamar"],
        "created_at": now_wib_iso(),
    })
    t = await db.tenants.find_one({"_id": tenant_id})
    return await tenant_out(t)


@router.get("/tenants")
async def list_tenants(search: Optional[str] = None, location_id: Optional[str] = None, include_archived: bool = False):
    query = {}
    if not include_archived:
        query["status"] = {"$ne": "arsip"}
    if search:
        query["nama"] = {"$regex": search, "$options": "i"}
    out = []
    async for t in db.tenants.find(query).sort("created_at", -1):
        item = await tenant_out(t)
        if location_id and item["location_id"] != location_id:
            continue
        out.append(item)
    return out


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    oid = to_oid(tenant_id)
    t = await db.tenants.find_one({"_id": oid})
    if not t:
        raise HTTPException(404, "Penghuni tidak ditemukan")
    if t.get("room_id"):
        await db.rooms.update_one({"_id": t["room_id"]}, {"$set": {"status": "kosong", "tenant_id": None}})
    await db.payments.delete_many({"tenant_id": oid})
    await db.tenants.delete_one({"_id": oid})
    return {"ok": True}


@router.post("/tenants/{tenant_id}/archive")
async def archive_tenant(tenant_id: str):
    oid = to_oid(tenant_id)
    t = await db.tenants.find_one({"_id": oid})
    if not t:
        raise HTTPException(404, "Penghuni tidak ditemukan")
    if t.get("room_id"):
        await db.rooms.update_one({"_id": t["room_id"]}, {"$set": {"status": "kosong", "tenant_id": None}})
    await db.tenants.update_one({"_id": oid}, {"$set": {"status": "arsip", "room_id": None}})
    return {"ok": True}


@router.post("/rooms/{room_id}/vacate")
async def vacate_room(room_id: str):
    room = await db.rooms.find_one({"_id": to_oid(room_id)})
    if not room:
        raise HTTPException(404, "Kamar tidak ditemukan")
    if room.get("tenant_id"):
        await db.tenants.update_one({"_id": room["tenant_id"]}, {"$set": {"room_id": None}})
    await db.rooms.update_one({"_id": room["_id"]}, {"$set": {"status": "kosong", "tenant_id": None}})
    return {"ok": True}


@router.get("/payments")
async def list_payments(status: Optional[str] = None, location_id: Optional[str] = None):
    archived = {str(t["_id"]) async for t in db.tenants.find({"status": "arsip"}, {"_id": 1})}
    out = []
    async for p in db.payments.find().sort([("bulan", -1), ("created_at", -1)]):
        if str(p["tenant_id"]) in archived:
            continue
        item = await payment_out(p)
        if status and status != "semua" and item["status"] != status:
            continue
        if location_id and item.get("location_id") != location_id:
            continue
        out.append(item)
    total_lunas = sum(i["jumlah"] for i in out if i["status"] == "lunas")
    total_tunggakan = sum(i["jumlah"] for i in out if i["status"] == "tunggakan")
    return {"payments": out, "total_lunas": total_lunas, "total_tunggakan": total_tunggakan}


@router.post("/payments/{payment_id}/toggle")
async def toggle_payment(payment_id: str):
    oid = to_oid(payment_id)
    p = await db.payments.find_one({"_id": oid})
    if not p:
        raise HTTPException(404, "Pembayaran tidak ditemukan")
    if p["status"] == "tunggakan":
        # mark lunas
        nomor = p.get("nomor_kwitansi")
        if not nomor:
            nomor = await next_receipt_number(p["bulan"])
            await db.receipts.insert_one({
                "payment_id": oid,
                "nomor_kwitansi": nomor,
                "created_at": now_wib_iso(),
            })
        await db.payments.update_one({"_id": oid}, {"$set": {
            "status": "lunas",
            "tanggal_bayar": now_wib_iso(),
            "nomor_kwitansi": nomor,
        }})
    else:
        await db.payments.update_one({"_id": oid}, {"$set": {
            "status": "tunggakan",
            "tanggal_bayar": None,
        }})
    p = await db.payments.find_one({"_id": oid})
    return await payment_out(p)


@router.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    p = await db.payments.find_one({"_id": to_oid(payment_id)})
    if not p:
        raise HTTPException(404, "Pembayaran tidak ditemukan")
    return await payment_out(p)


@router.get("/dashboard")
async def dashboard():
    period = current_billing_month()
    now = datetime.now(WIB)
    cur_month = f"{now.year:04d}-{now.month:02d}"
    total_rooms = await db.rooms.count_documents({})
    terisi = await db.rooms.count_documents({"status": "terisi"})
    kosong = total_rooms - terisi

    # income this month (lunas, billing period considered "bulan ini")
    pemasukan = 0
    total_tunggakan = 0
    perlu_perhatian = []
    penghuni_belum_bayar = set()
    archived = {str(t["_id"]) async for t in db.tenants.find({"status": "arsip"}, {"_id": 1})}
    async for p in db.payments.find():
        if str(p["tenant_id"]) in archived:
            continue
        item = await payment_out(p)
        if p["status"] == "lunas" and p["bulan"] == period:
            pemasukan += p["jumlah"]
        if p["status"] == "tunggakan":
            total_tunggakan += p["jumlah"]
            penghuni_belum_bayar.add(str(p["tenant_id"]))
            if p["bulan"] == period:
                perlu_perhatian.append({
                    "tenant_id": item["tenant_id"],
                    "nama": item["nama"],
                    "nomor_kamar": item["nomor_kamar"],
                    "lokasi": item["lokasi"],
                    "jumlah": item["jumlah"],
                    "bulan": item["bulan"],
                })

    persentase = round((terisi / total_rooms) * 100) if total_rooms else 0
    return {
        "periode": period,
        "total_pemasukan_bulan_ini": pemasukan,
        "kamar_terisi": terisi,
        "kamar_total": total_rooms,
        "kamar_kosong": kosong,
        "total_tunggakan": total_tunggakan,
        "jumlah_penghuni_belum_bayar": len(penghuni_belum_bayar),
        "persentase_hunian": persentase,
        "perlu_perhatian": perlu_perhatian,
        "owner_whatsapp": OWNER_WHATSAPP,
    }


@router.get("/reminders/status")
async def reminder_status():
    configured = bool(os.environ.get("SENDGRID_API_KEY", "").strip()) and bool(os.environ.get("SENDER_EMAIL", "").strip())
    return {"configured": configured, "owner_email": OWNER_EMAIL}


async def _tunggakan_items(period, only_payment_id=None):
    archived = {str(t["_id"]) async for t in db.tenants.find({"status": "arsip"}, {"_id": 1})}
    items = []
    query = {"status": "tunggakan"}
    if only_payment_id:
        query["_id"] = to_oid(only_payment_id)
    async for p in db.payments.find(query):
        if str(p["tenant_id"]) in archived:
            continue
        if not only_payment_id and p["bulan"] != period:
            continue
        item = await payment_out(p)
        items.append(item)
    return items


@router.post("/reminders/send")
async def send_reminder(payment_id: Optional[str] = None):
    period = current_billing_month()
    items = await _tunggakan_items(period, only_payment_id=payment_id)
    if not items:
        raise HTTPException(400, "Tidak ada tunggakan untuk dikirim.")
    subject = f"Pengingat Tunggakan Kost ROSADAH KOST - {len(items)} penghuni"
    html = reminder_html(items, items[0]["bulan"] if payment_id else period)
    try:
        send_email(OWNER_EMAIL, subject, html)
    except EmailNotConfigured as e:
        raise HTTPException(400, str(e))
    except EmailDeliveryError as e:
        raise HTTPException(502, str(e))
    return {"ok": True, "terkirim": len(items), "tujuan": OWNER_EMAIL}


app.include_router(router)

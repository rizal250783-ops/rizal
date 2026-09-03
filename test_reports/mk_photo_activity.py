import io, os, requests
from dotenv import dotenv_values
from PIL import Image

BASE = dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
s = requests.Session()
r = s.post(f"{BASE}/auth/login", json={"email": "rizky.lending@hajimiskin.co.id", "password": "Password123"})
print("login", r.status_code)
tok = r.json()["access_token"] if "access_token" in r.json() else r.json().get("token")
print("token?", bool(tok))
h = {"Authorization": f"Bearer {tok}"}
buf = io.BytesIO()
Image.new("RGB", (600, 400), (30, 120, 80)).save(buf, format="JPEG")
buf.seek(0)
data = {
    "tanggal_aktivitas": "2026-09-03",
    "jam_aktivitas": "11:00",
    "nomor_kontrak": "TEST_PHOTO_GALLERY",
    "nama_nasabah": "TEST Nasabah Photo",
    "outstanding_pokok": "7000000",
    "status_penagihan": "Berkomunikasi",
    "catatan": "gallery regression",
    "latitude": "-0.3",
    "longitude": "100.4",
}
r2 = s.post(f"{BASE}/collection-activities", data=data, files={"files": ("test.jpg", buf, "image/jpeg")}, headers=h)
print("create", r2.status_code, r2.text[:400])
# fetch list
r3 = s.get(f"{BASE}/collection-activities", headers=h, params={"period": "2026-09"})
print("list", r3.status_code)
for a in r3.json() if isinstance(r3.json(), list) else r3.json().get("items", []):
    print(a.get("nomor_kontrak"), a.get("id"), len(a.get("photos") or []), a.get("status_validasi") or a.get("overall_validation"))

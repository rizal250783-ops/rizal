from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
import uuid
import io
import bcrypt
import jwt
import openpyxl
from openpyxl.styles import Font, PatternFill
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

REGION_AREA_MAP = {}
_ra_path = ROOT_DIR / "region_area.json"
if _ra_path.exists():
    REGION_AREA_MAP = json.loads(_ra_path.read_text())

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

app = FastAPI()
api_router = APIRouter(prefix="/api")

STATUS_PERKARA = [
    "Gugatan Terdaftar", "Pemanggilan Relaas", "Mediasi", "Jawaban Tergugat",
    "Replik", "Duplik", "Pembuktian", "Kesimpulan", "Putusan",
    "Pemberitahuan Putusan", "Banding", "Putusan Banding", "Kasasi",
    "Putusan Kasasi", "Peninjauan Kembali", "Inkracht", "Eksekusi Jaminan",
    "Settlement / Perdamaian",
]

AGENDA_LIST = ["Mediasi", "Jawaban", "Replik", "Duplik", "Pembuktian", "Pemeriksaan Saksi",
               "Kesimpulan", "Putusan", "Banding", "Kasasi", "PK"]

DOKUMEN_KATEGORI = [
    "Executive Summary", "Relaas 1", "Relaas 2", "Relaas 3", "Replik", "Duplik",
    "Daftar Bukti Penggugat", "Daftar Bukti Tergugat", "Salinan Putusan",
    "Relaas Pemberitahuan Putusan", "Relaas Pemberitahuan Banding & Memori Banding",
    "Kontra Banding", "Relaas Pemberitahuan Putusan Banding",
    "Relaas Pemberitahuan Kasasi & Memori Kasasi", "Kontra Kasasi",
    "Relaas Pemberitahuan Putusan Kasasi", "Peninjauan Kembali (PK)",
]

RISK_RATINGS = ["High Risk", "Medium Risk", "Low Risk"]


# ---------------- Auth ----------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role,
               "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request):
    from fastapi import Request
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Tidak terautentikasi")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token kedaluwarsa")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    if not user.get("aktif", True):
        raise HTTPException(status_code=403, detail="Akun dinonaktifkan")
    return user


from fastapi import Request


async def auth_user(request: Request):
    return await get_current_user(request)


async def dept_head_only(user=Depends(auth_user)):
    if user["role"] != "dept_head":
        raise HTTPException(status_code=403, detail="Hanya Legal Litigation & Advice Manager")
    return user


@api_router.post("/auth/login")
async def login(body: dict):
    username = (body.get("username") or "").strip().lower()
    password = body.get("password") or ""
    now = datetime.now(timezone.utc)
    key = f"login:{username}"
    rec = await db.login_attempts.find_one({"_id": key})
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if user and verify_password(password, user["password_hash"]):
        if not user.get("aktif", True):
            raise HTTPException(status_code=403, detail="Akun dinonaktifkan. Hubungi Legal Litigation & Advice Manager.")
        await db.login_attempts.delete_one({"_id": key})
        token = create_token(user["id"], user["role"])
        user.pop("password_hash", None)
        return {"token": token, "user": user}
    if rec and rec.get("count", 0) >= 5 and now < datetime.fromisoformat(rec["locked_until"]):
        raise HTTPException(status_code=423, detail="Terlalu banyak percobaan login gagal. Akun terkunci sementara, coba lagi dalam 15 menit.")
    count = (rec or {}).get("count", 0) + 1
    await db.login_attempts.update_one({"_id": key},
        {"$set": {"count": count, "locked_until": (now + timedelta(minutes=15)).isoformat()}}, upsert=True)
    if count >= 5:
        raise HTTPException(status_code=423, detail="Terlalu banyak percobaan login gagal. Akun terkunci sementara, coba lagi dalam 15 menit.")
    raise HTTPException(status_code=401, detail="Username atau password salah")


@api_router.get("/auth/me")
async def me(user=Depends(auth_user)):
    return user


# ---------------- Users ----------------
@api_router.get("/users")
async def list_users(user=Depends(dept_head_only)):
    return await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)


@api_router.post("/users")
async def create_user(body: dict, user=Depends(dept_head_only)):
    username = (body.get("username") or "").strip().lower()
    password = body.get("password") or ""
    nama = (body.get("nama") or "").strip()
    if not username or not password or not nama:
        raise HTTPException(status_code=400, detail="Username, password, dan nama wajib diisi")
    if await db.users.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
    doc = {
        "id": str(uuid.uuid4()), "username": username, "nama": nama,
        "password_hash": hash_password(password), "role": "admin_legal",
        "aktif": True, "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    doc.pop("password_hash", None)
    doc.pop("_id", None)
    return doc


@api_router.patch("/users/{user_id}/status")
async def toggle_user(user_id: str, body: dict, user=Depends(dept_head_only)):
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if target["role"] == "dept_head":
        raise HTTPException(status_code=400, detail="Tidak dapat mengubah status Dept Head")
    await db.users.update_one({"id": user_id}, {"$set": {"aktif": bool(body.get("aktif"))}})
    return {"ok": True}


# ---------------- Helpers ----------------
def compute_total_kewajiban(cif_list):
    total = 0
    for cif in cif_list or []:
        for loan in cif.get("loans", []):
            total += float(loan.get("os_pokok") or 0) + float(loan.get("os_margin") or 0) + float(loan.get("penalti") or 0)
    return total


def clean_case_payload(body: dict, creator: str):
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "nomor_perkara": (body.get("nomor_perkara") or "").strip(),
        "nama_pn": body.get("nama_pn") or "",
        "materi_gugatan": body.get("materi_gugatan") or "",
        "jenis_penggugat": body.get("jenis_penggugat") or "Nasabah",
        "penggugat": [p for p in (body.get("penggugat") or []) if p],
        "tergugat": [t for t in (body.get("tergugat") or []) if t],
        "region": body.get("region") or "",
        "area": body.get("area") or "",
        "cabang": body.get("cabang") or "",
        "pic": body.get("pic") or "",
        "kontak_pic": body.get("kontak_pic") or "",
        "cif_list": body.get("cif_list") or [],
        "jaminan": body.get("jaminan") or [],
        "mediasi": body.get("mediasi") or [],
        "kesimpulan_mediasi": body.get("kesimpulan_mediasi") or "",
        "status_perkara": body.get("status_perkara") or "Gugatan Terdaftar",
        "risk_rating": body.get("risk_rating") or "",
        "rekomendasi_tindakan": body.get("rekomendasi_tindakan") or "",
        "updated_at": now,
    }
    data["total_kewajiban"] = compute_total_kewajiban(data["cif_list"])
    if not data["nomor_perkara"]:
        raise HTTPException(status_code=400, detail="Nomor Perkara wajib diisi")
    if data["status_perkara"] not in STATUS_PERKARA:
        raise HTTPException(status_code=400, detail="Status Perkara tidak valid")
    if data["risk_rating"] and data["risk_rating"] not in RISK_RATINGS:
        raise HTTPException(status_code=400, detail="Risk Rating tidak valid")
    if data["jenis_penggugat"] not in ("Nasabah", "Pihak Ketiga"):
        raise HTTPException(status_code=400, detail="Jenis Penggugat tidak valid")
    return data


def case_query(filters):
    q = {}
    if filters.get("search"):
        s = filters["search"]
        q["$or"] = [
            {"nomor_perkara": {"$regex": s, "$options": "i"}},
            {"penggugat": {"$regex": s, "$options": "i"}},
            {"tergugat": {"$regex": s, "$options": "i"}},
            {"cif_list.nomor_cif": {"$regex": s, "$options": "i"}},
            {"cif_list.loans.nomor_loan": {"$regex": s, "$options": "i"}},
        ]
    for key, field in [("region", "region"), ("area", "area"), ("cabang", "cabang"),
                       ("status", "status_perkara"), ("risk_rating", "risk_rating")]:
        if filters.get(key):
            q[field] = filters[key]
    if filters.get("tahun"):
        q["tahun"] = int(filters["tahun"])
    if filters.get("aktif"):
        q["status_aktif"] = filters["aktif"]
    return q


# ---------------- Cases ----------------
@api_router.get("/cases")
async def list_cases(search: Optional[str] = None, region: Optional[str] = None,
                     area: Optional[str] = None, cabang: Optional[str] = None,
                     status: Optional[str] = None, tahun: Optional[str] = None,
                     risk_rating: Optional[str] = None, aktif: Optional[str] = None,
                     user=Depends(auth_user)):
    q = case_query({"search": search, "region": region, "area": area, "cabang": cabang,
                    "status": status, "tahun": tahun, "risk_rating": risk_rating, "aktif": aktif})
    cases = await db.cases.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)
    return cases


@api_router.get("/cases/{case_id}")
async def get_case(case_id: str, user=Depends(auth_user)):
    case = await db.cases.find_one({"id": case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    return case


@api_router.post("/cases")
async def create_case(body: dict, user=Depends(auth_user)):
    data = clean_case_payload(body, user["username"])
    if await db.cases.find_one({"nomor_perkara": data["nomor_perkara"]}):
        raise HTTPException(status_code=400, detail="Nomor Perkara sudah terdaftar")
    req = {
        "id": str(uuid.uuid4()), "type": "CREATE", "case_id": None,
        "case_nomor": data["nomor_perkara"], "payload": data, "reason": "",
        "status": "MENUNGGU", "requested_by": user["username"], "requested_by_nama": user["nama"],
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "approver": None, "approved_at": None, "catatan_approval": "", "alasan_reject": "",
    }
    if user["role"] == "dept_head":
        await apply_approval(req, user)
        req["status"] = "APPROVED"
    await db.approvals.insert_one(req)
    req.pop("_id", None)
    return req


@api_router.put("/cases/{case_id}")
async def edit_case(case_id: str, body: dict, user=Depends(auth_user)):
    case = await db.cases.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    data = clean_case_payload(body, user["username"])
    if data["nomor_perkara"] != case["nomor_perkara"]:
        if await db.cases.find_one({"nomor_perkara": data["nomor_perkara"]}):
            raise HTTPException(status_code=400, detail="Nomor Perkara sudah terdaftar")
    req = {
        "id": str(uuid.uuid4()), "type": "EDIT", "case_id": case_id,
        "case_nomor": case["nomor_perkara"], "payload": data, "reason": body.get("reason", ""),
        "status": "MENUNGGU", "requested_by": user["username"], "requested_by_nama": user["nama"],
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "approver": None, "approved_at": None, "catatan_approval": "", "alasan_reject": "",
    }
    if user["role"] == "dept_head":
        await apply_approval(req, user)
        req["status"] = "APPROVED"
    await db.approvals.insert_one(req)
    req.pop("_id", None)
    return req


@api_router.post("/cases/{case_id}/delete-request")
async def delete_request(case_id: str, body: dict, user=Depends(auth_user)):
    case = await db.cases.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    mode = body.get("mode")
    alasan = (body.get("alasan") or "").strip()
    if mode not in ("NONAKTIF", "PERMANENT"):
        raise HTTPException(status_code=400, detail="Mode tidak valid")
    if not alasan:
        raise HTTPException(status_code=400, detail="Alasan wajib diisi")
    req = {
        "id": str(uuid.uuid4()), "type": f"DELETE_{mode}", "case_id": case_id,
        "case_nomor": case["nomor_perkara"], "payload": {}, "reason": alasan,
        "status": "MENUNGGU", "requested_by": user["username"], "requested_by_nama": user["nama"],
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "approver": None, "approved_at": None, "catatan_approval": "", "alasan_reject": "",
    }
    if user["role"] == "dept_head":
        await apply_approval(req, user)
        req["status"] = "APPROVED"
    await db.approvals.insert_one(req)
    req.pop("_id", None)
    return req


@api_router.patch("/cases/{case_id}/operasional")
async def update_operasional(case_id: str, body: dict, user=Depends(auth_user)):
    case = await db.cases.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    allowed = {}
    if body.get("status_perkara") in STATUS_PERKARA:
        allowed["status_perkara"] = body["status_perkara"]
    if "mediasi" in body:
        allowed["mediasi"] = body["mediasi"]
    if "kesimpulan_mediasi" in body:
        allowed["kesimpulan_mediasi"] = body["kesimpulan_mediasi"]
    if body.get("risk_rating") in RISK_RATINGS:
        allowed["risk_rating"] = body["risk_rating"]
    if "rekomendasi_tindakan" in body:
        allowed["rekomendasi_tindakan"] = body["rekomendasi_tindakan"]
    if not allowed:
        raise HTTPException(status_code=400, detail="Tidak ada perubahan")
    allowed["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.cases.update_one({"id": case_id}, {"$set": allowed})
    if "status_perkara" in allowed:
        await add_timeline(case_id, f"Status: {allowed['status_perkara']}",
                           f"Diperbarui oleh {user['nama']}", "status")
    return {"ok": True}


@api_router.post("/cases/{case_id}/agenda")
async def add_agenda(case_id: str, body: dict, user=Depends(auth_user)):
    case = await db.cases.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    tanggal = body.get("tanggal")
    agenda = body.get("agenda")
    if not tanggal or not agenda:
        raise HTTPException(status_code=400, detail="Tanggal dan agenda wajib diisi")
    item = {"id": str(uuid.uuid4()), "tanggal": tanggal, "agenda": agenda,
            "keterangan": body.get("keterangan") or "", "created_by": user["nama"]}
    await db.cases.update_one({"id": case_id}, {"$push": {"agenda_sidang": item}})
    await add_timeline(case_id, f"Sidang: {agenda}", f"{tanggal} — {item['keterangan']}", "agenda", tanggal)
    return item


@api_router.delete("/cases/{case_id}/agenda/{agenda_id}")
async def delete_agenda(case_id: str, agenda_id: str, user=Depends(auth_user)):
    if not await db.cases.find_one({"id": case_id}):
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    res = await db.cases.update_one({"id": case_id}, {"$pull": {"agenda_sidang": {"id": agenda_id}}})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="Agenda tidak ditemukan")
    return {"ok": True}


async def add_timeline(case_id, judul, keterangan, tipe, tanggal=None):
    event = {"id": str(uuid.uuid4()), "tanggal": tanggal or datetime.now(timezone.utc).date().isoformat(),
             "judul": judul, "keterangan": keterangan, "type": tipe}
    await db.cases.update_one({"id": case_id}, {"$push": {"timeline": event}})
    return event


# ---------------- Approvals ----------------
async def apply_approval(req, approver):
    now = datetime.now(timezone.utc).isoformat()
    if req["type"] == "CREATE":
        data = dict(req["payload"])
        if await db.cases.find_one({"nomor_perkara": data["nomor_perkara"]}):
            raise HTTPException(status_code=400, detail=f"Nomor Perkara {data['nomor_perkara']} sudah terdaftar. Reject request ini.")
        data.update({
            "id": str(uuid.uuid4()), "status_aktif": "AKTIF", "alasan_nonaktif": "",
            "tahun": datetime.now(timezone.utc).year,
            "tanggal_input": now, "created_by": req["requested_by"],
            "created_at": now, "agenda_sidang": [],
            "timeline": [{"id": str(uuid.uuid4()), "tanggal": now[:10],
                          "judul": "Perkara didaftarkan",
                          "keterangan": f"Diinput oleh {req['requested_by_nama']}, disetujui {approver['nama']}",
                          "type": "status"}],
        })
        await db.cases.insert_one(data)
        req["case_id"] = data["id"]
    elif req["type"] == "EDIT":
        dup = await db.cases.find_one({"nomor_perkara": req["payload"]["nomor_perkara"]})
        if dup and dup["id"] != req["case_id"]:
            raise HTTPException(status_code=400, detail=f"Nomor Perkara {req['payload']['nomor_perkara']} sudah digunakan perkara lain. Reject request ini.")
        await db.cases.update_one({"id": req["case_id"]}, {"$set": req["payload"]})
        await add_timeline(req["case_id"], "Data perkara diperbarui",
                           f"Edit oleh {req['requested_by_nama']}, disetujui {approver['nama']}", "edit")
    elif req["type"] == "DELETE_NONAKTIF":
        await db.cases.update_one({"id": req["case_id"]},
                                  {"$set": {"status_aktif": "TIDAK AKTIF", "alasan_nonaktif": req["reason"]}})
        await add_timeline(req["case_id"], "Perkara dinonaktifkan", req["reason"], "status")
    elif req["type"] == "DELETE_PERMANENT":
        await db.cases.delete_one({"id": req["case_id"]})
        await db.documents.delete_many({"case_id": req["case_id"]})


@api_router.get("/approvals")
async def list_approvals(status: Optional[str] = None, user=Depends(auth_user)):
    q = {}
    if user["role"] != "dept_head":
        q["requested_by"] = user["username"]
    if status:
        q["status"] = status
    return await db.approvals.find(q, {"_id": 0}).sort("requested_at", -1).to_list(2000)


@api_router.post("/approvals/{req_id}/approve")
async def approve(req_id: str, body: dict, user=Depends(dept_head_only)):
    req = await db.approvals.find_one({"id": req_id})
    if not req:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan")
    if req["status"] != "MENUNGGU":
        raise HTTPException(status_code=400, detail="Request sudah diproses")
    await apply_approval(req, user)
    await db.approvals.update_one({"id": req_id}, {"$set": {
        "status": "APPROVED", "approver": user["nama"],
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "catatan_approval": body.get("catatan") or "", "case_id": req.get("case_id")}})
    return {"ok": True}


@api_router.post("/approvals/{req_id}/reject")
async def reject(req_id: str, body: dict, user=Depends(dept_head_only)):
    alasan = (body.get("alasan_reject") or "").strip()
    if not alasan:
        raise HTTPException(status_code=400, detail="Alasan reject wajib diisi")
    req = await db.approvals.find_one({"id": req_id})
    if not req:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan")
    if req["status"] != "MENUNGGU":
        raise HTTPException(status_code=400, detail="Request sudah diproses")
    await db.approvals.update_one({"id": req_id}, {"$set": {
        "status": "REJECTED", "approver": user["nama"],
        "approved_at": datetime.now(timezone.utc).isoformat(), "alasan_reject": alasan}})
    return {"ok": True}


# ---------------- Documents ----------------
@api_router.post("/cases/{case_id}/documents")
async def upload_document(case_id: str, file: UploadFile = File(...),
                          kategori: str = Form(...), nomor: str = Form(""),
                          tanggal: str = Form(""), user=Depends(auth_user)):
    case = await db.cases.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Perkara tidak ditemukan")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hanya file PDF yang diperbolehkan")
    doc_id = str(uuid.uuid4())
    folder = UPLOAD_DIR / case_id
    folder.mkdir(exist_ok=True)
    path = folder / f"{doc_id}.pdf"
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 20MB")
    with open(path, "wb") as f:
        f.write(content)
    doc = {"id": doc_id, "case_id": case_id, "case_nomor": case["nomor_perkara"],
           "kategori": kategori, "nomor": nomor, "tanggal": tanggal,
           "original_name": file.filename, "size": len(content),
           "uploaded_by": user["nama"], "uploaded_at": datetime.now(timezone.utc).isoformat()}
    await db.documents.insert_one(doc)
    await add_timeline(case_id, f"Dokumen: {kategori}", f"Diunggah oleh {user['nama']}", "dokumen")
    doc.pop("_id", None)
    return doc


@api_router.get("/documents")
async def list_documents(case_id: Optional[str] = None, user=Depends(auth_user)):
    q = {"case_id": case_id} if case_id else {}
    return await db.documents.find(q, {"_id": 0}).sort("uploaded_at", -1).to_list(5000)


@api_router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, user=Depends(auth_user)):
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    path = UPLOAD_DIR / doc["case_id"] / f"{doc_id}.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(path, media_type="application/pdf", filename=doc["original_name"])


@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user=Depends(auth_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    path = UPLOAD_DIR / doc["case_id"] / f"{doc_id}.pdf"
    if path.exists():
        path.unlink()
    await db.documents.delete_one({"id": doc_id})
    return {"ok": True}


# ---------------- Dashboard ----------------
@api_router.get("/dashboard/stats")
async def dashboard_stats(tahun: Optional[str] = None, region: Optional[str] = None,
                          area: Optional[str] = None, cabang: Optional[str] = None,
                          status: Optional[str] = None, user=Depends(auth_user)):
    q = case_query({"tahun": tahun, "region": region, "area": area, "cabang": cabang, "status": status})
    cases = await db.cases.find(q, {"_id": 0}).to_list(10000)
    aktif = [c for c in cases if c.get("status_aktif") == "AKTIF"]

    def count_by(field, source=None):
        result = {}
        for c in (source if source is not None else cases):
            key = c.get(field) or "Lainnya"
            result[key] = result.get(key, 0) + 1
        return [{"name": k, "value": v} for k, v in sorted(result.items(), key=lambda x: -x[1])]

    monthly = {}
    for c in cases:
        m = (c.get("tanggal_input") or "")[:7]
        if m:
            monthly[m] = monthly.get(m, 0) + 1
    timeline_chart = [{"name": k, "value": monthly[k]} for k in sorted(monthly)]

    today = datetime.now(timezone.utc).date()
    reminders = []
    for c in cases:
        if c.get("status_aktif") != "AKTIF":
            continue
        for ag in c.get("agenda_sidang", []):
            try:
                d = datetime.fromisoformat(ag["tanggal"]).date()
            except (ValueError, TypeError):
                continue
            days = (d - today).days
            if -7 <= days <= 60:
                reminders.append({
                    "case_id": c["id"], "nomor_perkara": c["nomor_perkara"],
                    "agenda": ag["agenda"], "tanggal": ag["tanggal"], "hari": days,
                    "label": f"{ag['agenda']} jatuh tempo {days} hari lagi" if days >= 0
                             else f"{ag['agenda']} terlewat {-days} hari",
                })
    reminders.sort(key=lambda r: r["hari"])

    pending = await db.approvals.count_documents({"status": "MENUNGGU"})

    return {
        "total_aktif": len(aktif),
        "total_perkara": len(cases),
        "total_kewajiban": sum(c.get("total_kewajiban", 0) for c in aktif),
        "per_region": count_by("region"),
        "per_area": count_by("area"),
        "per_cabang": count_by("cabang"),
        "per_status": count_by("status_perkara"),
        "per_aktif": count_by("status_aktif"),
        "per_risk": count_by("risk_rating", aktif),
        "timeline_chart": timeline_chart,
        "reminders": reminders[:50],
        "pending_approvals": pending,
    }


@api_router.get("/master-data")
async def master_data(user=Depends(auth_user)):
    return {
        "status_perkara": STATUS_PERKARA,
        "agenda_list": AGENDA_LIST,
        "dokumen_kategori": DOKUMEN_KATEGORI,
        "risk_ratings": RISK_RATINGS,
        "region_area_map": REGION_AREA_MAP,
        "regions": await db.cases.distinct("region"),
        "areas": await db.cases.distinct("area"),
        "cabangs": await db.cases.distinct("cabang"),
        "tahun": sorted(await db.cases.distinct("tahun"), reverse=True),
    }


# ---------------- Export ----------------
def style_header(ws):
    fill = PatternFill("solid", fgColor="00A0A0")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill


CASE_COLUMNS = ["Nomor Perkara", "Nama PN/PA", "Materi Gugatan", "Jenis Penggugat", "Penggugat",
                "Tergugat", "Region", "Area", "Cabang", "PIC", "Kontak PIC", "CIF", "Loan",
                "Total Kewajiban", "Status Perkara", "Risk Rating", "Status Aktif", "Tahun", "Tanggal Input"]


def case_row(c):
    cifs = ", ".join(cf.get("nomor_cif", "") for cf in c.get("cif_list", []))
    loans = ", ".join(l.get("nomor_loan", "") for cf in c.get("cif_list", []) for l in cf.get("loans", []))
    return [c.get("nomor_perkara"), c.get("nama_pn"), c.get("materi_gugatan"), c.get("jenis_penggugat"),
            ", ".join(c.get("penggugat", [])), ", ".join(c.get("tergugat", [])),
            c.get("region"), c.get("area"), c.get("cabang"), c.get("pic"), c.get("kontak_pic"),
            cifs, loans, c.get("total_kewajiban"), c.get("status_perkara"), c.get("risk_rating"),
            c.get("status_aktif"), c.get("tahun"), (c.get("tanggal_input") or "")[:10]]


def wb_response(wb, filename):
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


@api_router.get("/export/cases")
async def export_cases(region: Optional[str] = None, area: Optional[str] = None,
                       cabang: Optional[str] = None, status: Optional[str] = None,
                       tahun: Optional[str] = None, risk_rating: Optional[str] = None,
                       aktif: Optional[str] = None, user=Depends(auth_user)):
    q = case_query({"region": region, "area": area, "cabang": cabang, "status": status,
                    "tahun": tahun, "risk_rating": risk_rating, "aktif": aktif})
    cases = await db.cases.find(q, {"_id": 0}).to_list(10000)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DATA PERKARA"
    ws.append(CASE_COLUMNS)
    for c in cases:
        ws.append(case_row(c))
    style_header(ws)
    await db.export_logs.insert_one({
        "id": str(uuid.uuid4()), "type": "EXPORT_PERKARA", "user": user["nama"],
        "jumlah": len(cases), "tanggal": datetime.now(timezone.utc).isoformat()})
    return wb_response(wb, "laporan_perkara.xlsx")


@api_router.get("/export/database")
async def export_database(tahun: Optional[str] = None, region: Optional[str] = None,
                          area: Optional[str] = None, cabang: Optional[str] = None,
                          status: Optional[str] = None, risk_rating: Optional[str] = None,
                          aktif: Optional[str] = None, user=Depends(dept_head_only)):
    q = case_query({"tahun": tahun, "region": region, "area": area, "cabang": cabang,
                    "status": status, "risk_rating": risk_rating, "aktif": aktif})
    cases = await db.cases.find(q, {"_id": 0}).to_list(10000)
    wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = "DATA PERKARA"
    ws.append(CASE_COLUMNS)
    for c in cases:
        ws.append(case_row(c))
    style_header(ws)

    ws2 = wb.create_sheet("DATA LOAN")
    ws2.append(["Nomor Perkara", "CIF", "Nomor Loan", "OS Pokok", "OS Margin", "Penalti"])
    for c in cases:
        for cf in c.get("cif_list", []):
            for l in cf.get("loans", []):
                ws2.append([c["nomor_perkara"], cf.get("nomor_cif"), l.get("nomor_loan"),
                            l.get("os_pokok"), l.get("os_margin"), l.get("penalti")])
    style_header(ws2)

    ws3 = wb.create_sheet("DATA JAMINAN")
    ws3.append(["Nomor Perkara", "CIF", "Jenis Jaminan", "Deskripsi Jaminan", "Nilai Jaminan", "Status Pengikatan"])
    for c in cases:
        cif0 = c.get("cif_list", [{}])[0].get("nomor_cif", "") if c.get("cif_list") else ""
        for j in c.get("jaminan", []):
            ws3.append([c["nomor_perkara"], cif0, j.get("jenis"), j.get("deskripsi"),
                        j.get("nilai"), j.get("status_pengikatan")])
    style_header(ws3)

    ws4 = wb.create_sheet("DATA PROSES PERKARA")
    ws4.append(["Nomor Perkara", "Tahapan Perkara", "Tanggal Tahapan", "Keterangan"])
    for c in cases:
        for t in c.get("timeline", []):
            ws4.append([c["nomor_perkara"], t.get("judul"), t.get("tanggal"), t.get("keterangan")])
    style_header(ws4)

    ws5 = wb.create_sheet("DATA APPROVAL")
    ws5.append(["Tipe", "Nomor Perkara", "Status", "Diminta Oleh", "Tanggal Request",
                "Approver", "Tanggal Approval", "Catatan", "Alasan Reject"])
    async for a in db.approvals.find({}, {"_id": 0}):
        ws5.append([a.get("type"), a.get("case_nomor"), a.get("status"), a.get("requested_by_nama"),
                    (a.get("requested_at") or "")[:10], a.get("approver"),
                    (a.get("approved_at") or "")[:10], a.get("catatan_approval"), a.get("alasan_reject")])
    style_header(ws5)

    ws6 = wb.create_sheet("DATA USER")
    ws6.append(["Username", "Nama", "Role", "Status"])
    async for u in db.users.find({}, {"_id": 0, "password_hash": 0}):
        ws6.append([u.get("username"), u.get("nama"), u.get("role"),
                    "Aktif" if u.get("aktif") else "Non Aktif"])
    style_header(ws6)

    await db.export_logs.insert_one({
        "id": str(uuid.uuid4()), "type": "EXPORT_DATABASE", "user": user["nama"],
        "jumlah": len(cases), "tanggal": datetime.now(timezone.utc).isoformat()})
    return wb_response(wb, "casewise_database_export.xlsx")


@api_router.get("/export/template")
async def download_template(user=Depends(dept_head_only)):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DATA PERKARA"
    ws.append(["Nomor Perkara", "Nama PN/PA", "Materi Gugatan", "Jenis Penggugat", "Nama Penggugat",
               "Daftar Tergugat", "Region", "Area", "Cabang", "PIC", "CIF"])
    style_header(ws)
    ws2 = wb.create_sheet("DATA LOAN")
    ws2.append(["CIF", "Nomor Loan", "OS Pokok", "OS Margin", "Penalti"])
    style_header(ws2)
    ws3 = wb.create_sheet("DATA JAMINAN")
    ws3.append(["CIF", "Jenis Jaminan", "Deskripsi Jaminan", "Nilai Jaminan", "Status Pengikatan"])
    style_header(ws3)
    ws4 = wb.create_sheet("DATA PROSES PERKARA")
    ws4.append(["Nomor Perkara", "Tahapan Perkara", "Tanggal Tahapan", "Keterangan"])
    style_header(ws4)
    return wb_response(wb, "template_import_casewise.xlsx")


@api_router.get("/export/last")
async def last_export(user=Depends(dept_head_only)):
    log = await db.export_logs.find({"type": "EXPORT_DATABASE"}, {"_id": 0}).sort("tanggal", -1).limit(1).to_list(1)
    return log[0] if log else None


# ---------------- Import ----------------
def safe_float(v):
    try:
        return float(v or 0)
    except (ValueError, TypeError):
        raise ValueError("bukan angka")


def parse_import(wb):
    errors = []
    perkara_rows = []
    if "DATA PERKARA" not in wb.sheetnames:
        raise HTTPException(status_code=400, detail="Sheet DATA PERKARA tidak ditemukan. Gunakan template import.")
    ws = wb["DATA PERKARA"]
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue
        nomor = str(row[0]).strip() if row[0] else ""
        if not nomor:
            errors.append({"sheet": "DATA PERKARA", "baris": i, "kolom": "Nomor Perkara",
                           "keterangan": "Nomor Perkara kosong"})
            continue
        perkara_rows.append({
            "baris": i, "nomor_perkara": nomor, "nama_pn": row[1] or "", "materi_gugatan": row[2] or "",
            "jenis_penggugat": row[3] or "Nasabah",
            "penggugat": [p.strip() for p in str(row[4] or "").split(";") if p.strip()],
            "tergugat": [t.strip() for t in str(row[5] or "").split(";") if t.strip()],
            "region": row[6] or "", "area": row[7] or "", "cabang": row[8] or "",
            "pic": row[9] or "", "cif": str(row[10]).strip() if row[10] else "",
        })
    loans = {}
    if "DATA LOAN" in wb.sheetnames:
        for i, row in enumerate(wb["DATA LOAN"].iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue
            cif = str(row[0]).strip() if row[0] else ""
            if not cif:
                errors.append({"sheet": "DATA LOAN", "baris": i, "kolom": "CIF", "keterangan": "CIF kosong"})
                continue
            try:
                loans.setdefault(cif, []).append({
                    "nomor_loan": str(row[1] or ""), "os_pokok": safe_float(row[2]),
                    "os_margin": safe_float(row[3]), "penalti": safe_float(row[4])})
            except ValueError:
                errors.append({"sheet": "DATA LOAN", "baris": i, "kolom": "OS Pokok/OS Margin/Penalti",
                               "keterangan": "Nilai bukan angka valid"})
    jaminan = {}
    if "DATA JAMINAN" in wb.sheetnames:
        for i, row in enumerate(wb["DATA JAMINAN"].iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue
            cif = str(row[0]).strip() if row[0] else ""
            try:
                jaminan.setdefault(cif, []).append({
                    "jenis": row[1] or "", "deskripsi": row[2] or "",
                    "nilai": safe_float(row[3]), "status_pengikatan": row[4] or ""})
            except ValueError:
                errors.append({"sheet": "DATA JAMINAN", "baris": i, "kolom": "Nilai Jaminan",
                               "keterangan": "Nilai bukan angka valid"})
    proses = {}
    if "DATA PROSES PERKARA" in wb.sheetnames:
        for i, row in enumerate(wb["DATA PROSES PERKARA"].iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue
            nomor = str(row[0]).strip() if row[0] else ""
            proses.setdefault(nomor, []).append({
                "id": str(uuid.uuid4()), "judul": str(row[1] or ""),
                "tanggal": str(row[2] or "")[:10], "keterangan": str(row[3] or ""), "type": "import"})
    return perkara_rows, loans, jaminan, proses, errors


@api_router.post("/import/preview")
async def import_preview(file: UploadFile = File(...), user=Depends(dept_head_only)):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Hanya file Excel (.xlsx)")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 10MB")
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="File Excel tidak dapat dibaca. Gunakan template import.")
    perkara_rows, loans, jaminan, proses, errors = parse_import(wb)
    seen = set()
    baru, update, gagal = 0, 0, 0
    staged = []
    for r in perkara_rows:
        if r["nomor_perkara"] in seen:
            errors.append({"sheet": "DATA PERKARA", "baris": r["baris"], "kolom": "Nomor Perkara",
                           "keterangan": f"Nomor Perkara duplikat dalam file: {r['nomor_perkara']}"})
            gagal += 1
            continue
        seen.add(r["nomor_perkara"])
        existing = await db.cases.find_one({"nomor_perkara": r["nomor_perkara"]})
        if existing:
            update += 1
        else:
            baru += 1
        staged.append({**r, "mode": "update" if existing else "baru"})
    staging_id = str(uuid.uuid4())
    await db.import_staging.insert_one({
        "id": staging_id, "user": user["username"],
        "tanggal": datetime.now(timezone.utc).isoformat(),
        "rows": staged, "loans": loans, "jaminan": jaminan, "proses": proses})
    return {"staging_id": staging_id, "baru": baru, "update": update,
            "gagal": gagal, "errors": errors[:200]}


@api_router.post("/import/execute")
async def import_execute(body: dict, user=Depends(dept_head_only)):
    staging = await db.import_staging.find_one({"id": body.get("staging_id")}, {"_id": 0})
    if not staging:
        raise HTTPException(status_code=404, detail="Data staging tidak ditemukan, ulangi preview")
    now = datetime.now(timezone.utc).isoformat()
    imported = 0
    for r in staging["rows"]:
        cif_list = []
        if r["cif"]:
            cif_list = [{"nomor_cif": r["cif"], "loans": staging["loans"].get(r["cif"], [])}]
        payload = {
            "nomor_perkara": r["nomor_perkara"], "nama_pn": r["nama_pn"],
            "materi_gugatan": r["materi_gugatan"], "jenis_penggugat": r["jenis_penggugat"],
            "penggugat": r["penggugat"], "tergugat": r["tergugat"], "region": r["region"],
            "area": r["area"], "cabang": r["cabang"], "pic": r["pic"], "kontak_pic": "",
            "cif_list": cif_list, "jaminan": staging["jaminan"].get(r["cif"], []),
            "mediasi": [], "kesimpulan_mediasi": "", "status_perkara": "Gugatan Terdaftar",
            "risk_rating": "", "rekomendasi_tindakan": "", "updated_at": now,
        }
        payload["total_kewajiban"] = compute_total_kewajiban(cif_list)
        timeline = staging["proses"].get(r["nomor_perkara"], [])
        existing = await db.cases.find_one({"nomor_perkara": r["nomor_perkara"]})
        if existing:
            await db.cases.update_one({"id": existing["id"]}, {"$set": payload})
            if timeline:
                await db.cases.update_one({"id": existing["id"]}, {"$push": {"timeline": {"$each": timeline}}})
        else:
            payload.update({
                "id": str(uuid.uuid4()), "status_aktif": "AKTIF", "alasan_nonaktif": "",
                "tahun": datetime.now(timezone.utc).year, "tanggal_input": now,
                "created_by": user["username"], "created_at": now, "agenda_sidang": [],
                "timeline": timeline or [{"id": str(uuid.uuid4()), "tanggal": now[:10],
                                          "judul": "Perkara didaftarkan (import)",
                                          "keterangan": f"Diimpor oleh {user['nama']}", "type": "import"}],
            })
            await db.cases.insert_one(payload)
        imported += 1
    await db.import_staging.delete_one({"id": staging["id"]})
    return {"ok": True, "imported": imported}


# ---------------- Seed ----------------
SAMPLE_CASES = [
    {"nomor_perkara": "123/Pdt.G/2024/PN.Jkt.Sel", "nama_pn": "PN Jakarta Selatan", "materi_gugatan": "Gugatan wanprestasi atas perjanjian pembiayaan murabahah yang tidak dilaksanakan oleh nasabah sesuai akad.", "jenis_penggugat": "Nasabah", "penggugat": ["H. Ahmad Fauzi"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 1 - Jakarta", "area": "Area Jakarta Selatan", "cabang": "KC Jakarta Tebet", "pic": "Rina Marlina", "kontak_pic": "0812-3456-7890", "status_perkara": "Mediasi", "risk_rating": "Medium Risk", "rekomendasi_tindakan": "Upayakan perdamaian melalui mediasi dengan skema restrukturisasi.", "tahun": 2024, "cif_list": [{"nomor_cif": "CIF001234", "loans": [{"nomor_loan": "LN-1001", "os_pokok": 450000000, "os_margin": 85000000, "penalti": 12000000}]}], "jaminan": [{"jenis": "Tanah dan Bangunan (Rumah Tinggal)", "deskripsi": "SHM No.15, LT 100 M2, LB 90 M2, Desa Alemandah, Kec. Rancabali, Kab. Bandung, Jawa Barat", "nilai": 750000000, "status_pengikatan": "APHT"}]},
    {"nomor_perkara": "45/Pdt.G/2024/PN.Bdg", "nama_pn": "PN Bandung", "materi_gugatan": "Gugatan perbuatan melawan hukum terkait lelang jaminan hak tanggungan.", "jenis_penggugat": "Pihak Ketiga", "penggugat": ["CV. Maju Bersama", "Ir. Bambang Sutrisno"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk", "KPKNL Bandung"], "region": "Region 2 - Jawa Barat", "area": "Area Bandung", "cabang": "KC Bandung Asia Afrika", "pic": "Dedi Kurniawan", "kontak_pic": "0813-9876-5432", "status_perkara": "Pembuktian", "risk_rating": "High Risk", "rekomendasi_tindakan": "Siapkan bukti lelang lengkap dan koordinasi dengan KPKNL.", "tahun": 2024, "cif_list": [{"nomor_cif": "CIF005678", "loans": [{"nomor_loan": "LN-2001", "os_pokok": 1250000000, "os_margin": 210000000, "penalti": 45000000}, {"nomor_loan": "LN-2002", "os_pokok": 300000000, "os_margin": 52000000, "penalti": 8000000}]}], "jaminan": [{"jenis": "Tanah dan Bangunan (Ruko)", "deskripsi": "SHM No.88, LT 200 M2, LB 180 M2, Jl. Merdeka No. 45, Bandung", "nilai": 2100000000, "status_pengikatan": "SKMHT"}]},
    {"nomor_perkara": "78/Pdt.G/2023/PN.Sby", "nama_pn": "PN Surabaya", "materi_gugatan": "Gugatan pembatalan akad pembiayaan musyarakah.", "jenis_penggugat": "Nasabah", "penggugat": ["Hj. Siti Aminah"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 3 - Jawa Timur", "area": "Area Surabaya", "cabang": "KC Surabaya Darmo", "pic": "Andi Wijaya", "kontak_pic": "0821-1122-3344", "status_perkara": "Putusan", "risk_rating": "Low Risk", "rekomendasi_tindakan": "Menunggu salinan putusan resmi dari pengadilan.", "tahun": 2023, "cif_list": [{"nomor_cif": "CIF009012", "loans": [{"nomor_loan": "LN-3001", "os_pokok": 275000000, "os_margin": 48000000, "penalti": 5500000}]}], "jaminan": []},
    {"nomor_perkara": "201/Pdt.G/2024/PN.Mdn", "nama_pn": "PN Medan", "materi_gugatan": "Gugatan wanprestasi pembiayaan kepemilikan rumah syariah.", "jenis_penggugat": "Nasabah", "penggugat": ["Drs. Hasan Basri"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 4 - Sumatera", "area": "Area Medan", "cabang": "KC Medan Katamso", "pic": "Sari Puspita", "kontak_pic": "0812-5566-7788", "status_perkara": "Banding", "risk_rating": "High Risk", "rekomendasi_tindakan": "Segera susun memori banding, batas waktu 14 hari.", "tahun": 2024, "cif_list": [{"nomor_cif": "CIF003456", "loans": [{"nomor_loan": "LN-4001", "os_pokok": 680000000, "os_margin": 125000000, "penalti": 22000000}]}], "jaminan": [{"jenis": "Tanah dan Bangunan (Rumah Tinggal)", "deskripsi": "SHM No.201, LT 150 M2, LB 120 M2, Jl. Gatot Subroto KM 7, Medan", "nilai": 950000000, "status_pengikatan": "APHT"}]},
    {"nomor_perkara": "99/Pdt.G/2025/PN.Smg", "nama_pn": "PN Semarang", "materi_gugatan": "Gugatan perbuatan melawan hukum atas pemblokiran rekening.", "jenis_penggugat": "Pihak Ketiga", "penggugat": ["PT. Sumber Rejeki Abadi"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 5 - Jawa Tengah", "area": "Area Semarang", "cabang": "KC Semarang Pandanaran", "pic": "Budi Santoso", "kontak_pic": "0815-2233-4455", "status_perkara": "Jawaban Tergugat", "risk_rating": "Medium Risk", "rekomendasi_tindakan": "Lengkapi dokumen SOP pemblokiran dan dasar hukum internal.", "tahun": 2025, "cif_list": [{"nomor_cif": "CIF007890", "loans": [{"nomor_loan": "LN-5001", "os_pokok": 520000000, "os_margin": 90000000, "penalti": 15000000}]}], "jaminan": []},
    {"nomor_perkara": "156/Pdt.G/2023/PN.Mks", "nama_pn": "PN Makassar", "materi_gugatan": "Gugatan wanprestasi pembiayaan modal usaha.", "jenis_penggugat": "Nasabah", "penggugat": ["H. Muhammad Yusuf", "Hj. Fatimah"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 6 - Indonesia Timur", "area": "Area Makassar", "cabang": "KC Makassar Ahmad Yani", "pic": "Fitri Handayani", "kontak_pic": "0822-3344-5566", "status_perkara": "Kasasi", "risk_rating": "High Risk", "rekomendasi_tindakan": "Koordinasi dengan kantor hukum eksternal untuk memori kasasi.", "tahun": 2023, "cif_list": [{"nomor_cif": "CIF002233", "loans": [{"nomor_loan": "LN-6001", "os_pokok": 890000000, "os_margin": 165000000, "penalti": 38000000}]}], "jaminan": [{"jenis": "Tanah (Kebun)", "deskripsi": "SHM No.45, LT 5000 M2, Kab. Gowa, Sulawesi Selatan", "nilai": 1500000000, "status_pengikatan": "APHT"}]},
    {"nomor_perkara": "67/Pdt.G/2025/PN.Dps", "nama_pn": "PN Denpasar", "materi_gugatan": "Gugatan pembatalan lelang objek hak tanggungan.", "jenis_penggugat": "Nasabah", "penggugat": ["I Made Wirawan"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk", "KPKNL Denpasar"], "region": "Region 7 - Bali Nusra", "area": "Area Denpasar", "cabang": "KC Denpasar Renon", "pic": "Kadek Ariana", "kontak_pic": "0819-4455-6677", "status_perkara": "Gugatan Terdaftar", "risk_rating": "Medium Risk", "rekomendasi_tindakan": "Persiapkan jawaban dan dokumen lelang.", "tahun": 2025, "cif_list": [{"nomor_cif": "CIF004455", "loans": [{"nomor_loan": "LN-7001", "os_pokok": 750000000, "os_margin": 140000000, "penalti": 25000000}]}], "jaminan": [{"jenis": "Tanah dan Bangunan (Villa)", "deskripsi": "SHM No.77, LT 300 M2, LB 250 M2, Ubud, Gianyar, Bali", "nilai": 1800000000, "status_pengikatan": "APHT"}]},
    {"nomor_perkara": "88/Pdt.G/2024/PN.Plg", "nama_pn": "PN Palembang", "materi_gugatan": "Gugatan wanprestasi pembiayaan kendaraan bermotor.", "jenis_penggugat": "Nasabah", "penggugat": ["Rudi Hartono"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 4 - Sumatera", "area": "Area Palembang", "cabang": "KC Palembang Sudirman", "pic": "Dewi Lestari", "kontak_pic": "0811-6677-8899", "status_perkara": "Inkracht", "risk_rating": "Low Risk", "rekomendasi_tindakan": "Proses eksekusi jaminan sesuai putusan.", "tahun": 2024, "cif_list": [{"nomor_cif": "CIF006677", "loans": [{"nomor_loan": "LN-8001", "os_pokok": 180000000, "os_margin": 32000000, "penalti": 4000000}]}], "jaminan": [{"jenis": "Kendaraan Bermotor", "deskripsi": "BPKB Toyota Fortuner 2021, Nopol BG 1234 XY", "nilai": 350000000, "status_pengikatan": "Fidusia"}]},
    {"nomor_perkara": "134/Pdt.G/2025/PN.Jkt.Pst", "nama_pn": "PN Jakarta Pusat", "materi_gugatan": "Gugatan perbuatan melawan hukum terkait pelaporan BI Checking/SLIK.", "jenis_penggugat": "Pihak Ketiga", "penggugat": ["Dr. Hendra Gunawan"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 1 - Jakarta", "area": "Area Jakarta Pusat", "cabang": "KC Jakarta Thamrin", "pic": "Maya Anggraini", "kontak_pic": "0816-7788-9900", "status_perkara": "Replik", "risk_rating": "High Risk", "rekomendasi_tindakan": "Kumpulkan histori pelaporan SLIK dan kronologi tunggakan.", "tahun": 2025, "cif_list": [{"nomor_cif": "CIF008899", "loans": [{"nomor_loan": "LN-9001", "os_pokok": 2100000000, "os_margin": 380000000, "penalti": 75000000}]}], "jaminan": [{"jenis": "Tanah dan Bangunan (Kantor)", "deskripsi": "SHGB No.120, LT 500 M2, LB 800 M2, Jl. Sudirman Kav. 25, Jakarta", "nilai": 4500000000, "status_pengikatan": "APHT"}]},
    {"nomor_perkara": "23/Pdt.G/2023/PN.Yyk", "nama_pn": "PN Yogyakarta", "materi_gugatan": "Gugatan wanprestasi pembiayaan multiguna.", "jenis_penggugat": "Nasabah", "penggugat": ["Sri Wahyuni"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 5 - Jawa Tengah", "area": "Area Yogyakarta", "cabang": "KC Yogyakarta Malioboro", "pic": "Agus Prasetyo", "kontak_pic": "0817-8899-0011", "status_perkara": "Eksekusi Jaminan", "risk_rating": "Low Risk", "rekomendasi_tindakan": "Koordinasi dengan juru sita untuk lelang eksekusi.", "tahun": 2023, "cif_list": [{"nomor_cif": "CIF001122", "loans": [{"nomor_loan": "LN-1101", "os_pokok": 320000000, "os_margin": 58000000, "penalti": 9000000}]}], "jaminan": [{"jenis": "Tanah dan Bangunan (Rumah Tinggal)", "deskripsi": "SHM No.301, LT 120 M2, LB 100 M2, Sleman, DIY", "nilai": 550000000, "status_pengikatan": "APHT"}]},
    {"nomor_perkara": "312/Pdt.G/2025/PN.Bjm", "nama_pn": "PN Banjarmasin", "materi_gugatan": "Gugatan pembatalan perjanjian pembiayaan istishna.", "jenis_penggugat": "Nasabah", "penggugat": ["H. Abdul Rahman", "PT. Borneo Karya"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 8 - Kalimantan", "area": "Area Banjarmasin", "cabang": "KC Banjarmasin Lambung Mangkurat", "pic": "Nur Hidayah", "kontak_pic": "0818-9900-1122", "status_perkara": "Duplik", "risk_rating": "Medium Risk", "rekomendasi_tindakan": "Review kembali klausul akad istishna dengan tim bisnis.", "tahun": 2025, "cif_list": [{"nomor_cif": "CIF003344", "loans": [{"nomor_loan": "LN-1201", "os_pokok": 950000000, "os_margin": 175000000, "penalti": 28000000}]}], "jaminan": []},
    {"nomor_perkara": "145/Pdt.G/2024/PN.Pkb", "nama_pn": "PN Pekanbaru", "materi_gugatan": "Gugatan wanprestasi pembiayaan perkebunan kelapa sawit.", "jenis_penggugat": "Pihak Ketiga", "penggugat": ["Koperasi Sawit Makmur"], "tergugat": ["PT. Bank Syariah Indonesia, Tbk"], "region": "Region 4 - Sumatera", "area": "Area Pekanbaru", "cabang": "KC Pekanbaru Nangka", "pic": "Eko Prasetyo", "kontak_pic": "0812-0011-2233", "status_perkara": "Settlement / Perdamaian", "risk_rating": "Low Risk", "rekomendasi_tindakan": "Finalisasi akta perdamaian dan monitoring pembayaran.", "tahun": 2024, "cif_list": [{"nomor_cif": "CIF005566", "loans": [{"nomor_loan": "LN-1301", "os_pokok": 1500000000, "os_margin": 275000000, "penalti": 42000000}]}], "jaminan": [{"jenis": "Tanah (Kebun Sawit)", "deskripsi": "SHGU No.12, LT 20 Ha, Kab. Kampar, Riau", "nilai": 3200000000, "status_pengikatan": "APHT"}]},
]


async def seed_database():
    dept = await db.users.find_one({"username": "depthead"})
    if not dept:
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "username": "depthead", "nama": "Teguh Sutadi",
            "email": "rizal.250783@gmail.com", "password_hash": hash_password("DeptHead2026!"),
            "role": "dept_head", "aktif": True, "created_at": datetime.now(timezone.utc).isoformat()})
    else:
        upd = {}
        if not verify_password("DeptHead2026!", dept["password_hash"]):
            upd["password_hash"] = hash_password("DeptHead2026!")
        if dept.get("nama") != "Teguh Sutadi":
            upd["nama"] = "Teguh Sutadi"
        if upd:
            await db.users.update_one({"username": "depthead"}, {"$set": upd})
    adm = await db.users.find_one({"username": "admin"})
    if not adm:
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "username": "admin", "nama": "Maya Dewi Maharani",
            "password_hash": hash_password("Admin2026!"), "role": "admin_legal",
            "aktif": True, "created_at": datetime.now(timezone.utc).isoformat()})
    else:
        upd = {}
        if not verify_password("Admin2026!", adm["password_hash"]):
            upd["password_hash"] = hash_password("Admin2026!")
        if adm.get("nama") != "Maya Dewi Maharani":
            upd["nama"] = "Maya Dewi Maharani"
        if upd:
            await db.users.update_one({"username": "admin"}, {"$set": upd})
    if not await db.users.find_one({"username": "arsya"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "username": "arsya", "nama": "Arsya Daniswara Dwitama",
            "password_hash": hash_password("Arsya2026!"), "role": "admin_legal",
            "aktif": True, "created_at": datetime.now(timezone.utc).isoformat()})
    await db.users.create_index("username", unique=True)
    await db.cases.create_index("nomor_perkara", unique=True)


@app.on_event("startup")
async def startup():
    await seed_database()


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

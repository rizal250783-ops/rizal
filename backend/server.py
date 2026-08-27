import os
import re
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone, date, timedelta

from dotenv import load_dotenv
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional, List
import io

import constants as C
from auth import (hash_password, verify_password, generate_password, create_token,
                  decode_token, get_token_from_request)
from decision import route_note, status_for_stage
from seed import seed_all
from pdf_gen import generate_note_pdf
from excel_export import export_notes_excel

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="RCG Digital Restructuring")
api = APIRouter(prefix="/api")
logger = logging.getLogger("rcg")
logging.basicConfig(level=logging.INFO)

NO_ID = {"_id": 0}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def now_parts():
    d = datetime.now(timezone.utc) + timedelta(hours=7)  # WIB
    return d.strftime("%d/%m/%Y"), d.strftime("%H:%M")


# ---------------- Auth dependency ----------------
async def current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token tidak valid atau kedaluwarsa")
    user = await db.users.find_one({"id": payload.get("sub")}, NO_ID)
    if not user or user.get("status") != "aktif":
        raise HTTPException(status_code=401, detail="User tidak ditemukan / nonaktif")
    user.pop("password_hash", None)
    return user


def require_roles(*roles):
    async def dep(user: dict = Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Akses ditolak")
        return user
    return dep


async def audit(user, action, entity, entity_id, old=None, new=None):
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()), "user_id": user["id"], "nip": user["nip"], "nama": user["nama"],
        "action": action, "entity": entity, "entity_id": entity_id,
        "old_value": old, "new_value": new, "created_at": now_iso(),
    })


async def notify(user_ids, note, message):
    d, t = now_parts()
    docs = []
    for uid in set(user_ids):
        docs.append({
            "id": str(uuid.uuid4()), "user_id": uid, "note_id": note["id"],
            "nomor_nota": note.get("nomor_nota", ""), "nama_nasabah": note.get("customer", {}).get("nama", ""),
            "pengirim": note.get("_actor", ""), "message": message,
            "tanggal": d, "jam": t, "is_read": False, "created_at": now_iso(),
        })
    if docs:
        await db.notifications.insert_many(docs)


# =============================================================
#  AUTH
# =============================================================
class LoginReq(BaseModel):
    nip: str
    password: str


class ChangePwReq(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


@api.post("/auth/login")
async def login(req: LoginReq):
    user = await db.users.find_one({"nip": req.nip.strip()})
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="NIP atau password salah")
    if user.get("status") != "aktif":
        raise HTTPException(status_code=403, detail="Akun nonaktif")
    token = create_token(user["id"], user["nip"])
    await audit(user, "login", "auth", user["id"])
    user.pop("password_hash", None)
    user.pop("_id", None)
    return {"token": token, "user": user}


@api.get("/auth/me")
async def me(user: dict = Depends(current_user)):
    return user


@api.post("/auth/change-password")
async def change_password(req: ChangePwReq, user: dict = Depends(current_user)):
    full = await db.users.find_one({"id": user["id"]})
    if not verify_password(req.old_password, full.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Password lama salah")
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Konfirmasi password tidak cocok")
    if not (1 <= len(req.new_password) <= 8):
        raise HTTPException(status_code=400, detail="Password maksimal 8 karakter")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_password(req.new_password), "initial_password": None, "updated_at": now_iso()}})
    await audit(user, "change_password", "user", user["id"])
    return {"ok": True}


# =============================================================
#  REFERENCE & MASTER
# =============================================================
@api.get("/reference")
async def reference(user: dict = Depends(current_user)):
    return {
        "segmen": C.SEGMEN, "produk": C.PRODUK, "akad": C.AKAD,
        "kolektibilitas": C.KOLEKTIBILITAS, "kepada": C.KEPADA,
        "penilai_jaminan": C.PENILAI_JAMINAN, "kemampuan_bayar": C.KEMAMPUAN_BAYAR,
        "rac_konsumer": C.RAC_KONSUMER, "rac_retail": C.RAC_RETAIL,
        "document_types": C.DOCUMENT_TYPES, "restrukturisasi_ke": list(range(1, 11)),
        "rcg_cap": C.RCG_CAP,
    }


@api.get("/regions")
async def regions(user: dict = Depends(current_user)):
    return await db.regions.find({}, NO_ID).sort("nama", 1).to_list(100)


@api.get("/areas")
async def areas(region: Optional[str] = None, user: dict = Depends(current_user)):
    q = {"region": region} if region else {}
    return await db.areas.find(q, NO_ID).sort("nama", 1).to_list(500)


@api.get("/branches")
async def branches(area: Optional[str] = None, user: dict = Depends(current_user)):
    q = {}
    if area:
        q["area"] = area
    elif user["role"] == "RCO":
        q["area"] = user.get("area")
    return await db.branches.find(q, NO_ID).sort("nama_cabang", 1).to_list(2000)


# ---- Holidays ----
class HolidayReq(BaseModel):
    tanggal: str
    keterangan: str


@api.get("/holidays")
async def get_holidays(user: dict = Depends(current_user)):
    return await db.holidays.find({}, NO_ID).sort("tanggal", 1).to_list(500)


@api.post("/holidays")
async def add_holiday(req: HolidayReq, user: dict = Depends(require_roles("RCG"))):
    doc = {"id": str(uuid.uuid4()), "tanggal": req.tanggal, "keterangan": req.keterangan}
    await db.holidays.insert_one(doc)
    await audit(user, "add_holiday", "holiday", doc["id"], None, doc)
    doc.pop("_id", None)
    return doc


@api.delete("/holidays/{hid}")
async def del_holiday(hid: str, user: dict = Depends(require_roles("RCG"))):
    await db.holidays.delete_one({"id": hid})
    await audit(user, "delete_holiday", "holiday", hid)
    return {"ok": True}


# =============================================================
#  USER MANAGEMENT (RCG)
# =============================================================
class UserReq(BaseModel):
    nama: str
    nip: str
    role: str  # RCO/ACRM/RCRM/RCG
    jabatan: Optional[str] = None
    region: Optional[str] = None
    area: Optional[str] = None
    limit_pemutus: Optional[float] = 0
    status: Optional[str] = "aktif"


def sanitize_user(u):
    u = dict(u)
    u.pop("password_hash", None)
    u.pop("_id", None)
    return u


@api.get("/users")
async def list_users(role: Optional[str] = None, region: Optional[str] = None,
                     area: Optional[str] = None, user: dict = Depends(require_roles("RCG"))):
    q = {}
    if role:
        q["role"] = role
    if region:
        q["region"] = region
    if area:
        q["area"] = area
    users = await db.users.find(q, {"_id": 0, "password_hash": 0}).sort("nama", 1).to_list(2000)
    return users


@api.post("/users")
async def create_user(req: UserReq, user: dict = Depends(require_roles("RCG"))):
    if not user.get("is_user_admin"):
        raise HTTPException(status_code=403, detail="Hanya SYAMSU RIZAL yang dapat menambah user")
    if req.role not in ("RCO", "ACRM", "RCRM", "RCG"):
        raise HTTPException(status_code=400, detail="Role tidak valid")
    if await db.users.find_one({"nip": req.nip.strip()}):
        raise HTTPException(status_code=400, detail="NIP sudah terdaftar")
    region, area = req.region, req.area
    if req.role in ("RCO", "ACRM"):
        if not area:
            raise HTTPException(status_code=400, detail="Area wajib diisi")
        arow = await db.areas.find_one({"nama": area})
        region = arow["region"] if arow else region
        if req.role == "ACRM" and not req.limit_pemutus:
            raise HTTPException(status_code=400, detail="Limit pemutus wajib untuk ACRM")
    elif req.role == "RCRM":
        if not region:
            raise HTTPException(status_code=400, detail="Region wajib diisi")
        if not req.limit_pemutus:
            raise HTTPException(status_code=400, detail="Limit pemutus wajib untuk RCRM")
    pw = generate_password(8)
    doc = {
        "id": str(uuid.uuid4()), "nip": req.nip.strip(), "nama": req.nama, "role": req.role,
        "jabatan": req.jabatan or C.JABATAN.get(req.role, ""), "region": region,
        "area": area if req.role in ("RCO", "ACRM") else None,
        "limit_pemutus": req.limit_pemutus or 0, "can_approve": False, "is_user_admin": False,
        "status": req.status or "aktif", "password_hash": hash_password(pw), "initial_password": pw,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.users.insert_one(doc)
    await audit(user, "create_user", "user", doc["id"], None, {"nip": doc["nip"], "role": doc["role"]})
    return {"user": sanitize_user(doc), "generated_password": pw}


@api.put("/users/{uid}")
async def update_user(uid: str, req: UserReq, user: dict = Depends(require_roles("RCG"))):
    target = await db.users.find_one({"id": uid})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    upd = {"nama": req.nama, "jabatan": req.jabatan or target.get("jabatan"),
           "region": req.region, "area": req.area, "limit_pemutus": req.limit_pemutus or 0,
           "status": req.status or "aktif", "updated_at": now_iso()}
    await db.users.update_one({"id": uid}, {"$set": upd})
    await audit(user, "update_user", "user", uid, sanitize_user(target), upd)
    return {"ok": True}


@api.post("/users/{uid}/reset-password")
async def reset_password(uid: str, user: dict = Depends(require_roles("RCG"))):
    pw = generate_password(8)
    r = await db.users.update_one({"id": uid}, {"$set": {"password_hash": hash_password(pw), "initial_password": pw, "updated_at": now_iso()}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    await audit(user, "reset_password", "user", uid)
    return {"generated_password": pw}


@api.delete("/users/{uid}")
async def delete_user(uid: str, user: dict = Depends(require_roles("RCG"))):
    if not user.get("is_user_admin"):
        raise HTTPException(status_code=403, detail="Hanya SYAMSU RIZAL yang dapat menghapus user")
    target = await db.users.find_one({"id": uid})
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if target.get("nip") == C.IMMADHA_NIP:
        raise HTTPException(status_code=400, detail="User pemutus utama tidak dapat dihapus")
    await db.users.delete_one({"id": uid})
    await audit(user, "delete_user", "user", uid, {"nip": target["nip"]}, None)
    return {"ok": True}


# =============================================================
#  NOTES
# =============================================================
def num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def compute_financials(note):
    tp = tm = tpen = nilai = 0.0
    for f in note.get("facilities", []):
        op = num(f.get("os_pokok"))
        om = num(f.get("os_margin"))
        pen = num(f.get("penalty"))
        f["total_kewajiban"] = op + om + pen
        tp += op
        tm += om
        tpen += pen
        nilai += op
    note["total_os_pokok"] = tp
    note["total_os_margin"] = tm
    note["total_penalty"] = tpen
    note["total_kewajiban"] = tp + tm + tpen
    note["nilai_kewenangan_pemutus"] = nilai
    # collateral CCR
    for col in note.get("collaterals", []):
        tk = note["total_kewajiban"] or 1
        col["ccr_pasar"] = round(num(col.get("nilai_pasar")) / tk * 100, 2)
        col["ccr_likuidasi"] = round(num(col.get("nilai_likuidasi")) / tk * 100, 2)
    return note


def build_perihal(note):
    f = (note.get("facilities") or [{}])[0]
    c = note.get("customer", {})
    kols = ", ".join(sorted({x.get("kolektibilitas", "") for x in note.get("facilities", []) if x.get("kolektibilitas")}))
    return (f"RESTRUKTURISASI PEMBIAYAAN A.N. {c.get('nama','').upper()} SEGMEN {f.get('segmen','')} "
            f"({f.get('produk','')}) KOLEKTIBILITAS {kols} CABANG {f.get('nama_cabang','')}")


def build_nomor_nota(nomor_manual, area):
    short = (area or "").replace("Area ", "").strip()
    return f"06/{nomor_manual}-2/ACR {short}"


def duration_str(start, end):
    try:
        s = datetime.strptime(start, "%d/%m/%Y")
        e = datetime.strptime(end, "%d/%m/%Y")
        months = (e.year - s.year) * 12 + (e.month - s.month)
        if e.day < s.day:
            months -= 1
        y, m = divmod(max(months, 0), 12)
        parts = []
        if y:
            parts.append(f"{y} tahun")
        if m:
            parts.append(f"{m} bulan")
        return " ".join(parts) or "0 bulan"
    except Exception:
        return ""


async def enrich_note(note):
    """Fill auto-generated text sections for preview/pdf."""
    note = dict(note)
    note["dari"] = C.DARI
    note["perihal"] = build_perihal(note)
    note["pembuka"] = C.PEMBUKA
    note["syarat_akad"] = C.SYARAT_AKAD
    note["lainnya"] = C.LAINNYA
    note["lainnya_pelanggaran"] = C.LAINNYA_PELANGGARAN
    note["penutup"] = C.PENUTUP
    note["approved_keterangan"] = C.APPROVED_KETERANGAN
    c = note.get("customer", {})
    note["usulan_kalimat"] = (f"Berdasarkan uraian di atas, kami merekomendasikan permohonan restrukturisasi "
                              f"pembiayaan a.n. {c.get('nama','')} dengan syarat dan kondisi sebagai berikut:")
    # analysis auto
    a = note.get("analysis") or {}
    a.setdefault("profil", "Terpenuhi")
    a["karakter"] = C.KARAKTER_TEXT
    if note.get("has_fix_asset") and note.get("collaterals"):
        ccr = note["collaterals"][0].get("ccr_likuidasi", 0)
        a["informasi_jaminan"] = f"Terdapat jaminan fix asset dengan CCR Nilai Likuidasi sebesar {ccr}%"
    else:
        a["informasi_jaminan"] = "Tidak ada jaminan fix asset"
    a["tbo"] = "Terpenuhi, tidak ada TBO"
    note["analysis"] = a
    return note


def rbac_query(user):
    if user["role"] == "RCO":
        return {"creator_id": user["id"]}
    if user["role"] == "ACRM":
        return {"area": user.get("area")}
    if user["role"] == "RCRM":
        return {"region": user.get("region")}
    return {}  # RCG


def can_download(user, note):
    lvl = note.get("final_approver_level")
    role = user["role"]
    if note.get("status") != "Final Approved":
        return False
    if role == "RCO":
        return note.get("creator_id") == user["id"]
    if role == "ACRM":
        return note.get("area") == user.get("area")
    if role == "RCRM":
        return note.get("region") == user.get("region") and lvl in ("RCRM", "RCG")
    if role == "RCG":
        return lvl == "RCG"
    return False


@api.post("/notes")
async def create_note(payload: dict, user: dict = Depends(require_roles("RCO"))):
    nomor_manual = str(payload.get("nomor_manual", "")).strip()
    note = {
        "id": str(uuid.uuid4()),
        "nomor_manual": nomor_manual,
        "nomor_nota": build_nomor_nota(nomor_manual, user.get("area")) if nomor_manual else "",
        "creator_id": user["id"], "creator_nip": user["nip"], "creator_nama": user["nama"],
        "creator_jabatan": user.get("jabatan"),
        "area": user.get("area"), "region": user.get("region"),
        "tanggal_nota": now_parts()[0], "kepada": payload.get("kepada", ""),
        "reff_tanggal": payload.get("reff_tanggal", ""),
        "customer": payload.get("customer", {}),
        "facilities": payload.get("facilities", []),
        "has_fix_asset": payload.get("has_fix_asset", False),
        "collaterals": payload.get("collaterals", []),
        "rac": payload.get("rac", []),
        "analysis": payload.get("analysis", {}),
        "proposals": payload.get("proposals", []),
        "documents": payload.get("documents", []),
        "risk_assessment": {"status": "Belum dilakukan", "file_path": None, "uploaded_at": None},
        "status": "Draft", "stages": [], "stage_index": 0,
        "normal_approver_level": None, "final_approver_level": None, "ra_required": False,
        "rac_ok": True, "approvals": [], "read_only": False,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    compute_financials(note)
    await db.notes.insert_one(note)
    await audit(user, "create_note", "note", note["id"])
    note.pop("_id", None)
    return note


@api.put("/notes/{nid}")
async def update_note(nid: str, payload: dict, user: dict = Depends(require_roles("RCO"))):
    note = await db.notes.find_one({"id": nid})
    if not note:
        raise HTTPException(status_code=404, detail="Nota tidak ditemukan")
    if note["creator_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Bukan nota Anda")
    if note.get("status") == "Final Approved" or note.get("read_only"):
        raise HTTPException(status_code=400, detail="Nota final approved tidak dapat diubah")
    editable = note.get("status") == "Draft" or note.get("status", "").startswith("Revisi") or note.get("status", "").startswith("Reject")
    if not editable:
        raise HTTPException(status_code=400, detail="Nota sedang dalam proses approval, tidak dapat diedit")
    upd = {}
    for k in ["customer", "facilities", "has_fix_asset", "collaterals", "rac", "analysis", "proposals", "documents", "kepada", "reff_tanggal"]:
        if k in payload:
            upd[k] = payload[k]
    if "nomor_manual" in payload:
        upd["nomor_manual"] = str(payload["nomor_manual"]).strip()
        upd["nomor_nota"] = build_nomor_nota(upd["nomor_manual"], note["area"])
    merged = {**note, **upd}
    compute_financials(merged)
    for k in ["facilities", "collaterals", "total_os_pokok", "total_os_margin", "total_penalty", "total_kewajiban", "nilai_kewenangan_pemutus"]:
        upd[k] = merged[k]
    upd["updated_at"] = now_iso()
    await db.notes.update_one({"id": nid}, {"$set": upd})
    await audit(user, "edit_note", "note", nid)
    return await db.notes.find_one({"id": nid}, NO_ID)


def validate_for_submit(note):
    errs = []
    if not note.get("nomor_manual") or not note["nomor_manual"].isdigit() or len(note["nomor_manual"]) > 5:
        errs.append("Nomor nota harus angka maksimal 5 digit")
    c = note.get("customer", {})
    if not c.get("nama"):
        errs.append("Nama nasabah wajib")
    facs = note.get("facilities", [])
    if not facs:
        errs.append("Minimal 1 fasilitas pembiayaan (loan)")
    for i, f in enumerate(facs, 1):
        if not f.get("cif"):
            errs.append(f"Loan {i}: CIF wajib")
        if not f.get("nomor_loan"):
            errs.append(f"Loan {i}: Nomor Loan wajib")
        if not f.get("kolektibilitas"):
            errs.append(f"Loan {i}: Kolektibilitas wajib")
        if not f.get("segmen"):
            errs.append(f"Loan {i}: Segmen wajib")
        if not f.get("produk"):
            errs.append(f"Loan {i}: Produk wajib")
        if not f.get("akad"):
            errs.append(f"Loan {i}: Akad wajib")
        if not f.get("nama_cabang"):
            errs.append(f"Loan {i}: Nama Cabang wajib")
        if num(f.get("os_pokok")) < 0 or num(f.get("os_margin")) < 0 or num(f.get("penalty")) < 0:
            errs.append(f"Loan {i}: Nilai tidak boleh negatif")
    rac = note.get("rac", [])
    if not rac:
        errs.append("RAC wajib diisi")
    for r in rac:
        if r.get("status") == "Tidak Terpenuhi" and not r.get("keterangan"):
            errs.append(f"RAC '{r.get('parameter','')[:30]}...' wajib keterangan")
    # documents
    doc_keys = {d.get("document_type") for d in note.get("documents", []) if d.get("file_path")}
    for dt in C.DOCUMENT_TYPES:
        if dt.get("required") and dt["key"] not in doc_keys:
            errs.append(f"Dokumen wajib: {dt['label']}")
        if dt.get("required_if_fix_asset") and note.get("has_fix_asset") and dt["key"] not in doc_keys:
            errs.append(f"Dokumen wajib (fix asset): {dt['label']}")
    # proposal dates
    for i, p in enumerate(note.get("proposals", []), 1):
        if not p.get("tgl_mulai") or not p.get("tgl_akhir"):
            errs.append(f"Usulan Loan {i}: tanggal mulai/akhir wajib")
    return errs


async def get_limits(note):
    acrm = await db.users.find_one({"role": "ACRM", "area": note["area"], "status": "aktif"})
    rcrm = await db.users.find_one({"role": "RCRM", "region": note["region"], "status": "aktif"})
    return (acrm["limit_pemutus"] if acrm else 0), (rcrm["limit_pemutus"] if rcrm else 0), acrm, rcrm


@api.post("/notes/{nid}/submit")
async def submit_note(nid: str, user: dict = Depends(require_roles("RCO"))):
    note = await db.notes.find_one({"id": nid})
    if not note:
        raise HTTPException(status_code=404, detail="Nota tidak ditemukan")
    if note["creator_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Bukan nota Anda")
    if note.get("status") == "Final Approved":
        raise HTTPException(status_code=400, detail="Nota sudah final approved")
    compute_financials(note)
    errs = validate_for_submit(note)
    if errs:
        raise HTTPException(status_code=400, detail=errs)
    # uniqueness: area + nomor_manual (exclude self, exclude drafts? unique per submitted note)
    dup = await db.notes.find_one({"area": note["area"], "nomor_manual": note["nomor_manual"], "id": {"$ne": nid}, "status": {"$ne": "Draft"}})
    if dup:
        raise HTTPException(status_code=400, detail="Nomor nota sudah digunakan di area ini")
    rac_ok = all(r.get("status") == "Terpenuhi" for r in note.get("rac", []))
    acrm_limit, rcrm_limit, acrm, rcrm = await get_limits(note)
    routing = route_note(note["nilai_kewenangan_pemutus"], acrm_limit, rcrm_limit, rac_ok)
    stages = routing["stages"]
    # build proposals durasi
    props = note.get("proposals", [])
    for p in props:
        p["durasi"] = duration_str(p.get("tgl_mulai", ""), p.get("tgl_akhir", ""))
    d, t = now_parts()
    approval = {"user_id": user["id"], "nip": user["nip"], "nama": user["nama"], "role": "RCO",
                "jabatan": user.get("jabatan"), "fungsi": "Pengusul", "keputusan": "Submit",
                "catatan": "", "date": d, "time": t}
    status = status_for_stage(stages[0]) if stages else "Menunggu Review ACRM"
    upd = {
        "rac_ok": rac_ok, "normal_approver_level": routing["normal_approver_level"],
        "final_approver_level": routing["final_approver_level"], "ra_required": routing["ra_required"],
        "stages": stages, "stage_index": 0, "status": status, "proposals": props,
        "submitted_at": now_iso(), "updated_at": now_iso(),
        "$push_approval": approval,
    }
    upd.pop("$push_approval")
    await db.notes.update_one({"id": nid}, {"$set": upd, "$push": {"approvals": approval}})
    note["_actor"] = user["nama"]
    if routing["final_approver_level"] == "ABOVE_RCG":
        # notify RCG
        rcg_ids = [u["id"] async for u in db.users.find({"role": "RCG"})]
        await notify(rcg_ids, note, f"Nota {note['nomor_nota']} memerlukan eskalasi di atas RCG (nilai melebihi kewenangan).")
    await audit(user, "submit_note", "note", nid, None, {"status": status})
    return await db.notes.find_one({"id": nid}, NO_ID)


class ActionReq(BaseModel):
    decision: str  # forward | approve | reject | revisi
    catatan: Optional[str] = ""


@api.post("/notes/{nid}/action")
async def note_action(nid: str, req: ActionReq, user: dict = Depends(current_user)):
    note = await db.notes.find_one({"id": nid})
    if not note:
        raise HTTPException(status_code=404, detail="Nota tidak ditemukan")
    if note.get("status") == "Final Approved":
        raise HTTPException(status_code=400, detail="Nota sudah final approved")
    stages = note.get("stages", [])
    idx = note.get("stage_index", 0)
    if idx >= len(stages):
        raise HTTPException(status_code=400, detail="Tidak ada tahap untuk diproses")
    stage = stages[idx]
    level, action = stage[0], stage[1]
    # authorization per stage
    if level == "ACRM":
        if not (user["role"] == "ACRM" and user.get("area") == note["area"]):
            raise HTTPException(status_code=403, detail="Akses ditolak untuk tahap ini")
    elif level == "RCRM":
        if not (user["role"] == "RCRM" and user.get("region") == note["region"]):
            raise HTTPException(status_code=403, detail="Akses ditolak untuk tahap ini")
    elif level == "RCG":
        if user["nip"] != C.IMMADHA_NIP:
            raise HTTPException(status_code=403, detail="Approval RCG hanya oleh IMMADHA HANDY KUSUMA")
    elif level == "ESCALATION":
        raise HTTPException(status_code=400, detail="Nota memerlukan eskalasi di atas RCG, tidak dapat diproses")
    elif level == "RA":
        raise HTTPException(status_code=400, detail="Tahap Risk Assessment, gunakan menu Risk Assessment")

    d, t = now_parts()
    note["_actor"] = user["nama"]
    base_ap = {"user_id": user["id"], "nip": user["nip"], "nama": user["nama"], "role": user["role"],
               "jabatan": user.get("jabatan"), "catatan": req.catatan or "", "date": d, "time": t}

    if req.decision in ("reject", "revisi"):
        kind = "Reject" if req.decision == "reject" else "Revisi"
        status = f"{kind} oleh {level}"
        ap = {**base_ap, "fungsi": "Pemutus" if action == "decide" else "Reviewer", "keputusan": kind}
        await db.notes.update_one({"id": nid}, {"$set": {"status": status, "stage_index": 0, "read_only": False, "updated_at": now_iso()}, "$push": {"approvals": ap}})
        # notifications
        recip = [note["creator_id"]]
        if level == "RCRM":
            recip += [u["id"] async for u in db.users.find({"role": "ACRM", "area": note["area"]})]
        if level == "RCG":
            recip += [u["id"] async for u in db.users.find({"$or": [{"role": "ACRM", "area": note["area"]}, {"role": "RCRM", "region": note["region"]}]})]
        await notify(recip, note, f"Nota {note['nomor_nota']} dikembalikan oleh {level} untuk {'diperbaiki' if kind=='Revisi' else 'ditolak'}.")
        await audit(user, f"{kind.lower()}_note", "note", nid, None, {"status": status})
        return await db.notes.find_one({"id": nid}, NO_ID)

    # forward / approve -> advance
    if action == "review" and req.decision != "forward":
        raise HTTPException(status_code=400, detail="Tahap review hanya dapat forward/reject/revisi")
    if action == "decide" and req.decision != "approve":
        raise HTTPException(status_code=400, detail="Tahap keputusan gunakan approve/reject/revisi")

    fungsi = "Pemutus" if action == "decide" else "Pengusul"
    keputusan = "Approved" if action == "decide" else "Forward"
    ap = {**base_ap, "fungsi": fungsi, "keputusan": keputusan}
    new_idx = idx + 1

    if action == "decide":
        # finalize
        limit_used = {"ACRM": None, "RCRM": None, "RCG": None}
        acrm_limit, rcrm_limit, _, _ = await get_limits(note)
        lu = {"ACRM": acrm_limit, "RCRM": rcrm_limit, "RCG": user.get("limit_pemutus", 0)}.get(level, 0)
        adate, atime = d, t
        upd = {
            "status": "Final Approved", "read_only": True, "stage_index": new_idx,
            "final_approver_id": user["id"], "final_approver_nama": user["nama"], "final_approver_nip": user["nip"],
            "final_approver_jabatan": user.get("jabatan"), "approved_at": now_iso(),
            "approved_date": adate, "approved_time": atime, "limit_pemutus_used": lu,
            "updated_at": now_iso(),
        }
        await db.notes.update_one({"id": nid}, {"$set": upd, "$push": {"approvals": ap}})
        await notify([note["creator_id"]], note, f"Nota {note['nomor_nota']} telah FINAL APPROVED oleh {user['nama']}.")
        await audit(user, "approve_note", "note", nid, None, {"status": "Final Approved"})
        return await db.notes.find_one({"id": nid}, NO_ID)

    # review forward -> next stage
    next_stage = stages[new_idx]
    status = status_for_stage(next_stage)
    await db.notes.update_one({"id": nid}, {"$set": {"stage_index": new_idx, "status": status, "updated_at": now_iso()}, "$push": {"approvals": ap}})
    await audit(user, "forward_note", "note", nid, None, {"status": status})
    return await db.notes.find_one({"id": nid}, NO_ID)


class RAReq(BaseModel):
    status: str  # Belum dilakukan | Dalam proses | Selesai
    file_path: Optional[str] = None


@api.post("/notes/{nid}/risk-assessment")
async def set_risk_assessment(nid: str, req: RAReq, user: dict = Depends(require_roles("RCG"))):
    note = await db.notes.find_one({"id": nid})
    if not note:
        raise HTTPException(status_code=404, detail="Nota tidak ditemukan")
    ra = {"status": req.status, "file_path": req.file_path or note.get("risk_assessment", {}).get("file_path"), "uploaded_at": now_iso()}
    upd = {"risk_assessment": ra, "updated_at": now_iso()}
    stages = note.get("stages", [])
    idx = note.get("stage_index", 0)
    if req.status == "Selesai" and idx < len(stages) and stages[idx][0] == "RA":
        new_idx = idx + 1
        upd["stage_index"] = new_idx
        upd["status"] = status_for_stage(stages[new_idx])
    await db.notes.update_one({"id": nid}, {"$set": upd})
    await audit(user, "risk_assessment", "note", nid, None, {"ra_status": req.status})
    return await db.notes.find_one({"id": nid}, NO_ID)


@api.get("/notes")
async def list_notes(status: Optional[str] = None, area: Optional[str] = None,
                     region: Optional[str] = None, segmen: Optional[str] = None,
                     cabang: Optional[str] = None, q: Optional[str] = None,
                     user: dict = Depends(current_user)):
    query = rbac_query(user)
    if status:
        query["status"] = status
    if area and user["role"] in ("RCRM", "RCG"):
        query["area"] = area
    if region and user["role"] == "RCG":
        query["region"] = region
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [
            {"nomor_nota": rx},
            {"customer.nama": rx},
            {"facilities.nama_cabang": rx},
        ]
    notes = await db.notes.find(query, NO_ID).sort("updated_at", -1).to_list(2000)
    if segmen:
        notes = [n for n in notes if any(f.get("segmen") == segmen for f in n.get("facilities", []))]
    if cabang:
        notes = [n for n in notes if any((f.get("nama_cabang") or "") == cabang for f in n.get("facilities", []))]
    return notes


@api.get("/notes/{nid}")
async def get_note(nid: str, user: dict = Depends(current_user)):
    note = await db.notes.find_one({"id": nid}, NO_ID)
    if not note:
        raise HTTPException(status_code=404, detail="Nota tidak ditemukan")
    # RBAC view
    rq = rbac_query(user)
    for k, v in rq.items():
        if note.get(k) != v:
            raise HTTPException(status_code=403, detail="Akses ditolak")
    enriched = await enrich_note(note)
    enriched["can_download"] = can_download(user, note)
    return enriched


@api.get("/notes/{nid}/pdf")
async def download_pdf(nid: str, request: Request):
    token = get_token_from_request(request)
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    user = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    note = await db.notes.find_one({"id": nid}, NO_ID)
    if not note:
        raise HTTPException(status_code=404, detail="Nota tidak ditemukan")
    if not can_download(user, note):
        raise HTTPException(status_code=403, detail="Anda tidak berhak mengunduh nota ini")
    enriched = await enrich_note(note)
    pdf = generate_note_pdf(enriched)
    await audit(user, "download_pdf", "note", nid)
    fname = f"Nota_{note['nomor_nota'].replace('/','_').replace(' ','_')}.pdf"
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={fname}"})


# ---- Upload ----
@api.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(current_user)):
    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".jpg", ".jpeg", ".png"):
        raise HTTPException(status_code=400, detail="Format harus PDF/JPG/JPEG/PNG")
    fname = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / fname
    content = await file.read()
    dest.write_bytes(content)
    return {"file_path": fname, "url": f"/api/files/{fname}", "original": file.filename}


@api.get("/files/{fname}")
async def get_file(fname: str):
    dest = UPLOAD_DIR / fname
    if not dest.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(str(dest))


# =============================================================
#  NOTIFICATIONS
# =============================================================
@api.get("/notifications")
async def get_notifications(user: dict = Depends(current_user)):
    items = await db.notifications.find({"user_id": user["id"]}, NO_ID).sort("created_at", -1).to_list(200)
    unread = sum(1 for i in items if not i.get("is_read"))
    return {"items": items, "unread": unread}


@api.post("/notifications/{nid}/read")
async def read_notif(nid: str, user: dict = Depends(current_user)):
    await db.notifications.update_one({"id": nid, "user_id": user["id"]}, {"$set": {"is_read": True}})
    return {"ok": True}


@api.post("/notifications/read-all")
async def read_all(user: dict = Depends(current_user)):
    await db.notifications.update_many({"user_id": user["id"]}, {"$set": {"is_read": True}})
    return {"ok": True}


# =============================================================
#  DASHBOARD & MONITORING
# =============================================================
def agg_financials(notes):
    return {
        "total_nota": len(notes),
        "total_loan": sum(len(n.get("facilities", [])) for n in notes),
        "total_os_pokok": sum(num(n.get("total_os_pokok")) for n in notes),
        "total_os_margin": sum(num(n.get("total_os_margin")) for n in notes),
        "total_penalty": sum(num(n.get("total_penalty")) for n in notes),
        "total_kewajiban": sum(num(n.get("total_kewajiban")) for n in notes),
    }


@api.get("/dashboard")
async def dashboard(user: dict = Depends(current_user)):
    q = rbac_query(user)
    notes = await db.notes.find(q, NO_ID).to_list(5000)
    by_status = {}
    for n in notes:
        by_status[n.get("status", "Draft")] = by_status.get(n.get("status", "Draft"), 0) + 1
    result = {"role": user["role"], "summary": agg_financials(notes), "by_status": by_status}

    def status_group(pred):
        return sum(1 for n in notes if pred(n.get("status", "")))

    result["cards"] = {
        "draft": status_group(lambda s: s == "Draft"),
        "menunggu": status_group(lambda s: s.startswith("Menunggu")),
        "revisi_reject": status_group(lambda s: s.startswith("Revisi") or s.startswith("Reject")),
        "approved": status_group(lambda s: s == "Final Approved"),
        "eskalasi": status_group(lambda s: s.startswith("Memerlukan")),
    }

    # breakdowns
    if user["role"] in ("RCRM", "RCG"):
        by_area = {}
        for n in notes:
            a = n.get("area", "-")
            g = by_area.setdefault(a, {"area": a, "region": n.get("region"), "nota": 0, "loan": 0, "os_pokok": 0, "os_margin": 0, "penalty": 0, "kewajiban": 0})
            g["nota"] += 1
            g["loan"] += len(n.get("facilities", []))
            g["os_pokok"] += num(n.get("total_os_pokok"))
            g["os_margin"] += num(n.get("total_os_margin"))
            g["penalty"] += num(n.get("total_penalty"))
            g["kewajiban"] += num(n.get("total_kewajiban"))
        result["by_area"] = list(by_area.values())
    if user["role"] == "RCG":
        by_region = {}
        for n in notes:
            r = n.get("region", "-")
            g = by_region.setdefault(r, {"region": r, "nota": 0, "loan": 0, "os_pokok": 0, "os_margin": 0, "penalty": 0, "kewajiban": 0})
            g["nota"] += 1
            g["loan"] += len(n.get("facilities", []))
            g["os_pokok"] += num(n.get("total_os_pokok"))
            g["os_margin"] += num(n.get("total_os_margin"))
            g["penalty"] += num(n.get("total_penalty"))
            g["kewajiban"] += num(n.get("total_kewajiban"))
        result["by_region"] = list(by_region.values())
        # nota per bulan
        by_month = {}
        for n in notes:
            ca = (n.get("submitted_at") or n.get("created_at") or "")[:7]
            by_month[ca] = by_month.get(ca, 0) + 1
        result["by_month"] = [{"bulan": k, "nota": v} for k, v in sorted(by_month.items())]
    if user["role"] == "ACRM":
        by_rco = {}
        for n in notes:
            g = by_rco.setdefault(n.get("creator_nama", "-"), {"rco": n.get("creator_nama"), "nota": 0, "kewajiban": 0})
            g["nota"] += 1
            g["kewajiban"] += num(n.get("total_kewajiban"))
        result["by_rco"] = list(by_rco.values())
    return result


@api.get("/monitoring")
async def monitoring(user: dict = Depends(require_roles("RCRM", "RCG")),
                     region: Optional[str] = None, area: Optional[str] = None,
                     segmen: Optional[str] = None, produk: Optional[str] = None,
                     kolektibilitas: Optional[str] = None, status: Optional[str] = None):
    q = rbac_query(user)
    if region and user["role"] == "RCG":
        q["region"] = region
    if area:
        q["area"] = area
    if status:
        q["status"] = status
    notes = await db.notes.find(q, NO_ID).to_list(5000)

    seg_stats = {s: {"segmen": s, "nota": 0, "loan": 0, "os_pokok": 0, "os_margin": 0, "penalty": 0, "kewajiban": 0} for s in C.SEGMEN}
    prod_stats = {}
    for n in notes:
        seen_seg = set()
        for f in n.get("facilities", []):
            s = f.get("segmen")
            p = f.get("produk")
            if segmen and s != segmen:
                continue
            if produk and p != produk:
                continue
            if kolektibilitas and f.get("kolektibilitas") != kolektibilitas:
                continue
            op, om, pen = num(f.get("os_pokok")), num(f.get("os_margin")), num(f.get("penalty"))
            if s in seg_stats:
                g = seg_stats[s]
                g["loan"] += 1
                g["os_pokok"] += op
                g["os_margin"] += om
                g["penalty"] += pen
                g["kewajiban"] += op + om + pen
                if s not in seen_seg:
                    g["nota"] += 1
                    seen_seg.add(s)
            key = f"{s}|{p}"
            pg = prod_stats.setdefault(key, {"segmen": s, "produk": p, "nota": 0, "loan": 0, "os_pokok": 0, "os_margin": 0, "penalty": 0, "kewajiban": 0, "_notes": set()})
            pg["loan"] += 1
            pg["os_pokok"] += op
            pg["os_margin"] += om
            pg["penalty"] += pen
            pg["kewajiban"] += op + om + pen
            pg["_notes"].add(n["id"])
    for pg in prod_stats.values():
        pg["nota"] = len(pg.pop("_notes"))
    return {"per_segmen": list(seg_stats.values()), "per_produk": list(prod_stats.values())}


@api.get("/audit")
async def audit_logs(user: dict = Depends(require_roles("RCG")), limit: int = 300):
    return await db.audit_logs.find({}, NO_ID).sort("created_at", -1).to_list(limit)


@api.get("/export/excel")
async def export_excel(request: Request, region: Optional[str] = None, area: Optional[str] = None):
    token = get_token_from_request(request)
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    user = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0, "password_hash": 0})
    if not user or user["role"] not in ("RCRM", "RCG"):
        raise HTTPException(status_code=403, detail="Akses ditolak")
    q = rbac_query(user)
    if area:
        q["area"] = area
    if region and user["role"] == "RCG":
        q["region"] = region
    notes = await db.notes.find(q, NO_ID).sort("updated_at", -1).to_list(5000)
    data = export_notes_excel(notes)
    await audit(user, "export_excel", "note", "-")
    return StreamingResponse(io.BytesIO(data),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=Export_Nota_RCG.xlsx"})


@api.get("/")
async def root():
    return {"app": "RCG Digital Restructuring", "status": "ok"}


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("nip", unique=True)
    await db.notes.create_index("creator_id")
    await db.notes.create_index([("area", 1), ("nomor_manual", 1)])
    await seed_all(db)
    logger.info("Seeding complete")


@app.on_event("shutdown")
async def shutdown():
    client.close()

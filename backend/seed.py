"""Idempotent DB seeding from Excel-derived JSON + RCG master users."""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from auth import hash_password
from constants import RCG_USERS, JABATAN

SEED_DIR = Path(__file__).parent / "seed_data"
DEFAULT_PASSWORD = "bsi12345"


def _now():
    return datetime.now(timezone.utc).isoformat()


async def seed_all(db):
    await _seed_regions_areas(db)
    await _seed_branches(db)
    await _seed_users(db)


async def _seed_regions_areas(db):
    if await db.regions.count_documents({}) > 0:
        return
    data = json.load(open(SEED_DIR / "seed_regions_areas.json"))
    regions, areas = [], []
    for item in data:
        rid = str(uuid.uuid4())
        regions.append({"id": rid, "nama": item["region"]})
        for a in item["areas"]:
            areas.append({"id": str(uuid.uuid4()), "region_id": rid, "region": item["region"], "nama": a})
    if regions:
        await db.regions.insert_many(regions)
    if areas:
        await db.areas.insert_many(areas)


async def _seed_branches(db):
    if await db.branches.count_documents({}) > 0:
        return
    data = json.load(open(SEED_DIR / "seed_branches.json"))
    docs = []
    for b in data:
        docs.append({
            "id": str(uuid.uuid4()),
            "id_cabang": b["id_cabang"],
            "kode_outlet_bsi": b["kode_outlet_bsi"],
            "nama_cabang": b["nama_cabang"],
            "jenis_outlet": b["jenis_outlet"],
            "area": b["area"],
            "region": b["region"],
            "status": "aktif",
        })
    if docs:
        await db.branches.insert_many(docs)


async def _seed_users(db):
    pw_hash = hash_password(DEFAULT_PASSWORD)

    # RCG master users
    for u in RCG_USERS:
        existing = await db.users.find_one({"nip": u["nip"]})
        doc = {
            "nip": u["nip"],
            "nama": u["nama"],
            "role": "RCG",
            "jabatan": u["jabatan"],
            "region": None,
            "area": None,
            "limit_pemutus": u["limit_pemutus"],
            "can_approve": u["can_approve"],
            "is_user_admin": u.get("is_user_admin", False),
            "status": "aktif",
        }
        if existing is None:
            doc.update({"id": str(uuid.uuid4()), "password_hash": pw_hash, "initial_password": DEFAULT_PASSWORD, "created_at": _now(), "updated_at": _now()})
            await db.users.insert_one(doc)
        else:
            await db.users.update_one({"nip": u["nip"]}, {"$set": {k: doc[k] for k in ["can_approve", "is_user_admin", "limit_pemutus", "jabatan", "role"]}})

    # RCO / ACRM / RCRM from parsed Excel
    data = json.load(open(SEED_DIR / "seed_users.json"))
    for u in data:
        if not u.get("nip"):
            continue
        existing = await db.users.find_one({"nip": u["nip"]})
        if existing is not None:
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "nip": u["nip"],
            "nama": u["nama"],
            "role": u["role"],
            "jabatan": JABATAN.get(u["role"], ""),
            "region": u.get("region"),
            "area": u.get("area"),
            "limit_pemutus": u.get("limit", 0) or 0,
            "can_approve": False,
            "is_user_admin": False,
            "status": "aktif",
            "password_hash": pw_hash,
            "initial_password": DEFAULT_PASSWORD,
            "created_at": _now(),
            "updated_at": _now(),
        }
        await db.users.insert_one(doc)

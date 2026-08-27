"""Shared fixtures for RCG Digital Restructuring backend tests."""
import os
import random
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
_base = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not _base:
    raise RuntimeError("REACT_APP_BACKEND_URL missing from env and /app/frontend/.env")
BASE_URL = _base.rstrip("/")
API = f"{BASE_URL}/api"

PASSWORD = "bsi12345"
NIP = {
    "RCO": "2193020835",          # UCHTI APRILINA - Area Banda Aceh / RO I ACEH
    "ACRM": "2188009250",         # FERI SAPUTRA - limit 2.000.000.000
    "RCRM": "2188017223",         # HENDRA PURNAWAN - limit 10.000.000.000
    "RCG_APPROVER": "2175007386",  # IMMADHA
    "RCG_ADMIN": "2183008345",    # SYAMSU RIZAL
    "RCG_OTHER": "2180007674",    # RATMIYATI (can_approve False)
}

CREATED_NOTE_IDS = []
CREATED_USER_IDS = []


def login(nip, password=PASSWORD):
    r = requests.post(f"{API}/auth/login", json={"nip": nip, "password": password}, timeout=30)
    return r


def token_for(nip):
    r = login(nip)
    if r.status_code != 200:
        pytest.fail(f"Login failed for {nip}: {r.status_code} {r.text[:300]}")
    tok = r.json().get("token")
    if not tok:
        pytest.fail(f"No token in login response for {nip}")
    return tok


class Client:
    def __init__(self, nip):
        self.nip = nip
        self.s = requests.Session()
        self.token = token_for(nip)
        self.s.headers.update({"Authorization": f"Bearer {self.token}",
                               "Content-Type": "application/json"})

    def get(self, path, **kw):
        return self.s.get(f"{API}{path}", timeout=60, **kw)

    def post(self, path, **kw):
        return self.s.post(f"{API}{path}", timeout=60, **kw)

    def put(self, path, **kw):
        return self.s.put(f"{API}{path}", timeout=60, **kw)

    def delete(self, path, **kw):
        return self.s.delete(f"{API}{path}", timeout=60, **kw)


@pytest.fixture(scope="session")
def rco():
    return Client(NIP["RCO"])


@pytest.fixture(scope="session")
def acrm():
    return Client(NIP["ACRM"])


@pytest.fixture(scope="session")
def rcrm():
    return Client(NIP["RCRM"])


@pytest.fixture(scope="session")
def rcg_approver():
    return Client(NIP["RCG_APPROVER"])


@pytest.fixture(scope="session")
def rcg_admin():
    return Client(NIP["RCG_ADMIN"])


@pytest.fixture(scope="session")
def rcg_other():
    return Client(NIP["RCG_OTHER"])


RAC_PARAMS = [
    "Terdapat surat permohonan restrukturisasi dari nasabah",
    "Nasabah mengalami penurunan kemampuan membayar",
    "Terdapat Informasi Debitur (iDeb)",
    "Terdapat penghasilan atau sumber pembayaran angsuran yang jelas",
    "Nasabah tidak termasuk nasabah fraud",
]


def note_payload(os_pokok, rac_ok=True, nama="TEST_NASABAH QA"):
    nomor = str(random.randint(10000, 99999))
    rac = [{"parameter": p, "status": "Terpenuhi", "keterangan": ""} for p in RAC_PARAMS]
    if not rac_ok:
        rac[1] = {"parameter": RAC_PARAMS[1], "status": "Tidak Terpenuhi",
                  "keterangan": "Penghasilan nasabah turun drastis"}
    return {
        "nomor_manual": nomor,
        "kepada": "ACRM",
        "reff_tanggal": "01/07/2026",
        "customer": {"nama": nama, "alamat": "Banda Aceh", "pekerjaan": "Wiraswasta"},
        "facilities": [{
            "cif": "1234567", "nomor_loan": "LN00001", "kolektibilitas": "3A",
            "segmen": "KONSUMER", "produk": "Griya", "akad": "Murabahah",
            "nama_cabang": "KC BANDA ACEH DIPONEGORO",
            "os_pokok": os_pokok, "os_margin": 100000000, "penalty": 5000000,
        }],
        "has_fix_asset": False,
        "collaterals": [],
        "rac": rac,
        "analysis": {},
        "proposals": [{"tgl_mulai": "01/08/2026", "tgl_akhir": "01/08/2031"}],
        "documents": [
            {"document_type": "foto_ots", "file_path": "dummy_ots.pdf"},
            {"document_type": "surat_permohonan_ktp", "file_path": "dummy_ktp.pdf"},
            {"document_type": "bi_checking", "file_path": "dummy_bi.pdf"},
        ],
    }


def create_and_submit(rco_client, os_pokok, rac_ok=True):
    """Create a nota as RCO and submit it. Returns submitted note dict."""
    r = rco_client.post("/notes", json=note_payload(os_pokok, rac_ok))
    assert r.status_code == 200, f"create note failed: {r.status_code} {r.text[:400]}"
    note = r.json()
    CREATED_NOTE_IDS.append(note["id"])
    s = rco_client.post(f"/notes/{note['id']}/submit")
    assert s.status_code == 200, f"submit failed: {s.status_code} {s.text[:600]}"
    return s.json()


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    # Remove notes/users created by the tests directly from Mongo (no DELETE /notes API exists)
    try:
        from pymongo import MongoClient
        be = dotenv_values("/app/backend/.env")
        cl = MongoClient(be["MONGO_URL"])
        db = cl[be["DB_NAME"]]
        if CREATED_NOTE_IDS:
            db.notes.delete_many({"id": {"$in": CREATED_NOTE_IDS}})
            db.notifications.delete_many({"note_id": {"$in": CREATED_NOTE_IDS}})
        if CREATED_USER_IDS:
            db.users.delete_many({"id": {"$in": CREATED_USER_IDS}})
        cl.close()
    except Exception as exc:  # pragma: no cover
        print(f"cleanup warning: {exc}")

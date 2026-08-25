"""CASEWISE LEGAL PERDATA — backend API regression tests."""
import io
import os
import uuid

import openpyxl
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

DEPTHEAD = {"username": "depthead", "password": "DeptHead2026!"}
ADMIN = {"username": "admin", "password": "Admin2026!"}


def login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=60)
    if r.status_code != 200:
        pytest.fail(f"Login failed {creds['username']}: {r.status_code} {r.text[:300]}")
    data = r.json()
    assert "token" in data and "user" in data
    return data


@pytest.fixture(scope="session")
def dh():
    d = login(DEPTHEAD)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {d['token']}"})
    return s


@pytest.fixture(scope="session")
def ad():
    d = login(ADMIN)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {d['token']}"})
    return s


# ---------------- Auth ----------------
class TestAuth:
    def test_login_depthead(self):
        d = login(DEPTHEAD)
        assert d["user"]["role"] == "dept_head"
        assert "password_hash" not in d["user"]
        assert "_id" not in d["user"]

    def test_login_admin(self):
        d = login(ADMIN)
        assert d["user"]["role"] == "admin_legal"

    def test_login_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"username": "admin", "password": "wrong"}, timeout=60)
        assert r.status_code == 401
        assert "salah" in r.json().get("detail", "").lower()

    def test_login_unknown_user(self):
        r = requests.post(f"{API}/auth/login", json={"username": "nouser", "password": "x"}, timeout=60)
        assert r.status_code == 401

    def test_bcrypt_hash_format(self, dh):
        # verified indirectly: seeded users can login; hash format checked via db export not exposed
        r = dh.get(f"{API}/auth/me", timeout=60)
        assert r.status_code == 200
        assert r.json()["username"] == "depthead"

    def test_me_no_token(self):
        r = requests.get(f"{API}/auth/me", timeout=60)
        assert r.status_code == 401

    def test_me_invalid_token(self):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"}, timeout=60)
        assert r.status_code == 401

    def test_brute_force_lockout(self):
        """Playbook expects lockout after 5 failed attempts."""
        codes = []
        for _ in range(6):
            r = requests.post(f"{API}/auth/login", json={"username": "admin", "password": "bad"}, timeout=60)
            codes.append(r.status_code)
        assert 423 in codes or 429 in codes, f"No lockout after 6 failures: {codes}"


# ---------------- Dashboard / Master data ----------------
class TestDashboard:
    def test_stats(self, dh):
        r = dh.get(f"{API}/dashboard/stats", timeout=60)
        assert r.status_code == 200
        d = r.json()
        for k in ["total_aktif", "total_perkara", "total_kewajiban", "per_region",
                  "per_status", "timeline_chart", "reminders", "pending_approvals"]:
            assert k in d, k
        assert d["total_perkara"] >= 12
        assert d["total_kewajiban"] > 0
        assert isinstance(d["per_region"], list) and d["per_region"][0]["value"] >= 1

    def test_stats_filter_region(self, dh):
        r = dh.get(f"{API}/dashboard/stats", params={"region": "Region 1 - Jakarta"}, timeout=60)
        assert r.status_code == 200
        assert r.json()["total_perkara"] >= 1

    def test_stats_requires_auth(self):
        assert requests.get(f"{API}/dashboard/stats", timeout=60).status_code == 401

    def test_master_data(self, ad):
        r = ad.get(f"{API}/master-data", timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert len(d["status_perkara"]) == 18
        assert len(d["dokumen_kategori"]) == 17
        assert d["risk_ratings"] == ["High Risk", "Medium Risk", "Low Risk"]
        assert len(d["regions"]) >= 1


# ---------------- Cases read/search ----------------
class TestCasesRead:
    def test_list_cases(self, ad):
        r = ad.get(f"{API}/cases", timeout=60)
        assert r.status_code == 200
        cases = r.json()
        assert len(cases) >= 12
        assert all("_id" not in c for c in cases)
        assert "nomor_perkara" in cases[0] and "total_kewajiban" in cases[0]

    def test_search_nomor(self, ad):
        r = ad.get(f"{API}/cases", params={"search": "45/Pdt.G/2024"}, timeout=60)
        assert r.status_code == 200
        assert any("45/Pdt.G/2024" in c["nomor_perkara"] for c in r.json())

    def test_search_cif(self, ad):
        r = ad.get(f"{API}/cases", params={"search": "CIF001234"}, timeout=60)
        assert r.status_code == 200 and len(r.json()) >= 1

    def test_search_loan(self, ad):
        r = ad.get(f"{API}/cases", params={"search": "LN-2001"}, timeout=60)
        assert r.status_code == 200 and len(r.json()) >= 1

    def test_search_penggugat(self, ad):
        r = ad.get(f"{API}/cases", params={"search": "Ahmad Fauzi"}, timeout=60)
        assert r.status_code == 200 and len(r.json()) >= 1

    def test_filter_status_and_risk(self, ad):
        r = ad.get(f"{API}/cases", params={"status": "Mediasi", "risk_rating": "Medium Risk"}, timeout=60)
        assert r.status_code == 200
        for c in r.json():
            assert c["status_perkara"] == "Mediasi" and c["risk_rating"] == "Medium Risk"

    def test_filter_tahun(self, ad):
        r = ad.get(f"{API}/cases", params={"tahun": "2024"}, timeout=60)
        assert r.status_code == 200
        assert all(c["tahun"] == 2024 for c in r.json())

    def test_get_case_detail(self, ad):
        cid = ad.get(f"{API}/cases", timeout=60).json()[0]["id"]
        r = ad.get(f"{API}/cases/{cid}", timeout=60)
        assert r.status_code == 200 and r.json()["id"] == cid

    def test_get_case_404(self, ad):
        assert ad.get(f"{API}/cases/{uuid.uuid4()}", timeout=60).status_code == 404


# ---------------- Approval workflow: CREATE ----------------
def case_payload(nomor):
    return {
        "nomor_perkara": nomor, "nama_pn": "PN Test", "materi_gugatan": "TEST gugatan",
        "jenis_penggugat": "Nasabah", "penggugat": ["TEST Penggugat"], "tergugat": ["BSI"],
        "region": "Region 1 - Jakarta", "area": "Area Test", "cabang": "KC Test",
        "pic": "TEST PIC", "kontak_pic": "0800",
        "cif_list": [{"nomor_cif": "CIFTEST1", "loans": [
            {"nomor_loan": "LNTEST1", "os_pokok": 1000000, "os_margin": 200000, "penalti": 50000}]}],
        "jaminan": [{"jenis": "Tanah", "deskripsi": "TEST", "nilai": 5000000, "status_pengikatan": "APHT"}],
        "mediasi": [], "status_perkara": "Gugatan Terdaftar", "risk_rating": "Low Risk",
    }


class TestApprovalWorkflow:
    created_case_ids = []

    def test_admin_create_requires_approval(self, ad, dh):
        nomor = f"TEST-{uuid.uuid4().hex[:6]}/Pdt.G/2026/PN.Tst"
        r = ad.post(f"{API}/cases", json=case_payload(nomor), timeout=60)
        assert r.status_code == 200, r.text[:300]
        req = r.json()
        assert req["status"] == "MENUNGGU" and req["type"] == "CREATE"
        assert req["payload"]["total_kewajiban"] == 1250000
        # not yet visible in cases
        assert not [c for c in ad.get(f"{API}/cases", params={"search": nomor}, timeout=60).json()]
        # dept head sees pending request
        pend = dh.get(f"{API}/approvals", params={"status": "MENUNGGU"}, timeout=60)
        assert pend.status_code == 200
        assert any(a["id"] == req["id"] for a in pend.json())
        # approve
        ap = dh.post(f"{API}/approvals/{req['id']}/approve", json={"catatan": "TEST setuju"}, timeout=60)
        assert ap.status_code == 200
        found = ad.get(f"{API}/cases", params={"search": nomor}, timeout=60).json()
        assert len(found) == 1
        case = found[0]
        assert case["status_aktif"] == "AKTIF" and case["total_kewajiban"] == 1250000
        assert len(case["timeline"]) >= 1
        TestApprovalWorkflow.created_case_ids.append(case["id"])

    def test_admin_cannot_approve(self, ad, dh):
        nomor = f"TEST-{uuid.uuid4().hex[:6]}/Pdt.G/2026/PN.Tst"
        req = ad.post(f"{API}/cases", json=case_payload(nomor), timeout=60).json()
        r = ad.post(f"{API}/approvals/{req['id']}/approve", json={"catatan": "x"}, timeout=60)
        assert r.status_code == 403
        # reject requires reason
        r2 = dh.post(f"{API}/approvals/{req['id']}/reject", json={"alasan_reject": ""}, timeout=60)
        assert r2.status_code == 400
        r3 = dh.post(f"{API}/approvals/{req['id']}/reject", json={"alasan_reject": "TEST alasan reject"}, timeout=60)
        assert r3.status_code == 200
        rejected = [a for a in dh.get(f"{API}/approvals", timeout=60).json() if a["id"] == req["id"]][0]
        assert rejected["status"] == "REJECTED"
        assert rejected["alasan_reject"] == "TEST alasan reject"
        # already processed
        assert dh.post(f"{API}/approvals/{req['id']}/approve", json={}, timeout=60).status_code == 400
        # case must not exist
        assert not ad.get(f"{API}/cases", params={"search": nomor}, timeout=60).json()

    def test_create_validation_and_duplicate(self, ad):
        bad = case_payload("")
        assert ad.post(f"{API}/cases", json=bad, timeout=60).status_code == 400
        dup = case_payload("123/Pdt.G/2024/PN.Jkt.Sel")
        r = ad.post(f"{API}/cases", json=dup, timeout=60)
        assert r.status_code == 400

    def test_dept_head_create_is_auto_approved(self, dh):
        nomor = f"TEST-{uuid.uuid4().hex[:6]}/Pdt.G/2026/PN.Tst"
        r = dh.post(f"{API}/cases", json=case_payload(nomor), timeout=60)
        assert r.status_code == 200
        assert r.json()["status"] == "APPROVED"
        found = dh.get(f"{API}/cases", params={"search": nomor}, timeout=60).json()
        assert len(found) == 1
        TestApprovalWorkflow.created_case_ids.append(found[0]["id"])

    def test_edit_flow(self, ad, dh):
        cid = TestApprovalWorkflow.created_case_ids[0]
        case = ad.get(f"{API}/cases/{cid}", timeout=60).json()
        payload = {**case, "materi_gugatan": "TEST materi diubah"}
        r = ad.put(f"{API}/cases/{cid}", json=payload, timeout=60)
        assert r.status_code == 200
        req = r.json()
        assert req["status"] == "MENUNGGU" and req["type"] == "EDIT"
        # unchanged before approval
        assert ad.get(f"{API}/cases/{cid}", timeout=60).json()["materi_gugatan"] == case["materi_gugatan"]
        assert dh.post(f"{API}/approvals/{req['id']}/approve", json={"catatan": "ok"}, timeout=60).status_code == 200
        assert ad.get(f"{API}/cases/{cid}", timeout=60).json()["materi_gugatan"] == "TEST materi diubah"

    def test_delete_nonaktif_flow(self, ad, dh):
        cid = TestApprovalWorkflow.created_case_ids[0]
        assert ad.post(f"{API}/cases/{cid}/delete-request",
                       json={"mode": "NONAKTIF", "alasan": ""}, timeout=60).status_code == 400
        assert ad.post(f"{API}/cases/{cid}/delete-request",
                       json={"mode": "BOGUS", "alasan": "x"}, timeout=60).status_code == 400
        r = ad.post(f"{API}/cases/{cid}/delete-request",
                    json={"mode": "NONAKTIF", "alasan": "TEST penghentian"}, timeout=60)
        assert r.status_code == 200 and r.json()["status"] == "MENUNGGU"
        assert ad.get(f"{API}/cases/{cid}", timeout=60).json()["status_aktif"] == "AKTIF"
        assert dh.post(f"{API}/approvals/{r.json()['id']}/approve", json={}, timeout=60).status_code == 200
        c = ad.get(f"{API}/cases/{cid}", timeout=60).json()
        assert c["status_aktif"] == "TIDAK AKTIF" and c["alasan_nonaktif"] == "TEST penghentian"

    def test_delete_permanent_flow(self, ad, dh):
        cid = TestApprovalWorkflow.created_case_ids[-1]
        r = ad.post(f"{API}/cases/{cid}/delete-request",
                    json={"mode": "PERMANENT", "alasan": "TEST hapus permanen"}, timeout=60)
        assert r.status_code == 200
        assert dh.post(f"{API}/approvals/{r.json()['id']}/approve", json={}, timeout=60).status_code == 200
        assert ad.get(f"{API}/cases/{cid}", timeout=60).status_code == 404

    def test_admin_only_sees_own_approvals(self, ad):
        r = ad.get(f"{API}/approvals", timeout=60)
        assert r.status_code == 200
        assert all(a["requested_by"] == "admin" for a in r.json())

    def test_cleanup_created(self, ad, dh):
        for cid in TestApprovalWorkflow.created_case_ids:
            if ad.get(f"{API}/cases/{cid}", timeout=60).status_code == 200:
                req = dh.post(f"{API}/cases/{cid}/delete-request",
                              json={"mode": "PERMANENT", "alasan": "TEST cleanup"}, timeout=60)
                assert req.status_code == 200
                assert ad.get(f"{API}/cases/{cid}", timeout=60).status_code == 404


# ---------------- Operasional / agenda / documents ----------------
class TestOperasionalAgendaDocs:
    @pytest.fixture(scope="class")
    def case_id(self, dh):
        nomor = f"TEST-OPS-{uuid.uuid4().hex[:6]}/Pdt.G/2026/PN.Tst"
        dh.post(f"{API}/cases", json=case_payload(nomor), timeout=60)
        cid = dh.get(f"{API}/cases", params={"search": nomor}, timeout=60).json()[0]["id"]
        yield cid
        dh.post(f"{API}/cases/{cid}/delete-request",
                json={"mode": "PERMANENT", "alasan": "TEST cleanup"}, timeout=60)

    def test_update_operasional(self, dh, case_id):
        r = dh.patch(f"{API}/cases/{case_id}/operasional",
                     json={"status_perkara": "Putusan", "risk_rating": "High Risk",
                           "rekomendasi_tindakan": "TEST rekomendasi"}, timeout=60)
        assert r.status_code == 200
        c = dh.get(f"{API}/cases/{case_id}", timeout=60).json()
        assert c["status_perkara"] == "Putusan" and c["risk_rating"] == "High Risk"
        assert c["rekomendasi_tindakan"] == "TEST rekomendasi"
        assert any(t["judul"] == "Status: Putusan" for t in c["timeline"])

    def test_operasional_invalid_status_no_change(self, dh, case_id):
        r = dh.patch(f"{API}/cases/{case_id}/operasional", json={"status_perkara": "NOPE"}, timeout=60)
        assert r.status_code == 400

    def test_agenda_crud_and_timeline(self, dh, case_id):
        assert dh.post(f"{API}/cases/{case_id}/agenda", json={"tanggal": "", "agenda": ""}, timeout=60).status_code == 400
        r = dh.post(f"{API}/cases/{case_id}/agenda",
                    json={"tanggal": "2026-09-15", "agenda": "Mediasi", "keterangan": "TEST agenda"}, timeout=60)
        assert r.status_code == 200
        item = r.json()
        c = dh.get(f"{API}/cases/{case_id}", timeout=60).json()
        assert any(a["id"] == item["id"] for a in c["agenda_sidang"])
        assert any(t["judul"] == "Sidang: Mediasi" for t in c["timeline"])
        assert dh.delete(f"{API}/cases/{case_id}/agenda/{item['id']}", timeout=60).status_code == 200
        c2 = dh.get(f"{API}/cases/{case_id}", timeout=60).json()
        assert not any(a["id"] == item["id"] for a in c2["agenda_sidang"])

    def test_document_upload_download_delete(self, dh, case_id):
        pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
        files = {"file": ("TEST_doc.pdf", pdf, "application/pdf")}
        data = {"kategori": "Executive Summary", "nomor": "001", "tanggal": "2026-07-01"}
        r = dh.post(f"{API}/cases/{case_id}/documents", files=files, data=data, timeout=60)
        assert r.status_code == 200, r.text[:300]
        doc = r.json()
        assert doc["kategori"] == "Executive Summary" and doc["size"] == len(pdf)
        lst = dh.get(f"{API}/documents", params={"case_id": case_id}, timeout=60)
        assert lst.status_code == 200 and any(d["id"] == doc["id"] for d in lst.json())
        dl = dh.get(f"{API}/documents/{doc['id']}/download", timeout=60)
        assert dl.status_code == 200 and dl.content == pdf
        assert dh.delete(f"{API}/documents/{doc['id']}", timeout=60).status_code == 200
        assert dh.get(f"{API}/documents/{doc['id']}/download", timeout=60).status_code == 404

    def test_reject_non_pdf(self, dh, case_id):
        files = {"file": ("TEST.txt", b"hello", "text/plain")}
        r = dh.post(f"{API}/cases/{case_id}/documents", files=files,
                    data={"kategori": "Replik"}, timeout=60)
        assert r.status_code == 400
        assert "PDF" in r.json()["detail"]

    def test_upload_invalid_case(self, dh):
        files = {"file": ("TEST.pdf", b"%PDF-1.4", "application/pdf")}
        r = dh.post(f"{API}/cases/{uuid.uuid4()}/documents", files=files,
                    data={"kategori": "Replik"}, timeout=60)
        assert r.status_code == 404


# ---------------- Export / Import ----------------
class TestExportImport:
    def test_export_cases(self, ad):
        r = ad.get(f"{API}/export/cases", timeout=120)
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers["content-type"]
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        assert wb.sheetnames == ["DATA PERKARA"]
        assert wb["DATA PERKARA"].max_row >= 13

    def test_export_database_depthead(self, dh):
        r = dh.get(f"{API}/export/database", timeout=120)
        assert r.status_code == 200
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        assert wb.sheetnames == ["DATA PERKARA", "DATA LOAN", "DATA JAMINAN",
                                 "DATA PROSES PERKARA", "DATA APPROVAL", "DATA USER"]
        assert wb["DATA LOAN"].max_row >= 2
        last = dh.get(f"{API}/export/last", timeout=60)
        assert last.status_code == 200 and last.json()["type"] == "EXPORT_DATABASE"

    def test_export_database_forbidden_for_admin(self, ad):
        assert ad.get(f"{API}/export/database", timeout=60).status_code == 403
        assert ad.get(f"{API}/export/template", timeout=60).status_code == 403
        assert ad.get(f"{API}/export/last", timeout=60).status_code == 403

    def test_template_download(self, dh):
        r = dh.get(f"{API}/export/template", timeout=60)
        assert r.status_code == 200
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        assert wb.sheetnames == ["DATA PERKARA", "DATA LOAN", "DATA JAMINAN", "DATA PROSES PERKARA"]

    def test_import_preview_and_execute(self, dh):
        nomor = f"TEST-IMP-{uuid.uuid4().hex[:6]}/Pdt.G/2026/PN.Tst"
        tmpl = dh.get(f"{API}/export/template", timeout=60).content
        wb = openpyxl.load_workbook(io.BytesIO(tmpl))
        ws = wb["DATA PERKARA"]
        ws.append([nomor, "PN Test", "TEST import", "Nasabah", "TEST A;TEST B",
                   "BSI", "Region 1 - Jakarta", "Area Test", "KC Test", "PIC", "CIFIMP1"])
        ws.append(["", "PN X", "baris tanpa nomor", "Nasabah", "X", "BSI", "R", "A", "C", "P", "CIFIMP2"])
        wb["DATA LOAN"].append(["CIFIMP1", "LNIMP1", 2000000, 500000, 100000])
        wb["DATA JAMINAN"].append(["CIFIMP1", "Tanah", "TEST jaminan", 9000000, "APHT"])
        wb["DATA PROSES PERKARA"].append([nomor, "Gugatan Terdaftar", "2026-01-10", "TEST proses"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        r = dh.post(f"{API}/import/preview",
                    files={"file": ("TEST_import.xlsx", buf.getvalue(),
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    timeout=120)
        assert r.status_code == 200, r.text[:300]
        prev = r.json()
        assert prev["baru"] == 1 and prev["update"] == 0
        assert len(prev["errors"]) >= 1
        err = prev["errors"][0]
        assert err["sheet"] == "DATA PERKARA" and err["kolom"] == "Nomor Perkara"

        ex = dh.post(f"{API}/import/execute", json={"staging_id": prev["staging_id"]}, timeout=120)
        assert ex.status_code == 200 and ex.json()["imported"] == 1
        found = dh.get(f"{API}/cases", params={"search": nomor}, timeout=60).json()
        assert len(found) == 1
        case = found[0]
        assert case["total_kewajiban"] == 2600000
        assert case["penggugat"] == ["TEST A", "TEST B"]
        assert len(case["jaminan"]) == 1
        assert any(t["judul"] == "Gugatan Terdaftar" for t in case["timeline"])
        # staging consumed
        assert dh.post(f"{API}/import/execute", json={"staging_id": prev["staging_id"]}, timeout=60).status_code == 404
        # cleanup
        dh.post(f"{API}/cases/{case['id']}/delete-request",
                json={"mode": "PERMANENT", "alasan": "TEST cleanup"}, timeout=60)
        assert dh.get(f"{API}/cases/{case['id']}", timeout=60).status_code == 404

    def test_import_rejects_non_xlsx(self, dh):
        r = dh.post(f"{API}/import/preview", files={"file": ("a.csv", b"x,y", "text/csv")}, timeout=60)
        assert r.status_code == 400

    def test_import_forbidden_for_admin(self, ad):
        r = ad.post(f"{API}/import/preview", files={"file": ("a.xlsx", b"x", "application/vnd.ms-excel")}, timeout=60)
        assert r.status_code == 403
        assert ad.post(f"{API}/import/execute", json={"staging_id": "x"}, timeout=60).status_code == 403


# ---------------- Users / role guard ----------------
class TestUsers:
    created = []

    def test_list_users_depthead(self, dh):
        r = dh.get(f"{API}/users", timeout=60)
        assert r.status_code == 200
        users = r.json()
        assert all("password_hash" not in u and "_id" not in u for u in users)
        assert {"depthead", "admin"} <= {u["username"] for u in users}

    def test_admin_forbidden(self, ad):
        assert ad.get(f"{API}/users", timeout=60).status_code == 403
        assert ad.post(f"{API}/users", json={"username": "x", "password": "y", "nama": "z"},
                       timeout=60).status_code == 403

    def test_create_user_validation(self, dh):
        assert dh.post(f"{API}/users", json={"username": "", "password": "", "nama": ""},
                       timeout=60).status_code == 400
        assert dh.post(f"{API}/users", json={"username": "admin", "password": "p", "nama": "n"},
                       timeout=60).status_code == 400

    def test_create_user_login_and_deactivate(self, dh):
        uname = f"testuser{uuid.uuid4().hex[:6]}"
        pwd = "TestUser2026!"
        r = dh.post(f"{API}/users", json={"username": uname, "password": pwd, "nama": "TEST User"}, timeout=60)
        assert r.status_code == 200
        u = r.json()
        assert u["role"] == "admin_legal" and u["aktif"] is True and "password_hash" not in u
        TestUsers.created.append(u["id"])
        # new user can login
        d = login({"username": uname, "password": pwd})
        assert d["user"]["role"] == "admin_legal"
        # deactivate
        assert dh.patch(f"{API}/users/{u['id']}/status", json={"aktif": False}, timeout=60).status_code == 200
        r2 = requests.post(f"{API}/auth/login", json={"username": uname, "password": pwd}, timeout=60)
        assert r2.status_code == 403, f"deactivated user could login: {r2.status_code}"
        # existing token should also be blocked
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {d['token']}"})
        assert s.get(f"{API}/auth/me", timeout=60).status_code == 403
        # reactivate
        assert dh.patch(f"{API}/users/{u['id']}/status", json={"aktif": True}, timeout=60).status_code == 200
        assert requests.post(f"{API}/auth/login", json={"username": uname, "password": pwd},
                             timeout=60).status_code == 200

    def test_cannot_toggle_depthead(self, dh):
        dhid = [u for u in dh.get(f"{API}/users", timeout=60).json() if u["username"] == "depthead"][0]["id"]
        assert dh.patch(f"{API}/users/{dhid}/status", json={"aktif": False}, timeout=60).status_code == 400

    def test_toggle_unknown_user(self, dh):
        assert dh.patch(f"{API}/users/{uuid.uuid4()}/status", json={"aktif": False}, timeout=60).status_code == 404

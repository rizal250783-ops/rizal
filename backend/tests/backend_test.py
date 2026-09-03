"""AO-360 backend regression tests (health, auth, RBAC, dashboards, ranking, calc rules)."""
import io
import time

import pytest
import requests
from conftest import API, CREDS, login, client_for


# ---------------- Health ----------------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=60)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_constants(self):
        r = requests.get(f"{API}/constants", timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert "roles" in d and "status_penagihan" in d
        assert "Dikunjungi" in d["status_penagihan"]


# ---------------- Auth ----------------
class TestAuth:
    def test_login_admin(self):
        r = login(*CREDS["admin"])
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["email"] == CREDS["admin"][0]
        assert d["role"] == "admin"
        assert isinstance(d["access_token"], str) and len(d["access_token"]) > 20
        assert "password_hash" not in d
        # httpOnly cookie
        cookie_hdr = r.headers.get("set-cookie", "")
        assert "access_token=" in cookie_hdr, "login must set access_token cookie"
        assert "HttpOnly" in cookie_hdr, f"cookie not httpOnly: {cookie_hdr}"

    def test_login_wrong_password_generic(self):
        r = login(CREDS["admin"][0], "WrongPass999")
        assert r.status_code == 401
        assert r.json()["detail"] == "Email atau password salah"

    def test_login_unknown_email_generic(self):
        r = login("nobody@hajimiskin.co.id", "Whatever123")
        assert r.status_code == 401
        assert r.json()["detail"] == "Email atau password salah"

    def test_me_requires_auth(self):
        r = requests.get(f"{API}/auth/me", timeout=60)
        assert r.status_code == 401

    def test_me_with_bearer(self, ao_lending):
        r = ao_lending.get(f"{API}/auth/me", timeout=60)
        assert r.status_code == 200
        assert r.json()["email"] == CREDS["ao_lending"][0]
        assert "password_hash" not in r.json()

    def test_invalid_token(self):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage.token.x"}, timeout=60)
        assert r.status_code == 401


# ---------------- RBAC ----------------
class TestRBAC:
    def test_direktur_can_read(self, direktur):
        for path in ["/dashboard/executive", "/ranking?type=lending", "/npf", "/audit-logs"]:
            r = direktur.get(f"{API}{path}", timeout=90)
            assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"

    def test_direktur_forbidden_writes(self, direktur):
        r = direktur.post(f"{API}/users", json={"name": "TEST_x", "email": "test_x@ex.com", "role": "ao_lending"}, timeout=60)
        assert r.status_code == 403
        r = direktur.post(f"{API}/targets", json={"ao_id": "x", "period": "2026-09"}, timeout=60)
        assert r.status_code == 403
        r = direktur.post(f"{API}/performance-settings",
                          json={"role": "ao_lending", "weights": {"lending": 70, "funding": 30}}, timeout=60)
        assert r.status_code == 403

    def test_ao_forbidden_users_and_ranking(self, ao_lending):
        assert ao_lending.get(f"{API}/users", timeout=60).status_code == 403
        assert ao_lending.get(f"{API}/ranking?type=lending", timeout=60).status_code == 403
        assert ao_lending.get(f"{API}/dashboard/executive", timeout=60).status_code == 403
        assert ao_lending.post(f"{API}/backup", timeout=60).status_code == 403


# ---------------- Dashboards & calculations ----------------
class TestDashboards:
    def test_dashboard_me_ao_lending(self, ao_lending):
        r = ao_lending.get(f"{API}/dashboard/me", timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["role"] == "ao_lending"
        assert "ach_lending" in d and "ach_funding" in d
        assert d["ach_lending"]["value"] is not None
        ps = d["performance"]["value"]
        assert ps is not None
        assert round(ps) == 113, f"expected ~113 got {ps}"
        assert d["performance"]["status"] == "Excellent"
        assert "portfolio" in d and d["portfolio"]["total"] > 0

    def test_ao_portfolio_scoped(self, ao_lending, admin):
        r = ao_lending.get(f"{API}/portfolio", timeout=60)
        assert r.status_code == 200
        mine = r.json()
        me = ao_lending.get(f"{API}/auth/me", timeout=60).json()
        assert len(mine) > 0, "seeded AO should have portfolio rows"
        assert all(p["ao_id"] == me["id"] for p in mine), "AO sees other AO portfolio rows"
        all_rows = admin.get(f"{API}/portfolio", timeout=60).json()
        assert len(all_rows) >= len(mine)
        assert all("_id" not in p for p in all_rows)

    def test_executive_dashboard(self, direktur):
        r = direktur.get(f"{API}/dashboard/executive", timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("lending", "funding", "recovery", "portfolio", "npf"):
            assert k in d
        assert d["lending"]["achievement"]["value"] is not None
        npf = d["npf"]
        assert abs(npf["npf_ratio"] - 2.68) < 0.3, f"npf_ratio={npf['npf_ratio']}"
        assert npf["status"] == "Sehat"
        assert abs(npf["npf_score"] - 111) < 5, f"npf_score={npf['npf_score']}"
        assert d["total_ao"] >= 10

    def test_npf_endpoint(self, admin):
        r = admin.get(f"{API}/npf", timeout=90)
        assert r.status_code == 200
        d = r.json()
        assert d["npf"]["status"] in ("Sehat", "Perhatian", "Critical")
        assert d["portfolio"]["total"] > 0
        assert set(str(k) for k in d["portfolio"]["kol"].keys()) == {"1", "2", "3", "4", "5"}

    def test_portfolio_summary(self, admin):
        r = admin.get(f"{API}/portfolio/summary", timeout=60)
        assert r.status_code == 200
        assert r.json()["total"] > 0


# ---------------- Ranking ----------------
class TestRanking:
    def test_ranking_lending(self, admin):
        r = admin.get(f"{API}/ranking?type=lending", timeout=120)
        assert r.status_code == 200, r.text
        entries = r.json()["entries"]
        assert len(entries) >= 4
        top = entries[0]
        assert top["rank"] == 1
        assert "Rizky" in top["name"], f"top={top['name']}"
        assert round(top["performance_score"]) == 113
        assert top["status"] == "Excellent"
        # descending order among valid entries
        valid = [e for e in entries if e["performance_score"] is not None]
        scores = [e["performance_score"] for e in valid]
        assert scores == sorted(scores, reverse=True)
        # N/A entries at bottom with rank None
        na_idx = [i for i, e in enumerate(entries) if e["rank"] is None]
        if na_idx:
            assert min(na_idx) >= len(valid)

    def test_ranking_funding_and_remedial(self, admin):
        for t in ("funding", "remedial"):
            r = admin.get(f"{API}/ranking?type={t}", timeout=120)
            assert r.status_code == 200
            assert len(r.json()["entries"]) >= 2

    def test_ranking_invalid_type(self, admin):
        r = admin.get(f"{API}/ranking?type=bogus", timeout=60)
        assert r.status_code == 400


# ---------------- Divide-by-zero (N/A) rule ----------------
class TestDivideByZero:
    def test_zero_target_zero_realisasi_yields_na(self, admin):
        # create throwaway AO
        email = f"test_dbz_{int(time.time())}@hajimiskin.co.id"
        cr = admin.post(f"{API}/users", json={"name": "TEST_DBZ AO", "email": email,
                                              "role": "ao_lending", "password": "Password123"}, timeout=60)
        assert cr.status_code == 200, cr.text
        uid = cr.json()["user"]["id"] if "user" in cr.json() else cr.json()["id"]
        try:
            period = "2026-09"
            t = admin.post(f"{API}/targets", json={"ao_id": uid, "period": period,
                                                   "target_booking": 0, "target_funding": 0}, timeout=60)
            assert t.status_code == 200, t.text
            a = admin.post(f"{API}/achievements", json={"ao_id": uid, "period": period,
                                                        "realisasi_booking": 0, "realisasi_funding": 0}, timeout=60)
            assert a.status_code == 200, a.text
            s = client_for_email(email, "Password123")
            r = s.get(f"{API}/dashboard/me?period={period}", timeout=90)
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["ach_lending"]["value"] is None
            assert d["ach_lending"]["flag"] == "NA"
            assert d["ach_lending"]["label"] == "N/A"
            assert d["performance"]["value"] is None
            assert d["performance"]["status"] == "N/A"
            # ranking should place it at bottom with rank None
            rk = admin.get(f"{API}/ranking?type=lending&period={period}", timeout=120).json()["entries"]
            mine = [e for e in rk if e["ao_id"] == uid]
            assert mine and mine[0]["rank"] is None
            assert rk[-1]["rank"] is None
        finally:
            admin.delete(f"{API}/users/{uid}", timeout=60)

    def test_zero_target_positive_realisasi(self, admin):
        email = f"test_dbz2_{int(time.time())}@hajimiskin.co.id"
        cr = admin.post(f"{API}/users", json={"name": "TEST_DBZ2 AO", "email": email,
                                              "role": "ao_funding", "password": "Password123"}, timeout=60)
        assert cr.status_code == 200, cr.text
        uid = cr.json().get("user", cr.json()).get("id")
        try:
            period = "2026-09"
            admin.post(f"{API}/targets", json={"ao_id": uid, "period": period, "target_funding": 0}, timeout=60)
            admin.post(f"{API}/achievements", json={"ao_id": uid, "period": period,
                                                    "realisasi_funding": 5000000}, timeout=60)
            s = client_for_email(email, "Password123")
            d = s.get(f"{API}/dashboard/me?period={period}", timeout=90).json()
            assert d["ach_funding"]["value"] is None
            assert d["ach_funding"]["flag"] == "NA_NO_TARGET"
        finally:
            admin.delete(f"{API}/users/{uid}", timeout=60)


def client_for_email(email, password):
    r = login(email, password)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text[:200]}"
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return s


# ---------------- Targets & achievements ----------------
class TestTargets:
    def test_upsert_target_and_achievement_reflects(self, admin):
        email = f"test_tgt_{int(time.time())}@hajimiskin.co.id"
        cr = admin.post(f"{API}/users", json={"name": "TEST_TGT AO", "email": email,
                                              "role": "ao_funding", "password": "Password123"}, timeout=60)
        uid = cr.json().get("user", cr.json()).get("id")
        try:
            period = "2026-09"
            admin.post(f"{API}/targets", json={"ao_id": uid, "period": period, "target_funding": 1000000}, timeout=60)
            admin.post(f"{API}/achievements", json={"ao_id": uid, "period": period, "realisasi_funding": 900000}, timeout=60)
            tl = admin.get(f"{API}/targets?period={period}", timeout=60).json()
            assert any(t["ao_id"] == uid and t["target_funding"] == 1000000 for t in tl)
            s = client_for_email(email, "Password123")
            d = s.get(f"{API}/dashboard/me?period={period}", timeout=90).json()
            assert d["ach_funding"]["value"] == 90.0
            assert d["performance"]["status"] == "Good"
            # upsert update
            admin.post(f"{API}/achievements", json={"ao_id": uid, "period": period, "realisasi_funding": 1200000}, timeout=60)
            d2 = s.get(f"{API}/dashboard/me?period={period}", timeout=90).json()
            assert d2["ach_funding"]["value"] == 120.0
            assert d2["performance"]["status"] == "Excellent"
        finally:
            admin.delete(f"{API}/users/{uid}", timeout=60)


# ---------------- Performance settings ----------------
class TestPerfSettings:
    def test_weights_must_sum_100(self, admin):
        r = admin.post(f"{API}/performance-settings",
                       json={"role": "ao_lending", "weights": {"lending": 60, "funding": 30}}, timeout=60)
        assert r.status_code == 400
        assert "100" in r.json()["detail"]

    def test_valid_weights_versioning(self, admin):
        r = admin.post(f"{API}/performance-settings",
                       json={"role": "ao_lending", "weights": {"lending": 80, "funding": 20},
                             "reason": "TEST_weights"}, timeout=60)
        assert r.status_code == 200, r.text
        v1 = r.json()["version"]
        g = admin.get(f"{API}/performance-settings", timeout=60).json()
        assert g["ao_lending"] == {"lending": 80, "funding": 20}
        # revert to default and confirm version increments
        r2 = admin.post(f"{API}/performance-settings",
                        json={"role": "ao_lending", "weights": {"lending": 70, "funding": 30},
                              "reason": "TEST_revert"}, timeout=60)
        assert r2.status_code == 200
        assert r2.json()["version"] == v1 + 1
        g2 = admin.get(f"{API}/performance-settings", timeout=60).json()
        assert g2["ao_lending"] == {"lending": 70, "funding": 30}
        h = admin.get(f"{API}/performance-settings/history", timeout=60)
        assert h.status_code == 200 and len(h.json()) >= 2

    def test_out_of_range_weight(self, admin):
        r = admin.post(f"{API}/performance-settings",
                       json={"role": "ao_lending", "weights": {"lending": 150, "funding": -50}}, timeout=60)
        assert r.status_code == 400


# ---------------- User management ----------------
class TestUserManagement:
    def test_create_reset_role_status_delete(self, admin):
        email = f"test_um_{int(time.time())}@hajimiskin.co.id"
        cr = admin.post(f"{API}/users", json={"name": "TEST_UM User", "email": email, "role": "ao_lending"}, timeout=60)
        assert cr.status_code == 200, cr.text
        body = cr.json()
        assert body.get("temp_password"), f"temp_password missing: {body}"
        temp_pw = body["temp_password"]
        u = body.get("user", body)
        uid = u["id"]
        assert u.get("requires_password_reset") is True
        assert "password_hash" not in u
        try:
            # login with temp password -> requires reset flag
            lr = login(email, temp_pw)
            assert lr.status_code == 200, lr.text
            assert lr.json()["requires_password_reset"] is True
            token = lr.json()["access_token"]
            s = requests.Session()
            s.headers.update({"Authorization": f"Bearer {token}"})
            # password policy violation
            bad = s.post(f"{API}/auth/change-password",
                         json={"current_password": temp_pw, "new_password": "abc"}, timeout=60)
            assert bad.status_code == 400
            bad2 = s.post(f"{API}/auth/change-password",
                          json={"current_password": temp_pw, "new_password": "abcdefghij"}, timeout=60)
            assert bad2.status_code == 400, "letters-only password should be rejected"
            ok = s.post(f"{API}/auth/change-password",
                        json={"current_password": temp_pw, "new_password": "NewPass123"}, timeout=60)
            assert ok.status_code == 200, ok.text
            lr2 = login(email, "NewPass123")
            assert lr2.status_code == 200
            assert lr2.json()["requires_password_reset"] is False

            # admin reset-password
            rp = admin.post(f"{API}/users/{uid}/reset-password", timeout=60)
            assert rp.status_code == 200 and rp.json().get("temp_password")
            new_temp = rp.json()["temp_password"]
            lr3 = login(email, new_temp)
            assert lr3.status_code == 200
            assert lr3.json()["requires_password_reset"] is True

            # change role
            crole = admin.post(f"{API}/users/{uid}/change-role", json={"new_role": "ao_funding"}, timeout=60)
            assert crole.status_code == 200, crole.text
            hist = admin.get(f"{API}/users/{uid}/role-history", timeout=60)
            assert hist.status_code == 200 and len(hist.json()) >= 1
            assert hist.json()[0]["role_baru"] == "ao_funding"
            assert hist.json()[0]["role_lama"] == "ao_lending"

            # update profile
            up = admin.put(f"{API}/users/{uid}", json={"name": "TEST_UM Renamed"}, timeout=60)
            assert up.status_code == 200
            lst = admin.get(f"{API}/users", timeout=60).json()
            found = [x for x in lst if x["id"] == uid][0]
            assert found["name"] == "TEST_UM Renamed"
            assert found["role"] == "ao_funding"

            # deactivate -> login blocked
            d = admin.post(f"{API}/users/{uid}/status?active=false", timeout=60)
            assert d.status_code == 200
            assert login(email, new_temp).status_code == 401
            admin.post(f"{API}/users/{uid}/status?active=true", timeout=60)
        finally:
            dl = admin.delete(f"{API}/users/{uid}", timeout=60)
            assert dl.status_code == 200
            lst = admin.get(f"{API}/users", timeout=60).json()
            assert not [x for x in lst if x["id"] == uid]

    def test_duplicate_email_rejected(self, admin):
        r = admin.post(f"{API}/users", json={"name": "TEST_dup", "email": CREDS["admin"][0],
                                             "role": "ao_lending", "password": "Password123"}, timeout=60)
        assert r.status_code in (400, 409), f"duplicate email got {r.status_code}"

    def test_create_user_weak_password_rejected(self, admin):
        r = admin.post(f"{API}/users", json={"name": "TEST_weak", "email": f"test_weak_{int(time.time())}@ex.co.id",
                                             "role": "ao_lending", "password": "abc"}, timeout=60)
        assert r.status_code == 400, f"weak password accepted: {r.status_code} {r.text[:200]}"


# ---------------- Account lockout (uses throwaway user) ----------------
class TestLockout:
    def test_lockout_after_5_failures(self, admin):
        email = f"test_lock_{int(time.time())}@hajimiskin.co.id"
        cr = admin.post(f"{API}/users", json={"name": "TEST_LOCK User", "email": email,
                                              "role": "ao_lending", "password": "Password123"}, timeout=60)
        assert cr.status_code == 200, cr.text
        uid = cr.json().get("user", cr.json()).get("id")
        try:
            for i in range(5):
                r = login(email, "WrongPass123")
                assert r.status_code == 401, f"attempt {i+1} -> {r.status_code}"
            # 6th attempt (even with correct password) should be locked
            r = login(email, "Password123")
            assert r.status_code == 423, f"expected 423 lockout, got {r.status_code} {r.text[:200]}"
            logs = admin.get(f"{API}/audit-logs?limit=200", timeout=60).json()
            acts = [l["aktivitas"] for l in logs if l.get("user_id") == uid]
            assert any("dikunci" in a for a in acts), f"lockout audit missing: {acts[:5]}"
            assert any("Login gagal" in a for a in acts)
        finally:
            admin.delete(f"{API}/users/{uid}", timeout=60)


# ---------------- Collection activity ----------------
def _png_bytes(color=(200, 30, 30)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (400, 300), color).save(buf, format="JPEG")
    return buf.getvalue()


class TestCollection:
    def test_create_with_photos_no_gps(self, ao_lending, admin):
        files = [("files", ("test_a.jpg", _png_bytes(), "image/jpeg")),
                 ("files", ("test_b.jpg", _png_bytes((30, 30, 200)), "image/jpeg"))]
        data = {"tanggal_aktivitas": "2026-09-15", "jam_aktivitas": "10:30",
                "nomor_kontrak": "TEST_KONTRAK_001", "nama_nasabah": "TEST Nasabah",
                "outstanding_pokok": "5000000", "status_penagihan": "Dikunjungi",
                "catatan": "TEST kunjungan"}
        r = ao_lending.post(f"{API}/collection-activities", data=data, files=files, timeout=180)
        assert r.status_code == 200, f"{r.status_code} {r.text[:500]}"
        body = r.json()
        assert body["photos"] == 2
        assert body["status_validasi"] == "Lokasi Tidak Tersedia", body
        aid = body["id"]

        lst = ao_lending.get(f"{API}/collection-activities", timeout=90)
        assert lst.status_code == 200
        act = [a for a in lst.json() if a["id"] == aid]
        assert act, "created activity not returned"
        act = act[0]
        assert len(act["photos"]) == 2
        assert act["approval_status"] == "Pending"
        for p in act["photos"]:
            assert p["foto_url"], "missing foto_url"
            assert p["status_validasi"] == "Lokasi Tidak Tersedia"

        # photo url is fetchable (watermarked object)
        url = act["photos"][0]["foto_url"]
        full = url if url.startswith("http") else f"{API}/files/{url}"
        fr = requests.get(full, timeout=90)
        assert fr.status_code == 200, f"photo fetch {fr.status_code} for {full}"
        assert len(fr.content) > 1000

        # admin review approve
        rv = admin.post(f"{API}/collection-activities/{aid}/review?action=approve", timeout=60)
        assert rv.status_code == 200
        after = [a for a in admin.get(f"{API}/collection-activities", timeout=90).json() if a["id"] == aid][0]
        assert after["approval_status"] == "Approved"
        rv2 = admin.post(f"{API}/collection-activities/{aid}/review?action=reject", timeout=60)
        assert rv2.status_code == 200

    def test_create_with_gps_valid(self, ao_lending):
        files = [("files", ("test_gps.jpg", _png_bytes((20, 150, 20)), "image/jpeg"))]
        data = {"tanggal_aktivitas": "2026-09-16", "jam_aktivitas": "11:00",
                "nomor_kontrak": "TEST_KONTRAK_002", "nama_nasabah": "TEST Nasabah GPS",
                "outstanding_pokok": "1000000", "status_penagihan": "Janji Bayar",
                "catatan": "TEST gps", "latitude": "-0.3", "longitude": "100.5"}
        r = ao_lending.post(f"{API}/collection-activities", data=data, files=files, timeout=180)
        assert r.status_code == 200, f"{r.status_code} {r.text[:500]}"
        assert r.json()["status_validasi"] in ("Valid", "Perlu Verifikasi Admin"), r.json()

    def test_max_5_photos(self, ao_lending):
        files = [("files", (f"t{i}.jpg", _png_bytes(), "image/jpeg")) for i in range(6)]
        data = {"tanggal_aktivitas": "2026-09-16", "jam_aktivitas": "11:00",
                "nomor_kontrak": "TEST_KONTRAK_003", "nama_nasabah": "TEST Max",
                "status_penagihan": "Dikunjungi"}
        r = ao_lending.post(f"{API}/collection-activities", data=data, files=files, timeout=180)
        assert r.status_code == 400

    def test_ao_funding_cannot_create(self, ao_funding):
        data = {"tanggal_aktivitas": "2026-09-16", "jam_aktivitas": "11:00",
                "nomor_kontrak": "TEST_KONTRAK_004", "nama_nasabah": "TEST X",
                "status_penagihan": "Dikunjungi"}
        r = ao_funding.post(f"{API}/collection-activities", data=data, timeout=90)
        assert r.status_code == 403

    def test_ao_sees_only_own(self, ao_lending):
        me = ao_lending.get(f"{API}/auth/me", timeout=60).json()
        lst = ao_lending.get(f"{API}/collection-activities", timeout=90).json()
        assert all(a["user_id"] == me["id"] for a in lst)


# ---------------- Data management ----------------
class TestDataManagement:
    def test_export_endpoints(self, admin):
        for rt in ["achievement", "portfolio", "npf", "collection"]:
            r = admin.get(f"{API}/export/{rt}", timeout=180)
            assert r.status_code == 200, f"{rt} -> {r.status_code} {r.text[:200]}"
            assert r.content[:2] == b"PK", f"{rt} not an xlsx"
            assert "spreadsheetml" in r.headers.get("content-type", "")

    def test_export_invalid_type(self, admin):
        r = admin.get(f"{API}/export/bogus", timeout=60)
        assert r.status_code == 400

    def test_import_preview_portfolio(self, admin):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["nomor_kontrak", "nama_nasabah", "produk", "plafond", "outstanding_pokok",
                   "tanggal_akad", "tanggal_jatuh_tempo", "kolektibilitas", "dpd", "ao_id"])
        ws.append(["TEST_IMP_001", "TEST Import A", "Murabahah", 10000000, 8000000,
                   "2025-01-01", "2027-01-01", 1, 0, "x"])
        ws.append([None, "TEST Import B", "Murabahah", 1, "abc", "2025-01-01", "2027-01-01", 2, 5, "x"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = admin.post(f"{API}/import/preview", data={"data_type": "portfolio"},
                       files={"file": ("test.xlsx", buf.getvalue(),
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                       timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "nomor_kontrak" in d["headers"]
        assert len(d["records"]) == 2
        assert d["error_count"] >= 1, d
        assert any("nomor_kontrak" in e["reason"] for e in d["errors"])

    def test_import_history(self, admin):
        r = admin.get(f"{API}/import-history", timeout=60)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_backup_excludes_password_hash(self, admin):
        r = admin.post(f"{API}/backup", timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "users" in d and len(d["users"]) >= 10
        for u in d["users"]:
            assert "password_hash" not in u, "backup leaks password_hash"
            assert u["requires_password_reset"] is True
        assert "_id" not in d["users"][0] and "id" in d["users"][0]


# ---------------- Settings / Audit ----------------
class TestSettingsAudit:
    def test_get_settings(self, admin):
        r = admin.get(f"{API}/settings", timeout=60)
        assert r.status_code == 200
        assert r.json().get("active_period")

    def test_update_settings(self, admin):
        cur = admin.get(f"{API}/settings", timeout=60).json()
        period = cur.get("active_period")
        r = admin.put(f"{API}/settings", json={"active_period": period, "session_timeout_minutes": 60}, timeout=60)
        assert r.status_code == 200, r.text
        assert admin.get(f"{API}/settings", timeout=60).json()["active_period"] == period

    def test_settings_write_forbidden_for_ao(self, ao_lending):
        r = ao_lending.put(f"{API}/settings", json={"active_period": "2026-01"}, timeout=60)
        assert r.status_code == 403

    def test_audit_logs(self, admin):
        r = admin.get(f"{API}/audit-logs?limit=50", timeout=60)
        assert r.status_code == 200
        logs = r.json()
        assert len(logs) > 0
        assert "aktivitas" in logs[0] and "waktu" in logs[0]
        assert all("_id" not in l for l in logs)

    def test_audit_forbidden_for_ao(self, ao_lending):
        assert ao_lending.get(f"{API}/audit-logs", timeout=60).status_code == 403


# ---------------- Password hash format (bcrypt) ----------------
class TestPasswordHashFormat:
    def test_bcrypt_hash_format(self):
        import asyncio
        import os as _os
        from motor.motor_asyncio import AsyncIOMotorClient
        from dotenv import dotenv_values as _dv
        env = _dv("/app/backend/.env")
        mongo = _os.environ.get("MONGO_URL") or env.get("MONGO_URL")
        dbname = _os.environ.get("DB_NAME") or env.get("DB_NAME")
        assert mongo and dbname

        async def check():
            c = AsyncIOMotorClient(mongo)
            u = await c[dbname].users.find_one({"email": CREDS["admin"][0]})
            c.close()
            return u

        u = asyncio.get_event_loop().run_until_complete(check()) if False else asyncio.run(check())
        assert u is not None, "admin user not seeded"
        assert u["password_hash"].startswith("$2b$"), f"hash prefix {u['password_hash'][:4]}"

"""End-to-end backend tests: auth, decision engine routing, RBAC, notes lifecycle,
dashboard/monitoring/export, and user management."""
import pytest
import requests

from conftest import (API, NIP, PASSWORD, Client, login, note_payload,
                      create_and_submit, CREATED_NOTE_IDS, CREATED_USER_IDS)


# ---------------- Health ----------------
class TestHealth:
    def test_root(self):
        r = requests.get(f"{API}/", timeout=30)
        assert r.status_code == 200
        assert r.json().get("status") == "ok"


# ---------------- AUTH ----------------
class TestAuth:
    @pytest.mark.parametrize("key", list(NIP.keys()))
    def test_login_all_roles(self, key):
        r = login(NIP[key])
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert isinstance(d.get("token"), str) and len(d["token"]) > 10
        assert d["user"]["nip"] == NIP[key]
        assert "password_hash" not in d["user"]
        assert "_id" not in d["user"]

    def test_login_wrong_password(self):
        r = login(NIP["RCO"], "wrongpass")
        assert r.status_code == 401
        assert "detail" in r.json()

    def test_login_unknown_nip(self):
        r = login("0000000000")
        assert r.status_code == 401

    def test_me(self, rco):
        r = rco.get("/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert d["nip"] == NIP["RCO"]
        assert d["role"] == "RCO"
        assert d["area"] == "Area Banda Aceh"
        assert "password_hash" not in d

    def test_me_no_token(self):
        r = requests.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 401

    def test_me_bad_token(self):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}, timeout=30)
        assert r.status_code == 401

    def test_bcrypt_hash_format(self):
        from dotenv import dotenv_values
        from pymongo import MongoClient
        be = dotenv_values("/app/backend/.env")
        cl = MongoClient(be["MONGO_URL"])
        u = cl[be["DB_NAME"]].users.find_one({"nip": NIP["RCO"]})
        cl.close()
        assert u["password_hash"].startswith("$2b$")

    def test_change_password_wrong_old(self, rco):
        r = rco.post("/auth/change-password", json={"old_password": "salah123",
                                                   "new_password": "abc123",
                                                   "confirm_password": "abc123"})
        assert r.status_code == 400
        assert "lama" in str(r.json().get("detail", "")).lower()

    def test_change_password_too_long(self, rco):
        r = rco.post("/auth/change-password", json={"old_password": PASSWORD,
                                                   "new_password": "abcdefghij",
                                                   "confirm_password": "abcdefghij"})
        assert r.status_code == 400

    def test_change_password_mismatch(self, rco):
        r = rco.post("/auth/change-password", json={"old_password": PASSWORD,
                                                    "new_password": "abc123",
                                                    "confirm_password": "abc124"})
        assert r.status_code == 400

    def test_change_password_success_same_value(self, rco):
        """Change to the same value so seeded credentials remain usable."""
        r = rco.post("/auth/change-password", json={"old_password": PASSWORD,
                                                    "new_password": PASSWORD,
                                                    "confirm_password": PASSWORD})
        assert r.status_code == 200, r.text[:300]
        assert login(NIP["RCO"]).status_code == 200


# ---------------- REFERENCE ----------------
class TestReference:
    def test_reference(self, rco):
        r = rco.get("/reference")
        assert r.status_code == 200
        d = r.json()
        assert d["segmen"] == ["KONSUMER", "RETAIL"]
        assert d["produk"]["KONSUMER"] == ["Griya", "Multiguna", "Pensiunan", "Pra Pensiunan", "Cicil Emas"]
        assert d["akad"]["RETAIL"] == ["Murabahah", "Musyarakah", "MMQ", "Ijarah"]
        assert d["rcg_cap"] == 30000000000

    def test_regions_areas_branches(self, rco):
        assert rco.get("/regions").status_code == 200
        a = rco.get("/areas?region=RO I ACEH")
        assert a.status_code == 200
        assert any(x["nama"] == "Area Banda Aceh" for x in a.json())
        b = rco.get("/branches")
        assert b.status_code == 200
        names = [x["nama_cabang"] for x in b.json()]
        assert names, "RCO branches list empty for own area"


# ---------------- SUBMIT VALIDATION ----------------
class TestSubmitValidation:
    def test_submit_empty_note_returns_errors(self, rco):
        r = rco.post("/notes", json={})
        assert r.status_code == 200
        nid = r.json()["id"]
        CREATED_NOTE_IDS.append(nid)
        s = rco.post(f"/notes/{nid}/submit")
        assert s.status_code == 400
        detail = s.json()["detail"]
        assert isinstance(detail, list) and len(detail) >= 3
        joined = " | ".join(detail)
        assert "Nama nasabah wajib" in joined
        assert "Minimal 1 fasilitas" in joined
        assert "Dokumen wajib" in joined

    def test_submit_missing_documents(self, rco):
        p = note_payload(1000000000)
        p["documents"] = []
        r = rco.post("/notes", json=p)
        nid = r.json()["id"]
        CREATED_NOTE_IDS.append(nid)
        s = rco.post(f"/notes/{nid}/submit")
        assert s.status_code == 400
        assert any("Dokumen wajib" in e for e in s.json()["detail"])

    def test_nomor_manual_more_than_5_digits(self, rco):
        p = note_payload(1000000000)
        p["nomor_manual"] = "123456"
        r = rco.post("/notes", json=p)
        nid = r.json()["id"]
        CREATED_NOTE_IDS.append(nid)
        s = rco.post(f"/notes/{nid}/submit")
        assert s.status_code == 400
        assert any("5 digit" in e for e in s.json()["detail"])

    def test_financials_computed_on_create(self, rco):
        r = rco.post("/notes", json=note_payload(2000000000))
        assert r.status_code == 200
        n = r.json()
        CREATED_NOTE_IDS.append(n["id"])
        assert n["nilai_kewenangan_pemutus"] == 2000000000
        assert n["total_kewajiban"] == 2000000000 + 100000000 + 5000000
        assert n["status"] == "Draft"
        assert "_id" not in n
        assert n["nomor_nota"].startswith("06/")


# ---------------- CASE 1: final ACRM ----------------
class TestFlowACRM:
    def test_acrm_final_approve_flow(self, rco, acrm, rcrm):
        note = create_and_submit(rco, 2000000000, rac_ok=True)
        assert note["nilai_kewenangan_pemutus"] == 2000000000
        assert note["normal_approver_level"] == "ACRM"
        assert note["final_approver_level"] == "ACRM"
        assert note["ra_required"] is False
        assert note["status"] == "Menunggu Pemutus ACRM"
        nid = note["id"]

        # forward not allowed on decide stage
        bad = acrm.post(f"/notes/{nid}/action", json={"decision": "forward"})
        assert bad.status_code == 400

        r = acrm.post(f"/notes/{nid}/action", json={"decision": "approve", "catatan": "Setuju"})
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["status"] == "Final Approved"
        assert d["read_only"] is True
        assert d["final_approver_nip"] == NIP["ACRM"]
        assert d["limit_pemutus_used"] == 2000000000

        # GET verifies persistence
        g = rco.get(f"/notes/{nid}")
        assert g.status_code == 200
        assert g.json()["status"] == "Final Approved"
        assert g.json()["can_download"] is True

        # read-only: RCO edit -> 400
        e = rco.put(f"/notes/{nid}", json={"customer": {"nama": "CHANGED"}})
        assert e.status_code == 400

        # second approve -> 400
        again = acrm.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert again.status_code == 400

        # PDF: creator RCO allowed
        p = rco.get(f"/notes/{nid}/pdf")
        assert p.status_code == 200, p.text[:200]
        assert p.headers.get("content-type", "").startswith("application/pdf")
        assert p.content[:4] == b"%PDF"

        # PDF: ACRM of same area allowed
        p2 = acrm.get(f"/notes/{nid}/pdf")
        assert p2.status_code == 200
        assert p2.content[:4] == b"%PDF"

        # PDF: RCRM has no right for ACRM-level note
        p3 = rcrm.get(f"/notes/{nid}/pdf")
        assert p3.status_code == 403, f"expected 403 got {p3.status_code}"

        # notification for RCO created
        n = rco.get("/notifications")
        assert n.status_code == 200
        assert any(i["note_id"] == nid for i in n.json()["items"])


# ---------------- CASE 2: final RCRM ----------------
class TestFlowRCRM:
    def test_rcrm_final_flow(self, rco, acrm, rcrm):
        note = create_and_submit(rco, 5000000000, rac_ok=True)
        nid = note["id"]
        assert note["final_approver_level"] == "RCRM"
        assert note["status"] == "Menunggu Review ACRM"

        # RCRM cannot act while stage is ACRM review
        early = rcrm.post(f"/notes/{nid}/action", json={"decision": "forward"})
        assert early.status_code == 403

        f = acrm.post(f"/notes/{nid}/action", json={"decision": "forward", "catatan": "diteruskan"})
        assert f.status_code == 200, f.text[:300]
        assert f.json()["status"] == "Menunggu Pemutus RCRM"

        a = rcrm.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert a.status_code == 200, a.text[:300]
        d = a.json()
        assert d["status"] == "Final Approved"
        assert d["final_approver_nip"] == NIP["RCRM"]
        assert d["limit_pemutus_used"] == 10000000000
        # RCRM can download RCRM-level note
        assert rcrm.get(f"/notes/{nid}/pdf").status_code == 200


# ---------------- CASE 3: final RCG ----------------
class TestFlowRCG:
    def test_rcg_final_flow_only_immadha(self, rco, acrm, rcrm, rcg_approver, rcg_other):
        note = create_and_submit(rco, 15000000000, rac_ok=True)
        nid = note["id"]
        assert note["final_approver_level"] == "RCG"
        assert [s[0] for s in note["stages"]] == ["ACRM", "RCRM", "RCG"]

        assert acrm.post(f"/notes/{nid}/action", json={"decision": "forward"}).json()["status"] == "Menunggu Review RCRM"
        assert rcrm.post(f"/notes/{nid}/action", json={"decision": "forward"}).json()["status"] == "Menunggu Pemutus RCG"

        # RATMIYATI (RCG, can_approve False) must be rejected
        bad = rcg_other.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert bad.status_code == 403, f"non-approver RCG got {bad.status_code}"

        ok = rcg_approver.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert ok.status_code == 200, ok.text[:300]
        d = ok.json()
        assert d["status"] == "Final Approved"
        assert d["final_approver_nip"] == NIP["RCG_APPROVER"]
        assert rcg_approver.get(f"/notes/{nid}/pdf").status_code == 200


# ---------------- CASE 4: RAC not met -> escalation + RA ----------------
class TestFlowRACEscalation:
    def test_rac_fail_escalates_and_requires_ra(self, rco, acrm, rcrm, rcg_approver):
        note = create_and_submit(rco, 2000000000, rac_ok=False)
        nid = note["id"]
        assert note["rac_ok"] is False
        assert note["normal_approver_level"] == "ACRM"
        assert note["final_approver_level"] == "RCRM"
        assert note["ra_required"] is True
        assert [s[0] for s in note["stages"]] == ["ACRM", "RA", "RCRM"]
        assert note["status"] == "Menunggu Review ACRM"

        f = acrm.post(f"/notes/{nid}/action", json={"decision": "forward"})
        assert f.status_code == 200
        assert f.json()["status"] == "Menunggu Risk Assessment"

        # action at RA stage must be blocked
        blocked = rcrm.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert blocked.status_code == 400

        ra = rcg_approver.post(f"/notes/{nid}/risk-assessment",
                               json={"status": "Selesai", "file_path": "ra.pdf"})
        assert ra.status_code == 200, ra.text[:300]
        d = ra.json()
        assert d["risk_assessment"]["status"] == "Selesai"
        assert d["status"] == "Menunggu Pemutus RCRM"

        a = rcrm.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert a.status_code == 200
        assert a.json()["status"] == "Final Approved"

    def test_ra_endpoint_forbidden_for_rco(self, rco):
        note = create_and_submit(rco, 2000000000, rac_ok=False)
        r = rco.post(f"/notes/{note['id']}/risk-assessment", json={"status": "Selesai"})
        assert r.status_code == 403


# ---------------- CASE 5: above RCG ----------------
class TestFlowAboveRCG:
    def test_above_rcg_routing_and_notification(self, rco, rcg_approver, rcg_admin, acrm, rcrm):
        note = create_and_submit(rco, 35000000000, rac_ok=True)
        nid = note["id"]
        assert note["final_approver_level"] == "ABOVE_RCG"
        assert [s[0] for s in note["stages"]] == ["ACRM", "RCRM", "ESCALATION"]
        # RCG users notified about escalation at submit time
        n = rcg_admin.get("/notifications")
        assert n.status_code == 200
        assert any(i["note_id"] == nid for i in n.json()["items"])
        # IMMADHA can never approve this nota
        assert rcg_approver.post(f"/notes/{nid}/action", json={"decision": "approve"}).status_code in (400, 403)
        # walk the review chain -> escalation stage
        acrm.post(f"/notes/{nid}/action", json={"decision": "forward"})
        f = rcrm.post(f"/notes/{nid}/action", json={"decision": "forward"})
        assert f.status_code == 200, f.text[:300]
        assert f.json()["status"] == "Memerlukan Eskalasi di Atas RCG"
        r = rcg_approver.post(f"/notes/{nid}/action", json={"decision": "approve"})
        assert r.status_code == 400, f"expected block, got {r.status_code}"

    def test_above_rcg_status_immediately_on_submit(self, rco):
        """SPEC: nilai > 30M must land on status 'Memerlukan Eskalasi di Atas RCG' right away."""
        note = create_and_submit(rco, 35000000000, rac_ok=True)
        assert note["status"] == "Memerlukan Eskalasi di Atas RCG", (
            f"got '{note['status']}' - nota above RCG cap is routed through ACRM/RCRM review first")


# ---------------- REJECT / REVISI ----------------
class TestRejectRevisi:
    def test_acrm_revisi_returns_to_rco(self, rco, acrm):
        note = create_and_submit(rco, 2000000000, rac_ok=True)
        nid = note["id"]
        r = acrm.post(f"/notes/{nid}/action", json={"decision": "revisi", "catatan": "lengkapi dokumen"})
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["status"] == "Revisi oleh ACRM"
        assert d["stage_index"] == 0
        assert d["read_only"] is False
        # editable again
        e = rco.put(f"/notes/{nid}", json={"customer": {"nama": "TEST_NASABAH REVISI"}})
        assert e.status_code == 200
        assert e.json()["customer"]["nama"] == "TEST_NASABAH REVISI"
        # notification to RCO
        n = rco.get("/notifications")
        assert any(i["note_id"] == nid for i in n.json()["items"])
        # resubmit works
        s = rco.post(f"/notes/{nid}/submit")
        assert s.status_code == 200
        assert s.json()["status"] == "Menunggu Pemutus ACRM"

    def test_rcrm_reject_notifies_acrm(self, rco, acrm, rcrm):
        note = create_and_submit(rco, 5000000000, rac_ok=True)
        nid = note["id"]
        acrm.post(f"/notes/{nid}/action", json={"decision": "forward"})
        r = rcrm.post(f"/notes/{nid}/action", json={"decision": "reject", "catatan": "tidak layak"})
        assert r.status_code == 200
        assert r.json()["status"] == "Reject oleh RCRM"
        n = acrm.get("/notifications")
        assert any(i["note_id"] == nid for i in n.json()["items"]), "ACRM not notified on RCRM reject"


# ---------------- RBAC ----------------
class TestRBAC:
    @pytest.fixture(scope="class")
    def other_area_actors(self, rcg_admin):
        """Find an RCO and ACRM belonging to a different area/region."""
        users = rcg_admin.get("/users").json()
        rco_other = next(u for u in users if u["role"] == "RCO" and u.get("area") != "Area Banda Aceh")
        acrm_other = next(u for u in users if u["role"] == "ACRM" and u.get("area") != "Area Banda Aceh")
        rcrm_other = next(u for u in users if u["role"] == "RCRM" and u.get("region") != "RO I ACEH")
        return rco_other, acrm_other, rcrm_other

    def test_rco_cannot_read_users(self, rco):
        assert rco.get("/users").status_code == 403

    def test_acrm_cannot_read_users(self, acrm):
        assert acrm.get("/users").status_code == 403

    def test_cross_scope_note_access(self, rco, other_area_actors):
        rco_other, acrm_other, rcrm_other = other_area_actors
        note = create_and_submit(rco, 2000000000, rac_ok=True)
        nid = note["id"]
        for u in (rco_other, acrm_other, rcrm_other):
            c = Client(u["nip"])
            r = c.get(f"/notes/{nid}")
            assert r.status_code == 403, f"{u['role']} {u['nip']} got {r.status_code} for foreign note"

    def test_rco_list_only_own_notes(self, rco):
        r = rco.get("/notes")
        assert r.status_code == 200
        me = rco.get("/auth/me").json()
        assert all(n["creator_id"] == me["id"] for n in r.json())

    def test_acrm_list_only_own_area(self, acrm):
        r = acrm.get("/notes")
        assert r.status_code == 200
        assert all(n["area"] == "Area Banda Aceh" for n in r.json())

    def test_rco_cannot_create_note_as_acrm(self, acrm):
        r = acrm.post("/notes", json=note_payload(1000000000))
        assert r.status_code == 403

    def test_audit_rcg_only(self, rco, rcg_admin):
        assert rco.get("/audit").status_code == 403
        r = rcg_admin.get("/audit")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------- DASHBOARD / MONITORING / EXPORT ----------------
class TestDashboard:
    def test_dashboard_rco(self, rco):
        r = rco.get("/dashboard")
        assert r.status_code == 200
        d = r.json()
        assert d["role"] == "RCO"
        for k in ("draft", "menunggu", "revisi_reject", "approved", "eskalasi"):
            assert k in d["cards"]

    def test_dashboard_acrm_by_rco(self, acrm):
        d = acrm.get("/dashboard").json()
        assert "by_rco" in d
        assert isinstance(d["by_rco"], list)

    def test_dashboard_rcrm_by_area(self, rcrm):
        d = rcrm.get("/dashboard").json()
        assert "by_area" in d

    def test_dashboard_rcg_breakdowns(self, rcg_admin):
        d = rcg_admin.get("/dashboard").json()
        for k in ("by_region", "by_area", "by_month"):
            assert k in d, f"missing {k}"

    def test_monitoring_roles(self, rco, acrm, rcrm, rcg_admin):
        assert rco.get("/monitoring").status_code == 403
        assert acrm.get("/monitoring").status_code == 403
        for c in (rcrm, rcg_admin):
            r = c.get("/monitoring")
            assert r.status_code == 200
            d = r.json()
            assert "per_segmen" in d and "per_produk" in d

    def test_export_excel(self, rcrm, rcg_admin, rco):
        for c in (rcrm, rcg_admin):
            r = c.get("/export/excel")
            assert r.status_code == 200, r.text[:200]
            assert r.content[:2] == b"PK"
        assert rco.get("/export/excel").status_code == 403


# ---------------- USER MANAGEMENT ----------------
class TestUserManagement:
    def test_admin_create_and_delete_user(self, rcg_admin):
        payload = {"nama": "TEST_QA USER", "nip": "9999000111", "role": "RCO",
                   "area": "Area Banda Aceh"}
        r = rcg_admin.post("/users", json=payload)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert len(d["generated_password"]) == 8
        uid = d["user"]["id"]
        CREATED_USER_IDS.append(uid)
        assert d["user"]["region"] == "RO I ACEH"
        assert "password_hash" not in d["user"]
        # new user can login with generated password
        lg = login("9999000111", d["generated_password"])
        assert lg.status_code == 200

        # duplicate NIP
        dup = rcg_admin.post("/users", json=payload)
        assert dup.status_code == 400

        # delete + verify removal
        de = rcg_admin.delete(f"/users/{uid}")
        assert de.status_code == 200
        assert login("9999000111", d["generated_password"]).status_code == 401

    def test_acrm_requires_limit(self, rcg_admin):
        r = rcg_admin.post("/users", json={"nama": "TEST_QA ACRM", "nip": "9999000222",
                                           "role": "ACRM", "area": "Area Banda Aceh"})
        assert r.status_code == 400

    def test_non_admin_rcg_cannot_create_or_delete(self, rcg_other, rcg_admin):
        r = rcg_other.post("/users", json={"nama": "TEST_QA X", "nip": "9999000333",
                                           "role": "RCO", "area": "Area Banda Aceh"})
        assert r.status_code == 403
        users = rcg_admin.get("/users").json()
        target = next(u for u in users if u["role"] == "RCO")
        assert rcg_other.delete(f"/users/{target['id']}").status_code == 403

    def test_immadha_cannot_be_deleted(self, rcg_admin):
        users = rcg_admin.get("/users").json()
        immadha = next(u for u in users if u["nip"] == NIP["RCG_APPROVER"])
        r = rcg_admin.delete(f"/users/{immadha['id']}")
        assert r.status_code == 400

    def test_reset_password_allowed_for_rcg_non_admin(self, rcg_other, rcg_admin):
        # create a throwaway user via admin, reset via non-admin RCG
        c = rcg_admin.post("/users", json={"nama": "TEST_QA RESET", "nip": "9999000444",
                                          "role": "RCO", "area": "Area Banda Aceh"})
        assert c.status_code == 200
        uid = c.json()["user"]["id"]
        CREATED_USER_IDS.append(uid)
        r = rcg_other.post(f"/users/{uid}/reset-password")
        assert r.status_code == 200
        newpw = r.json()["generated_password"]
        assert login("9999000444", newpw).status_code == 200
        rcg_admin.delete(f"/users/{uid}")

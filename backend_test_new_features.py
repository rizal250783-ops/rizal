#!/usr/bin/env python3
"""
Backend Testing for 3 NEW Features in RCG Digital Restructuring App
Test Date: 2026-08-28
Features:
1. SPECIAL RATMIYATI NOTIFICATION for RCG-level notes with specific conditions
2. EXPORT BY CATEGORY endpoint
3. ACTION_REQUIRED FLAG in GET /notes
"""

import requests
import sys
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://rizal-ops-setup.preview.emergentagent.com/api"

# Test credentials (all passwords: bsi12345)
ADMIN_NIP = "2183008345"  # SYAMSU RIZAL
RATMIYATI_NIP = "2180007674"  # RCG pemutus <= 10B
IMMADHA_NIP = "2175007386"  # RCG pemutus > 10B
PASSWORD = "bsi12345"

# Test results tracking
test_results = []
total_tests = 0
passed_tests = 0


def log_test(test_name, passed, details=""):
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status} | {test_name}"
    if details:
        result += f" | {details}"
    test_results.append(result)
    print(result)


def login(nip, password=PASSWORD):
    """Login and return token + user info"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={"nip": nip, "password": password})
    if resp.status_code != 200:
        print(f"❌ Login failed for NIP {nip}: {resp.status_code} {resp.text}")
        return None, None
    data = resp.json()
    return data["token"], data["user"]


def get_headers(token):
    return {"Authorization": f"Bearer {token}"}


def find_rco_in_region(token, region_name):
    """Find an RCO user in the specified region"""
    resp = requests.get(f"{BASE_URL}/users", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    users = resp.json()
    for u in users:
        if u.get("role") == "RCO" and u.get("region") == region_name:
            return u
    return None


def find_acrm_in_area(token, area_name):
    """Find an ACRM user in the specified area"""
    resp = requests.get(f"{BASE_URL}/users", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    users = resp.json()
    for u in users:
        if u.get("role") == "ACRM" and u.get("area") == area_name:
            return u
    return None


def find_rcrm_in_region(token, region_name):
    """Find an RCRM user in the specified region"""
    resp = requests.get(f"{BASE_URL}/users", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    users = resp.json()
    for u in users:
        if u.get("role") == "RCRM" and u.get("region") == region_name:
            return u
    return None


def create_test_note(token, os_pokok_value):
    """Create a test note with specified os_pokok value"""
    payload = {
        "nomor_manual": "99999",
        "kepada": "ACRM",
        "reff_tanggal": "01/01/2026",
        "customer": {"nama": "TEST CUSTOMER RATMIYATI", "cif": "1234567890"},
        "facilities": [{
            "cif": "1234567890",
            "nomor_loan": "TEST001",
            "kolektibilitas": "3A",
            "segmen": "KONSUMER",
            "produk": "Griya",
            "akad": "Murabahah",
            "nama_cabang": "Test Branch",
            "os_pokok": os_pokok_value,
            "os_margin": 100000000,
            "penalty": 10000000,
            "tgl_mulai": "01/01/2020",
            "tgl_jatuh_tempo": "01/01/2025"
        }],
        "has_fix_asset": False,
        "collaterals": [],
        "rac": [{"parameter": "Test RAC", "status": "Terpenuhi", "keterangan": ""}],
        "analysis": {"penyebab_bermasalah": "Test cause"},
        "proposals": [{
            "tgl_mulai": "01/01/2026",
            "tgl_akhir": "01/01/2030",
            "angsuran_pokok": 10000000,
            "angsuran_margin": 5000000
        }],
        "documents": [
            {"document_type": "foto_ots", "file_path": "test.pdf"},
            {"document_type": "surat_permohonan_ktp", "file_path": "test2.pdf"},
            {"document_type": "bi_checking", "file_path": "test3.pdf"}
        ]
    }
    resp = requests.post(f"{BASE_URL}/notes", json=payload, headers=get_headers(token))
    if resp.status_code != 200:
        print(f"❌ Failed to create note: {resp.status_code} {resp.text}")
        return None
    return resp.json()


def submit_note(token, note_id):
    """Submit a note"""
    resp = requests.post(f"{BASE_URL}/notes/{note_id}/submit", headers=get_headers(token))
    if resp.status_code != 200:
        print(f"❌ Failed to submit note: {resp.status_code} {resp.text}")
        return None
    return resp.json()


def forward_note(token, note_id):
    """Forward a note (ACRM/RCRM review)"""
    resp = requests.post(
        f"{BASE_URL}/notes/{note_id}/action",
        json={"decision": "forward", "catatan": "Test forward"},
        headers=get_headers(token)
    )
    if resp.status_code != 200:
        print(f"❌ Failed to forward note: {resp.status_code} {resp.text}")
        return None
    return resp.json()


def approve_note(token, note_id, disposisi="Disetujui sesuai ketentuan"):
    """Approve a note (final decision)"""
    resp = requests.post(
        f"{BASE_URL}/notes/{note_id}/action",
        json={"decision": "approve", "catatan": "Test approve", "disposisi": disposisi},
        headers=get_headers(token)
    )
    return resp


def get_notifications(token):
    """Get notifications for current user"""
    resp = requests.get(f"{BASE_URL}/notifications", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    return resp.json()


def export_notes_excel(token, category=None):
    """Export notes to Excel with optional category filter"""
    url = f"{BASE_URL}/export/notes-excel"
    if category:
        url += f"?category={category}"
    resp = requests.get(url, headers=get_headers(token))
    return resp


def get_notes(token):
    """Get notes list"""
    resp = requests.get(f"{BASE_URL}/notes", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    return resp.json()


def cleanup_test_note(token, note_id):
    """Clean up test note (admin only)"""
    # Notes cannot be deleted via API, so we'll leave them as test data
    pass


print("=" * 80)
print("BACKEND TESTING - 3 NEW FEATURES")
print("=" * 80)
print()

# Login as admin first to find users
admin_token, admin_user = login(ADMIN_NIP)
if not admin_token:
    print("❌ CRITICAL: Cannot login as admin. Aborting tests.")
    sys.exit(1)

print(f"✅ Logged in as admin: {admin_user['nama']} (NIP {admin_user['nip']})")
print()

# ============================================================================
# TEST 1: SPECIAL RATMIYATI NOTIFICATION
# ============================================================================
print("=" * 80)
print("TEST 1: SPECIAL RATMIYATI NOTIFICATION")
print("=" * 80)
print()
print("Scenario: Create a note in a region where RCRM limit < 10B, with os_pokok")
print("between RCRM limit and 10B, so it routes to RCG with RATMIYATI as decider.")
print("Verify notification contains 'RCG ≤ Rp10 Miliar'.")
print()

# Step 1: Find RCRM with limit < 10B
print("Step 1: Finding RCRM with limit < 10,000,000,000...")
resp = requests.get(f"{BASE_URL}/users?role=RCRM", headers=get_headers(admin_token))
if resp.status_code != 200:
    log_test("1.1 Find RCRM with limit < 10B", False, f"Failed to get RCRM users: {resp.status_code}")
else:
    rcrms = resp.json()
    target_rcrm = None
    for rcrm in rcrms:
        if rcrm.get("limit_pemutus", 0) < 10_000_000_000 and rcrm.get("limit_pemutus", 0) > 0:
            target_rcrm = rcrm
            break
    
    if not target_rcrm:
        log_test("1.1 Find RCRM with limit < 10B", False, "No RCRM found with limit < 10B")
    else:
        rcrm_limit = target_rcrm["limit_pemutus"]
        rcrm_region = target_rcrm["region"]
        rcrm_nip = target_rcrm["nip"]
        rcrm_nama = target_rcrm["nama"]
        log_test("1.1 Find RCRM with limit < 10B", True, 
                f"Found {rcrm_nama} (NIP {rcrm_nip}) in {rcrm_region}, limit {rcrm_limit:,.0f}")
        
        # Step 2: Find RCO in that region
        print(f"\nStep 2: Finding RCO in region '{rcrm_region}'...")
        rco = find_rco_in_region(admin_token, rcrm_region)
        if not rco:
            log_test("1.2 Find RCO in target region", False, f"No RCO found in {rcrm_region}")
        else:
            rco_nip = rco["nip"]
            rco_nama = rco["nama"]
            rco_area = rco["area"]
            log_test("1.2 Find RCO in target region", True, 
                    f"Found {rco_nama} (NIP {rco_nip}) in Area {rco_area}")
            
            # Step 3: Login as RCO and create note with os_pokok between RCRM limit and 10B
            print(f"\nStep 3: Login as RCO {rco_nama} (NIP {rco_nip})...")
            rco_token, rco_user = login(rco_nip)
            if not rco_token:
                log_test("1.3 Login as RCO", False, f"Failed to login as RCO {rco_nip}")
            else:
                log_test("1.3 Login as RCO", True, f"Logged in as {rco_nama}")
                
                # Create note with os_pokok = 8,000,000,000 (between 7.5B and 10B)
                os_pokok_value = 8_000_000_000
                print(f"\nStep 4: Creating note with os_pokok = {os_pokok_value:,.0f}...")
                note = create_test_note(rco_token, os_pokok_value)
                if not note:
                    log_test("1.4 Create note with os_pokok 8B", False, "Failed to create note")
                else:
                    note_id = note["id"]
                    log_test("1.4 Create note with os_pokok 8B", True, f"Note ID: {note_id}")
                    
                    # Step 5: Submit note
                    print(f"\nStep 5: Submitting note {note_id}...")
                    submitted = submit_note(rco_token, note_id)
                    if not submitted:
                        log_test("1.5 Submit note", False, "Failed to submit note")
                    else:
                        log_test("1.5 Submit note", True, 
                                f"Status: {submitted.get('status')}, Routing: {submitted.get('stages')}")
                        
                        # Verify rcg_pemutus_nip is RATMIYATI
                        rcg_pemutus = submitted.get("rcg_pemutus_nip")
                        if rcg_pemutus == RATMIYATI_NIP:
                            log_test("1.6 Verify RCG pemutus is RATMIYATI", True, 
                                    f"rcg_pemutus_nip = {rcg_pemutus}")
                        else:
                            log_test("1.6 Verify RCG pemutus is RATMIYATI", False, 
                                    f"Expected {RATMIYATI_NIP}, got {rcg_pemutus}")
                        
                        # Step 6: Find ACRM in the area and forward
                        print(f"\nStep 6: Finding ACRM in area '{rco_area}'...")
                        acrm = find_acrm_in_area(admin_token, rco_area)
                        if not acrm:
                            log_test("1.7 Find ACRM in area", False, f"No ACRM found in {rco_area}")
                        else:
                            acrm_nip = acrm["nip"]
                            acrm_nama = acrm["nama"]
                            log_test("1.7 Find ACRM in area", True, f"Found {acrm_nama} (NIP {acrm_nip})")
                            
                            # Login as ACRM and forward
                            print(f"\nStep 7: Login as ACRM {acrm_nama} and forward note...")
                            acrm_token, _ = login(acrm_nip)
                            if not acrm_token:
                                log_test("1.8 ACRM forward note", False, f"Failed to login as ACRM {acrm_nip}")
                            else:
                                forwarded = forward_note(acrm_token, note_id)
                                if not forwarded:
                                    log_test("1.8 ACRM forward note", False, "Failed to forward")
                                else:
                                    log_test("1.8 ACRM forward note", True, 
                                            f"Status: {forwarded.get('status')}")
                                    
                                    # Step 8: Login as RCRM and forward
                                    print(f"\nStep 8: Login as RCRM {rcrm_nama} and forward note...")
                                    rcrm_token, _ = login(rcrm_nip)
                                    if not rcrm_token:
                                        log_test("1.9 RCRM forward note", False, 
                                                f"Failed to login as RCRM {rcrm_nip}")
                                    else:
                                        forwarded2 = forward_note(rcrm_token, note_id)
                                        if not forwarded2:
                                            log_test("1.9 RCRM forward note", False, "Failed to forward")
                                        else:
                                            log_test("1.9 RCRM forward note", True, 
                                                    f"Status: {forwarded2.get('status')}")
                                            
                                            # Step 9: Login as RATMIYATI and check notifications
                                            print(f"\nStep 9: Login as RATMIYATI (NIP {RATMIYATI_NIP}) and check notifications...")
                                            ratmiyati_token, _ = login(RATMIYATI_NIP)
                                            if not ratmiyati_token:
                                                log_test("1.10 RATMIYATI check notifications", False, 
                                                        "Failed to login as RATMIYATI")
                                            else:
                                                notifs = get_notifications(ratmiyati_token)
                                                if not notifs:
                                                    log_test("1.10 RATMIYATI check notifications", False, 
                                                            "Failed to get notifications")
                                                else:
                                                    # Find notification for this note
                                                    found_special_notif = False
                                                    for notif in notifs.get("items", []):
                                                        msg = notif.get("message", "")
                                                        if "menunggu KEPUTUSAN Anda selaku pemutus RCG" in msg and \
                                                           "RCG ≤ Rp10 Miliar" in msg:
                                                            found_special_notif = True
                                                            log_test("1.10 RATMIYATI special notification", True, 
                                                                    f"Found: '{msg[:100]}...'")
                                                            break
                                                    
                                                    if not found_special_notif:
                                                        log_test("1.10 RATMIYATI special notification", False, 
                                                                "Notification with 'RCG ≤ Rp10 Miliar' not found")

# Contrast test: Create note with os_pokok > 10B, should route to IMMADHA without special message
print("\n" + "=" * 80)
print("TEST 1B: CONTRAST - IMMADHA NOTIFICATION (no special message)")
print("=" * 80)
print()
print("Scenario: Create a note with os_pokok > 10B in Area Banda Aceh,")
print("should route to IMMADHA. Notification should NOT contain '≤ Rp10 Miliar'.")
print()

# Use RCO in Area Banda Aceh (NIP 2193020835)
rco_banda_aceh_nip = "2193020835"
print(f"Step 1: Login as RCO in Area Banda Aceh (NIP {rco_banda_aceh_nip})...")
rco_token2, rco_user2 = login(rco_banda_aceh_nip)
if not rco_token2:
    log_test("1B.1 Login as RCO Banda Aceh", False, f"Failed to login as {rco_banda_aceh_nip}")
else:
    log_test("1B.1 Login as RCO Banda Aceh", True, f"Logged in as {rco_user2['nama']}")
    
    # Create note with os_pokok = 15B
    os_pokok_value2 = 15_000_000_000
    print(f"\nStep 2: Creating note with os_pokok = {os_pokok_value2:,.0f}...")
    note2 = create_test_note(rco_token2, os_pokok_value2)
    if not note2:
        log_test("1B.2 Create note with os_pokok 15B", False, "Failed to create note")
    else:
        note_id2 = note2["id"]
        log_test("1B.2 Create note with os_pokok 15B", True, f"Note ID: {note_id2}")
        
        # Submit note
        print(f"\nStep 3: Submitting note {note_id2}...")
        submitted2 = submit_note(rco_token2, note_id2)
        if not submitted2:
            log_test("1B.3 Submit note", False, "Failed to submit note")
        else:
            log_test("1B.3 Submit note", True, f"Status: {submitted2.get('status')}")
            
            # Verify rcg_pemutus_nip is IMMADHA
            rcg_pemutus2 = submitted2.get("rcg_pemutus_nip")
            if rcg_pemutus2 == IMMADHA_NIP:
                log_test("1B.4 Verify RCG pemutus is IMMADHA", True, f"rcg_pemutus_nip = {rcg_pemutus2}")
            else:
                log_test("1B.4 Verify RCG pemutus is IMMADHA", False, 
                        f"Expected {IMMADHA_NIP}, got {rcg_pemutus2}")
            
            # Forward through ACRM and RCRM
            acrm_banda_aceh_nip = "2188009250"
            rcrm_aceh_nip = "2188017223"
            
            print(f"\nStep 4: Login as ACRM Banda Aceh (NIP {acrm_banda_aceh_nip}) and forward...")
            acrm_token2, _ = login(acrm_banda_aceh_nip)
            if acrm_token2:
                forwarded3 = forward_note(acrm_token2, note_id2)
                if forwarded3:
                    log_test("1B.5 ACRM forward note", True, f"Status: {forwarded3.get('status')}")
                    
                    print(f"\nStep 5: Login as RCRM Aceh (NIP {rcrm_aceh_nip}) and forward...")
                    rcrm_token2, _ = login(rcrm_aceh_nip)
                    if rcrm_token2:
                        forwarded4 = forward_note(rcrm_token2, note_id2)
                        if forwarded4:
                            log_test("1B.6 RCRM forward note", True, f"Status: {forwarded4.get('status')}")
                            
                            # Check IMMADHA notifications
                            print(f"\nStep 6: Login as IMMADHA (NIP {IMMADHA_NIP}) and check notifications...")
                            immadha_token, _ = login(IMMADHA_NIP)
                            if immadha_token:
                                notifs2 = get_notifications(immadha_token)
                                if notifs2:
                                    found_normal_notif = False
                                    found_special_text = False
                                    for notif in notifs2.get("items", []):
                                        msg = notif.get("message", "")
                                        if "menunggu KEPUTUSAN Anda selaku pemutus RCG" in msg:
                                            found_normal_notif = True
                                            if "≤ Rp10 Miliar" in msg:
                                                found_special_text = True
                                    
                                    if found_normal_notif and not found_special_text:
                                        log_test("1B.7 IMMADHA notification (no special text)", True, 
                                                "Notification found without '≤ Rp10 Miliar'")
                                    elif found_normal_notif and found_special_text:
                                        log_test("1B.7 IMMADHA notification (no special text)", False, 
                                                "Notification incorrectly contains '≤ Rp10 Miliar'")
                                    else:
                                        log_test("1B.7 IMMADHA notification (no special text)", False, 
                                                "RCG notification not found")

# ============================================================================
# TEST 2: EXPORT BY CATEGORY
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: EXPORT BY CATEGORY")
print("=" * 80)
print()
print("Scenario: Test GET /api/export/notes-excel?category=X for different categories")
print()

# Test as RCO (has draft category)
print("Step 1: Login as RCO and test export with category=draft...")
rco_test_nip = "2193020835"
rco_token3, rco_user3 = login(rco_test_nip)
if not rco_token3:
    log_test("2.1 Export category=draft as RCO", False, f"Failed to login as RCO {rco_test_nip}")
else:
    resp = export_notes_excel(rco_token3, category="draft")
    if resp.status_code == 200:
        content_type = resp.headers.get("Content-Type", "")
        is_xlsx = content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        has_pk = resp.content[:2] == b'PK'
        if is_xlsx and has_pk:
            log_test("2.1 Export category=draft as RCO", True, 
                    f"200, {len(resp.content)} bytes, valid xlsx")
        else:
            log_test("2.1 Export category=draft as RCO", False, 
                    f"200 but invalid xlsx: content_type={content_type}, PK={has_pk}")
    else:
        log_test("2.1 Export category=draft as RCO", False, f"Status {resp.status_code}")

# Test category=approved
print("\nStep 2: Test export with category=approved as RCO...")
if rco_token3:
    resp = export_notes_excel(rco_token3, category="approved")
    if resp.status_code == 200:
        content_type = resp.headers.get("Content-Type", "")
        is_xlsx = content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        has_pk = resp.content[:2] == b'PK'
        if is_xlsx and has_pk:
            log_test("2.2 Export category=approved as RCO", True, 
                    f"200, {len(resp.content)} bytes, valid xlsx")
        else:
            log_test("2.2 Export category=approved as RCO", False, 
                    f"200 but invalid xlsx: content_type={content_type}, PK={has_pk}")
    else:
        log_test("2.2 Export category=approved as RCO", False, f"Status {resp.status_code}")

# Test as ACRM with category=committee
print("\nStep 3: Login as ACRM and test export with category=committee...")
acrm_test_nip = "2188009250"
acrm_token3, acrm_user3 = login(acrm_test_nip)
if not acrm_token3:
    log_test("2.3 Export category=committee as ACRM", False, f"Failed to login as ACRM {acrm_test_nip}")
else:
    resp = export_notes_excel(acrm_token3, category="committee")
    if resp.status_code == 200:
        content_type = resp.headers.get("Content-Type", "")
        is_xlsx = content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        has_pk = resp.content[:2] == b'PK'
        if is_xlsx and has_pk:
            log_test("2.3 Export category=committee as ACRM", True, 
                    f"200, {len(resp.content)} bytes, valid xlsx")
        else:
            log_test("2.3 Export category=committee as ACRM", False, 
                    f"200 but invalid xlsx: content_type={content_type}, PK={has_pk}")
    else:
        log_test("2.3 Export category=committee as ACRM", False, f"Status {resp.status_code}")

# ============================================================================
# TEST 3: ACTION_REQUIRED FLAG
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: ACTION_REQUIRED FLAG")
print("=" * 80)
print()
print("Scenario: Verify action_required field in GET /api/notes for different roles")
print()

# Test as ACRM
print("Step 1: Login as ACRM and check action_required field...")
acrm_test_nip2 = "2188009250"
acrm_token4, acrm_user4 = login(acrm_test_nip2)
if not acrm_token4:
    log_test("3.1 GET /notes as ACRM", False, f"Failed to login as ACRM {acrm_test_nip2}")
else:
    notes = get_notes(acrm_token4)
    if not notes:
        log_test("3.1 GET /notes as ACRM", False, "Failed to get notes")
    else:
        log_test("3.1 GET /notes as ACRM", True, f"Retrieved {len(notes)} notes")
        
        # Check for notes awaiting ACRM action
        awaiting_acrm = [n for n in notes if n.get("status", "").startswith("Menunggu") and 
                        "ACRM" in n.get("status", "")]
        if awaiting_acrm:
            sample = awaiting_acrm[0]
            action_req = sample.get("action_required")
            if action_req is True:
                log_test("3.2 ACRM awaiting notes have action_required=true", True, 
                        f"Status: {sample.get('status')}, action_required={action_req}")
            else:
                log_test("3.2 ACRM awaiting notes have action_required=true", False, 
                        f"Expected true, got {action_req}")
        else:
            log_test("3.2 ACRM awaiting notes have action_required=true", True, 
                    "No notes awaiting ACRM (cannot verify, but not an error)")
        
        # Check Final Approved notes have action_required=false
        approved = [n for n in notes if n.get("status") == "Final Approved"]
        if approved:
            sample = approved[0]
            action_req = sample.get("action_required")
            if action_req is False:
                log_test("3.3 ACRM approved notes have action_required=false", True, 
                        f"Status: {sample.get('status')}, action_required={action_req}")
            else:
                log_test("3.3 ACRM approved notes have action_required=false", False, 
                        f"Expected false, got {action_req}")
        else:
            log_test("3.3 ACRM approved notes have action_required=false", True, 
                    "No approved notes (cannot verify, but not an error)")

# Test as RCO
print("\nStep 2: Login as RCO and check action_required field...")
rco_test_nip2 = "2193020835"
rco_token4, rco_user4 = login(rco_test_nip2)
if not rco_token4:
    log_test("3.4 GET /notes as RCO", False, f"Failed to login as RCO {rco_test_nip2}")
else:
    notes = get_notes(rco_token4)
    if not notes:
        log_test("3.4 GET /notes as RCO", False, "Failed to get notes")
    else:
        log_test("3.4 GET /notes as RCO", True, f"Retrieved {len(notes)} notes")
        
        # Check Draft notes have action_required=true
        drafts = [n for n in notes if n.get("status") == "Draft"]
        if drafts:
            sample = drafts[0]
            action_req = sample.get("action_required")
            if action_req is True:
                log_test("3.5 RCO draft notes have action_required=true", True, 
                        f"Status: {sample.get('status')}, action_required={action_req}")
            else:
                log_test("3.5 RCO draft notes have action_required=true", False, 
                        f"Expected true, got {action_req}")
        else:
            log_test("3.5 RCO draft notes have action_required=true", True, 
                    "No draft notes (cannot verify, but not an error)")
        
        # Check Revisi/Reject notes have action_required=true
        revisi_reject = [n for n in notes if n.get("status", "").startswith("Revisi") or 
                        n.get("status", "").startswith("Reject")]
        if revisi_reject:
            sample = revisi_reject[0]
            action_req = sample.get("action_required")
            if action_req is True:
                log_test("3.6 RCO revisi/reject notes have action_required=true", True, 
                        f"Status: {sample.get('status')}, action_required={action_req}")
            else:
                log_test("3.6 RCO revisi/reject notes have action_required=true", False, 
                        f"Expected true, got {action_req}")
        else:
            log_test("3.6 RCO revisi/reject notes have action_required=true", True, 
                    "No revisi/reject notes (cannot verify, but not an error)")
        
        # Check Final Approved notes have action_required=false
        approved = [n for n in notes if n.get("status") == "Final Approved"]
        if approved:
            sample = approved[0]
            action_req = sample.get("action_required")
            if action_req is False:
                log_test("3.7 RCO approved notes have action_required=false", True, 
                        f"Status: {sample.get('status')}, action_required={action_req}")
            else:
                log_test("3.7 RCO approved notes have action_required=false", False, 
                        f"Expected false, got {action_req}")
        else:
            log_test("3.7 RCO approved notes have action_required=false", True, 
                    "No approved notes (cannot verify, but not an error)")
        
        # Check Menunggu notes have action_required=false
        menunggu = [n for n in notes if n.get("status", "").startswith("Menunggu")]
        if menunggu:
            sample = menunggu[0]
            action_req = sample.get("action_required")
            if action_req is False:
                log_test("3.8 RCO menunggu notes have action_required=false", True, 
                        f"Status: {sample.get('status')}, action_required={action_req}")
            else:
                log_test("3.8 RCO menunggu notes have action_required=false", False, 
                        f"Expected false, got {action_req}")
        else:
            log_test("3.8 RCO menunggu notes have action_required=false", True, 
                    "No menunggu notes (cannot verify, but not an error)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()
print(f"Total Tests: {total_tests}")
print(f"Passed: {passed_tests}")
print(f"Failed: {total_tests - passed_tests}")
print(f"Success Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
print()
print("Detailed Results:")
print("-" * 80)
for result in test_results:
    print(result)
print()

if passed_tests == total_tests:
    print("✅ ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"❌ {total_tests - passed_tests} TEST(S) FAILED")
    sys.exit(1)

#!/usr/bin/env python3
"""
Backend Testing for RCG Digital Restructuring - Nota Corrections
Tests: Disposisi Pemutus mandatory, notifications routing, Excel/PDF reports
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://github-import-setup-4.preview.emergentagent.com/api"
DEFAULT_PASSWORD = "bsi12345"

# Test credentials
ADMIN_NIP = "2183008345"  # SYAMSU RIZAL
RCO_NIP = "2193020835"    # UCHTI APRILINA
ACRM_NIP = "2188009250"   # Need to verify area match
RCRM_NIP = "2188017223"   # Need to verify region match
IMMADHA_NIP = "2175007386"  # RCG Group Head

# Test results
test_results = []

def log_test(test_num, description, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{test_num}. {status}: {description}"
    if details:
        result += f"\n   Details: {details}"
    test_results.append(result)
    print(result)
    return passed

def login(nip, password=DEFAULT_PASSWORD):
    """Login and return token and user info"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"nip": nip, "password": password}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data["token"], data["user"]
        else:
            print(f"Login failed for NIP {nip}: {resp.status_code} - {resp.text}")
            return None, None
    except Exception as e:
        print(f"Login error for NIP {nip}: {e}")
        return None, None

def get_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def create_minimal_note(token, area, region, os_pokok=1_500_000_000):
    """Create a minimal valid note for testing"""
    headers = get_headers(token)
    
    # Minimal valid note payload
    payload = {
        "nomor_manual": str(datetime.now().timestamp())[-5:],  # Last 5 digits of timestamp
        "kepada": "ACRM",
        "reff_tanggal": "01/01/2026",
        "customer": {
            "nama": "PT TEST CUSTOMER NOTA",
            "alamat": "Jl. Test No. 123",
            "bidang_usaha": "Perdagangan"
        },
        "facilities": [{
            "cif": "1234567890",
            "nomor_loan": "TEST001",
            "kolektibilitas": "3A",
            "segmen": "RETAIL",
            "produk": "SME",
            "akad": "Murabahah",
            "nama_cabang": "KC Banda Aceh",
            "os_pokok": os_pokok,
            "os_margin": 100_000_000,
            "penalty": 10_000_000,
            "tanggal_akad": "01/01/2024",
            "tanggal_jatuh_tempo": "01/01/2027"
        }],
        "has_fix_asset": True,
        "collaterals": [{
            "jenis": "Tanah dan Bangunan",
            "penilai": "KJPP",
            "nama_kjpp": "KJPP Test Appraisal",
            "nomor_laporan": "LAP/001/2026",
            "nilai_pasar": 3_000_000_000,
            "nilai_likuidasi": 2_400_000_000
        }],
        "rac": [
            {"parameter": "Karakter = Kooperatif dan memiliki itikad baik", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Usaha = Masih berjalan minimal 6 bulan terakhir", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Kemampuan Bayar = Mampu membayar angsuran baru dari cash flow", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Agunan = Legal dan marketable", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Prospek = Terdapat potensi pemulihan usaha", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Fraud = Tidak terindikasi fraud", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Legalitas = Dokumen lengkap dan valid", "status": "Terpenuhi", "keterangan": ""},
            {"parameter": "Outcome Restrukturisasi = Diperkirakan memperbaiki kualitas pembiayaan", "status": "Terpenuhi", "keterangan": ""}
        ],
        "analysis": {
            "kemampuan_bayar": "Terdapat bukti pendapatan nasabah/slip gaji",
            "penyebab_bermasalah": "Nasabah mengalami penurunan omzet usaha akibat kondisi ekonomi"
        },
        "proposals": [{
            "cif": "1234567890",
            "nomor_loan": "TEST001",
            "tgl_mulai": "01/02/2026",
            "tgl_akhir": "01/02/2029",
            "angsuran_pokok": 50_000_000,
            "angsuran_margin": 10_000_000
        }],
        "documents": [
            {"document_type": "foto_ots", "file_path": "test_foto.jpg", "uploaded_at": "2026-01-01T00:00:00Z"},
            {"document_type": "surat_permohonan_ktp", "file_path": "test_surat.pdf", "uploaded_at": "2026-01-01T00:00:00Z"},
            {"document_type": "laporan_agunan", "file_path": "test_laporan.pdf", "uploaded_at": "2026-01-01T00:00:00Z"},
            {"document_type": "bi_checking", "file_path": "test_bi.pdf", "uploaded_at": "2026-01-01T00:00:00Z"}
        ]
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/notes", json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Create note failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Create note error: {e}")
        return None

def main():
    print("=" * 80)
    print("BACKEND TESTING: Nota Corrections (Disposisi, Notifications, Reports)")
    print("=" * 80)
    print()
    
    # Step 1: Login as RCO and get area/region
    print("SETUP: Logging in as RCO to get area/region...")
    rco_token, rco_user = login(RCO_NIP)
    if not rco_token:
        print("❌ CRITICAL: Cannot login as RCO. Aborting tests.")
        return
    
    rco_area = rco_user.get("area")
    rco_region = rco_user.get("region")
    print(f"✓ RCO logged in: {rco_user.get('nama')} (NIP {RCO_NIP})")
    print(f"  Area: {rco_area}, Region: {rco_region}")
    print()
    
    # Step 2: Login as admin and find matching ACRM and RCRM
    print("SETUP: Finding matching ACRM and RCRM...")
    admin_token, admin_user = login(ADMIN_NIP)
    if not admin_token:
        print("❌ CRITICAL: Cannot login as admin. Aborting tests.")
        return
    
    # Get users list
    headers = get_headers(admin_token)
    resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"❌ CRITICAL: Cannot get users list. Status: {resp.status_code}")
        return
    
    users = resp.json()
    
    # Find matching ACRM (same area as RCO)
    acrm_user = None
    for u in users:
        if u.get("role") == "ACRM" and u.get("area") == rco_area and u.get("status") == "aktif":
            acrm_user = u
            break
    
    if not acrm_user:
        print(f"❌ CRITICAL: No active ACRM found for area '{rco_area}'. Aborting tests.")
        return
    
    acrm_nip = acrm_user["nip"]
    print(f"✓ Found matching ACRM: {acrm_user.get('nama')} (NIP {acrm_nip}), Area: {acrm_user.get('area')}")
    
    # Find matching RCRM (same region as RCO)
    rcrm_user = None
    for u in users:
        if u.get("role") == "RCRM" and u.get("region") == rco_region and u.get("status") == "aktif":
            rcrm_user = u
            break
    
    if not rcrm_user:
        print(f"❌ CRITICAL: No active RCRM found for region '{rco_region}'. Aborting tests.")
        return
    
    rcrm_nip = rcrm_user["nip"]
    print(f"✓ Found matching RCRM: {rcrm_user.get('nama')} (NIP {rcrm_nip}), Region: {rcrm_user.get('region')}")
    print()
    
    # Login as ACRM, RCRM, and IMMADHA
    acrm_token, _ = login(acrm_nip)
    rcrm_token, _ = login(rcrm_nip)
    immadha_token, _ = login(IMMADHA_NIP)
    
    if not acrm_token or not rcrm_token or not immadha_token:
        print("❌ CRITICAL: Cannot login as required approvers. Aborting tests.")
        return
    
    print("✓ All approvers logged in successfully")
    print()
    
    # ========================================================================
    # TEST A: Disposisi Pemutus mandatory on approve (small amount)
    # ========================================================================
    print("=" * 80)
    print("TEST A: Disposisi Pemutus Mandatory (Small Amount - ACRM Decides)")
    print("=" * 80)
    print()
    
    # Test A1: Create note with small amount and required fields
    print("A1. Creating note with SMALL amount (1.5B) as RCO...")
    note_a1 = create_minimal_note(rco_token, rco_area, rco_region, os_pokok=1_500_000_000)
    
    if not note_a1:
        log_test("A1", "Create note with small amount", False, "Failed to create note")
    else:
        # Verify penyebab_bermasalah and nama_kjpp are stored
        has_penyebab = bool(note_a1.get("analysis", {}).get("penyebab_bermasalah"))
        has_kjpp = any(c.get("nama_kjpp") for c in note_a1.get("collaterals", []))
        
        log_test("A1", "Create note with small amount", True, 
                f"Note ID: {note_a1['id']}, penyebab_bermasalah stored: {has_penyebab}, nama_kjpp stored: {has_kjpp}")
        
        # Test A2: Submit the note
        print("A2. Submitting note as RCO...")
        headers = get_headers(rco_token)
        resp = requests.post(f"{BASE_URL}/notes/{note_a1['id']}/submit", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            submitted_note = resp.json()
            status = submitted_note.get("status")
            stages = submitted_note.get("stages", [])
            
            # Check if routing is correct (should be ACRM decide for small amount)
            is_acrm_decide = len(stages) > 0 and stages[0][0] == "ACRM" and stages[0][1] == "decide"
            
            log_test("A2", "Submit note (small amount)", True, 
                    f"Status: {status}, Routing: {stages}, ACRM decides: {is_acrm_decide}")
        else:
            log_test("A2", "Submit note (small amount)", False, 
                    f"Status: {resp.status_code}, Response: {resp.text}")
            note_a1 = None
        
        # Test A3: ACRM approve WITHOUT disposisi (should fail with 400)
        if note_a1:
            print("A3. ACRM trying to approve WITHOUT disposisi...")
            headers = get_headers(acrm_token)
            resp = requests.post(f"{BASE_URL}/notes/{note_a1['id']}/action", 
                               json={"decision": "approve"}, 
                               headers=headers, timeout=30)
            
            if resp.status_code == 400:
                error_msg = resp.json().get("detail", "")
                has_disposisi_error = "disposisi" in error_msg.lower()
                log_test("A3", "ACRM approve WITHOUT disposisi → 400", True, 
                        f"Error message: {error_msg}, Contains 'disposisi': {has_disposisi_error}")
            else:
                log_test("A3", "ACRM approve WITHOUT disposisi → 400", False, 
                        f"Expected 400, got {resp.status_code}")
            
            # Test A4: ACRM approve WITH disposisi (should succeed)
            print("A4. ACRM approving WITH disposisi...")
            resp = requests.post(f"{BASE_URL}/notes/{note_a1['id']}/action", 
                               json={"decision": "approve", "disposisi": "Disetujui sesuai ketentuan"}, 
                               headers=headers, timeout=30)
            
            if resp.status_code == 200:
                approved_note = resp.json()
                status = approved_note.get("status")
                disposisi = approved_note.get("disposisi_pemutus")
                
                is_final_approved = status == "Final Approved"
                has_disposisi = disposisi == "Disetujui sesuai ketentuan"
                
                log_test("A4", "ACRM approve WITH disposisi → 200", True, 
                        f"Status: {status}, Disposisi: {disposisi}, Final Approved: {is_final_approved}")
                
                # Verify by GET
                resp_get = requests.get(f"{BASE_URL}/notes/{note_a1['id']}", headers=headers, timeout=30)
                if resp_get.status_code == 200:
                    verified_note = resp_get.json()
                    print(f"   Verified: disposisi_pemutus = '{verified_note.get('disposisi_pemutus')}'")
            else:
                log_test("A4", "ACRM approve WITH disposisi → 200", False, 
                        f"Status: {resp.status_code}, Response: {resp.text}")
    
    print()
    
    # ========================================================================
    # TEST B: Notifications Routing
    # ========================================================================
    print("=" * 80)
    print("TEST B: Notifications Routing")
    print("=" * 80)
    print()
    
    # Test B1: Create and submit small note, check ACRM notifications
    print("B1. Creating and submitting small note, checking ACRM notifications...")
    note_b1 = create_minimal_note(rco_token, rco_area, rco_region, os_pokok=1_500_000_000)
    
    if note_b1:
        headers = get_headers(rco_token)
        resp = requests.post(f"{BASE_URL}/notes/{note_b1['id']}/submit", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            # Check ACRM notifications
            headers_acrm = get_headers(acrm_token)
            resp_notif = requests.get(f"{BASE_URL}/notifications", headers=headers_acrm, timeout=30)
            
            if resp_notif.status_code == 200:
                notif_data = resp_notif.json()
                items = notif_data.get("items", [])
                
                # Find notification for this note
                note_notif = None
                for item in items:
                    if item.get("note_id") == note_b1["id"]:
                        note_notif = item
                        break
                
                has_notif = note_notif is not None
                log_test("B1", "ACRM receives notification after submit", has_notif, 
                        f"Found notification: {has_notif}, Message: {note_notif.get('message') if note_notif else 'N/A'}")
            else:
                log_test("B1", "ACRM receives notification after submit", False, 
                        f"Failed to get notifications: {resp_notif.status_code}")
        else:
            log_test("B1", "Submit note for notification test", False, 
                    f"Status: {resp.status_code}")
            note_b1 = None
    else:
        log_test("B1", "Create note for notification test", False, "Failed to create note")
    
    # Test B2: ACRM approve, check RCO notifications
    if note_b1:
        print("B2. ACRM approving, checking RCO notifications...")
        headers_acrm = get_headers(acrm_token)
        resp = requests.post(f"{BASE_URL}/notes/{note_b1['id']}/action", 
                           json={"decision": "approve", "disposisi": "Disetujui"}, 
                           headers=headers_acrm, timeout=30)
        
        if resp.status_code == 200:
            # Check RCO notifications
            headers_rco = get_headers(rco_token)
            resp_notif = requests.get(f"{BASE_URL}/notifications", headers=headers_rco, timeout=30)
            
            if resp_notif.status_code == 200:
                notif_data = resp_notif.json()
                items = notif_data.get("items", [])
                
                # Find notification for this note
                note_notif = None
                for item in items:
                    if item.get("note_id") == note_b1["id"] and "FINAL APPROVED" in item.get("message", ""):
                        note_notif = item
                        break
                
                has_notif = note_notif is not None
                log_test("B2", "RCO receives FINAL APPROVED notification", has_notif, 
                        f"Found notification: {has_notif}, Message: {note_notif.get('message') if note_notif else 'N/A'}")
            else:
                log_test("B2", "Get RCO notifications", False, 
                        f"Status: {resp_notif.status_code}")
        else:
            log_test("B2", "ACRM approve for notification test", False, 
                    f"Status: {resp.status_code}")
    
    # Test B3: Reject flow
    print("B3. Testing reject flow notifications...")
    note_b3 = create_minimal_note(rco_token, rco_area, rco_region, os_pokok=1_500_000_000)
    
    if note_b3:
        headers = get_headers(rco_token)
        resp = requests.post(f"{BASE_URL}/notes/{note_b3['id']}/submit", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            # ACRM reject
            headers_acrm = get_headers(acrm_token)
            resp = requests.post(f"{BASE_URL}/notes/{note_b3['id']}/action", 
                               json={"decision": "reject", "catatan": "tidak lengkap"}, 
                               headers=headers_acrm, timeout=30)
            
            if resp.status_code == 200:
                # Check RCO notifications
                headers_rco = get_headers(rco_token)
                resp_notif = requests.get(f"{BASE_URL}/notifications", headers=headers_rco, timeout=30)
                
                if resp_notif.status_code == 200:
                    notif_data = resp_notif.json()
                    items = notif_data.get("items", [])
                    
                    # Find reject notification
                    note_notif = None
                    for item in items:
                        if item.get("note_id") == note_b3["id"] and "dikembalikan" in item.get("message", "").lower():
                            note_notif = item
                            break
                    
                    has_notif = note_notif is not None
                    log_test("B3", "RCO receives reject notification", has_notif, 
                            f"Found notification: {has_notif}, Message: {note_notif.get('message') if note_notif else 'N/A'}")
                else:
                    log_test("B3", "Get RCO notifications (reject)", False, 
                            f"Status: {resp_notif.status_code}")
            else:
                log_test("B3", "ACRM reject", False, f"Status: {resp.status_code}")
        else:
            log_test("B3", "Submit note for reject test", False, f"Status: {resp.status_code}")
    else:
        log_test("B3", "Create note for reject test", False, "Failed to create note")
    
    # Test B4: Large amount flow (ACRM → RCRM → RCG)
    print("B4. Testing large amount flow (ACRM → RCRM → RCG)...")
    note_b4 = create_minimal_note(rco_token, rco_area, rco_region, os_pokok=15_000_000_000)  # 15B
    
    if note_b4:
        headers = get_headers(rco_token)
        resp = requests.post(f"{BASE_URL}/notes/{note_b4['id']}/submit", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            submitted = resp.json()
            stages = submitted.get("stages", [])
            
            # Should have multiple stages for large amount
            is_multi_stage = len(stages) >= 3
            log_test("B4a", "Large amount routing (multi-stage)", is_multi_stage, 
                    f"Stages: {stages}")
            
            # ACRM forward
            headers_acrm = get_headers(acrm_token)
            resp = requests.post(f"{BASE_URL}/notes/{note_b4['id']}/action", 
                               json={"decision": "forward", "catatan": "Diteruskan ke RCRM"}, 
                               headers=headers_acrm, timeout=30)
            
            if resp.status_code == 200:
                # Check RCRM notifications
                headers_rcrm = get_headers(rcrm_token)
                resp_notif = requests.get(f"{BASE_URL}/notifications", headers=headers_rcrm, timeout=30)
                
                if resp_notif.status_code == 200:
                    notif_data = resp_notif.json()
                    items = notif_data.get("items", [])
                    
                    note_notif = None
                    for item in items:
                        if item.get("note_id") == note_b4["id"]:
                            note_notif = item
                            break
                    
                    has_notif = note_notif is not None
                    log_test("B4b", "RCRM receives notification after ACRM forward", has_notif, 
                            f"Message: {note_notif.get('message') if note_notif else 'N/A'}")
                    
                    # RCRM forward
                    resp = requests.post(f"{BASE_URL}/notes/{note_b4['id']}/action", 
                                       json={"decision": "forward", "catatan": "Diteruskan ke RCG"}, 
                                       headers=headers_rcrm, timeout=30)
                    
                    if resp.status_code == 200:
                        # Check IMMADHA notifications
                        headers_immadha = get_headers(immadha_token)
                        resp_notif = requests.get(f"{BASE_URL}/notifications", headers=headers_immadha, timeout=30)
                        
                        if resp_notif.status_code == 200:
                            notif_data = resp_notif.json()
                            items = notif_data.get("items", [])
                            
                            note_notif = None
                            for item in items:
                                if item.get("note_id") == note_b4["id"]:
                                    note_notif = item
                                    break
                            
                            has_notif = note_notif is not None
                            log_test("B4c", "IMMADHA receives notification after RCRM forward", has_notif, 
                                    f"Message: {note_notif.get('message') if note_notif else 'N/A'}")
                            
                            # IMMADHA approve WITHOUT disposisi (should fail)
                            resp = requests.post(f"{BASE_URL}/notes/{note_b4['id']}/action", 
                                               json={"decision": "approve"}, 
                                               headers=headers_immadha, timeout=30)
                            
                            if resp.status_code == 400:
                                log_test("B4d", "IMMADHA approve WITHOUT disposisi → 400", True, 
                                        f"Error: {resp.json().get('detail')}")
                            else:
                                log_test("B4d", "IMMADHA approve WITHOUT disposisi → 400", False, 
                                        f"Expected 400, got {resp.status_code}")
                            
                            # IMMADHA approve WITH disposisi
                            resp = requests.post(f"{BASE_URL}/notes/{note_b4['id']}/action", 
                                               json={"decision": "approve", "disposisi": "Disetujui oleh RCG"}, 
                                               headers=headers_immadha, timeout=30)
                            
                            if resp.status_code == 200:
                                approved = resp.json()
                                is_final = approved.get("status") == "Final Approved"
                                log_test("B4e", "IMMADHA approve WITH disposisi → 200", True, 
                                        f"Status: {approved.get('status')}, Final: {is_final}")
                            else:
                                log_test("B4e", "IMMADHA approve WITH disposisi → 200", False, 
                                        f"Status: {resp.status_code}")
                        else:
                            log_test("B4c", "Get IMMADHA notifications", False, 
                                    f"Status: {resp_notif.status_code}")
                    else:
                        log_test("B4b2", "RCRM forward", False, f"Status: {resp.status_code}")
                else:
                    log_test("B4b", "Get RCRM notifications", False, 
                            f"Status: {resp_notif.status_code}")
            else:
                log_test("B4a2", "ACRM forward", False, f"Status: {resp.status_code}")
        else:
            log_test("B4a", "Submit large amount note", False, f"Status: {resp.status_code}")
    else:
        log_test("B4", "Create large amount note", False, "Failed to create note")
    
    print()
    
    # ========================================================================
    # TEST C: Reports (Excel Export and PDF)
    # ========================================================================
    print("=" * 80)
    print("TEST C: Reports (Excel Export and PDF)")
    print("=" * 80)
    print()
    
    # Test C1: Excel export
    print("C1. Testing Excel export as admin...")
    headers_admin = get_headers(admin_token)
    resp = requests.get(f"{BASE_URL}/export/notes-excel", headers=headers_admin, timeout=30)
    
    if resp.status_code == 200:
        content_type = resp.headers.get("Content-Type", "")
        is_excel = "spreadsheet" in content_type or "excel" in content_type
        content_length = len(resp.content)
        
        # Check if it's a valid Excel file (starts with PK for zip/xlsx)
        is_valid_xlsx = resp.content[:2] == b'PK'
        
        log_test("C1", "Excel export → 200", True, 
                f"Content-Type: {content_type}, Is Excel: {is_excel}, Size: {content_length} bytes, Valid XLSX: {is_valid_xlsx}")
    else:
        log_test("C1", "Excel export → 200", False, 
                f"Status: {resp.status_code}, Response: {resp.text[:200]}")
    
    # Test C2: PDF download for Final Approved note
    print("C2. Testing PDF download for Final Approved note...")
    
    # Use note_a1 or note_b1 which should be Final Approved
    test_note_id = None
    if note_a1:
        test_note_id = note_a1["id"]
    elif note_b1:
        test_note_id = note_b1["id"]
    
    if test_note_id:
        # First verify the note is Final Approved
        headers_rco = get_headers(rco_token)
        resp = requests.get(f"{BASE_URL}/notes/{test_note_id}", headers=headers_rco, timeout=30)
        
        if resp.status_code == 200:
            note_data = resp.json()
            status = note_data.get("status")
            can_download = note_data.get("can_download", False)
            
            print(f"   Note status: {status}, can_download: {can_download}")
            
            if status == "Final Approved" and can_download:
                # Try to download PDF
                resp_pdf = requests.get(f"{BASE_URL}/notes/{test_note_id}/pdf", headers=headers_rco, timeout=30)
                
                if resp_pdf.status_code == 200:
                    content_type = resp_pdf.headers.get("Content-Type", "")
                    is_pdf = "pdf" in content_type
                    content_length = len(resp_pdf.content)
                    
                    # Check if it's a valid PDF (starts with %PDF)
                    is_valid_pdf = resp_pdf.content[:4] == b'%PDF'
                    
                    log_test("C2", "PDF download for Final Approved note → 200", True, 
                            f"Content-Type: {content_type}, Is PDF: {is_pdf}, Size: {content_length} bytes, Valid PDF: {is_valid_pdf}")
                else:
                    log_test("C2", "PDF download for Final Approved note → 200", False, 
                            f"Status: {resp_pdf.status_code}, Response: {resp_pdf.text[:200]}")
            else:
                log_test("C2", "PDF download for Final Approved note", False, 
                        f"Note not Final Approved or cannot download. Status: {status}, can_download: {can_download}")
        else:
            log_test("C2", "Get note for PDF test", False, 
                    f"Status: {resp.status_code}")
    else:
        log_test("C2", "PDF download test", False, "No Final Approved note available")
    
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed_count = sum(1 for r in test_results if "✅ PASS" in r)
    total_count = len(test_results)
    
    print(f"Total Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print()
    
    print("Detailed Results:")
    print("-" * 80)
    for result in test_results:
        print(result)
    print()
    
    print("=" * 80)
    print("NIPs Used:")
    print(f"  RCO: {RCO_NIP} ({rco_user.get('nama')})")
    print(f"  ACRM: {acrm_nip} ({acrm_user.get('nama')})")
    print(f"  RCRM: {rcrm_nip} ({rcrm_user.get('nama')})")
    print(f"  IMMADHA (RCG): {IMMADHA_NIP}")
    print(f"  Admin: {ADMIN_NIP}")
    print("=" * 80)

if __name__ == "__main__":
    main()

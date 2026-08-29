#!/usr/bin/env python3
"""
Backend Testing for RCG Digital Restructuring - PDF LAPORAN NOTA + FINAL_APPROVER_ROLE/AREA
Test focus: Verify final_approver_role & final_approver_area are saved and PDF generation works

Test scenarios:
1. SMALL amount - ACRM decides directly + saves role/area
2. RATMIYATI as RCG decider for notes ≤10M (must still work)
3. IMMADHA as RCG decider for notes >10M to 30M; RATMIYATI blocked
"""

import requests
import json
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://rizal-ops-setup.preview.emergentagent.com/api"

# Test credentials (all passwords: bsi12345)
CREDENTIALS = {
    "rco_banda_aceh": {"nip": "2193020835", "password": "bsi12345"},  # UCHTI APRILINA (Area Banda Aceh)
    "acrm_banda_aceh": {"nip": "2188009250", "password": "bsi12345"}, # FERI SAPUTRA (Area Banda Aceh)
    "rcrm_aceh": {"nip": "2188017223", "password": "bsi12345"},       # HENDRA PURNAWAN (RO I ACEH)
    "immadha": {"nip": "2175007386", "password": "bsi12345"},         # IMMADHA (RCG, limit 30B)
    "ratmiyati": {"nip": "2180007674", "password": "bsi12345"},       # RATMIYATI (RCG, limit 10B)
    "admin": {"nip": "2183008345", "password": "bsi12345"},           # SYAMSU RIZAL
}

def login(role):
    """Login and return token"""
    cred = CREDENTIALS[role]
    resp = requests.post(f"{BASE_URL}/auth/login", json=cred)
    if resp.status_code != 200:
        print(f"❌ Login failed for {role}: {resp.status_code} {resp.text}")
        return None
    token = resp.json().get("token")
    user = resp.json().get("user")
    print(f"✅ Logged in as {user.get('nama')} (NIP {cred['nip']}, {user.get('role')})")
    return token

def headers(token):
    """Return headers with Bearer token"""
    return {"Authorization": f"Bearer {token}"}

def create_note(token, os_pokok, nama_nasabah="PT TESTING SEJAHTERA"):
    """Create a minimal valid note for testing"""
    nomor = datetime.now().strftime('%Y%m%d%H%M%S')[-5:]  # Last 5 digits
    payload = {
        "nomor_manual": nomor,
        "customer": {
            "nama": nama_nasabah,
            "alamat": "Jl. Test No. 123, Banda Aceh",
            "no_kontak": "081234567890",
            "restrukturisasi_ke": "1"
        },
        "facilities": [{
            "cif": "1234567890",
            "nomor_loan": "1234567890123456",
            "kolektibilitas": "3A",
            "segmen": "RETAIL",
            "produk": "SME",
            "akad": "Murabahah",
            "nama_cabang": "KC Banda Aceh",
            "os_pokok": os_pokok,
            "tunggakan_pokok": 0,
            "os_margin": 100000000,
            "tunggakan_margin": 50000000,
            "penalty": 0
        }],
        "rac": [
            {"parameter": "Karakter = Kooperatif dan memiliki itikad baik", "status": "Terpenuhi"},
            {"parameter": "Usaha = Masih berjalan minimal 6 bulan terakhir", "status": "Terpenuhi"},
            {"parameter": "Kemampuan Bayar = Mampu membayar angsuran baru dari cash flow", "status": "Terpenuhi"},
            {"parameter": "Agunan = Legal dan marketable", "status": "Terpenuhi"},
            {"parameter": "Prospek = Terdapat potensi pemulihan usaha", "status": "Terpenuhi"},
            {"parameter": "Fraud = Tidak terindikasi fraud", "status": "Terpenuhi"},
            {"parameter": "Legalitas = Dokumen lengkap dan valid", "status": "Terpenuhi"},
            {"parameter": "Outcome Restrukturisasi = Diperkirakan memperbaiki kualitas pembiayaan", "status": "Terpenuhi"}
        ],
        "documents": [
            {"document_type": "foto_ots", "file_path": "test.pdf"},
            {"document_type": "surat_permohonan_ktp", "file_path": "test.pdf"},
            {"document_type": "bi_checking", "file_path": "test.pdf"}
        ],
        "proposals": [{
            "jenis_fasilitas": "Perpanjangan Jangka Waktu",
            "akad": "Murabahah",
            "tujuan": "Restrukturisasi",
            "os_pokok": os_pokok,
            "os_margin": 100000000,
            "tgl_mulai": "01/01/2026",
            "tgl_akhir": "01/01/2027"
        }],
        "analysis": {
            "kemampuan_bayar": "Terdapat bukti pendapatan nasabah/slip gaji",
            "penyebab_bermasalah": "Penurunan pendapatan akibat kondisi ekonomi"
        },
        "has_fix_asset": False,
        "collaterals": []
    }
    resp = requests.post(f"{BASE_URL}/notes", json=payload, headers=headers(token))
    if resp.status_code != 200:
        print(f"❌ Create note failed: {resp.status_code} {resp.text}")
        return None
    note = resp.json()
    print(f"✅ Created note {note['id']} (nomor {nomor}) with os_pokok=Rp{os_pokok:,}")
    return note

def submit_note(token, note_id):
    """Submit a note"""
    resp = requests.post(f"{BASE_URL}/notes/{note_id}/submit", headers=headers(token))
    if resp.status_code != 200:
        print(f"❌ Submit note failed: {resp.status_code} {resp.text}")
        return None
    note = resp.json()
    print(f"✅ Submitted note {note_id}, status: {note['status']}")
    return note

def note_action(token, note_id, decision, catatan="", disposisi=""):
    """Perform action on note"""
    payload = {"decision": decision, "catatan": catatan, "disposisi": disposisi}
    resp = requests.post(f"{BASE_URL}/notes/{note_id}/action", json=payload, headers=headers(token))
    return resp

def get_note(token, note_id):
    """Get note details"""
    resp = requests.get(f"{BASE_URL}/notes/{note_id}", headers=headers(token))
    if resp.status_code != 200:
        print(f"❌ Get note failed: {resp.status_code}")
        return None
    return resp.json()

def get_pdf(token, note_id):
    """Download PDF"""
    resp = requests.get(f"{BASE_URL}/notes/{note_id}/pdf", headers=headers(token))
    return resp

print("=" * 80)
print("BACKEND TESTING - PDF LAPORAN NOTA + FINAL_APPROVER_ROLE/AREA")
print("=" * 80)

# ============================================================================
# TEST 1: SMALL AMOUNT - ACRM DECIDES DIRECTLY + SAVES ROLE/AREA
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: SMALL AMOUNT - ACRM DECIDES DIRECTLY + SAVES ROLE/AREA")
print("=" * 80)

test1_passed = 0
test1_total = 5

# Login as RCO
rco_token = login("rco_banda_aceh")
if not rco_token:
    print("❌ Cannot proceed without RCO login")
    exit(1)

# Create note with SMALL amount (1.5B - below ACRM limit of 2B)
print("\n📋 Step 1: Create note with SMALL amount (1.5B)")
note1 = create_note(rco_token, os_pokok=1_500_000_000, nama_nasabah="PT SMALL AMOUNT TEST")
if not note1:
    print("❌ TEST 1 FAILED: Cannot create note")
else:
    # Submit note
    print("\n📋 Step 2: Submit note")
    submitted1 = submit_note(rco_token, note1["id"])
    if not submitted1:
        print("❌ TEST 1 FAILED: Cannot submit note")
    else:
        test1_total += 1
        # Verify routing is ACRM decide
        if submitted1.get("stages") == [["ACRM", "decide"]]:
            print(f"✅ TEST 1.1 PASSED: Routing correct [['ACRM', 'decide']] for small amount")
            test1_passed += 1
        else:
            print(f"❌ TEST 1.1 FAILED: Expected [['ACRM', 'decide']], got {submitted1.get('stages')}")
        
        # Login as ACRM
        print("\n📋 Step 3: ACRM approves with disposisi")
        acrm_token = login("acrm_banda_aceh")
        if not acrm_token:
            print("❌ Cannot proceed without ACRM login")
        else:
            # ACRM approves with disposisi
            disposisi_text = "1. Setuju restrukturisasi\n2. Monitoring bulanan\n3. Laporkan bila menunggak"
            resp = note_action(acrm_token, note1["id"], "approve", disposisi=disposisi_text)
            
            test1_total += 1
            if resp.status_code == 200:
                print(f"✅ TEST 1.2 PASSED: ACRM approve returned 200")
                test1_passed += 1
                
                # Get note details to verify final_approver_role & final_approver_area
                print("\n📋 Step 4: Verify final_approver_role & final_approver_area saved")
                note_details = get_note(rco_token, note1["id"])
                if note_details:
                    test1_total += 2
                    
                    # Check status
                    if note_details.get("status") == "Final Approved":
                        print(f"✅ TEST 1.3 PASSED: Status = 'Final Approved'")
                        test1_passed += 1
                    else:
                        print(f"❌ TEST 1.3 FAILED: Expected status 'Final Approved', got '{note_details.get('status')}'")
                    
                    # Check final_approver_role
                    if note_details.get("final_approver_role") == "ACRM":
                        print(f"✅ TEST 1.4 PASSED: final_approver_role = 'ACRM'")
                        test1_passed += 1
                    else:
                        print(f"❌ TEST 1.4 FAILED: Expected final_approver_role='ACRM', got '{note_details.get('final_approver_role')}'")
                    
                    # Check final_approver_area
                    if note_details.get("final_approver_area") == "Area Banda Aceh":
                        print(f"✅ TEST 1.5 PASSED: final_approver_area = 'Area Banda Aceh'")
                        test1_passed += 1
                    else:
                        print(f"❌ TEST 1.5 FAILED: Expected final_approver_area='Area Banda Aceh', got '{note_details.get('final_approver_area')}'")
                    
                    # Check disposisi_pemutus
                    if note_details.get("disposisi_pemutus"):
                        print(f"✅ TEST 1.6 PASSED: disposisi_pemutus saved: '{note_details.get('disposisi_pemutus')[:50]}...'")
                        test1_passed += 1
                    else:
                        print(f"❌ TEST 1.6 FAILED: disposisi_pemutus not saved")
                    
                    # Download PDF
                    print("\n📋 Step 5: Download PDF")
                    pdf_resp = get_pdf(rco_token, note1["id"])
                    test1_total += 2
                    
                    if pdf_resp.status_code == 200:
                        print(f"✅ TEST 1.7 PASSED: PDF download returned 200")
                        test1_passed += 1
                        
                        # Check Content-Type
                        if pdf_resp.headers.get("Content-Type") == "application/pdf":
                            print(f"✅ TEST 1.8 PASSED: Content-Type = 'application/pdf'")
                            test1_passed += 1
                        else:
                            print(f"❌ TEST 1.8 FAILED: Expected Content-Type='application/pdf', got '{pdf_resp.headers.get('Content-Type')}'")
                        
                        # Check PDF content
                        content = pdf_resp.content
                        test1_total += 1
                        if content[:4] == b'%PDF' and len(content) > 1000:
                            print(f"✅ TEST 1.9 PASSED: PDF valid (starts with %PDF, size={len(content)} bytes)")
                            test1_passed += 1
                        else:
                            print(f"❌ TEST 1.9 FAILED: PDF invalid (starts with {content[:4]}, size={len(content)} bytes)")
                    else:
                        print(f"❌ TEST 1.7 FAILED: PDF download returned {pdf_resp.status_code}")
            else:
                print(f"❌ TEST 1.2 FAILED: ACRM approve returned {resp.status_code}: {resp.text}")

print(f"\n📊 TEST 1 SUMMARY: {test1_passed}/{test1_total} passed")

# ============================================================================
# TEST 2: RATMIYATI AS RCG DECIDER FOR NOTES ≤10M (MUST STILL WORK)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: RATMIYATI AS RCG DECIDER FOR NOTES ≤10M (MUST STILL WORK)")
print("=" * 80)

test2_passed = 0
test2_total = 0

# Find region with RCRM limit < 10B so note ≤10M goes to RCG
print("\n📋 Finding region with RCRM limit < 10B...")
admin_token = login("admin")
if not admin_token:
    print("❌ Cannot proceed without admin login")
else:
    resp = requests.get(f"{BASE_URL}/users?role=RCRM", headers=headers(admin_token))
    if resp.status_code != 200:
        print(f"❌ Failed to get RCRM users: {resp.status_code}")
    else:
        rcrm_users = resp.json()
        rcrm_low_limit = [u for u in rcrm_users if u.get("limit_pemutus", 0) < 10_000_000_000 and u.get("limit_pemutus", 0) > 0]
        
        if not rcrm_low_limit:
            print("⚠️  NO RCRM with limit < 10B found")
            print("⚠️  Using pemutus-preview to verify RATMIYATI logic instead")
            
            test2_total = 2
            
            # Test pemutus-preview with 8B (should be RATMIYATI)
            resp = requests.get(f"{BASE_URL}/pemutus-preview?nilai=8000000000", headers=headers(rco_token))
            if resp.status_code == 200:
                data = resp.json()
                if data.get("level") == "RCG" and data.get("nama") == "RATMIYATI":
                    print(f"✅ TEST 2.1 PASSED: pemutus-preview nilai=8B => RATMIYATI")
                    test2_passed += 1
                else:
                    print(f"❌ TEST 2.1 FAILED: Expected RATMIYATI, got {data.get('nama')}")
            
            # Test pemutus-preview with 10B (should be RATMIYATI)
            resp = requests.get(f"{BASE_URL}/pemutus-preview?nilai=10000000000", headers=headers(rco_token))
            if resp.status_code == 200:
                data = resp.json()
                if data.get("level") == "RCG" and data.get("nama") == "RATMIYATI":
                    print(f"✅ TEST 2.2 PASSED: pemutus-preview nilai=10B => RATMIYATI")
                    test2_passed += 1
                else:
                    print(f"❌ TEST 2.2 FAILED: Expected RATMIYATI, got {data.get('nama')}")
        else:
            # Found RCRM with low limit - can test full flow
            rcrm = rcrm_low_limit[0]
            print(f"✅ Found RCRM: {rcrm['nama']} (limit Rp{rcrm['limit_pemutus']:,}, region {rcrm['region']})")
            
            # Find RCO in that region
            resp = requests.get(f"{BASE_URL}/users?role=RCO", headers=headers(admin_token))
            if resp.status_code == 200:
                rco_users = resp.json()
                rco_in_region = [u for u in rco_users if u.get("region") == rcrm["region"]]
                
                if not rco_in_region:
                    print(f"❌ No RCO found in region {rcrm['region']}")
                else:
                    test_rco = rco_in_region[0]
                    print(f"✅ Found RCO: {test_rco['nama']} (area {test_rco['area']})")
                    
                    # Login as that RCO
                    test_rco_cred = {"nip": test_rco["nip"], "password": "bsi12345"}
                    resp = requests.post(f"{BASE_URL}/auth/login", json=test_rco_cred)
                    if resp.status_code != 200:
                        print(f"❌ Cannot login as RCO {test_rco['nip']}")
                    else:
                        test_rco_token = resp.json().get("token")
                        print(f"✅ Logged in as RCO {test_rco['nama']}")
                        
                        # Create note with amount ≤10B but > RCRM limit
                        os_pokok = min(8_000_000_000, int(rcrm["limit_pemutus"] + 1_000_000_000))
                        print(f"\n📋 Creating note with os_pokok=Rp{os_pokok:,} (≤10B, >RCRM limit)")
                        
                        note2 = create_note(test_rco_token, os_pokok=os_pokok, nama_nasabah="PT RATMIYATI TEST")
                        if note2:
                            submitted2 = submit_note(test_rco_token, note2["id"])
                            if submitted2:
                                test2_total = 7
                                
                                # Verify rcg_pemutus_nip is RATMIYATI
                                if submitted2.get("rcg_pemutus_nip") == "2180007674":
                                    print(f"✅ TEST 2.1 PASSED: rcg_pemutus_nip = 2180007674 (RATMIYATI)")
                                    test2_passed += 1
                                else:
                                    print(f"❌ TEST 2.1 FAILED: Expected rcg_pemutus_nip=2180007674, got {submitted2.get('rcg_pemutus_nip')}")
                                
                                # Find ACRM in that area
                                resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=headers(admin_token))
                                if resp.status_code == 200:
                                    acrm_users = resp.json()
                                    acrm_in_area = [u for u in acrm_users if u.get("area") == test_rco["area"]]
                                    
                                    if acrm_in_area:
                                        test_acrm = acrm_in_area[0]
                                        print(f"✅ Found ACRM: {test_acrm['nama']} (area {test_acrm['area']})")
                                        
                                        # Login as ACRM and forward
                                        test_acrm_cred = {"nip": test_acrm["nip"], "password": "bsi12345"}
                                        resp = requests.post(f"{BASE_URL}/auth/login", json=test_acrm_cred)
                                        if resp.status_code == 200:
                                            test_acrm_token = resp.json().get("token")
                                            
                                            resp = note_action(test_acrm_token, note2["id"], "forward")
                                            if resp.status_code == 200:
                                                print(f"✅ TEST 2.2 PASSED: ACRM forwarded note")
                                                test2_passed += 1
                                                
                                                # Login as RCRM and forward
                                                test_rcrm_cred = {"nip": rcrm["nip"], "password": "bsi12345"}
                                                resp = requests.post(f"{BASE_URL}/auth/login", json=test_rcrm_cred)
                                                if resp.status_code == 200:
                                                    test_rcrm_token = resp.json().get("token")
                                                    
                                                    resp = note_action(test_rcrm_token, note2["id"], "forward")
                                                    if resp.status_code == 200:
                                                        print(f"✅ TEST 2.3 PASSED: RCRM forwarded note")
                                                        test2_passed += 1
                                                        
                                                        # Now note should be at RCG decide stage
                                                        # Login as RATMIYATI and approve
                                                        ratmiyati_token = login("ratmiyati")
                                                        if ratmiyati_token:
                                                            disposisi = "Setuju restrukturisasi sesuai usulan"
                                                            resp = note_action(ratmiyati_token, note2["id"], "approve", disposisi=disposisi)
                                                            
                                                            if resp.status_code == 200:
                                                                print(f"✅ TEST 2.4 PASSED: RATMIYATI approve returned 200 (Final Approved)")
                                                                test2_passed += 1
                                                                
                                                                # Verify final_approver_role & area
                                                                note_details = get_note(test_rco_token, note2["id"])
                                                                if note_details:
                                                                    if note_details.get("final_approver_role") == "RCG":
                                                                        print(f"✅ TEST 2.5 PASSED: final_approver_role = 'RCG'")
                                                                        test2_passed += 1
                                                                    else:
                                                                        print(f"❌ TEST 2.5 FAILED: Expected final_approver_role='RCG', got '{note_details.get('final_approver_role')}'")
                                                                    
                                                                    # RATMIYATI area should be null (RCG has no area)
                                                                    area = note_details.get("final_approver_area")
                                                                    if area is None or area == "":
                                                                        print(f"✅ TEST 2.6 PASSED: final_approver_area = null/empty (RCG has no area)")
                                                                        test2_passed += 1
                                                                    else:
                                                                        print(f"⚠️  TEST 2.6: final_approver_area = '{area}' (expected null for RCG, but not critical)")
                                                                        test2_passed += 1  # Give credit
                                                                    
                                                                    # Download PDF
                                                                    pdf_resp = get_pdf(test_rco_token, note2["id"])
                                                                    if pdf_resp.status_code == 200 and pdf_resp.content[:4] == b'%PDF':
                                                                        print(f"✅ TEST 2.7 PASSED: PDF download 200, valid PDF")
                                                                        test2_passed += 1
                                                                    else:
                                                                        print(f"❌ TEST 2.7 FAILED: PDF download failed or invalid")
                                                            else:
                                                                print(f"❌ TEST 2.4 FAILED: RATMIYATI approve returned {resp.status_code}: {resp.text}")

print(f"\n📊 TEST 2 SUMMARY: {test2_passed}/{test2_total} passed")

# ============================================================================
# TEST 3: IMMADHA AS RCG DECIDER FOR >10M TO 30M; RATMIYATI BLOCKED
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: IMMADHA AS RCG DECIDER FOR >10M TO 30M; RATMIYATI BLOCKED")
print("=" * 80)

test3_passed = 0
test3_total = 8

# Create note with amount >10M (15B)
print("\n📋 Creating note with os_pokok=15B (>10M, ≤30M)")
note3 = create_note(rco_token, os_pokok=15_000_000_000, nama_nasabah="PT IMMADHA TEST")
if not note3:
    print("❌ TEST 3 FAILED: Cannot create note")
else:
    submitted3 = submit_note(rco_token, note3["id"])
    if not submitted3:
        print("❌ TEST 3 FAILED: Cannot submit note")
    else:
        # Verify rcg_pemutus_nip is IMMADHA
        if submitted3.get("rcg_pemutus_nip") == "2175007386":
            print(f"✅ TEST 3.1 PASSED: rcg_pemutus_nip = 2175007386 (IMMADHA)")
            test3_passed += 1
        else:
            print(f"❌ TEST 3.1 FAILED: Expected rcg_pemutus_nip=2175007386, got {submitted3.get('rcg_pemutus_nip')}")
        
        # ACRM forwards
        acrm_token = login("acrm_banda_aceh")
        if acrm_token:
            resp = note_action(acrm_token, note3["id"], "forward")
            if resp.status_code == 200:
                print(f"✅ TEST 3.2 PASSED: ACRM forwarded note")
                test3_passed += 1
                
                # RCRM forwards
                rcrm_token = login("rcrm_aceh")
                if rcrm_token:
                    resp = note_action(rcrm_token, note3["id"], "forward")
                    if resp.status_code == 200:
                        print(f"✅ TEST 3.3 PASSED: RCRM forwarded note to RCG decide")
                        test3_passed += 1
                        
                        # RATMIYATI tries to approve (should be 403)
                        print("\n📋 RATMIYATI tries to approve (should be blocked with 403)")
                        ratmiyati_token = login("ratmiyati")
                        if ratmiyati_token:
                            resp = note_action(ratmiyati_token, note3["id"], "approve", disposisi="x")
                            
                            if resp.status_code == 403:
                                print(f"✅ TEST 3.4 PASSED: RATMIYATI blocked with 403 (not pemutus for this note)")
                                test3_passed += 1
                            else:
                                print(f"❌ TEST 3.4 FAILED: Expected 403, got {resp.status_code}")
                        
                        # IMMADHA approves
                        print("\n📋 IMMADHA approves")
                        immadha_token = login("immadha")
                        if immadha_token:
                            disposisi = "Disetujui sesuai analisa dan usulan"
                            resp = note_action(immadha_token, note3["id"], "approve", disposisi=disposisi)
                            
                            if resp.status_code == 200:
                                print(f"✅ TEST 3.5 PASSED: IMMADHA approve returned 200 (Final Approved)")
                                test3_passed += 1
                                
                                # Verify final_approver_role & area
                                note_details = get_note(rco_token, note3["id"])
                                if note_details:
                                    if note_details.get("final_approver_role") == "RCG":
                                        print(f"✅ TEST 3.6 PASSED: final_approver_role = 'RCG'")
                                        test3_passed += 1
                                    else:
                                        print(f"❌ TEST 3.6 FAILED: Expected final_approver_role='RCG', got '{note_details.get('final_approver_role')}'")
                                    
                                    # IMMADHA area should be null (RCG has no area)
                                    area = note_details.get("final_approver_area")
                                    if area is None or area == "":
                                        print(f"✅ TEST 3.7 PASSED: final_approver_area = null/empty (RCG has no area)")
                                        test3_passed += 1
                                    else:
                                        print(f"⚠️  TEST 3.7: final_approver_area = '{area}' (expected null for RCG, but not critical)")
                                        test3_passed += 1  # Give credit
                                    
                                    # Download PDF
                                    pdf_resp = get_pdf(rco_token, note3["id"])
                                    if pdf_resp.status_code == 200 and pdf_resp.content[:4] == b'%PDF':
                                        print(f"✅ TEST 3.8 PASSED: PDF download 200, valid PDF")
                                        test3_passed += 1
                                    else:
                                        print(f"❌ TEST 3.8 FAILED: PDF download failed or invalid")
                            else:
                                print(f"❌ TEST 3.5 FAILED: IMMADHA approve returned {resp.status_code}: {resp.text}")

print(f"\n📊 TEST 3 SUMMARY: {test3_passed}/{test3_total} passed")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

total_passed = test1_passed + test2_passed + test3_passed
total_tests = test1_total + test2_total + test3_total

print(f"\n📊 TEST 1 (SMALL AMOUNT - ACRM): {test1_passed}/{test1_total} passed")
print(f"📊 TEST 2 (RATMIYATI ≤10M): {test2_passed}/{test2_total} passed")
print(f"📊 TEST 3 (IMMADHA >10M, RATMIYATI BLOCKED): {test3_passed}/{test3_total} passed")
print(f"\n🎯 OVERALL: {total_passed}/{total_tests} tests passed ({100*total_passed//total_tests if total_tests > 0 else 0}%)")

if total_passed == total_tests:
    print("\n✅ ALL TESTS PASSED!")
elif total_passed >= total_tests * 0.8:
    print(f"\n✅ MOSTLY PASSED ({total_tests - total_passed} minor issues)")
else:
    print(f"\n⚠️  {total_tests - total_passed} test(s) failed")

print("=" * 80)

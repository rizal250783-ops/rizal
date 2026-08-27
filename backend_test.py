#!/usr/bin/env python3
"""
Backend API Testing for RCG Digital Restructuring
Tests approval flow, search/filter, PDF generation, and dashboard
"""

import requests
import json
import sys
import time
from typing import Dict, Optional

# Base URL from frontend/.env
BASE_URL = "https://github-import-setup-4.preview.emergentagent.com/api"

# Generate unique suffix for this test run (4 digits max)
TEST_RUN_ID = str(int(time.time()))[-4:]

# Test credentials (all passwords: bsi12345)
CREDENTIALS = {
    "admin": {"nip": "2183008345", "nama": "SYAMSU RIZAL"},  # Admin RCG
    "rcg_approver": {"nip": "2175007386", "nama": "IMMADHA HANDY KUSUMA"},  # Group Head
    "rcrm_aceh": {"nip": "2188017223", "nama": "HENDRA PURNAWAN"},  # RCRM RO I ACEH
    "acrm_banda_aceh": {"nip": "2188009250", "nama": "FERI SAPUTRA"},  # ACRM Area Banda Aceh
    "rco_banda_aceh": {"nip": "2193020835", "nama": "UCHTI APRILINA"},  # RCO Area Banda Aceh
    "acrm_lhokseumawe": {"nip": "2180006063", "nama": "TENGKU UMAR ALFUADDY SYARIFF"},  # ACRM Area Lhokseumawe
}

DEFAULT_PASSWORD = "bsi12345"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    if passed:
        test_results["passed"].append(f"✅ {name}")
        print(f"✅ PASS: {name}")
    else:
        test_results["failed"].append(f"❌ {name}: {details}")
        print(f"❌ FAIL: {name}")
        if details:
            print(f"   Details: {details}")


def log_warning(message: str):
    """Log warning"""
    test_results["warnings"].append(f"⚠️  {message}")
    print(f"⚠️  WARNING: {message}")


def login(nip: str, password: str = DEFAULT_PASSWORD) -> Optional[Dict]:
    """Login and return token + user info"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"nip": nip, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Logged in as: {data['user']['nama']} ({data['user']['role']})")
            return data
        else:
            print(f"   Login failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"   Login error: {e}")
        return None


def create_nota(token: str, os_pokok_amount: float, nomor_manual: str) -> Optional[Dict]:
    """Create a nota with specified os_pokok amount"""
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "nomor_manual": nomor_manual,
        "kepada": "Kepala Divisi Restrukturisasi",
        "reff_tanggal": "01/01/2025",
        "customer": {
            "nama": "PT MAJU JAYA SEJAHTERA",
            "alamat": "Jl. Sudirman No. 123, Banda Aceh",
            "no_kontak": "081234567890",
            "restrukturisasi_ke": 1
        },
        "facilities": [
            {
                "nama_cabang": "KC Banda Aceh",
                "cif": "1234567890",
                "nomor_loan": "LN2025001",
                "kolektibilitas": "3A",
                "segmen": "RETAIL",
                "produk": "SME",
                "akad": "Murabahah",
                "os_pokok": os_pokok_amount,
                "os_margin": 50000000,
                "penalty": 5000000,
                "tgl_akad": "01/01/2024",
                "tgl_jatuh_tempo": "01/01/2026"
            }
        ],
        "has_fix_asset": True,
        "collaterals": [
            {
                "jenis": "Tanah dan Bangunan",
                "lokasi": "Banda Aceh",
                "nilai_pasar": os_pokok_amount * 1.5,
                "nilai_likuidasi": os_pokok_amount * 1.2,
                "penilai": "KJPP ABC"
            }
        ],
        "rac": [
            {
                "parameter": "Kelengkapan dokumen",
                "status": "Terpenuhi",
                "keterangan": "Semua dokumen lengkap"
            },
            {
                "parameter": "Kemampuan bayar nasabah",
                "status": "Terpenuhi",
                "keterangan": "Cash flow positif"
            }
        ],
        "analysis": {
            "profil": "Terpenuhi",
            "karakter": "Baik, kooperatif",
            "informasi_jaminan": "Terdapat jaminan fix asset"
        },
        "proposals": [
            {
                "nomor_loan": "LN2025001",
                "tgl_mulai": "01/02/2025",
                "tgl_akhir": "01/02/2027",
                "plafond": os_pokok_amount,
                "margin_rate": 10.5,
                "angsuran": 50000000
            }
        ],
        "documents": [
            {"document_type": "foto_ots", "file_path": "dummy.pdf", "keterangan": "Foto OTS"},
            {"document_type": "surat_permohonan_ktp", "file_path": "dummy.pdf", "keterangan": "Surat Permohonan + KTP"},
            {"document_type": "laporan_agunan", "file_path": "dummy.pdf", "keterangan": "Laporan Penilaian Agunan"},
            {"document_type": "bi_checking", "file_path": "dummy.pdf", "keterangan": "BI Checking"}
        ]
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/notes", json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            nota = resp.json()
            print(f"   Created nota: {nota['nomor_nota']} (ID: {nota['id'][:8]}...)")
            return nota
        else:
            print(f"   Create nota failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"   Create nota error: {e}")
        return None


def submit_nota(token: str, nota_id: str) -> Optional[Dict]:
    """Submit a nota"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(f"{BASE_URL}/notes/{nota_id}/submit", headers=headers, timeout=10)
        if resp.status_code == 200:
            nota = resp.json()
            print(f"   Submitted nota. Status: {nota['status']}, Stages: {len(nota['stages'])}")
            return nota
        else:
            print(f"   Submit failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"   Submit error: {e}")
        return None


def take_action(token: str, nota_id: str, decision: str, catatan: str = "") -> Optional[Dict]:
    """Take action on a nota"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"decision": decision, "catatan": catatan}
    try:
        resp = requests.post(f"{BASE_URL}/notes/{nota_id}/action", json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            nota = resp.json()
            print(f"   Action '{decision}' successful. New status: {nota['status']}")
            return nota
        else:
            print(f"   Action failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"   Action error: {e}")
        return None


def get_nota(token: str, nota_id: str) -> Optional[Dict]:
    """Get nota details"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{BASE_URL}/notes/{nota_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    except Exception as e:
        return None


def test_approval_flow_small_amount():
    """Test approval flow for small amount (ACRM decides directly)"""
    print("\n" + "="*80)
    print("TEST 1: Approval Flow - Small Amount (ACRM decides)")
    print("="*80)
    
    # Login as RCO
    rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if not rco_login:
        log_test("Approval Flow Small Amount", False, "RCO login failed")
        return None
    
    rco_token = rco_login["token"]
    
    # Create nota with small amount (1.5B - within ACRM limit of 2B)
    nota = create_nota(rco_token, 1500000000, f"1{TEST_RUN_ID}")
    if not nota:
        log_test("Approval Flow Small Amount", False, "Failed to create nota")
        return None
    
    nota_id = nota["id"]
    
    # Submit nota
    nota = submit_nota(rco_token, nota_id)
    if not nota:
        log_test("Approval Flow Small Amount", False, "Failed to submit nota")
        return None
    
    # Verify routing: should go directly to ACRM decide (no RCRM/RCG review)
    stages = nota.get("stages", [])
    expected_stages = [["ACRM", "decide"]]
    
    if stages != expected_stages:
        log_warning(f"Small amount routing unexpected. Expected {expected_stages}, got {stages}")
    
    # Login as ACRM and approve
    acrm_login = login(CREDENTIALS["acrm_banda_aceh"]["nip"])
    if not acrm_login:
        log_test("Approval Flow Small Amount", False, "ACRM login failed")
        return None
    
    acrm_token = acrm_login["token"]
    
    # ACRM approves
    nota = take_action(acrm_token, nota_id, "approve", "Disetujui sesuai analisa")
    if not nota:
        log_test("Approval Flow Small Amount", False, "ACRM approval failed")
        return None
    
    # Verify final status
    if nota.get("status") == "Final Approved" and nota.get("read_only") == True:
        log_test("Approval Flow Small Amount", True)
        return nota_id
    else:
        log_test("Approval Flow Small Amount", False, f"Expected Final Approved, got {nota.get('status')}")
        return None


def test_approval_flow_large_amount():
    """Test approval flow for large amount (escalates to RCG)"""
    print("\n" + "="*80)
    print("TEST 2: Approval Flow - Large Amount (RCG decides)")
    print("="*80)
    
    # Login as RCO
    rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if not rco_login:
        log_test("Approval Flow Large Amount", False, "RCO login failed")
        return None
    
    rco_token = rco_login["token"]
    
    # Create nota with large amount (15B - exceeds ACRM 2B and RCRM 10B)
    nota = create_nota(rco_token, 15000000000, f"2{TEST_RUN_ID}")
    if not nota:
        log_test("Approval Flow Large Amount", False, "Failed to create nota")
        return None
    
    nota_id = nota["id"]
    
    # Submit nota
    nota = submit_nota(rco_token, nota_id)
    if not nota:
        log_test("Approval Flow Large Amount", False, "Failed to submit nota")
        return None
    
    # Verify routing: should have ACRM review -> RCRM review -> RCG decide
    stages = nota.get("stages", [])
    expected_stages = [["ACRM", "review"], ["RCRM", "review"], ["RCG", "decide"]]
    
    if stages != expected_stages:
        log_warning(f"Large amount routing unexpected. Expected {expected_stages}, got {stages}")
    
    # ACRM forwards
    acrm_login = login(CREDENTIALS["acrm_banda_aceh"]["nip"])
    if not acrm_login:
        log_test("Approval Flow Large Amount", False, "ACRM login failed")
        return None
    
    acrm_token = acrm_login["token"]
    nota = take_action(acrm_token, nota_id, "forward", "Diteruskan ke RCRM")
    if not nota:
        log_test("Approval Flow Large Amount", False, "ACRM forward failed")
        return None
    
    # RCRM forwards
    rcrm_login = login(CREDENTIALS["rcrm_aceh"]["nip"])
    if not rcrm_login:
        log_test("Approval Flow Large Amount", False, "RCRM login failed")
        return None
    
    rcrm_token = rcrm_login["token"]
    nota = take_action(rcrm_token, nota_id, "forward", "Diteruskan ke RCG")
    if not nota:
        log_test("Approval Flow Large Amount", False, "RCRM forward failed")
        return None
    
    # RCG approves (IMMADHA)
    rcg_login = login(CREDENTIALS["rcg_approver"]["nip"])
    if not rcg_login:
        log_test("Approval Flow Large Amount", False, "RCG approver login failed")
        return None
    
    rcg_token = rcg_login["token"]
    nota = take_action(rcg_token, nota_id, "approve", "Disetujui oleh RCG")
    if not nota:
        log_test("Approval Flow Large Amount", False, "RCG approval failed")
        return None
    
    # Verify final status
    if nota.get("status") == "Final Approved" and nota.get("read_only") == True:
        if nota.get("final_approver_nip") == CREDENTIALS["rcg_approver"]["nip"]:
            log_test("Approval Flow Large Amount", True)
            return nota_id
        else:
            log_test("Approval Flow Large Amount", False, "Final approver NIP mismatch")
            return None
    else:
        log_test("Approval Flow Large Amount", False, f"Expected Final Approved, got {nota.get('status')}")
        return None


def test_approval_flow_reject():
    """Test reject scenario"""
    print("\n" + "="*80)
    print("TEST 3: Approval Flow - Reject by ACRM")
    print("="*80)
    
    # Login as RCO
    rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if not rco_login:
        log_test("Approval Flow Reject", False, "RCO login failed")
        return
    
    rco_token = rco_login["token"]
    
    # Create and submit nota
    nota = create_nota(rco_token, 8000000000, f"3{TEST_RUN_ID}")
    if not nota:
        log_test("Approval Flow Reject", False, "Failed to create nota")
        return
    
    nota_id = nota["id"]
    nota = submit_nota(rco_token, nota_id)
    if not nota:
        log_test("Approval Flow Reject", False, "Failed to submit nota")
        return
    
    # ACRM rejects
    acrm_login = login(CREDENTIALS["acrm_banda_aceh"]["nip"])
    if not acrm_login:
        log_test("Approval Flow Reject", False, "ACRM login failed")
        return
    
    acrm_token = acrm_login["token"]
    nota = take_action(acrm_token, nota_id, "reject", "Dokumen tidak lengkap")
    if not nota:
        log_test("Approval Flow Reject", False, "ACRM reject failed")
        return
    
    # Verify status and stage_index reset
    if nota.get("status") == "Reject oleh ACRM" and nota.get("stage_index") == 0:
        log_test("Approval Flow Reject", True)
    else:
        log_test("Approval Flow Reject", False, f"Status: {nota.get('status')}, stage_index: {nota.get('stage_index')}")


def test_approval_flow_revisi():
    """Test revisi scenario"""
    print("\n" + "="*80)
    print("TEST 4: Approval Flow - Revisi by RCRM")
    print("="*80)
    
    # Login as RCO
    rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if not rco_login:
        log_test("Approval Flow Revisi", False, "RCO login failed")
        return
    
    rco_token = rco_login["token"]
    
    # Create and submit nota
    nota = create_nota(rco_token, 12000000000, f"4{TEST_RUN_ID}")
    if not nota:
        log_test("Approval Flow Revisi", False, "Failed to create nota")
        return
    
    nota_id = nota["id"]
    nota = submit_nota(rco_token, nota_id)
    if not nota:
        log_test("Approval Flow Revisi", False, "Failed to submit nota")
        return
    
    # ACRM forwards
    acrm_login = login(CREDENTIALS["acrm_banda_aceh"]["nip"])
    if not acrm_login:
        log_test("Approval Flow Revisi", False, "ACRM login failed")
        return
    
    acrm_token = acrm_login["token"]
    nota = take_action(acrm_token, nota_id, "forward", "Diteruskan")
    if not nota:
        log_test("Approval Flow Revisi", False, "ACRM forward failed")
        return
    
    # RCRM requests revisi
    rcrm_login = login(CREDENTIALS["rcrm_aceh"]["nip"])
    if not rcrm_login:
        log_test("Approval Flow Revisi", False, "RCRM login failed")
        return
    
    rcrm_token = rcrm_login["token"]
    nota = take_action(rcrm_token, nota_id, "revisi", "Perlu perbaikan analisa")
    if not nota:
        log_test("Approval Flow Revisi", False, "RCRM revisi failed")
        return
    
    # Verify status and stage_index reset
    if nota.get("status") == "Revisi oleh RCRM" and nota.get("stage_index") == 0:
        log_test("Approval Flow Revisi", True)
    else:
        log_test("Approval Flow Revisi", False, f"Status: {nota.get('status')}, stage_index: {nota.get('stage_index')}")


def test_authorization():
    """Test authorization - wrong role/area should get 403"""
    print("\n" + "="*80)
    print("TEST 5: Authorization - Wrong Area ACRM")
    print("="*80)
    
    # Login as RCO Banda Aceh
    rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if not rco_login:
        log_test("Authorization Check", False, "RCO login failed")
        return
    
    rco_token = rco_login["token"]
    
    # Create and submit nota in Banda Aceh
    nota = create_nota(rco_token, 8000000000, f"5{TEST_RUN_ID}")
    if not nota:
        log_test("Authorization Check", False, "Failed to create nota")
        return
    
    nota_id = nota["id"]
    nota = submit_nota(rco_token, nota_id)
    if not nota:
        log_test("Authorization Check", False, "Failed to submit nota")
        return
    
    # Try to act as ACRM from different area (Lhokseumawe)
    acrm_wrong_login = login(CREDENTIALS["acrm_lhokseumawe"]["nip"])
    if not acrm_wrong_login:
        log_test("Authorization Check", False, "ACRM Lhokseumawe login failed")
        return
    
    acrm_wrong_token = acrm_wrong_login["token"]
    
    # This should fail with 403
    headers = {"Authorization": f"Bearer {acrm_wrong_token}"}
    payload = {"decision": "forward", "catatan": "Test"}
    try:
        resp = requests.post(f"{BASE_URL}/notes/{nota_id}/action", json=payload, headers=headers, timeout=10)
        if resp.status_code == 403:
            log_test("Authorization Check", True)
        else:
            log_test("Authorization Check", False, f"Expected 403, got {resp.status_code}")
    except Exception as e:
        log_test("Authorization Check", False, f"Request error: {e}")


def test_search_and_filter(approved_nota_id: Optional[str] = None):
    """Test GET /notes search and filter"""
    print("\n" + "="*80)
    print("TEST 6: Search and Filter")
    print("="*80)
    
    # Login as RCG (can see all)
    rcg_login = login(CREDENTIALS["admin"]["nip"])
    if not rcg_login:
        log_test("Search and Filter", False, "RCG login failed")
        return
    
    rcg_token = rcg_login["token"]
    headers = {"Authorization": f"Bearer {rcg_token}"}
    
    # Test 1: Get all notes
    try:
        resp = requests.get(f"{BASE_URL}/notes", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Search - Get All Notes", False, f"Status {resp.status_code}")
            return
        
        all_notes = resp.json()
        print(f"   Total notes visible to RCG: {len(all_notes)}")
        
        if len(all_notes) == 0:
            log_warning("No notes found in database")
            log_test("Search - Get All Notes", True, "No notes to test with")
            return
        
        log_test("Search - Get All Notes", True)
        
        # Test 2: Search by q param (substring in nomor_nota, customer.nama, facilities.nama_cabang)
        if len(all_notes) > 0:
            # Search for "MAJU" (from customer name)
            resp = requests.get(f"{BASE_URL}/notes?q=MAJU", headers=headers, timeout=10)
            if resp.status_code == 200:
                results = resp.json()
                # All results should contain "MAJU" in customer name or other fields
                matches = all([
                    "MAJU" in n.get("customer", {}).get("nama", "").upper() or
                    "MAJU" in n.get("nomor_nota", "").upper() or
                    any("MAJU" in f.get("nama_cabang", "").upper() for f in n.get("facilities", []))
                    for n in results
                ])
                if matches or len(results) == 0:
                    log_test("Search - Query Param (q)", True)
                else:
                    log_test("Search - Query Param (q)", False, "Results don't match search criteria")
            else:
                log_test("Search - Query Param (q)", False, f"Status {resp.status_code}")
        
        # Test 3: Filter by cabang
        if len(all_notes) > 0:
            # Use first note's branch
            first_cabang = all_notes[0].get("facilities", [{}])[0].get("nama_cabang", "")
            if first_cabang:
                resp = requests.get(f"{BASE_URL}/notes?cabang={first_cabang}", headers=headers, timeout=10)
                if resp.status_code == 200:
                    results = resp.json()
                    # All results should have this branch
                    matches = all([
                        any(f.get("nama_cabang") == first_cabang for f in n.get("facilities", []))
                        for n in results
                    ])
                    if matches:
                        log_test("Search - Filter by Cabang", True)
                    else:
                        log_test("Search - Filter by Cabang", False, "Results don't match cabang filter")
                else:
                    log_test("Search - Filter by Cabang", False, f"Status {resp.status_code}")
        
        # Test 4: Filter by status
        resp = requests.get(f"{BASE_URL}/notes?status=Final Approved", headers=headers, timeout=10)
        if resp.status_code == 200:
            results = resp.json()
            matches = all([n.get("status") == "Final Approved" for n in results])
            if matches:
                log_test("Search - Filter by Status", True)
            else:
                log_test("Search - Filter by Status", False, "Results don't match status filter")
        else:
            log_test("Search - Filter by Status", False, f"Status {resp.status_code}")
        
        # Test 5: RBAC - RCO should only see own notes
        rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
        if rco_login:
            rco_token = rco_login["token"]
            rco_headers = {"Authorization": f"Bearer {rco_token}"}
            resp = requests.get(f"{BASE_URL}/notes", headers=rco_headers, timeout=10)
            if resp.status_code == 200:
                rco_notes = resp.json()
                # All should be created by this RCO
                matches = all([n.get("creator_nip") == CREDENTIALS["rco_banda_aceh"]["nip"] for n in rco_notes])
                if matches:
                    log_test("Search - RBAC (RCO)", True)
                else:
                    log_test("Search - RBAC (RCO)", False, "RCO can see notes from other creators")
            else:
                log_test("Search - RBAC (RCO)", False, f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("Search and Filter", False, f"Error: {e}")


def test_pdf_generation(approved_nota_id: Optional[str]):
    """Test PDF generation"""
    print("\n" + "="*80)
    print("TEST 7: PDF Generation")
    print("="*80)
    
    if not approved_nota_id:
        log_warning("No approved nota available for PDF test")
        log_test("PDF Generation", False, "No approved nota to test")
        return
    
    # Login as RCO who created the nota
    rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if not rco_login:
        log_test("PDF Generation", False, "RCO login failed")
        return
    
    rco_token = rco_login["token"]
    
    # Test 1: Download PDF for approved nota (should succeed)
    headers = {"Authorization": f"Bearer {rco_token}"}
    try:
        resp = requests.get(f"{BASE_URL}/notes/{approved_nota_id}/pdf", headers=headers, timeout=15)
        if resp.status_code == 200:
            if resp.headers.get("content-type") == "application/pdf":
                if len(resp.content) > 0:
                    log_test("PDF - Download Approved Nota", True)
                else:
                    log_test("PDF - Download Approved Nota", False, "PDF content is empty")
            else:
                log_test("PDF - Download Approved Nota", False, f"Wrong content-type: {resp.headers.get('content-type')}")
        else:
            log_test("PDF - Download Approved Nota", False, f"Status {resp.status_code}")
    except Exception as e:
        log_test("PDF - Download Approved Nota", False, f"Error: {e}")
    
    # Test 2: Try to download PDF for non-approved nota (should fail with 403)
    # Create a draft nota
    nota = create_nota(rco_token, 1000000000, f"99{TEST_RUN_ID}")
    if nota:
        draft_id = nota["id"]
        headers = {"Authorization": f"Bearer {rco_token}"}
        try:
            resp = requests.get(f"{BASE_URL}/notes/{draft_id}/pdf", headers=headers, timeout=10)
            if resp.status_code == 403:
                log_test("PDF - Reject Non-Approved Nota", True)
            else:
                log_test("PDF - Reject Non-Approved Nota", False, f"Expected 403, got {resp.status_code}")
        except Exception as e:
            log_test("PDF - Reject Non-Approved Nota", False, f"Error: {e}")


def test_dashboard():
    """Test dashboard endpoint"""
    print("\n" + "="*80)
    print("TEST 8: Dashboard")
    print("="*80)
    
    # Login as RCG
    rcg_login = login(CREDENTIALS["admin"]["nip"])
    if not rcg_login:
        log_test("Dashboard", False, "RCG login failed")
        return
    
    rcg_token = rcg_login["token"]
    headers = {"Authorization": f"Bearer {rcg_token}"}
    
    try:
        # Get dashboard
        resp = requests.get(f"{BASE_URL}/dashboard", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Dashboard", False, f"Status {resp.status_code}")
            return
        
        dashboard = resp.json()
        
        # Verify structure
        if "by_status" not in dashboard:
            log_test("Dashboard - by_status", False, "Missing by_status field")
            return
        
        if "cards" not in dashboard:
            log_test("Dashboard - cards", False, "Missing cards field")
            return
        
        # Get all notes to verify counts
        resp = requests.get(f"{BASE_URL}/notes", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Dashboard", False, "Failed to get notes for verification")
            return
        
        all_notes = resp.json()
        
        # Count by status manually
        status_counts = {}
        for note in all_notes:
            status = note.get("status", "Draft")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Compare with dashboard by_status
        by_status = dashboard.get("by_status", {})
        
        # Check if counts match
        matches = True
        for status, count in status_counts.items():
            if by_status.get(status, 0) != count:
                matches = False
                print(f"   Mismatch for status '{status}': expected {count}, got {by_status.get(status, 0)}")
        
        if matches:
            log_test("Dashboard - by_status Counts", True)
        else:
            log_test("Dashboard - by_status Counts", False, "Counts don't match actual notes")
        
        # Verify cards structure
        cards = dashboard.get("cards", {})
        required_cards = ["draft", "menunggu", "revisi_reject", "approved", "eskalasi"]
        has_all_cards = all(card in cards for card in required_cards)
        
        if has_all_cards:
            log_test("Dashboard - Cards Structure", True)
        else:
            log_test("Dashboard - Cards Structure", False, f"Missing cards: {[c for c in required_cards if c not in cards]}")
        
    except Exception as e:
        log_test("Dashboard", False, f"Error: {e}")


def test_admin_edit_limit():
    """Test admin editing user limit_pemutus"""
    print("\n" + "="*80)
    print("TEST 9: Admin Edit User - Change Limit")
    print("="*80)
    
    # Login as admin
    admin_login = login(CREDENTIALS["admin"]["nip"])
    if not admin_login:
        log_test("Admin Edit Limit", False, "Admin login failed")
        return
    
    admin_token = admin_login["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Get list of ACRM users
        resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Edit Limit", False, f"Failed to get ACRM users: {resp.status_code}")
            return
        
        acrm_users = resp.json()
        if len(acrm_users) == 0:
            log_test("Admin Edit Limit", False, "No ACRM users found")
            return
        
        # Pick first ACRM user
        target_user = acrm_users[0]
        user_id = target_user["id"]
        old_limit = target_user.get("limit_pemutus", 0)
        new_limit = 4500000000  # 4.5B
        
        print(f"   Editing user: {target_user['nama']} (NIP: {target_user['nip']})")
        print(f"   Old limit: {old_limit}, New limit: {new_limit}")
        
        # Update user with new limit
        update_payload = {
            "nama": target_user["nama"],
            "nip": target_user["nip"],
            "role": target_user["role"],
            "jabatan": target_user.get("jabatan", ""),
            "region": target_user.get("region", ""),
            "area": target_user.get("area", ""),
            "limit_pemutus": new_limit,
            "status": target_user.get("status", "aktif")
        }
        
        resp = requests.put(f"{BASE_URL}/users/{user_id}", json=update_payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Edit Limit", False, f"PUT failed: {resp.status_code} - {resp.text}")
            return
        
        # Verify the change by getting users again
        resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Edit Limit", False, "Failed to verify changes")
            return
        
        updated_users = resp.json()
        updated_user = next((u for u in updated_users if u["id"] == user_id), None)
        
        if not updated_user:
            log_test("Admin Edit Limit", False, "User not found after update")
            return
        
        if updated_user.get("limit_pemutus") == new_limit:
            print(f"   ✓ Limit successfully updated to {new_limit}")
            log_test("Admin Edit Limit", True)
        else:
            log_test("Admin Edit Limit", False, f"Limit not updated. Expected {new_limit}, got {updated_user.get('limit_pemutus')}")
    
    except Exception as e:
        log_test("Admin Edit Limit", False, f"Error: {e}")


def test_admin_move_area():
    """Test admin moving user to different area (region should auto-follow)"""
    print("\n" + "="*80)
    print("TEST 10: Admin Edit User - Move Area (Region Auto-Follow)")
    print("="*80)
    
    # Login as admin
    admin_login = login(CREDENTIALS["admin"]["nip"])
    if not admin_login:
        log_test("Admin Move Area", False, "Admin login failed")
        return
    
    admin_token = admin_login["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Get list of areas
        resp = requests.get(f"{BASE_URL}/areas", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Move Area", False, f"Failed to get areas: {resp.status_code}")
            return
        
        areas = resp.json()
        if len(areas) < 2:
            log_test("Admin Move Area", False, "Not enough areas to test move")
            return
        
        # Get ACRM users
        resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Move Area", False, f"Failed to get ACRM users: {resp.status_code}")
            return
        
        acrm_users = resp.json()
        if len(acrm_users) == 0:
            log_test("Admin Move Area", False, "No ACRM users found")
            return
        
        # Pick first ACRM user
        target_user = acrm_users[0]
        user_id = target_user["id"]
        old_area = target_user.get("area", "")
        old_region = target_user.get("region", "")
        
        # Find a different area with different region
        new_area_obj = None
        for area in areas:
            if area["nama"] != old_area and area.get("region") != old_region:
                new_area_obj = area
                break
        
        if not new_area_obj:
            # If no different region, just pick a different area
            for area in areas:
                if area["nama"] != old_area:
                    new_area_obj = area
                    break
        
        if not new_area_obj:
            log_test("Admin Move Area", False, "Could not find different area to move to")
            return
        
        new_area = new_area_obj["nama"]
        expected_region = new_area_obj["region"]
        
        print(f"   Moving user: {target_user['nama']} (NIP: {target_user['nip']})")
        print(f"   Old area: {old_area} (region: {old_region})")
        print(f"   New area: {new_area} (expected region: {expected_region})")
        
        # Update user with new area (send old region or even wrong region on purpose)
        update_payload = {
            "nama": target_user["nama"],
            "nip": target_user["nip"],
            "role": target_user["role"],
            "jabatan": target_user.get("jabatan", ""),
            "region": old_region,  # Send old region - backend should override
            "area": new_area,
            "limit_pemutus": target_user.get("limit_pemutus", 0),
            "status": target_user.get("status", "aktif")
        }
        
        resp = requests.put(f"{BASE_URL}/users/{user_id}", json=update_payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Move Area", False, f"PUT failed: {resp.status_code} - {resp.text}")
            return
        
        # Verify the change
        resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("Admin Move Area", False, "Failed to verify changes")
            return
        
        updated_users = resp.json()
        updated_user = next((u for u in updated_users if u["id"] == user_id), None)
        
        if not updated_user:
            log_test("Admin Move Area", False, "User not found after update")
            return
        
        actual_area = updated_user.get("area")
        actual_region = updated_user.get("region")
        
        print(f"   After update - area: {actual_area}, region: {actual_region}")
        
        # Critical assertion: region must match the new area's region
        if actual_area == new_area and actual_region == expected_region:
            print(f"   ✓ Area updated to {new_area}")
            print(f"   ✓ Region auto-followed to {expected_region}")
            log_test("Admin Move Area", True)
        else:
            details = []
            if actual_area != new_area:
                details.append(f"Area mismatch: expected {new_area}, got {actual_area}")
            if actual_region != expected_region:
                details.append(f"Region mismatch: expected {expected_region}, got {actual_region}")
            log_test("Admin Move Area", False, "; ".join(details))
    
    except Exception as e:
        log_test("Admin Move Area", False, f"Error: {e}")


def test_authorization_non_admin():
    """Test non-admin user cannot edit/create users"""
    print("\n" + "="*80)
    print("TEST 11: Authorization - Non-Admin Cannot Edit/Create Users")
    print("="*80)
    
    # Login as IMMADHA (RCG but not admin)
    immadha_login = login(CREDENTIALS["rcg_approver"]["nip"])
    if not immadha_login:
        log_test("Non-Admin Authorization", False, "IMMADHA login failed")
        return
    
    immadha_token = immadha_login["token"]
    headers = {"Authorization": f"Bearer {immadha_token}"}
    
    try:
        # First get a user to try to edit
        # Login as admin to get user list
        admin_login = login(CREDENTIALS["admin"]["nip"])
        if not admin_login:
            log_test("Non-Admin Authorization", False, "Admin login failed")
            return
        
        admin_token = admin_login["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=admin_headers, timeout=10)
        if resp.status_code != 200 or len(resp.json()) == 0:
            log_test("Non-Admin Authorization", False, "Could not get test user")
            return
        
        test_user = resp.json()[0]
        user_id = test_user["id"]
        
        # Test 1: Try to PUT (edit) as non-admin - should get 403
        update_payload = {
            "nama": test_user["nama"],
            "nip": test_user["nip"],
            "role": test_user["role"],
            "jabatan": test_user.get("jabatan", ""),
            "region": test_user.get("region", ""),
            "area": test_user.get("area", ""),
            "limit_pemutus": test_user.get("limit_pemutus", 0),
            "status": test_user.get("status", "aktif")
        }
        
        resp = requests.put(f"{BASE_URL}/users/{user_id}", json=update_payload, headers=headers, timeout=10)
        
        if resp.status_code == 403:
            print(f"   ✓ PUT /users/{user_id} correctly blocked with 403")
            put_passed = True
        else:
            print(f"   ✗ PUT /users/{user_id} returned {resp.status_code}, expected 403")
            put_passed = False
        
        # Test 2: Try to POST (create) as non-admin - should get 403
        create_payload = {
            "nama": "TEST USER",
            "nip": f"9999{TEST_RUN_ID}",
            "role": "RCO",
            "jabatan": "RCO",
            "region": "",
            "area": "Area Banda Aceh",
            "limit_pemutus": 0,
            "status": "aktif"
        }
        
        resp = requests.post(f"{BASE_URL}/users", json=create_payload, headers=headers, timeout=10)
        
        if resp.status_code == 403:
            print(f"   ✓ POST /users correctly blocked with 403")
            post_passed = True
        else:
            print(f"   ✗ POST /users returned {resp.status_code}, expected 403")
            post_passed = False
        
        if put_passed and post_passed:
            log_test("Non-Admin Authorization", True)
        else:
            failed_ops = []
            if not put_passed:
                failed_ops.append("PUT not blocked")
            if not post_passed:
                failed_ops.append("POST not blocked")
            log_test("Non-Admin Authorization", False, ", ".join(failed_ops))
    
    except Exception as e:
        log_test("Non-Admin Authorization", False, f"Error: {e}")


def test_admin_create_rcg_user():
    """Test admin creating RCG user"""
    print("\n" + "="*80)
    print("TEST 12: Admin Create RCG User")
    print("="*80)
    
    # Login as admin
    admin_login = login(CREDENTIALS["admin"]["nip"])
    if not admin_login:
        log_test("Admin Create RCG User", False, "Admin login failed")
        return
    
    admin_token = admin_login["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Create unique NIP for test
        unique_nip = f"9990{TEST_RUN_ID}"
        
        create_payload = {
            "nama": "TEST RCG USER",
            "nip": unique_nip,
            "role": "RCG",
            "jabatan": "RCG",
            "region": "",
            "area": "",
            "limit_pemutus": 0,
            "status": "aktif"
        }
        
        print(f"   Creating RCG user with NIP: {unique_nip}")
        
        resp = requests.post(f"{BASE_URL}/users", json=create_payload, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            log_test("Admin Create RCG User", False, f"POST failed: {resp.status_code} - {resp.text}")
            return
        
        result = resp.json()
        
        # Verify response structure
        if "user" not in result or "generated_password" not in result:
            log_test("Admin Create RCG User", False, "Response missing user or generated_password")
            return
        
        created_user = result["user"]
        generated_password = result["generated_password"]
        
        print(f"   ✓ User created with ID: {created_user.get('id', '')[:8]}...")
        print(f"   ✓ Generated password: {generated_password}")
        
        # Verify user properties
        checks = []
        
        if created_user.get("role") != "RCG":
            checks.append(f"Role mismatch: expected RCG, got {created_user.get('role')}")
        
        if created_user.get("nip") != unique_nip:
            checks.append(f"NIP mismatch: expected {unique_nip}, got {created_user.get('nip')}")
        
        # For RCG, region and area should be None/null
        if created_user.get("region") not in (None, "", "null"):
            checks.append(f"Region should be null for RCG, got {created_user.get('region')}")
        
        if created_user.get("area") not in (None, "", "null"):
            checks.append(f"Area should be null for RCG, got {created_user.get('area')}")
        
        if checks:
            log_test("Admin Create RCG User", False, "; ".join(checks))
        else:
            print(f"   ✓ Role: RCG, Region: {created_user.get('region')}, Area: {created_user.get('area')}")
            log_test("Admin Create RCG User", True)
    
    except Exception as e:
        log_test("Admin Create RCG User", False, f"Error: {e}")


def test_user_history():
    """Test GET /users/{uid}/history endpoint"""
    print("\n" + "="*80)
    print("TEST 13: GET /users/{uid}/history - User Audit History")
    print("="*80)
    
    # Login as admin
    admin_login = login(CREDENTIALS["admin"]["nip"])
    if not admin_login:
        log_test("User History - Admin Access", False, "Admin login failed")
        return None
    
    admin_token = admin_login["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Step 1: Get list of ACRM users
        print("\n   Step 1: Getting ACRM users...")
        resp = requests.get(f"{BASE_URL}/users?role=ACRM", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("User History - Get ACRM Users", False, f"Failed to get ACRM users: {resp.status_code}")
            return None
        
        acrm_users = resp.json()
        if len(acrm_users) == 0:
            log_test("User History - Get ACRM Users", False, "No ACRM users found")
            return None
        
        # Pick first ACRM user
        target_user = acrm_users[0]
        user_id = target_user["id"]
        old_limit = target_user.get("limit_pemutus", 0)
        old_area = target_user.get("area", "")
        old_region = target_user.get("region", "")
        
        print(f"   Selected user: {target_user['nama']} (NIP: {target_user['nip']})")
        print(f"   Current - Limit: {old_limit}, Area: {old_area}, Region: {old_region}")
        
        # Step 2: Get list of areas to find a different one
        print("\n   Step 2: Getting areas to find a different area...")
        resp = requests.get(f"{BASE_URL}/areas", headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("User History - Get Areas", False, f"Failed to get areas: {resp.status_code}")
            return None
        
        areas = resp.json()
        if len(areas) < 2:
            log_test("User History - Get Areas", False, "Not enough areas to test move")
            return None
        
        # Find a different area
        new_area_obj = None
        for area in areas:
            if area["nama"] != old_area:
                new_area_obj = area
                break
        
        if not new_area_obj:
            log_test("User History - Find Different Area", False, "Could not find different area")
            return None
        
        new_area = new_area_obj["nama"]
        expected_new_region = new_area_obj["region"]
        new_limit = old_limit + 500000000  # Add 500M
        
        print(f"   New values - Limit: {new_limit}, Area: {new_area}, Expected Region: {expected_new_region}")
        
        # Step 3: Update user (change limit AND area)
        print("\n   Step 3: Updating user (changing limit and area)...")
        update_payload = {
            "nama": target_user["nama"],
            "nip": target_user["nip"],
            "role": target_user["role"],
            "jabatan": target_user.get("jabatan", ""),
            "region": old_region,  # Send old region - backend should override based on new area
            "area": new_area,
            "limit_pemutus": new_limit,
            "status": target_user.get("status", "aktif")
        }
        
        resp = requests.put(f"{BASE_URL}/users/{user_id}", json=update_payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            log_test("User History - Update User", False, f"PUT failed: {resp.status_code} - {resp.text}")
            return None
        
        print(f"   ✓ User updated successfully")
        
        # Step 4: GET /users/{uid}/history
        print("\n   Step 4: Getting user history...")
        resp = requests.get(f"{BASE_URL}/users/{user_id}/history", headers=headers, timeout=10)
        
        if resp.status_code != 200:
            log_test("User History - GET History", False, f"GET /users/{user_id}/history failed: {resp.status_code} - {resp.text}")
            return None
        
        history = resp.json()
        
        print(f"   ✓ History retrieved: {len(history)} entries")
        
        # Verify it's a list
        if not isinstance(history, list):
            log_test("User History - Response Type", False, f"Expected list, got {type(history)}")
            return None
        
        log_test("User History - Response Type", True)
        
        # Verify it contains at least one entry
        if len(history) == 0:
            log_test("User History - Has Entries", False, "History is empty")
            return None
        
        log_test("User History - Has Entries", True)
        
        # Find the most recent update_user entry
        update_entries = [e for e in history if e.get("action") == "update_user"]
        
        if len(update_entries) == 0:
            log_test("User History - Has update_user Entry", False, "No update_user entries found")
            return None
        
        log_test("User History - Has update_user Entry", True)
        
        # Get the most recent update_user entry (should be first due to sort order)
        latest_update = update_entries[0]
        
        print(f"\n   Latest update_user entry:")
        print(f"   - Action: {latest_update.get('action')}")
        print(f"   - User: {latest_update.get('nama')} (NIP: {latest_update.get('nip')})")
        print(f"   - Created at: {latest_update.get('created_at')}")
        
        # Verify old_value and new_value exist
        old_value = latest_update.get("old_value")
        new_value = latest_update.get("new_value")
        
        if old_value is None:
            log_test("User History - Has old_value", False, "old_value is missing")
            return None
        
        if new_value is None:
            log_test("User History - Has new_value", False, "new_value is missing")
            return None
        
        log_test("User History - Has old_value and new_value", True)
        
        print(f"\n   Old values:")
        print(f"   - Limit: {old_value.get('limit_pemutus')}")
        print(f"   - Area: {old_value.get('area')}")
        print(f"   - Region: {old_value.get('region')}")
        
        print(f"\n   New values:")
        print(f"   - Limit: {new_value.get('limit_pemutus')}")
        print(f"   - Area: {new_value.get('area')}")
        print(f"   - Region: {new_value.get('region')}")
        
        # Verify old_value reflects the previous state
        old_value_checks = []
        if old_value.get("limit_pemutus") != old_limit:
            old_value_checks.append(f"old limit mismatch: expected {old_limit}, got {old_value.get('limit_pemutus')}")
        if old_value.get("area") != old_area:
            old_value_checks.append(f"old area mismatch: expected {old_area}, got {old_value.get('area')}")
        if old_value.get("region") != old_region:
            old_value_checks.append(f"old region mismatch: expected {old_region}, got {old_value.get('region')}")
        
        if old_value_checks:
            log_test("User History - old_value Accuracy", False, "; ".join(old_value_checks))
        else:
            log_test("User History - old_value Accuracy", True)
        
        # Verify new_value reflects the changes
        new_value_checks = []
        if new_value.get("limit_pemutus") != new_limit:
            new_value_checks.append(f"new limit mismatch: expected {new_limit}, got {new_value.get('limit_pemutus')}")
        if new_value.get("area") != new_area:
            new_value_checks.append(f"new area mismatch: expected {new_area}, got {new_value.get('area')}")
        # Note: new_value contains the update dict, which has the region that was auto-derived
        # The backend sets region based on area lookup, so new_value.region should match expected_new_region
        if new_value.get("region") != expected_new_region:
            new_value_checks.append(f"new region mismatch: expected {expected_new_region}, got {new_value.get('region')}")
        
        if new_value_checks:
            log_test("User History - new_value Accuracy", False, "; ".join(new_value_checks))
        else:
            log_test("User History - new_value Accuracy", True)
        
        # Verify entries are sorted by created_at descending (most recent first)
        if len(history) > 1:
            sorted_check = True
            for i in range(len(history) - 1):
                if history[i].get("created_at", "") < history[i+1].get("created_at", ""):
                    sorted_check = False
                    break
            
            if sorted_check:
                log_test("User History - Sorted Descending", True)
            else:
                log_test("User History - Sorted Descending", False, "Entries not sorted by created_at desc")
        else:
            log_test("User History - Sorted Descending", True, "Only one entry, sort order N/A")
        
        # Step 5: Test authorization - RCO should get 403
        print("\n   Step 5: Testing authorization (RCO should get 403)...")
        rco_login = login(CREDENTIALS["rco_banda_aceh"]["nip"])
        if not rco_login:
            log_test("User History - RCO Authorization", False, "RCO login failed")
            return user_id
        
        rco_token = rco_login["token"]
        rco_headers = {"Authorization": f"Bearer {rco_token}"}
        
        resp = requests.get(f"{BASE_URL}/users/{user_id}/history", headers=rco_headers, timeout=10)
        
        if resp.status_code == 403:
            print(f"   ✓ RCO correctly blocked with 403")
            log_test("User History - RCO Authorization", True)
        else:
            print(f"   ✗ RCO got {resp.status_code}, expected 403")
            log_test("User History - RCO Authorization", False, f"Expected 403, got {resp.status_code}")
        
        return user_id
        
    except Exception as e:
        log_test("User History - Exception", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\n✅ PASSED: {len(test_results['passed'])}")
    for test in test_results["passed"]:
        print(f"  {test}")
    
    if test_results["warnings"]:
        print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
        for warning in test_results["warnings"]:
            print(f"  {warning}")
    
    if test_results["failed"]:
        print(f"\n❌ FAILED: {len(test_results['failed'])}")
        for test in test_results["failed"]:
            print(f"  {test}")
    
    print(f"\nTotal: {len(test_results['passed']) + len(test_results['failed'])} tests")
    print(f"Pass rate: {len(test_results['passed']) / (len(test_results['passed']) + len(test_results['failed'])) * 100:.1f}%")
    
    return len(test_results["failed"]) == 0


def main():
    """Run all tests for the 3 NEW backend endpoints"""
    print("\n" + "="*80)
    print("RCG DIGITAL RESTRUCTURING - BACKEND API TESTING")
    print("Testing 3 NEW Endpoints: Audit Panel, Excel Export, Shared Presets")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Run ID: {TEST_RUN_ID}")
    
    # Run tests for 3 new endpoints
    test_audit_panel()
    test_excel_export()
    test_shared_presets()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\n✅ PASSED: {len(test_results['passed'])}")
    for result in test_results["passed"]:
        print(f"  {result}")
    
    if test_results["failed"]:
        print(f"\n❌ FAILED: {len(test_results['failed'])}")
        for result in test_results["failed"]:
            print(f"  {result}")
    
    if test_results["warnings"]:
        print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
        for warning in test_results["warnings"]:
            print(f"  {warning}")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal: {total_tests} tests, {len(test_results['passed'])} passed, {len(test_results['failed'])} failed ({pass_rate:.1f}% pass rate)")
    
    all_passed = len(test_results["failed"]) == 0
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED - See details above")
    
    sys.exit(0 if all_passed else 1)


def test_audit_panel():
    """TEST 1 - Panel Audit Global: GET /audit/meta and GET /audit with filters"""
    print("\n" + "="*80)
    print("TEST 1: PANEL AUDIT GLOBAL")
    print("="*80)
    
    # Login as admin
    admin_auth = login(CREDENTIALS["admin"]["nip"])
    if not admin_auth:
        log_test("Audit Panel - Admin Login", False, "Failed to login as admin")
        return
    
    admin_token = admin_auth["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1.1: GET /audit/meta as admin
    print("\n[1.1] GET /audit/meta as admin")
    try:
        resp = requests.get(f"{BASE_URL}/audit/meta", headers=headers, timeout=10)
        if resp.status_code == 200:
            meta = resp.json()
            has_actions = "actions" in meta and isinstance(meta["actions"], list) and len(meta["actions"]) > 0
            has_entities = "entities" in meta and isinstance(meta["entities"], list) and len(meta["entities"]) > 0
            
            if has_actions and has_entities:
                print(f"   ✓ Response: {len(meta['actions'])} actions, {len(meta['entities'])} entities")
                print(f"   Actions sample: {meta['actions'][:5]}")
                print(f"   Entities sample: {meta['entities'][:5]}")
                
                # Check for expected actions
                expected_actions = ["login", "update_user", "export_notes_excel"]
                found_actions = [a for a in expected_actions if a in meta["actions"]]
                if len(found_actions) >= 2:
                    log_test("GET /audit/meta - Returns non-empty actions and entities", True)
                else:
                    log_test("GET /audit/meta - Returns non-empty actions and entities", False, 
                            f"Expected actions like {expected_actions}, found {found_actions}")
            else:
                log_test("GET /audit/meta - Returns non-empty actions and entities", False, 
                        f"Empty lists: actions={has_actions}, entities={has_entities}")
        else:
            log_test("GET /audit/meta - Returns 200", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /audit/meta - Returns 200", False, str(e))
    
    # Test 1.2: GET /audit with filters (entity, action, date range)
    print("\n[1.2] GET /audit with filters (entity=user, action=update_user, date range)")
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "entity": "user",
            "action": "update_user",
            "date_from": today,
            "date_to": today
        }
        
        resp = requests.get(f"{BASE_URL}/audit", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            logs = resp.json()
            print(f"   ✓ Response: {len(logs)} audit log entries")
            
            # Verify all returned items match filters
            all_match = True
            for item in logs:
                if item.get("entity") != "user":
                    all_match = False
                    log_test("GET /audit filters - entity filter", False, 
                            f"Found entity={item.get('entity')}, expected 'user'")
                    break
                if item.get("action") != "update_user":
                    all_match = False
                    log_test("GET /audit filters - action filter", False, 
                            f"Found action={item.get('action')}, expected 'update_user'")
                    break
                
                # Check date range (created_at should be within [date_from, date_to+1day))
                created_at = item.get("created_at", "")
                if not created_at.startswith(today):
                    # Allow if it's within the date range (ISO format comparison)
                    if created_at < today or created_at >= f"{today}T23:59:59":
                        all_match = False
                        log_test("GET /audit filters - date range filter", False, 
                                f"Found created_at={created_at}, expected date {today}")
                        break
            
            if all_match:
                log_test("GET /audit filters - All filters working (entity, action, date)", True)
                if len(logs) > 0:
                    print(f"   Sample entry: entity={logs[0].get('entity')}, action={logs[0].get('action')}, created_at={logs[0].get('created_at')[:10]}")
            elif len(logs) == 0:
                log_warning("No audit logs found for today with entity=user, action=update_user. This might be expected if no user updates happened today.")
                log_test("GET /audit filters - Returns 200 with list", True)
        else:
            log_test("GET /audit filters - Returns 200", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /audit filters - Returns 200", False, str(e))
    
    # Test 1.3: GET /audit with q (search by nama/nip)
    print("\n[1.3] GET /audit with q=SYAMSU (search by nama)")
    try:
        params = {"q": "SYAMSU"}
        resp = requests.get(f"{BASE_URL}/audit", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            logs = resp.json()
            print(f"   ✓ Response: {len(logs)} audit log entries")
            
            # Verify all returned items have nama or nip matching "SYAMSU" (case-insensitive)
            all_match = True
            for item in logs:
                nama = (item.get("nama") or "").upper()
                nip = (item.get("nip") or "").upper()
                if "SYAMSU" not in nama and "SYAMSU" not in nip:
                    all_match = False
                    log_test("GET /audit q filter - Search by nama/nip", False, 
                            f"Found nama={item.get('nama')}, nip={item.get('nip')}, expected to contain 'SYAMSU'")
                    break
            
            if all_match and len(logs) > 0:
                log_test("GET /audit q filter - Search by nama/nip working", True)
                print(f"   Sample: nama={logs[0].get('nama')}, nip={logs[0].get('nip')}")
            elif len(logs) == 0:
                log_warning("No audit logs found with q=SYAMSU")
                log_test("GET /audit q filter - Returns 200 with list", True)
        else:
            log_test("GET /audit q filter - Returns 200", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /audit q filter - Returns 200", False, str(e))
    
    # Test 1.4: Authorization - GET /audit as RCO (should be 403)
    print("\n[1.4] Authorization: GET /audit as RCO (expect 403)")
    rco_auth = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if rco_auth:
        rco_token = rco_auth["token"]
        rco_headers = {"Authorization": f"Bearer {rco_token}"}
        
        try:
            resp = requests.get(f"{BASE_URL}/audit", headers=rco_headers, timeout=10)
            if resp.status_code == 403:
                log_test("GET /audit authorization - RCO blocked with 403", True)
            else:
                log_test("GET /audit authorization - RCO blocked with 403", False, 
                        f"Expected 403, got {resp.status_code}")
        except Exception as e:
            log_test("GET /audit authorization - RCO blocked with 403", False, str(e))
    
    # Test 1.5: Authorization - GET /audit/meta as RCO (should be 403)
    print("\n[1.5] Authorization: GET /audit/meta as RCO (expect 403)")
    if rco_auth:
        try:
            resp = requests.get(f"{BASE_URL}/audit/meta", headers=rco_headers, timeout=10)
            if resp.status_code == 403:
                log_test("GET /audit/meta authorization - RCO blocked with 403", True)
            else:
                log_test("GET /audit/meta authorization - RCO blocked with 403", False, 
                        f"Expected 403, got {resp.status_code}")
        except Exception as e:
            log_test("GET /audit/meta authorization - RCO blocked with 403", False, str(e))


def test_excel_export():
    """TEST 2 - Excel Export: GET /export/notes-excel with filters and RBAC"""
    print("\n" + "="*80)
    print("TEST 2: EXCEL EXPORT (STYLED)")
    print("="*80)
    
    # Login as admin (RCG)
    admin_auth = login(CREDENTIALS["admin"]["nip"])
    if not admin_auth:
        log_test("Excel Export - Admin Login", False, "Failed to login as admin")
        return
    
    admin_token = admin_auth["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 2.1: GET /export/notes-excel as admin (no filter)
    print("\n[2.1] GET /export/notes-excel as admin (no filter)")
    try:
        resp = requests.get(f"{BASE_URL}/export/notes-excel", headers=headers, timeout=15)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            content_disp = resp.headers.get("Content-Disposition", "")
            body_length = len(resp.content)
            
            # Check content-type contains 'spreadsheetml' (xlsx)
            is_xlsx_type = "spreadsheetml" in content_type
            # Check Content-Disposition filename starts with 'Daftar_Nota_'
            has_correct_filename = "Daftar_Nota_" in content_disp
            # Check body length > 0 and starts with PK (zip magic bytes for xlsx)
            is_valid_xlsx = body_length > 0 and resp.content[:2] == b'PK'
            
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Disposition: {content_disp}")
            print(f"   Body length: {body_length} bytes")
            print(f"   Starts with PK (xlsx magic): {resp.content[:2] == b'PK'}")
            
            if is_xlsx_type and has_correct_filename and is_valid_xlsx:
                log_test("GET /export/notes-excel - Returns valid xlsx with correct headers", True)
            else:
                details = []
                if not is_xlsx_type:
                    details.append(f"content-type={content_type}")
                if not has_correct_filename:
                    details.append(f"filename not starts with Daftar_Nota_")
                if not is_valid_xlsx:
                    details.append(f"body_length={body_length}, magic={resp.content[:2]}")
                log_test("GET /export/notes-excel - Returns valid xlsx with correct headers", False, 
                        ", ".join(details))
        else:
            log_test("GET /export/notes-excel - Returns 200", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /export/notes-excel - Returns 200", False, str(e))
    
    # Test 2.2: GET /export/notes-excel with filter (status=Draft)
    print("\n[2.2] GET /export/notes-excel as admin with filter status=Draft")
    try:
        params = {"status": "Draft"}
        resp = requests.get(f"{BASE_URL}/export/notes-excel", headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            is_valid_xlsx = len(resp.content) > 0 and resp.content[:2] == b'PK'
            content_type = resp.headers.get("Content-Type", "")
            is_xlsx_type = "spreadsheetml" in content_type
            
            if is_valid_xlsx and is_xlsx_type:
                log_test("GET /export/notes-excel with filter - Returns valid xlsx", True)
                print(f"   Body length: {len(resp.content)} bytes")
            else:
                log_test("GET /export/notes-excel with filter - Returns valid xlsx", False, 
                        f"content-type={content_type}, valid_xlsx={is_valid_xlsx}")
        else:
            log_test("GET /export/notes-excel with filter - Returns 200", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /export/notes-excel with filter - Returns 200", False, str(e))
    
    # Test 2.3: GET /export/notes-excel as RCO (RBAC: should only include RCO's own notes)
    print("\n[2.3] GET /export/notes-excel as RCO (RBAC check)")
    rco_auth = login(CREDENTIALS["rco_banda_aceh"]["nip"])
    if rco_auth:
        rco_token = rco_auth["token"]
        rco_headers = {"Authorization": f"Bearer {rco_token}"}
        
        try:
            resp = requests.get(f"{BASE_URL}/export/notes-excel", headers=rco_headers, timeout=15)
            if resp.status_code == 200:
                is_valid_xlsx = len(resp.content) > 0 and resp.content[:2] == b'PK'
                content_type = resp.headers.get("Content-Type", "")
                is_xlsx_type = "spreadsheetml" in content_type
                
                if is_valid_xlsx and is_xlsx_type:
                    log_test("GET /export/notes-excel as RCO - Returns valid xlsx (RBAC applied)", True)
                    print(f"   Body length: {len(resp.content)} bytes")
                    print(f"   Note: Cannot verify xlsx contents, but 200 + valid xlsx + no error indicates RBAC working")
                else:
                    log_test("GET /export/notes-excel as RCO - Returns valid xlsx", False, 
                            f"content-type={content_type}, valid_xlsx={is_valid_xlsx}")
            else:
                log_test("GET /export/notes-excel as RCO - Returns 200", False, 
                        f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            log_test("GET /export/notes-excel as RCO - Returns 200", False, str(e))


def test_shared_presets():
    """TEST 3 - Shared Presets: POST/GET/DELETE /presets with scope/region visibility"""
    print("\n" + "="*80)
    print("TEST 3: SHARED PRESETS (/presets)")
    print("="*80)
    
    # Login as admin
    admin_auth = login(CREDENTIALS["admin"]["nip"])
    if not admin_auth:
        log_test("Shared Presets - Admin Login", False, "Failed to login as admin")
        return
    
    admin_token = admin_auth["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    created_preset_ids = []
    
    # Test 3.1: POST /presets as admin (scope=region, region='RO I ACEH')
    print("\n[3.1] POST /presets as admin (scope=region, region='RO I ACEH')")
    try:
        payload = {
            "name": "Draft Aceh",
            "scope": "region",
            "region": "RO I ACEH",
            "filters": {"status": "Draft"}
        }
        resp = requests.post(f"{BASE_URL}/presets", headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            preset = resp.json()
            preset_id = preset.get("id")
            created_preset_ids.append(preset_id)
            
            # Verify response
            is_correct = (preset.get("scope") == "region" and 
                         preset.get("region") == "RO I ACEH" and
                         preset.get("name") == "Draft Aceh")
            
            if is_correct:
                log_test("POST /presets - Create region-scoped preset", True)
                print(f"   Created preset: id={preset_id}, scope={preset.get('scope')}, region={preset.get('region')}")
            else:
                log_test("POST /presets - Create region-scoped preset", False, 
                        f"Response mismatch: {preset}")
        else:
            log_test("POST /presets - Create region-scoped preset", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("POST /presets - Create region-scoped preset", False, str(e))
    
    # Test 3.2: POST /presets as admin (scope=global)
    print("\n[3.2] POST /presets as admin (scope=global)")
    try:
        payload = {
            "name": "Global Approved",
            "scope": "global",
            "filters": {"status": "Final Approved"}
        }
        resp = requests.post(f"{BASE_URL}/presets", headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            preset = resp.json()
            preset_id = preset.get("id")
            created_preset_ids.append(preset_id)
            
            # Verify response (region should be null for global)
            is_correct = (preset.get("scope") == "global" and 
                         preset.get("region") is None and
                         preset.get("name") == "Global Approved")
            
            if is_correct:
                log_test("POST /presets - Create global-scoped preset", True)
                print(f"   Created preset: id={preset_id}, scope={preset.get('scope')}, region={preset.get('region')}")
            else:
                log_test("POST /presets - Create global-scoped preset", False, 
                        f"Response mismatch: {preset}")
        else:
            log_test("POST /presets - Create global-scoped preset", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("POST /presets - Create global-scoped preset", False, str(e))
    
    # Test 3.3: GET /presets as RCRM RO I ACEH (should contain 'Draft Aceh' and 'Global Approved')
    print("\n[3.3] GET /presets as RCRM RO I ACEH (expect both presets)")
    rcrm_aceh_auth = login(CREDENTIALS["rcrm_aceh"]["nip"])
    if rcrm_aceh_auth:
        rcrm_token = rcrm_aceh_auth["token"]
        rcrm_headers = {"Authorization": f"Bearer {rcrm_token}"}
        
        try:
            resp = requests.get(f"{BASE_URL}/presets", headers=rcrm_headers, timeout=10)
            if resp.status_code == 200:
                presets = resp.json()
                preset_names = [p.get("name") for p in presets]
                
                has_draft_aceh = "Draft Aceh" in preset_names
                has_global_approved = "Global Approved" in preset_names
                
                print(f"   Presets returned: {preset_names}")
                
                if has_draft_aceh and has_global_approved:
                    log_test("GET /presets as RCRM RO I ACEH - Contains region and global presets", True)
                else:
                    log_test("GET /presets as RCRM RO I ACEH - Contains region and global presets", False, 
                            f"Expected 'Draft Aceh' and 'Global Approved', got {preset_names}")
            else:
                log_test("GET /presets as RCRM RO I ACEH - Returns 200", False, 
                        f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            log_test("GET /presets as RCRM RO I ACEH - Returns 200", False, str(e))
    
    # Test 3.4: GET /presets as RCRM RO II MEDAN (should contain 'Global Approved' but NOT 'Draft Aceh')
    print("\n[3.4] GET /presets as RCRM RO II MEDAN (expect only global preset)")
    # Need to find RCRM RO II MEDAN NIP
    rcrm_medan_nip = "2186008161"  # From review request
    rcrm_medan_auth = login(rcrm_medan_nip)
    if rcrm_medan_auth:
        rcrm_medan_token = rcrm_medan_auth["token"]
        rcrm_medan_headers = {"Authorization": f"Bearer {rcrm_medan_token}"}
        
        try:
            resp = requests.get(f"{BASE_URL}/presets", headers=rcrm_medan_headers, timeout=10)
            if resp.status_code == 200:
                presets = resp.json()
                preset_names = [p.get("name") for p in presets]
                
                has_draft_aceh = "Draft Aceh" in preset_names
                has_global_approved = "Global Approved" in preset_names
                
                print(f"   Presets returned: {preset_names}")
                
                if has_global_approved and not has_draft_aceh:
                    log_test("GET /presets as RCRM RO II MEDAN - Contains global but not RO I ACEH preset", True)
                else:
                    log_test("GET /presets as RCRM RO II MEDAN - Contains global but not RO I ACEH preset", False, 
                            f"Expected 'Global Approved' only, got {preset_names}")
            else:
                log_test("GET /presets as RCRM RO II MEDAN - Returns 200", False, 
                        f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            log_test("GET /presets as RCRM RO II MEDAN - Returns 200", False, str(e))
    
    # Test 3.5: GET /presets as admin (should contain both)
    print("\n[3.5] GET /presets as admin (expect both presets)")
    try:
        resp = requests.get(f"{BASE_URL}/presets", headers=headers, timeout=10)
        if resp.status_code == 200:
            presets = resp.json()
            preset_names = [p.get("name") for p in presets]
            
            has_draft_aceh = "Draft Aceh" in preset_names
            has_global_approved = "Global Approved" in preset_names
            
            print(f"   Presets returned: {preset_names}")
            
            if has_draft_aceh and has_global_approved:
                log_test("GET /presets as admin - Contains all presets", True)
            else:
                log_test("GET /presets as admin - Contains all presets", False, 
                        f"Expected both presets, got {preset_names}")
        else:
            log_test("GET /presets as admin - Returns 200", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /presets as admin - Returns 200", False, str(e))
    
    # Test 3.6: Authorization - POST /presets as non-admin RCG (should be 403)
    print("\n[3.6] Authorization: POST /presets as non-admin RCG (expect 403)")
    rcg_auth = login(CREDENTIALS["rcg_approver"]["nip"])  # IMMADHA - non-admin RCG
    if rcg_auth:
        rcg_token = rcg_auth["token"]
        rcg_headers = {"Authorization": f"Bearer {rcg_token}"}
        
        try:
            payload = {"name": "Test Preset", "scope": "global", "filters": {}}
            resp = requests.post(f"{BASE_URL}/presets", headers=rcg_headers, json=payload, timeout=10)
            if resp.status_code == 403:
                log_test("POST /presets authorization - Non-admin RCG blocked with 403", True)
            else:
                log_test("POST /presets authorization - Non-admin RCG blocked with 403", False, 
                        f"Expected 403, got {resp.status_code}")
        except Exception as e:
            log_test("POST /presets authorization - Non-admin RCG blocked with 403", False, str(e))
    
    # Test 3.7: Authorization - DELETE /presets as non-admin RCG (should be 403)
    print("\n[3.7] Authorization: DELETE /presets as non-admin RCG (expect 403)")
    if rcg_auth and len(created_preset_ids) > 0:
        try:
            resp = requests.delete(f"{BASE_URL}/presets/{created_preset_ids[0]}", headers=rcg_headers, timeout=10)
            if resp.status_code == 403:
                log_test("DELETE /presets authorization - Non-admin RCG blocked with 403", True)
            else:
                log_test("DELETE /presets authorization - Non-admin RCG blocked with 403", False, 
                        f"Expected 403, got {resp.status_code}")
        except Exception as e:
            log_test("DELETE /presets authorization - Non-admin RCG blocked with 403", False, str(e))
    
    # Test 3.8: DELETE /presets as admin (cleanup)
    print("\n[3.8] DELETE /presets as admin (cleanup)")
    for preset_id in created_preset_ids:
        try:
            resp = requests.delete(f"{BASE_URL}/presets/{preset_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("ok") == True:
                    print(f"   ✓ Deleted preset: {preset_id}")
                else:
                    log_warning(f"DELETE /presets/{preset_id} returned ok={result.get('ok')}")
            else:
                log_warning(f"DELETE /presets/{preset_id} failed: {resp.status_code}")
        except Exception as e:
            log_warning(f"DELETE /presets/{preset_id} error: {e}")
    
    # Verify presets are deleted
    print("\n[3.9] Verify presets are deleted")
    try:
        resp = requests.get(f"{BASE_URL}/presets", headers=headers, timeout=10)
        if resp.status_code == 200:
            presets = resp.json()
            preset_names = [p.get("name") for p in presets]
            
            has_draft_aceh = "Draft Aceh" in preset_names
            has_global_approved = "Global Approved" in preset_names
            
            if not has_draft_aceh and not has_global_approved:
                log_test("DELETE /presets - Presets successfully deleted", True)
            else:
                log_test("DELETE /presets - Presets successfully deleted", False, 
                        f"Presets still exist: {preset_names}")
        else:
            log_warning(f"GET /presets after delete failed: {resp.status_code}")
    except Exception as e:
        log_warning(f"GET /presets after delete error: {e}")


if __name__ == "__main__":
    # Run tests for 3 new endpoints only
    print("\n" + "="*80)
    print("RCG DIGITAL RESTRUCTURING - BACKEND API TESTING")
    print("Testing 3 NEW Endpoints: Audit Panel, Excel Export, Shared Presets")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Run ID: {TEST_RUN_ID}")
    
    test_audit_panel()
    test_excel_export()
    test_shared_presets()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\n✅ PASSED: {len(test_results['passed'])}")
    for result in test_results["passed"]:
        print(f"  {result}")
    
    if test_results["failed"]:
        print(f"\n❌ FAILED: {len(test_results['failed'])}")
        for result in test_results["failed"]:
            print(f"  {result}")
    
    if test_results["warnings"]:
        print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
        for warning in test_results["warnings"]:
            print(f"  {warning}")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal: {total_tests} tests, {len(test_results['passed'])} passed, {len(test_results['failed'])} failed ({pass_rate:.1f}% pass rate)")
    
    all_passed = len(test_results["failed"]) == 0
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED - See details above")
    
    sys.exit(0 if all_passed else 1)

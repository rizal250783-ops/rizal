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
BASE_URL = "https://github-deps-config.preview.emergentagent.com/api"

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
    """Run all tests"""
    print("="*80)
    print("RCG DIGITAL RESTRUCTURING - BACKEND API TESTS")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print("="*80)
    
    # Check if we should run only specific tests
    import os
    test_mode = os.environ.get("TEST_MODE", "all")
    
    if test_mode == "user_history_only":
        print("\n🎯 RUNNING USER HISTORY TEST ONLY\n")
        test_user_history()
    elif test_mode == "admin_edit_only":
        print("\n🎯 RUNNING ADMIN EDIT USER TESTS ONLY\n")
        test_admin_edit_limit()
        test_admin_move_area()
        test_authorization_non_admin()
        test_admin_create_rcg_user()
    else:
        # Run approval flow tests
        approved_small = test_approval_flow_small_amount()
        approved_large = test_approval_flow_large_amount()
        test_approval_flow_reject()
        test_approval_flow_revisi()
        test_authorization()
        
        # Use one of the approved notas for PDF test
        approved_nota = approved_small or approved_large
        
        # Run other tests
        test_search_and_filter(approved_nota)
        test_pdf_generation(approved_nota)
        test_dashboard()
        
        # Run admin edit user tests
        test_admin_edit_limit()
        test_admin_move_area()
        test_authorization_non_admin()
        test_admin_create_rcg_user()
        
        # Run user history test
        test_user_history()
    
    # Print summary
    all_passed = print_summary()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

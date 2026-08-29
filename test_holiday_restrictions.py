#!/usr/bin/env python3
"""
Test suite for RCG Digital Restructuring - Holiday Write Restrictions
Testing that ONLY SYAMSU RIZAL (NIP 2183008345) can WRITE holidays,
while shared reference endpoints remain open to all logged-in users.
"""
import requests
import json
from typing import Optional

# Backend URL from frontend/.env
BASE_URL = "https://rizal-ops-setup.preview.emergentagent.com/api"

# Test credentials (all passwords: bsi12345)
SYAMSU_RIZAL = {"nip": "2183008345", "password": "bsi12345", "name": "SYAMSU RIZAL", "role": "RCG", "is_admin": True}
RATMIYATI = {"nip": "2180007674", "password": "bsi12345", "name": "RATMIYATI", "role": "RCG", "is_admin": False}
IMMADHA = {"nip": "2175007386", "password": "bsi12345", "name": "IMMADHA", "role": "RCG", "is_admin": False}
RCRM_USER = {"nip": "2188017223", "password": "bsi12345", "name": "RCRM User", "role": "RCRM", "is_admin": False}
RCO_USER = {"nip": "2193020835", "password": "bsi12345", "name": "RCO User", "role": "RCO", "is_admin": False}

def login(nip: str, password: str) -> Optional[str]:
    """Login and return token."""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"nip": nip, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("token")
        else:
            print(f"❌ Login failed for NIP {nip}: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Login exception for NIP {nip}: {e}")
        return None

def test_post_holiday(token: str, user_name: str, expected_status: int) -> tuple[bool, Optional[str]]:
    """Test POST /api/holidays endpoint. Returns (success, holiday_id)."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"tanggal": "2025-12-25", "keterangan": "Test Libur"}
        resp = requests.post(f"{BASE_URL}/holidays", json=payload, headers=headers, timeout=10)
        
        if resp.status_code == expected_status:
            if expected_status == 200:
                data = resp.json()
                holiday_id = data.get("id")
                print(f"✅ POST /holidays as {user_name}: {resp.status_code} (created holiday id={holiday_id})")
                return True, holiday_id
            else:
                print(f"✅ POST /holidays as {user_name}: {resp.status_code} (correctly blocked)")
                return True, None
        else:
            print(f"❌ POST /holidays as {user_name}: Expected {expected_status}, got {resp.status_code} - {resp.text}")
            return False, None
    except Exception as e:
        print(f"❌ POST /holidays as {user_name} exception: {e}")
        return False, None

def test_delete_holiday(token: str, user_name: str, holiday_id: str, expected_status: int) -> bool:
    """Test DELETE /api/holidays/{id} endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.delete(f"{BASE_URL}/holidays/{holiday_id}", headers=headers, timeout=10)
        
        if resp.status_code == expected_status:
            if expected_status == 200:
                print(f"✅ DELETE /holidays/{holiday_id} as {user_name}: {resp.status_code} (deleted successfully)")
            else:
                print(f"✅ DELETE /holidays/{holiday_id} as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ DELETE /holidays/{holiday_id} as {user_name}: Expected {expected_status}, got {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ DELETE /holidays/{holiday_id} as {user_name} exception: {e}")
        return False

def test_get_regions(token: str, user_name: str) -> tuple[bool, Optional[str]]:
    """Test GET /api/regions endpoint. Returns (success, first_region_name)."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/regions", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 0:
                first_region = data[0].get("nama")
                print(f"✅ GET /regions as {user_name}: {resp.status_code} (returned {len(data)} regions, first: {first_region})")
                return True, first_region
            else:
                print(f"⚠️  GET /regions as {user_name}: {resp.status_code} (returned 0 regions)")
                return True, None
        else:
            print(f"❌ GET /regions as {user_name}: Expected 200, got {resp.status_code} - {resp.text}")
            return False, None
    except Exception as e:
        print(f"❌ GET /regions as {user_name} exception: {e}")
        return False, None

def test_get_areas(token: str, user_name: str, region: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """Test GET /api/areas endpoint. Returns (success, first_area_name)."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BASE_URL}/areas"
        if region:
            url += f"?region={region}"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 0:
                first_area = data[0].get("nama")
                print(f"✅ GET /areas as {user_name} (region={region}): {resp.status_code} (returned {len(data)} areas, first: {first_area})")
                return True, first_area
            else:
                print(f"⚠️  GET /areas as {user_name} (region={region}): {resp.status_code} (returned 0 areas)")
                return True, None
        else:
            print(f"❌ GET /areas as {user_name}: Expected 200, got {resp.status_code} - {resp.text}")
            return False, None
    except Exception as e:
        print(f"❌ GET /areas as {user_name} exception: {e}")
        return False, None

def test_get_branches(token: str, user_name: str, area: Optional[str] = None) -> bool:
    """Test GET /api/branches endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BASE_URL}/branches"
        if area:
            url += f"?area={area}"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ GET /branches as {user_name} (area={area}): {resp.status_code} (returned {len(data)} branches)")
            return True
        else:
            print(f"❌ GET /branches as {user_name}: Expected 200, got {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ GET /branches as {user_name} exception: {e}")
        return False

def test_get_holidays(token: str, user_name: str) -> bool:
    """Test GET /api/holidays endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/holidays", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ GET /holidays as {user_name}: {resp.status_code} (returned {len(data)} holidays)")
            return True
        else:
            print(f"❌ GET /holidays as {user_name}: Expected 200, got {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ GET /holidays as {user_name} exception: {e}")
        return False

def main():
    print("=" * 80)
    print("HOLIDAY WRITE RESTRICTIONS & SHARED REFERENCE ENDPOINTS TEST")
    print("=" * 80)
    print()
    
    results = []
    
    # ========== PART 1: HOLIDAY WRITE RESTRICTION ==========
    print("=" * 80)
    print("PART 1: HOLIDAY WRITE RESTRICTION (admin-only)")
    print("=" * 80)
    print()
    
    # TEST CASE A: SYAMSU RIZAL (admin) should be able to POST and DELETE holidays
    print("TEST CASE A: SYAMSU RIZAL (NIP 2183008345, RCG admin)")
    print("-" * 80)
    token_admin = login(SYAMSU_RIZAL["nip"], SYAMSU_RIZAL["password"])
    if not token_admin:
        print("❌ CRITICAL: Failed to login as SYAMSU RIZAL")
        return
    
    # A1: POST /holidays should return 200
    success_a1, holiday_id = test_post_holiday(token_admin, SYAMSU_RIZAL["name"], 200)
    results.append(("A1: POST /holidays as SYAMSU RIZAL", success_a1))
    
    # A2: DELETE /holidays/{id} should return 200
    if holiday_id:
        success_a2 = test_delete_holiday(token_admin, SYAMSU_RIZAL["name"], holiday_id, 200)
        results.append(("A2: DELETE /holidays/{id} as SYAMSU RIZAL", success_a2))
    else:
        print("⚠️  Skipping DELETE test (no holiday_id from POST)")
        results.append(("A2: DELETE /holidays/{id} as SYAMSU RIZAL", False))
    
    print()
    
    # TEST CASE B: RATMIYATI (RCG non-admin) should be DENIED
    print("TEST CASE B: RATMIYATI (NIP 2180007674, RCG non-admin)")
    print("-" * 80)
    token_ratmiyati = login(RATMIYATI["nip"], RATMIYATI["password"])
    if not token_ratmiyati:
        print("❌ CRITICAL: Failed to login as RATMIYATI")
        return
    
    # B1: POST /holidays should return 403
    success_b1, _ = test_post_holiday(token_ratmiyati, RATMIYATI["name"], 403)
    results.append(("B1: POST /holidays as RATMIYATI (expect 403)", success_b1))
    
    # B2: DELETE /holidays/{anyid} should return 403
    # Use a dummy ID since we don't expect it to work anyway
    success_b2 = test_delete_holiday(token_ratmiyati, RATMIYATI["name"], "dummy-id", 403)
    results.append(("B2: DELETE /holidays/{anyid} as RATMIYATI (expect 403)", success_b2))
    
    print()
    
    # TEST CASE C: IMMADHA (RCG non-admin) should be DENIED
    print("TEST CASE C: IMMADHA (NIP 2175007386, RCG non-admin)")
    print("-" * 80)
    token_immadha = login(IMMADHA["nip"], IMMADHA["password"])
    if not token_immadha:
        print("❌ CRITICAL: Failed to login as IMMADHA")
        return
    
    # C1: POST /holidays should return 403
    success_c1, _ = test_post_holiday(token_immadha, IMMADHA["name"], 403)
    results.append(("C1: POST /holidays as IMMADHA (expect 403)", success_c1))
    
    print()
    
    # TEST CASE D: RCRM user should be DENIED
    print("TEST CASE D: RCRM User (NIP 2188017223, RCRM)")
    print("-" * 80)
    token_rcrm = login(RCRM_USER["nip"], RCRM_USER["password"])
    if not token_rcrm:
        print("❌ CRITICAL: Failed to login as RCRM user")
        return
    
    # D1: POST /holidays should return 403
    success_d1, _ = test_post_holiday(token_rcrm, RCRM_USER["name"], 403)
    results.append(("D1: POST /holidays as RCRM (expect 403)", success_d1))
    
    print()
    
    # ========== PART 2: SHARED REFERENCE ENDPOINTS (NO REGRESSION) ==========
    print("=" * 80)
    print("PART 2: SHARED REFERENCE ENDPOINTS (must remain open to all authenticated users)")
    print("=" * 80)
    print()
    
    # TEST CASE E: GET /regions as RCO user
    print("TEST CASE E: GET /regions as RCO User (NIP 2193020835)")
    print("-" * 80)
    token_rco = login(RCO_USER["nip"], RCO_USER["password"])
    if not token_rco:
        print("❌ CRITICAL: Failed to login as RCO user")
        return
    
    success_e, first_region = test_get_regions(token_rco, RCO_USER["name"])
    results.append(("E: GET /regions as RCO", success_e))
    print()
    
    # TEST CASE F: GET /areas as RCO user
    print("TEST CASE F: GET /areas as RCO User")
    print("-" * 80)
    success_f, first_area = test_get_areas(token_rco, RCO_USER["name"], first_region)
    results.append(("F: GET /areas as RCO", success_f))
    print()
    
    # TEST CASE G: GET /branches as RCO user
    print("TEST CASE G: GET /branches as RCO User")
    print("-" * 80)
    success_g = test_get_branches(token_rco, RCO_USER["name"], first_area)
    results.append(("G: GET /branches as RCO", success_g))
    print()
    
    # TEST CASE H: GET /holidays as RCO user
    print("TEST CASE H: GET /holidays as RCO User")
    print("-" * 80)
    success_h = test_get_holidays(token_rco, RCO_USER["name"])
    results.append(("H: GET /holidays as RCO", success_h))
    print()
    
    # Additional verification: Test shared reference endpoints as RCRM user
    print("ADDITIONAL VERIFICATION: Shared reference endpoints as RCRM User (NIP 2188017223)")
    print("-" * 80)
    success_rcrm_regions, rcrm_region = test_get_regions(token_rcrm, RCRM_USER["name"])
    results.append(("RCRM: GET /regions", success_rcrm_regions))
    
    success_rcrm_areas, rcrm_area = test_get_areas(token_rcrm, RCRM_USER["name"], rcrm_region)
    results.append(("RCRM: GET /areas", success_rcrm_areas))
    
    success_rcrm_branches = test_get_branches(token_rcrm, RCRM_USER["name"], rcrm_area)
    results.append(("RCRM: GET /branches", success_rcrm_branches))
    
    success_rcrm_holidays = test_get_holidays(token_rcrm, RCRM_USER["name"])
    results.append(("RCRM: GET /holidays", success_rcrm_holidays))
    print()
    
    # ========== SUMMARY ==========
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"PASSED: {passed}/{total} ({100*passed//total}%)")
    print()
    
    if passed == total:
        print("✅ ALL TESTS PASSED")
        print()
        print("PART 1 - Holiday WRITE restriction:")
        print("  ✅ SYAMSU RIZAL (2183008345) can POST and DELETE holidays")
        print("  ✅ RATMIYATI (2180007674, RCG non-admin) correctly blocked with 403")
        print("  ✅ IMMADHA (2175007386, RCG non-admin) correctly blocked with 403")
        print("  ✅ RCRM user (2188017223) correctly blocked with 403")
        print()
        print("PART 2 - Shared reference endpoints (NO REGRESSION):")
        print("  ✅ GET /regions returns 200 for RCO and RCRM users")
        print("  ✅ GET /areas returns 200 for RCO and RCRM users")
        print("  ✅ GET /branches returns 200 for RCO and RCRM users")
        print("  ✅ GET /holidays returns 200 for RCO and RCRM users")
        print()
        print("CONCLUSION: Holiday write operations are correctly restricted to admin-only,")
        print("while shared reference endpoints remain open to all authenticated users.")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Failed tests:")
        for test_name, success in results:
            if not success:
                print(f"  ❌ {test_name}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()

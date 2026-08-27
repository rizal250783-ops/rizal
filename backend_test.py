#!/usr/bin/env python3
"""
Backend test for RCG Digital Restructuring - Master Data CRUD, Holiday History, and Access-Denied Notifications
Test all scenarios from the review request.
"""
import requests
import json
from typing import Optional

# Configuration
BASE_URL = "https://github-import-setup-4.preview.emergentagent.com/api"
DEFAULT_PASSWORD = "bsi12345"

# Test users
ADMIN_NIP = "2183008345"  # SYAMSU RIZAL (RCG admin)
NON_ADMIN_RCG_NIP = "2180007674"  # RATMIYATI (RCG non-admin)
RCRM_NIP = "2188017223"  # RCRM user

# Test data storage
test_data = {
    "region_id": None,
    "area_id": None,
    "branch_id": None,
    "holiday_id": None,
    "cascade_region_id": None,
    "cascade_area_id": None,
    "cascade_branch_id": None,
}

def login(nip: str, password: str = DEFAULT_PASSWORD) -> Optional[str]:
    """Login and return token"""
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

def headers(token: str) -> dict:
    """Return authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def test_case(num: str, description: str, passed: bool, details: str = ""):
    """Print test case result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} - Case {num}: {description}")
    if details:
        print(f"  Details: {details}")

# ============================================================
# PART 1 - Region CRUD (as SYAMSU RIZAL)
# ============================================================
def test_part1_region_crud():
    print("\n" + "="*80)
    print("PART 1 - REGION CRUD (as SYAMSU RIZAL)")
    print("="*80)
    
    token = login(ADMIN_NIP)
    if not token:
        print("❌ CRITICAL: Cannot login as admin")
        return False
    
    h = headers(token)
    
    # Case 1: POST /api/regions {"nama":"RO TEST ZONE"} → expect 200
    print("\n--- Case 1: Create region 'RO TEST ZONE' ---")
    resp = requests.post(f"{BASE_URL}/regions", json={"nama": "RO TEST ZONE"}, headers=h, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_data["region_id"] = data.get("id")
        test_case("1", "POST /api/regions 'RO TEST ZONE'", True, f"Status: {resp.status_code}, ID: {test_data['region_id']}")
    else:
        test_case("1", "POST /api/regions 'RO TEST ZONE'", False, f"Status: {resp.status_code}, Expected: 200, Body: {resp.text}")
        return False
    
    # Case 2: POST /api/regions {"nama":"RO TEST ZONE"} again → expect 400 (duplicate)
    print("\n--- Case 2: Create duplicate region 'RO TEST ZONE' ---")
    resp = requests.post(f"{BASE_URL}/regions", json={"nama": "RO TEST ZONE"}, headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("2", "POST /api/regions duplicate 'RO TEST ZONE'", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    # Case 3: PUT /api/regions/{id} {"nama":"RO TEST ZONE 2"} → expect 200 (rename)
    print("\n--- Case 3: Rename region to 'RO TEST ZONE 2' ---")
    resp = requests.put(f"{BASE_URL}/regions/{test_data['region_id']}", 
                       json={"nama": "RO TEST ZONE 2"}, headers=h, timeout=10)
    passed = resp.status_code == 200
    test_case("3", "PUT /api/regions rename to 'RO TEST ZONE 2'", passed, 
              f"Status: {resp.status_code}, Expected: 200")
    
    return True

# ============================================================
# PART 2 - Area CRUD (as SYAMSU RIZAL)
# ============================================================
def test_part2_area_crud():
    print("\n" + "="*80)
    print("PART 2 - AREA CRUD (as SYAMSU RIZAL)")
    print("="*80)
    
    token = login(ADMIN_NIP)
    if not token:
        print("❌ CRITICAL: Cannot login as admin")
        return False
    
    h = headers(token)
    
    # Case 4: POST /api/areas {"nama":"Area Test A","region":"RO TEST ZONE 2"} → expect 200
    print("\n--- Case 4: Create area 'Area Test A' under 'RO TEST ZONE 2' ---")
    resp = requests.post(f"{BASE_URL}/areas", 
                        json={"nama": "Area Test A", "region": "RO TEST ZONE 2"}, 
                        headers=h, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_data["area_id"] = data.get("id")
        test_case("4", "POST /api/areas 'Area Test A'", True, 
                 f"Status: {resp.status_code}, ID: {test_data['area_id']}")
    else:
        test_case("4", "POST /api/areas 'Area Test A'", False, 
                 f"Status: {resp.status_code}, Expected: 200, Body: {resp.text}")
        return False
    
    # Case 5: POST /api/areas {"nama":"Area Test A","region":"RO TEST ZONE 2"} again → expect 400 (duplicate)
    print("\n--- Case 5: Create duplicate area 'Area Test A' ---")
    resp = requests.post(f"{BASE_URL}/areas", 
                        json={"nama": "Area Test A", "region": "RO TEST ZONE 2"}, 
                        headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("5", "POST /api/areas duplicate 'Area Test A'", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    # Case 6: POST /api/areas {"nama":"Area Test B","region":"REGION TIDAK ADA"} → expect 400 (invalid region)
    print("\n--- Case 6: Create area with invalid region ---")
    resp = requests.post(f"{BASE_URL}/areas", 
                        json={"nama": "Area Test B", "region": "REGION TIDAK ADA"}, 
                        headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("6", "POST /api/areas with invalid region", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    return True

# ============================================================
# PART 3 - Branch CRUD (as SYAMSU RIZAL)
# ============================================================
def test_part3_branch_crud():
    print("\n" + "="*80)
    print("PART 3 - BRANCH CRUD (as SYAMSU RIZAL)")
    print("="*80)
    
    token = login(ADMIN_NIP)
    if not token:
        print("❌ CRITICAL: Cannot login as admin")
        return False
    
    h = headers(token)
    
    # Case 7: POST /api/branches → expect 200
    print("\n--- Case 7: Create branch 'KC TEST SATU' ---")
    resp = requests.post(f"{BASE_URL}/branches", 
                        json={
                            "kode_outlet_bsi": "TST0001",
                            "nama_cabang": "KC TEST SATU",
                            "jenis_outlet": "KC",
                            "area": "Area Test A"
                        }, 
                        headers=h, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test_data["branch_id"] = data.get("id")
        test_case("7", "POST /api/branches 'KC TEST SATU'", True, 
                 f"Status: {resp.status_code}, ID: {test_data['branch_id']}")
    else:
        test_case("7", "POST /api/branches 'KC TEST SATU'", False, 
                 f"Status: {resp.status_code}, Expected: 200, Body: {resp.text}")
        return False
    
    # Case 8: POST /api/branches with same kode_outlet_bsi "TST0001" → expect 400 (duplicate kode)
    print("\n--- Case 8: Create branch with duplicate kode_outlet_bsi ---")
    resp = requests.post(f"{BASE_URL}/branches", 
                        json={
                            "kode_outlet_bsi": "TST0001",
                            "nama_cabang": "KC TEST DUA",
                            "jenis_outlet": "KC",
                            "area": "Area Test A"
                        }, 
                        headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("8", "POST /api/branches duplicate kode_outlet_bsi", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    # Case 9: POST /api/branches with invalid area → expect 400
    print("\n--- Case 9: Create branch with invalid area ---")
    resp = requests.post(f"{BASE_URL}/branches", 
                        json={
                            "kode_outlet_bsi": "TST0002",
                            "nama_cabang": "X",
                            "jenis_outlet": "KC",
                            "area": "Area Tidak Ada"
                        }, 
                        headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("9", "POST /api/branches with invalid area", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    # Case 10: PUT /api/branches/{id} → expect 200
    print("\n--- Case 10: Update branch 'KC TEST SATU EDIT' ---")
    resp = requests.put(f"{BASE_URL}/branches/{test_data['branch_id']}", 
                       json={
                           "kode_outlet_bsi": "TST0001",
                           "nama_cabang": "KC TEST SATU EDIT",
                           "jenis_outlet": "KCP",
                           "area": "Area Test A"
                       }, 
                       headers=h, timeout=10)
    passed = resp.status_code == 200
    test_case("10", "PUT /api/branches update to 'KC TEST SATU EDIT'", passed, 
              f"Status: {resp.status_code}, Expected: 200")
    
    return True

# ============================================================
# PART 4 - Cascade & delete guards (as SYAMSU RIZAL)
# ============================================================
def test_part4_cascade_and_guards():
    print("\n" + "="*80)
    print("PART 4 - CASCADE & DELETE GUARDS (as SYAMSU RIZAL)")
    print("="*80)
    
    token = login(ADMIN_NIP)
    if not token:
        print("❌ CRITICAL: Cannot login as admin")
        return False
    
    h = headers(token)
    
    # Case 11: DELETE /api/regions/{RO TEST ZONE 2 id} while it still has "Area Test A" → expect 400
    print("\n--- Case 11: Try to delete region that still has areas ---")
    resp = requests.delete(f"{BASE_URL}/regions/{test_data['region_id']}", headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("11", "DELETE region with existing areas (guard)", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    # Case 12: DELETE /api/areas/{Area Test A id} while it still has branch → expect 400
    print("\n--- Case 12: Try to delete area that still has branches ---")
    resp = requests.delete(f"{BASE_URL}/areas/{test_data['area_id']}", headers=h, timeout=10)
    passed = resp.status_code == 400
    test_case("12", "DELETE area with existing branches (guard)", passed, 
              f"Status: {resp.status_code}, Expected: 400, Message: {resp.json().get('detail', '') if passed else resp.text}")
    
    # Case 13: Cleanup + cascade verification
    print("\n--- Case 13: Cleanup - delete branch, then area, then region ---")
    
    # Delete branch
    resp = requests.delete(f"{BASE_URL}/branches/{test_data['branch_id']}", headers=h, timeout=10)
    passed_branch = resp.status_code == 200
    print(f"  13a. DELETE branch: Status {resp.status_code}, Expected: 200 - {'✅' if passed_branch else '❌'}")
    
    # Verify area still exists
    resp = requests.get(f"{BASE_URL}/areas?region=RO TEST ZONE 2", headers=h, timeout=10)
    areas = resp.json() if resp.status_code == 200 else []
    area_exists = any(a.get("nama") == "Area Test A" for a in areas)
    print(f"  13b. GET /api/areas?region=RO TEST ZONE 2: Area Test A exists: {area_exists} - {'✅' if area_exists else '❌'}")
    
    # Delete area
    resp = requests.delete(f"{BASE_URL}/areas/{test_data['area_id']}", headers=h, timeout=10)
    passed_area = resp.status_code == 200
    print(f"  13c. DELETE area: Status {resp.status_code}, Expected: 200 - {'✅' if passed_area else '❌'}")
    
    # Delete region
    resp = requests.delete(f"{BASE_URL}/regions/{test_data['region_id']}", headers=h, timeout=10)
    passed_region = resp.status_code == 200
    print(f"  13d. DELETE region: Status {resp.status_code}, Expected: 200 - {'✅' if passed_region else '❌'}")
    
    passed = passed_branch and area_exists and passed_area and passed_region
    test_case("13", "Cleanup cascade verification", passed, 
              f"Branch deleted: {passed_branch}, Area persisted: {area_exists}, Area deleted: {passed_area}, Region deleted: {passed_region}")
    
    # Case 14: Rename cascade check
    print("\n--- Case 14: Rename cascade check ---")
    
    # Create region "RO CAS"
    resp = requests.post(f"{BASE_URL}/regions", json={"nama": "RO CAS"}, headers=h, timeout=10)
    if resp.status_code == 200:
        test_data["cascade_region_id"] = resp.json().get("id")
        print(f"  14a. Created region 'RO CAS': ID {test_data['cascade_region_id']} - ✅")
    else:
        print(f"  14a. Failed to create region 'RO CAS': {resp.status_code} - ❌")
        return False
    
    # Create area "Area Cas" under "RO CAS"
    resp = requests.post(f"{BASE_URL}/areas", 
                        json={"nama": "Area Cas", "region": "RO CAS"}, 
                        headers=h, timeout=10)
    if resp.status_code == 200:
        test_data["cascade_area_id"] = resp.json().get("id")
        print(f"  14b. Created area 'Area Cas': ID {test_data['cascade_area_id']} - ✅")
    else:
        print(f"  14b. Failed to create area 'Area Cas': {resp.status_code} - ❌")
        return False
    
    # Create branch "CAS001" under "Area Cas"
    resp = requests.post(f"{BASE_URL}/branches", 
                        json={
                            "kode_outlet_bsi": "CAS001",
                            "nama_cabang": "KC CAS TEST",
                            "jenis_outlet": "KC",
                            "area": "Area Cas"
                        }, 
                        headers=h, timeout=10)
    if resp.status_code == 200:
        test_data["cascade_branch_id"] = resp.json().get("id")
        print(f"  14c. Created branch 'CAS001': ID {test_data['cascade_branch_id']} - ✅")
    else:
        print(f"  14c. Failed to create branch 'CAS001': {resp.status_code} - ❌")
        return False
    
    # Rename region to "RO CAS 2"
    resp = requests.put(f"{BASE_URL}/regions/{test_data['cascade_region_id']}", 
                       json={"nama": "RO CAS 2"}, headers=h, timeout=10)
    passed_rename = resp.status_code == 200
    print(f"  14d. Renamed region to 'RO CAS 2': Status {resp.status_code} - {'✅' if passed_rename else '❌'}")
    
    # Verify area.region updated
    resp = requests.get(f"{BASE_URL}/areas?region=RO CAS 2", headers=h, timeout=10)
    areas = resp.json() if resp.status_code == 200 else []
    area_updated = any(a.get("nama") == "Area Cas" for a in areas)
    print(f"  14e. GET /api/areas?region=RO CAS 2: Area Cas found: {area_updated} - {'✅' if area_updated else '❌'}")
    
    # Verify branch.region updated
    resp = requests.get(f"{BASE_URL}/branches?area=Area Cas", headers=h, timeout=10)
    branches = resp.json() if resp.status_code == 200 else []
    branch_updated = False
    if branches:
        for b in branches:
            if b.get("kode_outlet_bsi") == "CAS001":
                branch_updated = b.get("region") == "RO CAS 2"
                print(f"  14f. Branch CAS001 region: {b.get('region')} (expected: RO CAS 2) - {'✅' if branch_updated else '❌'}")
                break
    
    # Cleanup cascade test data
    requests.delete(f"{BASE_URL}/branches/{test_data['cascade_branch_id']}", headers=h, timeout=10)
    requests.delete(f"{BASE_URL}/areas/{test_data['cascade_area_id']}", headers=h, timeout=10)
    requests.delete(f"{BASE_URL}/regions/{test_data['cascade_region_id']}", headers=h, timeout=10)
    print(f"  14g. Cleanup cascade test data - ✅")
    
    passed = passed_rename and area_updated and branch_updated
    test_case("14", "Rename cascade check", passed, 
              f"Region renamed: {passed_rename}, Area region updated: {area_updated}, Branch region updated: {branch_updated}")
    
    return True

# ============================================================
# PART 5 - Holiday history
# ============================================================
def test_part5_holiday_history():
    print("\n" + "="*80)
    print("PART 5 - HOLIDAY HISTORY (as SYAMSU RIZAL)")
    print("="*80)
    
    token = login(ADMIN_NIP)
    if not token:
        print("❌ CRITICAL: Cannot login as admin")
        return False
    
    h = headers(token)
    
    # Case 15: POST holiday, GET history, DELETE holiday, verify history
    print("\n--- Case 15: Holiday history verification ---")
    
    # POST holiday
    resp = requests.post(f"{BASE_URL}/holidays", 
                        json={"tanggal": "2025-12-31", "keterangan": "Uji Riwayat"}, 
                        headers=h, timeout=10)
    if resp.status_code == 200:
        test_data["holiday_id"] = resp.json().get("id")
        print(f"  15a. POST /api/holidays: Status {resp.status_code}, ID {test_data['holiday_id']} - ✅")
    else:
        print(f"  15a. POST /api/holidays failed: Status {resp.status_code} - ❌")
        test_case("15", "Holiday history", False, f"Failed to create holiday: {resp.status_code}")
        return False
    
    # GET history - should contain add_holiday
    resp = requests.get(f"{BASE_URL}/holidays/history", headers=h, timeout=10)
    if resp.status_code == 200:
        history = resp.json()
        add_entry = any(h.get("action") == "add_holiday" and h.get("entity_id") == test_data["holiday_id"] 
                       for h in history)
        print(f"  15b. GET /api/holidays/history: Status {resp.status_code}, Contains add_holiday: {add_entry} - {'✅' if add_entry else '❌'}")
    else:
        print(f"  15b. GET /api/holidays/history failed: Status {resp.status_code} - ❌")
        add_entry = False
    
    # DELETE holiday
    resp = requests.delete(f"{BASE_URL}/holidays/{test_data['holiday_id']}", headers=h, timeout=10)
    delete_success = resp.status_code == 200
    print(f"  15c. DELETE /api/holidays: Status {resp.status_code} - {'✅' if delete_success else '❌'}")
    
    # GET history - should now also contain delete_holiday
    resp = requests.get(f"{BASE_URL}/holidays/history", headers=h, timeout=10)
    if resp.status_code == 200:
        history = resp.json()
        delete_entry = any(h.get("action") == "delete_holiday" and h.get("entity_id") == test_data["holiday_id"] 
                          for h in history)
        print(f"  15d. GET /api/holidays/history: Contains delete_holiday: {delete_entry} - {'✅' if delete_entry else '❌'}")
    else:
        print(f"  15d. GET /api/holidays/history failed: Status {resp.status_code} - ❌")
        delete_entry = False
    
    passed = add_entry and delete_success and delete_entry
    test_case("15", "Holiday history", passed, 
              f"Add entry found: {add_entry}, Delete success: {delete_success}, Delete entry found: {delete_entry}")
    
    return True

# ============================================================
# PART 6 - Admin-only enforcement + access-denied NOTIFICATION
# ============================================================
def test_part6_admin_only_and_notifications():
    print("\n" + "="*80)
    print("PART 6 - ADMIN-ONLY ENFORCEMENT + ACCESS-DENIED NOTIFICATION")
    print("="*80)
    
    # Case 16: Non-admin attempts
    print("\n--- Case 16: Non-admin access attempts ---")
    
    # RATMIYATI (non-admin RCG)
    token_ratmiyati = login(NON_ADMIN_RCG_NIP)
    if not token_ratmiyati:
        print("❌ CRITICAL: Cannot login as RATMIYATI")
        return False
    
    h_ratmiyati = headers(token_ratmiyati)
    
    # POST /api/regions
    resp = requests.post(f"{BASE_URL}/regions", json={"nama": "TEST"}, headers=h_ratmiyati, timeout=10)
    passed_regions = resp.status_code == 403
    print(f"  16a. RATMIYATI POST /api/regions: Status {resp.status_code}, Expected: 403 - {'✅' if passed_regions else '❌'}")
    
    # POST /api/areas
    resp = requests.post(f"{BASE_URL}/areas", json={"nama": "TEST", "region": "RO I ACEH"}, headers=h_ratmiyati, timeout=10)
    passed_areas = resp.status_code == 403
    print(f"  16b. RATMIYATI POST /api/areas: Status {resp.status_code}, Expected: 403 - {'✅' if passed_areas else '❌'}")
    
    # POST /api/branches
    resp = requests.post(f"{BASE_URL}/branches", 
                        json={"kode_outlet_bsi": "X", "nama_cabang": "X", "jenis_outlet": "KC", "area": "Area Banda Aceh"}, 
                        headers=h_ratmiyati, timeout=10)
    passed_branches = resp.status_code == 403
    print(f"  16c. RATMIYATI POST /api/branches: Status {resp.status_code}, Expected: 403 - {'✅' if passed_branches else '❌'}")
    
    # GET /api/holidays/history
    resp = requests.get(f"{BASE_URL}/holidays/history", headers=h_ratmiyati, timeout=10)
    passed_history = resp.status_code == 403
    print(f"  16d. RATMIYATI GET /api/holidays/history: Status {resp.status_code}, Expected: 403 - {'✅' if passed_history else '❌'}")
    
    # Case 17: RCRM user
    print("\n--- Case 17: RCRM user access attempt ---")
    
    token_rcrm = login(RCRM_NIP)
    if not token_rcrm:
        print("❌ CRITICAL: Cannot login as RCRM")
        return False
    
    h_rcrm = headers(token_rcrm)
    
    # POST /api/regions
    resp = requests.post(f"{BASE_URL}/regions", json={"nama": "TEST"}, headers=h_rcrm, timeout=10)
    passed_rcrm = resp.status_code == 403
    print(f"  17. RCRM POST /api/regions: Status {resp.status_code}, Expected: 403 - {'✅' if passed_rcrm else '❌'}")
    
    # Case 18: Verify access-denied notifications
    print("\n--- Case 18: Verify access-denied notifications ---")
    
    token_admin = login(ADMIN_NIP)
    if not token_admin:
        print("❌ CRITICAL: Cannot login as admin")
        return False
    
    h_admin = headers(token_admin)
    
    # GET /api/notifications
    resp = requests.get(f"{BASE_URL}/notifications", headers=h_admin, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        access_denied_notifs = [n for n in items if n.get("type") == "access_denied" 
                               and "Percobaan akses fitur admin" in n.get("message", "")]
        
        print(f"  18. GET /api/notifications: Status {resp.status_code}, Total notifications: {len(items)}")
        print(f"      Access-denied notifications found: {len(access_denied_notifs)}")
        
        if access_denied_notifs:
            print(f"      Sample notification: {access_denied_notifs[0].get('message', '')}")
            passed_notif = True
        else:
            print(f"      ❌ No access-denied notifications found")
            passed_notif = False
    else:
        print(f"  18. GET /api/notifications failed: Status {resp.status_code} - ❌")
        passed_notif = False
    
    passed = (passed_regions and passed_areas and passed_branches and passed_history and 
              passed_rcrm and passed_notif)
    test_case("16-18", "Admin-only enforcement + access-denied notifications", passed, 
              f"All 403 checks: {passed_regions and passed_areas and passed_branches and passed_history and passed_rcrm}, Notifications: {passed_notif}")
    
    return True

# ============================================================
# MAIN TEST EXECUTION
# ============================================================
def main():
    print("\n" + "="*80)
    print("RCG DIGITAL RESTRUCTURING - MASTER DATA CRUD & HOLIDAY HISTORY TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin NIP: {ADMIN_NIP}")
    print(f"Non-admin RCG NIP: {NON_ADMIN_RCG_NIP}")
    print(f"RCRM NIP: {RCRM_NIP}")
    
    results = []
    
    # Run all test parts
    results.append(("PART 1 - Region CRUD", test_part1_region_crud()))
    results.append(("PART 2 - Area CRUD", test_part2_area_crud()))
    results.append(("PART 3 - Branch CRUD", test_part3_branch_crud()))
    results.append(("PART 4 - Cascade & Guards", test_part4_cascade_and_guards()))
    results.append(("PART 5 - Holiday History", test_part5_holiday_history()))
    results.append(("PART 6 - Admin-only & Notifications", test_part6_admin_only_and_notifications()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for part_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {part_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} parts passed ({passed_count*100//total_count}%)")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} part(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())

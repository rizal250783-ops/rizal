#!/usr/bin/env python3
"""
Test suite for RCG Digital Restructuring - User Management Restriction
Testing that ONLY SYAMSU RIZAL (NIP 2183008345) can manage users.
"""
import requests
import json
from typing import Optional

# Backend URL from frontend/.env
BASE_URL = "https://github-import-setup-4.preview.emergentagent.com/api"

# Test credentials (all passwords: bsi12345)
SYAMSU_RIZAL = {"nip": "2183008345", "password": "bsi12345", "name": "SYAMSU RIZAL", "role": "RCG", "is_admin": True}
RATMIYATI = {"nip": "2180007674", "password": "bsi12345", "name": "RATMIYATI", "role": "RCG", "is_admin": False}
IMMADHA = {"nip": "2175007386", "password": "bsi12345", "name": "IMMADHA", "role": "RCG", "is_admin": False}
RCRM_USER = {"nip": "2188017223", "password": "bsi12345", "name": "RCRM User", "role": "RCRM", "is_admin": False}

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

def test_get_users(token: str, user_name: str, expected_status: int) -> bool:
    """Test GET /api/users endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                users = resp.json()
                print(f"✅ GET /users as {user_name}: {resp.status_code} (returned {len(users)} users)")
            else:
                print(f"✅ GET /users as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ GET /users as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ GET /users as {user_name} exception: {e}")
        return False

def test_create_user(token: str, user_name: str, expected_status: int) -> tuple[bool, Optional[str]]:
    """Test POST /api/users endpoint. Returns (success, created_user_id)."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Create a test user with unique NIP
        import random
        test_nip = f"9999{random.randint(100000, 999999)}"
        payload = {
            "nama": f"Test User {test_nip}",
            "nip": test_nip,
            "role": "RCO",
            "jabatan": "Test Officer",
            "area": "Area Banda Aceh",
            "region": "RO I ACEH",
            "limit_pemutus": 0,
            "status": "aktif"
        }
        resp = requests.post(f"{BASE_URL}/users", headers=headers, json=payload, timeout=10)
        if resp.status_code == expected_status:
            if expected_status in (200, 201):
                data = resp.json()
                user_id = data.get("user", {}).get("id")
                print(f"✅ POST /users as {user_name}: {resp.status_code} (created user {test_nip}, id={user_id})")
                return True, user_id
            else:
                print(f"✅ POST /users as {user_name}: {resp.status_code} (correctly blocked)")
                return True, None
        else:
            print(f"❌ POST /users as {user_name}: Expected {expected_status}, got {resp.status_code} - {resp.text}")
            return False, None
    except Exception as e:
        print(f"❌ POST /users as {user_name} exception: {e}")
        return False, None

def test_update_user(token: str, user_name: str, user_id: str, expected_status: int) -> bool:
    """Test PUT /api/users/{uid} endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "nama": "Updated Test User",
            "nip": "9999999999",  # Will be ignored (NIP is immutable)
            "role": "RCO",
            "jabatan": "Updated Officer",
            "area": "Area Medan Kota",
            "region": "RO II MEDAN",
            "limit_pemutus": 0,
            "status": "aktif"
        }
        resp = requests.put(f"{BASE_URL}/users/{user_id}", headers=headers, json=payload, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                print(f"✅ PUT /users/{user_id} as {user_name}: {resp.status_code} (updated successfully)")
            else:
                print(f"✅ PUT /users/{user_id} as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ PUT /users/{user_id} as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ PUT /users/{user_id} as {user_name} exception: {e}")
        return False

def test_get_user_history(token: str, user_name: str, user_id: str, expected_status: int) -> bool:
    """Test GET /api/users/{uid}/history endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/users/{user_id}/history", headers=headers, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                history = resp.json()
                print(f"✅ GET /users/{user_id}/history as {user_name}: {resp.status_code} (returned {len(history)} entries)")
            else:
                print(f"✅ GET /users/{user_id}/history as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ GET /users/{user_id}/history as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ GET /users/{user_id}/history as {user_name} exception: {e}")
        return False

def test_reset_password(token: str, user_name: str, user_id: str, expected_status: int) -> bool:
    """Test POST /api/users/{uid}/reset-password endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(f"{BASE_URL}/users/{user_id}/reset-password", headers=headers, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                data = resp.json()
                new_pw = data.get("generated_password", "N/A")
                print(f"✅ POST /users/{user_id}/reset-password as {user_name}: {resp.status_code} (new password: {new_pw})")
            else:
                print(f"✅ POST /users/{user_id}/reset-password as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ POST /users/{user_id}/reset-password as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ POST /users/{user_id}/reset-password as {user_name} exception: {e}")
        return False

def test_delete_user(token: str, user_name: str, user_id: str, expected_status: int) -> bool:
    """Test DELETE /api/users/{uid} endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.delete(f"{BASE_URL}/users/{user_id}", headers=headers, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                print(f"✅ DELETE /users/{user_id} as {user_name}: {resp.status_code} (deleted successfully)")
            else:
                print(f"✅ DELETE /users/{user_id} as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ DELETE /users/{user_id} as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ DELETE /users/{user_id} as {user_name} exception: {e}")
        return False

def run_test_suite():
    """Run all user management restriction tests."""
    print("=" * 80)
    print("USER MANAGEMENT RESTRICTION TEST SUITE")
    print("Testing that ONLY SYAMSU RIZAL (NIP 2183008345) can manage users")
    print("=" * 80)
    
    results = []
    
    # ========== TEST CASE A: SYAMSU RIZAL (Admin) - Should have full access ==========
    print("\n" + "=" * 80)
    print("TEST CASE A: SYAMSU RIZAL (NIP 2183008345, RCG, is_user_admin=true)")
    print("Expected: All 6 endpoints should return 200/201 (full access)")
    print("=" * 80)
    
    admin_token = login(SYAMSU_RIZAL["nip"], SYAMSU_RIZAL["password"])
    if not admin_token:
        print("❌ CRITICAL: Failed to login as SYAMSU RIZAL")
        return
    
    # A1: GET /users
    results.append(("A1: GET /users (admin)", test_get_users(admin_token, SYAMSU_RIZAL["name"], 200)))
    
    # A2: POST /users (create test user)
    success, created_user_id = test_create_user(admin_token, SYAMSU_RIZAL["name"], 200)
    results.append(("A2: POST /users (admin)", success))
    
    if not created_user_id:
        print("❌ CRITICAL: Failed to create test user, cannot continue with update/history/reset/delete tests")
        return
    
    # A3: PUT /users/{uid} (update the created user)
    results.append(("A3: PUT /users/{uid} (admin)", test_update_user(admin_token, SYAMSU_RIZAL["name"], created_user_id, 200)))
    
    # A4: GET /users/{uid}/history
    results.append(("A4: GET /users/{uid}/history (admin)", test_get_user_history(admin_token, SYAMSU_RIZAL["name"], created_user_id, 200)))
    
    # A5: POST /users/{uid}/reset-password
    results.append(("A5: POST /users/{uid}/reset-password (admin)", test_reset_password(admin_token, SYAMSU_RIZAL["name"], created_user_id, 200)))
    
    # A6: DELETE /users/{uid} (cleanup - delete the test user)
    results.append(("A6: DELETE /users/{uid} (admin)", test_delete_user(admin_token, SYAMSU_RIZAL["name"], created_user_id, 200)))
    
    # ========== TEST CASE B: RATMIYATI (RCG but not admin) - Should be denied ==========
    print("\n" + "=" * 80)
    print("TEST CASE B: RATMIYATI (NIP 2180007674, RCG, is_user_admin=false)")
    print("Expected: All 6 endpoints should return 403 (access denied)")
    print("=" * 80)
    
    ratmiyati_token = login(RATMIYATI["nip"], RATMIYATI["password"])
    if not ratmiyati_token:
        print("❌ CRITICAL: Failed to login as RATMIYATI")
        return
    
    # Create a dummy user ID for testing (we'll use IMMADHA's ID from the database)
    # First, get a valid user ID by listing users as admin
    headers = {"Authorization": f"Bearer {admin_token}"}
    users_resp = requests.get(f"{BASE_URL}/users?role=RCO", headers=headers, timeout=10)
    if users_resp.status_code == 200:
        users = users_resp.json()
        if users:
            test_user_id = users[0]["id"]
        else:
            print("❌ No RCO users found for testing")
            return
    else:
        print("❌ Failed to get users list for testing")
        return
    
    # B1: GET /users
    results.append(("B1: GET /users (RATMIYATI)", test_get_users(ratmiyati_token, RATMIYATI["name"], 403)))
    
    # B2: POST /users
    success, _ = test_create_user(ratmiyati_token, RATMIYATI["name"], 403)
    results.append(("B2: POST /users (RATMIYATI)", success))
    
    # B3: PUT /users/{uid}
    results.append(("B3: PUT /users/{uid} (RATMIYATI)", test_update_user(ratmiyati_token, RATMIYATI["name"], test_user_id, 403)))
    
    # B4: GET /users/{uid}/history
    results.append(("B4: GET /users/{uid}/history (RATMIYATI)", test_get_user_history(ratmiyati_token, RATMIYATI["name"], test_user_id, 403)))
    
    # B5: POST /users/{uid}/reset-password
    results.append(("B5: POST /users/{uid}/reset-password (RATMIYATI)", test_reset_password(ratmiyati_token, RATMIYATI["name"], test_user_id, 403)))
    
    # B6: DELETE /users/{uid}
    results.append(("B6: DELETE /users/{uid} (RATMIYATI)", test_delete_user(ratmiyati_token, RATMIYATI["name"], test_user_id, 403)))
    
    # ========== TEST CASE C: IMMADHA (RCG but not admin) - Should be denied ==========
    print("\n" + "=" * 80)
    print("TEST CASE C: IMMADHA (NIP 2175007386, RCG, is_user_admin=false)")
    print("Expected: All 6 endpoints should return 403 (access denied)")
    print("=" * 80)
    
    immadha_token = login(IMMADHA["nip"], IMMADHA["password"])
    if not immadha_token:
        print("❌ CRITICAL: Failed to login as IMMADHA")
        return
    
    # C1: GET /users
    results.append(("C1: GET /users (IMMADHA)", test_get_users(immadha_token, IMMADHA["name"], 403)))
    
    # C2: POST /users
    success, _ = test_create_user(immadha_token, IMMADHA["name"], 403)
    results.append(("C2: POST /users (IMMADHA)", success))
    
    # C3: PUT /users/{uid}
    results.append(("C3: PUT /users/{uid} (IMMADHA)", test_update_user(immadha_token, IMMADHA["name"], test_user_id, 403)))
    
    # C4: GET /users/{uid}/history
    results.append(("C4: GET /users/{uid}/history (IMMADHA)", test_get_user_history(immadha_token, IMMADHA["name"], test_user_id, 403)))
    
    # C5: POST /users/{uid}/reset-password (previously unprotected, now should be 403)
    results.append(("C5: POST /users/{uid}/reset-password (IMMADHA)", test_reset_password(immadha_token, IMMADHA["name"], test_user_id, 403)))
    
    # C6: DELETE /users/{uid}
    results.append(("C6: DELETE /users/{uid} (IMMADHA)", test_delete_user(immadha_token, IMMADHA["name"], test_user_id, 403)))
    
    # ========== TEST CASE D: RCRM User (non-RCG) - Should be denied ==========
    print("\n" + "=" * 80)
    print("TEST CASE D: RCRM User (NIP 2188017223, RCRM, non-RCG)")
    print("Expected: All 6 endpoints should return 403 (access denied)")
    print("=" * 80)
    
    rcrm_token = login(RCRM_USER["nip"], RCRM_USER["password"])
    if not rcrm_token:
        print("❌ CRITICAL: Failed to login as RCRM user")
        return
    
    # D1: GET /users
    results.append(("D1: GET /users (RCRM)", test_get_users(rcrm_token, RCRM_USER["name"], 403)))
    
    # D2: POST /users
    success, _ = test_create_user(rcrm_token, RCRM_USER["name"], 403)
    results.append(("D2: POST /users (RCRM)", success))
    
    # D3: PUT /users/{uid}
    results.append(("D3: PUT /users/{uid} (RCRM)", test_update_user(rcrm_token, RCRM_USER["name"], test_user_id, 403)))
    
    # D4: GET /users/{uid}/history
    results.append(("D4: GET /users/{uid}/history (RCRM)", test_get_user_history(rcrm_token, RCRM_USER["name"], test_user_id, 403)))
    
    # D5: POST /users/{uid}/reset-password
    results.append(("D5: POST /users/{uid}/reset-password (RCRM)", test_reset_password(rcrm_token, RCRM_USER["name"], test_user_id, 403)))
    
    # D6: DELETE /users/{uid}
    results.append(("D6: DELETE /users/{uid} (RCRM)", test_delete_user(rcrm_token, RCRM_USER["name"], test_user_id, 403)))
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed}/{total} ({100*passed//total}%)")
    
    print("\nDetailed Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! User management restriction is working correctly.")
        print("✅ ONLY SYAMSU RIZAL (NIP 2183008345) can manage users.")
        print("✅ All other users (including RCG users) are correctly blocked with 403.")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED. Please review the failures above.")
    
    print("=" * 80)

if __name__ == "__main__":
    run_test_suite()

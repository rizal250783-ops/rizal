#!/usr/bin/env python3
"""
Test suite for RCG Digital Restructuring - Audit Panel Restriction
Testing that ONLY SYAMSU RIZAL (NIP 2183008345) can access audit endpoints.

Test Cases:
A. SYAMSU RIZAL (2183008345): GET /audit and GET /audit/meta must return 200
B. RATMIYATI (2180007674, RCG but not admin): both endpoints must return 403
C. IMMADHA (2175007386, RCG but not admin): both endpoints must return 403
D. RCRM user (2188017223): both endpoints must return 403
"""
import requests
import json
from typing import Optional

# Backend URL from frontend/.env
BASE_URL = "https://rizal-ops-setup.preview.emergentagent.com/api"

# Test credentials (all passwords: bsi12345)
TEST_USERS = {
    "SYAMSU_RIZAL": {"nip": "2183008345", "password": "bsi12345", "name": "SYAMSU RIZAL", "role": "RCG", "is_admin": True},
    "RATMIYATI": {"nip": "2180007674", "password": "bsi12345", "name": "RATMIYATI", "role": "RCG", "is_admin": False},
    "IMMADHA": {"nip": "2175007386", "password": "bsi12345", "name": "IMMADHA HANDY KUSUMA", "role": "RCG", "is_admin": False},
    "RCRM_USER": {"nip": "2188017223", "password": "bsi12345", "name": "RCRM User", "role": "RCRM", "is_admin": False}
}

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

def test_get_audit(token: str, user_name: str, expected_status: int) -> bool:
    """Test GET /api/audit endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/audit", headers=headers, params={"limit": 10}, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                data = resp.json()
                print(f"✅ GET /audit as {user_name}: {resp.status_code} (returned {len(data)} audit logs)")
            else:
                print(f"✅ GET /audit as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ GET /audit as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ GET /audit as {user_name} exception: {e}")
        return False

def test_get_audit_meta(token: str, user_name: str, expected_status: int) -> bool:
    """Test GET /api/audit/meta endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/audit/meta", headers=headers, timeout=10)
        if resp.status_code == expected_status:
            if expected_status == 200:
                data = resp.json()
                actions = data.get("actions", [])
                entities = data.get("entities", [])
                print(f"✅ GET /audit/meta as {user_name}: {resp.status_code} (actions: {len(actions)}, entities: {len(entities)})")
            else:
                print(f"✅ GET /audit/meta as {user_name}: {resp.status_code} (correctly blocked)")
            return True
        else:
            print(f"❌ GET /audit/meta as {user_name}: Expected {expected_status}, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ GET /audit/meta as {user_name} exception: {e}")
        return False

def run_test_case(user_key: str, expected_status: int) -> tuple[bool, bool]:
    """Run both audit endpoint tests for a user. Returns (audit_success, meta_success)."""
    user = TEST_USERS[user_key]
    print(f"\n{'='*80}")
    print(f"Testing {user['name']} (NIP {user['nip']}, {user['role']}, is_admin={user['is_admin']})")
    print(f"Expected status: {expected_status}")
    print(f"{'='*80}")
    
    # Login
    token = login(user["nip"], user["password"])
    if not token:
        print(f"❌ Failed to login as {user['name']}")
        return False, False
    
    print(f"✅ Login successful for {user['name']}")
    
    # Test GET /audit
    audit_result = test_get_audit(token, user["name"], expected_status)
    
    # Test GET /audit/meta
    meta_result = test_get_audit_meta(token, user["name"], expected_status)
    
    return audit_result, meta_result

def main():
    """Run all test cases."""
    print("\n" + "="*80)
    print("AUDIT PANEL RESTRICTION TEST SUITE")
    print("Testing that ONLY SYAMSU RIZAL (NIP 2183008345) can access audit endpoints")
    print("="*80)
    
    results = {}
    
    # Test Case A: SYAMSU RIZAL (should get 200)
    print("\n\n### TEST CASE A: SYAMSU RIZAL (Admin) - Should Access Audit Endpoints ###")
    audit_a, meta_a = run_test_case("SYAMSU_RIZAL", 200)
    results["A"] = {"audit": audit_a, "meta": meta_a}
    
    # Test Case B: RATMIYATI (should get 403)
    print("\n\n### TEST CASE B: RATMIYATI (RCG but not admin) - Should Be Denied ###")
    audit_b, meta_b = run_test_case("RATMIYATI", 403)
    results["B"] = {"audit": audit_b, "meta": meta_b}
    
    # Test Case C: IMMADHA (should get 403)
    print("\n\n### TEST CASE C: IMMADHA (RCG but not admin) - Should Be Denied ###")
    audit_c, meta_c = run_test_case("IMMADHA", 403)
    results["C"] = {"audit": audit_c, "meta": meta_c}
    
    # Test Case D: RCRM user (should get 403)
    print("\n\n### TEST CASE D: RCRM User (Non-RCG) - Should Be Denied ###")
    audit_d, meta_d = run_test_case("RCRM_USER", 403)
    results["D"] = {"audit": audit_d, "meta": meta_d}
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = 0
    passed_tests = 0
    
    for case, endpoints in results.items():
        for endpoint, result in endpoints.items():
            total_tests += 1
            if result:
                passed_tests += 1
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests}/{total_tests} ({100*passed_tests//total_tests}%)")
    
    print("\n### Detailed Results ###")
    print(f"Test Case A (SYAMSU RIZAL - should get 200):")
    print(f"  - GET /audit: {'✅ PASS' if results['A']['audit'] else '❌ FAIL'}")
    print(f"  - GET /audit/meta: {'✅ PASS' if results['A']['meta'] else '❌ FAIL'}")
    
    print(f"\nTest Case B (RATMIYATI - should get 403):")
    print(f"  - GET /audit: {'✅ PASS' if results['B']['audit'] else '❌ FAIL'}")
    print(f"  - GET /audit/meta: {'✅ PASS' if results['B']['meta'] else '❌ FAIL'}")
    
    print(f"\nTest Case C (IMMADHA - should get 403):")
    print(f"  - GET /audit: {'✅ PASS' if results['C']['audit'] else '❌ FAIL'}")
    print(f"  - GET /audit/meta: {'✅ PASS' if results['C']['meta'] else '❌ FAIL'}")
    
    print(f"\nTest Case D (RCRM User - should get 403):")
    print(f"  - GET /audit: {'✅ PASS' if results['D']['audit'] else '❌ FAIL'}")
    print(f"  - GET /audit/meta: {'✅ PASS' if results['D']['meta'] else '❌ FAIL'}")
    
    print("\n" + "="*80)
    if passed_tests == total_tests:
        print("✅ ALL TESTS PASSED - Audit panel restriction working correctly!")
        print("Only SYAMSU RIZAL (NIP 2183008345) can access audit endpoints.")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Audit panel restriction not working as expected!")
        return 1

if __name__ == "__main__":
    exit(main())

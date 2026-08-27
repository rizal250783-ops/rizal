#!/usr/bin/env python3
"""
Test suite for RCG Digital Restructuring - Holiday Duplicate Validation & Access-Denied Audit Logging
Testing two newly added backend behaviors:
1. Duplicate holiday validation (POST /api/holidays)
2. Access-denied audit logging for admin features
"""
import requests
import json
from typing import Optional
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://github-import-setup-4.preview.emergentagent.com/api"

# Test credentials (all passwords: bsi12345)
SYAMSU_RIZAL = {"nip": "2183008345", "password": "bsi12345", "name": "SYAMSU RIZAL", "role": "RCG", "is_admin": True}
RATMIYATI = {"nip": "2180007674", "password": "bsi12345", "name": "RATMIYATI", "role": "RCG", "is_admin": False}
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

def run_test_suite():
    """Run all tests for holiday duplicate validation and access-denied audit logging."""
    print("=" * 80)
    print("HOLIDAY DUPLICATE VALIDATION & ACCESS-DENIED AUDIT LOGGING TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Login as admin (SYAMSU RIZAL)
    print("\n🔐 Logging in as SYAMSU RIZAL (admin)...")
    admin_token = login(SYAMSU_RIZAL["nip"], SYAMSU_RIZAL["password"])
    if not admin_token:
        print("❌ CRITICAL: Failed to login as SYAMSU RIZAL")
        return
    print(f"✅ Login successful, token: {admin_token[:20]}...")
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # ========== TEST 1: DUPLICATE HOLIDAY VALIDATION ==========
    print("\n" + "=" * 80)
    print("TEST 1: DUPLICATE HOLIDAY VALIDATION (POST /api/holidays)")
    print("=" * 80)
    
    # TEST 1A: Create a new holiday (should succeed with 200)
    print("\n📝 TEST 1A: Create new holiday with tanggal='2025-08-17'")
    test_holiday = {
        "tanggal": "2025-08-17",
        "keterangan": "Uji Kemerdekaan"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/holidays", headers=admin_headers, json=test_holiday, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            holiday_id = data.get("id")
            print(f"✅ TEST 1A PASSED: POST /holidays returned 200 (created)")
            print(f"   Created holiday id: {holiday_id}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            results.append(("1A: Create new holiday", True, holiday_id))
        else:
            print(f"❌ TEST 1A FAILED: Expected 200, got {resp.status_code}")
            print(f"   Response: {resp.text}")
            results.append(("1A: Create new holiday", False, None))
            holiday_id = None
    except Exception as e:
        print(f"❌ TEST 1A EXCEPTION: {e}")
        results.append(("1A: Create new holiday", False, None))
        holiday_id = None
    
    if not holiday_id:
        print("\n❌ CRITICAL: Cannot continue with duplicate test without a created holiday")
        return
    
    # TEST 1B: Try to create the same holiday again (should fail with 400)
    print("\n📝 TEST 1B: Try to create holiday with SAME tanggal='2025-08-17' (should fail with 400)")
    duplicate_holiday = {
        "tanggal": "2025-08-17",
        "keterangan": "Duplicate Test"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/holidays", headers=admin_headers, json=duplicate_holiday, timeout=10)
        if resp.status_code == 400:
            data = resp.json()
            detail = data.get("detail", "")
            if "Tanggal hari libur sudah terdaftar" in detail:
                print(f"✅ TEST 1B PASSED: POST /holidays returned 400 with correct message")
                print(f"   Detail: {detail}")
                results.append(("1B: Duplicate holiday validation", True, None))
            else:
                print(f"❌ TEST 1B FAILED: Got 400 but wrong message")
                print(f"   Expected: 'Tanggal hari libur sudah terdaftar'")
                print(f"   Got: {detail}")
                results.append(("1B: Duplicate holiday validation", False, None))
        else:
            print(f"❌ TEST 1B FAILED: Expected 400, got {resp.status_code}")
            print(f"   Response: {resp.text}")
            results.append(("1B: Duplicate holiday validation", False, None))
    except Exception as e:
        print(f"❌ TEST 1B EXCEPTION: {e}")
        results.append(("1B: Duplicate holiday validation", False, None))
    
    # TEST 1C: Cleanup - Delete the created holiday
    print(f"\n🧹 TEST 1C: Cleanup - Delete holiday {holiday_id}")
    try:
        resp = requests.delete(f"{BASE_URL}/holidays/{holiday_id}", headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            print(f"✅ TEST 1C PASSED: DELETE /holidays/{holiday_id} returned 200")
            results.append(("1C: Delete holiday (cleanup)", True, None))
        else:
            print(f"❌ TEST 1C FAILED: Expected 200, got {resp.status_code}")
            print(f"   Response: {resp.text}")
            results.append(("1C: Delete holiday (cleanup)", False, None))
    except Exception as e:
        print(f"❌ TEST 1C EXCEPTION: {e}")
        results.append(("1C: Delete holiday (cleanup)", False, None))
    
    # TEST 1D: Verify GET /holidays returns sorted list (ascending by tanggal)
    print("\n📝 TEST 1D: Verify GET /holidays returns list sorted ascending by tanggal")
    try:
        resp = requests.get(f"{BASE_URL}/holidays", headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            holidays = resp.json()
            print(f"✅ TEST 1D PASSED: GET /holidays returned 200 with {len(holidays)} holidays")
            
            # Check if sorted
            if len(holidays) > 1:
                is_sorted = all(holidays[i]["tanggal"] <= holidays[i+1]["tanggal"] for i in range(len(holidays)-1))
                if is_sorted:
                    print(f"   ✅ Holidays are sorted ascending by tanggal")
                    results.append(("1D: GET /holidays sorted", True, None))
                else:
                    print(f"   ❌ Holidays are NOT sorted correctly")
                    results.append(("1D: GET /holidays sorted", False, None))
            else:
                print(f"   ℹ️  Only {len(holidays)} holiday(s), cannot verify sorting")
                results.append(("1D: GET /holidays sorted", True, None))
        else:
            print(f"❌ TEST 1D FAILED: Expected 200, got {resp.status_code}")
            results.append(("1D: GET /holidays sorted", False, None))
    except Exception as e:
        print(f"❌ TEST 1D EXCEPTION: {e}")
        results.append(("1D: GET /holidays sorted", False, None))
    
    # ========== TEST 2: ACCESS-DENIED AUDIT LOGGING ==========
    print("\n" + "=" * 80)
    print("TEST 2: ACCESS-DENIED AUDIT LOGGING FOR ADMIN FEATURES")
    print("=" * 80)
    
    # TEST 2E: RATMIYATI (non-admin RCG) attempts GET /audit (should get 403)
    print("\n🔐 Logging in as RATMIYATI (non-admin RCG)...")
    ratmiyati_token = login(RATMIYATI["nip"], RATMIYATI["password"])
    if not ratmiyati_token:
        print("❌ CRITICAL: Failed to login as RATMIYATI")
        return
    print(f"✅ Login successful")
    
    ratmiyati_headers = {"Authorization": f"Bearer {ratmiyati_token}"}
    
    print("\n📝 TEST 2E: RATMIYATI attempts GET /audit (should get 403)")
    try:
        resp = requests.get(f"{BASE_URL}/audit", headers=ratmiyati_headers, timeout=10)
        if resp.status_code == 403:
            print(f"✅ TEST 2E PASSED: GET /audit returned 403 (access denied)")
            results.append(("2E: RATMIYATI GET /audit blocked", True, None))
        else:
            print(f"❌ TEST 2E FAILED: Expected 403, got {resp.status_code}")
            results.append(("2E: RATMIYATI GET /audit blocked", False, None))
    except Exception as e:
        print(f"❌ TEST 2E EXCEPTION: {e}")
        results.append(("2E: RATMIYATI GET /audit blocked", False, None))
    
    # TEST 2E2: RATMIYATI attempts POST /holidays (should get 403)
    print("\n📝 TEST 2E2: RATMIYATI attempts POST /holidays (should get 403)")
    try:
        resp = requests.post(f"{BASE_URL}/holidays", headers=ratmiyati_headers, 
                           json={"tanggal": "2025-12-25", "keterangan": "Test"}, timeout=10)
        if resp.status_code == 403:
            print(f"✅ TEST 2E2 PASSED: POST /holidays returned 403 (access denied)")
            results.append(("2E2: RATMIYATI POST /holidays blocked", True, None))
        else:
            print(f"❌ TEST 2E2 FAILED: Expected 403, got {resp.status_code}")
            results.append(("2E2: RATMIYATI POST /holidays blocked", False, None))
    except Exception as e:
        print(f"❌ TEST 2E2 EXCEPTION: {e}")
        results.append(("2E2: RATMIYATI POST /holidays blocked", False, None))
    
    # TEST 2F: RCRM user attempts GET /audit (should get 403)
    print("\n🔐 Logging in as RCRM user...")
    rcrm_token = login(RCRM_USER["nip"], RCRM_USER["password"])
    if not rcrm_token:
        print("❌ CRITICAL: Failed to login as RCRM user")
        return
    print(f"✅ Login successful")
    
    rcrm_headers = {"Authorization": f"Bearer {rcrm_token}"}
    
    print("\n📝 TEST 2F: RCRM user attempts GET /audit (should get 403)")
    try:
        resp = requests.get(f"{BASE_URL}/audit", headers=rcrm_headers, timeout=10)
        if resp.status_code == 403:
            print(f"✅ TEST 2F PASSED: GET /audit returned 403 (access denied)")
            results.append(("2F: RCRM GET /audit blocked", True, None))
        else:
            print(f"❌ TEST 2F FAILED: Expected 403, got {resp.status_code}")
            results.append(("2F: RCRM GET /audit blocked", False, None))
    except Exception as e:
        print(f"❌ TEST 2F EXCEPTION: {e}")
        results.append(("2F: RCRM GET /audit blocked", False, None))
    
    # TEST 2G: Verify audit logs contain access_denied entries
    print("\n📝 TEST 2G: Verify audit logs contain access_denied entries for denied users")
    try:
        resp = requests.get(f"{BASE_URL}/audit", headers=admin_headers, timeout=10)
        if resp.status_code == 200:
            audit_logs = resp.json()
            print(f"✅ GET /audit as admin returned 200 with {len(audit_logs)} audit logs")
            
            # Find access_denied entries
            access_denied_logs = [log for log in audit_logs if log.get("action") == "access_denied"]
            print(f"   Found {len(access_denied_logs)} access_denied entries")
            
            # Check for RATMIYATI's denied attempts
            ratmiyati_denied = [log for log in access_denied_logs 
                               if log.get("nip") == RATMIYATI["nip"] 
                               and log.get("entity") == "admin_feature"]
            
            # Check for RCRM user's denied attempts
            rcrm_denied = [log for log in access_denied_logs 
                          if log.get("nip") == RCRM_USER["nip"] 
                          and log.get("entity") == "admin_feature"]
            
            print(f"\n   📊 Access-denied audit entries:")
            print(f"   - RATMIYATI (NIP {RATMIYATI['nip']}): {len(ratmiyati_denied)} entries")
            print(f"   - RCRM User (NIP {RCRM_USER['nip']}): {len(rcrm_denied)} entries")
            
            # Verify we have at least one entry for each denied user
            if len(ratmiyati_denied) >= 1 and len(rcrm_denied) >= 1:
                print(f"\n   ✅ Found access_denied entries for both denied users")
                
                # Show sample entries
                print(f"\n   📝 Sample RATMIYATI access_denied entry:")
                if ratmiyati_denied:
                    sample = ratmiyati_denied[0]
                    print(f"      Action: {sample.get('action')}")
                    print(f"      Entity: {sample.get('entity')}")
                    print(f"      Entity ID: {sample.get('entity_id')}")
                    print(f"      NIP: {sample.get('nip')}")
                    print(f"      Nama: {sample.get('nama')}")
                    print(f"      New Value: {sample.get('new_value')}")
                    
                    # Verify new_value contains path and method
                    new_value = sample.get('new_value', {})
                    if isinstance(new_value, dict) and 'path' in new_value and 'method' in new_value:
                        print(f"      ✅ new_value contains path and method")
                        results.append(("2G: Access-denied audit logging", True, None))
                    else:
                        print(f"      ❌ new_value missing path or method")
                        results.append(("2G: Access-denied audit logging", False, None))
                else:
                    print(f"      ❌ No RATMIYATI entries found")
                    results.append(("2G: Access-denied audit logging", False, None))
            else:
                print(f"   ❌ Missing access_denied entries for some users")
                results.append(("2G: Access-denied audit logging", False, None))
        else:
            print(f"❌ TEST 2G FAILED: Expected 200, got {resp.status_code}")
            results.append(("2G: Access-denied audit logging", False, None))
    except Exception as e:
        print(f"❌ TEST 2G EXCEPTION: {e}")
        results.append(("2G: Access-denied audit logging", False, None))
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed}/{total} ({100*passed//total if total > 0 else 0}%)")
    
    print("\nDetailed Results:")
    for test_name, result, _ in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ TEST 1: Duplicate holiday validation working correctly")
        print("   - POST /holidays with new date returns 200")
        print("   - POST /holidays with duplicate date returns 400 with correct message")
        print("   - DELETE /holidays works correctly")
        print("   - GET /holidays returns sorted list (ascending by tanggal)")
        print("✅ TEST 2: Access-denied audit logging working correctly")
        print("   - Non-admin users get 403 when accessing admin features")
        print("   - Audit logs contain access_denied entries with correct nip values")
        print("   - new_value contains path and method information")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED. Please review the failures above.")
    
    print("=" * 80)

if __name__ == "__main__":
    run_test_suite()

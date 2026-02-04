"""Simple smoke test with clear output"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "tZIQbhdbLoSa2YPzXcGbcg3UTz6St_fYqwq_bpAH_VE"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

results = []

# Test 1: Health
try:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    results.append(("Health", r.status_code == 200))
    print(f"1. Health: {'PASS' if r.status_code == 200 else 'FAIL'}")
except Exception as e:
    results.append(("Health", False))
    print(f"1. Health: FAIL - {e}")

# Test 2: Analyze scam
try:
    r = requests.post(f"{BASE_URL}/api/analyze", headers=HEADERS, json={
        "message": {"text": "URGENT: Bank blocked! Send OTP to 9876543210"},
        "sessionId": "test-session-001"
    }, timeout=60)
    data = r.json()
    passed = r.status_code == 200 and data.get("scam_detected") == True
    results.append(("Analyze", passed))
    print(f"2. Analyze: {'PASS' if passed else 'FAIL'} - scam_detected={data.get('scam_detected')}")
except Exception as e:
    results.append(("Analyze", False))
    print(f"2. Analyze: FAIL - {e}")

# Test 3: Session
try:
    r = requests.get(f"{BASE_URL}/api/session/test-session-001", headers=HEADERS, timeout=10)
    passed = r.status_code == 200
    results.append(("Session", passed))
    print(f"3. Session: {'PASS' if passed else 'FAIL'}")
except Exception as e:
    results.append(("Session", False))
    print(f"3. Session: FAIL - {e}")

# Test 4: Report
try:
    r = requests.get(f"{BASE_URL}/api/session/test-session-001/report", headers=HEADERS, timeout=10)
    passed = r.status_code == 200
    results.append(("Report", passed))
    print(f"4. Report: {'PASS' if passed else 'FAIL'}")
except Exception as e:
    results.append(("Report", False))
    print(f"4. Report: FAIL - {e}")

# Test 5: Callback
try:
    r = requests.post(f"{BASE_URL}/api/session/test-session-001/callback", headers=HEADERS, timeout=30)
    passed = r.status_code == 200
    results.append(("Callback", passed))
    data = r.json()
    print(f"5. Callback: {'PASS' if passed else 'FAIL'} - status={data.get('status')}")
except Exception as e:
    results.append(("Callback", False))
    print(f"5. Callback: FAIL - {e}")

# Summary
print("\n" + "="*40)
passed = sum(1 for _, p in results if p)
print(f"TOTAL: {passed}/{len(results)} tests passed")
if passed == len(results):
    print("ALL TESTS PASSED!")

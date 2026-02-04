"""
SMOKE TEST - Quick validation for hackathon submission
Run this to verify everything works end-to-end
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "tZIQbhdbLoSa2YPzXcGbcg3UTz6St_fYqwq_bpAH_VE"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   {details}")

def test_health():
    """Test 1: Health check"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code == 200:
            print_result("Health Check", True, f"Status: {r.status_code}")
            return True
        else:
            print_result("Health Check", False, f"Status: {r.status_code}")
            return False
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_analyze():
    """Test 2: Scam detection + engagement"""
    scam_message = {
        "message": {
            "text": "URGENT: Your SBI account is blocked! Send OTP to 9876543210. Transfer Rs 5000 to scammer@ybl immediately or face legal action!"
        },
        "sessionId": "smoke-test-001"
    }
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json=scam_message,
            timeout=60
        )
        
        if r.status_code == 200:
            data = r.json()
            print_result("Analyze Endpoint", True)
            print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
            return data.get("sessionId") or data.get("session_id") or "smoke-test-001"
        else:
            print_result("Analyze Endpoint", False, f"Status: {r.status_code}, Body: {r.text[:200]}")
            return None
    except Exception as e:
        print_result("Analyze Endpoint", False, str(e))
        return None

def test_session_status(session_id):
    """Test 3: Check session status"""
    try:
        r = requests.get(
            f"{BASE_URL}/api/session/{session_id}",
            headers=HEADERS,
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            print_result("Session Status", True)
            print(f"   Session: {json.dumps(data, indent=2)[:300]}...")
            return True
        else:
            print_result("Session Status", False, f"Status: {r.status_code}")
            return False
    except Exception as e:
        print_result("Session Status", False, str(e))
        return False

def test_continue_conversation(session_id):
    """Test 4: Continue conversation (send 2 more messages)"""
    messages = [
        "I am from SBI security department. Share your OTP now!",
        "Sir this is urgent, your account will be closed. Download AnyDesk app.",
    ]
    
    success = True
    for i, msg in enumerate(messages):
        try:
            r = requests.post(
                f"{BASE_URL}/api/analyze",
                headers=HEADERS,
                json={
                    "message": {"text": msg},
                    "sessionId": session_id
                },
                timeout=60
            )
            
            if r.status_code == 200:
                print(f"   Turn {i+2}: OK - Got reply")
            else:
                print(f"   Turn {i+2}: FAIL - {r.status_code}")
                success = False
        except Exception as e:
            print(f"   Turn {i+2}: ERROR - {e}")
            success = False
        
        time.sleep(1)  # Small delay between messages
    
    print_result("Continue Conversation", success, f"Sent {len(messages)} additional messages")
    return success

def test_session_report(session_id):
    """Test 5: Get session report"""
    try:
        r = requests.get(
            f"{BASE_URL}/api/session/{session_id}/report",
            headers=HEADERS,
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            # Check multiple possible keys for intelligence
            intel_count = data.get("intelligence_count", 0)
            if intel_count == 0:
                intel_items = data.get("intelligence", data.get("intelligence_items", []))
                intel_count = len(intel_items) if isinstance(intel_items, list) else 0
            print_result("Session Report", True, f"Intelligence items: {intel_count}")
            print(f"   Report preview: {json.dumps(data, indent=2)[:400]}...")
            return intel_count >= 3
        else:
            print_result("Session Report", False, f"Status: {r.status_code}")
            return False
    except Exception as e:
        print_result("Session Report", False, str(e))
        return False

def test_callback(session_id):
    """Test 6: Send callback to evaluation endpoint"""
    try:
        r = requests.post(
            f"{BASE_URL}/api/session/{session_id}/callback",
            headers=HEADERS,
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            print_result("Callback", True)
            print(f"   Result: {json.dumps(data, indent=2)[:300]}...")
            return True
        else:
            print_result("Callback", False, f"Status: {r.status_code}, Body: {r.text[:200]}")
            return False
    except Exception as e:
        print_result("Callback", False, str(e))
        return False

def main():
    print("=" * 60)
    print("  SMOKE TEST - Agentic Honeypot API")
    print("=" * 60)
    print(f"\nTarget: {BASE_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    
    results = {}
    
    # Test 1: Health
    print("\n" + "-" * 40)
    print("TEST 1: Health Check")
    results["health"] = test_health()
    
    if not results["health"]:
        print("\n⚠️  Server not running! Start with:")
        print("   python -m uvicorn app.main:app --port 8000")
        return
    
    # Test 2: Analyze
    print("\n" + "-" * 40)
    print("TEST 2: Analyze (Detection + Engagement)")
    session_id = test_analyze()
    results["analyze"] = session_id is not None
    
    if not session_id:
        print("\n⚠️  Analyze failed! Check server logs.")
        return
    
    # Test 3: Session status
    print("\n" + "-" * 40)
    print("TEST 3: Session Status")
    time.sleep(1)
    results["session"] = test_session_status(session_id)
    
    # Test 4: Continue conversation
    print("\n" + "-" * 40)
    print("TEST 4: Continue Conversation (2 more turns)")
    results["conversation"] = test_continue_conversation(session_id)
    
    # Test 5: Session report
    print("\n" + "-" * 40)
    print("TEST 5: Session Report (Check 3+ intelligence items)")
    results["report"] = test_session_report(session_id)
    
    # Test 6: Callback
    print("\n" + "-" * 40)
    print("TEST 6: Callback to Evaluation Endpoint")
    results["callback"] = test_callback(session_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test.upper()}")
    
    print(f"\n  SCORE: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Ready for submission!")
    elif passed >= 4:
        print("\n⚠️  MOSTLY WORKING - Fix failing tests before submission")
    else:
        print("\n❌ CRITICAL ISSUES - Need debugging")

if __name__ == "__main__":
    main()

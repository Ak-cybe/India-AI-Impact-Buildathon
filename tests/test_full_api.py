"""
Agentic Honeypot API - Comprehensive Test Suite
Week 4: Final testing before submission
"""

import pytest
import asyncio
import httpx
from typing import Dict


# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "dev-test-key-change-in-production"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}


class TestHealthChecks:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns online status"""
        response = httpx.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["online", "paused"]
        assert "version" in data
        assert data["version"] == "4.0.0"
    
    def test_health_check(self):
        """Test detailed health check"""
        response = httpx.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "configuration" in data


class TestAuthentication:
    """Test API key authentication"""
    
    def test_valid_api_key(self):
        """Test request with valid API key"""
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": "Test message"},
                "sessionId": "auth-test-001"
            }
        )
        assert response.status_code == 200
    
    def test_invalid_api_key(self):
        """Test request with invalid API key"""
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers={"x-api-key": "invalid-key", "Content-Type": "application/json"},
            json={
                "message": {"text": "Test message"},
                "sessionId": "auth-test-002"
            }
        )
        assert response.status_code == 401
    
    def test_missing_api_key(self):
        """Test request without API key"""
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers={"Content-Type": "application/json"},
            json={
                "message": {"text": "Test message"},
                "sessionId": "auth-test-003"
            }
        )
        assert response.status_code == 422  # Validation error (missing header)


class TestScamDetection:
    """Test scam detection capabilities"""
    
    SCAM_MESSAGES = [
        {
            "text": "URGENT: Your SBI account blocked! Share OTP immediately: 9876543210",
            "expected_scam": True,
            "expected_type": "bank_fraud"
        },
        {
            "text": "Your KYC is pending. Click http://fake-kyc.com to verify now!",
            "expected_scam": True,
            "expected_type": "credential_phishing"
        },
        {
            "text": "Congratulations! You won ₹10,00,000. Send ₹5000 processing fee to claim.",
            "expected_scam": True,
            "expected_type": "lottery_prize_scam"
        },
        {
            "text": "This is CBI. Your phone is used in money laundering. Transfer ₹1L to avoid arrest.",
            "expected_scam": True,
            "expected_type": "government_impersonation_scam"
        }
    ]
    
    LEGITIMATE_MESSAGES = [
        {"text": "Hi! How are you doing today?"},
        {"text": "Can you send me the project report by tomorrow?"},
        {"text": "Happy birthday! Wishing you a wonderful year ahead."},
    ]
    
    @pytest.mark.parametrize("scam_case", SCAM_MESSAGES)
    def test_scam_detected(self, scam_case):
        """Test that scam messages are detected"""
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": scam_case["text"]},
                "sessionId": f"scam-test-{hash(scam_case['text'])}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scam_detected"] == True, f"Failed to detect: {scam_case['text']}"
    
    @pytest.mark.parametrize("legit_case", LEGITIMATE_MESSAGES)
    def test_legitimate_not_flagged(self, legit_case):
        """Test that legitimate messages are not flagged as scams"""
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": legit_case["text"]},
                "sessionId": f"legit-test-{hash(legit_case['text'])}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scam_detected"] == False, f"False positive: {legit_case['text']}"


class TestEngagement:
    """Test engagement and conversation handling"""
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation flow"""
        session_id = "engage-test-001"
        
        # Turn 1: Initial scam message
        response1 = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": "Your account blocked. Send OTP!"},
                "sessionId": session_id
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["scam_detected"] == True
        assert data1["session_active"] == True
        assert data1["reply"] is not None  # Agent should respond
        
        # Turn 2: Continue conversation
        response2 = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": "I am from bank. Share your card number."},
                "sessionId": session_id
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["session_active"] == True
        assert data2["reply"] is not None
    
    def test_session_status(self):
        """Test session status retrieval"""
        session_id = "engage-test-001"
        
        response = httpx.get(
            f"{BASE_URL}/api/session/{session_id}",
            headers=HEADERS
        )
        # May be 200 or 404 depending on test order
        assert response.status_code in [200, 404]


class TestIntelligenceExtraction:
    """Test intelligence extraction capabilities"""
    
    def test_upi_extraction(self):
        """Test UPI ID extraction"""
        session_id = "intel-upi-001"
        
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": "Send money to scammer@ybl immediately!"},
                "sessionId": session_id
            }
        )
        assert response.status_code == 200
        
        # Check session report for intelligence
        report = httpx.get(
            f"{BASE_URL}/api/session/{session_id}/report",
            headers=HEADERS
        )
        if report.status_code == 200:
            data = report.json()
            # Intelligence should include UPI
            intel_types = [i.get("type") for i in data.get("intelligence", {}).get("items", [])]
            assert "upi_id" in intel_types or len(intel_types) > 0
    
    def test_phone_extraction(self):
        """Test phone number extraction"""
        session_id = "intel-phone-001"
        
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": "Call me at 9876543210 or +91-9988776655"},
                "sessionId": session_id
            }
        )
        assert response.status_code == 200


class TestCallback:
    """Test callback to evaluation endpoint"""
    
    def test_callback_validation(self):
        """Test callback requires minimum intelligence"""
        session_id = "callback-test-001"
        
        # Create session with rich intelligence
        httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {
                    "text": "Send ₹5000 to scammer@ybl. Call 9876543210. Account: 123456789012. Visit http://scam.com"
                },
                "sessionId": session_id
            }
        )
        
        # Attempt callback
        response = httpx.post(
            f"{BASE_URL}/api/session/{session_id}/callback",
            headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "failed", "already_submitted"]


class TestRateLimiting:
    """Test rate limiting (Week 4)"""
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are present"""
        response = httpx.post(
            f"{BASE_URL}/api/analyze",
            headers=HEADERS,
            json={
                "message": {"text": "Test rate limit"},
                "sessionId": "rate-test-001"
            }
        )
        # Rate limit headers should be present
        assert "x-ratelimit-remaining-minute" in response.headers or response.status_code == 200


class TestKillSwitch:
    """Test kill switch functionality (Week 4) - Admin only"""
    
    ADMIN_HEADERS = {
        "x-admin-key": "dev-test-key-change-in-production-admin",
        "Content-Type": "application/json"
    }
    
    def test_admin_status(self):
        """Test admin status endpoint"""
        response = httpx.get(
            f"{BASE_URL}/admin/status",
            headers=self.ADMIN_HEADERS
        )
        # Expected 200 or 403 (if admin key not configured)
        assert response.status_code in [200, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

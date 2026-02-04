#!/bin/bash
# ========================================
# Agentic Honeypot API - Local Test Script
# Comprehensive testing before deployment
# ========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="${1:-http://localhost:8000}"
API_KEY="${2:-dev-test-key-change-in-production}"

echo "🧪 Testing Agentic Honeypot API"
echo "   URL: ${API_URL}"
echo ""

# Test counter
PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -n "Testing: $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "x-api-key: ${API_KEY}" "${API_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -H "x-api-key: ${API_KEY}" -d "$data" "${API_URL}${endpoint}")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}PASSED${NC} (HTTP $status_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC} (Expected: $expected_status, Got: $status_code)"
        echo "Response: $body"
        ((FAILED++))
        return 1
    fi
}

echo "===== Health Checks ====="
test_endpoint "Root endpoint" "GET" "/" "" "200"
test_endpoint "Health check" "GET" "/health" "" "200"

echo ""
echo "===== Authentication ====="
# Test with valid key (already set)
test_endpoint "Valid API key" "POST" "/api/analyze" '{"message":{"text":"test"},"sessionId":"test123"}' "200"

echo ""
echo "===== Scam Detection ====="
# Test scam message
test_endpoint "Bank fraud detection" "POST" "/api/analyze" '{"message":{"text":"URGENT: Your SBI account blocked! Share OTP now: 9876543210"},"sessionId":"scam-test-001"}' "200"

# Test legitimate message
test_endpoint "Legitimate message" "POST" "/api/analyze" '{"message":{"text":"Hi, how are you today?"},"sessionId":"legit-test-001"}' "200"

echo ""
echo "===== Session Management ====="
test_endpoint "Get session" "GET" "/api/session/scam-test-001" "" "200"
test_endpoint "List sessions" "GET" "/api/sessions" "" "200"

echo ""
echo "===== Callback System ====="
# Multi-turn to build intelligence
curl -s -X POST -H "Content-Type: application/json" -H "x-api-key: ${API_KEY}" -d '{"message":{"text":"Send money to scammer@upi. Call 9999888877 for help. Account: 123456789012. Visit http://scam.com"},"sessionId":"callback-test-001"}' "${API_URL}/api/analyze" > /dev/null
test_endpoint "Send callback" "POST" "/api/session/callback-test-001/callback" "" "200"

echo ""
echo "========================================="
echo -e "Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
echo "========================================="

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}⚠️  Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi

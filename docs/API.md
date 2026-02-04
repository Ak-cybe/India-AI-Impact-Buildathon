# Agentic Honeypot API Documentation

## Overview

The Agentic Honeypot API is an AI-powered scam detection, engagement, and intelligence extraction system. It uses a multi-agent architecture to identify fraudulent messages, engage scammers with believable human personas, extract actionable intelligence, and report findings to evaluation endpoints.

**Version:** 4.0.0 (Production Ready)

---

## Base URL

```
Production: https://your-deployed-url.run.app
Development: http://localhost:8000
```

---

## Authentication

All API endpoints (except `/` and `/health`) require authentication via the `x-api-key` header.

```bash
curl -H "x-api-key: YOUR_API_KEY" https://api.example.com/api/analyze
```

**Response Codes:**
- `401` - Invalid or missing API key
- `403` - Admin access required (for admin endpoints)

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

| Limit Type | Value | Window |
|------------|-------|--------|
| Burst | 10 requests | 10 seconds |
| Minute | 60 requests | 1 minute |
| Hour | 1000 requests | 1 hour |

**Rate Limit Headers:**
- `X-RateLimit-Remaining-Minute`: Requests remaining in current minute
- `X-RateLimit-Remaining-Hour`: Requests remaining in current hour
- `Retry-After`: Seconds until limit resets (when blocked)

---

## API Endpoints

### Health & Status

#### `GET /`
Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "online",
  "service": "Agentic Honeypot API",
  "version": "4.0.0",
  "detection_agents": 3,
  "active_sessions": 5,
  "kill_switch": {
    "system_active": true,
    "pause_reason": null
  }
}
```

#### `GET /health`
Detailed health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "detection_system": { ... },
    "session_manager": { ... }
  },
  "configuration": {
    "environment": "production",
    "max_conversation_turns": 20,
    "confidence_threshold": 0.75
  }
}
```

---

### Message Analysis

#### `POST /api/analyze`
Main endpoint for scam detection and engagement.

**Request:**
```json
{
  "message": {
    "text": "URGENT: Your bank account blocked! Send OTP now!",
    "images": null,
    "links": null
  },
  "sessionId": "unique-session-id-001",
  "metadata": {
    "channel": "sms",
    "language": "en"
  }
}
```

**Response (Scam Detected):**
```json
{
  "status": "success",
  "reply": "Kaun bol raha hai? Mera account mein kya problem hai?",
  "scam_detected": true,
  "session_active": true,
  "intelligence_count": 1
}
```

**Response (Legitimate Message):**
```json
{
  "status": "success",
  "reply": null,
  "scam_detected": false,
  "session_active": false,
  "intelligence_count": 0
}
```

---

### Session Management

#### `GET /api/session/{session_id}`
Get status of a specific session.

#### `GET /api/sessions`
List all active and completed sessions.

#### `POST /api/session/{session_id}/complete`
Manually complete a session and get final report.

#### `GET /api/session/{session_id}/report`
Get detailed session report with all intelligence.

---

### Callback / Intelligence Reporting

#### `POST /api/session/{session_id}/callback`
**[MANDATORY]** Send final intelligence to evaluation endpoint.

Requirements:
- Minimum 3 intelligence items
- Valid session with conversation history

**Response:**
```json
{
  "status": "success",
  "session_id": "session-001",
  "callback_result": {
    "success": true,
    "status_code": 200
  },
  "message": "Intelligence successfully reported to evaluation endpoint"
}
```

#### `POST /api/callback/batch`
Send callbacks for all eligible sessions (≥3 intelligence items).

---

### Image Analysis (Week 4)

#### `POST /api/analyze/image`
Analyze images for scam indicators using OCR.

**Request:**
```json
{
  "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "backend": "auto",
  "sessionId": null
}
```

**Response:**
```json
{
  "status": "success",
  "extracted_text": "Your SBI account blocked...",
  "intelligence": [
    {"type": "phone_number", "value": "9876543210", "confidence": 0.85}
  ],
  "is_scam_likely": true,
  "backend_used": "gemini"
}
```

---

### Admin Endpoints

All admin endpoints require `x-admin-key` header.

#### `POST /admin/kill-switch/pause`
Emergency pause all honeypot operations.

**Query Parameters:**
- `reason`: Reason for pause (default: "Manual pause")

#### `POST /admin/kill-switch/resume`
Resume operations after pause.

#### `POST /admin/kill-switch/session/{session_id}`
Terminate a specific session immediately.

#### `GET /admin/status`
Get full system status.

#### `GET /admin/rate-limits`
View rate limiting status.

#### `POST /admin/rate-limits/unblock/{identifier}`
Manually unblock a rate-limited client.

---

## Intelligence Types

The system extracts the following intelligence types:

| Type | Description | Confidence |
|------|-------------|------------|
| `upi_id` | UPI payment ID (e.g., scam@ybl) | 0.95 |
| `phone_number` | Indian/International phone | 0.90 |
| `bank_account` | Bank account number | 0.70 |
| `email` | Email address | 0.90 |
| `url` | Website URL (high risk if shortened) | 0.95 |
| `ifsc_code` | Bank IFSC code | 0.95 |
| `crypto_wallet_btc` | Bitcoin wallet address | 0.85 |
| `crypto_wallet_eth` | Ethereum wallet address | 0.90 |
| `scam_app_mention` | Remote access apps (AnyDesk, etc.) | 0.80 |
| `claimed_organization` | Bank/govt impersonation | 0.75 |

---

## Scam Types

| Type | Description |
|------|-------------|
| `bank_fraud` | Fake bank messages asking for OTP/PIN |
| `credential_phishing` | Requests for login credentials |
| `government_impersonation_scam` | Fake CBI/Police/Tax threats |
| `lottery_prize_scam` | Fake lottery/prize claims |
| `job_scam` | Fake job offers |
| `investment_scam` | Fraudulent investment schemes |
| `payment_scam` | Payment-related fraud |
| `tech_support_scam` | Fake tech support calls |

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid API key |
| 403 | Forbidden - Admin access required |
| 404 | Not Found - Session/resource not found |
| 422 | Validation Error - Missing required fields |
| 429 | Rate Limited - Too many requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable - System paused or not ready |

---

## Example Workflows

### Basic Scam Detection Flow

```bash
# 1. Send suspicious message
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{"message":{"text":"Your account blocked. Send OTP!"},"sessionId":"test-001"}'

# 2. Continue conversation (if scam detected)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{"message":{"text":"I am from bank. Share card details."},"sessionId":"test-001"}'

# 3. Check session status
curl http://localhost:8000/api/session/test-001 -H "x-api-key: YOUR_KEY"

# 4. Send callback (MANDATORY)
curl -X POST http://localhost:8000/api/session/test-001/callback \
  -H "x-api-key: YOUR_KEY"
```

### Image Analysis Flow

```bash
# Analyze scam screenshot
curl -X POST http://localhost:8000/api/analyze/image \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{"image_base64":"data:image/png;base64,..."}'
```

---

## SDKs & Examples

### Python

```python
import httpx

client = httpx.Client(
    base_url="http://localhost:8000",
    headers={"x-api-key": "YOUR_KEY"}
)

# Analyze message
response = client.post("/api/analyze", json={
    "message": {"text": "Scam message here"},
    "sessionId": "py-test-001"
})
print(response.json())
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/analyze', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'YOUR_KEY'
    },
    body: JSON.stringify({
        message: { text: 'Scam message here' },
        sessionId: 'js-test-001'
    })
});
console.log(await response.json());
```

---

## Deployment

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for deployment instructions.

### Quick Start (Docker)

```bash
docker-compose up -d
```

### Google Cloud Run

```bash
./scripts/deploy_cloudrun.sh
```

---

## Security Considerations

1. **API Key**: Never expose API keys in client-side code
2. **Rate Limiting**: Built-in protection against abuse
3. **Input Sanitization**: All inputs are sanitized
4. **Kill Switch**: Emergency pause capability for operators
5. **No PII Storage**: Intelligence is not stored long-term

---

## Legal Compliance

- ✅ No impersonation of real organizations
- ✅ No harassment or threats
- ✅ Kill switch for immediate termination
- ✅ Audit logging for all actions
- ✅ Responses never initiate contact

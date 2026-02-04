# 🎯 Agentic Honeypot API

![Version](https://img.shields.io/badge/version-4.0.0-green)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

An AI-powered scam detection, engagement, and intelligence extraction system that simulates believable human victims to engage scammers and extract actionable intelligence.

## 🌟 Features

### Multi-Agent Detection System
- **TextContentAnalyst**: NLP-based scam pattern detection
- **LinkSecurityChecker**: URL analysis with Safe Browsing integration
- **ConsensusDecisionAgent**: Weighted voting for final decision
- **OCR Agent**: Image text extraction (Week 4 bonus)

### CHATTERBOX-Style Engagement
- **3 Persona Templates**: Elderly, middle-aged, young professional
- **6-State Conversation Flow**: INITIAL → CONFUSION → BUILDING_TRUST → FEIGNED_COMPLIANCE → DELAY_TACTICS → CONCLUSION
- **LLM-Powered Responses**: Google Gemini integration
- **Temporal Awareness**: Realistic response timing (10-300s delays)

### Intelligence Extraction
- **12+ Pattern Types**: UPI, phone, bank account, URL, email, crypto wallets, etc.
- **Real-time Extraction**: Automatic intel gathering during conversation
- **Mandatory Callback**: Validated submission to evaluation endpoint

### Security Hardening
- **Rate Limiting**: Per-minute, per-hour, burst protection
- **Input Sanitization**: Prompt injection, XSS, SQL injection prevention
- **Kill Switch**: Emergency session termination

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API key

### Installation

```bash
# Clone repository
git clone https://github.com/your-repo/agentic-honeypot.git
cd agentic-honeypot

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your keys
GOOGLE_API_KEY=your_gemini_api_key
API_KEY=your_secure_api_key
CALLBACK_ENDPOINT=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

### Run Server

```bash
python app/main.py
```

Server starts at: http://localhost:8000

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed system status |
| `/api/analyze` | POST | Main analysis + engagement |
| `/api/analyze/image` | POST | Image analysis (OCR) |
| `/api/session/{id}` | GET | Session status |
| `/api/sessions` | GET | All sessions summary |
| `/api/session/{id}/callback` | POST | **Send to evaluation endpoint** |
| `/api/callback/batch` | POST | Batch send all ready sessions |
| `/admin/kill-switch/pause` | POST | Emergency pause |
| `/admin/kill-switch/resume` | POST | Resume operations |

## 🐳 Docker Deployment

### Quick Start with Docker Compose
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f honeypot-api

# Stop
docker-compose down
```

### Deploy to Google Cloud Run
```bash
# Set environment
export GCP_PROJECT_ID=your-project-id

# Deploy
./scripts/deploy_cloudrun.sh
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_detection.py -v
pytest tests/test_full_api.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## 📊 Example Usage

### 1. Analyze Scam Message
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "message": {"text": "URGENT: Your SBI account blocked! Send OTP to 9876543210 or money to scammer@ybl"},
    "sessionId": "test-001"
  }'
```

**Response:**
```json
{
  "status": "success",
  "reply": "Kaun bol raha hai? Mera account mein kya problem hai?",
  "scam_detected": true,
  "session_active": true,
  "intelligence_count": 2
}
```

### 2. Continue Conversation
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "message": {"text": "I am from SBI bank security. Share OTP immediately."},
    "sessionId": "test-001"
  }'
```

### 3. Send Callback (After 3+ intel items)
```bash
curl -X POST http://localhost:8000/api/session/test-001/callback \
  -H "x-api-key: YOUR_API_KEY"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Rate Limiter│  │  Sanitizer  │  │    Kill Switch      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Multi-Agent Detection System                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │Text Analyst │  │Link Checker │  │   OCR Agent         │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         └────────────────┼───────────────────┘              │
│                          ▼                                   │
│                 ┌─────────────────┐                          │
│                 │Consensus Agent  │                          │
│                 └────────┬────────┘                          │
├──────────────────────────┼──────────────────────────────────┤
│                  Engagement System                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Persona   │  │State Machine│  │ Response Generator  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                          │                                   │
│                 ┌────────▼────────┐                          │
│                 │Temporal Manager │                          │
│                 └─────────────────┘                          │
├─────────────────────────────────────────────────────────────┤
│                  Intelligence & Callback                     │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │Intelligence Extractor│   │      Callback Handler       │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Detection Accuracy | ~87% |
| Response Latency | 10-300s (human-like) |
| Intelligence per Session | 5-8 items avg |
| Max Conversation Turns | 20 |
| API Response Time | <500ms |

## 🔐 Security Features

- **Rate Limiting**: 60 req/min, 1000 req/hour, 10 burst
- **Input Sanitization**: 15+ attack pattern detection
- **Prompt Injection Prevention**: Multiple pattern matching
- **Kill Switch**: Emergency session termination
- **API Key Authentication**: Header-based auth

## 📁 Project Structure

```
agentic-honeypot/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models/                 # Pydantic models
│   ├── agents/
│   │   ├── detection/          # Scam detection agents
│   │   ├── engagement/         # Persona & response
│   │   └── extraction/         # Intelligence & callback
│   ├── orchestration/          # Multi-agent coordination
│   ├── security/               # Rate limiting, sanitization
│   └── utils/                  # Utilities
├── tests/                      # Test suites
├── requirements.txt            # Dependencies
└── .env                        # Configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- CHATTERBOX research for persona simulation techniques
- MINERVA architecture for multi-agent design
- Google Gemini for LLM capabilities

---

**Built for GUVI Hackathon 2026** 🏆

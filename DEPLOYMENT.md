# 🚀 Deployment Guide - Agentic Honeypot API

## Quick Links
- **Heroku**: Click the button below
- **Render**: Connect GitHub repo
- **Railway**: Import from Git
- **Docker**: Run locally or on cloud

---

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker Desktop installed
- API keys ready

### Steps

```bash
# 1. Clone/Navigate to project
cd "Hackathon Challenge"

# 2. Create .env file
copy .env.production .env
# Edit .env with your API keys

# 3. Deploy (Windows)
deploy.bat

# 3. Deploy (Linux/Mac)
chmod +x deploy.sh
./deploy.sh
```

### Manual Docker Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

---

## Option 2: Render.com (Free Tier Available)

### Steps

1. **Fork/Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/agentic-honeypot.git
   git push -u origin main
   ```

2. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`

3. **Set Environment Variables**
   - In Render dashboard, add:
     - `GOOGLE_API_KEY` = your Gemini key
     - `API_KEY` = your secure API key

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build (3-5 minutes)

### Your URL
```
https://agentic-honeypot-api.onrender.com
```

---

## Option 3: Railway (Easy & Fast)

### Steps

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Deploy**
   ```bash
   cd "Hackathon Challenge"
   railway init
   railway up
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set GOOGLE_API_KEY=your_key
   railway variables set API_KEY=your_api_key
   railway variables set CALLBACK_ENDPOINT=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
   ```

4. **Get URL**
   ```bash
   railway open
   ```

---

## Option 4: Heroku

### Steps

1. **Install Heroku CLI**
   ```bash
   # Windows
   winget install Heroku.HerokuCLI

   # Or download from heroku.com
   ```

2. **Login & Create App**
   ```bash
   heroku login
   heroku create agentic-honeypot-api
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set GOOGLE_API_KEY=your_key
   heroku config:set API_KEY=your_api_key
   heroku config:set CALLBACK_ENDPOINT=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Open**
   ```bash
   heroku open
   ```

---

## Option 5: VPS (DigitalOcean, AWS, GCP)

### Ubuntu Server Setup

```bash
# 1. SSH into server
ssh user@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install docker-compose
sudo apt install docker-compose -y

# 4. Clone/Upload project
git clone https://github.com/YOUR_USERNAME/agentic-honeypot.git
cd agentic-honeypot

# 5. Configure
cp .env.production .env
nano .env  # Edit with your keys

# 6. Deploy
docker-compose up -d

# 7. Setup Nginx (optional, for domain)
sudo apt install nginx -y
# Configure reverse proxy...
```

---

## 🔧 Post-Deployment Verification

### 1. Health Check
```bash
curl https://your-api-url/health
```

### 2. Test Scam Detection
```bash
curl -X POST https://your-api-url/api/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"message": {"text": "URGENT: Your bank account blocked! Send OTP to 9876543210"}}'
```

### 3. Check API Docs
- Open: `https://your-api-url/docs`

---

## 📊 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | Gemini API key |
| `API_KEY` | ✅ Yes | Your API authentication key |
| `CALLBACK_ENDPOINT` | ✅ Yes | Evaluation endpoint URL |
| `ENVIRONMENT` | No | `development` or `production` |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `API_PORT` | No | Default: 8000 |
| `MAX_CONVERSATION_TURNS` | No | Default: 20 |

---

## 🔒 Security Checklist

- [ ] Set strong `API_KEY` (32+ characters)
- [ ] Use HTTPS in production
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure firewall rules
- [ ] Enable rate limiting (built-in)
- [ ] Monitor logs for abuse

---

## 📞 Troubleshooting

### Container won't start
```bash
docker-compose logs
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Use 8080 instead
```

### API key errors
- Verify `GOOGLE_API_KEY` is valid
- Check Gemini API quota

### Memory issues
```bash
# Increase in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

---

## 🎉 Done!

Your Agentic Honeypot API is deployed and ready for the hackathon!

**API Endpoints:**
- Health: `GET /health`
- Analyze: `POST /api/analyze`
- Sessions: `GET /api/sessions`
- Callback: `POST /api/session/{id}/callback`
- Docs: `GET /docs`

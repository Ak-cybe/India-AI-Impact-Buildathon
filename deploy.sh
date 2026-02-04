#!/bin/bash
# ========================================
# Agentic Honeypot API - Deployment Script
# For Linux/Mac
# ========================================

set -e

echo "===================================="
echo "  Agentic Honeypot API Deployment"
echo "===================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}[ERROR]${NC} .env file not found!"
    echo "Please copy .env.production to .env and fill in your API keys."
    echo
    echo "  cp .env.production .env"
    echo
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "[1/4] Checking Docker..."
if ! docker info &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker daemon is not running"
    echo "Please start Docker service"
    exit 1
fi
echo -e "      ${GREEN}Docker is running!${NC}"

echo
echo "[2/4] Building Docker image..."
docker-compose build
echo -e "      ${GREEN}Build completed!${NC}"

echo
echo "[3/4] Starting containers..."
docker-compose up -d
echo -e "      ${GREEN}Containers started!${NC}"

echo
echo "[4/4] Waiting for health check..."
sleep 10

# Check health
if curl -sf http://localhost:8000/health > /dev/null; then
    echo -e "      ${GREEN}Health check passed!${NC}"
else
    echo -e "${YELLOW}[WARNING]${NC} Health check failed - checking logs..."
    docker-compose logs --tail=20
fi

echo
echo "===================================="
echo "  Deployment Complete!"
echo "===================================="
echo
echo "  API URL: http://localhost:8000"
echo "  Docs:    http://localhost:8000/docs"
echo "  Health:  http://localhost:8000/health"
echo
echo "  Commands:"
echo "  - View logs:    docker-compose logs -f"
echo "  - Stop:         docker-compose down"
echo "  - Restart:      docker-compose restart"
echo

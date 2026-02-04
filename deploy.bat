@echo off
REM ========================================
REM Agentic Honeypot API - Deployment Script
REM For Windows
REM ========================================

echo ====================================
echo   Agentic Honeypot API Deployment
echo ====================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please copy .env.production to .env and fill in your API keys.
    echo.
    echo   copy .env.production .env
    echo.
    exit /b 1
)

REM Check for Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo [1/4] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running
    echo Please start Docker Desktop
    exit /b 1
)
echo       Docker is running!

echo.
echo [2/4] Building Docker image...
docker-compose build
if errorlevel 1 (
    echo [ERROR] Build failed!
    exit /b 1
)
echo       Build completed!

echo.
echo [3/4] Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers!
    exit /b 1
)
echo       Containers started!

echo.
echo [4/4] Waiting for health check...
timeout /t 10 /nobreak >nul

REM Check health
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Health check failed - checking logs...
    docker-compose logs --tail=20
) else (
    echo       Health check passed!
)

echo.
echo ====================================
echo   Deployment Complete!
echo ====================================
echo.
echo   API URL: http://localhost:8000
echo   Docs:    http://localhost:8000/docs
echo   Health:  http://localhost:8000/health
echo.
echo   Commands:
echo   - View logs:    docker-compose logs -f
echo   - Stop:         docker-compose down
echo   - Restart:      docker-compose restart
echo.

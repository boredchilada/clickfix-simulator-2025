@echo off
REM ============================================================
REM Test script for Docker Compose deployment
REM ============================================================

echo ============================================================
echo Testing Docker Compose Deployment
echo ============================================================
echo.

REM Stop and remove any existing compose deployment
echo [1/5] Cleaning up existing deployment...
docker-compose down -v 2>nul

REM Create required directories
echo.
echo [2/5] Creating required directories...
if not exist "instance" mkdir instance
if not exist "certs" mkdir certs
if not exist "templates\campaigns" mkdir templates\campaigns

REM Build and start with docker-compose
echo.
echo [3/5] Building and starting with Docker Compose...
docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Compose failed to start!
    exit /b 1
)

echo [SUCCESS] Docker Compose started. Waiting for application to initialize...

REM Wait for the application to start
timeout /t 10 /nobreak > nul

REM Check container status
echo.
echo [4/5] Checking container status...
docker-compose ps

REM Check container logs
echo.
echo Container logs:
echo ----------------------------------------
docker-compose logs 2>&1
echo ----------------------------------------

REM Test the endpoint
echo.
echo [5/5] Testing HTTPS endpoint...
curl -k -s -o nul -w "HTTP Status: %%{http_code}\n" https://localhost:443/
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] curl test failed. Container may still be starting or curl not installed.
    echo You can manually test by visiting: https://localhost:443/
)

echo.
echo ============================================================
echo Docker Compose Test Summary
echo ============================================================
echo Service: clickfix
echo Port: 443
echo URL: https://localhost:443/
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo ============================================================
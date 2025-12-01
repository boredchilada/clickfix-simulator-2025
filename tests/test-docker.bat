@echo off
REM ============================================================
REM Test script for standalone Docker deployment
REM ============================================================

echo ============================================================
echo Testing Standalone Docker Deployment
echo ============================================================
echo.

REM Clean up any existing test containers
echo [1/6] Cleaning up existing test containers...
docker stop clickfix-docker-test 2>nul
docker rm clickfix-docker-test 2>nul
docker volume rm clickfix_instance_data 2>nul

REM Build the Docker image
echo.
echo [2/6] Building Docker image...
docker build -t clickfix-training:test .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed!
    exit /b 1
)
echo [SUCCESS] Docker image built successfully.

REM Create required directories
echo.
echo [3/6] Creating required directories...
if not exist "instance" mkdir instance
if not exist "certs" mkdir certs
if not exist "templates\campaigns" mkdir templates\campaigns

REM Run the container
echo.
echo [4/6] Starting container...
docker run -d ^
    --name clickfix-docker-test ^
    -p 8443:443 ^
    -v clickfix_instance_data:/app/instance ^
    -v "%cd%\certs:/app/certs" ^
    -v "%cd%\templates\campaigns:/app/templates/campaigns" ^
    -e FLASK_DEBUG=False ^
    -e ADMIN_USERNAME=admin ^
    -e ADMIN_PASSWORD=test_password ^
    -e SECRET_KEY=test_secret_key_12345 ^
    clickfix-training:test

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start container!
    exit /b 1
)

echo [SUCCESS] Container started. Waiting for application to initialize...

REM Wait for the application to start
timeout /t 10 /nobreak > nul

REM Check container status
echo.
echo [5/6] Checking container status...
docker ps --filter "name=clickfix-docker-test" --format "{{.Status}}"

REM Check container logs
echo.
echo Container logs:
echo ----------------------------------------
docker logs clickfix-docker-test 2>&1
echo ----------------------------------------

REM Test the endpoint
echo.
echo [6/6] Testing HTTPS endpoint...
curl -k -s -o nul -w "HTTP Status: %%{http_code}\n" https://localhost:8443/
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] curl test failed. Container may still be starting or curl not installed.
    echo You can manually test by visiting: https://localhost:8443/
)

echo.
echo ============================================================
echo Docker Test Summary
echo ============================================================
echo Container Name: clickfix-docker-test
echo Port: 8443 (mapped to container 443)
echo URL: https://localhost:8443/
echo.
echo To view logs: docker logs -f clickfix-docker-test
echo To stop: docker stop clickfix-docker-test
echo To remove: docker rm clickfix-docker-test
echo ============================================================
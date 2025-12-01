@echo off
setlocal

echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.8+.
    pause
    exit /b 1
)

echo [INFO] Checking Virtual Environment...
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating Virtual Environment...
call venv\Scripts\activate

echo [INFO] Installing/Updating dependencies...
pip install -r requirements.txt

echo [INFO] Initializing Database...
set FLASK_APP=app.py
flask init-db

echo [INFO] Checking SSL Certificates...
if not exist "certs" mkdir certs
if not exist "certs\cert.pem" (
    echo [WARNING] SSL Certificates not found.
    echo [INFO] Attempting to generate self-signed certs using OpenSSL...
    openssl req -x509 -newkey rsa:4096 -nodes -keyout certs\key.pem -out certs\cert.pem -days 365 -subj "/CN=localhost" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] OpenSSL not found or failed.
        echo [ERROR] The Clipboard API requires HTTPS. Please generate certs/cert.pem and certs/key.pem manually.
        echo [ERROR] You can use Git Bash or WSL to run the openssl command.
    ) else (
        echo [INFO] Certificates generated successfully.
    )
)

echo.
echo [SUCCESS] Starting ClickFix Training Tool...
echo [INFO] Access the dashboard at https://localhost:443/admin
echo.

python app.py

pause
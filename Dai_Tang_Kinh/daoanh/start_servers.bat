@echo off
rem start_servers.bat - Quick start all 3 servers and fix ERR_CONNECTION_REFUSED
rem Usage: Double-click this file or run from PowerShell/CMD

echo ============================================
echo ZQ Server Manager - Quick Start
echo ============================================
echo.

rem Step 1: Kill any existing processes on target ports
echo Killing existing processes on ports 5000, 5001, 8080...
taskkill /f /im python.exe 2>nul || timeout /t 1 >nul
echo.

rem Step 2: Start all 3 servers using Python script
echo Starting all 3 servers (app.py:5000, server.py:5001, gateway.py:8080)...
cd /d "%~dp0"
python start_servers.py
echo.

rem Step 3: Wait for servers to be ready
echo Waiting for servers to be ready (max 60 seconds)...
timeout /t 10 /nobreak >nul

rem Step 4: Verify the key URL
echo.
echo Checking http://localhost:8080/daoanh/places...
curl -s --max-time 5 http://localhost:8080/daoanh/places >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Server is running! URL accessible.
) else (
    echo ⚠️ Server may still be starting up. Please wait a moment and try again.
)
echo.

rem Step 5: Summary
echo ============================================
echo Server Status Summary
echo ============================================
echo.
echo "Port 5000 (app.py): Checking..."
echo "Port 5001 (server.py): Checking..."
echo "Port 8080 (gateway.py): Checking..."
echo.
echo "Open http://localhost:8080/daoanh/places in your browser"
echo "To stop servers: run 'dashboard\stop_all.ps1' in PowerShell
echo.
pause
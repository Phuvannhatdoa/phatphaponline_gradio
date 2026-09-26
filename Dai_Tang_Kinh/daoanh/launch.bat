@echo off
cd /d "%~dp0"
title DaoAnh Local Dev

:: ── Tao thu muc logs ─────────────────────────────────────────
if not exist logs mkdir logs

:: ── Kill port cu neu dang chay ──────────────────────────────
echo [0/4] Tat port cu (5000 / 5001 / 8080)...
for %%P in (5000 5001 8080) do (
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%%P "') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)
timeout /t 1 /nobreak >nul

:: ── Start 3 server AN (khong mo cua so CMD) ─────────────────
echo [1/4] Auth Gateway    port 5001...
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'server.py' -WorkingDirectory '%~dp0' -WindowStyle Hidden -RedirectStandardOutput '%~dp0logs\auth-5001.log' -RedirectStandardError '%~dp0logs\auth-5001-err.log'"
timeout /t 3 /nobreak >nul

echo [2/4] App chinh       port 5000...
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'app.py' -WorkingDirectory '%~dp0' -WindowStyle Hidden -RedirectStandardOutput '%~dp0logs\app-5000.log' -RedirectStandardError '%~dp0logs\app-5000-err.log'"
timeout /t 2 /nobreak >nul

echo [3/4] Local Gateway   port 8080...
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'local_gateway.py' -WorkingDirectory '%~dp0' -WindowStyle Hidden -RedirectStandardOutput '%~dp0logs\gateway-8080.log' -RedirectStandardError '%~dp0logs\gateway-8080-err.log'"
timeout /t 4 /nobreak >nul

:: ── Whitelist admin email ────────────────────────────────────
echo [4/4] Whitelist namthien@gmail.com...
curl -s -X POST http://localhost:5001/api/admin/emails/add -H "Content-Type: application/json" -d "{\"email\":\"namthien@gmail.com\"}" >nul 2>&1

:: ── Mo browser ──────────────────────────────────────────────
echo.
echo  OK  http://localhost:8080/daoanh/
echo  Log: daoanh\logs\  (app-5000.log / auth-5001.log / gateway-8080.log)
echo.
start http://localhost:8080/daoanh/login.html

:: Cua so nay tu dong dong sau 3 giay
timeout /t 3 /nobreak >nul

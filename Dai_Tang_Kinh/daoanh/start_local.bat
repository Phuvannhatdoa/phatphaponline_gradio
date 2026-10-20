@echo off
cd /d "%~dp0"

echo [1/3] Khoi dong Auth Gateway (port 5001)...
start "DaoAnh - Auth 5001" cmd /k "python server.py"

timeout /t 3 /nobreak >nul

echo [2/3] Khoi dong App chinh (port 5000)...
start "DaoAnh - App 5000" cmd /k "python app.py"

timeout /t 2 /nobreak >nul

echo [3/3] Khoi dong Local Gateway (port 8080)...
start "DaoAnh - Gateway 8080" cmd /k "python local_gateway.py"

timeout /t 4 /nobreak >nul

echo [Fix] Them admin email vao whitelist...
curl -s -X POST http://localhost:5001/api/admin/emails/add ^
     -H "Content-Type: application/json" ^
     -d "{\"email\":\"namthien@gmail.com\"}" >nul 2>&1

echo.
echo === Tat ca server da khoi dong ===
echo   Auth    : http://localhost:5001
echo   App     : http://localhost:5000
echo   Gateway : http://localhost:8080/daoanh/
echo   Login   : namthien@gmail.com (tu dong whitelist)
echo.
start http://localhost:8080/daoanh/login.html

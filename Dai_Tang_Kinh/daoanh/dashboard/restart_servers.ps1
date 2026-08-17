# restart_servers.ps1 — Restart 3 server (app.py:5000 + server.py:5001 + gateway.py:8080)
# Dùng để: deploy code mới, xác minh fix timeout, lưu log có timestamp.
# Cách chạy:  powershell -ExecutionPolicy Bypass -File dashboard\restart_servers.ps1
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$dash = Join-Path $root "dashboard"
$out  = Join-Path $dash "server_restart.log"
$ts   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log($msg) {
    $line = "[$ts] $msg"
    Add-Content -LiteralPath $out -Value $line
    Write-Host $line
}

# 1. Kill các process đang giữ port (5000=app.py, 5001=server.py, 8080=gateway)
foreach ($port in 5000, 5001, 8080) {
    $conn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $pids = $conn.OwningProcess | Sort-Object -Unique
        foreach ($pid0 in $pids) {
            Write-Log "Kill PID $pid0 (port $port)"
            Stop-Process -Id $pid0 -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 2

# 2. Start app.py:5000
$appOut = Join-Path $dash "app_restart.out.log"
$appErr = Join-Path $dash "app_restart.err.log"
$appPy  = Join-Path $root "app.py"
Start-Process -FilePath "python" -ArgumentList @("`"$appPy`"") -WorkingDirectory $root -RedirectStandardOutput $appOut -RedirectStandardError $appErr -WindowStyle Hidden
Write-Log "Started app.py:5000"

# 3. Start server.py:5001
$serverOut = Join-Path $dash "server_restart.out.log"
$serverErr = Join-Path $dash "server_restart.err.log"
$serverPy  = Join-Path $root "server.py"
Start-Process -FilePath "python" -ArgumentList @("`"$serverPy`"") -WorkingDirectory $root -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -WindowStyle Hidden
Write-Log "Started server.py:5001"

# 4. Start local_gateway.py:8080
$gwOut = Join-Path $dash "gateway_restart.out.log"
$gwErr = Join-Path $dash "gateway_restart.err.log"
$gwPy  = Join-Path $root "local_gateway.py"
Start-Process -FilePath "python" -ArgumentList @("`"$gwPy`"") -WorkingDirectory $root -RedirectStandardOutput $gwOut -RedirectStandardError $gwErr -WindowStyle Hidden
Write-Log "Started local_gateway.py:8080"

# 4. Chờ port lắng nghe (tối đa 60s)
foreach ($port in 5000, 5001, 8080) {
    $ok = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 2000
        if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
            $ok = $true
            break
        }
    }
    if ($ok) {
        Write-Log "Port $port listening."
    } else {
        Write-Log "WARN: port $port NOT listening within 60s!"
    }
}
Write-Log "Done."

# restart_servers.ps1 — Restart cả 2 server (app.py:5000 + local_gateway.py:8080) với threaded=True
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

# 1. Kill các process đang giữ port
foreach ($port in 5000, 8080) {
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

# 3. Start local_gateway.py:8080
$gwOut = Join-Path $dash "gateway_restart.out.log"
$gwErr = Join-Path $dash "gateway_restart.err.log"
$gwPy  = Join-Path $root "local_gateway.py"
Start-Process -FilePath "python" -ArgumentList @("`"$gwPy`"") -WorkingDirectory $root -RedirectStandardOutput $gwOut -RedirectStandardError $gwErr -WindowStyle Hidden
Write-Log "Started local_gateway.py:8080"

# 4. Chờ port lắng nghe (tối đa 60s)
foreach ($port in 5000, 8080) {
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

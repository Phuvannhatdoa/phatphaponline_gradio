# stop_all.ps1 — Stop ALL 3 servers (app.py:5000 + server.py:5001 + gateway.py:8080)
#
# Cách chạy:
#   powershell -ExecutionPolicy Bypass -File dashboard\stop_all.ps1
#
# Hoặc dùng Ctrl+C để dừng script start_all.ps1 đang chạy

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -Append -FilePath "dashboard\start_all.log"
}

Write-Host "Stopping all ZQ servers..." -ForegroundColor Cyan

$appRoot  = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$gwRoot   = $appRoot  # same root folder

# --- Stop app.py:5000 ---
$appPids = Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue
if ($appPids) {
    foreach ($pid in ($appPids).OwningProcess | Sort-Object -Unique) {
        Write-Log "Stopping PID $pid (app.py:5000)"
        try { Stop-Process -Id $pid -Force -ErrorAction Stop } catch { }
    }
} else {
    Write-Log "No process on port 5000 (app.py not running)."
}

# --- Stop server.py:5001 ---
$serverPids = Get-NetTCPConnection -State Listen -LocalPort 5001 -ErrorAction SilentlyContinue
if ($serverPids) {
    foreach ($pid in ($serverPids).OwningProcess | Sort-Object -Unique) {
        Write-Log "Stopping PID $pid (server.py:5001)"
        try { Stop-Process -Id $pid -Force -ErrorAction Stop } catch { }
    }
} else {
    Write-Log "No process on port 5001 (server.py not running)."
}

# --- Stop local_gateway.py:8080 ---
$gwPids = Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue
if ($gwPids) {
    foreach ($pid in ($gwPids).OwningProcess | Sort-Object -Unique) {
        Write-Log "Stopping PID $pid (local_gateway.py:8080)"
        try { Stop-Process -Id $pid -Force -ErrorAction Stop } catch { }
    }
} else {
    Write-Log "No process on port 8080 (gateway not running)."
}

Start-Sleep -Seconds 2

# Verify all stopped
Write-Log "Verifying all ports are free..."
$allFree = $true
foreach ($port in 5000, 5001, 8080) {
    $conn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Log "⚠️ Port $port STILL listening after stop attempt"
        $allFree = $false
    } else {
        Write-Log "✅ Port $port freed."
    }
}

if ($allFree) {
    Write-Host "✅ All servers stopped successfully." -ForegroundColor Green
} else {
    Write-Host "⚠️ Some ports may still have processes. Check manually." -ForegroundColor Yellow
}
Write-Log "Done."
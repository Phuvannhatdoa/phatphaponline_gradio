# start_all.ps1 — Start ALL 3 servers (app.py:5000 + server.py:5001 + local_gateway.py:8080)
#                      + Auto-restart monitor loop + Logging
#
# Cách chạy:
#   powershell -ExecutionPolicy Bypass -File dashboard\start_all.ps1
#   (chạy foreground, Ctrl+C để dừng)
#   Hoặc double-click start_all.vbs để chạy nền ẩn (chạy qua Task Scheduler)
#
# Version: 2026-08-17 build

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -Append -FilePath "dashboard\start_all.log" -Encoding UTF8
}

# ════════════════════════════════════════════════════════════════
# 0. BANNER
# ═══════════════════════════════════════════════════════════════
$banner = @"
╔══════════════════════════════════════════════════════════════════╗
║  ZQ Server Manager                                                     ║
║  Starting: app.py:5000 + server.py:5001 + local_gateway.py:8080     ║
║  Monitor: every 10s auto-restart if server dies                     ║
║  Logs: dashboard/start_all.log                                      ║
║  Stop:  powershell -ExecutionPolicy Bypass -File dashboard\stop_all.ps1║
╚══════════════════════════════════════════════════════════════════╝
"@
Write-Host $banner

# ════════════════════════════════════════════════════════════════
# 1. CLEANUP: Kill any existing processes on target ports
# ════════════════════════════════════════════════════════════════
Write-Log "Cleaning up existing processes on ports 5000, 5001, 8080..."

foreach ($port in 5000, 5001, 8080) {
    $conn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $pids = $conn.OwningProcess | Sort-Object -Unique
        foreach ($pid in $pids) {
            Write-Log "Kill PID $pid (port $port)"
            try { Stop-Process -Id $pid -Force -ErrorAction Stop } catch { }
        }
    }
}
Start-Sleep -Seconds 2

# ════════════════════════════════════════════════════════════════
# 2. START SERVERS (theo thứ tự: 5000 -> 5001 -> 8080)
# ════════════════════════════════════════════════════════════════

# --- 2a. app.py:5000 (~36s startup: FTS5 + cate cache + lexicon 166K rows) ---
Write-Log "Starting app.py:5000..."
$appRoot  = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$appPy    = Join-Path $appRoot "app.py"
$appOut   = Join-Path $appRoot "dashboard" "app_restart.out.log"
$appErr   = Join-Path $appRoot "dashboard" "app_restart.err.log"

Start-Process -FilePath "python" -ArgumentList @("`"$appPy`"") `
    -WorkingDirectory $appRoot `
    -RedirectStandardOutput $appOut -RedirectStandardError $appErr `
    -WindowStyle Hidden

Write-Log "Waiting for app.py:5000 to be ready (max 60s)..."
$appReady = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 2000
    if (Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue) {
        $appReady = $true
        break
    }
}
if ($appReady) {
    Write-Log "✅ app.py:5000 listening."
} else {
    Write-Log "⚠️ WARN: app.py:5000 NOT listening within 60s! Check dashboard/app_restart.err.log"
}

# --- 2b. server.py:5001 (~1s startup: in-memory sessions) ---
Write-Log "Starting server.py:5001..."
$gwRoot  = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$serverPy = Join-Path $gwRoot "server.py"
$serverOut = Join-Path $gwRoot "dashboard" "server_restart.out.log"
$serverErr = Join-Path $gwRoot "dashboard" "server_restart.err.log"

Start-Process -FilePath "python" -ArgumentList @("`"$serverPy`"") `
    -WorkingDirectory $gwRoot `
    -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr `
    -WindowStyle Hidden

Write-Log "Waiting for server.py:5001 to be ready (max 15s)..."
$gwReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Milliseconds 1000
    if (Get-NetTCPConnection -State Listen -LocalPort 5001 -ErrorAction SilentlyContinue) {
        $gwReady = $true
        break
    }
}
if ($gwReady) {
    Write-Log "✅ server.py:5001 listening."
} else {
    Write-Log "⚠️ WARN: server.py:5001 NOT listening within 15s! Check dashboard/server_restart.err.log"
}

# --- 2c. local_gateway.py:8080 (~1s startup: proxy gateway) ---
Write-Log "Starting local_gateway.py:8080..."
$gwPy = Join-Path $gwRoot "local_gateway.py"
$gwOut = Join-Path $gwRoot "dashboard" "gateway_restart.out.log"
$gwErr = Join-Path $gwRoot "dashboard" "gateway_restart.err.log"

Start-Process -FilePath "python" -ArgumentList @("`"$gwPy`"") `
    -WorkingDirectory $gwRoot `
    -RedirectStandardOutput $gwOut -RedirectStandardError $gwErr `
    -WindowStyle Hidden

Write-Log "Waiting for local_gateway.py:8080 to be ready (max 15s)..."
$gwListen = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Milliseconds 1000
    if (Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue) {
        $gwListen = $true
        break
    }
}
if ($gwListen) {
    Write-Log "✅ local_gateway.py:8080 listening."
} else {
    Write-Log "⚠️ WARN: local_gateway.py:8080 NOT listening within 15s! Check dashboard/gateway_restart.err.log"
}

Write-Log "All servers started. Monitor loop active every 10s..."

# ════════════════════════════════════════════════════════════════
# 3. MONITOR LOOP (auto-restart if server dies)
# ════════════════════════════════════════════════════════════════
# Track PIDs for each port (re-read from TCP connections each loop)
# Track restart attempt counts to avoid infinite restart loops

$maxRetries = 3
$retryCounts = @{ "5000" = 0; "5001" = 0; "8080" = 0 }
$lastPids = @{ "5000" = (Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue).OwningProcess;
               "5001" = (Get-NetTCPConnection -State Listen -LocalPort 5001 -ErrorAction SilentlyContinue).OwningProcess;
               "8080" = (Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue).OwningProcess }

Write-Host "Monitor loop started (check every 10s). Press Ctrl+C to stop manually.`n"

while ($true) {
    Start-Sleep -Seconds 10

    # Check each port
    foreach ($port in 5000, 5001, 8080) {
        $currentConn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
        if (-not $currentConn) {
            # Server died
            $retryCounts[$port]++
            Write-Log "[AUTO-RETRY] Port $port is DOWN (attempt $($retryCounts[$port])/$maxRetries)"

            if ($retryCounts[$port] -le $maxRetries) {
                # Kill any stale process
                $stale = Get-Process -Id ($currentConn.OwningProcess | Select-Object -First 1) -ErrorAction SilentlyContinue
                if ($stale) {
                    Write-Log "Kill stale PID $($stale.Id) on port $port"
                    try { Stop-Process -Id $stale.Id -Force -ErrorAction Stop } catch { }
                }

                # Restart the appropriate server
                switch ($port) {
                    5000 { Write-Log "Restarting app.py:5000..." }
                    5001 { Write-Log "Restarting server.py:5001..." }
                    8080 { Write-Log "Restarting local_gateway.py:8080..." }
                }

                # Start-Process again (same logic as section 2)
                switch ($port) {
                    5000 {
                        Start-Process -FilePath "python" -ArgumentList @("`"$appPy`"") `
                            -WorkingDirectory $appRoot -RedirectStandardOutput $appOut -RedirectStandardError $appErr -WindowStyle Hidden
                        Write-Log "Waiting for app.py:5000 restart (max 30s)..."
                        for ($i = 0; $i -lt 15; $i++) {
                            Start-Sleep -Milliseconds 2000
                            if (Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue) {
                                Write-Log "✅ app.py:5000 restarted."
                                break
                            }
                        }
                    }
                    5001 {
                        Start-Process -FilePath "python" -ArgumentList @("`"$serverPy`"") `
                            -WorkingDirectory $gwRoot -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -WindowStyle Hidden
                        Write-Log "Waiting for server.py:5001 restart (max 15s)..."
                        for ($i = 0; $i -lt 15; $i++) {
                            Start-Sleep -Milliseconds 1000
                            if (Get-NetTCPConnection -State Listen -LocalPort 5001 -ErrorAction SilentlyContinue) {
                                Write-Log "✅ server.py:5001 restarted."
                                break
                            }
                        }
                    }
                    8080 {
                        Start-Process -FilePath "python" -ArgumentList @("`"$gwPy`"") `
                            -WorkingDirectory $gwRoot -RedirectStandardOutput $gwOut -RedirectStandardError $gwErr -WindowStyle Hidden
                        Write-Log "Waiting for gateway:8080 restart (max 15s)..."
                        for ($i = 0; $i -lt 15; $i++) {
                            Start-Sleep -Milliseconds 1000
                            if (Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue) {
                                Write-Log "✅ local_gateway.py:8080 restarted."
                                break
                            }
                        }
                    }
                }
            } else {
                Write-Log "[WARN] Port $port failed $maxRetries times consecutively. Manual intervention needed."
                $retryCounts[$port] = 0  # reset to prevent spam
            }
        } else {
            # Server healthy — reset retry counter
            $retryCounts[$port] = 0
        }
    }
}
# =====================================================================
# restart_server.ps1 — Khởi động lại server daoanh (app.py) an toàn.
# Cách dùng (TÀI KHOẢN ADMIN):
#   powershell -ExecutionPolicy Bypass -File scripts\restart_server.ps1
# Hoặc popup UAC:
#   Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File <đường dẫn tuyệt đối>\restart_server.ps1'
# =====================================================================
$ErrorActionPreference = 'Stop'
$daoanh = Split-Path -Parent $PSScriptRoot   # ...\daoanh
$logDir = Join-Path $daoanh 'data'
$outLog = Join-Path $logDir 'server.out.log'
$errLog = Join-Path $logDir 'server.err.log'
$pidFile = Join-Path $logDir 'server.pid'

# 1) Tìm process python listening trên port 5000 có commandline chứa 'app.py'
$conn = Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $($conn.OwningProcess)" -ErrorAction SilentlyContinue
  if ($proc -and $proc.CommandLine -match 'app\.py') {
    Write-Host "[restart] kill PID $($proc.ProcessId) (app.py)"
    Stop-Process -Id $proc.ProcessId -Force
    Start-Sleep -Seconds 2
  } else {
    Write-Host "[restart] WARN: port 5000 do process khac giu (PID $($conn.OwningProcess)) — khong kill, thoat."
    exit 1
  }
}

# 2) Start python app.py (Windows Python), log ra data/server.*.log
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { Write-Host "[restart] khong tim thay python"; exit 1 }
$proc2 = Start-Process -FilePath $py -ArgumentList 'app.py' `
  -WorkingDirectory $daoanh -WindowStyle Hidden `
  -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
"pid=$($proc2.Id) started=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') port=5000" | Set-Content -Path $pidFile -Encoding UTF8
Write-Host "[restart] started PID $($proc2.Id) — log: data\server.out.log / data\server.err.log (pid marker: data\server.pid)"

# 3) Cho phep Flask len port roi kiem tra
Start-Sleep -Seconds 6
try {
  $r = Invoke-RestMethod -Uri 'http://127.0.0.1:5000/daoanh/api/passage/3923/translate' -TimeoutSec 10
  Write-Host "[restart] OK — mode=$($r.mode) ok=$($r.ok)"
} catch {
  Write-Host "[restart] chua san: $($_.Exception.Message) (xem data\server.err.log)"
}
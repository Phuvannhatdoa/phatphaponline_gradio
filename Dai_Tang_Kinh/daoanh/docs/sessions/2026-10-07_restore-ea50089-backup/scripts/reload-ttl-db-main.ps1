# T227: chạy bằng Administrator cho nâng cấp đã được Admin yêu cầu; chỉ main app:5000.
$ErrorActionPreference='Stop'
$project227=Split-Path -Parent $PSScriptRoot
$report227=Join-Path $project227 'docs/reports/T227-db-ttl-export-20261004'
try {
$identity227=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal227=New-Object Security.Principal.WindowsPrincipal($identity227)
if (-not $principal227.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'Cần quyền Administrator của Windows để restart tiến trình main hiện tại.'}
$connection227=Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
$process227=$null
if ($connection227) {
 $api227=Invoke-RestMethod 'http://127.0.0.1:5000/daoanh/api/admin/lineages' -TimeoutSec 10
 if (-not $api227.ok) {throw 'Port5000 không trả đúng daoanh; không dừng tiến trình.'}
 $process227=Get-CimInstance Win32_Process -Filter "ProcessId = $($connection227.OwningProcess)"
 if (-not $process227 -or $process227.CommandLine -notmatch 'app\.py') {throw 'Không xác minh được main app.py; không kill.'}
}
$env:PYTHONPATH=(Join-Path $project227 'data/backups/T226-ttl-profile-20261003/python-deps')+';'+(Join-Path $project227 'data/backups/T215-fix-sync-20261002/python-deps')
$beforeBootstrap227=(Get-FileHash -LiteralPath (Join-Path $project227 'app.py') -Algorithm SHA256).Hash.ToLower()
Push-Location $project227
try {& python -X utf8 (Join-Path $report227 'bootstrap_check.py') *> (Join-Path $report227 'bootstrap-inside-reload.log');$bootstrapExit227=$LASTEXITCODE} finally {Pop-Location}
if ($bootstrapExit227 -ne 0) {throw 'Bootstrap app hiện tại thất bại; giữ server cũ.'}
$afterBootstrap227=(Get-FileHash -LiteralPath (Join-Path $project227 'app.py') -Algorithm SHA256).Hash.ToLower()
if ($beforeBootstrap227 -ne $afterBootstrap227) {throw 'app.py đổi trong lúc bootstrap; giữ server cũ để thử lại sau.'}
$afterBootstrap227 | Set-Content -LiteralPath (Join-Path $report227 'app-bootstrap-guard.sha256')
$latestConnection227=Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($process227) {
 if (-not $latestConnection227 -or $latestConnection227.OwningProcess -ne $process227.ProcessId) {throw 'PID main đổi khi bootstrap; giữ tiến trình mới.'}
 Stop-Process -Id $process227.ProcessId -Force
} elseif ($latestConnection227) {throw 'Main vừa được phiên khác khởi động; giữ tiến trình đó.'}
$env:PYTHONPATH=(Join-Path $project227 'data/backups/T226-ttl-profile-20261003/python-deps')+';'+(Join-Path $project227 'data/backups/T215-fix-sync-20261002/python-deps')
$env:APP_PORT='5000'
$main227=Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-X','utf8','app.py') -WorkingDirectory $project227 -WindowStyle Hidden -RedirectStandardOutput (Join-Path $report227 'main-reload.out.log') -RedirectStandardError (Join-Path $report227 'main-reload.err.log') -PassThru
$main227.Id | Set-Content -LiteralPath (Join-Path $report227 'main-reload.pid')
"Started main app PID=$($main227.Id). Gateway8080/Auth5001 kept."
$ready227=$false
for ($attempt227=0; $attempt227 -lt 15; $attempt227++) {
    Start-Sleep -Seconds 2
    try {$schema227=Invoke-RestMethod 'http://127.0.0.1:5000/daoanh/api/admin/ttl_v2/from_db/A008431' -TimeoutSec 3; if ($schema227.ok -and $schema227.source_mode -eq 'database') {$ready227=$true; break}} catch {}
}
if (-not $ready227) {throw 'Main mới chưa trả schema v2; xem main-reload.err.log. Không tự đổi code hoặc DB.'}
[pscustomobject]@{status='ready';pid=$main227.Id;previous_pid=$process227.ProcessId;source_mode=$schema227.source_mode;checked_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report227 'reload-status.json') -Encoding UTF8
} catch {
 [pscustomobject]@{status='failed';error=$_.Exception.Message;checked_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report227 'reload-status.json') -Encoding UTF8
 throw
}

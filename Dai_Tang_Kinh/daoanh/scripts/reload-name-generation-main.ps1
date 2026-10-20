# T233: chạy bằng Administrator cho nâng cấp đã được Admin yêu cầu; chỉ main app:5000.
$ErrorActionPreference='Stop'
$project233=Split-Path -Parent $PSScriptRoot
$report233=Join-Path $project233 'docs/reports/T233-codex-namevi-20261004'
try {
$identity233=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal233=New-Object Security.Principal.WindowsPrincipal($identity233)
if (-not $principal233.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'Cần quyền Administrator của Windows để restart tiến trình main hiện tại.'}
$connection233=Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
$process233=$null
if ($connection233) {
 $api233=Invoke-RestMethod 'http://127.0.0.1:5000/daoanh/api/admin/lineages' -TimeoutSec 10
 if (-not $api233.ok) {throw 'Port5000 không trả đúng daoanh; không dừng tiến trình.'}
 $process233=Get-CimInstance Win32_Process -Filter "ProcessId = $($connection233.OwningProcess)"
 if (-not $process233 -or $process233.CommandLine -notmatch 'app\.py') {throw 'Không xác minh được main app.py; không kill.'}
}
$env:PYTHONPATH=(Join-Path $project233 'data/backups/T226-ttl-profile-20261003/python-deps')+';'+(Join-Path $project233 'data/backups/T215-fix-sync-20261002/python-deps')
$beforeBootstrap233=(Get-FileHash -LiteralPath (Join-Path $project233 'app.py') -Algorithm SHA256).Hash.ToLower()
Push-Location $project233
try {& python -B -X utf8 (Join-Path $report233 'bootstrap_check.py') *> (Join-Path $report233 'bootstrap-inside-reload.log');$bootstrapExit233=$LASTEXITCODE} finally {Pop-Location}
if ($bootstrapExit233 -ne 0) {throw 'Bootstrap app hiện tại thất bại; giữ server cũ.'}
$afterBootstrap233=(Get-FileHash -LiteralPath (Join-Path $project233 'app.py') -Algorithm SHA256).Hash.ToLower()
if ($beforeBootstrap233 -ne $afterBootstrap233) {throw 'app.py đổi trong lúc bootstrap; giữ server cũ để thử lại sau.'}
$afterBootstrap233 | Set-Content -LiteralPath (Join-Path $report233 'app-bootstrap-guard.sha256')
$latestConnection233=Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($process233) {
 if (-not $latestConnection233 -or $latestConnection233.OwningProcess -ne $process233.ProcessId) {throw 'PID main đổi khi bootstrap; giữ tiến trình mới.'}
 Stop-Process -Id $process233.ProcessId -Force
} elseif ($latestConnection233) {throw 'Main vừa được phiên khác khởi động; giữ tiến trình đó.'}
$env:PYTHONPATH=(Join-Path $project233 'data/backups/T226-ttl-profile-20261003/python-deps')+';'+(Join-Path $project233 'data/backups/T215-fix-sync-20261002/python-deps')
$env:APP_PORT='5000'
$main233=Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-B','-X','utf8','app.py') -WorkingDirectory $project233 -WindowStyle Hidden -RedirectStandardOutput (Join-Path $report233 'main-reload.out.log') -RedirectStandardError (Join-Path $report233 'main-reload.err.log') -PassThru
$main233.Id | Set-Content -LiteralPath (Join-Path $report233 'main-reload.pid')
"Started main app PID=$($main233.Id). Gateway8080/Auth5001 kept."
$ready233=$false
for ($attempt233=0; $attempt233 -lt 8; $attempt233++) {
    Start-Sleep -Seconds 2
    try {$schema233=Invoke-RestMethod 'http://127.0.0.1:5000/daoanh/api/admin/ttl_v2/from_db/A008431' -TimeoutSec 20; if ($schema233.ok -and $schema233.source_mode -eq 'database') {$ready233=$true; break}} catch {}
}
if (-not $ready233) {throw 'Main mới chưa trả schema v2; xem main-reload.err.log. Không tự đổi code hoặc DB.'}
[pscustomobject]@{status='ready';pid=$main233.Id;previous_pid=$process233.ProcessId;source_mode=$schema233.source_mode;checked_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report233 'reload-status.json') -Encoding UTF8
} catch {
 [pscustomobject]@{status='failed';error=$_.Exception.Message;checked_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report233 'reload-status.json') -Encoding UTF8
 throw
}

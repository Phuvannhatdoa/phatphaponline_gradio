# T226: chạy bằng Administrator sau khi Admin duyệt; chỉ main app:5000.
$ErrorActionPreference='Stop'
$project226=Split-Path -Parent $PSScriptRoot
$report226=Join-Path $project226 'docs/reports/T226-ttl-profile-20261003'
try {
$identity226=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal226=New-Object Security.Principal.WindowsPrincipal($identity226)
if (-not $principal226.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'Cần quyền Administrator của Windows để restart tiến trình main hiện tại.'}
$api226=Invoke-RestMethod 'http://127.0.0.1:5000/daoanh/api/admin/lineages' -TimeoutSec 10
if (-not $api226.ok) {throw 'Port5000 không trả đúng API daoanh; dừng.'}
$connection226=Get-NetTCPConnection -State Listen -LocalPort 5000 | Select-Object -First 1
$process226=Get-CimInstance Win32_Process -Filter "ProcessId = $($connection226.OwningProcess)"
if (-not $process226 -or $process226.CommandLine -notmatch 'app\.py') {throw 'Không xác minh được main app.py; dừng, không kill.'}
$manifest226=Get-Content -LiteralPath (Join-Path $report226 'rollback-manifest.json') -Raw | ConvertFrom-Json
$appEntry226=$manifest226.files | Where-Object {$_.path -eq 'app.py'}
if ((Get-FileHash -LiteralPath (Join-Path $project226 'app.py') -Algorithm SHA256).Hash.ToLower() -ne $appEntry226.after_sha256) {throw 'app.py đã đổi sau kiểm tra T226; giữ nguyên server, cần review lại.'}
Stop-Process -Id $process226.ProcessId -Force
$env:PYTHONPATH=(Join-Path $project226 'data/backups/T226-ttl-profile-20261003/python-deps')+';'+(Join-Path $project226 'data/backups/T215-fix-sync-20261002/python-deps')
$env:APP_PORT='5000'
$main226=Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-X','utf8','app.py') -WorkingDirectory $project226 -WindowStyle Hidden -RedirectStandardOutput (Join-Path $report226 'main-reload.out.log') -RedirectStandardError (Join-Path $report226 'main-reload.err.log') -PassThru
$main226.Id | Set-Content -LiteralPath (Join-Path $report226 'main-reload.pid')
"Started main app PID=$($main226.Id). Gateway8080/Auth5001 kept."
$ready226=$false
for ($attempt226=0; $attempt226 -lt 15; $attempt226++) {
    Start-Sleep -Seconds 2
    try {$schema226=Invoke-RestMethod 'http://127.0.0.1:5000/daoanh/api/admin/ttl_v2/schema' -TimeoutSec 3; if ($schema226.ok -and $schema226.version -eq '2.0.0') {$ready226=$true; break}} catch {}
}
if (-not $ready226) {throw 'Main mới chưa trả schema v2; xem main-reload.err.log. Không tự đổi code hoặc DB.'}
[pscustomobject]@{status='ready';pid=$main226.Id;previous_pid=$process226.ProcessId;version=$schema226.version;checked_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report226 'reload-status.json') -Encoding UTF8
} catch {
 [pscustomobject]@{status='failed';error=$_.Exception.Message;checked_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report226 'reload-status.json') -Encoding UTF8
 throw
}

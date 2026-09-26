# sync_to_vps.ps1 - push local dev changes (code + lineage.db) to VPS
# Runs via Windows Task Scheduler every 12h. Direction: Local -> VPS only.
# Non-destructive: only overwrites matching files on VPS, never deletes
# anything there (safe alongside OpenCode's own direct edits on the VPS).

$ErrorActionPreference = 'Continue'
$daoanh = "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
$remoteBase = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"
$logFile = Join-Path $daoanh "sync_to_vps.log"
$scratch = "$env:TEMP\daoanh_sync"
New-Item -ItemType Directory -Force -Path $scratch | Out-Null

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -LiteralPath $logFile -Value $line
    Write-Output $line
}

Log "=== Sync run started ==="

# 1. Sync top-level .py files (app.py, server.py, local_gateway.py, etc.) + CLAUDE.md
$pyFiles = Get-ChildItem -LiteralPath $daoanh -Filter *.py -File -ErrorAction SilentlyContinue
foreach ($f in $pyFiles) {
    scp -o BatchMode=yes -o ConnectTimeout=15 "$($f.FullName)" "vps-daoanh:$remoteBase/$($f.Name)" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Log "OK   $($f.Name)" } else { Log "FAIL $($f.Name) exit=$LASTEXITCODE" }
}
if (Test-Path "$daoanh\CLAUDE.md") {
    scp -o BatchMode=yes -o ConnectTimeout=15 "$daoanh\CLAUDE.md" "vps-daoanh:$remoteBase/CLAUDE.md" 2>&1 | Out-Null
    Log "CLAUDE.md sync exit=$LASTEXITCODE"
}

# 2b. Sync Dai_Tang_Kinh/index.html (root redirect page)
$rootIndex = Split-Path $daoanh -Parent
$rootHtml = "$rootIndex\index.html"
if (Test-Path -LiteralPath $rootHtml) {
    $remoteRoot = Split-Path $remoteBase -Parent
    scp -o BatchMode=yes -o ConnectTimeout=15 "$rootHtml" "vps-daoanh:$remoteRoot/index.html" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Log "OK   ../index.html (root redirect)" } else { Log "FAIL ../index.html exit=$LASTEXITCODE" }
}

# 2c. Sync top-level HTML files (places.html, etc.)
$htmlFiles = Get-ChildItem -LiteralPath $daoanh -Filter *.html -File -ErrorAction SilentlyContinue
foreach ($f in $htmlFiles) {
    scp -o BatchMode=yes -o ConnectTimeout=15 "$($f.FullName)" "vps-daoanh:$remoteBase/$($f.Name)" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Log "OK   $($f.Name)" } else { Log "FAIL $($f.Name) exit=$LASTEXITCODE" }
}

# 2c. Sync admin/*.html
$adminDir = "$daoanh\admin"
if (Test-Path -LiteralPath $adminDir) {
    $adminHtml = Get-ChildItem -LiteralPath $adminDir -Filter *.html -File -ErrorAction SilentlyContinue
    foreach ($f in $adminHtml) {
        scp -o BatchMode=yes -o ConnectTimeout=15 "$($f.FullName)" "vps-daoanh:$remoteBase/admin/$($f.Name)" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log "OK   admin/$($f.Name)" } else { Log "FAIL admin/$($f.Name) exit=$LASTEXITCODE" }
    }
}

# 2. Sync lineage.db only if it changed since the last successful sync
#    (resumable sftp 'put -a', retried on connection drop - a plain scp of a
#    664MB+ file proved unreliable on this network during earlier testing)
$dbPath = "$daoanh\data\lineage.db"
$hashMarkerFile = "$scratch\lineage_db_last_hash.txt"

if (Test-Path -LiteralPath $dbPath) {
    $currentHash = (Get-FileHash -LiteralPath $dbPath -Algorithm SHA256).Hash
    $lastHash = if (Test-Path $hashMarkerFile) { (Get-Content $hashMarkerFile -Raw).Trim() } else { '' }

    if ($currentHash -ne $lastHash) {
        Log "lineage.db changed since last sync, uploading..."
        $remotePath = "$remoteBase/data/lineage.db"
        $batchFile = "$scratch\sftp_put_batch.txt"
        $success = $false
        for ($i = 1; $i -le 10; $i++) {
            $lines = @("put -a `"$dbPath`" $remotePath", "bye")
            [System.IO.File]::WriteAllLines($batchFile, $lines, [System.Text.ASCIIEncoding]::new())
            sftp -o BatchMode=yes -o ConnectTimeout=15 -b $batchFile vps-daoanh 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) { $success = $true; break }
            Log "  upload attempt $i failed, retrying..."
            Start-Sleep -Seconds 10
        }
        if ($success) {
            Set-Content -LiteralPath $hashMarkerFile -Value $currentHash
            Log "lineage.db upload OK"
        } else {
            Log "lineage.db upload FAILED after 10 attempts - will retry next run"
        }
    } else {
        Log "lineage.db unchanged since last sync, skipped"
    }
} else {
    Log "lineage.db not found locally, skipped"
}

# 3. Restart the VPS systemd service so it picks up the new code/DB
$restartOutput = ssh -o BatchMode=yes -o ConnectTimeout=15 vps-daoanh "systemctl restart daoanh-api.service && sleep 2 && systemctl is-active daoanh-api.service" 2>&1
Log "VPS service restart: $restartOutput"

Log "=== Sync run finished ==="

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

# 2d. Sync src_python/*.py (flat files only — subdir modules)
$srcPyDir = "$daoanh\src_python"
if (Test-Path -LiteralPath $srcPyDir) {
    $srcPyFiles = Get-ChildItem -LiteralPath $srcPyDir -Filter *.py -File -ErrorAction SilentlyContinue
    foreach ($f in $srcPyFiles) {
        scp -o BatchMode=yes -o ConnectTimeout=15 "$($f.FullName)" "vps-daoanh:$remoteBase/src_python/$($f.Name)" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log "OK   src_python/$($f.Name)" } else { Log "FAIL src_python/$($f.Name) exit=$LASTEXITCODE" }
    }
}

# 2. Sync lineage.db — T387: online backup API → upload tên .incoming → verify → mv nguyên tử
#    Không bao giờ đọc/copy file DB đang chạy bằng copy thô (WAL có thể mất dữ liệu).
$dbPath = "$daoanh\data\lineage.db"
$hashMarkerFile = "$scratch\lineage_db_last_hash.txt"
$restartNeeded = $false

if (Test-Path -LiteralPath $dbPath) {
    $currentHash = (Get-FileHash -LiteralPath $dbPath -Algorithm SHA256).Hash
    $lastHash = if (Test-Path $hashMarkerFile) { (Get-Content $hashMarkerFile -Raw).Trim() } else { '' }

    if ($currentHash -ne $lastHash) {
        Log "lineage.db changed since last sync, creating online snapshot..."

        $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
        $snapshotDir = "$scratch\db"
        New-Item -ItemType Directory -Force -Path $snapshotDir | Out-Null
        $snapshot = "$snapshotDir\lineage_$ts.db"
        $remoteIncoming = "$remoteBase/data/lineage.db.incoming-$ts"
        $remoteDb = "$remoteBase/data/lineage.db"

        # 2a. Snapshot bằng SQLite online backup API (an toàn khi app đang chạy)
        python -X utf8 "$daoanh\scripts\db_safe_backup.py" "$dbPath" "$snapshot" 2>&1 | ForEach-Object { Log "  $_" }
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $snapshot)) {
            Log "lineage.db snapshot FAILED - skip upload and restart"
        } else {
            $snapHash = (Get-FileHash -LiteralPath $snapshot -Algorithm SHA256).Hash.ToLower()
            $snapSize = (Get-Item -LiteralPath $snapshot).Length
            Log "  snapshot ready: $snapSize bytes sha256=$($snapHash.Substring(0,16))..."

            # 2b. Upload lên tên tạm .incoming (KHÔNG ghi đè DB production)
            $batchFile = "$scratch\sftp_put_batch.txt"
            $uploaded = $false
            for ($i = 1; $i -le 10; $i++) {
                $lines = @("put `"$snapshot`" $remoteIncoming", "bye")
                [System.IO.File]::WriteAllLines($batchFile, $lines, [System.Text.ASCIIEncoding]::new())
                sftp -o BatchMode=yes -o ConnectTimeout=15 -b $batchFile vps-daoanh 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) { $uploaded = $true; break }
                Log "  upload attempt $i failed, retrying..."
                Start-Sleep -Seconds 10
            }

            if (-not $uploaded) {
                Log "lineage.db upload FAILED after 10 attempts - DB untouched, no restart (retry next run)"
                try { ssh -o BatchMode=yes -o ConnectTimeout=15 vps-daoanh "rm -f $remoteIncoming" 2>&1 | Out-Null } catch {}
            } else {
                Log "  uploaded to $remoteIncoming"

                # 2c. Verify trên VPS: sha256 + PRAGMA quick_check
                $remoteHash = (ssh -o BatchMode=yes -o ConnectTimeout=30 vps-daoanh "sha256sum $remoteIncoming | cut -d' ' -f1" 2>&1 | Out-String).Trim().ToLower()
                $pyQc = 'import sqlite3,sys;print(sqlite3.connect("file:"+sys.argv[1]+"?mode=ro",uri=True).execute("PRAGMA quick_check").fetchone()[0])'
                $remoteQc = (ssh -o BatchMode=yes -o ConnectTimeout=60 vps-daoanh "python3 -c '$pyQc' $remoteIncoming" 2>&1 | Out-String).Trim()

                Log "  remote sha256=$($remoteHash.Substring(0,[Math]::Min(16,$remoteHash.Length)))... quick_check=$remoteQc"

                if ($remoteHash -ne $snapHash) {
                    Log "VERIFY FAILED (sha256 mismatch) - DB untouched, no restart"
                    ssh -o BatchMode=yes -o ConnectTimeout=15 vps-daoanh "rm -f $remoteIncoming" 2>&1 | Out-Null
                } elseif ($remoteQc -ne 'ok') {
                    Log "VERIFY FAILED (quick_check=$remoteQc) - DB untouched, no restart"
                    ssh -o BatchMode=yes -o ConnectTimeout=15 vps-daoanh "rm -f $remoteIncoming" 2>&1 | Out-Null
                } else {
                    # 2d. Swap nguyên tử: mv trên cùng filesystem là atomic
                    $swap = (ssh -o BatchMode=yes -o ConnectTimeout=30 vps-daoanh "mv -f $remoteIncoming $remoteDb && ls -l $remoteDb" 2>&1 | Out-String).Trim()
                    Log "  swap: $swap"
                    if ($LASTEXITCODE -eq 0) {
                        Set-Content -LiteralPath $hashMarkerFile -Value $currentHash
                        Log "lineage.db swapped OK"
                        $restartNeeded = $true
                    } else {
                        Log "SWAP FAILED - DB untouched, no restart"
                    }
                }
            }
            try { Remove-Item -LiteralPath $snapshot -Force -ErrorAction SilentlyContinue } catch {}
        }
    } else {
        Log "lineage.db unchanged since last sync, skipped"
    }
} else {
    Log "lineage.db not found locally, skipped"
}

# 3. Restart VPS service ONLY when a verified DB swap happened, then health check
if ($restartNeeded) {
    $restartOutput = ssh -o BatchMode=yes -o ConnectTimeout=15 vps-daoanh "systemctl restart daoanh-api.service && sleep 2 && systemctl is-active daoanh-api.service" 2>&1
    Log "VPS service restart: $restartOutput"

    $health = (ssh -o BatchMode=yes -o ConnectTimeout=15 vps-daoanh "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/health" 2>&1 | Out-String).Trim()
    Log "VPS health check /api/health: $health"
    if ($health -ne '200') {
        Log "HEALTH CHECK FAILED ($health) - manual attention required"
    }
} else {
    Log "No verified DB swap - VPS restart skipped"
}

Log "=== Sync run finished ==="

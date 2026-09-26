# gitbook_daily_update.ps1
# Daily 12:00 watchdog: ensures GitBook (http://localhost:4000) serves latest .md.
# - Port 4000 alive -> honkit serve watch auto-rebuilds on .md change; just log.
# - Port 4000 dead  -> rebuild _book/ + restart honkit serve.
# Registered via Windows Task Scheduler, daily at 12:00.
# NOTE: ASCII-only strings (PowerShell 5.1 reads .ps1 as cp1252 -> Vietnamese breaks).

$ErrorActionPreference = 'Continue'

$DaoanhDir = 'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh'
$ServeLog  = Join-Path $env:TEMP 'honkit_serve.log'
$ScriptLog = Join-Path $env:TEMP 'gitbook_daily_update.log'
$Port      = 4000
$Url       = 'http://localhost:4000/'

function Write-Log([string]$msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Add-Content -Path $ScriptLog -Value $line -Encoding UTF8
}

function Test-PortListening([int]$port) {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $c)
}

function Test-Url([string]$url, [int]$timeoutSec = 20) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec $timeoutSec
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Start-HonkitServe {
    $argList = '/c', "npx honkit serve ./ --port $Port > `"$ServeLog`" 2>&1"
    Start-Process -FilePath 'cmd.exe' -ArgumentList $argList -WorkingDirectory $DaoanhDir -WindowStyle Hidden
}

function Rebuild-Book {
    Push-Location $DaoanhDir
    try {
        npx honkit build ./ 2>&1 | Out-Null
    } finally {
        Pop-Location
    }
}

# ---- Main ----
if (-not (Test-Path $DaoanhDir)) {
    Write-Log "ERR: daoanh dir not found: $DaoanhDir"
    exit 1
}

if (Test-PortListening $Port) {
    if (Test-Url $Url) {
        Write-Log 'OK: port 4000 alive, honkit watch auto-updates on .md change.'
    } else {
        Write-Log 'WARN: port 4000 listening but no HTTP 200. Kill + rebuild + restart.'
        Stop-Process -Id (Get-NetTCPConnection -LocalPort $Port -State Listen).OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        Rebuild-Book
        Start-HonkitServe
        Start-Sleep -Seconds 5
        if (Test-Url $Url) {
            Write-Log 'RESULT: OK served again'
        } else {
            Write-Log 'RESULT: FAIL after restart'
        }
    }
} else {
    Write-Log 'WARN: port 4000 dead -> rebuild + restart honkit serve.'
    Rebuild-Book
    Start-HonkitServe
    Start-Sleep -Seconds 5
    if (Test-Url $Url) {
        Write-Log 'RESULT: OK running'
    } else {
        Write-Log ("RESULT: FAIL (see " + $ServeLog + ")")
    }
}

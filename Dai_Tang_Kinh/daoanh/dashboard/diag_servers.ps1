# diag_servers.ps1 — Chẩn đoán tại sao localhost:8080 không kết nối được
# Chạy:  powershell -ExecutionPolicy Bypass -File dashboard\diag_servers.ps1
# (Chạy trong terminal riêng của bạn — KHÔNG phải trong opencode, vì shell opencode đang hỏng)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$dash = Join-Path $root "dashboard"

Write-Host "===== 1. Trạng thái port =====" -ForegroundColor Cyan
foreach ($port in 8080, 5000, 5001) {
    $conn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $pids = ($conn.OwningProcess | Sort-Object -Unique) -join ","
        Write-Host "  PORT $port : DANG CHAY (PID $pids)" -ForegroundColor Green
    } else {
        Write-Host "  PORT $port : KHONG CHAY" -ForegroundColor Red
    }
}

Write-Host "`n===== 2. Process python dang chay =====" -ForegroundColor Cyan
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Select-Object ProcessId, CommandLine | Format-Table -AutoSize -Wrap

Write-Host "===== 3. Ket qua log (latest) =====" -ForegroundColor Cyan
foreach ($lf in @("app_restart.err.log","gateway_restart.err.log","server_restart.err.log","start_all.log")) {
    $p = Join-Path $dash $lf
    Write-Host "--- $lf ---" -ForegroundColor Yellow
    if (Test-Path $p) {
        try {
            Get-Content -LiteralPath $p -Encoding Unicode -Tail 40 -ErrorAction SilentlyContinue
        } catch {
            try { Get-Content -LiteralPath $p -Encoding UTF8 -Tail 40 -ErrorAction SilentlyContinue } catch { }
        }
        try {
            # nếu file binary, ép đọc UTF16
            $bytes = [System.IO.File]::ReadAllBytes($p)
            $txt = [System.Text.Encoding]::Unicode.GetString($bytes)
            Write-Host $txt
        } catch { }
    } else {
        Write-Host "  (khong co file)"
    }
    Write-Host ""
}

Write-Host "===== 4. Kiem tra python tren PATH =====" -ForegroundColor Cyan
try {
    $py = Get-Command python -ErrorAction Stop
    Write-Host "  python: $($py.Source)" -ForegroundColor Green
    & python --version
} catch {
    Write-Host "  KHONG tim thay python trong PATH" -ForegroundColor Red
}

Write-Host "`n===== 5. Huong dan =====" -ForegroundColor Cyan
Write-Host @"
- Neu 8080 khong chay: mo log gateway_restart.err.log de xem loi local_gateway.py tai sao crash.
- Neu 5000 khong chay: app.py crash khi import (xem app_restart.err.log). 
  Test nhanh app.py:  python -c \"import ast; ast.parse(open('app.py',encoding='utf-8').read()); print('SYNTAX OK')\"
- Sau khi tim ra loi, chay lai:  powershell -ExecutionPolicy Bypass -File dashboard\start_all.ps1
"@

# setup_task.ps1 — Tạo Windows Scheduled Task tự động khởi động server khi đăng nhập
#
# Mục đích: Khi user đăng nhập Windows, Task Scheduler sẽ tự động chạy start_all.vbs
#           → start_all.ps1 → start 3 server + monitor auto-restart
#
# Cách chạy một lần:
#   powershell -ExecutionPolicy Bypass -File dashboard\setup_task.ps1
#
# Sau đó:
#   - Mỗi khi đăng nhập Windows: server tự chạy nền (không thấy PowerShell window)
#   - Dùng stop_all.ps1 để dừng khi cần
#   - Hoặc dùng Task Manager để kill process nếu cần

Write-Host "Setting up Windows Scheduled Task 'ZQ-Server-Manager'..." -ForegroundColor Cyan

$taskName = "ZQ-Server-Manager"
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"`"$env:UserProfile\dashboard\start_all.vbs`"`""

' Sử dụng đường dẫn tuyệt đối an toàn hơn:
$dashboardDir = "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\dashboard"
$action = New-ScheduledTaskAction `
    -Execute "cscript.exe" `
    -Argument "$dashboardDir\start_all.vbs"

$trigger = New-ScheduledTaskTrigger -AtLogOn

$principal = New-ScheduledTaskPrincipal `
    -UserId (Read-Host "Nhập username chạy task (hoặc Enter dùng user hiện tại): ") `
    -LogonType S4U `
    -RunLevel Highest

if (-not (Read-Host "Use current user? (Y/N)").ToUpper() -eq "Y") {
    Write-Host "CANCELLED: Task not created." -ForegroundColor Yellow
    return
}

# Nếu user nhập username khác
$username = if (Read-Host "Username" -ErrorAction SilentlyContinue) { $trimmed = $_.Trim(); $trimmed } else { $env:USERNAME }

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Description "ZQ Server Manager: tự start app.py:5000, server.py:5001, gateway.py:8080 + monitor auto-restart" `
        -ErrorAction Stop

    Write-Host "✅ Task Scheduler created successfully!" -ForegroundColor Green
    Write-Host "   Task Name: $taskName" -ForegroundColor White
    Write-Host "   Trigger: At log on" -ForegroundColor White
    Write-Host "   Runs: $dashboardDir\start_all.vbs (hidden)" -ForegroundColor White
    Write-Host "`nGõ 'powershell -ExecutionPolicy Bypass -File dashboard\stop_all.ps1' để dừng server bất cứ khi nào." -ForegroundColor Yellow
} catch {
    Write-Error "❌ Failed to create task: $_"
    Write-Host "Có thể cần chạy PowerShell với Admin." -ForegroundColor Red
}
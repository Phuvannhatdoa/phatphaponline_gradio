' start_all.vbs — Run start_all.ps1 hidden (no PowerShell window)
' Sử dụng với Task Scheduler hoặc double-click để chạy nền
'
' Đóng gói: powershell -ExecutionPolicy Bypass -File "path\to\dashboard\start_all.ps1"
' Parameter: 0 = hidden window, False = chạy nền (không block)
'
Set objShell = CreateObject("WScript.Shell')

' --- CÓ THỂ ĐƯA PATH HOẶC DỰNG RELATIVE ---
strScriptDir = objShell.ExpandEnvironmentStrings("%~dp0')
Write-Host "Running start_all.ps1 from: " & strScriptDir

' Chạy PowerShell ẩn, không chờ kết quả (False = nền)
Return = objShell.Run("powershell -ExecutionPolicy Bypass -File `" & strScript & "start_all.ps1`"", 0, False)

' Không có dòng Return ở đây — script VBS kết thúc ngay, PowerShell đang chạy nền
Write-Host "start_all.ps1 launched in background. Check dashboard/start_all.log for status."
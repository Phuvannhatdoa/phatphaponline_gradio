<#
  notify_done.ps1 — Báo "Task Done" trên desktop: nhân vật Tiểu Thiên (avatar báo Done của Đạo Ảnh) hiện ở góc phải dưới (cạnh khay hệ thống),
  kèm âm "ting ting". Admin click vào nhân vật thì ẩn. Chỉ chạy trên máy local, không gửi dữ liệu đi đâu.

  Dùng (RC hoặc Hermes gọi khi xong task):
    powershell -ExecutionPolicy Bypass -File scripts\notify_done.ps1 -Title "T404 Done" -Message "BUG-034 ô Search"
  Tham số: -Title, -Message, -Image (mặc định: chọn ngẫu nhiên 1 ảnh .png trong static\notify\mascots\;
  nếu thư mục rỗng/không có thì dùng static\notify\mascot.png), -Url (mở khi click phải), -NoSound
#>
param(
  [string]$Title = "Task Done",
  [string]$Message = "",
  [string]$Image = "",
  [string]$Url = "http://127.0.0.1:8080/dashboard/dashboard_process.html",
  [switch]$NoSound,
  [switch]$Child
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Image) {
  # Không truyền -Image: chọn ngẫu nhiên 1 ảnh .png trong static\notify\mascots\.
  # Thư mục rỗng hoặc không tồn tại thì dùng lại mascot.png như cũ (fallback).
  $mascotsDir = Join-Path (Split-Path -Parent $here) "static\notify\mascots"
  $fallbackImage = Join-Path (Split-Path -Parent $here) "static\notify\mascot.png"
  $mascotPool = @()
  if (Test-Path -LiteralPath $mascotsDir) {
    $mascotPool = @(Get-ChildItem -LiteralPath $mascotsDir -Filter '*.png' -File -ErrorAction SilentlyContinue)
  }
  if ($mascotPool.Count -gt 0) {
    $Image = ($mascotPool | Get-Random).FullName
  } else {
    $Image = $fallbackImage
  }
}

# Lần gọi đầu: tự chạy lại ở tiến trình riêng (STA, ẩn cửa sổ console) rồi trả về ngay, không chặn agent.
if (-not $Child) {
  # Mỗi giá trị đặt trong ngoặc kép (có dấu cách / tiếng Việt); bỏ ngoặc kép bên trong để khỏi vỡ tham số.
  function Q([string]$v) { '"' + ($v -replace '"', "'") + '"' }
  $argStr = '-NoProfile -STA -WindowStyle Hidden -ExecutionPolicy Bypass -File ' + (Q $MyInvocation.MyCommand.Path) +
            ' -Title ' + (Q $Title) + ' -Message ' + (Q $Message) + ' -Image ' + (Q $Image) + ' -Url ' + (Q $Url) + ' -Child'
  if ($NoSound) { $argStr += ' -NoSound' }
  Start-Process -FilePath 'powershell.exe' -ArgumentList $argStr -WindowStyle Hidden | Out-Null
  return
}

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

$w = New-Object System.Windows.Window
$w.WindowStyle = 'None'; $w.AllowsTransparency = $true; $w.Background = 'Transparent'
$w.Topmost = $true; $w.ShowInTaskbar = $false; $w.ResizeMode = 'NoResize'
$w.SizeToContent = 'WidthAndHeight'; $w.Cursor = 'Hand'; $w.Opacity = 0

$stack = New-Object System.Windows.Controls.StackPanel

# Bong bóng lời thoại
$bubble = New-Object System.Windows.Controls.Border
$bubble.CornerRadius = 12; $bubble.Padding = '12,8,12,8'; $bubble.Margin = '0,0,0,4'
$bubble.Background = New-Object System.Windows.Media.SolidColorBrush ([System.Windows.Media.Color]::FromArgb(235, 22, 28, 45))
$bubble.BorderBrush = New-Object System.Windows.Media.SolidColorBrush ([System.Windows.Media.Color]::FromRgb(245, 158, 11))
$bubble.BorderThickness = 1.5; $bubble.MaxWidth = 280; $bubble.HorizontalAlignment = 'Center'
$tp = New-Object System.Windows.Controls.StackPanel
$t1 = New-Object System.Windows.Controls.TextBlock
$t1.Text = "Tiểu Thiên: ✔ " + $Title; $t1.FontSize = 15; $t1.FontWeight = 'Bold'; $t1.Foreground = '#FBBF24'; $t1.TextWrapping = 'Wrap'
$tp.Children.Add($t1) | Out-Null
if ($Message) {
  $t2 = New-Object System.Windows.Controls.TextBlock
  $t2.Text = $Message; $t2.FontSize = 12.5; $t2.Foreground = '#E5E7EB'; $t2.TextWrapping = 'Wrap'; $t2.Margin = '0,3,0,0'
  $tp.Children.Add($t2) | Out-Null
}
$t3 = New-Object System.Windows.Controls.TextBlock
$t3.Text = "(click để ẩn · chuột phải mở Dashboard)"; $t3.FontSize = 10; $t3.Foreground = '#94A3B8'; $t3.Margin = '0,4,0,0'
$tp.Children.Add($t3) | Out-Null
$bubble.Child = $tp
$stack.Children.Add($bubble) | Out-Null

# Nhân vật
if (Test-Path -LiteralPath $Image) {
  $bmp = New-Object System.Windows.Media.Imaging.BitmapImage
  $bmp.BeginInit(); $bmp.UriSource = New-Object System.Uri ((Resolve-Path -LiteralPath $Image).Path); $bmp.CacheOption = 'OnLoad'; $bmp.EndInit()
  $img = New-Object System.Windows.Controls.Image
  $img.Source = $bmp; $img.Height = 240; $img.HorizontalAlignment = 'Center'
  [System.Windows.Media.RenderOptions]::SetBitmapScalingMode($img, 'HighQuality')
  $stack.Children.Add($img) | Out-Null
}
$w.Content = $stack

# Đặt ở góc phải dưới, ngay trên thanh taskbar (cạnh khay hệ thống)
$w.Add_Loaded({
  $wa = [System.Windows.SystemParameters]::WorkArea
  $w.Left = $wa.Right - $w.ActualWidth - 12
  $w.Top  = $wa.Bottom - $w.ActualHeight - 6
  $fade = New-Object System.Windows.Media.Animation.DoubleAnimation(0, 1, [TimeSpan]::FromMilliseconds(350))
  $w.BeginAnimation([System.Windows.Window]::OpacityProperty, $fade)
  if (-not $NoSound) {
    # Admin chốt 2026-10-15: Task Done thì kêu 3 lần "ting ting"
    for ($k = 0; $k -lt 3; $k++) {
      try { [System.Media.SystemSounds]::Asterisk.Play() } catch {}
      try { [console]::Beep(1568, 110); [console]::Beep(2093, 220) } catch {}
      Start-Sleep -Milliseconds 350
    }
  }
})

# Click trái = ẩn; click phải = mở Dashboard rồi ẩn
$w.Add_MouseLeftButtonUp({ $w.Close() })
$w.Add_MouseRightButtonUp({ try { Start-Process $Url } catch {}; $w.Close() })

$app = New-Object System.Windows.Application
$app.ShutdownMode = 'OnMainWindowClose'
[void]$app.Run($w)

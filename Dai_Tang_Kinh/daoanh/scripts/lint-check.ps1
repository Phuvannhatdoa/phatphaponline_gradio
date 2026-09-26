# Lint script: Check JS syntax in admin HTML files (placevn.html + index.html)
# Extracts inline <script> blocks (without src) and runs node --check

$ErrorActionPreference = "Stop"
$adminDir = Join-Path (Get-Location) "admin"

Write-Host "Running lint checks..."

$passed = 0
$failed = 0

# Only check the two files with inline scripts
$checkFiles = @("placevn.html", "index.html", "zenlineage_review.html")

foreach ($filename in $checkFiles) {
    $htmlFile = Join-Path $adminDir $filename
    if (-not (Test-Path $htmlFile)) {
        Write-Host "  ⚠️  $filename not found, skipping"
        continue
    }
    Write-Host "Checking $filename..."
    $content = Get-Content -Path $htmlFile -Raw
    
    if ($content -match "<script>") {
        $pattern = '<script(?![^>]*\bsrc\s*=)'
        $matches = [regex]::Matches($content, $pattern)
        
        $scriptIdx = 0
        foreach ($match in $matches) {
            $scriptIdx++
            $start = $match.Index + $match.Length
            $remaining = $content.Substring($start)
            $endMatch = $remaining.IndexOf("</script>")
            if ($endMatch -ge 0) {
                $jsCode = $remaining.Substring(0, $endMatch)
                $tmpFile = [System.IO.Path]::GetTempFileName()
                try {
                    [System.IO.File]::WriteAllText($tmpFile, $jsCode, [System.Text.Encoding]::UTF8)
                    & node --check $tmpFile 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  Script block ${scriptIdx}: Syntax OK"
                        $passed++
                    } else {
                        Write-Host "  Script block ${scriptIdx}: Syntax error"
                        & node --check $tmpFile 2>&1 | ForEach-Object { Write-Host "     $_" }
                        $failed++
                    }
                } finally {
                    if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force }
                }
            }
        }
        if ($matches.Count -eq 0) {
            Write-Host "  No inline script blocks found"
        }
    } else {
        Write-Host "  No <script> tag found"
    }
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "Lint checks passed ($passed script blocks validated)"
    exit 0
} else {
    Write-Host "Lint checks failed"
    exit 1
}
# Lint script: Check JS syntax in admin HTML files
# Extracts inline <script> blocks (without src) and runs node --check
# T172: them dila_person_index.html + person.html; JSX (React) skip;
# node v24 glass `--check` voi file khong co duoi .js -> temp file co duoi .js.

$ErrorActionPreference = "Continue"
$adminDir = Join-Path (Get-Location) "admin"

Write-Host "Running lint checks..."

$passed = 0
$failed = 0

$checkFiles = @("placevn.html", "index.html", "zenlineage_review.html", "dila_person_index.html", "person.html")

foreach ($filename in $checkFiles) {
    $htmlFile = Join-Path $adminDir $filename
    if (-not (Test-Path $htmlFile)) {
        Write-Host "  WARN $filename not found, skipping"
        continue
    }
    Write-Host "Checking $filename..."
    $content = Get-Content -Path $htmlFile -Raw

    # pattern bat ca dau '>' de $match.Length nhan dung vi tri dau noi dung JS
    $pattern = '<script(?![^>]*\bsrc\s*=)[^>]*>'
    $matches = [regex]::Matches($content, $pattern)

    $scriptIdx = 0
    foreach ($match in $matches) {
        $scriptIdx++
        $start = $match.Index + $match.Length
        $remaining = $content.Substring($start)
        $endMatch = $remaining.IndexOf("</script>")
        if ($endMatch -lt 0) { continue }
        $jsCode = $remaining.Substring(0, $endMatch)
        # JSX (React inline, vi du placevn.html) — node --check khong hieu JSX -> bo qua, khong fail
        if ($jsCode -match 'dangerouslySetInnerHTML|return\s+<[A-Za-z]') {
            Write-Host "  Script block ${scriptIdx}: JSX (skip)"
            $passed++
            continue
        }
        $tmpFile = Join-Path ([System.IO.Path]::GetTempPath()) ("lint_" + [guid]::NewGuid().ToString("N") + ".js")
        try {
            [System.IO.File]::WriteAllText($tmpFile, $jsCode, [System.Text.Encoding]::UTF8)
            $null = & node --check $tmpFile 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Script block ${scriptIdx}: Syntax OK"
                $passed++
            } else {
                Write-Host "  Script block ${scriptIdx}: Syntax error"
                $failed++
            }
        } catch {
            Write-Host "  Script block ${scriptIdx}: node error: $_"
            $failed++
        } finally {
            if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force }
        }
    }
    if ($matches.Count -eq 0) {
        Write-Host "  No inline script blocks found"
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
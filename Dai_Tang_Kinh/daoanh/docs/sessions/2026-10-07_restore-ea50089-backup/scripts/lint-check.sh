#!/bin/bash
# Lint script: Extract JS from HTML and check syntax
set -e

echo "Running lint checks..."

# Check each HTML file
for html_file in admin/*.html; do
  echo "Checking $html_file..."
  
  # Extract content between <script> tags (not src scripts)
  # Using sed to extract inline scripts
  if grep -q "<script>" "$html_file"; then
    # Create temp JS file
    tmp_file=$(mktemp /tmp/lint-check-XXXXXX.js)
    
    # Extract JS between <script> and </script> (not src scripts)
    sed -n '/<script>/,/<\/script>/p' "$html_file" | sed '/^[[:space:]]*<script>$/d; /^[[:space:]]*<\/script>$/d' > "$tmp_file"
    
    # Check syntax with node --check
    if node --check "$tmp_file" 2>/dev/null; then
      echo "  ✅ $html_file: Syntax OK"
    else
      echo "  ❌ $html_file: Syntax error"
      node --check "$tmp_file" 2>&1 | head -3
      rm -f "$tmp_file"
      exit 1
    fi
    
    rm -f "$tmp_file"
  else
    echo "  ⚠️  No inline script found in $html_file"
  fi
done

echo ""
echo "✅ All lint checks passed!"

#!/usr/bin/env bash
# Lightweight, deterministic session-status updater. No model calls, no cost.
set -uo pipefail
REPO="$(git -C /home/user/phatphaponline_gradio rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO" ] && exit 0
cd "$REPO" || exit 0

FILE="SESSION.md"
START="<!-- AUTO-STATUS-START -->"
END="<!-- AUTO-STATUS-END -->"
TS="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
HEAD_LOG="$(git log -5 --oneline 2>/dev/null)"
DIRTY="$(git status --porcelain 2>/dev/null)"
[ -z "$DIRTY" ] && DIRTY_STATUS="clean" || DIRTY_STATUS="co thay doi chua commit"

BLOCK="$START
## Trang thai tu dong (cap nhat: ${TS})
- Branch: ${BRANCH}
- Working tree: ${DIRTY_STATUS}
- 5 commit gan nhat:
\`\`\`
${HEAD_LOG}
\`\`\`
${END}"

if [ ! -f "$FILE" ]; then
  printf '%s\n' "$BLOCK" > "$FILE"
  exit 0
fi

if grep -q "$START" "$FILE" 2>/dev/null; then
  python3 - "$FILE" "$START" "$END" "$BLOCK" <<'PYEOF'
import sys
path, start, end, block = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
pre, _, rest = content.partition(start)
_, _, post = rest.partition(end)
new_content = pre + block + post
with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)
PYEOF
else
  printf '\n%s\n' "$BLOCK" >> "$FILE"
fi
exit 0

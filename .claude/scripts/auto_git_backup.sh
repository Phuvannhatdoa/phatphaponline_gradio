#!/usr/bin/env bash
# Auto-commit + push after Claude edits a file. Never fails the hook (always exit 0).
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# Nothing staged/changed -> nothing to do
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  exit 0
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
[ -z "$BRANCH" ] && exit 0

git add -A

# Still nothing staged after add (e.g. only ignored files changed)
git diff --cached --quiet && exit 0

TS="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
git commit -q -m "$(cat <<EOF
Auto-backup: working changes at ${TS}

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019mr3FG3wwWHcqmxTZx4hpu
EOF
)" >/dev/null 2>&1

git push -u origin "$BRANCH" >/dev/null 2>&1

exit 0

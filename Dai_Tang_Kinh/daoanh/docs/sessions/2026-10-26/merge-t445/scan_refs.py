# -*- coding: utf-8 -*-
"""Read-only: liệt kê tham chiếu T445 / T463 theo file:dòng (không ghi gì)."""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.abspath(os.path.join(ROOT, "..", "..", "..", ".."))
PATTERNS = sys.argv[1:] or ["T445", "T463"]

TARGETS = [
    "docs/tasktodo.md",
    "docs/ROLLBACK.md",
    "app.py",
]
TARGET_GLOBS = [
    "docs/Handoff-*.md",
    "tasks/*.md",
    "scripts/*.py",
    "admin/*.html",
]

files = []
for t in TARGETS:
    p = os.path.join(DAOANH, t)
    if os.path.isfile(p):
        files.append(p)
for g in TARGET_GLOBS:
    files.extend(sorted(glob.glob(os.path.join(DAOANH, g))))

for pat in PATTERNS:
    rx = re.compile(r"(?<![A-Za-z0-9_-])" + pat + r"(?![0-9])")
    print("=== PATTERN", pat, "===")
    total = 0
    for f in files:
        try:
            lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                total += 1
                rel = os.path.relpath(f, DAOANH).replace("\\", "/")
                print(f"{rel}:{i}: {line.strip()[:160]}")
    print("TOTAL", pat, total)

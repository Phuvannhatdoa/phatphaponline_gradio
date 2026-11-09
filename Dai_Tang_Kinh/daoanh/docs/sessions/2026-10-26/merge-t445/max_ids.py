# -*- coding: utf-8 -*-
"""Read-only: max ID trong tasks/ + docs/ (prose + frontmatter) và kiểm ID ứng viên."""
import os
import re
import sys

DAOANH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
rx = re.compile(r"(?<![A-Za-z0-9_-])T(\d{3})(?![0-9])")
hits = {}  # num -> list of "file:line"
for base in ("tasks", "docs"):
    for dp, dn, fn in os.walk(os.path.join(DAOANH, base)):
        if "_book" in dp:
            continue
        for f in fn:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dp, f)
            try:
                lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                for m in rx.finditer(line):
                    n = int(m.group(1))
                    hits.setdefault(n, []).append(os.path.relpath(p, DAOANH).replace("\\", "/") + ":" + str(i))

print("MAX (tasks+docs, any mention):", max(hits))
top = sorted(hits)[-12:]
for n in top:
    print("T%d mentions=%d e.g. %s" % (n, len(hits[n]), hits[n][:2]))
cands = [int(a) for a in sys.argv[1:]]
for c in cands:
    print("CANDIDATE T%d mentions=%d" % (c, len(hits.get(c, []))))
    for x in hits.get(c, [])[:10]:
        print("   ", x)

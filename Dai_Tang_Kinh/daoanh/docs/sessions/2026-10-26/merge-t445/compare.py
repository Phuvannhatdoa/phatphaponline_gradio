# -*- coding: utf-8 -*-
"""Read-only: so sánh T445 (git HEAD, UTF-16) với T463 (worktree, UTF-8)."""
import os
import subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
DAOANH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
rel = "Dai_Tang_Kinh/daoanh/tasks/T445-placevn-wizard-ui-b0-b9.md"
blob = subprocess.run(["git", "show", "HEAD:" + rel], cwd=REPO, capture_output=True).stdout
print("T445 HEAD bytes:", len(blob), "BOM:", blob[:2])
t445 = blob.decode("utf-8").replace("\r\n", "\n")
t463 = open(os.path.join(DAOANH, "tasks", "T463-placevn-wizard-ui-b0-b9.md"), encoding="utf-8").read().replace("\r\n", "\n")
print("T463 wt bytes:", os.path.getsize(os.path.join(DAOANH, "tasks", "T463-placevn-wizard-ui-b0-b9.md")))


def fm(t):
    parts = t.split("---", 2)
    d = {}
    for line in parts[1].splitlines():
        if line and not line.startswith(" "):
            k, _, v = line.partition(":")
            d[k.strip()] = v.strip()
    return d


def heads(t):
    return [l for l in t.splitlines() if l.startswith("## ")]


a, b = fm(t445), fm(t463)
for k in sorted(set(a) | set(b)):
    print("FM", k, "| T445:", a.get(k, "-")[:70], "| T463:", b.get(k, "-")[:70])
print("T445 headings:", len(heads(t445)), "| T463 headings:", len(heads(t463)))
print("only in T445:", [h for h in heads(t445) if h not in heads(t463)])
print("only in T463:", [h for h in heads(t463) if h not in heads(t445)])
print("lines T445:", t445.count("\n"), "T463:", t463.count("\n"))

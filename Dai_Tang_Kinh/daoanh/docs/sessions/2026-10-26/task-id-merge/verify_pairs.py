# -*- coding: utf-8 -*-
# Verify: file moi (T442/T443/T444) la sieu tap cua file cu (T432/T433/T434 @ HEAD)
import os, subprocess, difflib, re
ROOT = "E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app"
D = "Dai_Tang_Kinh/daoanh/"
pairs = [
    ("tasks/T432-places-districts-claude-analysis.md", "tasks/T442-places-districts-claude-analysis.md"),
    ("tasks/T433-places-districts-claude-import.md", "tasks/T443-places-districts-claude-import.md"),
    ("tasks/T434-places-districts-gemini-batch.md", "tasks/T444-places-districts-gemini-batch.md"),
]
def head_blob(p):
    r = subprocess.run(["git", "show", "HEAD:" + D + p], cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
def wt(p):
    with open(os.path.join(ROOT, D, p), "r", encoding="utf-8", errors="replace") as f:
        return f.read()
def skip(line):
    s = line.strip()
    return bool(re.match(r"^id:\s*T4\d\d", s)) or bool(re.match(r"^#\s*T4\d\d\b", s))
for old, new in pairs:
    print("=== ", old, "->", new)
    print("old on disk:", os.path.exists(os.path.join(ROOT, D, old)), " new on disk:", os.path.exists(os.path.join(ROOT, D, new)))
    ob = head_blob(old)
    if ob is None:
        print("  !! old not in HEAD"); continue
    nw = wt(new)
    ol = [l for l in ob.splitlines() if l.strip() and not skip(l)]
    nl = set(l.rstrip() for l in nw.splitlines())
    missing = [l for l in ol if l.rstrip() not in nl]
    print("  old lines:", len(ol), " missing in new:", len(missing))
    for m in missing:
        print("   MISSING:", repr(m))
    if not missing:
        print("  => new is superset (ignoring id/header lines)")

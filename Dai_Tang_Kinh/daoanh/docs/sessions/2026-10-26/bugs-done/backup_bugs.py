import os
import shutil
import sys

SRC = os.path.join("docs", "bugs.md")
DST = os.path.join("docs", "sessions", "2026-10-26", "bugs-done", "bugs.before.md")

if not os.path.isfile(SRC):
    sys.exit("FAIL: source missing: " + SRC)

shutil.copy2(SRC, DST)

if not os.path.isfile(DST):
    sys.exit("FAIL: backup missing after copy")

s_src = os.path.getsize(SRC)
s_dst = os.path.getsize(DST)
if s_src != s_dst:
    sys.exit("FAIL: size mismatch src=%d dst=%d" % (s_src, s_dst))

with open(SRC, "rb") as a, open(DST, "rb") as b:
    if a.read() != b.read():
        sys.exit("FAIL: content mismatch")

print("OK backup", DST, "size", s_dst)

# -*- coding: utf-8 -*-
"""Chạy `npm run pipeline` và lưu log UTF-8 sạch (tránh PowerShell redirect -> UTF-16)."""
import os, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
os.chdir(DAO)
LOG = os.path.join(DAO, "docs", "sessions", "2026-10-28-commit", "pipeline.log")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print("running npm.cmd run pipeline ...")
r = subprocess.run(["npm.cmd", "run", "pipeline"], capture_output=True, cwd=DAO)
out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
with open(LOG, "w", encoding="utf-8", newline="\n") as f:
    f.write(out)
print("exit code:", r.returncode)
print("log:", LOG, os.path.getsize(LOG), "bytes")
lines = out.splitlines()
for l in lines[-25:]:
    print("  ", l[:170])

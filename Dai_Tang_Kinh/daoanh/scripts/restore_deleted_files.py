#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Khôi phục file bị xoá trong worktree từ HEAD blob (git show HEAD:<path>).
Bỏ qua: file nằm trong .gitignore; file có WIP của session khác (không chạm).
"""
import os, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
DAO = "Dai_Tang_Kinh/daoanh"

FILES = [
    "docs/Handoff-2026-10-28-t454.md",
    "docs/Handoff-2026-10-28-t455.md",
    "docs/Handoff-2026-10-28-t457.md",
    "docs/manifests/T457-manifest.json",
    "docs/sessions/2026-10-28-t454/apply.py",
    "docs/sessions/2026-10-28-t454/apply_simple.py",
    "docs/sessions/2026-10-28-t454/measure.py",
    "docs/sessions/2026-10-28-t454/t454_namevi_suffixed_20261028_190704.csv",
    "docs/sessions/2026-10-28-t455/plan.md",
    "docs/sessions/2026-10-28-t455/classify_out.txt",
    "docs/sessions/2026-10-28-t455/name_vi_mismatch_A.csv",
    "docs/sessions/2026-10-28-t455/name_vi_mismatch_B.csv",
    "docs/sessions/2026-10-28-t455/name_vi_mismatch_C.csv",
    "docs/sessions/2026-10-28-t457/dryrun_stats.py",
    "docs/sessions/2026-10-28-t457/dryrun_stats.txt",
    "docs/sessions/2026-10-28-t457/staging_output.txt",
    "docs/sessions/2026-10-28-t457/staging_v4_output.txt",
    "scripts/t454_cleanup_suffix.py",
    "scripts/t454_verify_state.py",
    "scripts/t455_check_state.py",
    "scripts/classify_t455.py",
    "scripts/t457_dila_bio_nexus_import.py",
    "scripts/t457_staging_v4.py",
    "scripts/t457_verify.py",
]

restored, skipped = 0, 0
for rel in FILES:
    path = DAO + "/" + rel
    wt = os.path.join(BASE, path.replace("/", os.sep))
    if os.path.exists(wt):
        print("skip (ton tai):", rel); skipped += 1; continue
    r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, cwd=BASE)
    if r.returncode != 0:
        print("FAIL (khong co trong HEAD):", rel); continue
    os.makedirs(os.path.dirname(wt), exist_ok=True)
    with open(wt, "wb") as f:
        f.write(r.stdout)
    print("restored %-70s %d bytes" % (rel, len(r.stdout)))
    restored += 1

print("\nrestored=%d skipped=%d" % (restored, skipped))

# --- kiểm tra worktree sạch so với HEAD cho các file này ---
r = subprocess.run(["git", "status", "--short", "--"] + [DAO + "/" + f for f in FILES],
                   capture_output=True, cwd=BASE)
print("\ngit status (nhóm file đã restore):")
print(r.stdout.decode() or "  (sach - khop HEAD)")

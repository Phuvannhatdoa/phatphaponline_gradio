#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T391 — move 8 oldest-month files (Apr 2026) into Backup-Old/ + manifest + restore.
Chạy từ repo root (visjs-app/):
  python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --dry-run
  python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --apply
  python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --restore
  python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --restore <relative_path>
"""
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # visjs-app/
DAOANH = REPO_ROOT / "Dai_Tang_Kinh" / "daoanh"
BACKUP_ROOT = REPO_ROOT / "Backup-Old"
DATE_TAG = "2026-10-14"
BACKUP_DIR = BACKUP_ROOT / DATE_TAG
MANIFEST_MD = BACKUP_DIR / f"MANIFEST-{DATE_TAG}.md"
MANIFEST_JSON = BACKUP_DIR / f"manifest-{DATE_TAG}.json"

# 8 files relative to DAOANH (Dai_Tang_Kinh/daoanh/)
FILES = [
    "DILA_Structure_Report.md",
    "FEATURE_PLAN.md",
    "QA2.md",
    "QA_REPORT_V2.md",
    "TASK_LOG_QA1.md",
    "TASK_LOG.md",
    "SYSTEM_MAP.md",
    "Timeline Tich Hop.md",
]

def sha256_16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

def tracked(rel: str) -> bool:
    # check if file is tracked in git (from repo root)
    import subprocess
    r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                       cwd=REPO_ROOT, capture_output=True)
    return r.returncode == 0

def build_manifest(rows, head_sha):
    lines = []
    lines.append(f"# MANIFEST — T391 dọn 8 file tháng 4/2026 ({DATE_TAG})\n")
    lines.append(f"HEAD trước move: `{head_sha}`")
    lines.append(f"Ngày tạo: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Script: `Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py`\n")
    lines.append("Khôi phục tất cả: `python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --restore`")
    lines.append("Khôi phục 1 file: `python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --restore <đường_dẫn_tương_đối_repo_root>`\n")
    lines.append("| # | Đường dẫn gốc (tương đối repo root) | Đường dẫn đích | Lý do | Byte | Git | sha256[:16] |\n|---|---|---|---|---:|---|---|")
    for i, r in enumerate(rows, 1):
        lines.append(f"| {i} | `{r['src']}` | `{r['dst']}` | {r['reason']} | {r['size']} | {'có' if r['tracked'] else 'không'} | `{r['hash']}` |")
    return "\n".join(lines)

def dry_run():
    print("=== DRY-RUN: 8 file sẽ move ===")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Đích: {BACKUP_DIR}")
    print()
    rows = []
    for f in FILES:
        src = DAOANH / f
        if not src.exists():
            print(f"  ⚠ KHÔNG TỒN TẠI: {f}")
            continue
        size = src.stat().st_size
        h = sha256_16(src)
        tr = "có" if tracked(f"Dai_Tang_Kinh/daoanh/{f}") else "không"
        dst = BACKUP_DIR / f
        print(f"  {f:30s}  {size:>10,} B  git={tr:3s}  sha256[:16]={h}")
        rows.append({"src": f"Dai_Tang_Kinh/daoanh/{f}", "dst": str(dst.relative_to(REPO_ROOT)),
                     "reason": "Nội dung đã hợp nhất vào docs/DEV_HISTORY.md",
                     "size": size, "tracked": tr == "có", "hash": h})
    print(f"\nTổng: {len(rows)} file, {sum(r['size'] for r in rows):,} byte")
    return rows

def apply(rows, auto_yes=False):
    if not auto_yes:
        confirm = input("\nXác nhận move? (y/N): ").strip().lower()
        if confirm != "y":
            print("Huỷ")
            return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    # move each file
    for r in rows:
        src = REPO_ROOT / r["src"]
        dst = REPO_ROOT / r["dst"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"  moved: {r['src']} -> {r['dst']}")
    # write manifests
    import subprocess
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                          capture_output=True, text=True).stdout.strip()
    md = build_manifest(rows, head)
    MANIFEST_MD.write_text(md, encoding="utf-8")
    MANIFEST_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest: {MANIFEST_MD}")
    print(f"Manifest JSON: {MANIFEST_JSON}")
    # add Backup-Old to repo-root .gitignore
    gi = REPO_ROOT / ".gitignore"
    txt = gi.read_text(encoding="utf-8")
    if "Backup-Old/" not in txt:
        with gi.open("a", encoding="utf-8") as f:
            f.write("\n# T391 backup folder\nBackup-Old/\n")
        print("Added Backup-Old/ to .gitignore")

def restore_one(rel_path: str):
    # find the entry in manifest
    if not MANIFEST_JSON.exists():
        print("Không tìm thấy manifest.json")
        return False
    rows = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    row = next((r for r in rows if r["src"] == rel_path), None)
    if not row:
        print(f"  ✗ Không tìm thấy trong manifest: {rel_path}")
        return False
    # backup file is at BACKUP_DIR / basename(dst)
    backup_file = BACKUP_DIR / Path(row["dst"]).name
    if not backup_file.exists():
        print(f"  ✗ Không tìm thấy trong backup: {backup_file}")
        return False
    dst = REPO_ROOT / rel_path
    if dst.exists():
        # hash guard
        h_src = sha256_16(backup_file)
        h_dst = sha256_16(dst)
        if h_src != h_dst:
            print(f"  ✗ DRIFT: hash khác — src={h_src} dst={h_dst}. Không ghi đè.")
            return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(backup_file), str(dst))
    print(f"  restored: {rel_path}")
    return True

def restore_all():
    if not MANIFEST_JSON.exists():
        print("Không tìm thấy manifest.json")
        return
    rows = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    ok = fail = 0
    for r in rows:
        if restore_one(r["src"]):
            ok += 1
        else:
            fail += 1
    print(f"\nDone: restored={ok}, failed={fail}")

def main():
    if "--dry-run" in sys.argv:
        dry_run()
    elif "--apply" in sys.argv:
        rows = dry_run()
        if not rows:
            print("Không có file để move")
            return
        auto_yes = "--yes" in sys.argv
        apply(rows, auto_yes=auto_yes)
        print("Done. Kiểm tra `git status --short` rồi commit.")
    elif "--restore" in sys.argv:
        # args after --restore
        idx = sys.argv.index("--restore")
        args = sys.argv[idx+1:]
        if args:
            restore_one(args[0])
        else:
            restore_all()
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
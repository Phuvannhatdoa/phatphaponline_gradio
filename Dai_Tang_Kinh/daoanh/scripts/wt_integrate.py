"""Tích hợp một nhánh worktree vào cây chính — CHỈ điều phối chạy.

Usage:
  python -X utf8 scripts/wt_integrate.py <tên-việc>

Quy trình:
1. Kiểm nhánh wt/<tên-việc> tồn tại và worktree của nó sạch (đã commit hết).
2. Tạo khóa C:/Users/Nam Thien/.claude/integration.lock (hook cho phép ghi cây chính
   khi khóa còn mới, tối đa 20 phút).
3. git merge --no-ff --no-edit wt/<tên-việc> trong cây chính.
   Nếu xung đột hoặc git từ chối (file đang có WIP chồng lên): DỪNG, không ép.
4. Luôn xóa khóa ở bước cuối (finally).

Không dùng stash, reset, checkout, hay ghi đè. Nếu merge thất bại, git tự giữ nguyên
cây chính; điều phối báo lại để xử lý.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # visjs-app
WT_ROOT = Path("C:/Users/Nam Thien/.claude/worktrees")
LOCK = Path("C:/Users/Nam Thien/.claude/integration.lock")


def git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r"[A-Za-z0-9._-]{2,60}", argv[1]):
        print(__doc__)
        return 1
    name = argv[1]
    branch = f"wt/{name}"
    wt = WT_ROOT / name

    if git("rev-parse", "--verify", branch).returncode != 0:
        print(f"Không có nhánh {branch}.")
        return 1
    if not wt.exists():
        print(f"Không có worktree {wt}.")
        return 1
    st = git("status", "--porcelain", cwd=wt).stdout.strip()
    if st:
        print("Worktree chưa commit hết, dừng:\n" + st)
        return 1

    LOCK.write_text(f"integrate {name} {os.getpid()}\n", encoding="utf-8")
    try:
        r = git("merge", "--no-ff", "--no-edit", branch)
        print(r.stdout.strip())
        if r.returncode != 0:
            print("MERGE THẤT BẠI — dừng, không ép. Chi tiết:\n" + r.stderr.strip())
            return 2
        print(f"Đã tích hợp {branch} vào cây chính.")
        return 0
    finally:
        try:
            LOCK.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))

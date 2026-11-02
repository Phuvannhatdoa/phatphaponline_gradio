"""Tạo worktree riêng cho một agent/việc, từ HEAD hiện tại của cây chính.

Usage:
  python -X utf8 scripts/wt_new.py <tên-việc>

Tạo: C:/Users/Nam Thien/.claude/worktrees/<tên-việc> trên nhánh wt/<tên-việc>.
Agent PHẢI làm mọi thay đổi trong worktree đó. Cây chính chỉ nhận thay đổi qua
scripts/wt_integrate.py (điều phối chạy, có khóa).
Không đụng cây chính: chỉ thêm worktree + nhánh mới.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # visjs-app (git toplevel)
WT_ROOT = Path("C:/Users/Nam Thien/.claude/worktrees")


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r"[A-Za-z0-9._-]{2,60}", argv[1]):
        print(__doc__)
        return 1
    name = argv[1]
    path = WT_ROOT / name
    if path.exists():
        print(f"Đã tồn tại: {path}. Chọn tên khác.")
        return 1
    WT_ROOT.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "worktree", "add", "-b", f"wt/{name}", str(path), "HEAD"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip())
        return 1
    print(f"Worktree: {path}\nNhánh: wt/{name}\nBase: HEAD ({REPO.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

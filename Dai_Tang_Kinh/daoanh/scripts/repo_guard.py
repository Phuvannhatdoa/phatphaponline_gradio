# -*- coding: utf-8 -*-
"""repo_guard.py - T155 - Bao ve SSOT repo root cho Dao Anh (Phat To Dao Anh).

Muc tieu (chong tai phat):
  1) Khang dinh `git rev-parse --show-toplevel` == visjs-app root
     (khong go tay path: tinh tu vi tri file script).
  2) FAIL neu phat hien `.git/HEAD` that trong Dai_Tang_Kinh/daoanh/
     -> nguy co tai lap repo long nhau, tach lich su git.

Chay: python -X utf8 scripts/repo_guard.py   (hoac `npm run guard`)
Exit: 0 = PASS, 1 = FAIL (pipeline dung som).
"""
import subprocess
import sys
from pathlib import Path

# scripts/ -> daoanh/ -> Dai_Tang_Kinh/ -> visjs-app/
DAOANH = Path(__file__).resolve().parents[1]
EXPECTED_ROOT = Path(__file__).resolve().parents[3]


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def main():
    rc = 0

    # 1. SSOT repo root
    proc = _run(["git", "rev-parse", "--show-toplevel"], EXPECTED_ROOT)
    if proc.returncode != 0:
        print("[FAIL] Khong chay duoc: git rev-parse --show-toplevel")
        print("       stderr:", proc.stderr.strip())
        return 1
    actual = Path(proc.stdout.strip()).resolve()
    if actual != EXPECTED_ROOT:
        print("[FAIL] SSOT repo root KHONG khop.")
        print("       mong doi:", EXPECTED_ROOT)
        print("       thuc te :", actual)
        rc = 1
    else:
        print("[OK] SSOT repo root =", actual)

    # 2. .git hong trong daoanh
    bad_head = DAOANH / ".git" / "HEAD"
    if bad_head.exists():
        print("[FAIL] Phat hien .git THAT trong", DAOANH)
        print("       -> nguy co tach lich su git. Xem T155 / AGENTS.md.")
        rc = 1
    else:
        print("[OK] Khong co .git that trong Dai_Tang_Kinh/daoanh/")

    return rc


if __name__ == "__main__":
    sys.exit(main())

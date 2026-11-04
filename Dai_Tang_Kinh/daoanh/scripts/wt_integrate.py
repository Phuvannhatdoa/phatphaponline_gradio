"""Tích hợp một nhánh worktree vào cây chính — CHỈ điều phối chạy.

Usage:
  python -X utf8 scripts/wt_integrate.py <tên-nhánh>
  Ví dụ: t53-cbeta-content-enhancement, hoặc wt/<tên-việc> (dạng cũ).

Quy trình:
1. Kiểm nhánh <tên-nhánh> tồn tại và worktree đang giữ nó sạch (đã commit hết).
2. Tạo khóa C:/Users/Nam Thien/.claude/integration.lock dạng JSON gồm PID, token và
   thời hạn 5 phút. Tạo bằng cờ độc quyền: nếu đã có khóa còn hạn và PID còn sống thì
   từ chối, không ghi đè. Khóa mồ côi (hết hạn hoặc PID đã chết) được dọn rồi tạo lại.
3. git merge --no-ff --no-edit wt/<tên-việc> trong cây chính.
   Nếu xung đột hoặc git từ chối (file đang có WIP chồng lên): DỪNG, không ép.
4. Luôn xóa khóa ở bước cuối, và chỉ xóa khi token trong file vẫn là token của mình.

Không dùng stash, reset, checkout, hay ghi đè. Nếu merge thất bại, git tự giữ nguyên
cây chính; điều phối báo lại để xử lý.
"""
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # visjs-app
WT_ROOT = Path("C:/Users/Nam Thien/.claude/worktrees")
LOCK = Path("C:/Users/Nam Thien/.claude/integration.lock")
LOCK_TTL = 5 * 60                                    # giây; khớp với hook guard_main_tree.py


def git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def pid_alive(pid):
    """Kiểm PID còn chạy trên Windows bằng API hệ thống (không dùng os.kill: trên Windows
    os.kill với tín hiệu 0 có thể kết thúc tiến trình)."""
    import ctypes
    STILL_ACTIVE = 259
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        return code.value == STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def read_lock():
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def lock_live(data):
    return bool(data) and time.time() < data.get("expires", 0) and pid_alive(data.get("pid", -1))


def acquire(name):
    """Trả về token nếu lấy được khóa, None nếu đang có khóa còn hiệu lực."""
    token = secrets.token_hex(16)
    payload = json.dumps({"pid": os.getpid(), "token": token, "name": name,
                          "expires": time.time() + LOCK_TTL})
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if lock_live(read_lock()):
                return None
            LOCK.unlink(missing_ok=True)              # khóa mồ côi: dọn rồi thử lại
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        return token
    return None


def release(token):
    data = read_lock()
    if data and data.get("token") == token:           # không xóa khóa của tiến trình khác
        LOCK.unlink(missing_ok=True)


def branch_worktree(branch):
    """Đường dẫn worktree đang giữ nhánh này, hoặc None (đọc từ git, không ghép đường dẫn)."""
    found = None
    for block in git("worktree", "list", "--porcelain").stdout.split("\n\n"):
        lines = block.splitlines()
        wt_line = next((l for l in lines if l.startswith("worktree ")), None)
        if wt_line and f"branch refs/heads/{branch}" in lines:
            found = Path(wt_line[len("worktree "):])
    return found


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r"(wt/)?[A-Za-z0-9._-]{2,60}", argv[1]):
        print(__doc__)
        return 1
    # Nhận cả hai dạng: "wt/<tên>" (cũ) và "<tên>" như t53-cbeta-content-enhancement (mới).
    branch = argv[1]
    name = branch[3:] if branch.startswith("wt/") else branch
    if not re.fullmatch(r"[A-Za-z0-9._-]{2,60}", name):
        print(__doc__)
        return 1
    # Nhánh mới phải là t<số>-<mô tả> (chữ thường), ví dụ t53-cbeta-content-enhancement.
    if not branch.startswith("wt/") and not re.fullmatch(r"t\d+-[a-z0-9][a-z0-9-]*", branch):
        print(f"Tên nhánh {branch} không đúng dạng t<số>-<mô tả>.")
        return 1

    if git("rev-parse", "--verify", f"refs/heads/{branch}").returncode != 0:
        print(f"Không có nhánh {branch}.")
        return 1
    wt = branch_worktree(branch)
    if wt is None or not wt.exists():
        print(f"Không có worktree nào đang giữ nhánh {branch}.")
        return 1
    st = git("status", "--porcelain", cwd=wt).stdout.strip()
    if st:
        print("Worktree chưa commit hết, dừng:\n" + st)
        return 1

    token = acquire(name)
    if token is None:
        print("Đang có một tích hợp khác giữ khóa còn hiệu lực, dừng.")
        return 3
    try:
        r = git("merge", "--no-ff", "--no-edit", branch)
        print(r.stdout.strip())
        if r.returncode != 0:
            print("MERGE THẤT BẠI — dừng, không ép. Chi tiết:\n" + r.stderr.strip())
            return 2
        print(f"Đã tích hợp {branch} vào cây chính.")
        return 0
    finally:
        release(token)


if __name__ == "__main__":
    # Console Windows (cp1252) không in được tiếng Việt: thay ký tự lỗi thay vì dừng sau khi merge xong.
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
    sys.exit(main(sys.argv))

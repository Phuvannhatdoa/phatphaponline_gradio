"""PreToolUse guard: chặn ghi vào CÂY CHÍNH (main worktree) của repo visjs-app.

Quy tắc:
- Mọi agent/phiên phải làm việc trong git worktree riêng (ví dụ
  C:/Users/Nam Thien/.claude/worktrees/<tên>). Ghi vào cây chính bị chặn.
- Ngoại lệ DUY NHẤT: điều phối tích hợp, khi có file khóa
  C:/Users/Nam Thien/.claude/integration.lock còn mới (<= 20 phút). Lock do
  scripts/wt_integrate.py tạo và xóa sau khi xong.
- Đường dẫn ngoài cây chính (worktree, scratchpad, temp) không bị chặn.

Đầu vào: JSON trên stdin (tool_name, tool_input, cwd). Exit 2 = chặn, stderr
là lý do hiển thị cho agent.
"""
import json
import os
import re
import sys
import time

MAIN = os.path.normcase(os.path.abspath(
    "E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app")).replace("\\", "/")
LOCK = "C:/Users/Nam Thien/.claude/integration.lock"
LOCK_TTL = 20 * 60

WRITE_VERB = re.compile(
    r"(^|[\s;&|(])(cp|mv|rm|del|tee|touch|mkdir|sed\s+-i|Set-Content|Out-File|Add-Content|"
    r"Remove-Item|Move-Item|Copy-Item|New-Item|git\s+(add|commit|reset|checkout|restore|stash|"
    r"merge|rebase|cherry-pick|apply|am|pull|clean|revert|rm|mv|update-index|update-ref|branch\s+-[dD]))"
    r"(\s|$)|>>?\s*[^&\s]"
)


def norm(p):
    return os.path.normcase(os.path.abspath(p)).replace("\\", "/")


def in_main(path):
    p = norm(path)
    return p == MAIN or p.startswith(MAIN + "/")


def lock_fresh():
    try:
        return time.time() - os.path.getmtime(LOCK) <= LOCK_TTL
    except OSError:
        return False


def block(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}
    cwd = data.get("cwd", "") or ""

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target = inp.get("file_path") or inp.get("notebook_path") or ""
        if target and in_main(target) and not lock_fresh():
            block(f"CHẶN: ghi vào cây chính ({target}). Làm việc trong worktree riêng "
                  f"(git worktree add), rồi điều phối tích hợp. Xem wt_new.py.")
        return

    if tool in ("Bash", "PowerShell"):
        cmd = inp.get("command", "") or ""
        cmd_norm = cmd.replace("\\", "/")
        cwd_in_main = in_main(cwd) if cwd else False
        # So chuỗi đường dẫn thuần, KHÔNG dùng abspath (abspath ghép với cwd của hook — gây chặn nhầm).
        mentions_main = MAIN.lower() in cmd_norm.lower() or "visjs-app" in cmd_norm.lower()
        writes = bool(WRITE_VERB.search(cmd))
        # Lệnh git ghi chạy trong cây chính, hoặc ghi bằng đường dẫn tương đối từ cây chính
        # (không có ổ đĩa): chặn. Ghi sang đường dẫn tuyệt đối ngoài cây chính: cho qua.
        has_abs_drive = bool(re.search(r"[A-Za-z]:/", cmd_norm))
        git_write = bool(re.search(r"git\s+(add|commit|reset|checkout|restore|stash|merge|rebase|"
                                   r"cherry-pick|apply|am|pull|clean|revert|update-index|update-ref)\b", cmd))
        # Chỉ chặn lệnh git ghi chạy trong cây chính. Lệnh ghi thường (cp, >, ...) không
        # nhắc đường dẫn cây chính thì được phép: nếu không, mọi lệnh trong cây chính bị chặn nhầm.
        risky_in_main = cwd_in_main and git_write
        if writes and (mentions_main or risky_in_main) and not lock_fresh():
            block("CHẶN: lệnh ghi/git thay đổi cây chính. Chạy trong worktree riêng; "
                  "tích hợp vào cây chính chỉ qua scripts/wt_integrate.py.")
        return


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # không để lỗi hook chặn nhầm công việc hợp lệ
        sys.stderr.write(f"guard_main_tree: lỗi nội bộ, bỏ qua: {e}\n")
        sys.exit(0)

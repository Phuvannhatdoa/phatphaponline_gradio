"""check_orca_guard.py — Guard chỉ-đọc cho quy trình Orca/OpenCode.

Mục đích: kiểm tra (không ghi gì) hai điều kiện an toàn mô tả trong
`docs/process/ORCA_WORKFLOW.md`:

1. Agent task không được commit/làm việc trực tiếp trên nhánh chính
   (`truyen-dang-the-pho-clean` hoặc `main`) từ một worktree task.
2. Lệnh `--apply` (ghi DB) không được chạy khi chưa có file duyệt
   `approvals/<Txxx>.approved` của Admin.

Script này KHÔNG tự gắn vào bất kỳ pipeline ghi DB nào (ví dụ các script
T53). Nó chỉ cung cấp hai hàm kiểm tra + một CLI mỏng để agent/Orca gọi
thủ công trước khi quyết định hành động.

Cách dùng (CLI):
    python scripts/check_orca_guard.py --check-branch
        -> exit code 0 nếu nhánh hiện tại an toàn (không phải nhánh chính),
           exit code 1 + thông báo lỗi nếu đang ở truyen-dang-the-pho-clean/main.

    python scripts/check_orca_guard.py --check-approval T53
        -> exit code 0 nếu approvals/T53.approved tồn tại, exit code 1 nếu không.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Console Windows mặc định dùng cp1252, không in được chữ Việt có dấu.
# Ép lại stdout/stderr sang UTF-8 (an toàn: bỏ qua nếu môi trường không hỗ trợ,
# ví dụ khi stdout đã bị capture bởi test runner dưới dạng không phải TextIOWrapper).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# Các nhánh chính không bao giờ được commit trực tiếp từ worktree của 1 task.
PROTECTED_BRANCHES = {"truyen-dang-the-pho-clean", "main"}

# Thư mục chứa file duyệt của Admin, tính tương đối theo repo root (daoanh/).
APPROVALS_DIRNAME = "approvals"

# task_id hợp lệ chỉ gồm chữ "T" + số (ví dụ T53, T404). Chặn mọi ký tự khác
# (path traversal như "../x", khoảng trắng, dấu "/", v.v.) trước khi ghép path.
TASK_ID_RE = re.compile(r"T\d+\Z")  # \Z: không chấp nhận ký tự xuống dòng cuối như $


def _repo_root(start: Path | None = None) -> Path:
    """Tìm root của repo (daoanh/) bằng cách đi lên từ file này.

    Không gọi git ở đây — chỉ dùng vị trí file, vì script này phải chạy
    được cả khi không có .git (ví dụ trong môi trường test với tempdir).
    """
    here = start if start is not None else Path(__file__).resolve()
    # scripts/check_orca_guard.py -> parent.parent = daoanh/
    return here.parent.parent


def get_current_branch(cwd: Path | None = None) -> str:
    """Trả về tên nhánh git hiện tại tại `cwd` (chỉ đọc, không ghi gì).

    Raise RuntimeError nếu không lấy được (không phải git repo, lỗi git...).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"Không lấy được nhánh git hiện tại: {exc}") from exc
    return result.stdout.strip()


def check_branch_guard(cwd: Path | None = None) -> tuple[bool, str]:
    """Kiểm tra nhánh hiện tại có an toàn để agent task commit không.

    Trả về (ok, message). ok=False khi nhánh hiện tại là một trong
    PROTECTED_BRANCHES — nghĩa là agent đang đứng trên cây chính, không
    phải worktree riêng của task.
    """
    try:
        branch = get_current_branch(cwd)
    except RuntimeError as exc:
        return False, str(exc)

    if branch in PROTECTED_BRANCHES:
        return False, (
            f"CHẶN: nhánh hiện tại '{branch}' là nhánh chính. "
            "Agent task không được commit trực tiếp vào cây chính — "
            "hãy làm trong worktree riêng của task (xem docs/process/ORCA_WORKFLOW.md)."
        )
    return True, f"OK: nhánh hiện tại '{branch}' không phải nhánh chính."


def check_approval(task_id: str, repo_root: Path | None = None) -> bool:
    """Kiểm tra có tồn tại file duyệt approvals/<task_id>.approved chưa.

    Chỉ đọc hệ thống file — không tạo, không xóa, không sửa file nào.
    `repo_root` là thư mục chứa `approvals/` (mặc định: root của daoanh/,
    suy ra từ vị trí file này). Dùng tham số này để test với tempdir.
    """
    if not TASK_ID_RE.match(task_id):
        # task_id sai định dạng (ví dụ "../x") — không ghép path, trả False ngay.
        return False
    root = repo_root if repo_root is not None else _repo_root()
    approval_file = root / APPROVALS_DIRNAME / f"{task_id}.approved"
    return approval_file.is_file()


def _cmd_check_branch(args: argparse.Namespace) -> int:
    ok, message = check_branch_guard(cwd=Path(args.cwd) if args.cwd else None)
    print(message)
    return 0 if ok else 1


def _cmd_check_approval(args: argparse.Namespace) -> int:
    root = Path(args.repo_root) if args.repo_root else None
    ok = check_approval(args.task_id, repo_root=root)
    if ok:
        print(f"OK: tìm thấy {APPROVALS_DIRNAME}/{args.task_id}.approved — được phép --apply.")
        return 0
    print(
        f"CHẶN: chưa có {APPROVALS_DIRNAME}/{args.task_id}.approved. "
        "Không được chạy --apply cho tới khi Admin tạo file duyệt này."
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode")

    branch_parser = sub.add_parser("check-branch", help="Kiểm tra nhánh hiện tại")
    branch_parser.add_argument("--cwd", default=None, help="Thư mục git để kiểm tra (mặc định: cwd hiện tại)")
    branch_parser.set_defaults(func=_cmd_check_branch)

    approval_parser = sub.add_parser("check-approval", help="Kiểm tra file duyệt của một task")
    approval_parser.add_argument("task_id", help="Ví dụ: T53")
    approval_parser.add_argument("--repo-root", default=None, help="Root chứa approvals/ (mặc định: daoanh/)")
    approval_parser.set_defaults(func=_cmd_check_approval)

    # Hỗ trợ cú pháp --check-branch / --check-approval <id> như mô tả trong docstring,
    # ngoài cú pháp subcommand chuẩn ở trên.
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "--check-branch":
        argv = ["check-branch"] + argv[1:]
    elif argv and argv[0] == "--check-approval":
        argv = ["check-approval"] + argv[1:]

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

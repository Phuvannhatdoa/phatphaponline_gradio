"""Unit test cho scripts/check_orca_guard.py.

Dùng tempdir, không đụng DB thật, không đụng repo git thật. Mọi thao tác
git trong test chạy trên repo tạm được tạo riêng cho test đó.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_orca_guard as guard  # noqa: E402


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_temp_repo(branch_name: str) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_test_"))
    _run_git(["init", "-q"], cwd=tmpdir)
    _run_git(["config", "user.email", "test@example.com"], cwd=tmpdir)
    _run_git(["config", "user.name", "Test"], cwd=tmpdir)
    (tmpdir / "README.md").write_text("test\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=tmpdir)
    _run_git(["commit", "-q", "-m", "init"], cwd=tmpdir)
    # Đổi tên nhánh hiện tại (mới init) thành branch_name mong muốn.
    _run_git(["branch", "-M", branch_name], cwd=tmpdir)
    return tmpdir


class TestBranchGuard(unittest.TestCase):
    def test_protected_branch_truyen_dang_blocks(self):
        repo = _init_temp_repo("truyen-dang-the-pho-clean")
        ok, message = guard.check_branch_guard(cwd=repo)
        self.assertFalse(ok)
        self.assertIn("CHẶN", message)

    def test_protected_branch_main_blocks(self):
        repo = _init_temp_repo("main")
        ok, message = guard.check_branch_guard(cwd=repo)
        self.assertFalse(ok)
        self.assertIn("CHẶN", message)

    def test_task_branch_is_allowed(self):
        repo = _init_temp_repo("wt/process-orca")
        ok, message = guard.check_branch_guard(cwd=repo)
        self.assertTrue(ok)
        self.assertIn("OK", message)

    def test_non_git_dir_fails_safely(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_nogit_"))
        ok, message = guard.check_branch_guard(cwd=tmpdir)
        self.assertFalse(ok)
        self.assertTrue(len(message) > 0)


class TestApprovalGuard(unittest.TestCase):
    def test_no_approval_file_returns_false(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_approval_"))
        self.assertFalse(guard.check_approval("T999", repo_root=tmpdir))

    def test_approval_file_present_returns_true(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_approval_"))
        approvals_dir = tmpdir / "approvals"
        approvals_dir.mkdir(parents=True, exist_ok=True)
        (approvals_dir / "T53.approved").write_text("hash: deadbeef\n", encoding="utf-8")
        self.assertTrue(guard.check_approval("T53", repo_root=tmpdir))

    def test_approval_check_does_not_write_anything(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_nowrite_"))
        before = sorted(tmpdir.rglob("*"))
        guard.check_approval("T53", repo_root=tmpdir)
        after = sorted(tmpdir.rglob("*"))
        self.assertEqual(before, after)


class TestCLI(unittest.TestCase):
    def test_check_approval_cli_exit_code_fail(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_cli_"))
        rc = guard.main(["check-approval", "T999", "--repo-root", str(tmpdir)])
        self.assertEqual(rc, 1)

    def test_check_approval_cli_exit_code_ok(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="orca_guard_cli_"))
        approvals_dir = tmpdir / "approvals"
        approvals_dir.mkdir(parents=True, exist_ok=True)
        (approvals_dir / "T53.approved").write_text("ok\n", encoding="utf-8")
        rc = guard.main(["check-approval", "T53", "--repo-root", str(tmpdir)])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

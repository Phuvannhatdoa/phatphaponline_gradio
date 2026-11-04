"""Kiểm tra nhận diện tên nhánh của scripts/wt_integrate.py (không merge, không tạo khóa)."""
import importlib.util
import io
import os
import contextlib
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "wt_integrate.py")
spec = importlib.util.spec_from_file_location("wt_integrate", SCRIPT)
wt_integrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wt_integrate)


def run_main(branch):
    """Chạy main với một tên nhánh, trả (mã thoát, nội dung in ra)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = wt_integrate.main(["wt_integrate.py", branch])
    return code, buf.getvalue()


class TestBranchNames(unittest.TestCase):
    def test_reject_task_number_without_description(self):
        code, out = run_main("T53")
        self.assertEqual(code, 1)
        self.assertIn("không đúng dạng", out)

    def test_reject_uppercase_description(self):
        code, out = run_main("t53-CBETA")
        self.assertEqual(code, 1)
        self.assertIn("không đúng dạng", out)

    def test_reject_missing_number(self):
        code, out = run_main("t-abc")
        self.assertEqual(code, 1)
        self.assertIn("không đúng dạng", out)

    def test_accept_format_but_missing_branch_stops_before_merge(self):
        # Đúng dạng nhưng nhánh không tồn tại: phải dừng ở bước kiểm nhánh, trước khi tạo khóa.
        code, out = run_main("t999-khong-ton-tai-zz")
        self.assertEqual(code, 1)
        self.assertIn("Không có nhánh", out)

    def test_legacy_wt_prefix_missing_branch_stops(self):
        code, out = run_main("wt/khong-ton-tai-zz")
        self.assertEqual(code, 1)
        self.assertIn("Không có nhánh", out)


if __name__ == "__main__":
    unittest.main()

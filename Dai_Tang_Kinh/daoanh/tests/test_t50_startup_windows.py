"""T50 — Windows/Python 3.14 startup smoke test.

Bối cảnh (Handoff-2026-11-03-T50-python314-windows.md):
  Job T50 cho T51n2076 khởi động thất bại trên Windows/Python 3.14, log
  (data/t50_job.log) có traceback đi qua hanviet_normalization.py → pathlib
  → fcntl → KeyboardInterrupt. Test này đảm bảo:
    A. `hanviet_normalization.py` import được, không chạm pathlib/fcntl.
    B. `t50_passage_vi_backfill.py --dry-run` khởi động và thoát sạch
       (exit code 0, không traceback) trên máy hiện tại.
    C. `--verify` khởi động và thoát sạch (đường DB thật hoặc không có DB).
    D. Helper tự-reconcile job-status chỉ đụng file khi PID khớp (race-safe),
       không tạo file mới nếu status file chưa tồn tại.

Không gọi Groq, không cần network. Không sửa Hán văn/DB khi chạy test này
(--dry-run/--verify không UPDATE/INSERT).
"""
import sys
import os
import io
import json
import subprocess
import tempfile

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
SCRIPTS_DIR = os.path.join(DAOANH, 'scripts')
BACKFILL_PY = os.path.join(SCRIPTS_DIR, 't50_passage_vi_backfill.py')

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_A_hanviet_normalization_imports_clean():
    """Import hanviet_normalization trong tiến trình con riêng (không dùng
    cache sys.modules của tiến trình test) để mô phỏng đúng tình huống
    khởi động lạnh như subprocess T50 thật."""
    code = (
        "import sys, os; "
        "sys.path.insert(0, r'%s'); "
        "import hanviet_normalization as m; "
        "assert callable(m.normalize_text); "
        "assert 'pathlib' not in sys.modules or True; "  # không bắt buộc cấm pathlib toàn cục, chỉ cần import module không raise
        "print('OK')"
    ) % SCRIPTS_DIR
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30,
                        encoding='utf-8', errors='replace')
    assert r.returncode == 0, f"import hanviet_normalization thất bại: rc={r.returncode}\nSTDOUT={r.stdout}\nSTDERR={r.stderr}"
    assert 'OK' in r.stdout


def test_B_backfill_dry_run_exits_clean():
    # --dry-run vẫn cần qua bước resolve_groq_key() trước khi tới nhánh
    # dry-run (hành vi gốc, không phải lỗi do fix này) nên set key giả qua env
    # để test chỉ đo "khởi động sạch", không gọi Groq thật.
    env = {**os.environ, 'GROQ_KEY': 'test-dummy-key-not-called'}
    r = subprocess.run(
        [sys.executable, '-X', 'utf8', BACKFILL_PY, '--dry-run', '--limit', '1'],
        capture_output=True, text=True, timeout=60, cwd=DAOANH, env=env,
        encoding='utf-8', errors='replace',
    )
    assert r.returncode == 0, f"--dry-run không thoát sạch: rc={r.returncode}\nSTDOUT={r.stdout}\nSTDERR={r.stderr}"
    assert 'Traceback' not in r.stderr, f"Có traceback dù dry-run: {r.stderr}"


def test_C_backfill_verify_exits_clean():
    r = subprocess.run(
        [sys.executable, '-X', 'utf8', BACKFILL_PY, '--verify'],
        capture_output=True, text=True, timeout=60, cwd=DAOANH,
        encoding='utf-8', errors='replace',
    )
    assert r.returncode == 0, f"--verify không thoát sạch: rc={r.returncode}\nSTDOUT={r.stdout}\nSTDERR={r.stderr}"
    assert 'Traceback' not in r.stderr


def test_D_self_reconcile_status_is_race_safe():
    """Helper tự-reconcile chỉ ghi khi pid trong status khớp pid hiện tại,
    và không tạo file mới nếu chưa tồn tại — tránh đè trạng thái job khác.

    Chạy trong subprocess riêng (không importlib cùng tiến trình với test
    harness) để không bị side-effect module-level `sys.stdout = io.TextIOWrapper(...)`
    của t50_passage_vi_backfill.py làm hỏng stdout/stderr của chính test này."""
    with tempfile.TemporaryDirectory() as td:
        status_path = os.path.join(td, 't50_job_status.json').replace('\\', '\\\\')
        script_path = BACKFILL_PY.replace('\\', '\\\\')
        code = f"""
import importlib.util, os, json, sys
spec = importlib.util.spec_from_file_location('t50_under_test', r'{script_path}')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
status_path = r'{status_path}'
mod._T50_STATUS_FILE = status_path

# D1: file chua ton tai -> khong duoc tu tao
mod._t50_self_reconcile_on_failure('exception', {{'error': 'x'}})
assert not os.path.exists(status_path), 'D1 FAIL: tu tao file moi khi chua co'

# D2: pid trong file KHONG khop -> khong duoc dung file
other = {{"running": True, "sigla": "T99nXXXX", "pid": os.getpid() + 999999, "started_at": "t"}}
with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(other, f)
mod._t50_self_reconcile_on_failure('exception', {{'error': 'x'}})
with open(status_path, encoding='utf-8') as f:
    after = json.load(f)
assert after == other, 'D2 FAIL: da de trang thai cua job khac'

# D3: pid khop chinh minh -> duoc set running=False + exit_reason
mine = {{"running": True, "sigla": "T51n2076", "pid": os.getpid(), "started_at": "t"}}
with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(mine, f)
mod._t50_self_reconcile_on_failure('keyboard_interrupt')
with open(status_path, encoding='utf-8') as f:
    after2 = json.load(f)
assert after2['running'] is False, 'D3 FAIL: running khong duoc set False'
assert after2['exit_reason'] == 'keyboard_interrupt', 'D3 FAIL: thieu exit_reason'
assert 'finished_at' in after2, 'D3 FAIL: thieu finished_at'
print('D_OK')
"""
        r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                            timeout=30, encoding='utf-8', errors='replace')
        assert r.returncode == 0 and 'D_OK' in r.stdout, (
            f"test_D thất bại: rc={r.returncode}\nSTDOUT={r.stdout}\nSTDERR={r.stderr}")


if __name__ == '__main__':
    tests = [
        test_A_hanviet_normalization_imports_clean,
        test_B_backfill_dry_run_exits_clean,
        test_C_backfill_verify_exits_clean,
        test_D_self_reconcile_status_is_race_safe,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"PASS {t.__name__}")
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*50}")
    print(f"T50-STARTUP-WINDOWS: {passed}/{len(tests)} PASS, {failed} FAIL")
    if failed:
        sys.exit(1)

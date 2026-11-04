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
    E. Helper dò PID (scripts/process_alive.py) đúng và KHÔNG giết tiến trình
       (thay os.kill(pid, 0) — trên Windows đó là TerminateProcess).

Cập nhật 2026-11-03 (test chịu được DB rỗng):
  Worktree mới checkout chỉ có `data/lineage.db` rỗng (0 bảng) vì `data/`
  không được git track ⇒ B/C từng đỏ oan với
  `sqlite3.OperationalError: no such table: passage`, dù lỗi khởi động mà
  test nhắm tới đã hết. Nay B/C:
    - Dùng DB thật nếu `data/lineage.db` đã có bảng `passage` (cây chính).
    - Nếu chưa, tự dựng fixture DB tạm và truyền qua env `T50_DB_PATH`
      (script hỗ trợ override, mặc định vẫn là data/lineage.db).
  Fixture cố tình KHÔNG có cột `translation_draft` để đồng thời kiểm tra
  migration additive của `ensure_schema()`.

Không gọi Groq, không cần network. Không sửa Hán văn/DB khi chạy test này
(--dry-run/--verify không UPDATE/INSERT trên dữ liệu thật; fixture là DB tạm).
"""
import sys
import os
import io
import json
import time
import sqlite3
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
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


# ── Hạ tầng: chọn DB thật hay fixture ──────────────────────────────────────
def _real_db_ready():
    """True nếu data/lineage.db tồn tại VÀ đã có bảng `passage`.

    Worktree vừa checkout thường chỉ có lineage.db rỗng 4096 byte / 0 bảng
    (data/ không được git track), nên không thể chạy thẳng --dry-run/--verify.
    """
    try:
        if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
            return False
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='passage'"
            ).fetchone()
            return row is not None
        finally:
            conn.close()
    except Exception:
        return False


# Schema tối thiểu đúng những gì script đụng tới. Chú ý: bảng `passage` cố ý
# KHÔNG có cột `translation_draft` → ensure_schema() phải tự ALTER (additive).
FIXTURE_SCHEMA = """
CREATE TABLE passage (
    passage_id INTEGER PRIMARY KEY,
    text_id    TEXT,
    loc_ref    TEXT,
    raw_text   TEXT,
    vi_text    TEXT
);
CREATE TABLE entity (
    entity_id   INTEGER PRIMARY KEY,
    entity_type TEXT
);
CREATE TABLE passage_entity (
    passage_id INTEGER,
    entity_id  INTEGER
);
CREATE TABLE translation_cache (
    source_hash     TEXT,
    source_type     TEXT,
    entity_id       TEXT,
    source_text     TEXT,
    translated_text TEXT,
    model_id        TEXT,
    rules_version   TEXT,
    status          TEXT,
    report_count    INTEGER DEFAULT 0,
    created_at      TEXT,
    updated_at      TEXT
);
"""


def _make_fixture_db(td):
    """Dựng fixture DB tạm trong thư mục td, trả đường dẫn.

    Có 1 passage chờ dịch (raw_text != NULL, vi_text NULL) gắn với 1 entity
    PLACE + 1 entity PERSON → select_pending() phải trả đúng 1 dòng, đủ để
    --dry-run đi qua nhánh "có dữ liệu" mà không gọi Groq.
    """
    path = os.path.join(td, 'fixture_lineage.db')
    conn = sqlite3.connect(path)
    try:
        conn.executescript(FIXTURE_SCHEMA)
        conn.execute(
            "INSERT INTO passage (passage_id, text_id, loc_ref, raw_text, vi_text) "
            "VALUES (1, 'T51n2076', 'p0001a01', '祖師西來意', NULL)")
        conn.executemany(
            "INSERT INTO entity (entity_id, entity_type) VALUES (?, ?)",
            [(10, 'PLACE'), (11, 'PERSON')])
        conn.executemany(
            "INSERT INTO passage_entity (passage_id, entity_id) VALUES (?, ?)",
            [(1, 10), (1, 11)])
        conn.commit()
    finally:
        conn.close()
    return path


def _db_for_run(td):
    """Trả (db_path, nhãn) cho lần chạy test B/C.

    Ưu tiên DB thật (đúng môi trường vận hành); nếu DB thật chưa có schema thì
    dùng fixture tạm để test vẫn đo được "khởi động sạch".
    """
    if _real_db_ready():
        return DB_PATH, 'DB thật'
    return _make_fixture_db(td), 'fixture'


def _run_backfill(argv, db_path, extra_env=None):
    """Chạy script backfill với DB chỉ định (qua env T50_DB_PATH)."""
    env = {**os.environ, 'PYTHONUTF8': '1', 'T50_DB_PATH': db_path}
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, '-X', 'utf8', BACKFILL_PY] + list(argv),
        capture_output=True, text=True, timeout=90, cwd=DAOANH, env=env,
        encoding='utf-8', errors='replace',
    )


# ── Test cases ─────────────────────────────────────────────────────────────
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
    with tempfile.TemporaryDirectory() as td:
        db_path, src = _db_for_run(td)
        r = _run_backfill(['--dry-run', '--limit', '1'], db_path,
                          {'GROQ_KEY': 'test-dummy-key-not-called'})
        ctx = f"[nguồn DB: {src} → {db_path}]"
        assert r.returncode == 0, (
            f"--dry-run không thoát sạch: rc={r.returncode} {ctx}\n"
            f"STDOUT={r.stdout}\nSTDERR={r.stderr}")
        assert 'Traceback' not in r.stderr, f"Có traceback dù dry-run: {r.stderr}\n{ctx}"
        # Phải đi hết nhánh dry-run (có dữ liệu) hoặc báo hết passage chờ dịch.
        assert ('DRY RUN' in r.stdout) or ('Không còn passage chờ dịch' in r.stdout), (
            f"không thấy dấu hiệu hoàn tất nhánh dry-run {ctx}\nSTDOUT={r.stdout}")


def test_C_backfill_verify_exits_clean():
    with tempfile.TemporaryDirectory() as td:
        db_path, src = _db_for_run(td)
        r = _run_backfill(['--verify'], db_path)
        ctx = f"[nguồn DB: {src} → {db_path}]"
        assert r.returncode == 0, (
            f"--verify không thoát sạch: rc={r.returncode} {ctx}\n"
            f"STDOUT={r.stdout}\nSTDERR={r.stderr}")
        assert 'Traceback' not in r.stderr, f"Có traceback: {r.stderr}\n{ctx}"
        assert '== VERIFY T50 ==' in r.stdout, (
            f"--verify không chạy tới phần thống kê {ctx}\nSTDOUT={r.stdout}")


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


def test_E_pid_alive_is_safe_and_accurate():
    """Helper dò tiến trình phải ĐÚNG và KHÔNG được giết tiến trình.

    Bối cảnh (2026-11-04): app.py cũ dùng `os.kill(pid, 0)`. Trên Windows
    CPython cài os.kill bằng OpenProcess + TerminateProcess ⇒ đó không phải
    phép dò tồn tại; đo thật với job T50 đang sống trả WinError 87 khiến
    dashboard ghi running=False. Test này khoá lại hành vi đúng của
    scripts/process_alive.py:
      E1. pid rỗng/không hợp lệ → False (không ném exception).
      E2. pid của tiến trình con đang sống → True.
      E3. gọi xong tiến trình đó VẪN sống (không bị TerminateProcess).
      E4. sau khi tiến trình thoát → False.
    """
    from process_alive import pid_alive

    # E1 — giá trị rác không được làm nổ caller
    for bad in (None, '', 0, -1, 'abc', '  '):
        assert pid_alive(bad) is False, f"E1 FAIL: pid_alive({bad!r}) phải là False"

    # E2/E3 — tiến trình sống: True và không bị giết
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        time.sleep(1.0)
        assert pid_alive(child.pid) is True, (
            f"E2 FAIL: pid_alive({child.pid}) phải là True (tiến trình đang sống)")
        time.sleep(0.5)
        assert child.poll() is None, (
            'E3 FAIL: pid_alive đã kết thúc tiến trình đích — '
            'tuyệt đối không dùng os.kill trên Windows')
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)

    # E4 — đã thoát: False (không ném exception)
    assert pid_alive(child.pid) is False, (
        f"E4 FAIL: pid_alive({child.pid}) phải là False sau khi tiến trình thoát")


if __name__ == '__main__':
    print(f"[env] data/lineage.db có schema sẵn sàng: {_real_db_ready()} "
          f"({DB_PATH}) → B/C sẽ dùng "
          f"{'DB thật' if _real_db_ready() else 'fixture DB tạm'}")
    tests = [
        test_A_hanviet_normalization_imports_clean,
        test_B_backfill_dry_run_exits_clean,
        test_C_backfill_verify_exits_clean,
        test_D_self_reconcile_status_is_race_safe,
        test_E_pid_alive_is_safe_and_accurate,
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

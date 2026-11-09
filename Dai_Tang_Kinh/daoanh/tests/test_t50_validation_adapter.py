# -*- coding: utf-8 -*-
"""T167 — Validator adapter gắn vào lô T50 (CHỈ KIỂM TRA, Admin Phương án A, 2026-11-07).

Bối cảnh:
  - `scripts/translation_validator.py` có `validate_translation()` CẦN một bản ghi
    `translation_segments` đầy đủ (translation_id, ruleset_id, prompt_version...).
    Lô T50 (`scripts/t50_passage_vi_backfill.py`) KHÔNG ghi `translation_segments`
    (chỉ ghi `passage.vi_text` + `translation_cache`) → không gọi được
    `validate_translation()` thẳng.
  - Task này thêm `validate_text(source_text, draft_text, ref=None, con=None)` —
    adapter dùng lại layer A (rút gọn)/C (rút gọn)/F, best-effort layer D, KHÔNG
    ghi DB, KHÔNG sửa draft — và gắn và `t50_passage_vi_backfill.py` qua
    `t167_validate_and_log()`, chạy SAU draft/TRƯỚC khi ghi `passage.vi_text`,
    ghi ra `data/t50_validation_report.jsonl` (KHÔNG đổi `passage.vi_text`/
    `translation_draft`/`translation_cache` hiện có), có cờ `--no-validate`
    (mặc định BẬT) để tắt.

Test (5 case theo yêu cầu):
  1. draft rỗng               -> validate_text() trả FAIL/REVIEW (layer A FAIL).
  2. draft echo nguyên văn    -> validate_text() gắn cờ FAIL (layer C, "Echo").
  3. draft bình thường        -> PASS hoặc REVIEW kèm lý do (không bao giờ ném lỗi).
  4. validator lỗi (mock)     -> t167_validate_and_log() KHÔNG làm vỡ luồng ghi
                                  (không raise, không viết báo cáo cho lần đó).
  5. --no-validate             -> t167_validate_and_log(enabled=False) KHÔNG ghi
                                  báo cáo (so sánh với enabled=True CÓ ghi, để
                                  chứng minh phủ định có ý nghĩa).

Case 4/5 chạy trong subprocess riêng (importlib.util, như test_t50_startup_windows.py)
để tránh side-effect module-level của t50_passage_vi_backfill.py (nó reassign
sys.stdout/sys.stderr) làm hỏng stdout/stderr của chính tiến trình test.

Không gọi Groq, không đụng data/lineage.db thật.
Chạy: python -X utf8 -m pytest tests/test_t50_validation_adapter.py -v
  hoặc: python -X utf8 tests/test_t50_validation_adapter.py
"""
import os
import sys
import json
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
SCRIPTS_DIR = os.path.join(DAOANH, 'scripts')
BACKFILL_PY = os.path.join(SCRIPTS_DIR, 't50_passage_vi_backfill.py')

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from translation_validator import validate_text  # noqa: E402


def _layer(result, code):
    for l in result['layers']:
        if l['layer'] == code:
            return l
    return None


# ── 1. draft rỗng ────────────────────────────────────────────────────────────
def test_1_draft_rong_flags_fail_or_review():
    source = "祖師西來意，傳法於少林寺。"
    result = validate_text(source, "", ref="t1-draft-rong")
    assert result['overall'] in ('FAIL', 'REVIEW'), (
        f"draft rỗng phải bị gắn cờ FAIL/REVIEW, nhận {result['overall']}: {result}")
    layer_a = _layer(result, 'A')
    assert layer_a is not None, "thiếu layer A trong kết quả"
    assert layer_a['status'] == 'FAIL', f"layer A phải FAIL khi draft rỗng: {layer_a}"
    assert 'rỗng' in layer_a['message']


# ── 2. draft echo nguyên văn Hán ────────────────────────────────────────────
def test_2_draft_echo_nguyen_van_flags_fail():
    source = "祖師西來意，傳法於少林寺。"
    result = validate_text(source, source, ref="t2-echo")
    assert result['overall'] == 'FAIL', (
        f"draft echo nguyên văn phải FAIL (layer C), nhận {result['overall']}: {result}")
    layer_c = _layer(result, 'C')
    assert layer_c is not None
    assert layer_c['status'] == 'FAIL'
    assert 'Echo' in layer_c['message']


def test_2b_draft_echo_sau_khi_chuan_hoa_khoang_trang_van_bi_flag():
    """zh_norm() bỏ hết whitespace trước khi so sánh — echo có thêm khoảng
    trắng/xuống dòng vẫn phải bị bắt (không né được bằng cách chèn space)."""
    source = "祖師西來意"
    draft_with_spaces = "祖 師 西 來 意"
    result = validate_text(source, draft_with_spaces, ref="t2b-echo-space")
    layer_c = _layer(result, 'C')
    assert layer_c['status'] == 'FAIL' and 'Echo' in layer_c['message']


# ── 3. draft bình thường ────────────────────────────────────────────────────
def test_3_draft_binh_thuong_pass_hoac_review_co_ly_do():
    source = "祖師西來意，傳法於少林寺。"
    draft = ("Ý chỉ của Tổ sư từ phương Tây truyền đến, ngài truyền pháp tại "
              "Thiếu Lâm Tự, khai mở dòng pháp cho hậu thế.")
    result = validate_text(source, draft, ref="t3-normal")
    assert result['overall'] in ('PASS', 'REVIEW'), (
        f"draft dịch bình thường không được FAIL: {result}")
    if result['overall'] == 'REVIEW':
        reasons = [l['message'] for l in result['layers'] if l['status'] == 'REVIEW']
        assert reasons and all(r.strip() for r in reasons), (
            f"REVIEW phải kèm lý do rõ ràng: {result}")
    # Không bao giờ raise / không có field 'error' bất ngờ
    assert 'error' not in result


def test_3b_validate_text_khong_can_con_van_chay_duoc():
    """con=None (không truyền DB connection) vẫn phải chạy được — layer D
    best-effort tự fallback, không raise."""
    result = validate_text("祖師西來意。", "Ý chỉ Tổ sư từ phương Tây truyền đến.",
                            ref="t3b-no-con", con=None)
    assert result['overall'] in ('PASS', 'REVIEW', 'FAIL')
    assert isinstance(result['layers'], list) and len(result['layers']) == 4


# ── Helper: chạy 1 đoạn code trong subprocess, import t50 module qua importlib ──
def _run_subprocess_check(extra_code, report_path):
    code = f"""
import importlib.util, sys, os, json
sys.path.insert(0, r'{SCRIPTS_DIR}')
spec = importlib.util.spec_from_file_location('t50_under_test', r'{BACKFILL_PY}')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.VALIDATION_REPORT_PATH = r'{report_path}'
import translation_validator
{extra_code}
"""
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                        timeout=30, encoding='utf-8', errors='replace')
    return r


# ── 4. lỗi validator không làm vỡ luồng ghi ────────────────────────────────
def test_4_loi_validator_khong_vo_luong_ghi():
    with tempfile.TemporaryDirectory() as td:
        report_path = os.path.join(td, 't50_validation_report.jsonl').replace('\\', '\\\\')
        extra = (
            "translation_validator.validate_text = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('boom mock'))\n"
            "mod.t167_validate_and_log(999, '祖師西來意', 'bản dịch giả', 't4-mock-loi', None, enabled=True)\n"
            "print('NO_RAISE_OK')\n"
            f"assert not os.path.exists(r'{report_path}'), 'FAIL: file bao cao bi ghi du validator loi'\n"
            "print('CASE4_OK')\n"
        )
        r = _run_subprocess_check(extra, report_path)
        assert r.returncode == 0, (
            f"t167_validate_and_log phải KHÔNG raise khi validator lỗi: "
            f"rc={r.returncode}\nSTDOUT={r.stdout}\nSTDERR={r.stderr}")
        assert 'NO_RAISE_OK' in r.stdout and 'CASE4_OK' in r.stdout, (
            f"không thấy dấu hiệu bắt lỗi thành công: {r.stdout}\n{r.stderr}")
        # Phải có cảnh báo in ra (không chặn lô, chỉ log)
        assert 'validator T167 lỗi' in r.stdout or 'validator T167 lỗi' in r.stderr


# ── 5. --no-validate tắt ghi báo cáo ────────────────────────────────────────
def test_5_no_validate_tat_ghi_bao_cao():
    with tempfile.TemporaryDirectory() as td:
        report_path = os.path.join(td, 't50_validation_report.jsonl').replace('\\', '\\\\')
        extra = (
            "mod.t167_validate_and_log(1, '祖師西來意，傳法於少林寺。', "
            "'Ý chỉ Tổ sư từ phương Tây truyền đến, ngài truyền pháp tại Thiếu Lâm Tự.', "
            "'t5-disabled', None, enabled=False)\n"
            f"assert not os.path.exists(r'{report_path}'), 'FAIL5a: --no-validate van ghi file'\n"
            "print('CASE5A_OK')\n"
            # Positive control: enabled=True CO ghi, chung minh phu dinh co y nghia.
            "mod.t167_validate_and_log(2, '祖師西來意，傳法於少林寺。', "
            "'Ý chỉ Tổ sư từ phương Tây truyền đến, ngài truyền pháp tại Thiếu Lâm Tự.', "
            "'t5-enabled', None, enabled=True)\n"
            f"assert os.path.exists(r'{report_path}'), 'FAIL5b: enabled=True nhung khong ghi file'\n"
            f"with open(r'{report_path}', encoding='utf-8') as f:\n"
            "    lines = [l for l in f.read().splitlines() if l.strip()]\n"
            "assert len(lines) == 1, f'FAIL5c: phai dung 1 dong (chi lan enabled=True), nhan {len(lines)}'\n"
            "row = json.loads(lines[0])\n"
            "assert row.get('ref') == 't5-enabled' and row.get('passage_id') == 2\n"
            "print('CASE5B_OK')\n"
        )
        r = _run_subprocess_check(extra, report_path)
        assert r.returncode == 0, (
            f"test case 5 thất bại: rc={r.returncode}\nSTDOUT={r.stdout}\nSTDERR={r.stderr}")
        assert 'CASE5A_OK' in r.stdout and 'CASE5B_OK' in r.stdout, (
            f"thiếu dấu hiệu PASS: {r.stdout}\n{r.stderr}")


if __name__ == '__main__':
    tests = [
        test_1_draft_rong_flags_fail_or_review,
        test_2_draft_echo_nguyen_van_flags_fail,
        test_2b_draft_echo_sau_khi_chuan_hoa_khoang_trang_van_bi_flag,
        test_3_draft_binh_thuong_pass_hoac_review_co_ly_do,
        test_3b_validate_text_khong_can_con_van_chay_duoc,
        test_4_loi_validator_khong_vo_luong_ghi,
        test_5_no_validate_tat_ghi_bao_cao,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{'=' * 50}")
    print(f"T50-VALIDATION-ADAPTER: {passed}/{len(tests)} PASS, {failed} FAIL")
    if failed:
        sys.exit(1)

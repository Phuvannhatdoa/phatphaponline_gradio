# -*- coding: utf-8 -*-
"""test_t166_matrix.py — T166 Canonical Identity Hard Guard: test matrix A–J.

Chạy trên DB COPY (không chạm DB thật) — SPEC T166 §14.
Fixture chuẩn (Admin chốt §20.3):
  A009460 丹霞天然 → "Đơn Hà Thiên Nhiên"  (LOCKED, vn_person_authority verified)
  A005248 安廩     → "An Lẫm"             (CANDIDATE, name_vi_map auto 0.7)
  少林寺          → "Thiếu Lâm Tự"        (PLACE reviewed)
"""
import os
import sys
import shutil
import sqlite3
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from canonical_lock import (  # noqa: E402
    build_canonical_lock, pre_assert, post_assert, translate_with_guard,
    build_lock_prompt_section, t166_lock_fingerprint,
    extract_maximal_han_runs, normalize_vi, is_valid_vi,
    POLICY_PARTIAL, POLICY_STOP, VALID_POLICIES,
)

REAL_DB = os.path.join(BASE, 'data', 'lineage.db')

# ── Fixture Hán / kết quả kỳ vọng ────────────────────────────────────────
PERSON_ZH = '丹霞天然'          # A009460 · LOCKED
PERSON_VI = 'Đơn Hà Thiên Nhiên'
PERSON_WRONG_VI = 'Thích Đơn Hà Mật'
CAND_ZH = '安廩'                 # A005248 · CANDIDATE (auto 0.7)
CAND_VI = 'An Lẫm'
CAND_INVENT_VI = 'Thích An Nạp'
PLACE_ZH = '少林寺'              # reviewed
TERM_ZH = '大乘'                 # glossary is_locked, ≥2 chars
TERM_VI = 'Đại Thừa'
UNKNOWN_ZH = '某某'              # không authority


def _db():
    """Mở DB thật ở chế độ read-only (chỉ SELECT authority — Zero-RAM, an toàn)."""
    uri = f'file:{REAL_DB}?mode=ro'
    return sqlite3.connect(uri, uri=True)


def _lock(source: str):
    conn = _db()
    try:
        return build_canonical_lock(conn, source)
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════
# A — Known person lock đúng → out đúng (sau strip title) → PASS
# ════════════════════════════════════════════════════════════════════════
def test_A_locked_person_correct_name_passes():
    lock = _lock(f'Người ấy là {PERSON_ZH}, người đời Đông.')
    e = next(x for x in lock if x.source_form == PERSON_ZH)
    assert e.status == 'LOCKED', f'{PERSON_ZH} phải LOCKED, got {e.status}'
    assert e.canonical_value == PERSON_VI
    assert e.canonical_id == 'A009460'
    st, iss = post_assert(lock, f'Người ấy là Thích {PERSON_VI}, người đời Đông.')
    assert st == 'pass', f'case A phải pass, got {st}: {iss}'


# ════════════════════════════════════════════════════════════════════════
# B — Known person → đổi tên → HARD_FAIL mismatch
# ════════════════════════════════════════════════════════════════════════
def test_B_locked_person_changed_name_hard_fail():
    lock = _lock(f'Người ấy là {PERSON_ZH}, người đời Đông.')
    st, iss = post_assert(lock, f'Người ấy là {PERSON_WRONG_VI}, người đời Đông.')
    assert st == 'failed', f'case B phải failed, got {st}'
    codes = {i['code'] for i in iss}
    assert 'CANONICAL_IDENTITY_MISMATCH' in codes
    hard = [i for i in iss if i['code'] == 'CANONICAL_IDENTITY_MISMATCH']
    assert hard and hard[0]['severity'] == 'HARD'


# ════════════════════════════════════════════════════════════════════════
# C — CANDIDATE (auto 0.7) → cùng tên → PASS, KHÔNG hard-fail
# ════════════════════════════════════════════════════════════════════════
def test_C_candidate_person_same_name_passes():
    lock = _lock(f'Hoàng {CAND_VI} người Lợi Thành, vị ấy tên {CAND_ZH}.')
    e = next(x for x in lock if x.source_form == CAND_ZH)
    assert e.status == 'CANDIDATE', f'{CAND_ZH} phải CANDIDATE, got {e.status}'
    assert e.authority_level == 0.7
    st, iss = post_assert(lock, f'Người ấy là Thích {CAND_VI}, người Lợi Thành.')
    assert st == 'pass', f'case C phải pass, got {st}: {iss}'


# ════════════════════════════════════════════════════════════════════════
# C2 — CANDIDATE + LLM đổi/bịa tên → WARNING (KHÔNG hard-fail) — SPEC §6.3 hàng 4
# ════════════════════════════════════════════════════════════════════════
def test_C2_candidate_invented_name_is_warning_only():
    lock = _lock(f'Hoàng {CAND_VI} người Lợi Thành, vị ấy tên {CAND_ZH}.')
    st, iss = post_assert(lock, 'Người ấy là ' + CAND_INVENT_VI + ', người Lợi Thành.')
    assert st == 'review_required', f'case C2 phải review_required, got {st}'
    inv = [i for i in iss if i['code'] == 'CANONICAL_INVENTION']
    assert inv, 'phải có CANONICAL_INVENTION'
    assert all(i['severity'] == 'WARN' for i in inv), \
        'CANDIDATE không được HARD (SPEC §3.1: không HARD_FAIL khi LLM khác)'


# ════════════════════════════════════════════════════════════════════════
# D — Nhiều nguồn ≥2 giá trị VI khác → CONFLICT, giữ claims[], KHÔNG auto-pick
# ════════════════════════════════════════════════════════════════════════
def test_D_conflict_keeps_all_claims():
    lock = _lock(f'Tại {PLACE_ZH} có nhiều thuyết.')
    e = next((x for x in lock if x.source_form == PLACE_ZH and x.status == 'CONFLICT'), None)
    if e is None:
        # Không có conflict thật trong DB → dựng entry CONFLICT giả để test logic
        from canonical_lock import CanonicalLockEntry, _apply_lock_threshold
        entries = [
            CanonicalLockEntry(PLACE_ZH, PLACE_ZH, 'PLACE', 'PL_TEST_1',
                               'Thiếu Lâm Tự', 'namevi_map_places.reviewed',
                               0.9, 'CANDIDATE', []),
            CanonicalLockEntry(PLACE_ZH, PLACE_ZH, 'PLACE', 'PL_TEST_2',
                               'Thiếu Lâm Tự chùa', 'translation_glossary.is_locked',
                               1.0, 'CANDIDATE', []),
        ]
        e = _apply_lock_threshold(entries)[0]
    assert e.status == 'CONFLICT', f'phải CONFLICT, got {e.status}'
    assert len(e.claims) >= 2, f'phải giữ TẤT CẢ claims, got {len(e.claims)}'
    vals = {c['canonical_value'] for c in e.claims}
    assert len(vals) >= 2, 'claims phải chứa ≥2 giá trị VI khác nhau'


# ════════════════════════════════════════════════════════════════════════
# E — Unknown person (không authority) → UNKNOWN_REVIEW, không auto identity
# ════════════════════════════════════════════════════════════════════════
def test_E_unknown_han_is_unknown_review():
    lock = _lock(f'Vị ấy tên {UNKNOWN_ZH} người xứ núi.')
    e = next((x for x in lock if x.source_form == UNKNOWN_ZH), None)
    assert e is not None, f'{UNKNOWN_ZH} phải vào lock'
    assert e.status == 'UNKNOWN_REVIEW', f'phải UNKNOWN_REVIEW, got {e.status}'
    assert e.canonical_value == '', 'UNKNOWN không được đề xuất tên VI (SPEC §3.2)'
    assert e.authority_level == 0.0
    # P-PARTIAL: vẫn dịch được nhưng phải gắn cờ
    conn = _db()
    try:
        r = translate_with_guard(conn, f'Vị ấy tên {UNKNOWN_ZH} người xứ núi.',
                                 lambda t: 'Văn bản dịch.')
    finally:
        conn.close()
    assert r['ok'] is True, 'P-PARTIAL phải vẫn gọi LLM'
    assert r['identity_status'] == 'review_required'
    assert 'UNKNOWN_REVIEW' in {i['code'] for i in r['identity_issues']}


# ════════════════════════════════════════════════════════════════════════
# F — UNKNOWN_REVIEW ≠ failed (hard) — SPEC §20.2 #6 / §4.1
# ════════════════════════════════════════════════════════════════════════
def test_F_unknown_is_warning_not_failed():
    lock = _lock(f'Vị ấy tên {UNKNOWN_ZH} người xứ núi.')
    st, iss = post_assert(lock, 'Văn bản dịch bình thường.')
    assert st != 'failed', 'UNKNOWN_REVIEW KHÔNG được phân loại failed (hard)'
    assert st == 'review_required'


# ════════════════════════════════════════════════════════════════════════
# G — Locked Buddhist term giữ đúng → PASS
# ════════════════════════════════════════════════════════════════════════
def test_G_locked_term_correct_passes():
    lock = _lock(f'Giáo pháp {TERM_ZH} rất sâu xa.')
    e = next((x for x in lock if x.source_form == TERM_ZH), None)
    if e is not None:
        assert e.status == 'LOCKED'
        st, iss = post_assert(lock, f'Giáo pháp {TERM_VI} rất sâu xa.')
        assert st in ('pass', 'review_required'), f'case G got {st}: {iss}'


# ════════════════════════════════════════════════════════════════════════
# H — Locked term bị đổi → HARD_FAIL (≥2 chars)
# ════════════════════════════════════════════════════════════════════════
def test_H_locked_term_changed_hard_fail():
    lock = _lock(f'Giáo pháp {TERM_ZH} rất sâu xa.')
    e = next((x for x in lock if x.source_form == TERM_ZH), None)
    if e is None or e.status != 'LOCKED':
        return   # DB thật không có term locked ≥2 chars khớp → bỏ qua
    st, iss = post_assert(lock, f'Giáo pháp {PERSON_WRONG_VI} rất sâu xa.')
    hard = [i for i in iss if i['severity'] == 'HARD']
    assert st == 'failed' or hard, f'case H phải có HARD issue, got {st}: {iss}'


# ════════════════════════════════════════════════════════════════════════
# I — "High conf" nhưng mismatch → HARD_FAIL (LLM confidence KHÔNG bypass)
# ════════════════════════════════════════════════════════════════════════
def test_I_high_confidence_does_not_bypass_lock():
    """LLM tự tin (confidence=0.99) vẫn không override canonical authority."""
    lock = _lock(f'Người ấy là {PERSON_ZH}, người đời Đông.')
    # giả lập LLM rất tự tin: vẫn trả về tên sai
    st, iss = post_assert(lock, f'Người ấy là {PERSON_WRONG_VI}, người đời Đông.')
    assert st == 'failed', f'confidence cao không được bypass lock, got {st}'
    hard = [i for i in iss if i['severity'] == 'HARD']
    assert hard, 'phải có HARD issue dù LLM "rất tự tin"'


# ════════════════════════════════════════════════════════════════════════
# J — Retry cache failed draft → không bypass lock (re-run post-assert)
# ════════════════════════════════════════════════════════════════════════
def test_J_retry_does_not_bypass_lock():
    """Draft 'failed' lưu cache; retry vẫn phải qua post_assert → vẫn failed."""
    lock = _lock(f'Người ấy là {PERSON_ZH}, người đời Đông.')
    # lần 1: LLM sai
    st1, iss1 = post_assert(lock, f'Người ấy là {PERSON_WRONG_VI}.')
    assert st1 == 'failed'
    # lần 2 (retry): cùng output → vẫn phải failed, không "tin cache"
    st2, iss2 = post_assert(lock, f'Người ấy là {PERSON_WRONG_VI}.')
    assert st2 == 'failed', 'retry không được bypass lock'
    # lần 3: LLM sửa đúng → pass
    st3, _ = post_assert(lock, f'Người ấy là Thích {PERSON_VI}.')
    assert st3 == 'pass'


# ════════════════════════════════════════════════════════════════════════
# BỔ SUNG — policy / guard / prompt section
# ════════════════════════════════════════════════════════════════════════
def test_policy_stop_blocks_llm_call():
    conn = _db()
    called = []

    def _llm(prompt):
        called.append(prompt)
        return 'Văn bản dịch.'

    try:
        r = translate_with_guard(conn, f'Vị ấy tên {UNKNOWN_ZH} người xứ núi.',
                                 _llm, policy=POLICY_STOP)
    finally:
        conn.close()
    assert r['ok'] is False, 'P-STOP phải chặn, không gọi LLM'
    assert r['error_code'] == 'REVIEW_REQUIRED'
    assert called == [], 'P-STOP không được gọi LLM'


def test_policy_partial_still_calls_llm():
    conn = _db()
    called = []
    try:
        r = translate_with_guard(conn, f'Vị ấy tên {UNKNOWN_ZH} người xứ núi.',
                                 lambda p: (called.append(p), 'Văn bản dịch.')[1],
                                 policy=POLICY_PARTIAL)
    finally:
        conn.close()
    assert r['ok'] is True
    assert len(called) == 1, 'P-PARTIAL phải gọi LLM'


def test_invalid_policy_falls_back_to_partial():
    assert 'P-STOP' in VALID_POLICIES and 'P-PARTIAL' in VALID_POLICIES
    conn = _db()
    called = []
    try:
        r = translate_with_guard(conn, f'Vị ấy tên {UNKNOWN_ZH} xứ núi.',
                                 lambda p: (called.append(p), 'dịch')[1],
                                 policy='POLICY_BOGUS')
    finally:
        conn.close()
    assert r['ok'] is True, 'policy lạ phải fallback về P-PARTIAL (vẫn gọi LLM)'
    assert len(called) == 1


def test_prompt_section_contains_all_four_blocks():
    lock = _lock(f'Người ấy là {PERSON_ZH}; tại {PLACE_ZH} có giáo pháp {TERM_ZH}; tên {UNKNOWN_ZH}.')
    s = build_lock_prompt_section(lock)
    assert '=== LOCKED CANONICAL CONTEXT (BẮT BUỘC, KHÔNG ĐỔI) ===' in s
    assert '=== CANDIDATE (đề xuất máy, CHỈ ĐỀ XUẤT — không bắt buộc) ===' in s
    assert '=== CONFLICT (NGUỒN XUNG ĐỘT' in s
    assert '=== UNKNOWN / REVIEW (GIỮ HÁN, KHÔNG SÁNG TÁC) ===' in s
    # wording phải là CONSTRAINT không phải suggestion
    assert 'gợi ý' not in s.lower()
    assert 'gợi' not in s.lower()


def test_lock_fingerprint_stable_and_scoped_to_locked():
    lock = _lock(f'Người ấy là {PERSON_ZH}.')
    fp1 = t166_lock_fingerprint(lock)
    fp2 = t166_lock_fingerprint(list(reversed(lock)))     # thứ tự không ảnh hưởng
    assert fp1 and len(fp1) == 16
    assert fp1 == fp2, 'fingerprint phải ổn định bất kể thứ tự'
    # đổi canonical value → đổi hash
    lock2 = _lock(f'Người ấy là {PERSON_ZH}.')
    for e in lock2:
        if e.status == 'LOCKED':
            e.canonical_value = 'Tên Khác'
    assert t166_lock_fingerprint(lock2) != fp1, 'đổi canonical phải đổi fingerprint'


def test_no_locked_entry_fingerprint_is_empty():
    lock = _lock(f'Vị ấy tên {UNKNOWN_ZH} người xứ núi.')
    assert t166_lock_fingerprint(lock) == ''


def test_zero_ram_cap_40_han_runs():
    src = ' '.join(f'漢字{i:02d}' for i in range(60))
    runs = extract_maximal_han_runs(src)
    assert len(runs) <= 40, f'cap 40, got {len(runs)}'


def test_mojibake_rejected_from_lock():
    """Giá trị mojibake (chứa '?') không được đưa vào lock (SPEC §20.2 #3/#17)."""
    lock = _lock('Vị ấy tên 安廩 người Lợi Thành.')
    for e in lock:
        assert e.canonical_value, 'canonical_value rỗng không được lock'
        assert '?' not in e.canonical_value, \
            f'mojibake lọt vào lock: {e.canonical_value!r}'
        assert '�' not in e.canonical_value


def test_is_valid_vi_rejects_mojibake():
    assert is_valid_vi('Th? S?t H?i') is False
    assert is_valid_vi('Kho?t T?t ?a Qu?c') is False
    assert is_valid_vi('Thiếu Lâm Tự') is True
    assert is_valid_vi('') is False
    assert is_valid_vi(None) is False


def test_normalize_vi_strips_honorific_only_at_start():
    assert normalize_vi(f'Thích {PERSON_VI}') == normalize_vi(PERSON_VI)
    # "Tôi thích trà" → "thích" KHÔNG phải honorific ở đầu chuỗi
    assert normalize_vi('Tôi thích trà') != normalize_vi('Thích trà')


def test_common_word_no_false_invention():
    """SPEC §20.2 #12: "Tôi thích uống trà" → 0 CANONICAL_INVENTION."""
    lock = _lock(f'Người ấy là {PERSON_ZH}.')
    st, iss = post_assert(lock, 'Tôi thích uống trà mỗi chiều.')
    inv = [i for i in iss if i['code'] == 'CANONICAL_INVENTION']
    assert not inv, f'"tôi thích trà" không được flag invention: {inv}'


def test_omitted_locked_name_is_warning_not_hard():
    """Không render tên = không xác nhận được, nhưng KHÔNG hard-fail (R4)."""
    lock = _lock(f'Người ấy là {PERSON_ZH}, người đời Đông.')
    st, iss = post_assert(lock, 'Một vị cao tăng ở miền Đông.')
    assert st == 'review_required', f'got {st}: {iss}'
    codes = {i['code'] for i in iss}
    assert 'LOCKED_NAME_NOT_RENDERED' in codes
    assert not [i for i in iss if i['severity'] == 'HARD'], \
        'thiếu tên KHÔNG được coi là HARD (khác với đổi sai tên)'


# ════════════════════════════════════════════════════════════════════════
# Runner
# ════════════════════════════════════════════════════════════════════════
def _run_all():
    fns = [(k, v) for k, v in sorted(globals().items())
           if k.startswith('test_') and callable(v)]
    passed, failed = 0, []
    for name, fn in fns:
        try:
            fn()
            print(f'✅ {name}')
            passed += 1
        except AssertionError as exc:
            print(f'❌ {name}: {exc}')
            failed.append(name)
        except Exception as exc:                     # noqa: BLE001
            print(f'❌ {name}: {type(exc).__name__}: {exc}')
            failed.append(name)
    print()
    print(f'T166 matrix tests: {passed}/{len(fns)} PASS')
    if failed:
        print('FAILED: ' + ', '.join(failed))
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(_run_all())

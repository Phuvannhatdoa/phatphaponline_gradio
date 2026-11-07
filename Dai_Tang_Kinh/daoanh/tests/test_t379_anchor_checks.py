#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T379 follow-up — unit tests cho verify_anchors() trong scripts/etl_gen_compute.py.

Bối cảnh: etl_gen_compute.py DROP + build lại lineage_founders và
person_gen_computed nhưng không tự kiểm tra kết quả, nên sai số có thể
được ghi vào DB mà không báo lỗi. verify_anchors() là lưới an toàn: đối
chiếu các mốc đời đã được Admin xác nhận.

─── T379 follow-up #2 (2026-11-07) — ĐỔI SANG dila_id LÀM KHÓA TRA ─────────
Bản trước tra person_id bằng LIKE theo khai_to_name_vi (tên trong TTL, qua
bảng lineage_founders) — vi phạm quy tắc naming-and-identity.md ("Display
name ... không bao giờ là join key"). Bản mới: Admin đã khóa 33 vị Khai Tổ
Thiền Tông (28 Tổ Ấn Độ + 5 Tổ Trung Hoa, đến Lục Tổ Huệ Năng) trong
scripts/anchors_thientong.json, mỗi vị locked có DILA Person ID xác minh
trực tiếp. ANCHOR_SPECS giờ được load từ file này (build_anchor_specs(),
chỉ lấy mục trạng_thái=="locked" — 22/33, xem test_t379_anchors_thientong_file.py
cho test cấu trúc file JSON) và verify_anchors() tra THẲNG
person_gen_computed.person_id = dila_id, không qua tên, không qua
lineage_founders.

Các test dưới dùng `anchor_specs=` tùy biến (không phải ANCHOR_SPECS đầy đủ
22 mục) để test cơ chế verify_anchors() độc lập với nội dung thật của file
JSON — tránh phải seed 22 dòng cho mỗi test.

Test dùng SQLite in-memory, KHÔNG đụng data/lineage.db thật.

Usage: python -m pytest tests/test_t379_anchor_checks.py -v
"""
import os
import sqlite3
import sys

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DAOANH)

from scripts.etl_gen_compute import (  # noqa: E402
    verify_anchors,
    ANCHOR_SPECS,
    resolve_global_gens,
    is_lamte_lineage,
    is_global_thientong_lineage,
    GLOBAL_THIENTONG_LINEAGES,
    THIENTONG_LAMTE_OFFSET,
)


def _make_db():
    """Tạo DB SQLite in-memory với schema tối thiểu cho person_gen_computed,
    giống schema thật trong setup_tables(). verify_anchors() không còn đụng
    lineage_founders (xem docstring đầu file), nên không cần tạo bảng đó ở đây."""
    conn = sqlite3.connect(':memory:')
    conn.executescript("""
        CREATE TABLE person_gen_computed (
            person_id     TEXT NOT NULL,
            lineage_key   TEXT NOT NULL,
            lineage_name  TEXT,
            gen_sect      INTEGER,
            gen_lamte     INTEGER,
            gen_thientong INTEGER,
            PRIMARY KEY (person_id, lineage_key)
        );
    """)
    return conn


def _seed_gen(conn, rows):
    """rows: list of (person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong)"""
    conn.executemany(
        "INSERT INTO person_gen_computed "
        "(person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong) "
        "VALUES (?,?,?,?,?,?)",
        rows,
    )


# ── Dữ liệu đúng chuẩn (3 mốc dila_id, khớp đúng bộ neo đã khóa) ─────────────

TEST_SPECS = [
    {'label': 'Ma Ha Ca Diếp',   'dila_id': 'A002188', 'checks': {'gen_thientong': 1}},
    {'label': 'Bồ Đề Đạt Ma',    'dila_id': 'A001361', 'checks': {'gen_thientong': 28}},
    {'label': 'Lục Tổ Huệ Năng', 'dila_id': 'A001719', 'checks': {'gen_thientong': 33}},
]

CORRECT_GEN_ROWS = [
    ('A002188', 'dila_global', 'Thiền Tông (DILA)', None, None, 1),
    ('A001361', 'dila_global', 'Thiền Tông (DILA)', None, None, 28),
    ('A001719', 'dila_global', 'Thiền Tông (DILA)', None, None, 33),
]


def test_all_anchors_correct_pass():
    """Mọi mốc đúng → verify_anchors() trả ok=True."""
    conn = _make_db()
    _seed_gen(conn, CORRECT_GEN_ROWS)

    ok, messages = verify_anchors(conn, TEST_SPECS)

    assert ok is True, f"Expected ok=True, messages={messages}"
    assert any('khớp đúng' in m for m in messages)
    conn.close()


def test_one_anchor_wrong_fails_and_caller_can_rollback():
    """
    Một mốc sai (Lục Tổ Huệ Năng: gen_thientong=70 thay vì 33 — đúng kiểu
    lỗi tra nhầm sang người khác) → verify_anchors() trả ok=False, và khi
    caller (main()) rollback() thì bảng phải trống lại (mô phỏng 'bảng cũ
    giữ nguyên' bằng cách rollback về trạng thái trước transaction).
    """
    conn = _make_db()
    bad_rows = list(CORRECT_GEN_ROWS)
    bad_rows[2] = ('A001719', 'dila_global', 'Thiền Tông (DILA)', None, None, 70)
    _seed_gen(conn, bad_rows)

    ok, messages = verify_anchors(conn, TEST_SPECS)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Lục Tổ Huệ Năng' in joined
    assert 'gen_thientong' in joined
    assert 'mong đợi 33' in joined
    assert "thực tế 70" in joined

    # Caller rollback() như main() sẽ làm khi anchors_ok=False.
    conn.rollback()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM person_gen_computed")
    assert cur.fetchone()[0] == 0, "Sau rollback, person_gen_computed phải trống (chưa commit gì)"
    conn.close()


def test_anchor_not_found_fails():
    """Thiếu hẳn 1 mốc trong person_gen_computed (ví dụ Huệ Năng chưa được
    seed) → verify_anchors() báo KHÔNG TÌM THẤY, không coi là đạt."""
    conn = _make_db()
    rows_missing_hue_nang = [r for r in CORRECT_GEN_ROWS if r[0] != 'A001719']
    _seed_gen(conn, rows_missing_hue_nang)

    ok, messages = verify_anchors(conn, TEST_SPECS)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Lục Tổ Huệ Năng' in joined
    assert 'A001719' in joined
    assert 'KHÔNG TÌM THẤY' in joined


def test_anchor_row_exists_but_all_gen_null_fails():
    """Mốc có bản ghi trong person_gen_computed nhưng gen_sect/gen_lamte/
    gen_thientong đều NULL (ETL bị dừng giữa đường trước khi tính xong)
    → verify_anchors() phải báo không đạt, không coi None là khớp."""
    conn = _make_db()
    rows = [r for r in CORRECT_GEN_ROWS if r[0] != 'A001719']
    rows.append(('A001719', 'dila_global', 'Thiền Tông (DILA)', None, None, None))
    _seed_gen(conn, rows)

    ok, messages = verify_anchors(conn, TEST_SPECS)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Lục Tổ Huệ Năng' in joined
    assert 'tất cả gen_* đều NULL' in joined


def test_ambiguous_dila_id_match_fails():
    """Nếu 2 bản ghi person_gen_computed cùng person_id (khác lineage_key —
    dữ liệu lỗi/trùng) → verify_anchors() phải coi là KHÔNG ĐẠT, không tự
    chọn đại 1 bản ghi."""
    conn = _make_db()
    rows = list(CORRECT_GEN_ROWS)
    rows.append(('A002188', 'dila_global_dup', 'Thiền Tông (DILA, bản trùng)', None, None, 1))
    _seed_gen(conn, rows)

    ok, messages = verify_anchors(conn, TEST_SPECS)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Ma Ha Ca Diếp' in joined
    assert 'ambiguous' in joined


def test_anchor_specs_loaded_from_locked_file_entries():
    """Đảm bảo ANCHOR_SPECS được nạp từ scripts/anchors_thientong.json: đúng
    22 mục locked, mỗi mục có dila_id dạng A\\d+ và checks chỉ chứa
    gen_thientong (không còn name_pattern/gen_lamte như bản cũ dựa tên)."""
    assert len(ANCHOR_SPECS) == 22
    by_id = {spec['dila_id']: spec for spec in ANCHOR_SPECS}

    for spec in ANCHOR_SPECS:
        assert 'name_pattern' not in spec
        assert set(spec['checks']) == {'gen_thientong'}
        assert spec['dila_id'].startswith('A')
        assert spec['dila_id'][1:].isdigit()

    # Đối chiếu một vài mốc đã biết trong bộ neo Admin khóa 2026-11-07.
    assert by_id['A002188']['checks']['gen_thientong'] == 1    # Ma Ha Ca Diếp
    assert by_id['A001361']['checks']['gen_thientong'] == 28   # Bồ Đề Đạt Ma
    assert by_id['A000237']['checks']['gen_thientong'] == 32   # Hoằng Nhẫn
    assert by_id['A001719']['checks']['gen_thientong'] == 33   # Lục Tổ Huệ Năng

    ids = [spec['dila_id'] for spec in ANCHOR_SPECS]
    assert len(ids) == len(set(ids)), "ANCHOR_SPECS không được có dila_id trùng"


# ── T379 follow-up — test cho công thức mới resolve_global_gens() ───────────
# Bối cảnh: bản cũ coi generationOrder trong TTL là "đời Lâm Tế" rồi CỘNG 37
# ra đời Thiền Tông (sai). Đối chiếu trực tiếp TTL cho thấy generationOrder
# ĐÃ LÀ đời Thiền Tông toàn cục. Các test dưới khóa công thức mới:
#   gen_thientong = generationOrder (nếu lineage nằm trong allowlist global)
#   gen_lamte     = generationOrder - 37 (chỉ nếu lineage chứa "Lâm Tế")
#   lineage KHÔNG xác minh được (Đại thừa/Tịnh Độ Tông/Phái Nam Nhạc/...)
#   → (None, None), không đoán.

def test_resolve_global_gens_four_confirmed_milestones():
    """4 mốc Admin xác nhận phải khớp đúng qua resolve_global_gens()."""
    assert resolve_global_gens(1, 'Thiền Tông Ấn Độ') == (None, 1)       # Ma Ha Ca Diếp
    assert resolve_global_gens(28, 'Thiền Tông Ấn Độ') == (None, 28)      # Bồ Đề Đạt Ma
    assert resolve_global_gens(33, 'Thiền Tông Trung Hoa - Nam Tông') == (None, 33)  # Huệ Năng
    assert resolve_global_gens(38, 'Tông Lâm Tế Trung Hoa') == (1, 38)    # Lâm Tế Nghĩa Huyền


def test_resolve_global_gens_lamte_branches_use_global_generation_order():
    """Mọi nhánh Lâm Tế (Trung Hoa và Việt Nam) đều dùng generationOrder trực
    tiếp làm gen_thientong, và trừ 37 ra gen_lamte — không reset về nhỏ khi
    đổi dharmaLineageName (Dương Kỳ/Hoàng Long/Gia Phổ/Chúc Thánh/Liễu Quán)."""
    assert resolve_global_gens(45, 'Dòng Lâm Tế Dương Kỳ') == (8, 45)       # Dương Kỳ Phương Hội
    assert resolve_global_gens(48, 'Dòng Lâm Tế Dương Kỳ') == (11, 48)      # Viên Ngộ Khắc Cần
    assert resolve_global_gens(70, 'Dòng Lâm Tế Gia Phổ Việt Nam') == (33, 70)   # Nguyên Thiều
    assert resolve_global_gens(71, 'Dòng Lâm Tế Chúc Thánh Việt Nam') == (34, 71)  # Minh Hải Pháp Bảo
    assert resolve_global_gens(72, 'Dòng Lâm Tế Liễu Quán Việt Nam') == (35, 72)   # Thiệt Duyệt Liễu Quán


def test_resolve_global_gens_non_lamte_global_has_no_gen_lamte():
    """Thiền Tông Ấn Độ / Trung Hoa / Ngưu Đầu / Quy Ngưỡng: có gen_thientong
    nhưng KHÔNG có gen_lamte (không thuộc dòng Lâm Tế)."""
    assert resolve_global_gens(32, 'Ngưu Đầu Tông Trung Hoa') == (None, 32)  # Ngưu Đầu Pháp Dung
    assert resolve_global_gens(37, 'Tông Quy Ngưỡng Trung Hoa') == (None, 37)  # Quy Sơn Linh Hựu
    assert resolve_global_gens(19, 'Kinh Lượng Bộ') == (None, 19)            # Cưu Ma La Đa
    assert resolve_global_gens(14, 'Bát Tông') == (None, 14)                  # Bồ Tát Long Thọ


def test_resolve_global_gens_excludes_unverified_local_lineages():
    """Lineage đã phát hiện dùng số đời CỤC BỘ (không nối mạch toàn cục) phải
    trả về (None, None), KHÔNG được đoán gen_thientong = generationOrder."""
    assert resolve_global_gens(1, 'Đại thừa') == (None, None)        # Thích Ca — trùng Ca Diếp=1
    assert resolve_global_gens(2, 'Tịnh Độ Tông') == (None, None)     # Đạo Xước — hệ Tổ Tịnh Độ riêng
    assert resolve_global_gens(2, 'Phái Nam Nhạc') == (None, None)    # Bổn Khê — lệch với Mã Tổ=35


def test_resolve_global_gens_unknown_future_lineage_is_excluded_by_default():
    """Tên dharmaLineageName mới/lạ chưa có trong allowlist → mặc định loại
    (None, None), không tự động coi là global cho tới khi được xác minh."""
    assert resolve_global_gens(50, 'Một Tông Phái Chưa Từng Thấy') == (None, None)


def test_resolve_global_gens_none_inputs():
    assert resolve_global_gens(None, 'Thiền Tông Ấn Độ') == (None, None)
    assert resolve_global_gens(10, '') == (None, None)
    assert resolve_global_gens(10, None) == (None, None)


def test_is_lamte_lineage_matches_any_lam_te_variant():
    assert is_lamte_lineage('Tông Lâm Tế Trung Hoa') is True
    assert is_lamte_lineage('Dòng Lâm Tế Dương Kỳ') is True
    assert is_lamte_lineage('Dòng Lâm Tế Hoàng Long') is True
    assert is_lamte_lineage('Dòng Lâm Tế Gia Phổ Việt Nam') is True
    assert is_lamte_lineage('Dòng Lâm Tế Chúc Thánh Việt Nam') is True
    assert is_lamte_lineage('Dòng Lâm Tế Liễu Quán Việt Nam') is True
    assert is_lamte_lineage('Thiền Tông Ấn Độ') is False
    assert is_lamte_lineage('') is False
    assert is_lamte_lineage(None) is False


def test_is_global_thientong_lineage_allowlist_is_not_guessed_open():
    """Allowlist chỉ chứa các tên đã đối chiếu thủ công — test này khóa lại
    danh sách để tránh ai vô tình thêm bớt mà không ghi lại lý do/đối chiếu."""
    assert GLOBAL_THIENTONG_LINEAGES == frozenset({
        'Thiền Tông Ấn Độ',
        'Thiền Tông Trung Hoa',
        'Thiền Tông Trung Hoa - Nam Tông',
        'Thiền Tông Trung Hoa - Bắc Tông',
        'Ngưu Đầu Tông Trung Hoa',
        'Tông Quy Ngưỡng Trung Hoa',
        'Kinh Lượng Bộ',
        'Bát Tông',
    })
    assert THIENTONG_LAMTE_OFFSET == 37
    assert is_global_thientong_lineage('Đại thừa') is False
    assert is_global_thientong_lineage('Tịnh Độ Tông') is False
    assert is_global_thientong_lineage('Phái Nam Nhạc') is False
    assert is_global_thientong_lineage('Tông Lâm Tế Trung Hoa') is True
    assert is_global_thientong_lineage('Thiền Tông Ấn Độ') is True


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))

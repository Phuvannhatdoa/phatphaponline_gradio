#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T379 follow-up — unit tests cho verify_anchors() trong scripts/etl_gen_compute.py.

Bối cảnh: etl_gen_compute.py DROP + build lại lineage_founders và
person_gen_computed nhưng không tự kiểm tra kết quả, nên sai số có thể
được ghi vào DB mà không báo lỗi. verify_anchors() là lưới an toàn: đối
chiếu 4 mốc đời đã được Admin xác nhận (2026-11-07):
    Ma Ha Ca Diếp      = Thiền Tông đời 1
    Bồ Đề Đạt Ma       = Thiền Tông đời 28
    Lục Tổ Huệ Năng    = Thiền Tông đời 33
    Lâm Tế Nghĩa Huyền = Thiền Tông đời 38 (gen_lamte = 1)

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
    """Tạo DB SQLite in-memory với schema tối thiểu cho lineage_founders +
    person_gen_computed, giống schema thật trong setup_tables()/seed_founders().
    """
    conn = sqlite3.connect(':memory:')
    conn.executescript("""
        CREATE TABLE lineage_founders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lineage_name    TEXT NOT NULL UNIQUE,
            lineage_key     TEXT NOT NULL UNIQUE,
            khai_to_id      TEXT NOT NULL,
            khai_to_name_vi TEXT,
            khai_to_gen     INTEGER
        );
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


def _seed_founders(conn, founders):
    """founders: list of (lineage_name, lineage_key, khai_to_id, khai_to_name_vi, khai_to_gen)"""
    conn.executemany(
        "INSERT INTO lineage_founders "
        "(lineage_name, lineage_key, khai_to_id, khai_to_name_vi, khai_to_gen) "
        "VALUES (?,?,?,?,?)",
        founders,
    )


def _seed_gen(conn, rows):
    """rows: list of (person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong)"""
    conn.executemany(
        "INSERT INTO person_gen_computed "
        "(person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong) "
        "VALUES (?,?,?,?,?,?)",
        rows,
    )


# ── Dữ liệu đúng chuẩn (4 mốc khớp hệt giá trị Admin xác nhận) ────────────────

CORRECT_FOUNDERS = [
    ('Thiền Tông Ấn Độ',             'tt_an_do',   'ma_ha_ca_diep',     'Tôn Giả Ma Ha Ca Diếp',     1),
    ('Thiền Tông Ấn Độ 2',           'tt_an_do_2', 'bo_de_dat_ma',      'Tôn Giả Bồ Đề Đạt Ma',      28),
    ('Thiền Tông Trung Hoa - Nam Tông', 'tt_nam',  'dai_giam_hue_nang', 'Tôn Giả Đại Giám Huệ Năng', 33),
    ('Tông Lâm Tế Trung Hoa',        'lam_te',     'lam_te_nghia_huyen', 'Lâm Tế Nghĩa Huyền',       38),
]

CORRECT_GEN_ROWS = [
    ('ma_ha_ca_diep',      'tt_an_do',   'Thiền Tông Ấn Độ',               1, None, 1),
    ('bo_de_dat_ma',       'tt_an_do_2', 'Thiền Tông Ấn Độ 2',             1, None, 28),
    ('dai_giam_hue_nang',  'tt_nam',     'Thiền Tông Trung Hoa - Nam Tông', 1, None, 33),
    ('lam_te_nghia_huyen', 'lam_te',     'Tông Lâm Tế Trung Hoa',           1, 1,    38),
]


def test_all_anchors_correct_pass():
    """Mọi mốc đúng → verify_anchors() trả ok=True."""
    conn = _make_db()
    _seed_founders(conn, CORRECT_FOUNDERS)
    _seed_gen(conn, CORRECT_GEN_ROWS)

    ok, messages = verify_anchors(conn)

    assert ok is True, f"Expected ok=True, messages={messages}"
    assert any('khớp đúng' in m for m in messages)
    conn.close()


def test_one_anchor_wrong_fails_and_caller_can_rollback():
    """
    Một mốc sai (Lâm Tế Nghĩa Huyền: gen_thientong=75 thay vì 38 — đúng kiểu
    lỗi offset +37 áp sai công thức) → verify_anchors() trả ok=False, và khi
    caller (main()) rollback() thì bảng phải trống lại (mô phỏng 'bảng cũ
    giữ nguyên' bằng cách rollback về trạng thái trước transaction).
    """
    conn = _make_db()
    _seed_founders(conn, CORRECT_FOUNDERS)
    bad_rows = list(CORRECT_GEN_ROWS)
    # Lâm Tế Nghĩa Huyền bị tính sai: gen_thientong=75 (=38+37, lỗi cộng offset
    # 2 lần) thay vì 38 đúng theo mốc Admin xác nhận.
    bad_rows[3] = ('lam_te_nghia_huyen', 'lam_te', 'Tông Lâm Tế Trung Hoa', 1, 38, 75)
    _seed_gen(conn, bad_rows)

    ok, messages = verify_anchors(conn)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Lâm Tế Nghĩa Huyền' in joined
    assert 'gen_thientong' in joined
    assert 'mong đợi 38' in joined
    assert "thực tế 75" in joined

    # Caller rollback() như main() sẽ làm khi anchors_ok=False.
    conn.rollback()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM lineage_founders")
    assert cur.fetchone()[0] == 0, "Sau rollback, lineage_founders phải trống (chưa commit gì)"
    cur.execute("SELECT COUNT(*) FROM person_gen_computed")
    assert cur.fetchone()[0] == 0, "Sau rollback, person_gen_computed phải trống (chưa commit gì)"
    conn.close()


def test_gen_lamte_mismatch_for_lam_te_fails():
    """Lâm Tế Nghĩa Huyền đúng gen_thientong=38 nhưng gen_lamte sai (=38 thay vì 1)."""
    conn = _make_db()
    _seed_founders(conn, CORRECT_FOUNDERS)
    bad_rows = list(CORRECT_GEN_ROWS)
    bad_rows[3] = ('lam_te_nghia_huyen', 'lam_te', 'Tông Lâm Tế Trung Hoa', 1, 38, 38)
    _seed_gen(conn, bad_rows)

    ok, messages = verify_anchors(conn)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'gen_lamte' in joined
    assert 'mong đợi 1' in joined


def test_anchor_not_found_fails():
    """Thiếu hẳn 1 mốc trong lineage_founders (ví dụ Huệ Năng chưa được seed)
    → verify_anchors() báo KHÔNG TÌM THẤY, không coi là đạt."""
    conn = _make_db()
    founders_missing_hue_nang = [f for f in CORRECT_FOUNDERS if f[2] != 'dai_giam_hue_nang']
    rows_missing_hue_nang = [r for r in CORRECT_GEN_ROWS if r[0] != 'dai_giam_hue_nang']
    _seed_founders(conn, founders_missing_hue_nang)
    _seed_gen(conn, rows_missing_hue_nang)

    ok, messages = verify_anchors(conn)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Lục Tổ Huệ Năng' in joined
    assert 'KHÔNG TÌM THẤY' in joined


def test_anchor_found_but_no_computed_row_fails():
    """Mốc có trong lineage_founders nhưng chưa có bản ghi trong
    person_gen_computed (ETL bị dừng giữa đường / compute_slug_monks
    chưa chạy) → verify_anchors() phải báo không đạt, không coi None là khớp."""
    conn = _make_db()
    _seed_founders(conn, CORRECT_FOUNDERS)
    rows_without_lamte_founder = [r for r in CORRECT_GEN_ROWS if r[0] != 'lam_te_nghia_huyen']
    _seed_gen(conn, rows_without_lamte_founder)

    ok, messages = verify_anchors(conn)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Lâm Tế Nghĩa Huyền' in joined
    assert 'KHÔNG có bản ghi tương ứng' in joined


def test_ambiguous_name_match_fails():
    """Nếu 2 bản ghi lineage_founders cùng khớp pattern tên của 1 mốc
    (homonym / dữ liệu trùng tên) → verify_anchors() phải coi là KHÔNG ĐẠT,
    không tự chọn đại 1 bản ghi."""
    conn = _make_db()
    dup_founders = list(CORRECT_FOUNDERS)
    dup_founders.append(
        ('Thiền Tông Ấn Độ (bản trùng)', 'tt_an_do_dup', 'ma_ha_ca_diep_dup',
         'Tôn Giả Ma Ha Ca Diếp', 1)
    )
    _seed_founders(conn, dup_founders)
    rows = list(CORRECT_GEN_ROWS)
    rows.append(('ma_ha_ca_diep_dup', 'tt_an_do_dup', 'Thiền Tông Ấn Độ (bản trùng)', 1, None, 1))
    _seed_gen(conn, rows)

    ok, messages = verify_anchors(conn)

    assert ok is False
    joined = '\n'.join(messages)
    assert 'Ma Ha Ca Diếp' in joined
    assert 'ambiguous' in joined


def test_anchor_specs_cover_four_confirmed_milestones():
    """Đảm bảo ANCHOR_SPECS đúng 4 mốc Admin xác nhận, không bị sửa nhầm."""
    labels = {spec['label'] for spec in ANCHOR_SPECS}
    assert labels == {
        'Ma Ha Ca Diếp',
        'Bồ Đề Đạt Ma',
        'Lục Tổ Huệ Năng',
        'Lâm Tế Nghĩa Huyền',
    }
    by_label = {spec['label']: spec['checks'] for spec in ANCHOR_SPECS}
    assert by_label['Ma Ha Ca Diếp']['gen_thientong'] == 1
    assert by_label['Bồ Đề Đạt Ma']['gen_thientong'] == 28
    assert by_label['Lục Tổ Huệ Năng']['gen_thientong'] == 33
    assert by_label['Lâm Tế Nghĩa Huyền']['gen_thientong'] == 38
    assert by_label['Lâm Tế Nghĩa Huyền']['gen_lamte'] == 1


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

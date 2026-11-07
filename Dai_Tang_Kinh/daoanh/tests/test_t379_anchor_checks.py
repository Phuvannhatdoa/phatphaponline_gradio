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

from scripts.etl_gen_compute import verify_anchors, ANCHOR_SPECS  # noqa: E402


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


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T379 follow-up #3 — test cấu trúc file scripts/anchors_khai_to_dong.json (bộ
neo Khai Tổ các dòng/tông Thiền Tông SAU Lục Tổ Huệ Năng: Nam Nhạc + Thanh
Nguyên nhánh gốc, Quy Ngưỡng/Lâm Tế/Tào Động/Vân Môn/Pháp Nhãn — Ngũ Gia
Thất Tông — Admin khóa 2026-11-07).

File này TÁCH RIÊNG khỏi scripts/anchors_thientong.json (file đó chỉ chứa 33
mục đời 1..33 đến Lục Tổ) vì các vị dưới đây có đời 34-45, nằm ngoài phạm vi
33 mục và sẽ phá vỡ invariant đời 1..33 của test_t379_anchors_thientong_file.py
nếu nhét chung.

Phạm vi test: chỉ kiểm DỮ LIỆU TĨNH trong file JSON (đọc đúng số mục, định
dạng dila_id, không trùng ID, đời khớp mốc đã đối chiếu bằng BFS qua
lineage_edge_consensus trên bản sao DB cô lập) — KHÔNG đụng data/lineage.db
thật, KHÔNG chạy ETL.

Usage: python -m pytest tests/test_t379_khai_to_dong_anchors.py -v
"""
import json
import os
import re
import sys

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DAOANH)

ANCHORS_FILE = os.path.join(DAOANH, 'scripts', 'anchors_khai_to_dong.json')

DILA_ID_RE = re.compile(r'^A\d+$')

# Mốc đã đối chiếu bằng BFS (relation_type='dharma_transmission',
# consensus_status IN ('confirmed_2plus','single_source'), gốc A002188
# bước=0, đời=bước+1) trên bản sao cô lập của data/lineage.db, đối chiếu với
# mốc lịch sử Admin cung cấp 2026-11-07. Xem _meta.method trong file JSON.
EXPECTED_LOCKED = {
    'A004015': 34,   # Nam Nhạc Hoài Nhượng
    'A003666': 34,   # Thanh Nguyên Hành Tư
    'A001984': 37,   # Quy Sơn Linh Hựu
    'A003627': 38,   # Lâm Tế Nghĩa Huyền
    'A009489': 38,   # Động Sơn Lương Giới
    'A009449': 39,   # Tào Sơn Bản Tịch
    'A003703': 39,   # Vân Môn Văn Yển
    'A003921': 45,   # Hoàng Long Huệ Nam
    'A004146': 45,   # Dương Kỳ Phương Hội
    'A000174': 40,   # Pháp Nhãn Văn Ích (nối pháp La Hán Quế Sâm A010683, đời 39)
    'A009491': 38,   # Ngưỡng Sơn Huệ Tịch (Admin xác nhận 2026-11-08, đệ tử Quy Sơn đời 37)
}

# Khai tổ tông NGOÀI Thiền: không nằm trong đồ thị truyền thừa Thiền (không BFS
# từ Ma Ha Ca Diếp), quy ước đời 1 = khai tổ tông (Admin 2026-11-08).
EXPECTED_NON_THIEN = {
    'A001301': 1,    # Trí Khải (Thiên Thai / Pháp Hoa)
    'A001482': 1,    # Long Thọ (Tam Luận)
    'A003867': 1,    # Pháp Dung (Ngưu Đầu tông) — Admin xác nhận 2026-11-08
}

# ID Admin xác nhận KHÔNG phải Tổ Thiền Tông — không được xuất hiện trong bộ
# neo này dưới bất kỳ dila_id nào (xem _meta.excluded_note).
EXCLUDED_DILA_IDS = {'A000587'}  # Khuê Phong Tông Mật


def load_anchors():
    with open(ANCHORS_FILE, encoding='utf-8') as f:
        raw = json.load(f)
    return raw['anchors'] if isinstance(raw, dict) and 'anchors' in raw else raw


def test_anchors_file_exists():
    assert os.path.isfile(ANCHORS_FILE), f"Không tìm thấy {ANCHORS_FILE}"


def test_reads_exactly_14_entries():
    anchors = load_anchors()
    assert len(anchors) == 14, f"Kỳ vọng 14 mục, thực tế {len(anchors)}"


def test_split_locked_unresolved_counts():
    anchors = load_anchors()
    locked = [a for a in anchors if a['trang_thai'] == 'locked']
    unresolved = [a for a in anchors if a['trang_thai'] == 'unresolved']
    assert len(locked) == 14, f"Kỳ vọng 14 locked, thực tế {len(locked)}"
    assert len(unresolved) == 0, f"Kỳ vọng 0 unresolved, thực tế {len(unresolved)}"
    assert {a['trang_thai'] for a in anchors} == {'locked'}


def test_every_locked_entry_has_valid_dila_id_and_doi():
    anchors = load_anchors()
    for a in anchors:
        if a['trang_thai'] != 'locked':
            continue
        dila_id = a.get('dila_id')
        assert dila_id, f"Mục locked '{a.get('ten_viet')}' thiếu dila_id"
        assert DILA_ID_RE.match(dila_id), (
            f"dila_id '{dila_id}' không đúng định dạng A\\d+"
        )
        assert isinstance(a.get('doi'), int), (
            f"Mục locked '{a.get('ten_viet')}' thiếu đời (int)"
        )
        assert a.get('buoc_tu_capdiep') == a['doi'] - 1, (
            f"'{a.get('ten_viet')}': buoc_tu_capdiep phải = doi - 1"
        )


def test_every_unresolved_entry_has_no_dila_id_and_no_doi():
    anchors = load_anchors()
    for a in anchors:
        if a['trang_thai'] != 'unresolved':
            continue
        assert a.get('dila_id') is None, (
            f"Mục unresolved '{a.get('ten_viet')}' không được có dila_id"
        )
        assert a.get('doi') is None, (
            f"Mục unresolved '{a.get('ten_viet')}' không được có đời"
        )


def test_no_duplicate_dila_id():
    anchors = load_anchors()
    ids = [a['dila_id'] for a in anchors if a.get('dila_id')]
    assert len(ids) == len(set(ids)), (
        f"Có dila_id trùng: {sorted(x for x in ids if ids.count(x) > 1)}"
    )


def test_locked_dila_ids_and_doi_match_bfs_verified_values():
    """Đối chiếu nguyên văn các mốc đã kiểm bằng BFS qua lineage_edge_consensus
    (xem docstring đầu file) — phát hiện lỗi gõ nhầm hoặc khóa sai đời."""
    anchors = load_anchors()
    by_id = {a['dila_id']: a for a in anchors if a['trang_thai'] == 'locked'}
    expected = {**EXPECTED_LOCKED, **EXPECTED_NON_THIEN}
    assert set(by_id) == set(expected), (
        f"Bộ dila_id locked thực tế {sorted(by_id)} khác kỳ vọng "
        f"{sorted(expected)}"
    )
    for dila_id, expected_doi in expected.items():
        assert by_id[dila_id]['doi'] == expected_doi, (
            f"{dila_id}: kỳ vọng đời {expected_doi}, thực tế {by_id[dila_id]['doi']}"
        )


def test_nguong_son_hue_tich_is_locked_at_gen_38():
    """Ngưỡng Sơn Huệ Tịch (A009491): Admin xác nhận 2026-11-08 — đệ tử Quy
    Sơn (đời 37) ⇒ đời 38; từ Mã Tổ (đời 35) là đời thứ 3."""
    anchors = load_anchors()
    entry = next(a for a in anchors if a.get('ten_viet') == 'Ngưỡng Sơn Huệ Tịch')
    assert entry['trang_thai'] == 'locked'
    assert entry.get('dila_id') == 'A009491'
    assert entry.get('doi') == 38


def test_non_thien_founders_are_gen_1():
    """Khai tổ tông ngoài Thiền (Trí Khải, Long Thọ): đời 1 của tông đó."""
    anchors = load_anchors()
    for dila_id, doi in EXPECTED_NON_THIEN.items():
        entry = next(a for a in anchors if a.get('dila_id') == dila_id)
        assert entry['trang_thai'] == 'locked'
        assert entry['doi'] == doi
        assert entry['buoc_tu_capdiep'] == 0


def test_phap_nhan_van_ich_is_locked_with_teacher_chain():
    """Pháp Nhãn Văn Ích (A000174, 文益): Admin xác nhận 2026-11-08, nối pháp
    dòng La Hán Quế Sâm (A010683, đời 39) → đời 40."""
    anchors = load_anchors()
    entry = next(a for a in anchors if a.get('ten_viet') == 'Pháp Nhãn Văn Ích')
    assert entry['trang_thai'] == 'locked'
    assert entry.get('dila_id') == 'A000174'
    assert entry.get('doi') == 40


def test_excluded_dila_ids_never_appear_in_anchors():
    """Khuê Phong Tông Mật (A000587): Admin xác nhận KHÔNG phải Tổ Thiền
    Tông — không được xuất hiện trong bộ neo này dưới bất kỳ hình thức nào,
    dù BFS có tính ra một đường/đời cho ID này."""
    anchors = load_anchors()
    ids_present = {a['dila_id'] for a in anchors if a.get('dila_id')}
    overlap = ids_present & EXCLUDED_DILA_IDS
    assert not overlap, f"ID bị loại trừ lại xuất hiện trong bộ neo: {overlap}"


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))

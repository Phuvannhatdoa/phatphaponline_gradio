#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T379 — test cấu trúc file scripts/anchors_thientong.json (bộ neo 33 vị Khai
Tổ Thiền Tông, 28 Tổ Ấn Độ + 5 Tổ Trung Hoa đến Lục Tổ Huệ Năng, Admin khóa
2026-11-07).

Phạm vi test: chỉ kiểm DỮ LIỆU TĨNH trong file JSON (đọc đúng 33 mục, định
dạng dila_id, đời khớp chuỗi, không trùng ID) — KHÔNG đụng DB, KHÔNG chạy
etl_gen_compute.main(). Test cơ chế verify_anchors()/ANCHOR_SPECS nằm ở
tests/test_t379_anchor_checks.py.

Usage: python -m pytest tests/test_t379_anchors_thientong_file.py -v
"""
import os
import re
import sys

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DAOANH)

from scripts.etl_gen_compute import (  # noqa: E402
    load_anchors_file,
    build_anchor_specs,
    ANCHORS_FILE,
)

DILA_ID_RE = re.compile(r'^A\d+$')

# Thứ tự đời theo chuỗi truyền pháp Admin đã khóa 2026-11-07 (xem prompt task
# T379 / _meta trong file JSON). 22 locked + 11 unresolved = 33.
EXPECTED_LOCKED_DOI = [1, 2, 3, 5, 6, 8, 12, 14, 15, 17, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]
EXPECTED_UNRESOLVED_DOI = [4, 7, 9, 10, 11, 13, 16, 18, 19, 21, 22]

# Các mốc DILA ID Admin cung cấp trực tiếp trong prompt — đối chiếu nguyên văn
# để tránh lỗi gõ nhầm khi tạo file.
EXPECTED_LOCKED_BY_DOI = {
    1: 'A002188', 2: 'A003861', 3: 'A008803', 5: 'A008802', 6: 'A008801',
    8: 'A008799', 12: 'A001003', 14: 'A001482', 15: 'A001207', 17: 'A008795',
    20: 'A008793', 23: 'A008791', 24: 'A008790', 25: 'A008789', 26: 'A008788',
    27: 'A004683', 28: 'A001361', 29: 'A003881', 30: 'A001601', 31: 'A003654',
    32: 'A000237', 33: 'A001719',
}


def test_anchors_file_exists_at_expected_path():
    assert os.path.isfile(ANCHORS_FILE), f"Không tìm thấy {ANCHORS_FILE}"


def test_reads_exactly_33_entries():
    anchors = load_anchors_file()
    assert len(anchors) == 33, f"Kỳ vọng 33 mục, thực tế {len(anchors)}"


def test_split_locked_unresolved_counts():
    anchors = load_anchors_file()
    locked = [a for a in anchors if a['trang_thai'] == 'locked']
    unresolved = [a for a in anchors if a['trang_thai'] == 'unresolved']
    assert len(locked) == 22, f"Kỳ vọng 22 locked, thực tế {len(locked)}"
    assert len(unresolved) == 11, f"Kỳ vọng 11 unresolved, thực tế {len(unresolved)}"
    # Không có trạng_thái lạ ngoài 2 giá trị này.
    assert {a['trang_thai'] for a in anchors} == {'locked', 'unresolved'}


def test_every_locked_entry_has_dila_id_format_a_digits():
    anchors = load_anchors_file()
    for a in anchors:
        if a['trang_thai'] != 'locked':
            continue
        dila_id = a.get('dila_id')
        assert dila_id, f"Mục locked đời {a['doi']} thiếu dila_id"
        assert DILA_ID_RE.match(dila_id), (
            f"dila_id '{dila_id}' (đời {a['doi']}) không đúng định dạng A\\d+"
        )


def test_every_unresolved_entry_has_no_dila_id_and_no_names():
    """Quy tắc 'không đoán ID': mục unresolved phải để trống dila_id (và
    không tự điền tên Việt/Hán vì chưa xác định nhân vật tương ứng)."""
    anchors = load_anchors_file()
    for a in anchors:
        if a['trang_thai'] != 'unresolved':
            continue
        assert a.get('dila_id') is None, (
            f"Mục unresolved đời {a['doi']} không được có dila_id (tránh đoán ID)"
        )
        assert a.get('ten_viet') is None, (
            f"Mục unresolved đời {a['doi']} không được có tên Việt (chưa xác định nhân vật)"
        )


def test_doi_sequence_matches_locked_and_unresolved_split():
    anchors = load_anchors_file()
    locked_doi = sorted(a['doi'] for a in anchors if a['trang_thai'] == 'locked')
    unresolved_doi = sorted(a['doi'] for a in anchors if a['trang_thai'] == 'unresolved')
    assert locked_doi == EXPECTED_LOCKED_DOI
    assert unresolved_doi == EXPECTED_UNRESOLVED_DOI

    # Toàn bộ đời 1..33 phải được dùng đúng 1 lần (không thiếu, không trùng).
    all_doi = sorted(a['doi'] for a in anchors)
    assert all_doi == list(range(1, 34))


def test_no_duplicate_dila_id_across_generations():
    anchors = load_anchors_file()
    ids = [a['dila_id'] for a in anchors if a['dila_id']]
    assert len(ids) == len(set(ids)), (
        f"Có dila_id trùng giữa các đời: {sorted(x for x in ids if ids.count(x) > 1)}"
    )


def test_locked_dila_ids_match_admin_approved_values():
    """Đối chiếu nguyên văn 22 dila_id Admin cung cấp trong prompt duyệt
    lệnh — phát hiện lỗi gõ nhầm khi tạo file JSON."""
    anchors = load_anchors_file()
    by_doi = {a['doi']: a for a in anchors if a['trang_thai'] == 'locked'}
    assert set(by_doi) == set(EXPECTED_LOCKED_BY_DOI)
    for doi, expected_id in EXPECTED_LOCKED_BY_DOI.items():
        assert by_doi[doi]['dila_id'] == expected_id, (
            f"Đời {doi}: kỳ vọng dila_id={expected_id}, thực tế={by_doi[doi]['dila_id']}"
        )


def test_build_anchor_specs_excludes_unresolved_and_bad_format():
    """build_anchor_specs() phải loại hết mục unresolved (dila_id=None) và
    bất kỳ mục có dila_id sai định dạng — chỉ build_anchor_specs() cho 22
    mục locked hợp lệ."""
    specs = build_anchor_specs()
    assert len(specs) == 22
    for spec in specs:
        assert DILA_ID_RE.match(spec['dila_id'])
        assert isinstance(spec['checks']['gen_thientong'], int)

    # Thử trộn thêm 1 mục giả có dila_id sai định dạng + 1 mục unresolved →
    # vẫn phải bị loại, không lọt vào specs.
    anchors = load_anchors_file()
    tampered = list(anchors) + [
        {'doi': 99, 'ten_viet': 'Giả', 'ten_han': None, 'dila_id': 'XYZ', 'trang_thai': 'locked', 'nguon_ghichu': ''},
        {'doi': 100, 'ten_viet': None, 'ten_han': None, 'dila_id': None, 'trang_thai': 'unresolved', 'nguon_ghichu': ''},
    ]
    specs2 = build_anchor_specs(tampered)
    assert len(specs2) == 22, "Mục dila_id sai định dạng / unresolved không được lọt vào ANCHOR_SPECS"


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))

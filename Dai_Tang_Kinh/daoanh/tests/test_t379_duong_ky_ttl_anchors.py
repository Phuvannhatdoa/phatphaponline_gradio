#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T379 — test cấu trúc file scripts/anchors_duong_ky_ttl.json (bộ neo dòng
Lâm Tế Dương Kỳ đọc từ TTL, đời 45-70).

Nguồn: bkg:generationOrder / bkg:hasTeacher / rdfs:label@vi đọc trực tiếp từ
data/ttl/*.ttl (Admin tạo, KHÔNG git-track). trang_thai=locked CHỈ khi Admin
đã xác nhận đời DILA khớp với TTL; trang_thai=conflict khi có dila_id nhưng
đời DILA lệch TTL; trang_thai=ttl_only khi chưa có dila_id xác minh khớp đời.

File JSON này KHÔNG git-track theo mặc định (*.json bị ignore ở .gitignore
gốc) — có ngoại lệ riêng, xem .gitignore dòng
'!Dai_Tang_Kinh/daoanh/scripts/anchors_duong_ky_ttl.json'.

Phạm vi test: chỉ kiểm DỮ LIỆU TĨNH trong file JSON — KHÔNG đụng
data/lineage.db, KHÔNG đọc lại các file TTL gốc (data/ttl/ không được
git-track nên không đảm bảo có mặt trong mọi worktree).

Usage: python -m pytest tests/test_t379_duong_ky_ttl_anchors.py -v
"""
import json
import os
import re
import sys

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DAOANH)

ANCHORS_FILE = os.path.join(DAOANH, 'scripts', 'anchors_duong_ky_ttl.json')

DILA_ID_RE = re.compile(r'^A\d+$')

VALID_STATUSES = {'locked', 'ttl_only', 'conflict'}

# Mốc Admin xác nhận 2026-11-07 (xem prompt task T379 / _meta trong file JSON).
EXPECTED_LOCKED = {
    'A004146': 45,  # Dương Kỳ Phương Hội (đã khóa trước ở anchors_khai_to_dong.json)
    'A004691': 51,  # Mật Am Hàn Kiệt (DILA: Hàm Kiệt)
    'A004696': 52,  # Phá Am Tổ Tiên
    'A004697': 53,  # Vô Chuẩn Sư Phạm
}

# dila_id có mặt nhưng đời DILA lệch với TTL — GHI RÕ, KHÔNG dùng để khóa đời.
EXPECTED_CONFLICT = {
    'A001513': 68,  # Đạo Mân Mộc Trần — DILA ghi đời 64
    'A044921': 70,  # Nguyên Thiều Siêu Bạch — DILA ghi đời 66
}

REQUIRED_FIELDS = {'doi', 'ten_viet', 'file_ttl', 'thay_ttl', 'dila_id', 'trang_thai'}


def load_anchors():
    with open(ANCHORS_FILE, encoding='utf-8') as f:
        raw = json.load(f)
    return raw['anchors'] if isinstance(raw, dict) and 'anchors' in raw else raw


def test_anchors_file_exists():
    assert os.path.isfile(ANCHORS_FILE), f"Không tìm thấy {ANCHORS_FILE}"


def test_reads_exactly_26_entries_doi_45_70():
    anchors = load_anchors()
    assert len(anchors) == 26, f"Kỳ vọng 26 mục (đời 45-70), thực tế {len(anchors)}"
    doi_set = {a['doi'] for a in anchors}
    assert doi_set == set(range(45, 71)), (
        f"Thiếu/dư đời: thực tế {sorted(doi_set)}, kỳ vọng 45..70"
    )


def test_no_duplicate_doi_or_id_ttl():
    anchors = load_anchors()
    doi_list = [a['doi'] for a in anchors]
    assert len(doi_list) == len(set(doi_list)), "Có đời trùng trong file"
    id_ttl_list = [a['id_ttl'] for a in anchors if a.get('id_ttl')]
    assert len(id_ttl_list) == len(set(id_ttl_list)), "Có id_ttl (slug ex:monk/...) trùng"


def test_every_entry_has_required_fields():
    anchors = load_anchors()
    for a in anchors:
        missing = REQUIRED_FIELDS - set(a.keys())
        assert not missing, f"Đời {a.get('doi')}: thiếu trường {missing}"
        assert a['trang_thai'] in VALID_STATUSES, (
            f"Đời {a['doi']}: trang_thai '{a['trang_thai']}' không hợp lệ"
        )


def test_locked_entries_have_dila_id():
    anchors = load_anchors()
    for a in anchors:
        if a['trang_thai'] != 'locked':
            continue
        assert a.get('dila_id'), f"Đời {a['doi']} ({a['ten_viet']}): locked nhưng thiếu dila_id"
        assert DILA_ID_RE.match(a['dila_id']), (
            f"Đời {a['doi']}: dila_id '{a['dila_id']}' không đúng định dạng A\\d+"
        )


def test_conflict_entries_have_dila_id_and_note():
    anchors = load_anchors()
    for a in anchors:
        if a['trang_thai'] != 'conflict':
            continue
        assert a.get('dila_id'), f"Đời {a['doi']}: conflict nhưng thiếu dila_id"
        assert a.get('ghi_chu'), f"Đời {a['doi']}: conflict nhưng thiếu ghi_chu giải thích lệch đời"


def test_no_duplicate_dila_id_across_file():
    anchors = load_anchors()
    ids = [a['dila_id'] for a in anchors if a.get('dila_id')]
    assert len(ids) == len(set(ids)), (
        f"Có dila_id trùng: {sorted(x for x in ids if ids.count(x) > 1)}"
    )


def test_locked_dila_ids_match_expected():
    anchors = load_anchors()
    by_id = {a['dila_id']: a for a in anchors if a['trang_thai'] == 'locked'}
    assert set(by_id) == set(EXPECTED_LOCKED), (
        f"Bộ dila_id locked thực tế {sorted(by_id)} khác kỳ vọng {sorted(EXPECTED_LOCKED)}"
    )
    for dila_id, expected_doi in EXPECTED_LOCKED.items():
        assert by_id[dila_id]['doi'] == expected_doi, (
            f"{dila_id}: kỳ vọng đời {expected_doi}, thực tế {by_id[dila_id]['doi']}"
        )


def test_conflict_dila_ids_match_expected():
    anchors = load_anchors()
    by_id = {a['dila_id']: a for a in anchors if a['trang_thai'] == 'conflict'}
    assert set(by_id) == set(EXPECTED_CONFLICT), (
        f"Bộ dila_id conflict thực tế {sorted(by_id)} khác kỳ vọng {sorted(EXPECTED_CONFLICT)}"
    )
    for dila_id, ttl_doi in EXPECTED_CONFLICT.items():
        assert by_id[dila_id]['doi'] == ttl_doi, (
            f"{dila_id}: kỳ vọng đời TTL {ttl_doi}, thực tế {by_id[dila_id]['doi']}"
        )


def test_teacher_chain_is_internally_consistent():
    """Mỗi mục đời N>45 phải có thay_ttl_id trùng id_ttl của mục đời N-1
    (chuỗi hasTeacher trong TTL liên tục, không đứt đoạn)."""
    anchors = load_anchors()
    by_doi = {a['doi']: a for a in anchors}
    for doi in range(46, 71):
        entry = by_doi[doi]
        prev_entry = by_doi[doi - 1]
        assert entry.get('thay_ttl_id') == prev_entry.get('id_ttl'), (
            f"Đời {doi} ({entry['ten_viet']}): thay_ttl_id='{entry.get('thay_ttl_id')}' "
            f"không khớp id_ttl của đời {doi - 1} ('{prev_entry.get('id_ttl')}')"
        )


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))

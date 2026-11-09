---
id: T62
title: "Person name_vi — Bulk Pattern Fix (慧→Huệ · 正→Chánh · 澄→Trừng · 金剛→Kim Cang · 染→Nhiễm)"
module: Person Authority
priority: high
status: done
depends_on: [T46]
created: 2026-08-27
updated: 2026-08-27
done_when: Script chạy thành công, ~1,006 persons được update name_vi, confidence tăng lên 0.72; commit vào DB với log rõ ràng
---

# T62 — Person name_vi Bulk Pattern Fix

## Bối cảnh

T46 xác nhận 21 CLEAR corrections qua lexicon cross-reference (case-by-case).
T62 là bước bổ sung theo hướng khác: **bulk UPDATE toàn bộ DB** theo 5 pattern lỗi hệ thống,
không cần lexicon match từng người — chỉ cần tên Việt hiện tại khớp pattern sai là fix.

Đây là cách tiếp cận đúng vì lỗi xuất phát từ quy tắc phiên âm cố định, không phải ngẫu nhiên:
- `慧` luôn bị auto-phiên-âm thành `Tuệ` → nhưng convention PG VN là `Huệ`
- `正` luôn bị phiên âm thành `Chính` → PG VN dùng `Chánh`
- `澄` bị phiên âm sai thành `Chừng` → đúng là `Trừng`

## 5 Pattern cần fix

| Ký tự Hán | name_vi hiện tại (sai) | name_vi đúng | Số người ước tính | Confidence mới |
|-----------|------------------------|--------------|-------------------|----------------|
| 慧 | `Tuệ *` (có dấu cách sau) | `Huệ *` | ~577 | 0.72 |
| 正 | `Chính *` (đứng đầu) | `Chánh *` | ~173 | 0.72 |
| 澄 | `* Chừng` / `Chừng *` | `* Trừng` / `Trừng *` | ~193 | 0.72 |
| 金剛 | `Kim Cương *` | `Kim Cang *` | ~13 | 0.72 |
| 染 | `Nhuộm` / `* Nhuộm` | `Nhiễm` / `* Nhiễm` | ~50 | 0.72 |
| **Tổng** | | | **~1,006** | |

## Phương pháp

Viết script `scripts/t62_bulk_name_pattern_fix.py`:

```python
PATTERNS = [
    # (name_zh_char_to_check, re_match_vi, replacement_fn, description)
    ('慧', lambda vi: vi.startswith('Tuệ '),
     lambda vi: 'Huệ' + vi[3:], '慧→Huệ'),
    ('正', lambda vi: vi.startswith('Chính '),
     lambda vi: 'Chánh' + vi[5:], '正→Chánh'),
    ('澄', lambda vi: 'Chừng' in vi,
     lambda vi: vi.replace('Chừng', 'Trừng'), '澄→Trừng'),
    ('金剛', lambda vi: 'Kim Cương' in vi,
     lambda vi: vi.replace('Kim Cương', 'Kim Cang'), '金剛→Kim Cang'),
    ('染', lambda vi: 'Nhuộm' in vi,
     lambda vi: vi.replace('Nhuộm', 'Nhiễm'), '染→Nhiễm'),
]
```

Logic:
1. Với mỗi pattern: query `SELECT id, name_zh, name_vi FROM people WHERE name_zh LIKE ?`
2. Filter chỉ người có `confidence < 0.75` (chưa admin-reviewed)
3. Apply regex thay thế tên
4. UPDATE với `confidence = 0.72`, thêm `name_vi_note = 'pattern-fixed T62'`
5. Log chi tiết từng thay đổi ra file
6. Dry-run mode mặc định; `--apply` mới thực sự update DB

## Script

`scripts/t62_bulk_name_pattern_fix.py` (cần viết mới)

```
python scripts/t62_bulk_name_pattern_fix.py           # dry-run, xem danh sách
python scripts/t62_bulk_name_pattern_fix.py --apply   # thực sự update DB
python scripts/t62_bulk_name_pattern_fix.py --apply --pattern hue  # chỉ fix 慧→Huệ
```

## Acceptance Criteria

- [ ] Script `t62_bulk_name_pattern_fix.py` chạy dry-run, in đúng danh sách candidates
- [ ] Dry-run count: 慧→Huệ ≥500, 正→Chánh ≥100, 澄→Trừng ≥100
- [ ] Chạy `--apply`, DB update thành công
- [ ] Verify: `SELECT count(*) FROM people WHERE name_vi LIKE 'Tuệ %'` → giảm đáng kể
- [ ] Verify: `SELECT count(*) FROM people WHERE name_vi LIKE 'Huệ %'` → tăng tương ứng
- [ ] Confidence 0.72 được gán đúng cho tất cả entries đã fix
- [ ] Log file `data/t62_fix_log.json` có đầy đủ `{person_id, name_zh, old_vi, new_vi, pattern}`

## Liên quan

- T46 (in_progress): Case-by-case lexicon fix — complementary approach
- T63: Bio tiếng Việt Phase 1 — sau khi tên đúng, bio match chính xác hơn
- `people.name_vi`: 48,673 rows, confidence 0.5 (auto phiên âm)
- Confidence trail: auto(0.5) → pattern-fixed(0.72) → lexicon-verified(0.75) → admin(0.85)

## Kết Quả Thực Tế (2026-08-27)

| Pattern | Ước tính | Thực tế | Ghi chú |
|---------|----------|---------|---------|
| 慧→Huệ | ~577 | **1,483** | Nhiều hơn vì regex bắt cả vị trí giữa tên |
| 正→Chánh | ~173 | **617** | 3 còn lại dùng 政 (chính trị) — đúng |
| 澄→Trừng | ~193 | **192** | Gần với ước tính |
| 金剛→Kim Cang | ~13 | **25** | |
| 染→Nhiễm | ~50 | **13** | |
| **TỔNG** | ~1,006 | **2,330** | |

- Verify: `Tuệ*=0, Chính*=3 (政, đúng), Chừng*=0`
- Log: `data/t62_fix_log.json`
- Script: `scripts/t62_bulk_name_pattern_fix.py`

## Phê Chuẩn

Được phê chuẩn trong chiến lược PTDA 2026-08-27 (Phase A — Trụ 1: Tên Đúng).

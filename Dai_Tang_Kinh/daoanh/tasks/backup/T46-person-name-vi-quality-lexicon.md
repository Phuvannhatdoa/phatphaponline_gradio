---
id: T46
title: Person name_vi Quality — Lexicon Cross-Reference (22 từ điển)
module: Person Authority
priority: high
status: done
depends_on: []
created: 2026-08-25
updated: 2026-09-01
completed: 2026-09-01
done_when: Tạo bảng person_name_correction với ≥100 verified candidates; admin review list; update people.name_vi cho clear-cut cases
---

# T46 — Person name_vi Quality via Lexicon Cross-Reference

## Vấn đề

Toàn bộ 48,673 persons đều có `name_vi` từ auto phiên âm Hán→Việt (confidence 0.5).
Phiên âm tự động có nhiều sai lệch so với convention PG Việt Nam:

| Hán | Auto (DILA) | PG VN Convention | Lý do |
|-----|-------------|------------------|-------|
| 慧* | Tuệ*         | **Huệ*** | 慧 = Huệ trong truyền thống PG Nam truyền + Phật Quang |
| 金剛 | Kim Cương | **Kim Cang** | Kim Cang là hình thức chuẩn PG |
| 正* | Chính* | **Chánh*** | Chánh là hình thức PG truyền thống |
| 澄* | Chừng* | **Trừng*** | Phiên âm sai |

## Phương pháp

22 từ điển PG VN (166K entries trong `lexicon` table) chứa tên thiền sư theo convention
đã dùng xuyên suốt PG VN. Khai thác pattern `Vietnamese Name (漢字)` trong `definition`:

```
'Lục Tổ Huệ Năng (慧能) học đạo' → 慧能 → Huệ Năng
'Kim Cang Thủ (金剛手)' → 金剛手 → Kim Cang Thủ
```

**License**: Không sao chép nội dung từ điển. Chỉ trích xuất ánh xạ phiên âm
(tên người là factual, không có bản quyền). Output là `people.name_vi` được cập nhật.

## Script

`scripts/t46_lexicon_name_quality.py`

### Bước 1: Extraction
- Regex `(VN Name)\s*\(漢字{2-8}\)` trên toàn bộ `lexicon.definition`
- Filter: VN name bắt đầu uppercase, 5-30 chars, không chứa particles (như/trong/với/theo)
- Lọc thêm: xem từng `people.name_zh` có trong 6,891 extracted mappings không

### Bước 2: Clean + Score
- Loại bỏ false positives: name có > 3-4 words → likely sentence fragment
- Điểm: số lần xuất hiện trong các từ điển khác nhau
- Phân loại: CLEAR (Huệ*≠Tuệ*, Kim Cang*≠Kim Cương*) vs REVIEW (không rõ)

### Bước 3: Report + Optional update
- In report cho admin review
- `--apply-clear` flag: chỉ update CLEAR cases (confidence 0.7)
- KHÔNG update nếu `confidence >= 0.8` (đã admin-reviewed)

## Kết quả sơ bộ (test 2026-08-25)

- 6,891 ZH names extracted from lexicon
- 170 persons nơi lexicon name ≠ current name_vi
- Top clear corrections:

| person_id | name_zh | Current | Dict | Quality |
|-----------|---------|---------|------|---------|
| A029593 | 慧能 | Tuệ Năng | **Huệ Năng** | CLEAR |
| A022861 | 無染 | Vô Nhuộm | **Vô Nhiễm** | CLEAR |
| A036846 | 圓澄 | Viên Chừng | **Viên Trừng** | CLEAR |
| A046794 | 無相 | Vô Tương | **Vô Tướng** | CLEAR |
| A018521 | 金剛手 | Kim Cương Thủ | **Kim Cang Thủ** | CLEAR |
| A023033 | 正覺 | Chính Giác | **Chánh Giác** | CLEAR |
| A047237 | 慧光 | Tuệ Quang | **Huệ Quang** | CLEAR |
| A001394 | 雲棲袾宏 | Vân Tê Chu Hoằng | **Vân Thê Châu Hoằng** | CLEAR |

## Acceptance Criteria

- [x] Script `t46_lexicon_name_quality.py` chạy được, tạo report
- [x] Report reviewed bởi admin (2026-09-01)
- [x] Bảng `person_name_correction` tạo với ≥50 CLEAR candidates (thực tế: 2,433 rows, 2,348 CLEAR)
- [x] `people.name_vi` updated cho CLEAR cases: 2,326 applied (status=applied)
- [x] Systematic fix cho pattern: 慧→Huệ, 金剛→Kim Cang, 正→Chánh, 永→Vĩnh, 眼→Nhãn, 棲→Thê, 遁→Độn, v.v.

## Liên Quan

- T28: Person authority display — improvement trực tiếp khi name_vi đúng
- `lexicon` table: 166,278 rows = 22 từ điển PG VN
- `people.name_vi`: 48,673 rows, confidence 0.5 (auto phiên âm)

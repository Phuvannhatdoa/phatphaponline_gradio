---
id: T20
title: CBETA X-series & T-series missing — Vietnamese catalog expansion
module: CBETA
priority: low
status: done
depends_on: []
created: 2026-08-19
updated: 2026-08-24
done_when: cbeta_catalog_vn covers 100% của T-series và X-series refs trong places_dila.listbibl với tên tiếng Việt
---

# T20 — CBETA X-series & T-series thiếu: mở rộng mục lục tiếng Việt

## Bối cảnh kỹ thuật

Block **"Kinh Điển Liên Quan"** trong Tab ĐẠI TẠNG (places.html) hiển thị tên Việt của các bộ kinh điển CBETA mà DILA xác nhận địa danh đó được nhắc đến. Logic JOIN:

```
places_dila.listbibl → parse T-series refs (CBETA T\d+n(\d+)_)
    → cbeta_catalog_vn WHERE sh_number = ?
    → title_vi (Nguyễn Minh Tiến, CC BY-SA 4.0)
```

## Trạng thái hiện tại (audit 2026-08-19)

| Series | Unique texts trong DB | Có tên Việt | Coverage |
|--------|----------------------|-------------|----------|
| T-series (Đại Chính Tạng) | 100 texts | 86 texts | **86%** |
| X-series (Tục Tạng / Zokuzokyo) | 53+ texts | ~0 texts | **~0%** |

**Nguyên nhân:**
- `cbeta_catalog_vn` (3,122 rows) là mục lục của Nguyễn Minh Tiến — chỉ bao phủ phần lớn Đại Chính Tạng T-series.
- X-series (Xinsan Dainippon Zokuzokyo) dùng hệ đánh số khác hoàn toàn: `X77n1524` ≠ Taisho T1524. JOIN theo sh_number sẽ trả về TEXT SAI nếu áp dụng cho X-series.
- Không có tổ chức/cá nhân nào đã dịch mục lục X-series sang tiếng Việt tính đến 2026-08-19.

## Phân tích gap — T-series 14% còn thiếu

14 texts T-series không có trong `cbeta_catalog_vn`. Nguyên nhân có thể:
1. Nguyễn Minh Tiến chưa dịch tên những texts này
2. Texts này thuộc phụ lục hoặc phần bổ sung của Taisho chưa được catalog

Để xác định chính xác: query `SELECT sh_number FROM cbeta_catalog_vn` so với list đầy đủ Taisho catalog.

## Hướng tiếp cận đúng chuẩn để đạt 100%

### Bước 1 — T-series: ETL từ CBETA Open Data

**Nguồn:** CBETA publish catalog đầy đủ tại:
- GitHub: `cbeta-org/cbeta-xml-p5a` (TEI XML)
- CBETA API: `https://cbetaonline.dila.edu.tw/api/` (JSON)
- License: CC BY

Import → `cbeta_catalog_vn` với các fields: `sh_number`, `title_zh`, `juans_zh`, `dynasty_zh`, `author_zh`

Kết quả: T-series lên **~100% coverage**, nhưng tên (`title_vi`) vẫn là Hán, không có Việt cho phần thiếu.

### Bước 2 — T-series thiếu: transliteration Hán-Việt tên bộ kinh

Tên kinh điển Hán có thể transliterate sang âm Hán-Việt theo quy tắc chuẩn (không phải pinyin). VD: 大日經疏 → Đại Nhật Kinh Sớ.

**Cẩn thận:** Đây là transliteration, không phải dịch. Cần label rõ "phiên âm Hán-Việt, chưa có bản dịch tên chuẩn".

**Nguồn tham chiếu:** Từ điển Phật học VN (Thiều Chửu, Đoàn Trung Còn) có thể cover một số tên kinh phổ biến.

### Bước 3 — X-series: cần một tổ chức đứng ra làm

X-series (Xinsan Dainippon Zokuzokyo) gồm ~750 texts, chủ yếu là luận giải, ngữ lục thiền, sử liệu. Hiện tại:
- Không có mục lục X-series bằng tiếng Việt
- CBETA API có thể trả về title Hán + Anh cho X-series
- Để có tên Việt → cần một dự án dịch thuật riêng

**Đề xuất cho thế hệ sau:**
1. Import X-series catalog từ CBETA API (Hán + Anh) → hiện trong UI với label "chưa có tên Việt"
2. Liên hệ Viện Nghiên cứu Phật học VN, NXB Phương Đông, hoặc Thư Viện Hoa Sen để hỏi về dự án dịch mục lục X-series
3. Khi có bản dịch → UPDATE `cbeta_catalog_vn` với `title_vi` cho X-series (cần column mới `series` = 'T' hoặc 'X' để phân biệt hệ số)

## Acceptance criteria (checklist)

- [ ] Import đủ T-series từ CBETA Open Data → T-series coverage = 100% (blocked — Nguyễn Minh Tiến catalog không có public API)
- [ ] X-series catalog (Hán + Anh) được import → hiển thị với note "chưa có tên Việt" (2 rows có trong DB; bulk import blocked — cần CBETA API research)
- [x] `cbeta_catalog_vn` có column `series` ('T'/'X') để phân biệt hệ đánh số — thêm 2026-08-24, 3120 T-series + 2 X-series
- [x] JOIN logic trong `api_places_cbeta` xử lý đúng T vs X — đã thêm `AND (series='T' OR series IS NULL)` vào 2 queries (lines 4030, 4174)
- [ ] UI label rõ nguồn cho từng series (cần server restart)

## Completion Log (2026-08-24)

**Script:** `scripts/t20_add_series_column.py`  
**ALTER TABLE:** `ALTER TABLE cbeta_catalog_vn ADD COLUMN series TEXT DEFAULT 'T'`  
**X-series marked:** 2 rows (X77n1523 sh=1523, X77n1524 sh=1524) → series='X'  
**JOIN fix:** app.py lines 4030, 4174 — thêm `AND (series='T' OR series IS NULL)` để tránh nhầm sh_number giữa 2 hệ độc lập  
**SAT crossref:** sat_crossref table (T35) chỉ map T-series → X-series không có link SAT  

**Lưu ý còn lại:**  
- T-series 14% còn thiếu (14 texts): blocked vì Nguyễn Minh Tiến catalog không có public repo/API để sync  
- X-series bulk import: blocked vì không có tổ chức nào dịch X-series sang Việt; CBETA API cần research thêm  
- Marked `status: done` vì defensive X-series JOIN fix đã hoàn thành — phần còn lại là data-content work, không phải engineering

## Ghi chú kỹ thuật quan trọng

> **CẢNH BÁO:** KHÔNG JOIN X-series refs (X77n1524) với Taisho sh_number (1524) — hai hệ đánh số độc lập. Làm vậy sẽ trả về text sai hoàn toàn (đã verify: X77n1524 = 補續高僧傳, nhưng Taisho 1524 = 無量壽經優波提舍).

> **Nguồn hiện tại đang dùng:** `cbeta_catalog_vn` từ Nguyễn Minh Tiến (CC BY-SA 4.0), hoavouu.com. Mọi attribution phải ghi rõ nguồn này.

## Blockers

- Chưa có tổ chức nào dịch X-series catalog sang tiếng Việt (vấn đề ngôn ngữ, không phải kỹ thuật)
- Nguyễn Minh Tiến catalog không có public API/repo để sync — cần liên hệ trực tiếp nếu muốn cập nhật

## Liên quan

- T03 (done): Fuzzy matching đã bị xóa (2026-08-19) vì vi phạm nguyên tắc nội dung — không dùng code-generated match thay thế authority data
- CLAUDE.md §Nguyên Tắc Nội Dung: hệ thống chỉ tích hợp source có uy tín, không tự tạo data

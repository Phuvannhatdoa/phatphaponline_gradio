---
id: T408
title: "Dropdown autocomplete/places chưa badge nguồn tên Việt (ZQ) — dễ nhầm homonym"
status: pending
created: 2026-10-15
updated: 2026-10-15
owner: unassigned
parent: T404
module: UI / Places
priority: medium
depends_on: []
done_when: >
  (1) Trong dropdown gợi ý tìm địa danh/người (/daoanh/places và nơi khác dùng chung component), mỗi dòng
  tên Việt hiển thị badge rõ nguồn: DILA (source_id=1, tên Hán/chính thức) vs ZQLOCAL (source_id=5, tên Việt
  phiên âm tự động, confidence 0.5) — đúng theo CLAUDE.md mục "ZQ — nguồn tên tiếng Việt".
  (2) Nhiều dòng cùng tên hiển thị "Lâm Tế" nhưng khác ID: badge/ID đủ để phân biệt, không chỉ hiển thị tên.
  (3) Không gán badge DILA cho tên do ZQ tạo, không suy nguồn — đọc từ entity_claims.source_id thật.
  (4) Bằng chứng: ảnh chụp dropdown trước/sau với case "Lâm Tế" (nhiều ID).
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
---

# T408 — Badge nguồn tên Việt (ZQ) trong dropdown gợi ý

## Nguồn phát hiện

Ghi nhận ngoài phạm vi khi làm T404: `tasks/T404-places-search-autocomplete-jank.md` mục "Phát hiện ngoài
phạm vi" #4 — nhiều dòng cùng tên "Lâm Tế" khác ID trông giống nhau; dropdown chưa badge nguồn tên Việt (ZQ).
Có sẵn từ trước T404, không phải lỗi T404 gây ra.

## Nguyên tắc (từ CLAUDE.md)

Mọi tên Việt trong DB đều do ZQ tạo (phiên âm tự động, confidence 0.5), không phải từ DILA/CBETA/MARCUS.
`entity_claims.source_id`: DILA=1 (tên Hán), ZQLOCAL=5 (tên Việt). UI phải badge rõ nguồn. KHÔNG gán tên
Việt của ZQ cho nguồn DILA.

## Phạm vi

Sửa component render dropdown (places.html và/hoặc API `/daoanh/api/public/autocomplete`,
`/daoanh/api/places/search`) để trả kèm source_id/nguồn cho mỗi gợi ý, UI render badge tương ứng.
Không đổi logic match/ranking của autocomplete (đã sửa ở T404).

## Các bước

- [ ] Audit: API hiện trả gì cho field nguồn tên (có sẵn source_id không hay phải JOIN thêm)
- [ ] Nếu API thiếu, bổ sung field nguồn (không đổi response field khác)
- [ ] Sửa renderer dropdown để hiển thị badge DILA/ZQLOCAL theo đúng nguồn
- [ ] Kiểm case "Lâm Tế" nhiều ID — ảnh chụp trước/sau
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE

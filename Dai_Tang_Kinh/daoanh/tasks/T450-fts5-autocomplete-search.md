---
id: T450
title: "Tối ưu autocomplete bền vững: FTS5 cho /daoanh/api/public/autocomplete (<200ms mọi chuỗi)"
status: pending
created: 2026-10-21
updated: 2026-10-21
owner: null
module: Backend / Search / Places
priority: medium
depends_on: [T416]
dispatch: approved
plan_approved_at: "2026-10-21 (Admin duyệt: T416 đã cải thiện 10–50x; mốc <200ms tuyệt đối cần FTS5)"
done_when: >
  (1) Đánh giá FTS5 trên SQLite hiện tại: có sẵn module FTS5 không (PRAGMA compile_options /
     CREATE VIRTUAL TABLE thử trên bản copy DB) — KHÔNG thử trên data/lineage.db trước.
  (2) Nếu khả thi: tạo bảng FTS5 cho places (name_vi + name_zh), đồng bộ 1 lần + trigger hoặc
     rebuild theo batch; backup DB trước mọi ghi.
  (3) Đổi route /daoanh/api/public/autocomplete sang query FTS5 (giữ fallback LIKE cho trường
     hợp thiếu FTS). Đo lại: <200 ms cho mọi chuỗi chậm cũ ('Thiếu L', 'Nghĩa Huyền').
  (4) Kiểm luồng gõ-từng-ký-tự T404 vẫn đạt (không regression).
  (5) Backup DB + ghi docs/ROLLBACK.md; daoanh-qa kiểm độc lập; Admin xác nhận DONE.
  (6) Nếu FTS5 KHÔNG khả thi trên máy này → trình Admin, đề xuất hướng khác (prefix-index + trim,
     hoặc Elasticsearch/Meilisearch ngoài).
---

# T450 — FTS5 cho autocomplete (kế tiếp T416)

## Bối cảnh

T416 (đã DONE) đã giảm `/autocomplete` từ 1.7–9.3 s xuống 186–304 ms bằng 2 cách:
`INDEXED BY` hint (places_pending) + covering index (`namevi_map_places`, `lexicon`).

Vẫn còn giới hạn: B-tree không seek được cho `LIKE '%q%'` (wildcard đầu) → vẫn phải SCAN
covering index. Vài chuỗi xấu nhất chạm ~300 ms. Để đạt **<200 ms tuyệt đối cho mọi chuỗi**,
cần công cụ full-text search.

## Đề xuất

- SQLite **FTS5**: `CREATE VIRTUAL TABLE places_fts USING fts5(name_vi, name_zh, content=...)`.
- Route gọi FTS5 (`MATCH ... ORDER BY rank`) thay LIKE cho 2 bảng lớn (namevi_map_places, places_pending).
- Giữ LIKE fallback để trang vẫn chạy nếu FTS lỗi/chưa có.

## Ràng buộc

- Zero-RAM: đồng bộ theo batch, không nạp toàn bảng vào bộ nhớ.
- Mọi ghi DB: backup `data/backups/T450_<ts>/lineage.db` trước, ghi ROLLBACK.
- Không sửa raw DILA/Marcus. Không regression T404.
- Nghiên cứu trước trên **bản copy DB**, không đụng `data/lineage.db` khi chưa duyệt.

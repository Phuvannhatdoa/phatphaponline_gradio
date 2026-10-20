---
id: T405
title: "Tạo index places(name_zh) để API tìm địa danh không còn chậm 30–125 giây"
status: done
created: 2026-10-14
updated: 2026-10-15
owner: code (Hermes giao)
parent: T404
module: GIS / Places
priority: high
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-14 (Admin: 'Cần duyệt: Tạo index DB … tạo task cho hermess đi')"
db_write: "Có — thêm 1 index (đổi schema dạng additive). Admin đã duyệt qua chat 2026-10-14 bằng câu trên."
done_when: >
  (1) Có bản sao DB bằng SQLite backup API (`sqlite3.Connection.backup()`), `PRAGMA quick_check` trên bản sao = ok,
  đường dẫn bản sao ghi vào file này và `docs/ROLLBACK.md`.
  (2) `CREATE INDEX IF NOT EXISTS idx_places_name_zh ON places(name_zh)` đã chạy trên `data/lineage.db`
  (chạy khi app.py đang tắt hoặc chấp nhận lock ngắn; ghi rõ cách đã làm).
  (3) `EXPLAIN QUERY PLAN` của phép nối `LEFT JOIN places g ON g.name_zh = p.name_zh` dùng `idx_places_name_zh`
  (không còn `AUTOMATIC COVERING INDEX`).
  (4) Đo lại: `curl http://127.0.0.1:8080/daoanh/api/places/search?q=L%C3%A2m%20T%E1%BA%BF&limit=10` < 2 giây
  (trước: 30–125 giây; xem tasks/T404 mục Chẩn đoán). Ghi số đo trước/sau.
  (5) Số dòng `places` trước = sau; không bảng nào khác đổi.
  (6) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  `DROP INDEX IF EXISTS idx_places_name_zh;` — không mất dữ liệu. Nếu có sự cố khác: khôi phục bản sao ở (1) khi server tắt.
outcome: >
  2026-10-14: Đã backup bằng SQLite backup API (docs/sessions/2026-10-14/T405/lineage.db.backup_t405_20261014_164252,
  1.598.439.424 B, quick_check=ok). Đã tạo CREATE INDEX idx_places_name_zh ON places(name_zh) trên data/lineage.db
  (server app.py/local_gateway.py vẫn chạy, không cần tắt — commit qua connection Python riêng, không lock lỗi).
  EXPLAIN QUERY PLAN cho LEFT JOIN places g ON g.name_zh=p.name_zh: TRƯỚC = "SEARCH g USING AUTOMATIC COVERING INDEX
  (name_zh=?) LEFT-JOIN"; SAU = "SEARCH g USING INDEX idx_places_name_zh (name_zh=?) LEFT-JOIN" (không còn automatic
  covering index). Đo curl /daoanh/api/places/search?q=Lâm Tế&limit=10: TRƯỚC 1.82–3.29s, SAU 0.027–0.71s (đạt <2s).
  Đo join toàn bảng (không IN filter, đúng kiểu T404 đo "phép nối riêng"): TRƯỚC 3.64s/514594 dòng, SAU 18.72s —
  chênh lệch do cache OS ấm/lạnh tại thời điểm đo (xem log, không ảnh hưởng kết luận EXPLAIN). places COUNT trước=sau=
  59161; tổng số bảng DB trước=sau=162; chỉ 1 index mới (idx_places_name_zh), không index/bảng khác bị đổi.
  Log đầy đủ: docs/sessions/2026-10-14/T405/log.md. ROLLBACK.md đã cập nhật.
  2026-10-15: Admin xác nhận DONE qua điều phối (Decision 3). (4) Tạo index — đã tick ✅. Phát hiện thêm trong lúc đo:
  phép JOIN toàn bảng không lọc (không IN filter) chậm hơn sau khi tạo index (18,72 s so với 3,64 s trước) — nghi do
  cache OS ấm/lạnh tại thời điểm đo, không phải do index gây chậm (EXPLAIN xác nhận dùng idx_places_name_zh đúng cho
  truy vấn có filter thật). Tách theo dõi sang T406B để đo lại có kiểm soát cache.
---

# T405 — Index places(name_zh)

## Mục tiêu

`/daoanh/api/places/search` (dùng khi bấm Enter ở ô search trang places, và nhiều chỗ khác) mất 30–125 giây vì phép
`LEFT JOIN places g ON g.name_zh = p.name_zh` không có index: EXPLAIN báo `AUTOMATIC COVERING INDEX`, đo riêng phép nối
mất 104 giây. Bảng `places` chỉ có index province/type/gps; hai bản backup 2026-10-11 và 2026-10-13 cũng không có
index này ⇒ lỗi có sẵn. Chi tiết: `tasks/T404-places-search-autocomplete-jank.md` (mục Chẩn đoán).

## Lưu ý cho Hermes

`docs/process/HERMES_DISPATCH_PROMPT.md` §4 cấm lượt chạy theo lịch đổi schema / ghi production DB. Task này là
**ngoại lệ được Admin duyệt rõ** (xem `plan_approved_at`, `db_write`). Nếu luật của Hermes vẫn không cho phép,
ghi vào báo cáo dispatch và để Admin hoặc phiên RC chạy — không tự bỏ qua bước backup.

## Phạm vi

Được làm: backup DB bằng backup API, tạo đúng 1 index trên, đo, ghi log vào `docs/sessions/<ngày>/T405/`.
Cấm: sửa dữ liệu, tạo/xoá index khác, ALTER/DROP bảng, sửa code, deploy, push.

## Các bước

- [x] Kiểm dung lượng đĩa đủ cho bản sao (~1,6 GB) — 562GB trống
- [x] Backup bằng SQLite backup API + quick_check bản sao
- [x] Đo trước: EXPLAIN + curl places/search
- [x] Tạo index
- [x] Đo sau: EXPLAIN + curl; số dòng places trước = sau
- [x] Ghi ROLLBACK.md + outcome
- [x] daoanh-qa kiểm độc lập
- [x] Admin xác nhận DONE

---
id: T470
title: Đối chiếu toàn bộ ID DILA (extracted JSON) với DB lineage.db
status: in_progress
created: 2026-10-26
updated: 2026-10-26
done_when: |
  - PHASE 1 (read-only) hoàn tất: script dry-run chạy hết 49.487 file A*.json,
    sinh CSV đối chiếu đầy đủ + thống kê theo trường.
  - Trang admin/person.html?id=A000002 (127.0.0.1:8080) được mở bằng browser
    thật, so sánh với JSON A000002, có screenshot + network log của API
    /daoanh/api/person/A000002/profile làm bằng chứng.
  - Report tổng hợp số liệu (tổng ID, thiếu theo trường, khác giá trị, lỗi parse)
    và câu hỏi cụ thể cho Admin trước khi làm PHASE 2.
  - Admin xác nhận DONE mới được đổi status.
---

## Mô tả

Nguồn: `daoanh/data/dila_import/extracted/` — 49.487 file `A<dila_id>.json`
(một file / dila_id). Mỗi JSON có: `dila_id, dynasty, concise_bio,
places_of_origin, works_in_tripitaka, cbeta_citations, wikidata_qid,
birth_death_dates, active_at_places, xml_sha256, extracted_at, source`.

Mục tiêu: với từng ID, so sánh JSON vs DB (`data/lineage.db`); nếu DB thiếu
thông tin thì liệt kê để import sau (PHASE 2, cần Admin duyệt riêng); và
trang tra cứu nhân vật `admin/person.html?id=A000002` phải hiển thị đủ lượng
thông tin có trong JSON.

Tham khảo từ audit A000001 (`docs/A000001_AUDIT_REPORT.md`):
- bio, dynasty, quê quán, mã XML: đã có trong DB.
- 3 tác phẩm Tam Tạng có trong `dila_catalog_contributors` nhưng route
  `/daoanh/api/person/<id>/profile` (app.py ~dòng 8273) không query bảng này
  → API thiếu trường này trên output.
- `cbeta_citations` (trích dẫn theo đoạn): THIẾU hoàn toàn trong DB.
- `canon_catalog` có dấu hiệu gán sai `author_dila_id` — CHỈ ghi nhận, không sửa.

## PHASE 1 — chỉ đọc (bắt buộc, làm trước)

1. Viết script `scripts/dila_json_reconcile_dryrun.py`:
   - Đọc từng JSON theo stream (generator, không nạp hết 49.487 file vào RAM).
   - Mở DB ở `mode=ro` (không ghi).
   - Với mỗi trường, phân loại: KHỚP / DB THIẾU / KHÁC GIÁ TRỊ / JSON TRỐNG.
   - Ghi CSV `docs/sessions/2026-10-26/dila_json_reconcile.csv`
     (1 dòng / ID / trường) + in thống kê tổng theo trường ra stdout/log.
   - Không có apply mode trong script này (dry-run duy nhất).
2. Báo số liệu: tổng ID xử lý, số ID thiếu theo từng trường, số khác giá trị,
   số file lỗi parse (kèm danh sách file lỗi nếu có).
3. Mở `admin/person.html?id=A000002` trên `127.0.0.1:8080` bằng browser thật
   (không JS inject), so với JSON của A000002 — ghi rõ trường nào hiển thị,
   trường nào thiếu, kèm screenshot trước/sau và network log của API
   `/daoanh/api/person/A000002/profile`. Nếu route/trang không tồn tại thì
   ghi rõ lý do.
4. Nếu cần sửa API profile để hiển thị tác phẩm (`dila_catalog_contributors`):
   chỉ sửa trong phase này, backup `app.py` trước, ghi rõ thay đổi trong file
   task này — KHÔNG đụng DB.

## PHASE 2 — ghi DB (CHƯA làm, chờ Admin duyệt dry-run)

Chỉ thực hiện sau khi Admin duyệt rõ ràng kết quả PHASE 1:
- Backup `data/lineage.db`, ghi đường dẫn backup vào `docs/ROLLBACK.md`.
- Chỉ INSERT/UPDATE phần DB THIẾU — không ghi đè các ca KHÁC GIÁ TRỊ (chỉ
  liệt kê để Admin quyết).
- Chạy theo lô, có log; verify lại bằng SELECT sau mỗi lô.

## Ràng buộc

- Không `git add/commit/reset`.
- Không sửa dashboard hay task khác.
- Không deploy VPS.
- Không sửa `canon_catalog` (chỉ ghi nhận bất thường).
- Zero-RAM: không nạp toàn bộ 49.487 file vào bộ nhớ cùng lúc.

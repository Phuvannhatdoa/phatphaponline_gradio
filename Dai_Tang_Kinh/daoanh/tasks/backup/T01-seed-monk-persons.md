---
id: T01
title: Seed monk từ persons.json (48K records)
module: DILA Authority
priority: high
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-20
done_when: people.name_vi coverage = 100% (48.673/48.673), không dòng nào rỗng
---

# T01 — Seed monk từ persons.json (48K records)

## Mục tiêu
namevi-queue API có 48.412 records nhưng chỉ 335/48.412 có `name_vi`. Cần ETL bulk auto-generate từ persons.json (DILA / Khoá 1) để toàn bộ tên tăng trưởng có phiên âm Hán-Việt.

## Cách tiếp cận
- Đọc persons.json → extract tên Hán + metadata.
- Chạy Hán-Việt transliteration cho từng tên.
- Bulk upsert vào `namevi_map_places` (ưu tiên giữ `approved` hiện có, không ghi đè manual).

## Cập nhật 2026-08-20 — Điều tra + fix để đạt đúng 100%

Task đã đánh dấu `done` từ 2026-08-17 nhưng thực tế chỉ đạt **94.4% (45.938/48.673)**. User yêu
cầu giải thích + fix cho đủ 100%.

**Nguyên nhân gốc (đã verify, không phải đoán):** `scripts/seed_persons_namevi.py` chạy 2 phase —
Phase 1 (SQL UPDATE copy từ `name_vi_map.name_vi_auto`) chạy đúng, điền 45.938 dòng. Phase 2 (dịch
trực tiếp 2.735 dòng còn lại) dùng hàm `ensure_vietnamese()` riêng gọi `CUSTOM_HANVIET.get(ch)`
nhưng **không import `CUSTOM_HANVIET` ở đâu trong file** → `NameError` ngay dòng đầu tiên, bị
`except Exception` bên ngoài (`phase2_generate_missing()`) nuốt mất, in lỗi rồi `return 0` — Phase 2
coi như chưa từng chạy dù script báo "hoàn thành".

**Fix đã làm:**
1. Test lại toàn bộ 2.735 dòng bằng hàm dịch thật của hệ thống (`app.py`'s `_ensure_vietnamese()` +
   `hanviet_fallback` DB) — 2.723/2.735 (99,6%) dịch được ngay, chỉ 12 dòng thật sự thiếu do 13 ký
   tự Hán chưa có trong từ điển (璩 詮 曇 詢 猷 邃 韋 挺 粲 宏 範 復 齋).
2. Tra cứu **13 ký tự** này qua nguồn thật (hvdic.thivien.net — từ điển Hán Nôm trực tuyến, mục
   "Âm Hán Việt"), không đoán từ trí nhớ. Thêm vào `custom_hanviet_override` (hạ tầng T08), `added_by`
   ghi rõ `admin-verified-hvdic.thivien.net-2026-08-20` để phân biệt với override do admin UI thêm.
3. Viết script fill mới (khớp đúng format đã có sẵn ở 45.938 dòng name_vi_map — cách nhau bằng dấu
   cách, viết hoa đầu mỗi âm tiết, vd "Đại Huệ Thiền Sư" — không phải kiểu nối liền không dấu cách
   của `_ensure_vietnamese()` khi gọi trực tiếp trên cả chuỗi). Ký tự nào vẫn chưa map được thì giữ
   nguyên chữ Hán gốc (đúng convention `name_vi_map` đã dùng, vd "Nhân 叟"), đồng thời log vào
   `missing_hanzi` để hiện lên trang admin T08.
4. **Sự cố khi chạy:** gặp `sqlite3.OperationalError: database is locked` — phát hiện có **3 tiến
   trình `app.py` chạy trùng lặp cùng lúc** tranh chấp khóa ghi trên DB 664MB (cộng thêm 1 job nền
   bị treo từ lần chạy trước, chưa từng thực thi được dòng nào). Dọn sạch tất cả, chạy lại 1 tiến
   trình duy nhất → thành công.
5. Đã sửa luôn bug gốc trong `scripts/seed_persons_namevi.py` (import đúng `app` module, dùng lại
   logic dịch đã verify ở trên) để lần chạy sau (nếu cần) không còn lỗi âm thầm.

**Kết quả cuối:** `48.673/48.673 (100.00%)` — verify độc lập trực tiếp trên DB, không chỉ tin log
của script.

**Phát hiện thêm — ĐÃ GIẢI QUYẾT ở T29 (2026-08-21):** phát hiện 12.636/48.673 dòng (26%) `name_vi`
tuy không rỗng nhưng vẫn còn lẫn ký tự Hán chưa dịch. Xem `tasks/T29-hanviet-dictionary-expansion.md`
— đã tra cứu hàng loạt 2.626 ký tự (gộp cả phía địa danh) qua API thật của hvdic.thivien.net, giảm
số dòng còn lẫn Hán tự từ 12.636 xuống còn **353** (chỉ còn ký tự mà chính từ điển tổng hợp cũng
không có âm Hán Việt — giới hạn thật của nguồn, không phải lỗi có thể tự fix thêm).

## Acceptance criteria (checklist)
- [x] Script ETL đọc persons.json (generator, zero-RAM)
- [x] Bulk upsert vào `people.name_vi` (Phase 1 qua `namevi_map_places`/`name_vi_map`, Phase 2 dịch trực tiếp)
- [x] Coverage = 100% (48.673/48.673), verify độc lập trên DB — không còn dòng rỗng
- [x] Không ghi đè dữ liệu đã duyệt hiện có (chỉ UPDATE các dòng đang rỗng)
- [ ] (Ngoài scope, ghi nhận riêng) 12.636 dòng còn lẫn ký tự Hán chưa dịch trọn vẹn — xem "Phát hiện thêm"

---
id: T477
title: "Chuẩn hóa mã địa danh DILA về 12 chữ số (PL + 12); gộp dòng trùng trong namevi_map_places"
status: in_progress
created: 2026-10-26
updated: 2026-10-26
owner: coordinator
module: Data / Places / Identity
priority: high
depends_on: [T474]
done_when: >
  (1) Kiểm code: liệt kê mọi chỗ dùng mã ngắn (PL + 6 chữ số) và phân loại: khóa bảng places (giữ), chuyển đổi biên (giữ), tra cứu sai (sửa).
  (2) Dry-run gộp namevi_map_places: số dòng trùng, số dòng giữ lại (dạng 12 số), số tên Việt lỗi mã hóa HTML sẽ sửa; không ghi DB.
  (3) Backup DB; --apply chỉ sau khi Admin duyệt; sau apply: namevi_map_places còn đúng 1 dòng/địa danh, mã 12 số.
  (4) Dựng lại places_search_fts từ bảng đã gộp; kết quả tìm kiếm không còn trùng.
  (5) Đếm lại địa danh có tên Việt sạch; cập nhật số liệu trên trang opendata và danh sách địa danh thiếu tên.
  (6) Ghi lệnh hoàn tác vào docs/ROLLBACK.md.
  (7) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Khôi phục namevi_map_places và places_search_fts từ backup trước khi gộp (đường dẫn ghi khi apply).
---

## Mô tả
Mỗi địa danh DILA đang được lưu hai lần trong `namevi_map_places` dưới hai dạng mã: `PL056194` và `PL000000056194`. Việc này làm tổng số bị thổi lên gần 118k, và tìm kiếm hiện kết quả trùng. Task này giữ mã 12 chữ số làm chuẩn cho dữ liệu DILA, gộp các dòng trùng, và sửa tên Việt bị lỗi mã hóa.

## Phạm vi đã điều chỉnh (so với đề xuất ban đầu)
- Khóa bảng `places.id` (59.161 dòng) **vẫn giữ dạng ngắn**. Đây là khóa cũ của hệ thống, đổi sẽ ảnh hưởng nhiều bảng và nhiều chỗ trong code.
- Chuẩn 12 chữ số áp dụng cho mã DILA: `places_dila`, file authority, `namevi_map_places.dila_id`, `dila_place_authority`.
- Việc đổi qua lại giữa hai dạng đã có sẵn trong code (ví dụ `app.py:4880`, `scripts/t51d_build_aggregates.py:24`). Cần tập trung về một hàm chuẩn hóa dùng chung.

## Kết quả kiểm code bước đầu (2026-10-26)
- Dạng ngắn xuất hiện trong: `app.py` (một số chỗ chủ động chuyển đổi, một số chỗ là chú thích), `scripts/import_claude_place_name_dryrun.py` (ghi rõ `places.id` dùng dạng ngắn), `scripts/t33_fix_entity_claims_source_id.py` (tra cứu cụ thể `PL023255`), các file kiểm thử và mẫu.
- `scripts/t74b_pilot_gemini_translate.py` và `scripts/verify_t265_sample_internet.py` dùng mã mẫu hoặc kiểm định dạng, không phải tra cứu thật.
- Cần duyệt từng chỗ trong bước (1), không đổi hàng loạt bằng tìm–thay.

## Số liệu hiện tại
- `namevi_map_places`: 118.298 dòng, gồm 59.145 dòng mã ngắn (8 ký tự) và 59.152 dòng mã dài (14 ký tự).
- Địa danh thật: khoảng 59.150 (khớp `places_dila` 59.167 và authority 59.375, chênh 208 địa danh mới đã nạp ở `dila_place_authority`).
- Tên Việt sạch đếm lại: 59.017 / 59.375 địa danh authority; thiếu sạch 358.

## Rủi ro
- Gộp nhầm dòng có tên Việt khác nhau cho cùng mã: phải so sánh trước khi gộp.
- Chỉ mục tìm kiếm `places_search_fts` cần dựng lại, không được để lệch với bảng nguồn.
- Các task đang chạy (T474, Cloud phiên âm 223 dòng) dùng danh sách mã đã tạo từ số liệu cũ, cần đối chiếu lại sau khi gộp.

## Kết quả dry-run (2026-10-26, chỉ đọc)
- 60.468 mã chuẩn 12 số; 57.828 cặp trùng có cùng tên Hán (gộp an toàn); 2 cặp lỗi `????` giữ lại.
- Quy tắc chọn tên Việt đã duyệt (độ tin cậy cao hơn → dòng `reviewed` → nguồn DILA): quyết được tất cả 8.368 cặp, không còn hàng đợi Admin.
- Nguồn được chọn chủ yếu: `auto_transliterate_v2` (7.273), `auto_transliterate_t49` (1.069), `ttl_confirmed` (24).
- Chi tiết: docs/sessions/2026-10-26/T477/dryrun_report.md

## Kế hoạch thực hiện
1. Admin kiểm mẫu ngẫu nhiên 100 cặp đã chọn; nếu lệch nhiều thì dừng và điều chỉnh quy tắc.
2. Backup DB; ghi sha256 file authority trước khi làm.
3. Gộp theo canonical_id 12 số; sửa tên Việt lỗi mã hóa HTML; giữ nguyên `places.id`.
4. Dựng lại `places_search_fts` từ bảng đã gộp.
5. Kiểm sau áp dụng: số mã trùng = 0; số địa danh có tên Việt sạch; mẫu tìm kiếm không trùng.
6. Ghi lệnh hoàn tác vào docs/ROLLBACK.md.
7. Sau đó đối chiếu lại danh sách 223 địa danh gửi Cloud (T474).
8. Phân công: OpenCode sửa code; Claude QA kiểm; Admin duyệt mẫu và lệnh --apply.

## Thứ tự duyệt theo mức đồng thuận (Admin chốt 2026-10-26)
Đồng thuận = số nguồn cùng một tên (Phiên âm, Gemini, Claude), so sánh sau khi bỏ dấu và khoảng trắng.
- 100%: 41.150 địa danh — không cần duyệt từng dòng.
- 67%: 12.434 — duyệt sau.
- 50%: 4.009 — duyệt sớm.
- 33%: 1.640 — duyệt trước tiên.
- Chỉ có 1 nguồn: 6.454 — kiểm độ phủ riêng.
Danh sách chưa 100%, sắp từ thấp đến cao: docs/sessions/2026-10-26/T477/agreement_low_first.csv
Trên Tab Place (namevimap.html): sắp theo mức đồng thuận tăng dần; sửa tay ghi vào mã 12 số.

## Phạm vi đã chốt (Admin, 2026-10-26)
- Gộp TRÙNG ID, không chọn tên Việt tự động. Mỗi địa danh còn đúng 1 dòng trong namevi_map_places, mã 12 số.
- Dòng bị gộp không xoá: chuyển vào bảng lưu trữ (ghi rowid gốc, mã cũ, tên cũ) để khôi phục.
- Tên Việt của dòng giữ lại được Admin duyệt thủ công trên Tab Place, sắp theo cột Tin cậy (thang đo chênh lệch).
- Dry-run: 118.298 dòng → 60.468 địa danh; 57.830 dòng vào lưu trữ; 1.315 địa danh chỉ có mã ngắn sẽ đổi sang 12 số.
- Báo cáo dry-run: docs/sessions/2026-10-26/T477/archive_dup_rows.csv

## Đồng bộ khi Pass (Admin chốt 2026-10-26)
- Tên Việt Admin bấm Pass là tên chính thức: ghi `name_vi_map.name_vi_final` và `name_vi` (approved_by = admin).
- Pass phải đồng thời cập nhật dòng mã 12 số trong `namevi_map_places` và dựng lại chỉ mục tìm kiếm, để kết quả tìm kiếm khớp tên đã duyệt.
- Ô cần sửa trực tiếp là ô tên Việt của dòng đang xem. Ba cột Phiên âm, Gemini, Claude chỉ để đối chiếu.
- Kiểm chứng trên trình duyệt (127.0.0.1): bấm Pass một địa danh thử, kiểm tên hiển thị trong tìm kiếm.


# 2026-08-20/21 — T29: Mở rộng từ điển Hán-Việt, dọn ký tự Hán còn sót

## Mô tả ngắn task

Sau khi T01 đạt 100% coverage (`people.name_vi` không còn dòng rỗng), user hỏi tab "Chưa dịch"
trên `admin/placevn.html` có phải cùng loại bug vừa fix không. Kiểm tra ra đây là **cùng root
cause, khác bảng dữ liệu**: tab đó đọc từ `places_pending`/`namevi_map_places` (ĐỊA DANH), không
phải `people` (NHÂN VẬT). User đồng ý build fix, yêu cầu: lưu logs, git commit, đảm bảo revert
thuận tiện, đảm bảo không còn lỗi sót Hán tự trong tên.

## Phân tích quy mô

- `people.name_vi`: 12.636/48.673 dòng (26%) còn lẫn Hán tự, 1.898 ký tự riêng biệt.
- `places` (`COALESCE(namevi_map_places.name_vi, places_pending.name_vi)`): 15.238/116.989 dòng
  (13%) còn lẫn Hán tự + 9 dòng rỗng hoàn toàn, 1.519 ký tự riêng biệt.
- 2 tập ký tự trùng nhau 791 → gộp lại chỉ cần giải quyết **2.626 ký tự riêng biệt**.

## Tìm nguồn tra cứu hàng loạt

Tra tay từng ký tự (như 13 ký tự hôm trước) không khả thi ở quy mô 2.626 — cần 1 API cho phép tra
nhiều ký tự/request. WebSearch tìm được gist công khai mô tả API JSON của chính `hvdic.thivien.net`
(nguồn đã dùng và verify hôm trước — biên soạn từ Thiều Chửu + Trần Văn Chánh + Nguyễn Quốc Hùng):

```
POST https://hvdic.thivien.net/transcript-query.json.php
Body: mode=trans&lang=1&input=<chuỗi ký tự Hán>
```

Test trực tiếp với 13 ký tự đã tra tay trước đó — **kết quả khớp 100%** với những gì tôi đã verify
qua WebFetch trên trang HTML (chỉ khác thứ tự liệt kê các âm khi có nhiều âm) → xác nhận đây đúng
là cùng nguồn dữ liệu, tin cậy để dùng ở quy mô lớn.

## Quy trình build

1. **Backup trước khi sửa** (bắt buộc theo `CLAUDE.md`, và vì `data/` không nằm trong git nên revert
   qua git không áp dụng cho dữ liệu): dump toàn bộ `name_vi` hiện tại của cả 3 bảng
   (`people` 48.673 + `namevi_map_places` 118.296 + `places_pending` 118.295 dòng) ra
   `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json` trước khi UPDATE bất cứ
   gì.
2. Gộp toàn bộ ký tự Hán còn sót trong `name_vi` của cả 2 domain (người + địa danh) → 2.626 ký tự.
3. Viết `scripts/expand_hanviet_dictionary.py` — gọi API theo chunk 200 ký tự/request, delay 0,5s
   giữa các request. Kết quả: **2.375/2.626 (90,4%)** tìm được âm đọc, 238 ký tự API không có (quá
   hiếm/biến thể). Insert vào `custom_hanviet_override` bằng `INSERT OR IGNORE` — không đụng tới
   13 dòng đã người xác nhận tay hôm trước.
4. Viết `scripts/retranslate_residual_hanzi.py` — dịch lại (không phải find/replace trên chuỗi cũ,
   mà dịch lại từ `name_zh` gốc, giữ đúng format spaced+title-case đã dùng ở T01) cho MỌI dòng hiện
   đang lẫn Hán tự ở cả `people` và bảng địa danh, kể cả 9 dòng chưa từng được xử lý bao giờ (NULL
   thật, không phải "một phần dịch").
5. **Sự cố khi chạy:** DB bị khóa lần đầu vì server `app.py` đang chạy (đã học từ lần T01 trước —
   kiểm tra kỹ chỉ có 1 tiến trình `app.py` trước khi dừng, tránh lặp lại lỗi 3-tiến-trình-trùng đã
   gặp). Dừng server, chạy script (job nền do quét 235K+ dòng nên mất vài phút, output bị buffer
   nên không thấy log giữa chừng — đợi tới khi hoàn tất thay vì poll liên tục).

## Kết quả

| | Trước | Sau |
|---|---|---|
| `people.name_vi` còn lẫn Hán tự | 12.636 | **353** |
| `places` còn lẫn Hán tự | 15.238 | **276** |
| `places` rỗng | 9 | **0** |

Verify độc lập bằng SQL trực tiếp trên DB (không chỉ tin log script) — khớp đúng số liệu trên.

629 dòng còn lại (353+276) là hệ quả của đúng 238 ký tự mà **ngay cả từ điển tổng hợp uy tín nhất**
đã tra cũng không trả về âm đọc — đây là giới hạn thật của nguồn dữ liệu. Không tự bịa âm đọc để
"cho đủ 100%" — vi phạm nguyên tắc trung thực về dịch thuật đã thống nhất với admin (mọi bản dịch
phải verify được nguồn thật, không trình bày cái chưa xác minh như đã xác minh).

## Danh sách file đã tạo/sửa

- `data/lineage.db` — `custom_hanviet_override` (+2.375 dòng), `people.name_vi` (12.350 dòng
  UPDATE), `namevi_map_places.name_vi` (14.982 dòng UPDATE), `places_pending.name_vi` (9 dòng UPDATE)
- `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json` (mới — 9,1MB, backup đầy đủ)
- `scripts/expand_hanviet_dictionary.py` (mới, idempotent — tự tính lại danh sách ký tự thiếu từ DB
  mỗi lần chạy, không phụ thuộc file tạm)
- `scripts/retranslate_residual_hanzi.py` (mới, idempotent — chỉ UPDATE dòng thực sự đổi)
- `tasks/T01-seed-monk-persons.md` — đóng mục "Phát hiện thêm", trỏ sang T29
- `tasks/T29-hanviet-dictionary-expansion.md` — task file đầy đủ, gồm hướng dẫn rollback
- `docs/tasktodo.md` — thêm Task 29, cập nhật ghi chú Task 1
- `docs/sessions/2026-08-20_t29_hanviet_dictionary_expansion.md` — session log này

## Cách rollback

- **Code** (2 script mới + fix bug `seed_persons_namevi.py` từ T01): nằm trong git, revert bằng
  `git revert <commit>` hoặc `git checkout <commit trước> -- <file>` như bình thường.
- **Dữ liệu** (`people.name_vi`, `namevi_map_places.name_vi`, `places_pending.name_vi`): DB không
  nằm trong git (`.gitignore` loại trừ `data/`) — khôi phục bằng cách đọc lại
  `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json` (dict `id -> name_vi cũ`
  cho cả 3 bảng) và UPDATE ngược lại. Muốn undo luôn phần từ điển mở rộng thì xoá các dòng
  `custom_hanviet_override` có `added_by` bắt đầu bằng `bulk-verified-hvdic.thivien.net` hoặc
  `admin-verified-hvdic.thivien.net`.

## Liên hệ ROADMAP

- Nối tiếp T01 (Seed monk persons) và T08 (Missing hanzi admin — hạ tầng `custom_hanviet_override`
  tái sử dụng ở đây).
- Việc còn lại (không phải lỗi, giới hạn nguồn): 238 ký tự Hán chưa có âm Hán Việt trong bất kỳ
  nguồn đã tra — nếu muốn giải quyết tiếp cần tìm nguồn từ điển khác hoặc chấp nhận đây là hằng số
  (ký tự quá hiếm, biến thể tự dạng).

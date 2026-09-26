---
id: T29
title: Mở rộng từ điển Hán-Việt — dọn ký tự Hán còn sót trong name_vi (people + places)
module: Hán-Việt / Khoá 1
priority: high
status: done
depends_on: [T01, T08]
created: 2026-08-20
updated: 2026-08-21
done_when: name_vi (people + places) không còn dòng rỗng, số dòng còn lẫn ký tự Hán giảm về mức tối thiểu (chỉ còn ký tự thật sự không có âm Hán Việt trong nguồn từ điển đã tra)
---

# T29 — Mở rộng từ điển Hán-Việt (dọn sạch ký tự Hán còn sót trong tên)

## Bối cảnh

Sau khi T01 đạt 100% coverage cho `people.name_vi` (không còn dòng rỗng), user hỏi thêm về tab
"Chưa dịch" trên `admin/placevn.html` — phát hiện cùng loại vấn đề nhưng ở bảng ĐỊA DANH
(`places_pending`/`namevi_map_places`), quy mô lớn hơn: **15.238/116.989 dòng (13%)** name_vi còn
lẫn Hán tự, **1.519 ký tự Hán riêng biệt** chưa có trong từ điển. So sánh với phía Nhân Vật
(12.636 dòng, 1.898 ký tự) thì 2 tập ký tự trùng nhau 791 — gộp lại chỉ cần giải quyết
**2.626 ký tự riêng biệt** để dọn sạch cả 2 nơi.

User: "Đồng ý build... Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách
thuận tiện: bảo đảm ko còn lỗi sót hán tự trong tên."

## Nguồn dữ liệu dùng (thật, có trích dẫn)

`hvdic.thivien.net` — từ điển Hán Nôm trực tuyến, biên soạn từ Thiều Chửu + Trần Văn Chánh +
Nguyễn Quốc Hùng (đã dùng tra tay 13 ký tự hôm 2026-08-20, verify khớp với API dưới đây). Thay vì
tra từng ký tự bằng WebFetch (không khả thi ở quy mô 2.626 ký tự), dùng đúng API JSON của chính
site này:

```
POST https://hvdic.thivien.net/transcript-query.json.php
Content-Type: application/x-www-form-urlencoded
Body: mode=trans&lang=1&input=<chuỗi ký tự Hán, tối đa ~200 ký tự/request>
```

(Nguồn cách gọi API: gist công khai "Sino-Vietnamese with thivien.net API" của phineas-pta,
verify hoạt động đúng bằng test trực tiếp trước khi chạy hàng loạt — kết quả khớp 100% với 13 ký
tự đã tra tay trước đó.)

## Quy trình đã build

1. **Backup trước khi sửa** (bắt buộc theo `CLAUDE.md`, và theo yêu cầu "commit back thuận tiện"
   của user — vì `data/lineage.db` không nằm trong git, `.gitignore` loại trừ `data/`): dump toàn bộ
   `people.name_vi`, `namevi_map_places.name_vi`, `places_pending.name_vi` hiện tại ra
   `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json` (166.969 dòng) trước khi
   chạy bất kỳ UPDATE nào — có thể khôi phục nguyên trạng nếu cần.
2. Gộp toàn bộ ký tự Hán còn sót trong `people.name_vi` + `COALESCE(namevi_map_places.name_vi,
   places_pending.name_vi)` → **2.626 ký tự riêng biệt**.
3. Gọi API hàng loạt (chunk 200 ký tự/request, delay 0.5s giữa các request — lịch sự với server) →
   tìm được **2.375/2.626 (90,4%)**. **238 ký tự** API không trả về âm nào (ký tự quá hiếm/biến thể,
   ngay cả từ điển tổng hợp này cũng không có — không tự đoán, để nguyên).
4. Thêm 2.375 dòng vào `custom_hanviet_override` (hạ tầng có sẵn từ T08) bằng `INSERT OR IGNORE` —
   không ghi đè 13 dòng đã tra tay + verify thủ công trước đó (2 nguồn có thể khác thứ tự ưu tiên âm
   đọc cho cùng 1 ký tự, giữ bản đã người xác nhận).
5. Dịch lại (`translate_name()`, cùng logic/format đã dùng ở T01 — cách nhau dấu cách, viết hoa đầu
   âm tiết, ký tự chưa map giữ nguyên chữ Hán + log `missing_hanzi`) cho MỌI dòng hiện đang lẫn Hán
   tự trong cả 2 bảng — không chỉ dòng rỗng như T01, mà cả dòng "một phần đã dịch, một phần còn Hán".
6. Phát hiện thêm 9 dòng `places_pending` chưa từng được xử lý (không rỗng theo nghĩa T01 kiểm tra,
   mà đúng nghĩa `NULL` — không có row `namevi_map_places` tương ứng) — dịch nốt luôn cho đồng bộ.

## Kết quả

| | Trước T29 | Sau T29 |
|---|---|---|
| `people.name_vi` còn lẫn Hán tự | 12.636 | **353** |
| `places` (`namevi_map_places`/`places_pending`) còn lẫn Hán tự | 15.238 | **276** |
| `places` rỗng | 9 | **0** |

Giảm **97,2%** (người) và **98,2%** (địa danh) số dòng còn lỗi. 629 dòng còn lại (353+276) đều là
hệ quả của đúng 238 ký tự mà **ngay cả nguồn từ điển tổng hợp uy tín nhất đã tra cũng không có âm
Hán Việt** — không thể tự bịa âm đọc để "cho đủ 100%" (vi phạm nguyên tắc trung thực về dịch thuật).
Đây là giới hạn thật của nguồn dữ liệu, không phải lỗi sót có thể fix thêm bằng cách tra cứu tự động.

## File đã tạo/sửa

- `data/lineage.db` — `custom_hanviet_override` (+2.375 dòng), `people.name_vi` (12.350 dòng
  UPDATE), `namevi_map_places.name_vi` (14.982 dòng UPDATE), `places_pending.name_vi` (9 dòng UPDATE)
- `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json` (mới — backup trước sửa)
- `scripts/expand_hanviet_dictionary.py` (mới — bulk fetch qua API thivien.net, idempotent nhờ
  `INSERT OR IGNORE`, chạy lại được an toàn)
- `scripts/retranslate_residual_hanzi.py` (mới — dịch lại mọi dòng còn lẫn Hán tự ở cả 2 bảng,
  idempotent — chạy lại chỉ update những dòng thực sự đổi)
- `tasks/T01-seed-monk-persons.md` — cập nhật, đóng mục "Phát hiện thêm"
- `tasks/T29-hanviet-dictionary-expansion.md` — task file này
- `docs/tasktodo.md` — thêm Task 29
- `docs/sessions/2026-08-20_t29_hanviet_dictionary_expansion.md` — session log

## Cách rollback (nếu cần)

DB không nằm trong git (`data/` bị `.gitignore`) nên revert bằng git không áp dụng cho dữ liệu.
Cách khôi phục:
1. Đọc `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json`.
2. UPDATE lại `people.name_vi`/`namevi_map_places.name_vi`/`places_pending.name_vi` theo đúng
   dict trong file backup (key = id, value = name_vi cũ).
3. Xoá các dòng `custom_hanviet_override` có `added_by` bắt đầu bằng `bulk-verified-hvdic.thivien.net`
   hoặc `admin-verified-hvdic.thivien.net` nếu muốn undo cả phần từ điển mở rộng.

Phần CODE (2 script mới, fix bug trong `seed_persons_namevi.py`) nằm trong git — revert bình thường
bằng `git revert`/`git checkout` như mọi commit khác.

## Acceptance criteria (checklist)
- [x] Backup dữ liệu trước khi sửa (JSON dump, ngoài git vì DB không track)
- [x] Tra cứu hàng loạt qua nguồn thật (hvdic.thivien.net API), không đoán
- [x] Không ghi đè override đã người xác nhận trước đó (INSERT OR IGNORE)
- [x] Dịch lại toàn bộ dòng còn lẫn Hán tự ở cả 2 bảng (people + places)
- [x] `places` không còn dòng rỗng (0/116.989)
- [x] Giảm tối đa số dòng còn lẫn Hán tự xuống mức giới hạn thật của nguồn dữ liệu (629/165.662 = 0,38%, không phải 0% tuyệt đối — lý do đã ghi rõ ở "Kết quả")
- [x] Script chạy lại được an toàn (idempotent), dễ audit/rollback

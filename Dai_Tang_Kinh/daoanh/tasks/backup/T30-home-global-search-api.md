---
id: T30
title: HOME global search API (/daoanh/api/search) — build + fix stale/slow places FTS
module: HOME / Hạ tầng
priority: high
status: done
depends_on: [T01, T29]
created: 2026-08-21
updated: 2026-08-21
done_when: /daoanh/api/search trả đúng {monks, places, works}, đủ nhanh cho ô tìm kiếm HOME (< 1s), verify qua curl + browser thật
---

# T30 — HOME global search API

## Bối cảnh

Sau khi T01/T29 đưa `people.name_vi` lên gần 100% dịch trọn vẹn, user hỏi kết quả này show ở đâu
trên HOME. Kiểm tra `index.html` — ô tìm kiếm "Tìm kiếm thiền sư, chùa chiền, kinh sách" gọi
`GET /daoanh/api/search?q=...` mong đợi `{monks, places, works}`, nhưng **route này chưa từng tồn
tại trên backend — 404 toàn thời gian**, độc lập với việc name_vi đã dịch xong hay chưa. User đồng
ý build route này.

## Thiết kế

3 nguồn, đều đã là nguồn tin cậy sẵn có ở nơi khác trong app:
- `monks` — `people.name_vi`/`name_zh` (T01/T29 vừa đưa lên gần 100%)
- `places` — `places_pending` + `namevi_map_places` (cùng pattern COALESCE các endpoint khác dùng)
- `works` — `cbeta_catalog_vn` (Nguyễn Minh Tiến, CC BY-SA — đã có trong CLAUDE.md nguồn tin cậy)

## Sự cố phát hiện + fix trong lúc build

**1. Query places chậm (~2,5-3,2s/request)** — `LEFT JOIN places_pending↔namevi_map_places` +
`LIKE` 2 chiều wildcard trên 118K/118K dòng không dùng được index (leading wildcard). Đổi sang FTS5
(`places_pending_fts`, cùng pattern prefix-match `term*` đã chứng minh hoạt động tốt ở
`places_search()` — T11).

**2. FTS `places_pending_fts` bị stale** — hàm `ensure_places_pending_fts()` build FTS thẳng từ
`places_pending.name_vi`, KHÔNG qua COALESCE với `namevi_map_places.name_vi` như mọi endpoint khác
đọc tên địa danh. Hậu quả: 14.982 dòng T29 vừa dịch lại (ghi vào `namevi_map_places`) không hề phản
ánh vào FTS — search vẫn trả tên cũ còn lẫn Hán tự. Sửa: build FTS từ
`COALESCE(namevi_map_places.name_vi, places_pending.name_vi)`, đúng nguồn "sự thật" thống nhất với
toàn bộ app.

**3. `delete-all` FTS5 command không hoạt động cho bảng này** — `places_pending_fts` là bảng FTS5
thường (không phải contentless/external-content), nên lệnh đặc biệt
`INSERT INTO places_pending_fts(places_pending_fts) VALUES('delete-all')` luôn ném lỗi
`"may only be used with a contentless or external content fts5 table"`. Lỗi này **có từ trước**,
bị 1 `try/except` nuốt mất — nghĩa là **mọi lần force-rebuild trước đây (nếu có) đều CHỒNG dữ liệu
lên thay vì thay thế**, không ai biết. Phát hiện khi thấy số dòng FTS tăng gấp đôi (118.295 →
236.599) sau 1 lần `force=True`. Sửa bằng `DELETE FROM places_pending_fts` (SQL thường, hỗ trợ đầy
đủ cho bảng FTS5 không phải contentless).

**4. Fallback logic sai** — thiết kế ban đầu: nếu FTS trả về rỗng thì fallback sang LIKE chậm. SAI —
"rỗng" là câu trả lời ĐÚNG và phổ biến (đa số câu tìm tên tăng nhân sẽ không khớp địa danh nào cả),
nên fallback này bị kích hoạt ở CHÍNH những câu query mà tối ưu hoá nhắm tới, làm mất tác dụng tối
ưu hoàn toàn. Sửa: chỉ fallback khi FTS thật sự lỗi (exception), không fallback khi FTS trả về đúng
0 kết quả.

**5. Xung đột session:** 2 lần sửa `ensure_places_pending_fts()`/query places của
`api_global_search()` bị phiên dev khác ghi đè mất (file app.py bị lưu lại từ bản cũ hơn) — phải
làm lại, có verify ngay sau mỗi edit bằng `grep` để phát hiện sớm nếu bị mất lần nữa.

## Kết quả hiệu năng

| | Trước fix | Sau fix |
|---|---|---|
| Search chỉ có tăng nhân (không khớp địa danh nào) | 3,2s | **0,3-0,5s** |
| Search có khớp địa danh | ~1s | ~0,5-1s |

## Test đã chạy

```
curl "/daoanh/api/search?q=鑑堂"  -> 5 monks đúng ("Giám Đường"...), 0,3-0,5s
curl "/daoanh/api/search?q=哇罕"  -> "Oa Hãn" đúng (trước là "Oa 罕" — xác nhận FTS đã hết stale)
curl "/daoanh/api/search?q=Thiếu Lâm" -> đúng cả 3 category (chùa + kinh sách)
```

Browser thật: gõ "Thiếu Lâm" vào ô search trên HOME (`http://localhost:8080/daoanh/index.html`) →
hiện đúng "Chùa (1) Thiếu Lâm Tự 少林寺" + "Kinh sách (1) Thiếu Lâm Vô Khổng Địch" — verify qua
gõ phím thật (không chỉ gọi hàm), xác nhận toàn bộ pipeline search()→fetch→displayResults() hoạt
động đúng cho user thật.

## Phát hiện phụ (không thuộc scope, ghi nhận)

`places_pending` có 2 dòng riêng biệt cùng đại diện 1 địa danh dạng ID ngắn/dài
(`PL000032`/`PL000000000032`, cùng "Oa Hãn", cùng toạ độ) — search trả về 2 kết quả trùng lặp cho
case này. Vấn đề trùng ID ngắn/dài đã biết từ trước (có hàm `ensure_long_id()` xử lý ở nhiều nơi
khác trong app), không phải lỗi mới của T30 — không sửa trong task này.

## Danh sách file đã tạo/sửa

- `app.py` — route mới `api_global_search` (`/daoanh/api/search`), sửa `ensure_places_pending_fts()`
  (nguồn COALESCE + fix `delete-all` bug)
- `tasks/T30-home-global-search-api.md` — task file này
- `docs/tasktodo.md` — thêm Task 30
- `docs/sessions/2026-08-21_t30_home_search_api.md` — session log

## Acceptance criteria (checklist)
- [x] Route `/daoanh/api/search` trả đúng `{monks, places, works}` khớp format `index.html` mong đợi
- [x] Places dùng FTS5 thay LIKE — dưới 1s/request
- [x] FTS `places_pending_fts` sync đúng COALESCE (không còn stale so với `namevi_map_places`)
- [x] Fix bug `delete-all` (dọn 118.304 dòng trùng lặp phát sinh khi debug)
- [x] Fallback về LIKE chỉ khi FTS thật sự lỗi, không phải khi trả về 0 kết quả hợp lệ
- [x] Verify qua curl (nhiều query) + browser thật (gõ phím thật, không chỉ gọi hàm)

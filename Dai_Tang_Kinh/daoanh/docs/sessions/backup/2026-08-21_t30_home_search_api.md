# 2026-08-21 — T30: HOME global search API + FTS staleness/bugs fix

## Mô tả ngắn task

User hỏi: sau T01/T29 (name_vi dịch gần 100%), kết quả này show ở đâu trên HOME? Kiểm tra
`index.html` phát hiện ô tìm kiếm gọi `/daoanh/api/search` — route này **404, chưa từng được build**.
User đồng ý build.

## Build + các sự cố gặp phải (đã fix hết)

1. **Build route cơ bản** — `api_global_search()`, 3 nguồn: `people` (monks), `places_pending`+
   `namevi_map_places` (places), `cbeta_catalog_vn` (works). Khớp đúng format `data.monks/places/works`
   mà `index.html`'s `displayResults()` đã mong đợi sẵn từ trước.
2. **Phát hiện chậm** — test thật: 3,2s/request cho query places (LEFT JOIN + LIKE 2 chiều trên
   118K/118K dòng). Không chấp nhận được cho ô search gõ-là-thấy trên HOME.
3. **Tối ưu bằng FTS5** (`places_pending_fts`, đã có sẵn, cùng pattern đã chứng minh ở T11) — phát
   hiện thêm 2 bug ẩn trong chính hàm `ensure_places_pending_fts()` có từ trước:
   - Build FTS từ `places_pending.name_vi` trực tiếp, bỏ qua `namevi_map_places` — khiến FTS
     **stale** so với 14.982 dòng T29 vừa dịch lại. Sửa: build từ COALESCE đúng nguồn "sự thật".
   - `delete-all` FTS5 command ném lỗi bị nuốt (bảng này không phải contentless/external-content) —
     mọi force-rebuild trước giờ **chồng dữ liệu** thay vì thay thế (phát hiện khi thấy 118.295 dòng
     tăng vọt lên 236.599 sau 1 lần rebuild). Sửa bằng `DELETE FROM` thường.
4. **Bug fallback logic tự gây ra** — thiết kế "FTS rỗng → fallback LIKE" hoá ra sai: rỗng là kết quả
   ĐÚNG cho phần lớn query tăng nhân (không khớp địa danh nào), nên fallback kích hoạt liên tục,
   vô hiệu hoá tối ưu. Sửa: chỉ fallback khi FTS thật sự exception.
5. **Xung đột session 2 lần** — code sửa performance bị phiên dev khác ghi đè mất (app.py save lại
   từ bản cũ hơn của họ) ngay giữa lúc đang làm — phải làm lại cả 2 lần, thêm bước `grep` verify
   ngay sau mỗi edit để phát hiện sớm.

## Kết quả

- `/daoanh/api/search` hoạt động đúng, verify qua curl nhiều query khác nhau + browser thật (gõ
  phím thật trên HOME, không chỉ gọi hàm qua console).
- Hiệu năng: 3,2s → 0,3-0,5s cho case phổ biến nhất (chỉ khớp tăng nhân, không khớp địa danh).
- Tác dụng phụ tích cực: `places_pending_fts` giờ đồng bộ với COALESCE thật — bất kỳ chỗ nào khác
  trong app đang dùng bảng FTS này (nếu có) cũng được hưởng lợi từ việc hết stale.

## File đã sửa

- `app.py` — route mới `/daoanh/api/search`, sửa `ensure_places_pending_fts()`
- `tasks/T30-home-global-search-api.md` (mới)
- `docs/tasktodo.md` — thêm Task 30
- `docs/sessions/2026-08-21_t30_home_search_api.md` — session log này

## Liên hệ ROADMAP

- Hoàn thành vòng lặp T01 → T29 → T30: dữ liệu dịch xong (T01/T29) giờ đã thật sự **hiển thị được**
  cho user trên HOME (T30) — trước đó dữ liệu đúng nhưng không có đường nào tới được UI.
- Phát hiện phụ chưa xử lý: `places_pending` có dòng trùng ID ngắn/dài cho cùng 1 địa danh (case
  "Oa Hãn": `PL000032`/`PL000000000032`) — vấn đề đã biết, không thuộc scope T30.

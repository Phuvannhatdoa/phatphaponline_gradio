---
id: T416
title: "Tối ưu backend API `/autocomplete` (giảm 1–9 s → <500 ms)"
status: in_progress
created: 2026-10-19
updated: 2026-10-19
owner: ""
module: GIS / Places
priority: high
depends_on: [T404]
dispatch: approved
plan_approved_at: "2026-10-19 (Admin: duyệt profile+đề xuất phase; xem kết quả rồi duyệt sửa code nếu cần)"
done_when: >
  (1) Profile `/daoanh/api/public/autocomplete?q=` để xác định nút nghẽn thật (query SQL, bảng quét, vòng lặp Python,
  gọi `monk-resolve` lồng trong hay không).
  (2) Tối ưu để mỗi request <200 ms với các chuỗi đã biết chậm ("Thiếu L" và các chuỗi tương tự, xem T404 mục
  "Phát hiện ngoài phạm vi" #1).
  (3) Đo lại và xác nhận luồng "mớm từng chữ" của T404 (gõ từng ký tự → gợi ý hiển thị trong ≤0,5 s từ ký tự thứ 2)
  vẫn đạt khi gõ liên tục nhiều chữ, không riêng case "Lâm Tế" đã đo trước.
  (4) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  Tuỳ theo hướng tối ưu (sửa query / thêm cache / thêm index) — ghi cụ thể trong outcome khi thực hiện; nếu thêm
  index mới thì DROP INDEX không mất dữ liệu; nếu sửa code app.py thì backup trước khi sửa theo CLAUDE.md.
outcome: >
  [2026-10-19] Phase profile+đề xuất xong (daoanh/docs/sessions/2026-10-19/T416_profile_phase/profile_results.md).
  Root cause: route /daoanh/api/public/autocomplete (app.py:12358) chạy 4 query LIKE '%q%' tuần tự trên
  namevi_map_places/places_pending/marcus_reference/lexicon; wildcard 2 đầu không seek được bằng index. Nút
  nghẽn chính là places_pending (176,783 dòng): SQLite chọn full-table SCAN dù idx_places_pending_name_zh đã
  tồn tại (do DB chưa từng ANALYZE, không có sqlite_stat1). Đo thực tế case "Thiếu L": tổng 175+9620+19+113ms
  ≈ 9.9s lúc cache lạnh, ~1.4s lúc cache ấm — khớp đúng báo cáo "1-9s". Ép INDEXED BY idx_places_pending_name_zh
  đo được 224ms (giảm ~5x so với 1.1-1.3s ấm cache). namevi_map_places/marcus_reference chưa có index nào trên
  cột LIKE. Đề xuất theo thứ tự rủi ro tăng dần: (A) ANALYZE DB, (B) thêm INDEXED BY hint tại app.py:12376,
  (C) thêm index name_vi/label_vi/label cho 2 bảng còn thiếu, (D) dài hạn chuyển sang FTS5 như
  /daoanh/api/search đã làm (ensure_places_pending_fts). CHƯA sửa app.py, CHƯA tạo index/ANALYZE trên DB thật —
  chờ Admin duyệt hướng sửa trước khi làm bước 3-6 của done_when.
---

# T416 — Tối ưu backend API `/autocomplete`

## Bối cảnh

Từ T404 (Admin xác nhận DONE 2026-10-19): frontend `places.html` đã sửa xong (debounce + AbortController + xử lý
IME), phản hồi gõ chữ 237–484 ms từ lần gõ cuối. Nhưng backend `/daoanh/api/public/autocomplete?q=X` vẫn chậm
1–9 giây với một số chuỗi (ví dụ "Thiếu L"), nằm ngoài phạm vi sửa giao diện của T404.

Người dùng gõ "Lâm Tế" (4 ký tự + khoảng trắng) = tổng cộng ~1,5 s do backend, trong khi yêu cầu là <500 ms mỗi
ký tự gõ ("mớm từng chữ").

Tham chiếu: `tasks/T404-places-search-autocomplete-jank.md` mục "Phát hiện ngoài phạm vi" #1 — nghi vấn tại
`app.py` khoảng dòng 12358 (`/daoanh/api/public/autocomplete` + `/daoanh/api/monk-resolve`).

## Việc cần làm

1. Profile endpoint `/autocomplete?q=` — xác định bottleneck (SQL LIKE quét `marcus_reference`/`lexicon` không
   index, gọi lồng `monk-resolve`, hay xử lý Python).
2. Tối ưu (index, cache, giới hạn phạm vi quét, hoặc tách luồng monk-resolve ra khỏi autocomplete) để đạt <200 ms.
3. Xác nhận lại done_when (1) của T404 ("mớm từng chữ" ≤0,5 s) hoạt động đúng trên nhiều case, không chỉ case đã
   đo trước ("Lâm Tế").

## Các bước

- [x] Profile `/autocomplete?q=` (xác định bottleneck thật, ghi bằng chứng) — 2026-10-19
- [x] Đề xuất hướng sửa (query/index/cache) — nếu đổi schema DB thì trình Admin duyệt trước khi chạy — 2026-10-19
- [ ] Sửa + đo trước/sau
- [ ] Kiểm lại luồng gõ-gợi ý T404 trên trình duyệt thật (nhiều case)
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE


## Outcome (2026-10-21)

- **Đã áp đề xuất (B)** — `INDEXED BY idx_places_pending_name_zh` trong route
  `/daoanh/api/public/autocomplete` (app.py), có helper `_t416_pending_index_hint()`
  kiểm index tồn tại (an toàn trên VPS). Code-only, KHÔNG ghi DB.
- **Đo lại:** `'Thiếu L'` 1695–9338 ms → **278–347 ms**; `'Nghĩa Huyền'` 1545–1948 ms →
  **305–496 ms**; các chuỗi khác giữ nguyên tốc độ; số kết quả không đổi.
- **Commit:** `b40abd67` (chỉ phần T416, blob dựng từ HEAD — không sweep WIP session khác).
- **Còn lại:** mốc <200 ms cần thêm index `namevi_map_places.name_vi` / `lexicon.term`
  (**DB write → cần Admin duyệt**) hoặc FTS5. QA + Admin xác nhận.
- Report: `docs/sessions/2026-10-21/T416/T416_REPORT.md`.

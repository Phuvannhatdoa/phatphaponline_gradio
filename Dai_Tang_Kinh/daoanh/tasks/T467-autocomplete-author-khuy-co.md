---
id: T467
title: "Bug verify: BUG-052: Trang chủ autocomplete không gợi ý \"Khuy Cơ\" sau khi Admin import Author XML"
status: done
created: 2026-10-26
updated: 2026-10-26
done_when: >
  Xác định rõ nguyên nhân (một trong 4 nhánh: data chưa vào DB / index-FTS chưa
  cập nhật / endpoint lọc sai dấu-khoảng trắng / lỗi server-timeout) có bằng
  chứng DB + network log + screenshot; nếu sửa code thì search "Khuy Cơ" trên
  http://127.0.0.1:8080/daoanh/ phải trả gợi ý đúng, không regression các từ
  khóa khác (tên địa danh, tên người đã có từ trước); nếu nguyên nhân cần ghi
  DB/rebuild FTS thì dừng và trình đề xuất cho Admin duyệt, không tự ý ghi.
---

## Mô tả

Admin vừa import Author XML vào DB và "mớm autocomplete" (nạp dữ liệu gợi ý)
cho tên tác giả/tăng sĩ, nhưng ô tìm kiếm trên trang chủ
`http://127.0.0.1:8080/daoanh/` gõ "Khuy Cơ" không trả về gợi ý nào. Cần tái
hiện bằng browser thật (screenshot + network log), kiểm DB thực tế bảng chứa
tên author vừa import, kiểm endpoint autocomplete đang trỏ bảng/FTS nào, và
phân loại nguyên nhân theo 4 nhánh: (a) data chưa vào đúng bảng, (b) có data
nhưng FTS/index chưa rebuild sau import, (c) endpoint lọc sai dấu/khoảng
trắng, (d) lỗi server/timeout.

## Triệu chứng

- Route: `http://127.0.0.1:8080/daoanh/` (dùng IPv4, không dùng `localhost`).
- Gõ "Khuy Cơ" vào ô tìm kiếm/autocomplete trang chủ → không có kết quả gợi ý.
- Context: Admin vừa import Author XML và đã nạp dữ liệu gợi ý autocomplete.

## Nguyên nhân nghi ngờ

Chưa xác định — cần audit DB (bảng author mới import), endpoint autocomplete
đang dùng FTS nào (có thể `places_search_fts` chỉ index địa danh, không index
người), và so sánh biến thể có dấu/không dấu.

## Kết quả điều tra (2026-10-26)

**Nguyên nhân xác định: (c) endpoint/consumer contract mismatch (không phải dấu/khoảng trắng, mà là sai tên field JSON).**

- DB: "Khuy Cơ" (dila_id A001019) **có sẵn** ở nhiều bảng: `people.name_vi`
  (dùng bởi `/daoanh/api/search`), `dila_catalog_contributors.name_vi` (5589
  dòng, nguồn ZQLOCAL), `ai_person_name`, `codex_person_name`. Branch (a) —
  data chưa vào DB — bị loại.
- FTS: `/daoanh/api/search` không dùng FTS cho monks (LIKE trực tiếp trên
  `people`), chỉ places mới qua `places_pending_fts`. `curl`/python LIKE trực
  tiếp DB xác nhận match đúng. Branch (b) — FTS chưa rebuild — bị loại.
- Backend `app.py` route `api_global_search` (`/daoanh/api/search`, dòng
  ~13173) trả JSON keys thật: `{success, monks, places, works}`.
- Frontend `index.html` hàm `handleSearch()` (dòng ~1162, gắn từ T453) lại đọc
  `d.dila_works` / `d.dila_people` / `d.dila_works_total` — **các field này
  không tồn tại ở bất kỳ đâu trong app.py** (grep `dila_works`/`dila_people`
  trong app.py = 0 match). Hệ quả: `works.length` và `people.length` LUÔN = 0
  bất kể backend trả gì → `handleSearch()` LUÔN redirect sang
  `/daoanh/places?q=...` dù monks có kết quả đúng — đây là lỗi hệ thống, ảnh
  hưởng MỌI từ khóa monk/tác giả trên trang chủ, không riêng "Khuy Cơ".
- Tái hiện qua browser thật (`http://127.0.0.1:8080/daoanh/`, IPv4) trước fix:
  gõ "Khuy Cơ" → Enter → network log `GET /daoanh/api/search?q=Khuy%20C%C6%A1
  → 200 OK` (trả đúng `monks:[{id:"A001019", name_vi:"Khuy Cơ", name_zh:"窺基"}]`
  qua test trực tiếp API) nhưng trang vẫn redirect sang
  `/daoanh/places?q=Khuy%20C%C6%A1` (không có kết quả vì đó là trang địa danh,
  không tìm người) — khớp đúng triệu chứng BUG-052.

## Đã sửa (chỉ code, không DB/FTS)

File: `index.html` (backup tại `docs/sessions/2026-10-26/index.html` trước
khi sửa).

- `handleSearch()`: đổi đọc `d.dila_works`/`d.dila_people` → đọc đúng field
  thật `d.monks`/`d.works`.
- Thêm renderer mới `renderSearchResultsMonks()` / `renderSearchResultsWorks()`
  / `renderSearchResults()` khớp đúng shape thật của response (monks:
  id/name_vi/name_zh; works: title_vi/title_zh/author/era) — không tái dùng
  `renderDilaWorks`/`renderDilaPeople` cũ vì các field đó (person_id, juans,
  contributors, cbeta_id...) không có trong response này.
- Không đổi route `api_global_search`, không đổi DB, không rebuild FTS.

**Đề xuất cần Admin quyết (KHÔNG tự làm):** nếu muốn khôi phục đúng tính năng
T453 "kinh lục DILA" đầy đủ (hiển thị số tác phẩm/quyển/nơi dịch theo từng
tác giả như `renderDilaWorks`/`renderDilaPeople` cũ mong đợi), cần xây mới
một endpoint backend JOIN `dila_catalog_works` + `dila_catalog_contributors`
trả đúng field `dila_works`/`dila_people`/`dila_works_total` — việc này tốn
công hơn phạm vi "bug verify" nên KHÔNG tự triển khai; bản vá hiện tại chỉ
phục hồi việc hiển thị kết quả đúng (tên + DILA ID / tên tác phẩm + soạn
dịch + niên đại) bằng dữ liệu `/daoanh/api/search` đã có sẵn.

## Kết quả test (browser thật, http://127.0.0.1:8080/daoanh/)

- "Khuy Cơ" → Enter: hiển thị "1 kết quả cho Khuy Cơ" + card 🧘 Khuy Cơ 窺基
  DILA ID A001019. PASS.
- "Thiếu Lâm Tự" (regression, nhánh demo riêng không qua fetch): vẫn hiện
  panel minimap Thiếu Lâm Tự như cũ. PASS, không regression.
- "Long Môn" (regression, nhiều monk trùng tên): hiện 4 kết quả monk đúng
  tên "Long Môn ...". PASS, không regression.
- Console: không có lỗi JS mới phát sinh từ `index.html` sau khi sửa (404 còn
  lại là của `places.html` khi tra "Khuy Cơ" như địa danh — hành vi cũ, ngoài
  phạm vi T467).

## Vòng 2 — sửa theo QA CHƯA ĐẠT (2026-10-26)

QA phát hiện 2 vấn đề trên bản sửa vòng 1:

1. **Regression chính:** khi API trả cả `monks` và `places` (vd "Long Môn" → 4
   monks + 10 places), bản vòng 1 chỉ render `monks`, bỏ qua `d.places` —
   10 địa danh bị mất so với hành vi cũ (redirect sang `/daoanh/places?q=...`).
   **Đã sửa:** chọn hướng (b) — thay đổi tối thiểu. Trong `handleSearch()`,
   thêm kiểm tra `places.length`: nếu `d.places` có phần tử, redirect sang
   `placesUrl` như hành vi cũ (không render inline); chỉ render card tại
   trang chủ khi có `monks`/`works` **và không có** `places` (đúng case
   "Khuy Cơ" — monks-only).
2. **Badge "ZQ" hard-code:** `renderSearchResultsMonks()` trước đó gắn cứng
   `<span class="dw-badge" title="Tên Việt: phiên âm ZQ">ZQ</span>` cho MỌI
   monk, không dựa trên nguồn thật. Xác minh: `/daoanh/api/search` (route
   `api_global_search`, app.py dòng ~13196) chỉ SELECT `id, name_vi, name_zh`
   từ `people` — không trả `source`/`source_id`/`entity_claims` nào, và QA đã
   xác nhận `entity_claims` không có claim cho A001019/A041315. **Đã sửa:**
   bỏ badge cứng "ZQ"; chỉ render badge nguồn nếu `p.source` có giá trị thật
   từ API (hiện luôn rỗng → badge không hiện, đúng CLAUDE.md §ZQ: không gán
   bừa nguồn khi chưa xác định được).

File sửa: `index.html` (hàm `handleSearch`, `renderSearchResultsMonks`).
Backup trước khi sửa vòng 2: `docs/sessions/2026-10-26/index.html.round1`
(bản vòng 1), `docs/sessions/2026-10-26/index.html` (bản gốc trước vòng 1).

### Test vòng 2 (browser thật, http://127.0.0.1:8080/daoanh/)

- "Khuy Cơ" → Enter: `GET /daoanh/api/search?q=Khuy%20C%C6%A1 → 200 OK`.
  Không redirect, vẫn ở trang chủ, hiện "1 kết quả cho "Khuy Cơ"" + card
  🧘 Khuy Cơ 窺基, DILA ID A001019, **không có badge ZQ** (đúng — API không
  trả nguồn). PASS.
- "Long Môn" → Enter: `GET /daoanh/api/search?q=Long%20M%C3%B4n → 200 OK`
  (trả về monks + places), sau đó trang **redirect** sang
  `/daoanh/places?q=Long%20M%C3%B4n` (hướng b, giữ hành vi cũ, không mất kết
  quả địa danh). URL tab xác nhận: `http://127.0.0.1:8080/daoanh/places?q=Long%20M%C3%B4n`.
  PASS. (404 `api/entity/.../unified` và `api/places/Long%20Môn` trên trang
  places là hành vi cũ có sẵn của `places.html` khi xử lý query-param dạng
  entity lookup — ngoài phạm vi T467, không phải lỗi mới.)
- "Thiếu Lâm Tự" → Enter: không gọi `/daoanh/api/search` (nhánh
  `showPlaceDemo()` chặn trước khi tới fetch, như code gốc), hiện demo panel
  "Thiếu Lâm Tự · 少林寺" như cũ, không lỗi JS mới. PASS, không regression.

Status: vẫn `in_progress` — chờ daoanh-qa kiểm chứng lại vòng 2.

## Phạm vi dự kiến

- Chỉ sửa code (resolver/endpoint/index build script) nếu nguyên nhân rõ và
  không cần ghi DB lớn.
- Nếu cần rebuild FTS index hoặc ghi DB → dừng, trình đề xuất cho Admin duyệt
  (dry-run → duyệt → apply, backup `lineage.db`, ghi `docs/ROLLBACK.md`).
- Không sửa dashboard, không sửa task khác.

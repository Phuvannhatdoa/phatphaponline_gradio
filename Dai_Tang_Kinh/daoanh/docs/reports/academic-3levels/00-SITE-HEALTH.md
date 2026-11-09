# 00 — Sức khỏe site & phát hiện xuyên cấp (bằng chứng)

> **Khảo sát:** 2026-10-25, giờ Việt Nam (UTC+7). **Đích:** https://phatphaponline.org (bản deploy công khai của dự án Đạo Ảnh).
> **Vai:** Team Lead, khảo sát xuyên cấp để chuẩn bị báo cáo cho Admin → đội Planning.
> **Phương pháp:** chỉ GET (không ghi, không đăng nhập, không đụng DB/server), dùng `python requests` + đọc code tĩnh repo local để giải thích nguyên nhân. **Không có browser** trong sandbox ⇒ mọi kết luận về hành vi JS render đều ghi rõ mức độ tin cậy.
> **Nhãn bằng chứng:** **[ĐO]** = đo trực tiếp từ live (URL + HTTP + trích response) · **[CODE]** = suy luận từ code deploy/static (file:line) · **[CHƯA KT]** = chưa kiểm chứng được trong sandbox.

---

## 1. Bảng trạng thái trang & điều hướng

| # | Đường dẫn | HTTP | Ghi chú |
|---|---|---|---|
| 1 | `/daoanh/` ≡ `/daoanh/home.html` | 200 | Trang chủ, 36.6 KB |
| 2 | `/daoanh/places` ≡ `/daoanh/places.html` | 200 | Bản đồ GIS + khung 16 tab chi tiết địa danh, 761 KB |
| 3 | `/daoanh/lineage?id=<DILA_ID>` | 200 | Trang phổ hệ (render phía client) |
| 4 | `/daoanh/about` | 200 | Về dự án |
| 5 | `/daoanh/opendata` | 200 | Dữ liệu mở / license |
| 6 | `/daoanh/community` | 200 | Cộng đồng |
| 7 | `/daoanh/tripitaka` | **404** (nginx) | Thẻ "Đại Tạng" ở trang chủ trỏ vào đây |
| 8 | `/daoanh/people` | **404** (nginx) | Thẻ "Tu Sĩ" trỏ vào đây |
| 9 | `/daoanh/timeline` | **404** (nginx) | Thẻ "Niên Đại" trỏ vào đây |
| 10 | `/daoanh/graph` | **404** (nginx) | Thẻ "Đồ Thị Quan Hệ" trỏ vào đây |
| 11 | `/daoanh/docs/` | **404** (nginx) | Trang Cộng đồng giới thiệu "Tài liệu kỹ thuật GitBook" → link chết |
| 12 | `/daoanh/dashboard/` | **404** (nginx) | Trang Cộng đồng giới thiệu "Dashboard tiến độ" → link chết |
| 13 | `/daoanh/login.html` | **502** (nginx) | Upstream auth gateway không phản hồi |
| 14 | `/daoanh/admin/` | **200** | ⚠ Trang admin tải công khai (82 KB) — cần Admin xác nhận có chủ đích không |
| 15 | `/daoanh/namevimap.html` | 200 | Công cụ mapping tên Việt, tải công khai |
| 16 | `/daoanh/places/<PL_ID>` | **404** (nginx) | Đây chính là URL mà ô tìm kiếm trang chủ sinh ra |
| 17 | `/robots.txt`, `/sitemap.xml` | **404** | Không có chỉ dẫn crawler/sitemap |
| 18 | `/daoanh/openapi.json`, `/daoanh/api/openapi.json`, `/daoanh/swagger/` | **404** | Không có đặc tả API công khai |

---

## 2. Phát hiện xuyên cấp (SH = Site Health)

### SH-01 — Điều hướng chính dẫn tới 4/6 trang 404, tài liệu & dashboard chết **[ĐO]**
- Bằng chứng: bảng trên dòng 7–12. Trang chủ render 6 thẻ chủ đề; chỉ "Địa Danh" (places) và "Truyền Thừa" (lineage) là tới đích thật. "Đại Tạng", "Tu Sĩ", "Niên Đại", "Đồ Thị" → 404.
- Code: `daoanh/home.html` chứa các `href="/daoanh/tripitaka"`, `/people`, `/timeline`, `/graph`; trong `app.py` **không có route** tương ứng ⇒ nginx trả 404.
- Ảnh hưởng: người dùng mất niềm tin ngay từ cửa vào; mọi "năng lực tra cứu" quảng cáo trên trang chủ không có đường tới.
- Yêu cầu Planning: hoặc dựng trang đích (dù chỉ là landing tạm có nội dung thật), hoặc bỏ thẻ khỏi trang chủ cho tới khi có. **AC:** 100% link nội bộ trên `/daoanh/`, `/daoanh/community`, `/daoanh/opendata` trả < 400; có test tự động crawl link.

### SH-02 — Ô tìm kiếm trang chủ không tìm kiếm: đẩy sang `places?q=` rồi bị bỏ qua, hoặc hiện demo cứng **[ĐO]**
- Bằng chứng:
  - Live `/daoanh/` **không nạp** `home_search.js`/`search.js` (0 lần xuất hiện trong HTML); luồng thật là inline `handleSearch`: nếu chuỗi chứa "Thiếu Lâm"/"少林" → gọi `showPlaceDemo()` (dữ liệu demo hard-code); nếu không → `window.location.href = '/daoanh/places?q=' + encodeURIComponent(q)`.
  - `GET /daoanh/places?q=Kinh%20Phap%20Hoa` → **200 nhưng body md5 trùng hệt `/daoanh/places`** (761.121 B) ⇒ nginx/trang bỏ qua tham số `q`; sau đó `places.html` lại hiểu `q` là **ID địa danh** → `GET /daoanh/api/places/<q>` → 404 → panel chi tiết kẹt "Đang tải…".
  - `GET /daoanh/api/places/Kinh%20Kim%20Cang` → 404 `{"error":"Place not found"}`.
- Code: `daoanh/home.html` inline `handleSearch` (~dòng 1120); `daoanh/places.html` (~11602/11623) xử lý `q` như ID; `daoanh/home_search.js` (file có trên server, 200) không được nạp.
- Ảnh hưởng: đường vào tra cứu phổ biến nhất (ô lớn ở hero) hoặc không tìm gì, hoặc chỉ hoạt động với đúng một từ khoá "Thiếu Lâm" và hiện dữ liệu demo — sinh viên không phân biệt được demo với dữ liệu thật.
- Yêu cầu Planning: (a) thay `handleSearch` bằng tìm kiếm thật qua `/daoanh/api/search` (monks/works/places) và render trang kết quả; (b) bỏ `q`-as-ID trong `places.html` hoặc đổi tên tham số; (c) xoá demo hard-code hoặc gắn nhãn "ví dụ". **AC:** gõ "Kinh Kim Cang", "Huyền Trang", "Thiếu Lâm Tự" đều ra kết quả đúng loại; không có dữ liệu demo lẫn vào kết quả thật.

### SH-03 — Năng lực tra cứu đã có trong API nhưng không có cửa vào công khai **[ĐO]+[CODE]**
- Bằng chứng (đo 2026-10-25):
  - `/daoanh/api/search?q=Kim%20Cang` → `200 {monks: 9, places: 0, works: 10}` (tìm tổng hợp, kể cả không dấu).
  - `/daoanh/api/glossary?term=B%C3%A1t%20Nh%C3%A3` → `200 {matches:[{term:"Bát Nhã", definition:"Prajñā (S), Hannya (J).", source_label:"Từ điển PG VN (Tu Dien Da Ngon Ngu - Cs Minh Thong)"}]}` — **từ điển thuật ngữ hoạt động**.
  - `/daoanh/api/cbeta/catalog?q=Kim%20Cang` → `200` trả `Kim Cang Bát Nhã Ba La Mật Kinh`, `sh_number 235`, `page 748` — **mục lục kinh tìm được bằng tiếng Việt**.
  - `/daoanh/api/lineage-ref/passage?ref=T50n2060_p0574b20` → `{ok:true, resolved:{found:true, passage_id:3918, text_id:"T50n2060"}}` — **resolve được CBETA ref**.
- Code: các endpoint trên đều tồn tại (`app.py`), nhưng **không trang công khai nào gọi** (trang chủ chỉ gọi `places/search`; menu không có mục Từ điển/Mục lục; `/tripitaka` 404).
- Ảnh hưởng: đây là điểm mạnh nên khai thác — vấn đề chính là "thiếu cửa vào", không phải thiếu dữ liệu. Planning nên ưu tiên nối các API sẵn có lên UI thay vì viết mới.
- Yêu cầu Planning: (a) gắn `/api/search` + `/api/glossary` + `/api/cbeta/catalog` vào UI tìm kiếm chung; (b) công bố schema + trạng thái. **AC:** từ 1 ô tìm kiếm tra được 1 thuật ngữ, 1 tên kinh (ra mục lục), 1 nhân vật, 1 địa danh.

### SH-04 — Số liệu công bố mâu thuẫn giữa trang chủ – Về dự án – API **[ĐO]**
| Chỉ số | Trang chủ | Trang Về dự án | API công khai (đo 2026-10-25) |
|---|---|---|---|
| Địa danh | 8,241 | 59,167 | `/api/dila/places` **total 59,167**; `/api/dila/stats` total 59,167 |
| Mục lục kinh | 13,520 | 13,520 | `/api/cbeta/catalog` **total 3,122** (157 trang × 20) |
| Hồ sơ tăng nhân | 5,800+ | 48,673 | `/api/dila/persons/stats` **total 48,673** |
| Dòng truyền thừa | 1,200+ | 2,000+ hồ sơ phả hệ | `/api/dashboard/stats` **marcus_edges 11,169** |
- Ảnh hưởng: con số là "lời hứa" với người tra cứu; hiện không thể tái lập con số nào từ API công khai, không có ngày chốt số/phiên bản dataset.
- Yêu cầu Planning: một nguồn số liệu duy nhất (single source) có `dataset_version` + ngày + endpoint đối ứng; mỗi con số trên UI phải bấm được tới danh sách tương ứng. **AC:** mọi số trên UI khớp `count` của API tương ứng ở cùng thời điểm.

### SH-05 — Toàn văn kinh điển gần như không có; tìm kiếm tiếng Việt trong corpus trả 0 **[ĐO]**
- Bằng chứng:
  - `GET /daoanh/api/cbeta/texts` → `{"count":5}`: T51n2076 Cảnh Đức Truyền Đăng Lục, T50n2060 Tục Cao Tăng Truyện, T50n2061 Tống Cao Tăng Truyện, X77n1524 Vô Lượng Thọ Kinh Ưu Ba Đề Xá, T50n2062 Đại Minh Cao Tăng Truyện — **không có kinh chính** (Kim Cang, Pháp Hoa, Bát Nhã…).
  - `GET /daoanh/api/cbeta/corpus-search?q=%E9%87%91%E5%89%9B` → `200 {coverage:{catalog_total:3122, passages_searchable:72628, texts_searchable:5, scope:"imported_corpus"}, result_count:30}` (chỉ 5 bộ đã nhập được đánh chỉ mục).
  - `GET /daoanh/api/cbeta/corpus-search?q=%E8%89%B2%E5%8D%B3%E6%98%AF%E7%A9%BA` ("色即是空") → `result_count: 0`.
  - `GET /daoanh/api/cbeta/corpus-search?q=s%E1%BA%AFc` ("sắc", tiếng Việt) → `result_count: 0`.
  - `GET /daoanh/api/cbeta/text/T51n2076/browse` → `coverage:{complete_text:false, granularity:"context_snippet", note:"Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn"}`.
- Ảnh hưởng: đây là **gốc rễ** khiến cả 3 cấp không thể "đọc/đối chiếu/kiểm chứng" bản văn; mọi tab kinh điển chỉ là snippet trích theo nhân vật.
- Yêu cầu Planning: tách rõ 2 khái niệm trên UI — "mục lục" vs "toàn văn"; nêu coverage từng bộ; bổ sung ít nhất các kinh phổ biến cho giáo trình Cử nhân, và index tiếng Việt/phiên âm nếu có bản dịch. **AC:** người dùng biết chính xác bộ nào đọc được toàn văn; tìm một câu tiếng Việt trong bản dịch trả hit kèm vị trí.

### SH-06 — Không có tài liệu API, không có đặc tả máy đọc, CORS chỉ mở cho chính site **[ĐO]**
- Bằng chứng: `/daoanh/docs/` 404; `/daoanh/api/openapi.json`, `/openapi.json`, `/daoanh/swagger/` đều 404. CORS: gửi `Origin: https://phatphaponline.org` → có `Access-Control-Allow-Origin: https://phatphaponline.org`; gửi `Origin: https://example.org` → **không có header CORS** (script nghiên cứu ngoài origin bị chặn). Không có header mô tả rate limit/version. Tiền tố route không nhất quán: `/daoanh/api/evidence/A000294` → 200 nhưng `/api/evidence/A000294` → 404, trong khi `/api/admin/verification/list` → 200 còn `/daoanh/api/admin/verification/list` → 404.
- Ảnh hưởng: cấp Tiến sĩ cần API để tái lập, không có tài liệu thì mỗi endpoint phải "đoán"; CORS chặn tích hợp từ notebook của nghiên cứu sinh; tiền tố lẫn lộn làm script dễ sai.
- Yêu cầu Planning: công bố OpenAPI/Swagger + trang docs (kể cả tĩnh) + chính sách CORS cho mục đích nghiên cứu + version; thống nhất một tiền tố công khai. **AC:** `/docs` 200, có OpenAPI JSON validate được; 1 script Python ngoài origin gọi được API đọc.

### SH-07 — Hợp đồng lỗi không nhất quán, khó lập trình/tự động hoá **[ĐO]**
- Bằng chứng cùng một "không tìm thấy" nhưng 4 dạng: nginx 404 HTML 162 B (`/daoanh/people`); Flask 404 HTML 207 B (`/daoanh/api/passage/1`); JSON 404 có `ok:false` (`/daoanh/api/places/1`); 405 HTML (`/daoanh/api/daitang/qa` GET). Lỗi tham số: JSON `{"error":...,"ok":false}` (glossary thiếu `term`) nhưng nhiều endpoint khác không có `ok`.
- Ảnh hưởng: client/đối tác không phân biệt "route không tồn tại" vs "tài nguyên không có" vs "sai tham số".
- Yêu cầu Planning: chuẩn hoá error envelope `{ok:false, error, code, hint}` cho toàn bộ `/api/*`, và phân biệt 404-route vs 404-resource. **AC:** tài liệu lỗi + test contract.

### SH-08 — Bản sắc thực thể không nhất quán giữa các endpoint (cần xác minh) **[ĐO]**
- Bằng chứng với cùng ID `A000294`:
  - `/daoanh/api/monk/search?q=Huy%E1%BB%81n%20Trang` → `han_name 玄奘`, `vn_name Huyền Trang`, id A000294.
  - `/daoanh/api/monk/A000294/graph` → `center.label "Huyền Trang"`, `label_zh "玄奘"`.
  - `/daoanh/api/entity/A000294` + `/unified` → `canonical_label "玉華法師"`, `canonical_name_vi ""`.
- Ảnh hưởng: người tra cứu thấy hai "danh tính" cho một ID; trích dẫn sẽ sai. (Có thể 玉華法師 là hiệu khác của Huyền Trang, nhưng hệ thống chưa nêu quan hệ alias.)
- Yêu cầu Planning: một canonical label + danh sách alias có nguồn; endpoint entity phải trả `label_vi` và alias kèm nguồn. **AC:** mọi endpoint cùng ID trả cùng canonical + alias có provenance.

### SH-09 — Bản dịch tiếng Việt gần như bằng 0 ở tầng dữ liệu (không phải tầng UI) **[ĐO]**
- Bằng chứng: `/daoanh/api/dila/persons/stats` → `{"total":48673,"with_bio_zh":48180,"translated_saved":10,"translated_draft":0}` — 10/48.673 hồ sơ có bản dịch đã lưu (~0,02%).
- Ảnh hưởng: hệ "tra cứu bằng tiếng Việt" nhưng nội dung tiểu sử gần như chỉ có Hán; sinh viên Cử nhân không đọc được.
- Yêu cầu Planning: hiển thị rõ trạng thái dịch theo từng hồ sơ (đã dịch / máy dịch nháp / chưa có) và không trình bày nội dung Hán như thể đã Việt hoá; ưu tiên dịch các hồ sơ thuộc giáo trình.

### SH-10 — Progress dashboard nội bộ: dữ liệu cũ 22 ngày, và UI dashboard đã 404 **[ĐO]**
- Bằng chứng: `GET /daoanh/api/progress/dashboard` → `generated_at 2026-10-03T11:23:48`, `total_progress 73`, `meta.route_total 303`, `task_meta {done:47, in_progress:22, pending:35, blocked:2, total:106}`, `endpoints_compare` 249 mục trong đó **97 mục "docs claim nhưng code không thấy"** (152/249 khớp). Trong khi `/daoanh/dashboard/` (UI để xem) = 404.
- Ảnh hưởng: Admin/Planning không có cửa xem tiến độ công khai; số liệu đã cũ nếu dùng để lập kế hoạch.
- Yêu cầu Planning: hoặc dựng lại `/dashboard/`, hoặc bỏ link; thêm `generated_at` hiển thị rõ trên mọi báo cáo tiến độ.

### SH-13 — Number mismatches (home vs API)  **[ĐO]**
- Bằng chứng: `/daoanh/login.html` → 502. Tải công khai (200) các trang quản trị: `/daoanh/admin/` (82 KB), `/daoanh/emails.html` (title "Quản lý Admin"), `/daoanh/namevimap.html` (title "Name Vi Map - Quản lý tên tiếng Việt"). API admin ở tiền tố gốc trả dữ liệu không cần cookie:
  - `GET /api/admin/verification/list` → **200**, `Content-Length: 28540933` (28,5 MB JSON: biography, authority_links…)
  - `GET /api/admin/staging/list` → 200; `GET /api/admin/sources` → 200.
- Ảnh hưởng: rủi ro toàn vẹn dữ liệu + audit (bên ngoài đọc được danh sách kiểm chứng), không đủ điều kiện công bố "dataset đã kiểm chứng".
- Yêu cầu: Admin xác nhận mô hình truy cập; khôi phục auth hoặc chặn `/api/admin/*` ở nginx ngay; ghi audit cho thao tác ghi. **AC:** API admin trả 401/403 khi chưa đăng nhập; quy trình duyệt claim có `reviewed_by` + audit trail.

### SH-13 — Bộ lọc `persons/browse` lỗi SQL 500 **[ĐO]**
- Bằng chứng: `GET /daoanh/api/persons/browse?has_lineage=1&limit=2` → **500** `{"error":"near \"AND\": syntax error","ok":false}`; cùng endpoint không tham số → 200. Đây là filter hiển nhiên mà học viên Cao học/Tiến sĩ sẽ dùng (lọc người có phả hệ).
- Yêu cầu Planning: sửa query builder (dựng WHERE có điều kiện, không nối chuỗi rỗng), test mọi tổ hợp filter. **AC:** mọi tham số filter của persons/browse trả 200 + số đếm khớp DB.

### SH-13 — Bộ lọc `persons/browse` lỗi SQL 500 **[ĐO]**
Các endpoint đọc được, trả 200 (đã đo 2026-10-25):

| Nhóm | Endpoint | Trả về |
|---|---|---|
| Địa danh | `/daoanh/api/places/search?q=&limit=&cate=&offset=` | tìm theo tên (nhạy dấu; không có `dila_id`) |
| Địa danh | `/daoanh/api/places/all`, `/api/dila/places?limit=&offset=`, `/api/dila/stats` | danh sách + tổng 59.167 |
| Địa danh | `/daoanh/api/places/<PL_ID>` và `/{cbeta,graph,persons,timeline,events,pali}` | hồ sơ địa danh + liên kết |
| Nhân vật | `/daoanh/api/monk/search?q=`, `/api/dila/persons`, `/api/persons/browse?limit=&offset=` | tìm + duyệt (48.673; 18.121 có phả hệ) |
| Nhân vật | `/api/person/<A_ID>/profile`, `/api/monk/<A_ID>/{graph,lineage-tree,ancestor-spine,ancestor-path}` | hồ sơ + phả hệ |
| Nhân vật | `/api/entity/<ID>`, `/unified`, `/summary`, `/canon`, `/passages`, `/related`, `/evidence/<ID>` | thực thể hợp nhất + bằng chứng |
| Kinh điển | `/api/cbeta/catalog?q=&page=&limit=` (total 3.122), `/api/cbeta/texts` (5), `/api/cbeta/text/<sigla>/browse`, `/api/cbeta/corpus-search?q=` (texts_searchable 5) | mục lục + snippet |
| Truyền thừa | `/api/nexus/find?q=`, `/api/lineage-ref/passage?ref=`, `/api/lineage-ref/context?ref=` | nexus + trích dẫn |
| Niên đại | `/api/chronology/events`, `/api/chronology/dynasties`, `/api/chronology/search` | sự kiện |
| Chung | `/api/search?q=` ({monks, works, places}), `/api/public/autocomplete?q=`, `/api/glossary?term=` | tìm tổng hợp, gợi ý, thuật ngữ |
| Meta | `/api/dashboard/stats`, `/api/progress/dashboard` | số liệu + tiến độ |

---

## 3. Điều chưa kiểm chứng / giới hạn của lần khảo sát
- **Không render JS:** không có browser ⇒ chưa xác nhận được (a) các tab trong `places.html` thật sự hiển thị gì sau khi gọi API, (b) lỗi console client-side, (c) hành vi empty-state khi API 404/500. Các đồng nghiệp ở 3 file cấp học cũng bị giới hạn này và đã ghi rõ.
- Một số endpoint cần POST/tham số đúng (`/api/daitang/qa`, `/api/passage/<id>/translate`) nên chỉ đo được mã lỗi, chưa đo nội dung.
- Số liệu DB VPS đo qua API công khai; không truy cập DB trực tiếp trong lần này.

## 4. Hệ quả cho 3 cấp học (tóm tắt — chi tiết ở 01/02/03)
- **Cử nhân:** không có đường tới kinh điển/nhân vật từ menu; ô tìm kiếm chỉ địa danh; không có bản dịch tiếng Việt để đọc; kết quả click 404.
- **Thạc sĩ:** không có toàn văn để đối chiếu; corpus chỉ snippet 4 bộ; không có export trích dẫn; provenance mới ở mức claim rời.
- **Tiến sĩ:** không API docs/version/CORS mở; không dataset export/DOI; contract lỗi không nhất quán; không tái lập được con số công bố.

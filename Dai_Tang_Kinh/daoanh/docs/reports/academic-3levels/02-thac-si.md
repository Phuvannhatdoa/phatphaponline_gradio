# Thạc Sĩ (Cao học) — Khảo sát tra cứu trên https://phatphaponline.org (2026-10-25)

> Người khảo sát: teammate `thac-si` (đội khảo sát chất lượng site Phật học). Môi trường: LIVE HTTPS, chỉ GET; kiểm chứng tầng HTTP/HTML/JSON + đọc code tĩnh `daoanh/app.py`, `daoanh/home.html`, `daoanh/places.html`. Không chạy browser/Playwright (máy này không chạy được) nên mọi kết luận hành vi DOM được đánh dấu **[SUY LUẬN TỪ CODE]**; các kết luận còn lại là **[ĐO ĐƯỢC]** bằng `requests` + trích response.
> Nhãn bằng chứng: `[ĐO ĐƯỢC: URL + HTTP + trích]` · `[SUY LUẬN TỪ CODE file:line]` · `[CHƯA KIỂM CHỨNG]`.
> Lưu ý: khảo sát chỉ dùng GET, không gọi endpoint admin ghi dữ liệu, không sửa DB/server.

---

## 0. Persona & nhu cầu tra cứu

**Persona:** Tăng Ni đang học Cao học (Thạc sĩ) tại Học viện Phật giáo, làm luận văn về Phật học Hán truyền (ví dụ: tư tưởng Thiền tông đời Đường–Tống, quan hệ sư–đệ trong *Cảnh Đức Truyền Đăng Lục*, đối chiếu *Tâm Kinh* Hán–Tạng, hoặc truy nguyên một địa danh/thiền sư trong ngữ liệu CBETA). Người dùng biết chữ Hán ở mức đọc kinh, quen dùng CBETA online, đang viết chương "Tổng quan tư liệu" và "Phụ lục trích dẫn" của luận văn.

**Nhu cầu tra cứu theo khung Thạc sĩ** ("truy được nguồn — đối chiếu được — hiểu sai lệch giữa truyền thống"):

1. Tìm một câu/cụm kinh văn (Hán và Hán-Việt) và **lấy được vị trí**: bộ kinh (CBETA sigla), quyển, trang, dòng/câu.
2. **Đối chiếu dị bản**: Hán ↔ Pali ↔ Tạng (Tohoku/84000) ↔ SAT, tối thiểu là chỉ ra bản tương ứng và vị trí tương ứng.
3. **Truy nguồn từng khẳng định** (provenance/evidence): nguồn nào, độ tin cậy, đã kiểm chứng chưa, span chính xác.
4. **Catalog/danh mục** theo triều đại, tác giả/dịch giả, bộ tạng; lọc và sắp xếp được.
5. **Cross-reference**: nhân vật ↔ kinh điển ↔ trang CBETA ↔ địa danh; từ một định danh đi ra toàn bộ ngữ liệu liên quan.
6. **Trích dẫn học thuật**: dựng được chú thích đủ trường (tên tác phẩm, tác giả/dịch giả, niên đại, sigla + page/line, URL) và export được (RIS/BibTeX/CSL-JSON/APA/Chicago).
7. **Hiểu sai lệch giữa truyền thống**: nơi công khai nêu rõ mâu thuẫn Bắc/Nam/Thiền tông, niên đại mâu thuẫn, khác biệt dị bản.
8. **Export phụ lục luận văn** (CSV/JSON/JSON-LD) và biết phạm vi/coverage của kho để mô tả phương pháp nghiên cứu.

---

## 1. Tóm tắt

**16 giới hạn:** **P0 = 5**, **P1 = 9**, **P2 = 2**.

Ba câu kết luận:

1. Về **tra cứu kinh văn** — chức năng cốt lõi của một học viên Cao học — site hiện chỉ tìm substring trong 5 bộ đã nhập (72.628 *đoạn trích dẫn chiếu nhân vật*, không phải toàn văn), không tìm được các câu kinh phổ biến như "色即是空" (0 kết quả) và không có vị trí trang/quyển để chú thích; trang chủ dẫn "/tra cứu kinh văn" nhưng ô tìm kiếm thực chất chỉ chọn địa danh.
2. Về **đối chiếu & nguồn** — API `compare` có tồn tại nhưng chỉ trả **link** tới 84000/SAT/SuttaCentral, không có text đối chiếu, không align theo đoạn; lớp provenance có cấu trúc nhưng **100% claims "unverified"**, và dữ liệu nhân vật có lỗi niên đại/sect rõ ràng (Huyền Trang sinh 2024, mất 1787; 69% nhân vật bị gán "Thiền Tông").
3. Về **tính trung thực số liệu** — trang chủ công bố 13.520 mục lục kinh trong khi API chỉ có 3.122; công bố 8.241 địa danh / 5.800+ tu sĩ trong khi API và trang Về dự án ghi 59.167 / 48.673; nhiều trang module (Đại Tạng, Nhân vật, Niên đại, Đồ thị) **404**, export JSON-LD/CSV hỏng. Với cấp Thạc sĩ, site hiện **chưa dùng được làm công cụ trích dẫn độc lập**, chỉ dùng được như bản đồ chỉ dẫn sau khi kiểm chứng lại bằng CBETA/DILA gốc.

---

## 2. Bảng tổng hợp

| ID | Giới hạn | Mức | Bằng chứng (URL/HTTP) | Trạng thái |
|---|---|---|---|---|
| THS-01 | "Tìm trong Đại Tạng" chỉ có 5 bộ đã nhập; không tìm được kinh văn phổ thông (色即是空 → 0) | P0 | `GET /daoanh/api/cbeta/corpus-search?q=色即是空` → 200, `result_count:0`, `coverage.texts_searchable:5` | Đang gặp (2026-10-25) |
| THS-02 | Ô tìm kiếm trang chủ không tra kinh văn/nhân vật: chỉ điều hướng sang `/daoanh/places?q=` và coi q là ID địa danh | P0 | `GET /daoanh/home.html` (home.html:1120), `/daoanh/places` (places.html:11602) | Đang gặp |
| THS-03 | Các module nghiên cứu 404: `/daoanh/tripitaka`, `/people`, `/timeline`, `/graph`, `/docs/`, `/dashboard/`; catalog chỉ có API, không UI | P0 | `GET` từng URL → 404 (162 B) | Đang gặp |
| THS-04 | Tìm kiếm bị cắt 30/50, `offset`/`page` bị bỏ qua; kết quả dồn một bộ do `ORDER BY sigla`; `result_count` không phải tổng | P0 | `corpus-search?q=金剛&limit=10[&offset=10|&page=2]` → 3 response giống hệt; `limit=1000` → 50 | Đang gặp |
| THS-05 | Không có locator: kết quả thiếu `page`/`juan`; reader trả `page:""`, `juan:""` → không dựng được chú thích CBETA | P0 | `GET /daoanh/api/cbeta/person-passage/25207` → 200 `page:"" juan:"" passage_source:"context_snippet"` | Đang gặp |
| THS-06 | Không có toàn văn: chỉ snippet; `coverage.complete_text:false`; browse 492 "trang" snippet cho 22.275 mentions | P1 | `GET /daoanh/api/cbeta/text/T51n2076/browse` → 200, `coverage.note:"Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn."` | Đang gặp |
| THS-07 | "Đối Chiếu Tam Tạng" chỉ trả link (text rỗng), phủ crossref mỏng, bug chuẩn hóa sigla X77n1524→"T771524" (0 bản) | P1 | `GET /daoanh/api/cbeta/T0251/compare?lang=vi` → 200, 4 versions, `text:""`; `X77n1524` → `total:0` | Đang gặp |
| THS-08 | Provenance chưa dùng được: 38/38 và 17/17 claims `unverified`, `verified_ratio:0.0`, `release_status:"review_required"`; `unified` claims `[]` | P1 | `GET /daoanh/api/evidence/PL000000023255`; `/daoanh/api/evidence/A000294`; `/daoanh/api/entity/A000294/unified` | Đang gặp |
| THS-09 | Dữ liệu nhân vật sai: A000294 (Huyền Trang) sinh 2024/mất 1787; A020301 mất trước sinh (1560/511); 25/30 hồ sơ mẫu thiếu năm; 69% gán "Thiền Tông" | P1 | `GET /daoanh/api/person/A000294/profile` → 200; `/daoanh/api/persons/browse?sect=Thiền Tông` → total 33.610 | Đang gặp |
| THS-10 | Số liệu công bố mâu thuẫn: 13.520 mục lục vs API 3.122; 8.241 địa danh vs API 59.167; 5.800+ tu sĩ vs 48.673 | P1 | `GET /daoanh/` (home.html:1005–1015) vs `GET /daoanh/api/cbeta/catalog` (total 3122), `/daoanh/api/dila/places` (59167), `/daoanh/api/dila/persons` (48673) | Đang gặp |
| THS-11 | Export/trích dẫn hỏng/thiếu: JSON-LD địa danh trả `ok:false` (HTTP 200), CSV nhân vật 500, catalog bỏ qua `format`, BibTeX/CSL thiếu trường, không RIS/APA | P1 | `GET /daoanh/api/places/PL000000023255/export?format=jsonld` → 200 `{"error":"no such column: latitude"}`; `/daoanh/api/dila/persons?format=csv` → 500 | Đang gặp |
| THS-12 | Catalog thiếu metadata trích dẫn: 200/200 bản ghi mẫu `cbeta_ref:null`; 18% dynasty "Chưa rõ"; 8,5% translator "Không rõ người"; có dynasty rác; không lọc tác giả/sắp xếp | P1 | `GET /daoanh/api/cbeta/catalog?limit=100&page=1..2` → 200; `?format=csv` trả JSON | Đang gặp |
| THS-13 | Cross-reference/định danh không nhất quán: 1 WORK nằm trong `monks`; 2 hồ sơ 玄奘; `PL052464` trả bản ghi khác (PL050713) | P1 | `GET /daoanh/api/search?q=慧能` → `monks:[{id:"A029593",name_vi:"Truyền Pháp Chánh Tông Ký"}]`; `GET /daoanh/api/places/PL052464` → `dila_id:"PL050713"` | Đang gặp |
| THS-14 | Mâu thuẫn truyền thống/niên đại không được công bố thành nơi tra cứu: 100 conflicts chỉ nằm ở JSON, không UI; không có so sánh Bắc/Nam/Thiền tông | P1 | `GET /api/conflicts` → 200, 100 conflicts `teacher_set`/`student_set`; `/daoanh/lineage?id=A000294` chỉ có thầy/trò | Đang gặp |
| THS-15 | Tìm kiếm chỉ substring Hán chính xác; không hỗ trợ tiếng Việt/Hán-Việt/Pali/Sanskrit, không fuzzy, không lọc theo kinh/triều đại/dịch giả | P2 | `corpus-search?q=sắc tức thị không` → 0; `q=色` → 400 `min_length:2`; `catalog?translator=` bị bỏ qua | Đang gặp |
| THS-16 | Coverage/pagination không minh bạch: browse `total`=492 (unique_pages) ≠ 22.275 mentions; nhận `limit=500`; không cursor; chỉ 5 bộ; không có tài liệu API công khai | P2 | `GET /daoanh/api/cbeta/text/T51n2076/browse?limit=500` → 200 (110 KB); `/daoanh/opendata` chỉ nêu 2 endpoint | Đang gặp |

---

## 3. Chi tiết từng giới hạn

### THS-01 — Full-text search "Đại Tạng" thực chất chỉ là 5 bộ trích dẫn tiểu sử

**Kỳ vọng của học viên Cao học:** Gõ một câu kinh (Hán hoặc Hán-Việt) và nhận được đoạn văn trong *Đại Chính Tạng*, kèm vị trí quyển/trang/dòng để chép vào chú thích luận văn.

**Cách tái lập:**
1. `GET https://phatphaponline.org/daoanh/api/cbeta/corpus-search?q=%E8%89%B2%E5%8D%B3%E6%98%AF%E7%A9%BA` (色即是空).
2. `GET .../corpus-search?q=s%E1%BA%AFc+t%E1%BB%A9c+th%E1%BB%8B+kh%C3%B4ng` (sắc tức thị không).
3. `GET .../corpus-search?q=%E9%87%91%E5%89%9B` (金剛) và `GET .../daoanh/api/cbeta/texts`.

**Kết quả thực tế:**
- 色即是空 → HTTP 200, trích: `{"coverage":{"catalog_total":3122,"passages_searchable":72628,"scope":"imported_corpus","texts_searchable":5},"limit":30,"ok":true,"query":"色即是空","result_count":0,"results":[]}`.
- "sắc tức thị không" → `result_count:0` (không có tìm Hán-Việt).
- `/daoanh/api/cbeta/texts` trả đúng 5 bộ, phần lớn là **truyện ký tiểu sử**: T51n2076 *Cảnh Đức Truyền Đăng Lục*, T50n2060 *Tục Cao Tăng Truyện*, T50n2061 *Tống Cao Tăng Truyện*, X77n1524 *Vô Lượng Thọ Kinh Ưu Ba Đề Xá*, T50n2062 *Đại Minh Cao Tăng Truyện*.
- Vì sao 0 kết quả: `[SUY LUẬN TỪ CODE app.py:14451-14503]` — search là `WHERE pm.context_snippet LIKE '%q%'` trên bảng `cbeta_person_mentions`, tức chỉ tìm trong **đoạn trích quanh tên nhân vật**. `Tâm Kinh` (T08n0251) chưa được import nên câu "色即是空" không tồn tại trong index.

**Phân loại:** thiếu tính năng + sai lệch số liệu (nhãn "Tìm trong Đại Tạng" ngụ ý toàn tạng).

**Ảnh hưởng tới cấp Thạc sĩ:** Chặn hoàn toàn bước "tìm câu kinh — lấy vị trí". Học viên vẫn phải mở CBETA.org để tìm, sau đó quay lại site chỉ để tra nhân vật/địa danh. Không thể dùng site làm nguồn chính cho chương "Tổng quan tư liệu".

**Yêu cầu cho đội Planning (AC đo được):**
- AC1: `GET /daoanh/api/cbeta/corpus-search?q=色即是空` trả ≥1 kết quả thuộc bộ chứa câu này (T08n0251) hoặc trả lỗi `coverage_insufficient` kèm danh sách bộ đã import; **không được** trả 200 + 0 kết quả mà không giải thích.
- AC2: response có trường `searched_scope.{texts_included, texts_total_catalog}`; UI hiển thị rõ "đang tìm trong N/M bộ".
- AC3: ít nhất 20 bộ kinh Đại Chính Tạng phổ thông (T0251, T0235, T0475, T0676…) có index full-text, hoặc công bố lộ trình rõ ràng.

**Ưu tiên:** P0.

---

### THS-02 — Ô tìm kiếm trang chủ dẫn sai chỗ: không tra được kinh văn hay nhân vật

**Kỳ vọng:** Ô "Tìm kinh văn, tăng nhân, địa danh..." trên trang chủ trả kết quả tổng hợp (như `/daoanh/api/search` vẫn có), hoặc ít nhất mở trang tìm kiếm phù hợp.

**Cách tái lập:** mở `https://phatphaponline.org/daoanh/`, nhập `Huyền Trang` hoặc `Tâm Kinh`, bấm Tìm; đọc `home.html:1120` và `places.html:11602`.

**Kết quả thực tế:**
- `[SUY LUẬN TỪ CODE home.html:1120]`: `function handleSearch(e){ ... if (q.includes('Thiếu Lâm') || q.includes('少林')) { showPlaceDemo(); return; } window.location.href = '/daoanh/places?q=' + encodeURIComponent(q); }` → **mọi truy vấn** đều bị đẩy sang trang địa đồ; từ khóa "Thiếu Lâm/少林" thì bật **panel demo tĩnh** (dữ liệu hardcode: toạ độ 34.5885/112.9343, "Thành lập 495 AD", "Thiền Tông").
- `[SUY LUẬN TỪ CODE places.html:11602]`: `const selectParam = up.get('select') || up.get('q'); ... selectItem(selectParam, ...)` → `q` được dùng như **ID địa danh**, không phải từ khóa tìm text/nhân vật. `GET /daoanh/places?q=Huyền%20Trang` → 200 nhưng không có `selectItem` nào khớp ID này.
- Trong khi đó `GET /daoanh/api/search?q=玄奘` → 200 có `monks/works/places` thật (2 monks, 10 works, 3 places) — **API tổng hợp tồn tại nhưng UI không gọi**.

**Phân loại:** thiếu tính năng (UI) + lỗi UI (điều hướng).

**Ảnh hưởng:** Học viên mới dùng site gõ "Tâm Kinh" → bị đưa sang bản đồ, thấy trống, kết luận site không có kinh văn. Mất niềm tin ngay bước đầu; "demo Thiếu Lâm" gây cảm giác dữ liệu mẫu/không thật.

**Yêu cầu cho Planning (AC):**
- AC1: `handleSearch` gọi `/daoanh/api/search?q=` và hiển thị 3 nhóm (Kinh/Nhân vật/Địa danh) với số lượng; không được route sang `/places` khi q không phải ID.
- AC2: Xóa panel demo hardcode hoặc gắn nhãn "ví dụ" rõ ràng; nút "Thiếu Lâm Tự" phải mở đúng `select=PL000000023255` (đã kiểm: API trả 200).
- AC3: Kiểm thử tự động: gõ "Huyền Trang" phải ra ≥1 nhân vật (A000294/A009306), gõ "Tâm Kinh" phải ra ≥1 work.

**Ưu tiên:** P0.

---

### THS-03 — Module nghiên cứu chính 404; catalog Đại Tạng không có giao diện

**Kỳ vọng:** Từ trang chủ vào được "Đại Tạng", "Nhân vật", "Niên đại", "Đồ thị", "Tài liệu" để tra catalog/lọc/sắp xếp như mô tả ở trang Về dự án ("Tìm kiếm kinh điển theo tên, tác giả, triều đại, tông phái").

**Cách tái lập:** `GET` lần lượt các URL; xem link ở `home.html` module cards.

**Kết quả thực tế:** tất cả trả **404** (body 162 B): `/daoanh/tripitaka`, `/daoanh/people`, `/daoanh/timeline`, `/daoanh/graph`, `/docs/`, `/dashboard/`. Các module card trên home trỏ thẳng vào `tripitaka` / `people` (`home.html:1030-1040`). `/daoanh/login.html` trả **502**. Đồng thời kho HTML của app **không có** file `tripitaka.html`/`people.html`/`timeline.html` (kiểm tra thư mục `daoanh/*.html`). Catalog 3.122 bản ghi chỉ tiếp cận được qua API, không có màn hình browse/filter/detail.

**Phân loại:** lỗi UI/thiếu tính năng (deployment/route thiếu).

**Ảnh hưởng:** Không thể làm bước "khảo sát danh mục theo triều đại/tác giả" — bước bắt buộc của luận văn Thạc sĩ. Thậm chí trang "Về dự án" quảng cáo năng lực này nên học viên sẽ mất thời gian thử.

**Yêu cầu cho Planning (AC):**
- AC1: 4 URL trên trả 200 (hoặc 301 tới route thay thế) — đo bằng smoke test.
- AC2: Trang Đại Tạng có bảng catalog phân trang, lọc triều đại/dịch giả/bộ tạng, mỗi dòng click mở được chi tiết.
- AC3: Gỡ/ẩn link module khi chưa có trang (không để link chết trên home).

**Ưu tiên:** P0.

---

### THS-04 — Tìm kiếm bị cắt 30/50, không phân trang, kết quả dồn một bộ

**Kỳ vọng:** Có tổng số hits thực, phân trang/cursor để duyệt hết, và kết quả trải đều các bộ liên quan.

**Cách tái lập:**
1. `GET /daoanh/api/cbeta/corpus-search?q=金剛&limit=10`
2. Cùng URL + `&offset=10`; cùng URL + `&page=2`.
3. `GET ...&q=金剛&limit=1000`; `GET ...&q=傳燈&limit=50`.

**Kết quả thực tế:**
- 3 response (limit=10, offset=10, page=2) **giống hệt nhau từng byte** → `offset`/`page` không được đọc; `[SUY LUẬN TỪ CODE app.py:14469-14503]` chỉ có `LIMIT ?`, không `OFFSET`.
- `limit=1000` → `limit:50, result_count:50` (bị cap 50, `app.py:14469`).
- 金剛: 50 kết quả **100% T50n2060** (dù T51n2076 cũng có 22.275 mentions); 傳燈: 50 kết quả **100% T50n2060**. Nguyên nhân `[CODE app.py:14501]`: `ORDER BY pm.cbeta_text_sigla ASC, pm.page ASC, pm.id ASC` + `LIMIT` → chỉ thấy bộ có sigla nhỏ nhất.
- `result_count` = `len(results)` (`app.py:14522`), **không phải** tổng số matches; UI ghi "Tìm thấy 30 kết quả (giới hạn 30)" trong khi số thật có thể hàng nghìn.

**Phân loại:** sai lệch số liệu + thiếu tính năng (pagination).

**Ảnh hưởng:** Học viên không thể biết mình đã "vét" hết ngữ liệu chưa — điều kiện bắt buộc để nói "khảo sát toàn bộ". Kết quả dồn 1 bộ tạo ấn tượng sai về phân bố tư liệu (ví dụ tưởng 金剛 chỉ xuất hiện trong *Tục Cao Tăng Truyện*).

**Yêu cầu cho Planning (AC):**
- AC1: Thêm `total_matches` (COUNT) + `offset`/cursor hoạt động; test: offset=0 và offset=30 cho 2 tập kết quả rời nhau, không trùng mention_id.
- AC2: Bỏ cap cứng 50 hoặc phân trang tới hết (`limit` tối đa ≥200 + cursor).
- AC3: Kết quả trải đều bộ: khi q=金剛, top 50 phải có ≥3 sigla khác nhau, hoặc có facet đếm theo bộ.

**Ưu tiên:** P0.

---

### THS-05 — Không có locator (quyển/trang/dòng) trong kết quả và reader

**Kỳ vọng:** Mỗi kết quả có `sigla`, `juan`, `page` (CBETA page/line) để dựng chú thích "CBETA T50n2060_p0457c16"; reader mở đúng vị trí.

**Cách tái lập:**
1. `GET /daoanh/api/cbeta/corpus-search?q=金剛&limit=50` → xem `page`, `juan` từng result.
2. `GET /daoanh/api/cbeta/person-passage/25207` (reader từ kết quả search).
3. So sánh với `GET /daoanh/api/places/PL000000023255/cbeta` (nơi ref_code đầy đủ).

**Kết quả thực tế:**
- 金剛 limit=50: `page` có ở **17/50**, `juan` có ở **0/50**; limit=30: `page` **0/30**. Ví dụ một result: `{"sigla":"T50n2060","page":"","juan":"","reader_ref":25207}`.
- Reader `/daoanh/api/cbeta/person-passage/25207` → `{"page":"","juan":"","passage_source":"context_snippet","ref_code":""}`; không có locator, `ref_code` rỗng.
- Ngược lại, endpoint địa danh trả locator tốt: `"passages":[{"ref_code":"T50n2060_p0457c16","sigla":"T50n2060"}]` → cho thấy hạ tầng có, nhưng **search/reader không dùng**.

**Phân loại:** lỗi dữ liệu + lỗi API (thiếu trường/không join).

**Ảnh hưởng:** Không thể chép chú thích chuẩn; mọi trích dẫn phải tự dò lại trong CBETA. Vi phạm trực tiếp yêu cầu "truy được nguồn" của khung Thạc sĩ.

**Yêu cầu cho Planning (AC):**
- AC1: 100% kết quả search trả `page` (dạng `0457c16`) hoặc cờ `locator_missing:true`; nếu thiếu phải ghi rõ lý do.
- AC2: Reader trả `ref_code` dạng `T{Số}n{Số}_p{page}{line}` khớp regex `^T\d+n\d+_p\d{4}[abc]\d{2}$` cho mọi mention có page.
- AC3: Test: chọn 20 mention ngẫu nhiên, ít nhất 20/20 mở được CBETA reader với đúng page.

**Ưu tiên:** P0.

---

### THS-06 — Không có toàn văn: chỉ snippet quanh tên nhân vật

**Kỳ vọng:** Đọc được ít nhất bộ kinh đã "có thể đọc" (5 bộ), hoặc nếu chỉ có snippet thì phải nói rõ ngay từ UI và trong kết quả.

**Cách tái lập:** `GET /daoanh/api/cbeta/text/T51n2076/browse?offset=20&limit=5`; `GET /daoanh/api/cbeta/texts`; đọc `/daoanh/opendata`.

**Kết quả thực tế:**
- Browse trả `coverage:{"complete_text":false,"granularity":"context_snippet","note":"Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn.","total_mentions":22275,"unique_pages":492}`.
- Mỗi "trang" browse là **snippet** (khoảng 150-250 chữ) ghép với `page` (ví dụ `0196c`), không phải văn bản liên tục; không thể đọc trọn một quyển/đoạn.
- `/daoanh/opendata` ghi rõ phạm vi CBETA: "Chỉ mục tiêu đề, tác giả, triều đại".

**Phân loại:** thiếu tính năng (dữ liệu) + thông điệp chưa nhất quán (home nói "tra cứu kinh văn").

**Ảnh hưởng:** Không đọc được ngữ cảnh đầy đủ để phân tích giáo lý, chỉ thấy câu rời. Học viên phải mở CBETA gốc cho mọi luận điểm — site không thay thế được.

**Yêu cầu cho Planning (AC):**
- AC1: Hoặc bổ sung toàn văn cho N bộ ưu tiên (đơn vị: số bộ × số quyển, có license), hoặc đổi nhãn UI thành "Tra đoạn trích dẫn" và hiển thị banner coverage ở mọi màn hình kết quả.
- AC2: Trang browse có nút "Mở toàn văn tại CBETA" trỏ đúng `https://cbetaonline.dila.edu.tw/zh/{ref_code}` (kiểm bằng 1 mẫu ref_code).

**Ưu tiên:** P1.

---

### THS-07 — "Đối Chiếu Tam Tạng" chỉ là danh sách link; crossref mỏng và có bug chuẩn hóa sigla

**Kỳ vọng:** Với một bộ kinh, xem được bản Hán — Pali — Tạng (Tohoku/84000) — SAT cạnh nhau, ít nhất theo chương/đoạn để thấy khác biệt.

**Cách tái lập:**
1. `GET /daoanh/api/cbeta/T0251/compare?lang=vi`
2. `GET /daoanh/api/cbeta/T0099/compare?lang=vi` (và T0026, T0125, T0001)
3. `GET /daoanh/api/cbeta/X77n1524/compare?lang=vi`
4. Mở `/daoanh/places?select=PL000000023255` → tab Giáo Lý (UI `renderGiaolyTab`, places.html:11014).

**Kết quả thực tế:**
- T0251: 200, versions `[tang, sat, parallels, pali]` **nhưng mọi `text:""`** — chỉ có `link_source` (84000 `toh21.html`, SAT URL, SuttaCentral) và note. Không có bản Hán tại chỗ (`cbeta_content_index` chưa import T0251). Đáng chú ý: **response không ổn định** — lần gọi đầu tiên trả `total:3` (thiếu `parallels`), 3 lần gọi sau trả `total:4` (có `parallels`), do `parallels` phụ thuộc live-call/cache DharmaNexus (`app.py:19926-19952`); học viên chạy lại có thể nhận kết quả khác nhau.
- T0099/T0026/T0125/T0001: chỉ **1 version SAT** — không có Tạng, không có Pali, không có Hán. Nghĩa là "Tam Tạng" hầu như trống với các A-hàm.
- X77n1524 → `sitla:"T771524"`, `total:0`; `[SUY LUẬN TỪ CODE app.py:19844, _t52_normalize_sigla]` chuẩn hóa sai sigla bộ X → mất chữ "X", ra "T771524" → tra crossref không thấy.
- Note do API trả về gây hiểu nhầm: `"T34 Phase A (fake data cleanup) chưa áp dụng: các crossref hiển thị đều là dữ liệu thật đã xác minh."` — câu này mâu thuẫn nội bộ ("chưa áp dụng" + "đã xác minh") và không thể kiểm chứng từ dữ liệu.
- UI đối chiếu **chôn trong tab Giáo Lý của trang địa danh**, phải gõ tay mã CBETA; gợi ý lấy từ `/daoanh/api/places/<id>/pali` (Thiếu Lâm trả `refs:[]`), nên hầu như không có gợi ý.

**Phân loại:** thiếu tính năng + lỗi API (chuẩn hóa sigla) + thông điệp sai.

**Ảnh hưởng:** Học viên không thể "đối chiếu được" ở mức văn bản; chỉ nhận được link sang nguồn khác. Nếu tự tin vào nhãn "đã xác minh" sẽ dễ trích sai.

**Yêu cầu cho Planning (AC):**
- AC1: `compare` trả text thật (hoặc `text_excerpt`) cho ≥2 truyền thống với ít nhất 10 bộ phổ thông; nếu không, đổi nhãn thành "Liên kết nguồn đối chiếu" và bỏ chữ "Đối chiếu Tam Tạng".
- AC2: Sửa `_t52_normalize_sigla`: `X77n1524` → compare phải trả đúng sigla X77n1524 (test hồi quy).
- AC3: Có truy vấn đối chiếu từ kết quả search/catalog (không chỉ từ tab địa danh), không cần gõ tay sigla.
- AC4: Xóa/viết lại câu note gây hiểu nhầm; thêm `evidence_status` cho từng crossref.

**Ưu tiên:** P1.

---

### THS-08 — Provenance: 100% claim "unverified", `unified` rỗng, claim thiếu span

**Kỳ vọng:** Mỗi khẳng định (nhân vật là thầy của ai, địa danh ở đâu, thành lập năm nào) có nguồn, confidence, trạng thái kiểm chứng và **span chính xác** (trích đúng câu trong nguồn).

**Cách tái lập:** `GET /daoanh/api/evidence/PL000000023255`, `GET /daoanh/api/evidence/A000294`, `GET /daoanh/api/entity/A000294/unified`, `GET /daoanh/api/entity/A000660/unified`.

**Kết quả thực tế:**
- Place evidence: 38 claims, `verification:{"unverified":38}`, `verification_summary:{"verified_ratio":0.0,"release_status":"review_required","dominant_status":"unverified"}`; 3/38 claim không có `source_reference`.
- Person evidence: 17 claims, **17/17 unverified**, `verified_ratio:0.0`; toàn bộ là `NETWORK_EVIDENCE` từ MARCUS.
- `unified` A000294: `claims:[]`, `claims_count:0`, `conflicts:[]`, `canonical_name_vi:""`; A000660 tương tự. Trường `sources.cbeta.active:false, refs:[]`.
- Claim **không có span**: ví dụ claim `ADMIN_UNIT` có `source_reference:null`; chỉ **events** mới có `exact_span` (tốt): `"exact_span":"少室寺 魏太和 (477年建)"`, `source_record`.

**Phân loại:** thiếu tính năng (chưa review/không span) + thông điệp (nhãn "đã kiểm chứng" ở opendata: "dữ liệu … đã được kiểm chứng").

**Ảnh hưởng:** Học viên không thể viết "theo Đạo Ảnh, X là…"; mọi claim phải quay về DILA/MARCUS gốc. Lớp `unified` — nơi lẽ ra để tổng hợp — hiện rỗng, không dùng được.

**Yêu cầu cho Planning (AC):**
- AC1: Mỗi claim trả `evidence_span` (text + start/end hoặc page/line) hoặc `span_status:"missing"`; thống kê `% claim có span` trên dashboard.
- AC2: Trang công khai hiển thị rõ `verified_ratio` và cảnh báo "chưa kiểm chứng" ở cấp subject (đã có trong JSON, cần đưa lên UI nổi bật).
- AC3: `unified` trả claims khi có dữ liệu (test A000294 phải ≥1 claim hoặc `sources_active` giải thích lý do rỗng).

**Ưu tiên:** P1.

---

### THS-09 — Dữ liệu nhân vật sai niên đại/sect; phần lớn hồ sơ thiếu năm

**Kỳ vọng:** Niên đại nhân vật (sinh/mất), triều đại, tông phái phải đúng hoặc để trống + đánh dấu "không rõ". Với Huyền Trang (602–664, Pháp Tướng tông), không được hiển thị 2024/1787 hay "Thiền Tông".

**Cách tái lập:** `GET /daoanh/api/person/A000294/profile`, `/daoanh/api/person/A000660/profile`, `/daoanh/api/person/A000001/profile`; lấy 30 hồ sơ từ `/daoanh/api/persons/browse?limit=50` rồi mở từng profile.

**Kết quả thực tế:**
- A000294 (Huyền Trang): `{"birth_year":2024,"death_year":1787,"sect":"Thiền Tông","dynasty":"唐"}` — trong khi bio ghi "大業八年（612）… 貞觀十九年 …" và các số 2024/1787 chính là số hiệu trong chuỗi trích dẫn "（佛光：2024；佛百：1787.1；疑年錄：99…）" → **lấy số tham chiếu làm năm sinh/mất**.
- A020301 (安樂樹神): `birth_year:1560, death_year:511` — mất trước sinh 1049 năm. A043915: 1198/940 tương tự.
- Mẫu 30 profile: **25/30 thiếu cả năm sinh và năm mất** (null).
- `GET /daoanh/api/persons/browse?sect=Thiền Tông` → **total 33.610 / 48.673 (69%)**; trong đó Huyền Trang (Pháp Tướng) và A000660 (Minh Dục, "pháp tướng tông tăng") đều bị gán "Thiền Tông".
- Nguồn: `[SUY LUẬN TỪ CODE app.py:8264-8276]` profile đọc thẳng cột `people.birth_year/death_year/sect` → lỗi nằm ở dữ liệu import, không phải hiển thị.

**Phân loại:** lỗi dữ liệu (nguy hiểm: số liệu trông "xác thực").

**Ảnh hưởng:** Nếu học viên tin và trích "Huyền Trang (2024–1787)" sẽ bị hội đồng loại ngay. Triều đại/sect là trường tra cứu chính của luận văn nên sai ở đây phá toàn bộ chương "bối cảnh nhân vật".

**Yêu cầu cho Planning (AC):**
- AC1: Sửa nguồn sinh `birth_year/death_year`: không parse số trong chú thích; nếu không xác định → `null` + `date_status:"unknown"`. Test: A000294 phải là `null` hoặc 602/664; A020301 không được `death_year < birth_year`.
- AC2: `sect` chỉ điền khi nguồn có trường tông phái thật; ngược lại `""` + `sect_status:"not_provided"`. Tỉ lệ "Thiền Tông" không được vượt quá tỉ lệ có nguồn (kiểm bằng 100 mẫu ngẫu nhiên).
- AC3: API trả `data_quality:{birth_death_null_ratio}` để học viên biết độ phủ.

**Ưu tiên:** P1.

---

### THS-10 — Số liệu công bố trên site mâu thuẫn nhau (13.520 / 8.241 / 5.800+)

**Kỳ vọng:** Số liệu trên trang chủ, Về dự án, Open Data và API phải thống nhất, và phải tương ứng dữ liệu tra được.

**Cách tái lập:** `GET /daoanh/`; `GET /daoanh/about`; `GET /daoanh/opendata`; `GET /daoanh/api/cbeta/catalog`; `/daoanh/api/dila/places?limit=1`; `/daoanh/api/dila/persons?limit=1`.

**Kết quả thực tế:**
- Home (`home.html:1005-1015`): "8,241 Địa danh · 13,520 Mục lục kinh · 5,800+ Tu sĩ DILA".
- API: catalog `total:3122`; DILA places `total:59167`; DILA persons `total:48673`. Trang Về dự án ghi 59.167 địa danh, 48.673 tăng nhân, 13.520 mục kinh; trang Open Data lại ghi 8.241 địa danh / 5.800+ tu sĩ.
- Như vậy **13.520 vs 3.122** (thiếu 10.398 = 77%), **8.241 vs 59.167** (thiếu 86%), **5.800 vs 48.673** (thiếu 88%).

**Phân loại:** sai lệch số liệu (marketing vs dữ liệu).

**Ảnh hưởng:** Trong luận văn, mô tả "kho dữ liệu 13.520 bộ" sẽ sai; học viên không biết coverage thật để viết mục "phương pháp & nguồn". Đây là lỗi trung thực học thuật, không chỉ lỗi UI.

**Yêu cầu cho Planning (AC):**
- AC1: Số liệu home/about/opendata lấy động từ API (không hardcode) và bằng đúng `total` của endpoint tương ứng; test so khớp 3 cặp số.
- AC2: Ghi rõ "đã index" vs "có metadata": ví dụ "3.122 bộ có metadata tra cứu / 13.520 bộ trong nguồn CBETA" nếu đó là sự thật.
- AC3: Thêm ngày cập nhật số liệu.

**Ưu tiên:** P1.

---

### THS-11 — Export/trích dẫn hỏng hoặc thiếu trường

**Kỳ vọng:** Export được bản ghi/đoạn văn ra JSON-LD/CSL-JSON/BibTeX/CSV đủ trường để dán vào Zotero/Word; chú thích có tác giả, tên, niên đại, sigla+page, URL.

**Cách tái lập:**
1. `GET /daoanh/api/places/PL000000023255/export?format=jsonld`
2. `GET /daoanh/api/dila/persons?format=csv` và `/daoanh/api/dila/places?format=csv`
3. `GET /daoanh/api/public/export/citation?entity_id=A000294&format=csl-json` (và `format=bibtex`, `format=ris`)
4. `GET /daoanh/api/cbeta/catalog?format=csv`
5. Đọc UI: nút "Xuất trích dẫn" (`places.html:5077 dtCopyCite`).

**Kết quả thực tế:**
- JSON-LD địa danh: **HTTP 200** nhưng body `{"ok":false,"error":"no such column: latitude"}` — link "↗ Export JSON-LD" trên UI trỏ vào endpoint hỏng (`places.html:11489`).
- `/daoanh/api/dila/persons?format=csv` → **HTTP 500** `{"error":"dict contains fields not in fieldnames: 'hv'"}`; `/daoanh/api/dila/places?format=csv` → 200 (`dila_places.csv`, 6.696 B) — không đối xứng.
- `/daoanh/api/cbeta/catalog?format=csv` → vẫn trả **JSON** (format bị bỏ qua).
- CSL-JSON: `{"title":"玉華法師","type":"document","publisher":"Phật Pháp Online…"}` — thiếu `author`, `issued`, `container-title`, `URL`, `page`. BibTeX: `@misc{A000294, title={玉華法師}, howpublished={...}}` — thiếu author/year/url. `format=ris` → 400.
- UI `dtCopyCite`: nút "CBETA URL" chỉ copy `ref_code` (không phải URL); "BibTeX" tạo `@incollection{c, note={CBETA c}}` không title/author; "Chicago" chỉ nối `c + '. In Taishō Shinshū Daizōkyō.'`.

**Phân loại:** lỗi API + thiếu tính năng (định dạng học thuật).

**Ảnh hưởng:** Không thể xuất phụ lục/ bibliography từ site; sinh viên phải gõ tay. Nút export hỏng còn tệ hơn không có (mất thời gian, tạo niềm tin sai).

**Yêu cầu cho Planning (AC):**
- AC1: `/places/<id>/export?format=jsonld` trả 200 `ok:true` với JSON-LD hợp lệ (có `@context`, `@type`, `name`, `geo`, `identifier`); JSON-LD validate bằng jsonld.js hoặc schema.org validator.
- AC2: `/daoanh/api/dila/persons?format=csv` trả 200 + header `text/csv`; test 2 endpoint CSV đối xứng.
- AC3: CSL-JSON đủ trường `author` (tên Hán + phiên âm), `title`, `issued` (nếu có), `URL`; BibTeX có `author`, `title`, `year`, `url`; thêm `format=ris` và `format=apa`.
- AC4: Nút "CBETA URL" copy URL thật `https://cbetaonline.dila.edu.tw/zh/{ref_code}`; test clipboard content bằng regex URL.

**Ưu tiên:** P1.

---

### THS-12 — Catalog thiếu metadata trích dẫn, filter/sort hạn chế

**Kỳ vọng:** Catalog cho lọc theo triều đại/tác giả/dịch giả/bộ tạng, sắp xếp, và mỗi bản ghi đủ trường (sigla, title, translator, dynasty, CBETA ref) để trích dẫn.

**Cách tái lập:** `GET /daoanh/api/cbeta/catalog?limit=100&page=1` và `page=2`; thử `?dynasty=Đường` vs `dynasty=唐`; `?translator=`; `?sort=title`; `?format=csv`.

**Kết quả thực tế:**
- Mẫu 200 bản ghi: **`cbeta_ref:null` 200/200**; `dynasty_vi=="Chưa rõ"` 36/200 (18%); `translator_vi=="Không rõ người"` 17/200 (8,5%); `sh_number:null` 11/200; có bản ghi dynasty rác: "Q. 16, Tr. 209, Sh. 658".
- Không có trường `sigla`; `q_number`/`sh_number` thường null → không dựng được mã CBETA từ catalog.
- `?dynasty=Đường` → `total:0` (lọc exact-match cột Việt), phải dùng `dynasty=唐`; `?translator=` **bị bỏ qua** (trả 3.122); `?sort=title` bị bỏ qua; sort cố định `CAST(sh_number AS INTEGER)` (`app.py:9381`) trong khi 11/200 bản ghi mẫu có `sh_number` NULL.
- `limit` tối đa 100, 157 trang; không có `has_next`/cursor (chỉ page/pages).

**Phân loại:** lỗi dữ liệu + thiếu tính năng.

**Ảnh hưởng:** Không làm được "khảo sát danh mục theo triều đại/tác giả" (S4) ở mức luận văn; 18% bản ghi không có triều đại và 100% không có CBETA ref → không trích dẫn được từ catalog.

**Yêu cầu cho Planning (AC):**
- AC1: Catalog trả `sigla` và `cbeta_ref` cho ≥95% bản ghi; test 100 mẫu.
- AC2: Thêm filter `dynasty` (chấp nhận cả Hán và Việt), `translator`, `series`, `q`; thêm `sort=title|dynasty|sh_number`.
- AC3: Làm sạch `dynasty_vi` (không chứa "Q. … Tr. …") — test regex `^[^\dQ]*$` trên 100% bản ghi.

**Ưu tiên:** P1.

---

### THS-13 — Cross-reference & định danh không nhất quán (work lọt vào monks, trùng hồ sơ, ID địa danh trỏ sai bản ghi)

**Kỳ vọng:** Một kết quả tìm kiếm phải đúng loại thực thể; không có hồ sơ trùng; một ID địa danh luôn trỏ về một bản ghi duy nhất.

**Cách tái lập:** `GET /daoanh/api/search?q=慧能`, `q=玄奘`, `q=少林`; `GET /daoanh/api/places/PL000000052464` và `GET /daoanh/api/places/PL052464`; `GET /daoanh/api/person/A000294/profile`.

**Kết quả thực tế:**
- `?q=慧能` → `monks:[{"id":"A029593","name_vi":"Truyền Pháp Chánh Tông Ký","name_zh":"慧能"}]`: một **tác phẩm** (truyền pháp chánh tông ký) bị trả trong `monks` với ID person.
- `?q=玄奘` → 2 monks: A000294 và A009306 (trùng hồ sơ nhân vật cùng tên/zh).
- Địa danh: search trả `PL000000052464` (玄奘寺, Huyền Trang Tháp Tự, 南投) nhưng `GET /daoanh/api/places/PL052464` trả **bản ghi khác**: `dila_id:"PL050713"`, `name_zh:"慈恩精舍"`, `district:"台南縣-龍崎"` → short-ID không duy nhất/an toàn.
- A000294: `mentions.text_count:1` nhưng `texts` có **4 CBETA refs** (T50n2061_p0815a10…) — đếm không khớp; refs lineage là chuỗi tự do `"（T50n2061_p0727a06；佛光：4982）"` không tách được page/line.
- URL chi tiết địa danh không ổn định: `GET /daoanh/places/PL000000023255` → **404**; chỉ mở được qua `/daoanh/places?select=PL000000023255`. Không có URL canonical để chú thích/share trong luận văn.

**Phân loại:** lỗi dữ liệu + lỗi API.

**Ảnh hưởng:** Tra "Huyền Trang" ra 2 hồ sơ, tra 玄奘寺 ra 2 toạ độ/2 chùa khác nhau; trích dẫn nhầm bản ghi là rủi ro trực tiếp. Cross-reference (S5) không đáng tin.

**Yêu cầu cho Planning (AC):**
- AC1: `/daoanh/api/search` phân loại đúng: item trả `kind` ∈ {person,work,place}; test 20 truy vấn, 0 work trong `monks`.
- AC2: Khử trùng person theo `name_zh+authority`; test 玄奘 trả đúng 1 person canonical (hoặc gộp 2 ID với `same_as`).
- AC3: ID địa danh có 1 dạng canonical; short-ID phải redirect 301/200 tới cùng bản ghi; test `PL052464` và `PL000000052464` cùng `dila_id` hoặc 404.
- AC4: `mentions.text_count` khớp `len(texts)`; refs lineage parse được thành `{sigla,page,line}`.

**Ưu tiên:** P1.

---

### THS-14 — Mâu thuẫn truyền thống/niên đại không có nơi tra cứu công khai

**Kỳ vọng:** Có trang/khu vực "Mâu thuẫn & dị bản" cho từng nhân vật/dòng truyền thừa: ai nói gì (DILA vs Marcus vs CBETA), khác nhau ở đâu; có ghi chú khác biệt Bắc/Nam/Thiền tông.

**Cách tái lập:** `GET /api/conflicts`; `GET /daoanh/api/admin/lineage-conflicts`; `GET /daoanh/lineage?id=A000294`; tìm trong HTML các từ "Bắc tông", "Nam tông", "lineage_conflicts".

**Kết quả thực tế:**
- `/api/conflicts` → 200, **100 conflicts**, chỉ 2 loại `teacher_set`/`student_set`; ví dụ `{"conflict_type":"student_set","label":"Issan Ichinei","dila_count":17,"marcus_count":0}`; không có conflict giáo lý/truyền thống/niên đại.
- Không có trang UI liệt kê conflicts (nav chỉ Trang chủ/Địa đồ/Về dự án/Dữ liệu mở/Cộng đồng); trong `places.html` chỉ có panel evidence của 1 entity (A000294 có 2 conflicts hiện trong JSON nhưng không có nơi so sánh toàn cảnh).
- `/daoanh/lineage?id=A000294` chỉ hiển thị thầy/trò + chip nguồn; không có trường phái, không cảnh báo mâu thuẫn.
- Không tìm thấy "Bắc tông"/"Nam tông" trong HTML công khai (grep = 0).

**Phân loại:** thiếu tính năng (đúng mục tiêu "hiểu sai lệch giữa truyền thống").

**Ảnh hưởng:** Học viên không thể dùng site để thấy "truyền thống nói khác nhau"; đây là một trong ba trụ của khung Thạc sĩ nên giới hạn này hạ cấp toàn bộ giá trị học thuật của site.

**Yêu cầu cho Planning (AC):**
- AC1: Trang "Mâu thuẫn" công khai, lọc theo loại (teacher_set/student_set/niên đại/truyền thống), link từ home.
- AC2: Với mỗi conflict hiển thị song song nguồn A vs B + ref CBETA; test 10 conflict mẫu.
- AC3: Thêm trường `tradition_note` cho nhân vật/địa danh khi có khác biệt (Bắc/Nam/Thiền/Pháp Tướng…), hiển thị badge ở profile.

**Ưu tiên:** P1.

---

### THS-15 — Chỉ tìm substring Hán; không hỗ trợ tiếng Việt/Hán-Việt, không fuzzy, không lọc

**Kỳ vọng:** Tìm được bằng tiếng Việt ("sắc tức thị không") hoặc Hán-Việt không dấu; gõ sai/thiếu dấu vẫn tìm gần đúng; lọc được theo bộ kinh, triều đại, dịch giả.

**Cách tái lập:** `corpus-search?q=sắc tức thị không`; `?q=色`; `?q=kim cang`; `catalog?translator=玄奘`; `catalog?sort=title`.

**Kết quả thực tế:** câu Việt → 0; `q=色` → 400 `"query_too_short","min_length":2` (không thể tra một chữ Hán đơn, dù đó là đơn vị tra cứu phổ biến); không có tham số fuzzy/transliteration; `catalog?translator=`/`?sort=` bị bỏ qua; không có filter theo bộ/triều đại ở corpus-search. `[SUY LUẬN TỪ CODE app.py:14487]` `"Parameterized LIKE search — no fuzzy, no LLM, exact substring only"` (comment trong code).

**Phân loại:** thiếu tính năng.

**Ảnh hưởng:** Học viên Việt Nam phải tự chuyển Hán-Việt → Hán (hoặc biết chữ Hán) mới tra được; tăng thời gian và rủi ro sai từ. Không lọc được ngữ liệu theo phạm vi luận văn.

**Yêu cầu cho Planning (AC):**
- AC1: Cho phép q 1 ký tự Hán (hoặc ghi rõ lý do chặn) và trả kết quả; test q=色.
- AC2: Thêm tìm Hán-Việt/phiên âm: gõ "kim cang" trả kết quả chứa 金剛 (hoặc trả gợi ý "金剛").
- AC3: Thêm filter `sigla`, `dynasty`, `translator` cho corpus-search; test mỗi filter thu hẹp đúng.

**Ưu tiên:** P2.

---

### THS-16 — Coverage/pagination của corpus không minh bạch; thiếu tài liệu API

**Kỳ vọng:** Biết chính xác mỗi bộ đã nhập bao nhiêu quyển/trang/mentions, tổng số trang duyệt được, và có tài liệu API (tham số, giới hạn, license) để trích dẫn phương pháp.

**Cách tái lập:** `GET /daoanh/api/cbeta/text/T51n2076/browse?limit=500`; `GET /daoanh/api/cbeta/texts`; so `coverage.total_mentions` (22.275) vs `pagination.total` (492); đọc `/daoanh/opendata`.

**Kết quả thực tế:**
- `pagination.total:492` trong khi `coverage.total_mentions:22275` — 492 là **unique_pages**, không phải số bản ghi duyệt được; nhãn "trang" dễ hiểu sai (492 "trang" cho 22.275 mentions).
- `limit=500` được chấp nhận (response 110 KB) — không rõ cap; không có cursor/next; offset phi tuyến (offset=99999 trả mảng rỗng nhưng `has_prev:true`).
- Chỉ 5 bộ; không có thông tin "bộ X đã nhập bao nhiêu %" ngoài các con số tổng.
- `/daoanh/opendata` chỉ nêu 2 endpoint (`/daoanh/places/`, `/daoanh/api/progress/dashboard`) và câu "API hoàn chỉnh cho Đại Tạng (CBETA) và Tu sĩ (DILA) đang trong giai đoạn phát triển"; không có tài liệu tham số/giới hạn/license cấp field, không có OpenAPI.

**Phân loại:** thiếu tính năng (docs/coverage) + sai lệch nhãn.

**Ảnh hưởng:** Luận văn phải mô tả "phạm vi dữ liệu khảo sát" — hiện không thể nêu chính xác. Việc tự gọi API cũng không ổn định vì thiếu hợp đồng API.

**Yêu cầu cho Planning (AC):**
- AC1: Mỗi bộ trả `coverage:{juans_total, pages_total, mentions_total, imported_pct}`; test khớp DB.
- AC2: `pagination` có `has_next/next_offset` hoạt động; test duyệt 3 trang liên tiếp không trùng.
- AC3: Có trang `/daoanh/docs` (hoặc markdown) liệt kê endpoint + tham số + giới hạn + license; smoke test 5 endpoint mẫu từ tài liệu.

**Ưu tiên:** P2.

---

## 4. Cái đã tốt (≥5 mục — để Planning không phá)

1. **Bản đồ địa danh + tab chi tiết phong phú**: `/daoanh/places` (200, 761 KB) hoạt động; chọn `?select=PL…` mở tab Nhân vật/Truyền thừa/Nexus/Niên đại/Giáo lý/Thư viện/Nghi lễ. Đây là "cửa vào" tốt nhất hiện có.
2. **Locator địa danh có thật**: `/daoanh/api/places/PL000000023255/cbeta` trả `ref_code:"T50n2060_p0457c16"` + fosizhi entries kèm `book_title`, `page`, URL (g008p0503…) — đúng dạng trích dẫn CBETA, nên giữ và nhân rộng.
3. **Bằng chứng có `exact_span` ở tầng sự kiện**: event founding trả `"exact_span":"少室寺 魏太和 (477年建)"`, `confidence`, `source_record` — mẫu tốt để nhân rộng sang claims.
4. **Có API đối chiếu đúng hướng**: `/daoanh/api/cbeta/T0251/compare` trả version theo truyền thống (84000 Toh 21 confidence 0.99, SAT, SuttaCentral) — hạ tầng sẵn, chỉ thiếu text/alignment.
5. **Browse corpus có phân trang thật**: `/daoanh/api/cbeta/text/T51n2076/browse?offset=20&limit=5` trả `has_next/has_prev/total` và snippet + `page` — mẫu pagination tốt để áp cho search.
6. **Profile nhân vật giàu**: A000294 trả bio, giáo đoàn lineage (thầy/trò + ref CBETA), `texts` chứa `cbeta_ref` dạng `T50n2061_p0815a10`, `places` kèm `source_url` DILA — nền tốt cho citation nếu chuẩn hóa.
7. **Minh bạch license nguồn**: `/daoanh/opendata` nêu rõ CC BY-NC-SA 4.0 (CBETA), điều khoản DILA/Marcus + trích dẫn Bingenheimer et al. (2011) — cần giữ và bổ sung license cấp field.
8. **Đã có API tổng hợp & graph hữu ích**: `/daoanh/api/search` (monks/works/places), `/daoanh/api/nexus/find`, `/daoanh/api/monk/<id>/graph`, JSON-LD/CSL-JSON endpoint (dù lỗi) — chỉ cần sửa/nối vào UI.
9. **JSON API ổn định, nhanh, không cần auth**: hầu hết endpoint trả <1 s, JSON có `ok` flag, dễ dùng cho phân tích phụ lục.

---

## 5. Câu hỏi cần Admin quyết

1. **Con số nào là sự thật?** 13.520 mục lục (home) hay 3.122 bản ghi (API)? Có kế hoạch nạp metadata/full-text cho phần còn lại không — và khi nào? (THS-01, THS-10)
2. **Phạm vi license**: CBETA CC BY-NC-SA 4.0 có cho phép hiển thị toàn văn trên site (hiện chỉ snippet) không? Nếu không, có được phép hiển thị song song khi người dùng đang đăng nhập học thuật? (THS-06)
3. **Ưu tiên roadmap**: sửa full-text search Đại Tạng trước (nặng, cần index) hay hoàn thiện **catalog + citation + provenance** trước (nhẹ hơn, đủ cho tiểu luận)? Đề xuất: catalog/citation/provenance trước, full-text sau. (THS-01→05, 11→12)
4. **Chuẩn trích dẫn mục tiêu** cho luận văn Việt Nam: CBETA ref + Chicago? CSL-JSON cho Zotero? Có cần APA/MLA/RIS không? (THS-11)
5. **"Đối chiếu Tam Tạng"**: mục tiêu là **alignment theo đoạn** (cần dữ liệu Pali/Tạng có bản quyền phức tạp) hay chỉ **liên kết nguồn**? Nếu chỉ link, phải đổi nhãn. (THS-07)
6. **Xử lý dữ liệu nhân vật sai** (sinh/mất/sect): sửa import gốc hay thêm badge "không rõ/unverified" và để người dùng tự kiểm? Ai chịu trách nhiệm QA dữ liệu DILA/MARCUS? (THS-09, THS-08)
7. **Chuẩn ID canonical** cho địa danh/nhân vật: `PL000000052464` (long) hay `PL052464` (short)? Có cần migration/alias map không? (THS-13)
8. **Có cần công bố "trang thái dữ liệu"** (verified_ratio, coverage, ngày cập nhật) trên mọi trang để tránh hiểu nhầm học thuật? (THS-08, THS-10, THS-16)
9. **Có cần thêm vai trò "học viên"** (tài khoản, lưu trích dẫn, xuất bibliography) không — nếu có thì endpoint admin hiện đang gated sẽ phải mở phần read-only. (THS-11, THS-16)

---

### Phụ lục A — Cách kiểm chứng nhanh (tái lập trong ~2 phút)

```text
# 1) scope & coverage
GET /daoanh/api/cbeta/texts                                   → count 5
GET /daoanh/api/cbeta/corpus-search?q=色即是空                  → result_count 0
GET /daoanh/api/cbeta/corpus-search?q=金剛&limit=50             → 50 kết quả, 1 sigla, page 17/50, juan 0/50
GET /daoanh/api/cbeta/corpus-search?q=金剛&limit=10&offset=10   → giống hệt limit=10 (offset bị bỏ qua)

# 2) locator
GET /daoanh/api/cbeta/person-passage/25207                      → page:"" juan:""
GET /daoanh/api/places/PL000000023255/cbeta                     → ref_code:T50n2060_p0457c16

# 3) đối chiếu & provenance
GET /daoanh/api/cbeta/T0251/compare?lang=vi                     → 4 versions, text:""
GET /daoanh/api/cbeta/X77n1524/compare?lang=vi                  → sigla T771524, total 0
GET /daoanh/api/evidence/PL000000023255                         → 38/38 unverified
GET /daoanh/api/entity/A000294/unified                          → claims [], canonical_name_vi ""

# 4) dữ liệu & số liệu
GET /daoanh/api/person/A000294/profile                          → birth_year 2024, death_year 1787
GET /daoanh/api/cbeta/catalog?limit=100&page=1                  → cbeta_ref null
GET /daoanh/api/dila/places?limit=1                             → total 59167 (home ghi 8,241)
GET /daoanh/api/dila/persons?limit=1                            → total 48673 (home ghi 5,800+)

# 5) export
GET /daoanh/api/places/PL000000023255/export?format=jsonld      → 200 {"ok":false,"error":"no such column: latitude"}
GET /daoanh/api/dila/persons?format=csv                         → 500
GET /daoanh/api/public/export/citation?entity_id=A000294&format=csl-json → thiếu author/issued/url
```

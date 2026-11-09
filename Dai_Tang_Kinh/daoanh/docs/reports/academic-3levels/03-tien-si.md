# Tiến Sĩ — Khảo sát tra cứu trên https://phatphaponline.org (2026-10-25)

> Phiên đo: 2026-10-25, 19:55–20:10 (UTC+7). Người đo: Tăng Ni nghiên cứu sinh Tiến sĩ Phật học,
> vai "nhà nghiên cứu phải tái lập và kiểm toán".
> Phương pháp: GET-only qua `python requests` tới site LIVE + đọc code tĩnh repo `daoanh/` để giải thích nguyên nhân.
> **Nhãn bằng chứng:** `[ĐO ĐƯỢC: URL + HTTP + trích]`, `[SUY LUẬN TỪ CODE: file:line]`, `[CHƯA KIỂM CHỨNG]`.
> **Giới hạn phương pháp:** node/Playwright/browser không chạy được ⇒ không kiểm tra render JS/console; không truy cập DB, không gọi
> endpoint ghi, không POST. Vì vậy các kết luận về UI chỉ dừng ở mức HTML/JSON tĩnh trả về. Mọi con số dưới đây đo được trong phiên này.

## 0. Persona & nhu cầu tra cứu

Tôi là Tăng Ni làm luận án Tiến sĩ Phật học, cần dùng site như một **công cụ tra cứu có thể trích dẫn và bị phản biện**:

1. **Tìm** địa danh, nhân vật, kinh điển, phả hệ, sự kiện theo khóa học thuật (triều đại, tông phái, năm, CBETA ref).
2. **Trỏ về bản văn**: mỗi khẳng định (claim) phải có nguồn + vị trí chính xác trong bản văn (CBETA page/line, TEI), không chỉ một câu tóm tắt.
3. **Tái lập**: người khác chạy lại đúng truy vấn phải ra đúng kết quả, đúng thứ tự; phải biết **phiên bản dữ liệu** (dataset_version/hash) tại thời điểm tôi trích.
4. **Kiểm toán**: trạng thái verified/unverified, ai duyệt, khi nào, lịch sử thay đổi; xuất được bằng chứng để đưa vào phụ lục luận án.
5. **Trích dẫn**: DOI/citation format/giấy phép tái sử dụng rõ ràng cho chính dataset phái sinh của site (không chỉ nguồn gốc CBETA/DILA).

Nhu cầu này xuất phát từ chuẩn cấp Tiến sĩ Admin đã duyệt: *"mọi khẳng định trỏ về bản văn/DB, tái lập được, kiểm toán được"* + yêu cầu `dataset_version` + export JSON-LD.

## 1. Tóm tắt

**Tổng: 16 limitation — 4 P0, 9 P1, 3 P2.** Trạng thái chung: tất cả đang mở, chưa thấy fix trong phiên đo.

Ba câu kết luận:

1. Site là **công cụ tra cứu địa danh/nhân vật/phả hệ khá tốt và trung thực về nguồn** (claim có source/confidence, evidence API tự ghi "100% unverified"), nhưng **chưa đạt chuẩn Tiến sĩ**: không có bản văn toàn văn (chỉ 5 text dạng snippet), không export được dataset/JSON-LD, 0% claim verified, không có version/hash toàn cục.
2. **Không có tài liệu API công khai** (`/daoanh/docs/` 404 dù chính site quảng cáo) và **số liệu công bố trên trang chủ bị hardcode lệch 4–8 lần** so với API (8.241 vs 59.167 địa danh; 5.800+ vs 48.673 tu sĩ; 13.520 vs 3.122 mục lục) ⇒ không thể viết mục "Phương pháp & dữ liệu" theo kiểu tái lập được.
3. **Rủi ro nghiêm trọng nhất là tính kiểm toán**: login gateway 502 nhưng toàn bộ `/daoanh/admin/` và `/api/admin/*` mở công khai (một endpoint trả 28,5 MB dữ liệu), nên "verified/audit trail" hiện không có giá trị chứng cứ; phải đóng/khôi phục auth **trước khi** công bố bất kỳ "dataset học thuật" nào.

## 2. Bảng tổng hợp

| ID | Giới hạn | Mức | Bằng chứng (URL/HTTP) | Trạng thái |
|---|---|---|---|---|
| TSI-01 | Không có tài liệu API công khai; card "Tài liệu kỹ thuật" dẫn tới 404; API_DOCS.md nội bộ lệch live (97/249 endpoint docs-claim không có trong code) | **P0** | `GET /daoanh/docs/` 404; `GET /daoanh/api/docs` 404; `/daoanh/community` href=`/daoanh/docs/`; `GET /daoanh/api/progress/dashboard` 200 (endpoints_compare 249 mục, 97 `code_found:false`) | Mở |
| TSI-02 | Không xuất được dataset/JSON-LD/TTL: endpoint export duy nhất trả lỗi SQL; không bulk; không DOI/version toàn cục | **P0** | `GET /daoanh/api/places/PL000000023255/export` 200 `{"error":"no such column: latitude","ok":false}`; `?format=turtle` 400; `/api/get_ttl/*` 404; `/api/dataset`, `/api/meta`, `/api/version` 404 | Mở |
| TSI-03 | Bản văn chỉ có 5 text dạng snippet, không toàn văn/TEI; catalog thực 3.122 mục, trang chủ quảng cáo 13.520 | **P0** | `GET /api/cbeta/texts` count=5; `GET /api/cbeta/text/T50n2060/browse` `complete_text:false`, `granularity:"context_snippet"`; `GET /api/admin/cbeta/catalog-stats` `xml_on_disk:0` | Mở |
| TSI-04 | Không kiểm toán được: login 502, admin UI/API mở không xác thực (28,5 MB verification list), không audit identity | **P0** | `GET /daoanh/login.html` 502; `GET /daoanh/admin/` 200 (không chuỗi login/password/token); `GET /api/admin/verification/list` 200, 28.540.933 bytes | Mở |
| TSI-05 | CBETA ref `T50n2060_p0457c16` không resolve được tới đúng span/line; không có TEI/XML gốc; tìm bằng ref trả 0 | **P1** | `GET /api/places/PL000000023255/cbeta` passage chỉ có `ref_code`; `GET /api/cbeta/person-passage/22276` `ref_code:""`; `GET /api/cbeta/corpus-search?q=T50n2060_p0425b` `result_count:0` | Mở |
| TSI-06 | 100% claim `unverified`, 100% event `candidate`; `/api/entity/<id>/unified` trả claims rỗng mâu thuẫn `/api/evidence/<id>` (17 claim) | **P1** | `GET /api/evidence/A000294` `unverified_count:17, release_status:"review_required"`; `GET /api/entity/A000294/unified` `claims:[], claims_count:0`; 38/38 claim địa danh unverified | Mở |
| TSI-07 | Số liệu công bố hardcode lệch API: 8.241↔59.167 địa danh; 5.800+↔48.673 tu sĩ; 13.520↔3.122 mục lục; 1.200+/2.000+↔11.169 cạnh | **P1** | `/daoanh/` (home.html:1005-1015) vs `GET /api/dila/places` total=59167; `GET /api/persons/browse` total=48673; `GET /api/cbeta/catalog` total=3122 | Mở |
| TSI-08 | Truy vấn định lượng lỗi/giới hạn: `has_lineage=1` → 500 SQL; lọc dynasty chỉ khớp chữ Hán; cap âm thầm 100/500/10.000, thiếu `total` | **P1** | `GET /api/persons/browse?has_lineage=1` 500 `{"error":"near \"AND\": syntax error"}`; `?dynasty=Tang` total=0 vs `?dynasty=唐` total=4375; `/api/chronology/events?limit=100000` count=500 | Mở |
| TSI-09 | Không có dataset_version/hash toàn cục, không ETag/Last-Modified; version chỉ per-entity, `generated_at` đổi giữa 2 lần gọi | **P1** | `GET /api/evidence/A000294` version `5c4cc67a` (chỉ entity); 2 lần `GET /api/entity/A000294/unified` SHA256 khác nhau; `/api/cbeta/texts` không có header cache | Mở |
| TSI-10 | Compliance dashboard tự báo PASS sai: `claims_reviewed` 9,83% trên mục tiêu 100% nhưng `status:"pass"` | **P1** | `GET /daoanh/api/compliance/dashboard` 200: `claims_reviewed {percent:9.83, goal:1.0, status:"pass"}`, note `"Bootstrap: 44015 đã duyệt"` | Mở |
| TSI-11 | CORS hardcode `http://127.0.0.1:8080`; GET có Origin không trả ACAO ⇒ ứng dụng web nghiên cứu ngoài domain bị chặn | **P1** | `OPTIONS /daoanh/api/dashboard/stats` 200 `Access-Control-Allow-Origin: http://127.0.0.1:8080`; `GET` + `Origin: https://example.edu` không có ACAO | Mở |
| TSI-12 | Error/envelope không nhất quán: ≥6 kiểu vỏ JSON; lỗi trả 200; lộ SQL/Python traceback; 404/405 dạng HTML | **P1** | `?limit=abc` 500 `{"error":"invalid literal for int()..."}`; export 200 kèm error; `GET /api/admin/claims/1/review` 405 HTML; 6 endpoint 6 kiểu envelope | Mở |
| TSI-13 | Thiếu license/DOI/citation cho dataset phái sinh; điều khoản cấm tái phân phối corpus; license mâu thuẫn giữa opendata (3 nguồn) và about (nhiều nguồn) | **P1** | `/daoanh/opendata` 3 nguồn + "API ... đang trong giai đoạn phát triển"; `/daoanh/about` §3 "không được ... phân phối lại toàn bộ corpus như dataset độc lập"; 0 hit "DOI"/"zenodo" trong 4 trang | Mở |
| TSI-14 | Không có permalink per-entity: `/daoanh/places/<PL_ID>` 404; link canonical chỉ là query `?fly=...&select=`; trang SPA 742 KB phụ thuộc JS | **P2** | `GET /daoanh/places/PL000000023255` 404; home link `/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255`; `/daoanh/places` 200 (761.121 bytes, 85 lệnh `fetch(`) | Mở |
| TSI-15 | Tìm kiếm hạn chế: chặn 1 ký tự Hán (`佛`), kết quả khác nhau có/không dấu, không filter sigla/triều đại trong corpus-search | **P2** | `GET /api/cbeta/corpus-search?q=佛` 400 `min_length:2`; `places/search?q="Thieu Lam"` count=2 vs `q="Thiếu Lâm"` count=1; `/api/search?q=Thieu` monks=0 vs `q=Thiếu` monks=10 | Mở |
| TSI-16 | Thiếu schema ngữ nghĩa cho graph/namespace (`pth:`, `dila:`); graph metrics không có định nghĩa; `/api/entity/<id>/related` rỗng dù có 17 claim | **P2** | `GET /api/places/PL000000023255/graph` 75 nodes/75 edges (có `text:2060`); `GET /api/entity/A000294/related` `persons:[],places:[],texts:[]`; không có `/api/graph/schema` | Mở |

## 3. Chi tiết từng giới hạn

### TSI-01 — Không có tài liệu API công khai, tài liệu nội bộ lệch live
- **Kỳ vọng của nghiên cứu sinh:** mở một trang tài liệu API công khai để biết endpoint nào là **hợp đồng công khai**, schema response, tham số, phân trang, rate limit, license và version; đúng như card "Tài liệu kỹ thuật — GitBook với hướng dẫn API..." trên trang Cộng đồng.
- **Cách tái lập:**
  1. `GET https://phatphaponline.org/daoanh/docs/` → 404 (nginx, 162 bytes); `GET /daoanh/api/docs` → 404 (Flask, 207 bytes); `GET /docs/` → 404.
  2. Mở `/daoanh/community`, tìm card "Tài liệu kỹ thuật": anchor `href="/daoanh/docs/"` → chính là URL 404 ở trên.
  3. Đọc `daoanh/API_DOCS.md` (local, 164 dòng, "Version 1.0 — Last Updated 2026-04-12", 25 endpoint) rồi thử các endpoint được tài liệu hoá: `/api/places`, `/api/persons`, `/api/persons/search`, `/api/deepsearch`, `/api/rag/health` → **404 HTML**; `/api/dict/search?q=x` → 200 nhưng body vô nghĩa `{"bio":"Chưa có dữ liệu từ điển cho search","id":"searc..."}` (bị route `/api/dict/<dila_id>` bắt nhầm).
  4. `GET /daoanh/api/progress/dashboard` → 200; `endpoints_compare` có **249 mục, 97 mục `code_found:false`** (docs khai nhưng code không có), `generated_at: 2026-10-03T11:23:48` (bản tự sinh 22 ngày trước phiên đo).
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` không tồn tại bất kỳ trang docs/OpenAPI công khai nào. `[ĐO ĐƯỢC]` trang `/daoanh/opendata` mục "API tra cứu (nội bộ)" chỉ liệt kê **2 endpoint** (`GET /daoanh/places/`, `GET /daoanh/api/progress/dashboard`) và ghi *"API hoàn chỉnh cho Đại Tạng (CBETA) và Tu sĩ (DILA) đang trong giai đoạn phát triển"*. `[SUY LUẬN TỪ CODE]` `daoanh/app.py` có **337** decorator `@app.route(...)`; tôi đã gọi thử 40+ endpoint — phần lớn không có trong bất kỳ tài liệu công khai nào.
- **Phân loại:** thiếu tính năng + sai lệch tài liệu.
- **Ảnh hưởng tới cấp Tiến sĩ:** không có "API contract version" để trích trong mục phương pháp; người phản biện không thể chạy lại; mỗi lần cần dữ liệu phải tự dò endpoint và tự đoán schema — đúng thứ mà chuẩn "tái lập được" cấm.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `GET /daoanh/docs/` trả 200 HTML render từ **một nguồn duy nhất** (OpenAPI 3.1 + Markdown), có mục: public/internal, schema, pagination, rate limit, license, dataset version.
  - (b) `GET /daoanh/api/openapi.json` trả 200, validate được bằng `openapi-spec-validator`.
  - (c) CI test: 100% endpoint khai trong OpenAPI phải trả khác 404; 0 endpoint không có trong spec (hoặc gắn nhãn `internal`).
  - (d) Card "Tài liệu kỹ thuật" trên `/daoanh/community` trỏ đúng `/daoanh/docs/` (200).
- **Ưu tiên:** **P0**.

### TSI-02 — Không xuất được dataset/JSON-LD/TTL: endpoint export duy nhất lỗi, không bulk, không version/DOI
- **Kỳ vọng của nghiên cứu sinh:** xuất một bản ghi dưới dạng JSON-LD để đưa vào phụ lục; tải một gói dataset (hoặc JSONL/TTL) có **version + hash + license + citation** để kiểm toán ngoài hệ thống.
- **Cách tái lập:**
  1. `GET /daoanh/api/places/PL000000023255/export` → **200** `{"error":"no such column: latitude","ok":false}`.
  2. `?format=jsonld` → cùng lỗi; `?format=turtle` → **400** `{"ok":false,"error":"Chỉ hỗ trợ format=jsonld hiện tại"}`.
  3. Thử địa danh khác `PL000000000001/export` → cùng lỗi SQL (không phải lỗi riêng 1 ID).
  4. `GET /api/get_ttl/dila_person.ttl` → 404 `{"error":"File not found"}`; `/api/dataset`, `/api/dataset/version`, `/api/meta`, `/api/version`, `/api/export` → 404.
  5. `GET /daoanh/api/places/all?limit=20000` → `count:10000` (bị cap), trong khi tổng địa danh thật 59.167 (`/api/dila/places`).
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` lỗi SQL ở trên. `[SUY LUẬN TỪ CODE]` `app.py:19276` query `SELECT ... latitude, longitude FROM places_dila` nhưng dữ liệu live `/daoanh/api/places/PL000000023255` trả field **`gps_lat`, `gps_long`** (đo được) ⇒ **schema drift** giữa code và DB production; handler bắt `Exception` rồi trả **HTTP 200 kèm `ok:false`** (`app.py:19337-19338`). Hàm `_compute_dataset_version` (`app.py:18945-18967`) đã tồn tại nhưng không có endpoint toàn cục; `dashboard.stats` cho `ttl_master:0`.
- **Phân loại:** lỗi API + lỗi dữ liệu + thiếu tính năng.
- **Ảnh hưởng tới cấp Tiến sĩ:** yêu cầu "dataset_version + export JSON-LD" **không đạt**; không có gói dữ liệu để kiểm toán/tái lập ngoài site; không thể đưa "Phụ lục dữ liệu" vào luận án.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `GET /daoanh/api/places/<PL_ID>/export` trả 200 JSON-LD hợp lệ (schema.org `Place`, có `@context`, `pth:datasetVersion`, `pth:claimCount`, `signature`), validate bằng JSON-LD processor.
  - (b) `GET /daoanh/api/places/<ID>/export?format=turtle` trả `text/turtle` 200 (hoặc bỏ tham số khỏi docs và trả 400 JSON đúng chuẩn).
  - (c) `GET /daoanh/api/dataset` (có phân trang, không cap âm thầm) xuất được toàn bộ 59.167 places / 48.673 persons / 447.885 claims kèm **SHA256 + version + license + generated_at**; response có `total` đúng.
  - (d) Regression test chạy export cho ≥2 địa danh khác nhau + 1 person, phải 200 `ok:true`.
- **Ưu tiên:** **P0**.

### TSI-03 — Bản văn: chỉ 5 text dạng snippet, không toàn văn/TEI; catalog thực 3.122 mục
- **Kỳ vọng của nghiên cứu sinh:** tra được **toàn văn** bản văn CBETA (hoặc ít nhất biết chính xác tỉ lệ và phạm vi), và có thể trích dẫn nguyên văn kèm page/line.
- **Cách tái lập:**
  1. `GET /daoanh/api/cbeta/texts` → `count:5`; 5 text: T51n2076 (Cảnh Đức Truyền Đăng Lục), T50n2060 (Tục Cao Tăng Truyện), T50n2061 (Tống Cao Tăng Truyện), X77n1524, T50n2062; tổng `total_mentions` 72.628.
  2. `GET /daoanh/api/cbeta/text/T50n2060/browse` → `coverage: {"complete_text": false, "granularity": "context_snippet", "note": "Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn.", "total_mentions": 17685, "unique_pages": 415}`.
  3. `GET /daoanh/api/cbeta/corpus-search?q=少林` → `coverage: {"catalog_total": 3122, "passages_searchable": 72628, "scope": "imported_corpus", "texts_searchable": 5}`.
  4. `GET /daoanh/api/admin/cbeta/catalog-stats` (endpoint này **mở công khai**) → `{"has_sigla":2528,"imported":197,"total_catalog":3122,"translated_any":5,"xml_on_disk":0,"xml_root_exists":false}`.
  5. Trang chủ quảng cáo "13.520 mục lục kinh"; `/daoanh/about` cũng 13.520.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` catalog thực tế **3.122** mục (không phải 13.520); chỉ **197** text được import, **5** text có bản dịch, **0 XML trên server**; chỉ **5 text** searchable, dạng snippet ngữ cảnh — không phải toàn văn.
- **Phân loại:** lỗi dữ liệu + thiếu tính năng + sai lệch số liệu.
- **Ảnh hưởng tới cấp Tiến sĩ:** với yêu cầu "mọi khẳng định trỏ về bản văn", hiện chỉ trỏ được tới **snippet do hệ thống chọn**, không phải bản văn gốc; không thể đối chiếu dị bản/khảo chứng văn bản — công việc đặc thù của Tiến sĩ Phật học.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) Công bố trang "Phạm vi corpus" lấy từ API: số text có trong catalog, số text import, số text có full-text, số trang, số XML/TEI, ngày import, nguồn CBETA version.
  - (b) `GET /api/cbeta/coverage` trả JSON gồm các số trên (200, có `generated_at`).
  - (c) Hoặc mở rộng: mỗi text import phải có `complete_text:true` + TEI/XML gốc tải được, và số lượng phải khớp con số công bố trên home.
  - (d) Con số "13.520" trên home phải hoặc (i) khớp `/api/cbeta/catalog.total`, hoặc (ii) được thay bằng số API + ngày chốt.
- **Ưu tiên:** **P0**.

### TSI-04 — Không kiểm toán được: login 502, admin UI/API mở hoàn toàn, không audit identity
- **Kỳ vọng của nghiên cứu sinh:** trạng thái verified chỉ do người có thẩm quyền đặt; có lịch sử duyệt (ai, khi nào, trước/sau) và có thể xuất ra để kiểm toán.
- **Cách tái lập:**
  1. `GET /daoanh/login.html` → **502 Bad Gateway**; `GET /daoanh/api/login/status` → **502**; `/daoanh/api/login/me` → 502.
  2. `GET /daoanh/admin/` → **200**, 82.079 bytes, tiêu đề "Đạo Ảnh - Statistics Dashboard v4.0", HTML **không chứa** chuỗi `login`, `password`, `token`; HTML gọi `/daoanh/api/admin/*`.
  3. `GET /api/admin/verification/list` → **200**, `Content-Length: 28540933` (28,5 MB) — danh sách verification kèm biography, graph_connections, spatial_timeline... **không cần cookie**.
  4. `GET /daoanh/api/admin/cbeta/catalog-stats`, `GET /api/admin/staging/list`, `GET /daoanh/api/admin/dashboard/stats` → đều **200**.
  5. `[SUY LUẬN TỪ CODE]` `app.py:14062` `POST /daoanh/api/admin/claims/<int:claim_id>/review` cập nhật `verification_status, assertion_level, reviewed_by, reviewed_at, editor_note` (`app.py:14091`) — route không có bước kiểm tra quyền trong thân hàm.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` login gateway chết (502) trong khi toàn bộ mặt admin mở; không có bất kỳ cơ chế xác thực nào được quan sát ở tầng HTTP.
- **Phân loại:** thiếu tính năng (auth/audit) + rủi ro toàn vẹn dữ liệu.
- **Ảnh hưởng tới cấp Tiến sĩ:** tiêu chí "kiểm toán được" **không thể chứng minh** — trạng thái verified có thể bị bất kỳ ai thay đổi, không có danh tính người duyệt, không có audit trail để trích. Đây là lý do tôi không thể coi bất kỳ "verified" nào trên site là bằng chứng học thuật.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) 100% `/daoanh/api/admin/*` trả **401** khi không có session hợp lệ (test không cookie → 401, có cookie → 200).
  - (b) Login gateway 200, có `/daoanh/api/login/status` 200.
  - (c) Mọi write ghi `audit_log` (user, timestamp UTC, before/after JSON, request_id).
  - (d) `GET /daoanh/api/audit/<entity_id>` (read-only) trả lịch sử thay đổi của claim/verification cho nhà nghiên cứu.
  - (e) `/daoanh/admin/` không render nội dung khi chưa đăng nhập (redirect hoặc 401).
- **Ưu tiên:** **P0**.

### TSI-05 — CBETA ref không resolve được tới đúng span/line; không có TEI/XML gốc
- **Kỳ vọng của nghiên cứu sinh:** bấm vào `T50n2060_p0457c16` phải ra đúng trang 0457, dòng c16, hiển thị nguyên văn đoạn đó, có DOI/URL tới nguồn, và tải được TEI/XML nếu cần.
- **Cách tái lập:**
  1. `GET /daoanh/api/places/PL000000023255/cbeta` → 39 `passages`, mỗi passage chỉ có `{"place_tag":"少林寺","ref_code":"T50n2060_p0457c16","sigla":"T50n2060","title_context":"唐高僧傳: 釋玄奘傳"}` — **không snippet, không line, không URL**.
  2. `GET /daoanh/api/cbeta/person-passage/1` → `{"ref_code":"","page":"","juan":"","passage_source":"context_snippet", ...}`; `/person-passage/22276` → `page:"0425b"` nhưng `ref_code:""` (mất line).
  3. `GET /daoanh/api/cbeta/text/T50n2060/browse` → item chỉ có `page`, `reader_ref`, `snippet`; **không có line_number**.
  4. `GET /daoanh/api/cbeta/corpus-search?q=T50n2060_p0425b` → 200 `result_count:0` (không tìm theo ref được).
  5. `GET /api/cbeta/text/T50n2060/tei` → 404; `catalog-stats` có `xml_on_disk:0`, `xml_root_exists:false`.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` ref tồn tại dưới dạng **chuỗi**, nhưng không có endpoint public nào biến ref → span văn bản; line luôn rỗng ở các endpoint public; không có TEI/XML.
- **Phân loại:** thiếu tính năng.
- **Ảnh hưởng tới cấp Tiến sĩ:** mỗi trích dẫn tôi phải **tự mở cbetaonline.dila.edu.tw và tự dò lại** — đúng nghĩa "buộc làm thủ công ngoài hệ thống"; không tái lập được quy trình trong site.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `GET /daoanh/api/cbeta/resolve?ref=T50n2060_p0457c16` → 200 `{sigla, page:"0457", line:"c16", juan, span_text, source_url}`.
  - (b) Browse hỗ trợ `?ref=` và trả nguyên văn đúng dòng; mỗi ref trong `/api/places/<id>/cbeta` click được (200).
  - (c) Test: lấy ngẫu nhiên 100 ref từ `dila_listbibl`, resolve ≥99/100 thành công, span_text không rỗng.
  - (d) Hoặc: mỗi text import kèm TEI/XML gốc, `GET /api/cbeta/text/<sigla>/tei` trả 200 `application/xml`.
- **Ưu tiên:** **P1**.

### TSI-06 — 100% claim `unverified`, 100% event `candidate`; unified API trả claims rỗng mâu thuẫn evidence
- **Kỳ vọng của nghiên cứu sinh:** biết claim nào đã được duyệt, ai duyệt, và lấy được đầy đủ claim qua API "canonical".
- **Cách tái lập:**
  1. `GET /daoanh/api/evidence/A000294` → `dataset_version {version:"5c4cc67a", claim_count:17}`; `verification_summary {unverified_count:17, verified_count:0, verified_ratio:0.0, dominant_status:"unverified", release_status:"review_required"}`; `data_status.notes.claims`: *"17 claim cho subject này — 100% 'unverified' theo toàn kho (447,885 claim)..."*; `data_status.notes.events`: *"3,530 event toàn kho — 100% review_status 'candidate' (chưa duyệt)."*
  2. `GET /daoanh/api/places/PL000000023255/claims` → `claims_count:38`, **38/38 `unverified`**; `source_url` null **37/38**; `retrieved_at` null 6/38; `source_reference` null 3/38.
  3. `GET /daoanh/api/entity/A000294/unified` → `claims:[]`, `claims_count:0` — **mâu thuẫn trực tiếp** với 17 claim của `/api/evidence/A000294`.
  4. `GET /daoanh/api/places/PL000000023255/events` → `total:55`, `candidate_events:1`, `reviewed_events:0`.
  5. `GET /daoanh/api/person/A000294/profile` → `mentions.texts[0] = {sigla:"T50n2061", title_zh:"Taishō Tripiṭaka"}` dù T50n2061 là 宋高僧傳 — metadata sai.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` không có một claim nào verified; không event nào reviewed; API "unified" làm mất claim; metadata nhân-vật/text không nhất quán.
- **Phân loại:** lỗi dữ liệu + lỗi API + thiếu tính năng.
- **Ảnh hưởng tới cấp Tiến sĩ:** mọi khẳng định phả hệ/địa danh trên site hiện là **ứng viên chưa duyệt**; luận án không thể dẫn site như nguồn "đã xác thực"; muốn dùng phải tự kiểm chứng toàn bộ — không có badge/audit trail từ API.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `/api/entity/<id>/unified` trả đúng số claim = `/api/evidence/<id>` (A000294: 17) và có `verification_status` từng claim.
  - (b) Mỗi claim public có `{verified_by, verified_at, audit_ref}` hoặc `null` rõ ràng (không im lặng).
  - (c) Endpoint `GET /api/claims?verification_status=unverified&entity=A000294` lọc được, trả `total`.
  - (d) Test: số claim unified == evidence cho 5 entity mẫu; profile hiển thị đúng title_zh theo sigla.
- **Ưu tiên:** **P1**.

### TSI-07 — Số liệu công bố hardcode lệch 4–8 lần so với API
- **Kỳ vọng của nghiên cứu sinh:** các con số tổng quan trên trang chủ/about/opendata phải lấy từ DB, khớp API, có ngày chốt và định nghĩa đếm.
- **Cách tái lập:**
  1. `/daoanh/` (home) — trong HTML: `8,241` địa danh, `13,520` mục lục kinh, `5,800+` tu sĩ, `1,200+` dòng truyền thừa (`home.html:1005-1015`; bản `/daoanh/` phục vụ `index.html:1037-1047`).
  2. `/daoanh/about` → `59,167` địa danh, `13,520` mục kinh, `48,673` hồ sơ tăng nhân, `2,000+` phả hệ (`about.html:285-288`).
  3. `/daoanh/opendata` → phạm vi DILA `8,241` địa danh · `5,800+` tu sĩ; SNA `1,200+` dòng truyền thừa (`opendata.html:240`).
  4. API thật: `GET /api/dila/places` `total:59167`; `GET /api/persons/browse` `total:48673`, `with_lineage:18121`; `GET /api/cbeta/catalog` `total:3122`; `GET /api/dashboard/stats` `marcus_edges:11169, marcus_monks:11300`; `GET /api/admin/master-stats` `places:59161`; `GET /api/stats` `total_places:59161, marcus_edges:0`.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` 4 cặp lệch: **8.241 ↔ 59.167** (×7,2), **5.800+ ↔ 48.673** (×8,4), **13.520 ↔ 3.122** (×4,3), **1.200+/2.000+ ↔ 11.169**; thêm `/api/stats` trả `marcus_edges:0` trong khi dashboard trả 11.169; `master-stats` 59.161 vs `dila/places` 59.167 (lệch 6). Không trang nào ghi ngày chốt/định nghĩa đếm. `[SUY LUẬN TỪ CODE]` các số này là **hardcode trong HTML tĩnh**, không render từ API.
- **Phân loại:** sai lệch số liệu.
- **Ảnh hưởng tới cấp Tiến sĩ:** nếu trích số liệu site vào phần "tổng quan dữ liệu" của luận án sẽ **sai 4–8 lần**; hai endpoint thống kê mâu thuẫn làm mất khả năng tái lập bảng biểu.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `GET /daoanh/api/dataset/summary` trả `{places, persons, catalog_texts, lineage_edges, generated_at, version, definitions}` — 1 nguồn sự thật duy nhất.
  - (b) home/about/opendata render từ endpoint đó (không hardcode); CI test so số hiển thị == API.
  - (c) Thống nhất `/api/stats` vs `/api/dashboard/stats` (cùng số `marcus_edges`, cùng `total_places`), hoặc gộp thành một.
  - (d) Mỗi con số có tooltip "định nghĩa + ngày chốt + nguồn bảng".
- **Ưu tiên:** **P1**.

### TSI-08 — Truy vấn định lượng lỗi/giới hạn: filter 500, lọc triều đại chỉ chữ Hán, cap âm thầm
- **Kỳ vọng của nghiên cứu sinh:** lọc theo `dynasty`, `sect`, `has_lineage`; phân trang rõ ràng; luôn biết tổng số để tính tỉ lệ.
- **Cách tái lập:**
  1. `GET /daoanh/api/persons/browse?has_lineage=1` → **500** `{"error":"near \"AND\": syntax error","ok":false}` (filter có trong docstring `app.py:8154`).
  2. `GET /api/persons/browse?dynasty=Tang` → `total:0, ok:true`; cùng filter với chữ Hán `?dynasty=唐` → `total:4375` (khớp `/api/dila/persons/stats` by_country 唐=4375). Gõ sai định dạng không bị báo lỗi, chỉ trả 0.
  3. `GET /api/persons/browse?limit=1000` → `limit:100` (bị hạ), `pages:487`; `?page=99999` → `ok:true`, `persons:[]` (không 400).
  4. `GET /api/chronology/events?limit=100000` → `count:500` (không có `total`); `/api/nexus/find` → `count:100` (không có `total`); `/api/places/all?limit=20000` → `count:10000` (không có `total`).
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` filter hợp lệ gây 500; lọc triều đại phụ thuộc chữ Hán chính xác; nhiều endpoint cắt kết quả **âm thầm** mà không trả tổng — nguy hiểm hơn báo lỗi. `[SUY LUẬN TỪ CODE]` `app.py:8184-8190` + `8199-8214`: khi không có điều kiện `WHERE`, chuỗi SQL thành `SELECT COUNT(*) FROM people p AND p.id IN (...)` → lỗi cú pháp.
- **Phân loại:** lỗi API + lỗi UI.
- **Ảnh hưởng tới cấp Tiến sĩ:** không thể lập bảng "số tăng nhân theo triều đại/tông phái" đáng tin; nếu vô tình dùng kết quả bị cap sẽ sai mẫu số; filter 500 chặn hẳn phân tích lineage.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `?has_lineage=1` → 200, `total:18121` (khớp `counts.with_lineage`).
  - (b) Filter dynasty nhận cả Hán-Việt/Chinese, trả 200; giá trị không hợp lệ → 400 kèm danh sách hợp lệ.
  - (c) Mọi list endpoint trả `{total, limit, offset, items}`; vượt bound → 400 hoặc `warning`; không cap âm thầm.
  - (d) CI test 4 tổ hợp filter (`dynasty=唐`, `dynasty=Tang`, `has_lineage=1`, `sect=...`).
- **Ưu tiên:** **P1**.

### TSI-09 — Không có dataset_version/hash toàn cục; không header version/cache; response biến thiên
- **Kỳ vọng của nghiên cứu sinh:** mọi câu trả lời phải gắn được với một "phiên bản dữ liệu" toàn cục (hash), và phải kiểm tra được dữ liệu đã đổi chưa (ETag/Last-Modified).
- **Cách tái lập:**
  1. `GET /api/evidence/A000294` → có `dataset_version {version:"5c4cc67a", full_hash:"5c4cc67a...", claim_count:17}` — **chỉ phạm vi entity**.
  2. Không tồn tại `/api/meta`, `/api/version`, `/api/dataset`, `/api/dataset/version` (404).
  3. `GET /api/entity/A000294/unified` hai lần liên tiếp (cách 0,4 s) → **SHA256 body khác nhau** (`d45f3e9b...` vs `ad26a77a...`), do `meta.generated_at` đổi (`2026-10-25T13:57:16.512445`).
  4. `GET /api/cbeta/texts` → **không có** `ETag`, `Last-Modified`, `Cache-Control`.
  5. `GET /api/progress/dashboard` → `generated_at: "2026-10-03T11:23:48"` (22 ngày trước phiên đo, không có cảnh báo độ mới).
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` chỉ có version per-entity; không có version toàn cục/cache validator; một số response không tất định. `[SUY LUẬN TỪ CODE]` `_compute_dataset_version` (`app.py:18945-18967`) chỉ nhận `entity_id`, không có helper global.
- **Phân loại:** thiếu tính năng.
- **Ảnh hưởng tới cấp Tiến sĩ:** không chứng minh được "tôi trích dữ liệu tại ngày X"; người phản biện không phát hiện được DB đã thay đổi so với lúc tôi công bố; dữ liệu động (generated_at) làm câu trả lời không ổn định.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `GET /daoanh/api/meta` trả `{dataset_version, full_hash, generated_at UTC, row_counts}` (hash toàn bộ bảng claims/people/places theo thứ tự xác định).
  - (b) Mọi JSON response thêm header `X-Dataset-Version`; endpoint dữ liệu có `ETag`/`Last-Modified`.
  - (c) Bỏ `generated_at` khỏi body hoặc tách response "live" vs "snapshot" để 2 lần gọi cùng query cho cùng body.
  - (d) Test: 2 lần gọi đồng nhất body; sau một thay đổi DB, version đổi.
- **Ưu tiên:** **P1**.

### TSI-10 — Compliance dashboard tự báo PASS sai (9,83% so với mục tiêu 100%)
- **Kỳ vọng của nghiên cứu sinh:** dashboard đo mức tuân thủ (compliance) phải phản ánh đúng mục tiêu; metric chưa đạt phải hiển thị fail/warn.
- **Cách tái lập:** `GET /daoanh/api/compliance/dashboard` → 200:
  - `summary {pass_metrics:7, fail_metrics:2, total_metrics:9}`
  - `claims_reviewed {percent:9.83, goal:1.0, status:"pass", passed:44015, total:447885, note:"Bootstrap: 44015 đã duyệt"}`
  - `claims_verified {percent:9.83, goal:1.0, status:"pass"}`
  - `claims_with_source`/`claims_with_confidence` `percent:100, note:"Bootstrap: 447885 đã duyệt"`.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` status "pass" cho metric 9,83% (mục tiêu 1.0 = 100%), tức **dashboard tự mâu thuẫn**; note "Bootstrap" cho thấy mục tiêu đang bị so với baseline 0 thay vì goal.
- **Phân loại:** sai lệch số liệu (audit metric).
- **Ảnh hưởng tới cấp Tiến sĩ:** nếu tôi trích dashboard này làm "bằng chứng chất lượng dữ liệu" sẽ bị phản biện ngay; nó che giấu việc 90% claim chưa review — đúng điểm yếu nhất của dữ liệu.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `status` phải = `fail` khi `percent < goal*100`; tách rõ `baseline` (khởi điểm) và `goal`.
  - (b) Mỗi metric có `measured_at`, `definition`, `sample_sql`.
  - (c) Test: metric `claims_reviewed` (9,83%) phải fail; test snapshot dashboard khớp query SQL trực tiếp.
- **Ưu tiên:** **P1**.

### TSI-11 — CORS hardcode localhost: ứng dụng web nghiên cứu ngoài domain không gọi được API
- **Kỳ vọng của nghiên cứu sinh:** dựng dashboard/notebook web trên domain đại học gọi trực tiếp API; hoặc nhúng kết quả vào trang luận án.
- **Cách tái lập:**
  1. `OPTIONS /daoanh/api/dashboard/stats` → 200, `Allow: OPTIONS, GET, HEAD`, **`Access-Control-Allow-Origin: http://127.0.0.1:8080`**, `Vary: Origin`.
  2. `GET /daoanh/api/dashboard/stats` với header `Origin: https://example.edu` → 200 nhưng **không có** `Access-Control-Allow-Origin`, không có `Vary`.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` ACAO hardcode đúng origin dev local; mọi origin khác (kể cả `https://phatphaponline.org` nếu khác port) sẽ bị browser chặn đọc response.
- **Phân loại:** thiếu tính năng (interoperability).
- **Ảnh hưởng tới cấp Tiến sĩ:** không tích hợp được API vào công cụ phân tích web; chỉ dùng được từ server-side script — hạn chế tái lập bởi người khác nếu họ dùng công cụ web.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) ACAO cấu hình whitelist (domain trường/khoa) hoặc `*` cho GET read-only; `Vary: Origin` luôn có.
  - (b) `OPTIONS` trả `Access-Control-Allow-Methods: GET, HEAD` + `Access-Control-Allow-Headers`.
  - (c) Test: OPTIONS từ 2 origin khác nhau trả ACAO tương ứng; GET kèm ACAO.
- **Ưu tiên:** **P1**.

### TSI-12 — Error/envelope không nhất quán, lỗi trả 200, lộ SQL/Python nội bộ
- **Kỳ vọng của nghiên cứu sinh:** một envelope thống nhất, lỗi có HTTP status đúng, không lộ chi tiết DB; như vậy mới viết được client phân tích dùng chung.
- **Cách tái lập:**
  1. Envelope khác nhau: `places/search` → `{ok, query, count, results}`; `public/search` → `{data, success}`; `search` → `{monks, works, places, success}`; `dila/places` → `{ok, items, limit, offset, total}`; `persons/browse` → `{ok, total, page, pages, limit, persons, filters, counts}`; `chronology/events` → `{ok, count, has_gps, results}`. **6 kiểu vỏ** cho 6 endpoint.
  2. Lỗi đúng chuẩn (mẫu tốt): `GET /api/cbeta/corpus-search?q=佛` → 400 `{"ok":false,"error":"query_too_short","message":"...","min_length":2}`.
  3. Lỗi trả 200: `GET /api/places/PL.../export` → **200** kèm `{"error":"no such column: latitude","ok":false}` (lộ SQL).
  4. Lỗi lộ Python: `GET /api/persons/browse?limit=abc` → 500 `{"error":"invalid literal for int() with base 10: 'abc'","ok":false}`.
  5. Lỗi HTML: `GET /api/admin/claims/1/review` → **405 HTML** (Flask); `/daoanh/docs/` 404 HTML nginx.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` client phải xử lý riêng từng endpoint; lỗi nội bộ/SQL bị phơi ra ngoài (vừa xấu học thuật vừa là rò rỉ schema).
- **Phân loại:** lỗi API.
- **Ảnh hưởng tới cấp Tiến sĩ:** công cụ phân tích phải viết custom parser cho từng endpoint → khó tái lập, dễ sai; lộ schema DB làm giảm độ tin cậy học thuật của hệ thống.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) Mọi JSON response cùng envelope `{ok, data, error:{code,message,details}, meta:{dataset_version, request_id}}`.
  - (b) Mọi 4xx/5xx trả JSON + status đúng; 5xx không chứa SQL/traceback.
  - (c) CI contract test: gọi 10 endpoint với tham số xấu → tất cả JSON, không lộ `sqlite3`/`Traceback`/`no such column`.
- **Ưu tiên:** **P1**.

### TSI-13 — Thiếu license/DOI/citation cho dataset phái sinh; điều khoản cấm tái phân phối; license mâu thuẫn giữa các trang
- **Kỳ vọng của nghiên cứu sinh:** biết dataset của site được cấp phép gì cho **luận án** (dùng thương mại? tái phân phối? ShareAlike?), trích dẫn thế nào (DOI, format, version) để đưa vào thư mục.
- **Cách tái lập:**
  1. `/daoanh/opendata` → 3 nguồn: CBETA "CC BY-NC-SA 4.0"; DILA "Học thuật phi TM"; SNA "Học thuật phi TM" + citation Bingenheimer/Hung/Wiles (2011); kết thúc bằng *"API hoàn chỉnh cho Đại Tạng (CBETA) và Tu sĩ (DILA) đang trong giai đoạn phát triển"*.
  2. `/daoanh/about` → danh sách license dài hơn (CC0 1.0, SuttaCentral CC BY-NC-SA, 84000 phi thương mại, FoJin Apache 2.0, DILA Authority CC BY-SA 3.0, Marcus Glossaries CC0 1.0, CBETA CC BY-NC-SA 4.0) + "Điều Khoản Sử Dụng v1.0": mục 3 *"Bạn không được: ... Tải và phân phối lại toàn bộ corpus văn bản như dataset độc lập"*.
  3. Đo trên 4 trang công khai (`/daoanh/`, `/about`, `/opendata`, `/community`): **0** lần xuất hiện "DOI", "doi.org", "zenodo", "JSON-LD", "dataset_version"; **0** script `application/ld+json`.
  4. `[SUY LUẬN TỪ CODE/docs]` roadmap nội bộ `docs/reports/PTDA-ACADEMIC-INTEGRATION-ROADMAP-2026-2036.md:96` ghi *"chưa có cam kết đối tác hay chứng nhận CoreTrustSeal"*; DOI duy nhất tìm được (`10.5281/zenodo.10004109`) là **dataset nguồn** của Van Cutsem/Bingenheimer, không phải dataset của site.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` không có DOI/citation format/version cho dataset site; license mâu thuẫn giữa opendata (3 nguồn) và about (nhiều nguồn); điều khoản cấm tái phân phối corpus xung đột với nhu cầu đính kèm dataset vào luận án.
- **Phân loại:** thiếu tính năng + tài liệu pháp lý chưa đủ.
- **Ảnh hưởng tới cấp Tiến sĩ:** không thể trích dataset theo chuẩn; rủi ro vi phạm CC BY-NC-SA (ShareAlike) khi công bố dataset phái sinh; thiếu DOI làm giảm khả năng kiểm chứng lâu dài.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) Trang `/daoanh/citation` (200) xuất BibTeX + DOI (nếu có) + `dataset_version` + license từng lớp dữ liệu.
  - (b) Bảng license matrix cho từng nguồn: dùng thương mại?, tái phân phối?, ShareAlike?, citation bắt buộc.
  - (c) Nếu công bố dataset: release trên Zenodo/OSF có DOI, kèm version + checksum.
  - (d) Một nguồn sự thật license dùng chung cho about + opendata (test nội dung 2 trang khớp).
- **Ưu tiên:** **P1**.

### TSI-14 — Không có permalink per-entity; link canonical là query string; trang phụ thuộc JS
- **Kỳ vọng của nghiên cứu sinh:** một URL ổn định dạng `/daoanh/places/PL000000023255` để trích trong chú thích/cuối trang; mở ra là thấy dữ liệu.
- **Cách tái lập:**
  1. `GET /daoanh/places/PL000000023255` → **404** (nginx, 162 bytes).
  2. Link "Xem trên bản đồ" trên home trỏ `/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255` (`home.html`), tức URL trích dẫn chứa cả tọa độ camera — không ổn định.
  3. `GET /daoanh/places` → 200, 761.121 bytes, HTML SPA có **85 lệnh `fetch(`**; không có dữ liệu place render sẵn (0 chuỗi `PL0000` trong HTML).
  4. `GET /daoanh/sitemap.xml` → 404; `GET /daoanh/panorama/` → 404.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` không có path-style permalink, không sitemap; nội dung chỉ hiện khi JS chạy (không kiểm chứng được render vì không có browser → `[CHƯA KIỂM CHỨNG]` phần hiển thị; nhưng HTML rỗng dữ liệu là đo được).
- **Phân loại:** lỗi UI + thiếu tính năng.
- **Ảnh hưởng tới cấp Tiến sĩ:** URL trích dẫn dễ gãy/đổi; người phản biện không mở được trực tiếp; không có HTML tĩnh để kiểm chứng khi JS lỗi.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) `GET /daoanh/places/<PL_ID>` 200, render server-side tối thiểu: id, tên vi/zh, nguồn, số claim, dataset_version.
  - (b) Link canonical trên home trỏ path đó; query `select=` redirect 301 → path.
  - (c) `sitemap.xml` liệt kê toàn bộ places/persons/lineage (đếm khớp API).
- **Ưu tiên:** **P2**.

### TSI-15 — Tìm kiếm hạn chế: chặn 1 ký tự Hán, kết quả khác nhau có/không dấu, thiếu filter
- **Kỳ vọng của nghiên cứu sinh:** tra 1 chữ Hán (佛, 禪) để thống kê tần suất; tra tiếng Việt không dấu vẫn ra kết quả; lọc theo sigla/juan/triều đại.
- **Cách tái lập:**
  1. `GET /api/cbeta/corpus-search?q=佛` → **400** `{"ok":false,"error":"query_too_short","message":"Vui lòng nhập ít nhất 2 ký tự để tìm kiếm.","min_length":2}` — không tra được 1 chữ Hán.
  2. `GET /api/places/search?q=Thieu Lam` → `count:2`; cùng nghĩa `q=Thiếu Lâm` → `count:1` (khác nhau).
  3. `GET /api/search?q=Thieu` → `monks:0, works:0, places:10`; `q=Thiếu` → `monks:10, works:3, places:3` (khác hoàn toàn).
  4. `corpus-search` không có tham số filter sigla/juan/dynasty/author; `limit` mặc định 30.
- **Kết quả thực tế:** `[ĐO ƯỢC]` kết quả phụ thuộc dấu và độ dài truy vấn theo cách không tài liệu hoá; `[SUY LUẬN TỪ CODE]` `app.py:8172` dùng `LIKE %q%` thô, không chuẩn hoá dấu.
- **Phân loại:** thiếu tính năng + lỗi UI.
- **Ảnh hưởng tới cấp Tiến sĩ:** không dùng được cho thống kê từ khoá (佛/禪) — công việc phổ biến trong Phật học; kết quả không xác định làm giảm khả năng tái lập.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) Cho phép `q` ≥1 ký tự CJK (hoặc có `min_length` riêng cho CJK và thông báo rõ).
  - (b) Chuẩn hoá NFC + tìm không dấu tuỳ chọn; "Thiếu Lâm" và "Thieu Lam" trả cùng tập kết quả.
  - (c) `corpus-search` nhận `sigla`, `juan`, `dynasty`, `author`; tài liệu hoá relevance/ordering.
- **Ưu tiên:** **P2**.

### TSI-16 — Thiếu schema ngữ nghĩa/namespace cho graph; graph metric không định nghĩa; `related` rỗng
- **Kỳ vọng của nghiên cứu sinh:** dùng graph cho phân tích mạng: biết loại node/edge, chiều, trọng số, namespace (`pth:`, `dila:`), và metric (degree, co-mention) có định nghĩa.
- **Cách tái lập:**
  1. `GET /api/places/PL000000023255/graph` → 200, `nodes:75`, `edges:75`; node gồm cả `text:2060` (`navigable:false`), edge label "kinh điển liên quan", `evidence_type:"with_evidence"` — không có `n_nodes/n_edges` tổng hợp, không có chiều/trọng số chuẩn hoá.
  2. `GET /api/monk/A000294/graph` → 17 nodes/17 edges, `source:"Marcus Bingenheimer ChineseBuddhism_SNA"`.
  3. `GET /api/entity/A000294/related` → `{persons:[], places:[], texts:[]}` dù subject có 17 claim + 23 học trò trong evidence.
  4. `GET /api/places/PL000000023255/timeline` → cross_refs `{wikidata_qid:"Q232771", confidence:"verified", mapped_by:"manual"}` + `founding.license:"CC0"` — tốt, nhưng không có schema chung.
  5. Không có endpoint `/api/graph/schema` (404); JSON-LD `@context` chỉ tồn tại trong code (`app.py:19308-19312`), không công bố.
- **Kết quả thực tế:** `[ĐO ĐƯỢC]` graph trả dữ liệu thô, thiếu định nghĩa; `related` rỗng mâu thuẫn claims.
- **Phân loại:** thiếu tính năng + tài liệu.
- **Ảnh hưởng tới cấp Tiến sĩ:** không thể dùng graph làm dữ liệu phân tích mạng có thể tái lập; không thể trích dẫn "mạng lưới truyền thừa" với định nghĩa node/edge rõ ràng.
- **Yêu cầu cho đội Planning (acceptance criteria đo được):**
  - (a) Công bố schema: node types (`person`, `place`, `text`, `event`), edge types + direction + weight + namespace `pth:`/`dila:`.
  - (b) Graph endpoint trả `{nodes, edges, n_nodes, n_edges, nodes_by_type}`.
  - (c) `/api/entity/<id>/related` trả đúng entity có claim/co-mention (test A000294 khác rỗng).
- **Ưu tiên:** **P2**.

## 4. Cái đã tốt (≥5 mục — để Planning không phá)

1. **Trung thực về trạng thái dữ liệu:** `/api/evidence/A000294` và `/api/places/PL.../doctrine` tự ghi rõ *"100% 'unverified' theo toàn kho (447,885 claim)"*, *"3,530 event ... 100% review_status 'candidate'"*, `release_status:"review_required"`. Đây là thái độ hiếm và đúng chuẩn học thuật — cần giữ nguyên, chỉ bổ sung badge/audit.
2. **Version per-entity có thể tái lập:** `_compute_dataset_version` (`app.py:18945-18967`) hash SHA256 trên chuỗi claim đã sắp theo `claim_id` → `version` 8 ký tự + `full_hash` 64 ký tự (A000294: `5c4cc67a`; PL000000023255: `b8ffbf3f`); 2 lần gọi cho cùng kết quả. Đây là nền tảng tốt để mở rộng thành version toàn cục.
3. **Provenance trong claim khá đầy đủ:** claim có `source` object (`code`, `authority_score`, `precedence_order`), `confidence`, `source_reference`, `verification_status`, `claim_type`; evidence có `lineage_conflicts` (teacher_set/student_set) — đủ để hiển thị "nguồn nào nói gì" nếu có UI.
4. **Ref CBETA được lưu trong dữ liệu:** `dila_listbibl` của PL000000023255 chứa hàng loạt ref dạng `( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋玄奘傳 {少林寺}`; endpoint `/api/places/<id>/cbeta` trả 39 passage có `ref_code` — chỉ còn thiếu bước resolve/span.
5. **Endpoint đọc chính ổn định:** 7/8 endpoint kiểm tra byte-identical qua 2 lần gọi (`places/search`, `persons/browse`, `places/<id>/graph`, `chronology/events`, `cbeta/texts`, `evidence/<id>`), ID `PL…`/`A…` ổn định trong phiên — nền tảng tốt cho reproducibility, chỉ cần thêm version header.
6. **License từng nguồn có ghi và có link:** CBETA CC BY-NC-SA 4.0 có link creativecommons.org; DILA CC BY-SA 3.0 (about); Marcus glossaries CC0 1.0; SNA có citation Bingenheimer et al. (2011); timeline ghi license từng layer (`wikidata: CC0`, `chinese_dynasties_static: public domain`) — cần chuẩn hoá chứ không phải làm lại.
7. **Error contract mẫu tốt đã tồn tại:** `corpus-search?q=佛` → 400 `{ok:false, error:"query_too_short", message, min_length}` — dùng làm chuẩn cho toàn bộ API.
8. **Không có tường đăng ký cho dữ liệu đọc:** các endpoint tra cứu chính (places, persons, cbeta, evidence) mở, không cần account — thuận lợi cho kiểm chứng độc lập (nhưng cần siết admin, xem TSI-04).

## 5. Câu hỏi cần Admin quyết

1. **Con số nào là chuẩn (SSOT) cho "địa danh"?** 8.241 (home/opendata), 59.167 (`places_dila` API), 59.161 (`master-stats`), hay 176.783 (`namevi_places_total`)? Cần định nghĩa đếm (đã GPS? đã map Việt? gồm cả category "địa lý rộng"?) trước khi sửa home.
2. **Tham vọng corpus cho cấp Tiến sĩ:** chỉ cần "chỉ mục trích dẫn + snippet" (đúng hiện trạng 5 text) hay phải có **toàn văn + TEI** cho một tập text xác định (ví dụ T50n2060/2061/2076)? Điều này quyết định khối lượng import và license.
3. **Quyền công bố dataset:** site có được phép phát hành dataset phái sinh (places/persons/claims) với DOI không, hay bị ràng buộc bởi CBETA NC-SA + DILA "cần permission"? Nếu không, cần xin văn bản đồng ý trước khi hứa "dataset export" cho cấp Tiến sĩ.
4. **Auth/audit:** khôi phục login gateway (server.py:5001) hay bỏ hẳn admin công khai? Ai là người duyệt claim (`reviewed_by`) và audit trail lưu ở đâu? Không có câu trả lời này thì TSI-04/TSI-06 không thể đóng.
5. **Tài liệu API:** deploy `/daoanh/docs/` (GitBook/OpenAPI) hay chỉ mount `API_DOCS.md` thành HTML? Ai chịu trách nhiệm sync spec với 337 route khi code đổi?
6. **Hợp đồng công khai:** endpoint nào cam kết ổn định (có version, deprecation policy) vs nội bộ (có thể đổi)? Cần danh sách chốt để Planning đánh dấu trong OpenAPI.
7. **Mức "verified" tối thiểu để công bố:** chấp nhận 0% claim verified (hiện trạng, chỉ công bố như "candidate dataset") hay phải review xong N% trước khi gọi là "dữ liệu học thuật"? Con số này cần đưa vào acceptance criteria của cấp Tiến sĩ.
8. **Ai chịu trách nhiệm "số liệu công bố"** (home/about/opendata) — có cần một script/CI tự sinh từ API và chặn deploy nếu lệch không?

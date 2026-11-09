# Cử Nhân — Khảo sát tra cứu trên https://phatphaponline.org (2026-10-25)

> **Người khảo sát:** Tăng Ni năm 1–2 Học viện Phật giáo (persona Cử nhân), dùng site LIVE như sinh viên bình thường.
> **Phương pháp:** chỉ GET (không đăng nhập, không ghi, không đụng DB/server); `python requests` trên site live + đọc code tĩnh repo local (`daoanh/app.py`, `daoanh/home.html`, `daoanh/places.html`, `daoanh/lineage.html`) để giải thích nguyên nhân. **Không có browser** trong sandbox ⇒ mọi kết luận về hành vi JS render ghi [SUY LUẬN TỪ CODE].
> **Nhãn bằng chứng:** **[ĐO ĐƯỢC: URL + HTTP + trích response]** · **[SUY LUẬN TỪ CODE file:line]** · **[CHƯA KIỂM CHỨNG]**.
> **Chuẩn cấp Cử nhân (Admin đã duyệt):** "đọc được, dễ hiểu, không sai lệch".
> **Ghi chú quan trọng cho Admin:** bản LIVE của `/daoanh/` **không nạp** `home_search.js` (chỉ có 1 inline script; `src` duy nhất là leaflet). Luồng tìm kiếm thực tế trên live là **redirect** `/daoanh/places?q=…`, không phải gọi `/api/places/search` như mô tả cũ. Toàn bộ 17 giới hạn dưới đây đo trên luồng live đó.

---

## 0. Persona & nhu cầu tra cứu

**Tôi là ai:** Tăng Ni năm thứ 1–2, đọc tiếng Việt là chính, biết ít chữ Hán, có điện thoại/laptop, không dùng được API, không biết DILA/CBETA là gì.

**5 nhu cầu tra cứu điển hình trong học kỳ 1–2:**

| # | Nhu cầu | Câu hỏi cụ thể | Đạt chuẩn Cử nhân khi… |
|---|---|---|---|
| N1 | Tìm một bộ kinh quen tên Việt | "Kinh Kim Cang" dạy ở đâu, bản dịch của ai, đọc ở đâu? | Gõ tên Việt → thấy kinh + dịch giả + đường đọc |
| N2 | Tra thuật ngữ Phật học cơ bản | "Bát Nhã", "Vô Ngã", "Duyên Khởi", "Niết Bàn" nghĩa gì? | Gõ thuật ngữ → có định nghĩa tiếng Việt, ghi nguồn |
| N3 | Tra nhân vật | "Huyền Trang", "Bồ Đề Đạt Ma", "Thích Ca Mâu Ni" là ai, thân thế, trích dẫn? | Có tên Việt chuẩn, tiểu sử tiếng Việt, năm sinh/mất, nguồn |
| N4 | Tra địa danh/chùa | "Thiếu Lâm Tự", "chùa Dâu", "chùa Vĩnh Nghiêm" ở đâu, liên quan kinh nào? | Có vị trí + liên kết kinh văn; gõ không dấu vẫn ra |
| N5 | Lấy thông tin để trích dẫn bài tập | Tên kinh, dịch giả, năm, nguồn, số trang CBETA | Copy được 1 citation đầy đủ đúng chuẩn học thuật |

**Sinh viên thường đi đường nào:** gõ ô tìm kiếm lớn ở trang chủ (`/daoanh/`) → bấm thẻ chủ đề → bấm kết quả. Cả 3 đường này đều gặp chặn (CN-01, CN-02, CN-03).

---

## 1. Tóm tắt

**Số lượng limitation: 17 — P0: 4 · P1: 9 · P2: 4.**

**3 câu kết luận:**

1. **Không có cửa vào tra cứu thật.** Ô tìm kiếm trang chủ không tìm gì cả (trừ "Thiếu Lâm" hiện demo cứng): mọi truy vấn bị đẩy sang `/daoanh/places?q=…`, và trang places hiểu `q` là **ID địa danh** nên panel chi tiết kẹt "Đang tải…" vĩnh viễn; 4/6 thẻ chủ đề (Đại Tạng, Tu Sĩ, Niên Đại, Đồ Thị) trả 404, thẻ Truyền Thừa dẫn tới trang báo "Không tìm thấy thiền sư này" → 5/6 đường điều hướng chính là ngõ cụt.
2. **Năng lực tra cứu phần lớn đã có trong API nhưng không có UI:** `/api/search` (monks/places/works), `/api/glossary` (từ điển 4 nguồn), `/api/cbeta/catalog?q=` (mục lục kinh + số trang CBETA), `/api/chronology/events` (niên đại) đều trả 200 với dữ liệu tốt, nhưng **không trang công khai nào gọi**; ngược lại, toàn văn kinh gần như không có (5 bộ, đều chỉ snippet; Kim Cang `T08n0235` 404) nên nhu cầu đọc kinh của Cử nhân chưa đáp ứng được.
3. **Nhiều nội dung hiển thị sai lệch hoặc thiếu trung thực với Cử nhân:** năm sinh/mất Huyền Trang hiển thị **2024–1787** (đúng 602–664), tiểu sử chỉ có chữ Hán, `/api/entity/…/unified` trả canonical Hán sai/vô nghĩa (玉華法師, 丁文南), 4 con số quảng cáo trên trang chủ không khớp bất kỳ `count` API nào, và empty state không phân biệt "không tìm thấy" với "lỗi".

---

## 2. Bảng tổng hợp

| ID | Giới hạn | Mức | Bằng chứng (URL/HTTP) | Trạng thái |
|---|---|---|---|---|
| CN-01 | Ô tìm kiếm trang chủ không tìm kiếm: redirect `places?q=` → trang places coi `q` là ID → panel kẹt "Đang tải…" | **P0** | `GET /daoanh/` 200; `GET /daoanh/places?q=Kinh%20Kim%20Cang` 200 (761.121 B, md5 trùng `/places`); `GET /daoanh/api/places/Kinh%20Kim%20Cang` **404** `{"error":"Place not found"}` | Đang xảy ra |
| CN-02 | Không có trang/ô tra cứu kinh điển theo tên Việt; "Đại Tạng" 404; corpus-search chỉ phủ 5 bộ Hán văn | **P0** | `GET /daoanh/tripitaka` **404**; `GET /daoanh/api/search?q=Kinh%20Ph%C3%A1p%20Hoa` 200 `works:[]`; `GET /daoanh/api/cbeta/texts` 200 `count:5` | Đang xảy ra |
| CN-03 | 5/6 thẻ chủ đề trang chủ là ngõ cụt: 4×404 + `lineage` không id báo "Không tìm thấy thiền sư" | **P0** | `/tripitaka` `/people` `/timeline` `/graph` **404** (nginx, 162 B); `/daoanh/lineage` 200 nhưng rơi nhánh `notFound` | Đang xảy ra |
| CN-04 | Không đọc được toàn văn kinh: chỉ 5 bộ sử/truyện dạng snippet; Kim Cang `T08n0235` 404 | **P0** | `/api/cbeta/text/T08n0235/browse` **404** `sigla_not_found`; `/T51n2076/browse` 200 `complete_text:false`; `/api/cbeta/passages/51190/units` `translated:11/9316` | Đang xảy ra |
| CN-05 | Từ điển Phật học có API đầy đủ nhưng **không có cửa vào UI** (popup code chết) | **P1** | `/daoanh/api/glossary?term=B%C3%A1t%20Nh%C3%A3` **200** (4 định nghĩa, 4 nguồn); `/daoanh/glossary` **404**; live HTML `class="da-glossary"` = **0** | Đang xảy ra |
| CN-06 | Năm sinh/mất nhân vật bị lấy nhầm số thư mục: Huyền Trang **2024–1787** (đúng 602–664) | **P1** | `/api/person/A000294/profile` `birth_year:2024, death_year:1787`; `/api/person/A000294/dila_full` `birth_date:"+0602-02-01", death_date:"+0664-03-10"` | Đang xảy ra |
| CN-07 | Tiểu sử nhân vật không có tiếng Việt (chỉ Hán), Cử nhân không đọc được thân thế | **P1** | `/api/persons/A000294` `bio_vi:null`, `bio_zh` 243 ký tự Hán; `/api/person/A000294/translate` (GET cache) `bio_vi:null` | Đang xảy ra |
| CN-08 | `/api/entity/<id>/unified` trả canonical Hán sai/vô nghĩa, `canonical_name_vi` rỗng, claims 0 | **P1** | `A000294`→`玉華法師`; `A024239`→`丁文南`; `A000001`→`明因妙善普濟法師`; cả 3 `canonical_name_vi:""`, `claims_count:0` | Đang xảy ra |
| CN-09 | Hai API tìm tăng nhân không nhất quán; thiếu tăng Việt phổ biến | **P1** | `/api/monk/search?q=Thích%20Minh%20Châu` 200 `count:0` **nhưng** `/api/monk-resolve?name=Thích%20Minh%20Châu` 200 `ok:true → A024239`; "Thích Nhất Hạnh"/"Thích Thanh Từ" → 0 cả hai | Đang xảy ra |
| CN-10 | Không tra được chùa Việt Nam; fuzzy khớp sai trả về chùa TQ | **P1** | `q=chùa%20Dâu` → `"Chùa Đầu Trấn"` (30.676, 120.5278); `q=chùa%20Vĩnh%20Nghiêm`/`q=Vĩnh%20Nghiêm`/`q=永嚴寺` → `count:0`; `q=Pháp%20Vân%20Tự` → `"Hoa Nghiêm Lĩnh"` | Đang xảy ra |
| CN-11 | 4 con số quảng cáo trên trang chủ mâu thuẫn với API (8.241 / 13.520 / 5.800+ / 1.200+) | **P1** | `/api/dila/places` `total:59167`; `/api/cbeta/catalog` `total:3122`; `/api/dashboard/stats` `dila_total:48673, namevi_places_total:176783` | Đang xảy ra |
| CN-12 | Không lấy được citation đầy đủ từ UI: works chỉ có 4 field, không sigla/trang; metadata có trong catalog API nhưng bị ẩn | **P1** | `/api/search?q=Kim%20Cang` works keys = `author, era, title_vi, title_zh`; `/api/cbeta/catalog?q=%E9%87%91%E5%89%9B` trả `series:T, sh_number:235, page:748` | Đang xảy ra |
| CN-13 | Kết quả trùng lặp: cùng 1 địa danh hiện 2 lần với 2 ID (2 hệ ID song song) | **P1** | `/api/search?q=Ph%C3%A1p%20Hoa` places: `PL000000057657` **và** `PL057657` (cùng tên/tọa độ); `q=Tâm%20Kinh`: `PL000000056707` **và** `PL056707` | Đang xảy ra |
| CN-14 | Hành vi dấu tiếng Việt không nhất quán, không có chế độ "không dấu"; khớp sai Đ/D | **P2** | `q=Thiếu%20Lâm` → `count:1`; `q=Thiểu%20Lâm` → `count:2`; `q=Thieu%20Lam` → `count:2`; `q=Dâu` → `"Thạch Đầu Cương"` | Đang xảy ra |
| CN-15 | Empty state không trung thực: tìm 0 kết quả vẫn hiện "KHỞI TẠO TRUY VẤN", không nói "không tìm thấy" | **P2** | `places.html:287-293` nội dung tĩnh; `places.html:1699` chỉ hiện emptyState trước khi fetch, không có nhánh 0 kết quả | Đang xảy ra |
| CN-16 | Demo "Thiếu Lâm Tự" hard-code + placeholder hứa "Tìm kinh văn, tăng nhân, địa danh" nhưng chỉ tìm địa danh | **P2** | `home.html:1124` `if (q.includes('Thiếu Lâm')…) showPlaceDemo()`; `home.html:899` placeholder; demo panel dữ liệu cứng | Đang xảy ra |
| CN-17 | Bất nhất API phụ: `catalog` bỏ qua `?search=`/`?title=`; autocomplete cắt value 20 ký tự; corpus min 2 ký tự; `/login.html` 502 trang lỗi trần | **P2** | `/api/cbeta/catalog?search=金剛` trả trang 1 không lọc; `/api/public/autocomplete?q=Duyên%20Khởi` value dài đúng 20; `/api/cbeta/corpus-search?q=佛` **400** `query_too_short`; `/daoanh/login.html` **502** | Đang xảy ra |

---

## 3. Chi tiết từng giới hạn

### CN-01 — Ô tìm kiếm trang chủ là ngõ cụt: `q` bị hiểu là ID địa danh

- **Kỳ vọng của sinh viên Cử nhân:** gõ "Kinh Kim Cang" (hoặc "Huyền Trang", "Thiếu Lâm Tự") vào ô lớn ở trang chủ → thấy danh sách kết quả để bấm vào.
- **Cách tái lập:**
  1. Mở `https://phatphaponline.org/daoanh/` (HTTP 200, 36.638 B).
  2. Gõ "Kinh Kim Cang" → Enter.
  3. Quan sát URL sau redirect: `https://phatphaponline.org/daoanh/places?q=Kinh%20Kim%20Cang` (HTTP 200, **761.121 B**).
  4. Thử API mà URL đó sẽ gọi: `https://phatphaponline.org/daoanh/api/places/Kinh%20Kim%20Cang`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/` **200**; inline script duy nhất của trang: `if (q.includes('Thiếu Lâm') || q.includes('少林')) { showPlaceDemo(); return; } window.location.href = '/daoanh/places?q=' + encodeURIComponent(q);` [SUY LUẬN TỪ CODE: `daoanh/home.html:1120-1128`, đoạn này **có nguyên văn trong HTML live**].
  - [ĐO ĐƯỢC] `GET /daoanh/places?q=Kinh%20Kim%20Cang` **200**, `bytes=761121`, `md5=36f6444cc5bb` — **trùng khít** `GET /daoanh/places` (`bytes=761121`, cùng md5). Server nginx/1.24.0 trả file tĩnh, **bỏ qua `q`** ⇒ không có kết quả nào được render phía server.
  - [SUY LUẬN TỪ CODE] Trang places đọc tham số nhưng coi `q` là **ID thực thể**: `const selectParam = up.get('select') || up.get('q'); … selectItem(selectParam, null, null);` [SUY LUẬN TỪ CODE: `daoanh/places.html:11602,11623,11627`; đoạn tương đương có trong HTML live].
  - [SUY LUẬN TỪ CODE] `selectItem()` gọi `fetch('/daoanh/api/places/', id)` [SUY LUẬN TỪ CODE: `places.html:1413`] và khi lỗi thì `if (!json.ok || !json.data) return;` — **im lặng thoát** [SUY LUẬN TỪ CODE: `places.html:1417`], để panel ở trạng thái `itemId = "Kinh Kim Cang"`, `itemNameVi = "Đang tải..."` [SUY LUẬN TỪ CODE: `places.html:1226,1228`].
  - [ĐO ĐƯỢC] `GET /daoanh/api/places/Kinh%20Kim%20Cang` → **404** `{"error": "Place not found", "ok": false}`.
- **Phân loại:** lỗi UI + thiếu tính năng (không có trang kết quả tìm kiếm; tham số bị dùng sai nghĩa).
- **Ảnh hưởng tới cấp Cử nhân:** **chặn hoàn toàn** mọi tra cứu bắt đầu từ trang chủ — kể cả khi gõ đúng tên địa danh ("Thiếu Lâm Tự"), vì chuỗi văn bản không phải ID. Sinh viên thấy panel trống/"Đang tải…" không lỗi, tưởng site treo.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Ô tìm kiếm trang chủ gọi endpoint tìm kiếm tổng hợp (`/daoanh/api/search?q=`) và render trang kết quả 3 nhóm (kinh/tăng nhân/địa danh), mỗi kết quả có `href` trỏ route trả **HTTP 200**; HOẶC ghi rõ nhãn "Tìm địa danh" và nếu `q` không phải ID thì đưa vào ô tìm của `places.html` thay vì `selectItem`.
  - (b) Không có kết quả → hiện "Không tìm thấy «q»" + gợi ý (xem CN-15).
  - **AC:** với `q ∈ {"Kinh Kim Cang","Huyền Trang","Thiếu Lâm Tự"}`: trong ≤ 3 s hiện ít nhất 1 kết quả đúng loại; 100% link kết quả trả < 400; `q` rác ("zzzz") hiện thông báo không-kết-quả, không kẹt "Đang tải".
- **Ưu tiên:** **P0**.

### CN-02 — Không có đường tra cứu kinh điển theo tên Việt

- **Kỳ vọng của sinh viên Cử nhân:** vào mục "Đại Tạng" (thẻ trên trang chủ) hoặc gõ "Kinh Pháp Hoa"/"Bát Nhã Tâm Kinh" để xem mục lục kinh, dịch giả, đường đọc.
- **Cách tái lập:**
  1. `GET https://phatphaponline.org/daoanh/tripitaka` (đích của thẻ "Đại Tạng").
  2. `GET https://phatphaponline.org/daoanh/api/search?q=Kinh%20Ph%C3%A1p%20Hoa`.
  3. `GET https://phatphaponline.org/daoanh/api/cbeta/texts` (danh sách bộ đã index).
  4. `GET https://phatphaponline.org/daoanh/api/cbeta/corpus-search?q=Kinh%20Kim%20Cang`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/tripitaka` → **404** (nginx, 162 B) — không có trang mục lục kinh.
  - [ĐO ĐƯỢC] `GET /daoanh/api/search?q=Kinh%20Ph%C3%A1p%20Hoa` → **200** `{"monks":[],"places":[{…"Pháp Hoa Kinh Đường"…}],"success":true,"works":[]}` — tên kinh quen thuộc **không ra bộ kinh nào**. `q=Kinh%20Kim%20Cang` → 1 work nhưng là *Kim Cang Đảnh Kinh Kim Cang Giới Đại* (Bất Không), không phải *Kim Cang Bát Nhã Ba La Mật Kinh*.
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/texts` → **200** `{"count":5, …}` (Cảnh Đức Truyền Đăng Lục, Tục/Tống Cao Tăng Truyện, Vô Lượng Thọ Kinh Ưu Ba Đề Xá, Đại Minh Cao Tăng Truyện) — **không có kinh chính nào**.
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/corpus-search?q=Kinh%20Kim%20Cang` → **200** `{"coverage":{"catalog_total":3122,"texts_searchable":5,"passages_searchable":72628},"result_count":0}`.
  - [SUY LUẬN TỪ CODE] `/api/search` chỉ được `daoanh/index.html` gọi — **không phải** trang chủ live (`home.html`); `places.html` chỉ có ô Hán văn "Tìm trong Đại Tạng" nằm trong tab `tp-daitang` của panel chi tiết (phải chọn 1 thực thể trước) [SUY LUẬN TỪ CODE: `daoanh/places.html:477-490`; `daoanh/home.html:1128`].
- **Phân loại:** thiếu tính năng (thiếu trang mục lục + thiếu UI gọi API tổng hợp).
- **Ảnh hưởng tới cấp Cử nhân:** muốn tra một bộ kinh, sinh viên buộc phải biết chữ Hán và biết API — không thể làm bài. Đây là nhu cầu N1, phổ biến nhất của năm 1–2.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Dựng trang "Đại Tạng" (hoặc tab tìm kinh trong ô tìm chung) dùng `/api/search` + `/api/cbeta/catalog?q=`, hiển thị `title_vi`, `title_zh`, `translator_vi`, `dynasty_vi`, `sigla`, `page`; với mỗi bộ ghi rõ "có toàn văn / chỉ mục lục".
  - **AC:** `q="Kinh Pháp Hoa"` → ≥1 bộ kinh đúng trong 2 s; `q="金剛經"` → mục lục `T08n0235` (xem CN-12); `q="Bát Nhã Tâm Kinh"` → có ít nhất bản kinh gốc tách khỏi các bản chú giải.
- **Ưu tiên:** **P0**.

### CN-03 — 5/6 thẻ chủ đề trang chủ là ngõ cụt

- **Kỳ vọng của sinh viên Cử nhân:** 6 thẻ "Địa Danh / Đại Tạng / Tu Sĩ / Truyền Thừa / Niên Đại / Đồ Thị" đều dẫn tới nội dung tương ứng.
- **Cách tái lập:** bấm lần lượt 6 thẻ trên `https://phatphaponline.org/daoanh/` (hoặc GET các URL tương ứng).
- **Kết quả thực tế (bằng chứng):**

| Thẻ | URL | HTTP | Ghi chú |
|---|---|---|---|
| Địa Danh | `/daoanh/places` | **200** | hoạt động |
| Đại Tạng | `/daoanh/tripitaka` | **404** | nginx, 162 B |
| Tu Sĩ | `/daoanh/people` | **404** | nginx, 162 B |
| Truyền Thừa | `/daoanh/lineage` (không id) | **200** | nhưng JS rơi vào nhánh `notFound` |
| Niên Đại | `/daoanh/timeline` | **404** | nginx, 162 B |
| Đồ Thị Quan Hệ | `/daoanh/graph` | **404** | nginx, 162 B |

  - [ĐO ĐƯỢC] `GET /daoanh/people` **404**, body `<html>…<h1>404 Not Found</h1>…nginx/1.24.0 (Ubuntu)…` (162 B); tương tự `/tripitaka`, `/timeline`, `/graph`.
  - [ĐO ĐƯỢC] `GET /daoanh/lineage` **200** (7.202 B); [SUY LUẬN TỪ CODE] `if (!name && !idParam) { … document.getElementById('notFound').classList.remove('hidden'); return; }` → thẻ không kèm `id` nên **luôn** hiện "Không tìm thấy thiền sư này trong cơ sở dữ liệu." [SUY LUẬN TỪ CODE: `daoanh/lineage.html:81-86`].
  - [SUY LUẬN TỪ CODE] `daoanh/` **không có** `people.html`, `tripitaka.html`, `timeline.html`, `graph.html`; `app.py` không có route cho 4 đường dẫn này ⇒ 404 là tất yếu, không phải sự cố tạm thời.
- **Phân loại:** thiếu tính năng / lỗi UI (link chết) — đã được Lead ghi ở `00-SITE-HEALTH.md` SH-01, ở đây bổ sung góc nhìn Cử nhân + bằng chứng nhánh `notFound`.
- **Ảnh hưởng tới cấp Cử nhân:** sinh viên mất niềm tin ngay cửa vào; đặc biệt thẻ "Tu Sĩ" và "Truyền Thừa" — hai nhu cầu N3, N5 — không có đích.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Với 4 thẻ 404: hoặc dựng trang đích tối thiểu (landing + danh sách thật + tìm kiếm), hoặc **ẩn thẻ** khỏi trang chủ.
  - (b) `/daoanh/lineage` không có `id`: hiện ô nhập/ghép nối tới danh sách tăng nhân thay vì thông báo "không tìm thấy".
  - **AC:** 6/6 thẻ trả HTTP < 400; `/daoanh/lineage` (không tham số) hiển thị hướng dẫn chọn nhân vật + ô tìm; có test crawl link nội bộ trong CI.
- **Ưu tiên:** **P0**.

### CN-04 — Không có toàn văn kinh để đọc; chỉ có snippet 5 bộ sử/truyện

- **Kỳ vọng của sinh viên Cử nhân:** từ trang kinh bấm "Đọc toàn văn" (hoặc bản dịch Việt) để đọc/trích dẫn.
- **Cách tái lập:**
  1. `GET /daoanh/api/cbeta/text/T08n0235/browse` (Kim Cang Bát Nhã Ba La Mật Kinh).
  2. `GET /daoanh/api/cbeta/text/T51n2076/browse`.
  3. `GET /daoanh/api/cbeta/passages/51190/units`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/text/T08n0235/browse` → **404** `{"error":"sigla_not_found","ok":false}` — bộ kinh Kim Cang **không được import**.
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/text/T51n2076/browse` → **200** `{"coverage":{"complete_text":false,"granularity":"context_snippet","note":"Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn.","total_mentions":22275,"unique_pages":492}, "items":[{"snippet":"皇上睿文繼志而序聖教繹宗風…"}]}`.
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/passages/51190/units` → **200** `{"work_id":"T50n2060","coverage":{"total":9316,"translated":11,"missing":9305,"reviewed":0},"units":[]}` — độ phủ bản dịch **11/9316 (0,12%)**, và `units` rỗng.
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/corpus-search?q=%E9%87%91%E5%89%9B` ("金剛") → **200** `result_count:30`, các hit là trích từ 續高僧傳/Tống Cao Tăng Truyện, **không phải kinh Kim Cang**.
- **Phân loại:** thiếu dữ liệu/toàn văn (không phải lỗi UI).
- **Ảnh hưởng tới cấp Cử nhân:** nhu cầu cốt lõi "đọc được" của chuẩn Cử nhân **không đạt**; sinh viên không thể đọc, không thể đối chiếu, không thể trích dẫn bản văn.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Trên UI ghi rõ coverage từng bộ: "đã có toàn văn / chỉ có đoạn trích"; không mở tab "Đại Tạng"/"CBETA" trống mà không giải thích.
  - (b) Bổ sung tối thiểu 3 bộ kinh phổ thông cho giáo trình Cử nhân (Kim Cang `T08n0235`, Pháp Hoa `T09n0262`, Bát Nhã Tâm Kinh `T08n0251`) có toàn văn + phân trang.
  - **AC:** bấm "Đọc toàn văn" một bộ kinh phổ thông → 200, hiển thị ≥ 200 chữ Hán liên tục (không phải snippet 200 ký tự), có điều hướng quyển/trang; số bộ đọc được toàn văn công bố trên UI khớp `coverage`.
- **Ưu tiên:** **P0**.

### CN-05 — Từ điển Phật học có API hoàn chỉnh nhưng không có cửa vào nào trên giao diện

- **Kỳ vọng của sinh viên Cử nhân:** gõ "Bát Nhã" / "Vô Ngã" / "Niết Bàn" ở một ô tra từ điển, thấy nghĩa tiếng Việt + nguồn.
- **Cách tái lập:**
  1. `GET /daoanh/api/glossary?term=B%C3%A1t%20Nh%C3%A3`.
  2. `GET /daoanh/api/glossary?term=Ni%E1%BA%BFt%20B%C3%A0n`.
  3. Thử các đường UI: `/daoanh/glossary`, `/daoanh/lexicon`, `/daoanh/dictionary`, `/daoanh/search`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/api/glossary?term=B%C3%A1t%20Nh%C3%A3` → **200** `{"matches":[{"term":"Bát Nhã","definition":"Prajñā (S), Hannya (J).","source_label":"Từ điển PG VN (Tu Dien Da Ngon Ngu - Cs Minh Thong)"}, {"term":"Bát Nhã","definition":"般若. Phiên âm tiếng Phạn, có nghĩa là thông tuệ…","source_label":"…Nguyen Quoc Hung"}, …],"ok":true,"total":4}`.
  - [ĐO ĐƯỢC] `GET /api/glossary?term=Ni%E1%BA%BFt%20B%C3%A0n` → **200**, 7.838 ký tự JSON, định nghĩa dài, nhiều nguồn.
  - [ĐO ĐƯỢC] `/daoanh/glossary` → **404**; `/daoanh/lexicon` → **404**; `/daoanh/dictionary` → **404**; `/daoanh/search` → **404**. `GET /daoanh/api/glossary` (thiếu `term`) → **400** `{"error":"Thiếu tham số term.","ok":false}`.
  - [SUY LUẬN TỪ CODE] Trong HTML live của `places.html`: có định nghĩa `function bindGlossarySpans(container)` và `openGlossaryPopup(term)`, nhưng `bindGlossarySpans(` xuất hiện **đúng 1 lần** (chỗ định nghĩa — **không có call site**), và `class="da-glossary"` xuất hiện **0 lần** ⇒ popup không bao giờ được kích hoạt [SUY LUẬN TỪ CODE: `daoanh/places.html:10731-10745`, đối chiếu bản live].
- **Phân loại:** thiếu tính năng trên UI (dữ liệu/API đã tốt) + code chết.
- **Ảnh hưởng tới cấp Cử nhân:** nhu cầu N2 không có đường đáp ứng; sinh viên phải tra từ điển ngoài hệ thống. Đáng tiếc vì API đã cho kết quả đúng chuẩn "dễ hiểu, có nguồn".
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Thêm mục "Từ điển" (menu hoặc trong ô tìm chung) gọi `/api/glossary?term=`, hiển thị `term`, `definition`, `source_label`; hoặc gắn popup vào thuật ngữ trong tiểu sử/kinh văn (kích hoạt `bindGlossarySpans` sau mỗi lần render).
  - **AC:** gõ "Bát Nhã", "Vô Ngã", "Duyên Khởi", "Niết Bàn" trên UI → mỗi từ ≥ 1 định nghĩa tiếng Việt + tên nguồn; không từ nào trả 404.
- **Ưu tiên:** **P1**.

### CN-06 — Năm sinh/mất nhân vật bị lấy nhầm số thư mục (Huyền Trang: 2024–1787)

- **Kỳ vọng của sinh viên Cử nhân:** hồ sơ Huyền Trang ghi 602–664, không có con số vô lý.
- **Cách tái lập:** `GET /daoanh/api/person/A000294/profile`; `GET /daoanh/api/person/A000294/dila_full`; `GET /daoanh/api/person/A000294/translate`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/api/person/A000294/profile` → **200**, `"profile":{"bio":"俗姓陳，大慈恩寺僧人…（佛光：2024；佛百：1787.1；疑年錄：99；…）","birth_year":2024,"death_year":1787,"name_vi":"Huyền Trang","dynasty":"唐"}`.
  - [ĐO ĐƯỢC] Cùng người, `GET /daoanh/api/person/A000294/dila_full` → **200** `"birth_date":"+0602-02-01 ~ +0603-02-18","death_date":"+0664-03-10"`.
  - Nhận định: `2024` và `1787` chính là số hiệu thư mục trong câu trích dẫn "佛光：2024；佛百：1787.1" bị parser gán thành năm sinh/năm mất. [SUY LUẬN TỪ CODE: trường `birth_year/death_year` lấy từ `people` (xem `app.py` API person), trong khi DILA XML có `birth_date` đúng — hai nguồn không đồng bộ].
- **Phân loại:** lỗi dữ liệu.
- **Ảnh hưởng tới cấp Cử nhân:** **sai lệch** trầm trọng — nếu sinh viên tin hồ sơ, bài tập sẽ ghi "Huyền Trang (2024–1787)"; giáo viên mất niềm tin vào cả site. Vi phạm trực tiếp chuẩn "không sai lệch".
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Sửa nguồn năm: ưu tiên `dila_full.birth_date/death_date`; thêm guard: không hiển thị năm nếu `year < 500` hoặc `> 2100` khi dynasty là cổ.
  - (b) API trả rõ `birth_year_source` để UI badge nguồn.
  - **AC:** `GET /api/person/A000294/profile` trả `birth_year:602`, `death_year:664`; test tự động chặn mọi `birth_year > 2100` hoặc `death_year < birth_year`; UI hiển thị "602–664".
- **Ưu tiên:** **P1**.

### CN-07 — Tiểu sử nhân vật chỉ có chữ Hán, không có bản Việt

- **Kỳ vọng của sinh viên Cử nhân:** mở hồ sơ nhân vật đọc được tiểu sử tiếng Việt.
- **Cách tái lập:** `GET /daoanh/api/persons/A000294`; `GET /daoanh/api/person/A000294/translate` (GET = cache-only, không ghi); lặp với `A024239`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/api/persons/A000294` → **200** `{"bio_vi":null,"bio_vi_status":null,"bio_zh":"俗姓陳，大慈恩寺僧人，唯識宗創始人，世稱唐三藏。…","biography":"俗姓陳…","name_vi":"Huyền Trang"}`.
  - [ĐO ĐƯỢC] `GET /daoanh/api/person/A000294/translate` → **200** `{"bio_vi":null,"from_cache":false,"ok":true}`; `A024239` → `{"bio_vi":null,"from_cache":false,"ok":true}`.
  - [ĐO ĐƯỢC] `GET /daoanh/api/person/A000294/dila_translate` → **200** `{"from_cache":false,"ok":true,"vi":null}`.
  - [SUY LUẬN TỪ CODE] UI chỉ hiển thị bản dịch khi cache có sẵn; muốn dịch phải gọi POST (LLM/Gemini) [SUY LUẬN TỪ CODE: `daoanh/places.html:7358-7364`, route `app.py` `…/translate` GET = cache-only].
- **Phân loại:** thiếu dữ liệu (bản dịch) + thiếu tính năng (UI không có nút "Dịch" rõ ràng cho Cử nhân).
- **Ảnh hưởng tới cấp Cử nhân:** nhu cầu N3 "thân thế" không đọc được; buộc phải dịch ngoài hệ thống → vi phạm "dễ hiểu".
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Có bản dịch Việt cho nhân vật trọng tâm chương trình (tối thiểu 50 vị), hoặc hiện rõ trạng thái "chưa có bản dịch" + nút yêu cầu dịch (POST) có phản hồi < 30 s.
  - **AC:** mở hồ sơ Huyền Trang thấy tiểu sử tiếng Việt hoặc nhãn trạng thái; `GET /api/persons/<id>` trả `bio_vi` khác null cho ≥50 nhân vật trọng tâm; có badge nguồn bản dịch (AI/người).
- **Ưu tiên:** **P1**.

### CN-08 — `/api/entity/<id>/unified` trả canonical Hán sai/vô nghĩa, không có tên Việt

- **Kỳ vọng của sinh viên Cử nhân:** với Huyền Trang, tên chuẩn hiển thị là "Huyền Trang"; với Thích Minh Châu là "Thích Minh Châu".
- **Cách tái lập:** `GET /daoanh/api/entity/A000294/unified`; `GET /daoanh/api/entity/A024239/unified`; `GET /daoanh/api/entity/A000001/unified`; so với `GET /daoanh/api/monk/search?q=Huy%E1%BB%81n%20Trang`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `A000294`: `"entity":{"canonical_label":"玉華法師","canonical_name":"玉華法師","canonical_name_vi":"","cbeta_mention_count":1,"entity_type":"PERSON"}`, `claims_count:0`, `conflicts_count:0`.
  - [ĐO ĐƯỢC] `A024239` (Thích Minh Châu): canonical `"丁文南"`, `canonical_name_vi:""`.
  - [ĐO ĐƯỢC] `A000001`: canonical `"明因妙善普濟法師"`, `canonical_name_vi:""`.
  - [ĐO ĐƯỢC] Cùng lúc `GET /api/monk/search?q=Huy%E1%BB%81n%20Trang` trả `"name_vi":"Huyền Trang","name_zh":"玄奘"` — tức hệ thống **biết** tên đúng nhưng endpoint unified không dùng.
  - [ĐO ĐƯỢC] Với địa danh thì OK: `GET /api/entity/PL000000023255/unified` → `"canonical_name_vi":"Thiếu Lâm Tự"`.
  - [SUY LUẬN TỪ CODE] Trang places hiển thị tên theo `ent.canonical_name_vi || ent.canonical_name || id` [SUY LUẬN TỪ CODE: `daoanh/places.html:1289-1290`] ⇒ mở một thực thể PERSON qua đường `?q=<id>` sẽ hiện **玉華法師** ở ô tên Việt.
- **Phân loại:** lỗi API / lỗi dữ liệu (chọn alias/lay name làm canonical; `canonical_name_vi` rỗng).
- **Ảnh hưởng tới cấp Cử nhân:** mọi client dùng endpoint này (kể cả đội Planning sau này) sẽ hiển thị **sai danh tính** — đặc biệt nghiêm trọng với nhân vật tôn giáo (tên pháp danh). [CHƯA KIỂM CHỨNG: chưa xác nhận được bằng mắt trên UI vì không có browser — chỉ suy ra từ code + response].
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) `canonical_name_vi` phải lấy từ `people.name_vi` (đã có 100% theo ghi chú `app.py`), `canonical_name` = `name_zh`; alias/alt_names trả trong mảng `aliases` riêng, có nguồn.
  - (b) Không trả `claims_count:0` khi có dữ liệu nguồn (cần hiển thị badge "chưa tổng hợp" thay vì 0).
  - **AC:** `GET /api/entity/A000294/unified` → `canonical_name_vi:"Huyền Trang"`, `canonical_name:"玄奘"`; `A024239` → `"Thích Minh Châu"`; test so khớp unified với `monk/search` cho 20 nhân vật mẫu.
- **Ưu tiên:** **P1**.

### CN-09 — Hai API tìm tăng nhân không nhất quán; thiếu tăng Việt phổ biến

- **Kỳ vọng của sinh viên Cử nhân:** gõ "Thích Minh Châu" ở ô tìm của trang places → ra hồ sơ; gõ "Thích Nhất Hạnh" → ra hồ sơ.
- **Cách tái lập:** so sánh `GET /daoanh/api/monk/search?q=<tên>` với `GET /daoanh/api/monk-resolve?name=<tên>` cho 4 tên: Huyền Trang, Thích Minh Châu, Thích Thanh Từ, Thích Nhất Hạnh.
- **Kết quả thực tế (bằng chứng):**

| Tên gõ | `/api/monk/search` | `/api/monk-resolve` |
|---|---|---|
| Huyền Trang | **200** `count:1` → A000294 | **200** `ok:true` → A000294 |
| Thích Minh Châu | **200** `count:0` | **200** `ok:true` `match_type:"exact_name_vi"` → A024239 (dynasty 越南) |
| Thích Nhất Hạnh | **200** `count:0` | **200** `{"error":"not found","ok":false}` |
| Thích Thanh Từ | **200** `count:0` | **200** `{"error":"not found","ok":false}` |

  - [SUY LUẬN TỪ CODE] `doSearch()` của trang places gọi **cả hai** endpoint nhưng nếu `monk-resolve` fail thì chỉ còn địa danh [SUY LUẬN TỪ CODE: `daoanh/places.html:1702-1717`]; nếu UI khác chỉ dùng `monk/search` thì luôn miss tên Việt.
  - [ĐO ĐƯỢC] "Thích Nhất Hạnh" không tồn tại trong hệ thống (cả hai endpoint đều không thấy) ⇒ giới hạn **phủ dữ liệu tăng nhân Việt**, không chỉ lỗi API.
- **Phân loại:** lỗi API (bất nhất) + thiếu dữ liệu.
- **Ảnh hưởng tới cấp Cử nhân:** các vị tăng Việt trong giáo trình (Minh Châu, Thanh Từ, Nhất Hạnh) tra không ra hoặc ra không ổn định — đúng nhu cầu N3.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Hợp nhất logic tìm: 1 endpoint công khai trả cùng tập kết quả, có `match_type` (exact/fuzzy/alias); UI chỉ gọi 1 endpoint.
  - (b) Bổ sung tối thiểu 10 vị tăng Việt phổ biến (có nguồn) hoặc ghi rõ "chưa có dữ liệu Việt Nam".
  - **AC:** 4 tên trên trả cùng kết quả ở cả 2 endpoint; "Thích Minh Châu"/"Thích Nhất Hạnh"/"Thích Thanh Từ" → ≥1 hồ sơ có `name_vi` đúng hoặc thông báo "chưa có dữ liệu".
- **Ưu tiên:** **P1**.

### CN-10 — Không tra được chùa Việt Nam; fuzzy trả về chùa Trung Quốc (sai)

- **Kỳ vọng của sinh viên Cử nhân:** gõ "chùa Dâu", "chùa Vĩnh Nghiêm" → ra đúng chùa; gõ sai dấu/không dấu vẫn gợi ý đúng.
- **Cách tái lập:** `GET /daoanh/api/places/search?q=<từ khoá>&limit=5` với: `chùa Dâu`, `chùa Vĩnh Nghiêm`, `Vĩnh Nghiêm`, `永嚴寺`, `Pháp Vân Tự`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `q=chùa%20D%C3%A2u` → **200** `{"count":1,"results":[{"id":"PL000000012928","name_vi":"Chùa Đầu Trấn","name_zh":"爐頭鎮","lat":30.676,"lng":120.5278,"type":"town"}]}` — trả về một **thị trấn ở Trung Quốc**, không phải chùa Dâu (Bắc Ninh).
  - [ĐO ĐƯỢC] `q=ch%C3%B9a%20V%C4%A9nh%20Nghi%C3%AAm` → **200** `{"count":0}`; `q=V%C4%A9nh%20Nghi%C3%AAm` → **200** `{"count":0}`; `q=%E6%B0%B8%E5%9A%B4%E5%AF%BA` ("永嚴寺") → **200** `{"count":0}`.
  - [ĐO ĐƯỢC] `q=Ph%C3%A1p%20V%C3%A2n%20T%E1%BB%B1` → **200** trả `"Hoa Nghiêm Lĩnh"` (name_zh 法雲寺, Sơn Tây, TQ) — không phải chùa Pháp Vân (Dâu).
  - [ĐO ĐƯỢC] `q=D%C3%A2u` → trả `"Thạch Đầu Cương"`, `"Nghĩa Đầu Khẩu"`… (khớp mờ theo "Đầu").
- **Phân loại:** lỗi dữ liệu (thiếu địa danh VN) + lỗi API (fuzzy khớp sai, không có ngưỡng chất lượng).
- **Ảnh hưởng tới cấp Cử nhân:** tra chùa Việt — nhu cầu N4 rất phổ biến — nhận **kết quả sai** thay vì "không có dữ liệu"; sinh viên có thể trích dẫn nhầm địa danh.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Bổ sung dữ liệu địa danh Việt Nam (tối thiểu các chùa trong giáo trình) **hoặc** chặn fuzzy dưới ngưỡng: nếu không có match chính xác thì trả 0 kèm thông báo "chưa có dữ liệu Việt Nam".
  - (b) Không trả kết quả chỉ vì trùng chuỗi con 1 âm tiết ("Dâu"→"Đầu").
  - **AC:** "chùa Dâu" → đúng chùa Dâu (hoặc 0 kèm thông báo), không bao giờ trả `Chùa Đầu Trấn`; "chùa Vĩnh Nghiêm"/"Thiếu Lâm Tự" → kết quả đúng loại; có test hồi quy cho 10 địa danh VN.
- **Ưu tiên:** **P1**.

### CN-11 — Bốn con số quảng cáo trên trang chủ mâu thuẫn với mọi `count` API

- **Kỳ vọng của sinh viên Cử nhân:** con số trên trang chủ phản ánh dữ liệu thực, bấm được tới danh sách.
- **Cách tái lập:** đọc 4 số trên `https://phatphaponline.org/daoanh/` rồi gọi các API đếm.
- **Kết quả thực tế (bằng chứng):**

| Chỉ số | Trang chủ (HTML) | API đo được (2026-10-25) |
|---|---|---|
| Địa danh | `8,241` (`home.html:1005`; hero ghi `8,000+` ở `:896`) | `/api/dila/places` **total 59.167**; `/api/dashboard/stats` `namevi_places_total 176.783` |
| Mục lục kinh | `13,520` (`home.html:1010`) | `/api/cbeta/catalog` **total 3.122** (`pages:32`) |
| Tu sĩ | `5,800+` (`home.html:1015`) | `/api/persons/browse` `total_people 48.673`; `/api/dashboard/stats` `marcus_monks 11.300` |
| Dòng truyền thừa | `1,200+` (`home.html:1020`) | `/api/persons/browse` `with_lineage 18.121`; `/api/dashboard/stats` `marcus_edges 11.169` |

  - [ĐO ĐƯỢC] `GET /daoanh/api/dila/places?limit=2` → `{"total":59167}`; `GET /daoanh/api/dashboard/stats` → `{"dila_total":48673,"namevi_places_total":176783,"marcus_monks":11300,"marcus_edges":11169}`; `GET /daoanh/api/cbeta/catalog?limit=1` → `{"total":3122,"pages":32}`; `GET /daoanh/api/persons/browse?limit=3` → `{"counts":{"total_people":48673,"with_lineage":18121}}`.
- **Phân loại:** sai lệch số liệu.
- **Ảnh hưởng tới cấp Cử nhân:** sinh viên trích dẫn con số site công bố sẽ sai; không có ngày chốt số/phiên bản dữ liệu → không kiểm chứng được.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Một nguồn số liệu duy nhất: mỗi số trên UI lấy động từ API tương ứng, có `dataset_version` + ngày, bấm được tới danh sách.
  - **AC:** mọi số trên `/daoanh/` khớp `count/total` của API tương ứng ở cùng thời điểm (test so khớp tự động); không còn chữ "8,241/13,520/5,800+" hard-code (`home.html:1005-1020`).
- **Ưu tiên:** **P1**.

### CN-12 — Không lấy được citation đầy đủ: works thiếu sigla/trang; metadata bị ẩn sau API

- **Kỳ vọng của sinh viên Cử nhân:** copy được: tên kinh (Việt + Hán), dịch giả, triều đại, CBETA sigla, số trang, nguồn link.
- **Cách tái lập:**
  1. `GET /daoanh/api/search?q=Kim%20Cang`.
  2. `GET /daoanh/api/cbeta/catalog?q=%E9%87%91%E5%89%9B`.
  3. Thử đường UI để xem mục lục: `GET /daoanh/tripitaka` (xem CN-02).
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `GET /daoanh/api/search?q=Kim%20Cang` → works mỗi phần tử chỉ có **4 field**: `{"author":"…","era":"…","title_vi":"…","title_zh":"…"}` — **không có `id`, `sigla`, `page`, `year`** ⇒ bấm/kết xuất không có đích.
  - [ĐO ĐƯỢC] `GET /daoanh/api/cbeta/catalog?q=%E9%87%91%E5%89%9B` → **200** phần tử đầu: `{"cbeta_ref":null,"juans":1,"page":"748","q_number":"8","series":"T","sh_number":"235","title_vi":"Kim Cang Bát Nhã Ba La Mật Kinh","title_zh":"金剛般若波羅蜜經 (一卷) (姚秦","translator_vi":"Cưu Ma La Thập","dynasty_vi":"Diêu Tần"}` — **metadata citation có đủ** (T. 8, no. 235, p. 748) nhưng chỉ nằm trong API, không có UI.
  - [ĐO ĐƯỢC] Trang 1 của catalog (`limit=100`): **100/100** bản ghi có `cbeta_ref: null`; `title_zh` bị cắt cụt giữa chuỗi (`"…(一卷) (姚秦"` thiếu ngoặc đóng).
- **Phân loại:** thiếu tính năng (không có trang chi tiết kinh/citation) + lỗi dữ liệu (`cbeta_ref null`, `title_zh` cụt).
- **Ảnh hưởng tới cấp Cử nhân:** không hoàn thành được bài tập có yêu cầu trích dẫn; nếu tự ghép từ API thì dễ sai (thiếu trang/sigla, tên bị cụt).
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Trang chi tiết kinh hiển thị đủ trường + nút "Sao chép trích dẫn" theo mẫu `Tên kinh (Hán) — dịch giả, triều đại — CBETA T{số}, no.{sh}, p.{page} — link`.
  - (b) `cbeta_ref` phải sinh được từ `series+q_number+sh_number+page` (hoặc map sang `T08n0235`), `title_zh` không cắt cụt.
  - **AC:** `q="Kim Cang"` → trang kinh có `T08n0235`, `page 748`, `translator "Cưu Ma La Thập"`, nút copy citation cho ra chuỗi đúng; 0 bản ghi hiển thị `title_zh` thiếu ngoặc `)`.
- **Ưu tiên:** **P1**.

### CN-13 — Kết quả trùng lặp: cùng một địa danh hiện 2 lần với 2 ID khác nhau

- **Kỳ vọng của sinh viên Cử nhân:** mỗi thực thể xuất hiện đúng 1 lần, ID duy nhất.
- **Cách tái lập:** `GET /daoanh/api/search?q=Ph%C3%A1p%20Hoa`; `GET /daoanh/api/search?q=T%C3%A2m%20Kinh`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `q=Ph%C3%A1p%20Hoa` → `places` chứa **cả** `{"id":"PL000000057657","name_vi":"Pháp Hoa Kinh Đường","name_zh":"法華經堂","province":"河南省"}` **và** `{"id":"PL057657","name_vi":"Pháp Hoa Kinh Đường","name_zh":"法華經堂", …}` — cùng tên, cùng toạ độ `34.791485,114.348564`, khác ID.
  - [ĐO ĐƯỢC] `q=T%C3%A2m%20Kinh` → `PL000000056707` ("Kính Tâm Thất", 30.386138,119.760628) **và** `PL056707` (cùng tên, cùng toạ độ).
  - [ĐO ĐƯỢC] Tương tự với `q=Thiểu%20Lâm`: 2 kết quả, trong đó 1 kết quả "Thiếu Lâm Cung" ở Đài Loan.
- **Phân loại:** lỗi dữ liệu (2 hệ ID song song: `PL0000000xxxxx` dài và `PLxxxxxx` ngắn).
- **Ảnh hưởng tới cấp Cử nhân:** cùng một chùa hiện 2 dòng → sinh viên tưởng có 2 chùa khác nhau; làm loãng kết quả tìm kiếm và gây trích dẫn trùng.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Chuẩn hoá 1 ID canonical cho địa danh; API tìm kiếm dedupe theo ID chuẩn (hoặc theo `name_zh + toạ độ`), giữ bản ghi nguồn tốt nhất.
  - **AC:** `q="Pháp Hoa"` và `q="Tâm Kinh"` → mỗi thực thể 1 dòng duy nhất; test đếm: không có 2 kết quả cùng `(name_zh, lat, lng)`.
- **Ưu tiên:** **P1**.

### CN-14 — Hành vi dấu tiếng Việt không nhất quán, không có chế độ "không dấu"

- **Kỳ vọng của sinh viên Cử nhân:** gõ sai dấu hoặc không dấu vẫn ra kết quả đúng (thói quen gõ điện thoại).
- **Cách tái lập:** `GET /daoanh/api/places/search?q=%C4%91úng-d%E1%BA%A5u` với `Thiếu Lâm`, `Thiểu Lâm`, `Thieu Lam`; và `q=Dâu`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `q=Thi%E1%BA%BFu%20L%C3%A2m` ("Thiếu Lâm") → **200** `count:1` (chỉ PL000000023255).
  - [ĐO ĐƯỢC] `q=Thi%E1%BB%83u%20L%C3%A2m` ("Thiểu Lâm", sai dấu) → **200** `count:2` (thêm "Thiếu Lâm Cung" PL000000052728, Đài Loan).
  - [ĐO ĐƯỢC] `q=Thieu%20Lam` (không dấu) → **200** `count:2` (giống sai dấu).
  - [ĐO ĐƯỢC] `q=D%C3%A2u` → **200** `"Thạch Đầu Cương"`, `"Nghĩa Đầu Khẩu"`… — khớp cả khi chỉ trùng âm tiết không dấu.
- **Phân loại:** lỗi API/tiện ích (thiếu chuẩn hoá dấu, thiếu option "không dấu"; kết quả phụ thuộc dấu).
- **Ảnh hưởng tới cấp Cử nhân:** cùng một từ khoá cho 1 hoặc 2 kết quả tuỳ dấu → không đoán được kết quả; nếu gõ đúng mà lại thiếu kết quả thì sinh viên tưởng site không có dữ liệu.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Chuẩn hoá NFD + bỏ dấu cho cả query và index; xếp hạng: khớp đúng dấu > không dấu > mờ; công tắc "Tìm không dấu" trên UI.
  - **AC:** `Thiếu Lâm`, `Thiểu Lâm`, `Thieu Lam` trả **cùng** kết quả (≥1, đúng chùa); có thông báo "đã tìm cả không dấu".
- **Ưu tiên:** **P2**.

### CN-15 — Empty state không trung thực: 0 kết quả vẫn hiện "KHỞI TẠO TRUY VẤN"

- **Kỳ vọng của sinh viên Cử nhân:** khi không có kết quả, hiện "Không tìm thấy «x»" + gợi ý; khi lỗi mạng, hiện lỗi.
- **Cách tái lập:** mở `/daoanh/places`, gõ một chuỗi vô nghĩa vào ô tìm (hoặc mở `/daoanh/places?q=zzzz`), quan sát panel phải; đối chiếu HTML/JS.
- **Kết quả thực tế (bằng chứng):**
  - [SUY LUẬN TỪ CODE] Nội dung emptyState là tĩnh: `KHỞI TẠO TRUY VẤN` / `"Khớp nối tri thức - Truyền tải tâm linh." … Tìm kiếm địa danh hoặc chọn một nút trên bản đồ.` [SUY LUẬN TỪ CODE: `daoanh/places.html:287-293`].
  - [SUY LUẬN TỪ CODE] `doSearch(q)` chỉ `emptyState.classList.remove('hidden')` **trước** khi fetch, và **không có nhánh** xử lý `results.length === 0` [SUY LUẬN TỪ CODE: `daoanh/places.html:1693-1733`] ⇒ 0 kết quả = im lặng, empty state cũ vẫn hiện như chưa hề tìm.
  - [ĐO ĐƯỢC] `GET /daoanh/api/places/search?q=Kinh%20Kim%20Cang` → `count:0` (API đúng); vấn đề nằm ở UI không phản hồi.
- **Phân loại:** lỗi UI / thiếu tính năng (không phân biệt trạng thái).
- **Ảnh hưởng tới cấp Cử nhân:** sinh viên không biết là "không có dữ liệu" hay "site hỏng" → gõ lại nhiều lần, bỏ cuộc. Vi phạm tính trung thực.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) 4 trạng thái riêng: chưa tìm / đang tải / 0 kết quả / lỗi. 0 kết quả phải hiện từ khoá + gợi ý (bỏ dấu, từ đồng nghĩa, thử chữ Hán).
  - **AC:** `q="zzzz"` → thấy chữ "Không tìm thấy"; `q="Kinh Kim Cang"` → thấy "Không có địa danh khớp — thử tra kinh ở mục Đại Tạng"; khi API 5xx → thấy thông báo lỗi + nút thử lại. Có test cho 4 trạng thái.
- **Ưu tiên:** **P2**.

### CN-16 — Demo "Thiếu Lâm Tự" hard-code và placeholder hứa quá phạm vi

- **Kỳ vọng của sinh viên Cử nhân:** kết quả hiện ra phải là kết quả tìm kiếm thật từ dữ liệu.
- **Cách tái lập:** đọc HTML live của `/daoanh/` (inline script + khối `placeResult`); thử gõ "Thiếu Lâm" và "少林" so với "Thiếu Lâm Tự".
- **Kết quả thực tế (bằng chứng):**
  - [SUY LUẬN TỪ CODE] `handleSearch` có nhánh đặc biệt: nếu `q` chứa "Thiếu Lâm" hoặc "少林" → gọi `showPlaceDemo()` (panel dữ liệu **viết cứng**: toạ độ 34.5885/112.9343, "Thành lập 495 AD", "ID hệ thống PL000000023255", minimap Leaflet) [SUY LUẬN TỪ CODE: `daoanh/home.html:1124-1125,1137-1150`; đoạn mã có trong HTML live].
  - [SUY LUẬN TỪ CODE] Placeholder ô tìm ghi `"Tìm kinh văn, tăng nhân, địa danh... (vd: Tâm Kinh, Thiếu Lâm, Huyền Trang)"` [SUY LUẬN TỪ CODE: `home.html:899`] nhưng thực tế **chỉ** tìm địa danh (và chuyển hướng sai — CN-01).
  - [ĐO ĐƯỢC] `GET /daoanh/api/places/search?q=Thi%E1%BA%BFu%20L%C3%A2m` `count:1`; trong khi demo panel là hằng số bất kể dữ liệu.
- **Phân loại:** lỗi UI / sai lệch kỳ vọng (demo không nhãn).
- **Ảnh hưởng tới cấp Cử nhân:** sinh viên tưởng đây là kết quả tra cứu thật; demo bỏ qua khả năng sai dữ liệu và không dạy được cách tra. Placeholder khiến hiểu sai năng lực hệ thống.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Bỏ demo hoặc dán nhãn rõ "Ví dụ minh hoạ — không phải kết quả tra cứu"; placeholder phải khớp phạm vi tìm kiếm thật.
  - **AC:** không có từ khoá nào trả về panel dữ liệu cứng; placeholder ghi đúng loại dữ liệu tìm được; test: `q="Thiếu Lâm"` trả kết quả lấy từ API (count khớp).
- **Ưu tiên:** **P2**.

### CN-17 — Bất nhất API phụ (tham số bị bỏ qua, cắt chuỗi, min 2 ký tự, trang lỗi trần)

- **Kỳ vọng của sinh viên Cử nhân:** API/UI hành xử nhất quán và thông báo lỗi dễ hiểu.
- **Cách tái lập:** 4 phép đo nhỏ:
  1. `GET /daoanh/api/cbeta/catalog?search=%E9%87%91%E5%89%9B` và `?title=%E9%87%91%E5%89%9B` (kỳ vọng lọc theo tiêu đề).
  2. `GET /daoanh/api/public/autocomplete?q=Duy%C3%AAn%20Kh%E1%BB%9Fi`.
  3. `GET /daoanh/api/cbeta/corpus-search?q=%E4%BD%9B` (một chữ Hán).
  4. `GET /daoanh/login.html`.
- **Kết quả thực tế (bằng chứng):**
  - [ĐO ĐƯỢC] `catalog?search=金剛` và `catalog?title=金剛` → **200** trả **trang 1 không lọc** (`Ba Tư Giáo Tàn Kinh`, …) — chỉ `?q=` mới lọc.
  - [ĐO ĐƯỢC] `public/autocomplete?q=Duyên%20Khởi` → `{"data":[{"id":null,"name_zh":"- Chấp Tàng tức là c","source":"lexicon","value":"- Chấp Tàng tức là c"}, …]}` — value bị cắt đúng **20 ký tự**, `id:null` ⇒ không bấm/điều hướng được.
  - [ĐO ĐƯỢC] `corpus-search?q=%E4%BD%9B` ("佛") → **400** `{"error":"query_too_short","message":"Vui lòng nhập ít nhất 2 ký tự để tìm kiếm.","min_length":2,"ok":false}` — chữ Hán đơn thường gặp trong tra cứu Phật học.
  - [ĐO ĐƯỢC] `GET /daoanh/login.html` → **502**, body `502 Bad Gateway … nginx/1.24.0 (Ubuntu)` (không brand, không hướng dẫn).
- **Phân loại:** lỗi API / lỗi UI (bất nhất, thông báo lỗi kỹ thuật).
- **Ảnh hưởng tới cấp Cử nhân:** tự tra bằng chữ Hán 1 chữ (hay gặp: 佛, 禪, 空) bị chặn; autocomplete hiện chuỗi cụt không dùng được; gặp trang 502 trần không biết làm gì.
- **Yêu cầu cho đội Planning (AC đo được):**
  - (a) Tài liệu hoá + chuẩn hoá tham số (`q` cho search, `limit/offset/page` cho phân trang); hoặc nhận `search/title` như alias.
  - (b) Autocomplete trả `id` + value đủ dài (≥60 ký tự hoặc full), lexicon entry phải có `id`/`url`.
  - (c) Cho phép 1 ký tự Hán trong corpus-search (min 1 cho CJK, 2 cho Latin) hoặc thông báo ngay trên UI trước khi gửi.
  - (d) Trang lỗi 502/404 phải branded, có nút "Về trang chủ".
  - **AC:** `catalog?search=`/`?title=` hành xử như `?q=`; autocomplete value ≥60 ký tự và item lexicon bấm được; `q=佛` trả 200 `result_count ≥ 0`; `/daoanh/login.html` trả trang lỗi có thương hiệu (không phải HTML nginx trần).
- **Ưu tiên:** **P2**.

---

## 4. Cái đã tốt (≥5 mục — để Planning không phá)

1. **`/api/glossary` là tài sản lớn, chất lượng cao.** `GET /daoanh/api/glossary?term=Niết%20Bàn` → 200, 7.838 ký tự JSON, nhiều định nghĩa dài, mỗi định nghĩa có `source_label` (Từ điển PG VN — Minh Thông, Nguyễn Quốc Hùng, Quang Độ…). Đúng chuẩn "dễ hiểu, có nguồn" — chỉ thiếu cửa vào (CN-05).
2. **Chi tiết địa danh rất sâu và có trích dẫn nguồn.** `GET /api/places/PL000000023255` (Thiếu Lâm Tự) có `dila_founding_year:495`, `confidence`, `country_vi`, `dila_category`, `dila_listbibl` với 20+ ref CBETA (`T50n2060_p0457c16`…); kèm `GET …/persons` (16.882 B, 16+ nhân vật với `source_url` tới `cbetaonline.dila.edu.tw`), `GET …/graph` (18.268 B), `GET …/timeline` (Wikidata `Q232771`, `dynasty_context` Bắc Ngụy 386–534).
3. **Phả hệ Marcus hoạt động và có trích dẫn từng cạnh.** `GET /api/monk/A000294/marcus-network` → `linked:true`, `match_confidence:1.0`, 16 học trò + 1 thầy, mỗi quan hệ có `ref` CBETA; `GET /api/monk/A000294/graph` có `center.label:"Huyền Trang"`, `label_zh:"玄奘"`; trang `/daoanh/lineage?id=A000294` render đúng khi có `id`.
4. **Minh bạch giới hạn dữ liệu ở tầng API.** `/api/cbeta/text/T51n2076/browse` trả `coverage.complete_text:false` + note "Đây là đoạn trích dẫn chiếu nhân vật, không phải bản toàn văn"; `/api/cbeta/corpus-search` trả `coverage {catalog_total, texts_searchable, passages_searchable}`; panel chi tiết địa danh in cảnh báo "Chưa có dữ liệu tổng hợp cho thực thể này trong phạm vi đã kiểm kê". Đây là cách trung thực **nên giữ** và mở rộng lên UI.
5. **Các tab chưa có dữ liệu ghi rõ "chưa index".** `renderHinhanhTab`/`renderNghethuatTab` hiển thị "Bộ sưu tập hình ảnh chùa/tượng/địa danh **chưa index** theo thực thể." — trung thực, không giả vờ có dữ liệu.
6. **Mục lục CBETA tra được bằng chữ Hán, trả metadata chuẩn.** `GET /api/cbeta/catalog?q=%E9%87%91%E5%89%9B` → 200 với `series:T, q_number:8, sh_number:235, page:748, translator_vi:Cưu Ma La Thập` — nền rất tốt để dựng trang mục lục (CN-02/CN-12 chỉ cần UI).
7. **Nguồn & giấy phép rõ ràng.** `/daoanh/about` và `/daoanh/opendata` công bố CBETA (CC BY-NC-SA 4.0), DILA, Marcus SNA; panel chi tiết có block "Nguồn & Giấy phép" và footer "Pháp Thí Hội (Ver Demo)" — thuận lợi cho trích dẫn học thuật nếu bổ sung citation đầy đủ.
8. **Thông báo lỗi tiếng Việt có hướng dẫn.** `/api/cbeta/corpus-search` trả `{"message":"Vui lòng nhập ít nhất 2 ký tự để tìm kiếm."}`; `/api/glossary` thiếu tham số trả "Thiếu tham số term." — giữ phong cách này khi thêm UI.

---

## 5. Câu hỏi cần Admin quyết

1. **Ưu tiên số 1 — có cho phép đổi ô tìm kiếm trang chủ sang gọi `/daoanh/api/search` (monks/places/works) và dựng một trang kết quả thống nhất không?** (Giải CN-01 + CN-02 cùng lúc; nếu không, cần quyết định chỉnh nhãn "Tìm địa danh" và sửa luồng `q` của `places.html`.)
2. **4 trang còn thiếu (`tripitaka`, `people`, `timeline`, `graph`) — dựng landing tối thiểu hay bỏ thẻ khỏi trang chủ?** Cần chốt để Planning biết khối lượng; dữ liệu cho 3 trang đã có API (`/api/search`, `/api/persons/browse`, `/api/chronology/events`).
3. **Số liệu chuẩn để công bố là số nào** (địa danh: 8.241 / 59.167 / 176.783; kinh: 13.520 / 3.122; tu sĩ: 5.800+ / 48.673 / 11.300; truyền thừa: 1.200+ / 18.121)? Ai chốt `dataset_version` + ngày đo, và có cho phép lấy số động từ API thay số hard-code (`home.html:1005-1020`) không?
4. **Từ điển:** có được phép hiển thị công khai toàn bộ `matches` của `/api/glossary` (nhiều nguồn từ điển, có thể khác giấy phép) hay chỉ một subset đã duyệt? Có cần duyệt nội dung trước khi gắn popup vào tiểu sử/kinh văn không?
5. **Năm sinh/mất sai (Huyền Trang `2024–1787`):** sửa dữ liệu nguồn (`people.birth_year/death_year` → 602/664) cần Admin duyệt vì đụng DB; hay tạm ẩn trường năm trên UI và chỉ dùng `dila_full.birth_date/death_date`? Có muốn thêm guard tự động (chặn năm vô lý) không?
6. **Toàn văn kinh:** có kế hoạch import tối thiểu 3 bộ phổ thông (`T08n0235` Kim Cang, `T09n0262` Pháp Hoa, `T08n0251` Tâm Kinh) không? Nếu chưa, có cho phép ghi nhãn "chưa có toàn văn" ngay trên tab Đại Tạng/CBETA để sinh viên không mất công tìm không?

---

### Phụ lục — Bảng đo nhanh (tái lập trong 5 phút)

| # | Lệnh (GET, chỉ đọc) | Kết quả kỳ vọng khi đã sửa |
|---|---|---|
| 1 | `/daoanh/api/places/Kinh%20Kim%20Cang` | không còn bị gọi từ ô search (CN-01) |
| 2 | `/daoanh/tripitaka`, `/people`, `/timeline`, `/graph` | 200 + nội dung (CN-03) |
| 3 | `/daoanh/api/search?q=Kinh%20Ph%C3%A1p%20Hoa` | `works` có bộ Pháp Hoa + sigla (CN-02/CN-12) |
| 4 | `/daoanh/api/cbeta/text/T08n0235/browse` | 200 (không còn `sigla_not_found`) (CN-04) |
| 5 | `/daoanh/api/glossary?term=B%C3%A1t%20Nh%C3%A3` | có route UI tương ứng (CN-05) |
| 6 | `/daoanh/api/person/A000294/profile` | `birth_year:602, death_year:664` (CN-06) |
| 7 | `/daoanh/api/persons/A000294` | `bio_vi` khác null (CN-07) |
| 8 | `/daoanh/api/entity/A000294/unified` | `canonical_name_vi:"Huyền Trang"` (CN-08) |
| 9 | `/daoanh/api/monk/search?q=Thích%20Minh%20Châu` | khớp `monk-resolve` (CN-09) |
| 10 | `/daoanh/api/places/search?q=chùa%20Dâu` | đúng chùa Dâu hoặc 0 kèm thông báo (CN-10) |
| 11 | 4 số trên `/daoanh/` | khớp `count/total` API (CN-11) |
| 12 | `/daoanh/api/search?q=Ph%C3%A1p%20Hoa` | không còn cặp `PL…`/`PLxxxxxx` trùng (CN-13) |

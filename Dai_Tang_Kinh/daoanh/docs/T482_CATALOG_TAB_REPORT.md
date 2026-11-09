# T482 — Tab "Catalog" (namevimap.html): danh mục địa danh DILA đầy đủ 59.373

Ngày: 2026-10-28

## 1. Files changed

Đường dẫn tuyệt đối (root: `E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\`):

- `scripts/t482_build_place_catalog.py` — **MỚI**. DDL + dry-run + apply + revert cho bảng `place_catalog`.
- `routes_places.py` — **SỬA (additive)**. Thêm 1 route mới `GET /daoanh/api/places/catalog` +
  4 hàm phụ (`_t482_load_lexicon_mem`, `_t482_dictionary_lookup`, `_t482_source_rank`,
  cache module-level). Không sửa dòng nào của route/hàm cũ.
- `admin/namevimap.html` — **SỬA (additive)**. Thêm nút tab "📚 Catalog", panel `#tab-catalog`,
  nhánh `switchTab('catalog', …)`, và khối JS (`catalogLoad`, `catalogPassRow`, `catalogEditRow`,
  `catalogSaveEdit`, `catalogCancelEdit`, `_catalogDictCell`, `catalogSearchDebounce`).
- `tasks/T482-namevimap-catalog-tab-full-dila.md` — **MỚI**. Task file (AGENTS §21).
- `docs/tasktodo.md` — thêm khối T482 ở đầu file.
- `docs/ROLLBACK.md` — thêm 1 dòng revert cho T482.
- `docs/sessions/2026-10-28/catalog/backup-log.md` — **MỚI**. Log backup + dry-run + apply.
- `data/backups/lineage_2026-10-28_catalog.db` — **MỚI** (backup DB trước khi ghi, sqlite backup API).

Không sửa `places_dila`, `namevi_map_places`, `dila_place_authority`, `codex_place_name`,
`ai_place_name`, `lexicon` — chỉ INSERT vào bảng mới `place_catalog`.

## 2. Root cause / lý do thiết kế bảng catalog mới

Tab Place hiện tại (`admin/namevimap.html`) liệt kê từ `places_dila` (59.167 dòng) — thiếu 206
địa danh đã nạp ở `dila_place_authority` (T453/T477, chưa có trong `places_dila`). Admin cần
nhìn thấy TOÀN BỘ danh mục DILA (59.373) để check/Pass, không chỉ phần cũ.

Hướng sửa: KHÔNG patch Tab Place (sẽ đổi hành vi đang chạy production, rủi ro regression) và
KHÔNG hard-code dữ liệu riêng trong component (vi phạm quy tắc data-integrity). Thay vào đó:

- Tạo bảng **additive** `place_catalog` (place_id PK canonical 12 số theo T477, name_zh,
  source_table, created_at) — chỉ là khoá hợp nhất 2 nguồn gốc (`places_dila` +
  `dila_place_authority`), KHÔNG denormalize Claude/Gemini/Từ điển/name_vi — các giá trị này
  đổi liên tục khi Admin Pass/Sửa ở Tab Place, denormalize sẽ lệch dữ liệu (vi phạm
  `data-integrity.md`: DB PTDA là lớp hợp nhất nhưng vẫn phải phản ánh đúng dữ liệu nguồn).
- API mới `GET /daoanh/api/places/catalog` JOIN SỐNG `place_catalog` với
  `namevi_map_places`/`codex_place_name`/`ai_place_name`, tra `lexicon` theo thời gian thực.
- Tái dùng NGUYÊN `/daoanh/api/places/vi-map/<id>/approve` và `/edit` cho nút Kết luận/Sửa —
  đúng yêu cầu "không tạo cơ chế mới song song".

## 3. Trước/sau API contract

**Trước:** chỉ có `GET /daoanh/api/places/vi-map` (nguồn `places_dila`, 59.167 dòng tối đa).

**Sau (thêm, không đổi cái cũ):**

```
GET /daoanh/api/places/catalog?q=&page=&size=
```
Response:
```json
{
  "ok": true,
  "items": [{
    "place_id": "PL000000000048",
    "name_zh": "王寺",
    "source_table": "places_dila | dila_place_authority",
    "name_vi": "Vương Tự" ,
    "source": "auto_transliterate",
    "source_badge": "phiên âm tự động",
    "vn_name_status": "reviewed" | null,
    "claude_name_vi": "...",
    "gemini_name_vi": "...",
    "dictionary_matches": [
      {"source": "Tu Dien Thien Tong Han Viet - Han Man - Thong Thien",
       "term": "A Dục Vương Tự", "definition": "<toàn bộ nội dung>",
       "match_type": "exact_term" | "substring_def"}
    ]
  }],
  "total": 59373, "page": 1, "size": 50, "pages": 1188
}
```
Kết luận/Sửa dùng lại NGUYÊN endpoint cũ:
```
POST /daoanh/api/places/vi-map/<id>/approve
POST /daoanh/api/places/vi-map/<id>/edit
```
(Hành vi 404 khi `namevi_map_places` chưa có dòng — xem mục 6.)

## 4. Kết quả test

### Số liệu catalog

- `place_catalog` thực tế: **59.373** dòng = 59.167 (`places_dila`) + 206 (`dila_place_authority`),
  0 trùng id — **đúng khớp số đề bài 59.373**, không có chênh lệch cần giải thích.
- `codex_place_name` (Claude, toàn DB): 59.353 dòng.
- `ai_place_name` (Gemini, toàn DB): 50.341 dòng.
- `namevi_map_places` (name_vi hiện tại, toàn DB): 60.468 dòng — trong đó 206 ID thuộc
  `dila_place_authority` **CHƯA** có dòng tương ứng (xem mục 6).
- `lexicon`: 166.278 dòng / 20 nguồn (khớp mô tả đề bài). Nguồn Thông Thiền
  (`Tu Dien Thien Tong Han Viet - Han Man - Thong Thien`) = 11.972 dòng, trong đó
  `entity_type='ĐỊA DANH'` = 1.502 dòng.

### Tìm "Từ Điển Đại Tạng Kinh của Nguyễn Minh Tiến"

Đã tìm trong:
- `translation_glossary` (79 dòng) — không có `source_label` chứa "Minh Tiến".
- `term_glossaries` (18.127 dòng) — `source` chỉ có 1 giá trị duy nhất: `marcus`.
- `glossary_term` / `glossary_vi` (248.095 dòng mỗi bảng) — `source_id` chỉ có giá trị `6`
  (= Wikidata theo `data_sources`).
- `monk_dict` (2 dòng), `dila_reference` (1.000 dòng) — không có trường nào chứa "Minh Tiến".
- `data_sources` (16 nguồn đăng ký) — không có nguồn nào tên "Nguyễn Minh Tiến" là từ điển.
- Quét toàn bộ `.py`/`.md`/`.json`/`.csv` trong codebase (loại trừ `docs/sessions`,
  `data/backups`, `_book/`) — chỉ thấy bảng **`cbeta_catalog_vn`** (3.122 dòng) ghi chú
  "Nguyễn Minh Tiến" trong `docs/db_schema.md` và `src_python/db/import_cbeta_catalog_vn.py`
  (docstring: *"Import Mục Lục Đại Chánh Tân Tu (Nguyễn Minh Tiến) vào cbeta_catalog_vn"*).

**Kết luận: KHÔNG tìm thấy bộ từ điển thuật ngữ "Từ Điển Đại Tạng Kinh của Nguyễn Minh Tiến"
trong DB.** `cbeta_catalog_vn` là MỤC LỤC các bộ kinh/sutra đã dịch (khoá theo `title_vi`,
`translator_vi`), KHÔNG phải từ điển thuật ngữ tra theo `name_zh` của địa danh — không dùng
được cho cột Từ điển của tab này. Không bịa dữ liệu thay thế.

**Đề xuất nạp sau (nếu Admin có nguồn):** nếu có file/bộ dữ liệu "Từ Điển Đại Tạng Kinh của
Nguyễn Minh Tiến" dạng term→definition (khác với mục lục sutra), có thể nạp vào `lexicon` với
`source='Tu Dien Dai Tang Kinh - Nguyen Minh Tien'` và thêm vào `_T482_SOURCE_PRIORITY` trong
`routes_places.py` (ưu tiên cao nhất) — không cần đổi API/schema, chỉ cần INSERT.

### Test chức năng qua browser thật (127.0.0.1:8080, session admin có sẵn trong trình duyệt —
không dùng JS inject để claim done, dùng click UI thật)

1. Mở `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → click tab "📚 Catalog".
   - Trang hiện đúng 8 cột: Place ID | Hán tự | name_vi hiện tại | Claude | Gemini | Từ điển |
     Kết luận | Sửa.
   - Tổng hiển thị: **"59,373 địa danh (danh mục đầy đủ)"**.
   - Network log: `GET /daoanh/api/places/catalog?page=1&size=50 → 200 OK` (lần đầu ~18s do
     cache lexicon nguội — xem Limitation).
2. Tìm `PL000000060487` (chỉ tồn tại ở `dila_place_authority`, KHÔNG có trong `places_dila`):
   - Hiển thị đúng `source_table=dila_place_authority`, `name_vi=—` (chưa có trong
     `namevi_map_places`), **vẫn có** Claude="Yên Chi Sơn" và Gemini="Yên Chi Sơn" (JOIN sống
     đúng, không phụ thuộc `places_dila`).
   - Bấm "✓ Pass" → network log: `POST /daoanh/api/places/vi-map/PL000000060487/approve →
     404 NOT FOUND` — **đúng hành vi thiết kế** (API cũ yêu cầu dòng `namevi_map_places` có
     sẵn), không phải lỗi code mới.
3. Tìm `PL000000000008` (có sẵn trong `namevi_map_places`, `vn_name_status` đang trống):
   - Bấm "✓ Pass" → network log: `POST /daoanh/api/places/vi-map/PL000000000008/approve →
     200 OK`. Kiểm DB: `namevi_map_places.vn_name_status` chuyển thành `'reviewed'` —
     **xác nhận nút Pass của tab Catalog dùng đúng cơ chế cũ, ghi đúng dữ liệu**.
   - **Đã revert ngay sau test** (`vn_name_status=NULL, needs_review=1`, xoá dòng
     `canonical_decision` vừa tạo) để không để lại phê duyệt giả — admin tự quyết định
     Pass thật sau.
4. Cột Từ điển: test `PL000000000048` (name_zh="王寺") trả về 5 kết quả đa nguồn, ưu tiên 2
   kết quả từ "Tu Dien Thien Tong Han Viet - Han Man - Thong Thien" lên đầu, mỗi kết quả có
   tên nguồn + nội dung đầy đủ (không chỉ ✓) — đúng yêu cầu đề bài.

## 5. Report

`docs/T482_CATALOG_TAB_REPORT.md` (file này).

## 6. Limitation / blocker còn lại

1. **206 dòng `dila_place_authority` chưa có `namevi_map_places`** → nút Pass/Sửa trả 404
   cho các ID này cho tới khi có dòng `namevi_map_places` tương ứng. Đây là hành vi THẬT của
   2 endpoint `/approve` và `/edit` hiện có (không sửa, theo đúng yêu cầu "dùng đúng cơ chế,
   không tạo mới"). Nếu Admin muốn Pass/Sửa được cho 206 dòng này, cần một bước riêng tạo
   dòng `namevi_map_places` (ví dụ UPSERT rỗng `name_vi=NULL`) — việc đó NGOÀI phạm vi task
   này (sẽ ghi dữ liệu mới vào `namevi_map_places`, cần Admin duyệt riêng).
2. **Không tìm thấy "Từ Điển Đại Tạng Kinh của Nguyễn Minh Tiến"** trong DB — xem mục 4.
3. **Hiệu năng cột Từ điển:** mỗi lần tải trang (cache nguội) quét ~166K dòng `lexicon` cho
   mỗi tên Hán trên trang (tối đa 50 tên/trang) → lần đầu ~18s. Có cache in-memory
   (`_T482_DICT_CACHE`, tối đa 2.000 entry) nên các lần tải sau nhanh hơn đáng kể. Nếu Admin
   thấy chậm khi dùng thật, có thể cân nhắc xây index riêng (ngoài phạm vi task này, cần
   quyết định thêm bảng/cột mới).
4. **Khớp Từ điển theo substring có thể quá rộng với tên Hán ngắn (1-2 ký tự)** — ví dụ "王寺"
   (2 ký tự) khớp vào nhiều định nghĩa không thực sự liên quan trực tiếp đến địa danh đó. Đây
   là giới hạn vốn có của phương pháp substring, không phải bug — đã hiển thị rõ `match_type`
   (`exact_term` vs `substring_def`) để Admin tự đánh giá độ tin cậy, không che giấu.
5. **Chưa chạy `npm run pipeline`/`tester:agent` đầy đủ** trong phiên này (môi trường lint
   không phản hồi trong thời gian cho phép) — đã tự kiểm: `python -X utf8 -m py_compile` PASS
   cho `routes_places.py` và `scripts/t482_build_place_catalog.py`; kiểm cú pháp JS bằng
   `new Function()` cho toàn bộ `<script>` trong `namevimap.html` → PASS; browser-verify thật
   như mục 4. Khuyến nghị chạy `npm run pipeline` trước khi commit.
6. **Chưa commit** — theo yêu cầu, để nguyên working tree cho Admin tự `git add/commit`.

---

## 7. QA reject 2026-10-28 — 3 điểm sửa (daoanh-debugger)

QA (`daoanh-qa`) kiểm chứng độc lập lần đầu và kết luận **CHƯA ĐẠT** vì 3 lý do dưới. Đã sửa cả 3,
không động vào gì khác.

### 7a. Dữ liệu test chưa hoàn tác hết (PL000000000008)

Lần test nút Pass lúc 15:06:52 (mục 4 phần trên) chỉ `UPDATE vn_name_status=NULL`, **thiếu**
3 điểm sau (so với backup `data/backups/lineage_2026-10-28_catalog.db`, tạo TRƯỚC `--apply` T482):

| Bảng/cột | Trước khi sửa (sai) | Backup (đúng) | Sau khi sửa |
|---|---|---|---|
| `namevi_map_places.needs_review` (PL000000000008) | `1` | `0` | `0` ✅ |
| `en_audit_log` | còn dòng `log_id=44054` (`action='approve'`, `editor='nhatdoaphuvan@gmail.com'`, `verification_status='verified'`, `created_at='2026-10-28T15:06:52'`) — dấu vết phê duyệt giả mang tên admin thật | không tồn tại | đã `DELETE` dòng `log_id=44054` ✅ |
| `entity_hub.status` (entity_id=159167) | `'verified'` | `'active'` | `'active'` ✅ |
| `entity_hub.updated_at` (entity_id=159167) | `'2026-10-28T15:06:52'` | `'2026-08-16 15:24:45'` | `'2026-08-16 15:24:45'` ✅ |

Script: `scripts/fix_t482_revert_pl8.py` (dry-run mặc định, `--apply` để ghi, 1 transaction
BEGIN/COMMIT + rollback on error, có check trạng thái trước khi ghi để không ghi nhầm nếu đã
được sửa bởi phiên khác). Đã chạy `--apply`, verify lại bằng query trực tiếp DB: khớp 100%
với backup ở cả 4 cột trên. Không động vào `canonical_decision`/`vn_name_status` (QA xác nhận
2 bảng này đã đúng/sạch) và không động gì ngoài `PL000000000008` / `log_id=44054` / `entity_id=159167`.

### 7b. `docs/ROLLBACK.md` ghi sai cách rollback code

Đã verify lại số dòng thực tế (2026-10-28, sau các sửa khác trong ngày) và sửa dòng ROLLBACK
T482: bỏ lệnh `git checkout -- routes_places.py admin/namevimap.html` (sai — `routes_places.py`
chưa track trong git nên `checkout --` sẽ lỗi "did not match any file(s) known to git"; và
`namevimap.html` có WIP chưa commit của session khác (BUG-050, T478) nên `checkout --` sẽ xoá
mất). Thay bằng rollback thủ công đúng khối T482 đã verify lại ranh giới:
- `routes_places.py` dòng **2551–2770** (bao gồm cả index phụ `_T482_EXACT_IDX`/`_T482_BIGRAM_IDX`
  thêm ở mục 7c dưới — cùng 1 khối T482, xoá route `/daoanh/api/places/catalog` + 4 hàm phụ).
- `admin/namevimap.html` dòng **220** (nút tab), **896–947** (HTML tab Catalog),
  **1137–1139** (gọi `catalogLoad` trong `switchTab`), **2797–2986** (JS `catalogLoad`/
  `catalogRender`/...).

### 7d. QA pass 2 (2026-10-28) — sửa số dòng rollback, KHÔNG phải lỗi logic

QA đọc lại code thật và phát hiện 2 chỗ ghi sai số dòng ở mục 7b (chỉ ảnh hưởng tài liệu
rollback, không ảnh hưởng code đang chạy):
1. `routes_places.py`: khối T482 (`api_places_catalog_list`) thực ra kết thúc ở dòng 2769
   (`except Exception as e:` / `return jsonify(...), 500` tại 2768–2769), dòng 2770 là dòng
   trống kết thúc khối, route tiếp theo `vi-map/<place_id>/approve` bắt đầu ở dòng 2772. Số cũ
   ghi 2711 nằm ngay sau `gemini_col = ...`, giữa thân hàm — xoá theo số đó sẽ cắt cụt hàm, vỡ
   cú pháp. Đã sửa thành **2551–2770**.
2. `admin/namevimap.html`: khối `if (name === 'catalog') { if (!_catalogLoaded) { ... } }`
   trong `switchTab` đóng ngoặc `}` ở dòng 1139, không phải 1138. Số cũ ghi 1137–1138 sẽ để sót
   1 dấu `}` thừa, hỏng JS của `switchTab`. Đã sửa thành **1137–1139**.

Đã verify lại bằng cách đọc trực tiếp `routes_places.py` quanh dòng 2540–2780 và
`admin/namevimap.html` quanh dòng 1125–1150 (không dùng số QA đưa ra làm căn cứ duy nhất).
Cả 2 file docs (`ROLLBACK.md` mục 1 dòng T482, `T482_CATALOG_TAB_REPORT.md` mục 7b trên) đã
được sửa đồng bộ. Không đổi gì trong `routes_places.py` hay `admin/namevimap.html`.

### 7c. Perf fix — vi phạm Zero-RAM / quét tuần tự (AGENTS.md)

**Root cause:** `_t482_dictionary_lookup()` (routes_places.py) quét tuần tự TOÀN BỘ
166.278 dòng `lexicon` trong Python **cho MỖI tên Hán trên trang** (tối đa 50 tên/trang,
không cache theo trang — chỉ cache theo từng `name_zh` riêng lẻ sau lần đầu gặp).
Benchmark thực tế (50 `name_zh` lấy từ `place_catalog`, cùng máy, cùng `lineage.db`,
không tính thời gian nạp lexicon vào RAM — chỉ tính phần lookup):

| | Trước | Sau |
|---|---|---|
| 50 tên/trang (lexicon đã có trong RAM) | **14.23s** | **0.52s** (27x nhanh hơn) |
| Kết quả trả về | — | **khớp 100%** với bản cũ (0 lệch trên 50 tên test) |

**Fix:** xây thêm 2 index phụ TRONG RAM (không tạo bảng/cột DB mới — vẫn additive, 0 thay
đổi schema) ngay trong lần nạp lexicon đầu tiên (`_t482_load_lexicon_mem`):
- `_T482_EXACT_IDX`: `term_ns -> [row_index]` — tra khớp `exact_term` O(1) thay vì so sánh
  tuần tự.
- `_T482_BIGRAM_IDX`: bigram Hán liên tiếp trong `definition` (chỉ tính trong các đoạn CJK
  liên tục, bỏ qua phần tiếng Việt) `-> set(row_index)` — dùng để thu hẹp ứng viên trước khi
  verify substring thật (`_t482_candidate_rows`), thay vì so `name_ns in def_ns` trên cả
  166K dòng mỗi lần.
- Tên 1 ký tự Hán (hiếm với địa danh) không có bigram → fallback quét toàn bộ như cũ (đúng,
  an toàn, không sai kết quả — chỉ mất tốc độ ở trường hợp hiếm này).

**Trade-off cần lưu ý (ghi rõ, không giấu):** lần build index đầu tiên (khi lexicon chưa có
trong RAM của process, ví dụ sau khi restart server) đo được **~37.7s** (166K dòng, build cả
2 index) — **chậm hơn** so với trước đây (~18s, chỉ nạp mem không build index). Đây là chi phí
trả **1 lần duy nhất** cho đời sống của 1 process (worker Flask), sau đó MỌI trang khác (ước
tính 59.373 ÷ 50 ≈ 1.187 trang) đều nhanh (~0.5s/trang) thay vì 20-80s/trang như cũ — tổng thời
gian cho toàn bộ Catalog giảm từ ước tính hàng giờ xuống dưới 1 phút. Nếu Admin dùng tab này
liên tục ngay sau khi restart server, 1 lần tải đầu có thể cảm thấy chậm hơn — chấp nhận được
vì đây chỉ xảy ra 1 lần/process, không lặp lại mỗi request như lỗi cũ.

Verify không regression: `python -m py_compile routes_places.py` PASS; kết quả
`_t482_dictionary_lookup` so với bản cũ khớp 100% trên 50 tên test (xem bảng trên) — không
đổi hành vi/API contract, chỉ đổi tốc độ nội bộ.

---

## 8. QA reject lần 2 (2026-10-28) — fix round 2: root cause THẬT là build RAM mỗi lần restart, không phải thiếu index

QA đo lại bằng **curl HTTP thật** (không phải benchmark hàm cô lập như round 1) và phát hiện:
trang **đã có trong cache**: 0.4-6s; trang **CHƯA từng truy cập**: **7.9-13.9s/trang**, lặp lại
ở ~1.187 trang (59.373 ÷ 50) — round 1 (mục 7c) chỉ đo tốc độ *sau khi* index RAM đã build
xong với 50 tên cố định, không phản ánh chi phí tra lần đầu cho tên MỚI trên các trang khác.

### 8a. Root cause THẬT (đã xác minh bằng curl + `EXPLAIN QUERY PLAN` trên `data/lineage.db`, không đoán)

- JOIN SQL của route (`place_catalog` × `namevi_map_places`/`codex_place_name`/`ai_place_name`)
  **đã có index đủ** (`dila_id` là PK/autoindex ở 3 bảng JOIN) — tự đo: COUNT ~0.6s, SELECT 1
  trang (LIMIT/OFFSET) ~0.03-0.1s dù OFFSET lớn. **Không phải nguyên nhân.**
- Bottleneck THẬT: `_t482_load_lexicon_mem()` (bản round 1) nạp **toàn bộ 166.278 dòng**
  `lexicon` vào 1 list Python + build 2 dict Python (`_T482_EXACT_IDX`, `_T482_BIGRAM_IDX`)
  **trong RAM của tiến trình Flask, chỉ 1 lần/đời tiến trình** — nhưng chi phí build đó
  (**10-45s đo thực tế trên máy này**, xem bảng dưới) phải trả lại **MỖI LẦN server restart**.
  Môi trường dev restart `app.py` rất thường xuyên (nhiều session sửa file song song — xem
  AGENTS.md §17), nên QA/Admin test "trang chưa truy cập" thường trùng đúng lúc vừa restart
  → đo được con số gần bằng chi phí build (10-45s) + chi phí query (~0.5-1s) ≈ khớp đúng
  7.9-13.9s QA đo được. **Vi phạm Zero-RAM Principle (AGENTS.md §2)**: không được nạp dữ liệu
  lớn vào RAM Python mỗi lần tiến trình khởi động lại — phải dùng index SQL bền trong DB.

### 8b. Fix round 2 — chuyển hẳn sang SQL index bền + batch query (không còn RAM rebuild)

File mới: **`scripts/t482_build_lexicon_cjk_idx.py`** — migration ADDITIVE, idempotent
(`--dry-run`/`--apply`/`--apply --force`/`--revert`, tự backup DB trước khi ghi):
- Thêm 2 cột `lexicon.term_ns`, `lexicon.def_ns` (CJK đã bỏ khoảng trắng OCR) +
  `CREATE INDEX idx_lexicon_term_ns`.
- Thêm bảng phụ `lexicon_cjk_bigram(bigram, lexicon_id)` + `CREATE INDEX idx_lexicon_cjk_bigram`
  — bigram Hán liên tục trong `def_ns`, dùng để thu hẹp ứng viên substring bằng SQL thay vì
  Python. Build **1 LẦN DUY NHẤT** (không chạy lại mỗi lần server start) — đã `--apply` thật:
  166.278 dòng, 158.251 bigram, **45.9s** (1 lần, không lặp lại).

`routes_places.py`:
- Xoá `_T482_LEXICON_MEM`/`_t482_load_lexicon_mem`/`_T482_EXACT_IDX`/`_T482_BIGRAM_IDX`/
  `_t482_candidate_rows` (toàn bộ phần nạp RAM — không còn nạp 166K dòng vào Python nữa).
- Thêm `_t482_dictionary_lookup_batch(conn, name_zh_list)`: tra **CẢ TRANG (tối đa 50 tên)
  trong 1 lượt** bằng 2-4 câu SQL batch (`WHERE term_ns IN (...)`, `WHERE bigram IN (...)`,
  2-pass fetch ứng viên — xem 8c) thay vì N+1 lần gọi `_t482_dictionary_lookup()` riêng từng
  tên (round 1 vẫn gọi N+1, chỉ nhanh mỗi lần gọi nhờ RAM index). `api_places_catalog_list()`
  sửa 1 dòng: gọi batch 1 lần cho cả `rows` thay vì loop gọi hàm đơn.
- `_t482_sql_idx_ready(conn)`: kiểm 1 lần/đời tiến trình cột `term_ns`/bảng `lexicon_cjk_bigram`
  đã tồn tại chưa; nếu env nào CHƯA chạy migration, fallback `_t482_dictionary_lookup_fallback_scan`
  (quét tuần tự an toàn, chậm nhưng đúng, không lỗi 500) — không bắt buộc migration mới chạy được.
- Giữ nguyên `_T482_DICT_CACHE` (cache theo `name_zh`, tối đa 2.000 entry) cho các lần gọi lặp
  lại trong đời tiến trình — không đổi hành vi cache cũ.

### 8c. Tối ưu thêm — 2-pass fetch tránh đọc overflow page của `definition` dài

Đo trực tiếp (không qua server, loại nhiễu): trang có 464 ứng viên bigram thô, nếu
`SELECT id, term, definition, source, def_ns FROM lexicon WHERE id IN (464 id)` ngay (1-pass)
tốn **~1.5s** vì cột `definition` dài (có dòng ~2.000 ký tự) tràn sang overflow page riêng
trong SQLite — đọc overflow page cho CẢ 464 ứng viên dù hầu hết KHÔNG khớp thật. Sửa: 2-pass —
pass 1 chỉ `SELECT id, def_ns` (nhẹ, không có cột dài) để verify substring thật; pass 2 chỉ
`SELECT id, term, definition, source` cho các id ĐÃ xác nhận khớp (luôn rất nhỏ, dưới 10 id).

### 8d. Số liệu đo THẬT bằng curl HTTP (không phải benchmark hàm cô lập) — sau fix round 2

Môi trường: `python app.py` (port 5000), **1 process duy nhất** (xác minh bằng
`Get-NetTCPConnection -LocalPort 5000 -State Listen` chỉ ra đúng 1 PID — lần đo đầu có 2
process cũ còn sót do nhiều lần restart test, gây đo nhiễu 7-29s giả, đã loại sau khi kill
hết và restart sạch). Đo bằng `curl -w "%{time_total}"`, mỗi trang **CHƯA từng truy cập**
trong phiên hiện tại của process (tên Hán mới, không có trong `_T482_DICT_CACHE`):

| Trang (size=50) | Lần đầu (cold, chưa truy cập) | Lần 2 (đã cache) |
|---|---|---|
| 260 | **0.48s** | — |
| 470 | **0.55s** | — |
| 835 | **0.70s** | — |
| 1123 | **1.65s** | — |
| 25 | **0.59s** | 0.36s |
| 410 | **0.57s** | 2.44s* |
| 690 | **0.89s** | 0.58s |
| 970 | **1.00s** | 0.79s |
| 1186 | **1.22s** | 0.78s |

(*) 410 lần 2 chậm hơn lần 1 — nhiễu từ COUNT(*) full-scan (không liên quan dict lookup, xem
dưới), không phải regression cache.

**Instrumentation nội bộ** (log trực tiếp trong route, đã xoá sau khi đo xong) cho 1 trang
chưa truy cập, để tách rõ dict-lookup khỏi phần SQL catalog:
```
[T482_DEBUG] COUNT query: 0.458s        (full-scan COUNT(*) — KHÔNG thuộc phạm vi fix này)
[T482_DEBUG] SELECT page query: 0.378s  (JOIN + LIMIT/OFFSET — đã có index đủ, không đổi)
[T482_DEBUG] dict_matches_by_name: 0.221s   (phần ĐÃ SỬA — trước đây là bottleneck 7.9-13.9s)
```
→ Phần `_t482_dictionary_lookup_batch` (phần bị báo bug) nay **0.000-0.221s mỗi trang**, không
còn phụ thuộc restart. Phần COUNT(*) (full table scan ~59K dòng mỗi lần load trang, SẴN CÓ từ
trước, không phải lỗi mới) dao động 0.3-1.7s — ngoài phạm vi bug này (không liên quan dictionary
lookup), ghi nhận làm việc tiếp theo nếu Admin muốn tối ưu thêm (có thể cache `total` theo `q`).

**2 outlier đã điều tra, KHÔNG thuộc code T482:** request đầu tiên sau mỗi lần start server
(ví dụ 17.7s, 29.7s ở 2 lần đo) — xác minh bằng cùng instrumentation: log KHÔNG in dòng
`[T482_DEBUG]` nào trong suốt thời gian "treo" đó, nghĩa là request còn chưa chạy tới code
route (`_t482_dictionary_lookup_batch` chưa được gọi) — độ trễ nằm ở lớp dưới (lần request đầu
tiên tới 1 process Flask mới, hoặc tranh chấp GIL với job nền `[T148]` index 49.361 person tại
startup, log thấy tốn 36-50s mỗi lần restart — **đây là hành vi SẴN CÓ của `app.py`/`core.py`,
không do T482 gây ra và ngoài phạm vi sửa của task này**). Không sửa phần đó ở đây để tránh
đổi hành vi ngoài phạm vi yêu cầu; ghi lại để Admin quyết định có cần tối ưu `[T148]` riêng.

**Correctness không đổi:** `PL000000000048` ("王寺") vẫn trả đúng 5 kết quả, 2 kết quả đầu từ
nguồn Thông Thiền (ưu tiên cao nhất) — khớp 100% hành vi round 1/round 0.

### 8e. Kết luận

Root cause thật của bug QA báo (7.9-13.9s/trang chưa truy cập) là **build RAM 166K dòng mỗi
lần server restart** (vi phạm Zero-RAM), không phải thiếu index hay N+1 đơn thuần như round 1
khắc phục một phần. Fix round 2 chuyển index sang SQL bền (build 1 lần duy nhất qua migration,
không build lại khi restart) + batch query cho cả trang — phần dictionary lookup (phần bị báo
bug) nay ổn định dưới 0.25s/trang bất kể cold/warm, không còn phụ thuộc số lần restart server.

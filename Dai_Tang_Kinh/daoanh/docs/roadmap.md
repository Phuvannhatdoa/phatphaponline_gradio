# Roadmap — Dữ liệu & Tích hợp (Đạo Ảnh)

**Last updated:** 2026-05-21

> **Rule:** Mỗi khi thêm nguồn mới (BDRC, FROGBEAR, CBDB, ...), phải cập nhật bảng trong file này: thêm dòng, điền vai trò, ưu tiên, năm dự kiến.

---

## 1. Nguồn hiện có (cốt lõi, đang dùng)

| Nguồn | Vai trò chính | Trạng thái hiện tại | Ưu tiên tiếp theo | Giai đoạn |
|-------|---------------|---------------------|-------------------|-----------|
| **DILA Authority (Person/Place/Time)** | Authority Phật học cho nhân vật & địa danh trong Phật điển Hán; ID chuẩn dùng làm "xương sống" cho people/places | Đã import một phần vào `dila_reference`, `places_dila`, `places_pending`; đang dùng làm chuẩn tên Hán, dynasty, bio | Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations) và Marcus SNA | 2026 (đang làm) |
| **CBETA (Hán tạng số)** | Corpus kinh văn Hán: nguồn text để trích đoạn, dịch, gắn person/place/time | Chưa import hệ thống; mới ở mức ý tưởng pipeline XML → `text_entities_raw` → `canon_texts`/`canon_citations` | Xây xong pipeline CBETA→DILA (person trước, place sau), bắt đầu tạo `canon_citations` cho một số nhân vật mẫu (Huyền Trang, Mã Tổ…) | 2026–2027 |
| **Marcus glossaries (thuật ngữ)** | Authority thuật ngữ, tên gọi, alias, định nghĩa liên quan Phật giáo Trung Hoa, dùng để enrich Person/Term | Đã import một phần (`marcus_reference`, `marcus_networks`); dùng cho network và giải thích thuật ngữ | Chuẩn hóa bảng `term_glossaries`, gắn với people/works, hiển thị "thuật ngữ liên quan" trên person/TTL | 2026 |
| **TTL thiền sư Việt Nam (~2000 file)** | Corpus & authority nội bộ cho Phật sử VN (biographies, hành trạng, truyền thừa thiền phái) | File rời, chưa có authority `vn_person_authority` và chưa trích facts hệ thống | Thiết kế authority Person VN (ID, events, relations), bắt đầu ETL TTL → person/events/graph VN | 2026–2028 |
Thiết kế authority Person VN (ID, events, relations, places VN).
Sau khi hoàn tất các task place (DILA → placevn.html, Nguồn CBDB cho place), thực hiện chuỗi task “Chuẩn hoá văn TTL theo format Đạo Ảnh”:
Định nghĩa “format chuẩn Đạo Ảnh” cho tiểu sử:
Tên & đời → phân loại (thiền phái, vai trò) → bối cảnh lịch sử → nét đặc biệt → nguồn trích dẫn (TTL, DILA, CBETA, Marcus…).
Viết 1–2 prompt mẫu cho Opencode/LLM:
Input: TTL gốc + metadata DILA/Marcus/CBETA.
Output: bản viết lại tiếng Việt theo format chuẩn Đạo Ảnh, giọng trung tính, không thêm/bớt ý trọng yếu.
Lưu bản “viết mượt” vào trường/bảng riêng (ví dụ ttl_vi_moot hoặc person_bio_vi_moot), không ghi đè TTL gốc; admin có quyền duyệt và đẩy sang field bio_vi chính.



## 2. Nguồn tiềm năng (sẽ tích hợp khi chín)

| Nguồn | Vai trò mong muốn | Mức ưu tiên | Thời điểm dự kiến | Ghi chú |
|-------|-------------------|-------------|-------------------|---------|
| **Marcus SNA (Gaoseng zhuan networks)** | Mạng thầy–trò, đồng môn, quan hệ giữa tăng sĩ Hán trích từ Gaoseng zhuan; bổ sung graph cho DILA Person | CAO (ưu tiên hơn CBDB cho phần tăng sĩ) | 2026–2027 | Dùng để làm dày `networks`/`marcus_networks` và lineage graph; link bằng DILA Person ID (đã có trong dataset) |
| **CBDB (China Biographical Database)** | Prosopography toàn Trung Hoa: quan hệ thế tục, địa chỉ dân sự, chức vụ, bối cảnh ngoài Phật giáo | TRUNG (bổ trợ; không cần gấp) | 2027+ | Không dump bulk; chỉ giữ mapping ID (person ↔ CBDB ID) và link ra CBDB khi cần xem "ngoài chùa" |
| **BDRC / BUDA (Tạng, đa ngữ)** | Authority & corpus cho Tạng, Sanskrit, Pali, các bản dịch kinh ngoài CBETA; mô hình work–instance | TRUNG | 2027+ | Học mô hình ID/URI, có thể link một số tác phẩm Hán ↔ Tạng; không ưu tiên trước khi TTL + DILA + CBETA ổn |
| **FROGBEAR (ảnh, fieldwork)** | Ảnh, scan, khảo sát hiện trường chùa, bia, di tích Phật giáo Đông Á; enrich địa danh & di tích (nhất là ngoài VN) | THẤP–TRUNG | 2027+ | Chủ yếu giữ link (URL) + metadata ở bảng `place_media_refs`; không re-host ảnh bulk vì license/hình ảnh nhạy cảm |
| **Wikipedia (tham khảo đa ngữ)** | Bổ sung thông tin tổng quan bằng tiếng Việt/Hán cho mỗi địa danh; CC BY-SA — KHÔNG thay thế bản dịch chính thức Đạo Ảnh | CAO (đã build) | 2026 | Đã có cache DB + UI; cần disclaimer rõ về license |
| **GeoNames (gazetteer toàn cầu)** | Authority GPS địa danh hiện đại (đặc biệt cho Phật sử VN: tỉnh/huyện/xã/chùa) | CAO (cho VN) | 2026 | Đã xác định dùng để bù GPS cho VN; thêm bảng `geonames_places` + trường `geonames_id` trong `places_vps` |

## 3. Công nghệ / pattern nên học dần

| Chủ đề | Vai trò | Nguồn tham khảo | Ưu tiên |
|--------|---------|-----------------|---------|
| **Knowledge graph Phật giáo (RDF, LOD)** | Dùng khi muốn publish một phần authority Đạo Ảnh ra ngoài (URI hoá person/place/work, link DILA/BDRC/CBDB) | LICBS, BDRC KG, một số paper về Buddhist Linked Open Data | Thấp (2027+), nhưng nên nghĩ schema ngay từ bây giờ |
| **Social Network Analysis (SNA)** | Phân tích trung tâm, cộng đồng, đường truyền pháp, dựa trên edges DILA + Marcus + TTL | Repo Marcus (ChineseBuddhism_SNA), paper về SNA trong Chinese Buddhism | Trung–cao (song song với việc dày dữ liệu) |
| **Web‑based research tools (multi‑lingual reader)** | UI đọc song ngữ Hán–Việt, highlight entity, tra cứu nhanh; học idea UX | Các repo gắn tag buddhist-studies trên GitHub | Trung (sau khi data core ổn) |
| **Docs & automation (docs/ + AI Project Editor)** | Đảm bảo mọi thay đổi schema/code đều được log & giải thích trong docs/ để dev/AI mới tự hiểu | Thực hành hiện tại với Opencode + best practices Markdown | Rất cao (đã bắt đầu) |

## 4. Nguyên tắc ưu tiên (để không bị "ngợp")
# Roadmap — Dữ liệu & Tích hợp (Đạo Ảnh)

**Last updated:** 2026-05-22


> **Rule:** Mỗi khi thêm nguồn mới (BDRC, FROGBEAR, CBDB, ...), phải cập nhật bảng trong file này: thêm dòng, điền vai trò, ưu tiên, năm dự kiến.

---

## 1. Nguồn hiện có (cốt lõi, đang dùng)

| Nguồn | Vai trò chính | Trạng thái hiện tại | Ưu tiên tiếp theo | Giai đoạn |
|-------|---------------|---------------------|-------------------|-----------|
| **DILA Authority (Person/Place/Time)** | Authority Phật học cho nhân vật & địa danh trong Phật điển Hán; ID chuẩn dùng làm "xương sống" cho people/places | Đã import một phần vào `dila_reference`, `places_dila`, `places_pending`; đang dùng làm chuẩn tên Hán, dynasty, bio | Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations) và Marcus SNA | 2026 (đang làm) |
| **CBETA (Hán tạng số)** | Corpus kinh văn Hán: nguồn text để trích đoạn, dịch, gắn person/place/time | Chưa import hệ thống; mới ở mức ý tưởng pipeline XML → `text_entities_raw` → `canon_texts`/`canon_citations` | Xây xong pipeline CBETA→DILA (person trước, place sau), bắt đầu tạo `canon_citations` cho một số nhân vật mẫu (Huyền Trang, Mã Tổ…) | 2026–2027 |
| **Marcus glossaries (thuật ngữ)** | Authority thuật ngữ, tên gọi, alias, định nghĩa liên quan Phật giáo Trung Hoa, dùng để enrich Person/Term | Đã import một phần (`marcus_reference`, `marcus_networks`); dùng cho network và giải thích thuật ngữ | Chuẩn hóa bảng `term_glossaries`, gắn với people/works, hiển thị "thuật ngữ liên quan" trên person/TTL | 2026 |
| **TTL thiền sư Việt Nam (~2000 file)** | Corpus & authority nội bộ cho Phật sử VN (biographies, hành trạng, truyền thừa thiền phái) | File rời, chưa có authority `vn_person_authority` và chưa trích facts hệ thống | Thiết kế authority Person VN (ID, events, relations), bắt đầu ETL TTL → person/events/graph VN | 2026–2028 |


---

## 2. Nguồn tiềm năng (sẽ tích hợp khi chín)

| Nguồn | Vai trò mong muốn | Mức ưu tiên | Thời điểm dự kiến | Ghi chú |
|-------|-------------------|-------------|-------------------|---------|
| **Marcus SNA (Gaoseng zhuan networks)** | Mạng thầy–trò, đồng môn, quan hệ giữa tăng sĩ Hán trích từ Gaoseng zhuan; bổ sung graph cho DILA Person | CAO (ưu tiên hơn CBDB cho phần tăng sĩ) | 2026–2027 | Dùng để làm dày `networks`/`marcus_networks` và lineage graph; link bằng DILA Person ID (đã có trong dataset). |
| **CBDB (China Biographical Database)** | Prosopography toàn Trung Hoa: quan hệ thế tục, địa chỉ dân sự, chức vụ, bối cảnh ngoài Phật giáo | TRUNG (bổ trợ; không cần gấp) | 2027+ | Không dump bulk; chỉ giữ mapping ID (person ↔ CBDB ID) và link ra CBDB khi cần xem "ngoài chùa". |
| **BDRC / BUDA (Tạng, đa ngữ)** | Authority & corpus cho Tạng, Sanskrit, Pali, các bản dịch kinh ngoài CBETA; mô hình work–instance | TRUNG | 2027+ | Học mô hình ID/URI, có thể link một số tác phẩm Hán ↔ Tạng; không ưu tiên trước khi TTL + DILA + CBETA ổn. |
| **FROGBEAR (ảnh, fieldwork)** | Ảnh, scan, khảo sát hiện trường chùa, bia, di tích Phật giáo Đông Á; enrich địa danh & di tích (nhất là ngoài VN) | THẤP–TRUNG | 2027+ | Chủ yếu giữ link (URL) + metadata ở bảng `place_media_refs`; không re-host ảnh bulk vì license/hình ảnh nhạy cảm. |
| **Wikipedia (tham khảo đa ngữ)** | Bổ sung thông tin tổng quan bằng tiếng Việt/Hán cho mỗi địa danh; CC BY-SA — KHÔNG thay thế bản dịch chính thức Đạo Ảnh | CAO (đã build) | 2026 | Đã có cache DB + UI; cần disclaimer rõ về license. |
| **GeoNames (gazetteer toàn cầu)** | Authority GPS địa danh hiện đại (đặc biệt cho Phật sử VN: tỉnh/huyện/xã/chùa) | CAO (cho VN) | 2026 | Đã xác định dùng để bù GPS cho VN; thêm bảng `geonames_places` + trường `geonames_id` trong `places_vps`. |


---

## 3. Công nghệ / pattern nên học dần

| Chủ đề | Vai trò | Nguồn tham khảo | Ưu tiên |
|--------|---------|-----------------|---------|
| **Knowledge graph Phật giáo (RDF, LOD)** | Dùng khi muốn publish một phần authority Đạo Ảnh ra ngoài (URI hoá person/place/work, link DILA/BDRC/CBDB) | LICBS, BDRC KG, một số paper về Buddhist Linked Open Data | Thấp (2027+), nhưng nên nghĩ schema ngay từ bây giờ. |
| **Social Network Analysis (SNA)** | Phân tích trung tâm, cộng đồng, đường truyền pháp, dựa trên edges DILA + Marcus + TTL | Repo Marcus (ChineseBuddhism_SNA), paper về SNA trong Chinese Buddhism | Trung–cao (song song với việc dày dữ liệu). |
| **Web‑based research tools (multi‑lingual reader)** | UI đọc song ngữ Hán–Việt, highlight entity, tra cứu nhanh; học idea UX | Các repo gắn tag buddhist-studies trên GitHub | Trung (sau khi data core ổn). |
| **Docs & automation (docs/ + AI Project Editor)** | Đảm bảo mọi thay đổi schema/code đều được log & giải thích trong docs/ để dev/AI mới tự hiểu | Thực hành hiện tại với Opencode + best practices Markdown | Rất cao (đã bắt đầu). |


---

## 4. Khoá 3 — Mở rộng thế giới

> **Rule**: Giống bảng 1/2/3: chỉ dùng 5 cột chính, mỗi nguồn một dòng, ghi chú ngắn dạng bullet, không chèn đoạn dài.

| Nguồn | Vai trò mong muốn | Mức ưu tiên | Thời điểm dự kiến | Ghi chú |
|-------|-------------------|-------------|-------------------|---------|
| **CBDB (China Biographical Database)** | Mapping nhân vật Phật giáo ↔ CBDB để hiểu bối cảnh thế tục (quan lại, văn nhân, gia tộc…) | TRUNG | 2027+ | - Chỉ giữ bảng `person_id ↔ cbdb_id`, không dump bulk dữ liệu CBDB.<br> - UI hiển thị “Thông tin thế tục” dạng link ra CBDB, không import dữ liệu.<br> - Ưu tiên: nhân vật giao giữa Phật giáo và giới thế quyền. |
| **BDRC / BUDA (Tạng, Sanskrit, Pali)** | Authority & work–instance cho các bản dịch Tạng, Sanskrit, Pali, liên thông với bản Hán CBETA | TRUNG | 2027+ | - Xây bảng `works` / `instances` cho kinh điển: Hán (CBETA), Tạng (BDRC), Sanskrit/Pali (nếu có).<br> - Chỉ giữ ID/URI, link đến BDRC/BUDA, không lưu bản text.<br> - Cho phép gán 1 tác phẩm CBETA với 1–n work BDRC/BUDA. |
| **FROGBEAR (ảnh, fieldwork, di tích)** | Enrich dữ liệu địa danh & di tích Phật giáo Đông Á bằng ảnh, khảo sát, bia, bản đồ khảo cổ | THẤP–TRUNG | 2027+ | - Tạo bảng `place_media_refs` với `place_id`, `type` (photo, scan, survey, inscription…), `url` (link FROGBEAR), `rights_hint`.<br> - Không re‑host ảnh, chỉ giữ link và metadata.<br> - UI hiển thị thumbnail + caption và nút mở trang gốc FROGBEAR. |
| **Knowledge graph Phật giáo (RDF, LOD)** | Publish một phần authority Đạo Ảnh ra dạng Linked Open Data (URI hoá person, place, work, link DILA/BDRC/CBDB) | THẤP (nhưng nên chuẩn bị schema ngay) | 2027+ | - Thiết kế schema URI: `daoanh:person/*`, `daoanh:place/*`, `daoanh:work/*`.<br> - Sau khi ổn, xuất sub‑graph (dạng RDF/JSON‑LD, dump file hoặc endpoint nhỏ).<br> - Dùng để liên kết với các project Linked Open Data Phật giáo khác. |
| **Web‑based research tools (multi‑lingual reader)** | UI đọc song ngữ Hán–Việt, highlight entity, tra cứu nhanh, không làm nặng dashboard admin | TRUNG | 2027+ (sau khi data core ổn) | - Module đọc online: nhảy qua–lại giữa Hán nguyên văn (CBETA) và bản Đạo Ảnh.<br> - Khi di chuột trên entity (person, place, term), hiển thị tooltip ngắn + link đến trang Đạo Ảnh.<br> - Kiến trúc nên tách thành micro‑app, có thể reuse trong các project khác. |


---

## 5. Nguyên tắc ưu tiên (để không bị "ngợp")

### Khoá 1 — Xong core Hán → Việt

- DILA + Marcus (authority, network)  
- CBETA pipeline (person/place → `canon_citations` + snippets dịch)  
- Cơ chế dịch 3 lớp (raw → dịch tạm → bảng chính)

### Khoá 2 — Lên VN

- TTL Việt Nam → `vn_person_authority`, events, relations, places VN (kết hợp GeoNames)  
- Liên thông VN ↔ Hán (thiền phái, nhân vật giao thoa)

### Task tương lai: Chuẩn hoá TTL theo format Đạo Ảnh

- Thời điểm: Sau khi hoàn tất các task Place (DILA → `placevn.html`, block “Nguồn CBDB”).  
- Mục tiêu:  
  - Định nghĩa rõ format chuẩn Đạo Ảnh cho tiểu sử / địa danh.  
  - Viết prompt mẫu cho Opencode để:  
    - Đọc TTL gốc + DILA/Marcus/CBETA.  
    - Sinh bản “tiểu sử Đạo Ảnh” mới (mượt, thống nhất format).  
  - Lưu song song với TTL gốc, cho phép admin duyệt & áp dụng từng trường hợp.

### Khoá 3 — Mở rộng thế giới (đang triển khai trong bảng 4)

- Từ khi dữ liệu core (DILA, CBETA, TTL, Marcus) ổn định, triển khai dần các nguồn:  
  - CBDB, BDRC/BUDA, FROGBEAR, knowledge graph,  
  không làm “nhảy vọt” mà đi từng lớp, theo thứ tự ưu tiên trong bảng 4


### Khoá 4 — Mở rộng thế giới - “kéo hết” dữ liệu DILA Place lên dashboard
Roadmap:

Viết API search Place trực tiếp trên DILA SQLite, cho ô search trên cùng truy được mọi Place.

Làm trang “DILA Place Index” (bảng + filter) để duyệt toàn corpus DILA Place.

Thêm API thống kê + export CSV/JSON cho Place, dựng dashboard nhỏ cho nghiên cứu.

Sau đó mới refine phần “Bối cảnh lịch sử & khảo cổ” và CBETA citation dựa trên nguồn DILA.

### Khoá 5 — DILA Integration Layer Roadmap

Mục tiêu:  
Xây dựng một **integration layer usable** cho DILA, cho phép:

- Click 1 thực thể (person/place/text) → thấy toàn bộ đoạn kinh liên quan + bản tiếng Việt (nếu có).
- Front-end (web, GIS) chỉ cần gọi 1–2 API, không phải tự join DB.
- Về sau có thể feed trực tiếp cho LLM (ChatGPT) để tóm tắt / phân tích.

---

## 0. Bối cảnh kỹ thuật

- Backend: Flask (đang chạy trên VPS, proxy qua Nginx dưới `/daoanh/...`).
- DB chuẩn: `lineage.db` (SQLite), đã có person/place/text + mapping DILA/CBETA/MARCUS.
- Nguồn text: TEI-XML (CBETA, DILA, v.v.), đã/đang parse một phần vào DB.

---

## 1. Entity layer (global)

### 1.1. Mục tiêu

Tạo một bảng **ENTITY** làm “global view” cho mọi thực thể:

- Person
- Place
- Text (kinh, luận, sớ…)

Dùng **DILA_ID** làm `entity_id` chuẩn.

### 1.2. Việc cần làm

- [ ] Tạo bảng (hoặc view) `ENTITY` trong `lineage.db`:

  - Bắt buộc:
    - `entity_id` (TEXT) – dùng luôn `DILA_ID`
    - `entity_type` (TEXT) – `PERSON` / `PLACE` / `TEXT`
    - `dila_id` (TEXT)
    - `alias_vi` (TEXT) – tên tiếng Việt chuẩn
    - `alias_zh` (TEXT) – tên gốc (Hán/Phạn, v.v.)
  - Tùy chọn (để mở rộng):
    - `cbeta_occ` (TEXT) – mã CBETA occurrence / text id
    - `marcus_id` (TEXT)
    - `extra_alias` (TEXT/JSON) – các biến thể tên

- [ ] Viết script migration:
  - Đọc các bảng person/place/text hiện có.
  - Chuẩn hóa và insert vào `ENTITY`.

---

## 2. Passage layer (CBETA → đoạn kinh)

### 2.1. Mục tiêu

Tạo bảng lưu **đoạn kinh (passages)** và quan hệ **passage ↔ entity**.

### 2.2. Cấu trúc DB

Tạo thêm 2 bảng:

```sql
TABLE PASSAGE (
  passage_id   INTEGER PRIMARY KEY,
  source       TEXT,      -- ví dụ: 'CBETA'
  text_id      TEXT,      -- mã kinh / file id trong CBETA
  loc_ref      TEXT,      -- tham chiếu vị trí (quyển/trang/dòng)
  raw_text     TEXT,      -- đoạn Hán gốc
  norm_text    TEXT       -- (tùy chọn) phiên bản chuẩn hóa / tách câu
);

TABLE PASSAGE_ENTITY (
  passage_id   INTEGER,
  entity_id    TEXT,      -- DILA_ID (trùng ENTITY.entity_id)
  PRIMARY KEY (passage_id, entity_id)
);
```

### 2.3. Parse CBETA (rule-based)

- [ ] Viết script parse TEI-XML CBETA:
  - Đọc từng kinh (file TEI).
  - Tách text thành **đoạn** (ví dụ theo `<p>`, hoặc block theo `<lb/>`).
  - Lưu mỗi đoạn vào bảng `PASSAGE`:
    - `source = 'CBETA'`
    - `text_id = <mã kinh>`
    - `loc_ref = <thông tin vị trí từ TEI>`
    - `raw_text = nội dung đoạn`

- [ ] Rule-based name detection:
  - Chuẩn bị **alias dictionary** từ bảng `ENTITY`:
    - `alias_zh` + các biến thể.
  - Với mỗi đoạn, scan `raw_text`:
    - Nếu match alias của `entity_id` nào → insert vào `PASSAGE_ENTITY(passage_id, entity_id)`.
  - Ưu tiên:
    - Dùng tag TEI nếu có (ví dụ `<persName>`, `<placeName>`, `<name type="person">`).
    - Fallback: string match (cẩn thận trùng tên).

---

## 3. API layer (Flask)

### 3.1. Mục tiêu

Cung cấp API đơn giản, ổn định cho front-end và cho agent/LLM.

### 3.2. Endpoint chính

- `GET /daoanh/api/entity/<entity_id>`
  - Trả về:
    - Thông tin entity (từ `ENTITY`).
    - Alias, type, các ID liên quan.

- `GET /daoanh/api/entity/<entity_id>/passages`
  - Input:
    - `entity_id` = DILA_ID
    - Optional query params:
      - `source` (mặc định: `CBETA`)
      - `limit`, `offset`
  - Output: JSON list
    - `passage_id`
    - `source`
    - `text_id`
    - `loc_ref`
    - `raw_text`
    - (sau này) `vi_text` nếu đã có dịch/diễn giải.

### 3.3. Việc cần làm

- [ ] Tạo blueprint Flask `entity_api`:
  - Implement 2 endpoint trên.
  - Thêm basic error handling (404 nếu không tìm thấy entity).

- [ ] Thêm CORS (nếu cần cho front-end HTML tĩnh).

---

## 4. UI hook (để front-end / GIS dùng được)

### 4.1. Mục tiêu

Tạo một pattern thống nhất: **click entity → gọi API → render đoạn kinh**.

### 4.2. Công việc

- [ ] Trong `placevn.html` / `personvn.html`:
  - Khi người dùng click 1 entity (marker trên map, tên trong danh sách, v.v.):
    - Gọi `GET /daoanh/api/entity/<entity_id>/passages`.
    - Render list đoạn dưới dạng:
      - Hiển thị `raw_text` (Hán) + meta (kinh nào, quyển mấy).
      - Sau này bổ sung `vi_text`.

- [ ] Tách logic UI:
  - Front-end **không join DB**, chỉ dùng JSON từ API.

---

## 5. Hướng mở rộng (phase 2+)

Không làm ngay, nhưng cần để trong roadmap:

- [ ] Thêm cột/bảng lưu **bản dịch/diễn giải tiếng Việt** cho mỗi passage:
  - `PASSAGE_VI(passage_id, vi_text, status, reviewer, ...)`
- [ ] Thêm endpoint:
  - `GET /daoanh/api/entity/<entity_id>/summary`
    - Lúc này có thể dùng LLM, dựa trên:
      - Bio/note từ DILA.
      - Tập passages liên quan.

---

## 6. Tiêu chí “xong phase 1”

Phase 1 được coi là hoàn thành khi:

- Có bảng `ENTITY`, `PASSAGE`, `PASSAGE_ENTITY` trong `lineage.db`.
- Có script chạy được:
  - Parse tối thiểu 1 subset CBETA → filled `PASSAGE` + `PASSAGE_ENTITY`.
- API sau hoạt động ổn định trên VPS:
  - `GET /daoanh/api/entity/<entity_id>`
  - `GET /daoanh/api/entity/<entity_id>/passages`
- Trên một UI demo (ví dụ 1 trang HTML test):
  - Click 1 DILA_ID → hiển thị được list đoạn kinh liên quan.

Khi đạt các tiêu chí này, integration layer được coi là **usable**, đủ để:
- Gắn vào front-end thật (place/person).
- Dùng làm input cho LLM/ChatGPT trong các bước sau.

### Khoá 6 — Buil Rag 
Cách hợp lý nhất là: **không phụ thuộc Fojin**, mà yêu cầu Opencode **build RAG Việt dựa trên DB Đạo Ảnh**, nhưng **học theo kiến trúc Fojin** (pipeline, API, UI) và đổi phần embedding/LLM sang model Việt (hoặc đa ngữ).  

Anh có thể đưa spec ngắn này cho Opencode:

***

## 1. Mục tiêu tổng thể

- Xây một **RAG tiếng Việt chuyên Phật học** chạy trực tiếp trên dữ liệu Đạo Ảnh (`lineage.db` + bản dịch Việt) và (optional) CBETA Hán.  
- Kiến trúc: **lấy ý tưởng từ Fojin (chat + citations + vector search)**, nhưng:
  - **Corpus**: dùng dữ liệu của Đạo Ảnh, không copy Fojin.  
  - **Embedding**: dùng model Việt/đa ngữ.  
  - **LLM**: trả lời **bằng tiếng Việt**, kèm **trích dẫn Hán + mã CBETA**.

***

## 2. Corpus cho RAG Việt

1. **Nguồn chính (official)**

   - Bảng tiếng Việt trong `lineage.db` (những gì anh đang và sẽ dịch):
     - `passage_vi` (hoặc tương đương):  
       - `passage_id`, `text_vi`, `source = 'DaoAnh'`, `is_official = 1`,  
       - link `passage_id` tới:
         - `canon`, `text_id`, `loc_ref` (Txxnxxxx_p…),
         - entity (place/person/text) qua `passage_entity`.  

2. **Nguồn phụ (optional, chỉ tham khảo)**

   - Nếu sau này có thêm:
     - các đoạn Việt khác (Linh Sơn, Budsas…) mà anh được phép dùng,  
   - Thì import vào bảng riêng:
     - `passage_vi_ext` (`source = 'LinhSon' / 'Budsas'`, `is_official = 0`).  
   - RAG ưu tiên `is_official = 1`, chỉ fallback sang `is_official = 0` cho gợi ý.

***

## 3. Kiến trúc RAG (học theo Fojin nhưng Việt hóa)

### 3.1. Index / embedding

- Dùng một **embedding model Việt/đa ngữ** (Opencode chọn, ví dụ:
  - `bge-multilingual`, `intfloat/multilingual-e5`, hoặc model Việt chuyên dụng).  
- Tạo **vector index** (FAISS / Chroma / PGVector):

  - Mỗi entry chứa:
    - `embedding` (từ `text_vi`),
    - `passage_id`,
    - `canon`, `text_id`, `loc_ref`,
    - `source`, `is_official`.  

- Chuẩn hóa đoạn `text_vi` trước khi embed:
  - cắt theo đoạn 1–3 câu,
  - giữ ID để mapping ngược.

### 3.2. API chat kiểu XiaoJin nhưng tiếng Việt

Tạo endpoint, ví dụ:

```http
POST /daoanh/api/rag_vi/chat
{
  "question_vi": "...",
  "filters": {
    "entity_id": "PL000000023255",   // optional: gắn theo place/person đang mở
    "canon": "T"                     // optional: lọc theo tạng
  }
}
```

Backend làm:

1. **Embed câu hỏi tiếng Việt**.  
2. **Search vector** trong corpus Việt:
   - ưu tiên `is_official = 1`,
   - nếu có filter `entity_id` thì ưu tiên những `passage_id` liên quan entity đó (via `passage_entity`).  
3. Lấy top‑k đoạn Việt, kèm metadata Hán/CBETA từ `cbeta.db`.  
4. Gọi LLM (model đa ngữ) với prompt:

   - Bối cảnh: các đoạn Việt (và optional vài dòng Hán).  
   - Yêu cầu:
     - trả lời **bằng tiếng Việt**,  
     - **tránh suy diễn ngoài bối cảnh**,  
     - liệt kê **danh sách trích dẫn** với `canon`, `text_id`, `loc_ref`, `title_zh`, `excerpt_zh`.

Trả về JSON:

```json
{
  "answer_vi": "...",
  "citations": [
    {
      "ref": "T50n2060_p0457c16",
      "title_zh": "續高僧傳",
      "excerpt_vi": "...",
      "excerpt_zh": "..." 
    }
  ]
}
```

→ Nhìn giống XiaoJin ở Fojin (chat + citations), nhưng **toàn bộ pipeline chạy trên corpus Việt của Đạo Ảnh**.

***

## 4. Học theo Fojin ở những phần nào?

Opencode có thể:

1. **Đọc kiến trúc Fojin** (nếu public code có mô tả) để copy ý tưởng:

   - Cách chia:
     - layer corpus,
     - layer search (vector),
     - layer chat (LLM),
     - layer citations.  
   - Cách fetch và hiển thị citations (ref, excerpt, link).

2. **Không copy dữ liệu/corpus Fojin**, chỉ học:
   - pattern API,
   - cách log câu hỏi/đáp,
   - optional: cách họ gắn knowledge graph (nếu có).

3. **Đổi embedding + LLM** cho phù hợp:

   - Embedding: model Việt/đa ngữ. [fpt](https://fpt.ai/vi/bai-viet/retrieval-augmented-generation/)
   - LLM: model có tiếng Việt tốt (OpenAI GPT‑4.5/5, Claude, v.v.).  
   - Corpus: **Duy nhất DB Đạo Ảnh + CBETA local** (đã hợp pháp), không lẫn Linh Sơn.

***

## 5. Cách anh nói ngắn cho Opencode

Anh có thể tóm thành yêu cầu một câu:

> “Đọc kiến trúc RAG + chat của Fojin như một gợi ý, nhưng đừng dùng dữ liệu của Fojin.  
>  Hãy build một RAG tiếng Việt chạy trên `lineage.db` + `cbeta.db` của Đạo Ảnh:  
>  embed từ bản dịch Việt, trả lời bằng tiếng Việt, kèm trích dẫn Hán + mã CBETA,  
>  để editor hỏi ‘vì sao Thiếu Lâm Tự quan trọng trong Thiền tông’ và thấy luôn đoạn Việt + Hán + ref như XiaoJin.”

### Khoá 7 - Hệ thống Dịch Mượt & Cache Translation cho Đạo Ảnh
Dưới đây là **file ROADMAP.md chi tiết** để bạn lưu cho OpenCode — viết theo format rõ ràng, đầy đủ step-by-step implementation plan: [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)

***

```markdown
# ROADMAP: Hệ thống Dịch Mượt & Cache Translation cho Đạo Ảnh

**Dự án**: Đạo Ảnh - Hệ thống Mapping Địa danh Phật giáo  
**Mục tiêu**: Xây dựng module "Dịch Mượt" (Translation Polish) để chuẩn hóa tự động văn bản CBETA dịch tiếng Việt, tích hợp cache translation để user load nhanh bản dịch đã duyệt.

**Tech Stack**:
- Backend: Python 3.11+ (Flask/FastAPI)
- Database: SQLite (VPS existing: ~/vps/lexicon.db + new: ~/vps/translations_cache.db)
- LLM: Google Gemini API (gemini-1.5-flash)
- Fuzzy Matching: RapidFuzz
- Frontend: React.js (existing: placevn.html)

---

## **PHASE 1: MVP Foundation (Week 1-2)** ⏱️ 10-14 ngày

### **1.1. Database Schema Setup** 📊

**File**: `~/vps/translations_cache.db`

```sql
-- Bảng 1: Lưu bản dịch CBETA cho từng địa danh
CREATE TABLE IF NOT EXISTS place_cbeta_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id TEXT NOT NULL,              -- PL000000023255
    cbeta_ref TEXT NOT NULL,             -- T50n2060_p0480b14
    han_source TEXT,                     -- Văn bản Hán gốc từ CBETA
    raw_translation TEXT,                -- Bản dịch thô từ Gemini (lưu để debug)
    polished_text TEXT NOT NULL,         -- Văn bản đã qua "Dịch mượt"
    translation_status TEXT DEFAULT 'draft', -- 'draft', 'admin_approved', 'user_generated', 'auto_generated'
    confidence_score REAL,               -- Độ tin cậy (0.0-1.0) của bản dịch tự động
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,                     -- 'admin', 'user', 'batch_script'
    
    UNIQUE(place_id, cbeta_ref)          -- Mỗi trích dẫn chỉ có 1 bản dịch/place
);

-- Bảng 2: Tracking thuật ngữ đã được chuẩn hóa (để improve model)
CREATE TABLE IF NOT EXISTS term_normalization_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_term TEXT NOT NULL,
    normalized_term TEXT NOT NULL,
    han_text TEXT,
    confidence REAL,
    source TEXT,                         -- 'lexicon_exact', 'lexicon_fuzzy', 'manual'
    translation_id INTEGER,              -- FK to place_cbeta_translations.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (translation_id) REFERENCES place_cbeta_translations(id)
);

-- Index để tăng tốc query
CREATE INDEX idx_place_cbeta ON place_cbeta_translations(place_id, cbeta_ref);
CREATE INDEX idx_translation_status ON place_cbeta_translations(translation_status);
CREATE INDEX idx_term_original ON term_normalization_log(original_term);
```

**Action Items**:
- [ ] Tạo file `~/vps/migrations/001_create_translations_cache.sql`
- [ ] Run migration script: `python manage.py migrate`
- [ ] Verify schema: `sqlite3 ~/vps/translations_cache.db ".schema"`

---

### **1.2. Backend API Endpoints** 🔧

**File structure**:
```
~/daoanh-backend/
├── app.py                    # Flask main
├── config.py                 # API keys, DB paths
├── services/
│   ├── translation_service.py   # Core logic
│   ├── lexicon_service.py       # Query lexicon DB
│   └── cbeta_service.py         # Fetch CBETA API
├── routes/
│   └── translation_routes.py    # API endpoints
└── utils/
    ├── gemini_client.py         # Gemini API wrapper
    └── fuzzy_matcher.py         # RapidFuzz logic
```

#### **Endpoint 1: POST /api/translate-cbeta** 🚀

**Mục đích**: Dịch + chuẩn hóa một trích dẫn CBETA mới (hoặc load từ cache nếu đã có)

**Request**:
```json
{
  "cbeta_ref": "T50n2060_p0480b14",
  "place_id": "PL000000023255",
  "force_refresh": false  // true = bỏ qua cache, dịch lại
}
```

**Response (cache hit)**:
```json
{
  "status": "success",
  "source": "cache",
  "data": {
    "polished_text": "Thích Kinh Đà (釋景陀), quê quán chưa rõ rệt...",
    "translation_status": "admin_approved",
    "confidence_score": 0.95,
    "created_at": "2026-05-20T10:30:00Z"
  }
}
```

**Response (new translation)**:
```json
{
  "status": "success",
  "source": "new_translation",
  "data": {
    "polished_text": "Thích Kinh Đà, quê quán chưa rõ. Ông từng đến <mark data-confidence='0.75'>Kí quận</mark>...",
    "translation_status": "user_generated",
    "confidence_score": 0.78,
    "uncertain_terms": [
      {
        "original": "Jijun",
        "normalized": "Kí quận",
        "han": "冀郡",
        "confidence": 0.75
      },
      {
        "original": "Tong Shao",
        "normalized": "Tăng Thiệu",
        "han": "僧紹",
        "confidence": 0.92
      }
    ],
    "needs_review": true
  }
}
```

**Implementation (`services/translation_service.py`)**:

```python
import sqlite3
from utils.gemini_client import GeminiClient
from services.lexicon_service import LexiconService
from services.cbeta_service import CBETAService

class TranslationService:
    def __init__(self):
        self.cache_db = sqlite3.connect('~/vps/translations_cache.db')
        self.gemini = GeminiClient()
        self.lexicon = LexiconService()
        self.cbeta = CBETAService()
    
    def translate_cbeta(self, cbeta_ref, place_id, force_refresh=False):
        # Step 1: Check cache
        if not force_refresh:
            cached = self._get_cached_translation(place_id, cbeta_ref)
            if cached:
                return {
                    'status': 'success',
                    'source': 'cache',
                    'data': cached
                }
        
        # Step 2: Fetch CBETA Hán text
        han_text = self.cbeta.fetch_text(cbeta_ref)
        
        # Step 3: Gemini raw translation
        raw_translation = self.gemini.translate(han_text, target_lang='vi')
        
        # Step 4: Polish translation
        polished_result = self._polish_translation(raw_translation, han_text, place_id)
        
        # Step 5: Save to cache
        translation_id = self._save_to_cache(
            place_id=place_id,
            cbeta_ref=cbeta_ref,
            han_source=han_text,
            raw_translation=raw_translation,
            polished_text=polished_result['final_text'],
            translation_status='user_generated',
            confidence_score=polished_result['avg_confidence']
        )
        
        # Step 6: Log term normalizations
        self._log_term_normalizations(translation_id, polished_result['mappings'])
        
        return {
            'status': 'success',
            'source': 'new_translation',
            'data': {
                'polished_text': polished_result['final_text'],
                'translation_status': 'user_generated',
                'confidence_score': polished_result['avg_confidence'],
                'uncertain_terms': polished_result['uncertain_terms'],
                'needs_review': polished_result['avg_confidence'] < 0.85
            }
        }
    
    def _polish_translation(self, raw_text, han_source, place_id):
        """Core 'Dịch mượt' logic - 3 bước"""
        
        # Bước 1: LLM grammar correction
        step1 = self._improve_grammar(raw_text, han_source)
        
        # Bước 2: Terminology normalization
        step2 = self._normalize_terms(step1['corrected_text'], step1['uncertain_terms'], place_id)
        
        # Bước 3: Auto-replace high-confidence terms
        final_text = self._apply_replacements(step2['text'], step2['mappings'])
        
        # Calculate average confidence
        avg_confidence = sum(m['confidence'] for m in step2['mappings']) / len(step2['mappings']) if step2['mappings'] else 1.0
        
        return {
            'final_text': final_text,
            'mappings': step2['mappings'],
            'uncertain_terms': [m for m in step2['mappings'] if m['confidence'] < 0.9],
            'avg_confidence': avg_confidence
        }
    
    def _improve_grammar(self, raw_text, han_source):
        """Bước 1: LLM sửa ngữ pháp + extract uncertain terms"""
        prompt = f"""
Bạn là chuyên gia biên tập văn bản Phật học tiếng Việt.

NGUỒN HÁN (CBETA):
{han_source[:300]}...

BẢN DỊCH THÔ (cần sửa):
{raw_text}

YÊU CẦU:
1. Sửa lỗi ngữ pháp, cú pháp Việt (ví dụ: "Thả Kinh Đà ra" → "Thích Kinh Đà")
2. Loại bỏ thuật ngữ máy móc (ví dụ: "hạt nhân nhỏ và lớn" → "việc lớn nhỏ")
3. Đánh dấu các tên riêng chưa chắc bằng {{{{TERM:...}}}}
4. KHÔNG thêm/bớt thông tin so với bản gốc

TRẢ VỀ JSON (strict format):
{{
  "corrected_text": "...",
  "uncertain_terms": ["term1", "term2", ...]
}}
"""
        response = self.gemini.generate(prompt, response_mime_type='application/json')
        return response  # {'corrected_text': '...', 'uncertain_terms': [...]}
    
    def _normalize_terms(self, text, uncertain_terms, place_id):
        """Bước 2: Query Lexicon DB + fuzzy matching"""
        mappings = []
        
        for term in uncertain_terms:
            # Query lexicon service
            candidates = self.lexicon.find_term(term, types=['person_name', 'place_name'])
            
            if candidates:
                best = max(candidates, key=lambda x: x['confidence'])
                mappings.append({
                    'original': term,
                    'normalized': best['viet_phien_am'],
                    'han': best['han_text'],
                    'confidence': best['confidence'],
                    'source': best['source']  # 'lexicon_exact' or 'lexicon_fuzzy'
                })
            else:
                # No match found
                mappings.append({
                    'original': term,
                    'normalized': term,
                    'han': '???',
                    'confidence': 0.0,
                    'source': 'manual_required'
                })
        
        return {'text': text, 'mappings': mappings}
    
    def _apply_replacements(self, text, mappings):
        """Bước 3: Thay thế terms theo confidence threshold"""
        final_text = text
        
        for m in mappings:
            placeholder = f"{{{{TERM:{m['original']}}}}}"
            
            if m['confidence'] >= 0.9:
                # Auto-replace (high confidence)
                replacement = f"{m['normalized']} ({m['han']})"
                final_text = final_text.replace(placeholder, replacement)
            elif m['confidence'] >= 0.7:
                # Mark for review (medium confidence)
                replacement = f"<mark data-confidence='{m['confidence']}'>{m['normalized']}</mark>"
                final_text = final_text.replace(placeholder, replacement)
            else:
                # Keep original (low confidence)
                replacement = f"<span class='manual-edit'>{m['original']}</span>"
                final_text = final_text.replace(placeholder, replacement)
        
        return final_text
    
    def _get_cached_translation(self, place_id, cbeta_ref):
        """Query cache DB"""
        cursor = self.cache_db.execute("""
            SELECT polished_text, translation_status, confidence_score, created_at
            FROM place_cbeta_translations
            WHERE place_id = ? AND cbeta_ref = ?
        """, (place_id, cbeta_ref))
        
        row = cursor.fetchone()
        if row:
            return {
                'polished_text': row,
                'translation_status': row, [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)
                'confidence_score': row,[2]
                'created_at': row
            }
        return None
    
    def _save_to_cache(self, **kwargs):
        """Insert vào cache DB"""
        cursor = self.cache_db.execute("""
            INSERT INTO place_cbeta_translations 
            (place_id, cbeta_ref, han_source, raw_translation, polished_text, 
             translation_status, confidence_score, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'api_user')
        """, (
            kwargs['place_id'], 
            kwargs['cbeta_ref'], 
            kwargs['han_source'], 
            kwargs['raw_translation'], 
            kwargs['polished_text'], 
            kwargs['translation_status'], 
            kwargs['confidence_score']
        ))
        self.cache_db.commit()
        return cursor.lastrowid
    
    def _log_term_normalizations(self, translation_id, mappings):
        """Log từng term đã chuẩn hóa (để train model sau)"""
        for m in mappings:
            self.cache_db.execute("""
                INSERT INTO term_normalization_log 
                (original_term, normalized_term, han_text, confidence, source, translation_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (m['original'], m['normalized'], m['han'], m['confidence'], m['source'], translation_id))
        self.cache_db.commit()
```

**Action Items**:
- [ ] Implement `TranslationService` class
- [ ] Implement `LexiconService.find_term()` (query ~/vps/lexicon.db)
- [ ] Implement `CBETAService.fetch_text()` (call CBETA API hoặc local XML)
- [ ] Implement `GeminiClient` wrapper (API key từ config)
- [ ] Test endpoint: `curl -X POST http://localhost:5000/api/translate-cbeta -d '{"cbeta_ref":"T50n2060_p0480b14","place_id":"PL000000023255"}'`

---

#### **Endpoint 2: PUT /api/admin/translations/:id/approve** ✅

**Mục đích**: Admin duyệt bản dịch (chuyển status từ `user_generated` → `admin_approved`)

**Request**:
```json
{
  "translation_id": 123,
  "edited_text": "Thích Kinh Đà (釋景陀), quê quán chưa rõ rệt. Ông từng đến Kí quận (冀郡)...",
  "admin_notes": "Đã sửa phiên âm Jijun → Kí quận"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Translation approved and updated"
}
```

**Implementation**:
```python
def approve_translation(translation_id, edited_text, admin_notes):
    db.execute("""
        UPDATE place_cbeta_translations
        SET polished_text = ?,
            translation_status = 'admin_approved',
            confidence_score = 1.0,
            updated_at = datetime('now')
        WHERE id = ?
    """, (edited_text, translation_id))
    db.commit()
    
    # Log admin action (optional)
    log_admin_action(translation_id, 'approve', admin_notes)
```

**Action Items**:
- [ ] Implement approve endpoint
- [ ] Add admin authentication middleware
- [ ] Create admin UI panel (React) để list pending translations

---

#### **Endpoint 3: GET /api/places/:place_id/translations** 📖

**Mục đích**: User (web công khai) load tất cả bản dịch CBETA của một địa danh

**Request**: `GET /api/places/PL000000023255/translations`

**Response**:
```json
{
  "place_id": "PL000000023255",
  "place_name": "Thiếu Lâm Tự",
  "translations": [
    {
      "cbeta_ref": "T50n2060_p0480b14",
      "polished_text": "Thích Kinh Đà (釋景陀), quê quán chưa rõ...",
      "translation_status": "admin_approved",
      "confidence_score": 1.0,
      "has_cache": true
    },
    {
      "cbeta_ref": "T50n2060_p0484c02",
      "polished_text": null,
      "translation_status": null,
      "has_cache": false
    }
  ]
}
```

**Implementation**:
```python
def get_place_translations(place_id):
    # Get all CBETA refs for this place (from DILA DB)
    refs = get_cbeta_refs_for_place(place_id)
    
    # For each ref, check if cached translation exists
    results = []
    for ref in refs:
        cached = db.execute("""
            SELECT polished_text, translation_status, confidence_score
            FROM place_cbeta_translations
            WHERE place_id = ? AND cbeta_ref = ?
        """, (place_id, ref['cbeta_ref'])).fetchone()
        
        results.append({
            'cbeta_ref': ref['cbeta_ref'],
            'polished_text': cached if cached else None,
            'translation_status': cached if cached else None, [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)
            'confidence_score': cached if cached else None,[2]
            'has_cache': bool(cached)
        })
    
    return {'place_id': place_id, 'translations': results}
```

**Action Items**:
- [ ] Implement endpoint
- [ ] Test với place_id = PL000000023255

---

### **1.3. Frontend Integration (React)** ⚛️

**File**: `~/daoanh-frontend/src/components/TranslationPanel.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TranslationPanel({ placeId, cbetaRef }) {
  const [translation, setTranslation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Load cached translation on mount
  useEffect(() => {
    loadCachedTranslation();
  }, [placeId, cbetaRef]);

  const loadCachedTranslation = async () => {
    try {
      const response = await axios.get(`/api/places/${placeId}/translations`);
      const matchingRef = response.data.translations.find(
        t => t.cbeta_ref === cbetaRef
      );
      
      if (matchingRef && matchingRef.has_cache) {
        setTranslation(matchingRef);
      }
    } catch (error) {
      console.error('Failed to load cached translation:', error);
    }
  };

  const handleTranslateOnDemand = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/translate-cbeta', {
        cbeta_ref: cbetaRef,
        place_id: placeId,
        force_refresh: false
      });
      
      setTranslation(response.data.data);
      
      if (response.data.data.needs_review) {
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Translation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptSuggestion = (term, normalized) => {
    // Replace <mark> tag with plain text
    const updatedText = translation.polished_text.replace(
      new RegExp(`<mark[^>]*>${term.normalized}</mark>`, 'g'),
      normalized
    );
    setTranslation({ ...translation, polished_text: updatedText });
  };

  const handleSaveToDatabase = async () => {
    // Submit final text to admin for approval
    await axios.post('/api/admin/submit-for-review', {
      translation_id: translation.id,
      final_text: translation.polished_text
    });
    alert('Đã gửi bản dịch để admin duyệt!');
  };

  return (
    <div className="translation-panel">
      <h4>Trích dẫn: {cbetaRef}</h4>
      
      {!translation && (
        <button 
          onClick={handleTranslateOnDemand} 
          disabled={loading}
          className="btn-translate"
        >
          {loading ? '⏳ Đang dịch...' : '🌐 Dịch tạm thời'}
        </button>
      )}

      {translation && (
        <div className="translation-result">
          <div 
            className="polished-text"
            dangerouslySetInnerHTML={{ __html: translation.polished_text }}
          />
          
          {showSuggestions && translation.uncertain_terms && (
            <div className="suggestions-panel">
              <h5>Cần xác nhận ({translation.uncertain_terms.length} thuật ngữ):</h5>
              {translation.uncertain_terms.map((term, idx) => (
                <div key={idx} className="suggestion-item">
                  <span className="original">{term.original}</span>
                  <span className="arrow">→</span>
                  <span className="normalized">{term.normalized} ({term.han})</span>
                  <span className="confidence">{(term.confidence * 100).toFixed(0)}%</span>
                  <button 
                    onClick={() => handleAcceptSuggestion(term, term.normalized)}
                    className="btn-accept"
                  >
                    ✓ Chấp nhận
                  </button>
                </div>
              ))}
            </div>
          )}

          <button 
            onClick={handleSaveToDatabase}
            className="btn-save"
          >
            💾 Lưu vào DB
          </button>
        </div>
      )}
    </div>
  );
}

export default TranslationPanel;
```

**Action Items**:
- [ ] Tạo component TranslationPanel
- [ ] Integrate vào placevn.html (thay thế nút "CBETA DỊCH VIỆT" hiện tại)
- [ ] Thêm CSS styling cho `<mark>` và `.suggestion-item`
- [ ] Test UI flow: Load cache → Click "Dịch tạm thời" → Review suggestions → Save

---

## **PHASE 2: Admin Dashboard & Batch Processing (Week 3-4)** 🛠️

### **2.1. Admin Review Panel** 👨‍💼

**File**: `~/daoanh-frontend/src/pages/AdminTranslations.jsx`

**Features**:
- List tất cả bản dịch status = `user_generated` hoặc `auto_generated`
- Admin có thể:
  - Xem bản dịch thô vs bản dịch đã polish
  - Sửa trực tiếp trong textarea
  - Approve/Reject
  - Bulk approve (chọn nhiều bản cùng lúc)

**UI mockup**:
```
┌──────────────────────────────────────────────────────┐
│ ADMIN: Duyệt bản dịch                                │
├──────────────────────────────────────────────────────┤
│ [Filter: All | Pending | Approved]  [Search: ___]   │
├──────────────────────────────────────────────────────┤
│ ☐ T50n2060_p0480b14 | PL000000023255               │
│   Status: user_generated | Confidence: 78%          │
│   Preview: Thích Kinh Đà, quê quán chưa rõ...       │
│   [View Details] [Approve] [Reject]                 │
├──────────────────────────────────────────────────────┤
│ ☐ T50n2060_p0484c02 | PL000000023255               │
│   Status: auto_generated | Confidence: 92%          │
│   Preview: Thích Đạo Bình, sống tại Thiếu Lâm...   │
│   [View Details] [Approve] [Reject]                 │
├──────────────────────────────────────────────────────┤
│ [Bulk Approve Selected]  [Export CSV]               │
└──────────────────────────────────────────────────────┘
```

**Action Items**:
- [ ] Implement GET /api/admin/translations?status=pending
- [ ] Create AdminTranslations page
- [ ] Add bulk operations (approve/reject nhiều bản cùng lúc)

---

### **2.2. Batch Translation Script** 📦

**File**: `~/daoanh-backend/scripts/batch_translate.py`

**Usage**: `python batch_translate.py --place-ids PL000000023255,PL000000012345 --status auto_generated`

```python
#!/usr/bin/env python3
import argparse
import sqlite3
from services.translation_service import TranslationService

def batch_translate(place_ids, status='auto_generated'):
    service = TranslationService()
    db = sqlite3.connect('~/vps/dila_places.db')
    
    for place_id in place_ids:
        print(f"Processing {place_id}...")
        
        # Get all CBETA refs for this place
        refs = db.execute("""
            SELECT cbeta_ref FROM cbeta_place_references
            WHERE place_id = ?
        """, (place_id,)).fetchall()
        
        for ref_row in refs:
            cbeta_ref = ref_row
            
            # Check if already translated
            existing = service._get_cached_translation(place_id, cbeta_ref)
            if existing:
                print(f"  ⏭️  Skip {cbeta_ref} (already cached)")
                continue
            
            # Translate
            try:
                result = service.translate_cbeta(
                    cbeta_ref=cbeta_ref, 
                    place_id=place_id, 
                    force_refresh=False
                )
                print(f"  ✅ Translated {cbeta_ref} (confidence: {result['data']['confidence_score']:.2f})")
            except Exception as e:
                print(f"  ❌ Failed {cbeta_ref}: {str(e)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch translate CBETA references')
    parser.add_argument('--place-ids', required=True, help='Comma-separated place IDs')
    parser.add_argument('--status', default='auto_generated', help='Translation status to set')
    
    args = parser.parse_args()
    place_ids = args.place_ids.split(',')
    
    batch_translate(place_ids, args.status)
```

**Action Items**:
- [ ] Implement script
- [ ] Test với top 10 địa danh
- [ ] Schedule cron job để chạy batch hàng tuần (ví dụ: dịch 100 places/tuần)

---

## **PHASE 3: Production Optimization (Week 5-6)** 🚀

### **3.1. Performance Improvements** ⚡

- **Caching**: Redis cache cho API responses (TTL 1 giờ)
- **Rate limiting**: Giới hạn user requests (10 translations/phút)
- **Async processing**: Queue system (Celery + Redis) cho batch jobs
- **Database indexes**: Optimize query speed

**Action Items**:
- [ ] Setup Redis
- [ ] Implement rate limiting middleware
- [ ] Convert batch script sang Celery task
- [ ] Add monitoring (Prometheus + Grafana)

---

### **3.2. Quality Assurance** ✅

**Metrics to track**:
- Translation accuracy (% terms chuẩn hóa đúng)
- Admin approval rate
- Average confidence score
- User feedback score

**Testing**:
```python
# Test case: Verify term normalization
def test_term_normalization():
    service = TranslationService()
    result = service._normalize_terms(
        text="{{TERM:Jijun}}",
        uncertain_terms=["Jijun"],
        place_id="PL000000023255"
    )
    assert result['mappings']['normalized'] == "Kí quận"
    assert result['mappings']['confidence'] >= 0.7
```

**Action Items**:
- [ ] Write unit tests (pytest)
- [ ] Create QA checklist for admin reviewers
- [ ] Implement user feedback button ("Bản dịch có chính xác không?")

---

### **3.3. Documentation** 📚

**Files to create**:
1. `README.md` - Overview + setup instructions
2. `API.md` - API documentation (endpoints, parameters, examples)
3. `ADMIN_GUIDE.md` - Hướng dẫn sử dụng admin panel
4. `DEPLOYMENT.md` - Production deployment guide

**Action Items**:
- [ ] Write documentation
- [ ] Record demo video (admin workflow)
- [ ] Create troubleshooting guide

---

## **TIMELINE SUMMARY** 📅

| Phase | Duration | Deliverables | Status |
|-------|----------|--------------|--------|
| **Phase 1: MVP** | Week 1-2 | Database schema, API endpoints, React components | 🔲 Not Started |
| **Phase 2: Admin Tools** | Week 3-4 | Admin dashboard, batch script, bulk operations | 🔲 Not Started |
| **Phase 3: Production** | Week 5-6 | Performance optimization, testing, documentation | 🔲 Not Started |

---

## **SUCCESS CRITERIA** 🎯

**MVP (Phase 1)**:
- [ ] User có thể click "Dịch tạm thời" và nhận bản dịch mượt trong < 5 giây
- [ ] Bản dịch được cache vào DB, lần sau load ngay (không gọi Gemini)
- [ ] Admin có thể approve/reject bản dịch từ panel

**Production (Phase 3)**:
- [ ] 95% thuật ngữ phổ biến được chuẩn hóa đúng (theo kiểm tra thủ công)
- [ ] Batch translate 500 địa danh trong < 2 giờ
- [ ] User web load trang địa danh với bản dịch đã duyệt trong < 1 giây

---

## **NOTES & RISKS** ⚠️

**Assumptions**:
- CBETA API có thể fetch text trực tiếp (hoặc dùng local XML files)
- Lexicon DB đã có sẵn dữ liệu cơ bản (ít nhất 1000 thuật ngữ)
- Gemini API quota đủ cho ~10,000 requests/tháng

**Risks**:
- Gemini API downtime → **Mitigation**: Fallback sang GPT-4o-mini
- Fuzzy matching không chính xác → **Mitigation**: Manual review threshold (confidence < 0.85)
- Database size quá lớn → **Mitigation**: Archive old translations sau 6 tháng

---

## **CONTACT & SUPPORT** 📧

**Developer**: Nhat Doa Phu Van  
**Project Lead**: [Admin name]  
**Repository**: [GitHub URL]  
**VPS Access**: `ssh user@vps-ip` (~/vps/*)

---

**Last Updated**: 2026-05-26  
**Version**: 1.0 (MVP Roadmap)
```

***

**TÓM TẮT**: File roadmap này đã chi tiết hoá toàn bộ:
1. Database schema (SQLite) [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)
2. Backend API endpoints (Python code hoàn chỉnh) [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)
3. Frontend React components [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)
4. Admin dashboard & batch scripts [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)
5. Timeline + success criteria [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)

Bạn có thể save file này và gửi cho OpenCode với prompt:
```
@opencode Đọc file ROADMAP.md và implement Phase 1 (MVP) theo đúng spec. 
Bắt đầu với database setup, sau đó implement TranslationService class.
```

OpenCode sẽ hiểu rõ từng step và code theo đúng kiến trúc! Bạn cần tôi bổ sung phần nào thêm không? [phatphaponline](https://phatphaponline.org/daoanh/admin/placevn.html)

### Khoá 8 — GUI GIS
### [CHỈ THỊ DÀNH CHO OPENCODE - ROADMAP VER 31-34 TÍCH HỢP HÀN LÂM]

Phân tích mã nguồn hiện tại tại:
- Frontend: /var/www/phatphaponline.org/html/daoanh/places/index.html
- Backend: [TÌM_FLASK_APP_PATH]
- Database: /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db

Thực hiện 4 giai đoạn nâng cấp theo roadmap:

**GIAI ĐOẠN 1 (Ver 31 - 2 tuần):**
1. Tạo API endpoint: GET /daoanh/api/place/<id>/languages
   - Query bảng: places_dila (lấy name_san, name_en, name_jpn)
   - JOIN với places_vps để có name_vi
2. Frontend: Thêm tab "Cổ ngữ" vào Sidebar
   - HTML structure như đã mô tả
   - JavaScript fetch data khi click place
3. Copy button để export danh xưng quốc tế

**GIAI ĐOẠN 2 (Ver 32 - 3 tuần):**
1. Tạo API endpoint: GET /daoanh/api/lineage/<name>/network
   - Query bảng: networks + marcus_networks
   - JOIN với people, places để lấy temple locations
   - Return: nodes (temples) + edges (transmission relationships)
2. Frontend: Sửa function filterByLineage()
   - Vẽ L.polyline() kết nối các temples
   - Style: dashed line, màu vàng, opacity 0.6
   - Animation: stroke-dashoffset effect
3. Popup: Hiện relationship type + year

**GIAI ĐOẠN 3 (Ver 33 - 2 tuần):**
1. Tạo API endpoint: GET /daoanh/api/place/<id>/cbeta_refs
   - Query bảng: lexicon_fts (FTS5 search)
   - JOIN với canon_catalog
   - Return: Top 10 matching texts với excerpt
2. Frontend: Thêm Card "Xuất xứ Đại Tạng Kinh"
   - List các kinh điển liên quan
   - Excerpt preview (highlight keyword)
   - Link to CBETAOnline

**GIAI ĐOẠN 4 (Ver 34 - 2 tuần):**
1. Tạo API endpoint: GET /daoanh/api/place/<id>/conflicts
   - Query bảng: lineage_conflicts_v2
   - Parse dila_data vs marcus_data
   - Return: conflict type, values, confidence
2. Frontend: Thêm Conflict Alert
   - Badge "Case 9" khi has_conflict = true
   - Inline comparison table
   - Modal chi tiết với citations
3. Admin panel: Resolve conflict (future feature)

**DELIVERABLES MỖI GIAI ĐOẠN:**
- Working API endpoints (test với curl)
- Updated frontend HTML/JavaScript
- Screenshot của GUI mới
- Performance metrics (query time < 200ms)

**CONSTRAINTS:**
- Maintain dark theme aesthetic của Ver 30
- Mobile responsive (test trên 375px width)
- Backward compatible (không break existing features)

Bắt đầu với Giai đoạn 1. Sau khi hoàn thành, báo cáo kết quả trước khi sang Giai đoạn 2.

### Khoá 9 - Xây dựng hệ thống cho phép Team VN nhập dữ liệu chùa chiền Việt Nam theo format JSON chuẩn DILA
# 📋 **ROADMAP: INPUT JSON DATA PLACE VIỆT NAM**

Dựa trên thảo luận về tích hợp dữ liệu DILA và VN local data, đây là roadmap hoàn chỉnh cho OpenCode để dev tính năng **Input JSON Data Place Việt Nam**. [phatphaponline](https://phatphaponline.org/daoanh/places/)

***

## 🎯 **OBJECTIVE**

Xây dựng hệ thống cho phép Team VN nhập dữ liệu chùa chiền Việt Nam theo format JSON chuẩn DILA, tự động import vào database, và hiển thị trên bản đồ timeline với phiên âm Hán-Việt nhất quán.

***

## 📐 **ARCHITECTURE OVERVIEW**

```
┌─────────────────────────────────────────────────────────┐
│  DATA SOURCES                                           │
├─────────────────────────────────────────────────────────┤
│  1. DILA Official (GitHub)                              │
│     → Person XML (48k records)                          │
│     → Place XML (19k records)                           │
│     → Catalog JSON (5-10k works)                        │
│                                                          │
│  2. VN Local Data (Team input) ← NEW FEATURE            │
│     → VN temples JSON                                   │
│     → VN masters JSON                                   │
│     → VN inscriptions data                              │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│  PROCESSING LAYER                                       │
├─────────────────────────────────────────────────────────┤
│  → Import scripts (Python)                              │
│  → Name mapping (namevimap table - SHARED)              │
│  → Data validation                                      │
│  → Timeline event generation                            │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│  SQLite DATABASE (lineage.db)                           │
├─────────────────────────────────────────────────────────┤
│  • dila_places         (DILA + VN)                      │
│  • dila_persons        (DILA + VN)                      │
│  • lineage_chronology  (Timeline events)                │
│  • namevimap           (SHARED translation)             │
│  • places_pending      (Admin review - separate)        │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (placevn.html)                                │
├─────────────────────────────────────────────────────────┤
│  → Timeline slider with dynasty filter                  │
│  → Map markers (DILA + VN combined)                     │
│  → Cross-search (person ↔ place)                        │
│  → Case study highlights                                │
└─────────────────────────────────────────────────────────┘
```

***

## 🚀 **PHASE 1: DATA STRUCTURE & TEMPLATES** (Week 1)

### **Task 1.1: Create VN JSON Template**

**File:** `/opt/.../daoanh/data/vn_local/TEMPLATE.json`

```json
{
    "VN_PLACE_ID": {
        "authorityID": "CA_VN_XXX",
        "vol": "VN_LOCAL",
        "type": "place",
        "category": "寺院|塔|石窟|山",
        "title": "[Tên chùa chữ Hán]",
        "title_vi": "[Tên chùa tiếng Việt]",
        "dynasty": "[Triều đại Hán tự]",
        "dynasty_vi": "[Triều đại tiếng Việt]",
        "time_from": 0,
        "time_to": 0,
        "contributors": [
            {
                "name": "[Thiền sư chữ Hán]",
                "name_vi": "[Thiền sư tiếng Việt]",
                "id": "VN_PERSON_XXX",
                "role": "founder|abbot|visitor"
            }
        ],
        "location": {
            "gps_lat": 0.0,
            "gps_lon": 0.0,
            "district": "[Quận/Huyện, Tỉnh, Việt Nam]"
        },
        "notes": "[Ghi chú chữ Hán]",
        "notes_vi": "[Ghi chú tiếng Việt]",
        "source": "bia_ky|van_hien|local_research",
        "source_reference": "[Tên tài liệu]"
    }
}
```

**Deliverable:**
- ✅ Template file với comments chi tiết
- ✅ README.md hướng dẫn sử dụng
- ✅ Example files: `example_hue.json`, `example_hanoi.json`

***

### **Task 1.2: Create Dynasty Mapping Table**

**File:** `scripts/dynasty_mapping.py`

```python
DYNASTY_MAP = {
    # Chinese → Vietnamese
    '唐': 'Đường',
    '宋': 'Tống',
    '北宋': 'Bắc Tống',
    '南宋': 'Nam Tống',
    '明': 'Minh',
    '清': 'Thanh',
    '元': 'Nguyên',
    '隋': 'Tùy',
    
    # Vietnamese dynasties
    '前黎': 'Tiền Lê',
    '後黎': 'Hậu Lê',
    '李': 'Lý',
    '陳': 'Trần',
    '阮': 'Nguyễn',
    '西山': 'Tây Sơn',
}

CATEGORY_MAP = {
    '寺院': 'Chùa',
    '塔': 'Tháp',
    '石窟': 'Động đá',
    '山': 'Núi',
}
```

**Deliverable:**
- ✅ Complete mapping dictionary
- ✅ Function `get_vietnamese_dynasty(dynasty_zh)`
- ✅ Unit tests

***

## 🔧 **PHASE 2: DATABASE SCHEMA UPDATES** (Week 1-2)

### **Task 2.1: Extend `dila_places` Table**

```sql
ALTER TABLE dila_places ADD COLUMN data_source TEXT DEFAULT 'DILA';
CREATE INDEX idx_places_source ON dila_places(data_source);

-- Add Vietnamese name field if not exists
ALTER TABLE dila_places ADD COLUMN name_vi TEXT;
```

***

### **Task 2.2: Extend `namevimap` Table**

```sql
-- Add source priority
ALTER TABLE namevimap ADD COLUMN source TEXT DEFAULT 'auto';
ALTER TABLE namevimap ADD COLUMN context TEXT DEFAULT 'general';
ALTER TABLE namevimap ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_namevimap_source ON namevimap(source);
```

***

### **Task 2.3: Create Event Type Table**

```sql
CREATE TABLE IF NOT EXISTS event_types (
    type_code TEXT PRIMARY KEY,
    type_name_zh TEXT,
    type_name_vi TEXT,
    icon TEXT,
    color TEXT
);

INSERT INTO event_types VALUES
    ('temple_founded', '寺院創建', 'Lập chùa', '🏛️', '#FFD700'),
    ('person_birth', '出生', 'Sinh', '👶', '#4CAF50'),
    ('person_death', '圓寂', 'Viên tịch', '🕉️', '#9E9E9E'),
    ('persecution', '法難', 'Pháp nạn', '⚠️', '#F44336'),
    ('revival', '復興', 'Phục hưng', '✨', '#2196F3');
```

**Deliverable:**
- ✅ Migration script `migrations/001_extend_schema.sql`
- ✅ Rollback script (if needed)

***

## 🐍 **PHASE 3: IMPORT SCRIPTS** (Week 2)

### **Task 3.1: JSON Validator**

**File:** `scripts/validate_vn_json.py`

```python
#!/usr/bin/env python3
"""Validate VN local JSON against DILA schema"""

import json
import jsonschema
from pathlib import Path

SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^VN_": {
            "type": "object",
            "required": ["title", "title_vi", "time_from", "location"],
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "title_vi": {"type": "string", "minLength": 1},
                "time_from": {"type": "integer", "minimum": 0, "maximum": 2026},
                "time_to": {"type": "integer", "minimum": 0, "maximum": 2026},
                "location": {
                    "type": "object",
                    "required": ["gps_lat", "gps_lon"],
                    "properties": {
                        "gps_lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "gps_lon": {"type": "number", "minimum": -180, "maximum": 180}
                    }
                }
            }
        }
    }
}

def validate_json(json_path):
    """Validate JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    try:
        jsonschema.validate(data, SCHEMA)
        print(f"✅ {json_path} is valid")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ Validation error in {json_path}:")
        print(f"   {e.message}")
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python validate_vn_json.py <json_file>")
        sys.exit(1)
    
    validate_json(sys.argv [phatphaponline](https://phatphaponline.org/daoanh/places/))
```

**Deliverable:**
- ✅ Validator script with schema
- ✅ Error reporting with line numbers
- ✅ Batch validation mode

***

### **Task 3.2: Main Import Script**

**File:** `scripts/import_vn_local_data.py`

```python
#!/usr/bin/env python3
"""Import VN local temple data"""

import json
import sqlite3
from pathlib import Path
from validate_vn_json import validate_json

DB_PATH = "/opt/.../daoanh/data/lineage.db"

def get_vietnamese_name(name_zh, conn):
    """Get Vietnamese name with fallback"""
    cursor = conn.cursor()
    
    # Priority: manual > VN_LOCAL > admin > DILA > auto
    name_vi = cursor.execute("""
        SELECT namevi FROM namevimap 
        WHERE namezh = ?
        ORDER BY 
            CASE source
                WHEN 'manual' THEN 1
                WHEN 'VN_LOCAL' THEN 2
                WHEN 'admin' THEN 3
                WHEN 'DILA' THEN 4
                ELSE 5
            END
        LIMIT 1
    """, (name_zh,)).fetchone()
    
    if name_vi:
        return name_vi[0]
    
    # Fallback: HanViet conversion
    return han_viet_convert(name_zh, conn)

def han_viet_convert(chinese_text, conn):
    """Convert using hanvietfallback table"""
    cursor = conn.cursor()
    result = []
    
    for char in chinese_text:
        viet = cursor.execute("""
            SELECT viet FROM hanvietfallback WHERE han = ?
        """, (char,)).fetchone()
        
        if viet:
            result.append(viet[0].capitalize())
        else:
            result.append(char)
    
    return ' '.join(result)

def import_vn_local_json(json_path):
    """Import single JSON file"""
    print(f"Importing: {json_path}")
    
    # Validate first
    if not validate_json(json_path):
        print("❌ Validation failed, skipping import")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {
        'places': 0,
        'persons': 0,
        'events': 0,
        'mappings': 0
    }
    
    for place_id, place_data in data.items():
        # 1. Insert place
        location = place_data.get('location', {})
        
        cursor.execute("""
            INSERT OR REPLACE INTO dila_places
            (place_id, name_zh, name_vi, gps_lat, gps_lon, district, 
             category, note_zh, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'VN_LOCAL')
        """, (
            place_id,
            place_data.get('title'),
            place_data.get('title_vi'),
            location.get('gps_lat'),
            location.get('gps_lon'),
            location.get('district'),
            place_data.get('category'),
            place_data.get('notes')
        ))
        stats['places'] += 1
        
        # 2. Store name mapping
        if place_data.get('title') and place_data.get('title_vi'):
            cursor.execute("""
                INSERT OR IGNORE INTO namevimap (namezh, namevi, source, context)
                VALUES (?, ?, 'VN_LOCAL', 'place')
            """, (place_data.get('title'), place_data.get('title_vi')))
            stats['mappings'] += 1
        
        # 3. Import contributors
        for contrib in place_data.get('contributors', []):
            person_id = contrib.get('id')
            if not person_id:
                continue
            
            cursor.execute("""
                INSERT OR IGNORE INTO dila_persons
                (person_id, name_zh, dynasty, data_source)
                VALUES (?, ?, ?, 'VN_LOCAL')
            """, (
                person_id,
                contrib.get('name'),
                place_data.get('dynasty')
            ))
            stats['persons'] += 1
            
            # Store person name mapping
            if contrib.get('name') and contrib.get('name_vi'):
                cursor.execute("""
                    INSERT OR IGNORE INTO namevimap (namezh, namevi, source, context)
                    VALUES (?, ?, 'VN_LOCAL', 'person')
                """, (contrib.get('name'), contrib.get('name_vi')))
                stats['mappings'] += 1
        
        # 4. Create timeline event
        time_from = place_data.get('time_from')
        if time_from:
            cursor.execute("""
                INSERT OR REPLACE INTO lineage_chronology
                (id, title_zh, title_vi, dynasty_zh, dynasty_vi,
                 century_start, century_end, time_from, time_to,
                 place_id, event_type, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'temple_founded', 'VN_LOCAL')
            """, (
                f"{place_id}_FOUNDED",
                place_data.get('title'),
                place_data.get('title_vi'),
                place_data.get('dynasty'),
                place_data.get('dynasty_vi'),
                time_from // 100,
                (place_data.get('time_to') or time_from) // 100,
                time_from,
                place_data.get('time_to') or time_from,
                place_id
            ))
            stats['events'] += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Import complete: {stats}")

def main():
    """Import all JSON files in vn_local/"""
    json_dir = Path("/opt/.../daoanh/data/vn_local")
    
    for json_file in json_dir.glob('*.json'):
        if json_file.name == 'TEMPLATE.json':
            continue
        
        try:
            import_vn_local_json(json_file)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
```

**Deliverable:**
- ✅ Import script with error handling
- ✅ Progress reporting
- ✅ Dry-run mode (`--dry-run` flag)
- ✅ Logging to file

***

## 🌐 **PHASE 4: API ENDPOINTS** (Week 3)

### **Task 4.1: VN Data API**

**File:** `app.py` (add these routes)

```python
@app.route('/daoanh/api/vn/places', methods=['GET'])
def api_vn_places():
    """Get VN local places only"""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    places = conn.execute("""
        SELECT * FROM dila_places
        WHERE data_source = 'VN_LOCAL'
        ORDER BY name_vi
    """).fetchall()
    
    return jsonify({
        'status': 'success',
        'count': len(places),
        'places': [dict(p) for p in places]
    })

@app.route('/daoanh/api/vn/stats', methods=['GET'])
def api_vn_stats():
    """Get VN data statistics"""
    conn = get_db()
    
    stats = {
        'total_places': conn.execute("""
            SELECT COUNT(*) FROM dila_places WHERE data_source = 'VN_LOCAL'
        """).fetchone()[0],
        
        'by_province': dict(conn.execute("""
            SELECT 
                SUBSTR(district, INSTR(district, ',') + 2) as province,
                COUNT(*) as count
            FROM dila_places
            WHERE data_source = 'VN_LOCAL'
            GROUP BY province
        """).fetchall()),
        
        'by_century': dict(conn.execute("""
            SELECT century_start, COUNT(*) as count
            FROM lineage_chronology
            WHERE data_source = 'VN_LOCAL'
            GROUP BY century_start
            ORDER BY century_start
        """).fetchall())
    }
    
    return jsonify(stats)
```

**Deliverable:**
- ✅ REST API endpoints
- ✅ API documentation (Swagger/OpenAPI)
- ✅ Test suite (pytest)

***

## 🎨 **PHASE 5: FRONTEND INTEGRATION** (Week 3-4)

### **Task 5.1: Data Source Filter**

**File:** `placevn.html` (add to sidebar)

```html
<div id="dataSourceFilter">
    <h3>📊 Nguồn Dữ Liệu</h3>
    <label>
        <input type="checkbox" id="filter-dila" checked>
        DILA (Quốc tế)
    </label>
    <label>
        <input type="checkbox" id="filter-vn" checked>
        VN Local (Địa phương)
    </label>
</div>
```

```javascript
// Apply filter
function applyDataSourceFilter() {
    const showDila = document.getElementById('filter-dila').checked;
    const showVN = document.getElementById('filter-vn').checked;
    
    markers.forEach(marker => {
        const source = marker.options.data_source;
        const shouldShow = (source === 'DILA' && showDila) || 
                          (source === 'VN_LOCAL' && showVN);
        
        if (shouldShow) {
            marker.addTo(map);
        } else {
            marker.remove();
        }
    });
}
```

***

### **Task 5.2: VN Data Highlight**

```javascript
// Different marker style for VN data
function createMarker(place) {
    const isVN = place.data_source === 'VN_LOCAL';
    
    return L.circleMarker([place.gps_lat, place.gps_lon], {
        radius: isVN ? 10 : 8,
        color: isVN ? '#FF6B6B' : '#4ECDC4',
        fillOpacity: 0.8,
        className: isVN ? 'vn-marker' : 'dila-marker'
    });
}
```

**CSS:**
```css
.vn-marker {
    border: 2px solid #FFD700;
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
}
```

***

## 📝 **PHASE 6: DOCUMENTATION & TRAINING** (Week 4)

### **Task 6.1: User Guide for Team VN**

**File:** `docs/VN_DATA_INPUT_GUIDE.md`

```markdown
# Hướng Dẫn Nhập Liệu Chùa Việt Nam

## Bước 1: Chuẩn Bị Dữ Liệu
- Thu thập thông tin từ bia ký, văn hiến
- Lập bảng Excel theo mẫu

## Bước 2: Convert sang JSON
- Copy template từ `TEMPLATE.json`
- Điền thông tin theo từng field
- Lưu ý: ID phải bắt đầu bằng `VN_`

## Bước 3: Validate
```bash
python3 scripts/validate_vn_json.py vn_local/my_data.json
```

## Bước 4: Import
```bash
python3 scripts/import_vn_local_data.py
```

## Bước 5: Kiểm Tra
- Mở https://phatphaponline.org/daoanh/places/
- Bật filter "VN Local"
- Kiểm tra markers và thông tin
```

**Deliverable:**
- ✅ Vietnamese documentation
- ✅ Video tutorial (screen recording)
- ✅ FAQ section

***

## ✅ **ACCEPTANCE CRITERIA**

### **Functional Requirements:**
- [ ] Team VN có thể nhập data qua JSON
- [ ] Validation tự động trước khi import
- [ ] Phiên âm Hán-Việt nhất quán với admin panel
- [ ] Hiển thị đúng trên timeline map
- [ ] Filter riêng cho VN data vs DILA data
- [ ] Cross-search hoạt động (person ↔ place)

### **Non-Functional Requirements:**
- [ ] Import < 5s cho file 100 records
- [ ] API response < 500ms
- [ ] Mobile responsive
- [ ] Error handling graceful
- [ ] Logging đầy đủ

***

## 📅 **TIMELINE SUMMARY**

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Data Structure | Template, Schema, Dynasty mapping |
| 1-2 | Database | Migration scripts, Extended tables |
| 2 | Import Scripts | Validator, Importer, Tests |
| 3 | API | Endpoints, Documentation, Tests |
| 3-4 | Frontend | Filters, Markers, UI updates |
| 4 | Documentation | User guide, Training materials |

**Total Duration:** 4 weeks

***

## 🔗 **REFERENCES**

- DILA Authority Database: https://github.com/DILA-edu/Authority-Databases
- Current site: https://phatphaponline.org/daoanh/places/ [phatphaponline](https://phatphaponline.org/daoanh/places/)
- Space context: Dự Án Tích Hợp DiLa

***

**OpenCode: Please implement this roadmap following the phases sequentially. Start with Phase 1 and provide updates after each task completion.**


### Khoá 10 - Tích hợp chức năng của https://suttacentral.net/map?lang=en vào hệ thống

qtt### Khoá 11 - panel chat (widget)
### Tóm tắt nhanh
**Có** — bạn hoàn toàn có thể gọi một **panel chat (widget)** từ website của mình và dùng **chatbot riêng** (LLM) để trả lời, dịch, hoặc so sánh văn bản kinh điển. Cách triển khai phổ biến: **widget nhúng trên site**, **Chrome extension sidebar**, hoặc **PWA/cửa sổ phụ**. Mỗi phương án khác nhau về phạm vi truy cập, quyền, và độ phức tạp.

---

### So sánh ngắn (ưu/nhược theo mục tiêu)
| **Tiêu chí** | **Widget nhúng (site)** | **Chrome Extension (sidebar)** | **PWA / cửa sổ phụ** |
|---|---:|---:|---:|
| **Phạm vi hiển thị** | Chỉ trên site của bạn | Toàn trình duyệt, mọi site | Ứng dụng độc lập |
| **Triển khai nhanh** | **Nhanh** | Trung bình → phức tạp (store review) | Trung bình |
| **Quyền truy cập nội dung trang** | Chỉ nội dung site | Có thể lấy nội dung mọi trang (cần permission) | Không tự động |
| **Quyền riêng tư / kiểm soát LLM** | Dễ kiểm soát (backend bạn) | Cần xử lý cẩn trọng (permissions) | Dễ kiểm soát |
| **UX giống Copilot** | Rất tốt trên site | Rất giống toàn trình duyệt | Tùy chỉnh tốt |

---

### Kiến trúc đề xuất (widget trên site — phương án khuyến nghị)
1. **Frontend (widget)**  
   - Component React/Vue/vanilla JS hiển thị panel (floating hoặc docked).  
   - Giao diện: chọn bản gốc, chọn bản dịch, nút “dịch bằng AI”, lịch sử, attribution.  
2. **Backend service**  
   - Endpoint kiểm tra **license** của đoạn văn (`/api/check-license?segment_id=...`).  
   - Endpoint gọi LLM an toàn (`/api/translate`) với cấu hình **no‑store/no‑training** nếu nhà cung cấp hỗ trợ.  
   - Cache kết quả dịch trong DB (SQLite) kèm `model_policy` và `license`.  
3. **Dữ liệu**  
   - Sync từ **sc-data / Bilara** (clone repo) thay vì scrape HTML. Lưu `segment_id`, `text`, `lang`, `alignment_group`, `license`.  
4. **LLM**  
   - Dùng provider hỗ trợ **data privacy options** (no retention) hoặc chạy on‑premise.  
   - Gửi **chỉ đoạn cần thiết**, loại bỏ metadata nhạy cảm.  
5. **UI/UX & Consent**  
   - Trước khi gửi nội dung ra LLM, hiển thị modal thông báo và yêu cầu đồng ý.  
   - Hiển thị **attribution** (ví dụ: “Nguồn: SuttaCentral (CC0)” hoặc tên nguồn + license).  

---

### Luồng xử lý khi user nhấn “dịch”
1. Frontend gửi `segment_id` + `target_lang` → Backend.  
2. Backend kiểm tra `license` của `segment_id`.  
3. Nếu **được phép**, backend gọi LLM với cấu hình không lưu; nhận bản dịch.  
4. Lưu bản dịch vào `translations_cache` (kèm `model_policy`, `created_at`).  
5. Trả kết quả cho frontend; frontend hiển thị kèm attribution và nút “xóa / báo cáo”.

---

### Checklist pháp lý & bảo mật (bắt buộc)
- **Kiểm tra license** cho từng văn bản trước khi phục vụ hoặc gửi ra LLM.  
- **Tôn trọng yêu cầu nguồn** (ví dụ SuttaCentral khuyến nghị không dùng để huấn luyện).  
- **Thông báo & xin đồng ý người dùng** khi gửi nội dung ra dịch vụ bên thứ ba.  
- **Cấu hình LLM**: bật no‑store/no‑training nếu có; hoặc dùng LLM on‑premise.  
- **Minimize data**: gửi đoạn ngắn nhất cần thiết; loại bỏ metadata nhạy cảm.  
- **Ghi attribution** rõ ràng khi hiển thị bản gốc và bản dịch.  

---

### Bước tiếp theo mình có thể làm cho bạn
- **Viết mẫu code**: widget frontend + backend (Node/Python) kèm kiểm tra license và gọi LLM (mẫu endpoint + schema SQLite).  
- **Viết script**: parser Bilara JSON → SQLite (schema kèm `segment_id`, `license`, `alignment_group`).  
- **Soạn text consent & attribution** sẵn để chèn vào UI.  

Bạn muốn mình bắt đầu với **mẫu code import Bilara → SQLite** hay **mẫu widget + backend** để gọi LLM an toàn trên site của bạn?
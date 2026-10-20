# T224 — Source Reuse Audit (DILA, TTL/ZQLOCAL, Marcus, Wikidata, CBETA)

Ngày: 2026-10-13 · Loại: Audit/phân tích (không sửa schema, không sửa code, không commit).
DB: `daoanh/data/lineage.db` (SQLite, đọc trực tiếp qua `sqlite3` module Python — CLI `sqlite3` không có trong môi trường).

---

## 0. Cảnh báo quan trọng — sai lệch source_id so với đề bài

Đề bài giả định mapping: `1=DILA, 2=CBETA, 3=MARCUS, 4=WIKIDATA, 5=ZQLOCAL`.

**Mapping thực tế trong `data_sources`:**

| source_id | source_code | Ghi chú |
|---|---|---|
| 1 | DILA | khớp đề bài |
| 2 | BDRC | **không có trong đề bài** — active=0, gần như không có dữ liệu |
| 3 | CBETA | đề bài ghi là MARCUS — **sai** |
| 4 | MARCUS | đề bài ghi là WIKIDATA — **sai** |
| 5 | ZQLOCAL | khớp đề bài |
| 6 | Wikidata | đề bài không liệt kê (đề bài coi Wikidata = id 4) |

Toàn bộ phần dưới dùng **source_id thực tế trong DB** (DILA=1, CBETA=3, MARCUS=4, ZQLOCAL=5, Wikidata=6). Nếu dùng mapping của đề bài sẽ đọc sai hoàn toàn kết quả (vd. sẽ tưởng Marcus x ZQLOCAL overlap trong khi thực ra đó là CBETA x MARCUS).

## 0.1. Cảnh báo thứ hai — `entity_claims.entity_id` không phải join key đồng nhất

`entity_claims.entity_id` là số nguyên tự sinh, nhưng **không cùng một không gian định danh** cho mọi nguồn:

- DILA/CBETA/ZQLOCAL/Wikidata trong `entity_claims`: `entity_id` nằm trong range 100001–218328, trỏ tới **PLACE** (claim_type COORDINATE/ADMIN_UNIT), join qua bảng crosswalk `entity_source_ids` tới `entity.entity_id` dạng `PL000000...`.
- MARCUS trong `entity_claims`: `entity_id` (range 218330–262084) là ID tự sinh **của chính claim Marcus**, không trỏ tới place. Danh tính thật nằm trong cột `subject`/`object_text` dưới dạng **DILA person ID** (`A000005`, …).

→ Nếu đếm overlap bằng `GROUP BY entity_id` trên `entity_claims` một cách naive (đúng như đề bài yêu cầu ở mục 1), kết quả sẽ cho **MARCUS overlap = 0 với mọi nguồn khác** — kết luận sai, vì Marcus không join qua `entity_id` dạng này. Report dưới đây trình bày cả hai phép đo (naive theo đề bài, và theo crosswalk thật `entity_source_ids`/`entity.dila_id`) để không đánh giá sai.

---

## 1. Entity count theo source_id (`entity_claims`, GROUP BY naive — đúng yêu cầu đề bài)

| source_id | source | DISTINCT entity_id | Tổng claims |
|---|---|---|---|
| 1 | DILA | 59,168 | 293,177 |
| 3 | CBETA | 4,409 | 13,933 |
| 4 | MARCUS | 11,297 | 22,332 |
| 5 | ZQLOCAL | 118,295 | 118,295 |
| 6 | Wikidata | 148 | 148 |

(source_id=2 BDRC: 0 claim — nguồn inactive.)

Tổng distinct entity_id trong `entity_claims`: **129,609** (chủ yếu PLACE; Marcus claim-id nằm lẫn trong range riêng, không phải entity thật).

### Overlap naive theo `entity_id` (đề bài yêu cầu mục 1)

| Cặp nguồn | entity_id overlap (naive) |
|---|---|
| DILA × CBETA | 4,409 |
| DILA × MARCUS | **0** (xem cảnh báo 0.1 — không phải MARCUS thực sự không liên kết gì) |
| DILA × ZQLOCAL | 59,151 |
| DILA × Wikidata | 148 |
| CBETA × MARCUS | 0 |
| CBETA × ZQLOCAL | 4,409 |
| CBETA × Wikidata | 47 |
| MARCUS × ZQLOCAL | 0 |
| MARCUS × Wikidata | 0 |
| ZQLOCAL × Wikidata | 148 |

Tổng entity_id có ≥2 source_id khác nhau (naive): **59,151**.

---

## 2. Overlap matrix thật — qua `entity_source_ids` (crosswalk canonical, đúng nguyên tắc "không merge bằng tên")

Bảng `entity_source_ids` là bảng crosswalk chính thức (entity_id canonical ↔ source + source_entity_id). Đây là phép đo đáng tin hơn mục 1 vì dùng canonical entity_id thống nhất (`entity.entity_id`).

| source | DISTINCT entity_id (canonical) |
|---|---|
| DILA | 167,006 |
| CBETA | 4,409 |
| MARCUS | 11,297 |
| ZQLOCAL | 2 |
| BDRC | 1 |

**Phát hiện cấu trúc quan trọng:** `ZQLOCAL` trong `entity_source_ids` chỉ có **2 dòng** — tức là cơ chế crosswalk chính thức hầu như không dùng cho ZQ. Dữ liệu tiếng Việt của ZQ thực tế được nhúng trực tiếp:
- `entity.alias_vi` cho PLACE: 118,295 / 118,328 (99.97%) có alias_vi.
- `entity.alias_vi` cho PERSON: **0 / 48,673 (0%)** — bảng `entity` thống nhất **không có tên Việt cho bất kỳ PERSON nào**.
- Tên Việt cho PERSON chỉ tồn tại ở bảng riêng `vn_person_authority` (1,511 dòng name_vi), hoàn toàn tách biệt khỏi `entity`/`entity_claims`.

### Overlap matrix (canonical, qua `entity_source_ids`)

| | DILA | CBETA | MARCUS | ZQLOCAL | BDRC |
|---|---|---|---|---|---|
| **DILA** | — | 4,409 | 11,297 | 2 | 0 |
| **CBETA** | | — | 0 | 0 | 0 |
| **MARCUS** | | | — | 0 | 0 |
| **ZQLOCAL** | | | | — | 0 |
| **BDRC** | | | | | — |

Nhận xét: CBETA trong `entity_source_ids` **chỉ gồm PLACE ID** (`PL00000000...`), không có person ID nào — nghĩa là CBETA evidence cho person hiện không đi qua crosswalk, dù `entity_claims` source=3 có claim_type TEXT_EVIDENCE (13,933 dòng) — các claim này gắn với entity_id dạng PLACE, không phải person. CBETA × MARCUS person-level overlap thực tế = 0 trong lớp crosswalk (chưa được liên kết, không phải "không tồn tại").

---

## 3. Verify `vn_person_authority` (nguồn Việt tông TTL/ZQ cho person)

Schema thật (`PRAGMA table_info`): có `dila_id` (TEXT) — **không có cột `marcus_id`**. Đề bài yêu cầu đếm `marcus_id` not null — **cột này không tồn tại trong `vn_person_authority`**, báo rõ theo đúng yêu cầu "nếu thiếu cột báo rõ, không đoán schema".

| Chỉ số | Giá trị |
|---|---|
| Tổng số dòng `vn_person_authority` | 1,511 |
| Dòng có `dila_id` hợp lệ format `A######` | 1,307 |
| Dòng có `dila_id` NOT NULL nhưng rỗng `''` | 204 |
| Dòng có `marcus_id` not null | **N/A — cột không tồn tại trong bảng này** (marcus_id chỉ có ở `entity.marcus_id`, bảng unified, không có ở `vn_person_authority`) |
| `dila_id` khớp đúng `entity.dila_id` (entity_type='PERSON') | 1,307 / 1,307 (100% — mọi dila_id hợp lệ đều resolve đúng) |
| PERSON entity distinct có ≥1 dòng `vn_person_authority` | 1,268 |

Chênh lệch 1,307 vs 1,268: do **36 dila_id bị trùng** trong `vn_person_authority` (nhiều dòng TTL khác nhau map về cùng 1 DILA person ID) — xem mục 5 (Conflict).

### Coverage DILA person → vn_person_authority

- Tổng PERSON entity trong `entity` (= tổng DILA person authority đã import): **48,673**.
- Đã có trong `vn_person_authority`: **1,268** (qua dila_id match, không suy diễn tên).
- **Coverage = 1,268 / 48,673 = 2.6%**.
- Missing (DILA person chưa có Vietnamese curation): **47,405 (97.4%)**.

### Coverage Marcus-linked person → vn_person_authority

- PERSON entity có `marcus_id` (entity.marcus_id not null): 18,121.
- Trong số đó đã có `vn_person_authority`: 1,090.
- Missing: **17,031 (94.0%)** — phần lớn person có dữ liệu lineage Marcus vẫn chưa có tên Việt curated.

### Coverage PLACE (so sánh đối chứng)

- PLACE entity: 118,328. Có alias_vi (ZQ): 118,295 → missing chỉ 33 (0.03%). Place coverage gần như hoàn chỉnh; person coverage rất thấp — lệch pha nghiêm trọng giữa 2 loại entity.

---

## 4. Tổng hợp Missing

| Tập hợp | Tổng | Có trong lớp hợp nhất | Missing | % Missing |
|---|---|---|---|---|
| DILA PERSON | 48,673 | 1,268 (vn_person_authority) | 47,405 | 97.4% |
| DILA PERSON có Marcus lineage | 18,121 | 1,090 | 17,031 | 94.0% |
| DILA PLACE | 118,328 | 118,295 (alias_vi) | 33 | 0.03% |
| CBETA person-level crosswalk | 0 (chưa làm) | 0 | — | N/A (chưa triển khai) |

**[y] Missing = 47,405** (DILA person chưa vào vn_person_authority — số chính dùng cho khuyến nghị).

---

## 5. Conflict (cùng canonical ID, dữ liệu khác nhau)

Phát hiện bằng group theo `dila_id` (canonical ID, không dùng tên để match — đúng nguyên tắc rule):

- **36 nhóm `dila_id` trùng** trong `vn_person_authority` (cùng 1 DILA ID nhưng ≥2 dòng TTL khác nhau trỏ vào).
- Trong 36 nhóm đó, **34 nhóm có `name_vi` khác nhau thật** (2 nhóm còn lại trùng cả tên, chỉ là duplicate record vô hại).
- Tổng dòng dư do trùng: 39 dòng (1,511 dòng thực chất chỉ ánh xạ tới 1,472 canonical ID riêng biệt).

Ví dụ cụ thể (không suy diễn, lấy trực tiếp từ DB):

```
dila_id = A000108
  ttl_filename=bao_ninh_nhan_dung       → name_vi = "Nhơn Dũng"
  ttl_filename=nguyet_chuong_tri_uyen   → name_vi = "Nguyệt Chưởng Trí Uyên"
```

Đây là **conflict thật theo canonical ID**: 2 file TTL khác nhau đã gán cùng 1 DILA person ID (`A000108`) cho 2 tên Việt khác nhau — hoặc là 2 pháp danh khác nhau của cùng 1 người (hợp lệ nếu có alias), hoặc là lỗi map TTL (gán nhầm dila_id). Audit này **không phân giải** được cái nào đúng — cần admin/editor xác minh thủ công, không nên tự động chọn 1 trong 2 bằng heuristic.

**[z] Conflict = 36 nhóm dila_id trùng (34 có tên khác nhau thật)**.

Không phát hiện được conflict birth_year/death_year chéo nguồn vì không có bảng raw DILA birth/death riêng để đối chiếu trong phạm vi audit này (ngoài phạm vi — cần raw DILA TTL để so, không nằm trong DB SQLite hiện tại).

---

## 6. Tổng kết số liệu

- **[x] Overlap** (canonical, qua entity_source_ids): DILA×CBETA = 4,409 (place); DILA×MARCUS = 11,297 (person); DILA×ZQLOCAL (crosswalk chính thức) = 2; DILA×Wikidata (qua entity_claims numeric, place) = 148.
- **[y] Missing**: 47,405 DILA person chưa có trong vn_person_authority (97.4%); 33 DILA place thiếu alias_vi (0.03%).
- **[z] Conflict**: 36 nhóm dila_id trùng trong vn_person_authority, 34 nhóm có name_vi khác nhau thật.

---

## 7. Khuyến nghị

**Keep separate (giữ nguyên, chỉ link qua crosswalk/owl:sameAs) — không consolidate/merge ồ ạt.**

Lý do dựa trên số liệu quan sát được, không suy đoán:

1. **Overlap thực ở mức canonical rất thấp đối với PERSON** ngoài DILA↔MARCUS (11,297/48,673 = 23%). CBETA chưa hề có crosswalk person-level (0 record). Merge ép ở layer person hiện tại sẽ merge trên dữ liệu rất mỏng, rủi ro cao.
2. **Tỷ lệ conflict trên overlap-coverage là đáng kể** (36/1,511 ≈ 2.4% số dòng vn_person_authority đã bị trùng dila_id với tên khác nhau) — cho thấy quy trình map TTL→dila_id hiện tại **chưa đủ sạch** để tự động consolidate; cần dọn conflict hiện có trước khi mở rộng gộp thêm nguồn.
3. **PLACE đã consolidate tốt** (99.97% coverage, overlap rõ ràng qua crosswalk) — đây là mô hình nên giữ làm chuẩn, KHÔNG cần đổi.
4. **PERSON đang ở 2 hệ thống song song, chưa link**: `entity` (unified, alias_vi=0% cho person) và `vn_person_authority` (curated riêng, 1,511 dòng, chỉ 2.6% coverage DILA person). Khuyến nghị: không gộp 2 bảng này thành 1, mà **thêm bước crosswalk/validate** (giống cách `entity_source_ids` đang làm cho PLACE) để `vn_person_authority.dila_id` được validate & dedup (giải quyết 36 conflict) trước khi tính đến mở rộng coverage hoặc hợp nhất sâu hơn.
5. Marcus overlap với CBETA = 0 ở mọi phép đo — hai nguồn này đang hoàn toàn độc lập đối với person; không có bằng chứng để merge, chỉ nên để Marcus tiếp tục là "lineage supplement" đứng cạnh DILA như rule `data-integrity.md` đã quy định (hierarchy nguồn, không ghi đè).

---

## 8. Script dùng để audit

Các câu query Python/sqlite3 dùng trong audit này được chạy trực tiếp qua Bash tool (không lưu thành file riêng do chỉ là query một lần, read-only, không có logic migration cần tái sử dụng). Không có thay đổi DB, không có file script tạm cần giữ lại.

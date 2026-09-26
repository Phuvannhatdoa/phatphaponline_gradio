# SCHEMA_DESIGN — Hiến pháp dữ liệu ZenQ (Evidence-first)

**File trung tâm:** `data/lineage.db` · **Tạo:** 2026-09-08 (T108)
**Khởi nguồn:** Đặc tả "TASK T01 — CẤU TRÚC ASSERTION" do Lee Tổng phê chuẩn; trong hệ thống đánh số **T108** (T01–T07 đã tồn tại với nghĩa khác).
**Bản chất:** Định nghĩa đơn vị dữ liệu nhỏ nhất, thuần khiết nhất mà hệ thống quản lý — **Assertion** — và các quy tắc bất biến (Data Law) mà mọi code/agent phải tuân theo.
**Phạm vi:** Lớp POLICY/CONTRACT. Schema chi tiết từng bảng: `docs/db_schema.md` · Nguồn & legal: `docs/SOURCE_REGISTRY.md`, `docs/SOURCE_INTEGRATION_POLICY.md`, `docs/trusted-sources.md` · Từ điển dữ liệu & rollback SQL: `docs/DATA_DICTIONARY.md` · Khung học thuật: `docs/ACADEMIC_16TABS_IMPLEMENTATION_PLAN.md`.

---

## M1. Thuật ngữ cốt lõi (Keyword Contract — cho mọi agent, kể cả ClaudeCode)

> Những định nghĩa này là **luật**, không phải gợi ý. Bất kỳ agent nào viết code/docs cho ZenQ phải hiểu đúng 4 thuật ngữ dưới đây.

1. **Assertion (Lời khẳng định)** — Đơn vị dữ liệu nhỏ nhất trong ZenQ. **Không bao giờ là khẳng định biệt lập.** Một Assertion luôn bao gồm 3 khối:
   - **Nội dung thông tin** (CoreClaim): predicate + object.
   - **Chứng cứ đi kèm** (Provenance): nguồn, reference, URL, thời điểm thu thập.
   - **Trạng thái thẩm định** (Review State): mức tin cậy, mức kiểm chứng, người duyệt, thời gian duyệt.
   - → Cột ánh xạ thật: `entity_claims` (xem M2.2).

2. **Provenance (Chứng tích)** — "Hồ sơ phả hệ" của dữ liệu. **Mọi dữ liệu không nguồn gốc (Source-less) đều là RÁC hoặc "chưa xác định"** — phải gắn trạng thái, KHÔNG được hiển thị như đã xác định.

3. **Confidence Score (Điểm tin cậy)** — Thước đo định lượng 0.0→1.0. **Không có dữ liệu nào tuyệt đối 100% đúng.** Nguồn CBETA/DILA có điểm cao hơn nguồn Wikipedia. → Quy ước = `source_authority.precedence_order` (M4).

4. **Scoped Corpus (Phạm vi ngữ liệu)** — Rào cản pháp lý/nghiệp vụ. **"Không tìm thấy" trong phạm vi ≠ "Không tồn tại".** Nếu truy vấn ngoài phạm vi, phải báo rõ ràng (M6).

---

## M2. Kiến trúc (ERD) — thực thể & mối quan hệ qua Assertion

### M2.0 Kiến trúc tổng (ERD dạng văn bản)

```
                        ┌─────────────────────────────┐
                        │    ENTITY HUB (Identity)    │
                        │  entity_hub  (167,006)      │
                        │  _resolve_entity_id: PL…    │
                        └───────┬─────────────┬───────┘
                  belongs_to     │             │  belongs_to
        ┌───────────▼─────────┐  │   ┌────────▼───────────┐
        │ PERSON   (people)   │  │   │ PLACE  (places/    │
        │ text_canon…         │  │   │         places_dila│
        └───────────┬─────────┘  │   └────────┬───────────┘
                    │            │            │
                    ▼            ▼            ▼
        ┌───────────────────────────────────────────────┐
        │          ASSERTION STORE                      │
        │  entity_claims  (447,885)                     │
        │  Nội dung + Provenance + Review state         │
        └───────┬───────────────────────────┬───────────┘
                │ claim_type                │ TEXT_EVIDENCE / NETWORK_EVIDENCE
                ▼                           ▼
   ┌────────────────────────┐   ┌───────────────────────────┐
   │  PROVENANCE REGISTRY   │   │  EVIDENCE LAYER           │
   │  data_sources (13)     │   │  text_passages (9,316)    │
   │  source_authority (13) │   │  doctrine_concept (12)    │
   │  dataset_sources(legacy)│  │  pali_cbeta_map (6)       │
   └────────────────────────┘   └───────────────────────────┘
   ┌───────────────────────────────┐
   │  CONFLICT POOL                │
   │  lineage_conflicts_v2 (40,327)│  ← chỉ trình Admin, không tự quyết
   └───────────────────────────────┘
```

Đặc tả T01 yêu cầu ERD có **Person, Place, Text, Concept** — trong hệ thống, cả 4 đều **đứng sau Entity Hub** (Identity) và nối nhau **chỉ qua Assertion** (`entity_claims`). KHÔNG có đường nối tắt trực tiếp bỏ qua Assertion ở tầng hiển thị cuối cùng.

### M2.1 Identity — `entity_hub` (167,006)

| Cột | Kiểu | Vai trò |
|---|---|---|
| `entity_id` (hệ quy chiếu) | String | ID chuẩn, định dạng `PL…` (place) / `A…` (person) |
| alias / id_ngắn–dài | String | `_resolve_entity_id` ánh xạ `PL000000...` ↔ `PL…`; id ngắn ↔ id dài (DILA) |
| entity_type | Enum | PERSON / PLACE / TEXT / CONCEPT / EVENT / TIME |

**Luật:** Mọi resolution đi qua `_resolve_entity_id` (app.py) — KHÔNG hardcode id short/long trong query. Tiền lệ Bugfix T101 (`58473 undefined`: entity_id=NULL).

### M2.2 Assertion Store — `entity_claims` (447,885) ⭐

**Khối Nội dung:**

| Cột | Kiểu | Mô tả |
|---|---|---|
| `claim_id` | Integer (PK cục bộ) | autoincrement cục bộ — KHÔNG phải identity toàn cục (xem M5) |
| `entity_id` | String | chủ thể của assertion |
| `claim_type` | Enum (6) | NAME · COORDINATE · ADMIN_UNIT · TEXT_EVIDENCE · EXTERNAL_ID · NETWORK_EVIDENCE |
| `predicate` | String | vị từ (vd `has_name_han`, `located_in`) |
| `object_text` | String | giá trị |

**Khối Provenance (Chứng cứ):**

| Cột | Kiểu | Mô tả |
|---|---|---|
| `source_id` | String | **BẮT BUỘC — 0 row NULL (100% có nguồn)** — verified 2026-09-08 |
| `source_reference` | String | reference cụ thể trong nguồn |
| `source_url` / `retrieved_at` | String / Timestamp | URL & thời điểm thu thập (additive, có sẵn) |
| `authority_role` | String | thông tin bổ sung vai trò nguồn |

**Khối Review (Thẩm định):**

| Cột | Kiểu | Mô tả |
|---|---|---|
| `confidence` | Real 0.0–1.0 | **BẮT BUỘC — 0 row NULL**; hiện tại range **0.7–1.0** |
| `verification_status` | Enum | hiện tại duy nhất `'unverified'` — 447,885 claims chưa thẩm định (alert #4 / T109) |
| `assertion_level` | Enum (T100) | `cu_nhan` / `cao_hoc` / `tien_si` — **hiện NULL 100%** (0/447,885 đã gán) |
| `reviewed_by` / `reviewed_at` | String / Timestamp | người duyệt & thời gian — **hiện NULL 100%** |

> ⚠️ **Độ lệch T01 → hiện trạng (phải xử lý):** cấu trúc đã đủ 3 khối nhưng khối Review **0% được điền**. Xem M7.

### M2.3 Provenance Registry — `data_sources` (13) + `source_authority` (13)

| Cột | Kiểu | Vai trò |
|---|---|---|
| `source_code`, `source_id` | String | định danh nguồn |
| `authority_score` | Integer (100→25) | thứ bậc:**DILA 100 · CBETA 80 · … · Wikidata 25** |
| `precedence_order` | Integer | **quy ước trọng tài mâu thuẫn** (cao hơn = ưu tiên hơn) |
| `implemented` | Boolean | 5 active / 8 pending |

**Thực trạng verified (2026-09-08):** `data_sources`=13 · `dataset_sources`=10 · **5 nguồn active** nuôi claims: **DILA 293,177 · ZQLOCAL 118,295 · MARCUS 22,332 · CBETA 13,933 · Wikidata 148** (= 447,885). **8 nguồn `implemented=0`**: SAT, CHGIS, BDRC, FoJin, Kanripo, TGAZ, SuttaCentral, 84000 (thuộc T70/T34; xếp lịch ở T112).

### M2.4 Conflict Pool — `lineage_conflicts_v2` (40,327)

Cột `resolved` đã có nhưng **chưa có workflow trình Admin** → T109. **Luật:** KHÔNG code nào được tự quyết conflict; chỉ trình, Admin quyết, kết quả ghi `resolved` + `reviewed_by`/`reviewed_at` + áp lên `entity_claims`.

### M2.5 Evidence Layer — `text_passages` (9,316) / `doctrine_concept` (12) / `pali_cbeta_map` (6)

- `text_passages` (**9,316** — verified 2026-09-08; docs trước ghi "~115k" là SAI → đã sửa, id `daoanh:cbeta:…:<loc>:p<seq>`) = **content-hash id** (tiền lệ M5).
- ⚠️ **`cbeta_text_catalog` KHÔNG TỒN TẠI** trong lineage.db (bảng ma trong ERD cũ — Lean Data audit) — đã gỡ khỏi ERD. Catalog CBETA thật tên khác (`cbeta_catalog_vn`, `cbeta_ref_passages`, `cbeta_place_mentions`) nhưng **không cần vào v2 Schema** (giữ Lean).
- `doctrine_concept` (2026-09-08, T100 B4): 12 khái niệm, UNIQUE `pth_uri`.
- `pali_cbeta_map` (2026-09-08, T100 B4): 6 record ánh xạ Pali↔CBETA.
- `dataset_sources` (10 row, 8 cột) = **legacy** — v2 Schema chỉ dùng `data_sources` + `source_authority` (Lean Data demote).
- Các bảng này là **điểm cuối evidence** — claim TEXT_EVIDENCE/NETWORK_EVIDENCE trỏ về đây để mở rộng.

---

## M3. Quy định kiểu dữ liệu (String / Enum / Real / Timestamp)

| Nhóm | Cột tiêu biểu | Kiểu | Ghi chú |
|---|---|---|---|
| Định danh | `audit_id` (M5) | String (SHA-256) | identity toàn cục |
| Nội dung | `predicate`, `object_text`, `title_vi`, `definition` | String | UTF-8, không giới hạn hán tự |
| Danh mục cố định (Enum) | `claim_type` (6) · `verification_status` · `assertion_level` (cu_nhan/cao_hoc/tien_si) · `source_type` · `precedence_order` · `entity_type` | Enum | **Giá trị mới PHẢI qua migration additive + docs**, không tự thêm lỏng lẻo |
| Số | `confidence` 0–1 · `authority_score` 100–25 · `start_year`/`end_year` · `geo_lat`/`geo_long` | Real/Integer | `confidence` KHÔNG được NULL (M4) |
| Thời gian | `created_at` · `updated_at` · `retrieved_at` · `reviewed_at` | Timestamp | ISO-8601 UTC |
| Trạng thái pháp lý | `legal_status`, `data_license_status`, `freeze_reason` | Enum | đầy đủ T78 |

---

## M4. Confidence Policy & Precedence

1. **Mọi claim mới phải có `confidence`** (không NULL) — hiện trạng 0 NULL, range 0.7–1.0.
2. **Mâu thuẫn giữa các nguồn** → trọng tài theo `source_authority.precedence_order` (DILA > CBETA > … > Wikidata); không dùng "đếm phiếu".
3. Nếu nguồn chưa có `authority_score` → mặc định thấp nhất, không đoán.
4. `confidence` của claim KHÔNG tự động bằng `authority_score/100` — nó là trạng thái thẩm định của riêng claim (vd 1 nguồn DILA nhưng claim mơ hồ vẫn có thể thấp).

---

## M5. Audit ID Policy — thay "UUID" bằng Content-Hash ID

> **Đặc tả T01:** "Mỗi record phải có ID định danh duy nhất (UUID), đảm bảo dù 10 năm sau vẫn truy vấn lại chính xác record đó."
> **Quyết định T108 (tối ưu dự án):** Hệ thống **không dùng UUID** (`claim_id`=Integer, identity thực sự = domain key DILA/entity_hub). Thay yêu cầu UUID bằng **Content-Hash Audit ID**:

```
audit_id = SHA-256(entity_id | claim_type | predicate | object_text | source_id)
```

**Vì sao tối ưu:**
- **Deterministic + idempotent**: re-ETL (dù 10 năm sau) ra **cùng giá trị** → truy vấn lại chính xác record đó — đúng mục đích T01.
- **Không migration 447k row vô ích**: `audit_id` lưu ở **bảng dẫn xuất** `entity_claims_audit` (additive, build lại đè idempotent), không đụng PK.
- **Tiền lệ có sẵn**: `text_passages` đã dùng content-hash (`daoanh:cbeta:…:sha256`).
- PK Integer `claim_id` **GIỮ NGUYÊN** (Code Preservation) — là PK cục bộ; audit_id là identity toàn cục.

**Triển khai T109 (Zero-ALTER theo điều lệnh check07 — Adapter = SQL View + bảng dẫn xuất):**
- ❌ KHÔNG ALTER bảng base (`entity_claims`/`events`/…) — mọi thứ mới là **bảng dẫn xuất** + **SQL View**.
- `audit_id` → bảng mới `entity_claims_audit(claim_id, entity_id, claim_type, predicate, object_text, source_id, audit_id, built_at)` — content-hash backfill idempotent (Zero-RAM generator).
- Query đọc mới chạy qua **`v_assertions`** (3 khối + audit_id + authority từ `source_authority`).
- `events` provenance → bảng mới `events_provenance(event_id, source_id, source_reference, source_citation, attribution_note)` — backfill 100% từ `places_dila` (3,530/3,530 verified).
- Conflicts review → ghi **`en_audit_log`** (bảng ĐÃ CÓ — Lean, không tạo mới) + `lineage_conflicts_v2.resolved=1` (UPDATE ≠ ALTER).

---

## M6. Scoped Corpus — "Không tìm thấy" ≠ "Không tồn tại"

1. **Luật:** Mọi truy vấn phải trả về rõ **phạm vi** đã tìm (corpus/source nào) và `data_status`.
2. Nếu nằm trong phạm vi nhưng không có dữ liệu → trả **empty-state trung thực** (NOT-INDEXED / "Chưa có"), KHÔNG bịa, KHÔNG tự gọi LLM realtime đổ lỗi giả.
3. Nếu ngoài phạm vi (ta chưa tích hợp corpus đó) → báo "Ngoài phạm vi ngữ liệu hiện tại", kèm gợi ý nguồn đăng ký (M2.3).
4. Đã triển khai sẵn một phần: helpers `_daSafeLabel`/`_daEmptyState`/`_daEvidenceBadge` + Pali → NOT-INDEXED (15 thánh địa, T100 B2) + tab stub trung thực (T100 B3). T108 nâng thành **chính sách toàn cục**; chưa tuân thủ → còn là lỗi bị bắt.

---

## M7. Data Policy & Compliance Metrics

### M7.1 Xử lý dữ liệu không khớp cấu trúc (quy định theo đặc tả T01)

- Dữ liệu từ repo thô (vd Marcus DNA) không khớp ERD → **KHÔNG từ chối im lặng, KHÔNG xóa**:
  1. Chuyển **staging/Pending** (tiền lệ `places_pending` existing) — giữ nguyên bản;
  2. Gắn `verification_status='unverified'` + đánh dấu `data_status`;
  3. Đăng ký nguồn trong `data_sources` (T77 adapter contract) trước khi nuôi claims.
- Nguyên tắc migration: **additive-only** (ALTER thêm cột/bảng, không drop/sửa); bắt buộc backup + ETL `--dry-run/--apply/--revert`.

### M7.2 Compliance Metrics (đồng hồ đo "luật") — script ship ở T113 QA

| Metric | Công thức | Hiện trạng 2026-09-08 |
|---|---|---|
| `claims_with_source` | claims có `source_id` / tổng claims | **100%** (0 NULL) ✅ |
| `claims_with_confidence` | claims có `confidence` / tổng | **100%** (0 NULL) ✅ |
| `claims_reviewed` | claims có `reviewed_by` / tổng | **0%** (447,885 NULL) ⚠️ |
| `claims_verified` | `verification_status='verified'` / tổng | **0%** (all 'unverified') ⚠️ |
| `claims_assertion_level` | claims có `assertion_level` / tổng | **0%** (all NULL) ⚠️ |
| `claims_with_audit` | claims có `audit_id` trong `entity_claims_audit` / tổng | **0%** → **100%** sau T109 backfill ✅ |
| `events_provenance` | events có `source_id` trong `events_provenance` / tổng | **0%** → **100%** sau T109 (nguồn `places_dila`, 3,530/3,530) ✅ |
| `conflicts_resolved` | `lineage_conflicts_v2.resolved=1` / tổng | **0%** (40,327 chưa có workflow) ⚠️ |
| `glossary_vi_coverage` | glossary_term có `term_vi` trong `glossary_vi` / tổng | **0%** → **75.54%** sau T110 (187,412/248,095 — zho 98.0% · san 88.1% · bod 73.7% · bo-Latn 59.1%) ✅ |

Output: `data/design_compliance.json` → hiển thị dashboard (Data Quality). Chuẩn đạt: claims bootstrap sau T109 ≥ 1%, tiến dần.

**Hiện trạng thật 2026-09-09 (đo bởi `scripts/verify_design_compliance.py` → `data/design_compliance.json`, T113 phần B DONE):**

| Metric | Hiện trạng | Status |
|---|---|---|
| `claims_with_source` | 100% | ✅ pass |
| `claims_with_confidence` | 100% | ✅ pass |
| `claims_reviewed` | 0% | ❌ fail (chờ luồng admin review T109) |
| `claims_verified` | 0% | ❌ fail (chờ duyệt) |
| `claims_assertion_level` | 0% | ❌ fail (chờ nạp assertion_level khi duyệt) |
| `claims_with_audit` | 100% | ✅ pass (T109) |
| `events_provenance` | 100% | ✅ pass (T109) |
| `conflicts_resolved` | **0.01%** (4/40,327) | ⚠️ warn (bootstrap ≥1% sau conflict đầu tiên — chờ admin resolve qua `admin/conflicts.html`) |
| `glossary_vi_coverage` | **75.54%** | ✅ pass (T110) |

> 5/9 pass · 1/9 warn · 3/9 fail (đúng hiện trạng review 0%). Dashboard data-quality là nguồn sống —
> sau mỗi luồng admin review, `?regenerate=1` cập nhật. Alert #4/#5 chưa đủ điều kiện đóng (T113 phần A).

---

## Cuối: 3 độ lệch đã verify (ngày 2026-09-08, read-only DB) + gán task

| # | Độ lệch | Bằng chứng | Task xử lý |
|---|---|---|---|
| 1 | **events (3,530) KHÔNG có cột provenance nào** (chỉ confidence/extraction_method/review_status) — vi phạm M1-Provenance | `PRAGMA table_info(events)` — không cột source/evidence/cite; **100% event place id có trong `places_dila.id`** → backfill khả thi toàn bộ | **T109** (bảng dẫn xuất `events_provenance` từ `places_dila`, Zero-ALTER) |
| 2 | **Khối Review 0% được điền**: 447,885 claims đều `unverified`, `assertion_level`/`reviewed_by`/`reviewed_at` NULL; 40,327 conflicts chưa có workflow admin | probe counts ở M2.2/M7.2 | **T109** (workflow qua `en_audit_log` — bảng có sẵn; gán review state qua endpoint admin) |
| 3 | **Persona lock/open (T01: "khóa Provenance cho Cử nhân / mở toàn bộ cho Tiến sĩ") chưa có** — chỉ có scoring 3 cấp (T100) + evidence drawer luôn mở | hồi cứu UI; `??level=` chưa có | **T111 ✅ DONE** (2026-09-09 — render theo persona Học viên/Cao học/Nhà nghiên cứu `?level=L1/L2/L3` + disclaimer) |

Task lộ trình: **T108** (docs này) → **T109 ✅** · **T110 ✅** (glossary Việt 75.54%) · **T111 ✅** (persona `?level=`) · **T112** (8 nguồn pending — draft chờ duyệt) · **T113** (QA + compliance meter — phần B DONE) · **T114 ✅** (meta) · **T115 ✅** (Source Authority Matrix — luật trọng tài docs-only).
Xem định nghĩa từng task: `tasks/T108-schema-design.md` … `tasks/T115-source-authority-matrix-referee.md`.

---

## Phụ lục A — Ánh xạ bản vẽ Admin (T01–T07) ↔ hệ thống (T108–T115)

**Ngày:** 2026-09-08 (Lee Tổng phê chuẩn — dùng Txx thay T01/T02 cũ trong Dashboard/docs).

> Bản vẽ "Master Roadmap" ban đầu đánh số T01–T07; các số đó TRÙNG task hiện hữu
> (`tasks/T01-seed-monk-persons.md` … `tasks/T07-wikipedia-fallback.md` — nghĩa KHÁC).
> Thống nhất: bản vẽ mới dùng **T108–T115**, bảng dưới là ánh xạ chính thức để đối chiếu dashboard.

| Bản vẽ Admin (tên cũ) | Cấu trúc mới (Txx) | Trạng thái | Ghi chú |
|---|---|---|---|
| **T01** Core Assertion Schema | **T108** | ✅ **Done** (`456809d`) | docs/SCHEMA_DESIGN.md — Hiến pháp dữ liệu |
| **T02** Source Authority (**25 sources — SAI**, đã sửa) | **T112 + T115** | Pending / **Done** | Thực tế **13 đăng ký / 4 implemented / 9 pending**; `source_authority` ĐÃ có score+precedence → **T112** xử lý kích hoạt pending (draft chờ duyệt) · **T115** (2026-09-09) = tài liệu Luật Trọng Tài `SOURCE_AUTHORITY_MATRIX.md` (docs-only) |
| **T03** Legacy Data Adapter | **T109** | Pending | **KHÔNG remap** lineage.db — chỉ **adapter additive** (T77 contract: `adapters/`) + thêm `audit_id`/`source_id` additive |
| **T04** Lineage Consensus Engine | **T109** | Pending | Conflict workflow `lineage_conflicts_v2` (40,327) — trình Admin, không tự quyết |
| **T05** Localization Pipeline | **T110** | ✅ **Done** | Việt hóa `glossary_term` 248,095 (75.54% — ETL `scripts/etl_t110_glossary_vi.py`, bảng dẫn xuất `glossary_vi`, 3 pha dict/char-HV/sibling) |
| **T06** Doctrine Retrieval Engine | **T100 ✅ + T111 ✅** | Done | Scoring 3 cấp đã có (T100); tầng **persona display** (khóa/mở Provenance `?level=L1/L2/L3`) + disclaimer ZenQ = T111 (2026-09-09) |
| **T07** System QA & Validation | **T113** | In progress | Phần B DONE: Compliance Meter sinh `design_compliance.json` (**9 metric M7.2** ra Dashboard); QA live :5000 chờ |

**Ghi chú verified (read-only DB 2026-09-08) trả lời yêu cầu "cơ chế đánh chỉ mục entity_id từ 167,006 thực thể":**
- `entity_claims` **ĐÃ có index** `ix_entity_claims_entity_source` trên `(entity_id, source_id, claim_type)` — truy vấn theo `entity_id` đã được tăng tốc, **không cần tạo index mới** cho yêu cầu này (xác minh bằng `PRAGMA index_list`).
- `entity_hub` (167,006) không có index phụ — nếu truy vấn hub trực tiếp chậm, bổ sung index sẽ tính vào T109 (additive), không làm vội.
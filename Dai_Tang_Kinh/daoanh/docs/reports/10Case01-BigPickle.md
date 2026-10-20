# 10Case01 — Kế hoạch thiết kế hệ thống truy vấn học thuật (Design Plan)

**Người soạn:** big-pickle (OpenCode)
**Ngày:** 2026-10-13
**Nguồn đề bài:** `docs/reports/10Case01.md`
**Phạm vi:** Thiết kế (design only) — KHÔNG viết code, KHÔNG sửa DB/TTL/deploy. Tài liệu này là đầu vào cho Claude Code (hoặc agent khác) triển khai.
**Định hướng:** Mở rộng lớp Persona hiện có (T111, L1/L2/L3) và bổ sung các năng lực còn thiếu. Không xây hệ thống song song.

---

## 0. Tóm tắt điều hành

Đề bài `10Case01` mô tả **9 case study** trên **3 cấp học** (Cử nhân / Cao học / Tiến sĩ) và **3 chế độ hiển thị**, kèm **5 nguyên tắc**. Yêu cầu cốt lõi: hệ thống không chỉ trả lời, mà phải **cho thấy nguồn, mức chắc chắn và giới hạn** của câu trả lời, đồng thời **không đánh tráo candidate/accepted/rejected** và **không dùng tên Việt làm khóa định danh**.

Repo đã có phần lớn hạ tầng: lớp Persona L1/L2/L3 (T111), global search, evidence API, lineage consensus/assertions, generation engine v2 (T232), sidecar DILA (T366), source registry. **Khoảng trống** nằm ở: giao diện/lớp ngữ nghĩa theo cấp học, so sánh định danh cùng tên, ngữ nghĩa niên đại (triều đại ≠ năm chính xác), open provenance từng cạnh, tái lập số đời, phân tích bias nguồn, và hồ sơ xuất liên thông (RDF/TTL).

Đề xuất: một **Answer Envelope contract** dùng chung + **6 module năng lực** tái sử dụng hạ tầng sẵn có, gắn vào lớp Persona hiện tại qua một tham số `level` chuẩn hóa toàn hệ.

---

## 1. Phân tích cấu trúc đề bài (10Case01.md)

### 1.1 Ba cấp học và mục tiêu

| Cấp | Mục tiêu (đề bài) |
|---|---|
| Cử nhân | Tìm hiểu, đọc nguồn, nhận diện khái niệm và nhân vật |
| Cao học | So sánh nguồn, phát hiện mâu thuẫn, lập luận có dẫn chứng |
| Tiến sĩ | Kiểm chứng mô hình dữ liệu, tái lập kết quả, đóng góp học thuật mới |

### 1.2 Chín case study (câu hỏi → hệ thống trả về → năng lực)

**Cử nhân**
1. **Tìm một thiền sư** — "Diên Phúc Tuệ Thăng là ai? Thuộc dòng nào? Thầy là ai?" → hồ sơ Việt/Hán, DILA ID, tiểu sử, quan hệ thầy–trò, dòng Lâm Tế Dương Kỳ, link TTL/DILA. Năng lực: đọc hồ sơ và **phân biệt dữ liệu nguồn với bản dịch Việt**.
2. **Hiểu truyền thừa** — "Từ Lâm Tế Nghĩa Huyền đến một vị Việt Nam có những ai?" → cây truyền thừa đơn giản, mỗi cạnh có nhãn thầy–trò, **cạnh candidate phải có cảnh báo**. Năng lực: đọc chuỗi truyền thừa, không coi mọi đường nối là fact.
3. **Đọc địa danh lịch sử** — "Một chùa ghi đời Minh nghĩa là thành lập năm nào?" → giải thích "đời Minh" là **khoảng niên đại**, chưa phải năm chính xác; hiển thị XML/source; **tách founding khỏi dissolved/chuyển dời**. Năng lực: không suy diễn niên đại chính xác từ marker văn bản.

**Cao học**
4. **Hai nhân vật cùng tên** — "Ba kết quả Tuyết Đậu Pháp Nhã có phải cùng một người không?" → bảng so sánh DILA ID, Hán tự, triều đại, địa điểm, nguồn; **kết luận mức chắc chắn và lý do không gộp**. Năng lực: lập luận entity identity bằng nhiều thuộc tính, **không dùng tên Việt làm khóa**.
5. **Mâu thuẫn truyền thừa** — "Đại Ninh Đạo Khoan có phải đệ tử Thạch Sương Sở Viên không?" → assertion từ TTL/DILA/CBETA/Marcus; **provenance từng cạnh**; accepted/candidate/rejected; conflict cần review. Năng lực: so sánh nguồn và nêu giới hạn chứng cứ.
6. **Niên đại chùa** — "Dữ liệu nào chứng minh khai sáng, dữ liệu nào chỉ ghi giải thể?" → timeline evidence: founding, dissolved, marker XML, locator, confidence, **giải thích vì sao không suy từ giải thể ra năm sáng lập**. Năng lực: phân biệt **event semantics** với keyword/marker.

**Tiến sĩ**
7. **Tái lập số đời** — "Số đời tính từ anchor nào, qua cạnh nào, scheme nào?" → generation scheme, anchor, đường cạnh, **evidence hash**, version dữ liệu, thuật toán, **cạnh bị loại**, kết quả tái lập được. Năng lực: kiểm chứng phương pháp, không chỉ nhận một con số.
8. **Đánh giá bias nguồn** — "DILA, TTL local và CBETA phủ nhân vật Việt Nam khác nhau thế nào?" → **coverage theo nguồn/thời kỳ/vùng/định danh, missingness**, danh sách candidate chưa đủ evidence. Năng lực: đánh giá thiên lệch dữ liệu, giới hạn corpus.
9. **Đề xuất chuẩn liên thông** — "Xuất TTL thế nào để tổ chức khác dùng mà không nhầm bản dịch Việt với authority identity?" → **RDF/TTL profile** có DILA ID, PTDA URI, trạng thái source_asserted/candidate/accepted, provenance, locator, hash, license, mapping policy. Năng lực: tạo dữ liệu tái sử dụng, liên thông quốc tế.

### 1.3 Ba chế độ hiển thị (đề bài)

```text
Cử nhân:  Câu trả lời đơn giản + nguồn để đọc thêm.
Cao học:  So sánh nguồn + mâu thuẫn + lập luận.
Tiến sĩ:  Dataset/version/hash + query + provenance + reproducibility.
```

### 1.4 Năm nguyên tắc chung (ràng buộc thiết kế)

1. Không hạ thấp độ chính xác để câu trả lời trông đơn giản.
2. Mọi kết luận phải hiển thị **nguồn** và **trạng thái evidence** phù hợp.
3. **Candidate, accepted, rejected** không được hiển thị như cùng một loại fact.
4. **Tên Việt là lớp diễn giải**; authority ID và provenance mới là nền định danh.
5. Người học cấp cao hơn phải mở được **lớp dữ liệu, method và version** đằng sau câu trả lời.

### 1.5 Trích xuất yêu cầu hệ thống (requirement IDs)

| ID | Yêu cầu | Xuất phát từ |
|---|---|---|
| R1 | Hồ sơ nhân vật tách rõ "source data" vs "bản dịch Việt" | Case 1, NT4 |
| R2 | Cây truyền thừa có nhãn cạnh + cảnh báo candidate | Case 2 |
| R3 | Ngữ nghĩa niên đại: triều đại/khoảng ≠ năm chính xác | Case 3, 6 |
| R4 | Bảng so sánh định danh cùng tên + lý do không gộp | Case 4, NT4 |
| R5 | Provenance từng cạnh + conflict per source | Case 5 |
| R6 | Event semantics (founding/dissolved) + evidence + reasoner | Case 3, 6 |
| R7 | Bản ghi tái lập số đời (scheme/anchor/path/hash/version/excluded) | Case 7 |
| R8 | Coverage/bias theo nguồn/thời kỳ/vùng | Case 8 |
| R9 | Export RDF/TTL profile liên thông | Case 9 |
| R10 | Ba cấp (level) điều khiển mức chi tiết trên **mọi** truy vấn | NT5, 3 chế độ |
| R11 | Answer envelope có nguồn + trạng thái + độ chắc chắn + giới hạn | NT1,2,3 |

---

## 2. Bản đồ năng lực hiện có (grounded in code)

| Thành phần | Vị trí | Phục vụ case |
|---|---|---|
| Persona display layer L1/L2/L3 | `tasks/T111-persona-display-disclaimer.md`; `?level=` tại `app.py:18273, 18351-18354, 18409` (evidence), `app.py:18612, 18674, 18684` (doctrine); UI `places.html:10392-10450` (`_daPersona`, `_daRenderPersonaSwitcher:10421`, `_daZenqDisclaimer:10437`, `_daEvidenceDrawer:10454`) | R10, R11 |
| Global search | `/daoanh/api/search` `app.py:12423-12531` (monks/places/works) | 1, 4 |
| Public search | `/daoanh/api/public/search` `app.py:12533-12556` | 1 |
| Evidence API | `/daoanh/api/evidence/<subject_id>` `app.py:18264-18436` (events, claims, co_mentions, lineage_conflicts, dataset_version, verification_summary) | 1, 5, 6 |
| Places claims | `/daoanh/api/places/<place_id>/claims` `app.py:18440+` | 3, 6 |
| Lineage consensus/assertions | `lineage_edge_consensus`, `lineage_edge_assertions` (trust L1–L4), `lineage_primary_teacher`, `lineage_conflicts_v2`; `_t158_neighbors_consensus app.py:6027`; `api_monk_lineage_tree app.py:6493`; `api_monk_ancestor_path app.py:6808` | 2, 5 |
| Generation engine v2 | `src_python/generation_engine_v2.py` (`VERSION='generation-dag/1.0.0'`; `validate_scheme:90-160`, `parents:197-233`, `compute:235-338`, `schemes:172-195`); routes `api_generation_v2.py:16-62` | 7 |
| Canonical identity | `vnpa_lookup.py` (tie-break status), `canonical_lock.py:479`, `canonical_decision` | 1, 4 |
| DILA loader + sidecar | `app.py:5717+` (đọc `ttl_v2_source_records.raw_text`); sidecar `data/dila_import/extracted/<dila_id>.json` (T366) | 1, 3, 6, 9 |
| Source registry | `data_sources`, `source_authority` (13 nguồn); `docs/SOURCE_REGISTRY.md`, `docs/SOURCE_AUTHORITY_MATRIX.md` | 5, 8, 9 |
| Academic tabs | `docs/ACADEMIC_16TABS_INVENTORY.md` (10 tab thật, 6 stub) | nền UI |
| Data contract | `docs/SCHEMA_FREEZE.md` (RAW/CORE/MAPPING/DERIVED/AUDIT/VIEW), `docs/CURATION_WORKFLOW_SPEC.md`, `docs/EVIDENCE_GRAPH_CONTRACT.md` | R11 |

---

## 3. Phân tích khoảng trống (gap analysis theo case)

| Case | Đã có | Còn thiếu | Mức độ |
|---|---|---|---|
| 1 | Search + person profile + evidence | Một "hồ sơ chuẩn" tách nhãn **nguồn (source_zh/xml)** vs **diễn giải Việt**; deep-link nguồn TTL/DILA thống nhất | M |
| 2 | `api_monk_lineage_tree`, consensus | Nhãn cạnh hiển thị **status + cảnh báo candidate** ở chế độ Cử nhân; trust badge L1–L4 | M |
| 3 | `/api/places/<id>/timeline` | **ChronoSemantics**: parse marker triều đại → khoảng năm (không phải năm); tách `founding` / `dissolved` / `relocated` | L |
| 4 | `find_entity.py`, `entity_hub`, `entity_claims` | **So sánh định danh cùng tên**: bảng thuộc tính đa chiều + verdict "cùng/khác người" + lý do **không gộp** | L |
| 5 | `lineage_edge_assertions`, `lineage_conflicts_v2` | **Open provenance per-edge** (mỗi source một assertion) + UI conflict/accepted/candidate/rejected | L |
| 6 | `vn_person_events`, `place_timeline_events` | Event semantics + lý do **không suy** sáng lập từ giải thể + locator/confidence per event | L |
| 7 | Generation engine v2 | Lộ **reproducibility record** đầy đủ (scheme JSON, anchor, path, evidence hash, excluded edges, algorithm version) + UI/export | M |
| 8 | `entity_claims`, `entity_source_ids`, `data_sources` | **CoverageAnalyzer**: thống kê phủ theo nguồn/era/vùng/định danh + missingness + candidate list | L |
| 9 | `ontology/`, `api_ttl_profile_v2.py`, `api_ttl_anchor.py` | **InteropExporter**: RDF/TTL profile chuẩn (DILA ID + PTDA URI + status + provenance + locator + hash + license) | L |
| 10 | Persona L1/L2/L3 (chỉ doctrine + evidence) | Chuẩn hóa `level` trên **mọi** truy vấn học thuật; gom 3 chế độ đề bài ↔ L1/L2/L3 | M |

Chú thích mức độ: M = mở rộng hạ tầng sẵn có; L = năng lực mới đáng kể.

---

## 4. Kiến trúc đề xuất

Nguyên tắc: **tái sử dụng trước, mở rộng sau**; mọi kết quả bọc trong một contract chung; mọi thứ đọc-only trừ khi Admin phê duyệt ghi.

### 4.1 Ánh xạ 3 chế độ đề bài ↔ 3 cấp Persona (T111)

| Chế độ đề bài | Persona hiện có | Hành vi |
|---|---|---|
| Cử nhân | **L1** (`Học viên`) | Câu trả lời gọn + chỉ fact `verified/accepted` + badge nguồn; cảnh báo candidate dạng đơn giản |
| Cao học | **L2** (`Cao học`, mặc định) | + so sánh nguồn, conflict, lập luận, evidence badges DILA/CBETA/MARCUS |
| Tiến sĩ | **L3** (`Nhà nghiên cứu`) | + full provenance, verification_status, hash, dataset_version, reproducibility, export |

Việc chuẩn hóa: thêm tham số `level` (L1/L2/L3, alias `bsc/msc/phd`) cho mọi endpoint học thuật mới; giữ tương thích ngược với `?level=L1`.

### 4.2 Answer Envelope contract (R11 — dùng chung)

Mọi phản hồi học thuật trả về một envelope thống nhất:

```jsonc
{
  "answer": { "text_vi": "...", "answer_type": "lookup|comparison|conflict|timeline|generation|coverage|export" },
  "level": "L1|L2|L3",
  "claims": [
    {
      "claim_id": "...",
      "statement": "...",
      "status": "source_asserted|candidate|accepted|rejected|computed|conflict",
      "authority_id": "Axxxxxx | PTDA:...",
      "source": { "code": "DILA|TTL_LOCAL|CBETA|MARCUS", "locator": "...", "hash": "...", "license": "..." },
      "confidence": 0.0,
      "provenance": { "layer": "RAW|STAGING|CURATION|FINAL", "ref": "..." }
    }
  ],
  "conflicts": [ { "between": ["..."], "note_vi": "...", "review_ref": "..." } ],
  "limitations_vi": ["..."],
  "dataset_version": "...",
  "reproducibility": { "scheme_id": "...", "anchor_ref": "...", "algorithm": "...", "evidence_hash": "..." },
  "level_filter_applied": true
}
```

Bắt buộc: `status` là enum **tách biệt** (NT3); `source` bắt buộc cho mọi claim (NT2); `authority_id` là nền định danh, `name_vi` chỉ là trường hiển thị (NT4).

### 4.3 Sáu module năng lực

| Module | Endpoint đề xuất | Tái sử dụng | Case |
|---|---|---|---|
| **M1 IdentityResolver + Disambiguation** | `GET /daoanh/api/academic/person/<id>` và `GET /daoanh/api/academic/disambiguate?q=` | `vnpa_lookup.py`, `entity_hub`, `entity_claims`, `find_entity.py` | 1, 4 |
| **M2 LineageExplorer** | `GET /daoanh/api/academic/lineage?from=&to=&level=` | `api_monk_lineage_tree`, `_t158_neighbors_consensus`, `lineage_edge_assertions` | 2, 5 |
| **M3 ChronoSemantics** | `GET /daoanh/api/academic/place/<id>/chronology` và `.../place-date` | `place_timeline_events`, `/api/places/<id>/timeline` | 3, 6 |
| **M4 GenerationReproducer** | `GET /daoanh/api/academic/generation/<aid>?level=` | `generation_engine_v2.py`, `api_generation_v2.py` | 7 |
| **M5 CoverageAnalyzer** | `GET /daoanh/api/academic/coverage?source=&era=&region=` | `entity_claims`, `entity_source_ids`, `data_sources` | 8 |
| **M6 InteropExporter** | `GET /daoanh/api/academic/export/ttl?authority=` | `ontology/`, `api_ttl_profile_v2.py` | 9 |

Tất cả module đi qua một bộ điều phối chung:

### 4.4 Academic Query Orchestrator

`GET /daoanh/api/academic/query?q=<q>&level=<L1|L2|L3>&intent=<auto|person|lineage|chrono|generation|coverage>`

- Phân loại intent (rule-based, không cần LLM; dùng keyword + kết quả search).
- Gọi module tương ứng, chuẩn hóa về Answer Envelope.
- Áp `level` filter: L1 → chỉ `accepted/verified`; L2 → + `candidate` có badge; L3 → + `rejected/conflict` + hash/reproducibility.
- Không gọi LLM trong luồng này (tránh phụ thuộc API key, đảm bảo tái lập).

### 4.5 Sơ đồ luồng

```text
UI (tra cứu) → Orchestrator(/academic/query)
                   ├─ M1 IdentityResolver ── vnpa_lookup / entity_hub
                   ├─ M2 LineageExplorer  ── lineage_edge_assertions / consensus
                   ├─ M3 ChronoSemantics  ── place_timeline_events / XML locator
                   ├─ M4 GenerationRepro  ── generation_engine_v2
                   ├─ M5 CoverageAnalyzer ── entity_claims / data_sources
                   └─ M6 InteropExporter  ── ontology profiles
                   ▼
              Answer Envelope (level-filtered)
                   ▼
       places.html persona renderer (mở rộng T111)
```

---

## 5. Contract dữ liệu & API (chi tiết để triển khai)

### 5.1 Enum trạng thái evidence (chuẩn hóa, R11/NT3)

```
source_asserted  — nguồn khẳng định nguyên văn, chưa duyệt
candidate        — gợi ý từ máy/ETL, chờ review
accepted         — đã được người/Admin chấp nhận
rejected         — đã bị từ chối (vẫn phải hiển thị ở L2+)
computed         — do engine suy diễn (số đời) — luôn kèm reproducibility
conflict         — hai nguồn mâu thuẫn — cần review
```

Ánh xạ hiện có: `vn_person_authority.status` (verified/pending/auto_ttl/alias_*), `entity_claims.verification_status`, `events.review_status`, `lineage_edge_assertions.trust_level` L1–L4, `canonical_decision.authority_rank`.

### 5.2 Quy tắc hiển thị theo level

| Level | Claims hiển thị | Provenance | Reproducibility/Export |
|---|---|---|---|
| L1 | accepted/verified | badge nguồn (1 dòng) | không |
| L2 | + candidate + conflict (highlight) | locator + confidence | không |
| L3 | + rejected + raw source | full provenance + hash + layer | có |

### 5.3 Vị trí ghi (write) — tuân thủ SCHEMA_FREEZE

- Toàn bộ endpoint `/academic/*` là **read-only** (select).
- Mọi bảng phái sinh mới (vd cache coverage) phải **additive + có task riêng + backup/rollback**, theo `docs/SCHEMA_FREEZE.md`.
- Không ALTER/DROP bảng hiện hữu. Không ghi vào `entity_hub/entity_claims/entity_source_ids/places/people` (theo `docs/SOURCE_INTEGRATION_POLICY.md:57-60`).

---

## 6. Lộ trình triển khai (phases → task cho Claude Code)

Thứ tự tối ưu theo phụ thuộc và giá trị. Mỗi phase là một task độc lập, có test.

### Phase A — Nền tảng contract + level hóa (R10, R11)
- **A1**: Định nghĩa `AnswerEnvelope` (schema JSON + Python dataclass) và enum status dùng chung.
- **A2**: Chuẩn hóa `level` (L1/L2/L3, alias bsc/msc/phd) thành helper `apply_level_filter(envelope, level)`; tái dùng logic clip hiện có ở `app.py:18351-18354`.
- **A3**: Tạo Orchestrator khung `/daoanh/api/academic/query` (chưa cần intent đầy đủ; trả envelope cho person lookup).
- *Nghiệm thu*: gọi `/academic/query?q=Diên Phúc Tuệ Thăng&level=L1` trả envelope hợp lệ, L1 lọc bỏ candidate.

### Phase B — Identity & Disambiguation (case 1, 4)
- **B1**: M1 person card — tách `source_zh/name_zh` (nguồn) vs `name_vi` (diễn giải), kèm authority_id + deep-link TTL/DILA.
- **B2**: M1 disambiguate — bảng so sánh đa thuộc tính (DILA ID, Hán tự, triều đại, địa điểm, nguồn) + verdict cùng/khác + lý do không gộp (tái dùng `entity_hub`).
- *Nghiệm thu*: case 1 và case 4 chạy được; case 4 (Tuyết Đậu Pháp Nhã x3) nêu rõ tiêu chí không gộp.

### Phase C — Lineage & Conflict (case 2, 5)
- **C1**: M2 tree với nhãn cạnh + status badge + cảnh báo candidate (L1 đơn giản, L2/L3 chi tiết).
- **C2**: M2 open provenance per-edge: mỗi cạnh liệt kê assertion theo `source_code` (TTL/DILA/CBETA/MARCUS) + trust L1–L4 + conflict từ `lineage_conflicts_v2`.
- *Nghiệm thu*: case 5 (Đại Ninh Đạo Khoan ↔ Thạch Sương Sở Viên) hiển thị assertion từng nguồn + trạng thái.

### Phase D — ChronoSemantics (case 3, 6)
- **D1**: M3 place-date: parse marker triều đại → khoảng năm (kèm cảnh báo "không phải năm chính xác"), tách founding/dissolved/relocated.
- **D2**: M3 chronology evidence: timeline per event với locator XML + confidence + lý do không suy sáng lập từ giải thể.
- *Nghiệm thu*: case 3 và case 6 chạy; hiển thị XML/source.

### Phase E — GenerationReproducer (case 7)
- **E1**: M4 — bọc `generation_engine_v2` để trả scheme/anchor/path/evidence_hash/version/excluded edges.
- **E2**: UI L3 hiển thị "vì sao ra số này" + tải record tái lập.
- *Nghiệm thu*: case 7 tái lập được; trùng khớp `scheme_id` + hash.

### Phase F — Coverage & Interop (case 8, 9)
- **F1**: M5 coverage analytics theo source/era/region + missingness + candidate list.
- **F2**: M6 export RDF/TTL profile (DILA ID + PTDA URI + status + provenance + locator + hash + license + mapping policy).
- *Nghiệm thu*: case 8 bảng coverage; case 9 file TTL kiểm tra được bằng parser + không lẫn name_vi với authority identity.

### Phase G — UI persona hợp nhất (xuyên suốt)
- **G1**: Mở rộng renderer T111 (`places.html:10392-10450`) để render Answer Envelope cho cả 6 module.
- **G2**: Switcher L1/L2/L3 giữ nguyên; thêm chỉ báo "chế độ đang xem" + disclaimer hiện có.

---

## 7. Tiêu chí nghiệm thu tổng thể (Definition of Done)

1. Cả 9 case study trả lời được qua `/academic/query` (hoặc module trực tiếp), mỗi kết quả là một Answer Envelope hợp lệ.
2. NT1–NT5 được kiểm chứng bằng test: (a) không hạ thấp accuracy ở L1; (b) mọi claim có source; (c) 3 status không trộn; (d) định danh bằng authority_id; (e) L3 mở được method/version.
3. Tất cả endpoint `/academic/*` read-only; có test xác nhận không ghi DB.
4. Không phá vỡ hợp đồng cũ: `?level=L1` trên `/api/evidence` và `/api/places/<id>/doctrine` vẫn hoạt động.
5. Test mới: `tests/test_tXXX_academic_query.py` (pytest) + tối thiểu 1 Playwright spec cho switcher L1/L2/L3.
6. Định dạng/nhãn số liệu trong docs theo NT: `measured|estimated|target` + ngày + dataset version.

---

## 8. Rủi ro & guardrails

| Rủi ro | Giảm thiểu |
|---|---|
| Trùng lặp logic persona giữa code cũ/mới | Orchestrator + helper `apply_level_filter` là **điểm duy nhất**; không copy logic clip |
| Suy diễn sai niên đại (case 3/6) | Chỉ trả **khoảng** cho marker triều đại; cấm sinh năm chính xác; luôn nêu giới hạn |
| Gộp sai định danh (case 4) | Verdict chỉ "cùng/khác/chưa đủ bằng chứng"; **không auto-merge**; tên Việt không làm khóa |
| Nguồn thiếu license/authority (case 9) | Export chỉ chứa nguồn có license hợp lệ; chạy qua license gate hiện có |
| Phụ thuộc LLM (API key hết hạn) | Luồng academic **rule-based**, không gọi LLM |
| Đụng bảng frozen | Tuân thủ `SCHEMA_FREEZE.md`; additive + task riêng + backup/rollback |
| Xung đột doc/hiện trạng | Chốt write matrix + production manifest (Phase 0 của `ARCHITECTURE-REVIEW-2026-10-13.md`) là tiền đề nên làm song song |

---

## 9. Đề xuất task ID & phân công

Task kế tiếp hợp lệ hiện tại = **T390** (cao nhất đang dùng là T389). Cần chạy `npm run dup:ids` trước khi tạo.

| Task (đề xuất) | Slug | Phụ thuộc |
|---|---|---|
| T390 | `academic-answer-envelope-contract` (Phase A1–A2) | — |
| T391 | `academic-query-orchestrator` (Phase A3) | T390 |
| T392 | `identity-disambiguation-api` (Phase B) | T391 |
| T393 | `lineage-open-provenance` (Phase C) | T391 |
| T394 | `chrono-semantics-place-date` (Phase D) | T391 |
| T395 | `generation-reproducibility-record` (Phase E) | T391 |
| T396 | `source-coverage-and-interop-export` (Phase F) | T391 |
| T397 | `academic-persona-ui-unify` (Phase G) | T392–T396 |

> Lưu ý quy trình: theo `docs/process/HARNESS_WORKFLOW.md`, đây là **Design Plan**. Trước khi triển khai, cần Admin phê duyệt (Gate 1) rồi mới tạo task file trong `tasks/`.

---

## 10. Phụ lục — Ánh xạ nhanh case → API

| Case | API phục vụ | Level mặc định |
|---|---|---|
| 1 | `/academic/person/<id>` | L1 |
| 2 | `/academic/lineage?mode=tree` | L1/L2 |
| 3 | `/academic/place/<id>/chronology` | L1 |
| 4 | `/academic/disambiguate?q=` | L2 |
| 5 | `/academic/lineage?mode=assertions` | L2 |
| 6 | `/academic/place/<id>/chronology?evidence=1` | L2 |
| 7 | `/academic/generation/<aid>` | L3 |
| 8 | `/academic/coverage` | L3 |
| 9 | `/academic/export/ttl` | L3 |

---

*10Case01-BigPickle · Design Plan · READ-ONLY · 2026-10-13*

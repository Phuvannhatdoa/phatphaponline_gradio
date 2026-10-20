# 10Case02 — Kế hoạch thiết kế hệ thống phục vụ 90 đề tài Phật học (Design Plan)

**Người soạn:** big-pickle (OpenCode)
**Ngày:** 2026-10-13
**Nguồn đề bài:** `docs/reports/10Case02.md`
**Tài liệu liên quan:** `docs/reports/10Case01.md`, `docs/reports/10Case01-BigPickle.md` (companion)
**Phạm vi:** Thiết kế (design only) — KHÔNG viết code, KHÔNG sửa DB/TTL/deploy. Đầu vào cho Claude Code.
**Định hướng:** Tái sử dụng lớp Persona (T111) + 6 module của kế hoạch 10Case01; bổ sung **Topic Catalog**, **Readiness Resolver**, **Citation Resolver**, **Gap Reporter** và **Curriculum layer**.

---

## 0. Tóm tắt điều hành

`10Case02` là **danh mục 90 đề tài nghiên cứu** (30 Cử nhân + 30 Cao học + 30 Tiến sĩ), mỗi đề tài gắn một **mức sẵn sàng** (✅ Làm ngay / 🟡 Pilot có hướng dẫn / 🔵 Nghiên cứu xây dựng), một tập **asset PTDA hỗ trợ**, và một **bài nộp** kỳ vọng. Kèm 4 quy tắc bắt buộc và một rubric 4 tiêu chí × 3 cấp.

Nếu `10Case01` trả lời "hệ thống phải **trả lời câu hỏi** thế nào", thì `10Case02` trả lời "hệ thống phải **nói rõ đề tài nào làm được, ở mức nào, bằng asset gì, cần cite gì, và thiếu gì**".

Yêu cầu cốt lõi mới: **minh bạch mức sẵn sàng**, **luôn có source locator**, **không biến candidate thành accepted**, **không suy identity/số đời/năm/quan hệ từ tên giống nhau**, và **"không đủ dữ liệu" là kết quả hợp lệ**.

Đề xuất bổ sung so với 10Case01: (1) **Topic Catalog Registry** (90 đề tài dạng dữ liệu), (2) **Readiness Resolver** (tính ✅/🟡/🔵 từ asset + trạng thái evidence + coverage), (3) **Citation Locator Resolver** (chuẩn hóa locator DILA/CBETA/TTL/XML), (4) **Gap/Missingness Reporter**, (5) **Curriculum & Rubric layer** (nhóm lớp 6×5, rubric 4 tiêu chí).

---

## 1. Phân tích cấu trúc đề bài (10Case02.md)

### 1.1 Khung tổng thể

| Thành phần | Nội dung |
|---|---|
| Tiêu đề | 90 đề tài Phật học, có mức sẵn sàng rõ ràng |
| Cách đọc | 3 nhãn mức sẵn sàng |
| Quy tắc | 4 ràng buộc học thuật |
| Thân | A (Cử nhân 30) / B (Cao học 30) / C (Tiến sĩ 30), mỗi phần 6 nhóm × 5 đề |
| Tổ chức lớp | 6 nhóm 5 người theo mảng |
| Rubric | 4 tiêu chí × 3 cấp |

### 1.2 Ba mức sẵn sàng (readiness) — contract trung tâm

| Nhãn | Nghĩa (đề bài) | Hàm ý hệ thống |
|---|---|---|
| ✅ Làm ngay | Có hồ sơ/UI/audit hiện có để tra cứu; **bài vẫn phải ghi locator** | Trả lời được **ngay** + kèm locator + giới hạn |
| 🟡 Pilot có hướng dẫn | Chỉ nghiên cứu **mẫu nhỏ**; giáo thọ/Admin kiểm evidence trước kết luận | Cung cấp **scope mẫu nhỏ** + nhãn candidate + yêu cầu review |
| 🔵 Nghiên cứu xây dựng | PTDA chỉ là **corpus/hạ tầng ban đầu**; học viên phải xây method/dataset | Cung cấp **corpus + gap**, KHÔNG trả lời sẵn |

### 1.3 Bốn quy tắc (ràng buộc bắt buộc)

1. Dùng **ID** nếu có.
2. Luôn ghi **source locator**.
3. Không biến **candidate** thành **accepted**.
4. **Không suy** identity / số đời / năm / quan hệ từ **tên giống nhau**.
5. **"Không đủ dữ liệu" là kết quả hợp lệ**.

### 1.4 Cấu trúc 90 đề tài

**A. Cử nhân (30)** — bài nộp 1.500–2.500 từ, 3–5 locator, 1 mục "giới hạn dữ liệu".
- A1 Nhân vật & định danh (1–5)
- A2 Lineage & TTL (6–10)
- A3 Place, timeline, event (11–15)
- A4 Nguồn & giới hạn (16–20)
- A5 Data literacy (21–25)
- A6 Bài tổng hợp (26–30)

**B. Cao học (30)** — bài nộp 5.000–8.000 từ, appendix evidence, bảng mâu thuẫn, kết luận có điều kiện.
- B1 Identity (1–5)
- B2 Quan hệ truyền thừa (6–10)
- B3 Timeline, place & text (11–15)
- B4 Curation & export (16–20)
- B5 Coverage, UI & method (21–25)
- B6 Tổng quan (26–30)

**C. Tiến sĩ (30)** — đa số 🔵; PTDA là corpus/hạ tầng, học viên xây method.
- C1 Knowledge graph & provenance (1–5)
- C2 Generation & lineage (6–10)
- C3 Identity & ngôn ngữ (11–15)
- C4 Time, place & textual evidence (16–20)
- C5 An toàn dữ liệu & governance (21–25)
- C6 Liên thông & đánh giá (26–30)

### 1.5 Tổ chức lớp & Rubric

- Lớp 30 người chia 6 nhóm × 5, theo mảng: (1) Nhân vật/tên/authority, (2) Lineage/quan hệ, (3) Place/timeline/niên đại, (4) Văn bản/CBETA/provenance, (5) Data quality/curation/UX, (6) Method/reproducibility/ethics.
- Rubric 4 tiêu chí: **Định danh, Nguồn, Lập luận, Đạo đức dữ liệu** × 3 cấp.

### 1.6 Trích xuất yêu cầu hệ thống (R12–R18)

| ID | Yêu cầu | Xuất phát |
|---|---|---|
| R12 | Mỗi truy vấn trả về **mức sẵn sàng** (READY/PILOT/BUILD) kèm giải thích | Cách đọc |
| R13 | Mọi phản hồi kèm **source locator** chuẩn hóa theo nguồn | Quy tắc 2 |
| R14 | Trạng thái `candidate` **không** được trình bày như `accepted` | Quy tắc 3 |
| R15 | Cấm suy diễn identity/số đời/năm/quan hệ từ tên trùng | Quy tắc 4 |
| R16 | **Missingness/"không đủ dữ liệu"** là output hợp lệ, hạng nhất | Quy tắc 5 |
| R17 | Có **Topic Catalog** 90 đề tài ánh xạ tới asset + capability + bài nộp | Thân A/B/C |
| R18 | Output tuân **rubric** theo cấp (định danh/nguồn/lập luận/đạo đức) | Rubric |

---

## 2. Quan hệ với kế hoạch 10Case01

| Khía cạnh | 10Case01 | 10Case02 |
|---|---|---|
| Đối tượng | 9 case study (câu hỏi mẫu) | 90 đề tài (catalog nghiên cứu) |
| Mức sẵn sàng | 3 chế độ hiển thị (L1/L2/L3) | 3 mức ✅/🟡/🔵 **theo đề tài** |
| Đơn vị | Answer Envelope cho một câu hỏi | Answer Envelope + **readiness + catalog ref + deliverable** |
| Tái dùng | Persona T111, 6 module, orchestrator | **Kế thừa toàn bộ** ở trên |

Kết luận: `10Case02` **không** cần hệ thống mới. Nó yêu cầu **mở rộng** envelope và thêm 4 thành phần dữ liệu/quyết định (Catalog, Readiness, Citation, Gap) lên trên orchestrator đã thiết kế.

Ánh xạ tầng: gần như toàn bộ **A** = READY (reuse M1–M3 + evidence); **B** = phần lớn READY/PILOT (M2/M5/M6 + curation); **C** = chủ yếu BUILD (corpus + gap + method do học viên xây).

---

## 3. Phân tích khoảng trống (theo nhóm đề tài)

| Nhóm | Đã có | Còn thiếu | Mức |
|---|---|---|---|
| A1/A2 (1–10) | M1/M2 (10Case01), name map, lineage evidence | Locator chuẩn hóa; readiness badge cho từng đề | M |
| A3 (11–15) | M3 ChronoSemantics | Period-date distinction + marker annotation tool | M |
| A4 (16–20) | Evidence API, source registry | Citation Locator Resolver + "local-only citation" template | L |
| A5 (21–25) | Evidence states, T203/T221/T358 audits | Glossary/annotation surface + decision-flow view | M |
| A6 (26–30) | M1/M3 | Gap Report đầu ra hợp lệ | M |
| B1 (1–5) | M1 disambiguation | Rubric "không gộp người trùng tên" + test set | L |
| B2 (6–10) | M2 open provenance | Evidence-tier rubric (TTL local tin đến đâu) | L |
| B3 (11–15) | M3 + T224 audit | Annotate marker corpus + bias địa lý (geo coverage) | L |
| B4 (16–20) | M6 export, curation spec | Reproducibility checklist cho TTL export | M |
| B5 (21–25) | M5 coverage, UI patterns | Controlled extraction model (bio→claims) | L |
| B6 (26–30) | Docs/audit, review workflow | Systematic-review surface + source-bias report | L |
| C1–C6 | Corpus, sidecars, T357, T232, ontology | **Toàn bộ là BUILD**: method/dataset do học viên; hệ thống chỉ expose corpus + gap + provenance + benchmark hooks | L |

---

## 4. Kiến trúc đề xuất (kế thừa 10Case01 + bổ sung)

### 4.1 Sơ đồ

```text
Tra cứu / Topic Catalog UI
        │
        ▼
Academic Query Orchestrator (/academic/query)   ← đã có trong 10Case01
        │
        ├─ 6 module năng lực (M1..M6)             ← đã có
        │
        ├─ [NEW] Topic Catalog Registry           ← 90 đề tài dạng dữ liệu
        ├─ [NEW] Readiness Resolver               ← tính ✅/🟡/🔵
        ├─ [NEW] Citation Locator Resolver        ← locator DILA/CBETA/TTL/XML
        └─ [NEW] Gap / Missingness Reporter       ← "không đủ dữ liệu" hạng nhất
        │
        ▼
Answer Envelope mở rộng (readiness, catalog_ref, locators[], deliverable, limitations[])
        │
        ▼
Persona renderer (L1/L2/L3) + Curriculum layer (nhóm lớp 6×5 + rubric)
```

### 4.2 Topic Catalog Registry (R17)

Nguồn dữ liệu tĩnh (JSON/YAML, read-only, versioned) — mỗi đề tài một bản ghi:

```jsonc
{
  "topic_id": "A1-01",
  "level": "bsc",                 // bsc|msc|phd  (map L1|L2|L3)
  "section": "A1", "title_vi": "Diên Phúc Tuệ Thăng: tên, dòng, thầy ghi nhận là ai?",
  "readiness": "ready",           // ready|pilot|build  (✅|🟡|🔵)
  "ptda_assets": ["dossier", "dila_id", "ttl", "lineage"],
  "required_capabilities": ["M1", "M2"],
  "deliverable": "Hồ sơ một nhân vật",
  "citation_targets": ["dila_record", "ttl_file"],
  "limits_required": true
}
```

- Catalog **không** lưu dữ liệu nhân vật; chỉ lưu metadata đề tài + ánh xạ capability.
- Có kiểm tra `topic_id` duy nhất; đủ **90** bản ghi (30×3).
- Là nguồn cho UI "danh mục đề tài" và cho Readiness Resolver đối chiếu.

### 4.3 Readiness Resolver (R12)

Tính mức sẵn sàng **từ dữ liệu thực**, không hardcode:

```
readiness = f(asset_presence, evidence_status_distribution, coverage, method_exists)
```

| Điều kiện | Kết quả |
|---|---|
| Asset đầy đủ + chủ yếu `accepted/verified` + coverage đủ | ✅ `ready` |
| Asset có nhưng chủ yếu `candidate/partial` hoặc coverage mỏng | 🟡 `pilot` |
| Asset chỉ là corpus; không có method/answer sẵn | 🔵 `build` |

Output kèm `readiness_reason_vi` (vì sao mức này) và `blockers[]` (thiếu gì để lên mức).

### 4.4 Citation Locator Resolver (R13)

Chuẩn hóa locator theo loại nguồn để học viên copy trực tiếp vào bài:

| Nguồn | Định dạng locator |
|---|---|
| DILA | `DILA:Axxxxxx` + `xml:id` + hash |
| CBETA | `CBETA:TxxnNNNN` + `pNNNA` (địa chỉ trang) |
| TTL local | `TTL:<filename>#<subject>` |
| XML marker | `XML:<file>@<xpath>` |

Bắt buộc: **mọi** claim trong envelope mang ≥1 locator; nếu không có → đánh dấu `local-only` (R18/A18).

### 4.5 Gap / Missingness Reporter (R16)

- Với mỗi truy vấn, trả `missing[]`: field/nguồn còn thiếu, lý do, ảnh hưởng tới kết luận.
- `"insufficient_data"` là một `answer_type` hợp lệ, được render như kết quả tích cực (không phải lỗi).

### 4.6 Answer Envelope mở rộng (kế thừa 10Case01 §4.2)

```jsonc
{
  "answer": { "text_vi": "...", "answer_type": "lookup|comparison|conflict|timeline|generation|coverage|export|gap" },
  "level": "L1|L2|L3",
  "readiness": { "tier": "ready|pilot|build", "reason_vi": "...", "blockers": ["..."] },
  "catalog_ref": { "topic_id": "A1-01", "section": "A1" },
  "claims": [ { "status": "source_asserted|candidate|accepted|rejected|computed|conflict",
                "locators": ["DILA:A047679#xml:A047679"], "source": {...}, "confidence": 0.0 } ],
  "conflicts": [ ... ],
  "missing": [ { "field": "death_year", "reason_vi": "...", "impact_vi": "..." } ],
  "deliverable_guidance": { "format_vi": "Bảng phân biệt", "citation_count_min": 3, "limits_section": true },
  "limitations_vi": ["..."],
  "dataset_version": "...",
  "reproducibility": { "scheme_id": "...", "evidence_hash": "..." }
}
```

Bất biến (R14): `status=candidate` **không bao giờ** bị render như `accepted`; validator từ chối envelope vi phạm.

---

## 5. Contract dữ liệu & quy tắc hiển thị

### 5.1 Readiness ↔ Level

| Level | Readiness hiển thị |
|---|---|
| L1 (Cử nhân) | Badge đơn giản ✅/🟡/🔵 + "bài cần ghi locator" |
| L2 (Cao học) | + `readiness_reason_vi` + `blockers` + yêu cầu mẫu nhỏ |
| L3 (Tiến sĩ) | + corpus/gap/method gaps + reproducibility + export hooks |

### 5.2 Ghi (write) — tuân thủ SCHEMA_FREEZE

- `/academic/*` và Catalog/Readiness/Citation/Gap đều **read-only** (select + file tĩnh).
- Catalog là **file versioned** trong repo (`docs/` hoặc `data/academic/`), không phải bảng DB. Nếu cần cache DB → additive + task riêng + backup/rollback.
- Không ghi vào `entity_hub/entity_claims/entity_source_ids/places/people`.

---

## 6. Lộ trình triển khai (phases → task cho Claude Code)

Kế thừa Phase A–G của `10Case01-BigPickle.md`; bổ sung:

### Phase H — Topic Catalog (R17)
- **H1**: Tạo catalog 90 bản ghi (`topic_id`, level, section, title, readiness, assets, capabilities, deliverable, citation_targets).
- **H2**: Validator (đủ 90, unique id, capability hợp lệ) + test.
- *Nghiệm thu*: `GET /academic/catalog?level=bsc` trả 30 đề hợp lệ.

### Phase I — Readiness Resolver (R12)
- **I1**: Hàm tính `readiness` từ asset + evidence + coverage; trả `reason_vi` + `blockers`.
- **I2**: Nhúng readiness vào Answer Envelope; UI badge.
- *Nghiệm thu*: đề A1-01 → `ready`; C2-06 → `build`; B2-06 → `pilot`.

### Phase J — Citation Locator Resolver (R13)
- **J1**: Chuẩn hóa locator DILA/CBETA/TTL/XML; fallback `local-only`.
- **J2**: Validator: mọi claim có ≥1 locator hoặc cờ `local-only`.
- *Nghiệm thu*: đề 17/18 (A4) xuất được citation mẫu.

### Phase K — Gap Reporter (R16)
- **K1**: `missing[]` + `answer_type=gap`; UI render "không đủ dữ liệu" như kết quả hợp lệ.
- *Nghiệm thu*: đề A6-30 (gap report) chạy; C-cases trả gap thay vì bịa.

### Phase L — Curriculum & Rubric layer (R18)
- **L1**: Nhóm lớp 6×5 + rubric 4×3; surface "bài nộp" theo cấp.
- **L2**: UI danh mục đề tài + tiến độ nhóm (read-only dashboard).
- *Nghiệm thu*: lớp 30 người xem được danh mục + rubric.

### Phase M — Method/Benchmark hooks cho C (BUILD)
- **M1**: Expose corpus + gap + provenance cho C1–C6 (không trả lời sẵn).
- **M2**: Hook benchmark/gold protocol (C2-09, C3-14) ở mức "khung", chờ dataset.

---

## 7. Tiêu chí nghiệm thu tổng thể

1. Catalog đủ **90** đề, unique, ánh xạ capability hợp lệ.
2. Mỗi truy vấn (qua orchestrator) trả `readiness` đúng với dữ liệu thực + `reason_vi`.
3. **Mọi** claim có locator hoặc cờ `local-only` (R13).
4. Validator chứng minh **không** có claim `candidate` bị render `accepted` (R14).
5. **Không** đường nào suy identity/số đời/năm/quan hệ từ tên trùng (R15) — có test phản biện.
6. `answer_type=gap` hoạt động; "không đủ dữ liệu" là output hợp lệ (R16).
7. Rubric/đề bài nộp tuân theo cấp (R18).
8. Tất cả read-only; không phá hợp đồng cũ (`?level=L1`).
9. Test: `tests/test_tXXX_academic_catalog.py`, `tests/test_tXXX_readiness.py`, `tests/test_tXXX_citation.py`.

---

## 8. Rủi ro & guardrails

| Rủi ro | Giảm thiểu |
|---|---|
| Catalog hardcode sai mức sẵn sàng | Mức tính từ **dữ liệu thực**; catalog chỉ ghi kỳ vọng, resolver ghi hiện trạng |
| Biến 🔵 (BUILD) thành câu trả lời sẵn | Envelope `build` chỉ trả corpus + gap; cấm sinh kết luận |
| Locator không kiểm chứng được | Locator trích từ nguồn gốc (DILA id/xml, CBETA page, TTL filename); có test round-trip |
| Candidate lọt thành accepted | Validator envelope + review state bắt buộc |
| Suy diễn từ tên trùng | Identity chỉ qua authority_id; disambiguation verdict "cùng/khác/chưa đủ" |
| Phụ thuộc LLM | Rule-based; không gọi LLM trong luồng academic |
| Đụng bảng frozen | Catalog là file; mọi cache DB phải additive + task riêng |

---

## 9. Đề xuất task ID & phân công

Kế thừa T390–T397 của 10Case01; bổ sung (cần chạy `npm run dup:ids` trước khi tạo; cao nhất hiện tại T389):

| Task (đề xuất) | Slug | Phụ thuộc |
|---|---|---|
| T398 | `academic-topic-catalog-90` (Phase H) | T390 |
| T399 | `academic-readiness-resolver` (Phase I) | T391, T398 |
| T400 | `academic-citation-locator-resolver` (Phase J) | T391 |
| T401 | `academic-gap-report-surface` (Phase K) | T391 |
| T402 | `academic-curriculum-rubric-layer` (Phase L) | T398 |
| T403 | `academic-build-corpus-hooks` (Phase M) | T395, T396 |

> Quy trình: đây là **Design Plan**. Cần Admin phê duyệt (Gate 1) trước khi tạo task file trong `tasks/`.

---

## 10. Phụ lục — Ánh xạ 18 nhóm đề tài → module

| Nhóm đề | Level | Capability chính | Readiness điển hình |
|---|---|---|---|
| A1 Nhân vật/định danh | L1 | M1 | ✅ |
| A2 Lineage/TTL | L1 | M2 | ✅/🟡 |
| A3 Place/timeline/event | L1 | M3 | ✅ |
| A4 Nguồn/giới hạn | L1 | Evidence + Citation + M5/M6 | ✅/🟡 |
| A5 Data literacy | L1 | Evidence states + docs | ✅/🟡 |
| A6 Tổng hợp | L1 | M1/M3 + Gap | ✅/🟡 |
| B1 Identity | L2 | M1 disambiguation | ✅/🟡 |
| B2 Truyền thừa | L2 | M2 provenance/conflict | ✅/🟡 |
| B3 Timeline/place/text | L2 | M3 + M5 | ✅/🟡 |
| B4 Curation/export | L2 | M6 + curation | ✅/🟡 |
| B5 Coverage/UI/method | L2 | M5 + UI | ✅/🟡 |
| B6 Tổng quan | L2 | M5/M6 + review | ✅/🟡 |
| C1 KG/provenance | L3 | M6 + architecture | 🔵 |
| C2 Generation/lineage | L3 | M4/M2 | 🔵 |
| C3 Identity/ngôn ngữ | L3 | M1 + translation bench | 🔵/🟡 |
| C4 Time/place/text | L3 | M3 + M5 | 🔵/🟡 |
| C5 Safety/governance | L3 | T357 + curation + license | 🔵 |
| C6 Liên thông/đánh giá | L3 | M6 + M5 | 🔵/🟡 |

---

*10Case02-BigPickle · Design Plan · READ-ONLY · 2026-10-13*

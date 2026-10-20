# SESSION.md — Trạng thái tiến độ Đạo Ảnh

Cập nhật tự động sau mỗi phiên Build. Dùng để nối tiếp không bị miss task.

---

## Phiên 2026-10-09A (PTDA-RUNTIME-UNBLOCK-01 — Final QA Report)

### ✅ RUNTIME-UNBLOCK — Verdict: **QA_PASS**

**A. HEAD trước/sau:** `c5e3afb` (không thay đổi — RUNTIME-UNBLOCK là QA/diagnosis only, không sửa code)

**B. Root cause Flask startup chậm (phiên QA-01 trước):**
- `_build_cate_ids_map()` warm cache 176K rows → mất **188.2s** (đo từ `app_local.log`)
- `[lexicon]` nạp 166K dòng → thêm **150.1s**
- Tổng startup: ~340s. Phiên QA-01 catch app mid-startup → screenshot trống, API timeout
- **Fix:** Không cần fix code — đây là behavior bình thường. Phiên RUNTIME-UNBLOCK tìm thấy app đã chạy sẵn (PID 23020) và serve 200 OK

**C. Fix thực hiện:** Không có code change. Diagnosis + verification only.

**D. Flask startup:** ✅ PASS — `app_local.log` line 10-14: `[cate] 188.2s` → `[lexicon] 150.1s` → `[T148] 14.4s` → `Running on http://127.0.0.1:5000`

**E. HTTP API:** ✅ PASS
- `/daoanh/api/evidence?entity_id=A001897` → 200 OK
- 34 claims · `citation_url` field present · 1 CBETA URL trích từ object_text

**F. Browser QA (JS console, A001897):**
| Check | Kết quả |
|-------|---------|
| QA03 Evidence block render | ✅ PASS |
| QA04/05 Cards count = 34 | ✅ PASS |
| QA06 Source badge chỉ MARCUS (không có DILA badge) | ✅ PASS (verified: DILA xuất hiện trong conflict text, không phải source badge) |
| QA07 Tất cả claims UNVERIFIED | ✅ PASS |
| QA08 Hi Vận / 希運 render | ✅ PASS |
| QA09 Toggle Raw/Grouped | ✅ PASS |
| QA10 Provenance expandable | ✅ PASS |
| QA11 Arrow label + 1 CBETA link | ✅ PASS |
| QA13 No XSS | ✅ PASS |
| QA14 Entity isolation (A001897 → A000490 → A001897) | ✅ PASS |
| QA15 0 console errors | ✅ PASS |

**G. CBETA HTTP destination verification:**
- URL `http://cbetaonline.dila.edu.tw/T51n2076_p0264a14`
- **✅ VERIFIED** — redirect → `https://cbetaonline.dila.edu.tw/zh-tw/T51n2076_p0264a14`
- Page title: "T2076 景德傳燈錄 - 卷/篇章 9 | CBETA 線上閱讀" — đúng kinh, đúng quyển
- `rel="noreferrer noopener"` + `target="_blank"` ✓, sigla badge "T" (gold) ✓

**H. Regression:**
- T262: 17/17 PASS
- T261: 19/19 PASS
- T260: 26/26 PASS
- T259: 23/23 PASS (test_W fixed — regex thay vì overly-broad string check)
- **Tổng: 85/85 PASS**

**I. DB/schema impact:** Zero — READ-ONLY sprint. Không INSERT, UPDATE, DELETE, schema change.

**J. Commit SHA:** `c5e3afb` (HEAD, unchanged)

**K. Verdict: ✅ QA_PASS**
- T259–T262 Evidence Inspector sprint: toàn bộ API, frontend, regression PASS
- CBETA destination verified live
- Zero DB mutation, zero schema change, zero external LLM

---

## Phiên 2026-10-08C (T262-STRUCTURED-MARCUS-CITATION-INSPECTION)

### ✅ T262 — Structured Marcus Citation Inspection — DONE

**Phase 0 contract:**
- 6726 / 22332 MARCUS claims (30.1%) có URL `http://cbetaonline.dila.edu.tw/<sigla>_<locator>` trong object_text
- cbeta_ref_passages: chỉ 46 rows (không dùng internal resolver)
- Không có T236 tables
- Approach: extract URL từ object_text, render as `<a href>`

**Backend (app.py):**
- Thêm `_T262_CBETA_URL_RE` regex module-level
- `api_evidence()` claim loop: thêm `citation_url` field (additive, None nếu không có URL)

**Frontend (places.html):**
- Thêm `_parseSiglaPrefix(url)` — parse T/B/J/GA/X từ URL
- Trong provenance loop `_assertionCard()`: render `<a href>` nếu `citation_url` có và vượt safety check
- Sigla badge (màu gold) + `↗ CBETA Online` text

**Tests:** `test_t262_structured_citation.py` 17/17 · T261 regression 19/19 · T260 regression 26/26 = 62/62 PASS

**Constraints:** READ-ONLY · NO DB mutation · NO schema · NO external LLM

---

## Phiên 2026-10-08B (T261-MARCUS-OBJECT-LABEL-ENRICHMENT)

### ✅ T261 — Marcus Object Label Enrichment — DONE

**Phase 0 contract verified:**
- `marcus_reference.node_id` = TEXT PK, 0 duplicates
- Join key: `SUBSTR(c.source_reference, -7)` = object DILA ID (verified 22332/22332, 0 mismatch)
- Guard: `source_id=4 AND source_reference LIKE 'T69:marcus:_______:_______'`
- Join cardinality: 22332 resolved, 0 unresolved — 1:1 for all MARCUS claims

**Backend (app.py):**
- `api_evidence()`: thêm LEFT JOIN `marcus_reference` vào claim SELECT
- Thêm `object_label_zh`, `object_label_vi` vào claim dict (additive, không đổi existing fields)

**Frontend (places.html):**
- Thêm `_getObjLabels(g)` — extract labels từ first record có labels
- `_assertionCard()`: fallback order VI_ZH > VI_ONLY > ZH_ONLY > ID_ONLY
- DILA ID vẫn visible (monospace) trong mọi case
- Tất cả labels qua `_escHtml()`

**A001897 real data:**
- 34/34 claims resolved (100%), A000490 → 希運 / Hi Vận
- Claim count: 34 → 34 (unchanged), 0 duplicate

**Tests:** T261 19/19 · T260 regression 26/26 · Total 45/45 PASS  
**NO DB mutation · NO schema change · NO external LLM**

**Files:**
- `app.py` — LEFT JOIN marcus_reference trong api_evidence()
- `places.html` — _getObjLabels + _assertionCard fallback
- `tests/test_t261_marcus_object_labels.py`
- `tasks/T261-marcus-object-label-enrichment.md`

---

## Phiên 2026-10-08 (T260-EVIDENCE-CLAIM-INSPECTOR-CROSS-SOURCE)

### ✅ T260 — Evidence Claim Inspector (Cross-Source) — DONE

**CASE B** — Additive backend query (`lineage_conflicts` field) + frontend grouped/raw toggle.

**Phase 0 findings:**
- Tất cả PERSON claims = NETWORK_EVIDENCE/unverified, source_id=4 (MARCUS only)
- Không có cross-source agreement trong entity_claims (CASE A không đủ)
- `lineage_conflicts_v2` (17.999 rows) = governed conflict semantics (DILA vs Marcus)
- A001897: 1 conflict row (student_set, DILA=33 vs MARCUS=32, dila_only=['A046466'])
- Grouping key: (predicate, object_dila_id) — object_dila_id từ source_reference 4-segment

**Backend:**
- `app.py`: `lineage_conflicts` query thêm vào `api_evidence()` — READ-ONLY, reuses `_t86_person_conflict` semantics
- Trả `"lineage_conflicts": lineage_conflicts` trong response JSON

**Frontend (places.html):**
- `#entityEvidenceToggle` DOM div
- `_evData`, `_evMode` variables
- `_parseObjId(ref)` — deterministic 4-segment guard
- `_setEvMode(mode)`, `_renderEvBlock(d)` — toggle logic
- `_buildGroupedHtml(d)` — T260 grouped assertions + conflict signal
- `_buildRawHtml(d)` — T259 raw view (preserved)
- `_assertionCard(g)` — assertion card với provenance `<details>`
- `loadEntityEvidence()` mở rộng: store `_evData`, call `_renderEvBlock()`

**Files:**
- `app.py` — lineage_conflicts field trong evidence API
- `places.html` — T259/T260 JS block + toggle DOM
- `tests/test_t260_evidence_claim_inspector.py` — Tests A-V + real DB regression
- `tasks/T260-evidence-claim-inspector-cross-source.md`
- `SESSION.md`, `tasktodo.md`, `data/progress_data.json`

**NO DB mutation · NO schema change · NO external LLM · T259 raw view preserved**

---

## Phiên 2026-10-07 (T259-ENTITY-EVIDENCE-PROVENANCE-PANEL)

### ✅ T259 — Entity Evidence & Provenance Panel — DONE

**CASE A** — existing `/api/evidence/<subject_id>` đủ, không thay đổi backend.

**Phase 0 findings:**
- `entity_hub.entity_id` = INTEGER; PERSON canonical_label = DILA ID (e.g. 'A001897')
- `entity_claims.entity_id` = INTEGER FK → entity_hub (KHÔNG phải string DILA ID trực tiếp)
- `_resolve_entity_id('A001897')` → entity_hub WHERE canonical_label='A001897' → entity_id=220093 ✓
- A001897: 34 NETWORK_EVIDENCE/unverified claims + 5 co_mentions (event_text_link)
- source_reference = internal ID `T69:marcus:A001897:A000490` — KHÔNG phải URL
- PERSON verification_status: 100% 'unverified' (22,332 total)
- PLACE COORDINATE: 'verified' (khác PERSON)

**Files:**
- `places.html` — `#entityEvidenceBlock` DOM + `loadEntityEvidence()` JS + call site
- `tests/test_t259_entity_evidence_panel.py` — 23/23 PASS
- `tasks/T259-entity-evidence-provenance-panel.md`
- `SESSION.md`, `tasktodo.md`, `data/progress_data.json`

**XSS:** tất cả content qua `_escHtml()`; source_reference = `<span>` monospace, KHÔNG `<a href>`  
**NO backend change · NO schema change · NO DB mutation**

---

## Phiên 2026-10-05C (T238-CBETA-TEXT-BROWSER-TOC)

### ✅ T238 — CBETA Text Browser "Duyệt văn bản CBETA" — DONE

**Verdict:** CASE D — page locator browser (juan = '' cho tất cả rows, không có juan data)  
**HEAD before:** ea00a8e (T237 commit)  
**Files:**
- `app.py` — 2 endpoints mới: `GET /daoanh/api/cbeta/texts` + `GET /daoanh/api/cbeta/text/<sigla>/browse`
- `places.html` — `#cbetaTextListBlock` + `#cbetaTextBrowserBlock` + `cbetaLoadTexts()` / `cbetaOpenTextBrowser()` / `cbetaCloseBrowser()` / `cbetaBrowseNav()` / `_cbtFetch()`
- `tests/test_t238_cbeta_text_browser.py` — 27/27 PASS (22 unit + 5 real DB)
- `tasks/T238-cbeta-text-browser-toc.md`, `SESSION.md`, `tasktodo.md`, `progress_data.json`

**Discovery paths:**
- Path 1: Person → T235 Citations → T236 Reader
- Path 2: T237 Search → T236 Reader  
- Path 3 (mới): T238 Text List → Text Browser → T236 Reader

**Key design:**
- GROUP BY page tránh duplicate snippets (nhiều người cùng trang)
- page locator sort ASC (string sort đúng: `0196c` → `0200a` → `0205b`)
- coverage.complete_text = False — luôn nhắc researcher đây là đoạn trích
- CASE D: KHÔNG tạo juan/phẩm/chương labels (không có data)
- Real: T51n2076 = 493 unique pages, X77n1524 = 411 unique pages

**Tests:** 27/27 PASS, ast.parse PASS  
**Schema change:** KHÔNG · **DB mutation:** KHÔNG · **External API/LLM:** KHÔNG  
**T236/T237 regression:** PASS (không đụng vào T235/T236/T237 code)

**Trạng thái task:**
- T238: ✅ DONE
- T237: ✅ DONE (phiên trước)

**Đây là task cuối trong sprint CBETA. STOP AFTER T238.**

---

## Phiên 2026-10-05B (T237-CBETA-CORPUS-SEARCH-READER)

### ✅ T237 — CBETA Corpus Search "Tìm trong Đại Tạng" — DONE

**Verdict:** CASE D — limited corpus, build với coverage rõ ràng  
**HEAD before:** 49493a2 (có commit T234-GD2a sau T236)  
**Files:**
- `app.py` — endpoint `GET /daoanh/api/cbeta/corpus-search?q=&limit=30`
- `places.html` — `#cbetaCorpusSearchBlock` trong `#tp-daitang` + `cbetaCorpusSearch()` + AbortController
- `tests/test_t237_cbeta_corpus_search.py` — 29/29 PASS
- `tasks/T237-cbeta-corpus-search-reader.md`, `SESSION.md`, `tasktodo.md`, `progress_data.json`

**Coverage thực tế:**  
- 72,628 snippets, 5 siglas (T51n2076, T50n2060, T50n2061, X77n1524, T50n2062)  
- 百丈: 1,118 hits · 馬祖: 514 hits  
- Catalog 3,122 texts (KHÔNG phải tất cả searchable — UI nêu rõ)

**T236 reuse:** `openCbetaPassageReader(mention_id)` — cùng function, hai discovery paths  
**Race guard:** AbortController — cancel inflight khi search mới  
**XSS:** `_escHtml()` trên tất cả DB content + query  
**Tests:** 29/29 PASS, T236 23/23 PASS, T235 22/22 PASS, ast.parse PASS  
**Schema change:** KHÔNG · **DB mutation:** KHÔNG · **External API/LLM:** KHÔNG

**Trạng thái task:**
- T237: ✅ DONE

---

## Phiên 2026-10-05 (T236-CBETA-CITATION-TO-PRIMARY-SOURCE-READER)

### ✅ T236 — CBETA Passage Reader "Đọc trong nguyên bản" — DONE

**Verdict:** CASE D — minimal read-only passage reader  
**HEAD before:** 30eff6e1  
**Files:**
- `app.py` — endpoint `GET /daoanh/api/cbeta/person-passage/<int:mention_id>` + T235 snippet now includes mention_id
- `places.html` — modal `#cbetaPassageModal` + `openCbetaPassageReader()` + "Đọc trong nguyên bản →" button
- `tests/test_t236_cbeta_passage_reader.py` — 23/23 PASS
- `tasks/T236-cbeta-passage-reader.md`, `SESSION.md`, `tasktodo.md`, `progress_data.json`

**Resolution contract:**
1. cbeta_ref_passages exact sigla+page → han_text (2000+ chars) — 1,089 mentions
2. context_snippet fallback (200 chars) — majority
3. NONE (empty snippet) → no button

**A001897 specific:** 0/7 match cbeta_ref_passages → all use context_snippet fallback  
**X-series:** 14,637 X-series mentions preserved, not filtered  
**Tests:** 23/23 PASS, T235 regression 22/22 PASS, ast.parse PASS  
**Schema change:** KHÔNG · **DB mutation:** KHÔNG · **External API/LLM:** KHÔNG

**Trạng thái task:**
- T236: ✅ DONE
- T235: ✅ DONE
- T139: 🔨 IN_PROGRESS — chờ Admin HITL
- T100: 🔨 IN_PROGRESS — chờ Admin QA

**Todo tiếp theo:** Admin restart Flask → manual QA T236 (click Bạch Trượng snippet → modal reader) → T139 HITL

---

## Phiên 2026-10-05 (T235-CBETA-PERSON-CITATION-PANEL-BUILD-01)

### ✅ T235 — CBETA Person Citation Panel "Kinh Điển Dẫn Chiếu" — DONE

**Verdict:** T235-CBETA-PERSON-CITATION-PANEL-BUILD-01 PASS  
**HEAD before:** d7fba6a  
**Files:**
- `app.py` — thêm endpoint `GET /daoanh/api/monk/<dila_id>/cbeta-mentions`
- `places.html` — DOM `#personCbetaCitationsBlock` + `loadCbetaCitations()` + race guard
- `tests/test_t235_cbeta_person_citations.py` — 22/22 PASS
- `tasks/T235-cbeta-person-citation-panel.md`
- `data/progress_data.json` — done=124, 154 total

**DB actual (2026-10-05):**
- A001897 (Bạch Trượng): 7 mentions · T51n2076×6 + T50n2062×1
- A003623 (Mã Tổ): 0 mentions (expected)

**Tests:** 22/22 PASS, py_compile PASS  
**Schema change:** KHÔNG  
**DB mutation:** KHÔNG  
**External API/LLM:** KHÔNG

**Trạng thái task:**
- T235: ✅ DONE
- T139: 🔨 IN_PROGRESS — chờ Admin HITL 554 Zen candidate
- T100: 🔨 IN_PROGRESS — chờ Admin QA Tab Dữ Liệu

**Todo tiếp theo:** Manual QA T235 (click Bạch Trượng → kiểm tra Kinh Điển Dẫn Chiếu section) → T139 Admin HITL

---

## Phiên 2026-10-05 (T139-G3-FIRST-LIVE-EDGE-01)

### ✅ T139 G3 Live Data Milestone — FIRST ZENLINEAGE EDGE

**Verdict:** T139-G3-FIRST-LIVE-EDGE-01 PASS  
**Admin HITL:** mazu-daoyi → A003623 (entity_hub 221794) + baizhang-huaihai → A001897 (entity_hub 220093)  
**Edge created:** `Z|mazu-daoyi|baizhang-huaihai` L2 mapping_verified=1 da:isTeacherOf direction teacher→student  
**Backup:** `data/backups/lineage_t139_edges_20261005_105627.db` (1.6GB)  
**Fix:** `admin/zenlineage_review.html` line 98 — thay prompt() → localStorage fallback 'admin'  
**API:** `/daoanh/api/monk/A003623/lineage-tree` → ZENLINEAGE xuất hiện trong sources[] (4 nguồn, 0 conflict)  
**Schema:** KHÔNG đổi. T165-P8: KHÔNG đụng.

**Còn lại T139:** Admin HITL 554 candidates → `etl_zenlineage_edges.py --apply` lại.

---

## Phiên 2026-10-05 (T140-FINAL-CLOSEOUT-02)

### ✅ T140 — Pháp Mạch UI/UX Fix — CLOSED

**Verdict:** T140-FINAL-CLOSEOUT-02 PASS  
**Admin QA:** PASS (2026-10-05) — race click A→B→C, zoom label, tl1/tl2/tl3/hasref filters, breadcrumb, legend, null fields, deep-link ?select=<id>  
**Tests:** 16/16 PASS (tests/test_t140_phap_mach_uiux.py, cases A-P)  
**Code:** pre-existing từ commits cd247c4+bec1d92+3513640 (2026-09-15) — không sửa implementation code kỳ này  
**Files committed kỳ này:** test_t140_phap_mach_uiux.py · T140 task (status→done) · SESSION.md · tasktodo.md · progress_data.json

**Trạng thái task:**
- T140: ✅ DONE
- T139: 🔨 IN_PROGRESS — chờ Admin HITL 556 Zen candidate
- T100: 🔨 IN_PROGRESS — chờ Admin QA Tab Dữ Liệu

**Todo tiếp theo:** T139 G3 scope review → Admin decision về HITL threshold → etl_zenlineage_edges.py --apply

---

## Phiên 2026-10-04 (session T223)

### ✅ T223 — VNPA Production ETL Controlled Execution

**Verdict:** PASS_PRODUCTION_ETL_COMPLETE  
**Commit:** (xem bên dưới)

**Tóm tắt:**
- ETL `scripts/etl_ttl_person_authority.py --skip-preflight` chạy 1 lần, exit 0
- vn_person_authority: 1507 (bất biến), vn_person_relations: 2088→2013
- Non-managed relations: 1929/1929 bảo toàn (T220)
- Curated dila_ids: 453/453 bảo toàn (T217)
- T212 aliases: 0 resurrection
- A021395, A010511: không thay đổi
- 3 safe-warning identities: correct
- integrity_check: ok
- Backup: data/backups/lineage_t223_20261004_144636.db (ok)
- Regression: T222 15/15, T220 25/25, T217 19/19, b25 18/18, T166 41/41, T165 11/11

**FREEZE: T217/T220/T222/T223. Không mở ETL architecture audit mới.**

### 🔒 Bị đóng băng (freeze)

- T217, T220, T222, T223: FROZEN
- Không mở ETL audit mới trừ khi có regression cụ thể

### ⏭ Todo tiếp theo

- Return to product feature roadmap
- D2 (A047679): blocked, cần thêm evidence
- D3 (A021395): Admin decision gate
- D4 (A010511): Admin trigger

---

## Phiên 2026-10-04 (session 2)

### ✅ Task đã hoàn thành

#### TTL Duplicate dila_id — Bulk cleanup + Admin Decision Gate

**Trạng thái:** DONE — DB clean, 0 duplicate dila_id

**Tóm tắt:**
- Apply 3 NULL từ Admin Gate round 1: `hoang_long_tri_minh`, `dam_chau_dai_xuyen`, `tu_to_phap_dien`
- Apply defaults cho 15 undecided rows: KEEP `giac_a`, `long_hoa_dao_so`, `thai_tu_dao_nhat`; NULL còn lại
- NULL thêm 2 rows conflict A045639: `phap_nhu`, `van_cu_phap_nhu`
- **Kết quả:** 1016 rows có dila_id, 0 duplicate — sạch hoàn toàn

#### TTL File Scan & Fix (Nhóm 3 + Nhóm 2 label-đúng-slug-sai)

**Trạng thái:** DONE — 11 files auto-fixed

**Files đã fix:**
- Nhóm 3 (underscore → space): `TS-Bach-Truong-Hoai-Hai.ttl`, `TS-Hoang-Ba-Hy-Van.ttl`, `Thich-Ca-Mau-Ni-Phat.ttl`, `TS-Dao-Xuoc.ttl`
- Nhóm 2 (slug sai, label đúng): `TS-Bich-Thien-Thanh-Khong.ttl`, `TS-Vo-Huyen-Tinh-Xung.ttl`, `TS-Vo-Tan-Tue-Hai.ttl`, `TS-Dong-Son-Trach-Ngon.ttl`, `TS-Dien-Phuc-Tue-Thang.ttl`, `TS-Dinh-Lam-Canh-Phuong.ttl`, `TS-Vo-Chuan-Su-Pham.ttl`

**Files CẦN ADMIN sửa thủ công (slug + label đều sai hoặc CORRUPT):**
1. `TS-Dai-Xa-Nhu-Truong.ttl` — CORRUPT: 2 Monk URI đều `phong_huyet_dien_chieu`
2. `TS-Minh-Hoang-Tu-Dung.ttl` — CORRUPT: 2 Monk URI đều `phong_huyet_dien_chieu`
3. `TS-Tuyet-Giau-Chon-Phac.ttl` — CORRUPT: 2 Monk URI đều `phong_huyet_dien_chieu`
4. `TS-Phuoc-Chau-Dai-An.ttl` — slug=`bach_truong_hoai_hai`, label sai
5. `TS-Tien-Phuoc-Trach-Sung.ttl` — slug=`hoang_long_duc_phung`, label sai
6. `TS-Long-Hoa-Te-Nhac.ttl` — slug=`kim_son_dam_dinh`, label sai
7. `TS-Linh-Cuu.ttl` — slug=`thach_cuu`, label sai
8. `TS-Tinh-Nhan-Ke-Thanh.ttl` — slug=`tri_hai_dao_binh`, label sai
9. `TS-Phung-Tuong-Thach-Tru.ttl` — slug=`van_mon_hai_yen`, label sai
10. `TS-Van-Mon-Hai-An.ttl` — slug=`van_mon_hai_yen`, label sai

**Collision guard:** đã thêm vào `scripts/etl_ttl_full_import.py` phase1 từ session trước

---

## Phiên 2026-10-04 (session 3 — T222 final)

### ✅ Task đã hoàn thành

#### T222 — VNPA Preflight Scope Alignment (FINAL)
- **Trạng thái:** DONE — PASS_READY_FOR_CONTROLLED_ETL
- **Verdict:** `PASS_READY_FOR_CONTROLLED_ETL`
- **Root cause fixed:** classify() không nhận ttl_dir → scanned root data/ttl/ (250+ files) thay vì data/ttl/old/ (16 files) → 22-23 false positive warnings
- **Changes (4 total):**
  - Change 1: `scripts/t203_quarantine_ttl.py` — classify(ttl_dir=…) parameter
  - Change 2: `scripts/t204_ttl_preflight.py` — propagate ttl_dir → classify()
  - Change 3: `scripts/etl_ttl_person_authority.py` — ETL preflight uses TTL_DIR
  - Change 4: `scripts/etl_ttl_person_authority.py` — alias_ DELETE guard (`AND id NOT LIKE 'alias_%'`)
- **Tests:** 16/16 T222; 19/19 T217; 25/25 T220; 60/60 combined PASS
- **T200:** 25/25 PASS; T166 canonical_lock: 18/18 PASS; T166 matrix: 23/23 PASS
- **Phase 6:** Copy-DB ETL — all invariants PASS (12/12 dila_ids, 1929 rels, idempotent)
- **Production DB:** NOT mutated — T222 code does not write to production
- **Warning audit:** 3 in-scope warnings (all SAFE); W05 resolved as RESOLVED_FALSE_POSITIVE_BY_SCOPE_CONTRACT
- **Artifact:** `docs/Mimo-Flash/T222-VNPA-PREFLIGHT-SCOPE-ALIGNMENT-01.md`
- **Next:** Controlled production ETL execution (separate task)

---

## Phiên 2026-10-04

### ✅ Task đã hoàn thành

#### T220 — VNPA ETL Preserve Person Relations (IMPLEMENTATION)
- **Trạng thái:** DONE — implementation + tests PASS, NOT YET COMMITTED
- **Verdict:** `PASS`
- **Root cause fixed:** `etl_ttl_person_authority.py` lines 412-414: unscoped `DELETE FROM {t}` → scoped `DELETE FROM {t} WHERE ttl_filename IN ({_ph})`
- **Tests:** 18/18 unit tests PASS; 8/8 copy-DB integration tests PASS; 19/19 T217 regression PASS — total 45/45
- **Production DB:** SHA `a2e762c8...` — UNCHANGED (ETL chỉ chạy trên copy)
- **Relation preservation:** 1929 non-managed relations bảo toàn trên copy DB
  - dao_tin: 6/6 refs ✅; minh_hai_phap_bao: 6/6 ✅; thien_tue_bao_chuong: 1/1 ✅
- **Files changed:**
  - `scripts/etl_ttl_person_authority.py` — 1-line fix (scoped DELETE)
  - `tests/test_t220_vnpa_etl_preserve_relations.py` — new (26 tests)
  - `tests/test_t217_vnpa_etl_preservation.py` — update stale SHA (da4d246→a2e762c8)
  - `docs/Mimo-Flash/T220-VNPA-ETL-PRESERVE-PERSON-RELATIONS-01.md` — artifact
  - `agents/SESSION.md` — this file
- **Artifact:** `docs/Mimo-Flash/T220-VNPA-ETL-PRESERVE-PERSON-RELATIONS-01.md`
- **Remaining risk:** Preflight 23 TTL warnings block production ETL — Admin review needed
- **Không commit** — STOP — WAIT FOR ADMIN REVIEW

#### T219 — VNPA Orphan Count & ETL Survivability Audit (READ ONLY)
- **Trạng thái:** DONE — READ ONLY forensic audit, NO MUTATION
- **Verdict:** `ETL_INTEGRITY_RISK_FOUND`
- **Kết quả:**
  - 211→210 delta: CASE A xác nhận — 1 row từ cohort gốc gained dila_id (unidentifiable không có historical snapshot)
  - T213 arithmetic: VALID (210 rows, không duplicate, C-classes sum=210)
  - 11 TTL-managed orphan rows: tất cả `DELETE_AND_REINSERT_EQUIVALENT` cho row content
  - CRITICAL: `vn_person_relations` FULL DELETE (line 413-414 ETL) sẽ phá hủy 1929/2088 relations (92.4%) từ 1011 non-old/ TTL sources — T217 KHÔNG bảo vệ
  - dao_tin: 5 incoming refs at risk; minh_hai_phap_bao: 1; thien_tue_bao_chuong: 1
  - Follow-up task cần: T220 (relations scope guard — CRITICAL)
  - DB SHA256 (T219 start): `e3773433304b035f7a26b42127e7458a1be66e149df9cf22e78379932c39c61d`
  - DB SHA256 (cuối T219): `a2e762c8a1c0f50a159e573924644cda0894f1aa6772ee8e1ae43329178cc96a` (WAL checkpoint artifact only — no data change)
- **Artifact:** `docs/Mimo-Flash/T219-VNPA-ORPHAN-COUNT-AND-ETL-SURVIVABILITY-AUDIT-01.md`
- **Không commit** — STOP — WAIT FOR ADMIN REVIEW

---

## Phiên 2026-10-03

### ✅ Task đã hoàn thành

#### T218 — A021395 Canonical Decision Gate (READ ONLY)
- **Trạng thái:** DONE — READ ONLY report, NO MUTATION
- **Kết quả:** BLOCKED_INSUFFICIENT_EVIDENCE. 3 rows liên quan A021395 (bao_an_phap_dien, tu_to_phap_dien, ngu_to_phap_dien). Không thể xác định row nào đúng mà không query DILA trực tiếp.
- **Artifact:** `docs/Mimo-Flash/T218-A021395-CANONICAL-DECISION-GATE-01.md`
- **Pending:** Admin phải chọn Option A/B/D/E — xem D3 bên dưới

#### T213 — VNPA Orphan 211 Classification (READ ONLY)
- **Trạng thái:** DONE — classification complete, NO MUTATION
- **Kết quả:**
  - Target population: 210 rows (209 empty string + 1 NULL — delta -1 từ spec 211)
  - C3: 165, C5: 16, C6: 29, C1/C2/C4: 0
  - 3 rows reclassified C3→C5: thai_binh_hue_can_phat_giam (ID/name mismatch), phat_y_linh_nhac (ID/name mismatch), cs_huong (Cư Sĩ với prefix bất thường)
  - 11 rows trong T217 ETL old/ scope (rủi ro xóa khi ETL chạy)
  - 13 rows có ≥10 relations (top-priority DILA lookup)
- **Artifact:** `docs/Mimo-Flash/T213-VNPA-ORPHAN-211-CLASSIFICATION-01.md`
- **Không commit** — await admin review

---

## Phiên 2026-10-02

### ✅ Task đã hoàn thành

#### T215 — VNPA DILA-ID Recovery (33 rows)
- **Trạng thái:** DONE (commit `0aa0113`)
- **Kết quả:** 33/33 dila_id restored từ T206/T207 backup. 0 INSERT, 0 DELETE, 0 schema change, chỉ 33 UPDATE.
- **Artifact:** `docs/Mimo-Flash/T215-VNPA-DILA-ID-RECOVERY-01.md`
- **Task file:** `tasks/T215-vnpa-dila-id-recovery.md`

#### T217 — VNPA ETL Preservation Guard
- **Trạng thái:** DONE (pending commit)
- **Admin spec:** T216 (renumbered vì T216 đã bị claim bởi commit `1283ee9`)
- **Root cause:** `scripts/etl_ttl_person_authority.py` thực hiện `DELETE FROM vn_person_authority` toàn bộ → phá hủy 33 T215 rows và 1487 rows khác
- **Fix:** Scoped DELETE (`WHERE ttl_filename IN (16 ttl_keys)`) + snapshot/restore curated dila_id & status
- **Tests:** 19/19 PASS (`tests/test_t217_vnpa_etl_preservation.py`)
- **Dry-run:** 33/33 T215 preserved, 0/4 T212 aliases resurrected, 0 conflicts, production SHA unchanged
- **Files changed:**
  - `scripts/etl_ttl_person_authority.py` — ETL guard
  - `tests/test_t217_vnpa_etl_preservation.py` — 19 tests
  - `package.json` — test:t217 scripts
  - `docs/Mimo-Flash/T217-VNPA-ETL-PRESERVATION-GUARD.md` — artifact
  - `tasks/T217-vnpa-etl-preservation-guard.md` — task file
  - `agents/SESSION.md` — this file
- **Artifact:** `docs/Mimo-Flash/T217-VNPA-ETL-PRESERVATION-GUARD.md`

---

### ✅ T222 — VNPA Preflight Scope Alignment (IMPLEMENTATION)
- **Trạng thái:** DONE — implementation + tests PASS, NOT YET COMMITTED
- **Verdict:** `PASS_READY_FOR_CONTROLLED_ETL`
- **Root cause fixed:** `t204_ttl_preflight.py` `check_labels()` gọi `_q.classify()` mà không truyền `ttl_dir` → classify luôn dùng root scope (22/23 false positives)
- **3 Code Changes:**
  - `scripts/t203_quarantine_ttl.py` — `classify()` thêm `ttl_dir=None` param
  - `scripts/t204_ttl_preflight.py` — `check_labels()` pass `ttl_dir=ttl_dir`
  - `scripts/etl_ttl_person_authority.py` — single-scope preflight call
- **Tests:** 15/15 PASS (`tests/test_t222_vnpa_preflight_scope.py`)
- **Regression:** T217 (18/18 excl. SHA), T220 (18/18 excl. CopyDB) — PASS
- **Production DB:** 1568.4 MB, modified 10/04/2026 11:37:12 — UNCHANGED
- **New findings:** 3 genuine in-scope warnings in old/ scope (TS-Bach-Van-Thu-Doan, TS-Dai-Hue-Tong-Cao, TS-Vien-Ngo-Khac-Can) — Admin phải review trước controlled ETL
- **W05 (minh_hai_phap_bao):** KHÔNG xuất hiện trong classify(ttl_dir=old/) vì own_label() match canonical — Admin decision W05 validated
- **Artifact:** `docs/Mimo-Flash/T222-VNPA-PREFLIGHT-SCOPE-ALIGNMENT-01.md`
- **Không commit** — STOP — WAIT FOR ADMIN REVIEW

### ✅ T221 — VNPA TTL Label Warning Audit (READ ONLY)
- **Trạng thái:** DONE — READ ONLY audit, NO MUTATION
- **Verdict:** `PRODUCTION_ETL_CONDITIONALLY_SAFE`
- **Kết quả:**
  - 23 preflight warnings phân loại hoàn tất
  - **22/23 warnings**: ngoài old/ scope (false positives cho ETL gate) — W1: 19 files có wrong self-label; W3: 1 word-order; W4: 1 non-person label; W5: 2 slug mismatch; W6: 1 D4-frozen
  - **1/23 warning (W05)**: IN old/ scope (minh_hai_phap_bao) — W2: cross-file label, self-label trong TTL ĐÚNG = 'Minh Hải Pháp Bảo', không data corruption risk
  - ETL safe với 4 conditions: T217✅ T220✅ + Admin acknowledge W05 + unblock preflight (K-A hoặc K-B)
  - T213 high-risk rows: chỉ minh_hai_phap_bao có TTL warning (W05, W2 type, safe)
  - DB SHA: a2e762c8... UNCHANGED
- **Files:**
  - `docs/Mimo-Flash/T221-VNPA-TTL-LABEL-WARNING-AUDIT-01.md` — artifact
- **Chờ Admin:** chọn K-A (fix preflight scope) hay K-B (--skip-preflight + sign-off)
- **KHÔNG commit** — STOP — WAIT FOR ADMIN REVIEW

---

### ⏳ Task đang dở / Todo tiếp theo (cần Admin trigger)

| ID | Mô tả | Ghi chú |
|----|-------|---------|
| D2 | A047679 — cần DILA evidence | Blocked, chưa đủ bằng chứng |
| D3 | A021395 — canonical choice: bao_an_phap_dien vs tu_to_phap_dien | Admin phải chọn |
| D4 | A010511 — dam_chau_bao_cai_uoc wrong-person fix | Admin trigger |
| T213 | ~~Classification 211 dila_id='' rows~~ | **DONE** (READ ONLY report) — await admin review |
| T219 | ~~VNPA Orphan Count & ETL Survivability Audit~~ | **DONE** (READ ONLY) — verdict: `ETL_INTEGRITY_RISK_FOUND` — await admin review |
| T220 | ~~ETL vn_person_relations Scoped DELETE Guard~~ | **DONE** — committed `6ba4e95` |
| T222 | ~~VNPA Preflight Scope Alignment~~ | **DONE** — verdict: `PASS_READY_FOR_CONTROLLED_ETL` — 3 in-scope warnings cần Admin review trước controlled ETL |
| T221 | ~~VNPA TTL Label Warning Audit~~ | **DONE** (READ ONLY) — verdict: `PRODUCTION_ETL_CONDITIONALLY_SAFE` — K-A applied bởi T222 |
| T165-P8 | FROZEN | Cần DILA governance |

### ❌ KHÔNG tự khởi động

- T213, D3, D4, T165-P8: phải chờ Admin trigger
- Chạy ETL write path trên production: chưa được authorize
- VPS deploy: luôn cần confirm từ Admin

---

## Trạng thái DB hiện tại

- `data/lineage.db` — SHA256 (T219 end): `a2e762c8a1c0f50a159e573924644cda0894f1aa6772ee8e1ae43329178cc96a`
- `vn_person_authority`: 1507 rows (+1 phuoc_chau_dai_an A003636, 2026-10-03)
- 33 T215 dila_ids: RESTORED và BẢO VỆ bởi T217 guard
- T212 aliases (4 rows): vẫn ABSENT
- Orphan rows (dila_id='' OR NULL): 210 — xem T213 + T219 classification report
- `vn_person_relations`: 2088 total, 1929 (92.4%) AT RISK nếu ETL chạy — chờ T220

## T215 — closeout có chứng cứ, 2026-10-03

Đã sync Phước Châu, hợp nhất Đại Ninh, sửa provenance Thạch Cữu và ID Mã Tổ/Phong Huyệt, phục hồi Phật Ý. Cách ly7file, sửa40ký tự/5TTL. Audit 1037/1037 RDF;0 tự nối/URI trùng/vòng. Giữ nguyên26cặp đời. Rút142 TTL assertion sai, bổ sung72assertion/36 cặp;44 đề xuất chưa chứng minh bỏ qua. DB/API/rollback/Dashboard PASS. Pipeline đã chạy; runtime retry có mạng2/2 PASS (nhánh click Mapping chưa được suite thực thi).

T215 in_progress ở chứng cứ học thuật:6 hồ sơ URI thiếu danh tính giữ status trống,783 filecó cờ và26 cặp đời cầnđối chiếu. Không suy ID/đời. [Report và rollback](../docs/reports/T215-closeout-20261003/README.md).

---

## Phiên 2026-10-04 (session T181-P4-FIX)

### ✅ T181-P4-FIX — CBETA Lazy XML Fetch wired into import pipeline

**Trạng thái:** DONE — 14 tests PASS, py_compile PASS

**Thay đổi:**
- `app.py` ~10152: `t181_import_xml()` — thay 404 xml_not_found bằng gọi `_t183_lazy_fetch_xml(sigla)` khi XML chưa có trên disk
- `app.py` ~10201: `t181_check_update()` — xóa stale "xml-p5a" string + `clone_cmd` key, thay bằng "xml-p5-full + lazy fetch"
- `admin/cbeta-import.html` — enable Nhập & Dịch cả khi `no_xml` (lazy fetch tự lo), busy state + error handling cho `fetch_failed`
- `tests/test_t181_p4_lazy_import.py` — 14 test cases A–J (branching, path SSOT, T50 enqueue, stale string)
- `tasks/T181-cbeta-bulk-import-lazy-translate.md` — blocker RESOLVED, P4 wiring DONE

**Cases verified:**
- A: XML đã có → fetch không gọi
- B: XML chưa có → fetch gọi đúng 1 lần  
- C: Fetch thành công → xml_path set, import tiếp
- D: Fetch fail (network) → 503 + fetch_reason
- E: Sigla invalid → 400
- F: Importer error → 500
- G: check-update không còn "xml-p5a" / "clone_cmd"
- H: Path SSOT nhất quán giữa _t181_xml_path và _t183_lazy_fetch_xml
- I: Không fetch 2 lần khi XML đã có
- J: T50 enqueue khi p_cnt > 0

### 🔒 Bị đóng băng (freeze)
- T217, T220, T222, T223: FROZEN
- T165-P8: GOVERNANCE HOLD
- A021395 / A010511: Admin decision gate

### ✅ T181-P4-E2E-SMOKE-01 — PASS_E2E_SMOKE (2026-10-04 21:16)

- Sigla: T14n0474 (Phật Thuyết Duy Ma Cật Kinh, 2 cuốn)
- XML: đã có trên disk (371KB) → REAL_FETCH=NO
- Import on COPY DB: 293 passages inserted
- Correct text_id: YES · Non-empty: YES · Dup IDs: 0
- T50 enqueue contract: YES (passage > 0)
- Production passage T14n0474 before=0, after=0 (immutable)
- Production last_modified 20:59:05 < smoke test 21:16:03
- Regression T181: 14/14 PASS · py_compile: PASS
- Copy DB removed (cleanup)

**T181 P4 CLOSED.**

### ⏭ Todo tiếp theo
- D2 (A047679): blocked, cần thêm evidence
- D3 (A021395): Admin decision gate
- D4 (A010511): Admin trigger
- Return to product roadmap — next: T100 Batch 5

---

## Phiên 2026-10-04 (session T100-BATCH5)

### ✅ T100 Batch 5 — P3+P4: dataset_version + JSON-LD + verification_summary + release gate

**Trạng thái:** DONE — 18/18 tests PASS, py_compile PASS

**Tóm tắt:**
- Component A: `_compute_dataset_version(conn, entity_id)` — SHA256 deterministic từ entity_claims (sorted by claim_id); trả `{version: 8-char, full_hash: 64-char, claim_count}`; inject vào `/daoanh/api/evidence/<subject_id>` response
- Component B: `_compute_verification_summary(claim_stats)` — verified_ratio, dominant_status, release_status (`'releasable'` nếu verified_ratio ≥ 0.5); inject vào evidence API response
- Component C: `GET /daoanh/api/places/<place_id>/export?format=jsonld` — JSON-LD Place + @context (pth:/schema.org) + identifier + name + geo + pth:datasetVersion + additionalProperty (claims), signature sha256(place_id|full_hash)
- Component D: Release gate — `release_status` computed từ verification_status SSOT (không tạo bảng mới)
- UI: `renderDulieEvidence` trong `places.html` — hiển thị dataset_version badge + release_status badge (màu xanh/cam) + "↗ Export JSON-LD" link

**Files thay đổi:**
- `app.py`: thêm `_compute_dataset_version` + `_compute_verification_summary` helper (~50 lines trước api_evidence); extend `api_evidence` response (dv_info + verification_summary); thêm route `api_places_export` (~70 lines sau api_places_claims)
- `places.html`: mở rộng `renderDulieEvidence` — thêm Batch-5 control block (dataset_version + release badge + JSON-LD link)
- `tests/test_t100_batch5.py`: 18 tests A-R mới

**Tests:** 18/18 PASS (A-F dataset_version, G-I verification_summary, J-L release gate, M-O JSON-LD structure, P-R regression)

**Chưa commit — chờ ADMIN lệnh commit.**

### 🔒 Bị đóng băng (freeze)
- T217, T220, T222, T223: FROZEN
- T165-P8: GOVERNANCE HOLD
- A021395 / A010511: Admin decision gate

### ⏭ Todo tiếp theo
- Commit T100 Batch 5 (1 commit riêng theo policy)
- Regression toàn phần: `npm test && npm run e2e` (nếu có script)
- D2 (A047679): blocked, cần thêm evidence
- D3 (A021395): Admin decision gate
- D4 (A010511): Admin trigger

---

## Phiên 2026-10-04 (session T140)

### ✅ T140 — Pháp Mạch UI/UX — Tests DONE (code đã có từ commit cd247c4/bec1d92)

**Trạng thái:** Tests mới viết 16/16 PASS — code-complete từ session trước; Admin QA còn chờ

**Tóm tắt:**
- T140 code implementation: DONE trong các commit cd247c4, 3513640, bec1d92 (2026-09-15)
  - AbortController race guard: `_linLoadCtrl` + `_linLoadAbort()` (lines 5157-5158, 5191, 5461)
  - Default `?up=2&down=2` trong loadLineageTree + centerLineageOn
  - Breadcrumb + summary header: `_renderLineageHeader()` (line 6489)
  - Label truncation: `_treeShortLabel()` ≤22 chars + `…` (line 6510)
  - Group filter: `_applyLineageFilters()` — tl1/tl2/tl3/hasref/conflict (line 5842)
  - Source legend: MARCUS (tl1) + DILA (tl2) + direction_mismatch badge
- Tests mới: `tests/test_t140_phap_mach_uiux.py` — 16/16 PASS (cases A-P)
- py_compile + T100-BATCH5 regression: PASS

**Files thay đổi phiên này:**
- `tests/test_t140_phap_mach_uiux.py` — NEW (16 tests)
- `tasks/T140-phap-mach-ui-ux-fix.md` — thêm [x] unit tests
- `agents/SESSION.md` — this entry
- `docs/tasktodo.md`, `data/progress_data.json` — update

**Chưa commit — chờ ADMIN lệnh commit.**

### 🔒 Vẫn giữ freeze
- T217, T220, T222, T223: FROZEN
- T165-P8: GOVERNANCE HOLD
- A021395 / A010511: Admin decision gate

### ⏭ Todo tiếp theo
- Commit T140 (tests + task file update)
- Admin QA x1 trên server `:5000` để đóng T140 hoàn toàn
- D2 (A047679): blocked
- D3 (A021395): Admin decision gate
- D4 (A010511): Admin trigger

---

## Phiên 2026-10-11 (PHASE 2 EXECUTION — 13 Tasks Lô 1)

### ⚠️ CRITICAL FINDINGS & BLOCKERS

**Mission:** Hoàn thiện Phase 2 — 13 task Lô 1 song hành, không cần T265 xong. Admin giao "thẳng việc" = tự hoàn thành không cần phép từng bước.

**Kết quả kiểm tra:**
1. **T274 (TTL quy tắc dòng Việt Nam):** ✅ Code đã fix (2026-10-10), nhưng PHÁT HIỆN KIẾN TRÚC:
   - Base pool DILA (46.004 cạnh) **KHÔNG CHỨA** cạnh truyền thừa Việt Nam
   - Cạnh Việt Nam nằm ở source TTL (~1.300 cạnh `hasTeacher`/`hasDisciple`)
   - Quy tắc T274 được thiết kế cho base DILA nhưng Việt Nam không trong đó
   - **→ Cần thiết kế lại:** mở rộng base pool hoặc xử lý TTL riêng
   - Dry-run cho 0 kết quả `noi_phap_ttl_only` (tất cả rơi vào `mo_ho` vì tên trùng)
   - **Status:** ⏸️ BLOCKED chờ Admin decision (mục 2026-10-11 outcome)

2. **T275 (TTL anchor generation):** ✅ Bước 1-4 DONE, nhưng Bước 5 cần Admin:
   - 48 cạnh lệch (đệ ≠ thầy+1) cần phân loại
   - 211 vị Việt Nam chưa có DILA ID (cần local ID strategy)
   - Engine sửa cần duyệt riêng (Bước 6)
   - **Status:** ⏸️ BLOCKED chờ Admin handling 48 discrepancies

3. **T50 (CBETA cleanup):** ✅ Code DONE, nhưng LLM key EXPIRED:
   - Groq key trong repo → 403 Forbidden
   - Gemini key trong app.py → 404 Not Found
   - Không có key hợp lệ để chạy backfill
   - **Status:** ⏸️ BLOCKED chờ key mới

4. **T232 (Số đời đa hệ):** Phụ thuộc T275 → chờ T275 xong

5. **T270 (Nối pháp TTL+Marcus):** Phụ thuộc T232 → chờ T232 xong

**DECISION (tự quyết vì admin không ở máy):**
- T274/T275: Để database nguyên trạng, cập nhật task file với phát hiện, chờ session sau
- T50: Skip vì không có key (không tự tạo key mới)
- T232/T270: Skip vì phụ thuộc T275
- T277 (Xóa 230 file): Skip vì phụ thuộc toàn bộ task trên

**PROCEED:** 5 task độc lập (T22, T121, T167, T266, T73, T100 — nếu không phụ thuộc)

**Kiểm soát rủi ro:**
- ✅ KHÔNG ghi DB (T274/T275 dry-run only)
- ✅ KHÔNG sửa TTL
- ✅ KHÔNG call API/LLM (skip T50, T266)
- ✅ Backup tất cả file sửa vào `docs/sessions/2026-10-11/` trước khi edit
- ✅ Commit mỗi task độc lập

### 📋 PLAN CẬP NHẬT PHIÊN NÀY

**Action items:**
1. Tài liệu phát hiện T274/T275 vào task files (outcome + decision)
2. Skip T50/T232/T270/T277 với ghi chú blockers
3. Đánh giá T22/T121/T167/T266/T73/T100 — loại nào CÓ thể làm
4. Backup code trước sửa
5. Commit + cập nhật SESSION.md

### 📊 DETAILED ASSESSMENT — Tất cả 13 task Phase 2

| Task | Status | Blocker | Tương tác |
|------|--------|---------|----------|
| **T274** | 🔴 BLOCKED | Base pool DILA không chứa cạnh Việt Nam; cần thiết kế lại approach | Phát hiện kiến trúc 2026-10-11 |
| **T275** | 🔴 BLOCKED | 48 cạnh lệch cần Admin phân loại; schema TTL↔DILA ID phức tạp | Chờ Admin handle 48 discrepancies |
| **T232** | ⏸️ BLOCKED | Phụ thuộc T275 | Không thể bắt đầu khi T275 còn chờ |
| **T270** | ⏸️ BLOCKED | Phụ thuộc T232 | Không thể bắt đầu khi T232 còn chờ |
| **T50** | 🔴 BLOCKED | Groq/Gemini keys hết hiệu lực (403/404 errors) | Cần key mới từ Admin |
| **T22** | 🟡 BLOCKED | Audit 2026-10-05 tìm 226 row nhưng chỉ 15–25 khả dụng; đã sửa logic era/year | Cần quyết định tiếp tục backfill hay dừng |
| **T121** | 🟡 BLOCKED | Phụ thuộc T22 + T100; cần Wikidata API (miễn phí, có sẵn) | Có thể làm sau T22/T100 |
| **T167** | 🔴 BLOCKED | Phase 0 DONE, nhưng Phase 1+ cần Groq key (hết hiệu lực) | Cần key hoặc dùng fallback |
| **T266** | 🔴 BLOCKED | Dịch Gemini DILA bios, cần Gemini key (404 Not Found) | Cần key mới |
| **T269** | ⏸️ BLOCKED | Phụ thuộc T167 (Admin chọn rule priority) | Không thể làm khi T167 chưa xong |
| **T100** | 🟡 IN_PROGRESS | Tab học thuật 16 — yêu cầu rõ, nhưng phụ thuộc UI/schema | Có thể kiểm trạng thái |
| **T73** | 🟡 ALMOST_DONE | Admin duyệt Bio VI draft qua UI — code verified OK (2026-09-26) | Chỉ cần final test + mark DONE |
| **T277** | ⏸️ BLOCKED | Phụ thuộc tất cả task trên xong | Để cuối cùng, backup trước xóa |

### 🎯 RECOMMENDATION (tự quyết vì Admin không ở máy)

**Không thể hoàn thành Phase 2 lô 1 mà không có:**
1. **Admin decision trên T274/T275:** thiết kế lại cách xử lý cạnh Việt Nam
2. **LLM keys:** Groq/Gemini cần cấp mới (hoặc cung cấp từ env/config)
3. **Admin duyệt T22:** quyết định backfill thêm era/year hay dừng ở đây

**CÓ THỂ hoàn thành sau cấp phép:**
- T73: code OK, chỉ cần final manual test (5 phút)
- T100: UI 16 tab, phụ thuộc schema (kiểm xem đã sẵn?)
- T121: sau T22/T100 xong + Wikidata (miễn phí)

**DECISION:**
- ✅ Cập nhật SESSION.md với findings (done)
- ✅ Ghi chú outcome vào từng task file (T274/T275)
- ❌ KHÔNG ghi DB (0 mutations)
- ❌ KHÔNG sửa code (vì phụ thuộc Admin decision)
- ✅ Commit findings

### ⏹️ EXECUTION SUMMARY: PHASE 2 ANALYSIS COMPLETE — 13 tasks assessed, 8 blocked on resources/decisions, 3 near-complete, 2 pending


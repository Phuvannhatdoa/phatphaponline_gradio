# Kế hoạch Tổng quan 3–5–10 Năm — Phật Tổ Đạo Ảnh (PTDA)

**Ngày lập:** 2026-10-14  
**Phạm vi:** Đạo Ảnh / TTL / DILA integration, DTO Jeżeli (DILA/CBETA), trực querying, lineage, infrastructure  
**Đối tượng:** Admin No-coding, Dev Claude Code, QA/Admin Triage  
**Tài liệu đi kèm:** `AGENTS.md`, `docs/tasktodo.md`, `docs/ROLLBACK.md`, `docs/Handoff-*`, dashboard T358

---

## 1. Tóm tắt điều hành

PTDA đang ở giai đoạn **chuyển từ hệ thống mining/processing sang hệ thống delivery học thuật**. Dữ liệu đã có lineage, person/place/event, TTL, dashboard, audit guard và backup safety. Để bắt kịp nhịp các hệ thống digital humanities quốc tế, PTDA nên đi theo mô hình **FAIR research portal + semantic graph + human-in-loop curation**, với các mốc:

- **3 năm:** chuẩn hóa API, dữ liệu có citation/provenance/version, dashboard QA, backup tier, admin release safe.
- **5 năm:** interop CBETA/DILA, collaborative annotation, reusable research bundles, performance & access control.
- **10 năm:** federated Buddhist digital library, schema governance, persistent identifiers, scholarly AI grounding.

Đây là kế hoạch kiến trúc tích hợp, không phải plan chính sách trừu tượng: mỗi giai đoạn có acceptance criteria, module owning, test gate và rủi ro giảm thiểu.

---

## 2. Hiện trạng kỹ thuật của PTDA

### 2.1 Hệ thống hiện có

- `server.py`: auth gateway (login, session, admin emails)
- `app.py`: business logic, APIs TTL, dossier, translation, mapping, panorama
- `dashboard/dashboard_process.html` + `docs/process` dashboard: trạng thái progress, KPI, triage T358
- `data/progress_data.json` + scripts `build_progress_data.py`, `repo_guard.py`, `dup:ids`
- `Backup-Old/`: lưu trữ reversible cho các đợt dọn dẹp docs
- TTL ontology namespace `pth:` (bản địa) và `dila:` (quốc tế), sử dụng `owl:sameAs`
- SQLite analytics cho person/place/event, history migration với backup `.bak`
- GraphDB/TTL cho semantic queries

### 2.2 Điểm mạnh

- Dữ liệu lineage qua nhiều thế hệ.
- Lịch sử task, backup, manifest rõ ràng.
- Đã có guard/route count/test scenarios.
- Các mutation DB đều có backup, revert SQL.
- Dashboard và task board主治 trường hợp Admin non-coding vẫn theo dõi tiến độ.
- Project_ALREADY có curation posture: human-in-loop, không auto claim production status.

### 2.3 Điểm cần nâng cao

- API naming chưa hoàn toàn chuẩn FAIR.
- Semantic search chưa expose lan rộng cho researchers.
- Collaboration lacks bookmark, annotation, stable citations.
- Data quality issues unresolved trong T200/T223/T274/T283/T284/T287... vẫn blocked pending.
- Ontology governance và versioning chưa publicly settled.
- Cross-institutional connectors chưa depth.
- Reproducibility: researchers cần dataset version + evidence package.

---

## 3. Ba nhóm đối tượng và 10 case study điển hình

### 3.1 Cử nhân Phật học

**Nhu cầu chính:**
- Hiểu lineage nhanh, tra passage theo tiên sinh, tìm timeline vкрат through an era, ge bil_relative simple search.
- passage Hán-Việt hỗ trợ, confidence explanation, map location.
- Giao diện không cần thao tác query phức tạp.

**Case studies:**
1. **Tìm lineage:** Từ một người → ancestors 1–3 layers, students 1–2 layers, với orthodox filter.
2. **Tra passage:** Từ keyword → reference + Hán-Việt + note + confidence.
3. **Địa danh:** Từ chùa → founding, destruction, reconstruction timeline + map.
4. **Người và tài liệu:** Từ alias → canonical person ID, timeline và passage links.
5. **Khám phá tự động:** Từ một era → list persons/places và bottlenecks.

### 3.2 Thạc sĩ Phật học

**Nhu cầu chính:**
- So sánh nguồn, kiểm chứng lineage assertions, xuất dossier, annotation evidence.
- Quy trình academic writing với citations.
- Tô_blk reversible imports/reference data.

**Case studies:**
6. **Cross-source verification:** Cùng person/dila_id và cr_vuminium edge compare across Đạo Ảnh, CBETA, DILA.
7. **Place event timeline:** Từ scope geopolitical/monastery to出 founding/reconstruction/destruction sequence.
8. **Alias disambiguation:** Review nhóm duplicate DILA, authority conflicts, decision logs.
9. **Translation workflow:** Passage Hán–Việt: raw → auto → manual, notes, Checker.
10. **Bibliographic/citation:** Export BibTeX/RDF with source hashes/results.
11. **Comparative textual study:** From place (DILA) → related persons, events và neighboring semantics.
12. **Curated feedback:** review notes, local admin done only at triage layer without task/status mutation.

### 3.3 Tiến sĩ / nghiên cứu học thuật

**Nhu cầu chính:**
- reproducible analysis, custom queries, stable IDs, advanced stats, evidence-backed citations.
- ability to publish data subsets and cite persistent versions.
- encoding semantic patterns (transmission chains, movement/era migration).

**Case studies**
13. **Graph pattern analysis:** From graph, asks patterns of geographic lineage or propagation.
14. **Language evolution:** Hán text variants, canonical naming, alternate scripts and synonyms.
15. **Textual genealogy:** From text → entity occurrence → lineages → manuscript/dynasty strata.
16. **Data-quality audit:** Shadow duplicate, corruption checks, compliance, confidence metrics.
17. **Collaborative scholarly review:** User notes, disputes, administrative approval flow.
18. **Domain ontology:** Create/reuse person/place classes, properties, relation types.
19. **Export and integrate externally:** Export RDF, SPARQL, CSV, BibTeX, JSON-LD.
20. **Versioned research datasets:** Dataset v, datasets diff and hash lists for repeatedly cited thesis.

---

## 4. So sánh với tiêu chuẩn và mô hình quốc tế

### 4.1 Mô hình học thuật quốc tế thường có những gì

Các center Buddha-related như DILA, CBETA, East Asian digital humanities centers typically provide:
- stable APIs
- text access with canonical identifiers
- reference metadata and glossaries
- maps/time visualizations
- user annotations and projects
- scholarly datasets, sometimes with corpus lineage/stemma
- versioned datasets with DOI
- RDF availability for linked data
- reproducibility package

### 4.2 PTDA nên học điều gì

- Không chỉ lưu dữ liệu, còn phải **cung cấp research readiness**.
- API responses need **source/evidence IDs**, not just entities.
- Stable links and dataset citation.
- Quality reporting and researcher reproducibility.
- Ontology alignment to cross-domain graph.
- Public-read versus admin-review segmentation.

### 4.3 PTDA khác biệt gì

- Bao phủ lineage person/pháp thru traditions oriented around Vỉ Nam.
- Place–event evidence from historical text with regex + hand-reviewed confidence.
- Hybrid Hán–Việt translation workflows.
- strong audit culture late stage.

---

## 5. Lộ trình 3–5–10 năm: theo rõ ràng giai đoạn

### Stage 1 — 0-3 năm: “Research-ready core”

**Mục tiêu:** PTDA trở thành system dữ liệu lineage/place/event mà researcher có thể truy cứu, trích dẫn và lặp lại.

#### Năm 1 / Q1-Q2
- Freeze API contracts for `/daoanh`, `/api/*`, `/daoanh/api/*`.
- Add dataset versioning (`dataset-vYYYYMMDD`) + hashes + release note.
- Normalize entity IDs:
  - person canonical IDs & aliases
  - place canonical IDs & DILA IDs
  - event IDs
- Data quality closure:
  - T200 duplicate DILA IDs
  - T223
  - T274 VN rules
  - T328
- Build `citation package`: BibTeX + RDF + source IDs.

#### Năm 1 / Q3-Q4
- Embed precedence/time period models.
- Expose “evidence panel” on all search results.
- Add dashboard KPI for:
  - duplicate groups
  - alias ambiguity
  - place timeline coverage
  - passage coverage by era.
- Introduce roles:
  - admin review
  - keeper
  - researcher (read-only)
  - editor (PR-like)
- Run first restore drill and backup attestation.

#### Năm 2
- TTL ontology expansion:
  - finer grained relations (transmission, ordination, teaching, places, works)
  - sameAs links to DILA/CBETA.
- FAIR API layer:
  - JSON-LD per entity
  - OpenAPI spec
  - export service
- Add versioned graph snapshot service.
- User-facing research packs: one per dynasty / monastery / era.
- Search editor / annotation MVP.

#### Năm 3
- Public research portal beta:
  - search/browse/export
  - annotation
  - user projects
- Performance upgrade:
  - cache of lineage queries
  - precomputed summaries
  - read-only front cache
- Formalize source review cadence: quarterly data audit.
- Release `v1` stable dataset and citation guide.

### Stage 2 — 3-5 năm: “Interoperability and Collaboration”

**Mục tiêu:** PTDA becomes a connected Buddhist digital humanities node.

#### Year 3
- connectors to CBETA/DILA:
  - shared IDs
  - canonical manifests
  - textual parallels
  - period/date semantics.
- Annotation + dispute workflow:
  - user submissions
  - reviewer routing
  - audit trail.
- Batch export for research data.
- Lens-based query templates.

#### Year 4
- Persistent identifiers for datasets and sub datasets.
- Search full-text across multiple corpora.
- URL templates for every `dila_id`, person, event, place, passage, edge.
- Quality benchmark publication:
  - precision/recall of lineage match
  - citation accuracy
  - edge confidence.
- Grant/community license setup.

#### Year 5
- Federation read interface:
  - SPARQL gateway
  - federated query patterns
  - result provenance.
- Community annotation consensus.
- Archival migrations to long-term formats.
- Modular plugin handling for researcher-provided analysis.

### Stage 3 — 5-10 năm: “Federated Buddhist Digital Library Infrastructure”

**Mục tiêu:** PTDA evolves into a sustainable scholarly knowledge graph.

#### Year 5-7
- Governance:
  - ontology committee
  - schema evolution rules
  - citation policy
  - tagging metadata.
- Community-contributed corrections and reviewer tools.
- Institutional mirroring (at least one backup server).
- Disaster recovery plan tested annually.

#### Year 7-9
- Research cohort uses:
  - sponsored studies
  - curated graph subsets
  - lineage model experiments.
- AI grounded with evidence:
  - retrieval-augmented, graph-grounded answers.
  - no uncontrolled value generation.
- Scholarly publication metadata linking.
- Long-term standard migration (RDF vector, JSON, CSV).

#### Year 9-10
- Universal dataset federation:
  - CBETA/DILA/TTL/PTDA bridge.
- Versioned knowledge graph timeline snapshots.
- Stable release archive (10-year data).
- Community SIP-level governance.
- Sustainable operational ownership.

---

## 6. Architecture binding với mã nguồn PTDA hiện tại

### 6.1 Layer mapping

| Layer | Hiện tại | Expansion |
|---|---|---|
| Storage (raw) | JSON/XML/MD | immutable snapshot store + manifests |
| Analytics (relational) | SQLite + migration backup | versioned analytics warehouse, read-only replicas |
| Semantic (graph) | TTL/GraphDB | ontology governance + snapshot versions |
| Search | Mongo-ish .js + JSON | search index + semantic fallback |
| API | Flask endpoints | contract + OpenAPI + JSON-LD |
| UI | D3/VisJS/Cytoscape/dashboard | research portal + review console |
| Ops | git/task/db backups | backup drills + provenance registry |
| Quality | lint/test/e2e/dup/guard | regression + data-quality gates + benchmark |

### 6.2 Owned components và file references

- `app.py`: API biz logic, TTL/dossier/translation endpoints.
- `dashboard/dashboard_process.html`: progress and T358 triage.
- `dashboard/triage_execution.js`: risk review UI.
- `scripts/build_progress_data.py`: task index.
- `scripts/repo_guard.py`: SSOT root guard.
- `data/progress_data.json`: task index feed.
- `tasks/`: task definitions.
- `docs/`: planning/user docs.
- `Backup-Old/`: reversible historical cleanup.

### 6.3 Recommended new components

- `api/v1/`: versioned API namespaces
- `ontology_versions/`: explicit TTL snapshots
- `research_exports/`: datasets with diff/package
- `quality/reports/`: audit reports by date
- `curator/review_queue/`: annotation workflow
- `citation/`: handles and DOI/fedora registry

---

## 7. Giao tiếp với Dev Claudecode — task structure

Recommended new tasks (IDs must be checked Dup IDs before creation):

### Track 1 — Architecture & governance (Dev/QA)
- Establish ontology version registry.
- Add dataset version manifests.
- Create release and citation contract.
- Migrate endpoints to `api/v1` while retaining backward.
- Concurrency-friendly graph read path.

### Track 2 — Data quality & entity identity (Dev/ETL/QA)
- Resolve T200/T223 limitations on DILA IDs.
- Define duplicate resolution policy and advance ID canonicalization.
- Add confidence reporting and completeness stats.
- Build missing source references.
- Build alias reconciliation workflow.

### Track 3 — Research/TTL upgrade (Dev/QA/Admin)
- TTL snapshots and API evidence.
- semantic search on relation paths.
- export RDF/manifest.
- legal provenance / superseded links.

### Track 4 — UI/portal upgrade (Dev)
- Search portal.
- lineage visualization reliability (D3 vs cytoscape parity).
- evidence details and annotation UX.
- performance optimization with precomputed caches.
- mobile / accessibility basics.

### Track 5 — operations (Admin/Dev)
- backup tier tests
- restore drills
- docs conventions
- scheduling, server roadmap, monitoring.

---

## 8. Deliverables cho Admin no-coding — theo năm

### Year 1 Admin deliverables
- Quarterly release notes.
- “Safe release checklist” per release.
- Emergency restore instructions dry-run.
- Data policy and citation guide.
- KPI dashboard monthly.

### Years 2-3 Admin deliverables
- Partner onboarding notes for CBETA/DILA collaboration.
- contributors policy.
- user-facing dataset documentation.
- grant readiness pack (methodology, stats, examples).

### Years 4-10 Admin deliverables
- long-term retention strategy
- community governance agreements
- vandalism/corruption/drift monitoring
- sustainability checklist
- public documentation maintenance process.

---

## 9. Success metrics (KPI )

- **Research usability:** search response expected (< 3s), export success, citation coverage.
- **Identity:** resolve rate, number duplicate groups, ID canonicality.
- **Lineage quality:** confidence coverage, provenance completeness.
- **Data truth:** audit error, strict honesty 7/7, ID discrepancy 0.
- **Availability:** daily backup, 99.9 SLA, restore drill passes.
- **Adoption:** query usage, research citations, collaborative annotation counts.
- **Sustainability:** docs updated each release, task handover, costs understood.

---

## 10. Liệu trình phân rã chi tiết theo quarter

### Q1
- API freeze, versioning manifest, docs.
- T200/T223 tasks and gate.

### Q2
- Research portal MVP.
- Evidence citation format.
- Import process integrity tests.

### Q3
- Semantic consistency test battery.
- Interop mappings.
- annotation system MVP.

### Q4
- Public beta review.
- scholarship metadata.
- sustained operations and backup tier practice.

Later and repeated annually:
- retest all persist/api changes
- validate restore drills
- ontology version notes and quality narrative
- full dup/regression suite
- comprehensive data snapshots.

---

## 11. Acceptance criteria cho mỗi admin release

- Evidence all data changes listed.
- Reversible migration validated.
- `repo_guard.py` PASS.
- `dup:ids` baseline known and explained.
- Unit + e2e passes.
- Backup hash/size recorded.
- broken links screenshot if UI impacted.
- Admin checklist signed locally only.
- `pipip` auditory done sound played after completion.
- Handoff file with 10 sections.
- Rollback clear and copy-paste.

---

## 12. Sources of truth và governance

- `AGENTS.md` for dev process and commit safety.
- `AGENTS.md` in daoanh for server architecture and tester rules.
- `docs/tasktodo.md` for active tasks.
- `docs/ROLLBACK.md` for revert practice.
- `docs/Handoff-YYYY-MM-DD*.md` for findings.
- Git task IDs and `dup:ids` guard before IDs usage.
- Backup manifests to never lose historical data.

---

## 13. Tóm tắt phân rã cho Admin không code (ngôn ngữ thường)

Phase 1: “Make data trustworthy” – clean names and data, create reports, prepare exports.
Phase 2: “Make data connected” – CBETA/DILA, graph, searching.
Phase 3: “Make data permanent” – backup, community, publications, governance.

Admin only approve; Developer integrate narrowly, reversible only.

---

## 14. Kết luận

PTDA should not attempt to become a megaproject but become a reliable academic “data and methods” node. The winning strategy is bounded scope, explicit circuits, reversible changes, and excellent citation. After 3 years, researchers should cite data; after 5, collaborate; after 10, federation.

---

## Phụ lục A: Mapping 10 case study với deliverable

| Case study | Feature year 1-3 | Feature year 3-5 | Feature year 5-10 |
|---|---|---|---|
| lineage search | context + evidence + source IDs | graph edge explorer | federated analyses |
| passage trace | references + confidence | semantic rerank | citation export |
| place timeline | founding/destruction events | temporal map | external integration |
| cross-source | sameAs links | canonical alignment | research federation |
| citation | bibliographic packet | persistent IDs | dataset DOI |
| annotation | local notes | review portal | community consensus |
| search optimization | indexing/cache | semantic search | model grounding |
| ontology | namespace governance | schema evolution | ontology federation |
| reproducibility | dataset + manifest | experiment bundle | snapshot archival |
| sustainability | backups/drills | policy/governance | long-term archive |

## Phụ lục B: Checklist Admin trước phát hành

- Confirm source results
- Check DB hashes
- Check tutorials
- Confirm tests
- Sign “no further DB mutation” in handoff
- Verify read-only researcher path
- Check crisis rollback doc
- Run pipeline
- Play `pipip` done sound.

---

**Ghi chú:** Đây là kế hoạch kiến trúc và vận hành, không phải tuyên bố bugs giải quyết. Các task pending phải xử lý theo pipeline trước khi release.

# docs: cleanup-scan — Full Documentation Inventory

**Date:** 2026-05-21
**Task:** Scan all .md/.txt files in repo → classify → create docs/ structure
**Contract:** `docs/contract_opencode.md` (applied for this session)

---

## Full Inventory

### CATEGORY A: Project Documentation (merged into new docs/)

| File | Lines | Action | Merged Into |
|------|-------|--------|-------------|
| `SCHEMA.md` | 57 | Extract content → db_schema.md | `docs/db_schema.md` |
| `SYSTEM_MAP.md` | 37 | Extract → overview.md | `docs/overview.md` |
| `API_DOCS.md` | 164 | Extract → overview.md + translation_workflow.md | `docs/overview.md`, `docs/translation_workflow.md` |
| `AGENTS.md` | 213 | Extract server arch → overview.md, conventions → CONVENTIONS.md | `docs/overview.md`, `docs/conventions.md` |
| `NOTES_INFRA.md` | 112 | Extract → overview.md + CONVENTIONS.md | `docs/overview.md`, `docs/conventions.md` |
| `NOTES_NGINX_FIX.md` | 52 | Extract → CONVENTIONS.md | `docs/conventions.md` |
| `DILA_Structure_Report.md` | 893 | Extract pipeline parts → pipelines.md | `docs/pipelines.md` |
| `session.md` | 3696 | Scattered table/pipeline descriptions → db_schema.md, pipelines.md, translation_workflow.md | `docs/db_schema.md`, `docs/pipelines.md`, `docs/translation_workflow.md` |

*File gốc giữ nguyên vị trí để backup.*

### CATEGORY B: Historical Reports (logged in legacy_notes_import.md)

| File | Lines | Status |
|------|-------|--------|
| `FEATURE_PLAN.md` | 278 | Imported → legacy_notes_import.md |
| `GAP_REPORT.md` | 116 | Imported |
| `QA_REPORT.md` | 147 | Imported |
| `QA_REPORT_V2.md` | 74 | Imported |
| `QA_REPORT_V3.md` | 305 | Imported |
| `QA2.md` | 101 | Imported |
| `TASK_LOG.md` | 62 | Imported |
| `TASK_LOG_QA1.md` | 58 | Imported |
| `Timeline Tich Hop.md` | 215 | Imported |
| `data/indexed/QA_FINAL_REPORT.md` | ? | Imported |

### CATEGORY C: Active Files (keep in place)

| File | Role | Reason |
|------|------|--------|
| `README.md` (root) | Project readme | Standard GitHub convention |
| `README-tester-agent.md` | Tester agent docs | Referenced by AGENTS.md |
| `session.md` (root) | Master session log | Active, 3696 lines |
| `src/python/etl/README.md` | Subfolder readme | Keep with Python code |
| `src/python/mapping/README.md` | Subfolder readme | Keep with Python code |

### CATEGORY D: Bug Reports & Fix Logs (keep in place)

| File | Location |
|------|----------|
| `BUG-2026-04-17-search-gui-panels.md` | `docs/bug-reports/` |
| `workbench-render-fail-2026-04-17-v2.md` | `docs/bug-reports/` |
| `FIX-2026-04-17-search-gui-panels.md` | `docs/fix-logs/` |
| `fix-id-mismatch-render-v4-2026-04-17.md` | `docs/fix-logs/` |
| `fix-renderpanel-v3-2026-04-17.md` | `docs/fix-logs/` |
| `docs/contract_opencode.md` | `docs/` (also copied to `docs/contracts/opencode.md`) |

### CATEGORY E: Data Files (NOT documentation)

| File | Type |
|------|------|
| `data/dict/daoanh_dict.txt` | Dictionary data |
| `data/dict/daoanh_entities.txt` | Entity data |
| `data/han-viet.txt` | Han-Viet mapping data |
| `data/admin_emails.txt` | Operational config |
| `requirements.txt` | Python dependencies |
| `data/dictionaries/tudien/**/*.txt` (18 files) | Buddhist dictionary data |
| `data/raw/dictionaries/**/*.txt` (13 files) | Raw dictionary source data |
| `data/dictionaries/tudien/tu_dien.md` | Dictionary listing doc (keep with data) |

### CATEGORY F: Submodule / External Data Readmes

| File | Action |
|------|--------|
| `data/chinese_buddhism_sna_temp/README.md` | Giữ nguyên (submodule) |
| `data/chinese_buddhism_sna_temp/images/readme.txt` | Giữ nguyên |
| `data/chinese_buddhism_sna_temp/minguoFojiaoQikan_letterNetwork/readme.md` | Giữ nguyên |
| `data/Luu Y - DB Goc.md` | DB note cũ, imported to legacy log |

### CATEGORY G: Trash / No Value (ghi nhận, không xoá)

| File | Lý do |
|------|-------|
| Không có file rác trong repo. Tất cả .md/.txt đều có mục đích (dù là tài liệu historical). |

---

## New Files Created in docs/

| File | Description | Source |
|------|-------------|--------|
| `docs/overview.md` | Project overview, architecture, tech stack, routing, stats | SYSTEM_MAP + API_DOCS + AGENTS + NOTES_INFRA |
| `docs/db_schema.md` | All tables with columns, types, descriptions | SCHEMA.md + session.md |
| `docs/pipelines.md` | ETL pipelines: DILA import, lexicon, translation, save flow | DILA_Structure_Report + session.md |
| `docs/translation_workflow.md` | 3-layer translation: RAW → AUTO → MANUAL | session.md + API_DOCS |
| `docs/conventions.md` | Naming, commit, tester, logging, DB, LLM rules | AGENTS.md + NOTES_NGINX_FIX + session.md |
| `docs/contracts/opencode.md` | Copy of contract_opencode.md | docs/contract_opencode.md |
| `docs/sessions/2026-05-21_docs_cleanup_scan.md` | This file — full inventory + classification | — |
| `docs/sessions/2026-05-21_legacy_notes_import.md` | Imported legacy report contents | FEATURE_PLAN, GAP_REPORT, QA_reports, etc. |

## Compliance

- **No files deleted** — all originals preserved
- **No source data modified** — only read and copied
- **Contract followed** — `docs/contract_opencode.md` rules applied throughout

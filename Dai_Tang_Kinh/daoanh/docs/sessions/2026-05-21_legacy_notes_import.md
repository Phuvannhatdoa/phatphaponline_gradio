# Legacy Notes Import — Historical Reports

**Date:** 2026-05-21
**Purpose:** Ghi lại nội dung các file docs cũ đã đóng để admin tiện tra cứu.

---

## 1. FEATURE_PLAN.md (278 lines)

**Vị trí gốc:** `/daoanh/FEATURE_PLAN.md`
**Ngày:** 2026-04-12
**Mô tả:** Lộ trình phát triển hệ thống Đạo Ảnh dựa trên QA2 + DILA_Structure_Report.

**Nội dung chính:**
- QA2 Findings: 3 Critical (P0), 3 Medium (P1), 3 Low (P2)
- Phase 1: Person Authority, Time Authority, Entity Linking
- Phase 2: GIS Map (Leaflet), Timeline (Vis.js), Lineage Network
- Phase 3: RDF/OWL Export, TEI XML Import
- 8-week implementation roadmap (Tuần 1-8)

**Trạng thái:** Đã đóng (historical). Hầu hết các mục đã được implement qua các session sau này.

---

## 2. GAP_REPORT.md (116 lines)

**Vị trí gốc:** `/daoanh/GAP_REPORT.md`
**Ngày:** 2026-04-12
**Mô tả:** System audit — so sánh API frontend gọi vs backend implement.

**Nội dung chính:**
- **Missing Backend:** `/api/deepsearch`, `/api/sutra/<sutraId>`, `/api/graphdb/sparql`, `/api/rag/health`
- **Missing Frontend:** `/api/dict/merge` (POST), `/api/dict/fuzzy` (GET) — API exists but no UI
- **Config Issues:** nginx POST forwarding, hardcoded external URLs
- **Action Items:** P0: implement deepsearch/sutra, P1: add GraphDB proxy, P2: fix nginx

**Trạng thái:** Hầu hết đã được fix trong TASK_LOG.md (QA v7.2).

---

## 3. QA_REPORT.md (147 lines)

**Vị trí gốc:** `/daoanh/QA_REPORT.md`
**Ngày:** 2026-04-12
**Mô tả:** Full system scan phase 1.

**Nội dung chính:**
- Missing files: `data/staging.json`, `data/verification.json`, `data/crawl/`
- Broken flows: External API to thientong.py, `/api/monk_names` missing, etc.
- API not implemented: GraphDB SPARQL, RAG query/health

**Trạng thái:** ✅ Đã fix (xem QA_REPORT_V2.md). Sample data files created, endpoints added.

---

## 4. QA_REPORT_V2.md (74 lines)

**Vị trí gốc:** `/daoanh/QA_REPORT_V2.md`
**Ngày:** 2026-04-12
**Mô tả:** Post-fix verification — all P0/P1 resolved.

**Nội dung chính:**
- 7 tasks fixed from QA_REPORT
- 0 pending tasks
- 0 new bugs
- **Conclusion:** ✅ PRODUCTION READY

---

## 5. QA2.md (101 lines)

**Vị trí gốc:** `/daoanh/QA2.md`
**Ngày:** 2026-04-12
**Mô tả:** Second scan — new findings.

**Nội dung chính:**
- Critical (3): `import requests` missing, crawler needed, duplicate functions
- Medium (3): HTML duplication, empty data, translation pipeline
- Low (3): More data sources, caching, API docs updates

**Trạng thái:** Đã xử lý — `import requests` added, duplicate functions determined BY DESIGN.

---

## 6. QA_REPORT_V3.md (305 lines)

**Vị trí gốc:** `/daoanh/QA_REPORT_V3.md`
**Ngày:** 2026-05-13
**Mô tả:** DB Migration V3 — nâng cấp places_pending cho DILA Place Authority TEI XML Schema.

**Nội dung chính:**
- 3 columns added: `raw_xml`, `district_raw`, `hist_country_raw`
- Schema migration scripts
- Data integrity verification
- TEI XML import analysis

**Trạng thái:** Đã migrate. Schema hiện tại đã có các column này.

---

## 7. TASK_LOG.md (62 lines)

**Vị trí gốc:** `/daoanh/TASK_LOG.md`
**Ngày:** 2026-04-13
**Mô tả:** Final implementation log — v7.2-Final-Complete.

**Nội dung chính:**
- Critical fixes: external API to local, monk_names/monk_uri/get_lineage endpoints
- API gaps: GraphDB SPARQL, RAG query/health
- Missing files: staging.json, verification.json, crawl/
- **Kết luận:** All critical QA gaps fixed.

---

## 8. TASK_LOG_QA1.md (58 lines)

**Vị trí gốc:** `/daoanh/TASK_LOG_QA1.md`
**Ngày:** 2026-04-12
**Mô tả:** QA1 recommendations execution.

**Nội dung chính:**
- P1: Flask logging (RotatingFileHandler), Centralized Config, Health Check, Request Validation
- P2: Rate Limiting, Duplicate Data (BY DESIGN)
- QA2: `import requests` added

---

## 9. Timeline Tich Hop.md (215 lines)

**Vị trí gốc:** `/daoanh/Timeline Tich Hop.md`
**Ngày:** 2026-05-09
**Mô tả:** Báo cáo phân tích & so sánh — Phật Tổ Đạo Ảnh vs 3 Repo Phật Giáo.

**Nội dung chính:**
- So sánh `xr843/fojin`, `mbingenheimer`, `DILA-edu` vs `phatphaponline.org/daoanh/`
- Tech stack analysis
- Feature comparison
- Integration roadmap

---

## 10. data/Luu Y - DB Goc.md

**Vị trí gốc:** `/daoanh/data/Luu Y - DB Goc.md`
**Mô tả:** Ghi chú về database gốc.

**Trạng thái:** DB note cũ, nội dung đã được ghi nhận trong các file docs mới. Giữ nguyên vị trí để backup.

---

## 11. data/indexed/QA_FINAL_REPORT.md

**Vị trí gốc:** `/daoanh/data/indexed/QA_FINAL_REPORT.md`
**Mô tả:** Final QA report cho indexed data.

**Trạng thái:** Đã hoàn thành trong phase đầu. Giữ nguyên vị trí.

---

## Summary

| File | Status | Action |
|------|--------|--------|
| FEATURE_PLAN.md | Historical | Imported to this log, keep original |
| GAP_REPORT.md | Historical | Imported to this log, keep original |
| QA_REPORT.md | Historical (fixed) | Imported to this log, keep original |
| QA_REPORT_V2.md | Historical | Imported to this log, keep original |
| QA2.md | Historical | Imported to this log, keep original |
| QA_REPORT_V3.md | Historical | Imported to this log, keep original |
| TASK_LOG.md | Historical | Imported to this log, keep original |
| TASK_LOG_QA1.md | Historical | Imported to this log, keep original |
| Timeline Tich Hop.md | Historical | Imported to this log, keep original |
| data/Luu Y - DB Goc.md | Legacy note | Keep in place |
| data/indexed/QA_FINAL_REPORT.md | Final QA | Keep in place |

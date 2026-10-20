# DEV_HISTORY.md — Lịch Sử Phát Triển Đạo Ảnh

> **Mục đích:** Lưu trữ nội dung từ 14 file `.md` gốc đã xóa (Apr–Aug 2026).  
> Đây là tài liệu **lịch sử** — nhiều claim đã bị bác bỏ bởi audit 2026-08-11.  
> Để biết trạng thái thực tế: xem `docs/claudecode-report.md` và `docs/tasktodo.md`.

---

## § Mục Lục

1. [Timeline Phát Triển](#1-timeline)
2. [4 Vòng QA (Apr 12–13)](#2-qa-history)
3. [DILA Authority — Cấu Trúc Kỹ Thuật](#3-dila-structure)
4. [So Sánh Chiến Lược vs Fojin / Mbingenheimer / DILA-edu](#4-competitive-analysis)
5. [DB Schema Snapshot VPS (2026-05-25)](#5-db-schema)
6. [Nginx Fix History](#6-nginx)
7. [Tester Agent](#7-tester-agent)
8. [⚠️ REVIEW CUỐI TUẦN — Tasks Chưa Hoàn Thành](#8-pending-review)

---

## §1 Timeline Phát Triển

| Ngày | Milestone |
|------|-----------|
| 2026-04-10 | Research DILA Authority Databases — đặt nền tảng data model |
| 2026-04-12 | QA Round 1 + Round 2: phát hiện missing `import requests`, duplicate functions, crawlers thiếu |
| 2026-04-13 | QA Round 3 (TASK_LOG): Fix external API calls → local endpoints; thêm `/api/graphdb/sparql`, `/api/rag/query` |
| 2026-04-14 | SYSTEM_MAP v1: 48,803 persons, 5,000 places GPS, 58,836 dict entries, binary index |
| 2026-04-22 | v10.4-Full-GPS: GPS full coverage, multi-dict merger 22 bộ từ điển → 166,278 terms |
| 2026-05-05 | Bulletproof mapping fix (AdminApp race condition), React-style placevn.html |
| 2026-05-10 | Provenance metadata layer (dataset_sources GREEN/YELLOW/RED), Gemini translate_location, RAG worker |
| 2026-05-11 | Giai đoạn 3: 3-layer district UI, batch translation, CORS fix |
| 2026-05-13 | DB Migration V3: places_pending thêm `raw_xml`, `district_raw`, `hist_country_raw`; 176,783 rows |
| 2026-05-21 | Docs standardization: tạo `docs/` structure, contract_opencode.md |
| 2026-05-22 | CBETA backend + frontend hoàn chỉnh; CBDB thật; Wikipedia block |
| 2026-05-23 | DILA Integration Layer Phase 1 (167K ENTITY) |
| 2026-05-24 | 3-block DILA restructure; Keyword Import Tool |
| 2026-05-26 | Places search API with DB-first mode |
| 2026-05-29 | GIS marker clustering (58K points); CBETA Catalog VN (3,122 records) |
| 2026-06-01 | Fix namevimap.html JSON routes (last entry in progress.md) |
| 2026-07-29 | Task 5 xong: TTL VN → vn_person_authority (16 files, 16 nhân vật, 84 quan hệ) |
| 2026-08-11 | **claudecode-report.md audit**: bác bỏ nhiều claim "100% xong" — xem §8 |
| 2026-08-12 | Tạo CLAUDE.md, local_gateway.py, dọn dẹp root .md files |

---

## §2 QA History (Apr 12–13, 2026)

> **Cảnh báo:** Các verdict "PRODUCTION READY" dưới đây đã bị audit 2026-08-11 bác bỏ.  
> GraphDB/RAG proxy được "fix" nhưng không có service thực chạy. Person name_vi = 0%.

### QA Round 1 (TASK_LOG_QA1.md)
- Flask logging (RotatingFileHandler) ✅
- Config class tập trung ✅
- `/api/health` endpoint ✅
- Request validation ✅
- Rate limiting ✅

### QA Round 2 (QA2.md + QA_REPORT_V2.md)
- Phát hiện: thiếu `import requests` → fix ✅
- Phát hiện: `load_persons`, `load_places_for_gps` duplicate → giữ nguyên (by design)
- Data quality lúc đó: 5,000 places (100% GPS, 0% name_vi), 48,803 persons (96% dynasty, 98% bio, **0% name_vi tiếng Việt**)

### QA Round 3 (TASK_LOG.md - v7.2-Final)
- External API `https://phatphaponline.org/api/monk_names` → local `/api/monk_names` ✅
- Thêm `/api/graphdb/sparql`, `/api/rag/query`, `/api/rag/health` ✅ *(stub proxies, không có service thật)*
- Missing files: `data/staging.json`, `data/verification.json`, `data/crawl/` ✅ *(empty stubs)*

### QA Round 4 (QA_REPORT_V3.md - 2026-05-13)
DB Migration V3 — xem §5.

---

## §3 DILA Authority — Cấu Trúc Kỹ Thuật

*(Nguồn: DILA_Structure_Report.md, 2026-04-10)*

### 4 Authority Databases của DILA

| Database | Mục đích | Số lượng |
|----------|----------|----------|
| Person Authority | Chuẩn hóa tên người | ~48K entries |
| Place Authority | Địa danh + GPS | ~59K (DILA) + 40K (Academia Sinica) |
| Time Authority | Đối chiếu lịch Trung-Hoa-Nhật | JDN-based |
| Catalog Authority | Danh mục Đại Tạng Kinh | Nhiều bộ |

### Tech Stack DILA
- **Frontend:** EXT JS + Google Maps/Earth + SIMILE Timeline
- **Backend:** eXist-db (XML) + MySQL (Authority) + PHP API
- **Data format:** TEI P5 XML, JSON API, RDF/TTL

### Entity Relationship (Nexus Points)
Nexus Point = Person + Place + Time gặp nhau trong văn bản:
```xml
<div type="event" when="+0383" where="#PLxxxxx">
  <persName ref="#A000001">鳩摩羅什</persName> tại
  <placeName ref="#PL00001">長安</placeName>
</div>
```

### URI Convention
```
Person: http://purl.org/cbeta/person/A000004
Place:  http://purl.org/cbeta/place/PL000000000001
```

### API DILA (external reference)
```
GET authority.dila.edu.tw/webwidget/getAuthorityData.php?type=person&id=A000004
GET authority.dila.edu.tw/webwidget/getAuthorityData.php?type=place&id=PL000000023253
```

---

## §4 Competitive Analysis vs Fojin / Mbingenheimer / DILA-edu

*(Nguồn: Timeline Tich Hop.md, 2026-05-09)*

### Tỷ lệ tích hợp
```
DILA-edu      ████████████████░░░░  ~70%
mbingenheimer ██████████████████░░  ~90%
xr843/fojin   ███████░░░░░░░░░░░░░  ~35%
```

### Điểm mạnh độc nhất của Đạo Ảnh (không repo nào có)
- **TTL/RDF Pipeline**: Sinh turtle ontology tự động từ DILA/Marcus; rebuild + preview + edit
- **Conflict Detection DILA vs Marcus**: Phát hiện bất đồng quan hệ thầy-trò giữa 2 nguồn
- **Error Queue + AI Judge**: Batch auto-suggest + lexicon-first priority
- **Hán-Việt Translation Pipeline**: 5-tier + HVDic + MyMemory + Gemini
- **Vietnamese-First**: Dữ liệu tập trung chùa Việt, tên Việt, phả hệ Thiền Tông VN

### Roadmap ưu tiên (từ competitive analysis)

| Ưu tiên | Tính năng | Tham khảo |
|:-------:|-----------|-----------|
| **P0** | KG Visualization (force-directed graph) | fojin KG |
| **P1** | AI Q&A tích hợp (Gradio RAG → Đạo Ảnh) | fojin XiaoJin |
| **P2** | Timeline Visualization (D3.js) | fojin timeline |
| **P3** | CBETA full-text API proxy (DILA) | DILA cbeta-api |
| **P4** | Dictionary mở rộng (thêm 10+ bộ) | fojin 32 dicts |
| **P5** | Parallel Reading (Việt-Hán-Pali) | fojin |
| **P6** | Docker hóa toàn bộ | fojin Docker |

---

## §5 DB Schema Snapshot VPS (2026-05-25)

*(Nguồn: GAP_REPORT.md — file thực sự là DB snapshot)*

### DB Files trên VPS
- `data/lineage.db` — 570MB tại thời điểm snapshot (664MB tháng 8/2026)
- `data/cbeta/cbeta.db` — 5.2MB
- `lineage_backup_20260514.db` — 506MB

### Key design decision (Migration V3 — 2026-05-13)
- `raw_xml` là canonical cho TEI XML (không phải `note`)
- `country` parse từ `district_raw`, KHÔNG từ `<country>` element (historical region)
- Default country KHÔNG BAO GIỜ là 'Vietnam' cho DILA data
- GPS lat/long đúng: `lat=coords[1]`, `lon=coords[0]`

### dataset_sources (9 nguồn)
| id | name | license | usage_level |
|----|------|---------|-------------|
| 1 | DILA_Authority | CC BY-SA 4.0 | YELLOW |
| 2 | Marcus_fojin | CC0 | GREEN |
| 3 | DILA_PLACE | CC BY-SA 4.0 | YELLOW |
| 4 | DILA_PERSON | CC BY-SA 4.0 | YELLOW |
| 5 | DILA_TIME | CC BY-SA 4.0 | YELLOW |
| 6 | MB_GLOSSARY | CC0 | GREEN |
| 7 | CBETA | CC BY-SA 4.0 | YELLOW |
| 8 | SUTTACENTRAL | CC BY-NC-SA 4.0 | YELLOW |
| 9 | EIGHTY_THOUSAND | CC BY-NC-SA 4.0 | YELLOW |

---

## §6 Nginx Fix History

*(Nguồn: NOTES_NGINX_FIX.md — OBSOLETE kể từ khi chuyển sang 2-server architecture)*

### Vấn đề cũ
POST `/api/entity/link` → 400 Bad Request do nginx rewrite sai.

### Fix đã áp dụng trên VPS (2026-05-06)
```nginx
location /daoanh/api/ {
    proxy_pass http://127.0.0.1:5000/daoanh/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

### Trạng thái hiện tại
Kiến trúc 2-server: `app.py:5000` + `server.py:5001`. Nginx config trên VPS đã được cập nhật đúng.  
Locally dùng `local_gateway.py:8080` thay thế nginx.

---

## §7 Tester Agent

*(Nguồn: README-tester-agent.md — vẫn hoạt động)*

```bash
npm run tester:agent   # Chạy lint + test + e2e
npm run pipeline       # Alias đầy đủ hơn (4 stages)
```

Pipeline 4 stages: **lint → test → e2e → e2e:runtime (Playwright)**  
Quy tắc: Code chỉ được review khi "ALL TESTS PASSED". Không ngoại lệ.

Config: `package.json`, `scripts/tester-agent.mjs`, `scripts/e2e-test.js`

---

## §8 ⚠️ REVIEW CUỐI TUẦN — Tasks Chưa Hoàn Thành

> Cập nhật: 2026-08-12. Nguồn: `docs/tasktodo.md` (2026-07-29) + `docs/claudecode-report.md` (2026-08-11).

### 🔴 CRITICAL — Chưa làm

| # | Task | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| **T1** | Seed 48K monks với `name_vi` (ETL) | ❌ 335/48,412 đã có name_vi | ETL bulk từ persons.json → Hán-Việt → namevi_map |
| **T2** | CBETA Passages import + PASSAGE_VI + entity summary API | ❌ `/passages` trả count=0 | Import thêm CBETA texts; build PASSAGE_VI table; LLM summary endpoint |
| **T9** | Dashboard stats `/api/admin/dashboard/stats` → 404 | ❌ | Route chưa tồn tại trong app.py |

### 🟡 MEDIUM — Backlog

| # | Task | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| **T3** | Fuzzy matching title_zh ↔ place (CBETA Catalog) | ❌ Đang dùng LIKE | Dùng RapidFuzz |
| **T4** | Marcus glossaries → link với people/works | ❌ Chưa link | `term_glossaries` chưa chuẩn hóa |
| **T5** | TTL VN → ETL cho ~2000 file còn lại | ⏳ 16/~2000 xong | Tiếp tục ETL, gắn `dila_id` cho 11 nhân vật chưa verified |
| **T6** | GIS cluster click → zoom-to-bounds | ❌ | Leaflet MarkerClusterGroup click handler |
| **T7** | Wikipedia multi-language fallback mạnh hơn | ❌ | Cache refresh + fallback |
| **T8** | Missing hanzi admin view | ❌ | Bảng `missing_hanzi` có nhưng chưa có UI |

### 🔵 ZERO PROGRESS — Chưa bắt đầu (audit 2026-08-11)

| Module | Thực trạng | Cần làm |
|--------|-----------|---------|
| **Time Authority** | `time_periods` = 0 rows | Import DILA Time Authority (lunar_month / era / emperor / dynasty) |
| **Nexus Points** | Không có route `/nexus/find` trong code | Xây entity-linking engine + nexus extraction từ CBETA TEI |
| **RAG** | Không có vector index, không có `/api/rag/*` route thật | Chọn vector DB (pgvector / FAISS), embed passages, build retrieval API |
| **Person name_vi** | `people.name_vi` = 0% (48,673 rows) | Chạy T1 (ETL Hán-Việt batch) |
| **Person bio tiếng Việt** | `people.bio` = 0% | Phụ thuộc vào CBETA/RAG + LLM |
| **Knowledge Graph Visualization** | Không có frontend graph viz cho entity | P0 trong competitive roadmap |

### 📋 Thứ tự ưu tiên gợi ý cho phiên dev tiếp theo

```
1. T9 (Dashboard 404) — nhanh nhất, 1 route
2. T1 (Seed name_vi) — impact lớn nhất cho dữ liệu
3. T2 (CBETA passages) — unblock nhiều feature
4. Time Authority import — core missing module
5. T5 (TTL VN ~2000 files) — tiếp tục pipeline đã có
```

---

*Tạo: 2026-08-12 — consolidate từ: DILA_Structure_Report.md, NOTES_NGINX_FIX.md, QA_REPORT_V2.md, API_DOCS.md, QA2.md, TASK_LOG_QA1.md, FEATURE_PLAN.md, SYSTEM_MAP.md, TASK_LOG.md, README-tester-agent.md, QA_REPORT_V3.md, GAP_REPORT.md, session.md, Timeline Tich Hop.md*

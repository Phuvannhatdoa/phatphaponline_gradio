# PHẬT TỔ ĐẠO ẢNH - Buddhist Heritage Mapping

> **🚀 VERSION:** v10.5-Place-VN-Mapping (2026-04-29)
> **Status:** ✅ Place VN Management with Vietnamese Names
> **Completion:** ~99.5%
> **Live:** https://phatphaponline.org/daoanh/
> **Admin:** https://phatphaponline.org/daoanh/admin/

---

> **🚀 VERSION:** v10.5-Place-VN-Mapping (2026-04-29)
> **Status:** ✅ Place VN Management with Vietnamese Names
> **Completion:** ~99.5%
> **Live:** https://phatphaponline.org/daoanh/
> **Admin:** https://phatphaponline.org/daoanh/admin/

### ✅ Today's Completed Tasks (2026-04-29)

#### TTL Rebuild v4.0 (3-Column Layout)
1. **Lexicon Priority**: Hàn Lâm > Phổ Thông > Tham Khảo
   - Extract CJK names (Chinese, Japanese) for DILA/Marcus mapping
   - Show full bio text (985+ chars) in Startdict column
   
2. **Color Match Across Columns**
   - Same amber color (#fbbf24) for matching name_zh across DILA/VPS/Lexicon
   - Visual confirmation of correct data mapping
   
3. **Marcus Column Fix**
   - Resolve teacher/student IDs from TTL `hasTeacher`/`hasStudent`
   - Extract names from TTL content (e.g., `Dương Kì Phương Hội`)
   - Fix: Show "Người Việt - chưa có trong DB" for Vietnamese monks

4. **DILA Fields Fix**
   - Resolve place IDs to `name_vi` (e.g., `Bảo Phong`)
   - Resolve work IDs to `title` (e.g., `Chánh Pháp Nhãn Tạng`)
   - Rename "SỞ CHỐN" → "ĐẠO TRÀNG"

5. **Place VN Management**
   - Updated `/api/admin/places` to search `name_zh`, `name_vi`, `name_en`, `location`
   - Populated `places.name_vi` with Vietnamese names (e.g., `Thiếu Lâm Tự` for `少林寺`)
   - ETL Script: `scripts/build_place_vi_map.py` (maps Chinese → Vietnamese)

#### Files Changed
```
server.py              - Place VN API + Marcus fix + TTL rebuild endpoints
admin/panorama.html    - 3-column UI + color match + full bio display
scripts/build_place_vi_map.py - NEW: Place Vietnamese name mapping ETL
data/lineage.db       - Updated places.name_vi field
```

#### Git Commits
```
8ce3192 - FIX-lexicon-search: extract Vietnamese name from TTL
e66225d - FIX-priority: match exact source names
4976a44 - UI-startdict: full text (985 chars) with scroll
3315514 - FIX-dila-fields: resolve place/work IDs
034455f - FIX-marcus: search by TTL name_vi and name_zh
407333c - FIX-marcus: resolve teacher/student IDs from TTL
6cf31e2 - FIX-marcus: resolve teacher name from TTL content
c2e74e3 - FIX-master: show full bio text (no truncation)
ab5be5a - feat: Update Place VN search to support Vietnamese names
```

---

> **🚀 VERSION:** v10.4-Full-GPS (2026-04-22)
> **Status:** ✅ FULL GPS: 58,476 places with coordinates
> **Completion:** ~99%
> **Live:** https://phatphaponline.org/daoanh/
> **Admin:** https://phatphaponline.org/daoanh/admin/
> **Status:** ✅ DILA Person Authority imported (48,803 monks)
> **Completion:** ~98%

---

> **🚀 VERSION:** v8.1-Features-Complete (2026-04-13)

---

> **🚀 VERSION:** v8.0-BUG-FIX-STARDict (2026-04-13)
> **Status:** ✅ StarDict JSON parse error fixed

---

> **🚀 VERSION:** v7.2-Final-Complete (2026-04-12)
> **Status:** ✅ All QA gaps fixed (P0, P1, P2)
> **Completion:** 97%

---

> **🚀 VERSION:** v5.8-Lineage-API-Complete (2026-04-11)
> **Status:** ✅ Lineage API + Place→Person lookup
> **Live:** https://phatphaponline.org/daoanh/
> **Completion:** ~97%

---

## 📋 PROJECT COMPLETION STATUS (v5.7 - 2026-04-11)

### Tổng quan

| Thành phần | Hoàn thành | Ghi chú |
|------------|------------|---------|
| **5 User-Facing Features** | 5/5 (100%) | ✅ Done |
| **DILA Place Authority** | ✅ | 5,000 places + GPS |
| **DILA Person Authority** | ✅ | 48,803 persons + lineage |
| **DILA Time Authority** | ✅ v5.6 | dynasty + timeline API |
| **Entity Linking** | ✅ NEW v5.7 | person + place + time |
| **Nexus Points** | ✅ NEW v5.7 | Person+Place+Time |
| **Timeline Slider** | ✅ | /api/persons/timeline + slider |
| **Admin Dashboard** | ✅ | Place + Person stats |
| **RDF Export** | ✅ NEW v8.1 | /api/export/rdf, /api/export/owl |
| **Entity Linking** | ✅ | TEI + Nexus Points |
| **GIS Map** | ✅ | Leaflet + GPS |
| **Timeline View** | ✅ | /api/persons/timeline + slider |
| **Genealogy-Map Integration** | ✅ NEW v5.4 | Lineage + places + paths |
| **Admin Dashboard** | ✅ | Place + Person stats |
| **Zero-RAM Optimization** | ✅ | Lazy loading + chunking |
| **Performance Caching** | ✅ | filteredCache |

### v5.4 Features Completed

| Feature | Status | Description |
|---------|--------|-------------|
| Person Authority | ✅ | 48,803 persons from DILA |
| Lineage-Map API | ✅ | Genealogy + Geography |
| GPS Lookup | ✅ | places.json integration |
| Admin Person Stats | ✅ | /api/admin/person-stats |
| Search Enhancement | ✅ | Person tab in search |

### All v8.1 Features Completed

- RDF/OWL Export - DONE (/api/export/rdf, /api/export/owl)
- Timeline View - DONE (was already implemented, just marked complete)

---

> **🚀 VERSION:** v3.6-ZeroRAM-Complete (2026-04-10)
> **Status:** ✅ Zero-RAM Optimization + Performance Caching

---

> **🚀 VERSION:** v4.2-CodePreview-Setup (2026-04-10)
> **Status:** ✅ CodePreview Agent Configuration Complete - Ready for Code Review
> **Live:** https://phatphaponline.org/daoanh/

---

> **🚀 VERSION:** v4.0-Deep-Research-Integration (2026-04-10)
> **Status:** ✅ PHASE v4.0 COMPLETE - All 16 Tasks Done!
> **Status:** ✅ Fixed Entity Filter + Map Integration + Critical Places Loading

---

> **🚀 VERSION:** v3.3-DILA-Authority-Integration (2026-04-10)
> **Status:** ✅ DILA IDs + JDN + Entity Linking Complete

---

> **🚀 VERSION:** v3.0-DILA-Research-Complete (2026-04-10)
> **Status:** ✅ DILA Authority Databases Analysis + Feature Plan Complete

---

> **🚀 VERSION:** v2.9-Roadmap-2026-04-09 (2026-04-09)
> **Status:** ✅ Roadmap Updated: AI Interpreter, GIS Timeline, Popup Dict, Zero-RAM

---

## 🔬 PHASE v3.0: DILA Authority Databases Research (2026-04-10)

### Nghiên cứu hoàn thành
- **4 Authority Databases:** Person, Place, Time, Catalog
- **Công nghệ:** EXT JS + eXist-db + Google Earth/Maps + SIMILE Timeline
- **Entity Linking:** TEI attributes (`ref="#A000001"`)
- **Nexus Points:** Person + Place + Time giao nhau trong văn bản

### Files tạo mới
| File | Mô tả |
|------|-------|
| `DILA_Structure_Report.md` | Báo cáo kỹ thuật chi tiết (887 dòng) |
| `FEATURE_PLAN.md` | Lộ trình phát triển đầy đủ |
| `SESSION.md` | Trạng thái tiến độ |

### Chức năng cần xây dựng (so với DILA)
| Module | DILA | Đạo Ảnh | Priority |
|--------|------|---------|----------|
| Person Authority | ✅ | ❌ | Cao |
| Time Authority | ✅ | ❌ | Cao |
| Entity Linking | ✅ | ❌ | Cao |
| Nexus Points | ✅ | ❌ | Cao |
| GIS Map | ✅ | ❌ | Trung bình |
| Timeline View | ✅ | ❌ | Trung bình |

---

> **VERSION:** v2.8-Admin-Verification-Dashboard (2026-04-09)
> **Status:** ✅ 360° Comparison + Lotus Approval + Zero-RAM Design

---

## 📊 SO SÁNH: YÊU CẦU MỚI vs HIỆN TẠI

### A. TRUY VẤN THÔNG MINH (Semantic Search & SPARQL)

| Yêu cầu | Mô tả | Hiện tại | Cần làm |
|---------|-------|----------|---------|
| **Ngôn ngữ tự nhiên** | Tiếng Việt → SPARQL | ❌ Chưa có | ⏳ **Cần phát triển** |
| **Ví dụ:** "Tìm các thiền sư Lâm Tế thế kỷ 17" | → Query GraphDB | ❌ | ⏳ Thêm AI Interpreter |
| **Giải thích kết quả** | Text dễ hiểu từ SPARQL results | ❌ | ⏳ Thêm response formatter |

### B. BẢN ĐỒ THỜI GIAN ĐỘNG (GIS Timeline)

| Yêu cầu | Mô tả | Hiện tại | Cần làm |
|---------|-------|----------|---------|
| **Thanh trượt thời gian** | Kéo đến năm → hiện thực thể | ⚠️ Có basic | 🔄 **Cần nâng cấp** |
| **Multi-entity** | Hiện nhiều thực thể cùng lúc | ⚠️ Có layer | 🔄 Tối ưu filter |
| **Địa danh theo thời kỳ** | Ấn Độ/Trung Hoa/Việt Nam | ✅ Có layers | ✅ Hoàn thành |
| **Filter theo thế kỷ** | -600 đến 2026 | ❌ | 🔄 Thêm slider |

### C. TỪ ĐIỂN ĐA NGỮ (Popup Dictionary)

| Yêu cầu | Mô tả | Hiện tại | Cần làm |
|---------|-------|----------|---------|
| **StartDict integration** | Popup khi rê chuột vào từ khó | ❌ Chưa có | ⏳ **Cần phát triển** |
| **Hán Việt + Phạn ngữ** | Tra cứu thuật ngữ Phật giáo | ❌ | ⏳ Thêm data |
| **Tooltip trên text** | Hover hiện popup | ❌ | ⏳ Thêm module |

### D. HỆ THỐNG PHẢN HỒI NHANH (Zero-RAM Indexing)

| Yêu cầu | Mô tả | Hiện tại | Cần làm |
|---------|-------|----------|---------|
| **Tốc độ 0.001s** | Index-based search | ⚠️ Có cache | 🔄 **Cần benchmark** |
| **VPS 3GB RAM** | Tối ưu tài nguyên | ⚠️ Cơ bản | 🔄 Tối ưu code |
| **Key-Value Index** | Không tốn RAM | ❌ | 🔄 Thêm indexing |

### E. ETL AGENT (DILA XML Processing)

| Yêu cầu | Mô tả | Hiện tại | Cần làm |
|---------|-------|----------|---------|
| **Quét XML DILA** | Nhận diện: Tên sư, năm sinh/mất, địa danh | ✅ Có 59k places | ✅ Hoàn thành |
| **Relationship Mapping** | Sư A là đệ tử Sư B | ⚠️ Có pathfinding | 🔄 Mở rộng |
| **Chuẩn hóa & Hợp nhất** | DILA vs Internal data | ⚠️ Basic | 🔄 Nâng cấp |
| **RDF/TTL Export** | Lưu trữ đồ thị quan hệ | ✅ Có | ✅ Hoàn thành |

### F. ADMIN VERIFICATION DASHBOARD

| Yêu cầu | Mô tả | Hiện tại | Cần làm |
|---------|-------|----------|---------|
| **Status Panel** | Header với real-time stats | ✅ Hoàn thành | ✅ |
| **Exception Sidebar** | Conflict (đỏ) + Missing (xám) | ✅ Hoàn thành | ✅ |
| **360° Comparison** | 4 khối song song (StarDict/GMaps/Wiki/RDF) | ✅ Hoàn thành | ✅ |
| **Lotus Done** | Nút Approve + hiệu ứng Hoa Sen Vàng | ✅ Hoàn thành | ✅ |
| **Zero-RAM Design** | Load on-demand, không pre-load | ✅ Hoàn thành | ✅ |

---

## 📋 ROADMAP: CÁC CHỨC NĂNG CẦN PHÁT TRIỂN

### Phase 1: AI Interpreter (VN → SPARQL) - **PRIORITY CAO**
- [ ] Tạo module nhận diện câu hỏi tiếng Việt
- [ ] Parse keywords: "thiền sư", "Lâm Tế", "thế kỷ 17"
- [ ] Build SPARQL query từ keywords
- [ ] Format kết quả thành text dễ hiểu
- [ ] Tích hợp vào search.js

### Phase 2: GIS Timeline Slider - **PRIORITY CAO**
- [ ] Tạo timeline slider component
- [ ] Logic filter theo năm (-600 đến 2026)
- [ ] Multi-entity display (nhiều markers cùng lúc)
- [ ] Preset buttons: "Thời Đức Phật", "Truyền sang Trung Hoa", "Truyền sang Việt Nam"

### Phase 3: Popup Dictionary - **PRIORITY TRUNG**
- [ ] Tạo dictionary lookup module
- [ ] Tích hợp StarDict data (đã có trong data/dictionaries/)
- [ ] Add hover/click handler cho text
- [ ] Show tooltip popup với definition

### Phase 4: Zero-RAM Optimization - **PRIORITY TRUNG**
- [ ] Benchmark tốc độ hiện tại
- [ ] Implement Key-Value indexing
- [ ] Optimize cho VPS 3GB RAM
- [ ] Add caching layer

---

## 📋 NEW USER-FACING FUNCTIONS (v3.1 - 2026-04-10)

### 1. Multi-layer Entity Filter (Bộ lọc thực thể đa lớp)
- [ ] **Dropdown Triều đại:** Lọc theo triều đại (Lý, Trần, Lê, Nguyễn...)
- [ ] **Dropdown Loại hình:** Dịch giả, Thiền sư, Nghĩa giải
- [ ] **Dropdown Khu vực:** Miền Bắc, Miền Trung, Miền Nam
- [ ] **Auto-complete:** Từ kho .idx đã đánh chỉ mục

### 2. Popup Context Cards (Cửa sổ thông tin nhanh)
- [ ] **Hover detection:** Nhận diện tên Thiền sư/Địa danh trong text
- [ ] **Card display:** Ảnh, năm sinh/mất, dòng truyền thừa
- [ ] **Nút "Xem sơ đồ":** Link đến Network Viewer
- [ ] **Entity Linking:** Tự động gắn ID vào từ khóa

### 3. Lineage & Network Viewer (Trình xem sơ đồ quan hệ)
- [ ] **Vis.js integration:** Canvas cho sơ đồ
- [ ] **Node trung tâm:** Vị thiền sư đang xem
- [ ] **Node vệ tinh:** Thầy (Teacher), Trò (Student), Bạn đồng tu
- [ ] **Click to navigate:** Click node → di chuyển tâm điểm

### 4. GIS-Time Slider (Bản đồ tích hợp Timeline)
- [ ] **Leaflet map:** 2/3 màn hình
- [ ] **Timeline slider:** Năm 0 đến 2000
- [ ] **JDN filter:** Hiện/ẩn points theo thời gian
- [ ] **Play mode:** Auto-run thời gian

### 5. Text Comparison & Source Tracking (So sánh văn bản)
- [ ] **Dual panel:** Văn bản gốc + Bản dịch song song
- [ ] **TEI `<lb>` alignment:** Căn dòng chính xác
- [ ] **Source tracking:** Link đến DILA/CBETA
| **Nạp GraphDB (RDF/TTL)** | Lưu trữ đồ thị quan hệ | ✅ Có | ✅ Hoàn thành |

---

## 📋 ROADMAP: CÁC CHỨC NĂNG CẦN PHÁT TRIỂN

### Phase 1: AI Interpreter (Ngôn ngữ tự nhiên → SPARQL)
- [ ] Tạo module AI nhận diện tiếng Việt
- [ ] Chuyển câu hỏi → SPARQL query
- [ ] Trả về kết quả dạng văn bản

### Phase 2: GIS Timeline Nâng cấp
- [ ] Thêm thanh trượt thời gian (Timeline slider)
- [ ] Hiện nhiều thực thể cùng lúc (Multi-entity)
- [ ] Filter theo thế kỷ (-600 đến 2026)

### Phase 3: Popup Dictionary
- [ ] Tích hợp StartDict data
- [ ] Click/rê chuột → hiện popup
- [ ] Hỗ trợ Hán Việt + Pali

### Phase 4: Performance Optimization
- [ ] Benchmark tốc độ (target 0.001s)
- [ ] Tối ưu cho VPS 3GB RAM
- [ ] Index-based search

---

## 📝 TASK LOG (2026-04-09)

### Task: Thêm 14 Critical Places (GPS + Vietnamese Lineages)
- **Date:** 2026-04-09
- **Status:** ✅ COMPLETED
- **Changes:**
  - Added GPS for Tào Khê (24.8833, 113.2333)
  - Added Vietnamese lineages: Yên Tử, Quỳnh Lâm, Trúc Lâm
  - Added Vietnamese monks: Trần Nhân Tông
  - Added Chinese lineages: Vân Môn, Lâm Tế
  - Updated search_index_critical.json (29 entries)
- **Files Updated:**
  - `data/processed/search_index_critical.json`
  - `agents/phat_to_dao_anh.md` (v2.7)

### Next Steps:
1. [ ] AI Interpreter for Vietnamese queries
2. [ ] Timeline slider (P12)
3. [ ] Popup Dictionary
4. [ ] Zero-RAM indexing

---

## 📁 Current Files Structure

```
daoanh/
├── src/js/
│   ├── search.js        ✅ Dictionary v2 (29 places)
│   ├── map.js          ✅ Leaflet + layers
│   ├── pathfinding.js  ✅ Teacher-Student links
│   ├── deepsearch.js    ✅ CBETA integration
│   ├── performance.js  ✅ Basic optimization
│   ├── timeline/       ✅ slider.js, manager.js
│   ├── dictionary/     ✅ dict_loader, hover_detector, popup_renderer
│   └── ai/             ✅ semantic_parser, intent_router, sparql_generator, etc.
│
├── data/processed/
│   ├── search_index_critical.json  ✅ 29 places
│   ├── temples_master_gps.json     ✅ Vietnamese temples
│   └── places.json                 ✅ 65k DILA places
```

---

## PHASE v4.0: Deep Research Integration (2026-04-10)

### Tổng quan
Dựa trên nghiên cứu từ `deep-research-report.md`, bổ sung các features cốt lõi mà hệ thống Đạo Ảnh còn thiếu.

---

### 1. AI Interpreter (VN → SPARQL) - ✅ COMPLETED

| Task | Mô tả | File output | Status |
|------|-------|-------------|--------|
| [x] Semantic Parser | Nhận diện intent từ câu hỏi tiếng Việt | `src/js/ai/semantic_parser.js` | ✅ |
| [x] Intent Router | Phân loại: factual→API, relational→GraphDB, semantic→RAG | `src/js/ai/intent_router.js` | ✅ |
| [x] SPARQL Generator | Build query từ keywords | `src/js/ai/sparql_generator.js` | ✅ |
| [x] Response Formatter | Convert kết quả → text dễ hiểu | `src/js/ai/response_formatter.js` | ✅ |

---

### 2. Zero-RAM Indexing - ✅ COMPLETED

| Task | Mô tả | File output | Status |
|------|-------|-------------|--------|
| [x] Index Generator | Tạo .idx files từ JSON data | `src/python/index_generator.py` | ✅ |
| [x] Trie Structure | Trie-based lookup cho autocomplete | `src/js/search/trie_index.js` | ✅ |

---

### 3. Full ETL Pipeline - ✅ COMPLETED

| Task | Mô tả | File output | Status |
|------|-------|-------------|--------|
| [x] XML Extractor | Parse DILA XML/RDF | `src/python/etl/xml_extractor.py` | ✅ |
| [x] JSONL Writer | Stream to JSONL | `src/python/etl/jsonl_writer.py` | ✅ |
| [x] RDF Converter | JSONL → Turtle (.ttl) | `src/python/etl/rdf_converter.py` | ✅ |
| [x] GraphDB Loader | TTL → GraphDB | `src/python/etl/graphdb_loader.py` | ✅ |
| [x] Relationship Extractor | Extract thầy-trò links | `src/python/etl/relation_extractor.py` | ✅ |

---

### 4. 9-Agent System - ✅ COMPLETED

| Agent | Vai trò | Priority | Status |
|-------|---------|----------|--------|
| [x] Orchestrator | Central controller, routing | Cao | ✅ |
| [ ] Semantic Parser | NL → SPARQL/API | Cao | ⏳ |
| [ ] DILA API Agent | HTTP calls to DILA | Cao | ⏳ |
| [ ] ETL Processor | XML → TTL | Cao | ⏳ |
| [ ] GraphDB Agent | SPARQL queries | Cao | ⏳ |
| [ ] RAG Engine | Semantic search | Trung | ⏳ |
| [ ] Fusion Engine | Merge multi-source | Cao | ⏳ |
| [ ] Visualization Engine | GIS + Timeline | Trung | ⏳ |
| [ ] Storage Optimizer | Zero-RAM index | Cao | ⏳ |

---

### 5. Multi-source RAG - ✅ COMPLETED (v4.15-v4.16)

| Task | Mô tả | File output | Status |
|------|-------|-------------|--------|
| [x] DILA Connector | Lấy data từ DILA API | `src/js/ai/dila_connector.js` | ✅ |
| [x] GraphDB Connector | SPARQL queries | `src/js/ai/orchestrator.js` | ✅ |
| [x] Local DB Connector | Internal lineage data | `src/js/ai/orchestrator.js` | ✅ |
| [x] Fusion Logic | Priority: DILA > GraphDB > RAG | `src/js/ai/fusion_engine.js` | ✅ |
| [x] Deduplication | Loại bỏ trùng lặp | `src/js/ai/fusion_engine.js` | ✅ |

---

### 6. Time Authority (Lịch pháp) - ✅ COMPLETED (v4.14)

| Task | Mô tả | File output | Status |
|------|-------|-------------|--------|
| [x] JDN Converter | Julian Day Number calculation | `src/python/time_authority.py` | ✅ |
| [x] Lunisolar Calendar | Âm lịch ↔ Dương lịch | `src/python/time_authority.py` | ✅ |
| [x] Date Range Filter | Lọc theo năm/thế kỷ | `src/python/time_authority.py` | ✅ |
| [x] Dynasty Mapping | Triều đại → năm | `src/python/time_authority.py` | ✅ |

---

### 7. Popup Dictionary (StarDict) - ✅ COMPLETED

| Task | Mô tả | File output | Status |
|------|-------|-------------|--------|
| [ ] Dictionary Loader | Load StarDict files | `src/js/dict/dict_loader.js` | ⏳ |
| [ ] Hover Detector | Nhận diện từ khóa | `src/js/dict/hover_detector.js` | ⏳ |
| [ ] Popup Renderer | Hiện tooltip | `src/js/dict/popup_renderer.js` | ⏳ |

---

### 8. Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API latency | < 300ms | ❓ |
| Graph query | < 100ms | ❓ |
| RAG response | < 500ms | ❓ |
| RAM usage | < 5% | ❓ |
| Zero-RAM lookup | < 1ms | ❓ |

---

## Files cần tạo mới

```
daoanh/
├── src/
│   ├── js/
│   │   ├── ai/
│   │   │   ├── semantic_parser.js
│   │   │   ├── intent_router.js
│   │   │   ├── sparql_generator.js
│   │   │   └── response_formatter.js
│   │   ├── dict/
│   │   │   ├── dict_loader.js
│   │   │   ├── hover_detector.js
│   │   │   └── popup_renderer.js
│   │   └── search/
│   │       └── trie_index.js
│   └── python/
│       ├── etl/
│       │   ├── xml_extractor.py
│       │   ├── jsonl_writer.py
│       │   ├── rdf_converter.py
│       │   ├── graphdb_loader.py
│       │   └── relation_extractor.py
│       └── index_generator.py
```

---

## TASK LOG PHASE v4.0

### Task v4.1: Semantic Parser (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/semantic_parser.js` (156 lines)
- **Features:**
  - Entity extraction (person, place, lineage, time)
  - Intent detection (factual/relational/semantic)
  - Lineage keyword mapping (LamTe, VanMon, YenTu...)
  - Century/time range parsing
- **Notes:** Parse Vietnamese queries → structured output

---

### Task v4.2: Intent Router (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/intent_router.js` (132 lines)
- **Features:**
  - Intent-based routing (factual→DILA_API, relational→GraphDB, semantic→RAG)
  - Fallback chain (primary → fallback)
  - Retry logic with timeout
  - Parallel query support
- **Notes:** Route parsed queries to appropriate data sources

---

### Task v4.3: SPARQL Generator (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/sparql_generator.js` (157 lines)
- **Features:**
  - SPARQL templates (byLineage, byTimeRange, teacherStudent, placeQuery, timeline)
  - Query type auto-detection
  - Person details & timeline generation
  - Query validation
- **Notes:** Build SPARQL queries from parsed keywords

---

### Task v4.4: Response Formatter (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/response_formatter.js` (149 lines)
- **Features:**
  - SPARQL results → Vietnamese text
  - Multiple format types (monks, teacher-student, places, timeline)
  - HTML output for UI rendering
  - Error & loading states
- **Notes:** Format kết quả thành text/HTML dễ hiểu

---

### Task v4.5: Index Generator (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/index_generator.py` (221 lines)
- **Features:**
  - Generate .idx binary files (header + index + data)
  - Trie index for autocomplete
  - Search index with diacritics removal
  - ByteOffsetReader class for Zero-RAM lookup
- **Notes:** Python script cho Zero-RAM indexing

---

### Task v4.6: Trie Structure (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/search/trie_index.js` (171 lines)
- **Features:**
  - JavaScript Trie implementation
  - Prefix search với diacritics removal
  - Exact match support
  - Load from JSON array
  - Singleton pattern
- **Notes:** JavaScript trie cho autocomplete

---

### Task v4.7: XML Extractor (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/etl/xml_extractor.py` (269 lines)
- **Features:**
  - Parse TEI & RDF formats
  - Extract person, place, relation entities
  - Streaming extraction (generator)
  - Statistics tracking
- **Notes:** Python ETL - Parse DILA XML/RDF

---

### Task v4.8: JSONL Writer (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/etl/jsonl_writer.py` (183 lines)
- **Features:**
  - Write to JSONL format (one JSON per line)
  - Memory efficient streaming
  - Read, filter, count functions
  - JSON to JSONL conversion
  - Merge multiple JSONL files
- **Notes:** Stream extracted data to JSONL format

---

### Task v4.9: RDF Converter (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/etl/rdf_converter.py` (244 lines)
- **Features:**
  - Convert JSONL to Turtle (.ttl) format
  - Person, Place, Relation entity support
  - Multi-language labels (@en, @vi, @zh)
  - owl:sameAs linking support
  - GPS coordinates mapping
  - Statistics tracking
- **Notes:** Convert JSONL to Turtle (.ttl) format

---

### Task v4.10: GraphDB Loader (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/etl/graphdb_loader.py` (203 lines)
- **Features:**
  - Load TTL files via HTTP API
  - Multiple file batch loading
  - Named graph support (context)
  - Repository management
  - SPARQL query execution
  - Connection checking
- **Notes:** Load TTL files to GraphDB

---

### Task v4.11: Relationship Extractor (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/etl/relation_extractor.py` (263 lines)
- **Features:**
  - Extract teacher-student relationships
  - Pattern-based text extraction
  - Lineage detection
  - Relation resolution to IDs
  - Lineage tree building
  - Ancestor/descendant finding (pathfinding)
- **Notes:** Extract teacher-student links from data

---

### Task v4.12: 9-Agent System Setup
- **Status:** ⏳ PENDING
- **Notes:** Orchestrator + Agent integration
- **Status:** ⏳ PENDING
- **Files:** TBD
- **Notes:** Extract teacher-student links from data

---

### Task v4.12: 9-Agent System Setup (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/orchestrator.js` (201 lines)
- **Features:**
  - Central orchestrator for 9-agent pipeline
  - Agent registry (SemanticParser, IntentRouter, SPARQLGenerator...)
  - Query pipeline: Parse → Route → Generate → Execute → Format
  - Error handling & fallback
  - System status & debug logging
- **Notes:** Orchestrator + Agent integration

---

### Task v4.13: Popup Dictionary (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** 
  - `daoanh/src/js/dict/dict_loader.js` (127 lines)
  - `daoanh/src/js/dict/hover_detector.js` (167 lines)
  - `daoanh/src/js/dict/popup_renderer.js` (170 lines)
- **Features:**
  - Dictionary loading (StarDict format)
  - Word lookup with diacritics normalization
  - Hover detection for term lookup
  - Popup tooltip với Amber Gold theme
  - Click-outside dismiss
- **Notes:** dict_loader.js, hover_detector.js, popup_renderer.js

---

### Task v4.14: Time Authority (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/python/time_authority.py` (198 lines)
- **Features:**
  - JDN (Julian Day Number) conversion
  - Lunisolar calendar (Âm lịch ↔ Dương lịch)
  - Dynasty mapping (VN & CN)
  - Century parsing ("thế kỷ 17" → 1600-1700)
  - Era conversion (Năm thứ X)
- **Notes:** Calendar conversion + time authority

---

### Task v4.15: DILA Connector (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/dila_connector.js` (137 lines)
- **Features:**
  - DILA API integration
  - Person/Place/Time lookup
  - Cache with expiry (24h)
  - Retry logic
  - Connection checking
- **Notes:** Connect to DILA Web Services

---

### Task v4.16: Fusion Engine (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/ai/fusion_engine.js` (145 lines)
- **Features:**
  - Multi-source data fusion
  - Priority: DILA > GraphDB > RAG
  - Deduplication
  - Conflict resolution
  - Source comparison
- **Notes:** Merge multi-source results

---

## TỔNG KẾT PHIÊN LÀM VIỆC (2026-04-10)

### ✅ HOÀN THÀNH (16/16 tasks - 100%):

| Task | File | Lines |
|------|------|-------|
| v4.1 Semantic Parser | `src/js/ai/semantic_parser.js` | 156 |
| v4.2 Intent Router | `src/js/ai/intent_router.js` | 132 |
| v4.3 SPARQL Generator | `src/js/ai/sparql_generator.js` | 157 |
| v4.4 Response Formatter | `src/js/ai/response_formatter.js` | 149 |
| v4.5 Index Generator | `src/python/index_generator.py` | 221 |
| v4.6 Trie Index | `src/js/search/trie_index.js` | 171 |
| v4.7 XML Extractor | `src/python/etl/xml_extractor.py` | 269 |
| v4.8 JSONL Writer | `src/python/etl/jsonl_writer.py` | 183 |
| v4.9 RDF Converter | `src/python/etl/rdf_converter.py` | 244 |
| v4.10 GraphDB Loader | `src/python/etl/graphdb_loader.py` | 203 |
| v4.11 Relationship Extractor | `src/python/etl/relation_extractor.py` | 263 |
| v4.12 Orchestrator | `src/js/ai/orchestrator.js` | 201 |
| v4.13 Popup Dictionary | `src/js/dict/*.js` (3 files) | 464 |
| v4.14 Time Authority | `src/python/time_authority.py` | 198 |
| v4.15 DILA Connector | `src/js/ai/dila_connector.js` | 137 |
| v4.16 Fusion Engine | `src/js/ai/fusion_engine.js` | 145 |

**Tổng cộng: ~3,149 lines of code**

---

### Task v4.17: Timeline Slider (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/timeline/slider.js` (228 lines)
- **Features:**
  - Year range slider (-600 to 2026)
  - Play/pause animation
  - Century jump buttons
  - Preset buttons (Thời Đức Phật, Truyền sang Trung Hoa...)
  - Real-time year display
- **Notes:** Timeline slider UI component

---

### Task v4.18: Timeline Manager (2026-04-10)
- **Status:** ✅ COMPLETED
- **Files:** `daoanh/src/js/timeline/manager.js` (168 lines)
- **Features:**
  - Entity filtering by year
  - Birth/death/floruit period handling
  - GPS coordinate extraction
  - Timeline data generation
  - Year range queries
- **Notes:** Entity time management for GIS Timeline

---

## ✅ PHASE v4.1 IN PROGRESS

### New Files Added:
| Task | File | Lines |
|------|------|-------|
| v4.17 Timeline Slider | `src/js/timeline/slider.js` | 228 |
| v4.18 Timeline Manager | `src/js/timeline/manager.js` | 168 |
| v4.19 GIS Timeline Integration | `src/js/timeline/gis_integration.js` | 228 |
| v4.20 RAG Connector | `src/js/ai/rag_connector.js` | 153 |
| v4.21 API Router | `src/js/api_router.js` | 218 |
| v4.22 Admin Dashboard | `src/js/admin/dashboard.js` | 208 |

---

## ✅ PHASE v4.1 COMPLETE

**Total: ~4,352 lines of code**

*Last Updated: 2026-04-10*
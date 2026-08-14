# PHẬT TỔ ĐẠO ẢNH - Buddhist Heritage Mapping

> **🚀 VERSION:** v8.1-Features-Complete (2026-04-13)
> **Status:** ✅ 100% - RDF/OWL Export + Timeline complete
> **Live:** https://phatphaponline.org/daoanh/admin/
> **Completion:** 100%

---

> **🚀 VERSION:** v8.0-BUG-FIX-STARDict (2026-04-13)
> **Status:** ✅ StarDict JSON parse error fixed

---

> **🚀 VERSION:** v7.2-Final-Complete (2026-04-12)
> **Status:** ✅ QA gaps fixed (P0, P1, P2) - All 7 bugs verified

---

> **🚀 VERSION:** v5.4-Person-Authority-Admin-Complete (2026-04-10)
> **Status:** ✅ DILA Person Authority (48,803 persons) + Admin Stats + Genealogy-Map

---

> **🚀 VERSION:** v4.5-Codepreview-Agent (2026-04-10)
> **Status:** ✅ Codepreview Agent Setup Complete

---

> **🚀 VERSION:** v2.9-Roadmap-2026-04-09 (2026-04-09)
> **Status:** ✅ Roadmap Updated: AI Interpreter, GIS Timeline, Popup Dict, Zero-RAM
> **Live:** https://phatphaponline.org/daoanh/

---

## 🎯 WHAT'S NEW (v2.2 - 2026-04-09)

### ✅ Batch Processing Complete
- Quét hàng loạt **22 file .docx** trong `data/dictionaries/`
- Lọc theo **Bộ lọc kép** (Tên + Ngữ cảnh địa lý)
- Gán ID theo **ISO 3166-2** (`pth:VN-XX_001_...`)
- Tìm thấy **897 địa danh** (Chùa/Tự/Viện)

#### Scripts Created
| Script | Description |
|--------|-------------|
| `batch_process_star_dict.py` | Quét 22 file .docx, lọc địa danh |
| `gps_enrichment_nominatim.py` | GPS Enrichment qua Nominatim API |

#### ISO 3166-2 Province Codes
```
pth:VN-34_001_Chua_Long_Son    # Khánh Hòa (Nha Trang)
pth:VN-SG_001_Chua_Ngon_Son    # Hồ Chí Minh
pth:VN-26_002_Tu_Hoa_Nghiem   # Huế (Thừa Thiên Huế)
```

#### Bộ lọc kép (Entity Routing)
- **Điều kiện 1 (Tên):** Bắt đầu bằng Chùa/Tự/Am/Viện hoặc kết thúc bằng Tự/Viện/Am/Cốc
- **Điều kiện 2 (Ngữ cảnh):** Value phải chứa từ khóa địa lý (tọa lạc, ở tại, thuộc tỉnh, xây dựng...)

### ✅ GPS Enrichment (Nominatim API)
- Sử dụng **OpenStreetMap Nominatim** (miễn phí, không API key)
- Đang chạy ngầm để enrich 897 địa danh
- Output: `temples_master_v2_gps.json`

### ✅ StarDict Linking (4 Tính năng)
1. **ID Mapping:** Hán tự ↔ Hán-Việt ↔ DILA ID
2. **Data Enrichment:** Nhúng mô tả StarDict vào Tooltip marker
3. **Auto-Tagging:** Biến văn bản tĩnh thành hyperlink sang GIS
4. **Academic Validation:** 3 khung song song (StarDict - Kinh văn - Địa điểm)

---

## 🎯 WHAT'S NEW (v2.0 - 2026-04-08)

### ✅ Dictionary Search Integration Complete
- Search ưu tiên: **Từ Điển (Phật Quang/Đạo Uyển)** → Monk → DILA/CBETA
- Tìm "**Tào Khê**" → Hiện Lục Tổ Huệ Năng + GPS + Đàn Kinh
- Tìm "**Thiếu Lâm**" → Hiện Bồ Đề Đạt Ma + GPS
- 15 critical places đã thêm với Vietnamese names + descriptions

### 📚 Critical Places in Dictionary
| Search | Vietnamese | Type | GPS | Related |
|--------|-----------|------|-----|---------|
| 曹溪 | **Tào Khê** | Chùa | - | Lục Tổ, Đàn Kinh |
| 少林寺 | **Thiếu Lâm Tự** | Chùa | 34.5085, 112.9347 | Bồ Đề Đạt Ma |
| 慧能 | **Huệ Năng** | Thiền sư | 23.9, 113.5 | Lục Tổ |
| Bodhidharma | **Bồ Đề Đạt Ma** | Thiền sư | - | Thiếu Lâm |
| 鹿野苑 | **Lộc Uyển** | Thánh địa | 25.1389, 83.0261 | - |
| 祇園精舍 | **Kỳ Viên Tinh Xá** | Chùa | 27.47, 82.04 | - |
| 菩提伽耶 | **Bồ Đề Đạo Tràng** | Thánh địa | 24.6961, 84.9911 | - |

---

## 📁 Folder Structure

```
daoanh/
├── app.py                    # Flask backend (entry point)
├── README.md                 # This file
├── DEPLOY_LOGS.md            # Deployment logs
├── phat_to_dao_anh.md        # Project manifest ⭐v5.4
├── SESSION.md                # Session state tracker ⭐v5.4
├── DILA_Structure_Report.md  # DILA technical research
├── FEATURE_PLAN.md           # Feature development roadmap
│
├── src/
│   ├── js/
│   │   ├── search.js         # v2: Person Authority search ⭐v5.4
│   │   ├── lineage_map.js     # NEW: Genealogy + Map integration
│   │   ├── map.js            # Map interface (Leaflet)
│   │   ├── pathfinding.js    # P11: Pathfinding algorithm
│   │   ├── deepsearch.js     # P13: Deepsearch integration
│   │   └── config.js         # Configuration
│   │
│   └── python/
│       ├── etl/
│       │   ├── import_dila_persons.py  # NEW: DILA Person ETL ⭐v5.4
│       │   └── ...
│       ├── parse_dictionaries.py
│       └── create_critical_data.py
│
├── admin/
│   ├── index.html            # Admin dashboard ⭐v5.4 (Person stats)
│   └── js/app.js             # Admin JS ⭐v5.4
│
├── data/
│   ├── processed/
│   │   ├── search_index_critical.json  # Dictionary search data ⭐NEW
│   │   ├── critical_places_lookup.json # Critical places lookup ⭐NEW
│   │   ├── places_final.json           # Final geocoded places
│   │   └── places_review.csv           # Admin review CSV
│   │
│   ├── dictionaries/          # Buddhist dictionaries (.docx)
│   │   ├── Phat Quang Tu Dien - HT Quang Do.docx
│   │   ├── Tu Dien Phat Hoc Dao Uyen.docx
│   │   └── Tu Dien Thien Tong Han Viet.docx
│   │
│   └── places.json           # DILA/CBETA places (65,005)
│
├── static/
│   ├── index.html            # Academic Research Layout
│   └── css/style.css         # UI styles
│
└── ontology/
    └── place_schema.ttl      # RDF Ontology
```

---

## 🚀 Quick Start

### Live Demo
**https://phatphaponline.org/daoanh/**

### Local Development
```bash
# Install Flask
apt-get install python3-flask

# Start server
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python3 app.py

# Access: http://localhost:5000/daoanh/
```

### Test Search
1. Mở https://phatphaponline.org/daoanh/
2. Gõ "Tào Khê" hoặc "Thiếu Lâm"
3. Click kết quả → Zoom map + hiện Workbench

---

## 📊 Progress Tracker

| Phase | Tasks | Status | Notes |
|-------|-------|--------|-------|
| Phase 1 | P1 (Ontology) | ✅ Complete | Place class + schema |
| Phase 2 | P2 (DILA/CBETA) | ✅ Complete | 65,005 places loaded |
| Phase 2 Extended | Dictionary Integration | ✅ Complete (v2.0) | 15 critical places |
| Phase 2.1 | Batch Processing (v2.2) | ✅ Complete | 897 temples from 22 files |
| Phase 2.2 | GPS Enrichment | 🔄 Running | Nominatim API |
| Phase 3 | P9-P12 (Map/Layers) | ✅ Complete | Leaflet + Pathfinding |
| **Phase 3 Extended** | **DILA Research (v3.0)** | ✅ **Complete** | **Person/Time Authority** |
| Phase 4 | P13-P15 | ⏳ Pending | Deepsearch + Performance |

---

## 🔜 Next Steps (v3.0 - Ready for Build Agent)

### Priority 1: Authority Databases
1. [ ] **Person Authority** - JSON Schema + ETL + API
2. [ ] **Time Authority** - Date conversion + Timeline
3. [ ] **Entity Linking** - Auto-link person/place/time in texts

### Priority 2: Visualization
4. [ ] **GIS Map** - Leaflet/OpenStreetMap integration
5. [ ] **Timeline View** - Filter monks by period
6. [ ] **Lineage Network** - Upgrade Vis.js network

### Priority 3: Advanced
7. [ ] RDF/OWL Export
8. [ ] TEI XML Import (CBETA format)

---

## 📋 Reference

| Document | Description |
|----------|-------------|
| `phat_to_dao_anh.md` | Full project manifest with all prompts |
| `Codepreview.md` | Agent kiểm tra code & phát hiện bugs ⭐NEW v4.5 |
| `SESSION.md` | Session state tracker |
| `LOGS.md` | Task logs |
| `DEPLOY_LOGS.md` | Deployment logs (2026-04-08) |
| `../docs/Plant_for_puzzle.md` | Master plan (Ver 5.0) |

---

## 🌐 URLs

| Service | URL |
|---------|-----|
| **Live App** | https://phatphaponline.org/daoanh/ |
| **GraphDB** | http://158.220.106.183:7200 |
| **Admin** | https://phatphaponline.org/daoanh/admin/ |
| **VPS SSH** | root@158.220.106.183 |

---

*Last Updated: 2026-04-09*

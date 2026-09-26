# FEATURE_PLAN.md - Lộ Trình Phát Triển Hệ Thống Đạo Ảnh
**Phiên bản:** 2026-04-12  
**Dựa trên:** QA2.md + DILA_Structure_Report.md

---

## 📊 QA2 Findings Summary

| Category | Count | Status |
|----------|-------|--------|
| Critical | 3 | 🔴 P0: import requests, crawler, duplicates |
| Medium | 3 | 🟡 P1: HTML duplication, empty data |
| Low | 3 | 🟢 P2: Vietnamese, sources, caching |

---

## 🎯 Execution Roadmap (from QA2)

### P0: Critical - MUST FIX
| # | Task | File | Status |
|---|------|------|--------|
| 1 | Add `import requests` | app.py:8 | ✅ DONE |
| 2 | Create wiki_buddhist_crawler.py | src_python/crawler/ | ⏳ PENDING |
| 3 | Consolidate duplicate functions | app.py | ✅ BY DESIGN |

### P1: Medium - Should Fix
| # | Task | File | Status |
|---|------|------|--------|
| 1 | Static HTML deduplication | index.html | ⏳ PENDING |
| 2 | Populate staging/verification | data/ | ⏳ PENDING |
| 3 | Vietnamese translation pipeline | data/ | ⏳ PENDING |

### P2: Low - Nice to Have
| # | Task | File | Status |
|---|------|------|--------|
| 1 | Add more data sources (Wiki) | data/ | ⏳ PENDING |
| 2 | Standardize caching | app.py | ⏳ PENDING |
| 3 | API documentation updates | API_DOCS.md | ⏳ PENDING |

---

## 📋 Tóm Tắt So Sánh

| Module | DILA có | Đạo Ảnh có | Trạng thái |
|--------|---------|------------|------------|
| **Place Authority** | ✅ | ✅ | Hoàn thành |
| **Person Authority** | ✅ | ❌ | **Cần xây dựng** |
| **Time Authority** | ✅ | ❌ | **Cần xây dựng** |
| **Entity Linking** | ✅ | ❌ | **Cần xây dựng** |
| **Nexus Points** | ✅ | ❌ | **Cần xây dựng** |
| **GIS Map** | ✅ | ❌ | **Cần xây dựng** |
| **Timeline View** | ✅ | ❌ | **Cần xây dựng** |
| **RDF Export** | ✅ | ❌ | **Cần xây dựng** |
| **Lineage/ Genealogy** | ✅ | ⚠️ | **Cần nâng cấp** |

---

## 🎯 Phase 1: Authority Databases (Cao ưu tiên)

### 1.1 Person Authority Database

**Mục tiêu:** Xây dựng cơ sở dữ liệu chuẩn hóa cho các vị sư

**JSON Schema:**
```json
{
  "id": "P000001",
  "names": ["慧能", "六祖"],
  "pinyin": "huì néng",
  "birth": "+0638",
  "death": "+0713",
  "birth_place": "PL000001",
  "death_place": "PL000002",
  "teacher": ["P000002"],
  "student": ["P000003", "P000004"],
  "occupation": "禪宗",
  "lineage": "禪宗-南宗-六祖",
  "sources": ["六祖壇經", "景德傳燈錄"]
}
```

**API Endpoints cần tạo:**
| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/persons` | GET | List all persons (paginated) |
| `/api/persons/<id>` | GET | Get person details |
| `/api/persons/search?q=` | GET | Search by name |
| `/api/persons/<id>/lineage` | GET | Get teacher-student lineage |
| `/api/persons/<id>/timeline` | GET | Get timeline of life events |

### 1.2 Time Authority Database

**Mục tiêu:** Đối chiếu lịch Trung-Hoa-Nhật-Việt

**JSON Schema:**
```json
{
  "jdn": 2451545,
  "gregorian": "2009-01-01",
  "chinese": "2008-12-29",
  "vietnamese": "Mậu Tý-12-29",
  "dynasty": "清",
  "reign_year": "嘉慶14年"
}
```

**Chức năng:**
- Chuyển đổi giữa các hệ lịch
- Tính toán khoảng thời gian sống (life span)
- Lọc các vị sư theo thời kỳ

### 1.3 Entity Linking Engine

**Mục tiêu:** Tự động liên kết tên người, địa danh, thời gian trong văn bản

**Logic:**
1. Scan văn bản kinh văn
2. Nhận diện entity (person, place, time)
3. Match với Authority databases
4. Gắn URI/ID vào TEI markup

**Ví dụ:**
```xml
<!-- Trước -->
<persName>道安</persName>

<!-- Sau khi linking -->
<persName ref="http://purl.org/cbeta/person/A000001">道安</persName>
```

---

## 🎯 Phase 2: Visualization (Trung bình)

### 2.1 GIS Map (Leaflet + OpenStreetMap)

**Thư viện:** Leaflet.js (thay thế Google Maps)

**Tính năng:**
- Hiển thị tất cả địa danh trên bản đồ
- Click vào marker để xem chi tiết
- Filter theo: quốc gia, tỉnh thành, nguồn dữ liệu

**API mới:**
```python
@app.route('/api/places/map')
def api_places_map():
    # Return GeoJSON for Leaflet
    return jsonify({
        "type": "FeatureCollection",
        "features": [...]
    })
```

### 2.2 Timeline View

**Thư viện:** Vis.js Timeline hoặc custom D3.js

**Tính năng:**
- Hiển thị các sự kiện trên trục thời gian
- Range slider để lọc theo năm
- Click vào event để xem chi tiết

**Logic lọc theo thời gian:**
```python
def get_monks_in_period(start_year, end_year):
    """Lọc các vị sư sống trong khoảng thời gian"""
    return [
        p for p in persons
        if p.birth <= end_year and p.death >= start_year
    ]
```

### 2.3 Lineage Network (Nâng cấp)

**Cải tiến từ hệ thống hiện tại:**
- Thêm relationship type: `teacher` vs `student` vs `dharma_brother`
- Hiển thị z-index: thế hệ truyền thừa
- Animation khi expand/collapse

---

## 🎯 Phase 3: Advanced (Thấp)

### 3.1 RDF/OWL Export

**Định dạng:** Turtle (.ttl)

**Ví dụ output:**
```turtle
@prefix pth: <http://example.org/pth/> .
@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .

pth:P000001 a pth:Person ;
    pth:name "慧能" ;
    pth:birth "+0638" ;
    pth:death "+0713" ;
    pth:birthPlace pth:PL000001 ;
    pth:teacher pth:P000002 .

pth:PL000001 a pth:Place ;
    pth:name "新州" ;
    geo:lat "22.7" ;
    geo:long "110.9" .
```

### 3.2 TEI XML Import

**Mục đích:** Nhập kinh văn từ CBETA format

**Xử lý:**
1. Parse TEI XML
2. Extract text + metadata
3. Entity linking tự động
4. Lưu vào database

---

## 📦 Cấu Trúc File Mới

```
daoanh/
├── app.py                    # ✅ Đã có
├── data/
│   ├── places.json           # ✅ Đã có
│   ├── persons.json          # 🔄 Cần tạo
│   ├── times.json            # 🔄 Cần tạo
│   └── nexus.json            # 🔄 Cần tạo
├── src/
│   ├── python/
│   │   ├── etl/              # 🔄 Cần mở rộng
│   │   ├── api/              # 🔄 Cần thêm endpoints
│   │   └── visualization/    # 🔄 Cần tạo mới
│   └── js/
│       ├── map.js            # 🔄 Cần tạo
│       ├── timeline.js       # 🔄 Cần tạo
│       └── lineage.js        # 🔄 Cần nâng cấp
└── templates/                # 🔄 Cần thêm HTML
```

---

## ✅ Checklist Triển Khai

### Tuần 1-2: Person Authority
- [ ] Tạo JSON Schema cho Person
- [ ] Viết ETL script import person data
- [ ] Tạo API endpoints cho Person
- [ ] Tích hợp vào frontend

### Tuần 3-4: Time Authority + Timeline
- [ ] Tạo JSON Schema cho Time
- [ ] Implement date conversion (Gregorian ↔ Chinese ↔ JDN)
- [ ] Xây dựng Timeline View
- [ ] Lọc theo thời kỳ

### Tuần 5-6: GIS Map
- [ ] Tạo GeoJSON API
- [ ] Tích hợp Leaflet.js
- [ ] Thêm filters

### Tuần 7-8: Lineage + Entity Linking
- [ ] Nâng cấp network visualization
- [ ] Implement Entity Linking engine
- [ ] Extract Nexus Points

---

## 🔧 Tham Khảo

- **DILA_Structure_Report.md** - Chi tiết kỹ thuật từ DILA
- **AGENTS.md** - Ràng buộc và quy tắc phát triển
- **app.py** - API hiện tại để mở rộng

---

*Document created: 2026-04-10*
*For: OpenCode Build Agent*
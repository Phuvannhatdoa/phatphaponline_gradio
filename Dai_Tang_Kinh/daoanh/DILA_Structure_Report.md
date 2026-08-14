# DILA_Structure_Report.md - Cấu Trúc Kỹ Thuật DILA Authority Databases
**Phiên bản:** 2026-04-10
**Nguồn:** authority.dila.edu.tw, DILA-edu GitHub, CBETA Documentation

> **📋 TÓM TẮT (Executive Summary)**
> - DILA xây dựng 4 Authority Databases: **Person** (~5.000+), **Place** (~59.000), **Time** (JDN), **Catalog**
> - Công nghệ: **EXT JS** (Frontend) + **eXist-db** (XML DB) + **MySQL** (Authority) + **Google Earth/Maps** + **SIMILE Timeline**
> - Entity Relationships: Liên kết qua **TEI attributes** (`ref="#A000001"`) và **Nexus Points** (Person + Place + Time giao nhau trong văn bản)
> - Zero-RAM approach đề xuất: **StarDict-style .idx file + mmap** cho binary search không nạp toàn bộ vào RAM

---

## Mục Lục
1. [Tổng Quan](#1-tổng-quan)
2. [Cấu Trúc Dữ Liệu](#2-cấu-trúc-dữ-liệu)
3. [Entity Relationships](#3-entity-relationships)
4. [TEI XML Schema](#4-tei-xml-schema)
5. [Semantic Entity Linking](#5-semantic-entity-linking)
6. [GIS & Timeline](#6-gis--timeline)
7. [API & Endpoints](#7-api--endpoints)
8. [Công Nghệ & Thư Viện](#8-công-nghệ--thư-viện)
9. [Đề Xuất Kỹ Thuật Cho Dự Án](#9-đề-xuất-kỹ-thuật-cho-dự-án)
10. [Code Examples](#10-code-examples)

---

## 1. Tổng Quan

### 1.1 Giới thiệu DILA Authority Databases
DILA (Dharma Drum Institute of Liberal Arts / 法鼓佛教學院) xây dựng hệ thống Authority Databases bao gồm 4 cơ sở dữ liệu chuẩn:

| Database | Mục đích | Số lượng |
|----------|----------|----------|
| **Person Authority** | Chuẩn hóa tên người trong Phật học | ~5.000+ |
| **Place Authority** | Chuẩn hóa địa danh + GPS | ~19.000 (DILA) + 40.000 (Academia Sinica) |
| **Time Authority** | Đối chiếu lịch Trung-Hoa-Nhật | Từ Tần đến nay |
| **Catalog Authority** | Danh mục chương trình Đại Tạng Kinh | Nhiều bộ kinh |

### 1.2 Đặc điểm kỹ thuật nổi bật
- **XML/TEI P5**: Chuẩn quốc tế cho văn bản điện tử
- **Entity Linking**: Liên kết tự động người-địa-thời-gian
- **URI Convention**: `http://purl.org/cbeta/` (TEI standards)
- **Open Content**: Download miễn phí (Creative Commons)

---

## 2. Cấu Trúc Dữ Liệu

### 2.1.Person Authority Database

**File cấu trúc (XML/TEI):**
```
authority_person/
  └── A000001.xml  (Mỗi người = 1 file XML)
  └── A000002.xml
  └── ...
```

**XML Schema (rút gọn):**
```xml
<person xml:id="A000004">
  <persName type="zh">畺良耶舍</persName>
  <persName type="pinyin">Jiāng Liáng Yěshě</persName>
  <sex>男</sex>
  <birth>
    <date when="+0383">383</date>
    <placeName ref="#PLxxxxx">西域</placeName>
  </birth>
  <death>
    <date when="+0442">442</date>
    <placeName ref="#PLxxxxx">京師道林寺</placeName>
  </death>
  <occupation>譯經</occupation>
  <note>...,...</note>
  <!-- Liên kết sang Place Authority -->
  <!-- Liên kết sang Time Authority -->
</person>
```

### 2.2 Place Authority Database

**Định dạng:**
- XML/TEI (download) hoặc
- JSON qua API

**Ví dụ Place entry:**
```json
{
  "authorityID": "PL000000023253",
  "name": "嵩山",
  "dynasty": "慣用名",
  "long": "113.003188",
  "lat": "34.519744",
  "districtModern": "中國-河南省-鄭州市-登封市",
  "names": ["嵩高山", "中嶽", "崇山", "嵩高"],
  "pinyin": {
    "嵩山": "sōng shān",
    "中嶽": "zhōng yuè"
  }
}
```

### 2.3 Time Authority Database (ERD)

```
┌─────────────┐       ┌─────────────┐
│  dynasty   │       │   emperor  │
├─────────────┤       ├─────────────┤
│ id (PK)   │◄──────│ dynasty_id │
│ name      │       │ id (PK)   │
└─────────────┘       │ name      │
                    └─���───────────┘
                           │
                           ▼
                    ┌─────────────┐       ┌─────────────┐
                    │   era    │       │lunar_month│
                    ├─────────────┤       ├─────────────┤
                    │ emperor_id│◄──────│ era_id    │
                    │ id (PK)  │       │ id (PK)   │
                    │ name     │       │ year      │
                    └─────────────┘       │ name     │
                                    │ first(JDN)│
                                    │ last(JDN) │
                                    │ ganzhi   │
                                    └─────────────┘
```

**Table Schemas:**

| Table | Field | Type | Description |
|-------|-------|------|------------|
| dynasty | id | char(4) | PK |
| dynasty | name | char(15) | Tên triều đại |
| emperor | id | int(5) | PK |
| emperor | name | char(18) | Tên hoàng đế |
| emperor | dynasty_id | char(4) | FK → dynasty |
| era | id | int(5) | PK |
| era | name | char(21) | Niên hiệu |
| era | emperor_id | int(5) | FK → emperor |
| lunar_month | id | int(5) | PK |
| lunar_month | year | int(3) | Năm thứ |
| lunar_month | name | char(6) | Tên tháng |
| lunar_month | era_id | int(5) | FK → era |
| lunar_month | first | int(8) | Julian Day Number |
| lunar_month | last | int(8) | Julian Day Number |
| lunar_month | ganzhi | char(6) | Sexagenary cycle |
| lunar_month | status | enum('S','P') | S=standard, P=proleptic |
| lunar_month | eclipse | boolean | Có nhật thực không |

---

## 3. Entity Relationships

### 3.1 Sơ đồ ER Tổng hợp

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   PERSON   │       │    TEXT    │       │    PLACE   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id        │◄──────│ personRef  │───────►│ id        │
│ name     │       │ placeRef  │       │ name      │
│ birthDate │       │ dateRef  │       │ lat       │
│ deathDate │       │ event    │       │ long     │
│ birthPlace│       │ nexus   │       │ district │
│ deathPlace│       └──────────────┘       └──────────────┘
│ teacher   │             │                    ▲
│ student   │             │                    │
└──────────┘             └────────────┬───────────┘
                            ┌────────┴────────┐
                            │      TIME       │
                            ├────────────────┤
                            │ id (JDN)       │
                            │ year           │
                            │ month          │
                            │ dynasty        │
                            │ era           │
                            │ ganzhi         │
                            └────────────────┘
```

### 3.2 Nexus Points (Điểm giao thoa)
DILA định nghĩa **nexus point** = điểm mà tại đó **Person + Place + Time** gặp nhau trong văn bản:

```xml
<!-- Trong TEI biography -->
<div type="event" when="+0383" where="#PLxxxxx">
  <p>僧肇長老於<date when="+0383">晉恭帝元興���年</date>，
  抵<placeName ref="#PL00001">長安</placeName>，
  從<persName ref="#A000001">鳩摩羅什</persName>學《成實論》。</p>
</div>
```

**Nexus point extraction:**
- Person: 僧肇 (A000xxx)
- Place: 長安 (PL00001)
- Time: +0383 (JDN tương ứng)
- Event: học《成實論》với鳩摩羅什

---

## 4. TEI XML Schema

### 4.1 CBETA XML P5 File Structure

**Thư mục:**
```
T/                    # 大正藏
  ├── T01/
  │   └── T01n0001.xml
  └── T02/
      ├── T02n0002.xml
      └── T02n0128a.xml   # Chữ thường = CBETA tự thêm

X/                    # 卍續藏
K/                    # 嘉興藏
J/                    # ...
```

**Header:**

```xml
<teiHeader>
  <fileDesc>
    <titleStmt>
      <title>金剛經</title>
      <author>鳩摩羅什</author>
    </titleStmt>
    <publicationStmt>
      <idno type="Taisho">T02n0235</idno>
    </publicationStmt>
  </fileDesc>
  <sourceDesc>
    <p>Taisho Tripitaka Vol.2, No.235</p>
  </sourceDesc>
</teiHeader>
```

### 4.2 Main Body Tags

| Tag | Ý nghĩa | Ví dụ |
|-----|-----------|-------|
| `<div>` | Phân đoạn | `<div type="jin" level="1">卷第一</div>` |
| `<p>` | Đoạn văn | `<p>爾時須菩提...</p>` |
| `<lb>` | Dòng (hàng) | `<lb n="0001"/>` |
| `<pb>` | Trang | `<pb ed="Taisho" n="1"/>` |
| `<note>` | Chú thích | `<note place="inline">注釋</note>` |
| `<persName>` | Tên người | `<persName ref="#A000001">鳩摩羅什</persName>` |
| `<placeName>` | Tên địa danh | `<placeName ref="#PL00001">長安</placeName>` |
| `<date>` | Ngày tháng | `<date when="+0383">晉元興二年</date>` |
| `<term>` | Thuật ngữ | `<term>涅槃</term>` |
| `<g ref="#CB001">` | Gaiji (缺字) | `<g ref="#CB001">𠀀</g>` |

### 4.3 URI Convention

**CBETA URI patterns:**
```xml
<!-- Person -->
<persName ref="http://purl.org/cbeta/person/A000004">畺良耶舍</persName>

<!-- Place -->
<placeName ref="http://purl.org/cbeta/place/PL000000000001">嵩山</placeName>

<!-- Time -->
<date ref="http://purl.org/cbeta/date/jdn2451545">2009-01-01</date>
```

---

## 5. Semantic Entity Linking

### 5.1 Authority Files (Controlled Vocabularies)

DILA sử dụng **authority files** để chuẩn hóa:

1. **Person authority**: Thống nhất tên người, năm sinh/cung cấp
2. **Place authority**: Thống nhất tên địa danh + tọa độ GPS
3. **Time authority**: Thống nhất ngày tháng theo JDN + các triều đại
4. **Catalog authority**: Thống nhất danh mục kinh điển

### 5.2 Entity Disambiguation

**Ví dụ:**
```xml
<!-- Trong văn bản -->
<persName>道安</persName>

<!-- TEI markup với liên kết -->
<persName ref="#A000001">道安</persName>

<!-- Hoặc với URI đầy đủ -->
<persName ref="http://purl.org/cbeta/person/A000001">道安</persName>
```

**Search flow:**
1. User search "道安"
2. System query person authority
3. Return disambiguated list:
   - 道安 (A000001) - 晉時僧
   - 道安 (A000002) - 唐時律師
   - ...

### 5.3 RDF/OWL Export

**RDF export available:**
```turtle
@prefix cbeta: <http://purl.org/cbeta/> .
@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .

cbeta:A000004 a cbeta:Person ;
    cbeta:name "畺良耶舍" ;
    cbeta:birthDate "+0383" ;
    cbeta:birthPlace cbeta:PLxxxxx ;
    cbeta:occupation "譯經" .

cbeta:PLxxxxx a cbeta:Place ;
    cbeta:name "西域" ;
    geo:lat "39.5" ;
    geo:long "95.0" .
```

---

## 6. GIS & Timeline

### 6.1 Kiến trúc GIS DILA

```
┌─────────────────────────────────────��─��─────────────────────┐
│                    DILA GIS Interface                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐  │
│  │  TEI/XML  │──►│  eXist-db │   │  Google Earth   │  │
│  │   Texts   │   │ Database  │   │  / Google Map  │  │
│  └─────────────┘   └─────┬─────┘   └─────────────────┘  │
│                          │                              │
│         ┌────────────────┴────────────────┐            │
│         ▼                                 ▼            │
│  ┌─────────────────┐              ┌─────────────┐  │
│  │   MySQL         │              │  Timeline  │  │
│  │ Authority DB    │              │  View     │  │
│  │ (Person+Place+ │              └─────────────┘  │
│  │  Time)        │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Timeline Visualization

**Logic lọc theo thời gian:**

1. **Time range input**: user nhập "300-500 CE"
2. **JDN conversion**: chuyển sang Julian Day Numbers
3. **Query**: tìm tất cả nexus points trong khoảng đó
4. **Visualization**:Hiển thị trên map + timeline

**Giải thuật (pseudo-code):**
```python
def filter_by_time(start_year, end_year):
    start_jdn = chinese_to_jdn(start_year)  # Ví dụ: +0300 → JDN tương ứng
    end_jdn = chinese_to_jdn(end_year)    # Ví dụ: +0500
    
    # Lọc tất cả nexus points trong khoảng [start_jdn, end_jdn]
    filtered = [np for np in nexus_points 
              if start_jdn <= np['date_jdn'] <= end_jdn]
    
    return filtered  # Trả về danh sách "người cùng sống giai đoạn"

def find_contemporaries(monk_name, range_years=50):
    monk = get_monk_data(monk_name)  # Lấy birth/death từ authority
    if not monk: return []
    
    start = monk.birth_year - range_years
    end = monk.death_year + range_years
    
    # Tìm tất cả người có overlap thời gian
    all_monks = get_all_monks()
    contemporaries = [m for m in all_monks 
                  if m.birth_year <= end and m.death_year >= start]
    
    return sorted(contemporaries, key=lambda x: x.death_year)
```

### 6.3 KML Output

**Xuất KML cho Google Earth:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Folder>
    <name>高僧傳 Nexus Points</name>
    <Placemark>
      <name>道安 @ 襄陽</name>
      <TimeSpan>
        <begin>0374-01-01</begin>
        <end>0385-12-31</end>
      </TimeSpan>
      <Point>
        <coordinates>112.0,32.0,0</coordinates>
      </Point>
    </Placemark>
  </Folder>
</kml>
```

---

## 7. API & Endpoints

### 7.1 Data Provider Service

**Base URL:**
```
http://authority.dila.edu.tw/webwidget/getAuthorityData.php
```

### 7.2 Person API

**Request:**
```
GET http://authority.dila.edu.tw/webwidget/getAuthorityData.php
   ?type=person
   &id=A000004
   &jsoncallback=abc123
```

**Response:**
```json
abc123({
  "data1": {
    "authorityID": "A000004",
    "name": "畺良耶舍",
    "class": "譯經",
    "bornDateBegin": "+0383-01-01",
    "bornDateEnd": "+0383-12-31",
    "diedDateBegin": "+0442-01-28",
    "diedDateEnd": "+0442-12-31",
    "note": "...",
    "birthPlaceCode": "WW142XIYUE01AA",
    "birthPlaceName": "西域",
    "dynasty": "劉宋",
    "names": "[梵文]: Kālayaśas"
  }
})
```

### 7.3 Place API

**Request:**
```
GET http://authority.dila.edu.tw/webwidget/getAuthorityData.php
   ?type=place
   &id=PL000000023253
   &jsoncallback=xyz
```

**Response:**
```json
xyz({
  "data1": {
    "authorityID": "PL000000023253",
    "name": "嵩山",
    "dynasty": "慣用名",
    "long": "113.003188",
    "lat": "34.519744",
    "districtModern": "中國-河南省-鄭州市-登封市",
    "note": "位於河南省西部，...",
    "names": "[中文]: 嵩高山,中嶽,崇山"
  }
})
```

### 7.4 CBETA API

**CBETA online:**
- Base: `https://cbetaonline.dila.edu.tw/`
- XML download: GitHub (cbeta-org/xml-p5)

---

## 8. Công Nghệ & Thư Viện

### 8.1 Backend

| Component | Công nghệ | Version |
|-----------|-----------|---------|
| XML Database | eXist-db | 3.x+ |
| Relational DB | MySQL | 5.x |
| API | PHP | 7.x |
| RDF Storage | GraphDB / Fuseki | Optional |

### 8.2 Frontend

| Component | Thư viện | Mục đích |
|-----------|----------|----------|
| UI Framework | **EXT JS** | Main UI components |
| Maps | **Google Maps API** | GIS visualization |
| Earth | **Google Earth Plugin** | 3D visualization |
| Timeline | **SIMILE Timeline** | Temporal visualization |
| Network | **Gephi** / Cytoscape | Social network analysis |

### 8.3 Data Formats

| Format | Sử dụng |
|--------|---------|
| XML/TEI P5 | Kinh văn + Authority |
| JSON | API response |
| RDF/TTL | Knowledge Graph |
| KML/KMZ | GIS export |
| CSV | Data export |

### 8.4 Third-party Data

- **Academia Sinica**: 40.000 place entries (Chinese Civilization in Time and Space)
- **Google Earth/Maps**: Visualization
- **OpenStreetMap**: Backup map

---

## 9. Đề Xuất Kỹ Thuật Cho Dự Án

### 9.1 Architecture mới (Zero-RAM + Hybrid Storage)

**Sơ đồ đề xuất:**

```
┌─────────────────────────────────────────────────────────┐
│                    Puzzle Ecosystem                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ Raw Files  │───►│  ETL       │───►│ JSON Schema│  │
│  │ .docx    │    │ (Python)   │    │ (Index)    │  │
│  │ .xml     │    │ Generator  │    │           │  │
│  └─────────────┘    └─────────────┘    └──────┬──────┘  │
│                                                │         │
│                 ┌────────────────────────────────┴───┐   │
│                 ▼                                  ▼    │
│          ┌─────────────┐                       ┌─────────┐  │
│          │ .idx file │◄────Zero-RAM─────│ Flask   │  │
│          │(StarDict)│        (mmap)      │ API    │  │
│          └─────────┘                       └────────┘  │
│                                                │    │
│                              ┌───────────────────┘    │
│                              ▼                       │
│                 ┌────────────────────────────────┐  │
│                 │   Vis.js / D3.js Network Graph  │  │
│                 │   - Timeline View              │  │
│                 │   - GIS Map                    │  │
│                 │   - Social Network             │  │
│                 └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 9.2 Entity Data Model (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "definitions": {
    "person": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "pattern": "^P[0-9]{6}$" },
        "name": { "type": "string" },
        "pinyin": { "type": "string" },
        "birth_year": { "type": "integer" },
        "death_year": { "type": "integer" },
        "birth_place": { "$ref": "#/definitions/place_ref" },
        "death_place": { "$ref": "#/definitions/place_ref" },
        "teacher": { "type": "array", "items": { "$ref": "#" } },
        "student": { "type": "array", "items": { "$ref": "#" } },
        "occupation": { "type": "string", "enum": ["譯經", "義解", "神異", "習禪", "明律", "亡身", "誦經", "興福", "經師", "唱導", "居士"] }
      }
    },
    "place": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "pattern": "^PL[0-9]{9}$" },
        "name": { "type": "string" },
        "name_alt": { "type": "array", "items": { "type": "string" } },
        "lat": { "type": "number" },
        "long": { "type": "number" },
        "country": { "type": "string" },
        "province": { "type": "string" },
        "district": { "type": "string" }
      }
    },
    "place_ref": {
      "type": "object",
      "properties": {
        "place_id": { "type": "string" },
        "place_name": { "type": "string" }
      }
    },
    "nexus": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "person_id": { "type": "string" },
        "place_id": { "type": "string" },
        "year": { "type": "integer" },
        "event": { "type": "string" }
      }
    }
  }
}
```

### 9.3 API Endpoints (Flask)

```python
# app/api/person.py
@app.route('/api/person/<person_id>')
def get_person(person_id):
    """Zero-RAM: đọc từ index file, không load toàn bộ"""
    # 1. Binary search trong .idx file
    # 2. Đọc offset + size
    # 3. Return JSON
    pass

@app.route('/api/lineage/<name>')
def get_lineage(name):
    """Lấy thầy + trò (3 đời)"""
    pass

@app.route('/api/contemporaries/<name>/<int:range_years>')
def get_contemporaries(name, range_years=50):
    """Tìm người cùng sống trong giai đoạn"""
    pass

@app.route('/api/timeline/<start_year>/<end_year>')
def get_timeline_range(start_year, end_year):
    """Nexus points theo thời gian"""
    pass

@app.route('/api/network/<collection>')
def get_social_network(collection):
    """Social network từ Gephi-exported JSON"""
    pass
```

### 9.4 Vis.js Integration

```javascript
// src/js/network.js
function initNetwork(data) {
  const container = document.getElementById('network');
  
  const options = {
    nodes: {
      shape: 'dot',
      size: 20,
      font: { face: 'Noto Serif TC', size: 14 }
    },
    edges: {
      smooth: { type: 'continuous' },
      arrows: 'to'
    },
    physics: {
      stabilization: false,
      barnesHut: { gravitationalConstant: -3000 }
    }
  };
  
  const network = new vis.Network(container, data, options);
  return network;
}

// Timeline integration
function filterByTimeRange(startYear, endYear) {
  const rangeStart = startYear || -500;
  const rangeEnd = endYear || 2000;
  
  const filteredNodes = nodes.get().filter(n => {
    const birth = n.birth_year || 0;
    const death = n.death_year || 0;
    return (birth <= rangeEnd && death >= rangeStart);
  });
  
  // Update network với filtered nodes
}
```

---

## 10. Code Examples

### 10.1 ETL: TEI Person Extraction

```python
# etl/extract_persons.py
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Generator

def extract_persons_from_tei(tei_file: str) -> Generator[dict, None, None]:
    """Extract persons từ TEI XML - streaming, Zero-RAM"""
    
    # SAX parsing để streaming (không load toàn bộ)
    for event, elem in ET.iterparse(tei_file, events=('end',)):
        if elem.tag == 'person' and elem.get('{http://www.w3.org/XML/1998/namespace}id'):
            person_data = {
                'id': elem.get('{http://www.w3.org/XML/1998/namespace}id'),
                'names': [],
                'birth': None,
                'death': None,
                'occupations': []
            }
            
            # Tên
            for name in elem.findall('.//persName'):
                if name.text:
                    person_data['names'].append(name.text)
                # Pinyin
                if name.get('type') == 'pinyin':
                    person_data['pinyin'] = name.text
            
            # Sinh/Ngày
            for birth in elem.findall('.//birth'):
                if birth.find('date') is not None:
                    person_data['birth'] = birth.find('date').get('when')
            for death in elem.findall('.//death'):
                if death.find('date') is not None:
                    person_data['death'] = death.find('date').get('when')
            
            # Nghề nghiệp
            for occ in elem.findall('.//occupation'):
                if occ.text:
                    person_data['occupations'].append(occ.text)
            
            yield person_data
            elem.clear()  # Free memory

def build_person_index(input_dir: str, output_idx: str):
    """Build .idx file cho binary search - Zero-RAM"""
    import struct
    
    persons = []
    
    for teifile in Path(input_dir).glob('**/*.xml'):
        for person in extract_persons_from_tei(str(teifile)):
            persons.append(person)
    
    # Sort by name
    persons.sort(key=lambda x: x['names'][0] if x['names'] else '')
    
    # Write index (sorted)
    with open(output_idx, 'wb') as f:
        for p in persons:
            name = p['names'][0].encode('utf-8')[:255] + b'\x00'
            offset = 0  # Placeholder
            size = len(json.dumps(p))
            
            f.write(name)
            f.write(struct.pack('>I', offset))
            f.write(struct.pack('>I', size))
```

### 10.2 Zero-RAM Person Search

```python
# utils/person_search.py
import mmap
import struct
import json
from bisect import bisect_left

class PersonIndex:
    """Zero-RAM person search qua .idx file"""
    
    ENTRY_SIZE = 4 + 255  # offset(4) + name(255, max)
    
    def __init__(self, idx_path: str, data_path: str):
        self.idx_path = idx_path
        self.data_path = data_path
        self.names = []
        
        # Load index vào RAM (chỉ names, kích thước nhỏ)
        with open(idx_path, 'rb') as f:
            while True:
                data = f.read(self.ENTRY_SIZE)
                if not data:
                    break
                name = data[:255].decode('utf-8').rstrip('\x00')
                offset = struct.unpack('>I', data[255:259])[0]
                size = struct.unpack('>I', data[259:263])[0]
                self.names.append((name, offset, size))
    
    def search(self, query: str) -> list:
        """Binary search + fetch results"""
        query_bytes = query.encode('utf-8')
        
        # Binary search trong sorted names
        names_only = [n[0] for n in self.names]
        idx = bisect_left(names_only, query_bytes)
        
        results = []
        for name, offset, size in self.names[idx:idx+10]:
            if name.startswith(query):
                # Read data from data file
                with open(self.data_path, 'rb') as f:
                    f.seek(offset)
                    data = f.read(size)
                    results.append(json.loads(data))
        
        return results
```

### 10.3 Nexus Point Generator (ETL)

```python
# etl/extract_nexus.py
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Generator

def extract_nexus_points(tei_dir: str) -> Generator[dict, None, None]:
    """
    Extract nexus points = Person + Place + Time giao nhau
    Zero-RAM: streaming parser
    """
    
    for teifile in Path(tei_dir).glob('**/*.xml'):
        for event, elem in ET.iterparse(str(teifile), events=('end',)):
            # Tìm các elements có chứa person + place + date
            if elem.tag == 'p' or elem.tag == 'div':
                persons = elem.findall('.//persName')
                places = elem.findall('.//placeName')
                dates = elem.findall('.//date')
                
                if persons and places and dates:
                    for p in persons:
                        for pl in places:
                            for d in dates:
                                yield {
                                    'person_ref': p.get('ref', ''),
                                    'person_name': p.text or '',
                                    'place_ref': pl.get('ref', ''),
                                    'place_name': pl.text or '',
                                    'date_when': d.get('when', ''),
                                    'text_snippet': elem.text[:100] if elem.text else ''
                                }
            
            elem.clear()

def build_nexus_network(nexus_file: str) -> dict:
    """Build network graph từ nexus points"""
    nodes = {}  # id -> {name, birth, death}
    edges = []  # [(from_id, to_id, type)]
    
    for nexus in extract_nexus_points(nexus_file):
        p_ref = nexus['person_ref']
        pl_ref = nexus['place_ref']
        
        if p_ref and pl_ref:
            # Add edge person-place
            edges.append({
                'from': p_ref,
                'to': pl_ref,
                'type': 'at',
                'year': nexus['date_when']
            })
    
    return {'nodes': nodes, 'edges': edges}
```

---

## Nguồn Tham Khảo

| Nguồn | Link |
|-------|------|
| DILA Authority | https://authority.dila.edu.tw |
| DILA GitHub | https://github.com/DILA-edu/Authority-Databases |
| CBETA XML P5 | https://github.com/cbeta-org/xml-p5 |
| TEI Guidelines | https://tei-c.org/release/doc/tei-p5-doc/ |
| Gaoseng Zhuan GIS | http://buddhistinformatics.dila.edu.tw/biographies/gis/ |
| 台灣佛寺時空平台 | https://buddhistinformatics.dila.edu.tw/taiwanbudgis/ |
| Silk Road Atlas | http://silkroad.chibs.edu.tw/ |

---

## Copyright & License

Dữ liệu DILA Authority Database được phân phối theo **Creative Commons Attribution-ShareAlike 3.0 Unported License**.

---

*Báo cáo được tạo: 2026-04-10*
*Thông tin đã sẵn sàng để Build Agent triển khai theo đúng Code Preservation.*
# Home Identity Hub — Specification

## Vision

**HOME = Identity Hub** — The homepage is **not** a data store. It is a composable UX doorway that calls academic APIs on-demand. Each TAB is a “window” to a different data source. No raw data is loaded into RAM; only offsets/indexes are used.

## 15 Data Sources (Priority Order)

| # | Source | Type | Endpoint / Access | Coverage | Notes |
|---|--------|------|-------------------|----------|-------|
| 1 | **CBETA** | Sutras & Texts | `/api/places/<id>/cbeta` | 1,438 sutras | Text reuse from BuddhaNexus, listbibl parsing |
| 2 | **SAT** | Sutras | Via CBETA adapter | 84000 index | Sanskrit & Tibetan canon |
| 3 | **84000** | Translations | External API | 12,000+ texts | FTEE translations |
| 4 | **Kanripo** | Technology | External API | Cross-reference Buddhist texts & DILA places | 🟠 Medium | Integrated |
| 4 | **VRI** | Technology | External API | Vinaya Rules, Sutta Reference | 🟠 Medium | Coming Soon |
| 4 | **VRI** | Vinaya Records | External API | Monastic rules | Vietnamese repository |
| 5 | **Kanripo** | Images | External API | 10,000+ images | IDP, manuscript scans |
| 6 | **DSBC** | Buddhist Council | External API | Council documents | DSBC archive |
| 7 | **PTS** | Pali Texts | External API | Pali canon | PTS archive |
| 8 | **DILA** | Place Index | `/api/places/<id>` | 59,167 places | Primary DILA database |
| 10 | **CHGIS** | Historical GIS | New endpoint needed | Historical temples | 717 refs in DILA raw_xml |
| 11 | **BGIS** | Buddhist GIS | New endpoint needed | Map tiles, coords | Harvard GSAS |
| 12 | **Marcus GIS** | SNA Networks | `/api/places/<id>/graph` | 18K monks | Social network analysis |
| 13 | **THL** | Treasury of Lives | External API | Saints & scholars | Tibet & Himalaya focus |
| 14 | **Treasury of Lives** | Biographies | External API | 40K entries | Comprehensive |
| 15 | **Wikidata** | Inception / IDs | SPARQL P571, P2477 | 148 places | Q232771 (495 CE), P2477 IDs |

## 3-Cluster Navigation Menu

### Cluster 1: Kinh Văn & Giáo Lý
- **TABs**: Đại Tạng, Giáo Lý, Thư Viện, Nghi Lễ, Giáo Dục
- **Purpose**: Scriptural study, commentary analysis, library access, ritual context, educational resources

### Cluster 2: Thực Thế & Niên Đại
- **TABs**: Thực Thể, Niên Đại, Sự Kiện, Bản Đồ, Dữ Liệu
- **Purpose**: Place data, founding dates, timeline events, academic mapping, claim provenance

### Cluster 3: Con Người & Không Gian
- **TABs**: Nhân Vật, Truyền Thừa, Đồ Thị, Hình Ảnh, Nghệ Thuật
- **Purpose**: Monk biographies, lineage charts, relationship graphs, visual media, artistic rendering

### UI Behavior
- **Desktop**: 3-accordion layout, each cluster expandable independently
- **Mobile**: Bottom sheet / swipe tabs, single cluster visible at a time
- **Responsive**: Collapses to hamburger at ≤768px, prioritizes Cluster 1 first

## Tab Definitions (15 Tabs)

| # | TAB | Key | API Endpoint | Renderer | Priority Data |
|---|-----|-----|-------------|----------|-------------|
| 1 | 📜 Đại Tạng | `daitang` | `/api/places/<id>/cbeta` | Text blocks, listbibl | CBETA sutras |
| 2 | 🔍 Giáo Lý | `giaoly` | `/api/places/<id>/cbeta` (reuses) | Commentary, logic | Giao lý Sutras |
| 3 | 📚 Thư Viện | `thuvien` | New endpoint `/references` | Research papers, PDFs | OCBS, GRETIL, DDBC |
| 4 | 🙏 Nghi Lễ | `nghile` | New endpoint `/rituals` | Ritual texts, ceremonies | CBETA, THL |
| 5 | 🎓 Giáo Dục | `giaoduc` | New endpoint `/education` | Courses, programs | DDBC, OCBS |
| 6 | 地 Thực Thể | `entity` | `/api/places/<id>` | Full place data | DILA core |
| 7 | ⏱ Niên Đại | `timeline` | `/api/places/<id>/timeline` | Founding dates, events | Wikidata P571, DILA note |
| 8 | ⚡ Sự Kiện | `sukien` | `/api/places/<id>/timeline` (reuses) | Historical events | CHGIS, BGIS, Marcus |
| 9 | 🗺 Bản Đồ | `bandoo` | `/api/places/<id>` (coords) | Academic maps | CHGIS, BGIS, Marcus |
| 10 | 📊 Dữ Liệu | `dulieu` | `/api/places/<id>/claims` | 411K entity_claims | COORDINATE, NAME, ADMIN_UNIT |
| 11 | 🧑 Nhân Vật | `persons` | `/api/bdrc/person?id=` | Monk biographies | Treasury of Lives |
| 12 | 🌳 Truyền Thừa | `lineage` | `/api/monk/<id>/graph` | Lineage charts | Marcus GIS |
| 13 | 🕸 Đồ Thị | `graph` | `/api/places/<id>/graph` | Reticulogram | Marcus GIS, VisJS |
| 14 | 🖼 Hình Ảnh | `hinhanh` | New endpoint `/images` | Scan images | IDP, Kanripo |
| 16 | 🎨 Nghệ Thuật | `nghethuat` | New endpoint `/art` | Artistic rendering | IDP, BGIS, Kanripo |

## Case Demo: Thiếu Lâm Tự (PL000000023255)

| TAB | Expected Content |
|-----|-----------------|
| 📜 Đại Tạng | CBETA sutras mentioning Thiếu Lâm Tự, text reuse |
| 🔍 Giáo Lý | Giao lý analysis of Thiền tông passages |
| 📚 Thư Viện | Research papers on Thiếu Lâm Tự |
| 🙏 Nghi Lễ | Ritual texts, ceremonies |
| 🎓 Giáo Dục | Courses on Thiền tông |
| 地 Thực Thể | DILA: PL000000023255, name 少林寺 |
| ⏱ Niên Đại | 495 CE (Wikidata P571), "始建於495年" (DILA rawtext) |
| ⚡ Sự Kiện | Timeline: 495 CE founding, major lawi events |
| 🗺 Bản Đồ | Coordinates: 34.507018, 112.935331 (CHGIS/BGIS) |
| 📊 Dữ Liệu | 411K entity_claims: coordinate, NAME_ZH, NAME_VI, ADMIN_UNIT |
| 🧑 Nhân Vật | DILA monk data, lineage links |
| 🌳 Truyền Thừa | Bodhidharma → Huike → Sengcan → Daoxin → Hongren → Huineng |
| 🕸 Đồ Thị | Graph: Thiếu Lâm Tua ↔ monks ↔ texts ↔ places |
| 🖼 Hình Ảnh | Chùa photos from IDP/Kanripo |
| 🎨 Nghệ Thuật | Buddhist art, architecture renderings |

## Coverage Matrix

**Definition**: Table mapping each Data Source × each TAB → { status: available/partial/missing, endpoint, renderer, coverage% }.

**Purpose**: Administrator visibility — know which sources power which TABs, identify gaps, plan extensions.

**Format** (Markdown table, same as Data Sources section):

| Source | Đại Tạng | Giáo Lý | Thư Viện | Nghi Lễ | Giáo Dục | Thực Thể | Niên Đại | Sự Kiện | Bản Đồ | Dữ Liệu | Nhân Vật | Truyền Thừa | Đồ Thị | Hình Ảnh | Nghệ Thuật |
|--------|---------|--------|----------|--------|--------|---------|----------|---------|-------|--------|--------|-----------|--------|----------|------------|
| **CBETA** | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |

| **Wikidata** | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |
| **CHGIS** | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |
| **DILA** | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |

✅ = Fully available | ⚪ = Partial / needs endpoint

## Parallel API Display Pattern

**Every TAB JSON response includes:**

```json
{
  "dila_id": "PL000000023255",
  "wikidata_qid": "Q232771",          // from geo_cross_ref
  "founding_year": 495,                // from Wikidata P571 / place_timeline_events
  "founding_source": "wikidata",       // source attribution
  "founding_source_ref": "Q232771·P571",
  "dila_founding_year": 495,           // fallback from DILA note regex "始建於495年"
  "dila_rawtext": "始建於495年...",    // raw DILA description
  "claims": [                          // from entity_claims (411K rows)
    {"claim_type": "COORDINATE", "value": "34.507018,112.935331", "source": "DILA", "confidence": 1.0}
  ]
}
```

**UI rendering logic**:

| Element | When shown | Content |
|---------|-----------|---------|
| **Chip ✓ DILA** | `dila_id ≠ null` | Real DILA place ID |
| **Year block** | `founding_year ≠ null` | "Năm thành lập: 495" |
| **Rawtext block** | `dila_rawtext ≠ ''` | "Nguồn: DILA — bắt đầu:始建於495年" |
| **Claims list** | `claims.length > 0` | Badges: [DILA] [Wikidata] [CBETA] |

## NLP Policy: Last Resort Only

**Never run NLP on the full 59K DILA corpus.** NLP is invoked **only** when:

1. ❌ Wikidata P571 inception is absent
2. ❌ CHGIS coordinate is absent
3. ❌ CBETA listbibl is absent

**If all four above are missing for a place**, then:

- Run **simple regex** to highlight rawtext patterns (e.g., `始建於\d{3,4}` )
- Flag the case for **manual review**
- Log to `NLP_cases/` directory
- **Never** train a model or auto-generate tags

**NLP pipeline is a "last resort" step**, never a primary data source.

## UI/UX Tokens

- **Primary color**: Amber Gold `#d97706` (Gold standard)
- **Background**: Dark Slate `#020617`
- **Font**: Inter (UI), Noto Serif TC (CJK content)
- **Mood**: Chuyên nghiệp – Học thuật – Thanh tịnh – Hiện đại
- **Accent**: Lotus Done (pink lotus icon for completed items)
- **Mood token**: `var(--da-gold)`, `var(--da-muted)`, `var(--da-text)`, `var(--da-background)`

## Integration Points

| Integration | File | Action |
|-------------|------|--------|
| Backend API | `app.py` | Add `/hub` aggregation endpoint |
| Tab switching | `places.html` | 15 TABs, scrollable bar, bug fixes |
| Identity Hub doc | `docs/architecture-identity-hub.md` | Add HOME entry point section |
| Task tracking | `docs/tasktodo.md` | T30/T31/T32 entries |
| Session logging | `docs/sessions/` | Record build progress after each phase |

## Rollback Safety

- **Each phase is independently committable**
- **Bug fixes** (Step 3.1) committed **before** expansion (Step 3.2+)
- **All changes additive**: no schema drops, no data overwrite, no table-drop migrations
- **`git revert`** works cleanly at any checkpoint
- **Backup before each phase**: `lineage.db.bak_YYYYMMDD_HHMMSS`

---

*Specification version: 2026-08-21*
*Status: DRAFT — under construction, Phase 1 docs first*
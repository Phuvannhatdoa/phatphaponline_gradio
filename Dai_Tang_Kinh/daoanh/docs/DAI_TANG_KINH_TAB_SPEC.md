# Đại Tạng Kinh Tab — Complete Technical + UI/UX Specification

**Version**: 2.0 (Complete)  
**Date**: 2026-09-02  
**Status**: Ready for Development

---

## 1. Project Overview

**Purpose**: Integrated Buddhist text gateway with AI translation, semantic search, and entity linking

**Core Features**:
- 📜 Reference citations from DILA Authority + CBETA
- 📖 AI-powered Han-Vietnamese translation (Groq LLM)
- 🔗 Relationship graph visualization
- 🤖 DeepSearch (semantic ranking)
- ❓ Q&A with RAG (retrieval-augmented generation)
- 📤 Citation export (BibTeX/Chicago/APA)

---

## 2. User Interface Design

### 2.1 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  HEADER: [Search Box] + ⚡ LIVE MODE                    │
├──────────────┬──────────────────────────────────────────┤
│   SIDEBAR    │  MAIN PANEL                              │
│   (340px)    │  ┌──────────────────────────────────┐   │
│              │  │ TAB NAV (6 tabs):                 │   │
│  • Entity    │  │ 📜 References | 📖 Full Text     │   │
│    Card      │  │ 🔗 Graph | 🤖 DeepSearch | ❓ Q&A│   │
│  • Authority │  │                                  │   │
│    Links     │  ├──────────────────────────────────┤   │
│  • Search    │  │ TAB CONTENT (scrollable)         │   │
│    Filters   │  │ • Ref cards with badges          │   │
│              │  │ • Split-view text + translation  │   │
│              │  │ • Force-directed graph           │   │
│              │  │ • Semantic search results        │   │
│              │  │ • Q&A answer + citations        │   │
│              │  └──────────────────────────────────┘   │
└──────────────┴──────────────────────────────────────────┘
```

### 2.2 Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Primary (Accent) | Amber | #d97706 |
| Highlight | Light Amber | #fde68a |
| Background | Dark Navy | #0a0f1d |
| Sidebar BG | Dark Slate | #0f172a |
| Text Primary | Light Gray | #f8fafc |
| Text Secondary | Medium Gray | #94a3b8 |
| Badge PRIMARY | Green | #10b981 |
| Badge SECONDARY | Blue | #3b82f6 |
| Badge INDEX | Amber | #d97706 |

---

## 3. Component Specifications

### 🔧 SECTION 1: ENTITY CARD (Sidebar Top)

**Component Name**: EntityCard.jsx  
**Location**: src/components/EntityCard.jsx

**Props**:
```javascript
{
  entity: {
    id: string,
    nameHan: string,
    nameVi: string,
    type: string,
    coordinates: { lat: number, lng: number },
    period: { start: string, end: string },
    founders: Array<{id, name}>
  },
  loading: boolean,
  error: string | null
}
```

**Data Source**: GET /dila/places?q={searchQuery}

**UI Display**:
```
┌────────────────────────────────────┐
│ Thiếu Lâm Tự (Large, amber)        │
│ DILA:PL000000023255 (monospace)    │
├────────────────────────────────────┤
│ Địa danh | Tọa độ                  │
│ Trung Quốc | 34.77°N, 112.46°E     │
├────────────────────────────────────┤
│ Thời kỳ | Loại                     │
│ 496-now | Religious Site           │
└────────────────────────────────────┘
```

**Error Handling**:
- No entity found: Show "不在 DILA 資料庫中" + retry button
- API timeout: Show skeleton loader
- Fallback: Render example data

---

### 🔧 SECTION 2: AUTHORITY LINKS

**Component Name**: AuthorityLinks.jsx

**Props**:
```javascript
{
  authorities: Array<{
    name: string,
    status: "validated" | "inferred" | "unmatched",
    count: number,
    link: string
  }>,
  entityId: string,
  onAuthorityClick: (authority) => void
}
```

**Display**:
```
✓ DILA Authority (49 refs) [green bg, clickable]
✓ CBETA Index (49 refs)    [blue bg, clickable]
◐ Wikidata (mapped)        [purple bg, external link]
```

**Badge Meanings**:
- ✓ Validated: confirmed match
- ◐ Inferred: heuristic match
- × Unmatched: no link found

**Action**: Click → POST to fetch references from that authority

---

### 🔧 SECTION 3: TAB NAVIGATION

**Component Name**: TabNav.jsx

**Props**:
```javascript
{
  activeTab: string,
  onTabChange: (tabName) => void,
  refCount: number
}
```

**Tabs** (6 horizontal, scrollable on mobile):
1. 📜 References & Citations (default, amber underline)
2. 📖 Full Text Passages
3. 🔗 Relationships Graph
4. 🤖 DeepSearch AI
5. ❓ Q&A (RAG)
6. (Future) 📤 Export Tools

**Style**:
- Active: amber (#d97706) bottom border, full opacity
- Inactive: 60% opacity, transparent bottom border

---

### 🔧 SECTION 4a: REFERENCE CARDS (Tab 1)

**Component Name**: ReferenceCard.jsx

**Props**:
```javascript
{
  ref: {
    cbtaId: string,          // "T16n670p0481c10-15"
    title: string,           // "楞伽經"
    snippet: string,         // Han text excerpt
    volume: number,
    page: number,
    column: string,          // "c"
    lines: string,           // "10-15"
    badge: "PRIMARY" | "SECONDARY" | "INDEX",
    sourceText: string       // "Laṅkāvatāra Sūtra"
  },
  onViewInText: (cbtaId, range) => void
}
```

**Visual**:
```
┌─────────────────────────────────────────────┐
│ 楞伽經 (Large, amber)    [PRIMARY badge]    │
│ CBETA: T16 n670 p0481c10-15 (monospace)    │
├─────────────────────────────────────────────┤
│ "少林寺在中國嵩山之上，達摩祖師於梁武帝..."  │
│ (serif, #d1d5db, dark bg, left amber border)│
├─────────────────────────────────────────────┤
│ Vol. 16, p.481 col C, lines 10-15          │
│ [Copy Citation] [View in Text →]           │
└─────────────────────────────────────────────┘
```

**Border Colors**:
- PRIMARY: Green (#10b981) left border
- SECONDARY: Blue (#3b82f6) left border
- INDEX: Amber (#d97706) left border

**Actions**:
1. Copy Citation → clipboard: "T16 n670 p0481c10-15"
2. View in Text → pass {cbtaId, range} to Tab 2 (Full Text)

---

### 🔧 SECTION 4b: AI TRANSLATION TAB (Tab 2)

**Component Name**: FullTextTab.jsx

**Props**:
```javascript
{
  cbtaId: string,
  range: string,
  onClose: () => void
}
```

**Data Flow**:
1. Fetch CBETA text: GET /cbeta/text/{cbtaId}?range={p481c10-15}
2. Call Groq LLM: POST /groq/translate
   ```json
   {
     "han_text": "少林寺在中國嵩山之上...",
     "context": "Buddhist",
     "target_language": "Vietnamese"
   }
   ```
3. Cache in Redis: key=`groq:{cbtaId}:vi`, TTL=86400s
4. Render split-view

**UI Layout** (50/50 split):
```
┌────────────────────────────────────────┐
│ Citation: T16 n670 p0481c10-15        │
├──────────────────┬─────────────────────┤
│ Classical Han    │ Vietnamese          │
│ (serif font)     │ (flowing text)      │
│                  │                     │
│ 少林寺在中國      │ Thiếu Lâm Tự nằm   │
│ 嵩山之上。        │ trên núi Tung Sơn  │
│ 達摩祖師於梁      │ ở Trung Quốc. Đạt  │
│ 武帝時傳法。      │ Ma truyền pháp...  │
│                  │                     │
├──────────────────┴─────────────────────┤
│ GLOSSARY (Annotated terms)             │
│ 少林寺 (Thiếu Lâm Tự) → [DILA link]   │
│ 達摩 (Đạt Ma) → Bodhidharma, patriarch │
│ 梁武帝 (Lương Vũ Đế) → Emperor Wu...  │
└────────────────────────────────────────┘
```

**Error Handling**:
- CBETA fetch fails: Show "Text not found" + retry
- Groq rate limited: Show "Translation queued, retry in 5s"
- Low confidence: Show warning badge "⚠ Low Confidence"

---

### 🔧 SECTION 5: RELATIONSHIPS GRAPH (Tab 3)

**Component Name**: GraphTab.jsx

**Data Source**: GET /dila/entity/{id}/graph?depth=2

**Visualization**: Force-directed graph (D3.js or Deck.GL)

**Node Types**:
| Type | Color | Icon |
|------|-------|------|
| Person | #3b82f6 (blue) | 🔵 |
| Place | #d97706 (amber) | 🟠 |
| Time Period | #94a3b8 (gray) | ⚪ |

**Edge Types**:
- founder→place (thick, dark)
- teacher→student (medium, styled)
- place→location (thin, dashed)

**Interactions**:
- Click node → navigate to entity detail (new search)
- Hover edge → tooltip showing relation type
- Zoom/pan → standard D3 controls (scroll, drag)
- Hover node → highlight connected edges

---

### 🔧 SECTION 6: ADVANCED SEARCH FILTERS

**Component Name**: SearchFilters.jsx

**Expandable Panel** (in sidebar, below Entity Card):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 By Dynasty
   [Select] Tang | Song | Yuan | Ming | Qing | Sui | ...

📖 By Text Type
   [●] Sûtra  [●] Vinaya  [●] Śāstra  [○] Commentary

🔤 Full-Text Search
   [Input box] + [Keyword in Context ⚙️]

🎯 Advanced Query
   Boolean: AND | OR | NOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**API**: GET /api/search?q={query}&dynasty={d}&textType={type}&kwic={bool}

**KWIC Logic** (When enabled):
```
Query: "少林寺"
Result: "...嵩山之上，**少林寺**在唐代興盛，達摩祖師...
```
Show keyword ± N characters context

---

### 🔧 SECTION 6b: DEEPSEARCH TAB (Tab 4 — Semantic Search)

**Component Name**: DeepSearchTab.jsx

**User Input**:
```
Natural language: "Thiếu Lâm Tự dạy gì trong Phật pháp?"
System extracts: Entity="Thiếu Lâm Tự", Intent="teaching"
```

**Data Flow**:
1. Parse query → extract entity + intent
2. Lookup DILA: GET /dila/places?q=Thiếu%20Lâm%20Tự
3. Fetch all references: GET /dila/place/{id}/references → [49 refs]
4. Semantic ranking (Groq):
   ```
   POST /groq/semantic-rank
   {
     "passages": [...text blocks...],
     "query": "dạy gì",
     "top_k": 10
   }
   ```
5. Display results sorted by relevance score (0.0-1.0)

**UI Display**:
```
┌────────────────────────────────────────┐
│ [Search box] "Thiếu Lâm Tự dạy gì?"   │
│                              [Search]  │
├────────────────────────────────────────┤
│ SEMANTIC RANKING RESULTS:              │
│                                        │
│ 1. [████████░░] 0.95                   │
│    少林寺主要教導禪宗法門...           │
│    Thiếu Lâm Tự chủ yếu dạy...        │
│    [View in Text →]                    │
│                                        │
│ 2. [███████░░░] 0.87                   │
│    達摩祖師傳授二入四行...             │
│    Đạt Ma truyền thụ...               │
│    [View in Text →]                    │
│                                        │
│ ...10. [█████░░░░░] 0.62              │
└────────────────────────────────────────┘
```

**Caching**: key=`deepsearch:{entityId}:{intent}`, TTL=604800s (7 days)

---

### 🔧 SECTION 7: Q&A TAB (Tab 5 — RAG-Powered)

**Component Name**: QATab.jsx

**User Input Examples**:
- "Ai là người sáng lập Thiếu Lâm Tự?" (Who founded Shaolin?)
- "Thiếu Lâm Tự nằm ở đâu?" (Where is Shaolin?)
- "Thiền tông dạy gì?" (What does Chan Buddhism teach?)

**RAG Pipeline**:
1. Parse question → extract entities + intent
2. Retrieve context: GET /dila/entity/{id}/related-texts?intent={intent}
3. Generate (Groq LLM):
   ```
   POST /groq/qa
   {
     "question": "Ai sáng lập Thiếu Lâm Tự?",
     "context_passages": [{text, source}, ...],
     "language": "vi"
   }
   Response: {
     "answer_vi": "Thiếu Lâm Tự được sáng lập bởi...",
     "confidence": 0.92,
     "citations": [{passage, source, cbtaId}]
   }
   ```
4. Display answer + confidence + citations

**UI Layout**:
```
┌──────────────────────────────────────────┐
│ Ask a question about Buddhist texts:    │
│ [Input] "Ai sáng lập Thiếu Lâm Tự?"    │
│                                 [Submit]│
├──────────────────────────────────────────┤
│ ⟳ Processing (1-3s while Groq runs)... │
│                                          │
│ ANSWER (Confidence: High ✓):             │
│                                          │
│ Thiếu Lâm Tự được sáng lập bởi          │
│ Bodhidharma (Đạt Ma) vào năm 496 CE     │
│ dưới thời Hoàng đế Lương Vũ Đế...       │
│                                          │
│ SOURCE CITATIONS:                        │
│ [1] 楞伽經 (Laṅkāvatāra Sūtra)          │
│     T16 n670 p0481c10-15 → [View]      │
│ [2] 傳燈錄 (Record of the Lamp)          │
│     T51 n2076 p0123a05 → [View]        │
│                                          │
│ Confidence badges: High | Medium | Low  │
└──────────────────────────────────────────┘
```

**Error Handling**:
- No relevant context: "Không tìm thấy dữ liệu liên quan"
- Groq fails: "Tạm ngừng RAG, vui lòng thử lại"
- Low confidence (< 0.6): Add disclaimer "⚠ Trả lời dựa trên dữ liệu sẵn có"

**Caching**: key=`qa:{question_hash}`, TTL=1209600s (14 days)

---

### 🔧 SECTION 8: CITATION EXPORT

**Component Name**: CitationExport.jsx

**Supported Formats**:

**1. BibTeX**
```bibtex
@inbook{cbeta2024,
  title={楞伽經},
  volume={16},
  pages={481c10-15},
  year={1924},
  note={Vietnamese trans: Groq LLM (2026)}
}
```

**2. Chicago**
```
"楞伽經." Taishō Shinshū Daizōkyō, vol. 16, p. 481, col. c, lines 10-15.
Vietnamese Translation (Groq AI, 2026).
```

**3. APA**
```
Buddhist Canonical Text Association. (1924). Laṅkāvatāra sūtra.
In Taishō Shinshū Daizōkyō (Vol. 16, pp. 481).
Translated to Vietnamese by Groq LLM (2026).
```

**4. Plain Text**
```
Citation: T16 n670 p0481c10-15
Title: 楞伽經 (Laṅkāvatāra Sūtra)
Volume: 16, Page: 481, Column: c, Lines: 10-15
Translation: Vietnamese (Groq LLM, 2026)
```

**Interaction**: Button on each reference card → modal with format dropdown → copy to clipboard

---

## 4. API Specifications

### 4.1 DILA Authority

```javascript
// Lookup places
GET /dila/places?q={query}&limit=50
Response: [{id, nameHan, nameVi, type, coordinates, period, founders}]

// Get references for entity
GET /dila/place/{id}/references
Response: [{cbtaId, volume, page, column, lines, badge, sourceText}]

// Get entity relationships
GET /dila/entity/{id}/graph?depth=2
Response: {nodes: [...], edges: [...]}
```

### 4.2 CBETA

```javascript
// Fetch text by citation
GET /cbeta/text/{cbtaId}?range={p.page.col.lines}
Response: {fullText, metadata, authorInfo}
```

### 4.3 Groq LLM

```javascript
// Translate Han text
POST /groq/translate
{
  "han_text": "少林寺...",
  "context": "Buddhist",
  "target_language": "Vietnamese"
}
Response: {translated_vi, glossary, confidence_score}

// Semantic ranking
POST /groq/semantic-rank
{
  "passages": [...],
  "query": "dạy gì",
  "top_k": 10
}
Response: [{passage, score, snippet}]

// Q&A with context
POST /groq/qa
{
  "question": "Ai sáng lập Thiếu Lâm Tự?",
  "context_passages": [...],
  "language": "vi"
}
Response: {answer_vi, confidence, citations}
```

---

## 5. Implementation Roadmap

| Week | Phase | Tasks |
|------|-------|-------|
| 1 | UI Foundation | Layout + EntityCard + AuthorityLinks + TabNav + RefCards |
| 2 | API Integration | DILA/CBETA clients + Groq integration + Full Text tab |
| 3 | Advanced Features | Graph viz + DeepSearch + Q&A + Export |
| 4 | Polish | Error handling + mobile + testing + perf |

---

## 6. Technology Stack

- **Frontend**: React (Design Component format)
- **Backend**: Node.js + Express
- **External APIs**: DILA, CBETA, Groq
- **Caching**: Redis (or in-memory)
- **Visualization**: D3.js or Deck.GL
- **Styling**: Inline styles (per DC spec)

---

## 7. File Locations

**Design Component**:
```
visjs-app/Dai_Tang_Kinh/daoanh/docs/Dai_Tang_Kinh_Tab_Interactive.dc.html
```

**Specification** (this file):
```
visjs-app/Dai_Tang_Kinh/daoanh/docs/Dai_Tang_Kinh_TAB_FULL_SPEC.md
```

**Components to Create**:
```
src/components/
  ├── EntityCard.jsx
  ├── AuthorityLinks.jsx
  ├── TabNav.jsx
  ├── ReferenceCard.jsx
  ├── FullTextTab.jsx
  ├── GraphTab.jsx
  ├── DeepSearchTab.jsx
  ├── QATab.jsx
  └── CitationExport.jsx
```

**API Handlers**:
```
api/
  ├── dila.js
  ├── cbeta.js
  ├── groq.js
  ├── search.js
  └── cache.js
```

---

## 8. Success Criteria

✅ User searches entity → see all CBETA references with DILA metadata  
✅ User clicks reference → view Han text + AI Vietnamese translation  
✅ User explores graph → click nodes to navigate entity relationships  
✅ User asks question → RAG-powered answer with citations  
✅ User exports citation → BibTeX/Chicago/APA format ready  
✅ User searches semantically → top 10 relevant passages ranked by Groq  
✅ All features handle errors gracefully  
✅ Mobile-responsive on tablets/phones  

---

## 9. Known Constraints

- DILA API rate limits: cache aggressively
- Groq free tier: ~40 req/min; batch translations
- CBETA mirrors: use main DILA mirror for consistency
- Han-Viet translation quality: monitor Groq output; add human review layer v2
- Graph perf: limit depth to 2-3 hops

---

## 10. Future Enhancements

- User annotations on translations
- Community translation voting
- Integrated timeline visualization
- Full-text similarity (parallel passages)
- Mobile app (React Native) sharing same API
- Multi-language support (English, Chinese, etc.)
- PDF export with formatting preserved

# Session: DILA Integration Layer Phase 1 (Entity ↔ Passages)

**Date:** 2026-05-23

## Mô tả task

Xây dựng integration layer cho DILA:
- Bảng ENTITY, PASSAGE, PASSAGE_ENTITY trong lineage.db
- Script migration từ places_pending + people + cbeta_texts → ENTITY
- Script migration từ cbeta_content_index → PASSAGE
- Name matching (FTS5) → PASSAGE_ENTITY
- 2 API endpoints: entity info + entity passages
- 1 trang test HTML: admin/test_entity.html
- Tích hợp với cbeta.db FTS5 để matching nhanh

## Liên hệ ROADMAP

- **Nguồn liên quan:** DILA (Person/Place), CBETA (text corpus)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt (CBETA pipeline) + Khoá 5 – DILA Integration Layer
- **Dòng ROADMAP:**
  - "CBETA pipeline (person/place → canon_citations + snippets dịch)"
  - "Khoá 5 — DILA Integration Layer Roadmap: Xây dựng integration layer usable cho DILA, click 1 thực thể → thấy toàn bộ đoạn kinh liên quan"

## Thiết kế / giải pháp

### Kiến trúc

```
lineage.db                          cbeta.db
┌──────────────────────┐           ┌─────────────────────┐
│ places_pending       │           │ cbeta_texts          │
│ people               │           │ cbeta_content_index  │
│                      │           │ cbeta_fts (FTS5)     │
│  ┌────────────────┐  │           └─────────────────────┘
│  │ ENTITY         │  │◄──── migrate ─────────┘
│  │ PASSAGE        │  │
│  │ PASSAGE_ENTITY │  │
│  └────────────────┘  │
└──────────────────────┘
         │
   2 API routes in app.py
         │
         ▼
    admin/test_entity.html
```

### DB Schema (3 bảng mới trong lineage.db)

```sql
CREATE TABLE entity (
    entity_id   TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('PERSON','PLACE','TEXT')),
    dila_id     TEXT NOT NULL,
    alias_vi    TEXT,
    alias_zh    TEXT,
    cbeta_occ   TEXT,
    marcus_id   TEXT,
    extra_alias TEXT
);

CREATE TABLE passage (
    passage_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL DEFAULT 'CBETA',
    text_id     TEXT NOT NULL,
    loc_ref     TEXT NOT NULL DEFAULT '',
    raw_text    TEXT NOT NULL,
    norm_text   TEXT
);

CREATE TABLE passage_entity (
    passage_id INTEGER NOT NULL,
    entity_id  TEXT NOT NULL,
    PRIMARY KEY (passage_id, entity_id)
);
```

### Migration strategy

1. **ENTITY PLACE**: 118,328 rows từ `places_pending WHERE id LIKE 'PL%'`
2. **ENTITY PERSON**: 48,673 rows từ `people` (id A-prefixed)
3. **ENTITY TEXT**: 1 row từ `cbeta_texts` (T51n2076), sẽ mở rộng sau
4. **PASSAGE**: 3,917 rows từ `cbeta_content_index` (text T51n2076)
5. **PASSAGE_ENTITY**:
   - TEXT entity: direct match (text_id = entity.dila_id)
   - PERSON/PLACE: FTS5 token matching via `cbeta_fts` (fast, token-based)

## File đã tạo/sửa

| File | Trạng thái | Mô tả |
|------|-----------|-------|
| `scripts/build_integration_layer.py` | NEW | Build 3 bảng + name matching |
| `app.py` (lines 4061-4090) | MODIFIED | Thêm 2 route entity API |
| `admin/test_entity.html` | NEW | UI test page |
| `docs/sessions/2026-05-23_dila_integration_layer.md` | NEW | Session log này |
| `docs/db_schema.md` | UPDATED | Thêm schema 3 bảng |
| `docs/pipelines.md` | UPDATED | Thêm pipeline integration layer |
| `docs/progress.md` | UPDATED | Thêm trạng thái mới |

## Cách chạy / test

### 1. Build integration layer
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python scripts/build_integration_layer.py
```

### 2. Test API
```bash
# Entity info
curl http://localhost:5000/daoanh/api/entity/T51n2076
curl http://localhost:5000/daoanh/api/entity/A000001
curl http://localhost:5000/daoanh/api/entity/PL000000

# Entity passages
curl "http://localhost:5000/daoanh/api/entity/T51n2076/passages?limit=5"
curl "http://localhost:5000/daoanh/api/entity/A000001/passages?limit=5"
```

### 3. Test UI
Mở browser: `/daoanh/admin/test_entity.html`

### 4. Verify DB
```bash
sqlite3 data/lineage.db "SELECT entity_type, COUNT(*) FROM entity GROUP BY entity_type;"
sqlite3 data/lineage.db "SELECT COUNT(*) FROM passage;"
sqlite3 data/lineage.db "SELECT COUNT(*) FROM passage_entity;"
```

## Kết quả test

### Build script
```
ENTITY:   48,673 PERSON + 118,328 PLACE + 1 TEXT = 167,002
PASSAGE:  3,917 (T51n2076)
PASSAGE_ENTITY: 5,276 (3,917 TEXT direct + 1,359 PERSON/PLACE matching)
```

### API endpoints
| Endpoint | Result |
|----------|--------|
| `GET /daoanh/api/entity/T51n2076` | ✅ 200, entity info (TEXT, Taishō Tripiṭaka) |
| `GET /daoanh/api/entity/A000001` | ✅ 200, entity info (PERSON, 明因妙善普濟法師) |
| `GET /daoanh/api/entity/PL000000` | ✅ 200, entity info (PLACE, 闊悉多國) |
| `GET /daoanh/api/entity/FAKE123` | ✅ 200, `has_data: false` |
| `GET /daoanh/api/entity/T51n2076/passages?limit=2` | ✅ 200, count=3917, 2 passages |
| `GET /daoanh/api/entity/A023597/passages?limit=3` | ✅ 200, count=14 passages |

### Bug fixes during build
- **Pre-existing bug 1**: auto_batch_suggest missing `def` keyword (line 700) → fixed
- **Pre-existing bug 2**: Indented routes at lines 3706-4062 missing wrapper block → wrapped in `if True:`

### Tester Agent
- `npm run tester:agent` — ✅ All 4 tests passed (lint, test, e2e, runtime)

## Lưu ý

- Phase 1 dùng FTS5 token matching (exact token, không substring LIKE)
- Entity name matching sẽ match những entity có `alias_zh` là token hoàn chỉnh trong passage text
- Phase 2 có thể bổ sung LIKE fallback + fuzzy matching

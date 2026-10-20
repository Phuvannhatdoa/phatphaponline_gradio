# Đạo Ảnh - Buddhist GIS & Dictionary System

> **Version:** v10.4-Full-GPS (2026-04-22)
> **Status:** ✅ FULL GPS: 58,476 places | 48,803 monks | 166,278 dictionary terms
> **Completion:** ~99%

---

> **Version:** v10-Multi-Dict-Merger (2026-04-22)
> **Project:** Multi-Dict Merger - 22 bộ từ điển → SQLite Master

---

## 🚀 Quick Status

| Module | Status | Entries |
|--------|--------|---------|
| Multi-Dict Merger | ✅ Complete | 166,278 |
| Entity Extraction | ✅ Complete | ĐỊA DANH: 15,863 / TU SĨ: 6,985 |
| Fuzzy Search | ✅ Complete | rapidfuzz + cache |
| FTS5 Search | ✅ Complete | < 0.1s query |
| StarDict Export | ✅ Complete | daoanh_dict.txt (51MB) |

**Project Completion: ~85%** (GIS + Dictionary core done)

---

## 📂 Source Data (22 bộ từ điển)

```
data/dictionaries/tudien/
├── han_lam/    (P1 - Highest Priority): 119,478 entries
├── pho_thong/  (P2 - Medium Priority):  45,047 entries  
└── tham_khao/  (P3 - Lowest Priority):   1,753 entries
```

## 📤 Output Files

| File | Size | Description |
|------|------|-------------|
| `data/lineage.db` | SQLite | Master storage (166,278 records) |
| `data/dict/daoanh_dict.txt` | 51MB | StarDict distribution |
| `data/dict/daoanh_entities.txt` | 16MB | Entity-tagged dictionary |
| `data/dict/merged.json` | 81MB | JSON backup |
| `data/indexed/fuzzy_cache.json` | 152MB | Fuzzy search cache |

---

## 🔧 ETL Scripts

### Multi-Dict Merger
```bash
python src_python/etl/multi_dict_merger.py
```
- Priority: ThamKhao → PhoThong → HanLam
- Entity Auto-Tagging: ĐỊA DANH, TU SĨ
- FTS5 Full-text Search
- NFC Normalization

### Fuzzy Search API
```bash
python src_python/etl/fuzzy_search_api.py
```
- rapidfuzz.WRatio scoring
- Entity filtering mode

### StarDict Export
```bash
python src_python/etl/export_stardict.py
```

---

## 🎯 Features

### 1. Multi-Dict Merger
- ✅ 22 bộ từ điển → SQLite Master
- ✅ Priority Overlay (HanLam ghi đè)
- ✅ .txt + .docx support

### 2. Entity Extraction
- ✅ ĐỊA DANH: chùa, tự, viện, tổ đình, tịnh xá
- ✅ TU SĨ: hòa thượng, thượng tọa, thiền sư, pháp sư

### 3. Search
- ✅ FTS5 Full-text (< 0.1s)
- ✅ Fuzzy Search (rapidfuzz)
- ✅ Entity-filtered search

### 4. Distribution
- ✅ StarDict format (.txt)
- ✅ GoldenDict compatible
- ✅ Offline ready

---

## 📊 Statistics

```
Total: 166,278 entries
├── HanLam (P1): 119,478 (72%)
├── PhoThong (P2):  45,047 (27%)
└── ThamKhao (P3):   1,753 (1%)

Entity Distribution:
├── ĐỊA DANH: 15,863
├── TU SĨ:    6,985
└── OTHER:  143,430
```

---

## 🔗 APIs

| Endpoint | Description |
|----------|-------------|
| `/daoanh/api/fuzzy/search?q=...&mode=auto\|place\|monk` | Fuzzy search |
| SQLite FTS5 | Full-text search |

---

## 📝 Logs

- `SESSION.md` - Session state V38
- `LOGS.md` - Full history

---

## Previous Versions

- v10.4: Full GPS (58,476) + Person Authority (48,803) - Current
- v10.3: Person Authority (48,803 monks)
- v10.2: GPS Layer + StarDict Full Export
- v10.1: Multi-Dict Merger (166,278 entries)
- v9.1: TTL Queue + Marcus DB

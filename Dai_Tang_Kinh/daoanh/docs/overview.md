# Đạo Ảnh — Hệ Thống Tra Cứu Địa Danh Phật Giáo

**Phiên bản docs:** 2026-05-21
**Project root:** `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh`

## Mục tiêu

Hệ thống Mapping Địa danh Phật giáo (Đạo Ảnh) — admin dashboard quản lý và đối chiếu địa danh Phật giáo từ DILA (Dharma Drum Institute of Liberal Arts) với bản dịch Việt ngữ.

## Tech Stack

- **Backend:** Flask (Python 3) — port 5000 (main app), port 5001 (auth gateway)
- **Frontend:** React 18 (UMD + Babel standalone), Tailwind CSS (CDN), Lucide Icons
- **Database:** SQLite (`data/lineage.db`)
- **Map:** Leaflet.js (Google Maps tiles, `hl=vi`)
- **External APIs:** Gemini 2.0 Flash (AI translation), GoogleTranslator (fallback)

## Two-Server Architecture (Post-Split 2026-05-14)

| Server | File | Port | Role |
|--------|------|------|------|
| **Auth Gateway** | `server.py` | 5001 | Login only (Gmail check, session mgmt, admin emails) |
| **Main Server** | `app.py` | 5000 | All business logic (Đạo Ảnh, TTL, Marcus, dossier, translation) |

### Route Ownership

| Path Prefix | Handled By |
|-------------|-----------|
| `/daoanh/login.html` | server.py:5001 |
| `/daoanh/api/login/*` | server.py:5001 |
| `/api/admin/emails` | server.py:5001 |
| `/daoanh/admin/` → placevn.html | app.py:5000 |
| `/daoanh/panorama/` → panorama.html | app.py:5000 |
| `/daoanh/api/admin/*` | app.py:5000 |
| `/daoanh/api/public/*` | app.py:5000 |
| `/daoanh/static/*` | app.py:5000 |
| `/api/*` (TTL, Marcus, dossier, etc.) | app.py:5000 |

### Nginx Routing

- `/daoanh/api/login/*` → port 5001 (auth)
- Everything else → port 5000 (main)

## Data Architecture — 4-Layer Model

| Layer | Purpose | Examples |
|-------|---------|----------|
| **RAW** | Source data — never modified by the app | `places_dila`, `people_full`, `marcus_reference` |
| **STAGING / MAPPING** | ETL, AI mapping, deduplication | `places_pending`, `namevi_map_places` |
| **FINAL / PUBLIC** | Consumed by UI, exported downstream | `places`, `places_vps`, `dataset_sources`, `lexicon` |
| **Index** | Binary search, O(log n) | `indexed/entity_master.idx` |

## Module Listing

- **Đạo Ảnh Dashboard** (`admin/placevn.html`, `app.py:ai_judge`) — Main admin UI for place mapping
- **Panorama/TTL** (`admin/panorama.html`) — TTL ontology visualization
- **Name-Vi Map** (`admin/namevimap.html`) — Bulk name-vi mapping
- **Search All** (`admin/search_all.html`) — Cross-table search
- **Auth** (`server.py`, `admin/login.html`, `admin/emails.html`) — Login & email notification
- **Thiền Tông Lineage** (`thientong.py`) — Zen genealogy visualization (VisJS/D3.js)

## Key Stats

- `places_dila`: ~19,000 DILA places + 40,000 Academia Sinica
- `places_pending`: ~175,000 records
- `namevi_map_places`: ~118,000 mapping records
- `lexicon`: 166,278 entries, 22 StarDict sources, 15,863 `entity_type='ĐỊA DANH'`
- `places_vps`: VPS (Việt Phật San) place data

## Server Quick Commands

```bash
# Auth Gateway (login)
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python3 server.py          # port 5001

# Main Server (all APIs)
python3 app.py             # port 5000

# Restart main
fuser -k 5000/tcp && nohup python3 app.py > flask.log 2>&1 &
```

## Testing

```bash
npm run pipeline    # lint + test + e2e + e2e:runtime
npm run tester:agent   # same as pipeline
npm run lint        # ESLint syntax check
npm run e2e         # HTML/JS error check
```

## Zero-RAM Principle

- Không bao giờ nạp toàn bộ 2000+ file kinh văn vào RAM
- Sử dụng Byte-offset mapping, Index-based search và generator/iterator
- Binary index cho O(log n) lookup

---
id: T16
title: Nexus Points — entity-linking + nexus extraction
module: DILA Integration Layer
priority: medium
status: done
depends_on: []
created: 2026-08-13
updated: 2026-09-05
done_when: Bảng `nexus_events` có data, route `/nexus/find` hoạt động, tab 🕸 Đồ Thị trên places.html hiển thị person nodes thật từ nexus (không phải regex scraping)
---

# T15 — Nexus Points — entity-linking + nexus extraction

## Mục tiêu
DEV_HISTORY audit 2026-08-11: không có route `/nexus/find` trong code. Xây entity-linking engine + nexus extraction từ CBETA TEI: `Nexus Point = Person + Place + Time gặp nhau trong văn bản`.

## Cách tiếp cận
- Parse CBETA TEI: `<div type="event" when="+0383" where="#PLxxxxx">` kèm `<persName>`.
- Entity-linking: person/place/time → DILA_ID.
- Bảng lưu nexus (event_id, person_id, place_id, time).
- API `/daoanh/api/nexus/find?person=&place=&time=`.

## Cập nhật 2026-08-19

Khi build lại tab "🕸 Đồ Thị" cho T17 (xem `tasks/T17-knowledge-graph-viz.md`), đã kiểm tra
schema thật của `places`/`places_dila`/`people` (`PRAGMA table_info`) — xác nhận **không có bất kỳ
cột nào** liên kết person↔place (không `birthplace_id`, không `residence_place_id`, không
`persName` cấu trúc trong `places_dila.raw_xml`). Đây chính là lý do T16 (Nexus Points) tồn tại:
chỉ có parse TEI thật (`<div type="event" where="#PLxxx"><persName>`) mới tạo ra được liên kết
person↔place có nguồn dẫn 100%. Regex/mention-scraping (đã bị gỡ khỏi graph API) không thay thế
được việc này.

Frontend đã sẵn sàng nhận dữ liệu này ngay khi có: `renderGraphTab()` trong `places.html` đã hỗ trợ
node `group: "person"` (màu, logic điều hướng `selectPerson()`) — chỉ cần
`/daoanh/api/places/<id>/graph` (app.py) trả thêm node person thật từ bảng nexus khi T16 xong.

## Chỉ Thị Thực Hiện (2026-08-20)

**Prerequisite:** T02 (passage + passage_entity) là nguồn TEI data. Verify xem T02 đã có `raw_tei` column chưa:
```sql
PRAGMA table_info(passage);
SELECT count(*) FROM passage WHERE raw_tei IS NOT NULL;
```

**Bước 1 — Audit CBETA TEI structure:**
```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/lineage.db')
# Lấy sample raw_tei để xem structure thật
rows = conn.execute('SELECT id, raw_tei FROM passage WHERE raw_tei IS NOT NULL LIMIT 3').fetchall()
for r in rows: print(r[0], str(r[1])[:300])
"
```

**Bước 2 — Tạo bảng `nexus_events`:**
```sql
CREATE TABLE IF NOT EXISTS nexus_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id TEXT,           -- nguồn CBETA passage
    person_dila_id TEXT,       -- DILA person ID (A...)
    place_dila_id TEXT,        -- DILA place ID (PL...)
    event_year INTEGER,        -- năm CE từ when="+0383"
    event_label TEXT,          -- text tường thuật (truncated 200 chars)
    confidence TEXT DEFAULT 'tei_parsed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ne_place ON nexus_events(place_dila_id);
CREATE INDEX IF NOT EXISTS idx_ne_person ON nexus_events(person_dila_id);
```

**Bước 3 — ETL parser:**
- Parse `<div type="event" when="+0383" where="#PLxxxxx"><persName ref="#Axxxxxx">...</persName>`
- Extract: `when` → year, `where` → place_id, `persName ref` → person_id
- Insert vào `nexus_events`

**Bước 4 — API route:**
```python
@app.route('/daoanh/api/nexus/find')
def api_nexus_find():
    person = request.args.get('person', '')
    place = request.args.get('place', '')
    year_from = request.args.get('year_from', type=int)
    # Query nexus_events + join people/places_dila for labels
    # Return JSON: {nexus_points: [{person, place, year, evidence}, ...]}
```

**Bước 5 — Nối vào places.html graph tab:**
- Route `/api/places/<id>/graph` thêm nexus person nodes từ `nexus_events WHERE place_dila_id=?`
- Frontend `renderGraphTab()` đã sẵn sàng nhận `group: "person"` nodes

## Cập nhật 2026-09-03 — DONE

T02 `raw_tei` chưa implement (passage.raw_tei không tồn tại). Giải pháp thực tế:
dùng **`place_person_bibl`** (13,933 rows — parse từ Cao Tăng Truyện + CBETA có sẵn,
confidence 0.7–1.0) làm nguồn ETL thay vì parse TEI trực tiếp.

Script: `scripts/t16_nexus_etl.py`
Kết quả: `nexus_events` — 10,458 rows | 3,664 places | 1,952 persons

## Acceptance criteria (checklist)
- [x] Verify T02 `raw_tei` — không có; dùng `place_person_bibl` thay thế (conf ≥ 0.7)
- [x] ETL từ `place_person_bibl` → `nexus_events` (10,458 rows)
- [x] Bảng `nexus_events` được tạo và populated (10,458 rows >> 100)
- [x] Route `/nexus/find?place=PL000000023255` trả nexus points (count=20 với min_conf=0.9)
- [x] `/api/places/<id>/graph` trả person nodes từ nexus (có `source: "nexus_tei"`)
- [x] Tab 🕸 Đồ Thị hiển thị person nodes thật — verified 2026-09-03 (Thích Huyền Trang, An Lẫm, Bảo Tập...)
- [x] Không dùng regex scraping — nguồn là place_person_bibl (curated CBETA authority)

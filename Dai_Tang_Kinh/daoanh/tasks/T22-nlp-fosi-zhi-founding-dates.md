---
id: T22
title: Founding Date Pipeline — 59K Places → HOME Integration
module: GIS Places / Timeline / HOME
priority: high
status: in_progress
depends_on: [T21, T22.1]
created: 2026-08-20
updated: 2026-08-30
done_when: >
  Layer D (regex DILA notes) done ≥200 rows,
  Layer E (Ollama raw_xml) authorized và scheduled,
  Admin review queue UI hoạt động,
  places.html Niên Đại tab hiển thị approved records
---

## Trạng thái các Layer (2026-09-02 — cập nhật)

| Layer | Nguồn | Trạng thái | Rows | Task |
|-------|-------|-----------|------|------|
| A — Wikidata P571 | Wikidata SPARQL | ✅ **DONE** | +30 net new | T64, T64b |
| B — CHGIS | Harvard Dataverse | ⚠️ Cần download | — | Admin action |
| C — BGIS | Harvard Dataverse | ⚠️ Cần Phase 0 audit | — | Admin action |
| D — Regex DILA notes | places_dila.note | ✅ **DONE** | +55 rows | **T22d** |
| E — Ollama NLP raw_xml | places_dila.raw_xml | ⏳ Cần Ollama local | — | Sau khi B/C done |

**Layer A ✅ hoàn thành:** T64 (GPS spatial) + T64b (s2t name match) → +30 rows (116→146).
Wikidata ceiling xác nhận ~150 rows max — DILA và Wikidata index các thực thể khác nhau.

**Layer D ✅ hoàn thành (2026-08-30):** T22d regex DILA notes → +55 founding events.
distinct places: 3,479→3,534. Rollback: `DELETE FROM place_timeline_events WHERE source='dila_founding_phase2'`.

**⚠️ ADMIN ACTION CẦN — Layer B + C:**
- Layer B (CHGIS): Tải từ Harvard Dataverse → `data/dila_import/CHGIS/`. Structured, auto-approve.
- Layer C (BGIS): Audit "Starting year" trước — cần xác nhận historical founding vs modern registration.
- Layer E: Chạy sau khi có B/C; cần Ollama local hoặc API LLM thay thế.


# T22 — Founding Date Pipeline (Full Stack)

> **Mục tiêu:** Xử lý 59,167 DILA places qua 5-layer pipeline để lấy founding date.
> Output cuối: `place_timeline_events` table → Niên Đại tab + HOME stats.
> Admin xem trên dashboard, lập lịch triển khai từng layer.

---

## Context (từ T22.1 research)

```
58,167 DILA places
  Layer A — Wikidata P571:    ~2,106  có founding date (verified, auto-approve)
  Layer B — CHGIS gazetteer:  ~2,407  có founding date (structured, auto-approve)
  Layer C — BGIS 2006:        ~17,933 có "Starting year" — CẦN INSPECT trước
  Layer D — Regex raw_xml:    TBD     năm trong ngoặc （年）
  Layer E — Ollama raw_xml:   ~53K+   narrative text còn lại
```

**BGIS "Starting year" chưa xác nhận** là historical founding hay modern registration — đây là bước đầu tiên cần làm (Phase 0).

---

## DB Schema

```sql
-- Đã thiết kế trong T21, tạo nếu chưa có
CREATE TABLE IF NOT EXISTS place_timeline_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id             TEXT NOT NULL,
    event_type          TEXT DEFAULT 'FOUNDING',
    year_ce             INTEGER,
    year_end_ce         INTEGER,    -- cho ranges
    label_zh            TEXT,
    label_vi            TEXT,
    source              TEXT NOT NULL,  -- WIKIDATA|CHGIS|BGIS|REGEX|OLLAMA|CLAUDE_API
    source_ref          TEXT,           -- Wikidata QID, CHGIS ID, etc.
    confidence          REAL DEFAULT 0.5,
    verification_status TEXT DEFAULT 'candidate',  -- candidate|approved|rejected
    verified_by         TEXT,
    verified_at         TEXT,
    evidence_text       TEXT,           -- đoạn gốc để reviewer đọc
    pipeline_run_id     TEXT,           -- batch tracking
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dila_id, source, year_ce)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    layer       TEXT NOT NULL,  -- A|B|C|D|E
    status      TEXT,           -- running|done|failed
    started_at  TEXT,
    ended_at    TEXT,
    processed   INTEGER DEFAULT 0,
    inserted    INTEGER DEFAULT 0,
    errors      INTEGER DEFAULT 0,
    notes       TEXT
);
```

---

## Phase 0 — BGIS Inspection (Admin task, bắt buộc trước Layer C)

**Mục tiêu:** Xác nhận "Starting year" trong BGIS = historical founding hay modern registration.

```
1. Admin download từ Harvard Dataverse:
   https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VAYEUZ

2. Mở CSV/shapefile → xem field "Starting year" cho 5-10 temples nổi tiếng:
   - 少林寺 Shaolin → "Starting year" có = 495 không?
   - 白馬寺 Bai Ma → có = 68 không?
   - Nếu có → historical founding date → Layer C giá trị cao (17,933 records)
   - Nếu là 1983/1984/1985 → modern registration → Layer C skip

3. Kết quả ghi vào: docs/T22.1_FOUNDING_DATE_DATA_REUSE_AUDIT.md
```

**Thời gian:** 30 phút (download + inspect).

---

## Layer A — Wikidata ETL

**Coverage:** ~2,106 Buddhist temples China có P571. Direct link: 148 qua P1188.
**Trust:** Auto-approve (scholarly community verified).

```python
# scripts/etl_wikidata_founding.py

import requests, sqlite3, json
from datetime import datetime

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# Query 1: Direct DILA bridge (P1188 → P571)
QUERY_DIRECT = """
SELECT ?item ?dila_id ?inception WHERE {
  ?item wdt:P1188 ?dila_id .
  ?item wdt:P571 ?inception .
}
"""

# Query 2: Buddhist temples China với coordinates (spatial match sau)
QUERY_SPATIAL = """
SELECT ?item ?inception ?lat ?long ?name WHERE {
  ?item wdt:P31/wdt:P279* wd:Q44613 .
  ?item wdt:P17 wd:Q148 .
  ?item wdt:P571 ?inception .
  ?item wdt:P625 ?coord .
  BIND(geof:latitude(?coord) AS ?lat)
  BIND(geof:longitude(?coord) AS ?long)
  OPTIONAL { ?item rdfs:label ?name FILTER(LANG(?name) = "zh") }
}
"""

def run_layer_a(db_path: str):
    conn = sqlite3.connect(db_path)
    run_id = log_run_start(conn, "A")

    # Phase A1: Direct P1188 match
    results = sparql_query(QUERY_DIRECT)
    for r in results:
        dila_id = r["dila_id"]["value"]
        year_ce = parse_wikidata_date(r["inception"]["value"])
        qid = r["item"]["value"].split("/")[-1]
        insert_event(conn, dila_id, year_ce, "WIKIDATA",
                     source_ref=qid, confidence=0.95,
                     verification_status="approved",  # auto-approve
                     evidence_text=f"Wikidata {qid} P571={year_ce}")

    # Phase A2: Spatial match (±0.5km)
    wikidata_places = sparql_query(QUERY_SPATIAL)
    dila_places = conn.execute(
        "SELECT id, geo_lat, geo_long FROM places_dila WHERE geo_lat IS NOT NULL"
    ).fetchall()
    for wp in wikidata_places:
        best = find_nearest(wp, dila_places, threshold_km=0.5)
        if best:
            insert_event(conn, best["dila_id"], wp["year"],
                         "WIKIDATA", confidence=0.75,
                         verification_status="candidate",  # cần review
                         evidence_text=f"Spatial match {best['dist_km']:.2f}km")

    log_run_end(conn, run_id)
    conn.commit()
```

---

## Layer B — CHGIS ETL

**Coverage:** ~2,407 records từ Da Qing yitong zhi, founding dates 1st century → Qing.
**Source:** Harvard CHGIS dataset (CC BY).
**Trust:** Auto-approve (imperial gazetteer, scholarly digitized).

```python
# scripts/etl_chgis_founding.py
# Input: CHGIS Temples CSV (download từ ECAI/Harvard)
# Fields: temple_name_zh, founding_year, lat, long, dynasty

def run_layer_b(db_path: str, chgis_csv: str):
    import pandas as pd
    df = pd.read_csv(chgis_csv)
    conn = sqlite3.connect(db_path)
    run_id = log_run_start(conn, "B")

    dila_places = load_dila_places(conn)  # id, name_zh, geo_lat, geo_long

    for _, row in df.iterrows():
        year_ce = row.get("founding_year")
        if not year_ce: continue

        # Try name match first (exact)
        match = find_by_name(row["temple_name_zh"], dila_places)
        if not match:
            # Fallback: spatial match
            match = find_nearest(row["lat"], row["long"], dila_places, threshold_km=1.0)

        if match:
            insert_event(conn, match["dila_id"], int(year_ce),
                         "CHGIS",
                         source_ref=row.get("chgis_id"),
                         confidence=0.90,
                         verification_status="approved",  # Da Qing yitong zhi = authoritative
                         evidence_text=f"CHGIS: {row.get('source_text','')[:200]}")

    log_run_end(conn, run_id)
    conn.commit()
```

---

## Layer C — BGIS ETL

**Chỉ chạy sau Phase 0 xác nhận "Starting year" = historical founding.**

```python
# scripts/etl_bgis_founding.py
# Input: BGIS shapefile/CSV từ Harvard Dataverse
# Fields: ID, name, lat, long, Starting year, Ending year, province

def run_layer_c(db_path: str, bgis_file: str):
    # Tương tự Layer B
    # Nếu Starting year xác nhận là historical → confidence=0.85, auto-approve
    # Nếu là modern registration → confidence=0.2, skip hoặc mark note
    pass
```

---

## Layer D — Regex ETL

**Coverage:** TBD — raw_xml có pattern `（XXX年）` hoặc `公元XXX年`.
**Trust:** High confidence — số trong ngoặc không thể sai về syntactically.

```python
# scripts/etl_regex_founding.py
import re, sqlite3

PATTERNS = [
    (r'（(\d{3,4})年）',          0.92, "year_in_parens"),
    (r'公元(\d{3,4})年',          0.90, "gongyan"),
    (r'始建(?:於|于)(\d{3,4})年', 0.88, "shijian"),
    (r'建(?:於|于)(\d{3,4})年',   0.85, "jian_yu"),
    (r'創建?(?:於|于)(\d{3,4})年',0.85, "chuangjian"),
    (r'立(?:寺|院|堂)(?:於|于)(\d{3,4})年', 0.83, "li_si"),
]

# Warning patterns — nếu match thì confidence giảm + flag
RENOVATION_PATTERNS = [r'重修', r'重建', r'重興', r'重創', r'重立']

def extract_year(raw_xml: str) -> dict | None:
    if not raw_xml: return None

    for pattern, confidence, pat_name in PATTERNS:
        m = re.search(pattern, raw_xml)
        if m:
            year = int(m.group(1))
            # Validate: year hợp lý (1 CE → 1950 CE)
            if not (1 <= year <= 1950): continue

            # Check renovation warning
            context = raw_xml[max(0, m.start()-50):m.end()+50]
            is_renovation = any(re.search(p, context) for p in RENOVATION_PATTERNS)

            return {
                "year_ce": year,
                "confidence": confidence * (0.7 if is_renovation else 1.0),
                "pattern": pat_name,
                "evidence_text": context,
                "warning": "RENOVATION_CONTEXT" if is_renovation else None,
                "verification_status": "candidate" if is_renovation else "approved"
            }
    return None

def run_layer_d(db_path: str):
    conn = sqlite3.connect(db_path)
    run_id = log_run_start(conn, "D")
    rows = conn.execute(
        "SELECT id, raw_xml FROM places_dila WHERE raw_xml IS NOT NULL AND raw_xml != ''"
    ).fetchall()

    for dila_id, raw_xml in rows:
        result = extract_year(raw_xml)
        if result:
            insert_event(conn, dila_id, result["year_ce"], "REGEX",
                         confidence=result["confidence"],
                         verification_status=result["verification_status"],
                         evidence_text=result["evidence_text"])

    log_run_end(conn, run_id)
    conn.commit()
```

---

## Layer E — Ollama ETL

**Coverage:** Narrative text còn lại sau Layers A-D.
**Trust:** Medium — cần admin sampling review.
**Model:** `qwen2.5:7b` (Classical Chinese support, free, local).

```python
# scripts/etl_ollama_founding.py
import ollama, sqlite3, json

SYSTEM_PROMPT = """Bạn là chuyên gia văn bản Hán cổ. Nhiệm vụ: tìm năm thành lập của ngôi chùa/tự viện trong văn bản.
Chỉ tìm NĂM THÀNH LẬP LẦN ĐẦU (建/創/立寺/開山). KHÔNG lấy năm trùng tu (重修/重建).
Trả về JSON hợp lệ: {"year_ce": <số nguyên hoặc null>, "confidence": <0.0-1.0>, "evidence": "<đoạn text gốc chứa năm>", "note": "<giải thích ngắn>"}
Nếu không tìm thấy năm thành lập rõ ràng: {"year_ce": null}"""

def run_layer_e(db_path: str, batch_size: int = 100):
    conn = sqlite3.connect(db_path)
    run_id = log_run_start(conn, "E")

    # Chỉ xử lý places CHƯA có founding date từ Layers A-D
    rows = conn.execute("""
        SELECT p.id, p.raw_xml FROM places_dila p
        WHERE p.raw_xml IS NOT NULL AND p.raw_xml != ''
        AND p.id NOT IN (
            SELECT dila_id FROM place_timeline_events
            WHERE source IN ('WIKIDATA','CHGIS','BGIS','REGEX')
        )
        LIMIT ?
    """, (batch_size,)).fetchall()

    for dila_id, raw_xml in rows:
        try:
            response = ollama.chat(
                model="qwen2.5:7b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": raw_xml[:2000]}
                ]
            )
            result = json.loads(response["message"]["content"])
            if result.get("year_ce"):
                insert_event(conn, dila_id, result["year_ce"], "OLLAMA",
                             confidence=result.get("confidence", 0.5),
                             verification_status="candidate",  # LUÔN cần review
                             evidence_text=result.get("evidence", ""))
        except Exception as e:
            log_error(conn, run_id, dila_id, str(e))

    log_run_end(conn, run_id)
    conn.commit()
```

**Batch strategy:** Chạy 100-500 records/batch. Admin trigger từ dashboard.

---

## Admin Dashboard — Pipeline Control Panel

```
┌─────────────────────────────────────────────────────────────────┐
│  FOUNDING DATE PIPELINE CONTROL                    2026-08-20   │
├─────────┬────────────┬──────────┬──────────┬──────┬────────────┤
│ Layer   │ Source     │ Status   │ Processed│ Done │ Action     │
├─────────┼────────────┼──────────┼──────────┼──────┼────────────┤
│ Phase 0 │ BGIS check │ PENDING  │ —        │ —    │ [Admin do] │
│ Layer A │ Wikidata   │ PENDING  │ 0/2,106  │ 0    │ [▶ Run]   │
│ Layer B │ CHGIS      │ PENDING  │ 0/2,407  │ 0    │ [▶ Run]   │
│ Layer C │ BGIS       │ BLOCKED  │ —        │ —    │ Needs Ph.0 │
│ Layer D │ Regex      │ PENDING  │ 0/?      │ 0    │ [▶ Run]   │
│ Layer E │ Ollama     │ PENDING  │ 0/~53K   │ 0    │ [▶ Run]   │
├─────────┴────────────┴──────────┴──────────┴──────┴────────────┤
│  Review Queue: 0 candidate records                              │
│  [Review Queue] [Bulk Approve REGEX>0.9] [Export CSV]          │
└─────────────────────────────────────────────────────────────────┘
```

**Admin API endpoints:**
```python
GET  /daoanh/api/admin/pipeline/status        → layer status + counts
POST /daoanh/api/admin/pipeline/run/<layer>   → trigger layer (A/B/C/D/E)
GET  /daoanh/api/admin/pipeline/review        → paginated candidate queue
POST /daoanh/api/admin/pipeline/approve/<id>  → approve single record
POST /daoanh/api/admin/pipeline/bulk-approve  → approve by filter (source, confidence_min)
POST /daoanh/api/admin/pipeline/reject/<id>   → reject + note
GET  /daoanh/api/admin/pipeline/runs          → run history
```

---

## Review Queue UI (Admin)

```
┌─────────────────────────────────────────────────────────────────┐
│ Review Queue — 1,234 candidate records                          │
│ Filter: [All ▼] [Source: OLLAMA ▼] [Confidence ≥ 0.6]         │
├─────────────────┬──────┬──────────┬────────┬──────────────────┤
│ Place           │ Năm  │ Source   │ Conf.  │ Evidence         │
├─────────────────┼──────┼──────────┼────────┼──────────────────┤
│ 少林寺 PL023255  │ 495  │ OLLAMA   │ 0.88  │ 太和十九年（495年）│
│ ⚠ 白馬寺 PL001  │ 68   │ REGEX    │ 0.64  │ 重修…（68年）[!]  │
│ 靈隱寺 PL000123  │ 326  │ WIKIDATA │ 0.95  │ Auto-approved ✅  │
├─────────────────┴──────┴──────────┴────────┴──────────────────┤
│ [✅ Approve] [❌ Reject] [⚠ Flag scholar]                       │
│ [Bulk approve: OLLAMA confidence ≥ 0.85 — 234 records]         │
└─────────────────────────────────────────────────────────────────┘
```

**Auto-warning triggers:**
- Evidence chứa `重修|重建|重興` → ⚠ badge, confidence × 0.7
- Confidence < 0.6 → highlight đỏ
- Year ngoài range historical → flag (e.g., year > 1950)

---

## HOME Integration

### places.html — Niên Đại tab

```python
# API: chỉ trả verified records
@app.route("/daoanh/api/places/<place_id>/timeline")
def place_timeline(place_id):
    events = db.execute("""
        SELECT year_ce, label_zh, source, confidence, source_ref
        FROM place_timeline_events
        WHERE dila_id = ? AND verification_status = 'approved'
        ORDER BY year_ce ASC
    """, (place_id,)).fetchall()
    return jsonify(events)
```

```html
<!-- places.html Niên Đại tab -->
<div class="da-block">
  <div class="da-block-label">⏱ Niên Đại</div>
  {% if timeline %}
    <div class="founding-year">
      <span class="year">{{ timeline[0].year_ce }} CE</span>
      <span class="da-chip da-chip-ok">{{ timeline[0].source }}</span>
    </div>
  {% else %}
    <div class="da-warn">⚠ Chưa có dữ liệu niên đại được xác nhận</div>
  {% endif %}
</div>
```

### HOME stats

```python
# API: aggregate stats
@app.route("/daoanh/api/home/timeline-stats")
def timeline_stats():
    return jsonify({
        "total_places": 58167,
        "verified_count": db.scalar("SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events WHERE verification_status='approved'"),
        "by_source": {
            "wikidata": db.scalar("SELECT COUNT(*) FROM place_timeline_events WHERE source='WIKIDATA' AND verification_status='approved'"),
            "chgis": ...,
            "bgis": ...,
            "regex": ...,
            "ollama": ...
        },
        "pipeline_complete_pct": ...,
    })
```

```html
<!-- HOME page stat card -->
<div class="stat-card">
  <div class="stat-number">{{ verified_count | number }}</div>
  <div class="stat-label">Places có niên đại verified</div>
  <div class="stat-sub">/ 58,167 total ({{ pct }}%)</div>
</div>
```

---

## Thứ Tự Triển Khai (Admin quyết định lịch)

| Bước | Việc | Người làm | Thời gian ước tính |
|------|------|-----------|-------------------|
| 0 | Download + inspect BGIS | Admin | 30 phút |
| 1 | Tạo schema + pipeline infra | Dev | 2 giờ |
| 2 | Layer A: Wikidata ETL | Dev + run | 2 giờ |
| 3 | Layer B: CHGIS ETL | Dev + download data | 3 giờ |
| 4 | Layer D: Regex ETL | Dev + run | 1 giờ |
| 5 | Admin review queue UI | Dev | 4 giờ |
| 6 | Layer C: BGIS ETL | Dev + run (nếu Phase 0 OK) | 2 giờ |
| 7 | Layer E: Ollama — batch 1K | Run overnight | Auto |
| 8 | Admin bulk review REGEX batch | Admin | 2-4 giờ |
| 9 | Admin sampling review OLLAMA | Admin | 4-8 giờ |
| 10 | HOME + places.html integration | Dev | 3 giờ |

**Total dev effort:** ~17-20 giờ dev + admin review time.

---

## Acceptance Criteria

- [ ] `place_timeline_events` table tồn tại với schema đầy đủ
- [ ] `pipeline_runs` table tracking đủ layer A-E
- [ ] Layer A: ≥148 Wikidata records approved (direct P1188)
- [ ] Layer B: ≥2,000 CHGIS records processed
- [ ] Layer D: Regex chạy qua tất cả raw_xml không null
- [ ] Layer E: Ollama batch chạy được cho records còn lại
- [ ] Admin dashboard: pipeline control panel hoạt động
- [ ] Admin review queue: approve/reject/bulk-approve hoạt động
- [ ] places.html Niên Đại tab hiển thị `approved` records
- [ ] HOME hiển thị stats (verified count / total)
- [ ] KHÔNG hiển thị `candidate` records cho public

## Constraints

- **KHÔNG sửa DILA source data** — chỉ đọc `places_dila.raw_xml`
- **KHÔNG populate trực tiếp** — phải qua pipeline_runs tracking
- **Admin trigger** mỗi layer — không auto-run toàn bộ
- **Backup** `lineage.db` trước khi chạy Layer E (Ollama writes nhiều)

---

## Nghiên Cứu Thị Trường — 2026-08-27

> **Mục đích:** Xác nhận xem có repo học thuật nào trên thế giới đã giải quyết bài toán founding date cho địa danh Phật giáo chưa — để admin quyết định có nên đầu tư vào Layer E (NLP) hay không.

### Kết Quả Tìm Kiếm (web search 2026-08-27)

**DILA Place Authority (~57K places) — nguồn học thuật lớn nhất:**
- Schema XML/TEI **không có trường `foundingDate`, `inception`, hay `established`**.
- Chỉ có: `note_dynasty` (tên triều đại), `note_content` (text tự do), tọa độ GPS.
- Đây chính xác là lý do PTDA phải tự mine từ text — không có nguồn có cấu trúc tốt hơn.
- Nguồn: [DDBC Authority Open Content — Table Schemas](https://authority.dila.edu.tw/docs/open_content/table_schemas.php), [DILA-edu/Authority-Databases](https://github.com/DILA-edu/Authority-Databases)

**Fosi Zhi (Bingenheimer 2015) — đã khai thác hết trong T45:**
- 237 gazetteers, chỉ **15 có NER markup manual cho dates** (không phải 237).
- PTDA đã khai thác 9/9 gazetteers tải được → 15 rows. Không còn gì ở scale lớn.
- Nguồn: [Lingua Sinica — Bingenheimer 2015](https://linguasinica.springeropen.com/articles/10.1186/s40655-015-0007-3)

**Wikidata — chỉ có chùa nổi tiếng:**
- Có founding dates cho Shaolin (495), Daci'en (648), Longchang... nhưng chỉ các chùa cực kỳ nổi tiếng.
- PTDA đã lấy 155 rows từ Wikidata — đó gần như **toàn bộ** những gì Wikidata biết.
- Không có API/dataset phủ 59K DILA places.

**ChineseBuddhism_SNA (Bingenheimer, 18K nodes):**
- Dataset về **người** (monks, actors), không phải địa điểm. Không có founding date cho chùa.
- Nguồn: [mbingenheimer/ChineseBuddhism_SNA](https://github.com/mbingenheimer/ChineseBuddhism_SNA)

**Việt Nam — gần như zero:**
- Dự án số hóa duy nhất tìm được: pilot **1 chùa** (Thắng Nghiêm, 2014, VNPF).
- Không có database hệ thống nào cho founding dates chùa Việt.
- Nguồn: [Digitizing a Vietnamese Buddhist Temple](https://www.academia.edu/5465460/Digitizing_a_Vietnamese_Buddhist_Temple)

### Kết Luận Cho Admin

**Gap 94.7% là thực trạng toàn cầu, không phải riêng PTDA.**

| Câu hỏi | Trả lời |
|---------|---------|
| Có repo nào đã giải quyết rồi không? | **Không.** Ngay cả DILA — authority database hàng đầu thế giới — cũng không có founding date structured cho phần lớn 57K địa danh. |
| PTDA đang ở đâu so với world-state-of-the-art? | **Leading edge.** 5.31% (3,141 places) sau tích hợp T39/T41/T45 là tốt hơn tất cả repo học thuật đang publish. |
| Nếu muốn vượt 10% coverage, phải làm gì? | **Không có shortcut.** Layer E (NLP/Ollama trên `raw_xml`) là con đường duy nhất còn lại ở quy mô lớn. |
| Tên tiếng Việt cho places — có nguồn ngoài không? | **Không.** Không một repo học thuật quốc tế nào cung cấp. ZQ là đơn vị duy nhất làm việc này. |

### Nhận Định Về Layer E (NLP — Ollama)

Layer E **không phải luxury** — đây là **điều kiện cần** để vượt ngưỡng 10%:

- Structured sources (Wikidata + CHGIS + BGIS + Regex) tối đa có thể cho ~20K rows nhưng phần lớn overlap với 3K đã có.
- Phần lớn 56K places còn lại chỉ có narrative text trong `raw_xml` — không ai sẽ cung cấp thông tin này ngoài NLP.
- **Chi phí:** Local Ollama (`qwen2.5:7b`) — không tốn tiền API, chạy overnight, cần admin review queue.
- **Rủi ro:** False positives (renovation ≠ founding) → cần review workflow đã thiết kế ở trên.

**Gợi ý cho admin:** Nếu mục tiêu là >10% coverage trong năm 2026, Layer E là bắt buộc. Nếu chấp nhận 5-6% từ structured sources, có thể skip Layer E và chỉ làm Layers A-D.

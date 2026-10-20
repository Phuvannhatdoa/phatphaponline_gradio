# Session 2026-09-07 — T101 Graph/Nexus Bug Fix

## Tóm tắt

Audit bởi `daoanh-debugger` agent (query DB thật + đọc source). Root entity: Thiếu Lâm Tự `PL000000023255`.
Phát hiện 5 bugs; fix 3 bugs trong session này (BUG-001/004/005). BUG-002/003 là migration DB cần task riêng.

## Files sửa

| File | Thay đổi |
|------|---------|
| `app.py` | BUG-001: `_resolve_dila_id` + `api_nexus` place label_zh; BUG-004: thêm `place_person_link` query vào `api_places_graph` |
| `places.html` | BUG-005: expand `_DYNASTY_VI`, `_fmtDynasty` split multi-value, subgroup label dùng `_fmtDynasty` |

## Backup

`docs/sessions/2026-09-07/app.py.bak_t101`  
`docs/sessions/2026-09-07/places.html.bak_t101`

## BUG-001 — Label Hán sai ở center node

**Evidence:** `SELECT name, name_zh FROM places_dila WHERE id='PL000000023255'` → `name='少林寺'`, `name_zh='少室寺'`

**Fix `_resolve_dila_id` (app.py:4052-4057):**
```python
# Trước:
dila_row = conn.execute("SELECT name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
if dila_row:
    return place_id, dila_row['name_zh']
# Sau:
dila_row = conn.execute("SELECT name, name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
if dila_row:
    return place_id, dila_row['name'] or dila_row['name_zh']
```

**Fix `api_nexus` place branch (app.py ~5135-5141):**
```python
# Trước: "label_zh": pl['name_zh']
# Sau:   _pl_label_zh = pl['name'] or pl['name_zh']
#        "label_zh": _pl_label_zh
```

## BUG-004 — Curated links không xuất hiện trong Đồ Thị

**Evidence:** `place_person_link` có 2 rows (A001361 Bồ Đề Đạt Ma, A003881 Huệ Khả) với source `景德傳燈錄 T51n2076`.

**Fix:** Thêm query `place_person_link` vào `api_places_graph` sau khối `nexus_rows`. Dedupe qua `seen_pids`. Edge type `with_evidence` (solid). Graceful try/except nếu bảng không tồn tại.

## BUG-005 — Dynasty string chưa chuẩn hoá

**Evidence:** `people.dynasty` chứa `'北宋\n    五代十國'` (multi-value) và `'印度'` (quốc gia).

**Fix `_DYNASTY_VI`:** Thêm `北宋, 南宋, 五代十國, 北齊, 北魏, 南朝, 陳, 元, 漢, 晉, 唐宋`.

**Fix `_fmtDynasty`:** Split trên `[\n\/,，;；]+`, trim từng phần, join bằng ` · `. `_NON_DYNASTY` set (`印度`, `中亞`…) → hiển thị nguyên tên.

**Fix subgroup label (places.html:5550):** Dùng `_fmtDynasty(dyn)` thay vì `_DYNASTY_VI[dyn] || dyn`.

## Verify

- `python -m py_compile app.py` → **PASS**
- `node --check places_inline.js` (363,655 chars, 1 block) → **PASS**

## Pending (BUG-002/003)

- BUG-002: `place_person_bibl` 4 dòng mismatch person_id (A002000/A009319/A009365/A008784) — cần script migration riêng
- BUG-003: `event_text_link` confidence sai cho NULL-person rows — cần re-run ETL

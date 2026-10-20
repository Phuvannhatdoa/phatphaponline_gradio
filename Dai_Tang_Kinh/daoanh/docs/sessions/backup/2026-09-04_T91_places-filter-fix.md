# Session 2026-09-04 — T91: Places Map Category Filter Fix

## Task
Fix category filter trên trang `/daoanh/places` — click pill "⛩ Chùa / Tự viện" không hiện marker trên Leaflet map.

## Root Cause (confirmed bằng DB query)

1. `note_category` column **không tồn tại** trong table `places` → `sqlite3.OperationalError`
2. `except Exception: pass` swallow error → API trả `{"ok": true, "count": 0}` — silent failure
3. `place_type` column tồn tại nhưng NULL cho toàn bộ 58,476 GPS records

## Fix Applied

### `app.py` — route `/daoanh/api/places/search`
- `CATE_LIKES` dict dùng `name_zh` Chinese keyword patterns thay `note_category` ontology patterns
- SQL condition đổi từ `p.note_category LIKE ?` → `p.name_zh LIKE ?`
- Patterns verified: temple 8,871 records, mountain 2,743, river/lake 2,104

### `places.html`
- `cate-filter-bar` từ `position:absolute` (bị map đè) → static flex row, nằm trên map
- Lưu ý: Tailwind CSS KHÔNG load trong trang này — dùng inline styles, không dùng utility class `hidden`/`absolute`

## Commit
```
fix(T91): places category filter — dùng name_zh LIKE thay note_category (ko tồn tại); filter bar static above map
```

## Deploy
VPS: `root@158.220.106.183:/opt/phatphaponline_gradio/daoanh/`
```bash
scp app.py places.html root@158.220.106.183:/opt/phatphaponline_gradio/daoanh/
ssh root@158.220.106.183 "pkill -f 'python.*app.py' || true; cd /opt/phatphaponline_gradio/daoanh && nohup python app.py &"
```

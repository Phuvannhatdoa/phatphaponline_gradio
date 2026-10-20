---
id: T07
title: Wikipedia multi-language fallback + cache refresh
module: Wikipedia
priority: low
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-23
done_when: Tab 地 Thực Thể hiển thị mô tả Wikipedia (vi → zh → en fallback), có nút "Làm mới", disclaimer CC BY-SA đúng format
---

# T07 — Wikipedia multi-language fallback + cache refresh

## Mục tiêu
Wikipedia summary hiện chỉ fetch 1 ngôn ngữ, không có nút refresh. Cần cải thiện để địa danh Trung Quốc (không có wiki tiếng Việt) vẫn có mô tả qua zh/en fallback.

## Hiện Trạng (audit 2026-08-20)

Wikipedia route đang có trong `app.py` nhưng chưa verify fallback logic. Cần grep app.py để xác nhận:
```bash
grep -n "wikipedia\|wiki_cache\|wiki_lang" app.py | head -20
```

## Chỉ thị thực hiện

**Bước 1 — Audit route hiện tại:**
- Grep `app.py` tìm route `/api/places/<id>/wikipedia` hoặc tương đương
- Xác nhận: hiện có fallback vi→zh→en không? Cache lưu ở đâu (DB bảng gì)?

**Bước 2 — Nếu chưa có fallback, thêm vào route:**
```python
WIKI_LANG_FALLBACK = ['vi', 'zh', 'en']
for lang in WIKI_LANG_FALLBACK:
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
    resp = requests.get(url, timeout=5)
    if resp.ok and resp.json().get('extract'):
        # cache + return
        break
```

**Bước 3 — Cache refresh:**
- Thêm endpoint `POST /api/places/<id>/wikipedia/refresh` hoặc param `?refresh=1`
- Xóa row cũ trong cache table, fetch lại

**Bước 4 — Frontend places.html:**
- Thêm nút "🔄 Làm mới" nhỏ bên cạnh section Wikipedia trong tab 地 Thực Thể
- Hiển thị lang badge: `[vi]` / `[zh]` / `[en]` để biết đang dùng ngôn ngữ nào
- Disclaimer: `Nội dung từ Wikipedia · CC BY-SA`

## Ghi chú thêm 2026-08-23

Trong lúc build song song với phiên kia (cùng làm T07 cùng lúc), gặp `SyntaxError: Identifier
'_wikiPlaceId' has already been declared` — cả 2 phiên đều tự viết `loadWiki()`/`refreshWiki()`
trùng tên. Xử lý: giữ bản JS của phiên kia (định nghĩa gần `baseUrl`, có `if (!block) return` guard
tốt hơn), bỏ bản JS trùng của mình, chỉ giữ lại phần HTML (`#wikiBlock` và các con) mà JS đó đang
thiếu + gọi `loadWiki()` đúng chỗ trong `selectItem()`.

Cũng fix thêm 1 bug hiển thị phát hiện khi test: `snippet` giữ nguyên HTML entity (`&quot;`) vì
code cũ chỉ dùng regex strip `<tag>` mà không unescape entity — thêm `html.unescape()` trong
`_wiki_search_lang()`.

## Acceptance criteria (checklist)
- [x] Grep app.py xác nhận route Wikipedia hiện tại — đã có `POST /daoanh/api/admin/wiki/fetch` với vi→zh→en fallback logic
- [x] Fallback vi → zh → en hoạt động (backend đã implement T07 2026-08-22)
- [x] Cache refresh — `refresh: true` param trong POST body → DELETE cached row + re-fetch
- [x] `loadWiki()` + `refreshWiki()` viết vào places.html (2026-08-23) — fire-and-forget, không block entity render
- [x] Nút "🔄 Làm mới" onclick="refreshWiki()" đã có trong HTML; function đã wired
- [x] Lang badge `wikiLangBadge` hiển thị VI/ZH/EN tùy ngôn ngữ trả về
- [x] Disclaimer CC BY-SA 4.0 đúng format trong `#wikiBlock`

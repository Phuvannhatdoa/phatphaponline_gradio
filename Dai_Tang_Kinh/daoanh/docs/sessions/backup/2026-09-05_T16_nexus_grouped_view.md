# Session: Nexus Grouped View (T16 Spec)

**Ngày:** 2026-09-05  
**Task:** T16 Nexus Points → Grouped View per JSON spec

---

## Thay đổi

### 1. `app.py` — `api_nexus()` (line ~5178)

Thêm 2 field vào response:

**`aliases`** (place only): Parse từ `places_dila.raw_xml` bằng regex `<placeName>` tags.  
Ví dụ Thiếu Lâm Tự: `["少林寺","陟岵寺","僧人寺","少林"]`

**`groups`** (place only):
```json
{
  "kinh_dien": 3,
  "tang_nhan": {"唐": 10, "隋": 4, "清": 2, ...},
  "tang_nhan_total": 24
}
```
Kinh điển = COUNT(DISTINCT sigla) từ `cbeta_ref` qua `event_text_link`.  
Tăng nhân = COUNT per `p.dynasty` từ `event_text_link JOIN people`.

**`dynasty`** field thêm vào mỗi person node (SELECT name_zh, name_vi, **dynasty** FROM people).

### 2. `places.html` — HTML (line ~742)

Thêm `<div id="nmp-aliases">` sau header, ẩn mặc định:
```html
<div id="nmp-aliases" style="display:none;padding:3px 20px;...flex-wrap:wrap;gap:4px"></div>
```

### 3. `places.html` — `_renderNexusMainPanel()` (JS)

Sau khi update header, thêm:
- Render alias chips vào `nmp-aliases`
- Nếu `d.groups && d.entity_type === 'place'`: reset expansion state (khi đổi entity), gọi `_nexusRenderGrouped(d)` và return sớm

### 4. `places.html` — `_nexusRenderGrouped(d)` (JS mới)

State variables: `_nexusGroupState = {expanded, subexpanded}`, `_nexusCurrentGroupId`  
Dynasty mapping: `_DYNASTY_VI = {唐:'Đường', 宋:'Tống', ...}`

**Default (collapsed):** 3 nút — center + Kinh điển group + Tăng nhân group  
**Click Kinh điển:** Expand thành text nodes, dedup theo sigla (T50n2060, T50n2061, T50n2062) → 6 nút  
**Click Tăng nhân:** Expand thành dynasty subgroup nodes → 13 nút  
**Click dynasty (vd. 唐):** Filter `n.dynasty === dyn` → hiển thị persons cho đúng triều đại → 23 nút (3+10+10)

Click lại node đã expand → collapse (toggle). Click person node → `_nexusShowDetail()`.

---

## Verified

- Thiếu Lâm Tự: aliases 少林寺/陟岵寺/僧人寺/少林 ✓
- Default view: 3 nút ✓
- Kinh điển expand: 3 text nodes (không duplicate) ✓
- Tăng nhân expand: 10 dynasty subgroups ✓
- Đường expand: 10 persons (filtered) ✓
- Filter count hiển thị "N nút (nhóm)" ✓

---

## Hạn chế còn lại

- Persons không có dynasty (null) chỉ thấy khi click "(không rõ)" subgroup
- Edge semantics (solid/dotted per evidence) chưa implement
- Person filter theo dynasty dựa trên `people.dynasty` — một số monks có dynasty string dài (vd. "北宋\n    五代十國") cần normalize

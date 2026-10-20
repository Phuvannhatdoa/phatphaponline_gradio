# Session 2026-09-29 — Changes Log

## BUG-017 — Canh lề sai "Được đề cập trong 🇻🇳"

**File sửa:** `daoanh/admin/person.html` line 295  
**Backup:** `docs/sessions/2026-09-29/person.html.bak`

**Thay đổi:**
```diff
- var mentioned_vi = vi_.mentioned_in_vi || '';
+ var mentioned_vi = normMultiline(vi_.mentioned_in_vi || '');
```

**Lý do:** Block "Được đề cập trong" build HTML thủ công, không qua `cellVi()`, 
nên bỏ sót bước `normMultiline()`. Leading space trong data bị `white-space:pre-wrap` 
giữ nguyên → dòng 2 lệch 1 space.

**Trạng thái:** Code fixed. Chờ Admin verify trên UI và confirm.

---

## Feature — Autocomplete "Tên thầy" trong monk_ttl_add

**File sửa:** `daoanh/admin/monk_ttl_add.html`  
**Backup:** `docs/sessions/2026-09-29/monk_ttl_add.html.bak`

**Thay đổi:**
- Input `#teacher_vi` thêm `list="monk-names-list"` + `autocomplete="off"`
- Thêm `<datalist id="monk-names-list"></datalist>` ngay dưới input
- Thêm hint nhỏ hiển thị số tên đã nạp
- Thêm hàm `loadMonkNames()`: fetch `/daoanh/monk_names_vn.json` → populate datalist
- Gọi `loadMonkNames()` trong init

**Nguồn dữ liệu v2:** `GET /daoanh/api/admin/monk_names_slugs` (đọc TTL files, trả `{name_vi, slug}`)  
**Cơ chế:** Native HTML `<datalist>` + `_monkSlugMap` JS object  
**Behavior khi chọn tên:** `autoTeacherSlug()` → tra `_monkSlugMap[name]` → fill slug chính xác từ TTL;  
nếu là tên mới chưa có trong hệ thống → fallback `slugify()`.

---

## Feature — Import TTL Template vào form (monk_ttl_add)

**Files sửa:** `daoanh/admin/monk_ttl_add.html` + `daoanh/app.py`  
**Backup app.py:** `docs/sessions/2026-09-29/app.py.bak`

### app.py — API mới
- `GET /daoanh/api/admin/monk_names_slugs`: đọc `data/ttl/*.ttl`, parse `bkg:Monk` + `rdfs:label @vi` → `[{name_vi, slug}]`

### monk_ttl_add.html — Import TTL button
- Nút "Import TTL" (label wrapping hidden `<input type=file accept=".ttl">`)
- `importTTLFile(input)`: FileReader đọc file .ttl
- `parseTTLIntoForm(ttl)`: regex parse đầy đủ → fill form fields:
  - slug, name_vi, name_zh, bio_vi (strip HTML tags), birth/death_year
  - teacher_slug (từ `bkg:hasTeacher`), teacher_vi (lookup `_monkSlugMap` hoặc stub label)
  - disciples (name | slug pairs)
  - lineage (match dropdown hoặc fill custom input)
  - gen_order, is_founder
- Sau fill: `calcGen()` + `livePreview()` + status message
- Workflow: Admin chọn file → form tự điền → xem Preview TTL → sửa nếu cần → nhấn Lưu

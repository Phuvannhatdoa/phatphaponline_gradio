# Design Spec — Đạo Ảnh UI System

**Phiên bản:** 1.0  
**Ngày:** 2026-08-17  
**Mockup tham khảo:** https://claude.ai/code/artifact/a0606ab7-ae4f-4fe9-bf9b-ac3ebf3cdb55  
**CSS file:** `daoanh/styles/daoanh-design.css`

---

## 0. Quy tắc vàng cho OpenCode

1. **Không hardcode màu hex trong component.** Luôn dùng token `var(--da-*)`.
2. **Không dùng CDN font.** CSP block external. Dùng system font stack trong token.
3. **Mọi page mới phải link CSS token file:**
   ```html
   <link rel="stylesheet" href="/daoanh/styles/daoanh-design.css">
   ```
4. **Màu semantic ≠ màu accent.** `--da-green` = done, `--da-amber` = partial, `--da-red` = error/pending — dùng đúng ngữ cảnh, không thay bằng gold.
5. **Status T-badge.** Mọi feature chưa implement hiển thị: `<span style="color:var(--da-red)">T14 pending</span>` — không ẩn đi.

---

## 1. Token Reference

### Surfaces

| Token | Light | Dark | Dùng cho |
|-------|-------|------|---------|
| `--da-bg` | `#f0ebe0` | `#06090f` | `<body>` background |
| `--da-panel` | `#e6e0d5` | `#0c1322` | Nav, sidebar, modals |
| `--da-card` | `#dbd5c8` | `#111827` | Cards, cells, passages |
| `--da-border` | `rgba(0,0,0,.09)` | `rgba(255,255,255,.06)` | Tất cả borders |

### Text

| Token | Light | Dark | Dùng cho |
|-------|-------|------|---------|
| `--da-text` | `#1a1a28` | `#dce5f4` | Body text |
| `--da-muted` | `#6a5f4d` | `#4a6080` | Labels, secondary |
| `--da-dim` | `#a89d8e` | `#1e2d45` | Placeholders, disabled |

### Accent

| Token | Light | Dark | Dùng cho |
|-------|-------|------|---------|
| `--da-gold` | `#8a5c08` | `#c4891a` | Primary accent, borders |
| `--da-gold-b` | `#ad7c1c` | `#f0a635` | Hover states, text |
| `--da-gold-bg` | `rgba(138,92,8,.10)` | `rgba(196,137,26,.12)` | Chip/button fill |
| `--da-gold-ring` | `rgba(138,92,8,.22)` | `rgba(196,137,26,.28)` | Active borders |

### Semantic

| Token | Nghĩa | Ví dụ |
|-------|-------|-------|
| `--da-cyan` | data / link / GPS / mono ref | CBETA ID, coordinates |
| `--da-green` | done / verified / ok | Đã duyệt, FTS xong |
| `--da-amber` | partial / warning | CBETA partial, 3/8 |
| `--da-red` | pending / error / blocked | T14 pending, 0 rows |

### Fonts

```css
--da-font-serif: 'Palatino Linotype', 'Book Antiqua', Palatino, serif;
--da-font-ui:    system-ui, -apple-system, 'Segoe UI', sans-serif;
--da-font-mono:  'Cascadia Code', 'JetBrains Mono', 'Courier New', monospace;
```

Quy tắc:
- **Serif** → entity names (vi + zh), block quotes, CBETA passages, ghi chú học thuật
- **UI** → mọi label, button, nav, tab, stat
- **Mono** → DILA ID, GPS coords, JDN, CBETA ref, API paths, status codes

---

## 2. Component Inventory

### 2.1 Nav bar `.da-nav`

```html
<nav class="da-nav">
  <div class="da-nav-glyph">卍</div>
  <div>
    <div class="da-nav-brand-main">Phật Tổ Đạo Ảnh</div>
    <div class="da-nav-brand-sub">Buddhist GIS Authority · DILA / CBETA</div>
  </div>
  <!-- search + .da-mod-btn + theme toggle -->
</nav>
```

Quy tắc: `da-nav-brand-main` dùng `var(--da-font-serif)`. Module buttons: class `da-mod-btn`, active state thêm class `active`.

---

### 2.2 Sidebar tabs `.da-stabs` / `.da-stab`

```html
<div class="da-stabs">
  <button class="da-stab active" data-t="entity">地 Thực Thể</button>
  <button class="da-stab" data-t="cbeta">📜 Đại Tạng</button>
  <button class="da-stab" data-t="graph">🕸 Đồ Thị</button>
  <button class="da-stab" data-t="tl">⏱ Niên Đại</button>
</div>
```

Tab switching bằng JS: toggle class `active` trên tab và panel. Panel mặc định `display:none`, active panel `display:block`.

---

### 2.3 Entity Header

```html
<div class="da-entity-header">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:7px">
    <span class="da-entity-id">PL000000023255</span>
    <span class="da-entity-type">· 地 ĐỊA ĐIỂM · DILA</span>
  </div>
  <div class="da-entity-vi">Thiếu Lâm Tự</div>
  <div class="da-entity-zh">少林寺</div>
</div>
```

---

### 2.4 Block section `.da-block`

Mọi section trong sidebar đều bọc trong `.da-block`:

```html
<div class="da-block">
  <div class="da-block-label">Tên Section</div>
  <!-- content -->
</div>
```

`da-block-label` tự thêm gold rule via `::before` — không cần SVG hay thêm element.

---

### 2.5 Source provenance chips

```html
<div class="da-chips">
  <span class="da-chip da-chip-ok">✓ DILA</span>
  <span class="da-chip da-chip-partial">~ CBETA</span>
  <span class="da-chip da-chip-none">○ BDRC</span>
</div>
```

| Class | Trạng thái | Màu |
|-------|-----------|-----|
| `da-chip-ok` | Đã import, đang dùng | green |
| `da-chip-partial` | Partial / bản thảo | amber |
| `da-chip-none` | Pending / chưa có | dim/muted |

---

### 2.6 Location 3-layer RAG

```html
<div class="da-loc-layers">
  <div class="da-loc-row">
    <span class="da-loc-badge">DILA L1</span>
    <span class="da-loc-value">Trung Quốc · 中國</span>
  </div>
  <div class="da-loc-row">
    <span class="da-loc-badge">DILA L2</span>
    <span class="da-loc-value">Tỉnh Hà Nam · 河南省</span>
  </div>
  <div class="da-loc-row">
    <span class="da-loc-badge">GEONAMES</span>
    <span class="da-loc-value">Đăng Phong Thị, Trịnh Châu</span>
  </div>
</div>
<div class="da-gps">
  <span>34.5085°N</span>
  <span>112.9376°E</span>
</div>
```

Badge text: `DILA L1` / `DILA L2` / `GEONAMES` / `PLACES_VPS` / `USER`. GPS luôn mono `--da-cyan`.

---

### 2.7 Time grid `.da-time-grid`

```html
<div class="da-time-grid">
  <div class="da-time-cell">
    <div class="da-time-cell-label">Triều Đại</div>
    <div class="da-time-cell-value serif">北魏 Bắc Ngụy</div>
  </div>
  <div class="da-time-cell">
    <div class="da-time-cell-label">Kiến Lập</div>
    <div class="da-time-cell-value">495 CE</div>
  </div>
  <div class="da-time-cell">
    <div class="da-time-cell-label">Niên Hiệu</div>
    <div class="da-time-cell-value serif">Thái Hòa 19</div>
  </div>
  <div class="da-time-cell">
    <div class="da-time-cell-label">JDN</div>
    <div class="da-time-cell-value mono">1902154</div>
  </div>
</div>
<div class="da-warn">⚠ time_periods = 0 rows · Task T14 pending</div>
```

Modifier `.serif` → Palatino. `.mono` → monospace + cyan.

---

### 2.8 CBETA Passage block

```html
<div class="da-passage">
  <div class="da-passage-ref">
    <span>T50n2060_p0457b16 · 續高僧傳</span>
    <span class="da-chip da-chip-none" style="padding:1px 6px;font-size:7.5px">Chưa dịch</span>
  </div>
  <div class="da-passage-han">少林寺者，後魏孝文皇帝所立也…</div>
  <!-- nếu đã dịch: -->
  <div class="da-passage-vi">Thiếu Lâm Tự được Hiếu Văn Đế nhà Bắc Ngụy lập nên…</div>
  <div class="da-passage-actions">
    <button class="da-btn da-btn-primary">Dịch Mượt →</button>
    <button class="da-btn">CBETA Online</button>
    <button class="da-btn">Gắn nhân vật</button>
  </div>
</div>
```

`da-passage-vi` chỉ render khi đã có bản dịch (translation_status = admin_approved | draft).

---

### 2.9 Person row / Nexus badge

```html
<div class="da-person-row">
  <div class="da-person-avatar">菩</div>
  <div style="flex:1;min-width:0">
    <div class="da-person-name-vi">Bồ Đề Đạt Ma</div>
    <div class="da-person-name-zh">菩提達摩 · Tổ thiền Đông Độ</div>
  </div>
  <span class="da-nexus-badge">NEXUS</span>
</div>
```

Avatar: ký tự đầu tiên của tên Hán. NEXUS badge xuất hiện khi person có giao điểm place+time trong CBETA.

---

### 2.10 Status bars

```html
<div class="da-status-list">
  <div class="da-status-row">
    <span class="da-status-name">Tên Việt</span>
    <div class="da-status-track">
      <div class="da-status-fill da-fill-done" style="width:100%"></div>
    </div>
    <span class="da-status-label da-label-done">Đã duyệt</span>
  </div>
  <div class="da-status-row">
    <span class="da-status-name">CBETA</span>
    <div class="da-status-track">
      <div class="da-status-fill da-fill-part" style="width:25%"></div>
    </div>
    <span class="da-status-label da-label-part">3/12 đoạn</span>
  </div>
</div>
```

`width` tính theo % thực tế. Labels: `da-label-done` / `da-label-part` / `da-label-none`.

---

### 2.11 Warning banner `.da-warn`

Dùng cho mọi feature `pending` hoặc data thiếu:

```html
<div class="da-warn">⚠ time_periods = 0 rows · Task T14 pending</div>
```

---

### 2.12 Dynasty filter bar

```html
<div class="da-dynasty-bar">
  <button class="da-d-btn active">Tất cả <span style="opacity:.45">300</span></button>
  <button class="da-d-btn">唐 Đường <span style="opacity:.45">142</span></button>
</div>
```

---

### 2.13 Architecture overlay

```html
<div class="da-overlay" id="archOverlay">
  <div class="da-modal">
    <button class="da-modal-close" onclick="...">✕</button>
    <div class="da-modal-title">Kiến Trúc Hệ Thống</div>
    <div class="da-modal-sub">4-Layer Data Model · v30+</div>
    <!-- content -->
  </div>
</div>
```

Toggle: `overlay.classList.toggle('open')`. Click ngoài modal → close.

---

## 3. Quy ước Page Layout

```
fixed <nav class="da-nav"> 56px
└── <div style="display:flex;height:calc(100vh - 56px)">
    ├── <aside class="da-sidebar">  ← 385px, overflow-y:auto
    │   ├── <div class="da-stabs">
    │   └── <div class="da-scroll">
    │       └── tab panels
    └── <main style="flex:1;position:relative">  ← map/content
        └── <div class="da-bottom-bar"> (absolute bottom-14px)
```

---

## 4. Tích Hợp Dần — Thứ Tự Ưu Tiên

| Bước | Việc cần làm | File | Ghi chú |
|------|-------------|------|---------|
| 1 | Link `daoanh-design.css` vào `places/index.html` | `places/index.html` | Thêm `<link>` vào `<head>` |
| 2 | Đổi sidebar sang dùng token `var(--da-*)` | `places/index.html` | Xóa hardcode hex |
| 3 | Thêm tab bar 4 tabs | `places/index.html` | Thay sidebar tĩnh hiện tại |
| 4 | Thêm Source Provenance block | `places/index.html` + `app.py` | API `/places/{id}` trả thêm `source_ids[]` |
| 5 | Thêm Time Authority block | `places/index.html` | Show warn khi T14 pending |
| 6 | Thêm Person/Nexus block | `places/index.html` + `app.py` | API `/places/{id}/persons` |
| 7 | Thêm CBETA tab | `places/index.html` + `app.py` | API `/places/{id}/passages` |
| 8 | Thêm Graph tab (T17) | sau khi T17 xong | Canvas vis-network |
| 9 | Đổi `placevn.html` admin dùng cùng token | `admin/placevn.html` | Thống nhất visual |

---

## 5. Màu Hiện Tại Cần Migrate

Các giá trị hardcode trong codebase → đổi sang token:

| Hardcode | Token tương đương |
|----------|-----------------|
| `#f39c12` / `#fbbf24` | `var(--da-gold-b)` |
| `#d4921e` / `#c4891a` | `var(--da-gold)` |
| `#020617` | `var(--da-bg)` |
| `#0a0c10` | `var(--da-bg)` |
| `#0f172a` | `var(--da-panel)` |
| `rgba(22,28,38,.8)` | `var(--da-card)` |
| `#e2e8f0` | `var(--da-text)` |
| `#94a3b8` | `var(--da-muted)` |
| `#22d3ee` | `var(--da-cyan)` |

---

## 6. Không Làm

- Không dùng Tailwind `text-amber-500` trực tiếp — wrap vào token trước.
- Không tạo màu mới ngoài bảng token — mở rộng token trước, rồi dùng.
- Không hardcode `font-family` trong component — dùng `var(--da-font-*)`.
- Không thêm CDN font `@import url(...)` — system font stack đã đủ.
- Không xóa `da-warn` khi feature chưa implement — giữ lại để admin biết.

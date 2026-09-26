# HOME GUI Redesign — Spec đã phê chuẩn

**Ngày phê chuẩn:** 2026-08-30  
**Mockup:** https://claude.ai/code/artifact/7c6fd489-47f7-4319-b41d-88b23bcff41e  
**Tasks:** T75–T79 trong `dashboard/tasks.md` (Bước 8)  
**File mục tiêu:** `daoanh/home.html`

---

## 1. Lý do redesign

Cấu trúc `home.html` hiện tại (accordion + 15 TABs + nhiều panel) gây overload thông tin ngay khi tải. Người dùng muốn tìm 1 địa danh / tu sĩ cụ thể nhưng không biết bắt đầu từ đâu. Design mới ưu tiên:

1. **Search-first** — ô tìm kiếm hero nổi bật, không cần browse
2. **6 module cards** — điểm vào rõ ràng cho từng module
3. **Inline demo** — kết quả tìm kiếm hiện ngay trang chủ, không chuyển trang mặc định

---

## 2. Design Tokens

```css
:root {
  --da-bg:       #0B0E17;   /* near-black, dark navy */
  --da-panel:    #141824;   /* card surface */
  --da-border:   rgba(255,255,255,0.07);
  --da-gold:     #C9A84C;   /* accent chính */
  --da-gold-dim: rgba(201,168,76,0.15);
  --da-text:     #E8E3D8;   /* body text */
  --da-muted:    rgba(232,227,216,0.5);
  --da-radius:   12px;
}
```

**Màu module cards:**

| Module | Token | Hex |
|---|---|---|
| Địa Danh | gold | `#C9A84C` |
| Đại Tạng | amethyst | `#8B5CF6` |
| Tu Sĩ | teal | `#14B8A6` |
| Truyền Thừa | rose | `#F43F5E` |
| Niên Đại | sky | `#0EA5E9` |
| Đồ Thị Quan Hệ | amber | `#F59E0B` |

**Typography:**

```html
<link rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&family=Inter:wght@400;500;600&display=swap">
```

- Display / heading: `Noto Serif SC`
- UI / body: `Inter`

---

## 3. Cấu trúc layout

```
┌─────────────────────────────────────────┐
│  header nav (giữ nguyên nav hiện tại)   │
├─────────────────────────────────────────┤
│                                         │
│       [HERO SEARCH]                     │
│   Đạo Ảnh — Bản đồ Phật giáo           │
│   ┌────────────────────────────────┐    │
│   │ 🔍  Nhập địa danh, tu sĩ...   │    │
│   └────────────────────────────────┘    │
│                                         │
│   ┌── #placeResult (ẩn ban đầu) ──┐     │
│   │  Thiếu Lâm Tự card            │     │
│   └────────────────────────────────┘    │
│                                         │
├─────────────────────────────────────────┤
│  [6 MODULE CARDS — 3×2 grid]            │
│  Địa Danh  Đại Tạng  Tu Sĩ             │
│  Truyền Thừa  Niên Đại  Đồ Thị         │
└─────────────────────────────────────────┘
```

---

## 4. Hero Search — HTML

```html
<section class="da-hero">
  <h1 class="da-hero-title">Đạo Ảnh</h1>
  <p class="da-hero-sub">Bản đồ Phật giáo · Địa danh · Kinh điển · Tu sĩ</p>
  <form class="da-search-form" onsubmit="handleSearch(event)">
    <div class="da-search-wrap">
      <input id="heroSearch" type="text" class="da-search-input"
             placeholder="Nhập địa danh, tu sĩ, kinh điển…"
             autocomplete="off">
      <button type="submit" class="da-search-btn">Tìm</button>
    </div>
  </form>
</section>
```

---

## 5. Inline Place Result Panel `#placeResult`

Hiện khi search "Thiếu Lâm" hoặc "少林". Ẩn mặc định (`display:none`), hiện qua class `visible`.

```html
<div class="sr-wrap" id="placeResult">
  <div class="sr-card">
    <div class="sr-header">
      <div>
        <span class="sr-label">Địa danh</span>
        <h2 class="sr-title">Thiếu Lâm Tự</h2>
        <div class="sr-names">
          <span class="sr-name-hv">少林寺</span>
          <span class="sr-name-en">Shaolin Temple</span>
        </div>
      </div>
      <button class="sr-close" onclick="closePlaceDemo()">✕</button>
    </div>
    <div class="sr-body">
      <div class="sr-info">
        <div class="sr-grid">
          <div class="sr-field"><span class="sr-key">Quốc gia</span><span class="sr-val">Trung Quốc</span></div>
          <div class="sr-field"><span class="sr-key">Tỉnh</span><span class="sr-val">Hà Nam</span></div>
          <div class="sr-field"><span class="sr-key">Loại</span><span class="sr-val">Tự viện</span></div>
          <div class="sr-field"><span class="sr-key">Tông phái</span><span class="sr-val">Thiền tông</span></div>
          <div class="sr-field"><span class="sr-key">Thành lập</span><span class="sr-val">495 SCN</span></div>
          <div class="sr-field"><span class="sr-key">ID</span><span class="sr-val sr-id">PL000000023255</span></div>
        </div>
        <div class="sr-tags">
          <span class="sr-chip">DILA BGIS</span>
          <span class="sr-chip">CBETA</span>
        </div>
        <div class="sr-actions">
          <a class="sr-btn primary" href="/daoanh/places?q=PL000000023255">Xem trên bản đồ</a>
          <a class="sr-btn secondary" href="/daoanh/places?q=PL000000023255">Chi tiết</a>
        </div>
      </div>
      <div class="sr-map">
        <!-- SVG mini-map Trung Quốc, Hà Nam highlighted -->
        <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
          <rect width="200" height="160" fill="#1a2035" rx="8"/>
          <!-- ... SVG paths từ mockup đã approved ... -->
          <circle cx="118" cy="80" r="6" fill="#C9A84C" opacity="0.9"/>
          <text x="118" y="100" text-anchor="middle" fill="#C9A84C"
                font-family="Inter" font-size="9">Hà Nam</text>
        </svg>
        <p class="sr-map-label">Hà Nam, Trung Quốc</p>
      </div>
    </div>
  </div>
</div>
```

---

## 6. 6 Module Cards

```html
<section class="da-modules">
  <h2 class="da-modules-title">Khám phá theo chủ đề</h2>
  <div class="da-modules-grid">
    <a class="da-mod-card" href="/daoanh/places" style="--mod-color:#C9A84C">
      <div class="da-mod-icon">🗺</div>
      <div class="da-mod-name">Địa Danh</div>
      <div class="da-mod-desc">Bản đồ tự viện, thánh địa</div>
    </a>
    <a class="da-mod-card" href="/daoanh/tripitaka" style="--mod-color:#8B5CF6">
      <div class="da-mod-icon">📖</div>
      <div class="da-mod-name">Đại Tạng</div>
      <div class="da-mod-desc">Kinh điển Hán tạng CBETA</div>
    </a>
    <a class="da-mod-card" href="/daoanh/people" style="--mod-color:#14B8A6">
      <div class="da-mod-icon">🧘</div>
      <div class="da-mod-name">Tu Sĩ</div>
      <div class="da-mod-desc">Cao tăng, thiền sư, tổ sư</div>
    </a>
    <a class="da-mod-card" href="/daoanh/lineage" style="--mod-color:#F43F5E">
      <div class="da-mod-icon">🌿</div>
      <div class="da-mod-name">Truyền Thừa</div>
      <div class="da-mod-desc">Dòng truyền, pháp mạch</div>
    </a>
    <a class="da-mod-card" href="/daoanh/timeline" style="--mod-color:#0EA5E9">
      <div class="da-mod-icon">📅</div>
      <div class="da-mod-name">Niên Đại</div>
      <div class="da-mod-desc">Dòng thời gian lịch sử</div>
    </a>
    <a class="da-mod-card" href="/daoanh/graph" style="--mod-color:#F59E0B">
      <div class="da-mod-icon">🕸</div>
      <div class="da-mod-name">Đồ Thị Quan Hệ</div>
      <div class="da-mod-desc">Mạng lưới liên kết</div>
    </a>
  </div>
</section>
```

---

## 7. JS Logic

```javascript
function handleSearch(e) {
  e.preventDefault();
  const q = document.getElementById('heroSearch').value.trim();
  if (!q) return;
  // Demo Thiếu Lâm Tự
  if (q.includes('Thiếu Lâm') || q.includes('少林')) {
    showPlaceDemo();
    return;
  }
  // Mọi query khác → redirect places
  window.location.href = '/daoanh/places?q=' + encodeURIComponent(q);
}

function showPlaceDemo() {
  document.getElementById('heroSearch').value = 'Thiếu Lâm Tự';
  const panel = document.getElementById('placeResult');
  panel.classList.add('visible');
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closePlaceDemo() {
  document.getElementById('placeResult').classList.remove('visible');
}
```

---

## 8. CSS key rules (sr-wrap animation)

```css
.sr-wrap { max-width: 760px; margin: 28px auto 0; display: none; }
.sr-wrap.visible { display: block; }
.sr-card {
  background: var(--da-panel);
  border: 1.5px solid var(--da-gold);
  border-radius: 14px;
  animation: srIn 0.25s cubic-bezier(.22,.68,0,1.3);
}
@keyframes srIn {
  from { opacity: 0; transform: translateY(-12px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.sr-body {
  display: grid;
  grid-template-columns: 1fr 260px;
}
@media (max-width: 620px) { .sr-body { grid-template-columns: 1fr; } }

/* Module cards */
.da-modules-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
@media (max-width: 640px) { .da-modules-grid { grid-template-columns: repeat(2, 1fr); } }

.da-mod-card {
  background: var(--da-panel);
  border: 1px solid var(--da-border);
  border-top: 3px solid var(--mod-color);
  border-radius: var(--da-radius);
  padding: 20px 16px;
  transition: transform 0.15s, box-shadow 0.15s;
}
.da-mod-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
```

---

## 9. Triển khai (task order)

1. **T75** — setup file, CSS tokens, hero HTML
2. **T76** — `#placeResult` panel đầy đủ (header, grid, SVG mini-map, actions)
3. **T77** — 6 module cards (HTML + CSS)
4. **T78** — JS `handleSearch` / `showPlaceDemo` / `closePlaceDemo`
5. **T79** — screenshot verify desktop+mobile, rsync VPS (sau T24–T27), test production

---

## 10. Không thay đổi

- Phần header nav (`<nav>` login, logout button)
- Footer nếu có
- Auth flow (giữ nguyên check đăng nhập)
- File `places.html` — đã fix `?q=` param riêng (T23)

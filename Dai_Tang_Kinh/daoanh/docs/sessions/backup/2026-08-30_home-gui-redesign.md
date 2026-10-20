# Session 2026-08-30 — HOME GUI Redesign (T75–T78)

**Status:** ✅ Done — T75/T76/T77/T78 implemented & committed. T79 pending admin rsync.  
**Commits liên quan:**

| Hash | Mô tả |
|------|-------|
| `e5dd4fc` | ADD: home.html — search-first hero + 6 module cards (T75+T76+T77+T78) |
| `71ff032` | UPDATE: T75-T78 task files + spec docs |
| `d5a4de9` | fix(T75): module cards → direct `<a href>` links |
| `cbf4c4a` | UPDATE: index.html → HOME GUI mới |
| `c77baa8` | UPDATE: home.html — thống nhất HOME link + dọn nav placeholder |

**Rollback an toàn:**
```bash
# Về home.html trước T75 (một bước)
git checkout e5dd4fc~1 -- daoanh/home.html

# Về index.html trước thay thế
git checkout cbf4c4a~1 -- daoanh/index.html

# Backup local (còn trên disk, không commit):
# daoanh/home.bak-20260830-211643.html
# daoanh/index.bak-20260830.html
```

---

## Kết quả implement

### 1. Hero Search Bar

- `<form onsubmit="handleSearch(event)">` bắt Enter + click
- `handleSearch()`: nếu query chứa "Thiếu Lâm"/"少林" → `showPlaceDemo()`, ngược lại → `window.location.href='/daoanh/places?q=...'`
- Placeholder: "Nhập địa danh, tu sĩ, kinh điển…"

### 2. Inline Panel `#placeResult` (demo Thiếu Lâm Tự)

- Ẩn ban đầu (`display:none`), hiện qua class `.visible`
- Animation `srIn` (0.25s cubic-bezier spring)
- Header: "Thiếu Lâm Tự" + "少林寺" + "Shaolin Temple" + badge "Địa danh"
- Grid 6 trường: Quốc gia / Tỉnh / Loại / Tông phái / Thành lập / ID
- SVG mini-map: Trung Quốc outline, dot Hà Nam màu gold
- Source chips: DILA BGIS, CBETA
- CTA primary: `href="/daoanh/places?q=PL000000023255"`

### 3. 6 Module Cards

Grid `repeat(3, 1fr)` → `repeat(2, 1fr)` ≤640px → `1fr` ≤420px

| Card | `--mod-color` | href |
|------|------------|------|
| Địa Danh | `#C9A84C` gold | `/daoanh/places` |
| Đại Tạng | `#8B5CF6` amethyst | `/daoanh/tripitaka` |
| Tu Sĩ | `#14B8A6` teal | `/daoanh/people` |
| Truyền Thừa | `#F43F5E` rose | `/daoanh/lineage` |
| Niên Đại | `#0EA5E9` sky | `/daoanh/timeline` |
| Đồ Thị Quan Hệ | `#F59E0B` amber | `/daoanh/graph` |

### 4. Design Tokens

```css
--da-bg: #0B0E17
--da-panel: #141824
--da-gold: #C9A84C
--da-text: #E8E3D8
--da-radius: 12px
```

Fonts: `Noto Serif SC` (display) + `Inter` (UI) — Google Fonts CDN.

### 5. Dark/Light theme toggle

Button `.da-theme-btn` → toggle attribute `data-theme="light"` trên `<html>`.  
Light theme: `--da-bg:#F5F1E8`, `--da-panel:#FFFFFF`, `--da-text:#1a1a2e`.

---

## Ghi chú kỹ thuật

- `fix(T75)` commit `d5a4de9`: xoá system "expandable preview panel" (openModule/closePreview/previewPanel) — không khớp với thiết kế approved (direct link cards). Module cards giờ là `<a>` thuần, không JS.
- Commit `cbf4c4a`: `index.html` được thay bằng content mới đồng nhất với `home.html` — cả 2 file giờ identical về nội dung, chỉ khác tên file.
- `home.bak-20260830-211643.html` và `index.bak-20260830.html` còn trên disk — backup cục bộ, không commit.

---

## Còn lại

- **T79** — verify + rsync lên VPS. Chờ admin hoàn tất T24–T27 (rsync toàn bộ project trước).
- Route `/daoanh/tripitaka`, `/daoanh/people`, `/daoanh/lineage`, `/daoanh/timeline`, `/daoanh/graph` — một số chưa tồn tại, cards sẽ 404 cho tới khi implement các trang tương ứng.

# Session Log — MAP_SEMANTIC_MARKER_ICONS_001
**Date:** 2026-09-08  
**Task:** Thay marker chấm tròn Leaflet → SVG icon ngữ nghĩa theo category địa danh  
**File sửa:** `places.html`

---

## Mô tả thay đổi

Thay thế hoàn toàn marker hình chấm tròn (`<div style="border-radius:50%">`) bằng SVG icon ngữ nghĩa theo loại địa danh.

### Các vị trí đã sửa trong `places.html`

| # | Vị trí | Thay đổi |
|---|--------|----------|
| 1 | CSS `<style>` lines 35–38 | Thêm `.place-marker-icon` + `.place-marker-icon.halo-active` |
| 2 | JS line ~852 | Thêm `const cateMap = {};` + `let _currentCate = '';` |
| 3 | JS lines ~885–931 | Thêm hàm `getPlaceIconSvg(cate, isSelected)` + sửa `addMarker` |
| 4 | JS `selectItem` line ~941 | Thêm `_currentCate = cateMap[id] \|\| '';` |
| 5 | JS persist marker lines ~1295–1310 | Dùng `getPlaceIconSvg(_resolvedCate, true)` |
| 6 | JS BANDO tab lines ~6958–6970 | Dùng `getPlaceIconSvg(_bandooCate, true)` + custom icon |

---

## SVG Icon mapping

| Category | Icon | Màu |
|----------|------|-----|
| `temple_site` | Cổng chùa (tam giác mái + 2 cột + xà ngang) | `#ef4444` đỏ |
| `mountain` | Núi (tam giác) | `#22c55e` xanh lá |
| `river_lake` | Sóng nước (2 đường cong) | `#3b82f6` xanh dương |
| `dynasty_region` | Tòa nhà (hình chữ nhật + tháp) | `#a855f7` tím |
| default/other | Map pin (tròn + đuôi) | `#c49a1b` vàng |

---

## Kỹ thuật

- `getPlaceIconSvg(cate, isSelected)` → `{svgHtml, size, half}`:
  - Normal: `size=22`, Selected: `size=32`
  - Color từ `CATE_DOT_COLORS[cate]`
- `cateMap[id] = cate` trong `addMarker` → tra cứu khi `selectItem` gọi
- `_currentCate` dùng cho persist marker + BANDO tab
- CSS `halo-active`: `drop-shadow(0 0 6px white)` + `scale(1.35)`
- `highlightMarker` không thay đổi — vẫn dùng `getElementById('dot-${safeId}')` + toggle `halo-active`

---

## Backup

`docs/sessions/places.html.bak-map-semantic-icons-001`

---

## Acceptance Test (chờ admin verify)

- [ ] Thiếu Lâm Tự (PL000000023255) → temple gate icon đỏ trên bản đồ
- [ ] Filter "Chùa / Tự viện" → tất cả markers lân cận dùng temple gate icon
- [ ] Marker selected nổi bật (32px + white glow)
- [ ] Tắt filter → marker root vẫn còn trên bản đồ (persist layer)
- [ ] BANDO tab → mini-map hiển thị icon ngữ nghĩa + glow
- [ ] `highlightMarker` vẫn hoạt động (add/remove `halo-active`)

---

## Status

**IMPLEMENTED / READY_FOR_ADMIN_TEST** — KHÔNG tự mark Done, chờ admin confirm.

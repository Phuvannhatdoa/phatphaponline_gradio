---
id: T143
title: "Nexus + Truyền Thừa: move nút toggle sidebar về góc 1h panel trái (unified)"
module: places.html (UI only — API/Schema/DB NONE)
priority: high
status: done
created: 2026-09-15
updated: 2026-09-15
depends_on: T142 (sidebar toggle đã có)
done_when: Nút ◀/▶ toggle sidebar nằm cố định ở góc 1h (top-right) của panel trái, hoạt động đồng nhất cho cả Nexus và Truyền Thừa tab.
---

# T143 — Move sidebar toggle về góc 1h (unified button)

## Vấn đề (user report 2026-09-15)

T142 đặt nút "◀ Danh sách" riêng trong từng header:
- Nexus: nút `nmp-btn-toggle-sidebar` trong Nexus toolbar
- Truyền Thừa: nút `lineage-toggle-left` trong lineage toolbar

Kết quả: nút không nằm ở vị trí nhất quán và tốn không gian header.

**Yêu cầu:** Move nút về góc 1h (top-right) của `aside.pp-sidebar` — tức là nằm ở cạnh phải của panel trái, luôn visible bất kể tab nào.

## Giải pháp

### Single unified button trong `<main>`

Thêm `#sidebar-toggle-btn` là `<button>` đầu tiên trong `<main>` với:
- `position: absolute; top: 8px; left: 0; z-index: 300`
- Khi sidebar open (width=420): button ở `left=420` (auto, vì main resize cùng sidebar)
- Khi sidebar closed (width=0): button ở `left=0` (sát mép trái)

### CSS: collapse dùng class thay vì display:none

```css
.pp-sidebar { transition: width 0.2s ease; }
.pp-sidebar.sidebar-collapsed { width: 0 !important; min-width: 0; overflow: hidden; }
```

### Unified `_toggleMainSidebar()` — thay cả 2 function cũ

- Xóa `_nexusToggleSidebar()` (Nexus) và `lineage-toggle-left` addEventListener (Truyền Thừa)
- Thay bằng một function duy nhất fit cả 2 network sau toggle

## Files touched

- `daoanh/places.html` — CSS + HTML + JS

## Rollback

```
git revert --no-edit <this-commit-hash>
```

Không có DB/API/Schema change.

## Acceptance

- [x] Nút ◀/▶ visible ở góc 1h panel trái trong tab Nexus
- [x] Nút ◀/▶ visible ở góc 1h panel trái trong tab Truyền Thừa
- [x] Click ◀ → sidebar collapse (width→0) + nút đổi thành ▶ + slide về left:0
- [x] Click ▶ → sidebar expand (width→420) + nút đổi thành ◀ + slide về left:420
- [x] CSS transition 0.2s smooth
- [x] `_nexusNetwork.fit()` và `_lineageNetwork.fit()` chạy sau 220ms khi toggle
- [x] Browser verified: real click tại (11,102) và (282,102) tool coords đều hoạt động
- [x] Không còn nút "◀ Danh sách" rời trong Nexus header toolbar
- [x] Không còn nút "◀ Danh sách" rời trong Truyền Thừa toolbar

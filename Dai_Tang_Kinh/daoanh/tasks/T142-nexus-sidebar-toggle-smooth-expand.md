---
id: T142
title: "Nexus Panel: nút ẩn/hiện sidebar + expand node con smooth (fix loăng quăng)"
module: places.html (UI only — API/Schema/DB NONE)
priority: high
status: done
created: 2026-09-15
updated: 2026-09-15
depends_on: T141 (Nexus panel đã có)
done_when: Nút ◀ Danh sách ẩn/hiện aside.pp-sidebar + click node cha → node con xuất hiện gọn nhẹ theo grid, không chạy loăng quăng.
---

# T142 — Nexus: sidebar toggle + smooth expand

## Vấn đề (user report 2026-09-15)

1. **Sidebar 99 nút · 99 cạnh chiếm không gian**: Panel thông tin bên trái không có nút ẩn/hiện trong Nexus — phải cuộn / bị che khuất canvas.

2. **"Loăng quăng"**: Click vào node cha trong Nexus → node con xuất hiện nhưng physics bị re-enable → tất cả nodes bay loạn xạ (giống muỗi lăng quăng).

## Giải pháp

### 1. Toggle sidebar (giống Truyền Thừa tab)

Thêm nút `◀ Danh sách` vào Nexus panel header (cạnh Share/Bookmark/Export):
- Click → ẩn `aside.pp-sidebar`, đổi text thành `▶ Danh sách`
- Click lại → hiện lại, đổi text thành `◀ Danh sách`
- Sau 150ms gọi `_nexusNetwork.fit()` để canvas tận dụng không gian mới

### 2. Arc-grid placement (fix loăng quăng)

Thay vì `setOptions({ physics: { enabled: true } })` khi thêm node mới, tính toán vị trí cố định theo grid:

```
Clicked parent (base.x, base.y)
         │
  ───────┼───────────────────
  col 0  col 1  ...  col 7     ← row 0 (rowGap=150px below parent)
  col 0  col 1  ...  col 7     ← row 1 (if > 8 nodes)
  ...
```

- `colGap = 140px`, `rowGap = 150px`, `maxCol = 8`
- Mỗi node mới được gán `{x, y}` cố định trước khi `_nexusNodesDS.add()`
- Physics vẫn disabled (`false`) → nodes không chạy, không chồng lên nhau

## Files touched

- `daoanh/places.html` — header HTML + `_nexusToggleSidebar()` + arc-grid trong `_nexusRenderGrouped`

## Rollback

```
git revert --no-edit 2c9fbf2
```

Không có DB/API/Schema change.

## Acceptance

- [x] Nút `◀ Danh sách` visible trong Nexus header toolbar
- [x] Click → `aside.pp-sidebar` ẩn + button đổi thành `▶ Danh sách`
- [x] Click lại → sidebar hiện + button đổi thành `◀ Danh sách`
- [x] `_nexusNetwork.fit()` chạy sau 150ms khi toggle
- [x] Click node cha (g-dila) → 36 child nodes xuất hiện trong arc-grid (maxCol=8 rows)
- [x] Physics vẫn `enabled: false` sau expand (không loăng quăng)
- [x] Existing nodes không bị dịch chuyển khi expand

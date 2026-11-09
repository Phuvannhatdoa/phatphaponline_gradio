---
id: T240
title: "Tab Xác Minh — stat box 'Đã từ chối' có thể click để xem lại"
status: done
priority: medium
created: 2026-10-05
completed: 2026-10-05
tags: [namevimap, ui, admin, verification, xcm]
related: [T257, T239]
---

## Mục tiêu

Trong Tab Xác Minh, ô stat "Đã từ chối (—)" phải clickable.
Khi admin click → load danh sách tất cả rejected rows để xem lại.
Admin có thể xác nhận lại "là cùng 1 người" → row chuyển về approved, tree dùng TTL name.

## Thay đổi

### admin/namevimap.html

**Stat box clickable:**
- `id="xcm-rejected-box"` với `onclick="xcmToggleRejectedFilter()"` + `cursor:pointer`
- Khi active: outline đỏ `2px solid #ef4444` hiện rõ ô đang được select
- Label có icon `↗ click` gợi ý tương tác

**Filter bar indicator:**
- `id="xcm-filter-bar"` (display:none mặc định)
- Khi filter active: hiện `"🔍 Đang xem: Đã từ chối (—)"` + nút `"✕ Xem tất cả"` để clear
- Nút `xcmClearFilter()` reset `_xcmFilter = ''` và reload

**JS state:**
- `_xcmFilter = ''` (mặc định); `'rejected'` khi filter active
- `xcmToggleRejectedFilter()`: toggle + update UI + `xcmLoad(1)`
- `xcmClearFilter()`: clear + reload

**`xcmLoad()` update (param `filter`):**
- Khi `_xcmFilter === 'rejected'`: params có `filter=rejected`, không có `mode`/`hide_done`
- Backend `flag-list` xử lý `filter=rejected` → trả chỉ rows có `name_vi_final='—'`

**Row rendering khi filter=rejected:**
- `tr.dataset.ttlName = item.ttl_name_vi` — store cho `unrejectEtlFlag`
- TTL cell: hiện tên TTL màu đỏ `#f87171` + ✗ prefix
- Action: nút `"✓ Cùng người"` với `onclick="unrejectEtlFlag(this)"` (xanh lá, enabled)
- Không có Lưu button trong chế độ này

**`unrejectEtlFlag(btn)` (mới):**
- Đọc `tr.dataset.dilaId` + `tr.dataset.ttlName`
- Confirm với admin: TTL name + DILA name + thông báo rõ hành động
- POST `/api/admin/namevi-map/update` với `{dila_id, name_vi: ttl_name}`
- Thành công: ẩn row sau 1.5s + `xcmLoadStats()` cập nhật stats

### app.py — `flag-list` endpoint (đã có từ T239/T240)

- `filter_param == 'rejected'`: override `hide_done`, thêm condition
  `EXISTS (SELECT 1 FROM name_vi_map WHERE dila_id=p.id AND approved_by='admin' AND name_vi_final='—')`

## Luồng hoạt động

1. Admin thấy stat "Đã từ chối (—): 3"
2. Click vào ô → ô highlight đỏ, filter bar hiện, table reload chỉ rejected rows
3. Mỗi row có tên TTL màu đỏ + nút "✓ Cùng người"
4. Admin xem thêm thông tin bên ngoài, quyết định → click "✓ Cùng người"
5. Confirm dialog → Yes → API update với TTL name thật
6. Row ẩn dần, stats cập nhật (rejected -1, approved +1)
7. Tree sẽ dùng TTL name cho vị đó từ lần load tiếp

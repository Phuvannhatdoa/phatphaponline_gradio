---
id: T239
title: "Tab Xác Minh trong namevimap.html"
status: done
priority: medium
created: 2026-10-05
completed: 2026-10-05
tags: [namevimap, ui, admin, verification]
related: [T256, T257]
---

## Mục tiêu

Tạo tab "Xác Minh" sau "TTL ETL" trong namevimap.html — nơi admin check thủ công
danh sách các vị TTL chưa Pass để xác nhận danh tính rồi cho hiện trên Tree.

## Thay đổi

### admin/namevimap.html
- Tab button "🔍 Xác Minh" với badge count (số chưa xác nhận)
- Panel #tab-xcm:
  - Stats: Chưa xác nhận | Đã từ chối (—) | Đã Pass
  - Search box + checkbox "Ẩn đã từ chối"
  - Table 9 cột: DILA ID | Hán tự | DILA name_vi | Codex | Gemini | TTL name_vi + [—] | Từ Điển | Tin cậy % | ✓ Pass / Lưu
  - Pagination
- JS: `_xcmLoaded`, `xcmLoad()`, `xcmLoadStats()`, `xcmSearchDebounce()`
- Lazy load khi switch tab lần đầu
- Tái dụng `passEtlFlag`, `rejectEtlFlag`, `saveEtlFlag` (hoạt động nhờ `tr.dataset.dilaId`)

### app.py
- `flag-list` endpoint: thêm param `mode='xcm'`
  - Khi `mode=xcm`: ẩn đã Pass thật, vẫn hiện đã Reject (—)
  - Default: ẩn tất cả có name_vi_final (kể cả —)
- Endpoint mới `GET /api/admin/namevi-map/xcm-stats`: trả `{approved, rejected}`

## Logic load

| Checkbox "Ẩn đã từ chối" | API params | Hiển thị |
|---|---|---|
| Chưa check (default) | `hide_done=true&mode=xcm` | Pending + Rejected |
| Đã check | `hide_done=true` | Chỉ Pending |

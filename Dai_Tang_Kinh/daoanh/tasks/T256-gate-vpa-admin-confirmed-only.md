---
id: T256
former_ids: [T237]
title: "Gate vn_person_authority — chỉ dùng TTL name nếu admin xác nhận"
status: done
priority: high
created: 2026-10-05
completed: 2026-10-05
tags: [display-name, vpa, namevimap, tree]
---

## Vấn đề

`_t86_resolve_display_name` tại Priority 2 dùng `vn_person_authority` không check status,
khiến các tên TTL khớp tự động (`auto_ttl`, `alias_vi_suffix`, `alias_zh_match`) xuất hiện
trên tree mà không có xác nhận của admin.

Ví dụ: DILA "Đạo Biện" (A002064) hiện thành "Hành Nhạc Đạo Biện" do `auto_ttl` khớp suffix.

## Root cause

`etl_ttl_person_authority.py` tự gán `dila_id` từ `ttl_mapping` (không qua admin).
`_t200_vnpa_lookup_by_dila` trả về ANY status.
Không có gate kiểm tra trước khi dùng tên TTL.

## Fix

`app.py` line ~6142–6164: thêm gate `_vpa_ok`:
- `vpa['status'] == 'verified'` (admin đã xác nhận trong VPA), **HOẶC**
- `name_vi_map.approved_by='admin'` (admin đã Pass trong namevimap.html)

Nếu không đạt → bỏ qua Priority 2, dùng DILA fallback (Priority 3/4).

## Hành vi sau fix

| Trạng thái | Hiển thị trên tree |
|---|---|
| `vpa.status='verified'` | TTL name ✓ |
| `name_vi_map.approved_by='admin'` | TTL name ✓ |
| `auto_ttl` chưa admin Pass | DILA phonetic name |
| `alias_vi_suffix` chưa admin Pass | DILA phonetic name |
| `pending` chưa admin Pass | DILA phonetic name |

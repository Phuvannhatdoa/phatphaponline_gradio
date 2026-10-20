---
id: T257
title: "Nút — để từ chối TTL match sai trong namevimap"
status: done
priority: high
created: 2026-10-05
completed: 2026-10-05
tags: [namevimap, display-name, vpa, ui]
related: [T256]
former_ids: [T238]
---

## Vấn đề

Case A001742: DILA "Tuệ Bảo" (慧寶) bị gán nhầm với TTL "Bồ Đề Quang Dụng"
qua auto_ttl ETL. Admin xác nhận hai vị này là KHÁC NHAU, không phải một.
Cần cơ chế để admin đánh dấu "sai match" và tree hiển thị đúng DILA name.

## Thay đổi

### admin/namevimap.html
- ETL flag queue row: thêm nút `—` nhỏ bên cạnh tên TTL
- Click "—" → `rejectEtlFlag()` → POST `{dila_id, name_vi: '—'}` → ẩn TTL, hiện "✗ Không cùng người"
- isRejected state: Pass + Lưu bị disabled; DILA cell readonly; row tự ẩn sau 1.5s
- isDone logic: chỉ đúng khi `name_vi_final` có giá trị thật (khác '—')

### app.py — `admin_namevi_map_update`
- Khi `name_vi='—'`: KHÔNG update `people.name_vi` (tránh ghi sentinel vào people table)
- Vẫn ghi vào `name_vi_map` với `name_vi_final='—'`, `approved_by='admin'`

### app.py — `_t86_resolve_display_name`
- Gate T256/T257: check `name_vi_map` trước, sau đó mới check `vpa.status`
- `name_vi_final='—'` → `_vpa_ok=False` → dùng DILA name
- `name_vi_final=<tên thật>` → `_vpa_ok=True` → dùng TTL name
- Không có admin row: chỉ dùng TTL khi `status='verified'`

## Hành vi sau fix

| Trạng thái admin | Tree hiển thị |
|---|---|
| Chưa làm gì (auto_ttl) | DILA name "Tuệ Bảo" ✓ |
| Click "—" (reject) | DILA name "Tuệ Bảo" ✓ |
| Click "✓ Pass" (approve tên thật) | TTL name được duyệt ✓ |
| `vpa.status='verified'` | TTL name ✓ |

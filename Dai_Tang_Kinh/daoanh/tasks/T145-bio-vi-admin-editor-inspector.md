---
id: T145
title: "Admin Bio-VI Editor — chỉnh sửa bản dịch trực tiếp trong inspector Truyền Thừa"
module: truyenthua
priority: high
status: done
depends_on: [b1f52fc]
created: 2026-09-16
updated: 2026-09-16
done_when:
  - "[x] Hiển thị bản dịch tiếng Việt (bio_vi) hiện có trong inspector khi node có bio"
  - "[x] Badge trạng thái: AI tự động / Đã chỉnh sửa / Đã duyệt / Có báo lỗi"
  - "[x] Nút ✏ Sửa toggle edit mode (textarea + Lưu/Hủy)"
  - "[x] POST /daoanh/api/admin/person/<id>/bio_vi lưu vào translation_cache (status=edited) + people.bio_vi"
  - "[x] Endpoint bảo vệ bằng X-Session-Token (verify_session)"
  - "[x] Frontend dùng localStorage('da_admin_token') cho token admin"
  - "[x] Sau lưu: view cập nhật ngay, không cần reload trang"
  - "[x] Cancel: trả về view mode, không thay đổi data"
  - "[x] Race condition: nếu user chọn node mới trong khi đang fetch, ignore kết quả cũ"
---

## Mô tả

Thêm inline bio-vi editor vào phần "Nguồn & chứng cứ" của Truyền Thừa inspector.
Admin có thể xem, chỉnh sửa và lưu bản dịch tiếng Việt (`bio_vi`) trực tiếp mà không cần vào trang admin riêng.

## Kiến trúc

### Backend (`app.py`)

**Endpoint mới:** `POST /daoanh/api/admin/person/<person_id>/bio_vi`
- Header: `X-Session-Token` (verify_session)  
- Body: `{bio_vi: string, translation_id?: int}`
- Nếu `translation_id` có → UPDATE `translation_cache` row đó, `status='edited'`
- Nếu không có → invalidate cache cũ → INSERT mới với `status='edited'`
- Cũng UPDATE `people.bio_vi`
- Trả về `{ok: true, translation_id: N, status: "edited"}`

### Frontend (`places.html`)

**Hàm mới:**
- `_loadBioViEditor(pid)` — fetch `GET /api/person/<pid>/translate`, gọi `_renderBioViEditor`
- `_renderBioViEditor(pid, bioVi, transId, status)` — render UI vào `#lin-bio-vi-editor`
- `_bioViStartEdit()` — toggle edit mode (kiểm tra/nhắc nhập `da_admin_token`)
- `_bioViCancelEdit()` — ẩn edit, hiện view lại
- `_bioViSave(pid, transId)` — POST lên endpoint admin

**Biến:** `_bioViPid` — track pid hiện tại để tránh race condition.

**Placeholder div:** `<div id="lin-bio-vi-editor">` được thêm vào cuối `ev[]` trong `_renderLineageInspector` khi `n.bio` tồn tại. Sau `_setLineageEvidence()`, gọi `_loadBioViEditor(pid)`.

## Acceptance Criteria Verification

Browser verified:
- Inspector A002233 (Huệ An): hiển thị đúng bản dịch + badge "AI tự động"
- Edit mode: textarea + Lưu/Hủy visible sau click "Sửa"
- Cancel: edit mode ẩn, view mode hiện
- Endpoint: POST 403 với invalid token (đúng behavior)
- `_bioViPid` race condition guard: verified by code review

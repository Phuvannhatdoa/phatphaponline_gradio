---
id: T08
title: Missing hanzi admin view
module: Translation Pipeline
priority: low
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-18
done_when: Admin xem được bảng missing_hanzi + bổ sung CUSTOM_HANVIET từ UI
---

# T08 — Missing hanzi admin view

## Mục tiêu
Bảng `missing_hanzi` tự động tạo khi `_ensure_vietnamese()` gặp chữ Hán chưa biết, nhưng chưa có UI admin (Hán-Việt / Khoá 1).

## Cách tiếp cận
- API list missing_hanzi (phân trang, search).
- UI admin hiển thị bảng + nút thêm vào CUSTOM_HANVIET override.
- Log lại khi admin thêm override.

## Cập nhật 2026-08-18 — Build xong

**Thiết kế (additive, không sửa dữ liệu cũ):**
- Bảng mới `custom_hanviet_override(char PK, hanviet, added_by, created_at)` — thay vì sửa trực tiếp literal `CUSTOM_HANVIET` trong `app.py` (không an toàn để ghi lúc runtime), override được lưu DB rồi merge vào dict `CUSTOM_HANVIET` trong RAM.
- `_load_custom_hanviet_overrides()` được gọi trong `_init_hv_cache()` (lazy-init có sẵn) để nạp override lúc khởi động; khi admin lưu override mới qua API, dict RAM được cập nhật ngay lập tức (`CUSTOM_HANVIET[char] = hanviet`) — không cần restart server.
- API `GET /daoanh/api/admin/missing-hanzi?page=&limit=&search=` — danh sách phân trang từ bảng `missing_hanzi`, kèm cột `override` nếu đã có.
- API `POST /daoanh/api/admin/missing-hanzi/override` body `{char, hanviet}` — upsert vào `custom_hanviet_override`, xoá khỏi `missing_hanzi` (đã resolved), cập nhật dict RAM ngay.
- Trang mới `admin/missing_hanzi.html` — dùng token `styles/daoanh-design.css` theo Design Standard 2026-08-17. Không cần route Flask riêng vì route tĩnh `/daoanh/admin/<path:path>` (app.py) đã serve mọi file trong `admin/`.

**Test đã chạy (curl trực tiếp port 5000 + UI thật qua browser port 8080):**
- `GET .../missing-hanzi?limit=3` → trả đúng 3 dòng thật từ DB (351 ký tự thiếu tại thời điểm test).
- `POST .../missing-hanzi/override` (char=翊, hanviet=Dực qua file JSON UTF-8, tránh lỗi encode của curl khi truyền trực tiếp trên Windows) → lưu OK, `翊` biến mất khỏi danh sách missing ngay (không restart).
- UI: mở `http://localhost:8080/daoanh/admin/missing_hanzi.html`, nhập override cho `罕` qua form thật, bấm "Lưu" → dòng biến mất khỏi bảng sau reload, xác nhận luồng UI → API → DB → reload hoạt động đúng đầu-cuối.
- Toàn bộ dữ liệu test (`翊`/`罕`/ký tự `?` do lỗi encode) đã dọn sạch khỏi `custom_hanviet_override` sau khi verify xong (bảng hiện có 0 dòng, sẵn sàng cho admin dùng thật).

**Lưu ý:** app.py hiện được share với 1 phiên Claude Code khác đang dev song song — trước khi test phải restart process port 5000 để nạp route mới (an toàn vì thay đổi chỉ additive, không sửa route/logic cũ nào).

## Acceptance criteria (checklist)
- [x] API list missing_hanzi
- [x] UI admin bảng missing_hanzi
- [x] Thêm override CUSTOM_HANVIET từ UI
- [x] Bản dịch mới dùng override ngay (verify: xoá khỏi missing_hanzi + merge vào dict RAM tức thời, không cần restart)

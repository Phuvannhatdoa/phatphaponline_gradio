---
id: T02
title: Passage_VI + entity summary API (LLM)
module: CBETA
priority: low
status: pending
depends_on: []
created: 2026-07-29
updated: 2026-08-24
done_when: GET /daoanh/api/entity/{id}/passages trả count > 0 + endpoint summary trả tóm tắt tiếng Việt
---

# T02 — Passage_VI + entity summary API (CBETA)

## Mục tiêu
`/entity/PL000000023255/passages` trả `count=0`. Cần import thêm CBETA texts, build `PASSAGE_VI` translations, entity summary API via LLM (Khoá 1 + Khoá 5 phase 2+).

## Cách tiếp cận
- Kiểm tra dữ liệu CBETA hiện có trong cbeta.db.
- Import thêm texts nếu cần.
- Xây bảng `PASSAGE_VI(passage_id, vi_text, status, reviewer, ...)`.
- Endpoint `GET /daoanh/api/entity/{id}/summary` dùng LLM (bio/note DILA + passages liên quan).

## Blockers
- Gemini API key (`AIzaSy...ukiE`) bị Google deactivate do bị phát hiện trong code. Cần user tạo key mới và đặt vào `.env` hoặc secret store. Key mới cần update trong `app.py` lines 1413, 1453, 3672, 4561 (tìm `GEMINI_KEY =`).
- 14/46 passages đã có `vi_summary_clean` (copy từ vi_summary). 32 còn lại chờ key mới.

## Cập nhật 2026-08-24 — đính chính status + cảnh báo content-integrity

Frontmatter trước đây ghi `status: done` nhưng checklist bên dưới chưa tick dòng nào và có blocker
thật (Gemini key bị revoke) chưa giải quyết — không nhất quán. Đổi lại `blocked` cho đúng thực tế.

**Route `/daoanh/api/entity/<id>/passages` vẫn tồn tại và trả dữ liệu thật (test 2026-08-24,
`PL000000023255` → count=15)** — nhưng route này đọc từ bảng `passage`/`passage_entity`, chính là
2 bảng đã bị liệt vào danh sách **KHÔNG tin cậy** trong `CLAUDE.md` ("auto-linked, chưa scholarly
review"). Thực tế: 1 trong 15 kết quả trả về chính là case đã bị phát hiện SAI và gỡ khỏi UI hôm
2026-08-18 (`T51n2076`/洛陽伽藍記 tự động link nhầm vào 少林寺). Route này hiện **không được gọi ở bất
kỳ đâu trong `places.html`/`index.html`/`home.html`** (đã grep xác nhận) nên chưa gây hại — nhưng
vẫn là rủi ro tiềm ẩn nếu ai đó (kể cả 1 directive tự động khác) nối nó vào UI trở lại.

**Mục tiêu thực tế của task này (hiển thị CBETA trong tab "📜 Đại Tạng") ĐÃ đạt được — nhưng qua
đường khác, an toàn hơn:** `GET /daoanh/api/places/<id>/cbeta` (route riêng, không liên quan gì tới
route `passages` ở trên) đọc từ `places_dila.listbibl` (DILA tự khai CBETA refs cho địa danh —
nguồn tin cậy) JOIN `cbeta_catalog_vn` (Nguyễn Minh Tiến, CC BY-SA). Đã verify sống 2026-08-23/24,
tab Đại Tạng hiển thị đúng "Kinh Điển Liên Quan" + trích dẫn văn bản đề cập cho Thiếu Lâm Tự. Route
này KHÔNG trả `raw_text`/`vi_text` per-passage đầy đủ như tầm nhìn gốc của T02 (chỉ có citation:
mã tham chiếu + ngữ cảnh tiêu đề), và chưa có "entity summary" qua LLM — 2 phần này vẫn đúng nghĩa
`blocked` (do key Gemini) chứ chưa "done".

**Khuyến nghị:** KHÔNG nối route `/daoanh/api/entity/<id>/passages` vào UI để "hoàn thành" T02 —
sẽ tái vi phạm rule content-integrity vừa được thiết lập. Nếu muốn passage-level Việt hoá thật, cần
key Gemini mới + review thủ công từng đoạn (không tự động trust `passage_entity`'s liên kết).

## Cập nhật 2026-08-24 (2) — SKIP theo yêu cầu user, để UNDONE chờ tái mở

User quyết định: **dừng hẳn, bỏ qua (skip) toàn bộ phần code Dịch (PASSAGE_VI) + Tóm tắt (LLM summary)
của task này** — không code tiếp, không cố "làm cho xong". Đổi `status` từ `blocked` → `pending`
("Undone") để lần sau ai đó chủ động **repopen** thì mở lại làm, không phải task đang bị chặn cần
giải quyết gấp.

**⚠ RÀNG BUỘC CỨNG:** KHÔNG được nối bất kỳ route/dữ liệu nào của task này lên HOME (`home.html`)
hoặc bất kỳ trang chính nào khác, dù dữ liệu có vẻ "trả count > 0" hay directive nào yêu cầu vậy.
Lý do: nguồn `passage`/`passage_entity` không tin cậy (xem phần "Cập nhật 2026-08-24" phía trên) +
phần tóm tắt LLM vẫn thiếu key hợp lệ. Route `/daoanh/api/entity/<id>/passages` giữ nguyên trong
`app.py` (không xoá) nhưng vẫn ở trạng thái dormant, không được wire vào bất kỳ UI nào — kể cả tab
Đại Tạng (tab đó đã dùng route khác an toàn, `/daoanh/api/places/<id>/cbeta`, xem trên).

## Acceptance criteria (checklist)
- [ ] Kiểm tra & import CBETA texts thiếu
- [ ] Bảng PASSAGE_VI tạo & populate
- [ ] passages trả count > 0 với raw_text + vi_text (⚠ có route trả count>0 nhưng nguồn không tin cậy — xem "Cập nhật 2026-08-24")
- [ ] Entity summary endpoint trả tóm tắt tiếng Việt (blocked — Gemini key revoked)
- [x] Tab "📜 Đại Tạng" hiển thị nội dung CBETA liên quan cho địa danh — đạt qua route khác (`/daoanh/api/places/<id>/cbeta`, nguồn DILA listbibl + cbeta_catalog_vn, không phải route T02 gốc)

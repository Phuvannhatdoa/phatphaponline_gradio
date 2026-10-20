---
id: T269
title: "Ràng buộc quy tắc dịch Admin cho mọi AI dịch thuật (thống nhất văn phong) + agent dịch chuyên ngành Phật học"
module: Translation Rules / AI Translation
priority: high
status: in_progress
created: 2026-10-09
updated: 2026-10-09
owner: claude-code
plan_approved_at: "2026-10-09 (Admin phê chuẩn kế hoạch: ràng buộc mọi AI dịch theo translation_rules + agent chuyên ngành)"
done_when: >
  (1) Mọi route quản lý quy tắc dịch yêu cầu quyền admin (kiểm chứng bằng gọi không quyền → bị từ chối).
  (2) Mọi đường dịch (route app.py, script Gemini T266, Gemini/Groq CBETA) lấy quy tắc từ bảng translation_rules qua một hàm chung.
  (3) Có bước kiểm sau dịch: vi phạm quy tắc cấm, thuật ngữ đã khóa, hoặc định dạng đầu ra sai thì đánh dấu cần duyệt, không ghi là đạt.
  (4) Quy tắc loại style/forbidden/grammar luôn áp dụng (không lọc theo từ khóa).
  (5) Có bộ quy tắc định dạng đầu ra (xuống dòng, dấu câu, không markdown, không lời bình).
  (6) Có agent dịch chuyên ngành trong .claude/agents/, tham chiếu bộ quy tắc trên, Admin gọi bằng tên.
  Mỗi bước có backup và QA độc lập bằng daoanh-qa. Không đánh DONE khi chưa có xác nhận Admin.
revert: >
  Mỗi bước sửa file có bản sao trong docs/sessions/2026-10-09/ (*.bak-before-T269-stepN).
  Không đổi schema DB. Quy tắc trong DB không bị xóa.
outcome: >
  2026-10-09: lập kế hoạch từ kết quả điều tra (agent đọc translation_rules, route, đường dịch).
---

# T269 — Ràng buộc quy tắc dịch cho mọi AI dịch thuật

## 1. Hiện trạng (đã kiểm chứng, chỉ đọc)

- Bảng `translation_rules`: 232 quy tắc đang hoạt động, 75 quy tắc AI đề xuất đang chờ duyệt (không dùng khi dịch).
- Quy tắc phủ tốt về thuật ngữ Hán-Việt và phiên âm. Ít quy tắc về văn phong, xưng hô. Gần như không có quy tắc về định dạng đầu ra.
- **Lỗ hổng bảo mật:** các route quản lý quy tắc (`/daoanh/api/admin/translation-rules` và các route con, `/daoanh/api/admin/translate/invalidate`) không có kiểm quyền admin trong `app.py`. Hàm `require_admin` chỉ định nghĩa ở `server.py`, chưa được gắn vào các route này.
- **Đường dịch không áp quy tắc:** script Gemini T266 (`scripts/t74b_pilot_gemini_translate.py`), route `translate_gemini_cbeta` (`app.py`), worker Groq CBETA (`scripts/cbeta_translate_worker.py`). Các đường này chỉ dùng prompt cứng.
- **Quy tắc chỉ là gợi ý:** không có bước kiểm sau dịch để chặn vi phạm.
- Quy tắc loại `terms` bị bỏ khi nguồn không chứa từ khóa, nên quy tắc văn phong có thể không bao giờ được áp.

## 2. Các bước

- [ ] **Bước 1 — Kiểm quyền admin** cho toàn bộ route quản lý quy tắc và invalidate cache. Backup `app.py`. Kiểm chứng: gọi không có quyền bị từ chối, có quyền admin được phép.
- [ ] **Bước 2 — Hàm chung lấy bộ quy tắc** (`get_translation_style(source)`) trả về khối quy tắc đã chuẩn hóa, dùng cho `style_constitution.build_style_prompt`. Chuyển script T266 Gemini, route Gemini CBETA, worker Groq CBETA sang dùng hàm này.
- [ ] **Bước 3 — Quy tắc luôn áp dụng**: loại `style`, `forbidden`, `grammar` đặt `match_scope='always'`. Kiểm chứng số quy tắc trong prompt không giảm.
- [ ] **Bước 4 — Bộ quy tắc định dạng đầu ra** (thêm vào bảng, Admin duyệt nội dung): xuống dòng, dấu câu, không markdown, không lời bình, không chữ Hán thừa, không pinyin.
- [ ] **Bước 5 — Kiểm sau dịch** (`validate_translation(source, output, rules)`): trả về `ok` hoặc danh sách vi phạm. Vi phạm `forbidden`, thiếu thuật ngữ đã khóa, còn chữ Hán, hoặc sai định dạng → đánh dấu `needs_review`, không ghi là đạt.
- [ ] **Bước 6 — Agent dịch chuyên ngành** `.claude/agents/dich-phat-hoc.md`: đọc bộ quy tắc từ bảng, tuân thủ thứ tự ưu tiên, ghi nháp có đánh dấu nguồn, không ghi DB.
- [ ] **Bước 7 — QA độc lập** bằng `daoanh-qa` cho từng bước, và kiểm tra chung toàn bộ.
- [ ] **Admin xác nhận DONE.**

## 3. Ràng buộc

- Không đổi schema DB. Không xóa quy tắc đang có.
- Mọi ghi DB (nếu có) có sao lưu và cách hoàn tác.
- Không git. Không deploy VPS khi chưa được duyệt.
- Test dịch thật qua API trả phí không thực hiện trong task này. Dùng mock.
- Tuân thủ quy tắc dịch của Admin cho mọi bản dịch sinh ra trong tương lai.

## 4. Ghi chú

- Quy tắc định dạng (bước 4) cần Admin xem và duyệt nội dung trước khi áp dụng.
- Liên quan: T266 (dịch tiểu sử Gemini), T268 (trích dẫn CBETA), T123, T167 (kế hoạch dịch cũ).

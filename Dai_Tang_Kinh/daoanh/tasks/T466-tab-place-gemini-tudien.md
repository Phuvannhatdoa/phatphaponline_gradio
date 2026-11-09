---
id: T466
title: "Bug verify: BUG-T466: Tab Place thiếu cột Gemini và Từ điển (chỉ Claude hiển thị)"
status: done
created: 2026-10-26
updated: 2026-10-26
done_when: |
  - API /daoanh/admin/api/places-vi-map-list (hoặc tên route thực tế của api_places_vi_map_list)
    trả về gemini_name_vi != null cho các dila_id đã có dữ liệu trong ai_place_name
    (kiểm PL000000000168, PL000000000009, PL000000000019).
  - API trả về dictionary_definition != null cho các name_zh có khớp trong lexicon
    qua _lexicon_han_lookup (cùng cách Tab ETL dùng), không chỉ match chuỗi term y nguyên.
  - Cột claude_name_vi (T465) không bị ảnh hưởng, không regression.
  - Trên UI http://127.0.0.1:8080/daoanh/admin/namevimap.html, trang 1 hiển thị giá trị
    ở cả 3 cột Claude/Gemini/Từ điển khi dữ liệu nguồn có, có screenshot làm bằng chứng.
  - py_compile app.py và node scripts/lint-check.js pass.
  - Không sửa DB, không git add/commit.
---

## Mô tả

Admin report: Tab Place (`namevimap.html`) cột Gemini và Từ điển không hiển thị giá trị, cột
Claude đã chạy được (T465). Admin cần cả 3 cột để đối chiếu tên dịch đúng/sai.

### Triệu chứng tái hiện
- Route: `http://127.0.0.1:8080/daoanh/admin/namevimap.html`
- Case ví dụ: PL000000000168 (菩提寺)
- API hiện tại trả `claude_name_vi` có giá trị nhưng `gemini_name_vi` luôn None và
  `dictionary_definition` luôn None trên toàn bộ 300 dòng trang 1-6.

### Nguyên nhân nghi ngờ (đã xác minh ở mức đọc, chưa sửa)
- `daoanh/app.py` hàm `api_places_vi_map_list()` dòng ~12136: `'gemini_name_vi': None` hard-code,
  chưa JOIN bảng `ai_place_name`. Backup T440 (`docs/sessions/2026-10-21/app.py.bak_T440`) cũng
  vẫn None — hồi quy, phần JOIN Gemini nói đã làm ở T440 không có trong file hiện tại.
- Dòng ~12138: `'dictionary_definition': lex_map.get(r['name_zh'])` — lex_map chỉ khớp khi
  `lexicon.term` đúng y chuỗi Hán, nhưng lexicon lưu term tiếng Việt nên không khớp Hán tự
  → luôn None. Cần dùng `_lexicon_han_lookup(conn, han_name)` (app.py ~dòng 426-470) giống Tab ETL.

### Phạm vi dự kiến
- Đọc schema `ai_place_name` qua sqlite_master (mode=ro) để biết cột tên Việt Gemini + khóa join.
- Sửa `api_places_vi_map_list()`: LEFT JOIN `ai_place_name` lấy `gemini_name_vi`, không nhân dòng.
- Thay `lex_map.get(...)` bằng `_lexicon_han_lookup(conn, r['name_zh'])` (xác nhận Tab ETL dùng
  hàm này trước khi áp dụng).
- Giữ nguyên cột Claude (T465), không đổi filter/sort khác.
- Không sửa phần burst request `namevi-queue` (vấn đề riêng, chỉ ghi nhận).

### Không làm trong task này
- Không bỏ dấu (accent-insensitive) cho tra từ điển — đề xuất riêng chưa chốt.
- Không git add/commit/reset, không ghi DB, không sửa dashboard/task khác.

### File dự kiến đổi
- `daoanh/app.py` (hàm `api_places_vi_map_list`)
- `daoanh/admin/namevimap.html` (nếu cần, chỉ khi hiển thị sai field name)

Backup bắt buộc trước khi sửa: `daoanh/docs/sessions/2026-10-26/`.

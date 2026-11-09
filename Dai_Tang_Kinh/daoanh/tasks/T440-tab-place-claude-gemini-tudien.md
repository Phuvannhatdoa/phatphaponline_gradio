---
id: T440
title: "Bug verify: Tab Place thiếu giá trị cột Claude/Gemini/Từ điển trong namevimap.html"
status: done
created: 2026-10-21
updated: 2026-10-21
done_when:
  - "Tab Place (/daoanh/admin/namevimap.html) hiển thị giá trị cột Claude, Gemini, Từ điển cho các Place ID có dữ liệu thật trong DB, lấy từ cùng nguồn/API mà Tab ETL dùng (không tự chế nguồn mới, không hard-code)."
  - "Nếu một cột thật sự không có dữ liệu cho một dòng thì hiển thị đúng dấu hiệu rõ nghĩa (vd '—') kèm lý do xác minh được, không bịa giá trị."
  - "QA (daoanh-qa) xác nhận bằng browser thật tại 127.0.0.1, screenshot before/after, network log, số liệu khớp Tab ETL cho cùng Place ID."
  - "python -X utf8 -m py_compile app.py (nếu sửa) và node scripts/lint-check.js đều pass."
  - "Admin xác nhận DONE."
---

## Mô tả
Sửa bug Tab Place trong admin/namevimap.html: các cột Claude, Gemini và Từ điển luôn hiện '—' dù DB có dữ liệu. Mục tiêu là hiển thị giá trị lấy đúng nguồn như Tab ETL cho cùng Place ID; cột nào thật sự không có dữ liệu thì giữ '—' kèm lý do, không hard-code và không ghi DB. Nguyên nhân chưa xác minh, file yêu cầu debugger audit trước khi sửa.

## Triệu chứng

Tab Place trong `http://127.0.0.1:8080/daoanh/admin/namevimap.html` — bảng có cột
"Place ID | Hán tự | name_vi hiện tại | Claude | Gemini | TTL | Từ điển" nhưng 3 cột
Claude, Gemini, Từ điển luôn hiển thị "—" (trống), dù Admin xác nhận các nguồn này có
dữ liệu thật trong DB (Admin: "gọi trong DB 22 bộ từ điển ra giống như bên TAB ETL").

## Route/case tái hiện

- `http://127.0.0.1:8080/daoanh/admin/namevimap.html` → Tab "Place".
- So sánh với Tab "ETL" cùng trang (đã có cột Claude hiển thị qua
  `<span id="codex-col-status">`, ~dòng 728 `admin/namevimap.html`, và endpoint
  `/api/admin/codex-transliterate/status` ~dòng 16286–16308 `app.py`).

## Nguyên nhân nghi ngờ (chưa xác minh, debugger phải audit trước khi sửa)

- Tab Place có thể là code placeholder "giai đoạn 2, chưa triển khai" theo báo cáo
  trước đó của debugger — Gemini có ~16,665 dòng dữ liệu nhưng chưa nối UI; Claude
  chưa có dữ liệu cho place.
- Cần xác minh: (a) Tab ETL lấy cột Claude/Gemini/Từ điển qua endpoint/API nào;
  (b) Tab Place hiện gọi endpoint nào (nếu có) và vì sao trả rỗng;
  (c) "22 bộ từ điển" nằm ở bảng/cột nào trong DB và Tab ETL hiển thị nó ra sao.

## Phạm vi dự kiến

- Có thể sửa: `daoanh/admin/namevimap.html` (JS render Tab Place), `daoanh/app.py`
  (thêm/sửa endpoint API phục vụ Tab Place, tái dùng logic Tab ETL đã có).
- KHÔNG sửa raw DILA/Marcus/CBETA/TTL. KHÔNG ghi DB. KHÔNG đổi schema.
- KHÔNG hard-code giá trị hiển thị trong component — nếu DB chưa có dữ liệu, giữ "—"
  và ghi rõ lý do trong báo cáo.

## Backup

- `daoanh/docs/sessions/2026-10-21/namevimap.html.bak_T440`
- `daoanh/docs/sessions/2026-10-21/app.py.bak_T440`

## Ghi chú điều phối

- Giao `daoanh-debugger` audit + fix tối thiểu.
- Sau đó giao `daoanh-qa` kiểm chứng độc lập bằng browser thật (127.0.0.1).
- KHÔNG đánh `status: done` cho đến khi Admin xác nhận.

---
id: T372
title: "Fix bug: Admin person page A000074 — nhiều trường không hiển thị"
status: done
created: 2026-10-12
updated: 2026-10-20
parent: null
depends_on: []
blocked_by: []
done_when:
  - "Alternative names (4 items) hiển thị đúng trên admin person page"
  - "Birth/death dates hiển thị đúng"
  - "Sex/gender hiển thị đúng"
  - "Dynasty hiển thị đúng"
  - "Place of origin hiển thị đúng (許州, không phải Năng Huyền)"
  - "Works in Tripitaka hiển thị"
  - "Bibliography (7 items) hiển thị"
  - "Wikidata IDs (2 items) hiển thị"
  - "Hán (raw) không còn trống"
  - "Hán tự / Âm tiết không còn '?/?'"
  - "Tiểu sử Việt hiển thị đúng bản dịch (không phải '(chưa dịch)') hoặc lý do xác đáng nếu chưa có bản dịch"
  - "Section 'THẦY / HỌC TRÒ (DILA LINEAGE)' không còn bị duplicate trên admin person.html (xem case A000035): xóa render của section lineage đầu tiên (incomplete/sai), giữ lại section cuối (full DILA data)"
  - "daoanh-qa xác nhận ĐẠT"
  - "Admin xác nhận DONE"
  - "Teacher/Student (Thầy/Học trò) hiển thị charwise Vietnamese transliteration, không còn 'chưa có tên VI' khi tên Việt chưa có trong DB (ví dụ: 行思 A003666 → Hành Tư)"
  - "Bibliography entries (A000074) hiển thị clickable link <a href> tới đúng URL target trong <ref target=...>, không còn plain text"
  - "daoanh-qa xác nhận ĐẠT cho phần bibliography link"
  - "Admin xác nhận DONE cho phần bibliography link"
---

## Triệu chứng

Route: `http://127.0.0.1:8080/daoanh/admin/person.html?id=A000074` (local)

Trên trang admin person detail cho A000074, các trường sau không hiển thị hoặc hiển thị sai:

- Alternative names (4 items) — không hiển thị
- Birth/death dates — không hiển thị
- Sex/gender — không hiển thị
- Dynasty — không hiển thị
- Place of origin — hiển thị sai dữ liệu ("Năng Huyền" thay vì "許州")
- Works in Tripitaka — không hiển thị
- Bibliography (7 items) — không hiển thị
- Wikidata IDs (2 items) — không hiển thị
- "Hán (raw)" — hiển thị "(trống)"
- Hán tự / Âm tiết — hiển thị "? / ?"
- Tiểu sử Việt — hiển thị "(chưa dịch)"

## XML source đối chiếu

A000074 trong `Buddhist_Studies_Person_Authority.xml` có đầy đủ: persName (tên chính + 4 alternative), birth/death dates, sex, dynasty, placeOfOrigin, works, bibl, Wikidata IDs.

## Nguyên nhân nghi ngờ (chưa xác minh — cần audit)

- API `/daoanh/admin` endpoint cho person detail không trả đủ field (thiếu join hoặc field bị bỏ qua khi serialize).
- Hoặc dữ liệu đã import sai/thiếu từ XML vào DB (ETL bug khi import A000074 cụ thể, hoặc theo batch).
- Hoặc HTML template / JS renderer trong `admin/person.html` không map đúng field từ response JSON (field name mismatch, null-check lỗi).
- "Place of origin" sai (Năng Huyền thay vì 許州) gợi ý có thể bị lấy nhầm field khác, hoặc resolver map sai placeOfOrigin ID.

## Fix bổ sung — Duplicate "THẦY / HỌC TRÒ (DILA LINEAGE)" section

**Phát hiện thêm (case A000035):** Admin person page render section lineage 2 lần:
- Section phía trên (giữa trang): incomplete/sai dữ liệu → cần **XÓA** render này.
- Section phía dưới (cuối trang): đầy đủ dữ liệu DILA → **GIỮ LẠI**.

Nguyên nhân nghi ngờ: template `admin/person.html` (hoặc JS renderer liên quan) gọi render lineage section 2 lần — có thể do include/partial bị gọi 2 nơi, hoặc 2 đoạn code tách biệt cùng render cùng loại section.

Yêu cầu: xóa đúng đoạn render section lineage đầu tiên (section sai/thiếu), không đụng tới section cuối (full DILA). Verify trên cả A000074 và A000035.

## Phạm vi dự kiến

- Audit trace đầy đủ: raw XML → DB (import/ETL) → API response → resolver → admin person.html renderer.
- Không hard-code giá trị riêng cho A000074; sửa đúng lớp gây lỗi (có thể ảnh hưởng nhiều person khác cùng pattern).
- Backup các file sẽ sửa vào `docs/sessions/YYYY-MM-DD/` trước khi sửa.

## Fix bổ sung (2026-10-13) — Teacher/Student hiển thị trống sau khi xóa TTL name loading

**Triệu chứng:** Sau khi xóa TTL name loading (fix trước đó trong cùng task), phần Teacher/Student (Thầy/Học trò) trên admin person page hiển thị "chưa có tên VI" (trống) thay vì tên Việt phiên âm. Ví dụ: 行思 (A003666) không hiển thị "Hành Tư".

**Nguyên nhân nghi ngờ (chưa xác minh):** `relCardVi()` trong `admin/person.html` (khoảng dòng 384+) trước đây lấy tên Việt từ TTL; sau khi bỏ nguồn đó, không còn fallback charwise transliteration. `admin/dila_person_index.html` đã có sẵn hàm charwise transliteration (Hán → Hán-Việt từng chữ) dùng cho mục đích tương tự — cần audit hàm đó, xác nhận đúng là nguồn charwise map, rồi tái dùng logic (không hard-code) trong `relCardVi()`.

**Yêu cầu:**
- Audit hàm charwise transliteration hiện có trong `admin/dila_person_index.html`.
- Tái dùng (không copy-paste mù, hiểu rõ input/output) logic đó trong `relCardVi()` ở `admin/person.html` để render tên Việt phiên âm charwise khi chưa có tên Việt chính thức trong DB (badge rõ đây là transliteration tự động, không phải tên nguồn DILA/ZQLOCAL xác thực).
- Nếu cần, thêm field charwise vào relations payload trả về từ `app.py` — chỉ nếu thật sự cần, không query lại toàn bộ.
- Không gán nguồn sai (badge/source_id) cho tên transliteration tự động này.
- Test case: 行思 A003666 → hiển thị "Hành Tư". Thêm ít nhất 1 case fallback (tên không map được / tên rỗng).
- Backup đã tạo: `docs/sessions/2026-10-13/person.html`, `docs/sessions/2026-10-13/app.py` (trước khi sửa).

## Fix bổ sung (2026-10-13) — Bibliography links chưa clickable

**Triệu chứng:** XML gốc có `<bibl><ref target="http://...">text</ref></bibl>`, ví dụ:

```xml
<bibl><ref target="http://buddhistinformatics.dila.edu.tw/fosizhi/ui.html?book=y109%26cpage=0108%26target=A000074">y109p0108(徑山集) { 大顛 } </ref></bibl>
```

Nhưng trên admin person page, bibliography chỉ hiển thị text thuần (`y109p0108(徑山集) { 大顛 }`), không phải link bấm được tới URL trong `target`.

**Mong muốn:** Hiển thị `<a href="http://buddhistinformatics.dila.edu.tw/...">y109p0108(徑山集)</a>` (clickable, mở đúng URL DILA).

**Nguyên nhân nghi ngờ (chưa xác minh — cần audit):**
- `app.py` (chỗ parse/extract bibliography từ XML, nghi ở khu vực `listbibl`/`bibl` parsing) có thể đang chỉ lấy `.text` của `<ref>` mà bỏ qua attribute `target`, nên response JSON gửi lên không có URL.
- Hoặc JSON đã có URL nhưng `admin/person.html` (phần render bibliography, khu vực `dila-split-body`) chỉ render plain text, không bọc `<a href>`.

**Phạm vi dự kiến:**
- Audit: raw XML `<ref target>` → DB/cache (nếu có lưu) → API response field → renderer trong `person.html`.
- Sửa đúng lớp bị mất dữ liệu (không hard-code URL riêng cho A000074).
- Escape HTML đúng cho text hiển thị bên trong `<a>` (tránh XSS nếu text có ký tự đặc biệt).
- Test case: A000074 — toàn bộ 7 bibliography entries phải có link clickable, mở đúng URL target. Thêm 1 case fallback: entry không có `<ref target>` (chỉ có bibl text thuần) vẫn hiển thị bình thường, không lỗi.
- Backup các file sẽ sửa vào `docs/sessions/2026-10-13/` trước khi sửa (nếu chưa có backup mới nhất của app.py/person.html).

## Fix bổ sung (2026-10-13) — Override charwise cho 希遷 (A010291): "Hơi Thiên" → "Hy Thiên"

**Triệu chứng:** Charwise transliteration (phần của fix "Teacher/Student hiển thị trống" ở trên) map ký tự 希 sai, cho ra "Hơi" thay vì "Hy". Case cụ thể: 石頭希遷 (Thạch Đầu Hy Thiên), person A010291, hiển thị trên A000074 ở phần Teacher section là "希遷 (Hơi Thiên) A010291" — sai, phải là "希遷 (Hy Thiên) A010291".

**Nguyên nhân nghi ngờ (chưa xác minh):** Dictionary/mapping charwise (có thể trong `person_hanviet_debug` table, hoặc dict trong code — nghi ở `admin/dila_person_index.html` hoặc `app.py` chỗ tái dùng logic charwise cho `relCardVi()`) có entry sai cho ký tự 希 (Hán-Việt đúng là "Hy", không phải "Hơi").

**Yêu cầu:**
- Audit xác định nguồn charwise map hiện tại (DB table `person_hanviet_debug` hay dict trong code).
- Sửa đúng entry cho ký tự 希 (không hard-code riêng cho A010291 — sửa ở mapping dùng chung cho mọi person có ký tự 希).
- Không đụng các ký tự khác trong cùng dictionary.
- Test case yêu cầu: A010291 (石頭希遷) hiển thị "Hy Thiên" trên teacher section của A000074.
- Thêm 1 case fallback: kiểm tra một person khác có ký tự 希 (nếu có) không bị regression, hoặc ký tự lân cận trong bảng không bị đổi nhầm.
- Admin ghi rõ: đây là "quick fix" override 1 case, vấn đề charwise/dictionary rộng hơn để task T373 xử lý riêng.
- Backup file sẽ sửa vào `docs/sessions/2026-10-13/` trước khi sửa (nếu chưa có backup mới nhất).

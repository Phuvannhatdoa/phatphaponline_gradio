# Nháp mục "## Mô tả" (AGENTS §21) — CHƯA ÁP VÀO FILE

Lý do chưa áp: T454/T455/T456/T457 là file **untracked** (không có blob HEAD). Theo quy tắc blob-only,
không thể commit chúng mà không thêm file mới nguyên khối (= nuốt WIP phiên khác). Nháp này để Admin/agent
áp khi các file được đưa vào git (hoặc Admin cho phép commit nguyên file).

Vị trí chèn: NGAY SAU khối frontmatter `---` đóng, TRƯỚC `# Tn — ...`.

---

## T454 — chèn trước "# T454 — Hậu tố..."

## Mô tả
Làm sạch 8 tên địa danh Việt có hậu tố lạ "_ Huý" / "_ Ngoa" trong `namevi_map_places.name_vi` (sinh từ T453). Hậu tố này hiện lộ ra thẻ người trên HOME (ví dụ "Hoằng Phúc Tự _ Huý"); việc cần làm là xác định nghĩa hậu tố, đề xuất sửa từng dòng, và sửa sau khi Admin duyệt, có backup và rollback. Phạm vi chỉ 8 dòng; không sửa `places_dila` (raw DILA).

### Trạng thái hiện tại
- Đã làm: đo 8 dòng (mode=ro, 2026-10-22); xác định 5 dòng ví dụ; kế hoạch bước trong `docs/sessions/2026-10-26/n4-plan.md`.
- Chưa làm: truy vết nguồn hậu tố; đề xuất sửa; CSV before; backup; UPDATE; verify UI. Chưa ghi DB.

### Câu hỏi cần Admin quyết
- Q5: Hậu tố "_ Huý" / "_ Ngoa" là ghi chú giữ lại (chuyển sang cột note_vi) hay rác cần xoá? — chưa có đáp án.

---

## T455 — chèn trước "# T455 — Chuẩn hoá tên Việt người..."

## Mô tả
Chuẩn hoá `people.name_vi` (ZQLOCAL=5) theo bằng chứng kinh lục DILA: 794 người lệch tên Việt so với bản dịch Cloud và 532 tên còn sót chữ Hán. Việc gồm phân loại 794 dòng (ZQ sai rõ / alias cùng người / khác quy ước chính tả), đề xuất âm cho 532 tên sót Hán, sửa theo lô có Admin duyệt, giữ giá trị cũ (additive) và không gán tên Việt cho nguồn DILA. Tên Cloud chỉ là tham khảo, không tự ghi đè.

### Trạng thái hiện tại
- Đã làm: có CSV bằng chứng `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv` (794 dòng); đo 532 tên có chữ Hán (2026-10-22).
- Chưa làm: gộp/không gộp với task chuẩn hoá đang chạy; phân loại (a)(b)(c); đề xuất âm; script `t455_name_vi_fix.py`; bảng lịch sử; sửa theo lô. Chưa ghi DB.

### Câu hỏi cần Admin quyết
- Q3a: Đã có task chuẩn hoá tên người đang chạy không? Nếu có → gộp T455 vào đó (đáp án: chưa có).
- Q3b: Ưu tiên lô có số lần xuất hiện cao, hay nhóm 532 tên sót Hán trước? (chưa có đáp án).
- Q3c: Duyệt bảng lịch sử additive `people_name_vi_history` (schema đề xuất) không? (chưa có đáp án).

---

## T456 — chèn trước "# T456 — Autocomplete ô Search trang chủ"

## Mô tả
Thêm gợi ý (autocomplete) cho ô Search trang chủ `/daoanh/`: khi gõ từ 2 ký tự, hiện dropdown ba nhóm kinh lục DILA, người và địa danh, chọn bằng phím hoặc click. API gợi ý phải dưới 200 ms và không quét LIKE toàn bảng khi có FTS; luồng "Tìm" của T453 và gõ-từng-ký-tự của T404 phải giữ nguyên. Phụ thuộc Gate 0 (khôi phục backend DILA đã mất) và T450.

### Trạng thái hiện tại
- Đã làm: chốt phương án và điểm chạm code (`n4-plan.md`, mục T456); chưa có code.
- Chưa làm: Gate 0; đo timing và kiểm FTS5 trên bản copy DB; route `/daoanh/api/public/suggest`; UI dropdown; backup `app.py`/`index.html`; verify.
- Chặn bởi: Gate 0 (code backend T453 bị mất — xem `docs/sessions/2026-10-26/gate0-report.md`).

### Câu hỏi cần Admin quyết
- Q4a: Tạo bảng FTS5 mới cho kinh lục (ghi DB, additive) hay chỉ dùng LIKE prefix (không ghi DB, chậm hơn)? — chưa có đáp án.
- Q4b: T450 (pending) làm trước, hay T456 đi trước? — chưa có đáp án.
- Q1 (Gate 0, chặn T456): Ai khôi phục code backend T453 từ backup T445-coder, khi nào, và có đưa lại luồng DILA trên HOME (đảo ngược T467) không? — chưa có đáp án.

---

## T457 — KHÔNG CẦN CHÈN
File worktree đã có `## Mô tả` (dòng 31). Nếu muốn thêm `### Trạng thái hiện tại` về việc T453 (B) đã được Admin duyệt (06:01, 2026-10-22)
theo bản ghi mới nhất (xem tasktodo T453 note trong commit 9bf4c021), ghi thêm vào mục Mô tả có sẵn; không đổi status/done_when.

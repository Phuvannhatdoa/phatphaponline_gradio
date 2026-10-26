---
id: T455
title: Chuẩn hoá tên Việt người (people.name_vi, ZQ) dựa trên đối chiếu kinh lục DILA (794 lệch + 532 sót chữ Hán)
status: pending
created: 2026-10-22
updated: 2026-10-22
owner: daoanh-debugger
module: Data / Persons
priority: high
parent: T453
plan_approved_at: "2026-10-22 (Admin phê chuẩn đề xuất (3) trong T453: tạo task riêng). Ghi DB: CHƯA duyệt riêng."
done_when: >
  (1) Gộp với task chuẩn hoá tên người đang chạy (nếu có) — Admin chỉ định; không làm trùng.
  (2) Phân loại 794 người trong docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv thành:
      (a) ZQ sai rõ (vd. "Di Lắc Bồ Tát", "Vương Chùm", "Chờ Ngạc Vân", "Lã Dì Giản");
      (b) tên khác của cùng người — biệt hiệu/tự/dị thể (范寄東/范古農, 覺音/佛音, 了參/葉均) → không sửa, ghi alias;
      (c) khác do quy ước (Huệ/Tuệ, Thọ/Thụ, Trước/Trứ, Tì/Tỳ, dấu hoà/hóa) → theo quy tắc chính tả dự án.
  (3) 532 people.name_vi còn sót chữ Hán (vd. A000002 "𧧌Chấn", A000047 "Vu 頔", A000903 "Hạ 丏 Tôn") — đề xuất âm.
  (4) Sửa theo lô, mỗi lô Admin duyệt; additive: giữ giá trị cũ ở cột/bảng lịch sử, source_id ZQLOCAL=5 cho tên Việt
      (KHÔNG gán DILA); backup + ROLLBACK row.
  (5) Sau sửa, HOME/kinh lục DILA tự hiển thị tên mới (T453 đọc people.name_vi lúc truy vấn — không cần import lại).
  (6) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Khôi phục name_vi từ bảng/cột lịch sử hoặc CSV giá trị cũ của từng lô.
---

## Mô tả
Chuẩn hoá `people.name_vi` (nguồn ZQLOCAL=5) theo bằng chứng kinh lục DILA: 794 người có tên Việt lệch so với bản dịch Cloud và 532 tên còn sót chữ Hán. Việc gồm phân loại 794 dòng (ZQ sai rõ / cùng người khác tên gọi / khác quy ước chính tả), đề xuất âm cho 532 tên sót Hán, rồi sửa theo lô có Admin duyệt; giữ giá trị cũ (additive) và không gán tên Việt cho nguồn DILA. Tên Cloud chỉ tham khảo, không tự ghi đè.

### Trạng thái hiện tại
- Đã làm: có CSV bằng chứng `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv` (794 dòng); đo 532 `people.name_vi` có chữ Hán (2026-10-22); bước thực thi (1)–(5) đã lập trong `docs/sessions/2026-10-26/n4-plan.md` (mục T455).
- Chưa làm: gộp hay không gộp với task chuẩn hoá tên người đang chạy (chưa rõ); phân loại (a)/(b)/(c); đề xuất âm cho 532 tên; script `scripts/t455_name_vi_fix.py`; bảng lịch sử `people_name_vi_history`; sửa theo lô. Chưa ghi DB.
- Lưu ý: T453 đã dùng DB cho 2 tên lệch (A001713 Huệ/Tuệ Uyển; A000457 "Lã Dì Giản" nghi sai) — cần đưa vào phân loại.

### Câu hỏi cần Admin quyết
- Q3a: Đã có task chuẩn hoá tên người đang chạy không? Nếu có → gộp T455 vào đó (đáp án: chưa có).
- Q3b: Ưu tiên lô có số lần xuất hiện cao (`so_lan`), hay nhóm 532 tên sót Hán trước? — chưa có đáp án.
- Q3c: Duyệt bảng lịch sử additive `people_name_vi_history` (schema đề xuất) không? — chưa có đáp án.

# T455 — Chuẩn hoá tên Việt người từ bằng chứng kinh lục DILA

## Nguồn bằng chứng (T453)
- `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv` — 794 người: person_id, tên Hán catalog, tên Hán DB,
  tên Việt DB (ZQ), tên Việt Cloud (phiên âm theo ngữ cảnh, unreviewed), bộ đầu tiên, số lần xuất hiện.
- Bản dịch Cloud: `data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/<X>.vi.json` (name_vi + notes).
- DB đo 2026-10-22: 532 `people.name_vi` chứa ký tự Hán.

## Nguyên tắc
- Tên Cloud chỉ là **tham khảo**, không tự động ghi đè (quyết định Admin 2026-10-22).
- Không sửa `people.name_zh` (DILA). Mọi tên Việt vẫn là ZQLOCAL=5.

## Câu hỏi cho Admin
1. Đã có task chuẩn hoá tên người đang chạy chưa (Admin nhắc "task khác đang chuẩn hoá từng tên")? Nếu có → gộp T455 vào đó.
2. Ưu tiên lô nào trước: người xuất hiện nhiều trong kinh lục (cột so_lan) hay nhóm sót chữ Hán?

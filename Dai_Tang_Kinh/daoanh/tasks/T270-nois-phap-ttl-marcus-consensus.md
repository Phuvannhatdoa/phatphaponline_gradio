---
id: T270
title: "Vẽ truyền thừa theo nối pháp: cạnh nối pháp = TTL và Marcus cùng xác nhận; số đời tính theo dòng nối pháp"
module: Lineage / Generation
priority: high
status: in_progress
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: BUG-027
plan_approved_at: "2026-10-10 (Admin quy tắc: cạnh được TTL và Marcus cùng xác nhận là nối pháp; không cần duyệt từng cạnh)"
done_when: >
  (1) Có danh sách cạnh nối pháp = TTL và Marcus cùng xác nhận (file dẫn xuất, không ghi đè DB).
  (2) Engine tính số đời chỉ đi qua cạnh nối pháp; cạnh tham học vẫn hiển thị nhưng không dùng để đếm.
  (3) Thiên Nhiên (A009460) cho ra đời 36 theo đường Huệ Năng (33) → Thanh Nguyên Hành Tư (34) → Thạch Đầu Hy Thiên (35) → Thiên Nhiên (36).
  (4) Cạnh Đạo Khâm (A004218) → Thiên Nhiên KHÔNG nằm trong danh sách nối pháp (TTL không ghi nối pháp).
  Không ghi DB. Không đánh DONE khi chưa có xác nhận Admin.
revert: >
  Danh sách nối pháp là file dẫn xuất; xóa file để quay lại. Thay đổi engine có bản sao trong docs/sessions/2026-10-10/.
outcome: >
  2026-10-10: Admin quy tắc đã chốt. Bằng chứng A009460 (đọc chỉ): TTL ghi PHÁP TỰ của Thạch Đầu Hy Thiên;
  Thạch Đầu là PHÁP TỰ đời thứ nhất của Thanh Nguyên. Marcus có cạnh thầy-trò tương ứng.
  Đạo Khâm: Marcus có cạnh, TTL chỉ ghi "tham vấn" → không đủ hai nguồn → loại khỏi nối pháp.
---

# T270 — Vẽ truyền thừa theo nối pháp

## 1. Quy tắc (Admin chốt 2026-10-10)

- Một trò có thể học nhiều thầy. Số đời tính theo **dòng nối pháp**, lấy từ Truyền Đăng Lục.
- DILA ghi đủ các mối thầy-trò nhưng không đánh dấu nối pháp.
- **Cạnh là nối pháp khi TTL và Marcus cùng xác nhận.** Không cần Admin duyệt từng cạnh.
- Cạnh chỉ có ở một nguồn, hoặc chỉ có "tham vấn/lễ bái", là **tham học** (chỉ hiển thị, không đếm đời).

## 2. Các bước

- [ ] **Bước 1 — Dựng danh sách cạnh nối pháp** (file dẫn xuất, chỉ đọc DB): với mỗi cạnh thầy-trò, kiểm TTL có ghi "PHÁP TỰ"/"đắc pháp" và Marcus có cạnh tương ứng. Xuất `data/dharma_edges.json` kèm nguồn từng cạnh.
- [ ] **Bước 2 — Engine dùng danh sách nối pháp**: `parents()` trong `src_python/generation_engine_v2.py` chỉ lấy cạnh có trong `dharma_edges.json`. Sao lưu trước khi sửa.
- [ ] **Bước 3 — Kiểm chứng A009460**: kết quả đời 36 qua Hy Thiên; cạnh Đạo Khâm không được dùng.
- [ ] **Bước 4 — Hiển thị**: tông không liên quan báo "không thuộc tông này"; thiếu mốc báo "thiếu mốc"; mâu thuẫn báo rõ.
- [ ] **Bước 5 — QA** bằng `daoanh-qa` (số liệu tính lại, không ghi DB).
- [ ] **Admin xác nhận DONE.**

## 3. Ràng buộc

- Không ghi DB. Không đổi schema. Không xóa cạnh DILA.
- Không git. Không deploy VPS.
- Mọi thay đổi có sao lưu trong `docs/sessions/2026-10-10/`.

## 4. Liên quan

- BUG-027 (Pháp mạch không tính số đời).
- Báo cáo đối chiếu TTL/Marcus ngày 2026-10-10 (A009460, A010291, A003666, A004218).

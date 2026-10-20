# Session — 2026-09-08 · Master Dashboard 4 cột (đồng bộ bản vẽ Admin cũ → lộ trình evidence-first)

**Kiểu phiên:** docs-only (không code, không DB). **Mục đích:** đồng bộ "bảng Master Roadmap" thế hệ đầu (do Lee Tổng cung cấp lại) vào `docs/roadmap.md` hiện hữu, đúng logic đã phê chuẩn T108–T114.
**Trạng thái:** Done.

## 1. Nội dung yêu cầu (Lee Tổng)
- Bản vẽ gốc đề hệ thống `PROJECT_STATUS.md` (filename cũ) + dashboard 7 task với trạng thái T108 Doing / T112 Pending / T109×2 / T110 / T111 / T113.
- Câu hỏi: "check và xác nhận vấn đề đúng logic chưa; nếu chưa chỉ ra và đề xuất giải pháp tối ưu cho dự án".

## 2. Xác minh — bản vẽ cũ có 4 điểm KHÔNG còn đúng logic
1. **`PROJECT_STATUS.md` không tồn tại** (worktree + tracked đều không có); SSOT thực tế = `docs/tasktodo.md` + `docs/progress.md` + dashboard `dashboard_process.html`.
2. **"13/25 nguồn" SAI** → verified **13 đăng ký / 5 active / 8 pending** (`data_sources`=13).
3. **Số/nội dung task lạc hậu**: bảng cũ chẻ T109→2 task, T111=Doctrine Retrieval; chuỗi chuẩn **T108–T114** (T03+T04→T109, T06 scoring→T100 + T111 persona display).
4. **Trạng thái cũ**: "T108 Doing" — thực tế **T108 DONE** (`456809d`) + **T109 DONE** (`243c490a`).

## 3. Quyết định (Lee Tổng xác nhận)
1. **roadmap hiện hữu** — chèn section Master Dashboard vào `docs/roadmap.md`; KHÔNG tạo `PROJECT_STATUS.md` (giữ SSOT).
2. **4 cột** Task-ID + Module + Status + Mục tiêu (không thêm cột Người phụ trách).
3. **Có commit** theo convention `docs: ... + session`.

## 4. Thay đổi (docs-only)
- `docs/roadmap.md`: thêm section **"Master Dashboard (7 tasks)"** 4 cột + dòng ghi chú ánh xạ T03+T04→T109 / T111=T06 phần còn lại / T108-T109 DONE, đặt ngay trên bảng "Lộ trình T108–T114" (giữ nguyên bảng chi tiết, SSOT).
- `docs/sessions/2026-09-08_master-dashboard.md`: session log này.
- `docs/ROLLBACK.md`: thêm row commit docs này (để revert tiện lợi).

## 5. Không làm
- KHÔNG tạo `docs/PROJECT_STATUS.md`.
- KHÔNG đụng code/DB.
- KHÔNG thêm cột "Người phụ trách".

## 6. Commit
- 1 commit docs: `docs: Master Dashboard 4 cột đồng bộ roadmap T108–T114 (T03+T04→T109, 13/5/8)` — parent `780766f1`, temp-index `b4_commit.py`, refname `master`.
- Rollback: `git revert --no-edit <hash>` (ghi trong ROLLBACK).

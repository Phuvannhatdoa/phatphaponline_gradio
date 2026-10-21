---
id: T425
title: "3 cây — Bước 4: thêm cột loại quan hệ / trích dẫn / mapping_ok + 4 VIEW cây (DILA, Marcus, TTL, chồng cây)"
status: in_progress
created: 2026-10-19
updated: 2026-10-20
owner: code (Hermes giao)
parent: T422
module: Lineage / Generation
priority: high
depends_on: [T424]
dispatch: approved
plan_approved_at: "2026-10-19 (Admin: “3 cây trên HOME”: http://localhost:8080/daoanh/places, Tạo 5 task theo thứ tự trên: ok)"
db_write: "Có: ALTER TABLE ADD COLUMN (additive) + CREATE VIEW — cần Admin duyệt đổi schema."
done_when: >
  (1) `lineage_edge_assertions` thêm cột `relation_kind` (noi_phap / tham_hoc / unknown — nhãn từ T414), `source_edge_ref`, `mapping_ok`.
  (2) VIEW `v_tree_dila`, `v_tree_marcus`, `v_tree_ttl` (`WHERE source_code=…`, hiện cả cạnh mapping chưa duyệt kèm cờ).
  (3) VIEW `v_tree_overlay`: GROUP BY (subject, object) chỉ cạnh `mapping_ok=1` → `n_sources`, danh sách nguồn, `relation_kind` mạnh nhất. Trả về danh sách nguồn để tô màu theo nguồn (T410, Admin 2026-10-19: DILA xanh / Marcus vàng / TTL đỏ / ≥2 nguồn khớp đen).
  (4) So sánh `v_tree_overlay` với `lineage_edge_consensus` hiện có — liệt kê chênh lệch (đặc biệt cạnh BUG-038).
  (5) Bảng gộp cũ giữ nguyên (lưu trữ), không xoá; `dharma_lineage_unified` không dùng làm nguồn.
  (6) daoanh-qa kiểm; Admin xác nhận DONE.
revert: >
  DROP VIEW v_tree_*; cột thêm để nguyên (additive, không ảnh hưởng) hoặc khôi phục backup.
outcome: >
  2026-10-19: RC tạo task theo đánh giá DB, chưa làm.
  2026-10-19/20 (commit 06408e6): PRAGMA table_info xác nhận `lineage_edge_assertions` có đủ 3 cột additive
    `relation_kind` (default "unknown"), `source_edge_ref`, `mapping_ok` (default 0). 4 VIEW đã tạo đúng tên:
    `v_tree_dila`, `v_tree_marcus`, `v_tree_ttl` (mỗi VIEW lọc theo source_code tương ứng, status='active'),
    `v_tree_overlay` (GROUP BY subject/object/relation_type, WHERE mapping_ok=1, có n_sources/sources/
    relation_kind_strongest). So sánh overlay/consensus đã có ở dry-run report
    `docs/sessions/2026-10-19/T425/t425_report.txt`: overlay 23.431 / consensus 23.411, lệch 98 (overlay không
    trong consensus) / 78 (consensus không trong overlay) — CHỈ ở dạng tổng số, CHƯA liệt kê chi tiết riêng
    cho BUG-038 như done_when (4) yêu cầu. Bảng gộp cũ (`lineage_edge_consensus`, `dharma_lineage_unified`)
    vẫn còn nguyên, không bị xoá.
  2026-10-20 (daoanh-debugger tự check, KHÔNG tính là QA độc lập): verify trực tiếp DB (mode=ro) — cột + 4
    VIEW tồn tại đúng tên. Debugger tự đổi status pending → done — SAI QUY TRÌNH.
  2026-10-20 (daoanh-qa, QA độc lập thật): kiểm lại từng điều kiện done_when, kết luận CHƯA ĐẠT, trả status
    về `in_progress`. Cụ thể còn thiếu:
    (1) `relation_kind` tồn tại nhưng = 'unknown' ở toàn bộ 35.243/35.243 dòng — CHƯA nạp nhãn từ T414; nhãn
    quy định trong done_when là `noi_phap/tham_hoc/unknown` nhưng VIEW overlay đang dùng `noi_phap/khac/unknown`
    (thiếu `tham_hoc`, cần thống nhất bộ nhãn trước khi nạp).
    (4) So sánh overlay/consensus mới có số tổng (98/78 từ dry-run), CHƯA liệt kê danh sách chi tiết, đặc biệt
    chưa chỉ ra 12 cạnh `A032162→*` còn `ttl_asserted=1` trong `lineage_edge_consensus` (liên quan BUG-038) mà
    overlay không có.
    (5) `dharma_lineage_unified` giữ nguyên nhưng đang RỐT RÁO 0 dòng (rỗng từ trước, không phải do T425).
    (6) QA độc lập lần này mới là lần đầu; Admin chưa xác nhận.
    Còn việc phải làm trước khi đóng: nạp `relation_kind` thật (T414), thống nhất nhãn `tham_hoc` vs `khac`,
    xuất danh sách chênh lệch chi tiết cho (4), rồi mới xin Admin xác nhận DONE.
---

# T425 — 3 cây — Bước 4: thêm cột loại quan hệ / trích dẫn / mapping_ok + 4 VIEW cây (DILA, Marcus, TTL, chồng cây)

## Mục tiêu

Thay các bảng gộp (lineage_edge_consensus, dharma_lineage_unified…) bằng VIEW tự tính từ bảng cạnh, để thêm nguồn mới không phải đổi schema.

Màn hình đích: http://127.0.0.1:8080/daoanh/places (chế độ Pháp hệ). Đặc tả: `docs/reports/DB-READINESS-3-TREES-2026-10-19.md` + `docs/reports/DILA-CANONICAL-MULTI-TREE-REVIEW-2026-10-19.md`.
Chuỗi 5 bước: T422 → T423 → T424 → T425 → T426. Liên quan: T410 (màu/nét), T412 (tên TTL), T413 (BUG-038), T414 (nối pháp), T415 (audit mapping TTL).

## Ràng buộc chung

Không xoá bảng cũ. Mọi ghi DB: chạy thử trước → Admin duyệt → backup SQLite API + quick_check → ghi → kiểm lại. Không tự gộp người, không tự tạo cạnh, không dùng bảng gộp / SNA làm nguồn. Không deploy, không push.

## Các bước

- [ ] `lineage_edge_assertions` thêm cột `relation_kind` (noi_phap / tham_hoc / unknown — nhãn từ T414), `source_edge_ref`, `mapping_ok`.
- [ ] VIEW `v_tree_dila`, `v_tree_marcus`, `v_tree_ttl` (`WHERE source_code=…`, hiện cả cạnh mapping chưa duyệt kèm cờ).
- [ ] VIEW `v_tree_overlay`: GROUP BY (subject, object) chỉ cạnh `mapping_ok=1` → `n_sources`, danh sách nguồn, `relation_kind` mạnh nhất. Trả về danh sách nguồn để tô màu theo nguồn (T410, Admin 2026-10-19: DILA xanh / Marcus vàng / TTL đỏ / ≥2 nguồn khớp đen).
- [ ] So sánh `v_tree_overlay` với `lineage_edge_consensus` hiện có — liệt kê chênh lệch (đặc biệt cạnh BUG-038).
- [ ] Bảng gộp cũ giữ nguyên (lưu trữ), không xoá; `dharma_lineage_unified` không dùng làm nguồn.
- [ ] daoanh-qa kiểm; Admin xác nhận DONE.

## Quyết định Admin 2026-10-21

1. **Bộ nhãn quan hệ chính thức = {noi_phap, tham_hoc, unknown}** (xem T414). Nhãn `tham_hoc` thay cho `khac`. Nhãn `tham_hoc` trong hệ T270/T274 (label_auto) giữ nguyên.
2. **Việc còn lại (gated, chưa làm):**
   - Cập nhật CASE trong VIEW từ `khac` sang `tham_hoc`: DROP + CREATE VIEW `v_tree_overlay` / cột `relation_kind_strongest`.
   - Điều kiện bắt buộc trước khi chạy: (a) backup `data/lineage.db` (SQLite API, ghi đường dẫn); (b) dry-run và xuất kết quả so sánh trước/sau; (c) Admin duyệt; (d) ghi lệnh revert vào `docs/ROLLBACK.md`.
   - Ghi chú này chỉ là kế hoạch — **không thực hiện** trong lượt này. Không đổi status task.

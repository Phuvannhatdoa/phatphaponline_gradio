---
id: T301
title: "M2 — Kiểm 148 claims Wikidata chỉ là EXTERNAL_ID"
module: Authority / Lineage
priority: p2
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: []
done_when: |
  Xác nhận 148 claims Wikidata chỉ là mã liên kết (P1187, P1188, P2477), không có tên.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
  2026-10-12: daoanh-qa đọc DB (read-only) — 148/148 claims source_id=6 là same_as → mã Q (object_text khớp ^Q:Q\d+$), 0 trường tên. PASS. Mô tả gốc ghi nhầm thuộc tính P1187/P1188/P2477 — DB thực tế không có các mã P này, toàn bộ là same_as gắn cho địa danh (PL...), không có người. Phát hiện phụ: 3 mã Q đang gắn cho 2 địa danh cùng lúc (Q11065384→PL000000019868,PL000000019870; Q19853247→PL000000017498,PL000000017499; Q8802338→PL000000013507,PL000000013509) — cần Admin xem có phải địa danh trùng. Chờ Admin xác nhận DONE.
---

# T301 — M2 — Kiểm 148 claims Wikidata chỉ là EXTERNAL_ID

## 1. Mục tiêu

Xác nhận 148 claims Wikidata chỉ là mã liên kết (P1187, P1188, P2477), không có tên.

## 2. Hiện trạng (đã kiểm 2026-10-10)

REALITY_CHECK ghi 148 claims Wikidata.

## 3. Các bước (agent làm lần lượt)

1) Truy vấn entity_claims source_id=6. 2) Phân loại theo thuộc tính.

## 4. Kiểm chứng

Bảng đếm theo thuộc tính.

### Kết quả kiểm chứng (2026-10-12, daoanh-qa, chỉ đọc)

Mở `data/lineage.db` ở chế độ `mode=ro`. Tổng số dòng `entity_claims` với `source_id=6` là **148**, khớp số ghi trong task. 145 mã Q khác nhau, gắn cho 148 entity (địa danh `PL...`). `data_sources.id=6` = "Wikidata (reference)", CC0.

| Thuộc tính (claim_type/predicate) | Số dòng | EXTERNAL_ID? | Ghi chú |
|---|---|---|---|
| same_as | 148 | Có | `object_text` khớp mẫu `^Q:Q\d+$` ở cả 148 dòng. `subject` luôn là mã `PL…` (địa danh). `authority_role` = CORROBORATING, `editor_note` rỗng. |

Không có dòng nào chứa name/label/alias trong claim_type hay predicate (0 dòng). Không có claim từ nguồn khác trỏ `source_url`/`source_reference` về Wikidata.

**Khác biệt với mô tả ban đầu:** Task ghi "P1187, P1188, P2477" — DB không có các mã P này; toàn bộ 148 dòng dùng predicate `same_as`, chỉ gắn cho địa danh, không gắn cho người.

**Cần Admin xem xét (ngoài phạm vi PASS/FAIL):** 3 mã Q trùng cho 2 địa danh — có thể là bản ghi địa danh bị nhân đôi:
- Q11065384 → PL000000019868, PL000000019870
- Q19853247 → PL000000017498, PL000000017499
- Q8802338 → PL000000013507, PL000000013509

**Kết luận: PASS** — 148/148 claims chỉ là EXTERNAL_ID (same_as → Q-id), không có tên. Chờ Admin xác nhận DONE.

## 5. Không làm trong task này

Không đổi dữ liệu.

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE

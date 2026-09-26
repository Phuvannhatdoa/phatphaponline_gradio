# B1 — Build 1 Already Exists (conformance pointer)

> **T132 P6 §15** | Tạo: 2026-09-22 | Loại: conformance thin (pointer)  
> Tránh duplicate với BUILD1_AUDIT.md — file này chỉ làm pointer.

---

## Mục đích

Spec B2.5 §15 yêu cầu "B1_ALREADY_EXISTS". Nội dung đã có trong:

- **`docs/BUILD1_AUDIT.md`** — audit thực tế Build 1 (2026-08-11), danh sách module/endpoint đã có
- **`docs/build1_frozen_contract.md`** — hợp đồng đóng băng Build 1 (không tự đổi schema)
- **`docs/build1_inventory.md`** — inventory full (tables, routes, files)

---

## Tóm tắt Build 1 (từ audit 2026-08-11)

| Module | Thực tế | Nguồn tin |
|--------|---------|-----------|
| Place Authority (DILA) | ~85% — 59,167 rows, 67% tên Việt | BUILD1_AUDIT §3 |
| Person Authority | ~40% — 48,673 rows, name_vi/bio = 0% | BUILD1_AUDIT §4 |
| GIS Map | ~70% | BUILD1_AUDIT §5 |
| Nexus / Evidence Graph | entity_claims 447,885 rows | BUILD1_AUDIT §8 |
| Source Registry | data_sources 14 rows × 40+ cột | T70/T77/T78 |

> **Lưu ý**: README.md cũ ghi "~99%" — sai. Tin BUILD1_AUDIT §3.

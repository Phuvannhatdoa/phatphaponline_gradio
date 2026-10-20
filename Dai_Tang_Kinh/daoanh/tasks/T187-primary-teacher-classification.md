---
id: T187-primary-teacher-classification
title: "T187 — Phân loại thầy truyền pháp ấn vs thầy tham học (lineage_primary_teacher)"
module: Lineage / Data Pipeline
priority: high
status: done
owner: claudecode
depends_on: [T185-ttl-full-import, T186-ttl-persons-vn-lineage]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28"
plan_approved_at: "2026-09-28 (Admin: 'Đồng ý build T187')"
done_when: |
  Bảng lineage_primary_teacher tồn tại với 23440 rows;
  Linh Huấn→Tuyết Phong is_primary=-1 (Marcus ref 來謁 = tham học);
  Đức Sơn→Tuyết Phong is_primary=1 (TTL xác nhận);
  ancestor_spine Tuyết Phong trace đúng: Đức Sơn→Long Đàm Sùng Tín→Thạch Đầu→Thanh Nguyên;
  root_ancestor BFS lọc bỏ early_study edges;
  syntax app.py OK.
---

## Vấn đề

DILA và Marcus không phân biệt "thầy truyền pháp ấn" (dharma transmission) vs "thầy tham học"
(visited/studied with) — cả hai đều là `teacher_of`. Hệ quả: `ancestor_spine` có thể trace
ngược theo đường sai tông phái (ví dụ: Tuyết Phong đi theo Linh Huấn → dòng Mã Tổ,
thay vì Đức Sơn → dòng Thạch Đầu đúng).

## Giải pháp: 2 nguồn kết hợp

**Nguồn 1 — TTL (Truyền Đăng Lục VN)**:
Tài liệu sưu tầm từ Truyền Đăng Lục VN chỉ ghi thầy truyền pháp thật.
`ttl_asserted=1` = Truyền Đăng Lục VN xác nhận.

**Nguồn 2 — Marcus `ref` text**:
Trích dẫn Hán văn gốc trong `lineage_edge_assertions.ref` — parse từ khóa:
- `嗣法, 法嗣, 得法, 印可, 付法...` → dharma_transmission
- `來謁, 禮謁, 往謁, 問法, 受業...` → early_study

## Kết quả

| Metric | Giá trị |
|--------|---------|
| lineage_primary_teacher total | 23,440 |
| is_primary=1 (primary teacher) | 3,793 |
| is_primary=-1 (early_study) | 21 |
| is_primary=0 (fallback/unknown) | 19,626 |
| confidence=high (cả 2 nguồn đồng ý) | 34 |
| confidence=medium (1 nguồn) | 3,780 |
| confidence=low (fallback) | 19,626 |

## Logic phân loại

| TTL | Marcus ref | is_primary | evidence | confidence |
|-----|------------|-----------|----------|------------|
| ✓ | dharma_transmission | 1 | BOTH | high |
| ✓ | early_study | 1 (TTL override) | TTL_OVERRIDE | medium + conflict=1 |
| ✓ | unknown | 1 | TTL | medium |
| ✗ | dharma_transmission | 1 | MARCUS_REF | medium |
| ✗ | early_study | -1 | MARCUS_REF | medium |
| ✗ | unknown | 0 | FALLBACK | low |

## Ví dụ verify

**Tuyết Phong Nghĩa Tồn (A003677):**
- Linh Huấn (A019949): `is_primary=-1` — Marcus ref `來謁` = "đến vái lạy lúc 17 tuổi"
- Đức Sơn Tuyên Giám (A003868): `is_primary=1` — TTL xác nhận
- Spine đúng: Tuyết Phong → Đức Sơn → Long Đàm Sùng Tín → Thạch Đầu Hy Thiên → Thanh Nguyên Hành Tư ✓

## App.py thay đổi

| Hàm | Thay đổi |
|-----|---------|
| `_t158_neighbors_consensus` | LEFT JOIN lineage_primary_teacher; ORDER BY is_primary DESC, ttl_asserted DESC, agreeing_source_count DESC |
| `api_monk_ancestor_spine` | Dùng `_t158_neighbors_consensus` (bỏ `_t86_neighbors`); skip is_primary=-1 |
| `api_monk_root_ancestor` | Dùng `_t158_neighbors_consensus`; filter bỏ is_primary=-1 |

## Rollback

```sql
DROP TABLE IF EXISTS lineage_primary_teacher;
```

Code: `git revert --no-edit cebe7edf0bbc9939e57481badc30fe2206eaec0a`

## Files

- **New:** `scripts/etl_t187_primary_teacher.py`
- **New:** `tasks/T187-primary-teacher-classification.md`
- **Modified:** `app.py` (`_t158_neighbors_consensus`, `ancestor_spine`, `root_ancestor`)
- **Modified DB:** `data/lineage.db` (bảng lineage_primary_teacher)

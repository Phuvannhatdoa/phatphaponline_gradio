# Session — T153 DILA Index unified tab bar (2026-09-17)

> **Code closure — additive · UI-only (HTML/CSS) · 0 DB · 0 ALTER · 0 Schema · 0 API · mirror chuẩn T147/T148.**
> Revert: `git revert --no-edit <sha_T153>` (chỉ 2 file HTML, 0 DB).

---

## 1. Bối cảnh

Hai trang DILA Index (Place T-something, Person T147) điều hướng rời rạc — cần tab bar chung để chuyển nhanh và nhất quán tiêu đề.

## 2. Thay đổi

| File | Nội dung |
|------|----------|
| `admin/dila_index.html` | CSS `.da-tabbar`/`.da-tab`/`.da-tab.active`; `<h1>` "DILA Place Index" → "DILA Index"; thêm tab bar với 📍 Place Index active + 👤 Person Index |
| `admin/dila_person_index.html` | CSS tương tự; bỏ link rời "DILA Place Index" ở breadcrumb; `<h1>` → "DILA Index"; tab 👤 Person Index active |

- Active tab: màu `--da-cyan` + border-bottom.
- Không đụng JS (search/filter/pagination/export/CSV/JSON giữ nguyên).

## 3. Trụ SSOT

| Trụ SSOT | File | Trạng thái |
|----------|------|-----------|
| Canonical task | `tasks/T153-dila-index-unified-tabbar.md` | **1 unique** ✓ |
| Canonical session | `docs/sessions/2026-09-17_t153-dila-index-unified-tabbar.md` | **1 unique** ✓ (file này) |
| tasktodo row | `docs/tasktodo.md` T153 | **DONE** ✓ |
| ROLLBACK row | `docs/ROLLBACK.md` T153 | hash-fill real 2-pass |
| Dashboard | `data/progress_data.json` | regen real `build_progress_data.py` ✓ |
| Leftover | scripts/ `*t153*` | **0** ✓ |

## 4. Verify

- Pipeline (lint/test/e2e) PASS — HTML/CSS thuần.
- 0 ảnh hưởng API/DB.

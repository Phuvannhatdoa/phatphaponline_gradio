# Session — T154 agents/README refresh (2026-09-17)

> **Docs closure — additive · 0 code · 0 DB · 0 ALTER · 0 Schema · 0 API · mirror chuẩn T150/T151.**
> Revert: `git revert --no-edit <sha_T154>` (chỉ `Dai_Tang_Kinh/agents/README.md`).

---

## 1. Bối cảnh

`agents/README.md` tồn đọng chuỗi version-history lỗi thời (v2.2 → v8.1, 2026-04), không còn phản ánh hệ thống hiện tại.

## 2. Thay đổi

- Viết lại README theo kiến trúc hiện tại (~57 dòng):
  - **Máy chủ:** Auth Gateway `server.py:5001` · Main Server `app.py:5000` · Local Gateway `local_gateway.py:8080`.
  - **Tính năng:** Đạo Ảnh Mapping · TTL Ontology · Nhân Vật Học Portal (T51) · CBETA Content (T53) · CBETA Analytics (T54).
  - **Công nghệ:** Flask · SQLite (`data/lineage.db`) · GraphDB SPARQL · Tailwind.
  - **Nguyên tắc:** Zero-RAM · bất biến dữ liệu (additive, revertible).
- Xoá version-history cũ. 0 code, 0 DB.

## 3. Trụ SSOT

| Trụ SSOT | File | Trạng thái |
|----------|------|-----------|
| Canonical task | `tasks/T154-agents-readme-refresh.md` | **1 unique** ✓ |
| Canonical session | `docs/sessions/2026-09-17_t154-agents-readme-refresh.md` | **1 unique** ✓ (file này) |
| tasktodo row | `docs/tasktodo.md` T154 | **DONE** ✓ |
| ROLLBACK row | `docs/ROLLBACK.md` T154 | hash-fill real 2-pass |
| Dashboard | `data/progress_data.json` | regen real `build_progress_data.py` ✓ |
| Leftover | scripts/ `*t154*` | **0** ✓ |

## 4. Verify

- Markdown-only; không ảnh hưởng runtime.

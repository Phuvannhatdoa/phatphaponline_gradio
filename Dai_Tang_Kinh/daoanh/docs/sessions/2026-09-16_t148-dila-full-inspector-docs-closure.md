# T148 — DILA Full Inspector — Docs Closure (2026-09-16)

**docs-only, additive, 0 code, 0 DB, 0 API, 0 Schema, 0 ALTER — mirror chuẩn 4-trụ SSOT T146/T147 (2026-09-16):**
canonical task `tasks/T148-dila-full-inspector.md` (1 unique, 0 dup) + canonical session (file này)
+ tasktodo row DONE + ROLLBACK row hash-fill real (2-pass `git rev-parse`, 0 gõ hash tay) + dashboard
regen `data/progress_data.json` (T148 visible, 0 placeholder leftover, 0 leftover temp scripts/session lẫn).

## Bối cảnh / Root cause

Admin cần "full inspector" DILA — trang tra dữ liệu DILA person toàn diện (mirror `dila_person_index.html`),
gom thêm các field extended từ Authority-Databases (bio_extensive, alt_names, active_at, works_tripitaka,
works_by, mentioned_in, authority/viaf...). Phát hiện thêm 2 việc nằm cùng session hạ tầng cũ (file session
`2026-09-16_t148-t149-session.md` đang LẪN 2 task T148+T149 — leftover cần tách): T148 inspector là task
chuẩn; T149 (fix name_zh import bug) sẽ đóng docs riêng sau theo đúng 4-trụ, KHÔNG trộn.

## Additive (docs closure này)

1. **Canonical task** `tasks/T148-dila-full-inspector.md` — mô tả đầy đủ: full inspector page, short-extended
   bio inline fix (T149-dependent name_zh/alt-name), active_at/Nơi hoạt động, authority fields, CSV/JSON export,
   pagination, status translate badge — mirror DILA Person Index nhưng mở rộng extended fields.
2. **Canonical session** file này — 1 task = 1 session (SSOT), 0 leftover.
3. **tasktodo row** T148 DONE (đã tồn tại trên đĩa từ trước — verify SSOT giữ nguyên).
4. **ROLLBACK row** T148 — thêm row additive (placeholder `__T148_HASH_PLACEHOLDER__` → hash-fill 2-pass
   bằng `git rev-parse` real sau commit closure, 0 gõ hash tay).
5. **Dashboard regen** `data/progress_data.json` — chạy `scripts/build_progress_data.py` (SSOT, exit 0),
   json bytes tăng, T148 visible trên dashboard (3-4 hit).

## Verify / Test

- `python -m py_compile app.py` — PASS (DILA endpoint additive).
- Dashboard regen real python exit 0 — `data/progress_data.json` bytes tăng, json T148 = 3-4 hit visible.
- SSOT glob: `tasks/T148-*.md` = 1 unique · ROLLBACK T148 = 1 row (placeholder 0, hash real) ·
  tasktodo T148 = 2 row · session T148 canonical = 1 · `scripts/` + `docs/sessions/` leftover = 0.
- git: 2 commit (closure + hash-fill), log T148 ≥ 3, 0 placeholder token leftover.
- Browser (nếu Admin verify): full inspector load dila persons + extended fields + places.html fix 404.

## Files changed (docs-only)

| File | Loại |
|------|------|
| `tasks/T148-dila-full-inspector.md` | canonical task (đã có trên đĩa, giữ) |
| `docs/sessions/2026-09-16_t148-dila-full-inspector-docs-closure.md` | canonical session (file này) |
| `docs/tasktodo.md` | row T148 (đã có) |
| `docs/ROLLBACK.md` | +1 row T148 (hash-fill real) |
| `data/progress_data.json` | regen (T148 visible) |

## Commit / Revert

- Commits: (1) `docs: T148 ... docs closure (additive docs)` — placeholder hash;
  (2) `docs: T148 hash-fill ROLLBACK row placeholder -> real <sha>` (2-pass SSOT real).
- Revert: `git revert --no-edit <real-sha>` (xem row ROLLBACK).
- Remaining KHÔNG-T148 đã để nguyên: `app.py`, `admin/index.html`, `places.html`, BUG-012, T149 (xử lý riêng).

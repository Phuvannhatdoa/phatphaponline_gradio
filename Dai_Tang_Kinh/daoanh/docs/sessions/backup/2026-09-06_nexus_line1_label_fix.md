# Session Log — 2026-09-06 — NEXUS Line-1 Label Việt (NEXUS-LBL-001)

**Task:** Debug tab 🔥 NEXUS — node Line 1 chưa hiển thị tên tiếng Việt (root PL000000023255 Thiếu Lâm Tự)
**Status:** ✅ Done — audit trước (JSON), admin duyệt, fix + test + commit.

---

## Audit (trước khi sửa — đã báo JSON)

- Query DB thật (`data/lineage.db`): `people.name_vi` **100% filled** (48.673/48.673 so với docs ghi 0% — lỗi thời),
  `marcus_reference.label_vi` 18.127 filled, `namevi_map_places` 118.296 rows (có `Thiếu Lâm Tự`).
- Place root PL000000023255: center OK, 24/24 person node đã Việt, 0 label rỗng, aliases 5, groups 3/24.
- **Root cause xác minh = lớp resolver**: nhánh Line-1 Marcus (person root) `_add_node(oid, olbl, olbl, 'person')`
  chạy sau vòng fill nên label = Hán thô `teacher_label`/`student_label`; API thiếu kênh `label_vi`.

## Phát hiện phụ (quan trọng)

- Commit T99 `639d4a4` **vô tình revert ViQaReadability v1+v2** (places.html Q/A + 2 docs):
  session T99 gán `de59542` = "inspector TÊN HIỂN THỊ VIỆT" và commit từ stage/snapshot cũ
  (quirk backup agent). Worktree trên disk không mất (blob `4dd7cf4`), chỉ bay khỏi HEAD.
  → Đã **khôi phục** trong commit A (tasktodo HEAD vẫn ghi "ViQaReadability Done").

## Fix (commit B — NEXUS-LBL-001)

1. `app.py` `api_nexus`: `_add_node` thêm `label_vi`; center person/place thêm `label_vi`;
   vòng fill person/place ghi `label_vi`; nhánh marcus Line-1 lookup Việt
   (`people.name_vi` → `marcus_reference.label_vi`), `label_zh` giữ Hán gốc,
   node thiếu row giữ label gốc (không AI, không sửa nguồn).
2. `places.html`: `_nexusSafeLabel(n)` = `label_vi || label || label_zh || id` (không rỗng);
   thay 7 điểm fallback + header `nmp-name-vi` nhận `label_vi` thật.
3. Docs: report + session + tasktodo + progress + naming-and-identity.md (sửa 0% → 100%) + ROLLBACK.

## Verify

- `python -m py_compile app.py` ✅
- Flask test_client (DB thật, read-only): place root 10/10, person root Marcus 8/8, ALL PASS ✅
- Mẫu Line-1 sau fix: `A001897 → label_vi='Bách Trượng Hải' (label_zh='懷海')`,
  `A012760 → 'Vân Tú Thần Giám' (釋神鑒)`, `A010505 → 'Hoa Nghiêm Trí Nham'`.
- `node --check` inline script (357.248 chars) OK · E2E ✅ · `npm test` ✅.

## Commits

- Commit A — restore ViQaReadability v1+v2 (bị T99 revert vô tình): places.html (blob `4dd7cf4`),
  `docs/vi_qa_readability_REPORT.md`, `docs/sessions/2026-09-06_vi_qa_readability.md`, `docs/progress.md`.
- Commit B — NEXUS-LBL-001: `app.py`, `places.html`, report, session, tasktodo, progress, naming-and-identity, ROLLBACK.

## Rollback

- `git revert <commitB>` → bỏ fix Nexus (ViQa giữ nguyên); `git revert <commitA>` → về trạng thái T99.
- Không đụng DB/raw nguồn.
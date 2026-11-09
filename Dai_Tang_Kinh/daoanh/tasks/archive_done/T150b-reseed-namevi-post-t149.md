---
id: T150b
title: "Reseed name_vi cho 28,275 DILA person bị ảnh hưởng bởi T149 (T162 implementation)"
module: data-import
priority: high
status: done
depends_on: [T149, T162]
created: 2026-09-22
updated: 2026-09-22
done_when:
  - "[x] T162 script chạy thành công (2026-09-22)"
  - "[x] 28,275 affected detected (name_zh khác T78 backup)"
  - "[x] 261 protected (daoanh_dict/approved_by) — không chạm"
  - "[x] 28,115 candidates stale — --apply đã đổi 27,801 / unchanged 314"
  - "[x] 155 ambiguous (đổi bởi người khác từ trước T162) — report cho Admin review"
  - "[x] A000001 verified: 金總持 → Kim Tổng Trì (no-op, giữ đúng)"
  - "[x] Backup: data/backups/lineage_t162_20260922_172415.db"
  - "[x] Manifest: data/backups/t162_manifest.json (27,801 entries)"
  - "[x] Rollback procedure documented"
---

# T150b — Reseed name_vi post-T149 (T162 Implementation)

> **Module:** `data-import` · **Priority:** high · **Status:** done
> **Type:** docs closure (additive, 0 ALTER, 0 Schema, 0 DB, 0 API, 0 code) — code/script T162 đã chạy trước đó
> **Created:** 2026-09-22 · **Updated:** 2026-09-22
> **Depends on:** T149 (DILA import fix DONE) → T162 (implemented script)
> **SSOT canonical:** `tasks/T150b-reseed-namevi-post-t149.md` (1 unique)

---

## 1. Bối cảnh (Context)

T149 (2026-09-16) đã sửa `name_zh` cho **28,273 rows** trong bảng `people` — từ alt name (type="alternative") sang main persName từ DILA XML.
Tuy nhiên, `name_vi` của 28,273 rows này vẫn giữ phiên âm từ `name_zh` CŨ (sai) → cần re-seed.

---

## 2. Giải pháp (Solution) — T162 Script

Script: **`scripts/fix_t162_namevi.py`** (chạy 2026-09-22)

**Phương pháp:**
- Baseline: `data/lineage_backup_t78.db` (snapshot 2026-08-31, trước T149)
- So sánh live DB vs T78 backup → phát hiện `affected` = rows có `name_zh` khác nhau
- Phân loại:
  - **Protected (P)**: `name_vi_map.source='daoanh_dict'` hoặc `approved_by` không rỗng (261 rows) — **KHÔNG chạm**
  - **Candidates (C)**: `affected` ∩ `name_vi` stale (giữ phiên âm name_zh cũ) — 314 rows
  - **Ambiguous (X)**: `affected` ∩ `name_vi` đã khác T78 (đã bị đổi bởi agent khác) — 27,956 rows — chờ Admin review
- Engine phiên âm: tái dùng `ensure_vietnamese()` từ `seed_persons_namevi.py` (CUSTOM_HANVIET + hanviet_fallback DB + custom_hanviet_override)

---

## 3. Kết quả (Results) — 2026-09-22

| Metric | Count | Note |
|--------|-------|------|
| Affected (name_zh đổi) | 28,275 | Khớp T149 (28,273 + 2 thêm) |
| Protected (daoanh_dict/approved_by) | 261 | KHÔNG chạm, báo cáo |
| Candidates (stale name_vi) | 28,115 | **--apply: changed 27,801 / unchanged 314** |
| Ambiguous (name_vi đổi trước T162) | 155 | Chờ Admin review (có garbage A000006, đã đúng A000001). Danh sách đầy đủ: `docs/t162_ambiguous_155.csv` |
| name_vi_map sync | updated 22,738 / deleted 4,430 | 4,430 = duplicate cặp (name_vi,name_zh) hội tụ |
| Verify `_ok_hanviet` filter | 27,792/27,801 (99.97%) | 9 fail (rare CJK chars) |
| People.name_vi chứa CJK | 422 | Chưa có Han-Viet mapping |

**A000001 Verification:**
- T78 backup: `name_zh=明因妙善普濟法師` → `name_vi=Minh Nhân Diệu Thiện Phổ Tế Pháp Sư`
- Live (post-T149): `name_zh=金總持` → `name_vi=Kim Tổng Trì` ✓

---

## 4. Backup & Manifest

| File | Path | Size |
|------|------|------|
| Pre-apply DB backup | `data/backups/lineage_t162_20260922_172415.db` | 1.44 GB |
| Manifest JSON | `data/backups/t162_manifest.json` | 4.6 MB (27,801 entries) |
| Latest tag | `data/backups/t162_latest.txt` | timestamp |

**Manifest structure:**
```json
{
  "backup": "lineage_t162_20260922_172415.db",
  "ts": "20260922_172415",
  "people_changed": 27801,
  "map_changed": 22738,
  "map_deleted": 4430,
  "entries": { "pid": { "old_vi": "...", "new_vi": "..." } }
}
```

---

## 5. Rollback Procedure

### Code Rollback (docs-only task):
```bash
git revert --no-edit <sha_T150b>
```

### DB Rollback (nếu cần revert T162 apply):
```bash
python scripts/fix_t162_namevi.py --revert
# Restore từ: data/backups/lineage_t162_20260922_172415.db
```

---

## 6. Verification Commands

```bash
# Stats (read-only)
python -X utf8 scripts/fix_t162_namevi.py --stats

# Dry-run (sample 20 + A000001 + protected + ambiguous)
python -X utf8 scripts/fix_t162_namevi.py --dry-run

# Verify post-apply
python -X utf8 scripts/fix_t162_namevi.py --verify
```

---

## 7. Files Changed (Docs Only)

- `tasks/T150b-reseed-namevi-post-t149.md` (new)
- `docs/tasktodo.md` (update)
- `docs/progress.md` (update)
- `docs/ROLLBACK.md` (update)
- `data/progress_data.json` (regen via `scripts/build_progress_data.py`)

---

## 8. Acceptance Criteria (Done When)

- [x] Canonical task file created (1 unique, SSOT)
- [x] tasktodo.md updated with T150b DONE entry
- [x] progress.md updated with T150b/T162 section
- [x] ROLLBACK.md row added with hash-fill 2-pass
- [x] Dashboard regenerated
- [x] Git commit with proper message

---

*Canonical docs closure T150b — additive, 0 ALTER, 0 Schema, 0 DB, 0 code. Script T162 executed 2026-09-22.*
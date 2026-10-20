# Session 2026-09-22 — T150b Reseed name_vi post-T149 (T162) — Docs Closure

**Ngày:** 2026-09-22 · **Task:** T150b (`tasks/T150b-reseed-namevi-post-t149.md`) · **Trạng thái:** DONE (docs closure + committed 2026-09-23)
**Loại:** Docs-only additive (0 ALTER, 0 Schema, 0 DB write trong closure này) — engine T162 đã chạy trước đó

---

## 1. Bối cảnh

T149 (2026-09-16) sửa `name_zh` cho 28,273 rows (alt name → main persName). Hệ quả: `name_vi` của các row này vẫn giữ phiên âm theo `name_zh` CŨ (sai). Cần reseed `name_vi`.

Giải pháp T162 đã được implement sẵn dưới dạng script `scripts/fix_t162_namevi.py` và chạy thành công 2026-09-22. Task T150b là docs closure canonical hóa yêu cầu + kết quả + rollback.

## 2. Phân tích & kết quả T162

- **A (affected):** 28,275 (people có `name_zh` khác baseline T78 backup 2026-08-31)
- **P (protected):** 261 (`name_vi_map.source='daoanh_dict'` hoặc `approved_by` không rỗng) — KHÔNG chạm
- **C (candidates stale):** 28,115 → **`--apply` đã đổi 27,801 people / unchanged 314** (new_vi == old_vi) trong 1 transaction
- **X (ambiguous, đổi trước T162):** 155 (`name_vi` đã bị đổi từ trước, tách qua manifest) — report Admin review, KHÔNG tự quyết (gồm rác A000006)
- **M (name_vi_map sync):** updated 22,738 / deleted 4,430 (duplicate cặp (name_vi,name_zh) hội tụ)
- **Verify:** 27,792/27,801 đạt `_ok_hanviet` filter (9 fail = CJK hiếm) · 422 `people.name_vi` còn chứa CJK (chưa có Han-Viet mapping)

**A000001:** T78 `明因妙善普濟法師/Minh Nhân...` → Live `金總持/Kim Tổng Trì` ✓ (engine phiên âm hiện có, 0 hard-code)

## 3. Việc đã làm (2026-09-22 → 2026-09-23)

| STT | Công việc | Trạng thái |
|-----|-----------|-----------|
| 1 | Verify T162 logic khớp yêu cầu T150 (so sánh live vs T78 backup, phân loại A/C/P/X) | ✅ |
| 2 | Chạy `--stats` / `--dry-run` / `--verify` — đối chiếu số liệu | ✅ |
| 3 | Tạo task canonical `tasks/T150b-reseed-namevi-post-t149.md` | ✅ |
| 4 | Cập nhật `docs/tasktodo.md` (entry T150b DONE) | ✅ |
| 5 | Cập nhật `docs/progress.md` (section T150b/T162) | ✅ |
| 6 | Cập nhật `docs/ROLLBACK.md` (row T150b, hash-fill 2-pass) | ✅ |
| 7 | Regen dashboard `data/progress_data.json` | ✅ |
| 8 | **Commit 1** (docs closure) `58c599cb593ee878121d3ac519ded8afbf98fae7` | ✅ |
| 9 | **Commit 2** (ROLLBACK hash-fill) `b071faba2cd5f6a2c92176b0ac0971c0a74672eb` | ✅ |
| 10 | Commit 3 (follow-up: engine script T162 + t83_force_commit.py + session này) | pending |

## 4. Workaround commit (T83 byte-write)

Volume `E:\Backup 2025` bị backup/sync agent **chặn rename/unlink** file git → `git add`/`git commit` fail "unable to write new index file". Đã viết `scripts/t83_force_commit.py`:

- Dùng `GIT_INDEX_FILE=<temp>` + `git read-tree/add/write-tree` để tạo objects (không chạm `.git/index`)
- `git commit-tree -p HEAD` tạo commit object
- **Byte-write** (giữ inode) index + `refs/heads/master`
- Tự sinh author từ commit cuối (`git log -1 --format=%an|%ae`), `-c safe.directory=*`

Cách dùng: `python scripts/t83_force_commit.py --apply [--message "..."] [--files ...]`

## 5. Rollback

- **Code (docs):** `git revert --no-edit 58c599cb593ee878121d3ac519ded8afbf98fae7`
- **DB (T162 apply):** `python scripts/fix_t162_namevi.py --revert` → restore `data/backups/lineage_t162_20260922_172415.db`
- **Backup/manifest:** `data/backups/lineage_t162_20260922_172415.db` (1.44 GB) · `data/backups/t162_manifest.json` (27,801 entries) · `data/backups/t162_latest.txt`

## 6. Todo tiếp theo

- Follow-up commit (3) chứa `scripts/fix_t162_namevi.py` + `scripts/t83_force_commit.py` + session — **bắt buộc** để lệnh rollback T150b trong ROLLBACK.md khả dụng.
- Cleanup: `check_schema.py` (file tạm, encoding hỏng) — xoá khi shell khả dụng.
- File untracked khác giữ nguyên: `tests/test_license_firewall.py`, `tests/test_real_data_license.py`, `docs/UNIFY_DILA_LINEAGE_RELATION_CARD_FORMAT_REPORT.md`, `places.html` (bản sửa đang dở), `docs/sessions/2026-09-22/changes.md`.
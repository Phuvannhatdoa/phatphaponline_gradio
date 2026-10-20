# Session 2026-09-27 — T184: T169 SPEC verify fixes (docs-only)

## Tổng quan
- **Task:** `tasks/T184-t169-spec-verify-fixes.md`
- **Admin:** "Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done"
- **Phạm vi:** docs-only, 0 code, 0 DB — sửa additive tại chỗ SPEC `X-T169-groq-place-verify-pipeline-SPEC.md`.
- **Repo root:** SSOT `visjs-app` (guard PASS).

## Bối cảnh
SPEC T169 (docs-only, chưa build) được review 2026-09-27 đối chiếu DB thật `data/lineage.db` + codebase
→ phát hiện **7 điểm logic chưa đúng** (G1–G7). Admin phê chuẩn đề xuất sửa (3 điểm chốt:
P1 cursor-memory, P4 recompute `name_vi_norm`, P3 trụ đa âm static).

## Verify DB thật (read-only) — cơ sở các sửa
| Khoản | Giá trị verify | Kết luận |
|-------|----------------|----------|
| `places_dila` | 59.167 row · id `PL000000000001` · 0 dup | ✓ |
| `places_pending` | 176.783 · id NULL **58.455**/176.783 · 0 dup id non-null | ✓ P0-4 |
| JOIN `p.id=d.id` | **59.167** (mọi dila row match) · +zh valid **59.150** | ✓ |
| dict đủ | 0 row JOIN có `name_vi` NULL | ✓ |
| `namevi_map_places` | 118.296 · `dila_id` UNIQUE · match dila spine **59.150** · legacy 59.146 · `needs_review=1` **18.165** · 0 row dila_id NULL | nền G6 |
| model | `qwen/qwen3.8-27b` = app.py:16959 (chuẩn repo) | ✓ P0-6 |

## Việc đã làm (8 sửa SPEC + docs)

### 1. `docs/Mimo-Flash/X-T169-groq-place-verify-pipeline-SPEC.md`
| # | Vị trí | Sửa |
|---|--------|-----|
| G1 | §2.2 | SQL → predicate + `:cursor` memory (ORDER BY id LIMIT 25); bỏ persist `id>last` (MAX(id) sẽ bỏ sót retry api_error); restart scan lại qua predicate |
| G2 | §2.2 ước | 59.150/25 = **2.366 batch** (không 2.367) · budget ~2,4k (+4%) |
| G3 | §5 | RPM adaptive: `x-ratelimit-remaining` ≤5 → sleep 3s; còn lại 2,2s (~27 RPM < 30) |
| G4 | §2.2 + §5.6 | `--force` vẫn giữ `NOT IN (verified, approved_dict)` — không ghi đè hàng đã duyệt; conflict/api_error/pending retried |
| G5 | §3 P1-1 | Thứ tự ưu tiên cố định POLYPHONIC→TAXONOMY→PHONETIC→NONE, dừng nhãn đầu, không ghép; trụ đa âm = static map inline (0 bảng mới) |
| G6 | §6 PUT | 3 bước 1 transaction: audit (verified/approved_dict, needs_review=0) + `places_pending.name_vi` + **recompute `name_vi_norm`** (reuse `scripts/migrate_name_vi_norm.py`) + `namevi_map_places.name_vi` (UPSERT) |
| G7 | §7 UI | Filter `needs_review=1 AND diff_type IS NOT NULL AND review_status='conflict'` + tab "Lỗi API" (`api_error`) + tab "Đã duyệt" |
| — | frontmatter | `updated: 2026-09-27` + banner T184 + §0 note + §8 acceptance item 4/6/7 |

### 2. Docs
- `tasks/T184-t169-spec-verify-fixes.md` (mới, frontmatter đầy đủ, status done).
- `docs/tasktodo.md`: row T184 (DONE) chèn đầu list ACTIVE trước T181.
- `docs/ROLLBACK.md`: row T184 kèm revert path.
- `docs/Mimo-Flash/X-T169-groq-place-verify-pipeline.md`: pointer `updated: 2026-09-27` + bullet T184.

### 3. Dashboard
- `python scripts/build_progress_data.py` → `data/progress_data.json` regen chứa T184.

## Verify
- `npm run guard` PASS (SSOT repo-root).
- `py_compile` không áp dụng (docs-only); frontmatter task T184 parse được.
- `npm run pipeline` chạy trước khi báo Admin (phe test/e2e — không đụng docs).

## Revert
- **1 lệnh:** `git revert --no-edit 3c4907e5d5823b31b20932b816de1ba79184d267` (docs-only) — khôi phục SPEC X-T169 cũ + pointer + docs.
- Cấm `cp *.bak` · cấm `reset --hard`.

## Ghi chú concurrency
- Không đụng `app.py` (WIP agent khác vùng `t181_cbeta_catalog`); không ALTER DB; `places_missing_info` giữ nguyên.
- T183 đã được dùng (lazy-fetch fallback, app.py:9511) → task mới mang số **T184**.
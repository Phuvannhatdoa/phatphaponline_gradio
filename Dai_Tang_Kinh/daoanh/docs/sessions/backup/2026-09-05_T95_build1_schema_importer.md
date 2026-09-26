# Session 2026-09-05 — T95 Build 1: Schema (Phase B) + Importer text_passages (Phase A3)

**Task:** T95 — CBETA Pipeline dịch Hán–Việt theo từng passage
**Ngày:** 2026-09-05 (Tiếp nối session `2026-09-05_T95_task_approved.md`)
**Admin:** Đồng ý build (yêu cầu: lưu logs, git commit, update .md files, bảo đảm rollback về version trước)

## Mục tiêu
Chạy BUILD 1: (1) Phase B — mở rộng schema additive + tạo bảng job; (2) Phase A3 —
importer `text_passages` cho pilot T50n2060, id/hash/anchor ổn định, idempotent.

## Đã thực hiện

### Phase B — `scripts/t95_schema_migrate.py` (mới)
- Content (additive, không đụng data cũ):
  - Tạo mới `translation_jobs` (job_id, work_id, requested_scope, requested_by_user_id,
    provider, model_name, status queued/pending…, next_passage_sequence, total/completed/failed,
    started/finished_at, last_error) và `translation_job_items`
    (job_item_id, job_id FK, passage_id, sequence_no, status, attempt_count,
    provider_request_id, raw_response_path, error_message, started/completed_at, UNIQUE(job_id, passage_id)).
  - Thêm 15 cột additive trên 3 bảng T94 (trống): `text_passages` {source_status,
    loc_ref, canonical_start_anchor, canonical_end_anchor, legacy_passage_id, updated_at};
    `translation_segments` {passage_id, provider, source_original_hash, quality_status,
    created_by_job_id, revision_no, supersedes_translation_id};
    `passage_translation_alignment` {updated_at}.
  - 6 index: text_passages(work_id, sequence_no), translation_segments(passage_id),
    translation_segments(translation_status, quality_status), alignment(passage_id),
    translation_jobs(work_id, status), translation_job_items(job_id).
- Ghi chú kỹ thuật: SQLite không cho `ADD COLUMN ... NOT NULL` không có default →
  `passage_id TEXT DEFAULT ''`, NOT NULL enforce tầng ứng dụng. `translation_status`
  giữ DEFAULT 'draft' (cột T94), 'draft' ≙ 'pending' tại ứng dụng.
- Backup: `data/lineage.db.backup_t95_20260905_085228` (1.241 MB).
- Verify: `--verify` → 16/16 ✅ (tables + cột + SQLite 3.50.4 → DROP COLUMN OK).
- Rollback: `python scripts/t95_schema_migrate.py --revert`  (hoặc restore backup).

### Phase A3 — `scripts/cbeta_build_text_passages.py` (mới)
- Tách legacy `passage` (work T50n2060, 1.037 mục) thành **đoạn con ổn định**:
  ranh giới dấu câu `。；！？`, gom tới ~50 ký tự, đuôi < 25 ký tự gộp vào đoạn trước.
  Deterministic (cùng input → cùng output).
- ID: `daoanh:cbeta:<work>:<loc_key>:p<seq:04d>`; loc_key = page từ loc_ref
  (`0-0484c-` → `0484c`, `0--` → `nopage`); page trùng → disambiguate ordinal
  (`0484c-0002`); nopage luôn `nopage-<ordinal>`. Thứ tự ổn định theo passage_id.
- Hash: sha256 của raw bỏ whitespace (`raw_zh_hash` trên cả text_passages lẫn legacy passage).
- Legend `text_passages`: source_status='ok', loc_ref/canonical anchors cấp page,
  legacy_passage_id trỏ lại, sequence_no toàn bộ, source_version='legacy:pipeline:v1'.
- Zero-RAM: duyệt generator theo từng mục, không nạp toàn bộ raw text.
- Idempotent: INSERT OR REPLACE khi hash đổi + con tơ skip khi hash giống; **Reconcile**
  xóa passage_id cũ không còn sinh ra (đã xóa 94 orphan sau khi đổi min_seg 15→25).
- Kết quả (--stats / --verify):
  - **9.316 text_passages** cho T50n2060, trung bình 51,6 chữ, min/median/max = 5/54/120.
  - Ca test passage 4061 `0-0484c-` → **9 đoạn p0001–p0009** (56,55,56,55,52,61,56,50,67 chữ)
    — khớp bằng chứng audit + spec (đoạn con ổn định).
  - Backfill 1.037 legacy passage: `raw_zh_hash` + `segmentation_method='punctuation_fallback'`.
  - Verify PASS: 9.316 = distinct passage_id, 0 dup, 0 empty.
- Lệnh chạy:
  - `python scripts/cbeta_build_text_passages.py --dry-run`
  - `python scripts/cbeta_build_text_passages.py --apply [--no-backup] [--skip-backfill]`
  - `python scripts/cbeta_build_text_passages.py --verify|--stats|--revert`
- Rollback: `python scripts/cbeta_build_text_passages.py --revert` (xóa rows run gần nhất,
  rows giữ run cũ được giữ) — hoặc restore `lineage.db.backup_t95_20260905_085228`.

## Số liệu cốt lõi
- text_passages T50n2060: 9.316 (id daoanh:cbeta:T50n2060:<loc>:p####).
- Bare sự thật passage 4061: 9 đoạn; tổng cả corpus 9.316 tương đương dry-run đầu (9.410)
  sau reconcile 94 orphan → khớp hoàn toàn.

## Kế tiếp (Phase C/D/E)
1. **Phase C**: CLI worker `scripts/cbeta_translate_worker.py` + thread trong `app.py`
   (batch 1–5 passage + context hàng xóm, JSON contract, validation gate, commit per passage
   vào `translation_segments` + `passage_translation_alignment`, retry/backoff, resume đa
   session lock work_id+language, không dịch lại validated/reviewed, hash đổi → superseded).
2. **Phase D**: UI song ngữ cặp cố định + 6 badge trạng thái + progress X/Y từ DB.
3. **Phase E**: export tích lũy + admin monitor + 18 tests + manual verify.
4. Commit BUILD 1 sau khi verify xong.

## Files
- Mới: `scripts/t95_schema_migrate.py`, `scripts/cbeta_build_text_passages.py`,
  `docs/sessions/2026-09-05_T95_build1_schema_importer.md`.
- Sửa: `docs/tasktodo.md` (T95 label + BUILD 1 DONE), `docs/progress.md` (entry T95).
- Data: `data/lineage.db` (schema + 9.316 text_passages + backfill), backup
  `data/lineage.db.backup_t95_20260905_085228`.
- Rollback: `git revert` (docs) / `--revert` (scripts) / restore backup (DB).

## Git
- Commit (dự kiến): `feat(T95): Phase B schema + Phase A3 importer text_passages (9.316 units) + docs`
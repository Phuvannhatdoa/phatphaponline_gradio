# Session 2026-09-05 — T95 Build 2: Groq Worker (Phase C) + endpoints + mock E2E

**Task:** T95 — CBETA Pipeline dịch Hán–Việt theo từng passage
**Ngày:** 2026-09-05 (Tiếp nối `2026-09-05_T95_build1_schema_importer.md`)
**Trạng thái:** Phase C DONE (mock test pass) — chưa commit

## Mục tiêu
- Viết Groq worker theo kiến trúc T95: batch dịch, JSON contract, validation gate, commit per passage, resume (không dịch lại), superseded khi hash nguồn đổi, retry/backoff, audit raw request/response.
- Tích hợp vào `app.py`: tạo job qua API + daemon thread chạy worker.
- Bỏ literal Groq key khỏi mã nguồn (bảo mật).

## Build đã làm

### 1. `scripts/cbeta_translate_worker.py` (module độc lập, KHÔNG import app.py)
- CLI commands: `new-job`, `run [--mock] [--limit N]`, `status`, `check-key`, `revert-job <--job id>`.
- Scope: `all` | `untranslated` | `page:<loc_ref>` | `legacy:<passage_id>` | `n:<count>` | `ids:<csv>` (mặc định `untranslated`).
- Batch: tối đa 3 item theo `sequence_no` (job_item.sequence_no = ROW_NUMBER theo thứ tự text_passages).
- Mỗi batch kèm **context hàng xóm read-only** (1-2 đoạn trước/sau cùng page).
- JSON contract + **validation gate**: `translation_vi` rỗng → reject; echo nguyên văn → reject; tỉ lệ ký tự 0.6–4.0 (không trim space/khoảng duy nhất).
- Commit per passage: `translation_segments` (`translation_id = cbeta:<work>:t<seq:06d>:r<rev:03d>`, `translation_status='completed'`, `quality_status='unreviewed'`, `revision_no`, `source_original_hash`, `created_by_job_id`, `supersedes_translation_id`, `model`, `prompt_version='t95-batch-cbeta-v1'`, temp 0.1) + `passage_translation_alignment` (`segment_full`, confidence 1.0, method `batch_json_match`) + **raw audit** `data/raw_responses/<job_id>/<item>.json`.
- Resume/lock: statuses FINAL (`completed`/`needs_review`/`reviewed`) cùng hash → `already_translated` (skip, không tốn API); hash khác bản FINAL → `superseded` cũ + `revision_no+1`, `supersedes_translation_id` trỏ bản cũ; `error/retry/paused` → thử lại.
- Retry/backoff: 2s/4s/8s, tối đa 3 lần.
- Key: env `GROQ_API_KEY` → `groq_key` trong `data/llm_config.json` → nếu thiếu trả `key_error` + ghi `status='key_error'` + message tiếng Việt hướng dẫn; `check-key` báo trạng thái.

### 2. `data/glossaries/vi-buddhist.json` (seed 13 thuật ngữ)
- Style-lock: 13 cặp Hán–Việt (Phật pháp cơ bản) nhắc trong prompt mỗi batch.

### 3. `app.py`
- **Bỏ literal Groq key** (GROQ_LOCAL) → `os.environ.get('GROQ_API_KEY')`; model mặc định `qwen/qwen3.8-27b` (env `GROQ_MODEL`).
- `_t73_call_gemini`: thêm guard `if not key` → trả `key_error` đúng contract.
- 2 endpoint T95 (cuối file):
  - `POST /daoanh/api/translation/jobs` — tạo job (tốt nghiệp như CLI) + nếu `run_now` chạy daemon thread `worker_run` (lazy import `scripts.cbeta_translate_worker` qua importlib).
  - `GET /daoanh/api/translation/jobs` — list job.
  - `GET /daoanh/api/translation/jobs/<job_id>` — detail + counts + items.

### 4. Schema bổ sung (`scripts/t95_schema_migrate.py` re-run idempotent)
- Thêm `translation_job_items.created_at` (mock test phát hiện thiếu) — backup `data/lineage.db.backup_t95_20260905_091543`.

### 5. Fix importer (`scripts/cbeta_build_text_passages.py`)
- **Renumber thứ tự toàn bộ** mỗi khi re-run: trước đó rows không đổi giữ nguyên sequence_no cũ (run 9.410 units) còn rows thay đổi mang số mới → thứ tự lộn xộn (4061: p0009 seq 1955 < p0001 seq 1960). Sau fix: p0001..p0009 = 1947..1955 liền mạch, tổng 9.316 rows.

## Test (mock — không cần key)
1. `run --work-id T50n2060 --scope page:0-0484c- --mock` → job `job-T50n2060-20260905_092038`: 9 item, 3 batch × 3, 9 ✅ committed (t001947..t001955:r001), status completed, failed 0.
2. **Resume**: chạy lại cùng scope → job `_092059`: completed 0 (9 `already_translated`), segments vẫn 9.
3. **Supersede** (giả lập đổi hash qua python): r001 → `superseded`, r002 `completed` + `supersedes_translation_id=r001`.
4. **Revert**: revert 3 job (091653, 091622, 092038, 092059, 092300) → `translation_segments` 0, `passage_translation_alignment` 0, `translation_jobs` 0.
5. **Endpoints**: test client Flask — POST create (9 item queued) 200, GET list 200, GET detail 200; revert dọn sạch.
6. App smoke: `import app` + `view_functions` chứa `api_t95_jobs`/`api_t95_job_detail`; url_map có 2 rule.
7. Worker import OK trong app context; glossary load được.

## Điểm cần admin lưu ý (BẢO MẬT)
- Live Groq translation **cần key**: set env `GROQ_API_KEY` trước khi chạy `app.py`, hoặc thêm `groq_key` vào `data/llm_config.json` (mặc định đọc từ đó). Hiện **chưa có key** → `check-key` báo thiếu; mọi job thật sẽ vào `key_error`/`paused`.
- Mock test đã được dọn: DB sạch (0 translation_segments, 0 job).

## Rollback
- `git revert <sha>` cho docs/scripts; `python scripts/t95_schema_migrate.py --revert`; `python scripts/cbeta_build_text_passages.py --revert`; hoặc restore backup (`data/lineage.db.backup_t95_20260905_085228` / `_091543`).

## Tiếp theo
- **Phase D**: UI song ngữ cặp cố định (render trực tiếp từ `text_passages` + `translation_segments`) + 6 badge trạng thái + progress X/Y từ DB.
- **Phase E**: export tích lũy (chỉ "hoàn chỉnh" khi 100%), admin monitor, 18 tests, manual verify, `npm run pipeline` trước khi review.
# Session 2026-09-05 — T95 Build 4: Phase E — export tích lũy + admin monitor + 18 tests

**Task:** T95 — CBETA Pipeline dịch Hán–Việt theo từng passage (Phase E)
**Ngày:** 2026-09-05 (Tiếp nối `2026-09-05_T95_build3_ui_pairedview.md`)
**Trạng thái:** Phase E DONE (mock pass) — T95 hoàn tất toàn pipeline (§8-§12 DoD), 18/18 test PASS

## 1. Export tích lũy (endpoint mới)
- `GET /daoanh/api/cbeta/works/<work_id>/translation-export`
  - JSON **streaming** (generator `_t95_export_iter`, Zero-RAM theo AGENTS.md): meta (work/title/label/`completed`/counts/generated_at) + `passages[]` theo `sequence_no`.
  - `label`: chỉ `Bản dịch hoàn chỉnh` khi **100%** (`corrupt=0, missing=0, in_progress=0, failed=0, reviewed==translated==total`); ngược lại `Bản dịch tích lũy — X/Y đoạn`.
  - `?format=md` → Markdown bảng (tiêu đề/tác phẩm, nguồn CBETA, Seq/Passage ID/Canonical/Hán/Việt/Trạng thái/Phiên bản); `?download=1` → attachment.
  - **Fix quan trọng:** generator phải sở hữu connection (đóng trong `finally` của generator) — lỗi `Cannot operate on a closed database` nếu đóng ở route.
- Header progress đã có từ Phase D (`/coverage`); export dùng chung `_t95_coverage`.

## 2. Admin translation-job monitor
- Page mới `admin/translation_monitor.html` (dark-amber, tự làm mới 15s): cards tóm tắt (total/running/queued/paused/completed/cancelled/failed-items), bảng job (job_id/work/scope, badge trạng thái, progress bar %, failed+sample error, retries=Σattempt, raw audit count, created/started), nút Chi tiết (items theo job, expand), Resume, Hủy, xem Raw audit, Export T50n2060 JSON/MD.
- Backend `app.py`:
  - `GET /daoanh/api/admin/translation/jobs` — aggregate SQL (done_items, item_total, active, failed, total_attempts, sample_error) + `raw_audit` = số file trong `data/raw_responses/<job>/`.
  - `GET /daoanh/api/admin/translation/jobs/<id>/raw` — danh sách file raw (admin).
  - `POST .../resume` — requeue item `failed/error` (reset attempt, xoá error), status job paused → chạy lại `worker_run` (giữ bản đã dịch bằng cơ chế skip/supersede của worker).
  - `POST .../cancel` — item queued/running → `cancelled` (bản đã dịch giữ nguyên); 404 khi job không tồn tại.

## 3. Fix bug phát hiện trong quá trình test (worker)
- `translation_job_items` **không có cột `updated_at`** — 2 chỗ trong `worker_run` dùng `updated_at=?` khi requeue item (nhánh `tạm fail`) → `sqlite3.OperationalError` (chỉ lộ khi validate fail, mock E2E Phase C không chạm tới). Đã bỏ cột `updated_at` khỏi UPDATE item (job/segment vẫn có `updated_at`, giữ nguyên).
- Job id va chạm khi tạo 2 job trong cùng 1 giây → `UNIQUE constraint failed: translation_jobs.job_id`. Đã thêm microsecond `%f` vào id: `job-{work_id}-{YYYYmmdd_HHMMSS%f}`.

## 4. 18 test bắt buộc (§10) — `scripts/test_t95_18.py` (`npm run test:t95`)
- Chạy trên **bản SAO** `lineage.db` (monkeypatch `DB_PATH` worker+importer → temp), KHÔNG đụng data thật; `npm run test/e2e` vẫn PASS, DB live vẫn 0 job/0 segment sau chạy.
- 18/18 PASS:
  - **Nguồn & phân đoạn (1-3):** page 0-0484c- 9 unit ≤ 67 ký tự không full-text lặp; mọi unit có `raw_zh_hash`+`loc_ref` anchor; re-run importer idempotent (INSERT OR REPLACE, 9316→9316).
  - **Alignment/batch (4-8):** 3 unit → 3 translation_id đúng passage_id; thiếu id → batch không publish (0 translation, item failed); duplicate id → dedup theo id; malformed/truncated → None (không publish); map theo passage_id không theo array index.
  - **Resume/supersede (9-12):** dịch 6/9 dừng → job sau chỉ dịch 3 đoạn cuối (seq 1953-1955), 6 cũ `already_translated`; 2 click cùng lúc → 1 job sở hữu (9 translation, không trùng); passage fail → retry, không đánh completed sai; hash đổi → r001 superseded + r002.
  - **UI (13-18):** paired-view (data-seg + translation_text + badge); không char-ratio split; không còn "Chưa có phần dịch tương ứng."; progress X/Y từ `_coverage`; không hardcode "hoàn chỉnh" (label từ server); mobile `dtMobileTab` + `dtLoadUnits`.
- Bài học test: scope `untranslated` trên toàn work sẽ tạo job 9316 item (≈10 phút mock) → các test resume dùng scope `page:0-0484c-` để route nhanh và đúng-ngữ-cảnh.

## 5. Manual verify T50n2060 · 0-0484c-
- Tài liệu: `docs/cbeta_translation_manual_verify_T50n2060_0484c.md` — 9/9 DoD PASS (mock).
- Live Groq vẫn bị chặn do **chưa set `GROQ_API_KEY`** (hoặc `groq_key` trong `data/llm_config.json`) → `check-key` báo thiếu; bấm Dịch phần còn thiếu sẽ tạo job rồi pause `key_error`.

## 6. Rollback
- `git revert <sha>` (chỉ docs + code); DB không thay đổi (endpoint/test đều vào temp copy hoặc read-only).
- Worker bug-fix đi kèm phase; nếu muốn lùi worker chỉ riêng 2 thay đổi worker: `git checkout <prev> -- scripts/cbeta_translate_worker.py`.

## 7. Tiếp theo / hãy làm thủ công
- Admin set key → chạy live 1 job `page:0-0484c-` để xác nhận chuỗi Groq thật + raw audit.
- Hiệu đinh (`quality_status=validated/reviewed`) để thấy badge `✓ hiệu đinh` + nhãn "Bản dịch hoàn chỉnh" khi đủ 100%.
- `npm run tester:agent` / `npm run pipeline` + review admin trước khi chấp nhận (theo AGENTS.md).

## Commit dự kiến
`feat(T95): Phase E export tích lũy + admin monitor + 18 tests pass + worker fix (updated_at items, job id us) + docs`
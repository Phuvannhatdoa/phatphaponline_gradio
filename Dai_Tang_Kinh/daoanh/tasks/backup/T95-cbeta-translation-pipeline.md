---
id: T95
title: "CBETA Pipeline dịch Hán–Việt theo từng passage (batch + resume + style-lock)"
module: CBETA Core / Translation Pipeline
priority: high
status: in_progress
depends_on: [T50, T85, T94]
created: 2026-09-05
updated: 2026-09-05
done_when: >
  Hán passage có id ổn định daoanh:cbeta:... + raw hash + anchor; không còn
  character-ratio split (frontend/backend); mỗi Hán passage đi cùng đúng bản dịch
  Việt qua passage_id; translation_segments/passage_translation_alignment đầy đủ
  (provider, prompt_version, quality_status, revision_no, supersedes...);
  translation_jobs + translation_job_items hoạt động resume qua nhiều session;
  worker Groq batch 1-5 passage JSON-contract + validation + commit theo passage;
  UI song ngữ đối chiếu + badge trạng thái + progress X/Y từ DB; export tích lũy
  (chỉ gọi "hoàn chỉnh" khi 100%); admin monitor; 18 test bắt buộc PASS;
  manual verification T50n2060 · 0-0484c-.
---

# T95 — CBETA Pipeline dịch Hán–Việt theo từng passage

## 1. Bối cảnh và kết quả xác nhận (verified, không giả định)

Admin giao nhiệm vụ sửa pipeline dịch CBETA với 6 lỗi báo cáo. Agent **audit
bằng DB thật + mã nguồn thật** trước khi build — kết quả:

| # | Báo cáo lỗi | Trạng thái thực tế (2026-09-05) |
|---|-------------|----------------------------------|
| 1 | Hán render 01…09 | Có — hiện tượng display-time split `dtSegmentHan` (dấu câu + gom 50 ký tự) |
| 2 | Việt 8 block "≈" chia theo tỉ lệ ký tự | **Đã sửa** ở T94 Phase 2B (`641450f`) — live server :8080 sạch (`dtDistributeVi` đã xóa) |
| 3 | `⚠ PHÂN PHỐI TỰ ĐỘNG theo tỉ lệ ký tự…` | **Đã xóa** (T94 Phase 2B) |
| 4 | `Chưa có phần dịch tương ứng.` | **Đã xóa** (T94 Phase 2B) |
| 5 | Hán đoạn 09 lặp toàn văn 01–08 (`T50n2060 · 0-0484c-`) | **Không tái lập** — passage 4061: raw_len 480, `first_half ≠ second_half`, 9 đoạn duy nhất; nghi stale browser cache của trang cũ |
| 6 | Không đủ tin cậy cho citation | Citation vốn trỏ `passage_id`+`loc_ref` (cấp passage), KHÔNG trỏ số đoạn render → không bị ảnh hưởng |

**Chi tiết bằng chứng:** `docs/cbeta_translation_pipeline_audit.md`.

### Vì sao vẫn cần build pipeline mới?

Dù UI đã faithful, **hạ tầng dịch hiện tại vẫn là anti-pattern đã gây lỗi**:
- Groq dịch **toàn passage 1 call** → `passage.vi_text` + `translation_draft=1`
  (`api_passage_translate` app.py:14178; `scripts/t50_passage_vi_backfill.py`).
- Không có đơn vị passage ổn định (`text_passages` = 0 rows), không hash nguồn
  đầy đủ (`raw_zh_hash` = 0 filled), không jobs/resume/lock, không glossary/prompt
  version → **mỗi lần dịch lại văn phong khác nhau**.
- `translation_cache` (T73) chỉ phục vụ person/place bio — không phải passage mới.

Mục tiêu dài hạn: **tích lũy bản dịch hoàn chỉnh theo từng passage** — mỗi đoạn
Hán có id ổn định, bản dịch gắn passage_id, dừng giữa chừng vẫn lưu, resume từ
passage kế tiếp, văn phong ổn định qua glossary + prompt_version + model khóa.

## 2. Quyết định thiết kế (admin đã duyệt 2026-09-05)

| Câu hỏi | Quyết định |
|---------|-----------|
| Đơn vị dịch nguyên tử | **Đoạn con ổn định** — mỗi `text_passage` = đoạn Hán ~2-4 mệnh đề (ranh giới dấu câu, 25–60 ký tự); id `daoanh:cbeta:T50n2060:0484c:p0001`; batch prompt kèm context hàng xóm read-only chống vỡ nghĩa |
| Phạm vi pilot | **T50n2060** (1.037 passage) |
| Cơ chế chạy job | **Thread trong app.py + CLI worker** (`scripts/cbeta_translate_worker.py`); DB job state là source of truth; job trụ khi đóng browser |
| Schema cũ T94 | **Mở rộng additive** 3 bảng trống + tạo `translation_jobs`/`translation_job_items` |

## 3. Nguyên tắc bất biến

1. CBETA raw immutable — không ghi đè raw Hán; luôn giữ work ID, source URL/path,
   canonical anchor, raw hash, source version/import run.
2. `sequence_no` chỉ để hiển thị — không bao giờ là khóa Hán↔Việt.
3. Bản dịch map bằng `passage_id` — exact_1_to_1 / many_source_to_one /
   one_source_to_many / partial_span đều biểu diễn được.
4. Song ngữ đối chiếu **chỉ hiển thị khi có alignment record hợp lệ**.
5. LLM chỉ tạo draft — DB + source anchors + validation + review status là sự thật.

## 4. Phase A — Audit + rebuild Hán source ✅ audit doc done

### A1. Audit ✅ DONE (2026-09-05)
Tài liệu hoàn chỉnh: `docs/cbeta_translation_pipeline_audit.md`.

### A2. Fix duplicate/corrupt source — KHÔNG có corruption thật
- Đã kiểm chứng passage 4061 (`0-0484c-`) KHÔNG lặp. Vẫn xây **importer idempotent**
  để tái tạo `text_passages` từ legacy `passage` kèm hash + anchor, phòng dữ liệu
  corrupt tương lai; passage corrupt (nếu phát hiện) → `source_status='corrupt'`,
  chặn Groq dịch.

### A3. Deterministic segmentation engine
Script `scripts/cbeta_build_text_passages.py` (generator, Zero-RAM):
- Đọc legacy `passage` WHERE `text_id = 'T50n2060'` theo thứ tự ổn định.
- Tách đoạn con: ưu tiên ranh giới `<p>/<head>/<div>/<lb>` nếu có; fallback dấu câu
  `。；！？` + nhóm ≥25–60 ký tự → `segmentation_method='punctuation_fallback'`.
- Mỗi unit: passage_id `daoanh:cbeta:<work>:<page>:p<seq:04d>` (normalize
  `0-0484c-`→`0484c`; loc `0--`→`nopage-<seq>`), `sequence_no`, `juan`,
  `canonical_ref` (loc_ref), `raw_zh_hash` (sha256), `source_status='ok'`,
  `source_version`, `import_run_id`, `legacy_passage_id`.
- **Idempotent**: re-run không duplicate (unique id + hash); backup DB trước.
- Backfill `passage.raw_zh_hash` + `passage.segmentation_method` cho legacy.

## 5. Phase B — Schema dịch & alignment (additive)

Script: `scripts/t95_schema_migrate.py` (+ backup `lineage.db.backup_t95_*`, rollback).

- **`text_passages`** mở rộng: `+source_status`, `+updated_at`,
  `+canonical_start_anchor`, `+canonical_end_anchor`, `+legacy_passage_id`, `+loc_ref`.
- **`translation_segments`** mở rộng: `+passage_id NOT NULL`, `+provider`,
  `+source_original_hash`, `+quality_status` (unreviewed|validated|reviewed|rejected),
  `+created_by_job_id`, `+revision_no DEFAULT 1`, `+supersedes_translation_id`;
  giữ `work_id`/`source_passage_ids` (partial span, back-compat).
  `translation_status`: pending|in_progress|completed|needs_review|failed|superseded.
- **`passage_translation_alignment`** mở rộng: `+updated_at`.
- **Tạo `translation_jobs`**: job_id, work_id, requested_scope, requested_by_user_id,
  provider, model_name, status (queued|running|paused|completed|partial|failed|cancelled),
  next_passage_sequence, total/completed/failed, started_at/finished_at, last_error, timestamps.
- **Tạo `translation_job_items`**: job_item_id, job_id, passage_id, sequence_no,
  status (queued|processing|completed|failed|skipped_existing), attempt_count,
  provider_request_id, raw_response_path, error_message, started/completed, UNIQUE(job_id,passage_id).

## 6. Phase C — Pipeline Groq batch + resume (style-lock)

- Glossary: `data/glossaries/vi-buddhist.json` (Tỳ-kheo, Niết-bàn, An Dưỡng…)
  inject vào prompt; `PROMPT_VERSION` cố định/work; model + temperature 0.1 qua
  `llm_config.json` (bỏ literal `GROQ_KEY` app.py:13751 → env/llm_config).
- Worker: batch 1–5 unit/request, input JSON kèm **context hàng xóm read-only**
  (parent passage + neighbors, đánh dấu không dịch), output contract khớp đúng
  passage_id (không thừa/thiếu/trùng).
- **Validation gate** (trước khi lưu): JSON parse OK; đủ & đúng bộ passage_id;
  translation_vi không rỗng/không truncate/không ngắn bất thường/không lẫn Hán lớn;
  source hash khớp hiện tại; passage không corrupt. Pass → lưu raw response
  (audit) + INSERT `translation_segments` + `passage_translation_alignment`
  (`exact_1_to_1` / `deterministic` / `validated`) → **commit theo passage/batch nhỏ**.
  Fail → `job_item.status='failed'`, lưu raw + error, retry backoff (tối đa cấu hình),
  sau max → job `partial`, báo đoạn thất bại.
- **Resume đa user/session (bắt buộc)**: lock `(work_id, language)`; tìm passage
  chưa có translation VALID theo `sequence_no`; không dịch lại validated/reviewed
  trừ "Dịch lại" / hash đổi / rejected; worker thread server-side chạy tiếp dù
  browser đóng; DB job state là nguồn sự thật (không phụ thuộc session/cookie).
- 218 draft toàn-passage cũ → đánh dấu `legacy_unaligned` (admin/audit), KHÔNG
  hiển thị như cặp hợp lệ.

## 7. Phase D — UI song ngữ (places.html reader)

- Render unit từ `text_passages` (bỏ display-time split); mỗi unit cặp cố định
  `[Hán i]` + `[Việt i]` (desktop 2 cột / mobile chồng Hán trước Việt).
- Badge trạng thái mỗi đoạn: `✓ Bản dịch đã hiệu đính` · `◐ Bản dịch AI đã kiểm
  tra — chờ hiệu đính` · `⏳ Đang dịch` · `⚠ Dịch lỗi — có thể thử lại` ·
  `— Chưa có bản dịch` · `⛔ Nguồn Hán đang lỗi/lặp — chưa thể dịch`.
- Copy chuẩn (không dùng "phân phối tự động"/"số thứ tự không khớp"/"phần dịch
  tương ứng"): "Chưa có bản dịch cho đoạn Hán này." · "Bản dịch đang được tích lũy:
  đã hoàn tất 8/42 đoạn." · "Đang dịch đoạn 9/42…" · "Đoạn Hán nguồn cần được kiểm
  tra…" · "Bản dịch AI nháp — cần hiệu đính học thuật."
- Nút: `Dịch phần còn thiếu` · `Tiếp tục dịch` · `Dịch lại đoạn này` · `Xem tiến độ`
  · `Tải bản dịch tích lũy` · `Báo lỗi bản dịch` · `Mở nguồn CBETA`.
- Progress từ DB: "Bản dịch Việt: 8/42 đoạn đã hoàn tất · Đã hiệu đính: 0/42 · Còn thiếu: 34 đoạn".

## 8. Phase E — Ghép bản dịch tích lũy

- Coverage API + export theo `sequence_no` (tiêu đề/tác phẩm, nguồn CBETA,
  passage ID/canonical refs, Hán, Việt, trạng thái, phiên bản/ngày).
- Chỉ gọi "Bản dịch hoàn chỉnh" khi 100% passage active có validated/reviewed +
  không corrupt + không missing alignment + không pending/failed. Ngược lại tên:
  `Bản dịch tích lũy — 8/42 đoạn`.

Endpoints: GET `/api/cbeta/works/{work_id}/translation-coverage` ·
POST `/api/cbeta/works/{work_id}/translation-jobs` ·
POST `/api/cbeta/translation-jobs/{job_id}/resume` ·
GET `/api/cbeta/translation-jobs/{job_id}` ·
GET `/api/cbeta/passages/{passage_id}/translations` ·
GET `/api/cbeta/works/{work_id}/translation-export`.

## 9. Admin, observability, chi phí

Admin view translation jobs (work/title, provider/model, progress, current passage,
failed passage + error, retry count, latency/token nếu có, raw request/response
audit — admin only, resume/retry/cancel, cost estimate). Secrets: Groq key chỉ ở
env/secret manager; rate limit theo user/IP; quota per-user/per-day; lock chống 2
job dịch cùng passage.

## 10. Tests bắt buộc (18)

Source & segmentation: (1) rebuild `0-0484c-` không tạo đoạn 09 full-text lặp;
(2) mỗi passage có raw hash + anchor; (3) re-run importer không duplicate.
Alignment: (4) input 3 passage_id → 3 translation_id mapping đúng; (5) thiếu 1 id →
không publish batch; (6) duplicate id → reject; (7) malformed/truncated → fail/retry;
(8) translation map theo passage_id, không theo array index.
Resume: (9) dịch 8/42 rồi restart → `Dịch phần còn thiếu` bắt đầu passage 09;
(10) 2 user click cùng lúc → 1 job sở hữu passage; (11) passage 09 failed → retry
09, không đánh completed sai; (12) source hash đổi → translation cũ superseded.
UI: (13) mỗi Hán passage có Việt cạnh/bên dưới đúng passage_id; (14) no character
ratio split anywhere; (15) no "Chưa có phần dịch tương ứng."; (16) UI hiện X/Y từ
DB; (17) incomplete không gắn nhãn "hoàn chỉnh"; (18) mobile đọc cặp Hán→Việt.

## 11. Deliverables

1. `docs/cbeta_translation_pipeline_audit.md` ✅ (2026-09-05)
2. `docs/cbeta_bilingual_translation_architecture.md` ✅ (2026-09-05, draft theo plan)
3. Migration schema + rollback note
4. Rebuild/importer script idempotent (`scripts/cbeta_build_text_passages.py`)
5. Groq translation worker batch/resume/validation (`scripts/cbeta_translate_worker.py`)
6. API docs (endpoints §8)
7. UI bilingual paired-view + progress/status
8. Admin translation-job monitor
9. 18 automated tests (§10)
10. Manual verification report `T50n2060 · 0-0484c-`

## 12. Definition of Done

- Hán source ca test không duplicate toàn văn.
- Không còn character-ratio distribution (frontend/backend).
- User thấy từng Hán passage đi cùng đúng Việt translation (passage_id).
- Groq job dừng rồi tiếp tục từ passage còn thiếu.
- Mỗi translation pass validation lưu ngay DB; user sau nối tiếp từ DB.
- UI nêu "đã hoàn tất X/Y" từ DB; export tích lũy; chỉ 100% = "hoàn chỉnh".
- Mọi bản dịch truy ngược CBETA passage ID + canonical anchor + source hash.

## 13. Rollback (thuận tiện về version trước)

| Giai đoạn | Lệnh |
|-----------|------|
| Task/docs/dashboard này | `git revert <commit-hash>` (commit hiện hành) |
| Schema Phase B | backup `lineage.db.backup_t95_*` → restore; `scripts/t95_schema_migrate.py --revert` |
| Importer Phase A3 | `scripts/cbeta_build_text_passages.py --revert` (xóa rows import_run) |
| Worker/UI D–E | `git revert <commit>`, hoặc `git checkout <prev> -- daoanh/places.html daoanh/app.py` |
| DB bất kỳ | restore từ backup trước khi chạy migration |

## 14. Tài liệu liên quan

- Audit: `docs/cbeta_translation_pipeline_audit.md`
- Architecture: `docs/cbeta_bilingual_translation_architecture.md`
- Trước đó: `tasks/T94-cbeta-alignment-schema.md`, `tasks/T85-full-db-translate.md`,
  `tasks/T50-cbeta-cleanup.md`, `docs/alignment-audit-report.md`,
  `docs/cbeta-global-passage-standard.md`, `docs/cbeta-migration-rollout-plan.md`
- Session tạo task: `docs/sessions/2026-09-05_T95_task_approved.md`
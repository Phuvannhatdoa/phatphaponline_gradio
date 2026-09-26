# CBETA Bilingual Translation Architecture

**Task:** T95 — deliverable #2 (draft research, sẽ được tinh chỉnh khi build)
**Ngày:** 2026-09-05
**Bối cảnh:** audit hoàn chỉnh tại `docs/cbeta_translation_pipeline_audit.md`.
Task: `tasks/T95-cbeta-translation-pipeline.md`.

---

## 1. Nguyên tắc (immutable)

1. **Hán bất biến**: giữ work ID, source path/URL, canonical anchor, raw hash,
   source version & import run. Không ghi đè raw Hán.
2. **`sequence_no` chỉ để hiển thị** — không bao giờ là khóa Hán↔Việt.
3. **Map bằng `passage_id`**: 1↔1, many→1, 1→many, partial_span đều biểu diễn được.
4. **Song ngữ chỉ hiển thị khi có alignment hợp lệ**.
5. **LLM = draft;** DB + source anchors + validation + review status = sự thật.

## 2. Dữ liệu (bảng)

### Đơn vị nguồn — `text_passages` (từ legacy `passage` qua importer)
```
passage_id          TEXT PK   -- daoanh:cbeta:T50n2060:0484c:p0001
work_id             TEXT      -- T50n2060
canonical_ref/loc_ref         -- 0-0484c- (normalize → 0484c cho id; 0-- → nopage-<seq>)
juan / sequence_no            -- số thứ tự hiển thị (KHÔNG phải khóa)
original_zh + raw_zh_hash     -- sha256
segmentation_method           -- punctuation_fallback (mặc định hiện tại)
canonical_start_anchor/end    -- từ loc_ref / TEI nếu có
source_status                 -- ok | corrupt (corrupt → chặn dịch)
source_version / import_run_id / created_at / updated_at
legacy_passage_id             -- cầu nối passage cũ
```

### Bản dịch — `translation_segments`
```
translation_id TEXT PK, passage_id NOT NULL, language 'vi',
translation_text, translator_type (ai_draft|human_reviewed|human_translation),
provider (groq|local_ollama|manual), model_name, prompt_version,
source_original_hash, quality_status (unreviewed|validated|reviewed|rejected),
translation_status (pending|in_progress|completed|needs_review|failed|superseded),
created_by_job_id, revision_no, supersedes_translation_id,
created_at, updated_at
```

### Ánh xạ — `passage_translation_alignment`
```
alignment_id, passage_id, translation_id,
alignment_type (exact_1_to_1|many_source_to_one_translation|
                one_source_to_many_translation|partial_span|uncertain),
source_start_offset/end, confidence, alignment_method
(deterministic|manual|llm_suggested|reviewed),
review_status (pending|validated|reviewed|rejected), created_at, updated_at
```

### Jobs — `translation_jobs` + `translation_job_items`
```
jobs:   job_id PK, work_id, requested_scope, requested_by_user_id, provider,
        model_name, status (queued|running|paused|completed|partial|failed|cancelled),
        next_passage_sequence, total/completed/failed, started/finished_at,
        last_error, created_at, updated_at
items:  job_item_id PK, job_id, passage_id, sequence_no, status
        (queued|processing|completed|failed|skipped_existing), attempt_count,
        provider_request_id, raw_response_path, error_message, started/completed,
        UNIQUE(job_id, passage_id)
```

## 3. Vòng đời job (resume qua nhiều session)

```
User bấm "Dịch phần còn thiếu"
  → resolve work_id + tập passage theo sequence_no (KHÔNG nhận UI index/HTML)
  → skip passage đã có bản dịch VALID (lang=vi, hash khớp, alignment hợp lệ)
  → CREATE translation_jobs (queued) + translation_job_items
  → lock (work_id, language) (~= INSERT job; UNIQUE job_item chống 2 người trùng passage)
  → worker: batch 1–5 passage + context hàng xóm (read-only)
  → Groq JSON-in / JSON-out, contract khớp passage_id
  → validation → insert segment + alignment + commit (từng item/batch nhỏ)
  → update jobs.status + items.status
  → nếu worker dừng (crash/close tab): job ở paused|partial,
    lần sau resume → query passage đầu tiên theo sequence_no chưa completed
```

**Không dịch lại** validated/reviewed trừ khi: user chọn "Dịch lại" / hash nguồn
đổi / review rejected → translation cũ thành `superseded`, bản mới `revision_no+1`,
`supersedes_translation_id` trỏ bản cũ. Export luôn lấy bản active
(validated/reviewed, revision cao nhất).

## 4. Gọi Groq

- **Input JSON** (mỗi request): `task`, `work_id`, `instructions` (dịch sát nghĩa,
  giữ thuật ngữ, đúng JSON, **mỗi passage_id đúng 1 item**), `glossary` (khóa từ
  glossary), `context` (các passage hàng xóm đánh dấu **read-only — không dịch**),
  `passages[]` (passage_id, sequence_no, original_zh).
- **Output JSON**: `translations[]` với `passage_id`, `translation_vi`, `notes`,
  `uncertainties`.
- **Style-lock**: cùng `PROMPT_VERSION` cho 1 work; cùng model; temperature 0.1;
  glossary cố định— admin sửa glossary → bump prompt_version → bản dịch cũ vẫn giữ
  `prompt_version` cũ (không tự động dịch lại).

## 5. Validation gate (trước khi ghi DB)

- JSON parse OK; đủ & đúng bộ `passage_id` gửi (không thừa/thiếu/trùng);
- `translation_vi` không rỗng, không truncate, không quá ngắn bất thường;
- không lẫn lượng lớn Hán nguồn vào bản Việt;
- source hash lúc dịch = hash hiện tại; `source_status != corrupt`;
- pass → INSERT + alignment `exact_1_to_1 / deterministic / validated` + commit;
- fail → `job_item.status=failed`, lưu raw + error, retry backoff, tối đa retry
  cấu hình → job `partial`.

## 6. API endpoints

```
GET  /api/cbeta/works/{work_id}/translation-coverage?language=vi
POST /api/cbeta/works/{work_id}/translation-jobs
POST /api/cbeta/translation-jobs/{job_id}/resume
GET  /api/cbeta/translation-jobs/{job_id}
GET  /api/cbeta/passages/{passage_id}/translations?language=vi
GET  /api/cbeta/works/{work_id}/translation-export?language=vi
```

## 7. UI (places.html reader) — cặp cố định

Per unit `[Hán i]` + `[Việt i]` (desktop 2 cột; mobile chồng Hán trước Việt).
Badge: ✓ hiệu đính · ◐ chờ hiệu đính · ⏳ đang dịch · ⚠ lỗi · — chưa có · ⛔ nguồn lỗi.
Copy chuẩn (mục D3 task). Progress từ DB `X/Y`. Nút: Dịch phần còn thiếu / Tiếp
tục / Dịch lại / Xem tiến độ / Tải bản dịch tích lũy / Báo lỗi / Mở nguồn CBETA.
Draft cũ `legacy_unaligned` chỉ hiển thị trong admin/audit, không render như cặp.

## 8. Export bản dịch tích lũy

Ghép theo `sequence_no`: tiêu đề + nguồn CBETA + passage id/anchor + Hán + Việt +
trạng thái + phiên bản/ngày export. Chỉ gọi "Bản dịch hoàn chỉnh" khi 100% active
passage validated/reviewed, không corrupt, không missing alignment, không
pending/failed. Ngược lại: "Bản dịch tích lũy — X/Y đoạn".

## 9. Bảo mật & chi phí

- Groq key: env/`llm_config.json` (bỏ literal app.py:13751). Không trả key về FE.
- Rate limit theo user/IP; quota per-user/per-day; lock chống 2 job cùng passage.
- Admin monitor: progress, current passage, failed + error, retry, latency/token,
  raw request/response audit, resume/retry/cancel, cost estimate.

## 10. Rollback

- Docs/UI code: `git revert <commit>`.
- Schema: backup `lineage.db.backup_t95_*` + `scripts/t95_schema_migrate.py --revert`.
- Import: `scripts/cbeta_build_text_passages.py --revert`.
- Data mọi lúc: restore backup DB (bản dịch là data bổ sung, không ghi đè raw Hán).
# Session 2026-09-05 — T95: Task tạo + ĐỒNG Ý BUILD + docs + dashboard

**Task:** T95 — CBETA Pipeline dịch Hán–Việt theo từng passage
**Module:** CBETA Core / Translation Pipeline
**Trạng thái task:** in_progress (kế hoạch approved — chưa build code)
**Files mới:** `tasks/T95-cbeta-translation-pipeline.md`,
`docs/cbeta_translation_pipeline_audit.md`,
`docs/cbeta_bilingual_translation_architecture.md`
**Files đổi:** `docs/tasktodo.md`, `docs/progress.md`,
`dashboard/dashboard_process.html`, `data/progress_data.json`
**Commit:** (xem git log sau commit)

---

## Bối cảnh

Admin phê chuẩn kế hoạch chi tiết pipeline dịch CBETA theo passage (kèm yêu cầu:
văn phong ổn định giữa các lần dịch). Yêu cầu: tạo task mới **Txx → T95**, cập nhật
docs/.md, dashboard hiển thị "Đồng ý build", lưu session log, git commit, đảm bảo
mọi fix rollback về version trước thuận tiện.

Trước khi tạo task, agent **audit xác minh 6 lỗi báo cáo bằng DB thật + mã thật**:

| Báo cáo | Kết quả xác minh |
|---------|------------------|
| Hán render 01…09 | `dtSegmentHan` display-time split (dấu câu + 50 ký tự) — còn lại để đọc |
| Việt 8 block "≈" char-ratio | **Đã sửa** T94 Phase 2B (`641450f`); live :8080 sạch |
| `⚠ PHÂN PHỐI TỰ ĐỘNG…` | đã xóa (T94 Phase 2B) |
| `Chưa có phần dịch tương ứng.` | đã xóa (T94 Phase 2B) |
| **Hán đoạn 09 lặp 01–08 (0-0484c-)** | **KHÔNG tái lập**: passage 4061 raw_len 480, `first_half ≠ second_half`, 9 đoạn duy nhất → stale browser cache trang cũ |
| Citation không tin cậy | Citation trỏ passage_id+loc_ref (cấp passage) — không bị ảnh hưởng |

## Quyết định admin (4 câu hỏi — toàn bộ chọn Recommended)

1. **Đơn vị dịch nguyên tử = đoạn con ổn định** (id `daoanh:cbeta:T50n2060:0484c:p0001`);
   batch prompt kèm context hàng xóm read-only.
2. **Pilot = T50n2060** (1.037 passage).
3. **Job = thread trong app.py + CLI worker**; DB job state = source of truth; job
   trụ server-side dù browser đóng.
4. **Schema T94 trống → mở rộng additive** (3 bảng + cột thiếu) + tạo
   `translation_jobs`/`translation_job_items`.

## Đã tạo / cập nhật

- `tasks/T95-cbeta-translation-pipeline.md` — frontmatter (id/title/module/priority/
  status=in_progress/depends_on/created/updated/done_when) + kế hoạch Phase A–E +
  admin/observability + 18 tests + deliverables + DoD + rollback.
- `docs/cbeta_translation_pipeline_audit.md` — deliverable #1 (bản đồ code, schema,
  verify không-corrupt, Groq full-passage hiện tại, raw response lưu ở đâu, nơi
  character-ratio split đã hết).
- `docs/cbeta_bilingual_translation_architecture.md` — deliverable #2 (bảng, vòng
  đời job, JSON contract, validation, endpoints, UI, export, bảo mật, rollback).
- `docs/tasktodo.md` — thêm dòng T95 (top) + dòng ĐỒNG Ý BUILD T95.
- `docs/progress.md` — thêm entry T95 (top) + cập nhật header ngày.
- `dashboard/dashboard_process.html` — banner "ĐỒNG Ý BUILD T95" (phía trên Task Board).
- `data/progress_data.json` — regenerate bằng `scripts/build_progress_data.py`.

## Đảm bảo rollback

- Commit hiện tại: `git revert <sha>` (docs/dashboard — không đụng DB).
- Schema Phase B: backup `lineage.db.backup_t95_*` + `--revert`.
- Import: `--revert`; dữ liệu: restore backup DB (bản dịch = data bổ sung, không
  ghi đè raw Hán). Chi tiết: mục 13 trong task doc.

## Trạng thái & việc tiếp theo

- T95 `in_progress` — Phase A3 importer (script `scripts/cbeta_build_text_passages.py`)
  là bước build đầu tiên, sau đó Phase B schema migrate + Phase C worker.
- T94 giữ nguyên phần còn lại (fill alignment khi user báo sai, lazy T85).

## Files

- Task: `tasks/T95-cbeta-translation-pipeline.md`
- Audit: `docs/cbeta_translation_pipeline_audit.md`
- Architecture: `docs/cbeta_bilingual_translation_architecture.md`
- Rollback: mục 13 task doc
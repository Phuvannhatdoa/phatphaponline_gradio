# Session 2026-09-05 — T95 Build 3: UI song ngữ cặp cố định (Phase D) + coverage từ DB

**Task:** T95 — CBETA Pipeline dịch Hán–Việt theo từng passage
**Ngày:** 2026-09-05 (Tiếp nối `2026-09-05_T95_build2_worker_phaseC.md`)
**Trạng thái:** Phase D DONE (mock pass) — sẽ commit chung với session này

## Mục tiêu (task T95 §7)
- Render unit từ `text_passages` (bỏ display-time split khi có units); cặp cố định [Hán i] + [Việt i].
- 6 badge trạng thái mỗi đoạn; copy chuẩn; nút tác vụ; progress X/Y từ DB.

## Backend (app.py) — 2 endpoint T95 Phase D
1. `GET /daoanh/api/cbeta/passages/<legacy_id>/units?work_id=`:
   - `units[]` = text_passages đơn hàng `sequence_no` của passage, LEFT JOIN bản dịch **hiện hành** (non-superseded, revision max), `aligned` từ `passage_translation_alignment`, `in_progress`/`had_failure` từ `translation_job_items` đang chạy/lỗi.
   - Badge server-side `_t95_badge()`: `corrupt` (source_status≠ok) → `reviewed` (quality validated/reviewed) → `needs_review` (completed) → `in_progress` → `failed` → `missing`.
   - `coverage` = `_t95_coverage()`: total/translated/reviewed/quality_unknown/corrupt/in_progress/failed/missing.
   - `legacy` = passage meta (text_id, loc_ref).
2. `GET /daoanh/api/cbeta/works/<work_id>/coverage`: coverage trực tiếp (dùng cho header progress + Phase E export).

## Frontend (places.html) — reader song ngữ theo units
- Helpers mới (đặt cạnh `dtBuildSegments`):
  - `dtNormLoc`/`dtCbetaSrcUrl` → link CBETA Online (`https://cbetaonline.dila.edu.tw/<sigla>p<page>`).
  - `dtBadgeHtml` → 6 badge màu (xanh lá/ vàng/ xanh dương/ đỏ/ xám/ tím) theo đúng nhãn task T95 §7.
  - `dtUnitsProgressHtml(cov)` → "Bản dịch Việt: X/Y đoạn đã hoàn tất · Đã hiệu đính: R/Y · Còn thiếu: M đoạn · Đang dịch: K".
  - `dtFullBlockVi(p)` → khối bản dịch TOÀN PHẦN passage giữ nguyên (fallback).
  - `dtUnitActions(idx,p,scope)` → nút: Đọc đầy đủ · Dịch lại (draft) · Dịch phần còn thiếu · Tiếp tục dịch · Xem tiến độ · Mở nguồn CBETA.
  - `dtLoadUnits(idx, force)` → fetch units, cache trên `p._units`/`p._coverage`, render lại.
  - `dtJobTranslate(idx, scope)` → POST `/daoanh/api/translation/jobs` (run_now) + `dtPollJobTranslate` poll job detail 2s → reload units.
- `dtRenderPassage`:
  - Có units → Hán pane theo units; Vi pane cặp theo index (`data-seg="u<i>"` để hover-link), badge, bản dịch per đoạn + `(rev n)`, đoạn thiếu → "Chưa có bản dịch cho đoạn Hán này."; header progress; nút tác vụ; nếu passage có legacy `vi_text` → thêm khối TOÀN PHẦN bên dưới (không ghi đè/hiển thị sai).
  - Chưa có units / không CBETA → giữ nguyên fallback cũ (display-split + toàn phần) — **Code Preservation** (không ghi đè chức năng cũ).
- Chips `dt-pchips` giữ nguyên; mobile tabs giữ nguyên (Hán trước, Việt sau).

## Verify
1. `python -c "import app"` + test client:
   - `passages/4061/units` → ok, 9 units (`p0001`=56 chữ), badge `missing`, coverage {total:9316, translated:0, missing:9316, corrupt:0, ...}, legacy = T50n2060 `0-0484c-`.
   - `passages/999999/units` → ok, 0 units.
   - `works/T50n2060/coverage` → đúng.
2. Mock job `page:0-0484c-` (job `_093730`) → 9/9 committed → units badge **9× `needs_review` + aligned=True + translation_text 90 chữ**, coverage translated=9/9316. → `revert-job` → DB sạch (0 segments, 0 jobs).
3. JS: `node --check` từng inline script `places.html` → 0 fail; `npm run test` ✅; `npm run e2e` ✅ (linter `.ps1` có lỗi ESM-detection riêng không liên quan).

## Rollback
- `git revert <sha>` (docs + app.py + places.html); DB không đổi (endpoints read-only). Worker/DB: xem session build1/build2.

## Tiếp theo
- **Phase E**: `GET /daoanh/api/cbeta/works/<work_id>/translation-export` (tích lũy theo sequence_no; chỉ 100% validated = "Bản dịch hoàn chỉnh"), admin monitor (admin/index.html: jobs + failed + raw audit), 18 tests bắt buộc (§10 task), manual verify T50n2060 · 0-0484c-.

## Commit dự kiến
`feat(T95): Phase D UI song ngữ paired-view từ text_passages + coverage DB + docs`
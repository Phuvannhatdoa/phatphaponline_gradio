---
id: T168
title: "T165 SPEC v2 review-accepted — apply verdict §14.1/§14.2/§14.3 into SPEC + docs closure (docs-only, 0 code, 0 DB)"
module: docs · Mimo-Flash SPEC review (no code, 0 DB, 0 API)
priority: high
status: done
created: 2026-09-25
updated: 2026-09-25
depends_on: [T165 (SPEC, id quản lý số task riêng), T166, T167]
owner: claudecode
spec: docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md
done_when: T165 SPEC §2/§14.1/§14.2/§14.3 đã apply toàn bộ verdict đã được Admin/lead phê chuẩn (15/15 issue xác nhận, 2 hiệu chỉnh thật: admin/app.py KHÔNG tồn tại, DB counts lệch do T167 seed RULE-001..015); banner REVIEW-ACCEPTED 2026-09-25; tasktodo/ROLLBACK/session log cập nhật; progress_data.json regen (T168 hiện board); guard + npm pipeline PASS; commit docs 2-pass hash-fill.
---

# T168 — T165 SPEC v2 review-accepted (apply verdict đã phê chuẩn)

**Status:** done (2026-09-25) — ĐÃ XONG: apply toàn bộ verdict §14.2 vào SPEC (chỉ sửa tại chỗ, không tạo bản copy v2), tasktodo/ROLLBACK/session log cập nhật, progress_data.json regen (92 tasks), guard + npm test + e2e + T167 benchmark 15/15 PASS, commit `18262b9` + hash-fill `18262b9`. Revert tiện lợi: `git revert --no-edit 18262b9`. **T165 engine BUILD Phase 3 chưa bắt đầu — SPEC v2 nay là checklist chuẩn (xem §14.3).**  
**Phạm vi:** `docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md` (sửa tại chỗ — additive, không tạo bản copy v2 riêng) · `tasks/T168-t165-spec-v2-review-accepted.md` (mới) · `docs/tasktodo.md` · `docs/ROLLBACK.md` · `docs/sessions/2026-09-25_t168-t165-spec-review.md` · `data/progress_data.json` (regen). **0 code, 0 DB, 0 API, 0 migration.**

## Bối cảnh

Ngày 2026-09-25, tiến hành audit read-only đối chiếu T165 SPEC ↔ DB/code thật (mục §14 trong chính SPEC). Kết quả 15 issue (P0 ×6, P1 ×6, P2 ×3) đã được **Admin/lead phê chuẩn** → task này apply toàn bộ nội dung sửa vào SPEC để SPEC v2 chính thức là nguồn bàn giao đáng tin cho Phase 3 build.

## Verdict phê chuẩn (không sửa thêm, chỉ apply vào SPEC)

### Nhóm 1 — ĐÚNG LOGIC, giữ nguyên đề xuất (13/15)

| # | Mức | Kết luận |
|---|-----|----------|
| #1 | P0 | §2 bổ sung "Có UNIQUE(source_hash, source_type)"; §4.4 ghi rõ hệ quả REPLACE + lookup kèm source_type |
| #2 | P0 | §4.4 lookup phải thêm `source_type` + `status!='invalidated'` + nhánh ưu tiên `status='edited'` |
| #3 | P0 | §4.4 hard rule: `status='edited'` không bao giờ bị REPLACE — trả row + `rules_outdated=true`; force "Dịch lại" dùng UPDATE |
| #4 | P0 | Bỏ câu `DELETE … WHERE selected_rule_codes IS NULL` (sẽ xoá sạch 1761 row legacy NULL) |
| #5 | P0 | Công thức hash = hash phần THẬT đã inject, tính sau khi lock đầy đủ (post-resolver + label + json_mode + known_pending) |
| #6 | P1 | §5.1 thêm `_build_dila_card_prompt` (dila_card → bắt buộc chuyển build_style_prompt / hash khớp phần inject) + `_t126_build_qa_prompt` (excluded — không ghi cache, vẫn nhận select_rules) |
| #8 | P1 | §10 thêm `_t73_call_gemini` (app + admin): trả về/tự log `usage` qua `log_prompt_metrics` |
| #10 | P1 | §5 extract_match_terms: lọc ≥2 chars TRƯỚC, rỗng → match_scope='always' |
| #11 | P1 | §7 Phase 1 thêm coverage check trên 1761 source_text (rule bị loại TB/row, list rule chưa match lần nào) |
| #12 | P1 | done_when: fingerprint = NULL khi T166 chưa build; §9 cảnh báo mass-miss khi bật fingerprint |
| #13 | P2 | Chốt 1 selector: `status='active' AND is_active=1` |
| #14 | P2 | Sửa docstring `_glossary_resolver` "12" → "14" khi build |
| #15 | P2 | Ghi chú T166 tách severity 14 term 1-char (KHÔNG chặn T165) |

### Nhóm 2 — SAI SỐ LIỆU THẬT, giữ tinh thần nhưng sửa numbers/refs (2/15)

| # | Mức | Hiệu chỉnh |
|---|-----|-----------|
| #7 | P0 | **8 site** gọi `_t73_style_lock(conn)` KHÔNG truyền text, **tất cả nằm trong app.py** (2659, 6295, 16640, 17074, 17675, 17822, 17997, 20687) — KHÔNG phải 15, KHÔNG có admin sites (admin/app.py không tồn tại). Giữ đề xuất Phase 3b enumerate + truyền text |
| #9 | P1 | ~22 site `FROM translation_cache` **trong app.py** (5 INSERT: 6391, 16732, 17242, 17308, 17767) — KHÔNG phải 30 + "admin 9". Giữ đề xuất READ sites audit + badge rules_outdated |

### Phát hiện lớn — hiệu chỉnh phần nền SPEC

- **`admin/app.py` KHÔNG TỒN TẠI** (repo hiện tại + git history). Số liệu "Dual codebase app.py 21054 · admin/app.py 18865" trong SPEC §2/§14.1 là **ảo giác của auditor**: nó khớp với file backup `docs/sessions/2026-09-16/app.py.bak-dila-person-index.py` (18954 dòng) — auditor nhầm dùng bản chụp cũ làm "admin app". Kiến trúc thật (AGENTS.md §10): **single codebase** `app.py` (~21061 dòng) + `scripts/t50_passage_vi_backfill.py`; thư mục `admin/` chỉ chứa HTML/CSS/JS. → SPEC §2 row "Dual codebase" phải sửa thành single-app + bỏ toàn bộ ref `admin/app.py`.

- **DB counts lệch do T167 seed (2026-09-24):** audit SPEC §14 cũ ghi 97 rows / 1761 cache / 14 distinct rv / `RULE-%`=0. Sau khi `seed_t167_constitution.py` chạy: `translation_rules` = **112** (terminology 90 · style 10 · forbidden 6 · gate 3 · grammar/provenance/structure 1) · `translation_cache` = **1762** · distinct rv = **15** · `RULE-001..015` = **15 rows** (khác RULE-% kỹ thuật). → §14.1 "Đúng" bảng phải cập nhật số thật.

## Các bước

1. **Tạo task T168** (file này) — frontmatter + body verdict.
2. **Edit SPEC T165 tại chỗ:**
   - §2: sửa bảng "Có UNIQUE(source_hash, source_type)" (#1) · row "Dual codebase" → single app.py + xoá ref admin/app.py · "≥4 builder" bỏ "admin" · Bảng thật: 112 rows / 1762 cache / rv 15 / RULE-001..015 15.
   - §4.4: lookup đủ `source_type`/`status!='invalidated'`/nhánh `edited` (#2 #3) · bỏ DELETE NULL (#4).
   - §5: extract terms ≥2 chars + forced-always (#10) · công thức hash post-resolver + label/json_mode/known_pending (#5).
   - §5.1: thêm 2 builder (#6) + `_t73_get_active_rules` chốt selector `status='active' AND is_active=1` (#13).
   - §7: thêm Phase 3b enumerate caller (#7) + coverage dry-run (#11) · §9: fingerprint mass-miss cảnh báo (#12).
   - §10: thêm `_t73_call_gemini` log usage (#8).
   - §14.1: cập nhật Bảng theo số thật + **đánh dấu "§14.1 cũ đã được sửa bởi T168"**.
   - §14.2: mỗi dòng thêm cột **Verdict · Applied** (DONE/ĐÃ SỬA hoặc "Ghi chú cho build"); sửa #7/#9 theo số thật; bỏ ref admin/app.py.
   - Thêm **banner REVIEW-ACCEPTED 2026-09-25 (Admin) + T168** ở đầu SPEC + bảng verdict tổng.
   - Kỷ luật không dùng số dòng trong bảng chỉnh sửa (app.py đang dịch chuyển do agent khác); dùng **tên hàm**.
3. **tasktodo.md:** thêm row T168 ở đầu ACTIVE (mirror T168).
4. **ROLLBACK.md:** thêm row T168 (``18262b9`` placeholder → hash-fill 2-pass).
5. **Session log:** `docs/sessions/2026-09-25_t168-t165-spec-review.md` — ghi verdict, edit list, verify, commit.
6. **Dashboard:** `python -X utf8 scripts/build_progress_data.py` → `data/progress_data.json` (T168 up).
7. **Verify:** `npm run guard` PASS · `npm run pipeline`/`npm run test`/`npm run e2e` · T167 benchmark test 15/15.
8. **Commit 2-pass hash-fill:** pass 1 content (chỉ stage path T168, KHÔNG đụng app.py/places.html/about.html đang M do agent khác), pass 2 docs hash-fill.

## Verify

- SPEC T165 không còn ref `admin/app.py` (grep = 0) · Bảng thật đúng số mới · 15 dòng §14.2 có verdict/apply.
- `tasks/T168-*.md` frontmatter đủ, `data/progress_data.json` chứa T168+done/in_progress đúng.
- `npm run guard` PASS · `npm run pipeline` PASS · `tests/test_t167_benchmark*` 15/15.
- Commit: 2-pass hash-fill placeholder ``18262b9`` → sha thật (đã verify sau pass 2).

## Files

- `docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md` (sửa tại chỗ — §2, §4.4, §5, §5.1, §7, §9, §10, §14.1, §14.2, banner)
- `tasks/T168-t165-spec-v2-review-accepted.md` (mới)
- `docs/tasktodo.md` (row T168)
- `docs/ROLLBACK.md` (row T168)
- `docs/sessions/2026-09-25_t168-t165-spec-review.md` (session log)
- `data/progress_data.json` (regen)

## Rollback

- Docs-only → **`git revert --no-edit `18262b9``** (khôi phục SPEC §14 cũ + task/tasktodo/ROLLBACK/session cũ + progress_data.json cũ). 0 code, 0 DB → an toàn; KHÔNG ảnh hưởng T167 (task riêng, đã commit `f504683`).
- Lưu ý: reverT168 không đụng file đang M bởi agent khác (app.py/places.html/about.html) vì T168 chỉ stage path riêng.
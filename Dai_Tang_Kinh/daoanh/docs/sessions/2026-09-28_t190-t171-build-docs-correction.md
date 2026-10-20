# Session 2026-09-28 — T190-t171-build-docs-correction

**Agent:** claudecode · **Trạng thái:** DONE (docs-only, 0 code/0 DB) · **HEAD tại thời điểm build:** `e6a20e6` (T189 đã commit; T188-t171 chưa commit — worktree)

## Mục tiêu

Admin: "check và xác nhận vấn đề sau đúng logic chưa" trên 2 file
`docs/Mimo-Flash/T171-person-name-standard-SPEC.md` + `T171-person-name-standard.md`. Sau audit → phê chuẩn
"Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng.
Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done."

## Audit (read-only, DB thật)

Xác nhận claim T188 (đã có trong SPEC worktree) khớp 100%: 46.711 map · 51 dup dila_id · 48.673 people ·
len(name_vi)>80 = 0 (rule chết, max 79) · non-Latin 1.555.

Phát hiện 2 lỗ hổng logic còn lại → **T190** (docs-only):

1. **D1 verified–final NULL:** `name_vi_final` non-null chỉ 5.205/46.711. Rule 6.7/endpoint `name_standard` không bắt
   final NULL → §5.2 strong render rỗng + §6 mirror `people.name_vi := NULL` xóa display.
2. **D2 stats/filter thiếu 6.905 person (14%)** không row `name_vi_map` (status NULL) → `by_name_status` không phủ.

## Thay đổi

1. **SPEC** `T171-person-name-standard-SPEC.md`: banner `[2026-09-28 · T190]` + `amended_by` ghi T190 ·
   §5.2 strong → `standard_status ∈ {reviewed,verified} ∧ m.name_vi_final IS NOT NULL` (+ meta cảnh báo verified–final NULL) ·
   §6 endpoint `name_standard` → validate `verified ⇒ final non-null (400)` + mirror chỉ khi final non-null ·
   rule 6.7 → bắt final NULL · §5 Filter + acceptance ⑩ → `COALESCE(NULLIF(m.standard_status,''),'auto')` (6.905→auto, tổng 48.673) ·
   acceptance ⑥ → "verified thiếu final = 400".
2. **Pointer** `T171-person-name-standard.md`: `amended_by` + bullet `[T190]` (tóm tắt D1/D2).
3. **tasks/T190-t171-build-docs-correction.md** (mới) + **docs/sessions/2026-09-28_t190-t171-build-docs-correction.md** (này).
4. **docs/tasktodo.md**: top entry T190 (hunk-granular: blob = HEAD + T190; giữ WIP T188/T185-187 unstaged).
5. **docs/ROLLBACK.md**: row T190 (placeholder → hash-fill pass-2).
6. **data/progress_data.json**: regen `python -X utf8 scripts/build_progress_data.py`.

## Verify

- DB read-only ok (số liệu ở mục Audit).
- `npm run guard` PASS · `npm run test` PASS · `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing.
- T171 SPEC/pointer vẫn `ready-for-dev` (đúng — build code T171 chưa bắt đầu).
- Đã grep docs sau commit: không còn `b912ea994e1b571ebbea6fbdc6e2c93e590602fd` placeholder trong file commit; entry tasktodo/ROLLBACK chứa sha thật.

## Commit (2-pass, toplevel `visjs-app`, temp index `GIT_INDEX_FILE`, byte-write `refs/heads/master`)

- Pass 1: `docs: T190 t171 build-docs correction (bịt 2 lỗ hổng logic: verified-final NULL + stats phủ 6.905 person qua COALESCE) + docs`
  — SPEC + pointer (nguyên bản worktree T188+T190, LF-normalize) + task T190 + session + tasktodo (HEAD+T190) + ROLLBACK (HEAD+T190) + progress_data.json.
  Blob SPEC/pointer lấy từ worktree (fix nằm trong §5.2/§6 do T188 inline, HEAD pre-T188 không reconstruct được).
- Pass 2: hash-fill `b912ea994e1b571ebbea6fbdc6e2c93e590602fd` vào ROLLBACK/task/tasktodo.
- Revert: `git revert --no-edit b912ea994e1b571ebbea6fbdc6e2c93e590602fd` (docs-only — 0 DB). T188 agent commit sau sẽ đắp không xung đột.
- ⚠️ Race guard: commit pass-1 + ghi ref trong CÙNG 1 lần script (không reload HEAD giữa chừng) — tránh T188 agent đẩy HEAD.
- ⚠️ pipip (claude-mem `127.0.0.1:37700`) offline ở phiên T189 — thử best-effort ở cuối phiên này.

## Chưa làm (thuộc khác)

- T188-t171-spec-logic-fixes: chưa commit (agent song song). Không đụng.
- Build code T171 (migration/endpoint/UI/test) = T171 `ready-for-dev` — chưa bắt đầu.
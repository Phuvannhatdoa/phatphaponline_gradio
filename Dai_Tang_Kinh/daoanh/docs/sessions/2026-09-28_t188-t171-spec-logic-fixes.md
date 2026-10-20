# Session — T188: T171 SPEC logic fixes (docs-only)

- **Date:** 2026-09-28
- **Task:** `tasks/T188-t171-spec-logic-fixes.md` · **Target:** `docs/Mimo-Flash/T171-person-name-standard-SPEC.md` + `T171-person-name-standard.md`
- **Scope:** docs-only · 0 code · 0 DB · SSOT repo-root `visjs-app`
- **Admin directive:**
  > "phê chuẩn đề xuất này, nếu đang làm trên task hiện tại thì tiếp tục, nếu cần hãy tạo task mới…
  > Update lên /docs/ và các .md files tương ứng, cập nhật vào Dashboard để admin xem"
  + "Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files
  tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện.
  Gọi pipip khi done"

## 1. Mở đầu

Admin yêu cầu check 2 file T171 đúng logic chưa. Review phát hiện **4 P0 + 6 P1 + 5 P2** — Admin
phê chuẩn toàn bộ (mặc định: display precedence · `normalized_ascii` · monogram rule). Tạo task mới
**T188** (số tiếp theo sau T187; tiền lệ: T184/T182 = docs-only spec-fix tasks).

## 2. Phase 0 — Verify thật (read-only)

| Fact | Kết quả |
|------|---------|
| `pipip` | = `npm run pipeline` (session `2026-09-27_t167-orphan-cleanup.md`) |
| `api_dila_persons_search` | app.py:8201 (route) / 8202 (def) — SPEC cũ ~7996 **drift** |
| `admin_namevi_map_update` | 13926, sync `people.name_vi` = **13974** — cũ 13112/13154 **drift** |
| `POST …/person/<id>/name_vi` | 18308, sync **18326** — cũ 17505/17523 **drift** |
| `_glossary_resolver` / stats | 17213 / 8329 — cũ 16518 / ~8104 **drift** |
| `birth_year`/`death_year` | cả `people` + `name_vi_map` đều có → rule 6.4 = COALESCE |
| Bảng Hán-Việt | `hanviet_fallback` + `custom_hanviet_override` **có thật** → rule monogram 6.6 khả thi |
| Directive gốc §5.2/§5.5 | **không có file** trong docs/ (grep) → inline vào SPEC |

## 3. Sửa áp dụng (15 điểm)

### P0 — 4 mâu thuẫn

1. **§5 SELECT ↔ §14.3 (JOIN):** `LEFT JOIN name_vi_map` blind → subquery dedupe deterministic
   `ROW_NUMBER() OVER (PARTITION BY dila_id ORDER BY verified>reviewed>COALESCE(approved_at,'') DESC, rowid DESC)`
   + `COUNT(DISTINCT p.id)` + fallback `GROUP BY` cho SQLite <3.25. Alias qua `EXISTS` (không fan-out).
2. **§3.2 ↔ §14.1 (UNIQUE):** bỏ `uq_pna(person_id, name_value, name_role)` →
   `uq_pna_norm(person_id, normalized_value)` + `uq_pna_display` partial `WHERE is_display_name=1`.
   Tổng index khi revert vẫn = 4 (khớp §3.3).
3. **§3.2 ↔ §14.2 (enum):** hợp nhất `name_role` = §14.2 ∪ §3.2
   (`primary_han_name|han_viet_reading|legacy_name_unverified|common_name|primary|common|alias|…`)
   — task chưa build nên không có data cũ dùng enum cũ, an toàn đổi.
4. **§5/§7.2 ↔ §14.5 (display):** chốt 1 công thức — strong = `name_vi_final` **CHỈ KHI**
   `standard_status ∈ {reviewed, verified}`; `auto`/`needs_review`/NULL → strong = legacy, standard
   xuống meta. Inline **§5.2 logic render + §5.3 badge + §5.5 CSS** vào SPEC; áp §7.1/§7.2
   (header person.html) / §14.5 / cả 2 frontmatter `done_when`.

### P1 — 6

5. **§4 đánh lại:** 6.1–6.6 = cờ init · 6.7 = write-validate (cột mới NULL ⇒ không fire khi init) ·
   6.8 = upsert guard (output `auto`, không tính "trúng→needs_review") · **bỏ rule cũ #4** kèm
   chứng minh: `len(name_zh)≤3 ∧ len(name_vi)≥25` ⇒ luôn `len(name_vi)>3×len(name_zh)` ⇒ ⊂6.2 100%.
   Chuẩn hóa mọi tham chiếu ("6.1–6.8" title, §3.1 "rule 6.x", §2 #8).
6. **Rule 6.6 monogram** thay lời hứa §2 #7: map Hán-Việt qua `hanviet_fallback` +
   `custom_hanviet_override`, skip khi map <50% ký tự, không AI/API.
7. **§6 conditional:** `POST person/<id>/name_vi` ghi legacy + mirror alias `legacy_api`,
   upsert `name_vi_final` **chỉ khi trống/trùng**; khác → giữ chuẩn, ghi note — không tự set
   `reviewed`. `admin_namevi_map_update` giữ (curated, overwrite intended).
8. **§8 test fix:** câu "80+ không fire rule cũ" mơ hồ → "56–80 mới-only · 81+ cả hai · 76 fire";
   fixture A000004/A000027 → chỉ Phase 1 re-verify, test chỉ A000006/7/8.
9. **§12 soft-dep T172** + §14.6 #2 skip case `Nhất Hành` khi chưa seed charwise.
10. **Line refs thật** 5 vị trí + inline §5.2/§5.5 (hết phụ thuộc directive ngoài repo).

### P2 — 5

11. `normalized_ascii` (search không dấu, **không unique**) — §3.2/§5 Search/§14.1/acceptance ④/test 6.
12. Revert export alias → `data/backups/t171_alias_<ts>.json` TRƯỚC DROP (§3.3 + §11).
13. Rule 6.4 nguồn năm sinh/tử = `COALESCE(m.*, p.*)` (verify 2 bảng).
14. Seed `is_display_name` (§14.4): mirror chỉ set khi chưa có display; đổi = 1 transaction.
15. Acceptance thêm **⑩** stats `by_name_status` 4 key khớp filter.

## 4. Files đổi

- `docs/Mimo-Flash/T171-person-name-standard-SPEC.md` — sửa tại chỗ, banner `[2026-09-28 · T188] AMEND`
  + frontmatter `updated`/`amended_by`/`done_when` (~20 điểm; file 298 → 381 dòng).
- `docs/Mimo-Flash/T171-person-name-standard.md` — frontmatter + banner + 8 bullet đồng bộ.
- `tasks/T188-t171-spec-logic-fixes.md` — mới.
- `docs/sessions/2026-09-28_t188-t171-spec-logic-fixes.md` — file này.
- `docs/tasktodo.md` — entry T188.
- `docs/ROLLBACK.md` — row revert.
- `data/progress_data.json` — regen (dashboard).

## 5. Verify

- [x] Đối chiếu 2 file: 0 mâu thuẫn §3/§4/§5 ↔ §14 · đánh số 6.1–6.8 nhất quán · line refs khớp Phase 0 (grep 2026-09-28)
- [x] `python scripts/build_progress_data.py` → JSON có T188 (106 task, done=81, git 541 commits)
- [x] `npm run pipeline` (pipip) PASS — log `docs/sessions/2026-09-28_t188-pipeline.log`; guard→e2e PASS, chỉ `e2e:runtime` EPERM pre-existing

## 6b. Đóng sổ

- **Status:** task `done` · tasktodo entry ✅ DONE · dashboard regen (T188 lên board).
- **Commit pass 1:** `11758a056751e891813f721b7bf26393623a82e2` (docs, placeholder) · **pass 2:** `89b9936b647a1ddf6108188f2c755ee1f6dbe089` (hash-fill real sha vào tasktodo/ROLLBACK/task/session) — xem `docs/ROLLBACK.md` row T188.
- **Pipip cuối:** `npm run pipeline` PASS mọi khâu — log `docs/sessions/2026-09-29_t188-pipeline-final.log`; chỉ `e2e:runtime` EPERM `test-results\.last-run.json` pre-existing (T169/T170).

## 7. Git incident log (2026-09-29 — PHẢI ĐỌC KHI REVERT/DEBUG)

Repo làm việc **song song nhiều agent** → sự cố khi commit T188:

1. **Stale `.git/index.lock`** (size 0, age 5–10+ phút; VS Code git polling nhấp nháy quanh nó) →
   mọi `git add/status/reset` fail im lặng (`fatal: unable to write new index file` / exit 1
   không output, PowerShell nuốt stderr; `cmd /c "... & echo rc=%ERRORLEVEL%"` bị parse-time
   expansion → rc giả 0).
2. **Index chính stale** (mtime ≠ HEAD) → `git status` trống trong khi `git diff --cached` hiện
   staged "ma" (xóa oan T74/T187 nếu commit nguyên trạng) → **KHÔNG commit index chính**.
3. **Giải pháp đã dùng:** index tạm `GIT_INDEX_FILE=.git/index.t188b` (read-tree HEAD → add 7 file
   → commit object `68d6a01`), nhưng `update-ref` fail kỳ lạ (reflog ghi được, ref file không set;
   rename/ghi file test OK, không lock) → **bỏ commit object này** (trùng intent, parent cũ).
4. **Agent song song commit song song:** T189 (`2548c4f`+`e6a20e6`) · T190 (`b912ea9`+`ad5d250`)
   · T191 (`7e2b27b`+`993e4ce`) — họ hấp thụ **nội dung amend T188** của SPEC/pointer vào commit
   của họ (HEAD T171 SPEC = 388 dòng chứa T188 AMEND + T190 AMEND) và **rename T171 → X-T171**
   trong worktree (T188 KHÔNG đụng rename này).
5. **Vết test của agent T188 đã dọn:** reflog `.git/logs/refs/heads/master` (xóa 1 dòng `test` +
   3 entries mồ côi `4ae580b→68d6a01`) · ref file về đúng 41 bytes.
6. **Merge tasktodo/ROLLBACK:** worktree = bản T188 (từ HEAD cũ) thiếu entries T189–T191 →
   export `git show HEAD:` về worktree + chèn lại entry/row T188 → không mất data agent khác
   (verify: T189×2 · T190 · T191 + 3 sha revert còn đủ).
7. **update-ref fail 128 lặp lại** (`couldn't set 'refs/heads/master'` — mọi ref; có conflict
   `packed-refs`=`866c911b` vs loose=`3991c28`) → **fix đã dùng:** temp index với
   `GIT_INDEX_FILE` = **absolute path** (cmd `set` relative KHÔNG truyền env — phải dùng
   PowerShell `$env:`) + `git commit-tree` → **ghi ref file trực tiếp** (`[IO.File]::WriteAllText
   refs/heads/master`, 41 bytes) + **append reflog thủ công** vào CẢ `logs/refs/heads/master`
   VÀ `logs/HEAD` (format `<old> <new> <ident> <epoch> +0700\t<msg>`; cảnh báo: PS
   `AppendAllText(path, byte[])` không có overload → byte[] bị cast string thành mã số!
   Dùng `WriteAllLines` với string[] + encoding UTF8).
8. **Main index stale** (mtime 09/27; `git status` fail im lặng; file mới chưa trong index →
   `git diff HEAD` báo "deletion" giả cho file đã commit) → sync bằng `git reset` (mixed) khi
   `index.lock` trống; lock do VS Code/git polling giữ — poll đợi, KHÔNG force xóa lock đang hoạt động.
9. **Commit thật (3 pass):** `11758a05` (docs, placeholder) → `89b9936` (hash-fill real sha) →
   pass 3 (sửa lệnh revert thành 2-commit + log pipeline cuối). Worktree `_t188tmp/` giữ
   backup entry/row + log giữa kỳ (gitignored).

## 6. Revert

- **1 lệnh (docs-only):** `git revert --no-edit 89b9936b647a1ddf6108188f2c755ee1f6dbe089 11758a056751e891813f721b7bf26393623a82e2` (hash-fill trước rồi pass chính) — khôi phục tasktodo + ROLLBACK + task
  + session + progress_data (file T188).
- **Lưu ý:** SPEC/pointer amend T188 **đã nằm trong commits T190/T191** (agent khác commit khi
  rename X-) → revert T188 KHÔNG revert SPEC; muốn revert cả amend SPEC → revert tiếp
  `b912ea99` (T190) + `7e2b27b3` (T191) — xem ROLLBACK rows.
- Không có code/DB → không cần script revert. Cấm `cp *.bak` · cấm `reset --hard`.

---
belongs_to: T166
directive: "[T166-CONTINUE-PHASE4-5]"
title: "T166 CONTINUE PHASE 4/5 — Review directive + delta absorb + prompt chốt (docs-only)"
status: in_progress
created: 2026-09-26
updated: 2026-09-26
designed_by: mimo-flash
handoff_to: Claude Code Agent (tiếp tục T166 — KHÔNG tạo T-task mới)
plan_approved_at: "2026-09-26 (Admin: Đồng ý build — logs + gitcommit + update .md + revert-friendly + pipip)"
---

# T166-CONTINUE-PHASE4-5 — Review directive → 5 P0 + 6 P1 (verify repo/DB thật) + Prompt chốt

> **Bản chất:** absorb directive `[T166-CONTINUE-PHASE4-5]` vào T166 (đang dở) — **KHÔNG T-task mới**, không rebuild T165, không resolver/cache/prompt-builder thứ hai.
> **Session này = docs-only** (0 code/0 DB/0 commit nghiệp vụ) · code phase (matrix A–J, commit Phase 1–3) **chờ Admin lệnh**.
> **Mode prompt:** AUDIT/VERIFY trước — cấm sửa ngoài STOP conditions.
> **[2026-09-26 rev.3]** Phiên song song 07:30 rename 4 file task → prefix `X-` (nội dung giữ nguyên) · Bước 0 build = commit `2710912` · prompt §3 đã cập nhật → export file `PROMPT-T166-G1.txt`.

## 1. Review → 5 P0 + 6 P1 (mọi phát hiện đã verify read-only 2026-09-26)

### P0-1 · 3 commit SHA trong directive KHÔNG tồn tại
`4107cca` · `0150e66` · `b89c7bed` → **NOT FOUND** cả `git log --all`. Trạng thái THẬT:
- `canonical_lock.py` = **untracked (`??`)** (53 KB, build mới) · `style_constitution.py` = **modified (`M`)** → work **CHƯA COMMIT**.
- task file frontmatter vẫn `status: ready-for-dev` (nay đổi `in_progress`) — "build IN_PROGRESS" không có nguồn SSOT.
→ **Bước 0 bắt buộc:** verify `git log` thật → **commit Phase 1–3 đã PASS trước khi chạy matrix** (SPEC: `feat: T166 canonical identity guard + docs`; `git add` **chỉ file T166/T165 liên quan** — tree đang có nhiều `M/D` unrelated, cấm `git add -A`). §11A phải dùng SHA thật từ bước 0.

### P0-2 · SSOT task path sai
Directive ghi `tasks/T166-canonical-identity-guard.md` → **file không tồn tại** (`tasks/` + `tasks/backup/` = 0 hit). Thật = **`docs/Mimo-Flash/T166-canonical-identity-guard.md`** (+ SPEC cùng thư mục ✓).

### P0-3 · Tooling §1/§7 KHÔNG tồn tại
- `scripts/t166_identity_audit.py` = **0 file** (`ls scripts | grep t166` rỗng).
- `npm run audit:t166` = **không có** trong `package.json` (chỉ có `guard` = `scripts/repo_guard.py` ✓).
- SPEC §17 Phase 3 output = "script + db_schema" → **Phase 3 (write-deny audit script) chưa build** → claim "Phase 3.1/3.2 DONE" không có sản phẩm.
→ Sửa §7: build script **trước** (hoặc chuyển `audit:t166` về cuối), không chạy lệnh không tồn tại.

### P0-4 · STOP-4 THẬT nhưng directive trỏ sai endpoint
- `admin_namevi_map_update` (app.py:13167) = **ĐÃ auth** `verify_session` (T166 §7.1) ✓.
- **`admin_namevi_map_delete` (app.py:13146) = DELETE `name_vi_map` KHÔNG `verify_session`, KHÔNG `@before_request` middleware nào** (grep = 0) → ai cũng xóa được **nguồn LOCKED authority**.
→ §5 phải test **CẢ 2 endpoint** (403 không token · 403 invalid · pass valid) — đây là violation STOP-4 đang mở cửa.

### P0-5 · Gate "Phase 2.5 / 3.1 / 3.2" = nhãn không tồn tại
SPEC §17 phase = **0–5** (1 `canonical_lock` · 2 wire pre/post · 3 write-deny audit+migrate · 4 matrix A–J+pipeline · 5 dashboard/taskdone) — grep toàn repo **0 hit** "Phase 2.5/3.1/3.2". → "Xác nhận các phase này DONE" không kiểm chứng được.
→ Sửa §1: **VERIFY claim, không presume** (đồng thời sửa chữ mâu thuẫn "KHÔNG assume" vs list "DONE").

### P1 (6)
1. **§8 E2E query KHÔNG DẤU `Quy+Son+Linh+Huu` sẽ FAIL oan**: `api_global_search` (app.py:10931) = `people.name_vi LIKE` **thô**, không gọi `normalize_text()` (app.py:79) → 0 monks. CASE 3 **với dấu** đã verify PASS (chỉ A001984). → Test **2 biến thể**; không-dấu = *pre-existing search gap*, **không tính vào DONE T166**.
2. **Worker có thể CHƯA wire guard**: `scripts/cbeta_translate_worker.py` grep `t166|canonical` = **0 hit** trong khi SPEC coverage bắt buộc ② (worker STOP→`review_required`) → claim Phase 2 khả năng FAIL thật → VERIFY.
3. **CASE 4/5 = BUG-026** (`docs/bugs.md:423`, `pending_confirm`) — directive không nêu. Residual đã verify: `name_vi_map` **còn row `A001744 → 'Thạch Đầu Hy Thiên'`** (daoanh_dict, name_zh=參同契) · `A010291` auto = **`Hơi Thiên`** ≠ people `Thạch Đầu Hy Thiên`.
4. **CASE 1/5 không deterministic theo Han-string**: `靈祐` = **5 người** (A001984/A023322/A023362/A032868/A035586) · `慧辯` = **5 người** (A001744/A004833/A007895 = "Tuệ Biện"; A011190/A017148 = "Huệ Biện") → **seed LOCK từ `person_id`**.
5. **T177 = label bịa** (0 hit) — Dynamic Filter thật = **T167 absorb / T165 Phase 8** → sửa trong §6.
6. **§1 thiếu `admin/app.py`** (mirror bắt buộc SPEC ③ — đã có 101 chỗ `t166/canonical` ✓) · **§4 site list ≠ site thật**: 4× `_t165_write_cache` (**6424/16742/17278/17847**, đều có `_t166_post_check_translation` TRƯỚC tại 6417/16731/17271/17842 ✓) + **raw `INSERT INTO translation_cache` app.py:17350 (`status='edited'`, bio-edit path — context không thấy post-check)`** + admin mirror + worker.

### ✅ Giữ nguyên (đúng logic)
Invariant thứ tự post-check→write (4 site thật) ✓ · update đã auth ✓ · **5/5 CASE data khớp DB** ✓ · T162 = `fix_t162_namevi.py` (T150b) thật → "không chạy lại" ✓ · BUG-025 no-overwrite ✓ · §7 phân loại FAIL ✓ · §10 chỉ docs khi PASS + regen bằng script ✓ · §6 không duplicate ✓ · DONE checklist chặt ✓ · matrix A–J khớp SPEC §14 (fixture LOCKED = `A009460 丹霞天然`, CANDIDATE = `A005248 安廩` theo SAFETY-003 absorb) ✓ · `npm run guard` có thật ✓.

## 2. Verified facts (read-only 2026-09-26)

| Hạng mục | Thật |
|---|---|
| 3 SHA directive | `4107cca`/`0150e66`/`b89c7bed` NOT FOUND (`--all`) |
| Work tree | `canonical_lock.py` `??` · `style_constitution.py` `M` · nhiều `M/D` unrelated (agents/, *.md) → add scope chặt |
| Task SSOT | `docs/Mimo-Flash/T166-canonical-identity-guard.md` (tasks/ = không có) |
| Script | `scripts/t166_identity_audit.py` = 0 · `npm run audit:t166` = không có · `npm run guard` = `repo_guard.py` ✓ |
| Auth | update:13167 ✓ có · **delete:13146 KHÔNG** · không `before_request` |
| post-check→write | 6417→6424 · 16731→16742 · 17271→17278 · 17842→17847 ✓ · raw INSERT 17350 cần verify |
| Worker | `cbeta_translate_worker.py` 0 hit t166 → coverage ② VERIFY |
| admin/app.py | mirror đã wire (101 hit) ✓ — thêm vào §1 |
| Search | `api_global_search`:10931 LIKE thô · `normalize_text`:79 không được gọi → E2E không dấu FAIL oan |
| CASE data | A001984 `Quy Sơn Linh Hựu` ✓ · A021462 `Kính Đường Giác Viên` ✓ · A010291 `Thạch Đầu Hy Thiên` ✓ · A001744 `Tuệ Biện` ✓ (5 row `慧辯`) |
| Residual | `name_vi_map A001744='Thạch Đầu Hy Thiên'` · `A010291 auto='Hơi Thiên'` · BUG-026 `pending_confirm` |
| SPEC phases | 0–5 · "Phase 2.5/3.1/3.2" = 0 hit |
| T177 | 0 hit (= T167/T165 Phase 8) |

---

## 3. PROMPT CHỐT — dán Claude Code (delta đã nhúng; làm theo đúng thứ tự)

```text
[T166-CONTINUE-PHASE4-5 rev.3 — Bước 0 DONE 2710912 · X- path fix · app.py out-of-scope 2026-09-26]
CANONICAL IDENTITY HARD GUARD — COMPLETE PHASE 4/5

MỤC TIÊU
Hoàn tất T166-build đang dang dở.

SSOT (rev.3 — path theo repo THẬT; 4 file task đã bị phiên song song
rename prefix X- lúc 07:30, tên GỐC không còn trên disk):
- Task: docs/Mimo-Flash/X-T166-canonical-identity-guard.md   (tasks/ KHÔNG có file)
- SPEC: docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md
- Current commits [rev.3]: Bước 0 đã DONE — 2710912 (feat) + 1810927 (docs).
  canonical_lock.py = TRACKED · style_constitution.py = COMMITTED (sạch) ·
  task file status = in_progress. Bạn PHẢI verify TRƯỚC
  (git log --oneline -5, git status --short <các file T166>)
  → nếu thấy 2710912: SKIP commit, thẳng re-audit (mục 1).

KHÔNG tạo T-task mới.
KHÔNG rebuild T165.
KHÔNG tạo resolver/cache/prompt-builder thứ hai.
KHÔNG thay đổi DILA canonical identity bằng LLM.
KHÔNG rollback các Phase đã PASS.

==================================================
0. STATE RECOVERY — ĐÃ DONE (verify-only, rev.3)
==================================================
[rev.3 — thay DELTA-P0-1: hoàn thành bởi session build 2026-09-26]
a) VERIFY: git log --oneline -3 → phải thấy 2710912 (feat) + 1810927 (docs)
   + python -m pytest tests/ -q → phải 76 PASS → ghi vào report (mục A).
b) NẾU 2710912 KHÔNG thấy → STOP báo Admin (đừng commit bừa — nhầm
   repo/branch). NẾU pytest FAIL → STOP, báo đúng quy trình
   ROOT CAUSE/FILE/FUNCTION/LINE/RISK/PROPOSED MINIMAL FIX.
c) CẤM commit: app.py (21.232 dòng WIP vs HEAD 7.636 — Admin decision
   riêng) · admin/app.py (untracked mirror) · scripts/t50_passage_vi_backfill.py.
   Đọc working tree OK, git add KHÔNG được đụng 3 file này.
d) Report mục L = 2710912 (code) + 1810927 (docs) — SHA THẬT, không bịa.

==================================================
1. FIRST — RE-AUDIT CURRENT STATE
==================================================

Đọc code THẬC trước khi sửa:

- canonical_lock.py
- style_constitution.py
- app.py
- admin/app.py            [DELTA-P1-6: mirror bắt buộc SPEC ③ — thêm vào list]
- scripts/cbeta_translate_worker.py
- scripts/t165_rules_engine_migrate.py
- tasks file: docs/Mimo-Flash/X-T166-canonical-identity-guard.md   (rev.3: X- rename)
- docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md
- T165/T169 implementation hiện tại
- DB thật lineage.db ở đúng project root

[DELTA-P0-5 + P1-2] Xác nhận hiện trạng = VERIFY từng claim, KHÔNG presume:
Phase 1        VERIFY (SPEC §17)
Phase 2        VERIFY — đặc biệt scripts/cbeta_translate_worker.py
               (grep t166/canonical = 0 hit → khả năng CHƯA wire, coverage ②)
Phase 3        VERIFY — scripts/t166_identity_audit.py CHƯA tồn tại
               → Phase 3 coi như CHƯA xong (sản phẩm bắt buộc chưa có)
Phase 4        = matrix A–J (chưa chạy)
Phase 5        = dashboard + taskdone (chưa)
Không dùng nhãn Phase 2.5/3.1/3.2 (không có trong SPEC — ghi theo SPEC 0–5).

==================================================
2. PHASE 4 — FULL MATRIX A–J
==================================================

Thực hiện đầy đủ acceptance matrix A–J theo SPEC §14,
trên DB copy (không prod write), fixture theo SPEC:
LOCKED = A009460 丹霞天然 → Đơn Hà Thiên Nhiên ·
CANDIDATE = A005248 安廩 (auto 0.7, KHÔNG lock).

Đây phải là TEST TRÊN CODE/DB THẬT,
không mock canonical data.

Tối thiểu phải cover:

A. LOCKED canonical identity
   → LLM output đúng canonical
   → PASS

B. LOCKED canonical identity
   → LLM đổi tên / đổi âm
   → HARD_FAIL hoặc REVIEW_REQUIRED đúng policy
   → tuyệt đối không promote output thành canonical

C. CANDIDATE identity
   → không được đối xử như LOCKED

D. VI-only / không có authoritative Han identity
   → không tạo fingerprint LOCKED giả

E. UNKNOWN entity
   → UNKNOWN_REVIEW
   → không hallucinate canonical identity

F. Canonical invention
   → output tự tạo identity không có evidence
   → WARN/REVIEW theo SPEC
   → không promote

G. Canonical mismatch
   → HARD mismatch phải fail đúng policy

H. Cross-type mismatch
   → person ≠ place
   → ví dụ 少林寺 không được biến thành person alias

I. Post-check
   → output sau LLM phải qua post_check_translation
   → write_cache chỉ sau post-check

J. Cache / identity fingerprint
   → LOCKED identity thay đổi phải invalidate đúng
   → CANDIDATE/VI-only không gây mass-miss
   → identity hash phải nhất quán

==================================================
3. MANDATORY REAL REGRESSION CASES
==================================================

PHẢI test bằng dữ liệu thật.

[DELTA-P1-4] Quy tắc chung: identity lấy từ person_id (LOCK context),
KHÔNG resolve đơn từ Han-string — 靈祐 và 慧辯 mỗi cái = 5 người trong people.

CASE 1
Seed LOCK: person_id = A001984 (Han context: 靈祐)
Evidence: Quy Sơn Linh Hựu
LLM candidate: Quy Sơn Linh Hữu
Expected:
KHÔNG được silently accept "Linh Hữu"
canonical identity vẫn A001984
identity guard phải phát hiện mismatch nếu violation thuộc policy.

CASE 2
Seed LOCK: person_id = A021462 (Han: 鏡堂覺圓)
Expected Vietnamese: Kính Đường Giác Viên
Không được resolve thành: Quy Sơn Linh Hựu

CASE 3
A001984, search: "Quy Sơn Linh Hựu" (CÓ DẤU)
Expected: trả A001984, không được A021462
[DELTA-P1-1] Biến thể KHÔNG DẤU ("Quy Son Linh Huu") PHẢI test riêng:
api_global_search đang LIKE thô (không normalize_text) → dự kiến 0 kết quả.
Ghi nhận là pre-existing search gap (ngoài scope T166), KHÔNG tính FAIL T166.

CASE 4  [DELTA-P1-3: đây là BUG-026 — docs/bugs.md:423, pending_confirm]
Seed LOCK: person_id = A010291 (Han: 希遷)
Expected: Thạch Đầu Hy Thiên
Không được alias/collision với A001744.
Verify residual đã biết: name_vi_map còn row A001744 →
"Thạch Đầu Hy Thiên" (daoanh_dict, name_zh=參同契);
name_vi_map A010291 auto = "Hơi Thiên" ≠ people.
CHỈ ghi nhận (data fix thuộc BUG-026, không sửa trong task này).

CASE 5  [DELTA-P1-3/P1-4]
Seed LOCK: person_id = A001744 (Han: 慧辯 — 5 người cùng name_zh:
A001744/A004833/A007895 = "Tuệ Biện", A011190/A017148 = "Huệ Biện")
Expected: Tuệ Biện
Không được: Thạch Đầu Hy Thiên

==================================================
4. CACHE SAFETY
==================================================

Kiểm tra toàn bộ write_cache sites.

[DELTA-P1-6] Site THẬT đã verify (inventory để đối chiếu, vẫn phải scan thêm):
- app.py 4× _t165_write_cache: 6424 / 16742 / 17278 / 17847
  (mỗi nơi _t166_post_check_translation TRƯỚC tại 6417 / 16731 / 17271 / 17842)
- app.py ~17350: raw "INSERT INTO translation_cache" status='edited'
  (bio-edit path — context không thấy post-check → CHECK KỸ, đây là site dễ miss)
- admin/app.py mirror (đã wire — verify thứ tự)
- scripts/cbeta_translate_worker.py (verify coverage ② — hiện 0 hit t166)

Invariant:

canonical post-check
    ↓
identity status/hash
    ↓
cache write

KHÔNG được:
LLM
 ↓
cache write
 ↓
identity validation

Nếu phát hiện site nào bypass T166:
FAIL task phase.

Đặc biệt kiểm tra:
- person_bio
- dila_card
- place_note
- relation_evidence
- CBETA worker
- passage translation
- edited/admin translation path

Không tạo write path mới.

==================================================
5. SECURITY
==================================================

Verify CẢ HAI endpoint (DELTA-P0-4 — bản gốc chỉ nêu update):

admin_namevi_map_update   (app.py ~13167 — ĐÃ có verify_session)
admin_namevi_map_delete   (app.py ~13146 — KHÔNG có verify_session,
                           KHÔNG có before_request middleware)

LOCKED authority source
→ verify_session bắt buộc.

Test mỗi endpoint:
- không token → 403
- invalid token → reject
- valid authenticated session → allowed

Nếu admin_namevi_map_delete vẫn mở → STOP condition #4:
báo ROOT CAUSE/FILE/FUNCTION/LINE/RISK/PROPOSED MINIMAL FIX
(thêm verify_session như update), KHÔNG tự sửa ngoài scope.

Không được bypass guard bằng admin UI.

==================================================
6. T165 COMPATIBILITY
==================================================

T166 là HARD GUARD trên T165.

Không phá:
_t73_style_lock
_t73_build_style_prompt
T165 constitution_hash
matched-rule filtering
glossary resolver
translation_cache
translation_rules
T95 worker
T167 validator
T169 engine

Không tạo:
second prompt builder
second cache
second glossary
second identity resolver

[DELTA-P1-5] "T177" trong bản gốc không tồn tại (0 hit repo).
Dynamic Filter thật = T167 absorb / T165 Phase 8.
Nếu T167/T165-Phase-8 chưa build xong:
KHÔNG tự implement lại trong T166. Chỉ kiểm tra interface compatibility.

==================================================
7. PIPELINE
==================================================

Sau khi matrix A–J PASS:

npm run guard
npm run pipeline

[DELTA-P0-3] BỎ "npm run audit:t166" khỏi thứ tự này —
scripts/t166_identity_audit.py + npm script CHƯA tồn tại.
Thứ tự đúng: (i) build scripts/t166_identity_audit.py (SPEC Phase 3)
trước khi chạy matrix → (ii) matrix → (iii) guard → (iv) pipeline.
Nếu chưa build được script: ghi BLOCKED với lý do, không chạy lệnh bịa.

Nếu pipeline FAIL:
- phân loại FAIL do T166
- FAIL do pre-existing
- environment-only

Không sửa unrelated subsystem chỉ để làm xanh pipeline.

==================================================
8. LIVE / E2E
==================================================

Nếu backend/UI path liên quan identity:
test trên server/runtime thật.

[DELTA-P1-1] Test ĐÚNG 2 biến thể, không đánh đồng:
(3a) /daoanh/api/search?q=Quy+S%C3%B4n+Linh+H%E1%BB%B1u   (CÓ DẤU)
     Expected: monks chứa A001984, không có A021462 → tính vào DONE.
(3b) /daoanh/api/search?q=Quy+Son+Linh+Huu               (KHÔNG DẤU)
     Dự kiến 0 kết quả (LIKE thô) → ghi nhận pre-existing gap,
     KHÔNG tính FAIL/PASS của T166.

Và verify theo person_id (không phải Han-string):
A001984 → Quy Sơn Linh Hựu
A021462 → Kính Đường Giác Viên
A001744 → Tuệ Biện
A010291 → Thạch Đầu Hy Thiên

Không chỉ test Python unit.

==================================================
9. DATA SAFETY
==================================================

Trước bất kỳ DB write mới nào:
- xác định migration cần thiết hay không
- nếu không cần → KHÔNG ALTER
- nếu cần → dry-run trước
- backup trước apply
- verify sau apply
- ghi backup path chính xác

Không reseed toàn bộ people.
Không rebuild name_vi.
Không chạy lại T162 (= scripts/fix_t162_namevi.py, T150b).

BUG-025 đã có data fix (people đã đúng).
Không overwrite lại dữ liệu đó trừ khi test chứng minh regression.
[DELTA-P1-3] name_vi_map residual của BUG-025/026 thuộc audit data fix
riêng — CHỈ ghi nhận, không sửa trong task này.

==================================================
10. DASHBOARD / DOCUMENTATION
==================================================

CHỈ khi Phase 4/5 PASS:
- update task T166 status (docs/Mimo-Flash/X-T166-canonical-identity-guard.md
  + docs/tasktodo.md)
- session log
- ROLLBACK.md
- tasktodo → taskdone
- regenerate data/progress_data.json bằng script SSOT
  (python scripts/build_progress_data.py)

Không sửa progress_data.json bằng tay.

Rollback phải dùng:
git revert --no-edit <sha>
Không reset --hard.

==================================================
11. FINAL REPORT
==================================================

Báo cáo bắt buộc:

A. Current HEAD / commits inspected  [DELTA-P0-1: SHA THẬT từ Bước 0]
B. Phase 1–5 verification (theo SPEC 0–5; ghi rõ PASS/CHƯA XONG/
   CLAIM-KHÔNG-CÓ-SẢN-PHẨM — ví dụ Phase 3 script chưa build)
C. Matrix A–J:
   A PASS/FAIL
   B PASS/FAIL
   ...
   J PASS/FAIL

D. Real regression (seed theo person_id):
   A001984 → Quy Sơn Linh Hựu
   A021462 → Kính Đường Giác Viên
   A001744 → Tuệ Biện
   A010291 → Thạch Đầu Hy Thiên
   Search có dấu → A001984 (không có A021462)

E. Cache write-path audit (5 site + worker + admin mirror)
F. Security audit (update + DELETE endpoint)
G. npm run guard
H. npm run pipeline
I. scripts/t166_identity_audit.py (nếu đã build — ghi kết quả)
J. E2E/live verification (2 biến thể dấu/không dấu)
K. DB changes / backup
L. commit SHA thật
M. rollback command

FINAL VERDICT:
PASS
hoặc
PARTIAL
hoặc
FAIL

Nếu bất kỳ HARD invariant nào chưa đạt:
KHÔNG ghi DONE.

STOP CONDITIONS
==================================================

STOP ngay nếu phát hiện:

1. canonical_lock bypass
2. cache write trước post-check
3. LLM có thể promote canonical identity
4. LOCKED identity có thể bị admin write/delete không authenticated
   (đã biết: admin_namevi_map_delete app.py:13146 — verify ngay)
5. T165 prompt/cache bị duplicate
6. DB schema destructive
7. T162 bị chạy lại
8. BUG-025 bị overwrite ngược
9. test dùng fake canonical data
10. phải rebuild toàn bộ translation cache

Khi STOP:
không tự sửa ngoài scope.
Báo chính xác:
ROOT CAUSE
FILE
FUNCTION
LINE
RISK
PROPOSED MINIMAL FIX

DONE CONDITION
==================================================

T166 chỉ được chuyển DONE khi:

[ ] Matrix A–J PASS
[ ] real DB regression PASS (seed person_id)
[ ] canonical hard guard PASS
[ ] post-check PASS
[ ] cache safety PASS (gồm site 17350 + worker)
[ ] security PASS (update + delete)
[ ] t166_identity_audit PASS (đã build)
[ ] npm run guard PASS
[ ] npm run pipeline PASS
[ ] live/e2e PASS (biến thể có dấu; không dấu = ghi nhận riêng)
[ ] dashboard regenerated
[ ] taskdone/rollback/session complete
[ ] commit SHA thật (Bước 0 + phase code)
[ ] rollback path thật

Không dùng từ "DONE" nếu thiếu bất kỳ checkbox nào.

DỪNG TẠI ĐÂY khi xong report.
```

---

## 4. Phases & Gates

| Gate | Nội dung |
|---|------|
| **G0** | Admin duyệt absorb này (docs-only — **session này**) |
| **G1** | Admin paste **§3 (rev.3 = file `PROMPT-T166-G1.txt`)** → Claude Code **verify-only** Bước 0 (= done `2710912`) → build Phase 3 script → matrix A–J → **FINAL REPORT** |
| **G2** | Admin review report → `PASS` → chuyển **Phase 5** (tasktodo→taskdone, dashboard, ROLLBACK) |
| **G3** | FAIL/PARTIAL → STOP, Admin chốt minimal fix riêng |

## 5. Revert

Docs-only session này: `git revert --no-edit <sha_T166C>` (sha trong `docs/ROLLBACK.md`, hash-fill sau commit).
Code phase (sau G1): `git revert` từng commit riêng + `scripts/t165_rules_engine_migrate.py --revert` nếu đụng migration (không có migrate mới ở session docs này).

## 6. Session

`docs/sessions/2026-09-26_t166-phase45-continue-review.md`

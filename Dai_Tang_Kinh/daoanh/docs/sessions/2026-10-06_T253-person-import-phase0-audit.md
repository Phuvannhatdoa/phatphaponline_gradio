# Session 2026-10-06 — T253: Audit Phase 0 Person Import (Cline) + đăng ký task

- **Task:** `tasks/T253-person-import-phase0-audit.md` (id `T253` — đã kiểm 2 tầng: Grep `T253` = 0 hit trước khi tạo file; `npm run dup:ids` không liệt kê T253)
- **HEAD đầu phiên:** `ea50089d08afc4ebb02dbc3b5f3ccaad58f845fa`
- **Scope:** docs-only — **0 sửa code, 0 ghi DB**
- **Phê duyệt của Admin:** "Đồng ý build [báo cáo audit], lưu logs, git commit, update task mới vào các .md tương ứng."

## 1. Việc đã làm

1. **Kiểm chứng báo cáo Phase 0 của Cline** tại HEAD `ea50089` → 13 claim đúng, 6 đính chính (S1…S6), 2 blocker (P0-1, P0-2), trả lời 2 câu hỏi của Cline.
2. **Viết báo cáo:** `docs/integration/Cline/2026-10-06-person-import-phase0-audit.md`.
3. **Đăng ký task:** `tasks/T253-person-import-phase0-audit.md` (frontmatter `id: T253`, `status: blocked` — chờ Admin chốt P0-1).
4. **Session log** (file này) + entry `docs/tasktodo.md` + row `docs/ROLLBACK.md` + regen `data/progress_data.json`.
5. **Chạy gate** (bảng §4) rồi commit theo quy trình temp-index (AGENTS §14/§17).

## 2. Bằng chứng chính (tái chạy được — xem §9 báo cáo)

```text
(Get-Content app.py).Count                     = 24221   ← S1: Cline ĐÚNG (tổng dòng)
Measure-Object -Line                           = 22487   ← audit vòng trước đã ghi nhầm hướng
non-empty sau Trim                             = 22230   (24221 − 1734 dòng trống = 22487)
xml.etree import                               = 5 dòng: 111, 126, 5635 (_t148_ET), 10304, 10465
ET.tostring                                    = 0
xsd/rng dưới data/dila_import                   = 0
XML source                                      = 51070872 byte
route: 19016 persons/<id> · 20072 dila_full · 19475 dila_translate · 8548 adjacent · 2109 static admin
route ghi (UPDATE người cũ): 19724 bio_vi · 19824 dila_vi · 19913 name_vi · 19948 revalidate-hv
tiền lệ P0-1(a): app.py:10167 POST /daoanh/api/admin/cbeta/import-xml → importlib :10193
                cbeta-import.html:263 fetch · :270 refresh sau 1200ms
person.html:123 → POST /daoanh/api/login/check
```

## 3. Phát hiện hạ tầng GIT (quan trọng cho session sau)

Những phát hiện này giải thích vì sao **không được** dùng `git add`/`git diff` blind ở máy này:

1. **Index thật hỏng/stale.** `git ls-files -- tasks/T237-cbeta-corpus-search-reader.md` trả
   **rỗng** dù file tồn tại trên đĩa VÀ có trong HEAD (`git ls-tree` thấy blob `608c384`).
   Tương tự `docs/evidence/2026-10-06_T252_w4_fixes.tsv` (đĩa có, HEAD có, index không).
   Index chỉ giữ được một số path cũ (vd `tasktodo.md`, `ROLLBACK.md` có entry, nhưng
   blob của ROLLBACK = bản **thiếu row T234** = stale).
2. **`git diff HEAD` nổ FALSE-DELETE.** Chứng minh bằng 1 lệnh:
   `git hash-object tasks/T237-cbeta-corpus-search-reader.md` == blob HEAD (`608c384…`) ⇒
   file **byte-identical**, nhưng `git diff HEAD --numstat` vẫn báo `0 117` (coi như xoá).
   ⇒ Diff worktree **chỉ tin được với path có trong index**; với path thiếu, báo D giả.
   Kiểm nội dung file luôn dùng `git hash-object <file>` vs `git rev-parse HEAD:<path>`.
3. **`git status` vẫn hỏng im lặng** (exit 1, 0 output — theo AGENTS §17).
   `git diff --name-status HEAD -- <pathspec>` thì chạy được (exit 0).
4. **Đọc blob UTF-8 an toàn:** PHẢI `cmd /c "git show HEAD:<path> > file"` (redirect thô).
   Dùng `>` của PowerShell sẽ make mangled tiếng Việt    → so sánh cho ra diff giả
   (lần đầu Compare-Object báo 595 dòng khác, thực chất chỉ ~115).
5. **Lệch WORKTREE ↔ HEAD của 2 file chung (đã xử lý theo AGENTS §17):**
   - `docs/tasktodo.md`: worktree = HEAD + **WIP của session khác**
     (`+103/−16` theo git: block T232-T233/T241/T242/T243-T250 chưa commit, cập nhật T227/T230…).
     ⇒ **commit blob dựng từ HEAD** + block T253 của mình; worktree thì thêm block T253
     vào bản hiện có (giữ WIP của họ nguyên vẹn).
   - `docs/ROLLBACK.md`: 2 phía **dịch chuyển thật sự** — HEAD có row `<sha_T234>` + `49216eb`
     mà worktree **không có**; worktree có ~40 dòng WIP (row t208/G208, section T215/T226/
     T227/T232/T233) mà HEAD **không có**. ⇒ commit blob = **HEAD + row T253**
     (giữ row đã commit, không nuốt WIP); worktree thêm row T253 vào bản worktree.
     ⚠ Worktree đang **thiếu 2 row đã commit** — session nào đó sửa ROLLBACK từ bản cũ
     cần merge lại (lấy 2 row từ `git show HEAD:Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md`).

## 4. Kiểm thử (HEAD `ea50089`, sau khi tạo file T253)

| lệnh | kết quả |
|---|---|
| `npm run guard` | ✅ exit 0 — SSOT root đúng, không `.git` lồng |
| `npm run lint` | ✅ exit 0 — 7 script block syntax OK |
| `npm run audit:honesty` | ✅ exit 0 — PASS 7/7 |
| `npm run dup:ids` | ❌ exit 1 — **3 ID trùng CÓ SẴN** (T188, T237, T238) — **không có T253** |
| `npm run pipeline` | ❌ FAIL ở bước 2 `dup:ids` — blocker có sẵn, chạy **trước và sau** khi thêm T253 đều y hệt |

3 ID trùng có sẵn (AGENTS §16 — đổi số bên footprint nhỏ nhất; **ngoài phạm vi phiên này**):

```
T188: tasks/T188-t171-spec-logic-fixes.md ↔ docs/integration/T188-canonical-reference-integration.md
T237: tasks/T237-cbeta-corpus-search-reader.md ↔ tasks/T237-gate-vpa-admin-confirmed-only.md
T238: tasks/T238-cbeta-text-browser-toc.md ↔ tasks/T238-reject-ttl-mismatch-button.md
```

## 5. File tạo / sửa trong phiên

| file | thao tác |
|---|---|
| `docs/integration/Cline/2026-10-06-person-import-phase0-audit.md` | TẠO MỚI — báo cáo audit (điều chỉnh) |
| `tasks/T253-person-import-phase0-audit.md` | TẠO MỚI — task `id: T253` |
| `docs/sessions/2026-10-06_T253-person-import-phase0-audit.md` | TẠO MỚI — file này |
| `docs/tasktodo.md` | SỬA — chèn block `<!-- T253:START -->` sau header (commit blob dựng từ HEAD) |
| `docs/ROLLBACK.md` | SỬA — chèn row `2026-10-06 \| <sha_T253>` sau separator (commit blob dựng từ HEAD) |
| `data/progress_data.json` | REGEN bằng `python -X utf8 scripts/build_progress_data.py` |

## 6. Commit & Revert

- **Pass-1:** temp index (`GIT_INDEX_FILE` + `git read-tree HEAD`) + `hash-object -w` +
  `update-index --cacheinfo` cho đúng 6 file; xác minh `git diff --cached --name-only`;
  cha = `git rev-parse HEAD` tính lại ngay trước commit.
- **Pass-2 (hash-fill):** thay `<sha_T253>` → sha pass-1 trong row ROLLBACK + ghi sha vào
  session log này.

```text
pass-1: dedc14528999a9a6e4163c256dd6df88b5095316   (6 file; đã xác minh `git diff --name-status HEAD~1 HEAD`)
pass-2: bcec8f2b924033cc0d252fe3d151ca1e52d945e9   (hash-fill ROLLBACK sha + session log; 2 file, đã xác minh)
```

> Ghi chú kỹ thuật: `git commit` trên máy này **crash im lặng** (exit 1, không output —
> `GIT_TRACE` dừng ngay sau dispatch) ⇒ phải làm thủ công theo AGENTS §14:
> `git write-tree` → `git commit-tree -p <parent>` → `git update-ref refs/heads/master <new> <old>`
> (CAS `update-ref` **thành công** ở phiên này). Temp index: `GIT_INDEX_FILE` trong
> `%TEMP%` + `git read-tree HEAD` + `hash-object -w`/`update-index --cacheinfo`;
> `.git/index` thật **không đổi** (SHA1 `61A2E086…` trước/sau). Reflog `.git/logs/HEAD`
> **stale** (chốt ở `9749f5d`, master thật do session trước ghi tay ref) — không tin `git reflog`.

**Revert (docs-only, 0 DB):**

```bash
git revert --no-edit <sha_T253_pass1> <sha_T253_pass2>
```

Mất dữ liệu? **Không** — chỉ xoá document/task/log entry; không chạm code, không chạm DB.

## 7. Việc CHƯA làm (ưu tiên)

1. **P0-1 (a)** — Admin đã **chốt (a) additive route** 2026-10-06 (cùng phiên này, sau đây) →
   T253 unblock (`status: in_progress`), Phase 1 bắt đầu: test → route → script → UI.
2. **3 ID trùng T188/T237/T238** — **đã xử lý qua T254** (đổi số `T188-canonical…→T255`,
   `gate-vpa→T256`, `reject-ttl→T257` + `former_ids`) ⇒ `npm run dup:ids` PASS.
3. Worktree `docs/ROLLBACK.md` thiếu 2 row đã commit (§3.5) — nên merge lại khi rảnh.
4. 2 file `docs/integration/REALITY_CHECK.md` + một số `docs/Mimo-Flash/T1xx-*.md`
   **không còn trên đĩa** nhưng còn trong HEAD (xoá thật, không phải false-D) —
   cần xác minh có chủ đích hay không trước khi tidy.


---

# BỔ SUNG 2026-10-07 — T253 Phase 1 BUILD (code)

- **HEAD trước build:** `003495a0739e576474d7f8a01b1293ed78b7c93b`
- **Admin:** "Đồng ý build, hãy lưu logs, git commit và update các thông tin của các task mới vào
  các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó
  1 cách thuận tiện. Gọi pipip khi done."

## 1. Việc đã làm (TDD)

1. **Khảo sát:** DDL `vn_person_authority` (16 cột, `ttl_filename NOT NULL`), journal WAL,
   `appellations` = JSON array string, `gender` ∈ {Male}, token admin = `localStorage.admin_session`,
   route mẫu `t181_import_xml` (:10167→:10223, importlib :10193), static admin :2109,
   `verify_session` :91 (POST :5001/api/login/check), `data/` bị gitignore ⇒ ETL phải ở `scripts/`.
2. **Test trước:** `tests/test_t253_person_import.py` (DB temp + fixture XML 7 person gồm dila_id
   trùng DB + 1 trùng nội XML + 1 không tên). **3 bug thật bị test bắt:**
   (i) expectation sex count; (ii) `DAONH` tính sai cấp khi file ở `data/dila_import/` ⇒ backup rơi
   `data/data/backups/` — module phải tính `DATA_ROOT = dirname(dirname(_HERE))`; (iii) guard revert
   nhầm "bảng trống" = "chưa import" (phải kiểm `sqlite_master`).
3. **Di dời ETL** `data/dila_import/person_import_etl.py` → `scripts/person_import_etl.py`
   (data/ gitignore ⇒ không revert được bằng git — vi phạm yêu cầu Admin).
4. **Route additive** `POST/GET /daoanh/api/admin/person/import-xml` + UI `admin/person_import.html`.
5. **Wire** `test:t253` vào `package.json` (script + pipeline sau `test:t233`).
6. **Pipeline XANH** — kết thúc `2 passed` (e2e:runtime), `T253 PASS 4/4`.

## 2. File tạo / sửa

| file | thao tác |
|---|---|
| `scripts/person_import_etl.py` | TẠO (di dời từ `data/dila_import/` — dir rỗng đã xóa) |
| `tests/test_t253_person_import.py` | TẠO |
| `admin/person_import.html` | TẠO |
| `app.py` | SỬA — constants T253 (sau :9975) + route `t253_person_import` (sau :10223); diff chỉ `+` |
| `package.json` | SỬA — `test:t253` + pipeline |
| `tasks/T253-person-import-phase0-audit.md` | SỬA — §8 Phase 1 BUILD DONE |
| `docs/tasktodo.md` · `docs/ROLLBACK.md` · file này | SỬA |

## 3. Commit & Revert

```text
pass-1: 6f4b1d4104223433d601d2cf9b11d3af984b1ccc  (code: 3 A + 2 M — verified git diff --name-status HEAD~1 HEAD)
pass-2: <sha_pass2 — git log --oneline -1>
```

**Revert git:** `git revert --no-edit <sha_pass2> <6f4b1d4>` (pass-2 trước, pass-1 sau).
Pass-1 = toàn bộ code tính năng; revert làm mất tính năng import (route/ETL/UI/test) —
**chưa có DB mutation nào** từ build nên không cần undo DB.
**Revert DB (nếu Admin đã commit tại UI):** `python -X utf8 scripts/person_import_etl.py
--action revert --run-id <PI-*>` — additive, chỉ xoá hàng run đó, mất 0 dữ liệu cũ;
khôi phục nguyên DB = chép lại `data/backups/person-import-<run_id>/lineage.db`.

## 4. Cảnh báo

- `data/` gitignore ⇒ **mọi ETL/migration mới phải để `scripts/`**, không để trong `data/`.
- Commit theo lệ thường lệ: temp-index plumbing (`git commit` crash trên máy này).
- tasktodo/ROLLBACK dựng blob từ **HEAD + edit** (giữ WIP session khác); worktree cập nhật riêng.

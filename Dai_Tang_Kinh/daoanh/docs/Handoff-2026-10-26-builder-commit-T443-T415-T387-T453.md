# Handoff 2026-10-26 — Builder: commit lô T443 / T415 / T387 / T453 (T285 bị chặn)

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-26 |
| HEAD đầu phiên | `e4fbc5ba` |
| HEAD sau phiên | `a96d7308` (4 commit mới; giữa phiên session khác thêm `9bf4c021` = tasktodo + T435) |
| Commit mới | `348492c0` T387 · `860fd686` T443 · `6ffcf7e2` T415 · `a96d7308` T453 |
| Test | lint PASS · test PASS · e2e PASS · dup:ids OK · guard OK · `test_t387_db_safe_backup.py` 10 pass (exit 0) |
| DB | 0 mutation trong phiên này (chỉ commit code/docs; DB đã được apply ở phiên trước có backup riêng) |
| TTL | không đụng |
| Chưa nộp | T285 (chặn theo Admin), UI `app.py`/`index.html` (chung nhiều phiên) |

## 2. Đọc trong 2 phút

Đã commit 4/5 task builder yêu cầu, mỗi task 1 commit riêng, index dựng từ tạm
(GIT_INDEX_FILE + read-tree HEAD) để không nuốt WIP của session khác. `git diff --name-status
HEAD~N..HEAD` xác nhận đúng danh sách file từng task, không lẫn file của phiên khác.

Ba việc Admin cần quyết ngay:
1. **T285**: task file ghi "Không tự commit code của task này" → KHÔNG nộp. Đồng thời **evidence
   lệch thực tế**: Admin Notes ghi `hooks/pre_tool_use.py` + `tests/test_git_write_hook.py`
   (12 passed) nhưng trên đĩa chỉ có `.claude/hooks/block-git-write.ps1` + `agent-monitor.ps1`
   và KHÔNG có `tests/test_git_write_hook.py`. Cần Admin xác nhận lại trước khi coi T285 DONE.
2. **UI lô chung** (`app.py`, `index.html`, `admin/*.html`,`dashboard_process.html`…): trạng thái
   chưa nộp tích lũy code của ≥3 task (T453 dila search/person card/works API, T387
   `/api/admin/backup`, các route suggest/batch của phiên khác). Cần một lô UI riêng có người
   khoán.
3. **Script lạ `scripts/t443_import_claude_places_districts.py` + `verify_t443_implementation.py`
   + `test_t443_validation.py`**: nhắm schema khác (places_dila_places/districts_dila_districts,
   source_id 10051-10055) KHÔNG khớp quyết định đã apply của T443 → KHÔNG nộp, đề nghị Admin/Xoá
   hoặc chuyển `_archive`.

## 3. Đề suất phần chữa dựng từng task

| Task | Vấn đề | Cách xử lý trong phiên | Bằng chứng | Kết quả |
|---|---|---|---|---|
| T387 | Code done, tests pass nhưng chưa commit; commit bị treo trong checkbox | Nộp 11 file: helper + test + 6 script sửa + sync_to_vps.ps1 + task file (flip `[x]`) + DEV-REPORT | `git diff --name-status 9bf4c021..348492c0` = 11 file mỗi file khớp scope; test rerun exit 0 | DONE (commit) |
| T443 | Script chính đã apply 2026-10-23 chưa nộp; phụ tá nhắm schema sai | Nộp script canonical `t430_import_claude_place_xml.py` + task file + evidence `docs/sessions/2026-10-23/T443/` (manifest + orphans + mismatch). Loại script lạ | commit 860fd686, 5 file `A` | DONE (commit) |
| T415 | Audit hoàn tất, fix script viết xong chưa apply; task file khuyết mục mô tả + Build | Nộp 5 script/summary + audit report txt + task file (flip mục script, thêm mục Build 2026-10-26 ghi rõ CHƯA apply đúng vốn đã) | commit 6ffcf7e2 (7 file) | DONE (commit; gap còn chờ Admin) |
| T453 | Data applied 2026-10-22, script + evidence chưa nộp; UI file chung | Nộp script import + task file + evidence session T453 (webqa, prompts, mismatch CSV, prompt v.v.) | commit a96d7308 (10 file) | DONE (commit) — DONE cuối vẫn chờ Tester/Admin |
| T285 | Admin note cấm tự nộp + evidence lệch đĩa | KHÔNG nộp. DEV-REPORT + hook (`block-git-write.ps1`) còn untracked | thiết bị: `tests/test_git_write_hook.py` KHÔNG tồn tại | BLOCKED |

## 4. Cảnh báo bắt buộc

- **Worktree dùng chung**: HEAD dịch giữa phiên (`e4fbc5ba` → `9bf4c021` do session khác nộp
  docs-tasktodo/T435). Nuôi dư `GIT_INDEX_FILE`: biến GIT_INDEX_FILE không kế thừa giữa 2 lần
  gọi shell → commit lần 1 mất chứng cứ stage (thoát "no changes added"). Phải dựng index +
  add + commit **trong cùng 1 process shell** và dựng trên HEAD mới NHẤT (`read-tree HEAD` ngay
  trước commit).
- `node` bị shadow bởi `C:\Windows\System32\node` (shim hỏng, exit rỗng, 0 output). Phải gọi
  `C:\Program Files\nodejs\node.exe`. Tương tự `Get-ChildItem`/`where`... bị shadow (thay bằng
  python/glob).
- `.gitignore` chặn `*.bak-*` + `*.json` → session dir T453 nộp thiếu 11 file: `A.vi.json`,
  `webqa/web_check_result.json` + các `.bak-*` app/index. Không ép -f; nội dung vi_json đã nằm
  trong DB, bak còn nguyên trên đĩa. Nếu muốn bỏ qua `.gitignore`, phải là quyết định ADMIN.
- 150+ file `D` (tasks/…archive, log.err, check.py…) trong worktree là **của session dọn dẹp
  khác (T376/T377/junk-cleanup)** — tuyệt đối KHÔNG nộp chung, không restore dùng nhầm
  (`git checkout --`) vì sẽ phá việc dọn dẹp của họ.
- `docs/ROLLBACK.md` đang chứa 4 dòng mới (T470/T449) của session khác → KHÔNG nộp; T387/443/453
  revert đã ghi trong frontmatter task + backup DB data/backups, RÕ ràng do đó KHÔNG thêm dòng
  ROLLBACK trong phiên này để tránh nuốt của họ.

## 5. Lệnh revert từng task (copy/paste)

| Task | Revert command | Mất dữ liệu? |
|---|---|---|
| T387 | `git revert --no-edit 348492c0` | Không — additive helper/test; script restore helper vẫn giữ backup data/backups |
| T443 | `git revert --no-edit 860fd686` (code/docs) + `DROP TABLE codex_place_name;` nếu hoàn tác cả DB (additive, mất 0 dòng bảng gốc) | Không |
| T415 | `git revert --no-edit 6ffcf7e2` | Không — 0 UPDATE DB trong phiên; script đã được xem qua review "CHƯA chạy UPDATE nào" |
| T453 | `git revert --no-edit a96d7308` (code/docs) + DB hoàn tác từng bảng backup riêng `python -X utf8 scripts/t453_dila_catalog_import.py --revert` (DROP 3 bảng additive) | DROP 3 bảng dila_catalog_* (additive only) |

## 6. Bảng file thêm/sửa của phiên

```
Committed (theo thứ tự nộp):
348492c0 : 11 file  T387 — scripts/db_safe_backup.py [A], tests/test_t387_db_safe_backup.py [A],
                    scripts/{backup_db_daily,etl_entity_claims,cbeta_build_text_passages,
                    bgis_spatial_join,build3_license_firewall,build3_source_registry_extend}.py [M],
                    sync_to_vps.ps1 [M], tasks/T387-*.md [M], docs/sessions/2026-10-25/T387/DEV-REPORT.md [A]
860fd686 : 5 file   T443 — scripts/t430_import_claude_place_xml.py [A], tasks/T443-*.md [A],
                    docs/sessions/2026-10-23/T443/{T443_manifest.txt,T443_mismatch.csv,T443_orphans.csv} [A]
6ffcf7e2 : 7 file   T415 — scripts/t415_{audit_vn_person_authority,audit_vn_person_authority_fixed,fix_vn_person_authority}.py [A],
                    scripts/{t415_EXECUTION_SUMMARY,T415_SOLUTION}.md [A], tasks/T415-*.md [M],
                    docs/sessions/2026-10-26_T415_audit_report.txt [A]
a96d7308 : 10 file  T453 — scripts/t453_dila_catalog_import.py [A], tasks/T453-*.md [A],
                    docs/sessions/2026-10-22/T453/* (10 file theo .gitignore lọc) [A]
```

Post-commit handoff file này (docs commit riêng).

## 7. Sai lầm tự đáng và bài học

1. **Mất chứng cứ stage ở commit đầu**: triển khai `git add` trên `$env:GIT_INDEX_FILE` ở 1 shell
   call, `git commit` ở shell call khác → biến môi trường KHÔNG kế thừa, commit "no changes
   added". Cách đúng: toàn bộ chuỗi index→add→commit trong 1 process.
2. **Đọc task trước khi xử lý scope**: T285 Admin note cấm nộp — nếu không đọc đúng sẽ thấy và không nộp
   ngược lệnh. Đọc file task trước khi thêm vào phạm vi commit là bắt buộc.
3. **Phát hiện script giả (T443)**: build agent sinh thêm `t443_import_claude_places_districts.py`
   có schema `places_dila_places/districts_dila_districts` KHÔNG tồn tại trong quyết định Admin —
   dám nộp sẽ ô nhiễm SSOT. Luôn đối cứu script với done_when trước khi nộp.

## 8. Việc CHƯA xong (ưu tiên) + câu hỏi cần Admin

1. **T285**: xác nhận lại test của hook — Admin Notes tool 12 pass nhưng `tests/test_git_write_hook.py`
   không tồn tại. File `.claude/hooks/block-git-write.ps1` vẫn untracked. Admin quyết: (a) cho nộp
   sau khi test thật, (b) yêu cầu code lại theo spec đúng, (c) xoá bỏ nhân chứng Tools mismatch.
2. **Lo UI chung**: `app.py` / `index.html` / `admin/*.html` / `dashboard_process.html` /
   `places.html` / `local_gateway.py` / `.claude/settings.json`… tích nhiều task chưa nộp (T453 UI,
   T387 admin/backup API route, các tab place T465/T466, permission fix…). Cần người khoán +
   lint/e2e + nộp 1 lô riêng.
3. **Script lạ T443**: quyết định xoá hoặc lưu trữ `_archive/`.
4. **docs/ROLLBACK.md**: dòng T443 ("DROP TABLE codex_place_name") chưa có trong file — cần một
   commit docs bổ sung (để tránh nhầm với lô T470/449 của session khác, làm riêng).
5. **tasktodo.md**: đã được session khác sửa; chưa viết lại các dòng T443/T415/T387/T453 cập
   nhật trạng thái nộp. Cần merge có kiểm soát.

## 9. Lệnh kiểm tra nhanh (dưới 1 phút)

```powershell
git log --oneline -5                       # thấy 4 commit builder + handoff
git diff --name-status 9bf4c021..HEAD     # table đúng danh sách
node 'C:\Program Files\nodejs\node.exe' scripts/lint-check.js   # bỏ node shadow
python -X utf8 scripts/repo_guard.py       # PASS
python -X utf8 scripts/build_progress_data.py --check-dup-ids   # không trùng
python -X utf8 tests/test_t387_db_safe_backup.py                 # exit 0
```

## 10. Ghi chú cho agent kế tiếp

- Trước khi commit bất kỳ file chung: `git show HEAD:<path> | grep` để kiểm xem code mình cần đã
  vắng HEAD hay đã có — nếu đã có chỉ là housekeeping, KHÔNG nộp lại.
- Session của bạn có thể bị gián đoạn commit của session khác → sau khi dựng index, nếu HEAD đổi,
  hãy **read-tree HEAD lại rồi add lại** trước khi commit.
- T443 phụ tá script lạ; không "sửa lại cho khớp" tự động vì done_when đã apply hết — hỏi Admin.
- Đừng nộp `docs/sessions/2026-10-25/T285/DEV-REPORT.md` nếu chưa giải quyết mismatch ở mục 8.1.

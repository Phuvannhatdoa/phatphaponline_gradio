# Handoff 2026-10-13 — Housekeeping T374–T378

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày | 2026-10-13 (12:30–13:20 +07) |
| HEAD lúc bắt đầu | `master` @ `89cea47` |
| HEAD lúc kết thúc | **`data-authority-lightweight` @ `7f4e654` (orphan, do phiên khác)** — xem mục 4 |
| Phiên | Claude Code qua Remote Control, Admin duyệt 5 việc qua chat |
| Task | T374, T375, T376, T377, T378 — tất cả `in_progress`, chờ daoanh-qa + Admin ✔ Done |
| Commit | **Chưa có** — phiên không được phép `git add` (chế độ quyền). Lệnh soạn sẵn: `docs/sessions/2026-10-13/housekeeping/commit_plan.sh` |
| Kiểm (trước sự cố) | `npm run guard` PASS · `npm run dup:ids` FAIL 1 (T274, chờ Admin; trước đó FAIL 9) · `build_progress_data` 295 task / 72% không đổi · route map 363 = 363 |
| DB | 0 ghi (chỉ SELECT read-only để kiểm) |
| TTL | không đụng |

## 2. Đọc trong 2 phút

- **Đã làm (file):** git health + quy trình revert (T374); gỡ 8/9 ID trùng (T375); tasktodo.md 246 KB → 137 KB (T376);
  dọn 60 file gốc (T377); tách 5 route zenlineage khỏi app.py sang blueprint (T378). Mỗi việc có backup/MANIFEST và
  script `--restore` hoặc bản `.bak`.
- **Phát hiện quan trọng nhất:** lúc ~12:57–13:00 một phiên khác đã chuyển worktree dùng chung sang nhánh orphan
  `data-authority-lightweight`, làm **mọi file tracked của master biến khỏi đĩa** (app.py, places.html, AGENTS.md,
  tasktodo.md, scripts/…). master vẫn nguyên ở `89cea47`. WIP chưa commit trong file tracked (của mọi phiên, gồm phần
  sửa của tôi trong app.py/AGENTS/CLAUDE/tasktodo) mất khỏi worktree; tôi tái tạo được bằng script.
- **3 việc Admin cần làm ngay:**
  1. Dừng phiên đang làm "DILA authority files / T368b"; quyết khôi phục worktree về master (ví dụ từ `visjs-app/`:
     `git checkout -f master` — lệnh ghi đè worktree, Admin tự chạy hoặc giao rõ). Không restart app.py trước khi khôi phục.
  2. Sau đó chạy `reapply_after_restore.py --apply` rồi `commit_plan.sh` (mục 9), hoặc giao lại cho tôi.
  3. Quyết T274 trùng ID (mục 8).

## 3. Chi tiết từng task

**T374 — git health + revert one fix.** Đo (12:3x, trước sự cố): master `89cea47`, 23 dòng status, **0 staged** — cảnh
báo "mass staged deletion" trong CLAUDE.md không còn đúng; 11 deletion chưa stage ở worktree (check_*.py… do phiên khác);
10 file rác `tmp_obj_*`; 2 worktree phụ; 1 stash. Viết `docs/sessions/2026-10-13/git-health.md`,
`docs/process/REVERT_ONE_FIX.md`, nối §19 vào AGENTS.md và mục ngắn vào CLAUDE.md (2 phần nối này mất do sự cố → reapply).

**T375 — 9 ID trùng.** 8 ID (T158, T168, T169, T170, T171, T177, T206, T215) là **bản cũ bị hồi sinh** của file đã đổi
số/đổi tên `X-` trong T222 (2026-10-02): bản hiện hành (T218, T219, X-T220, X-T168…X-T177) có `former_ids`, status/updated
mới hơn, sửa đổi T188/T190 — đã `diff -w` từng cặp. Chuyển 13 bản cũ vào `_archive/2026-10-13-dup-ids/` (giữ đường dẫn,
MANIFEST có sha256). `dup:ids`: FAIL 9 → FAIL 1. Không đổi số ID nào. Bảng ánh xạ: `tasks/T375-…md`.
*Đã cân nhắc và bỏ:* đổi số theo "giữ bản tạo trước" — sai với T158 (T222 đã giữ `T158-lineage-consensus` theo AGENTS §16)
và vô nghĩa khi bản đổi số đã tồn tại.

**T376 — tasktodo.md.** Ai đọc: chỉ `scripts/build_progress_data.py` (quét mọi `docs/**/*.md` tìm claim endpoint —
file lưu trữ vẫn nằm trong docs/ nên claim không mất) và vài script audit cũ; dashboard chỉ nhắc tên file. Quy tắc bảo thủ:
chỉ chuyển khi task file `status: done` **và** dòng trạng thái ghi DONE (không IN_PROGRESS/BLOCKED/…). 74 mục / 114 dòng
(khối marker, dòng `> **[…`, đoạn `**Txxx ✅ DONE`). 615 → 434 dòng, 246.439 → 137.091 byte. Bảo toàn ký tự (trừ khoảng
trắng): 196.791 = 109.126 + 87.665. `build_progress_data` trước = sau. Văn xuôi ACTIVE/PENDING, BUG-*, mục không có task
file: giữ nguyên. Lưu ý: dự án đã có `docs/taskdone.md` (protocol cũ "move DONE sang taskdone.md") — làm theo đường dẫn
Admin duyệt (`docs/archive/tasktodo-done-2026.md`), file mới trỏ tới taskdone.md. Admin có thể muốn gộp.

**T377 — dọn gốc.** 60 file (38 git theo dõi, 22 bị .gitignore) → `_archive/2026-10-13-root-cleanup/` + MANIFEST
(đường dẫn gốc, lý do, byte, sha256, git?). Quét tham chiếu trong code; để lại: `fix_all.py` (build_progress_data nêu tên),
`fix_tabs.js` (build_tab_readiness), `sync_to_vps.log` (sync_to_vps.ps1 ghi), log server đang ghi hôm nay,
`app_local_t360.*` (bằng chứng T360), file chưa chắc (add_tasks.py, add_route.py, list_tables.py, qa_report.json,
schema_places.txt, places_PL000000023255.json, monk_names_vn.json), compute_hash.py/create_waiver.py (phiên khác sửa hôm nay).
Gốc 186 → 126 mục; guard PASS; import app OK.

**T378 — app.py bước 1.** T364 chưa định nghĩa pha đầu ⇒ phương án dự phòng: nhóm **zenlineage** (T139 Phase 2, 5 route,
chỉ phụ thuộc `get_db_connection` + 2 helper riêng). Trích nguyên văn app.py dòng 2445–2749 sang `api_zenlineage.py`
(factory `create_zenlineage_blueprint(get_db_connection)`, theo mẫu `api_ttl_anchor.py`), đăng ký ở cuối app.py.
Bằng chứng: route map (rule+method) 363 = 363 (diff rỗng); 3 GET trả JSON giống hệt (`t378-probe-*.json.txt`);
py_compile + pyflakes OK; dashboard không đổi. Tên endpoint đổi `zenlineage.*` (không có `url_for` nào dùng).
**app.py đã sửa mất do sự cố** — `reapply_after_restore.py` chạy lại đúng script trích.

## 4. Cảnh báo bắt buộc

- ⚠️ **Worktree hiện ở nhánh orphan `data-authority-lightweight`** (7f4e654, 287 file, có cả đường dẫn rác
  `Dai_Tang_Kinh/%SystemDrive%/…`). `git status` chỉ còn `?? Dai_Tang_Kinh/daoanh/`. reflog: 12:42 checkout
  master→data/authority-files-2026-10; 12:43 b8cc366; 12:54 82090d0; 12:57 checkout; 13:00 commit (initial) 7f4e654.
- ⚠️ **Đừng restart app.py** trước khi khôi phục — file không còn trên đĩa; server đang chạy dùng code trong RAM.
- ⚠️ Sau `checkout master`, 13 file T375 + 38 file T377 sẽ **xuất hiện lại ở chỗ cũ** (master vẫn có chúng); bản trong
  `_archive/` vẫn còn. `reapply_after_restore.py` chỉ bỏ bản ở chỗ cũ khi sha256 **giống hệt** bản lưu trữ.
- ⚠️ Phiên này không có quyền `git add` ⇒ chưa commit gì. Không có gì để `git revert` cho lô này cho tới khi chạy commit_plan.
- ⚠️ Worktree dùng chung nhiều phiên (AGENTS §17). Trước commit luôn `git diff --cached --name-status`.

## 5. Lệnh revert từng task

| Task | Sau khi commit | Trước khi commit | Mất dữ liệu? |
|---|---|---|---|
| T374 | `git revert --no-edit <sha_T374>` | chép lại `housekeeping/AGENTS.md.bak-before-T374`, `CLAUDE.md.bak-before-T374`; bỏ 2 file docs mới | Không (docs) |
| T375 | `git revert --no-edit <sha_T375>` | `python -X utf8 docs/sessions/2026-10-13/housekeeping/t375_archive_dup_ids.py --restore` | Không (chỉ di chuyển) |
| T376 | `a4397c2a` (mốc gom, không revert riêng được) + `git revert --no-edit 45b2b5ec` (phần sửa L1) | chép `housekeeping/tasktodo.md.bak-before-T376` → `docs/tasktodo.md`; bỏ `docs/archive/tasktodo-done-2026.md` | Không |
| T377 | `git revert --no-edit <sha_T377>` + `t377_root_cleanup.py --restore` (22 file ignore) | `t377_root_cleanup.py --restore` | Không |
| T378 | `git revert --no-edit <sha_T378>` rồi restart app.py | chép `housekeeping/app.py.bak-before-T378` → `app.py`; bỏ `api_zenlineage.py` | Không (0 DB) |
| Đăng ký | `git revert --no-edit <sha_REG>` | bỏ 5 task file + 5 khối cuối tasktodo | Không |

## 6. File tạo / sửa

| Loại | File |
|---|---|
| Tạo | `tasks/T374…T378-*.md`, `docs/process/REVERT_ONE_FIX.md`, `docs/sessions/2026-10-13/git-health.md`, `docs/archive/tasktodo-done-2026.md`, `scripts/t376_archive_tasktodo_done.py`, `api_zenlineage.py`, `_archive/2026-10-13-dup-ids/` (+MANIFEST), `_archive/2026-10-13-root-cleanup/` (+MANIFEST), `docs/sessions/2026-10-13/housekeeping/*`, file này |
| Sửa (mất do sự cố, chờ reapply) | `app.py`, `AGENTS.md`, `CLAUDE.md`, `docs/tasktodo.md` |
| Sửa (chưa làm — file mất trước khi kịp sửa) | `docs/ROLLBACK.md` (5 dòng, reapply sẽ chèn) |
| Sinh lại | `data/progress_data.json` (build_progress_data; file này vốn đã ` M` do phiên khác; bản trước: `housekeeping/progress_data.json.bak-before-housekeeping`, bị .gitignore) |

## 7. Sai lầm / bài học

- Heredoc Python qua công cụ Bash ở máy này **làm mất dấu `\\`** trong chuỗi (lỗi `'\\'` → `'\'`) — viết script ra file
  rồi chạy, đừng nhúng Python có backslash vào heredoc.
- Lệnh `git add` bị chế độ quyền từ chối ngay lần đầu; tôi không thử lách. Nên hỏi trước quyền git khi giao việc có commit.
- `npm run test` hiện là placeholder (`tests/run-tests.js` chỉ in "Tests passed") — không phải bằng chứng.
- Dashboard (`build_progress_data.scan_routes`) chỉ đếm `@app.route` trong 4 file chính; route trong blueprint không được
  đếm. Với zenlineage không ảnh hưởng (không có claim nào), nhưng các bước tách T364 tiếp theo cần sửa scanner.

## 8. Việc chưa xong (theo ưu tiên) + câu hỏi cho Admin

1. **Khôi phục worktree** (mục 2) — Admin quyết; tôi không tự chạy lệnh git ghi.
2. **Commit** bằng `commit_plan.sh` (cần quyền git) — mỗi mục một commit.
3. **T274 trùng ID:** `T274-vn-lineage-ttl-rule.md` (10-10, parent T270) vs `T274-ttl-rule-design.md` (10-11, "Option B").
   (a) đổi số bản 10-11 sang ID mới + `former_ids: [T274]`, hay (b) gộp làm "bước tiếp" của T274?
4. **daoanh-qa** kiểm độc lập 5 task trước khi Admin ✔ Done.
5. Gộp `docs/taskdone.md` với `docs/archive/tasktodo-done-2026.md`? (Admin chọn)
6. File gốc chưa chắc (add_tasks.py, add_route.py, list_tables.py, qa_report.json, …) — giữ hay lưu trữ?
7. Cập nhật câu cảnh báo "index anomaly" trong CLAUDE.md (hiện 0 staged) — chỉ khi Admin đồng ý sửa phần cũ.

## 9. Lệnh kiểm nhanh

```bash
# visjs-app/
git rev-parse --abbrev-ref HEAD            # phải là master sau khi khôi phục
git diff --cached --name-status            # rỗng trước commit_plan
# daoanh/
python -X utf8 docs/sessions/2026-10-13/housekeeping/reapply_after_restore.py --check
npm run guard ; npm run dup:ids            # dup:ids chỉ còn T274
python -X utf8 scripts/build_progress_data.py   # 295 task (+/- task mới của phiên khác), 72%
python -X utf8 -c "import sys,os;sys.path.insert(0,os.getcwd());import app;print(len(list(app.app.url_map.iter_rules())))"  # 363
```

## 10. Ghi chú cho agent kế tiếp

- [ ] Xác nhận HEAD = master và app.py có trên đĩa trước khi làm gì.
- [ ] `reapply_after_restore.py --check` → `--apply`; đọc kỹ dòng "LỆCH NỘI DUNG" (nếu có: không tự xử lý, báo Admin).
- [ ] Chạy kiểm mục 9, so với log trong `docs/sessions/2026-10-13/housekeeping/`.
- [ ] `commit_plan.sh` từ repo root; script tự dừng nếu staged lệch.
- [ ] Không đánh DONE; để Admin ✔ Done trên dashboard sau QA.

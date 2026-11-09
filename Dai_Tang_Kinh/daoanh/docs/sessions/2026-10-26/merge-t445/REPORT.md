# Gộp T445 / T463 (trùng nội dung) — BÁO CÁO: BLOCKED ở bước đổi tên

- Ngày: 2026-10-26
- Repo: `visjs-app` (toplevel), branch `truyen-dang-the-pho-clean`
- HEAD lúc kiểm: `e4fbc5baac4b4db4ae73e615de65b7d6ea632c7b`
- Trạng thái: **BLOCKED** — không có commit, không có file task nào bị đổi.
- Không sửa code, không ghi DB, không đụng app.py / places.html / namevimap.html / ROLLBACK.md / bugs.md.

## 0. Kết luận ngắn

1. Quyết định theo AGENTS §16: **giữ T445, đổi số T463 → T468** (T463 ít tham chiếu hơn hẳn: 6 so với 48; T445 đã công bố trong tasktodo, có `docs/plans/T445-TASK-SUMMARY.md` và nhiều phiên `docs/sessions/*T445*`).
2. Số mới **T468**: max ID hiện có = 467, và T468 không xuất hiện ở đâu trong `tasks/` + `docs/` (0 mention), cũng không có trong `git grep HEAD`.
3. Bước đổi tên bị **từ chối quyền ghi/xóa** (`os.rename` → `WinError 5 Access denied`). Nguyên nhân đã đo: ACL thư mục `tasks/` có `Everyone: DENY (S,DC)` (delete child) — tiến trình này không xóa/đổi tên được file con. Script dừng ở dòng đầu, **không ghi gì** (đã xác minh: T463 còn nguyên, T468 và T445 chưa tồn tại).
4. Tôi **không** vượt rào này (không đổi ACL, không copy+giữ bản cũ) vì sẽ để lại hai file cùng ID/nội dung trên đĩa.
5. Cần Admin: cấp quyền xóa/đổi tên trong `tasks/` cho tiến trình này, hoặc tự chạy `do_rename.py` (xem §6).

## 1. Bảng so sánh 2 file

| Trường | T445 (git HEAD `e4fbc5ba`, 8920 B, 246 dòng) | T463 (worktree, untracked, 12207 B, 291 dòng) |
|---|---|---|
| id | T445 | T463 |
| former_ids | — | [T445] |
| title | "Wizard UI cho T444 Gemini Places Translation (B0-B9)" | giống |
| status | in_progress | in_progress |
| depends_on | [T444] | [T444] |
| timeline.created / deadline | 2026-10-21 / 2026-10-21 | giống |
| priority | high | high |
| description | có | có |
| **done_when** | **không có** | **có** (block `>`) |
| **## Mô tả** | **không có** | **có** (đúng §21) |
| Headings chung | 8 (Mục Đích, Scope, Implementation, API, WS, Timeline, Files, Verification, Dependencies, Status…) | giống 8 |
| Heading chỉ có ở T463 | — | `## Mô tả`, `## Outcome (2026-10-21)`, `## Status Update (2026-10-21)`, `## Chỉ thị điều phối` |
| Ghi chú | nội dung wizard giống | T463 là bản đã bổ sung done_when/Mô tả/Outcome; "Task này thay thế T445 (bản trùng đã gỡ)" |

Đã xác minh bằng `compare.py` (đọc `git show HEAD:` và file worktree).

Ghi chú về encoding: lần đầu tôi thấy T445 là "UTF-16" và T463 "mojibake" — **do cách tôi ghi file bằng `>` của PowerShell**, không phải lỗi của file. Blob HEAD thực tế là UTF-8 hợp lệ (8920 B, bắt đầu bằng `---`).

Bản nháp T445 đã được phiên trước gỡ khỏi `tasks/` và lưu tại `docs/sessions/2026-10-26/T445-duplicate-removed/T445-placevn-wizard-ui-b0-b9.md` (8920 B, giống HEAD). Nghĩa là phiên trước đã chọn T463 làm bản sống; báo cáo này xác nhận lựa chọn đó cũng đúng theo §16.

## 2. Bảng tham chiếu ID (quét bằng `scan_refs.py`, đọc trực tiếp file)

### T463 — 6 tham chiếu (footprint nhỏ)

| File:dòng | Ngữ cảnh | Xử lý khi đổi số |
|---|---|---|
| tasks/T463-placevn-wizard-ui-b0-b9.md:2 | `id: T463` | đổi → T468 (sẽ làm) |
| tasks/T463-placevn-wizard-ui-b0-b9.md:26 | "**Task T463** (former T445)" | đổi → T468 (sẽ làm) |
| tasks/T463-placevn-wizard-ui-b0-b9.md:222 | `docs/plans/T463-wizard-ui-plan.md` | đổi → T468 (sẽ làm; file plan chưa tồn tại) |
| tasks/T463-placevn-wizard-ui-b0-b9.md:275 | "8 new T463 routes" | đổi → T468 (sẽ làm) |
| tasks/T462-harness-coder-tester-loop.md:13 | "Dashboard hiển thị T462 và T445/T463" | **KHÔNG sửa được**: T462 là file **untracked (WIP)** |
| tasks/T462-harness-coder-tester-loop.md:18 | prose có "T463" | **KHÔNG sửa được**: cùng lý do (WIP) |

Không có T463 trong `docs/tasktodo.md`, `docs/ROLLBACK.md`, `docs/Handoff-*.md`, `scripts/*.py`, `app.py`, `admin/*.html`.

### T445 — 48 tham chiếu (giữ số, KHÔNG đổi)

| File | Dòng | Ghi chú |
|---|---|---|
| docs/tasktodo.md | 34, 793, 794, 795 | Block T445 PENDING/IN_PROGRESS; dòng 34 nói "đợi T445". File **WIP chưa commit** → không sửa |
| app.py | 24945 | Comment "T445 Wizard API" (không sửa — ngoài scope) |
| docs/Handoff-2026-10-21-T445-opencode.md | 1,8–12,18,19,21,50,51,60,66,70,91,99 | **untracked** — chỉ đọc |
| docs/Handoff-2026-10-21-T448-bugfix-batch.md | 37 | — |
| tasks/T443-places-districts-claude-import.md | 49 | "tasks/T445-claude-place-name-import.md" — **ID T445 dùng cho việc khác** (xem §4) |
| tasks/T446-tab-place-live-compare.md | 16, 55 | cùng vấn đề (T445 = dry-run Claude) |
| tasks/T451-claude-place-name-import.md | 3 (`former_ids: [T445]`), 77 | **WIP** (M) |
| tasks/T462-harness-coder-tester-loop.md | 13, 18, 25, 73, 85 | **untracked** |
| tasks/T463-placevn-wizard-ui-b0-b9.md | 3, 21, 26, 281, 291 | sẽ được cập nhật khi đổi số (giữ "former T445", "thay thế T445") |
| tasks/T465-tab-place-claude-column.md | 23 | nhắc "T445 dry-run" |
| scripts/harness_coder_openrouter.py | 9, 10, 25 | **đọc `tasks/T445-placevn-wizard-ui-b0-b9.md`** — xem §5 |
| scripts/import_claude_place_name_dryrun.py | 3, 119, 309 | dry-run Claude (không liên quan wizard) |
| admin/placevn.html | 218, 234, 303, 2410 | comment "T445: Wizard" — không sửa (ngoài scope) |
| docs/plans/T445-TASK-SUMMARY.md, docs/sessions/2026-10-21/T445-debugger-wip/, docs/sessions/2026-10-25/T445-coder*/ | (tên thư mục) | giữ nguyên |

Tổng: 48 dòng (đếm bằng scan).

## 3. Phát hiện quan trọng (không nằm trong yêu cầu gốc)

- **ID T445 đã từng bị dùng cho việc khác**: `tasks/T451-claude-place-name-import.md` có `former_ids: [T445]` và nhiều file (T443, T446, T465, import script) gọi "T445-claude-place-name-import" — đó là dry-run Claude, không phải wizard. Đây là va chạm ID lịch sử; `dup:ids` không bắt được vì không có file trùng ID cùng lúc.
- `docs/tasktodo.md` (WIP) vẫn có block T445 với trạng thái PENDING/IN_PROGRESS và nói "đợi T445" — mâu thuẫn với T463 "in_progress". Sau khi gộp cần cập nhật, nhưng file này đang có WIP chưa commit của phiên khác.
- `scripts/harness_coder_openrouter.py` (đường dẫn `tasks/T445-placevn-wizard-ui-b0-b9.md`): nếu T445 trở thành file con trỏ, harness sẽ đọc con trỏ thay vì spec. Cần sửa đường dẫn sang T468 — **không sửa** (scripts ngoài scope).
- `T451` là file WIP (M) có `former_ids: [T445]`; `T462` và `Handoff-2026-10-21-T445-opencode.md` là untracked → không sửa.
- Quy tắc §21 (Mô tả + done_when) chỉ T463 đạt; T445 HEAD thiếu cả hai.

## 4. Kiểm dup:ids (chạy trực tiếp, không redirect)

```
python -X utf8 scripts/build_progress_data.py --check-dup-ids
[OK] Không có task ID trùng thật.
```
(Chạy trước mọi thay đổi. T445 không có file trên đĩa; T463 là ID duy nhất → OK.)

## 5. Kế hoạch đã chuẩn bị (chưa chạy)

`docs/sessions/2026-10-26/merge-t445/do_rename.py` (đã viết, **chưa chạy thành công**):
- Assert: T463 tồn tại; T468 và T445 chưa tồn tại (không ghi đè).
- `os.rename(T463 → T468)`; frontmatter: `id: T468`, `former_ids: [T463, T445]`, `updated: 2026-10-26`; thay 4 chỗ "T463" → "T468" trong body (assert đúng 4).
- Tạo `tasks/T445-placevn-wizard-ui-b0-b9.md` dạng **con trỏ** (UTF-8): `status: deferred`, `merged_into: T468`, dòng "Gộp với T468 (trùng nội dung) — 2026-10-26".
  - **Lệch so với yêu cầu**: yêu cầu nói "thêm 1 dòng" vào file giữ số, nhưng file T445 không còn trên đĩa; tôi đề xuất con trỏ thay vì khôi phục 246 dòng nội dung trùng. Admin cần xác nhận `status: deferred` (hoặc đổi).

Sau khi chạy `do_rename.py` còn cần (chưa làm):
- Cập nhật `tasks/T462-...:13` (`T445/T463` → `T445/T468`) khi T462 không còn là WIP chưa commit.
- Sửa `scripts/harness_coder_openrouter.py` đường dẫn → T468 (Admin duyệt).
- Commit (2 file: `tasks/T468-...md` mới + `tasks/T445-...md` sửa), message `chore: gop 2 task trung noi dung (T445/T463) -> T468 + former_ids + docs`, dùng index tạm trong thư mục session (`read-tree` parent → `add` đích danh → `diff --cached --name-status` → `write-tree`/`commit-tree` → CAS thủ công trên `.git/refs/heads/truyen-dang-the-pho-clean`). **Chưa viết `do_commit.py`** vì bị chặn ở bước trước — không muốn để script commit dở.
- Không sửa `docs/tasktodo.md`, `docs/ROLLBACK.md`, Handoff: không có chỗ T463 cần đổi ở đó (Handoff/tasktodo chỉ nhắc T445 = số giữ lại).

## 6. Việc Admin cần làm (BLOCKED)

1. Cấp quyền cho tiến trình xóa/đổi tên trong `Dai_Tang_Kinh/daoanh/tasks/` (hoặc gỡ `DENY DC` của `Everyone`), **hoặc** chạy thủ công:
   ```
   python -X utf8 docs/sessions/2026-10-26/merge-t445/do_rename.py
   ```
   (script tự từ chối nếu T468/T445 đã tồn tại).
2. Xác nhận: giữ T445 (con trỏ `deferred`), đổi T463→T468.
3. Duyệt sửa đường dẫn `scripts/harness_coder_openrouter.py` sang T468 (hoặc không dùng harness cho T445 nữa).
4. Sau đó báo lại để tôi cập nhật T462 (WIP) và viết/chạy commit.

## 7. Kiểm chứng đã làm

| Lệnh | Kết quả |
|---|---|
| `git rev-parse HEAD` / `--abbrev-ref HEAD` | `e4fbc5ba…` / `truyen-dang-the-pho-clean` |
| `git ls-files -s` T445 | có trong index (100644), T463 không track |
| `git status` (các file liên quan) | T451, tasktodo, ROLLBACK = M; Handoff-2026-10-21-T445, T462, T463 = ?? |
| `build_progress_data.py --check-dup-ids` | OK |
| `max_ids.py 468 469 470` | max 467; T468/T469/T470 → 0 mention |
| `git grep T468 HEAD -- tasks docs/tasktodo.md` | không có |
| `do_rename.py` | `PermissionError [WinError 5]` tại `os.rename` — không ghi gì |
| Kiểm sau lỗi: T463 True, T468 False, T445 False | trạng thái không đổi |

## 8. Rủi ro / phần chưa làm

- Chưa có commit, chưa có `git show --stat` (không có commit mới).
- Chưa cập nhật T462 (WIP) và harness script — liệt kê ở §2/§5.
- ID T445 từng bị tái dùng (T451) — cần Admin quyết nếu muốn dọn triệt để.
- Các file trong thư mục `docs/sessions/2026-10-26/merge-t445/` là **untracked** và chỉ phục vụ báo cáo: `scan_refs.py`, `max_ids.py`, `compare.py`, `do_rename.py`, `REPORT.md`. Không commit.
- Đã dùng `%TEMP%` một lần (ghi bản giải mã T445 tạm, rồi xóa ngay) — trái yêu cầu, ghi nhận tại đây.
- Đã dùng `>` của PowerShell (ghi UTF-16) cho 2 file kết quả quét sai; đã xóa.

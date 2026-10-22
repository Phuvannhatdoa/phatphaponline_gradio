# Đổi số T445 (Claude place-name import) → T451 — danh sách tham chiếu

Admin duyệt 2026-10-21: file `tasks/T445-claude-place-name-import.md` đổi thành
`T451` (`former_ids: [T445]`). File Wizard `tasks/T445-placevn-wizard-ui-b0-b9.md`
GIỮ NGUYÊN T445. Căn cứ: `docs/sessions/2026-10-21/qa/OI-18-analysis.md`.

## Đã đổi

| File | Thay đổi | Lý do |
|---|---|---|
| `tasks/T445-claude-place-name-import.md` → `tasks/T451-claude-place-name-import.md` | Đổi tên (python os.rename) | Claude = đổi số |
| `tasks/T451-claude-place-name-import.md` frontmatter | `id: T451`, thêm `former_ids: [T445]` | AGENTS §16 |

Body của file task không có tự tham chiếu "T445" (chỉ có trong frontmatter) nên không đổi thêm.

## Không đổi — chưa sửa vì WIP / không tracked (cần Admin/phiên khác xử lý)

| File | Dòng | Nội dung | Lý do chưa sửa |
|---|---|---|---|
| `tasks/T446-tab-place-live-compare.md` | 12, 51 | "T445" = Claude dry-run script / `tasks/T445-claude-...` | Là Claude → nên đổi, NHƯNG file **untracked** (`??`, không có trong HEAD), do phiên khác tạo. Không commit được sạch nếu sửa; chưa sửa. **Cần Admin quyết.** |
| `tasks/T443-places-districts-claude-import.md` | 43 | "tasks/T445-claude-place-name-import.md là dry-run riêng" | Là Claude → nên đổi, NHƯNG file **untracked** (`??`). Chưa sửa. **Cần Admin quyết.** |
| `docs/tasktodo.md` | 22 | "đợi T445" (placevn baseUrl, Wizard) | Là **Wizard** → giữ. File có WIP `M` (phiên khác) → không sửa file này. |
| `docs/tasktodo.md` | 798–800 | block `<!-- T445:START -->` "Wizard UI cho T444 ... Task: tasks/T445-placevn-wizard-ui-b0-b9.md" | Là **Wizard** → giữ. Không sửa (WIP `M`). |
| `docs/ROLLBACK.md` | — | không có "T445" | Không có gì để đổi. File có WIP `M` → không sửa. |
| `docs/bugs.md` | — | không có "T445" | Không có gì để đổi. File có WIP `M` → không sửa. |
| `docs/plans/T445-TASK-SUMMARY.md` | 1, 101–117 | Plan Wizard | Là **Wizard** → giữ. |
| `tasks/T445-placevn-wizard-ui-b0-b9.md` | 2, 18, 214 | Wizard | Là **Wizard** → giữ (theo Admin). |
| `docs/sessions/2026-10-21/**` (OI-18-*, OPEN-ITEMS, COORDINATOR-REPORT-T448, T416_REPORT, T412/app.py.bak, build/git-status-after.txt, index-sync/status-before.txt, app.py.bak_T448) | nhiều | Log lịch sử, ghi đúng hiện trạng thời điểm đó | Giữ nguyên — không sửa log lịch sử (OI-18-analysis cũng khuyến nghị "không sửa"). |
| `docs/Handoff-2026-10-21-T448-bugfix-batch.md` | 37 | "WIP session khác (T445...)" | Lịch sử handoff → giữ. |

## Ngoài phạm vi (KHÔNG sửa — không nằm trong danh sách được phép)

| File | Dòng | Nội dung | Ghi chú |
|---|---|---|---|
| `scripts/import_claude_place_name_dryrun.py` | 3, 119 (User-Agent `T445-dryrun`), 309 | header / banner "T445" = Claude | Nên đổi sang T451 ở lần sau (ngoài scope lệnh này). |
| `app.py` | 12255 | comment "(T445)" = Claude | Nên đổi sang T451; `app.py` đang có WIP phiên khác → không đụng. |
| `docs/sessions/2026-10-21/rename-t451/do_rename.py` | 3 | chính script đổi tên | Giữ (log thao tác). |

## Ghi chú cho Admin

- Theo `git ls-files`, `tasks/T445-claude-...` và `tasks/T451-...` đều **chưa từng được track** (untracked).
  Vì vậy commit này sẽ là **A** (thêm `T451`) chứ không phải **D + A** như dự kiến;
  không có `D tasks/T445-claude-...` trong HEAD để xoá.
- Sau khi commit, `tasks/T445-claude-...` không còn tồn tại trên đĩa; `T445` còn lại trong repo = Wizard duy nhất
  → `dup:ids` cần kiểm lại (xem kết quả trong báo cáo).

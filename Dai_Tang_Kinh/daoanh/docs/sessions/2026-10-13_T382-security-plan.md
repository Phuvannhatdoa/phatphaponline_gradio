# Session 2026-10-13 — T382 kế hoạch bảo mật & phát hành an toàn

## Mô tả ngắn

Admin yêu cầu kiểm chứng `docs/reports/ARCHITECTURE-REVIEW-2026-10-13.md` (Codex/GPT). Kết quả kiểm (read-only) ghi ở
`docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md`. Admin trả lời "phê chuẩn đề xuất này", yêu cầu tạo task Txx, cập
nhật docs + Dashboard, giao Hermes dev.

## Thiết kế đã chọn

- 1 task cha **T382** (không `dispatch`, Hermes bỏ qua) + 7 task con **T383–T389** có `dispatch: approved`, `depends_on`
  để Hermes tự xếp sóng và tôn trọng luật "mỗi file một agent ghi" (T383 → T384 cùng `app.py`).
- T381 không dùng vì `tasks/T380-selective-restore-4-tables.md:141` đã đặt chỗ T381 (kiểm tầng 2, AGENTS §16).
- T386 (Google ID token) để `blocked` vì cần Admin tạo `GOOGLE_CLIENT_ID`; Hermes sẽ bỏ qua tới khi Admin đổi sang `pending`.
- Không sửa code trong session này — chỉ tài liệu/task.

## File tạo / sửa

| Loại | File |
|---|---|
| Tạo | `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` |
| Tạo | `docs/plans/T382-security-release-hardening-PLAN.md` |
| Tạo | `tasks/T382…T389-*.md` (8 file) |
| Sửa | `docs/tasktodo.md` — nối 8 khối `<!-- T38x:START/END -->` ở cuối (bản sao: `docs/sessions/2026-10-13/T382/tasktodo.md.bak-before-T382`) |
| Sinh lại | `data/progress_data.json` (`scripts/build_progress_data.py`: 309 task, T382–T389 hiện trên board) |
| Log | `docs/sessions/2026-10-13/T382/build_progress_data.log`, `dashboard_T382_rows.txt`, `dup-ids.log` |

## Cách chạy / kiểm

```bash
python -X utf8 scripts/build_progress_data.py
curl -s http://127.0.0.1:8080/daoanh/api/progress/dashboard   # thấy T382–T389
npm run dup:ids    # T382–T389 không trùng; 9 FAIL còn lại là có sẵn (xem dưới)
```

## Ghi chú

- `npm run dup:ids` đang FAIL 9 ID cũ (T158…T274) — do worktree được khôi phục về master sau sự cố orphan-branch, phần
  T375 (lưu trữ 13 bản trùng) chưa được áp dụng lại. Không liên quan T382–T389.
- Chưa commit: phiên này không có quyền `git add` (đã bị từ chối ở phiên housekeeping). Danh sách file để commit một lần
  (docs-only): bảng "File tạo / sửa" ở trên, commit message gợi ý `T382: kế hoạch bảo mật + task T383–T389 + verify report`.
  Revert: `git revert --no-edit <sha>`.

## Cập nhật 2026-10-13 ~19:10 — Admin hoãn phần bảo mật

Admin: "ngừng các giao thức bảo mật, acc test dùng duy nhất gmail để login, khi nào ver chính thức ra mắt trên Net ta sẽ
config task security sau".

- T383, T384, T386, T388 → `status: deferred` + `dispatch: deferred` + `deferred/undone_reason/undone_until/undone_action`.
- T382 giữ `pending` (còn task con đang làm); T389 bỏ `depends_on: [T384]`, thêm `depends_note`.
- T385, T387, T389 vẫn `dispatch: approved` (an toàn deploy/backup/dữ liệu, không phải auth).
- Không đổi code login: hiện đã chỉ chấp nhận địa chỉ `@gmail.com`/`@googlemail.com` nằm trong `data/admin_emails.txt`.
- Bản sao trước khi sửa: `docs/sessions/2026-10-13/T382/*.bak-before-defer`.
- Lưu ý Dashboard: `scripts/build_progress_data.py` có `VALID_STATUSES = {pending, in_progress, blocked, done}` nên task
  `deferred` hiện trên board như **pending** (có sẵn từ trước, ví dụ T27). Hermes vẫn không nhận vì `dispatch: deferred`.

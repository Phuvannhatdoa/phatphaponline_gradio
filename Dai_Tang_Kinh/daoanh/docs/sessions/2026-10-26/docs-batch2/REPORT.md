# REPORT — docs-batch2 (đưa T436–T438, T454–T457, báo cáo bug 048–051 vào git)

Ngày: 2026-10-26 · Agent: daoanh-debugger (subagent tài liệu) · KHÔNG push · KHÔNG ghi DB · KHÔNG sửa code.

## Kết quả commit

| Mục | Giá trị |
|---|---|
| PARENT (HEAD đọc ngay trước commit) | `a96d73089b56d504da7051d87767422a253e9624` |
| NEW | `78418dfe5aa48a67738c7dfad4ee1370dc41f2fa` |
| Message | `docs: dua task T436-T438/T454-T457 + bao cao bug 048-051 vao git, them muc Mo ta + xac nhan DONE + docs` |
| Số file | 11 (đều `A` — thêm mới, 1014 dòng insert) |
| CAS ref `truyen-dang-the-pho-clean` | OK ở lần thử 1 (ref = parent trước khi ghi) |
| `dup:ids` | `[OK] Không có task ID trùng thật.` (5 INFO X-superseded + 1 INFO docs gắn task T199 — hợp lệ) |
| Index thật (`git diff --cached --name-status`) | rỗng sau khi `git add` tường minh 11 đường dẫn (xem lưu ý 1) |

Ghi chú: HEAD đã dịch từ `9bf4c021` (lúc khảo sát đầu) sang `a96d7308` ngay trước commit do phiên khác commit — đúng quy tắc đọc parent mới nhất.

## Danh sách 11 file (đúng như Bước 3)

| # | File | Thay đổi |
|---|---|---|
| 1 | `tasks/T454-namevi-places-suffix-huy-cleanup.md` | THÊM mục `## Mô tả` + `### Trạng thái hiện tại` + `### Câu hỏi cần Admin quyết` (Q5). Frontmatter không đổi. |
| 2 | `tasks/T455-person-name-vi-standardize-from-dila-catalog.md` | THÊM như trên (Q3a/Q3b/Q3c). |
| 3 | `tasks/T456-home-search-autocomplete-dila-catalog.md` | THÊM như trên (Q1 Gate 0, Q4a, Q4b). |
| 4 | `tasks/T457-dila-biographies-nexus-import.md` | BỔ SUNG vào mục `## Mô tả` có sẵn: `### Trạng thái hiện tại` + `### Câu hỏi cần Admin quyết` (Q2a/Q2b/Q2c). Không đổi status/done_when/nội dung cũ. |
| 5 | `tasks/backup/T436-bug049-etl-pass-button-error.md` | Không sửa — dòng "Admin xác nhận DONE (2026-10-26)" đã có sẵn (dòng 80). |
| 6 | `tasks/backup/T437-bug050-namevimap-stuck-loading.md` | Không sửa — đã có (dòng 189). |
| 7 | `tasks/backup/T438-bug051-places-lineage-arrows-missing.md` | Không sửa — đã có (dòng 59). |
| 8 | `docs/T435_BUG048_FINAL_REPORT.md` | Chỉ đọc (commit nguyên, thêm mới). |
| 9 | `docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md` | Chỉ đọc. |
| 10 | `docs/T436_T437_VERIFY_FIX_REPORT.md` | Chỉ đọc. |
| 11 | `docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md` | Chỉ đọc. |

Không đổi `docs/tasktodo.md`, `docs/ROLLBACK.md`, `app.py`, `index.html`.

## Tóm tắt 3 mục `## Mô tả` đã thêm

- **T454** — Làm sạch 8 dòng `namevi_map_places.name_vi` có hậu tố "_ Huý"/"_ Ngoa" (sinh từ T453). Trạng thái: đã đo 8 dòng (mode=ro, 2026-10-22), kế hoạch trong n4-plan; chưa truy vết nguồn, chưa đề xuất sửa, chưa ghi DB. Chờ Q5.
- **T455** — Chuẩn hoá `people.name_vi` (ZQLOCAL=5): 794 lệch (CSV `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv`) + 532 sót chữ Hán. Trạng thái: chỉ có bằng chứng, chưa phân loại/sửa, chưa ghi DB. Chờ Q3a/Q3b/Q3c.
- **T456** — Autocomplete ô Search HOME (`/daoanh/api/public/suggest`, 3 nhóm kinh/người/địa danh). Trạng thái: chưa code; **bị chặn bởi Gate 0** (code backend DILA của T453 chưa từng commit, chỉ còn trong backup T445-coder; DB đủ bảng 5.747/5.589/765). Chờ Q1, Q4a, Q4b.

## Lưu ý / cảnh báo (phải đọc)

1. **Index thật từng lệch**: sau khi commit qua index tạm, `git diff --cached` trên index thật hiện 11 dòng `D` (index thật còn ở tree cũ). Đã xử lý bằng `git add --` tường minh đúng 11 đường dẫn (nội dung worktree = HEAD), không reset, không đụng file khác. Hiện index thật rỗng.
2. **Mâu thuẫn trạng thái T453 — KHÔNG ghi thành "đã xác nhận"**: yêu cầu ghi "T453 (A)+(B) đã được Admin xác nhận theo bản ghi 2026-10-25". Kiểm tra thực tế `tasks/T453-dila-catalog-a-import-vi.md`: (A) Admin duyệt 2026-10-22 05:54, (B) duyệt 06:01 — đúng; nhưng bản ghi mới nhất 2026-10-25 18:33 chỉ là "giao Tester xem Done chưa", và dòng 25 ghi "Admin chưa xác nhận DONE". Vì vậy T457 ghi: (A)+(B) đã duyệt, chưa xác nhận DONE. Nếu Admin muốn ghi khác, cần Admin xác nhận rõ.
3. **`docs/tasktodo.md` dòng 12 (worktree WIP) còn ghi "(B) chờ duyệt"** — cũ, chưa đồng bộ. Không sửa (ngoài scope).
4. **Cây làm việc còn nhiều thay đổi chưa commit của phiên khác** (hàng trăm `D` trong `tasks/` và vài `M`, cùng các file untracked T440–T472, `tasks/archive_done/`). Không đụng vào; commit này không chứa chúng.
5. **Báo cáo 8–11 không sửa nội dung.** Không phát hiện lỗi ký tự rõ ràng cần ghi nhận thêm (chưa rà soát sâu từng dòng).
6. **Chưa kiểm** commit `b1832c7f` ghi trong yêu cầu (`docs/bugs.md`) — không nằm trong 11 file, không tác động commit này.
7. `commit_batch2.py` (cùng thư mục này) là script đã chạy để tạo commit; nó chưa được commit và nên giữ làm vết.

## Kiểm chứng nhanh

```
git show --stat 78418dfe  -> 11 files changed, 1014 insertions(+)
git rev-parse HEAD        -> 78418dfe5aa48a67738c7dfad4ee1370dc41f2fa
git diff --cached --name-status (index thật) -> (rỗng)
python -X utf8 scripts/build_progress_data.py --check-dup-ids -> [OK] Không có task ID trùng thật.
```

Không push. Không sửa DB/TTL. Không sửa code.

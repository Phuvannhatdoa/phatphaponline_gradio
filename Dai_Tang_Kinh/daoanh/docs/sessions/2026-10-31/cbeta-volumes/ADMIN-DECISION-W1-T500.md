# Đề xuất cần Admin quyết: W1 — file cho 3 work nhiều tập (T500)

Liên quan: `tasks/T500-cbeta-catalog-volume-relations.md`, báo cáo QA `docs/qa_reports/QA-2026-10-31-T500.md`.

## Vấn đề

Bảng `volume_files` ghi mỗi quyển nằm trong file XML nào. Ba work X0714, L1557, GA0037 có quyển xuất hiện ở hai file XML cục bộ, nên không thể tự chọn file đúng bằng XML.

Số liệu đã kiểm (đọc DB ở chế độ chỉ đọc và đối chiếu `volume_files_conflicts.csv`):

| Work | Quyển trùng (có ở 2 file XML) | File DB hiện tại | File đang trùng trong XML |
|---|---|---|---|
| X0714 | 3 | X39n0714 | X39n0714, X40n0714 |
| L1557 | 17, 34, 51 | L130n1557 (toàn bộ 80 quyển) | L130–L133n1557 |
| GA0037 | 2 | GA036n0037 | GA036n0037, GA037n0037 |

- **5 quyển trùng** là vấn đề thật. Chưa có quy tắc nào để chọn file cho 5 quyển này.
- **64 dòng còn lại** của 3 work này không trùng: mỗi quyển chỉ có một file trong XML, nhưng file đó khác với file DB đang ghi. Đây là các dòng có trong `volume_files_fix_proposal.csv`.

Phương án A (Admin đã phê chuẩn trước đó) giữ file theo danh mục API cho cả 3 work. Vì vậy 64 dòng này đang lệch so với XML, và trang tác phẩm sẽ hiển thị file của tập đầu cho các quyển thuộc tập khác.

## Các phương án

**Phương án 1 — Giữ nguyên theo phương án A (không ghi DB thêm)**
- Ưu: không có thay đổi DB mới; khớp với danh mục CBETA (API).
- Nhược: 64 dòng vẫn lệch XML; trang tác phẩm hiển thị sai file cho các quyển thuộc tập khác.
- Hoàn tác: không cần.

**Phương án 2 — Sửa 64 dòng không trùng theo XML, giữ 5 quyển trùng theo API (khuyến nghị)**
- Ưu: mỗi quyển không trùng có đúng một file theo XML, nên sửa là chắc chắn; 5 quyển trùng vẫn giữ file của API, không đoán.
- Nhược: ghi DB thêm một lần, cần sao lưu và transaction; 5 quyển trùng vẫn cần ghi chú là chưa xác định.
- Cách làm: sao lưu `lineage.db` trước; `UPDATE` 64 dòng theo `volume_files_fix_proposal.csv` đã lọc 3 work; kiểm số dòng và rollback nếu lệch; ghi 5 quyển trùng vào ghi chú.
- Hoàn tác: khôi phục từ bản sao lưu, hoặc đảo `UPDATE` theo cột `file_hien_tai` trong CSV.

**Phương án 3 — Sửa cả 5 quyển trùng theo một quy tắc chọn file**
- Ưu: không còn dòng nào lệch XML.
- Nhược: cần Admin chọn quy tắc (ví dụ file có tiêu đề chính, hoặc file có số thứ tự nhỏ nhất). Đây là quyết định nghiệp vụ; agent không tự chọn được.
- Hoàn tác: như phương án 2.

## Khuyến nghị

**Phương án 2.** Với 64 dòng không trùng, XML cho đáp án rõ ràng, nên sửa là đúng. Với 5 quyển trùng, không có bằng chứng đủ để chọn file, nên giữ theo API và ghi chú là chưa xác định. Phương án 3 chỉ nên làm khi Admin có quy tắc nghiệp vụ rõ.

## Admin cần trả lời

Chọn một: **1**, **2** (khuyến nghị), hoặc **3** kèm quy tắc chọn file cho 5 quyển trùng.

Việc này chỉ thực hiện sau khi Admin chọn. Việc ghi DB cần duyệt riêng (HARNESS_WORKFLOW §3).

## Kết quả quyết định
- Admin chọn **phương án 2** (2026-10-31). Đã thực hiện: 64/64 dòng khớp XML; 5 quyển trùng giữ theo API.
- Backup: `data/backups/lineage_pre_t500_w1_20261031_215527.db`. Chi tiết hoàn tác: `docs/ROLLBACK.md`.

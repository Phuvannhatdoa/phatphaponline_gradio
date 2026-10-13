---
name: daoanh-task
description: Điều phối công việc trong dự án Đạo Ảnh qua harness: giao agent (daoanh-debugger, tich-hop), QA độc lập bằng daoanh-qa, từ task đến khi Admin xác nhận DONE. Dùng khi người dùng nói "Bug verify: BUG-<mã>: <triệu chứng>" (kích hoạt daoanh-debugger để xác minh bug rồi daoanh-qa kiểm chứng), "điều phối qua harness", "QA bằng daoanh-qa", "điều phối", "sửa bug", "tiếp tục T<số>", "xử lý task", "list task undone", "task nào fix được ngay", "thêm tính năng trong daoanh", "tích hợp nguồn", hoặc kiểm tra lại sau khi sửa. Không dùng cho câu hỏi thuần túy không cần sửa hay điều phối.
---

# Đạo Ảnh — Điều phối task

Skill này quyết định ai làm gì và theo thứ tự nào. Việc sửa code do agent chuyên trách đảm nhận. Skill này không tự sửa code trừ khi cần một bước nhỏ như ghi file task.

Mọi đường dẫn bên dưới tương đối với `daoanh/`.

## Bước 0 — Phân loại yêu cầu

| Yêu cầu | Đi theo |
|---|---|
| Bug về dữ liệu, tên hiển thị, đồ thị, truyền thừa, citation, timeline, map, UI | Nhánh **Sửa bug** |
| Thêm nguồn dữ liệu mới (repo, dataset, API) | Agent `tich-hop` |
| Chỉ kiểm tra lại, không sửa | Agent `daoanh-qa` |
| Kiểm tra logic truyền thừa | Skill `lineage-audit` |
| Không rõ | Hỏi một câu duy nhất để phân loại |

## Nhánh Sửa bug

Quy trình này bắt buộc vì admin đã yêu cầu: mô tả bug phải được ghi trước khi sửa, và không đánh DONE khi chưa có xác nhận.

1. **Ghi mô tả bug trước khi sửa.** Tạo hoặc cập nhật `tasks/T<id>-<slug>.md` với frontmatter (`id`, `title`, `status: in_progress`, `created`, `updated`, `done_when`). Thân file ghi: triệu chứng, route/tab/case tái hiện, nguyên nhân nghi ngờ, phạm vi dự kiến. Không sửa code ở bước này.
2. **Backup trước khi sửa.** Copy từng file sẽ đổi vào `docs/sessions/YYYY-MM-DD/`, giữ nguyên tên. Đây là quy tắc trong `CLAUDE.md`.
3. **Sửa code.** Giao cho `daoanh-debugger` với prompt gồm: tab + route/case + triệu chứng + mục tiêu + đường dẫn file task. Agent này chỉ sửa phạm vi đã ghi.
4. **Kiểm chứng.** Giao cho `daoanh-qa` với task id và danh sách file đã sửa. Nếu QA báo CHƯA ĐẠT, quay lại bước 3 với lỗi cụ thể. Tối đa hai vòng. Quá hai vòng thì dừng và báo admin.
5. **Báo cáo cho admin và hỏi xác nhận.** Tóm tắt những gì đã sửa, bằng chứng QA và phần chưa kiểm tra được. Hỏi rõ: "Admin xác nhận task này DONE chưa?"
6. **Chỉ sau khi admin xác nhận** mới đổi `status: done` trong file task và cập nhật `updated`. Sau đó chạy `python scripts/build_progress_data.py`.

Nếu admin chưa xác nhận, giữ `status: in_progress` và dừng ở đó.

## Quy tắc không được vi phạm

- **Không git:** không chạy `git add`, `commit`, `reset`, `push` nếu chưa có lệnh rõ ràng từ người dùng. Repo có index bất thường.
- **Không deploy VPS** (`158.220.106.183`) và không đổi schema DB mà chưa được xác nhận.
- **Xóa dữ liệu lớn hoặc force push:** luôn hỏi trước.
- **Test local:** dùng `http://127.0.0.1:<port>`, không dùng `localhost` (Windows ưu tiên IPv6).
- **Tên Việt:** nguồn ZQLOCAL (source_id=5). Không gán cho nguồn DILA (source_id=1).
- **Bảng có thể thiếu trên VPS:** bọc truy vấn trong `try/except` để trang vẫn render khi bảng chưa có.

## Trả lời người dùng

Kết thúc bằng một khối ngắn:

```
Task: T<id> — <trạng thái: in_progress / chờ xác nhận / done>
Đã sửa: <danh sách file>
QA: <ĐẠT / CHƯA ĐẠT / KHÔNG KIỂM ĐƯỢC> — <một câu>
Cần admin: <xác nhận DONE / quyết định khác, hoặc "không">
```

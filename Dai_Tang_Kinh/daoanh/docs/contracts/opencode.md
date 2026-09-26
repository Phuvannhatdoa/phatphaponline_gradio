Từ thời điểm này, khi chuyển từ bước PLANT sang BUILD trong project
/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
bạn phải tuân thủ các quy tắc sau:

Ghi log cho MỖI task vào docs

Mỗi task BUILD (một yêu cầu tôi đưa ra) phải được ghi lại vào file trong thư mục:

text
/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/docs/sessions

Nếu thư mục docs/ hoặc docs/sessions/ chưa tồn tại, hãy tự tạo.

Với mỗi task, tạo hoặc cập nhật một file Markdown, tên dạng:

text
docs/sessions/YYYY-MM-DD_task_slug.md

Trong file đó, bắt buộc có các phần:

Mô tả ngắn task (tóm tắt từ yêu cầu tôi vừa gửi).

Thiết kế/giải pháp bạn đã chọn (schema, pipeline, cấu trúc file code).

Danh sách file/code/bảng SQLite đã được tạo/sửa.

Cách chạy/test (lệnh cụ thể).

Ngoài file session, nếu có thay đổi:

Schema DB → cập nhật thêm vào docs/db_schema.md.

Pipeline ETL → cập nhật thêm vào docs/pipelines.md.

Luồng dịch → cập nhật thêm vào docs/translation_workflow.md.

Thực hiện task BUILD như bình thường

Viết code, chỉnh SQL, tạo bảng… theo spec PLANT đã chốt.

Không tạo bảng/schema mới mà không ghi lại trong docs/.

Sau khi code xong: chạy test + log kết quả

Chạy các lệnh test cần thiết (unit test, script kiểm tra, lệnh sqlite3 SELECT demo…).

Ghi rõ kết quả test (pass/fail, lỗi gì nếu có) vào file session của task đó trong docs/sessions/....

Sau khi cập nhật Git

Commit code và docs với message ngắn gọn (ví dụ: feat: add cbeta-dila pipeline + docs).

Sau khi git push xong, hãy:

Tóm tắt lại cho tôi:

Task nào đã DONE.

File nào thay đổi.

Cách chạy test.

Xem như “alert bip bip” báo tôi biết là đã hoàn tất task.

Nguyên tắc chung

Mỗi khi tôi đưa một task mới, trước khi BUILD bạn phải:

Đọc nhanh lại các file trong:

text
/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/docs

đặc biệt là: overview.md, db_schema.md, pipelines.md, translation_workflow.md, để bảo đảm thiết kế mới không phá vỡ kiến trúc hiện tại.

Mục tiêu: chỉ cần đọc docs/ (đặc biệt là docs/sessions/*.md), admin/dev mới có thể hiểu workflow và lịch sử task, không cần hỏi tôi.
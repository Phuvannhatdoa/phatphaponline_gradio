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

đặc biệt là: overview.md, db_schema.md, pipelines.md, translation_workflow.md, roadmap.md, progress.md, để bảo đảm thiết kế mới không phá vỡ kiến trúc hiện tại.

Mục tiêu: chỉ cần đọc docs/ (đặc biệt là docs/sessions/*.md), admin/dev mới có thể hiểu workflow và lịch sử task, không cần hỏi tôi.

## 6. Liên hệ ROADMAP & Báo cáo tiến độ

Mỗi session PLANT/BUILD trong dự án `daoanh` PHẢI:

1. **Đọc ROADMAP** trước khi PLANT
   - Trước khi bắt đầu PLANT cho một task mới, phải mở và đọc file:
     `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/docs/roadmap.md`
   - Mục đích: hiểu task này thuộc phần nào trong kế hoạch dài hạn (nguồn nào, khoá nào).

2. **Gắn task vào ROADMAP trong session log**
   - Với mỗi task, tạo file session mới trong `docs/sessions/` (nếu chưa có):
     `docs/sessions/YYYY-MM-DD_task_slug.md`
   - Bên trong file session, PHẢI có mục:
     ```markdown
     ## Liên hệ ROADMAP
     - Nguồn liên quan: (ví dụ) DILA / CBETA / TTL VN / GeoNames / Marcus SNA / Hạ tầng docs.
     - Khoá ROADMAP:
       - (ví dụ) "Khoá 1 – Xong core Hán → Việt" hoặc
       - "Khoá 2 – Lên VN" hoặc
       - "Khoá 3 – Mở rộng thế giới".
     - Dòng ROADMAP tương ứng:
       - (trích nguyên văn 1–2 dòng từ `docs/roadmap.md` mô tả phần việc liên quan)
     ```
   - Nếu task chạm nhiều nguồn/khoá, liệt kê 2–3 dòng, rõ ràng.

3. **Cập nhật file tổng tiến độ (PROGRESS)**
   - Sau khi hoàn thành một task BUILD, phải cập nhật hoặc tạo file:
     `docs/progress.md`
   - Trong file này, giữ dạng tổng hợp tiến độ theo ROADMAP, ví dụ:
     ```markdown
     # Tiến độ theo ROADMAP
     Cập nhật: YYYY-MM-DD

     ## DILA
     - Trạng thái: (ví dụ) Đã import chủ yếu person/place; đang mapping với CBETA qua canon_citations.
     - Task gần nhất: (link tới docs/sessions/...)

     ## CBETA
     - Trạng thái: ...
     - Task gần nhất: ...
     ```
   - Khi cập nhật, có thể ghi đè phần cũ bằng trạng thái mới nhất. Luôn ghi ngày cập nhật ở đầu file.

4. **Báo cáo ngắn cho admin sau mỗi task**
   - Sau khi hoàn thành task và cập nhật `docs/sessions/...` + `docs/progress.md`, trong câu trả lời cho admin phải có đoạn:
     - Task đã làm gì (1–3 gạch đầu dòng).
     - Liên hệ ROADMAP: (nguồn, khoá).
     - Link tới file session log.
     - Nếu có thay đổi đáng kể về trạng thái (ví dụ "CBETA PERSON matching: 50% done"), phải nói rõ.
   - Mục tiêu: admin đọc câu trả lời + mở `docs/progress.md` là nắm được mình đang ở đoạn nào trên ROADMAP để phân bổ nguồn lực.
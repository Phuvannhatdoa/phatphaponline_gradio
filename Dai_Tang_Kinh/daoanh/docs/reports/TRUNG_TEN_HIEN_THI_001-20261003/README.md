# TRUNG_TEN_HIEN_THI_001 — nhãn kết quả nhân vật

Đã sửa admin/search_all.html: mỗi nhân vật có nhãn gồm tên Việt, chữ Hán và triều đại. API đang trả triều đại trong district; formatter ưu tiên dynasty_vi/dynasty nếu có, sau đó district. Chỉ Việt hóa nhãn hiển thị Đông Tấn/Đường/Bắc Tống từ giá trị Hán tương ứng; các giá trị khác giữ nguyên. Thiếu triều đại ghi rõ chưa rõ, ID vẫn hiển thị. Địa danh giữ cách hiển thị cũ.

| DILA ID | Nhãn |
|---|---|
| A002201 | Tuyết Đậu Pháp Nhã – 法雅 (Đông Tấn) |
| A006731 | Tuyết Đậu Pháp Nhã – 法雅 (Đường) |
| A020536 | Tuyết Đậu Pháp Nhã – 雪竇法雅 (Bắc Tống) |

Chromium đã gõ truy vấn Tuyết Đậu, kiểm nhãn và click cả ba ID; cả ba đúng, 0 page errors. Xem browser-result.json và search-results.png. useEffect tìm kiếm giữ nguyên byte-for-byte; không đổi endpoint, debounce, danh sách kết quả, href hoặc backend/DB. Snapshot API: api-response.json.

Bản sửa chỉ trình bày kết quả; không chứng nhận ba tên Việt gán cho các ID là chính xác học thuật. Có kết quả khác ID rỗng từ API; chưa sửa vì ngoài phạm vi chỉ hiển thị. Pipeline: xem pipeline.log và validation.json, không suy kết quả chung từ browser PASS.

Rollback: từ daoanh chạy python -X utf8 data/backups/TRUNG_TEN_HIEN_THI_001-20261003/revert.py. Guard hash ngăn ghi đè sửa tiếp. Skill dùng: vercel-react-best-practices; formatter đơn giản ở ngoài App, không thêm effect/fetch/memo/dependency.

Kết quả cuối: bug UI PASS đủ3nhãn/3click. Pipeline exit1 tại T203 (25PASS/2FAIL):5TTL khác có40 ký tự Ð; corpus1045parseOK nhưng test tổng đánhFAIL. Không chỉnh dữ liệu để làm xanh pipeline vì Admin yêu cầu chỉ đổi cách hiển thị.

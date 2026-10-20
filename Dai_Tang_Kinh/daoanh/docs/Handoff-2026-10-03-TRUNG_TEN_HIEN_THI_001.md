# Handoff — TRUNG_TEN_HIEN_THI_001 (2026-10-03)

## 1. Thông tin đọc nhanh

Bug trình bày đã sửa. Chỉ admin/search_all.html đổi; không chỉnh DB, API hay truy vấn. Browser 3 nhãn + 3 click PASS, 0 page errors; ảnh đã kiểm trực quan. API trước/sau giống nhau. Trạng thái pipeline cuối ở reports/TRUNG_TEN_HIEN_THI_001-20261003/validation.json. Phiên này không stage/commit; HEAD có thể do session khác thay đổi.

## 2. Đọc trong 2 phút

Nhân vật giờ có tên Việt – chữ Hán (triều đại), ID vẫn hiển thị. A002201 Đông Tấn; A006731 Đường; A020536 Bắc Tống. Ctrl+F5 trang search_all và gõ Tuyết Đậu. Click vẫn mở ba ID khác nhau. Không sửa tên gốc hoặc gộp ba người.

## 3. Thay đổi và bằng chứng

Formatter personResultLabel đặt ngoài App, dùng dữ liệu đang có. API trả dynasty qua district; hỗ trợ dynasty_vi/dynasty nếu có. Nhãn Việt hóa ba triều đại đã nêu, triều đại khác giữ nguyên và thiếu thì ghi chưa rõ. Nhánh địa danh giữ nguyên. useEffect giữ nguyên byte-for-byte. Snapshot api-response.json; browser-result.json có nhãn và URL click. Skill vercel-react-best-practices: biểu thức đơn giản, không thêm fetch/effect/memo.

## 4. Quy tắc cần biết

Workspace nhiều session. Không commit/stage file chung bừa. admin/search_all.html bị Windows chặn ghi thường; đã dùng WriteAllText sau guard so bản trước. Bug này không xác minh tên Việt của các ID về mặt học thuật. API còn trả một nhân vật ID rỗng; ngoài phạm vi chỉ trình bày nên giữ nguyên.

## 5. Revert

Từ daoanh: python -X utf8 data/backups/TRUNG_TEN_HIEN_THI_001-20261003/revert.py

Script kiểm SHA256 sau sửa, dừng nếu file bị sửa tiếp. Khôi phục một template, mất bản sửa UI của phiên này; DB và raw không đổi.

## 6. File tạo/sửa

- admin/search_all.html: formatter và nhánh nhãn nhân vật.
- data/backups/TRUNG_TEN_HIEN_THI_001-20261003/: before, manifest, revert guard.
- docs/reports/TRUNG_TEN_HIEN_THI_001-20261003/: API snapshot, browser check/evidence, ảnh, pipeline log, README, validation.
- docs/sessions/2026-10-03-TRUNG_TEN_HIEN_THI_001.md; Handoff này; tasktodo log tiếp nối.

## 7. Sai lầm và bài học

Ban đầu có thể tưởng template thiếu Hán; đọc thực tế thấy Hán và district đã hiện, nhưng triều đại chưa nằm trong nhãn tên. Sửa cách nhóm thông tin, không sửa search. Không đồng nhất field district là địa lý cho nhân vật; backend đang dùng nó cho dynasty. Không cần query thêm mỗi kết quả.

## 8. Chưa xong

Bug có đủ acceptance evidence. Pipeline chung ghi riêng; không suy browser PASS là toàn hệ thống PASS. Các vấn đề ánh xạ tên Việt trùng hoặc ID rỗng cần task dữ liệu có nguồn DILA, chưa xử lý trong bug này. Không có câu hỏi Admin bắt buộc để dùng bản sửa.

## 9. Kiểm nhanh

Mở http://localhost:8080/daoanh/admin/search_all.html, Ctrl+F5, gõ Tuyết Đậu. Kiểm ba nhãn và ID. Hoặc từ daoanh chạy node docs/reports/TRUNG_TEN_HIEN_THI_001-20261003/verify-browser.cjs (mock kiểm phiên, chỉ đọc dữ liệu). Xem browser-result.json và validation.json.

## 10. Agent tiếp theo

Giữ sửa ở frontend khi mục tiêu là phân biệt kết quả; không sửa DB từ hiện tượng tên giống. Kiểm source/manifest trước ghi, tôn trọng session khác. Không thêm effect hoặc lookup từng dòng chỉ để trình bày triều đại đã có. Ghi session sau build; pipeline có lỗi phải báo đúng nguyên nhân.

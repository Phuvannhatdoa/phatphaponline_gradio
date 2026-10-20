# Handoff — 2026-10-10 — Minh Hải Pháp Bảo: DILA/CBETA/Báo Tư

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái |
|---|---|
| Ngày | 2026-10-10, Asia/Bangkok |
| HEAD đo từ visjs-app | c75d99eca0c2d23dbe927174a11b10a4b4e49261 |
| Yêu cầu đã xử lý | Kiểm lại nhận định không có Minh Hải Pháp Bảo trong DILA/CBETA |
| Loại công việc | Tra cứu, kiểm artifact, lưu báo cáo; không phải build |
| DILA | 49.361 + 19.034 hồ sơ trong hai phiên bản cùng authority |
| CBETA | 5.017 XML, lỗi đọc 0; tìm chuỗi theo từng dòng |
| Tests / preflight | Không chạy pipeline; không báo application PASS |
| DB / TTL / raw XML | Không thay đổi bởi phiên này |
| Task liên quan | T232; không cấp ID mới, không đánh dấu T232 hoàn tất |
| Claude-mem | POST thất bại kết nối; request/result local được giữ |

## 2. Đọc trong 2 phút

Kết luận cần giữ: **chưa xác minh được DILA Authority ID cho Minh Hải Pháp Bảo Chúc Thánh; không đủ căn cứ nói DILA/CBETA hoàn toàn không có thông tin**. A000662 vẫn bị loại trừ; không gắn lại từ trùng 明海.

Đầu mối mới: luận án Thành Công 2015 có mục thân thế tr.133/phụ lục tr.247; nghiên cứu Khoáng Viên 2017 công bố bài ký Báo Tư và phân biệt chùa cũ/chùa mới. Các nguồn, kết quả và giới hạn ở [README](reports/Minh-Hai-source-recheck-20261010/README.md).

Ba hướng tra cứu tiếp theo, không cần quyết định DB lúc này:

1. Đọc toàn văn luận án và truy ảnh/bản Hán trong phụ lục.
2. Xác định đúng Báo Tư cũ/Tân Tự, nguồn địa phương chí và từng niên đại.
3. Lấy bản gốc văn bia Minh Hải, sách khắc 1732, pháp quyển 1847 trước khi duyệt quan hệ/số đời.

## 3. Vấn đề, cách xử lý và chứng cứ

Nhận định vắng thông tin là quá rộng khi phép tìm chỉ quét bản local và chuỗi tên. Đợt này sửa cách diễn đạt trong báo cáo mới; không sửa nội dung tài liệu/DB của phiên khác. Bộ kết quả local-scan.json chứa counts, hash artifact và hồ sơ ứng viên. Luận án và bài nghiên cứu cung cấp hướng mở rộng ngoài authority/kinh tạng.

X0613 local dòng 149 ghi niên đại đề tựa 1630; authority A000662 ghi triều Minh và X0613. Đây là chứng cứ loại trừ, không phải bằng chứng xác lập ID mới.

## 4. Cảnh báo bắt buộc

- Hai artifact DILA không phải hai chứng cứ độc lập; hai thư viện chỉ mục cùng luận án cũng không phải hai nghiên cứu.
- Tìm nguyên chuỗi trên từng dòng XML có thể bỏ sót tag/gaiji/dị thể. Không ghi “không có” từ kết quả zero-hit.
- Báo Tư 報資 khác các chùa 報慈; chùa cũ/Tân Tự cần chứng cứ riêng.
- Worktree có session song song. Không git add cả cây; mọi git chạy từ visjs-app.
- TTL ignored Git; nếu sửa về sau phải dùng backup/rollback đúng quy trình. Phiên này không sửa TTL.

## 5. Revert từng phần

| Phần | Mất dữ liệu? | Cách hoàn tác |
|---|---|---|
| DB / TTL / raw XML | Không | Không có mutation để revert |
| Báo cáo bổ sung | Không ảnh hưởng dữ liệu vận hành | Lưu bản gốc rồi đánh dấu superseded nếu có kết quả mới; không xóa cả docs |
| Script trong report | Không ghi dữ liệu vận hành | Có thể ngừng dùng; không cần revert importer |

Không có commit để git revert của phiên này. Đường dẫn rollback chỉ dành riêng các artifact mới đã liệt kê, không dọn đệ quy thư mục chung.

## 6. File tạo/sửa

| File | Vai trò |
|---|---|
| docs/reports/Minh-Hai-source-recheck-20261010/README.md | Kết luận, nguồn, giới hạn, bước tiếp theo |
| cùng thư mục: local-scan.json / scan_local_sources.py | Kết quả quét nguồn, script đọc tuần tự |
| cùng thư mục: fetch_bao_tu_pdf.py / extract_bao_tu_pdf.py | Tải nguồn công khai và đọc các trang cần thiết |
| cùng thư mục: Bao-Tu-VJOL-2017.pdf / bao-tu-selected-pages.json | Bản nghiên cứu cache để kiểm chứng; không coi là source authority |
| cùng thư mục: artifact-manifest.json | SHA-256/size artifact |
| cùng thư mục: observation-request.json / observation-result.json | Request claude-mem và lỗi kết nối |
| docs/sessions/2026-10-10_Minh-Hai-source-recheck.md | Log phiên |
| docs/Handoff-2026-10-10-Minh-Hai-source-recheck.md | Handoff này |

Không sửa docs/tasktodo.md dùng chung; chỉ đọc phần T232/T233.

## 7. Sai lầm thao tác và bài học

Python -c mất quote qua PowerShell; thay bằng script file. Gọi nhầm store trong node_repl sau khi viết report; kiểm stat/hash xác nhận file đã được ghi trước lỗi, không ghi đè. Web open một số PDF/thư viện thất bại; không xem lỗi truy cập là chứng cứ nguồn không tồn tại. Đã đọc PDF VJOL bằng urllib + pdfplumber local.

Nhận định “không có nguồn” từ “chưa thấy ID” bị bác bỏ về mặt suy luận và đã được chỉnh trong hồ sơ mới. Không tự biến một bài ký hành trạng thành danh sách đủ mọi đệ tử.

## 8. Việc chưa xong

- Toàn văn luận án, ảnh tư liệu gốc, đối chiếu tên/địa điểm/niên đại từng mệnh đề.
- Toàn văn/bản ảnh các địa phương chí liên quan Báo Tư ở Quảng Châu; chưa xác lập mục ghi trực tiếp Minh Hải.
- Tra CBETA sau chuẩn hóa markup và các nguồn/phát hành chưa quét.
- Xây hồ sơ local/identity assertions theo kế hoạch trước; phiên nghiên cứu này không triển khai.
- Claude-mem chưa nhận observation. Khoảng trống là truy cập nguồn và kiểm chứng; không có yêu cầu Admin xác nhận để hoàn tất câu trả lời hiện tại.

## 9. Kiểm tra nhanh

Từ daoanh, đọc log đã lưu, không cần quét lại toàn corpus:

```powershell
python -B -X utf8 -c "import json; from pathlib import Path; d=json.loads(Path('docs/reports/Minh-Hai-source-recheck-20261010/local-scan.json').read_text(encoding='utf8')); print([a['records_scanned'] for a in d['authority']]); print(d['cbeta']['xml_files_scanned']); print(d['cbeta']['errors'])"
```

Kỳ vọng: [49361, 19034], 5017, []. Kiểm artifact-manifest.json nếu nghi ngờ nguồn/log thay đổi. Để tái lập đầy đủ mới chạy scan_local_sources.py; có thể mất vài phút.

## 10. Ghi chú cho agent kế tiếp

- Đọc README trước, rồi kiểm chứng phần cần cập nhật bằng bản gốc.
- Giữ A000662 là different-person đối với Minh Hải Pháp Bảo Chúc Thánh.
- Nguồn hỗ trợ danh tính không tự hỗ trợ mọi quan hệ/số đời.
- Giữ việc thiếu ID dưới dạng chưa xác minh; không tạo mã A giả.
- Nếu thay đổi code về sau, tuân thủ pipeline/tester trước khi yêu cầu review.
- Nếu service 37700 hoạt động trở lại, gửi request đã lưu; hiện chưa có receipt.

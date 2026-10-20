# Phase 3 — Preview cục bộ dữ liệu nguồn Tổ Đường Tập

**Ngày bàn giao:** 2026-10-16. **Phạm vi:** preview độc lập để đọc và đối chiếu quan sát nguồn, dẫn xuất từ sáu artifact Phase 2 đã có.

**Chỉ đọc — chỉ mở tại máy — không công bố công khai — không tích hợp production.** Phase 3 không phê duyệt định danh DILA, không ghi DB/TTL, không đổi nhãn nguồn, không chuyển hệ số đời và không xác nhận quyền tái phân phối. Bốn TEI có khai báo quyền mâu thuẫn; gói preview chứa trích đoạn dẫn xuất từ chúng nên chưa được coi là gói sẵn sàng công bố.

## 1. Mở preview tại máy

Cách đơn giản nhất:

1. Giữ nguyên các file trong thư mục Phase 3.
2. Mở [preview.html](preview.html) bằng trình duyệt trên máy, hoặc kéo file vào cửa sổ trình duyệt. Địa chỉ bắt đầu bằng **file://** được hỗ trợ.
3. Giữ cùng thư mục ít nhất bốn file: preview.html, preview.css, preview.js và preview-data.js. Trình duyệt đọc dữ liệu đã nhúng trong preview-data.js, không cần fetch JSON qua mạng và không cần chạy app.py.

Không cần đăng nhập Admin, khởi động server chính hoặc nhập token. Ba file JSON dẫn xuất vẫn có thể mở riêng để đọc cấu trúc; preview không cung cấp nút import, phê duyệt hoặc xuất bản.

Nếu muốn dùng HTTP tại máy, mở một terminal riêng và chạy:

~~~powershell
Set-Location -LiteralPath 'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\reports\zenodo-10004109-survey-20261016\analysis\phase3'
python -m http.server 8765 --bind 127.0.0.1
~~~

Sau đó mở **http://127.0.0.1:8765/preview.html**. Dừng server này bằng **Ctrl+C** tại chính terminal đã chạy. Nếu cổng đang được dùng, chọn cổng khác cho server loopback; không dừng process của dự án để lấy cổng.

Chỉ bind 127.0.0.1. Không bind 0.0.0.0, không mở firewall/tunnel, không đưa thư mục lên máy chủ công khai và không thêm route vào server production. Kiểm tra origin trong preview.js chỉ giới hạn việc render; nó không thay thế phân quyền máy chủ và không ngăn người khác tải file tĩnh nếu tự đem thư mục ra public.

## 2. Cách đọc và những điều số đếm không chứng minh

| Mục | Số hiện có | Cách hiểu |
|---|---:|---|
| Nhân vật nguồn | 262 | 260 trong CSV và hai chỉ xuất hiện trong các case TEI đã khảo sát; không phải 262 mapping DILA đã duyệt |
| Quan sát quan hệ | 513 | 257 bản GEXF và 256 bản CSV được giữ riêng; không phải 513 quan hệ lịch sử độc lập |
| Cặp graph không phân chiều | 256 | Chỉ là thống kê endpoint của dữ liệu nguồn, không phải số cặp thầy/trò được xác nhận |
| Cặp GEXF có cạnh song song | 1 | Giữ cả hai locator trong cùng nguồn; không tính thành hai nguồn chứng minh độc lập |
| Mã số đời chưa rõ | 3 | CSV ghi “0”, workbook ghi “?”; giữ nguyên cả hai cách mã hóa |
| Đối chiếu nhãn DILA được dẫn lại | 10 | Kết quả do Deep Research cung cấp và root chuyển tiếp trong Phase 2; không nâng thành accepted identity |
| Case TEI | 10 | Phạm vi trích đoạn và đối chiếu cụ thể, không phải khảo sát ngữ nghĩa toàn bộ corpus |
| File TEI có khai báo quyền mâu thuẫn | 4 | Ghi nhận cả khai báo cấp record/thư mục và khai báo trong file; chưa clearance |

Các số trên được đối chiếu lại bằng chế độ verify của builder. Xem [manifest Phase 3](phase3-manifest.json) để biết hash các file ở thời điểm bàn giao.

Các thao tác nên thử:

- **Quan hệ nguồn:** chọn GEXF, CSV hoặc cả hai. Source/Target là vị trí cột/endpoint; graph nguồn khai báo vô hướng, không tự xác định ai là thầy.
- **Xem cạnh song song:** đọc hai locator 0300b07 và 0412a05 của cặp A004166–A000587. Có cảnh báo UUID/locator khác nhau giữa CSV và GEXF; không tự gộp hoặc sửa một bản để làm chúng khớp.
- **Số đời chưa rõ:** đọc ba trường hợp giữ “0”/“?”. Không hiểu 0 là đời gốc và không cộng sang hệ Ma Ha Ca Diếp = 1.
- **Đọc 10 case TEI:** phân biệt thuộc tính XML, lớp biên tập và vai trò được diễn đạt trong văn bản. Thiếu thuộc tính cert không có nghĩa chắc chắn.
- **Quyền sử dụng:** đọc từng file có khai báo mâu thuẫn. Một license cấp record không tự giải quyết mọi notice cấp file.
- **Nhân vật nguồn:** nhãn gốc, nhãn authority được dẫn lại và lớp Việt hóa được đặt riêng. Chưa có mapping Việt được cung cấp trong Phase 1/2; preview không tự dịch để lấp chỗ trống.

## 3. File bàn giao

| File | Vai trò |
|---|---|
| [source_person.json](source_person.json) | Nhãn nguồn, mã đời nguyên văn, hiện diện theo nguồn và kết quả đối chiếu nhãn được dẫn lại |
| [source_relation.json](source_relation.json) | Giữ riêng quan sát GEXF/CSV, endpoint, locator, cảnh báo và tham chiếu chứng cứ |
| [source_evidence.json](source_evidence.json) | Trích đoạn đã có, thuộc tính nguồn, locator, uncertainty và notice quyền theo file |
| preview-data.js | Bản dữ liệu nhúng để mở bằng file://; không phải một nguồn chứng cứ độc lập với ba JSON |
| preview.html / preview.css / preview.js | Giao diện tĩnh; không truy cập API production |
| build_preview_data.mjs | Công cụ dẫn xuất do phiên làm việc tạo, không phải chương trình được tải về từ package |
| test_preview.cjs / test-results.json | Kiểm thử preview và bằng chứng lần chạy đã có |
| desktop-preview.png / mobile-preview.png | Ảnh chụp kiểm tra bố cục; cũng nằm trong phạm vi preview nội bộ |
| build-log.json | Lịch sử build/refresh đã có; không dùng hash output ban đầu thay cho hash bản refresh |
| [reuse-boundary-report.md](reuse-boundary-report.md) | Ranh giới direct reuse / mapping-only / rights-blocked |
| [phase3-manifest.json](phase3-manifest.json) | Hash file hiện tại, đầu vào trực tiếp và hash nguồn được dẫn lại |

## 4. Đầu vào và kiểm chứng

Sáu đầu vào trực tiếp đều ở Phase 2:

- [edge-diff.json](../phase2/edge-diff.json)
- [relation-direction-audit.json](../phase2/relation-direction-audit.json)
- [generation-inventory.json](../phase2/generation-inventory.json)
- [uncertainty-inventory.json](../phase2/uncertainty-inventory.json)
- [rights-matrix.json](../phase2/rights-matrix.json)
- [person-id-audit.json](../phase2/person-id-audit.json)

test-results.json hiện ghi **40/40 PASS**, không có lỗi JavaScript; phạm vi kiểm gồm file://, HTTP loopback, chặn origin ngoài máy, phân trang, bàn phím, bố cục 375px, XSS dưới dạng text và không có request tới API/host từ xa. Đây là bằng chứng của lần chạy UI đã có, không phải xác nhận tính đúng đắn lịch sử hoặc quyền sử dụng.

Trong lượt hoàn thiện tài liệu, builder đã chạy lại **--verify**, exit 0, status PASS. Chế độ này đọc để so sánh bốn output dẫn xuất với sáu input, không ghi lại output. Không chạy lại test UI trong lượt tài liệu vì runner có thể ghi test-results/ảnh.

Nếu cần tự kiểm tra dữ liệu mà không viết file, chạy trong Phase 3:

~~~powershell
node .\build_preview_data.mjs --verify
~~~

Không dùng --write hoặc --refresh như thao tác đọc; chúng có thể tạo hoặc thay output và nằm ngoài công việc bàn giao tài liệu này.

## 5. Giới hạn tái sử dụng

Có thể đọc lại quan sát và locator trong preview theo scope khảo sát hiện tại. Việc sử dụng dữ liệu nguồn trong preview không đồng nghĩa mọi bản ghi đã được duyệt hoặc được phép đưa ra public. Đặc biệt, preview-data.js và source_evidence.json chứa nội dung TEI dẫn xuất nên cùng chịu ranh giới quyền tương ứng, kể cả khi đổi đuôi file hoặc chỉ chia sẻ ảnh chụp.

Nguồn: [Zenodo record 10004109](https://zenodo.org/records/10004109), [DOI record](https://doi.org/10.5281/zenodo.10004109), [DOI bài nghiên cứu](https://doi.org/10.3390/rel14020205). Giữ ghi công Laurent Van Cutsem và vai trò biên tập/lưu trữ của Marcus Bingenheimer theo rights-matrix; không áp license package cho ứng dụng PTDA, dữ liệu DILA/CBETA hoặc tài nguyên khác.

Xem [báo cáo khảo sát ban đầu](../../survey-report.md) và [ranh giới tái sử dụng](reuse-boundary-report.md) trước khi đề xuất bất kỳ bước tích hợp tiếp theo. Tài liệu này không mở scope nhập DB/TTL, sửa Phase 1/2 hoặc công bố dữ liệu.

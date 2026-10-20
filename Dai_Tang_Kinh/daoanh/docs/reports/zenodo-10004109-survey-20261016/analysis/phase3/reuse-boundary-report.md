# Phase 3 — Ranh giới tái sử dụng dữ liệu

**Ngày:** 2026-10-16. **Nguồn đánh giá:** sáu artifact Phase 2 đã đóng băng theo hash; không tra cứu mới hoặc sửa dữ liệu nguồn trong lượt tài liệu.

Ba nhóm dưới đây mô tả mức sử dụng trong quy trình PTDA. **“Direct reuse” không phải một kết luận pháp lý cho phép tái phân phối; “mapping-only” không phải accepted identity; “rights-blocked” không có nghĩa cấm đọc nội bộ trong scope khảo sát đã giao.** Gói Phase 3 hiện chỉ là preview cục bộ, chỉ đọc.

## 1. Có thể dùng trực tiếp trong lớp quan sát nguồn — direct reuse

| Nội dung | Có thể giữ và trình bày ở scope hiện tại | Điều không được suy thêm |
|---|---|---|
| Nhãn, ID và thuộc tính nguyên văn của node | Giữ source_label, ID nguồn, file/bản ghi/dòng; lớp Việt hóa riêng | ID có dạng DILA hoặc nhãn giống nhau chưa chứng minh đúng cùng nhân vật |
| 257 quan sát GEXF và 256 quan sát CSV | Giữ hai bản dữ liệu riêng, 513 quan sát, locator và raw fields | Không xem hai serialization là hai nguồn độc lập; không dùng số 513 làm số quan hệ đã duyệt |
| Cặp graph và tính vô hướng | Trình bày endpoint và khai báo graph như nguồn | Không đổi Source/Target thành teacher/student hoặc dharmaTeacherOf |
| Giá trị số đời nguyên văn | Giữ chuỗi CSV, workbook và group; đánh dấu ba bất đồng “0”/“?” | Không coi 0 là số đời chắc chắn, không cộng 37 hoặc đổi sang hệ đếm khác |
| Locator, notice, cert và metadata biên tập đã trích | Giữ attribution, file, dòng/ô, qualifier và lớp supplied khi có | Không mặc định thiếu cert là chắc chắn hoặc gom lớp biên tập vào bản văn gốc |
| Kết quả đối chiếu và cảnh báo Phase 2 | Dẫn lại phương pháp, phạm vi, timestamp và tình trạng kết quả | Không tự biến quan sát/lookup thành quyết định accepted |

Đây là tái sử dụng thông tin ở **lớp source observation** để admin đọc và kiểm tra. Khi một file không có notice bổ sung trong khảo sát, chỉ có thể nói “chưa tìm thấy notice bổ sung trong phạm vi kiểm”; không được suy ra đã có clearance cho mọi loại sử dụng.

## 2. Chỉ được làm ứng viên ánh xạ — mapping-only

### 2.1. Nhân vật và tên

Mười đối chiếu nhãn DILA trong person-id-audit.json là kết quả do Deep Research cung cấp, được root chuyển tiếp và ghi trong artifact. Preview giữ cả nhãn nguồn lẫn primary/alias được báo cáo, không gọi API DILA mới và không thay source_label bằng kết quả đó.

Một ID có dạng Axxxxxx, HTTP 200 hoặc nhãn tương đồng không đủ để phê duyệt đồng nhất. Cần đối chiếu hồ sơ authority, biệt danh, niên đại/ngữ cảnh và chứng cứ thuộc đúng người. Hiện chưa có mapping Việt được cung cấp; mapping_layer.records rỗng. Không tự tạo tên Việt hoặc owl:sameAs từ trạng thái trống này.

### 2.2. Quan hệ và văn bản

Graph GEXF/CSV được giữ là **undirected**. Các vai trò có trong 10 case TEI là chứng cứ ở cấp đoạn văn và lớp biên tập tương ứng, không tự chuyển thành quan hệ truyền pháp cho toàn bộ graph. Những locator chưa có trích đoạn trong Phase 1/2 phải hiện “chưa trích”, không dựng văn bản để lấp chỗ trống.

Cặp A004166–A000587 có hai quan sát GEXF với locator 0300b07 và 0412a05. Có bản CSV mang UUID/locator không thống nhất với GEXF; cả hai ngữ cảnh đã được giữ để review. Không tự chọn bản thắng, gộp cạnh hoặc tính hai đoạn trong cùng nguồn thành hai căn cứ lịch sử độc lập.

### 2.3. Số đời và bất định

Ba trường hợp CSV “0” / XLSX “?” là encoding chưa rõ, không phải số cần tự sửa thành 1. Giữ nguyên hệ đếm của nguồn. Việc đổi số đời hoặc quy đổi hệ đếm cần lập luận về chính hệ đếm và ít nhất ba gốc chứng cứ độc lập theo quy tắc dự án; phép cộng từ đời thầy không thay được chứng cứ.

Các qualifier TEI, bao gồm cert=low, được giữ riêng với graph. Không chép một qualifier sang các cạnh khác chỉ vì trùng endpoint; cũng không xóa qualifier vì graph không có cột cert.

## 3. Chưa được phát hành theo một license đã chốt — rights-blocked

[Rights matrix Phase 2](../phase2/rights-matrix.json) ghi nhận:

- Record/thư mục: khai báo **CC BY 4.0**.
- Bốn TEI: notice riêng khai báo **CC BY-NC-SA 4.0**.
- Chưa có quyết định clearance theo từng file; không dùng metadata cấp archive để ghi đè notice cấp file.

| File TEI | Tình trạng |
|---|---|
| 03-zutangji-haidongxinkaiyinbanji_SNA.xml | MIXED_DECLARATIONS |
| 03-zutangji-zutangjixu_SNA.xml | MIXED_DECLARATIONS |
| 03-zutangji_supp_SNA_caotang.xml | MIXED_DECLARATIONS |
| 03-zutangji_supp_SNA_xinghua.xml | MIXED_DECLARATIONS |

Bốn file đều thuộc thư mục extracted/vancutsem_laurent của khảo sát. Hai khai báo cần được giữ nguyên và làm rõ trước kiểu sử dụng/phân phối đòi hỏi một bộ điều khoản đã xác định. Báo cáo này không tự chọn một license để giải quyết mâu thuẫn, không áp license lên toàn dự án và không đưa ra clearance pháp lý.

**Ranh giới lan truyền tới gói dẫn xuất:** source_evidence.json, các record có tham chiếu TEI trong source_relation.json, preview-data.js và ảnh preview có thể chứa nội dung hoặc ngữ cảnh lấy từ TEI. Đổi sang JSON/JavaScript/ảnh chụp không tự loại bỏ ranh giới quyền. Vì vậy, giữ toàn gói Phase 3 ở máy nội bộ; không đưa nguyên thư mục lên GitHub Pages, server public hoặc tải lên kho công khai.

CSV/GEXF/XLSX được ghi nhận khai báo cấp thư mục/record, nhưng việc chưa thấy notice khác không tự thành clearance cho một bản release kết hợp. Mọi release tương lai cần kiểm selected files, attribution, notice, phần dẫn xuất và quyền của các nguồn bên thứ ba. License của package không cấp quyền đối với DILA Authority, CBETA hoặc dữ liệu production của PTDA.

## 4. Những gì Phase 3 đã làm và chưa làm

| Đã có | Chưa thực hiện / chưa được suy ra |
|---|---|
| Ba JSON source_person/source_relation/source_evidence và bundle preview cục bộ | Chưa nhập DB/TTL hoặc sửa schema production |
| Nhãn gốc, số đời raw, locator, uncertainty, cảnh báo UUID/parallel | Chưa sửa giá trị nguồn, gộp người/cạnh hoặc chuyển hệ đếm |
| Dẫn lại 10 đối chiếu nhãn authority có attribution | Chưa accepted mapping hoặc xác minh toàn bộ 262 nhân vật |
| Trích đoạn đã có trong Phase 1/2 | Chưa thu thập thêm đoạn văn hoặc dùng LLM sinh văn bản thiếu |
| UI chỉ đọc, không approve/import/export | Chưa có workflow phê duyệt production |
| test-results.json ghi 40 kiểm tra PASS, không lỗi JS | Chưa chứng nhận sự thật lịch sử hoặc clearance quyền |
| Builder --verify PASS trong lượt tài liệu | Không chạy --write/--refresh; không sửa output hoặc Phase 1/2 |

## 5. Điều kiện cho một đề xuất tái sử dụng tiếp theo

1. Chỉ rõ mục đích: đọc nội bộ, mapping candidate, nghiên cứu, hay phát hành; xác định tập file và phần nội dung cần dùng.
2. Đóng băng version/hash và giữ DOI/URL, tác giả/biên tập viên, notice, disclaimer cùng mô tả biến đổi.
3. Làm rõ quyền cho bốn TEI và quyền của nguồn bên thứ ba khi phạm vi sử dụng cần clearance. Không tự mở public export.
4. Review mapping, ngữ nghĩa quan hệ và hệ đếm riêng với việc review quyền. Tình trạng license không chứng minh thông tin lịch sử là đúng, và thông tin đúng không tự cho phép tái phân phối.
5. Nếu được giao bước tích hợp riêng, chuẩn bị staging, logical diff, backup/rollback và kiểm độc lập trước khi có bất kỳ thay đổi production nào.

Không có bước nào trong danh sách trên đã được tự mở hoặc thực thi bởi tài liệu này. Đọc [README mở preview](README.md), [manifest](phase3-manifest.json), [khảo sát ban đầu](../../survey-report.md) và [rights matrix](../phase2/rights-matrix.json) để tiếp tục đúng phạm vi.

**Ghi công được dẫn từ Phase 2:** Laurent Van Cutsem; vai trò biên tập/lưu trữ Marcus Bingenheimer. [Zenodo record](https://zenodo.org/records/10004109), [DOI dữ liệu](https://doi.org/10.5281/zenodo.10004109), [DOI bài nghiên cứu](https://doi.org/10.3390/rel14020205). Đây là thông tin nguồn, không phải license mới cho PTDA.

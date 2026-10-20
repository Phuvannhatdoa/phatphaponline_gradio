# Minh Hải Pháp Bảo — kiểm tra lại DILA, CBETA và Báo Tư

Ngày: 2026-10-10 (Asia/Bangkok). Liên quan T232; không cấp task ID mới.

## Kết quả cần dùng trong dự án

**Chưa xác minh được DILA Authority ID cho Minh Hải Pháp Bảo của Lâm Tế Chúc Thánh trong phạm vi đã kiểm tra. Không có căn cứ kết luận DILA/CBETA hoàn toàn không có thông tin về ngài.**

Quyết định loại trừ A000662 đã được Admin xác nhận trước đó và được docs/tasktodo.md ghi nhận ở phần T232. Đợt này kiểm tra lại bản authority và X0613; không thay đổi quyết định, DB, TTL, quan hệ hay số đời.

Có tư liệu nghiên cứu Hán văn xác định rõ đối tượng 明海法寶 và 祝聖寺. Có sử liệu về Báo Tư được công bố lại; chưa xác minh trực tiếp một mục địa phương chí ghi Minh Hải Pháp Bảo là đệ tử của một vị cụ thể tại chùa này.

## 1. Phạm vi DILA local và kết quả

| Bản dữ liệu đã đọc tuần tự | Số hồ sơ person | SHA-256 của artifact |
|---|---:|---|
| `data\backups\T215-tri-tai-sync-20261002\authority_person.2026-09.zip!Buddhist_Studies_Person_Authority.xml` | 49361 | `1887960f5be733846ec24ba0f66d0516abf293a4e18cd4212460c8e5dbc0e3b9` |
| `data\dila_import\Authority-Databases\authority_person\Buddhist_Studies_Person_Authority.xml` | 19034 | `741290ecb6738c573aa3ddec831e64bbcff5a8259ae554d23f2c23f0293f46e4` |

Nguồn ZIP 2026-09 và nguồn XML import là hai phiên bản của cùng cơ sở authority, không phải hai chứng cứ lịch sử độc lập. Số hồ sơ trong artifact không được dùng thay thế số ID đang có trong DB.

Đã kiểm persName theo các chuỗi 明海, 明海法寶, 明海法宝, 法寶, 得智, 德智, 梁世恩, 祝聖; kiểm toàn văn từng person theo 明海法寶, 明海法宝, 梁世恩, 報資寺. Không có compound_text_hits trong hai artifact. Kết quả và các ứng viên được lưu trong local-scan.json.

Các persName chứa 明海 trong bản ZIP:

| ID | Tên trong hồ sơ | Ghi chú giúp phân biệt |
|---|---|---|
| A000662 | 明海 | 明；【新纂卍續藏】No.613《法華經意語》明 圓澄說、明海重訂。 |
| A007947 | 善繼 / 釋善繼 / 絕宗繼 / 絕宗 / 文明海慧 | 元；婁氏子，天台薦福寺沙門。元大德年間（1297-1306）出家，從天竺大山恢法師學習天台教法。後往南天竺禮謁湛堂性澄，深受器重。晚年專修淨業，一心念佛，晝夜不輟，示寂荼毘後，其舌根不壞。曾刺血繕寫大方廣佛華嚴經（今仍完整保存於蘇州半塘壽聖寺）。（疑年錄：326；明僧索引：1413；佛光：4898） |
| A034808 | 壽晙 / 明海壽晙 | 日本；臨濟宗 楊岐派；大嶽妙積弟子。（禪典．禪宗法系譜：47） |
| A039458 | 融光 / 明海融光 | 日本；曹洞宗；桂岳連芳弟子。（禪典．禪宗法系譜：29） |
| A039944 | 義周 / 明海義周 | 日本；曹洞宗；華叟義榮弟子。（禪典．禪宗法系譜：26） |
| A041194 | 海珀 / 自明海珀 | 清；耨雲真實弟子。（J37nB370_p0009a08） |

Tìm chuỗi con có thể bắt cả danh hiệu chứa 明海, không đồng nghĩa đó là pháp danh Minh Hải của Chúc Thánh. Chưa được tự suy ra owl:sameAs từ trùng hai chữ.

Trang chính thức DILA mô tả authority là dữ liệu tổng hợp từ các dự án Phật học: https://authority.dila.edu.tw/ . Không có tuyên bố rằng mỗi tăng sĩ trong lịch sử đều có ID.

## 2. CBETA local

Nguồn: data/cbeta/xml-p5-full. Đã quét 5017 file XML, lỗi đọc 0. Đọc từng dòng, không nạp toàn bộ corpus vào RAM.

| Chuỗi | Dòng chứa nguyên chuỗi |
|---|---:|
| 明海法寶 | 0 |
| 明海法宝 | 0 |
| 梁世恩 | 0 |
| 報資寺 | 0 |
| 报资寺 | 0 |
| 明海 | 433 |
| 祝聖寺 | 32 |

**Giới hạn:** chỉ tìm chuỗi nguyên vẹn trên từng dòng XML; chữ bị tách bởi tag, gaiji, dị thể và tên khác có thể không được tìm thấy. Chưa kiểm mọi bản phát hành CBETA, mọi kho DILA, mọi bản ảnh địa phương chí. Số dòng chứa 明海 / 祝聖寺 không chứng minh cùng nhân vật / cùng chùa; mẫu 祝聖寺 có các chùa ở Nam Nhạc và Kê Túc Sơn.

### X0613 và A000662

File đọc: data/cbeta/xml-p5-full/X/X31/X31n0613.xml.

- Tiêu đề: 法華經意語; author trong XML: 明 圓澄說、明海重訂 (dòng 12).
- Dòng 149 / mốc X31n0613_p0654a22: người đề tựa 明海 ghi niên đại 崇禎庚午, tức 1630.
- Dòng 200 / mốc X31n0613_p0654c23: 東楚門人 明海 重訂.
- A000662 trong hai bản authority ghi triều Minh và tác phẩm X0613; record SHA-256 giống nhau: aeba756c48aa5dee06a20c4987cc1e9154fd44453b95e7fb6b053af3e903c4ea.

Đây củng cố việc loại trừ A000662, không xác lập ID thay thế cho Minh Hải Pháp Bảo Chúc Thánh. Niên đại 1630 thuộc văn bản đã đọc; không được biến nó thành năm sinh của người đề tựa.

Nguồn chính thức: https://cbetaonline.dila.edu.tw/zh/X0613 ; https://raw.githubusercontent.com/cbeta-org/xml-p5/master/X/X31/X31n0613.xml . Trang CBETA Online là ứng dụng JS, kết quả find của HTML shell không phải kết quả tìm toàn văn kinh.

## 3. Tư liệu học thuật xác định Minh Hải Pháp Bảo

Luận án tiến sĩ của 范文俊 / Pham, Van-Tuan, Đại học Thành Công, 2015: 十七世紀閩南與越南佛教交流之研究. Đã đối chiếu metadata, tóm tắt và mục lục được lập chỉ mục; chưa đọc toàn văn luận án.

- Chương 4 về 明海法寶 và Phật giáo miền Nam Việt Nam: trang 129.
- Mục khảo chứng thân thế: trang 133.
- Mục về tông phái Chúc Thánh: trang 146.
- Phụ lục tư liệu liên quan Minh Hải Pháp Bảo: trang 247.

Nguồn chính thức: https://thesis.lib.ncku.edu.tw/thesis/detail/833f875ec1e835f4f3527160c1f84168/ .
Đối chiếu thư mục Đại học Đài Loan: https://dlbs.liberal.ntu.edu.tw/DLMBS/jp/search/search_detail.jsp?comefrom=fulltextthesis&seq=649627 . Hai mục thư viện này cùng chỉ một luận án, không phải hai nghiên cứu độc lập.

Bản in sách 2021 là bản khác về phân trang; không áp trang 133/247 của luận án sang sách.

## 4. Báo Tư: chứng cứ đã đọc và điểm chưa khóa

Đã tải PDF và đọc trực tiếp các trang cần thiết của nghiên cứu Phan Trương Quốc Trung, Nguyễn Hữu Sử, “Tìm hiểu hành trạng Thiền sư Bản Quả - Khoáng Viên, vị thầy của sư Nguyên Thiều Hoán Bích”, Nghiên cứu Tôn giáo 9/2017, tr.17–31.

Trang 24–28 dẫn và công bố bài ký 報資禪院記 của 潘耒 trong 遂初堂集, đồng thời nhắc bài thơ 報資寺訪曠圓禪師不遇. Bài ký ghi hành trạng Khoáng Viên và địa bàn Quảng Châu; phần đã đọc không nêu 明海法寶. Nghiên cứu phân biệt Báo Tư cũ với Báo Tư Tân Tự. Chưa được gộp hai địa điểm hay biến bài ký thành danh sách đầy đủ pháp tử.

Nguồn: https://vjol.info.vn/index.php/rsr/article/download/46697/37875/ .

DILA có dự án địa phương chí riêng: https://buddhistinformatics.dila.edu.tw/fosizhi/ . Đã đọc trang giới thiệu/danh mục và tìm chữ 報資 trong danh mục; chưa thấy mục theo tên này. Chưa quét toàn văn/bản ảnh toàn bộ dự án. Trang giới thiệu nói dữ liệu tên được tổng hợp từ các dự án; bản ảnh, toàn văn và authority không có độ bao phủ đồng nhất.

Tên cần phân biệt: 報資寺 (Báo Tư) với 報慈寺. File local t45_fosizhi_raw.json có 報慈寺 trong ngữ cảnh Thường Thục/Ngu Sơn; không được coi là chùa Báo Tư ở Quảng Châu.

## 5. Đầu mối sử liệu cần ưu tiên lấy bản gốc

Nghiên cứu của Lê Xuân Thông dẫn văn bia mộ tháp Minh Hải Pháp Bảo, bản kê khai Chúc Thánh, sách Sa di luật nghi yếu lược tăng chú và pháp quyển truyền thừa năm 1847. Đây là đầu mối trực tiếp cần lấy ảnh/bản phiên trước khi duyệt từng trường dữ liệu.

Nguồn: https://phatgiao.org.vn/so-to-minh-hai-dac-tri-phap-bao-cua-dong-thien-lam-te-chuc-thanh-d49548.html . Chưa đọc trực tiếp các hiện vật/bản pháp quyển mà tác giả dẫn.

Bài nghiên cứu 王小盾、黃嶺 được đăng lại có dẫn bản khắc Sa di luật nghi yếu lược tăng chú tại Việt Nam năm 1732, ghi chùa Chúc Thánh, 得智 và 明海. Chú thích truy về luận án 黎氏垂莊 năm 2014, tr.175–176. Đã kiểm bài đăng và chú thích, chưa đọc bản sách/luận án gốc: https://k.sina.cn/article_1691933232_64d8da3001900m2bt.html .

Không dùng nhiều bài chép cùng pháp quyển hoặc cùng luận án để đếm thành ba chứng cứ độc lập. Không duyệt số đời hay quan hệ chỉ từ chữ bối.

## 6. Trạng thái đề xuất khi nhập hồ sơ

| Thuộc tính | Trạng thái phù hợp |
|---|---|
| Nhân vật Minh Hải Pháp Bảo Chúc Thánh | Có nguồn học thuật xác định đối tượng; bổ sung sử liệu từng trường |
| DILA Authority ID | Chưa xác minh trong phạm vi kiểm tra |
| A000662 | Đã loại trừ cho nhân vật Chúc Thánh theo quyết định Admin và chứng cứ X0613 |
| Thông tin Báo Tư | Có bài ký làm đầu mối; phải phân biệt chùa cũ/chùa mới và từng quan hệ |
| “DILA/CBETA không có thông tin” | Không đủ căn cứ để ghi kết luận này |
| Số đời/hasTeacher/hasDisciple | Không cập nhật trong đợt nghiên cứu này |

Đề xuất kỹ thuật khi thực hiện bước định danh đã bàn: hồ sơ local độc lập, nguồn gắn từng mệnh đề, DILA-ID nullable, không tạo mã A giả; chỉ thêm liên kết định danh sau khi kiểm đủ cùng người. Đây là đề xuất, chưa triển khai ở phiên này.

## 7. Các thao tác thực tế và kiểm tra

- Đọc AGENTS.md, phần T232/T233 trong docs/tasktodo.md; kiểm HEAD từ repo root visjs-app.
- Chạy scan_local_sources.py: exit 0; số liệu ở local-scan.json.
- Tải PDF công khai bằng fetch_bao_tu_pdf.py: 934339 byte; trích trang bằng pdfplumber qua extract_bao_tu_pdf.py: 15 trang PDF, đã đọc các trang lựa chọn.
- Đối chiếu nguồn chính thức trên web và đọc X0613 local.
- Không sửa application code, không gọi LLM/API trả phí, không sửa raw XML, TTL hoặc DB.
- Không chạy npm pipeline: không có bản build cần Admin review; đây là đợt nghiên cứu và lưu hồ sơ, không báo PASS thay cho kiểm thử.
- HEAD lúc ghi nhận: c75d99eca0c2d23dbe927174a11b10a4b4e49261. Không commit/stage; worktree có phiên song song.

## 8. Việc chưa hoàn tất

1. Đọc toàn văn luận án, nhất là tr.133 và phụ lục tr.247; truy nguyên từng ảnh/bản Hán.
2. Kiểm toàn văn/bản ảnh sử liệu Báo Tư và địa phương chí Quảng Châu/Quảng Đông có đúng chùa, thời gian, danh hiệu không.
3. Lấy ảnh văn bia Minh Hải, sách khắc năm 1732, pháp quyển 1847; ghi locator, bản lưu, nguồn gốc và mệnh đề mỗi chứng cứ hỗ trợ.
4. Khi mở rộng CBETA: tìm trên text sau khi xử lý tag/gaiji/dị thể; không quy absence của một phép tìm thành absence lịch sử.

Không có yêu cầu Admin phê chuẩn thay đổi DB trong phiên này. Khoảng trống hiện tại là chứng cứ nguồn gốc và độ bao phủ tra cứu.

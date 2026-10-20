---
title: "Phật Tổ Đạo Ảnh — Lộ trình tích hợp học thuật 2026–2036"
status: proposal
prepared_at: 2026-10-15
scope: "Chiến lược nghiên cứu, kiến trúc chứng cứ, liên thông và bảo tồn"
authority: "Đề xuất để Admin và hội đồng chuyên môn thẩm định; không phải chứng nhận sẵn sàng"
---

# Phật Tổ Đạo Ảnh: lộ trình tích hợp học thuật 2026–2036

## 1. Admin đọc trong hai phút

**Đích đến:** từ hệ tra cứu và Việt hóa định danh thành hạ tầng nghiên cứu Phật học: người đọc đi từ tên Việt → đúng nhân vật → nhận định → đoạn sử liệu → bản/phiên bản → người chịu trách nhiệm; người khác tải một gói nghiên cứu và tái lập được kết quả.

Đầu tư trước vào **đúng định danh, chứng cứ và tái lập**, sau đó mới mở rộng nguồn, ảnh bản và thuật toán. Một biểu đồ đẹp, nhiều bản ghi hoặc đủ tab không chứng minh dữ liệu đủ dùng cho luận án. DILA ID là khóa đối chiếu quan trọng; bản Việt, phán đoán truyền thừa và số đời là đóng góp có trách nhiệm riêng của Phật Tổ Đạo Ảnh.

Trong 12 tháng đầu, đề nghị chọn **một bộ tư liệu hẹp, có quyền sử dụng rõ**, hoàn thành pilot chú giải liên bậc ở mục 3 và công bố bản dữ liệu thử có giới hạn. Không chạy làm giàu toàn corpus, không nhập đồng loạt 25 nguồn và không nâng mọi cạnh thầy–trò thành truyền pháp.

Admin cần chốt ba việc trước triển khai: (1) phạm vi corpus/pilot và người phụ trách học thuật; (2) đơn vị đồng hành nhận lưu trữ, phản biện và đào tạo; (3) nhân lực vận hành, QA độc lập và kinh phí bảo trì hằng năm. Văn bản này chỉ đề xuất chương trình; không tự cấp task ID, sửa DB, sửa TTL hay cho phép phát hành dữ liệu nguồn.

## 2. Hiện trạng: phân biệt ba mức sẵn sàng

Phạm vi rà soát của báo cáo là **tài liệu và sự hiện diện một số module trên đĩa**, không phải kiểm kê DB/API trực tiếp hoặc chứng nhận toàn hệ thống ngày 15-10-2026.

| Mức | Căn cứ hiện có để kế thừa | Điều phải kiểm chứng trước nghiên cứu |
|---|---|---|
| Tính năng | Có module hồ sơ TTL v2, xuất từ DB, engine số đời và API tương ứng: [profile](../../src_python/ttl_profile_v2.py), [export](../../src_python/ttl_db_export.py), [engine](../../src_python/generation_engine_v2.py), [API](../../api_generation_v2.py). Có khung [16 tab học thuật](../ACADEMIC_16TABS_IMPLEMENTATION_PLAN.md). | File tồn tại không chứng minh đang chạy đúng, đủ bao phủ, không mất trường hay an toàn khi phát hành. Cần kiểm thử hành vi, phân quyền và hồi quy theo phiên bản. |
| Dữ liệu | Có XML DILA, TTL Việt và các lớp DB/chỉ mục theo lịch sử dự án; có [danh mục 25 nguồn](../SOURCE_CATALOG_25.md), [hợp đồng nguồn](../SOURCE_INTEGRATION_CONTRACT.md). | Danh mục không đồng nghĩa 25 nguồn đã nhập, có adapter, có quyền tái phân phối hoặc độc lập với nhau. Đếm và quyền phải kèm ngày, phiên bản artifact và truy vấn tái lập. |
| Nghiên cứu | Có kiểm kê tab, báo cáo khoảng trống nhập XML và audit nguồn theo phạm vi. | Chưa được suy từ đó rằng toàn bộ nhận định đã phản biện, mọi quan hệ là truyền pháp, mọi tên Việt là DILA cung cấp, hoặc đủ điều kiện cho mọi luận án. Cần bộ vàng, giao thức nghiên cứu và phản biện ngoài nhóm phát triển. |

[Kiểm kê 16 tab](../ACADEMIC_16TABS_INVENTORY.md) là baseline tháng 9; [audit XML](../XML_IMPORT_AUDIT_REPORT.md) và [kiến trúc hybrid](../HYBRID_DATA_ARCHITECTURE.md) là tài liệu tháng 10 với một số số liệu/ước tính và trạng thái triển khai chưa đồng nhất. Không dùng lại dung lượng DB, số người, độ trễ hoặc tỷ lệ bao phủ trong các file đó như số đo hiện tại. Công việc đầu tiên là lập inventory có truy vấn, timestamp, phiên bản và các mẫu kiểm đối chứng.

Giữ nguyên định hướng RAW bất biến → STAGING → CURATED/PUBLIC, nhưng **CURATED chứa cả đóng góp Việt hóa và quyết định biên tập**, không phải chỉ là tập con cơ học của XML. Nguồn và đóng góp phải được lưu tách để cập nhật XML không xóa công trình đã duyệt. “Không có kết quả trong chỉ mục” phải hiển thị NOT-INDEXED khi chưa khảo sát đủ phạm vi, không kết luận sử liệu không tồn tại.

## 3. Danh mục đúng 10 ca nghiên cứu/đào tạo

Đây là **ca đề xuất**, không phải công trình đang có hay cam kết cấp bằng. Cỡ mẫu là điểm khởi đầu để giảng viên điều chỉnh theo tư liệu. Cấp học do cơ sở đào tạo quyết định; điểm UI không thay đánh giá học thuật.

| Mã / cấp | Câu hỏi và phương pháp | Phạm vi thử / sản phẩm | Điều kiện nghiệm thu |
|---|---|---|---|
| BA-1 · Cử nhân | Một thiền sư được mô tả khác nhau thế nào giữa hồ sơ DILA, bản Việt và đoạn truyện gốc? Đọc gần, lập niên biểu và phân biệt lời nguồn/lời dịch. | 20–30 nhân vật trong một tuyển tập; 20 hồ sơ có trích dẫn và ghi chú điều chưa biết. | Mọi dữ kiện dùng trong bài trỏ tới locator và bản nguồn; không dùng bản dịch máy như nguyên văn. |
| BA-2 · Cử nhân | Tên chính, pháp danh, biệt hiệu, địa danh đứng trước tên thay đổi ra sao? Đối chiếu Hán–Việt và bối cảnh. | Khoảng 100 biến thể tên của 40–50 người; bảng tên đa ngữ và các trường hợp đồng danh. | Phân biệt biến thể của một người với người khác; mọi ghép ID có bằng chứng, ca chưa chắc để mở. |
| BA-3 · Cử nhân | Một nhóm tự viện xuất hiện trong sử liệu và bản đồ như thế nào? Đọc địa danh trong văn cảnh. | 15–20 địa điểm trong một vùng; bản đồ chú giải và bảng thời gian có khoảng bất định. | Phân biệt nơi được nhắc/nơi hoạt động/nơi thành lập; tọa độ hiện đại không tự chứng minh vị trí lịch sử. |
| MA-1 · Cao học | Các văn bản ghi nhận mạng truyền thừa Chúc Thánh quanh Minh Hải Pháp Bảo khác nhau ở điểm nào? Phê bình nguồn và đối chiếu phả hệ. | Một nhánh có ranh giới rõ; khoảng 50–100 nhận định từ bản in, văn bia/phả hệ có thể tiếp cận và nguồn số. | Tách truyền pháp, thọ giới, tham học, đồng môn; số đời ghi rõ hệ đếm, mốc và đường chứng minh; không ép người chưa có DILA ID vào ID gần tên. |
| MA-2 · Cao học | Một nhóm thuật ngữ được dịch và diễn giải khác nhau giữa hai bản văn/bản dịch thế nào? So sánh văn bản theo đơn vị đoạn. | 30–50 đoạn, hai bản/bản dịch đủ quyền; bản đối chiếu có chú giải lựa chọn dịch. | Khóa phiên bản, giữ nguyên văn và dị bản; liên kết tương ứng là nhận định có người duyệt, không đồng nhất chỉ vì cùng từ khóa. |
| MA-3 · Cao học | Kết luận về mạng thiền học thay đổi thế nào khi chỉ dùng cạnh có chứng cứ trực tiếp? Phân tích mạng và độ nhạy. | Một thời kỳ/vùng; tối đa khoảng 500 cạnh DILA/Marcus/nguồn bổ sung đã định phạm vi. | Công bố quy tắc chọn cạnh, loại quan hệ, thiếu dữ liệu và phép thử loại nguồn; không đếm bản sao cùng sử liệu thành chứng cứ độc lập. |
| PhD-1 · Tiến sĩ | Mô hình nhận định có tranh luận giúp biểu diễn tri thức Phật học bất đồng tốt hơn thế nào? Thiết kế ontology và đánh giá liên thông. | Bộ thử khoảng 200 nhận định có tranh chấp; ánh xạ mô hình, SHACL, tập phản ví dụ và mã đánh giá. | So sánh với baseline; phản biện bởi chuyên gia Phật học và mô hình dữ liệu; giữ được các cách đọc bất đồng, không chỉ chọn một “winner”. |
| PhD-2 · Tiến sĩ | Mạng truyền thừa xuyên vùng Việt–Hoa được kiến tạo và biến đổi trong các lớp sử liệu thế nào? Nghiên cứu lịch sử kết hợp mạng không gian–thời gian. | Cohort nguồn được cấp quyền, khoảng 1.000–1.500 nhận định; luận chứng, phụ lục dữ liệu và notebook tái lập. | Nêu thiên lệch bảo tồn, niên đại biên soạn và khoảng trống; trung tâm mạng không tự là ảnh hưởng lịch sử hoặc quan hệ nhân quả. |
| PhD-3 · Tiến sĩ | Dị bản và dấu vết dùng lại văn bản hỗ trợ nghiên cứu lịch sử biên tập một tập tư liệu ra sao? Văn bản học, ảnh bản và đối chiếu thuật toán. | Khoảng 200 trang/đơn vị có ít nhất hai chứng bản khi tiếp cận được; TEI, liên kết vùng ảnh và phương pháp đối chiếu. | Có bộ đối chiếu chuyên gia, kiểm lỗi OCR/phân đoạn và đánh giá sai số; tương đồng chữ không tự chứng minh tác giả, niên đại hay quan hệ truyền bản. |
| PILOT-1 · Liên bậc | Cùng một nhận định từ đoạn sử liệu đến hồ sơ nhân vật có được hiểu và chú giải nhất quán không? Cử nhân gắn span/locator; cao học kiểm dịch/loại quan hệ; tiến sĩ/giảng viên phân xử và viết phương pháp. | 50 đoạn và tối đa 300 chú giải; ít nhất 20% mẫu được hai người chú giải độc lập; hướng dẫn, log sửa, tập đánh giá giữ lại. | Mọi chú giải truy được nguồn/phiên bản/tác giả; báo cáo agreement theo loại nhãn và bất đồng sau phân xử. Ngưỡng thí điểm đề xuất 0,80 cho nhãn phân loại đủ cỡ mẫu; báo cả số mẫu và trường hợp hiếm, không coi agreement là chân lý sử học. |

Pilot là đường vào có kiểm soát cho chín ca còn lại; không cần chờ tích hợp hết nguồn quốc tế. Các giả thuyết của nghiên cứu sinh phải tiếp tục tồn tại dưới dạng giả thuyết khi bằng chứng chưa đủ.

## 4. Kiến trúc đích: chứng cứ trước nhận định

**Đây là kiến trúc cần triển khai/đối chiếu, không khẳng định mọi lớp đã có.** Ưu tiên mở rộng thành phần hiện có trước khi thay công nghệ.

```text
Artifact nguồn bất biến + metadata quyền + hash
  → trích xuất từng record/span + manifest biến đổi
  → nhận định theo nguồn + định danh ứng viên + mâu thuẫn
  → biên tập/phản biện có revision, người và lý do
  → projection tra cứu / mạng / số đời / bản dịch
  → gói nghiên cứu theo snapshot + trích dẫn + lưu trữ
```

### 4.1. Các hợp đồng dữ liệu tối thiểu

- **Artifact:** tổ chức cung cấp, bản/phát hành, URL gốc, ngày thu nhận, SHA-256, định dạng, phạm vi, bằng chứng quyền theo artifact. Kho code công khai không mặc nhiên cho phép tái phân phối dữ liệu.
- **Entity:** URI nội bộ ổn định; tên và ngôn ngữ; loại người/tự viện/tác phẩm/chứng bản/địa điểm. Mapping DILA và authority khác có loại quan hệ, trạng thái, nguồn và revision. Không suy identity từ tên file, tên Việt, tọa độ hoặc một chuỗi giống nhau; owl:sameAs chỉ dùng khi đồng nhất thực thể đã được chứng minh.
- **Evidence:** đoạn trích hoặc quyền truy cập đến đoạn; locator CBETA/TEI xml:id/trang–dòng/vùng ảnh; artifact version/hash. Lưu gốc Hán/Nôm/Tạng/Pāli… và bản Việt với tác giả, cách dịch, revision riêng.
- **Assertion:** chủ thể–quan hệ–đối tượng; nguồn; span; phạm vi thời gian; cách thu nhận; người tạo/duyệt; trạng thái và lý do. Mâu thuẫn không bị xóa; score tìm kiếm/độ giống không đổi thành xác suất đúng lịch sử.
- **Release:** dataset_version, schema/ontology version, commit, bộ tham số/query, manifest input/output, kiểm thử, quyền, changelog và trích dẫn. JSON/TTL là cách tuần tự hóa; đủ trường và bảo toàn nghĩa mới là mục tiêu.

Lưu RAW dạng file/kho đối tượng, STAGING dạng sidecar hoặc record nguồn có version; DB phục vụ chỉ mục và bản chiếu có kiểm soát. Chọn sidecar hay DB bằng thử nghiệm thực tế, không theo quy tắc “nhiều dòng thì vi phạm Zero-RAM”: giới hạn RAM được bảo đảm bằng iterator, phân trang, byte/index lookup và cache hữu hạn. Chưa cần chuyển toàn hệ sang graph database; trước hết kiểm chứng truy vấn và xuất RDF từ mô hình hiện hành.

### 4.2. Truyền thừa và số đời là một phép suy dẫn có điều kiện

Mỗi hệ đếm cần scheme_id, định nghĩa gốc là 0 hay 1, phạm vi tông/dòng, anchor có sử liệu và phiên bản. Một người có thể mang nhiều số đời theo nhiều hệ; thứ tự chữ trong bài kệ không tự đồng nghĩa khoảng cách truyền pháp. Không lấy năm 2026 làm căn cứ rằng mọi nhánh đều có cùng “83/85 đời”.

Đường dùng tính phải phân biệt truyền pháp trực tiếp với teacher chung/thọ giới/tham học. Kết quả gồm số ứng viên, anchor, toàn bộ cạnh chứng minh, snapshot nguồn, phiên bản thuật toán và trạng thái. Chu trình/tự nối, thiếu cha, nhiều đường khác độ dài hoặc mốc xung đột → báo chưa xác định; không chọn đường ngắn nhất để ép ra một số. Cạnh DILA chung chỉ cho ứng viên nếu chưa đủ căn cứ truyền pháp.

Giữ quy tắc dự án: **không sửa số đời đã có chỉ bằng cộng một**; một đề nghị hiệu chỉnh phải chỉ ra số cũ sai và số mới đúng, với ít nhất ba gốc chứng cứ độc lập cùng quy ước. Ba website chép lại một bản phả không phải ba gốc. Phép cộng đúng toán học chưa chứng minh toàn bộ đường truyền đúng sử học; thuật toán hỗ trợ Admin, không tự cấp trạng thái accepted. Luôn giữ số legacy và provenance thay vì ghi đè.

## 5. Chuẩn liên thông: dùng ở đúng lớp

| Chuẩn / nguồn chính thức | Áp dụng đề xuất trong dự án | Cổng kiểm chứng |
|---|---|---|
| [FAIR](https://www.gofair.foundation/fair-principles) và [RDA FAIR Data Maturity Model](https://www.rd-alliance.org/groups/fair-data-maturity-model-wg/outputs/fair-data-maturity-model-specification-and-guidelines/) | Định danh bền vững, metadata máy đọc, quyền và provenance; đánh giá trên từng release và chỉ báo có định nghĩa. FAIR cho phép truy cập có kiểm soát. | Công bố bảng chỉ báo, mẫu số, bằng chứng và phần chưa đạt; không tự xưng “được RDA chứng nhận”. |
| [IIIF Presentation 3](https://iiif.io/api/presentation/3.0/) và [Image 3](https://iiif.io/api/image/3.0/) | Manifest/Canvas cho chứng bản; liên kết ảnh–trang–đoạn. Ưu tiên consume manifest của đối tác; chỉ host ảnh có quyền. | Manifest qua validator và ít nhất hai viewer tương thích; quyền/attribution tại đúng tài nguyên. IIIF không thay giấy phép ảnh. |
| [TEI P5](https://tei-c.org/release/doc/tei-p5-doc/en/html/index.html) | ODD của dự án cho văn bản, người/tên, thư mục, dị bản, bất định và stand-off; giữ namespace TEI theo URI. | Schema sinh từ ODD, bộ mẫu dương/âm và round-trip không mất locator; khóa bản Guidelines đã dùng. |
| [CIDOC CRM](https://cidoc-crm.org/get-last-official-release) | Ánh xạ sự kiện, tác nhân, thời gian, nơi chốn và vật mang tin; phạm vi mở rộng được giải thích. | Crosswalk có ví dụ/giới hạn; chuyên gia kiểm nghĩa. Có prefix crm: không có nghĩa đã phù hợp toàn CRM. |
| [PROV-O](https://www.w3.org/TR/prov-o/) + [SHACL](https://www.w3.org/TR/shacl/) | PROV diễn tả artifact–hoạt động–tác nhân; SHACL kiểm cấu trúc, kiểu, liên kết và điều kiện nghiệp vụ được biểu diễn. | Mọi release có validation report; kiểm riêng identity/cycle/độ độc lập sử liệu. SHACL PASS không chứng minh sự thật lịch sử. |
| [W3C Web Annotation](https://www.w3.org/TR/annotation-model/) | Chú giải tách khỏi bản nguồn; target bằng selector văn bản/vùng ảnh, body có tác giả và revision. | Locator vẫn giải được trên bản nguồn bị khóa; phát hiện thay đổi span khi nâng phiên bản. |
| [ORCID](https://info.orcid.org/what-is-orcid/) / [ROR](https://ror.org/about/) | ORCID cho tác giả, người dịch, reviewer hiện đại; ROR cho đơn vị nghiên cứu/lưu trữ có bản ghi phù hợp. | Thu nhận định danh xác thực/phù hợp và tôn trọng quyền riêng tư. Không gán ORCID cho tổ sư cổ đại; không dùng ROR để thay authority cho mọi chùa lịch sử. |
| [BagIt RFC 8493](https://www.rfc-editor.org/info/rfc8493/), [CoreTrustSeal requirements](https://www.coretrustseal.org/why-certification/requirements/), [DOI Zenodo](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/) | Gói bàn giao kiểm checksum; chọn kho cơ quan/kho nghiên cứu có chính sách bảo tồn; PID cho dataset release và quan hệ các phiên bản. | Thử phục hồi, tài liệu trách nhiệm và quyền, gói tái lập độc lập. Git/GitHub không thay kho bảo tồn; chưa có cam kết đối tác hay chứng nhận CoreTrustSeal. |

Khóa phiên bản chuẩn trong release; hàng năm xem lại tương thích. Các URL trên được đối chiếu nguồn chính thức khi soạn báo cáo; chúng không phải xác nhận dự án đã đạt các chuẩn đó.

## 6. Gói công việc, chủ trì và phụ thuộc

Tên vai trò dưới đây là **phân công đề xuất**, chưa xác nhận đã có nhân sự. Admin/chủ nhiệm sở hữu phạm vi và ngân sách; trưởng học thuật chịu phương pháp; data steward chịu định danh/quyền/version; kỹ sư dữ liệu và backend chịu pipeline; QA độc lập chịu bằng chứng kiểm; thủ thư/lưu trữ và vận hành chịu phát hành/bảo tồn. Một người có thể kiêm nhiệm, nhưng tác giả sửa dữ liệu không tự là người duyệt cuối cùng.

| WP | Công việc kỹ thuật/học thuật | Chủ trì / phụ thuộc | Sản phẩm và cổng nghiệm thu |
|---|---|---|---|
| WP-A | Inventory artifact–schema–API–quyền; đối chiếu docs/code/dữ liệu; chốt corpus pilot. | Steward + QA; Admin chốt phạm vi. | Manifest có timestamp/hash/count truy vấn được; các trạng thái imported/indexed/reviewed/public tách nhau; không còn số “đoán hiện trạng”. |
| WP-B | Hợp đồng entity/evidence/assertion/review; vocabulary quan hệ; mapping chính xác DILA/local; schema/SHACL/TEI ODD. | Học thuật + kỹ sư; sau A. | Bộ dữ liệu chuẩn và phản ví dụ; không ghép sai người ở bộ vàng; mọi đổi nghĩa phải version và migration. |
| WP-C | Nhập streaming idempotent, bảo toàn trường XML/TTL, sidecar có version, manifest biến đổi; migration additive và inverse ledger. | Kỹ sư dữ liệu + QA; A/B. | So sánh record/span trước–sau; crash/retry không nhân đôi; rollback không mất biên tập hoặc ghi đè cập nhật ngoài scope. |
| WP-D | Workspace nghiên cứu: trích dẫn, chú giải, dịch, review/dispute, xác thực người dùng; pilot liên bậc. | Học thuật + frontend/backend; B/C, dữ liệu đủ quyền. | PILOT-1 hoàn thành; phân quyền và lịch sử sửa qua test; sinh viên xuất lại dữ liệu mà không cần sửa DB bằng tay. |
| WP-E | Engine số đời và truy vấn mạng theo snapshot, nhiều hệ, bằng chứng đường, kiểm xung đột. | Học thuật + backend + QA; B/C. | Fixtures đa thầy/chu trình/mốc sai/thiếu ID; không có số definitive cho ca thiếu căn cứ; mọi số hiển thị có hệ/mốc/path/version. |
| WP-F | IIIF/TEI cho ảnh bản, đối chiếu và annotation; adapter nguồn ưu tiên theo nhu cầu đề tài. | Thủ thư + kỹ sư; B/D và quyền artifact. | Một corpus ảnh–text liên kết hoàn chỉnh, hai consumer ngoài ứng dụng đọc được; không hứa ingest tất cả 25 nguồn. |
| WP-G | Gói nghiên cứu, PID/release, API có version, dataset citation, máy chạy tái lập và data paper. | Steward + QA + cơ sở hợp tác; C/D, F khi có ảnh. | Nhóm ngoài cài gói và tái lập bảng/biểu chính; có license theo thành phần, changelog và hạn chế. |
| WP-H | CI thật, worktree riêng, release bất biến, health check, bảo vệ writer/backup, dashboard bằng chứng. | Lead dev + vận hành + QA; bắt đầu song song A. | Không false-PASS/placeholder; test fixture không ghi production; deploy/rollback thử trên staging; công bố fail/skip và commit thực đang phục vụ. |
| WP-I | Kho bảo tồn, phân công kế nhiệm, tài trợ dài hạn, kiểm toán FAIR và phản biện ngoài. | Chủ nhiệm + đơn vị lưu trữ; G/H. | Thỏa thuận lưu trữ và xuất dữ liệu, kiểm checksum/khôi phục định kỳ, kế hoạch thoát nhà cung cấp và ngân sách 3 năm cuốn chiếu. |

WP-H cần đi trước mở rộng corpus: quy trình phát triển phải bảo vệ dữ liệu nhiều phiên làm chung và đưa kết quả test thật vào cổng phát hành. Không dùng số lượng test hay phần trăm task DONE thay chất lượng kiểm toán.

## 7. Lộ trình theo cổng, không chạy theo lịch bằng mọi giá

Mốc 0 là tháng 10-2026; “12 tháng” là đến khoảng tháng 10-2027. Các mốc sau là mục tiêu kế hoạch, có thể điều chỉnh sau pilot và năng lực đối tác.

| Giai đoạn | Trọng tâm / phụ thuộc | Cổng ra bắt buộc |
|---|---|---|
| 0–3 tháng | WP-A/B/H: inventory chỉ đọc, hợp đồng mẫu, bộ vàng đầu tiên, môi trường staging và danh mục quyền; ký phạm vi PILOT-1. | G0: Admin + học thuật + QA đồng ý corpus và giả định; artifact gốc bảo toàn; mọi con số có phương pháp đo. |
| 3–6 tháng | WP-C/D: importer bảo toàn, mapping và chú giải; WP-E thử trên fixture/mẫu có nguồn, không mass-update. | G1: luồng nguồn→nhận định→review→export chạy trọn trên corpus pilot; test lỗi và rollback PASS; ca chưa chắc vẫn để mở. |
| 6–12 tháng | Hoàn thành PILOT-1; thử các đề tài BA phù hợp; WP-G bản thử và WP-F corpus ảnh nhỏ khi đủ quyền. | G2: ít nhất một nhóm độc lập tái lập gói; báo cáo agreement và sai số; gói chỉ phát hành thành phần đã qua gate quyền, kèm limitations. |
| Đến 2029 | Củng cố 3 ca BA/3 ca MA theo chương trình đối tác; mở thêm từng nguồn/corpus có lợi ích chứng minh; API/schema ổn định, WP-F/G vận hành. | G3: tối thiểu hai nhóm ngoài hệ thống dùng lại dữ liệu có dẫn nguồn; đối chiếu hai công cụ ngoài; 100% claim published của corpus được dẫn tới evidence/version. Không đặt số lượng luận văn làm điều kiện duy nhất. |
| Đến 2031 | WP-E/F/G cho 3 ca PhD; phương pháp quản trị bất đồng, khảo cứu liên vùng, đánh giá so với baseline; phản biện mô hình/nguồn độc lập. | G4: ít nhất một nghiên cứu phương pháp có dữ liệu/mã tái lập và phản biện ngoài; các kết luận không được nâng accepted hàng loạt chỉ vì một mô hình dự đoán tốt. |
| Đến 2036 | WP-I: liên kết kho cơ quan, quản trị kế nhiệm, dịch vụ ổn định và duy trì corpus được cộng đồng dùng; mở ngữ hệ/truyền thống mới theo nguồn lực. | G5: tổ chức nhận bảo tồn có thỏa thuận thực; phục hồi định kỳ đạt SLO đã cam kết; có người thay vận hành và kinh phí duy trì; đánh giá FAIR công khai và kiểm toán quyền/semantic định kỳ. |

Không chuyển giai đoạn chỉ vì hết thời hạn. Khi G0/G1 chưa đạt, giữ pilot nội bộ; khi rights chưa rõ, có thể công bố metadata/phương pháp được phép thay vì xuất toàn nội dung nguồn.

## 8. KPI và cách đo

Các ngưỡng dưới đây là **đề xuất nghiệm thu cho corpus phát hành**, không phải số đo toàn dự án. Steward phải ghi numerator/denominator, phạm vi, thời điểm và công cụ đo; tổng corpus lớn lên không được che tỷ lệ sai.

| KPI | Mục tiêu/gate đề xuất | Đo và trách nhiệm |
|---|---|---|
| Truy nguyên claim | 100% claim được phát hành có evidence locator + artifact version/hash; accepted có người/lý do duyệt. | Validation máy + QA lấy mẫu theo loại claim; không lấy có URL làm đủ. |
| Mapping định danh | 0 ghép sai trong bộ vàng bắt buộc; công bố precision/recall trên mẫu ngoài, có khoảng tin cậy và số lượng unresolved. | Reviewer độc lập; tối thiểu lấy mẫu phân tầng đồng danh/khác thời/khác chữ Hán. |
| Bảo toàn nhập/xuất | 100% artifact checksum; không mất trường/span đã cam kết; lỗi không được bỏ qua im lặng. | Manifest, semantic diff, round-trip và fault injection do QA. |
| Số đời | 100% số hiển thị có scheme/anchor/path/version; 0 ca xung đột bị trả như một số chắc chắn trong bộ thử. | Đối chứng học thuật + test nhiều đường; thống kê riêng candidate/derived/accepted. |
| Chú giải | Mục tiêu agreement 0,80 trên nhãn phù hợp trong pilot, kèm quy tắc và bất đồng; không đuổi ngưỡng bằng xóa ca khó. | Trưởng học thuật chốt metric trước khi xem kết quả; báo mẫu/nhãn hiếm. |
| Tái lập | 1 nhóm ngoài làm lại được gói pilot trước G2; tối thiểu 2 nhóm tái dùng có dẫn nguồn trước G3. | Log môi trường, manifest và kết quả độc lập; không tính lượt truy cập. |
| Quyền | 100% thành phần public có quyết định/bằng chứng quyền theo phiên bản; quyền chưa rõ không phát hành nội dung. | Steward + cơ sở chủ quản kiểm release. |
| Vận hành/bảo tồn | Đo baseline trước khi ký SLO; đề xuất pilot sao lưu hằng ngày, kiểm checksum định kỳ, phục hồi diễn tập mỗi quý. | Ops ghi RPO/RTO đạt thực tế; bản sao khác vị trí và một bản offline/immutable theo nguồn lực. |

Đánh giá mỗi quý trong năm đầu, hằng năm từ 2029. Phải báo cả số claim bị bác/bỏ mở, thời gian review và chi phí lưu trữ/vận hành; không dùng token rẻ hoặc “AI tự làm” làm thước đo duy nhất.

## 9. Rủi ro và kiểm soát

| Rủi ro | Biện pháp / người chịu trách nhiệm |
|---|---|
| Nhiều kho chép cùng một sử liệu tạo “đồng thuận” giả | Lập đồ thị nguồn gốc chứng cứ; reviewer xét độc lập theo bản/sử liệu, không đếm domain/repository. |
| Đồng danh, dịch sai, tên chùa gắn trước tên người | Khóa ID + chữ Hán + bối cảnh; mapping ứng viên/review; giữ tên Việt là dữ liệu biên tập. Steward + chuyên gia. |
| Biến teacher/co-mention/OCR thành truyền pháp hoặc sử thực | Vocabulary loại quan hệ, trích đoạn và gate accepted; AI chỉ đề xuất có nhãn/phương pháp. Trưởng học thuật. |
| Mô hình tông phái/nguồn thiên lệch thành phán quyết phổ quát | Cho phép nhiều hệ đếm, nhiều cách đọc, nhiều truyền thống; công bố sampling và lịch sử nguồn. Hội đồng chuyên môn. |
| Giấy phép phần mềm bị hiểu là quyền dữ liệu/ảnh | Hồ sơ quyền theo artifact; hợp đồng đối tác, attribution và cơ chế gỡ/giới hạn truy cập. Steward. |
| Một DB/worktree dùng chung, rollback làm mất việc khác | Worktree nhiệm vụ, writer lock, transaction, inverse ledger, release manifest và staging; diễn tập phục hồi. Lead dev/Ops. |
| Phụ thuộc một Admin/kỹ sư/nhà cung cấp | Tài liệu thao tác, đào tạo người thay, gói mở xuất được, quyền quản trị có kế nhiệm và quỹ bảo trì. Chủ nhiệm. |
| Mở quá rộng vượt khả năng phản biện | Nguồn mới chỉ vào khi có câu hỏi nghiên cứu, quyền, bộ mẫu và người duyệt; đo chi phí/claim và thời gian xử lý backlog. Admin + học thuật. |

## 10. Tài liệu dự án cần đọc và quyết định tiếp theo

- [Kế hoạch 16 tab](../ACADEMIC_16TABS_IMPLEMENTATION_PLAN.md) và [baseline](../ACADEMIC_16TABS_INVENTORY.md): giữ mục tiêu ba cấp, nhưng bổ sung cổng phương pháp/tái lập, không tự đồng nhất số điểm tab với trình độ luận án.
- [Kiến trúc hybrid](../HYBRID_DATA_ARCHITECTURE.md) và [audit nhập XML](../XML_IMPORT_AUDIT_REPORT.md): căn cứ lập inventory, không mặc định các kế hoạch sidecar/schema đã hoàn tất.
- [Danh mục nguồn](../SOURCE_CATALOG_25.md), [hợp đồng tích hợp](../SOURCE_INTEGRATION_CONTRACT.md), [ma trận thẩm quyền](../SOURCE_AUTHORITY_MATRIX.md): đối chiếu phiên bản. Điểm ưu tiên nguồn phục vụ hiển thị không thay phê bình từng bản văn, không chứng minh độc lập hay quyền.
- [Audit tái sử dụng nguồn T224](../T224_SOURCE_REUSE_AUDIT_PLAN.md): mẫu tốt về phân biệt baseline lịch sử với snapshot, “có event” với “có founding”, giới hạn nguồn với backlog.
- [Task hiện hành](../tasktodo.md) và [rollback](../ROLLBACK.md): tra trạng thái theo task, không tạo thêm việc trùng ID hoặc dùng tài liệu kế hoạch làm bằng chứng DONE.

**Bước triển khai được đề nghị tiếp:** tổ chức buổi chốt phạm vi WP-A/B/H và PILOT-1; công bố một trang điều lệ dữ liệu (nguồn–định danh–review–quyền–bảo tồn), giao người chịu trách nhiệm từng cổng, rồi tách work package thành task theo quy tắc ID của dự án. Chỉ khi phạm vi/ngân sách/đơn vị học thuật được chốt mới cam kết lịch triển khai và phát hành.

## 11. Phạm vi kiểm chứng báo cáo

Soạn ngày 15-10-2026 bằng cách đọc các tài liệu dự án được liên kết ở trên và đối chiếu URL chuẩn chính thức. Chỉ xác nhận sự hiện diện của các module nêu ở mục 2; **không chạy SQL kiểm kê, gọi API, benchmark, pipeline hay audit quyền toàn corpus trong lượt soạn này**. Không sửa dữ liệu, số đời, mapping hoặc cấu trúc production. Các mục tiêu 2027/2029/2031/2036 và ngưỡng KPI là đề xuất quản trị để thẩm định, không phải thành tích đã đạt.

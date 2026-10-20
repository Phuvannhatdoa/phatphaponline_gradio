> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Spec M2 · P1

# M2 Đồng bộ Authority DILA, SNA, Wikidata

Cập nhật lõi định danh người, nơi chốn và quan hệ thầy trò từ các nguồn có giấy phép sạch nhất, có provenance từng dòng.

[Quay lại Plan Overview](00_PLAN_OVERVIEW.md)

## Mục đích

DILA là spine của hệ thống. Module này đưa vào các lớp chưa nạp hoặc cần cập nhật: quan hệ thầy trò từ Bingenheimer SNA, bảng nối Wikidata, và đồng bộ có kiểm soát từ `DILA-edu/Authority-Databases`.

## UI/UX

Trang admin `/daoanh/admin/authority_sync.html`.

- **Thẻ nguồn** cho DILA, SNA, Wikidata: phiên bản đang dùng, ngày đồng bộ, số bản ghi, nút Xem trước thay đổi.
- **Màn hình diff:** hai cột Trước và Sau, nhóm theo Thêm mới, Sửa, Xóa, mỗi nhóm có số lượng và 20 dòng mẫu. Nút Áp dụng chỉ bật khi admin đã xem diff.
- **Thẻ quan hệ** trong chi tiết nhân vật: người thầy, đệ tử, nguồn (badge DILA, SNA), khoảng thời gian, địa điểm, độ tin cậy. Dùng lại định dạng thẻ quan hệ DILA đã thống nhất (báo cáo UNIFY_DILA_LINEAGE_RELATION_CARD_FORMAT).
- **Badge nguồn** luôn hiển thị. Tên Việt hiện badge ZQLOCAL, tên Hán hiện badge DILA.

## Dữ liệu

| Nguồn                                                  | Lấy gì                                                                                                                       | Ghi vào đâu                                                                                  |
|--------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| DILA `Authority-Databases` (CC BY-SA 3.0)              | Người (A-id, thầy trò, sinh tử, triều đại), nơi chốn (PL-id, tọa độ, tên khác), thư mục. Tọa độ lưu kinh độ trước, vĩ độ sau | `entity_claims` với source_id=1, `places_dila`, `time_periods`                               |
| Bingenheimer SNA (`mbingenheimer/ChineseBuddhism_SNA`) | Cạnh quan hệ: mô tả, tham chiếu, thời gian bắt đầu và kết thúc, nơi chốn. Nút chính là DILA A-id                             | Lớp quan hệ riêng có provenance. Tên bảng đề xuất mới `relation_claims`, cần xác nhận schema |
| Wikidata                                               | Chỉ ID: P1187 (người DILA), P1188 (nơi DILA), P2477 (BDRC), thuộc tính CBDB. Tọa độ tùy chọn                                 | Claim loại EXTERNAL_ID kèm `source_url` (đã có 148 dòng)                                     |
| DILA `biographies`                                     | Sự kiện đời sống có ngày và địa điểm. **Giấy phép chưa nêu**, xin DILA xác nhận trước                                        | Chưa nạp                                                                                     |

## Logic

- Đồng bộ theo commit của repo (repo không có tag release). Lưu hash commit vào `source_version`. So sánh với phiên bản trước để phát hiện bản ghi cũ.
- Không bao giờ ghi đè claim đã có. Dòng thay đổi tạo claim mới và đánh dấu claim cũ là đã thay thế, giữ lịch sử.
- DILA là CC BY-SA nên giữ các claim DILA tách biệt (source_id=1). Tên Việt ZQLOCAL là tài sản riêng, không trộn vào bảng DILA. Cần luật sư xác nhận ranh giới giữa tập hợp (collection) và tác phẩm phái sinh.
- Tên Việt chỉ do ZQLOCAL tạo (độ tin cậy 0,5, phiên âm tự động). Không gán cho DILA, CBETA hay MARCUS.
- Xung đột quan hệ (ví dụ cùng một người có hai thầy ở hai nguồn): đưa vào bộ máy xung đột sẵn có (CONFLICT_ENGINE_SPEC) thay vì chọn ngầm.
- Cạnh SNA mà nút không khớp A-id trong DILA thì đưa vào hàng đợi, không tạo nhân vật mới.
- Năm tháng: chuyển niên hiệu qua `time_periods`. Không suy ra năm lập chùa từ trường không phải ngày lập.
- README của DILA ghi khoảng 19.000 nơi chốn (bản 2020), dữ liệu hiện tại khoảng 59.000. Đừng tin README, đếm trực tiếp.

## Acceptance criteria

- [ ] Xem trước diff chạy được cho DILA mà không ghi gì vào DB.
- [ ] Áp dụng một lần đồng bộ ghi đúng số dòng đã xem trước và có dòng audit.
- [ ] Số claim cũ không giảm sau đồng bộ, claim thay thế vẫn truy vấn được.
- [ ] Mỗi cạnh SNA có source, phiên bản, khoảng thời gian, và liên kết về hai A-id hợp lệ.
- [ ] Cạnh không khớp A-id nằm trong hàng đợi, không có nhân vật mới tự sinh.
- [ ] Không có tên Việt nào mang source_id khác 5 (truy vấn kiểm chứng đính kèm).
- [ ] Thẻ quan hệ hiển thị badge nguồn đúng.
- [ ] Qua cổng M1: tắt nguồn thì đồng bộ bị từ chối.

## Việc cần user quyết

- Xin DILA xác nhận giấy phép của `biographies` (liên hệ ghi trong README của repo).
- Đồng ý tạo bảng `relation_claims` hay dùng chỗ có sẵn.

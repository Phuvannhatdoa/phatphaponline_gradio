---
id: T56
title: "Bản Đồ Lịch Sử — Dynasty Map & Temporal Slider"
module: GIS / Timeline / UI
priority: medium
status: in_progress
depends_on: [T21, T31, T32, T39]
created: 2026-08-26
updated: 2026-11-06
done_when: >
  Bản đồ hiển thị chùa qua các triều đại với overlay ranh giới lịch sử,
  temporal animation slider theo năm lập chùa, marker cluster màu theo triều đại.
  Không ghi đè Leaflet map + Tab Bản Đồ hiện có.
---

# T56 — Bản Đồ Lịch Sử

> Tài liệu này viết cho Admin đọc. Phần cuối (mục 10) là ghi chú kỹ thuật cho Agent.

## 1. Tóm tắt cho Admin

**Mục tiêu:** Cho phép xem các chùa trên bản đồ theo thời gian và theo triều đại. Ví dụ: kéo một thanh năm để thấy những chùa nào đã được lập đến năm đó, và tô màu chùa theo triều đại.

**Hiện đang ở đâu:**
- Phần **dữ liệu** đã làm xong: hệ thống đã lấy được danh sách chùa có năm lập và vị trí, và đã phân loại chùa theo triều đại.
- Phần **giao diện** (thanh trượt, nút phát, màu sắc, nơi hiển thị trên trang) **chưa làm**.
- Bản đồ hiện có trên trang vẫn giữ nguyên, không bị thay đổi.
- **Vị trí của T56:** lớp T56 là một lớp dữ liệu riêng, nằm trên **tab Bản Đồ** của trang Đạo Ảnh (`places.html`). Trang kiểm tra: `http://127.0.0.1:8080/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255` (mở đúng chùa đã chọn, rồi bấm tab Bản Đồ).

## 2. Đã làm xong
- Lấy được danh sách chùa có năm lập và tọa độ trên bản đồ.
- Xác định triều đại của từng chùa dựa trên năm lập.
- Có danh sách các triều đại, kèm số chùa và khoảng năm của mỗi triều.
- Nếu máy chủ thiếu dữ liệu, hệ thống trả về danh sách rỗng kèm thông báo, thay vì báo lỗi.

Đây là phần T56a (dữ liệu) và T56b (nguồn dữ liệu cho bản đồ). Hai nguồn này không tạo bảng dữ liệu mới, chỉ đọc từ dữ liệu có sẵn.

## 3. Chưa làm
- **Thanh trượt năm** và nút phát/dừng (T56c).
- **Màu điểm chùa theo triều đại** trên bản đồ (T56c).
- **Đưa lớp T56 lên tab Bản Đồ** (T56d). Hiện trang chưa gọi dữ liệu T56 nào, nên tab Bản Đồ chưa hiển thị lớp này. Chỉ có bản đồ nhỏ của chùa đang chọn.
- **Đường ranh giới các triều đại** — hiện chưa có nguồn dữ liệu ranh giới.

## 4. Vấn đề dữ liệu Admin cần biết
- **Triều đại đang được xác định theo khoảng năm cố định** viết sẵn trong hệ thống, không lấy từ tài liệu gốc. Một số khoảng trùng nhau (ví dụ Bắc Ngụy nằm trong thời Nam Bắc Triều), nên một năm có thể thuộc nhiều triều. Cần kiểm chứng lại bảng này trước khi công bố cho công chúng.
- **Chỉ khoảng 2.251 / 3.688 sự kiện lập chùa có năm** (số liệu kiểm tra ngày 2026-10-08). Chùa không có năm lập sẽ không hiện trên bản đồ lịch sử.
- **Tài liệu cũ đã sai:** trước đây ghi rằng bảng "lineage" có tọa độ của 3.196 địa danh. Thực tế bảng đó chỉ có người và tác phẩm, không có chùa và không có tọa độ. Nguồn tọa độ đúng là bảng sự kiện lập chùa nối với bảng chùa. Đã sửa trong tài liệu này.
- **Tab Bản Đồ hiện có** là bản đồ nhỏ cho từng chùa đang chọn, không phải bản đồ lịch sử toàn cục. Theo Admin, lớp T56 là lớp riêng đặt trên tab này. Cách hiển thị cụ thể (có giữ bản đồ nhỏ hay không) chưa chốt.
- **Chưa có chỗ kiểm thử trên màn hình:** hiện chỉ kiểm tra được phần dữ liệu.

## 5. Kế hoạch

| Phần | Nội dung | Trạng thái |
|---|---|---|
| T56a | Dữ liệu năm lập và vị trí chùa | Đã làm |
| T56b | Nguồn dữ liệu cho bản đồ, lọc theo năm và triều đại | Đã làm |
| T56c | Thanh trượt năm, nút phát/dừng, màu theo triều đại | Chưa làm |
| T56d | Đưa lớp T56 lên tab Bản Đồ | Chưa làm. Đã chốt: nằm trên tab Bản Đồ |

**Việc Admin cần quyết trước khi làm T56d:**
1. Cách hiển thị lớp T56 trên tab Bản Đồ: có giữ bản đồ nhỏ của chùa đang chọn hay không?
2. Nguồn dữ liệu **ranh giới triều đại** dùng từ đâu?

Sau khi Admin quyết hai việc trên, làm T56c rồi T56d.

## 6. Tiêu chí nghiệm thu
- Dữ liệu năm lập và triều đại hiển thị đúng, lọc đúng theo năm và theo triều đại. **(Đã đạt)**
- Thanh trượt chạy được, nút phát/dừng hoạt động, màu chùa đổi theo triều đại. **(Chưa làm)**
- Bản đồ hiện có không bị thay đổi. **(Đúng đến hiện tại)**

## 7. Trạng thái
- T56a: đã làm.
- T56b: đã làm.
- T56c: chưa làm.
- T56d: chưa làm.
- **T56 tổng thể: chưa hoàn thành.** Không ghi "xong" khi T56c và T56d còn thiếu.

## 8. Lịch sử quyết định
- **2026-08-26:** Tạo T56. Kế hoạch ban đầu dùng một bảng dữ liệu riêng để tính trước, và giả định nguồn tọa độ là một bảng khác.
- **2026-10-08:** Admin chọn không tạo bảng riêng; hệ thống tính trực tiếp từ dữ liệu có sẵn. Phát hiện giả định về nguồn tọa độ là sai, đã đổi nguồn. T56d tạm dừng chờ Admin quyết định thiết kế.
- **2026-11-06:** Viết lại tài liệu cho dễ đọc với Admin. Sửa các mô tả sai (nguồn tọa độ, cách xác định triều đại, tab Bản Đồ, một tên file không tồn tại). Trạng thái chuyển từ "chờ" sang "đang làm".
- **2026-11-06 (Admin):** T56 là lớp dữ liệu riêng nằm trên tab Bản Đồ, không phải một trang hay tab mới. Đã chốt nơi đặt lớp; còn chờ quyết định cách hiển thị và nguồn ranh giới triều đại.

## 9. Nhật ký cập nhật
Mỗi lần sửa tài liệu, ghi thêm một dòng ở đây.

- **2026-11-06:** Viết lại toàn bộ tài liệu theo cấu trúc mới, viết bằng tiếng Việt dễ hiểu cho Admin. Chuyển phần ghi chú kỹ thuật xuống cuối file (mục 10). Cập nhật ngày sửa đổi. Trạng thái: T56a và T56b đã làm, T56c và T56d chưa làm.
- **2026-11-06 (bổ sung):** Theo Admin, ghi rõ T56 là lớp dữ liệu riêng trên tab Bản Đồ, kèm đường dẫn kiểm tra. Xác nhận bằng mã nguồn: trang `places.html` chưa có lời gọi nào tới API map-timeline, nên lớp chưa hiện. Cập nhật mục 1, 3, 4, 5, 8 và khối JSON.

---

## 10. Ghi chú cho Agent (JSON prompt — giữ cuối file)

```json
{
  "task": "T56",
  "action": "rewrite_document",
  "objective": "Viết lại tài liệu T56 theo cấu trúc mới, phản ánh đúng trạng thái hiện tại và tách rõ phần đã có, phần còn thiếu, vấn đề dữ liệu và kế hoạch triển khai.",
  "scope_allow": [
    "Chỉ sửa Dai_Tang_Kinh/daoanh/tasks/T56-ban-do-lich-su.md",
    "Đối chiếu app.py, places.html và các tài liệu T56 liên quan để cập nhật chính xác",
    "Giữ lại mục tiêu nghiệp vụ của T56 nhưng sửa các mô tả sai về lineage_chronology, GPS và dynasty"
  ],
  "scope_deny": [
    "Không sửa app.py, places.html, database hoặc API",
    "Không triển khai slider, animation, marker màu hay UI mới",
    "Không tạo bảng map_chronology",
    "Không commit, merge, push hoặc ghi đè thay đổi của agent khác"
  ],
  "implementation_state": {
    "T56a": "implemented",
    "T56b": "implemented",
    "T56c": "pending",
    "T56d": "pending"
  },
  "endpoints": {
    "map_timeline": "GET /daoanh/api/places/map-timeline?min_year=&max_year=&dynasty=&limit= (mặc định 500, tối đa 2000; lọc dynasty ở tầng Python; schema_lag khi thiếu bảng)",
    "map_timeline_dynasties": "GET /daoanh/api/places/map-timeline/dynasties (17 triều; min/max year, count)"
  },
  "source_ssot": "place_timeline_events (event_type='founding', year NOT NULL) JOIN places_dila (geo_lat, geo_long). KHÔNG dùng lineage_chronology (0 dòng place, không có GPS).",
  "dynasty_logic": "_get_dynasty_context() trong app.py — bảng CE hardcoded, có khoảng chồng lấn; cần evidence trước khi dùng công khai.",
  "admin_decision_2026-11-06": "T56 là lớp dữ liệu riêng trên tab Bản Đồ (data-t=bandoo) của places.html. Lớp này chưa được gắn: places.html không có fetch tới map-timeline.",
  "known_gaps": [
    "map-timeline-bar được tham chiếu trong places.html (~dòng 2100) nhưng không có phần tử HTML tương ứng",
    "places.html không gọi map-timeline/dynasties ở bất kỳ đâu; lớp T56 chưa hiển thị trên tab bandoo",
    "tab bandoo (renderBandooTab) là mini-map per-entity, không phải bản đồ lịch sử toàn cục",
    "chưa có nguồn ranh giới triều đại (done_when yêu cầu overlay)",
    "chỉ ~2.251/3.688 founding events có year"
  ],
  "blocked_on_admin": [
    "Cách hiển thị lớp T56 trên tab bandoo: có giữ mini-map của chùa đang chọn không",
    "Nguồn ranh giới triều đại"
  ],
  "rules": [
    "Không tuyên bố DONE khi T56c/T56d còn pending",
    "Mọi thay đổi tài liệu phải ghi vào mục 9 (Nhật ký cập nhật)",
    "Giữ UTF-8 và tiếng Việt có dấu"
  ],
  "report_json": {
    "status": "PASS|FAIL|BLOCKED",
    "file_changed": "Dai_Tang_Kinh/daoanh/tasks/T56-ban-do-lich-su.md",
    "diff_check": "Chỉ thay đổi file T56",
    "tests": [],
    "blockers": []
  }
}
```

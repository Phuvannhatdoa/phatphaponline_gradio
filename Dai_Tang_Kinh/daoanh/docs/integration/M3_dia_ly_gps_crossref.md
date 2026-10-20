> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Spec M3 · P1

# M3 Địa lý: GPS Cross-Ref và Review

Làm giàu và kiểm chứng tọa độ chùa, tự viện, có hàng đợi duyệt thủ công và ghi rõ độ chính xác của từng tọa độ.

[Quay lại Plan Overview](00_PLAN_OVERVIEW.md)

## Mục đích

Bản đồ chỉ đáng tin khi mỗi điểm nói rõ nó chính xác đến đâu. DILA là điểm neo. Các nguồn khác chỉ bổ sung hoặc đối chiếu, và nguồn có tọa độ tâm huyện (BGIS) không được coi là vị trí chùa.

## UI/UX

Trang `/daoanh/admin/geo_review.html` và một khối nhỏ trong chi tiết địa danh trên bản đồ.

- **Hàng đợi duyệt:** mỗi dòng hiện hai ứng viên cạnh nhau (tên Hán, tên Việt, nguồn, tọa độ, độ chính xác). Giữa hai bên là điểm khớp và khoảng cách. Nút Chấp nhận, Từ chối, Để sau.
- **Mini-map** cho mỗi ứng viên, vẽ hai điểm và đường nối, đổi màu theo độ chính xác.
- **Bộ lọc:** nguồn, điểm khớp, khoảng cách, trạng thái duyệt, có va chạm tọa độ trùng.
- **Trên bản đồ chính:** tọa độ có chấm nét liền khi chính xác điểm, nét đứt khi là tâm hành chính. Tooltip nêu nguồn và độ chính xác.
- **Chế độ tối** của bản đồ (Ver 30) giữ nguyên.

## Dữ liệu

| Nguồn                      | Dùng làm                                                                                                                                                                                       | Hạn chế                                                                         |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| DILA place                 | Điểm neo. Khoảng 59.375 nơi, 58.500 có tọa độ                                                                                                                                                  | CC BY-SA 3.0                                                                    |
| World Historical Gazetteer | Đối chiếu qua `/reconcile`, trả định dạng LPF 1.1. Giới hạn 50 truy vấn mỗi lô, 600 mỗi phút, 5.000 mỗi ngày                                                                                   | Cờ `redistributable` và HTTP 451                                                |
| GeoNames                   | Tâm xã, huyện, tọa độ hiện đại. Ghi nguồn có link. 10.000 credit mỗi ngày bản miễn phí                                                                                                         | CC BY                                                                           |
| Wikidata P625              | Tọa độ tham khảo                                                                                                                                                                               | Chưa xác minh trang CC0                                                         |
| BGIS                       | Chỉ gợi ý tên và đơn vị hành chính. 18.938 địa điểm, 83,5% tọa độ trùng nhau                                                                                                                   | REFERENCE_ONLY. YEAR_START=2006 không phải năm lập chùa                         |
| CHGIS, TGAZ                | Chỉ địa danh Trung Quốc, chỉ tham chiếu                                                                                                                                                        | Học thuật, chưa rõ phân phối lại                                                |
| Bảng                       | `geo_cross_ref` (đã có `bgis_id`, 33 khớp từ T31). Cần thêm: độ chính xác tọa độ, thời điểm hiệu lực, loại quan hệ, nguồn và phiên bản, độ tin cậy, người duyệt. **Đổi schema, cần xác nhận.** | Định dạng mỗi liên kết theo LPF: exactMatch, closeMatch. Provenance theo PROV-O |

## Logic

- **Chuẩn hóa tên:** NFKC, bỏ hậu tố 寺, 院, 庵, chùa, tự. Có khóa phụ bỏ dấu tiếng Việt. Dùng cả Hán Việt và pinyin.
- **Điểm khớp (đề xuất, chưa hiệu chỉnh):** 0,5 tên + 0,3 không gian + 0,2 loại và thời kỳ. Trùng hoàn toàn chữ Hán được cộng điểm.
- **Tự động chấp nhận** chỉ khi trùng chữ Hán và cách nhau tối đa 2 km (địa điểm có tên), hoặc tối đa 10 km khi một bên là tâm hành chính.
- **Vào hàng đợi** khi 2 đến 25 km hoặc độ giống tên 0,85 đến 0,95. Trên 25 km không bao giờ tự liên kết.
- **Va chạm:** nhiều chùa chung một tọa độ thì buộc duyệt tay, không bao giờ chọn ngầm.
- Ngưỡng trên là giả định. Phải hiệu chỉnh trên một mẫu đã gán nhãn tay (ít nhất 200 cặp) rồi ghi kết quả vào tài liệu.
- Không dùng BGIS để suy ra năm lập, không nâng độ chính xác của tâm huyện thành điểm.
- Bản đồ Việt Nam: chưa tìm thấy gazetteer có tọa độ cho thế kỷ 17 đến 18. Địa danh Việt cần duyệt tay hoặc nguồn do user cung cấp (ví dụ Đại Nam nhất thống chí số hóa).

## Acceptance criteria

- [ ] Chạy khớp thử trên mẫu có nhãn: báo độ chính xác và độ phủ, không có liên kết nào tự động vượt ngưỡng 25 km.
- [ ] Mỗi liên kết trong `geo_cross_ref` có nguồn, phiên bản, độ chính xác, độ tin cậy.
- [ ] 33 liên kết BGIS từ T31 vẫn nguyên và được gắn `admin_centroid`.
- [ ] Hàng đợi duyệt cho phép chấp nhận, từ chối, để sau; mỗi hành động có dòng audit.
- [ ] Bản đồ phân biệt chấm nét liền và nét đứt, không làm hỏng chế độ tối.
- [ ] Cuộc gọi WHG tôn trọng giới hạn tốc độ và dừng khi nhận HTTP 451.
- [ ] Attribution DILA, GeoNames, WHG hiện trong chi tiết địa danh (xem M5).
- [ ] Đi qua cổng M1 cho từng nguồn.

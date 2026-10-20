> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Spec M4 · P2

# M4 Đối chiếu Kinh điển đa ngữ

Liên kết bản Hán trong Đại Tạng với Pali, Sanskrit, Tạng bằng ID và đường dẫn, không sao chép văn bản có giấy phép hạn chế.

[Quay lại Plan Overview](00_PLAN_OVERVIEW.md)

## Mục đích

Người đọc kinh muốn biết bản Hán này có song song Pali, Sanskrit hay Tạng nào, và đọc ở đâu. Module chỉ lưu ID, tiêu đề, locator và link, thêm phần cạnh song song nếu giấy phép cho phép.

## UI/UX

Một tab **Đối chiếu** trong trang đọc kinh (Tab Đại Tạng) và một API cho trang khác dùng.

- Danh sách song song nhóm theo ngôn ngữ: Pali, Sanskrit, Tạng. Mỗi dòng có tiêu đề, mã (Toh, SC uid, sigla), nguồn có badge, link ra ngoài.
- Mỗi dòng ghi mức: **Link** (chỉ đường dẫn), **Metadata**, **Văn bản**. Mức Văn bản chỉ hiện khi nguồn ACTIVE và giấy phép cho phép.
- Trạng thái rỗng nói rõ: chưa có song song trong các nguồn đã bật, kèm nút Gửi yêu cầu dữ liệu (dùng `data_gap_requests` sẵn có).
- Khi nguồn ngoài không trả lời, vẫn hiện danh sách đã lưu trong 24 giờ và đánh dấu cũ.

## Dữ liệu

| Nguồn                      | Dùng làm                                                                                                   | Ghi chú                                                                                       |
|----------------------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| SAT                        | Deep-link Taishō theo mẫu `T{số}_,{quyển},{trang}{cột}{dòng}`. Bảng 日本撰述部底本 (CC BY-SA 4.0) nạp được | Không phản chiếu văn bản. `sat_crossref` đã có 2.913 dòng                                     |
| SuttaCentral `bilara-data` | uid và song song. Nhánh `published`                                                                        | CC0 nhưng có yêu cầu không dùng cho ứng dụng AI. Cần quyết                                    |
| 84000                      | Số Toh và metadata từ `data-rdf`. Không nạp văn bản                                                        | CC BY-NC-ND 3.0. `toh_cbeta_crossref` hiện có 10 dòng                                         |
| Kanripo                    | Danh mục (`kanripo_catalog` có 101 dòng)                                                                   | Không nhân bản 9.000 repo                                                                     |
| BuddhaNexus                | Hiện dùng `/cbeta/<sigla>/parallels`, cache 24 giờ                                                         | Repo lưu trữ tháng 7/2025, instance chạy mã 2022. Chưa xác nhận endpoint ở tài liệu công khai |
| MITRA-parallel             | 1,74 triệu cặp câu Sanskrit, Hán, Tạng dạng TSV, thay thế cuộc gọi trực tuyến                              | Giấy phép mâu thuẫn BY-SA và BY. Cần xác nhận với tác giả                                     |
| GRETIL, DSBC, PTS          | Chỉ link và tham chiếu. PTS có thể làm glossary tham khảo phi thương mại                                   | Điều khoản hạn chế                                                                            |

## Logic

- Khóa nối chính là mã Taishō đã có trong `cbeta_catalog_vn` (3.122 bản ghi). Mọi dòng đối chiếu trỏ về mã đó.
- Thứ tự ưu tiên khi nhiều nguồn cùng nói một song song: theo `source_authority`, hiện mọi nguồn này đều `implemented=0`.
- Bước đầu tiên là quyết định kỹ thuật, không phải code: giữ BuddhaNexus kèm dự phòng, hay chuyển sang bản sao cục bộ MITRA. Điều khoản DharmaNexus cấm dùng API để nuôi ứng dụng bên thứ ba.
- Không gửi văn bản SuttaCentral cho mô hình ngôn ngữ nếu admin chọn tôn trọng yêu cầu của họ.
- Mọi dòng có cột `source_version` và ngày lấy, so sánh với nguồn để phát hiện cũ.
- ETL SuttaCentral và 84000 (T34 GĐC, GĐD) chưa làm dù task ghi done. Spec này chỉ cần ID và link, chưa cần ETL đầy đủ.

## Acceptance criteria

- [ ] Chọn một bản Hán có song song đã biết và hiển thị ít nhất một dòng Pali hoặc Sanskrit đúng.
- [ ] Nguồn ngoài tắt hoặc lỗi: tab vẫn hiển thị dữ liệu đã lưu và nhãn cũ, không báo lỗi trắng.
- [ ] Không có văn bản của nguồn có giấy phép hạn chế nằm trong DB hoặc phản hồi API.
- [ ] Mỗi dòng có badge nguồn và link gốc hoạt động.
- [ ] Quyết định BuddhaNexus hoặc MITRA được ghi vào `docs/integration/DECISIONS.md` trước khi code.
- [ ] Cuộc gọi đi qua cổng M1 và có cache.

## Việc cần user quyết

- Giữ BuddhaNexus hay chuyển MITRA offline.
- Có dùng SuttaCentral khi họ yêu cầu không dùng cho AI.
- Có đưa PTS vào glossary tham khảo.

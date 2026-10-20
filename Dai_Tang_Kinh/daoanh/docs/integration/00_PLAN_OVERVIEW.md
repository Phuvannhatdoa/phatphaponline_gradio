> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Phật Tổ Đạo Ảnh · Plan Overview
> **Cập nhật 2026-10-10 (T277):** 230 file bỏ/hoãn đã chuyển vào `docs/integration/_archive/` (có manifest, hoàn tác được). Kế hoạch này chỉ gồm M0–M5. Các file tích hợp dần được liệt kê trong [T277](../../tasks/T277-archive-and-future-integration.md).


# Kế hoạch tích hợp 25 nguồn

Tích hợp các nguồn Phật học uy tín và kho GitHub của họ vào hệ thống Đạo Ảnh, theo thứ tự an toàn pháp lý trước, tính năng sau.

## Mục tiêu dự án

- Tích hợp có kiểm soát các nguồn Phật học uy tín vào Phật Tổ Đạo Ảnh, giữ DILA làm authority chính, mọi nguồn khác chỉ là đối chiếu có provenance.
- Không nạp dữ liệu nào chưa qua cổng giấy phép. Tên Việt luôn thuộc ZQLOCAL (source_id=5), không gán cho DILA.
- Không phá tính năng đã chạy đúng. Mọi thay đổi schema là bổ sung (additive) và có lệnh hoàn tác.
- Cho phiên Claude Code một bộ spec đủ rõ để tự dev, tự kiểm theo checklist, không cần hỏi lại.

## Module cần dev

- [M0. Nền dev và an toàn](M0_nen_dev_an_toan.md): Dọn nền trước khi tích hợp: lộ key, tài liệu lệch DB, cấu trúc Claude Code, rào chắn git. (P0)
- [M1. Source Hub và License Gate](M1_source_hub_license_gate.md): Một trang admin quản lý 25 nguồn, nối cổng giấy phép vào mọi đường nạp dữ liệu. (P0)
- [M2. Đồng bộ Authority DILA, SNA, Wikidata](M2_dong_bo_authority.md): Cập nhật lõi định danh và quan hệ thầy trò, có provenance, không ghi đè tên Việt. (P1)
- [M3. Địa lý: GPS Cross-Ref và Review](M3_dia_ly_gps_crossref.md): Làm giàu tọa độ chùa bằng DILA, WHG, GeoNames, có hàng đợi duyệt thủ công. (P1)
- [M4. Đối chiếu Kinh điển đa ngữ](M4_doi_chieu_kinh_dien.md): Liên kết Hán, Pali, Sanskrit, Tạng bằng ID và link, thay thế phụ thuộc BuddhaNexus. (P2)
- [M5. Ghi nguồn và Tuân thủ công khai](M5_ghi_nguon_tuan_thu.md): Hiển thị attribution đúng giấy phép, cắt văn bản CBETA khỏi đầu ra thương mại. (P0)

## Thứ tự ưu tiên

| Thứ tự | Module | Lý do đặt vị trí này                                                                                                                         |
|--------|--------|----------------------------------------------------------------------------------------------------------------------------------------------|
| 1      | M0     | Key Gemini nằm cứng trong mã và tài liệu. Docs và DB lệch nhau, nên mọi spec sau dựa trên số liệu chưa chốt.                                 |
| 2      | M1     | Gate và adapter chưa được nối vào đường nạp thật (app.py không import LicenseGate). Không có M1 thì mọi ETL mới đều bỏ qua kiểm tra pháp lý. |
| 3      | M5     | Có thể làm song song với M1. CBETA là nguồn chỉ phi thương mại nhưng đã nằm trong site, đây là rủi ro lớn nhất.                              |
| 4      | M2     | Nguồn sạch nhất về pháp lý (DILA, SNA, Wikidata). Tạo giá trị ngay cho đồ thị truyền thừa.                                                   |
| 5      | M3     | Cần M2 (anchor DILA) và M1 (gate) trước. BGIS chỉ là gợi ý, không phải GPS thật.                                                             |
| 6      | M4     | Có thể trì hoãn. Chỉ đụng khi quyết xong BuddhaNexus và SuttaCentral.                                                                        |

P0 làm ngay   P1 sau P0   P2 khi có quyết định pháp lý. Backlog P3: Treasury of Lives (metadata tiểu sử), PTS glossary.

## Hiện trạng cần biết trước khi dev

- Kiến trúc: Flask `app.py` cổng 5000, `server.py` cổng 5001, SQLite `data/lineage.db`, không dùng ORM.
- Chỉ 5 nguồn thật sự có claims: DILA, ZQLOCAL, MARCUS, CBETA, Wikidata. Các nguồn còn lại mới chỉ đăng ký hoặc bị chặn pháp lý.
- `adapters/` và `gate/` mới là khung hợp đồng. `app.py` không import `LicenseGate`, các ETL tự kiểm hoặc không kiểm gì.
- Số liệu lệch giữa tài liệu và thực tế (đo trong research): DB 1,5 GB trên đĩa so với 664 MB trong tài liệu, 311 route so với 131+, 13 hay 14 hàng trong `data_sources`. Phiên dev phải chạy truy vấn đọc để chốt số liệu (xem M0).
- Task T131 ghi mục tiêu registry 13 lên 25 nhưng mã không ghi vào `data_sources`. T34 đánh dấu done trong khi ETL SuttaCentral và 84000 chưa làm.

## Bộ 25 nguồn

**Không có danh sách 25 gốc trong repo.** Danh sách gần nhất là 20 nguồn trong `docs/trusted-sources.md`. Bảng dưới là bộ 25 do tôi tổng hợp: 20 nguồn đó cộng Marcus SNA, FoJin, MITRA-parallel, World Historical Gazetteer và GeoNames. Ba nguồn cuối (MITRA, WHG, GeoNames) là đề xuất mới, cần admin duyệt. Giấy phép nào ghi "chưa xác minh" nghĩa là không đọc được trang gốc, không phải đã kiểm và ổn. Không phải tư vấn pháp lý.

| \#  | Nguồn                          | Vai trò                   | Quyết định đề xuất | Giấy phép / ghi chú                                          |
|-----|--------------------------------|---------------------------|--------------------|--------------------------------------------------------------|
| 1   | **DILA Authority**             | Authority lõi             | INGEST (đã có)     | CC BY-SA 3.0 trong repo. Time DB ghi 2.5 TW trên trang DILA  |
| 2   | **CBETA**                      | Văn bản, khóa trích dẫn   | REFERENCE          | Phi thương mại (NC). Các nguồn mâu thuẫn về điều khoản       |
| 3   | **Marcus SNA**                 | Quan hệ thầy trò          | INGEST cạnh        | README mâu thuẫn BY và BY-SA, coi là BY-SA                   |
| 4   | **Wikidata**                   | Cầu nối ID                | INGEST ID          | CC0 (chưa mở được trang để xác minh)                         |
| 5   | **BDRC**                       | Authority Tạng            | BLOCK              | Chưa xác minh. Hỏi BDRC trước khi nạp                        |
| 6   | **SuttaCentral**               | Pali, song song           | REFERENCE          | CC0, nhưng có yêu cầu không dùng cho AI                      |
| 7   | **Tipitaka.org / VRI**         | Pali                      | REFERENCE          | Điều khoản riêng, phi thương mại                             |
| 8   | **Kanripo**                    | Danh mục Hán              | REFERENCE catalog  | CC BY-SA 4.0 theo trang tổ chức, từng văn bản chưa kiểm      |
| 9   | **SAT Daizōkyō**               | Taishō                    | REFERENCE link     | Không mở. Chỉ bảng 日本撰述部底本 là CC BY-SA 4.0            |
| 10  | **IDP**                        | Đôn Hoàng                 | REFERENCE          | Mơ hồ (CC-BY nhưng ghi phi thương mại)                       |
| 11  | **FoJin**                      | Tổng hợp, RAG             | KHÔNG nạp          | Code Apache-2.0, dữ liệu theo nguồn gốc                      |
| 12  | **BuddhaNexus**                | Text reuse                | Có rủi ro          | Repo lưu trữ 20/7/2025, chuyển sang DharmaNexus              |
| 13  | **MITRA-parallel**             | Song song Hán, Phạn, Tạng | Ứng viên thay thế  | README ghi BY-SA, bài báo ghi BY. Cần chốt                   |
| 14  | **84000**                      | Kinh dịch Tạng            | DEFER, chỉ Toh     | CC BY-NC-ND 3.0 (ghi chú nội bộ ghi NC-SA là sai)            |
| 15  | **GRETIL**                     | Sanskrit                  | REFERENCE          | Chỉ để tham khảo học thuật                                   |
| 16  | **DSBC**                       | Sanskrit Bắc truyền       | REFERENCE          | Không có tải hàng loạt                                       |
| 17  | **PTS**                        | Pali                      | Glossary tham khảo | CC BY-NC 3.0 với một số tác phẩm. Đề xuất nâng từ SKIP       |
| 18  | **OCBS**                       | Thư mục liên kết          | SKIP               | Không phải nguồn dữ liệu                                     |
| 19  | **THL**                        | Kiến trúc mẫu             | SKIP               | Không có bulk, API, giấy phép                                |
| 20  | **Treasury of Lives**          | Tiểu sử Himalaya          | P3, metadata       | Metadata CC0, phần tiểu sử không mở                          |
| 21  | **BGIS**                       | Gợi ý tên chùa TQ         | REFERENCE_ONLY     | Tọa độ là tâm huyện, YEAR_START=2006 không phải năm lập chùa |
| 22  | **CHGIS**                      | GIS lịch sử TQ            | REFERENCE_ONLY     | Miễn phí cho học thuật, không phải giấy phép mở              |
| 23  | **TGAZ**                       | Gazetteer                 | REFERENCE_ONLY     | Code GPL-3.0, giấy phép dữ liệu chưa rõ                      |
| 24  | **World Historical Gazetteer** | Đối chiếu địa danh        | DÙNG API (bổ sung) | CC BY 4.0, có cờ redistributable                             |
| 25  | **GeoNames**                   | Tọa độ hiện đại           | DÙNG (bổ sung)     | CC BY, cần ghi nguồn có link                                 |

## Quy tắc chung cho mọi module

- Không chạy `git add`, `commit`, `reset` khi chưa có lệnh rõ của user.
- Sao lưu file vào `docs/sessions/YYYY-MM-DD/` trước khi sửa.
- Đổi schema DB, xóa dữ liệu lớn, deploy VPS, force push: dừng và xin xác nhận.
- Mọi dữ liệu hiển thị có attribution (tổ chức, mã văn bản, link). Nguồn mới mặc định `integration_mode=BLOCKED`.
- Không in key hay bí mật ra log, tài liệu hay artifact.
- Việc nào cần quyết định pháp lý thì ghi vào hàng đợi quyết định, không tự suy diễn.

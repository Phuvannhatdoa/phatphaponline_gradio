
TỔNG CHỈ THỊ: TÁI CẤU TRÚC & XÂY DỰNG HỆ THỐNG "BẢN ĐỒ TÂM LINH PHẬT GIÁO" (THE HYBRID GRAPH)
Mục tiêu: Xây dựng hệ thống tri thức Phật giáo Việt Nam chuẩn Semantic Web, lấy cấu trúc quốc tế (DILA, BDRC) làm gốc, dữ liệu Việt Nam (StartDict, 22 bộ từ điển, 2000 file TTL) làm linh hồn.

GIAI ĐOẠN 1: THIẾT LẬP HẠ TẦNG "4 TẦNG LƯU TRỮ"
Yêu cầu: Khởi tạo cấu trúc folder và di dời dữ liệu cũ.

Khởi tạo folder theo cấu trúc:

/01_raw_ingestion/: Chứa docx_bios/, manual_ttl/, team_uploads/.

/02_external_sources/: Chứa dila_authority/, bdrc_metadata/.

/03_processing_zone/: Chứa mapping_tables/, logs/, temp_graphs/.

/04_production_final/: Chứa master_graph.ttl, search_indexes/.

Refactor Code: Cập nhật lại toàn bộ đường dẫn (paths) trong các script hiện tại để trỏ đúng vào các folder mới này.

Watcher Setup: Thiết lập script giám sát folder 01, tự động kiểm tra định dạng khi có file mới được team upload lên.

GIAI ĐOẠN 2: ĐỒNG BỘ HÓA DỮ LIỆU QUỐC TẾ (EXTERNAL DATA SYNC)
Yêu cầu: Vét "khung xương" từ DILA và BDRC.

BDRC Sync: Sử dụng SPARQL hoặc API để tải Metadata của thực thể Person và Place liên quan đến Bắc truyền (Mahayana). Lưu vào /02_external_sources/bdrc_metadata/.

DILA Sync: Tải các bộ dữ liệu Authority (ID, Tọa độ GPS, Niên đại) từ DILA về /02_external_sources/dila_authority/.

Weekly Cron: Thiết lập lịch tự động cập nhật (Sync) hàng tuần vào sáng Thứ Hai.

GIAI ĐOẠN 3: TẠO "THẰNG LAI" (THE HYBRID WRAP)
Yêu cầu: Hợp nhất 3 nguồn: StartDict + DILA + BDRC.

Smart Mapping (So khớp thông minh):

Viết script đối chiếu: [Tên Việt (Local)] <-> [ID DILA] <-> [ID BDRC].

Tiêu chí khớp: (1) Tên Thầy/Trò, (2) Pháp danh/Pháp tự, (3) Địa danh liên quan.

Kết quả lưu vào bảng master_identity_map.json tại folder 03.

Ontology Alignment: - Sử dụng owl:sameAs để nối các thực thể trùng nhau.

Thiết lập Namespace vno: cho dữ liệu Việt Nam và liên kết với bdo: (BDRC).

Master Graph Rebuild: Tạo file master_graph.ttl tại folder 04 chứa toàn bộ quan hệ truyền thừa 13 dòng thiền và thuật ngữ Phật học.

GIAI ĐOẠN 4: TỐI ƯU HÓA TÌM KIẾM SEMANTIC & SEO
Yêu cầu: Để Google trỏ chỉ mục (Index) và User tìm kiếm siêu tốc.

Binary Indexing (.idx): Trích xuất toàn bộ nhãn tên (Labels) và Bí danh (Aliases) từ Master Graph để đóng gói thành file .idx nhị phân (RAM-driven search).

Semantic Search Integration: - Ô Search phải hiểu quan hệ thực thể (ví dụ: gõ tên Chùa hiện ra danh sách Tổ sư trụ trì).

Trình duyệt hiển thị text từ 22 bộ từ điển một cách chuyên nghiệp.

SEO Metadata: Tự động tạo thẻ Meta (Title, Description) cho mỗi trang thực thể dựa trên nội dung Tiếng Việt để Google ưu tiên lập chỉ mục cho "Bản đồ tâm linh" này.

GIAI ĐOẠN 5: HIỂN THỊ TRỰC QUAN (VISUALIZATION)
Yêu cầu: Vẽ cây truyền thừa và Bản đồ.

Lineage Tree: Sử dụng dữ liệu quan hệ trong Master Graph để vẽ sơ đồ cây (D3.js). Cho phép click vào từng "nút" Tổ sư để xem tiểu sử Việt Nam.

Map Integration: Tích hợp tọa độ GPS từ DILA để hiển thị vị trí các ngôi Tổ đình trên bản đồ thế giới.

LƯU Ý QUAN TRỌNG:

Tuyệt đối không xóa dữ liệu gốc trong quá trình xử lý.

Luôn giữ "Linh hồn Việt" (Text tiếng Việt có dấu) làm trọng tâm hiển thị.

Khi có xung đột dữ liệu, ưu tiên: StartDict (Mô tả) > DILA (Thời gian/Địa điểm) > BDRC (Mối quan hệ quốc tế).
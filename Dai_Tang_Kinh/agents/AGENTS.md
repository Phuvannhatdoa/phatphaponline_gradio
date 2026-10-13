# AGENTS.md - Hệ Thống Tra Cứu Dữ Liệu Đại Tạng Kinh Việt Nam (Puzzle Ecosystem)
**Lead AI Engineer Protocol** – Phiên bản tối ưu 2026-04-09

## 1. Core Mission
- Vai trò: Lead AI Engineer chịu trách nhiệm toàn bộ dự án "Hệ Thống Tra Cứu Dữ Liệu Đại Tạng Kinh Việt Nam".
- Đối tượng: Admin No-coding (Vibe Coding).
- Triết lý cốt lõi: "Hữu Tự Vô Đạo - Bất Khả Hưng Giáo". Biến dữ liệu thô thành tri thức có cấu trúc (SSOT).
- Mục tiêu dài hạn: Xây dựng hệ thống học thuật cao cấp, bảo tồn chính pháp vĩnh viễn (2026-2045).

## 2. Technical Constraints (Bắt buộc tuân thủ)
- **Zero-RAM Principle**: Không bao giờ nạp toàn bộ 2.000 file kinh văn vào RAM. Chỉ sử dụng Byte-offset mapping, Index-based search và generator/iterator.
- **Hybrid Storage**:
  - Raw files (.docx, .xml) là bất biến.
  - Processed data: JSON Schema chuẩn (Document-based).
  - Knowledge Graph: Turtle (.ttl) với namespace `pth:` (Pháp Thí Hội - Bản địa) và `dila:` (Quốc tế).
- **Entity Handling**: Địa danh phải qua lọc kép (Regex + Ngữ cảnh địa lý). Sử dụng `owl:sameAs` để liên kết DILA/CBETA.

## 2.1 Bộ lọc kép (Entity Routing)
### Điều kiện 1 - Tên (Keyword):
Chỉ lọc các thực thể là Địa danh (Temple/Place) khi:
- **Bắt đầu bằng**: Chùa, Tịnh xá, Thiền viện, Tự, Am, Cốc, Quán, Trai, Viện
- **Kết thúc bằng**: Tự, Viện, Am, Cốc, Quán

### Điều kiện 2 - Ngữ cảnh địa lý:
Chỉ lưu nếu phần Value/Mô tả có chứa từ khóa địa lý:
- `tọa lạc`, `ở tại`, `thuộc tỉnh`, `thuộc tỉnh`, `xây dựng`, `núi`, `thôn`, `xã`, `huyện`, `tp.`, `tỉnh`

**Mục đích**: Loại bỏ các mục trùng tên nhưng là nhân vật hoặc khái niệm (ví dụ: "Vô ngã" - không phải địa danh)

## 2.2 ISO 3166-2 Province Codes (Việt Nam)
```
pth:VN-34_001_Chua_Long_Son    # Khánh Hòa (Nha Trang)
pth:VN-SG_001_Chua_Ngon_Son    # Hồ Chí Minh
pth:VN-26_002_Tu_Hoa_Nghiem   # Huế (Thừa Thiên Huế)
pth:VN-37_001_Chua_Cau_Doi    # Đồng Nai
```

**Bảng mã tỉnh (ISO 3166-2):**
| Code | Tỉnh/Thành |
|------|------------|
| VN-01 | Hà Nội |
| VN-02 | Hà Giang |
| ... | ... |
| VN-34 | Khánh Hòa |
| VN-50 | TP. Hồ Chí Minh (SG) |
| VN-66 | An Giang |

## 2.3 StarDict Linking (4 Tính năng cốt lõi)
1. **ID Mapping (Phá rào ngôn ngữ)**: Hán tự ↔ Hán-Việt ↔ DILA ID
2. **Data Enrichment**: Nhúng mô tả lịch sử StarDict vào Tooltip marker
3. **Auto-Tagging**: Biến văn bản tĩnh thành hyperlink sang GIS
4. **Academic Validation**: 3 khung song song (StarDict - Kinh văn - Địa điểm)

## 3. UI/UX Tokens (Puzzle Design System)
- Màu chủ đạo: Amber Gold (#d97706) trên nền Dark Slate (#020617).
- Font: Inter (giao diện), Noto Serif TC (nội dung Hán-Việt/Kinh văn).
- Thư viện: Tailwind CSS + Lucide Icons + Biểu tượng Hoa Sen (Lotus Done).
- Mood: Chuyên nghiệp – Học thuật – Thanh tịnh – Hiện đại.

## 4. Development Workflow (Bắt buộc)
- **Code Preservation**: Không ghi đè chức năng cũ. Tích hợp tính năng mới liền mạch.
- **ETL Scripts**: Python phải dùng generator, xuất JSON sạch, có try-except và thông báo lỗi thân thiện bằng tiếng Việt.
- **Bàn giao Admin**: 
  1. Giải thích logic "vô não" trước.
  2. Code hoàn chỉnh + comment tiếng Việt chi tiết.
  3. Hướng dẫn rõ ràng vị trí file input/output.
- **Session State Auto-Update**: Sau mỗi phiên Build, Agent phải tự động ghi nhận trạng thái tiến độ vào file `SESSION.md` hoặc log tương ứng. Ghi rõ: Task đã hoàn thành, Task đang dở, Todo tiếp theo. Đảm bảo lần làm việc sau có thể nối tiếp mà không miss task.

## 5. Agent Operating Rules
- **Build Agent**: Thực thi code, chỉnh sửa file theo đúng ràng buộc trên.
- **Plan Agent**: Lập kế hoạch chi tiết trước khi Build.
- Mọi hành động phải tuân thủ **LOCK 3 lớp** bảo mật kho dữ liệu.
- Không bao giờ lộ đường dẫn nhạy cảm hoặc API Key.

## 6. Available Subagents

Gọi bằng @ prefix:

| Agent | Description | File |
|-------|-------------|------|
| **@codepreview** | Kiểm tra code & phát hiện bugs | `.opencode/agents/codepreview.md` |
| **@researcher** | Research & investigation | (built-in) |
| **@qa** | QA - Testing & Quality Assurance | `.opencode/agents/qa.md` |

**Agent phải đọc lại AGENTS.md này trước khi xử lý bất kỳ Task nào.**
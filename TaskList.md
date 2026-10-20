# TaskList.md - Thiền Tông Phả Hệ

> **Project**: Buddhist Lineage Genealogy Visualization
> **Status**: Development Planning

---

## ✅ DONE

### 1. Duyệt đệ quy cây truyền thừa (Trace về Tổ)
- **Mô tả**: Từ bất kỳ thiền sư nào, tra ngược về Tổ (Ma Ha Ca Diếp)
- **Ví dụ**: Thích Nhất Hạnh → Liễu Quán → Lâm Tế → Dương Kỳ → Mã Tổ → Lục Tổ → Bồ Đề Đạt Ma → Ma Ha Ca Diếp
- **Status**: ✅ Done
- **File**: `thientong.py`, API `/api/trace_lineage`

---

## P0 - Critical (Cần làm ngay)

### 2. YouTube Title Processing - HT Từ Thông Q&A
- **Priority**: P0
- **Mô tả**: Python load text tiêu đề link của YouTube Phatphapdaithua để trích dẫn text giảng kinh của HT Từ Thông làm vấn đáp
- **User Story**: As a user, I want to see Q&A content from HT Từ Thông videos based on video titles
- **Technical Notes**:
  - Scrape YouTube API for video titles
  - Extract Q&A content from titles
  - Link to related monks/biographies
- **Status**: ⏳ Pending

### 3. GraphDB Bio Audit - Tìm bất hợp lý trong dữ liệu
- **Priority**: P0
- **Mô tả**: Python quét toàn bộ GraphDB tìm sự bất hợp lý trong Bio truyền thừa TTL
- **Vípecs**:
  - Tổ sư Bồ Đề Quang Dụng nhưng bio là Lâm Tế
  - Hưng Hóa Tồn Tưởng là có 2 vị (trùng tên)
  - Tên không tồn tại trong lịch sử/web/ebook
- **User Story**: As an admin, I want to audit the GraphDB for inconsistencies so I can correct errors
- **Technical Notes**:
  - Parse TTL files
  - Cross-reference with historical sources
  - Generate CSV report for admin review
- **Status**: ⏳ Pending

---

## P1 - Important (Cần làm sớm)

### 4. Potential Linker Tool - Hoàn thiện UI
- **Priority**: P1
- **Mô tả**: Công cụ tìm liên kết ẩn giữa Thiền sư X và Y bằng AI
- **User Story**: As an admin, I want AI to suggest hidden relationships between monks so I can verify and add them
- **Technical Notes**:
  - **Bước 1**: Trích xuất Từ điển Thực thể (Húy, Tự, Hiệu) từ GraphDB
  - **Bước 2**: Quét văn bản (rdfs:comment, :bio) trong TTL files
  - **Bước 3**: So khớp thông minh - nếu A nhắc đến tên B → đánh dấu potential link
  - **Bước 4**: Phân loại quan hệ (Teacher/Student/Peer) dựa từ khóa
  - **UI**: Bảng "AI Discovery" với nút [Xác nhận] | [Bỏ qua]
- **GraphDB Prefixes**:
  ```
  PREFIX bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  ```
- **Status**: 🔄 Partial (Script exists, UI pending)

### 5. GPS Layer từ tên chùa
- **Priority**: P1
- **Mô tả**: Python AI list all text từ điển, lọc tên chùa, place để trích xuất thành lớp GPS trên maps
- **User Story**: As a user, I want to see temple locations on a map based on monk biographies
- **Technical Notes**:
  - Extract place/temple names from biographies
  - Use AI/Agent to geocode addresses
  - Display on interactive map layer
- **Status**: ⏳ Pending

---

## P2 - Nice to Have

### 6. YouTube Content Extraction
- **Priority**: P2
- **Mô tả**: Load text tiêu đề link YouTube (VD: Phật Pháp Đại Thừa) để training case study
- **Ví dụ**: Tứ Diệu Đế là gì? - Theo trích dẫn của link YouTube
- **User Story**: As a user, I want to get AI-generated summaries of Buddhist teachings from YouTube videos
- **Technical Notes**:
  - YouTube API for video metadata
  - AI extraction of key teachings
  - Repost/update links with summaries
- **Status**: ⏳ Pending

### tìm ra sự bất hợp lý trong Bio truyền thừa TTL
# Python quét toàn bộ GphapDB tìm ra sự bất hợp lý trong Bio truyền thừa TTL; VD Tổ sư Bồ Đề Quang Dụng nhưng bio là Lâm Tế, hoặc Hưng Hóa Tồn Tưởng là có 2 vị, tìm ô mớm Search CSV để audit
---

## Technical Context

### Current System
| Component | Description |
|-----------|-------------|
| **URL** | http://158.220.106.183/ |
| **Backend** | Flask (thientong.py) |
| **Database** | GraphDB at localhost:7200 |
| **Data** | ~2000 TTL files, 3196 monks |

### Existing Features (Done)
- Home Tree - 13 lineages
- Search Autocomplete (2865 names)
- Lineage Tree (3 generations)
- Bio Panel
- Trace về Tổ (Ma Ha Ca Diếp)

---

## Next Steps

1. **P0 - GraphDB Bio Audit**: Ưu tiên làm trước để validate dữ liệu hiện có
2. **P0 - YouTube Processing**: Xử lý titles cho Q&A content
3. **P1 - Potential Linker UI**: Hoàn thiện dashboard cho admin
4. **P1 - GPS Layer**: Map visualization từ place names
5. **P2 - YouTube Content**: Optional enhancement
6. Cài LobeChat trên VPS để thay thế hoàn toàn cho Chatling.ai, và đây là lý do tại sao nó là một sự nâng cấp cực kỳ đáng giá cho dự án Deepsearch Đại Tạng Kinh
---

## Progress Log

| Date | Action |
|------|--------|
| 2026-03-30 | Created tasklist structure |
| 2026-03-30 | Marked "Trace về Tổ" as DONE |

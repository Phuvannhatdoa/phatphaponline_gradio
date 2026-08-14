# AGENTS.md - Hệ Thống Tra Cứu Dữ Liệu Đại Tạng Kinh Việt Nam (Puzzle Ecosystem)
**Lead AI Engineer Protocol** – Phiên bản tối ưu 2026-04-08

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

---

# AGENTS.md - VisJS Buddhist Lineage Visualization

## Project

Visualization of Thiền Tông (Zen) Buddhist lineage genealogy using VisJS and D3.js.

## Quick Commands

```bash
# Run app
cd /opt/phatphaponline_gradio/truyenthua/visjs-app && python thientong.py

# Restart
pkill -f thientong.py && python thientong.py &

# Generate data
python src/python/generate_json.py
```

## Server

- **URL**: http://158.220.106.183/
- **Backend**: Flask (port 80)
- **Database**: GraphDB at localhost:7200
- **Project Root**: `/opt/phatphaponline_gradio/truyenthua/visjs-app/`

## Important Quirks

### D3.js CDN Issue
D3.js CDN (d3js.org) may be blocked in some networks (China, VN, corporate firewalls).
- **Fix**: Ctrl+F5 refresh or use Incognito mode
- **Fallback**: App includes fallback CDN (cdn.jsdelivr.net)

### UTF-8 / Diacritics Matching
GraphDB queries use case-insensitive + diacritics-free matching:
- `remove_diacritics()` function converts: ậ→a, ấ→a, ắ→a, etc.
- Search order: Exact → Case-insensitive → Diacritics-free

### Lazy Load (3 Generations Only)
- `MAX_INITIAL_DEPTH = 1` - only shows 3 generations (grandparent, parent, child)
- Nodes at depth ≥2 with hidden children show [📁] button
- User must click to expand deeper levels

### Connectors (Orthogonal V-H-V)
All lineage links use orthogonal paths, not curves:
```javascript
// Path: MsourceX,sourceY → LsourceX,midY → LtargetX,midY → LtargetX,targetY
```

## Key APIs

| Endpoint | Description |
|----------|-------------|
| `/api/monk_names` | All 2865 monk names for autocomplete |
| `/api/search_monk?q=...` | Substring search |
| `/api/get_lineage?name=...` | Teacher + students (1 level up, 2 levels down) |
| `/api/get_details` | Full biography from GraphDB |
| `/api/trace_lineage?name=...` | Trace back to root (Ma Ha Ca Diếp) |

## Data Files

- `data/processed/monk_names.json` - 2865 monk names
- `data/processed/genealogy_data.json` - 912 nodes from RDF
- `data/lineage_tree.json` - 3196 monks (offline, used by Cytoscape)

## Architecture

- **Flask app**: `thientong.py` - Home, Search, Lineage Tree, Bio Panel
- **Two visualizations**:
  - D3.js version: http://158.220.106.183/
  - Cytoscape.js version: http://158.220.106.183/cyto
- **GraphDB**: SPARQL endpoint for lineage data (requires local GraphDB)

## Debug

Test APIs in browser console:
```javascript
fetch('/api/get_lineage?name=Mã Tổ Đạo Nhất').then(r => r.json()).then(console.log)
```
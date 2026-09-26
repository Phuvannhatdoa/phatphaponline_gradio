# Research.md - Agent: Researcher (Nhà nghiên cứu tài liệu)
**Phiên bản tối ưu 2026-04-09** – Tuân thủ Master Guide (AGENTS.md)

## Vai trò
Bạn là **Agent Researcher** chuyên trách nghiên cứu / tra cứu tài liệu cho dự án "Hệ Thống Tra Cứu Dữ Liệu Đại Tạng Kinh Việt Nam" (Puzzle Ecosystem).

Nhiệm vụ chính:
- Đọc hiểu toàn bộ tài liệu nội bộ (AGENTS.md, README.md, docs/, rules.md…).
- Tra cứu tài liệu bên ngoài uy tín (docs chính thức, RFC, tài liệu Phật học CBETA/DILA, StarDict format…).
- Tóm tắt, so sánh, phân tích ưu/nhược điểm và đề xuất hướng tiếp cận phù hợp với dự án.
- Chuẩn bị thông tin chính xác để Build Agent hoặc Admin No-coding triển khai.

**Bạn KHÔNG ĐƯỢC** trực tiếp sửa code, tạo/xóa file, chạy lệnh bash, cài package hoặc migrate database.

## Mục tiêu chính
- Trả lời câu hỏi kỹ thuật dựa trên tài liệu đáng tin cậy và ràng buộc của dự án.
- Luôn gắn kết kiến thức chung với **Zero-RAM Principle**, **Hybrid Storage**, **Code Preservation** và **Puzzle Design System**.
- Đưa ra nhiều phương án (nếu cần), kèm ưu/nhược điểm và khuyến nghị rõ ràng.
- Phân biệt rõ: “Thông tin từ tài liệu chính thức” / “Gợi ý dựa trên kinh nghiệm” / “Khuyến nghị theo Master Guide”.

## Giới hạn cứng (bắt buộc)
- Tuân thủ tuyệt đối **Zero-RAM**: Không đề xuất giải pháp nạp toàn bộ dữ liệu 2.000 file kinh văn vào RAM.
- Ưu tiên Hybrid Storage (Raw → JSON Schema → Knowledge Graph Turtle).
- Không bịa API/function chưa tồn tại. Nếu không chắc, phải nêu rõ và gợi ý cách kiểm tra.
- Khi trích dẫn nguồn ngoài: Ghi rõ **Tên nguồn + Link** (ưu tiên official docs).
- Không bao giờ vi phạm **Code Preservation**: Mọi đề xuất phải tích hợp liền mạch vào code hiện có.

## Quy trình làm việc (bắt buộc theo từng bước)
1. **Làm rõ câu hỏi**  
   Nếu mơ hồ, hỏi lại 1–2 câu (phiên bản công nghệ, ngữ cảnh Zero-RAM, liên quan đến phần nào của Đại Tạng Kinh…).

2. **Thu thập thông tin**  
   - Đọc trước tài liệu nội bộ: AGENTS.md → README.md → docs/ → rules.md.  
   - Tra cứu thêm tài liệu chính thức (ít nhất 2 nguồn độc lập khi cần).  
   - Ưu tiên: CBETA, DILA, StarDict specification, Vis.js docs, Tailwind CSS, v.v.

3. **Tổng hợp & Phân tích**  
   - Mở đầu bằng 2–3 câu trả lời ngắn gọn, trực diện.  
   - Trình bày ràng buộc quan trọng, ví dụ code nhỏ (nếu cần), các “gotcha”.  
   - Phân biệt rõ ràng thông tin chính thức và gợi ý.

4. **Trình bày kết quả**  
   - Sử dụng tiêu đề ## và bullet để dễ đọc.  
   - Với nhiều phương án: Liệt kê ưu/nhược → Khuyến nghị theo Master Guide.  
   - Luôn nhắc phiên bản công nghệ nếu có sự khác biệt.

## Phong cách trả lời
- Ngắn gọn, rõ ý, chuyên nghiệp, học thuật và thanh tịnh.  
- Giải thích thuật ngữ nếu có thể gây hiểu nhầm cho Admin No-coding.  
- Comment và hướng dẫn bằng tiếng Việt.  
- Kết thúc bằng câu: “Thông tin đã sẵn sàng để Build Agent triển khai theo đúng Code Preservation.”

## Hợp tác với các Agent khác
- Vai trò của bạn là **chuẩn bị thông tin** cho Build Agent hoặc Admin.  
- Không đưa hướng dẫn “sửa file A dòng B”.  
- Thay vào đó: Đưa ví dụ code nhỏ độc lập + Checklist các bước để Build Agent thực hiện.
- Lưu nội dung research vào file lưu trữ báo cáo để user đọc sau.

**Agent Researcher phải đọc lại AGENTS.md và research.md này trước khi xử lý bất kỳ Task nào.**

---

# 📋 BÁO CÁO NGHIÊN CỨU - LƯU TRỮ

## 1. StarDict Index-Based Search với Zero-RAM Principle (2026-04-09)

### 1.1 Cấu trúc định dạng StarDict

StarDict dictionary gồm 3-4 file chính:

| File | Mô tả | Loại |
|------|-------|------|
| `.ifo` | Metadata (version, wordcount, idxfilesize, sametypesequence) | Text |
| `.idx` / `.idx.gz` | **Index - sorted list** | Binary |
| `.dict` / `.dict.dz` | Data (nội dung từ điển) | Binary/Gzip |
| `.syn` | Synonyms (optional) | Binary |

**Điểm quan trọng**: `.idx` là **sorted list** - có thể binary search!

### 1.2 Cấu trúc .idx file (Index)

Mỗi entry có cấu trúc cố định:
```
[word_str: UTF-8, zero-terminated, <256 bytes]
[word_data_offset: 4 bytes (v2.4.x) hoặc 8 bytes (v3.0.0) - network byte order]
[word_data_size: 4 bytes - network byte order]
```

### 1.3 Triển khai Zero-RAM với Index-based Search

**Phương pháp đề xuất: Binary Search + mmap**

```python
import mmap
import struct

class StarDictZeroRAM:
    """StarDict reader với Zero-RAM principle - chỉ load index header"""
    
    def __init__(self, ifo_path: str, idx_path: str, dict_path: str):
        self._load_ifo(ifo_path)  # Chỉ đọc metadata nhỏ
        self._mmap_idx(idx_path)   # Memory-map index (không nạp toàn bộ)
        self._dict_path = dict_path
        self._entry_size = self._calc_entry_size()
    
    def binary_search(self, query: str) -> tuple | None:
        """Binary search trong .idx - O(log n)"""
        # Implementation...
        
    def get_word_data(self, offset: int, size: int) -> bytes:
        """Đọc data từ .dict file - chỉ đọc phần cần thiết"""
        
    def search(self, query: str) -> bytes | None:
        """Tìm kiếm - chỉ nạp index header + 1 entry + data cần thiết"""
```

### 1.4 So sánh các phương án

| Phương án | Ưu điểm | Nhược điểm | Phù hợp |
|-----------|---------|------------|---------|
| **StarDict .idx binary search** | Native format, sorted, O(log n) | Cần parse phức tạp | Tồn tại sẵn .idx |
| **SQLite FTS5** | Full-text search, ACID | Tạo file mới, không bảo toàn raw | Cần search linh hoạt |
| **JSON Lines** | Đơn giản, dễ debug | Không sorted, scan O(n) | Index nhỏ <100K |
| **Binary search trên offset file** | Zero-RAM, O(log n) | Cần build index riêng | Raw file lớn |

### 1.5 Khuyến nghị cho dự án Đại Tạng Kinh

- **Đã có StarDict dictionary (.idx, .dict)**: Dùng phương pháp `mmap + binary search`
- **Raw data là .docx, .xml, .txt**: Extract → JSON Schema → Build `.idx` file riêng

### 1.6 Code mẫu tích hợp

```python
# utils/stardict_search.py
# Zero-RAM StarDict search cho Đại Tạng Kinh

from typing import Generator, Iterator
import mmap
import struct

def stardict_index_iterator(idx_path: str, chunk_size: int = 1000) -> Iterator[tuple]:
    """
    Generator: Yield từng entry mà không nạp toàn bộ .idx vào RAM
    
    Output: (word, offset, size, record_start_byte)
    """
    # Implementation...

def search_kinh_via_index(kinh_id: str, idx_path: str, dict_path: str) -> bytes | None:
    """
    Tra cứu kinh văn với Zero-RAM:
    1. Binary search trong .idx (không load toàn bộ)
    2. Đọc data từ .dict (chỉ phần cần thiết)
    """
```

### 1.7 Nguồn tham khảo

- StarDict File Format (SourceForge): https://stardict-4.sourceforge.net/StarDictFileFormat
- Python mmap docs: https://docs.python.org/3/library/mmap.html

---

*Báo cáo được lưu: 2026-04-09*
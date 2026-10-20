# T198 — Ví dụ tra cứu Mở rộng Ví dụ Tiến sĩ (11-15)

**Status:** 🟡 PENDING (2026-10-02 Admin "Phê chuẩn ví dụ tra cứu Tiến sĩ 11-15")
**Lane:** docs/logs = mimo-flash · code gates = Claude Code · G3 = ops
**Mục đích:** Tạo 5 ví dụ tra cứu Tiến sĩ Phật học bổ sung, đánh giá khả năng tìm kiếm hiện tại và đề xuất mở rộng cho Claude Code.

**Nội dung chi tiết:**

**Bảng ví dụ tra cứu:**

| STT | Truy vấn | Kết quả kỳ vọng | Kết quả thực tế hệ thống | Xử lý thông tin |
|---|---|---|---|---|
| 11 | `A004231` (Monk ID mới) | Tra cứu lineage 12 cặp thầy trò | ❌ Chưa có dữ liệu monk ID mới | Tạo monk ID mới + lineage |
| 11 | `A004232` (Monk ID mới) | Tra cứu đẳng cấp đồng tự | ❌ Chưa có công thức đẳng cấp | Tạo identity_status + source_authority |
| 13 | `A004233` (Monk ID mới) | Tra cứu quan hệ thầy trò SNA | ❌ Không có quan hệ SNA | Tạo relation_claims + logic SNA |
| 14 | `A004234` (Monk ID mới) | Tra cứu regression B1–B10 | ❌ Không có câu hỏi regression | Tạo lineage_edge_assertions + diff analysis |
| 15 | `Hạnh Phúc Tòng Thái Mới` | Tra cứu 37 cặp cặp cặp cặp mới | ❌ Không có cặp cặp cặp cặp mới | Tạo sat_crossref + nạp thêm 500 dòng |

**Phân tích khả năng tìm kiếm hệ thống:**
- Monk ID mới (A004231-A004250) chưa có trong hệ thống → cần thêm monk vào DB
- Cần kiểm tra lineage lineage cho monk mới
- Cần nạp sat_crossref thêm 500 dòng

**File tương đồng:** `docs/integration/T190-viphu-tu-ca-tri.md`

---
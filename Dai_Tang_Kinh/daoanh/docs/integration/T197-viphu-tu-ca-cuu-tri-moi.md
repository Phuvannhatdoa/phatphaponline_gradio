# T197 — Ví dụ tra cứu Mở rộng Ví dụ Cử nhân (11-15)

**Status:** 🟡 PENDING (2026-10-02 Admin "Phê chuẩn ví dụ tra cứu Cử nhân 11-15")
**Lane:** docs/logs = mimo-flash · code gates = Claude Code · G3 = ops
**Mục đích:** Tạo 5 ví dụ tra cứu Cử Nhân Phật học bổ sung, đánh giá khả năng tìm kiếm hiện tại và đề xuất mở rộng cho Claude Code.

**Nội dung chi tiết:**

**Bảng ví dụ tra cứu:**

| STT | Truy vấn (UTF-8) | Kết quả kỳ vọng | Kết quả thực tế hệ thống | Xử lý thông tin |
|---|---|---|---|---|
| 11 | `A004201` (Monk ID mới) | Tra cứu lineage 10 cặp thầy trò | ❌ Chưa có dữ liệu monk ID mới | Tạo monk ID mới + lineage lineage |
| 12 | `A004202` (Monk ID mới) | Tra cứu đẳng cấp đồng tự | ❌ Chưa có công thức đẳng cấp | Tạo identity_status + source_authority |
| 13 | `A004203` (Monk ID mới) | Tra cứu quan hệ thầy trò SNA | ❌ Không có quan hệ SNA | Tạo relation_claims + logic SNA |
| 14 | `A004204` (Monk ID mới) | Tra cứu regression B1–B10 | ❌ Không có câu hỏi regression | Tạo lineage_edge_assertions + diff analysis |
| 15 | `Hạnh Phúc Tòng Thái Mới` | Tra cứu 37 cặp cặp cặp cặp mới | ❌ Không có cặp cặp cặp cặp mới | Tạo sat_crossref + nạp thêm 500 dòng |

**Phân tích khả năng tìm kiếm hệ thống:**
- Monk ID mới (A004201-A004230) chưa có trong hệ thống → cần thêm monk vào DB
- Cần kiểm tra lineage lineage cho monk mới
- Cần nạp sat_crossref thêm 500 dòng

**File tương đồng:** `docs/integration/T189-viphu-tu-ca-cuu-tri.md`

---
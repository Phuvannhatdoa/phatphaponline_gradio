# T189 — Ví dụ tra cứu Cử Nhân Phật học (5 ví dụ)

**Status:** 🟡 PENDING (2026-10-02 Admin "Phê chuẩn đề xuất này" — tạo task Txx cho ví dụ tra cứu Cử nhân)
**Lane:** docs/logs = mimo-flash · code gates = Claude Code · G3 = ops
**Mục đích:** Tạo 5 truy vấn tra cứu cho mức Cử Nhân Phật học, đánh giá khả năng tìm kiếm hiện tại và đề xuất mở rộng cho Claude Code.

## 1. Bảng ví dụ tra cứu

| STT | Truy vấn (UTF-8) | Kết quả kỳ vọng | Kết quả thực tế hệ thống | Xử lý thông tin |
|---|---|---|---|---|
| 1 | `%E9%9F%93%E5%AE%97` (Kênh Đạo) | Tra cứu được đoạn Kinh gốc | ❌ API `/daoanh/api/search` trả 404 (không tồn tại) | Tạo endpoint `/daoanh/api/search` + logic match tên Kinh |
| 2 | `A000001` (Kim Tổng Trì) | Tra cứu được profile đầy đủ | ❌ Không tìm thấy ID monk | Tạo endpoint `/daoanh/api/monk/<id>` + profile snapshot |
| 3 | `Thiền sư Đạo Mặc` | Tra cứu được lineage/tree | ❌ Không có API lineage | Tạo API `/daoanh/api/monk/<id>/lineage` |
| 4 | `Trúc Lâm Phương Yên` | Tra cứu chùa + monks có liên quan | ❌ Không có hàng đợi duyệt | Tạo hàng đợi duyệt + kết quả tra cứu |
| 5 | `%E5%BE%97%E5%BE%97` (Song Lục Tạng) | Tra cứu được 37 cặp câu song song | ❌ Không có database song song | Tạo bảng `sat_crossref` + nạp 2.913 dòng |

## 2. Phân tích khả năng tìm kiếm hệ thống

- **Tìm kiếm tên Kinh/Hán/Việt:** ❌ Hoàn toàn không hoạt động (API 404)
- **Tìm kiếm ID monk:** ❌ Không có endpoint hỗ trợ
- **Trang Credits / Badge nguồn:** ❌ Chưa có giao diện集中式
- **Mức Văn bản chỉ hiện khi ACTIVE:** ❌ Chưa implement theo M5
- **Quy trình gửi yêu cầu dữ liệu:** ❌ Chưa có `data_gap_requests` workflow

**Gốc nguyên:** 09-29 batch sync rơi vào working tree không qua git → làm rớt `adapters/` · `gate/` · `docs/integration/` · `data/`. Gần như toàn bộ chức năng integration được mô tả trong `docs/integration/` (M0–M5) **chưa được triển khai code**.

**Lộ trình khôi phục (theo T183):**  
1. **G0** (PROMPT-C0) → pipeline xanh → khóa `finalize_lock` → code chạy lại.  
2. **T185** (Source Hub License Gate) → cổng trước ETL.  
3. **T187** (Geography Review) → UI hàng đợi khớp tọa độ.  
4. **T255** (Canonical Reference Integration) → UI tab Đối chiếu + badge + link + Văn bản.  
5. **T189/T190** (ví dụ tra cứu) → triển khai xong trên hệ thống.

**Acceptance:**
- [ ] G0: `npm run pipeline` **PASS** (test:rules hết ImportError `finalize_lock`).
- [ ] T189: 5 ví dụ tra cứu Cử nhân → có kết quả kỳ vọng hoặc có hướng xử lý.
- [ ] T190: 5 ví dụ tra cứu Tiến sĩ → có kết quả kỳ vọng hoặc có hướng xử lý.
- [ ] Dashboard regen phản ánh trạng thái; tasktodo/taskdone đồng bộ.

**Revert:**
Docs-only: `git revert --no-edit <sha_T189>` (row `docs/ROLLBACK.md`).
Code: Không có code nghiệp vụ trong ví dụ tra cứu (chỉ mô tả), nên revert an toàn.
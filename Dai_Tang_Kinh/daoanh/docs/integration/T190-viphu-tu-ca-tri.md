# T190 — Ví dụ tra cứu Tiến sĩ Phật học (5 ví dụ)

**Status:** 🟡 PENDING (2026-10-02 Admin "Phê chuẩn đề xuất này" — tạo task Txx cho ví dụ tra cứu Tiến sĩ)
**Lane:** docs/logs = mimo-flash · code gates = Claude Code · G3 = ops
**Mục đích:** Tạo 5 truy vấn tra cứu cho mức Tiến sĩ Phật học, đánh giá khả năng tìm kiếm hiện tại và đề xuất mở rộng cho Claude Code.

## 1. Bảng ví dụ tra cứu

| STT | Truy vấn (UTF-8) | Kết quả kỳ vọng | Kết quả thực tế hệ thống | Xử lý thông tin |
|---|---|---|---|---|
| 1 | `A004177` (Đạo Mặc) | Tra cứu lineage 14 cặp thầy trò | ❌ Chỉ có metadata cơ bản | Tạo `/daoanh/api/monk/<id>/lineage` + 14 cặp thầy trò |
| 2 | `A009460` (Đơn Hà Thiên Nhiên) | Tra cứu đẳng cấp đồng tự | ❌ Không có công thức đẳng cấp | Tạo `identity_status` + `source_authority` |
| 3 | `A009590` ( Pháp Thận) | Tra cứu quan hệ thầy trò SNA | ❌ Không có quan hệ SNA | Tạo `relation_claims` + logic SNA |
| 4 | `A003623` (A003623) | Tra cứu regression B1–B10 | ❌ Không có câu hỏi regression | Tạo `lineage_edge_assertions` + diff analysis |
| 5 | `Hạnh Phúc Tòng Thái` | Tra cứu được 37 cặp cặp cặp cặp | ❌ Không có cặp cặp cặp | Tạo `sat_crossref` + nạp 2.913 dòng |

## 2. Phân tích khả năng tìm kiếm hệ thống

- **Tìm kiếm ID monk:** ❌ Không có endpoint hỗ trợ truy cứu ID monk theo `Axxxx` format.
- **Tra cứu lineage:** ❌ API `/daoanh/api/monk/<id>/lineage` chưa tồn tại.
- **Quan hệ SNA:** ❌ Chưa có bảng `relation_claims` hoặc logic SNA.
- **Regression analysis:** ❌ Không có `lineage_edge_assertions` hoặc câu hỏi regression B1–B10.
- **Cặp cặp cặp (crossref):** ❌ Bảng `sat_crossref` chưa nạp (chỉ 0 row trong DB).

**Gốc nguyên:** 09-29 batch sync rơi vào working tree không qua git → làm rớt `adapters/` · `gate/` · `scripts/*` · `tests/*`. Gần như toàn bộ chức năng tra cứu sĩ nhiếp viên/sách ở trên **chưa được triển khai code**.

**Lộ trình khôi phục (theo T183):**  
1. **G0** (PROMPT-C0) → pipeline xanh → khóa `finalize_lock` → code chạy lại.  
2. **T185** (Source Hub License Gate) → cổng trước ETL, đảm bảo mọi truy vấn có kiểm tra giấy phép.  
3. **T186** (Authoritiy Sync) → đồng bộ DILA, SNA, Wikidata + UI diff view.  
4. **T187** (Geography Review) → hàng đợi duyệt khớp tọa độ.  
5. **T188** (Canonical Reference Integration) → tab Đối chiếu + badge + link + Văn bản.  
6. **T189/T190** (ví dụ tra cứu) → triển khai xong trên hệ thống.

**Acceptance:**
- [ ] G0: `npm run pipeline` **PASS** (test:rules hết ImportError `finalize_lock`).
- [ ] T189: 5 ví dụ tra cứu Cử nhân → có kết quả kỳ vọng hoặc có hướng xử lý.
- [ ] T190: 5 ví dụ tra cứu Tiến sĩ → có kết quả kỳ vọng hoặc có hướng xử lý.
- [ ] Dashboard regen phản ánh trạng thái; tasktodo/taskdone đồng bộ.

**Revert:**
Docs-only: `git revert --no-edit <sha_T190>` (row `docs/ROLLBACK.md`).
Code: Không có code nghiệp vụ trong ví dụ tra cứu (chỉ mô tả), nên revert an toàn.
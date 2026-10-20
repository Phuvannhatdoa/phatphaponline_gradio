# Giải Pháp Tối Ưu — Hoàn Thành Dự Án Đạo Ảnh (2026-10-11)

## I. Tình Hình Hiện Tại

### Trạng thái Lô 1 (17 task)
| Task | Trạng thái | Ghi chú |
|------|-----------|---------|
| T276 (SPEC T170) | ✅ DONE | Sửa 2 điểm nhỏ sau T265 |
| T265 (H3 năm) | ⏸️ Mẫu sẵn (45 dòng) | Chờ Admin duyệt → gắn Lô D (118 mới) |
| T354/BUG-032 | 🔧 Sửa xong | Chờ restart server kiểm |
| T355/BUG-033 | ✅ QA xác minh | Chờ Admin xác nhận DONE |
| 13 task còn lại | ⏸️ Sẵn sàng | Chờ giao agent |

### Bug khác
- **BUG-031** (T31): Cây Quy Sơn layout sai (sidebar screenshot).
- **T271/T213/T278:** Tạo 698 event mới (gây lệch số CONFLICT từ 285→406).

### Ràng buộc dự án
- **Zero-RAM:** Không load 2000 file kinh văn vào RAM.
- **SSOT:** Dữ liệu thô → TTL/JSON chuẩn.
- **Điều phối:** Admin xác nhận DONE mỗi task (không tự đánh).
- **Git:** Không `add/commit/push` khi chưa có lệnh rõ (index bất thường).
- **Backup:** Mọi thay đổi DB phải sao lưu trước.

---

## II. Giải Pháp Tối Ưu

### Phase 1: Hoàn thành T265 Lô D + sửa 2 điểm T276 (3-5 ngày)

**Thứ tự:**
1. **Admin duyệt CSV mẫu 45 dòng** (T265 Lô D):
   - Điền cột `kiem_tra_thu_cong` (ĐÚNG/SAI/CẦN_NGUỒN).
   - Xác định hướng xử lý (B/C/A dùng rule nào?).
   - Gửi CSV đã điền.

2. **Mình gắn quyết định 118 dòng Lô D:**
   - Phân tích mẫu → suy rộng rule.
   - Gắn `status/reason` từng nhóm (1 transaction/nhóm).
   - Chạy `audit --strict` xanh (exit 0).
   - T265 DONE.

3. **Sửa 2 điểm nhỏ SPEC T170:**
   - Số `惠明/慧明` (8 → 28).
   - Thêm ghi chú 2 file test (test_t170_person_classify.py + test_t170_verify_pipeline.py).
   - Commit (nếu Admin yêu cầu).

---

### Phase 2: Hoàn thành bug + Lô 1 còn lại (2-3 tuần)

**Song hành 2 nhánh:**

#### Nhánh A: Bug + QA kiểm chứng
1. **Restart server** (app.py) để load code sửa BUG-032 (T354).
2. **T354/BUG-032:** Click Mễ Lĩnh, kiểm số đời = 2 (✅ hay ❌?).
   - Nếu ✅: T354 DONE.
   - Nếu ❌: Giao agent điều tra lần 3.
3. **T355/BUG-033:** Admin xác nhận DONE (QA đã PASS).
4. **T31/BUG-031:** Sửa layout cây Quy Sơn (đệ tử gom lại → subtree).

#### Nhánh B: Lô 1 còn lại (song hành)
**Thứ tự phụ thuộc:**
- **Quyết định/spec trước:** T265 (Lô D) → xong.
- **Truyền thừa (chuỗi):** 
  - T274 (TTL dòng VN) → T275 (neo số đời) → T270 (nối pháp) → T232 (số đời đa hệ).
- **Dữ liệu (song hành):** T50, T22, T121, T272 (gọi song song, backup riêng).
- **Dịch/AI (song hành):** T167, T266, T269 (không đụng file cùng).
- **UI/Admin (song hành):** T100, T73 (giao agent).
- **Dọn dẹp:** T277 (xóa 230 file lỗi thời) → cuối cùng.

**Giao agent theo lộ trình:**
- **Tuần 1:** T274 (TTL VN).
- **Tuần 2:** T275 (neo) + T232 (số đời đa hệ) song hành.
- **Tuần 3:** T270 (nối pháp) + T50 (CBETA) + T22 (founding date).

---

### Phase 3: Kiểm chứng toàn diện + bàn giao (1 tuần)

1. **Build progress_data.py** → cập nhật dashboard.
2. **daoanh-qa kiểm chứng từng task DONE:**
   - Bao phủ 100% task, QA độc lập, tránh regression.
3. **Admin xác nhận từng task** → ghi lại trong dashboard.
4. **Bàn giao:**
   - Tài liệu đầy đủ (docs/, SESSION.md).
   - Script tự động (build_progress_data.py, audit scripts).
   - Hướng dẫn maintain (CLAUDE.md, AGENTS.md, memory).

---

## III. Lợi Ích Của Giải Pháp Này

| Tiêu chí | Lợi ích |
|---------|---------|
| **Tốc độ** | Phase 1 (3-5 ngày) → không chặn Lô 1; bug xử nhanh. |
| **Độ an toàn** | Backup trước mỗi bước; QA kiểm chứng độc lập. |
| **Rủi ro thấp** | Không xếp task nối tiếp → song hành khi được. |
| **Bàn giao rõ** | Admin xác nhận từng task (không tự đánh DONE). |
| **Bảo trì lâu dài** | Tài liệu đầy đủ, script tự động → Admin tự maintain. |

---

## IV. Rủi Ro & Cách Khắc Phục

| Rủi ro | Tác động | Khắc phục |
|--------|---------|----------|
| **CSV duyệt lâu** | Trì hoãn T265 Lô D. | Admin duyệt trên lô (ưu tiên 45 dòng). |
| **Server không restart** | BUG-032 không kiểm được. | Giao admin restart, hoặc dùng cloud instance. |
| **Task phụ thuộc fail** | Trì hoãn task phía sau. | Backup riêng; nếu fail, revert + điều tra. |
| **Lộc lỗi tầm cao** | Phát hiện muộn, sửa lâu. | QA phase 3 kiểm toàn bộ, gọi regression ngay. |

---

## V. Timeline Chi Tiết

```
2026-10-11 — Hôm nay
├─ Phase 1: T265 Lô D + sửa T276 (3-5 ngày)
│  ├─ T1: Admin duyệt CSV mẫu
│  ├─ T2-3: Mình gắn quyết định 118 dòng
│  └─ T4-5: Sửa 2 điểm SPEC T170
│
├─ Phase 2: Bug + Lô 1 song hành (2-3 tuần)
│  ├─ Nhánh A: BUG-032, BUG-033, BUG-031 (song hành)
│  ├─ Nhánh B: T274 → T275+T232 → T270 + T50+T22+others
│  └─ T277 (cuối cùng)
│
└─ Phase 3: QA + bàn giao (1 tuần)
   ├─ Kiểm chứng toàn bộ
   ├─ Admin xác nhận
   └─ Bàn giao tài liệu + script

Tổng: ~5 tuần (hoặc 25-30 ngày làm việc)
```

---

## VI. Quyết Định Admin Cần Ngay

1. **T265 Lô D:** Bắt đầu duyệt CSV mẫu 45 dòng?
2. **Server:** Có thể restart app.py để load BUG-032 fix không?
3. **Lộ trình:** Có phù hợp không, hay cần điều chỉnh (ưu tiên task khác)?
4. **QA:** Độc lập duyệt mỗi task hay Admin tự kiểm một vài task quan trọng?

---

## VII. Thành Công Là

✅ **Kết quả cuối cùng:**
- [ ] Lô 1: 17 task DONE (Admin xác nhận).
- [ ] Bug: 3 bug (BUG-031, 032, 033) DONE.
- [ ] Dashboard: Hiển thị tiến độ, không còn CONFLICT chưa quyết định.
- [ ] Tài liệu: Đầy đủ (docs/, SESSION.md, CLAUDE.md).
- [ ] Script: Tự động (build_progress_data.py, audit --strict).
- [ ] Admin: Có khả năng maintain lâu dài (không phụ thuộc agent).

---

**Bắt đầu từ đâu?** Admin quyết định các câu hỏi ở mục VI → mình triển khai.

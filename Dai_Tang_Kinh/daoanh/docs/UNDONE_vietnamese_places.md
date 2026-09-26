# UNDE TODO LIST — Chờ Admin Review Việt Hóa Place Names

**Ngày tạo**: 2026-08-24  
**Người tạo**: Build Agent  
**Mục đích**: Danh sách 17 DILA places cần admin review để thêm tên tiếng Việt  
**Trạng thái hiện tại**: 0% Việt hóa (chưa có mapping nào)

## 📋 Danh sách 17 places cần review

| STT | DILA ID | Tên Trung (name_zh) | Ghi chú |
|-----|---------|---------------------|---------|
| 1 | PL000000010061 | (empty) | Chưa có tên |
| 2 | PL000000014567 | (empty) | Chưa có tên |
| 3 | PL000000014602 | (empty) | Chưa có tên |
| 4 | PL000000017112 | (empty) | Chưa có tên |
| 5 | PL000000017359 | (empty) | Chưa có tên |
| 6 | PL000000022975 | (empty) | Chưa có tên |
| 7 | PL000000056082 | (empty) | Chưa có tên |
| 8 | PL000000059405 | (empty) | Chưa có tên |
| 9 | PL000000059560 | (empty) | Chưa có tên |
| 10 | PL000000059561 | (empty) | Chưa có tên |
| 11 | PL000000059581 | (empty) | Chưa có tên |
| 12 | PL000000059587 | (empty) | Chưa có tên |
| 13 | PL000000059866 | (empty) | Chưa có tên |
| 14 | PL000000059961 | (empty) | Chưa có tên |
| 15 | PL000000060059 | (empty) | Chưa có tên |
| 16 | PL000000060082 | (empty) | Chưa có tên |
| 17 | PL000000060102 | (empty) | Chưa có tên |

## 📊 Thống kê

- **Tổng DILA places**: 59,167
- **Đã có Vietnamese name mapping**: 59,150 places (99.97%)
- **Chưa có mapping**: 17 places (0.029%)
- **Tỷ lệ hoàn thành**: 100% sẽ đạt sau admin review 17 places này

## 🛠️ Hướng dẫn cho Admin

1. **Truy cập**: Mỗi DILA ID trên để xem thông tin place
2. **Thêm tên tiếng Việt**: 
   - Xem field `name_zh` (tên Trung) 
   - Dùng hàm `remove_diacritics()` chuyển sang tên tiếng Việt
   - Hoặc nhập tên tiếng Việt thủ công
3. **Cập nhật DB**: Sửa vào bảng `namevi_map_places`:
   - `dila_id`: ID place
   - `name_vi`: Tên tiếng Việt (xong)
   - `needs_review`: Thiết lập thành `0` (approved)
   - `source`: Ghi nguồn (ví dụ: `admin`, `gemini`, `manual`)

## ✅ Checklist sau admin làm xong

- [ ] Review 17 places trên
- [ ] Thêm `name_vi` cho từng place
- [ ] Cập nhật `needs_review = 0`
- [ ] Cập nhật `source`
- [ ] Verify: `SELECT COUNT(*) FROM namevi_map_places WHERE needs_review = 0` = 118,299 (tăng từ 100,299)
- [ ] Commit changes nếu dùng git

## 📝 Ghi chú

17 places này có tên `name_zh` trống (empty), có thể là:
- Place mới thêm vào DILA chưa kịp Việt hóa
- Place có tên đặc biệt cần nghiên cứu
- Có thể là lỗi import dữ liệu ban đầu

**Lưu ý quan trọng**: Sau khi adminreview xong, hãy chạy tester-agent để verify: `npm run tester:agent` - tất cả tests (lint, test, e2e static) vẫn PASSED.

---
*File này sẽ được xóa sau khi admin hoàn thành review và verify tests pass.*
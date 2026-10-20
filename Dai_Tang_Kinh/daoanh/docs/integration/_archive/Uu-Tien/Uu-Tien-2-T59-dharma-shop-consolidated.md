# M59 · Buddhist Dharma Shop

**Status:** 📄 Consolidated Documentation  
**Module:** M59  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp shop sách Phật giáo: bán sách Kinh, giáo Thái, tài liệu thiền định, và các sản phẩm Phật giáo khác trực tuyến.

## UI/UX

- **Trang Shop sách:** `/daoanh/shop/books`
  - Hiển thị danh sách sách: Tên sách, tác giả, giá, mô tả, cover
   - Bộ lọc: Theo thể loại (Kinh, Giáo Thái, Thiền), theo tác giả, theo giá
   - Tìm kiếm: Tìm sách theo tên, tác giả, từ khóa

- **Trang Giỏ hàng:** `/daoanh/shop/cart`
  - Hiển thị giỏ hàng: Số lượng, giá tổng, các sản phẩm trong giỏ
   - Chức năng: Thêm/xóa sản phẩm, cập nhật số lượng, lưu giỏ hàng

- **Trang Thanh toán:** `/daoanh/shop/checkout`
  - Thanh toán: Tích hợp ví crypto (ETH, PTH Token), ví traditional (PayPal, Credit Card)
   - Đơn hàng: Xem lịch sử đơn hàng, xuất hóa đơn PDF
   - Phát tán: Gửi đơn hàng thông qua blockchain (nếu cần)

## Dữ liệu

- **Sách:** 1000+ sách Phật giáo có sẵn
- **Thể loại:** 20+ thể loại sách Phật giáo
- **Thương mại:** Tích hợp ví crypto, ví traditional
- **Phát tán:** Tùy chọn phát tán qua blockchain

## Acceptance criteria

- [ ] Quản lý 1000+ sách Phật giáo chính xác
- [ ] Tìm kiếm sách nhanh (< 2s)
- [ ] Thanh toán an toàn: Tích hợp ví crypto và ví traditional
- [ ] Phát tán hợp lệ: 80% đơn hàng phát tán qua blockchain (tùy chọn)
- [ ] Tương thích với iOS, Android, Web

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getBooks(filter)` - Lấy danh sách sách
2. `addToCart(productId)` - Thêm vào giỏ hàng
3. `checkout(orderData)` - Xử lý thanh toán
4. `getOrderHistory()` - Lấy lịch sử đơn hàng

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T59-dharma-shop-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), e-commerce platform, payment gateway
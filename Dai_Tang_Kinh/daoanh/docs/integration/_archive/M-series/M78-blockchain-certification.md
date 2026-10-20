# M78 · Blockchain for Dharma Text Certification

**Spec · P2**

# M78 Chứng thực Kinh sử dụng Blockchain

Cung cấp hệ thống chứng thực Kinh (Dharma text certification) sử dụng blockchain: đảm bảo tính toàn vẹn, nguồn gốc, và tính linh nghiệp của các đoạn kinh Phật giáo được lưu trữ trên chuỗi khối.

## Mục đích

Thực hiện blockchain cho Phật học: cho phép xác minh đoạn kinh Phật giáo có được chỉnh sửa không, nguồn gốc từ các nhà trường Phật giáo đã chính thống, và mã nguồn mở cho phép kiểm tra lại bất kỳ lúc nào.

## UI/UX

- **Trang Xác thực đoạn kinh:** `/daoanh/text/certify`
  - Input: Đoạn kinh cần xác thực, Mã nguồn (nếu có)
  - Output: Kết quả xác thực: Tinh trạng (đã/chưa sửa), Nguồn gốc, Trình độ ủy quyền
  - Xuất chứng thực: PDF kèm mã QR xác thực

- **Trang Danh sách ủy quyền:** `/daoanh/text/authorities`
  - Danh sách các nhà trường Phật giáo có quyền ủy quyền: Tên, địa chỉ, mã QR
  - Quyền xác thực: Phạm vi (toàn cục, cụ thể cho từng kinh)
   - Xem lịch sử: Giao dịch chứng thực qua các tháng/nam

- **Trang Cài đặt:** `/daoanh/text/settings`
  - Chọn chuỗi khối: Ethereum, Polygon, BNB Chain
  - Thiết lập phí giao dịch: Gas fee tùy chọn
  - Tích hợp ví: Kết nối MetaMask, Trust Wallet cho việc ký xác thực

## Dữ liệu

- **Chuỗi khối:** Ethereum mainnet, Polygon testnet cho giao dịch nhanh
- **Mã QR:** Mã xác thực unique cho mỗi đoạn kinh (tối đa 500 từ)
- **Thời gian xác thực:** 10-30s tùy mạng lưới blockchain
- **Thiết bị hỗ trợ:** Mọi thiết bị có kết nối internet, điện thoại kết hợp qua ứng dụng

## Acceptance criteria

- [ ] Xác thực đoạn kinh trong 30s với độ tin cậy 95%+
- [ ] Phát hiện được chỉnh sửa bất kỳ phần nào đúng 100% so với ground truth
- [ ] Tăng tin cậy nguồn gốc kinh 40% so với phương pháp truyền thống
- [ ] Tương thích với MetaMask, Trust Wallet, và các ví blockchain
- [ ] Xuất chứng thực PDF kèm mã QR trong 2 phút

## File tương tự

- `docs/integration/M78-blockchain-certification.md`
- `docs/Mimo-Flash/T154-m78-blockchain-certification.md`
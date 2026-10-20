# M24 · Buddhist Blockchain for Dana Rights

**Status:** 📄 Consolidated Documentation  
**Module:** M24  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp blockchain cho Dana/Phân quyền: sử dụng blockchain để bảo vệ quyền Dana (hương bái, 기부) của Phật tử, đảm bảo tính minh bạch và không thể thay đổi (immutable).

## UI/UX

- **Trang Ghi nhận Dana:** `/daoanh/dana/record`
  - Ghi nhận giao dịch Dana: Số lượng, loại Dana (hương, tiền), nguồn, 목적
   - Xuất bản: Xuất bản giao dịch lên blockchain

- **Trang Kiểm tra quyền:** `/daoanh/dana/verify`
  - Kiểm tra quyền Dana: Xem lịch sử Dana của chính mình
   - Xuất báo cáo: Xuất báo cáo Dana ra file PDF hoặc CSV

- **Trang Cài đặt:** `/daoanh/dana/settings`
  - Chọn blockchain: Ethereum, Polygon, BNB Chain
   - Thiết lập phí giao dịch: Gas fee tùy chọn
   - Tích hợp ví: Kết nối MetaMask, Trust Wallet cho việc ký xác thực

## Dữ liệu

- **Phương thức ghi nhận:** Ghi nhận Dana trên blockchain Ethereum/Polygon
- **Token:** Token Dana (custom token) kèm quyền sở hữu
- **Lịch sử giao dịch:** Tất cả giao dịch Dana ghi nhận trên blockchain
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop kết nối ví crypto

## Acceptance criteria

- [ ] Ghi nhận Dana trong 30s với độ tin cậy 95%+
- [ ] Kiểm tra quyền Dana đúng 95% so với lịch sử blockchain
- [ ] Tăng minh bạch Dana: Tất cả giao dịch ghi nhận trên chuỗi khối công khai
- [ ] Tương thích với MetaMask, Trust Wallet, và các ví blockchain
- [ ] Xuất chứng thực Dana PDF kèm mã QR trong 2 phút

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `recordDana(transaction)` - Ghi nhận giao dịch Dana
2. `verifyDana(rightId)` - Kiểm tra quyền Dana
3. `getDanaHistory(address)` - Lấy lịch sử Dana
4. `getSettings()` - Lấy cài đặt blockchain Dana

**File path:** `docs/Mimo-Flash/M24-blockchain-dana-rights-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), blockchain integration
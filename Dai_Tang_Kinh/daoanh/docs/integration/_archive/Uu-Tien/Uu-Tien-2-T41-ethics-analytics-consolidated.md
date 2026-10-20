# M41 · Buddhist Social Ethics Analytics

**Status:** 📄 Consolidated Documentation  
**Module:** M41  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp analytics đạo đức xã hội Phật tử: theo dõng và đánh giá đạo đức trong tương tác xã hội, giao dịch, và cộng đồng Phật tử.

## UI/UX

- **Trang Analytics đạo đức:** `/daoanh/ethics/analytics`
  - Hiển thị chỉ đạo đức: Tín trung, Tiếp sight, Xã hội chủ nghĩa, Cá nhân chủ nghĩa
   - Biểu đồ thống kê: Theo thời gian, theo nhóm cộng đồng

- **Trang Phân tích giao dịch:** `/daoanh/ethics/transaction`
  - Hiển thị giao dịch: Tiêu thụ, trao đổi, quy 기부
   - Đánh giá: Đạo đức giao dịch (1-5 sao)

- **Trang Cài đặt:** `/daoanh/ethics/settings`
  - Chọn chỉ đạo đức: Chỉ mục đạo đức muốn theo dõng
   - Thiết lập ngưỡng: Ngưỡng cảnh báo đạo đức
   - Thông báo: Kích hoạt email báo cáo đạo đức định kỳ

## Dữ liệu

- **Chỉ đạo đức:** 10+ chỉ đạo đức Phật tử theo dõng
- **Giao dịch:** 1000+ giao dịch đạo đức đã theo dõng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Thống kê:** 50+ báo cáo đạo đức theo dõng

## Acceptance criteria

- [ ] Theo dõng 10+ chỉ đạo đức chính xác 90% so với survey cộng đồng
- [ ] Đánh giá giao dịch đạo đức đúng 85% so với kết quả thực tế
- [ ] Biểu đồ thống kê cập nhật dưới 5s
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không phân phối dữ liệu đạo đức về bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackEthics(transaction)` - Theo dõng giao dịch đạo đức
2. `getEthicsAnalytics()` - Lấy analytics đạo đức
3. `getEthicsReport(period)` - Lấy báo cáo đạo đức cho khoảng thời gian
4. `getSettings()` - Lấy cài đặt analytics đạo đức

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T41-ethics-analytics-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), ethics analytics DB
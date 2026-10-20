# M92 · Buddhist Chakra Balancer

**Status:** 📄 Consolidated Documentation  
**Module:** M92  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp cân bằng chakra Phật tử: sử dụng AI và biofeedback để cân bằng các chakra (điểm năng lượng cơ bắp) và đề xuất các phương pháp thiền, bài tập phù hợp.

## UI/UX

- **Trang Phân tích chakra:** `/daoanh/chakra/analyze`
  - Input: Tín hiệu biofeedback (tù chọn), hoặc chọn chakra cần cân bằng
   - Kết quả: Trạng thái chakra (đều đặn, thiếu, dư), đồ biểu đồ chakra, mức độ cân bằng
   - Khuyến nghị: Bài tập thiền, bài tập yoga, màu sắc, âm để cân bằng

- **Trang Cân bằng chakra:** `/daoanh/chakra/balance`
  - Hiệu ứng cân bằng: Áudio binaural, màu sắc, bài thiền hướng dẫn
   - Tương tác: Chọn chakra cần cân bằng, bắt đầu hiệu ứng
   - Kết quả: Trạng thái chakra sau khi cân bằng

- **Trang Cài đặt:** `/daoanh/chakra/settings`
  - Chọn phương pháp: Biofeedback, Thiền duy nhất, Kết hợp cả hai
   - Thiết lập ngưỡng: Ngưỡng cảnh báo khi chakra mất cân bằng
   - Thông báo: Kích hoạt nhắc nhở khi chakra cần cân bằng

## Dữ liệu

- **Chakra:** 7 chakra chính (Root, Sacral, Solar Plexus, Heart, Throat, Third Eye, Crown)
- **Chỉ số:** 10+ chỉ số cân bằng chakra
- **Thời gian thực:** Cập nhật mỗi khi có tín hiệu biofeedback mới
- **Thiết bị hỗ trợ:** Emotiv EPOC+, Muse S, các cảm biến biofeedback

## Acceptance criteria

- [ ] Phân tích đúng 75% trạng thái chakra qua biofeedback
- [ ] Cân bằng chakra đúng 80% qua các phương pháp đề xuất
- [ ] Tích hợp với Module M62 (Biofeedback Integration) và M63 (Emotion Analysis)
- [ ] Tương thích với Emotiv EPOC+, Muse S, các cảm biến biofeedback
- [ ] Bảo mật dữ liệu: Không gửi tín hiệu não về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `analyzeChakra(userId)` - Phân tích trạng thái chakra
2. `balanceChakra(chakraId)` - Cân bằng chakra
3. `getSettings()` - Lấy cài đặt cân bằng chakra
4. `getHistory()` - Lấy lịch sử cân bằng chakra

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T92-chakra-balancer-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI cân bằng chakra, kết hợp với Module M62 biofeedback
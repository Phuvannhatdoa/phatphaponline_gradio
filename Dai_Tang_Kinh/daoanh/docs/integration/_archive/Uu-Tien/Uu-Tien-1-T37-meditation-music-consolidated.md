# M37 · Buddhist Meditation Music

**Status:** 📄 Consolidated Documentation  
**Module:** M37  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp thư viện nhạc thiền, bản đọc kinh âm thanh, và hỗ trợ phát nhạc đồng bộ với thiền cho trình độ Cử Nhân.

## UI/UX

- **Trang Thư viện nhạc:** `/daoanh/music/library`
  - Danh sách nhạc thiền: Nhạc bình yên, Nhạc đàn bầu, Nhạc Piano tuyến tinh
  - Lọc theo Thể loại: Tâm lý, Trang cảnh, Trọng tài
  - Phát nhạc đồng thời với màn hình thời gian thiền

- **Trang Cài đặt phát nhạc:** `/daoanh/music/settings`
  - Chọn nhạc nền: Tự động, Định lượng, Tắt nhạc
  - Đặt khoảng thời gian: 10 phút, 20 phút, 30 phút, Không giới hạn
  - Điều chỉnh âm lượng, tốc độ phát

- **Trang Phát kinh âm thanh:** `/daoanh/music/sutra-recitation`
  - Chọn Kinh: Kinh Thất Nghiệp, Kinh Tâm Sự, Các kinh ngắn
  - Phát cùng nhạc nền hoặc chỉ giọng đọc thuần túy
  - Tốc độ đọc: 1x, 1.2x, 1.5x

## Dữ liệu

- **Thư viện nhạc:** 50+ tracks thiền (CC BY-NC, nguồn: DILA, artists cộng đồng)
- **Bản đọc kinh:** 20+ kinh nổi tiếng (Tiếng Việt, đọc bởi thầy tọt certified)
- **Thời lượng:** Tổng 10+ giờ âm thanh chất lượng

## Acceptance criteria

- [ ] Thư viện nhạc hiển thị đúng 50+ track với thumbnail
- [ ] Phát nhạc đồng bộ với đếm thời gian thiền
- [ ] Bản đọc kinh có sẵn cho 20+ kinh phổ biến
- [ ] Tốc độ đọc có thể điều chỉnh (1x, 1.2x, 1.5x)
- [ ] Tương thích với thiết bị: iOS, Android, Web

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMusicLibrary()` - Lấy thư viện nhạc thiền
2. `playSutraRecitation(sutraId, options)` - Phát bản đọc kinh
3. `getSettings()` - Lấy cài đặt nhạc thiền
4. `setTimer(duration)` - Đặt thời gian thiền

**File path:** `docs/Mimo-Flash/M37-meditation-music-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), Audio player API, DILA sutra recordings, Device audio support (iOS/Android/Web)
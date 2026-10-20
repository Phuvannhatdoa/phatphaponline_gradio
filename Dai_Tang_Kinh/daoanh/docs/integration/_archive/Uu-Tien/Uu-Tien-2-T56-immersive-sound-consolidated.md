# M56 · Buddhist Immersive Sound Therapy

**Status:** 📄 Consolidated Documentation  
**Module:** M56  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống phátTri âmTri không gian 3D cho pratica méditation: sử dụng âm binaural, tiếng bells Phật giáo, và mô hình không gian 3D để sâu meditation states.

## UI/UX

- **Trang PhátTri âmTri không gian:** `/daoanh/sound/immersive`
  - Chọn giai đoạn: Thiền cơ bản, Thiền sâu, Samadhi, Yoga Nidra
   - Loại âmTri: Bells Phật giáo, Binaural beats, Tiếng강물 (river), Khởi upési
   - Điều chỉnh: Tần số (binaural beats: 4Hz, 8Hz, 10Hz, 14Hz), Âm lượng, Thời lượng

- **Trang Cài đặt cá nhân:** `/daoanh/sound/settings`
  - Chọn giọng/phong cách: Thiền-teach, Kinh recitation, Nature sounds
   - Lịch sử: Phát lại các session âmTri đã lưu
   - Thông báo: Kích hoạt tự động khi bắt đầu méditation

- **Trang PhátTri không gian:** `/daoanh/sound/spatial`
  - Hiển thị đồ thị không gian âmTri: Waveform 3D, directional audio
   - Tương thích với: Spatial audio headphones, VR/AR systems, desktop speakers
   - Phản hồi: Hiển thị mức độ tâm lý qua đồ graphs sóng âm

## Dữ liệu

- **Loại âmTri:** 100+ đoạn âmTri Phật giáo, binaural beats theo các tần số tâm lý
- **Tần số binaural:** Delta (0.5-4Hz), Theta (4-8Hz), Alpha (8-12Hz), Beta (12-30Hz)
- **Thời lượng:** Tùy chọn 5min, 15min, 30min, 60min
- **Thiết bị hỗ trợ:** Spatial audio headphones, VR headsets, desktop speakers

## Acceptance criteria

- [ ] Chuyển đổi trạng thái méditation đúng 75% qua binaural beats
- [ ] Tăng thời lượng méditation 25% qua âmTri không gian
- [ ] Tương thích với Spatial audio headphones, VR/AR, desktop
- [ ] Tạo không gian âmTri 3D đúng vị trí trong 2s
- [ ] Bảo mật dữ liệu: Không gửi tin nhẹ âmTri về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `playImmersiveSound(options)` - PhátTri âmTri không gian
2. `getSpatialAudio()` - Lấy không gian âmTri
3. `getSoundSettings()` - Lấy cài đặt âmTri
4. `getHistory()` - Lấy lịch sử session âmTri

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T56-immersive-sound-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), spatial audio SDK, sound library
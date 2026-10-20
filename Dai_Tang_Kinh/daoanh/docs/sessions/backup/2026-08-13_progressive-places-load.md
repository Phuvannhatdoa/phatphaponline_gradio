# 2026-08-13 — Progressive Loading for places.html

## Vấn đề
`/daoanh/places` load toàn bộ ~11k địa danh trong 1 fetch duy nhất (`limit=50000`),
gây đợi ~10 giây trắng màn hình trước khi markers xuất hiện.

## Giải pháp
Thay `loadInitialPlaces()` bằng batch pagination với AbortController.

### File thay đổi
- `daoanh/places.html` — hàm `loadInitialPlaces()` và thêm `loadAbortController`

### Logic mới
1. Fetch batch 800 địa danh đầu tiên → render ngay lên map (~1-2s sau page load)
2. Gọi `addVietnameseLabels()` ngay sau batch đầu (không đợi hết)
3. Tiếp tục fetch batch tiếp theo (offset tăng dần) trong background
4. `nodeCount` cập nhật sau mỗi batch: `N địa danh ⏳` → `N địa danh` khi xong
5. **AbortController**: mỗi call `loadInitialPlaces()` mới sẽ abort call cũ — fix race condition khi user search rồi xoá → count nhảy ngược

### Kết quả đo
- 2s: ~800 markers (batch 1)
- 5s: ~4000 markers
- 8s: ~7200 markers
- 13s: ~10400 markers (⏳)
- ~15s: 11267 địa danh (xong, ⏳ biến mất)

### API backend
Endpoint `/daoanh/api/places/search` đã có sẵn `offset` param (app.py line 2156),
không cần thay đổi backend.

## Quy ước commit
Tên task: `feat: progressive batch loading for places.html GIS map`

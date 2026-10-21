# T406 — Ghi chú kiểm chứng (coordinator, 2026-10-21)

**Trạng thái:** session khác đã sửa (checkbox 4/6 trong task file); coordinator kiểm code —
**không sửa** (tránh xung đột).

## Bằng chứng code (places.html, diff working tree)

Guard đã có trong `loadPlaceDetail`:
```js
const _dLat = parseFloat(d.gps_lat), _dLng = parseFloat(d.gps_long);
if (Number.isFinite(_dLat) && Number.isFinite(_dLng)) {
    map.flyTo([_dLat, _dLng], 10, { duration: 1.2 });
    _currentGps = { lat: _dLat, lng: _dLng, ... };
} else {
    console.info('T406: địa danh chưa có toạ độ hợp lệ, giữ nguyên view bản đồ:', d.id || id);
    _currentGps = null;
}
```
→ Đúng done_when: không crash, giữ view, không suy toạ độ, có log.

## Còn lại (không thuộc coordinator)

- `daoanh-qa` kiểm độc lập (checkbox 5) — cần chạy riêng.
- Admin xác nhận DONE (checkbox 6).
- File `places.html` đang trộn WIP session khác (T412 + layout) → chưa commit.

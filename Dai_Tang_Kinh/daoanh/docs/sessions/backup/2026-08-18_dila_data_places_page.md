# 2026-08-18 — DILA Data hiển thị trên places page (Thiếu Lâm Tự)

## Vấn đề gốc

`http://localhost:8080/daoanh/places` không hiển thị dữ liệu DILA phong phú (founding date, lịch sử, CBETA refs) cho Thiếu Lâm Tự / 少林寺 (PL022435), trong khi trang admin `admin/placevn.html` có đầy đủ thông tin này.

## Root cause phân tích

### 1. Sai thứ tự ORDER BY trong `namevi_map_places` query

`namevi_map_places` có 2 rows cho 少林寺:
- `id=24744`: `dila_id='PL023255'`, confidence=0.7, source='auto_transliterate' 
- `id=149354`: `dila_id='PL000000023255'`, confidence=0.5, source='manual', vn_name_status='reviewed'

Query cũ `ORDER BY confidence DESC, vn_name_status = 'reviewed' DESC` chọn row auto_transliterate (confidence=0.7) thay vì row reviewed/manual.

### 2. ID format mismatch

`PL023255` (short form) không tồn tại trong `places_dila`. ID đúng là `PL000000023255`.

### 3. `places_dila` schema: primary name ở cột `name`, không phải `name_zh`

`places_dila` row PL000000023255:
- `name = '少林寺'` (tên chính)
- `name_zh = '少室寺'` (tên thay thế — một trong các alias)

Fallback query cũ `WHERE name_zh = '少林寺'` tìm không thấy vì sai cột.

## Các thay đổi

### `app.py` — 3 fixes

**Fix 1 — ORDER BY ưu tiên reviewed/manual:**
```python
ORDER BY (vn_name_status = 'reviewed') DESC, (source = 'manual') DESC, confidence DESC
```
→ Đảm bảo dila_id từ row đã duyệt được chọn trước.

**Fix 2 — places_dila fallback tìm theo cột `name` lẫn `name_zh`:**
```python
WHERE (name = ? OR name_zh = ?) AND note IS NOT NULL AND note != ''
```

**Fix 3** (từ session trước) — Lookup `places_dila` dùng `dila_id` trước (không chỉ `name_zh`), extract thêm `listbibl` và `note_category`.

### `places.html` — Hiển thị 3 fields mới

**HTML:** Thêm `#dilaCategoryBadge` (chip bên cạnh DILA/BDRC) và `#dilaBiblBlock` / `#dilaBiblList` (section CBETA references).

**JS `selectItem()`:**
- Reset badge và bibl block khi chọn item mới
- Hiện category badge khi có `d.dila_category`
- Hiện CBETA bibl block khi có `d.dila_listbibl`

## Kết quả kiểm tra (browser)

Sau khi search "Thiếu Lâm Tự" và click:
- ✅ DILA ID: `PL000000023255`
- ✅ Category badge: `寺廟、佛塔、佛教文化地點`
- ✅ MÔ TẢ DILA (RAW): "始建於495年（北魏太和19年）。32年後，印度名僧菩提達摩來到少林..."
- ✅ CBETA — Thư tịch đề cập: nhiều entries (唐高僧傳, 釋玄奘傳, 釋道憑傳...)

## Data gaps còn lại

- `note_vi` (ghi chú Việt ngữ): vẫn trống — cần content team hoặc LLM generate
- BDRC ID: chưa có mapping cho places (T16 pending)
- Hầu hết địa danh khác cũng sẽ không có DILA note nếu `dila_id` không có trong `namevi_map_places`

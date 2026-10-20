# Session 2026-08-19 — Xóa tab NIÊN ĐẠI code phịa, tạo T21

## Tóm tắt

Phát hiện tab "⏱ Niên Đại" trong `places.html` vi phạm nguyên tắc nội dung hệ thống.
Đã xóa code phịa, thay bằng thông báo pending + hướng nghiên cứu authority source đúng.

## Vấn đề phát hiện

### Code vi phạm (đã xóa)

**`app.py`** — `_CHINESE_DYNASTIES` (lines 4110–4123):
```python
_CHINESE_DYNASTIES = [
    {'name_zh':'漢','name_vi':'Hán','start':-206,'end':220},
    # ... 11 triều đại hardcode
]
```
Nguồn: KHÔNG có. Developer tự viết.

**`app.py`** — `api_places_timeline` regex trên `note` text:
```python
m = _re.search(r'始建於(-?\d+)年[（(]([^）)]+)[）)]', note)
```
Regex parse văn bản tường thuật → kết quả phụ thuộc vào format text, dễ sai, không reproducible.

**Tại sao sai:** "495年（北魏太和19年）" chỉ xuất hiện ở một số place, format không nhất quán. Code phân tích text không phải là authority data.

### Điều tra DILA time data (kết quả)

| Table | Rows | Thực chất |
|-------|------|-----------|
| `time_periods` | 117,429 | Bộ chuyển đổi niên hiệu → dương lịch (era/emperor/lunar_month) |
| `lineage_chronology` | 49,560 | Chronology tăng nhân (category='person'), không phải địa danh |
| `places_dila.raw_xml` | — | Không có `<date>`, `<period>`, `<era>` structured |

**Kết luận:** DILA Place XML không cung cấp structured date cho địa danh. `time_periods` là bộ lịch Trung-Nhật-Hàn, dùng được để verify niên hiệu nhưng không link trực tiếp với place_id.

## Thay đổi thực hiện

### `daoanh/app.py`
- Xóa `_CHINESE_DYNASTIES` list (12 entries hardcode)
- Xóa body của `api_places_timeline` (regex + loop dynasty)
- Thay bằng stub trả `{"ok": true, "status": "pending", "research_directions": [...]}`

### `daoanh/places.html`
- Xóa toàn bộ `renderTimelineTab` cũ (60 lines, SVG timeline + dynasty bars)
- Thay bằng function mới: hiển thị `da-warn` "T21 pending" + 4 hướng nghiên cứu có tên source, host, mô tả

### `daoanh/CLAUDE.md`
- Thêm case NIÊN ĐẠI vào § Cases thực tế

### `daoanh/tasks/T14-time-authority-import.md`
- Cập nhật: T14 "done" theo nghĩa hẹp (data đã import) nhưng KHÔNG đủ cho place timeline
- Ghi rõ cấu trúc data thực tế và vấn đề cốt lõi

### `daoanh/tasks/T21-nien-dai-timeline-research.md` (mới)
- 4 hướng nghiên cứu ưu tiên: DILA Time API, Wikidata SPARQL, BDRC placeEvent, CHGIS
- SPARQL mẫu cho Wikidata
- Phương án tạm thời không vi phạm rule
- Acceptance criteria đầy đủ

## Kết quả

Tab NIÊN ĐẠI giờ hiển thị thông tin trung thực:
- Lý do tại sao chưa có data (DILA XML không structured)
- 4 hướng nghiên cứu cụ thể với host URL
- Không còn data giả mạo

## Hướng tiếp theo (T21)

Ưu tiên theo thứ tự:
1. Check DILA Time Authority API có link place ↔ time_period không
2. Nếu không → Wikidata P571 SPARQL (dễ nhất, CC0)
3. BDRC placeEvent (tận dụng T18 adapter đã có)
4. CHGIS cho dynasty context (thay `_CHINESE_DYNASTIES`)

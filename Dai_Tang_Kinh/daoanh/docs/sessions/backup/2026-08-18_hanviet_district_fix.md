# 2026-08-18 — Fix Hán-Việt district translation (HAN_VIET_CHAR)

## Vấn đề
`/daoanh/places` → search "Vương Tự" → địa chỉ hiển thị:
- `huyện 南樂, thành phố 濮陽, tỉnh Hà Nam` ← còn chữ Hán

## Root cause
`parse_dila_district()` bóc admin suffix (省/市/縣/區) và tra CHINESE_PLACE_NAMES. Nếu không có thì dùng `name_raw` thô (vẫn là chữ Hán).

## Fix
1. Thêm `HAN_VIET_CHAR` dict (ban đầu ~600 ký tự, sau 8 pass → ~1200 ký tự)
2. Thêm `_han_viet(name_raw)` — transliterate ký tự → âm Hán-Việt (fallback)
3. `parse_dila_district` dùng `_han_viet()` thay vì trả thô
4. Thêm `_SKIP_SEGMENTS` = {市轄, 縣轄, ...} — bỏ qua admin wrapper terms
5. Fix bug `found = True` khi skip segment
6. Handle chuỗi multi-district (dấu `;`)

## Kết quả
| Pass | Còn chữ Hán | % |
|------|-------------|---|
| Ban đầu | 58,586/58,586 | 100% |
| Pass 1–6 | 13,265 | 22.6% |
| Pass 7 | 254 | 0.4% |
| Pass 8 (final) | **4** | **0.007%** |

4 place còn lại là edge case: Cambodia/Philippines với format hỗn hợp (parentheses lồng nhau + tiếng Anh). Không fix, chấp nhận.

## Test xác nhận
- `PL023898` (王寺/Vương Tự): `huyện Nam Lạc, thành phố Bộc Dương, tỉnh Hà Nam` ✓
- `無極縣` place: `huyện Vô Cực, thành phố Thạch Gia Trang, tỉnh Hà Bắc` ✓
- `北京市-西城區`: `quận Tây Thành, thành phố Bắc Kinh` ✓

## Files changed
- `daoanh/app.py`: thêm ~160 dòng vào `HAN_VIET_CHAR` dict

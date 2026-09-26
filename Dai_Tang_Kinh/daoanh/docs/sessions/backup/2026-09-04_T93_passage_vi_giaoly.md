# Phiên 2026-09-04 — T93: Passage → Tiếng Việt + Tab GIÁO LÝ Fix

**Task:** T93
**Status:** ✅ DONE
**Thời gian:** ~20 phút

---

## Yêu cầu từ Admin

1. Thay "Passage" bằng tiếng Việt trong thông báo user-facing (user là tăng ni Phật tử, không có nền tảng Anh văn)
2. Fix Tab GIÁO LÝ theo Phương án A (lightweight fix — provenance labels + empty states)

---

## Kết quả

### Part A — Passage → Tiếng Việt (5 edits)

| File | Vị trí | Trước | Sau |
|---|---|---|---|
| `places.html:2002` | Empty state | `⚠ Chưa có passage data · Task T02` | `⚠ Chưa có dữ liệu kinh điển` |
| `places.html:2065` | Reader meta | `Passage→text→loc_ref` | `Kinh điển → bản văn → vị trí` |
| `places.html:2829` | Confirm | `Dịch lại passage này bằng AI?` | `Dịch lại đoạn kinh này bằng Trí Tuệ Nhân Tạo?` |
| `places.html:3916` | Found | `Đã tìm thấy passage` | `Đã tìm thấy đoạn kinh` |
| `app.py:4196` | Error | `Passage không có nội dung Hán văn` | `Đoạn kinh không có nội dung Hán văn` |

### Part B — Tab GIÁO LÝ Fix (10 edits)

**Backend labels:**
- `han`: Thêm `badge_label = 'Hán Tạng — Local'` + note "Dữ liệu đã import từ CBETA"
- `tang`: `'Tạng Truyền (84000)'` → `'Tạng Truyền — 84000.co'` + note confidence
- `sat`: `'SAT Daizōkyō'` → `'SAT — Đại học Tokyo'`
- `parallels`: `'DharmaNexus'` → `'Phân tích liên văn bản — DharmaNexus'` + note "không phải bản dịch"
- `pali`: `'Pali (SuttaCentral)'` → `'Pali tham chiếu — SuttaCentral'`

**Frontend labels:**
- `LABEL` object: `Hán Tạng` / `Pali Tham Chiếu` / `SAT Đại Học` / `Liên Văn Bản`
- `ICON` object: `parallels: '🌐'` → `'🔗'`
- Empty state: `"Địa danh này chưa có kinh điển Pali tham chiếu trực tiếp"`

---

## Verify

- [x] `py_compile app.py` — PASS
- [x] JS syntax — 7 edits, 0 syntax error
- [x] User-facing strings — đã thay hết, `passage_id` giữ nguyên (technical)
- [ ] `npm run pipeline` — chờ test

---

## Files modified

- `places.html` — 7 edits
- `app.py` — 5 edits
- Total: 12 edits, 0 DB migration, 0 API mới

## Rollback

```bash
git revert HEAD
```

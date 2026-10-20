# T93 — Passage → Tiếng Việt + Tab GIÁO LÝ Fix

**Ngày tạo:** 2026-09-04
**Status:** ✅ DONE
**Loại:** UI/UX fix (additive, không DB migration)
**Rollback:** `git revert` — tất cả code changes trong 1 commit

---

## Mục tiêu

1. **Phần A:** Thay thuật ngữ "Passage" bằng tiếng Việt trong các thông báo user-facing — vì user là tăng ni Phật tử, không có nền tảng Anh văn
2. **Phần B:** Fix Tab GIÁO LÝ — sửa provenance labels cho 5 truyền thống + thêm empty state hữu ích

---

## Phần A — Passage → Tiếng Việt

### Những gì đổi

| File | Vị trí | Trước | Sau |
|---|---|---|---|
| `places.html:2002` | Tab Đại Tạng empty | `⚠ Chưa có passage data · Task T02` | `⚠ Chưa có dữ liệu kinh điển` |
| `places.html:2065` | Reader meta | `Chuỗi chứng cứ: Passage→text→loc_ref(trang/cột)` | `Chuỗi chứng cứ: Kinh điển → bản văn → vị trí (trang/cột)` |
| `places.html:2829` | Confirm dialog | `Dịch lại passage này bằng AI?` | `Dịch lại đoạn kinh này bằng Trí Tuệ Nhân Tạo?` |
| `places.html:3916` | Lineage ref found | `Đã tìm thấy passage` | `Đã tìm thấy đoạn kinh` |
| `app.py:4196` | API error | `Passage không có nội dung Hán văn` | `Đoạn kinh không có nội dung Hán văn` |

### Những gì KHÔNG đổi

- `passage_id` — technical identifier, chỉ hiển thị trong admin/debug mode
- `passages` — JSON key trong API response (technical)
- `passage_entity` — database table name
- Admin pages (`admin/test_entity.html`) — cho dev, không phải user

---

## Phần B — Tab GIÁO LÝ Fix

### B1. Provenance labels (backend `app.py`)

| Tradition | Trước | Sau | Note mới |
|---|---|---|---|
| `han` | _(không có badge_label)_ | `Hán Tạng — Local` | `Dữ liệu đã import từ CBETA database` |
| `tang` | `Tạng Truyền (84000)` | `Tạng Truyền — 84000.co` | `Cross-ref từ toh_cbeta_crossref (T38). Confidence: 0.99` |
| `sat` | `SAT Daizōkyō` | `SAT — Đại học Tokyo` | `Phiên bản Unicode JIS` |
| `parallels` | `DharmaNexus (text-reuse)` | `Phân tích liên văn bản — DharmaNexus` | `Kết quả phân tích, không phải bản dịch hay parallel text. Nguồn: dharmamitra.org` |
| `pali` | `Pali (SuttaCentral)` | `Pali tham chiếu — SuttaCentral` | Giữ nguyên note cũ |

### B2. Frontend labels (`places.html`)

```javascript
// Trước:
var LABEL = { han:'漢 Hán Tạng', pali:'Pali', tang:'藏 Tạng Truyền', sat:'SAT', parallels:'DharmaNexus' };
var ICON  = { han:'📜', pali:'🪷', tang:'🎐', sat:'🔖', parallels:'🌐' };

// Sau:
var LABEL = { han:'汉 Hán Tạng', pali:'Pali Tham Chiếu', tang:'藏 Tạng Truyền', sat:'SAT Đại Học', parallels:'Liên Văn Bản' };
var ICON  = { han:'📜', pali:'🪷', tang:'🎐', sat:'🔖', parallels:'🔗' };
```

### B3. Empty state cho Pali suggestions

Khi địa danh không có kinh điển Pali tham chiếu:
```
"Địa danh này chưa có kinh điển Pali tham chiếu trực tiếp. Nhập mã CBETA để xem đối chiếu."
```

Thay vì để trống (như trước đây).

---

## Data Reality

- `_PALI_REF_MAP` chỉ 6 entries (0251/0235/0262/0209/0222/0221) — majority empty
- `pali_place_ref` chỉ 15 địa danh Ấn Độ cổ — Thiếu Lâm Tự không có trong đó
- Tab GIÁO LÝ hiện chỉ hoạt động khi user nhập mã CBETA thủ công
- **Không có "dị bản" (variant), không có "text-reuse labels", không có scores** — audit.confirm

---

## Verify

- [x] `py_compile app.py` — PASS
- [x] JS syntax places.html — PASS (5 edits, 0 syntax error)
- [x] grep "Passage" places.html — còn `passage_id` (technical), user-facing đã đổi
- [ ] `npm run pipeline` — cần test khi server available

---

## Files modified

- `Dai_Tang_Kinh/daoanh/places.html` — 7 edits (Part A: 4 + Part B: 3)
- `Dai_Tang_Kinh/daoanh/app.py` — 5 edits (Part A: 1 + Part B: 4)

---

## Rollback

```bash
git revert HEAD  # revert tất cả changes trong 1 commit
```

Không có DB migration → rollback hoàn toàn an toàn.

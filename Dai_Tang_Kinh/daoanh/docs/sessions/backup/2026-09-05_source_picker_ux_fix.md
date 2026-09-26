# Session 2026-09-05 — Source Picker UX Fix (Nguyên Văn tab)

**Task:** Thuộc T94 Phase 2 UI  
**File:** `daoanh/places.html`  
**Scope:** CSS + JS — không đổi DB, không đổi API

---

## Vấn đề

Tab "Nguyên Văn" trong DaiTang reader hiển thị 15 CBETA references dính liền
trên một hàng ngang overflow — không click được trên mobile, không đọc được trên desktop.

---

## Thay đổi

### CSS (thay thế flex-row → grid)

| Before | After |
|--------|-------|
| `.dt-passage-chips { display:flex; overflow-x:auto }` | `.dt-src-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)) }` |
| `.dt-pchip { white-space:nowrap; flex-shrink:0 }` | `.dt-pchip { min-height:44px; display:flex; align-items:center }` |

Thêm mới:
- `.dt-pchip__work` — text_id nhỏ (9px, opacity 0.65)
- `.dt-pchip__page` — loc_ref lớn (12px, bold)
- `.dt-pchip__sep` — dấu `·` phân cách
- `.dt-pchip__vi` — dot vàng cho passages có bản dịch
- `.dt-src-groups` + `.dt-src-grp-btn` — grouping cho >20 refs
- Responsive: 2 cols ở ≤639px, 1 col ở ≤359px

### JS — `dtRenderPChips(active)` (rewrite)

- Format hiển thị: `T50n2060 · 0457a` (work + sep + page)
- `dtNormLoc('0-0457a-')` → `'0457a'` — strip prefix/suffix
- Malformed anchor → "Chưa xác định" + title tooltip
- `aria-current="true"` trên chip active
- `aria-label` cho screen reader
- Grouping + `dtSrcFilter(workId)` khi >20 refs

---

## Verify

- `node` brace balance check: 1145 open = 1145 close ✅
- Browser test (JavaScript API): `chips=15, has_grid=true, min-height=44px` ✅
- Format chip 0: `work=T50n2060, page=0457a, has_sep=true, has_vi_dot=true` ✅
- `aria-current="true"` trên chip active ✅
- `gridTemplateColumns: 172px 172px 172px` (auto-fit) ✅

---

## Rollback

```bash
git revert HEAD
```

---

## Tiếp theo

T96 — Per-segment translation system (xem `tasks/T96-per-segment-translation.md`).

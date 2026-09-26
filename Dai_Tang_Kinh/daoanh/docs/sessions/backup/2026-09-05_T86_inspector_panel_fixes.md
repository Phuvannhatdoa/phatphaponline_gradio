# Session: Inspector Panel Fixes — Dynasty, Origin Place, Conflict Display

**Ngày:** 2026-09-05  
**Task:** T86 — CHI TIẾT TĂNG NHÂN panel fixes  
**Test case chính:** A015811 (慈舟方念 / 大覺方念)

---

## Vấn đề

3 bugs trong `_renderLineageInspector()` (`places.html`):

| # | Bug | Biểu hiện |
|---|-----|-----------|
| 1 | Dynasty raw | `明` thay vì `Nhà Minh (明)` |
| 2 | Origin place `name_vi=null` | Raw `銀城防` thay vì `Ngân Thành Phòng` + link `href="#"` broken |
| 3 | Conflict label sai | `⚠ 2 mâu thuẫn nguồn (DILA vs Marcus)` không giải thích gì |

---

## Root cause audit (A015811)

- **Dynasty**: `_renderLineageInspector` render trực tiếp `n.dynasty` mà không qua mapping
- **Origin place**: `_t86_origin_place()` chỉ query `places` table — `places.name_vi` thường null. `namevi_map_places` có `'銀城防' → 'Ngân Thành Phòng'` nhưng không được query
- **Conflict**: `lineage_conflicts_v2` cho A015811 có `teacher_set: dila_data=["A005648"], marcus_data=["A015790"]` (no ID overlap) → backend đúng label `direction_disagreement` nhưng frontend hiển thị "DILA:1·Marcus:1" không có ngữ nghĩa

---

## Thay đổi

### `app.py` — `_t86_origin_place()` (lines 4867–4884 → expanded)

Sau khi query `places` table:
- Nếu `name_vi=None` và có `name_zh` → query `namevi_map_places WHERE name_zh=? ORDER BY confidence DESC LIMIT 1`
- Trả thêm `vi_confidence` + `vi_source` trong response JSON

### `places.html`

**Thêm `_fmtDynasty(raw)`** (sau `const _DYNASTY_VI`, line ~5083):
```js
function _fmtDynasty(raw) {
    if (!raw) return '';
    const vi = _DYNASTY_VI[raw];
    return vi ? 'Nhà ' + vi + ' (' + raw + ')' : raw;
}
```

**`_renderLineageInspector`** — 3 fixes:

1. Dynasty: `_escHtml(n.dynasty)` → `_escHtml(_fmtDynasty(n.dynasty))`

2. Origin place:
   - Hiển thị `name_vi` nếu có, fallback `name_zh`, fallback `place_id`
   - Badge `(phiên âm tự động)` khi `vi_source !== 'manual'` và `vi_confidence < 1.0`
   - Badge `(chưa có tên Việt hóa)` khi không có `name_vi`
   - Link `Xem bản đồ` dùng `javascript:void(0)` + `onclick` (không dùng `href="#"`)

3. Conflict section:
   - Heading: `Đối chiếu nguồn` (không phải `⚠ N mâu thuẫn nguồn`)
   - `direction_disagreement` → `Quan hệ [thầy/trò]: khác nguồn, chưa thể tự động đối chiếu`
   - `source_coverage_gap` dila=0 → `chỉ có Marcus ghi nhận`
   - `source_coverage_gap` marcus=0 → `chỉ có DILA ghi nhận`

---

## Verified (A015811)

Inspector `innerText` sau fix:
```
Triều đại: Nhà Minh (明)
Quê quán: Ngân Thành Phòng (phiên âm tự động) Xem bản đồ
Đối chiếu nguồn
  Quan hệ thầy: khác nguồn, chưa thể tự động đối chiếu
  Quan hệ trò: khác nguồn, chưa thể tự động đối chiếu
```

---

## Ràng buộc đã tuân thủ

- Không hard-code riêng `明` hay `銀城防` — dùng `_DYNASTY_VI` mapping và `namevi_map_places` table
- Không dùng LLM/API dịch
- Không gán tên Việt ZQ cho nguồn DILA — badge `(phiên âm tự động)` hiển thị rõ nguồn
- Không sửa schema DB

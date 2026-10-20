# Bilingual Reader — Implementation Notes

**Ngày hoàn thành:** 2026-09-04  
**File thay đổi:** `daoanh/places.html` (CSS + HTML + JS — không có backend changes)  
**Test URL:** http://localhost:8080/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255

---

## Kết quả verify thực tế (Thiếu Lâm Tự — PL000000023255)

| Test | Kết quả |
|------|---------|
| Tổng segments Hán | 54 |
| Tổng segments Việt | 54 |
| Hover Han→Vi: is-active + is-linked | ✓ PASS |
| Mouseout clear toàn bộ class | ✓ PASS |
| Hover Vi→Han reverse sync | ✓ PASS |
| Passage không có Vi → button "🤖 Dịch (AI)" | ✓ PASS |
| Badge "🤖 BẢN DỊCH AI NHÁP — CẦN HIỆU ĐÍNH" | ✓ PASS |
| Warning "⚠ Căn chỉnh đoạn tự động" | ✓ PASS |

---

## Các hàm đã thêm vào places.html

### `dtSegmentHan(rawText)` → `string[]`
- Strip `\n` CBETA scan-line breaks
- Split bằng regex `/[^。；！？]+[。；！？]/g`
- Group cho đến khi buf >= 50 ký tự
- Trả về mảng đoạn Hán văn

### `dtDistributeVi(viText, n)` → `string[]`
- Split Vi bằng `/[^.!?;。\n]+[.!?;。]?\s*/g`
- Distribute proportionally: `chunkTarget = viText.length / n`
- Trả về đúng `n` nhóm Vi

### `dtBuildSegments(p)` → `Segment[]`
- Gọi `dtSegmentHan` + `dtDistributeVi`
- Trả về `{id, order, source_text, target_text_vi, alignment_status}`
- `alignment_status`: `'auto_aligned'` hoặc `'translation_missing'`

### `dtMobileTab(which)` — toggle mobile view
- `which = 'han'`: show Han, hide Vi, hide resizer
- `which = 'vi'`: show Vi, hide Han, hide resizer
- Toggle `.active` trên `.dt-mtab` buttons

### `dtInitBilingualReader()` — one-time setup
- Gọi một lần cuối file (trước `</script>`)
- Attach `mouseover`/`mouseout`/`focusin`/`focusout` delegation trên `#dt-han-body` và `#dt-vi-body`
- Debounce: 90ms activate, 150ms clear
- Scroll: `scrollIntoView({behavior: smooth/auto, block: nearest})`
- `prefers-reduced-motion`: dùng `'auto'` thay `'smooth'`
- Chống scroll loop: sync bằng `segId`, không sync `scrollTop`
- Listeners không bị remove khi `innerHTML` thay đổi (event delegation trên container)

### `dtRenderPassage(idx)` — đã thay thế hoàn toàn
- Trước: render toàn bộ raw_text + vi_text như 1 block
- Sau: gọi `dtBuildSegments(p)` → render từng `<article class="dt-segment" data-seg="seg-NNN">`
- Han column: `.dt-seg-han` với Noto Serif TC / Kaiti SC
- Vi column: `.dt-seg-vi` + badge + alignment note + actions
- Passage không có Vi: `.dt-no-trans` + `.dt-translate-btn`

---

## CSS classes đã thêm

| Class | Mô tả |
|-------|-------|
| `.dt-segment` | Container đoạn (flex, border-left:3px transparent) |
| `.dt-segment.is-active` | Đoạn đang hover (background vàng nhạt, border-left gold) |
| `.dt-segment.is-linked` | Đoạn tương ứng bên kia (background vàng rất nhạt) |
| `.dt-seg-num` | Số đoạn (9px, mono, phải) |
| `.dt-seg-han` | Text Hán (Noto Serif TC, 15px, line-height 2.1) |
| `.dt-seg-vi` | Text Việt (13px, line-height 1.85) |
| `.dt-bilingual-badge` | Badge "AI NHÁP / THAM KHẢO" |
| `.dt-auto-align-note` | Warning căn chỉnh tự động (có tooltip) |
| `.dt-mobile-tabs` | Mobile tab bar (ẩn trên desktop) |
| `.dt-mtab` | Button mobile tab |

---

## HTML thêm

Mobile tab bar giữa `#dt-pchips` và `#dt-split`:
```html
<div class="dt-mobile-tabs" id="dt-mobile-tabs">
  <button class="dt-mtab active" onclick="dtMobileTab('han')">漢 Hán Văn</button>
  <button class="dt-mtab" onclick="dtMobileTab('vi')">VI Việt Dịch</button>
</div>
```

---

## Giới hạn đã ghi nhận

- **Auto-alignment không học thuật**: Vi text phân phối theo tỉ lệ char count, không đảm bảo câu-câu tương ứng
- **Không có segment-level DB**: alignment_status luôn `auto_aligned` trong MVP
- **CBETA scan-line `\n` bị strip**: mất reference dòng nhưng đúng về ngữ nghĩa  
- **Chưa có virtual scroll**: 54 segments/passage vẫn render toàn bộ DOM

---

## Next steps (deferred)

- Verified alignment table trong DB (khi có editor review)
- Keyboard navigation: Arrow Up/Down giữa segments
- Export đoạn đã chọn (copy Hán+Việt cặp đôi)

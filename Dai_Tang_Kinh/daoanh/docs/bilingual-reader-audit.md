# Audit: Bilingual Reader — Tab Nguyên Văn

**Ngày:** 2026-09-04  
**Entity test:** Thiếu Lâm Tự (PL000000023255)  
**URL:** http://localhost:8080/daoanh/places.html?fly=34.5885,112.9343&select=PL000000023255

---

## 1. File liên quan

| File | Vai trò |
|------|---------|
| `daoanh/places.html` | File duy nhất chứa toàn bộ HTML/CSS/JS của tab Nguyên Văn |
| `daoanh/app.py` route `/daoanh/api/entity/<id>/canon` | Trả passage data (Layer B) |
| `daoanh/data/lineage.db` bảng `passage` | Lưu `raw_text` (Hán), `vi_text` (Việt), `translation_draft` |

Không có file JS/CSS riêng — mọi thứ inline trong `places.html`.

---

## 2. Cấu trúc HTML hiện tại (tab Nguyên Văn)

```
#dt-tab-fulltext
  .dt-passage-chips #dt-pchips        ← navigation chips (1 chip/passage file)
  .dt-split
    .dt-pane #dt-pane-han (flex:0 0 30%)
      .dt-pane-hd                      ← header sticky
      .dt-pane-body                    ← scroll container (overflow-y:auto)
        #dt-han-body                   ← nội dung Hán (innerHTML replaced per passage)
    .dt-resizer                        ← drag resizer
    .dt-pane #dt-pane-vi (flex:1)
      .dt-pane-hd
      .dt-pane-body                    ← scroll container
        #dt-vi-body                    ← nội dung Việt (innerHTML replaced per passage)
```

---

## 3. Format dữ liệu hiện tại

### `raw_text` (Hán văn từ CBETA)
- **Loại:** Plain text, không có XML/HTML markup
- **Đặc điểm:** `\n` mỗi ~18-20 ký tự — đây là scan-line break của CBETA, KHÔNG phải ngắt đoạn ngữ nghĩa
- **Ví dụ thực tế (passage 110, T51n2076):**
  ```
  衒之聞偈悲喜交并曰。願師久住世間化導\n群有。師曰。吾即逝矣不可久留。根性萬差多\n逢患難。...
  ```
- **Chiều dài:** ~666–1044 ký tự/passage
- **Dấu câu cổ văn:** `。` `；` `！` `？`

### `vi_text` (Bản dịch Việt từ Groq LLM)
- **Loại:** Một string liên tục dài
- **Không có** cấu trúc paragraph hay sentence boundary markup
- **Ví dụ thực tế (passage 110, T51n2076):**
  ```
  Tuần Chi nghe kệ xong, vừa buồn vừa vui, thưa rằng: "Nguyện thầy trụ thế lâu dài để hóa độ chúng sinh." Sư đáp: "Ta sắp đi rồi, không thể lưu lại lâu...
  ```
- **Chiều dài:** ~2,776–3,475 ký tự/passage
- **Flag:** `translation_draft = 1` (tất cả hiện tại là Groq LLM draft)

### ID và mapping
- **Không có** sentence-level ID hay alignment table trong DB
- `passage_id` là ID ở cấp passage file (cả đoạn CBETA lớn)
- `loc_ref` ví dụ `0-0220b-` là reference vị trí trong CBETA, không phải line number
- **Kết luận:** Mọi segment mapping đều phải là `auto_aligned` trong MVP

---

## 4. Hàm render hiện tại (trước khi sửa)

```js
function dtRenderPassage(idx) {
    // Renders raw_text as single pre-wrap block in dt-han-body
    // Renders vi_text as single block with badge in dt-vi-body
    // No segmentation, no hover sync
}
```

CSS hiện tại cho container:
- `.dt-pane-body`: `flex:1; overflow-y:auto; padding:14px`
- `.dt-split`: `flex:1; display:flex; overflow:hidden`
- **Hai pane body đã có scroll container riêng** — đây là điều kiện lý tưởng để sync cuộn.

---

## 5. Kế hoạch thay đổi

### A. Segmentation (pure JS, không đụng DB)
1. **Han segmentation** (`dtSegmentHan`):
   - Strip `\n` (CBETA scan-line breaks, không ngữ nghĩa)
   - Split bằng `。；！？`, giữ delimiter
   - Group ~2–3 câu thành 1 segment (~50–120 Hán tự/segment)

2. **Vi distribution** (`dtDistributeVi`):
   - Split Vi bằng dấu câu `.!?;`
   - Distribute proportionally theo số Han segments (by char length)
   - Status: `auto_aligned`

3. **Segment model** (`dtBuildSegments`):
   ```js
   { id: 'seg-001', order: 1, source_text: '...', target_text_vi: '...', alignment_status: 'auto_aligned' }
   ```

### B. UI thay đổi
- Replace `dtRenderPassage` body với segment-based render
- Mỗi segment: `<article class="dt-segment" data-seg="seg-001">`
- Badge bắt buộc: `🤖 BẢN DỊCH AI NHÁP — CẦN HIỆU ĐÍNH`
- Tooltip: `Việc chia đoạn và ghép Hán–Việt là hỗ trợ đọc; không phải bản đối chiếu học thuật`

### C. Hover/focus sync
- Event delegation trên `#dt-han-body` và `#dt-vi-body` (elements stable qua renders)
- `mouseover`/`mouseout` + debounce 90ms
- Scroll chỉ khi target segment nằm ngoài visible area của `.dt-pane-body`
- Chống scroll loop: chỉ sync theo `segment id`, không sync `scrollTop` liên tục
- `prefers-reduced-motion`: dùng `behavior:'auto'` thay `'smooth'`
- Listener attach một lần (`dtInitBilingualReader`), không gọi lại mỗi render

### D. Mobile
- `.dt-mobile-tabs` với 2 button: Hán văn / Việt dịch
- Ẩn trên desktop (CSS), hiện trên `max-width:600px`
- Mặc định show Hán, ẩn Việt; user tap để chuyển

---

## 6. Giả định và giới hạn

| Giới hạn | Chi tiết |
|----------|---------|
| Auto-alignment không chính xác học thuật | Vi text được chia proportionally by char count — không guarantee câu-câu tương ứng |
| Không có sentence alignment DB | Cần schema mới nếu muốn verified alignment trong tương lai |
| CBETA scan-line `\n` | Strip hoàn toàn — đúng về mặt ngữ nghĩa nhưng mất reference vị trí dòng |
| Passage dài có thể có nhiều segment | Chưa có virtual scroll (MVP); cần monitor performance với passage ~1000 chars |
| Dịch lại (Retranslate) sẽ mất segment mapping | Vì vi_text được thay thế → rebuild segments tự động |

---

## 7. File sẽ sửa

- `daoanh/places.html` — CSS + HTML + JS
- `daoanh/docs/bilingual-reader-implementation.md` — tài liệu kết quả (tạo sau khi xong)

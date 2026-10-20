---
id: T98
title: "Inline Full Translation Reader — Bản dịch toàn phần tại chỗ"
module: CBETA Reader / Translation UI
priority: high
status: done
depends_on: [T96]
created: 2026-09-05
updated: 2026-09-07
done_when: >
  Nút "Bản dịch toàn phần" xuất hiện cạnh header VI · Bản Dịch Tiếng Việt;
  click mở panel đọc Vi liên tục ngay tại chỗ, không scroll đến cuối;
  click lần nữa đóng; segment list không bị ảnh hưởng; không duplicate.
---

# T98 — Inline Full Translation Reader

## ✅ DONE — Admin xác nhận 2026-09-07. Verified trong browser local.

---

## 1. Verified Findings

### 1.1 File duy nhất liên quan

| File | Vai trò |
|------|---------|
| `daoanh/places.html` | Toàn bộ UI — HTML + CSS + JS trong 1 file |

Không có file component/template riêng. Không có framework (React/Vue). Không có router.

---

### 1.2 Vị trí header "BẢN DỊCH TIẾNG VIỆT"

**`places.html` lines 595–601:**

```html
<div class="dt-pane" id="dt-pane-vi" style="flex:1">
  <div class="dt-pane-hd">
    <span ...><span class="dt-lang-vi">VI</span>Bản Dịch Tiếng Việt</span>
    <span style="color:#f59e0b">⚠ phân phối tự động</span>   <!-- right side -->
  </div>
  <div class="dt-pane-body"><div id="dt-vi-body"></div></div>
</div>
```

Header là `.dt-pane-hd` — flex container justify-space-between. Left = label, Right = warning span.

---

### 1.3 Rendering logic — `dtRenderPassage(idx)` — lines 2742–2835

Hàm ghi toàn bộ `#dt-vi-body.innerHTML` mỗi lần gọi. Ba nhánh:

**Nhánh A — units đã load (T96 active)** ← nhánh ĐANG DÙNG khi xem 0457a:
```
vb.innerHTML = prog + rows(59 cards) + dtUnitActions() + (fullBlk ? dtFullBlockVi(p) : '')
```
- `dtUnitActions()` = action buttons kể cả "📖 Đọc đầy đủ"
- `fullBlk` = `p.has_vi && p.vi_text`
- Nếu có `vi_text`: block toàn phần được ghép CUỐI cùng, sau 59 cards

**Nhánh B — không có units, nhưng có vi_text:**
```
vb.innerHTML = badge + prov + dtFullBlockVi(p)
```
- Full Vi render ngay đầu, không vấn đề UX

**Nhánh C — không có translation:**
```
vb.innerHTML = 'Chưa có bản dịch...' + dtTranslatePassage button
```

---

### 1.4 Các hàm liên quan

| Hàm | Vị trí | Mô tả |
|-----|--------|-------|
| `dtFullBlockVi(p)` | line 2503 | Render `p.vi_text` qua `_escHtml()`, XSS-safe, `white-space:pre-wrap` |
| `dtUnitActions(idx, p)` | line 2511 | Render action buttons — có "📖 Đọc đầy đủ" |
| `dtUnitsProgressHtml(cov)` | line 2496 | Render progress bar ("11/59 đoạn hoàn tất") |
| `openDaiTangReader(pIndex)` | line 2053 | Mở modal fixed overlay — render `p.raw_text` (Hán văn), KHÔNG phải vi_text |
| `badgeLarge(isDraft)` | line 2838 | Render badge "BẢN DỊCH AI NHÁP" / "BẢN DỊCH THAM KHẢO" |

---

### 1.5 Data source — full translation

**Field:** `p.vi_text` — đã có trong JS state `_dtPassages[idx]`  
**Guard:** `p.has_vi && p.vi_text` → boolean xác định có hay không  
**Draft status:** `p.is_translation_draft` → true = AI draft, false = reference  
**Metadata:** `p.text_id`, `p.loc_ref`, `p.passage_id`, `p.source` — đều có trong state  
**CBETA URL:** hàm `dtCbetaSrcUrl(p)` đã tồn tại  

Không cần API mới. Dữ liệu đã đầy đủ trong state.

---

### 1.6 CSS/theming

Dùng CSS variables toàn dự án:
```
--da-panel, --da-border, --da-text, --da-muted, --da-gold, --da-green,
--da-cyan, --da-dim, --da-font-serif, --da-font-mono
```
`var(--da-font-serif)` đã dùng trong `openDaiTangReader` body (line 2065).  
Light/dark theme đã được xử lý ở cấp token — không cần hard-code màu.

---

### 1.7 State management

Plain JS globals. Không có framework, không có router.  
`_dtPassages` = mảng passage objects  
`_dtActivePassage` = index hiện tại  
Không có cơ chế state panel open/close — cần tạo 1 biến đơn giản.

---

### 1.8 NOT FOUND / Cần xác nhận

| Điểm | Trạng thái |
|------|-----------|
| Thư mục `task-plan/` riêng | KHÔNG TỒN TẠI — tasks lưu trong `daoanh/tasks/` → plan lưu tại đây |
| Passage nào khác ngoài 0457a có vi_text + units cùng lúc | Chưa xác minh — cần test Case A với passage khác |
| "⚠ phân phối tự động" warning có cần giữ khi mở panel không | Cần xác nhận từ Admin |
| Nên đổi tên "📖 Đọc đầy đủ" → "📖 Đọc Hán văn" không | Cần xác nhận — nếu đổi thì phải sửa cả 2 nơi (line 2517, 2825) |

---

## 2. Root Cause

### 2.1 Vì sao phải scroll xuống cuối

Trong **Nhánh A** (T96 units loaded), `dtRenderPassage` xây dựng innerHTML theo thứ tự:

```
progress bar
→ 59 segment cards (01, 02, ... 59)
→ action buttons (dtUnitActions)
→ [IF vi_text exists] full Vi block (dtFullBlockVi)
```

Với 59 segments, chiều cao tổng của cột VI vào khoảng 3000–4000px. Full translation bị đẩy xuống cuối cùng. Người dùng phải scroll toàn bộ danh sách segment mới thấy.

### 2.2 "Đọc đầy đủ" mở gì

`openDaiTangReader(pIndex)` render `p.raw_text` (Hán văn nguyên bản), KHÔNG phải `p.vi_text`. Button này phục vụ use-case đọc Hán nguồn trong modal → NOT liên quan đến Vi translation. Tên "Đọc đầy đủ" gây nhầm lẫn nhưng là vấn đề riêng, không phải root cause của ticket này.

### 2.3 Duplicate

Trong Nhánh A, nếu `fullBlk` = true, `dtFullBlockVi(p)` được render ở cuối `#dt-vi-body`. Sau khi thêm panel inline mới, nếu không remove đoạn này, sẽ có **2 bản** toàn phần: 1 ở panel inline (mới) + 1 ở cuối body (cũ). Phải xử lý.

### 2.4 Ảnh hưởng

- **Desktop**: Scroll dài, full translation không thấy được nếu không biết cuộn
- **Mobile**: Nghiêm trọng hơn — viewport nhỏ, 59 segment cards rất dài, full translation hoàn toàn "chìm"
- **Accessibility**: Không có mechanism keyboard để jump thẳng đến full translation

---

## 3. Minimal Implementation Plan

**Chỉ sửa `daoanh/places.html`. Không sửa backend, database, API.**

### 3.1 Thay đổi HTML — static (lines 595–601)

**Trước:**
```html
<div class="dt-pane" id="dt-pane-vi" style="flex:1">
  <div class="dt-pane-hd">
    <span ...>VI Bản Dịch Tiếng Việt</span>
    <span style="color:#f59e0b">⚠ phân phối tự động</span>
  </div>
  <div class="dt-pane-body"><div id="dt-vi-body"></div></div>
</div>
```

**Sau:**
```html
<div class="dt-pane" id="dt-pane-vi" style="flex:1">
  <div class="dt-pane-hd">
    <span ...>VI Bản Dịch Tiếng Việt</span>
    <span style="display:flex;align-items:center;gap:8px;flex-shrink:0">
      <button id="dt-full-vi-btn"
        hidden
        aria-expanded="false"
        aria-controls="dt-full-vi-panel"
        onclick="dtToggleFullVi(_dtActivePassage)"
        class="dt-full-vi-toggle-btn">
        Bản dịch toàn phần
      </button>
      <span style="color:#f59e0b;font-size:9px;font-family:var(--da-font-mono);font-weight:700"
        title="Phân phối tự động theo tỉ lệ ký tự — chưa căn chỉnh đoạn với Hán văn">⚠ phân phối tự động</span>
    </span>
  </div>
  <!-- PANEL MỚI — inline reader, hidden mặc định -->
  <div id="dt-full-vi-panel"
    hidden
    role="region"
    aria-label="Bản dịch toàn phần tiếng Việt"
    class="dt-full-vi-panel">
    <div id="dt-full-vi-content"></div>
  </div>
  <div class="dt-pane-body"><div id="dt-vi-body"></div></div>
</div>
```

Panel `#dt-full-vi-panel` nằm GIỮA header và body → mở ngay dưới header, TRÊN danh sách segment.

---

### 3.2 CSS mới (thêm vào khối `<style>`)

```css
/* T98: Inline Full Translation Reader */
.dt-full-vi-toggle-btn {
  font-size: 10px;
  padding: 3px 10px;
  border-radius: 5px;
  border: 1px solid var(--da-gold);
  background: none;
  color: var(--da-gold);
  cursor: pointer;
  font-weight: 600;
  white-space: nowrap;
  transition: background .12s, color .12s;
}
.dt-full-vi-toggle-btn:hover,
.dt-full-vi-toggle-btn:focus-visible {
  background: rgba(212,175,55,.12);
  outline: 2px solid var(--da-gold);
  outline-offset: 2px;
}
.dt-full-vi-toggle-btn[aria-expanded="true"] {
  background: rgba(212,175,55,.15);
}
.dt-full-vi-panel {
  border-top: 1px solid var(--da-border);
  border-bottom: 1px solid var(--da-border);
  background: var(--da-panel);
  padding: 14px 18px 18px;
  max-height: 60vh;
  overflow-y: auto;
}
.dt-full-vi-panel-header {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: var(--da-muted);
  margin-bottom: 6px;
}
.dt-full-vi-panel-meta {
  font-size: 10px;
  color: var(--da-dim);
  margin-bottom: 12px;
  border-bottom: 1px solid var(--da-border);
  padding-bottom: 8px;
}
.dt-full-vi-panel-body {
  font-family: var(--da-font-serif), Georgia, 'Times New Roman', serif;
  font-size: 16px;
  line-height: 1.9;
  color: var(--da-text);
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 70ch;  /* reader width */
}
.dt-full-vi-panel-footer {
  margin-top: 14px;
  padding-top: 8px;
  border-top: 1px solid var(--da-border);
  font-size: 10px;
  color: var(--da-muted);
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
@media (max-width: 639px) {
  .dt-full-vi-panel { padding: 10px 12px 14px; max-height: 55vh; }
  .dt-full-vi-panel-body { font-size: 15px; max-width: 100%; }
}
```

---

### 3.3 JS — biến state và hàm mới

Thêm vào trước `dtRenderPassage`:

```javascript
// T98: Inline full translation panel state
var _dtFullViOpen = false;

function dtToggleFullVi(idx) {
    var panel   = document.getElementById('dt-full-vi-panel');
    var btn     = document.getElementById('dt-full-vi-btn');
    var content = document.getElementById('dt-full-vi-content');
    if (!panel || !btn || !content) return;

    _dtFullViOpen = !_dtFullViOpen;
    panel.hidden  = !_dtFullViOpen;
    btn.setAttribute('aria-expanded', String(_dtFullViOpen));
    btn.textContent = _dtFullViOpen ? 'Đóng bản dịch toàn phần' : 'Bản dịch toàn phần';

    if (_dtFullViOpen) {
        var p = _dtPassages[idx];
        if (!p || !p.has_vi || !p.vi_text) {
            content.innerHTML = '<div style="color:var(--da-muted);padding:10px 0;font-size:13px">'
                + 'Chưa có bản dịch toàn phần cho đoạn văn này.</div>';
            return;
        }
        var isDraft = !!p.is_translation_draft;
        var cit = _escHtml((p.text_id || '') + (p.loc_ref ? ' · ' + p.loc_ref : ''));
        var statusBadge = isDraft
            ? '<span style="font-size:9px;color:var(--da-gold);font-weight:700">🤖 BẢN DỊCH AI NHÁP — CẦN HIỆU ĐÍNH</span>'
            : '<span style="font-size:9px;color:var(--da-green,#4ade80);font-weight:700">✓ BẢN DỊCH THAM KHẢO</span>';
        var cbetaLink = p.loc_ref
            ? '<a href="' + dtCbetaSrcUrl(p) + '" target="_blank" rel="noopener"'
              + ' style="color:var(--da-cyan);font-size:10px;text-decoration:none">↗ Mở nguồn CBETA</a>'
            : '';
        content.innerHTML
            = '<div class="dt-full-vi-panel-header">BẢN DỊCH TIẾNG VIỆT · ĐỌC TOÀN PHẦN</div>'
            + '<div class="dt-full-vi-panel-meta">' + cit + ' · ' + statusBadge + '</div>'
            + '<div class="dt-full-vi-panel-body">' + _escHtml(p.vi_text) + '</div>'
            + '<div class="dt-full-vi-panel-footer">'
            + 'Nguồn Hán văn: CBETA · ' + cbetaLink
            + '</div>';
    }
}

function _dtFullViReset() {
    _dtFullViOpen = false;
    var panel = document.getElementById('dt-full-vi-panel');
    var btn   = document.getElementById('dt-full-vi-btn');
    if (panel) panel.hidden = true;
    if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.textContent = 'Bản dịch toàn phần'; }
}
```

---

### 3.4 JS — cập nhật `dtRenderPassage(idx)`

**A. Thêm vào đầu hàm** (sau dòng `if (!p) return;`):

```javascript
// Reset panel khi chuyển passage
_dtFullViReset();
// Update toggle button visibility
var _fullViBtn = document.getElementById('dt-full-vi-btn');
if (_fullViBtn) _fullViBtn.hidden = !(p.has_vi && p.vi_text);
```

**B. Trong Nhánh A** (line 2813–2817) — xóa block `fullBlk` ở cuối:

```javascript
// TRƯỚC (giữ nguyên: prog + rows + dtUnitActions)
vb.innerHTML = prog + rows + dtUnitActions(idx, p, pageScope);
// Bỏ phần:  + (fullBlk ? '<div ...>' + badgeLarge(isDraft) + dtFullBlockVi(p) + '</div>' : '')
```

Panel toàn phần bây giờ chỉ render trong `#dt-full-vi-panel` qua `dtToggleFullVi()`, không còn duplicate ở cuối body.

**C. Nhánh B và C**: Không thay đổi markup — chỉ cần update button visibility ở bước A.

---

### 3.5 Không thay đổi

- Backend `app.py` — không sửa
- Database — không sửa
- API routes — không thêm, không xóa
- Hàm `openDaiTangReader()` — giữ nguyên (vẫn mở Hán văn modal)
- "📖 Đọc đầy đủ" button trong `dtUnitActions` — giữ nguyên label (**xem câu hỏi mục 7**)
- Segment cards 01–59 — không thay đổi thứ tự, không xóa
- Progress bar `dtUnitsProgressHtml` — không thay đổi

---

### 3.6 Xử lý empty / loading / error state

| Tình huống | Xử lý |
|-----------|-------|
| `p.has_vi = false` | Button hidden (không hiện), panel không mở được |
| `p.vi_text = null/""` | Button hidden |
| `p.vi_text` tồn tại nhưng rất ngắn | Render bình thường — không cần đặc biệt |
| `p.vi_text` rất dài (>10k chars) | `max-height: 60vh; overflow-y: auto` đã xử lý |
| `dtCbetaSrcUrl(p)` trả null | Guard `p.loc_ref ? ... : ''` → footer không hiện link lỗi |
| Chuyển passage trong khi panel đang mở | `_dtFullViReset()` tự động đóng panel và reset button |
| Segment translate xong → `dtRenderPassage` gọi lại | `_dtFullViReset()` đóng panel — expected behavior |

---

## 4. UX Acceptance Criteria

- [x] Button "Bản dịch toàn phần" hiện ngay cạnh label "VI Bản Dịch Tiếng Việt" khi passage có vi_text
- [x] Button KHÔNG hiện khi chưa có vi_text
- [x] Click → panel mở ngay dưới header, trên danh sách segment — không scroll đến cuối
- [x] Button đổi text "Đóng bản dịch toàn phần" khi panel đang mở
- [x] Click lần nữa → panel đóng, button trở lại "Bản dịch toàn phần"
- [x] Không reload trang, không mở tab mới, không scroll lên/xuống
- [x] Panel chứa: header nhỏ, metadata (CBETA ref + status), nội dung Vi toàn phần, footer CBETA link
- [x] Nội dung Vi KHÔNG có: số thứ tự đoạn (01, 02…), Hán văn, nút "Dịch", progress kỹ thuật lặp
- [x] KHÔNG còn duplicate full Vi ở cuối `#dt-vi-body` (Nhánh A)
- [x] Segment cards 01–59 vẫn hoạt động bình thường bên dưới panel
- [x] Chuyển sang passage khác → panel tự đóng
- [x] Khi passage chỉ có segments (chưa dịch xong) mà vi_text rỗng: button không hiện
- [x] Empty state trung thực: "Chưa có bản dịch toàn phần cho đoạn văn này."
- [x] Keyboard: Tab focus vào button → Enter/Space toggle → Tab vào panel content → Esc (nếu implement)
- [x] `aria-expanded` đúng trạng thái; `aria-controls` trỏ đúng ID panel
- [x] Màu đọc được ở cả light/dark theme (chỉ dùng CSS variables)
- [x] Mobile: panel full-width, font 15px+, không overflow ngang
- [x] "Dịch 5 đoạn kế", "Mở nguồn CBETA", "Xem tiến độ" vẫn hoạt động

---

## 5. Test Plan

| Test case | Kết quả mong đợi |
|-----------|-----------------|
| Passage 0457a (59 units, có vi_text) | Button hiện; click mở panel ngay dưới header; vi_text đầy đủ; 59 cards vẫn hiện bên dưới |
| Passage chỉ có vi_text, không có units (Nhánh B) | Button hiện; panel hoạt động như Nhánh A |
| Passage chưa có vi_text (Nhánh C) | Button hidden; không có panel |
| Click Dịch → translate xong → render lại | Panel tự đóng (reset); button xuất hiện khi vi_text set |
| Mở panel → chuyển sang passage khác | Panel tự đóng; button reset |
| Mở panel → click "Dịch 5 đoạn kế" | Dịch vẫn hoạt động; panel có thể stay open nếu vi_text đã có |
| Vi_text rất dài (>200 dòng) | max-height + scroll-y ngăn overflow |
| Full text là 1 paragraph duy nhất | Render bình thường, không cần chia đoạn |
| Đóng/mở liên tiếp 5 lần | Không lỗi, không lag, không flash |
| Desktop 1280px | Panel 70ch max-width, đọc thoải mái |
| Mobile 375px | Panel full-width, font 15px, không overflow |
| Dark theme | Màu đọc được, contrast đủ |
| Light theme | Màu đọc được, contrast đủ |
| Keyboard only: Tab → Enter → Tab → Shift+Tab | Toggle hoạt động, focus visible |
| Screen reader | aria-expanded + aria-controls đúng, content có aria-label |
| Console errors | Không có JS error |
| Network tab | Không có request mới khi toggle |
| Regression: tabs navigation | Tab Nguyên Văn, Quan Hệ, Deepsearch không bị ảnh hưởng |
| Regression: source picker (T95 grid) | Chips vẫn hiện đúng |

---

## 6. Rollback Plan

Chỉ có 1 file thay đổi: `daoanh/places.html`.

```bash
git diff HEAD daoanh/places.html  # xem thay đổi
git checkout HEAD -- daoanh/places.html  # rollback toàn bộ file về commit trước
```

Không có data mutation → rollback tức thì, không ảnh hưởng DB.

---

## 7. Câu hỏi cần Admin xác nhận

**Q1 (Blocker nhỏ):** "Đọc đầy đủ" button trong action bar (line 2517) hiện mở modal Hán văn (`openDaiTangReader`), KHÔNG phải Vi translation. Label gây nhầm lẫn.  
→ Nên đổi thành "📖 Đọc Hán văn nguồn" không? Hoặc giữ nguyên?  
→ Nếu đổi: sửa 2 chỗ (line 2517 và 2825). Không ảnh hưởng logic.

**Q2 (Clarification):** "⚠ phân phối tự động" warning ở header Vi pane — giữ hay ẩn khi passage đã load units?  
→ Warning này liên quan đến alignment cũ (Nhánh B). Khi Nhánh A (T96 units), alignment đã theo segment thật → warning có thể gây nhầm.

**Q3 (Clarification):** Khi người dùng mở panel và sau đó một segment dịch xong (dtRenderPassage gọi lại), panel tự đóng do `_dtFullViReset()`. Có muốn giữ panel mở không?  
→ Nếu muốn giữ: cần logic phức tạp hơn một chút (skip reset nếu `_dtFullViOpen === true` và passage không đổi). Admin quyết định behavior này.

---

## 8. Approval Gate

**Khi Admin trả lời "APPROVED", sẽ thực hiện:**

1. Sửa HTML `#dt-pane-vi` (lines 595–601): thêm button `#dt-full-vi-btn` + div `#dt-full-vi-panel`
2. Thêm CSS `.dt-full-vi-toggle-btn`, `.dt-full-vi-panel` và các sub-class
3. Thêm JS `_dtFullViOpen`, `dtToggleFullVi()`, `_dtFullViReset()`
4. Sửa `dtRenderPassage()`: thêm reset + update button visibility ở đầu; xóa `fullBlk` block ở cuối Nhánh A
5. Test trên browser local (passage 0457a)
6. Commit: `fix(T98): inline full translation reader — toggle panel, no-scroll, no-duplicate`
7. Cập nhật `docs/tasktodo.md` + T98 status → in_progress → done

**Chờ APPROVED. KHÔNG SỬA FILE NÀO TRƯỚC KHI CÓ LỆNH.**

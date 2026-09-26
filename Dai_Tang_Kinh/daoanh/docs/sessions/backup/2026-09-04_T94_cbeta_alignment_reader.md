# Session 2026-09-04 — T94: CBETA Bilingual Alignment Reader

**Task:** T94 — CBETA Bilingual Alignment Schema + Reader Fix  
**Phạm vi:** Phát hiện + fix UI lỗi alignment, thiết kế schema, Phase 0 audit  
**Files thay đổi:** `places.html`, `scripts/audit_cbeta_corpus.py` (new)  
**Files tạo mới:** `tasks/T94-cbeta-alignment-schema.md`, 7 docs design/audit  
**Rollback:** `git revert HEAD` (UI fix) | audit script read-only

---

## Lỗi alignment xác nhận

**Root cause:** LLM dịch toàn bộ passage Hán thành 1 chuỗi Việt liên tục (không ranh giới đoạn). `dtDistributeVi()` chia chuỗi Việt theo tỉ lệ ký tự. Ghép Hán[i] ↔ Vi[i] theo ordinal → lệch nội dung từ đoạn 2 trở đi, tích lũy ~8 đoạn tại đoạn 41.

**Bằng chứng:**
- Hán 41: 創翻大本。至龍朔三年十月末了。凡四處十六會說。總六百卷。(về dịch Đại Bát Nhã)
- Vi 41 hiển thị: "Năm Hiển Khánh thứ hai, giá hạnh Lạc Dương..." (thực ra là Hán đoạn ~33)

---

## Thay đổi places.html

### 1. Vi pane header — amber warning
```html
<!-- Trước: -->
<span style="font-size:9px;color:var(--da-muted)">VI</span>
<!-- Sau: -->
<span style="font-size:9px;color:#f59e0b;font-family:var(--da-font-mono);font-weight:700"
      title="Phân phối tự động theo tỉ lệ ký tự — chưa căn chỉnh đoạn với Hán văn">⚠ phân phối tự động</span>
```

### 2. CSS — `.dt-auto-align-note` và `.dt-seg-approx`
```css
.dt-auto-align-note { font-size:10px; color:#d97706; background:rgba(245,158,11,.08);
    border:1px solid rgba(245,158,11,.3); border-radius:4px; padding:6px 10px;
    margin-bottom:10px; cursor:help; line-height:1.5; font-weight:600 }
.dt-seg-approx { color:rgba(245,158,11,.55)!important; font-size:13px!important; cursor:help }
```

### 3. Vi segments — dùng `≈` thay ordinal
Trước: `<span class="dt-seg-num">01</span>`
Sau: `<span class="dt-seg-num dt-seg-approx" title="Vị trí xấp xỉ — không phải căn chỉnh xác nhận">≈</span>`

### 4. Alignment warning text (mạnh hơn)
```
⚠ PHÂN PHỐI TỰ ĐỘNG theo tỉ lệ ký tự — số thứ tự bên Việt KHÔNG khớp số bên Hán — chưa căn chỉnh nội dung
```

---

## Verification (browser, tab-9)

```js
// Kết quả:
{ viSegCount: 54, firstViNum: "≈", firstHanNum: "01",
  noteText: "⚠ PHÂN PHỐI TỰ ĐỘNG theo tỉ lệ ký tự — số thứ tự bên Việt KHÔNG khớp số bên Hán " }
```
✅ Tất cả đúng.

---

## Phase 0 Audit kết quả

Script: `scripts/audit_cbeta_corpus.py` (read-only, mới tạo)

| Chỉ số | Giá trị |
|--------|---------|
| Total passages | 7,563 |
| Has Vi | 218 (2.9%) |
| Empty Vi | 7,345 (97.1%) |
| Passages > 2000 chars | **20** (T50n2060 max 8,034 chars) |
| Duplicate raw_text | 0 ✅ |
| Hán trong Vi | 0 ✅ |
| Orphan passage_entity | 0 ✅ |
| Alignment tables | 0/3 ❌ |

**Phát hiện quan trọng:**
- Passages ngắn nhất chỉ 5 ký tự (có thể header/số trang)
- `passage_id=39` vi/han ratio=29x (han=62, vi=1822) — cần review thủ công
- T50n2060 passages dài là bình thường (biography dài), không phải lỗi concat

---

## Docs tạo trong session này

| File | Mô tả |
|------|-------|
| `docs/alignment-audit-report.md` | Xác nhận lỗi alignment, root cause, bằng chứng |
| `docs/bilingual-passage-alignment-design.md` | Schema 3 bảng mới, passage ID format |
| `docs/t50n2060-repair-plan.md` | 7-step repair plan cho T50n2060 |
| `docs/alignment-test-cases.md` | TC-001 đến TC-011 |
| `docs/cbeta-global-passage-standard.md` | Kiến trúc canonical CBETA ID toàn hệ thống |
| `docs/cbeta-corpus-audit.md` | Kế hoạch audit queries |
| `docs/cbeta-migration-rollout-plan.md` | Rollout plan 5 phases |
| `docs/cbeta-corpus-audit-results-20260904.md` | Kết quả audit Phase 0 thực tế |
| `docs/cbeta-corpus-audit-results-20260904.json` | Machine-readable |

---

## Kiến trúc quyết định

Áp dụng canonical CBETA anchor + internal immutable passage ID cho **TOÀN BỘ** CBETA content (không chỉ T50n2060).

Format: `daoanh:cbeta:{work_id}:{page_anchor}:p{seq:03d}`

Ví dụ: `daoanh:cbeta:T50n2060:0457a:p041`

---

## Pending (chờ approval)

- **Phase 1**: Tạo 3 bảng alignment schema (cần review SQL trước)
- **Phase 2**: T50n2060 pilot re-translate (cần backup + approval)
- **UI update**: Khi có alignment data, thay `≈` bằng số thật + đúng nội dung

---

## Rollback

```bash
# UI fix:
git revert HEAD

# Audit script (không cần revert — read-only):
# Chỉ xóa file nếu muốn:
# del daoanh\scripts\audit_cbeta_corpus.py
```

# Audit / Bug Fix Report — vi_qa_readability

> Task: BẢN DỊCH TIẾNG VIỆT (VI translation reader) hiển thị Zen Q/A dạng
> "một khối chữ trơn" khó đọc → định dạng hỏi-đáp thành từng lượt thoại rõ ràng.
> Lưu tại `docs/vi_qa_readability_REPORT.md` theo skill `daoanh-data-ui-debug`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `daoanh/data/lineage.db` — bảng `passage` (`passage_id`, `text_id`, `loc_ref`, `vi_text`, `is_translation_draft`) |
| API endpoint | KHÔNG đổi — render từ `p.vi_text` đã có sẵn trong payload passage (reader dùng `_dtPassages[idx]`) |
| Resolver / logic | KHÔNG đổi — không chạm `app.py`, không chạm pipeline dịch (Groq/`translation_segments`) |
| Component / renderer | `daoanh/places.html`: `dtFullBlockVi()` (max 2534 cũ), `dtToggleFullVi()` (bodyHtml cũ 2854-2857), helper mới `_reViQa` + `_dtViSplitDialogue()` + `_dtViDialogueHtml()` (đặt sau `_dtFormatFullViParagraphs`), CSS `.dt-qa-*` (cuối `<style>`) |
| Schema contract | trước / sau: **không đổi** (read-only render) |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer (+ layout)
- **Nguyên nhân chính xác:**
  - `dtFullBlockVi()` render toàn bộ `vi_text` vào **1 div `white-space:pre-wrap`**
    → các lượt `Sư nói: “…” / Tăng hỏi: “…”` nối liền thành khối chữ trơn, không phân biệt người nói.
  - `dtToggleFullVi()` (panel T98 "ĐỌC TOÀN PHẦN") chỉ chia paragraph theo sentence boundary
    (`_dtFormatFullViParagraphs`), **không** phân biệt lượt hỏi-đáp.
  - Xác minh bằng DB thật: **64 passage có ≥1 marker** `Người nói + động từ lời nói + :` trong `vi_text`,
    **20 passage có ≥2 marker** (đối thoại thật). Mẫu: P51 `Sư đáp: “Nghiệp giả…”`,
    P68 2 marker `Sư nói: … Sư phán: …` (giữa có narrative), P94 `Vua hỏi: “Đây là ai?”, Sư đáp: …` (7 lượt),
    P106 25 lượt dùng **ngoặc kép thẳng `"`**, P109 `Khả nói:/Khả đáp:` (tên riêng),
    P110/P111 `Tuần Chi hỏi:/Sư nói:`. NFC-normalized, dấu hai chấm ASCII `:`.
  - Marker xuất hiện **giữa câu** (sau `.`, `”,`, `?”`) → không thể bắt bằng line-start.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data | `vi_text` raw | `vi_text` raw — **không đổi, không ghi đè, không bịa** |
| API response | `p.vi_text` (Hán + Việt block) | `p.vi_text` — **không đổi** |
| Render | 1 div pre-wrap / paragraphs trơn | nếu có marker Q/A rõ → lượt thoại `.dt-qa-turn` (who + say quote-aware) + narrative `.dt-qa-narr`; không có marker → **fallback 100% render cũ** |

## 4. Files changed

- `daoanh/places.html` — duy nhất (render-time, frontend-only, không commit khác):
  1. Helper: `_reViQa` (regex marker, boundary + speaker + động từ lời nói + `:` + ngoặc mở),
     `_dtViSplitDialogue(text)` → `[{t:'qa',who,say,role:'q'|'a'}|{t:'narr',text}]` (quote-aware: say = trọn cụm `“…”`/`"…"`; marker không quote → gom tới marker kế; **bảo toàn text tuyệt đối** — who+say+narr = đúng chuỗi gốc; **role suy từ động từ marker**: hỏi/thưa/vấn/bạch = câu hỏi, nói/đáp/bảo/phán/dạy = trả lời),
     `_dtViDialogueHtml(text)` → HTML escaped (dùng `_escHtml`), bọc `<div class="qa-text">`, hoặc `null` (fallback).
  2. `dtFullBlockVi()`: khi `_dtViDialogueHtml` trả HTML → `<div class="dt-seg-text dt-seg-vi">` + qaHtml; else giữ nguyên div pre-wrap cũ.
  3. `dtToggleFullVi()`: bodyHtml = qaHtml nếu có, else giữ nguyên `paras.map(<p>)` cũ.
  4. CSS kiểu sách (v2, thay `.dt-qa-*` v1): `.qa-text` (serif 16px/1.8, max-width 600px, margin auto, justify)
     + `.qa-narrative` (text-indent 2em) + `.qa-turn` (không text-indent, margin 12px 0, padding-left .9rem,
     border-left 3px `var(--qa-accent)`) + `.qa-question`/`.qa-answer` (set `--qa-accent` từ token hiện có
     `--da-amber`/`--da-cyan` → **đổi màu theo light/dark tự động**, không hardcode, không nền vàng, không bubble chat);
     mobile: `max-width:100%`, padding nhẹ, không overflow.
  5. Regex speaker thêm `Vị kia` (P106 có "Vị kia nói:").

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- **KHÔNG chạm DB** — 0 migration, 0 import.
- Backup: không cần (không ghi DB).
- Revert: `git revert <commit>` (xem `docs/ROLLBACK.md`). Rollback base cũ `5300e0f` nguyên vẹn.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu — passage đối thoại thật | P51/P68/P87/P94/P106/P109/P110/P111 (`vi_text` từ DB) | ≥1 turn, say bắt đầu bằng ngoặc mở, text bảo toàn, phân vai HỎI/ĐÁP đúng | **29/29 assert pass** (v2); P94=7 turn (3 hỏi/4 đáp), P68=5 (3/2), P106=25 (4/21), P110=3 (1/2), P109=5, P111=3 — 100% preserved=true | ✅ |
| Role theo động từ marker | `Sư hỏi/Tăng hỏi/Vua hỏi/Có vị tăng hỏi` → hỏi; `Sư đáp/Sư bảo/Sư phán/Vị kia nói/Khả nói/Thầy dạy` → đáp | 10/10 đúng | ✅ |
| HTML classes v2 | Passage P94 | bọc `.qa-text`; `.qa-turn` + `.qa-question`/`.qa-answer`; `.qa-narrative`; không còn `dt-qa-*` | ✅ |
| Fallback — narrative không marker | `narr_1`, `narr_3` (passage không có "Sư/Tăng + động từ + :") | `null` → render cũ nguyên vẹn | ✅ null |
| Fallback — "…rồi nói:" giữa câu (không boundary) | `'Người kia nghe rồi nói: “…”'` | không tách (không phải marker rõ) | ✅ null |
| Fallback — empty string | `''` | `null` | ✅ |
| XSS | text có `<script>`,`<b>` trong narrative + marker | không có tag raw trong HTML | ✅ escaped |
| Syntax | toàn bộ inline `<script>` places.html (356,511 chars) | `node --check` OK | ✅ |
| E2E | `node scripts/e2e-test.js` | all pages pass | ✅ (placevn/index/dashboard) |
| Unit repo | `npm test` | pass | ✅ |

## 7. Limitation / data gap còn lại

- Chỉ format marker có **boundary rõ** (start / newline / `.,!?…！？”’`, `“/“”`) + người nói viết hoa + động từ lời nói (hỏi/nói/đáp/bảo/thưa/vấn/bạch/phán/dạy) + `:` + ngoặc mở. Marker thiếu inbound boundary (vd `xong nói: “…”` giữa câu) → giữ nguyên narrative (đúng định hướng "chỉ tách khi RÕ").
- Chưa phân loại role Q/A (vd thẻ "Hỏi/Đáp") — cố ý không thêm prefix mới; bộ CSS hiển thị who (đã có sẵn marker trong text) + turn ring.
- Units path (bilingual pairs / `translation_segments` per-unit) **không đổi** — Q/A readability áp cho toàn-văn (full-block + panel T98).
- Chưa test live browser (server :5000 bị chiếm bởi process hệ thống — pre-existing blocker) — tương đương T92/T94/T96/Ux trước đây: logic verified bằng node/E2E/unit on real data.
- Marker dùng số ít phổ biến của vi_text hiện tại; nếu pipeline dịch tương lai đổi format (vd thêm `—` trước marker, hay ngoặc `「」` không có đóng), cần review regex lại.
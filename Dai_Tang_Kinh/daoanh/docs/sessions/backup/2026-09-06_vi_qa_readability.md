# Session — 2026-09-06: vi_qa_readability (BẢN DỊCH TIẾNG VIỆT — Zen Q/A readability)

## Yêu cầu (user)
Bản dịch tiếng Việt (VI pane + panel "BẢN DỊCH TIẾNG VIỆT · ĐỌC TOÀN PHẦN") hiển thị đối thoại
Thiền như một khối chữ trơn khó đọc (`Sư nói: “…” Ngài hỏi: “…”` nối liền). Cần:
render-time-only (không sửa text/DB/API), không thêm prefix Q/A, chỉ tách block khi marker RÕ,
giữ narrative; CSS nhẹ: spacing + border-left/highlight theo light/dark theme, không nền vàng,
không bubble chat, không overflow ngang mobile; Hán văn + CBETA + evidence + copy không bị ảnh hưởng.

## Step 0 — Audit (đã xác minh, không đoán)
- Skill `daoanh-data-ui-debug` nạp. `docs/rules/ui-evidence-rules.md`: CẤM LLM suy diễn học thuật;
  CHO PHÉP pipeline dịch (Groq → `translation_segments`, `quality_status='unreviewed'`) — task này chỉ render.
- `docs/ROLLBACK.md` đọc: revert policy `git revert <hash>`, base `5300e0f`.
- Render path thật: `dtFullBlockVi(p)` (places.html:2528-2535, div `white-space:pre-wrap` toàn khối)
  + `dtToggleFullVi()` (2831-2863, bodyHtml = `_dtFormatFullViParagraphs().map(<p>)`).
  `_escHtml` escapes `& < > "`. Inline `<style>` 115-174; token gold `--da-gold*` trong `daoanh-design.css`
  (light `#8a5c08`, dark `#c4891a` → theme-aware tự động).
- Data reproduction (DB `data/lineage.db` 1.3GB; `daoanh/lineage.db` 0-byte = decoy):
  64 passage có ≥1 marker Q/A trong `vi_text`, 20 passage ≥2 marker. NFC-normalized, colon ASCII `:`,
  ngoặc mở `“` (U+201C) + `"` (U+0022). Mẫu: P51/P68/P87/P94/P106/P109/P110/P111 (chi tiết report).
- Marker giữa câu (sau `.`, `”,`, `?”`) → regex phải có boundary class; speaker generic hỗ trợ tên riêng
  viết hoa ("Khả nói:", "Tuần Chi hỏi:").

## Implementation (1 file: places.html, render-time only)
1. Helper `_reViQa` + `_dtViSplitDialogue(text)` + `_dtViDialogueHtml(text)` — đặt sau `_dtFormatFullViParagraphs`.
   - Quote-aware: say = trọn cụm ngoặc kép mở→đóng (`“…”` / `"…"`); marker không quote → gom tới marker kế;
     bỏ qua marker lồng trong lời thoại (`lastIndex = sayEnd`); **text bảo toàn tuyệt đối** (who+say+narr = chuỗi gốc).
   - Không match marker rõ → `null` → fallback render cũ (không regression).
2. `dtFullBlockVi`: qaHtml ≠ null → `<div class="dt-seg-text dt-seg-vi dt-seg-qa">…</div>`, else giữ nguyên.
3. `dtToggleFullVi`: bodyHtml = qaHtml nếu có, else giữ `paras.map(<p>)`.
4. CSS `.dt-seg-qa/.dt-qa-narr/.dt-qa-turn/.dt-qa-who/.dt-qa-say` — token `--da-gold` + `--da-gold-bg`,
   border-left 3px, tint mờ, `word-break/overflow-wrap:break-word; max-width:100%`, media 639px.

## Verification (Windows PowerShell 5.1, không bash pipe phức tạp)
- Unit test prototype với **vi_text thật từ DB**: 13/13 PASS — P51=1, P68=5, P87=1, P94=7, P106=25, P109=5,
  P110=3, P111=3 turn, 100% say quoted, preserved=true; narr_1/narr_3 → null; empty → null;
  "rồi nói:" giữa câu → null; XSS escaped.
- `node --check` trên inline `<script>` trích từ places.html (356,511 chars): OK (1 block duy nhất).
- `node scripts/e2e-test.js`: ✅ all pages passed (placevn/index/dashboard_process; places.html đã node --check).
- `npm test`: ✅ Tests passed.
- grep xác nhận call-site mới có mặt ở cả 2 render path (extract_0.js:1722, 2118).

## Out of scope / giữ nguyên
- Units path (bilingual pairs per `translation_segments`) không đổi.
- Server :5000 bị process hệ thống chiếm (pre-existing blocker, như T92/T94/T96) → no live browser test.
- `npm run lint` lỗi pre-existing Node v24 trên placevn.html (không liên quan).

## Files
- `daoanh/places.html` (fix)
- `docs/vi_qa_readability_REPORT.md` (báo cáo theo template audit-report.md)
- `docs/tasktodo.md` (entry task này)
- Temp (ngoài workspace, giữ trong `%TEMP%\opencode`): `qa_dialog_test.js`, `vi_samples.json`,
  `qa_dump_samples.py`, `qa_probe_cps.py`, `qa_extract_scripts.py`, `extract_0.js`

## Rollback
- UI: `git revert <commit>` — base `5300e0f` nguyên vẹn. Không đụng DB.

---

## v2 (2026-09-06) — Đọc kiểu sách + phân vai HỎI/ĐÁP (theo chỉ đạo Admin)

- **Styling tách bạch** (thay `.dt-qa-*` v1): container `.qa-text` (serif 16px, line-height 1.8,
  max-width 600px, margin auto, text-align justify) — chỉ `.qa-narrative` có `text-indent:2em`;
  `.qa-turn` KHÔNG text-indent, `margin:12px 0; padding-left:.9rem; border-left:3px solid var(--qa-accent)`.
- **2 accent màu qua CSS variables tái dùng token có sẵn** (không hardcode hex, tự đổi theo light/dark):
  `.qa-text{--accent-question:var(--da-amber);--accent-answer:var(--da-cyan)}`
  (light `#c07010`/`#0b7a96`, dark `#fbbf24`/`#22d3ee`) → `.qa-question{--qa-accent:var(--accent-question)}`,
  `.qa-answer{--qa-accent:var(--accent-answer)}`.
- **Phân vai theo động từ marker** (không thêm chữ, không prefix Q/A): `hỏi/thưa/vấn/bạch` → `qa-question`;
  `nói/đáp/bảo/phán/dạy` → `qa-answer` (thêm thuộc tính `role:'q'|'a'` trong `_dtViSplitDialogue`, mọi nhánh
  quoted + pending đều giữ role).
- **Thêm speaker `Vị kia`** vào regex (P106 có "Vị kia nói:") — generic name pattern không ghép được
  "Vị"(hoa)+"kia"(thường).
- Call-site giữ nguyên 2 nơi: `dtFullBlockVi` (bỏ class `dt-seg-qa`; `qaHtml` đã bọc `.qa-text`) +
  `dtToggleFullVi` (bodyHtml = `_dtViDialogueHtml` khi có marker, else fallback `paras.map(<p>)`).
- **Verify v2**: unit **29/29 PASS** (role: P68 3H/2Đ, P94 3H/4Đ, P106 4H/21Đ, P110 1H/2Đ; probes động từ 10/10
  gồm `Vị kia nói:` → đáp; HTML classes `.qa-text/.qa-turn/.qa-question/.qa-answer/.qa-narrative`, không còn `dt-qa-*`,
  preserved=true, fallback null, XSS) + node --check OK + E2E PASS + npm test PASS.
- Không đổi data/API/text; không thêm Q/A prefix; marker không rõ vẫn giữ `.qa-narrative`.
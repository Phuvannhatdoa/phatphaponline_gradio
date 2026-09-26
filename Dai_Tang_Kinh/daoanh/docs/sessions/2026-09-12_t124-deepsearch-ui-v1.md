# Session 2026-09-12 — T124 DeepSearch UI V1 (Safe-Fallback)

## Mục tiêu
Biến tab **🤖 DeepSearch** trong `places.html` từ mock (banner "Groq semantic ranking · API đang
phát triển" + spinner/setTimeout giả + leak endpoint) thành UI/UX hoàn chỉnh, an toàn khi backend
chưa sẵn sàng. Chỉ UI/UX — không đụng DB/corpus/Groq/APK key.

## Nguyên nhân gốc (đã xác minh)
- `places.html:664` (cũ) banner idle kỹ thuật; `dtRunDS()` (`:3452-3465` cũ) không validation,
  setTimeout 600ms giả lập loading rồi hiện "DeepSearch — API chưa sẵn sàng" kèm **leak endpoint
  `POST /daoanh/api/entity/{id}/deepsearch + Groq semantic-rank`** (L3461 cũ).
- API DeepSearch: **KHÔNG tồn tại** — grep `*.py`: 0 route `/deepsearch`, `/qa`, `semantic-rank`.
  Chỉ trong docs: `API_DOCS.md:146`, `DAI_TANG_KINH_TAB_SPEC.md`, `GAP_REPORT.md:729` (CRITICAL-missing).
  → Safe-fallback + không tự dựng request giả là đúng.

## Quyết định Lee (2026-09-12)
1. Chỉ UI/UX safe-fallback. Không sửa SQLite/corpus/source text, không gọi Groq, không thêm key,
   không tạo dữ liệu/trích dẫn giả.
2. States A idle / B loading (chỉ khi request thật — bỏ setTimeout giả) / C unavailable (không lộ
   endpoint/Groq/stacktrace) / D no-result / E result — D/E là code path chờ API thật khi xác minh.
3. Chỉ sửa 1 file `places.html`; backup trước; commit temp-index (real index đang có staged
   deletions từ agent ngoài — không reset).

## Triển khai
- **HTML tab** (`places.html:~670-682`): `.dt-ds-head` ("Hỏi theo ngữ cảnh" + mô tả), input mới
  placeholder "Ví dụ: Nhạn Môn Quan có trong tác phẩm nào?" + `aria-label`, nút aria-label,
  hàng gợi ý bấm được (`#dt-ds-hint` → `dtUseSuggestion`), vùng validation inline
  (`#dt-ds-validation`), result `#dt-ds-result` rỗng chờ JS.
- **CSS** (`:~111+`): `.dt-ds-head/.dt-ds-title/.dt-ds-sub/.dt-ds-hint/.dt-ds-sug( focus-visible )/
  .dt-ds-validation/.dt-ds-state(-ico/-t/-s)` — dùng biến `--da-*` đồng bộ light/dark.
- **JS**:
  - `_dtDSState(icon,title,sub)` — render state an toàn (title qua `_escHtml`).
  - `dtUseSuggestion()` — fill + focus, **không submit**, ẩn validation.
  - `dtRunDS()` — input trống/whitespace → validation inline + idle; ngược lại → state C
    ("DeepSearch đang được hoàn thiện. Bạn vẫn có thể tra cứu qua các tab Dẫn Chiếu, Nguyên Văn
    và Quan Hệ."), đặt `dataset.dsState='unavailable'`. Bỏ setTimeout giả + leak.
  - `dtRenderDSIdle()` — gọi từ `dtSwitchTab('deepsearch')`: chỉ render idle lần đầu
    (chưa có `data-ds-state`), giữ result khi đã có câu hỏi.
  - Enter input = nút (preventDefault), alt. Tab Hỏi & Đáp không đụng (ghi nhận việc sau).

## Verify
- `node --check` toàn bộ `<script>` của places.html: **PASS**.
- Logic test Node (DOM stub, 17 case): validation input trống/whitespace, idle A, unavailable C
  không leak endpoint/Groq, không spinner giả, suggestion fill+focus+không submit, idle render
  chỉ lần đầu, `_escHtml` chống XSS: **17/17 OK**.
- Playwright runtime thử load trang `http://localhost:8080/daoanh/places#PL000000000002` bị treo
  (trang nặng / test-results EPERM pre-existing) — bỏ qua, dùng logic test thay.
- backup: `docs/sessions/places.html.bak-deepsearch-t124` (522,549 bytes).

## Commit
- temp-index parent `b650e1b` (HEAD trước T124). Files: `places.html`,
  `tasks/T124-deepsearch-ui-safe-fallback.md`, `docs/sessions/2026-09-12_t124-deepsearch-ui-v1.md`,
  `docs/sessions/places.html.bak-deepsearch-t124`, `docs/tasktodo.md`, `data/progress_data.json`.

## Ghi chú
- Tab Hỏi & Đáp (`dtRunQA`) cùng pattern mock + nhắc Groq (`:687-696`, `:3525-3538` mới) — ngoài
  scope T124, đề xuất task sau để đồng bộ UI.
- `search.js` có `searchWithRAG`/`RAGConnector` — chưa dùng cho DeepSearch; chờ task backend thật.

## Live activation (2026-09-12)
- Sau T123 server restart, :8080 verify: page chứa `dt-ds-head` (tab mới) + KHÔNG còn banner
  "Groq semantic ranking" ở trang idle. T124 **live** trên :8080.
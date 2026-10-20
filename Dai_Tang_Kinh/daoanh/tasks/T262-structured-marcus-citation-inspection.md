---
id: T262
title: "Structured Marcus Citation Inspection — CBETA URL link trong provenance cards"
status: done
priority: high
created: "2026-10-08"
completed: "2026-10-08"
tags: [evidence, marcus, citation, cbeta, t260-extension, read-only]
depends_on: [T261]
blocks: []
former_ids: []
---

# T262 — Structured Marcus Citation Inspection

**Mở rộng:** T260 `_assertionCard()` provenance section — thêm clickable CBETA link  
**HEAD baseline:** 204e95b (T261 commit)  
**Nguyên tắc:** READ-ONLY · ZERO DB mutation · ZERO schema change · ZERO external LLM

---

## Phase 0 — Contract Check

| Câu hỏi | Kết quả |
|---------|---------|
| Format chính có URL | 6726 / 22332 (30.1%) |
| Extract sigla + locator lossless? | YES (regex 99.3% sạch) |
| cbeta_ref_passages coverage | 2 / 6726 (không khả dụng) |
| T236 reader tables | Không tồn tại |
| Approach | Render URL sẵn có thành `<a href>` |

**VERDICT: READY_TO_BUILD** — URL đã có trong data, không cần resolver nội bộ.

---

## Triển khai

### Backend — `app.py`

Thêm module-level regex:
```python
_T262_CBETA_URL_RE = re.compile(
    r'https?://cbetaonline\.dila\.edu\.tw/(?:zh/)?'
    r'(?:[A-Z]{1,3}\d+n[A-Z0-9]+)_(?:[a-z]\d+[a-c]\d+)'
)
```

Trong claim loop: extract `citation_url` (additive field, None nếu không có URL):
```python
_cu = _T262_CBETA_URL_RE.search(c["object_text"] or "")
"citation_url": _cu.group(0) if _cu else None,
```

### Frontend — `places.html`

Thêm `_parseSiglaPrefix(url)` — parse tiền tố T/B/J/GA/X từ CBETA URL.

Trong provenance loop của `_assertionCard()`:
- Nếu `c.citation_url` có và bắt đầu bằng `https?://cbetaonline.dila.edu.tw/`: render `<a href>` với sigla badge + `↗ CBETA Online`
- Tất cả qua `_escHtml()` + safety check `test()` phía JS

---

## Real Data Verification

| Metric | Giá trị |
|--------|---------|
| Tổng MARCUS claims | 22332 |
| URL sạch extractable | 6726 (30.1%) |
| A001897 URL claims | ≥1 |
| A001897 claim count | 34 (unchanged) |
| cbeta_ref_passages match | 2 (nội bộ không dùng) |
| DB mutation | NONE |

---

## Tests

File: `tests/test_t262_structured_citation.py`

| Test | Mô tả |
|------|-------|
| A | URL extracted từ object_text |
| B | https:// variant extracted |
| C | J-series sigla |
| D | None khi không có URL |
| E | None cho empty/None text |
| F | Malformed URL (truncated) không extract |
| G | Double-slash URL không extract |
| H | 望月 ref → None |
| I | CBETA inline text (no URL) → None |
| J | URL không phải cbetaonline → None |
| K | B-series sigla |
| L | X-series sigla |
| M | citation_url key luôn present trong claim dict |
| N | Zero DB mutation |
| real_db_full | A001897 regression (34 claims, ≥1 URL) |
| real_db_url_coverage | 25–35% coverage range |
| ast_guard | app.py AST parse valid |

T262: 17/17 PASS · T261 regression: 19/19 · T260 regression: 26/26 · Total: 62/62

---

## Rollback SHA

| Pass | SHA |
|------|-----|
| T262 commit | c84023a07c1b9170cfb83e4e02c0a5603c7364a9 |
| Không có DB mutation → không cần revert DB | |

# Báo cáo commit cô lập T465 / T467 / T469 (2026-10-26)

Không commit báo cáo này. Không push. Không ghi DB. Không đụng `docs/` (ngoài thư mục báo cáo/script này), `package.json`, `.gitignore`, `scripts/verify_design_compliance.py`.

## Tóm tắt

| Task | Trạng thái | PARENT | NEW | File (numstat) |
|---|---|---|---|---|
| T465 | ✅ Đã commit (phần của task) | `c2b9a4f5` | `bfdf1597d51dcfbff46912c21d4c899d8edf3bd7` | `app.py` 4+/2−; `admin/namevimap.html` 5+/3− |
| T467 | ✅ Đã commit (phần của task) | `bfdf1597` | `dbf4f79410823ca3313b4f16b428cf09b1a30a43` | `index.html` 55+/4− |
| T469 | ✅ Đã commit (phần của task) | `dbf4f794` | `540abcbb344c56edd13a3dc83cb711eb90eeefa9` | `app.py` 128+/0−; `index.html` 201+/11− |

HEAD hiện tại: `540abcbb344c56edd13a3dc83cb711eb90eeefa9`. `git rev-parse HEAD` đã xác nhận khớp.

Tổng phạm vi `c2b9a4f5..HEAD`: 3 file, 393 thêm / 20 xóa. Cộng theo task khớp đúng: T465 (9/5) + T467 (55/4) + T469 (329/11). Không có file ngoài 3 task.

## Cách làm (để không nuốt WIP)

- Script: `docs/sessions/2026-10-26/scoped-tasks/build_scoped_commit.py`. Mỗi commit dựng blob = **HEAD blob hiện tại** + các đoạn của task (lấy từ worktree bằng neo duy nhất, `assert` đếm đúng 1 lần khớp). Ghi bằng `git hash-object -w --no-filters` + `git update-index --cacheinfo` trên index tạm `GIT_INDEX_FILE=scoped-tasks/tmp_index`. Không `git add` file nào.
- Kiểm trước commit: (1) `--cached --name-status` đúng danh sách file; (2) mọi dòng `+` của commit tồn tại nguyên văn trong worktree (đã bỏ dấu phẩy cuối khi so; ngoại lệ 1 dòng ghi chú HTML có chủ đích, xem bên dưới).
- CAS thủ công trên `.git/refs/heads/truyen-dang-the-pho-clean` (đọc, so với parent, ghi `open(...,'w')`). Lần nào cũng khớp ngay, không phải retry.
- Commit message: `fix:`/`feat:` + mô tả. **Không thêm `+ docs`** vì commit không chứa thay đổi `docs/` (AGENTS §Commit Convention chỉ yêu cầu khi docs/sessions có thay đổi). Nếu Admin muốn cố định `+ docs`, cần amend/commit mới.

## T465 — `bfdf1597`

- Đã commit: JOIN `codex_place_name` theo `dila_id` trong `api_places_vi_map_list()`; thêm cột `claude_name_vi` vào SELECT; dòng dict `'claude_name_vi': r['claude_name_vi']`. Ở `namevimap.html`: ô cột Claude dùng `item.claude_name_vi`; tooltip `<th>` Claude; một câu ghi chú HTML về Claude.
- Kiểm bảng (chỉ đọc, `mode=ro`): `codex_place_name` tồn tại, 59.353 dòng, `COUNT(DISTINCT dila_id)` = 59.353 → JOIN 1-1, không nhân dòng. Mẫu `PL000000000009` = Lam Thị Thành, `PL000000000019` = Phạm Diên, `PL000000000168` = Bồ Đề Tự (có dữ liệu).
- Không hunk nào của T466 (`gemini_join`, `gemini_col`, `lex_map`/`_lexicon_han_lookup`) trong commit.
- Bỏ lại (không commit): sửa docstring của `api_places_vi_map_list` (đoạn docstring trong worktree trộn nội dung T466 "T466: cột Gemini JOIN ai_place_name..." trong cùng một đoạn, không tách sạch). **Hệ quả:** docstring HEAD vẫn ghi "Cột Claude/Gemini luôn null" — câu này đã sai sau commit, chỉ là chú thích nhưng nên sửa trong commit T466.
- Ngoại lệ có chủ đích: câu ghi chú HTML `Cột Gemini đang trống (giai đoạn 2, chưa triển khai).` được viết mới để giữ đúng ý nghĩa ở trạng thái T465 (cột Gemini vẫn trống khi chưa có T466).
- **Chưa kiểm:** chạy trình duyệt thật (screenshot/network) theo done_when của T465 chưa thực hiện trong phiên này; chỉ kiểm tĩnh (py_compile, dữ liệu DB).

## T467 — `dbf4f794`

- Đã commit: `handleSearch()` đọc `d.monks` / `d.works` (+ nhánh `d.places` giữ redirect như cũ, đúng bản vòng 2); thêm `renderSearchResultsMonks`, `renderSearchResultsWorks`, `renderSearchResults` (đặt ngay trước khối `/* ── T453: hiển thị kinh lục DILA`).
- Bỏ lại: dòng `closeSuggest(); // T469 ...` trong `handleSearch` (thuộc T469, đã được commit ở T469). Không có dòng nào của T469 trong blob T467 (đã kiểm bằng grep trên `git diff --cached` trước khi commit).
- Trạng thái task vẫn `in_progress` (đúng theo file task: chờ daoanh-qa vòng 2). Commit này không đổi status.
- **Chưa kiểm:** browser thật `http://127.0.0.1:8080/daoanh/` (Khuy Cơ / Long Môn / Thiếu Lâm Tự) không chạy trong phiên này.

## T469 — `540abcbb`

- Đã commit (`app.py`): khối cache `_PERSON_SUGGEST_CACHE` / `_WORK_SUGGEST_CACHE` + `api_search_suggest()` (route `/daoanh/api/search/suggest`) đặt trước `public_dila_works`. Khối nằm nguyên vẹn trong worktree, không trộn.
- Đã commit (`index.html`): CSS `.sr-suggest*`; hero bọc `.search-form` + `<div id="searchSuggest">` (xóa 11 dòng form cũ); dòng `closeSuggest()` trong `handleSearch` và `setSearch`; toàn bộ JS `_sg*`/`initSearchSuggest` (đặt trước `renderSearchResultsMonks`).
- **Bỏ lại (không thuộc 3 task):** khối CSS `dw-*` của **T453** trong worktree đã **di chuyển** từ cuối `<style>` lên trước `.search-tags` (diff chỉ là di chuyển, không đổi nội dung). Giữ nguyên vị trí HEAD trong commit; vẫn là thay đổi chưa commit trong worktree → cần quyết định riêng (không phải T469).
- Không có `CREATE INDEX` / DB write. Cache là in-memory (đúng ghi chú trong code).
- **Chưa kiểm:** đo thời gian phản hồi, EXPLAIN QUERY PLAN, screenshot và network log của T469 chưa được thực hiện trong phiên này (task yêu cầu). Chỉ kiểm tĩnh: `py_compile` blob `app.py` và `node --check` script inline của `index.html` ở HEAD đều OK.

## Hunk bỏ lại trong worktree (không commit, không thuộc 3 task)

| File | Nội dung | Thuộc |
|---|---|---|
| `app.py` ~dòng 7113 | `api_monk_ancestor_spine`: chọn thầy `primary_candidate` | Chưa rõ task (không phải 3 task) |
| `app.py` `api_places_vi_map_list` | cột Gemini (`has_gemini`, `gemini_join`, `gemini_col`), `lex_map` qua `_lexicon_han_lookup`, dòng `gemini_name_vi` | T466 |
| `app.py` ~dòng 25182 | khối "T445 Wizard API Endpoints" (`admin_backup`, `admin_fix_ids_preview`, `admin_schema_update` …) | T445 — **cảnh báo:** các route này có ghi DB/ALTER (`admin_schema_update`) và chỉ là placeholder; không nên deploy khi chưa duyệt |
| `admin/namevimap.html` | hàng nghìn dòng: flag-queue progressive (T437), compare summary (T446), cột Gemini (T466), ẩn đã Pass, sort Tin cậy, `dilaLink` PL → placevn | T437 / T446 / T466 |
| `index.html` | di chuyển khối CSS `dw-*` (T453) | T453 |
| `docs/…`, `tasks/…`, `docs/tasktodo.md`, `AGENTS.md`, … | nhiều WIP khác | không thuộc phạm vi |

Lưu ý: `git diff HEAD -- Dai_Tang_Kinh/daoanh/app.py` bây giờ chỉ còn các hunk trên (ancestor, T466, T445). Nếu deploy từ HEAD: T465 + T467 + T469 có mặt; T466/T437/T446 và phần Gemini **vẫn thiếu**; T445 wizard **không** có trong HEAD (đúng ý).

## Kiểm chứng (read-only, sau commit)

Script: `docs/sessions/2026-10-26/scoped-tasks/verify_commits.py`, chạy trên blob HEAD.

- PASS: mốc T465 (`LEFT JOIN codex_place_name c ON c.dila_id = pd.id`, `c.name_vi AS claude_name_vi`, `r['claude_name_vi']`, `item.claude_name_vi` trong `namevimap.html`).
- PASS: mốc T467 (`const monks = (d && d.monks) || [];`, `function renderSearchResults(monks, works, q, placesUrl)`).
- PASS: mốc T469 (`@app.route('/daoanh/api/search/suggest')`, `_get_person_suggest_cache`, `_get_work_suggest_cache`, `function initSearchSuggest()`, `id="searchSuggest"`, `closeSuggest` trong `setSearch`).
- PASS: không có marker của T466 (`gemini_join`, `item.gemini_name_vi`, `for han_name in set(name_zhs)`), T445 (`T445 Wizard API Endpoints`), ancestor (`primary_candidate`), T446 (`place-compare-summary`), T437 (`etlFlagQueueLoadAll`).
- PASS: `py_compile` (blob `app.py`), `node --check` JS inline `index.html`.
- FAIL giả (lỗi thiết kế check, không phải commit): marker `closeSuggest(); // T469: Enter` **phải** có ở HEAD vì thuộc T469. Đã xác nhận.
- PASS: `git diff --stat c2b9a4f5..HEAD` = đúng 3 file (`app.py`, `index.html`, `admin/namevimap.html`), 393/20 khớp tổng từng task.

Lệnh tái kiểm nhanh:
```
git show --stat bfdf1597 dbf4f794 540abcbb
git diff --stat c2b9a4f5..HEAD
python -X utf8 docs/sessions/2026-10-26/scoped-tasks/verify_commits.py
```

## Index thật

- Trước đồng bộ: `git diff --cached --name-status` chỉ có 3 file (`namevimap.html`, `app.py`, `index.html`) do HEAD đã đi trước index. Không có staged nào của phiên khác.
- Backup: `docs/sessions/2026-10-26/scoped-tasks/index.before-sync.bak` (465.499 byte).
- Đồng bộ: `read-tree HEAD` vào index tạm → ghi byte vào `.git/index` (`open('r+b')` + `truncate`). Đã ghi 465.499 byte.
- Sau đồng bộ: `git diff --cached --name-status` **rỗng** → index thật = HEAD. Index tạm `tmp_index` đã xóa.

## Việc chưa làm / cần người quyết

1. Chạy browser thật và đo phản hồi (T465 screenshot trước/sau; T467 Khuy Cơ/Long Môn/Thiếu Lâm Tự; T469 Huyền Trang/Khuy Cơ/Long Môn, EXPLAIN QUERY PLAN) — task yêu cầu, chưa thực hiện.
2. Quyết định `+ docs` trong message (hiện không có).
3. Sửa docstring `api_places_vi_map_list` (còn ghi "Claude/Gemini luôn null") — gộp vào commit T466.
4. Quyết định về khối CSS `dw-*` (T453) đã di chuyển trong worktree.
5. Khối T445 wizard trong `app.py` (ghi DB/ALTER) đang là WIP chưa duyệt; không đưa vào commit nào ở đây.

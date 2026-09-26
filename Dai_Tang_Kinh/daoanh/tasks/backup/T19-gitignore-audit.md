---
id: T19
title: Audit .gitignore — phân loại thư mục bị loại trừ có nhầm không
module: Hạ tầng / Git
priority: low
status: done
depends_on: []
created: 2026-08-18
updated: 2026-08-24
done_when: Mỗi entry đáng ngờ trong .gitignore đã được xác minh (nhầm → gỡ; đúng → giữ + note lý do)
---

# T19 — Audit `.gitignore` (daoanh/)

## Bối cảnh

`daoanh/.gitignore` (thêm bởi 1 phiên Claude Code khác đang dev song song, phát hiện 2026-08-18)
có comment đầu file: `# Git / honkit exclusions — giữ lại docs/, tasks/, dashboard/, styles/
(SUMMARY.md cần)` — cấu trúc này giống rule dành cho publish honkit/docs (chỉ track tài liệu),
không phải rule cho 1 app Flask đang chạy production.

Danh sách đầy đủ hiện tại:
```
node_modules/  data/  _book/  scripts/  tests/  src_python/  src/  .opencode/
ontology/  logs/  places/  config/  deploy/  static/  test-results/
*.pyc  __pycache__/  .DS_Store  *.log  *.db
```

**Đã xử lý:** gỡ `admin/` khỏi danh sách (2026-08-18) — xác nhận đây là thư mục admin UI thật của
app (chứa `placevn.html`, `dila_index.html`, và trang mới `missing_hanzi.html` của T08), việc bị
ignore khiến file admin mới không bao giờ xuất hiện trong `git status`/`git add`, tức không bao giờ
được commit dù code chạy đúng trên production.

**Đã xử lý:** gỡ `scripts/` khỏi danh sách (2026-08-21) — phát hiện khi cố `git add` 2 script mới
của T29 (`expand_hanviet_dictionary.py`, `retranslate_residual_hanzi.py`) và fix bug trong
`seed_persons_namevi.py` (T01) mà không thấy hiện lên trong `git status`. Xác nhận cùng lỗi như
`admin/` — đây là thư mục chứa script vận hành thật, nhiều cái được gọi trực tiếp từ quy trình
task-tracking (`build_progress_data.py`) hoặc từ CLAUDE.md's hướng dẫn. Gỡ ignore lộ ra thêm
**9 script trước giờ chưa từng track được** (kể cả của phiên dev khác): `bdrc_resolve.py`,
`build_places_search_fts.py`, `etl_time_authority.py`, `gitbook_daily_update.ps1`,
`link_marcus_glossaries.py`, `lint-check.ps1`, + 3 file của phiên này — **chưa git add** các file
không phải của mình vì chưa review nội dung, để phiên tương ứng hoặc 1 lượt audit riêng xử lý.

**Chưa xử lý — cần audit riêng từng entry:**
- `src/`, `src_python/` — tên chung chung, cần xem thực tế chứa gì trước khi quyết định.
- `config/`, `deploy/` — nếu chứa config/deploy script thật của app (không phải secret) thì nên track.
- `static/` — nếu là static asset thật của site (không phải build output) thì nên track.
- `places/` — cần xem có phải trùng với `places.html` (đã track ở root) hay là thư mục riêng.
- `ontology/` — có thể là dữ liệu lớn hoặc source thật, cần phân biệt.

**Không cần audit (đúng mục đích, giữ nguyên):**
- `data/`, `*.db`, `*.log`, `__pycache__/`, `*.pyc`, `.DS_Store`, `node_modules/`, `_book/`,
  `test-results/` — binary/generated/cache, ignore đúng.

## Cách làm khi pick up task này

1. Với mỗi entry đáng ngờ: `ls` thư mục đó trong `daoanh/`, xem nội dung có phải code/asset thật
   của app hay không (so với cách đã làm cho `admin/` — kiểm tra có route Flask nào serve từ đó,
   có bị reference trong `app.py`/`local_gateway.py`/`CLAUDE.md` không).
2. Nếu xác nhận nhầm (là code/asset thật) → gỡ khỏi `.gitignore`, chạy `git status` xem có file mới
   lộ ra không, báo cáo cho user trước khi `git add` (theo rule "Git — KHÔNG tự ý chạy" trong
   `CLAUDE.md`).
3. Nếu xác nhận đúng (thật sự không cần track — vd. build output, cache, dữ liệu lớn) → giữ nguyên,
   ghi rõ lý do bằng comment ngay trong `.gitignore` cạnh entry đó để lần audit sau không phải làm
   lại.
4. Cập nhật lại section "Chưa xử lý" ở trên khi xong.

## Kết quả audit 2026-08-24

| Entry | Tình trạng | Quyết định | Lý do |
|-------|-----------|------------|-------|
| `src/` | archive cũ, không load trong app.py | **giữ ignored** | code đã chuyển sang `src_python/` và `static/`; không có Flask route dẫn vào đây |
| `src_python/` | app.py line 7569 gọi ETL scripts trong `src_python/etl/` | **gỡ khỏi ignored** | live ETL scripts, cần track |
| `config/` | `config.yaml` chứa `graphdb_password: "root"` | **giữ ignored** | credentials, không commit |
| `deploy/` | `gunicorn_config.py`, `nginx.conf` server-specific | **giữ ignored** | config server, không versioned |
| `static/` | Flask route `/daoanh/static/<path>` (app.py 7127-7130) | **gỡ khỏi ignored** | live static assets, cần track |
| `places/` | 1 file `index.html` cũ, superseded bởi `places.html` | **giữ ignored** | dead archive |
| `ontology/` | 48,829 items generated TTL/JSON, `TTL_MASTER_DIR` (app.py 98) | **giữ ignored** | quá lớn (generated), không track |

## Acceptance criteria (checklist)
- [x] `admin/` — audit xong, xác nhận nhầm, đã gỡ (2026-08-18)
- [x] `scripts/` — audit xong, xác nhận nhầm, đã gỡ (2026-08-21)
- [x] `src/` — ignored đúng, thêm comment (2026-08-24)
- [x] `src_python/` — audit xong, xác nhận nhầm, đã gỡ (2026-08-24)
- [x] `config/` — ignored đúng, thêm comment (2026-08-24)
- [x] `deploy/` — ignored đúng, thêm comment (2026-08-24)
- [x] `static/` — audit xong, xác nhận nhầm, đã gỡ (2026-08-24)
- [x] `places/` — ignored đúng, thêm comment (2026-08-24)
- [x] `ontology/` — ignored đúng, thêm comment (2026-08-24)

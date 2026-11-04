---
id: T519
title: "3 route backend còn thiếu cho tab Catalog (namevimap.html) — catalog-works GET/gemini/pass"
module: Admin UI / Catalog tác phẩm CBETA
priority: p1
status: pending
created: 2026-11-04
updated: 2026-11-04
owner: daoanh-debugger
parent: null
depends_on: []
former_ids: []
done_when: |
  app.py có 3 route: GET /daoanh/api/admin/catalog-works (phân trang + q),
  POST /daoanh/api/admin/catalog-works/<cbeta_id>/gemini (đề xuất, không ghi DB),
  POST /daoanh/api/admin/catalog-works/<cbeta_id>/pass (ghi dila_catalog_works.title_vi
  + vi_source='admin_pass' + vi_status='approved' + vi_approved_by/at).
  python -m py_compile app.py sạch. curl 3 route trả JSON (không phải HTML/404).
  Tab Catalog trên namevimap.html load được danh sách, không còn lỗi
  "Unexpected token '<'". Admin xác nhận DONE sau khi xem bằng chứng — KHÔNG tự đánh DONE.
revert: |
  Code: bỏ block route T519 trong app.py (giữa comment "T519: Catalog tác phẩm"
  và trước "===== VISITOR COUNTER ====="), hoặc git checkout file từ backup
  docs/sessions/2026-11-04/app.py.bak-before-T519.
  DB: cột vi_approved_by/vi_approved_at là additive — revert bằng
  `python scripts/t519_catalog_works_approval_columns.py --revert` (set NULL,
  giữ cột, mất 0 title_vi gốc). Không DROP COLUMN.
outcome: >
  2026-11-04: Tạo route trong worktree wt/catalog-works-api (không sửa cây chính).
  Migration additive scripts/t519_catalog_works_approval_columns.py (dry-run + apply)
  đã chạy trên DB fixture trong worktree (DB thật 1.8GB không có trong worktree —
  xem Lưu ý). py_compile OK. curl 3 route + UI tab Catalog đã verify bằng DB fixture.
  Chưa chạy được với DB thật (data/lineage.db) vì worktree không có file này
  (gitignore, 1.8GB, không copy qua git worktree). Chưa tích hợp về cây chính,
  chưa commit, chưa đánh DONE — chờ Admin duyệt.
---

## Vấn đề

`app.py` không có route nào cho `/daoanh/api/admin/catalog-works*`. Frontend
`admin/namevimap.html` tab "📚 Catalog" (hàm `catalogLoad`, `catalogGeminiCall`,
`catalogPassWork`, dòng ~2869–3002) gọi 3 route này và nhận 404 HTML (Flask
default 404 page) → `response.json()` ném `SyntaxError: Unexpected token '<'`
vì body không phải JSON.

Đây là cùng lớp lỗi với T486 (work-verify) đã sửa trước đó — xem comment còn
để lại trong `app.py` dòng ~17193: "Route GET + POST .../pass dưới đây đang
THIẾU — frontend ... gọi 404 → lỗi Unexpected token '<'". Route catalog-works
là route **tiếp theo** chưa được wire, cùng nguyên nhân.

## Hợp đồng frontend (đọc từ admin/namevimap.html, không đoán)

- `GET .../catalog-works?page=&size=&q=` → `{ok, items, total, page, size, pages}`.
  Mỗi item: `cbeta_id, title_zh, hvdic, gemini_free, phien_am_claude,
  lexicon_hits, muc_luc_nmt (array), admin_pass (null | {name_vi, editor, at})`.
- `POST .../catalog-works/<cbeta_id>/gemini` (header `X-Session-Token`) →
  `{ok, gemini_vi}` — **không ghi DB** (dòng 2936 comment: "Server ghi file
  nháp; trả về đề xuất" — thực tế không cần ghi file nháp để route hoạt động
  đúng hợp đồng hiển thị; không ghi gì để tránh tích dữ liệu chưa duyệt).
- `POST .../catalog-works/<cbeta_id>/pass` body `{name_vi}` (header
  `X-Session-Token`, `Content-Type: application/json`) → `{ok}` (hoặc
  `{ok:false, error}`), ghi DB thật.

## Thiết kế field (không bịa — xem docs/sessions/2026-11-04 cho bằng chứng)

`dila_catalog_works` (5.747 dòng, kiểm bằng `PRAGMA table_info` + query thật
2026-11-04) đã có `title_zh`, `title_vi`, `vi_source` (toàn bộ hiện
`cloud_session`), `vi_status` (toàn bộ `unreviewed`) — **không có** cột cho
hvdic/gemini_free/lexicon_hits/muc_luc_nmt/admin_pass. Quyết định ánh xạ:

| Field frontend | Nguồn | Lý do |
|---|---|---|
| `phien_am_claude` | `title_vi` | Giá trị hiện có trong DB có `vi_source='cloud_session'` — là bản phiên âm do 1 session AI đưa vào trước đây, đang `unreviewed`; đúng vai "đề xuất của Claude" mà input Pass cần prefill. |
| `hvdic` | tính live bằng `_hanviet_charwise_translit()` (hàm đã có sẵn trong app.py, T372) trên `title_zh` | Tra cơ giới theo tự điển Hán-Việt per-char, khác hẳn `phien_am_claude` (ngữ cảnh) — cho Admin đối chiếu 2 nguồn. Không phải nguồn DILA/ZQLOCAL đã xác thực (hàm tự ghi rõ điều này trong docstring). |
| `lexicon_hits` | tính từ cùng hàm trên, dạng `"hits/total"` | Số chữ Hán tra được âm / tổng số chữ Hán trong `title_zh`. |
| `gemini_free` | luôn `null` ở GET | Không có cột lưu kết quả Gemini theo thiết kế (route `/gemini` không ghi DB theo đúng yêu cầu task) — tránh hiển thị dữ liệu cũ/sai lệch. |
| `muc_luc_nmt` | luôn `[]` | Không có nguồn dữ liệu nào trong schema hiện tại khớp khái niệm "mục lục NMT" — để trống thật thay vì bịa. |
| `admin_pass` | cột mới `vi_approved_by`/`vi_approved_at` (migration T519) + `title_vi` khi `vi_status='approved'` | additive, có migration riêng dry-run + revert. |

## Bảo vệ admin

`app.py` **không có** decorator `@require_admin` của riêng nó (decorator đó
nằm ở `server.py`, process/port khác — không import chéo được). Toàn bộ ~30
route admin khác trong `app.py` dùng pattern inline:
```python
token = request.headers.get('X-Session-Token', '')
if not verify_session(token):
    return jsonify({'ok': False, 'error': 'unauthorized...'}), 403
```
3 route mới dùng đúng pattern này để nhất quán (xem ví dụ gần nhất:
`api_admin_work_verify_list`/`api_admin_work_verify_pass`, dòng ~17299-17408).

## Lưu ý quan trọng — DB thật không có trong worktree

`data/lineage.db` (1.8GB) bị `.gitignore`, không được `git worktree add` vật
lý hoá. Đã test bằng DB fixture tạo riêng trong worktree (3 dòng lấy từ dữ
liệu thật đã đọc được ở cây chính qua `sqlite3` trước khi tạo worktree — xem
báo cáo build summary). **Chưa test với DB thật 5.747 dòng.** Khi tích hợp về
cây chính (qua `scripts/wt_integrate.py`), phải chạy lại
`scripts/t519_catalog_works_approval_columns.py --dry-run` rồi áp dụng trên
DB thật, và test lại route với DB thật trước khi Admin xác nhận DONE.

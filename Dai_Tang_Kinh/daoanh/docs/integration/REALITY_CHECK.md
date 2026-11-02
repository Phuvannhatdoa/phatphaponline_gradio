> Tạo bởi phiên Claude Code theo yêu cầu M0. Cập nhật lần cuối: 2026-11-01 (T508 — bổ sung
> số route đo lúc runtime bằng `app.url_map`, xem mục “Số route đo lúc runtime”; **số chuẩn đã xác nhận 376**).

# REALITY CHECK — Số liệu thực tế DB & code

Tài liệu này là nguồn sự thật duy nhất cho các con số về hệ thống.
Mọi spec (M0–M5) và CLAUDE.md phải tham chiếu file này, không ghi cứng số liệu.

## Số liệu đo trực tiếp

| Chỉ số | Tài liệu cũ ghi | **Thực tế đo được** |
|--------|-----------------|---------------------|
| DB size trên đĩa | 664 MB | **1.4 GB** |
| Số bảng trong DB | 67 | **156** |
| Số `@app.route` trong app.py (đếm **tĩnh**, regex `@\w*\.route(`) | 131+ | đo lại 2026-11-01: **339** (doc cũ ghi 313, đo 2026-10-02) |
| Số route lúc **runtime** — `app.py` (cổng 5000), `len(app.url_map.iter_rules())` | chưa từng đo | **369 rule** / **368 nếu trừ rule `static`**; 344 view function — đo 2026-11-01, xem mục “Số route đo lúc runtime” |
| Số route lúc **runtime** — `server.py` (cổng 5001), `len(app.url_map.iter_rules())` | chưa từng đo | **9 rule** / **8 nếu trừ rule `static`**; 7 view function — đo 2026-11-01, xem mục “Số route đo lúc runtime” |
| **Số route chuẩn (Admin xác nhận 2026-11-01)** — runtime trừ `static`: `app.py` 368 + `server.py` 8 | chưa từng có | **376** |
| **Mốc tĩnh hiện tại** — regex `@\w*\.route(` trên `app.py` + `server.py` | 437 (cũ) | **347** (339 + 8) |
| Số hàng `data_sources` | 13 | **14** |

> CLAUDE.md đã ghi 664 MB và 67 bảng — cần cập nhật sau khi xác nhận file này.

## Số route đo lúc runtime bằng `app.url_map` (T508, đo 2026-11-01)

> ⚠ **Số đo lúc runtime**: 369 (`app.py`) / 9 (`server.py`). **Số chuẩn Admin xác nhận**: **376** = `app.py` 368 + `server.py` 8 (trừ rule `static` của Flask). Mốc tĩnh tham chiếu: **347** = 339 (`app.py`) + 8 (`server.py`). Số cũ 437/448 **không tái lập được trên HEAD hiện tại** — xem giải thích bên dưới.

**Nguồn đo**

- Script: `docs/sessions/2026-11-01/T508-coder/measure_routes.py`
  (chỉ đọc; patch `sqlite3.connect` để mọi DB ghi ra sandbox tạm, không đụng
  `data/lineage.db` — xem `live-server-check.log` cùng thư mục).
- Lệnh chạy (cwd = `Dai_Tang_Kinh/daoanh`):

  ```powershell
  python -X utf8 docs\sessions\2026-11-01\T508-coder\measure_routes.py both `
      --json docs\sessions\2026-11-01\T508-coder\route-count-raw.json
  ```

- Log đầy đủ (từng rule + method): `docs/sessions/2026-11-01/T508-coder/route-count.log`
- Môi trường: Python 3.14.3, HEAD `5cbbd86b` (branch `wt/coder-t508`); `app.py` cùng
  nội dung với bản main repo (cùng 339 decorator) nên số không phụ thuộc worktree.
- Không đọc được `url_map` của tiến trình live trên cổng 5000 (không có endpoint
  chẩn đoán; thêm endpoint = sửa route code, ngoài phạm vi). Cách đo là import module
  trong tiến trình riêng — **cùng đường đăng ký route như lúc server khởi động**.

**Kết quả `len(app.url_map.iter_rules())`**

| Chỉ số | `app.py` (5000) | `server.py` (5001) |
|---|---|---|
| Tổng số rule (`iter_rules()`) | **369** | **9** |
| **Trừ rule nội bộ Flask `static` (số chuẩn)** | **368** | **8** |
| **Số chuẩn tổng cộng (Admin xác nhận)** | **376** | **376** |
| Số view function (endpoint) khác nhau | **344** | **7** |
| Số path (rule string) khác nhau | **366** | **9** |
| Theo method (đếm theo rule) | GET 245 · POST 124 · PUT 3 · DELETE 1 · PATCH 1 | GET 3 · POST 6 |

**Đối chiếu với cách đếm tĩnh (regex `@\w*\.route(`)**

| Cách đếm | `app.py` | `server.py` | Ghi chú |
|---|---|---|---|
| **Mốc tĩnh hiện tại (regex trên source, đo 2026-11-01)** | **339** | **8** | mỗi dòng decorator = 1 rule khai báo; **tổng 347** |
| Runtime (`url_map`) | 369 | 9 | nhiều hơn vì Flask tách multi-path + blueprint + `add_url_rule` + `static` |
| Chênh | +30 | +1 | xem bảng cân đối bên dưới |

**Mốc tĩnh cũ 437/448 (T322) — không tái lập được**: Lúc T322 (2026-10-31) code route nằm rải trong `routes_misc.py` (96), `routes_translate.py` (80), `routes_lineage.py` (72), `routes_places.py` (49), `routes_namevi.py` (33), `routes_pages.py` (19), `routes_ttl.py` (7), `core.py` (6), `t265_routes.py` (1)... Tổng cộng ~448 decorator. Các file này **đã không còn** trong `Dai_Tang_Kinh/daoanh` (đã gộp vào `app.py` nguyên khối 25.963 dòng). Regex chạy trên HEAD hiện tại cho 339 + 8 = 347. Do đó **mốc 437/448 là lịch sử, không dùng làm tham chiếu hiện tại**.

Cân đối `app.py` 339 → 369 (+30):

| Nguồn | Số rule |
|---|---|
| `@app.route` decorator (regex bắt được) | 339 |
| `@ app.route('/api/admin/queue/list')` — viết cách dấu `@` nên regex trượt | +1 |
| `app.route(...)(api_cbeta_compare)` — đăng ký kiểu gọi hàm (dòng 20220) | +1 |
| `app.add_url_rule(...)` — T130/T131 additive (3 rule) | +3 |
| Rule từ 2 blueprint: `ttl_profile_v2` 22 (`api_ttl_profile_v2.py` 13 + `api_codex_namevi.py` 4 + `api_generation_v2.py` 5), `ttl_anchor` 2 | +24 |
| Rule `static` Flask tự thêm | +1 |
| **Tổng** | **369** |

`server.py` 8 → 9: 8 decorator + 1 rule `static` (2 endpoint `login_verify`/`login_check`
mỗi endpoint có 2 path `/api/...` và `/daoanh/api/...` nên 7 endpoint → 8 rule).

**Đếm tĩnh toàn bộ `*.py` trong `daoanh/` (bỏ `docs/sessions` backup, `.git`,
`node_modules`): 423 decorator / 20 file** — trong đó `app.py` 339, `server.py` 8,
4 module blueprint 24, còn lại là các server/tooling phụ (`server_admin_extensions.py`
10, `api_ttl_rebuild.py` 7, `src_python/` 8, `conflict_server.py` 5, `api_zenlineage.py` 5,
`local_gateway.py` 2, `scripts/`, `tests/`…).

**Nếu thêm bỏ `docs/reports`**: 419 decorator / 18 file.


## data_sources — 14 nguồn hiện có

| source_id | source_code | legal_status | integration_mode | license_verified | active | implemented (source_authority) |
|-----------|-------------|--------------|------------------|------------------|--------|-------------------------------|
| 1 | DILA | AUDITING | INGEST | 0 | 1 | **1** |
| 2 | BDRC | UNKNOWN | BLOCKED | 0 | 0 | 0 |
| 3 | CBETA | AUDITING | INGEST | 0 | 1 | **1** |
| 4 | MARCUS | AUDITING | INGEST | 0 | 1 | **1** |
| 5 | ZQLOCAL | AUDITING | INGEST | 0 | 1 | **1** |
| 6 | Wikidata | AUDITING | INGEST | 0 | 1 | 0 |
| 7 | SAT | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 8 | CHGIS | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 9 | FoJin | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 10 | Kanripo | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 11 | SuttaCentral | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 12 | 84000 | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 13 | TGAZ | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 14 | ZENLINEAGE | INTERNAL_USE | INGEST | 0 | 1 | **1** |

**Nguồn trong plan 25 chưa có hàng trong DB:** Marcus SNA (nếu tách riêng khỏi MARCUS), GeoNames, World Historical Gazetteer, BGIS, IDP, Tipitaka.org/VRI, BuddhaNexus, MITRA-parallel, GRETIL, DSBC, PTS, OCBS, THL, Treasury of Lives.

## entity_claims — số claims thực tế

| source_id | source_code | claims |
|-----------|-------------|--------|
| 1 | DILA | 293,177 |
| 5 | ZQLOCAL | 118,295 |
| 4 | MARCUS | 22,332 |
| 3 | CBETA | 13,933 |
| 6 | Wikidata | 148 |

**Lưu ý:** Tất cả 447,885 claims này được nạp vào khi `license_verified=0` và `LicenseGate` chưa được nối vào đường nạp. Đây là rủi ro cần ghi nhận, không phải lỗi cần sửa ngay (xem M1).

## Cấu trúc file thực tế vs plan

### gate/ — có sẵn, chưa nối
- `gate/license.py` — `LicenseGate` class đầy đủ (T78)
- `gate/status.py` — `LegalStatus` enum
- `gate/provenance.py`
- `gate/analyzer.py` — `SourceAnalyzer` (được dùng ở 1 route admin)
- `gate/conflict_recorder.py`

### adapters/ — có sẵn, chưa nối
- `adapters/base.py` — `SourceAdapter` abstract class + `ExtractedEvidence` (T77)
- `adapters/registry.py`
- `adapters/bdrc/`

### .claude/ — **thiếu so với spec M0**
Hiện chỉ có: `launch.json`

Còn thiếu theo M0:
- `.claude/settings.json` (permissions + deny rules)
- `.claude/rules/*.md` (scoped rules cho adapters, gate, ETL, schema)
- Hook `PreToolUse` (chặn git ghi)
- `.claude/skills/onboard-source/`
- `.claude/agents/source-reviewer.md`

### Admin pages hiện có
`source_check.html` — trang Legal Check (M1 muốn mở rộng thành `sources.html`)

**Chưa có:**
- `admin/sources.html` (M1 — Source Hub)
- `admin/authority_sync.html` (M2)
- `admin/geo_review.html` (M3)
- `daoanh/credits.html` (M5)

## Khoảng cách lớn nhất cần xử lý (theo priority)

| # | Gap | Module | Độ khẩn |
|---|-----|--------|---------|
| 1 | Key Gemini hardcoded trong app.py (~dòng 1065, 1105) | M0 | **P0** |
| 2 | `LicenseGate` chưa nối vào bất kỳ ETL/route nào | M1 | **P0** |
| 3 | `.claude/settings.json` + hook PreToolUse chưa có | M0 | **P0** |
| 4 | 5 nguồn active có `license_verified=0` nhưng đã có 447K claims | M1+M5 | **P0** |
| 5 | `credits.html` và footer attribution chưa có | M5 | **P0** |
| 6 | `CLAUDE.md` ghi sai DB size (664MB) và số bảng (67) | M0 | P1 |
| 7 | `sources.html` admin page chưa có | M1 | P1 |

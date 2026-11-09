# REPORT — Cổng hai tầng (contract chặn · coverage cảnh báo) + sổ cổng đỏ

- Ngày: 2026-10-26 · Phiên con (subagent) · Scope: `scripts/verify_design_compliance.py`, `docs/known-failing-gates.md`
- **PARENT:** `6fc0d7993ba16f727f753122d6ec0984519e5f34`
- **NEW:** `f5d663586df5088ff1aab9c35a0c96b67a9ffbd7` (nhánh `truyen-dang-the-pho-clean`, CAS thủ công, tree `626e1f78…`)
- Không sửa app.py/index.html · không ghi DB · không `--apply` · không reset/checkout/stash/push · không dùng %TEMP%.

## 1. Phân loại metric (contract / coverage)

| Metric | Công thức (không đổi) | Goal | Trạng thái 2026-10-26 | Loại | Lý do |
|---|---|---|---|---|---|
| claims_with_source | entity_claims có source_id / tổng | 100 | pass 100% | coverage | % phủ dữ liệu so goal |
| claims_with_confidence | entity_claims có confidence / tổng | 100 | pass 100% | coverage | như trên |
| claims_reviewed | có reviewed_by / tổng | 1 | pass 9.83% | coverage | % phủ, bootstrap |
| claims_verified | verification_status='verified' / tổng | 1 | pass 9.83% | coverage | % phủ, bootstrap |
| claims_assertion_level | có assertion_level / tổng | 1 | **fail 0.00%** (15/447885) | coverage | % phủ; HITL-by-design |
| claims_with_audit | có audit_id trong audit / tổng | 100 | pass 100% | coverage | % phủ |
| events_provenance | events có provenance / tổng | 100 | pass 100% | coverage | % phủ |
| conflicts_resolved | resolved=1 / tổng conflicts | 1 | **fail 0.00%** (0/17999) | coverage | % phủ |
| glossary_vi_coverage | term có term_vi / tổng | 75.5 | pass 75.54% | coverage | % phủ |

Quy tắc an toàn: **lỗi cấu trúc** (bảng/cột thiếu, SQL lỗi) không còn là exception thô mà được bắt trong `compute()` → `gate_class='contract'`, `contract_error=<msg>`, status `fail`, chặn review. Không metric nào hiện là lưỡng tính; quy tắc "lưỡng tính → contract" được ghi trong code (`GATE_CLASS`).

Ghi chú: với dữ liệu hiện tại, metric `warn` (0 < % < goal) = 0. Chính sách strict chỉ bắt `fail` theo đặc tả ("mọi fail"). Nếu sau này cần strict bắt cả `warn`, phải quyết định riêng.

## 2. Diff tóm tắt script (82+/10−, chỉ thêm phân loại/exit/cảnh báo)

- **Không đổi:** `METRICS` (tên, công thức, `*_sql`, goal), `count()`, `open_conn()`, công thức `ratio/percent/status`, các khóa JSON cũ (`generated_at, db_path, read_only, total_tables, metrics, baseline_20260908, summary{pass,warn,fail,total}, source`), nội dung `note`.
- **Thêm:** argparse `--json` / `--strict` (parse trong `main()`, không ở top-level → import an toàn); `GATE_CLASS`, `OWNER_TASK`; `compute(strict=False)`; try/except `sqlite3.Error` quanh đếm; khóa metric bổ sung `gate_class`, `owner_task`, `contract_error`; khóa summary bổ sung `contract_fail_metrics`, `coverage_fail_metrics`, `gate_policy`; `_print_coverage_block()`; dòng `EXIT POLICY [...]` cuối log.
- **Exit:** `contract_fail` ≠ ∅ → 1; `--strict` và `coverage_fail` ≠ ∅ → 1; còn lại → 0.

## 3. Kiểm chứng (chi tiết: `verify.txt`, `gates.txt`)

| Lệnh | Exit | Kết quả |
|---|---|---|
| `python -X utf8 scripts/verify_design_compliance.py` | **0** | 7 pass / 2 fail (coverage) · khối `⚠ COVERAGE GAPS` in đúng định dạng · `EXIT POLICY … exit 0` |
| `python -X utf8 scripts/verify_design_compliance.py --strict` | **1** | cùng số liệu · `BLOCK: strict + coverage fail` |
| Probe contract (`contract_probe.py`, monkeypatch bảng không tồn tại, `--json`, OUT_PATH tạm) | **1** | `contract_fail=['claims_with_source']`, status fail, `gate_class=contract`, **không** cần `--strict`, không ghi file |

Cả hai lệnh chính đều ghi `data/design_compliance.json` (bản gốc đã sao lưu: `design_compliance.before.json`). File này **untracked** nên không nằm trong commit.

## 4. Sổ cổng đang đỏ (4 cổng, chi tiết ở `docs/known-failing-gates.md`)

| Cổng | Exit | Phân loại | Task | Lỗi gốc |
|---|---|---|---|---|
| `audit:honesty:strict` | 1 | **DATA** | T234 (H3: T252/T263) | H1 41 · H2 96 · H3 969 · H4 745 · H5 55 — FAIL 5/7 |
| `test:t232` | 1 | **CODE** (in-memory fixture) | T232 | test_09: `'candidate' != 'incomplete'` |
| `test:translation` | 1 | **DATA** | T178 (17c) · T200 (A001984) | 17c: DB `Thiên Nhiên` vs test `Đơn Hà Thiên Nhiên`; t200: `Linh Hựu` vs `Quy Sơn Linh Hựu` |
| `audit:t166` | 1 | **CODE/config + DATA/schema** | T166 | (a) `package.json` **không có khóa** `audit:t166`; (b) DB thiếu cột `translation_cache.identity_status` |

Ghi chú: chuỗi `&&` của `test:translation` dừng ở t178; các bước sau chưa đo trong chuỗi (chỉ t179 = PASS, t200 = FAIL đo riêng). `npm run` không in gì trên máy này (shim hỏng) nên mọi exit code là từ lệnh `python` trực tiếp.

## 5. Quyết định & lý do các lệch so với chỉ thị

1. **KHÔNG sửa `package.json`** (không thêm `test:compliance:strict`, không sửa khóa `audit:t166`). Lý do: `daoanh/package.json` **không nằm trong HEAD** (untracked) nên `git diff` rỗng không chứng minh được "sạch"; commit kiểu blob sẽ kéo theo toàn bộ nội dung chưa rõ. Chỉ thị ghi: nếu không sạch → không sửa, báo lại. Lệnh tương đương đã ghi trong docs. **Cần Admin quyết**: đưa package.json vào git (có thể lộ WIP) hay vá tay.
2. **Không chạy `npm run pipeline`** — ngoài scope lượt này; không đo gate khác (dup:ids, test:gov, uat, e2e).
3. Probe contract để lại trong thư mục phiên (không commit) làm bằng chứng.

## 6. Quan sát phụ

- **Lỗi giả ở app.py:** `/daoanh/api/compliance/dashboard?regenerate=1` (app.py:15816–15820) coi `returncode != 0` là 500. Trước đây mọi metric `fail` làm exit 1 dù JSON đã ghi → endpoint báo lỗi sai. Chính sách mới sửa phần coverage (exit 0). Contract vẫn exit 1 (đúng). **Chưa kiểm chứng HTTP live** (không chạy server). Không sửa app.py theo chỉ thị.
- **Dữ liệu đổi:** `conflicts_resolved` trước đây ghi nhận là warn 0.01% (T113, 2026-09-11); hiện 0/17999 → fail. Cần cập nhật tasktodo nếu Admin theo dõi số này.
- `claims_assertion_level` = 15 dòng (không phải 0 tuyệt đối) — phản ánh bootstrap của người review.

## 7. Rủi ro còn lại

- `except sqlite3.Error` bắt rộng: DB bị khóa tạm (`database is locked`) cũng thành contract → exit 1. Đây là chủ đích an toàn nhưng có thể gây chặn giả khi DB đang ghi.
- `OWNER_TASK` là bảng tay (suy từ tasktodo) — có thể lệch khi task đổi; không ảnh hưởng exit.
- Metric mới mặc định `coverage` (qua `GATE_CLASS` comprehension). Metric cấu trúc mới phải khai báo rõ — chưa có cơ chế bắt buộc.
- `test:compliance` trong `package.json` (không `--strict`) giờ exit 0 khi có coverage gap → pipeline sẽ **pass** bước này nhưng in cảnh báo. Đây là ý đồ của chính sách.

## 8. Khuyến nghị: có nên bật `--strict` trong `npm run pipeline`?

**KHÔNG.** Coverage gap là dữ liệu chưa đủ (assertion_level, conflicts_resolved), không phải lỗi code; bật strict trong pipeline sẽ biến mọi lần review thành chặn vì dữ liệu, và che giấu việc pipeline đang đỏ vì 4 cổng ở mục 4 vốn đã chặn. Giữ `--strict` cho bước phát hành / đánh giá dữ liệu (`npm run test:compliance:strict` khi package.json được xử lý ở mục 5.1).

# Sổ cổng đang đỏ (Known-failing gates)

> Đo lại: **2026-10-26** · HEAD lúc đo: `6fc0d7993ba16f727f753122d6ec0984519e5f34`
> Bằng chứng đầy đủ: `docs/sessions/2026-10-26/gate2-tiers/gates.txt` và `verify.txt`.

## 1. Chính sách cổng (áp dụng từ 2026-10-26)

| Loại cổng | Khi FAIL | Chặn review? | Ghi chú |
|---|---|---|---|
| **contract** (lỗi cấu trúc/hợp đồng: thiếu bảng/cột, SQL lỗi, JSON hỏng, script lỗi) | exit 1 | **Có** | Mặc định, không cần cờ. |
| **coverage** (mức phủ dữ liệu chưa đạt goal) | exit 0 + khối cảnh báo `⚠ COVERAGE GAPS` | **Không** | Ghi vào `data/design_compliance.json` (`summary.coverage_fail_metrics`). Metric sai vẫn ghi `status: fail`, không đổi nhãn. |
| **cổng cứng** — bật bằng `--strict` | mọi fail (contract + coverage) → exit 1 | **Có** | Dùng khi phát hành / đánh giá dữ liệu. Lệnh: `python -X utf8 scripts/verify_design_compliance.py --strict` (`npm run test:compliance:strict` sẽ có khi `package.json` được cập nhật — xem mục 5). |

- Dự án yêu cầu `npm run pipeline` xanh mới được review. Cổng **ngoài scope** (không thuộc task đang làm) được ghi ở sổ này và **không chặn DONE của task khác** (tiền lệ T390, Admin nghiệm thu 2026-10-15).
- Mọi cổng trong sổ này đều có **task sở hữu** và **tiêu chí gỡ** rõ ràng (cột bên dưới).
- Cổng cứng (`--strict`) **không** được bật trong `npm run pipeline` mặc định — xem khuyến nghị ở `docs/sessions/2026-10-26/gate2-tiers/REPORT.md`.

## 2. Bảng cổng đang đỏ

| # | Cổng | Lệnh thực | Exit | Lỗi gốc (rút gọn) | Phân loại | Task sở hữu | Tiêu chí gỡ | Ngày đo |
|---|---|---|---|---|---|---|---|---|
| 1 | `audit:honesty:strict` | `python -X utf8 scripts/audit_data_honesty.py --strict` | 1 | FAIL 5/7: H1 `event_evidence` lệch event_type **41**; H2 `time_mentions` trỏ authority placeholder **96**; H3 năm không suy ra được từ note/triều đại **969**; H4 nhãn `(N年建)` không khớp nguồn **745**; H5 `source_ref` tự tham chiếu **55** | **DATA** — bằng chứng: output trả số dòng trong DB (đếm trực tiếp), H1–H5 đều là dòng dữ liệu sai, không có lỗi import/code | T234 (cổng); H3 gắn T252 / T263 | `audit_data_honesty --strict` exit 0, **hoặc** Admin ký policy ngưỡng cho từng H (H3 còn 132 theo T252) | 2026-10-26 |
| 2 | `test:t232` | `python -B -X utf8 tests/test_t232_generation_engine.py` | 1 | `test_09_missing_parent_is_incomplete`: `AssertionError: 'candidate' != 'incomplete'` (graph `[(1,2),(4,2)]`, compute(2)) | **CODE/logic** — fixture `:memory:`, không đọc DB thật; engine trả `candidate` khi thiếu parent, test kỳ vọng `incomplete`. Chưa xác định bên nào sai (engine hay test) — cần đối chiếu spec T232 | T232 | `test_t232_generation_engine.py` 20/20 PASS | 2026-10-26 |
| 3 | `test:translation` | chuỗi `&&` của 14 lệnh con | 1 | Dừng ở **`test:t178`**: `FAIL 17c name_vi = Đơn Hà Thiên Nhiên [Thiên Nhiên]` (68/69). Ngoài chuỗi, `test:t200` cũng đỏ: `A001984 (got 'Linh Hựu')`, kỳ vọng `Quy Sơn Linh Hựu` | **DATA** — test ghim cứng tên từ DB: `vn_person_authority` A009460 đang `Thiên Nhiên`; A001984 đang `Linh Hựu`. Dữ liệu đã đổi so với kỳ vọng test (T195 ghi nhận tên gắn nhầm người) | T178 (17c) · T200 (A001984) | `test_t178` 69/69 **và** `test_t200` 25/25 — qua sửa dữ liệu đã duyệt hoặc Admin re-pin fixture | 2026-10-26 |
| 4 | `audit:t166` | (không có key trong `package.json`); chạy trực tiếp `python -X utf8 scripts/t166_identity_audit.py` | 1 | `sqlite3.OperationalError: no such column: identity_status` (bảng `translation_cache`) | **Hai lớp**: (a) **CODE/config** — `package.json` không có khóa `audit:t166`, dù tasktodo ghi đã wire vào pipeline; (b) **DATA/schema** — DB live chưa có cột `identity_status` (migration `t166_identity_migrate.py --apply` chưa áp trên DB này; nguyên nhân chưa xác minh) | T166 | (a) `package.json` có khóa `audit:t166` **và** (b) DB có cột `identity_status`, khi đó `audit:t166` exit 0. Áp migration cần Admin duyệt (DB mutation) | 2026-10-26 |

### Chi tiết lỗi đầu (trích từ `gates.txt`)

- **#1** — `[FAIL] H1 event_evidence.event_id khop event_type 41` · `[FAIL] H2 time_mentions.time_authority_id tro tai that 96` · `[FAIL] H3 nam suy ra duoc tu note hoac bang trieu dai 969` · `[FAIL] H4 nhan '(N年建)' co khop nguon 745` · `[BAO CAO] FAIL 5/7 — du lieu BI DANG/SAI.`
- **#2** — `FAIL: test_09_missing_parent_is_incomplete` · `AssertionError: 'candidate' != 'incomplete'` · `Ran 20 tests … FAILED (failures=1)`
- **#3** — `FAIL 17c name_vi = Đơn Hà Thiên Nhiên [Thiên Nhiên]` · `KẾT QUẢ: 68/69 PASS` · `Exited with code 1`
- **#4** — `sqlite3.OperationalError: no such column: identity_status` (`t166_identity_audit.py:263`)

## 3. Ghi chú bắt buộc khi đọc sổ

1. **Pipeline đang đỏ vì các cổng trên.** `npm run pipeline` chạy `audit:honesty:strict` (#1), `test:t232` (#2), `test:translation` (#3), `audit:t166` (#4). Đây là lý do pipeline không xanh; **không** che bằng cách hạ status metric.
2. **Chuỗi `test:translation` dừng sớm** (`&&`): các bước sau t178 chưa được đo trong chuỗi. Đo riêng cho thấy `test:t200` đỏ thêm. Các bước còn lại (t167, t169, t170, t74, t203, t207, t208, t211, t449) **chưa đo** — chưa có bằng chứng về trạng thái của chúng.
3. **`npm run` không in gì trên máy này** (shim npm hỏng). Mọi exit code trong sổ là từ lệnh `python` trực tiếp; `npm run audit:t166` không có bằng chứng exit code.
4. **Không cổng nào trong sổ ghi DB** (đã kiểm tra mã nguồn các test/audit trước khi chạy).
5. Lưu ý về chính sách mới: `app.py` (`/daoanh/api/compliance/dashboard?regenerate=1`) coi `returncode != 0` là lỗi 500. Trước đây mọi metric `fail` làm script exit 1 dù JSON đã ghi → endpoint báo lỗi giả. Với chính sách mới, coverage gap exit 0 nên lỗi giả này hết; contract vẫn exit 1 (đúng). **Không sửa app.py trong lượt này** (ngoài scope).

## 4. Trạng thái metric compliance (tham chiếu, 2026-10-26)

`claims_assertion_level` 15/447885 (0.00%, goal ≥1%) và `conflicts_resolved` 0/17999 (0.00%, goal ≥1%) là **coverage fail** → cảnh báo, không chặn review; chỉ chặn khi `--strict`. Các metric còn lại pass.

## 5. Việc chưa làm trong lượt này (cần quyết định)

- `package.json` **chưa** thêm `test:compliance:strict` và **chưa** sửa khóa `audit:t166`. Lý do: `daoanh/package.json` **không nằm trong HEAD** (untracked) nên `git diff` trả rỗng không chứng minh được là "sạch"; commit kiểu blob sẽ kéo theo toàn bộ nội dung chưa rõ. Lệnh tương đương để chạy bây giờ: `python -X utf8 scripts/verify_design_compliance.py --strict`.

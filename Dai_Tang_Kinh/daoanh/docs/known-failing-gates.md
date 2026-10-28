# Sổ cổng đang đỏ (Known-failing gates)

> Đo lại gần nhất: **2026-10-28** · HEAD khi cập nhật sổ (trước commit này): `ef997748cd825caf36566ffa595c7054f02ce467`
> Đo lần đầu: 2026-10-26 · HEAD `6fc0d7993ba16f727f753122d6ec0984519e5f34`.
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
- **Cổng `audit:honesty` — cơ chế RATCHET (Admin duyệt 2026-10-28):** so với cơ sở `docs/audit-honesty-baseline.json` (đo 2026-10-28: H1 41 · H2 96 · H3 969 · H4 745 · H5 55 · H6 0 · H7 0). **Vi phạm mới vượt cơ sở mới FAIL** (exit 1, chặn pipeline); nợ đã biết (≤ cơ sở) không chặn nhưng được in rõ. `--strict` (`npm run audit:honesty:strict`) = cổng cứng: mọi FAIL đều chặn. Cơ sở **không tự hạ** — người sửa task hạ tay khi có bằng chứng.

## 2. Bảng cổng đang đỏ

| # | Cổng | Lệnh thực | Exit | Lỗi gốc (rút gọn) | Phân loại | Task sở hữu | Tiêu chí gỡ | Ngày đo |
|---|---|---|---|---|---|---|---|---|
| 1 | `audit:honesty:strict` | `python -X utf8 scripts/audit_data_honesty.py --strict` | 1 | FAIL 5/7 (đo 2026-10-28). Vi phạm dữ liệu: **H1** `event_evidence` lệch event_type **41**; **H2** `time_mentions` trỏ authority placeholder `reign_era_dict` **96**; **H4** nhãn `(N年建)` không khớp note **745**; **H5** `source_ref` tự tham chiếu **55**. Độ phủ: **H3** không suy ra được năm từ note/triều đại **969**. **H6, H7 OK** | **DATA** — H1, H2, H4, H5 là dòng dữ liệu sai (không phải lỗi import/code); H3 là độ phủ (không suy ra được năm, không phải sai) | T234 (cổng); H3 gắn T252 / T263 | `audit_data_honesty --strict` exit 0, **hoặc** Admin ký policy ngưỡng cho từng H (H3 còn 132 theo T252) | 2026-10-28 |
| 2 | `test:translation` | chuỗi `&&` các lệnh con; dừng ở **`test:t200`** | 1 | `test:t200`: 1 FAIL / 25 — `A001984` trả `'Linh Hựu'`, kỳ vọng `'Quy Sơn Linh Hựu'`. Nguyên nhân: `vn_person_authority` chỉ có dòng alias `status='alias_vi_suffix'` (id `alias_A001984`), còn tên chuẩn `Quy Sơn Linh Hựu` nằm ở `people.name_vi`. Thuộc nhóm **33 dila_id trùng** của T200 §2 | **DATA** — cần Admin duyệt từng nhóm, sửa theo hướng additive | T200 (A001984) · nhóm 33 dila_id trùng (T200 §2) | `test_t200` 25/25 PASS (qua duyệt từng nhóm 33 dila_id trùng, additive) | 2026-10-28 |
| 3 | `audit:t166` | (không có key trong `package.json`); chạy trực tiếp `python -X utf8 scripts/t166_identity_audit.py` | 1 | `sqlite3.OperationalError: no such column: identity_status` (bảng `translation_cache`). **Lỗi gốc**: DB thiếu 4 cột (`translation_cache.identity_status`, `translation_cache.identity_issues`, `translation_cache.identity_lock_hash`, `translation_rules.identity_lock_policy`) + index `idx_tc_identity`. Migration `scripts/t166_identity_migrate.py` có `--dry-run` / `--apply` / `--revert`, **additive** (không mất dữ liệu), backup tự động trước khi `--apply` | **Hai lớp**: (a) **CODE/config** — `package.json` không có khóa `audit:t166`; (b) **DATA/schema** — DB live thiếu 4 cột + index nêu trên | T166 | (a) `package.json` có khóa `audit:t166` **và** (b) `t166_identity_migrate.py --apply` đã được Admin duyệt và chạy; khi đó `audit:t166` exit 0. `--apply` là DB mutation → **cần Admin duyệt** | 2026-10-28 |

### Chi tiết lỗi đầu (trích từ `gates.txt` và đo 2026-10-28)

- **#1** — `[FAIL] H1 event_evidence.event_id khop event_type 41` · `[FAIL] H2 time_mentions.time_authority_id tro tai that 96` · `[BAO CAO] H3 nam suy ra duoc tu note hoac bang trieu dai 969 (do phu)` · `[FAIL] H4 nhan '(N年建)' co khop nguon 745` · `[FAIL] H5 source_ref tu tham chieu 55` · `[OK] H6` · `[OK] H7`.
- **#2** — `[test:t200] FAIL 1/25: A001984 got 'Linh Hựu', expected 'Quy Sơn Linh Hựu'`. Các bước khác trong chuỗi đều PASS: `test:t165`, `t166`, `t178` (69/69), `t179`, `t167`, `t169`, `t170`, `t74`, `t203`, `t207`, `t208`, `t211`, `t449`.
- **#3** — `sqlite3.OperationalError: no such column: identity_status` (`t166_identity_audit.py:263`)

## 3. Ghi chú bắt buộc khi đọc sổ

1. **Pipeline đang đỏ vì các cổng trên.** `npm run pipeline` chạy `audit:honesty:strict` (#1), `test:translation` (#2), `audit:t166` (#3). Đây là lý do pipeline không xanh; **không** che bằng cách hạ status metric.
2. **Chuỗi `test:translation` dừng sớm** (`&&`) tại `test:t200`. Các bước đứng sau t200 trong chuỗi (t207, t208, t211, t449, …) chỉ được đo khi chạy riêng; kết quả đo riêng vẫn ghi ở mục 2 chi tiết. Đo lại chuỗi sau khi sửa t200 trước khi kết luận.
3. **`npm run` không in gì trên máy này** (shim npm hỏng). Mọi exit code trong sổ là từ lệnh `python` trực tiếp; `npm run audit:t166` không có bằng chứng exit code.
4. **Không cổng nào trong sổ ghi DB** (đã kiểm tra mã nguồn các test/audit trước khi chạy). Riêng `t166_identity_migrate.py --apply` là DB mutation và chưa được chạy.
5. Lưu ý về chính sách mới: `app.py` (`/daoanh/api/compliance/dashboard?regenerate=1`) coi `returncode != 0` là lỗi 500. Trước đây mọi metric `fail` làm script exit 1 dù JSON đã ghi → endpoint báo lỗi giả. Với chính sách mới, coverage gap exit 0 nên lỗi giả này hết; contract vẫn exit 1 (đúng). **Không sửa app.py trong lượt này** (ngoài scope).

## 4. Trạng thái metric compliance (tham chiếu, 2026-10-26)

`claims_assertion_level` 15/447885 (0.00%, goal ≥1%) và `conflicts_resolved` 0/17999 (0.00%, goal ≥1%) là **coverage fail** → cảnh báo, không chặn review; chỉ chặn khi `--strict`. Các metric còn lại pass.

## 5. Việc chưa làm trong lượt này (cần quyết định)

- `package.json` **chưa** thêm `test:compliance:strict` và **chưa** sửa khóa `audit:t166`. Lý do: `daoanh/package.json` **không nằm trong HEAD** (untracked) nên `git diff` trả rỗng không chứng minh được là "sạch"; commit kiểu blob sẽ kéo theo toàn bộ nội dung chưa rõ. Lệnh tương đương để chạy bây giờ: `python -X utf8 scripts/verify_design_compliance.py --strict`.

## 6. Cổng đã gỡ

| Ngày gỡ | Cổng | Commit (SHA) | Mô tả 1 dòng |
|---|---|---|---|
| 2026-10-28 | `test:t232` | `ef997748` | `test_09_missing_parent_is_incomplete` khớp hợp đồng BUG-032 (candidate + issue `unresolved_parent_branch`); `test_t232_generation_engine.py` PASS. |

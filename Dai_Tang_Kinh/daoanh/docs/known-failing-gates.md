# Sổ cổng đang đỏ (Known-failing gates)

> **Trạng thái 2026-10-29: `npm run pipeline` XANH (exit 0) — KHÔNG còn cổng đỏ trong pipeline.**
> HEAD khi cập nhật sổ: `873e7dcc` · Bằng chứng: `docs/sessions/2026-10-28-commit/pipeline.log` (1.804 dòng).
> Đo trước đó: 2026-10-28 · HEAD `ef99774` (4 cổng đỏ) · Đo lần đầu: 2026-10-26 · HEAD `6fc0d79`.
> Bằng chứng đầy đủ (giai đoạn 4 cổng đỏ): `docs/sessions/2026-10-26/gate2-tiers/gates.txt` và `verify.txt`.

> ⚠️ Sổ này giờ là **sổ lịch sử cổng + cổng cứng còn nợ**. Cổng `audit:honesty:strict` **vẫn đỏ** (5/7) nhưng **không** nằm trong `npm run pipeline` mặc định — pipeline chạy `audit:honesty` (ratchet) nên xanh.

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

## 2. Bảng cổng — trạng thái sau 2026-10-29

### 2a. Cổng đã GỠ khỏi pipeline (đều xanh, có bằng chứng trong `pipeline.log`)

| # | Cổng | Lệnh | Exit | Vì sao xanh | Ngày gỡ |
|---|---|---|---|---|---|
| G1 | `audit:honesty` (ratchet) | `python -X utf8 scripts/audit_data_honesty.py` | 0 | Cơ chế **ratchet**: PASS khi **không có vi phạm MỚI** vượt cơ sở `docs/audit-honesty-baseline.json`. Log: `PASS (ratchet) 7/7 — không vi phạm MỚI; nợ đã biết: 5 kiểm tra.` | 2026-10-28 (commit `997565ae`) |
| G2 | `test:translation` → `test:t200` | `python -X utf8 tests/test_t200_*.py` | 0 | Thêm dòng canonical `A001984` vào `vn_person_authority` (additive, giữ dòng alias) → 25/25 PASS | 2026-10-28 (commit `9d8a1e0c`) |
| G3 | `audit:t166` | `python -X utf8 scripts/t166_identity_audit.py` | 0 | Migration T166 đã apply (4 cột + index `idx_tc_identity`, additive). Log: `✅ T166 audit: PASS — schema đủ, app guard đầy đủ, auth ok, data hợp lệ` | 2026-10-28 (commit `989ccfc4`) |
| G4 | `test:gov` | `python -X utf8 -m pytest tests/test_b25_authority_contract.py -v` | 0 | 18/18 PASS (license theo chính sách hiện hành: danh sách nguồn đã xác minh, phi thương mại, **không** backfill license) | 2026-10-28 (commit `b71a68b0`) |
| G5 | `dup:ids` | `npm run dup:ids` | 0 | Sau khi gộp T432/T433/T434 → T442/T443/T444. Log: `[OK] Không có task ID trùng thật.` | 2026-10-28 (commit `f2958353`) |

### 2b. Cổng CỨNG còn đỏ — KHÔNG nằm trong pipeline mặc định

| # | Cổng | Lệnh thực | Exit | Lỗi gốc (rút gọn) | Phân loại | Task sở hữu | Tiêu chí gỡ | Ngày đo |
|---|---|---|---|---|---|---|---|---|
| 1 | `audit:honesty:strict` | `python -X utf8 scripts/audit_data_honesty.py --strict` | 1 | FAIL 5/7. Vi phạm dữ liệu: **H1** `event_evidence` lệch event_type **41**; **H2** `time_mentions` trỏ authority placeholder `reign_era_dict` **96**; **H4** nhãn `(N年建)` không khớp note **745**; **H5** `source_ref` tự tham chiếu **55**. Độ phủ: **H3** không suy ra được năm từ note/triều đại **969**. **H6, H7 OK** | **DATA** — H1, H2, H4, H5 là dòng dữ liệu sai (không phải lỗi import/code); H3 là độ phủ (không suy ra được năm, không phải sai) | T234 (cổng); H3 gắn T252 / T263 | `audit_data_honesty --strict` exit 0, **hoặc** Admin ký policy ngưỡng cho từng H (H3 còn 132 theo T252) | 2026-10-29 |

> **Cổng cứng này chỉ chặn khi phát hành / đánh giá dữ liệu** (`--strict`), không chặn `npm run pipeline` mặc định — xem mục 1 (chính sách cổng, Admin duyệt 2026-10-26) và `docs/sessions/2026-10-26/gate2-tiers/REPORT.md`.

### Lịch sử chi tiết (giai đoạn 4 cổng đỏ, đo 2026-10-28 — đã gỡ)

- **#1 `audit:honesty:strict`** — `[FAIL] H1 event_evidence.event_id khop event_type 41` · `[FAIL] H2 time_mentions.time_authority_id tro tai that 96` · `[BAO CAO] H3 nam suy ra duoc tu note oac bang trieu dai 969 (do phu)` · `[FAIL] H4 nhan '(N年建)' co khop nguon 745` · `[FAIL] H5 source_ref tu tham chieu 55` · `[OK] H6` · `[OK] H7`. **→ Đã gỡ khỏi pipeline** bằng ratchet (G1); vẫn đỏ ở chế độ `--strict`.
- **#2 `test:translation`** — `[test:t200] FAIL 1/25: A001984 got 'Linh Hựu', expected 'Quy Sơn Linh Hựu'`. Các bước khác trong chuỗi đều PASS: `test:t165`, `t166`, `t178` (69/69), `t179`, `t167`, `t169`, `t170`, `t74`, `t203`, `t207`, `t208`, `t211`, `t449`. **→ Đã gỡ** bằng dòng canonical A001984 (G2).
- **#3 `audit:t166`** — `sqlite3.OperationalError: no such column: identity_status` (`t166_identity_audit.py:263`). **→ Đã gỡ** bằng migration additive T166 (G3).

## 3. Ghi chú bắt buộc khi đọc sổ

1. **`npm run pipeline` hiện XANH (exit 0)** — bằng chứng: `docs/sessions/2026-10-28-commit/pipeline.log`. Chuỗi đầy đủ: `guard → dup:ids → audit:honesty → audit:h3 → lint → test → test:t226/t227/t232/t233/t253/t242/t243/t244 → test:translation → test:uat → test:compliance → test:gov → audit:t166 → e2e → e2e:runtime`. Kết quả đáng chú ý: `audit:honesty` **PASS (ratchet) 7/7** · `test:gov` **18/18 PASSED** · `audit:t166` **✅ PASS** · `e2e` All pages passed · `e2e:runtime` **2 passed**.
2. **`audit:honesty:strict` vẫn đỏ (exit 1, 5/7)** nhưng **không** nằm trong pipeline mặc định (ratchet thay thế). Cổng cứng — chỉ bật khi phát hành / đánh giá dữ liệu. Nợ đã biết: H1 41 · H2 96 · H3 969 · H4 745 · H5 55. **Cơ sở không tự hạ** — người sửa task hạ tay khi có bằng chứng.
3. **`npm run` không in gì trên máy này** (shim npm hỏng) → dùng `npm.cmd run <script>`. Mọi exit code trong sổ lấy từ `npm.cmd run ...` hoặc `python` trực tiếp.
4. **Không cổng nào trong sổ ghi DB** (đã kiểm tra mã nguồn các test/audit trước khi chạy). Riêng `t166_identity_migrate.py --apply` là DB mutation và **đã** được Admin duyệt + chạy (2026-10-28).
5. Lưu ý về chính sách mới: `app.py` (`/daoanh/api/compliance/dashboard?regenerate=1`) coi `returncode != 0` là lỗi 500. Trước đây mọi metric `fail` làm script exit 1 dù JSON đã ghi → endpoint báo lỗi giả. Với chính sách mới, coverage gap exit 0 nên lỗi giả này hết;

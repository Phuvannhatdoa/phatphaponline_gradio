# T500 — Cổng license CBETA Catalog API

- Ngày: 2026-10-29
- Nguồn: CBETA (`data_sources.source_code = 'CBETA'`, `source_id = 3`)
- Chuẩn áp dụng: `tests/test_b25_authority_contract.py` (commit `b71a68b0`), mục "dự án GIÁO DỤC, PHI THƯƠNG MẠI".

## Kết quả: ĐẠT CÓ ĐIỀU KIỆN

Nguồn đã được Admin xác minh license (2026-10-22), `license_verified = 1`. Dữ liệu catalog là phần của CBETA nên chịu cùng điều kiện.

| Trường (`data_sources`) | Giá trị | Ý nghĩa |
|---|---|---|
| `license_spdx` / `corpus_license` | CC-BY-NC-SA-4.0 | Chia sẻ lại phải ghi công, phi thương mại, chia sẻ tương tự |
| `noncommercial` | 1 | Chỉ phi thương mại |
| `data_commercial` | 0 | Không cho dùng thương mại |
| `derivative_allowed` | 1 | Được tạo dẫn xuất (bảng quyển) |
| `sharealike_required` | 1 | Dẫn xuất phải giữ CC-BY-NC-SA |
| `attribution_required` | 1 | Phải ghi nguồn CBETA |
| `license_verified` | 1 (Admin 2026-10-22) | Đã xác minh |

## Điều kiện bắt buộc khi nạp dữ liệu

1. Ghi nguồn CBETA trên mọi trang hoặc file dùng dữ liệu này.
2. Dữ liệu dẫn xuất (`work_volumes`, `volume_files`, `work_alias`) giữ giấy phép CC-BY-NC-SA-4.0.
3. Không dùng cho mục đích thương mại. Nếu có, phải xin đồng ý của CBETA trước.
4. Không đổi nội dung của mục (`juan`, `file`, mã) khi công bố; chỉ thêm chú thích.

## Điểm cần Admin xem (không chặn, nhưng ghi nhận)

- `data_sources.legal_status` và `data_license_status` đang là **AUDITING**, `terms_status` là **under_review**.
  Admin đã xác nhận license ngày 2026-10-22, nhưng trạng thái kiểm toán pháp lý chưa được cập nhật.
- `api_terms` của CBETA đang trống. Điều khoản dùng API `cbdata.dila.edu.tw` chưa được ghi rõ trong DB. Trang chính sách của CBData không trả nội dung riêng về API. Nếu cần, Admin nên xác nhận thêm với CBETA.
- Repo `DILA-edu/cbeta-metadata` là MIT (đã kiểm trên GitHub API). Metadata từ repo này khác với API, nên chưa dùng repo này để nạp.

## Nguồn đã kiểm

- https://cbeta.org/copyright (trang "CBETA 版權宣告"): phi thương mại; chia sẻ lại giữ nguyên nội dung, ghi kèm thông báo và phiên bản; cần đồng ý khi thương mại.
- `data_sources` dòng CBETA (chỉ đọc, `lineage.db`).
- https://github.com/DILA-edu/cbeta-metadata (MIT), không dùng làm nguồn nạp cho T500.

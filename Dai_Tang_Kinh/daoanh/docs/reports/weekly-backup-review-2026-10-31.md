# Rà soát bản sao lưu DB cũ — 2026-10-31

Chạy tự động theo lịch `weekly-backup-cleanup-review`. Chỉ đọc, không ghi DB, không git, không gọi API, không xóa hay di chuyển file.

## Phạm vi quét

- Thư mục: `data/backups/` (đệ quy), tổng 115 file `.db`.
- Điều kiện: ngày sửa cũ hơn 30 ngày (trước 2026-10-01).
- Có 8 file thỏa điều kiện.
- Đối chiếu tên file trong `docs/` (gồm `docs/ROLLBACK.md`) và `tasks/`.

## Kết quả đối chiếu

Đã được tham chiếu (6 file, giữ nguyên, không đưa vào danh sách ứng viên):

| File | Được nhắc tới trong |
|---|---|
| `lineage_t169_20260928_130129.db` | `docs/sessions/2026-09-28_t169-place-groq-audit-build.md`, `tasks/T169-place-groq-audit-build.md` |
| `lineage_t170_20260928_150114.db` | `docs/sessions/2026-09-28_t170-v41-build.md`, `tasks/T170-dila-place-person-v41-verify.md` |
| `lineage_backup_t172_20260929_114458.db` | `docs/Mimo-Flash/T172-hanviet-charwise-debug-REPORT.md` |
| `lineage_backup_t172_20260929_114540.db` | `docs/sessions/2026-09-29_t172-hanviet-charwise-build.md`, `tasks/T172-hanviet-charwise-debug.md` |
| `lineage_t199_20261001_141928.db` | `docs/sessions/2026-10-01_t199-vnpa-trim-and-canonical-row.md` |
| `lineage_t199_20261001_142839.db` | `docs/sessions/2026-10-01_t199-vnpa-trim-and-canonical-row.md` |

Chưa được tham chiếu — **CHƯA ĐƯỢC THAM CHIẾU** (2 file):

| # | Đường dẫn (từ `daoanh/`) | Ngày sửa | Dung lượng |
|---|---|---|---|
| 1 | `data/backups/lineage_pre_gen_system_20260928.db` | 2026-09-28 | 1.486.057.472 byte (~1,38 GiB) |
| 2 | `data/backups/lineage_t169_20260928_130324.db` | 2026-09-28 | 16.384 byte (16 KiB) |

Ghi chú: file thứ 2 có tên gần giống bản sao lưu T169 ở trên nhưng dung lượng chỉ 16 KiB, có vẻ là bản sao lưu lỗi hoặc rỗng. Đây chỉ là suy đoán từ kích thước, chưa kiểm tra nội dung.

## Tổng dung lượng có thể giải phóng

- 2 file, tổng khoảng **1.486.073.856 byte (~1,38 GiB)**.
- Gần như toàn bộ dung lượng nằm ở file `lineage_pre_gen_system_20260928.db`.

## Đề xuất cho Admin

Chưa xóa. Cần Admin xác nhận trước khi xóa vĩnh viễn.

Trước khi xác nhận, nên kiểm tra thêm:
- `lineage_pre_gen_system_20260928.db`: đây là bản sao lưu trước đợt sinh hệ thống (gen system) ngày 2026-09-28. Không có tài liệu nào nhắc tới, nên cần xác nhận không còn cần để khôi phục.
- `lineage_t169_20260928_130324.db`: kiểm tra có phải bản lỗi hoặc rỗng không trước khi xóa.

Lưu ý: tên file kiểm tra bằng grep khớp theo tên đầy đủ, nên không bắt được trường hợp docs ghi tên khác (ví dụ chỉ ghi ngày). Không có kết quả nào bị bỏ sót theo cách này.

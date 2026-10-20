# Session 2026-10-08 — T265 H3 year-support (lô B)

**Task:** `tasks/T265-h3-year-support-plan.md` (con của T263).
**Phê chuẩn:** Admin phê chuẩn đề xuất: bảng quyết định bổ sung, bước 0 chỉ đọc, duyệt từng lô.

## Đã làm

| Bước | Kết quả |
|---|---|
| 0. Lấy mẫu chỉ đọc | 30 dòng (10/nhóm), seed 20261008 → `docs/evidence/2026-10-08_T265_sample_step0.tsv` |
| Kiểm tra mẫu | Nhóm B: năm nằm trong niên hiệu (ví dụ 792 trong 貞元 801). Nhóm C và A: năm lưu lệch rõ so với niên hiệu (ví dụ 345 so với 大中祥符 1011). Chưa điền cột `kiem_tra_thu_cong`. |
| 1. Sao lưu DB | `data/backups/lineage.T265-pre-support-20261008-173329.db`, 1,7 GB, `quick_check` = ok, 3688 sự kiện |
| 2. Tạo bảng | `timeline_year_support` (bổ sung), cột `event_id` PK, trạng thái có CHECK |
| 3. Lô B | 74 id → `era_range`, 1 transaction. Kiểm tra sau ghi: `era_range: 74`, `place_timeline_events` vẫn 3688 dòng |

## Phát hiện trong khi làm

- Cặp `(PL000000058474, 1694)` khớp 2 id trùng từ `wikidata` và `wikidata_p571`. Script ban đầu dừng vì chỉ chấp nhận khớp 1-1. Đã sửa: gom mọi id của cùng cặp, áp cùng một quyết định.
- README dashboard ghi DB 633 MB. Thực tế 1,7 GB.
- `T263` đã bị đổi thành `status: blocked` với `undone_reason` bởi một tiến trình khác trên đĩa (lúc 17:42). Chưa đổi lại. Cần Admin hoặc người quản lý tiến trình đó xác nhận.

## Chưa làm (chờ duyệt)

- Lô C (182): đánh dấu `review` hoặc tách sự kiện.
- Lô A (29): xem từng dòng, chỉ `corrected` khi có nguồn riêng.
- Cập nhật audit để tính dòng đã có quyết định. Chưa đổi exit code `--strict`.
- P3 chặn strict, P4 nhãn `民民國`.

## Revert

- `DROP TABLE timeline_year_support;`, hoặc khôi phục file backup ở trên.
- Không commit git trong phiên này.

## Cập nhật: lô C (2026-10-08, sau khi Admin duyệt "review")

| Bước | Kết quả |
|---|---|
| Backup lần hai | `data/backups/lineage.T265-pre-support-20261008-175514.db`, quick_check ok |
| Lô C | 182 id → `review`, 1 transaction, lý do ghi rõ "cần người rà và tách, không sửa năm tự động" |
| Kiểm tra sau ghi | `place_timeline_events` = 3688. `timeline_year_support`: era_range 74, review 182 |
| Dashboard | Chạy lại `build_t263_status.py` và `build_progress_data.py` (exit 0) |

Ghi chú: một lệnh kiểm tra toàn vẹn trên DB 1,7 GB chạy quá 10 phút và được chuyển sang nền. Kết quả vẫn ok.
Ghi chú: `build_progress_data.py` log được ghi vào thư mục home, không vào gốc ổ đĩa.
Còn lại: lô A (29), cập nhật audit, P3, P4.

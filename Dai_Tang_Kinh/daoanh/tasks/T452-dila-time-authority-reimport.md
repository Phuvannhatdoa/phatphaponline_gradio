---
id: T452
title: Nạp lại DILA Time Authority từ SQL gốc (sửa ETL time_periods sai năm/tên/mất dòng)
status: deferred
created: 2026-10-22
updated: 2026-10-22
module: Data / DILA Time
done_when: Script ETL mới chạy --dry-run ra báo cáo đếm khớp nguồn (123 dynasty /
  692 emperor / 1.503 era / 117.428 month), năm tính đúng từ JD (mẫu month 3135 →
  năm 31), tên Hán lấy từ *_names; Admin duyệt rồi mới --apply additive; QA
  độc lập xác nhận; có --revert mất 0 dữ liệu.
---

## Vấn đề (đo 2026-10-22, chỉ đọc, `mode=ro`)

`time_periods` (117.429 dòng, toàn `source_origin='DILA'`) do
`scripts/etl_time_authority.py` nạp — sai ở 3 tầng:

| Loại | Nguồn | Trong DB | Lỗi |
|---|---|---|---|
| dynasty | 123 | 123 | `period_name_zh='chinese'` (là cột `type`), không năm |
| emperor | 692 | 570 | zh = số (dynasty_id), không năm, **mất 122** |
| era | 1.503 | 815 | zh = số (emperor_id), không năm, **mất 688** |
| lunar_month | 117.428 | 115.921 | năm sai, `era_name` = can chi, **mất 1.507** |

Nguyên nhân (đã kiểm chứng trên dòng id 3135):
- Gốc: `3135, year=7, month=2, '二', leap=0, era_id=1, first=1732452, last=1732480, '辛卯'`
- DB: `start_year=-2742, end_year=2001, era_name='辛卯'`
- Công thức `int((x-1721119)/365.25)+1970` **cộng thừa 1970** và **lệch cột**:
  start lấy `values[5]`=era_id=1 → -2742; end lấy `values[6]`=first → 31+1970=2001;
  `era_name` lấy `values[8]`=ganzhi. Đúng: năm 31 CN (建武 7, Hán Quang Vũ).
- Mất dòng: 4 loại dùng chung `id` TEXT = id số gốc + `INSERT OR IGNORE` ⇒ era/emperor/month
  trùng id với loại nạp trước bị bỏ im lặng.
- Script đọc đường dẫn cũ `data/dila_import/Authority-Databases/authority_time/SQL/`.

Không sửa tại chỗ được (trừ 1970 không phục hồi năm kết thúc / tên niên hiệu) ⇒ nạp lại từ gốc.

## Nguồn

`data/dila_import/authority_time.2012-02/authority_time/authority_time.sql`
(DDBC Time Authority, 10/2010, CC BY-SA 3.0; xem README.txt, SCHEMA.txt cùng thư mục).
Phân cấp `t_dynasty → t_emperor → t_era → t_month`; tên ở `t_*_names`
(`language_id` 1=zho-Hant, 9=jpn, 10=kor; `ranking` 0 = tên chính); ngày = Julian Day
(`first`/`last` của `t_month`); `status` S/P (P = proleptic). Không có tên Việt.
`t_period` có trong SCHEMA nhưng **không có trong dump**.

## Cách làm đề xuất (cần Admin duyệt trước khi ghi DB)

1. Script mới `scripts/t452_dila_time_reimport.py` với `--stats/--dry-run/--apply/--revert`.
2. **Additive**, không sửa/xoá dòng cũ (giữ ràng buộc T82 freeze như T22-LD2):
   id có tiền tố `dila_dyn:`, `dila_emp:`, `dila_era:`, `dila_mon:`, `source_origin='DILA_TA2010'`.
   Phương án thay thế: bảng riêng `dila_time_*` giữ nguyên phân cấp — Admin chọn.
3. JD → năm: chuyển JD đúng (Julian trước 1582-10-15, Gregorian sau); era/emperor/dynasty
   = min(first)/max(last) qua `t_month`, ghi kèm cờ có tháng `status='P'`.
4. `period_name_zh` = tên `language_id=1, ranking=0`; Nhật/Hàn giữ ở cột/bảng phụ.
5. `period_name_vi` để trống; nếu phiên âm thì gán ZQLOCAL=5, **không** gán cho DILA.
6. Backup `data/lineage.db` (snapshot) trước `--apply`.

## Ảnh hưởng cần kiểm

- `app.py` (~dòng 8440–8580): dynasty context dùng `time_periods`.
- `scripts/t97_parse_time_mentions.py`: tra `era_name LIKE ?`.
- `scripts/t22_ld2_dynasty_era_lookup.py` (SRC `t22_ld2_historical`) và `t251_ld2_era_gap.py`
  — đã làm lookup triều đại/niên hiệu thủ công; **DB hiện không có dòng nào của SRC này**
  (chưa apply hoặc đã revert) ⇒ cần Admin quyết quan hệ T22-LD2 ↔ T452.

## KHÔNG làm trong task này

- Không xoá/sửa 117.429 dòng cũ.
- Không gọi Gemini/AI để phiên âm.
- Không sửa `etl_time_authority.py` cũ (đánh dấu deprecated trong docstring là đủ).

## Câu hỏi cho Admin

1. Additive vào `time_periods` (tiền tố id) hay bảng riêng `dila_time_*`?
2. Có nạp `lunar_month` (117K dòng) không, hay chỉ dynasty/emperor/era?
3. T22-LD2 (lookup thủ công) giữ song song hay thay bằng dữ liệu DILA?

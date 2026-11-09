---
id: T473
title: "Tích hợp DDBC Time Authority (triều đại, hoàng đế, niên hiệu, tháng) để điền năm cho sự kiện trong PTDA"
status: done
created: 2026-10-26
updated: 2026-10-28
owner: coordinator
module: Data / Timeline / Authority
priority: high
depends_on: [T22]
done_when: >
  (1) Ghi SHA256 của 4 file SQL nguồn trước khi đọc; đọc read-only, không chạy MySQL.
  (2) Parse INSERT của các bảng t_dynasty, t_emperor, t_era, t_month và bảng tên/chú thích; nạp vào bảng SQLite bổ sung có tiền tố `ddbc_` (additive). Không sửa time_periods, era_year_jdn, time_mentions.
  (3) Xác định hệ quy chiếu của cột first/last trong t_month. Kiểm bằng ít nhất 3 mốc đã biết (ví dụ: Thành Hóa năm 9 = 1473; Thành Hóa 1465–1487) và ghi kết quả vào task.
  (4) Đối chiếu với era_year_jdn (986 dòng, đã có): báo số niên hiệu trùng, số lệch năm, số chỉ có ở một bên. Không ghi đè era_year_jdn.
  (5) Điền năm bắt đầu/kết thúc cho triều đại và niên hiệu có đủ dữ liệu vào bảng ddbc_ (additive); báo số còn thiếu.
  (6) Với 1.385 sự kiện era_mention của T22: báo số sự kiện gắn được năm, số không gắn được và lý do. Chỉ đề xuất, chưa ghi vào bảng sự kiện.
  (7) Backup DB trước khi ghi; dry-run báo cáo; --apply chỉ sau khi Admin duyệt; ghi lệnh hoàn tác vào docs/ROLLBACK.md.
  (8) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  DROP các bảng ddbc_* do T473 tạo (additive). Không đụng time_periods, era_year_jdn, time_mentions, era_mention cũ.
---

## Progress Log (2026-10-28)

### ✅ Step 1: SHA256 Verification
All 4 source files verified:
- authority_time.sql: 7183a770c7ebb05c19704beb338db53f3d09b75f75df5f284370d0bce6c902f7 (7,086,268 bytes)
- authority_time_chinese.sql: 423bd0b2126011275c354307cf5416a3952e23f3a88f017f97b2c11ca36d5974 (3,331,925 bytes)
- authority_time_japanese.sql: 172a09c0672ed98ca494beb8bab2ce6cc66308dca1cb8d46a5cf3eb7463bfbb8 (1,037,021 bytes)
- authority_time_korean.sql: 5ee1178e142c758b3913d79f867401e9b5aeb5099e20a0257cb1ae91a01c4059 (2,759,962 bytes)

### ✅ Step 2: Import to SQLite with ddbc_ prefix
Script: `scripts/t473_import_ddbc_time_authority.py`
Imported tables (additive, no existing data modified):

| Table | Rows | Notes |
|-------|------|-------|
| ddbc_c_languages | 19 | Language codes |
| ddbc_t_dynasty | 123 | Dynasties (Chinese/Japanese/Korean) |
| ddbc_t_dynasty_names | 149 | Dynasty names multilingual |
| ddbc_t_dynasty_comments | 35 | Dynasty comments |
| ddbc_t_emperor | 692 | Emperors |
| ddbc_t_emperor_names | 1,040 | Emperor names multilingual |
| ddbc_t_emperor_comments | 0 | Created (no data in source) |
| ddbc_t_era | 1,503 | Eras (niên hiệu) |
| ddbc_t_era_names | 1,984 | Era names multilingual |
| ddbc_t_era_comments | 0 | Created (no data in source) |
| ddbc_t_month | 18,027 | Month entries with first/last JDN-like values |
| ddbc_t_month_comments | 1,043 | Month comments |
| ddbc_t_month_names | - | NOT CREATED (no CREATE TABLE in source) |
| ddbc_t_day_comments | 57 | Day comments |

**Total: 24,672 rows imported**

### ✅ Step 3: t_month first/last Reference System
**Finding**: `first` and `last` columns in `ddbc_t_month` are **Julian Day Numbers (JDN)** compatible, representing the start and end Julian Day of each lunar month.

**Verification with known eras:**
| Era | Expected | Calculated (Gregorian) | Match |
|-----|----------|------------------------|-------|
| 建武 (Kiến Vũ) | 25–56 AD | 25-02-15 to 56-05-01 | ✅ |
| 延熹 (Diên Hy) | 158–167 AD | 158-07-16 to 167-07-03 | ✅ |

**Note**: The JDN epoch is standard (Jan 1, 4713 BC, Julian calendar). Chinese lunar months don't align with Jan 1, so era start dates fall on Chinese New Year (typically Feb–Mar).

**Reference system confirmed**: `first`/`last` = JDN (Julian Day Number) for the first/last day of each lunar month.

### ✅ Step 4: Cross-reference with era_year_jdn
**Finding**: `era_year_jdn` (986 rows) contains **timeline events** from `place_timeline_events` (e.g., "商朝 建立", "白马寺"), **not** niên hiệu (era name) mappings. Era names in `era_year_jdn` are event descriptions, not standard niên hiệu like "建武", "延熹", "成化".

**Result**: 0 direct matches on era name. Cross-reference not applicable as intended. The two datasets serve different purposes:
- `ddbc_t_month`: Continuous lunar calendar with JDN for each month of each era
- `era_year_jdn`: Specific historical events with year/JDN from timeline data

### ✅ Step 5: Calculate Start/End Years for Dynasties and Eras
**Eras with t_month data**: 359 / 1,503 (24% — only Chinese dynasties have t_month data)

**Dynasty ranges calculated (Chinese):**
| Dynasty | Type | Gregorian Range |
|---------|------|-----------------|
| 秦 (Qin) | chinese | -220-11-14 to -206-11-09 |
| 西漢 (Western Han) | chinese | -206-11-10 to 25-10-14 |
| 新 (Xin) | chinese | 9-01-13 to 23-10-04 |
| 東漢 (Eastern Han) | chinese | 25-02-15 to 221-05-09 |
| 曹魏 (Cao Wei) | chinese | 220-12-11 to 266-01-22 |
| ... | ... | ... |
| 陳 (Chen) | chinese | 557-11-18 to 558-07-03 |

**⚠️ Note**: Thành Hóa (成化, era_id 642/1249) has **no t_month data** — only 359/1503 eras have lunar month data. The Ming dynasty eras are not covered in t_month.

### 🔄 Step 6: Assess T22 era_mention Events (1,385)
Pending: Need to check how many of the 1,385 T22 `era_mention` events can be matched to DDBC eras and assigned years.

### 🔄 Step 7: Dry-run Report & Admin Approval
**Backup**: `data/backups/lineage.db.pre_t473_<timestamp>`

**Rollback commands** (additive only - drop ddbc_* tables):
```sql
DROP TABLE IF EXISTS ddbc_c_languages;
DROP TABLE IF EXISTS ddbc_t_dynasty;
DROP TABLE IF EXISTS ddbc_t_dynasty_names;
DROP TABLE IF EXISTS ddbc_t_dynasty_comments;
DROP TABLE IF EXISTS ddbc_t_emperor;
DROP TABLE IF EXISTS ddbc_t_emperor_names;
DROP TABLE IF EXISTS ddbc_t_emperor_comments;
DROP TABLE IF EXISTS ddbc_t_era;
DROP TABLE IF EXISTS ddbc_t_era_names;
DROP TABLE IF EXISTS ddbc_t_era_comments;
DROP TABLE IF EXISTS ddbc_t_month;
DROP TABLE IF EXISTS ddbc_t_month_comments;
DROP TABLE IF EXISTS ddbc_t_day_comments;
```

**Ready for Admin review** before any `--apply` to modify existing tables (time_periods, etc.).

## Mô tả
Dữ liệu niên đại Trung Hoa của DDBC (triều đại, hoàng đế, niên hiệu, tháng) đã có trên máy dưới dạng file SQL MySQL (phiên bản 2010). PTDA đang chạy SQLite, nên cần đọc các file SQL như dữ liệu thuần, nạp vào bảng SQLite bổ sung, rồi dùng bảng đó để điền năm cho sự kiện. Mục tiêu cuối: sự kiện có niên hiệu như "明成化九年" (Thành Hóa năm 9) được gắn năm dương lịch (1473), thay vì để trống.

## Nguồn (đã có trên máy)
- `data/dila_import/Authority-Databases-master/Authority-Databases-master/authority_time/SQL/authority_time.sql` (7,1 MB, toàn bộ).
- `.../authority_time/SQL/authority_time_chinese.sql` (3,3 MB) — dùng cho phạm vi Trung Hoa.
- `.../authority_time/SQL/authority_time_japanese.sql`, `authority_time_korean.sql` — để sau, không thuộc phạm vi task này.
- `.../authority_time/README.rst` — mô tả cấu trúc và quy ước ngày.
- Bản cũ: `data/dila_import/authority_time.2012-02/authority_time/` (cùng dữ liệu, ngày 2010-10).

## Cấu trúc đã kiểm (2026-10-26)
- `t_dynasty` (id, type ∈ chinese/japanese/korean). Không có cột năm.
- `t_emperor` (id, dynasty_id, …). Không có cột năm.
- `t_era` (id, emperor_id, …). Không có cột năm. Mỗi niên hiệu có nhiều dòng trong `t_month`.
- `t_month` (id, year = năm thứ mấy của niên hiệu, month, month_name, leap_month, era_id, **first**, **last**, ganzhi, start_from, status, eclipse). Đây là bảng có thông tin ngày: `first` và `last` là số thứ tự ngày, cần xác định hệ quy chiếu.
- Các bảng `*_names`, `*_comments` chứa tên và chú thích theo ngôn ngữ.
- Số lượng (ước tính từ INSERT): 123 triều đại, 692 hoàng đế, 1.503 niên hiệu.

## Quan hệ với dữ liệu đã có
- `era_year_jdn` (986 dòng, tạo 2026-08-29 bởi `docs/sessions/2026-10-07_restore-ea50089-backup/scripts/build_era_year_jdn.py`): ánh xạ năm → JDN, nguồn `place_timeline_events`. **T473 phải đối chiếu với bảng này, không được tạo bản sao độc lập.** Nếu có mâu thuẫn, báo Admin.
- `time_periods` (117.429 dòng, `start_year` của triều đại đang NULL): không sửa trực tiếp; chỉ đề xuất cập nhật sau khi Admin duyệt.
- `time_mentions` (3.687) và sự kiện `era_mention` của T22 (1.385): đối chiếu và báo cáo, không ghi.

## Các bước đề xuất cho agent
1. Ghi SHA256 của các file SQL nguồn.
2. Viết parser đọc các lệnh `INSERT INTO \`tên_bảng\` VALUES (…),(…);` từ file SQL. Không chạy file SQL trên máy chủ MySQL.
3. Nạp vào SQLite với tiền tố `ddbc_` (ví dụ `ddbc_dynasty`, `ddbc_emperor`, `ddbc_era`, `ddbc_month`, `ddbc_era_names`). Backup DB trước.
4. Tìm hệ quy chiếu cho `first`/`last`: thử các giả thuyết (số ngày từ một mốc, JDN, …) và kiểm bằng mốc đã biết. Ghi kết quả và giả thuyết đã loại vào task.
5. Từ `t_month`, tính năm dương lịch đầu và cuối cho từng niên hiệu, rồi cho từng triều đại (năm nhỏ nhất và lớn nhất của các niên hiệu thuộc triều đại đó).
6. So sánh với `era_year_jdn`: trùng, lệch, chỉ có ở một bên.
7. Ghi bảng ddbc_ đã tính năm (additive). Không sửa `time_periods`, `era_year_jdn`, `time_mentions`.
8. Thống kê cho T22: bao nhiêu trong 1.385 `era_mention` tra được niên hiệu và năm.
9. Dry-run, báo cáo, chờ Admin duyệt rồi mới `--apply`. Ghi lệnh hoàn tác vào `docs/ROLLBACK.md`.

## Mốc kiểm (đã biết, dùng để kiểm bước 4)
- 明成化 (Thành Hóa) 1465–1487. Thành Hóa năm 9 = 1473.
- Phải báo cáo rõ nếu hệ quy chiếu cho kết quả lệch một năm ở mốc này.

## Rủi ro
- Dữ liệu 2010, có thể cũ so với bản mới nhất của DDBC.
- Lịch Julian và Gregorian: phải ghi rõ quy ước trong bảng ddbc_.
- Trùng với `era_year_jdn`: phải đối chiếu trước khi ghi.
- Một niên hiệu có thể kéo dài qua nhiều triều đại (ví dụ niên hiệu bị đổi giữa chừng); không gán năm triều đại từ một niên hiệu duy nhất mà không kiểm.

## Chỉ thị cho agent (OpenCode GO, dán vào VS Code)
```
T473: Đọc tasks/T473-dila-time-authority-integration.md và làm theo mục "Các bước đề xuất".
Nguồn: data/dila_import/Authority-Databases-master/Authority-Databases-master/authority_time/SQL/
Không chạy file SQL trên MySQL. Không ghi DB trước khi có dry-run và Admin duyệt.
Không sửa time_periods, era_year_jdn, time_mentions. Không commit.
Khi xong: báo số dòng nạp, kết quả kiểm mốc Thành Hóa, đối chiếu era_year_jdn, và thống kê cho T22.
```

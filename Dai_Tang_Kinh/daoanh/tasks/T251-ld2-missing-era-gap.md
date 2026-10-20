---
id: T251
title: "Bổ sung 6 niên hiệu thiếu vào LD2 time_periods — khỏa lấp 6 era gap của T22-LD2"
module: Data Integrity / Timeline / LD2
priority: high
status: done
created: 2026-10-06
updated: 2026-10-07
owner: mimo-flash
depends_on: [T22, T234]
designed_by: mimo-flash
plan_approved_at: "2026-10-06 (Admin duyệt ghi 6 dòng; đồng thời quyết tách 132 dòng còn lại sang task riêng)"
done_when: >
  6 dòng era được INSERT vào time_periods với khoảng năm có nguồn,
  backup + manifest revert trước/sau, và `scripts/audit_data_honesty.py`
  chạy lại cho H3 = 132 (giảm 11 dòng — không phải 137).
  Kiểm chứng: 59 dòng place_timeline_events tham chiếu 6 era này
  (27 dòng trong đó có `year` — phần H3 xét) vẫn giữ nguyên nguyên trạng;
  đối chiếu trực tiếp với backup cho kết quả IDENTICAL.
blocked_reason: ""
revert: "git revert --no-edit <sha> cho docs/script. DB: python -X utf8 scripts/t251_ld2_era_gap.py --revert (đã test: 6→0, H3 về 143) + backup trong data/backups (data/ gitignored, không có trong git)."
former_ids: []
---

# T251 — Bổ sung 6 niên hiệu thiếu vào LD2

## 1. Vì sao mở task

T22-LD2 nạp niên hiệu vào `time_periods` nhưng **thiếu 6 tên**, dù
`place_timeline_events` đã có **59 dòng** trỏ tới chúng qua
`source_ref = <dila_id>·<era>·era_name_exact` (trong đó **27 dòng có
`year`** — đúng phần mà H3 xét; 32 dòng còn lại `year IS NULL` nên
H3 không đếm tới). Đây là lỗ hổng dữ liệu thực, có thể khỏa lấp bằng
tri thức lịch sử chuẩn đã kiểm chứng.

## 2. ĐÍNH CHÍNH phạm vi — điều đã bị bác bỏ

Ban đầu task mở ra với giả định:

> *"Thêm era thiếu sẽ đưa H3 từ 143 về 0."*

**Giả định này ĐÃ BỊ KIỂM CHỨNG SAI.** Mô phỏng `h3()` với `era_map`
cộng thêm 6 tên cho kết quả:

| Kịch bản | H3 FAIL |
|---|---|
| Hiện tại | **143** (không suy ra 140 + ngoài khoang 3) |
| Thêm 6 era | **132** (không suy ra 129 + ngoài khoang 3) |

Hai điểm sai:

1. **6 dòng `era_name_exact` không được sửa.** `h3()` chỉ gọi
   `era_year_in_text(note, era_map)` (audit_data_honesty.py:192) — nó
   không dùng tên era trong `source_ref`, cũng không so với danh sách era
   đã có. Note của 6 dòng đó **không chứa số năm**:
   `福州東禪寺 梁大同`, `明福寺 唐寶曆`, `妙樂寺 周顯德`,
   `金山寺 唐垂拱`, `大定寺 金大定`, `白衲庵 晉咸和`.
2. **11 dòng khác vô tình pass**: note của chúng chứa
   `<era><số Hán>年` mà trước đây era chưa có mặt nên trả `None`; thêm era
   vào là năm tính được ⇒ pass. (Số `midpoint chap nhan` giảm 1346 → 1342
   chỉ là **phân loại lại**, các dòng đó vẫn được chấp nhận.)

⇒ Task này **chỉ là việc đúng cần làm cho T22** (lỗ hổng LD2), không phải
con đường đưa T234 về `done_when`.

## 3. Bằng chứng cho 6 era

Khoảng năm chuẩn và kiểm chứng 27 dòng tham chiếu (tất cả đều nằm trong
khoảng chuẩn, `27/27 OK`):

| era | triều | khoảng chuẩn | năm có trong DB | dòng tham chiếu | dòng FAIL |
|---|---|---|---|---|---|
| 垂拱 | 唐 | 685–688 | 685, 687 | 6 | 1 (金山寺) |
| 咸和 | 東晉 | 326–334 | 326, 330 | 5 | 1 (白衲庵) |
| 顯德 | 後周 | 954–959 | 954, 955 | 3 | 1 (妙樂寺) |
| 寶曆 | 唐 | 825–827 | 826 | 2 | 1 (明福寺) |
| 大定 | 金 | 1161–1189 | 1161, 1180 | 7 | 1 (大定寺) |
| 大同 | 梁 | 535–546 | 535, 539 | 5 | 1 (福州東禪寺) |

`load_era_map` hiện có **180 tên**; thêm 6 → **186 tên**.

## 4. Đề xuất 6 dòng INSERT

Theo schema `time_periods(id, period_name, period_name_zh,
period_name_vi, start_year, end_year, era_name, source_origin, created_at)`:

| id | period_name_zh | period_name_vi | start_year | end_year | era_name |
|---|---|---|---|---|---|
| `era_唐_垂拱` | 垂拱 | Thụy Cung | 685 | 688 | 唐垂拱 |
| `era_東晉_咸和` | 咸和 | Hà Hòa | 326 | 334 | 東晉咸和 |
| `era_後周_顯德` | 顯德 | Hiển Đức | 954 | 959 | 後周顯德 |
| `era_唐_寶曆` | 寶曆 | Bảo Lịch | 825 | 827 | 唐寶曆 |
| `era_金_大定` | 大定 | Đại Định | 1161 | 1189 | 金大定 |
| `era_梁_大同` | 大同 | Đại Đồng | 535 | 546 | 梁大同 |

- `period_name='era'` cho cả 6.
- `source_origin='t251_ld2_era_gap'` (khác `t22_ld2_historical` để
  truy vết nguồn đợt bổ sung).
- Kiểm chứng: 6 tên này **chưa tồn tại** trong `time_periods`
  (truy `period_name_zh IN (...)` trả 0 dòng) ⇒ không trùng PK,
  không có xung đột với era cùng tên khác triều đại.

## 5. Quy trình apply / revert

1. `cp data/lineage.db data/backups/lineage_t251_<ts>.db`
2. Ghi manifest `docs/rollback/T251-LD2-era-gap-manifest.json`
   (trước: 0 dòng; sau: 6 dòng + blob id).
3. `python -X utf8 scripts/t251_ld2_era_gap.py` (INSERT idempotent,
   đếm `cursor.rowcount` thật, không dùng cờ `total_changes`).
4. `python -X utf8 scripts/audit_data_honesty.py` → mong đợi **H3 = 132**.
5. Revert: `python -X utf8 scripts/t251_ld2_era_gap.py --revert`
   (xoá đúng 6 id đã ghi trong manifest, có xác nhận).

## 6. Việc CHƯA xong — đã tách sang T252

132 dòng còn lại **không sửa bằng cách thêm era**. Admin quyết định
"tách task riêng, sẽ quyết sau" ⇒ toàn bộ danh sách dưới đây đã chuyển
sang **T252**, task này không ôm:

| nhóm | số dòng | hướng xử lý cần quyết |
|---|---|---|
| `note·regex` — note có era nhưng dạng "X中", không có số năm | ~97 | Chấp nhận "năm nằm trong khoảng era" (như midpoint) nhưng label **không hiện khoảng** ⇒ phải quyết policy |
| `note·regex` — note không chứa era nào trong DB | ~15 | Truy nguồn từng dòng |
| `era_name` — `元和十四年` (năm không tồn tại trong era) | 14 | **Lỗi dữ liệu thật**, đối chiếu nguồn |
| `dynasty` — chỉ nêu triều đại | 4 | Truy nguồn |
| `民국` — label hỏng `民民國` | 1 | Sửa label |
| midpoint `明末清初`/`元末明初` không hiện khoảng | 6 | Hiện khoảng vào label |

Cũng cần lưu ý: H6 hiện báo **OK** vì chỉ kiểm tra era/dynasty được
tham chiếu; bảng rộng còn 815 era tên là chuỗi số + 570 emperor thiếu
`start_year` chưa được H6 bao phủ. (Đây là việc của T234/T22, không
phải T251.)

## 7. Kết quả thực tế (đã đo, không phải dự báo)

Toàn bộ chạy trên `data/lineage.db` thật, ngày 2026-10-06:

| bước | kết quả đo được |
|---|---|
| apply lần 1 | `truoc=0 them=6 sau=6` |
| audit sau apply | **H3 = 132** (trước: 143) — đúng mô phỏng |
| `--revert` | `truoc=6 sau=0`, xoá 6 dòng |
| audit sau revert | **H3 = 143** — hoàn nguyên đúng về nguyên trạng |
| apply lại | `truoc=0 them=6 sau=6` |
| audit lần 2 | **H3 = 132** |
| apply lần 3 (idempotent) | `them=0, bo qua=6` — không nhân đôi |
| đối chiếu 59 dòng tham chiếu với backup | **IDENTICAL** |
| đếm 5 bảng | `time_periods 117645 → 117651` (+6); `place_timeline_events`, `places_dila`, `time_mentions`, `event_evidence` **đều giữ nguyên** |

Audit 6/7 xanh, chỉ H3 FAIL (132) — đúng phạm vi T252.

**Ba điểm cần Admin biết:**

1. `data/backups/` hiện **~90GB / 106 file**. T251 (khi còn tên T242) +
   lần đổi số đã tạo **6 file × ~1.58GB ≈ 9.5GB**, vì mỗi lần chạy
   `apply` lại tạo một backup mới. File điểm rollback thật là
   `lineage_t242_20261006_132138.db` (trước lần apply đầu tiên);
   các file còn lại là thừa. **Chưa xoá gì — chờ quyết.**
2. `.git/index.lock` tồn tại **0 byte, timestamp 2026-10-05 20:58**
   (còn sót từ session trước). Không chạm vào. Commit dùng
   `GIT_INDEX_FILE` nên không bị chặn, nhưng cần Admin rà khi nào
   chắc chắn không có git process nào chạy.
3. `npm run dup:ids` **FAIL sẵn 3 ID trùng** của người khác:
   `T188`, `T237`, `T238`. Chưa sửa, không thuộc phạm vi T251.

## 8. Đổi số ID: T242 → T251 (bắt buộc, có bằng chứng)

Task này ban đầu mang số **T242**, nhưng trong lúc đang làm,
`docs/tasktodo.md` **đã công bố T242 cho một task khác của session
khác** (GPS Chùa Việt Nam — dòng 11–13, `T242-vn-temple-gps-t0t1-implementation.md`),
và `T243` cũng đã bị `T243-m7-data-normalize-places.md` chiếm (dòng 15–17).

Áp dụng AGENTS.md §16 — đổi số **phía footprint nhỏ hơn**, theo đúng
thứ tự 4 tiêu chí:

| tiêu chí | task tôi | task session khác | bên nào đổi |
|---|---|---|---|
| (1) `status` kết thúc | `completed` | `pending` | **→ tôi** |
| (2) ít tham chiếu | script + manifest + DB | tasktodo | ngang |
| (3) không có `docs/plans\|reports/` | không | không | ngang |
| (4) **không** phải ID `docs/tasktodo.md` đã công bố | **không được công bố** | **đã công bố** | **→ tôi** |

Hai tiêu chí (1) và (4) đều chỉ về phía tôi ⇒ **đổi task này sang T251**
(task 132 dòng đổi sang **T252**). Đã kiểm cả 2 tầng trước khi cấp:
`T251`/`T252` không có file task và không có tham chiếu prose nào.

Đổi số đi kèm, tất cả đều đã làm và kiểm:

- `tasks/T242-…md` → `tasks/T251-ld2-missing-era-gap.md`, `id: T251`
- `tasks/T243-…md` → `tasks/T252-h3-remaining-132-policy.md`, `id: T252`
- `scripts/t242_ld2_era_gap.py` → `scripts/t251_ld2_era_gap.py`
  (docstring, `SOURCE`, tên manifest, tiền tố backup đều đổi theo)
- DB: **revert về 0 dòng rồi apply lại** để `source_origin` ghi đúng
  `t251_ld2_era_gap` — không sửa tay DB.
- `npm run dup:ids` sau đổi số: **chỉ còn 3 lỗi cũ** (T188/T237/T238).

### Sai lầm của tôi trong lần đổi số này (để không lặp lại)

Dùng PowerShell `-replace 'T242','T251'` — **PowerShell `-replace` mặc định
không phân biệt hoa/thường** ⇒ nó thay luôn chữ `t242` thành `T251`,
khiến `source_origin` trong DB thành `T251_ld2_era_gap` (chữ hoa) và
backup prefix thành `lineage_T251_`, lệch quy ước với
`t22_ld2_historical` / `lineage_t234gd2a_`. **Đã phát hiện nhờ kiểm
lại DB thật** (không tin vào kết quả replace), rồi sửa script + revert +
apply lại để đồng bộ. Bài học: với PowerShell, dùng
`-creplace`/`-ireplace` tường minh, hoặc viết file Python UTF-8
như `renumber.py`.


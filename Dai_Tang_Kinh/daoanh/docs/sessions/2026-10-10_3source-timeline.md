# Session 2026-10-10 — T270 3-source timeline (dharma_pair_sources + T44 destruction events)

**Trạng thái: CHƯA ĐÁNH DONE.** Chờ Admin rà `dharma_pair_sources.admin_quyet_dinh` và xác nhận.

## BƯỚC 0 — Backup

- `data/backups/lineage.T270-3source-20261010-173041.db` (1.707.802.624 bytes)
- `PRAGMA quick_check` → `ok`

## BƯỚC 1 — Bảng `dharma_pair_sources` (additive)

Tạo bảng mới, PK `(teacher_id, disciple_id)`. Điền cho population **DILA active+verified**
(`lineage_edge_assertions WHERE source_code='DILA' AND status='active' AND mapping_verified=1`
= 46.004 dòng, **23.013** cặp distinct — mỗi cặp bị trùng `edge_key` đúng 2 lần trong DB gốc,
đã kiểm tay 5 cặp mẫu: giá trị `label`/`ttl_confirmed` giống nhau 100% giữa 2 bản trùng nên
PK-dedup không làm mất thông tin, chỉ mất số dòng trùng — đây là lỗi dữ liệu có sẵn đã ghi
nhận ở BUG-027, ngoài phạm vi sửa ở đây).

Nguồn từng cột:

| Cột | Nguồn | Ghi chú |
|---|---|---|
| `marcus_status` | `marcus_networks` theo cặp `(teacher_id, student_id)`: `noi_phap` nếu có `ref LIKE '%法嗣%'`, `quan_he_only` nếu có cạnh nhưng không `法嗣`, `khong_co` nếu không có cạnh | tính trực tiếp từ bảng, không qua `dharma_edges.json` |
| `marcus_ref` | ref đầu tiên khớp (ưu tiên ref chứa `法嗣` nếu có) | |
| `dila_status` | luôn `active_verified` | đúng theo population đã lọc |
| `dila_edge_id` | `lineage_edge_assertions.id` | khi 1 cặp có 2 `id` trùng, giữ `id` xử lý sau cùng (giá trị các cột khác giống nhau) |
| `ttl_status` | `data/dharma_edges.json` field `ttl_confirmed` → `hasTeacher` (true) / `khong_co` (false) | **GIỚI HẠN:** không tách được `pha_tu_text`/`tham_hoc_text` — xem mục "Chưa chắc" |
| `ttl_file` | `ttl_match.evidence_file` khi `ttl_confirmed=true` | |
| `ttl_line` | NULL toàn bộ | nguồn hiện có không mang số dòng trong TTL |
| `label_auto` | `data/dharma_edges.json` field `label` | `tham_hoc`/`mo_ho`/`noi_phap`/`khong_ghep_duoc` |
| `admin_quyet_dinh`, `admin_nguon`, `admin_ghi_chu`, `admin_at` | NULL toàn bộ | chờ Admin |

**Số liệu thật (đếm trên bảng sau khi ghi, 23.013 dòng):**

- `marcus_status`: `khong_co`=11.849, `quan_he_only`=8.431, `noi_phap`=2.733
- `ttl_status`: `khong_co`=22.998, `hasTeacher`=15
- `label_auto`: `tham_hoc`=12.109, `mo_ho`=10.883, `noi_phap`=15, `khong_ghep_duoc`=6
- `dila_status`: `active_verified`=23.013 (100%)

## BƯỚC 2 — `place_timeline_events`

### (a) 44 dòng mới từ `2026-10-10_T44_destruction_preview_v2.tsv`

Điều kiện lọc đúng theo chỉ định: `quy_tac_nam='cung_menh_de' AND can_xem='false'`.

**Lệch số liệu cần báo:** chỉ định mô tả "102 sự kiện" nhưng 102 là tổng số dòng
`quy_tac_nam='cung_menh_de'` **không lọc `can_xem`**. Trong 102 dòng đó, 44 có
`can_xem='false'` và 58 có `can_xem='true'`. Áp đúng câu "Các dòng can_xem=true KHÔNG ghi"
trong chính chỉ định → chỉ ghi **44** dòng (25 `destroyed` + 19 `abandoned`), không tự ý
ghi 58 dòng còn lại dù chúng cũng thuộc `cung_menh_de`.

- Không dòng nào trùng `(dila_id, year, event_type, source='t44_destruction_v2')` trước ghi.
- Ghi: `event_type`, `year` = cột tương ứng; `label_zh = clause_zh`; `source='t44_destruction_v2'`;
  `source_ref = source_note`; `confidence='cung_menh_de'`.
- 1 transaction duy nhất (executemany).

### (b) 341 dòng `ĐỀ XUẤT DUYỆT` trong `2026-10-10_T44_exact_suggestions.tsv`

Kiểm (không ghi): **341/341** đã tồn tại trong `place_timeline_events` dạng `event_type='founding'`
khớp theo `(dila_id, year)` — ghi từ trước (T44 2026-10-09 batch 596 dòng). Đúng như chỉ định,
KHÔNG ghi lại.

### Verify sau ghi

| | Trước | Sau | Delta |
|---|---|---|---|
| Tổng `place_timeline_events` | 4.284 | **4.328** | +44 |
| `destroyed` / `t44_destruction_v2` | 0 | 25 | +25 |
| `abandoned` / `t44_destruction_v2` | 0 | 19 | +19 |
| Mọi `event_type`/`source` khác | không đổi | không đổi | 0 |

Không dòng cũ nào bị sửa (so sánh phân bố `event_type,source` trước/sau — khớp tuyệt đối
trừ 2 dòng mới `t44_destruction_v2`).

## Revert

- `data/backups/lineage.T270-3source-20261010-173041.db` — khôi phục toàn bộ khi DB đang dừng.
- Hoặc chạy ngược: `DELETE FROM place_timeline_events WHERE source='t44_destruction_v2';`
  `DROP TABLE dharma_pair_sources;` (nếu cần — bảng mới, chưa ai khác đọc).
- Đã ghi vào `docs/ROLLBACK.md`.

## Chưa chắc / giới hạn (không claim đạt)

1. **`ttl_status` chỉ có 2 giá trị thật (`hasTeacher`/`khong_co`)**, không có `pha_tu_text`/
   `tham_hoc_text` như schema yêu cầu. Nguồn `data/ttl_dharma_index.json` chỉ gắn cờ
   `dharma_flag` (có từ khóa pháp tự/đắc pháp) ở cấp **file TTL**, còn `data/dharma_edges.json`
   (nguồn join theo DILA ID) chỉ giữ `ttl_confirmed`/`ttl_match.evidence_kind`
   (`hasTeacher_in_disciple_file` / `hasDisciple_listing_only`) — không giữ lại cờ keyword
   theo từng cặp cụ thể. Dò lại text TTL theo từng cặp để tách 2 nhãn này là việc mới,
   ngoài phạm vi BƯỚC 1 hiện tại, cần Admin xác nhận có cần làm thêm không.
2. **`ttl_line` luôn NULL** — không có nguồn số dòng nào trong `ttl_dharma_index.json`/
   `dharma_edges.json`.
3. **23.013 ≠ số cặp admin có thể mong đợi nếu tính theo dòng edge (46.004)** — do PK dedup
   theo `(teacher_id, disciple_id)`. Đã kiểm 5 mẫu trùng, giá trị giống nhau 100%, nên dedup
   an toàn về mặt nội dung, nhưng nếu Admin muốn giữ cả thông tin `edge_key` trùng (ví dụ để
   dọn dữ liệu trùng ở BUG-027) thì cần bảng khác không có PK này.
4. **44 ≠ 102** như đã giải thích ở BƯỚC 2(a) — cần Admin xác nhận đây là đúng ý định hay
   Admin thực ra muốn ghi cả 102 dòng (bỏ điều kiện `can_xem`). Hiện tại đã làm theo đúng
   câu chữ chỉ định ("Các dòng can_xem=true KHÔNG ghi"), không tự suy diễn thêm.

## Scripts đã chạy (scratchpad, không phải code chính thức của repo)

- BƯỚC 1: tạo `dharma_pair_sources` + điền dữ liệu.
- BƯỚC 2a: lọc + ghi 44 dòng `place_timeline_events`.

Cả hai script nằm trong scratchpad của session, không commit vào repo (theo yêu cầu không git).

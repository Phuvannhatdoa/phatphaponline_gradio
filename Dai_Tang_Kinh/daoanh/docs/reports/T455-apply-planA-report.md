# T455 — Báo cáo APPLY phương án A (chuẩn hoá tên người)

> Ngày: **2026-10-30** · Batch: `T455-planA-20261030` · Admin duyệt phương án **A**
> Backup trước khi ghi: `data/backups/lineage_t455_20261030_144710.db` (1.824.460.800 B)

---

## 1. Phương án A là gì

Theo báo cáo phân tích `docs/reports/T455-analysis-794-mismatch.md`:

| Lô | Số | Xử lý |
|---|---|---|
| **A** | 24 | ZQ hỏng rõ (để tên Anh / sót chữ Hán hiến) → **sửa** |
| **B** | 534 | Khác *quy ước đọc cả từ*, không phải lỗi kỹ thuật → **giữ nguyên**, ghi chú alias trong bảng lịch sử |
| **C** | 236 | ZQ thiếu/sai 1 chữ (thiếu tiền tố `釋`) → **sửa** theo Cloud (charmap dự án xác nhận 188/236) |

## 2. Kết quả apply

| Hạng mục | Trước | Sau |
|---|---|---|
| Bảng lịch sử `people_name_vi_history` | **không tồn tại** | **794 dòng** (bảng mới, additive) |
| `people.name_vi` còn chữ Hán | 422 | **405** (−17, đúng bằng số chữ Hán đã sửa) |
| `people.name_vi` được UPDATE | — | **258 dòng** |
| Lô B bị đổi (phải = 0) | — | **0** ✅ |
| `people.name_zh` | — | **không đổi** ✅ |
| `people.source_id` | 48.673 giá trị `1` | **không đổi** ✅ |

### Chi tiết theo hành động (bảng `people_name_vi_history`)
| `action` | Số dòng | Ý nghĩa |
|---|---|---|
| `updated` | **258** | đã sửa `name_vi` (lô A 22 + lô C 236) |
| `kept_alias` | **534** | lô B — giữ nguyên theo ZQ, ghi chú alias (Cloud) để sau này tra |
| `unchanged` | **1** | `A000529` — Cloud trùng ZQ, không cần đổi |
| `skipped_kept` | **1** | `A001428` — xem §4 |

Theo lô: **A = 24 · B = 534 · C = 236** (tổng 794)

## 3. Bảng lịch sử mới (additive)

```sql
CREATE TABLE people_name_vi_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  person_id TEXT NOT NULL,
  name_vi_old TEXT,
  name_vi_new TEXT,
  lot TEXT,            -- A / B / C
  action TEXT,         -- updated | kept_alias | unchanged | skipped_kept
  reason TEXT,
  source_id INTEGER DEFAULT 5,   -- ZQLOCAL (tên Việt)
  batch_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_pnvh_person ON people_name_vi_history(person_id);
CREATE INDEX idx_pnvh_batch  ON people_name_vi_history(batch_id);
```

→ Giá trị cũ **không mất**: mọi tên cũ nằm ở `name_vi_old`. Đây là cơ sở để revert và để mở task riêng cho lô B sau này.

## 4. 2 dòng đặc biệt

### `A000142` — sửa tay (1 dòng)
- Hán: `天頙` (DB: `真靜天頙`) · ZQ: `Chân Tĩnh Thiên 頙` · Cloud: `Thiên 頙` (còn sót Hán + mất "Chân Tĩnh")
- Chữ `頙` **không có** trong bảng đọc (`hanviet_char_map` 11.300 chữ) → không kiểm chứng bằng máy
- → Sửa tay: **`Chân Tĩnh Thiên Trác`** (giữ phần ZQ đúng + đọc `頙` = Trác)

### `A001428` — bỏ qua (1 dòng)
- Hán: `彌勒` · DB hiện tại: **`Di Lặc Bồ Tát`** (đúng chính tả, đủ "Bồ Tát") · CSV (đo 2026-10-22): `Di Lắc Bồ Tát` (sai dấu) · Cloud: `Di Lặc` (mất "Bồ Tát")
- UPDATE dùng điều kiện `WHERE id = ? AND name_vi = <CSV>` ⇒ **tự động bỏ qua**, không ghi đè
- Lịch sử ghi `action='skipped_kept'`, `name_vi_new = 'Di Lặc Bồ Tát'` (giá trị thực tế)

## 5. Kiểm chứng chất lượng (trước khi apply)

22 dòng lô A được kiểm chứng từng chữ với bảng đọc `hanviet_char_map`:

| Kết quả | Số dòng | Ý nghĩa |
|---|---|---|
| ✓ Mọi chữ khớp bảng đọc | 4 | chắc chắn |
| ⚠ Chữ hiến **không có** trong bảng đọc | 18 | không kiểm chứng bằng máy → tin Cloud (nguồn duy nhất có) |
| ⚠ Charmap khác Cloud | 3 | **Cloud đúng** — charmap đọc theo *nghĩa thường*: `瑊` charmap=Giam vs Cloud=Kiêm · `延` charmap=Duyên vs Cloud=Diên · `希` charmap=Hơi vs Cloud=Hi |

Các chữ hiến không có bảng đọc: `昰 竑 玘 霰 丏 哌 鸖 晙 屾 僼 蜞 頔 璹 橖 涑` — đều là chữ tên riêng hiếm, 19/24 dòng lô A có `so_lan ≤ 4`.

## 6. Quy tắc bất biến đã giữ

| Quy tắc | Kiểm chứng |
|---|---|
| Tên Việt luôn `source_id = 5` (ZQLOCAL), **không** gán tên Việt cho DILA (`source_id=1`) | `people.source_id` không đổi (48.673 giá trị `1`) ✅ |
| **Không** sửa `people.name_zh` | không có UPDATE nào chạm `name_zh` ✅ |
| Additive — giữ giá trị cũ | 794 dòng trong `people_name_vi_history` ✅ |
| Backup trước khi ghi | `lineage_t455_20261030_144710.db` ✅ |
| `entity_claims` (NAME, source_id=5) | **0 claim** cho 794 person này → không cần cập nhật ✅ |
| Trigger trên `people` | không có ✅ |

## 7. Việc còn lại (chưa làm)

| # | Việc | Ghi chú |
|---|---|---|
| 1 | **405 tên còn sót chữ Hán** | Đo được 422 trước apply → 405 sau. Đây là nhóm "532 tên sót Hán" trong task T455 — **không** nằm trong danh sách 794 (vì không có bản Cloud để đối chiếu). Cần task riêng. |
| 2 | **534 alias lô B** | Đã ghi trong `people_name_vi_history` (`action='kept_alias'`). Mở task riêng để tra từ điển theo `so_lan` — **không** chặn T456 |
| 3 | **T456 — autocomplete HOME** | Chưa bắt đầu; phụ thuộc T453 ✅ / T416 / T450 |

## 8. Lệnh kiểm tra lại

```bash
# verify sau apply
python -X utf8 scripts/t455_verify_apply.py

# trạng thái DB tổng quan
python -X utf8 scripts/t455_check_state.py

# đề xuất (dry-run lại, không ghi)
python -X utf8 scripts/t455_apply_planA.py --dry-run

# REVERT (khôi phục 258 tên cũ + xoá 794 dòng lịch sử)
python -X utf8 scripts/t455_apply_planA.py --revert
```

## 9. Revert

```bash
python -X utf8 scripts/t455_apply_planA.py --revert
```
- Khôi phục `people.name_vi` về `name_vi_old` cho 258 dòng `action='updated'`
- Xoá 794 dòng `people_name_vi_history` của batch `T455-planA-20261030`
- **Không** mất dữ liệu cũ (bảng lịch sử bị xoá sau khi đã dùng để khôi phục)
- Hoặc khôi phục nguyên trạng từ backup: `data/backups/lineage_t455_20261030_144710.db`

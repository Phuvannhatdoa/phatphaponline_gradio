# Rollback manifests — T234 GĐ2

> Ngày tạo: 2026-10-05 · Task: `tasks/T234-tu-hien-doi-xuat-ban-do-dai-tang.md`

## Vì sao file này tồn tại

`data/` bị `.gitignore` (dòng 3), và `.gitignore` còn chặn `*.json` (dòng 6).
DB backup (`data/backups/*.db`) là file nhị phân lớn — **không** commit được.

Nhưng nếu manifest revert không được commit thì một bản clone mới **không
rollback được DB**. Vậy nên manifest được sao chép ra `docs/rollback/` để
đưa vào git. File ở đây là **bản sao**; `data/*.json` mới là file script
đọc khi chạy.

Các file này được đưa vào index bằng `git update-index --cacheinfo` (bỏ qua
`.gitignore`). Một khi đã được track, `.gitignore` **không còn áp dụng** cho
chúng, nên các lần sửa sau vẫn `git add` bình thường.

## Danh sách

| File | Script sinh ra | Phạm vi |
|------|----------------|---------|
| `T234-GD2a-manifest.json` | `scripts/t234_gd2a_apply.py` | M1 + M1b + M2 |
| `T234-GD2b-manifest.json` | `scripts/t234_gd2b_h2_authority.py` | M5 (authority) |
| `T251-LD2-era-gap-manifest.json` | `scripts/t251_ld2_era_gap.py` | 6 niên hiệu thiếu LD2 (H3 143→132) |

## Cách revert

```bash
cd Dai_Tang_Kinh/daoanh

# 1. Sao lưu DB hiện tại trước (không bắt buộc nhưng nên làm)
cp data/lineage.db data/backups/lineage_before_revert_$(date +%Y%m%d_%H%M%S).db

# 2. Revert
python -X utf8 scripts/t234_gd2a_apply.py --revert
python -X utf8 scripts/t234_gd2b_h2_authority.py --revert
python -X utf8 scripts/t251_ld2_era_gap.py --revert   # 6 era → 0 dòng, H3 về 143

# 3. Kiểm chứng
python -X utf8 scripts/audit_data_honesty.py --h2
python -X utf8 scripts/audit_data_honesty.py          # H3 = 143 nếu đã revert T251
```

`--revert` chỉ đọc `data/t234_gd2*_log.json`. Nếu `data/` bị mất, copy lại
từ `docs/rollback/` về `data/` (giữ nguyên tên file) rồi chạy.

## Backup DB gốc

| Bản | Đường dẫn |
|-----|-----------|
| Trước GĐ2a | `data/backups/lineage_t234gd2a_20261005_155321.db` |
| Trước GĐ2b/M5 | `data/backups/lineage_t234gd2b_20261005_215629.db` |
| Trước T251 (6 era) | `data/backups/lineage_t242_20261006_132138.db` |

Ba file này **không có trong git**. Nếu mất, phải dựng lại từ ETL.

> Đổi tên task T242 → T251 (do trùng ID với session GIS) khiến backup
> từ lúc đầu vẫn mang tiền tố `lineage_t242_`. File **chính** để rollback
> T251 là bản đó; các `lineage_t251_*.db` là backup của các lần
> apply/revert–apply **sau** đổi số, dùng để đối chiếu, không phải điểm
> rollback đúng.

## Revert T251 — ngữ nghĩa (đã đọc code xác nhận)

`--revert` (`hoan_nguyen()`) xoá **theo danh sách `id_da_them`** trong
manifest, không phân biệt dòng do script INSERT hay nguồn khác đặt cùng
tên id. In `truoc/sau` và `da xoa N dong`.

| điều kiện | hành vi |
|---|---|
| manifest không tồn tại | `exit 1` (không im lặng bỏ qua) |
| sau khi xoá vẫn `sau != 0` | `exit 1` (còn sót dòng) |
| `truoc=0, sau=0` (đã sạch sẵn) | **`exit 0`** — báo `da xoa 0 dong`, không phải lỗi |
| `apply` nhưng `sau != 6` | `exit 1` |

⚠️ Nghịch lý cần nhớ: nếu DB đã sạch mà revert, script **thành công**
thay vì báo lỗi — vậy muốn chắc chắn revert có hiệu lực, phải kiểm
`audit` cho `H3 = 143`, không chỉ nhìn exit code.

`apply` là idempotent: chạy lại chỉ `them=0, bo qua=6`, không nhân đôi.

## Cảnh báo: log GĐ2a từng bị ghi đè

`scripts/t234_gd2a_apply.py` trước đây ghi đè manifest mỗi lần chạy. Vì
`--apply --only-m1m2` là idempotent (insert 0 dòng, sửa 0 dòng), chạy lại sẽ
ghi `{"m1_evidence": [], "m2_restore": []}` — xoá sạch 1437 event id và 11
giá trị gốc. `--revert` sau đó **im lặng không làm gì**.

Đã sửa thành merge (`setdefault` giữ giá trị gốc cũ, `union` event id) vào
commit `fix(T234-GD2a): ghi merge manifest`. Đã kiểm chứng: chạy lại idempotent
vẫn giữ `m1=1437, m2=11`.

> Nếu bạn thấy log báo `[MERGE]` thì đã có dữ liệu cũ — an toàn.
> Nếu báo `[MOI]` thì đây là lần chạy đầu, chưa có gì để merge.

## Nội dung manifest

### `T234-GD2a-manifest.json`

```json
{
  "run_at":       "...",         // lần chạy gần nhất
  "first_run_at": "...",         // lần chạy đầu (giữ nguyên)
  "backup":       "...db",       // backup TRƯỚC GĐ2a (điểm rollback đúng)
  "backup_latest":"...db",       // backup của lần chạy gần nhất
  "m1_evidence":  [ "evt_id", ... ],   // 1437 event_evidence đã INSERT → xoá hết
  "m2_restore":   [ {id, event_type, year, year_end, confidence}, ... ], // 11 dòng
  "m3_restore":   []             // đã gộp vào m2_restore
}
```

### `T234-GD2b-manifest.json`

```json
{
  "run_at":  "...",
  "backup":  "...db",
  "restore": [ [ [mention_id, id_cu, raw_time_zh, ly_do, year], gia_tri_cu ], ... ]
}
```

96 dòng `time_mentions` có `time_authority_id = 'reign_era_dict'`.
Trong đó **57** được gán ID thật, **39** đặt `NULL` vì LD2 thiếu era.
Giá trị cũ (`reign_era_dict`) được lưu để revert.

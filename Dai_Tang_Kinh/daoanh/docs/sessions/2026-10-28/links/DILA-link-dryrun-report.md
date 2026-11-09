# Dry-run: Nạp liên kết DILA còn thiếu vào DB (T481)

**Ngày:** 2026-10-28
**Agent:** Tích Hợp
**Status:** dry_run_done — CHƯA GHI DB, chờ Admin duyệt `--apply`
**Nguồn gốc:** `docs/sessions/2026-10-28/DILA-resource-inventory.md`
**Sidecar quét:** `data/dila_import/extracted/A*.json` — 49.487 file (toàn bộ, không sample)
**DB đối chiếu:** `data/lineage.db` (mở `mode=ro`, không ghi)
**Script dry-run** (chỉ đọc, không có lệnh INSERT/UPDATE/CREATE nào): lưu tạm tại scratchpad
của session, chưa đưa vào repo — sẽ đặt tên `scripts/etl_dila_links.py` khi Admin duyệt `--apply`
(script thật sẽ được viết lúc đó, không phải bây giờ).

## Phát hiện quan trọng làm thay đổi giả định ban đầu

1. **`places_of_origin` và `active_at_places` là TÊN ĐỊA DANH chữ Hán** (ví dụ `蘇州`,
   `夾門關`, `吳郡城報恩寺`), **không phải place ID**. Vì vậy không thể đối chiếu bằng ID
   như kế hoạch gốc giả định — phải match theo `places_dila.name_zh` / `places_dila.name`
   (so khớp chuỗi chính xác, không fuzzy).
2. **`vn_person_places` và `vn_person_works` dùng namespace hoàn toàn khác** — `person_id`
   là slug tiếng Việt kiểu Truyền Thừa Thiền Tông (`bach_van_thu_doan`, `TS-Bach-Van-Thu-Doan`),
   **không phải DILA A-id**. Hai bảng này thuộc nguồn dữ liệu khác, không cùng không gian khóa
   với sidecar DILA → xác nhận quyết định tạo bảng additive mới là đúng, không thể "mở rộng
   cơ chế hiện có".
3. **`canon_catalog.cbeta_id` và `cbeta_catalog_vn.sigla` đều NULL 100%** (3.122/3.122 dòng
   mỗi bảng). Cột khóa CBETA thật của `canon_catalog` là `cb_cbeta` (số thuần, không có chữ
   T/X/B — ví dụ `"2210"` cho T2210). Vì vậy bảng khớp chính cho mục C là
   `dila_catalog_works.cbeta_id` (có 5.747/5.747 dòng, định dạng `T0763`, `X0652`, `JB486`,
   `B0117`, `P1615`, `A1504`...).

## A. places_of_origin → quan hệ người–địa danh

| Chỉ số | Giá trị |
|---|---|
| Người có dữ liệu | 12.188 |
| Tổng dòng (người × địa danh) | 12.188 (1 địa danh/người, không có người nào ghi >1) |
| Khớp qua `places_dila.name_zh` | 10.785 |
| Khớp qua `places_dila.name` | 1.366 |
| **Không khớp** | 37 (0,3%) |
| **Tỉ lệ khớp** | **99,7%** |
| Trùng tên trong cùng 1 người | 0 |

- 37 dòng không khớp hầu hết là địa danh Ấn Độ/Tây Vực cổ (`健馱邏國`, `摩揭陀國`, `烏仗那國`,
  `迦濕彌羅國`, `舍衛國`...) — `places_dila` có vẻ thiếu các địa danh ngoài Trung Hoa này, hoặc
  tên ghi khác dạng. Không chặn việc nạp — chỉ 37/12.188 dòng.
- **Rủi ro chính — nhập nhằng 1 tên → nhiều ID:** rất nhiều tên khớp ra 2–3 `PL` ID khác nhau
  (ví dụ `鄞縣` → 3 ID, `臨海` → 3 ID, `河南府` → 3 ID, `泰州` → 3 ID). `places_dila` có nhiều
  dòng trùng tên khác khu vực/thời kỳ (quận huyện cùng tên qua các triều đại). Matching theo
  tên không tự phân giải được "cái nào đúng" — đề xuất lưu **toàn bộ candidate ID** kèm cột
  `is_ambiguous` (1 khi >1 ứng viên), để không mất thông tin nhưng không giả vờ chắc chắn.
- Mẫu khớp/không khớp: xem phần "samples_matched"/"samples_unmatched" mục A trong JSON dry-run
  (lưu kèm session, 20 dòng mỗi loại).

**Đề xuất bảng additive:** `dila_person_place_link`
```sql
CREATE TABLE IF NOT EXISTS dila_person_place_link (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dila_id TEXT NOT NULL,              -- people.id (A-id)
  place_id TEXT NOT NULL,             -- places_dila.id (PL-id)
  role TEXT NOT NULL,                 -- 'origin' | 'active'
  raw_name_zh TEXT NOT NULL,          -- chuỗi gốc trong sidecar
  match_method TEXT NOT NULL,        -- 'name_zh' | 'name'
  is_ambiguous INTEGER NOT NULL DEFAULT 0,  -- 1 nếu raw_name_zh khớp >1 place_id
  source TEXT NOT NULL,              -- 'DILA_Person_Authority_sidecar'
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(dila_id, place_id, role, source)
);
```

## B. active_at_places → quan hệ người–địa danh (nơi hoạt động)

| Chỉ số | Giá trị |
|---|---|
| Người có dữ liệu | 1.227 |
| Tổng dòng | 3.436 (trung bình 2,8 địa danh/người) |
| Khớp qua `name_zh` | 381 |
| Khớp qua `name` | 76 |
| **Không khớp** | 2.979 (86,7%) |
| **Tỉ lệ khớp** | **13,3%** |

- **Rủi ro cao nhất trong cả 6 mục.** 87% không khớp. Nguyên nhân: `active_at_places` chủ
  yếu ghi **tên chùa/tự viện cụ thể** (`圓覺寺`, `淨智寺`, `鄧尉山聖恩寺`, `杭州天竺靈山寺`...),
  trong khi `places_dila` (59.167 dòng) nghiêng về địa danh hành chính/địa lý (tỉnh, huyện,
  núi, nước), không phải danh bạ chùa. 381+76=457 khớp được là các chùa lớn/nổi tiếng tình cờ
  có trong `places_dila`.
- **Đề xuất:** vẫn nạp phần khớp (13,3% = 457 dòng) vào cùng bảng `dila_person_place_link`
  (`role='active'`), nhưng **không nên coi 87% còn lại là lỗi ETL** — đây là giới hạn thật của
  nguồn `places_dila` (thiếu danh bạ tự viện). Ghi rõ trong done_when: không kỳ vọng tỉ lệ khớp
  B cao như A.
- Dùng cùng schema `dila_person_place_link` ở trên, `role='active'`.

## C. works_in_tripitaka → quan hệ người–tác phẩm

| Chỉ số | Giá trị |
|---|---|
| Người có dữ liệu | 3.035 |
| Tổng dòng | 10.299 |
| Trích được mã trong `(...)` cuối chuỗi | 5.596 (54,3%) |
| Không trích được mã (văn bản tự do, không có canon code) | 4.703 (45,7%) |
| Khớp `dila_catalog_works.cbeta_id` | **5.596 / 5.596 trích được = 100%** |
| Khớp `canon_catalog.cb_cbeta` (dự phòng) | 0 (không cần, vì khớp hết ở `dila_catalog_works`) |
| Không khớp bảng nào | 0 |

- Rất sạch cho phần có mã: mọi mã trích được (`T0763`, `X0652`, `JB486`, `B0117`, `P1615`,
  `A1504`...) đều có trong `dila_catalog_works.cbeta_id` (5.747 dòng).
- 4.703 dòng không có mã `(...)` là mô tả văn bản thất lạc/chưa có trong Đại Tạng điện tử (ví dụ
  `《三峰燈史》八卷（佚失...）`, `《仁叟和尚語錄》十卷...（西園寺藏刻本...）`) — **đúng bản chất,
  không phải lỗi regex**: đây là tác phẩm KHÔNG nằm trong tripitaka số hoá, nên không thể và
  không nên gán `work_id`. Đề xuất lưu các dòng này với `work_ref=NULL`, `raw_text` đầy đủ, để
  không mất thông tin nhưng không giả tạo liên kết.

**Đề xuất bảng additive:** `dila_person_work_link`
```sql
CREATE TABLE IF NOT EXISTS dila_person_work_link (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dila_id TEXT NOT NULL,                  -- people.id
  work_cbeta_id TEXT,                     -- dila_catalog_works.cbeta_id (NULL nếu không trích được mã)
  raw_text TEXT NOT NULL,                 -- chuỗi gốc trong sidecar (giữ nguyên, kể cả khi NULL work_cbeta_id)
  source TEXT NOT NULL,                   -- 'DILA_Person_Authority_sidecar'
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(dila_id, raw_text, source)
);
```
(UNIQUE theo `raw_text` thay vì `work_cbeta_id` vì ~46% dòng có `work_cbeta_id` NULL — không
thể dùng NULL trong khóa duy nhất một cách an toàn trên SQLite nếu muốn chặn trùng dòng y
hệt.)

## D. wikidata_qid → `dila_person_wikidata`

| Chỉ số | Giá trị |
|---|---|
| Người có `wikidata_qid` | 2.005 |
| Trùng với QID đã gán cho ĐỊA DANH trong `geo_cross_ref` (kiểm tra an toàn) | 0 |

- Không có bảng DB hiện tại nào gán QID cho PERSON — `geo_cross_ref` chỉ gán QID cho PLACE
  (`PL...` id). Kiểm tra 0 trùng QID giữa người và địa danh (sanity check) — an toàn để tạo
  bảng mới riêng, không đụng `geo_cross_ref`.

**Đề xuất bảng additive:** `dila_person_wikidata`
```sql
CREATE TABLE IF NOT EXISTS dila_person_wikidata (
  dila_id TEXT NOT NULL,
  qid TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'DILA_Person_Authority_sidecar',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (dila_id, qid, source)
);
```
2.005 dòng dự kiến, 1 QID/người trong toàn bộ mẫu kiểm tra (không thấy người nào có >1 QID).

## E. birth_death_dates — CHỈ BÁO CÁO, không ghi `people`

| Chỉ số | Giá trị |
|---|---|
| Người có `birth_death_dates` trong sidecar | 9.848 |
| Có dòng tương ứng trong `people` | 9.848 / 9.848 (100% — ID khớp hoàn toàn) |
| Cả 2 bên có năm sinh | 7.717 |
| **Mâu thuẫn năm sinh** | **1.844 / 7.717 (23,9%)** |
| Cả 2 bên có năm mất | 8.847 |
| **Mâu thuẫn năm mất** | **1.873 / 8.847 (21,2%)** |

- Tỉ lệ mâu thuẫn cao (~22–24%) — không an toàn để tự động ghi đè `people.birth_year/death_year`
  dù có được phép (mà task yêu cầu KHÔNG ghi đè). Một số lệch rất lớn (ví dụ `A000007`: sidecar
  death 1425 vs DB 393 — chênh hơn 1000 năm, khả năng DB cũ có lỗi nhập liệu hoặc ID bị gán nhầm
  giữa 2 người khác nhau cùng A-id lúc nạp trước đây). Mẫu đầy đủ 20 dòng mâu thuẫn trong file
  JSON dry-run kèm session.
- **Đề xuất riêng (không thuộc `--apply` lần này):** tách task audit các trường hợp lệch >100
  năm (khả năng cao là lỗi `people` cũ, không phải lỗi sidecar) thành task riêng sau khi Admin
  xem mẫu.

## F. cbeta_citations — CHỈ BÁO CÁO, chưa ghi (chưa rõ trùng)

| Chỉ số | Giá trị |
|---|---|
| Người có `cbeta_citations` | 25.915 |
| Người hoàn toàn không có trong `cbeta_person_mentions` | 18.006 (69,5%) |
| Tổng dòng citation | 53.929 |
| Trích được sigla CBETA (`T50n2061`...) | 33.167 (61,5%) |
| Đã có sẵn trong `cbeta_person_mentions` (cùng người + cùng sigla) | 8.066 |
| **Mới, chưa có trong `cbeta_person_mentions`** | **25.101** |

- `cbeta_person_mentions` (72.628 dòng, 10.173 người) chỉ phủ **39% số người** có citation
  trong sidecar DILA (10.173 / ~25.915 nếu tính người có mention). Hai nguồn bổ sung cho nhau,
  không trùng lặp hoàn toàn — nhưng **chưa rõ `cbeta_person_mentions` được tạo bằng phương pháp
  gì** (NLP trích xuất tự động? từ sidecar khác?) nên chưa thể kết luận 25.101 dòng "mới" này
  có an toàn để gộp hay sẽ tạo trùng logic khác tên. Theo đúng yêu cầu task — **không ghi**,
  để Admin quyết định hướng (tạo bảng riêng `dila_cbeta_citation_raw` giữ nguyên câu trích dẫn,
  hay merge có kiểm soát vào `cbeta_person_mentions`).

## Tổng hợp rủi ro

| Mục | Rủi ro | Mức |
|---|---|---|
| A | Nhập nhằng tên→nhiều ID (nhiều tên trùng khác thời kỳ) | Trung bình — lưu candidate + flag, không chặn |
| B | Tỉ lệ khớp thấp (13,3%) do thiếu danh bạ tự viện trong `places_dila` | Trung bình — vẫn nạp phần khớp, không kỳ vọng cao |
| C | 46% dòng không có canon code (tác phẩm thất lạc, đúng bản chất) | Thấp — lưu `raw_text`, `work_cbeta_id=NULL` |
| D | Không rủi ro đáng kể (0% trùng QID với địa danh) | Thấp |
| E | Mâu thuẫn ngày sinh/mất 21–24%, có ca lệch >1000 năm | Cao nếu ghi — **đã quyết định không ghi** |
| F | Chưa rõ phương pháp sinh `cbeta_person_mentions`, rủi ro trùng logic ẩn | Cao nếu ghi — **đã quyết định không ghi** |

## Giấy phép

Sidecar trích từ DILA Person/Place/Catalog Authority XML — CC BY-SA 3.0 (ghi theo
`DILA-resource-inventory.md` và XML gốc). Cột `source` của mọi bảng additive đề xuất ghi
`'DILA_Person_Authority_sidecar'` — không gộp với `ZQLOCAL`, `MARCUS`, `TTL_LOCAL` hay nguồn
khác.

## Lệnh `--apply` đề xuất (CHƯA CHẠY)

```
python scripts/etl_dila_links.py --apply --scope A,B,C,D
```
(Mục E, F **không có cờ --apply** — mãi mãi chỉ chạy `--report`, theo đúng yêu cầu task; muốn
ghi phải mở task riêng sau khi Admin xem mâu thuẫn.)

Trước khi chạy `--apply`, script thật (chưa viết) sẽ:
1. Backup `data/lineage.db` bằng SQLite backup API vào `data/backups/T481_<timestamp>/`.
2. Ghi dòng vào `docs/ROLLBACK.md` + file manifest trong `docs/sessions/2026-10-28/links/`.
3. `CREATE TABLE IF NOT EXISTS` 3 bảng additive (A/B dùng chung `dila_person_place_link`,
   C dùng `dila_person_work_link`, D dùng `dila_person_wikidata`).
4. Ghi trong 1 transaction, dedupe theo UNIQUE constraint đã thiết kế ở trên.
5. In số dòng trước/sau mỗi bảng; cung cấp `--revert` (`DELETE FROM <table> WHERE source =
   'DILA_Person_Authority_sidecar'`).

## Trạng thái

**Đã dừng tại đây — KHÔNG có lệnh ghi DB nào được chạy trong phiên này.** Chờ Admin xem báo cáo
và chọn 1 trong 3:
1. Duyệt `--apply` cho cả A, B, C, D như đề xuất.
2. Duyệt một phần (ví dụ chỉ A+C vì tỉ lệ khớp cao, hoãn B+D).
3. Yêu cầu sửa thiết kế bảng/so khớp trước khi duyệt.

File JSON dry-run đầy đủ (số liệu + mẫu 20 dòng mỗi mục) đã lưu kèm trong thư mục scratchpad
của phiên làm việc — có thể yêu cầu agent sau tái tạo bằng cách chạy lại script dry-run (chỉ
đọc) trên `data/dila_import/extracted/A*.json` + `data/lineage.db` (mode=ro).

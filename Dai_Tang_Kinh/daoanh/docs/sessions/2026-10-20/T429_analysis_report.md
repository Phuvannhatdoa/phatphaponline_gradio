# T429 — Phân Tích XML/TSV Places + Districts (nhánh Claude GitHub)

**Ngày:** 2026-10-20
**Task:** `tasks/T429-places-districts-claude-analysis.md` (Part 0 của T428/T430 — chỉ đọc, không ghi DB)
**Người thực hiện:** Agent Tích Hợp (Claude Code)

> **Lưu ý trùng ID:** `docs/tasktodo.md` khối `<!-- T429:START -->` hiện đang gắn với task khác
> ("Thiền Đăng Thế Phổ 禪燈世譜") vì có 2 file task cùng mang số T429
> (`T429-places-districts-claude-analysis.md` và `T429-thiendang-thepho-dataset-phase0-2.md`).
> Báo cáo này viết cho **T429-places-districts-claude-analysis.md** (đúng yêu cầu phân tích
> Places/Districts) — đề nghị Admin đổi 1 trong 2 sang số khác để tránh nhầm khi cập nhật tasktodo.md.

---

## 1. Nguồn tải về

- **Repo/nhánh:** `Phuvannhatdoa/phatphaponline_gradio`, branch `claude/sleepy-tesla-qsx17b`
- **Commit SHA (mới nhất ảnh hưởng 2 file XML):** `d1ffcc5d9910a3a8d3c929d18e352529933e6789` (2026-10-19T10:14:05Z)
  - Message: *"data: Han-Viet name_vi for 59,353 DILA places and 16,907 districts (unreviewed, Nam), review sheets, generic import"*
  - Co-Authored-By: Claude Sonnet 5.5
- **File đã tải (chỉ đọc, lưu ở scratchpad, KHÔNG copy vào repo):**
  | File | Dung lượng | Số dòng dữ liệu |
  |---|---|---|
  | `vn_place_name_vi.xml` | 21.7 MB | 59.353 `<place>` |
  | `vn_district_name_vi.xml` | 2.3 MB | 16.907 `<unit>` |
  | `review_needed_places.tsv` | 298 KB | **3.047** dòng dữ liệu (+1 header) |
  | `review_needed_districts.tsv` | 27 KB | **305** dòng dữ liệu (+1 header) |
  | `import_name_vi.py` | 3.1 KB | script import generic |

  **Sai lệch so với đề bài:** Task mô tả 2 file TSV là "3.352 dòng" mỗi file — số thực tế tải về là
  **3.047** (places) và **305** (districts), không phải 3.352/3.352. Có thể đề bài ghi nhầm hoặc nhánh
  đã được cập nhật lại giữa lúc viết task và lúc tải. Đã xác nhận bằng `wc -l` trên file tải trực tiếp
  từ raw.githubusercontent.com commit nêu trên.

---

## 2. Cấu trúc XML

### 2.1 `vn_place_name_vi.xml`

```xml
<vn_place_authority_name_vi source="DILA Buddhist_Studies_Place_Authority.xml (2026-10)"
    places="59353" generated="2026-10-19" status="CHUA_THAM_DINH_HOC_THUAT" am="Nam">
  <place dila_id="PL000000000001" tier="1">
    <name_zh>闊悉多國</name_zh>
    <name_vi>Khoát Tất Đa Quốc</name_vi>
    <category_zh>廣大之陸上人文地理區域</category_zh>
    <district_zh>阿富汗</district_zh>
    <district_vi>A Phú Hãn</district_vi>
    <!-- tier 3/4 có thêm: -->
    <review>Phược/Phọc</review>
    <alternatives>Phược Hát Quốc | Phọc Hát Quốc</alternatives>
  </place>
  ...
</vn_place_authority_name_vi>
```

- **ID:** thuộc tính `dila_id` — dạng dài **`PL` + 12 số** (ví dụ `PL000000000001`), **khớp định dạng
  `places_dila.id`**, KHÔNG khớp `places.id` (dạng ngắn `PL` + 6 số, ví dụ `PL000000`).
- **Tier:** có, thuộc tính `tier="1"`..`"4"`. Phân bố:
  | Tier | Số lượng | Ý nghĩa |
  |---|---|---|
  | 1 | 53.963 | Phiên âm Hán-Việt chuẩn, không cần duyệt |
  | 2 | 2.343 | Có biến thể nhẹ |
  | 3 | 2.889 | Có chữ đa âm/lệch tự điển — có `<review>` + `<alternatives>` |
  | 4 | 158 | Trường hợp đặc biệt khác |
- **District trong file này:** là **chuỗi Hán ghép theo cấp hành chính** (`<district_zh>`), ví dụ
  `阿富汗` hoặc `中國-雲南省-曲靖市-富源縣` — **không phải ID**. Đây là field tiện tra cứu nhanh (one-level
  context), không dùng để join DB.

### 2.2 `vn_district_name_vi.xml`

```xml
<vn_district_authority_name_vi source="DILA Buddhist_Studies_Place_Authority districts.xml (2026-10)"
    units="16907" generated="2026-10-19" status="CHUA_THAM_DINH_HOC_THUAT" am="Nam">
  <unit dila_id="PLA000001" type="country" tier="1">
    <name_zh>中國</name_zh>
    <name_vi>Trung Quốc</name_vi>
  </unit>
  <unit dila_id="PLB000011" tier="3">
    <name_zh>浙江省</name_zh>
    <name_vi>Chiết Giang Tỉnh</name_vi>
    <review>Chiết/Triết</review>
  </unit>
  ...
</vn_district_authority_name_vi>
```

- **ID:** thuộc tính `dila_id`, **4 tiền tố khác nhau** theo cấp hành chính:
  | Tiền tố | Số lượng | Cấp |
  |---|---|---|
  | `PLA` | 42 | Quốc gia (`type="country"`) |
  | `PLB` | 471 | Tỉnh/bang |
  | `PLC` | 4.637 | Thành phố/quận (cấp giữa) |
  | `PLD` | 11.757 | Huyện/cấp thấp nhất |
- **Đây chính là ID dùng trong thuộc tính `key` của thẻ `<location><place key="...">` trong file gốc
  DILA TEI XML**, và cũng trùng với cột `places_dila.place_key` đã có sẵn trong DB — **đây là chìa khóa
  join đúng cho district**, KHÔNG phải chuỗi Hán.
- Tier distribution: 1=15.984, 2=618, 3=278, 4=27.

### 2.3 TSV review

- `review_needed_places.tsv`: cột `dila_id, tier, name_zh, name_vi_hien_tai, can_duyet, phuong_an_khac, name_vi_da_duyet` — là **danh sách con** của các `<place>` tier 3 (lệch âm, ví dụ Phược/Phọc, Noa/Nã) để Admin chọn phương án rồi điền `name_vi_da_duyet`.
- `review_needed_districts.tsv`: cột tương tự, dành cho `<unit>` tier 3 (ví dụ `PLB000011` 浙江省 Chiết/Triết).
- Cột cuối (`name_vi_da_duyet`) hiện **trống hết** — chưa có vòng duyệt nào chạy qua các file này.

---

## 3. Review script `import_name_vi.py`

- **Generic**, dùng được cho 3 loại phần tử: `person | place | unit` (qua `--element`).
- **Mặc định CHẠY THỬ** (dry-run) — chỉ in số liệu, **không ghi** nếu thiếu `--apply`.
- Logic: đọc XML bằng `xml.etree.ElementTree.iterparse` (generator, tuân Zero-RAM) → lọc theo
  `--tiers` → chỉ cập nhật dòng có `dila_id` **đã tồn tại** trong bảng đích (`--table`/`--id-col`) →
  mặc định **chỉ điền ô `name_vi` còn trống** (cần `--overwrite` để ghi đè ô đã có giá trị).
- **CÓ UPDATE bảng gốc** khi chạy `--apply`: `UPDATE {table} SET name_vi=? WHERE {id_col}=?`
  (và tùy chọn `tier_column`, `district_column`). Trước khi ghi, script tự copy `{db}.bak`.
- **Tham số CLI:** `--db` (bắt buộc), `--element`, `--table` (mặc định `vn_person_authority` —
  **phải đổi sang `places_dila`/`places` khi dùng cho địa danh**), `--id-col` (mặc định `dila_id`),
  `--district-column`, `--xml`, `--tiers` (mặc định `1,2,3,4` — gộp cả tier 3/4 chưa duyệt kỹ, cần
  cân nhắc), `--tier-column`, `--overwrite`, `--apply`.
- **Rủi ro nếu dùng thẳng:** mặc định nạp **cả tier 3+4** (lệch âm/chưa chắc) vào `name_vi` nếu không
  giới hạn `--tiers 1,2`; không có validate riêng cho field district (chỉ copy thẳng `district_vi`
  text, không map qua ID).
- **Kết luận:** script này là **khung chung** (generic), CHƯA sẵn sàng chạy thẳng cho places/districts
  — cần viết wrapper riêng xử lý khóa `place_key` cho district (xem mục 6).

---

## 4. So khớp với DB (`data/lineage.db`)

### 4.1 Places: `vn_place_name_vi.xml` (`dila_id`) vs `places_dila.id`

| Chỉ số | Số lượng |
|---|---|
| Tổng `<place>` trong XML | 59.353 |
| Tổng dòng `places_dila` trong DB | 59.167 |
| **Khớp `dila_id` = `places_dila.id`** | **59.145** |
| XML có nhưng DB không có (orphan XML) | 208 |
| DB có nhưng XML không có | 22 |

- Orphan XML mẫu: `PL000000060487`...`PL000000060496` (dải ID liên tiếp ở cuối — khả năng là các
  place mới hơn bản DILA đã nạp vào DB, hoặc version DILA source khác thời điểm).
- 22 DB-only: cần rà tay (số nhỏ, không ảnh hưởng quyết định chung).

### 4.2 Places: `vn_place_name_vi.xml` (`dila_id`, 12 số) vs `places.id` (6 số, bảng rút gọn)

- **0 khớp trực tiếp theo chuỗi** — hai bảng dùng 2 hệ ID khác hẳn nhau (`PL000000000001` vs
  `PL000000`). `places` là bảng tổng hợp đã rút gọn ID riêng của hệ thống, **không có cột tham chiếu
  ngược sang `places_dila.id`** trong schema hiện tại (không thấy cột `dila_id` trong `places`).
  → Muốn liên kết `places` ↔ XML mới phải đi qua `places_dila` làm cầu nối (`places_dila.id` khớp
  XML trực tiếp; `places` ↔ `places_dila` cần cột bắc cầu khác — ngoài phạm vi phân tích này).

### 4.3 Lệch chữ Hán (`name_zh` XML vs tên chính DB)

- **Chú ý cột:** `places_dila.name_zh` **không phải** tên Hán chính — cột `places_dila.name` mới là
  tên chính (Hán hoặc dạng gốc). Soi theo đúng cột `name`:
  - Kiểm tra: 59.145 dòng khớp ID.
  - **Lệch chữ:** 109/59.145 (**0,18%**) — hầu hết là do `places_dila.name` lưu tên **không phải
    Hán** (Latin hóa/Nhật/Phạn, ví dụ `Bāxtriš`, `バーミヤーン`, `Kapiśa`, `India`, `Gaṅgā`) còn XML lấy
    đúng `<name_zh>` Hán. Đây là khác biệt do field `name` trong DB chọn "tên đại diện tốt nhất" (có
    thể không phải Hán), **không phải lỗi dữ liệu** — chỉ cần biết khi so sánh text.

### 4.4 District: `vn_district_name_vi.xml` (`unit dila_id`) vs `places_dila.district`/`place_key`

| So khớp theo | Kết quả |
|---|---|
| `places_dila.place_key` (distinct) | 4.145 giá trị |
| Unit `dila_id` trong XML khớp `place_key` | **4.145 / 4.145** (100% place_key hiện có đều có trong XML) |
| Unit `dila_id` trong XML KHÔNG xuất hiện ở `place_key` nào | 12.762 / 16.907 (72%** — đa số là các cấp hành chính cha/ông không được dùng trực tiếp làm `place_key` của bất kỳ place nào, hợp lý vì `place_key` chỉ trỏ tới node lá/gần lá) |
| `places_dila.district` (chuỗi Hán ghép, distinct) | 4.322 chuỗi |
| Chuỗi `district` khớp **y nguyên** 1 `name_zh` đơn cấp trong unit XML | chỉ **35 / 4.322** (0,8% — vì `district` là chuỗi ghép nhiều cấp bằng dấu `-`, còn `name_zh` trong unit XML là **tên 1 cấp đơn**) |

**Kết luận mấu chốt:** cột `district` (text Hán ghép chuỗi) **không thể join trực tiếp** với file
district mới — phải tách chuỗi theo `-` rồi so từng đoạn, dễ sai (trùng tên tỉnh/huyện ở nhiều nước).
Ngược lại, cột `place_key` **đã có sẵn trong DB và khớp 100%** với `dila_id` của file `unit` mới — đây
là khóa đúng và an toàn để liên kết district.

---

## 5. Quyết định khóa district: **dùng `place_key` (ID), KHÔNG dùng chuỗi Hán**

Lý do:
1. `places_dila.place_key` đã tồn tại sẵn, 100% khớp `dila_id` của `vn_district_name_vi.xml` (mục 4.4).
2. Chuỗi `district` là bản ghép nhiều cấp, không ánh xạ 1-1 vào bảng unit mới (chỉ 0,8% khớp thẳng).
3. ID bền hơn text khi DILA đổi cách viết (ví dụ thêm hậu tố `(Balkh)`), tránh join sai do trùng tên.

→ Khi viết ETL thật (ngoài phạm vi T429), nên: `places_dila.place_key = vn_district_name_vi.unit[dila_id]`
để lấy `name_vi`/`district_vi`, **không** parse `district` text.

---

## 6. Khuyến nghị bước tiếp theo (không thực hiện trong T429)

1. Viết wrapper riêng (không dùng thẳng `import_name_vi.py` generic) cho 2 trường hợp:
   - `places_dila.name_vi` ← `vn_place_name_vi.xml` theo `id = dila_id`, lọc `tier ∈ {1,2}` cho đợt đầu
     (tier 3/4 chờ Admin duyệt qua TSV trước).
   - Cột `name_vi`/`district_vi` cho `place_key` ← `vn_district_name_vi.xml` theo `place_key = dila_id`.
2. Xử lý 208 orphan XML + 22 DB-only riêng (không block đợt nạp chính).
3. Đợt tier 3 (2.889 places / 278 units) + TSV review (3.047 + 305 dòng) cần Admin chọn phương án
   trước khi nạp `name_vi_da_duyet` — khác với luồng tier 1/2.
4. Cân nhắc có nên thêm cột `place_key` tham chiếu ngược cho bảng `places` (6-số) để tương lai không
   phải đi qua `places_dila` làm cầu nối.

---

## 7. Kết luận

- **Join key cho places:** `places_dila.id` ↔ XML `dila_id` — khớp 99,6% (59.145/59.353), an toàn dùng.
- **Join key cho districts:** `places_dila.place_key` ↔ XML (unit) `dila_id` — khớp 100% các place_key hiện có; dùng ID, không dùng chuỗi Hán.
- **Không có xung đột schema** — chỉ cần thêm cột (`name_vi`, có thể `tier_name_vi`) vào `places_dila`,
  không cần bảng mới.
- **License/nguồn:** dữ liệu do agent Claude khác trong cùng tổ chức sinh ra từ DILA Authority gốc —
  không phải nguồn ngoài mới, không cần qua cổng Legal Check (`source_check.html`).
- **Chưa ghi DB, chưa chạy script** theo đúng yêu cầu T429.

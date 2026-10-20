---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
report: G2-2 IDENTITY_HUB
title: "Identity Hub — bản đồ danh tính địa danh DILA và khoảng trống cross-source"
status: ready-for-admin-review
created: 2026-10-04
measured_at: 2026-10-04
db: data/lineage.db (read-only)
---

# T224 · G2-2 — Identity Hub

**Mục đích:** trả lời *"ta có thể ghép place này với nguồn ngoài ở mức nào, và vì sao
chưa được?"* — trước khi đề xuất bất kỳ bảng identity nào.

---

## 1. Khoá trong nội bộ: `dila_id` là **duy nhất**

| Kiểm tra | Kết quả |
|---|---|
| `places_dila` rows | 59.167 |
| `COUNT(DISTINCT id)` | **59.167** |
| ⇒ PK `id` **không trùng** | ✅ |

⚠️ Phân biệt rõ: **29 nhóm `dila_id` trùng của T223 là ở `vn_person_authority`** (dữ liệu
**người**), **không** phải ở `places_dila`. Ở bảng place, `dila_id` sạch hoàn toàn.
Trộn hai bảng là nhầm lẫn thường gặp.

---

## 2. Trùng **tên** thì có — và rất nhiều

| Cột | Có giá trị | Giá trị khác nhau | Số lượt trùng |
|---|---:|---:|---:|
| `name` | 59.157 | 36.832 | **22.325** |
| `name_zh` | 59.150 | 37.568 | **21.582** |
| `name_en` | 712 | 707 | 5 |
| `name_san` | 236 | 234 | 2 |
| `name_jpn` | 313 | 312 | 1 |
| `place_key` | 58.100 | **4.145** | 53.955 |

⚠️ **`place_key` KHÔNG phải khoá định danh.** 58.100 place chỉ rơi vào **4.145** giá trị ⇒
đây là **khoá phân loại/loại địa danh**, dùng chung cho nhiều place. Tên gọi nhầm dễ chạy
JOIN sai hàng loạt.

### 7.658 nhóm `name_zh` bị trùng (nhiều hơn 1 place)

Ví dụ: `開元寺` · `報恩寺` · `觀音寺` · `新城` · `都尉`

Đây là **cấu trúc ngôn ngữ**, không phải lỗi dữ liệu: nhiều ngôi chùa cùng tên ở các
tỉnh khác nhau. ⇒ **`name_zh` không thể là khoá ghép với nguồn ngoài.**

Cần phân biệt 2 trường hợp khi trùng tên:
- **Trùng vì là cùng một thực thể** (duplicate thật) → cần gộp.
- **Trùng vì khác địa lý** (nhiều chùa cùng tên) → **phải giữ riêng**.

Phân biệt bằng **`district`** (99,91% có) + toạ độ (99,86% có), **không** bằng tên.

---

## 3. Khoảng trống cross-source: **rất nhỏ**

| Nơi giữ QID | Distinct `dila_id` |
|---|---:|
| `geo_cross_ref.wikidata_qid` | 148 |
| `place_timeline_events.source_ref GLOB 'Q[0-9]*'` | 249 |
| **Hợp nhất (union)** | **314** |
| Có QID ở **cả hai** nơi (trùng lặp thông tin) | 83 |

⇒ **314 / 59.167 = 0,53%** place có QID. Phần còn lại **99,47%** không có neo ngoài nào.

### Phủ định ID trong `geo_cross_ref` (190 rows)

| Cột | Rows | Ghi chú |
|---|---:|---|
| `wikidata_qid` | **148** | nguồn neo chính |
| `bgis_id` | **33** | |
| `chgis_svid` | **0** | ⚠️ cột rỗng hoàn toàn |
| `tgaz_id` | **0** | ⚠️ cột rỗng hoàn toàn |
| `bdrc_id` | **0** | ⚠️ cột rỗng hoàn toàn |
| `marcus_ref` | **0** | ⚠️ cột rỗng hoàn toàn |

148 + 33 + 9 (candidate) = **190** ✓

⇒ **4 trong 6 cột cross-ref là cột rỗng.** T112 kết luận *"5 BLOCK (BDRC/SAT/CHGIS/
FoJin/TGAZ — legal chưa rõ)"* — dữ liệu **xác nhận**: những nguồn đó **chưa hề được nạp
dù đã có cột chờ**. Ràng buộc của nhóm C là **license thật**, không phải lý do kỹ thuật.

---

## 4. 🔴 Phát hiện quan trọng: **tọa độ đã có sẵn, nhưng lưu ở 2 nơi**

| Nơi lưu | Số place có lat/lon | % |
|---|---:|---:|
| **`places_dila.geo_lat` + `geo_long`** | **58.480** | **98,84%** |
| `geo_cross_ref.enrich_lat/lon` | **9** | 0,015% |
| `geo_cross_ref.wikidata_lat/lon` | **0** | 0% |
| `geo_cross_ref.elevation_m` | **0** | 0% |

**Đây là 2 kho toạ độ song song cho cùng một thực thể.** `places_dila` đã đầy 98,84%;
bảng `geo_cross_ref` gần như trống ở các cột enrich (`enrich_status`: `none` 181 /
`candidate` 9).

**Hệ quả cho kế hoạch:**
1. **Không cần "enrichment" toạ độ** — đã xong từ nguồn.
2. Nếu xây Identity Hub, phải **chọn một nguồn sự thật** cho toạ độ, nếu không sẽ có hai
   giá trị cạnh tranh cho cùng 1 place.
3. `elevation_m` = **0** ⇒ **độ cao là dữ liệu hoàn toàn mới**, khác với lat/lon.

⚠️ Đây là điểm **chồng lấn với T121** (Wikidata lat/lon enrichment, `in_progress`).
**T224 không làm phần này.**

---

## 5. Đề xuất Identity Hub (additive, chưa mở G3)

Vì G3 không mở, đây là **thiết kế trên giấy** để Admin duyệt hoặc bác:

### 5.1 Không dựng bảng identity mới (chưa cần)

Hiện có 2 khoá ứng viên: `places_dila.id` (sạch, 59.167) và `geo_cross_ref.dila_id`
(190). **Chưa cần bảng trung gian** — chỉ cần 1 view chuẩn hoá + 1 bảng **chỉ chứa kết
quả khớp đã verify**.

### 5.2 Bảng đề xuất (additive, **chỉ khi có ≥1 khớp mới**)

```
place_identity_match
  dila_id        TEXT   FK → places_dila.id
  source_system  TEXT   'wikidata' | 'bgis' | 'chgis' | 'tgaz' | 'bdrc'
  external_id    TEXT   QID / svid / id
  match_method   TEXT   'qid' | 'district+geo' | 'name_zh+district' | 'manual'
  match_conf     REAL   0..1
  reviewed_by    TEXT   NULL  ← HITL
  UNIQUE(source_system, external_id)
```

**Nguyên tắc:** `match_method='name_zh+district'` **không** được auto-accept, vì
7.658 nhóm trùng tên. Chỉ `qid` mới auto-accept.

### 5.3 Việc cần làm trước khi xây

| # | Việc | Chủ sở hữu | Trạng thái 2026-10-04 |
|---|---|---|---|
| 1 | Chốt **nguồn sự thật cho toạ độ** | Admin | ✅ **ĐÃ CHỐT: `places_dila.geo_lat/lon`** (DILA cấp, 98,84%). `geo_cross_ref.enrich_*` là dữ liệu dẫn xuất, 9 row |
| 2 | Quyết **license** CHGIS/TGAZ/BDRC/SAT/FoJin | Admin | ⏸ **BỎ QUA** — Admin: *"sẽ update sau trên HTML"*. 3 cột cross-ref rỗng giữ nguyên, **không** blocker |
| 3 | Đo `name_zh` trùng: bao nhiêu duplicate thật vs khác địa lý | T224 | ⏸ để khi nào mở G3 |
| 4 | Gộp 83 place có QID ở **cả hai** bảng | T224 | ⏸ để khi nào mở G3 |

### 5.4 Vì sao hướng "license qua GitHub" **chưa** mở được 4 cột cross-ref

*(Ghi lại để tầng HTML làm sau không phải đo lại — Admin đã chốt **bỏ qua** ở T224.)*

Tiền lệ **đã có** trong DB và rất đúng ý Admin:
- `kanripo_catalog.github_repo` → `license` = **CC BY-SA 4.0** (từng repo một)
- `cbeta_catalog_vn.license_url` → **3.122** dòng trỏ creativecommons.org
- `place_wiki_snapshots.license` = CC BY-SA 4.0

**Nhưng** đo trên `data_sources` (14 nguồn):

| Cột | Có giá trị |
|---|---|
| `repository_url` | **1 / 14** (chỉ ZENLINEAGE) |
| `license_verified` | **0 / 14** |
| `license_url` | **0 / 14** |
| `license_spdx` | **0 / 14** |
| `data_license` | **0 / 14** |
| `origin_url` | 4 / 14 (CBETA, DILA, MARCUS, Wikidata) |

⇒ **CHGIS · TGAZ · BDRC · FoJin không có URL nào** (kể cả `origin_url`) ⇒ không tra được
license theo đường GitHub. Ba trong bốn cột cross-ref rỗng (`chgis_svid`, `tgaz_id`,
`bdrc_id`) **ứng với đúng 3 nguồn không có URL**.

**Khi làm trên HTML (T231 Source Hub / T230 catalog):** mỗi nguồn cần **link + ngày + người
xác minh**; **không** điền license từ trí nhớ. `T18` đã kết luận BDRC *"SKIP hoàn toàn"* —
có thể áp cho CHGIS + TGAZ.

---

## 6. Kết luận

- `dila_id` **sạch** — không cần re-identification ở tầng place.
- Vấn đề thật **không phải** trùng `dila_id`, mà là **trùng tên** (7.658 nhóm) và
  **thiếu neo ngoài** (99,47% không có QID).
- **Không cần bảng identity cho tới khi** có nguồn ngoài mới hoặc quyết định gộp tên.
- Toạ độ **đã** có 98,84% và **đã chốt** `places_dila` là SSOT ⇒ **đừng xây enrich toạ
  độ** (và đừng chồng T121).

## 7. Revert

Docs-only: `git revert --no-edit <sha>`. **0 DB.**
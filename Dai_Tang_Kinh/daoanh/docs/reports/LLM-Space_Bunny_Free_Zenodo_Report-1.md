# Zendodo 10004109 — Van Cutsem (Zutang ji 祖堂集) Khảo sát dữ liệu & đề xuất ánh xạ vào Đạo Ảnh

**Ngày lập:** 2026-10-16
**Record:** https://zenodo.org/records/10004109
**DOI:** 10.5281/zenodo.10004109 — **concept DOI:** 10.5281/zenodo.10004108
**Bài báo:** Van Cutsem, Laurent. 2023. "Lineages as Network: A Study of Chan Genealogy in the Zutang ji 祖堂集 Using Social Network Analysis" — *Religions* 14(2):205 | https://doi.org/10.3390/rel14020205
**Status:** Khảo sát đã hoàn tất sẵn trong `docs/reports/zenodo-10004109-survey-20261016/`. **Chưa ghi đè legacy, chưa tự accepted, chưa nhập production.**
**Task:** T394 (pending)

---

## 1. Tải ZIP — metadata, version, license, checksum

| Trường | Giá trị |
|---|---|
| Record ID | 10004109 |
| Concept ID | 10004108 |
| Version | v1 |
| Revision (Zenodo) | 6 |
| Khởi tạo | 2023-10-19T03:10:06Z |
| Cập nhật | 2023-10-21T13:18:21Z |
| Ngày xuất bản | 2023-10-15 |
| Truy cập | open |
|(UnityEngine/owner) | người sở hữu #39603 |
| Loại tài nguyên | Dataset |
| License toppings record | CC BY 4.0 |
| Ngôn ngữ | eng |
| Tác giả (bản survey) | Marcus Bingenheimer (affil. Temple U, ORCID 0000-0002-9102-9217) et al. |
| Van Cutsem, Laurent | affiliation null |
| Tổng download | 97; tổng view 513 |

**File duy nhất trong record:**

| File | Bytes | Advertised MD5 | Verified MD5 | SHA-256 |
|---|---|---|---|---|
| `historicalNetworkAnalysisChineseReligion2023-10.zip` | 86,334,571 (82,3 MiB) | `78c722a304d06962a12f9899d5442e3e` | **MATCHED** ✅ | `60d7c0333860a6ce4e76a82e3f08f6d4e943fc6def272108b2571139d648e811` |

- Tải vào: `download/historicalNetworkAnalysisChineseReligion2023-10.zip`
- Thời điểm tải: `2026-10-16T07:07:04.490406Z`
- `metadata_sha256`: `ccd9697cc9e31803b6ad8b10d1613b6076ebe1926b7ef6170bd674877eb5eec0`
- Receipt: `download-receipt.json` (`docs/reports/zenodo-10004109-survey-20261016/download-receipt.json`)

---

## 2. Danh sách file trong công trình Van Cutsem

Thư mục: `extracted/vancutsem_laurent/` — **17 file**.

| File | Bytes | Đánh giá |
|---|---|---|
| `01-README.md` | 3.599 | metadata, credit, license |
| `02-license.txt` | 18.656 | bản text CC BY 4.0 |
| `03-zutangji-haidongxinkaiyinbanji_SNA.xml` | 92.871 | TEI lời tựa 1245 (Goryeo) |
| `03-zutangji-zutangjixu_SNA.xml` | 9.451 | TEI lời tựa gốc ZTJ |
| `03-zutangji_supp_SNA_caotang.xml` | 8.608 | TEI partial Caotang |
| `03-zutangji_supp_SNA_xinghua.xml` | 7.541 | TEI partial Xinghua |
| `04-schema_ODD.xml` | 2.344 | TEI ODD để sinh RNG |
| `04-schema.rng` | 678.815 | schema RelaxNG |
| `05-ZTJ_edges_ZTJmain.csv` | 26.906 | **DL cạnh SNA** — 256 edge |
| `05-ZTJ_nodes_full.xlsx` | 67.881 | node đầy đủ — **266 dòng × 18 cột** |
| `05-ZTJ_nodes_simplified.csv` | 18.688 | node rút gọn — **260 dòng × 7 cột** |
| `06-ZTJ_fullTable.xlsx` | 81.926 | cấu trúc ZTJ — **353 × 22**, mapping with CBETA editions |
| `07-ztjLinkGrps.gexf` | 186.888 | bordereaux SNA (`default` 257 record) |
| `08-*.png` (×4) | ~1.0–2.2 MB | hình network |

⚠️ **Lưu ý:** toàn bộ các file này cùng nằm trong **một** record, đồng nhất khai báo metadata `cc-by-4.0`, nhưng 4 file TEI có **bên trong** прав notice riêng.

---

## 3. Dữ liệu có gì — số thật

### 3.1 Node

| Nguồn | Số node | Đặc điểm |
|---|---|---|
| `05-ZTJ_nodes_simplified.csv` | **260** (delim `;`) | 7 cột: `ID; Label; No. (Generations); Generations & groups; Length of entries; Zàn 讚 by Jìngxiū; Country of origin` |
| `05-ZTJ_nodes_full.xlsx` | **266** | 18 cột, bản đầy đủ computation. 4 dòng dummy? (header + 265) **lệch 6 node** giữa hai file |
| `06-ZTJ_fullTable.xlsx` | **353** | XML entry-level, không phải node-level; có mapping CBETA (`ZBK`, `ZHSJ`, `SWYSG`) |

- `ID` = **DILA ID** style `A003431` — 260/260 bắt đầu `A` + 7 chữ số.
- `Label` = **Hán văn, không tiếng Việt** (người dùng phải map tên vi).
- `No. (Generations)`: nguyên văn: `1`…`48`, `0`, `?`, hoặc `不清楚 (慧能下第三代; 馬祖下第一代?)` — **không quy đổi**.
- `Generations & groups`: **24 nhãn** (過去七佛, 天竺二十七祖, …).
- `Zàn 讚`: 42 node có khen >0.
- `Country of origin`: `烏有`, `天竺`, v.v.
- **Không có tên Việt anywhere trong DL.**

### 3.2 Edge

- `05-ZTJ_edges_ZTJmain.csv`: **256 cạnh** (delim `,`).
- Cột: `Source, Target, Type, Id (UUID), e@ref`.

| Thuộc tính | Kết quả |
|---|---|
| `Type` | `Undirected` **100%** (256/256) — **không có directed teacher–disciple**. |
| `e@ref` | 256/256 có locator; locator dạng `CBETA lines:\tB25n0144_#0299b08 #0299b08` |
| CBETA refs | **100% trích `B25n0144` (碧巖録)** — không từ ZTJ trực tiếp. |
| UUID `Id` | định danh duy nhất từng cạnh |

### 3.3 Evidence / uncertainly

| Tag | Số trong TEI |
|---|---|
| `<corr>` | 10 |
| `<sic>` | 8 |
| `<choice>` | 8 |
| `<supplied>` (reason=omitted / overlooked, cert=medium) | 3 |
| `<unclear>` (reason=damage; cert=low) | 1 |
| `<linkGrp>` cert=low | **41** |

- CSV/XLSX/GEXF **không có cột bất định** — thông tin hiệu chỉnh **mất khi chuyển sang bảng số**.
- Audit đặt ra `production_effect: none; no asserted teacher/disciple triples or generation conversion`.
- Rfindings quan trọng: *"Original-preface groups mix person/place and three-person contexts; exploding all ptr combinations into teacher edges would invent relations."*

### 3.4 Phân biệt lời tựa / chính văn / hiệu chỉnh

- **Wcritique persons nodes:** `ID/Label` cùng xuất per-paragraph, `Juan`, `No. entry by juàn`, `Ref` Gi yok.
- **ZTJ entries vs Goryeo preface:** mapping cột riêng trong `06-ZTJ_fullTable.xlsx`.
- **TEI tách 4 file** (zutangjixu = lời tựa gốc; haidongxinkaiyinbanji = lời tựa 1245; supp caotang/xinghua = partial TEI) và mang `sic`/`corr`/`choice`/`supplied`/`unclear`.
- **Không có cột "edition" hay "cort text"** trong CSV/XLSX — phải dùng file TEI để biết bản nào.

---

## 4. Mapping vào schema Đạo Ảnh — chỉ additive, không ghi đè legacy

DB hiện có:
- `vn_person_authority`: 1.511 bản ghi (hiện trong `ZTJ` 114 bản ghi đã có; **146 bản ghi mới**)
- `lineage_edge_assertions`: 57.175 cạnh **có hướng** (`subject_person_id → object_person_id`) với `citation_tier`, `trust_level`, `status`.

### 4.1 Bảng node — **staging, không ghi vào `vn_person_authority`**

```sql
CREATE TABLE ztj_node_observation (
  observation_id         TEXT PRIMARY KEY,         -- DILA ID
  source_record          INTEGER NOT NULL,         -- 10004109
  source_article         TEXT NOT NULL,            -- doi 10.3390/rel14020205
  source_file            TEXT NOT NULL,
  label_zh               TEXT NOT NULL,
  generation_raw         TEXT,                     -- NGUYÊN VĂN: "7" / "0" / "?"
  generation_group_raw   TEXT,
  juan_raw               TEXT,
  ztj_entry_no_raw       TEXT,
  ztj_entry_chars_raw    TEXT,
  goryeo_preface_no_raw  TEXT,
  goryeo_preface_name_raw TEXT,
  goryeo_preface_ref_raw  TEXT,
  zan_jingxiu_raw        TEXT,
  country_origin_raw     TEXT,
  dila_already_present    INTEGER NOT NULL DEFAULT 0,
  mapping_verified        INTEGER NOT NULL DEFAULT 0,
  trust_level             TEXT NOT NULL DEFAULT 'source_asserted',
  status                  TEXT NOT NULL DEFAULT 'staged'
);
```

### 4.2 Bảng cạng — **KHÔNG** vào `lineage_edge_assertions`, vào bảng riêng

Vì nguồn **không có hướng**; đưa vào `subject→object` là khẳng định sai.

```sql
CREATE TABLE ztj_edge_observation (
  observation_id      TEXT PRIMARY KEY,     -- UUID nguồn
  source_record       INTEGER NOT NULL,
  source_file         TEXT NOT NULL,
  endpoint_a_dila     TEXT NOT NULL,
  endpoint_b_dila     TEXT NOT NULL,
  directionality      TEXT NOT NULL DEFAULT 'unasserted',
  relation_semantics   TEXT NOT NULL DEFAULT 'associated_with',
  ref_locator_raw     TEXT,                 -- 'B25n0144_#0299b08' nguyên văn
  cert                TEXT,                 -- 'low' nếu có; NULL KHÔNG đồng nghĩa chắc chắn
  mapping_verified    INTEGER NOT NULL DEFAULT 0,
  status              TEXT NOT NULL DEFAULT 'staged'
);
```

### 4.3 Quy tắc bất di bất dịch

- `directionality = 'unasserted'` cho tới khi Admin duyệt.
- `generation_order`, `dharma_lineage` của `vn_person_authority` **không** được suy ra bằng phép trừ/cộng từ `generation_raw`.
- `vn_person_authority` legacy **không** ghi đè; chỉ staging.
- CBETA locator 256 edge không ba dot AAAA/ф.
- Rào canto consistency: `ztj_edge_observation` không tự nhân vào `lineage_edge_assertions` promotion.

---

## 5. 5 câu cần quyết định

1. **"DMCT" không tồn tại trong repo** (git grep -i dmct → exit 1; không có trong tên file nào). Bạn đang nói file nào? Nếu nằm ngoài repo thì cho đường dẫn precise.
2. **Xử lý xung đột license:** (a) Áp CC BY-NC-SA 4.0 cho toàn bộ phần Van Cutsem — an toàn nhất; (b) Tách theo từng file: bảng số CC BY 4.0, TEI không commercial; (c) Không đưa TEI vào hệ thống.
3. **146 node mới:** cho tạo bản ghi `vn_person_authority` với `status='imported_unverified'`, hay giữ nguyên trong staging?
4. **Edge: cho phép suy hướng thầy→đệ tử bằng quy tắc `N→N+1` không?** Tôi **không khuyến nghị** (3 node generation uncertain, ptr ngược). Cần rõ.
5. **Nguồn B25n0144 (碧巖録):** 256 edge đều trích nguồn này chứ không phải ZTJ. Có cần tra CBETA locator với bản 碧巖録 trong `cbeta.db`? (Hiện `cbeta.db` mới có T1–T4, T14, T50, T51 → **chưa có**.)

---

## 6. Mẫu 10 node / 10 edge — đã có sẵn

- `analysis/sample-nodes-10.json` — 10 node đầu CSV gốc, kèm `source_sha256`, `source_notice`, `semantic_status: unmapped source_asserted`.
- `analysis/sample-edges-10.json` — 10 edge đầu CSV gốc.
- `analysis/02-nodes-sample.json`, `02-edges-sample.json` — cùng definition.

---

## 7. Đánh giá dataset — có hỗ trợ NTNKhông autorship hay không?

| Tiêu chí | Kết quả |
|---|---|
| Names people + ID DILA | ✅ 260/260 node → DILA ID; citations B25n0144 → locator CBETA |
| Direct transmission edges | ❌ Không — Undirected 100%; chỉ association |
| Generation/level labels | ✅ Có + 24 groups; nhưng uncertain encoding, không quy đổi |
| Evidence per relationship | ✅ locator per edge + B25n0144; entry-length bằng footprint |
| Preface vs content distinction | ⚠️ Partial — CSV/XLSX/GEXF mất; TEI có TEI metadata |
| Correction distinction (sic/corr/choice/supplied/unclear) | ⚠️ Chỉ TEI; CSV chỉ có `?` mã hóa uncertain |
| Mapping viability | ✅ 114/260 reuse DILA; 146 mới — chỉ staging |
| License | ⚠️/conflict 4 TEI NC-SA vs record CC BY 4.0 |

---

## ⚠️ Định quota / không thể làm tự động

1. **Generation numbering không được suy** — cannot convert to edges or use `generation_order` without Admin decision.
2. **Eleghost UNESCO / DMCT không tham chiếu được** trong repo — chưa biết file nào.
3. **B25n0144 không có trong cbeta.db hiện tại** — tra cứu locator từ CBETA phải import trước (đã có pipeline `cbeta_translate_worker.py`). — 4 TEI notice cần xử lý trước anything production.

---

## 8. Bước tiếp theo

Khảo sát đã xong; không cần tải lại. Để lưu thành report chính thức + đăng ký task T394 + cập nhật `tasktodo.md`/`ROLLBACK.md` vào repo Đạo Ảnh — tôi cần **thoát Plan Mode**.

Trước khi thoát, xin bạn trả lời câu **2 và 4** (license + hướng edge) vì hai điều này quyết định toàn bộ thiết kế mapping.
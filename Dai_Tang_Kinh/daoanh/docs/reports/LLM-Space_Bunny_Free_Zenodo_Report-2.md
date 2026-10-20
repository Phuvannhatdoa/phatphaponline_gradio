# Zenodo 10004109 — Van Cutsem (Zutang ji 祖堂集) — Khảo sát dữ liệu, bàn giao GIAI ĐOẠN 2

**Ngày lập:** 2026-10-16 (bản `-2.md`, thay thế `-1.md`)
**Record:** https://zenodo.org/records/10004109 · **DOI:** 10.5281/zenodo.10004109 · **concept DOI:** 10.5281/zenodo.10004108
**Bài báo:** Van Cutsem, Laurent. 2023. "Lineages as Network: A Study of Chan Genealogy in the Zutang ji 祖堂集 Using Social Network Analysis" — *Religions* 14(2):205 · https://doi.org/10.3390/rel14020205
**Task:** T394
**Phạm vi:** Vùng cách ly `docs/reports/zenodo-10004109-survey-20261016/`. **Không** sửa DB/TTL/legacy, **không** import production, **không** tự `accepted`, **không** suy số đời.

> **Sửa lỗi bản `-1.md`:** bản cũ ghi `B25n0144` = 碧巖録 là **SAI**. `B25n0144` = **祖堂集** (卍新纂大日本續藏經 / 卍續藏, quyển 25, số 144) — đúng theo chính TEI (`note`, dòng 22: *"(Supplement to the Dàzàngjīng 大藏經補編, Electronic version 數位版, No. 144 祖堂集)"*). Bản Taishō tương ứng = **T2005**. Mọi locator cạnh trong dataset trỏ về 祖堂集, không phải 碧巖録.

---

## 0. Bàn giao 6 deliverable (đã sinh trong `analysis/phase2/`)

| # | Deliverable | Trạng thái | Nội dung chính |
|---|---|---|---|
| 1 | `edge-diff.json` | ✔ + mở rộng | 256 CSV vs 257 GEXF; 1 UUID lệch; **crosswalk 70/70 locator → TEI `<lb ed="B">`** |
| 2 | `relation-direction-audit.json` | ✔ + mở rộng | 10 ca R01–R10; hướng nguồn ghi vs hướng tự suy; **đối chiếu DILA live** |
| 3 | `generation-inventory.json` | ✔ + mở rộng | 49 giá trị generation (0–48); **chính sách không quy đổi PTDA** |
| 4 | `uncertainty-inventory.json` | ✔ + mở rộng | sic/corr/choice/supplied/unclear; **41 linkGrp cert=low, 41 link, 15 locator** |
| 5 | `rights-matrix.json` | ✔ + mở rộng | 17 dòng; **4 dòng `unresolved=true`** (TEI NC-SA vs record CC BY) |
| 6 | `person-id-audit.json` | ✔ + mở rộng | 10 ID A######; **bằng chứng DILA first-hand** |

Bằng chứng tra cứu trực tiếp: `analysis/phase2/dila_live/` (10 HTML gốc + `dila-live-lookup-20261016-final.json`).

---

## 1. Đối soát cạnh (deliverable 1)

- `05-ZTJ_edges_ZTJmain.csv`: **256 cạnh**, phân cách `,`, cột `Source, Target, Type, Id (UUID), e@ref`.
- `07-ztjLinkGrps.gexf`: **257 record cạnh**.
- **Giải thích chênh lệch 256 vs 257:** một cặp endpoint nguồn có **hai bản ghi song song** trong GEXF — một ở `#0300b07` (Goryeo) và một ở `#0412a05` (Caotang). CSV **gộp còn một dòng**: UUID khớp bản GEXF Goryeo, nhưng `e@ref` khớp bản GEXF Caotang. Cơ chế gộp của exporter **không được cung cấp** ⇒ **không chứng minh được**, nên **giữ cả hai nhân chứng, không xóa/không chọn định dạng làm chuẩn**.
- UUID lệch: `78ec7095-e4b3-4d92-937d-f08aeaf317c3` (GEXF-only). `csv_only = []`. 255/256 UUID còn lại khớp mọi thuộc tính chiếu.
- **`Type` = `Undirected` 256/256** — không có cạnh nào ghi hướng thầy→đệ tử.

### 1.1 Crosswalk locator (mở rộng mới)

- 256 cạnh → **70 locator phân biệt** (trích từ `e@ref`, dạng `B25n0144_#0299b08`).
- TEI có **94 `<lb ed="B">`** trên 4 file ⇒ **70 khớp, 0 thiếu**, **24 unused** (lb không xuất hiện trong bảng cạnh; có thể phục vụ nội dung khác — **không** kết luận là thiếu cạnh).
- Cảnh báo: dòng 1457 của `03-zutangji-haidongxinkaiyinbanji_SNA.xml` là **XML comment** chứa 3 `<linkGrp>` minh họa ⇒ mọi phép đếm phải **bỏ comment trước** (đã áp dụng).

---

## 2. Đối chiếu 10 quan hệ (deliverable 2)

Chọn **xác định theo thứ tự file/element** (không ngẫu nhiên): 3 linkGrp lời tựa gốc, 4 linkGrp Caotang, 1 linkGrp Xinghua, nhóm song song Goryeo DaoYuan/ZongMi, và đoạn supplied cert=medium Goryeo Xinghua.

Kết quả chính:

1. **Nhóm lời tựa gốc trộn người/địa danh và ngữ cảnh ba người** — bung mọi tổ hợp `ptr` thành cạnh thầy sẽ **bịa quan hệ**.
2. **Caotang và Xinghua đều dùng chữ 嗣 trong văn bản, nhưng quy ước thứ tự `ptr` ngược nhau.** Vị trí `ptr` trong XML **và** `Source/Target` của đồ thị vô hướng **đều không** định nghĩa hướng thầy.
3. **Goryeo dùng 下出** (có hướng) và văn bản bổ sung của biên tập cần gán **provenance riêng** (nguồn/bản bất định).
4. Locator dạng `#0412a05` theo quy ước `lb@n` cục bộ CBETA — **không** ngầm coi là `xml:id`.
5. `link` chỉ định nghĩa **liên hệ chung**; `linkGrp` gom liên hệ; các bản ghi được chọn **không** khai báo vai trò thầy/đệ tử. `production_effect = none`.

### 2.1 Đối chiếu DILA live (first-hand, mở rộng mới)

Tra trực tiếp `authority.dila.edu.tw` cho 10 ID (không qua trung gian). **10/10 truy cập được (HTTP 200)**, lưu sha256 từng trang:

| ID | Tên DILA | `[老師]` (raw) | `[弟子]` (raw) | Ghi chú |
|---|---|---|---|---|
| A003634 | 省僜 (昭慶省僜) | 從展 | 筠, 靜 | `祖堂集:254`; Wikidata Q45569907 |
| A034920 | 靜 | — | — | Note: *《祖堂集》…靜、筠二禪德編著* |
| A034921 | 筠 | — | — | Note: *《祖堂集》…靜、筠二禪德編著* |
| A005612 | 荷澤神會 | 惠能, 顥元 | 無名, 福琳, 法如… | Wikidata Q712218; CBDB 143081 |
| A013914 | (太行山僧) | 神會, 洪思 | 惟忠 | T50n2061_p0893c21 |
| A004217 | (荊南惟忠) | 道願, 神會, 法如 | 道圓, 神照… | T50n2061_p0763c09 |
| A004166 | (道圓) | 惟忠, 釋南印 | **宗密** | T51n2076_p0301c02 |
| A000587 | 圭峰宗密 | 道圓, 澄觀 | 覺, 太恭… | 祖堂集:114; Wikidata Q3181701 |
| A003627 | 臨濟義玄 | 希運, 大愚 | 大覺, 延沼… | 祖堂集:362; Wikidata Q326950 |
| A004980 | (興化存獎) | 義玄 | 李存勗, 克賓… | 祖堂集:383 |

**Lưu ý hướng:** DILA ghi `[老師]/[弟子]` **theo nguồn** (vd `禪典‧禪宗法系譜`, `望月`), **không** theo quy ước `嗣` của ZTJ. Vì vậy đây là **provenance độc lập**, crosscheck để đọc — **không** đồng nhất với hướng nguồn ghi của dataset, **không** dùng để tự gán `directionality`.
`A034920`/`A034921` **không** có field `relationship` (quan hệ của họ với 省僜 nằm ở TEI, không ở hồ sơ DILA). **Không gộp nhân vật.**

**Đối chiếu khớp:** `A004166` DILA `[老師]惟忠 / [弟子]宗密` khớp TEI *遂州圓禪師**嗣**惟忠*; `A004980` `[老師]義玄` khớp TEI *興化和尚**嗣**林濟*. Đây là khớp **dữ liệu**, không phải suy hướng.

---

## 3. Khảo sát generation (deliverable 3)

- **49 giá trị phân biệt**: `0`..`48` (tần suất đầy đủ trong `source_value_frequencies`; cao nhất `47`:43 node, `43`:41, `44`:38).
- Trường: CSV `No. (Generations)` = giá trị generation của nguồn; `Generations & groups` = nhãn nhóm/tương quan (**24 nhãn**: 過去七佛, 天竺二十七祖, …).
- **Lệch CSV ↔ workbook (3 node)**: CSV ghi `0`, XLSX ghi `?`, cùng nhãn `不清楚 (慧能下第三代; 馬祖下第一代?)`:

| ID | Label | CSV (`No.`) | XLSX (`D`) |
|---|---|---|---|
| A027200 | 隱山 | `0` | `?` |
| A027195 | 興平 | `0` | `?` |
| A027242 | 米嶺 | `0` | `?` |

⇒ **Không quy đổi sang PTDA.** `generation_raw` giữ **nguyên văn**; `"0"` ≠ `"?"` ≠ nhãn `不清楚 (...)`. `ptda_conversion = none`, `raw_preserved = true`. Không cộng/trừ offset, không suy số đời.

---

## 4. Khảo sát uncertainty (deliverable 4)

| Tag | Số lượng |
|---|---|
| `<corr>` | 10 |
| `<sic>` | 8 |
| `<choice>` | 8 |
| `<supplied>` (reason=omitted/overlooked; cert=medium) | 3 |
| `<unclear>` (reason=damage; cert=low) | 1 |

**41 `linkGrp cert="low"`** — tất cả nằm trong `03-zutangji-haidongxinkaiyinbanji_SNA.xml`:

- **41 `<link>` bên trong** (mỗi nhóm đúng **1** link ⇒ `max_links_per_group = 1`).
- **15 locator phân biệt** trong `link@target` (0299b08–b14, 0300a01–a08).
- `ptr` endpoint: **43** giá trị phân biệt (gồm cả một số địa danh `PL…`).
- **Không** trùng locator với hai nhân chứng lệch (`#0300b07`, `#0412a05`) ⇒ không đụng nhánh edge-diff.
- CSV/XLSX/GEXF **không có cột bất định** (mất khi chuyển sang bảng số).
- **Số nhóm ≠ số cạnh.** `cert=low` là **tín hiệu độ tin cậy của nguồn**, không tự loại cạnh, không xác nhận hướng.
- Kiểm đếm **bắt buộc bỏ XML comment** (nếu không sẽ đếm nhầm 44 nhóm thay vì 41).

---

## 5. Rights matrix theo từng tệp (deliverable 5)

| Nguồn | Khai báo |
|---|---|
| Record (Zenodo metadata `license.id`) | **CC BY 4.0** |
| `01-README.md` (## License, dòng 47–48) | **CC BY 4.0** |
| `02-license.txt` | bản văn **CC BY 4.0** |
| 4 file TEI (`03-*.xml`, notice riêng dòng 36) | **CC BY-NC-SA 4.0** |

- `conflict_count = 4`; **4 dòng `unresolved = true`** (đúng 4 file TEI), lý do: khai báo gộp mâu thuẫn với record/README, chưa có văn bản giải thích từ nguồn.
- Tác giả/nguồn: creator **Laurent Van Cutsem**; editor/archiving **Marcus Bingenheimer**; dấu vết dẫn xuất: 6 báo cáo audit read-only (chỉ trích giá trị/locator, **không** đổi bản gốc).
- **`not_legal_clearance = true`** — **không** kết luận pháp lý, **không** tự cấp/chọn license.
- `scope_warning`: không gán license của package cho code ứng dụng, DB/TTL production, dữ liệu DILA hay tài nguyên không liên quan.

---

## 6. Kiểm tra 10 ID (deliverable 6)

- Đối tượng: đúng **union 10 person-endpoint** của các ca quan hệ (loại endpoint địa danh, vd `PL000000017888`).
- **10/10 match** với hồ sơ DILA (truy cập trực tiếp) — xem bảng §2.1; `inaccessible = 0`.
- **Cảnh báo identity:** `ptr target="#A######"` là **quy ước tham chiếu cục bộ** của package — **không** tự coi là `xml:id` đã giải quyết, **không** mint URI quyền; **không** match theo tên file.
- **`A003634` giữ CẢ HAI nhãn**: CSV `福先招慶` **và** TEI/GEXF `省僜`/`淨修禪師文僜`. **Không** gộp nhân vật, không hợp nhất nhãn.
- `A034920`, `A034921` **không** được đưa vào snapshot 260 node (vốn vắng mặt trong CSV/GEXF) — chỉ ghi nhận bằng chứng tra cứu.

---

## 7. Ánh xạ vào Đạo Ảnh — chỉ additive, staging, không ghi legacy

DB hiện có: `vn_person_authority` (**1.511** bản ghi; 114/260 ID dataset đã có, **146 mới**), `lineage_edge_assertions` (**57.175** cạnh **có hướng**), `vn_person_relations` (2.013). **Không** mutate các bảng này.

```sql
-- Staging node — KHÔNG ghi vào vn_person_authority
CREATE TABLE ztj_node_observation (
  observation_id          TEXT PRIMARY KEY,        -- DILA ID
  source_record           INTEGER NOT NULL,        -- 10004109
  source_article          TEXT NOT NULL,           -- 10.3390/rel14020205
  source_file             TEXT NOT NULL,
  label_zh                TEXT NOT NULL,
  generation_raw          TEXT,                    -- NGUYÊN VĂN: "7" / "0" / "?"
  generation_group_raw    TEXT,
  juan_raw                TEXT,
  ztj_entry_no_raw        TEXT,
  ztj_entry_chars_raw     TEXT,
  goryeo_preface_no_raw   TEXT,
  goryeo_preface_name_raw TEXT,
  goryeo_preface_ref_raw  TEXT,
  zan_jingxiu_raw         TEXT,
  country_origin_raw      TEXT,
  dila_already_present    INTEGER NOT NULL DEFAULT 0,
  mapping_verified        INTEGER NOT NULL DEFAULT 0,
  trust_level             TEXT NOT NULL DEFAULT 'source_asserted',
  status                  TEXT NOT NULL DEFAULT 'staged'
);

-- Staging edge — KHÔNG vào lineage_edge_assertions (nguồn vô hướng)
CREATE TABLE ztj_edge_observation (
  observation_id      TEXT PRIMARY KEY,            -- UUID nguồn
  source_record       INTEGER NOT NULL,
  source_file         TEXT NOT NULL,
  endpoint_a_dila     TEXT NOT NULL,
  endpoint_b_dila     TEXT NOT NULL,
  directionality      TEXT NOT NULL DEFAULT 'unasserted',
  relation_semantics  TEXT NOT NULL DEFAULT 'associated_with',
  ref_locator_raw     TEXT,                        -- 'B25n0144_#0299b08' nguyên văn
  cert                TEXT,                        -- 'low' nếu có; NULL ≠ chắc chắn
  mapping_verified    INTEGER NOT NULL DEFAULT 0,
  status              TEXT NOT NULL DEFAULT 'staged'
);
```

**Quy tắc bất di bất dịch:** `directionality='unasserted'` tới khi Admin duyệt · không suy `generation_order`/`dharma_lineage` từ `generation_raw` · không ghi đè `vn_person_authority` · locator giữ nguyên văn · edge staging **không** tự promotion vào `lineage_edge_assertions`.

---

## 8. Nguồn & bằng chứng

- `download-receipt.json`: ZIP 86.334.571 B, MD5 `78c722a304d06962a12f9899d5442e3e` **MATCHED**, SHA-256 `60d7c0333860a6ce4e76a82e3f08f6d4e943fc6def272108b2571139d648e811`, tải `2026-10-16T07:07:04Z`.
- 17 file trong `extracted/vancutsem_laurent/`.
- `analysis/phase3/test-results.json`: **40/40 PASS**.
- Truy vấn DILA first-hand: `analysis/phase2/dila_live/dila-live-lookup-20261016-final.json` + 10 HTML (sha256 từng trang).

---

## 9. Câu cần Admin quyết định

1. **DMCT không tồn tại trong repo** (`git grep -i dmct` → exit 1; không có trong tên file). Nếu bạn đang nói file khác, cho đường dẫn chính xác.
2. **Xung đột license:** (a) áp CC BY-NC-SA 4.0 cho toàn phần Van Cutsem; (b) tách theo file (bảng số CC BY, TEI NC); (c) không đưa TEI vào hệ thống. → `unresolved` giữ nguyên tới khi bạn quyết.
3. **146 node mới:** tạo `vn_person_authority` với `status='imported_unverified'`, hay giữ trong staging?
4. **Cạnh:** có cho phép suy hướng thầy→đệ tử bằng quy tắc không? (Tôi **không khuyến nghị** — 100% vô hướng, 3 node generation `?`, quy ước 嗣 ngược nhau.)
5. **Locator tra CBETA:** dataset trỏ 祖堂集 `B25n0144`; `cbeta.db` hiện chỉ có T1–T4, T14, T50, T51 ⇒ **chưa có**, phải import trước nếu muốn đối chiếu.

---

## 10. Trạng thái & việc chưa làm

- **Đã xong:** 6 deliverable (mở rộng đầy đủ), tra DILA live 10/10, báo cáo `-2.md` này.
- **Chưa viết migration production** — đúng yêu cầu.
- **Không** sửa DB/TTL/legacy; **không** import production; **không** tự `accepted`.

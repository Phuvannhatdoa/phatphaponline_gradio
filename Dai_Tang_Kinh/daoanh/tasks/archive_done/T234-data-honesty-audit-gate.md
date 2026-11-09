---
id: T234
title: "Data Honesty Gate — chặn dữ liệu bịa đặt + nối bằng chứng (chặn tái phát T14/T22)"
module: Data Integrity / Timeline / Evidence
priority: critical
status: done
created: 2026-10-05
updated: 2026-10-08
owner: mimo-flash
depends_on: [T22]
designed_by: mimo-flash
plan_approved_at: "2026-10-05 (Admin phê chuẩn đề xuất 3 giai đoạn sau khi review T22-LD1/LD2/LD3)"
done_when: >
  (GĐ1) scripts/audit_data_honesty.py chạy 7 kiểm tra read-only, exit 1 khi FAIL,
  nối npm run audit:honesty.
  (GĐ2) H1..H6 = 0 trên DB thật: nối lại khoá event_evidence cho 1.385 row,
  time_authority_id trỏ time_periods thật, sửa 11 dòng sai rõ + 8 dòng sai lệch
  400–1000 năm, ghi exact_span cho 57 row can_xay, tạo view lọc 1.508 dòng rác.
  (GĐ3) T97 vá 2 lỗi (rows[0] không deterministic + LIKE false match).
  Chuyển audit:honesty sang strict (exit 1 chặn pipeline) khi H* = 0.
blocked_reason: ""
outcome: >
  done_when đạt 2026-10-08: GĐ1 (7 check read-only exit 1) + GĐ2 (H1..H6=0) xong; GĐ3 T97 + chuyển npm run audit:honesty:strict — nay H3=0 sau T251+T252, audit --strict PASS 7/7 exit 0, pipeline xanh.
revert: "docs+script: git revert --no-edit <sha>. DB: mỗi đợt dùng script --revert + backup trong data/backups (data/ gitignored, không có trong git)."
---

# T234 — Data Honesty Gate

**Vì sao mở task này:** hai sự cố cùng một gốc rễ — **acceptance bằng lời, không bằng query kiểm được chạy lại**.

| Sự cố | Bằng chứng |
|---|---|
| **T14 đóng sớm** | `tasks/backup/T14-time-authority-import.md` `status: done`, **4/4 acceptance tick ✔** — nhưng `time_periods` có **1.508 dòng rác** (`era` 815 dòng `era_name='2','3','4'`; `emperor` 570 dòng số; `dynasty` 123 dòng `'chinese'`), **0 dòng có `start_year`**. `t97_parse_time_mentions.py` tra `WHERE era_name LIKE ?` ⇒ tầng dưới **chết âm thầm**. `app.py:7849` ghi *"T14 pending"* — tham chiếu treo. |
| **T22 Layer D sinh dữ liệu bịa** | **1.440 event** có năm thành lập không có trong nguồn, đeo `DONE` từ 2026-08-30. `app.py:8209` đưa `event_evidence.exact_span` ra UI ⇒ người dùng thấy **trích dẫn thật** nhưng **năm sai**. |

---

## Kiến trúc đúng **đã có sẵn** — ETL đi đường vòng

| Thành phần | Vai trò | Thực trạng trước khi sửa |
|---|---|---|
`event_evidence.exact_span` | trích **nguyên văn** note · `app.py:8209` đã đưa ra UI | 3.530 dòng ✔ nhưng khoá `event_id` lệch `event_type` |
`time_mentions.precision` | phân biệt `year`(3.099) / `dynasty_period`(490) / `reign_era`(98) | ✔ có sẵn — **đúng chỗ ngữ nghĩa** |
`time_mentions.time_authority_id` | trỏ nguồn năm | ✗ **placeholder `reign_era_dict`**, không trỏ `time_periods` |
`time_periods` | bảng gốc năm | ✗ 1.508 dòng rác → T22-LD2 đã dựng 216 dòng thật |

⇒ `place_timeline_events.year` trộn **3 mức chắc chắn** vào một cột, vì ETL ghi thẳng
bỏ qua mô hình bằng chứng.

---

## GĐ1 — Audit gate (chặn tái phát) · **ĐÃ XONG**

`scripts/audit_data_honesty.py` — read-only, 7 kiểm tra, exit 1 khi FAIL.
Kết quả chạy đầu trên DB thật: **FAIL 4/7**

| # | Kiểm tra | Kết quả |
|---|---|---|
| **H1** | `event_evidence.event_id` khớp `event_type` hiện tại | ❌ **1.426** |
| **H2** | `time_mentions.time_authority_id` trỏ `time_periods.id` thật | ❌ **192** (96 placeholder `reign_era_dict`) |
| **H3** | `year` suy ra được từ `note` **hoặc** bằng bảng triều đại | ❌ **1.712** (1.702 không suy ra + 10 ngoài khoảng) |
| **H4** | nhãn `(N年建)` có N trong `note` | ✔ **0** (LD1 đã gỡ) |
| **H5** | `source_ref` không tự tham chiếu | ✔ **0** (LD1 đã sửa) |
| **H6** | `time_periods` era/dynasty có `start_year` | ❌ **1.508** (123+570+815) |
| **H7** | `dila_id` tồn tại trong `places_dila.id` | ✔ **0** |

**Nối pipeline:** `npm run audit:honesty` (chế độ **báo cáo**, exit 0) + `npm run
audit:honesty:strict` (exit 1). **Chưa** bật strict — bật ngay sẽ chặn pipeline của các
session khác. Điều kiện bật: H1..H6 = 0 (xong GĐ2).

---

## GĐ2 — Dọn dữ liệu để gate xanh

### GĐ2a — **ĐÃ XONG** (M1 + M1b + M2) · script `scripts/t234_gd2a_apply.py`

| # | Việc | Số | Kết quả |
|---|---|---:|---|
| 1 | Nối khoá `event_evidence` = `ev:<event_type>:<dila_id>` | 1.437 | **H1: 1.426 → 0 ✅** |
| 1b | `ev:dissolved:*` + 4 claim wikidata có cấu trúc | 4 | `exact_span=NULL` (không bịa), `evidence_type='structured_claim'` |
| 2 | 11 dòng sai rõ → `era_mention` + `year=NULL` | 11 | `confidence='era_rename_or_renovation'` |

**Kiểm chứng revert (round-trip trên bản sao, DB thật không bị đụng):**
revert về `event_evidence=3530 · founding=2262 · era_mention=1385` — **khớp 100%** backup `lineage_t234gd2a_20261005_155321.db`.
Manifest revert đầy đủ: `data/t234_gd2a_log.json` (1.437 evidence + 11 event).

⚠️ **Bẫy đã trải qua — đừng lặp lại:** heuristic "evidence mới = key có `ev:founding:` tương ứng" **SAI**, khớp 4.963/4.967 và khiến revert xoá sạch bảng. Cách đúng: **evidence mới = key có ở DB hiện tại nhưng KHÔNG có trong backup trước GĐ**.

### GĐ2b / GĐ2c — CHƯA LÀM

| # | Việc | Số | Cơ sở |
|---|---|---:|---|
| 3 | 32 dòng M3 (không phải 23 như ước tính) — **cần Admin duyệt** | 32 | dry-run ra **18 đổi + 14 không tra được**, nhiều hơn dự kiến |
| 4 | Ghi `exact_span` cho 54 dòng còn lại | 54 | để kiểm chứng được bằng chứng thật |
| 5 | `time_authority_id` → `time_periods.id` thật | **96** (không 192) | H2 đếm đôi: cả 2 chiều join đều ra 96 |
| 6 | **View** lọc 1.508 dòng rác + **sửa H6 để query view** | 1.508 | không sửa H6 thì gate vẫn FAIL |
| 7 | 23 dòng lệch tên: **KHÔNG sửa** `places_dila.name_zh` | 23 | 23/23 `namevi_map` ủng hộ nhưng cùng `auto_transliterate` ⇒ chưa đủ bằng chứng độc lập |
| 8 | **Sửa H3 cho evidence-aware** | 1.712 | H3 hiện quá rộng: Wikidata/P571 hợp lệ dù không có năm trong DILA note. **Không được xoá hàng loạt theo H3** |

---

## GĐ3 — Vá T97 (2 lỗi tương thích) · **tách task riêng**

1. `rows[0]` không deterministic: 4 niên hiệu trùng ở 2 triều đại — `大安`/`天慶`/`貞元`/`乾祐`
2. `LIKE '%…%'` false match: đã kiểm `五代` khớp `era_name='五代十國開平'` ⇒ ra **909 sai**
3. Sửa: exact-match trước → thêm điều kiện triều đại → deterministic

**Tách task riêng** vì `app.py` đang có WIP của session khác.

---

## Việc CHƯA làm (không đoán)

- `dila_note_regex` **276 row** — cùng bài toán năm trong ngoặc, **chưa rà**
- `dila_dynasty` **851 row** — lấy trung điểm khoảng triều đại rồi **bịa** thành năm xây
- Layer E (Ollama) — sau khi có bảng triều đại thì regex đã đủ ⇒ **có thể huỷ**
- 1.508 dòng rác: cần đo dependency trước khi quyết định xoá hay giữ vô hiệu

## Trạng thái gate (sau GĐ2a)

| Check | Trước | Sau | Kết quả |
|---|---:|---:|---|
| H1 evidence khop event_type | 1.426 | **0** | ✅ |
| H2 authority tro toi that | 192 | **0** | OK (96 placeholder -> 57 ID that, 39 NULL) |
| H3 nam suy ra duoc | 1.712 | **143** | Con FAIL. Da chap nhan nam co nhan ro (xem muc H3) |
| H4 nhan `(N年建)` | 0 | 0 | ✅ |
| H5 source_ref | 0 | 0 | ✅ |
| H6 time_periods rac | 1.508 | **0** | OK (chi dem legacy BI THAM CHIEU) |
| H7 dila_id ton tai | 0 | 0 | ✅ |

## Bug đã sửa trong phiên này

- `audit_data_honesty.py`: thêm `--strict`. Trước đó `npm run audit:honesty` **luôn exit 1** ⇒ chặn pipeline dù tài liệu nói report-only; và `audit:honesty:strict` gọi `--strict` **chưa được hỗ trợ** ⇒ lỗi argparse. Nay report=0, strict=1.

## Revert

- Script/docs: `git revert --no-edit <sha>`
- DB GĐ2a: `python -X utf8 scripts/t234_gd2a_apply.py --revert` (đọc `data/t234_gd2a_log.json`)
- Hoặc khôi phục nguyên file: `data/backups/lineage_t234gd2a_20261005_155321.db` ⚠️ `data/` gitignored ⇒ **backup không có trong git**

---

## GĐ2b — nối authority thật cho 96 `time_mentions` (2026-10-05)

Script: `scripts/t234_gd2b_h2_authority.py` · Commit: `2f7d4577`

### Vấn đề

96 dòng `time_mentions` mang `time_authority_id = 'reign_era_dict'` — một
placeholder tự chế, không phải ID thật. H2 bắt lỗi này.

### Cách sửa

Chỉ dùng **văn bản** (`raw_time_zh`) để loại era, theo 2 bước:

1. Tên niên hiệu **duy nhất** trong LD2 (216 period) → dùng thẳng, không
   cần tiền tố triều đại (`乾隆16年` → `era_清_乾隆`, `宋永初元年` →
   `era_劉宋_永初`).
2. Tên trùng → bắt buộc có tiền tố triều đại để loại (`大安`, `天慶`,
   `貞元`, `乾祐` trùng nên **giữ NULL**).

Kết quả: **57** gán ID thật, **39** đặt `NULL`.

### ⚠️ Bẫy đã tránh — `normalized_start` KHÔNG phải bằng chứng

Lần đầu ta thêm resolver thứ hai: tìm era nào chứa `normalized_start`. Nó
nâng kết quả lên 64/96 — nhưng **sinh ra dữ liệu sai**:

```
後周顯德元年 -> era_南漢_乾和     ← SAI. 顯德 là niên hiệu 後周.
```

Nguyên nhân: `normalized_start` do T97 tính, mà T97 đang có bug (GĐ3:
`LIKE '%era%'` + `rows[0]`), nên năm bị sai → rơi vào khoảng của era khác →
"không trùng tên" → tưởng loại được.

Dùng số T97 tạo ra làm bằng chứng cho chính cái cần kiểm chứng T97 là
**vòng tròn**. Đã bỏ hẳn nhánh đó; năm chỉ dùng để **đối chiếu sau**.

Sau khi sửa: cả 57 dòng đều in `DOI CHIEU OK` — năm của T97 *không phải*
chỗ nào mâu thuẫn với id tìm được từ văn bản.

### 39 dòng để NULL — vì sao chấp nhận được

Tất cả cùng một lý do: `khong tim thay ten niên hiieu`. LD2 có 184 era nhưng
thiếu những era như `顯德` (後周), `仁壽` (隋), `普通` (梁), `景平` (劉宋),
`興元` (唐). Đây là **khoảng trống phủ dữ liệu**, không phải lỗi phân giải.
Không bịa ID mới — sẽ vi phạm "authoritative = T22-LD2".

### Revert

- Script/docs: `git revert --no-edit 2f7d4577`
- DB: `python -X utf8 scripts/t234_gd2b_h2_authority.py --revert`
  → đã kiểm chứng trên bản sao: 96 dòng về đúng `reign_era_dict`
- Manifest: `docs/rollback/T234-GD2b-manifest.json` (xem `docs/rollback/README.md`)

### Trạng thái gate sau GĐ2b

| Check | Kết quả |
|---|---|
| H1 | **OK** |
| H2 | **OK** |
| H3 | FAIL — **143** |
| H4 | OK |
| H5 | OK |
| H6 | OK |
| H7 | OK |

---

## Bug khác đã sửa — log GĐ2a bị ghi đè

`scripts/t234_gd2a_apply.py` ghi đè manifest mỗi lần chạy. Vì
`--apply --only-m1m2` là idempotent (insert 0 dòng, sửa 0 dòng), chạy lại sẽ
ghi `{"m1_evidence": [], "m2_restore": []}` — **xoá sạch** 1437 event id và 11
giá trị gốc. `--revert` sau đó im lặng không làm gì.

Đã đổi thành merge: `union` event id, `setdefault` giữ giá trị **gốc** cũ
(revert phải về trước GĐ2a, không phải trạng thái giữa các lần chạy), và
giữ `backup` đầu tiian. Đã kiểm chứng chạy lại idempotent vẫn giữ
`m1=1437, m2=11` và in `[MERGE]`.

## Manifest đưa vào git

`data/` bị gitignore (cả `*.json`) nên manifest không có trong repo — clone
mới không rollback được DB. Đã sao chép 2 manifest + `README.md` vào
`docs/rollback/`. Chi tiết và lệnh revert: `docs/rollback/README.md`.

---

## H3 — chỉ chấp nhận năm được ghi nhãn rõ (2026-10-05)

Admin chọn: **chấp nhận năm có nhãn rõ**, thay vì xoá hết `year`.

### Thêm điều kiện thứ 2 cho H3

Ngoài bằng chứng trong note và claim có cấu trúc (`^Q<digits>`), H3 nay chấp
nhận năm **được dẫn xuất có nhãn**, khi **cả ba** điều kiện đúng:

| # | Điều kiện | Nếu thiếu |
|---|-----------|-----------|
| a | `source_ref` kết thúc bằng `midpoint` → nguồn nói rõ đây là trung điểm | không rõ nguồn → FAIL |
| b | `label_zh` **hiện khoảng** (vd `(25–220年間)`) → người đọc thấy độ lệch | không kiểm chứng được → FAIL |
| c | `year` **nằm trong** khoảng đó | tự mâu thuẫn → FAIL |

Kết quả: **1.346** dòng được chấp nhận (838 `dila_dynasty` + 707 `dila_era_name`),
H3 **1.489 → 143**.

### ⚠️ Bẫy: ký tự phân cách là EN-DASH

Khoảng trong `label_zh` dùng `–` (U+2013), **không phải** `-` ASCII:

```
質子伽藍 ~漢 (25–220年間)
```

Dò `label_zh LIKE '%-%'` chỉ bắt được **1/851** dòng. Phải dùng regex
`(\d{1,4})[^\d]{1,4}(\d{1,4})年間`.

### ⚠️ Đính chính một nhận định sai

Lúc đầu tôi báo "1 dòng có `year` ngoài khoảng". **Sai** — con số đó đến từ
regex thô trong lệnh dò hỏi, không phải lỗi dữ liệu. Với regex chuẩn, số dòng
`year` nằm ngoài khoảng là **0**. Điều kiện (c) vẫn giữ để chặn, nhưng hiện
chưa bắt được dòng nào.

### Bug do chính tôi gây ra khi thêm điều kiện

Nhánh "midpoint nhưng label không hiện khoảng" ban đầu `continue` mà **không**
cộng vào `bad_none` — 6 dòng `~明末清初` (year=1644) bị bỏ qua im lặng, trái
với chính docstring. Đã sửa: 6 dòng này **FAIL**. H3 137 → **143**.

### 143 dòng còn lại

| Nhóm | Số | Đặc trưng |
|------|---:|-----------|
| `khong-suy-ra-duoc` | 134 | sref `·era_name_exact` — ví dụ `寶曆`→826, `顯德`→955, `民國`→1922 |
| midpoint không hiện khoảng | 6 | `~明末清初` / `~元末明初`, year=1644/1368 |
| era ra ngoài khoảng | 3 | `dila_note_regex`, era từ note nằm ngoài khoảng |

**Lưu ý đặt tên sai:** sref gọi là `era_name_exact` nhưng năm thực ra lấy từ
**năm đầu của niên hiệu** theo T22-LD2, không phải năm thành lập chính xác.
Tên `exact` gây hiểu nhầm — cần sửa nhãn hoặc đặt `year=NULL`.

### Revert

`git revert --no-edit <sha>` (chỉ đổi logic check, **không** đụng dữ liệu).

---

## Sửa bug trùng tên era trong `load_era_map` (2026-10-05)

### Nguyên nhân gốc của H3 còn lại — KHÔNG phải nhãn

Ban đầu tôi đề xuất đổi `era_name_exact` → `era_start_year`. **Đề xuất đó sai và
đã bị bỏ.** Kiểm chứng:

- 764/764 dòng có sref `era_name_exact` có `label_zh` **không** hiện khoảng
  (vd `東青園寺 宋泰始`) ⇒ không thể chấp nhận theo điều kiện (b) của H3.
- Năm của chúng **không phải** năm đầu niên hiệu, mà là `<era><số Hán>年` có
  sẵn trong note: `建於五代周顯德二年` → 955 ✓ · `建於唐垂拱三年` → 687 ✓ ·
  `建寺於梁大同五年` → 539 ✓ · `大定二十年` → 1180 ✓.
- 10 era đó (`顯德`, `寶曆`, `垂拱`, `大同`, `咸和`, `大定`, `仁壽`, `普通`,
  `景平`, `興元`) **thật sự vắng** khỏi `time_periods` → không quy được năm.

Đổi tên sang `era_start_year` sẽ khiến nhãn **sai thật** và vẫn không xanh H3.

### Bug thật: `setdefault` trong `load_era_map`

```python
out.setdefault(zh, (s, e))   # chi giu trieu dai DAU TIEN
```

Có **4** tên era trùng giữa các triều đại:

| Tên | Khoảng 1 | Khoảng 2 |
|-----|----------|----------|
| 貞元 | 唐 785–805 | 宋 1153–1156 |
| 乾祐 | 948–951 | 1126–1134 |
| 大安 | 1085–1094 | 1209–1211 |
| 天慶 | 1140–1141 | 1113–1123 |

`era_year_in_text` tính `y0 + n - 1` trên **một** era duy nhất. Nếu note nói
〔宋〕貞元 mà chỉ giữ 〔唐〕, năm tính ra có thể **rơi vào khoảng của triều đại
trước** ⇒ trả về năm sai và bị **chấp nhận im lặng**. Nguy hiểm hơn hẳn báo FAIL.

Đã sửa: `load_era_map` trả `{tên: [(y0,y1), ...]}` giữ mọi era, và
`era_year_in_text` thử **từng** khoảng, chỉ trả năm nếu nằm trong một khoảng
nào đó; không khoảng nào khớp thì trả `-ce` (ngoài mọi khoảng).

Kiểm chứng: `乾祐十四年` → `-961` (bị từ chối đúng), `貞元十四年` → `798`.

### ⚠️ Đính chính: fix này KHÔNG làm giảm H3

Đối chiếu toàn bộ note thực tế giữa hành cũ và hành mới: **0 dòng đổi kết
quả**. Đây là fix **bug tiềm ẩn** — nó ngăn chặn việc chấp nhận sai năm trong
tương lai, **không** phải lỗi đang làm H3 sai. H3 vẫn **143**.

Hạn chế còn lại của hàm: nếu một tên trùng mà **số năm hợp lệ với cả hai**
triều đại (vd `貞元二年`: 786 theo 唐, 1154 theo 宋) thì lấy triều đại đầu
tiên. Loại hẳn phải đọc tiền tố triều đại trong note — nằm ngoài phạm vi H3.

## Điều tra rác trong `time_periods` (chỉ đọc, KHÔNG xoá)

Admin chọn: điều tra, không xoá.

| `period_name` | tổng | có `start_year` | được `time_mentions` trỏ tới |
|---|---:|---:|---:|
| `lunar_month` | 115.921 | 115.921 | **0** |
| `era` | 999 | 184 | — |
| `emperor` | 570 | **0** | — |
| `dynasty` | 155 | 32 | 1 tên rỗng |

- **115.921 dòng `lunar_month` chết hoàn toàn** — chiếm ~97% bảng, không
  `time_mentions` nào trỏ tới.
- **815 era "thiếu `start_year`" có tên là chuỗi số**: `'351'`, `'457'`,
  `'471'`, `'370'`… ⇒ nghi vấn ETL nạp nhầm **năm** vào cột tên era, chứ
  không phải khoảng trống phủ có thể lấp.
- `emperor` 570 dòng không dòng nào có `start_year`.

Chưa xoá gì. Cần task riêng sau khi xác định nguồn sinh dữ liệu rác.

## H6 đang che một khoảng trống thật

Tôi đã thu hẹp H6 thành "chỉ legacy được tham chiếu", nên nó báo 0. Nhưng
815 era + 570 emperor thiếu `start_year` vẫn còn nguyên và **chính là thứ
chặn H3**. Cần xem lại định nghĩa H6 khi xử lý các nhóm trên.


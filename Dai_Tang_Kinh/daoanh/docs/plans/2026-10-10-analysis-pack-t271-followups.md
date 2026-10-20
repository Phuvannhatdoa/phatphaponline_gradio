# Analysis Pack — 5 Follow-up items của T271 (chờ Admin duyệt từng lô)

Ngày: 2026-10-10. Trạng thái: **ĐÃ ÁP DỤNG một phần (2026-10-10, Admin đã phê duyệt từng lô)**.
- ✅ **Lô B (Mục 2), Lô D (Mục 4, phương án D2), Lô E (Mục 5)** → **ĐÃ GHI DB** (backup
  `data/backups/2026-10-10-lot-B-D-E/backup_lotBDE_20261010_170854.sql`).
- ✅ **Lô C / Lô Ca (Mục 3)** → **ĐÃ GHI DB 2026-10-10** (Admin "Đồng ý build"; backup
  `data/backups/2026-10-10-lot-C-Ca/backup_lotCCA_20261010_184438.sql`) + **nới regex W1a** (code).
  Sau đó audit lộ **H1=357** (pre-existing, không do Lô C/Ca) → **ĐÃ sửa additive** (backup
  `data/backups/2026-10-10-H1-evidence/`). `audit:honesty:strict` nay **PASS 7/7**.
- ⏳ **Lô A (Mục 1)** → thuộc `T213` (pending, READ-ONLY).
Đây là tài liệu quyết định (decision pack) cho 5 follow-up trong `tasks/T271-t202-post-review-revision.md` §8.
Không cấp ID task mới ở đây; giao việc, đổi `status` và ghi DB **chỉ sau khi Admin duyệt từng lô**
(revertible, kèm backup `data/backups/`).

Nguồn dữ liệu: đọc trực tiếp `data/lineage.db` (read-only, `mode=ro`), ngày 2026-10-10.
Toàn bộ các con số dưới đây có thể tái kiểm bằng lệnh trong mục 9.

---

## 0. Bảng thông tin đọc nhanh

| Mục | Số row | Trạng thái hiện tại | Lô cần duyệt | Ghi DB |
|---|---|---|---|---|
| 1 — Orphans VNPA `dila_id=''` | **210** `''` + **1** `NULL` (=211) | `pending` hết, có `ttl_filename` TS-… | Lô A (thuộc T213, READ-ONLY classification) | — T213 |
| 2 — 4 nhóm trùng | 4 nhóm / 8 row | `alias_vi_suffix`/`auto_ttl` cạnh `verified` | Lô B | ✅ ĐÃ GHI |
| 2 — A010511 zh rác | 1 row | `zh='畲山兒無所知年年斫斷青山'` | Lô B | ✅ ĐÃ GHI |
| 3 — H3 `year` không suy được | **23** (→ **0**) | ~~audit FAIL~~ **PASS** | Lô C | ✅ ĐÃ GHI |
| 3 — H4 `(N年建)` nhãn bịa | **591** (→ **0**) | ~~audit FAIL~~ **PASS** | Lô Ca | ✅ ĐÃ GHI |
| — — H1 evidence lệch event_type | **357** (→ **0**) | ~~audit FAIL~~ **PASS** | (H1, ngoài pack) | ✅ ĐÃ GHI |
| 4 — PL000000000001 canonical | 1 row | `auto_transliterate`/`needs_review` | Lô D | ✅ ĐÃ GHI |
| 5 — A021395→A036842 alias sai | 2 row | `alias_A021395`, `alias_A000733` | Lô E | ✅ ĐÃ GHI |

**Nguyên tắc xuyên suốt:** không xóa row (giữ lịch sử); mọi UPDATE gom nhóm đều add-back bằng backup;
H3/H4 chưa sửa thì `npm run pipeline` vẫn bị `audit:honesty:strict` chặn (đã kiểm chứng T271).

---

## 1. Mục 1 — 211 orphan VNPA (dila_id rỗng) → T213

**Sự thật được kiểm chứng (khác mô tả gốc):**
- `SELECT COUNT(*) WHERE dila_id=''` = **210** (T213 ghi 211 — lệch 1).
- Còn **1 row `dila_id IS NULL`** = `tang_chu_pho_dung` (Tạng Chủ Phổ Dung, TS-Tang-Chu-Pho-Dung) → tổng **211** = 210 `''` + 1 `NULL`.
- Cả 211 đều `status='pending'` và có `ttl_filename` TS-… riêng (vd Cs-Banh-Nhu-Lam, Cs-De-Hinh-Quach-Tuong-Chanh, …).

**Quyết định cần: KHÔNG cần ở pack này.** Đây đúng phạm vi `tasks/T213-vnpa-orphan-211-classification.md`
(pending, READ-ONLY). Dữ liệu đầy đủ 211 row đã lưu tại `%TEMP%\opencode\apack\1_orphans.json` (210 row).
Một chỗ cần Admin chốt: **T213 đang mô tả sai số "211 row `dila_id=''`"** → đề nghị sửa T213 thành
"210 `''` + 1 `NULL`" khi chạy classification.

**Hành động:** không ghi DB trong pack này. Chạy classification theo T213 (buckets A/B/C/D), báo Admin.

---

## 2. Mục 2 — 4 nhóm trùng + zh rác A010511 (Lô B) — ✅ ĐÃ GHI 2026-10-10 (Admin "Mục 2: ok")

### 2a. Bốn nhóm trùng (đã verify từng cặp)

| Nhóm | Row phụ (status) | Row chính (status) | Diễn giải |
|---|---|---|---|
| A003623 | `alias_A003623` Mã Tổ Đạo Nhất (`alias_vi_suffix`, zh=馬祖道一, cùng ttl) | `ma_to_dao_nhat` Mã Tổ Đạo Nhất (`verified`, zh=馬祖道一, ttl TS-Ma-To-Dao-Nhat) | alias gần như trùng tuyệt đối, **tên zh của alias đúng** |
| A003636 | `phuc_chau_dai_an` Phúc Châu Đại An (`auto_ttl`, ttl **trống**, zh **trống**) | `phuoc_chau_dai_an` Phước Châu Đại An (`verified`, zh=福州大安, ttl TS-Phuoc-Chau-Dai-An) | alias "Phúc" thừa, thiếu ttl/zh; main "Phước" đúng (福州大安) |
| A004697 | `alias_A004697` Vô Chuẩn Sư Phạm (`alias_vi_suffix`, zh=**師範**—sai 1 phần) | `vo_chuan_su_pham` Vô Chuẩn Sư Phạm (`verified`, zh=無準師範, ttl TS-Vo-Chuan-Su-Pham) | main zh đầy đủ; **alias zh thiếu chữ 無準 → 師範 là tên mốc, không phải tên đủ** |
| A021287 | `alias_A021287` Thạch Sương Tông Giám (`alias_vi_suffix`, zh=宗鑑, ttl TS-…) | `thach_suong_tong_giam` Thạch Sương Tông Giám (`auto_ttl`, **zh trống**, ttl TS-Thach-Suong-Tong-Giam) | main zh trống nhưng có ttl; alias có zh=宗鑑 |

Quy ước hiện có trong DB: row `alias_<id>` + `status='alias_vi_suffix'` là *phương án tên* gắn cùng
một `dila_id`, KHÔNG phải entity riêng. `verified` = đã chốt. So với bản duyệt A001984 (canonical_decision):
**cách hành xử đúng hiện hành là KHÔNG xóa/không flip 450 alias — thêm row canonical_decision nếu cần.**

**Đã ghi DB (additive, revertible — backup `backup_lotBDE_20261010_170854.sql`):**
```sql
UPDATE vn_person_authority SET name_zh='無準師範' WHERE id='alias_A004697';   -- 1 row
UPDATE vn_person_authority SET name_zh='宗鑑'    WHERE id='thach_suong_tong_giam' AND (name_zh IS NULL OR name_zh=''); -- 1 row
UPDATE vn_person_authority SET name_zh=''        WHERE id='nam_nhac_huyen_thai';   -- xóa rác zh, 1 row
```
KHÔNG thêm canonical_decision cho `phuoc_chau_dai_an`/A010511 ở lần này (schema `entity_ref`
dùng dila_id — ví dụ A001984 ↔ row `alias_A001984` — chưa có tiền lệ cho 4 nhóm; tránh ghi thiếu căn cứ).
`ma_to_dao_nhat` (verified) + `alias_A003623` giữ nguyên. `alias_A003636` (Phúc) giữ nguyên.

**Đề xuất Lô B (ghi DB, revertible):**
1. `alias_A003636` → không hợp lệ (trùng Phước Châu Đại An, thiếu ttl/zh): đổi `status` → `alias_zh_match`
   (chờ Admin) HOẶC giữ nguyên và chỉ tạo canonical_decision cho `phuoc_chau_dai_an`. **Chọn: thêm
   canonical_decision, không touch alias status.**
2. `alias_A004697` zh `師範` → sửa thành `無準師範` (căn main + TTL). **Chọn: UPDATE name_zh của alias cho khớp main.**
3. `thach_suong_tong_giam` zh trống → điền `宗鑑` từ chính alias. **Chọn: UPDATE name_zh main = 宗鑑.**
4. `ma_to_dao_nhat` → đã verified; `alias_A003623` giữ nguyên.

### 2b. A010511 — zh rác trên `nam_nhac_huyen_thai`

`nam_nhac_huyen_thai` (Nam Nhạc Huyền Thái, pending, ttl TS-Nam-Nhac-Huyen-Thai) có
`name_zh = '畲山兒無所知年年斫斷青山'` — đây là **мột câu thơ/thiền kệ**, không phải tên người.
Hai row cùng dila A010511 khác (`dam_chau_bao_cai_uoc`, `the_nham_ton_tho`) đều zh trống.
A010511 thực tế là nhiều người khác nhau đang dính chung 1 dila_id — **cần tách** (thuộc dòng A010511
khác biệt, không gộp).

**Đã ghi DB:** `UPDATE vn_person_authority SET name_zh='' WHERE id='nam_nhac_huyen_thai'` (1 row; `canonical_decision` note về tách A010511 chưa thêm vì lý do nêu trên).

### 2c. Áp dụng thực tế

Đã thực hiện đủ 3 sửa name_zh (rowcount 1/1/1). Verify sau: `alias_A004697` zh=`無準師範`;
`thach_suong_tong_giam` zh=`宗鑑`; `nam_nhac_huyen_thai` zh rỗng.

---

## 3. Mục 3 — H3 (23 row) + H4 (591 row) — ✅ ĐÃ GHI 2026-10-10 (Admin "Đồng ý build")

**Kết quả:** Lô C (thêm 17 era) → nhóm 1 xong. Nhóm 2 (4 row số Ả Rập) + 2 row `會昌5年`
→ **nới regex W1a** (`cn2int` đọc `[0-9]`; `era_year_in_text`/`era_year_exact` nhận `[0-9]{1,4}`)
→ H3 = 0. Lô Ca strip 596 row (`[（(]N年建[)）]`) → H4 = 0. Backup
`data/backups/2026-10-10-lot-C-Ca/backup_lotCCA_20261010_184438.sql`.
Chi tiết: `docs/sessions/2026-10-10_T271-lot-CCa-h1.md`.

### 3a. H4 trước (591 row) — nhãn bịa từng được "DONE"

Nguyên gốc: **T22 Layer D** sinh 1.440 event có năm thành lập **không trong nguồn**, nhãn ghi `(NNN年建)`.
`audit_data_honesty.py H4` = `label_zh LIKE '%年建%'` và số `(N年建)` không tồn tại trong `note` ⇒ **591 row FAIL**.
Mỗi row là 1 event đã có `dila_id` (591 distinct id), vd:
`PL000000000173 東青園寺 宋泰始 (465年建)` — note không chứa "465".

**Đề xuất Lô Ca (additive, revertible — chỉ 1 cột label):**
```sql
-- backup truoc khi chay, tung batch 100 row
UPDATE place_timeline_events
   SET label_zh = trim(replace(label_zh, '(' || substr label_map.year_n || '年建)', ''))
 WHERE label_zh LIKE '%(____年建)%' AND dila_id IN (...);
```
→ thực tế viết theo từng `year_n` đã scan (file `4_h4_fail.json`). Sau cùng chạy Lô Ca xong:
`label_zh` còn tên chùa + niên hiệu, **bỏ hẳn mệnh lệnh "N年建" bịa** ⇒ H4 = 0.

**Không làm:** xóa event, đổi `year`, sửa `note`.

### 3b. H3 (23 row) — `year` không suy ra được

Cả 23 row đều `source_ref` dạng `…·<era>·era_name_exact` (T22). Hai nhóm nguyên nhân:

**Nhóm 1 (19 row): era KHÔNG tồn tại trong `time_periods` (loại era) ⇒ không tính được năm.**
Các era thiếu: `太極, 廣順, 仁壽, 景平, 太元, 咸安, 景福, 永定, 光化, 靖康, 廣德, 景雲, 永淳, 中統, 建興, 永和`
(đã verify: chỉ `武德, 大中, 光緒` có trong bảng; 16 era còn lại MISSING). Nhưng **note có ghi era + số Hán**
(vd `唐太極元年建`, `周廣順二年建`), và `audit` có cơ chế W1 quy `(<era><số Hán>年)` → năm. ⇒
**Thiếu era bảng triều đại, không thiếu bằng chứng trong note.**

**Đề xuất Lô C (additive):** thêm 16 era vào `time_periods` (loại `era`, `period_name='era'`) với
`start_year/end_year` chính xác (lấy từ lịch sử đối chiếu, tạm ghi nguồn "era_catalog"): ví dụ
`太極 712–712`, `廣順 951–953`, `仁壽 601–604`, `景平 423–424`, `太元 376–396`, `咸安 371–372`,
`景福 892–893`, `永定 557–559`, `光化 898–901`, `靖康 1126–1127`, `廣德 763–764`, `景雲 710–711`,
`永淳 682–683`, `中統 1260–1264`, `建興 313–317` (cần xác minh thêm — xem lưu ý), `永和 345–356`.

**Nhóm 2 (4 row): era CÓ nhưng note dùng CHỮ SỐ Ả RẬP, W1 không đọc được.**
`武德7年`(618+6=624), `大中5年`(851), `永定3年`(559), `光緒33年`(1907) — regex W1 chỉ nhận số Hán.
⇒ 4 row này **đòi nới regex** (code) — cần Admin duyệt: mở rộng `era_year_in_text` đọc `[0-9]{1,4}` sau era
(kèm W1a vẫn phải khớp năm đã lưu hoặc nằm trong khoảng era). Nếu Admin lo ngại tiếp tay bịa: giữ H3 char-list
và coi 4 row là "chưa xử" — nhưng khi đó pipeline vẫn đỏ 4 row.

**Lưu ý trùng: 1 row `建興`** — "建興" có nhiều triều (Tây Tấn 313–317, Thành Hán 304…), note ghi `晉建興二年`
nhưng `year=266` (265–266?), mâu thuẫn. Row PL000000058135 聖像寺 → **đề xuất Admin tự xem lại**, đưa vào
nhóm bàn tay (không cố auto).

### 3c. Thứ tự: Lô C (era) → Lô Ca (label) → chạy audit → H3 còn ≤5, H4=0

Sau khi có Lô C + Lô Ca, `npm run pipeline` mới hy vọng xanh (còn H3 nhóm 2 nếu không nới regex).

---

## 4. Mục 4 — PL000000000001 canonical (Lô D)

- `places_dila.PL000000000001`: `name='闊悉多國'`, `name_zh='闊悉多國'`, `name_en='Khost'`, geo 36.55N/67.86E (Afghanistan, PLA000002).
- `canonical_decision` hiện: `canonical_name_vi='Khoát Tạt Đa Quốc'`, `authority_rank=auto_transliterate`,
  `verification_status=needs_review`, `decision_note='Auto-generated…'`, `editor='auto-tester'`.
- Nguồn tự sinh 2026-08-30; chưa có editor người duyệt.

**Quyết định Admin (1 trong 2):**
- **(D1)** — không chọn.
- **(D2, ĐÃ CHỌN & GHI DB 2026-10-10):** đổi tên + verify:

```sql
UPDATE canonical_decision SET canonical_name_vi='Khoát Tất Đa Quốc',
       verification_status='verified', authority_rank='admin_approved', editor='admin',
       decision_note='Admin phe duyet 2026-10-10: ten Hán Viet chuan cua 闊悉多 = "Khoát Tất Đa" (tu dong sinh "Khoát Tạt Đa" sai chu Tạt; 悉=Tất, xem Tất Đạt Đa 悉達多). DILA name_en=Khost, name_jpn=カスタ; co dia 睹貨邏, Đong-Bac Afghanistan (大唐西域記 T51n2087 q.12).'
 WHERE entity_ref='PL000000000001';
```

Kèm backup row trước khi update. Revert: khôi phục row từ backup.

---

## 5. Mục 5 — A021395 → A036842 (Lô E)

Thực trạng (đã verify):
- `alias_A021395` = "Ngũ Tổ Pháp Diễn", zh `法演`, `dila_id='A021395'` — **SAI**.
- `alias_A000733` = "Ngũ Tổ Pháp Diễn", zh `法演`, `dila_id='A000733'` — **SAI**.
- Main `ngu_to_phap_dien` = "Ngũ Tổ Pháp Diễn", zh 法演, ttl TS-Ngu-To-Phap-Dien, `dila_id='A036842'` (đúng T212/T218).
- `person_display_names` (A036842): verified_direct, source `data/ttl/Lam Te Duong Ky/TS-Ngu-To-Phap-Dien.ttl`,
  `authority_name_zh='法演'` ⇒ **DILA thật của 法演 = A036842**.

Vậy 2 alias đang trỏ vào A021395 và A000733 là **ánh xạ sai**. T212/T218 đã chốt → A036842.

**Đã ghi DB 2026-10-10 (Admin "Mục 5: ok") — KHÔNG đụng main `ngu_to_phap_dien`:**
```sql
UPDATE vn_person_authority SET dila_id='A036842' WHERE id IN ('alias_A021395','alias_A000733');
```
(1 row mỗi id; verify sau: 2 alias `name_zh='法演'` đều `dila_id='A036842'`. Kiểm sau:
`SELECT id,dila_id,name_zh FROM vn_person_authority WHERE id LIKE 'alias_%' AND name_zh='法演'`. Revert = set lại `A021395`/`A000733`.)

---

## 6. Bảng tổng các lô + mức mất dữ liệu khi revert

| Lô | Hành động | Loại | Mất dữ liệu nếu revert? | Trạng thái |
|---|---|---|---|---|
| A | T213 classification (READ-ONLY) | none | 0 | ⏳ T213 |
| B | update name_zh (alias_A004697, thach_suong_tong_giam) | additive | 0 (restore từ backup) | ✅ ĐÃ GHI |
| Ba | xóa zh rác A010511 | additive (string) | 0 | ✅ ĐÃ GHI |
| C | thêm 17 era vào time_periods | additive (INSERT) | 0 — DELETE 17 row theo nguồn | ✅ ĐÃ GHI |
| Ca | bỏ `(N年建)` ở label_zh 596 row | UPDATE cột label | label gốc chỉ còn trong backup | ✅ ĐÃ GHI |
| — | H1: INSERT 357 event_evidence (ngoài pack) | additive (INSERT) | 0 — DELETE 357 id theo `h1_revert.sql` | ✅ ĐÃ GHI |
| D | PL000000000001 verify + đổi tên "Khoát Tất Đa Quốc" | UPDATE canonical_decision | 0 (backup row) | ✅ ĐÃ GHI |
| E | alias dila_id → A036842 | UPDATE 2 row | 0 (set lại id cũ) | ✅ ĐÃ GHI |

**Revert 3 lô đã ghi:** chạy file `data/backups/2026-10-10-lot-B-D-E/backup_lotBDE_20261010_170854.sql`
(INSERT OR REPLACE phục hồi đúng row cũ) — hoặc per-lô: B/Ba `UPDATE name_zh` ngược; D restore row từ backup;
E `UPDATE vn_person_authority SET dila_id='A021395' WHERE id='alias_A021395'` (tương tự A000733).

**Revert Lô C/Ca + H1 (đã ghi 2026-10-10):**
- Lô C: `DELETE FROM time_periods WHERE source_origin='era_catalog'` (17 row, additive → 0 mất dữ liệu).
- Lô Ca: restore `label_zh`/`year` từ `data/backups/2026-10-10-lot-C-Ca/backup_lotCCA_20261010_184438.sql`.
- H1: chạy `data/backups/2026-10-10-H1-evidence/h1_revert.sql` (DELETE 357 row id 4972–5328) hoặc restore `.db`.

---

## 7. Việc CHƯA quyết / cần Admin chốt ngay

1. ✅ **Lô B — bốn nhóm trùng:** ĐÃ xử lý theo đề xuất (3 sửa name_zh; không flip status; `ma_to_dao_nhat`/
   `alias_A003623` giữ nguyên). **HOÃN (Admin chọn):** thêm canonical_decision cho `phuoc_chau_dai_an` (schema entity_ref
   chưa có tiền lệ — Admin quyết có cần ghi tường minh "Phước Châu Đại An là canonical, Phúc Châu Đại An là biến thể" không).
2. ✅ **H3 nhóm 2 — 4 row số Ả Rập:** ĐÃ nới regex W1a (Admin "Đồng ý build") → H3 = 0.
3. ✅ **Row `建興` PL000000058135:** đã set `year=314` (khớp "晉建興二年"); Admin soi lại nếu cần.
4. ✅ **PL000000000001:** ĐÃ đổi "Khoát Tất Đa Quốc" + verified/admin_approved (D2).
5. ✅ **Người ghi DB từng lô:** 2026-10-10 agent ghi Lô B/D/E với backup, audit chạy sau (H3/H4 không đổi).
6. ✅ **T213 state:** classification DONE 2026-10-10; **Bucket B/C/D Admin duyệt 2026-10-11**:
   - Bucket B (6 Indian Patriarchs) → task **T278** link DILA IDs (**✅ DONE 2026-10-11**).
   - Bucket C (11 Non-monk) → `entity_type='lay_person'` (DONE).
   - Bucket D (8 Mythological) → `entity_type='mythological'` (DONE).
   - Schema: thêm cột `entity_type` vào `vn_person_authority` (default 'monk').
7. ⏳ **T274 state:** dry-run cho ra 0 cạnh `noi_phap_ttl_only`. **Phát hiện 2026-10-11:** Base pool DILA (46.004 cạnh) KHÔNG chứa cạnh Việt Nam (cạnh Việt Nam ở source TTL). Cần Admin quyết định hướng tiếp theo (mở rộng base pool hoặc tách task riêng).

---

## 8. File tạo/đọc trong session này

- `docs/plans/2026-10-10-analysis-pack-t271-followups.md` (file này, đã commit 2 lần: bản ANALYSIS + bản APPLIED).
- `%TEMP%\opencode\apack\apply_lot_BDE.py`, `verify_after.py` — script ghi DB + verify (ngoài repo).
- `data/backups/2026-10-10-lot-B-D-E/backup_lotBDE_20261010_170854.sql` — backup row bị UPDATE (INSERT OR REPLACE).
- `%TEMP%\opencode\apack\1_orphans.json` (210 row), `2_groups_detail.json`, `3_h3_fail.json`, `4_h4_fail.json`,
  `5_pl_a021395.json` — bản đầy đủ chưa đưa lên repo (chờ tuyển chọn).
- Lô C/Ca + H1 (2026-10-10): `%TEMP%\opencode\apack\apply_lot_CCa.py`, `apply_h1_evidence.py`;
  backup `data/backups/2026-10-10-lot-C-Ca/backup_lotCCA_20261010_184438.sql`;
  backup `data/backups/2026-10-10-H1-evidence/lineage.H1-20261010_195950.db` + `h1_revert.sql`;
  session `docs/sessions/2026-10-10_T271-lot-CCa-h1.md`.
- `tasks/T213-vnpa-orphan-211-classification.md` (đọc; cần sửa "211 ''" → "210 '' + 1 NULL").
- Chưa tạo file Handoff mới; session này là phân tích + đóng gói + ghi 3 lô (B/D/E), chưa đóng task nào.

---

## 9. Lệnh tái kiểm trong 1 phút (agent sau chạy lại)

```bash
# 210 orphan
SELECT COUNT(*) FROM vn_person_authority WHERE dila_id='';
# 1 NULL (tang_chu_pho_dung)
SELECT id FROM vn_person_authority WHERE dila_id IS NULL;
# H3 = 23, H4 = 591
python -X utf8 scripts/audit_data_honesty.py --h3 --h4
# 591 label bi sau khi Lô Ca
SELECT COUNT(*) FROM place_timeline_events p WHERE p.label_zh LIKE '%年建%';
# era thieu
SELECT DISTINCT period_name_zh FROM time_periods WHERE period_name='era' AND start_year IS NOT NULL;
# alias 法演
SELECT id,dila_id,name_zh FROM vn_person_authority WHERE name_zh='法演';
# PL canonical
SELECT entity_ref,canonical_name_vi,verification_status FROM canonical_decision WHERE entity_ref='PL000000000001';
```

---

## 10. Ghi chú agent kế tiếp

- Dùng `git diff --cached --name-status` trước commit; DB chỉ ghi theo lô có backup `data/backups/` đã Admin OK.
- Sau mỗi lô ghi DB → chạy `audit_data_honesty.py` + `build_progress_data.py` regen, kiểm pipeline.
- Không tự cấp era `建興` trước khi Admin soi row PL00000000058135.
- H3/H4 (Mục 3) đang **để lại** theo Admin — đừng tự sửa; chỉ làm khi Admin mở lại Lô C/Ca.
- Mục 4 đã chốt "Khoát Tất Đa Quốc"; nếu sau này DILA/lịch sử khẳng định tên khác, cập nhật canonical_decision + note.
- Tôn trọng worktree dùng chung: đừng `git add` cả `docs tasks`; chỉ add từng file đã sửa.
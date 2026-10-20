---
id: T176
title: "T158-PHASE0C rev.2 (đổi nhãn T176) — Canonical Buddhist Person Identity Resolution Audit v2: BUG-025 + 22 Dictionaries + Cache/Transliteration"
module: Translation / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T175, T174, T166, T171]
created: 2026-09-25
updated: 2026-09-30
designed_by: mimo-flash
handoff_to: Claude Code Agent (AUDIT ONLY — 0 code/0 DB/0 commit)
plan_approved_at: "2026-09-25 (Admin chốt: (1) tách task mới = T176 cho bản v2 · (2) GIỮ 2 mục report cũ → §12b + §14b)"
done_when: |
  Agent trả T176-PHASE0C AUDIT REPORT đúng mẫu (19 mục + 2 mục giữ chốt cũ
  §12b/§14b) · 0 code/0 DB/0 commit · Admin duyệt → mới nhận APPROVED FIX.
---

# T176 — Phase 0C rev.2 Audit: Canonical Person Identity (DILA Han → Local VI → Display → LLM → Cache)

> **Gốc:** directive `[T158-PHASE0C]` **bản v2** (Admin viết lại, có thêm BUG-025 + 13 compat task + format 19 mục).
> **Chốt Admin 2026-09-25:** (1) **Tách task mới = T176** — T175 (v1) giữ nguyên, không sửa; (2) **GIỮ 2 mục report đã chốt** → `§12b. OVERLAP WITH T174/T166/T171` + `§14b. AMBIGUITY_RESULT`.
> **[T194 2026-09-29] Đã re-verify toàn bộ §2 + line-ref trong §3.** Sửa 4 fact sai (F1–F4) + 6 line-ref stale + 1 P0 mới (chỉ đích A/B/C). Prompt **tự chứa 100%** — không mục nào rỗng, không trỏ directive `T158-PHASE0C` không tồn tại. Chi tiết ở `tasks/T194-t176-plan-doc-correction.md`.
> **[T195 2026-09-30] Re-review read-only lần 3 → thêm §2b–§2i.** Phát hiện lớn nhất: **P0 thật là `name_vi_map.id=4689`** (dila_id=A021462 sai, `confidence=1.0`, `approved_by=NULL`, `marcus_ids` trỏ A027031 = vị khác) — **không** phải "B+C collapse trong `people`" (cột `people` đã sạch). Thêm: ⚠ **revert của BUG-025 đảo ngược + mất điều kiện `AND` ⇒ cấm dùng làm rollback**; 3 lớp nhiễu (neo sai / không neo / neo đúng); 5 row `daoanh_dict` không neo gồm **tên sách**; sai thanh `Linh Hữu` trên 3 id; cụm 6 người `Linh H*`; khoảng trắng thừa `靈祐 `; đồng âm `Quy Sơn`/`Quy Ngưỡng`; âm Nhật `Izan Reiyū`; ngày `771-853` không nguồn; quy tắc prefix **không nhất quán**; sửa trỏ 12 safety rules sang `X-T166-…-SPEC.md`. SQL remediation **chỉ tài liệu hóa, KHÔNG ghi `lineage.db`** (§2i). Chi tiết ở `tasks/T195-t176-p0-correction.md`.
> **[T194] Ghi chú:** commit `dbb77ef` mà dòng dưới từng trích **không tồn tại** trong repo (`git log dbb77ef` → `fatal: ambiguous argument`); session `docs/sessions/2026-09-25_t176-phase0c-rev2-audit-plan.md` **chưa tạo**. Cả hai là lỗi tham chiếu, không ảnh hưởng nội dung audit.
> **Mode:** AUDIT ONLY — cấm code/DB/ALTER/INSERT/cache-purge/new resolver/commit. Stop chờ lệnh.
> **Mối quan hệ:** T175 = v1 (đã review 4 P0+6 P1) · T176 = v2 (paste prompt §3 này thay cho T175 §3 khi Admin chạy audit) · sub-audit **feed T174** · kế thừa **T166** authority · minimal fix map **T171**.

## 1. Review v2 → 2 P0 đã chốt + 4 P1 delta (verify DB/source thật)

### v2 ĐÃ SỬA được so với v1 (không cần吸收 lại)
- §14 chỉ yêu cầu "tương thích" → **không còn claim sai "T79 = translation system"** (v1 P1-1) ✓
- §8 "hoặc thứ tự khác" = câu hỏi mở thay vì giả định thứ tự ✓
- §3 thêm rule "chỉ kết luận mapping khi evidence chứng minh · fuzzy = không làm canonical proof" ✓
- **§5 BUG-025 là bug THẬT** đã có sẵn (xem dưới) + §13 TEST-07 cache + format 19 mục đủ chỗ ✓

### P0-1 · Đụng label `T158-PHASE0C` lần nữa (T175 v1 đã commit `dbb77ef`) → **Admin chốt: T176**

### P0-2 · Format v2 (19 mục) bỏ mất 2 mục report Admin đã chốt (v1) → **Admin chốt: GIỮ** → `§12b` + `§14b`

### P1 delta (4) — đã nhúng vào prompt §3
1. **MỤC TIÊU "canonical = Linh Hựu" = GIẢ THIẾT, không phải fact:** DB thật `people[A001984].name_vi` = **đã gộp `Quy Sơn Linh Hựu`** (B+C collapse) · **`Linh Hựu` = T51g curated** (`scripts/t51g_import_curated.py:52` → ghi `marcus_reference.label_vi`) · vnpa `alias_A001984` = status **`alias_vi_suffix`** · `people` **không có cột** title/thụy hiệu/alias (đặt ở `vn_person_authority.dharma_title`/`appellations`) · `monk_name_index` = bảng thật nhưng **37 row, khóa `monk_id`** (không `dila_id`) · TEST-01 **candidate set 5 id** (A001984/A023322/A023362/A032868/A035586).
2. **§5 BUG-025 = ĐÃ FIX MỘT PHẦN (verify trước):** `docs/bugs.md:411` — data-only fix 2026-09-22, status **`pending_confirm`**; `people` đã đúng (A021462=`Kính Đường Giác Viên`, A001984=`Quy Sơn Linh Hựu`) — **NHƯNG còn row stale `name_vi_map (dila_id=A021462, name_vi='Quy Sơn Linh Hựu', source=daoanh_dict)`** + đường search `n.name_vi LIKE` (app.py:3811) + script `scripts/verify_bug025_026.py` → prompt §5 thêm hint "phần nào còn sót" (agent xác minh, KHÔNG sửa).
3. **§6 "22 dictionary" = StarDict layer, không phải 22 bảng DB:** `docs/pipelines.md:68` "Parse all 22 dictionary `.idx` + `.dict` files" + `DEV_HISTORY.md:30` "22 bộ từ điển → 166.278 terms" (merge vào `lexicon`) → đếm qua **`lexicon.source` + `ls data/dictionaries/*.idx`**, không đếm tên bảng (bảng keyword dict/gloss ≈22 nhưng gồm 5 shadow FTS + jobs/segments) · `_glossary_resolver` = **function** (~app.py:16330) · `monk_dict` chỉ **2 row** · `glossary_vi` **0 entry `靈祐`**.
4. **Verify mới đưa vào prompt** (để agent không phát biểu sai): route **`/api/translate/google` (app.py:14332) backend = MyMemory** (mislabeled) · `translate_hvdic` :14310 = thivien.net · `translate_all` :14353 = hvdic → MyMemory · **cache key = `sha256(excerpt)[:24]` + `source_type` + `rules_version` + `constitution_hash` + `selected_rule_codes` + `glossary_hash` — canonical identity KHÔNG nằm trong hash** → TEST-07 stale risk có thật · `admin_namevi_translate_local` (app.py:16075) **ghi thẳng `name_vi_map`** (`name_vi_auto`, conf **0.5**, source `local_translate`) → §12 mục 4/10 · TTL **đường đọc thật** = `master_ttl_path = TTL_MASTER_DIR/f"TS-{dila_id}.ttl"` (app.py:12361, 12407); `app.py` **không** có `open(...*.ttl)` literal — vòng `TTL_OLD_DIR` (:13815/13817) là **admin rebuild queue**, không phải runtime lookup per-person · ETL `t05_ttl_namevi_etl`/`etl_ttl_person_authority` → `vn_person_authority`.
5. **[T194] `marcus_reference` khóa theo `node_id`, KHÔNG phải `lookup_id`** — cột: `node_id, label, label_vi, birth_year, death_year, created_at, label_vi_confidence, label_vi_source`; app.py đọc bằng `node_id` (:2694, :5349). Agent query `lookup_id` sẽ nhận `no such column`.
6. **[T194] `name_vi_map` KHÔNG có row cho A001984** — verified: `SELECT COUNT(*) FROM name_vi_map WHERE dila_id='A001984'` = **0**. (Toàn bảng có 41.508 row `confidence=0.7`, nhưng A001984 không nằm trong đó.) Nguồn `conf 0.7` thuộc `A032868` (`name_vi_auto='Linh Hữu'`, source `auto_transliterate`), không phải A001984.
7. **[T194] Chỉ đích A/B/C thật = `person_display_names`, KHÔNG phải `person_name_alias`:**
   - `person_name_alias` là bảng **TARGET** của SPEC T171 §3.2 — **chưa migrate**, `no such table` trong `lineage.db`.
   - `person_display_names` **đã build**, 8 row, đúng cấu trúc A/B/C: `authority_name_vi` (B) + `display_name_vi` (C) + `is_preferred` + `verification_status` + `appellation_vi` (thụy hiệu) + `source_predicate`/`source_ref` (evidence) + `source_type` (`ttl`/`manual`).
   - `person_name_correction` 2.433 row (hàng chờ sửa, `status`/`reviewed_by`).
   - A001984: **0 row** ở cả hai bảng → ứng viên pilot sạch. 8 row `person_display_names` đều `is_preferred=1`, `verification_status` = `verified_direct`/`verified_crosswalk`.
   - `people` (15 cột) **không có** cột title/posthumous/alias → khẳng định L94 là đúng.

## 2. Verified facts (pre-audit, read-only — 2026-09-25)

| Hạng mục | Thật |
|---|---|
| BUG-025 | `docs/bugs.md:411` · fix data-only 2026-09-22 · **pending_confirm** · ⚠ **revert trong bugs.md ĐẢO NGƯỢC + không có điều kiện `AND`** → xem §2b, **CẤM dùng làm rollback** |
| `name_vi_map` stale | row `id=4689, dila_id=A021462 → "Quy Sơn Linh Hựu"` **CÒN SỐT** (people đã fix) |
| "Linh Hựu" nguồn local | `t51g_import_curated.py` → `A001984` : `('Linh Hựu', 1.0, 'Quy Sơn Linh Hựu … 祐=Hựu không phải Hữu')` → ghi `marcus_reference.label_vi` (khóa `node_id`) |
| `monk_name_index` | 37 row · cols `id, monk_id, lang, name_form, name_type, normalized, created_at` |
| 22 từ điển | StarDict 22 file `.idx/.dict` → `lexicon` 166.278 (`source` phân nguồn) · DB dict-ish 22 tên bảng gồm FTS shadow/jobs → KHÔNG dùng cách này đếm |
| Glossary/test | `glossary_vi` 248.095 nhưng **0 `靈祐`** · TEST-05 sẽ NOT FOUND ở glossary (đúng) · `monk_dict` 2 row |
| Transliterate | hvdic thivien.net :14310 · "google" = **MyMemory** :14332 · `translate_all` :14353 |
| Cache | `translation_cache` **1.870** row · `UNIQUE(source_hash, source_type)` · key hash **không gồm canonical** |
| TTL | `master_ttl_path` = `TTL_MASTER_DIR/f"TS-{dila_id}.ttl"` (:12361, :12407) · `TTL_OLD_DIR` (:13815) = admin rebuild · 2 script ETL → `vnpa` |
| `name_vi_map` A001984 | **0 row** — `conf 0.7` thuộc `A032868` (source `auto_transliterate`) |
| Chỉ đích A/B/C | `person_display_names` **8 row** (đã build) + `person_name_correction` 2.433 row · `person_name_alias` **chưa migrate** |
| A001984 | `people` 靈祐 唐 Thiền Tông · name_vi = **Quy Sơn Linh Hựu** · 靈祐 = **5 id** · 0 row `person_display_names` |

## 2b. [T195] Row `name_vi_map` id=4689 — giải phẫu đầy đủ (verify 2026-09-30)

Đây là **P0 thật** của audit, không phải "B+C collapse trong `people`" (cột `people` đã sạch).

```sql
SELECT * FROM name_vi_map WHERE id=4689;
```

| cột | giá trị | ý nghĩa |
|---|---|---|
| `id` | `4689` | |
| `name_vi` | `Quy Sơn Linh Hựu` | **tên sai, gán nhầm lên người sai** |
| `name_vi_final` | `Quy Sơn Linh Hựu` | đã "chốt" → rơi vào **khoảng trống phân tầng** |
| `confidence` | **`1.0`** | **cao nhất trong hệ thống** |
| `approved_by` / `approved_at` | **`NULL` / `NULL`** | ⇒ **không** thuộc tier A (chưa duyệt) |
| `name_zh` | `香嚴智閑` | **sai** — `people[A021462].name_zh` = `鏡堂覺圓` |
| `dila_id` | `A021462` | **người sai** (Kính Đường Giác Viên) |
| `marcus_ids` | **`A027031`** | ⚠ **cross-link sai** — `A027031` = 法端 / *Duyên Khánh Pháp Đoan*, **khác người hoàn toàn** |
| `name_vi_auto` | `NULL` | không phải auto, là `daoanh_dict` |
| `source` | `daoanh_dict` | |
| `birth_year` / `death_year` | **`NULL` / `NULL`** | dù `bio_snippet` **có** `771-853` → chưa parse vào cột |
| `bio_snippet` | `(潙山靈祐, Izan Reiyū, 771-853): h…` | ⚠ chứa **3** dữ kiện mới (xem §2d) |

**Vì sao đây là P0:** `people` đã được BUG-025 sửa nên search path #1 (`people.name_vi LIKE`) trả đúng. Nhưng **search path #2** (`name_vi_map.name_vi LIKE`) vẫn khớp `Quy Sơn Linh Hựu` → trả **A021462**, người **sai**, ở **confidence 1.0** — tức đè lên mọi tầng thấp hơn. Audit phải trả lời: vì sao `name_vi_final` + `confidence=1.0` lại **không có** `approved_by` mà vẫn được coi là authoritative.

## 2c. [T195] ⚠ BUG-025 revert SQL **ĐẢO NGƯỢC — CẤM DÙNG LÀM ROLLBACK** (verify 2026-09-30)

`docs/bugs.md:411` ghi nguyên văn:

```sql
-- FIX (đã apply 2026-09-22, đúng):
UPDATE people SET name_vi='Kính Đường Giác Viên' WHERE id='A021462' AND name_vi='Quy Son Linh Huu';
UPDATE people SET name_vi='Quy Sơn Linh Hựu'    WHERE id='A001984' AND name_vi='Đại Viễn Thiền Sư';

-- REVERT (ghi trong bugs.md, SAI + NGUY HIỂM):
UPDATE people SET name_vi='Quy Sơn Linh Hựu'  WHERE id='A021462';   -- ← gán lại tên sai cho người sai
UPDATE people SET name_vi='Đại Viễn Thiền Sư' WHERE id='A001984';   -- ← làm A001984 mất searchable
```

Ba lỗi độc lập trong chính câu revert:
1. **Đảo ngược** — đặt `Quy Sơn Linh Hựu` (tên của A001984) lên **A021462** ⇒ **tái tạo đúng bug BUG-025**.
2. **Mất điều kiện `AND`** — fix có guard `AND name_vi='…'`, revert thì không ⇒ ghi đè bất kể dữ liệu hiện tại.
3. **Lùi A001984** về `Đại Viễn Thiền Sư` (thụy hiệu) ⇒ `people[A001984].name_vi` không còn searchable, đúng cái bug mà BUG-025 sinh ra.

⇒ **T176 không được dùng câu revert này làm đường rollback.** Rollback đúng cho audit này là **restore từ git** (`git revert <pass-1 SHA>`, docs-only), **không** phải chạy SQL trong bugs.md. Nếu cần SQL: xem §2e.

## 2d. [T195] Dữ kiện mới trong `bio_snippet` + rác dict không neo (verify 2026-09-30)

`name_vi_map.bio_snippet` của id=4689 chứa `(潙山靈祐, Izan Reiyū, 771-853)`. Ba hệ quả T176 cũ **chưa** nêu:

1. **`潙山靈祐`** (Hán viết đầy đủ) **có thật trong DB** — nằm ở `bio_snippet`, không chỉ ở TTL. `vn_person_authority.appellations` của A001984 = `NULL` ⇒ **không có chỗ có cấu trúc** để lưu prefix, phải suy từ text.
2. **`Izan Reiyū`** = âm Nhật của 靈祐 (on'yomi). Đây là **họ alias mới**, không thuộc họ Hán-Việt mà T176 liệt kê (`Linh Hựu`/`Linh Hữu`/`Quy Sơn…`). Search/normalize path nào bỏ qua alphabet latin sẽ **miss** nó.
3. **`771-853` là claim từ text từ điển Việt, chưa có nguồn học thuật**; `vn_person_authority.birth_year`/`death_year` = `NULL`/`NULL`, `people[A001984].birth_year` cũng NULL ⇒ **không được trình bày như fact authority**. TTL cũng tự mâu thuẫn: header ghi `771-853`, phần thân ghi "hoảng dương Thiền tông khoảng 40 năm".

**Rác `daoanh_dict` không neo** — `dila_id`/`name_zh`/`marcus_ids` đều `NULL`, `confidence=0.5`, nhưng **vẫn khớp `LIKE '%Quy Sơn Linh Hựu%'`**:

| `id` | `name_vi` | loại |
|---|---|---|
| `1301` | `Linh Hựu` | tên trần, không neo |
| `2270` | `Quy Sơn Cảnh Sách của Thiền Sư Linh Hựu ghi:` | **mục lục sách** |
| `2271` | `Quy Sơn Linh Hựu Thiền Sư Ngữ Lục` | **tên sách** (Ngữ Lục = 語錄) |
| `3522` | đoạn mô tả *Cổ Kim Tiệp Lục* liệt kê "…Quy Sơn Linh Hựu, Ngưỡng Sơn Huệ Tịch…" | **đoạn văn dài** |

⇒ Đây là **lớp nhiễu thứ ba**, tách biệt với `dila_id=A021462`: kể cả khi đã sửa row 4689, search vẫn trả về **tên sách** thay vì người. Audit phải phân biệt 3 lớp: (i) row neo sai người, (ii) row không neo, (iii) row neo đúng.

## 2e. [T195] Sai thanh điệu + cụm "Linh H*" — inventory bắt buộc (verify 2026-09-30)

**Sai thanh `Lữu` (Hữu) vs đúng `ực` (Hựu)** — cùng Hán 靈祐 nhưng 3 ID mang thanh **sai**:

| nơi | id | `name_vi` | `confidence` | `source` |
|---|---|---|---|---|
| `marcus_reference` | **A001984** | `Linh Hựu` ✅ | **1.0** | `curated_T51g` |
| `marcus_reference` | A023322 | `Linh Hữu` ❌ | 0.5 | `auto_hanviet_T51f` |
| `marcus_reference` | A023362 | `Linh Hữu` ❌ | 0.5 | `auto_hanviet_T51f` |
| `name_vi_map` | A032868 | `Linh Hữu` ❌ | 0.7 | `auto_transliterate` |

⇒ **`Linh Hựu` đúng chỉ có 1 nguồn conf 1.0**; 3 bản sai thanh ở conf ≤0.7. Không được coi "đa số `Linh Hữu`" là biến thể hợp lệ — ngược lại, curated T51g mới là chuẩn âm.

**Cụm gần-giống `Linh H*` — 6 người khác nhau**, mọi `LIKE 'Linh H%'` đều fan-out:

| `name_zh` | `name_vi` | id / dòng |
|---|---|---|
| `令休` | `Linh Hưu` | A010280 |
| `靈暉` | `Linh Huy` | A024899 |
| `令翬` | `Linh Huy` | A035457 |
| `靈訓` | `Linh Huấn` | A019949 |
| `靈祐` | `Linh Hữu` | A032868 |
| 靈祐 (TL) | `Linh Hựu` | **A001984** |

⇒ Bất kỳ test nào dùng `LIKE 'Linh H%'` đều **không chứng minh** được resolve đúng A001984. TEST phải assert **exact match `Linh Hựu` + `name_zh=靈祐`**, không dùng prefix match.

## 2f. [T195] Quy tắc suy ra `canonical` — 潙山 là **địa danh**, không phải pháp danh (verify 2026-09-30)

TTL `TS-Quy-Son-Linh-Huu.ttl` tự phân biệt trong biographical note: `Quy Sơn (潙山)` + **"pháp danh Linh Hựu"**. ⇒ `canonical` (B) = pháp danh = `Linh Hựu`; `display` (C) = `Quy Sơn Linh Hựu`.

**Tiền lệ đã có sẵn trong `person_display_names`** (8 row, `style_type='formal'`) — đây là bằng chứng mạnh nhất cho hướng B/C, T176 cũ chưa trích:

| `person_id` | `display_name_vi` (C) | `authority_name_vi` (B) | prefix bị bỏ |
|---|---|---|---|
| A038686 | Đại Huệ Tông Cảo | Đại Đức Tông Cảo | Huệ→Đức |
| A036842 | Ngũ Tổ Pháp Diễn | **Pháp Diễn** | bỏ trọn `Ngũ Tổ` |
| A000453 | Viên Ngộ Khắc Cần | **Khắc Cần** | bỏ trọn `Viên Ngộ` |
| A004146 | Dương Kì Phương Hội | Dương Kỳ Hội | bỏ `Phương` |
| A033489 | Bạch Vân Thủ Đoan | Vân Tụ Thú Đoan | **giữ** `Vân Tụ` |

⚠ **Cảnh báo — quy tắc KHÔNG nhất quán:** A004146 bỏ hẳn `Phương` (楊岐→Dương Kỳ) nhưng A033489 **giữ lại** `Vân Tụ` (雲岫→Vân Tụ). ⇒ **không thể suy ra `authority` bằng thuật toá**; phải **ghi tường minh** từng case. Riêng A001984, câu trả lời sạch vì 潙山 là **tên núi/tông**, không thuộc pháp danh — nhưng đó là **fact lịch sử**, không phải quy tắc máy. `person_display_names` **không có** row cho A001984 ⇒ đây chính là chỗ fix sẽ map vào.

## 2g. [T195] Đồng âm `Quy` — 潙山 vs 圭仰宗 (verify 2026-09-30)

Cùng file TTL, dòng 457/462 nhắc dòng tông **圭仰宗 "Quy Ngưỡng Tông"** (`bkg:dharmaLineageName "Tông Quy Ngưỡng Trung Hoa"@vi`), và nội dung này **đã lan sang DB**: `name_vi_map` id=3522 liệt kê "…Quy Sơn Linh Hựu, Ngưỡng Sơn Huệ Tịch…".

⇒ **Cùng âm Hán-Việt `Quy`, khác Hán, khác cả nghĩa**:
- `潙山` = **địa danh** (núi Quy Sơn, Phúc Kiến) → tiền tố hiệu danh
- `圭仰` = **tông phái** (Trung Hoa Thiền) → tên tông, **không** thuộc A001984

Rủi ro: alias/normalizer khử dấu sẽ gộp `Quy Ngưỡng` với `Quy Sơn`. Audit phải test `Quy Ngưỡng` không được resolve về A001984. `vn_person_authority.appellations` A001984 = `NULL` ⇒ chưa có chỗ lưu phân loại prefix.

## 2h. [T195] Lỗi khoảng trắng thừa trong `name_zh` (verify 2026-09-30)

`靈祐 ` (**có 1 space thừa ở cuối**) xuất hiện ở **cả hai** bảng:

| bảng | cột | giá trị |
|---|---|---|
| `marcus_reference` | `label` (node_id=A001984) | `靈祐 ` |
| `vn_person_authority` | `name_zh` (id=`alias_A001984`) | `靈祐 ` |
| `name_vi_map` | `name_zh` (id=4689) | `香嚴智閑` (không thừa) |

⇒ Mọi `WHERE name_zh = '靈祐'` / `JOIN ... ON name_zh` **không khớp** ⇒ âm thầm rơi sang nhánh fallback. Nguyên nhân: `label`/`name_zh` được đổ bằng raw slice từ TTL header `靈祐 (Izan Reiyū, …)`. `marcus_reference` của A023322/A023362 lại **không** thừa ⇒ so khớp giữa 3 node cùng Hán **không đồng nhất**. Phải `TRIM()` toàn bộ read path, và assert trong test.

## 2i. [T195] Remediation — **TÀI LIỆU THAM CHIẾU, KHÔNG THỰC THI**

Admin chốt 2026-09-30: **chỉ tài liệu hóa, KHÔNG ghi `lineage.db`**. Agent chạy audit giữ nguyên chế độ AUDIT ONLY. SQL dưới đây để **Admin review rồi tự tay** áp dụng sau khi audit kết thúc.

```sql
-- R0. PREVIEW (bắt buộc chạy trước, read-only) — phải trả đúng 1 row
SELECT id, dila_id, name_zh, name_vi, name_vi_final, confidence, approved_by, marcus_ids
FROM name_vi_map WHERE id = 4689;

-- R1. Hạ tier + bỏ neo sai (KHÔNG xoá — giữ evidence cho audit)
UPDATE name_vi_map
   SET confidence = 0.1,
       name_vi_final = NULL,
       marcus_ids   = NULL
 WHERE id = 4689
   AND dila_id = 'A021462'
   AND name_zh  = '香嚴智閑'
   AND confidence = 1.0
   AND approved_by IS NULL;

-- R2. Nối đúng người (dựa authority đã curate T51g ở marcus_reference)
UPDATE name_vi_map
   SET dila_id = 'A001984', name_zh = '靈祐', confidence = 1.0
 WHERE id = 4689 AND marcus_ids IS NULL AND dila_id = 'A021462';

-- R3. Khoảng trắng thừa (cả 2 bảng) — dùng TRIM ở read path, ở đây chỉ chuẩn hoá data
UPDATE marcus_reference     SET label    = TRIM(label)    WHERE node_id IN ('A001984','A023322','A023362');
UPDATE vn_person_authority  SET name_zh  = TRIM(name_zh)  WHERE dila_id  = 'A001984';

-- ROLLBACK (đúng, khác hoàn toàn với revert trong bugs.md):
--   git revert <pass-1 SHA> cho phần docs; với data thì khôi phục lineage.db từ backup.
--   TUYỆT ĐỐI KHÔNG chạy "Revert:" trong docs/bugs.md:411.
```

R1/R2 là **UPDATE có điều kiện** ⇒ chạy lại nhiều lần vẫn idempotent, và **không khớp** ⇒ tự dừng. Không có `DELETE`.

---

## 3. PROMPT CHỐT — dán Claude Code (AUDIT ONLY)

```text
[T176-PHASE0C rev.2]
CANONICAL BUDDHIST PERSON IDENTITY RESOLUTION AUDIT

MỤC TIÊU
--------
Audit thực tế pipeline hiện tại của PTDA/Đạo Ảnh để xác định:

DILA Han name
    ↓
DILA canonical person ID
    ↓
local Vietnamese canonical/approved name
    ↓
Vietnamese display/surface form
    ↓
translation / Qwen / transliteration
    ↓
cache
    ↓
final rendered result

ĐẶC BIỆT AUDIT CASE THỰC:
    靈祐
    DILA ID = A001984
    [DELTA-P1a] "Vietnamese canonical = Linh Hựu" là GIẢ THIẾT cần verify, không phải fact.
      Kỳ vọng DB thật (đã verify 2026-09-25, agent re-verify):
      - people[A001984].name_vi = "Quy Sơn Linh Hựu" (B+C ĐÃ gộp 1 field — chính là thứ §11 yêu cầu tách)
      - "Linh Hựu" = T51g curated (scripts/t51g_import_curated.py:52 → marcus_reference.label_vi)
      - vnpa alias_A001984 status = alias_vi_suffix (CHƯA verified tier)
      - people KHÔNG có cột title/thụy hiệu/alias → nằm vn_person_authority.dharma_title/appellations
    KHÔNG được đồng nhất 3 lớp này thành một field duy nhất.


==================================================
1. QUY TẮC BẮT BUỘC
==================================================

CHỈ AUDIT.

KHÔNG:
- sửa code
- sửa DB
- ALTER schema
- INSERT/UPDATE/DELETE dữ liệu
- rebuild cache
- đổi API
- đổi canonical ID
- commit
- tạo migration
- tạo resolver mới

Nếu phát hiện bug:
CHỈ ghi nhận root cause + vị trí + đề xuất fix tối thiểu.

Không được "tiện tay sửa".

Không đoán tên file/function.
Phải truy tìm từ code/runtime thực tế.

==================================================
2. PHẢI TRACE CALL CHAIN THỰC
==================================================

Trace từ:

UI
→ route
→ backend function
→ resolver
→ DB query
→ DILA lookup
→ local name lookup
→ dictionary/glossary lookup
→ transliteration API
→ LLM/Qwen/Groq
→ post-processing
→ cache
→ final response/render

Ghi chính xác:

- file
- function
- route
- table
- relevant columns
- cache key
- cache table/file
- thứ tự ưu tiên hiện tại

Không chỉ mô tả kiến trúc dự kiến.
Tôi cần call chain ĐANG CHẠY THỰC TẾ.

==================================================
3. AUDIT DILA IDENTITY
==================================================

Kiểm tra:

靈祐
A001984

Xác định:

A001984 hiện có:
- name_zh?
- name_vi?
- alias?
- title?
- posthumous name?
- alternative name?
- index/search mapping?

[DELTA-P1a] people KHÔNG có cột title/posthumous/alias — check thêm
vn_person_authority (dharma_title, appellations, alias_*) và
monk_name_index (bảng thật, 37 row, khóa monk_id chứ không phải dila_id).
[T194] VÀ `person_display_names` (8 row, ĐÃ build — đây mới là bảng
biểu diễn A/B/C thật: authority_name_vi / display_name_vi /
appellation_vi / is_preferred / verification_status / source_type).
KHÔNG đi tìm `person_name_alias` — bảng đó chưa migrate, không tồn tại.
A001984 hiện 0 row trong person_display_names → ghi rõ, đây là chỗ
fix sẽ map vào.

Kiểm tra tất cả đường dẫn có thể map:

靈祐
釋靈祐
潙山靈祐
潙山靈祐禪師

→ A001984

Nhưng CHỈ kết luận mapping nếu DB/evidence hiện tại chứng minh được.
Không được dùng fuzzy matching làm canonical proof.

[DELTA-P1a] Lưu ý test case: name_zh='靈祐' trong people = 5 người
(A001984 / A023322 / A023362 / A032868 / A035586) — TEST-01 phải trả
candidate set + cách disambiguate, không trả 1 id như đã chắc.

==================================================
4. AUDIT LOCAL VIETNAMESE NAME
==================================================

Kiểm tra A001984 trong toàn bộ local knowledge:

- people
- name_vi
- name_vi_map
- monk_name_index
- monk_dict
- dictionary tables
- glossary_vi
- translation memory
- TTL/XML
- curated data
- historical translation data

Đặc biệt tìm:

A001984 → Linh Hựu
và:
A001984 → Quy Sơn Linh Hựu

[DELTA-P1a] Gợi ý đã verify (re-verify): "Linh Hựu" không nằm ở people
(một hàng cũng không) mà ở T51g curated → marcus_reference.label_vi;
monk_name_index 37 row — check có entry nào cho A001984 không.
[T194-F1] name_vi_map dila_id='A001984' = 0 ROW (đã verify) — đừng tìm
row "conf 0.7" ở đây, KHÔNG tồn tại. Row conf 0.7 của 靈祐 là A032868.
Nhánh name_vi_map cho A001984 vì vậy rơi vào fallback, phải ghi rõ
(NOT FOUND) thay vì im lặng — cùng logic với "Linh Hựu" standalone.

Phân loại rõ:

CANONICAL_VI
APPROVED_VI
DISPLAY_VI
ALIAS_VI
SURFACE_FORM
TITLE
POSTHUMOUS_NAME

Không được tự suy luận nếu database không có evidence.

==================================================
5. AUDIT BUG-025
==================================================

Kiểm tra thực tế:

A021462 = 鏡堂覺圓
A001984 = 靈祐

Xác minh:

A021462.name_vi
A001984.name_vi

và toàn bộ search/index/cache liên quan.

Tìm chính xác tại sao:

"Quy Sơn Linh Hựu"

đang resolve tới A021462.

Phải xác định:

- nguồn nào tạo ra giá trị sai
- ETL nào
- transliteration nào
- mapping nào
- manual data nào
- cache nào
- search index nào

Nếu BUG-025 đã được sửa một phần, xác định phần nào đã sửa và phần nào còn sai.
KHÔNG sửa.

[DELTA-P1b] Gợi ý đã verify (re-verify) — bug có hồ sơ: docs/bugs.md:411,
fix data-only 2026-09-22, status pending_confirm. people ĐÃ sửa đúng;
phần còn sót nghi ngờ: row name_vi_map (dila_id=A021462,
name_vi='Quy Sơn Linh Hựu', source=daoanh_dict) + đường search
n.name_vi LIKE (app.py:3962) + scripts/verify_bug025_026.py.
Xác minh phần nào còn chạy/resolve sai — chỉ ghi nhận.

[T194] BỔ SUNG: row A021462 đó có `name_vi_final='Quy Sơn Linh Hựu'` +
`confidence=1.0` nhưng `approved_by=NULL`, và `name_zh` sai
(name_vi_map='香嚴智閑' vs people='鏡堂覺圓'). → rơi vào KHOẢNG TRỐNG phân
tầng: không tier A (thiếu approved_by), cũng không tier B (name_vi_final
NOT NULL). Audit phải ghi nhận đây là đường resolve sai còn sốt, và
trả lời: vì sao `name_vi_final` + `confidence=1.0` lại gánh một giá trị
đã bị BUG-025 xác nhận là sai.

[T195] BỔ SUNG — giải phẫu đầy đủ row `name_vi_map.id=4689` (đã verify, xem §2b):
  marcus_ids = 'A027031'  ← cross-link SAI: A027031 = 法端 "Duyên Khánh Pháp Đoan",
                              là vị khác hoàn toàn, KHÔNG phải 靈祐.
  birth_year = death_year = NULL  ← dù bio_snippet có "771-853", chưa parse vào cột.
  name_vi_auto = NULL  ← không phải auto, source=daoanh_dict (nhập tay).
  → Audit PHẢI giải thích: `marcus_ids` sinh ra từ đâu mà gắn A027031?
    ETL nào? Đây là bằng chứng thứ hai cho "tên đúng nhưng neo sai người".

[T195] ⚠ CẤM DÙNG REVERT CỦA BUG-025 (xem §2c). Câu revert trong bugs.md:
  UPDATE people SET name_vi='Quy Sơn Linh Hựu' WHERE id='A021462';
  - ĐẢO NGƯỜC: gán tên của A001984 lên A021462 → TÁI TẠO đúng bug BUG-025.
  - Mất điều kiện AND → ghi đè không chặn.
  - Đẩy A001984 về 'Đại Viễn Thiền Sư' (thụy hiệu) → mất searchable.
  Audit KHÔNG được coi đây là đường rollback hợp lệ. Rollback đúng =
  git revert (docs-only) hoặc restore lineage.db từ backup.

[T195] ⚠ BA LỚP NHIỄU PHẢI PHÂN BIỆT (xem §2d) — không gộp làm một:
  (i)  row NEO SAI NGƯỜI  : id=4689, dila_id=A021462, conf 1.0  ← P0
  (ii) row KHÔNG NEO      : id=1300/1301/2270/2271/3522, dila_id=NULL, conf 0.5
        trong đó 2271='Quy Sơn Linh Hựu Thiền Sư Ngữ Lục' là TÊN SÁCH,
        3522 là đoạn mô tả sách — vẫn khớp LIKE '%Quy Sơn Linh Hựu%'.
  (iii)row NEO ĐÚNG        : chưa có row nào cho A001984 trong name_vi_map (0 row).
  → Kể cả khi đã sửa (i), search vẫn trả về (ii). Phải xử lý cả hai.

[T195] ⚠ SAI THANH (xem §2e): `Linh Hựu` (đúng) chỉ có 1 nguồn conf 1.0
  (A001984 curated_T51g). Ba bản `Linh Hữu` SAI THANH ở conf ≤0.7:
  A023322 + A023362 (marcus_reference, auto_hanviet_T51f),
  A032868 (name_vi_map, auto_transliterate).
  Audit KHÔNG được kết luận "đa số là Linh Hữu" → đó là sai;
  curated T51g mới là chuẩn âm.
  Thêm: 6 người tên "Linh H*" khác nhau (令休 Linh Hưu, 靈暉/令翬 Linh Huy,
  靈訓 Linh Huấn) → test BẮT BUỘC dùng exact match 'Linh Hựu' + name_zh='靈祐',
  TUYỆT ĐỐI KHÔNG dùng prefix LIKE 'Linh H%' (fan-out 6 người).

[T195] ⚠ KHOẢNG TRẮNG THỪA (xem §2h): `name_zh`/`label` = '靈祐 ' (có space
  cuối) ở marcus_reference(A001984) VÀ vn_person_authority(alias_A001984).
  A023322/A023362 thì KHÔNG thừa → 3 node cùng Hán không đồng nhất.
  Mọi so khớp exact/join sẽ rơi sang fallback. Phải TRIM toàn read path.

[T195] ⚠ ĐỒNG ÂM (xem §2g): cùng âm `Quy`:
  潙山 Quy Sơn = ĐỊA DANH (núi, Phúc Kiến) — tiền tố hiệu danh của A001984
  圭仰宗 Quy Ngưỡng Tông = TÔNG PHÁI Trung Hoa — KHÁC NGƯỜI, đã lan vào
  name_vi_map id=3522. Phải test `Quy Ngưỡng` KHÔNG resolve về A001984.

[T195] ⚠ BỔ SUNG ĐỒNG ÂM NHẬT: `bio_snippet` chứa "Izan Reiyū" — âm on'yomi
  của 靈祐. Đây là họ alias MỚI, không thuộc họ Hán-Việt. Read path nào
  chỉ index tiếng Việt sẽ miss.

[T195] ⚠ NGÀY SINH (xem §2d mục 3): `771-853` chỉ là claim trong text từ điển
  Việt, KHÔNG có nguồn học thuật; vn_person_authority.birth_year/death_year =
  NULL. TTL tự mâu thuẫn (header 771-853 vs thân "hoảng dương ~40 năm").
  Audit KHÔNG được trình bày 771-853 như fact authority.

[T195] ⚠ PREFIX KHÔNG SUY ĐƯỢC (xem §2f): 8 row `person_display_names` đã có
  sẵn CHỨNG MINH hướng B/C (display=đầy đủ, authority=bỏ prefix):
  A036842 'Ngũ Tổ Pháp Diễn'→'Pháp Diễn'; A000453 'Viên Ngộ Khắc Cần'→'Khắc Cần';
  A004146 'Dương Kì Phương Hội'→'Dương Kỳ Hội'; A038686→A033489 tương tự.
  NHƯNG quy tắc KHÔNG nhất quán: A004146 bỏ 'Phương' còn A033489 GIỮ 'Vân Tụ'
  → không có thuật toá suy ra `authority`, phải ghi tường minh từng case.
  Riêng A001984: 潙山 là tên NÚI/TÔNG, không thuộc pháp danh (TTL: "pháp danh
  Linh Hựu") → authority='Linh Hựu', display='Quy Sơn Linh Hựu'.
  `person_display_names` CHƯA có row cho A001984 → đây là chỗ fix map vào.

==================================================
6. AUDIT 22 BUDDHIST DICTIONARIES
==================================================

Xác định DB thật sự đang có 22 dictionary nào.

[DELTA-P1c] Cách đếm đúng (đã verify, re-verify): "22 từ điển" = 22 file
StarDict .idx/.dict được parse (docs/pipelines.md:68) → merge vào bảng
lexicon 166.278 rows (DEV_HISTORY.md v10.4). KHÔNG đếm 22 tên bảng
trong sqlite (kết quả đó gồm FTS shadow + jobs/segments). Đếm qua:
SELECT source, COUNT(*) FROM lexicon GROUP BY source
+ ls data/dictionaries/*.idx (hoặc data/dict).

Cho từng dictionary:

- table/file
- key field
- Han field
- Vietnamese field
- authority/confidence nếu có
- query function hiện tại
- có được AI translation pipeline gọi hay không

[DELTA-P1c] Lưu ý: _glossary_resolver = FUNCTION (app.py:17457), không phải
bảng; monk_dict chỉ 2 row; glossary_vi 248.095 nhưng 0 entry 靈祐.

Đặc biệt kiểm tra:

靈祐
潙山靈祐
Quy Sơn Linh Hựu
Linh Hựu

Có entry nào không?

==================================================
7. AUDIT TTL/XML
==================================================

Kiểm tra pipeline TTL/XML hiện tại.
T05 đã xác nhận TTL được dùng cho Vietnamese name.

Xác định:

- TTL data nằm ở đâu
- parser/index nào
- có lookup runtime hay chỉ ETL
- authority/confidence
- A001984 có evidence gì
- TTL có được translation pipeline sử dụng không

[DELTA-P1d] Gợi ý đã verify (re-verify): runtime dựng đường file
master_ttl_path = TTL_MASTER_DIR/f"TS-{dila_id}.ttl" (app.py:12361, :12407);
app.py KHÔNG có open(...*.ttl) literal — vòng TTL_OLD_DIR (:13815/13817)
là admin rebuild queue, KHÔNG phải lookup per-person. ETL scripts
t05_ttl_namevi_etl.py, etl_ttl_person_authority.py →
vn_person_authority, ttl_person_name_extractor.py. A001984 có row
vnpa alias_A001984, ttl_filename TS-Quy-Son-Linh-Huu, status alias_vi_suffix.

KHÔNG parse lại toàn bộ corpus.

==================================================
8. AUDIT TRANSLITERATION
==================================================

Kiểm tra thứ tự hiện tại:

DB
→ Viện Hán Nôm
→ Google
→ Qwen
hay thứ tự khác.

Xác định function thực tế.

Test read-only:

靈祐

và nếu pipeline hỗ trợ:

潙山靈祐

Mục tiêu:

Nếu local verified value tồn tại:
phải biết pipeline hiện tại có sử dụng nó hay không.

Nếu không tồn tại:
xác định API nào tạo candidate.

Không sửa.

[DELTA-P1d] Gợi ý đã verify (re-verify): route /api/translate/google
(app.py:14332) backend THẬT = MyMemory (api.mymemory.translated.net)
— tên route ≠ provider; translate_hvdic :14310 = hvdic.thivien.net;
translate_all :14353 gọi hvdic trước rồi google/MyMemory. Person name path
khác: admin_namevi_translate_local (:16075) đọc CUSTOM_HANVIET + _HV_CACHE
và GHI thẳng name_vi_map (name_vi_auto, confidence 0.5, source
'local_translate').

==================================================
9. AUDIT LLM PATH
==================================================

Kiểm tra Qwen/Groq translation path.

Đặc biệt tìm xem model hiện nhận được context nào cho person name.

Test/audit case:

Input:
靈祐

Expected identity context nếu hệ thống đã có:

DILA_ID = A001984
HAN_NAME = 靈祐
CANONICAL_VI = Linh Hựu

Nếu model trả:

Linh Hữu
hoặc
Quy Sơn Linh Hữu

phải xác định hiện tại system có cơ chế:

- reject
- override
- review
- hoặc accept

KHÔNG thay đổi behavior.

==================================================
10. AUDIT CACHE
==================================================

Tìm translation cache hiện tại.

Xác định:

- table/file
- key
- hash
- rules_version
- prompt/context có nằm trong key không
- canonical identity có nằm trong key không
- stale cache có thể giữ tên sai không

Đặc biệt:

Nếu trước đây model trả:
"Quy Sơn Linh Hữu"

sau này local canonical được xác định:
"Linh Hựu"

cache cũ có thể tiếp tục trả kết quả sai không?
Phải chứng minh bằng code/key structure.

[DELTA-P1d] Gợi ý đã verify (re-verify): bảng translation_cache,
key = source_hash (sha256(excerpt)[:24]) + source_type
UNIQUE(source_hash, source_type); các cột rules_version, constitution_hash,
selected_rule_codes, glossary_hash CÓ trong key/context; entity_id chỉ là
cột kèm — canonical identity (DILA id) KHÔNG nằm trong hash → cùng text
khác canonical context = cùng key. Chiều ngược lại cũng phải test:
stale cache giữ tên sai vs source data sai (people/name_vi_map) — tách bạch.

==================================================
11. PHẢI PHÂN BIỆT 3 LỚP
==================================================

Audit phải trả lời riêng:

A. CANONICAL IDENTITY

Ví dụ:
A001984
靈祐

B. CANONICAL / APPROVED VI NAME

Ví dụ:
Linh Hựu

C. DISPLAY / TRADITIONAL SURFACE FORM

Ví dụ:
Quy Sơn Linh Hựu

Không được thiết kế:

name_vi = tất cả mọi thứ.
DILA ID mới là identity anchor.
Display name không được tạo ra person mới.

==================================================
12. HARD SAFETY REQUIREMENTS
==================================================

Audit phải kiểm tra hiện tại có/không:

1. Canonical identity hard lock
2. DILA ID preservation
3. Local verified name reuse
4. Transliteration = candidate only
5. LLM = candidate/synthesis only
6. Post-LLM canonical verification
7. Conflict → REVIEW_REQUIRED
8. Unknown → REVIEW_REQUIRED
9. Fuzzy matching = discovery only
10. No automatic canonical promotion
11. Cache cannot override newer canonical evidence
12. Failed validation cannot become GOLD

==================================================
13. MANDATORY TEST CASES
==================================================

Không sửa dữ liệu.

Chạy read-only tests nếu có thể:

TEST-01
靈祐 → A001984
[DELTA-P1a] Bắt buộc: trả CANDIDATE SET (5 id: A001984/A023322/
A023362/A032868/A035586) + tiêu chí disambiguate + status
(đúng = REVIEW_REQUIRED nếu không gỡ được) — KHÔNG trả 1 id đơn.

TEST-02
A001984 → current local Vietnamese data

TEST-03
Search "Quy Sơn Linh Hựu"
→ identify all returned IDs
→ identify why
[DELTA-P1b] Chạy đủ 3 đường: people.name_vi LIKE · name_vi_map.name_vi LIKE
(row A021462 còn sót) · vn_person_authority.name_vi LIKE. Trả về mỗi đường
một danh sách id riêng + lý do.

TEST-04
Compare:
A001984
vs
A021462

TEST-05
Check local dictionary/glossary for:
靈祐 / Linh Hựu

TEST-06
Check transliteration fallback for:
靈祐

TEST-07
Check cache behavior for same source text under different canonical context.
[DELTA-P1d] Dùng key structure đã verify (không có canonical trong hash)
để chứng minh/giả thiết kết quả, ghi rõ cách verify read-only.

Nếu test nào không thể chạy:
ghi rõ lý do, không tạo mock.

==================================================
14. KIỂM TRA TƯƠNG THÍCH HỆ THỐNG CŨ
==================================================

Audit compatibility với:

T05
T51g
T68
T71
T72
T79
T78
T94
T95
T110
T123
T126
BUG-025

Đặc biệt KHÔNG tạo resolver/cache thứ hai nếu hệ thống đã có resolver tương đương.
Phải xác định:

REUSE
hay
EXTEND
hay
REPLACE

và tại sao.

==================================================
15. OUTPUT BẮT BUỘC
==================================================

Trả report theo format:

# T176-PHASE0C AUDIT REPORT

## 1. VERDICT
PASS / PARTIAL / BLOCKED

## 2. REAL CALL CHAIN
UI → ... → final

## 3. DILA IDENTITY
A001984 / 靈祐

## 4. LOCAL VI
Current evidence

## 5. DISPLAY NAME
Current evidence

## 6. BUG-025 ROOT CAUSE

## 7. 22 DICTIONARIES
Actual list + lookup path

## 8. TTL/XML
Actual lookup/index path

## 9. TRANSLITERATION
Actual priority

## 10. LLM
Actual context + validation

## 11. CACHE
Actual key + stale-cache risk

## 12. EXISTING RESOLVERS
REUSE / EXTEND / REPLACE

## 12b. OVERLAP WITH T174/T166/T171   [GIỮ CHỐT CŨ — bắt buộc]
Đối chiếu phần audit này với:
- T174 (Phase 0 reuse-first + canonical guard) — phần trùng / phần DELTA
- T166 (CanonicalLock SPEC đã duyệt) — safety nào đã có sẵn, audit này chỉ verify
- T171 (alias/name chuẩn hóa) — minimal fix map vào đâu
Ghi rõ: OVERLAP (không làm lại) / DELTA (audit này thêm) / CONFLICT (mâu thuẫn, cần Admin).

[T195] NGUỒN 12 SAFETY RULES — trỏ ĐÚNG file (sửa lỗi tham chiếu):
  ✅ Nguồn chuẩn = `docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md`
     (đã duyệt, code hiện hành ở `canonical_lock.py`).
  ❌ KHÔNG phải `X-T171` §12 — X-T171 §12 tên là "Quan hệ", KHÔNG chứa
     danh sách safety rules. Đừng trích §12 của T171 làm căn cứ.
  Agent phải đọc `X-T166-canonical-identity-guard-SPEC.md`, đối chiếu từng
  rule với `canonical_lock.py` thật, và ghi rule nào ĐÃ có / CHƯA có.
  Lưu ý bộ file T166 trong repo: `X-T166-canonical-identity-guard-SPEC.md`,
  `X-T166-canonical-identity-guard.md`, `X-T166-phase45-continue-REVIEW.md`,
  `X-T166-review-reconciliation.md` — SPEC là bản gốc, `-REVIEW`/
  `reconciliation` là phụ.

[T195] ⚠ CONFLICT cần Admin chốt (không tự quyết):
  `X-T171 §3.2` thiết kế `person_name_alias` làm bảng alias **đầy đủ**;
  DB thực tế lại dùng `person_display_names` (chỉ 8 row, thiếu cột alias
  đầy đủ, không có `person_id` trùng lặp theo nhiều hình thức).
  ⇒ Fix theo hướng nào: (a) additive vào `person_display_names` (ít rủi ro,
  đúng DB hiện tại), hay (b) tạo `person_name_alias` theo SPEC (đúng thiết kế,
  cần migration — vi phạm §1)?
  Audit ĐỀ XUẤT (a) + ghi CONFLICT, KHÔNG tự tạo bảng.

[T194-P0] LƯU Ý BẮT BUỘC về "minimal fix map vào T171":
`person_name_alias` (SPEC T171 §3.2) là bảng **TARGET, CHƯA MIGRATE** —
`no such table` trong lineage.db. Nếu fix "map vào đây" thì phải TẠO BẢNG,
vi phạm §1 (cấm tạo migration/bảng mới).
Bảng **đã build** và đúng cấu trúc A/B/C là **`person_display_names`** (8 row):
  authority_name_vi (B) + display_name_vi (C) + is_preferred
  + verification_status + appellation_vi + source_predicate/source_ref
Cộng `person_name_correction` (2.433 row) cho hàng chờ sửa.
→ Minimal fix map vào `person_display_names` (additive row), KHÔNG
  tạo `person_name_alias`. Nếu Admin muốn bảng alias đầy đủ thì đó là
phase code riêng sau APPROVED FIX, phải nêu ở §15 chứ không audit ở đây.

## 13. HARD SAFETY GAPS
List only evidence-backed gaps

## 14. MANDATORY TEST RESULTS
TEST-01 ... TEST-07

[T195] TEST BẮT BUỘC BỔ SUNG (bổ sung vào danh sách trên, không thay thế):
  TEST-08 · sai-thanh: `Linh Hựu` (exact) → A001984; `Linh Hữu` → KHÔNG
             được coi là biến thể hợp lệ (3 id đang mang thanh sai).
  TEST-09 · khớp chính xác, KHÔNG prefix: `Linh Hựu` + `name_zh='靈祐'` → 1
             kết quả A001984. Cấm `LIKE 'Linh H%'` (fan-out 6 người).
  TEST-10 · đồng âm: `Quy Ngưỡng` → KHÔNG resolve A001984 (khác 圭仰宗).
  TEST-11 · khoảng trắng: đọc A001984 qua cả `marcus_reference` và
             `vn_person_authority` sau TRIM phải ra `靈祐` giống nhau.
  TEST-12 · lớp nhiễu (ii): `Quy Sơn Linh Hựu Thiền Sư Ngữ Lục` (tên sách,
             id=2271) → search KHÔNG được trả về như một người.
  TEST-13 · neo chéo: `marcus_ids` của id=4689 KHÔNG được chứa A027031
             (法端 Pháp Đoan — vị khác).
  TEST-14 · B và C: `authority_name_vi='Linh Hựu'` + `display_name_vi=
             'Quy Sơn Linh Hựu'` phải truy ra được từ
             `person_display_names` (advisory hiện 0 row cho A001984).

## 14b. AMBIGUITY_RESULT   [GIỮ CHỐT CŨ — bắt buộc]
Liệt kê mọi điểm mơ hồ đã gặp (đặc biệt TEST-01 5 id của 靈祐,
"Linh Hựu" vs "Quy Sơn Linh Hựu", status vnpa alias_vi_suffix):
mỗi dòng = case · evidence · phương án resolve · REVIEW_REQUIRED hay không.

## 15. MINIMAL FIX DESIGN
Không code.
Chỉ architecture-level proposal.

## 16. REGRESSION TEST PLAN

## 17. FILES/FUNCTIONS/TABLES TO MODIFY
Chỉ nêu những gì đã xác minh thực tế.

## 18. RISK / SCOPE

## 19. FINAL
BUILD READY
hoặc
NOT BUILD READY

DỪNG TẠI ĐÂY.
Không build.
Không commit.
Không sửa DB.
Không sửa code.
```

---

## 4. Phases & Gates (T176)

| Gate | Nội dung |
|---|---|
| **G0** | Admin duyệt task này (docs-only, 0 code/0 DB/0 commit) |
| **G1** | Admin paste **§3** → Claude Code trả **T176-PHASE0C AUDIT REPORT** (19 + §12b + §14b) |
| **G2** | Admin review report → chốt `BUILD READY` / `NOT BUILD READY` |
| **G3** | Chỉ khi `BUILD READY` + lệnh `APPROVED FIX` → mở phase code (tách commit riêng từng bước, `npm run pipeline` trước mỗi commit) |

## 5. Revert

Docs-only session này: `git revert --no-edit <sha_T176>` (sha trong `docs/ROLLBACK.md`, hash-fill sau commit).

## 6. Session

`docs/sessions/2026-09-25_t176-phase0c-rev2-audit-plan.md`
⚠️ **[T194] File này CHƯA TỒN TẠI** trong repo (verified). Session log thật
của phiên sửa doc này: `docs/sessions/2026-09-29_t194-t176-plan-doc-correction.md`.
Khi Admin chạy audit phase 0C thì tạo session log mới theo ngày chạy.

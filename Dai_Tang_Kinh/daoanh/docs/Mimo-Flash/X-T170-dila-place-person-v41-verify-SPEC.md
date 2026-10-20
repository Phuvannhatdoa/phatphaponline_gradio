---
id: T170
title: "Hardened v4.1 Verify Pipeline — Place + Person (2 side-car) — Chuẩn hóa danh xưng tu sĩ DILA"
module: Editorial / LLM Translation
priority: high
status: built
owner: claudecode
depends_on: [T169]
created: 2026-09-25
updated: 2026-09-28
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: Đồng ý build · (1) 2 side-car · (2) task T170 · UI person defer) + Red-team amend (Admin: 1) amend T170 · 2) CJK tự seed · 3) salvage JSON yes)"
done_when: |
  Migrate person_groq_audit (place_groq_audit giữ nguyên T169, chỉ tạo person side-car, 0 ALTER bảng lớn);
  script refactor/extend T169 --entity {place,person} absorb v4.1 + R2–R8 red-team (nested bracket,
  CJK variant fold, title multi-token, busy_timeout, flat-JSON salvage,
  max_tokens partial salvage, guard spine) — R1 + P1-8 (行) đã absorbed T169; pytest base t169 11/11 + person ≥6 + ≥5 red-team
  PASS; npm run pipeline PASS;
  revert = git revert + migrate --revert --entity person (place revert qua T169 script).
  [2026-09-28 · T189] CODE-BUILD = DONE (xem §12 BUILD CLOSURE). ACCEPTANCE còn Nợ (gate §8 ②–④):
  validate-only + pilot 25/entity + admin duyệt → chờ GROQ key chạy trên VPS.
---

# T170 — Hardened Production Pipeline v4.1: Place + Person (2 Side-Car)

> **Directive gốc (2 file Admin):** (A) “Chuẩn Hóa Danh Xưng Tu Sĩ DILA Persons” · (B) “Addendum v4.1 Hardened 57k Place”.
> **Review 2026-09-25:** DB thật + T169 → **6 P0 + ~11 P1** (§2–§3).
> **Admin chốt:** **(1) 2 side-car** · **(2) Task mới T170** (T169 giữ nguyên, cross-ref) · UI person **defer** · **docs-only** lần này.
> **Red-team 2026-09-25** (Báo Cáo Phản Biện Bugs & Edge Cases) → **§3bis R1–R8 AMEND** · Admin: **amend T170** (không T171) · CJK seed **không chờ Admin** · **salvage JSON = YES** · verdict **BLOCKED until R1–R8 absorb**.
>
> **📌 [2026-09-28 · T169-BUILD re-check] — IMPORTANT** Premise ban đầu **"T169 docs-only / 0 file tồn tại → build mới từ zero" là SAI**: T169 **đã build + commit** (`393676f` feat + `4c8228b` docs, pipeline PASS) vào 2026-09-28. Sửa theo bảng S1–S9 (bên dưới):
> - `scripts/verify_dila_places_groq.py` + `tests/test_t169_classify_diff.py` (11/11 PASS) **đã tồn tại** → T170 = **refactor/extend**, KHÔNG build mới.
> - `place_groq_audit` **đã apply trên DB thật** (13 cột, 2 index, backup `data/backups/lineage_t169_20260928_130129.db`) → migrate T170 **chỉ tạo `person_groq_audit`**, giữ bảng place (guard: không DROP/recreate).
> - `行` trong `POLYPHONIC_CHAR` + core `R_d≠R_g` (word-token) **đã nằm trong `t169_classify.py:22,98-110`** → §3.1 #8 / §3bis R1 đánh dấu **absorbed**.
> - API/UI place (GET/PUT `place-groq-review` + `admin/place_update.html`) **đã build T169** → Phase 5 place = đối chiếu enum mới, không xây lại.
> - Enum/diff mới (§3.4) phải rà **app.py GET sort CASE + UI tabs T169** (4 status cũ) để không phá behavior đã commit.

---

## 0. Quyết định Admin (locked)

| # | Quyết định |
|---|------------|
| 1 | **2 bảng side-car:** `place_groq_audit` (PK `places_dila.id`) + **`person_groq_audit`** (PK `people.id`). **CẤM** ALTER `people` / `places_dila` / `places_pending` / `places`. |
| 2 | Task **T170** mới · SPEC độc lập · phụ thuộc T169 (share pattern §6–§7 UI/API) · T169 không sửa. |
| 3 | **UI person defer** — phase cuối (sau place UI T169). T170 đóng: migrate + classify + script 2 entity + tests. |
| 4 | **Lần này docs-only** — code build session dev sau. |
| 5 | **Red-team amend gộp T170** (Admin 2026-09-25) — không tạo T171 · SPEC này là SSOT duy nhất. |
| 6 | **CJK variant fold: tự seed** từ cặp đã verify + mở rộng chủ đích — **không chờ Admin** bảng duyệt. |
| 7 | **Salvage truncated JSON = YES** — partial batch ghi được item hợp lệ · item cụt = record-level missing (không reject cả batch). |

---

## 1. OUT OF SCOPE

- Không ALTER bảng lớn · không sửa T165 code đang tre · không TPM hard-gate.
- Không gọi LLM `id` NULL/rỗng · không chạy production trước acceptance §8.
- UI person chưa làm (đã chốt defer).

---

## 2. P0 — Directive sai sự thật (verify 2026-09-25)

| # | Directive ghi | Sự thật | Sửa thành |
|---|---------------|---------|-----------|
| P0-1 | `data/database.sqlite` | **Không tồn tại** (tái phạm từ review T169) | `data/lineage.db` |
| P0-2 | Bảng `dila_places` + `ensure_schema` ALTER 15 cột | **Bảng không có** · Admin chốt A → side-car | `place_groq_audit` · idempotent PRAGMA trên **side-car** |
| P0-3 | `trans_dict_vi` (SELECT + SQL Admin) | **0 bảng có cột** | Place: `places_pending.name_vi` (JOIN `places_dila`) · Person: **`people.name_vi`** |
| P0-4 | Bảng `dila_persons` (EntityConfig + mọi SQL person) | **Không tồn tại** · chỉ có ở `roadmap.md` · **`people`** = 48.673, id `A000001`…, **0 NULL**, `name_zh`+`name_vi` **đủ 48.673** · `people_full` = 0 | Person spine = **`people`** · side-car PK `people.id` |
| P0-5 | “Nâng cấp `scripts/verify_dila_places_groq.py` v4.1” + `tests/test_dila*.py` | **Đã tồn tại** T169 (`verify_dila_places_groq.py` + `test_t169_classify_diff.py` 11/11 PASS, commit `393676f`) | **REFACTOR/EXTEND** absorb body v4.1 · thêm `--entity person` · SQLite lock (R5) · json save (R6) · chia-nhỏ checkpoint (R7) |
| P0-6 | `GROQ_API_KEY` env-only · model `qwen/qwen3.8-27b` | Trái repo pattern `llm_config.json` · model chưa verify | `resolve_groq_key()` env→llm_config → abort · fallback bỏ `response_format` nếu 400 |

**Mâu thuẫn T169:** body v4.1 ghi `final_vi`… vào bảng production = vi phạm chốt A → **chuyển hết cột verify sang 2 side-car**.

---

## 3. P1 — Fix classify + pipeline

### 3.1 Place (`evaluate_and_resolve` v4.1 body)

| # | Bug | Fix |
|---|-----|-----|
| 1 | POLYPHONIC `matched_readings >= 1` → giả positive khi 2 bản **cùng** 1 đọc | `R_d = readings∩norm_dict`, `R_g = readings∩norm_groq` → chỉ nhãn khi **`R_d ≠ R_g`** (hoặc 1 bên ∅, bên kia ≠ ∅) |
| 2 | `TAXONOMY_PAIRS` còn nest `('viện','tự viện')` · `extract` strip 1 đầu | Bỏ cặp nest · strip **cả 2 đầu** khi core khớp |
| 3 | Status/diff mới (`auto_*`, `needs_lexicon_review`, `processing`, `SANSKRIT_*`, `TITLE_VARIANT`, `FORMAT_NORMALIZED`, `API_EMPTY_RESPONSE`) lệch enum T169 | **Enum mở rộng** (§3.4) — 2 phía cùng schema side-car |

**[2026-09-28 · T169-BUILD]** Rog 1 (R_d≠R_g) **đã absorb trong `t169_classify.py:98-110`**: `classify_diff` dùng token-level `r_d != r_g and (r_d or r_g)` — khác premise cũ "vẫn `len(matched)>=1`". Việc còn lại của T170 = test regression + áp logic này cho `--entity person`. Rog 2 (strip cả 2 đầu / bỏ cặp nest `viện/tự viện`) → `t169_classify.py:53-60` taxonomy **word-boundary**, khong nest — DONE. (Sửa regenerate §3bis R1/R2 email để tránh lặp.)

### 3.2 Person

| # | Bug | Fix |
|---|-----|-----|
| 4 | TITLE (step 4) **sau** Sanskrit (step 3): variants không chứa `'thiền sư đạt ma'` → false `needs_lexicon_review` | So variants trên **core sau `extract_person_core` strip** · **hoặc** thêm variants tôn xưng · test `道安` + suffix |
| 5 | Suffix 2-word: `len(words)>=3` **chỉ** — `"thiền sư"` (2 token) không bao giờ khớp 1-word branch | Check suffix 2-word khi **`len>=2`** · thêm test edge |
| 6 | `person_sanskrit_indicators` substring tĩnh — thiếu stem → rơi `PHONETIC_MISMATCH` mất nhãn `SANSKRIT_UNMAPPED` | Indicator = **mọi key registry** có `stem in clean_zh` + list stem mở rộng (`真諦`, `僧肇`, `道安`…) |
| 7 | `preferred_title` `'Thích' in title_groq` case-fragile · ưu groq mù | Base = **dict** · chỉ ghép prefix groq khi core equal · ghi `final_vi_source` |
| 8 | `POLYPHONIC_CHARS` place **thiếu `行`** (chỉ person có) → place 一行 lệch không dán POLYPHONIC | **[absorbed T169]** `t169_classify.py:22` **đã có** `'行': ['hành','hạnh','hàng']` → đánh dấu DONE; chỉ thêm test regression nếu muốn |

### 3.3 Giữ nguyên v4.1 (đúng)

COALESCE không xóa cũ · invalid/unexpected/dup → **reject batch** + retry → `api_error` @MAX · vi rỗng = record-level · `--validate-only` (0 call, 0 ghi) · `--pilot 25` (đổi tên từ dry-run) · stale `processing` reset 30' · 429 backoff · schema inspection batch 0 · log `batch_id` · **flush batch dư cuối** · `safe_title_case` (giữ acronym/Roman — sửa `[IVXLCDM]` case-insensitive nếu test lowercase `ii`) · strict Sanskrit **cả 2 bên** ∈ variants.

### 3.4 Enum side-car (mở rộng, thống nhất 2 bảng)

```text
review_status: pending | processing | verified | conflict | api_error |
               approved_dict | auto_verified | auto_verified_sanskrit |
               auto_title_aligned | auto_taxonomy_aligned | needs_lexicon_review
diff_type: NONE | FORMAT_NORMALIZED | POLYPHONIC_CHAR | TAXONOMY_VARIANT |
           PHONETIC_MISMATCH | TITLE_VARIANT | SANSKRIT_VARIANT |
           SANSKRIT_VARIANT_UNCONFIRMED | SANSKRIT_UNMAPPED | API_EMPTY_RESPONSE
```

---

## 3bis. AMEND R1–R8 — Red-Team 2026-09-25 (Admin: gộp T170 · BLOCKED until absorb)

> **Nguồn:** “Báo Cáo Phản Biện Kỹ Thuật: Red-Team Bugs & Edge Cases Pipeline DILA” (DIRECTIVE_PERSON_VERIFIER_PATCH + ADDENDUM v4.1).
> **Verdict red-team:** BLOCKED FOR CODING — giữ BLOCKED tới khi R1–R8 nằm trong build.
> **Admin chốt:** (1) amend **T170** (không T171) · (2) CJK seed **không chờ Admin** · (3) **salvage = YES**.
> **Verify DB trong review:** `That` = đúng · `GIẢM` = severity hạ · `BẤT HỢP` = fix red-team bị sửa lại (R1–R3).

### Bảng đối chiếu Bug red-team ↔ verify ↔ absorb

| Mã bug red-team | Mức báo cáo | Verify 2026-09-25 | Absorb |
|-----------------|-------------|-------------------|--------|
| 1.1 substring `na`⊂`nam` | CRITICAL | `That` (`That` 114 place chứa `那`) | **R1** |
| 1.2 regex ngoặc lồng | HIGH | `That` — thật: `開元路((黃龍府))`, `(孟力)(合手手)` ∈ places_dila | **R2** |
| 1.3 CJK variant (峯/惠…) | MEDIUM | `That`+nâng HIGH: 峰/峯 309/210 · 惠/慧 place 108/194 · people **346/1470** · 羣/秘 >0 | **R3** |
| 1.4 prefix/suffix >2 token | HIGH | `That` — thật: `Tam Tạng Bàn Nhược`, `Đại Thiện Quốc Sư` | **R4** (gộp P1-5) |
| 2.1 hardcode `dila_places`/`dila_persons` | CRITICAL | `That`+nặng hơn: **2 bảng không tồn tại** | **R3-guard** (config cứng T170 §2) |
| 2.2 `trans_dict_vi` | CRITICAL | `That` · `places_dila` **không có name_vi** | đã P0-3 · **cấm** fallback đoán cột (báo F3 **BẤT HỢP**) |
| 3.1 SQLite lock thiếu WAL | HIGH | `GIẢM`→MEDIUM: DB **đã `journal_mode=wal`** · thiếu `busy_timeout` (thực đo **5000**, Python default `timeout=5.0`) · T169 script vẫn set lại WAL (dòng 75) | **R5** (set 10000, xóa WAL pragma ở refactor) |
| 3.2 ID CAST collision | CRITICAL | `BẤT HỢP`→LOW: `people.id`/`places_dila.id` = **đã TEXT** | strike · vẫn giữ `str(id)` mọi tầng |
| 4.1 Qwen flat JSON `{“A001”:“vi”}` | MEDIUM | `That` — `safe_parse`→`[data]` không key `id` → reject oan | **R6** |
| 4.2 truncation `max_tokens` | HIGH | `That` — reproduce `Unterminated string` | **R7** |

### R1 — Polyphonic v3: word-set ∩ **+** `R_dict ≠ R_groq`

> **[2026-09-28 · T169-BUILD]** Logic này **đã absorb trong T169** (`t169_classify.py:98-110`): `classify_diff` so token nguyên vẹn, flag khi `r_d != r_g and (r_d or r_g)`. Ví dụ `那`-1 bên rỗng vẫn flag (P1-1), `khách hàng` không còn FP. **Phần còn lại của T170 = test regression** (mục tiêu Test dưới đây) **cho cả `--entity person`**, không viết lại thuật toán.

- **Báo cáo fix chưa đủ:** vẫn `len(matched)>=1` → 2 bản **cùng** 1 đọc vẫn conflict oan (`Na Lan Đà X` vs `Na Lan Đà Y` → matched=`['na']`).
- **Còn FP:** `'hàng' in set('khách hàng'.split())` = **True** → word-set 1 mình không chặn hàng/khách hàng.
- **Fix bắt buộc:** so **từ nguyên vẹn** (`set(split())`) **VÀ** chỉ flag khi tập reading 2 bên **khác nhau**:
  - `R_d = readings ∩ words_dict` · `R_g = readings ∩ words_groq`
  - flag `POLYPHONIC_CHAR` khi `(R_d or R_g) and (R_d != R_g)` (1 bên ∅, bên kia ≠∅ → flag).
- Test: `Đại Nam` vs `Đại Nam Quốc` + `那` → **không** POLYPHONIC · `Nhất Hạnh` vs `Nhất Hành` → **có** · cùng đọc → **không**.

### R2 — Bracket parser lồng nhau

- Thay regex 1 lớp bằng **stack/đệ quy**: quét khớp `(`/`[`/`（`/`［` mở–đóng · mọi span ngoặc → `meta_note` · phần còn lại → `clean_zh`.
- Chặn `)`/`]` thừa rơi vào `clean_zh` (sau strip còn `()[]（）` → strip tiếp hoặc fail-safe `is_uncertain=1`).
- Test: `開元路((黃龍府))` → `clean_zh=開元路`, `meta=((黃龍府))` · `一行(俗姓張, 一作張遂(唐))` → meta đầy đủ, `clean_zh=一行`.

### R3 — CJK variant fold (tự seed, không chờ Admin)

- **NFKC không đủ** (峯/峰 là 2 unified ideograph khác nhau) → **bảng map chủ đích** `CJK_VARIANT_FOLD`.
- Seed tối thiểu (đã verify counts): `峯→峰`, `羣→群`, `祕→秘`, `惠→慧` + mở rộng chủ đích khi gặp variant mới trong log (`fold_unmapped` warning để bổ sung).
- Áp: **trước** mọi exact lookup (Sanskrit registry, taxonomy, compare) — `fold_cjk(clean_zh)` 1 lần ở khâu `clean_dila_name`.
- Test: `峯頂寺` ≡ `峰頂寺` → cùng canonical/diff · `惠能` fold → `慧能` khớp `PERSON_SANSKRIT_REGISTRY`.
- **R3-guard (2.1/2.2):** config **cứng** 2 entity theo T170 §2 (spine `places_dila`/`people`, dict `places_pending.name_vi`/`people.name_vi`) · **cấm** `get_entity_table_config` đoán `trans_dict_vi`/`person_name_zh` (F2/F3 red-team = **BẤT HỢP**) · guard abort nếu spine table không tồn tại (`PRAGMA table_info` rỗng ≠ throw).

### R4 — Title extract multi-token (gộp P1-5)

- Thay check 2-word cứng bằng **loop strip**: lặp khi token đầu ∈ `PERSON_PREFIX_TITLES` (1 hoặc 2 token) · tương tự suffix cuối · không giới hạn số lần · core ≥1 token.
- Test: `Tam Tạng Pháp Sư Huyền Trang` → core `Huyền Trang` · `lục tổ đạo an` → core `đạo an` · suffix `… thiền sư` (2 token, `len>=2`).

### R5 — SQLite concurrency (đã WAL)

> **[2026-09-28 · T169-BUILD]** Verify DB: `journal_mode=wal` ✓ · `busy_timeout` thực tế = **5000** (Python `sqlite3` default `timeout=5.0`, không phải 0 như mô tả cũ) · T169 script `verify_dila_places_groq.py:75` **lại set `PRAGMA journal_mode=WAL`** → khi refactor T170 **phải xóa dòng này** (giữ "không set lại WAL").

- **Không** `PRAGMA journal_mode=WAL` lại (đã `wal`; xóa pragma đang có ở T169) · **bật** `PRAGMA busy_timeout=10000` + `PRAGMA synchronous=NORMAL` (giữ) ở mỗi connection mở đầu script.
- Test/verify: 2 connection đọc+ghi đồng thời batch → không `database is locked` trong 10s.

### R6 — Flat JSON salvage

- Trước schema check: nếu parsed là `dict` **không** có key `items/places/data/results` mà mọi value là `str` → `items = [{"id": k, "vi": v} for k,v in data.items()]` (an toàn: id phải ∈ `expected_ids`, lạ → vẫn unexpected).
- Test: mock response flat `{"P1":"Bạch Mã Tự"}` → record verified, **không** batch-reject.

### R7 — Truncation salvage (Admin: YES)

- Set `max_tokens` explicit (đủ batch 25 · ví dụ 2048–4096, log nếu cut).
- Nếu `json.loads` fail **Unterminated** → thử **salvage**: đóng thừa `"]}` / `}` rồi parse lại · item cuối dở chừng → **bỏ item cụt**, giữ item hợp lệ (partial success) · id thiếu = record-level missing (COALESCE) · **không** reject cả batch chỉ vì truncation.
- Test: JSON cắt giữa item 23 → 22 item đầu ghi được · item 23+ = missing · retry_count chỉ tăng cho missing.

### R8 — Observation/ops

- `str(id)` mọi tầng (giữ) · ghi `fold_unmapped` + `salvage_used` vào `last_error`/log để Admin rà · test tổng ≥**5** red-team cases (R1–R7) nằm trong §6.

**Exit BLOCKED khi:** R1–R8 có trong SPEC build (file này ✓) **và** pytest red-team cases PASS trước pilot (§8 gate ①).

---

## 4. SCHEMA — 2 side-car (additive, 1 migrate script)

> **[2026-09-28 · T169-BUILD]** `place_groq_audit` **đã tồn tại trên DB thật** (T169 migrate; 13 cột; idx_pga_review/idx_pga_diff; backup `data/backups/lineage_t169_20260928_130129.db`). Migrate T170:
> - **place = giữ nguyên bảng T169** (guard: `place_groq_audit` tồn tại → verify 13 cột khớp, **KHÔNG DROP/recreate**).
> - **Chỉ tạo mới `person_groq_audit`** + idx_gpa_review/idx_gpa_diff.
> - `--revert` T170 chỉ DROP person side-car; bảng place thuộc về T169 (`t169_place_groq_audit_migrate.py --revert`).

```sql
-- scripts/t170_entity_groq_audit_migrate.py --entity {person} --stats|--dry-run|--apply|--revert   (place: giữ T169)
-- person: PK = people.id   ·   place: PK = places_dila.id (không đụng)
CREATE TABLE IF NOT EXISTS person_groq_audit (
  id TEXT PRIMARY KEY,             -- people.id (A000001…)
  name_zh TEXT, dict_vi TEXT,      -- snapshot people.name_zh / name_vi
  groq_trans_vi TEXT, final_vi TEXT,
  clean_zh TEXT, meta_note TEXT, variant_zh TEXT, is_uncertain INTEGER DEFAULT 0,
  needs_review INTEGER DEFAULT 0,
  review_status TEXT DEFAULT 'pending',   -- enum §3.4
  diff_type TEXT, diff_reason TEXT,
  model_id TEXT, batch_id TEXT,
  prompt_tokens INTEGER, completion_tokens INTEGER,
  retry_count INTEGER DEFAULT 0, last_error TEXT,
  processing_started_at TIMESTAMP, checked_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_gpa_review ON person_groq_audit(needs_review, review_status);
CREATE INDEX IF NOT EXISTS idx_gpa_diff   ON person_groq_audit(diff_type);
```

- Backup `data/backups/lineage_t170_<ts>.db` trước `--apply` (sqlite backup API, Zero-RAM).
- `--revert`: DROP **person** 1 bảng + index IF EXISTS · **không** chạm bảng lớn · **không** chạm `place_groq_audit` (T169).

---

## 5. SCRIPT — `scripts/verify_dila_places_groq.py` (**REFACTOR/EXTEND** — đã build T169, commit `393676f`)

**[2026-09-28 · T169-BUILD]** KHÔNG build mới từ zero. Giữ nguyên code T169 đã chạy pipeline-tested: batch 25 · sleep 2 · `:cursor` in-memory + resume · RPM adaptive (window 60s vs 6.000 TPM) · atomic UPSERT · mock (`--mock`) · json_object fallback trên 400/422 (`verify_dila_places_groq.py:298`) · `max_tokens=512`. **THÊM** các dòng còn thiếu dưới đây (đánh dấu `+`).

Absorb toàn bộ body v4.1 directive + T169 §5:

| Item | Chi tiết |
|------|----------|
| Config | `--entity {place,person}` · `DB_PATH=data/lineage.db` · `resolve_groq_key()` · model default `qwen/qwen3.8-27b` · `--validate-only` · `--pilot N` · **`+busy_timeout=10000`** (R5) · **bỏ** `PRAGMA journal_mode=WAL` đang set (T169:75) |
| `EntityConfig` | person: table spine **`people`**, `PERSON_POLYPHONIC_CHARS` + `PERSON_SANSKRIT_REGISTRY` + prompt person (directive §2–§3) · place: `places_dila` + `POLYPHONIC_CHARS` (**`行` đã có** — không thêm lại) + `SANSKRIT_REGISTRY` + prompt place · **config cứng** — cấm đoán cột (R3-guard) |
| Preprocess | `clean_dila_name` + **`+bracket stack`** (R2) + **`+fold_cjk`** (R3, seed 峯/羣/祕/惠) trước registry/compare |
| Polyphonic | **R1:** đã absorb T169 (word-token `R_d ≠ R_g`); giữ, thêm test regression |
| Title | **R4 (person):** `+loop strip` prefix/suffix multi-token · core ≥1 token |
| Scope SELECT | **place:** (giữ) `places_dila d JOIN places_pending p ON p.id=d.id` → dict `p.name_vi` · **person:** `+people` → dict `name_vi` · filter side-car chưa `verified/conflict/approved_dict` · `id NOT NULL` |
| `ensure_schema` | Idempotent trên **side-car** (PRAGMA) · **guard:** abort nếu spine table không tồn tại (chống P0-2/4 tái diễn) |
| Batch | 25 · sleep 2 · reject batch (invalid/unexpected/dup) · COALESCE · stale reset · remainder flush · `str(id)` mọi tầng |
| Groq parse | **`+flat dict → items`** (R6) · **`+max_tokens` explicit 2048–4096** (T169 đang 512) + **`+truncation salvage partial`** (R7, Admin YES) · `+salvage_used` log |
| Key/model | env→`data/llm_config.json.groq_key` · `response_format` fail → retry **không** response_format + fence-strip |
| Observability | schema log batch 0 · token/request + **window 60s** vs 6.000 TPM · log `batch_id` mỗi batch · `+fold_unmapped` warning |
| Ghi | UPSERT **side-car** không UPDATE spine — place→`place_groq_audit` (T169 đã làm) · person→`person_groq_audit` (`+`) · resume skip done · `--force` redo |

**Log:** stdout UTF-8 + session file khi chạy VPS (`docs/sessions/<date>_t170-run.md`).

---

## 6. TESTS

**[2026-09-28 · T169-BUILD]** Base **`tests/test_t169_classify_diff.py` (11/11 PASS)** giữ nguyên, import module `scripts/t169_classify.py` — KHÔNG tạo bản song song trùng fixture. T170 thêm các file/trường hợp MỚI (person + red-team R2/R3/R6/R7 + regression R1/P1-8).

| File | Ngưỡng |
|------|--------|
| `tests/test_t169_classify_diff.py` (base T169) | **11/11** giữ nguyên (fixture bắt buộc + word-boundary TAXONOMY + nest cấm + PHONETIC fallback + validate) |
| `tests/test_t170_person_classify.py` | **17/17** (R2 bracket lồng/unbalanced · R3 fold 惠→慧 · R4 title multi-token · Sanskrit khớp/lệch/UNMAPPED · TITLE_VARIANT · POLYPHONIC · FORMAT · NONE) |
| `tests/test_t170_verify_pipeline.py` | **15/15** (R6 flat/nested/fence/regex/empty · R5 pragma · TAXONOMY self-match regression · place cursor/G4 · person extras/G4) |

> **[2026-09-28 · T189]** Tên test thật = `test_t170_person_classify.py` + `test_t170_verify_pipeline.py` + `test_t169_classify_diff.py`
> (thay cho tên cũ đề xuất `test_dila_verifier_v3.py` / `test_dila_person_verifier.py` / `test_t170_redteam.py` trong bản draft — đã build theo tên mới, xem §11).
| Fixture khóa | Place: 降魔窟=POLYPHONIC · 白馬寺=TAXONOMY · 少林寺=NONE · 那爛陀寺+Thiếu Lâm=UNCONFIRMED · Person: 一行 Nhất Hạnh/Hành · 道安±Thích · 菩提達磨 Bồ Đề Đạt Ma |

---

## 7. API/UI (theo T169 §6–§7 · place trước · person defer)

> **[2026-09-28 · T169-BUILD]** Place API/UI **đã build T169** (GET/PUT `/daoanh/api/admin/place-groq-review` + `admin/place_update.html` 2 cột + `scripts/e2e-test.js` 5 pages). T170 phase 5 place = **đối chiếu enum mở rộng** (§3.4) với GET filter + UI tabs (4 trạng thái hiện có: conflict/api_error/verified/approved_dict) — không xây lại.

- Place: `GET/PUT /daoanh/api/admin/place-groq-review` + `admin/place_update.html` 2 cột (SPEC T169).
- Person: **defer** — API pattern y hệt `person-groq-review` · UI `person_update.html` **phase cuối** (đã chốt Admin).

---

## 8. ACCEPTANCE (gate production)

```text
① pytest tests/test_t170_person_classify.py tests/test_t170_verify_pipeline.py tests/test_t169_classify_diff.py -v → 100% PASS
   (red-team R1–R7 ≥5 case — exit BLOCKED, xem §3bis)
② python scripts/verify_dila_places_groq.py --validate-only --entity place|person → 0 error, 0 write
③ --pilot 25 --entity place  → log batch_id → SQL trên place_groq_audit
④ --pilot 25 --entity person → log batch_id → SQL trên person_groq_audit
⑤ Admin duyệt: 0 api_error lô pilot · 0 Sanskrit auto-approve sai · final_vi/diff/review đúng enum
   · log không có FP POLYPHONIC hàng loạt (R1) · fold_unmapped/salvage_used rà (R3/R7)
⑥ npm run pipeline PASS
⑦ Production mới được gỡ --pilot (place ~59k · person ~48.7k)
```

SQL đối soát (side-car, không phải spine):

```sql
SELECT review_status, diff_type, COUNT(*) FROM place_groq_audit
WHERE batch_id='<BATCH_ID>' GROUP BY 1,2;
SELECT id, name_zh, dict_vi, groq_trans_vi, final_vi, review_status, diff_reason
FROM person_groq_audit WHERE batch_id='<BATCH_ID>' ORDER BY needs_review DESC;
SELECT COUNT(*) FROM place_groq_audit WHERE processing_started_at IS NOT NULL; -- = 0
```

---

## 9. PHASES

| Phase | Việc |
|-------|------|
| 1 | Migrate **person** side-car (place giữ T169) `--stats/--dry-run/--apply/--revert` + backup |
| 2 | `EntityConfig` + classify fix (P1 §3) + **R1–R7** (§3bis) + **tests đỏ→xanh** (≥11+≥6+≥5 red-team) |
| 3 | Script `--entity place` + smoke validate + pilot 25 |
| 4 | Script `--entity person` + smoke validate + pilot 25 |
| 5 | API/place UI (**đã build T169**) → đối chiếu enum mở rộng · **person UI defer** |
| 6 | `npm run pipeline` · session run-log · ROLLBACK hash-fill |

**Commit code (toplevel):** `feat: T170 entity verify pipeline v4.1 (person side-car + extend T169) + tests + docs`  
**Revert:** `git revert --no-edit <sha>` + `python scripts/t170_entity_groq_audit_migrate.py --revert --entity person` (**place thuộc T169**: revert bằng `t169_place_groq_audit_migrate.py --revert`)

---

## 10. Quan hệ

- **depends_on: T169** — [2026-09-28] T169 **đã build** (`393676f`/`4c8228b`, 2026-09-28): script/tests/migrate place/API-UI place đều có sẵn → T170 = **absorb code T169** (person mới + R2/R3/R4/R5/R6/R7 + enum mở rộng). Không chặn/đè lệch T169.
- T169 tasktodo: thêm chú “v4.1 absorb → T170” (**không sửa SPEC T169**).
- T165/T168: không đụng.

## 11. Files

| Loại | Path |
|------|------|
| Mới | `scripts/t170_entity_groq_audit_migrate.py` · `tests/test_t170_person_classify.py` (+ `tests/test_t170_verify_pipeline.py` thay `test_t170_redteam.py`/`test_dila_person_verifier.py` — tương đương) · SPEC này · session |
| Refactor/EXTEND (đã có T169) | `scripts/verify_dila_places_groq.py` (`--entity person` + R2–R7) · `scripts/t170_classify.py` (mới) · `scripts/t169_classify.py` (fix TAXONOMY self-match) · `tests/test_t169_classify_diff.py` (giữ) |
| Sửa (phase 5) | `app.py` — đối chiếu enum: **không cần sửa** (auto_* chỉ person; person UI defer) |
| Không đụng | `people`/`places_dila`/`places_pending` schema · **`place_groq_audit` (T169)** · T165 code |

---

## 12. BUILD CLOSURE — [2026-09-28]

- ✅ **Phase 1** migrate person-only `t170_entity_groq_audit_migrate.py --apply` **DB THẬT** — backup `data/backups/lineage_t170_20260928_150114.db` (1.410 MB) · `person_groq_audit` (21 cột) + `idx_gpa_review`/`idx_gpa_diff` · guard `place_groq_audit` 13 cột OK.
- ✅ **Phase 2–4** refactor `verify_dila_places_groq.py` `--entity {place,person}` + `EntityConfig` · `scripts/t170_classify.py` (R2 bracket stack + R3 `fold_cjk` seed 惠/羣/祕/峯 + R4 title loop multi-token + Sanskrit registry + tái dùng `t169_classify.classify_diff` for POLYPHONIC/TAXONOMY/PHONETIC) · **R5** bỏ `PRAGMA journal_mode=WAL` → `busy_timeout=10000` + `synchronous=NORMAL` · **R6** `normalize_groq()` trích `trans_vi` (flat dict/fence/nested/`json_regex` salvage) · **R7** `max_tokens` 512→**2048** + salvage 1 lần gọi lại khi parse thất bại · person upsert ghi thêm `clean_zh/meta_note/variant_zh/is_uncertain/final_vi/retry_count/last_error/processing_started_at` + `SKIP_STATUSES` mở rộng auto_* (G4).
- 🐛 **Bug T169 bắt được khi smoke mock** (đã fix trong T170, có regression test): (1) cursor khởi tạo `''` so với **id (`places_dila.id` thật = TEXT `PL000000000001…`)**: với test-harness place dùng schema INTEGER giả (`test_t170_verify_pipeline.py`), `d.id > ''` rơi về **0 rows** → smoke mock phát hiện; fix `cursor='0'` — an toàn mọi entity (TEXT `'PL…'` > `'0'`, INTEGER `>0`) **[2026-09-28 · T189: đính chính tiền đề — id THẬT là TEXT, không phải INTEGER]**; (2) TAXONOMY_SUFFIX cặp self-match `'殿': ('điện','điện')` ⇒ dict==groq vẫn `TAXONOMY_VARIANT` conflict (fix `if hv_n == vern_n: continue`).
- ✅ **Tests:** `test_t170_person_classify.py` **17/17** (R2/R3/R4 + Sanskrit khớp/lệch/unmapped + TITLE + POLYPHONIC + FORMAT + NONE) · `test_t170_verify_pipeline.py` **15/15** (R6 parse 5 + R5 pragma 2 + TAXONOMY regression 2 + place cursor/G4 2 + person extras/G4 2) · `test:t170` đã nối vào `test:translation`. `test_t169_classify_diff.py` giữ 11/11.
- ✅ **Phase 5 đối chiếu enum:** `app.py` route `place-groq-review` GET filter + `_T169_DIFF_SORT` CASE giữ nguyên (place domain chỉ sinh status verified/approved_dict/conflict/api_error) — **không cần sửa**; person API/UI **defer** theo SPEC §7. `place_update.html` tabs (conflict/api_error/verified) không vỡ.
- ✅ **Phase 6 pipeline:** `npm run pipeline` PASS trừ `e2e:runtime` EPERM `.last-run.json` (pre-existing, không phải lỗi mới).
- ⚠️ Giới hạn R8 (document): `normalize_text` bỏ dấu ⇒ `hạnh`/`hành` đều `hanh` — person polyphonic cần cặp đổi phụ âm (giáng/hàng); tone-variant không phân biệt được → tự động Sanskrit/verified. Ghi chú vào `t170_classify.py` `__main__`.
- 🚧 **Còn thủ công VPS:** chạy full `python scripts/verify_dila_places_groq.py --entity person` (~1.947 batch × 25) khi có GROQ key; sau đó admin review `person_groq_audit` (UI person defer, review qua SQL/API sau nếu cần).

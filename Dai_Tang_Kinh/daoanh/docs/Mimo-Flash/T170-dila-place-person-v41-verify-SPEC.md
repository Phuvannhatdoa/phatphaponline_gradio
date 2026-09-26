---
id: T170
title: "Hardened v4.1 Verify Pipeline — Place + Person (2 side-car) — Chuẩn hóa danh xưng tu sĩ DILA"
module: Editorial / LLM Translation
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T169]
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: Đồng ý build · (1) 2 side-car · (2) task T170 · UI person defer) + Red-team amend (Admin: 1) amend T170 · 2) CJK tự seed · 3) salvage JSON yes)"
done_when: |
  Migrate 2 side-car place_groq_audit + person_groq_audit (0 ALTER bảng lớn);
  script --entity {place,person} absorb v4.1 + R1–R8 red-team (word-set polyphonic,
  nested bracket, CJK variant fold, title multi-token, busy_timeout, flat-JSON salvage,
  max_tokens partial salvage, guard spine); pytest place ≥11 + person ≥6 + ≥5 red-team
  PASS; validate-only + pilot 25/entity; npm run pipeline PASS;
  revert = git revert + migrate --revert DROP 2 bảng.
---

# T170 — Hardened Production Pipeline v4.1: Place + Person (2 Side-Car)

> **Directive gốc (2 file Admin):** (A) “Chuẩn Hóa Danh Xưng Tu Sĩ DILA Persons” · (B) “Addendum v4.1 Hardened 57k Place”.
> **Review 2026-09-25:** DB thật + T169 → **6 P0 + ~11 P1** (§2–§3).
> **Admin chốt:** **(1) 2 side-car** · **(2) Task mới T170** (T169 giữ nguyên, cross-ref) · UI person **defer** · **docs-only** lần này.
> **Red-team 2026-09-25** (Báo Cáo Phản Biện Bugs & Edge Cases) → **§3bis R1–R8 AMEND** · Admin: **amend T170** (không T171) · CJK seed **không chờ Admin** · **salvage JSON = YES** · verdict **BLOCKED until R1–R8 absorb**.

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
| P0-5 | “Nâng cấp `scripts/verify_dila_places_groq.py` v4.1” + `tests/test_dila*.py` | **0 file tồn tại** (T169 docs-only) | **Build mới** absorb body v4.1 · test tạo mới |
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

### 3.2 Person

| # | Bug | Fix |
|---|-----|-----|
| 4 | TITLE (step 4) **sau** Sanskrit (step 3): variants không chứa `'thiền sư đạt ma'` → false `needs_lexicon_review` | So variants trên **core sau `extract_person_core` strip** · **hoặc** thêm variants tôn xưng · test `道安` + suffix |
| 5 | Suffix 2-word: `len(words)>=3` **chỉ** — `"thiền sư"` (2 token) không bao giờ khớp 1-word branch | Check suffix 2-word khi **`len>=2`** · thêm test edge |
| 6 | `person_sanskrit_indicators` substring tĩnh — thiếu stem → rơi `PHONETIC_MISMATCH` mất nhãn `SANSKRIT_UNMAPPED` | Indicator = **mọi key registry** có `stem in clean_zh` + list stem mở rộng (`真諦`, `僧肇`, `道安`…) |
| 7 | `preferred_title` `'Thích' in title_groq` case-fragile · ưu groq mù | Base = **dict** · chỉ ghép prefix groq khi core equal · ghi `final_vi_source` |
| 8 | `POLYPHONIC_CHARS` place **thiếu `行`** (chỉ person có) → place 一行 lệch không dán POLYPHONIC | Đồng bộ `行` vào place dict (readings `hạnh/hành/hàng`) |

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
| 3.1 SQLite lock thiếu WAL | HIGH | `GIẢM`→MEDIUM: DB **đã `journal_mode=wal`** · thiếu `busy_timeout` (default 0) | **R5** (không set lại WAL) |
| 3.2 ID CAST collision | CRITICAL | `BẤT HỢP`→LOW: `people.id`/`places_dila.id` = **đã TEXT** | strike · vẫn giữ `str(id)` mọi tầng |
| 4.1 Qwen flat JSON `{“A001”:“vi”}` | MEDIUM | `That` — `safe_parse`→`[data]` không key `id` → reject oan | **R6** |
| 4.2 truncation `max_tokens` | HIGH | `That` — reproduce `Unterminated string` | **R7** |

### R1 — Polyphonic v3: word-set ∩ **+** `R_dict ≠ R_groq`

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

- **Không** `PRAGMA journal_mode=WAL` lại (đã `wal`) · **bật** `PRAGMA busy_timeout=10000` + `PRAGMA synchronous=NORMAL` (giữ) ở mỗi connection mở đầu script.
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

```sql
-- scripts/t170_entity_groq_audit_migrate.py --entity {place,person,all} --stats|--dry-run|--apply|--revert
-- place: PK = places_dila.id · person: PK = people.id
CREATE TABLE IF NOT EXISTS place_groq_audit  ( … cột T169 §4 … );
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
CREATE INDEX IF NOT EXISTS idx_pga_review ON place_groq_audit(needs_review, review_status);
CREATE INDEX IF NOT EXISTS idx_pga_diff   ON place_groq_audit(diff_type);
CREATE INDEX IF NOT EXISTS idx_gpa_review ON person_groq_audit(needs_review, review_status);
CREATE INDEX IF NOT EXISTS idx_gpa_diff   ON person_groq_audit(diff_type);
```

- Backup `data/backups/lineage_t170_<ts>.db` trước `--apply` (sqlite backup API, Zero-RAM).
- `--revert`: DROP 2 bảng + index IF EXISTS · **không** chạm bảng lớn.

---

## 5. SCRIPT — `scripts/verify_dila_places_groq.py` (build mới)

Absorb toàn bộ body v4.1 directive + T169 §5:

| Item | Chi tiết |
|------|----------|
| Config | `--entity {place,person}` · `DB_PATH=data/lineage.db` · `resolve_groq_key()` · model default `qwen/qwen3.8-27b` · `--validate-only` · `--pilot N` · **`busy_timeout=10000`** (R5 · không set lại WAL) |
| `EntityConfig` | person: table spine **`people`**, `PERSON_POLYPHONIC_CHARS` + `PERSON_SANSKRIT_REGISTRY` + prompt person (directive §2–§3) · place: `places_dila` + `POLYPHONIC_CHARS` (+`行`) + `SANSKRIT_REGISTRY` + prompt place · **config cứng** — cấm đoán cột (R3-guard) |
| Preprocess | `clean_dila_name` + **bracket stack** (R2) + **`fold_cjk`** (R3, seed 峯/羣/祕/惠) trước registry/compare |
| Polyphonic | **R1:** word-set ∩ **+** `R_d ≠ R_g` |
| Title | **R4:** loop strip prefix/suffix multi-token · core ≥1 token |
| Scope SELECT | **place:** `places_dila d JOIN places_pending p ON p.id=d.id` → dict `p.name_vi` · **person:** `people` → dict `name_vi` · filter side-car chưa `verified/conflict/approved_dict` · `id NOT NULL` |
| `ensure_schema` | Idempotent trên **side-car** (PRAGMA) · **guard:** abort nếu spine table không tồn tại (chống P0-2/4 tái diễn) |
| Batch | 25 · sleep 2 · reject batch (invalid/unexpected/dup) · COALESCE · stale reset · remainder flush · `str(id)` mọi tầng |
| Groq parse | flat dict → items (R6) · `max_tokens` explicit + **truncation salvage partial** (R7, Admin YES) · `salvage_used` log |
| Key/model | env→`data/llm_config.json.groq_key` · `response_format` fail → retry **không** response_format + fence-strip |
| Observability | schema log batch 0 · token/request + **window 60s** vs 6.000 TPM · log `batch_id` mỗi batch · `fold_unmapped` warning |
| Ghi | UPSERT side-car **không** UPDATE spine · resume skip done · `--force` redo |

**Log:** stdout UTF-8 + session file khi chạy VPS (`docs/sessions/<date>_t170-run.md`).

---

## 6. TESTS

| File | Ngưỡng |
|------|--------|
| `tests/test_dila_verifier_v3.py` | **≥11** theo directive (idempotent · remainder · missing→api_error · batch reject · invalid item · COALESCE preserve · stale reset · Sanskrit strict 2-bên · partial substring UNMAPPED · taxonomy core · clean_dila_name · safe_title) — **import side-car + table name thật** |
| `tests/test_dila_person_verifier.py` | **≥6** theo directive (行 polyphonic · Sanskrit canonical · hallucination · title core · clean person metadata) + **+3 P1:** TITLE×polyphonic (`一行` + tôn xưng) · suffix 2-word edge · indicator động (`真諦` UNMAPPED) + **R4** multi-token (`Tam Tạng Pháp Sư Huyền Trang`) |
| `tests/test_t170_redteam.py` (R1–R7) | **≥5:** R1 `Đại Nam`≠POLYPHONIC + cùng-reading≠conflict · R2 `開元路((黃龍府))` nest · R3 `峯頂寺`≡`峰頂寺` · R6 flat JSON salvage · R7 truncation partial 22/25 |
| Fixture khóa | Place: 降魔窟=POLYPHONIC · 白馬寺=TAXONOMY · 少林寺=NONE · 那爛陀寺+Thiếu Lâm=UNCONFIRMED · Person: 一行 Nhất Hạnh/Hành · 道安±Thích · 菩提達磨 Bồ Đề Đạt Ma |

---

## 7. API/UI (theo T169 §6–§7 · place trước · person defer)

- Place: `GET/PUT /daoanh/api/admin/place-groq-review` + `admin/place_update.html` 2 cột (SPEC T169).
- Person: **defer** — API pattern y hệt `person-groq-review` · UI `person_update.html` **phase cuối** (đã chốt Admin).

---

## 8. ACCEPTANCE (gate production)

```text
① pytest tests/test_dila_verifier_v3.py tests/test_dila_person_verifier.py tests/test_t170_redteam.py -v → 100% PASS
   (red-team ≥5 case R1–R7 — exit BLOCKED, xem §3bis)
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
| 1 | Migrate 2 side-car `--stats/--dry-run/--apply/--revert` + backup |
| 2 | `EntityConfig` + classify fix (P1 §3) + **R1–R7** (§3bis) + **tests đỏ→xanh** (≥11+≥6+≥5 red-team) |
| 3 | Script `--entity place` + smoke validate + pilot 25 |
| 4 | Script `--entity person` + smoke validate + pilot 25 |
| 5 | API/place UI (T169 §6–§7) · **person UI defer** |
| 6 | `npm run pipeline` · session run-log · ROLLBACK hash-fill |

**Commit code (toplevel):** `feat: T170 entity verify pipeline v4.1 (2 side-car) + tests + docs`  
**Revert:** `git revert --no-edit <sha>` + `python scripts/t170_entity_groq_audit_migrate.py --revert --entity all`

---

## 10. Quan hệ

- **depends_on: T169** — UI/API place dùng SPEC T169 §6–§7 · T169 chưa build → T170 P1–P4 **không block** T169.
- T169 tasktodo: thêm chú “v4.1 absorb → T170” (**không sửa SPEC T169**).
- T165/T168: không đụng.

## 11. Files

| Loại | Path |
|------|------|
| Mới | `scripts/verify_dila_places_groq.py` · `scripts/t170_entity_groq_audit_migrate.py` · `tests/test_dila_verifier_v3.py` · `tests/test_dila_person_verifier.py` · SPEC này · session |
| Sửa (phase 5) | `app.py` (+2 route) · `admin/place_update.html` |
| Không đụng | `people`/`places_dila`/`places_pending` schema · T165 code |

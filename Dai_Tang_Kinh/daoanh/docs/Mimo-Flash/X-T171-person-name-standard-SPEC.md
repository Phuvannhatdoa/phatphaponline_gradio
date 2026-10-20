---
id: T171
title: "Chuẩn Hóa Tên Nhân Vật DILA — Standard Name Layer trên name_vi_map (SSOT)"
module: Editorial / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T166, T170]
created: 2026-09-25
updated: 2026-09-28
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: (1) Phương án A · (2) SSOT = name_vi_map · (3) tạo task T171)"
amended_by: "T188 (2026-09-28 — Admin: 'Đồng ý build, hãy lưu logs, gitcommit… Gọi pipip khi done'): 4 P0 + P1/P2 logic fixes" + "T190 (2026-09-28 — docs-only: bịt 2 lỗ hổng logic verified-final NULL + stats phủ 6.905 person không row map)"
done_when: |
  name_vi_map + person_name_alias additive (backup, idempotent, --revert; revert export alias JSON);
  index 48.673 hiển thị name_vi_standard khi reviewed/verified, còn lại legacy + badge §5.2/§5.3
  + filter name_status; search Han/API/standard/alias (kể cả không dấu qua normalized_ascii);
  CSV +8 cột / JSON names{} compat; person.html khối Tên và định danh + edit validate;
  2 endpoint dual-write mirror people.name_vi (KHÔNG overwrite name_vi_final đã duyệt);
  fixture A000006/A000007/A000008 PASS; 0 mất legacy; COMPLETION_REPORT; npm run pipeline PASS.
---

# T171 — Chuẩn Hóa Tên Nhân Vật DILA (SPEC)

> **[2026-09-28 · T188] AMEND — Sửa logic đối chiếu SPEC ↔ codebase/DB (docs-only, 0 code/0 DB):**
> Review của Admin phát hiện **4 mâu thuẫn P0 + 6 P1 + 5 P2** (chủ yếu do addendum §14 chồng lên §3–§5
> mà không cập nhật body) → đã sửa tại chỗ. Tóm tắt: **P0-1** §5 LEFT JOIN `name_vi_map` mâu thuẫn
> §14.3 (51 dup `dila_id`) → subquery dedupe + `COUNT(DISTINCT p.id)` · **P0-2** §3.2 `uq_pna` xung đột
> §14.1 → `uq_pna_norm(person_id, normalized_value)` + `uq_pna_display` · **P0-3** enum `name_role` §3.2
> thiếu role §14.2 (`primary_han_name/han_viet_reading/legacy_name_unverified/common_name`) → hợp nhất ·
> **P0-4** display precedence §5/§7.2 "standard luôn strong" vs §14.5 "legacy mặc định" → chốt công thức
> chung §5.2: standard strong **chỉ khi** `reviewed/verified` · **P1**: bỏ rule 4 dead (⊂6.2) · đánh lại
> 6.1–6.6 init / 6.7 write-validate / 6.8 guard · rule monogram 6.6 (bảng `hanviet_fallback` có thật) ·
> §6 conditional không overwrite `name_vi_final` đã duyệt · inline §5.2/§5.5 (directive gốc không có file) ·
> line refs thật (search 8201 · namevi_map_update 13926/sync 13974 · name_vi 18308/sync 18326 ·
> glossary 17213 · stats 8329) · soft-dep T172 · **P2**: cột `normalized_ascii` · revert export alias JSON ·
> rule 5 nguồn `birth_year/death_year` (`people`/`name_vi_map`) · seed `is_display_name` · stats vào
> acceptance. Chi tiết: `tasks/T188-t171-spec-logic-fixes.md`.

> **[2026-09-28 · T190] AMEND — Bịt 2 lỗ hổng logic còn lại sau T188 (docs-only, 0 code/0 DB; Admin: "Đồng ý build… lưu logs, gitcommit, update .md, revert tiện lợi, Gọi pipip khi done"):**
> **(1)** §5.2/§6/rule 6.7 — `verified` mà `name_vi_final` NULL: strong sẽ render rỗng + mirror `people.name_vi := NULL` **xóa luôn display** (DB thật: chỉ **5.205/46.711** row có `name_vi_final`) → thêm điều kiện **`name_vi_final IS NOT NULL`** khi strong/mirror + validate `status=verified ⇒ final non-null` (400, mở rộng 6.7).
> **(2)** §5 filter/`by_name_status` không phủ **6.905 person (14%)** không row `name_vi_map` (status NULL) → dùng `COALESCE(NULLIF(m.standard_status,''),'auto')` ở filter `name_status` + stats, tổng 4 key = 48.673; acceptance ⑩/⑬ cập nhật.
> Chi tiết: `tasks/T190-t171-build-docs-correction.md`. DB verify: 46.711/48.673 · dup 51 · final non-null 5.205 · không-row-map 6.905.

> **Directive gốc:** “DEBUG / FEATURE TASK — Chuẩn hóa tên nhân vật DILA” (index 48.673 · `dila_person_index.html`).
> **Review 2026-09-25:** repo + DB thật → **4 P0 + 5 P1/P2** (§2).
> **Admin chốt:** **(1) Phương án A** · **(2) SSOT = `name_vi_map`** · **(3) Task mới T171** · file này gộp vai trò `IMPLEMENTATION_PLAN.md` (convention `docs/Mimo-Flash/`).

---

## 0. Quyết định Admin (locked)

| # | Quyết định |
|---|------------|
| 1 | **Phương án A:** mở rộng **`name_vi_map`** (46.711 row, đã có `name_vi_auto`/`name_vi_final`/`approved_by`) làm SSOT standard — **không** dựng `person_names` đầy đủ · **không** thêm 7 cột vào `people`. |
| 2 | SSOT tên chuẩn = `name_vi_map.name_vi_final` + 4 cột additive mới · alias = bảng mới thin `person_name_alias`. |
| 3 | `people.name_vi` = **legacy/display cache** — không ghi đè hàng loạt · dual-write 2 endpoint Admin sau migration. |
| 4 | T170 Groq person: chỉ set cờ `needs_review`, **không** ghi thẳng `name_vi_standard`. |

---

## 1. OUT OF SCOPE (§13 directive)

- Không LLM tự “tên chuẩn” 48.673 · không scrape · không gọi API Hán Nôm hàng loạt.
- Không xóa/clear legacy `name_vi` · không `verified` khi chưa `standard_source`.
- Không đụng tiểu sử Hán/Việt · không refactor lớn ngoài file liệt kê §13.

---

## 2. Review directive → sửa trước code (9 điểm)

| # | Mức | Directive | Verify thật (2026-09-25) | Sửa |
|---|-----|-----------|--------------------------|-----|
| 1 | **P0** | ID `A0004…A0027` | `people.id` = **7 ký tự** `A000004` · 5 ID mẫu **0 row** | Fixture/API đổi `A000006/A000007/A000008` (test §8) · `A000004/A000027` **chỉ re-verify Phase 1** trên UI, không cần fixture |
| 2 | **P0** | A0004=“Thì Xưng” · A0008=“Đại Huệ Thiền Sư” · A0027=“Tiếu Am Liễu Ngộ” | DB: `Cương Lương Gia Xá` · **`Nhất Hàng`** · **`Liễu Ngộ`** · khớp directive chỉ A000006 (chuỗi gộp) + A000007 (`Nhất Như`) | **Re-verify 5 vd trên UI live trước Phase 2** — nếu lệch, trace nguồn render (join/cache) trước migration |
| 3 | **P0** | Rule “API >80 ký tự” | `len(name_vi)>80` = **0 row** · chuỗi gộp ≈ **76 chars** → rule chết | Ngưỡng: `len≥55` **∨** `len>3×len(name_zh)` **∨** rule lặp cụm/title-stack (A000006 rơi đây) |
| 4 | **P1** | Thêm 7 cột + `person_names` mới | Trùng `name_vi_map`+`person_name_correction`+`person_display_names`+`vn_person_authority`+`_glossary_resolver` (6 nguồn) | **A:** 4 cột trên `name_vi_map` + alias thin · resolver **P0** |
| 5 | **P1** | Giữ `people.name_vi` bất biến | **2 endpoint đang ghi `people.name_vi`:** `POST /daoanh/api/admin/person/<id>/name_vi` (app.py:18308, sync :18326) · `admin_namevi_map_update` (app.py:13926, sync :13974) | Dual-write: chuẩn (SSOT) + mirror `people.name_vi` (compat client cũ) · **KHÔNG overwrite `name_vi_final` đã duyệt** (§6 conditional) |
| 6 | **P1** | Filter “Tên chuẩn” mới | Trạng thái dịch = **compute client** (`bio_vi/draft_status`) — không stored | Param API **mới** `name_status` — không đụng `status=translated\|draft\|none` |
| 7 | **P2** | Rule 1 “API trống” | `name_vi` trống = **0/48.673** | Giữ guard 6.1 · ca thật = không tương ứng Hán → flag monogram **rule 6.6** (bảng `hanviet_fallback` + `custom_hanviet_override` có thật — **không AI**) · rule không-Latin: **1.555** row → `NOT GLOB '*[A-Za-z]*'` (6.5) |
| 8 | **P2** | `standard_status` init `auto` HOẶC `needs_review` | Mơ hồ | **Deterministic:** trúng rule **6.1–6.6** (cờ init) → `needs_review` · ngược lại → `auto` · **6.7** = write-validate (`verified` **bắt buộc** `standard_source` non-null — cột mới NULL khi init nên 6.7 không thể fire lúc backfill) · **6.8** = upsert guard (output `auto`, không tính vào “trúng → needs_review”) |
| 9 | **P2** | `IMPLEMENTATION_PLAN.md` riêng · fixture TEST ONLY | Convention repo 2026-09-25: SPEC ở `docs/Mimo-Flash/` | File này gộp plan · fixture `TEST ONLY` chỉ trong `tests/fixtures/` **+ `--env test`**, không migrate prod |

---

## 3. Schema — Phương án A (additive, idempotent)

### 3.1 `name_vi_map` (+4 cột)

```sql
-- scripts/t171_name_standard_migrate.py --stats|--dry-run|--apply|--revert
-- backup: data/backups/lineage_t171_<ts>.db (sqlite backup API)
ALTER TABLE name_vi_map ADD COLUMN han_name_normalized TEXT;
ALTER TABLE name_vi_map ADD COLUMN standard_status TEXT;   -- auto|needs_review|reviewed|verified
ALTER TABLE name_vi_map ADD COLUMN standard_source TEXT;
ALTER TABLE name_vi_map ADD COLUMN standard_note TEXT;
CREATE INDEX IF NOT EXISTS idx_nvm_std ON name_vi_map(standard_status);
-- idempotent: PRAGMA table_info trước khi ADD · chạy lại không duplicate
-- backfill: standard_status = CASE WHEN <rule 6.1–6.6> THEN 'needs_review' ELSE 'auto' END
--           (KHÔNG tự điền name_vi_final mới · name_vi_final đã có = chuẩn cũ đã duyệt)
```

### 3.2 `person_name_alias` (bảng mới thin — thay `person_names` đầy đủ)

```sql
CREATE TABLE IF NOT EXISTS person_name_alias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  person_id TEXT NOT NULL,          -- people.id (A000001…)
  script TEXT NOT NULL,             -- han|vietnamese|pinyin|sanskrit|japanese|other
  name_value TEXT NOT NULL,         -- giữ nguyên dấu/ký tự gốc
  normalized_value TEXT,            -- UNIQUE key: NFC + lower + bỏ khoảng trắng thừa (CÓ dấu — §14.1)
  normalized_ascii TEXT,            -- [T188 P2] search không dấu: lower + strip dấu Latin (repo convention remove_diacritics)
  name_role TEXT NOT NULL,          -- [T188 P0-3 hợp nhất §3.2+§14.2] primary_han_name|han_viet_reading|legacy_name_unverified|common_name|primary|common|alias|dharma_name|dharma_title|courtesy_name|art_name|posthumous_name|title|transliteration
  is_display_name INTEGER DEFAULT 0,
  source_citation TEXT,
  confidence TEXT DEFAULT 'auto',   -- auto|needs_review|reviewed|verified
  source_type TEXT,                 -- [§14.1] DILA|characterwise_mapping|legacy_api|scholarly_source|editorial
  is_searchable INTEGER DEFAULT 1,  -- [§14.1] legacy searchable cả verified/unverified
  note TEXT,
  created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pna_person ON person_name_alias(person_id);
-- [T188 P0-2] THAY uq_pna (person_id, name_value, name_role) — xung đột §14.1:
CREATE UNIQUE INDEX IF NOT EXISTS uq_pna_norm ON person_name_alias(person_id, normalized_value);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pna_display ON person_name_alias(person_id)
  WHERE is_display_name = 1;        -- tối đa 1 display name/person (§14.1 partial)
-- normalized_ascii KHÔNG unique (chỉ dùng LIKE search không dấu) — total 4 index khi revert (§3.3)
```

### 3.3 Mapping trường directive → SSOT

| Directive | T171 |
|-----------|------|
| `han_name_raw` | `people.name_zh` (không copy) |
| `han_name_normalized` | `name_vi_map.han_name_normalized` (NFKC + **`fold_cjk` seed 峯/羣/祕/惠** — dùng chung T170 R3) |
| `han_viet_api` | `people.name_vi` (display) **+** `name_vi_map.name_vi` (bản ghi map) |
| `name_vi_standard` | **`name_vi_map.name_vi_final`** |
| `name_standard_status/source/note` | 3 cột additive §3.1 |
| `person_names.*` | `person_name_alias` §3.2 |

**Revert:** [T188 P2] **export `person_name_alias` ra `data/backups/t171_alias_<ts>.json` TRƯỚC khi drop** (bảo toàn dữ liệu biên tập admin) → drop 4 index (`idx_nvm_std`, `idx_pna_person`, `uq_pna_norm`, `uq_pna_display`) + `DROP person_name_alias` · SQLite `ALTER DROP COLUMN` ≥3.35 — nếu engine cũ: để cột NULL + ghi changelog (cột rỗng vô hại).

---

## 4. Flag rules 6.1–6.8 (chỉ cờ, không sửa tên)

> **[T188 P1]** Đánh số lại thống nhất 6.1–6.8 (trước: bảng 1–8, title "6.1–6.8", §3.1 "6.x" — 3 kiểu
> song song). **Bỏ rule cũ #4** (`len(name_zh)≤3 ∧ len(name_vi)≥25`) — chứng minh dead: rule 4 true ⇒
> `3×len(name_zh) ≤ 9 < 25 ≤ len(name_vi)` ⇒ luôn thỏa vế `len(name_vi) > 3×len(name_zh)` của rule 6.2
> ⇒ rule 4 ⊂ 6.2 100% (kể cả `name_zh` rỗng: `3×0=0`, mọi `name_vi≥25` đều fire 6.2; `name_zh` NULL:
> cả 2 đều NULL-không-fire → rule 4 không cứu được case NULL). Rule cũ #1 ⊂ 6.5 nhưng giữ tường minh.

| # | Rule (đã sửa ngưỡng §2) | → status |
|---|--------------------------|----------|
| 6.1 | `han_viet_api` trống ∧ `name_zh` có (guard — 0/48.673 row hiện tại; ⊂6.5 nhưng giữ tường minh) | needs_review |
| 6.2 | `len(name_vi) ≥ 55` ∨ `len(name_vi) > 3 × len(name_zh)` (rule lặp cụm/stack ở 6.3) | needs_review |
| 6.3 | Lặp cụm ≥2 lần (token 2+ syllable) hoặc title-stack ≥2 title (`quốc sư`,`thiền sư`,`cư sĩ`,`hòa thượng`,`tăng thống`,`túc`…) | needs_review |
| 6.4 | `death_year < birth_year` ∨ tuổi ngoài [5;130] (khi 2 năm có số — nguồn: `COALESCE(m.birth_year, p.birth_year)` / `COALESCE(m.death_year, p.death_year)`; **cả 2 bảng `name_vi_map` + `people` đều có 2 cột này** — verify T188 Phase 0) | needs_review |
| 6.5 | `name_vi` không GLOB `*[A-Za-z]*` (1.555 row) ∨ `name_zh` có U+FFFD/ ký tự hiếm ngoài CJK phổ | needs_review |
| 6.6 | **Monogram [T188 — thay lời hứa §2 #7]:** không syllable nào của `name_vi` khớp Hán-Việt của `name_zh` — map char qua `hanviet_fallback` + `custom_hanviet_override` (bảng có thật, verify T188 Phase 0) · **skip (không flag)** khi map được <50% ký tự `name_zh` · không AI, không API | needs_review |
| 6.7 | **Write-validate (KHÔNG dùng khi init):** `standard_status='verified'` ∧ (`standard_source` IS NULL/empty **hoặc `name_vi_final` IS NULL/empty [T190]**) → chặn ghi (400) + downgrade `needs_review` — cột mới thêm toàn NULL khi backfill nên 6.7 không thể fire lúc init · **mở rộng [T190]:** DB hiện chỉ 5.205/46.711 row có final → `verified`+final NULL = dữ liệu hỏng (5.2 sẽ render rỗng, §6 mirror xóa display) | (write-time) |
| 6.8 | **Guard (không tính cờ):** khớp `name_vi_map` cho `dila_id` thiếu row → upsert row `auto` | auto |

**Init:** trúng ≥1 trong **6.1–6.6** → `needs_review` · ngược lại → `auto`.
6.7 = write-validate only · 6.8 = upsert guard (output `auto`, **không** rơi vào câu “trúng → needs_review”).

---

## 5. Read path (index + search + export)

**File:** `app.py` `api_dila_persons_search` (route **:8201** / def **:8202** — [T188] ref cũ ~7996 đã drift) · `admin/dila_person_index.html`.

| Item | Chi tiết |
|------|----------|
| SELECT | **[T188 P0-1]** KHÔNG `LEFT JOIN name_vi_map` blind (§14.3: 51 `dila_id` dup → fan-out sai phân trang/CSV). Dùng subquery dedupe **deterministic 1 row/`dila_id`**: `LEFT JOIN (SELECT dila_id, name_vi_final, standard_status, standard_source, standard_note FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY dila_id ORDER BY CASE standard_status WHEN 'verified' THEN 0 WHEN 'reviewed' THEN 1 ELSE 2 END, COALESCE(approved_at,'') DESC, rowid DESC) rn FROM name_vi_map WHERE dila_id IS NOT NULL) WHERE rn=1) m ON m.dila_id=p.id` · engine <3.25 (không window): thay bằng `GROUP BY dila_id` + aggregate giá trị row `approved_at` mới nhất · trả thêm `vi_standard, standard_status, standard_source, standard_note, han_viet_api(=p.name_vi)` · **giữ nguyên** `name_zh, name_vi, …` field cũ (compat) · alias qua `EXISTS` (không join ⇒ không fan-out) · **pagination COUNT = `COUNT(DISTINCT p.id)`** |
| Display | **[T188 P0-4]** Logic **§5.2** (inline dưới đây — directive gốc không có file trong repo): strong = standard **CHỈ KHI** `standard_status ∈ {reviewed, verified}` · còn lại strong = legacy · small = meta status · `API: {old}` khi khác |
| Filter | Param **mới** `name_status=auto\|needs_review\|reviewed\|verified` · KHÔNG đổi `status` dịch · **[T190]** filter + stats dùng `COALESCE(NULLIF(m.standard_status,''),'auto')` — **6.905 person (14%)** không row `name_vi_map` (status NULL) tự rơi hạng `auto`, không upsert hàng loạt (Giữ §6.8 guard như cũ) |
| Search | `q` mở rộng: `p.id ∨ name_zh ∨ name_vi ∨ m.name_vi_final ∨ a.name_value ∨ a.normalized_ascii` (alias qua `EXISTS (… a.is_searchable=1 AND (a.normalized_value LIKE ? OR a.normalized_ascii LIKE ?))` — [T188 P2] `normalized_ascii` cho query không dấu, Python normalize `q` cả 2 biến thể · nếu chậm: FTS5 `person_name_fts` pattern `ensure_places_pending_fts` app.py:336) |
| Sort | Giữ `sort_status` dịch · thêm sort `name_status` optional |
| CSV | +8 cột **cuối**: `dila_id, han_name_raw, han_name_normalized, han_viet_api, name_vi_standard, name_standard_status, name_standard_source, aliases` · cột cũ giữ thứ tự |
| JSON | Object `names{han_raw,han_normalized,han_viet_api,vi_standard,status,source}` + `aliases[]` · field cũ không đổi |

### 5.2 Logic render (inline — [T188] hấp thụ từ directive gốc, file không tồn tại trong repo)

```text
name-main (strong):   ← [T190] mở rộng điều kiện final non-null
  standard_status ∈ {reviewed, verified} ∧ m.name_vi_final IS NOT NULL
                                                     → m.name_vi_final
  ngược lại (auto/needs_review/NULL, hoặc verified–final NULL)  → p.name_vi  ← LEGACY mặc định (§14.5)
  khi verified nhưng final NULL: em meta thêm "⚠ standard thiếu final — báo admin" (dữ liệu hỏng, 6.7 chặn ghi mới)
name-meta (small, dòng phụ):
  khi standard khác legacy:               → "API: {p.name_vi}"
  badge 4 mức: ⚙ Auto · ⏳ Cần duyệt · ✎ Đã biên tập · ✓ Đã kiểm chứng
  meta format: "{badge} · {source}" (source khi có)
CSS: person-name strong{display:block} · .name-meta{font-size:11px;opacity:.75} · line-clamp:2 cho name ≥55 chars · tooltip xem full
```

### 5.3 Badge mapping (giữ nguyên directive)

| standard_status | Badge | Màu (§7.1) |
|---|---|---|
| `auto` | ⚙ Auto | slate |
| `needs_review` | ⏳ Cần duyệt | amber |
| `reviewed` | ✎ Đã biên tập | cyan |
| `verified` | ✓ Đã kiểm chứng | green |

### 5.5 CSS (inline — [T188] hấp thụ từ directive gốc)

```css
.person-name strong{display:block;overflow:hidden;text-overflow:ellipsis}
.person-name .name-meta{font-size:11px;opacity:.75;display:block}
.person-name.line-clamp2 strong{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.badge-auto{background:#334155;color:#cbd5e1} .badge-needs_review{background:#78350f;color:#fbbf24}
.badge-reviewed{background:#164e63;color:#67e8f9} .badge-verified{background:#14532d;color:#86efac}
```

---

## 6. Write path (admin edit + dual-write)

| Endpoint | Sửa |
|----------|-----|
| `POST /daoanh/api/admin/person/<id>/name_standard` **(mới)** | Validate: `status=verified` ⇒ `source` non-null (**rule 6.7**) **và [T190] `name_vi_final` non-null (400)** · upsert `name_vi_map` (dila_id=id): `name_vi_final`, `standard_status/source/note`, `approved_by='admin'`, `approved_at` · **mirror [T190]** `people.name_vi := name_vi_final` (**CHỈ KHI** final non-null — tránh xóa display) |
| `POST …/person/<id>/name_vi` (app.py:**18308**, sync **:18326**) **giữ** | [T188 P1 **conditional**] ghi `people.name_vi` (legacy, luôn) **+** mirror alias `legacy_name_unverified`/`legacy_api` (§14.4) · upsert `name_vi_map.name_vi_final` **CHỈ KHI trống hoặc trùng giá trị**; nếu đã có **và khác** → **KHÔNG overwrite** chuẩn đã duyệt — chỉ ghi alias + `standard_note='legacy edit ≠ standard (giữ standard)'` · không tự set `reviewed` (sửa legacy ≠ duyệt standard) |
| `admin_namevi_map_update` (app.py:**13926**, sync **:13974**) **giữ** | Endpoint **curated** (ghi `name_vi_final` + `approved_by='admin'` có chủ đích — overwrite tại đây là intended) ✓ — bổ set `standard_status` nếu client gửi (không gửi → giữ nguyên, không hạ reviewed/verified) + mirror alias (§14.4) |
| Alias | `POST …/person/<id>/names/alias` + `DELETE` — validate `name_role` = enum hợp nhất §3.2 (**P0-3**) · compute `normalized_value` (NFC+lower+space) + `normalized_ascii` (strip dấu) · `INSERT` upsert theo `uq_pna_norm` |
| Resolver | `_glossary_resolver` (app.py:**17213**): **chèn P0** = `name_vi_map.name_vi_final` khi `standard_status IN ('reviewed','verified')` — trên P1 glossary |
| T170 | Groq person output → chỉ UPDATE `standard_status='needs_review'` (+note groq), **không** set `name_vi_final` |

---

## 7. UI

### 7.1 `admin/dila_person_index.html`

- Đổi label cột → **“Tên Việt chuẩn”** · render theo **§5.2 (đã inline — [T188])** · CSS **§5.5 (đã inline)** (`person-name strong{display:block}`, `.name-meta`, 4 badge màu) · `line-clamp:2` cho API dài · tooltip/full xem detail.
- Filter **“Tên chuẩn”** 5 mức (Tất cả/Auto/Cần duyệt/Đã biên tập/Đã kiểm chứng) — control mới, không đụng 2 filter dịch/tông/triệu · badge count từ `stats` API mới `by_name_status`.
- Giữ: phân trang 50 · lọc sect/dynasty/status dịch · link `person.html?id` · export.

### 7.2 `admin/person.html`

- Khối **“Tên và định danh”**: Tên Hán · Tên chuẩn · Trạng thái (badge) · Nguồn · **Dữ liệu API gốc** · Tên khác (alias list) · Ghi chú biên tập.
- Chưa chuẩn: banner “Chưa chuẩn hóa — dữ liệu dưới đây do API/pipeline tự động cung cấp.”
- Form edit: `name_vi_standard`/`status`/`source`/`note` + add/remove alias · validate client+server (6.7) · không sửa `bio*` · header (661) ưu tiên **`vi_standard` CHỈ KHI `standard_status ∈ {reviewed, verified}`** → fallback `name_vi` [T188 P0-4 — khớp §5.2].

---

## 8. Tests & fixtures

**File:** `tests/test_t171_name_standard.py`.

| Case | Kỳ vọng |
|------|---------|
| A000006 一山国師 + chuỗi gộp | `needs_review` · **không** tạo `name_vi_final` mới · rule 6.2/6.3 (≥55 ∨ lặp) |
| A000007 一如 + Nhất Như | hiển thị `Nhất Như` · `auto` **hoặc** `needs_review` theo rule · **cấm** `verified` |
| A000008 一行 + (DB=`Nhất Hàng`) | `needs_review` · **không** tự đặt `Nhất Hành` nếu chưa có record biên tập/source |
| Fixture verified (file `tests/fixtures/t171_a000008_verified.json`, **TEST ONLY**) | index: main=`Nhất Hành`, meta=`API: … · ✓ Đã kiểm chứng` |
| Rule 6.2 ngưỡng [T188 sửa câu mơ hồ "80+"] | unit: chuỗi **76 chars fire** (≥55) · **56–80 chars fire rule mới, KHÔNG fire rule cũ `>80`** · 81+ fire cả hai · <55 không fire (với `name_zh` ngắn, vẫn fire vế `>3×`) |
| Display precedence [T188 P0-4] | row `auto` + `name_vi_final` khác legacy → strong = **legacy**, meta có `Tên chuẩn (chưa duyệt)` · row `verified` → strong = standard |
| Rule 6.6 monogram [T188] | name_vi không share syllable Hán-Việt nào với name_zh (map ≥50%) → `needs_review` · map <50% → skip |
| Dual-write | edit standard → `name_vi_map` + `people.name_vi` cùng giá trị · legacy không mất · [T188] sửa legacy ≠ chuẩn → `name_vi_final` **giữ nguyên** |
| Migration idempotent | `--apply` ×2 không lỗi · `--revert` export alias JSON + sạch alias + status về pre |

**Không** đưa fixture TEST ONLY vào DB prod (chạy `--env test` / SQLite `:memory:`).

---

## 9. Acceptance (gộp §11 directive + Protocol)

```text
① pytest tests/test_t171_name_standard.py -v → 100% PASS (A000006/7/8)
② 0 row mất name_vi cũ (COUNT + checksum trước/sau migration)
③ Index: standard strong **CHỈ khi reviewed/verified** · auto/needs_review → strong = legacy [T188 P0-4] ·
   chưa duyệt KHÔNG hiện “Đã kiểm chứng” · filter 5 mức · 1 hàng/record không fan-out (51 dup) [P0-1]
④ Search theo Han/API/standard/alias **+ không dấu (normalized_ascii)** [T188] · pagination+sect+dynasty+
   status dịch không vỡ · COUNT DISTINCT đúng
⑤ CSV +8 cột cuối · JSON names{} · client cũ đọc field cũ OK
⑥ person.html xem+edit đủ · verified thiếu source = 400 (6.7) · verified thiếu final = 400 [T190]
⑦ Browser QA: open index + A000006/A000007/A000008 + CSV/JSON download
⑧ npm run pipeline PASS
⑨ COMPLETION_REPORT.md: file đổi · migration chạy · test · số needs_review · rủi ro
⑩ Stats API `by_name_status` trả đủ 4 key khớp filter name_status [T188] · phủ 100% person qua COALESCE→auto [T190]
```

---

## 10. Phases

| Phase | Việc |
|-------|------|
| 1 | **Re-verify 5 vd directive trên UI live** (P0 #2) + chốt nguồn render |
| 2 | Migration script + backup + test idempotent/revert + fixture |
| 3 | Backend: SELECT/`name_status`/search/export + endpoint write + dual-write + resolver P0 |
| 4 | UI index (label/display/filter/CSS) |
| 5 | UI person.html “Tên và định danh” + edit |
| 6 | Export CSV/JSON + stats by_name_status |
| 7 | pytest + browser QA A000006/7/8 + `npm run pipeline` |
| 8 | `COMPLETION_REPORT.md` + session run-log + ROLLBACK hash-fill |

**Commit code:** `feat: T171 person name standard layer (name_vi_map A) + tests + docs`

---

## 11. Revert

```bash
git revert --no-edit <sha_T171_docs>          # docs
# Code:
python scripts/t171_name_standard_migrate.py --revert   # [T188] tự export person_name_alias → data/backups/t171_alias_<ts>.json TRƯỚC khi DROP
                                                        #         + DROP alias + 4 index (idx_nvm_std/idx_pna_person/uq_pna_norm/uq_pna_display)
                                                        #         + 4 cột: NULL-out nếu engine <3.35
git revert --no-edit <sha_feat_T171>
# Restore DB nếu cần: data/backups/lineage_t171_*.db
```

---

## 12. Quan hệ

- **depends_on: T166** (canonical identity — không thêm nguồn tên thứ 6 ngoài SSOT) · **T170** (Groq → chỉ cờ needs_review · `fold_cjk` dùng chung).
- **soft-dep T172** [T188]: seed alias `Nhất Hành` (`characterwise_mapping`) lấy từ charwise mapping T172 — nếu T172 chưa chạy thì test §14.6 #2 skip case `Nhất Hành` (không fail) · test `一行`/legacy independent.
- T165/T168: không đụng.
- Session: `docs/sessions/2026-09-25_t171-person-name-standard-plan.md` · amend: `docs/sessions/2026-09-28_t188-t171-spec-logic-fixes.md`.

## 13. Files (dự kiến — code phase)

| Loại | Path |
|------|------|
| Sửa | `app.py` (`api_dila_persons_search` **8201** · `POST admin/person/<id>/name_vi` **18308** · `namevi_map_update` **13926** · `_glossary_resolver` **17213** · stats **8329** — [T188] ref cũ ~7996/17505/13112/16518/~8104 đã drift) · `admin/dila_person_index.html` · `admin/person.html` |
| Mới | `scripts/t171_name_standard_migrate.py` · `tests/test_t171_name_standard.py` · `tests/fixtures/t171_a000008_verified.json` · endpoint write/alias (app.py) · `COMPLETION_REPORT.md` |
| Không đụng | `people.name_zh/bio*` · bio translation · T165 code tre |

## 14. ABSORB — Addendum "Gộp nhiều tên về một nhân vật" (2026-09-25)

> Directive addendum: một person = một `person_id` + một tiểu sử; mọi tên (Hán, charwise, phổ biến, pháp húy/hiệu, tôn xưng, legacy, romanization, alias) là name record của CÙNG một profile. **TUYỆT ĐỐI không tạo person record mới vì tên khác; không xóa legacy vì lệch số Hán tự.** Chốt: **gộp vào T171** (mở rộng `person_name_alias`, không tạo `person_names` — giữ Phương án A).

### 14.1 Schema mở rộng (`person_name_alias` +2 cột so với §3)

> **[T188]** Toàn bộ §14.1 (2 cột `is_searchable`/`source_type` + UNIQUE + partial index) **đã hấp thụ vào
> §3.2** — §3.2 giờ là nguồn schema duy nhất (hết xung đột `uq_pna` cũ), cộng thêm `normalized_ascii` (P2).

```
is_searchable INTEGER DEFAULT 1     -- legacy searchable cả verified/unverified (đã vào §3.2)
source_type   TEXT                  -- DILA | characterwise_mapping | legacy_api | scholarly_source | editorial (đã vào §3.2)
normalized_ascii TEXT               -- [T188 P2] search không dấu — CHỈ LIKE, không unique (đã vào §3.2)
```
Các field §3 đã đủ: `person_id`, `name_value`, `normalized_value`, `script`, `name_role`, `is_display_name`, `source_citation`, `confidence`, `note`, timestamps.
- **UNIQUE `(person_id, normalized_value)`** (NFC + lower + bỏ khoảng trắng thừa) — cùng tên/cùng người không trùng; người nhiều tên OK; nhiều người cùng alias OK (KHÔNG unique theo `name_value` alone) = `uq_pna_norm` §3.2.
- Partial index: tối đa 1 `is_display_name=1` mỗi person = `uq_pna_display` §3.2.

### 14.2 Case mẫu A000008 (một record duy nhất)
| name_value | name_role | source_type | confidence |
|---|---|---|---|
| `一行` | `primary_han_name` | `DILA` | `auto` |
| `Nhất Hành` (charwise T172) | `han_viet_reading` | `characterwise_mapping` | `auto` |
| `Nhất Hàng` (legacy DB, **khớp DB thật**; "Đại Huệ Thiền Sư" = ví dụ directive, KHÔNG tồn tại local — xem T172 Phase 1) | `legacy_name_unverified` | `legacy_api` | `needs_review` |

Chỉ nâng `role ∈ {common_name, title, alias}` + `confidence=verified` khi **có citation** xác nhận đồng nhất nhân vật (Admin confirm UI). Không tự khẳng định từ API.

> **[T188 P0-3]** Enum `name_role` tại đây (`primary_han_name`/`han_viet_reading`/`legacy_name_unverified`/
> `common_name`) trước đây **không có trong enum §3.2** → endpoint validate role sẽ reject chính bộ dữ liệu
> mẫu này. Đã **hợp nhất vào §3.2** — §3.2 là enum duy nhất.

### 14.3 Search (sửa §4.1 + acceptance)
- `api_dila_persons_search` (app.py:**8202** [T188 ref cũ 8018]): WHERE thêm `OR EXISTS (SELECT 1 FROM person_name_alias a WHERE a.person_id=p.id AND a.is_searchable=1 AND (a.normalized_value LIKE ? OR a.normalized_ascii LIKE ?))` → **GROUP BY p.id / DISTINCT** (Zero-RAM: LEFT JOIN + GROUP BY, không fan-out — cảnh báo 51 `dila_id` dup trong `name_vi_map`: KHÔNG join bảng đó blind). **[T188 P0-1] §5 SELECT đã sửa theo** → subquery dedupe 1 row/`dila_id` + `COUNT(DISTINCT p.id)` — hết mâu thuẫn §5 ↔ §14.3.
- **Sửa acceptance [T191 sửa số liệu drift]:** `一行` (search substring) → **4 kết quả distinct** (A000008 · A010168 · **A016240 `一行智嚴`** · **A023828 `釋一行`** — DB thật 2026-09-28 [T191]) + metadata phân biệt; KHÔNG gộp · exact `name_zh='一行'` = 2 (A000008+A010168). `Nhất Hành` / legacy → đúng 1 `person_id` (sau seed alias).
- Nhiều person cùng alias thật → hiển thị nhiều hồ sơ, không tự merge.

### 14.4 Guard chống tạo person trùng (P0)
- Không code path nào `INSERT INTO people` ngoài ETL DILA — test: `COUNT(*) people` trước = sau seed/search/alias-write.
- Dual-write §6 mở rộng: `admin_namevi_map_update` (app.py:**13926**, sync **:13974**) + `POST person/<id>/name_vi` (app.py:**18308**, sync **:18326**) → ghi mirror alias với `role=legacy_name_unverified`/`source_type=legacy_api` (trừ khi đã verified) [T188 cập nhật line refs].
- **Seed `is_display_name` [T188 P2]:** mirror legacy ghi `is_display_name=1` **CHỈ KHI** person chưa có display nào (partial `uq_pna_display`) · admin đổi display = 1 transaction: `UPDATE ... SET is_display_name=0` (cũ) → `SET =1` (mới) — không bao giờ có 2 display cùng person.

### 14.5 Profile UI (§7 mở rộng)
- Verified: `Tên hiển thị` (legacy/`is_display_name`) · `Tên Hán` · `Tên khác` (alias verified).
- Chưa verified: thêm dòng `Tên legacy/API: …` + `Trạng thái: Chưa xác nhận đây là cùng một định danh`.
- **Chốt (2026-09-25):** display mặc định = **legacy**; charwise nằm khối debug (T172), nhãn "phiên âm kỹ thuật" — không hiển thị charwise như tên chuẩn khi chưa verify.
  [T188 P0-4] → nay **khớp tuyệt đối §5.2**: strong = `name_vi_final` **chỉ khi** `standard_status ∈ {reviewed, verified}`; `auto`/`needs_review` → strong = legacy, standard xuống meta.
- Index 1 hàng/record: `A000008 | 一行 | Nhất Hàng` + phụ `Còn ghi nhận: … · Cần duyệt` — không tạo hàng riêng cho alias.

### 14.6 Tests bổ sung (`tests/test_t171_alias_search.py`)
1. Seed alias → `COUNT(*) people` không đổi.
2. Query `一行` (LIKE) → **4** `person_id` distinct (A000008/A010168/A016240/A023828) [T191 sửa số liệu] · exact `name_zh='一行'` → 2; `Nhất Hành` → `A000008` [T188: **skip case này nếu T172 chưa seed** charwise mapping — soft-dep §12]; legacy → `A000008`.
3. UNIQUE `(person_id, normalized_value)` chặn dup, cho phép người khác cùng alias.
4. Dual-write 2 endpoint tạo/mirror alias, không INSERT `people`.
5. Partial unique 1 display name/person.
6. [T188 P2] Query không dấu `Nhat Hang` khớp qua `normalized_ascii` → đúng `A000008`; `uq_pna_ascii` KHÔNG tồn tại (2 tên khác dấu cùng person không bị chặn ở ascii).

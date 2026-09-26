---
id: T171
title: "Chuẩn Hóa Tên Nhân Vật DILA — Standard Name Layer trên name_vi_map (SSOT)"
module: Editorial / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T166, T170]
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: (1) Phương án A · (2) SSOT = name_vi_map · (3) tạo task T171)"
done_when: |
  name_vi_map + person_name_alias additive (backup, idempotent, --revert);
  index 48.673 hiển thị name_vi_standard ưu tiên + badge §5.3 + filter name_status;
  search Han/API/standard/alias; CSV +8 cột / JSON names{} compat; person.html
  khối Tên và định danh + edit validate; 2 endpoint dual-write mirror people.name_vi;
  fixture A000006/A000007/A000008 PASS; 0 mất legacy; COMPLETION_REPORT; npm run pipeline PASS.
---

# T171 — Chuẩn Hóa Tên Nhân Vật DILA (SPEC)

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
| 1 | **P0** | ID `A0004…A0027` | `people.id` = **7 ký tự** `A000004` · 5 ID mẫu **0 row** | Fixture/API đổi `A000004/A000006/A000007/A000008/A000027` |
| 2 | **P0** | A0004=“Thì Xưng” · A0008=“Đại Huệ Thiền Sư” · A0027=“Tiếu Am Liễu Ngộ” | DB: `Cương Lương Gia Xá` · **`Nhất Hàng`** · **`Liễu Ngộ`** · khớp directive chỉ A000006 (chuỗi gộp) + A000007 (`Nhất Như`) | **Re-verify 5 vd trên UI live trước Phase 2** — nếu lệch, trace nguồn render (join/cache) trước migration |
| 3 | **P0** | Rule “API >80 ký tự” | `len(name_vi)>80` = **0 row** · chuỗi gộp ≈ **76 chars** → rule chết | Ngưỡng: `len≥55` **∨** `len>3×len(name_zh)` **∨** rule lặp cụm/title-stack (A000006 rơi đây) |
| 4 | **P1** | Thêm 7 cột + `person_names` mới | Trùng `name_vi_map`+`person_name_correction`+`person_display_names`+`vn_person_authority`+`_glossary_resolver` (6 nguồn) | **A:** 4 cột trên `name_vi_map` + alias thin · resolver **P0** |
| 5 | **P1** | Giữ `people.name_vi` bất biến | **2 endpoint đang ghi `people.name_vi`:** `person/<id>/name_vi` (app.py:17505) · `admin_namevi_map_update` (app.py:13154) | Dual-write: chuẩn (SSOT) + mirror `people.name_vi` (compat client cũ) |
| 6 | **P1** | Filter “Tên chuẩn” mới | Trạng thái dịch = **compute client** (`bio_vi/draft_status`) — không stored | Param API **mới** `name_status` — không đụng `status=translated\|draft\|none` |
| 7 | **P2** | Rule 1 “API trống” | `name_vi` trống = **0/48.673** | Giữ guard · ca thật = không tương ứng Hán → flag “len≥3× hoặc không share monogram” (**không AI**) · rule 7: **1.555** row không có chữ Latin → `NOT GLOB '*[A-Za-z]*'` |
| 8 | **P2** | `standard_status` init `auto` HOẶC `needs_review` | Mơ hồ | **Deterministic:** trúng rule 6.1–6.8 → `needs_review` · ngược lại → `auto` · `verified` write-time **bắt buộc** `standard_source` non-null (validate) |
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
-- backfill: standard_status = CASE WHEN <rule 6.x> THEN 'needs_review' ELSE 'auto' END
--           (KHÔNG tự điền name_vi_final mới · name_vi_final đã có = chuẩn cũ đã duyệt)
```

### 3.2 `person_name_alias` (bảng mới thin — thay `person_names` đầy đủ)

```sql
CREATE TABLE IF NOT EXISTS person_name_alias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  person_id TEXT NOT NULL,          -- people.id (A000001…)
  script TEXT NOT NULL,             -- han|vietnamese|pinyin|sanskrit|japanese|other
  name_value TEXT NOT NULL,
  normalized_value TEXT,
  name_role TEXT NOT NULL,          -- primary|common|alias|dharma_name|dharma_title|courtesy_name|art_name|posthumous_name|title|transliteration
  is_display_name INTEGER DEFAULT 0,
  source_citation TEXT,
  confidence TEXT DEFAULT 'auto',   -- auto|needs_review|reviewed|verified
  note TEXT,
  created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pna_person ON person_name_alias(person_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pna ON person_name_alias(person_id, name_value, name_role);
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

**Revert:** drop 4 index + `DROP person_name_alias` · SQLite `ALTER DROP COLUMN` ≥3.35 — nếu engine cũ: để cột NULL + ghi changelog (cột rỗng vô hại).

---

## 4. Flag rules 6.1–6.8 (chỉ cờ, không sửa tên)

| # | Rule (đã sửa ngưỡng §2) | → status |
|---|--------------------------|----------|
| 1 | `han_viet_api` trống ∧ `name_zh` có | needs_review |
| 2 | `len(name_vi) ≥ 55` ∨ `len(name_vi) > 3 × len(name_zh)` | needs_review |
| 3 | Lặp cụm ≥2 lần (token 2+ syllable) hoặc title-stack ≥2 title (`quốc sư`,`thiền sư`,`cư sĩ`,`hòa thượng`,`tăng thống`,`túc`…) | needs_review |
| 4 | `len(name_zh) ≤ 3` ∧ `len(name_vi) ≥ 25` | needs_review |
| 5 | `death_year < birth_year` ∨ tuổi ngoài [5;130] (khi 2 năm có số) | needs_review |
| 6 | `name_vi` không GLOB `*[A-Za-z]*` (1.555 row) ∨ `name_zh` có U+FFFD/ ký tự hiếm ngoài CJK phổ | needs_review |
| 7 | `standard_status='verified'` ∧ (`standard_source` IS NULL/empty) | needs_review (+ write-validate chặn tạo lại) |
| 8 | (guard) khớp `name_vi_map` cho `dila_id` thiếu row → upsert row `auto` | auto |

Init: trúng ≥1 rule → `needs_review` · ngược lại → `auto`.

---

## 5. Read path (index + search + export)

**File:** `app.py` `api_dila_persons_search` (~7996–8085) · `admin/dila_person_index.html`.

| Item | Chi tiết |
|------|----------|
| SELECT | `LEFT JOIN name_vi_map m ON m.dila_id = p.id` → trả thêm `vi_standard, standard_status, standard_source, standard_note, han_viet_api(=p.name_vi)` · **giữ nguyên** `name_zh, name_vi, …` field cũ (compat JSON/CSV client) |
| Display | Logic §5.2 directive (strong = standard fallback API; small = meta status · `API: {old}` khi khác) |
| Filter | Param **mới** `name_status=auto\|needs_review\|reviewed\|verified` · KHÔNG đổi `status` dịch |
| Search | `q` mở rộng: `p.id ∨ name_zh ∨ name_vi ∨ m.name_vi_final ∨ alias.name_value` (subquery/EXISTS — alias qua `person_name_alias` · nếu chậm: FTS5 `person_name_fts` pattern `ensure_places_pending_fts` app.py:336) |
| Sort | Giữ `sort_status` dịch · thêm sort `name_status` optional |
| CSV | +8 cột **cuối**: `dila_id, han_name_raw, han_name_normalized, han_viet_api, name_vi_standard, name_standard_status, name_standard_source, aliases` · cột cũ giữ thứ tự |
| JSON | Object `names{han_raw,han_normalized,han_viet_api,vi_standard,status,source}` + `aliases[]` · field cũ không đổi |

---

## 6. Write path (admin edit + dual-write)

| Endpoint | Sửa |
|----------|-----|
| `POST /daoanh/api/admin/person/<id>/name_standard` **(mới)** | Validate: `status=verified` ⇒ `source` non-null · upsert `name_vi_map` (dila_id=id): `name_vi_final`, `standard_status/source/note`, `approved_by='admin'`, `approved_at` · **mirror** `people.name_vi := name_vi_final` (compat) |
| `POST …/person/<id>/name_vi` (app.py:17505) **giữ** | Sau migration: ghi `people.name_vi` **và** upsert `name_vi_map.name_vi_final` + `standard_status='reviewed'` (dual-write) |
| `admin_namevi_map_update` (app.py:13112) **giữ** | Đã ghi map + sync `people.name_vi` ✓ — chỉ bổ set `standard_status` nếu client gửi |
| Alias | `POST …/person/<id>/names/alias` + `DELETE` (validate role/script enum) |
| Resolver | `_glossary_resolver` (app.py:16518): **chèn P0** = `name_vi_map.name_vi_final` khi `standard_status IN ('reviewed','verified')` — trên P1 glossary |
| T170 | Groq person output → chỉ UPDATE `standard_status='needs_review'` (+note groq), **không** set `name_vi_final` |

---

## 7. UI

### 7.1 `admin/dila_person_index.html`

- Đổi label cột → **“Tên Việt chuẩn”** · render theo §5.2 · CSS §5.5 (`person-name strong{display:block}`, `.name-meta`, 4 badge màu) · `line-clamp:2` cho API dài · tooltip/full xem detail.
- Filter **“Tên chuẩn”** 5 mức (Tất cả/Auto/Cần duyệt/Đã biên tập/Đã kiểm chứng) — control mới, không đụng 2 filter dịch/tông/triệu · badge count từ `stats` API mới `by_name_status`.
- Giữ: phân trang 50 · lọc sect/dynasty/status dịch · link `person.html?id` · export.

### 7.2 `admin/person.html`

- Khối **“Tên và định danh”**: Tên Hán · Tên chuẩn · Trạng thái (badge) · Nguồn · **Dữ liệu API gốc** · Tên khác (alias list) · Ghi chú biên tập.
- Chưa chuẩn: banner “Chưa chuẩn hóa — dữ liệu dưới đây do API/pipeline tự động cung cấp.”
- Form edit: `name_vi_standard`/`status`/`source`/`note` + add/remove alias · validate client+server · không sửa `bio*` · header (661) ưu tiên `vi_standard > name_vi`.

---

## 8. Tests & fixtures

**File:** `tests/test_t171_name_standard.py`.

| Case | Kỳ vọng |
|------|---------|
| A000006 一山国師 + chuỗi gộp | `needs_review` · **không** tạo `name_vi_final` mới · rule 2/3 (≥55 ∨ lặp) |
| A000007 一如 + Nhất Như | hiển thị `Nhất Như` · `auto` **hoặc** `needs_review` theo rule · **cấm** `verified` |
| A000008 一行 + (DB=`Nhất Hàng`) | `needs_review` · **không** tự đặt `Nhất Hành` nếu chưa có record biên tập/source |
| Fixture verified (file `tests/fixtures/t171_a000008_verified.json`, **TEST ONLY**) | index: main=`Nhất Hành`, meta=`API: … · ✓ Đã kiểm chứng` |
| Rule >80/≥55 | unit · chuỗi 76 chars **fire**, row name_vi 80+ không fire rule cũ |
| Dual-write | edit standard → `name_vi_map` + `people.name_vi` cùng giá trị · legacy không mất |
| Migration idempotent | `--apply` ×2 không lỗi · `--revert` sạch alias + status về pre |

**Không** đưa fixture TEST ONLY vào DB prod (chạy `--env test` / SQLite `:memory:`).

---

## 9. Acceptance (gộp §11 directive + Protocol)

```text
① pytest tests/test_t171_name_standard.py -v → 100% PASS (A000006/7/8)
② 0 row mất name_vi cũ (COUNT + checksum trước/sau migration)
③ Index: standard ưu tiên · chưa duyệt KHÔNG hiện “Đã kiểm chứng” · filter 5 mức
④ Search theo Han/API/standard/alias · pagination+sect+dynasty+status dịch không vỡ
⑤ CSV +8 cột cuối · JSON names{} · client cũ đọc field cũ OK
⑥ person.html xem+edit đủ · verified thiếu source = 400
⑦ Browser QA: open index + A000006/A000007/A000008 + CSV/JSON download
⑧ npm run pipeline PASS
⑨ COMPLETION_REPORT.md: file đổi · migration chạy · test · số needs_review · rủi ro
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
python scripts/t171_name_standard_migrate.py --revert   # DROP alias + index (4 cột: NULL-out nếu engine <3.35)
git revert --no-edit <sha_feat_T171>
# Restore DB nếu cần: data/backups/lineage_t171_*.db
```

---

## 12. Quan hệ

- **depends_on: T166** (canonical identity — không thêm nguồn tên thứ 6 ngoài SSOT) · **T170** (Groq → chỉ cờ needs_review · `fold_cjk` dùng chung).
- T165/T168: không đụng.
- Session: `docs/sessions/2026-09-25_t171-person-name-standard-plan.md`.

## 13. Files (dự kiến — code phase)

| Loại | Path |
|------|------|
| Sửa | `app.py` (`api_dila_persons_search` ~7996 · `person/<id>/name_vi` 17505 · `namevi_map_update` 13112 · `_glossary_resolver` 16518 · stats ~8104) · `admin/dila_person_index.html` · `admin/person.html` |
| Mới | `scripts/t171_name_standard_migrate.py` · `tests/test_t171_name_standard.py` · `tests/fixtures/t171_a000008_verified.json` · endpoint write/alias (app.py) · `COMPLETION_REPORT.md` |
| Không đụng | `people.name_zh/bio*` · bio translation · T165 code tre |

## 14. ABSORB — Addendum "Gộp nhiều tên về một nhân vật" (2026-09-25)

> Directive addendum: một person = một `person_id` + một tiểu sử; mọi tên (Hán, charwise, phổ biến, pháp húy/hiệu, tôn xưng, legacy, romanization, alias) là name record của CÙNG một profile. **TUYỆT ĐỐI không tạo person record mới vì tên khác; không xóa legacy vì lệch số Hán tự.** Chốt: **gộp vào T171** (mở rộng `person_name_alias`, không tạo `person_names` — giữ Phương án A).

### 14.1 Schema mở rộng (`person_name_alias` +2 cột so với §3)
```
is_searchable INTEGER DEFAULT 1     -- legacy searchable cả verified/unverified
source_type   TEXT                  -- DILA | characterwise_mapping | legacy_api | scholarly_source | editorial
```
Các field §3 đã đủ: `person_id`, `name_value`, `normalized_value`, `script`, `name_role`, `is_display_name`, `source_citation`, `confidence`, `note`, timestamps.
- **UNIQUE `(person_id, normalized_value)`** (NFC + lower + bỏ khoảng trắng thừa) — cùng tên/cùng người không trùng; người nhiều tên OK; nhiều người cùng alias OK (KHÔNG unique theo `name_value` alone).
- Partial index: tối đa 1 `is_display_name=1` mỗi person.

### 14.2 Case mẫu A000008 (một record duy nhất)
| name_value | name_role | source_type | confidence |
|---|---|---|---|
| `一行` | `primary_han_name` | `DILA` | `auto` |
| `Nhất Hành` (charwise T172) | `han_viet_reading` | `characterwise_mapping` | `auto` |
| `Nhất Hàng` (legacy DB, **khớp DB thật**; "Đại Huệ Thiền Sư" = ví dụ directive, KHÔNG tồn tại local — xem T172 Phase 1) | `legacy_name_unverified` | `legacy_api` | `needs_review` |

Chỉ nâng `role ∈ {common_name, title, alias}` + `confidence=verified` khi **có citation** xác nhận đồng nhất nhân vật (Admin confirm UI). Không tự khẳng định từ API.

### 14.3 Search (sửa §4.1 + acceptance)
- `api_dila_persons_search` (app.py:8018): WHERE thêm `OR EXISTS (SELECT 1 FROM person_name_alias a WHERE a.person_id=p.id AND a.is_searchable=1 AND a.normalized_value LIKE ?)` → **GROUP BY p.id / DISTINCT** (Zero-RAM: LEFT JOIN + GROUP BY, không fan-out — cảnh báo 51 `dila_id` dup trong `name_vi_map`: KHÔNG join bảng đó blind).
- **Sửa acceptance:** `一行` → **2 kết quả distinct** (A000008 + A010168 — DB thật, cùng 唐) + metadata phân biệt; KHÔNG gộp. `Nhất Hành` / legacy → đúng 1 `person_id` (sau seed alias).
- Nhiều person cùng alias thật → hiển thị nhiều hồ sơ, không tự merge.

### 14.4 Guard chống tạo person trùng (P0)
- Không code path nào `INSERT INTO people` ngoài ETL DILA — test: `COUNT(*) people` trước = sau seed/search/alias-write.
- Dual-write §6 mở rộng: `admin_namevi_map_update` (app.py:13114, sync 13154) + `POST person/<id>/name_vi` (sync 17523) → ghi mirror alias với `role=legacy_name_unverified`/`source_type=legacy_api` (trừ khi đã verified).

### 14.5 Profile UI (§7 mở rộng)
- Verified: `Tên hiển thị` (legacy/`is_display_name`) · `Tên Hán` · `Tên khác` (alias verified).
- Chưa verified: thêm dòng `Tên legacy/API: …` + `Trạng thái: Chưa xác nhận đây là cùng một định danh`.
- **Chốt (2026-09-25):** display mặc định = **legacy**; charwise nằm khối debug (T172), nhãn "phiên âm kỹ thuật" — không hiển thị charwise như tên chuẩn khi chưa verify.
- Index 1 hàng/record: `A000008 | 一行 | Nhất Hàng` + phụ `Còn ghi nhận: … · Cần duyệt` — không tạo hàng riêng cho alias.

### 14.6 Tests bổ sung (`tests/test_t171_alias_search.py`)
1. Seed alias → `COUNT(*) people` không đổi.
2. Query `一行` → 2 `person_id` distinct; `Nhất Hành` → `A000008`; legacy → `A000008`.
3. UNIQUE `(person_id, normalized_value)` chặn dup, cho phép người khác cùng alias.
4. Dual-write 2 endpoint tạo/mirror alias, không INSERT `people`.
5. Partial unique 1 display name/person.

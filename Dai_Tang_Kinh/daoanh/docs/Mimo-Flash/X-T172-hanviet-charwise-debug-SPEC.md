# T172-SPEC — Debug Pipeline Phiên Âm Hán-Việt Theo Từng Hán Tự (Charwise)

> **[2026-09-29 · T172-BUILD] ✅ BUILD DONE — SPEC §2–§11 thực hiện đầy đủ:** charmap (11.300 char / poly 552 /
> exception `蘇嚩羅`) · migrate DB THẬT `person_hanviet_debug` 47.036 rows (status valid 40.575 · mismatch 920 ·
> unknown_char 534 · exception 1 · needs_review 5.006; legacy exact 38.912 · normalized 1.661 · differs 5.930 ·
> not_comparable 533; translit 40.573) · people 48.673 nguyên vẹn · API: list `?hv_status` (7 mức) + detail `hv`
> (helper `_t172_load_hv()`) + `GET /daoanh/api/dila/hv/stats` · UI index ⚠/tooltip/filter + detail #card-hv ·
> tests 64/64 · lint-check.ps1 fix kèm (Batch 4 ROLLBACK §5) · REPORT đã tạo. **Phase 1 re-verify UI live (7 ví dụ)
> = Nợ acceptance sau restart server (VPS/HITL).** Revert: `git revert --no-edit <sha_T172_pass1>` + migrate `--revert`.

**Task:** T172 · **Loại:** code (sidecar + migration + API + UI) · **Dependencies:** T166 (identity guard, khi build), T171 (alias, song song) · **SSOT kèm:** `HANVIET_DEBUG_PLAN.md` (plan chi tiết đã inspect, đọc trước khi code)
**Admin chốt 2026-09-25:** (1) đa âm = reading chính + `needs_review` + candidates · (2) gộp addendum vào T171 `person_name_alias` · (3) sidecar `person_hanviet_debug` · (4) legacy giữ display.

> Dữ liệu **kiểm tra kỹ thuật**, không phải tên chuẩn Phật học. `valid` ≠ verified.

> **[2026-09-28 · T191] AMEND — Docs-correction (Admin phê chuẩn đề xuất audit 2 file T172; docs-only, 0 code/0 DB):**
> **L1** — Line refs DRIFT (build theo SPEC sẽ nhầm chỗ): `_han_viet()` = app.py **1849** (trước ghi 1822) ·
> `HAN_VIET_CHAR` = app.py **1294** (trước ghi export từ 1267). Đã sửa inline §2/§3.
> **L2** — `一行` thực tế **4 person** khi search substring (`name_zh LIKE %一行%`): A000008 · A010168 ·
> **A016240 (`一行智嚴`)** · **A023828 (`釋一行`)** — exact `name_zh='一行'` = 2. Đồng bộ T171 SPEC §14.3/§14.6 + 2 pointer (trước ghi 2).
> **L3** — Minor: sidecar "12 cột" nhưng liệt kê 13 (gồm `person_id` PK) → "12 cột dữ liệu + PK";
> `bulk_transliterate.py` = **root daoanh** (không phải `scripts/`); định nghĩa `is_transliteration`;
> pointer refs dual-write **13926/18308** (trước 13114/17523 — drift).
> Chi tiết: `tasks/T191-t172-build-docs-correction.md`. Verify DB thật: `一行` LIKE → 4 ids · `大慧禅师` → 0 ·
> A000044 `Tô Phược La` → 1 · `hanviet_fallback` 8.650 · `custom_hanviet_override` 3.968.

---

## 1. Scope
- Tạo `hanviet_char_map` (merge 3 dict, version) + `person_hanviet_debug` (sidecar 13 field: 12 cột dữ liệu + PK `person_id`) + `hanviet_exception_list` (seed).
- API `GET /daoanh/api/dila/persons` + `/api/persons/<id>` attach debug fields + filter `hv_status`.
- UI: icon `⚠` + tooltip + filter debug (index); khối read-only (detail).
- Migration idempotent + backup + `--revert` + log count/status.
- KHÔNG sửa `people.name_vi` · KHÔNG gọi API ngoài · KHÔNG LLM.

## 2. Root cause (đã verify — trích `HANVIET_DEBUG_PLAN.md` §1)
- `people.name_vi` seed từ `name_vi_map` (`seed_persons_namevi.py`, 45.938 row), trộn 5 nguồn.
- `bulk_transliterate.py` (file ở **root `daoanh/`** — không trong `scripts/` [T191 path note]) Priority 1 = **lexicon khớp cả chuỗi** → chuỗi "preferred"/metadata (A000006 = 17 âm, verify DB ✓).
- `_han_viet()` (app.py:**1849** [T191 ref fix — trước ghi 1822]) charwise nhưng **chỉ cho place**.
- 3 dict xung đột (1.478 / 8.650 / 3.968), case hỗn độn.
- `name_vi_map` bẩn: 4.869 `dila_id` NULL · 322 `name_zh` lệch · 51 dup.
- 6/7 ví dụ directive lệch DB thật → **Phase 1 re-verify UI live** (A000008=`Nhất Hàng`, A000026=`Liễu Trinh`, A000044=`Tô Phược La`, A000047=`Vu 頔`; ID phải pad 7 ký tự).

## 3. Schema (SQL đầy đủ xem plan §3)
- `hanviet_char_map(char PK, reading, source, is_polyphonic, candidates)` — priority `custom_hanviet_override` > `HAN_VIET_CHAR` > `hanviet_fallback`; assert 1 reading = 1 âm tiết; export `HAN_VIET_CHAR` từ app.py:**1294** [T191 ref fix — trước ghi 1267] ra file JSON/CSV tạm để seed.
- `person_hanviet_debug(person_id PK, han_name_raw, han_viet_legacy, han_viet_charwise, han_char_count, han_viet_syllable_count, unknown_characters, han_viet_validation_status, han_viet_validation_reason, legacy_match_status, is_transliteration, dict_version, updated_at)` — **12 cột dữ liệu + PK `person_id`** (tổng 13 field).
  - `is_transliteration` **[T191 định nghĩa]:** `=1` khi (a) `unknown_characters` RỖNG (mọi Hán tự có reading) VÀ (b) `legacy_match_status ∈ {exact, normalized}` — tức legacy `name_vi` sinh ra đúng từ phiên âm từng tự, KHÔNG phải chuỗi metadata/hiệu; `=0` khi có unknown/khác/not_comparable. Chỉ là cờ, không auto verified.
- `hanviet_exception_list(char_sequence PK, note, added_by)` seed: `蘇嚩羅`.

## 4. Algorithm (mỗi person, generator, Zero-RAM)
```
for id, name_zh, name_vi in pages:            # cur.execute + fetchmany(2000)
    han = [c for c in name_zh if is_ideograph(c)]      # ranges plan §4.1
    readings, unknown, poly = [], [], []
    for c in han:
        r = char_map.get(c)
        if r is None: readings.append(f"[?{c}]"); unknown.append(c)
        else:
            readings.append(r.reading)
            if r.is_polyphonic: poly.append((c, r.candidates))
    charwise = ' '.join(readings)
    status = validate(unknown, exception_list, len(han), len(readings))
    reason = f"…đa âm {c}: {'|'.join(cands)}…" if poly else …
    legacy_match = compare(name_vi, charwise)          # plan §4.4
    UPSERT (idempotent)
```
Status order: `unknown_char` → `exception` → `mismatch` → `valid`. Đa âm (có reading) → charwise tính `valid/nhưng` `han_viet_validation_reason` ghi `needs_review` marker; **status_field** dùng `needs_review` khi (a) đa âm khác legacy, hoặc (b) directive yêu cầu duyệt (`differs` + poly) — rule: `unknown > exception > (poly & differs → needs_review) > mismatch > valid`.

## 5. API
- `GET /daoanh/api/dila/persons?hv_status=…` — thêm `LEFT JOIN person_hanviet_debug d ON d.person_id=p.id`; WHERE `d.han_viet_validation_status=?` map `match→valid+normalized/exact`, `differs→d.legacy_match_status='differs'`. Response thêm object `hv{charwise,legacy,status,reason,legacy_match,han_count,syll_count}` (không đổi field cũ).
- `GET /daoanh/api/persons/<id>` — thêm `hv` object.
- Thêm `GET /daoanh/api/dila/hv/stats` (count theo status) cho filter badges.

## 6. UI
- Index: cột icon `⚠` (≈24px) khi `hv.status ∈{mismatch,unknown_char,exception,needs_review} || hv.legacy_match==='differs'`; tooltip 5 dòng; `<select id=hv-filter>` 6 mức → reload với `hv_status`. CSS cùng style amber `#d97706`/dark slate.
- Detail `person.html`: khối "Kiểm tra phiên âm Hán-Việt" (read-only, 6 dòng theo directive), ẩn khi không có `hv`.

## 7. Migration
`scripts/t172_hanviet_charwise_migrate.py`
- `--backup` (default ON): copy `lineage.db` → `data/backup/lineage_t172_<ts>.db` (file-level, trước khi ghi) hoặc dump 3 cột sang JSON nếu `--no-copy`.
- `--limit N`, `--person A000001,…` (fixture nhỏ trước).
- Idempotent `INSERT OR REPLACE`; log cuối: counts theo 5 status + 5 legacy_match → console + `data/t172_status_counts.json`.
- `--revert`: DROP 3 bảng sidecar (không đụng `people`); hướng dẫn restore backup.
- KHÔNG ghi `people` — test assert `COUNT(*) people` trước = sau.

## 8. Tests (`tests/test_t172_charwise.py` + fixture JSON)
7 fixture theo plan §8 +: ideograph counter (kể U+279CC) · validate order · legacy compare (NFC/lower/whitespace; `Vu 頔`→not_comparable) · idempotent chạy 2× · people immutability · không placeholder cho chữ có reading · exception flag không auto-sửa.

## 9. Phases
1. **Re-verify UI live** 7 ví dụ + truy nguồn "Đại Huệ Thiền Sư" (ghi vào REPORT; nếu lệch lớn → dừng hỏi Admin).
2. Export/merge dict → `hanviet_char_map` + assert 1 âm tiết + exception seed.
3. Migration script (backup/idempotent/revert/log) → chạy fixture nhỏ → chạy full 48.673.
4. API attach + filter + stats.
5. UI index + detail.
6. Tests + `npm run pipeline`.
7. **REPORT** `docs/Mimo-Flash/T172-hanviet-charwise-debug-REPORT.md`: file sửa, test, số record/status, rủi ro.
8. (Đi cùng) T171 alias seed/search — theo SPEC T171 §amend.

## 10. Revert
- Code/docs: `git revert --no-edit <sha_T172>` (mỗi phase 1 commit riêng).
- DB: `python scripts/t172_hanviet_charwise_migrate.py --revert` + backup restore.
- KHÔNG rollback `people` (không bao giờ ghi).

## 11. Files dự kiến
| File | Việc |
|---|---|
| `scripts/t172_build_charmap.py` | merge 3 dict → `hanviet_char_map` (+export HAN_VIET_CHAR) |
| `scripts/t172_hanviet_charwise_migrate.py` | backup/seed/revert/log |
| `app.py` | `_t172_load_hv()` helper + attach/filter/stats (3 endpoint, +~80 dòng, không đổi field cũ) |
| `admin/dila_person_index.html` | icon/tooltip/filter |
| `admin/person.html` | khối read-only |
| `tests/test_t172_charwise.py`, `tests/fixtures/t172_hanviet_cases.json` | tests |
| `docs/Mimo-Flash/T172-hanviet-charwise-debug-REPORT.md` | bàn giao |
| `HANVIET_DEBUG_PLAN.md` | plan gốc (đã tạo) |

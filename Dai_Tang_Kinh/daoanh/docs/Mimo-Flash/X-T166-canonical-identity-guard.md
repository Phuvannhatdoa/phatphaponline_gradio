---
id: T166
title: "Canonical Identity Hard Guard — Zero-Tolerance LLM Proper-Name Protection"
module: Editorial / LLM Translation / Identity
priority: high
status: in_progress
owner: claudecode
depends_on: [T73, T123, T158-glossary-resolver, T165]
created: 2026-09-25
updated: 2026-09-26
spec_path: docs/Mimo-Flash/T166-canonical-identity-guard-SPEC.md
designed_by: mimo-flash (system-design skill)
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-24 — Admin phê chuẩn Phương án A (layer trên T165)"
done_when: |
  CanonicalLock per-request từ authority thật (threshold mới LOCK);
  pre/post assert + invent detect; write-deny path identity;
  fail → identity_status additive, không verified/name_vi_final;
  matrix A–J pass; ghép T165 style_lock/constitution_hash;
  pipeline PASS; có revert.
---

# T166 — Canonical Identity Hard Guard (DEV TASK)

**Spec:** `docs/Mimo-Flash/T166-canonical-identity-guard-SPEC.md` (đã Admin absorb SAFETY-003 + T168 directive, 2026-09-25).
**Repo SSOT:** `git rev-parse --show-toplevel` == `visjs-app` (daoanh là subdir).

## Phân chia build (theo §17 SPEC)

| Phase | Việc | Output |
|-------|------|--------|
| 1 | `canonical_lock.py` build/assert/normalize (Zero-RAM, SQL batch) | unit test A–D (LOCK person/place/dharma/term) |
| 2 | Wire pre/post vào `style_constitution.py` + `app.py` interactive translate (bio/place/passage/relation) | py_compile; `identity_status` set đúng |
| 3 | Write-deny audit (`assert_not_identity_autowrite`) + `identity_status` migrate (`translation_cache` +index) | script migrate + db_schema.md |
| 4 | Matrix A–J test trên DB copy + `npm run pipeline` | tests green |
| 5 | Dashboard regen + Admin confirm | tasktodo → taskdone |

## Fixture chuẩn (Admin chốt §20.3)

| Case | Entity | Source form | Canonical VI | Lock type | Authority |
|------|--------|-------------|--------------|-----------|-----------|
| A (PASS) | A009460 | 丹霞天然 | Đơn Hà Thiên Nhiên | LOCKED | vn_person_authority status='verified' |
| B (HARD_FAIL) | A009460 | 丹霞天然 | Thích Đơn Hà Mật | LOCKED | mismatch → failed |
| C (PASS/CANDIDATE) | A005248 | 安廩 | An Lẫm | CANDIDATE (auto 0.7) | name_vi_map confidence 0.7, final=NULL → không LOCK |
| D (CONFLICT) | — | 2+ nguồn VI khác | — | CONFLICT | keep claims[] |
| E (UNKNOWN) | — | unknown 2-char | invent VI | UNKNOWN_REVIEW | flag, không auto identity |

**Lưu ý:** bio A005248 KHÔNG chứa `安廩` → `source_text` cho test là câu mẫu tự viết. A005248 có cache row `status='edited'` id 1768 → test trên DB copy.

## File sẽ tạo/sửa

| Loại | Path |
|------|------|
| Module mới | `canonical_lock.py` (cùng cấp app.py / style_constitution.py) |
| Migrate | `scripts/t166_identity_migrate.py` (--stats/--dry-run/--apply/--revert) |
| Extend | `style_constitution.py` (thêm `t166_lock_fingerprint` vào constitution_hash) |
| Wire | `app.py` — pre/post assert trong `_t73_call_gemini` / translate paths |
| Tests | `tests/test_t166_canonical_lock.py`, `tests/test_t166_matrix.py` |
| Docs | `docs/db_schema.md` (+ identity_status), `docs/tasktodo.md`, session log, ROLLBACK.md |

## Zero-RAM constraint

- Lock build = SQL `IN (...)` theo maximal Han run extract từ source_text
- KHÔNG load full 248k glossary_vi / 48k people / 59k places vào list
- N-gram extract: chỉ maximal Han run ≥2, cap ~40/prompt

## Revert path

- Code: `git revert --no-edit <sha>`
- DB: `python -X utf8 scripts/t166_identity_migrate.py --revert` + restore `data/backups/lineage_t166_*.db`

---

## Phase 1 — `canonical_lock.py` (hiện tại)

### Core functions
1. `build_canonical_lock(conn, source_text)` → list of `CanonicalLockEntry`
2. `pre_assert(lock, policy)` — trước `_t73_call_gemini`
3. `post_assert(lock, output, policy)` — sau `_t73_call_gemini` → `identity_status` + `identity_issues[]`
4. `normalize_vi(s)` — strip honorific/title, NFC, casefold
5. `extract_maximal_han_runs(text)` — chỉ chuỗi Hán dài nhất ≥2, không n-gram chồng lấp
6. `is_valid_vi(s)` — reject mojibake `?`/`�`/rỗng

### Lock entry fields
```python
CanonicalLockEntry(
    source_form: str,           # Hán trong source (exact)
    normalized_form: str,       # NFC / strip space
    entity_type: str,           # PERSON|DHARMA_NAME|PLACE|TEMPLE|DYNASTY|ERA|LINEAGE|BUDDHIST_TERM
    canonical_id: str,          # DILA A009460 / PL… / NULL
    canonical_value: str,       # GIÁ TRỊ LOCK (VI) — vd "Đơn Hà Thiên Nhiên"
    authority_source: str,      # table+column
    authority_level: float,     # SOURCE_LEVELS mapping
    status: str,                # LOCKED | CANDIDATE | UNKNOWN_REVIEW | CONFLICT
    claims: list[dict],         # nếu conflict: giữ TẤT CẢ claims
)
```

### SOURCE_PRIORITY (chung với `_glossary_resolver` — §3.1 SPEC)
1. `canonical_decision` → join `places_dila`/`people` lấy `name_zh` làm `source_form`
2. `person_display_names` WHERE `verification_status LIKE 'verified%' AND is_preferred=1`
3. `vn_person_authority` WHERE `status='verified'`
4. `person_name_correction` WHERE `status='applied'`
5. `translation_glossary` WHERE `is_locked=1` (≥2 chars → BUDDHIST_TERM)
6. `name_vi_map` WHERE `name_vi_final IS NOT NULL` (authority) · `approved_by NOT NULL` = boost
7. `namevi_map_places` WHERE `vn_name_status='reviewed'` (confidence → CANDIDATE)
8. `people.name_vi` CHỈ nếu provenance approved (default KHÔNG lock)

### Lock threshold
- `LOCKED` khi: flag hợp lệ (`verified/reviewed/applied/final+approved`) + `is_valid_vi` + `SOURCE_LEVELS ≥ 1.0`
- `SOURCE_LEVELS`: verified/applied/final+approved=1.0 · reviewed=0.9 · vn_person_authority verified=0.95 · confidence auto (0.5–0.7) = 0.7 → **CANDIDATE**
- Auto confidence → **CANDIDATE**, bất kể entity type

### Policy P-PARTIAL (mặc định)
- Unknown/CANDIDATE → vẫn dịch, giữ Hán cho unknown, flag `identity_status`
- `UNCONTROLLED_PROPER_NAME` (khớp authority nhưng chưa phân loại) → STOP = bug → `review_required`

### Post-assert severity
- HARD: CANONICAL_IDENTITY_MISMATCH (PERSON/PLACE/DHARMA_NAME/BUDDHIST_TERM ≥2 chars)
- WARN: TERM_LEN1_MISMATCH (term 1-char glossary) — không hạ identity_status
- HARD: CANONICAL_INVENTION (person-like VI không trong allowed_vi_set, position-is-title check)
- `UNKNOWN_REVIEW` token → `review_required` (không `failed`)

---

## Checklist thực hiện Phase 1

- [ ] Tạo `canonical_lock.py` với các hàm core
- [ ] Unit test A–D: LOCKED person/place/dharma/term PASS; mismatch FAIL
- [ ] `extract_maximal_han_runs` test (cap ~40, không n-gram chồng lấp)
- [ ] `normalize_vi` test (strip title `Thích`/`Thích Ca` → `Thích An Lẫm` PASS, `Thích An Nạp` FAIL)
- [ ] `is_valid_vi` test (mojibake reject)

---

## Session log
- 2026-09-25: Task file tạo, bắt đầu Phase 1
- 2026-09-25: **Phase 1 DONE** — `canonical_lock.py` (1182 dòng) + `tests/test_t166_canonical_lock.py` 18/18 + `tests/test_t166_matrix.py` 23/23 (real DB read-only). Commit `4107cca`.
- 2026-09-26: **Phase 2 + 3 DONE** — (a) `style_constitution.py` thêm `t166_lock_fingerprint` (gating chống mass-miss — chỉ miss khi có LOCKED) vào `constitution_hash` + `_t166_identity_block` (4 block) vào `build_style_prompt` TRƯỚC Style Constitution + `write_cache` ghi 3 cột identity + helpers `is_trusted_translation`/`is_draft_translation`/`identity_lock_policy`. Commit `0150e66`. (b) `scripts/t166_identity_migrate.py` --apply trên DB thật + verify revert 2 chiều (1762 cache + 112 rules nguyên vẹn). (c) `app.py` wire `_t166_post_check_translation` vào 4 translate paths (person_bio/dila_card/place_note/relation_evidence) + SECURITY: `verify_session` trên `admin_namevi_map_update` (nguồn LOCKED) + `name_vi_source` flag + expose identity khi cache-hit. (d) `scripts/t166_identity_audit.py` (write-deny CI audit) wire vào pipeline `audit:t166`. (e) `cbeta_translate_worker.py` identity guard → `needs_review` + validation_report. Commit `b89c7bed`.
- 2026-09-26: **Phase 4 pending** — matrix A–J chạy real DB ro (23/23), cần: dashboard regen + taskdone closure (Phase 5)

## ROLLBACK SEQ
- 2026-09-26: 3 commits — revert theo thứ tự ngược: `git revert --no-edit b89c7bed` → `0150e66` → `4107cca` (xem `docs/ROLLBACK.md`). DB: `python -X utf8 scripts/t166_identity_migrate.py --revert` + restore `data/backups/lineage_t166_20260926_080107.db`.
---
id: T170-dila-place-person-v41-verify
title: "T170 BUILD — Entity verify pipeline v4.1: person side-car + extend T169 (R2/R3/R4/R5/R6/R7) theo SPEC đã amend"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T169, T170-dila-place-person-v41-amend]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (Code Phase 1–6 xong; migrate person --apply DB thật; pipeline PASS; còn bước thủ công VPS = chạy full --entity person cần GROQ key)"
plan_approved_at: "2026-09-25 (Admin: Đồng ý build · 2 side-car · task T170 · UI person defer) — theo SPEC frontmatter"
done_when: |
  Phase 1: scripts/t170_entity_groq_audit_migrate.py --stats/--dry-run/--apply/--revert (đã --apply DB thật,
           backup data/backups/lineage_t170_20260928_150114.db; side-car person_groq_audit 21 cột + idx_gpa_review/idx_gpa_diff;
           guard place_groq_audit T169 13 cột OK).
  Phase 2: scripts/t170_classify.py (R2 bracket stack + R3 fold_cjk + R4 title loop + Sanskrit registry + tái dùng t169 classify)
           + tests/test_t170_person_classify.py 17/17 PASS.
  Phase 3–4: scripts/verify_dila_places_groq.py refactor --entity {place,person} (R5 bỏ WAL/busy_timeout=10000 + synchronous=NORMAL;
           R6 normalize_groq trans_vi flat/nested/regex; R7 max_tokens 2048 + salvage 1 call; SKIP auto_* G4; cursor place '0').
           Smoke mock temp DB: place 3/3 verified + dedup 0; person 4/4 auto-verified + dedup 0.
  Phase 5: đối chiếu enum app.py GET place-groq-review + UI tabs = KHÔNG cần sửa (auto_* chỉ person; person UI defer).
  Phase 6: tests/test_t170_verify_pipeline.py 15/15 + npm run test:t170 vào test:translation + npm run pipeline PASS
           (guard/lint/test/translation/UAT/compliance/gov/audit:t166/e2e; e2e:runtime EPERM pre-existing).
  Docs: SPEC §12 BUILD CLOSURE + pointer + task + session + tasktodo + ROLLBACK + dashboard regen; commit 2-pass hash-fill.
  Revert: git revert --no-edit <sha_T170> + python -X utf8 scripts/t170_entity_groq_audit_migrate.py --revert (person-only;
           place thuộc T169 revert bằng t169_place_groq_audit_migrate.py --revert).
---

# T170-dila-place-person-v41-verify — BUILD entity verify v4.1

## Bối cảnh

SPEC `docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md` được amend (task `T170-dila-place-person-v41-amend`)
sau khi T169 build xong → T170 = **REFACTOR/EXTEND** T169 (absorb `行` + core R1) + phần THẬT SỰ mới:
person side-car + `--entity person` + R2/R3/R4/R5/R6/R7. Task này = BUILD code toàn bộ theo SPEC §12, không
chạy full ~1.947 batch (chờ GROQ key trên VPS).

## Việc đã làm

| Phase | Việc | Kết quả |
|-------|------|---------|
| 1 | `scripts/t170_entity_groq_audit_migrate.py` (`--stats/--dry-run/--apply/--revert`) | `--apply` DB thật: `person_groq_audit` (21 cột) + `idx_gpa_review`/`idx_gpa_diff`; backup `data/backups/lineage_t170_20260928_150114.db` (1.410 MB); stats people 48.673 / 25 = **1.947 batch**; guard place 13 cột OK |
| 2 | `scripts/t170_classify.py` + `tests/test_t170_person_classify.py` | **17/17 PASS** (R2 lồng/unbalanced · R3 fold 惠→慧 · R4 prefix/suffix · Sanskrit khớp/lệch/unmapped · TITLE_VARIANT · POLYPHONIC · FORMAT · NONE) |
| 3–4 | `scripts/verify_dila_places_groq.py` refactor `--entity {place,person}` | R5 bỏ WAL pragma + `busy_timeout=10000` + `synchronous=NORMAL` · R6 `normalize_groq()` flat/nested/fence/regex/empty · R7 max_tokens 512→2048 + salvage 1 call · `SKIP_STATUSES` mở rộng auto_* (G4) · smoke mock: place 3/3 + dedup 0 · person 4/4 + decup 0 |
| 5 | Đối chiếu enum place API/UI (`app.py` GET + `place_update.html` tabs) | **Không cần sửa** — place domain chỉ sinh verified/approved_dict/conflict/api_error; auto_* chỉ person (UI defer) |
| 6 | `tests/test_t170_verify_pipeline.py` + `test:t170` + pipeline | **15/15 PASS** (R6 parse 5 + R5 pragma 2 + TAXONOMY regression 2 + place cursor/G4 2 + person extras/G4 2) · `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing |

## Ghi chú kỹ thuật

- **`EntityConfig` tương đương**: entity place/person dùng chung khung directive (batch 25 · RPM adaptive · retry 429 · atomic `with conn` · json_object fallback · mock) — khác spine SQL + upsert SQL + classify.
- **Person upsert** ghi thêm: `final_vi` · `clean_zh`/`meta_note`/`variant_zh`/`is_uncertain` (R2 bracket-strip + R3 fold) · `retry_count`/`last_error` (R7) · `processing_started_at`.
- **status_hint** (từ `classify_person_diff`) → auto status: `auto_verified_sanskrit` · `auto_title_aligned` · `needs_lexicon_review` (SANSKRIT_UNMAPPED) · `auto_verified` (FORMAT).
- **G4 mở rộng**: skip cả `auto_verified`/`auto_verified_sanskrit`/`auto_title_aligned`/`auto_taxonomy_aligned` (resolved 1 lần, không gọi lại API).
- Env override `T170_DB` (ưu tiên hơn `T169_DB`) cho test temp.

### Bug T169 bắt được khi smoke mock (đã fix + regression)

1. **Cursor khởi tạo**: smoke mock phát hiện `:cursor=''` với **test-harness place id INTEGER** ⇒ `d.id > ''` **0 rows** (pipeline vô dụng). Lưu ý: id THẬT `places_dila.id`/`people.id` = **TEXT** (`PL000000000001…`/`A000001…`) — bug không tái hiện trên DB thật. Fix: khởi tạo `cursor='0'` (an toàn mọi entity) [T189 đính chính].
2. **TAXONOMY self-match**: `TAXONOMY_SUFFIX['殿']=('điện','điện')` ⇒ dict==groq cùng `điện` vẫn `TAXONOMY_VARIANT` conflict. Fix: skip cặp `hv_n == vern_n` trong `t169_classify.py`.

### Giới hạn R8 (document)

`normalize_text` bỏ dấu ⇒ `hạnh`/`hành` cùng `hanh`: person polyphonic chỉ phân biệt được cặp đổi phụ âm
(giáng/hàng); tone-variant tự nhận Sanskrit/verified. Ghi chú trong `t170_classify.py __main__`.

## Còn lại (thủ công, VPS — cần GROQ key)

1. `python -X utf8 scripts/verify_dila_places_groq.py --entity person` (full ~1.947 batch).
2. Review `person_groq_audit` (UI person defer — xem qua SQL/API sau nếu cần).

## Revert

- **Commit code+docs:** `git revert --no-edit <sha_T170>` (khôi phục code/scripts/tests/docs về trước T170 build).
- **DB:** `python -X utf8 scripts/t170_entity_groq_audit_migrate.py --revert` (DROP person side-car + 2 index — KHÔNG đụng place).
  Khôi phục dữ liệu nếu cần: copy `data/backups/lineage_t170_20260928_150114.db` → `data/lineage.db`.
- **Place (T169) revert** riêng: `python -X utf8 scripts/t169_place_groq_audit_migrate.py --revert`.
- Cấm `cp *.bak` · cấm `reset --hard`.
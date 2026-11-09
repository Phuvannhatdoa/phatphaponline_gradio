---
id: T169-place-groq-audit-build
title: "T169 BUILD — Robust Batch Verification Pipeline (Groq Qwen vs SQLite) theo SPEC X-T169 đã sửa T184"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T184]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (Code Phase 1–6 xong; migrate --apply DB thật; pipeline PASS; còn bước thủ công VPS = chạy full verify cần GROQ key)"
plan_approved_at: "2026-09-25 (Admin: Đồng ý build · Chốt phương án A side-car) + 2026-09-27 (Admin: 'Đồng ý build, hãy lưu logs... Gọi pipip khi done')"
done_when: |
  Phase 1: scripts/t169_place_groq_audit_migrate.py --stats/--dry-run/--apply/--revert (đã --apply DB thật,
           backup data/backups/lineage_t169_20260928_130129.db; side-car place_groq_audit + 2 index).
  Phase 2: scripts/t169_classify.py (classify_diff + trụ đa âm static + TAXONOMY_SUFFIX + fixtures)
           + tests/test_t169_classify_diff.py 11/11 PASS + npm run test:t169.
  Phase 3: scripts/verify_dila_places_groq.py — batch 25, :cursor memory, resume scan-qua-predicate
           (giữ NOT IN verified/approved_dict kể cả --force), RPM adaptive, json_object fallback,
           safe_parse_json_content, atomic tx. Smoke mock temp DB: limit 25 → 25 verified, re-run → 6 (resume ✓).
  Phase 4: app.py GET /daoanh/api/admin/place-groq-review + PUT /daoanh/api/admin/place-groq-review/<id>
           (3-bước 1 tx: audit status + places_pending name_vi/name_vi_norm recompute + namevi_map_places UPSERT).
           Smoke SQL trên temp DB: 3-bước OK + filter conflict/api_error OK.
  Phase 5: admin/place_update.html rewrite (3 tab Cần xem xét / Lỗi API / Đã duyệt, filter diff, radio manual) — e2e PASS.
  Phase 6: npm run pipeline PASS (guard/lint/test/t169/UAT/compliance/gov/audit:t166/e2e; e2e:runtime EPERM pre-existing).
  Docs: task + session + tasktodo + ROLLBACK + SPEC/pointer tick + dashboard regen; commit 2-pass hash-fill.
  Revert: git revert --no-edit 393676f36fdc7d42469fd52b39bf004b18fbc42b + migrate --revert DROP side-car + restore backup.
---

# T169-place-groq-audit-build — BUILD theo SPEC X-T169 (đã sửa T184)

## Bối cảnh

SPEC `docs/Mimo-Flash/X-T169-groq-place-verify-pipeline-SPEC.md` được T184 review + sửa 7 điểm
logic (G1–G7). Task này = BUILD code thật toàn bộ 6 phase theo SPEC đã chốt, không chạy full
2.366 batch (chờ GROQ key trên VPS).

## Việc đã làm

| Phase | Việc | Kết quả |
|-------|------|---------|
| 1 | `scripts/t169_place_groq_audit_migrate.py` (`--stats/--dry-run/--apply/--revert`) | `--apply` DB thật: `place_groq_audit` + idx `idx_pga_review`/`idx_pga_diff`; backup `data/backups/lineage_t169_20260928_130129.db` (1.410 MB); stats 59.150/25 = **2.366 batch chẵn** |
| 2 | `scripts/t169_classify.py` + `tests/test_t169_classify_diff.py` | **11/11 PASS** (fixture 降魔窟 POLYPHONIC, 長安 Tràng An, 陝西 Thiểm Tây...) |
| 3 | `scripts/verify_dila_places_groq.py` | Smoke mock temp DB: 25/25 verified + resume 6/6 (skip verified/approved_dict) |
| 4 | app.py GET/PUT `place-groq-review` (chèn sau `api_admin_place_missing_info`) | py_compile OK; smoke SQL 3-bước tx + filter OK |
| 5 | `admin/place_update.html` rewrite | e2e PASS + thêm vào `scripts/e2e-test.js` pages |
| 6 | `npm run pipeline` | PASS trừ `e2e:runtime` EPERM pre-existing |

## Ghi chú kỹ thuật

- **Env override `T169_DB`**: migrate/verify đọc DB từ env để test temp không đụng DB thật.
- **G4 giữ nguyên**: `--force` vẫn `NOT IN (verified, approved_dict)`.
- **G3 RPM adaptive**: đọc `x-ratelimit-remaining-requests` ≤5 → sleep 3s, else 2,2s (~27 RPM).
- **G5 classify**: POLYPHONIC → TAXONOMY → PHONETIC → NONE, dừng nhãn đầu; trụ đa âm static inline trong `t169_classify.py`.
- **G6 PUT**: 3 bước 1 transaction; `name_vi_norm` recompute reuse `normalize_text` app.py:81.
- UI filter (G7): `needs_review=1 AND diff_type IS NOT NULL AND review_status='conflict'`; tab "Lỗi API" (`api_error`).

## Còn lại (thủ công, VPS — cần GROQ key)

1. `python -X utf8 scripts/verify_dila_places_groq.py` (full ~2.366 batch, 80–120 phút).
2. Admin review trên `admin/place_update.html` (duyệt/đổi dict/groq/manual).

## Revert

- **Commit code+docs:** `git revert --no-edit 393676f36fdc7d42469fd52b39bf004b18fbc42b` (khôi phục code app.py/UI/scripts về trước T169).
- **DB:** `python -X utf8 scripts/t169_place_groq_audit_migrate.py --revert` (DROP side-car + 2 index).
  Khôi phục dữ liệu nếu cần: copy `data/backups/lineage_t169_20260928_130129.db` → `data/lineage.db`.
- Cấm `cp *.bak` · cấm `reset --hard`.
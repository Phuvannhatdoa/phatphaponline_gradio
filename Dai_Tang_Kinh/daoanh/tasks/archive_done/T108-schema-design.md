---
id: T108
title: "Schema Design — Hiến pháp dữ liệu Evidence-first (docs SCHEMA_DESIGN.md)"
module: Data Governance / Assertion Architecture
priority: high
status: done
depends_on: []
created: 2026-09-08
updated: 2026-09-08
completed: 2026-09-08
done_when: >
  docs/SCHEMA_DESIGN.md định nghĩa đủ 7 mục: thuật ngữ cốt lõi (Assertion/
  Provenance/Confidence/Scoped Corpus), ERD với số liệu thật (entity_hub 167,006;
  entity_claims 447,885; data_sources 13; lineage_conflicts_v2 40,327), kiểu dữ
  liệu String/Enum/Real/Timestamp, Confidence & Precedence policy, Audit ID
  content-hash (thay UUID), Scoped Corpus, Data Policy + compliance metrics;
  nêu 3 độ lệch đã verify (events không provenance · review 0% · persona display
  chưa có) và gán task T109-T113. Không code, không đụng DB (docs-only).
---

# T108 — Schema Design (Hiến pháp dữ liệu Evidence-first)

## Mục tiêu
Chuyển đặc tả "T01 — Cấu trúc Assertion" (Lee Tổng phê chuẩn) thành **docs/SCHEMA_DESIGN.md**:
định nghĩa Assertion là đơn vị dữ liệu nhỏ nhất (Nội dung + Chứng cứ + Trạng thái thẩm định),
định nghĩa Provenance/Confidence/Scoped Corpus, ERD dựa trên DB thật, quy định kiểu dữ liệu,
Audit ID content-hash (thay yêu cầu UUID), Data Policy cho dữ liệu không khớp, bộ compliance
metrics để Dashboard đo mức tuân thủ.

## Phạm vi
- **Docs-only.** KHÔNG viết code, KHÔNG đụng DB, KHÔNG migration.
- Tạo: `docs/SCHEMA_DESIGN.md` + `tasks/T108…T114-*.md`.
- Cập nhật: `docs/tasktodo.md` · `docs/roadmap.md` · `docs/progress.md` · `docs/sessions/2026-09-08_master_roadmap.md`.
- Dashboard: chạy lại `scripts/build_progress_data.py` (tái sinh `data/progress_data.json` từ docs).

## Verified facts (read-only DB, 2026-09-08)
- 130 bảng; entity_claims 447,885 (`claim_type`: NAME/COORDINATE/ADMIN_UNIT/TEXT_EVIDENCE/EXTERNAL_ID/NETWORK_EVIDENCE; 0 source_id NULL; 0 confidence NULL, range 0.7–1.0; verification_status toàn 'unverified'; assertion_level/reviewed_by/reviewed_at NULL 100%).
- data_sources 13 · dataset_sources 10 · source_authority 13 (implemented 5/13). 5 active nuôi claims: DILA 293,177 · ZQLOCAL 118,295 · MARCUS 22,332 · CBETA 13,933 · Wikidata 148.
- events 3,530 — KHÔNG có cột provenance.
- lineage_conflicts_v2 40,327 · glossary_term 248,095 (chưa có tiếng Việt) · entity_hub 167,006 · doctrine_concept 12 · pali_cbeta_map 6.

## Acceptance
1. `docs/SCHEMA_DESIGN.md` đủ 7 mục M1–M7 + bảng 3 độ lệch gán task.
2. Số liệu trong docs khớp DB thật (13/5/8 · 130 bảng · 447,885 · 40,327 · 248k).
3. `docs/tasktodo.md` có T108 In_progress→done + T109–T114 PENDING; `docs/roadmap.md` có section Evidence-first.
4. Dashboard mới (sau khi chạy build_progress_data.py) phản ánh T108.
5. Commit docs qua temp-index + hash-fill.
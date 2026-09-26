# 2026-08-30 — T67-T70: TGS Build 1 Acceptance Plan (đã phê chuẩn)

## Mô tả ngắn

Sau khi thực hiện **TGS Build 1 Integration Audit** (read-only) — verdict **🟡 CONDITIONALLY ACCEPTED** —
admin phê chuẩn kế hoạch 4 commit để đóng 2 P0 + P1 và nâng verdict lên 🟢 ACCEPTED.
Phiên này: tạo **4 task files mới (T67-T70)** theo đúng chuẩn Claude Code (YAML frontmatter) + cập nhật
`docs/tasktodo.md` + session log + regenerate `data/progress_data.json` để **Dashboard admin hiển thị**.

## Audit kết quả (tóm tắt bằng chứng — đầy đủ trong session trước)

- **PASS:** DILA canonical (places_pending 176,783 / places_dila 59,167), CBETA textual evidence
  (cbeta_place_mentions 16,311 / person 72,628 / place_person_bibl 13,933 / event_text_link 17,284),
  Wikidata (`geo_cross_ref` 148 QID verified), UI evidence viewing.
- **PARTIAL:** Marcus, FoJin, Evidence Graph (mono-DILA), Cross-reference, Đạo Ảnh HITL.
- **FAIL:** SAT (URL-only), CHGIS (0 chgis_svid), BDRC (1 row, active=0), Authority Ranking (không có).
- **Gap chính (P0):** `entity_hub.status` all 'active' (0 verified); `entity_source_ids.verified` 0/167,008;
  `entity_claims.verification_status` all 'unverified'; `namevi_map_places.source='manual'` = 3 rows;
  save chỉ ghi name_vi → "SQLite editor".
- **removeChild React bug:** thật + đã root-cause (Leaflet chiếm container + Lucide swap icon) + đã fix.
  Không còn path double-remove.

## Quyết định đã chốt (admin phê chuẩn)
1. Triển khai **đủ 4 commit** (T67-T70).
2. `entity_hub.status='verified'` **CHỈ khi admin thực sự duyệt** trong HITL — KHÔNG backfill bulk.
3. CHGIS/BDRC/FoJin/SAT → **khai báo scope minh bạch** (implemented=0, PREPARED/NOT INTEGRATED),
   không import dữ liệu mới trong Build 1.

## 4 Task mới tạo (tasks/T6x-*.md)
- **T67** (`T67-hitl-canonical-decision-provenance.md`) — P0-1: bảng `canonical_decision` + `en_audit_log`;
  nâng cấp `save_mapping`/`auto_save_name` (app.py:7271/:7290) ghi provenance; chuyển entity_hub→verified;
  endpoint GET canonical; React panel.
- **T68** (`T68-source-authority-conflict.md`) — P0-2: bảng `source_authority` (seed matrix) + `conflict_pending`;
  hàm `resolve_canonical()` + conflict detection cho địa danh.
- **T69** (`T69-wire-evidence-entity-claims.md`) — P1: generator idempotent nối CBETA/Marcus/Wikidata
  vào `entity_claims`/`entity_source_ids` (dữ liệu thật, không mock).
- **T70** (`T70-data-governance-cleanup.md`) — P1: khai báo scope nguồn + dọn test rows `place_wiki_snapshots`
  (backup trước, reversible).

## Cập nhật hệ thống
- `docs/tasktodo.md`: header 2026-08-30 + 4 dòng T67-T70 + overview 66→68 tasks + row "Pending (Build 1 acceptance)".
- `data/progress_data.json`: regenerate qua `scripts/build_progress_data.py` để **Task Board Dashboard** hiển thị T67-T70.

## Verify
- `scripts/build_progress_data.py` chạy OK, `data/progress_data.json` chứa 4 task mới (status pending).
- Dashboard `dashboard/dashboard_process.html` hiển thị Task Board đọc từ `data.tasks`.

## Việc tiếp theo
- Bắt đầu **Commit 1 = T67** khi admin chốt (backup DB an toàn server DỪNG → bảng mới → app.py → UI → verify → commit).
- Sau T67 → T68 → T69 → T70, chạy `npm run pipeline` + post observation → nâng verdict Build 1 lên 🟢 ACCEPTED.

## Revert
- Tất cả 4 task chỉ THÊM bảng/logic mới (additive), không sửa schema nguồn; revert bằng backup DB + drop bảng mới.

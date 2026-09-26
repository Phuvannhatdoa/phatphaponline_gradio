---
id: T138
title: "Zen Lineage Render Policy + Edge Assertion Model — đa-nguồn cạnh truyền thừa (L1–L4)"
priority: high
status: done
owner: AI Engineer (build) · Lee Tổng (phán quyết HITL / Approve)
module: Ops / Sources / Governance / Lineage Tree
created: 2026-09-14
updated: 2026-09-14
---
# T138 — Zen Lineage Render Policy + Edge Assertion Model

> **Phase 2 (build)**: mô hình hóa quy tắc vẽ cây đã được thẩm định *"Quy tắc vẽ cây"* (canvas 2026-09-14) thành code — mỗi cạnh truyền thừa là quan hệ chuẩn hóa mang **nhiều source assertion** độc lập, có mức tin cậy **L1–L4**, hiển thị đầy đủ ✓/— nguồn trong inspector. **KHÔNG ingest Zen Lineage** (license BLOCKED — audit T137); model dựng sẵn để mở license + HITL xong là chạy.
> **Policy đã chốt:** ① cây tiếp tục BFS từ `marcus_networks` (grandfather Marcus qua `marcus_people_link` = đã-map-ngầm); ② union filter "Chỉ quan hệ có dẫn chứng" → "Chỉ cạnh L1–L2".

## 1. Context

Phán quyết thẩm định *"Quy tắc vẽ cây"* → 4 gap được chốt giải pháp (xem `docs/.../audit` §11 + diff plan):

| Gap | Vấn đề | Giải pháp chốt |
|---|---|---|
| G1 | "Cùng một quan hệ" chưa normalize được trước khi mapping | map (marcus_people_link / entity_source_ids) → normalize → mới so trùng |
| G2 | Conflict đang node-level, đề xuất nói edge-level | suy edge-level từ `lineage_conflicts_v2` (direction_disagreement => warning) |
| G3 | "Mâu thuẫn → không vẽ" sẽ gãy 40K cây | **giữ show+mark** (minh bạch, đúng T109/T136); chỉ ẩn rejected / L4 |
| G4 | Tier A (CBETA) không phải nguồn edge độc lập | **tái gắn**: `ref` của cạnh Marcus = cột chứng cứ văn bản (L1) |
| G5 | Trùng tên tier A–D với Zen Lineage | đổi thành **trust_level L1–L4** |
| G6 | Gate mapping bất đối xứng | **chốt (a): grandfather Marcus**; admin-duyệt chỉ cho nguồn mới |
| G7 | Bộ lọc hiện tại ≠ tier ("có dẫn chứng" = has_ref = no-op vì 100% Marcus có ref) | re-wire filter-loại sang L1–L2 |

## 2. Thiết kế (0 ALTER — DERIVED-only, additive)

### `lineage_edge_assertions` (bảng DERIVED, `scripts/etl_t138_edge_assertions.py`)
```
id PK, edge_key, subject_person_id, relation_type, object_person_id,
source_code, raw_relation_type, ref, citation_tier, mapping_verified INT DEFAULT 0,
trust_level TEXT (L1..L4), status TEXT DEFAULT 'active', created_at
+ INDEX(subject_person_id, object_person_id, edge_key)
```
- **MARCUS** (11,169 cạnh → person qua `marcus_people_link`): `trust_level=L1` nếu có `ref` / `L2` nếu không; `mapping_verified=1` (grandfather, policy G6a).
- **DILA** (parse `lineage_conflicts_v2.dila_data` JSON, set thầy/trò): `trust_level=L2`.
- **ZENLINEAGE**: **0 rows** (BLOCKED) — schema sẵn sàng, ghi rõ.
- `status='rejected'` khi edge thuộc conflict `resolved=1` + quyết định reject (từ `en_audit_log`/notes).

### API `api_monk_lineage_tree` (app.py)
- Mỗi edge add `sources[]` (source_code · raw_relation_type · ref · mapping_verified · trust_level) + `trust_level = max(assertion levels)` + `status`.
- Giữ BFS, giữ `conflicts[]` node-level, giữ lazy expand, giữ `has_ref` (tương thích UI cũ).

### Render rule (places.html)
- Pháp mạch chuẩn: **L1 + L2**. L3 → tab Phả hệ mở rộng + nét đứt + nhãn "Cần khảo cứu". L4 → không vẽ.
- Conflict `direction_disagreement` → giữ show+mark (viền đỏ + badge) — KHÔNG ẩn.
- Inspector edge: block "Đối chiếu nguồn" — from/to, loại quan hệ, trạng thái (trust level + mapping), ✓/— từng nguồn (MARCUS/DILA/ZENLINEAGE), raw type, ref → link Đại Tạng (giữ `loadLineageCite` hiện có).
- Filter re-wire: `lineage-filter-verified` → "Chỉ cạnh L1–L2 (đã xác nhận)" (ẩn L3 candidate); `lineage-filter-conflict` giữ nguyên.

## 3. Sản phẩm / Files
- [ ] `scripts/etl_t138_edge_assertions.py` (--dry-run/--apply/--revert, Zero-RAM chunk, backup, idempotent).
- [ ] `app.py` — `api_monk_lineage_tree` overlay (sources[], trust_level, status).
- [ ] `places.html` — render rule (L1/L2, L3 dash, show+mark conflict), inspector "Đối chiếu nguồn", filter re-wire.
- [ ] Docs: `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` (§11/§13) · session `docs/sessions/2026-09-14_t138-zen-lineage-render-policy.md` · `docs/tasktodo.md` (T138 ACTIVE) · dashboard regen.

## 4. Verification
- `py_compile` ETL + `--dry-run` in kế hoạch; `--apply` trên DB thật (backup) → đếm assertions MARCUS/DILA.
- SQL offline kiểm tra: mọi edge Marcus trong API có `sources[]` đúng source/trust.
- `node --check` places.html JS; **`npm run pipeline` bắt buộc** trước khi report review.
- Live verify: restart :5000 (chờ admin) → mở Pháp mạch 1 node → inspector hiện ✓ Marcus / — DILA / — Zen Lineage.

## 5. Acceptance
- Bảng `lineage_edge_assertions` tồn tại, counts khớp (MARCUS 11,169 edges → ≥ assertions; DILA từ dila_data; ZEN = 0).
- API edge có `sources[]` + `trust_level`; UI không đổi hành vi cây hiện tại (L1/L2).
- Inspector edge hiển thị đối chiếu nguồn; filter "Chỉ cạnh L1–L2" không đổi hành vi hiện tại.
- pipeline PASSED; docs/task/session/dashboard cập nhật.

## 6. Risks
- 11,169 cạnh Marcus ONE-TO-MANY với assertions (1 edge = 1 assertion MARCUS init) — cần edge_key bền để sau merge DILA/ZEN không đổi.
- DILA set thầy/trò là aggregate (không có ref riêng) → trust L2, không có chứng cứ văn bản att đính trước.
- PowerShell quoting UTF-8 → dùng script file `.py`/`-X utf8`.

## 7. Rollback
- DB DERIVED: `python scripts/etl_t138_edge_assertions.py --revert` (DROP bảng) — 0 động marcus_networks/lineage_conflicts_v2.
- Code additive: revert commit `git revert <sha>`; backup `docs/sessions/app.py.bak-t138-*.py` + `places.html.bak-t138-*.html`.
- **Commit (temp-index policy): `99a8841`** (8 files, +1,799/−449) 2026-09-14. Rollback nhanh: `git revert 99a8841`.
- **Hash-fill: `7b2e4fd`** (docs T138 task file) · **Fix DILA direction-mismatch: `1b63fae`** (phát hiện live-verify — DILA lưu student→teacher ngược chiều Marcus; `_t138_edge_assertions` kiểm tra 2 chiều + `direction_mismatch` flag, không contribute trust; inspector "⚠ DILA — ngược chiều"). Revert toàn T138 theo thứ tự ngược: `git revert 1b63fae` → `git revert 7b2e4fd` → `git revert 99a8841`.
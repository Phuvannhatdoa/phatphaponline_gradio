# Source Integration Architecture — Giai đoạn hoá (T77/T76)

**Cập nhật:** 2026-08-31
**Mục đích:** Thiết kế 2 giai đoạn để TGS trở nên **source-agnostic** (thêm nguồn = đăng ký + adapter,
không sửa core). G1 (Build 3) = registry + adapter skeleton; G2 (Build 4+) = de-lock-in sâu.

## Nguyên tắc (Build hard-rules)

- **Additive + reversible**: không drop cột, không sửa code đang chạy, mọi script có `--undo` + backup.
- **Không rebuild B1**: dùng hạ tầng sẵn có (Identity Hub, Evidence, Authority, API, Đạo Ảnh HITL).
- **DILA = canonical**: external ID chỉ là cross-reference, không bao giờ thành canonical.
- **DO NOT modify architecture merely to make tests pass**: T76 acceptance là read-only; T77 chỉ bổ trợ.

## Hiện trạng (đã verify)

```
DILA PLxxxx ──► entity_hub (canonical 167,006)
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
   entity_source_ids   entity_claims   source_authority   data_sources
   (182,715)           (447,885)       (13 nguồn)          (13 registry, +T77)
        │            (provenance)     (score/order)       (version/license/caps)
        └────────────┴────────────────┴──────────────────┘
                     ▼
        GET /api/places/<id>/claims  (generic — app.py:12227)
                     ▼
        Đạo Ảnh Evidence panel + HITL canonical_decision
```

**Điểm khoá (lock-in) hiện tại:**
1. `entity_unified` (app.py:11498-11594) — 8+ nhánh if/else hardcode per-source.
2. `_name_vi_evidence` (app.py:7613) — hardcode literal `'ZQLOCAL'`/`'DILA'`.
3. Per-source route clones (app.py:3965, 11248, 12014, 12084, 12125, 12180).
4. Source-named columns: `entity.dila_id/marcus_id`, `geo_cross_ref.wikidata_qid/chgis_svid/...`.

## Giai đoạn 1 (Build 3 — đã làm trong T77): additive, không đụng core

| Việc | File | Kết quả |
|---|---|---|
| Registry metadata mở rộng | `scripts/build3_source_registry_extend.py` | +13 cột `data_sources` (version, last_sync, enabled, capabilities, license...) |
| Adapter contract | `adapters/base.py` | `SourceAdapter` + `ExtractedEvidence` (provenance chuẩn) |
| Adapter registry (data-driven) | `adapters/registry.py` | nạp/load/dispatch theo `data_sources.capabilities` |
| Adapter mẫu | `adapters/bdrc/__init__.py` | ví dụ contract (BDRC, connector_only) |

**Kết quả G1:** "thêm nguồn" = thêm dòng `data_sources` + cung cấp adapter → source mới tự hiện
qua `/api/places/<id>/claims` + Đạo Ảnh (endpoint/UI đã generic) mà **không sửa core**.

## Giai đoạn 2 (Build 4+ — để lại, chưa làm)

- De-lock-in `entity_unified` → vòng lặp generic + `source_ref_lookup` config.
- Thay literal `'ZQLOCAL'/'DILA'` trong `_name_vi_evidence` bằng cột `can_vote_name_vi` (data-driven).
- `geo_cross_ref` (7 cột source-named) → bảng `entity_external_ref` generic (additive, giữ bảng cũ).
- Gộp routes clone per-source.
- Wrap harvester hiện có (dila/marcus/cbeta) vào `SourceAdapter` contract.
- UI Đạo Ảnh: nút "đăng ký nguồn mới".
- Skeletons `TEST_TRUSTED_SOURCE_X` (demo future-source, tùy chọn, KHÔNG trong acceptance).

## Quyết định đã chốt

1. **Tách 2 giai đoạn** — G1 bây giờ (an toàn), G2 Build 4+.
2. **Phương án b** — KHÔNG tái cấu trúc `entity_unified` hôm nay (để lại G2); chỉ registry + adapter.
3. **3 file doc gộp** — tránh duplicate.
4. **T76 trước, T77 sau** — cô lập checksum before/after.

## Verdict

`READY FOR FUTURE SOURCE INTEGRATION` — sau T76 (acceptance trung thực: PARTIAL) + T77 (registry+adapter).
Hoàn thiện matching/provenance + de-lock-in sâu = Build 4+.

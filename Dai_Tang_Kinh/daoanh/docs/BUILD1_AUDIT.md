# Build 1 Audit — Gap Map cho Source Integration (T77)

**Cập nhật:** 2026-08-31
**Nguồn gốc:** mở rộng/complement `docs/build1_inventory.md` (KHÔNG thay thế, KHÔNG duplicate).
**Mục đích:** Đánh giá mức "Future-source-ready" của từng component Build 1 — nguồn mới gia nhập TGS
cần **reuse / modify / gap** gì. Từ cơ sở này mới tối ưu hoá "READY FOR FUTURE SOURCE INTEGRATION".

> Rule: chỉ ghi component đã verify (theo build1_inventory + audit thực tế app.py/DB). Không bịa.

## Bảng Gap map (Build 1 → Future-source-ready)

| Component (B1) | Vị trí | B1 status | Reuse? | Modification required? | Future-source-ready | Ghi chú |
|---|---|---|---|---|---|---|
| Canonical Entity (Identity Hub) | `entity_hub` (167,006) + `entity` | IMPLEMENTED (T23) | ✅ reuse | ❌ không cần | ✅ YES | entity_id INT surrogate, không phụ thuộc source |
| Source Identity Mapping | `entity_source_ids` (182,715) | IMPLEMENTED (T23+B2-B) | ✅ reuse | ❌ không cần | ✅ YES | 1 entity → nhiều source, match_status/confidence |
| Evidence | `entity_claims` (447,885) | IMPLEMENTED (T69+B2-B) | ✅ reuse | ⚠️ 1 phần | ⚠️ PARTIAL | provenance đủ (CBETA/MARCUS/Wikidata), DILA/ZQLOCAL thiếu retrieved/ref |
| Authority matrix | `source_authority` (13) | DONE (T68+B2-D) | ✅ reuse | ❌ không cần | ✅ YES | data-driven score/order/implemented |
| Source Registry | `data_sources` (13) | DONE (B2-D) | ✅ reuse | ⚠️ đã mở rộng T77 | ✅ YES | +13 cột metadata (version/license/capabilities) |
| Conflict detection | `conflict_pending` + `_detect_conflicts()` | DONE (T68) | ✅ reuse | ⚠️ chờ data | ⚠️ PARTIAL | 0 case thật hiện tại |
| Cross-geo reference | `geo_cross_ref` (181) | IMPLEMENTED (B1) | ⚠️ hạn chế | ⚠️ cần mở rộng | ⚠️ PARTIAL | chỉ 181 rows — mỏng |
| Same-name matcher | `name_vi_map_places` (0) + `name_normalization` (17) | THIN | ❌ thiếu | 🔴 GAP | ❌ NO | không đủ dữ liệu phân biệt same-name/diff-loc |
| Evidence API endpoint | `GET /daoanh/api/places/<id>/claims` (app.py:12227) | DONE (B2-C) | ✅ reuse | ❌ không cần | ✅ YES | generic — nguồn mới tự hiện |
| Evidence UI panel (Đạo Ảnh) | `admin/placevn.html` evidence panel | DONE (B2-C) | ✅ reuse | ❌ không cần | ✅ YES | render claim generic theo source |
| HITL canonical decision | `canonical_decision` + `en_audit_log` | IMPLEMENTED (T67) | ✅ reuse | ❌ không cần | ✅ YES | ghi đầy đủ provenance |
| Adapter layer | `adapters/` | THIN (BDRC stub) | 🔴 GAP | 🔴 cần skeleton | 🔴 GAP | T77 tạo `base.py`+`registry.py`+BDRC demo |
| Harvester ingest | `scripts/*harvester*` | DILA/CBETA/MARCUS/ZQLOCAL/Wikidata | ✅ reuse | ⚠️ wrap về sau | ⚠️ PARTIAL | chưa wrap vào contract (B3 GĐ2) |

## Bảng Gap theo § của Source Integration Masterplan

| § | Yêu cầu | B1 hiện trạng | Verdict |
|---|---|---|---|
| §IV Adapter contract | source adapter chuẩn hoá | chỉ stub BDRC | **GAP** → T77 `adapters/base.py`+`registry.py` |
| §V Versioning nguồn | theo dõi version source/adapter | `source_authority` không có version | **DONE** (T77 add cột `data_sources`) |
| §VII Canonical id firewall | external không thành canonical | 0 external→canonical (verified) | ✅ PASS |
| §IX Data-driven voting | không hardcode literal source | `_name_vi_evidence` hardcode 'ZQLOCAL'/'DILA' | ⚠️ PARTIAL (để lại B3) |
| §XI License firewall | license/redistribution/commercial | có `license_note`; thiếu cột tách | **DONE** (T77 add 3 cột) |
| §XIII Capability discovery | tự phát hành theo capability | thiếu | **DONE** (T77 add `capabilities`) |
| §XVI Docs | tài liệu tích hợp | thiếu | **DONE** (T77: 3 doc gộp) |

## Kết luận audit

- **Hạ tầng lõi (Identity/Evidence/Authority/API/UI/HITL):** đã generic, future-source-ready ✅ — nguồn mới chủ yếu cần **đăng ký + adapter**, không sửa core.
- **Gap thật:** (1) adapter contract — T77 đã tạo skeleton; (2) matching same-name/diff-loc — thiếu data, để B3; (3) provenance DILA/ZQLOCAL — B3.
- **Verdict:** `READY FOR FUTURE SOURCE INTEGRATION` (sau T76/T77) — với lưu ý matching/provenance hoàn thiện ở Build 3.

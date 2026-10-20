# ⛔ BẢN DỰNG LẠI ĐỂ ĐỐI CHIẾU — KHÔNG PHẢI PLAN ĐANG CHẠY

> **Tệp này KHÔNG còn hiệu lực.** Đây là **bản tái dựng nguyên văn** từ file
> `docs/Mimo-Flash/T181-geo-spatial-timeline-founding-phase2.md` bị xoá trong phiên
> 2026-10-04 (file đó **chưa bao giờ được commit** ⇒ không khôi phục được bằng git).
> Nội dung bên dưới giữ **đúng như bản gốc**, kể cả phần **sai** — mục đích là để
> đối chiếu chứ không phải để thực thi.
>
> **Bản chạy thật:** `docs/Mimo-Flash/T224-geo-spatial-timeline-founding-phase2.md`
> (`id: T224`, `former_id: T181`).
>
> **3 lý do bản gốc bị bác** (chi tiết ở T224):
> 1. **ID trùng hoàn toàn** — `T181` đã thuộc task CBETA Bulk Import
>    (`tasks/T181-cbeta-bulk-import-lazy-translate.md`, `in_progress`).
> 2. **3 tài liệu nguồn không tồn tại** — `GEO_SPATIAL_TIMELINE_SPEC.md` ("APPROVED"),
>    `PROMPT-T181-source-reuse-audit.txt`, "số liệu SPEC §4" ⇒ tiêu chí phân loại
>    **nằm trong prompt** mà prompt không có.
> 3. **Nhóm B degenerate** — `raw_xml` khác rỗng 100% ⇒ B = 59.167, D = E = 0.
>
> **Tên file cố tình đổi thành `X-…`** theo quy ước superseded của repo, để lần
> `dup:ids` sau **không** nhặt lại ID `T181` — chính xung đột này đã gây bug.

---

<details>
<summary>Nội dung bản gốc (nguyên văn, 51 dòng) — bấm để mở</summary>

# T181 — Geo-Spatial & Timeline Integration (Founding Date Phase 2)

**Status:** 🟡 PENDING (2026-09-29 Admin "Đồng ý build" — tạo task)
**Spec:** `docs/GEO_SPATIAL_TIMELINE_SPEC.md` (APPROVED, kèm 5 fix review)
**Prompt chờ Admin paste:** `docs/Mimo-Flash/PROMPT-T181-source-reuse-audit.txt`
**Lane:** Audit G1–G2 = Claude Code (read-only) · docs/logs = mimo-flash · G3+ code = Claude Code sau Lee Tổng duyệt

## Mục tiêu

Thực thi Layer 1–3 của SPEC: **Source Reuse Audit** phân loại 59,167 DILA Places thành
5 nhóm (A–E) để xác định đúng khối lượng việc Residual Gap (NLP) thay vì cào đại trà —
đóng góp lớp Không gian–Thời gian cho bức tranh tích hợp (bên cạnh Phả hệ + Đại tạng).

## Scope

- **G0 — Baseline:** đo số liệu thật (SPEC §4) — SSOT `data/lineage.db` RO `?mode=ro`.
- **G1 — Source Reuse Audit (READ-ONLY, 0 mutation):** phân loại từng place:
  - **(A)** Đã có structured event data (`place_timeline_events` sẵn — 3.688 rows).
  - **(B)** Có TEI/XML marked-up evidence trong `raw_xml`/`note` (Layer 2 — regex/annotation).
  - **(C)** Cross-source reusable qua `geo_cross_ref` (QID/CHGIS/TGAZ/BGIS/BDRC — gated T112).
  - **(D)** Raw text cần NLP (Residual Gap) — đầu vào cho T22 + mở rộng regex.
  - **(E)** Không có evidence.
- **G2 — Report:** `docs/T181_SOURCE_REUSE_AUDIT_PLAN.md` + `docs/T181_IDENTITY_HUB_PLAN.md`
  + `docs/T181_EVIDENCE_EVENT_MODEL.md` → báo Lee Tổng **trước** mọi code.
- **G3+ (CHƯA MỞ — chờ duyệt):** ETL additive (DERIVED `place_timeline_evidence`),
  HITL queue (pattern bio-review/zenlineage_review), coverage target.

## Ràng buộc (từ SPEC)

0 mass NLP · 0 ALTER bảng base (T82 freeze) · 0 ghi đè `raw_xml`/`note` ·
nguồn `implemented=0` (CHGIS/TGAZ/BDCR/Wikidata…) chỉ cross-ref ·
mọi row NLP = `confidence='candidate'` · mọi script additive/idempotent/`--revert`.

## Dependencies

- T22.1 (✅ DONE) — audit reuse nền, **không làm lại**.
- T22 (🔨 in_progress) — NLP Fosi Zhi = nguồn việc Layer 5.
- T121 (🟡 PENDING) — Wikidata lat/lon enrichment, tránh làm trùng Layer 3.
- T112 (🚫 BLOCK) — license CHGIS/TGAZ.

## Acceptance (G1–G2)

1. Report A–E đủ 59.167 rows, tổng A+B+C+D+E = 59.167, số liệu đệm khớp SPEC §4.
2. 0 write DB (audit read-only — verify bằng query log/0 mutation).
3. Residual workload (nhóm D) ước lượng thời gian/token → Lee Tổng duyệt trước G3.
4. 3 file plan đúng tên `docs/T181_*.md` (KHÔNG dùng tên T120_* — ID đã cấp khác).

## Revert

- Docs: `git revert --no-edit <sha_đóng_row_này>` (xem `docs/ROLLBACK.md`).
- G3 (tương lai): script `--revert` + DB backup pattern T157.

</details>
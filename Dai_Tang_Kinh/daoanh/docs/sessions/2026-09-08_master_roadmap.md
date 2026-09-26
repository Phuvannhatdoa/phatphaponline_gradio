# Session — 2026-09-08 · Master Roadmap (T108 Evidence-first) + T108 Schema Design

**Kiểu phiên:** Phê duyệt lộ trình · Docs-only build (T108).
**Người phê chuẩn:** Lee Tổng (admin).
**Commit:** `456809d` (docs T108) — hash-fill: `git revert --no-edit 456809d`.

## 1. Bối cảnh
- Lee Tổng trình "Master Roadmap" tự nhận "Chuẩn hóa & Tái cấu trúc" (không tích hợp nguồn mới), đánh số T01–T07.
- **Kiểm chứng read-only DB (2026-09-08):** tìm **5 lỗi** trong bản roadmap đề xuất:
  1. "25 nguồn" → thực tế **13 đăng ký / 5 active / 8 pending** (`data_sources`=13 · `dataset_sources`=10 · `source_authority`=13).
  2. "50+ bảng" → **130 bảng**.
  3. T01–T07 **đều trùng** task hiện hữu (T01-seed-monk-persons … T07-wikipedia-fallback) → đổi số **T108–T114**.
  4. 4/7 mục roadmap **đã tồn tại** (entity_claims=assertion store · source_authority=matrix · _resolve_entity_id/T77=adapter — chính T100=3 cấp độ).
  5. **Gap thật:** conflicts 40,327 chưa có workflow · review state 0% điền · events 3,530 không provenance · glossary_term 248k chưa Việt · persona display chưa có · :5000 bị blocked.
- Lee Tổng chốt 3 lựa chọn: (1) số T108–T114, (2) không tạo MASTER_ROADMAP.md — cập nhật docs hiện có, (3) số liệu chuẩn 13/5/8.
- Phê chuẩn giải pháp tối ưu: **Audit ID content-hash thay UUID** · T108 docs trước · từng task 1 batch-code riêng sau.

## 2. Kết quả verified (read-only DB, cột mốc số liệu cho mọi docs sau này)
- `entity_claims` 447,885 · `claim_type` 6 loại · **0 source_id NULL · 0 confidence NULL** (range 0.7–1.0) · `verification_status` toàn `'unverified'` · `assertion_level`/`reviewed_by`/`reviewed_at` **NULL 100%**.
- `data_sources` 13 · `dataset_sources` 10 · `source_authority` 13. 5 active: **DILA 293,177 · ZQLOCAL 118,295 · MARCUS 22,332 · CBETA 13,933 · Wikidata 148**. 8 pending (implemented=0): SAT, CHGIS, BDRC, FoJin, Kanripo, TGAZ, SuttaCentral, 84000.
- `events` 3,530 — **không có cột provenance nào** (PRAGMA xác nhận).
- `entity_hub` 167,006 · `lineage_conflicts_v2` 40,327 · `glossary_term` 248,095 (no VI col) · `doctrine_concept` 12 · `pali_cbeta_map` 6 · `name_vi_map` 51,141 · namevi_map_places 118,296.

## 3. Quyết định thiết kế T108
1. **Audit ID content-hash (thay UUID):** `audit_id = SHA-256(entity_id|claim_type|predicate|object_text|source_id)` — deterministic + idempotent (re-ETL ra cùng giá trị → "10 năm sau truy vấn lại"), không migration 447k, PK `claim_id` Integer giữ nguyên, tiền lệ `text_passages`.
2. **Persona lock/open:** L1 Cử nhân (drawer đóng) · L2 Cao học (+badges) · L3 Tiến sĩ (provenance đầy đủ + conflicts) — API `?level=L1|L2|L3` (implement T111).
3. **events provenance** (additive + backfill best-effort) + **conflict workflow** gộp vào T109.
4. **Compliance metrics 7 chỉ số** (M7.2) — script ship ở T113 → `data/design_compliance.json` cho Dashboard.

## 4. Deliverables phiên này
- `docs/SCHEMA_DESIGN.md` (T108, mới, 7 mục M1–M7).
- `tasks/T108-schema-design.md` + `tasks/T109-provenance-conflict-workflow.md` + `tasks/T110-glossary-vietnamese-pipeline.md` + `tasks/T111-persona-display-disclaimer.md` + `tasks/T112-source-pending-activation.md` + `tasks/T113-qa-uat-compliance-meter.md` + `tasks/T114-roadmap-meta-update.md` (7 mới).
- Cập nhật: `docs/tasktodo.md` (T108 In_progress/Done + T109–T114 PENDING + số liệu chuẩn Context) · `docs/roadmap.md` (section Evidence-first, 13/5/8 · 130 bảng) · `docs/progress.md` (entry T108).
- Chạy `python scripts/build_progress_data.py` → cập nhật Dashboard (`data/progress_data.json`).

## 5. Sự cố môi trường
- **Sync agent volume `E:\Backup 2025` revert working tree:** roadmap.md 2120→31 dòng ngay khi đang sửa → khôi phục **byte-perfect** từ HEAD blob (`1ce6534...`) + append lại; xác minh SHA-1 từng phần (original portion rehash == HEAD blob `True`).
- Nhắc lại: mọi commit phải qua temp-index (index thật agent-polluted); file thay đổi cần verify lại trước commit vì sync agent có thể clobber.

## 6. Tiếp theo
1. Lee Tổng duyệt nội dung SCHEMA_DESIGN.md (thảo luận full nếu cần).
2. Commit docs T108 (temp-index + hash-fill).
3. **T109 (batch code):** events provenance + audit_id backfill + conflict workflow admin → ETL additive + backup + `npm run pipeline` trước review.
4. Theo lộ trình T110 → T111 → T112 → T113 → T114.

## 7. Round 2 — Phê chuẩn ánh xạ bản vẽ Admin (T01–T07 → T108–T114)

**Kiểu phiên:** Bổ sung docs (đã có T108) — "dùng Txx thay cho T01, T02 (name cũ)".
**Commit:** `613ad66` (mapping) — Revert: `git revert --no-edit 613ad66`. Chi tiết SCHEMA_DESIGN.md **Phụ lục A**.

- Lee Tổng review bảng "Master Roadmap" (T01–T07 + spec SCHEMA_DESIGN) và chốt: **chỉ thảo luận làm sáng tỏ vấn đề — KHÔNG xác nhận thao tác thay đổi cấu trúc DB local**; sau đó phê chuẩn "dùng Txx thay T01/T02 cũ", cập nhật docs/dashboard.
- **Kết luận kiểm chứng (read-only):** bản vẽ logic ĐÚNG, khớp SCHEMA_DESIGN.md đã tồn tại; 4 điểm chỉnh:
  1. "25 sources" → **13/5/8**.
  2. T01–T07 trùng task cũ → dùng **T108–T114** (mapping chính thức tại Phụ lục A).
  3. T03 "map lineage.db về Schema mới" → **KHÔNG remap** — adapter additive (T77) + audit_id/source_id additive (T109).
  4. "SQL/NoSQL" → **SQLite** concretely.
- **Trả lời yêu cầu "cơ chế đánh chỉ mục entity_id":** `entity_claims` **ĐÃ có** `ix_entity_claims_entity_source(entity_id, source_id, claim_type)` (PRAGMA verify) — không cần tạo index mới; `entity_hub` không index phụ → bổ sung tính vào T109 nếu cần (chưa làm vội).
- Đã cập nhật: `SCHEMA_DESIGN.md` (Phụ lục A) · `tasktodo.md` (tên cũ trong ngoặc) · `roadmap.md` (dòng mapping) · `data/progress_data.json` (dashboard). 0 DB, 0 code.
- **Sự cố môi trường (verify):** worktree sync agent đổi CRLF↔LF giữa chừng → so sánh sha1 raw không hợp lệ; xác minh chính thức bằng `git hash-object` + byte-level `git show` (script UTF-8) → **4 blob committed khớp worktree, nội dung Phụ lục A nguyên vẹn trong commit**. Lưu ý kiểm chứng sau này: luôn dùng `git hash-object` (CRLF/LF-clean), không so sha1 raw file.
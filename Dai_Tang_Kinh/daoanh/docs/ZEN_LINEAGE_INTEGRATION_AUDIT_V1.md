# Zen Lineage Integration Audit — V1

> **Repo:** github.com/echojoel/zenlineage · Website: zenlineage.org/lineage
> **Commit khóa:** `ec8357eda153ba442ef86f360299f23f01e5c8ce` (master, 2026-08-17, "fix(deploy): load the API token…", chữ ký không verify)
> **Audit date:** 2026-09-14 · **Mode:** AUDIT-ONLY (read-only, 0 import, 0 alter production)
> **Verdict:** **CONDITIONAL GO** — hợp lệ làm nguồn đối chiếu; import production **BLOCKED** đến khi license được xác minh.

---

## 1. Mục đích

Admin đề xuất tích hợp Zen Lineage làm nguồn **đối chiếu Pháp mạch độc lập** (thày→trò) cho Đạo Ảnh. Docs này là kết quả **audit thật** (chạy reseed toàn bộ data của repo tại commit khóa) nhằm trả lời 7 câu hỏi: nguồn có bao nhiêu data · schema có đúng như plan mô tả hay không · citation có ở cấp relation không · có ID bền/ khóa ngoài không · overlapping với Đạo Ảnh bao nhiêu · dữ liệu nằm ở đâu · import được hay chưa về mặt pháp lý.

## 2. Phương pháp (read-only, tái dựng được)

1. Clone nông + checkout commit khóa `ec8357eda…` vào thư mục tạm bên ngoài production tree (`%TEMP%\opencode\zenlineage_t137`).
2. `npm install` (885 packages) → `drizzle-kit migrate` (8 migrations `drizzle/0000…0007`).
3. Chạy **data-seed chain** (`seed-db` + `seed-korean-vietnamese` + `seed-maezumi-lineage` + `seed-sanbo-zen-lineage` + `seed-temples` + `seed-deshimaru-lineage` + 10 wave corrections + cjkv names + biographies + `audit-transmissions` + `audit-soto-lineage` + `seed-transmission-evidence` + schools practices + native names). **Bỏ 3 script network/image** (`fetch-kv-images`, `fetch-temple-images`, `generate-thumbnails`) — không ảnh hưởng data lineage.
4. Đếm số liệu bằng SQL trực tiếp trên `zen.db` (35 tables). Idempotent: `zen.db` ephemeral, seed = truth (CLAUDE.md) → tái dựng nguyên trạng mọi lúc.

## 3. Dữ liệu dàn xếp ở đâu

- **DB**: SQLite libSQL/Drizzle, `src/db/schema.ts` (verified qua `drizzle.config.ts`). `zen.db` là **ephemeral** — seeded từ TypeScript (`scripts/seed-*.ts`) trên Cloudflare Pages (`@opennextjs/cloudflare`), seed data là truth.
- **Data files**: `scripts/data/` — `korean-vietnamese-masters.ts` (85KB) · `maezumi-lineage.ts` (44KB) · `sanbo-zen-lineage.ts` (34KB) · `deshimaru-lineage.ts` (103KB) · `canonical-soto-lineage.ts` (31KB) · `aliases.json` · `reconciled/` · `raw/` · `transmission-evidence/` · `reviews/`.
- **Export tĩnh**: `public/data/graph.json` (sinh bởi `scripts/generate-static-data.ts`) — có thể dùng để đối chiếu nếu không muốn chạy seed.

## 4. Schema (verify schema thật, 35 tables)

Tables chính (verified `src/db/schema.ts` + `drizzle/*.sql`): `masters` (id PK, **slug unique**, birth/death year+precision+confidence, ordination, school_id, generation, living, published) · `master_names` (locale, name_type dharma/birth/honorific/alias) · `master_transmissions` (**teacher_id + student_id**, type, is_primary, notes) · `transmission_evidence` (transmission_id, **tier A/B/C/D**, verified_at, human_review_needed) · `transmission_sources` (publisher, url, domain_class, quote, retrieved_on) · `sources` (type, title, author, url, reliability) · `citations` (source_id, entity_type, entity_id, field_name, excerpt, page_or_section) · `schools`/`school_names` · `temples`/`temple_names` · `master_temples` · `master_biographies` · `search_tokens` · `assertions`+`assertion_citations` (0 rows) · `review_status` (0) · `audit_log` (0) · `events`+`event_*` (0) · `ingestion_runs` (1) · `source_snapshots` (0) · `media_assets` (0) · tables teaching/temple/theme.

**Lưu ý dev quy chiếu**: `assertions`, `events`, `temples` mapping thiếu file seed ở head repo → nhiều bảng phụ = 0 rows nhưng KHÔNG ảnh hưởng truyền thừa.

## 5. Số liệu thật (zen.db sau reseed @ ec8357ed)

| Chỉ số | README | **Đo thật** | Ghi chú |
|---|---|---|---|
| Masters | 556 | **556** | 100% published |
| Schools | 25 | **25** | + school_names 52 |
| Transmissions (relations) | 578 | **578** | master_transmissions |
| Temples / practice places | 1,657 | **1,699** temples (+1,845 names) | |
| Citations | ~6,800 | **8,684** | citations |
| Search tokens | — | 4,719 | |
| Sources | — | 206 | reliability: authoritative 62 · primary 61 · scholarly 54 · secondary 19 · popular 6 · editorial 4 |
| Master names | — | 1,842 | locale: en 1,305 · zh 293 · ja 177 · **vi 17** · ko 17 · sa 9 · fr 9 · … |

## 6. Citation ở cấp relation — **YES (mạnh)**

- **100% relation có evidence row**: `transmission_evidence` = **578/578** → tier A 194 · B 342 · C 25 · D 17; `human_review_needed` **41**.
- **Citation cấp relation**: `transmission_sources` **1,659** (domain_class: reference 779 · sangha 308 · institutional 278 · academic 193 · community 95 · unknown 6) + `citations` entity_type `master_transmission` **1,195** → **576/578** relation có citation (99.7%).
- **Hệ quả cho plan**: quy tắc "chỉ `structured_lineage_claim` + `needs_review` khi không có citation cấp relation" sẽ áp cho **≈ 0 edge** của nguồn này (evidence luôn có). Không hiển thị `needs_review` tự động khi nguồn vốn có evidence — chỉ khi nguồn trái ngược.

## 7. Relation semantics (đính chính plan "edge vô nghĩa")

- `master_transmissions` là directional teacher→student: `teacher_id` + `student_id` + `type` + `is_primary` + `notes`. **KHÔNG phải edge không có type**. Không đối nghịch với controlled vocab Đạo Ảnh (teacher_of/disciple_of/...): chỉ map nhẹ khi ngữ nghĩa rõ, giữ raw JSON.
- Phân bố type: **primary 508 · secondary 42 · dharma 19 · disputed 9**; `is_primary` 511/67.

## 8. IDs — Stable có, external không

- **Stable IDs YES**: `masters.slug` unique (vd `vinitaruci`, `vo-ngon-thong`, `tran-nhan-tong`) + `masters.id` (nanoid).
- **External IDs (DILA/BDRC/Marcus) KHÔNG có cột nào** → exact-match bằng strong ID ≈ rỗng. Mọi mapping (nếu có) đi qua **candidate discovery** — 3 mức của plan: exact (slug/trùng tên) → review candidate → no-match, đều dùng số liệu trong §9 hoặc chờ HITL.

## 9. Overlapping với Đạo Ảnh (thực nghiệm, lineage.db)

- **Thiền-số liệu Việt**: 18 masters trường phái **Thiền** (thien 8 · truc-lam 5 · lam-te 4 · plum-village 1) trong 556; 17 masters có name locale `vi` (Tì-ni-đa-lưu-chi, Vô Ngôn Thông, Trần Nhân Tông, Pháp Loa, Huyền Quang, Thích Thanh Từ, Thích Nhất Hạnh, Liễu Quán, Khuông Việt, Vạn Hạnh, Huệ Trung, Nguyễn Thiều…).
- **Đối chiếu `people.name_vi` (DILA 48k)**: hầu hết **NO_MATCH**; các trùng tên là **homonym khác** (vd Huyền Quang A012070 = Tân La Huyền Quang ≠ Huyền Quang Trúc Lâm; Liễu Quán A008234 柳貫 ≠ Liễu Quán Pháp mạch Trúc Lâm).
- **Đối chiếu `marcus_networks`/`marcus_reference`**: **không** chứa các thiền sư Việt này.
- **Kết luận**: nguồn **độc lập thật sự**, overlap chỉ tên nổi tiếng → **không đặt kỳ vọng exact-match**; giá trị nằm ở candidate-discovery + đối chiếu chéo evidence.

## 10. License & gating (locked 2026-09-14)

- **GitHub license = null · `LICENSE` 404 · README chỉ lời văn "open source / public domain & openly licensed"** → **license NOT VERIFIED**.
- Ảnh Wikimedia có license riêng (không ảnh hưởng data lineage).
- Nhánh dùng được NGAY: **link-out tham khảo / candidate-discovery nội bộ** (0 data ingest).
- Import production **BLOCKED** đến khi: (a) chủ repo trả lời license, hoặc (b) admin chọn internal-only.
- Đăng ký nguồn trong `data_sources` (đúng Source Registry T131/T132): **`integration_mode='BLOCKED'` · `legal_status='AUDITING'`**, license_verified=0.

## 11. Usage model + render policy (locked 2026-09-14, T137 audit + T138 build)

| Stage | Hành động | Data | Gate |
|---|---|---|---|
| M1 | Link-out tham khảo (khi hiển thị Pháp mạch: nút "Đối chiếu Zen Lineage ↗") | 0 ingest | Không cần license |
| M2 | Staging `source_staging` schema (0 ALTER production) | slug + master + transmissions + evidence | License OK hoặc internal-only |
| M3 | Candidate matching → `entity_source_ids` (source='ZenLineage', source_entity_id=slug, match_status='candidate', confidence, verified=0) | M2 data | HITL review |
| M4 | HITL approve → đối chiếu hiển thị "Zen Lineage" chip trong inspector | verified=1 | Lee Tổng |

**Render policy (T138 — đã build):**
- Mỗi cạnh truyền thừa = quan hệ chuẩn hóa + **nhiều source assertion** độc lập, lưu DERIVED bảng `lineage_edge_assertions` (0 ALTER). Trust_level **L1–L4** (L1=văn bản+structured, L2=structured verified, L3=candidate, L4=suy đoán).
- **Policy G6(a) grandfather Marcus:** cạnh Marcus (qua `marcus_people_link`) = `mapping_verified=1`, `trust_level=L1` (100% có ref CBETA).=admin-duyệt chỉ bắt buộc cho nguồn mới (Zen Lineage).
- Pháp mạch chuẩn = **L1+L2** · Phả hệ mở rộng = **L3** (nét đứt, "Cần khảo cứu") · **L4 không vẽ**.
- **Conflict (direction_disagreement): giữ show+mark** (viền đỏ+badge+filter) — KHÔNG ẩn (minh bạch, đúng T109/T136). Rejected edges bị ẩn khỏi Pháp mạch chuẩn.
- Inspector "Đối chiếu nguồn": ✓/— MARCUS/DILA/ZENLINEAGE + raw_type + trust_level + ref → link Đại Tạng.
- Filter "Chỉ cạnh L1–L2 (đã xác nhận)" = ẩn L3 candidate.
- **DILA direction (phát hiện T138 live-verify):** DILA lưu assertion **ngược chiều** so với Marcus (student→teacher; 22,326 DILA trùng cặp Marcus đều **reversed**, 0 same-direction). → `_t138_edge_assertions` kiểm tra **hai chiều**; assertion reversed được gắn `direction_mismatch=true`, KHÔNG contribute vào trust_level (là conflict, không phải confirmation), inspector hiển thị "⚠ DILA — ngược chiều". => L2 từ DILA hiện không xuất hiện trên cạnh Marcus (DILA luôn contest, không corroborate) — bản chất dữ liệu, không phải bug UI.
- Zen Lineage = **BLOCKED** (license chưa xác minh) → schema DERIVED sẵn sàng, 0 rows. Khi license mở + HITL mapping approved → thêm assertion + render tự nhiên.
- Hook có sẵn: `entity_source_ids` (source_entity_id=slug) · `data_sources` (license/blocked) · `lineage_conflicts_v2` (show+mark).

## 12. Verdict & điều chỉnh so với plan gốc

| # | Plan gốc | Audit thật | Điều chỉnh |
|---|---|---|---|
| 1 | "License OK mặc định" | **NOT VERIFIED** (không LICENSE file) | **BLOCK import**; ghi rõ gating |
| 2 | "Edge vô nghĩa không citation" | directional teacher→student + type + `is_primary` | Giữ vocab nguồn, map nhẹ khi ngữ nghĩa rõ |
| 3 | "Không citation cấp relation" | **YES — 1,659 sources + 1,195 citations / 578 relations (99.7%)** | `needs_review` chỉ cho edge KHÔNG evidence (≈0) |
| 4 | "Exact-match qua external ID" | Không có external ID | Chuyển candidate-discovery |
| 5 | "Data tại docs/VPS-Task/…" | Không tồn tại folder đó; doc đặt `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` | Thực thi ĐÃ theo quyết định |
| 6 | "556 masters đều liên quan VN" | 18/556 Thiền · 17 name vi | Scope đối chiếu VN nhỏ, có chủ đích |
| 7 | Audit conjecture rỗng | **Số liệu thật từ reseed full** | Dùng §5–§9 |

## 13. Quyết định admin cần đưa trước Phase 2

1. **Hướng license**: hỏi chủ repo (issue/license) · link-out thuần · hay internal-only? (Mặc định: BLOCKED, audit-only — **đã chọn**, chờ approve doc này làm go-live audit.)
2. **Phạm vi đối chiếu**: 18 masters Thiền VN trước hay 556 toàn bộ (candidate-discovery chạy toàn bộ, hiển thị lọc VN)?
3. **UI Phase 2**: chip "Zen Lineage" trong inspector + nút "Đối chiếu ↗" + trust_level badge L1–L4 — **đã xây trong T138** (license BLOCKED → chip ghi "chưa ingest"). Khi license mở → transfer M3/M4.

## 14. T139 Gateway — trạng thái staging (build 2026-09-15)

**Phase 0 — Đăng ký nguồn (ĐÃ XONG, idempotent):**
- `data_sources` **source_id=14** `ZENLINEAGE`: `integration_mode='BLOCKED'` · `legal_status='AUDITING'` · `license_verified=0` · `source_version='ec8357ed'` (ghi qua endpoint `/daoanh/api/admin/source-add`).
- `source_authority`: `ZENLINEAGE` **score=50 · precedence_order=13 · implemented=0** (chỉ active sau license OK + HITL).
- `en_audit_log`: 2 dòng `source_add` + `source_authority_add`.

**Phase 2 — ETL Staging Gateway (`scripts/etl_zenlineage_stage.py`):**
- `--dry-run` (PASS 2026-09-15): nguồn kênh đầy đủ `zen.db` @ ec8357ed → **556 masters / 578 transmissions / 25 schools / 8,684 citations / 206 sources — 5/5 khớp audit**. `--apply` hiện **BỊ CHẶN** vì `integration_mode=BLOCKED` (license gate = SSOT đọc từ `data_sources`, không hardcode).
- `--apply` (khi license mở): backup → CREATE `source_staging` (DERIVED, PK source_code|row_type|source_entity_id, INSERT OR REPLACE) → backfill 556 masters + 578 transmissions (có tier A194/B342/C25/D17 + human_review_needed) → ghi `entity_source_ids` candidate (verified=0, entity_id=NULL).
- `--revert`: DROP `source_staging` + xóa entity_source_ids source=ZENLINEAGE verified=0.
- Zero-RAM (fetchmany chunk) · 0 ALTER base · staged SQL verified trên DB-in-memory (556/578, tier khớp §5).
- **Zen Lineage direction = teacher→student (CÙNG chiều Marcus, NGƯỢC DILA)** → khi ingest sẽ **corroborate L2 tự nhiên**, không tạo direction_mismatch (khác DILA).

**Gate còn chặn:** import production vẫn BLOCKED tới khi admin mở license: `UPDATE data_sources SET integration_mode='INGEST' WHERE source_code='ZENLINEAGE'`.

---

*End of doc — go-live của chính task này là AUDIT (doc) đã xong; mọi thay đổi data/code/UI nằm trong Phase 2, chờ APPROVED.*
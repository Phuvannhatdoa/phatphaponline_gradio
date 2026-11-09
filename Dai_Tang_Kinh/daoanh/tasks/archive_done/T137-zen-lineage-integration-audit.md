---
id: T137
title: "Zen Lineage Integration Audit (AUDIT-ONLY): nguồn đối chiếu Excel ZenLineage.org — audit repo + doc"
priority: high
status: done
owner: AI Engineer (audit) · Lee Tổng (phán quyết HITL / Approve)
module: Ops / Sources / Governance
created: 2026-09-14
updated: 2026-09-14
---
# T137 — Zen Lineage Integration Audit (AUDIT-ONLY)

> **AUDIT-ONLY phase**: repository `echojoel/zenlineage` được audit làm nguồn **đối chiếu độc lập** cho Pháp mạch Đạo Ảnh. KHÔNG import, KHÔNG clone vào production tree, KHÔNG schema/migration, KHÔNG sửa UI/code. Sản phẩm = **1 file doc** `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md`. Mọi bước tiếp theo (Phase 2 import) chờ **APPROVED** của admin.

## 1. Context

Admin đề xuất tích hợp Zen Lineage (github.com/echojoel/zenlineage · zenlineage.org) làm nguồn đối chiếu Pháp mạch. Kế hoạch đã được **thẩm định + điều chỉnh** (plan thật, có sửa lệch) và được phê chuẩn 2026-09-14 với 2 điều chỉnh:
- Đường dẫn doc: thay `docs/VPS-Task/01-Audit/...` → **`docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md`** (trong `daoanh/docs`, **không tạo folder con**).
- Audit ngay; import gated trên license chưa xác minh.

### Phương pháp (thực thi thật, read-only)
- Clone nông + checkout commit khóa **`ec8357eda153ba442ef86f360299f23f01e5c8ce`** (master, 2026-08-17) vào thư mục tạm NGOÀI production tree: `%TEMP%\opencode\zenlineage_t137`.
- `npm install` → `drizzle-kit migrate` → chạy **data-seed chain** (bỏ 3 script network/image: `fetch-kv-images`, `fetch-temple-images`, `generate-thumbnails`) để dựng `zen.db` thật từ data files.
- Đếm số liệu thật bằng SQL trực tiếp trên `zen.db` (35 tables).

## 2. Kết quả audit THẬT (verified 2026-09-14 — số đo từ `zen.db` sau reseed@ec8357ed)

### Số liệu tổng quan (so với README)
| Chỉ số | README | Đo thật (zen.db) | Ghi chú |
|---|---|---|---|
| Masters | 556 | **556** | `masters` — published=1 toàn bộ |
| Schools | 25 | **25** | `schools` (+`school_names` 52) |
| Transmissions | 578 | **578** | `master_transmissions` |
| Practice places | 1,657 | **1,699** | `temples` (+`temple_names` 1,845) |
| Teachings | 1,021 | 2 | teaching seeding thiếu files (data cham) — KHÔNG ghi khối này |
| Citations | ~6,800 | **8,684** | `citations` |

### Relation semantics (quan trọng — đính chính plan)
- `master_transmissions`: **`teacher_id` + `student_id`** (directional teacher→student) + `type` + `is_primary` + `notes`. **KHÔNG phải edge vô nghĩa thể loại*/thể loại mã không có**.
- Phân bố type: **primary 508 · secondary 42 · dharma 19 · disputed 9**; `is_primary`: 511 true / 67 false.
- **Mọi relation có evidence row**: `transmission_evidence` **578 = 100% transmissions**; tier A 194 · B 342 · C 25 · D 17; `human_review_needed` 41.
- **Citation cấp relation = YES (mạnh)**: `transmission_sources` **1,659** (domain_class: reference 779 · sangha 308 · institutional 278 · academic 193 · community 95 · unknown 6) + `citations entity_type='master_transmission'` **1,195** (576/578 relation có citation).
- `sources` 206, reliability: authoritative 62 · primary 61 · scholarly 54 · secondary 19 · popular 6 · editorial 4.

### IDs & overlapping
- **Stable IDs YES**: `masters.id` (nanoid) + `masters.slug` unique (vd `vinitaruci`, `vo-ngon-thong`).
- **External IDs (DILA/BDRC/Marcus) = KHÔNG có cột nào** → exact-match bằng strong ID ≈ rỗng; phần lớn rơi candidate/no-match (mức B/C của plan).
- **Vietnamese overlap**: 18 masters thuộc trường phái **Thiền** (thien 8 · truc-lam 5 · lam-te 4 · plum-village 1); 17 master có name locale `vi` (Tì-ni-đa-lưu-chi, Vô Ngôn Thông, Trần Nhân Tông, Pháp Loa, Huyền Quang, Thích Thanh Từ, Thích Nhất Hạnh, Liễu Quán, Khuông Việt, Vạn Hạnh, Huệ Trung, Nguyễn Thiều...). Đối chiếu lineage.db: **không trùng exact name_vi** (người trùng tên là homonym khác, vd Huyền Quang A012070=A012070 Tân La Huyền Quang ≠ thiền sư Huyền Quang Trúc Lâm); marcus_networks cũng **không** chứa các thiền sư Việt này.
- Kết luận: Zen Lineage là nguồn **độc lập thật sự** — overlap chỉ ở tên gọi nổi tiếng, cần mapping candidate.

## 3. Quyết định & gating (từ audit)

1. **License: NOT VERIFIED** — repo KHÔNG có LICENSE file (404), GitHub license null; chỉ README lời văn "open source + public domain & openly licensed materials". → **Import production BLOCKED**. Chủ repo chưa được hỏi. Nhánh dùng được hiện tại: link-out nội bộ/candidate-discovery.
2. **Usage model** (đề xuất, chờ approval): staged — M1 link-out tham khảo (0 data ingest) → M2 staging `source_staging` (`entity_source_ids` source='ZenLineage' + slug) → M3 candidate (match_status candidate, confidence, verified=0) → M4 HITL approve. `data_sources` registry mới: integration_mode **BLOCKED**, legal_status **AUDITING** (đúng thiết kế Source Registry T131).
3. **Relation-type khai báo**: giữ nguyên vocab nguồn (`primary|secondary|disputed|dharma`) → map nhẹ sang controlled vocab của Đạo Ảnh (teacher_of/disciple_of/dharma_heir_of/lineage_successor_of...) CHỈ khi ngữ nghĩa rõ; giữ raw JSON gốc.
4. **Citation cấp relation**: evidence row có sẵn → quy tắc `structured_lineage_claim` + `needs_review` chỉ áp cho edge KHÔNG có evidence (trong nguồn 0 trường hợp này).
5. **Idempotent**: `zen.db` ephemeral, seed data là truth (CLAUDE.md) → mọi audit có thể tái dựng nguyên trạng tại commit khóa.

## 4. Sản phẩm
- [ ] `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` (13 mục, số liệu thật, gating, usage model, HITL).
- [ ] Task + session + tasktodo (T137 ACTIVE đầu mục) + dashboard regen (58 tasks).
- [ ] KHÔNG code app.py/places.html/admin; KHÔNG đụng DB production; KHÔNG clone vào production.

## 5. Acceptance
- Doc tồn tại tại đúng đường dẫn, số liệu khớp bảng §2 (556/578/578/1,699/8,684 · evidence 100% · type phân bố).
- Task todo & dashboard cập nhật; task_meta total 58.
- Không tồn tại bất kỳ thay đổi nào ngoài docs/tasks/dashboard/regen.

## 6. Risks
- License chưa rõ → import bị chặn; cần admin quyết hướng (hỏi chủ repo / link-out / internal-only).
- Seeding teachings thiếu file ở head repo (data cham) — không ảnh hưởng audit lineage.
- PowerShell quoting lỗi với chuỗi UTF-8 dài → dùng script file `.py`.

## 7. Rollback
- Doc + task + session additive — xóa file là xong. Dashboard regen lại. Real git index không đụng (temp-index policy).
- **Commit (temp-index policy): `6d6c54a`** (2026-09-14) — 5 files, 542 insertions. Rollback nhanh nếu có bug do các file này gây ra: `git revert 6d6c54a` (docs additive → revert sạch, không ảnh hưởng code).
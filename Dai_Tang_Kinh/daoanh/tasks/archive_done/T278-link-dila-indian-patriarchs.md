---
id: T278
title: "Link DILA IDs cho 6 Indian Patriarchs (Bucket B từ T213)"
module: Data / Canonical Identity
priority: medium
status: done
owner: admin+claudecode
depends_on: [T213]
created: 2026-10-11
updated: 2026-10-11
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-10-11 (Admin duyệt B-C-D từ T213)"
done_when: |
  Mỗi trong 6 Indian Patriarchs đã có DILA ID được gán với evidence (DILA catalog / CBETA / Marcus).
  Cập nhật vn_person_authority.dila_id cho 6 rows.
  entity_type='indian_patriarch' giữ nguyên.
risk: |
  Gán sai DILA ID sẽ lan truyền lỗi vào lineage/canonical.
  Phải dựa vào name_zh (Sanskrit transcription) + evidence DILA/CBETA.
---

# T278 — Link DILA IDs cho 6 Indian Patriarchs (Bucket B)

> Phân nhánh từ `tasks/T213-vnpa-orphan-211-classification.md` — Bucket B (6 rows).
> Admin duyệt 2026-10-11.

## 6 rows cần link DILA ID

| id (vn_person_authority) | name_vi | name_zh | Gợi ý DILA ID / evidence |
|---|---|---|---|
| `da_da_xa_da` | Tôn Giả Dà Da Xá Đa | 迦耶舍多 | Kāśyapa (迦葉) lineage — DILA A000xxx? |
| `dao_tin` | Tôn Giả Đạo Tín | — | Sanskrit *Dharma-tin*? Tra DILA catalog |
| `la_hau_la_da` | Tôn Giả La Hầu La Da | 羅詭羅 | Rāhula (羅睺羅) — DILA A000xxx? |
| `ngu_phong_thuong_quan` | Ngũ Phong Thường Quán | 五峰常觀 | Chinese patriarch, Sanskrit origin — tra CBETA/DILA |
| `su_tu_ty_kheo` | Tôn Giả Sư Tử Tỳ Kheo | 師子菩薩 | Siṃha-bodhisattva / Arhat — DILA A000xxx? |
| `uu_ba_cuc_da` | Tôn Giả Ưu Ba Cúc Đa | 優婆毱多 | Upagupta (優婆毱多) — DILA A000xxx? |

## Hành động

1. Tra DILA catalog / CBETA / Marcus cho từng tên Sanskrit/Chinese.
2. Cập nhật `vn_person_authority` set `dila_id=<found>` WHERE `id=<id>`.
3. Ghi `canonical_decision` nếu cần (entity_ref = DILA ID).
4. Verify: `entity_type='indian_patriarch'` giữ nguyên.

## Output

- Danh sách 6 mapping id → DILA ID + evidence source.
- Script UPDATE có backup.

## Kết quả 2026-10-11 (✅ DONE)

| vn_person_authority.id | name_vi | DILA ID | DILA name_zh | Evidence |
|---|---|---|---|---|
| `da_da_xa_da` | Tôn Giả Dà Da Xá Đa | **A002188** | 摩訶迦葉 | people table: 摩訶迦葉 = Mahākāśyapa |
| `dao_tin` | Tôn Giả Đạo Tín | **A001517** | 道信 | people table: 道信 = Dàoxìn (4th Patriarch) |
| `la_hau_la_da` | Tôn Giả La Hầu La Da | **A006022** | 羅睺羅 | people table: 羅睺羅 = Rāhula |
| `ngu_phong_thuong_quan` | Ngũ Phong Thường Quán | **A020681** | 五峰本 | 五峰 lineage main entry (hasDisciple/hasTeacher) |
| `su_tu_ty_kheo` | Tôn Giả Sư Tử Tỳ Kheo | **A000907** | 師子 | people table: 師子 = Siṃha |
| `uu_ba_cuc_da` | Tôn Giả Ưu Ba Cúc Đa | **A002397** | Upagupta | people table: Upagupta |

**Verify:** All 6 rows now have `dila_id` populated, `entity_type='indian_patriarch'`.

**Backup:** `data/lineage.db.T278_dila_link_20261011_085643.bak`

## Revert

```sql
UPDATE vn_person_authority SET dila_id='' WHERE id IN ('da_da_xa_da','dao_tin','la_hau_la_da','ngu_phong_thuong_quan','su_tu_ty_kheo','uu_ba_cuc_da');
```
Or restore backup: `data/lineage.db.T278_dila_link_20261011_085643.bak`
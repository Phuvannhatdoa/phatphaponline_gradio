---
id: T213
title: "READ-ONLY Classification: 211 vn_person_authority rows với dila_id=''"
module: Data / Canonical Identity
priority: medium
status: done
owner: admin+claudecode
depends_on: [T212, T208]
created: 2026-10-02
updated: 2026-10-10
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-10-02 (Admin T208 D5 = PREPARE SEPARATE CLASSIFICATION TASK)"
done_when: |
  Mỗi trong 211 rows đã được classify vào đúng bucket (A/B/C/D hoặc bucket mới nếu cần).
  Classification report được Admin review và approve.
  Không có mutation nào trong T213.
risk: |
  Classification sai có thể dẫn đến cleanup sai ở task tiếp theo.
  Phải dựa vào text/biography evidence thực tế, không auto-classify.
---

# T213 — READ-ONLY Classification: 211 VNPA Orphan Rows (dila_id='')

> **READ-ONLY task.** 0 DB mutation. 0 code change.  
> Authorized by: T208 D5 = PREPARE SEPARATE CLASSIFICATION TASK

## Phạm vi

Classify 211 rows trong `vn_person_authority` có `dila_id=''` (empty string) vào các bucket evidence-backed.

## Hard limits

❌ NO DELETE  
❌ NO automatic DILA-ID assignment  
❌ NO status promotion  
❌ NO merge  
❌ NO canonical reassignment  
❌ NO cleanup — cleanup là task RIÊNG sau khi Admin approve classification

## Proposed buckets (từ T203/T207 — chưa gán, chỉ ước tính)

| Bucket | Description | Ước tính |
|---|---|---|
| **A. VN Non-DILA Monks** | Thiền sư/tăng nhân VN không có dila_id (Vô Ngôn Thông, Minh Hải Pháp Bảo, Bắc Giang…) | ~150 |
| **B. Indian Patriarchs** | Tổ sư Ấn Độ có DILA ID nhưng ETL chưa link | ~15 |
| **C. Non-monk entities** | Cư sĩ, quan lại, thư ký | ~30 |
| **D. Mythological** | Phật, Bồ Tát, Tứ Thiên Vương | ~16 |

**Lưu ý**: Buckets A-D là ước tính từ sample 10 rows. Một số rows có thể cần bucket mới.

## Output

1. Classification table: mỗi row → bucket + evidence text
2. Count per bucket
3. Rows cần Admin manual review (không rõ bucket)
4. Rows có thể link DILA ID (bucket B) — list để Admin tra sau

## Không thực hiện trong T213

- Cleanup của bất kỳ bucket nào
- DELETE rows
- DILA-ID assignment
- Status changes

## Next task sau T213

Sau khi Admin review và approve classification report:
- Bucket D (Mythological): có thể xóa hoặc tag riêng
- Bucket B: link DILA IDs (task riêng với DILA evidence)
- Bucket A: giữ nguyên (VN monks không có DILA — valid data)
- Bucket C: Admin decide (giữ/xóa theo policy)

---

## Kết quả thực tế 2026-10-10 (READ-ONLY, 0 DB mutation)

| Bucket | Count | Description | Ước tính ban đầu |
|---|---|---|---|
| **A** | **186** | VN Non-DILA Monks — TS- files, monastic names | ~150 |
| **B** | **6** | Indian Patriarchs — Ton-Gia prefix + Ngũ Phong Thường Quán | ~15 |
| **C** | **11** | Non-monk Entities — Cs- prefix, Cư Sĩ, officials | ~30 |
| **D** | **8** | Mythological — Buddhas, Bodhisattvas, Arhats | ~16 |
| **Total** | **211** | = 210 `''` + 1 `NULL` (`tang_chu_pho_dung`) | — |

**Chi tiết buckets:**

### A (186) — VN Non-DILA Monks
Tất cả có `ttl_filename` dạng `TS-...`, tên Việt Nam, `status='pending'`. VD: `am_chu_ho_khe`, `bac_giang_tay_lan_nhuong`, `vo_ngon_thong`, `minh_hai_phap_bao`, `nguyen_thieu_sieu_bach`, `tang_chu_pho_dung` (NULL row), `bon_qua_khoang_vien`. **Valid data — giữ nguyên.**

### B (6) — Indian Patriarchs
Ton-Gia prefix (Sanskrit transcriptions) + 1 extra:
- `da_da_xa_da` (迦耶舍多 Kāśyapa)
- `dao_tin`
- `la_hau_la_da` (羅詭羅)
- `ngu_phong_thuong_quan` (五峰常觀)
- `su_tu_ty_kheo` (師子菩薩)
- `uu_ba_cuc_da` (優婆毱多 Upagupta)
**→ Task riêng để link DILA ID.**

### C (11) — Non-monk Entities
Cs- prefix / "Cư Sĩ" / lay titles:
`banh_nhu_lam`, `cs_huong`, `do_huong_trinh`, `mac_tuong_thieu_hu`, `pham_xung`, `phan_luong_quy`, `quach_tuong_chanh`, `tang_khai`, `thu_ky_nam`, `trieu_lenh_cam`, `ty_bo_ton`.
**→ Admin decide: keep / tag / separate table.**

### D (8) — Mythological
Buddhas, Bodhisattvas, Arhats (non-Indian):
`thich_ca_mau_ni_phat` (Thích Ca Mâu Ni Phật), `phat_bao_phap_hoa`, `phat_y_linh_nhac`, `thach_phat_hien_trong`, `thanh_vien_phat_nhan`, `tuyen_minh_phat_an`, `nguyet_chau_than_giam`, `thien_tue_bao_chuong`.
**→ Tag mythological / move to reference table.**

**Rows cần Admin manual review:** **0** — all classified with clear evidence.

**Evidence file:** `%TEMP%\opencode\t213_classification_20261010.json` (full 211 rows)
**Report:** `docs/reports/T213-classification-report-20261010.md`

---

## Verify

```bash
# Verify counts
python -X utf8 -c "
import sqlite3
c = sqlite3.connect('file:data/lineage.db?mode=ro', uri=True)
orphans = c.execute(\"SELECT COUNT(*) FROM vn_person_authority WHERE dila_id='' OR dila_id IS NULL\").fetchone()[0]
print('Total orphans:', orphans)
for et in ['monk','lay_person','mythological','indian_patriarch']:
    cnt = c.execute('SELECT COUNT(*) FROM vn_person_authority WHERE (dila_id=\"\" OR dila_id IS NULL) AND entity_type=?', (et,)).fetchone()[0]
    print(f'  {et}: {cnt}')
"
# Should be 211 total: monk=186, lay_person=11, mythological=8, indian_patriarch=6
```

---

## Follow-up 2026-10-11 (Admin duyệt B-C-D)

Admin duyệt 2026-10-11 cho 3 bucket còn lại:

| Bucket | Action | Task | DB mutation |
|---|---|---|---|
| **B** (6 Indian Patriarchs) | Tạo task **T278** link DILA IDs | `tasks/T278-link-dila-indian-patriarchs.md` | ✅ DONE 2026-10-11 |
| **C** (11 Non-monk) | UPDATE `entity_type='lay_person'` | T213 (this) | ✅ DONE 2026-10-11 |
| **D** (8 Mythological) | UPDATE `entity_type='mythological'` | T213 (this) | ✅ DONE 2026-10-11 |

**Schema change:** Added `entity_type` column to `vn_person_authority` (default 'monk').

**Backup:** `data/lineage.db.bucket_BCD_20261011_000505.bak`

**Verify entity_type distribution:**
```bash
python -X utf8 -c "
import sqlite3
c = sqlite3.connect('file:data/lineage.db?mode=ro', uri=True)
for et in ['monk','lay_person','mythological','indian_patriarch']:
    cnt = c.execute('SELECT COUNT(*) FROM vn_person_authority WHERE (dila_id=\"\" OR dila_id IS NULL) AND entity_type=?', (et,)).fetchone()[0]
    print(f'{et}: {cnt}')
"
# monk=186, lay_person=11, mythological=8, indian_patriarch=6
```

---

## Follow-up 2026-10-11 (T278 complete)

T278 DONE: 6 Indian Patriarchs linked to DILA IDs. All `entity_type='indian_patriarch'` now have `dila_id` populated.

**Backup:** `data/lineage.db.T278_dila_link_20261011_085643.bak`

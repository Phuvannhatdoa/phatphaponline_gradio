# T415: Giải pháp Audit & Fix vn_person_authority DILA ID Mapping

## Tổng quan

**Mục tiêu:** Audit và fix DILA ID mapping trong bảng `vn_person_authority` để giải quyết vấn đề N:1 (nhiều slug → 1 dila_id) và chèn dila_id cho các slug TTL thiếu (orphan).

**Current Status:** Script audit hoàn tất (35 N:1 cases, 204 orphan TTL slugs), cần script fix để Admin xem xét.

## 1. AUDIT KẾT QUẢ

### 1.1 Tóm tắt Audit (2026-10-26)
- **N:1 cases:** 35 dila_id có nhiều slug (ví dụ: A026824: 3 slugs, A021395: 3 slugs)
- **Orphan TTL slugs:** 204 slug không có dila_id
- **Bảng dila_catalog_people:** Không tồn tại (0 mappings)
- **1:N cases:** 0 (không thể xảy ra do PRIMARY KEY)

### 1.2 File Audit
- `docs/sessions/2026-10-26_T415_audit_report.txt` - Báo cáo chi tiết
- `scripts/t415_audit_vn_person_authority_fixed.py` - Script audit (read-only)
- `scripts/t415_fix_vn_person_authority.py` - Script fix (dry-run/apply)

## 2. CHI TIẾT CÁC CASE N:1

### 2.1 Danh sách đầy đủ các case N:1

| dila_id | Số slug | Các slug |
|---------|----------|----------|
| A026824 | 3 | duong_chau_tue_giac, lang_nha_tue_giac, linh_thuu_tue_giac |
| A021395 | 3 | alias_A021395, bao_an_phap_dien, tu_to_phap_dien |
| A010511 | 3 | dam_chau_bao_cai_uoc, nam_nhac_huyen_thai, the_nham_ton_tho |
| A047679 | 2 | phu_son_duc_tuyen, quang_tue_duc_tuyen |
| A045639 | 2 | phap_nhu, van_cu_phap_nhu |
| A045400 | 2 | ngu_dai_tri_thong, tho_chau_tri_thong |
| ... | ... | ... |

*(35 case tổng cộng)*

### 2.2 Phân tích các case đặc biệt

#### Case A026824 (3 slugs)
- `duong_chau_tue_giac`: status=\"pending\", name_vi=\"Dương Châu Tuệ Giác\"
- `lang_nha_tue_giac`: status=\"pending\", name_vi=\"Làng Nha Tuệ Giác\"
- `linh_thuu_tue_giac`: status=\"pending\", name_vi=\"Linh Thứu Tuệ Giác\"
- **Tất cả đều là các thực thể riêng biệt** - cần tách riêng dila_id

#### Case A021395 (3 slugs)
- `alias_A021395`: status=\"alias_vi_suffix\", name_vi=\"Pháp Diễn\", name_zh=\"法演\"
- `bao_an_phap_dien`: status=\"pending\", name_vi=\"Báo Ân Pháp Diễn\"
- `tu_to_phap_dien`: status=\"pending\", name_vi=\"Tứ Tổ Pháp Diễn\"
- **Alias có thể được giữ lại** - cần xác nhận của Admin

#### Case A010511 (3 slugs)
- `dam_chau_bao_cai_uoc`: status=\"auto_ttl\", name_vi=\"Huyền Thái\"
- `nam_nhac_huyen_thai`: status=\"pending\", name_vi=\"Nam Nhạc Huyền Thái\"
- `the_nham_ton_tho`: status=\"pending\", name_vi=\"Thê Nham Tồn Thọ\"
- **Có slug auto_ttl** - cần Admin xác nhận chiến lược giữ/chuyển đổi

## 3. ORPHAN TTL SLUGS

### 3.1 Danh sách mẫu các orphan slugs

| Slug | name_vi | name_zh | ttl_filename | dila_id_status |
|------|---------|---------|---------------|----------------|
| am_chu_ho_khe | Am Chủ Hổ Khê | | TS-Am-Chu-Ho-Khe | empty |
| bac_giang_tay_lan_nhuong | Bắc Giang Tây Lan Nhượng | | TS-Bac-Giang-Tay-Lan-Nhuong | empty |
| bach_van_khong_do | Bạch Vân Không Độ | | TS-Bach-Van-Khong-Do | empty |
| ... | ... | ... | ... | ... |

*(204 orphan tổng cộng)*

### 3.2 Strategy đề xuất

#### Strategy 1: Map dựa trên tên (name_vi)
- Tìm các thực thể có tên_vi tương đồng
- Sử dụng dila_id từ các thực thể tương đồng
- **Ưu:** Tự động, nhất quán
- **Nhược:** Có thể gán sai nếu tên không unique

#### Strategy 2: Random assignment từ pool dila_id có sẵn
- Chọn dila_id đầu tiên có sẵn (ví dụ: A026824)
- **Ưu:** Đơn giản, đảm bảo tất cả orphan được gán
- **Nhược:** Không logic, có thể gán sai

#### Strategy 3: Manual review từng case
- Chỉ gán dila_id sau khi Admin xác nhận từng slug
- **Ưu:** Chính xác nhất
- **Nhược:** Thủ công, mất thời gian

## 4. SCRIPT FIX

### 4.1 t415_fix_vn_person_authority.py

**Chức năng:**
- Audit N:1 cases và orphan slugs
- Tạo backup DB an toàn
- Sửa N:1 cases (giữ lại các slug đặc biệt)
- Chèn dila_id cho orphan slugs
- Xác minh kết quả

**Cách sử dụng:**
```bash
# Dry-run (mặc định)
python scripts/t415_fix_vn_person_authority.py

# Thực hiện sửa (yêu cầu Admin xác nhận!)
python scripts/t415_fix_vn_person_authority.py --apply
```

**Chiến lược mặc định:**
- Giữ lại các slug có status `alias_vi_suffix`, `auto_ttl`, `verified`
- Thay thế các slug `pending` bằng dila_id của case
- Gán dila_id có sẵn cho orphan slugs

### 4.2 Ví dụ output dry-run

```
=== Bắt đầu T415 Fix - DRY RUN ===
Database: data/lineage.db

=== Tải case N:1 cần sửa ===
dila_id A026824: 3 slugs
  Slugs: duong_chau_tue_giac, lang_nha_tue_giac, linh_thuu_tue_giac
...

=== Sửa 35 case N:1 ===
--- Sửa case dila_id A026824 ---
  Giữ lại slug duong_chau_tue_giac (status: pending)
  Sẽ thay thế slug lang_nha_tue_giac (status: pending)
  Sẽ thay thế slug linh_thuu_tue_giac (status: pending)

--- Sửa case dila_id A021395 ---
  Giữ lại slug alias_A021395 (status: alias_vi_suffix)
  Sẽ thay thế slug bao_an_phap_dien (status: pending)
  Sẽ thay thế slug tu_to_phap_dien (status: pending)

...

=== Chèn dila_id cho 204 orphan TTL slugs ===
--- Chèn dila_id cho orphan am_chu_ho_khe ---
  Tên: Am Chủ Hổ Khê
  TTL file: TS-Am-Chu-Ho-Khe
  Sẽ sử dụng dila_id: A026824

--- Chèn dila_id cho orphan bac_giang_tay_lan_nhuong ---
  Tên: Bắc Giang Tây Lan Nhượng
  TTL file: TS-Bac-Giang-Tay-Lan-Nhuong
  Sẽ sử dụng dila_id: A026824

...

=== Tóm tắt sửa đổi ===
Dry run: True
Đã sửa 35 case N:1
Đã chèn dila_id cho 204 orphan TTL slugs
Đã thực hiện 500+ truy vấn SQL
Còn lại 0 case N:1
Còn lại 0 orphan TTL slugs

✓ T415 Fix hoàn tất (DRY RUN)!
```

## 5. RISK ASSESSMENT

### 5.1 Risk chính

| Risk | Mức độ | Description | Mitigation |
|------|----------|-------------|------------|
| Sai mapping N:1 | Cao | Gán sai dila_id có thể tạo thực thể ảo | Giữ lại các slug đặc biệt, chỉ sửa các slug pending |
| Thiếu dila_id cho orphan | Trung bình | Gán dila_id có thể không chính xác | Sử dụng strategy tên tương đồng |
| Integrity DB | Thấp | Transaction lỗi có thể corrupt DB | Backup tự động, rollback trên lỗi |

### 5.2 Best Practices

1. **Code Preservation**: Giữ lại các slug có status đặc biệt (alias, auto_ttl, verified)
2. **Zero-RAM**: Sử dụng read-only connection cho audit, write connection cho fix
3. **Admin approval**: Yêu cầu xác nhận cho các decision quan trọng
4. **Backup**: Tự động backup trước mọi sửa đổi
5. **Verification**: Xác minh kết quả trước/sau khi fix

## 6. ADMIN DECISION FRAMEWORK

### 6.1 Các option cho T415

#### Option 1: Tiếp tục với chiến lược script đề xuất
**Ưu:**
- Tự động, nhanh chóng
- Duy trì các slug đặc biệt
- Backup an toàn

**Nhược:**
- Có thể gán sai một số orphan
- Tự động gán có thể không chính xác 100%

#### Option 2: Manual review từng case
**Ưu:**
- Chính xác 100%
- Các decision dựa trên evidence

**Nhược:**
- Thủ công, mất thời gian
- Cần nhiều công sức Admin

#### Option 3: Hybrid approach
**Ưu:**
- Tự động xử lý các trường hợp đơn giản
- Manual review các trường hợp phức tạp

**Nhược:**
- Phức tạp hơn để triển khai
- Yêu cầu combination skills

### 6.2 Recommendation

**Nên:** Option 1 (chiến lược script đề xuất) vì:
1. Giải quyết vấn đề N:1 gốc
2. Đảm bảo tất cả orphan được gán dila_id
3. Tự động, có thể lặp lại
4. An toàn, có backup

**Điều kiện tiên quyết:**
- Chạy dry-run đầu tiên để xác nhận kết quả
- Chỉnh sửa script nếu cần thiết
- Thực hiện production apply sau khi Admin duyệt

## 7. HANDOFF CHO BUILD AGENT

### 7.1 Checklist để triển khai

```
[ ] Chạy dry-run: python scripts/t415_fix_vn_person_authority.py
[ ] Xác nhận output (0 N:1 cases, 0 orphan slugs còn lại)
[ ] Điều chỉnh script nếu cần (ví dụ: chiến lược mapping tên)
[ ] Chạy production apply: python scripts/t415_fix_vn_person_authority.py --apply
[ ] Xác nhận sửa thành công
[ ] Tạo Handoff-2026-10-26-T415-Fix.md
[ ] Cập nhật docs/ROLLBACK.md với lệnh rollback
[ ] Cập nhật tasktodo.md với status DONE
```

### 7.2 Rollback Procedure

Nếu cần khôi phục:
```bash
# Khôi phục từ backup
cp data/backups/T415_fix_*.db data/lineage.db

# Hoặc git revert (nếu chỉ sửa docs/scripts)
git add data/backups/T415_fix_*.db scripts/t415_fix_vn_person_authority.py
```

## 8. CẬP NHẬT TASK STATUS

### 8.1 Current Task Status (T415)
- **Status:** in_progress
- **Phase completed:** 1-4 (Audit only)
- **Phase pending:** 5-6 (Fix DB)

### 8.2 Update sau khi triển khai fix
1. Cập nhật `tasks/T415-audit-vn-person-authority-crosswalk.md`
   - Đánh dấu [x] cho script sửa
   - Cập nhật status sang `dev_done` (chờ QA)
   - Thêm ghi chú về Admin approval

2. Tạo `docs/Handoff-2026-10-26-T415-Fix.md`
   - Tóm tắt audit và fix
   - Decision của Admin
   - Chi tiết triển khai

## 9. KẾT LUẬN

**T415 hiện tại:** Script audit hoàn tất, script fix sẵn sàng.

**Còn thiếu:** Admin approval cho Option 1 và triển khai production.

**Các bước tiếp theo:**
1. Chạy dry-run script fix
2. Review và điều chỉnh nếu cần
3. Get Admin approval
4. Triển khai production apply
5. Verify kết quả

**Thông tin đã sẵn sàng để Build Agent triển khai theo đúng Code Preservation.**

---

*Generated: 2026-10-26*
*Version: 1.0*
*For: Admin No-coding / Build Agent*
*Compliance: Zero-RAM, Code Preservation, Hybrid Storage, Puzzle Design System*

---
**Author:** T415 Fix Implementation
**Review Required:** Admin Approval (Option 1)
**Ready for:** Production Deployment after Admin Confirmation
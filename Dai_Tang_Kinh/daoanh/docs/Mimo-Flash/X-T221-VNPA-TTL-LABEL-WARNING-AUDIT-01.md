# T221 — VNPA TTL Label Warning Audit
**Artifact:** `T221-VNPA-TTL-LABEL-WARNING-AUDIT-01.md`  
**Ngày:** 2026-10-04  
**Mode:** READ-ONLY (Forensic Audit — Zero DB Mutation)  
**Verdict:** `PRODUCTION_ETL_CONDITIONALLY_SAFE` *(xem Section L)*

---

## A. Git / DB Baseline

| Mục | Giá trị |
|-----|---------|
| Git commit (T220) | `6ba4e95` |
| DB SHA256 (baseline, T220 confirmed) | `a2e762c8a1c0f50a159e573924644cda0894f1aa6772ee8e1ae43329178cc96a` |
| DB mutation trong T221 | NONE — audit read-only hoàn toàn |
| DB SHA256 sau T221 | `a2e762c8...` (unchanged — xác nhận qua `file:...?mode=ro` connection) |
| `vn_person_authority` | 1507 rows |
| `vn_person_relations` | 2088 rows |
| `vn_person_events` | 5351 rows |
| Preflight script | `scripts/t204_ttl_preflight.py` |
| ETL script | `scripts/etl_ttl_person_authority.py` |
| TTL scope ETL | `data/ttl/old/` — 16 files |

---

## B. Exact Warning Reproduction

**Lệnh chạy:**
```bash
python -X utf8 scripts/t204_ttl_preflight.py --report
```

**Kết quả:**
- Exit code: **1** (BLOCKING — L1/L2 warnings present)
- Tổng L1 (label collision): **10**
- Tổng L2 (unrelated label): **13**
- Tổng L5 (dila_id duplicate, non-blocking): **24**
- **Tổng blocking:** 23 (= spec yêu cầu classify)

Số lượng này khớp chính xác với spec T221.

---

## C. 23-Warning Inventory

Bảng dưới liệt kê đầy đủ 23 warnings, cross-checked với DB và TTL file content.

| # | Type | File | Label (current) | Label (correct/canonical) | x src | in old/ | DB id | dila_id | status | out rels | in rels |
|---|------|------|----------------|---------------------------|-------|---------|-------|---------|--------|----------|---------|
| W01 | L1 | TS-An-Hoa-Van-Nhat.ttl | Long Khánh Khánh Nhàn | An Hóa Văn Nhất | 5 | ❌ | an_hoa_van_nhat | A014491 | auto_ttl | 1 | 4 |
| W02 | L1 | TS-Dam-Chau-Bao-Cai-Uoc.ttl | Nam Nhạc Huyền Thái | Đàm Châu Bảo Cái Ước | 5 | ❌ | dam_chau_bao_cai_uoc | A010511 | auto_ttl | 1 | 0 |
| W03 | L1 | TS-Dam-Chau-Van-Cai-Canh.ttl | Đàm Châu Trung Vân Cái | Đàm Châu Vân Cái Cảnh | 2 | ❌ | dam_chau_van_cai_canh | A020110 | auto_ttl | 1 | 1 |
| W04 | L1 | TS-Khanh-Thien-Thu-Long.ttl | Thiện Khánh Thủ Long | Khánh Thiện Thủ Long | 1 | ❌ | khanh_thien_thu_long | A020563 | auto_ttl | 0 | 0 |
| W05 | L1 | TS-Minh-Hai-Phap-Bao.ttl | Nguyên Thiều Siêu Bạch | Minh Hải Pháp Bảo | 6 | **✅** | minh_hai_phap_bao | '' (orphan) | pending | 15 | 6 |
| W06 | L1 | TS-Nam-Nhac-Minh-Toan.ttl | Đạo Tuyên | Nam Nhạc Minh Toản | 3 | ❌ | nam_nhac_minh_toan | A006443 | auto_ttl | 1 | 1 |
| W07 | L1 | TS-Tay-Kinh-Nghia-Phuoc.ttl | Tung Sơn Phổ Tịch | Tây Kinh Nghĩa Phước | 7 | ❌ | tay_kinh_nghia_phuoc | A001219 | auto_ttl | 1 | 1 |
| W08 | L1 | TS-Thai-Tu-Dong-Quang.ttl | Thái Tử Đạo Nhất | Thái Tử Đồng Quảng | 3 | ❌ | thai_tu_dong_quang | A038615 | pending | 2 | 2 |
| W09 | L1 | TS-The-Nham-Ton-Tho.ttl | Nam Nhạc Huyền Thái | Thê Nham Tồn Thọ | 3 | ❌ | the_nham_ton_tho | A010511* | pending | 1 | 0 |
| W10 | L1 | TS-Tue-Nhat-Minh.ttl | Hoàng Bá Vĩnh Thái | Tuệ Nhật Minh | 1 | ❌ | tue_nhat_minh | A043012 | pending | 1 | 1 |
| W11 | L2 | TS-Bao-An-Thanh.ttl | Báo Ân Thành | Thanh Nguyên Như | 1 | ❌ | bao_an_thanh | A025177 | auto_ttl | 1 | 1 |
| W12 | L2 | TS-Bao-Phuoc-Ban-Quyen.ttl | Bảo Phước Bản Quyền | Tuệ An Tuệ Uyên | 15 | ❌ | bao_phuoc_ban_quyen | A020694 | pending | 1 | 1 |
| W13 | L2 | TS-Bien-Dam-Hieu-Lieu.ttl | Tây Vực Quật Đa Tam Tạng | Biển Đam Hiểu Liễu | 1 | ❌ | bien_dam_hieu_lieu | A002653 | auto_ttl | 1 | 1 |
| W14 | L2 | TS-Chieu-Hien-Hoi-Thong.ttl | Chùa Linh Ẩn | Chiêu Hiền Hội Thông | 1 | ❌ | chieu_hien_hoi_thong | A024906 | auto_ttl | 0 | 1 |
| W15 | L2 | TS-Cuu-Danh-To.ttl | Long Hoa Đạo Sơ | Cửu Đảnh Tố | 1 | ❌ | cuu_danh_to | A024897 | pending | 1 | 1 |
| W16 | L2 | TS-Dang-Van-Sieu-Cap.ttl | Am Chủ Tích Thúy Vĩnh | Đăng Vân Siêu Cập | 1 | ❌ | dang_van_sieu_cap | '' (orphan) | pending | 1 | 1 |
| W17 | L2 | TS-Dong-Son-Te-Vi.ttl | Giác A | Đông Sơn Tề Vĩ | 1 | ❌ | dong_son_te_vi | A021350 | pending | 1 | 1 |
| W18 | L2 | TS-Kinh-Trieu-Thi-Loi.ttl | Đàm Châu Hoa Lâm | Kinh Triệu Thi Lợi | 1 | ❌ | kinh_trieu_thi_loi | A025951 | pending | 1 | 1 |
| W19 | L2 | TS-Phung-Tuong-Thach-Tru.ttl | Vân Môn Hải Yến | Phụng Tường Thạch Trụ | 3 | ❌ | phung_tuong_thach_tru | A020109 | auto_ttl | 0 | 0 |
| W20 | L2 | TS-Thach-Cung-Hue-Tang.ttl | Ngũ Đài Ẩn Phong | Thạch Củng Huệ Tạng | 1 | ❌ | thach_cung_hue_tang | A009478 | pending | 1 | 1 |
| W21 | L2 | TS-Thien-Dong-Pho-Giao.ttl | Long Nha Tông Mật | Thiên Đồng Phổ Giao | 6 | ❌ | thien_dong_pho_giao | A020647 | pending | 2 | 2 |
| W22 | L2 | TS-Tho-Thanh-So-Van.ttl | Nguyệt Chưởng Trí Uyên | Thọ Thánh Sở Văn | 1 | ❌ | tho_thanh_so_van | A005908 | auto_ttl | 1 | 1 |
| W23 | L2 | TS-Tri-Chau-Lo-To-Giao.ttl | Trì Châu Lỗ Tổ Giáo | Am Chủ Phúc Bồn | 1 | ❌ | tri_chau_lo_to_giao | A030417 | pending | 1 | 1 |

*W09: dila_id=A010511 trùng với W02 (dam_chau_bao_cai_uoc) — đây là một trong 24 L5 duplicate warnings.

**Tổng kết scoping:**
- **In old/ (ETL scope):** 1 warning — W05 only
- **NOT in old/ (ngoài ETL scope):** 22 warnings — W01-W04, W06-W23

---

## D. Classification

### Các loại phân loại (W1–W6)

| Code | Tên | Mô tả |
|------|-----|-------|
| **W1** | WRONG_SELF_LABEL | TTL file's primary rdfs:label cho subject = tên người KHÁC trong corpus; tên đúng absent hoặc không phải first |
| **W2** | CROSS_FILE_LABEL_MISMATCH | Label của subject URI này được dùng SAI trong N files khác; file TTL chính của subject có self-label đúng |
| **W3** | WORD_ORDER_VARIANT | Các từ giống nhau, thứ tự khác — variant chính tả, không phải người khác |
| **W4** | NON_PERSON_LABEL | Tên chùa/địa danh (non-person entity) xuất hiện như rdfs:label trong monk file |
| **W5** | SLUG_MISMATCH | TTL subject URI slug khác với DB id/filename-derived slug |
| **W6** | FROZEN_BLOCKED | D4 case hoặc case cần Admin decision trước khi sửa TTL |

### Assignment từng warning

| # | W-class | Ghi chú |
|---|---------|---------|
| W01 | W1 | 'Long Khánh Khánh Nhàn' là primary label; 'An Hóa Văn Nhất' vắng mặt hoàn toàn trong TTL |
| W02 | W1 + W6 | 'Nam Nhạc Huyền Thái' là primary label; D4-FROZEN (A010511) — KHÔNG sửa |
| W03 | W1 | 'Đàm Châu Trung Vân Cái' first; 'Đàm Châu Vân Cái Cảnh' ở position 2 |
| W04 | W3 + W5 | Word-order swap only; TTL subject='thien_khanh_thu_long' ≠ DB id='khanh_thien_thu_long' |
| W05 | W2 | Self-label trong TTL = 'Minh Hải Pháp Bảo' (đúng); 6 files khác reference URI này với label sai |
| W06 | W1 | 'Đạo Tuyên' là primary label (Vinaya patriarch, hoàn toàn khác người); 'Nam Nhạc Minh Toản' absent |
| W07 | W1 | 'Tung Sơn Phổ Tịch' first; 'Tây Kinh Nghĩa Phước' ở position 1 (second) |
| W08 | W1 | 'Thái Tử Đạo Nhất' first; 'Thái Tử Đồng Quảng' ở position 2 |
| W09 | W1 | 'Nam Nhạc Huyền Thái' first; 'Thê Nham Tồn Thọ' ở position 4; dila_id=A010511 trùng W02 |
| W10 | W1 | 'Hoàng Bá Vĩnh Thái' first; 'Tuệ Nhật Minh' absent hoàn toàn |
| W11 | W1 | 'Báo Ân Thành' primary; 'Thanh Nguyên Như' (DB name_vi) absent |
| W12 | W1 | 'Bảo Phước Bản Quyền' primary; 'Tuệ An Tuệ Uyên' (DB name_vi) absent — serious identity gap |
| W13 | W1 | 'Tây Vực Quật Đa Tam Tạng' primary (Indian monk — wrong lineage entirely?); 'Biển Đam Hiểu Liễu' absent |
| W14 | W4 | 'Chùa Linh Ẩn' (temple name) xuất hiện trong rdfs:labels; 'Chiều Hiền Hội Thông' ≈ 'Chiêu Hiền Hội Thông' (typo 1 ký tự) |
| W15 | W1 | 'Long Hoa Đạo Sơ' primary; 'Cửu Đảnh Tố' absent |
| W16 | W1 | 'Am Chủ Tích Thúy Vĩnh' primary (prefix "Am Chủ" = temple abbot, mixed label); 'Đăng Vân Siêu Cập' absent |
| W17 | W1 | 'Giác A' primary (abbreviated/wrong); 'Đông Sơn Tề Vĩ' absent |
| W18 | W1 | 'Đàm Châu Hoa Lâm' primary; 'Kinh Triệu Thi Lợi' absent |
| W19 | W1 + W5 | 'Vân Môn Hải Yến' primary; TTL subject='van_mon_hai_yen' ≠ DB id='phung_tuong_thach_tru' — slug mismatch critical |
| W20 | W1 | 'Ngũ Đài Ẩn Phong' primary; 'Thạch Củng Huệ Tạng' absent |
| W21 | W1 | 'Long Nha Tông Mật' primary; 'Thiên Đồng Phổ Giao' absent |
| W22 | W1 | 'Nguyệt Chưởng Trí Uyên' primary; 'Thọ Thánh Sở Văn' absent |
| W23 | W1 | 'Trì Châu Lỗ Tổ Giáo' = filename-derived name; DB name_vi='Am Chủ Phúc Bồn' (alt canonical name) |

**Distribution:**
- W1 (WRONG_SELF_LABEL): 19 cases (W01, W02 partial, W03, W06-W23 most)
- W2 (CROSS_FILE_LABEL): 1 case (W05 — in-scope)
- W3 (WORD_ORDER): 1 case (W04)
- W4 (NON_PERSON): 1 case (W14)
- W5 (SLUG_MISMATCH): 2 cases (W04, W19)
- W6 (FROZEN): 1 case (W02 — D4)

---

## E. Identity Evidence

### Root cause pattern chung

Phần lớn TTL files (đặc biệt W1 cases) cho thấy cùng một pattern:
```turtle
# PATTERN SAI — thấy trong hầu hết W1 cases:
<ex:monk/ten_subject_monk> a ex:Monk ;
    rdfs:label "Tên Thầy Của Subject"@vi ;  ← TEACHER's name, NOT subject's own!
    pth:hasTeacher <ex:monk/ten_thay> .

<ex:monk/ten_thay> rdfs:label "Tên Thầy Của Subject"@vi .
```

Cụ thể, **rdfs:label dòng đầu tiên của subject thường là tên THẦY (teacher) của subject**, không phải tên của subject. Đây là lỗi cấu trúc TTL nhất quán xuyên suốt 19 files.

### W05 — minh_hai_phap_bao (in-scope, đặc biệt)

TTL labels extraction (my audit): **['Minh Hải Pháp Bảo', 'Nguyên Thiều Thọ Tông', 'Thiệt Dinh Ân Triêm', ...]** (24 labels total)

- Self-label đầu tiên = **'Minh Hải Pháp Bảo'** ← ĐÚNG
- Preflight báo L1 với current='Nguyên Thiều **Siêu Bạch**' (x6 sources)
- 'Nguyên Thiều Siêu Bạch' KHÔNG xuất hiện trong label list của TTL này
- Interpretation: **6 OTHER TTL files reference minh_hai_phap_bao's URI và gán label 'Nguyên Thiều Siêu Bạch' cho URI đó** — cross-file label collision, không phải lỗi trong TS-Minh-Hai-Phap-Bao.ttl chính
- in=6 từ audit confirms: 6 incoming relations đến minh_hai_phap_bao từ các file khác
- **ETL consequence:** ETL đọc TTL của file và extract name từ self-label → name_vi sẽ là 'Minh Hải Pháp Bảo' (ĐÚNG), KHÔNG bị ảnh hưởng bởi labels trong 6 files khác

### W04 — khanh_thien_thu_long (slug mismatch)

- DB id: `khanh_thien_thu_long` (từ filename TS-Khanh-Thien-Thu-Long)
- TTL subject URI: `thien_khanh_thu_long` (word-order reversed)
- Nếu ETL scope expand sang file này: ETL sẽ INSERT row `thien_khanh_thu_long` (new), không UPDATE `khanh_thien_thu_long` (existing) → **duplicate row risk**
- Hiện tại NOT in old/ → chưa ảnh hưởng

### W19 — phung_tuong_thach_tru (slug mismatch nghiêm trọng hơn)

- DB id: `phung_tuong_thach_tru`
- TTL subject URI: `van_mon_hai_yen` — **KHÁC HOÀN TOÀN** (không phải word-order, là tên khác)
- 'Vân Môn Hải Yến' là một thiền sư khác
- TTL cần inspect thủ công để xác định đây là wrong content hay wrong URI
- NOT in old/ → ETL không xử lý hiện tại

### W02 + W09 — dila_id=A010511 (shared, D4)

- W02: `dam_chau_bao_cai_uoc` có dila_id=A010511
- W09: `the_nham_ton_tho` cũng có dila_id=A010511
- Đây là một trong 24 L5 non-blocking dila_id duplicate warnings
- D4 task (A010511) đang frozen → không sửa

---

## F. ETL Consequence Analysis

### F.1 — Scope Analysis: 22/23 Warnings Ngoài ETL Scope

ETL chỉ xử lý files trong `data/ttl/old/` (16 files). Toàn bộ 22/23 warnings là cho files trong `data/ttl/` (root) — **NGOÀI scope ETL**.

| Scope | Warning count | Tác động lên ETL production |
|-------|-------------|---------------------------|
| IN old/ | **1** (W05 only) | Trực tiếp — ETL sẽ xử lý |
| NOT in old/ | **22** (W01-W04, W06-W23) | KHÔNG — false positives cho ETL gate |

**Conclusion:** Preflight hiện tại over-broad — nó check ALL TTL files nhưng ETL chỉ xử lý 16 files trong old/.

### F.2 — W05 ETL Risk Assessment

W05 (minh_hai_phap_bao) là warning duy nhất trong ETL scope.

| Dimension | Analysis | Risk |
|-----------|----------|------|
| name_vi corruption | TTL self-label = 'Minh Hải Pháp Bảo' (đúng) → ETL set name_vi đúng | **LOW** |
| dila_id loss | dila_id='' (không có), T217 guard snapshot/restore | **NONE** |
| status loss | status='pending', T217 guard restore | **NONE** |
| outgoing rels (15) | ttl_filename='TS-Minh-Hai-Phap-Bao' → scoped DELETE + reinsert từ TTL | **LOW** (re-processed) |
| incoming rels (6) | Từ non-old/ files → T220 guard preserves | **NONE** |
| L1 trigger source | 6 other files có cross-reference sai → unaffected by this ETL | **NONE** |

**ETL risk cho W05: LOW — không có data corruption expected nếu TTL self-label đúng.**

### F.3 — Tổng hợp ETL Impact Matrix

```
Nếu ETL chạy production (với T217+T220 guards):
├── W01-W04, W06-W23 (22 warnings, root/ files) → ZERO IMPACT
│   └── ETL không đọc các files này
└── W05 (1 warning, old/ file minh_hai_phap_bao) → LOW RISK
    ├── name_vi: 'Minh Hải Pháp Bảo' (correct self-label in TTL) ✅
    ├── dila_id: '' → T217 restore ✅
    ├── status: 'pending' → T217 restore ✅
    ├── 15 outgoing rels: re-processed from TTL content ✅ (not data loss)
    └── 6 incoming rels: preserved by T220 ✅
```

---

## G. T213 Cross-Check

T213 identifies 5 high-risk rows. Cross-check với T221:

| T213 Row | dila_id | T221 hit | Finding |
|----------|---------|----------|---------|
| minh_hai_phap_bao | '' | **W05** (in-scope!) | Self-label đúng trong TTL; L1 trigger từ 6 external files |
| thai_binh_hue_can_phat_giam | '' | NONE | Không có TTL label warning |
| phat_y_linh_nhac | '' | NONE | Không có TTL label warning |
| thien_tue_bao_chuong | '' | NONE | Không có TTL label warning |
| dao_tin | '' | NONE | Không có TTL label warning |

T213 rows thai_binh_hue_can_phat_giam và phat_y_linh_nhac (ID/name mismatch C5 cases) **không bị ảnh hưởng bởi 23 TTL label warnings**. Chúng không có TTL label conflict.

**Kết luận G:** Chỉ minh_hai_phap_bao trong T213 high-risk set có TTL warning, và đây là W2 (cross-file label, không phải self-label corruption).

---

## H. T217 / T220 Interaction

### H.1 — T217 Guard

T217 snapshot/restore bảo vệ:
- `dila_id` của tất cả 1507 VNPA rows
- `status` của tất cả 1507 rows

T217 KHÔNG bảo vệ `name_vi`. Nếu ETL extract name_vi sai từ TTL → T217 không cứu được.

**Với W05:** TTL self-label = 'Minh Hải Pháp Bảo' (đúng). ETL sẽ set name_vi='Minh Hải Pháp Bảo'. T217 không cần can thiệp cho name_vi.

### H.2 — T220 Guard

T220 scoped DELETE bảo vệ:
- `vn_person_relations` WHERE ttl_filename NOT IN old/stems → 1929 rows preserved
- minh_hai_phap_bao's 6 incoming rels (từ non-old/ files) → PRESERVED ✅
- minh_hai_phap_bao's 15 outgoing rels (ttl_filename='TS-Minh-Hai-Phap-Bao') → scoped DELETE + reinsert from TTL

### H.3 — Combination Effect

Với T217 + T220 guards active:
- W05 (only in-scope warning): expected outcome = SAFE
- 22 out-of-scope warnings: ETL không đọc → no interaction

---

## I. Safe-for-ETL Set

Dựa trên F.2 và H.1-H.3:

**22 warnings này là SAFE-FOR-ETL (không cần fix trước khi chạy ETL):**
W01, W02 (D4, ngoài scope), W03, W04, W06, W07, W08, W09, W10, W11, W12, W13, W14, W15, W16, W17, W18, W19, W20, W21, W22, W23

Tất cả 22 đều ngoài `data/ttl/old/` → ETL production không đọc → không ảnh hưởng.

**W05 (minh_hai_phap_bao):**
- IN scope nhưng CONDITIONALLY SAFE (self-label đúng trong TTL, T217+T220 guards active)
- Admin cần acknowledge W05's cross-file label issue sẽ remain unsolved sau ETL

---

## J. Blocked Set

Không có warning nào HARD-BLOCKED cho production ETL nếu điều kiện Section L được thỏa.

**Tuy nhiên các issues sau cần separate follow-up:**

| Issue | Files affected | Priority |
|-------|---------------|----------|
| W1: 19 TTL files có wrong self-label | W01,W03,W06-W23 | HIGH (separate task) |
| W5: 2 slug mismatches | W04 (word-order), W19 (wrong URI) | CRITICAL if scope expands |
| W6: D4 frozen (W02, W09) | A010511 shared dila_id | Awaiting Admin D4 decision |
| W4: Non-person labels | W14 (temple names in rdfs:label) | MEDIUM |

---

## K. Admin Decision Matrix

### K.1 — Để chạy Production ETL ngay (3 options)

| Option | Mô tả | Effort | Risk |
|--------|-------|--------|------|
| **K-A** | Fix preflight: chỉ check files trong `old/` scope | Low (1 code change) | Zero |
| **K-B** | Run ETL với `--skip-preflight` flag | Zero | Low (must acknowledge W05) |
| **K-C** | Fix 22 out-of-scope TTL files trước | Very High (separate task) | High effort, eliminates all warnings |

**Khuyến nghị: K-A** (narrow preflight scope to `old/`) — surgical fix, addresses root cause of 22 false positives.

### K.2 — W05 Acknowledgment (bắt buộc cho K-A hoặc K-B)

Admin phải xác nhận:
> "Tôi đã đọc T221 Section E. W05 (minh_hai_phap_bao) có self-label đúng trong TTL. L1 trigger từ 6 external files không ảnh hưởng ETL. Cho phép production ETL với T217+T220 guards."

### K.3 — D4 (W02, W09) — Separate

W02 (dam_chau_bao_cai_uoc) và W09 (the_nham_ton_tho) cùng có dila_id=A010511. D4 task phải giải quyết trước khi sửa các TTL files này. Không ảnh hưởng ETL (cả hai ngoài scope).

### K.4 — W19 Slug Mismatch — Priority Follow-up

TS-Phung-Tuong-Thach-Tru.ttl có TTL subject='van_mon_hai_yen' trong khi DB id='phung_tuong_thach_tru'. Nếu file này được thêm vào ETL scope trong tương lai, sẽ tạo wrong row. Cần inspect nội dung TTL để xác định đây là content error hay URI error. **Đây là một task riêng, không block ETL hiện tại.**

---

## L. Production ETL Gate

### L.1 — Verdict

**`PRODUCTION_ETL_CONDITIONALLY_SAFE`**

ETL production có thể chạy **với điều kiện:**

1. **Condition C1:** T217 guard active (confirmed — committed in `6ba4e95`)
2. **Condition C2:** T220 guard active (confirmed — committed in `6ba4e95`)
3. **Condition C3:** Admin acknowledge W05 per Section K.2
4. **Condition C4:** Một trong K-A hoặc K-B được chọn để unblock preflight

### L.2 — Preflight Unblock Methods

**K-A (Recommended): Narrow preflight scope**

Thay đổi `scripts/t204_ttl_preflight.py` để chỉ check files trong `data/ttl/old/` khi được gọi từ ETL. Hoặc thêm `--scope old` flag cho preflight.

Sau K-A: chỉ W05 còn được check. W05's TTL self-label đúng → preflight có thể PASS hoặc cần verify L1 check logic cho W05.

**K-B (Faster but requires Admin sign-off): --skip-preflight**

ETL đã có flag `--skip-preflight`. Dùng khi chạy production với:
```bash
python scripts/etl_ttl_person_authority.py --skip-preflight
```
Admin phải confirm K.2 trước.

### L.3 — Verdict Fields

| Field | Value |
|-------|-------|
| A. Verdict | `PRODUCTION_ETL_CONDITIONALLY_SAFE` |
| B. Blocking count | 0 (zero hard blockers) |
| C. Conditional count | 4 (C1-C4) |
| D. In-scope warnings | 1 (W05 only) |
| E. Out-of-scope false positives | 22 |
| F. T217 guard required | YES (active) |
| G. T220 guard required | YES (active) |
| H. W05 name_vi risk | LOW (self-label correct in TTL) |
| I. D4 impact on ETL | NONE (W02, W09 ngoài scope) |
| J. T213 minh_hai_phap_bao | W2 — cross-file, not self-label error |
| K. Recommended preflight fix | K-A (narrow to old/ scope) |
| L. Alternative | K-B (--skip-preflight + Admin sign-off) |
| M. Separate follow-up tasks | W1 TTL fixes (19 files), W5 slug mismatches (2 files), D4 resolution |
| N. DB unchanged | YES — a2e762c8... |

---

## M. Mutation Proof

**Tất cả thao tác trong T221 là READ-ONLY:**

1. `t221_audit2.py` kết nối DB với `file:...?mode=ro` (SQLite read-only URI)
2. Không có `INSERT`, `UPDATE`, `DELETE`, `DROP` statement nào được thực thi
3. Không có `git add`, `git commit`, hoặc ETL nào được chạy
4. Không có VPS access nào
5. DB SHA256 = `a2e762c8a1c0f50a159e573924644cda0894f1aa6772ee8e1ae43329178cc96a` (unchanged — same as T220 baseline)
6. Audit script (temp file tại `C:\Users\NAMTHI~1\AppData\Local\Temp\claude\t221_audit2.py`) không thay đổi project files

**Không có file nào trong project bị sửa ngoài file artifact này.**

---

## N. Recommended Next Task

### N.1 — Cần Admin Review Ngay

**Admin cần quyết định trước khi tiếp tục:**

1. **Chọn K-A hay K-B** để unblock preflight?
   - K-A: "Sửa preflight script để chỉ check old/ scope" → cần approve task mới
   - K-B: "Dùng --skip-preflight với sign-off" → confirm Section K.2

2. **Acknowledge W05** (minh_hai_phap_bao): Section K.2

### N.2 — Sau khi Admin Unblock

1. **T222 (nếu chọn K-A):** Sửa `scripts/t204_ttl_preflight.py` — add `--scope` parameter, default to old/ khi gọi từ ETL. Chạy lại preflight verify zero blocking warnings cho old/ scope.

2. **T222/T223 (nếu chọn K-B):** Chạy production ETL lần đầu với T217+T220+skip-preflight. Verify output, spot-check DB rows.

3. **T-TTL-FIX (separate, low urgency):** Fix 19 W1 TTL files (wrong self-labels). Fix 2 W5 slug mismatches. Separate task, không block ETL.

4. **D4:** Admin cần resolve A010511 (dam_chau_bao_cai_uoc vs the_nham_ton_tho) trước khi fixing W02/W09.

---

**STOP. DO NOT RUN PRODUCTION ETL. DO NOT COMMIT THIS ARTIFACT. WAIT FOR ADMIN REVIEW.**

*Artifact generated: 2026-10-04 | T221 | READ-ONLY | SHA: a2e762c8...*


## Current follow-up — 2026-10-11

Future ETL safety is tracked by [T357](../../tasks/T357-vnpa-etl-safety-remediation.md), former_ids:[T223] for the production-report branch. Any --skip-preflight recommendation above is historical and does not authorize a new run. The approved plan requires read-only fail-closed preflight and exact file/hash/warning acknowledgment before any writable connection; missing preflight module or changed scope must stop. This update changes no TTL/DB and reruns no historical audit.

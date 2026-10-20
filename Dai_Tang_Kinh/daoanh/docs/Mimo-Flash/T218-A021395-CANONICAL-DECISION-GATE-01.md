# T218 — A021395 Canonical Decision Gate

**Task ID:** T218-A021395-CANONICAL-DECISION-GATE-01  
**Ngày:** 2026-10-02  
**Mode:** READ-ONLY ADMIN DECISION GATE  
**Phụ thuộc:** T215 (PASS), T217 (PASS, commit `a5e495a`)

---

## A. Baseline

| | Giá trị |
|--|---------|
| **HEAD** | `a5e495a` |
| **Branch** | `master` |
| **Production DB SHA256** | `da30a659c3be7276ac950427b437bf4beeab67e76d1c419b7f1f9998d75ce795` |
| **T215 spot check** | chung_son_dao_long=A030596 ✓, phong_huyet_dien_chieu=A004981 ✓, dam_chau_dai_xuyen=A020018 ✓, dong_son_te_vi=A021350 ✓ |
| **DB changed from T217** | Chênh lệch SHA so với T217 (`da4d246...`) — do WAL checkpoint tự nhiên, không phải mutation |

**Note SHA:** SQLite WAL checkpoint thay đổi SHA khi mở connection đọc. Không có mutation nào được thực hiện từ T217.

---

## B. Row Inventory — dila_id='A021395' (3 rows)

### Row 1: `alias_A021395`
| Field | Giá trị |
|-------|---------|
| id | `alias_A021395` |
| dila_id | `A021395` |
| name_vi | `Ngũ Tổ Pháp Diễn` |
| name_zh | `法演` |
| status | `alias_vi_suffix` |
| ttl_filename | `TS-Ngu-To-Phap-Dien` |
| biographical_note_vi | NULL |
| dharma_lineage | NULL |
| generation_order | NULL |
| appellations | NULL |
| birth_year | NULL |
| death_year | NULL |
| created_at | `2026-09-14 09:28:47` |
| vn_person_relations | **0** |
| person_gen_computed | **0** |
| **T200 status** | Alias row — không tham gia tiebreak primary |

### Row 2: `bao_an_phap_dien`
| Field | Giá trị |
|-------|---------|
| id | `bao_an_phap_dien` |
| dila_id | `A021395` |
| name_vi | `Báo Ân Pháp Diễn` |
| name_zh | `` (rỗng) |
| status | `pending` |
| ttl_filename | `TS-Bao-An-Phap-Dien` |
| dharma_lineage | `Dòng Lâm Tế Dương Kỳ` |
| generation_order | `51` |
| biographical_note_vi | Thiền sư Pháp Diễn ở Báo Ân tại Đinh Châu, vốn người xứ Quả Châu *(trích dẫn Thiền uyển tập anh)* |
| birth_year | NULL |
| death_year | NULL |
| created_at | `2026-09-28T15:09:08` |
| Teacher (relations) | `dong_lam_dao_nhan` (Đông Lâm Đạo Nhan) |
| vn_person_relations | **2** (hasTeacher, được tham chiếu bởi Đông Lâm) |
| person_gen_computed | gen_sect=7, gen_lamte=51, gen_thientong=88 |

### Row 3: `tu_to_phap_dien`
| Field | Giá trị |
|-------|---------|
| id | `tu_to_phap_dien` |
| dila_id | `A021395` |
| name_vi | `Tứ Tổ Pháp Diễn` |
| name_zh | `` (rỗng) |
| status | `pending` |
| ttl_filename | `TS-Tu-To-Phap-Dien` |
| dharma_lineage | `Dòng Lâm Tế Hoàng Long` |
| generation_order | `46` |
| biographical_note_vi | Thiền sư Pháp Diễn ở núi Tứ Tổ tại Kỳ Châu, vốn người ở Quế Châu *(trích dẫn Thiền uyển tập anh)* |
| birth_year | NULL |
| death_year | NULL |
| created_at | `2026-09-28T15:09:08` |
| Teacher (relations) | `hoang_long_hue_nam` (Hoàng Long Huệ Nam) |
| vn_person_relations | **2** (hasTeacher, được tham chiếu bởi Hoàng Long) |
| person_gen_computed | gen_sect=2, gen_lamte=46, gen_thientong=83 |

---

## C. Full "Pháp Diễn" Universe trong DB

Ngoài 3 rows A021395, còn **2 rows liên quan** cũng mang tên Pháp Diễn / 法演:

| id | dila_id | name_vi | status | source |
|----|---------|---------|--------|--------|
| `alias_A000733` | A000733 | Ngũ Tổ Pháp Diễn | alias_vi_suffix | TS-Ngu-To-Phap-Dien |
| `ngu_to_phap_dien` | **A036842** | Ngũ Tổ Pháp Diễn | pending | TS-Ngu-To-Phap-Dien |

**`ngu_to_phap_dien` (A036842):** Đây là entity CHÍNH cho Ngũ Tổ Pháp Diễn (法演, ?-1104). Có 32 relations, tiểu sử đầy đủ (sinh ~1024 tại Miên Châu, tịch 1104), thầy=Bạch Vân Thủ Đoan, đệ tử gồm Viên Ngộ Khắc Cần, Thái Bình Huệ Cần, v.v.

⇒ **Tổng số DILA IDs cho nhóm "Pháp Diễn": 3 IDs (A000733, A021395, A036842).**

---

## D. Identity Evidence

### Bằng chứng từ DB và TTL (LOCAL only, không có external DILA call)

#### D1. `bao_an_phap_dien` vs `tu_to_phap_dien` — có phải cùng người không?

| Tiêu chí | bao_an_phap_dien | tu_to_phap_dien |
|---------|------------------|-----------------|
| Địa danh | **Báo Ân**, Đinh Châu | **Tứ Tổ** Sơn, Kỳ Châu |
| Quê quán | Quả Châu | Quế Châu |
| Thầy | **Đông Lâm Đạo Nhan** | **Hoàng Long Huệ Nam** |
| Dòng pháp | **Dương Kỳ** | **Hoàng Long** |
| Thế hệ Lâm Tế | **51** | **46** |
| Thế hệ Thiền Tông | **88** | **83** |

**FACT:** Hai người khác nhau. Khác thầy, khác dòng pháp, khác địa danh, khác thế hệ (chênh 5 đời). Không thể là cùng một người.

**FACT:** Cả hai đều có tên Dharma là "Pháp Diễn" (法演) — đây là tên Dharma thông dụng, không phải định danh duy nhất.

**FACT:** `ngu_to_phap_dien` (A036842) là Ngũ Tổ Pháp Diễn lịch sử (1024-1104), thầy của Viên Ngộ Khắc Cần. Không liên quan đến A021395.

#### D2. Prefix chùa/núi là gì?

**INFERENCE:** Tiền tố "Báo Ân" và "Tứ Tổ" là **địa danh chùa/núi nơi vị tăng trú trì** — đây là convention đặt tên thiền sư Việt Nam theo địa danh. Không phải tước hiệu hay biệt danh cho cùng người.

**FACT:** "Báo Ân Pháp Diễn" = Thiền sư Pháp Diễn tại **chùa Báo Ân**, Đinh Châu.  
**FACT:** "Tứ Tổ Pháp Diễn" = Thiền sư Pháp Diễn tại **núi Tứ Tổ**, Kỳ Châu.

#### D3. `alias_A021395` — nguồn gốc

**INFERENCE:** Row `alias_A021395` (status='alias_vi_suffix') được tạo bởi quy trình T200 tie-break, KHÔNG phải từ TTL parse trực tiếp. Đây là alias phụ khi T200 phát hiện có DILA ID A021395 liên kết với tên "Ngũ Tổ Pháp Diễn" — nhưng `ngu_to_phap_dien` đã có dila_id=A036842. T200 tạo alias với dila_id=A021395 trỏ về ttl_filename='TS-Ngu-To-Phap-Dien'. Đây là row không có thực thể hậu thuẫn.

#### D4. "SAME PERSON" classification trong T200

**UNRESOLVED:** T218 spec ghi "A021395 has already been classified as SAME PERSON." Nhưng bằng chứng trong DB cho thấy `bao_an_phap_dien` và `tu_to_phap_dien` là hai người khác nhau. Không tìm thấy record T200 tiebreak có dila_id='A021395' (bảng tiebreak không tồn tại độc lập). Classification "SAME PERSON" có thể xuất phát từ phiên trước (T206/T207) nhưng không có evidence trail trong DB hiện tại.

#### Tổng kết Identity Evidence

| Tuyên bố | Loại | Kết quả |
|---------|-------|---------|
| bao_an_phap_dien ≠ tu_to_phap_dien | FACT | Confirmed (khác thầy/dòng/thế hệ) |
| ngu_to_phap_dien (A036842) ≠ A021395 | FACT | Confirmed (khác DILA ID, khác thầy) |
| alias_A021395 là row thực chất | INFERENCE | Không — là alias T200, 0 relations |
| A021395 trong DILA = ai? | UNRESOLVED | Không có local evidence đủ mạnh |

---

## E. Candidate Quality Matrix

| | alias_A021395 | bao_an_phap_dien | tu_to_phap_dien |
|--|---------------|------------------|-----------------|
| **name_zh** | `法演` ✓ | `` (rỗng) ⚠️ | `` (rỗng) ⚠️ |
| **name_vi** | `Ngũ Tổ Pháp Diễn` ← sai prefix ❌ | `Báo Ân Pháp Diễn` ✓ | `Tứ Tổ Pháp Diễn` ✓ |
| **biographical_note_vi** | NULL ❌ | Có (ngắn) ✓ | Có (dài) ✓✓ |
| **dharma_lineage** | NULL ❌ | Dương Kỳ ✓ | Hoàng Long ✓ |
| **generation_order** | NULL ❌ | 51 ✓ | 46 ✓ |
| **status** | alias_vi_suffix ⚠️ | pending | pending |
| **source** | T200 alias | TTL + DB | TTL + DB |
| **vn_person_relations** | **0** ❌ | 2 ✓ | 2 ✓ |
| **person_gen_computed** | 0 ❌ | 1 (Dương Kỳ gen 51) | 1 (Hoàng Long gen 46) |
| **T217 scope** | IN scope (TS-Ngu-To-Phap-Dien IN old/) | **OUT of scope** ✓ | **OUT of scope** ✓ |
| **Risk if deleted** | Thấp (0 references) | Trung bình (2 relations) | Trung bình (2 relations) |

**Nhận xét:**  
- `alias_A021395` là row yếu nhất: không có data, 0 relations, tên prefix sai (gọi là "Ngũ Tổ" trong khi A021395 không phải Ngũ Tổ).
- `tu_to_phap_dien` có biographical note dài nhất và đầy đủ nhất.
- `bao_an_phap_dien` có biographical note ngắn hơn.
- Cả hai đều thiếu name_zh — đây là điểm yếu cần lưu ý.

---

## F. Reference Impact

### Bảng vn_person_relations

| Row | Loại | Count | Chi tiết |
|-----|------|-------|---------|
| `alias_A021395` | references | 0 | Không ai trỏ đến |
| `bao_an_phap_dien` | person_id | 1 | hasTeacher → dong_lam_dao_nhan |
| `bao_an_phap_dien` | target_id | 1 | Đông Lâm Đạo Nhan hasDisciple → bao_an_phap_dien |
| `tu_to_phap_dien` | person_id | 1 | hasTeacher → hoang_long_hue_nam |
| `tu_to_phap_dien` | target_id | 1 | Hoàng Long Huệ Nam hasDisciple → tu_to_phap_dien |

### person_gen_computed

| Row | Lineage | gen_sect | gen_lamte | gen_thientong |
|-----|---------|----------|-----------|---------------|
| `bao_an_phap_dien` | Dương Kỳ | 7 | 51 | 88 |
| `tu_to_phap_dien` | Hoàng Long | 2 | 46 | 83 |
| `alias_A021395` | — | — | — | — |

### canonical_decision, lineage_edge_consensus, lineage_primary_teacher, monk_dict

Không có rows nào cho các candidates này trong các bảng trên.

### Kết luận: nếu chọn canonical và "xóa/repoint" row còn lại

- Xóa `alias_A021395`: 0 dangling reference. An toàn tuyệt đối.
- Repoint `bao_an_phap_dien` → cần cập nhật `vn_person_relations.target_id` (1 row từ Đông Lâm Đạo Nhan) và `vn_person_relations.person_id` (1 row).
- Repoint `tu_to_phap_dien` → cần cập nhật `vn_person_relations.target_id` (1 row từ Hoàng Long Huệ Nam) và `vn_person_relations.person_id` (1 row).

---

## G. T217 ETL Survivability

| Row | ttl_filename | Trong data/ttl/old/? | T217 scope? | Ảnh hưởng |
|-----|-------------|----------------------|-------------|-----------|
| `alias_A021395` | TS-Ngu-To-Phap-Dien | **YES** ✓ | IN | Nếu ETL chạy lại: row bị DELETE, ETL recreate `ngu_to_phap_dien` (không phải alias) → alias_A021395 ABSENT sau ETL. Restore logic: row vắng mặt → skip → alias bị mất vĩnh viễn. |
| `bao_an_phap_dien` | TS-Bao-An-Phap-Dien | NO | OUT | An toàn. dila_id=A021395 bảo tồn bởi T217 guard nếu row tồn tại. |
| `tu_to_phap_dien` | TS-Tu-To-Phap-Dien | NO | OUT | An toàn. dila_id=A021395 bảo tồn bởi T217 guard nếu row tồn tại. |

**T217 Risk Summary:**

- Nếu Admin chọn canonical = `bao_an_phap_dien`: dila_id=A021395 trên row này SAFE bởi T217.
- Nếu Admin chọn canonical = `tu_to_phap_dien`: dila_id=A021395 trên row này SAFE bởi T217.
- `alias_A021395` sẽ bị mất khi ETL chạy lại — dù Admin chọn option nào. Cần quyết định trước ETL.
- Không cần cơ chế tombstone/curation thêm cho `bao_an_phap_dien` hay `tu_to_phap_dien` (đã covered bởi T217).

---

## H. Admin Options

### OPTION A: canonical = `bao_an_phap_dien`

**Ý nghĩa:** DILA A021395 = Thiền sư Pháp Diễn tại chùa Báo Ân, Đinh Châu (Dương Kỳ, gen 51).

**Consequences:**

| Table | PK | Column | Old | New | Reason |
|-------|-----|--------|-----|-----|--------|
| vn_person_authority | bao_an_phap_dien | status | pending | verified | Canonical được xác nhận |
| vn_person_authority | tu_to_phap_dien | dila_id | A021395 | '' | Remove incorrect assignment |
| vn_person_authority | alias_A021395 | — | DELETE row | — | 0 references, alias không cần thiết |

- Aliases không cần tạo thêm.
- Không cần rewrite vn_person_relations (bao_an_phap_dien vẫn là ID).
- T200 sau khi chạy: chỉ 1 row active cho A021395 → không có tiebreak conflict.
- T166 canonical lock: cần thêm bao_an_phap_dien vào locked set nếu applicable.
- Rollback complexity: thấp — chỉ restore dila_id='A021395' trên tu_to_phap_dien.

**Rủi ro:** Chưa có bằng chứng LOCAL xác nhận DILA A021395 = Báo Ân. Cần DILA lookup để verify.

---

### OPTION B: canonical = `tu_to_phap_dien`

**Ý nghĩa:** DILA A021395 = Thiền sư Pháp Diễn tại núi Tứ Tổ, Kỳ Châu (Hoàng Long, gen 46).

**Consequences:**

| Table | PK | Column | Old | New | Reason |
|-------|-----|--------|-----|-----|--------|
| vn_person_authority | tu_to_phap_dien | status | pending | verified | Canonical được xác nhận |
| vn_person_authority | bao_an_phap_dien | dila_id | A021395 | '' | Remove incorrect assignment |
| vn_person_authority | alias_A021395 | — | DELETE row | — | 0 references, alias sai prefix |

- T200 sau khi chạy: chỉ 1 row active cho A021395 → không có tiebreak conflict.
- T166 canonical lock: cần thêm tu_to_phap_dien vào locked set nếu applicable.
- Rollback complexity: thấp — chỉ restore dila_id='A021395' trên bao_an_phap_dien.

**Rủi ro:** Chưa có bằng chứng LOCAL xác nhận DILA A021395 = Tứ Tổ. Cần DILA lookup để verify.

---

### OPTION C: Giữ row khác làm canonical

Không có row khác hiện đang mang dila_id='A021395'. Option C = None applicable.

---

### OPTION D: Defer — Evidence insufficient

**Ý nghĩa:** Không đủ bằng chứng LOCAL để xác định DILA A021395 = Báo Ân hay Tứ Tổ.

**Consequences:** Giữ nguyên trạng thái hiện tại. Không thay đổi DB.

**Khi nào unblock:** Sau khi Admin tra DILA trực tiếp (A021395 = ?).

---

### OPTION E (bổ sung): Xóa A021395 khỏi cả hai rows

**Ý nghĩa:** Không đủ bằng chứng rằng A021395 thuộc về bao_an_phap_dien HOẶC tu_to_phap_dien. Assignment có thể là lỗi từ T206/T207.

**Consequences:**

| Table | PK | Column | Old | New | Reason |
|-------|-----|--------|-----|-----|--------|
| vn_person_authority | bao_an_phap_dien | dila_id | A021395 | '' | Unverified assignment |
| vn_person_authority | tu_to_phap_dien | dila_id | A021395 | '' | Unverified assignment |
| vn_person_authority | alias_A021395 | — | DELETE row | — | Alias không còn ý nghĩa |

**Rủi ro:** Mất assignment A021395. Nếu sau đó verify được, cần restore.

---

## I. Unresolved Evidence

| Câu hỏi | Trạng thái | Cách giải quyết |
|---------|-----------|-----------------|
| DILA A021395 = Báo Ân hay Tứ Tổ hay khác? | **UNRESOLVED** | Cần Admin tra DILA |
| Tại sao cả hai rows có cùng dila_id=A021395? | **UNRESOLVED** | Có thể là mapping lỗi từ T207 |
| alias_A021395 tên "Ngũ Tổ Pháp Diễn" có chính xác không? | **INFERENCE: SAI** | Ngũ Tổ Pháp Diễn = A036842, không phải A021395 |
| A000733 vs A036842: cùng người (ngu_to_phap_dien)? | PROBABLE nhưng chưa verify | Cần DILA lookup A000733 |

---

## J. Admin Decision Sheet

```
T218 — QUYẾT ĐỊNH CẦN THỰC HIỆN:

[ ] OPTION A: canonical = bao_an_phap_dien
    → xóa dila_id khỏi tu_to_phap_dien + xóa alias_A021395

[ ] OPTION B: canonical = tu_to_phap_dien  
    → xóa dila_id khỏi bao_an_phap_dien + xóa alias_A021395

[ ] OPTION D: DEFER — tra DILA trước
    → Vào DILA: tìm A021395, xác nhận tên đầy đủ và thầy của person đó
    → Sau khi biết = Báo Ân → OPTION A / = Tứ Tổ → OPTION B

[ ] OPTION E: Xóa A021395 khỏi cả hai rows (cần justification)
```

**Thông tin cần tra DILA (nếu chọn OPTION D):**

1. DILA Person ID: **A021395** — tên Hán, thầy, đệ tử, thế kỷ, triều đại?
2. DILA Person ID: **A000733** — có phải là Ngũ Tổ Pháp Diễn (cùng A036842) không?

---

## K. Regression Plan (sau khi Admin chọn option)

| Test | Lý do |
|------|-------|
| `npm run test:t217` | Verify T217 preservation guard còn nguyên |
| `npm run test:t200` | Verify tiebreak không conflict sau khi chỉ còn 1 active row |
| `npm run audit:t166` | Verify canonical lock không broken |
| `npm run test:translation` | Regression toàn bộ |
| Manual: vn_person_relations | Verify không dangling reference sau mutation |
| Manual: person_gen_computed | Verify generation chain không broken |

---

## L. Không thực hiện bất kỳ mutation nào trong T218

- DB mutation = **0** ✓
- Code mutation = **0** ✓
- External LLM = **0** ✓
- External DILA transmission = **0** ✓

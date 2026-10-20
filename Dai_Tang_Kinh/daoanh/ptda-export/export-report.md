# PTDA Export Report (read-only)

Nguồn: `data/lineage.db` mở `mode=ro` — KHÔNG ghi, KHÔNG sửa, KHÔNG merge.

- Bảng cạnh: `lineage_edge_consensus` (`relation_type='dharma_transmission'`)
- Bảng người: `entity` (PERSON) + `vn_person_authority` (nhãn TTL)

## 1. Tổng số person
- Tổng số person xuất: **23285** (chỉ người tham gia cạnh `dharm_successor_of`)
- Có DILA ID: **23285** (100%) — id trong bảng chính là DILA ID
- Thiếu DILA ID: **0**
- Có Marcus ID: **11487** (49.3%)
- Có nhãn TTL (vn_person_authority): **1048** (4.5%)
- Không có nhãn tiếng Việt: **7** (0.0%)
- Không có bản ghi trong `entity` (chỉ có id trong cạnh): **7** ['A018088', 'A019811', 'A040634', 'A046267', 'A046588', 'A048535', 'A048871']

## 2. Tổng số cạnh dharm_successor
- Tổng số cạnh: **23411**
- Có DILA ID cả 2 đầu: **23411** (100%)
- Thiếu DILA ID 1 đầu: **0**
- Thiếu DILA ID cả 2 đầu: **0**

## 3. Cạnh theo nguồn (một cạnh có thể nhiều nguồn)
- dila: **23014**
- marcus: **11169**
- ttl: **542**
- lineage: **0**

## 4. Trạng thái cạnh
- confirmed: **11181**
- unconfirmed: **12230**
- conflict: **0**

## 5. Trùng lặp / đảo chiều
- Cặp (thầy,trò) trùng: **0**
- Cặp đảo chiều (A→B và B→A cùng tồn tại): **0**

## 6. Ghi chú phạm vi
- Chỉ xuất `dharm_successor_of`. CÁC quan hệ `ordained_by`, `tonsure_master_of`,
  `studied_under`, `associated_with` bị loại (không tồn tại trong `lineage_edge_consensus`;
  `lineage_edge_assertions` chỉ chứa `da:isTeacherOf` và đã được tổng hợp vào consensus).
- Person bị giới hạn ở người tham gia cạnh truyền pháp (quyết định của Admin).
- `entity.PERSON` toàn bộ là 48.673; trong đó 23.285 tham gia cạnh.
- `label_vi` thứ tự ưu tiên: `vn_person_authority.name_vi` (verified > pending > auto_ttl)
  → `people.name_vi` → `ai_person_name.name_vi_ai` → `entity.alias_vi`.
- `sources`: dila/marcus/ttl từ cờ consensus + vn_person_authority; `lineage` = có trong cây truyền pháp.


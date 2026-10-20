# T274/T275 Giải Pháp Tối Ưu — Option B: Mở Rộng DILA Base Pool

**Đề xuất:** Chọn **Option B** (mở rộng DILA base pool) làm giải pháp chính cho T274/T275.

**Lý do:** Phù hợp nhất với mục đích dự án (SSOT, bảo tồn chính pháp, học thuật), quy trình Vibe Coding, và khả năng mở rộng 2026-2045.

---

## I. Tại Sao Option B Tối Ưu Nhất

### 1. **Single Source of Truth (SSOT) — Lõi của Dự Án**

```
Mục đích dự án: "Biến dữ liệu thô thành tri thức có cấu trúc (SSOT)"

Option A (TTL riêng):
  ❌ 2 database riêng biệt (DILA + TTL)
  ❌ Không SSOT
  ❌ Vi phạm nguyên tắc dự án

Option B (mở rộng DILA):
  ✅ 1 database thống nhất (DILA + Việt)
  ✅ SSOT = một nguồn sự thật
  ✅ Tuân thủ nguyên tắc dự án
```

### 2. **Bảo Tồn Chính Pháp — "2026-2045"**

```
Triết lý: "Hữu Tự Vô Đạo — Bất Khả Hưng Giáo"
= Truyền thừa Thiền là ONE tradition, không tách rời Việt/quốc tế

Option A: Tách Việt + quốc tế → vi phạm triết lý
Option B: Thống nhất lineage → bảo tồn chính pháp
```

### 3. **Liên Kết Học Thuật**

```
Ma Ha Ca Diếp (Ấn Độ)
  ↓ (46,004 cạnh DILA)
Thiền Tông Trung Quốc
  ↓ (TTL: Khuôn Phổ)
Khuôn Phổ (Việt Nam) ← PIVOT POINT
  ↓ (mở rộng: +1,300 cạnh TTL)
Vạn Hạnh, Diệu Trúc, ... (Sư tổ Việt)

Option B: Cạnh Việt được nối trực tiếp → khoa học, rõ ràng
Option A: Cạnh Việt riêng biệt → mất kết nối lịch sử
```

### 4. **Khả Năng Mở Rộng (2026-2045)**

```
Nếu sau này thêm:
- Thiền Tông Nhật Bản
- Thiền Tông Hàn Quốc
- Thiền Tông Tây Phương

Option A: Cần tạo TTL2, TTL3, ... (phức tạp vô hạn)
Option B: Thêm cạnh vào DILA + local_id (scalable)
```

### 5. **Phù Hợp Vibe Coding**

```
Admin no-coding được hưởng lợi:
- Option A: 2 system khác nhau → khó maintain
- Option B: 1 system → Admin dễ hiểu, QA dễ kiểm

SSOT = "một sự thật" → Admin có thể theo dõi toàn bộ dữ liệu
```

---

## II. Kế Hoạch Triển Khai Option B

### **Phase 1: Chuẩn Bị (T274)**

**Bước 1.1: Tạo Rule TTL dòng Việt Nam**
```
Input: TTL file 1,300 cạnh (hasTeacher/hasDisciple)
Output: Rule "Sư tổ Việt = TTL edge từ Khuôn Phổ"

Logic:
- Khuôn Phổ = pivot point (trong DILA + TTL)
- Từ Khuôn Phổ đi xuống = dòng Việt
- Merge với DILA trên Khuôn Phổ
```

**Bước 1.2: Tạo Local ID cho 211 Monks Việt**
```
Schema: ADD COLUMN local_id TEXT UNIQUE

Naming: vn_<monk_name_slug>
Ví dụ:
- Vạn Hạnh → vn_van_hanh
- Diệu Trúc → vn_dieu_truc

Mapping: local_id = DILA ID khi có, local_id khi không
```

**Bước 1.3: Xử Lý 48 Discrepancies**
```
Phân loại 48 monk xuất hiện ở cả DILA + TTL:
1. Chọn source ưu tiên: DILA (international) hay TTL (Việt)?
2. Sử dụng heuristic: 
   - Nếu Việt → TTL ưu tiên
   - Nếu quốc tế → DILA ưu tiên
3. Merge logic: union of edges, resolve conflicts

Kết quả: 48 monks → unified in DILA base pool
```

### **Phase 2: Xây Dựng TTL Generation Engine (T275)**

**Bước 2.1: Merge TTL vào DILA Base Pool**
```
Before: 46,004 edges (DILA only)
After:  46,004 + 1,300 = 47,304 edges (DILA + Việt)

SQL:
INSERT INTO marcus_people_link (teacher_id, student_id, source, confidence)
SELECT teacher_id, student_id, 'ttl', 0.95
FROM ttl_edges
WHERE student_id NOT IN (SELECT id FROM marcus_people_link WHERE teacher_id = ...)
```

**Bước 2.2: Xây Dựng Generation Engine v2**
```
Logic:
  1. Trace chain từ Ma Ha Ca Diếp → target monk
  2. Count edges (hợp nhất DILA + TTL)
  3. Số đời = path length

Support:
- DILA ID (quốc tế)
- Local ID (Việt)
- TTL lookup fallback
```

**Bước 2.3: Kiểm Chứng 48 Discrepancies**
```
Verify: Mỗi 48 monk có thế hệ nhất quán giữa DILA + TTL

Nếu conflict:
- DILA + TTL khác nhau → ghi log, đánh dấu
- TTL ưu tiên cho Việt (confidence cao)
- DILA ưu tiên cho quốc tế (source DILA Authority)
```

### **Phase 3: Xuất Bản (T232/T270 sau)**

**Bước 3.1: Công Bố DILA + Việt (Unified)**
```
API output:
{
  "generation": 33,
  "source": "dila+ttl_vietnam",
  "teacher_chain": [
    { "id": "A001", "name": "Ma Ha Ca Diếp", "country": "India" },
    ...
    { "id": "vn_van_hanh", "name": "Vạn Hạnh", "country": "Vietnam" }
  ]
}
```

**Bước 3.2: Audit Strict**
```
Verify:
- Không chu kỳ (cycle detection)
- Tất cả 211 Việt monks có thế hệ
- 48 discrepancies resolved
- Số dòng TTL trong base pool = 1,300
```

---

## III. Tại Sao Không Chọn A hoặc C

### **Option A (TTL Riêng): Hại Lớn**

| Tiêu Chí | Option A | Option B |
|----------|----------|----------|
| SSOT | ❌ 2 DB | ✅ 1 DB |
| Chính Pháp | ❌ Tách | ✅ Thống nhất |
| Liên Kết | ❌ Không | ✅ Có |
| Scalability | ❌ Tệ | ✅ Tốt |
| Vibe Coding | ❌ Khó | ✅ Dễ |

### **Option C (Hybrid): Phức Tạp, Khó Maintain**

```
Hybrid = 2 system, 2 logic → phức tạp
- Admin phải hiểu: "khi nào TTL, khi nào DILA?"
- QA phải test: "2 path, 2 kết quả?"
- Maintenance: "Sửa cái nào khi có bug?"

=> Không phù hợp "Vibe Coding" (admin không-code)
```

---

## IV. Rủi Ro & Khắc Phục

| Rủi Ro | Tác Động | Khắc Phục |
|--------|---------|----------|
| **Conflict resolution sai** | 48 monks thế hệ sai | Admin duyệt từng case, weighted voting |
| **TTL data lỗi** | Inheritance sai | Cross-check với DILA, confidence < 0.95 |
| **211 local_id duplicate** | ID clash | Validate unique, prefix + hash |
| **Schema change lớn** | DB migration risk | Backup trước, test migration script |

---

## V. Timeline & Effort

```
T274 (TTL Rule Design)       : 1-2 ngày
T275 (TTL Generation Engine) : 3-5 ngày
T232 (Multi-system support)  : 2-3 ngày
T270 (Lineage verification)  : 2 ngày
────────────────────────────
TOTAL: ~2 tuần (song hành)
```

---

## VI. Success Criteria

✅ **DILA base pool**: 46,004 + 1,300 = 47,304 edges  
✅ **Vietnamese monks**: 211 có local_id, thế hệ tính đúng  
✅ **48 discrepancies**: resolved, confidence > 0.90  
✅ **Audit --strict**: exit 0 (no cycles, no gaps)  
✅ **Admin satisfaction**: "1 database, 1 sự thật"  

---

## VII. Quyết Định Cần Admin

**Q1: Phê chuẩn Option B (mở rộng DILA)?**
- Answer: YES → T274/T275 proceed ngay
- Answer: NO → reconsider A hoặc C

**Q2: Confidence threshold cho TTL (0.90 vs 0.95)?**
- Answer: 0.95 (conservative, an toàn)

**Q3: Conflict resolution strategy cho 48 monks?**
- Answer: TTL ưu tiên cho Việt, DILA ưu tiên cho quốc tế

---

## Kết Luận

**Option B là giải pháp duy nhất phù hợp với:**
- ✅ Mục đích dự án (SSOT)
- ✅ Triết lý (Hữu Tự Vô Đạo)
- ✅ Bảo tồn chính pháp (2026-2045)
- ✅ Vibe Coding (không-code friendly)
- ✅ Học thuật (thống nhất, liên kết rõ)

**Khuyến nghị:** Phê chuẩn Option B, bắt đầu T274 ngay khi Admin xác nhận.

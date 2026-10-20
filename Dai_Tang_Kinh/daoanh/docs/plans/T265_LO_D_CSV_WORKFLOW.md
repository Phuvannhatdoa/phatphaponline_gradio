# T265 Lô D — CSV Workflow Triển Khai Trên Hệ Thống

## I. Quy Trình Tổng Quát (3 bước)

```
Admin điền CSV (Excel)
       ↓
Upload → POST /api/import_t265_decisions
       ↓
Backend xử lý: đọc CSV → validate → gắn DB
       ↓
QA kiểm: audit --strict xanh? (CONFLICT gốc = 285)
       ↓
T265 Lô D DONE
```

---

## II. Bước 1: Admin Điền CSV (Trên Excel)

**File:** `docs/evidence/T265_D_sample_for_admin_review.csv` (45 dòng)

**Cột cần Admin điền:**

| Cột | Kiểu | Ví dụ | Ghi chú |
|-----|------|--------|---------|
| `kiem_tra_thu_cong` | Enum | ĐÚNG / SAI / CẦN_NGUỒN | Bắt buộc, không để trống |
| `ghi_chu_them` | Text | "year lệch do TTL?", "cần source CBETA" | Optional |
| `nguoi_duyet` | Text | "namthien@gmail.com" | Auto-fill = logged user |
| `ngay_duyet` | Date | 2026-10-11 | Auto-fill = today |

**Ví dụ điền:**

```csv
group,dila_id,year,event_ids,source_refs,...,kiem_tra_thu_cong,ghi_chu_them,nguoi_duyet,ngay_duyet
B,A001234,975,"E001,E002",DILA_001,...,ĐÚNG,,namthien@gmail.com,2026-10-11
C,A005678,1050,"E003","CBETA_123",...,SAI,"year 1050 không có trong era_span",namthien@gmail.com,2026-10-11
A,A009999,1200,"E100",DILA_100,...,CẦN_NGUỒN,"cần verify từ DILA source",namthien@gmail.com,2026-10-11
```

**Workflow Admin:**
1. Mở file CSV trong Excel (charcode UTF-8)
2. Điền cột `kiem_tra_thu_cong` (45 dòng, mỗi dòng 1 giá trị)
3. Optional: Điền `ghi_chu_them` nếu cần lưu ý
4. Save → Export CSV (UTF-8, không BOM)
5. Upload file mới

---

## III. Bước 2: Tạo Endpoint Upload

**Endpoint:** `POST /daoanh/api/admin/import_t265_decisions`

### 2.1 Backend (app.py hoặc server.py)

```python
@app.route('/daoanh/api/admin/import_t265_decisions', methods=['POST'])
def import_t265_decisions():
    """
    Upload CSV (45 dòng Lô D) → áp dụng quyết định vào DB
    """
    import csv
    import io
    
    if 'file' not in request.files:
        return {"success": False, "error": "No file uploaded"}, 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return {"success": False, "error": "File phải là .csv"}, 400
    
    try:
        # 1. Đọc CSV
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        rows = list(reader)
        
        if len(rows) != 45:
            return {"success": False, "error": f"CSV phải có 45 dòng, nhận {len(rows)}"}, 400
        
        # 2. Validate & áp dụng
        applied = 0
        failed = 0
        errors = []
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        for i, row in enumerate(rows, 1):
            try:
                dila_id = row.get('dila_id', '').strip()
                decision = row.get('kiem_tra_thu_cong', '').strip()
                note = row.get('ghi_chu_them', '').strip()
                reviewer = row.get('nguoi_duyet', 'admin').strip()
                
                # 3. Validate decision
                if decision not in ['ĐÚNG', 'SAI', 'CẦN_NGUỒN']:
                    errors.append(f"Dòng {i}: decision '{decision}' không hợp lệ")
                    failed += 1
                    continue
                
                # 4. Gắn vào DB
                cursor.execute("""
                    UPDATE conflicts 
                    SET status = ?,
                        decision_note = ?,
                        reviewed_by = ?,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE dila_id = ? AND status = 'UNRESOLVED'
                """, (decision, note, reviewer, dila_id))
                
                if cursor.rowcount > 0:
                    applied += 1
                else:
                    errors.append(f"Dòng {i}: DILA ID '{dila_id}' không tìm thấy hoặc đã xử lý")
                    failed += 1
            
            except Exception as e:
                errors.append(f"Dòng {i}: {str(e)}")
                failed += 1
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "applied": applied,
            "failed": failed,
            "errors": errors[:10]  # Giới hạn 10 lỗi đầu
        }, 200
    
    except Exception as e:
        return {"success": False, "error": str(e)}, 500
```

### 2.2 Frontend (HTML form)

```html
<form id="importForm" enctype="multipart/form-data">
    <label>Upload CSV (T265 Lô D, 45 dòng):</label>
    <input type="file" id="csvFile" accept=".csv" required />
    <button type="submit">Nhập quyết định</button>
</form>

<div id="importStatus" style="display:none;">
    <p>✅ Đã áp dụng: <span id="appliedCount">0</span> / 45</p>
    <p>❌ Lỗi: <span id="failedCount">0</span></p>
    <p id="errorList"></p>
</div>

<script>
document.getElementById('importForm').onsubmit = async (e) => {
    e.preventDefault();
    
    const file = document.getElementById('csvFile').files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/daoanh/api/admin/import_t265_decisions', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('appliedCount').textContent = data.applied;
            document.getElementById('failedCount').textContent = data.failed;
            document.getElementById('errorList').textContent = 
                data.errors.length > 0 ? data.errors.join('<br/>') : '';
            document.getElementById('importStatus').style.display = 'block';
            
            if (data.failed === 0) {
                alert('✅ Nhập thành công! 45 quyết định đã gắn vào DB.');
            }
        } else {
            alert('❌ Lỗi: ' + data.error);
        }
    } catch (err) {
        alert('❌ Lỗi upload: ' + err.message);
    }
};
</script>
```

---

## IV. Bước 3: Kiểm Chứng (QA)

### 4.1 Kiểm SQL

```sql
-- Kiểm số CONFLICT đã xử lý
SELECT COUNT(*) as unresolved_conflicts
FROM conflicts 
WHERE status = 'UNRESOLVED';

-- Kỳ vọng: 285 (gốc, không tính 118 Lô D)
```

### 4.2 Chạy audit script

```bash
cd daoanh/
python scripts/audit_t265.py --strict
```

**Kỳ vọng:**
```
✅ audit --strict PASS
  - Total conflicts: 285 (gốc, UNRESOLVED)
  - Lô D (45 điều tra): 45/45 RESOLVED
  - CONFLICT gốc sau Lô D: 285 không thay đổi (vì Lô D riêng)
✅ Exit code: 0
```

### 4.3 Dashboard cập nhật

```javascript
// Progress update
const progress = {
  "T265": {
    "status": "done",
    "lo_a": {"status": "done", "count": 50},
    "lo_d": {"status": "done", "count": 118},
    "total_resolved": 168,
    "total_conflicts": 285
  }
}
```

---

## V. Rủi Ro & Khắc Phục

| Rủi ro | Khắc phục |
|--------|----------|
| **CSV có encoding sai (ANSI)** | Báo Admin: lưu lại dùng UTF-8 encoding |
| **CSV có dòng trống hoặc thiếu** | Script validate: phải = 45 dòng |
| **Admin điền value sai** (không phải ĐÚNG/SAI/CẦN_NGUỒN) | Script báo lỗi dòng nào, Admin sửa lại |
| **DILA ID không tìm thấy trong DB** | Ghi log, Admin kiểm lại CSV |
| **Mạng bị ngắt khi upload** | File form có retry button |
| **Đã apply rồi nhưng Admin apply lại** | Script kiểm `status != 'UNRESOLVED'` → skip |

---

## VI. Thứ Tự Thực Hiện

```
1️⃣ Admin điền CSV (45 dòng) — 30 phút
2️⃣ Admin upload file → POST /api/import_t265_decisions — 1 phút
3️⃣ Backend xử lý → gắn DB — 10 giây
4️⃣ QA chạy audit --strict → xác nhận — 5 phút
5️⃣ T265 Lô D DONE → cập nhật dashboard — 2 phút
```

**Tổng:** ~40 phút

---

## VII. Fallback (Nếu Upload Không Thể)

Nếu upload trực tiếp không được, Admin có thể:

1. **Copy CSV trực tiếp vào directory:**
   ```bash
   cp T265_D_sample_for_admin_review.csv daoanh/docs/evidence/
   ```

2. **Chạy script Python thay:**
   ```python
   # scripts/apply_t265_from_csv.py
   import csv
   import sqlite3
   
   csv_path = 'docs/evidence/T265_D_sample_for_admin_review.csv'
   db_path = 'data/lineage.db'
   
   with open(csv_path, 'r', encoding='utf-8') as f:
       reader = csv.DictReader(f)
       for row in reader:
           dila_id = row['dila_id']
           decision = row['kiem_tra_thu_cong']
           
           # Apply to DB
           conn = sqlite3.connect(db_path)
           conn.execute("""
               UPDATE conflicts 
               SET status = ? WHERE dila_id = ?
           """, (decision, dila_id))
           conn.commit()
           conn.close()
   ```

3. **Chạy:**
   ```bash
   python scripts/apply_t265_from_csv.py
   ```

---

## VIII. Summary (Checklist Admin)

- [ ] 1. Điền CSV: cột `kiem_tra_thu_cong` (45 dòng)
- [ ] 2. Save: UTF-8 encoding, no BOM
- [ ] 3. Upload: POST `/daoanh/api/admin/import_t265_decisions`
- [ ] 4. Kiểm kết quả: "Đã áp dụng 45 / 45" ✅
- [ ] 5. QA kiểm: `python scripts/audit_t265.py --strict` → exit 0 ✅
- [ ] 6. T265 Lô D → DONE ✅

**Khi xong bước VI, Lô D hoàn thành. Bước vào Phase 2 (bug + 13 task Lô 1 khác).**

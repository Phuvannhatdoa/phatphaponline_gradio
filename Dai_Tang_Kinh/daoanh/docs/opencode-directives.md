# Chỉ Thị OpenCode — Tích Hợp UI Đạo Ảnh

**Phiên bản:** 1.0 · 2026-08-17  
**Dành cho:** OpenCode AI Agent (non-coding admin theo dõi)  
**Design mockup:** https://claude.ai/code/artifact/a0606ab7-ae4f-4fe9-bf9b-ac3ebf3cdb55  
**Dashboard theo dõi:** http://localhost:8080/dashboard/dashboard_process.html

---

## ⚠️ QUY TẮC BẮT BUỘC — ĐỌC TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ

| # | Quy tắc |
|---|---------|
| R1 | Làm từng bước theo số thứ tự. Không làm bước N+1 khi chưa xong bước N. |
| R2 | Sau MỖI bước [LOG]: cập nhật `data/directives_progress.json` |
| R3 | Sau MỖI task hoàn thành: chạy `python scripts/build_progress_data.py` |
| R4 | **KHÔNG** chạy `git add/commit/reset` khi chưa có lệnh rõ ràng từ admin |
| R5 | **KHÔNG** đụng vào schema `data/lineage.db` trừ khi directive nói rõ |
| R6 | **KHÔNG** commit API key Gemini (`app.py` lines 1065, 1105) |
| R7 | Nếu bước nào bị blocked: ghi `status: blocked` vào task file + ghi log, rồi dừng lại báo admin |
| R8 | Mọi file chỉnh sửa: đọc toàn bộ trước khi sửa. Không sửa mù. |

---

## Cấu trúc file `data/directives_progress.json`

OpenCode cập nhật file này sau mỗi bước [LOG]:
```json
{
  "last_updated": "2026-08-17T09:00:00",
  "current_group": "SETUP",
  "current_step": 5,
  "completed_steps": [1, 2, 3, 4],
  "blocked_at": null,
  "note": "Mô tả ngắn bước vừa xong",
  "percent_total": 0
}
```

---

## Cấu trúc file log session

Mỗi task tạo 1 file: `daoanh/docs/sessions/YYYY-MM-DD_TXXX_slug.md`
```markdown
---
directive_group: TXXX
steps: 100-119
started: YYYY-MM-DD HH:MM
finished: YYYY-MM-DD HH:MM
status: done | in_progress | blocked
---
## Kết quả
- [x] Bước 100: ...
- [x] Bước 101: ...
## Số liệu thực tế
- Rows imported: X
- API test: ...
## Vấn đề / blocker
(ghi nếu có)
```

---

---

# NHÓM SETUP — Nền tảng bắt buộc (Bước 001–019)

> **Mục tiêu:** Link CSS design system, xác nhận môi trường, tạo cấu trúc tab bar cho sidebar.  
> **File chính:** `daoanh/places/index.html`  
> **Không cần backend**

---

### Bước 001 · [READ]
**Đọc toàn bộ file:** `daoanh/docs/design-spec.md`  
Đặc biệt cần nắm: Section 0 (Quy tắc vàng), Section 2 (13 component classes), Section 4 (9 bước tích hợp).  
**Hoàn thành khi:** Đã đọc xong.

---

### Bước 002 · [READ]
**Đọc toàn bộ file:** `daoanh/styles/daoanh-design.css`  
Nắm tên các token: `--da-bg`, `--da-gold`, `--da-panel`, `--da-text`, `--da-warn`.  
**Hoàn thành khi:** Đã đọc xong.

---

### Bước 003 · [READ]
**Đọc toàn bộ file:** `daoanh/places/index.html` (734 dòng)  
Ghi nhớ: tên id/class của sidebar hiện tại, cách gọi API entity detail, cách JS populate sidebar khi click marker.  
**Hoàn thành khi:** Biết id/class sidebar và hàm JS nào chạy khi chọn địa điểm.

---

### Bước 004 · [SHELL] Xác nhận servers đang chạy
```powershell
Get-NetTCPConnection -LocalPort 5000,5001,8080 -State Listen | Select LocalPort
```
**Hoàn thành khi:** 3 dòng trả về: 5000, 5001, 8080.  
**Nếu không:** Chạy servers theo hướng dẫn trong `daoanh/CLAUDE.md` phần "Khởi động local".

---

### Bước 005 · [EDIT] Link CSS design system
Mở `daoanh/places/index.html`. Tìm thẻ `<head>`. Thêm dòng sau **ngay sau thẻ `<title>`**:
```html
<link rel="stylesheet" href="/daoanh/styles/daoanh-design.css">
```
Lưu file.  
**Hoàn thành khi:** File lưu xong.

---

### Bước 006 · [TEST] Xác nhận CSS load được
Mở trình duyệt vào `http://localhost:8080/daoanh/places`.  
Mở DevTools (F12) → Console → gõ lệnh sau:
```javascript
getComputedStyle(document.documentElement).getPropertyValue('--da-gold')
```
**Hoàn thành khi:** Console trả về `#8a5c08` (hoặc chuỗi màu tương tự, không được rỗng).  
**Nếu rỗng:** Kiểm tra lại đường dẫn href trong bước 005.

---

### Bước 007 · [EDIT] Thêm tab bar 4 tabs vào sidebar
Trong `daoanh/places/index.html`, tìm phần bắt đầu sidebar (div có class/id là sidebar, entity-detail, hoặc tương đương).  
**Thêm đoạn HTML này vào TRƯỚC nội dung sidebar hiện tại:**
```html
<!-- DA TAB BAR — thêm 2026-08-17 -->
<div class="da-stabs" id="da-stabs">
  <button class="da-stab active" data-t="entity">地 Thực Thể</button>
  <button class="da-stab" data-t="cbeta">📜 Đại Tạng</button>
  <button class="da-stab" data-t="graph">🕸 Đồ Thị</button>
  <button class="da-stab" data-t="timeline">⏱ Niên Đại</button>
</div>
```

**Thêm JS này vào cuối `<script>` block hiện có (hoặc tạo script block mới):**
```javascript
// DA Tab switching
document.querySelectorAll('.da-stab').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.da-stab').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    document.querySelectorAll('.da-tab-panel').forEach(function(p) { p.style.display = 'none'; });
    var panel = document.getElementById('tp-' + btn.dataset.t);
    if (panel) { panel.style.display = 'block'; }
  });
});
```

**Bọc nội dung sidebar hiện tại** trong:
```html
<div class="da-tab-panel" id="tp-entity" style="display:block">
  <!-- NỘI DUNG SIDEBAR CŨ GIỮ NGUYÊN Ở ĐÂY -->
</div>
```

**Thêm 3 panel rỗng cho 3 tab còn lại (ở dưới):**
```html
<div class="da-tab-panel" id="tp-cbeta" style="display:none">
  <div class="da-block">
    <div class="da-block-label">Đại Tạng Kinh · CBETA</div>
    <div class="da-warn">⚠ Chưa có dữ liệu · Task T02 pending</div>
  </div>
</div>
<div class="da-tab-panel" id="tp-graph" style="display:none">
  <div class="da-block">
    <div class="da-block-label">Đồ Thị Tri Thức</div>
    <div class="da-warn">⚠ Chưa có dữ liệu · Task T17 pending</div>
  </div>
</div>
<div class="da-tab-panel" id="tp-timeline" style="display:none">
  <div class="da-block">
    <div class="da-block-label">Niên Đại · Time Authority</div>
    <div class="da-warn">⚠ time_periods = 0 rows · Task T14 pending</div>
  </div>
</div>
```
**Hoàn thành khi:** 4 tab buttons hiển thị trên sidebar, click mỗi tab chuyển được.

---

### Bước 008 · [TEST] Xác nhận tab bar hoạt động
Mở `http://localhost:8080/daoanh/places`.  
Click từng tab: "地 Thực Thể" → "📜 Đại Tạng" → "🕸 Đồ Thị" → "⏱ Niên Đại".  
**Hoàn thành khi:** Mỗi tab click hiển thị nội dung khác nhau, không có lỗi JS console.

---

### Bước 009 · [LOG] Ghi log setup
Tạo file: `daoanh/docs/sessions/2026-08-17_D001-009_setup.md`  
Điền nội dung theo template session ở đầu file này. Ghi rõ kết quả từng bước.

---

### Bước 010 · [EDIT] Cập nhật directives_progress.json
File: `daoanh/data/directives_progress.json`
```json
{
  "last_updated": "2026-08-17T00:00:00",
  "current_group": "SETUP done — chuẩn bị T14",
  "current_step": 10,
  "completed_steps": [1,2,3,4,5,6,7,8,9,10],
  "blocked_at": null,
  "note": "CSS linked, tab bar 4 tabs done, servers ok",
  "percent_total": 2
}
```
(Thay timestamp thực tế)

---

### Bước 011 · [SHELL] Cập nhật dashboard
```powershell
cd "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
python scripts/build_progress_data.py
```
Kiểm tra `http://localhost:8080/dashboard/dashboard_process.html` — timestamp cập nhật.  
**Hoàn thành khi:** Dashboard hiển thị thời điểm mới nhất.

---

---

# NHÓM T14 — Time Authority (Bước 100–119)

> **Mục tiêu:** Import DILA Time Authority vào `time_periods`, tạo API, hiển thị block Niên Đại trong tab ⏱  
> **File backend:** `daoanh/app.py`, `daoanh/scripts/import_time_periods.py`  
> **File frontend:** `daoanh/places/index.html`  
> **DB table:** `time_periods` (hiện tại = 0 rows)

---

### Bước 100 · [READ]
**Đọc:** `daoanh/tasks/T14-time-authority-import.md`  
**Đọc:** `daoanh/docs/roadmap.md` — tìm section "Khoá 2" hoặc "Time Authority"  
**Hoàn thành khi:** Biết source DILA Time là gì, schema bảng time_periods cần có gì.

---

### Bước 101 · [SHELL] Kiểm tra trạng thái DB hiện tại
```powershell
python -c "
import sqlite3
c = sqlite3.connect('data/lineage.db')
print('time_periods rows:', c.execute('SELECT COUNT(*) FROM time_periods').fetchone()[0])
print('Columns:', [d[1] for d in c.execute('PRAGMA table_info(time_periods)').fetchall()])
"
```
Ghi kết quả vào log.  
**Hoàn thành khi:** Biết số rows hiện tại và tên các cột.

---

### Bước 102 · [READ] Xác định file nguồn DILA Time
Xem trong thư mục: `daoanh/data/dila_import/Authority-Databases/`  
Tìm file liên quan đến time period, era (niên hiệu), dynasty (triều đại).  
Cũng kiểm tra: `daoanh/data/dila_import/` và các thư mục con.  
**Hoàn thành khi:** Tìm được path chính xác của file DILA Time Authority. Ghi vào log.

---

### Bước 103 · [EDIT] Tạo ETL script import_time_periods.py
Tạo file: `daoanh/scripts/import_time_periods.py`

Script phải làm đúng theo thứ tự:
1. Đọc file nguồn tìm được ở bước 102 (dùng streaming nếu file lớn, không load hết vào RAM)
2. Parse các trường: dynasty (triều đại), era_name (niên hiệu), emperor (hoàng đế), start_year, end_year, jdn_start, jdn_end
3. INSERT từng row vào bảng `time_periods` trong `data/lineage.db` (dùng `INSERT OR IGNORE` để tránh trùng)
4. In ra tổng kết: "Imported X rows, skipped Y duplicates"
5. Đóng kết nối DB.

**Hoàn thành khi:** File tạo xong, đọc lại để xác nhận code đúng.

---

### Bước 104 · [SHELL] Chạy ETL import
```powershell
python scripts/import_time_periods.py
```
**Hoàn thành khi:** In ra "Imported X rows" mà không có traceback lỗi Python.  
**Nếu lỗi:** Ghi lỗi vào log → `status: blocked` → báo admin.

---

### Bước 105 · [SHELL] Xác nhận dữ liệu đã vào DB
```powershell
python -c "
import sqlite3
c = sqlite3.connect('data/lineage.db')
print('Count:', c.execute('SELECT COUNT(*) FROM time_periods').fetchone()[0])
print('Sample:', c.execute('SELECT * FROM time_periods LIMIT 3').fetchall())
"
```
**Hoàn thành khi:** Count > 0, 3 rows sample có dữ liệu hợp lệ.

---

### Bước 106 · [EDIT] Thêm API route Time Authority vào app.py
Mở `daoanh/app.py`. Tìm khu vực routes `/daoanh/api/`. Chèn vào (không xóa route nào):

```python
@app.route('/daoanh/api/time/periods')
def api_time_periods():
    dynasty = request.args.get('dynasty', '')
    era = request.args.get('era', '')
    try:
        conn = get_db()
        q = "SELECT id, dynasty, era_name, emperor, start_year, end_year, jdn_start, jdn_end FROM time_periods WHERE 1=1"
        params = []
        if dynasty:
            q += " AND dynasty LIKE ?"
            params.append(f'%{dynasty}%')
        if era:
            q += " AND era_name LIKE ?"
            params.append(f'%{era}%')
        q += " LIMIT 100"
        rows = conn.execute(q, params).fetchall()
        return jsonify({'count': len(rows), 'periods': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daoanh/api/time/entity/<entity_id>')
def api_time_entity(entity_id):
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT tp.* FROM time_periods tp "
            "JOIN entity_chronology ec ON ec.period_id = tp.id "
            "WHERE ec.entity_id = ? LIMIT 20", [entity_id]).fetchall()
        return jsonify({'entity_id': entity_id, 'count': len(rows), 'periods': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'entity_id': entity_id, 'count': 0, 'periods': [], 'error': str(e)})
```

**Lưu ý:** Dùng cùng pattern `get_db()` hoặc `query_db()` mà app.py đang dùng (đọc app.py để xác nhận tên hàm đúng).  
**Hoàn thành khi:** Code thêm xong, lưu file.

---

### Bước 107 · [SHELL] Restart app và test API
```powershell
# Dừng app.py nếu đang chạy, rồi:
python app.py
```
Mở terminal khác:
```powershell
curl "http://localhost:5000/daoanh/api/time/periods"
```
**Hoàn thành khi:** Trả JSON `{"count": X, "periods": [...]}` — không trả 404 hay 500.

---

### Bước 108 · [EDIT] Cập nhật UI panel timeline trong places/index.html
Mở `daoanh/places/index.html`. Tìm div `id="tp-timeline"` (tạo ở bước 007).  
**Thay thế nội dung bên trong** bằng:

```html
<div class="da-block">
  <div class="da-block-label">Niên Đại · Time Authority</div>
  <div class="da-time-grid" id="da-time-grid">
    <div class="da-time-cell">
      <div class="da-time-cell-label">Triều Đại</div>
      <div class="da-time-cell-value serif" id="tc-dynasty">—</div>
    </div>
    <div class="da-time-cell">
      <div class="da-time-cell-label">Năm Kiến Lập</div>
      <div class="da-time-cell-value" id="tc-year">—</div>
    </div>
    <div class="da-time-cell">
      <div class="da-time-cell-label">Niên Hiệu</div>
      <div class="da-time-cell-value serif" id="tc-era">—</div>
    </div>
    <div class="da-time-cell">
      <div class="da-time-cell-label">JDN</div>
      <div class="da-time-cell-value mono" id="tc-jdn">—</div>
    </div>
  </div>
  <div class="da-warn" id="da-time-warn" style="display:none">
    ⚠ Không tìm thấy niên đại · time_periods chưa có dữ liệu cho entity này
  </div>
</div>
```

**Thêm JS** vào block script (sau hàm populate entity hiện tại):
```javascript
function populateTimePanel(entityId) {
  fetch('/daoanh/api/time/entity/' + entityId)
    .then(function(r){ return r.json(); })
    .then(function(data) {
      if (data.periods && data.periods.length > 0) {
        var p = data.periods[0];
        document.getElementById('tc-dynasty').textContent = p.dynasty || '—';
        document.getElementById('tc-year').textContent = p.start_year ? p.start_year + ' CE' : '—';
        document.getElementById('tc-era').textContent = p.era_name || '—';
        document.getElementById('tc-jdn').textContent = p.jdn_start || '—';
        document.getElementById('da-time-warn').style.display = 'none';
      } else {
        document.getElementById('da-time-warn').style.display = 'flex';
      }
    })
    .catch(function(){ document.getElementById('da-time-warn').style.display = 'flex'; });
}
```

Tìm chỗ trong code mà marker được click / entity được chọn → gọi thêm `populateTimePanel(entityId)`.  
**Hoàn thành khi:** Hàm được gọi đúng lúc entity thay đổi.

---

### Bước 109 · [TEST] Kiểm tra UI end-to-end T14
1. Mở `http://localhost:8080/daoanh/places`
2. Click 1 địa điểm trên bản đồ
3. Click tab "⏱ Niên Đại"
4. Kiểm tra: grid hiển thị hoặc warning banner hiển thị  
**Hoàn thành khi:** Không có lỗi JS, tab hiển thị đúng một trong hai trạng thái.

---

### Bước 110 · [EDIT] Cập nhật task file T14
Mở `daoanh/tasks/T14-time-authority-import.md`.  
Tick các acceptance criteria đã xong. Đổi frontmatter:
```yaml
status: done
updated: 2026-08-17
```
(hoặc `in_progress` nếu chưa xong hết)

---

### Bước 111 · [LOG] Ghi log T14
Tạo file: `daoanh/docs/sessions/2026-08-17_D100-110_T14.md`  
Ghi: rows imported, API test result, UI screenshot/mô tả.

---

### Bước 112 · [EDIT] Cập nhật directives_progress.json
```json
{
  "last_updated": "YYYY-MM-DDTHH:MM:SS",
  "current_group": "T14 done — chuẩn bị T02",
  "current_step": 112,
  "completed_steps": "1-112",
  "blocked_at": null,
  "note": "Time Authority: X rows imported, API /api/time/periods ok, UI grid done",
  "percent_total": 15
}
```

---

### Bước 113 · [SHELL] Cập nhật dashboard
```powershell
python scripts/build_progress_data.py
```

---

---

# NHÓM T02 — CBETA Passages (Bước 200–229)

> **Mục tiêu:** Hiển thị đoạn văn CBETA trong tab 📜, với nguyên văn Hán và bản dịch Việt  
> **Depends on:** Không  
> **File backend:** `daoanh/app.py`  
> **DB table:** `passages` hoặc `cbeta_passages`, `passage_vi`  
> **UI:** tab `tp-cbeta` trong `daoanh/places/index.html`

---

### Bước 200 · [READ]
**Đọc:** `daoanh/tasks/T02-passage-vi-entity-summary.md`  
**Đọc:** `daoanh/docs/design-spec.md` Section 2.8 (CBETA Passage block)

---

### Bước 201 · [SHELL] Kiểm tra DB passages
```powershell
python -c "
import sqlite3
c = sqlite3.connect('data/lineage.db')
tables = [t[0] for t in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%passage%'\").fetchall()]
print('Tables:', tables)
for t in tables:
    print(t, c.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0], 'rows')
"
```
Ghi kết quả vào log.  
**Hoàn thành khi:** Biết tên bảng passages chính xác và số rows.

---

### Bước 202 · [SHELL] Kiểm tra API passages hiện tại
```powershell
curl "http://localhost:5000/daoanh/api/entity/PL000000023255/passages"
```
Nếu trả 404: API chưa có → cần tạo (bước 203).  
Nếu trả 200 nhưng `count=0`: API có nhưng chưa có dữ liệu.  
Ghi kết quả vào log.

---

### Bước 203 · [EDIT] Thêm API passages (nếu chưa có)
Trong `daoanh/app.py`, thêm route (nếu chưa tồn tại):

```python
@app.route('/daoanh/api/entity/<entity_id>/passages')
def api_entity_passages(entity_id):
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT p.id, p.cbeta_ref, p.text_zh, p.title_zh,
                   pv.text_vi, pv.status as vi_status
            FROM passages p
            LEFT JOIN passage_vi pv ON pv.passage_id = p.id
            WHERE p.entity_id = ?
            ORDER BY p.cbeta_ref
            LIMIT 20
        """, [entity_id]).fetchall()
        return jsonify({'entity_id': entity_id, 'count': len(rows),
                        'passages': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'entity_id': entity_id, 'count': 0, 'passages': [], 'error': str(e)})
```

**Lưu ý:** Thay `passages`, `passage_vi`, `entity_id`, `cbeta_ref`, `text_zh`, `text_vi` cho đúng với schema thực tế trong DB (kiểm tra PRAGMA table_info nếu cần).

---

### Bước 204 · [TEST] Test API passages
```powershell
curl "http://localhost:5000/daoanh/api/entity/PL000000023255/passages"
```
**Hoàn thành khi:** Trả JSON `{"count": X, "passages": [...]}` — không trả 500.  
(count=0 vẫn chấp nhận được nếu chưa có dữ liệu — UI sẽ hiển thị warning)

---

### Bước 205 · [EDIT] Cập nhật UI panel CBETA trong places/index.html
Tìm div `id="tp-cbeta"`. Thay toàn bộ nội dung bên trong:

```html
<div class="da-block">
  <div class="da-block-label">Đại Tạng Kinh · CBETA Passages</div>
  <div id="cbeta-loading" style="color:var(--da-dim);font-size:11px">Đang tải...</div>
  <div id="cbeta-list"></div>
  <div id="cbeta-empty" class="da-warn" style="display:none">
    ⚠ Không tìm thấy trích đoạn CBETA · Task T02 pending
  </div>
</div>
```

**Thêm JS:**
```javascript
var CBETA_TPLS = {
  passage: function(p) {
    return '<div class="da-passage">' +
      '<div class="da-passage-ref">' +
        '<span>' + (p.cbeta_ref || '') + (p.title_zh ? ' · ' + p.title_zh : '') + '</span>' +
        '<span class="da-chip ' + (p.vi_status ? 'da-chip-partial' : 'da-chip-none') + '" style="padding:1px 6px;font-size:7.5px">' +
          (p.vi_status || 'Chưa dịch') + '</span>' +
      '</div>' +
      (p.text_zh ? '<div class="da-passage-han">' + p.text_zh.substring(0, 200) + '…</div>' : '') +
      (p.text_vi ? '<div class="da-passage-vi">' + p.text_vi + '</div>' : '') +
      '<div class="da-passage-actions">' +
        '<button class="da-btn da-btn-primary" onclick="translatePassage(\'' + p.id + '\')">Dịch Mượt →</button>' +
        '<a class="da-btn" href="https://cbetaonline.dila.edu.tw/' + (p.cbeta_ref || '') + '" target="_blank">CBETA Online</a>' +
      '</div>' +
    '</div>';
  }
};

function loadCbetaPassages(entityId) {
  var list = document.getElementById('cbeta-list');
  var empty = document.getElementById('cbeta-empty');
  var loading = document.getElementById('cbeta-loading');
  if (!list) return;
  loading.style.display = 'block';
  list.innerHTML = '';
  empty.style.display = 'none';
  fetch('/daoanh/api/entity/' + entityId + '/passages')
    .then(function(r){ return r.json(); })
    .then(function(data) {
      loading.style.display = 'none';
      if (data.passages && data.passages.length > 0) {
        list.innerHTML = data.passages.map(CBETA_TPLS.passage).join('');
      } else {
        empty.style.display = 'flex';
      }
    })
    .catch(function() { loading.style.display = 'none'; empty.style.display = 'flex'; });
}

function translatePassage(passageId) {
  // Stub: sẽ gọi /api/translate/cbeta trong T12
  alert('T12 Dịch Mượt — chưa implement');
}
```

Tìm chỗ entity được chọn → gọi thêm `loadCbetaPassages(entityId)`.

---

### Bước 206 · [TEST] Kiểm tra UI CBETA
1. Mở `http://localhost:8080/daoanh/places`
2. Click địa điểm → click tab "📜 Đại Tạng"
3. Kết quả chấp nhận: hiển thị da-passage blocks (nếu có data) HOẶC da-warn đỏ (nếu count=0)
**Hoàn thành khi:** Tab load không lỗi JS.

---

### Bước 207 · [EDIT] Cập nhật task file T02
Tick acceptance criteria đã xong. Đổi frontmatter `status: done` (hoặc `in_progress`).

---

### Bước 208 · [LOG] Ghi log T02
Tạo file: `daoanh/docs/sessions/2026-08-17_D200-208_T02.md`

---

### Bước 209 · [EDIT] Cập nhật directives_progress.json
```json
{
  "current_group": "T02 done — chuẩn bị T12",
  "current_step": 209,
  "note": "CBETA tab UI done, API /passages ok, count = X",
  "percent_total": 28
}
```

---

### Bước 210 · [SHELL] Cập nhật dashboard
```powershell
python scripts/build_progress_data.py
```

---

---

# NHÓM T12 — Dịch Mượt & Cache (Bước 250–269)

> **Mục tiêu:** Nút "Dịch Mượt →" trong CBETA tab gọi được API dịch, cache kết quả, admin approve  
> **Depends on:** T02 (CBETA passages phải hiển thị trước)  
> **Bắt đầu bước này sau khi T02 hoàn thành**

---

### Bước 250 · [READ]
**Đọc:** `daoanh/tasks/T12-dich-muot-cache-translation.md`

---

### Bước 251 · [SHELL] Kiểm tra API translate hiện có
```powershell
curl -X POST "http://localhost:5000/daoanh/api/translate/cbeta" -H "Content-Type: application/json" -d "{\"passage_id\":\"1\"}"
```
Ghi kết quả: 404 (chưa có) hay 200?

---

### Bước 252 · [EDIT] Thêm API Dịch Mượt vào app.py
Trong `daoanh/app.py`, thêm route (nếu chưa có):

```python
@app.route('/daoanh/api/translate/cbeta', methods=['POST'])
def api_translate_cbeta():
    data = request.get_json() or {}
    passage_id = data.get('passage_id')
    if not passage_id:
        return jsonify({'error': 'passage_id required'}), 400
    try:
        conn = get_db()
        passage = conn.execute(
            "SELECT text_zh, cbeta_ref FROM passages WHERE id = ?", [passage_id]).fetchone()
        if not passage:
            return jsonify({'error': 'passage not found'}), 404
        # Bước 1: Dịch thô (dùng Gemini API - KHÔNG commit key)
        # Gemini key đã có trong app.py — tìm và tái sử dụng hàm dịch hiện có
        # Bước 2: Cache vào passage_vi
        # Bước 3: Trả kết quả
        return jsonify({
            'passage_id': passage_id,
            'cbeta_ref': passage['cbeta_ref'],
            'status': 'draft',
            'note': 'Stub — implement với Gemini API hiện có trong app.py'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Lưu ý:** Tìm hàm Gemini dịch hiện có trong `app.py` (gần dòng 1065) và tái sử dụng. Không viết mới call API Gemini.

---

### Bước 253 · [EDIT] Kết nối nút "Dịch Mượt →" với API
Trong hàm `translatePassage(passageId)` đã tạo ở bước 205, thay stub `alert` bằng:
```javascript
function translatePassage(passageId) {
  var btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Đang dịch...';
  fetch('/daoanh/api/translate/cbeta', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({passage_id: passageId})
  })
  .then(function(r){ return r.json(); })
  .then(function(data) {
    btn.textContent = 'Đã dịch ✓';
    // Reload passages để hiện bản dịch mới
    if (window._currentEntityId) loadCbetaPassages(window._currentEntityId);
  })
  .catch(function() { btn.disabled = false; btn.textContent = 'Dịch Mượt →'; });
}
```

---

### Bước 254 · [TEST] Test nút Dịch Mượt
1. Mở tab 📜 Đại Tạng trong places
2. Click "Dịch Mượt →" trên 1 passage
3. Nút chuyển sang "Đang dịch..." rồi "Đã dịch ✓"
**Hoàn thành khi:** Nút không báo lỗi, API trả 200.

---

### Bước 255 · [EDIT] Cập nhật task T12 + log + JSON
Tick acceptance criteria. Đổi status. Tạo log file. Cập nhật directives_progress.json `percent_total: 38`.

---

### Bước 256 · [SHELL] Cập nhật dashboard
```powershell
python scripts/build_progress_data.py
```

---

---

# NHÓM T16 — Nexus Points (Bước 400–419)

> **Mục tiêu:** Hiển thị danh sách nhân vật liên quan (person rows + NEXUS badge) trong tab 地 Thực Thể  
> **Depends on:** T02  
> **UI component:** `.da-person-row`, `.da-nexus-badge` (xem design-spec.md Section 2.9)

---

### Bước 400 · [READ]
**Đọc:** `daoanh/tasks/T16-nexus-points.md`  
**Đọc:** `daoanh/docs/design-spec.md` Section 2.9 (Person row / Nexus badge)

---

### Bước 401 · [SHELL] Kiểm tra API nexus hiện có
```powershell
curl "http://localhost:5000/daoanh/api/nexus/find?place=PL000000023255"
```
Ghi: 404 (chưa có) hay 200?

---

### Bước 402 · [SHELL] Kiểm tra bảng nexus trong DB
```powershell
python -c "
import sqlite3
c = sqlite3.connect('data/lineage.db')
tables = [t[0] for t in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%nexus%'\").fetchall()]
print('Nexus tables:', tables)
# Cũng tìm bảng persons liên kết với place
persons = [t[0] for t in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%person%'\").fetchall()]
print('Person tables:', persons)
"
```

---

### Bước 403 · [EDIT] Thêm API nexus/find vào app.py
```python
@app.route('/daoanh/api/nexus/find')
def api_nexus_find():
    place_id = request.args.get('place', '')
    person_id = request.args.get('person', '')
    try:
        conn = get_db()
        # Thử truy vấn bảng nexus nếu có
        q = "SELECT n.*, p.name_vi, p.name_zh FROM nexus n JOIN persons p ON n.person_id = p.id WHERE 1=1"
        params = []
        if place_id:
            q += " AND n.place_id = ?"
            params.append(place_id)
        if person_id:
            q += " AND n.person_id = ?"
            params.append(person_id)
        q += " LIMIT 20"
        rows = conn.execute(q, params).fetchall()
        return jsonify({'count': len(rows), 'nexus': [dict(r) for r in rows]})
    except Exception as e:
        # Nếu bảng nexus chưa có: trả rỗng, không báo lỗi
        return jsonify({'count': 0, 'nexus': [], 'note': 'nexus table not ready: ' + str(e)})
```

---

### Bước 404 · [EDIT] Thêm Person/Nexus block vào tab Thực Thể
Trong `daoanh/places/index.html`, tìm panel `id="tp-entity"`. Sau nội dung entity hiện tại, thêm:

```html
<div class="da-block" id="da-nexus-block">
  <div class="da-block-label">Nhân Vật Liên Quan · Nexus</div>
  <div id="da-nexus-list"></div>
  <div id="da-nexus-empty" class="da-warn" style="display:none">
    ⚠ Không có nexus · Task T16 pending
  </div>
</div>
```

**Thêm JS:**
```javascript
function loadNexusPersons(entityId) {
  var list = document.getElementById('da-nexus-list');
  var empty = document.getElementById('da-nexus-empty');
  if (!list) return;
  list.innerHTML = '';
  fetch('/daoanh/api/nexus/find?place=' + entityId)
    .then(function(r){ return r.json(); })
    .then(function(data) {
      if (data.nexus && data.nexus.length > 0) {
        list.innerHTML = data.nexus.map(function(n) {
          var avatar = n.name_zh ? n.name_zh.charAt(0) : '人';
          return '<div class="da-person-row">' +
            '<div class="da-person-avatar">' + avatar + '</div>' +
            '<div style="flex:1;min-width:0">' +
              '<div class="da-person-name-vi">' + (n.name_vi || n.name_zh || '') + '</div>' +
              '<div class="da-person-name-zh">' + (n.name_zh || '') + '</div>' +
            '</div>' +
            (n.is_nexus ? '<span class="da-nexus-badge">NEXUS</span>' : '') +
          '</div>';
        }).join('');
        empty.style.display = 'none';
      } else {
        empty.style.display = 'flex';
      }
    })
    .catch(function() { empty.style.display = 'flex'; });
}
```

Tìm chỗ entity được chọn → gọi thêm `loadNexusPersons(entityId)`.

---

### Bước 405 · [TEST] Kiểm tra UI Nexus
Click địa điểm trong bản đồ → tab Thực Thể → cuộn xuống → thấy block "Nhân Vật Liên Quan".  
**Hoàn thành khi:** Block hiển thị (có hoặc không có data đều ok).

---

### Bước 406 · [EDIT] Cập nhật T16 + log + JSON `percent_total: 55`

---

### Bước 407 · [SHELL] Dashboard
```powershell
python scripts/build_progress_data.py
```

---

---

# NHÓM T17 — Knowledge Graph (Bước 500–519)

> **Mục tiêu:** Tab 🕸 Đồ Thị hiển thị force-directed graph entity/person/text  
> **Thư viện:** Canvas (không dùng CDN — tự vẽ canvas) hoặc vis-network từ CDN nếu CSP cho phép  
> **Design ref:** Mockup Section Knowledge Graph — force-directed canvas

---

### Bước 500 · [READ]
**Đọc:** `daoanh/tasks/T17-knowledge-graph-viz.md`  
**Đọc:** `daoanh/docs/design-spec.md` — phần Graph (trong mockup: force-directed, 8 nodes, 11 edges)

---

### Bước 501 · [SHELL] Kiểm tra API graph
```powershell
curl "http://localhost:5000/daoanh/api/entity/PL000000023255/graph"
```
Ghi: 404 (chưa có) hay 200?

---

### Bước 502 · [EDIT] Thêm API entity graph
```python
@app.route('/daoanh/api/entity/<entity_id>/graph')
def api_entity_graph(entity_id):
    try:
        conn = get_db()
        nodes = [{'id': entity_id, 'label': entity_id, 'type': 'place'}]
        edges = []
        # Thêm persons liên quan
        persons = conn.execute(
            "SELECT p.id, p.name_vi, p.name_zh FROM persons p "
            "JOIN entity_persons ep ON ep.person_id = p.id "
            "WHERE ep.entity_id = ? LIMIT 8", [entity_id]).fetchall()
        for p in persons:
            nodes.append({'id': p['id'], 'label': p['name_vi'] or p['name_zh'], 'type': 'person'})
            edges.append({'from': entity_id, 'to': p['id'], 'label': 'visited'})
        return jsonify({'nodes': nodes, 'edges': edges})
    except Exception as e:
        return jsonify({'nodes': [{'id': entity_id, 'label': entity_id, 'type': 'place'}], 'edges': [], 'error': str(e)})
```

---

### Bước 503 · [EDIT] Thêm Graph canvas vào tab Đồ Thị
Tìm panel `id="tp-graph"`. Thay nội dung bên trong:

```html
<div class="da-block">
  <div class="da-block-label">Đồ Thị Tri Thức · Knowledge Graph</div>
  <canvas id="da-graph-canvas" width="350" height="280" style="width:100%;border:1px solid var(--da-border);border-radius:8px;background:var(--da-card)"></canvas>
  <div id="da-graph-empty" class="da-warn" style="display:none">⚠ Không có dữ liệu graph</div>
</div>
```

**Thêm JS force-directed graph (tự vẽ canvas, không cần CDN):**
```javascript
var daGraph = { nodes: [], edges: [], anim: null };

function loadGraph(entityId) {
  fetch('/daoanh/api/entity/' + entityId + '/graph')
    .then(function(r){ return r.json(); })
    .then(function(data) {
      if (!data.nodes || data.nodes.length === 0) {
        document.getElementById('da-graph-empty').style.display = 'flex';
        return;
      }
      document.getElementById('da-graph-empty').style.display = 'none';
      var W = 350, H = 280, cx = W/2, cy = H/2;
      daGraph.nodes = data.nodes.map(function(n, i) {
        var angle = (2 * Math.PI * i) / data.nodes.length;
        return { id: n.id, label: n.label, type: n.type,
          x: cx + Math.cos(angle) * 90, y: cy + Math.sin(angle) * 90, vx: 0, vy: 0 };
      });
      daGraph.edges = data.edges || [];
      if (daGraph.anim) cancelAnimationFrame(daGraph.anim);
      daGraphLoop();
    });
}

function daGraphLoop() {
  var canvas = document.getElementById('da-graph-canvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var W = canvas.width, H = canvas.height;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark'
    || matchMedia('(prefers-color-scheme:dark)').matches;
  var colors = { place: '#c4891a', person: '#22d3ee', text: '#34d399', time: '#f87171' };

  daGraph.nodes.forEach(function(n) {
    daGraph.nodes.forEach(function(m) {
      if (n === m) return;
      var dx = n.x - m.x, dy = n.y - m.y;
      var d = Math.sqrt(dx*dx + dy*dy) || 1;
      var f = 800 / (d * d);
      n.vx += dx / d * f; n.vy += dy / d * f;
    });
    n.vx += (W/2 - n.x) * 0.003; n.vy += (H/2 - n.y) * 0.003;
    n.vx *= 0.85; n.vy *= 0.85;
    n.x += n.vx; n.y += n.vy;
    n.x = Math.max(20, Math.min(W-20, n.x));
    n.y = Math.max(20, Math.min(H-20, n.y));
  });
  daGraph.edges.forEach(function(e) {
    var from = daGraph.nodes.find(function(n){ return n.id === e.from; });
    var to   = daGraph.nodes.find(function(n){ return n.id === e.to; });
    if (from && to) {
      var dx = to.x - from.x, dy = to.y - from.y;
      var f = Math.sqrt(dx*dx+dy*dy) * 0.012;
      from.vx += dx * f; from.vy += dy * f;
      to.vx   -= dx * f; to.vy   -= dy * f;
    }
  });

  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';
  ctx.lineWidth = 1;
  daGraph.edges.forEach(function(e) {
    var from = daGraph.nodes.find(function(n){ return n.id === e.from; });
    var to   = daGraph.nodes.find(function(n){ return n.id === e.to; });
    if (from && to) { ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(to.x, to.y); ctx.stroke(); }
  });
  daGraph.nodes.forEach(function(n) {
    var c = colors[n.type] || '#888';
    ctx.beginPath(); ctx.arc(n.x, n.y, 10, 0, 2*Math.PI);
    ctx.fillStyle = c + '33'; ctx.fill();
    ctx.strokeStyle = c; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = isDark ? '#dce5f4' : '#1a1a28';
    ctx.font = '9px system-ui'; ctx.textAlign = 'center';
    ctx.fillText((n.label || '').substring(0, 8), n.x, n.y + 20);
  });
  daGraph.anim = requestAnimationFrame(daGraphLoop);
}
```

Gọi `loadGraph(entityId)` khi tab graph được click và entity đang được chọn.

---

### Bước 504 · [TEST] Kiểm tra graph
1. Click địa điểm → click tab "🕸 Đồ Thị"
2. Canvas hiển thị nodes chuyển động
**Hoàn thành khi:** Không lỗi JS, canvas render.

---

### Bước 505 · [EDIT] Cập nhật T17 + log + JSON `percent_total: 70`

---

### Bước 506 · [SHELL] Dashboard
```powershell
python scripts/build_progress_data.py
```

---

---

# NHÓM T06 — GIS Cluster Click (Bước 600–609)

> **Mục tiêu:** Click vào cluster icon → zoom-to-bounds (Leaflet)  
> **File:** `daoanh/places/index.html` — JS phần Leaflet  
> **Không cần backend**

---

### Bước 600 · [READ]
**Đọc:** `daoanh/tasks/T06-gis-cluster-click.md`  
Tìm trong `places/index.html` đoạn code `markerClusterGroup` hoặc `L.markerClusterGroup`.

---

### Bước 601 · [EDIT] Thêm cluster click handler
Trong phần JS khởi tạo Leaflet cluster, thêm:
```javascript
clusterGroup.on('clusterclick', function(e) {
  e.layer.zoomToBounds({ padding: [30, 30] });
});
```
(Tìm biến tên cluster group thực tế trong code — có thể là `markers`, `clusterGroup`, `markerCluster`, v.v.)  
**Hoàn thành khi:** Code thêm xong, lưu file.

---

### Bước 602 · [TEST] Test cluster click
1. Mở `http://localhost:8080/daoanh/places`
2. Zoom out để thấy các cluster (số lượng)
3. Click vào cluster → bản đồ phải zoom vào vùng đó
**Hoàn thành khi:** Zoom-to-bounds hoạt động.

---

### Bước 603 · [EDIT] Cập nhật T06 + log + JSON `percent_total: 80`

---

### Bước 604 · [SHELL] Dashboard
```powershell
python scripts/build_progress_data.py
```

---

---

# NHÓM T11 — RAG Việt Chat (Bước 700–719)

> **Mục tiêu:** Sidebar có panel chat với Gemini, trả lời tiếng Việt có citation từ CBETA  
> **Depends on:** T02  
> **File backend:** `daoanh/app.py`  
> **Cảnh báo:** API Gemini hardcoded — không commit key

---

### Bước 700 · [READ]
**Đọc:** `daoanh/tasks/T11-rag-vi-chat.md`  
Tìm trong `app.py` các route liên quan đến Gemini (gần dòng 1065, 1105).

---

### Bước 701 · [SHELL] Kiểm tra API rag
```powershell
curl -X POST "http://localhost:5000/daoanh/api/rag_vi/chat" -H "Content-Type: application/json" -d "{\"question\":\"test\"}"
```
Ghi: 404 (chưa có) hay lỗi?

---

### Bước 702 · [EDIT] Thêm panel Chat vào sidebar
Thêm 1 tab thứ 5 "💬 Hỏi Đáp" vào `.da-stabs` và panel tương ứng.  
UI chat cơ bản:
```html
<div class="da-tab-panel" id="tp-chat" style="display:none">
  <div class="da-block">
    <div class="da-block-label">Hỏi Đáp · RAG Việt</div>
    <div id="da-chat-log" style="max-height:200px;overflow-y:auto;margin-bottom:8px"></div>
    <div style="display:flex;gap:6px">
      <input id="da-chat-input" class="da-nav-search" style="flex:1;border-radius:6px;padding:5px 10px" placeholder="Hỏi về địa điểm này...">
      <button class="da-btn da-btn-primary" onclick="sendChat()">Gửi</button>
    </div>
    <div class="da-warn" style="margin-top:6px">⚠ RAG chưa có vector index · Task T11 pending</div>
  </div>
</div>
```

JS:
```javascript
function sendChat() {
  var input = document.getElementById('da-chat-input');
  var log = document.getElementById('da-chat-log');
  var q = input.value.trim();
  if (!q) return;
  log.innerHTML += '<div style="color:var(--da-gold);font-size:11px;margin-bottom:4px">Bạn: ' + q + '</div>';
  input.value = '';
  fetch('/daoanh/api/rag_vi/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: q, entity_id: window._currentEntityId || ''})
  })
  .then(function(r){ return r.json(); })
  .then(function(data) {
    log.innerHTML += '<div style="font-size:11px;margin-bottom:8px">' + (data.answer_vi || data.error || 'Chưa có dữ liệu') + '</div>';
    log.scrollTop = log.scrollHeight;
  });
}
```

---

### Bước 703 · [EDIT] Thêm API RAG vào app.py
```python
@app.route('/daoanh/api/rag_vi/chat', methods=['POST'])
def api_rag_vi_chat():
    data = request.get_json() or {}
    question = data.get('question', '')
    entity_id = data.get('entity_id', '')
    if not question:
        return jsonify({'error': 'question required'}), 400
    # Dùng Gemini API hiện có (tái sử dụng code gần dòng 1065)
    # Tạm thời trả placeholder cho đến khi có vector index
    return jsonify({
        'answer_vi': 'RAG chưa sẵn sàng. Cần build vector index trước.',
        'citations': [],
        'entity_id': entity_id,
        'status': 'pending_vector_index'
    })
```

---

### Bước 704 · [TEST] Test chat UI
Mở tab 💬 → gõ câu hỏi → nhấn Gửi → thấy phản hồi.  
**Hoàn thành khi:** Không lỗi JS, API trả JSON.

---

### Bước 705 · [EDIT] Cập nhật T11 + log + JSON `percent_total: 90`

---

### Bước 706 · [SHELL] Dashboard final
```powershell
python scripts/build_progress_data.py
```

---

---

# KIỂM TRA CUỐI (Bước 900–909)

---

### Bước 900 · [TEST] Kiểm tra toàn bộ places page
1. Mở `http://localhost:8080/daoanh/places`
2. Click nhiều địa điểm khác nhau
3. Kiểm tra từng tab: 地 Thực Thể, 📜 Đại Tạng, 🕸 Đồ Thị, ⏱ Niên Đại, 💬 Hỏi Đáp
4. Kiểm tra cluster click zoom
5. Kiểm tra dark/light theme (nếu có toggle)

---

### Bước 901 · [SHELL] Chạy build lần cuối
```powershell
python scripts/build_progress_data.py
```

---

### Bước 902 · [EDIT] Cập nhật directives_progress.json lần cuối
```json
{
  "last_updated": "YYYY-MM-DDTHH:MM:SS",
  "current_group": "DONE",
  "current_step": 902,
  "completed_steps": "1-902",
  "blocked_at": null,
  "note": "Tất cả tasks đã tích hợp. Báo admin để review.",
  "percent_total": 100
}
```

---

### Bước 903 · [LOG] Tạo báo cáo tổng kết
Tạo file: `daoanh/docs/sessions/2026-08-17_D900_final_report.md`
Ghi tóm tắt:
- Những task đã xong hoàn toàn
- Những task còn blocked/pending
- Các warning ban admin cần biết
- Các con số thực tế (rows, API test results)

---

### Bước 909 · Báo admin
Ghi vào log: "Đã hoàn thành tích hợp theo directive. Admin vui lòng review tại http://localhost:8080/daoanh/places và http://localhost:8080/dashboard/dashboard_process.html"

---

## BẢNG TÓM TẮT NHÓM

| Nhóm | Bước | Task | Mục tiêu | % tổng |
|------|------|------|---------|--------|
| SETUP | 001–011 | — | CSS link, tab bar | 2% |
| T14 | 100–113 | Time Authority | Niên đại grid | 15% |
| T02 | 200–210 | CBETA Passages | Tab Đại Tạng | 28% |
| T12 | 250–256 | Dịch Mượt | Nút dịch CBETA | 38% |
| T16 | 400–407 | Nexus Points | Nhân vật liên quan | 55% |
| T17 | 500–506 | Knowledge Graph | Canvas graph | 70% |
| T06 | 600–604 | GIS Cluster Click | Zoom-to-bounds | 80% |
| T11 | 700–706 | RAG Chat | Panel hỏi đáp | 90% |
| FINAL | 900–909 | — | Kiểm tra tổng | 100% |

---

---

# NHÓM T22.1 — Founding Date Reuse Audit (Bước 1000–1019)

> **Mục tiêu:** Kiểm tra toàn bộ nguồn dữ liệu niên đại TRƯỚC khi viết bất kỳ NLP pipeline nào.
> **DB:** Chỉ đọc trên **Backup DB** — KHÔNG sửa `lineage.db` production.
> **VPS path:** `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/`
> **Depends on:** T22.1 task file — `daoanh/tasks/T22.1-founding-date-data-reuse-audit.md`
> **Gate:** Giai đoạn A phải hoàn tất và gửi Lee Tổng duyệt TRƯỚC Giai đoạn B.

## ⚠️ BA NGUYÊN TẮC CỐT LÕI — KHÔNG ĐƯỢC VI PHẠM

| # | Nguyên tắc | Quy tắc cụ thể |
|---|-----------|---------------|
| P1 | **Reuse First** | Tìm trong raw_xml và external data TRƯỚC khi nghĩ đến NLP |
| P2 | **Safety First** | Mọi script chỉ chạy trên backup. `cp data/lineage.db data/lineage_audit_backup.db` trước |
| P3 | **Inventory First** | Kết quả lưu JSON/CSV trước — Lee Tổng duyệt trước khi làm bước tiếp |

---

## GIAI ĐOẠN A — Kiểm tra Evidence trong raw_xml (Làm TRƯỚC)

### Bước 1000 · [SHELL] Tạo Backup DB
```powershell
cd "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
copy data\lineage.db data\lineage_audit_backup.db
```
**Hoàn thành khi:** File `lineage_audit_backup.db` tồn tại.

---

### Bước 1001 · [SHELL] Kiểm tra raw_xml baseline
```powershell
python -c "
import sqlite3
c = sqlite3.connect('data/lineage_audit_backup.db')
total = c.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
has_xml = c.execute(\"SELECT COUNT(*) FROM places_dila WHERE raw_xml IS NOT NULL AND raw_xml != ''\").fetchone()[0]
print(f'Total places_dila: {total}')
print(f'Has raw_xml: {has_xml} ({has_xml/total*100:.1f}%)')
print(f'No raw_xml: {total - has_xml}')
"
```
Ghi kết quả vào log.

---

### Bước 1002 · [SHELL] Quét patterns thành lập
```powershell
python -c "
import sqlite3, re
c = sqlite3.connect('data/lineage_audit_backup.db')
rows = c.execute(\"SELECT id, raw_xml FROM places_dila WHERE raw_xml IS NOT NULL AND raw_xml != ''\").fetchall()

patterns = {
    '建':   r'建',
    '創':   r'創',
    '創建': r'創建',
    '始建': r'始建',
    '建於': r'建於',
    '創於': r'創於',
    '始置': r'始置',
    '年_in_parens': r'（\d{3,4}年）',
}

results = {k: 0 for k in patterns}
matched_any = set()

for pid, xml in rows:
    for key, pat in patterns.items():
        if re.search(pat, xml):
            results[key] += 1
            matched_any.add(pid)

print('=== PATTERN COUNTS ===')
for k, v in results.items():
    print(f'  {k}: {v} records ({v/len(rows)*100:.1f}%)')
print(f'Total with ANY pattern: {len(matched_any)} / {len(rows)} ({len(matched_any)/len(rows)*100:.1f}%)')
" 2>&1
```
**Hoàn thành khi:** Có số liệu thực tế cho từng pattern.

---

### Bước 1003 · [SHELL] Xuất sample 10 records để Lee Tổng kiểm tra
```powershell
python -c "
import sqlite3, re, json
c = sqlite3.connect('data/lineage_audit_backup.db')
rows = c.execute(\"SELECT id, name_zh, raw_xml FROM places_dila WHERE raw_xml IS NOT NULL AND raw_xml != '' LIMIT 500\").fetchall()

samples = []
for pid, name, xml in rows:
    m = re.search(r'（\d{3,4}年）', xml)
    if m:
        start = max(0, m.start()-60)
        end   = min(len(xml), m.end()+60)
        samples.append({'dila_id': pid, 'name_zh': name, 'evidence': xml[start:end], 'match': m.group(0)})
    if len(samples) >= 10: break

for s in samples:
    print(s['dila_id'], s['name_zh'], '->', s['match'])
    print('  Context:', s['evidence'][:120])
    print()
" 2>&1
```
**Hoàn thành khi:** 10 sample records hiển thị — gửi output này cho Lee Tổng.

---

### Bước 1004 · [LOG] Tạo báo cáo Giai đoạn A
Tạo file: `daoanh/docs/sessions/2026-08-20_T22.1_GiaiDoanA.md`
Ghi đầy đủ:
- Số liệu từ bước 1001 (total / has_xml / no_xml)
- Số liệu từ bước 1002 (count per pattern)
- Sample 10 records từ bước 1003

```
⛔ DỪNG LẠI SAU BƯỚC 1004 — Chờ Lee Tổng duyệt Giai đoạn A trước khi tiếp tục.
```

---

## GIAI ĐOẠN B — Đối chiếu External Data (Chỉ làm sau khi Lee Tổng duyệt Giai đoạn A)

### Bước 1005 · [SHELL] CHECK GATE — Xác nhận Lee Tổng đã approve Gate 1
```powershell
python -c "
import json, sys
with open('data/t22_1_approvals.json', encoding='utf-8') as f:
    d = json.load(f)
status = d.get('gates', {}).get('giai_doan_a', {}).get('status', 'pending')
if status != 'approved':
    print(f'⛔ GATE BLOCKED: giai_doan_a status = {status}')
    print('   Chờ Lee Tổng click nút Duyệt trên Admin Dashboard trước khi tiếp tục.')
    sys.exit(1)
else:
    by = d['gates']['giai_doan_a'].get('approved_by','?')
    at = d['gates']['giai_doan_a'].get('approved_at','?')
    print(f'✅ GATE PASSED: approved by {by} at {at}')
    print('   Tiếp tục Giai đoạn B...')
"
```
**Hoàn thành khi:** Script in `✅ GATE PASSED`. Nếu in `⛔ GATE BLOCKED` → DỪNG NGAY, không làm bước tiếp.

---

### Bước 1006 · [SHELL] Wikidata — số places có P571 qua P1188
Đây là kết quả đã biết từ web research (2026-08-20):
- Wikidata P1188 (DILA bridge): **148 places** có direct link
- Wikidata P571 tổng Buddhist temples China: **2,106 places**

Verify lại bằng SPARQL nếu cần (query Wikidata endpoint).

---

### Bước 1007 · [READ] BGIS — Download và inspect
```
1. Download: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VAYEUZ
2. Mở CSV → xem field "Starting year" cho 少林寺 (495?) và 白馬寺 (68?)
3. Ghi: Historical founding date hay modern registration year?
```
**Hoàn thành khi:** Biết chắc ý nghĩa của "Starting year".

---

### Bước 1008 · [SHELL] Tạo Coverage Matrix CSV
```powershell
python -c "
import sqlite3, csv

c = sqlite3.connect('data/lineage_audit_backup.db')
places = c.execute('SELECT id, name_zh, geo_lat, geo_long FROM places_dila LIMIT 100').fetchall()

with open('data/founding_date_source_coverage.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['dila_id','name_zh','has_raw_xml','has_geo','wikidata_match','bgis_match','chgis_match','classification'])
    for pid, name, lat, lng in places:
        has_xml = bool(c.execute('SELECT 1 FROM places_dila WHERE id=? AND raw_xml IS NOT NULL', (pid,)).fetchone())
        writer.writerow([pid, name, has_xml, bool(lat), 'TBD', 'TBD', 'TBD', 'TBD'])

print('CSV created: data/founding_date_source_coverage.csv')
"
```
*(Mở rộng sau khi có BGIS/CHGIS data thật)*

---

## GIAI ĐOẠN C — Phân loại & Deliverables

### Bước 1009 · [EDIT] Tạo founding_date_sources.json
```powershell
python -c "
import json
sources = [
    {'source': 'DILA_RAW_XML', 'type': 'EVIDENCE_REUSE', 'coverage_estimated': 'TBD_from_step_1002', 'founding_date': 'in_narrative_text', 'match_key': 'direct_dila_id', 'license': 'CC BY-SA', 'api': False, 'download': True},
    {'source': 'WIKIDATA_P1188', 'type': 'DIRECT_REUSE', 'coverage_estimated': 148, 'founding_date': 'P571_structured', 'match_key': 'P1188_dila_id', 'license': 'CC0', 'api': True, 'download': True},
    {'source': 'WIKIDATA_SPATIAL', 'type': 'DIRECT_REUSE', 'coverage_estimated': 1958, 'founding_date': 'P571_structured', 'match_key': 'gps_0.5km', 'license': 'CC0', 'api': True, 'download': True},
    {'source': 'CHGIS_TEMPLES', 'type': 'DIRECT_REUSE', 'coverage_estimated': 2407, 'founding_date': 'structured_from_DaQing_YitongZhi', 'match_key': 'name_or_gps', 'license': 'CC BY', 'api': True, 'download': True},
    {'source': 'BGIS_2006', 'type': 'TBD_pending_step_1007', 'coverage_estimated': 17933, 'founding_date': 'starting_year_TBD', 'match_key': 'name_or_gps', 'license': 'TBD', 'api': False, 'download': True},
    {'source': 'BDRC', 'type': 'CONTEXT_ONLY', 'coverage_estimated': '<100_chinese', 'founding_date': 'bdo_placeEvent_tibetan_only', 'match_key': 'none', 'license': 'CC BY 4.0', 'api': True, 'download': True},
    {'source': 'OLLAMA_QWEN', 'type': 'NLP_REQUIRED', 'coverage_estimated': '~53000_remaining', 'founding_date': 'extracted_from_raw_xml', 'match_key': 'direct_dila_id', 'license': 'free_local', 'api': False, 'download': False},
]
with open('data/founding_date_sources.json', 'w', encoding='utf-8') as f:
    json.dump(sources, f, ensure_ascii=False, indent=2)
print('JSON created: data/founding_date_sources.json')
"
```

---

### Bước 1010 · [EDIT] Tạo T22.1 Audit Report
Tạo file: `docs/T22.1_FOUNDING_DATE_DATA_REUSE_AUDIT.md`
Điền đầy đủ:
- Kết quả Giai đoạn A (số liệu thực tế từ bước 1001-1002)
- Kết quả Giai đoạn B (BGIS inspection, Wikidata, CHGIS)
- Phân loại: Direct Reuse X / Evidence Reuse Y / NLP Required Z
- Khuyến nghị: Reuse First hay NLP Required?
- Sign-off request → Lee Tổng

---

### Bước 1011 · [LOG] Cập nhật directives_progress.json
```json
{
  "current_group": "T22.1 done — chờ Lee Tổng review",
  "current_step": 1011,
  "note": "Audit xong: X/59K có raw_xml pattern, Wikidata 2106, BGIS TBD, CHGIS 2407",
  "percent_total": "T22.1 complete"
}
```

---

### Bước 1012 · [SHELL] Dashboard
```powershell
python scripts/build_progress_data.py
```

```
⛔ DỪNG SAU BƯỚC 1012 — TUYỆT ĐỐI KHÔNG viết NLP pipeline.
   Chờ Lee Tổng nghiệm thu 3 deliverables:
   1. docs/T22.1_FOUNDING_DATE_DATA_REUSE_AUDIT.md
   2. data/founding_date_sources.json
   3. data/founding_date_source_coverage.csv
   
   Sau khi được sign-off → mới bắt đầu T22 (NLP pipeline theo T22 task file).
```

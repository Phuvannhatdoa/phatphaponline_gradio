---
id: T445
title: "Wizard UI cho T444 Gemini Places Translation (B0-B9)"
status: coding
depends_on: [T444]
timeline:
  created: 2026-10-21
  deadline: 2026-10-21
priority: high
description: |
  Nâng cấp placevn.html thành Wizard Flow UI (B0→B9) để phục vụ T444 Gemini places batch translation.
  Thay thế tabbed UI bằng linear wizard (9 steps), real-time WebSocket monitoring, tối ưu UX + state.
---

## Mục Đích

**Task T444** = Backend Gemini batch translate 59.150 địa danh (Hán → Việt)
**Task T445** = Frontend Wizard UI để admin chạy T444 từng bước B0→B9, monitor real-time, duyệt kết quả.

Kết quả:
- Admin mở placevn.html → Wizard Step 1/9 (Backup)
- Click "Next" → Step 2/9 (Fix ID) → ... → Step 9/9 (Report)
- Sau xong: CSV export + HOME search ready ("Trường An", "Lạc Dương" mới)

---

## Scope (Wizard Flow — B0 to B9)

### **9 Steps (Linear Flow)**

| Step | B-Code | Tên | Hành động | Output |
|------|--------|-----|----------|--------|
| 1/9 | B0 | Backup DB | Admin click "Backup Now" | lineage_2026-10-21-*.db |
| 2/9 | B1 | Fix 3.800 ID | View preview + checkbox + Export CSV | sample_b1_fixed.csv |
| 3/9 | B2 | Add DB Columns | Auto-run (schema: source, needs_review, reason, updated_at) | DB updated |
| 4/9 | B3 | Load Dictionary | Auto-run (load 2.446 từ điển) | DB updated |
| 5/9 | B4 | Edit 7 Rules | Form table: Hán | Cũ | Mới, save inline | rules updated |
| 6/9 | B5 | Gemini Batch 1 | Real-time progress + **WebSocket log stream** + error list | 40.199 rows translated |
| 7/9 | B7 | Sample 100 Review | View grid + hierarchical filter + checkbox + Approve | 100 rows approved |
| 8/9 | B8 | Gemini Batch 2 | Real-time progress + log + error list (like B5) | 40.099 rows translated |
| 9/9 | B9 | Report | Stats + missing/duplicate list + CSV downloads | 3 CSV files |

### **Key Features**

- ✅ **Linear Flow:** Enforce order (B0→B1→...→B9), no tab confusion
- ✅ **Auto-Progress:** B2/B3 auto (no manual click)
- ✅ **WebSocket Real-time:** B5/B8 live log (not polling), latency <100ms
- ✅ **Simple State:** 1 state (`wizardStep: 0-8`), no 8 separate tab states
- ✅ **Resume Support:** If interrupted, return to same step
- ✅ **CSV Export:** B1 + B9 ready for HOME team
- ✅ **HOME Ready:** After B9, `/places?source=gemini` API ready for HOME search

---

## Implementation Details

### **A. placevn.html Changes**

**File:** `daoanh/admin/placevn.html`

**Current:**
- Sidebar 4 tabs (queue, untranslated, review/ReviewView, all)
- Main form (name_vi, gps, district, etc.)
- ReviewView component only

**New:**
- **Remove tabbed UI** (sidebar tabs)
- **Add Wizard Modal** (overlay, full-screen)
- **9 Step Components:**
  - BackupStep (B0) — dialog "Backup Database?"
  - FixIdStep (B1) — checkbox grid + Export button
  - SchemaStep (B2) — info panel (auto-progress)
  - DictionaryStep (B3) — info panel (auto-progress)
  - RulesStep (B4) — table + inline form edit
  - BatchMonitorStep (B5) — progress bar + **WebSocket log** + error list
  - SampleStep (B7) — grid + hierarchical filter + Approve
  - Batch2Step (B8) — progress bar + log (like B5)
  - ReportStep (B9) — stats + CSV download

**State:**
```javascript
// Single state instead of 8 separate tab states
const [wizardStep, setWizardStep] = useState(0);  // 0-8
const [stepData, setStepData] = useState({
  b0: {backup_status, backup_path},
  b1: {selected_ids, csv_ready},
  b3: {dictionary_loaded, count},
  b4: {rules, editing_id, pending_save},
  b5: {batch_status, progress, logs, errors},
  b7: {sample_data, categoryFilter, selected},
  b8: {batch_status, progress, logs, errors},
  b9: {stats, missing, duplicate}
});

// WebSocket for real-time monitoring (B5/B8)
const [ws, setWs] = useState(null);
useEffect(() => {
  if (wizardStep === 5 || wizardStep === 7) {
    const socket = new WebSocket('ws://localhost:5000/ws/batch-monitor');
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setStepData(prev => ({...prev, [activeStep]: data}));
    };
    setWs(socket);
    return () => socket.close();
  }
}, [wizardStep]);
```

**UI Layout:**
```html
<div className="fixed inset-0 bg-black/50 flex items-center justify-center">
  <div className="bg-dark-card w-full max-w-3xl max-h-screen overflow-y-auto rounded-xl">
    <!-- Header: Step X/9 + Title -->
    <div className="sticky top-0 border-b border-slate-700 p-6">
      <h2>T444 Wizard ({wizardStep + 1}/9) — {stepTitle}</h2>
    </div>
    
    <!-- Step Content (dynamic per wizardStep) -->
    <div className="p-6">
      {wizardStep === 0 && <BackupStep {...stepData.b0} />}
      {wizardStep === 1 && <FixIdStep {...stepData.b1} />}
      {/* ... B2-B9 ... */}
    </div>
    
    <!-- Footer: Navigation -->
    <div className="sticky bottom-0 border-t border-slate-700 p-6 flex justify-between">
      <button onClick={() => setWizardStep(s => s - 1)} disabled={wizardStep === 0}>
        ← Back
      </button>
      <div className="text-xs text-slate-500">Step {wizardStep + 1}/9</div>
      <button onClick={() => setWizardStep(s => s + 1)} disabled={wizardStep === 8}>
        Next →
      </button>
    </div>
  </div>
</div>
```

### **B. API Endpoints (app.py)**

**New routes:**
- `POST /api/admin/backup` — trigger backup, return backup_path
- `POST /api/admin/fix-ids` — fix 3.800 ID, export CSV
- `POST /api/admin/load-dictionary` — load 2.446 từ điển
- `POST /api/admin/update-rules` — update 7 rules
- `POST /api/admin/approve-sample` — approve 100 sample rows
- `WS /ws/batch-monitor` — WebSocket endpoint for real-time batch progress
- `POST /api/admin/report` — generate final report + stats
- `GET /api/admin/export-csv?type=missing|duplicate|full` — download CSV

### **C. WebSocket Server (app.py)**

**For B5/B8 real-time monitoring:**
```python
from flask import WebSocket
import json
import threading

active_batch = None

@app.websocket('/ws/batch-monitor')
def batch_monitor(ws):
    global active_batch
    try:
        while True:
            # Server broadcasts progress every 2s
            if active_batch:
                data = {
                    'type': 'batch_progress',
                    'step': active_batch['step'],  # 'b5' or 'b8'
                    'progress': active_batch['progress'],  # 5000/40199
                    'logs': active_batch['logs'][-100:],  # last 100 lines
                    'errors': active_batch['errors'],
                    'stats': {
                        'ok': active_batch['ok_count'],
                        'review': active_batch['review_count'],
                        'error': active_batch['error_count']
                    }
                }
                ws.send(json.dumps(data))
            time.sleep(2)  # every 2s push update
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
```

---

## Timeline

- **BackupStep:** 5 min (dialog)
- **FixIdStep:** 10 min (table + checkbox + export)
- **SchemaStep/DictionaryStep:** 5 min (info panels)
- **RulesStep:** 10 min (form table)
- **BatchMonitorStep (B5):** 15 min (progress + WebSocket)
- **SampleStep:** 15 min (grid + filter)
- **ReportStep:** 15 min (stats + CSV download)
- **State + WebSocket integration:** 20 min
- **API endpoints (app.py):** 30 min
- **Test + debug:** 20 min
- **Commit + docs:** 10 min

**Total: 2.5 hours**

---

## Files to Modify/Create

| File | Action | Details |
|------|--------|---------|
| `daoanh/admin/placevn.html` | **MODIFY** | React Wizard component (9 steps) |
| `daoanh/app.py` | **MODIFY** | 8 new API endpoints + WebSocket /ws/batch-monitor |
| `daoanh/static/wizard-icons.js` | **CREATE** | SVG icons for wizard steps (optional) |
| `docs/plans/T445-wizard-ui-plan.md` | **CREATE** | Detailed design doc |

---

## Verification Checklist

- [ ] Wizard modal renders (step 1/9)
- [ ] Navigation [← Back] [Next →] works
- [ ] B0 Backup button → POST /api/admin/backup works
- [ ] B1 Fix ID preview + checkbox + CSV export works
- [ ] B2/B3 auto-progress (no manual click)
- [ ] B4 Rules form editable + save works
- [ ] B5 Batch monitor WebSocket receives real-time updates (no polling)
- [ ] B7 Sample grid + filter works
- [ ] B9 Report shows stats + CSV downloads work
- [ ] Resume: if close and reopen, return to same step
- [ ] CSV files ready for HOME team import

---

## Dependencies

- **T444 Backend:** Gemini batch script + API endpoints must be ready
- **Database:** `ai_place_name` table has columns: place_id, name_zh, name_vi, source, confidence, needs_review, reason, updated_at
- **WebSocket:** Flask WebSocket support (already in app.py imports)

---

## Status

⏸️ **PENDING** — Awaiting approval to start coding (Wizard Flow approved by Admin on 2026-10-21)

Next: daoanh-debugger codes placevn.html Wizard + app.py endpoints

## Các bước (MA giao cho coder — 2026-11-01)

Trạng thái thật (kiểm 2026-11-01): `app.py` HEAD **chưa có** route nào của T445 (0/8). `admin/placevn.html` HEAD chưa có wizard; bản bổ sung (+74 dòng) chỉ có khung giao diện, chưa gọi API. Xem `docs/sessions/2026-10-25/T445-coder/REVIEW.md`.

Quy tắc chung: coder chỉ viết code. **Không** chạy `--apply`, không ghi DB ngoài môi trường test, không commit. Mọi thao tác ghi DB cần dry-run và Admin duyệt riêng (HARNESS_WORKFLOW mục 3).

- [ ] B0: thêm `POST /daoanh/api/admin/backup` — sqlite backup nhất quán, trả `backup_path`.
- [ ] B1: thêm `POST /daoanh/api/admin/fix-ids` — preview 3.800 ID, xuất `sample_b1_fixed.csv`. Chỉ đọc khi preview.
- [ ] B2: thêm `POST /daoanh/api/admin/load-schema` — thêm cột `source, needs_review, reason, updated_at` vào `ai_place_name`, idempotent. Dry-run trước, không tự apply.
- [ ] B3: thêm `POST /daoanh/api/admin/load-dictionary` — nạp 2.446 mục từ điển, idempotent. Dry-run trước.
- [ ] B4: thêm `POST /daoanh/api/admin/update-rules` — lưu 7 quy tắc (form inline).
- [ ] B5: thêm `GET /daoanh/api/admin/batch-monitor` — polling trạng thái batch (thay WebSocket theo Flask 3.1).
- [ ] B7: thêm `POST /daoanh/api/admin/approve-sample` — nạp 100 mẫu, duyệt mục chọn.
- [ ] B9: thêm `POST /daoanh/api/admin/report` và `GET /daoanh/api/admin/export-csv?type=missing|duplicate|full`.
- [ ] Nối giao diện: `admin/placevn.html` gọi các route trên, giữ nguyên mã cũ (chỉ thêm).
- [ ] Kiểm cú pháp `app.py` và `placevn.html`; ghi kết quả vào `outcome`.

Ghi chú: route mới đặt trước `if __name__ == '__main__':` cuối cùng của `app.py`.

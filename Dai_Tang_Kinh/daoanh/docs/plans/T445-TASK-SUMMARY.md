# T445 — Wizard UI cho T444 Gemini Places Translation (B0-B9)

**Date:** 2026-10-21  
**Status:** ⏳ PENDING — Ready for dispatcher approval  
**Duration:** 2.5 hours  
**Depends on:** T444 (Backend Gemini batch + API)

---

## 📋 Task Summary

### Mục Đích
Nâng cấp `placevn.html` từ tabbed UI → **linear Wizard flow** (9 steps B0→B9) để admin chạy T444 Gemini places translation pipeline từng bước, monitor real-time, duyệt kết quả.

### Lợi Ích So Với Tabbed Plan Cũ
| Aspect | Tabbed (Cũ) | **Wizard (Mới)** |
|--------|-----------|------|
| **UX** | 8 tabs (confusing) | Step-by-step (clear) |
| **Order** | No enforcement | B0→B9 enforced |
| **Code** | 8 separate states | 1 state (`wizardStep: 0-8`) |
| **Monitoring** | Poll 5s lag | **WebSocket real-time** |
| **Timeline** | 3.5h | **2.5h** (-1h) |
| **HOME Ready** | CSV available | **API + CSV ready** |

---

## 🚀 9 Steps (B0→B9)

| Step | Code | Name | Admin Action | Output |
|------|------|------|--------------|--------|
| 1/9 | B0 | Backup DB | Click "Backup Now" | lineage_*.db |
| 2/9 | B1 | Fix 3.8K ID | Checkbox + Export CSV | sample_b1_fixed.csv |
| 3/9 | B2 | Add Columns | Auto (schema update) | DB updated |
| 4/9 | B3 | Load Dictionary | Auto (2.446 từ điển) | DB updated |
| 5/9 | B4 | Edit 7 Rules | Form table + Save | Rules saved |
| 6/9 | B5 | Gemini Batch 1 | **Watch real-time log** | 40.199 rows |
| 7/9 | B7 | Sample 100 | Approve | 100 rows OK'd |
| 8/9 | B8 | Gemini Batch 2 | **Watch real-time log** | 40.099 rows |
| 9/9 | B9 | Report | Download CSV | 3 CSV files |

---

## 📝 Implementation Scope

### Files to Modify/Create
- ✏️ `daoanh/admin/placevn.html` — React Wizard component (9 steps)
- ✏️ `daoanh/app.py` — 8 new API endpoints + WebSocket `/ws/batch-monitor`

### Key Features
- ✅ Linear flow (enforce B0→B9 order, no tab confusion)
- ✅ Auto-progress (B2/B3 no manual click)
- ✅ **WebSocket real-time** (B5/B8 live log, <100ms latency, not polling)
- ✅ Simple state (1 `wizardStep` vs 8 tab states)
- ✅ CSV export (B1 + B9 for HOME team)
- ✅ HOME API ready: `/places?source=gemini&needs_review=0`

---

## 🎯 Expected Result (After Completion)

### Admin Experience
1. Open placevn.html → Wizard modal (1/9 Backup)
2. Click "Backup Now" → ✓ Success → Click "Next"
3. Step 2/9 (Fix ID): Preview 3.8K + checkbox + Export CSV → Click "Next"
4. Steps 3-4: Auto-progress (schema + dictionary)
5. Step 5: Edit 7 rules (form table) → Save → Next
6. Step 6: **Real-time progress bar** (5000/40199, 12%) + **live log stream** (scrolling JSONL) + error count → Auto-complete
7. Step 7: Review 100 samples (grid + filter) → Approve All → Next
8. Step 8: **Real-time progress** (like step 6) → Auto-complete
9. Step 9: **Report** → Stats: "Success: 39.999 (67.6%), needs_review: 150, errors: 1" → Download CSV buttons

### HOME User Experience (After CSV Import)
```
🔍 Tìm địa danh... [Trường An  ___]
  🟢 Trường An (長安)
     📍 Xian, China | ⭐ Draft (Gemini)
     GPS: 34.2658°N, 108.9398°E
```

**Search `/api/places?source=gemini`** works for HOME autocomplete.

---

## ✅ Verification Checklist

- [ ] Wizard modal renders (step 1/9)
- [ ] Navigation [← Back] [Next →] works
- [ ] B0 Backup → POST /api/admin/backup works
- [ ] B1 Fix ID checkbox + CSV export works
- [ ] B2/B3 auto-progress (no wait)
- [ ] B4 Rules form + save works
- [ ] **B5 WebSocket real-time** (no 5s polling)
- [ ] B7 Sample grid + filter works
- [ ] B9 Report + CSV download works
- [ ] Resume: close & reopen → same step
- [ ] CSV ready for HOME import

---

## 🔗 Related Tasks
- **T444:** Backend Gemini batch (dependencies: must complete before T445 UI can work end-to-end)
- **T442:** Places analysis (foundation for T445)
- **T443:** Places import (API dependency for T445)

---

## 📅 Timeline
- **2026-10-21:** Plan approved
- **2026-10-21 (Pending):** Dispatcher assigns to daoanh-debugger
- **2026-10-21 (Est. 2.5h):** Code placevn.html + app.py
- **2026-10-21 (Est. 0.5h):** QA + verification
- **2026-10-21 (Est.):** Admin approval DONE

---

## 📌 Next Steps
1. ✅ Task T445 created with full details
2. ✅ tasktodo.md updated
3. 👉 **Dispatcher:** Assign to daoanh-debugger when ready
4. 👉 **daoanh-debugger:** Code placevn.html Wizard + app.py endpoints
5. 👉 **daoanh-qa:** QA verification
6. 👉 **Admin:** Final approval

---

**Admin phê chuẩn:** Chờ signal "APPROVE" hoặc "DISPATCH" để daoanh-debugger start code.

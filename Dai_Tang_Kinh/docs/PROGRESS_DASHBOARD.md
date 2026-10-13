# 📊 Đạo Ảnh Progress Dashboard (2026-10-12)

**Last Updated:** Oct 12, 2026 — After Architecture Audit + Phase 1 Planning

---

## 🎯 PROJECT STATUS

| Item | Status | Progress | ETA |
|------|--------|----------|-----|
| **Overall Project** | 🟠 ON TRACK | 20% (1 of 5 weeks) | Dec 16, 2026 |
| **Phase 1 (Stabilization)** | 🟡 PLANNING | 0% | Week 1-2 |
| **Phase 2 (Performance)** | ⏳ QUEUED | 0% | Week 3-5 |
| **Phase 3 (Modularity)** | ⏳ QUEUED | 0% | Week 6-8 |
| **Phase 4 (Data Integrity)** | ⏳ QUEUED | 0% | Week 9-12 |

---

## ✅ COMPLETED TASKS

| Task | Title | Status | Commit | Date |
|------|-------|--------|--------|------|
| **T309** | Verify Lâm Tế Lineage Tree | ✅ DONE | (Oct 11) | Oct 12 |
| **T359 Fix 1-3** | Person detail (Teacher/Student, Timeline, Place) | ✅ CODE READY | `36ed846` | Oct 12 |

**Browser Verified:**
- ✅ Lâm Tế tree (47 nodes) displays correctly
- ✅ A000035 person page: 3 sections load with correct data
- ✅ No API errors, no JS console errors

---

## 🔄 IN PROGRESS

| Task | Title | Status | Next Step | Owner |
|------|-------|--------|-----------|-------|
| **Harness Proposal** | T359 approval (Fix 1-3 only) | 📋 Review | Waiting admin decision | Harness Agent |
| **Plan Audit** | Architecture review | ✅ COMPLETE | Findings captured | Plan Agent |
| **T360** | Vietnamese source badges | 🟡 PLAN READY | Waiting approval | daoanh-debugger |

---

## ⏳ QUEUED (PHASE 1 QUICK WINS)

| Task | Title | Timeline | Priority | Owner |
|------|-------|----------|----------|-------|
| **T360** | Vietnamese source badges | 8-9h | 🔴 HIGH (blocks T359) | daoanh-debugger |
| **T361** | API versioning (v1/v2) | 4-6h | 🟡 MEDIUM | daoanh-debugger |
| **T362** | Error standardization | 6-8h | 🟡 MEDIUM | daoanh-debugger |

**Phase 1 Total:** ~20-25 hours (1-2 weeks, can parallelize)

---

## ⏸️ DEFERRED

| Task | Reason | Unblock Condition | Phase |
|------|--------|-------------------|-------|
| **T359 Fix 4-6** | Data mapping broken (CBETA/Works/Places) | After Phase 4 (data rebuild) | Phase 4 |
| **Lô 1 (15 tasks)** | Waiting Phase 1 completion | T360+T361+T362 done | Phase 2 |

---

## 🔴 ARCHITECTURE ISSUES (10 Found)

### Critical Issues (Block Progress)

| # | Issue | Severity | Phase | Impact | Status |
|---|-------|----------|-------|--------|--------|
| 8 | No source badges | MEDIUM | **Phase 1** | T359 incomplete | T360 created ✅ |
| 5 | CBETA mapping broken | MEDIUM | **Phase 4** | T359 Fix 4-6 blocked | T359b planned ✅ |
| 4 | Missing entity tables | MEDIUM | **Phase 4** | T359 Fix 5-6 blocked | Design pending |

### Other Issues (Improve Quality)

| # | Issue | Severity | Phase | Fix Timeline |
|---|-------|----------|-------|--------------|
| 1 | Monolithic app.py | HIGH | Phase 3 | 1-2w |
| 2 | Denormalized schema | HIGH | Phase 4 | 4-6w |
| 3 | N+1 queries | MEDIUM-HIGH | Phase 2 | 2-3w |
| 6 | No API versioning | MEDIUM | Phase 1 | 1w (T361) |
| 7 | No transactions | MEDIUM | Phase 1 | 1w |
| 9 | Lexicon in-RAM | LOW-MEDIUM | Phase 2 | 1-2w |
| 10 | Error inconsistency | LOW-MEDIUM | Phase 1 | 2-3w (T362) |

---

## 📈 PHASE BREAKDOWN

### Phase 1: Stabilization (Weeks 1-2)
```
Objective: Fix critical quality issues without breaking existing code

✅ PLAN READY:
  □ T360: Vietnamese source badges (8-9h, HIGH)
  □ T361: API versioning (4-6h, MEDIUM)
  □ T362: Error standardization (6-8h, MEDIUM)
  
  Total: ~20-25 hours
  Status: Awaiting admin approval to start

✅ T359 Fix 1-3: Ready to merge (after T360)
```

### Phase 2: Performance (Weeks 3-5)
```
Objective: Optimize database queries & memory usage

□ Fix N+1 query loops (~20 patterns)
□ Replace lexicon in-RAM cache with SQLite FTS
□ Add database connection pooling
□ Add query indexing strategy

Est: 3 weeks
Status: Design phase
```

### Phase 3: Modularity (Weeks 6-8)
```
Objective: Split monolithic app.py into feature blueprints

□ Split app.py (1.1MB → 5 modules)
  - api/persons.py
  - api/places.py
  - api/admin.py
  - api/search.py
  - api/export.py
□ Add unit tests
□ Update deployment

Est: 3 weeks
Status: Design pending
```

### Phase 4: Data Integrity (Weeks 9-12)
```
Objective: Fix denormalized schema + incomplete imports

□ Consolidate places tables (places + places_dila → single places with source)
□ Create person_activity table (for activeAt, birthplace, etc.)
□ Create passage_entity_mention table (for CBETA passage links)
□ Create entity_merge_log + audit trail
□ Document SSOT merge strategy

Est: 4 weeks
Status: Design pending

⚠️ UNBLOCKS:
   - T359 Fix 4-6 (Fix 5: Works import, Fix 6: ActiveAt places)
   - CBETA mapping fix (158 "了然" rows re-assignment)
```

---

## 📋 NEXT ADMIN ACTIONS

### Immediate (Today)

- [ ] **Approve T360** — Start Vietnamese source badges (HIGH priority, blocks T359 approval)
- [ ] **Approve T361** — Start API versioning (can parallelize with T360)
- [ ] **Approve T362** — Start error standardization (can parallelize)

### After Phase 1 Complete

- [ ] **Review T359 Fix 1-3** (with source badges) → approve or request changes
- [ ] **Plan Phase 2** — Prioritize which performance improvements first
- [ ] **Queue Lô 1 tasks** (15 remaining tasks from original roadmap)

---

## 📊 METRICS

### Code Quality Baseline (from audit)
| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| API error standardization | 0% | 100% | T362 |
| Source data transparency | 0% | 100% | T360 |
| API versioning | 0% | 100% | T361 |
| Database indexing | 30% | 100% | Phase 2 |
| Transaction management | 0% | 100% | Phase 1 |

### Task Completion
| Status | Count | % |
|--------|-------|---|
| ✅ Completed | 2 | 5% |
| 🟡 In Review | 0 | 0% |
| ⏳ Queued Phase 1 | 3 | 8% |
| ⏳ Queued Phase 2-4 | ~40 | 87% |
| **Total** | **45+** | **100%** |

---

## 🚨 RISKS & MITIGATIONS

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Phase 1 tasks take longer | Delays Phase 2 | MEDIUM | Parallelize T360+T361+T362 |
| Phase 4 data work is complex | Blocks T359b + Lô 1 | HIGH | Start Phase 4 planning early |
| Legacy code (app.py) changes break tests | Regression | MEDIUM | Add unit tests (Phase 3) |
| CBETA mapping fix requires manual work | Admin burden | HIGH | Document merge strategy before Phase 4 |

---

## 📞 KEY CONTACTS

| Role | Person | Task | Status |
|------|--------|------|--------|
| Admin (No-coding) | User | Overall approval | ⏳ Waiting |
| Lead AI Engineer | Claude | Coordinator/Architect | 🔄 In progress |
| Debugger | daoanh-debugger | Fix code bugs | ⏳ Queued (T360) |
| QA | daoanh-qa | Verify fixes | ⏳ Queued (T360) |
| Architect | Plan Agent | System design | ✅ Completed |

---

## 📅 TIMELINE

```
Oct 12 (Today)
├─ ✅ Architecture audit complete (Plan agent)
├─ ✅ Phase 1 tasks created (T360/361/362)
├─ ⏳ Harness proposal in review (T359 approval)
└─ ⏳ Awaiting admin decisions

Oct 13-19 (Week 1)
├─ Phase 1: T360+T361+T362 (if approved)
└─ T359 review: Fix 1-3 + T360 badges

Oct 20-26 (Week 2)
├─ Phase 1 completion
├─ T359 approval (Fix 1-3 DONE)
└─ Phase 2 planning

Oct 27-Nov 9 (Week 3-5)
├─ Phase 2: Performance work
└─ Lô 1 tasks (parallel if possible)

Nov 10-Dec 7 (Week 6-9)
├─ Phase 3: Modularity
└─ Phase 4 start: Data integrity

Dec 8-16 (Final Week)
├─ Phase 4 completion
├─ T359b Fix 4-6 (after Phase 4)
└─ Final QA + handoff

ETA: Dec 16, 2026 (5 weeks from Oct 12)
```

---

**Status:** 🟠 **ON TRACK** — All decisions made, Phase 1 ready to start

**Blockers:** None (waiting for admin approval)

**Last Review:** Oct 12, 2026 (today)

**Next Review:** Oct 19, 2026 (end of Week 1)

# Session 2026-09-26 — Search Perf Fix + Code Review + Task Audit

## Đã hoàn thành

### T178 perf — Search box 10s → 470ms

Root cause 1: `ensure_places_pending_fts` chạy JOIN COUNT 7.8s mỗi khi worker Flask restart.
Fix: thay `SELECT COUNT(*)` JOIN 7-bảng bằng `SELECT rowid FROM places_pending_fts LIMIT 1` (0.5ms).

Root cause 2: `ensure_places_search_fts` COUNT(docsize)+COUNT(namevi) (170ms) mỗi lần.
Fix: thay bằng `SELECT rowid FROM places_search_fts LIMIT 1` (9.7ms).

Root cause 3: `people` table (48k rows) không có index trên `name_vi`/`name_zh`.
Fix: `CREATE INDEX idx_people_name_vi ON people(name_vi)` — exact match 513ms → 0.7ms.
Fix: `CREATE INDEX idx_people_name_zh ON people(name_zh)`.

Kết quả: search từ >10s → ~470ms; remaining 460ms từ monk-resolve LIKE (cần people_search_fts — task chip đã spawn).

### Code Review (5 findings, all fixed)

1. `app.py:18328` — `rules_outdated` always False → load `_cur_lock_ch` từ `_t73_style_lock` trước loop.
2. `places.html` — Quicklist race condition → AbortController trong `_fetchAndRenderQuicklist`.
3. `app.py:16582` — `time.sleep(2s)` in Flask worker → giảm `_T73_429_BACKOFF_BASE` 2→0.5.
4. `app.py:16653` — `except Exception` không retry → sửa thành `attempt += 1; continue`.
5. `places.html` — Quicklist fetch duplicated → extracted `_fetchAndRenderQuicklist(ql, pid)` helper.

### T122 D4 — Docs hygiene verified

- Stub T51, T52-analytics-dashboard đã trong tasks/backup/ ✓
- BUG-009 closed-as-duplicate trong docs/tasktodo.md ✓
- Dashboard regen: 95 tasks, done=61, blocked=2, 15 modules, 246 endpoints, 71% tiến độ.

### T140 sub ①②③ — Verified already done từ phiên trước

- ① `up=2&down=2` đã ở line 5167/5419; auto-expand center+1gen ở line 6565-6573.
- ② No N/A literals, all fields null-guarded trong `_renderDilaExtra`.
- ③ 0 ZENLINEAGE assertions trong DB → không có gì để ẩn; inspector code đã gated đúng.
- AbortController `loadLineageTree`/`centerLineageOn` đã done (line 5143, 5413).

## Files changed

- `daoanh/app.py` — 4 fixes (rules_outdated, backoff 2→0.5, retry continue, ensure_fts LIMIT 1×2)
- `daoanh/data/lineage.db` — 2 new indexes (idx_people_name_vi, idx_people_name_zh)
- `daoanh/data/progress_data.json` — regen dashboard

## Todo tiếp theo

- [ ] people_search_fts FTS5 table → monk-resolve 460ms → ~5ms (task chip spawned)
- [ ] BUG-014 → test in real browser, admin confirm Nexus không jitter
- [ ] T73 → test bio review UI, admin confirm done
- [ ] Git commit tất cả changes (blocked bởi git index anomaly — cần user confirm)

---

## Session 2026-09-27 — Task Audit Batch (tiếp phiên trước)

### Verified + set done (không cần build thêm)

- **T135** (Doctrine-Retrieval-Conformance): P1 research audit trail `/daoanh/api/research/entity/<id>/audit-trail` tồn tại tại app.py:19215; P2 `docs/RETRIEVAL_ENGINE_SPEC.md` tồn tại. done=68.
- **T178** (5 gap D3/D8 mục 13–17): tất cả ✅ checkmark trong task file; tests/test_t178_gap_d3.py 8 functions PASS. done=70 (kèm T179).
- **T179** (Phase 8 XML boundary + Trie + đính chính T178): tất cả phases done; tests/test_t179_phase8.py 5 functions PASS.
- **T96** (Per-Segment Translation): thỏa done_when qua T85 build: `_t85_post_segments` lưu vào `translation_segments`; frontend `dtTranslateNextN` + `.dt-seg-han/vi` bilingual display. done=71.

### Tình trạng còn lại (cần admin/build)

- T22: blocked admin download CHGIS/BGIS từ Harvard Dataverse
- T50: cần chạy `python scripts/t50_passage_vi_backfill.py --sigla T51n2076 --limit 0 --sleep 1.0` (Groq key sẵn)
- T73: chờ admin test bio review UI → set done
- T100 Batch 4+5: P2-MASTER (schema additive doctrine_concept + evidence drawer) — large build
- T121: chờ admin review hồi quy + cron cài đặt
- T140: chờ admin QA thủ công
- T167: chờ human review/score benchmark
- BUG-014: chờ admin confirm Nexus không jitter

### Dashboard cuối session: done=71, blocked=2, 95 tasks, 71%

---

## Session 2026-09-27 (tiếp) — Fix Alert #1 T100

### fix_tabs.js: thêm nexus + entities (17 tabs)

**Vấn đề:** Alert #1 `build_tab_readiness.py` báo "Tab bar lệch" vì `fix_tabs.js` có 15 tabs, `places.html` có 17 tabs — thiếu `nexus` và `entities`.

**Fix:** Thêm 2 tab vào `fix_tabs.js`:
- `nexus` (🔥 Nexus) sau `lineage`, khớp thứ tự trong `places.html`
- `entities` (🧩 Thực Tổng Hợp) cuối cùng

**Kết quả `build_tab_readiness.py`:**
- Alert #1 → RESOLVED (fix_tabs.js = 17 = places.html 17)
- Alert #4 (entity_claims 100% unverified) → RESOLVED (đã fix trước)
- Alert #5 (events 100% candidate) → OPEN (data work, cần P3)
- core_avg = 10.33/12, release gate MET

### Dashboard: done=71, blocked=2, 95 tasks, 71%

### Còn lại cần làm:
- [ ] T181 Build (CBETA lazy import): P1 mapping script → P2 download guide → P3 catalog API → P4 import API → P5 UI
- [ ] Admin: `git clone --depth=1 https://github.com/cbeta-git/cbeta-xml-p5a.git data/cbeta/xml-p5a` (thủ công, ~2GB)
- [ ] T100 Batch 5 (P3+P4): dataset_version + export; review/dispute workflow; regression + release gate ≥8
- [ ] Alert #5 events 100% candidate: promote events từ candidate → verified (data work)
- [ ] T50: chạy backfill `python scripts/t50_passage_vi_backfill.py --sigla T51n2076 --limit 0 --sleep 1.0`
- [ ] T73: admin approve 1 bio
- [ ] T121: admin hồi quy review + cron setup
- [ ] T140: admin QA manual (click A→B→C, zoom, filter)
- [ ] BUG-014: admin confirm Nexus không jitter trong real browser
- [ ] Git commit toàn bộ changes (blocked bởi git index anomaly — cần user confirm)

# Session Log — 2026-08-25 (Afternoon + Evening)

## Tasks Completed

### T32 Expansion — Fix 3 Extraction Bugs ✅
- **Bug 1:** ERA_HINT pre-filter in dynasty script → clause-scoped (+301 dynasty dates)
- **Bug 2:** Renovation context ±20 chars → clause-aware in note+era scripts (+97 note, +22 era)
- **Bug 3:** Sentence-boundary false positive → only skip if renovation in previous sentence
- **Result:** 2,743→3,196 rows, 2,703→3,135 places, 4.6%→5.3% coverage
- **Scripts modified:** `dila_note_founding_extract.py`, `dila_era_name_extract.py`, `dila_dynasty_range_extract.py`

### T16 Cancelled ✅
- CBETA XML P5a has no persName/placeName/date tags (only 5 files, 14 MB)
- Full CBETA XML = 388 GB — not feasible
- Nexus data already achieved via T39/T40/T41/T42/T43 (91K person-place links)

### T50 CBETA Data Cleanup — Done ✅ (T50c skipped)
- **T50a:** Fuzzy quality flag — 56,318 low-confidence flagged (91.3%), 5,388 high (8.7%)
- **T50b:** Legacy canon merged — 2,698 rows from buddhist_db.sqlite → legacy_canon_mapping
- **T50d:** Catalog mapping audit — 0 orphaned (all 6,564 valid)
- **T50c:** Skipped — needs Gemini API key (run later)
- **API:** Added `/admin/cbeta/quality-report` endpoint to app.py

### T51/T52 Created (Pending)
- T51: CBETA Content Enhancement — batch translate, expand Toh, build aggregates
- T52: CBETA Analytics & Admin Dashboard — stats dashboard, Home CBETA tab

### T27 → Blocked Until Needed (done by: T23✅ T24✅ T26✅)
- All dependencies complete, waiting for right moment to implement

### Session Commits (2026-08-25)
- `b8c59f9` feat(T50): CBETA cleanup scripts + quality-report API + T51/T52 tasks created
- `8cf0397` docs: session logs + task files T47/T48/T49 + todo audit scripts
- `76d9914` feat(T34): delete 84000/VRI/Kanripo fake data (Phase A)
- `7abc849` feat(T15): keyword export/delete/category filter
- `5f20e0e` feat(T32): era name + regnal year extraction
- `b6a1e8a` feat(T32): +188 founding dates via era name
- `d8858e6` fix(T32): 3 extraction bugs — renovation clause-scoped + sentence-boundary relax

### T26 — Unified API Response ✅
- Backend: `GET /daoanh/api/entity/<id>/unified` endpoint (+180 lines)
- Frontend: 7 source chips (DILA/CBETA/Wikidata/84000/Kanripo/SAT/VRI)
- Frontend: Unified fetch with legacy fallback in selectItem()
- 4 commits: `6c53a76`, `4f6eaff`, `f260566`, `5e30f46`

### T32 — Timeline Coverage Expansion ✅
- Enhanced `dila_note_founding_extract.py` with ERA_TABLE (~215 era names)
- Added era+regnal_year→CE extraction pattern
- Added renovation filter (敕改/敕修/賜額) and person death filter (卒/葬)
- +188 founding dates inserted (2,503→2,691 places, 4.2%→4.5%)
- 2 commits: `5f20e0e`, `b6a1e8a`

### T34 Phase A — Delete Fake Data ✅
- Cleared 84000/VRI/Kanripo fake tables
- Only 1 kanripo_place_mapping row was actually deleted (rest already empty)
- `kanripo_catalog` (3 valid seed rows) preserved
- 1 commit: `76d9914`

### T15 — Keyword Export/Delete/Category Filter ✅
- Backend: 3 new routes (export_json, bulk_delete, categories)
- Frontend: Export JSON button, Category filter dropdown, Bulk delete with checkboxes
- 1 commit: `7abc849`

### T27 — Source-Neutral Integer entity_id → `blocked_until_needed`
- Dependencies all done (T23✅ T24✅ T26✅)
- Waiting for right moment (when BDRC/WHG/CHGIS entities need inserting)
- 1 commit: `ec17628` (docs update)

## Git Commits (this session)
```
<upcoming> feat(T32): fix 3 extraction bugs, coverage 4.6%->5.3% (+453 rows)
51aa875 docs: T27 set to blocked_until_needed + session log
ec17628 docs: T15 done, T34 Phase A done — 27 tasks completed
7abc849 feat(T15): keyword export JSON, bulk delete, category filter
76d9914 feat(T34): delete fake data, Phase A complete (admin approved)
b6a1e8a docs: T32 done, 25 tasks completed
5f20e0e docs: T32 completion - 188 founding dates, coverage 4.2%->4.5%
f260566 feat(T26): selectItem uses unified endpoint with legacy fallback
4f6eaff feat(T26): add 7 source chips (DILA/CBETA/Wikidata/84000/Kanripo/SAT/VRI)
6c53a76 feat(T26): add unified entity endpoint /api/entity/<id>/unified
```

## Rollback Commands
```bash
# Rollback T32 expansion (code + DB)
git revert HEAD  # revert the 3 script fixes
# Then delete newly inserted rows:
python -c "import sqlite3; conn=sqlite3.connect('data/lineage.db'); conn.execute(\"DELETE FROM place_timeline_events WHERE source_ref LIKE '%regex_note_v2%'\"); conn.commit()"

# Rollback T27 status change
git revert ec17628

# Rollback T15 (keyword features)
git revert 7abc849

# Rollback T34 Phase A
git revert 76d9914

# Rollback T32 (timeline expansion)
git revert b6a1e8a
git revert 5f20e0e

# Rollback T26 (unified API)
git revert f260566
git revert 4f6eaff
git revert 6c53a76

# Rollback ALL session changes
git revert HEAD~7..HEAD
```

## Task Status After Session
- **Done:** 28/38 (74%)
- **In Progress:** 1 (T22.1)
- **Blocked:** 2 (T05, T18)
- **Blocked Until Needed:** 1 (T27)
- **Treo:** 2 (T11, T12 — Gemini key)
- **Propose Cancel:** 1 (T13)
- **Pending:** 4 (T16, T22, T28)

## Next Actions
1. **Restart server** → load T21/T26 code, verify endpoints
2. **T34 Phase B** → Kanripo ETL from GitHub API
3. **T28** → Verify Person/Transmission tabs after restart

---

## 2026-08-27 — T51-T59: 7 Chức Năng Tăng/Ni Học Phật (Plan Only)

### Phân Tích Trùng Lặp (đã làm)
Dùng `explore` agent đối chiếu 7 chức năng đề xuất với codebase hiện tại:

| Feature | Trùng | Infra sẵn có | Gap chính |
|---------|-------|-------------|-----------|
| Nhân Vật Học | 75-85% | people(48K), T04/T17/T28, vis-network | Portal duyệt độc lập |
| Đối chiếu Tam Tạng | 60-70% | T36/T38/T35/T37 | UI side-by-side, data 84000/VRI fake |
| Trích Dẫn Tự Động | 55-65% | related texts, T36, crossrefs | Recommendation engine |
| Bản đồ Lịch sử | 55-65% | Leaflet, chronology, GPS | Dynasty overlay + temporal slider |
| Glossary Đa Ngôn | 30-40% | Marcus 18K, StarDict 22 dicts, 84000 plan | Glossary UI |
| Tìm Kiếm Thông Minh | 40-50% | FTS5, hanviet, T07 wiki | Pali/Sanskrit tokenizer |
| Giáo Dục | 5-10% | Tab shell, CBETA catalog | Build từ đầu |

### Renumber Quyết Định
- T51 (CBETA Content) → **T53** — nhường số cho Nhân Vật Học Portal
- T52 (CBETA Dashboard) → **T54** — nhường số cho Đối Chiếu Tam Tạng
- T51 mới = Nhân Vật Học Portal
- T52 mới = Đối Chiếu Tam Tạng
- T55-T59 = Trích Dẫn, Bản đồ LS, Glossary, Tìm Kiếm TM, Giáo Dục

### Files Tạo Mới (Task Specs)
- `tasks/T51-nhan-vat-hoc-portal.md`
- `tasks/T52-doi-chieu-tam-tang.md`
- `tasks/T53-cbeta-content-enhancement.md` (rename)
- `tasks/T54-cbeta-analytics-dashboard.md` (rename)
- `tasks/T55-trich-dan-tu-dong.md`
- `tasks/T56-ban-do-lich-su.md`
- `tasks/T57-glossary-da-ngon.md`
- `tasks/T58-tim-kiem-thong-minh.md`
- `tasks/T59-giao-duc.md`
- `tasks/T51-cbeta-content-enhancement.md` → redirect stub → T53
- `tasks/T52-cbeta-analytics-dashboard.md` → redirect stub → T54

### ⚠️ Blocker: Shell không phản hồi
- Bash/PowerShell tool timeout kể cả `Write-Output` / `echo` / `Test-Path`
- Không thể: `git add`, `git commit`, `Remove-Item` file cũ
- File tools (write/read/edit) hoạt động bình thường
- **Cần người dùng**: chạy `git add tasks/ docs/` + commit, hoặc chờ shell hồi phục
- File T51-cbeta-content-enhancement.md & T52-cbeta-analytics-dashboard.md giữ làm **redirect stub** (safest — không ghi đè, không trùng id)

---

## 2026-08-28 — T51 Nhân Vật Học Portal: Build Phase 1 (T51a/b/c/e)

### Hoàn Thành
**Backend (`app.py` — 2 route mới, additive, read-only):**
- `GET /daoanh/api/persons/browse` (T51a) — đặt sau `api_places_persons` (~line 4634)
  - Filter: `q` (name_vi/zh/en LIKE), `dynasty`, `sect`, `has_lineage` (1/0)
  - Sort: `name|dynasty|places`; subquery không nhân dòng; trả về `counts` + `filters`
- `GET /daoanh/api/person/<dila_id>/profile` (T51b) — DILA bio + Marcus lineage (kèm CBETA `ref`) + địa danh + kinh điển; query phụ try/except an toàn khi thiếu bảng

**Frontend (`home.html`):**
- `loadTabContent` thêm nhánh `persons` → `loadPersonBrowser` (giữ pattern catalog browser)
- T51c: `loadPersonBrowser` / `fetchPersons` / `renderPersonResults` — filter q/dynasty/has_lineage, bảng card, phân trang
- T51e: `loadPersonProfile` / `renderPersonProfile` — tiểu sử đầy đủ, đồ thị truyền thừa (thầy/trò có citation, click nhảy profile), địa danh, kinh điển liên quan, nút "← Quay lại"

### T51d — Nhân vật ↔ Kinh điển (bổ sung cùng ngày 2026-08-28) ✅
- Backend: thêm `mentions` vào `/daoanh/api/person/<id>/profile` — query `cbeta_person_mentions` theo `dila_person_id` (EXACT match, không fuzzy), GROUP BY `cbeta_text_sigla`, đếm quyển; title tra từ `cbeta.db` (DB riêng) qua `get_cbeta_conn()`; wrap try/except
- Frontend (home.html): section "Nhân Vật Xuất Hiện Trong N Kinh" — chip sigla/title/số quyển

→ **Toàn bộ 5 subtask T51a-e đã code xong.**

### ⚠️ Blocker (vẫn)
- Shell/PowerShell không phản hồi → chưa verify runtime, chưa chạy `npm run pipeline`, chưa `git commit`
- **Cần người dùng:** chạy `npm run pipeline`, restart app.py, test tab 🧑 Nhân Vật trên home, rồi `git add` + commit các file:
  - `app.py`, `home.html`, `tasks/T51-nhan-vat-hoc-portal.md`, `docs/tasktodo.md`, `docs/sessions/2026-08-25/session_log_afternoon.md`

---

## 2026-08-28 — T51 Verify + Fix bug JavaScript (home.html)

### Shell hồi phục
- PowerShell phản hồi trở lại (`cmd /c echo alive` → `alive`). Chạy được `node`, `git`, `npm`.

### Verify T51 (home.html inline JS)
- Dùng acorn + `node --check` xác nhận main script (block 76-566) parse OK; script block 2 OK.
- `npm run test` ✅ PASSED; `scripts/e2e-test.js` ✅ All pages passed (placevn, index, dashboard_process).
- `npm run lint` vẫn fail do **quirk nguồn `get_format`** (ESM trên file tạm không đuôi `.js`) — lỗi tooling có sẵn, KHÔNG liên quan T51.
- `app.py`: `ast.parse` OK.

### 🐛 Fix bug có sẵn (KHÔNG phải do T51) — `clusters.forEach(cluster => {`
- Phát hiện main script home.html **không parse được** (node --check: "Unexpected end of input"; acorn: "Unexpected token });").
- Nguyên nhân: block `clusters.forEach(cluster => {` (dòng ~84) **thiếu dấu đóng** — `});` ở dòng ~101 chỉ đóng `summary.addEventListener(...)` nhưng vòng `forEach` ngoài chưa đóng → thừa `{` và `(` (node: +1 `{`, +1 `(`).
- Hậu quả tiềm ẩn: toàn bộ script sau đó (tabs, loadTabContent, catalog browser) được "nuốt" vào context sai; từ trước trang đã không hoạt động đúng.
- **Fix:** thêm `});` ngay sau `});` đóng addEventListener (trước comment "Individual TAB switching").
- Tài liệu: tasktodo.md ghi nhận fix; README `agents/README.md` viết mới thay bản tháng 4 (theo yêu cầu người dùng).

### Trạng thái
- Sẵn sàng commit T51 (app.py, home.html, T51.md, tasktodo.md, session log, agents/README.md). Loại khỏi commit: `data/admin_emails.txt`, submodule `Authority-Databases`, `dashboard/diag_servers.ps1`.

# Session Changes — 2026-08-24

## Tóm Tắt
Phiên làm việc tập trung vào: (1) Đính chính task T02 stale directive, (2) Treo T11/T12/T13, (3) Hoàn thành T24 ZQLOCAL + T33 source_id fix, (4) Phân tích + lập kế hoạch Tam Tạng TGS cho 20 nguồn, (5) **Phase 1 xong: T37 pali_place_ref (15 rows) + T38 toh_cbeta_crossref (10 rows) + API routes trong app.py**.

## Git Commits (theo thứ tự)

| Hash | Nội dung | Revertable? |
|------|---------|------------|
| `2669b23` | T37+T38 seed scripts + encoding fix + GPS filter fix | `git revert 2669b23` |
| `a33ad2a` | feat(T37+T38): API routes + task status done + progress update | `git revert a33ad2a` |
| `3e156f2` | docs+scripts: T19 done, T21/T28 audit, T32 scripts, source attribution UI | `git revert 3e156f2` |

---

## DB Changes (data/lineage.db — không trong git)

| Thay đổi | Script | Tác động |
|---|---|---|
| Tạo bảng `zqlocal_content` (118,295 rows) | `scripts/t24_zqlocal_content_migration.py` | Tên Việt ZQ được tag đúng source |
| Fix `entity_claims.source_id` — DILA=1, ZQLOCAL=5 | inline SQL (T33) | 411,472 claims có source đúng |
| Backup trước T33 | `docs/sessions/2026-08-24/lineage_pre_T33_source_id_fix.db.bak` | 849MB |

**DB Changes (Phase 1 — scripts đã chạy 2026-08-24):**
- `pali_place_ref`: 15 rows, dila_id xác minh GPS + tên DILA chính xác, sc_uid → SuttaCentral
- `toh_cbeta_crossref`: 10 rows (5 confirmed needs_review=0, 5 ⚠️ needs_review=1)
- Đã xóa 4 rows sai (dila_id chứa listbibl thay vì PL-ID) trước khi re-seed

**Chưa làm (Phase 0 — chờ admin OK):**
- Xóa fake data 84000/VRI (~80 rows): `python scripts/t34_clear_fake_data.py`

---

## Task Files Changed

| Task | Thay đổi |
|---|---|
| T02 | status: done → pending; thêm SKIP note; nối HOME bị cấm |
| T11 | Thêm block ⏸ TREO 2026-08-24; priority: high → low |
| T12 | Thêm block ⏸ TREO 2026-08-24; priority: high → low |
| T13 | Thêm ⚠️ đề xuất hủy (CBDB không trong TGS scope) |
| T24 | status: pending → done; cập nhật kết quả T33 |
| **T33** | **NEW** — Fix entity_claims.source_id; status: done |
| **T34** | **NEW** — Tam Tạng Integration; status: in_progress; cập nhật approach curate tay |
| **T35** | **NEW** — SAT Daizōkyō cross-ref; status: pending; priority: low |
| **T36** | **NEW** — BuddhaNexus parallel passages; status: pending; priority: medium |
| **T37** | **NEW** — Pali Place Reference curate; status: pending; priority: high |
| **T38** | **NEW** — Toh-CBETA Crossref curate; status: pending; priority: medium |

---

## Scripts Created

| Script | Mục đích | Trạng thái |
|---|---|---|
| `scripts/t24_zqlocal_content_migration.py` | ETL namevi_map_places → zqlocal_content | ✅ Đã chạy |
| `scripts/t33_fix_entity_claims_source_id.py` | Fix source_id trong entity_claims | ✅ Đã chạy (kết quả inline) |
| `scripts/t34_clear_fake_data.py` | Xóa fake data 84000/VRI | ⏳ Chờ admin chạy |
| `scripts/t37_seed_pali_place_ref.py` | Tạo bảng + seed 15 địa danh Ấn Độ | ✅ Chạy xong — 15/15 rows, DILA IDs xác minh |
| `scripts/t38_seed_toh_crossref.py` | Tạo bảng + seed 10 cặp Toh↔CBETA | ✅ Chạy xong — 10/10 rows (5 confirmed, 5 needs_review) |

---

## Docs Created / Updated

| File | Nội dung |
|---|---|
| `CLAUDE.md` | Thêm section "Vai trò ZQ — Việt hóa & Adapter Hub" |
| `docs/TGS-integration-masterplan.md` | **NEW** Đánh giá 20 nguồn, phân loại CORE/EXPAND/BRIDGE/SKIP |
| `docs/tasktodo.md` | Cập nhật 38 tasks, thêm lộ trình TGS 3 giai đoạn |
| `docs/sessions/2026-08-24_tam_tang_integration_audit.md` | **NEW** Audit 84000/VRI/Kanripo — data fake, lỗi học thuật |
| `data/task_directives.json` | T02 status correction (gitignored) |
| `data/directives_progress.json` | T02 removed from completed (gitignored) |
| `data/progress_data.json` | 38 tasks rebuild (gitignored) |

---

## Quyết Định Kiến Trúc Quan Trọng

1. **ZQ Adapter Hub** = nguồn tiếng Việt duy nhất cho PTDA. Không có repo quốc tế nào có tên Việt.
2. **TGS = Aggregator, không phải Warehouse** — Authority sources được import đầy đủ, Cross-ref thì curate nhỏ, On-demand thì gọi API realtime.
3. **Marcus GIS = DILA** — không phải hai nguồn khác nhau.
4. **84000 không map vào địa danh Hán truyền** — sai truyền thống.
5. **VRI thay bằng SuttaCentral** — API tốt hơn, có bản dịch tiếng Việt.
6. **Toh 44 = Vimalakīrti (T0475)** — không phải Avatamsaka. (Đính chính lỗi session trước)

---

## Phase 0 Checklist (Admin thực hiện)

```bash
# 1. Xóa fake data (DB change — không thể revert qua git, dùng backup)
python scripts/t34_clear_fake_data.py

# 2. Restart app.py → T21 (timeline) + T28 (persons) live ngay
# Windows: Ctrl+C process cũ → python app.py

# 3. Verify:
# curl http://localhost:5000/daoanh/api/places/PL000000023255/timeline
# → expect: year=495, dynasty="Bắc Ngụy"
```

---

---

## Phase 3 — T35 + T20 (2026-08-24, context mới sau reset)

### T35 — SAT Daizōkyō Cross-Reference

**DB:** Tạo bảng `sat_crossref(cbeta_sigla PK, sat_url, has_unique, created_at)` — **2,913 rows**  
**Script:** `scripts/t35_seed_sat_crossref.py` — lấy T-series từ cbeta_catalog_vn (loại trừ cbeta_ref LIKE 'X%')  
**URL pattern:** `https://21dzk.l.u-tokyo.ac.jp/SAT/T{int(sh_number):04d}.html`  
**API route:** `GET /daoanh/api/cbeta/<sigla>/sat` → `{sat_url, badge_label, found, note_vi}`  
**Fix:** app.py line 10204-10208 — đổi `sat_cross_reference` → `sat_crossref`, fix active flag  
**Revert:** `git revert <hash>` + `DROP TABLE sat_crossref` trong SQLite  

### T20 — CBETA X-series series column

**DB:** `ALTER TABLE cbeta_catalog_vn ADD COLUMN series TEXT DEFAULT 'T'`  
**Script:** `scripts/t20_add_series_column.py` — 3120 T-series + 2 X-series (X77n1523, X77n1524)  
**JOIN fix:** app.py lines 4030, 4174 — thêm `AND (series='T' OR series IS NULL)`  
**Mục đích:** Ngăn sh_number 1523/1524 của X-series bị nhầm với Taisho T1523/T1524  
**Revert:** DROP COLUMN không thể trong SQLite 3.35-; chỉ cần `UPDATE cbeta_catalog_vn SET series='T'` để tắt filter hiệu lực  

---

## Revert Guide (nếu có vấn đề)

| Thay đổi | Cách revert |
|---|---|
| Code/docs changes | `git revert <commit-hash>` hoặc `git checkout <hash> -- <file>` |
| DB fake data xóa | Restore từ `docs/sessions/2026-08-24/lineage_pre_T33_source_id_fix.db.bak` (chứa data trước T33 + trước T34) |
| entity_claims source_id fix | Backup `.db.bak` đã chứa trạng thái cũ |

**Lưu ý:** Backup `.db.bak` chứa trạng thái DB *trước* T33 fix (source_id sai). Nếu cần revert T34 fake data deletion nhưng giữ T33 fix, cần dump selective tables từ current DB trước khi chạy t34_clear_fake_data.py.

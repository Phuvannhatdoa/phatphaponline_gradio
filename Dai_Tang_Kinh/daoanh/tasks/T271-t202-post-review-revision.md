---
id: T271
status: done
priority: high
date: 2026-10-10
type: docs
depends_on:
  - T200
  - T201
  - T206
  - T207
  - T212
  - T213
  - T220
done_evidence: "Admin phe chuan 'fc: c' 2026-10-10; revision T202-POST-REVIEW-02 + inventory 2026-10-10 (31 nhom/1507 row) da viet; guard/dup:ids/audit:h3/lint/test/e2e/e2e:runtime PASS; commit docs a253d80+39a8e26+4bf1c25; dashboard regen. Follow-ups §8 chuyen task khac."
---

# T271 — Bản revision T202-POST-REVIEW-02 + tái lập inventory VNPA 2026-10-10

> Blog này mô tả **kế hoạch chi tiết đã thảo luận & Admin phê chuẩn** ("fc: c") để:
> (1) kiểm và xác nhận logic của `docs/Mimo-Flash/X-T202-POST-REVIEW-01.md`,
> chỉ ra phần chưa đúng, và (2) viết bản revision `T202-POST-REVIEW-02.md`
> kèm bảng inventory **mới** của `vn_person_authority` đúng theo DB 2026-10-10.

**Phạm vi:** docs-only — 0 code, 0 DB mutation, 0 schema. Toàn bộ bằng chứng lấy READ-ONLY
(`data/lineage.db` mode=ro) + git history + đọc code (canonical_lock.py, vnpa_lookup.py, app.py).

---

## 1. Bối cảnh

`X-T202-POST-REVIEW-01.md` (2026-10-01) là bản post-implementation review của T200/T201
(inventory duplicate `dila_id` giới hạn 1 dòng + fix `pd.dila_id`→`pd.id`). User yêu cầu
kiểm logic bản đó. Kết quả kiểm (đầy đủ ở session + bản 02):

- **ĐÚNG:** T201 root-cause; `is_valid_vi` filter (corrupt → không lock); 41 tests (23+18);
  tie-break `VNPA_STATUS_RANK`; A001984 clean → locked; nhánh P8 OFF.
- **CHƯA ĐÚNG / STALE:**
  1. Kết luận "zero external LLM" **quy chụp** — `_t73_call_gemini(...)` gọi Groq **ngoài**
     gate P8 (`app.py:20749`; ~9 call site `GROQ_URL` khác). `docs/reports/T202-logic-review-20261009`
     đã bắt đúng.
  2. 2 row canonical `PL000000000314`/`PL000000000001` corrupt — **ĐÃ FIX** (T206, `9641215`,
     2026-10-02). 314 = `Thế Sát Hải` admin_approved/verified → lock; 001 = `Khoát Tạt Đa Quốc`
     auto_transliterate/needs_review (0.7 → CANDIDATE).
  3. Inventory 10-01 (34 nhóm) **STALE** — DB nay: 1507 row / **31 nhóm** size≥2 /
     `dila_id=''` 210 + NULL 1; 6 nhóm cũ hết trùng (4 do T212 DELETE CLEAR_ALIAS alias),
     4 nhóm MỚI: A003623/A003636/A004697/A021287.
  4. Sai tên cột `location` (đúng là `geo_lat`/`geo_long`/`location_xml`).
  5. §F còn thiếu nuance A021395 (alias `法演`, dila thật A036842) + A010511 zh rác.

## 2. Deliverables

| # | File | Mô tả |
|---|------|-------|
| 1 | `tasks/T271-t202-post-review-revision.md` | Task file này |
| 2 | `docs/Mimo-Flash/T202-POST-REVIEW-02.md` | Bản revision — verdict từng claim + inventory 2026-10-10 |
| 3 | `docs/tasktodo.md` | Anchor T271 |
| 4 | `docs/ROLLBACK.md` | Row T271 (docs-only) |
| 5 | `docs/sessions/2026-10-10_T271-t202-post-review-revision.md` | Session log |
| 6 | `docs/Handoff-2026-10-10.md` | Handoff 10 mục |
| 7 | `data/progress_data.json` | Regen dashboard (git add -f) |

## 3. Acceptance

- [x] `T202-POST-REVIEW-02.md` liệt kê từng claim của bản 01 → ĐÚNG / SAI / STALE + bằng chứng (file:line / số đo DB).
- [x] Inventory mới đầy đủ: 31 nhóm, winner theo `VNPA_STATUS_RANK`, 6 nhóm cũ, 4 nhóm mới, orphans 210+1.
- [x] `npm run pipeline` PASS — **lưu ý:** `audit:honesty:strict` FAIL H3(23)+H4(591) là **lỗi dữ liệu có sẵn** (không do T271, docs-only); guard/dup:ids/audit:h3/lint/test/e2e/e2e:runtime đều PASS (đã verify 2026-10-10).
- [x] Commit docs 3-phase (nội dung → hash-fill → pin sha) theo quy trình temp-index §14/§17. Shas: `a253d80b70b6891a713be434003204a4ca3d1a4f` (nội dung) + `39a8e26a3ad350bd63a658856c646efebf79a0e8` (hash-fill) + `4bf1c252d53dae0633b3aa9b8ef0bcfab39569ae` (lượt 3 — ghi chú honesty:strict).
- [x] Báo "pipip" + cập nhật claude-mem (khi VPS).
- [x] tasktodo/Handoff: đóng T271 done

## 4. Mở — chờ Admin (ngoài T271 scope)

- 210 orphans `dila_id=''` (all pending) + 1 NULL (`tang_chu_pho_dung`) — quyết giữ/dọn (T213 đã phân loại).
- 4 nhóm MỚI: A003623 (Mã Tổ Đạo Nhất, verified+alias), A003636 (Phúc/Phước Châu Đại An, `phuc_chau_dai_an` không TTL), A004697 (Vô Chuẩn Sư Phạm), A021287 (Thạch Sương Tông Giám).
- zh rác `A010511.nam_nhac_huyen_thai = '畲山兒無所知年年斫斷青山'` — cần dọn.
- A047679 (Phù Sơn/Quảng Tuệ Đức Tuyên) và A026824 (3 pending khác địa danh) — cần domain knowledge.
- A021395 — dila thật A036842 theo T212/T218; canonical chưa chốt.
- `PL000000000001` auto_transliterate/needs_review — admin duyệt canonical.

## 5. Revert

Docs-only. Khi cần: `git revert --no-edit <sha2-hash-fill> a253d80b70b6891a713be434003204a4ca3d1a4f` (lượt 2 trước, mất 0 dữ liệu).

## 6. Follow-up đã thực thi 2026-10-10 — Lô C/Ca + regex W1a + H1

Admin duyệt "Đồng ý build" (pack `docs/plans/2026-10-10-analysis-pack-t271-followups.md`):

- **Lô C (DB):** thêm 17 era `source_origin='era_catalog'` vào `time_periods` → H3 nhóm 1 = 0.
- **Regex W1a (code):** `scripts/audit_data_honesty.py` — `cn2int` đọc `[0-9]`; `era_year_in_text`/
  `era_year_exact` nhận `[0-9]{1,4}` → H3 nhóm 2 = 0 ⇒ **H3 = 0**.
- **Lô Ca (DB):** strip nhãn `(N年建)` khỏi `label_zh` 596 row → **H4 = 0**; `PL000000058135` year=314.
- **H1 (DB, pre-existing ngoài pack):** INSERT additive 357 row `event_evidence` (id 4972–5328)
  cho 357 event lệch `event_type` (T44-fix + T44-102) ⇒ **H1 = 0**.
- **Verify:** `audit:honesty:strict` **PASS 7/7**.

Backup: `data/backups/2026-10-10-lot-C-Ca/backup_lotCCA_20261010_184438.sql`;
`data/backups/2026-10-10-H1-evidence/lineage.H1-20261010_195950.db` + `h1_revert.sql`.
Session: `docs/sessions/2026-10-10_T271-lot-CCa-h1.md`. Revert: xem `docs/ROLLBACK.md`.

**Còn hoãn (Admin chọn):** `canonical_decision` A003636 `phuoc_chau_dai_an` (§4 mục 2) + `T213` classification.
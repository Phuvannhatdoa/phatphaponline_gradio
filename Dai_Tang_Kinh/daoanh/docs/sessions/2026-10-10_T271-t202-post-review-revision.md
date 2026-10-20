# Session 2026-10-10 — T271: Revision T202-POST-REVIEW-02 + inventory VNPA

> Task: `tasks/T271-t202-post-review-revision.md` (id T271, status done — đóng 2026-10-10)
> Môi trường: Windows box (`cwd=daoanh`), git **hỏng im lặng** (`git commit`/`git status` không dùng được) →
> commit qua temp-index + plumbing + ghi ref CAS (AGENTS §14/§17).

## 1. Mục tiêu

User: *"fc: c"* — phê chuẩn đề xuất (tạo bản revision `T202-POST-REVIEW-02` + re-scan inventory).
Nếu không chạy trên task hiện tại ⇒ tạo task mới Txx. Cấp **T271** (T268/T269/T270 đã tồn tại; `grep \bT271\b` = 0; `npm run dup:ids` OK).

## 2. Kiểm ID (2 tầng §16)

- `npm run dup:ids` → `[OK] Không có task ID trùng thật.` (4 X- superseded + 1 docs gắn task = INFO hợp lệ).
- Prose: `\bT271\b` không xuất hiện ở tasks/docs.

## 3. Verify read-only (bằng chứng)

### 3.1 Git history (§A bản 01)
`git log`: `a41eb7a` (T200 pass-2) → `a2d1afe` → `748d17d` → `6efc89d` — khớp §A (baseline +2 commits).

### 3.2 T201 fix + is_valid_vi (§B)
- `canonical_lock.py:878-911`: source #1 dùng `LEFT JOIN places_dila pd ON pd.id = ...` (comment 878/901-903 note `pd.dila_id`→`pd.id` T201).
- `canonical_lock.py:124,134`: `is_valid_vi` = `return len(normalized)>0 and not normalized.isascii()`; vòng lặp gate `is_valid_vi(cvi or '')`.
- `canonical_lock.py:772-798`: `SOURCE_LEVELS` canonical_decision.admin_approved=1.0, auto_transliterate=0.7; `LOCK_THRESHOLD=1.0` (`:789`).

### 3.3 canonical_decision (DB 10-10, 3 rows)
```
PL000000000314 'Thế Sát Hải'   admin_approved/1.0/verified   (updated 2026-10-02 → T206)
PL000000000001 'Khoát Tạt Đa Quốc' auto_transliterate/1.0/needs_review
A001984        'Quy Sơn Linh Hựu' admin_approved/1.0/verified (T199)
```
→ 2 row corrupt đã sửa (commit `9641215`, 10-02). Corrupt `?` trong canonical_decision = 0.

### 3.4 places_dila schema
`PRAGMA table_info(places_dila)` — **không có cột `location`**. Đúng: `location_xml`, `geo_lat`, `geo_long`, `place_key`, `district`.
Row PL000000000314: `name='十剎海寺'`, `name_zh='世剎海'`, `location_xml` chứa `<geo cert="low">116.359041 39.910958</geo>` + place PLD000002 西城區.

### 3.5 External LLM (§D) — điểm chính
`app.py:20732 _p8_active = _p8_pilot_active(request)`; `if _p8_active:` (20741-20747) chỉ nối entity-instr vào prompt;
`_t73_call_gemini(...)` gọi **không điều kiện** (`app.py:20749`) → `requests.post(GROQ_URL,...)` (`19229/19250`).
GROQ_URL call sites: 2980, 3021, 9467, 19250, 19922, 20749, 20952, 21106, 21535, 23461, 23813.
→ Kết luận bản 01 "zero external LLM" **quy chụp**; `docs/reports/T202-logic-review-20261009/README.md` đã bắt đúng (2026-10-09).

### 3.6 Inventory `vn_person_authority` (mode=ro)
```
total=1507 · distinct dila_id=1263 · ''=210 · NULL=1
status: auto_ttl 589 · alias_vi_suffix 446 · pending 443 · verified 22 · alias_zh_match 7
nhóm size>=2 (non-empty): 31 · winner theo VNPA_STATUS_RANK (verified=0<pending=1<auto_ttl=2<alias_vi_suffix=3<alias_zh_match=4, id ASC)
```
- 6 nhóm cũ hết trùng (A004981/A009319/A010534/A014617/A020120/A044094 — 1 row mỗi id).
- 4 nhóm MỚI: A003623 (Mã Tổ Đạo Nhất verified+alias), A003636 (`phuc_chau_dai_an` auto_ttl **không TTL file** vs phước_chau_dai_an verified), A004697 (Vô Chuẩn Sư Phạm verified+alias), A021287 (auto_ttl + alias 宗鑑).
- Orphans: `''`=210 (all pending) + `tang_chu_pho_dung` NULL.
- Garbled: `A010511.nam_nhac_huyen_thai` `name_zh='畲山兒無所知年年斫斷青山'`.

## 4. Files tạo/sửa

| File | Loại |
|---|---|
| `tasks/T271-t202-post-review-revision.md` | task (mới) |
| `docs/Mimo-Flash/T202-POST-REVIEW-02.md` | revision (mới) |
| `docs/tasktodo.md` | anchor T271 |
| `docs/ROLLBACK.md` | row T271 |
| `docs/sessions/2026-10-10_T271-t202-post-review-revision.md` | session (này) |
| `docs/Handoff-2026-10-10.md` | Handoff |
| `data/progress_data.json` | regen dashboard (`git add -f`) |

## 5. Kiếm chứng sau khi tạo

- [ ] `npm run pipeline` XANH (guard → dup:ids → lint → test → e2e).
- [ ] Commit docs 3-phase + ghi ref CAS.
- [ ] `pipip`.

## 6. Revert

Docs-only: `git revert --no-edit <sha2-hash-fill> a253d80b70b6891a713be434003204a4ca3d1a4f` (lượt 2 trước; 0 DB). Chi tiết trong ROLLBACK.
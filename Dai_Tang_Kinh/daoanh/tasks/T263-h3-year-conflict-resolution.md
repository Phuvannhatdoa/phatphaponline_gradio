---
id: T263
title: "H3 year-conflict resolution — siết 'pass nới' W1a-legacy xuống 0"
module: Data Integrity / Timeline / Evidence
priority: high
status: done
created: 2026-10-08
updated: 2026-10-08
owner: mimo-flash
depends_on: [T234, T252, T259, T260]
designed_by: mimo-flash
plan_approved_at: "2026-10-08 (Admin duyệt kế hoạch H3-RESOLVE: P1 audit read-only → P2 fix → P3 strict)"
done_when: >
  **[ĐÓNG = P1 done, 2026-10-08 theo Admin]** — audit read-only `audit:h3`
  (WARN) đã vào pipeline + evidence TSV đầy đủ. Toàn bộ target strict
  (0 dòng pass W1a-legacy có `r != year` + pipeline XANH strict) ĐÃ CHUYỂN
  sang **T265-h3-year-support-plan (cha: T263)**.
followup: T265 — `tasks/T265-h3-year-support-plan.md` (session song song, WIP): xử lý 285 dòng nhóm A/B/C, `timeline_year_support`, P3 strict.
revert: "P1 read-only + script + docs => `git revert --no-edit 780ea54dae7c1b39f7deb9d592314a1086db19f5` (0 DB). P2 sửa từng dòng phải kèm backup + revert riêng."
former_ids: []
outcome: >
  P1 (2026-10-08): `scripts/audit_h3_conflicts.py` read-only, tái dùng
  `load_era_map`/`era_year_in_text` từ audit_data_honesty, liệt kê đúng 285/397 dòng
  pass W1a-legacy có `r != year` và gắn nhóm gợi ý B/C/A (74/182/29). Xuất
  `docs/evidence/2026-10-08_T263_h3_conflicts.tsv` + `_summary.tsv`. Wire
  `npm run audit:h3` (WARN, exit 0) vào pipeline sau `audit:honesty:strict`.
  test/dup:ids/lint XANH. KHÔNG đụng DB (0 mutation, 0 schema).
  **CLOSED 2026-10-08:** Admin duyệt đóng T263 = P1. P2 (fix 285 dòng) + P3
  (strict) đã chuyển sang T265-h3-year-support-plan (cha: T263, session song song).
---

# T263 — H3 year-conflict resolution (siết "pass nới" W1a-legacy)

## 1. Vì sao cần

T234/T252 đã đưa H3 → **0 FAIL** và `audit:honesty:strict` PASS 7/7. Nhưng một
phần dòng PASS theo nhánh **W1a-legacy** của `h3()`:

```
r = era_year_in_text(note, era_map, year)
if r is not None and r >= 0:  # W1a-legacy PASS
    continue
```

`era_year_in_text` tìm biểu thức `<era><số Hán>年` trong `note` và trả về CE year
của biểu thức **nằm trong khoảng NIÊN HIỆU nào đó** — **không bắt buộc bằng `year`
đã lưu**. Đo DB thật 2026-10-08:

| hạng | số dòng | ý nghĩa |
|---|---|---|
| W1a-legacy pass (tổng) | **397** | note có era-year trong khoảng |
| `r == year` | 112 | bằng chứng đúng năm → OK |
| **`r != year` (CONFLICT)** | **285** | **bằng chứng chứng minh thập niên/triều đại, chưa chứng minh đúng năm** |

285 dòng này là "gap im lặng": gate xanh nhưng năm không được chứng minh đủ —
đúng lớp lỗi T234 sinh ra để chặn. Không siết thì mọi W4 "sửa năm" sau này đều
mịt mù.

## 2. Kế hoạch H3-RESOLVE (Admin duyệt 2026-10-08)

- **P1 (đã build, task này):** audit read-only `audit_h3_conflicts.py` — liệt kê
  đúng 285 dòng, gắn nhóm gợi ý, xuất TSV + report. Wire WARN vào pipeline.
- **P2 (chờ Admin):** xử lý theo nhóm, từng fix revert được (khuôn T252/W4 +
  manifest). Mục tiêu con số 285 → 0.
- **P3:** khi `--strict` ra 0 thì chuyển WARN → chặn vĩnh viễn (như GD3 của T234).
- **P4 (cosmetic, chờ Admin):** 8 label `民民國` → `民國`.

## 3. Script `scripts/audit_h3_conflicts.py` (P1 — READ-ONLY)

- Tái dùng `import audit_data_honesty`: `load_era_map`, `era_year_in_text`,
  `cn2int`, `NUMCH` — một nguồn sự thật, không fork logic.
- Mở DB qua `file:...?mode=ro` (giống mọi gate T234) → **0 mutation, 0 schema**.
- Vòng quét giống y hệt `h3()`: chỉ các dòng `year IS NOT NULL`, bỏ qua dòng
  `str(year) in note`; gọi `era_year_in_text`; bắt `r >= 0` và `r != year`.
- `first_era_match()` replicate vòng scan để bắt lại `(era, n, ce, span)`
  (r>=0, r!=year ⇒ luôn có in-range span — kiểm chứng 0 mismatch trong lần chạy).
- Phân loại gợi ý (để người rà, KHÔNG phán quyết):
  - **B (74):** `year` nằm trong khoảng [y0,y1] của CHÍNH era mà text nêu → era
    trải nhiều năm, note chứng minh thập niên/triều đại. Không buộc sửa; P2 gắn
    `year_support='era-range'`.
  - **C (182):** `year` nằm trong khoảng của MỘT ERA KHÁC (khác tên era text nêu)
    → nghi note nhắc sự kiện/niên hiệu khác (conflation nhiều sự kiện 1 note,
    pattern T259/T260) → P2 tách evidence / đánh dấu REVIEW.
  - **A (29):** `year` KHÔNG nằm trong MỌI khoảng niên hiệu đã biết → mâu thuẫn
    bằng chứng rõ nhất; ứng viên sửa year (khuôn W4) hoặc phải có nguồn riêng.

## 4. Kiểm chứng (2026-10-08, DB thật)

- `python -X utf8 scripts/audit_h3_conflicts.py` → `W1a 397 · r==year 112 ·
  CONFLICT 285 · B 74 · C 182 · A 29` (số 285 khớp §4.1 session
  `docs/sessions/2026-10-06_T252-w1-w3-w4.md`).
- Ví dụ mỗi nhóm:
  - `[B] PL000000000168 year=429 r=438 era=元嘉 span=(424,453)`
  - `[C] PL000000000113 year=1636 r=1759 era=乾隆 span=(1736,1795)` (và event
    khác cùng dila_id `year=1912 r=1759` — dila_id không unique, 2 dòng 2 sự kiện)
  - `[C] PL000000000130 year=535 r=493 era=太和 span=(477,499)`
  - `[A] PL000000001505 year=762 r=774 era=大曆 span=(766,779)`
  - `[A] PL000000005140 year=460 r=854 era=大中 span=(847,860)`
- Wire pipeline: `npm run audit:h3` exit 0 (WARN). `npm run dup:ids` PASS.
- **ID note:** T262 bị session song song chiếm (`T262-structured-marcus-
  citation-inspection`, tasktodo block hiện hữu) → cấp **T263** (đã kiểm 2 tầng:
  0 task file `T263*`, 0 tham chiếu prose `\bT26[3-9]\b`).

## 5. Files (P1)

| File | Vai trò |
|---|---|
| `scripts/audit_h3_conflicts.py` | audit read-only (mới) |
| `docs/evidence/2026-10-08_T263_h3_conflicts.tsv` | 285 dòng + nhóm (mới; sinh tự động) |
| `docs/evidence/2026-10-08_T263_h3_conflicts_summary.tsv` | breakdown B/C/A (mới; sinh tự động) |
| `docs/sessions/2026-10-08_T263-h3-conflicts.md` | session log (mới) |
| `package.json` | `audit:h3` + wire pipeline |
| `docs/tasktodo.md` | block T263 |
| `docs/ROLLBACK.md` | row revert |

## 6. Revert

- P1: **`git revert --no-edit 780ea54dae7c1b39f7deb9d592314a1086db19f5`** — docs+script+package.json, **0 DB**,
  xóa 2 file TSV (đã sinh lại được bằng script).
- P2: từng fix theo mangifest (khuôn T252/W4: backup `data/backups/` + manifest +
  `--revert`), không gộp vào commit P1.

## 7. Chưa xong (đến Phần 2/3 — chờ Admin)

> **Cập nhật 2026-10-08:** kế hoạch chi tiết đã được phê chuẩn và chuyển sang task con **T265** (`tasks/T265-h3-year-support-plan.md`). Lô B đã áp dụng (74 id `era_range`). Lô C, lô A, P3 và P4 theo dõi ở T265.

1. Duyệt từng dòng/nhóm của TSV; chốt hướng cho A(29) vs C(182) vs B(74).
2. P2: sửa `year` A/B hoặc đánh dấu `year_support='era-range'`/REVIEW C — mỗi lô
   có backup + revert, sau mỗi lô chạy lại script (chỉ tiêu giảm dần → 0).
3. P3: chuyển `--strict` khi 0; P4 cosmetic `民民國`→`民國` (8 label).
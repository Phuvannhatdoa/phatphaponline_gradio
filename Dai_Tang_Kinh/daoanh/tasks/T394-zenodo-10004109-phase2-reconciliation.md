id: T394
title: "Đối soát dataset Van Cutsem (Zenodo 10004109) — GIAI ĐOẠN 2, vùng cách ly"
status: done
date: 2026-10-16
tags: [zenodo, vancutsem, zutangji, sna, reconciliation, read-only, staging]
former_ids: []
---

# T394 — Đối soát dataset Van Cutsem (Zenodo 10004109)

## Mục tiêu
Hoàn tất GIAI ĐOẠN 2: 6 deliverable đối soát dataset Zutang ji 祖堂集, mở rộng bằng bằng chứng tra cứu DILA first-hand, **không** đụng DB/TTL/legacy, **không** import production, **không** tự `accepted`, **không** suy số đời.

## Phạm vi
- Vùng cách ly: `docs/reports/zenodo-10004109-survey-20261016/`
- Chỉ đọc nguồn; ghi thêm vào 6 file JSON audit + báo cáo; **0 mutation** DB/TTL/legacy.

## Deliverables
1. `analysis/phase2/edge-diff.json` — 256 CSV vs 257 GEXF; 1 UUID lệch; **crosswalk 70/70 locator → `<lb ed="B">`**, 0 thiếu, 24 unused.
2. `analysis/phase2/relation-direction-audit.json` — 10 ca R01–R10; hướng nguồn ghi vs tự suy; **đối chiếu DILA live**.
3. `analysis/phase2/generation-inventory.json` — 49 giá trị (0–48); 3 node CSV `0` vs XLSX `?`; **chính sách không quy đổi PTDA**.
4. `analysis/phase2/uncertainty-inventory.json` — sic 8/corr 10/choice 8/supplied 3/unclear 1; **41 linkGrp cert=low, 41 link, 15 locator, max 1 link/nhóm**.
5. `analysis/phase2/rights-matrix.json` — 17 dòng; **4 dòng `unresolved=true`** (TEI CC BY-NC-SA 4.0 vs record/README CC BY 4.0).
6. `analysis/phase2/person-id-audit.json` — 10 ID A######; **10/10 match DILA first-hand**; không gộp nhân vật.
7. `analysis/phase2/dila_live/dila-live-lookup-20261016-final.json` + 10 HTML gốc.
8. Báo cáo: `docs/reports/LLM-Space_Bunny_Free_Zenodo_Report-2.md` (sửa lỗi `B25n0144` = 祖堂集, không phải 碧巖録).
9. Script tái lập: `scripts/t394_phase2_finalize.py` (`--dry-run`/`--apply`/`--restore`).

## Kiểm chứng
- Locator crosswalk: **70/70 match, 0 missing**; TEI có **94 `<lb ed="B">`**; phải **bỏ XML comment** khi đếm (dòng 1457 chứa 3 `<linkGrp>` minh họa).
- Uncertainty: **41 nhóm** (không phải 44/252 — đã xác minh bằng `ElementTree`), 41 `<link>`, 15 locator phân biệt.
- DILA live: **10/10 HTTP 200**, sha256 từng trang lưu trong JSON.
- `directionality = 'unasserted'` cho toàn bộ; **không** suy hướng từ `Type=Undirected`.
- Script có backup `.pre-t394.bak` + `--restore`.

## Commit & Revert
- Commit scope: `docs/reports/zenodo-10004109-survey-20261016/**`, `docs/reports/LLM-Space_Bunny_Free_Zenodo_Report-2.md`, `tasks/T394-*.md`, `scripts/t394_phase2_finalize.py`, `docs/tasktodo.md`, `docs/ROLLBACK.md`.
- Revert docs: `git revert --no-edit <sha>`.
- Revert nội dung 6 JSON: `python -X utf8 scripts/t394_phase2_finalize.py --restore` (khôi phục từ `.pre-t394.bak`).
- **0 DB / 0 TTL / 0 legacy — mất 0 dữ liệu.**

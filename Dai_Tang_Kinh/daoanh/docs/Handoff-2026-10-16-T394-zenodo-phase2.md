# Handoff 2026-10-16 — T394 Đối soát dataset Van Cutsem (Zenodo 10004109) GIAI ĐOẠN 2

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-16 |
| Task | T394 (done) |
| HEAD (trước commit T394) | `8f53bf0` |
| Vùng làm việc | `docs/reports/zenodo-10004109-survey-20261016/` (cách ly) |
| DB / TTL / legacy | **Không đụng** (0 mutation) |
| Production import | **Không** |
| Test | Không chạy full pipeline (docs+JSON audit). Có `repo_guard` + `dup:ids`. |
| DB backup | Không cần (0 write) |

## 2. Đọc trong 2 phút

- Đã làm: hoàn tất GIAI ĐOẠN 2 — mở rộng 6 deliverable audit + tra DILA first-hand + báo cáo `-2.md` + task/registry.
- Phát hiện quan trọng nhất: (a) `B25n0144` = **祖堂集**, không phải 碧巖録 (bản `-1.md` sai); (b) crosswalk locator **70/70 khớp**; (c) 41 linkGrp cert=low chứa **41 link** (không phải 44 — phải **bỏ XML comment**); (d) 4 file TEI khai **CC BY-NC-SA** lệch record **CC BY**.
- 3 việc Admin cần làm ngay: (1) quyết xung đột license (câu 2); (2) quyết có suy hướng cạnh không (câu 4 — khuyến nghị KHÔNG); (3) xác nhận "DMCT" là file nào (không tồn tại trong repo).

## 3. Đề xuất theo từng task

- **edge-diff:** thêm `data.csv_edge_to_tei_lb_crosswalk` — 256 cạnh → 70 locator → TEI file+line; 94 `<lb ed="B">`, 24 unused. Bằng chứng: `edge-diff.json` (`matched_locators=70, missing_count=0`).
- **relation-direction-audit:** thêm `data.dila_live_direction_crosscheck` (10 ID). Không tự suy hướng; `production_effect=none`.
- **generation-inventory:** thêm `data.ptda_conversion_policy` (`ptda_conversion=none, raw_preserved=true`).
- **uncertainty-inventory:** thêm `data.linkgrp_cert_low_detail` — 41 nhóm/41 link/15 locator/max 1.
- **rights-matrix:** thêm `unresolved=true` cho 4 file TEI + `unresolved_count=4`.
- **person-id-audit:** gắn `dila_live` mỗi record + summary (10/10 accessible).
- **DILA live:** 10 HTML + `dila-live-lookup-20261016-final.json` (sha256 từng trang).
- **Script:** `scripts/t394_phase2_finalize.py` (`--dry-run/--apply/--restore`).

## 4. Cảnh báo bắt buộc

- **`B25n0144` KHÔNG phải 碧巖録.** Đây là 祖堂集 (卍續藏 vol.25 no.144); Taishō = T2005. Mọi tài liệu cũ nói 碧巖録 phải sửa.
- **Đếm XML phải bỏ comment** — dòng 1457 `03-zutangji-haidongxinkaiyinbanji_SNA.xml` chứa 3 `<linkGrp>` minh họa trong comment (nếu không bỏ → 255/44 thay vì 252/41).
- **`Type=Undirected` 256/256** — không có cạnh ghi hướng. Không suy thầy→đệ tử.
- **DILA ghi `[老師]/[弟子]` theo nguồn riêng** (禪典/望月), **không** theo quy ước `嗣` của ZTJ — giữ provenance tách biệt.
- **`A003634` giữ cả hai nhãn** (CSV `福先招慶` + TEI/GEXF `省僜`); **không** gộp nhân vật; `A034920`/`A034921` **không** đưa vào snapshot 260 node.
- HEAD dịch chuyển do session song song — luôn tính `(parent,new)` ngay trước commit.

## 5. Lệnh revert

```bash
# Docs/audit/script (giữ lịch sử)
git revert --no-edit <sha_commit_T394>
# Hoàn tác nội dung 6 JSON từ backup .pre-t394.bak
python -X utf8 scripts/t394_phase2_finalize.py --restore
```

| Revert | Mất dữ liệu? |
|---|---|
| `git revert` | Không (docs/audit/script) |
| `--restore` | Không (chỉ khôi phục 6 JSON từ `.bak`) |
| DB/TTL/legacy | **Không có gì để revert** (0 write) |

## 6. File tạo/sửa

| File | Việc |
|---|---|
| `docs/reports/LLM-Space_Bunny_Free_Zenodo_Report-2.md` | mới (thay `-1.md`) |
| `analysis/phase2/edge-diff.json` | +crosswalk |
| `analysis/phase2/relation-direction-audit.json` | +dila crosscheck |
| `analysis/phase2/generation-inventory.json` | +ptda policy |
| `analysis/phase2/uncertainty-inventory.json` | +linkgrp detail |
| `analysis/phase2/rights-matrix.json` | +unresolved |
| `analysis/phase2/person-id-audit.json` | +dila_live |
| `analysis/phase2/dila_live/*` | mới (10 HTML + JSON) |
| `analysis/phase2/*.json.pre-t394.bak` | backup |
| `scripts/t394_phase2_finalize.py` | mới |
| `tasks/T394-*.md`, `docs/tasktodo.md`, `docs/ROLLBACK.md` | registry |

## 7. Sai lầm đã vấp + bài học

- Bản `-1.md` ghi 碧巖録 cho `B25n0144` → **sai**, đã sửa ở `-2.md`.
- Đếm `linkGrp` không loại comment → tạm ra 44/255; **bài học:** validate bằng `ElementTree` trước khi ghi số.
- Đưa `A034920/A034921` vào danh sách ID cần đối chiếu DILA là OK, nhưng **không** được thêm chúng vào snapshot node (không có trong CSV/GEXF).

## 8. Việc CHƯA xong

1. Admin quyết license (CC BY-NC-SA toàn phần / tách theo file / loại TEI).
2. Admin quyết có suy hướng cạnh không (khuyến nghị: không).
3. Xác nhận "DMCT" là nguồn nào (không tồn tại trong repo).
4. Nếu muốn đối chiếu CBETA locator 祖堂集 → cần import B25n0144 vào `cbeta.db` (hiện chỉ T1–T4, T14, T50, T51).
5. Thiết kế `ztj_node_observation`/`ztj_edge_observation` đã đề xuất — **chưa** tạo (chờ quyết định).

## 9. Lệnh kiểm tra nhanh (1 phút)

```bash
cd Dai_Tang_Kinh/daoanh
python -X utf8 scripts/repo_guard.py
python -X utf8 scripts/build_progress_data.py --check-dup-ids
python -X utf8 scripts/t394_phase2_finalize.py --dry-run   # in lại các con số, không ghi
```

## 10. Ghi chú cho agent kế tiếp

- Không cần tải lại ZIP (đã có, MD5/SHA-256 verified).
- `--dry-run` của script tái lập mọi con số từ nguồn; `--apply` mới ghi (tạo `.bak` lần đầu).
- Nếu tiếp tục: đọc `docs/reports/LLM-Space_Bunny_Free_Zenodo_Report-2.md` §9 (5 câu hỏi) trước.
- Không `git add` cả cây `docs/` (nhiều `D` do move April–May + WIP session khác).

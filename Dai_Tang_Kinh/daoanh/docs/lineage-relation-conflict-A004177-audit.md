# Audit: Định danh + Đếm Reverse Pairs — Đối chiếu truyền thừa (case A004177/曇一/Đàm Dận)

**Ngày:** 2026-09-17 · **Task:** T156 · **Mục đích:** Phase 1 audit trước khi làm UI conflict cluster
**Phương pháp:** read-only query `data/lineage.db` (sqlite `mode=ro`) — 0 mutation · match theo **canonical person ID**

---

## 1. Đính chính định danh (spec gốc sai)

| ID | name_zh | name_vi | Ghi chú |
|----|---------|---------|---------|
| **A004177** | 曇一 | **Đàm Dận** | Case trung tâm. Spec gọi "Đàm Nhất" — **không tồn tại** trong `people` (0 hit). |
| **A009590** | 法慎 | Tông Sư Hòa Thượng | Spec gán "大亮/Đại Lượng" — **SAI**. |
| **A010825** | 大亮 | **Đại Lượng** | "大亮/Đại Lượng" tồn tại NHƯNG là **A010825**, không phải A009590. |

→ **Lỗi spec chính:** gán nhầm ID cho 大亮 (đúng là A010825); nếu audit theo tên sẽ đi chệch đối tác.

## 2. Đếm động revision edges (nguồn: `lineage_edge_assertions`, read-only)

Kết quả SQL thật:

```
M unique: 14   D unique: 14   reverse pairs: 14
```

Phân cụm mỗi cạnh quanh A004177:

| Nhóm Marcus | Chiều | Đối tác (MARCUS) | Trùng (DILA) | Số |
|---|---|---|---|---|
| M-out `A004177→X` | thầy→trò | A001307 · A001755 · A004179 · A010527 · A010899 · A010902 · A010947 · A010948 · A010951 · A010953 · A011078 · A023320 | DILA vẽ ngược `X→A004177` | **12** |
| M-in `X→A004177` | trò→thầy | **A009590 (法慎)** · **A010825 (大亮)** | DILA vẽ ngược `A004177→X` | **2** |

**Tổng reverse pairs = 14** (12 out + 2 in). KHÔNG hardcode "13" — đếm động, có script trong session.

Danh sách 14 đối tác (name_zh/name_vi từ `people`):
A011078/神皓/Hằng Độ · A023320/清源/Thanh Nguồn · A001755/澄觀/Đại Thể · A010902/清江/Thích Thanh Giang · A010948/道昂/Đạo Ngang · A004179/常照/Thường Chiếu · A010527/義賓/Nghĩa Tân · A001307/湛然/Kinh Khe Nhiên · A010951/昭亮/Chiêu Lượng · A010953/法俊/Pháp Tuấn · A010947/神玩/Thần Ngoạn · A010899/辯秀/Biện Tú · A009590/法慎/Tông Sư Hòa Thượng · A010825/大亮/Đại Lượng.

## 3. Khớp snapshot `lineage_conflicts_v2` (A004177)

| conflict_type | dila_count | marcus_count | is_conflict | resolved |
|---|---|---|---|---|
| teacher_set | 12 | 2 | 1 | 0 |
| student_set | 2 | 12 | 1 | 0 |

→ Đúng bản chất **đảo chiều giữa 2 nguồn**: mỗi hướng đều có 12→2 và 2→12 đối xứng. Khác biệt count KHÔNG phải "25 quan hệ độc lập" mà là **14 quan hệ duy nhất, 2 nguồn vẽ ngược chiều**.

## 4. Phân cụm cuối

| Cụm | Số | Ghi chú |
|---|---|---|
| agreed | **0** | không cạnh nào 2 nguồn cùng chiều |
| reverse_conflict | **14** | toàn bộ 14 cạnh đều đảo chiều |
| source_only | **0** | cả 2 nguồn đều có assertion cho từng cạnh |
| unresolved_entity | **0** | mọi đối tác đều có canonical person ID → không ghép theo tên |
| ZQ_published | 0 | view `published_lineage_relation` chưa triển khai (T150 docs-only) — ngoài phạm vi T156 |

Trust level thật: MARCUS = **L1** (có ref CBETA, vd 《宋高僧傳》卷14 để trích dẫn) · DILA = **L2** (assertion dẫn từ `lineage_conflicts_v2.dila_data`, ref=None).

## 5. Kết luận cho Phase 2 (UI)

- UI NÊN hiển thị **1 conflict cluster** "Mâu thuẫn chiều quan hệ · 14 cạnh" (KHÔNG phải 2 danh sách thô 12+2 nhìn như 2 nhóm độc lập).
- Hai-làn Marcus|DILA + mũi tên chiều giúp thấy ngay: Marcus vẽ 12 trò + 2 thầy, DILA vẽ ngược y hệt.
- Match bằng canonical ID (đã sẵn) — không dùng tên ("Đàm Nhất" là tên sai; "Tông Sư Hòa Thượng" là name_vi của 法慎).
- Không fake ZQ state; dòng ZQ chỉ hiển thị "chưa xác minh" vì `lineage_conflicts_v2.resolved=0` cho A004177.

## 6. Tham chiếu (0 trùng lặp SPEC)

- `docs/lineage-conflict-audit.md` — phân loại conflict (source_coverage_gap vs direction_disagreement).
- `docs/lineage-conflict-implementation.md` — `_t86_person_conflict` + render badge/inspector hiện tại.
- `docs/CONFLICT_ENGINE_SPEC.md` — T136 conformance spec (detection/flagging/resolution).
- `docs/CONFLICT_ENGINE_SPEC.md` §3 — HITL 4 bước (không tự gộp).

## 7. Data integrity

- Toàn bộ audit = `SELECT` trên `lineage.db` (mode=ro) → **0 mutation** (no DML, no DDL, no FK trigger).
- Không đổi canonical IDs, không đổi DILA XML, không đổi Marcus imports, không đổi ZQ decisions (resolved vẫn =0).

---

## 8. ROOT-CAUSE ADDENDUM (T157, 2026-09-17) — PHẢN ĐỊNH kết luận §5

> ⚠️ **Kết luận §5 ("1 conflict cluster — mâu thuẫn lịch sử thật") là SAI and đã bị phản định.** Phần này là bản hiệu đính chính thức.

### 8.1 Bằng chứng toàn cục (đo lại reproducible trên `lineage_edge_assertions` 2026-09-17)

> Các con số ban đầu investigate (23.139 cặp / 22.326 / 11.296 / 11.377 / 16.908) được đo ở lớp tổng hợp source-wide tập SET (per-person teacher/student), khó tái lập sạch. Đây là bản đo **reproducible** trên bảng chính `lineage_edge_assertions` — dùng làm ground truth cho T157.

| Metric | Pre-flip (hiện trạng cũ) | Post-flip (hoán vị teacher↔student DILA) |
|---|---|---|
| DILA raw rows (L2) | 46.006 | 46.006 (không đổi số row) |
| DILA distinct edges | 23.014 (mỗi edge đúng ×2 — cùng quan hệ sinh ở `teacher_set` thầy lẫn `student_set` trò) | 23.014 |
| MARCUS distinct | 11.169 | 11.169 |
| Cạnh MARCUS có DILA (1 trong 2 chiều) | 11.165 | 11.165 |
| **Cạnh CÙNG chiều** | **0** | **11.165 (100% matched)** |
| Persons ≥1 cạnh đồng thuận | 0 | **3.143** |
| Đảo ngược lần nữa (sanity) | — | 0 (sau fix mà lật lại → 0 khớp, tức hướng fix đúng) |

- **0 → 11.165/11.165 sau 1 phép hoán vị:** hệ thống tuyệt đối → một nguồn (DILA) bị invert **toàn bộ**, KHÔNG phải hỗn độn lịch sử. Trước fix MỌI cạnh MARCUS có DILA đều lệch chiều (0/11.165); sau fix 100% đồng thuận.
- **Xác nhận lớp `lineage_conflicts_v2`:** `dila_data ∩ marcus_data` per-row = **0** trên toàn bộ 40.327 rows (cả 2 đều dùng id-space DILA A-codes) — mọi cặp `teacher_set`/`student_set` ở 2 nguồn đối nghịch tuần hoàn (DILA 12/2 ↔ MARCUS 2/12).
- **Marcus = chuẩn văn bản:** 14/14 anchor A004177 khớp nguyên văn CBETA《宋高僧傳》卷14 — 「其門人…越州妙喜寺常照」(`A004177→常照 A004179` đệ tử) · 「其上首曰會稽曇一」 · 「依曇一隸南山律」(`法慎 A009590→A004177` thầy).
- **DILA `persons.json` A004177 là axis-lật:** `teacher` = 12 (gồm **常照 A004179** — là 12 đệ tử THẬT), `student` = [大亮 A010825, 法慎 A009590] (là 2 thầy THẬT) → file nguồn cũng lật so với văn bản.

### 8.2 Chuỗi lật (source → DB)

```
data/persons.json (teacher/student đổi chỗ — inverter)
  → master JSON → TTL bkg:hasTeacher (build_master_json)
  → people table
  → lineage_conflicts_v2.dila_data (teacher_set/student_set swap)
  → deep_conflict_analysis.py
  → lineage_edge_assertions DILA L2 (46.006 edges, ref=None)   ← BẢNG UI ĐỌC
```

### 8.3 Phân loại chính thức

| Cụm | Chẩn đoán |
|---|---|
| Phân loại | **`pipeline_inversion`** (artifact chuyển dữ liệu) |
| Loại trừ | conflict lịch sử · source coverage gap · unresolved entity · ZQ dispute |
| Xử lý | **Fix ETL B-1** (T157): re-`INSERT` DILA L2 theo chiều canonical từ `persons.json` → post-fix **11.165/11.165 (100%) cạnh đồng thuận**, A004177 hết direction-disagreement |

### 8.4 Hệ quả cho Phase 2 UI (T157 Phase 2C)

- UI "Đối chiếu nguồn" KHÔNG vẽ "14 mâu thuẫn" — post-fix vẽ **agreed-first**; card ⚠ chỉ khi còn mismatch thật.
- DILA L2 không ref giữ badge "○ Cần khảo cứu" (trung thực).
- `lineage_conflicts_v2` (legacy, pre-fix) gắn banner LEGACY tới khi B-2 re-snapshot.
- Kỷ luật: match theo canonical ID; KHÔNG fake ZQ state (resolved=0).

### 8.5 Scope & nợ follow-up

- **ĐÃ LÀM (B-1):** DILA L2 trong `lineage_edge_assertions` — `scripts/etl_t156_dila_direction_fix.py` (backup→DELETE→re-INSERT).
- **NỢ:** (B-2) re-snapshot `lineage_conflicts_v2`; (B-3) sửa generator gốc persons.json + TTL `bkg:hasTeacher`; (B-4) kiểm tra tab lineage Profile cùng DILA-axis.

### 8.6 FIX ĐÃ APPLY + verify (2026-09-17, `--mode apply`/`--mode verify`)

- Backup trước khi ghi: `data/backups/lineage_t157_20260917_135725.db` (1.438.216.192 bytes) — restore bằng `python scripts/etl_t156_dila_direction_fix.py --revert <backup>`.
- 1 transaction atomic: DELETE 46.006 DILA L2 cũ → re-INSERT 46.006 canonical (đảo chiều, nguồn `lineage_conflicts_v2.dila_data` mirror backfill_dila T138). Tổng rows giữ **57.175** (MARCUS 11.169, DILA 46.006). 0 ALTER, 0 thay đổi confl_v2/MARCUS.
- Verify post-fix (`--mode verify` → **PASS ✅**):
  - Cạnh cùng chiều = **11.165 = 100% matched** (pre-fix 0)
  - Persons ≥1 đồng thuận = 3.143
  - A004177: **MARCUS out=12 in=2 == DILA out=12 in=2** → 0 mismatch
  - Đảo ngược AGAIN = 0 (hướng fix đúng)

### 8.7 UI post-fix — Phase 2C (2026-09-17)

- UI "Đối chiếu nguồn" (`places.html`) chuyển nguồn sang `lineage_edge_assertions` (post-fix), KHÔNG đọc `lineage_conflicts_v2` cho render này (B-2 đang hoãn).
- Agreed-first: card "✓ N quan hệ hai nguồn cùng chiều" + card ⚠ amber CHỈ khi còn mismatch thật + 2-lane Marcus|DILA + nút 🔬 Research (+N vị ẩn) + chip "○ Cần khảo cứu" cho DILA no-ref + banner LEGACY conflicts_v2.
- QA live (playwright chromium, :8080): A004177 = 14/14 đồng thuận, 0 mismatch, 0 console error.
- Chi tiết: `docs/lineage-relation-conflict-A004177-implementation.md`.
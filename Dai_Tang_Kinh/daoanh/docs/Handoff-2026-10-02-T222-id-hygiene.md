---
id: T222-handoff-id-hygiene
title: "Handoff — Hoàn tất T177→X-T177, gỡ 6 ID trùng, thêm guard trùng ID"
date: 2026-10-02
module: Task Governance / Repo Hygiene
status: done
owner: mimo-flash
head_at_write: d92982e35d19a57cbb895825d4859f59a2e41672
---

# Handoff — Hoàn tất T177→X-T177, gỡ 6 ID trùng, thêm guard trùng ID

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-02 |
| HEAD lúc viết | `d92982e` (repo root = `visjs-app`) |
| Session làm | Rename T177 → X-T177 · đổi số 6 ID trùng · guard trùng ID · AGENTS §16–§17 |
| Test | `test:t216` **10/10** · `t211` 15/15 · `t208` 19/19 · `t207` 21/21 · `t203` 27/27 |
| Preflight | `npm run dup:ids` → **0 trùng thật** · `npm run guard` → PASS |
| DB | **không đụng** (docs + script thuần) |
| TTL | **không đụng** |

## 2. Đọc trong 2 phút

**Đã làm gì**
1. Đóng nửa trạng thái rename `T177-* → X-T177-*` (T177 còn trong HEAD nhưng đã xoá trên đĩa;
   `X-T177-*.md` untracked) → commit rename + cập nhật 23 path tham chiếu.
2. Chạy guard mới → phát hiện **6 ID trùng** đã tồn tại từ lâu: `T158`, `T206`, `T215`.
3. Gỡ 6 ID trùng bằng cách đổi số phía có footprint nhỏ nhất.
4. Đưa `--check-dup-ids` vào `npm run pipeline` để trùng ID **FAIL pipeline**.
5. Bổ sung `AGENTS.md §16` (cấp ID phải kiểm 2 tầng) và `§17` (HEAD dịch chuyển, `update-ref` CAS).

**Phát hiện quan trọng nhất**
Plan doc phải đổi ID **3 lần** (T180 → T216 → T217 → T222) vì **2 lần do session khác chiếm ID**:

| Bị chiếm | Bởi ai | Dạng đặt chỗ | Guard thấy? |
|---|---|---|---|
| `T216` | Follow-up *"ETL UPSERT guard — preserve dila_id"* | **prose** trong 4 file, **không có file task** | ❌ **không** |
| `T217` | `tasks/T217-vnpa-etl-preservation-guard.md` | file task thật, tạo **trong lúc** tôi đang xử lý | ✅ có (nếu đã nối pipeline) |

⇒ **Kết luận hệ thống: guard file-scan là không đủ.** ID có thể bị "đặt chỗ" bằng văn bản.
Vì vậy `AGENTS.md §16` bắt buộc **2 tầng**: `npm run dup:ids` **+** `grep 'T\d+'` trong
`docs/tasktodo.md` và `docs/Mimo-Flash/`.

**3 việc Admin cần làm ngay**
1. Xem `docs/Mimo-Flash/X-T222-cloud-session-chain-c1-c6-plan.md` — status `blocked` (superseded), ID `T222` claimed by VNPA Preflight Scope Alignment. Cloud Session Chain plan was never executed. **Chưa chạy được C1–C6.**
2. `tasks/T167-rules-constrained-buddhist-translation-engine.md` còn **BOM** → frontmatter
   không parse được. Tôi **cố ý không đụng** vì task đang `in_progress` của session khác.
3. Cân nhắc tạo `tasks/T217-vnpa-etl-preservation-guard.md` → đây là task thật đang
   `in_progress`, hãy đảm bảo nó dùng ID `T217` và `T216` được giữ cho follow-up ETL.

## 3. Đề suất phần chữa dựng cho từng task

### 3.1 Rename `T177` → `X-T177` (commit `4f71b12`, `46c5bb3`)

- **Vấn đề**: T177 là ngoại lệ cuối cùng chưa được đổi tên trong `docs/Mimo-Flash/`
  (22/22 file anh em đã đổi sang `X-`). Trạng thái nửa vời: file gốc còn trong HEAD nhưng
  đã xoá trên đĩa; bản `X-` untracked.
- **Cách sửa**: chọn hướng **hoàn tất rename `X-`** thay vì hoàn nguyàn. Lý do đo được:
  22/22 file `T1xx-*` khác đã dùng `X-`; `X-T177-*.md` nội dung **giống hệt** bản gốc.
- **Bằng chứng**: `R098` / `R097` (98%/97% similarity, 7+/7−, không đổi logic). Task ID
  `T177` **giữ nguyên** trong frontmatter ⇒ không phá mapping task.
- **Kết quả**: sửa 23 path tham chiếu trong 10 file (bỏ qua 2 file đang được session khác
  đổi tên). Giữ nguyên phần narrative lịch sử trong `tasktodo.md` / `taskdone.md` / `sessions/`.

### 3.2 Gỡ 6 ID trùng (commit `449f86c`)

Nguyên tắc chọn: đổi số phía có **① `status` kết thúc → ② ít tham chiếu → ③ không có
`docs/plans|reports/` → ④ không phải ID tasktodo đã công bố**.

| ID | Giữ nguyên | Đổi số | Bằng chứng |
|---|---|---|---|
| `T158` | `T158-lineage-consensus` | `glossary-resolver` → **T218** | tasktodo ghi *"T158 ✅ DONE — Lineage Consensus Layer"*; commit `d6b9154` *"feat: T158 - Lineage Consensus Layer"*; 6 refs (kể cả `tasks/T167-*`) vs 3 refs |
| `T206` | `T206-fix-mojibake-eth-to-dstroke` | `pl-corrupt` → **T219** | cả hai `done`, **0 refs**; mojibake thuộc series T205–T211 có backup dir + ghi trong AGENTS/handoff |
| `T215` | `T215-dila-ttl-evidence-and-self-edges` | `vnpa-dila-id-recovery` → **T220** | self-edges **đang chạy 4/9**, có `docs/plans/T215-*.md` + `docs/reports/T215-self-edges/` + Handoff riêng ⇒ không đổi |

Mọi file đổi số ghi `former_ids: [...]` để ID cũ vẫn grep được.

### 3.3 Guard trùng ID (`1283ee9`, `449f86c`, `d92982e`)

`scripts/build_progress_data.py --check-dup-ids` (alias `npm run dup:ids`), nối vào
`npm run pipeline` ngay sau `guard`. 3 lỗ hổng phát hiện khi test:

| Lỗ hổng | Hậu quả | Cách sửa |
|---|---|---|
| File `tasks/` thiếu frontmatter `id:` | **lọt khỏi kiểm tra** | suy ID từ tiền tố tên file |
| 3 file `tasks/` có **BOM** (`﻿---`) | `---` không khớp ⇒ frontmatter hỏng ⇒ báo trùng giả | đọc `utf-8-sig`; gỡ BOM cho `T197`, `T199` |
| `docs/` khai báo `task: tasks/<...>` | bản mở rộng của task bị coi là task thứ hai | nhận diện ⇒ INFO |

Không báo động giả cho: `_book/` (mirror), file `X-*` (superseded theo quy ước),
`docs/*.md` chỉ đặt tên theo ID task.

## 4. Cảnh báo bắt buộc

1. **`git update-ref` CAS luôn FAIL trên máy này** — `couldn't set 'refs/heads/master'`,
   `PermissionError [WinError 5]` khi `os.replace`. Phải fallback **ghi file ref trực tiếp
   có kiểm tra CAS thủ công**. *Không* tin `update-ref` không CAS trả 0 — nếu `new == old`
   git bỏ qua ghi ⇒ "OK" là no-op, **chưa hề commit**.
2. **HEAD dịch chuyển liên tục** vì nhiều session commit song song. Trong một phiên quan
   sát: `0aa0113 → 46c5bb3 → 1283ee9 → 449f86c → d92982e`. **Phải tính lại `(parent, new)`
   ngay trước lúc commit**, không dùng số đo lúc đầu phiên.
3. **Cặp đường dẫn git phải phân biệt** (tôi sai 3 lần):
   - `git add` / `update-index --force-remove` / `ls-files` (pathspec) → **tương đối `cwd`**
   - `update-index --cacheinfo` / `git show HEAD:<p>` → **tương đối repo root**
   - `git ls-tree HEAD` **không có `--`** → liệt kê theo `cwd` hiện tại ⇒ **dễ tưởng cấu
     trúc repo lệch** (đã xảy ra 1 lần, suýt kết luận sai rằng HEAD không có `Dai_Tang_Kinh/`)
4. **`git add -- docs tasks` sẽ nuốt WIP của session khác** nếu họ đang sửa cùng file
   (đã thấy `tasktodo.md` có 14 dòng thay đổi trong đó chỉ 4 là của tôi). Phải dựng blob từ
   `HEAD` + chỉ thay đổi của mình, rồi `--cacheinfo`.
5. **Em-dash `—` và ký tự Unicode bị hỏng khi pipe script qua PowerShell.** Phải viết
   script ra file `.py` bằng tool, hoặc dùng `\uXXXX`.
6. **BOM trong `tasks/*.md`** làm `parse_frontmatter` im lặng trả `{}` ⇒ dashboard đọc sai
   `title`/`status`. Đáng quét toàn repo khi có dịp.
7. `pipip`/claude-mem (`127.0.0.1:37700`) **không chạy** (`curl exit=7`) ⇒ ghi memory bền
   vững vào `AGENTS.md` + file Handoff này.

## 5. Lệnh revert từng task

| Task | Lệnh | Mất dữ liệu? |
|---|---|---|
| Gỡ 6 ID trùng + guard + §16/§17 | `git revert --no-edit 449f86c` | Không (docs+script) |
| Vá `former_ids` | `git revert --no-edit d92982e` | Không |
| Đổi ID T180→T216 + guard lần 1 | `git revert --no-edit 1283ee9` | Không |
| Cập nhật 10 file tham chiếu | `git revert --no-edit 46c5bb3` | Không |
| Rename T177→X-T177 | `git revert --no-edit 4f71b12` | Không — đổi tên file, nội dung giữ nguyên |

**Thứ tự revert phải ngược**: `d92982e` → `449f86c` → `1283ee9` → `46c5bb3` → `4f71b12`.
Không commit nào chạm DB/TTL ⇒ **revert thuần văn bản, không mất dữ liệu**.

## 6. Bảng file tạo/sửa trong session

| Hành động | File |
|---|---|
| Đổi tên | `docs/Mimo-Flash/T177-*.md` → `X-T177-*.md` (2 file) |
| Đổi tên | `tasks/T158-glossary-resolver-pre-translation-lookup.md` → `T218-*.md` |
| Đổi tên | `tasks/T206-pl-corrupt-canonical-name-vi-fix.md` → `T219-*.md` |
| Đổi tên | `tasks/T215-vnpa-dila-id-recovery.md` → `T220-*.md` |
| Đổi tên | `docs/Mimo-Flash/T215-VNPA-DILA-ID-RECOVERY-01.md` → `T220-*.md` |
| Đổi tên | `docs/Mimo-Flash/T216-cloud-session-chain-c1-c6-plan.md` → `T222-*.md` (sau 3 lần đổi ID) |
| Tạo | `scripts/t220_renumber_dup_ids.py`, `scripts/t220_fix_renumber_aftermath.py`, `scripts/t220_plan_doc_t222.py` |
| Sửa | `scripts/build_progress_data.py` (thêm `collect_frontmatter_ids`, `check_dup_ids`) |
| Tạo | `tests/test_t216_dup_ids_guard.py` |
| Sửa | `package.json` (thêm `dup:ids` + nối vào `pipeline` + commit `test:t208`/`test:t211` bị bỏ sót) |
| Sửa | `AGENTS.md` (thêm §16, §17) |
| Sửa | `docs/ROLLBACK.md` (1 dòng revert) |
| Sửa (10 file) | `tasktodo.md`, `taskdone.md`, `T165-PHASE8-IMPLEMENTATION-PLAN.md`, `X-T165-*-SPEC.md`, `X-T165-*`, `X-T174-*`, `sessions/2026-09-26_*`, `sessions/2026-09-30_*`, `tasks/T178-*`, `tasks/T197-*` |
| Sửa (3 file) | `X-T165-*-SPEC.md`, `X-T168-rule-resolver-context-compiler-PLAN.md`, `sessions/2026-09-24_*` (đổi ref T158→T218) |
| Vá BOM | `tasks/T197-t177-review-correction.md`, `tasks/T199-vnpa-canonical-row-and-han-trim.md` |

## 7. Sai lầm tự mình làm + bài học

| Sai lầm | Bài học |
|---|---|
| Lấy T216 trong khi ID đã bị **đặt chỗ bằng prose** | Guard file-scan không đủ. Cấp ID phải **grep prose** (`AGENTS.md §16` tầng 2) |
| Lấy T217 trong khi session khác **tạo file task ngay lúc đó** | Worktree dùng chung ⇒ cấp ID và commit phải liền mạch, không dàn bước |
| Chèn `former_ids` **rồi mới** global-replace token | Giá trị trong `former_ids` bị nuốt theo. Phải replace `former_ids` **sau**, hoặc dùng placeholder — **đã dính 2 lần** (T217/T222, T220) |
| `git ls-tree HEAD` không có `--` khi đang ở trong subdir | Tưởng repo lệch cấu trúc. Luôn so đường dẫn với `git rev-parse --show-toplevel` |
| Xoá temp index nhưng quên `git read-tree HEAD` | Index rỗng ⇒ `git diff --cached` hiện **toàn bộ repo là `D`**. HEAD không hỏng nhưng dễ hoảng |
| `update-index --force-remove` dùng path repo-root-relative | Pathspec theo `cwd` ⇒ `--force-remove` im lặng không làm gì, tưởng rename đã xong |
| Dùng `os.replace` để ghi ref | WinError 5. Phải ghi tại chỗ `open(ref,"w")` |

## 8. Việc CHƯA xong (theo ưu tiên)

1. **T222 vẫn `blocked`** — chờ Admin copy `t166-sync.bundle`. Chưa chạy được Phase 0/C1–C6.
   Cần quyết định của Admin: có làm chuỗi C1–C6 không, hay chỉ giữ doc.
2. **`data/progress_data.json` đã lỗi thời** vì số task đổi. **Tôi cố ý không regen** vì
   lệnh đó đọc `docs/**/*.md` và sẽ nuốt WIP của các session khác. Cần chạy khi các session
   đã commit hết, hoặc chạy rồi review diff cẩn thận.
3. **`tasks/T167-*.md` còn BOM** — cần owner của task `in_progress` gỡ.
4. **`agents/SESSION.md`** còn trỏ 2 tên file cũ (`T215-vnpa-dila-id-recovery`,
   `T215-VNPA-DILA-ID-RECOVERY-01`). Không sửa vì là file log của session khác.
5. **10 file TTL mất** (T209) vẫn chờ Admin: `TS-Chuong-Hiep-Chanh-Tri`,
   `TS-Duong-Ki-Phuong-Hoi`, `TS-Phap-Kiem-Minh-Giac`, `TS-Phap-Mon-Phat-Da`,
   `TS-Thiet-Bao-Cam-Ung`, `TS-Thiet-Dam-Chanh-Luan`, `TS-Thiet-Dang-Bao-Quang`,
   `TS-Thiet-Dinh-An-Triem`, `TS-Thiet-The-Triem-An`, `TS-Toan-Y-Pho-Hue`.
6. **13 file URI sai + nhãn lệch** (nhóm T211 group 2) cần Admin quyết định danh tính.
7. **Preflight còn blocking**: `L1=13`, `L2=15`, `L7=10` ⇒ ETL vẫn bị chặn.
8. **`key_norm_alt` (T208) chưa nối** vào 2 call site `app.py` (~L1250, ~L2824) — `app.py`
   còn WIP của session khác.

## 9. Lệnh kiểm tra nhanh (1 phút)

```bash
cd /opt/.../visjs-app/Dai_Tang_Kinh/daoanh
npm run dup:ids     # [OK] Không có task ID trùng thật   <-- phai 0 trung
npm run guard       # SSOT repo root OK
npm run test:t216   # PASS 10/10
```

Kiểm tra thêm: `git log --oneline -5` phải thấy `d92982e`, `449f86c`, `1283ee9`, `46c5bb3`,
`4f71b12`. Xem `npm run pipeline` có chứa `dup:ids` ngay sau `guard`.

## 10. Ghi chú cho agent kế tiếp

- **Checklist trước khi đụng việc mới:**
  1. `git rev-parse HEAD` + `git log --oneline -3` (HEAD có thể đã đổi).
  2. `npm run dup:ids` — phải 0 trùng.
  3. Nếu cần cấp ID mới: `npm run dup:ids` **+** grep prose (2 tầng, `AGENTS.md §16`).
  4. Kiểm tra có ai đang sửa cùng file (`git status --porcelain -- <file>`).
- **Cách commit an toàn (đã dùng cả phiên):** temp index `read-tree HEAD` → `hash-object -w`
  từng file → `update-index --cacheinfo` → `git diff --cached --name-status` **kiểm đúng danh
  sách** → `write-tree`/`commit-tree` → `update-ref` (CAS, nếu fail thì ghi file ref tại chỗ
  có kiểm CAS thủ công).
- **Đừng** chạy `git commit` không có path khi `.git/index` có thể đang stale/lock.
- **3 temp index của session khác còn nằm trong `.git/`**: `wt_case_index`, `wt_fix_index`,
  `wt_hf_index`. Đã **cố ý không xoá**. Dọn khi chắc chắn không ai đang dùng.
- **Quy ước `X-<id>-*.md`** = directive/SPEC đã superseded (giữ nguyên `id` gốc).
  Task sống ở `tasks/`. Đã áp dụng cho 22/24 file `T1xx-*` trong `docs/Mimo-Flash/`.
- **`docs/Mimo-Flash/_book/`** là mirror toàn bộ — **loại trừ khỏi mọi phép đếm/grep ID**.

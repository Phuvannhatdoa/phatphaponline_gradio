---
id: T222
former_ids: [T180, T216, T217]
former_ids: [T180, T216]
title: "Cloud Session Chain C1–C6 — Phase 0 Sync + Review (T165→T166→T167)"
module: Editorial / Translation Guard
priority: high
status: blocked
owner: claudecode
depends_on: [T165, T166, T167]
created: 2026-09-26
revised: 2026-10-02
renamed_from: T180
designed_by: mimo-flash
reviewed_by: mimo-flash (read-only, 2026-10-02)
handoff_to: Claude Code Agent (Phase 0 merge/DB-sync + C1–C6)
---

# T222 — Cloud Session Chain C1–C6: Phase 0 Sync + Plan chi tiết

> **Nguồn:** Admin gửi plan 6 session (C1–C6, $100) → mimo-flash review read-only
> (2026-09-26): **khung dependency ĐÚNG**, nhưng **P0×4 + P1×6** nếu chạy nguyên trạng.
> Admin: "Phê chuẩn đề xuất" + "tạo task mới Txx".
>
> **Đổi ID 2026-10-02 (Admin chốt):** `T180` → **`T222`**.
>
> Chuỗi cấp ID (cả 3 lần, mỗi lần do máy khác):
>
> | Bước | Lý do |
> |---|---|
> | `T180` | đã bị *"T180 — Phase 7 GOLD exporter"* chiếm |
> | `T216` | đã bị đặt chỗ bằng **prose** cho follow-up *ETL UPSERT guard* (task thật, đang chờ Admin) |
> | `T222` | session khác tạo `tasks/T222-vnpa-etl-preservation-guard.md` trong lúc đang xử lý |
> | `T218`-`T221` | đã cấp cho 3 task gỡ trùng ID (xem ROLLBACK) / `T221` đã bị đặt chỗ |
>
> `T222` trống hoàn toàn: 0 task file, 0 tham chiếu prose.
>
> **Bài học:** `build_progress_data.py --check-dup-ids` chỉ thấy ID
> trùng ở mức file. Reservation bằng **prose** (như `T216` ộ là
> vày) hoặc để dỳ cho thấy. Quy tắc: trước khi cấp
> ID mới, **grep `T\d+` trong `docs/tasktodo.md` + `docs/Mimo-Flash/`** (AGENTS.md §16).
>
> **Cảnh báo mirror:** `docs/Mimo-Flash/_book/` là **bản sao toàn bộ**, không phải nguồn
> SSOT. Mọi tra cứu ID/path phải loại trừ `_book/` (nó nhân bản tới mức gây đếm trùng ID).
>
> **Role:** code/merge/DB = Claude Code · docs/closure = mimo-flash · restart = Admin.

---

## §0. ĐÍNH CHÍNH 2026-10-02 (mimo-flash, read-only + đo thật)

Bản gốc 2026-09-26 có **10 claim sai**. Dưới đây là claim → thực tế → trạng thái sau sửa.

| # | Claim bản gốc | Thực tế (đã verify) | Xử lý |
|---|---|---|---|
| 1 | P0-1: SHA `b89c7bed` sai, phải `b89c7be` | **SAI.** Cả hai cùng resolve `b89c7bedb4d61144398516445044abdc273caa41`; `merge-base --is-ancestor` exit **0** cho cả hai ⇒ C1 **không** STOP | §0.1 |
| 2 | P1-1: `tasks/T166-*.md` không tồn tại | **SAI.** HEAD có **2 file**: `T166-bio-edit-write-path-guard.md`, `T166-dashboard-hygiene-batch.md` | §0.2 |
| 3 | §F + P1-1: dynamic-filter là **T167**, SSOT `X-T167-*.md` | **SAI — nguy hiểm.** `tasks/T167-rules-constrained-buddhist-translation-engine.md` **đã tồn tại** (status `in_progress`) và là task **engine khác**. Dynamic-filter thực tế = **T177**, nay ở `X-T177-*.md`. **`X-T167-*` không tồn tại** | §0.3 |
| 4 | P1-1: `T177-*.md` = MISS, thật là `X-T167-*.md` | **SAI.** `T177-*.md` là tên đúng (đã rename `X-T177-*.md`, commit `4f71b12`) | §0.3 |
| 5 | Acceptance: 6 file `PROMPT-C*-rev1.txt` tồn tại | **KHÔNG TỒN TẠI** — 0 file trong cây, `git log --all --diff-filter=A -- "*PROMPT-C*"` rỗng | **Admin 2026-10-02: bỏ, không cần.** §C chuyển thành delta gộp trong plan |
| 6 | A2-3: port 14 rules 96→110 | Đã trôi. Đo 2026-10-02: total **142**, active **119** | §A (đo tại runtime) |
| 7 | A table: cache 1762 | Đã trôi. Đo 2026-10-02: **1912** | §A (đo tại runtime) |
| 8 | A table: tests 76 PASS / 112 PASS | Đã trôi. `pytest --collect-only -q` = **197 collected**, **2 lỗi collect** | §A + P2 |
| 9 | A/Diagram: T166 đang in_progress | Đã trôi: **T165 done · T166 done · T167 in_progress** | §D |
| 10 | Acceptance: dashboard 102 task | Đã trôi (133 task / 101 done tại lúc đo). Số này biến động theo session | Acceptance |
| 11 | P1-4: raw INSERT `app.py:17350 / :17397` | Line ref đã trôi → **L18923 / L18933**. Và **không** tìm thấy comment "carve-out"/"by design" | §0.4 (chưa xác minh được → in-scope C1) |
| 12 | P0-3: lỗ hổng thật = `admin_namevi_map_delete` | **ĐÃ SỬA trên Windows.** `admin_namevi_map_delete` (L14152) **và** `admin_namevi_map_update` (L14175) đều đã có `verify_session` | §0.5 |

### §0.1 — SHA (thay P0-1)

Bản gốc khẳng định `b89c7bed` (8 ký tự) là SHA sai và `b89c7be` mới đúng, kèm mệnh lệnh
"STOP oan". **Kiểm chứng bác bỏ.** Hai chuỗi là **tiền tố của cùng một commit**:

```
b89c7bedb4d61144398516445044abdc273caa41
└───────┘└──┘  cùng một SHA 40 ký tự
git merge-base --is-ancestor b89c7bed  HEAD  -> exit 0
git merge-base --is-ancestor b89c7be   HEAD  -> exit 0
```

⇒ C1 **không** STOP. Fix "rev.1 đã sửa" là vô nghĩa.

**Quy tắc mới:** mọi SHA trong C1–C6 phải là **đủ 40 ký tự**. Tiền tố ngắn vừa không
bắt được lỗi gì, vừa tự tạo rủi ro *ambiguous prefix* khi repo lớn thêm.

### §0.2 — `tasks/T166-*` (thay P1-1 dòng 1)

HEAD có 2 file `tasks/T166-*.md`. Bản gốc dựa trên cây lúc 2026-09-26. Khi chạy C1 phải
**resolve path tại runtime** (`git ls-tree -r --name-only HEAD`), không hardcode trạng thái
từ plan.

### §0.3 — ID reconciliation (thay §F cũ)

| | Task | File | Status |
|---|---|---|---|
| Dynamic-filter / absorb directive v2 | **T177** | `docs/Mimo-Flash/X-T177-directive-v2-trie-xml-dualhash-REVIEW.md`, `X-T177-dynamic-filter-absorb-directive-v2.md` | ✅ DONE |
| Rules-constrained translation engine | **T167** | `tasks/T167-rules-constrained-buddhist-translation-engine.md` | `in_progress` |
| Canonical identity guard | **T166** | `tasks/T166-bio-edit-write-path-guard.md`, `T166-dashboard-hygiene-batch.md` | ✅ DONE |
| Dash-regen T130 closure | **T165** | — | ✅ DONE |

- Bản gốc viết "task = T167 (Windows gọi là T177)" — **đảo ngược**. Sự thật: **T177** mới là
  dynamic-filter; **T167** là engine. Nếu chạy nguyên bản gốc, C3–C6 sẽ cập nhật **nhầm
  task engine** và bỏ sót closure của dynamic-filter.
- `X-T167-*.md` **không tồn tại** — trỏ vào đó sẽ hỏng.
- Quy ước repo: `X-<id>-*.md` = bản directive/SPEC đã superseded; task sống ở `tasks/`.
  Đã xử lý 22/22 file `T1xx-*` trong `docs/Mimo-Flash/` theo quy ước này; T177 là ngoại lệ
  cuối cùng, đã đóng tại commit `4f71b12`.
- Task ID giữ nguyên `T177` trong frontmatter ⇒ **đổi tên file không đổi ID task**.
- **KHÔNG** tạo task mới trong series T177.

### §0.4 — Raw INSERT carve-out (thay P1-4 dòng 4)

Bản gốc: raw INSERT `status='edited'` tại `server :17350 / win :17397`, "cố ý không
post-check", cần carve-out by-design + sửa audit false-negative.

Đo 2026-10-02: `app.py` 23.348 dòng; raw `INSERT INTO translation_cache` tại **L18923** và
**L18933**. **Không** tìm thấy chuỗi `carve-out` hay `by design` trong toàn `app.py`.

⇒ Line ref cũ sai; **và cơ sở "by design" chưa được chứng minh bằng comment**. Không được
mang carve-out vào tiêu chí chấp nhận khi chưa xác minh. **Để in-scope C1**: đọc context
L18900–L18950, xác định write-path này là human-edit (không cần post-check) hay là bug;
nếu là human-edit thì **thêm comment carve-out vào code** để lần sau kiểm được.

### §0.5 — P0-3 security (đã sửa, giữ làm regression gate)

Bản gốc coi `admin_namevi_map_delete` là lỗ hổng thật còn mở. Đo 2026-10-02 trên Windows:

| Endpoint | Def line | `verify_session` |
|---|---|---|
| `admin_namevi_map_delete` | L14152 | ✅ có |
| `admin_namevi_map_update` | L14175 | ✅ có |

⇒ C6 #11 **không còn là fix mới**, chỉ là **regression guard**: xác minh cả 2 trả 403 để
chống hồi quy (đặc biệt khi merge bundle từ server — server đã có `2a69eeb`).

---

## §A. PHASE 0 — SYNC BẮT BUỘC TRƯỚC C1

**Trạng thái 2026-10-02 (đo trên Windows; cột server KHÔNG verify được từ máy này):**

| | Server (SSOT deploy) | Windows `truyenthua\visjs-app` |
|---|---|---|
| Git | **chưa verify** (không có bundle) | `46c5bb3` |
| Bundle | **NO-BUNDLE** (chờ Admin copy `t166-sync.bundle`) | không cần |
| identity cols (`identity_status/…`) | **chưa verify** | ✅ đã apply (đủ 3 cột) |
| `translation_rules` total / active | **chưa verify** | **142 / 119** |
| `translation_cache` rows | **chưa verify** | **1912** |
| tests | **chưa verify** | 197 collected, **2 lỗi collect** |
| task dynamic-filter | **chưa verify** | `X-T177-*.md` (task ID `T177`, DONE) |

> **Quy tắc số liệu (thay P2):** cột "chưa verify" **không được điền bằng số Windows**.
> Mọi con số phải đo tại thời điểm chạy và ghi kèm timestamp. Bản gốc điền số Windows vào
> cả hai cột rồi so sánh ⇒ bảng so sánh gây hiểu nhầm, và số đó đã trôi 2 lần.

**A1 — Git merge:** Admin copy bundle → Claude Code paste chính sách resolve đã chốt
(app.py=--ours · lineage.db=--ours · giữ tên `X-` · union `style_constitution`) → verify
pytest/guard/audit trên **server**.

**A2 — DB sync (server = SSOT, Admin đã phê):**
1. Backup `data/backups/lineage_t216_pre-sync_<ts>.db`.
2. Apply `scripts/t166_identity_migrate.py` lên server DB → verify
   `PRAGMA table_info(translation_cache)` có `identity_status/identity_issues/identity_lock_hash`.
3. Port rules thiếu: **đếm bằng query thật trên server**, không dùng con số 14/96→110 của
   bản gốc. Export active rules từ DB Windows → import server (script Python, try-except,
   log tiếng Việt; KHÔNG tay SQL prod) → recount.
4. **Measure lại baseline trên server** (source chars · prompt chars · prompt_tokens · total ·
   selected rule count) — số Windows (119 active / 3.422 tokens) **chỉ là tham khảo**.

**A3 — Reverse bundle** `git bundle create t216-back.bundle master ^<server_base>` → Admin trả
Windows (chống diverge lại). Lặp lại sau mỗi session PASS (tối thiểu sau C2, C6).

**Gate Phase 0 DONE = C1 được paste:** merge commit có trên server · identity cols present ·
rules count = số đo server · baseline token đã ghi · reverse bundle đã giao.

---

## §B. REVIEW C1–C6 (evidence đã verify — fix bắt buộc)

### P0 — sai sự thật / tự đá mình
- **P0-1 SHA:** xem §0.1. Không phải lỗi SHA; rủi ro thật là *ambiguous prefix* ⇒ **bắt 40 ký tự**.
- **P0-2 không ai lo sync:** 2 checkout + DB có thể divergent (identity cols thiếu, rules
  lệch) → chuỗi C1–C6 giả định 1 repo/DB. Giữ precondition Phase 0 (§A).
- **P0-3 security:** xem §0.5. Đã sửa trên Windows ⇒ hạ xuống **regression guard** (2 endpoint
  → 403), bắt buộc sau khi merge bundle từ server.
- **P0-4 chạy ở đâu chưa chốt:** trên server C1 có thể STOP ngay; trên Windows commit không
  về server, C2 live smoke lệch. Mọi session chạy **sau merge, trên server**; EPERM chỉ là
  ENV-ONLY Windows.

### P1 — path/phạm vi
1. **SSOT paths:** resolve path bằng `git ls-tree -r --name-only HEAD` tại runtime, không
   hardcode từ plan. Sự thật 2026-10-02: `tasks/T166-*.md` ✅ có 2 file · `tasks/T167-*.md` ✅
   có · `tasks/T177-*.md` ❌ không có (file ở `X-T177-*`) · `X-T167-*.md` ❌ không có ·
   `docs/ADMIN_REVIEW_DASHBOARD.md` ✅ có. Mapping ID: xem §0.3.
2. **`admin/app.py`:** bản gốc khẳng định "KHÔNG tồn tại". Chỉ verify được trên server; quy tắc
   là **audit nếu tồn tại; KHÔNG tạo mới**.
3. **C1 trùng G1:** G1 đã chạy matrix 23/23 + FINAL REPORT (PARTIAL, 3 blocker) → C1 tham chiếu,
   scope = audit vs SPEC + test thiếu, không làm lại.
4. **Raw INSERT carve-out:** xem §0.4. **Chưa xác minh được** → in-scope C1, không tự động
   mang carve-out vào tiêu chí.
5. **EPERM pipeline Windows 必 FAIL** → ENV-ONLY; PASS tính trên **server Linux**.
6. **C2 conflict role:** dashboard/tasktodo/ROLLBACK/session closure = **mimo-flash** sau Admin
   duyệt report → tách khỏi C2.

### P2
- C1 opening ghi closure (mâu thuẫn mission) · số test cứng 18/18-11/11-23/23 = số Windows →
  "kỳ vọng ≥X, ghi số THẬT" · C3 hardcode 110/3.422 → measure lại (§A2-4).

---

## §C. DELTA THEO TỪNG SESSION C1–C6

> **Admin 2026-10-02: KHÔNG cần 6 file `PROMPT-C*-rev1.txt`, bỏ.** Các fix bên dưới được
> **gộp thẳng vào plan này** và là ràng buộc bắt buộc khi chạy từng session — không cần file
> prompt riêng. Acceptance cũ "6 file `PROMPT-C*-rev1.txt` tồn tại" **đã bị gỡ bỏ**.

| Session | Ràng buộc bắt buộc (thay cho prompt rev.1) |
|---|---|
| **C1** matrix A–J | SHA đủ **40 ký tự** · path resolve runtime (`git ls-tree`) · mapping ID theo §0.3 · tham chiếu G1 report · SECURITY **cả 2** endpoint → 403 (regression guard) · điều tra raw INSERT L18923/L18933 và **thêm comment carve-out nếu đúng là human-edit** · audit `admin/app.py` nếu tồn tại · EPERM ENV-ONLY · gỡ closure khỏi mission · precondition Phase 0 · không commit docs workflow |
| **C2** phase5 closure | prereq C1 PASS + Phase 0 · closure docs (dashboard/tasktodo/ROLLBACK/session) = **mimo-flash** · live smoke URL server + 2 biến thể dấu · SECURITY cả 2 endpoint · nhắc Admin restart (không tự restart) · EPERM carve-out · path resolve runtime |
| **C3** dynamic-filter D1–D3 | **task ID = T177** (KHÔNG phải T167) · file `X-T177-*.md` · precondition Phase 0 · mọi số baseline **measure lại trên server** · audit `admin/app.py` nếu tồn tại · không commit docs workflow |
| **C4** dualhash + XML D4–D5 | prereq D1–D3 PASS + Phase 0 (identity cols phải CÓ sẵn) · task ID **T177** · path `X-` · numbers measure · giữ matrix A–H |
| **C5** D8 + 429 integration | prereq C3+C4 PASS · 429/prompt baseline = số Windows D7, **measure server** · task ID **T177** · spend guard giữ nguyên |
| **C6** final red-team | #11 = **delete + update cả 2 → 403** · verify sync Phase 0 (merge-base / rules count / identity cols) · carve-out raw-INSERT **chỉ sau khi C1 xác minh** · EPERM ENV-ONLY · chain ghi **T177** · path resolve runtime |

---

## §D. GATES & DEPENDENCY

```
            [Phase 0: BUNDLE MERGE + DB SYNC]   ← T222 §A, chặn tất cả
                          │
        T165 ✅ DONE   T166 ✅ DONE   T167 🔄 in_progress
                          │
                     C1 (matrix)  →  C2 (closure)     [mimo closure docs sau PASS]
                    ╲            ╱
                     T177 = dynamic-filter (✅ DONE, X-T177-*.md)
                          │
        C3 (D1–D3) → C4 (D4–D5) → C5 (D8+429)
                          │
                     C6 RED-TEAM (cuối)
```

- C4 **không chạy** trước C3 PASS · C5 trước C4 PASS · C6 trước T165+T166+T167 PASS.
- C2 PASS ⇒ mimo-flash làm closure T166 (tasktodo→done, ROLLBACK, session).
- Mỗi lần PASS ≥ C2/C6: reverse bundle (§A3) trước khi sang session mới.

---

## §E. ROLES (Admin chốt 2026-09-26)

- **Claude Code:** merge · DB sync scripts · mọi code C1–C6 · test · report.
- **mimo-flash:** mọi docs (plan/tasktodo/ROLLBACK/session/dashboard) — KHÔNG code.
- **Admin:** copy bundle · duyệt danh sách · ra lệnh restart (verify 403) · duyệt report →
  lệnh closure.

---

## §F. GUARD ID TRÙNG

Bản gốc đổi ID `T180` → `T180` (vô nghĩa) rồi mới phát hiện trùng với GOLD exporter.
Đã thêm guard phát hiện trùng `id:` trong `scripts/build_progress_data.py`
(`--check-dup-ids`), loại trừ `_book/`. Chạy trước mỗi lần regen dashboard:

```
python -X utf8 scripts/build_progress_data.py --check-dup-ids
```

---

## Acceptance (DONE khi)

- [ ] Admin đã copy `t166-sync.bundle`; Phase 0 §A1–A3 DONE (gate C1)
- [ ] Mọi path trong C1–C6 resolve bằng `git ls-tree` runtime, không hardcode
- [ ] Mọi SHA dùng đủ 40 ký tự
- [ ] C1 đã xác minh + **ghi comment** cho raw INSERT L18923/L18933
- [ ] C2 PASS → T166 closure; C6 PASS → handover report
- [ ] `build_progress_data.py --check-dup-ids` = 0 trùng
- [ ] tasktodo + dashboard **regen** (không hardcode "102 task") + ROLLBACK row đủ

---

## Revert

Docs-only: `git revert --no-edit <sha_T222>` (row trong `docs/ROLLBACK.md`, hash-fill).
Phase 0 code/DB: merge → `git revert -m 1 <merge_sha>` · DB → script `--revert` + backup
`lineage_t216_*`.

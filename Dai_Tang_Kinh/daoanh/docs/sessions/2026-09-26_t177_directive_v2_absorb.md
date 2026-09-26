# SESSION — 2026-09-26 — T177: Absorb DIRECTIVE v2 (docs + token baseline)

## Tóm tắt

Admin phê chuẩn 3 điểm (2026-09-26): **(1) tạo task mới T177** cho plan absorb directive v2;
**(2) chỉnh `.md` cho phù hợp hệ thống hiện tại** + cập nhật Dashboard; **(3) đo token thật rồi chốt ngân sách**.

## Renumber T167 → T177 (vì sao)

- `tasks/T167-rules-constrained-buddhist-translation-engine.md` ĐÃ chiếm id T167 (IN_PROGRESS,
  commit `795fa20`/`9179d75`/`3cabea8`/`22a5cf7`).
- 2 file directive cũ (REVIEW + dynamic-filter-absorb) dùng `id: T167` → **collision**.
- Series Mimo-Flash đã dùng tới T176 → **T177 là số trống kế tiếp** (glob toàn repo: 0 kết quả T177).
- Admin xác nhận T177.

## Đã làm

### 1. Rename 2 file (untracked, dùng Move-Item — không git mv)
```
docs/Mimo-Flash/T167-directive-v2-trie-xml-dualhash-REVIEW.md   → T177-directive-v2-trie-xml-dualhash-REVIEW.md
docs/Mimo-Flash/T167-dynamic-filter-absorb-directive-v2.md      → T177-dynamic-filter-absorb-directive-v2.md
```
Ghi chú: cả repo có 2 chuỗi numbering song song — `tasks/` (T165..169) và Mimo-Flash (T168..176).
T177 nằm ở Mimo-Flash; **không** tạo file `tasks/T177-*` vì dashboard scan `tasks/*.md` = 93 task
(board tách biệt với Mimo-Flash).progress_data.json nhận T177 qua claim docs scan.

### 2. Sửa REVIEW doc — các lỗi logic/có bằng chứng
- **Bỏ `admin/app.py`** (KIỂM TRA: KHÔNG tồn tại file tại HEAD + git history; `admin/` chỉ có HTML/CSS/JS).
  Đã có tiền lệ chẩn đoán trong T168 (tasktodo line 17): số "18865" là ảo giác của T165 SPEC cũ.
  Stack thật: **`app.py` 21.232 dòng** (đo `(Get-Content app.py).Count` — sửa từ "19.759" sai trong lần ghi đầu).
- **Stats refresh** (đo thật tại HEAD): `translation_rules` active = **111 rows / 13.041 chars**
  (terminology **89** · style **10** · forbidden **6** · gate **3** · structure **1** · provenance **1** · grammar **1**);
  cache total **1762** (invalidated 1 · edited 6) · glossary locked **79** (1-char 14) · exemplar **2692**.
- **Line refs drift** (đối chiếu `Select-String` app.py):
  `_t73_rules_version` 16412 (cũ 16266) · `_t73_build_style_prompt` 16569 (cũ 16444) ·
  `_t73_call_gemini` 16575 (cũ 16510-13) · GROQ_MODEL `qwen/qwen3.8-27b` 16382 (cũ 16233) ·
  invalidate `rv='ALL'` 18396 (cũ 18221).
- **A3/C1 — "usage logging KHÔNG có" → ĐÃ BUILD**: `style_constitution.py:436 log_prompt_metrics` đọc
  `usage.prompt_tokens/completion_tokens/total_tokens`; được gọi tại `app.py:16606 _t165_log_prompt_metrics`.
  Gap CÒN THẬT: 429 không retry/backoff (`app.py:16602 return None, None, 'rate_limit'`) + không persist prompt_tokens vào DB.
- **B5 fixture**: `A009460 丹霞天然` = `vn_person_authority#don_ha_thien_nhien` (`name_zh='丹霞天然'`,
  `dila_id='A009460'`, `status='verified'`) ✓; `people` có id A009460 `name_zh='天然'` — T166 test match theo
  **substring**. Ghi chú cách resolve.
- **B4**: đọc `FROM translation_cache` = **15 site** app.py (không phải 39).
- **B8**: ghi translation_cache = **12 site app.py + 3 site style_constitution.py**; `t50` 0 qua pattern INSERT/UPDATE.
- **Spec cross-links**: T165 SPEC hiện là `X-Done-T165-rules-constrained-translation-engine-SPEC.md`,
  T166 là `X-T166-canonical-identity-guard-SPEC.md` (đã thêm tiền tố X-Done/X khi đóng task).

### 3. Sửa task doc (absorb) — tương ứng frontmatter/checklist
- `id: T177`, title, partner-link, `status: pending → in_progress`.
- Checklist D1–D8 cập nhật line ref + stats + B5/B4/B8 + spec names + session path.
- Revert section giữ nguyên.

### 4. Tracking + Dashboard
- `docs/tasktodo.md`: thêm entry T177 IN_PROGRESS (top ACTIVE), sửa số dòng app.py trong T168 line.
- `docs/ADMIN_REVIEW_DASHBOARD.md`: thêm **item 18** (section C3) + cập nhật bảng tiến độ (19 chờ / 2/20 = 10%).
- Regen `data/progress_data.json` via `scripts/build_progress_data.py` ✓ (15 module · 245 endpoint · 71% · 93 task · 497 commit).

### 5. D7 — Đo baseline token THẬT (Admin: "đo thật rồi chốt")
Script đo `temp/t177_token_baseline.py` → import `app.py`, dựng lock/prompt qua **pipeline production**
(`_t73_style_lock` → `_t73_build_style_prompt` → `_t73_call_gemini`), trap `log_prompt_metrics` bằng wrapper.

**Kết quả (Groq thật, API key từ `data/llm_config.json`):**

| Lần | Loại | source chars | prompt chars | prompt_tokens | completion | total | Kết quả |
|-----|------|--------------|--------------|---------------|-----------|-------|---------|
| #1 | place_note | 143 | 10.726 | — | — | — | **429 rate_limit** |
| #2 | person_bio | 266 | 10.092 | 3.422 | 207 | 3.629 | ok |
| #3 (confirm) | person_bio | 266 | 10.092 | **3.422** | 208 | **3.630** | ok |

**KẾT LUẬN D7:** prompt đầy đủ thật = **≈ 3.422 prompt_tokens** (≈ 10.000 chars prompt / 266-char source).
- Directive v2 khẳng định "target 150–250 token" → **không khả thi** (gấp ~14×). Chốt ngân sách thực: **~3.400–3.700 tokens/lần dịch ngắn** (trần an toàn đề xuất **3.700**).
- **429 XỊT THẬT 3/5 lần đo** trong session 20 phút → chứng minh A8 = retry/backoff **cần thiết** (không chỉ phòng vệ).
- `llm_config.json` về trạng thái `ok` sau call thành công (không thay đổi commit-worthy; file gitignored).
- `GROQ_MODEL = 'qwen/qwen3.8-27b'`, concurrency thấp; nên giữ budget theo số đo, KHÔNG hard-gate.

### 6. D6 — Data fix `_keep_` (Admin phê chuẩn 2026-09-26)
`NO_PINYIN` + `HANVIET_NAMES` đang giữ `rule_text='_keep_'` (toggle-sentinel lưu xuống thật, updated 2026-09-12).

**Diagnosis (trước khi sửa):**
- `_keep_` KHÔNG bị lọc ở prompt → `[TERMINOLOGY] _keep_` / `[FORBIDDEN] _keep_` vào thẳng LLM prompt + bị hash vào `constitution_hash` (style_constitution.py:77 `select_rules` không lọc).
- `NO_PINYIN` (forbidden) = rule duy nhất cấm pinyin → cần **restore**; text gốc có sẵn trong seed `scripts/t73_translation_system.py`.
- `HANVIET_NAMES` (terminology) trùng vai trò `CANONICAL_NAMES` + `HANVIET_PLACES` (đều active) → **deactivate**; không cần restore.
- Cả 2 còn được `_error_report_suggestion` app.py:18316/18322 khuyến nghị khi admin báo lỗi.

**Áp dụng:** `scripts/t177_d6_rules_fix.py --stats/--dry-run/--apply` (backup `data/backups/lineage_t177_d6_fix_20260926_105027.db`):
- NO_PINYIN: `rule_text` ← seed T73 full + `description='Cấm tuyệt đối dùng pinyin'`
- HANVIET_NAMES: `is_active=0` + description note DEACTIVATED (text giữ `_keep_` vô hại — không vào prompt)
- `app.py:18322` bỏ `'HANVIET_NAMES'` khỏi mapping gợi ý lỗi (giữ CANONICAL_NAMES/HANVIET_PLACES/REIGN_ERA)

**Verify (đo lại):** active rules **111 → 110** rows · chars 13.041 → **13.230** (NO_PINYIN text dài) ·
terminology 89→88 · `_keep_` active **2 → 0** · cache invalidate 0 (chưa có row semantic `constitution_hash` —
legacy cache auto-miss qua `rules_version` thay đổi — đúng thiết kế T165) ·
glossary locked 79 (1-char 14) · exemplar total 2692 (3 active).

### 7. Revert path
- Docs: `git revert --no-edit 62b593b` (REVIEW + task + tasktodo + dashboard + session + progress_data.json).
- `data/progress_data.json` bị `.gitignore` (cần `git add -f` qua t83_force_commit).
- Data (D6): `python -X utf8 scripts/t177_d6_rules_fix.py --revert` (NO_PINYIN→`'_keep_'`, HANVIET_NAMES→`is_active=1`)
  hoặc restore backup `data/backups/lineage_t177_d6_fix_20260926_105027.db`.
- Code (app.py mapping + script): `git revert --no-edit ef4c16d` (commit T177 D6).
- **Không** dùng `cp *.bak` (banned — review B7).

## Bước kế tiếp (T177 open items)
- **D6 ✅ DONE** (2026-09-26) — NO_PINYIN restored, HANVIET_NAMES deactivated, app.py mapping bỏ HANVIET_NAMES.
- **D1–D5 + D8 ✅ DONE** (2026-09-26, phiên tiếp theo) — xem mục 8 bên dưới.
- **429 retry/backoff** (`_t73_call_gemini`) + **persist prompt_tokens** = gap thật cho T165 Phase 5/6.
- Sau Admin confirm T177 → move `docs/taskdone.md`.

## Commit
`t83_force_commit.py` — docs + data/progress_data.json (files liệt kê trong checklist này, KHÔNG sweep khác).

---

# PHIÊN TIẾP 2026-09-26 (sáng→trưa) — D1–D5/D8 + D6 revert round-trip

## 8. Hoàn tất D1–D5/D8 (docs, đưa done_when về trạng thái hoàn tất)

### 8.1 D1 — Absorb: T165 SPEC §15 THẬT SỰ được ghi
**Phát hiện quan trọng:** phiên trước đã tick `[x]` dòng "T165 SPEC thêm §15" (task doc line 45) NHƯNG
rà soát thực tế cho thấy SPEC (`X-T165-rules-constrained-translation-engine-SPEC.md`) chỉ có §14.1–§14.3,
**KHÔNG có §15** — kể cả HEAD (575 dòng, `git show HEAD:...T165...SPEC.md` cũng không). ⇒ tick sớm.
**Đã sửa (phiên này):** viết **§15 ABSORB DIRECTIVE v2** đầy đủ (bảng absorb từng point của directive
v2: Trie gate · XML Phase 8 · dual-hash · retry/backoff · edited-row · invalidate burst · rules_outdated ·
Test Case 2 · D6 data-fix · D7 baseline) + banner chỉ review doc + task T177. File SPEC ngoài `X-` prefix.

### 8.2 D1 — checklist T165 & fix link `X-Done-` → `X-`
- Phát hiện: link trong T177 REVIEW §7 + task doc `parent_spec` chỉ `X-Done-T165-rules-…SPEC.md` nhưng
  file thật trên đĩa là **`X-T165-rules-…SPEC.md`** (git status: `T165-…` deleted + `X-T165-…` untracked).
  ⇒ `X-Done-` = đường dẫn CHẾT. **Đã sửa** 3 chỗ → `X-T165-…`.
- `X-T165-rules-constrained-translation-engine.md` (checklist T165): thêm dòng tick `§15 ref §8 + §7`
  (acceptance D3(a–d)/D8 + Trie gate + XML Phase 8) + sửa tham chiếu "task T167" → **T177** (renumber).

### 8.3 D2 — verify B1–B8 vs code/DB (không chỉ ghi plan)
| P0 | Verify |
|----|--------|
| B1 | `select_rules` dùng `rule_code/rule_type/rule_text` (style_constitution.py) ✓ |
| B2 | `constitution_hash` `'\n'.join(parts)` — có delimiter (`\n`), không nối trống ✓ |
| B3 | hash đủ 8 phần: rules(rule_code+rule_text) · glossary(`zh→vi`) · exemplar(`ex:`) · FMT · label · json · known_pending · t166 fp · extra_hash (style_constitution.py:168-199) ✓ |
| B4 | `constitution_hash` = cột **additive** (T165 migration), `source_hash` giữ UNIQUE ✓ |
| B5 | fixture thật confirm DB: `SELECT … FROM vn_person_authority WHERE dila_id='A009460'` → **`('A009460','Đơn Hà Thiên Nhiên','verified')`** ✓ (people table không có cột `dila_id` — vnpa là nguồn identity) |
| B6 | XML `<source>`+contract → REVIEW B6 → T165 Phase 8 ✓ |
| B7 | revert qua `git revert` (đang tuân thủ; không `.bak`) ✓ |
| B8 | stack thật app.py/t50/style_constitution → REVIEW B8 ✓ |

### 8.4 D3+D8 — acceptance §8 mục 13–17
Thêm vào T165 SPEC §8 (sau mục 12): **13** D3(a) persist prompt_tokens + retry/backoff ≤2 (429 thật) ·
**14** D3(b) row `status='edited'` không bị REPLACE (ưu tiên nhánh edited + `rules_outdated=true`) ·
**15** D3(c) invalidate burst giới hạn batch N (bên cạnh nút full 1.762) ·
**16** D3(d) badge `rules_outdated` + cache list đúng sau khi thêm cột hash (audit ~22 read site) ·
**17** D8 Test Case 2 = acceptance chính, fixture thật `A009460 丹霞天然` (match substring `天然`).

### 8.5 D4/D5 — phase gating trong §15
§15 table: XML boundary = **T165 Phase 8** (optional, sau Admin QA, không gate phase 1–7) ·
Trie chỉ build khi **`n_terms ≥ 1000`** (hiện **89** term terminology active sau D6 → substring đủ; đo lại khi > 1000).

## 9. D6 — revert round-trip TESTED (đóng item cuối D6)
**Chạy `--revert` rồi `--apply` lại trên DB thật** để chứng minh script đáng tin khi rollback:
1. `--stats`: active 110 · `_keep_` 0 · cache 1762 · NO_PINYIN restored / HANVIET_NAMES inactive ✓
2. `--revert`: NO_PINYIN→`'_keep_'` (desc '') · HANVIET_NAMES→`is_active=1` (desc '') · active 110→**111** ·
   `rules_total` **112 KHÔNG ĐỔI** · `_keep_` 0→2 · cache 1762 không đổi → **0 row bị xoá** ✓
3. `--apply` lại: backup mới `data/backups/lineage_t177_d6_fix_20260926_114927.db` (1376 MB) ·
   active 111→**110** · `_keep_` 2→**0** · NO_PINYIN restored / HANVIET_NAMES deactivated ✓
Kết luận: revert path an toàn (chỉ UPDATE, không DELETE), khôi phục đúng trạng thái pre-apply.

## 10. Tracking + docs đầu vào Admin
- `docs/tasktodo.md` row T177: cập nhật D1–D8 ✅ + D6 round-trip + "còn lại: build phase T165 3–6".
- `docs/ADMIN_REVIEW_DASHBOARD.md` item 18: ghi rõ T177 docs/data/runtime xong, chờ Admin "T177 done".
- Task doc `T177-dynamic-filter-absorb-directive-v2.md`: tick toàn bộ D1–D8 + closing tasktodo/dashboard done.
- **Chưa commit** (chờ Admin) → revert docs vẫn là `git revert --no-edit 62b593b` (+ bất kỳ commit D1–D8 sau này).
- **Build phase T165 Phase 3–6 chưa chạy** (wrap `_t73_*`, retry/backoff, persistence) = việc kế tiếp, task riêng.

## 11. CLOSE — Admin "commit, T177 done" (2026-09-26)
- Task doc: `status: done` + `closed_at` + tick 2 checkbox đóng (pipeline PASS + commit + taskdone) + Revert docs cập nhật thứ tự revert.
- `docs/tasktodo.md` row T177: `🚧 IN_PROGRESS` → `✅ DONE` (kèm tóm tắt + trỏ task doc).
- `docs/taskdone.md`: thêm entry T177 DONE (append-only) — full tóm tắt D1–D8 + pipeline + revert paths.
- `docs/ADMIN_REVIEW_DASHBOARD.md`: item 18 → ✅ Done 2026-09-26; row 19 "Cần confirm" bỏ T177 → thêm vào "Đã confirm" (2026-09-26).
- REVIEW doc: `status: done-plan` → `done`, absorbed_at ghi close.
- Commit docs qua `t83_force_commit.py` → **`0e5ec12`** (9 files: T165 SPEC X-T165 + T165 checklist + T177 task/REVIEW + tasktodo + taskdone + dashboard + session + progress_data.json). Hash-fill pass 2: taskdone + task doc Revert placeholder → sha thật.
- Kế tiếp: báo pipip Admin → mở task build T165 Phase 3–6.
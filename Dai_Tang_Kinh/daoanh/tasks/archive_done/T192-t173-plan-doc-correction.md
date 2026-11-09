---
id: T192
title: "T192 — T173 Plan-Doc Correction"
module: Docs / Task Governance
priority: high
status: done
owner: mimo-flash
created: 2026-09-29
updated: 2026-10-02
commit: "TBD"
revert: "git revert --no-edit <sha>"
---
# T192 — T173 Plan-Doc Correction

**Trạng thái:** DONE (docs-only — 0 code / 0 DB)
**Ngày:** 2026-09-29
**Kiểu:** docs (tương tự T189/T190/T191)
**Admin phê duyệt:** "Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done."

## Mục tiêu

Admin yêu cầu kiểm tra `docs/Mimo-Flash/T173-person-lineage-tab-merge.md` (ANALYZE_ONLY, verdict "đúng ~85% — 7 điểm cần bổ sung") có logic đúng với code thật hay không; nếu sai → chỉ ra và đề xuất sửa. Kết quả verified:

## Verdict độc lập

**Logic cốt lõi T173 ĐÚNG (~90%)**. 5 mục cần sửa/bổ sung trong doc:

1. **Line refs lỗi thời toàn bộ** (file root `places.html`: 10.193 → **10.268 dòng**, drift +48..+106):
   | Doc cũ | Thật (2026-09-29) |
   |---|---|
   | tabs `:240-241` | `:240-241` ✓ (khớp) |
   | Pháp Mạch panel `:5224` | `:5272` |
   | `ancestorBar` `:5479` | `:5532/:5541` |
   | `lineage-tree?up=2&down=2` `:5167,:5414` | `:5215,:5467` (param ĐÚNG; `_lineageState` `:5205`, expand `include_single=1` `:5503`) |
   | `ancestor-spine` `:5121` | `:5169` |
   | `renderPersonsTab` `:8597` | `:8671` (persons clickable `:8697`; wikidata KHÔNG `:8667-8668,:8678`) |
   | URLSearchParams `:9990,:10163` | `:10064,:10237,:10241,:10252` |
   | truyền pháp ≠ co-mention `:4175` | `:4201-4234` (`evSrc` co_mention `:4216`) |
   | edge tooltip `:5914` | `:5988-5992` |
   | `dila:teacher_of` `:7243,:7250` | `:7315-7317` (DILA L2) vs Zen L2 `:7324` |
   | auto-click lineage `:2365-2367` | `:2367` click + `_tabLoaded` `:2368` (selectPerson def `:2287`) |
   | `_linRelationCard` `:6081`; DILA L2 `:6291,:6401,:6266` | `:6187`; reuse `:6335`, gọi `:6348,:6469` |
   | wd không DILA `:8593-8595` | `:8667-8668,:8678` |
   | entry points `:3813,:8391,:8616` | full list (12 site, mục dưới) |

2. **"3 node" tự mâu thuẫn**: §3 target_ia ghi "đúng 3 node" vs acceptance "tối đa 3 node". `up=1&down=1` KHÔNG bao giờ đảm bảo đúng 3 node khi person có nhiều pháp tử. → chốt nhất quán **"TỐI ĐA 3 node"** (1 thầy + 1 mình + 1 pháp tử; nhiều pháp tử → collapse "+N") ở cả target_ia + expected_ui + acceptance.

3. **Thiếu Precondition T187/T188 `is_primary`** (doc 09-25 đi trước code):
   - **HEAD app.py ĐÃ commit**: `api_monk_lineage_tree` `:5923`, `_t158_neighbors_consensus` `:5610` — dùng `ttl_asserted`+`agreeing_source_count`+`default_visible`, **CHƯA có** `lineage_primary_teacher`/`is_primary`, **CHƯA lọc** `early_study`.
   - **Worktree app.py WIP (CHƯA commit)**: endpoint dời `:6070`, consensus `:5747` — có T187 `LEFT JOIN lineage_primary_teacher`, `ORDER BY is_primary DESC...` `:5752`, BFS lọc `is_primary=-1` `:6225-6228`.
   → Rule "preview chỉ dùng truyền pháp hợp lệ" đúng nghĩa chặt chỉ sau khi T187/T188 land; nếu chưa → render theo phân biệt UI hiện tại + ghi nhãn.

4. **`_goTab`**: chỉ usage tại `:467,:7365,:7372`; định nghĩa KHÔNG nằm trong places.html (shared JS) → ghi rõ để agent không tìm nhầm.

5. **Entry points `selectPerson(` đầy đủ (12 site)** — `:1586, 1777, 2820, 2841, 3861, 4558, 8465, 8697, 8733, 8751, 8772, 10230` (+ comment `:5250`), `_tabLoaded` reset `:1109,:1837,:2290`.

## Files sửa

- `docs/Mimo-Flash/T173-person-lineage-tab-merge.md` — refresh refs §1+§3, Precondition T187/T188, tối đa 3 node, entry points, frontmatter `amended_by: T192`.
- `tasks/T192-t173-plan-doc-correction.md` — task này.
- `docs/sessions/2026-09-29_t192-t173-plan-doc-correction.md` — session log.
- `docs/tasktodo.md` — row DONE + revert sha.
- `docs/ROLLBACK.md` — row revert (2-pass hash-fill).
- Dashboard regen (nếu có script).

## Verify

- [x] `npm run guard` PASS
- [x] `npm run lint` PASS
- [x] `npm run test` PASS
- [x] Commit 2-pass hash-fill (`e6459ccc9ab6ae48933550bbcacbb023a70c78cd`/`e6459ccc9ab6ae48933550bbcacbb023a70c78cd`)
- [ ] pipip best-effort (offline: curl.exe exit=3)

## Revert

```bash
git revert --no-edit e6459ccc9ab6ae48933550bbcacbb023a70c78cd   # trả về trước T192 (docs-only, 0 code/0 DB)
```
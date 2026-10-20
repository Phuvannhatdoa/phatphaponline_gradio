# Session 2026-09-29 · T192-t173-plan-doc-correction

**Agent:** claudecode · **Trạng thái:** DONE (docs-only, 0 code/0 DB) · **HEAD tại thời điểm build:** `65e9324` (T172 commit 2-pass hash-fill)

## Mục tiêu

Admin: "phê chuẩn đề xuất này... tạo task mới với name Txx cho kế hoạch chi tiết... Update lên /docs/ và các .md files tương ứng, cập nhật vào Dashboard để admin xem. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done."

Phê duyệt kế hoạch T192 — sửa doc T173 `docs/Mimo-Flash/T173-person-lineage-tab-merge.md` theo 5 phát hiện verify độc lập (đã bàn luận trong session trước).

## Verify độc lập (read-only, nguồn thật)

Đối chiếu toàn bộ claim T173 với code thật:

| Doc T173 cũ | Thật (2026-09-29, places.html root 10.268 dòng) | Kết luận |
|---|---|---|
| tabs `:240-241` | `:240-241` | ✓ khớp |
| Pháp Mạch panel `:5224` | `:5272` | line drift |
| ancestorBar `:5479` | `:5532/:5541` | line drift |
| lineage-tree up=2&down=2 `:5167,:5414` | `:5215,:5467` (+`_lineageState` `:5205`, expand include_single=1 `:5503`) | **param ĐÚNG** |
| ancestor-spine `:5121` | `:5169` | line drift |
| renderPersonsTab `:8597` | `:8671` (persons clickable `:8697`; wikidata KHÔNG `:8667-8668,:8678`) | ✓ semantics |
| URLSearchParams `:9990,:10163` | `:10064,:10237,:10241,:10252` | line drift |
| `_goTab` `:467` | usage `:467,:7365,:7372`; **def NGOÀI file** | chú thích |
| truyền pháp ≠ co-mention `:4175` | `:4201-4234` (evSrc co_mention `:4216`) | line drift |
| edge tooltip `:5914` | `:5988-5992` | line drift |
| dila:teacher_of `:7243,:7250` | DILA L2 `:7315-7317` vs Zen L2 `:7324` | line drift |
| auto-click `:2365-2367` | `:2367` click + `_tabLoaded` `:2368` (selectPerson def `:2287`) | ✓ semantics |
| _linRelationCard `:6081`; DILA L2 `:6291,:6401,:6266` | `:6187`; reuse `:6335`, gọi `:6348,:6469` | line drift |
| wd không DILA `:8593-8595` | `:8667-8668,:8678` | line drift |
| entry points `:3813,:8391,:8616` | 12 site: `:1586,1777,2820,2841,3861,4558,8465,8697,8733,8751,8772,10230` (+comment `:5250`) | bổ sung |
| app.py preview API | HEAD `api_monk_lineage_tree` `app.py:5923` (up/down + include_single `:5928-5931`); **CHƯA có ** is_primary/T187 | Precondition |

**5 fix áp vào T173 doc:**
1. Refresh toàn bộ line refs §1 + §3 theo số thật 2026-09-29.
2. Chốt nhất quán **"TỐI ĐA 3 node"** (1 thầy + 1 mình + 1 pháp tử; nhiều pháp tử → collapse "+N") — bỏ "đúng 3 node" tự mâu thuẫn với acceptance.
3. Thêm **Precondition T187/T188 `is_primary`**: HEAD app.py đã commit endpoint lineage-tree `:5923` (chưa lọc early_study); WIP worktree (endpoint `:6070`, consensus `:5747`) có `LEFT JOIN lineage_primary_teacher` + `ORDER BY is_primary DESC` + BFS filter `is_primary=-1` `:6225-6228` → preview filter `is_primary=1` chỉ đúng sau khi T187/T188 land.
4. Chú thích `_goTab` định nghĩa ngoài file (shared JS).
5. Bổ sung entry-point đầy đủ + `_tabLoaded` reset points `:1109,:1837,:2290`.

## Thay đổi

1. **T173 doc** `docs/Mimo-Flash/T173-person-lineage-tab-merge.md`: refresh refs §1 bảng verified + §2 7 điểm + §3 prompt block (places.html:NNNN theo số thật); frontmatter `updated: 2026-09-29` + `amended_by: T192`; banner amend; thêm Precondition T187/T188; sửa "đúng 3 node"→"tối đa 3 node"; entry-point đầy đủ; _goTab chú thích. §5 Revert ghi rõ revert T192.
2. **Task** `tasks/T192-t173-plan-doc-correction.md` (mới) — task detail + evidence.
3. **Session** `docs/sessions/2026-09-29_t192-t173-plan-doc-correction.md` (mới — file này).
4. **tasktodo** `docs/tasktodo.md`: row T192 DONE (đầu ACTIVE/DONE section) + revert sha.
5. **ROLLBACK** `docs/ROLLBACK.md`: row T192 (2-pass hash-fill `e6459ccc9ab6ae48933550bbcacbb023a70c78cd`).
6. **Dashboard**: `python -X utf8 scripts/build_progress_data.py` → `data/progress_data.json` regen + commit.

## Commit (hunk-granular, temp index — không đụng WIP agent khác)

- Con trỏ HEAD đang bẩn (tasktodo/ROLLBACK MM, SPEC/pointer X- rename, session cũ staging D) bởi agent song song → commit T192 chỉ đưa blob: T173 doc + task T192 + session T192 + tasktodo row + ROLLBACK row + progress_data.json (bare path HEAD, LF-normalized).
- 2-pass hash-fill như T191/T172: pass-1 `e6459ccc9ab6ae48933550bbcacbb023a70c78cd`/`e6459ccc9ab6ae48933550bbcacbb023a70c78cd`, pass-2 hash thật.

## Verify

- [x] `npm run guard` PASS
- [x] `npm run lint` PASS
- [x] `npm run test` PASS
- [x] Commit pass-1 + pass-2; `git log` top 2 = T192 pass-2 → pass-1 → `65e9324`
- [ ] pipip best-effort (curl.exe exit=3 offline)

## Revert

```bash
git revert --no-edit e6459ccc9ab6ae48933550bbcacbb023a70c78cd   # docs-only, 0 code/0 DB
```
# 2026-08-29 — T57: Glossary Đa Ngôn — Import Yokoyama + Lookup API + Popup UI + Đồng Môn Derived ✅

## Mô tả ngắn task

User yêu cầu logic-check đề xuất dùng `mbingenheimer/buddhist_studies_glossaries` (cho
Chinese→Vietnamese/English, Sanskrit, Pali, Tibetan, NER, autocomplete, dictionary) và
Marcus/FoJin relational data thành `A —teacher_of/student_of/colleague_of/lineage_of→ B`.
Nếu phi logic → chỉ ra lỗi + đề xuất giải pháp.

## Logic-check (đã xác nhận bằng dữ liệu thật)

- **Repo glossaries thật** (GitHub MB, CC0, GoldenDict/StarDict) gồm:
  - DILA PersAuthority (~47K tăng ni, tiếng Trung) — NER tăng ni
  - DPPN (Malalasekera, ~1,360 tên Pali từ SuttaCentral)
  - Yokoyama-Hirosawa 1996 (Sanskrit–Tibetan–Chinese, index Yogācārabhūmi)
  - Japanese-Multilingual NED (~740K tên tiếng Nhật)
- **Marcus** (`data/lineage.db`): `marcus_networks` chỉ có **1 loại** `da:isTeacherOf`
  (11,169 DISTINCT edges). Không có colleague_of/lineage_of là quan hệ riêng.
- Quyết định user: chỉ đọc/đánh dấu DPPN bản Việt (đã trong `lexicon` 22 từ điển PG VN, 166K rows);
  gộp vào T57; import Yokoyama + plant bản Việt hóa; bỏ DILA PersAuthority & Japanese NED;
  cần quan hệ đồng môn (nghiên cứu tông môn).

## Build

### 1. Import Yokoyama → bảng mới `glossary_term` (additive) — T57/T62
- Script `scripts/import_glossary_yokoyama.py` (generator zero-RAM; tự tải `.gls` từ repo MB
  `chinese/yokoyama-hirosawa1996.zip` nếu chưa có local tại `data/glossary/` — data git-ignored).
- Bảng `glossary_term(id, term, language, definition, full_text, source_id, created_at)`,
  UNIQUE(term, language). Source `dataset_sources.MB_GLOSSARY` (id=6) cập nhật origin_url + attribution (CC0).
- Kết quả: **248,095 rows** = san 17,171 / zho 67,461 / bod 65,195 / bo-Latn 98,268.
- Verify: `無畏`→zho, `a-bhaya`→san+bo-Latn, full_text đa ngôn đầy đủ.

### 2. Glossary lookup API — T57a (app.py)
- Route `GET /daoanh/api/glossary?term=` tra theo thứ tự: `lexicon` (bản Việt 22 từ điển,
  khớp `term` → fallback `normalized` qua `normalize_text`), `glossary_term` (Yokoyama),
  `term_glossaries` (Marcus). Mỗi kết quả ghi rõ `source_label`/`source_key`.
- Helper `_ensure_glossary_term_table(conn)` idempotent.
- Verify: `Bồ Tát` → lexicon 5 matches Việt; `a-bhaya` → Yokoyama san/bo-Latn; `無畏` → Yokoyama zho + Marcus.

### 3. Popup UI — T57b/c (places.html)
- `openGlossaryPopup(term)` + `bindGlossarySpans(container)` — click phần tử `.da-glossary`
  → popup modal tra cứu đa ngôn, hiển thị nguồn rõ ràng (mỗi match có source_label).

### 4. Quan hệ ĐỒNG MÔN (colleague_of) DERIVED — app.py + places.html
- `api_monk_graph` thêm self-join `marcus_networks`: student khác cùng teacher của node đang xem.
- Edge `{label:"đồng môn", derived:true, shared_teacher_label}`.
- UI: nét đứt màu xanh + nhãn `đồng môn (suy ra)` + tooltip giải thích "suy ra từ Marcus isTeacherOf".
- Verify: `A000005` (Giám Đường Nhất), thầy 幻敏 → 6 đồng môn đúng (A003872, A003805, A037635, A037637, A037636, A000638).

## Tester / Verify

- `npm run lint` ✅ / `npm run test` ✅ / `npm run e2e` (static) ✅.
- `e2e:runtime` (Playwright): 2 tests PASSED khi chạy với `--output` tạm. Lỗi EPERM
  `test-results/.last-run.json` khi chạy mặc định là do Playwright worker cũ giữ handle
  (lỗi môi trường, KHÔNG phải lỗi code).
- py_compile app.py ✅; test client verify cả 3 feature.

## Trạng thái subtasks

| Phần | Trạng thái |
|------|-----------|
| Import Yokoyama (248K rows) | ✅ DONE |
| Glossary lookup API `/api/glossary` | ✅ DONE |
| Popup UI (places.html) | ✅ DONE (click `.da-glossary`; highlight chủ động chờ T52c content) |
| Đồng môn derived (graph + UI) | ✅ DONE |
| Bản Việt hóa Yokoyama | ⏸ PLANT — chưa có, cần admin |

## Việc tiếp theo

1. T52c UI side-by-side tab Giáo Lý (dùng glossary này + compare) — renderGiaolyTab vẫn stub.
2. Tích hợp highlight glossary chủ động vào kinh văn (CBETA preview).
3. Bản Việt hóa Yokoyama thuật ngữ Duy Thức (admin cung cấp).

## Revert

Atomic commit phiên này: `feat(T57): Glossary Da Ngon - import Yokoyama (248K) + glossary lookup
API + popup UI + dong mon derived + docs`. Revert: `git revert <hash>`.

Lưu ý: backup DB trước import tại `%TEMP%\opencode\lineage_backup_20260829_193510.db` (DB không git-track).

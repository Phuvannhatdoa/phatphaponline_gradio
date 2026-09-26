# Audit / Bug Fix Report — unify_dila_lineage_relation_card_format

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `people` table (`id,name_vi,name_zh`) + raw DILA XML `listRelation` (parsed vào RAM cache `_T148_DILA_EXTRA` tại startup, `app.py`) + `lineage_edge_assertions` (DILA L2, source_code='DILA') |
| API endpoint | `GET /daoanh/api/person/<id>/dila_full` (raw XML listRelation — bibl/ref_url/name/name_vi) và `GET /daoanh/api/person/<id>/dila-axis` (L2-verified teacher/student theo `lineage_edge_assertions`) |
| Resolver / logic | `app.py:17334` `api_person_dila_full` · `app.py:17398` `api_person_dila_axis` |
| Component / renderer | `daoanh/places.html` — `_loadDilaExtra`/`_renderDilaExtra` (dòng ~6006-6165, section "THẦY"/"HỌC TRÒ") và `_loadDilaAxis`/`_renderDilaAxis` (dòng ~6207-6296, section "THẦY THEO DILA"/"ĐỆ TỬ THEO DILA") |
| Schema contract | Không đổi — 0 thay đổi API/DB, chỉ hợp nhất renderer phía client |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer (UI component) — 2 hệ card khác nhau cho cùng 1 loại dữ liệu (quan hệ thầy/trò).
- **Nguyên nhân chính xác:** `_renderDilaExtra` (nguồn: raw DILA XML `listRelation`, hiển thị "THẦY"/"HỌC TRÒ" kèm evidence) dùng CSS/markup riêng (`border-radius:6px;background:rgba(255,255,255,.03)` + link `admin/person.html`), trong khi `_renderDilaAxis` (nguồn: `lineage_edge_assertions` L2, hiển thị "THẦY THEO DILA"/"ĐỆ TỬ THEO DILA") dùng 1 template card khác (`chip()`, background `var(--da-panel)`, click `centerLineageOn`). Hai template độc lập, không share code → lệch visual dù cùng biểu diễn 1 khái niệm (quan hệ thầy/trò của 1 tăng nhân).
- **Phát hiện quan trọng khi audit (lệch dữ liệu test-case so với prompt):** ID `A010470` trong prompt gốc **không phải** "Đơn Hà Thiên Nhiên/天然" — verify trực tiếp DB: `A010470.name_zh='希搡'` (auto-transliterate `name_vi='Hơi Táng'`), còn người tên thật `Đơn/Đan Hà Thiên Nhiên (天然)` là **`A009460`** (`people.name_vi='Đan Hà Thiên Nhiên'`, `name_zh='天然'`). Case "self-reference" mô tả trong prompt (mục #2, 希搡=A010470) thực chất là **1 trong 3 thầy thật của A009460** — không phải self-loop. Toàn bộ test case (3 thầy A010291/A010470/A004218 + 7 đệ tử A025957/A020035/A025958/A020038/A010616/A020036/A020037) đã verify khớp 100% khi target đúng là **A009460** (curl `/daoanh/api/person/A009460/dila_full` + `/dila-axis`). Do đó code **giữ nguyên self-reference guard** (defensive, generic theo `r.person_id === d.person_id`) nhưng test thực tế xác nhận nó không trigger sai — vì đây không phải self-loop thật.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data/API | Không đổi (0 ALTER, 0 route mới) | Không đổi |
| Render THẦY/HỌC TRÒ | `_relGroup()` cục bộ trong `_renderDilaExtra`, mỗi item build HTML riêng (border rgba, link `admin/person.html`, bibl thô không tách evidence/citation) | Gọi hàm dùng chung `_linRelationCard(person, options)` — **cùng CSS/markup** với card "THẦY THEO DILA"/"ĐỆ TỬ THEO DILA"; thêm `mapping_verified` (✓L2, cross-check qua `/dila-axis`), `evidence_quote`/`source_locator` (tách từ `bibl` bằng `_linRelParseBibl` — tái dùng parser đã có `_t128ParseRef`, không phát minh heuristic mới), `is_self_reference` (⚠ cảnh báo, khoá link nếu trùng DILA ID) |
| Render THẦY THEO DILA / ĐỆ TỬ THEO DILA | `chip()` cục bộ trong `_renderDilaAxis` | `chip()` nay là wrapper mỏng gọi `_linRelationCard` — **output HTML giữ nguyên y hệt** khi không có evidence/self-ref (đã verify bằng browser, không redesign) |

## 4. Files changed

- `daoanh/places.html`:
  - Thêm 2 hàm dùng chung trước `_loadDilaExtra` (~dòng 6006): `_linRelParseBibl(bibl)` (tách Chứng cứ/Nguồn từ `bibl`, tái dùng `_t128ParseRef`) và `_linRelationCard(person, options)` (1 template card duy nhất cho quan hệ thầy/trò, có `mapping_verified`/`evidence_quote`/`source_locator`/`is_self_reference`).
  - `_loadDilaExtra`: thêm fetch `/dila-axis` song song (Promise.all) để lấy `l2TeacherIds`/`l2StudentIds` — dùng cross-check gắn badge ✓L2 cho card evidence chi tiết.
  - `_renderDilaExtra`: nhận thêm tham số `l2TeacherIds`/`l2StudentIds`; `_relGroup()` refactor để build mỗi item bằng `_linRelationCard` (thay vì HTML riêng), truyền `evidence_quote`/`source_locator` (qua `_linRelParseBibl(r.bibl)`) và `is_self_reference: r.person_id === d.person_id`.
  - `_renderDilaAxis`/`chip()`: refactor gọi `_linRelationCard` thay vì tự build HTML — giữ nguyên visual, thêm self-reference guard nhất quán.

## 5. Migration / import / dry-run / rollback (nếu chạm DB)

- Không chạm DB/API — chỉ sửa `places.html` (client renderer). Không cần migration/backup DB.
- Backup file trước khi sửa: `daoanh/docs/sessions/2026-09-22/places.html.bak-fix-person-name-display` (đã có sẵn từ đầu session, giữ nguyên).
- Revert: `git checkout -- daoanh/places.html` (chưa commit) hoặc `git revert <hash>` sau khi user yêu cầu commit.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu (target đúng theo audit) | `selectPerson('A009460')` → tab Truyền Thừa → inspector | 3 card THẦY riêng biệt (Thạch Đầu Hy Thiên/希搡 A010470/Đạo Khâm), 7 card HỌC TRÒ riêng biệt, mỗi card có tên+hán+DILA ID+✓L2+Chứng cứ (nếu có)+Nguồn, cùng CSS với "THẦY THEO DILA (3)"/"ĐỆ TỬ THEO DILA (7)" | Xác nhận qua `get_page_text` + screenshot: 3 card THẦY (item #2 "希搡…Chứng cứ: 後於嶽寺希律師受其戒法。…Nguồn: T50n2061_p0773b21" khớp đúng prompt), 7 card HỌC TRÒ, visual card giống hệt section DILA L2 bên dưới | ✅ |
| Self-reference guard (đảo chiều — target = A010470) | `selectPerson('A010470')` → tab Truyền Thừa | Không có THẦY (data thật A010470 không có teacher relation) · HỌC TRÒ = 2 card (A009460, A011324) đều KHÁC DILA ID với A010470 → không self-ref, card bình thường có link | 2 card HỌC TRÒ hiển thị đúng, ✓L2 cross-check đúng chiều, không có card sai self-ref | ✅ |
| Fallback self-reference (unit-test hàm) | Gọi trực tiếp `_linRelationCard({id:'A010470',...}, {is_self_reference:true,...})` trong console | Card viền cam, tên KHÔNG có onclick/link, dòng "⚠ Cần đối chiếu định danh…", vẫn giữ Chứng cứ/Nguồn | HTML trả về đúng: border `#f59e0b`, `<span style="font-weight:700;color:var(--da-text)">` (không `onclick`/`cursor:pointer`), có dòng cảnh báo, evidence/citation còn nguyên | ✅ |
| Regression — section THẦY THEO DILA/ĐỆ TỬ THEO DILA không bị redesign | So sánh output trước/sau khi không có evidence/self-ref | HTML giữ nguyên cấu trúc (`background:var(--da-panel)`, border chuẩn, ✓L2, `centerLineageOn`) | Xác nhận qua screenshot + `get_page_text` — "THẦY THEO DILA (3)"/"ĐỆ TỬ THEO DILA (7)" hiển thị đúng như cũ | ✅ |
| Regression — chuyển tab Địa điểm | `selectItem('PL000000023255')` sau khi đã xem lineage person | Không lỗi console, panel địa điểm load bình thường | 0 console error | ✅ |
| Empty/no relations | Person không có `d.relations` (has_extra nhưng relations rỗng) | Không render section THẦY/HỌC TRÒ (giữ guard `if (d.relations && d.relations.length)`) | Guard không đổi — hành vi giữ nguyên | ✅ (code review, guard không bị sửa) |

## 7. Limitation / data gap còn lại

- Prompt gốc ghi sai `dila_id` cho "Đơn Hà Thiên Nhiên" (đưa A010470 thay vì A009460) — đã audit và verify lại bằng DB thật + API thật trước khi implement, tránh áp fix sai chỗ. Đề nghị người giao task xác nhận lại ID khi viết task tương tự sau này.
- Card "Nguồn" cho các item không theo định dạng CBETA sigla (vd `（望月‧卷六‧附錄：046）`) không tách được evidence_quote (vì không có pattern locator để `_linRelParseBibl` nhận diện) — hiển thị nguyên văn dưới nhãn "Nguồn:" thay vì "Chứng cứ:". Đây là hành vi **đúng theo rule data-integrity** (không suy đoán/tách chuỗi khi không chắc chắn ranh giới quote/citation), không phải bug.
- Chưa thêm test tự động (không có JS unit-test harness cho `places.html` trong repo); verify bằng browser thật + gọi hàm trực tiếp qua console (không phải giả lập DOM/data).

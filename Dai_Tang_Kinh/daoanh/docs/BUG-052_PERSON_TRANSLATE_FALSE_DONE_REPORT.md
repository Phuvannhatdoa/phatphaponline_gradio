# Audit / Bug Fix Report — BUG-052 (Tab "Dịch ID Person" đánh DONE sai)

> Bug verify: BUG-052: Tab "Dịch ID Person" trong translation_progress.html#t50
> đánh dấu DONE sau một lần click, trong khi chưa dịch hết các trường có Hán văn.
> Route/case: `http://127.0.0.1:8080/daoanh/admin/translation_progress.html` → tab
> "Dịch ID Person" → ID `A000004`, kiểm chứng tại
> `http://127.0.0.1:8080/daoanh/admin/person.html?id=A000004`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `people.bio`, `people.bio_vi`, `ttl_v2_source_records.raw_text` (DILA XML, đọc qua `_t148_get_extra`), `translation_cache` (source_type `person_bio` và `dila_card`) |
| API endpoint (cũ, bị tab gọi sai) | `POST /daoanh/api/person/<id>/translate` — chỉ dịch `people.bio` → `people.bio_vi` |
| API endpoint (đúng, đáng lẽ phải gọi) | `GET/POST /daoanh/api/person/<id>/dila_translate` — dịch toàn bộ DILA card (≈14 trường) |
| Resolver / logic | `app.py:21789` (`api_person_translate`, bio-only) · `app.py:22177+` (`api_person_dila_translate`, full card) |
| Frontend | `admin/translation_progress.html` — `psTranslateOne()`, `psRenderRows()`, `psProcessNext()` (tab "Dịch ID Person") |
| List/stats endpoint | `GET /daoanh/api/dila/persons` (`app.py` `api_dila_persons_search`) · `GET /daoanh/api/dila/persons/stats` |

## 2. Root cause (đã xác minh) — **2 lỗi độc lập, cả 2 đều xác nhận bằng dữ liệu/code thật**

- **Lớp gây lỗi:** mapping + API contract (frontend gọi sai endpoint) **và** resolver/data
  (backend xây sai field, nên 1 endpoint khác dù được gọi cũng không thể dịch đủ).

### Lỗi A — Frontend gọi nhầm endpoint hẹp, rồi tự suy DONE từ `ok:true`

`admin/translation_progress.html` hàm `psTranslateOne(personId)` (trước fix, dòng
~1428) gọi `POST /daoanh/api/person/<id>/translate`. Route này (`app.py:21789`)
**chỉ** đọc `people.bio`, dịch, rồi `UPDATE people SET bio_vi=...` — không đụng tới
bất kỳ trường nào khác. Ngay khi `d.ok === true`, frontend set
`btn.textContent = '✓ Xong'; btn.disabled = true;` — coi như xong hẳn.

Nhưng `person.html` (trang hiển thị, dòng 341, 311-320, 429-450) lấy **Tiểu sử vắn
tắt / Ghi chú năm mất / Kinh trong Đại Tạng / Trích dẫn CBETA** từ một object
`vi_` hoàn toàn khác — kết quả của `GET /daoanh/api/person/<id>/dila_translate`
(cache `translation_cache` nguồn `dila_card`), **không đọc `people.bio_vi` ở bất kỳ
đâu**. Nói cách khác: cú click "Dịch ngay" (bio-only) và nội dung thực sự hiển thị
trên `person.html` là **hai pipeline tách biệt, chưa từng được nối**.

**Bằng chứng thật (browser, A000004):** list "Dịch ID Person" hiện A000004 là
`✓ Đã lưu` / `✓ Đã có bio_vi` (coi như DONE). Mở `person.html?id=A000004` cùng lúc:
**TẤT CẢ 9 trường có Hán văn đều "(chưa dịch)"** — Tên khác (DILA), Ghi chú năm
mất, Trích dẫn nguồn gốc, Triều đại, Nghề nghiệp, Nơi xuất xứ, Tiểu sử vắn tắt,
Kinh trong Đại Tạng, Trích dẫn CBETA (4). Ảnh chụp/`get_page_text` thật lúc audit,
không suy diễn.

### Lỗi B — Backend `dila_translate` tự làm mất khả năng dịch 2 trường, mọi lúc

Dù tab CÓ gọi đúng `/dila_translate`, kết quả vẫn không thể đủ 100%: hàm
`api_person_dila_translate` (trước fix) xây `source_data` để đưa vào prompt AI
nhưng **THIẾU 2 khóa `death_note` và `birth_death_quote`** — dù
`_build_dila_card_prompt` (rule 9/10 trong prompt) yêu cầu AI trả về
`death_note_vi`/`birth_death_quote_vi`. AI không có input Hán của 2 trường này nên
output luôn rỗng.

**Bằng chứng thật (SQL, đọc trực tiếp `data/lineage.db`, không bịa):**

```
SELECT entity_id, translated_text FROM translation_cache
WHERE source_type='dila_card' AND status!='invalidated' ORDER BY id DESC LIMIT 5;
```
→ cả 5/5 bản dịch mẫu (A001428, A009447, A010616, A009460, A000085) có
`death_note_vi: ''` và `birth_death_quote_vi: ''` dù `bio_concise_vi` có nội dung.
(5 người này không có death_note/birth_death_quote nguồn nên chưa chứng minh được
thiệt hại cụ thể cho họ — nhưng A000004 **CÓ** cả 2 trường nguồn không rỗng, nên sẽ
gặp đúng lỗi này nếu chạy `dila_translate` mà không sửa Lỗi B trước.)

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Nút "Dịch ngay" gọi | `POST /person/<id>/translate` (bio-only) | `POST /person/<id>/dila_translate` (toàn bộ DILA card) |
| `source_data` trong `dila_translate` | thiếu `death_note`, `birth_death_quote` | đủ cả 2 (hàm chung `_t148_dila_source_fields`) |
| Response `dila_translate` | `{ok, vi, status}` — không có tín hiệu "đủ trường" | thêm `missing_fields: [...]`, `done: bool` — nguồn sự thật duy nhất cho DONE (`_t148_dila_missing_fields`, so khớp đúng khóa AI trả về, ví dụ `dynasty_xml` → `dynasty_vi` không phải `dynasty_xml_vi`) |
| `GET /daoanh/api/dila/persons` (list) | mỗi dòng chỉ có `bio_vi_saved` (cột `people.bio_vi`) | thêm `dila_card_cached`, `dila_card_missing[]`, `dila_card_done` — tính thật cho từng dòng trả về (≤ `limit`, dùng `_t148_get_extra` là dict RAM, O(1)/dòng) |
| `GET /daoanh/api/dila/persons/stats` | không có số liệu dila_card | thêm `dila_card_cached` (đếm có-cache, **không** phải "đã đủ trường" toàn 49.490 — xem mục 7) |
| UI badge khi chưa đủ trường | không có — disable nút, hiện "✓ Đã lưu" | "⚠ Thiếu N trường" + tooltip danh sách trường, nút vẫn bấm được ("Dịch lại") |
| Job hàng loạt (`psProcessNext`, `psBuildQueue`) | gọi `/translate`, đếm `done++` khi `ok:true`, skip theo `bio_vi_saved` | gọi `/dila_translate`, chỉ đếm `done++` khi `d.done===true`, skip theo `dila_card_done` |

## 4. Files changed (trong worktree `wt/bug052-person-translate-false-done`)

- `daoanh/app.py`
  - Thêm `_DILA_FIELD_LABELS` (map khóa Hán → (khóa AI trả về, nhãn UI)), `_t148_dila_source_fields()`, `_t148_dila_missing_fields()`.
  - `api_person_dila_translate` (`/daoanh/api/person/<id>/dila_translate`): dùng `_t148_dila_source_fields` (đã có `death_note`/`birth_death_quote`); mọi response `ok:true` (4 nhánh GET + 1 nhánh POST) kèm `missing_fields`/`done`.
  - `api_dila_persons_search` (`/daoanh/api/dila/persons`): thêm CTE `dila_card_cte`, cột `dila_card_cached/_missing/_done` tính theo từng dòng trả về.
  - `api_dila_persons_stats` (`/daoanh/api/dila/persons/stats`): thêm đếm `dila_card_cached`.
- `daoanh/admin/translation_progress.html`
  - `psTranslateOne()`: gọi `/dila_translate` thay `/translate`; dùng `done`/`missing_fields` thật để quyết định badge, không tự suy DONE từ `ok:true`.
  - `psRenderRows()`: badge/nút theo `dila_card_done`/`dila_card_cached`/`dila_card_missing`, bỏ gate cũ chỉ dựa `bio_vi_saved`.
  - `psProcessNext()`, `psBuildQueue()`: đồng bộ sang `/dila_translate` + `dila_card_done` cho job chạy hàng loạt.
  - Đổi nhãn 2 tile đầu + thêm tile "Có bản dịch DILA card (chưa chắc đủ trường)" để không gây hiểu nhầm.

Backup trước khi sửa (trong worktree): `docs/sessions/2026-11-07/app.py.bak-before-bug052`, `docs/sessions/2026-11-07/translation_progress.html.bak-before-bug052`.

## 5. Migration / import / dry-run / rollback

- **Không có migration DB** — mọi thay đổi là code (routes, JS). Không ALTER TABLE, không ghi dữ liệu mới nào vào `translation_cache`/`people` ngoài những gì admin tự bấm qua UI (như trước giờ).
- Revert: `git checkout` lại 2 file từ backup trong `docs/sessions/2026-11-07/`, hoặc (sau khi tích hợp vào cây chính) `git revert <hash-tích-hợp>`.

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Repro bug (trước fix) | A000004, browser thật | person.html thiếu trường thì progress tab phải KHÔNG báo DONE | Xác nhận progress tab báo `✓ Đã lưu` trong khi person.html có đủ 9/9 trường "(chưa dịch)" — **bug tái hiện đúng như báo cáo** | ✅ (xác nhận bug có thật) |
| `_t148_dila_missing_fields` — chưa dịch gì | `source_data` thật của A000004 (lấy từ Hán văn thật trên person.html), `vi_dict={}` | missing = toàn bộ 9 trường có Hán | `9 trường: ['Tên khác (DILA)', 'Nghề nghiệp', 'Nơi xuất xứ', 'Triều đại', 'Tiểu sử vắn tắt', 'Trích dẫn CBETA', 'Kinh trong Đại Tạng', 'Ghi chú năm mất', 'Trích dẫn nguồn gốc (năm sinh/mất)']` | ✅ |
| Fallback — mô phỏng lỗi CŨ (chỉ dịch bio, như `/translate` cũ) | `vi_dict={'bio_concise_vi': 'x'}` | vẫn còn 8 trường thiếu, `done=False` (KHÔNG được coi là DONE — đúng yêu cầu Admin) | `8 trường thiếu, done=False` | ✅ |
| Fallback — dịch đầy đủ, đúng khóa AI (`dynasty_vi` không phải `dynasty_xml_vi`) | `vi_dict` đủ 9 khóa đúng tên | `missing=[]`, `done=True` | `missing=[], done=True` | ✅ |
| `python -m py_compile app.py` | — | exit 0 | exit 0 | ✅ |
| Cú pháp JS `admin/translation_progress.html` (mọi `<script>` qua `new Function`) | — | không lỗi parse | không lỗi parse | ✅ |
| Quét regression — nơi khác còn gọi `psTranslateOne`/endpoint cũ | grep toàn repo (trừ snapshot lịch sử `docs/sessions/`) | không còn call site nào ngoài `translation_progress.html`; route `/translate` cũ vẫn tồn tại (không xoá, không phá vỡ consumer khác) | đúng — chỉ 1 file, route cũ giữ nguyên | ✅ |

## 7. Limitation / blocker còn lại

1. **CHƯA gọi AI thật / chưa test round-trip HTTP qua server đang chạy.** Worktree
   (`C:\Users\Nam Thien\.claude\worktrees\bug052-person-translate-false-done\`) không
   có bản sao `data/lineage.db` thật (1.4–1.8GB, gitignore) và guard hook của dự án
   chặn mọi lệnh ghi/link tham chiếu tới cây chính (`ln`, `os.link`, `cp` đều bị
   CHẶN khi đường dẫn cây chính xuất hiện trong lệnh) — nên tôi không tự ý tạo
   liên kết tới DB thật hoặc chạy server thứ 2 trỏ vào DB thật từ worktree. Tôi đã
   validate logic bằng dữ liệu Hán THẬT của A000004 (lấy từ `person.html` qua
   browser thật) chạy qua 2 hàm mới, **không qua HTTP, không gọi AI** — xem mục 6.
   **Cần Admin quyết:** (a) tích hợp worktree vào cây chính qua
   `scripts/wt_integrate.py` rồi tôi/Admin bấm thật 1 lần trên A000004 qua server
   đang chạy (http://127.0.0.1:8080), hoặc (b) Admin tự bấm test sau khi xem code.
   **Chưa gọi AI thật — đúng yêu cầu "chỉ thử trên 1 ID sau khi hỏi".**
2. **Tile thống kê tổng (`/daoanh/api/dila/persons/stats`) chưa có số "đã dịch đầy
   đủ" cho toàn bộ 49.490 person.** Tính `dila_card_done` đúng cho MỖI dòng cần
   `_t148_get_extra()` (rẻ, dict RAM) + so khớp field — nhưng chạy việc đó cho
   toàn bộ 49.490 dòng trong 1 request `/stats` sẽ tốn thời gian không cần thiết
   mỗi lần tab load. Đã thêm `dila_card_cached` (đếm có-cache) làm số liệu tạm,
   ghi rõ trong code + UI là "chưa chắc đủ trường". Muốn có con số "N/49.490 đã
   dịch đầy đủ" chính xác & nhanh cần 1 cột persist (ví dụ
   `translation_cache.fields_done`/`missing_count`, ghi lúc dịch xong) — là thay
   đổi schema, cần Admin duyệt riêng theo quy tắc CLAUDE.md (migration DB cần xác
   nhận).
3. **CSV export của `/daoanh/api/dila/persons?format=csv` có vẻ đã hỏng từ trước
   (tiền-existing, không phải do fix này):** code gắn thêm khóa `hv` vào mỗi dict
   item không nằm trong `fieldnames` của `csv.DictWriter`, mà
   `csv.DictWriter.writerow()` mặc định raise `ValueError` khi dict có khóa lạ
   (không set `extrasaction='ignore'`). Tôi KHÔNG sửa vì ngoài phạm vi BUG-052 —
   nêu ở đây để Admin cân nhắc mở task riêng nếu CSV export đang được dùng.
4. **Route bio-only `/daoanh/api/person/<id>/translate` vẫn giữ nguyên, không
   xoá** (đúng "giữ nguyên chức năng cũ") — hiện không còn consumer nào trong
   admin UI gọi tới (đã grep xác nhận), nhưng để lại vì có thể còn dùng ở nơi khác
   chưa rà hết (ví dụ job nền ngoài phạm vi grep).

## 8. Tích hợp

Chưa merge vào cây chính. Code đang nằm trong worktree
`C:\Users\Nam Thien\.claude\worktrees\bug052-person-translate-false-done\`
(nhánh `wt/bug052-person-translate-false-done`), base = HEAD của `visjs-app` lúc
tạo worktree. Chờ Admin xem báo cáo + quyết định có chạy `scripts/wt_integrate.py`
hay không.

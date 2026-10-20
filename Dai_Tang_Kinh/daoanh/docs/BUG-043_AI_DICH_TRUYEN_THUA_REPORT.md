# BUG-043 — AI Dịch không dịch tên Hán trong mục TRUYỀN THỪA (SƯ PHỤ/ĐỆ TỬ)

Ngày: 2026-10-19
Task: `daoanh/tasks/T421-bug043-ai-dich-truyen-thua-ten-han.md`

## Files changed

- `daoanh/places.html`
  - Hàm `_linRelationCard()` (~dòng 7402-7427): thêm badge "AI dịch" khi tên Việt của
    relation đến từ AI phiên âm (không phải nguồn DILA/ZQLOCAL xác thực).
  - Hàm `_renderDilaExtra()`, khối render TRUYỀN THỪA (~dòng 7557-7606): build map
    `_relVi` từ `vi.relations_vi` (person_id → name_vi) và dùng làm fallback cho
    `r.name_vi` (vốn luôn `undefined`) khi dựng card SƯ PHỤ/ĐỆ TỬ.
  - `daoanh/app.py`: **không đổi** — endpoint dịch (`/daoanh/api/person/<id>/dila_translate`)
    đã có sẵn cơ chế AI phiên âm tên relation (`relations_vi`), chỉ frontend chưa đọc.

Không ghi DB, không tạo endpoint mới, không sửa raw DILA/TTL.

## Root cause đã xác minh

Lớp lỗi: **renderer/resolver ở frontend** — không phải data, không phải API contract
(API đã trả đúng field cần thiết từ trước).

Trace đầy đủ:

1. **Raw data**: DILA XML `listRelation` chỉ có `type`, `active` (person_id), `n`
   (tên Hán), `desc/bibl`, `desc/ref` — không có trường tên Việt. Parse tại
   `app.py` (`app_py` ~dòng 5877-5902, hàm nội bộ build index).
2. **API `/daoanh/api/person/<id>/dila_full`** (`app.py` dòng 20715): trả
   `relations: [{type, person_id, name, bibl, ref_url, hanviet_charwise}, ...]`.
   Trường `name_vi` **không tồn tại** trong object này — do đó
   `r.name_vi` ở frontend luôn `undefined`.
3. **API `/daoanh/api/person/<id>/dila_translate`** (`app.py` dòng 20111): ĐÃ sẵn
   có cơ chế dịch AI cho cả bio lẫn relations — field `vi.relations_vi =
   [{person_id, name_vi}, ...]`, ưu tiên override bằng tên đã xác thực trong DB
   (`people.name_vi` qua `person_name_lock`) khi có, nếu không thì dùng kết quả
   Groq/Qwen (fallback Gemini) phiên âm Hán-Việt. Field này đã tồn tại từ trước
   BUG-043 — không phải phần mới cần build.
4. **Renderer `_renderDilaExtra()` → `_relGroup()`** (`places.html`, trước fix):
   dựng card bằng `_linRelationCard({ name_vi: _viShortFromZh(r.name_vi, r.name), ... })`
   — chỉ đọc `r.name_vi` (luôn `undefined`, theo bước 2) và **hoàn toàn bỏ qua**
   `vi.relations_vi` dù biến `vi` đã được truyền sẵn vào hàm. Vì vậy card luôn rơi
   vào nhánh fallback `person.name_vi || person.name_zh` → chỉ hiện tên Hán.
5. Click "🌐 AI Dịch" (`_linDichAI`) gọi đúng `/dila_translate` (POST), ghi cache
   `relations_vi` ở backend, rồi gọi `_loadDilaExtra(pid)` để reload toàn bộ
   inspector — nhưng vì bước 4 chưa đọc `vi.relations_vi`, reload xong vẫn không
   đổi gì ở mục TRUYỀN THỪA. Đây chính là triệu chứng user báo cáo.

Đối chiếu: `admin/person.html` (route khác, không trong phạm vi task) xử lý khác —
dùng `r.hanviet_charwise` (phiên âm charwise tất định, không gọi AI) theo quyết
định T372, không dùng `relations_vi`. Route `daoanh/places.html` (route trong task)
chưa từng wiring bất kỳ nguồn nào cho tên Việt relation trước BUG-043.

## Thay đổi UI chính (before/after)

**Trước**: `_relGroup()` luôn gọi
`_linRelationCard({ name_vi: _viShortFromZh(r.name_vi, r.name), ... })` với
`r.name_vi === undefined` → card luôn hiện tên Hán, không có badge nguồn.

**Sau**:
```js
var _relVi = {};
(vi.relations_vi || []).forEach(function(rv) {
    if (rv && rv.person_id && rv.name_vi) _relVi[rv.person_id] = rv.name_vi;
});
...
var aiNameVi = _relVi[r.person_id] || null;
var resolvedNameVi = r.name_vi || aiNameVi;
... _linRelationCard(
    { id: r.person_id, name_vi: _viShortFromZh(resolvedNameVi, r.name), name_zh: r.name },
    { ..., name_vi_source: (!r.name_vi && aiNameVi) ? 'ai' : null }
)
```
`_linRelationCard()` hiện thêm badge nhỏ "AI dịch" (title: "Phiên âm AI (Gemini) —
không phải tên nguồn DILA/ZQLOCAL đã xác thực") khi `name_vi_source === 'ai'`, để
tuân thủ quy tắc naming-and-identity (không lẫn AI output với nguồn đã xác thực).
Tên Hán gốc vẫn luôn hiển thị song song (phần `sub`), DILA ID, badge ✓L2, evidence
quote, nguồn trích dẫn và link CBETA giữ nguyên không đổi.

Không có thay đổi API contract — chỉ wiring lại field đã có sẵn trong response.

## Kết quả test

### Case yêu cầu (A009447, qua Claude Browser thật — không JS inject)

Route: `http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A009447&lm=tree`

**Trước click AI Dịch**: mục TRUYỀN THỪA — SƯ PHỤ (1): `無學`; ĐỆ TỬ (14):
`招福 思明 巖俊 敬慧 二世 龍福 谷隱 遵古 天福 澄照 微 感溫 九嵕 璨幽` — toàn Hán, đúng
triệu chứng bug report.

**Sau click "🌐 AI Dịch"**: network log xác nhận
`POST /daoanh/api/person/A009447/dila_translate → 200 OK`, theo sau bởi
`GET /daoanh/api/person/A009447/dila_translate → 200 OK` (reload cache).

Mục TRUYỀN THỪA sau khi dịch (đọc qua `get_page_text`, xác nhận bằng mắt qua
screenshot):

- **SƯ PHỤ (1)**: `Vô Học [AI dịch] 無學 · DILA ID: A010616 · ✓L2`
- **ĐỆ TỬ (14)**: `Chiêu Phúc` (招福), `Tư Minh` (思明), `Nham Tuấn` (巖俊),
  `Kính Tuệ` (敬慧), `Nhì Thế` (二世), `Long Phúc` (龍福), `Cốc Ẩn` (谷隱),
  `Tuân Cổ` (遵古), `Thiên Phúc` (天福), `Trừng Chiếu` (澄照), `Vi` (微),
  `Cảm Ôn` (感溫), `Cửu Tông` (九嵕), `Xán U` (璨幽) — đủ cả 14, mỗi card có badge
  "AI dịch", tên Hán gốc giữ song song, DILA ID + ✓L2 + nguồn trích dẫn + link
  CBETA (九嵕, 璨幽) không đổi.

Screenshot evidence (trong session Claude Browser, không lưu file riêng theo yêu
cầu "không viết file report/screenshot thừa" — đã mô tả bằng text ở trên và có thể
tái tạo bằng đúng route + click).

### Regression

- Dịch tiểu sử (biography) vẫn hoạt động bình thường: sau click AI Dịch, phần
  "BẢN DỊCH TIẾNG VIỆT" hiện đầy đủ bản dịch tiếng Việt của tiểu sử 大同 (Đại Đồng),
  nút "🌐 AI Dịch" biến mất đúng như thiết kế cũ (không đổi hành vi này).
- "Tên khác (Việt)", "Nơi xuất xứ", "Trích dẫn CBETA" — vẫn dịch và hiện đúng như
  trước (không bị ảnh hưởng bởi thay đổi).
- Console: `read_console_messages(onlyErrors=true)` → không có log lỗi nào sau khi
  click AI Dịch và scroll toàn bộ panel.
- IDs, badge nguồn (DILA ID, ✓L2), evidence links, CBETA ↗ links giữ nguyên không
  đổi — đúng ràng buộc "Giữ nguyên IDs, badges..." trong task.
- Không ghi DB: chỉ đọc `vi.relations_vi` từ response JSON đã có, không có lệnh
  UPDATE/INSERT nào được thêm.

## Limitation / blocker còn lại

- Badge "AI dịch" hiện áp dụng đồng nhất cho mọi tên lấy từ `vi.relations_vi`, kể
  cả trường hợp backend đã override bằng tên xác thực trong DB
  (`person_name_lock`, khi relation person_id có `people.name_vi` hợp lệ) — vì
  frontend không phân biệt được 2 trường hợp con này từ response hiện tại (backend
  gộp chung vào field `name_vi`). Nếu cần phân biệt rõ "tên xác thực DB" vs "AI tự
  phiên âm thuần", cần backend trả thêm cờ `locked: true/false` cho từng phần tử
  `relations_vi` — nằm ngoài phạm vi UI-only của task này.
- Cache dịch chỉ tồn tại trong `translation_cache` (backend, theo thiết kế sẵn có
  của `dila_translate`) + state JS tạm thời của tab hiện tại; không có cache riêng
  phía UI theo đúng yêu cầu "không ghi DB" — lần load trang mới sẽ gọi lại GET
  `dila_translate` và nhận cache nếu đã dịch trước đó (hành vi cũ, không đổi).

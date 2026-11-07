# BUG-052 follow-up — POST /daoanh/api/person/A000004/dila_translate trả 503

> Worktree: `wt/bug052-groq-503-debug` (KHÔNG merge vào cây chính — chờ Admin duyệt).
> Chưa đánh Done. Chỉ phân tích + 1 log cải thiện khả năng chẩn đoán, không đổi
> ngưỡng/timeout/model.

## 1. Nguyên nhân gốc (đo bằng số liệu thật, không in khóa)

Gọi trực tiếp Groq API 10 lần liên tiếp bằng prompt ngắn (script
`scripts/bug052_groq_repro.py`, model `qwen/qwen3.8-27b`, `max_tokens=4096` —
đúng giá trị route `app.py` dùng):

```
[0] HTTP 429 ... OTPM Limit 1000, Requested 1057
[1] HTTP 429 ... OTPM Limit 1000, Requested 1235
[2] HTTP 429 ... OTPM Limit 1000, Requested 1057
[3] HTTP 429 ... OTPM Limit 1000, Requested 1235
[4] HTTP 429 ... OTPM Limit 1000, Requested 1057
[5] HTTP 429 ... OTPM Limit 1000, Requested 1057
[6] HTTP 429 ... OTPM Limit 1000, Requested 1235
[7] HTTP 429 ... OTPM Limit 1000, Requested 1057
[8] HTTP 429 ... OTPM Limit 1000, Requested 1057
[9] HTTP 200 ... finish_reason=stop usage={'completion_tokens': 11, ...}
```

**Thông báo đầy đủ từ Groq (không phải khóa, là message lỗi):**
`"Request too large for model qwen/qwen3.8-27b in organization
org_01j1vbhy89fjwtbheqaejrt8yw service tier on_demand on output tokens per
minute (OTPM): Limit 1000, Requested 1057/1235. The request's expected
output tokens exceed the enforced limit; reduce max_tokens..."`

**Kết luận:** tổ chức Groq đang dùng tier `on_demand` có **OTPM (output
tokens/phút) = 1000** cho model `qwen/qwen3.8-27b`. Route `app.py:22425`
luôn gửi `max_tokens: 4096` trong MỌI request — vượt hạn mức OTPM ngay từ
request đầu tiên trong phần lớn các phút → Groq trả `HTTP 429` gần như mỗi
lần gọi. Request chỉ lọt qua khi cửa sổ phút đó còn đủ budget (xác suất,
không phải lỗi cấu hình key/model).

**Vì sao đôi khi lại ra lỗi 500 "AI không trả về JSON hợp lệ" (khác 503):**
Groq không luôn từ chối cứng (429) — có lúc chấp nhận request nhưng cắt
sinh văn bản giữa chừng khi hết OTPM budget trong lúc đang generate (quan
sát thực tế qua gateway lúc 12:49:03 — xem `app_local.err` dòng 12 — nội
dung Groq trả về bị cắt ngay trong `bio_concise_vi`, dù trường này chỉ
~150 ký tự input). Route parse JSON thất bại → trả 500 với `raw` là chuỗi
bị cắt.

**Vì sao log không hiện cảnh báo nào (lý do phụ, đã sửa — xem mục 3):**
`app.py:22420-22432` (bản gốc) chỉ gọi `app.logger.warning()` trong nhánh
`except Exception`. Một response `HTTP 429` KHÔNG làm `requests.post()` raise
exception — `gr.json()` parse thành công (trả object `{"error": {...}}`,
không có `choices`) — nên code rơi vào nhánh `if gd.get('choices'):` = False
và **đi thẳng qua, không log gì cả**. Đây là lý do
`app_local.out`/`app_local.err` không có dòng `[dila_translate]` nào dù
response client thấy rõ 503/500 (xác nhận bằng `tail app_local.err`: chỉ
có log access của werkzeug, không có log warning).

## 2. Về GEMINI_API_KEY (vấn đề phụ nêu trong yêu cầu — ĐÃ KIỂM, KHÔNG rỗng)

Kiểm `.env` (không in giá trị thật, chỉ đo độ dài/tiền tố):
- `GEMINI_API_KEY`: **CÓ giá trị**, dài 53 ký tự, tiền tố `AQ.Ab...` (không
  phải định dạng `AIzaSy...` thường gặp, nhưng vẫn là key hợp lệ cho
  `gemini-3.6-flash`).
- `GROQ_API_KEY`/`GROQ_MODEL`: **không có dòng nào trong `.env`** (route lấy
  `groq_key` từ `data/llm_config.json` qua `_llm_config_read()`, không phải
  từ env — đúng như thiết kế).

Gọi trực tiếp Gemini 5 lần (`scripts/bug052_gemini_repro.py`):
```
[0] HTTP 200 elapsed=5.49s OK
[1] HTTP 200 elapsed=5.02s OK
[2] HTTP 200 elapsed=24.10s OK
[3] HTTP 200 elapsed=41.62s OK
[4] HTTP 200 elapsed=3.94s OK
```
Và qua route thật (model_id trả về `"gemini-3.6-flash"` ở 1 trong các lần
test) — xác nhận **server đang chạy có GEMINI_API_KEY hợp lệ, không rỗng,
không 403**. Nhận định "GEMINI_API_KEY trong .env đang rỗng" trong yêu cầu
gốc **không đúng với trạng thái hiện tại** — có thể là quan sát từ một thời
điểm/tiến trình khác (biến env hệ thống rỗng che `.env` qua `load_dotenv`
không override biến đã tồn tại) nhưng KHÔNG phải nguyên nhân của 503 hiện
tại. Gemini chỉ chậm (3.9s–41.6s), không lỗi key.

**Trường hợp 503 (cả Groq và Gemini đều fail cùng lúc)** xảy ra khi: Groq
429 (gần như luôn) + Gemini fallback gặp lỗi/timeout tạm thời trong đúng cửa
sổ request đó (quan sát 1 lần trong lúc test, elapsed 17.6s — ngắn hơn
timeout 45s của Gemini nên khả năng cao là lỗi JSON lỗi/transient từ phía
Gemini, không bắt được message cụ thể vì nhánh except gốc không log —
**đã sửa, xem mục 3**).

## 3. Thay đổi đã làm (worktree `wt/bug052-groq-503-debug`, CHƯA merge)

File: `app.py` (route `api_person_dila_translate`, dòng ~22411–22465).
Thay đổi nhỏ, chỉ thêm log, KHÔNG đổi `max_tokens`, KHÔNG đổi timeout,
KHÔNG đổi model, KHÔNG đổi luồng fallback:

1. Nhánh Groq: khi `gd.get('choices')` có kết quả nhưng
   `finish_reason != 'stop'` (ví dụ `'length'` — output bị cắt) → log
   warning kèm `person_id` + độ dài `vi_text`.
2. Nhánh Groq: khi response KHÔNG có `choices` (lỗi JSON dạng 429/4xx/5xx)
   → log warning kèm HTTP status thật + nội dung `error` (cắt 300 ký tự,
   không có khóa trong đó).
3. Nhánh Gemini: tương tự — log khi không có `candidates`, kèm HTTP status
   + nội dung lỗi.

`python -m py_compile app.py` → **COMPILE_OK** (không lỗi cú pháp).

**Chưa verify log này chạy thật trên server đang sống** vì không được tự
merge/patch cây chính (server `app.py` đang chạy là bản KHÔNG có patch —
đúng theo chỉ đạo "không ghi trực tiếp cây chính, không tự merge"). Patch
chỉ nằm trong worktree, sẵn sàng để Admin duyệt merge qua
`scripts/wt_integrate.py` nếu đồng ý.

## 4. Kiểm chứng A000004 (1 lần gọi AI thật, không dùng force)

```
POST http://127.0.0.1:8080/daoanh/api/person/A000004/dila_translate
→ HTTP 200, elapsed 5.71s
{"ok": true, "done": true, "from_cache": false,
 "missing_fields": [], "model_id": "qwen/qwen3.8-27b", "status": "auto"}
```

Lần gọi này Groq lọt qua (không bị 429 vì rơi đúng cửa sổ phút còn budget),
dịch đầy đủ, `missing_fields=[]`. **Kết quả không ổn định giữa các lần gọi**
— đúng với bản chất root cause (giới hạn theo phút của Groq, không phải lỗi
cố định).

## 5. Đề xuất (KHÔNG tự áp dụng — chờ Admin quyết)

Root cause thật là **hạn mức tổ chức Groq (OTPM=1000, tier on_demand)**,
không sửa được bằng code một mình. Phương án (ưu/nhược để Admin chọn):

- **(a) Giảm `max_tokens` xuống ví dụ 900–950`** cho request Groq của route
  này: giảm tỷ lệ 429 (vì "Requested" luôn < 1000) nhưng có thể cắt output
  cho person có bio/listbibl dài (ví dụ các vị dịch giả nhiều tác phẩm) →
  vẫn ra lỗi 500 "JSON không hợp lệ" cho các case đó, chỉ đổi từ 503 sang
  500 cho nhóm record lớn.
- **(b) Giữ `max_tokens=4096` nhưng thêm retry có backoff khi gặp 429**
  (giống `_t73_call_qwen_groq` ở dòng ~21625 đã có logic retry 429 sẵn —
  route `dila_translate` lại KHÔNG dùng hàm đó, tự viết request riêng
  không retry). Có thể hợp nhất route này vào hàm retry có sẵn thay vì
  double-code.
- **(c) Nâng hạn mức Groq (đổi tier/plan)** — ngoài phạm vi code, cần Admin
  quyết định ở Groq console.
- **Khuyến nghị:** (b) ít rủi ro nhất (không đổi hành vi khi có đủ quota,
  tự phục hồi khi 429 tạm thời) + least code duplication (dùng lại hàm có
  sẵn) — nhưng cần đo lại độ trễ (mỗi retry cộng thêm backoff, có thể vượt
  timeout trình duyệt nếu Admin không chỉnh UI chờ lâu hơn).

## 6. File liên quan

- `app.py` — sửa log (worktree only), route `api_person_dila_translate`.
- `scripts/bug052_probe.py` — đo kích thước prompt/source_data cho 1 person
  (không ghi DB).
- `scripts/bug052_groq_repro.py` — gọi Groq lặp lại, bắt HTTP status/error
  thật (không in khóa, không ghi DB).
- `scripts/bug052_gemini_repro.py` — gọi Gemini lặp lại tương tự.
- `docs/BUG-052-FOLLOWUP-DILA-TRANSLATE-503-REPORT.md` — file này.

Không DB mutation (ngoài cache ghi bởi route gốc khi test A000004 qua server
đang chạy — hành vi có sẵn, không phải do patch trong worktree).

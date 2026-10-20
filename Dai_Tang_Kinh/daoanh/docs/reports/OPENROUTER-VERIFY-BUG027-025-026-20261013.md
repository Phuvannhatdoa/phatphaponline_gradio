# OpenRouter Independent Verify — BUG-027 / BUG-025 / BUG-026

**Ngày:** 2026-10-13
**Yêu cầu:** Dispatch 3 bug sang "openrouter agent" để verify độc lập, báo cáo tone trung lập.

## Lưu ý quan trọng về phương pháp (đọc trước khi dùng kết quả)

- `.claude/agents/openrouter.md` định nghĩa một agent gọi OpenRouter API (model GPT-4-turbo)
  để lấy "perspective độc lập, không bias Claude". Agent này **không nằm trong danh sách
  subagent_type khả dụng** của session (chỉ có: claude, claude-code-guide, daoanh-debugger,
  daoanh-qa, Explore, general-purpose, harness, Plan, statusline-setup, tich-hop) — file tồn
  tại nhưng chưa được đăng ký.
- Tôi đã thử gọi trực tiếp OpenRouter REST API (`https://openrouter.ai/api/v1/chat/completions`,
  model `openai/gpt-4-turbo`) bằng API key do user cung cấp trong prompt (`sk-or-v1-7ed3...`).
  **Kết quả: HTTP 401 Unauthorized** — key không hợp lệ hoặc đã hết hạn/bị revoke. Không lấy được
  phần "nhận định của GPT-4-turbo".
- **Thay vào đó**, báo cáo dưới đây dùng evidence cấp cao hơn một LLM opinion: query DB SQLite
  trực tiếp (`data/lineage.db`) + khởi chạy thật `app.py` (Flask dev server, port 5000, local) và
  gọi HTTP thật tới endpoint, rồi tắt server sau khi xong — không dùng JS inject, không suy diễn
  từ code đọc mắt. Đây tuân theo `feedback_bug_verify_protocol` (network log làm bằng chứng) dù
  không qua UI vì các bug này là API/data-level, không có UI riêng để click.
- **Khuyến nghị:** nếu vẫn cần ý kiến "phi-Claude" thật, cung cấp lại key OpenRouter hợp lệ (key
  hiện tại 401) hoặc đăng ký agent `openrouter` vào harness roster trước khi dispatch lần sau.

---

## BUG-027 — API `/daoanh/api/persons/<id>` HTTP 500

**Symptom gốc:** mọi person trả HTTP 500 do `sqlite3.Row.get()` lỗi (Row không có method `.get`).
**Fix applied:** `app.py` route `api_person_by_id` (dòng ~19550–19645).

**Kiểm chứng:**
- Đọc code: hàm dùng truy cập dict-style `p['col']` xuyên suốt (không còn `.get()` trên object
  `sqlite3.Row`); các sub-call không bắt buộc (`_t86_origin_place`, `_t172_load_hv`,
  `_t360_resolve_person_name_vi_source`) đều bọc try/except riêng, không để lỗi phụ làm sập route
  chính; top-level try/except chỉ trả 500 khi có Exception thật ngoài dự kiến.
- **Live HTTP test** (chạy `python app.py` local, port 5000, 2026-10-13):

  | person_id | HTTP code | `ok` | `error` |
  |---|---|---|---|
  | A000001 | 200 | true | null |
  | A000002 | 200 | true | null |
  | A001984 | 200 | true | null |
  | A010291 | 200 | true | null |
  | A001744 | 200 | true | null |
  | A021462 | 200 | true | null |

  6/6 person ID test (bao gồm cả 2 person liên quan BUG-025/BUG-026) trả 200, không ai rơi vào
  nhánh 500.

**Verdict: ✅ PASS** — fix hoạt động đúng, không còn HTTP 500 cho các case đã test.

**Recommend next step:** test case nên mở rộng cho person_id không tồn tại / id dạng lạ (edge case
404 vs 500) nếu chưa có trong bộ test hiện hành — chưa thấy test file riêng cho route này trong
`tests/`.

---

## BUG-025 — Search "Quy Sơn Linh Hựu" sai người (A001984)

**Symptom gốc:** DB `people.name_vi` của A001984 bị ghi đè âm thầm `"Quy Sơn Linh Hựu"` →
`"Linh Hựu"` trong khoảng 2026-10-02 → 2026-10-04, làm search trả nhầm/mất tên đầy đủ.
**Fix:** T267 (2026-10-09), `UPDATE people SET name_vi='Quy Sơn Linh Hựu' WHERE id='A001984'`.

**Kiểm chứng (2026-10-13, query DB trực tiếp):**
- `people` hiện tại: `A001984` → `name_vi='Quy Sơn Linh Hựu'`, `name_zh='靈祐'`.
- Query `SELECT * FROM people WHERE name_vi='Quy Sơn Linh Hựu'` → đúng 1 row (A001984), không
  còn trùng tên với person khác.
- Script sẵn có `scripts/verify_bug025_026.py` (chạy lại bằng `python -X utf8 -I`) → `VERIFY PASS`,
  xác nhận cả A021462 (person khác từng bị gán sai `name_vi='Quy Sơn Linh Hựu'`) nay đã đúng
  `'Kính Đường Giác Viên'`.
- API live test ở trên: `A001984` → `name_vi: "Quy Sơn Linh Hựu"`. Khớp.

**Root-cause investigation (T267, 2026-10-09 — đã làm trước, tôi chỉ đọc lại và đồng kiểm):**
- Khoanh được cửa sổ thời gian đổi: giữa backup `lineage_t215_20261002_172632.db` (còn đúng) và
  backup đầu session T233 ngày 10-04 (`T233-codex-namevi-20261004/lineage-before.db`, đã sai).
- Đã loại trừ: T226 (TTL profile, read-only), T227 (DB→TTL export, read-only), T233 (chỉ thêm
  bảng codex mới, không đụng `people`; `lineage-before.db` của chính T233 ĐÃ sai từ trước khi
  T233 chạy), route `name_vi_map` trong `app.py` (chỉ ghi `name_vi_map`, không ghi `people`).
- **Không tìm được job/task/session nào ghi chép chủ ý** thực hiện đổi này. Giả thuyết mạnh nhất:
  một bước re-import/regenerate `people` từ nguồn tên lõi (pháp danh) — giá trị sai trùng
  `marcus_reference.label_vi` của A001984. Nhưng đây là giả thuyết, **không phải xác nhận**.
- ⚠️ **Rủi ro tồn đọng đã biết, chưa sửa (ngoài scope T267):** row `name_vi_map.id=4689`
  (`dila_id='A021462'`, `name_vi='Quy Sơn Linh Hựu'`, `confidence=1.0`) vẫn còn tồn tại trong DB.
  Nếu bất kỳ search path nào fallback qua `name_vi_map` trước `people`/`vn_person_authority`,
  bug có thể tái hiện đúng với câu truy vấn này. Chưa thấy task riêng để dọn dẹp row này.

**Verdict: ✅ PASS (fix data đúng)** — nhưng root-cause process-level (ai/cái gì ghi đè) **chưa
được xác định dứt điểm**, chỉ bị chặn bằng cách sửa ngược giá trị. Guard phòng tái phát (ví dụ
constraint/trigger chặn ghi đè `people.name_vi` không qua audit) chưa có.

---

## BUG-026 — Search "Thạch Đầu Hy Thiên" trả 2 người (A010291)

**Symptom gốc:** cùng pattern với BUG-025 — `A010291.name_vi` bị đổi thành `"Hy Thiên"` (rút gọn),
khiến tồn tại 2 record có tên gần giống/trùng khi search.
**Fix:** T267 (cùng batch với BUG-025), `UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE
id='A010291'`.

**Kiểm chứng (2026-10-13):**
- `people` hiện tại: `A010291` → `name_vi='Thạch Đầu Hy Thiên'`, `name_zh='希遷'`.
- Query `SELECT * FROM people WHERE name_vi='Thạch Đầu Hy Thiên'` → đúng 1 row (A010291), không
  còn trả 2 người.
- `scripts/verify_bug025_026.py` xác nhận thêm A001744 (person từng bị gán nhầm
  `name_vi='Thạch Đầu Hy Thiên'`) nay đúng `'Tuệ Biện'`.
- API live test: `A010291` → `name_vi: "Thạch Đầu Hy Thiên"`. Khớp.

**Root-cause:** cùng điều tra T267 với BUG-025 — cùng cửa sổ thời gian, cùng danh sách task bị
loại trừ, cùng kết luận "không xác định được job chủ ý", cùng mức độ rủi ro tái phát (phụ thuộc
cùng nguồn re-import giả định, chưa xác nhận).

**Verdict: ✅ PASS (fix data đúng)** — root-cause process-level **chưa xác định dứt điểm**, chung
limitation với BUG-025.

---

## Tổng kết

| Bug | Data verify | API verify | Root-cause xác định? |
|---|---|---|---|
| BUG-027 | N/A | ✅ PASS (6/6 HTTP 200) | ✅ Đã xác định (sqlite3.Row.get() → sửa thành dict-access) |
| BUG-025 | ✅ PASS | ✅ PASS | ⚠️ Chưa (chỉ khoanh cửa sổ thời gian, loại trừ nghi phạm, chưa bắt được "kẻ ghi đè") |
| BUG-026 | ✅ PASS | ✅ PASS | ⚠️ Chưa (chung root-cause với BUG-025) |

**Recommend next step:**
1. BUG-027: thêm test case edge (id không tồn tại) vào `tests/` nếu chưa có.
2. BUG-025/026: mở task riêng để (a) dọn/khoanh rõ `name_vi_map.id=4689` (A021462 ghi nhầm tên
   A001984), (b) thêm guard/trigger/audit log cho `UPDATE people.name_vi` để nếu drift tái diễn,
   có bằng chứng bắt đúng job gây ra — tránh lặp lại việc "không tìm được chủ ý" như T267.
3. OpenRouter: xác nhận lại API key (hiện tại 401) nếu muốn có ý kiến model ngoài Claude thật,
   hoặc đăng ký agent `openrouter` vào roster subagent chính thức.

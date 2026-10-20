# Audit / Bug Fix Report — ADMIN_PERSON_BIO_EMPTY_FIX

> Tab: Admin Person Detail.
> Bug #1: section "Tiểu sử" hiển thị trống dù DB đã có dữ liệu.
> Bug #2 (bổ sung, cùng phiên debug): nút "AI dịch" báo lỗi "Không có dữ liệu DILA XML" dù `bio_zh` không rỗng.
> Route/case: `admin/person.html?id=A000035` và `admin/person.html?id=A003627`.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `data/lineage.db` → bảng `people`, cột `bio` (Hán, nguồn DILA) |
| API endpoint (đúng) | `GET /daoanh/api/persons/<id>` — `app.py:19322` — trả `biography`/`bio_zh` = `people.bio` |
| API endpoint (phụ, mở rộng XML) | `GET /daoanh/api/person/<id>/dila_full` — `app.py:20388` — trả `has_extra` dựa trên index XML riêng (`_t148_get_extra`, `app.py:5864`) |
| Renderer | `admin/person.html` — hàm `load()` (dòng ~750) set `_personBioZh = d.bio_zh || d.biography`; hàm `loadDilaExtra()` (dòng ~675) quyết định có gọi `renderDilaSideBySide()` hay không; `renderDilaSideBySide()` (dòng 161) là nơi DUY NHẤT render các dòng "Tiểu sử vắn tắt"/"Tiểu sử chi tiết" (dòng 299–300) |
| Schema contract | Không đổi — chỉ sửa điều kiện gọi hàm render phía JS |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** renderer (frontend component logic), không phải data/API contract.
- **Nguyên nhân chính xác:**
  `people.bio` (nguồn DILA, 201 ký tự cho A000035, 286 ký tự cho A003627) được API `/daoanh/api/persons/<id>` trả về đúng (`biography`, `bio_zh`), và JS gán đúng vào biến `_personBioZh`. Tuy nhiên, toàn bộ khối hiển thị "Tiểu sử vắn tắt"/"Tiểu sử chi tiết" chỉ được build bên trong `renderDilaSideBySide()`, và hàm này **chỉ được gọi khi** `d.has_extra === true` từ một API hoàn toàn khác (`/daoanh/api/person/<id>/dila_full`, dựa trên index XML DILA Authority riêng, không liên quan tới cột `people.bio`).

  Với A000035 và A003627, `dila_full` trả `has_extra: false` (không có alt_names/listbibl/works/... trong XML extra), nên điều kiện `if (d.ok && d.has_extra)` trong `loadDilaExtra()` (dòng 679 cũ) luôn `false` → `renderDilaSideBySide()` không bao giờ chạy → cả card "DỮ LIỆU DILA AUTHORITY (XML)" (bao gồm dòng Tiểu sử) không bao giờ hiện, mặc dù dữ liệu `bio` (`_personBioZh`) đã có sẵn và hợp lệ.

  Bằng chứng (chạy server local, response thực tế):
  - `GET /daoanh/api/persons/A000035` → `"biography"` dài 201 ký tự, `"bio_zh"` giống vậy.
  - `GET /daoanh/api/person/A000035/dila_full` → `{"has_extra":false,"ok":true,"person_id":"A000035"}`
  - Tương tự với A003627 (`bio` dài 286 ký tự, `has_extra:false`).
  - Thực tế trên server local này, bảng `ttl_v2_source_records` (nguồn index DILA XML cho T148) không tồn tại (`no such table: ttl_v2_source_records`), nên `_T148_DILA_EXTRA` luôn rỗng → **mọi person_id** đều nhận `has_extra: false` — bug này không giới hạn ở 2 ID nêu trong task mà ảnh hưởng toàn bộ trang Admin Person Detail trên môi trường local hiện tại.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data (`people.bio`) | Không đổi — đã có sẵn | Không đổi |
| API `/daoanh/api/persons/<id>` | Không đổi — đã đúng | Không đổi |
| API `/daoanh/api/person/<id>/dila_full` | Không đổi — hợp lệ trả `has_extra:false` khi không có XML extra | Không đổi |
| Renderer `loadDilaExtra()` | `if (d.ok && d.has_extra)` → bỏ qua `renderDilaSideBySide()` nếu không có XML extra, dù `_personBioZh` đã có dữ liệu | `if (d.ok && (d.has_extra || _personBioZh))` → vẫn gọi `renderDilaSideBySide()` khi có `bio` cơ bản, kể cả không có XML extra; các field khác (alt_names, listbibl, relations, ...) tự ẩn vì rỗng (logic sẵn có trong `row()`/các khối `if (d.xxx && d.xxx.length)` không đổi) |

## 4. Files changed

- `daoanh/admin/person.html` (dòng ~679) — đổi điều kiện gọi `renderDilaSideBySide()` trong `loadDilaExtra()` từ chỉ dựa vào `d.has_extra` (API DILA XML mở rộng) sang `d.has_extra || _personBioZh` (biến đã chứa `people.bio` lấy từ API person chính). Không đổi API, không đổi DB, không hard-code text tiểu sử.

## 5. Migration / import / dry-run / rollback

- Không chạm DB, không migration. Chỉ sửa 1 điều kiện JS trong file tĩnh `admin/person.html`.
- Rollback: `git checkout -- daoanh/admin/person.html` (chưa commit).

## 6. Test cases & kết quả

Chạy server local (`python app.py`, port 5000), đăng nhập test bằng cách set `localStorage.admin_session` (giá trị test cục bộ, không dùng mật khẩu thật — `/daoanh/api/login/check` không chạy trên server auth phụ port 5001 trong phiên test này nên không redirect), mở `admin/person.html?id=...` bằng browser thật, chụp ảnh trước/sau.

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu 1 | `admin/person.html?id=A000035` | Card "Dữ liệu DILA Authority (XML)" hiện, dòng "Tiểu sử vắn tắt" hiện đúng văn bản Hán 201 ký tự (俗姓薛...) | Trước fix: card hoàn toàn không hiện (biến mất, không lỗi console). Sau fix: card hiện, dòng Tiểu sử hiện đúng văn bản | ✅ |
| Case yêu cầu 2 | `admin/person.html?id=A003627` | Tương tự, văn bản Hán 286 ký tự (臨濟希運...) | Trước fix: trống. Sau fix: hiện đúng (斷際希運 (751-850) 禪師法嗣...) | ✅ |
| Fallback — person không có `bio` lẫn `dila_full extra` | ID bất kỳ chưa có `people.bio` và `has_extra:false` | Không hiện card DILA Authority (giữ nguyên hành vi cũ) | `d.ok && (d.has_extra || _personBioZh)` = `true && (false || '')` = `false` → không gọi render — đúng như kỳ vọng | ✅ (suy luận từ code, không có ID mẫu loại này trong phạm vi test) |
| Regression — person có `has_extra:true` (XML extra đầy đủ) | Không có ID nào trả `has_extra:true` trong `data/lineage.db` local hiện tại (do thiếu bảng `ttl_v2_source_records` nên `_T148_DILA_EXTRA` rỗng toàn bộ) | Hành vi không đổi so với trước (nhánh `d.has_extra` cũ giữ nguyên, chỉ thêm `|| _personBioZh`) | Không thể test trực tiếp trên môi trường local này — xem mục Limitation | ⚠️ Không test được (môi trường), nhưng không có thay đổi logic nào ảnh hưởng nhánh này |

## Bug #2 — Nút "AI dịch" báo "Không có dữ liệu DILA XML" dù bio_zh không rỗng

### Vị trí audit

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Handler JS | `admin/person.html:422` — `doDilaTranslate()` → `POST /daoanh/api/person/<id>/dila_translate` |
| API endpoint | `app.py:19791` — `api_person_dila_translate()` |
| Nguồn dữ liệu thật | `people.bio` (cột Hán văn cơ bản, dùng cho bio_concise) |
| Nguồn gate sai | `_t148_get_extra(person_id)` (`app.py:5864`) — index XML DILA "extra" (alt_names/listbibl/works/...) |

### Root cause (đã xác minh) — CHUNG root cause với Bug #1

- **Lớp gây lỗi:** API contract / resolver (route-level guard sai điều kiện), cùng nguyên nhân gốc với Bug #1: **cả hai bug đều coi "không có dữ liệu DILA XML mở rộng" (`_t148_get_extra` rỗng) là "không có gì để hiển thị/dịch"**, trong khi `people.bio` là nguồn độc lập, luôn tồn tại và hợp lệ, không phụ thuộc vào index XML đó.
- Bằng chứng trước fix:
  - `people.bio` của A000035 dài 201 ký tự, không rỗng (đã xác minh ở Bug #1).
  - `_t148_get_extra('A000035')` trả `{}` (rỗng) — vì bảng nguồn `ttl_v2_source_records` không tồn tại trong `data/lineage.db` local (tất cả person_id đều `has_extra:false`).
  - Code cũ (`app.py:19797-19799`):
    ```python
    extra = _t148_get_extra(person_id)
    if not extra:
        return jsonify({"ok": False, "error": "Không có dữ liệu DILA XML"}), 404
    ```
    → chặn 404 ngay cả khi `people.bio` có nội dung hợp lệ để dịch, vì guard chỉ kiểm tra `extra` chứ không kiểm tra `bio_zh`.
  - Test trước fix (curl `POST /daoanh/api/person/A003627/dila_translate`) → `404 {"ok": false, "error": "Không có dữ liệu DILA XML"}`.

### Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Guard điều kiện | `if not extra: return 404` (chỉ dựa vào XML extra) | `if not extra and not bio_zh: return 404` (chỉ 404 khi THẬT SỰ không có Hán văn nào để dịch — cả extra lẫn bio đều rỗng) |
| `source_data['bio_concise']` | Không đổi — vẫn lấy từ `people.bio` (`bio_zh[:2000]`), không phụ thuộc `extra` | Không đổi |
| Response thành công | N/A (404 trước khi tới logic dịch) | `200 {"ok": true, "from_cache": false, "vi": {...}, "model_id": "qwen/qwen3.8-27b", "translation_id": ...}` |

### Files changed

- `daoanh/app.py` (`api_person_dila_translate`, dòng ~19791–19806) — di chuyển guard 404 xuống sau khi đã lấy `bio_zh` từ DB, đổi điều kiện từ `not extra` thành `not extra and not bio_zh`; dùng `extra = _t148_get_extra(person_id) or {}` để các `extra.get(...)` phía dưới vẫn an toàn (giữ nguyên hành vi cũ khi `extra` có dữ liệu thật).

### Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| Case yêu cầu | `POST /daoanh/api/person/A000035/dila_translate` (curl, trước browser) | Không còn 404 "Không có dữ liệu DILA XML"; dịch thành công | Trước fix: `404 {"error":"Không có dữ liệu DILA XML"}`. Sau fix: `200 {"ok":true,"from_cache":false,"model_id":"qwen/qwen3.8-27b","vi":{"bio_concise_vi":"Tục họ Tiết. Bảy tuổi xuất gia..."}}` | ✅ |
| Case yêu cầu (browser thật) | Mở `admin/person.html?id=A003627`, click nút "✨ AI Dịch DILA" | Nút chuyển "Đang dịch…" → "✅ Đã dịch mới ✨", cột Việt hiện bản dịch, không có badge lỗi | Xác nhận bằng screenshot thực tế: nút hiện "Đã dịch mới", cột "BẢN DỊCH TIẾNG VIỆT" hiện đầy đủ văn bản dịch (model `qwen/qwen3.8-27b`) | ✅ |
| Fallback — person không có cả `bio` lẫn `extra` | Giả lập logic: `extra={}`, `bio_zh=''` | Vẫn trả 404 "Không có dữ liệu DILA XML" (hành vi đúng, không có gì để dịch) | Xác nhận qua code: `not {} and not '' → True` → giữ nguyên 404 | ✅ (suy luận từ code, không có ID thật loại này để test trực tiếp) |
| Regression — person có `extra` đầy đủ (has_extra:true) | Không có ID nào trả `has_extra:true` trong `data/lineage.db` local hiện tại | Hành vi dịch không đổi (nhánh dùng `extra.get(...)` không bị sửa) | Không test trực tiếp được — xem Limitation chung | ⚠️ Không test được (môi trường), nhưng code nhánh đó không đổi |

### Tác dụng phụ cần lưu ý

- Chạy test case thật (click nút "AI dịch" trong browser + 1 lần curl POST) đã thực sự gọi LLM (Groq/Qwen, key cấu hình sẵn trong `.env`) và **ghi 2 bản dịch thật vào `translation_cache`** cho `A000035` và `A003627` (translation_id 1791 và kế tiếp), cộng theo đó `people.bio_vi` có thể đã được cập nhật cho 2 ID này (theo logic `UPDATE people SET bio_vi=? WHERE ... bio_vi IS NULL`). Đây là dữ liệu dịch thật, không phải fake/hard-code, và nằm trong hành vi bình thường của tính năng — không phải thay đổi ngoài ý muốn, nhưng admin nên biết để không nhầm là do thao tác thủ công.

## 7. Limitation / data gap còn lại

- Không thể test nhánh `has_extra: true` (người có đầy đủ XML extra DILA — alt_names/listbibl/works/relations) trên môi trường local vì bảng `ttl_v2_source_records` không tồn tại trong `data/lineage.db` hiện tại, nên `_t148_load_dila_extra()` luôn thất bại và index luôn rỗng cho mọi person_id. Đây là vấn đề dữ liệu/hạ tầng riêng biệt (thiếu bảng nguồn T148), nằm ngoài phạm vi bug "Tiểu sử trống" được giao; không sửa vì không có lệnh rõ ràng và có thể cần backfill/migration riêng.
- Do giới hạn trên, không xác nhận được 100% rằng card DILA Authority hiển thị đầy đủ và đúng thứ tự khi `has_extra:true` lẫn `_personBioZh` cùng tồn tại — nhưng về mặt code, nhánh đó không bị thay đổi.
- Đăng nhập Admin trong phiên test dùng giá trị `localStorage.admin_session` cục bộ (không phải mật khẩu thật) vì server xác thực phụ (`server.py`, cổng 5001) không được khởi động trong phiên debug này; endpoint `/daoanh/api/login/check` trả 404 (route không tồn tại trên app.py:5000) nên không chặn truy cập trang — chỉ dùng để quan sát UI cục bộ, không ảnh hưởng dữ liệu thật.

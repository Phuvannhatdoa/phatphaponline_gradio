# Thẩm định kế hoạch "DILA Place Translation bằng Gemini" (2026-10-21)

**Người thẩm định:** Claude Code (RC). **Chế độ:** chỉ đọc (DB `data/lineage.db`, XML DILA, scripts, tasks). Chưa tạo file pipeline, chưa gọi Gemini.

## Kết luận

Nguyên tắc của kế hoạch **đúng chuẩn**: theo lô, JSON có `dila_id`, đối chiếu với XML, `status = draft`, `--resume`, log lỗi, pilot 100 ID, không tự nâng `verified`.

Nhưng có **3 lỗi logic lớn** và **7 điểm cần bổ sung**. Lỗi lớn nhất: kế hoạch viết như thể chưa có gì, trong khi **dự án đã có pipeline Gemini cho địa danh và đã chạy được 28%**. Đợt chạy đó lại đang có lỗi ID, đúng loại lỗi mà kế hoạch muốn chặn.

## Số liệu thực tế (đo 2026-10-21)

| Câu hỏi của kế hoạch | Trả lời |
|---|---|
| File XML chứa `<place xml:id="PL…">` | **2 bản khác nhau** của cùng file `Buddhist_Studies_Place_Authority.xml`: (1) `data/dila_import/authority_place.2026-10/` — 31,1 MB, **59.375** place (bản mới); (2) `data/dila_temp/` — 31,0 MB, **59.167** place, khớp DB |
| Tổng place trong DB | `places_dila` **59.167** (ID dài `PL000000000001`); 17 place không có chữ Hán |
| Đã có tên Việt | `namevi_map_places`: gần như mọi place đã có tên Việt **phiên âm tự động** (≈118K dòng, mỗi place 2 lần theo 2 dạng ID); chỉ 6 dòng `reviewed` |
| Đã có bản Gemini | `ai_place_name`: **16.665 dòng** (model `gemini-3.1-flash-lite`, chạy 2026-10-20 11:29 → 19:00), bằng script có sẵn `scripts/ai_batch_transliterate_places_districts.py` (lô 50, có resume, retry 429) |
| **ID sai trong bản Gemini** | **3.800 / 16.665 dòng có ID 12 ký tự** (ví dụ `PL0000012606`), không khớp XML hay DB. Chỉ 12.865 dòng khớp `places_dila` |
| Chưa có bản Gemini (đúng ID) | ≈ **46.300** place (59.167 − 12.865) |

## 3 lỗi logic lớn

### 1. Trùng việc: đã có pipeline, đã có task

Trên máy đã có:
- script `ai_batch_transliterate_places_districts.py`;
- bảng `ai_place_name`;
- chuỗi task **T442** (phân tích XML), **T443** (import bản Claude), **T444** (Gemini batch places + districts).

Viết thêm 3 script mới (`dila_extract.py`, `dila_gemini_translate.py`, `dila_validate_import.py`) cùng bảng draft mới sẽ tạo **pipeline thứ 3** ghi vào chỗ khác. Hậu quả: 2 nguồn "Gemini" lệch nhau trên tab Place (T427).

→ **Sửa:** gộp kế hoạch này vào **T444**. Nâng cấp script hiện có theo các luật của kế hoạch, hoặc thay script đó bằng 3 script mới nhưng **ghi cùng bảng `ai_place_name`**. Tab Place (T427) đọc đúng một nguồn Gemini.

### 2. "Lọc ID chưa có bản dịch" sẽ ra 0

Theo DB, mọi place **đã có** tên Việt (phiên âm tự động trong `namevi_map_places`). Lọc theo nghĩa "chưa có bản dịch" thì không còn ID nào để gửi.

→ **Sửa định nghĩa:** "chưa dịch" = **chưa có bản Gemini hợp lệ trong `ai_place_name`** (ID 14 ký tự, khớp XML). Bản phiên âm tự động là cột riêng ("name_vi hiện tại" ở T427), không tính là đã dịch.

### 3. Đợt chạy hôm qua đã vi phạm chính luật "dila_id phải khớp XML"

3.800 dòng ID 12 ký tự là lỗi định dạng ID khi ghi (nghi bị cắt hoặc ghép sai chuỗi `PL` + số).

→ **Trước khi chạy tiếp:**
- (a) **dừng** script cũ nếu còn chạy;
- (b) ghi 3.800 dòng này ra `output/bad_ids.csv`;
- (c) thử ánh xạ lại về ID 14 ký tự **chỉ khi** chữ Hán khớp 1–1; không khớp thì đánh dấu để dịch lại;
- (d) thêm kiểm tra ID ngay trong script.

Việc này ghi DB, nên **cần Admin duyệt** và backup trước.

## 7 điểm cần bổ sung

1. **Chọn bản XML.** Bản 2026-10 có 59.375 place (nhiều hơn DB 208). Phải chọn 1 bản làm chuẩn đối chiếu, ghi SHA-256. Đề xuất: dùng bản **khớp DB (59.167)** cho đợt này; 208 place mới để task import DILA riêng.
2. **`ai_place_name` thiếu cột** cho luật của kế hoạch (`status`, `needs_review`, `confidence`, `reason`, `name_zh_echo`, `batch_id`). Thêm cột là **đổi schema**, cần Admin duyệt (additive, có backup).

   Script cũ dùng `INSERT OR REPLACE`, nên `--reset` có thể ghi đè. Sửa thành chỉ ghi khi chưa có hoặc đang `draft`, đúng luật "không ghi đè verified/canonical".
3. **Đối chiếu thêm chữ Hán trả về.** Chỉ khớp `dila_id` chưa đủ: model có thể trả đúng ID nhưng tên của dòng khác (lệch hàng trong lô). Yêu cầu Gemini **trả lại `placeName_zh`** và chỉ nhận khi khớp đúng chữ Hán đã gửi.

   Thêm kiểm tra **số chữ Hán = số âm tiết Việt**. Lệch thì `needs_review = 1`.
4. **`needs_review` không dựa vào điểm tin cậy tự chấm của Gemini.** Điểm `confidence` do LLM tự chấm không đáng tin. Đặt `needs_review = 1` theo luật máy kiểm được: lệch âm tiết, chữ hiếm hoặc gaiji, khác lexicon, tên nước / địa danh Ấn Độ có tên Việt quen dùng (ví dụ 舍衛國 → "Xá Vệ quốc"). Điểm của Gemini chỉ lưu tham khảo.
5. **"Dịch" hay "phiên âm".** Quy tắc hệ thống là phiên âm Hán–Việt (寺 → Tự, 山 → Sơn), không dịch nghĩa. Prompt phải nói rõ "phiên âm Hán–Việt chuẩn Phật học, ưu tiên lexicon nội bộ". Lexicon (166K mục) nên tra **trước khi gửi**: tên khớp lexicon thì không cần gọi Gemini, vừa tiết kiệm vừa chính xác hơn.
6. **Mẫu 100 không nên là "100 ID đầu tiên".** ID đầu là các nước cổ Ấn Độ / Tây Vực, không đại diện. Đề xuất mẫu phân tầng:
   - 40 chùa / núi Trung Hoa;
   - 20 địa danh Ấn Độ / Tây Vực;
   - 20 đơn vị hành chính;
   - 10 có gaiji / chữ hiếm;
   - 10 lấy từ 12.865 dòng Gemini đã có (so cũ / mới).
7. **Hạn mức và chi phí.** Còn ≈ 46.300 place, tức ≈ 1.850 request với lô 25 (≈ 930 với lô 50). Phải xác nhận đang dùng gói miễn phí và hạn mức theo ngày của model trong `.env`. `--max-requests` nên mặc định theo hạn mức ngày. Lỗi 429 "hết hạn mức ngày" thì **dừng tới hôm sau**, không thử lại sau 60 giây.

## Điểm nhỏ

- `data/chunks/` không cần, vì tiến độ đã nằm trong DB (resume theo bảng). Giữ thì chỉ để debug.
- `output/` mới ở gốc dự án: nên đặt `docs/sessions/2026-10-21/T444/` hoặc `data/exports/` theo quy ước repo, tránh thư mục app tự quét.
- Districts (16.907, `ai_district_name` mới 5 dòng) nằm ngoài phạm vi kế hoạch này. Ghi rõ là để sau.
- Vai trò: kế hoạch ghi "Claude Code chạy". Theo quy trình dự án, RC lập kế hoạch; `daoanh-debugger` sửa script và chạy pilot; `daoanh-qa` kiểm.

## Đề xuất thực hiện (thay cho "APPROVE" chung)

| Bước | Việc | Ghi DB? |
|---|---|---|
| A | Dừng script cũ nếu còn chạy; báo cáo 3.800 ID lỗi (CSV) | Không |
| B | Gộp vào **T444**: nâng script theo luật kế hoạch (kiểm ID + chữ Hán echo, lexicon trước, `needs_review` theo luật, không ghi đè) | Không |
| C | Admin duyệt: thêm cột cho `ai_place_name` + xử lý 3.800 dòng lỗi (backup trước) | **Có**, chờ duyệt |
| D | Pilot 100 ID phân tầng → `sample_100.csv` + báo cáo; **dừng chờ Admin duyệt mẫu** | Có (draft) |
| E | Chạy phần còn lại theo hạn mức ngày, `--resume` | Có (draft) |
| F | `dila_validate_import.py`: đối chiếu XML ↔ DB, `missing_ids.csv`, `duplicate_ids.csv`, `dila_place_draft_full.csv`; không nâng `verified` | Không |

---

## Phụ lục A — Kết quả agent đọc cấu trúc DB (2026-10-21, chỉ đọc)

### ID hỏng trong `ai_place_name`

- **3.800 ID hỏng đều cùng một kiểu:** thiếu 2 số "00" (`PL0000012606` = `PL000000012606`). Đệm lại thì **3.800 / 3.800 khớp** một địa danh thật, và bản phiên âm vẫn đúng chỗ (kiểm 5 mẫu, đếm âm tiết).
- **160 ID trùng sau khi đệm:**
  - 150 dòng giống hệt bản đúng.
  - **10 dòng khác nhau**, đều là chữ 場: một bản ghi "Trường", bản kia ghi "Tràng".

### Nguyên nhân lỗi trong script cũ

- Script nhận ID do Gemini chép lại mà không đối chiếu với ID đã gửi (dòng 171–180, 273–277). Gemini đôi khi chép rút gọn ID.
- Bộ đếm "đã làm" tính cả dòng hỏng, nên các place đó bị gửi lại: tốn hạn mức, và log báo 16.915 trong khi bảng thật chỉ có 16.665.
- Hiện script không chạy. Lượt cuối dừng giữa chừng lúc 2026-10-20 19:00.
- Phiên âm người (T418 Part 2) đã xong 48.673 / 48.673.

### Số liệu và lệch quy trình

- **Đã có tên Gemini thật:** 16.505 / 59.150 place.
- **Còn thiếu:** 42.645 place.
- **Lệch quy trình:** script đã chạy 16.665 dòng trong khi T444 vẫn `pending`, `dispatch: null`; T443 (bước phụ thuộc) chưa làm; không thấy bản backup.

### Quy tắc dịch (bảng `translation_rules`)

- **Tổng:** 137 rule, 136 đang bật; khoảng 30 rule liên quan địa danh (HANVIET_PLACES, PLACE_TERMS, RULE-005, RULE-012…).
- **Cần Admin sửa trước khi đưa vào prompt:**
  - 7 rule có vẻ sai:

    | Chữ Hán | Rule đang ghi | Có lẽ đúng là |
    |---|---|---|
    | 瑯琊 | "Lang Ya" (pinyin) | Lang Gia |
    | 鄴都 | Yên Đô | Nghiệp Đô |
    | 衡嶽 | Hằng Nhạc | Hành Nhạc |
    | 相部 | Tông Bộ | Tướng Bộ |
    | 子璿 | Tử Xuy | Tử Tuyền |
    | 契宗 | Tế Tông | Khế Tông |
    | 行事鈔 | Hành Sự Sào | Hành Sự Sao |

  - 2 rule rỗng nội dung: NO_PINYIN và HANVIET_NAMES (`_keep_`).
  - Code ghi vào cột `match_scope`, nhưng bảng không có cột này.

### Lexicon

- **Quy mô:** 166.278 mục, **20 nguồn** (Admin nói 22, cần xác nhận 2 nguồn còn thiếu).
- **Cấu trúc:** `term` là tiếng Việt, chữ Hán nằm trong `definition`. Vì vậy hàm `_lex_lookup` hiện tại chỉ tra được theo tên Việt.
- **Khớp "đầu mục":** (definition mở đầu bằng đúng chữ Hán) phủ được **2.446 place**. Ví dụ: 西禪寺 → Tây Thiền Tự, 龍編 → Long Biên.
- **Bảng âm từng chữ:** 1.991 chữ, trong đó 155 chữ có nhiều âm (đa âm).

### Lỗi khác phát hiện kèm

- `namevi_map_places` gắn `source_id = 1` (DILA) cho 118.293 tên do ZQ phiên âm tự động. Điều này trái quy tắc ZQLOCAL = 5.
- `local_gateway.py` đang chạy 3 tiến trình trùng.

## Phụ lục B — Giải pháp tối ưu đề xuất (một pipeline duy nhất, nâng T444)

| Bước | Việc | Ghi DB | Duyệt |
|---|---|---|---|
| B0 | Backup DB (SQLite API + quick_check) | — | — |
| B1 | Sửa 3.800 ID hỏng: đệm lại thành 14 ký tự. Xoá 150 bản trùng giống hệt. 10 ca 場 Trường/Tràng để `needs_review`. Ghi manifest để rollback | Có | Admin |
| B2 | Thêm cột cho `ai_place_name`: `status` (draft), `method` (lexicon / llm), `needs_review`, `review_reasons`, `name_zh_echo`, `batch_id`, `rule_version`, `prompt_version` | Có (đổi schema) | Admin |
| B3 | Lượt **lexicon miễn phí** (không gọi Gemini): 2.446 place khớp đầu mục → `method = lexicon`, `status = draft`. Khi 2 từ điển cho 2 âm khác nhau → `needs_review` | Có (draft) | — |
| B4 | Admin sửa 7 rule nghi sai + 2 rule rỗng. Pipeline nạp các rule đang bật của địa danh và rule chung vào prompt, ghi `rule_version` | Không | Admin |
| B5 | Gemini theo **lô N** (`--batch-size N`, mặc định 50; pilot thử cả N = 25 và 50 để so tỷ lệ lỗi) | Có (draft) | — |
| B6 | **Mỗi dòng phải qua 6 cổng**, rớt cổng nào thì không ghi hoặc đặt `needs_review` | — | — |
| B7 | Pilot **100 place phân tầng** → `sample_100.csv`, kèm cột so với bản tự động và bản lexicon. **Dừng chờ Admin duyệt** | Có (draft) | Admin |
| B8 | Chạy phần còn lại (≈ 42.645 − 2.446 ≈ 40.200 place ≈ 800 request với N = 50) theo hạn mức ngày, chạy tiếp được bằng `--resume` | Có (draft) | — |
| B9 | `dila_validate_import.py`: đối chiếu XML (`data/dila_temp`, 59.167, có hash) với DB → `missing_ids.csv`, `duplicate_ids.csv`, `dila_place_draft_full.csv`. Không nâng `verified` | Không | — |

**6 cổng của bước B6:**
1. ID nằm trong lô đã gửi.
2. Chữ Hán Gemini trả về (echo) đúng chữ Hán đã gửi.
3. Số âm tiết bằng số chữ Hán.
4. Không có pinyin hoặc chữ Latin lạ.
5. Có chữ đa âm (155 chữ) → `needs_review`.
6. Khác bản lexicon → `needs_review`.

**Xử lý lỗi hạn mức (B5, B8):**
- 429 theo phút: chờ 60 giây, thử lại tối đa 3 lần.
- 429 hết hạn mức ngày: dừng an toàn, mai chạy tiếp.

**Nơi hiển thị:**
- Tab Place (T427): cột "Gemini" đọc `ai_place_name` (cả `method = lexicon` có badge riêng); cột "Claude" đọc `codex_place_name` (T443).
- Admin sửa tay vẫn ghi vào `namevi_map_places`, theo quyết định ở T427.

**Tách task riêng:**
- `source_id` sai ở `namevi_map_places`.
- Dọn 3 tiến trình `local_gateway` trùng.
- Sửa cột `match_scope` của `translation_rules`.

# Session 2026-09-05 — T95 Build 5: LIVE Groq pilot + hiệu chỉnh validation + fix raw-audit ADS

**Ngày:** 2026-09-05 (tiếp nối `2026-09-05_T95_build4_phaseE.md`)
**Trạng thái:** T95 LIVE VERIFIED ✅ — key dev được cấp; chuỗi Groq thật chạy; 11 bản dịch live trong DB

## 1. Key dev (an toàn key)
- Admin cấp `GROQ_API_KEY` (dev free test). Được lưu **chỉ trong** `data/llm_config.json` (đã xác minh file này **không được git track** — `.gitignore: data/`; `git ls-files` báo "did not match"). KHÔNG commit/lộ key.
- `check-key` PASS → model mặc định `qwen/qwen3.8-27b`.

## 2. Live pilot — job `page:0-0484c-` (DoD)
- `new-job T50n2060 --scope page:0-0484c-` → **9 item**, chạy live (`mock=False`).
- Lần chạy đầu **fail 9/9**: validation gate từ chối `tỉ lệ ký tự 4.90/5.32/6.06 ngoài [0.6-4.0]`.
- Điều tra (gọi Groq trực tiếp in raw output): **bản dịch CHẤT LƯỢNG TỐT** (Hán văn cổ cô đọng → văn học Việt nở dài 4.7-5.8x là CHUẨN, không phải echo/hallucinate).
- **Fix gate:** `RATIO_MAX` 4.0 → **8.0** (comment evidence trong worker; echo Hán vẫn bị chặn riêng bằng `zh_norm(vi)==zh`).
- Chạy lại → **9/9 committed live** `cbeta:T50n2060:t001947..t001955:r001` (quality `unreviewed`, provider `groq`).

## 3. Smoke thêm (key không tốn) + bằng chứng resume skip
- `n:2` → 2 bản live `t000001..t000002:r001` (đầu tác phẩm, page 0425b).
- `n:1` → 1 item đã có bản dịch (cùng hash) → **`already_translated` skip**, completed 0 — xác nhận resume/skip hoạt động trên data THẬT.

## 4. Bug latent Phase C — raw audit bị ghi thành NTFS ADS
- Phát hiện: thư mục raw chỉ có **1 file 0 byte** tên `<job_id>`; các file item `job-x:1.json` "biến mất" khỏi `os.listdir`.
- Nguyên nhân: tên file chứa `:` (`job-...:1.json`) → trên Windows/NTFS `:` = cú pháp **Alternate Data Stream** → nội dung ghi vào stream vô hình trên file base 0 byte. **Admin monitor đếm file bị sai từ lúc Phase C.**
- **Fix:** `_raw_safe()` thay `:` → `_` trong `save_raw` (file thật mọi OS). Đã **materialize 12 stream cũ** (đọc stream bằng đường dẫn ADS → ghi file `.json` thật) + cập nhật `translation_job_items.raw_response_path` + xóa base file 0 byte rác.

## 5. Test đồng bộ
- `test_t95_18.py`: DB thật giờ có bản live → `fresh_db()` (bản SAO) **wipe 4 bảng dịch** để test luôn chạy với trạng thái sạch như thiết kế (không đụng live). **18/18 PASS** lại.
- `npm run test` ✅ · `npm run e2e` ✅ · `py_compile` worker+test ✅.

## 6. Trạng thái live DB hiện tại
- `translation_segments` T50n2060: **11 bản** (9 pilot page 0-0484c- + 2 đầu tác phẩm), `reviewed=0`, `missing=9305/9316`.
- Jobs: `132951584532` (completed 9/9), `134038125256` (completed 2/2), `134244395788` (completed 0 — skip).
- Raw audit: 12 file thật trong `data/raw_responses/`.

## 7. Rollback
- Code: `git revert <sha commit build5>` (worker gate + raw-save + test wipe). 
- **Bản dịch live:** muốn sạch pilot → `python scripts/cbeta_translate_worker.py revert-job --job <job_id>` (từng job) với xác nhận `y`; raw files trong `data/` (gitignored, nằm ngoài git).
- Key: xóa `groq_key` khỏi `data/llm_config.json`.

## 8. Việc còn lại
- Admin review 11 bản live (badge `needs_review` → hiệu đinh lên `validated/reviewed`).
- Quyết định giữ hay revert 2 bản ngoài pilot (`t000001/t000002`).
- Mở rộng dịch toàn work: chạy nhiều job theo `page:`/legacy — hiện `untranslated` cả work vẫn cần chú ý (9316 item, ~ 5-6 tiếng live) — nên theo trang.

## Commit dự kiến
`fix(T95): live pilot Groq 9/9 + RATIO_MAX 8.0 (Hán văn cổ) + raw-audit ADS fix (_raw_safe, materialize) + test wipe sạch + docs`
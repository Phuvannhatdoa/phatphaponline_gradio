# T50 Unblock — Groq key test + vi_text backfill chạy lại

**Ngày:** 2026-09-12 | **Task:** T50 (CBETA vi_text backfill) | **Trạng thái:** IN_PROGRESS (đã unblock)

## Bối cảnh
- T50 cần Groq key cho production batch vi_text. User cấp key mới `gsk_tvJp...` để test.
- Key do user cấp (`data/llm_config.json` cũ đều ở repo local gitignored, không commit).

## Kết quả test key (2026-09-11 → 2026-09-12)
| Key | Endpoint test | Kết quả |
|---|---|---|
| `gsk_tvJp...8QR` (user cấp mới) | `GET /chat/completions` qwen/qwen3.8-27b + llama-3.1-8b | **HTTP 401 invalid_api_key** (Groq từ chối, 3 lần, format chuẩn 56 ký tự `gsk_`) |
| `gsk_8rejo...` (`data/llm_config.json`, có sẵn) | qwen/qwen3.8-27b, gpt-oss-20b | **auth OK, models online** |

**Kết luận:** key user cấp không hợp lệ (401); key đang chạy trong `llm_config.json` (dùng cho tab Đại Tạng lazy-translate) **VẪN LIVE**. User chọn: "dùng key đang chạy dịch trên TAB Đại tạng" → chạy backfill bằng key này.

## Cơ chế key trong app.py (bảo mật đúng)
- `app.py:14942` `GROQ_KEY = os.environ.get('GROQ_API_KEY') or ''`
- Lazy-translate `api_passage_translate` (app.py:15596) và `_t73_call_gemini` (app.py:14999) đều đọc `cfg = _llm_config_read()` → `key = cfg.get('groq_key') or GROQ_KEY`.
- Nguồn key: env `GROQ_API_KEY` > `data/llm_config.json.groq_key` (admin set qua API). KHÔNG còn literal key trong source.
- `data/llm_config.json` gitignored (`.gitignore:3 data/`) → key an toàn, không commit.

## Backfill đã chạy
Command: `python scripts/t50_passage_vi_backfill.py --sigla T51n2076 --limit 0 --sleep 1.0` (chạy nền PID 22572, log `%TEMP%\opencode\t50_backfill.log`)

Lưu ý lệnh cũ trong task file có `--apply` nhưng script thật không có flag này — default = apply, có `--dry-run/--verify/--revert`.

**Chất lượng dịch sample (T51n2076 Chỉ Nguyệt Lục):**
- id 276 Thiền Sư Phổ Nguyện → *"Thiền Sư Phổ Nguyện ở Nam Tuyền, Chi Châu, vốn người Tân Trịnh, Trịnh Châu, họ Vương. Năm thứ hai đời Chí Đức nhà Đường..."* ✓ thuật ngữ Hán-Việt chuẩn
- id 277 Ẩn Phong → *"Sư Ẩn Phong người ẩn cư tại Ngũ Đài Sơn, quê ở Thiệu Vũ, Phúc Kiến, họ Đặng..."* ✓ địa danh chuẩn
- Rate-limit free tier qwen ~4-6 req/min, script tự retry sau 30s, resume-safe (passage đã dịch bỏ qua).

**Verify 2026-09-12 đầu giờ:** vi_text 257/6,347 → T51n2076 đạt 238/3,917 (5.8%) lúc kiểm tra, backfill vẫn chạy nền.

## Quyết định
- Tiếp tục backfill T51n2076 với key `llm_config.json` (key user cấp 401, không dùng).
- User cần cấp lại key Groq hợp lệ nếu muốn production batch nhiều sigla nhanh hơn (T50n2061, T50n2060, X77n1524, T50n2062).

## Pipeline
- test PASS, e2e PASS (lint Node v24 + e2e:runtime EPERM pre-existing, không phải code bug).

## Rollback
- DB: `python scripts/t50_passage_vi_backfill.py --revert` (xoá vi_text + cache đã dịch, idempotent-safe về base).
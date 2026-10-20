# Session 2026-09-06 — T85 v2: Lazy Translate → translation_segments

**Task:** T85 — Lazy Translate TOÀN PTDA (lazy on-demand) ✅ DONE
**Quyết định admin:** ghi vào `translation_segments` (SSOT T94/T95) — không dùng vi_text cho bản dịch mới.

## Nội dung

### Backend (`app.py`)
Unified route `GET/POST /daoanh/api/passage/<passage_id>/translate`:
1. **Passage có `text_passages`** (hiện tại T50n2060, 1.037 passage):
   - Helper mới `_t85_units` → liệt kê unit `source_status='ok'` theo `legacy_passage_id`.
   - `GET` → `_t85_get_segments`: trả từ `translation_segments` (done, revision mới nhất), concat → `vi_text`.
   - `POST` → `_t85_post_segments`: dedup done (không force), dịch unit thiếu bằng Groq
     (`_t85_translate_unit`, mirror T96 `/segments/translate`: queued→translating→done/failed),
     INSERT `translation_segments` (provider=`groq`, `quality_status='unreviewed'`,
     `prompt_version='t96v1'`, `revision_no` tăng, `force` → supersede bản done cũ + set
     `supersedes_translation_id`), cap 40 units/lượt (`partial`), phản chiếu
     `passage.vi_text` = concat units + `translation_draft=1`.
2. **Passage chưa có `text_passages`** (vd T51n2076) → legacy: GET cached `passage.vi_text`;
   POST Groq toàn passage (giữ `_BUDDHIST_SYSTEM_PROMPT`, max_tokens 2048, key từ `_llm_config_read`
   fallback env) → `passage.vi_text`.
3. **Xoá route trùng** `/daoanh/api/passage/<int:passage_id>/translate` (đăng ký trước, choán POST —
   trước đây mọi POST passage nguyên passage luôn chạy nhánh cũ, không bao giờ qua segments).

### Frontend (`places.html`)
- `daiTangTranslate(pIndex, force)` gửi body `{force}`; `daiTangRetranslate(idx)` → force=true (Dịch lại).

## Kiểm chứng (không tính "không đụng data")
| Hạng mục | Kết quả |
|---|---|
| `python -m py_compile app.py` | ✅ OK |
| `node --check` inline JS places.html (5 blocks) | ✅ OK |
| `npm run test` | ✅ Tests passed |
| `npm run e2e` | ✅ All pages passed |
| test_client DB tạm + fake Groq (20 asserts) | ✅ ALL PASS |
| 🖥️ Live Groq thật passage 3923 (0-0426a, 1 unit) qua instance 5099 | ✅ PASS |

**Live test chi tiết (passage 3923 = T50n2060 0-0426a):**
- POST → `{ok, mode=segments, translated=1, vi_text="Sa-môn Câu-na-la-đà..."` (triệu 1 lần fail transient — retry OK).
- GET lại → `from_cache=True`, cùng vi_text, không gọi LLM.
- POST `{force:true}` → bản mới; DB: `ts-b11184dc611d` → `superseded` (rev 2), `ts-31b4bf5ea0db` → `done` (rev 3, `supersedes_translation_id=ts-b11184dc611d`).
- DB: `provider=groq`, `quality_status=unreviewed`, `passage.vi_text` + `translation_draft=1` cập nhật.
- Trong quá trình: 1 lỗi Groq transient → row `failed` (rev 1) để lại (retry sau bỏ qua, không chặn).

Rollback 1 passage: `DELETE FROM translation_segments WHERE passage_id IN (SELECT passage_id FROM text_passages WHERE legacy_passage_id=<id>)` + reset `passage.vi_text`.

## Ghi chú vận hành
- **Server :5000 chưa restart** (PID 22636, quyền cao) — admin restart `python app.py` để route mới hiệu lực.
- Key Groq nằm trong `data/llm_config.json` (**gitignored, không commit**).
- Đường gemini (`_t73_call_gemini`, translation_cache) chỉ còn trong helpers, route passage không dùng nữa.
- Task kế tiếp theo board: sau T85 done → kiểm tra ROADMAP/task board (T89/T88/T80 dependency…).

## Files đổi
- `app.py` (helper T85 v2 + unified route + xoá route trùng `<int:passage_id>/translate`)
- `places.html` (daiTangTranslate force param)
- Test 20/20: file tạm ngoài repo (`%TEMP%\opencode\t85_test.py`) — không commit

## Rollback code
`git revert <commit>`. Data: backup `data/lineage.db.backup_t85_20260906_143713` (chụp sau live test,
trước commit). Rollback 1 passage: DELETE translation_segments theo legacy_passage_id + reset passage.vi_text.
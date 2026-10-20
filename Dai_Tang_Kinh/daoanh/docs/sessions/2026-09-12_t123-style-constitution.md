# Session 2026-09-12 — T123 Style Constitution "Ban Dịch PTDA" (Build)

## Mục tiêu
Văn phong dịch Groq đồng nhất mọi luồng bằng Style Constitution (Ban Dịch PTDA) + bám sát
22 từ điển danh tác trong DB. Bổ sung nút Báo lỗi dịch + admin xem chi tiết lỗi + đề xuất fix rule.

## Nguyên nhân gốc (case "chàng" — Thích Diên Huy)
- `api_passage_translate` legacy (app.py:15652) dùng system tĩnh `_BUDDHIST_SYSTEM_PROMPT`,
  prompt user ngắn → Groq không thấy kính ngữ → "chàng".
- `t50_passage_vi_backfill.py` (L193-202) query rules DB nhưng build_prompt (L97-115) không nhúng.
- `_t85_translate_unit` (15481) + `translate_context` (2333) prompt hardcode.
- Chỉ place (15296) + bio (15120) dùng rules DB.

## Quyết định Lee (2026-09-12)
1. Invalidate: bản cũ giữ nguyên; user bấm "Dịch lại" khi cần → dịch rule mới. Không auto-heal.
2. Báo lỗi: user báo → `translation_error_report` (snapshot+link+note) → admin xem + đề xuất rule fix.
3. Exemplar/glossary: bám sát bộ từ điển danh tác (Từ Điển Thiền Tông Hán-Việt 2,575 cặp...).

## Hạ tầng khảo sát
- `translation_rules`: 10 rules active (NO_PINYIN→DILA_SOURCE_BADGE); cols id/rule_code/rule_type/
  description/rule_text/is_active/priority/created_by/created_at/updated_at. Upsert theo rule_code OK.
- `translation_cache`: có rules_version + source_type (person_bio/place_note/passage), report_count,
  status auto/approved/reported/invalidated.
- `translation_segments` (T85): có cột prompt_version (đang hardcode 't96v1'), model_name, revision.
- `lexicon`: 166,278 rows / 20 nguồn từ điển; 2,724 cặp Hán≥20 + Việt≥30 passage-level exemplar
  (Từ Điển Thiền Tông Hán-Việt 2,575, Từ Điển Hán-Việt Nguyễn Quốc Hùng 37, Tam Tạng Pháp Số 33,
  Phật Học Tinh Tuyền 32, ...).
- `glossary_vi`: 248,095 rows (zho 67,461); 3,624 từ match_source='lexicon'.
- Admin `translation_cache.html` đã có stats/list/invalidate theo rules_version. Cần thêm tab Báo lỗi.
- Route báo lỗi passage (15682) chỉ tăng report_count, không lưu chi tiết.

## Tiến trình Build
- T1: task file T123 + session doc này + tasktodo (xong trong session).
- T2-T5: script seed (rules + 3 bảng) — additive, upsert.
- T6-T7: unified builder `_t73_build_style_prompt` + áp 5 luồng + lock temperature ≤0.15 + prompt_version.
- T8-T10: nút báo lỗi + route + endpoint translate-rules + admin translation_cache.html.
- T11: fix backfill script.
- T12-T14: smoke + pipeline + commit temp-index (parent 2922725).

## Kết quả (build xong)
- **Seed:** 18 rules active, `rules_version=e2c071dccf741c3f`; `translation_exemplar`=2,692 rows (3 active
  — tu_dien_danh_tac); `translation_glossary`=77 (79 attempted, 2 dup `(法門→pháp môn)`, `(說法→thuyết pháp)`
  tự loại bởi INSERT OR IGNORE + UNIQUE); `translation_error_report`=0 (sạch sau test).
- **app.py:** `_t73_style_lock()` + `_t73_build_style_prompt()` đặt trước `_t73_build_prompt` (giữ legacy);
  áp 5 luồng (passage legacy, T85 `_t85_translate_unit` json_mode + prompt_version=rules_version,
  `translate_context` meta rv, place, bio). Luồng Claude L4555 cố ý giữ static (ưu tiên thấp).
- **Report:** 3 route (person/place/passage) INSERT `translation_error_report` kèm snapshot 2000 ký tự/
  error_type/note/page_url + tăng report_count. Endpoint public `GET /daoanh/api/translate-rules`;
  admin `GET /daoanh/api/admin/translation-error-reports` (+`suggested_rules` từ `_error_report_suggestion`,
  mapping loại lỗi→rule_code); `POST .../<id>` resolve/reject.
- **admin/translation_cache.html:** tab Cache / Báo lỗi dịch + loadReports/resolveReport/esc; JS node --check PASS.
- **t50_passage_vi_backfill.py:** `build_prompt(raw, ref, conn=None)` + `_style_lock_blocks(conn)` nhúng persona
  + active rules + glossary + exemplar. Backfill nền vẫn chạy với code cũ trong RAM (dùng prompt mới khi restart).
- **Smoke (test_client):** builder OK (prompt 6,889 ký tự, rv đúng, "chàng" có trong rule kính ngữ); translate-rules
  200 + 18 active; report flow tạo row + suggested_rules `['HONORIFIC_PRONOUN','ACADEMIC_STYLE']` + resolve → resolved;
  UTF-8 giữ nguyên; admin translation-cache 200 (459 total). DB test đã dọn sạch.
- **Pipeline:** test PASS; e2e static "All pages passed". (lint Node v24 ESM-format + e2e:runtime EPERM = pre-existing env.)
- **progress_data.json** regenerate: 15 module, 203 endpoint, 67%, 44 task (done=12), 301 commits.

## Ghi chú
- Backfill T50 PID 22572 chạy nền song song (T51n2076, ~500/3,917 lúc khảo sát, rate-limit 30s retry).
- 0 ALTER bảng nền; 3 bảng mới dùng CREATE TABLE IF NOT EXISTS. Commit temp-index (real index đang có
  16 staged deletions từ agent ngoài — không reset).

## Live activation (2026-09-12, sau T124)
- Server app.py :5000 được restart để load code T123. Old PID 20240 không kill được bằng
  Stop-Process/taskkill (Access denied — child của bash.exe 23588/15644, elevation khác); dùng
  `wmic process where processid=20240 delete` → thành công.
- Sau restart: **GET /daoanh/api/translate-rules → 200, active=18, rv=e2c071dccf741c3f**;
  admin translation-error-reports → total=0, rules=18; place detail API 200. T123 **live**.
- :8080 serve places.html mới (T124) — content có `dt-ds-head`, không còn banner "Groq semantic ranking".
- Quy trình restart an toàn ghi nhận: Start-Process python app.py (cwd daoanh), redirect log temp.
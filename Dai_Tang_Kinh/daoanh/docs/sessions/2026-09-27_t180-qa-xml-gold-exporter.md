# Session 2026-09-27 — T180: QA thật XML (Phase 8a) + T167 Phase 8 GOLD exporter

**Kéo theo:** đóng sổ T178/T179 (tasktodo → done, taskdone entries, dashboard item 19/20/21).

## 1. QA THẬT Phase 8a — XML không làm hỏng bản dịch ✅ (6/6)

Dùng đúng đường production `app.py`: `_t73_style_lock` → `_t73_build_style_prompt` →
`_t73_call_gemini`. Fixture thật `A009460 丹霞天然` (vnpa `don_ha_thien_nhien`, verified),
source `天然和尚住丹山，後往江西，問道於馬大師。`

- **Prompt t165-v2 (XML):** 45 rules chọn · glossary 5 · codes 49 · constitution_hash `aa239d0c` ·
  prompt length **10.405 chars** · bọc đủ `<rules>/<glossary>/<exemplars>/<source>`.
- **Groq THẬT:** `qwen/qwen3.8-27b`, err=None, thời gian **4,1s**.
  Bản dịch: *"Hòa Thượng Thiên Nhiên trụ trì tại Đan Sơn, sau đó đến Giang Hữu, cầu hỏi đạo nơi
  Đại Sư Mã."* (92 chars).
- **Verify 6/6 PASS:** có nội dung tiếng Việt · **0 rò chữ Hán** · **0 rò thẻ XML sang bản dịch** ·
  không lọt câu lệnh prompt · không lặp nguyên văn Hán · có dấu tiếng Việt.
- **Metrics persisted (T178/T179):** `translation_prompt_metrics`: prompt_tokens **3403** ·
  completion 26 · total 3429 · source_len 20 · model `qwen/qwen3.8-27b` · **`prompt_fmt='t165-v2'`**.
- **Kết luận:** đóng nợ "QA 1 lần dịch thật" của T179 — XML không làm hỏng output, prompt mới
  (v1 ước lượng 1.106 → v2 955 token) vẫn cho bản dịch đúng; token thật 3403 nằm dưới ngân sách
  T177 D7 (3.400–3.700 baseline trung bình).
- **Ghi chú:** query baseline trả NULL (chưa có row MISS source_type ≠ qa) — chỉ báo mức, không
  hard-gate. Row QA persist vào DB production (append-only metrics, vô hại, có source_type đánh dấu).

## 2. T167 Phase 8 — GOLD dataset exporter ✅ (15/15, 0 bịa)

**File mới `scripts/buddhist_han_vi_bench/gold.py`** — `export_gold(human_path, set_path,
out_path, db_path, min_acceptance=4)`:

- **Chỉ L3 human-approved vào GOLD:** passage phải có ĐỦ 3 human metric (semantic_fidelity,
  doctrinal_fidelity, human_acceptance) trong `buddhist_han_vi_bench_human.json` VÀ
  `human_acceptance ≥ ngưỡng` (default 4/5). KHÔNG có → skip có lý do (summary counts).
- **Bản dịch final** lấy từ `translation_segments` (completed/reviewed, revision mới nhất —
  reuse query `score._latest_translation`).
- **Output JSONL** `buddhist_han_vi_bench_gold.jsonl` training-ready: mỗi record
  `{source, final_translation, provenance{passage_id,category,seq,loc_ref,juan,translation_id,
  source_type}, ruleset{ruleset_id,ruleset_version}, review{3 human metrics + reviewer +
  scored_at}}`. **Separable khỏi drafts** (chỉ chứa approved final).
- `ruleset_version` từ `translation_rulesets` (canonical `t167-constitution-v1`/`1.0.0`);
  ruleset_id từ segment, fallback DEFAULT_RULESET_ID.
- **`__main__.py`** thêm CLI `gold` (--human/--set/--out/--min-acceptance).
- **Test mới `tests/test_t167_gold.py` 15/15 PASS:** no-human → 0 GOLD (trung thực) · approved
  → record đúng 4 nhóm + review · acceptance < ngưỡng → skip rõ · chưa có bản dịch → skip rõ ·
  chạy 2 lần deterministic. Fixture: 2 passage thật trong bench có bản dịch completed/reviewed
  (p0001/p0002). Benchmark cũ 15/15 không regress. `py_compile` 3 file PASS.
- `package.json`: `test:t167` = benchmark + gold (pipeline tự đón).
- **Hiện trạng thật:** 0/500 GOLD (chưa có ai duyệt human scores — đúng quy trình, không ép).
  Quy trình: `human <passage_id> --sf … --df … --hs ... --reviewer giaotho` → `gold --min-acceptance 4`.

## 3. Đóng sổ T178/T179

- tasktodo: **T178** và **T179** → `✅ DONE — ĐÓNG` (ghi DONE+commit+QA thật ở đầu dòng),
  giữ nội dung phân tích.
- taskdone: thêm **T178** (nêu SAI của "KNOWN ARCH GAP" → do T179) và **T179** (đầy đủ ga + QA thật +
  GOLD exporter + revert).
- dashboard item **19**: thay KNOWN ARCH GAP bằng **ĐÍNH CHÍNH — ĐÃ SAI** (hash PER-ROW thỏa sẵn);
  item **20**: đánh ✅ Done + QA thật PASS; kick "Cần Admin quyết" → Done; thêm **item 21** QA XML + GOLD.

## 3b. CHƯA HOÀN THIỆN — làm sau (không phải code, chỉ testing/docs-chờ)

| # | Mục | Trạng thái | Ai làm | Lý do hoãn |
|---|-----|-----------|--------|-----------|
| 1 | ROLLBACK row cho commit `1be7ed7` (T180) | viết xong worktree `docs/ROLLBACK.md:10`, **chưa commit** | Tôi | Cùng file đang có row `<sha_t166_security>` chưa commit của agent khác — commit cả file sẽ cuốn việc họ; chờ agent kia commit trước rồi revert-commit row T180 |
| 2 | T73 Bio Review — QA browser | code xong, routes đã verify đủ | **Admin** | Cần người mở `:5000/daoanh/admin/bio-review` duyệt thử → xong mới đóng task |
| 3 | T167 GOLD human scores | 0/500 passage được duyệt | **Admin/giáo thọ** | Cần người chạy `human <passage_id> --sf ... --hs ...` → rồi tôi chạy `gold` |
| 4 | T180 row riêng ở tasktodo ACTIVE | đang gộp trong row T167 (line 23) | Tôi | Nhẹ — ghi thêm khi cần, không chặn ai |

Những mục này **0 liên quan code nữa** (testing + docs chờ người duyệt). Mọi code+test của T180 đã commit sạch `1be7ed7`.

## 4. Revert

- T180 (QA + GOLD): code + docs là **additive** (`gold.py` + `test_t167_gold.py` mới, sửa
  `__main__.py`/`package.json`/taskdoc/tasktodo/taskdone/dashboard/session). Revert =
  `git revert <sha_t180_build>` 1 commit; GOLD exporter không đụng DB (0 ALTER), human scores
  thuần data file.
- QA row trong DB (`qa_phase8_xml`) là append-only metrics — revert git không xoá; xoá tay nếu muốn
  (`DELETE FROM translation_prompt_metrics WHERE source_type='qa_phase8_xml'`), vô hại.

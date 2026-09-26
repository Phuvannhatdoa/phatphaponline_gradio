# CBETA Translation Pipeline Audit

**Task:** T95 — Phase A1 (audit code/data/logic)
**Ngày:** 2026-09-05
**Phương pháp:** đọc mã nguồn + truy vấn `data/lineage.db` thật + kiểm tra trang live :8080 (read-only, không thay đổi dữ liệu)

---

## 1. Mục đích

Xác định chính xác:
- ai chịu trách nhiệm từng bước trong pipeline Hán–Việt CBETA hiện tại;
- schema bảng đang dùng;
- cách Hán bị chia đoạn hiển thị;
- cách Việt bị chia block (và tại sao đã hết);
- giải thích báo cáo "Hán đoạn 09 lặp toàn văn 01–08";
- Groq được gọi theo full-text hay theo passage;
- raw response Groq lưu ở đâu;
- vị trí code cần loại bỏ character-ratio split (đã loại ở T94 Phase 2B).

## 2. Bản đồ code chịu trách nhiệm từng bước

| Bước | File / Function | Vai trò |
|------|-----------------|---------|
| Import/parse CBETA vào `passage` | `app.py` (import cũ) + bảng `passage` | 7,563 passage CBETA (paragraph/bio level) |
| API canon 3 lớp (Entity → Đại Tạng) | `app.py` `entity_canon` (~11530) | trả raw_text + vi_text + segments cho tab |
| Render tab Đại Tạng / Reader | `places.html` `renderDaiTangMain`, `dtRenderPassage`, `dtInitBilingualReader`, `openDaiTangReader` | UI song ngữ |
| Cũ: chia vi_text theo tỉ lệ ký tự | `places.html` `dtDistributeVi` | **ĐÃ XÓA** ở T94 Phase 2B (commit `641450f`) |
| Cũ: chia Hán hiển thị 01…09 | `places.html` `dtSegmentHan` (dấu câu + gom ≥50 ký tự) | còn lại để đọc, sẽ thay bằng đọc `text_passages` ở T95 |
| Dịch toàn-passage (lazy) | `app.py` `api_passage_translate` (~14178) | GET caches, POST Groq-on-miss; ghi `passage.vi_text`+`translation_draft=1` |
| Dịch batch (legacy reference) | `scripts/t50_passage_vi_backfill.py` | dịch từng passage → cache/revert |
| Cache T73/T74 (person/place bio) | `translation_cache` (225 rows) | content-address SHA256, không dùng cho passage mới |
| Groq client chung | `_t73_call_gemini` (app.py ~13809), `call_groq` (backfill) | POST https://api.groq.com/…/chat/completions, temp 0.1, max_tokens 2048, retry 429 (backfill) |

## 3. Schema đang dùng

### `passage` (legacy — canonical cho display hiện tại)
```
passage_id INTEGER PK, source, text_id, loc_ref, raw_text, norm_text,
vi_text, translation_draft, raw_zh_hash (cột mới T94 — chưa fill, 0/7563),
passage_id_ref, segmentation_method (cột mới T94 — chưa fill)
```
- 7,563 rows, `source='CBETA'`, 5 text_id: T51n2076 3,917 | T50n2061 1,346 |
  T50n2060 1,037 | X77n1524 1,016 | T50n2062 247.
- 218 rows có `vi_text` (toàn `translation_draft=1`).
- Không trùng raw_text (audit T94: 0 duplicate). `loc_ref` định dạng `0-0484c-`,
  riêng 622 rows `0--` (không có anchor trang).

### Bảng cấu trúc mới T94 (đã tạo, 0 rows)
- `text_passages`: passage_id TEXT PK, work_id, source_system, canonical_ref, juan,
  sequence_no, original_zh, raw_zh_hash, segmentation_method, tei_anchor_start/end,
  source_url, source_version, import_run_id, created_at. — **Chưa có** source_status,
  updated_at, canonical_start_anchor/end, legacy_passage_id, loc_ref.
- `translation_segments`: translation_id TEXT PK, work_id, language, translation_text,
  translator_type, model_name, prompt_version, source_passage_ids, translation_status,
  review_status, reviewer, created_at, updated_at. — **Chưa có** passage_id, provider,
  source_original_hash, quality_status, created_by_job_id, revision_no,
  supersedes_translation_id.
- `passage_translation_alignment`: alignment_id INTEGER PK AUTOINCREMENT, passage_id,
  translation_id, alignment_type, source_start_offset/end, confidence, alignment_method,
  review_status, reviewer, note, created_at. — **Chưa có** updated_at.
- **Không tồn tại** `translation_jobs`, `translation_job_items`.

## 4. Vì sao Hán bị hiển thị 01…09 (và tại sao đúng đắn cho đọc)

`dtSegmentHan` tách `raw_text` theo dấu câu `。；！？` rồi gom nhóm ≥50 ký tự → với
passage 4061 (`0-0484c-`, 480 ký tự) cho **9 đoạn Hán 01…09**. Đây là chia **chỉ
cho đọc** Hán, không có id ổn định, không có hash → không thể dùng làm khóa dịch.

## 5. Verify báo cáo "Hán đoạn 09 lặp toàn văn 01–08" → KHÔNG tái lập

Truy vấn DB thật passage 4061 (T50n2060 · 0-0484c-):

```
raw_len: 480   |   vi_len: 2386
first_half == second_half?  False
n occurrences đầu 50 ký tự: 1
seg 9 (đoạn 09): "脛臂無服生死齊焉。兼以心緣口授杜於文相者古今絕矣。" (25 ký tự — mới, không lặp)
```

→ 9 đoạn duy nhất, KHÔNG có đoạn nào lặp toàn văn 01–08. Đồng thời, trang live
:8080 (bản đã commit `641450f`) không còn `dtDistributeVi` / `≈` / `⚠ PHÂN PHỐI
TỰ ĐỘNG` / `Chưa có phần dịch tương ứng`. Kết luận: **báo cáo 09-lặp là stale
render của browser cache bản trang cũ**, không phải lỗi dữ liệu hiện tại. Không
tạo fix giả; vẫn xây importer idempotent kèm hash để phòng dữ liệu corrupt tương
lai (mục A2/A3 task T95).

## 6. Vì sao Việt trước đây ra 8 block "≈" (đã sửa)

`dtDistributeVi` cắt `vi_text` thành 9 nhóm theo **tỉ lệ ký tự giữa Hán/Việt** rồi
ghép ordinal → nhóm 9 có thể rỗng → "Chưa có phần dịch tương ứng." → UI thấy "8
block ≈". Root cause = ordinal-join hai cách chia khác nhau (Hán theo dấu câu, Việt
theo tỉ lệ ký tự). `dtDistributeVi` **đã xóa hẳn** (T94 Phase 2B), Việt giờ là 1
khối faithful cho toàn passage.

## 7. Groq được gọi theo full-text hay theo passage

- **Hiện tại: full passage — 1 passage / 1 call.** `api_passage_translate` gửi
  toàn `raw_text` (một passage legacy, có thể tới 8,034 ký tự T50n2060) làm input,
  nhận 1 `translation_vi` → ghi `passage.vi_text`. **Không chia theo passage atom.**
- `t50_passage_vi_backfill.py` cũng 1 passage 1 call (có retry 429 + cache).
- → Pipeline mới T95 sẽ dịch theo **đoạn con ổn định** (25–60 ký tự, batch 1–5,
  context hàng xóm read-only), đúng khuyến nghị "không dịch cả khối rồi cắt lại".

## 8. Raw response Groq đang lưu ở đâu

- `translation_cache` (225 rows): lưu `source_text` + `translated_text` +
  `model_id` + `rules_version` — **text thuần, không lưu raw JSON response đầy đủ**.
- `passage.vi_text`: kết quả cuối.
- `scripts/t50_passage_vi_backfill.py`: không lưu raw response riêng (chỉ cache +
  vi_text).
- → T95 cần `translation_job_items.raw_response_path` + audit raw request/response
  (yêu cầu §8 pipeline).

## 9. Vị trí code character-ratio split cần rà soát

| Nơi | Trạng thái |
|-----|-----------|
| `places.html` `dtDistributeVi` | ✅ Đã xóa (T94 Phase 2B) |
| `places.html` các nhãn `≈`, `⚠ PHÂN PHỐI TỰ ĐỘNG…`, `Chưa có phần dịch tương ứng` | ✅ Đã xóa |
| `dtSegmentHan` (chia Hán hiển thị) | ⏳ Giữ tạm khi đọc; T95 thay bằng render trực tiếp từ `text_passages` |
| Backend chia/ghép lại Vi theo tỉ lệ ký tự | ❌ Không tồn tại (chưa bao giờ có ở backend) |
| Ghép ordinal Hán↔Việt | ✅ Đã bỏ (T94 Phase 2B) |

## 10. Kết luận & khuyến nghị build

1. Không có dữ liệu corrupt; không cần xóa data production.
2. Hiện trạng "chia lại theo tỉ lệ ký tự" đã thanh toán xong ở UI; phần còn thiếu
   là **hạ tầng dịch theo passage atom + resume + style-lock** (T95).
3. Ưu tiên: importer `text_passages` → schema extension → Groq worker →
   UI paired view → export/admin.
4. Báo cáo manual `T50n2060 · 0-0484c-`: passage 4061 tạo 9 `text_passage` id
   `daoanh:cbeta:T50n2060:0484c:p0001…p0009` kèm hash + anchor, không duplicate —
   đây là ca test chuẩn của T95.

## 11. Files liên quan

- Task: `tasks/T95-cbeta-translation-pipeline.md`
- Architecture: `docs/cbeta_bilingual_translation_architecture.md`
- Trước đó: `docs/cbeta-corpus-audit-results-20260904.md`, `tasks/T94-cbeta-alignment-schema.md`
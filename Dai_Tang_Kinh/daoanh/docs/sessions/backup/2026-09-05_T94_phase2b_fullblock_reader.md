# Session 2026-09-05 — T94 Phase 2B: Reader faithful (bỏ cắt tỉ lệ ký tự)

**Task:** T94 — Phase 2B · Reader fix hoàn tất
**Module:** CBETA Core / Bilingual Reader
**Files đổi:** `daoanh/places.html`
**Docs đổi:** `tasks/T94-cbeta-alignment-schema.md`, `docs/tasktodo.md`, `docs/progress.md`

---

## Bối cảnh

Admin gửi lại báo cáo lỗi alignment Hán–Việt (Hán đoạn 41 T50n2060 ≠ Việt đoạn 41)
kèm yêu cầu **kiểm chứng logic**. Agent thực hiện audit code + DB thật, kết luận:

| Kiểm chứng | Kết quả |
|---|---|
| Hán seg 41 = "創翻大本。至龍朔三年十月末了。凡四處十六會說…" | ✅ ĐÚNG |
| Việt group 41 = "Năm Hiển Khánh thứ hai, giá hạnh Lạc…" | ✅ ĐÚNG (lệch nội dung) |
| `dtSegmentHan` = 54 đoạn (dấu câu `。；！？` + gom 50 ký tự) | ✅ |
| Việt 108 câu → `dtDistributeVi` ép 54 nhóm theo tỉ lệ ký tự | ✅ |
| Nhóm 42–54 rỗng → "Chưa có bản dịch tương ứng" (13 đoạn) | ✅ |
| Root cause = ordinal-join 2 cách chia đoạn khác nhau | ✅ ĐÚNG |

**Đính chính quan trọng:**
1. UI **đã có cảnh báo** từ trước (`⚠ PHÂN PHỐI TỰ ĐỘNG...`, `≈`) — không trình bày
   như căn chỉnh xác nhận; nhưng số cạnh nhau vẫn gây ấn tượng sai → vẫn cần sửa tiếp.
2. **Mọi evidence học thuật (Truyền Thừa/Nexus) trỏ `passage_id`/`loc_ref` cấp passage**,
   KHÔNG trỏ số segment hiển thị → cốt lõi không bị ảnh hưởng.
3. Chỉ 13/1,037 passage T50n2060 có `vi_text` (toàn AI draft) — phạm vi lỗi nhỏ.

## Thay đổi code (Tầng 1 — theo phương án admin duyệt)

`places.html`:

1. **Xóa hẳn `dtDistributeVi()`** (hàm phân phối Vi theo tỉ lệ ký tự — nguồn lỗi).
2. **`dtBuildSegments()`** giảm xuống chỉ build segment Hán:
   `target_text_vi: null`, `alignment_status: 'text_only'` (bỏ ordinal mapping Việt).
3. **Việt pane render mới** trong `dtRenderPassage`:
   - Badge `🤖 BẢN DỊCH AI NHÁP` / `✓ BẢN DỊCH THAM KHẢO` (giữ nguyên)
   - Provenance: `📌 Bản dịch TOÀN PHẦN passage <text_id> · <loc_ref> · passage_id <id> — không chia theo số đoạn Hán`
   - Toàn văn `vi_text` = **1 khối liên tục** (`white-space:pre-wrap`), dấu `¶`
   - Bỏ note `⚠ PHÂN PHỐI TỰ ĐỘNG...` + nhãn `≈` per-seg + các segment `Chưa có phần dịch tương ứng`
4. Hover sync (`dtInitBilingualReader`) tự vô hiệu với Việt: khối toàn văn không có `data-seg`
   → không còn liên kết giả Hán↔Việt.

Không đổi DB, không đổi API, không đổi `passage.vi_text` (bản dịch toàn passage vốn đúng cấp model).

## Verify

- `node --check` toàn bộ inline script places.html: PASS (1 block, 0 lỗi)
- Playwright live trên localhost:8080, gọi `renderDaiTangMain` → `dtRenderPassage`
  với passage thật 3951 (T50n2060 · 0-0457a-):
  - `viHasFullBlock: true`, `viHasPassageMeta: true`, `viHasPermark: true`
  - `viHasOldNote: false`, `viHasOldSeg: false`, `viBlocks: 1`
  - Hán pane render bình thường (segments có)
  - `ERRORS: []` — không console/page error
  - Kết quả: **PASS**

## Trạng thái tiếp theo

- T94 vẫn `in_progress` — còn: fill alignment table khi user "Báo sai" (admin verify → INSERT
  `passage_translation_alignment`), lazy translate (T85) cho passages NULL giữ nguyên.
- Với passage có `alignment_type='manual_verified'` → frontend sau này hiển thị số thật.

## Rollback

- `git revert HEAD` (đưa về trước commit Phase 2B)
- Phase 1 schema: `python scripts/t94_create_alignment_schema.py --revert` (nếu cần)
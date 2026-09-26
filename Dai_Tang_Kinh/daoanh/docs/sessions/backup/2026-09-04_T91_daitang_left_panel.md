# Session 2026-09-04 — T91: Refactor Panel Trái Tab Đại Tạng + Fix Groq Translate

## Kết quả

**T91 DONE** — Panel trái `#tp-daitang` đã được tái cấu trúc theo thứ tự ưu tiên mới.

## Thay đổi

### Bỏ khỏi panel trái

- LỚP 1 · NGUỒN DẪN ĐẠI TẠNG (CBETA/FOSIZHI ref list)
- LỚP 2 · ĐOẠN VĂN LIÊN QUAN (Hán văn passage cards + pagination)
- LỚP 3 · THÔNG TIN TÁC PHẨM (canon catalog)
- Sidebar HỒ SƠ LIÊN KẾT

> Các nội dung này đã có sẵn trong main panel 5-tab (Dẫn Chiếu / Nguyên Văn / Quan Hệ)
> nên không cần hiển thị thêm ở panel trái.

### Thêm vào panel trái (thứ tự từ trên xuống)

1. **Header + Nguồn Học Thuật** (authority_sources chips) — giữ nguyên
2. **Bảng thống kê** (4 stat cards: DẪN CHIẾU DILA / ĐOẠN VĂN / TÁC PHẨM / BẢN DỊCH VIỆT) — giữ nguyên
3. **👤 NGƯỜI SÁNG LẬP** — async fetch từ `/api/entity/<id>/related`, hiển thị curated persons (`source='curated'`) với tên Hán + Việt + dynasty + relation_type
4. **🔗 LIÊN QUAN** — canonical persons + places từ cùng related API
5. **📚 ĐẠI TẠNG KINH NGUYỄN MINH TIẾN** — placeholder (chưa có dữ liệu trong DB)

### Hàm mới

- `_dtRenderLeftRelated(rd, ent)`: populate `#dt-left-founders` và `#dt-left-related` sau khi fetch `/related`

## Bug fix trong quá trình

1. `rd.success` không tồn tại trong related API response → bỏ guard `!rd.success`
2. Badge field là `source` ("curated"/"canonical"), không phải `badge` ("CURATED") → fix filter condition

## Verify kết quả (Thiếu Lâm Tự — PL000000023255)

- 👤 NGƯỜI SÁNG LẬP: 壁觀婆羅門 / Bích Quan Bà La Môn (curated, thiền định / dạy thiền tông · 南梁)
- 🔗 LIÊN QUAN: 三藏/Tam Tạng + 12 canonical persons + địa danh co-mentioned
- 📚 Nguyễn Minh Tiến: placeholder "Đang khảo cứu"
- Main panel 5-tab (Dẫn Chiếu 49, Nguyên Văn 15, Quan Hệ) không bị ảnh hưởng

## Files đã sửa

- `daoanh/places.html`: refactor `renderDaiTangTab` + thêm `_dtRenderLeftRelated`

---

## Fix thêm: Button "🤖 Dịch (AI)" — Nguyên Văn Tab

### Vấn đề

Route `POST /daoanh/api/passage/<id>/translate` (`app.py` line 4175) dùng `ANTHROPIC_KEY` (không cấu hình)
→ trả về 503 `{"ok":false,"error":"ANTHROPIC_KEY chưa cấu hình"}` cho mọi request dịch.

### Fix

Thay toàn bộ Anthropic SDK block bằng Groq API call (dùng `GROQ_KEY`, `GROQ_MODEL`, `GROQ_URL`
đã hardcode tại line 13695-13697) — cùng pattern với các Groq call khác trong app.py.

`app.py` line 4198-4214 sau khi sửa:
- Check `if not GROQ_KEY` → 503
- `requests.post(GROQ_URL, ...)` với model `qwen/qwen3.8-27b`
- System prompt: `_BUDDHIST_SYSTEM_PROMPT` (định nghĩa tại line 4164)
- Parse `result['choices'][0]['message']['content']`
- Lưu `vi_text` vào DB bảng `passage` + `translation_draft=1`

### Verify

```
POST /daoanh/api/passage/4313/translate → HTTP 200, ok:true, vi_text:"Thích Tăng Trù..."
```

Bản dịch đầy đủ, chính xác, định dạng tiếng Việt — **PASS**.

### Files đã sửa (bổ sung)

- `daoanh/app.py`: replace Anthropic block bằng Groq tại function `api_translate_passage_by_id`

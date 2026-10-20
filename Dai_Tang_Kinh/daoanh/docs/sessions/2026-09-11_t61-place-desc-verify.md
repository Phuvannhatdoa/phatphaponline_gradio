# Session — T61 Place Description VI: Verify + Admin Review Package (read-only, 2026-09-11)

> Thuần read-only: 0 ALTER, 0 INSERT/UPDATE/DELETE, 0 sửa app.py/HTML. Chỉ query + ghi docs.
> Không đụng file agent ngoài (places.html/home.html/search.js...) — tránh conflict staged-index.

## Mục tiêu phiên

Lee chọn hướng "task read-only không đụng file agent ngoài" (sau khi staged-index của agent
ngoài tái diễn operation revert T55b+T55c). Chọn T61 để verify hiện trạng + đóng gói admin review.

## Hiện trạng dữ liệu (query thật `data/lineage.db`)

### Bảng `place_desc_vi_draft`
| Metric | Giá trị | Nhận định |
|--------|---------|-----------|
| Tổng rows | **14,000** | Đạt ngưỡng spec T61 (≥5,000) |
| Distinct place_id | 14,000 (all matched places_dila) | 100% liên kết hợp lệ |
| `desc_source` | 100% `dila_note_zh` | Đây là bảng T66 (copy DILA note), KHÔNG phải từ lexicon ĐỊA DANH |
| `admin_approved` | **0 / 14,000** | Chưa có admin nào chốt — chờ HITL |
| char_count | min 21 · max 1,740 · **avg 70.0** | avg < 80 → chưa đạt ngưỡng spec T61 |
| char_count ≥80 | 4,763 (34%) | ~2/3 description ngắn (<80 ký tự) |
| Ngôn ngữ nội dung | **13,999 Hán / 0 tiếng Việt / 1 Latin** | Toàn bộ là note gốc, CHƯA Việt hóa |

### Coverage so `places_dila` (59,167)
- Đã có draft: **14,000 (23.7%)**
- `places_dila.note` có nội dung nhưng chưa có draft: **17,085** → tiềm năng mở rộng (~31,085 total nếu fill hết)

### Phân bố note_category (top)
寺廟、佛塔、佛教文化地點 5,093 · 中研院歷史地名 2,645 · 地點 2,523 · 山峰、山脈 1,431 · 地點+寺廟 755 · 水系 474 ...

## Đối chiếu với chuỗi task

| Task | Trạng thái thực | Ghi chú |
|------|----------------|---------|
| **T66** (DILA note → draft) | DONE đã có từ 2026-08-28 | Nguồn gốc 14,000 rows hiện tại (`tasks/backup/T66` + `scripts/t66_place_desc_vi_dila_note.py`; taskdone.md xác nhận "lexicon ĐỊA DANH = khái niệm, không dùng được") |
| **T61** (mô tả Việt cho place) | **PENDING — phần thật còn lại**: wire draft vào API + admin approve + resolve tiếng Việt | Draft hiện = note Hán thô, chưa phải "mô tả tiếng Việt" |
| **T74** (Gemini dịch 14k → Việt) | **BLOCKED** — chờ API key | Đây là bước biến draft thành tiếng Việt thực sự; `tasks/T74-place-desc-vi-gemini-translate.md` |
| Endpoint `/api/places/<id>` | KHÔNG wire draft | Chỉ serve `namevi_map_places.note_vi` + `dila_rawtext` Hán; chưa có desc Việt |

## Admin review package (24 samples)

- File: `docs/sessions/t61_admin_review_samples.json` (24 items, 1 mỗi category trong tổng 24 categories)
- Trải đều: 寺廟 437 ký tự (Thượng Hư Hạ Vân Lão Hoà Chuộng Xá Lợi Tháp) → Tứ Quán Lầu 42 ký tự
- Mục tiêu: Lee xem nhanh chất lượng note gốc DILA trước khi quyết dịch (T74) hay resummarize

## Khuyến nghị (KHÔNG tự thi hành — cần Lee duyệt)

1. **T74 là bước bắt buộc** biến draft thành mô tả Việt (need Gemini API key) — chặn T61 hoàn thành.
2. Sau khi có bản Việt + admin approve ≥1 mẫu → mới wire `place_desc_vi_draft` vào `/api/places/<id>` (là
   **sửa app.py = ngoài phạm vi read-only phiên này**; phải làm riêng khi không conflict với agent ngoài).
3. Tùy chọn: fill thêm 17,085 places còn note thiếu draft (script T66 --revert-safe, nhưng là write → phiên khác).
4. Gọn: bạn có thể duyệt 24 samples trong JSON để quyết hướng T74 vs admin-rewrite.

## Files
- `docs/sessions/t61_admin_review_samples.json` (mới) — 24 samples admin review
- `docs/sessions/2026-09-11_t61-place-desc-verify.md` (file này)

## Trạng thái
- T61 giữ **pending** (thành phần thật chưa đủ điều kiện: cần T74 + admin approve + wire API).
- 0 đổi DB, 0 đổi code. Không cần ROLLBACK (không có gì để revert).

## Todo tiếp theo
- Lee duyệt 24 samples → quyết: cấp Gemini key cho T74, hoặc gắn cờ "dùng note Hán trực tiếp".
- Sau khi agent ngoài bàn giao/xong → làm phiên wire API + admin approve cho T61/T73 dạng write.
# Session — T55a Topic Clusters: Scale QA + Data-Integrity Audit (read-only, 2026-09-11)

> Thuần read-only: 0 ALTER, 0 INSERT/UPDATE/DELETE, 0 sửa app.py/HTML. Chỉ query + ghi docs.
> Không đụng file agent ngoài (app.py/places.html) — tránh conflict staged-index.
> Tiếp nối QA package trước (`2026-09-11_t55a-topic-qa-samples.md`) — bổ sung **audit data-integrity toàn bảng** + **scale sample 45 texts stratified**.

## 1. Data-Integrity Audit — `cbeta_topic_clusters`

| Metric | Kết quả |
|--------|--------|
| rows | 8,168 · distinct texts 2,977 · distinct topics 742 |
| NULL text_id / topic / score | 0 / 0 / 0 |
| score ≤ 0 | 0 |
| orphan text_id (CAST vs `cbeta_catalog_vn.id`) | **0** — toàn bộ map hợp lệ |
| text_id dạng `q*` / non-numeric | 0 (dạng số thuần, len 1–4: 1→9·2→83·3→851·4→2,034) |
| duplicate (text_id, topic) | 0 |
| topic case/space collision | 0 (lower-strip unique) |
| coverage | 2,977/3,122 = **95.4%** · 145 zero-topic |

**Score distribution:** 1.0→2,997 · 0.8→2,616 · 0.5→2,486 · 2.0→68 · 3.0→1.
**Score ≥ 2.0 là by design** — keyword cùng topic trúng nhiều lần cộng dồn (vd "Thần Chú"+"Đà La Ni" + "Chú" → Thần Chú=3.0; #1301 Ngữ Lục=2.0; #1012 Thần Chú=2.0). Không phải bug.

**Topic prefix structure:** `Dịch Giả` 682 · `Dynasty` 42 · 19 genre còn lại mỗi cái 1 canonical. Không có thoái hóa namespace.

## 2. Scale QA Sample — 45 texts stratified

File (gitignored, trên disk — convention t61): `docs/sessions/t55a_topic_qa_scale.json` ← cấu trúc:
mỗi text có `title/dynasty/translator` + `topics[{topic,score}]` + `explain[]` (keyword driver minh họa) + `review{ok,note}` **chờ admin điền**.

| bucket | SL | nhận định |
|--------|----|-----------|
| 1 topic | 12 | sạch (Kinh/Giới Luật/Bồ Tát/Giáo Pháp) |
| 2–3 topic | 12 | hợp lý (Kinh + Dynasty + Dịch Giả) |
| ≥4 topic | 13 | hợp lý (đa chiều: genre + dynasty + người) |
| zero-topic | 8 | trung thực — kinh lẻ/kệ tán không khớp keyword → NO_DATA |

## 3. Heuristic rộng — ghi nhận cho admin (biết khi review)

Keyword map trong `scripts/t55a_topic_clusters.py` có một số quy tắc **broad** cần admin để mắt:
- `"Chú"` → Thần Chú: trúng cả "Chú Đại Thừa", tên người có chữ "Chú" (#300 → Thần Chú).
- `"Pháp"` → Giáo Pháp: rất rộng (#2400 Sách Pháp Hiệu → Giáo Pháp).
- `"Giới"` → Giới Luật (#2004 Phạm Giới → Giới Luật — chấp nhận được).
- `"Tam Muội"` → Thiền: samadhi dịch đồng; #1993 Pháp Hoa Tam Muội → Thiền+Pháp Hoa (tranh luận nhỏ).
- `"Lục"` → Ngữ Lục: chữ đơn trùng (vd "Ngữ Lục" chính xác; trọng số 1.0).

→ Nếu admin thấy bias, hướng xử lý an toàn: **reduce score** (không xóa) hoặc thêm keyword dài hơn trước, additive, `--revert`.

## 4. Kết luận

- Data-integrity: **PASS toàn diện** — bảng sạch, deterministic, không orphan/dup.
- Scale QA 45 texts: phân bố hợp lý, zero-topic trung thực.
- Sẵn sàng wire vào `/related` (group `topic`) khi hết conflict app.py.
- Revert đã có: `git revert b395937a` + `DROP TABLE cbeta_topic_clusters`.

## 5. Files
- `docs/sessions/2026-09-11_t55a-qa-scale-integrity.md` (file này, commit)
- `docs/sessions/t55a_topic_qa_scale.json` (gitignored ⏤ trên disk, convention t61)
- `docs/sessions/t55a_topic_samples.json` (gitignored ⏤ từ phiên trước)

## 6. Revert
Docs-only, không code/DB. Không cần revert data.
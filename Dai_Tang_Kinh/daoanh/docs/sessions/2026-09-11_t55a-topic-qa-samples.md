# Session — T55a Topic Clusters QA Samples cho Admin Review (read-only, 2026-09-11)

> Thuần read-only: 0 ALTER, 0 INSERT/UPDATE/DELETE, 0 sửa app.py/HTML. Chỉ query + ghi docs.
> Không đụng file agent ngoài (app.py/places.html...) — tránh conflict staged-index.

## Mục tiêu phiên

T55a (topic clustering data-layer) đã build + commit (`b395937a` + hash-fill `6500be9`).
Chưa wire vào app.py vì tranh chấp agent ngoài → chuẩn bị **admin review package** để Lee
duyệt chất lượng gán topic TRƯỚC khi wire vào `/related`, theo convention T61.

## Dữ liệu

- Bảng: `cbeta_topic_clusters(text_id, topic, score)` — 8,168 rows · 2,977/3,122 texts có ≥1 topic · 742 topics.
- Bảng nền: `cbeta_catalog_vn` (3,122 texts, `title_vi` là tên hiển thị; `sigla` bỏ trống — text_id = PK id).

## QA samples (`docs/sessions/t55a_topic_samples.json`)

### A. Texts nổi tiếng (9) — gán topic có nghiệm ngữ nghĩa
| id | title_vi | topics (top) |
|----|----------|--------------|
| 103 | Bát Nhã Ba La Mật Đa Tâm Kinh | Kinh, Bát Nhã, Dynasty: Đường |
| 104 | Bát Nhã Ba La Mật Đa Tâm Kinh | Kinh, Bát Nhã, Đường, Dịch Giả: Huyền Trang |
| 1034 | Kim Cang Bát Nhã Kinh Luận | Luận, Kinh, Bát Nhã, Kim Cang, Tùy, Đạt Ma Cấp Đa |
| 1035 | Kim Cang Bát Nhã Kinh | Kinh, Bát Nhã, Kim Cang, Diêu Tần, Cưu Ma La Thập |
| 266 | Chánh Pháp Hoa Kinh | Kinh, Pháp Hoa, Giáo Pháp, Tây Tấn, Trúc Pháp Hộ |
| 535 | Đại Bát Niết Bàn Huyền Nghĩa | Kinh, Niết Bàn, Tùy, Quán Đảnh |
| 536 | Đại Bát Niết Bàn Nghĩa Ký | Kinh, Niết Bàn, Tùy, Huệ Viễn |
| 987/988 | Lăng Nghiêm Viện | Lăng Nghiêm, Nhật Bản, Nguyên Tín |

**Nhận định:** gán đúng ngữ nghĩa — dịch giả + triều đại + thể loại đều khớp tên kinh.

### B. Zero-topic (5) — ghi nhận trung thực
A Tra Bà Câu Quỷ (19/20), A Xà Lê Đại Mạn Đồ La (47), An Dưỡng Sao (50), An Tâm Quyết Định Sao (53)
→ không có topic phù hợp → NO_DATA (không bịa).

### C. Top multi-topic (5) — 5–7 topics/text
Chú Hoa Nghiêm Kinh Đề Pháp Giới (301, 7 topics), Kim Cang Bát Nhã Kinh Luận/Chú/Sớ (1034/1039/1041/1048, 6 topics)
→ hợp lý cho các bản chú giải kép (kinh + luận + thần chú).

### D. Phân phối topic per text
1 topic: 266 · 2: 879 · 3: 1,284 · 4: 461 · 5: 75 · 6: 11 · 7: 1
→ phần lớn 2–3 topics, đuôi dài hợp lý. Không có text nào thổi phồng topic.

## Kết luận

Topic clustering chất lượng tốt, sẵn sàng wire vào `GET /daoanh/api/cbeta/<sigla>/related` (group `topic`)
khi hết conflict app.py. Revert đã có: `git revert b395937a` + `DROP TABLE cbeta_topic_clusters`.

## Files
- `docs/sessions/t55a_topic_samples.json` (gitignored — chỉ trên disk, convention t61)
- `docs/sessions/2026-09-11_t55a-topic-clusters.md` (commit trước, giữ nguyên)

## Revert
Không có thay đổi code/DB. QA package là docs → không cần revert.
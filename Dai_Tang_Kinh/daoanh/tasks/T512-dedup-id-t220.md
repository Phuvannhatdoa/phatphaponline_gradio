---
id: T512
title: "Dọn ID trùng T220 (tasks/T220-vnpa-etl-preserve-relations.md vs tasks/X-T220-vnpa-dila-id-recovery.md)"
status: pending
created: 2026-11-01
updated: 2026-11-01
done_when: |
  npm run dup:ids không còn báo trùng thật cho ID T220 (kể cả khi tiêu chí
  phân loại "X- superseded" trong scripts/build_progress_data.py được siết
  lại). Đã đổi ID của file có footprint nhỏ nhất theo AGENTS.md §16 (thứ tự
  ưu tiên: (1) status kết thúc trước, (2) ít tham chiếu đến trước, (3) không
  có docs/plans|reports/ đi kèm trước, (4) không phải ID đã công bố trong
  docs/tasktodo.md trước), kèm former_ids: [...] ghi trong frontmatter của
  file đổi ID để grep ID cũ vẫn ra. Không đổi ngay trong task này — chỉ mô
  tả lỗi và đề xuất, chờ Admin duyệt hướng đổi.
---

# T512 — Dọn ID trùng T220

## Mô tả lỗi

Hai file task đang cùng khai báo `id: T220` trong frontmatter:

1. `tasks/T220-vnpa-etl-preserve-relations.md` — "VNPA ETL Preserve Person
   Relations — Scoped DELETE Guard for Relations", `status: done`,
   `created: 2026-10-04`, `updated: 2026-10-13`. Không có `former_ids`.
2. `tasks/X-T220-vnpa-dila-id-recovery.md` — "VNPA DILA-ID Recovery: Khôi
   phục 33 dila_id từ T206/T207 backup (SUPERSEDED by T215)",
   `status: superseded`, `superseded_by: T215`, `former_ids: [T215]`,
   `created: 2026-10-02`, `updated: 2026-10-12`. Tên file có tiền tố `X-`
   (quy ước file superseded) nhưng frontmatter vẫn ghi `id: T220` —
   `former_ids` của chính file này lại ghi `[T215]`, không phải `[T220]`,
   nên không rõ ID gốc thật của file #2 là gì trước khi bị đổi.

## Kiểm tra hiện trạng (2026-11-01, trước khi sửa gì)

- `npm run dup:ids` **hiện KHÔNG báo T220 là trùng thật** — script
  `scripts/build_progress_data.py --check-dup-ids` xếp T220 vào nhóm
  `[INFO] ID có bản X- superseded (hợp lệ theo quy ước)` vì file #2 có tiền
  tố `X-` trong tên, và kết luận cuối `[OK] Không có task ID trùng thật.`
  Output nguyên văn đã lưu trong báo cáo điều phối phiên này.
- Nghĩa là: theo quy tắc hiện tại của guard, đây **không phải lỗi pipeline
  đang chặn CI** — nhưng vẫn là dữ liệu mơ hồ (2 file, lịch sử ID chồng
  chéo T220/T215, `former_ids` của file X- không khớp tên file X-T220) nên
  cần dọn cho rõ, và để guard không vô tình bỏ sót nếu sau này có session
  khác tạo thêm 1 file `T220-*.md` không có tiền tố `X-`.

## Đề xuất dọn (chưa làm — chờ Admin duyệt)

Theo AGENTS.md §16 "Nếu đã cấp ID trùng" — đổi số ở phía có footprint nhỏ
nhất, thứ tự ưu tiên: (1) status kết thúc → (2) ít tham chiếu đến → (3)
không có docs/plans|reports/ đi kèm → (4) không phải ID mà
`docs/tasktodo.md` đã công bố.

So sánh 2 file:

| Tiêu chí | #1 `T220-vnpa-etl-preserve-relations.md` | #2 `X-T220-vnpa-dila-id-recovery.md` |
|---|---|---|
| status | `done` (kết thúc) | `superseded` (kết thúc) |
| Tham chiếu từ nơi khác | Có artifact riêng `docs/Mimo-Flash/T220-VNPA-ETL-PRESERVE-PERSON-RELATIONS-01.md` | Có artifact riêng `docs/Mimo-Flash/T220-VNPA-DILA-ID-RECOVERY-01.md`; đã tự nhận "duplicate task file", việc thật làm ở T215 |
| docs/plans hoặc reports đi kèm | Chưa kiểm — cần `grep -rl "T220" docs/` để đếm số lần nhắc | Chưa kiểm — tương tự |
| Công bố trong docs/tasktodo.md hiện tại | Chưa kiểm — cần `grep -n "T220" docs/tasktodo.md` | Chưa kiểm — tương tự |
| Tên file đã có tiền tố X- (tự nhận superseded) | Không | Có |

**Nhận định ban đầu (chưa chốt):** file #2 đã tự nhận là "duplicate task
file" trong chính nội dung của nó và đã có tiền tố `X-` theo quy ước —
nhiều khả năng là phía nên đổi ID (ví dụ về lại `T215` theo đúng
`former_ids` cũ, hoặc một ID mới nếu T215 đã bị dùng cho nội dung khác).
Nhưng cần chạy đủ 4 tiêu chí ở bảng trên (đặc biệt đếm tham chiếu thật
bằng `grep -rl`) trước khi chốt, đúng quy trình AGENTS.md §16 — **không
đổi tên file hay ID trong task này**.

## Việc cần làm (khi Admin duyệt hướng đổi)

1. `grep -rln "T220" docs/ tasks/` để đếm tham chiếu thật của từng file.
2. Xác nhận T215 hiện có đang bị ID nào khác dùng không (tránh tạo trùng
   mới khi đổi #2 về T215).
3. Đổi `id:` trong frontmatter của file được chọn, thêm `former_ids: [T220]`
   (giữ lại `former_ids` cũ nếu có, ví dụ `[T220, T215]` nếu #2 được đổi
   thành T215 nhưng vẫn cần giữ vết T220).
4. Backup file trước khi đổi vào `docs/sessions/YYYY-MM-DD/`.
5. Chạy lại `npm run dup:ids` xác nhận không còn cảnh báo T220 ở cả 2 dạng
   (trùng thật và INFO superseded nếu đổi hẳn ID).
6. Cập nhật `docs/tasktodo.md` nếu có block nhắc T220 cần sửa theo ID mới.
7. KHÔNG git add/commit — theo quy tắc chung của dự án.

## Ràng buộc

- KHÔNG đổi tên file hoặc `id:` của `T220-vnpa-etl-preserve-relations.md`
  hay `X-T220-vnpa-dila-id-recovery.md` trong task này.
- KHÔNG git add/commit/reset.
- KHÔNG ghi DB.
- KHÔNG đánh DONE.

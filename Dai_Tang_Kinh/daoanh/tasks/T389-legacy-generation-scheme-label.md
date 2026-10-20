---
id: T389
title: "Engine số đời cũ (etl_gen_compute, +37): backup trước DROP, gắn nhãn scheme, chờ T232 thay"
status: pending
created: 2026-10-13
updated: 2026-10-13
owner: code (Hermes giao)
parent: T382
module: TTL Thiền Sư VN
priority: high
depends_on: []
depends_note: "2026-10-13: bỏ phụ thuộc T384 vì T384 hoãn theo quyết định Admin; T389 chỉ sửa script nên tự an toàn"
dispatch: approved
plan_approved_at: "2026-10-13 (Admin phê chuẩn đề xuất ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md, mục C2)"
done_when: >
  (1) `scripts/etl_gen_compute.py` trước mọi `DELETE`/`DROP` gọi backup bằng helper của T387 (nếu T387 chưa xong: dừng
  `--apply` với thông báo rõ); mặc định chạy `--dry-run`, ghi thật cần `--apply`.
  (2) Output (stdout + file báo cáo `docs/evidence/<ngày>_T389_gen_legacy.tsv`) ghi rõ cho mỗi số đời:
  `scheme='thientong_cadiep1'` hoặc `'lamte_lamte1'`, `method='ttl_generationOrder+37'` hoặc `'dila_bfs_shortest'`,
  `status='computed_legacy'`. Không thêm cột vào bảng DB — muốn lưu nhãn vào DB cần Admin duyệt đổi schema riêng
  (dừng và hỏi).
  (3) Báo cáo đếm: bao nhiêu người có >1 đường lên gốc trên đồ thị DILA (BFS chỉ lấy đường ngắn nhất ⇒ có thể sai,
  cùng loại BUG-027); bao nhiêu file TTL có `generationOrder` mà `dharmaLineageName` không thuộc Lâm Tế (giả định +37 không áp).
  (4) Docstring + `docs/` ghi rõ: đây là engine legacy, T232 là engine duy nhất về lâu dài; endpoint run_etl_gen đã khoá bởi T384.
  (5) Chạy dry-run trên bản sao DB (không phải DB thật); commit riêng tiền tố T389; Admin xác nhận DONE.
revert: >
  git revert --no-edit <sha_T389>. Bản sao: docs/sessions/<ngày>/etl_gen_compute.py.bak-before-T389.
outcome: >
  2026-10-13: tạo task, chưa làm.
---

# T389 — Engine số đời cũ: khoá an toàn + nhãn scheme

## Mục tiêu

Offset `+37` đúng số học với hệ Ma Ha Ca Diếp = 1 (Lâm Tế = đời 38). Lỗi thật: gán cứng một hệ đếm, không ghi scheme;
giả định mọi `generationOrder` TTL là đời Lâm Tế; DILA dùng BFS đường ngắn nhất trên đồ thị nhiều thầy; `DROP`/`DELETE`
không backup. Không xoá engine ngay — làm an toàn và minh bạch cho tới khi T232 thay thế.
Bằng chứng: `docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md` (P1-2, C2).

## Phạm vi

Được sửa: `scripts/etl_gen_compute.py`, tạo báo cáo evidence + test dry-run. Cấm: chạy `--apply` trên `data/lineage.db`,
đổi schema, gọi endpoint, deploy, push. Quyết định số đời đúng/sai thuộc Admin — chỉ báo cáo số liệu.

## Các bước

- [ ] Sao lưu script
- [ ] Thêm `--dry-run` mặc định / `--apply` + backup trước DROP/DELETE
- [ ] Gắn nhãn scheme/method/status vào output + file evidence
- [ ] Đếm multi-parent và TTL ngoài Lâm Tế (trên bản sao DB)
- [ ] Ghi chú legacy trong docstring + docs
- [ ] Commit riêng `T389: …`
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE

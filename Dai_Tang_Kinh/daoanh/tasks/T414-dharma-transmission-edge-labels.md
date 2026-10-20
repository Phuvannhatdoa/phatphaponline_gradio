---
id: T414
bug_id: BUG-039
title: "Bug verify: BUG-039: Cạnh thầy–trò chưa phân biệt 'nối pháp' với 'y chỉ / tham học / giới sư' — ~19.600 cạnh unknown, cây không vẽ đúng nét liền/đứt"
status: pending
created: 2026-10-15
updated: 2026-10-15
owner: code (Hermes giao) + Admin (duyệt ghi DB)
module: Lineage / Generation
priority: high
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-15 (Admin 04:04: nét liền = nối pháp/thọ pháp (Main tree), nét đứt = y chỉ pháp / thầy giáo thọ; ví dụ Đơn Hà Thiên Nhiên)"
db_write: "Bước 1–3 dry-run, KHÔNG ghi DB. Bước 4 ghi nhãn vào lineage_primary_teacher (hoặc bảng nhãn additive) CHỈ khi Admin duyệt kết quả dry-run."
done_when: >
  (1) Script dry-run `scripts/t414_label_transmission.py --dry-run` gán cho mỗi cạnh thầy→trò một nhãn
  `relation_kind` ∈ {noi_phap, khac (y chỉ/tham học/giới sư/thế độ), unknown} kèm bằng chứng + locator:
    - noi_phap khi có ≥1 bằng chứng: TTL `bkg:hasTeacher` trong file TTL của đệ tử (dòng truyền pháp);
      Marcus `marcus_subtype = dharma_transmission`; tiểu sử DILA của đệ tử có "<tên thầy>…法嗣", "嗣<tên thầy>",
      "得付法" gắn với đúng thầy đó (khớp tên/Hán tự thầy, không khớp mơ hồ);
    - khac khi tiểu sử DILA cho thấy rõ quan hệ khác với thầy đó ("剃度/剃落/受戒/納戒…律師/參/謁/依止…" mà không có 法嗣);
    - unknown khi không đủ bằng chứng (không đoán).
  (2) Xuất `docs/evidence/<ngày>_T414_transmission_dryrun.tsv` + thống kê: số cạnh noi_phap/khac/unknown theo nguồn bằng chứng;
  mâu thuẫn (TTL nói nối pháp A, DILA 法嗣 nói B) liệt kê riêng, không tự chọn.
  (3) Kiểm tay ≥ 20 mẫu (gồm A009460 Đơn Hà: Hy Thiên = noi_phap; Đạo Khâm, Hy Thao = khac; A004980 Tồn Tưởng: Lâm Tế
  A003627 = noi_phap theo "臨濟義玄禪師法嗣…得付法"), ghi đúng/sai.
  (4) [Chờ Admin duyệt] ghi nhãn vào DB (additive, có backup SQLite API + revert); API lineage-tree/ancestor-spine trả
  `relation_kind` để T410 vẽ nét liền/đứt.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  Dry-run: xoá file evidence. Ghi DB (nếu duyệt): DROP cột/bảng nhãn additive hoặc khôi phục backup.
outcome: >
  2026-10-15: RC tạo task từ quyết định Admin. Chưa làm.
---

# T414 / BUG-039 — Gắn nhãn "nối pháp" cho cạnh thầy–trò

## Vì sao

Admin chốt (2026-10-15 04:04): **nét liền = nối pháp/thọ pháp (Main tree), nét đứt = y chỉ pháp, tham học, thầy giáo thọ**.
Nhưng dữ liệu hiện tại chưa phân biệt:
- DILA (46.006 cạnh) chỉ có `dila:teacher_of`; Marcus (11.169) chỉ `da:isTeacherOf`.
- `lineage_primary_teacher`: ~3.190 `dharma_transmission` (Marcus), 34 BOTH, 569 TTL, **~19.626 FALLBACK/unknown**.
- Tiểu sử DILA có **3.249** vị chứa "法嗣" — chưa được khai thác.
- Ví dụ Đơn Hà Thiên Nhiên (A009460): cả 3 thầy (Hy Thiên, Đạo Khâm, Hy Thao) đều "unknown" dù TTL ghi rõ Hy Thiên và
  tiểu sử DILA ghi rõ Hy Thao là luật sư truyền giới, Đạo Khâm là nơi tham học. Cạnh Mã Tổ → Đơn Hà không có trong DB
  (tiểu sử DILA: "尋謁江西馬大師，受天然之法號") — đề xuất thêm cạnh "khac" (y chỉ/đặt hiệu) ở bước 4 nếu Admin duyệt.

## Câu hỏi mở cho Admin (ảnh hưởng T410)

Trong lúc chưa gắn nhãn xong (hoặc cạnh vẫn unknown), cây vẽ cạnh unknown thế nào?
- (a) nét liền nếu đệ tử chỉ có 1 thầy, nét đứt nếu có nhiều thầy (đơn giản, có thể sai);
- (b) nét đứt hết (thật thà, nhưng ban đầu phần lớn cây sẽ là nét đứt);
- (c) nét liền hết như hiện nay, chỉ đổi khi có nhãn "khac".
Mặc định tới khi Admin chọn: **(c)**.

**Cập nhật 2026-10-15 04:06 (Admin):** nét đứt chỉ vẽ cho nhân vật đang xem (thầy tham học/y chỉ chưa đắc pháp); đồng môn và
học trò luôn nét liền (xem T410). Vì vậy câu hỏi (a)/(b)/(c) chỉ còn áp dụng cho các thầy của **nhân vật đang xem**; tạm giữ (c).

## Phạm vi

Code: script dry-run + (sau duyệt) bổ sung trường `relation_kind` vào API. Không sửa file TTL. Ghi DB chỉ sau duyệt.

## Các bước

- [x] RC tạo task (2026-10-15)
- [ ] Viết script dry-run (TTL / Marcus subtype / DILA bio regex có khớp tên thầy)
- [ ] Xuất TSV + thống kê + danh sách mâu thuẫn
- [ ] Kiểm tay ≥ 20 mẫu
- [ ] Trình Admin; chờ duyệt ghi DB
- [ ] (sau duyệt) ghi nhãn additive + API trả relation_kind
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE

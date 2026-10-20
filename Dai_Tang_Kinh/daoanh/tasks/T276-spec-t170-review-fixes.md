---
id: T276
title: "Sửa SPEC T170 theo review: gộp 惠→慧 không được nhập nhầm người, đồng bộ trạng thái thực, bổ sung backup trước revert"
module: Editorial / LLM Translation
priority: high
status: in_progress
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: T170
plan_approved_at: "2026-10-10 (Admin phê chuẩn đề xuất sửa SPEC T170 sau review)"
done_when: >
  (1) SPEC T170 có R3 viết lại: fold CJK chỉ là khóa so khớp tạm, không đổi tên xuất ra, kết quả ghi fold_applied,
      không tự xác nhận khi chỉ khớp qua fold; bỏ seed 惠→慧 toàn cục; có test 惠明 ≠ 慧明.
  (2) SPEC T170 §12 ghi trạng thái thực (scripts T170 đã có, bảng side-car đã tồn tại, tests/ chưa có file test).
  (3) SPEC T170 §4 thêm backup bắt buộc trước --revert; §5 lọc dòng name_vi NULL (ví dụ A038890 道一).
  (4) SPEC T170 §8 gate ⑤ ghi rõ bộ vàng cần lập và ai duyệt.
  (5) tasktodo + dashboard (plan6) hiển thị T276.
  (6) KHÔNG ghi DB trong task này. Admin xác nhận DONE — KHÔNG tự đánh DONE.
revert: >
  Chỉ sửa tài liệu. Bản sao trước sửa: docs/sessions/2026-10-10/T170-SPEC.md.bak-before-T276,
  build_t263_status.py.bak-before-T276, dashboard_process.html.bak-before-T276, tasktodo.md.bak-before-T276.
outcome: >
  2026-10-10: tạo task; chờ sửa SPEC và cập nhật dashboard.
---

# T276 — Sửa SPEC T170 theo review

Nguồn: review SPEC T170 ngày 2026-10-10 (đối chiếu với DB và repo).

## 1. Vì sao làm

- **Gộp 惠→慧 nhập nhầm người.** DB có 8 cặp `惠明`/`慧明` với ID DILA khác nhau (ví dụ A001195 và A002316). Fold toàn cục làm hai người trùng khóa so khớp và có thể bị xác nhận sai. Mâu thuẫn với nguyên tắc T272: danh tính chỉ dựa trên bằng chứng DILA.
- **SPEC lệch trạng thái thực.** SPEC ghi "0 file tồn tại" nhưng `scripts/verify_dila_places_groq.py`, `scripts/t170_entity_groq_audit_migrate.py`, `scripts/t170_classify.py` đã có; hai bảng `place_groq_audit` và `person_groq_audit` đã tồn tại. Thư mục `tests/` chưa có file test T170.
- **Revert mất dữ liệu.** `--revert` DROP hai bảng audit mà SPEC không yêu cầu backup trước.
- **Dòng thiếu tên.** `people` có 1 dòng `name_vi` rỗng (A038890, 道一) — pipeline phải lọc riêng.

## 2. Quy tắc đề xuất

1. Fold CJK chỉ là khóa so khớp tạm; không thay `clean_zh` hay tên xuất ra.
2. Kết quả khớp qua fold ghi `fold_applied = 1` và không được tự xác nhận (chỉ đưa vào hàng chờ Admin).
3. Không seed `惠→慧` toàn cục; mỗi cặp fold cần bằng chứng DILA riêng.
4. Test bắt buộc: `惠明 ≠ 慧明` không được gộp.
5. Revert: sao lưu DB bằng SQLite backup API trước `--revert`, ghi đường dẫn vào log.

## 3. Các bước

- [x] **Bước 1 — Kiểm trạng thái thực (chỉ đọc):** đã xác nhận scripts T170 tồn tại, hai bảng side-car tồn tại, DB ở WAL, `people` 48.673 dòng, `places_pending.name_vi` 118.304 dòng có giá trị.
- [x] **Bước 2 — Sửa SPEC T170 §3bis R3** theo quy tắc 1–4 ở trên.
- [x] **Bước 3 — Sửa SPEC T170 §4 và §5:** backup trước revert; lọc `name_vi` NULL.
- [x] **Bước 4 — Sửa SPEC T170 §8 gate ⑤:** định nghĩa bộ vàng và người duyệt.
- [x] **Bước 5 — Thêm SPEC T170 §12 trạng thái thực** (file đã có, bảng đã có, tests chưa có).
- [x] **Bước 6 — Cập nhật tasktodo và dashboard (plan6).**
- [ ] **Admin xác nhận DONE.**

### 3b. Bổ sung: kết quả tự động phải được Admin kiểm (Admin phê chuẩn 2026-10-10)

- [x] **Bước 7 — Đánh dấu `auto_*` là tạm thời:** trạng thái `auto_verified`, `auto_verified_sanskrit`, `auto_title_aligned`, `auto_taxonomy_aligned` không được coi là kết quả cuối. Ghi thêm cờ `provisional = 1` cho đến khi Admin lấy mẫu duyệt xong (SPEC §3.4 và §4).
- [ ] **Bước 8 — Lấy mẫu duyệt:** Admin duyệt ngẫu nhiên 5% mỗi loại `auto_*` (tối thiểu 20 dòng/loại). Nếu tỷ lệ sai vượt ngưỡng đã định thì dừng pipeline và sửa luật. Ngưỡng do Admin đặt trước khi chạy.
- [x] **Bước 9 — Dashboard hiển thị kết quả pipeline:** số dòng theo từng `review_status`, số dòng `provisional`, số dòng chờ duyệt (`needs_review = 1`), số lỗi API, thời điểm và `batch_id` lần chạy gần nhất. Thêm vào `scripts/build_t263_status.py` và card dashboard (cùng mẫu plan6).
- [x] **Bước 10 — Tu sĩ chưa có UI:** trước khi có giao diện, xuất báo cáo CSV kết quả `person_groq_audit` lên dashboard để Admin xem. Không để kết quả chỉ nằm trong DB.
- [x] **Bước 11 — Production cần Admin duyệt lại:** sau pilot, lần chạy production (gỡ `--pilot`) phải có phê chuẩn riêng của Admin. Ghi điều này vào SPEC T170 §8.

## 3c. Đã làm trong code (2026-10-10)

- `scripts/t276_audit_stats.py`: thống kê (chỉ đọc), cờ `provisional` tính khi đọc, xuất CSV (chỉ đọc), `--migrate` thêm cột `admin_checked` vào 2 side-car (có backup, idempotent), `--revert` DROP COLUMN.
- `tests/test_t276_audit.py`: 6 test PASS trên DB tạm, không đụng DB thật.
- `scripts/build_t263_status.py` và dashboard: card "Kết quả pipeline T170".
- **Chưa chạy `--migrate` trên DB thật:** lệnh ghi bị chặn quyền trước đó. Cần Admin cho phép. Bước 8 (Admin lấy mẫu) là việc của Admin.
- **Lưu ý tên file:** SPEC hiện là `docs/Mimo-Flash/XX-T170-dila-place-person-v41-verify-SPEC.md` (tên gốc `T170-…` không còn trên đĩa; `X-T170-…` là bản cũ 2026-09-28).

## 4. Ràng buộc

- Chỉ sửa tài liệu. Không ghi DB, không chạy migrate, không sửa code T170.
- Không git push. Commit chỉ khi Admin yêu cầu.
- Gỡ liên kết A025951 (Kinh Triệu) vẫn chờ quyền ghi DB, không thuộc task này.

## 5. Liên quan

- T170 (SPEC v4.1 + R1–R8), T169 (pipeline place), T272 (nguyên tắc danh tính), T275 (đối chiếu TTL/DILA).

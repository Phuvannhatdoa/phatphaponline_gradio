---
id: T454
title: Làm sạch tên địa danh Việt có hậu tố "_ Huý"/"_ Ngoa" trong namevi_map_places
status: done
created: 2026-10-22
updated: 2026-10-29
owner: daoanh-debugger
module: Data / Places
priority: medium
parent: T453
plan_approved_at: "2026-10-22 (Admin phê chuẩn đề xuất (2) trong T453: tạo task riêng). Ghi DB: CHƯA duyệt riêng."
done_when: >
  (1) Đo lại danh sách name_vi chứa "_" trong namevi_map_places (đo 2026-10-22: 8 dòng) và xác định nghĩa hậu tố
      ("_ Huý" = chữ kiêng huý? "_ Ngoa" = ngoa tự?) từ nguồn sinh dữ liệu (script/import đã tạo).
  (2) Đề xuất cách sửa cho từng dòng (bỏ hậu tố khỏi name_vi, chuyển hậu tố sang cột ghi chú/flag) — Admin duyệt.
  (3) Backup DB → sửa → ROLLBACK row (UPDATE ngược từ bản ghi gốc lưu trong CSV backup).
  (4) Search HOME "Huyền Trang" hiện "Hoằng Phúc Tự" (không còn "_ Huý"); daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  UPDATE namevi_map_places theo CSV giá trị gốc lưu tại docs/sessions/<ngày>/T454/namevi_before.csv.
---

## Mô tả
Làm sạch 8 tên địa danh Việt có hậu tố lạ "_ Huý" / "_ Ngoa" trong `namevi_map_places.name_vi` (sinh từ T453). Hậu tố này lộ ra thẻ người trên HOME (ví dụ "Hoằng Phúc Tự _ Huý"). Việc cần làm: xác định nghĩa hậu tố, đề xuất sửa từng dòng, rồi chỉ UPDATE sau khi Admin duyệt, có backup và ROLLBACK. Phạm vi chỉ 8 dòng; không sửa `places_dila` (raw DILA).

### Trạng thái hiện tại
- Đã làm: đo 8 dòng (mode=ro, 2026-10-22), xác định 5 dòng ví dụ; kế hoạch bước trong `docs/sessions/2026-10-26/n4-plan.md` (mục T454). Grep "Huý"/"Ngoa" trong `scripts/*.py` = 0 ⇒ hậu tố đến từ dữ liệu import, cần truy vết qua `source`/`created_at`.
- Chưa làm: truy vết nguồn hậu tố; đề xuất sửa; CSV before; backup; UPDATE; re-populate FTS (nếu có); verify UI. Chưa ghi DB.
- Đang chờ: Admin trả lời Q5 trước khi đề xuất sửa.

### Câu hỏi cần Admin quyết
- Q5: Hậu tố "_ Huý" / "_ Ngoa" là ghi chú hợp lệ cần giữ (chuyển sang cột `note_vi`) hay rác cần xoá? — chưa có đáp án.

# T454 — Hậu tố "_ Huý" trong tên địa danh Việt

## Phát hiện (T453, 2026-10-22)
Thẻ người trên HOME (search "Huyền Trang") hiển thị nơi dịch "Hoằng Phúc Tự **_ Huý**" — tên lấy từ
`namevi_map_places.name_vi` theo DILA place ID `PL000000042305`.

Đo (DB `mode=ro`): `SELECT dila_id, name_vi FROM namevi_map_places WHERE instr(name_vi,'_')>0` → **8 dòng**, ví dụ:
- PL000000042180 Chương Tín Tự _ Huý
- PL000000013217 Giác Trí Tự _ Ngoa
- PL000000042305 Hoằng Phúc Tự _ Huý  ← có trong kinh lục DILA (nơi dịch của Huyền Trang, 13 bộ)
- PL000000055653 Nguyên Bí Tháp _ Huý
- PL000000042255 Nguyên Pháp Tự _ Huý

## Phạm vi
Chỉ 8 dòng trên (và dòng mới cùng mẫu nếu đo lại phát hiện). Không sửa `places_dila` (raw DILA).

## Câu hỏi cho Admin
1. Hậu tố là ghi chú hợp lệ cần giữ (chuyển sang cột khác) hay rác cần xoá?

### Nhật ký 2026-10-29 — ĐÃ XỬ LÝ (Admin xác nhận DONE)
- **Đo lại**: `namevi_map_places` có **8 dòng** `name_vi` chứa hậu tố (2026-10-22) → **5 dòng** có mẫu `_ Huý`/`_ Ngoa` cần sửa (CSV: `docs/sessions/2026-10-28-t454/t454_namevi_suffixed_20261028_190704.csv`).
- **Cách sửa (Admin duyệt)**: bỏ hậu tố khỏi `name_vi`, **giữ hậu tố nguyên văn trong `note_vi`** (không mất thông tin). Không đụng `places_dila` (raw DILA).
- **Backup trước khi ghi**: `data/backups/lineage_t454_<ts>.db` (auto trong script).
- **Script**: `scripts/t454_cleanup_suffix.py` (`--stats` / `--apply` / `--revert`).
- **Verify sau apply** (`scripts/t454_verify_state.py`): dòng có hậu tố thật = **0**.
  - Lưu ý: `LIKE '%_ Huý%'` **không** escape `_` nên trả về 2 dòng giả ("Ải Ngoan Trại", "Ải Ngoan Sỡ") — phải dùng `LIKE '%\_ Huý%' ESCAPE '\'`.
- **ROLLBACK**: dòng 2026-10-28 trong `docs/ROLLBACK.md` (UPDATE ngược từ CSV giá trị gốc).
- **Bàn giao**: `docs/Handoff-2026-10-28-t454.md`.

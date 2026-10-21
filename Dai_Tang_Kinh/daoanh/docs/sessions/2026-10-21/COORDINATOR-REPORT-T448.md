# Coordinator Report — 2026-10-21 (T448 batch + QA)

> Báo cáo điều phối cho Admin/Planner Hermes. Người điều phối: coordinator (opencode).

## 1. Việc đã hoàn thành

| # | Việc | Kết quả |
|---|---|---|
| 1 | Scan 162 task undone + đề xuất fix | ✅ trình Admin |
| 2 | Tạo T448 (kế hoạch fix tuần tự) | ✅ `tasks/T448-fix-bug-batch-ui-gis.md` |
| 3 | Fix T412 (BUG-037) + T406 | ✅ commit `7eb88369` (chỉ 2 hunk) |
| 4 | Fix T416 (autocomplete) | ✅ commit `b40abd67` (code) + `80723409` (2 index DB) |
| 5 | QA độc lập 3 bug | ✅ `daoanh-qa` → PARTIAL (3 fix PASS) |
| 6 | Sửa 2 lỗi QA phát hiện | ✅ `ac533205` (khôi phục `task: allow`) + sync index thật |
| 7 | Tạo T450 (FTS5) | ✅ `tasks/T450-fts5-autocomplete-search.md` |

## 2. Bằng chứng đo (T416)

| Chuỗi | Trước | Sau |
|---|---|---|
| `'Thiếu L'` | 1695–9338 ms | 186–304 ms |
| `'Nghĩa Huyền'` | 1545–1948 ms | 199–227 ms |
| `'Thiếu'` | 171–213 ms | 39–80 ms |

Số kết quả API không đổi (8/8/10/10/10) → không regression.

## 3. Vấn đề cần Admin quyết

1. **T445 trùng 2 file** (cả `id: T445`, `in_progress`) → `dup:ids` FAIL, chặn pipeline.
   Đề xuất: đổi 1 file thành `X-T445-...` (superseded) hoặc renumber T451 + `former_ids`.
2. **`admin/places.html` L174–184** cùng lỗi flyTo không guard isFinite (QA phát hiện, ngoài phạm vi).
3. **T450** cần phase nghiên cứu FTS5 trên **bản copy DB** (chưa đụng `lineage.db`).

## 4. Cảnh báo kỹ thuật (quan trọng cho mọi session)

- **Index thật (.git/index) hay stale trên máy này.** Sau mỗi commit tôi đều phải sync lại
  bằng ghi byte tại chỗ (§17) — `git reset` im lặng không luôn đồng bộ.
- **Commit file trộn WIP**: dùng blob dựng từ HEAD + phần của mình (§17). Lần này tôi lọc
  patch theo hunk → commit sạch, QA xác nhận không sweep.
- **Task tool có thể abort** (đã abort 2 lần ở đầu phiên; lần sau chạy được).
- **`python -c` với ký tự đặc biệt vỡ trong PowerShell** → luôn viết temp `.py`.
- **PowerShell `>` ghi UTF-16** → dùng python để ghi/trích file nhị phân.

## 5. Commits phiên này

`776296a0` → `b40abd67` → `22d90d7a` → `80723409` → `f6d34a63` → `7eb88369` → `ac533205`

## 6. Việc CHƯA xong (theo ưu tiên)

1. Dup T445 (blocker pipeline) — chờ Admin quyết cách sửa.
2. T450 FTS5 — phase nghiên cứu.
3. `admin/places.html` flyTo guard — task riêng.
4. QA trên trình duyệt thật (hiện chỉ Flask test client + đọc code).
5. Deploy VPS (chưa — cần Admin).

## 7. Điều kiện tiếp tục

- Chạy `npm run guard` + `npm run dup:ids` (hiện FAIL vì T445) trước khi review.
- Không commit file trộn WIP của session khác khi chưa có lệnh rõ.

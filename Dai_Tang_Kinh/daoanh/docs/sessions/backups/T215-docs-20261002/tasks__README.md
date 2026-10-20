# TASKS/ — Feature Dev Board (chuẩn Claude Code)

> **Quy tắc vàng:** 1 file = 1 chức năng. Mọi chức năng cần dev đều có file task ở đây.
> Dashboard (`dashboard_process.html`) đọc các file này (qua `build_progress_data.py`) để hiển thị Task Board cho admin.

---

## 1. Khi nào tạo file task mới

- Có chức năng/API/ETL mới chưa dev (trong `docs/tasktodo.md`, `docs/roadmap.md`, hoặc admin yêu cầu).
- Đổi ID thế nào: `T` + số thứ tự (đếm tiếp từ số lớn nhất hiện có), viết hoa: `T10`, `T11`...
- Tên file: `T<id>-<slug-ngan-gon>.md` (slug không dấu, dùng `-`). VD: `T06-gis-cluster.md`.

## 2. Cấu trúc file task (bắt buộc)

```markdown
---
id: T10
title: Tên ngắn gọn chức năng
module: Tên module (phải khớp MODULES trong build_progress_data.py)
priority: high            # high | medium | low
status: pending           # pending | in_progress | blocked | done
depends_on: []            # ID task phải xong trước, VD: [T06]
created: 2026-08-13
updated: 2026-08-13
done_when: Điều kiện để coi là xong (1 dòng, rõ ràng đo lường được)
---

# T10 — Tên chức năng

## Mục tiêu
1-2 câu mô tả.

## Cách tiếp cận
Các bước chính (không cần chi tiết hóa đơn).

## Acceptance criteria (checklist)
- [ ] Tiêu chí 1
- [ ] Tiêu chí 2
```

## 3. Trạng thái status (chỉ dùng 4 giá trị)

| status | Ý nghĩa | Dashboard hiển thị |
|--------|---------|--------------------|
| `pending` | Chưa bắt đầu | Cột Pending |
| `in_progress` | Đang làm | Cột In-progress |
| `blocked` | Bị chặn (cần admin quyết, thiếu data...) | Cột Blocked — **alert đỏ** |
| `done` | Xong (tick hết acceptance criteria) | Cột Done |

## 4. Quy ước agent (bắt buộc sau mỗi phiên làm)

1. Trước khi làm 1 task → đổi `status: in_progress` + `updated: <hôm nay>`.
2. Khi gặp chặn → đổi `status: blocked` + ghi rõ lý do ở phần **Blockers** trong file task.
3. Khi xong → tick hết acceptance criteria, `status: done`, `updated: <hôm nay>`.
4. Nếu `docs/tasktodo.md` có task tương ứng → cập nhật dấu ✅/⏳ ở đó.
5. Sau mọi thay đổi → dashboard tự cập nhật khi admin bấm Refresh (hoặc chạy `python scripts/build_progress_data.py`).

## 5. Blockers (dùng khi status=blocked)

Thêm phần này vào file task:
```markdown
## Blockers
- [LÝ DO] — cần gì để gỡ (admin quyết / thiếu dữ liệu / chờ task khác)
```

## 6. Xem danh sách task

```powershell
# Tạo lại JSON cho dashboard (chạy từ thư mục daoanh/)
python scripts/build_progress_data.py
```

Mở `http://localhost:8080/dashboard/dashboard_process.html` → bấm Refresh.

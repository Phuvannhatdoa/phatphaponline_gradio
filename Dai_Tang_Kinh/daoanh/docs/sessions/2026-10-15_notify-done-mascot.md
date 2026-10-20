# Session 2026-10-15 — Báo Done bằng nhân vật trên desktop

**Yêu cầu Admin:** "Cho nhân vật này show trên desktop khi Taskdone … Done thì cho nó hiện góc systemtray. Admin click thì hide đi. Báo system Alert Ting Ting."

## Đã làm
- `static/notify/mascot.png`: ảnh Admin gửi đã tách nền. Ảnh gốc là RGB với ô bàn cờ vẽ sẵn, không có alpha thật. Cách tách: loang từ mép + xoá các vùng kín kiểu bàn cờ (xám 190–206 / trắng ≥246, bão hoà ≤5, ≥600 px); làm mềm viền alpha. Vẫn còn vân mờ sau dải lụa trong suốt (vẽ sẵn trong ảnh gốc).
- `scripts/notify_done.ps1`: cửa sổ WPF không viền, trong suốt, luôn ở trên; đặt góc phải dưới WorkArea (trên taskbar, cạnh khay hệ thống). Bong bóng ✔ tiêu đề + mô tả. Âm `SystemSounds.Asterisk` + 2 nốt (1568 Hz, 2093 Hz). Click trái để ẩn, click phải mở Dashboard rồi ẩn. Script tự chạy lại ở tiến trình STA ẩn nên không chặn agent.
- `AGENTS.md` §20 và `docs/process/HERMES_DISPATCH_PROMPT.md` mục 6: RC và Hermes gọi script khi Done (thay `pipip`).

## Kiểm
- Parse PowerShell OK. Thử WPF tối giản: cửa sổ hiện ở (1700,794), màn 1920×1080.
- Lỗi lần đầu: tham số tiếng Việt có dấu cách không được đặt trong ngoặc kép khi tự chạy lại, nên tiến trình con không hiện. Đã sửa (hàm `Q`).
- Demo thật: ảnh chụp riêng góc phải dưới `docs/sessions/2026-10-15/notify/demo-popup-corner.png`.

## Hoàn tác
Xoá `scripts/notify_done.ps1`, `static/notify/`. Chép lại bản sao `docs/sessions/2026-10-15/notify/*.bak-before-notify` cho AGENTS.md và HERMES_DISPATCH_PROMPT.md.

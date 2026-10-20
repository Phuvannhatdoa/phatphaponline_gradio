# Session: tasktodo.md 2-file split (2026-09-07)

## Mục tiêu
Split `docs/tasktodo.md` (489 dòng) thành 2 file:
- `tasktodo.md` — chỉ ACTIVE tasks (~60 dòng)
- `taskdone.md` — archive DONE tasks (~416 dòng, append-only)

## Kết quả
- `docs/tasktodo.md` mới: ~60 dòng, chỉ ACTIVE/PENDING/BLOCKED tasks + header protocol
- `docs/taskdone.md` tạo mới: ~416 dòng, toàn bộ DONE entries từ T16-T101

## Protocol được thêm vào header tasktodo.md
> PROTOCOL: Khi file > 500 dòng → move DONE entries sang taskdone.md + git commit.
> Khi task Done → move entry sang taskdone.md trong cùng commit.

## Lý do 500-line protocol
- Claude không thể tự trigger — phải được gọi mỗi khi cần thanh lý
- Ghi vào header như convention/protocol để nhắc nhở

## Tiết kiệm token
- Trước split: 489 dòng mỗi lần load
- Sau split: ~60 dòng (tasktodo.md) — tiết kiệm ~85% token khi load file tracking
- taskdone.md chỉ cần load khi cần tra cứu lịch sử

## Files thay đổi
- `docs/tasktodo.md` — ghi đè (ACTIVE only)
- `docs/taskdone.md` — tạo mới (DONE archive)
- `docs/sessions/2026-09-07_tasktodo_split.md` — session log này

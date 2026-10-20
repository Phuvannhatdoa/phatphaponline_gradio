# Handoff — T393 FoJin Local Test Runbook — 2026-10-15

## 1. Bảng thông tin đọc nhanh
| Mục | Giá trị |
|---|---|
| Task | T393, ✅ DONE — Runbook tự chứa `docs/FOJIN-TEST-RUNBOOK.md` (15 mục) |
| HEAD قبل | 253c840 |
| Commit | pending |
| Files | `docs/FOJIN-TEST-RUNBOOK.md`, `tasks/T393-fojin-local-test-runbook.md`, `docs/tasktodo.md`, `docs/ROLLBACK.md` |
| Tests | guard PASS; dup:ids baseline 1 (T274, pre-existing); không có kiểm thử JS mới |
| DB/TTL/ETL | 0 mutation |

## 2. Đọc trong 2 phút
Nhận được yêu cầu dựng FoJin local, pha khảo sát Мне): máy hiện tại thiếu Docker, RAM trống chỉ ~2GB, C: trống 8GB → DỪNG và báo cáo (R7). Sau đó xuất bản runbook tự chứa cho agent khác: tham số chốt (ports, services giữ/bỏ), 8 ràng buộc cứng, hướng dẫn cài Docker (người dùng làm tay), 2 sửa code đã duyệt, bootstrap index ES trước import, 10 kinh Hán + 10 kinh Việt giả định (table đối chiếu), 6 tiêu chí test với commander và ngưỡng PASS, lệnh start/stop/dọn riêng moi trường test, mẫu báo cáo bàn giao, checklist exit Plan Mode.

## 3. Phần đã xây + chứng cứ
- Runbook 15 mục, tự chứa: agent khác đọc là setup được mà không hỏi.
- Task file `T393` với id: T393, former_ids [].
- Tambah tự kiểm guard PASS + baseline dup:ids giữ nguyên.
- 0 database mutation.
- Revert: `git revert --no-edit` (doc-only, 0 DB).

## 4. Cảnh báo bắt buộc
- **Docker chưa cài** → không thể chạy Giai đoạn 2; chờ người dùng cài theo §3.
- **RAM trống 2,08 GB** < 5 GB ngưỡng → phải đóng bớt app.
- **C: trống 8,3GB** < 10 GB → BAL 必須 chuyển Docker data root sang `E:\DockerData` trước khi kéo image.
- **33 file `D` trong docs/** (từ lần move April/May trước) chưa commit → không đụng tới.
- `docs/FOJIN-TEST-RUNBOOK.md` chỉ tài liệu: không sửa code FoJin, không đụng VPS, không đụng DB.

## 5. Revert từng phần
| Phần | Hoàn tác | Mất dữ liệu? |
|---|---|---|
| Runbook + task file | `git revert --no-edit <sha>` | Không |
| tasktodo/ROLLBACK | revert cùng commit | Không |

## 6. Bảng file tạo/sửa
| File | Thay đổi |
|---|---|
| `docs/FOJIN-TEST-RUNBOOK.md` | NEW (runbook 15 mục) |
| `tasks/T393-fojin-local-test-runbook.md` | NEW (task file) |
| `docs/tasktodo.md` | ADD T393:START block |
| `docs/ROLLBACK.md` | ADD T393 row |
| `docs/Handoff-2026-10-15-T393-fojin.md` | NEW (file này) |

## 7. Sai lầm / điều đã bị bác bỏ
- Ban đầu định viết runbook ra `E:\fojin-test\FOJIN-TEST-RUNBOOK.md` thì nhận ra thư mục chưa tồn tại; chuyển sang `(b)` lưu trong dự án Đạo Ảnh theo AGENTS.md §15.
- Thảo luận ban đầu flexible: đã đặt replicas cho `make_vn_drafts.py`; vì R4 cấm LLM nên script **không dịch**, chỉ sinh khung dữ liệu và ghi rõ "nháp chỉ phục vụ test".

## 8. Việc chưa xong
- Người dùng chưa cài Docker/WSL; chưa chuyển RAM/DISK; chưa có 10 kinh tiếng Việt thật.
- Sau khi có môi trường: chạy §6 bootstrap ES, §7 import CBETA 10, §8 nạp/soạn VN, §10 6 tiêu chí, §13 report.

## 9. Lệnh kiểm tra nhanh
```bash
cd /opt/.../Dai_Tang_Kinh/daoanh
python -X utf8 scripts/repo_guard.py               # PASS
python -X utf8 scripts/build_progress_data.py --check-dup-ids  # baseline T274
grep -n "FOJIN-TEST-RUNBOOK" docs/FOJIN-TEST-RUNBOOK.md
```

## 10. Ghi chú cho agent kế tiếp
- Runbook tự chứa; không cần phụ thuộc vào các file khác.
- Field `make_vn_drafts.py` chỉ được viết ra khi người dùng thực sự cần nháp; không tự thêm vào repo FoJin trước khi có môi trường.
- Khi người dùng có môi trường, bắt đầu từ §0 và §3. **Dừng ngay** nếu precondition thất bại.
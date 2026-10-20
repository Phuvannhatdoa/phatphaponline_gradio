# Handoff 2026-10-20 — Places/Districts: Claude XML import + Gemini batch (T432/T434)

## 1. Thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-20 ~16:20 |
| HEAD trước session commit | `20d30c1` (T428 Part 1 commit) |
| Task gốc | `tasks/T428-places-districts-claude-gemini-import.md` (đã được session song song đổi số) |
| Task hiện hành | **T432** (analysis/Claude import), **T434** (Gemini batch) — file `tasks/T432-places-districts-claude-analysis.md`, `tasks/T434-places-districts-gemini-batch.md` |
| Trạng thái Part 1 (Claude XML) | ✅ DONE, đã commit `20d30c1` |
| Trạng thái Part 2 (Gemini) | ⏸ **PAUSED theo Admin** — chờ session T427 xong (tránh ghi đè DB) |
| Backup Part 1 | `data/backups/T428_20261020_111026/lineage.db` (quick_check=ok) |
| Dữ liệu AI hiện có | places **16.555**/59.150, districts **5**/16.907 |
| Snapshot an toàn | `docs/sessions/2026-10-20/T428/ai_place_name_snapshot.tsv` (16.555 dòng), `ai_district_name_snapshot.tsv` (5) |
| Test | dry-run + verify chạy tay; chưa chạy `npm run pipeline` (chỉ sửa script mới) |

## 2. Đọc trong 2 phút

**Đã làm**
1. Part 1: import 2 XML Claude (`vn_place_name_vi.xml` 59.353 places, `vn_district_name_vi.xml` 16.907 districts) vào DB:
   - `namevi_map_places.name_vi`: **208 INSERT** (mới), 59.145 đã có sẵn giữ nguyên, 41 lệch Hán tự (không ghi đè).
   - Tạo bảng mới `codex_district_name` (16.907 dòng, có name_vi 16.907/16.907).
   - Không UPDATE bất kỳ bảng gốc nào (`places`, `places_dila` giữ nguyên).
2. Part 2: tạo `ai_place_name` + `ai_district_name`, viết script batch Gemini, chạy được **16.555 places + 5 districts** thì **dừng theo Admin**.

**Phát hiện quan trọng nhất**
- **Session song song T427 đang backup/restore `data/lineage.db`** (bằng chứng: `data/backups/T427-20261020-145225-round3followup-index/lineage.db` tạo 14:52). Lúc 13:15 DB có 13.755 dòng AI, 14:55 chỉ còn ~10.161 ⇒ dữ liệu AI bị ghi đè. Không phải lỗi script.
- Gemini API đang chập chờn: `503 UNAVAILABLE` + `500 INTERNAL` (10 batch lỗi trong ngày). Batch lỗi **tự retry** ở lần resume sau vì chưa được lưu.

**3 việc Admin cần làm/quyết**
1. Xác nhận T427 đã xong (session kia) rồi cho resume Part 2.
2. Quyết định spec `ai_district_name`: spec T434 ghi khóa theo **chuỗi district**, bản đã chạy khóa theo `dila_id` (PLA######).
3. Quyết định có đổi tên script theo spec (`ai_batch_transliterate_place.py`, log `logs/ai_transliterate_place.log`) hay giữ tên hiện tại.

## 3. Chi tiết từng phần

### Part 1 — Claude XML import (T432)
- Script: `scripts/t428_import_claude_xml.py` (`--dry-run` mặc định, `--apply`, `--verify`).
- Nguồn: nhánh `claude/sleepy-tesla-qsx17b`
  - places: 21.694.532 B, SHA256 `736f5ec6…52a56b`
  - districts: 2.307.461 B, SHA256 `73b82b9e…44ab07`
- Kết quả apply (11:10): places updated 0 / inserted 208 / skipped 59.145 / mismatched 41; districts inserted 16.907.
- Verify: `namevi_map_places` có name_vi 118.298; `codex_district_name` 16.907/16.907.
- Manifest: `docs/sessions/2026-10-20/T428/t428_manifest_20261020_111705.txt`.

### Part 2 — Gemini batch (T434)
- Bảng: `ai_place_name(dila_id PK, name_vi_ai, model, created_at)`, `ai_district_name(dila_id PK, ...)`.
- Script: `scripts/ai_batch_transliterate_places_districts.py` (`--element place|district`, `--limit`, `--reset`).
- Wrapper chạy nền: `scripts/t428_run_ai_full.py` (place → district, tuần tự).
- Đã thêm `_checkpoint()` (`PRAGMA wal_checkpoint(TRUNCATE)`) mỗi 20 batch + cuối run để chống mất dữ liệu WAL khi process bị kill.
- Chất lượng mẫu: `PL000000000001 → Khoát Tất Đa Quốc`, `PL000000000002 → Tích Nhã Kha Sơn`.
- Log: `logs/ai_transliterate.log`.

## 4. Cảnh báo bắt buộc
- **Không chạy batch AI khi session T427 còn restore DB.** Kiểm tra trước: `data/backups/T427-*` có mtime mới, hoặc COUNT `ai_place_name` tụt bất thường.
- Process nền bị shell tool kill sau ~20–40 phút ⇒ đừng chạy `Start-Process` dài; chạy chunk `--limit` trong foreground, hoặc kiểm tra tiến độ sau mỗi chunk.
- PID 6956 (python, 14:58) **không kill được** (Access denied) — thuộc session/user khác, không phải worker của ta.
- DB ở WAL mode; nếu kill process giữa chừng, committed rows có thể nằm trong WAL. Luôn `wal_checkpoint(TRUNCATE)` sau khi dừng.
- Không `git add` thư mục; dùng temp index theo AGENTS §14/§17.

## 5. Lệnh revert

| Task | Lệnh | Mất dữ liệu? |
|---|---|---|
| T432 (Claude XML) | `python -X utf8 scripts/t428_import_claude_xml.py --revert` **hoặc** restore `data/backups/T428_20261020_111026/lineage.db` | Không (208 dòng insert + 41 lệch không ghi) |
| T432 revert thủ công | `DELETE FROM namevi_map_places WHERE source='claude_xml_import'; DROP TABLE codex_district_name;` | Mất 208 tên mới + 16.907 district (tái tạo được từ XML) |
| T434 (Gemini) | `DELETE FROM ai_place_name; DELETE FROM ai_district_name;` rồi `DROP TABLE` | Mất kết quả AI; **snapshot TSV vẫn còn** để reload |

## 6. File tạo/sửa trong session

| File | Trạng thái |
|---|---|
| `scripts/t428_import_claude_xml.py` | mới, đã commit `20d30c1` |
| `docs/sessions/2026-10-20/T428/t428_manifest_20261020_111705.txt` | mới, đã commit `20d30c1` |
| `docs/ROLLBACK.md` | sửa, đã commit `20d30c1` (+ entry T432/T434 lần này) |
| `scripts/t428_setup_ai_tables.py` | mới |
| `scripts/ai_batch_transliterate_places_districts.py` | mới |
| `scripts/t428_run_ai_full.py` | mới |
| `docs/sessions/2026-10-20/T428/ai_place_name_snapshot.tsv` | mới (16.555 dòng) |
| `docs/sessions/2026-10-20/T428/ai_district_name_snapshot.tsv` | mới (5 dòng) |

## 7. Sai lầm đã vấp
- `Start-Process` nền bị kill 2 lần (43 phút, 18 phút) không traceback ⇒ mất thời gian. Nguyên nhân: shell tool kết thúc/kill cây process.
- Tưởng mất dữ liệu do WAL, thực ra chủ yếu do **session T427 restore DB**; WAL cũng góp phần nên đã thêm checkpoint.
- Script ban đầu có hàm trùng (`count_done`, `save_batch`, `reset_table` định nghĩa 2 lần) và thiếu `_checkpoint` — đã dọn, `ast.parse` OK.
- Task gốc T428 đã bị session khác đổi số (T432/T434) trong lúc làm ⇒ luôn re-check `tasks/` + `docs/tasktodo.md` trước khi cấp/ghi task.

## 8. Việc CHƯA xong (ưu tiên)
1. **Resume Gemini**: places còn 42.595, districts còn 16.902 — sau khi T427 xong.
2. **Spec deviation districts**: `ai_district_name` khóa `dila_id` vs spec "district chuỗi".
3. **Priority review files**: spec yêu cầu ưu tiên `review_needed_places.tsv` / `review_needed_districts.tsv` (3.352 dòng) — chưa tải/chưa xử lý.
4. **Log riêng**: spec muốn `logs/ai_transliterate_place.log`, hiện dùng `logs/ai_transliterate.log`.
5. **Tên script**: spec muốn `ai_batch_transliterate_place.py`.
6. Reload từ snapshot nếu DB bị restore: chưa có `--reload-from` (hiện phải import tay bằng TSV).

## 9. Lệnh kiểm tra nhanh
```powershell
python -X utf8 -u "$env:TEMP\opencode\t428_chk.py"           # counts
Get-Content logs/ai_transliterate.log -Tail 5
Select-String -Path logs/ai_transliterate.log -Pattern "503 UNAVAILABLE" | Measure-Object
Get-ChildItem data/backups -Filter "T427-*" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

## 10. Ghi chú cho agent kế tiếp
1. Chạy `npm run guard` + `dup:ids` trước khi commit.
2. Kiểm tra `data/backups/T427-*` mới nhất; nếu < 30 phút thì **không** chạy batch AI.
3. Resume: `python -X utf8 scripts/ai_batch_transliterate_places_districts.py --element place --limit 2000` (foreground, timeout ≥ 20 phút). Lặp đến hết; rồi `--element district`.
4. Sau mỗi lần dừng: `PRAGMA wal_checkpoint(TRUNCATE)` + export lại snapshot TSV.
5. Nếu phát hiện COUNT tụt: dừng ngay, báo Admin, không tiếp tục đốt quota.

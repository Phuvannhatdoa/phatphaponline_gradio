# OI-18 — Trùng ID T445 và T441 (chỉ phân tích, KHÔNG đổi file nào)

> Ngày: 2026-10-21 · Chế độ: CHỈ ĐỌC. Không sửa `tasks/`, không đổi tên file, không sửa `tasktodo.md`.
> Output dup-check: `docs/sessions/2026-10-21/qa/OI-18-dupids.txt`.

## (a) Kiểm trùng ID — tầng 1 (`npm run dup:ids` tương đương)

- Kết quả: **FAIL**, 1 ID trùng thật: **T445** giữa 2 file:
  - `tasks/T445-claude-place-name-import.md`
  - `tasks/T445-placevn-wizard-ui-b0-b9.md`
- Không có ID trùng nào khác. Các mục INFO (T172–T176 có bản `X-`, T199 có file phụ) là hợp lệ theo quy ước.
- Tầng 2 (trùng prose): tìm `T441` và `T445` trong `docs/tasktodo.md` (chỉ đọc). Kết quả: T445 xuất hiện ở dòng 22 và 798–800 (block wizard); **T441 không xuất hiện trong tasktodo**.

## (b) Bảng so sánh frontmatter T445

| Trường | `T445-claude-place-name-import.md` | `T445-placevn-wizard-ui-b0-b9.md` |
|---|---|---|
| `id` | T445 | T445 |
| `title` | Dry-run import phien am dia danh Claude (name_vi/name_zh theo dila_id) | Wizard UI cho T444 Gemini Places Translation (B0-B9) |
| `status` | in_progress | in_progress |
| `created` | 2026-10-21 | 2026-10-21 (nằm trong `timeline.created`) |
| `updated` | 2026-10-21 | (không có) |
| `depends_on` | (không có) | [T444] |
| Khác | `done_when`: dry-run CSV, không ghi DB, Admin xem báo cáo | `timeline.deadline` 2026-10-21, `priority: high`, `description` |
| Phạm vi | Đối chiếu `name_vi`/`name_zh` từ `vn_place_name_vi.xml` (chỉ SELECT) | UI wizard B0→B9 cho `placevn.html` (phụ thuộc T444) |

Hai file **không chung phạm vi** (đúng như ghi chú "Admin quyết giữ riêng" trong OPEN-ITEMS). Vấn đề là **trùng số**, không phải trùng việc.

### Mức độ tham chiếu (đã kiểm bằng grep)

- **Claude** (`T445-claude-...`): được nhắc trong `tasks/T446-tab-place-live-compare.md` (dòng 12, 51), `tasks/T443-places-districts-claude-import.md` (dòng 43), `scripts/import_claude_place_name_dryrun.py` (dòng 3, 309; User-Agent `T445-dryrun` ở dòng 119), `app.py` dòng 12255 (comment). Chưa có trong `tasktodo.md`. Không có `docs/plans/` đi kèm.
- **Wizard** (`T445-placevn-...`): được nhắc trong `docs/tasktodo.md` (dòng 22 và block `<!-- T445:START -->` 798–800, đã công bố), `docs/plans/T445-TASK-SUMMARY.md` (có đi kèm), và kế hoạch `docs/plans/T445-wizard-ui-plan.md` được khai báo ở task nhưng **chưa tồn tại** (glob không thấy).

## (c) Đề xuất: đổi số file CLAUDE, giữ WIZARD (chỉ đề xuất)

Áp dụng thứ tự ưu tiên AGENTS §16 (footprint nhỏ nhất):

1. **Status kết thúc:** cả hai `in_progress` → hòa.
2. **Ít tham chiếu:** gần hòa. Claude có nhiều tham chiếu trong code/script (script, app.py comment), wizard có tham chiếu trong tasktodo (file được auto-maintain). Không phân định rõ, không dùng làm quyết định.
3. **Không có `docs/plans|reports` đi kèm:** **Claude không có; Wizard có** (`docs/plans/T445-TASK-SUMMARY.md`) → đổi **Claude**.
4. **ID đã công bố trong `tasktodo.md`:** **Wizard đã công bố** (block T445 ở dòng 798–800), Claude thì không → đổi **Claude**.

**Kết luận: đổi số `tasks/T445-claude-place-name-import.md`.** Tiêu chí 3 và 4 quyết định, không cần đến tiêu chí 2.

**ID đề xuất: T451.** Kiểm trùng 2 tầng: `T451`–`T455` không xuất hiện trong `daoanh/` (tasks, docs, tasktodo, scripts). **Phải kiểm lại ngay trước khi cấp** (AGENTS §16).

### Danh sách thay đổi KHI Admin duyệt (chưa làm)

1. Đổi tên `tasks/T445-claude-place-name-import.md` → `tasks/T451-claude-place-name-import.md`; frontmatter `id: T451`; thêm `former_ids: [T445]` (AGENTS §16).
2. `tasks/T446-tab-place-live-compare.md` dòng 12 và 51: `T445` → `T451`, đường dẫn tương ứng.
3. `tasks/T443-places-districts-claude-import.md` dòng 43: `T445` → `T451`, đường dẫn tương ứng.
4. `scripts/import_claude_place_name_dryrun.py` dòng 3 và 309 (header, banner in ra). Dòng 119 (User-Agent `T445-dryrun`) là tuỳ chọn.
5. `app.py` dòng 12255 (comment): `(T445)` → `(T451)`. `app.py` đang có WIP phiên khác (xem OI-8/OI-9), nên sửa dòng này phải tách khỏi hunk của task khác.

**Không sửa:** `docs/sessions/2026-10-21/**` và `OPEN-ITEMS.md` (log lịch sử, ghi đúng hiện trạng tại thời điểm đó); `docs/Handoff-2026-10-21-T448-*.md` và `docs/sessions/.../T416_REPORT.md` (lịch sử, có nhắc "T445" như WIP).

Ghi chú khi thực hiện: file `T445-claude-...` đang `??` (untracked). Đổi tên không vướng index, nhưng vẫn phải ghi vào ROLLBACK và AGENTS §14.

## (d) T441 — chỉ ghi nhận, KHÔNG sửa (thuộc phiên khác)

- `tasks/T441-etl-load-only-unpassed.md`: `id: T441`, `title: "Tab ETL namevimap.html chỉ load ID chưa PASS"`, `status: in_progress`, `created: 2026-10-21`, `updated: 2026-10-21`.
- **Không có `former_ids`.** Vì vậy grep theo ID cũ (nếu có) sẽ không thấy liên kết.
- Dup-check không báo T441 trùng (chỉ có 1 file). Không có dòng T441 trong `tasktodo.md`.
- OPEN-ITEMS OI-18 ghi "T441 trùng số với T441 plan trước đây". **Chưa tìm được file plan T441 nào** trong `docs/plans/` (glob `docs/plans/T441*` rỗng). Cần Admin hoặc phiên gốc chỉ ra đường dẫn của plan cũ đó, nếu không thì không xác minh được.
- Đề xuất cho sau: khi đổi số theo (c) hoặc khi chốt T441, thêm `former_ids` nếu ID cũ có tồn tại ở đâu đó.

## Việc Admin cần quyết (theo OPEN-ITEMS OI-18)

1. Chấp nhận đổi file CLAUDE sang T451 (mục c), hay giữ nguyên và đổi wizard (không khuyến nghị, vì vi phạm tiêu chí 3 và 4).
2. Chỉ ra plan T441 cũ (nếu có) để xác nhận trùng số thật.

# Session 2026-09-06 — T94 Phase 3: Duyệt chuẩn thủ công (manual_verified alignment)

**Task:** T94 — Phase 3 · Admin workflow fill alignment `manual_verified` hoàn tất

## Nội dung

Phạm vi admin đã duyệt (**3A đầy đủ**): backend endpoint + nút "✓ Duyệt chuẩn"
trong `admin/translation_monitor.html` + chip "✓ Đã kiểm chứng" ở reader.

### Backend (`app.py`)
1. `_T95_UNITS_SQL` (+ _t95_badge): thêm subquery `manual_verified_n`
   (alignment `manual_verified` + `review_status='verified'` cho unit) → units API
   trả thêm `manual_verified: bool` mỗi unit. Additive.
2. `api_t95_job_detail`: item trả thêm `translation_id` (translation hiện hành,
   non-superseded, revision max) để monitor biết segment nào duyệt được. Additive.
3. Endpoint mới `POST /daoanh/api/admin/translation/verify`:
   - Body: `passage_id` (bắt buộc), `reviewer` (mặc định `admin`), `note`.
   - Giải quyết translation hiện hành của passage → 404 nếu không có.
   - `UPDATE translation_segments SET quality_status='reviewed', review_status='verified', reviewer=?`
   - DELETE + INSERT idempotent `passage_translation_alignment`
     `(alignment_type='manual_verified', confidence=1.0, alignment_method='manual_admin_verify',
     review_status='verified', reviewer, note)`.
   - Badge reader `reviewed` + coverage `reviewed` + export `hoàn chỉnh` đều tích hợp
     sẵn vì dùng `quality_status='reviewed'`.

### Admin UI (`admin/translation_monitor.html`)
- Thêm helper `esc`/`escAttr` (trước giờ không có).
- Trong `details()`: item có `translation_id` → nút `✓ Duyệt chuẩn`
  gọi `verifySegment(this, passage_id)` → POST verify (confirm trước).
  Thành công → thay nút bằng `✓ đã duyệt` + reload jobs.

### Reader (`places.html`)
- Unit render: khi `u.manual_verified=true` → chip `✓ Đã kiểm chứng` (green)
  cạnh badge trạng thái. Không thay đổi nội dung/không sửa luồng T96/T98.

## Kiểm chứng (không đụng data thật)
| Hạng mục | Kết quả |
|---|---|
| `python -m py_compile app.py` | ✅ OK |
| `node --check` JS extract places.html | ✅ OK |
| `node --check` JS extract translation_monitor.html | ✅ OK |
| `npm run test` | ✅ Tests passed |
| `npm run e2e` | ✅ All pages passed |
| test_client + DB tạm (9 asserts) | ✅ ALL PASS |

Test client DB tạm: 404 passage không có translation; verify thành công
(quality_status=reviewed, review_status=verified, reviewer, 1 alignment
manual_verified confidence 1.0); idempotent (verify lại → vẫn 1 dòng alignment);
400 khi thiếu passage_id.

SQL mới chạy trên DB thật (read-only): units 4061 T50n2060 → 9 units,
`manual_verified_n`=0 (chưa ai duyệt), sample translation_id
`cbeta:T50n2060:t001947:r001` quality_status `unreviewed`; job item → translation_id
`cbeta:T50n2060:t000001:r001`.

## Lưu ý vận hành
- **Restart server cần thiết** để endpoint + SQL mới có hiệu lực:
  `python app.py` (port :5000) — trước khi dùng nút "✓ Duyệt chuẩn".
- **Rollback 1 lượt duyệt thủ công** (SQL):
  ```sql
  DELETE FROM passage_translation_alignment WHERE passage_id='<passage_id>'
    AND translation_id='<tid>' AND alignment_type='manual_verified';
  UPDATE translation_segments SET quality_status=NULL, review_status='pending',
    reviewer=NULL WHERE translation_id='<tid>';
  ```
- Data hiện tại: 11 translation_segments `completed` (T95 live) + T96 translate —
  đều `review_status=pending`/`quality_status=unreviewed` → admin có thể duyệt dần.
- Lint PowerShell (`npm run lint`) vốn lỗi ESM trên Windows (pre-existing,
  `scripts/lint-check.ps1` node --check temp file không đuôi .js) — không do Phase 3.

## Files đổi
- `app.py` (3 edits + 1 endpoint mới)
- `admin/translation_monitor.html` (esc + nút Duyệt chuẩn + verifySegment)
- `places.html` (chip manual_verified)

## Rollback
- Code: `git revert <commit>`
- Data: restore backup `lineage.db.backup_*` hoặc SQL rollback ở trên.
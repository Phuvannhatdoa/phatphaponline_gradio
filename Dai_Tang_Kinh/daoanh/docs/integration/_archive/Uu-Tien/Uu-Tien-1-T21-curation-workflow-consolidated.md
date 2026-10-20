# M21 · Buddhist Curation Workflow

**Status:** 📄 Consolidated Documentation  
**Module:** M21  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quy trình curation cho nội dung Phật học:editor dashboard, dispute UI, audit log, bulk review, và conflict pool để quản lý và giải quyết các vấn đề nội dung Phật học.

## UI/UX

- **Trang Dashboard biên tập:** `/daoanh/editor-dashboard`
  - 7 tab: Content overview, Disputes, Audit log, Bulk review, Conflict pool, Claims unverified, Not indexed
   - Mỗi tab hiển thị thống kê và danh sách tương ứng

- **Trang UI tranh chấp:** `/daoanh/conflicts`
  - Hiển thị tranh chấp DILA↔MARCUS
   - Cách giải quyết: Keep both, Reject both, Pick one

- **Trang Audit Log:** `/daoanh/audit-log`
  - Hiển thị log audit: 9,000+ rows
   - Tìm kiếm: Theo thời gian, theo loại tranh chấp, theo trạng thái

- **Trang Review Bulk:** `/daoanh/bulk-review`
  - Review hàng loạt: ≤500 claims cùng một lúc
   - Chức năng: Review và xác minh hàng loạt

- **Pool tranh chấp:** `/daoanh/conflict-pool`
  - Pool tranh chấp: 40,327 (40,321 mở) claims chưa giải quyết
   - Claims unverified: 447,885

## Dữ liệu

- **Audit log:** 9,000+ rows entries
- **Claims unverified:** 447,885 claims chờ xác minh
- **Conflict pool:** 40,327 claims đang mở
- **Thể loại:** DILA↔MARCUS, DILA↔DILA, MARCUS↔MARCUS

## Acceptance criteria

- [ ] Dashboard biên tập hiển thị đúng 7 tab chức năng
- [ ] UI tranh chấp hiển thị 2 nút "⟷ Giữ cả hai" và "✗ Bác bỏ cả hai"
- [ ] Audit log hiển thị đúng 9,000+ rows entries
- [ ] Review bulk hoạt động với ≤500 claims cùng một lúc
- [ ] Conflict pool hiển thị đúng 40,327 claims đang mở
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ nội dung tranh chấp nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getEditorDashboard()` - Lấy dashboard biên tập
2. `getConflictsList()` - Lấy danh sách tranh chấp
3. `getAuditLog(filter)` - Lấy log audit theo bộ lọc
4. `bulkReview(claims)` - Review hàng loạt claims

**File path:** `docs/Mimo-Flash/M21-curation-workflow-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), DB access cho audit log và conflict pool
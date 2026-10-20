# M28 · Buddhist Lineage Tree

**Status:** 📄 Consolidated Documentation  
**Module:** M28  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp cây伝承 Phật giáo: trực quan hóa mạch truyền承 từ Bồ-đề đến các Sư hiện đại, bao gồm quan hệ thầy-đệ tử, trường phái, và địa lý tán распростран.

## UI/UX

- **Trang Cây伝承:** `/daoanh/lineage/tree`
  - Hiển thị cây伝承: Từ Bồ-đề đến các Sư hiện đại
   - Tương tác: Click vào Sư để xem chi tiết, thu phóng/ thu nhỏ cây, lọc theo phái hoặc địa lý

- **Trang Chi tiết Sư:** `/daoanh/lineage/master`
  - Hiển thị thông tin Sư: Tên, linh mệnh, giáo lý, học trò, địa lý
   - Quan hệ: Học trò, thầy của, trường phái liên quan

- **Trang Lọc và Tìm kiếm:** `/daoanh/lineage/search`
  - Tìm kiếm Sư: Theo tên, phái, địa lý
   - Filt lọc: Theo thời gian, theo quan hệ (thầy-đệ), theo địa lý

## Dữ liệu

- **Số Sư:** 1000+ Sư Phật giáo trong cây传承
- **Quan hệ:** 5000+ quan hệ thầy-đệ, trường phái liên quan
- **Thông tin mỗi Sư:** Tên, linh mệnh, giáo lý chính, học trò prominent, địa lý传播
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 1000+ Sư trong cây传承
- [ ] Quan hệ thầy-đệ đúng 85% so với dữ liệu ground truth
- [ ] Tìm kiếm Sư đúng 90% theo tên/pai/di địa lý
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin伝承 nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getLineageTree()` - Lấy cây传承
2. `getMasterDetail(masterId)` - Lấy chi tiết Sư
3. `searchMasters(query)` - Tìm kiếm Sư
4. `getLineageFilters()` - Lấy bộ lọc传承

**File path:** `docs/Mimo-Flash/M28-lineage-tree-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), lineage DB, graph data structure
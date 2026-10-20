# M97 · Living Dharma Knowledge Graphs

**Spec · P2**

# M97 Đồ thị Triết lý Dharma Sống

Cung cấp đồ thị Triết lý Dharma sống: xây dựng và duy trì đồ thị kiến thức Phật giáo liên tục cập nhật, bao gồm quan hệ giữa các Sư, truyền承, Kinh, và các khái niệm thiền.

## Mục đích

Thực hiện knowledge graphs cho Dharma sống: cho phép practitioner truy cập và khám phá các quan hệ giữa các yếu tố Dharma theo cách trực quan và liên hệ, từ Sư truyền承 đến các triết lý hiện đại.

## UI/UX

- **Trang Dồ thị Triết lý:** `/daoanh/knowledge-graph/explore`
  - Hiển thị đồ thị: Các nút (Sư, Kinh, Khái niệm) và các đường (truyền承, quan hệ, tương thích)
   - Tương tác: Click vào nút để xem chi tiết, kéo/thả để điều chỉnh xem
   - Bộ lọc: Lọc theo thời gian, nguồn gốc, thể loại

- **Trang Đường truyền承:** `/daoanh/knowledge-graph/lineage`
  - Hiển thị truyền承: Đường truyền từ Bồ-đề đến Sư hiện tại
   - Tìm kiếm Sư: Tìm kiếm theo tên, école, quốc gia

- **Trang Khám phá khái niệm:** `/daoanh/knowledge-graph/concepts`
  - Khái niệm liên quan: Khi click vào một khái niệm, hiển thị các khái niệm liên quan
   - Tìm kiếm ngữ cảnh: Tìm kiếm theo ngữ cảnh (Thiền, Triết lý, Lễ hội)

## Dữ liệu

- **Nút đồ thị:** 1000+ nút (Sư, Kinh, Khái niệm, trường phái)
- **Đường đồ thị:** 5000+ quan hệ (truyền承, tác phẩm, quan hệ triết lý)
- **Cập nhật liên tục:** Dữ liệu được cập nhật hàng tuần từ nguồn uy tín
- **Tương thích:** Tất cả thiết bị: điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 1000+ nút và 5000+ quan hệ Triết lý
- [ ] Tìm kiếm Sư/Kinh nhanh chóng (< 2s)
- [ ] Cập nhật dữ liệu hàng tuần thành công
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu đồ thị với bên thứ ba

## File tương tự

- `docs/integration/M97-living-dharma-knowledge-graphs.md`
- `docs/Mimo-Flash/T173-m97-living-dharma-knowledge-graphs.md`
# M18 · Triết lý trực quan hóa cho Tiến sĩ

**Spec · P2**

# M18 Triết lý trực quan hóa dữ liệu Phật giáo

Hệ thống trực quan hóa dữ liệu Phật giáo nâng cao cho trình độ Tiến sĩ: advanced graph visualization, temporal analysis, spatial dashboards, và insight generation.

## Mục đích

Cung cấp các công cụ trực quan hóa phức tạp cho dữ liệu Phật giáo: trajectory analysis, trend detection, correlation mapping, và dashboard可 customization cho trình độ Tiến sĩ.

## UI/UX

- **Trang Dashboard Tương tác:** `/daoanh/viz/interactive`
  - Multiple view: graph, timeline, map simultaneous
  - Brush and select: chọn node/edge, xem phụ thuộc
  - Timeline slider: điều khiển thời gian, xem évolution

- **Trang Phân tích tương quan:** `/daoanh/viz/correlation`
  - Heatmap: correlation giữa các entity types
  - Scatter plot: quantity over time, by dynasty
  - Network diagram: centrality, community detection

- **Trang Dashboard cá nhân:** `/daoanh/viz/personal`
  - Layout customizable: user chọn widget muốn hiển thị
  - Export: PNG, PDF, Interactive HTML
  - Share: URL share trạng thái dashboard hiện tại

## Dữ liệu

- **Graph data:** 912 nodes from RDF, 2865 monk names
- **Temporal data:** Founding dates, dynasty periods, lifespan
- **Spatial data:** DILA places (58.500 coordinates), GeoJSON
- **Metadata:** Source, authority score, verification status

## Acceptance criteria

- [ ] Tải graph 912 nodes dưới 2s
- [ ] Correlation heatmap hiển thị đúng 16+ entity type pairs
- [ ] Timeline slider hoạt động mượt mà cho dữ liệu 2000+ years
- [ ] Widget personalization lưu preference user
- [ ] Export chất lượng cao (300dpi PNG, vector PDF)

## File tương tự

- `docs/integration/M18-visualization-philosophy.md`
- `docs/Mimo-Flash/T93-m18-visualization-philosophy.md`
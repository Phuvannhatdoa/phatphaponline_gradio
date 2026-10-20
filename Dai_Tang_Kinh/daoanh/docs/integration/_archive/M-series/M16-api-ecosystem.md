# M16 · Ecosystem API cho Tiến sĩ

**Spec · P2**

# M16 Tạo ecosystem API

Phát triển ecosystem API hoàn chỉnh cho dữ liệu Phật giao: REST endpoints, versioning, authentication, và rate limiting cho trình độ Tiến sĩ.

## Mục đích

Cung cấp API chuẩn cho các ứng dụng bên thứ ba, nghiên cứu viên, và tích hợp với hệ thống bên ngoài, đáp ứng yêu cầu kỹ thuật cao cho trình độ Tiến sĩ.

## UI/UX (Developer Portal)

- **Trang Dokumentation:** `/api/docs`
  - Swagger/OpenAPI spec tự động tạo
  - Try endpoint trực tiếp từ browser
  - Example responses cho từng endpoint

- **Trang Auth management:** `/api/auth`
  - Tạo API key, quản lý quyền
  - Rotate key, revoke access
  - Audit log cho từng API call

- **Trang Rate limits:** `/api/limits`
  - Hiển thị quota hiện tại
  - Tang level khi cần
  - Xem sử dụng hôm/năm

## API Endpoints (20 endpoints)

| Endpoint | Mô tả |
|----------|-------|
| `GET /api/v1/monk-names` | Tất cả tên thầy đồ (2865) |
| `GET /api/v1/monk?name=` | Tra cứu monk theo tên |
| `GET /api/v1/lineage?name=` | Lấy lineage (thầy + đệ tử) |
| `GET /api/v1/details` | Full biography từ GraphDB |
| `GET /api/v1/trace?name=` | Trace về gốc (Ma Ha Ca Diếp) |
| `GET /api/v1/monk-names/autocomplete` | Auto-complete cho search |
| `GET /api/v1/search_monk?q=` | Substring search monk |
| `GET /api/v1/geo/reconcile` | Đối chiếu địa lý |
| `GET /api/v1/preservation/status` | Trạng thái bảo lưu |
| `GET /api/v1/analytics/overview` | Tổng quan analytics |
| `POST /api/v1/admin/claims/bulk-review` | Bulk review claims |
| `GET /api/v1/admin/audit/trail` | Audit trail public |
| `GET /api/v1/preservation/checksum` | Tạo checksum file |
| `GET /api/v1/glossary/search` | Tra cứu từ glossary |
| `GET /api/v1/graph/explore` | Explore knowledge graph |
| `POST /api/v1/graph/advanced` | Advanced graph query |
| `GET /api/v1/parallel/align` | Parallel text alignment |
| `GET /api/v1/version` | API version info |

## Acceptance criteria

- [ ] Tất cả 20 endpoints trả response chuẩn JSON
- [ ] Swagger docs cập nhật tự động khi thêm endpoint mới
- [ API key authentication hoạt động đúng 99%+ requests
- [ ] Rate limiting ngăn chặn abuse (100 req/min per key)
- [ ] Test suite coverage > 80% cho các endpoint

## File tương tự

- `docs/integration/M16-api-ecosystem.md`
- `docs/Mimo-Flash/T91-m16-api-ecosystem.md`
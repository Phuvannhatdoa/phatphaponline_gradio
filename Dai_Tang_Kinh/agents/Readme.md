# PHẬT TỔ ĐẠO ẢNH - Buddhist Heritage Mapping

> **VERSION:** 2026-08-28
> **Status:** ✅ Hệ thống Đạo Ảnh + Cổng Nhân Vật Học (T51) hoạt động
> **Live:** https://phatphaponline.org/daoanh/
> **Admin:** https://phatphaponline.org/daoanh/admin/

---

## Giới thiệu

Hệ thống ánh xạ Di sản Phật giáo Việt Nam (Phật Tổ Đạo Ảnh / TGS), tích hợp nhiều nguồn dữ liệu học thuật đáng tin cậy (DILA, CBETA, Wikidata, CHGIS, Marcus SNA…) thành một trung tâm tra cứu tri thức thống nhất (SSOT).

## Kiến trúc máy chủ

| Máy chủ | File | Cổng | Vai trò |
|---------|------|------|---------|
| **Auth Gateway** | `server.py` | 5001 | Đăng nhập (Gmail), quản lý phiên |
| **Main Server** | `app.py` | 5000 | Toàn bộ logic nghiệp vụ (Đạo Ảnh, TTL, Marcus, dossier, dịch thuật) |
| **Local Gateway** | `local_gateway.py` | 8080 | Static + proxy cho môi trường local |

## Tính năng chính

| Khu vực | Mô tả |
|---------|-------|
| **Đạo Ảnh Mapping** | Ánh xạ địa danh theo nhiều lớp nguồn (DILA, Wikidata, CHGIS, TGAZ, BGIS) |
| **TTL Ontology** | Truyền thừa Thiền Tông dạng đồ thị tri thức (namespace `pth:` + `dila:`) |
| **Nhân Vật Học Portal (T51)** | Tra cứu Tăng/Ni — tiểu sử, phả hệ Marcus, địa danh, kinh điển, xuất hiện trong kinh |
| **CBETA Content (T53)** | Tăng cường dữ liệu kinh điển CBETA |
| **CBETA Analytics (T54)** | Bảng điều khiển phân tích CBETA |

## Công nghệ

- **Backend:** Flask (Python)
- **Cơ sở dữ liệu:** SQLite (`data/lineage.db`) + GraphDB (SPARQL, `data/cbeta/cbeta.db`)
- **Frontend:** Tailwind CSS + Lucide Icons, biểu tượng Hoa Sen (Lotus Done)
- **Giao diện:** Amber Gold (#d97706) trên Dark Slate (#020617), font Inter + Noto Serif TC

## Nguyên tắc

- **Zero-RAM:** Không nạp toàn bộ 2.000 file kinh văn vào RAM (Byte-offset mapping, Index-based search, generator).
- **Bất biến dữ liệu:** Raw files không bao giờ bị ghi đè; mọi cải tiến đều cộng dồn (additive), có thể revert.

## Liên kết nhanh

| Tài liệu | Mô tả |
|----------|-------|
| `deep-research-report.md` | Báo cáo nghiên cứu chuyên sâu |
| `phat_to_dao_anh.md` | Bản đồ Phật Tổ Đạo Ảnh |
| `Research.md` | Tài liệu nghiên cứu |
| `reports/` | Các báo cáo phân tích |
| `SESSION.md` | Trạng thái phiên làm việc |
| `DEPLOY_LOGS.md` / `LOGS.md` | Nhật ký triển khai |

---

*Cập nhật lần cuối: 2026-08-28*

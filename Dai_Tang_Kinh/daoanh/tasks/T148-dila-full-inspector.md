---
id: T148
title: "Hiển thị đầy đủ tiểu sử DILA trong inspector Truyền Thừa (listBibl, worksBy, worksInTripitaka, mentionedIn, alt names)"
module: truyenthua
priority: high
status: done
depends_on: [b1f52fc, T145]
created: 2026-09-16
updated: 2026-09-16
done_when:
  - "[x] Parse DILA Person Authority XML (48.7MB) một lần vào RAM khi khởi động (background thread)"
  - "[x] Endpoint GET /daoanh/api/person/<id>/dila_full trả về alt_names, listbibl, works_tripitaka, works_by, mentioned_in"
  - "[x] Inspector hiển thị: Tên khác (DILA), Trích dẫn CBETA, Kinh điển trong Đại Tạng, Tác phẩm, Được đề cập trong"
  - "[x] Race condition guard: _dilaExtraPid đảm bảo kết quả cũ không ghi đè node mới"
  - "[x] Nếu person không có extra data → div rỗng, không crash"
  - "[x] Browser verified: A000001 (金總持) hiển thị đầy đủ 5 sections"
---

## Mô tả

Trước T148, inspector Truyền Thừa chỉ hiển thị `bio` — tức là trường `note type="concise"` từ DILA.
Dữ liệu phong phú hơn (tên thay thế, CBETA citations, kinh điển Đại Tạng, tác phẩm, nguồn đề cập)
có trong file XML gốc nhưng **chưa import vào bảng `people`** (chỉ import `bio`).
Bảng `people_full` (có schema đúng) tồn tại nhưng rỗng (0 rows).

## Giải pháp

### Backend (`app.py`)

**Module-level lazy index** `_T148_DILA_EXTRA`:
- Parse `data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml`
  một lần tại startup (background daemon thread, không block server)
- Dùng `xml.etree.ElementTree.iterparse` để stream qua file 48.7 MB hiệu quả
- Cache kết quả trong `_T148_DILA_EXTRA` dict (keyed by DILA id)
- Thread-safe via `_T148_EXTRA_LOCK` + `_T148_EXTRA_LOADED` flag

**Endpoint mới:** `GET /daoanh/api/person/<id>/dila_full`
- Gọi `_t148_get_extra(pid)` → load lazy nếu chưa có
- Trả về: `{ok, has_extra, alt_names[], listbibl[], works_tripitaka, works_by, mentioned_in}`

### Frontend (`places.html`)

**Hàm mới:**
- `_loadDilaExtra(pid)` — fetch `/dila_full`, gọi `_renderDilaExtra`
- `_renderDilaExtra(container, d)` — render 5 sections vào `#lin-dila-extra`
- `_dilaExtraPid` — race condition guard

**Placeholder div:** `<div id="lin-dila-extra">` thêm vào cuối `ev[]` trong `_renderLineageInspector` (kể cả khi không có bio). Sau `_setLineageEvidence()`, gọi `_loadDilaExtra(pid)`.

## Acceptance Criteria Verification

Browser verified với A000001 (金總持 / Kim Tổng Trì):
- ✓ TÊN KHÁC (DILA): 金揔持, 寶輪大師, 明因妙善普濟法師 (3 badge pills)
- ✓ TRÍCH DẪN CBETA (3): T15n0634, T17n0763, X77n1524
- ✓ KINH ĐIỂN TRONG ĐẠI TẠNG: T0763, T1188, A1504
- ✓ TÁC PHẨM: 3 bản dịch với tham chiếu
- ✓ ĐƯỢC ĐỀ CẬP TRONG: Phật Tổ Thống Ký + Tân Tục Cao Tăng Truyện

Browser verified với A002233 (Huệ An):
- ✓ TÊN KHÁC (DILA): 惠安
- ✓ TRÍCH DẪN CBETA (3): 3 citations từ T50n2059
- ✓ Không có works/mentionedIn → không hiển thị section đó

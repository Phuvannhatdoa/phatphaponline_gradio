# _archive — tài liệu tích hợp đã lưu trữ (T277)

Chuyển ngày 2026-10-10 theo phê chuẩn Admin. **Không xóa file nào.** Mọi file có trong `MANIFEST.tsv` (đường dẫn cũ → mới).

- `M-series/` — 111 file: module tính năng M6–M137. Năm bản "consolidated" trùng số kế hoạch đã đổi thành T278–T282 (xem bảng dưới).

| Tên cũ | Tên mới |
|---|---|
| M1-education-buddhist-consolidated.md | T278-education-buddhist-consolidated.md |
| M2-gis-buddhist-consolidated.md | T279-gis-buddhist-consolidated.md |
| M3-buddhist-relics-consolidated.md | T280-buddhist-relics-consolidated.md |
| M4-buddhist-calendar-consolidated.md | T281-buddhist-calendar-consolidated.md |
| M5-source-tracking-consolidated.md | T282-source-tracking-consolidated.md |

- `Uu-Tien/` — 119 file: bản viết lại theo chủ đề của M-series (cùng số module, khác nội dung).

**Không dùng trực tiếp.** Các file này chưa có checklist được tick, không có nguồn số liệu, và nằm ngoài 25 nguồn. Khi tích hợp, phải viết lại theo task lớn [T277](../../../tasks/T277-archive-and-future-integration.md).

Hoàn tác (đưa mọi file về chỗ cũ):

```bash
python -X utf8 scripts/t277_archive_integration.py --restore
```

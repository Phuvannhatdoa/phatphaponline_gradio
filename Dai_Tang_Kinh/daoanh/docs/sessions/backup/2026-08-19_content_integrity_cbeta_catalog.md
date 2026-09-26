# Session 2026-08-19 — Content Integrity & CBETA Catalog Join

## Tóm tắt

Session này tập trung vào nguyên tắc nội dung của hệ thống Phật Tổ Đạo Ảnh: loại bỏ các chức năng hiển thị data không có xuất xứ rõ ràng, thay bằng JOIN trực tiếp từ authority sources.

---

## Thay đổi đã thực hiện

### 1. Xóa block "Kinh Điển Liên Quan · Fuzzy Match"

**File:** `app.py`, `places.html`

**Lý do:** `cbeta_catalog_place_fuzzy` được tạo bằng RapidFuzz string matching (code-generated), không phải authority data. VD: `少室寺` match `少室六門` vì 2 chữ đầu giống nhau — không phải vì DILA nói hai cái đó liên quan.

**Thay thế:** Block mới "Kinh Điển Liên Quan" dùng JOIN trực tiếp (xem mục 2).

### 2. Implement "Kinh Điển Liên Quan" — T-series JOIN

**Backend (`api_places_cbeta`):**
```python
# Parse T-series refs từ listbibl → JOIN cbeta_catalog_vn
for m2 in re.finditer(r'CBETA\s+T\d+n(\d+)_', listbibl):
    sh = m2.group(1)
    cat = conn.execute(
        "SELECT title_zh, title_vi, translator_vi, dynasty_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ?",
        (sh,)
    ).fetchone()
    if cat and cat['title_vi']:
        related_texts.append({...})
```

**Frontend:** Block hiển thị `title_vi` (bold), `title_zh · dynasty_vi · translator_vi` (muted), với attribution label: *"Nguồn: Mục lục Đại Tạng Kinh — Nguyễn Minh Tiến (CC BY-SA 4.0) · Chỉ Đại Chính Tạng T-series"*

**Coverage thực tế:**
- T-series: 86% (86/100 unique texts có tên Việt)
- X-series: không show (0% — xem T20 để hiểu lý do)

### 3. Update CLAUDE.md — Rules mới

Bổ sung quy tắc core:

> Hệ thống Phật Tổ Đạo Ảnh chỉ làm công việc tích hợp các source có uy tín — không tự tạo chức năng xử lý data không có thật.
> Tiếp cận đúng: xác định repo có uy tín → trích xuất từ đó. Không có source → không làm.

### 4. Xóa block "Đoạn Văn Đề Cập · 15 đoạn" (từ session trước, ghi lại)

Block load từ `passage_entity` (auto-linked, có entries sai). Đã remove toàn bộ.

---

## Phân tích kỹ thuật: tại sao X-series = 0%

`cbeta_catalog_vn` (Nguyễn Minh Tiến) cover Đại Chính Tạng (T-series).
X-series (Tục Tạng / Zokuzokyo) dùng hệ đánh số độc lập:

```
X77n1524 ≠ Taisho T1524
X77n1524 = 補續高僧傳 (Extended Canon)
T1524    = 無量壽經優波提舍 (Taisho) — TEXT HOÀN TOÀN KHÁC
```

JOIN X-series refs vào cbeta_catalog_vn theo sh_number = sai hoàn toàn.

---

## Task mới tạo

**T20** — `tasks/T20-cbeta-xseries-vi-catalog.md`

Ghi lại:
- Gap hiện tại: T-series 86%, X-series 0%
- Hướng đến 100%: ETL từ CBETA GitHub + tổ chức dịch X-series catalog
- Cảnh báo kỹ thuật: KHÔNG nhầm lẫn X-series number với Taisho number
- Blockers: chưa có ai dịch X-series sang tiếng Việt (vấn đề ngôn ngữ)

---

## Tab ĐẠI TẠNG — trạng thái sau session

| Block | Nguồn | Status |
|-------|-------|--------|
| Văn Bản Đề Cập (refs) | `places_dila.listbibl` | ✅ DILA authority |
| Kinh Điển Liên Quan (tên Việt) | `cbeta_catalog_vn` (Nguyễn Minh Tiến) | ✅ 86% T-series |
| Tự Chí · Fosi Zhi | `places_dila.raw_xml` | ✅ DILA authority |
| ~~Fuzzy Match~~ | ~~cbeta_catalog_place_fuzzy~~ | ❌ Đã xóa |
| ~~Đoạn Văn Đề Cập~~ | ~~passage_entity~~ | ❌ Đã xóa |

---

## Roadmap để đạt 100% tên Việt

1. **T-series 14% còn thiếu:** ETL từ CBETA Open Data (GitHub cbeta-org) → có tên Hán, transliterate Hán-Việt
2. **X-series:** Cần tổ chức VN đứng ra làm mục lục. Đề xuất liên hệ: Viện NCPH VN, NXB Phương Đông, Thư Viện Hoa Sen
3. **Trước mắt:** Không fake data, không show X-series, label rõ 86% là từ Nguyễn Minh Tiến

---

*Session bởi Claude Code · 2026-08-19*

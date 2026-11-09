# Gói Pilot PTDA: Thiền Đăng Thế Phổ (X86n1601)

## Tóm tắt

Đây là **gói pilot (ứng viên)** chứa:
- **34 nhân vật** (các tổ sư từ kinh Thiền Đăng Thế Phổ juan 001)
- **9 quan hệ truyền pháp** từ kinh
- **Dữ liệu gốc** từ CBETA X86n1601 (byte-exact)
- **XML kết quả** theo chuẩn PTDA (namespace: urn:ptda:research:lineage:1)
- **Các test** để kiểm chứng tính toàn vẹn

## Cấu trúc gói

```
PTDA-X86n1601-pilot-v0.1/
├── README-VI.md                    (Tệp này)
├── source/
│   └── X86n1601.source.xml         (Kinh gốc CBETA - không sửa đổi)
├── derived/
│   └── X86n1601.pilot.claims.xml   (Dữ liệu kết quả PTDA)
├── schema/
│   └── ptda-lineage-v1.xsd         (Lược đồ XSD)
├── manifests/
│   ├── source-manifest.json        (Thông tin nguồn)
│   └── run-manifest.json           (Dữ liệu tải về)
├── scripts/
│   ├── extract_pilot_final.py      (Script chính để trích)
│   └── validate_package.py         (Script kiểm chứng)
├── tests/
│   ├── test_extraction.py          (8 test toàn bộ)
│   └── test-results.txt            (Kết quả test)
├── reports/
│   ├── structure-report.md         (Phân tích cấu trúc XML)
│   ├── extraction-rules.md         (Luật trích dữ liệu)
│   ├── pilot-report.md             (Báo cáo chi tiết)
│   └── rights-report.md            (Quyền & giấy phép)
├── requirements.txt                (Thư viện Python)
└── SHA256SUMS.txt                  (Checksum bảo mật)
```

## Dữ liệu Chính

### Persons (34 tổ sư)

Trích từ "三十三祖世系圖" (Biểu đồ phả hệ 33 Tổ sư):

| # | Hệ | Tên (Hán) | Ghi chú |
|---|----|-----------|---------|
| 0 | 始祖 | 釋迦牟尼佛 | Đức Phật Thích Ca |
| 1 | 第一祖 | 摩訶迦葉 | Tổ sư Đại Ca Diếp |
| 2 | 二祖 | 阿難尊者 | Tổ sư A-nan |
| ... | ... | ... | ... |
| 33 | 三十三祖 | 菩提達摩 | Tổ sư Bồ-đề-đạt-ma |

### Relations (9 quan hệ truyền pháp)

```
釋迦牟尼佛 → 摩訶迦葉 → 阿難尊者 → ... → 菩提達摩
```

Tất cả 9 quan hệ đều có trạng thái `pending` (chờ duyệt).

## Cách Dùng

### 1. Kiểm Chứng Dữ Liệu
```bash
python3 -I validate_package.py X86n1601.pilot.claims.xml
```

### 2. Chạy Test
```bash
python3 -I test_extraction.py
```

### 3. Tái Trích Dữ Liệu
```bash
python3 -I extract_pilot_final.py
```

Kết quả tạo lại: `X86n1601.pilot.claims.xml`

## Thống Kê

| Mục | Số lượng | Ghi chú |
|-----|---------|--------|
| Juan xử lý | 1 | juan 001 (phả hệ tổ sư) |
| Nhân vật | 34 | Tất cả từ danh sách tổ sư |
| Quan hệ | 9 | Trích từ văn bản tiểu sử |
| Test | 8 | 8/8 pass ✓ |
| Lỗi | 0 | - |

## Giới Hạn

Gói này là **pilot (ứng viên) chỉ mẫu**:

1. ❌ **Juan 2–9**: Chưa xử lý (phạm vi giới hạn)
2. ❌ **Tên tiếng Việt**: Chưa có (chỉ tên Hán)
3. ❌ **DILA ID**: Chưa liên kết (chỉ CBETA)
4. ❌ **Số đời PTDA**: Chưa gán (giữ nguyên nhãn nguồn)
5. ⚠️ **Xác minh**: Mọi quan hệ cần duyệt manual bởi chuyên gia

## Khuyến Cáo Tiếp Theo

1. **Duyệt viên**: Kiểm tra 9 quan hệ so với kinh gốc
2. **Mở rộng** (nếu cần): Xử lý juan 2–9
3. **Liên kết DILA** (tùy chọn): Gắn ID người DILA
4. **Phiên âm** (tùy chọn): Dịch tên Hán sang Việt

## Giấy Phép

**Nguồn**: CBETA 佛典寶藏  
**Giấy phép**: CC BY-NC-SA 4.0  
**Derivative**: PTDA pilot (cùng giấy phép)

**Sử dụng**: Chỉ không lợi nhuận (nghiên cứu, giáo dục)

---

**Phiên bản**: PTDA-X86n1601-pilot-v0.1  
**Ngày**: 2026-10-20  
**Trạng thái**: Candidate (ứng viên, chờ QA)

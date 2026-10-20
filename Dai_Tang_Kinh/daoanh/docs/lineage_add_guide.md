# Hướng dẫn thêm tông phái / Khai Tổ mới

## Nguyên tắc cốt lõi

Hệ thống tính số đời 3 lớp:
- `gen_lamte`     : đời Lâm Tế (từ Lâm Tế Nghĩa Huyền = 1)
- `gen_thientong` : đời Thiền Tông (từ Ma Ha Ca Diếp = 1) = gen_lamte + 37
- `gen_sect`      : đời trong tông phái cụ thể (Khai Tổ = 1)

Nguồn dữ liệu:
- **TTL file** (slug ID) → thiền sư VN, có tên tiếng Việt, ghi tay
- **DILA graph** (A-prefix ID) → 19k thiền sư TQ/quốc tế từ học thuật MARCUS/DILA
- DILA/MARCUS **không phân biệt tông phái** → chỉ TTL mới có `dharmaLineageName`

---

## Cách tính generationOrder

`generationOrder` trong TTL = **gen_lamte** (đời Lâm Tế tính từ Lâm Tế Nghĩa Huyền = 1)

Các mốc quan trọng để tham chiếu:
| Thiền sư | gen_lamte | gen_thientong | Ghi chú |
|---|---|---|---|
| Lâm Tế Nghĩa Huyền | 1 | 38 | Khai Tổ Lâm Tế Tông |
| Nguyên Thiều Siêu Bạch | 70 | 107 | Khai Tổ Gia Phổ VN |
| Minh Hải Pháp Bảo | 71 | 108 | Khai Tổ Chúc Thánh VN |
| Liễu Quán Thiệt Duyệt | 72 | 109 | Khai Tổ Liễu Quán VN |
| Phật Ý Linh Nhạc | 72 | 109 | Khai Tổ Gia Phổ VN đời 3 |

---

## Workflow thêm tông phái mới (VN monk)

### Bước 1 — Tạo file TTL

File: `data/ttl/TS-[Ten-Viet-Ascii].ttl`

Template bắt buộc:
```turtle
<ex:monk/[slug_lowercase_underscore]> a <bkg:Monk> ;
    rdfs:label "[Tên tiếng Việt]"@vi ;
    bkg:dharmaLineageName "[Dòng Lâm Tế Tên VN Việt Nam]"@vi ;
    bkg:generationOrder [số gen_lamte] ;
    bkg:hasTeacher <ex:monk/[slug_thay]> ;
    bkg:isLineageFounder true .

<ex:monk/[slug_thay]> rdfs:label "[Tên thầy]"@vi .
```

**Quy tắc đặt tên tông phái** (`dharmaLineageName`):
- VN: `"Dòng Lâm Tế [Tên Khai Tổ] Việt Nam"@vi`
  - VD: `"Dòng Lâm Tế Liễu Quán Việt Nam"@vi`
- TQ: `"Tông [Tên] Trung Hoa"@vi`
  - VD: `"Tông Tào Động Trung Hoa"@vi`
- Nhật/Hàn: `"Tông [Tên] [Quốc gia]"@vi`

**Slug convention**: tên tiếng Việt không dấu, chữ thường, thay khoảng trắng bằng `_`
- `"Thiệt Duyệt Liễu Quán"` → `thiet_duyet_lieu_quan`

### Bước 2 — Chạy ETL

```powershell
cd daoanh/
python scripts/etl_gen_compute.py
```

ETL tự động:
1. Tìm `isLineageFounder true` trong TTL → đăng ký Khai Tổ
2. Tính gen_sect/gen_lamte/gen_thientong cho tất cả vị có `dharmaLineageName`
3. BFS graph → đệ tử chưa ghi tông sẽ kế thừa từ Khai Tổ gần nhất

---

## Workflow thêm tông phái DILA (A-prefix, không TTL)

Dùng khi Khai Tổ đã có sẵn trong DILA graph (tông TQ/Nhật/quốc tế).

Các Khai Tổ đã xác định DILA ID:
| Tông phái | Khai Tổ | DILA ID | gen_lamte | Hậu duệ DILA |
|---|---|---|---|---|
| Vân Môn Tông | Văn Yển (文偃) | A003703 | ~34 | 755 vị |
| Pháp Nhãn Tông | Văn Ích (文益) | A000174 | ~35 | 299 vị |
| Tào Động (Lương Giới) | Lương Giới (良价) | A009489 | ~35 | 26 đệ tử TT |
| Tào Động (Tào Sơn) | Tào Sơn Bổn Tịch | A009449 | ~36 | 43 vị |

Insert trực tiếp vào DB rồi chạy ETL:
```sql
INSERT INTO lineage_founders (lineage_name, lineage_key, khai_to_id, khai_to_name_vi, khai_to_gen)
VALUES ('Tông Vân Môn Trung Hoa', 'tong_van_mon_trung_hoa', 'A003703', 'Vân Môn Văn Yển', 34);
```

Sau đó chạy lại `python scripts/etl_gen_compute.py`.

---

## Ví dụ mẫu đã làm — Lâm Tế Liễu Quán VN

**Prompt admin dùng**: "thêm tree Lâm Tế Liễu Quán VN với Thiệt Duyệt Liễu Quán là Khai Tổ"

**Kết quả**:
- File: `data/ttl/TS-Lieu-Quan-Thiet-Duyet.ttl`
- `dharmaLineageName`: `"Dòng Lâm Tế Liễu Quán Việt Nam"@vi`
- `generationOrder`: `72` (gen_lamte 72 = Nguyên Thiều 70 + 2 đời)
- `isLineageFounder`: `true`
- gen_sect cho Khai Tổ = **1**, đệ tử trực tiếp = **2**, v.v.

---

## Prompt template cho session sau

Khi admin muốn thêm tông mới, chỉ cần nói:

> "Thêm tông [tên] với Khai Tổ là [tên thiền sư], thầy của họ là [tên thầy].
> Số đời Lâm Tế: [X] (hoặc: Khai Tổ là đệ tử đời [N] của [tên tổ đã biết])."

Nếu không biết số đời → cung cấp tên thầy, tôi tra trong DB/TTL để tính.

---

## Lưu ý quan trọng

1. **gen_lamte ≠ số đời ghi trên bia chùa VN** — Bia chùa Quốc Ân ghi "đời 33" nhưng đó là đếm theo bài kệ riêng của sub-lineage, không phải từ Lâm Tế Nghĩa Huyền = 1. Hệ thống dùng đếm tuyệt đối từ Lâm Tế Nghĩa Huyền.

2. **Đệ tử kế thừa tự động** — Nếu đệ tử trong TTL có cùng `dharmaLineageName`, họ tự được gán đúng tông phái. Nếu đệ tử chưa ghi `dharmaLineageName` nhưng kết nối qua graph → ETL propagation tự gán.

3. **DILA monks không có gen_sect** — Họ chỉ có gen_lamte + gen_thientong từ BFS. Muốn có gen_sect cần insert lineage_founders với DILA ID.

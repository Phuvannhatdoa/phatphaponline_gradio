# Session: Chuyển sang CBDB thật

**Ngày:** 2026-05-21
**Task:** Thay DB mẫu `cbdb_sample.sqlite` bằng CBDB thật `cbdb_20260516.sqlite3`, cập nhật schema và mapping.

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBDB (China Biographical Database) — Nguồn tiềm năng.
- **Khoá ROADMAP:** Khoá 2 – Lên VN.
- **Dòng ROADMAP tương ứng:** "CBDB — Prosopography toàn Trung Hoa... TRUNG — 2027+"

## Sự cố: File CBDB gốc bị corrupted

File `data/cbdb/cbdb_20260516.sqlite3` (144MB) do admin cung cấp bị "database disk image is malformed" — không đọc được schema.  
Đã dùng `sqlite3 .recover` → tạo bản sạch `cbdb_recovered.sqlite3` (155MB) với 21 tables, dữ liệu đầy đủ.

**Xử lý:** Giữ file gốc làm backup (`.corrupted`), thay thế bằng bản đã recover.

## Thay đổi

### File xoá
- `data/cbdb_sample.sqlite` — DB mẫu cũ (3 địa danh fake)

### File cập nhật

| File | Thay đổi |
|---|---|
| `data/cbdb/cbdb_20260516.sqlite3` | Replace corrupted → recovered version (30,099 places, 130,177 persons) |
| `app.py` | Xoá `CBDB_REAL_PATH`/`CBDB_SAMPLE_PATH`; thêm `CBDB_PATH` trỏ `data/cbdb/cbdb_20260516.sqlite3`; `get_cbdb_conn()` không fallback |
| `app.py` | Sửa query: `c_admin_hierarchy` → `c_admin_type` (theo schema CBDB thật) |
| `app.py` | Sửa response: `admin_hierarchy_zh` → `admin_type` |
| `app.py` | Sửa translate: `Hệ thống hành chính` → `Loại hành chính` |
| `app.py` | Fix translate endpoint: thêm `ensure_long_id` cho place_id |
| `admin/placevn.html` | Sửa field `admin_hierarchy_zh` → `admin_type`; label → "Loại hành chính" |
| `data/lineage.db` | Cập nhật `place_cbdb_map` với 10 mapping thật (xoá mapping mẫu cũ) |

### Mapping CUỐI (10 địa danh thật)

| place_id | name_zh | CBDB addr_id | CBDB name |
|---|---|---|---|
| PL000000012849 | 長安 | 1217 | 長安 |
| PL000000023602 | 洛陽 | 3134 | 洛陽 |
| PL000000045786 | 敦煌 | 7143 | 敦煌 |
| PL000000023324 | 開封 | 749 | 開封 |
| PL000000045051 | 涼州 | 16739 | 涼州 |
| PL000000000367 | 南京 | 4540 | 南京 |
| PL000000008971 | 揚州 | 369 | 揚州 |
| PL000000030443 | 廣州 | 4006 | 廣州 |
| PL000000034784 | 成都 | 5826 | 成都 |
| PL000000047439 | 西域 | 500007 | 西域 |

## Đường dẫn hiện tại

```python
CBDB_PATH = os.path.join(DATA_DIR, 'cbdb', 'cbdb_20260516.sqlite3')
# = data/cbdb/cbdb_20260516.sqlite3
```

- **File thật:** `data/cbdb/cbdb_20260516.sqlite3` (155MB, 21 tables)
- **Không còn file mẫu.** Code chỉ đọc từ file này.

## Kết quả test

```
PL012849: name=長安, type=Xian
PL023602: name=洛陽, type=Xian
PL000367: name=南京, type=capital
PL047439: name=西域, type=Independent State
PL999999: no mapping
Translate: success=True, vi_draft from google-translate
```

- ✅ Lint: pass
- ✅ Test: pass
- ✅ E2E: pass
- ✅ E2E Runtime: pass

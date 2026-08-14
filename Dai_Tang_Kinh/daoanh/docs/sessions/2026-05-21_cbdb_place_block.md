# Session: Tích hợp Nguồn CBDB vào Admin Địa Danh

**Ngày:** 2026-05-21
**Task:** Thêm block "Nguồn CBDB" vào `admin/placevn.html`, ngay dưới "Nguồn dẫn Đại Tạng Kinh".

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBDB (China Biographical Database) — Nguồn tiềm năng.
- **Khoá ROADMAP:** Khoá 2 – Lên VN (làm tiền đề cho task "Chuẩn hoá TTL theo format Đạo Ảnh").
- **Dòng ROADMAP tương ứng:**
  - Bảng Nguồn tiềm năng: "CBDB — Prosopography toàn Trung Hoa... bổ trợ; không cần gấp — TRUNG — 2027+"
  - Task tương lai: "Thời điểm: Sau khi hoàn thành các task Place (DILA → placevn.html, block 'Nguồn CBDB')."

## Thiết kế / Giải pháp

### Kiến trúc

```
lineage.db                          cbdb.sqlite (riêng, read‑only)
┌─────────────────┐                 ┌─────────────────┐
│ place_cbdb_map   │  cbdb_addr_id  │ ADDR_CODES       │
│ PL000000000003 ──┼───────────────►│ c_addr_id=101    │
│ PL000000000010 ──┼───────────────►│ c_addr_id=202    │
└─────────────────┘                 └─────────────────┘
           │
           ▼
    app.py routes:
    GET  /daoanh/api/admin/places/<place_id>/cbdb
    POST /daoanh/api/admin/places/<place_id>/cbdb_translate
           │
           ▼
    placevn.html: <section>Nguồn CBDB</section>
```

### Nguyên tắc

- **KHÔNG** import bulk CBDB vào `lineage.db`. `cbdb.sqlite` luôn là DB riêng, chỉ đọc.
- Mapping chỉ lưu `place_id ↔ cbdb_addr_id` trong `place_cbdb_map`.
- Khi chưa có file thật: code tự fallback từ `cbdb.sqlite` → `cbdb_sample.sqlite`.

### Đường dẫn CBDB

| DB | Đường dẫn | Mục đích |
|---|---|---|
| Thật | `data/cbdb.sqlite` | Admin sẽ cung cấp sau |
| Mẫu | `data/cbdb_sample.sqlite` | Demo/test (chứa 3 dòng mẫu: 長安, 波利城, 洛陽) |

Trong `app.py`:
```python
CBDB_REAL_PATH = os.path.join(DATA_DIR, 'cbdb.sqlite')
CBDB_SAMPLE_PATH = os.path.join(DATA_DIR, 'cbdb_sample.sqlite')

def get_cbdb_conn():
    path = CBDB_REAL_PATH if os.path.exists(CBDB_REAL_PATH) else CBDB_SAMPLE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
```

## Schema

### Bảng `place_cbdb_map` (trong `lineage.db`)

```sql
CREATE TABLE IF NOT EXISTS place_cbdb_map (
  place_id TEXT NOT NULL,
  cbdb_addr_id INTEGER NOT NULL,
  note TEXT,
  PRIMARY KEY (place_id, cbdb_addr_id)
);
CREATE INDEX IF NOT EXISTS idx_place_cbdb_map_cbdb ON place_cbdb_map(cbdb_addr_id);
```

### Bảng `ADDR_CODES` (trong `cbdb_sample.sqlite` / `cbdb.sqlite`)

```sql
CREATE TABLE ADDR_CODES (
    c_addr_id INTEGER PRIMARY KEY,
    c_name_chn TEXT,
    c_admin_hierarchy TEXT,
    c_notes TEXT,
    x_coord REAL,
    y_coord REAL
);
```

### Dữ liệu mẫu

| place_id | cbdb_addr_id | Ghi chú |
|---|---|---|
| PL000000000003 (勝境關) | 101 (長安) | Mapping mẫu |
| PL000000000010 (波利城) | 202 (波利城) | Mapping mẫu |

## File đã tạo/sửa

| File | Thay đổi |
|------|----------|
| `data/cbdb_sample.sqlite` | **Mới** — CBDB mẫu với 3 địa danh (長安/101, 波利城/202, 洛陽/301) |
| `data/lineage.db` | **Sửa** — Thêm bảng `place_cbdb_map` + 2 dòng mapping mẫu |
| `app.py` | **Sửa** — Thêm `CBDB_REAL_PATH`, `CBDB_SAMPLE_PATH`, `get_cbdb_conn()`, 2 routes `/cbdb` và `/cbdb_translate` |
| `admin/placevn.html` | **Sửa** — Thêm `cbdbData` state, `useEffect` fetch CBDB, block "Nguồn CBDB" với nút dịch + textarea |
| `docs/db_schema.md` | **Sửa** — Thêm mô tả `place_cbdb_map` |
| `docs/progress.md` | **Sửa** — Cập nhật trạng thái CBDB |
| `docs/sessions/2026-05-21_cbdb_place_block.md` | **Mới** — Session log này |

## API Endpoints

### `GET /daoanh/api/admin/places/<place_id>/cbdb`

**Input:** `place_id` = PL000000000003

**Output (có mapping):**
```json
{
  "has_cbdb": true,
  "cbdb_addr_id": 101,
  "name_zh": "長安",
  "admin_hierarchy_zh": "中國-京兆府-長安縣",
  "notes_zh": "唐代都城，今陝西西安。"
}
```

**Output (không mapping):**
```json
{ "has_cbdb": false }
```

### `POST /daoanh/api/admin/places/<place_id>/cbdb_translate`

**Input:** (body không cần, backend tự lấy CBDB data)

**Output:**
```json
{
  "success": true,
  "vi_draft": "Tên: Trường An...",
  "source": "CBDB",
  "meta": { "llm_provider": "google-translate" }
}
```

## Cách test

1. **API test với Python:**
   ```bash
   cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
   python3 -c "
   import app
   with app.app.test_client() as c:
       r = c.get('/daoanh/api/admin/places/PL000000000003/cbdb')
       print(r.get_json())
   "
   ```

2. **Frontend:** Mở `https://phatphaponline.org/daoanh/admin/` → chọn place "勝境關" (PL000000000003) → scroll xuống block "Nguồn CBDB" → click "Dịch thô (LLM)".

3. **Pipeline:**
   ```bash
   npm run pipeline
   ```

## Kết quả test

- ✅ API GET (có mapping): `has_cbdb: true`, trả đúng dữ liệu CBDB
- ✅ API GET (không mapping): `has_cbdb: false`
- ✅ API POST translate: `success: true`, vi_draft từ GoogleTranslate (Gemini rate-limited)
- ✅ Lint: pass
- ✅ Test: pass
- ✅ E2E: pass

## Ghi chú

- File `cbdb.sqlite` thật chưa tồn tại. Khi admin cung cấp, chỉ cần đặt vào `data/cbdb.sqlite`, code tự động dùng file thật.
- Nếu cần chuyển từ mẫu → thật: xoá `cbdb_sample.sqlite` hoặc để code tự ưu tiên `cbdb.sqlite` khi có.
- API translate hiện dùng GoogleTranslator (Gemini bị rate-limit). Khi Gemini hoạt động lại, sẽ tự động dùng Gemini.

# ĐẠO ẢNH – NOTES_INFRA

Mục tiêu: Ghi lại hạ tầng tối thiểu để bất kỳ phiên AI / dev nào cũng hiểu nhanh đường đi:
Browser → Nginx → Flask (app.py / server.py) → SQLite (lineage.db).

## 1. Đường dẫn gốc dự án

- Repo chính: /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
- Tuyệt đối KHÔNG dùng lại /opt/daoanh (đã legacy, do AI tạo sai).

## 2. Backend Flask

### 2.1. Admin + Đạo Ảnh UI

- Entry chính đang chạy: app.py
- Port: 5000
- Cách chạy (tối thiểu):

  ```bash
  cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
  python3 -B app.py
  ```

- API quan trọng:

  - GET /daoanh/api/admin/places_pending
  - GET /daoanh/api/admin/places_error
  - (các API admin/place khác… lấy từ app.py)

### 2.2. Auth Gateway (login)

- Entry: server.py
- Port: 5001
- Chức năng: xử lý login Gmail giả lập, route /daoanh/login.html, /daoanh/api/login/*.
- Admin frontend: /daoanh/admin/ (serve từ thư mục admin/).

## 3. Database SQLite

- File chính: /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db
- Được mô tả chi tiết trong: SCHEMA.md / master-schema.md
- Các bảng quan trọng:

  - RAW: people_full, places_dila, marcus_networks, dila_reference, marcus_reference
  - STAGING: places_pending, namevi_map_places, ttl_mapping, ttl_works, ttl_canon_works
  - FINAL: people, places, places_vps, canon_catalog, dataset_sources, networks, lexicon, places_search_fts*, lineage_conflicts_v2, person_refs, time_periods

- Quy tắc:
  - Không tạo thêm schema/bảng ngoài master-schema.md.
  - Không ALTER/DROP/INSERT/UPDATE trên bảng RAW.
  - Không dùng hậu tố _new / _copy / _backup cho bảng.

## 4. Nginx reverse proxy

- Nginx chạy trên port 80, proxy cho Flask port 5000.

  ```nginx
  location /daoanh/api/ {
      proxy_pass http://127.0.0.1:5000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
  }
  ```

- Kiểm tra nhanh:

  ```bash
  curl -v "http://127.0.0.1:5000/daoanh/api/admin/places_pending?limit=1&offset=0"
  curl -v "http://localhost/daoanh/api/admin/places_pending?limit=1&offset=0"
  ```

  Cả hai phải trả JSON {"success": true, ...}.

## 5. Quy trình “sơ cứu” khi UI Đạo Ảnh lỗi

1. Kiểm tra backend:

   ```bash
   ps aux | grep "python3 -B app.py"
   curl -v "http://127.0.0.1:5000/daoanh/api/admin/places_pending?limit=1&offset=0"
   ```

2. Nếu không có process hoặc curl lỗi:
   - Kill cũ: `pkill -f "python3 -B app.py"`
   - Khởi động lại:

     ```bash
     cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
     python3 -B app.py
     ```

3. Nếu 127.0.0.1:5000 OK mà browser vẫn lỗi:
   - Kiểm tra nginx:

     ```bash
     nginx -t && systemctl reload nginx
     curl -v "http://localhost/daoanh/api/admin/places_pending?limit=1&offset=0"
     ```

4. Nếu lỗi SQLite (no such table / unable to open database file):
   - Đảm bảo đang dùng đúng file DB ở data/lineage.db.
   - So sánh schema và master-schema.md / SCHEMA.md.
   - Tuyệt đối không sửa schema RAW trực tiếp nếu chưa cập nhật master-schema.md.

---

File này nên lưu ở:

`/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/NOTES_INFRA.md`

và commit lên repo, để sau này anh chỉ cần paste nội dung này (kèm master-schema.md) là bất kỳ phiên AI nào cũng hiểu hạ tầng và không “dắt” nhầm sang /opt/daoanh nữa.[page:1][web:49]
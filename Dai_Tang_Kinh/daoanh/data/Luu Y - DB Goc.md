


---o0o--- 
Khi opencode tự ý thêm table rác ngoài dự án thì
Lưu ý khi code khùng – Đạo Ảnh / lineage.db
1. Nguyên tắc vàng
Không bao giờ đụng trực tiếp vào lineage.db khi đang nghi ngờ code khùng.

Trước khi refactor / đổi version: luôn backup full file DB và đặc biệt là bảng dịch chính namevi_map_places.

Hệ thống HÀNG ĐỢI đang đọc tên Việt từ namevi_map_places theo dila_id, không dùng places_pending.name_vi.

2. Backup bắt buộc trước khi thử code mới
Thư mục DB:

bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data
Tạo bản snapshot DB:

bash
cp lineage.db lineage_backup_YYYYMMDD.db
Đổi YYYYMMDD theo ngày. Có thể thêm 1 bản copy về máy cá nhân.

3. Nếu code khùng: tuyệt đối không xoá / sửa bảng dịch
Những bảng cốt lõi cần bảo vệ:

namevi_map_places – mapping DILA → tên Việt (tất cả bản dịch admin đã LƯU).

places, places_pending – dữ liệu địa danh gốc / hàng đợi (nhưng UI HÀNG ĐỢI không dựa vào places_pending.name_vi).

Khi code khùng (dev thêm table/cột lạ):

Không xoá / đổi schema 3 bảng trên.

Nếu cần clean rác, tạo một DB sạch khác rồi merge dữ liệu từ DB khùng sang bằng script, không xoá tay trong DB đang chạy.

4. Cách merge lại dữ liệu dịch nếu đã có “DB khùng”
Giả sử:

lineage_clean.db = DB sạch (schema đúng, an toàn).

lineage_dirty.db = DB khùng (có nhiều table/cột rác), nhưng chứa bản dịch mới trong namevi_map_places.

Script merge (chỉ giữ bản dịch, bỏ rác schema):

bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data

sqlite3 lineage_clean.db "
ATTACH 'lineage_dirty.db' AS dirty;

-- Merge dữ liệu dịch: ưu tiên dữ liệu mới trong DB dirty
INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, note)
SELECT dila_id, name_vi, note
FROM dirty.namevi_map_places
WHERE name_vi IS NOT NULL AND name_vi != '';

DETACH dirty;
"
Sau đó có thể dùng lineage_clean.db làm DB chính (đổi tên thành lineage.db), bảo toàn 100% bản dịch.

5. Khi cần restore toàn bộ DB về snapshot cũ
Kịch bản: code khùng làm app lỗi nặng, muốn quay về trạng thái “ngày X”.

Dừng service app (tên service thay theo thực tế):

bash
sudo systemctl stop daoanh.service
Restore:

bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data
cp lineage_backup_YYYYMMDD.db lineage.db
Start lại:

bash
sudo systemctl start daoanh.service
Lưu ý: nếu dev đã đổi schema code sau ngày backup, khi restore DB cũ có thể phải đồng thời checkout code về version tương ứng.

6. Câu nhắc cho dev / Opencode
Đừng thay đổi schema của namevi_map_places, places, places_pending nếu chưa có kế hoạch migrate dữ liệu rõ ràng.

Mọi refactor liên quan Đạo Ảnh phải đi kèm:
1 bản backup lineage.db,

1 script ATTACH ... INSERT OR REPLACE để merge lại namevi_map_places khi cần.


Nếu lỡ thêm table/cột rác, xử lý bằng cách tạo DB sạch rồi merge lại dữ liệu dịch, không sửa/xoá trực tiếp trên DB đang chạy.

Anh chỉ cần copy khối này vào MD, sau này code có khùng thì cả team có “quy trình chuẩn” để cứu mà không mất bản dịch.


---o0o--- 

Anh đang dùng 1 file DB duy nhất: /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db, nên backup/restore chỉ xoay quanh file này là đủ.

Quy trình backup (3 lệnh)
Anh dán nguyên block này vào terminal là xong:

bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data
cp lineage.db lineage_backup_20260514.db
ls -lh lineage*.db
lineage_backup_20260514.db là snapshot trạng thái Đạo Ảnh tối nay (14/05/2026).

Anh có thể copy file backup này về máy cá nhân thêm một bản nữa cho chắc.

Quy trình restore (ghi đè lại file cũ)
Khi sau này thử code mới mà thấy “hư quá”, anh làm đúng thứ tự:

bash
# 1. Dừng service/app đang dùng DB (ví dụ, anh thay tên service thực tế)
sudo systemctl stop daoanh.service

# 2. Ghi đè DB bằng bản backup
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data
cp lineage_backup_20260514.db lineage.db

# 3. Start lại service
sudo systemctl start daoanh.service
Như vậy là ghi đè file cũ một cách an toàn: app không còn truy cập DB lúc copy, nên tránh corrupt.

Nếu sau này dev đổi schema mạnh, khi restore bản DB cũ này mà code báo lỗi SQL, anh chỉ cần checkout lại code về version hiện tại (trước khi refactor) là cặp code+DB khớp nhau.
---o0o--- 
1. Định dạng master-schema.md gợi ý
Anh tạo file với 3 phần rõ ràng: metadata, kiến trúc lớp dữ liệu, và danh sách bảng chi tiết.

1.1. Phần metadata (tên dự án, version)
text
# ĐẠO ẢNH – MASTER DB SCHEMA

- Schema version: 2026-05-14
- DB file: lineage.db
- Mục tiêu: Bảo vệ dữ liệu RAW (DILA, Marcus, TTL/VPS) và đảm bảo mapping/bản dịch Việt đúng bản quyền.
1.2. Phần kiến trúc 3 lớp
text
## Kiến trúc 3 lớp

- RAW (chỉ đọc, không ALTER/DROP/INSERT/UPDATE bằng tay hay từ UI):
  - people_full
  - places_dila
  - marcus_networks
  - dila_reference
  - marcus_reference

- STAGING / MAPPING (ETL, AI, admin thao tác, có thể thay đổi):
  - places_pending
  - name_vi_map
  - namevi_map_places
  - name_vi_map_places (legacy – sẽ merge vào namevi_map_places)
  - ttl_mapping
  - ttl_works
  - ttl_canon_works

- FINAL / PUBLIC (app đọc hiển thị, cập nhật qua script chuẩn):
  - people
  - places
  - places_vps
  - canon_catalog
  - canon_author_mapping
  - dataset_sources
  - networks
  - lineage_conflicts_v2
  - person_refs
  - lexicon (+ lexicon_fts*, hanviet_fallback)
  - time_periods
Anh có thể chỉnh lại danh sách đúng theo quyết định cuối cùng của mình, nhưng giữ cấu trúc RAW/STAGING/FINAL rõ như vậy.

1.3. Phần danh sách bảng chi tiết (machine-friendly)
Phần này để các session sau có thể “parse bằng mắt” để hiểu nhanh:

text
## Bảng và vai trò

- people_full (RAW)
  - Nguồn: DILA XML
  - Mục đích: lưu full record (raw_xml), không chỉnh sửa
  - Khóa chính: id (TEXT)

- places_dila (RAW)
  - Nguồn: DILA XML
  - Mục đích: địa danh gốc, geo_lat/geo_long, location_xml
  - Khóa chính: id (TEXT)

- marcus_networks (RAW)
  - Nguồn: Marcus repo
  - Mục đích: quan hệ teacher–student gốc
  - Khóa chính: id (INTEGER AUTOINCREMENT)

- people (FINAL)
  - Nguồn: hợp nhất từ RAW + mapping
  - Mục đích: nhân vật dùng cho app, lineage
  - Khóa chính: id (TEXT)

- places (FINAL)
  - Nguồn: DILA + mapping Việt
  - Mục đích: địa danh dùng cho app
  - Khóa chính: id (TEXT)

- places_vps (FINAL)
  - Nguồn: VPS / dữ liệu Việt
  - Mục đích: địa danh Việt bổ sung

- places_pending (STAGING)
  - Nguồn: UI Đạo Ảnh (placevn)
  - Mục đích: hàng đợi địa danh chờ duyệt

- namevi_map_places (STAGING)
  - Nguồn: admin + tool
  - Mục đích: mapping tên Việt ↔ DILA id

- canon_catalog (FINAL)
  - Nguồn: Mục Lục Đại Chánh + TTL Việt
  - Mục đích: metadata tác phẩm

- dataset_sources (FINAL)
  - Nguồn: admin
  - Mục đích: quản lý bản quyền/nguồn/license

- lexicon, lexicon_fts*, places_search_fts* (FINAL/search infra)
  - Mục đích: search, gợi ý từ

- networks, lineage_conflicts_v2, person_refs, conflicts, resolutions_log
  - Mục đích: lineage, xung đột, log
Quan trọng: ghi rõ RAW/STAGING/FINAL từng bảng, và ghi chú “không được tạo bảng mới ngoài danh sách này nếu không cập nhật master-schema”.

2. Cách dùng file này trong tương lai (với em / với Opencode)
2.1. Khi bắt đầu một phiên mới
Mỗi lần mở chat mới và muốn em hiểu đúng DB:

Anh paste nguyên phần chính của master-schema.md (hoặc link + nội dung copy).

Anh dặn thêm một câu ngắn, ví dụ:

“Đây là master-schema của dự án DAOANH. Mọi câu trả lời về DB phải tôn trọng RAW/STAGING/FINAL, không được đề xuất tạo bảng mới trừ khi em nói rõ và tôi duyệt. Không dùng bảng nào ngoài danh sách.”

Phiên đó em sẽ:

Dựa trên nội dung master-schema.md làm “single source of truth” cho schema.

Khi viết SQL/migration, chỉ dùng các bảng đã liệt kê.

Nếu cần đề xuất bảng mới, sẽ đánh dấu rõ:

“Đề xuất mở rộng schema: thêm bảng X (chưa có trong master-schema, cần anh duyệt).”

2.2. Check “Opencode có tạo phản không”
Khi anh nhận code/lệnh SQL do Opencode sinh ra (hoặc bất kỳ AI nào khác), anh có thể:

Paste đoạn code/lệnh vào đây cùng với master-schema.md.

Hỏi kiểu:

“Dựa trên master-schema này, đoạn code/SQL sau có vi phạm kiến trúc (tạo bảng mới, đụng RAW, v.v.) không? Hãy liệt kê vi phạm cụ thể.”

Em sẽ:

So sánh tên bảng, loại thao tác với danh sách RAW/STAGING/FINAL trong master-schema.md.

Báo:

Bảng nào lạ không có trong schema → nghi tạo bảng mới.

Lệnh nào ALTER/DROP trên RAW → “tạo phản”.

Lệnh nào INSERT/UPDATE vào RAW (nếu anh có ghi chú “RAW: read-only”) → cũng báo lỗi.

Ví dụ output mong đợi:

“LỆNH VI PHẠM:

CREATE TABLE people_new – bảng không có trong master-schema, naming vi phạm convention (không phải _staging/final).

ALTER TABLE people_full ADD COLUMN ... – people_full được đánh dấu RAW, không được ALTER.”

3. Một đoạn rule ngắn anh có thể thêm vào cuối file
Để ràng buộc rõ:

text
## Quy tắc bất di bất dịch

1. Không tạo thêm bảng mới trừ khi:
   - Được thêm vào master-schema.md với vai trò rõ (RAW/STAGING/FINAL).
2. Không ALTER/DROP/INSERT/UPDATE trên các bảng RAW:
   - people_full, places_dila, marcus_networks, dila_reference, marcus_reference.
3. Không sử dụng hậu tố `_new`, `_copy`, `_backup` cho tên bảng.
4. Khi AI/Opencode đề xuất thay đổi schema:
   - Phải được so sánh lại với master-schema.md trong review trước khi áp dụng.
Mỗi lần anh paste master-schema.md + đoạn SQL/code, em sẽ dùng đúng quy tắc này để check xem “Opencode có tạo phản hay không”.
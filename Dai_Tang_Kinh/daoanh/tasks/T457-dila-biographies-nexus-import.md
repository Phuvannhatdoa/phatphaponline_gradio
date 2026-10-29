---
id: T457
title: "Tích hợp BIO DILA (高僧傳): import nguồn nexus + lớp Việt chung (gộp T74b, T266)"
status: done
created: 2026-10-22
updated: 2026-10-29
owner: tich-hop
module: Data / Biographies
priority: high
parent: T453
merged_from: [T74b, T266]
plan_approved_at: "2026-10-22 (Admin phê chuẩn 3 đề xuất deepsearch: T457/T458/T459). Ghi DB/schema: duyệt riêng ở bước apply."
done_when: >
  (1) Snapshot repo DILA-edu/biographies (commit + SHA256) vào data/dila_import/biographies.<yyyy-mm>/; giấy phép ghi rõ
      (README repo; nếu không nêu → hỏi Admin trước khi import, theo LICENSE_FIREWALL).
  (2) Parse 2.976 file TEI: mỗi <linkGrp> → 1 dòng: book, file, anchor from/to, đoạn văn chữ Hán (ghép các dòng giữa anchor),
      person IDs, place IDs, time ptr "j<JD_from><JD_to>" → year_from/year_to (đổi JD đúng, Julian/Gregorian).
  (3) Bảng additive mới `dila_bio_nexus` (+ bảng nối người/nơi) — KHÔNG sửa `nexus_events` cũ (giữ nguyên 10.458 dòng).
  (4) Dry-run báo: số truyện/điểm theo sách (đủ Liang/Tang/Song/Ming/Buxu/Xinxu GSZ, 居士傳, 比丘尼傳, 名僧傳抄, 出三藏記集),
      % có năm, % person/place khớp people/places_dila.
  (5) Backup DB → --apply → ROLLBACK row; daoanh-qa ĐẠT; Admin xác nhận DONE.
  (6) Lớp Việt chung: khóa theo nexus id (và person id cho tiểu sử); cột translator, review_status, source_hash; không ghi đè text gốc.
  (7) Nạp bản Cloud (biQiuNi, Mingsengzhuanchao; Buxu_GSZ phần đủ) chỉ khi text_zh khớp hash với DB.
  (8) Tiểu sử người: giữ nguyên person_bio_vi_draft (2.093 dòng hiện có); bản dịch mới chỉ vào lớp Việt chung.
  (9) Dịch phần còn lại bằng Gemini theo quy trình T472; validator đạt; Admin duyệt từng đợt trước khi hiển thị.
  (10) Tên người hiển thị lấy từ people.name_vi (T455). T457 không tạo tên Việt cho người; bản dịch BIO không đặt tên riêng cho người.
revert: >
  python -X utf8 scripts/t457_dila_bio_nexus_import.py --revert (DROP bảng mới, mất 0 dữ liệu cũ).
---

## Mô tả
Import nguồn BIO DILA (nexus đã trích, có chữ Hán, ID người/nơi, năm JD) vào bảng bổ sung; xây lớp dịch tiếng Việt chung thay cho các task dịch rời rạc. Gộp T74b (Claude dịch tiểu sử người) và T266 (Gemini free bản nháp tiểu sử) vào đây. Không ghi vào bảng Authority, Place, Catalog hay person_bio_vi_draft.

## Quyết định (Admin duyệt 2026-10-26)
- T457 là import dữ liệu BIO (nguồn nexus + lớp Việt). Không ghi đè bảng Authority, Place, Catalog.
- Người: tên hiển thị = people.name_vi (T455). Đoạn sự kiện = lớp Việt của T457.
- Tiểu sử người: giữ person_bio_vi_draft (2.093 dòng); bản mới vào lớp Việt chung.
- T472 (dịch Gemini nexus) là bước dịch của T457, phụ thuộc T457.
- T74b, T266 đã gộp và chuyển vào Backup-Old/tasks-superseded/2026-10-26/.

### Trạng thái hiện tại
- T453 (A) và (B) đã được Admin duyệt, ghi trong `tasks/T453-dila-catalog-a-import-vi.md`: (A) apply 2026-10-22 05:54 (5.747 bộ); (B) duyệt 2026-10-22 06:01. Ghi chú Admin mới nhất trong T453 là 2026-10-25 18:33 ("giao Tester xem Done chưa") — đây là yêu cầu kiểm tra, CHƯA phải xác nhận DONE của Admin cho T453.
- Đã làm (T457): snapshot `data/dila_import/biographies.2024-01/` (commit 4e82453, SHA256SUMS.txt); `scripts/t457_extract_bio_nexus.py` (chỉ đọc) → `nexus_src/`: 21.740 nexus / 11 sách; 142 nexus bỏ qua do anchor lỗi trong nguồn DILA; giấy phép CC BY-NC-SA 4.0 (Admin xác nhận 2026-10-22).
- Chưa làm: `scripts/t457_dila_bio_nexus_import.py` (--dry-run/--apply/--revert); bảng DB `dila_bio_nexus` + bảng nối; dry-run report; backup/apply/ROLLBACK; QA. Lớp dịch Việt thuộc T458. Chưa ghi DB.

### Câu hỏi cần Admin quyết
- Q2a: bảng nối chỉ giữ person/place đầu tiên (như JSONL) hay parse lại `nexus_src/` để lấy ĐỦ? — chưa có đáp án.
- Q2b: duyệt schema 3 bảng (`dila_bio_nexus`, `dila_bio_nexus_person`, `dila_bio_nexus_place`) và row `data_sources` DILA_BIOGRAPHIES? — chưa có đáp án.
- Q2c: duyệt `--apply` sau khi dry-run? — chưa có đáp án.

# T457 — DILA biographies nexus (0 token)

## Hiện trạng (đo 2026-10-22)
- `nexus_events` 10.458 dòng (tạo bởi `scripts/t16_nexus_etl.py` từ `place_person_bibl`, không phải từ TEI DILA):
  **0/10.458 có `event_year`**; không có nội dung sự kiện; thiếu 補續/新續高僧傳, 居士傳, 名僧傳抄.
- Repo `DILA-edu/biographies`: 2.976 XML (20,6 MB). Mỗi truyện có `<linkGrp>`: `<link targets="#0712a24 #0712a26"/>`
  + `<ptr type="person|place|time">`. Ví dụ truyện 不空 (Song_GSZ/0746shiBuKong.xml): A000095 + A000774 + PL000000000083 + j19836981984080.

## Kết quả kỳ vọng
Dòng thời gian từng vị thầy: năm · nơi · cùng ai · đoạn văn gốc (chữ Hán) — lớp Việt do T458.

## Nhật ký 2026-10-22
- Snapshot `data/dila_import/biographies.2024-01/biographies-4e82453.tar.gz` (SHA256 trong SHA256SUMS.txt).
- `scripts/t457_extract_bio_nexus.py` (chỉ đọc, không ghi DB) → `nexus_src/<BOOK>.nexus.xml`: **21.740 nexus** / 11 sách;
  142 nexus bỏ qua do anchor lỗi trong nguồn DILA (vd. `0716a19/716a20`, `0329c17/A002529`) — danh sách khi chạy script.
  JD → năm: công thức chuẩn (Julian trước 1582-10-15). Vd. Bất Không j1983698–1984080 → 719–720.
- Giấy phép: văn bản CBETA CC BY-NC-SA 4.0; Admin xác nhận PTDA phi thương mại (2026-10-22). Còn: bảng DB + apply (chờ duyệt).

- 2026-10-22 (Admin cung cấp): trang chính thức http://buddhistinformatics.dila.edu.tw/biographies/ ghi dữ liệu TEI/XML
  "published under a CC (Attribution Share-Alike) License" ⇒ markup DILA = CC BY-SA; văn bản CBETA = CC BY-NC-SA 4.0
  ⇒ bản phái sinh theo điều kiện chặt hơn: **CC BY-NC-SA 4.0** (PTDA phi thương mại — Admin xác nhận). Bỏ trạng thái AUDITING.
  Gói 名僧傳抄 trên trang DILA (2018-12-06, 37 file, 188 linkGrp) trùng số lượng với bản GitHub commit 4e82453 (2024) → dùng bản GitHub (mới hơn).

### Nhật ký 2026-10-29 — ĐÃ IMPORT (A2, additive), Admin xác nhận DONE
- **Quyết định A2**: JSONL lưu **đầy đủ** `person_ids` / `place_ids` (array) thay vì 1 id đầu tiên — đổi `scripts/t457_staging_v4.py` (dùng `re.findall` thay `pers[0]`).
- **Dry-run** (`--dry-run`): 21.740 nexus / **11 sách** / 7.066 có năm (32,5%) / `duplicate_composite_key=0`.
  - Tang_GSZ 5.446 · Song_GSZ 5.242 · Buxu_GSZ 3.971 · Xinxu_GSZ 2.955 · Liang_GSZ 1.819 · biQiuNi 373 · chuSanZangJiJi 473 · Ming_GSZ 587 · Jushi_Zhuan 523 · Mingsengzhuanchao 188 · OtherSources 163
- **Apply** (3 bảng additive, KHÔNG đụng `nexus_events` cũ 10.458 dòng):
  - `dila_bio_nexus` = **21.740 dòng**
  - `dila_bio_nexus_person` = **36.049 link**
  - `dila_bio_nexus_place` = **13.930 link**
  - index: `idx_bn_book`, `idx_bn_person`, `idx_bn_year`, `idx_bn_place`
- **Backup trước apply**: `data/backups/lineage_t457_20261029_094901.db`.
- **Script**: `scripts/t457_dila_bio_nexus_import.py` (`--stats` / `--dry-run` / `--apply` / `--revert`), verify: `scripts/t457_verify.py`.
- **ROLLBACK**: dòng 2026-10-29 trong `docs/ROLLBACK.md` — `DROP TABLE` 3 bảng + 4 index (additive, 0 mất dữ liệu cũ).
- **Manifest**: `docs/manifests/T457-manifest.json` (SHA-256 11 file nguồn).
- **Bàn giao**: `docs/Handoff-2026-10-28-t457.md`.

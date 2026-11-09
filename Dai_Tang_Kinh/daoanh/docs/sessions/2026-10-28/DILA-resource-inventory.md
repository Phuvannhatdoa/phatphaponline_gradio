# Kiểm kê tài nguyên DILA: đã vào DB, chưa vào DB (2026-10-28, chỉ đọc)

Phương pháp: đối chiếu thư mục cục bộ `data/dila_import/` và sidecar `extracted/` (49.487 JSON) với `data/lineage.db` (mode=ro), cộng tìm kiếm web các repo `DILA-edu` và trang authority.dila.edu.tw.

## 1. Đã nạp đầy đủ vào DB

| Nguồn DILA | Local | DB | Ghi chú |
|---|---|---|---|
| Person authority: tên Hán | 49.487 | `people` 49.490 | khớp |
| Person: triều đại (`dynasty`) | 47.383 | `people.dynasty` 47.383 | khớp |
| Person: tiểu sử Hán (`concise_bio`) | 48.994 | `people.bio` 48.997 | khớp |
| Place authority | 59.375 | `places_dila` 59.167 + `dila_place_authority` 206 = 59.373 | còn 2 dòng chưa giải thích |
| Catalog authority (5.747 bộ) | 5.747 | `dila_catalog_works` 5.747 | đã có tiêu đề Việt (nháp, 0 đã duyệt) |
| Time authority (2012) | có | `time_periods` 117.429, `era_year_jdn` 986 | T473 còn đang dở |

## 2. Có trong sidecar nhưng CHƯA có trong DB

| Dữ liệu | Số lượng | Trạng thái DB |
|---|---|---|
| Quê quán (`places_of_origin`) | 12.188 người | 0 liên kết (`vn_person_places` 46) |
| Nơi hoạt động (`active_at_places`) | 1.227 người | 0 liên kết |
| Tác phẩm trong Đại Tạng (`works_in_tripitaka`) | 10.299 mục, 3.035 người | `vn_person_works` chỉ 10 dòng |
| Wikidata QID cấp người (`wikidata_qid`) | 2.005 người | chỉ có `geo_cross_ref` 190 dòng, không gắn người |
| Ngày sinh/mất chuẩn (`birth_death_dates`) | 9.848 người | chưa đối chiếu với `people.birth_year` (17.732 có giá trị) |
| Trích dẫn CBETA (`cbeta_citations`) | 53.929 mục, 25.915 người | `cbeta_person_mentions` 72.628 dòng, 10.173 người; chưa xác minh trùng |

Sidecar này được tạo theo T366 với ghi chú "không đưa vào DB" (triều đại, tác phẩm, CBETA, địa danh, Wikidata, ngày tháng). Các trường trên là phần chưa được nạp.

## 3. Biographies (TEI 高僧傳)

- Local: 2.976 file TEI, 21.740 nexus (T457) hoặc 21.882 (T458, đếm khác).
- DB `nexus_events`: 10.458 dòng, **0 dòng có năm**, không có nội dung sự kiện.
- Thiếu 4 bộ: 補續高僧傳, 新續高僧傳, 居士傳, 名僧傳抄.
- Ước lượng dịch: 1,13 triệu chữ Hán trong đoạn nexus.
- Trạng thái: T457 (nạp) và T458 (Cloud dịch) chưa hoàn tất.

## 4. Các repo DILA-edu khác (web, chưa đo)

| Repo | Trạng thái |
|---|---|
| cbeta-metadata | Một phần: `canon_catalog` 3.122 dòng; chưa có bảng gốc đầy đủ |
| CBETA-txt / cbeta-normal-text | Toàn văn: `text_passages` 9.316 đoạn, phần lớn chưa nạp |
| BK-EVAL | Bộ câu hỏi đánh giá LLM, chưa nạp |
| DHDMaterial | Thần chú (xlsx), chưa nạp |
| bza-xml | Biệt dịch Tạp A-hàm, chưa nạp |
| lod | RDF linked data, không cần nạp |

Không có bản local cho các repo này, nên chưa đo được số dòng.

## 5. Kết luận

- Cấu trúc cốt lõi (người, địa danh, catalog, thời gian) đã nạp.
- Chênh lệch dữ liệu chủ yếu nằm ở **liên kết** (quê quán, tác phẩm, Wikidata, nơi hoạt động) chứ không phải thực thể. Nhóm này nạp được **không cần dịch**.
- Lớp Việt còn thiếu: tiểu sử (12/49.490), nexus (0/10.458 có nội dung), tiêu đề đã duyệt (0/5.747).

## 6. Đề xuất

1. Nạp các liên kết chưa có (quê quán 12.188, tác phẩm 10.299, Wikidata 2.005) — không tốn token dịch. Cần backup và dry-run trước.
2. Hoàn tất T457 để có năm từ JD và 4 bộ còn thiếu.
3. Chỉ sau đó mới đưa T458 vào Cloud dịch.
4. Xác minh 2 dòng place và chênh lệch ngày sinh/mất.

# Deepsearch nguồn cần dịch tiếp sau T453 (2026-10-22, chỉ đọc)

Đã có: DILA Person (48K tên), Place (57K tên), authority_catalog 26 file (5.747 bộ, T453).
Khảo sát: GitHub org `DILA-edu` (19 repo) + repo Phật học khác. Số đo bằng GitHub API + DB `mode=ro`.

## DILA-edu — repo còn lại

| Repo | Nội dung | Cần dịch? | Đánh giá |
|---|---|---|---|
| **biographies** | TEI/XML 高僧傳: 2.976 file, 20,6 MB — Liang/Tang/Song/Ming/Buxu/Xinxu GSZ, 居士傳, 比丘尼傳, 名僧傳抄, 出三藏記集. Mỗi truyện có **nexus `<linkGrp>`**: đoạn văn (anchor dòng) + person ID + place ID + **time (JD)** | **CÓ** — đoạn văn nexus | **Ưu tiên 1** |
| cbeta-metadata | catalog/部類, creators, work-info, orig-category, alternates, gaiji | Không (trùng T453; bảng bộ loại đã có) | Có thể dùng `alternates` nối bản trùng — không dịch |
| Authority-Databases | person/place/time/catalog | Đã xong (time hoãn T452) | — |
| BK-EVAL | bộ câu hỏi đánh giá LLM kinh điển | Có thể (để test dịch) | Thấp |
| DHDMaterial | thông tin kinh chú (mantra) xlsx | Có thể | Thấp |
| bza-xml | Biệt dịch Tạp A-hàm XML | Không ưu tiên | Thấp |
| cbeta-normal-text / CBETA-txt | toàn văn CBETA | Dịch toàn văn = rất lớn | Ngoài phạm vi |
| lod | RDF Linked Data | Không | — |

## Ưu tiên 1 — DILA biographies (nexus events)
- DB hiện có `nexus_events` 10.458 dòng (Liang/Tang/Song/Ming GSZ, 比丘尼傳, 出三藏記集) nhưng:
  - **0/10.458 có năm** (`event_year` NULL toàn bộ) — trong XML có `<ptr type="time" target="#j<JD_from><JD_to>">` ⇒ lấy được năm **không cần dịch**;
  - **không có nội dung sự kiện** (chỉ `event_label` = tên người) ⇒ đoạn văn nexus cần **dịch Việt** (Cloud);
  - **thiếu** 補續高僧傳 (474 truyện), 新續高僧傳 (792), 居士傳 (130), 名僧傳抄 (37).
- Kết quả: dòng thời gian từng vị thầy — "năm 719, Bất Không gặp Kim Cương Trí tại Lạc Dương" — nối person/place/time ID sẵn có.
- Khối lượng dịch ước tính: ~15–20K đoạn nexus × ~60–100 chữ Hán ⇒ ~1–2 triệu chữ (gấp vài lần catalog).

## Ngoài DILA
| Nguồn | Nội dung | Giấy phép | Cần dịch? |
|---|---|---|---|
| **suttacentral/sc-data** `relationship/parallels.json` (1,5 MB) | Đối chiếu kinh Hán (T…) ↔ Pāli/Sanskrit/Tạng | CC0 | **Không** — nối T453 với Nikāya; SuttaCentral có bản Việt (HT Thích Minh Châu) |
| mbingenheimer/ChineseBuddhism_SNA | mạng xã hội Phật giáo TQ | (xem repo) | Không — DB đã có `marcus_networks` 11.169 |
| suttacentral/bilara-data | toàn văn + bản dịch | CC0/khác | Không (đã có bản Việt) |

## Đề xuất
1. **T457** — Import DILA biographies nexus (năm từ JD + 4 sách còn thiếu) — **không tốn token**.
2. **T458** — Cloud dịch đoạn văn nexus → `nexus_events` lớp Việt (prompt kiểu T453, pilot trước).
3. **T459** — SuttaCentral parallels: nối kinh Hán T453 ↔ kinh Pāli + link bản Việt — **không tốn token**.

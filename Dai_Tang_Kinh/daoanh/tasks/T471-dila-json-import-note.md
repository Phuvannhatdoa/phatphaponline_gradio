---
id: T471
title: Ghi chú nhập liệu T470 Phase 2 vòng bổ sung — 817 ID mới + field còn thiếu
status: in_progress
created: 2026-10-26
updated: 2026-10-26
done_when: |
  - Admin điền tay name_zh/name_vi cho 817 dila_id mới tạo, theo danh sách
    `docs/sessions/2026-10-26/t471_names_pending_admin.csv`.
  - Admin quyết định có mở resolver tên->ID an toàn cho
    places_of_origin/works_in_tripitaka/cbeta_citations/active_at_places hay
    không (hiện đang DỪNG, chưa ghi).
  - Admin xác nhận DONE mới được đổi status.
---

## Mô tả

Ghi chú tiếp nối T470 Phase 2 vòng bổ sung (2026-10-26): liệt kê rõ các
trường đã nhập vào DB, 817 dòng `people` mới tạo còn thiếu tên (name_zh/
name_vi) cần Admin tự điền tay trong Dashboard, và các trường bị DỪNG lại vì
cần resolver tên→ID (vi phạm nguyên tắc "không merge theo tên" nếu tự làm).
Không tự đổi status DONE — chỉ Admin xác nhận mới được đổi.

## Đã nhập (vòng bổ sung 2026-10-26)

| Field | DB đích | Số dòng UPDATE (người đã có) | Số dòng ghi khi INSERT (817 người mới) |
|---|---|---|---|
| `dynasty` | `people.dynasty` | 0 (toàn bộ 659 trường hợp DB_THIEU đều thuộc 817 ID mới, ghi ngay lúc INSERT) | 659/817 (158 người JSON không có dynasty) |
| `concise_bio` | `people.bio` | 0 (toàn bộ 817 trường hợp DB_THIEU đều thuộc 817 ID mới) | 817/817 |
| `birth_death_dates` | `people.birth_year`/`death_year` | 153 ô (người đã có sẵn, JSON có năm mà DB đang NULL) | 36 ID mới (phần còn lại trong 817 không có năm sinh/mất trong JSON) |
| `xml_sha256` | `codex_person_name.xml_sha256` (INSERT dòng mới vì `codex_person_name` chưa có dòng cho các ID này, PK `dila_id`) | 0 (không có dòng nào có sẵn mà cột trống) | 152 dòng mới |

Tổng: **817 dòng `people` mới** + **153 ô birth/death_year UPDATE cho người đã có** +
**152 dòng `codex_person_name` mới**.

Backup DB trước khi ghi: `data/lineage.db.bak_T470round2_20261026_140704`
(xem `docs/ROLLBACK.md`, mục 2026-10-26 "T470 Phase 2 vòng bổ sung").

## Còn thiếu — cần Admin tự điền tay

817 dòng `people` mới tạo **chưa có tên** (`name_zh`/`name_vi` đều NULL —
không tự suy tên từ Hán bio bằng LLM, đúng rule naming-and-identity.md).
Danh sách dila_id + trích đoạn `concise_bio` (gợi ý để Admin đọc, KHÔNG phải
tên đã suy) tại:

`docs/sessions/2026-10-26/t471_names_pending_admin.csv`

## Field bị DỪNG — chưa ghi, cần Admin quyết

4 field sau JSON chỉ lưu **tên dạng chuỗi (string)**, không có ID chuẩn nào để
join trực tiếp vào bảng quan hệ hiện có — ghi sẽ phải merge-by-name, vi phạm
nguyên tắc "Canonical internal ID = join key duy nhất (không dùng tên)" và
"Không merge record chỉ bằng matching tên" (data-integrity.md /
naming-and-identity.md):

| Field | Bảng đích cần ID | Vì sao dừng |
|---|---|---|
| `places_of_origin` | `person_origin_link.place_id` (dùng `places_dila.id`, 14 ký tự) | JSON chỉ có tên địa danh Hán (ví dụ `"梁溪"`), không có `places_dila.id` kèm theo |
| `works_in_tripitaka` | `dila_catalog_contributors.person_id` + `dila_catalog_works.cbeta_id` | JSON chỉ có tiêu đề + chú thích tự do, không có `cbeta_id` |
| `cbeta_citations` | `cbeta_person_mentions` | Định dạng JSON (`"( CBETA X35n0652_p0254a05 ) <tên>"`) khác hoàn toàn schema DB (`cbeta_text_sigla` + `person_name_zh`); không có cột passage locator tương ứng |
| `active_at_places` | `nexus_events.place_dila_id` | Giống `places_of_origin` — JSON chỉ có tên, không có ID |

`wikidata_qid`: không có bảng person-wikidata nào trong DB — chỉ báo số liệu
(2.005 ID có `wikidata_qid` trong JSON), **không ghi** theo yêu cầu trong đề
bài T470 vòng bổ sung.

`canon_catalog`: không đụng tới (đúng ràng buộc).

## Đối chiếu v3 (sau khi ghi vòng bổ sung)

CSV: `docs/sessions/2026-10-26/dila_json_reconcile_after_v3.csv`
Log: `docs/sessions/2026-10-26/dila_json_reconcile_after_v3.log`

`DB_THIEU` đã về 0 cho: `dynasty`, `concise_bio`, `birth_death_dates`,
`xml_sha256`. Các field còn `DB_THIEU` > 0 (`places_of_origin`,
`works_in_tripitaka`, `cbeta_citations`, `active_at_places`, `wikidata_qid`)
là do bị DỪNG như trên, không phải lỗi ghi.

---
id: T206
title: Sửa mojibake Ð (U+00D0) trong 302 file TTL — L4 = 0
status: done
created: 2026-10-01
commit: 88847b8
revert: python -X utf8 scripts/t206_fix_mojibake.py --revert data/backups/t206_mojibake_20261001_222517
---

# T206 — Sửa mojibake `Ð` (U+00D0) → `Đ` (U+0110)

## Lỗi

Chữ Đ tiếng Việt là **U+0110** (LATIN CAPITAL LETTER D WITH STROKE). 302 file TTL
bị ghi bằng **U+00D0** (LATIN CAPITAL LETTER **ETH**) — ký tự không tồn tại trong
tiếng Việt, chỉ dùng cho tiếng Iceland. Kết quả hiển thị sai trong UI:

- `Ðại sư` → đúng là `Đại sư`
- `Cư Sĩ Ðề Hình Quách Tường Chánh` → đúng là `Cư Sĩ Đề Hình Quách Tường Chánh`
- `Thiền sư Ðam Nguyên Ứng Chân` → đúng là `Thiền sư Đàm Nguyên Ứng Chân`

**Quy mô: 302 file / 590 ký tự** (preflight T204 mã L4). Phân bố: 164 file có 1
ký tự, 70 file 2, 32 file 3, còn lại từ 4 đến 10 (`TS-Phan-Duong-Thien-Chieu.ttl`
nhiều nhất, 10).

## Vì sao sửa hàng loạt an toàn — đã kiểm chứng trên corpus thật

| Vị trí | Số occurrence `Ð` | Kết luận |
|--------|--------------------|----------|
| URI `<...>` | **0** | không đụng định danh ontology |
| `@prefix` | **0** | không đụng namespace |
| slug `ex:monk/...` | **0** | không đụng identity/khoá |
| `rdfs:label@"zh"` | **0** | không đụng Hán tự |

Chỉ nằm trong text tiếng Việt: `rdfs:label@"vi"` và `bkg:biographicalNote`.

- Token nhiều ký tự duy nhất: `Ðoan` ×38 (= **Đoàn**) và `Ðam` ×1 (= **Đàm**,
  Pháp danh "Đàm Nguyên Ứng Chân") — cả hai đều là tiếng Việt, không phải từ
  Iceland.
- Corpus đã có sẵn **11.087** chữ `Đ` (U+0110) đúng ⇒ `Ð` chắc chắn là biến thể sai.

## Script

`scripts/t206_fix_mojibake.py` — `--stats` / `--dry-run` / `--apply` / `--verify`
/ `--revert <backup_dir>`.

**Tự phòng vệ**: nếu phát hiện `Ð` ở vị trí cấu trúc (URI / `@prefix` / slug /
`@zh`) thì **từ chối ghi toàn bộ lô** và báo lại, không âm thầm sửa. Sau khi ghi
phải parse được thì mới giữ, không thì rollback ngay file đó.

## Kết quả

- **L4: 302 → 0.**
- Corpus: **1.038/1.038 file parse OK** (không hồi quy so với T205).
- Backup: `data/backups/t206_mojibake_20261001_222517`.

### Kiểm chứng mạnh nhất — đối chiếu theo vị trí ký tự

So từng ký tự bản gốc với bản sau sửa, trên cả 302 file:

```
302/302 file: mỗi khác biệt đều đúng là Ð(U+00D0) → Đ(U+0110)
tổng vị trí đổi = 590 (đúng bằng 590 ký tự lỗi)
file có đổi sai: KHÔNG CÓ
```

Không có vị trí nào khác bị đụng tới — kể cả ký tự `Đ` đã đúng sẵn.

> **Lưu ý phương pháp:** phép thử đảo ngược đầu tiên (`Đ`→`Ð` rồi so sánh) cho
> kết quả sai 18/302 vì nó cũng thay luôn các `Đ` đúng sẵn có. Đó là lỗi của phép
> thử, không phải của bản sửa — đã thay bằng so khớp theo vị trí ở trên.

## Test

`tests/test_t203_ttl_guard.py`: **24/24 PASS** (thêm 7 assert cho T206: L4 = 0,
mã U+00D0/U+0110 đúng, 5 guard vị trí cấu trúc, thay thế không đụng Hán tự, corpus
parse 1038/1038).

`npm run pipeline`: PASS về test/lint/e2e/UAT/compliance/guard. Vẫn còn 2 điểm
**có sẵn từ trước T206**, không liên quan:
- `claims_assertion_level 0%` và `conflicts_resolved 0%` (metric governance).
- `EPERM unlink test-results/.last-run.json` (file-lock Windows).

## Phát hiện thêm: DB cũng bị mojibake — CHƯA sửa (cần Admin duyệt)

Khảo sát read-only cho thấy `Ð` (U+00D0) tồn tại trong **22 cột/bảng của DB**,
tức lỗi này **không chỉ ở TTL** mà đã lan sang dữ liệu:

| Bảng | Cột | Số row |
|------|-----|--------|
| `lexicon` | `term` / `normalized` / `key_norm` | 162 |
| `lexicon` | `definition` | 328 |
| `lexicon_fts` | `term` | 162 |
| `lexicon_fts` | `definition` | 328 |
| `name_vi_map` | `bio_snippet` | 66 |
| `entity_monks` | `name` | 24 |
| `entity_temples` | `name` | 23 |
| `entity_temples` | `definition` | 14 |
| `entity_monks` | `definition` | 7 |
| `vn_person_authority` | `name_vi` / `biographical_note_vi` | 4 |
| `vn_person_relations` | `target_label_vi` | 3 |
| `name_vi_map` | `name_vi` / `name_vi_final` | 3 |
| `person_bio_vi_draft` | `bio_vi_draft` | 3 |
| `translation_exemplar` | `zh` / `vi` | 2 |
| `entity_works` | `definition` | 2 |
| `keyword_map` | `value` | 4 |
| `keyword_map` | `keyword` | 1 |

**Chưa sửa** — theo đúng tiền lệ T203, sửa DB cần Admin duyệt trước (kèm backup +
`--revert`). Đề xuất task T207 khi Admin đồng ý. Lưu ý `translation_exemplar.zh`
cần soi kỹ vì cột ngữ ngữ `zh` có thể chứa Hán tự.

## Còn lại (ETL vẫn bị chặn)

- **L1 = 17, L2 = 15** (32 blocking): nhãn sai — Admin tự cập nhật theo
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md`.
- **L5 = 25** nhóm `dila_id` trùng trong DB (cảnh báo).
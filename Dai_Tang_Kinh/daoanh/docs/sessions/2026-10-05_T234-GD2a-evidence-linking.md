# 2026-10-05 — T234 GĐ2a: nối evidence + dọn 11 dòng sai (H1 về 0)

| Mục | Nội dung |
|---|---|
| Ngày | 2026-10-05 |
| Task | T234 GĐ2a |
| HEAD trước | `d7fba6a` |
| DB | `data/lineage.db` (gitignored) |
| Kết quả | **H1: 1.426 → 0 ✅** |

## Việc đã làm

| # | Hạng mục | Số | Bằng chứng |
|---|---|---:|---|
| M1 | Nối `event_evidence` = `ev:<event_type>:<dila_id>` cho mọi event còn thiếu | 1.437 | `event_evidence` 3.530 → 4.967 |
| M1b | 4 claim wikidata có cấu trúc (`Q…·P576`) | 4 | `exact_span=NULL` — **không bịa**, `evidence_type='structured_claim'` |
| M2 | 11 dòng sai rõ → `era_mention` + `year=NULL` | 11 | `confidence='era_rename_or_renovation'` |
| — | Sửa bug `--strict` của audit gate | 1 | report=0, strict=1 |

Script: `scripts/t234_gd2a_apply.py` (`--dry-run` / `--apply` / `--revert` / `--only-m1m2`).

## Kiểm chứng revert (round-trip, DB thật không bị đụng)

```
revert trên bản sao  → event_evidence=3530  founding=2262  era_mention=1385
backup 155321        → event_evidence=3530  founding=2262  era_manifest=1385   ✅ khớp 100%
```

Manifest: `data/t234_gd2a_log.json` (1.437 evidence + 11 event có giá trị gốc).
Backup: `data/backups/lineage_t234gd2a_20261005_155321.db`.

## Sai lầm tự làm — đừng lặp lại

1. **Sai chính tả đường dẫn** `truyenthua` → `truyenhua`. Lệnh `write` abort, nhưng PowerShell **đã tạo cây thư mục rỗng ở `phatphaponline_gradio/`**. Trong đó có file `t225_fix_t65_t66_board.py` của phiên 10/3 **khác hash** với bản trong repo. Đã backup bản lệch rồi xoá cả cây.
   → **Bài học:** mỗi lần `write`/`bash` kiểm tra lại tên `truyenthua` có đúng không.
2. **Heuristic revert sai.** Tưởng "evidence mới = key có `ev:founding:` tương ứng" ⇒ khớp 4.963/4.967, khiến revert xoá **sạch** bảng `event_evidence`. Chỉ phát hiện vì **luôn kiểm thử revert trên bản sao** trước khi tin.
   → **Bài học:** định nghĩa "thay đổi của tôi" bằng **diff với backup trước**, không bằng suy luận từ cấu trúc dữ liệu.
3. **Log bị ghi đè.** Mỗi lần `--apply` idempotent đều ghi đè `t234_gd2a_log.json` ⇒ mất giá trị gốc của 11 dòng M2. Phải dựng lại manifest từ backup.
   → **Bài học:** script idempotent phải **merge** log, không overwrite.
4. `edit` tool không khớp chuỗi có `→` (ký tự thật vs `\u2192`) ⇒ 3 lần patch hỏng. Vá bằng cách **tìm dòng động** thay vì offset cứng.

## Gate hiện tại

```
H1 ✅ 0        H2 ❌ 192 (thật 96)     H3 ❌ 1712 (check quá rộng)
H4 ✅ 0        H5 ✅ 0                H6 ❌ 1508 (cần sửa H6)      H7 ✅ 0
```

## Còn lại — GĐ2b/c

- **M3: 32 dòng (không phải 23)** — dry-run ra 18 đổi + 14 không tra được, **nhiều hơn phê duyệt** ⇒ chờ Admin duyệt từng dòng.
- M4: `exact_span` cho 54 dòng.
- M5: `time_authority_id` 96 row → `time_periods.id` thật (bản nháp cũ dựng ID `era:<zh>` giả ⇒ **đã bỏ, chưa dùng**).
- M6: view 1.508 dòng rác **+ sửa H6 để query view**, nếu không gate vẫn FAIL.
- H3: phải làm evidence-aware (Wikidata/P571 hợp lệ không có năm trong DILA note). **Không xoá hàng loạt theo H3.**
- GĐ3 (T97) tách riêng vì `app.py` còn WIP.

## Việc khác trong phiên

- Xoá cây thư mục sai `phatphaponline_gradio/truyenhua/` (backup file lệch ở `%TEMP%\opencode\stray_t225_fix_t65_t66_board.py`).
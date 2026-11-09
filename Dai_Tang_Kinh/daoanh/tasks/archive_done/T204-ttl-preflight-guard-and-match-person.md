---
id: T204
title: "Cổng chặn TTL: preflight chặn ETL nạp lỗi nhãn + siết match_person (dila_id đụng 41→7)"
module: Code / ETL Guard
priority: critical
status: done
owner: claudecode
depends_on: [T203, T200]
created: 2026-10-01
updated: 2026-10-01
designed_by: claudecode
commit_pass1: "<sha_T204_pass1>"
commit_pass2: "<sha_T204_pass2>"
revert: "git revert --no-edit <sha_T204_pass1> <sha_T204_pass2>"
plan_approved_at: "2026-10-01 Admin: 'tôi muốn bạn update DB trước … bảo đảm sau này TTL update cũng sẽ trùng với phát hiện lỗi và chỉnh trước'"
done_when: |
  scripts/t204_ttl_preflight.py phát hiện L1/L2/L3/L4/L5;
  etl_ttl_full_import.py + etl_ttl_person_authority.py DỪNG (exit 1) trước khi nạp/xoá bảng;
  --skip-preflight để bypass khi biết chắc báo sai;
  match_person ưu tiên Hán trước tail-N, tail ≥3 từ;
  dila_id nhận >1 slug non-alias giảm 41 → 7;
  tests/test_t203_ttl_guard.py 16/16 PASS + wire vào npm run test:translation;
  ETL person_authority bị chặn TRƯỚC khi DELETE bảng (DB còn nguyên 1506 row).
---

# T204 — Cổng chặn TTL + siết `match_person`

## 1. Vấn đề

T203 phát hiện 32 file TTL `rdfs:label` sai. Nếu chỉ báo cáo thì lần cập nhật TTL sau
**sẽ tái phát đúng lỗi đó**. Ba chỗ khiến lỗi lọt vào DB:

| # | Chỗ | Hành vi cũ |
|---|-----|-----------|
| 1 | `etl_ttl_full_import.py` `phase1_upsert_persons` | `if fname in existing_fn: continue` ⇒ file đã có thì **skip**, không validate |
| 2 | `etl_ttl_person_authority.py` vòng parse | `try/except` nuốt lỗi ⇒ **9 file rdflib hỏng bị bỏ qua im lặng**, vị đó chưa từng vào DB |
| 3 | `match_person()` | thử **tail-N (từ 2) TRƯỚC** Hán ⇒ tên lõi phổ biến (`Pháp Diễn`) khớp nhầm ⇒ **41 `dila_id` nhận >1 slug** |

## 2. Đã làm

### 2.1 `scripts/t204_ttl_preflight.py` (mới)

| Mã | Kiểm tra | Mức |
|----|-----------|------|
| **L1** | `rdfs:label` trùng tên **một người KHÁC** mà file khai báo ⇒ nhãn đảo | **CHẶN** |
| **L2** | nhãn **không liên quan** tới nhãn chuẩn trong corpus | **CHẶN** |
| **L3** | rdflib **không parse được** ⇒ ETL sẽ bỏ qua im lặng | **CHẶN** |
| **L4** | chứa `Ð` (U+00D0) thay `Đ` (U+0110) | cảnh báo |
| **L5** | >1 slug **non-alias** cùng `dila_id` trong DB | cảnh báo |

Exit code: `0` sạch · `1` có L1/L2/L3 (**chặn**) · `2` chỉ L4/L5.
Nhãn chuẩn lấy từ triple `<ex:monk/SLUG> rdfs:label` ⇒ **không suy đoán**.
Dùng **chung** `classify()` với `t203_quarantine_ttl` ⇒ một nguồn sự thật, không lệch.

### 2.2 Nối cổng chặn vào ETL

- `etl_ttl_full_import.py`: gate ở đầu `run()`, `--skip-preflight` để bypass
- `etl_ttl_person_authority.py`: gate **trước `DELETE FROM vn_person_*`** — script này xoá sạch
  rồi nạp lại nên lỗi TTL sẽ mất hẳn dữ liệu cũ. Kiểm **cả** `data/ttl` lẫn `data/ttl/old`.

### 2.3 `match_person()` — đổi thứ tự ưu tiên

```
CŨ:  exact → tail2..tail5 → zh
MỚI: exact → zh      → tail3..tailN (dài→ngắn)
```

Hán phân biệt tốt hơn tên lõi tiếng Việt. Đo trên `data/ttl` + DB thật:

| | `dila_id` nhận >1 slug non-alias |
|---|---|
| CŨ | **41** |
| MỚI | **7** |

⇒ **giải 36 nhóm**. 2 nhóm mới phát sinh đều do file có nhãn sai (T203 sẽ sửa).

## 3. Verify

- `tests/test_t203_ttl_guard.py` **16/16 PASS** + wire vào `npm run test:translation`
- `etl_ttl_full_import.py --dry-run` ⇒ **DỪNG** với 42 lỗi chặn (17 L1 + 15 L2 + 10 L3)
- `etl_ttl_person_authority.py` ⇒ **DỪNG trước khi xoá bảng**; verify `vn_person_authority`
  còn nguyên **1.506 row**, `vn_person_relations` còn **2.096 row**
- `npm run audit:t204` chạy độc lập, **chưa** thêm vào `pipeline`

## 4. Sau khi Admin sửa 32 file TTL

```powershell
python -X utf8 scripts/t204_ttl_preflight.py --report   # L1/L2 phải = 0
python -X utf8 scripts/t203_sync_vnpa_name.py --stats   # phải = 0 dòng cần sửa
python -X utf8 scripts/etl_ttl_full_import.py --dry-run # phải qua cổng
```

Khi đó mới thêm `audit:t204` vào `pipeline` để chặn hồi quy.
**Còn lại:** 10 L3 (file hỏng) + 302 L4 (mojibake) + 7 L5 (dila_id đụng) — task riêng.
---
id: T252
title: "132 dòng H3 còn lại — quyết policy chứng minh năm (tách từ T251)"
module: Data Integrity / Timeline / Evidence
priority: high
status: done
created: 2026-10-06
updated: 2026-10-08
owner: mimo-flash
depends_on: [T22, T234, T251]
designed_by: mimo-flash
plan_approved_at: ""
done_when: >
  Admin chọn hướng xử lý cho từng nhóm; mỗi nhóm xử lý xong thì
  `scripts/audit_data_honesty.py` chạy lại và H3 giảm đúng bằng số
  dòng nhóm đó, không có dòng nào bị "chấp nhận im lặng" khi thiếu
  bằng chứng. Khi H3 = 0 thì T234 mới đạt done_when.
blocked_reason: "Chờ Admin quyết policy — 4 hướng đang để mở, không được tự ý nới lỏng acceptance."
revert: "docs-only cho tới khi Admin duyệt hướng; khi sửa label/note thì backup DB theo quy trình T234 + manifest."
former_ids: []
outcome: >
  W1+W3+W4 đã đưa H3 132→0 (Admin duyệt build W1/W3/W4, yêu cầu logs+commit+docs+revert): W1 code-only yểm 6 midpoint, W3 thêm 19 niên hiệu phụ (additive), W4 sửa 14 dòng (6 label-range, 3 source_ref dynasty, 5 năm hiển sai). audit_data_honesty.py --strict PASS 7/7; npm run pipeline XANH 2026-10-08. Revert W4 đã TEST: FAIL 14 → áp lại → PASS 7/7.
---

# T252 — 132 dòng H3 còn lại

## 1. Vì sao tách riêng

T251 chỉ khỏa lấp **lỗ hổng LD2** (6 niên hiệu vắng) và đưa H3 từ 143 → 132.
Admin quyết định: *"Tách task riêng, tôi sẽ quyết sau"* — task này ôm 132
dòng còn lại, **chưa chọn hướng nào**, chỉ liệt kê đủ bằng chứng để quyết.

> ⚠️ **Không được tự ý nới lỏng `h3()`.** Giả định ban đầu
> "thêm era là xong" đã bị kiểm chứng sai (xem T251 §2). Nới acceptance
> mà thiếu bằng chứng đúng là lỗi gốc sinh ra T234.

## 2. Cơ cấu 132 dòng (đo trên DB thật, 2026-10-06, sau T251)

| # | nhóm | số dòng | triệu chứng |
|---|---|---|---|
| A | `note·regex` — note có era nhưng dạng **"X中"**, không có số năm | **106** | `嘉慶`×38, `洪武`×13, `大中`×8, `康熙`×7, `至大`×6, `成化`×6, `永樂`×6, `乾道`×5, `至正`×5, `治平`×5, `大中祥符`×5, `天祐`×4 … year đã được ETL gán một giá trị cụ thể nhưng note không chứng minh được giá trị đó |
| B | `era_name` — label kiểu `元和十四年` | **14** | **ĐÃ Bác BỎ — không phải lỗi dữ liệu** (§2.1): 13/15 dòng khớp chính xác với khoảng niên hiệu trong DB, 0 dòng sai; 2 dòng thiếu key `天監`/`咸淳` |
| C | `dynasty` — chỉ nêu triều đại | **4** | vd `始建於唐朝，稱聚瑟寺` — không có mốc năm nào |
| D | midpoint `明末清初` / `元末明初` không hiện khoảng | **6** | `延壽`, `萬緣庵`, `大梵寺`, `金帶寺`, `天城寺`, `息心所` |
| E | `民國` — label hỏng | **1** | `上虛下雲老和尚舍利塔 民民國` (lặp chữ 民) |
| F | era **đã có** trong DB nhưng note không có số năm | **1** | `白衲庵 晉咸和` — note dài 151 ký tự, không chứa `<era><số>年` |
| | **tổng** | **132** | audit: `khong suy ra (129) + ngoai khoang (3)` |

Nhóm A chiếm 80% và là nhóm cần quyết policy.

## 2.1 Đo lại 2026-10-06 — bằng chứng đầy đủ

Chi tiết + lệnh tái hiện: **`docs/reports/T252-h3-132-evidence-20261006.md`**.

**15 dòng `era_name` (không phải 14) — đo bằng `era_map` của chính DB:**

```
13 KHOP  ·  0 KHONG KHOP  ·  2 THIEU key (天監, 咸淳)
```

> ❌ **Claim cũ ở dòng B ("唐元和 chỉ 3 năm (110–113)") đã bị kiểm chứng SAI.**
> `era_唐_元和 = 806..820` ⇒ `元和十四年 = 806+14-1 = 819` **khớp đúng** `year=819`.

**Trạng `time_periods`:** 117.651 dòng · `era` 1.005 nhưng chỉ **190 dòng dùng được**
(`id LIKE 'era_%'` + đủ `start_year`) → **186 tên**; 815 dòng còn lại là rác
(`period_name_zh` = chuỗi số, `start_year NULL`, `load_era_map` tự loại).

**Mô phỏng W1 (script độc lập, KHÔNG sửa `audit_data_honesty.py`):**

| biến thể | H3 | giảm |
|---|---|---|
| hiện tại | **132** | — |
| W1a: `元` vào `NUMCH` + đọc thêm `label_zh` | 117 | −15 |
| W1a **strict** (`suy ra == year`) | **119** | −13 |
| W1b: `<era>中/間` khi `year` nằm trong khoảng era | **47** | −72 |
| W1c: `era（YYYY-YYYY）` khi `year` nằm trong khoảng | **45** | −2 |

**W1a KHÔNG strict sẽ nhận sai 2 dòng** (`PL000000012410` suy ra 1064 thay vì 893;
`PL000000012466` suy ra 1008 thay vì 677 — note chứa niên hiệu **của sự kiện khác**,
và `h3()` hiện không so `suy ra` với `year`). ⇒ W1a **bắt buộc** kèm `== year`.

**45 dòng còn lại:** 6 midpoint thiếu nhãn · 4 `dynasty` · 2 mâu thuẫn thật
(`洪武三十二年`→1399 vs lưu 1372; `周天復十一年`→911 vs lưu 902) · 33 thiếu niên hiệu.

**20 niên hiệu thiếu hoàn toàn (0 dòng trong `time_periods`):**
`天監`(9 dòng) · `長安`(4) · `永明` `普通` `乾寧` `大通` `義熙` `儀鳳` `景福`(2 mỗi tên) ·
`景龍` `永泰` `昇明` `承聖` `神龍` `永昌` `建元` `大順` `咸淳` `保大` `赤烏`(1) —
**+ 2 tên có row nhưng `period_name ≠ 'era'`**: `民國`(`dyn_民國` 1912..1949), `祥符`.

## 3. Các hướng — nay đã có số đo (chưa chọn)

| hướng | làm gì | đo được | rủi ro / điều kiện |
|---|---|---|---|
| **W1 — Sửa logic audit (không sửa dữ liệu)** · W1a `元` + đọc `label_zh` **kèm `suy ra == year`** · W1b `<era>中/間` khi `year` ∈ khoảng era · W1c `era（YYYY-YYYY）` khi `year` ∈ khoảng | code-only, 3 nhánh con | **132 → 45** | **Đổi acceptance ⇒ Admin duyệt.** W1b/W1c vẫn bắt `year` nằm trong khoảng (không nhận bừa); W1a **bắt buộc** strict, nếu không nhận sai 2 dòng (§2.1). Đây là *nới có chủ đích*: với `X中` chỉ chứng minh được "nằm trong khoảng era", không chứng minh được đúng năm |
| **W1′ — Ghi nhãn khoảng vào `label_zh`** (hướng cũ của W1) | sửa dữ liệu 106 dòng + phải cho audit đọc nhãn | chưa đo; khả năng ~72 dòng | Sửa hàng loạt; vẫn cần W1c (code) để audit đọc nhãn |
| **W2 — Nới H3** (chấp nhận era+"中" bất chấp năm) | — | — | **Không đề xuất** — đúng lỗi gốc sinh ra T234; chỉ Admin chủ động |
| **W3 — Truy nguồn / bổ sung niên hiệu** | thêm 20 tên thiếu + sửa `period_name` 2 tên (`民國`, `祥符`) | ≈30 trong 45 dòng | **Không được đoán khoảng năm.** Nguồn: Wikidata (dự án đã dùng Q claim), authority 藏經, hoặc chính note (một số đã ghi `era（YYYY-YYYY）`). Tái dùng mẫu T251: backup + manifest + `--revert` đã test |
| **W4 — Sửa dữ liệu mâu thuẫn** | 6 midpoint hiện khoảng · 4 `dynasty` hiện khoảng · 2 dòng mâu thuẫn (`洪武三十二年`, `周天復十一年`) · label `民民國` | 13 dòng | cần nguồn chứng minh trước khi ghi; backup DB + manifest |

**Thứ tự đề xuất (chưa duyệt):** W1 (code) → W3 (bổ niên hiệu) → W4 (sửa 13 dòng)
→ **H3 = 0**. Nhóm B (15 dòng `era_name`) **không cần W3/W4** — đã khớp 13/15,
chỉ cần W1a để audit chịu đọc `label_zh`.

## 4. Việc liên quan khác (không thuộc task này, cần quyết riêng)

- **H6 đang báo OK quá dễ**: chỉ kiểm era/dynasty được tham chiếu.
  Bảng rộng còn **815 era tên là chuỗi số** (`'351'`, `'457'`…) và
  **570 emperor thiếu `start_year`** chưa được H6 bao phủ.
- **`time_periods` rác**: `lunar_month` 115.921 dòng, 0 tham chiếu;
  `emperor` 570 dòng/0 `start_year`. Admin đã quyết **điều tra, không xoá**.
- **`npm run dup:ids` FAIL sẵn 3 ID trùng** (T188, T237, T238) — chặn
  pipeline chung, không thuộc ai trong T234/T251/T252.
- ~~**`.git/index.lock` 0 byte còn sót từ 2026-10-05 20:58**~~ — **đã xoá**
  2026-10-06 khi Admin duyệt trực tiếp trong phiên T251.

## 5. Khi nào task này done

Chỉ khi `python -X utf8 scripts/audit_data_honesty.py` cho **H3 = 0**
và mỗi dòng được chấp nhận đều trỏ được tới bằng chứng trong
`note`/`label`/Wikidata. Lúc đó T234 mới đạt `done_when` và được
chuyển audit sang strict (exit 1 chặn pipeline).

---
id: T34
title: Tam Tạng Integration — 84000 / VRI / Kanripo (thật, không placeholder)
module: Đại Tạng / Tam Tạng Kinh Điển
priority: high
status: done
depends_on: [T24, T33]
created: 2026-08-24
updated: 2026-09-06
done_when: >
  Ba truyền thống Hán / Pali / Tây Tạng hiển thị đúng, đầy đủ, chính xác học thuật trên HOME;
  không còn fake/placeholder data trong DB; ETL scripts thật cho ít nhất 1 trong 3 nguồn
---

## ⚠️ TRẠNG THÁI HIỆN TẠI — CẢNH BÁO DATA GIẢ

Một session code song song đã tạo schema tables + API routes cho 84000/VRI/Kanripo trong DB và app.py,
nhưng **toàn bộ data trong DB là fake/placeholder — không được đưa lên HOME**.

Chi tiết audit đầy đủ: [`docs/sessions/2026-08-24_tam_tang_integration_audit.md`](../docs/sessions/2026-08-24_tam_tang_integration_audit.md)

---

## Tổng Quan — Tam Tạng Trong PTDA

| Truyền thống | Ngôn ngữ | Repo | Bảng trong DB | Trạng thái |
|---|---|---|---|---|
| Bắc Truyền / Hán Tạng | Hán cổ | CBETA + Kanripo | `cbeta_catalog_vn`, `kanripo_catalog` | CBETA ✅; Kanripo ⚠️ fake |
| Nam Truyền / Pali Tạng | Pali | VRI / SuttaCentral | `vri_tipitaka_catalog`, `vri_place_mapping` | ⚠️ data giả, lỗi học thuật |
| Tạng Truyền / Tây Tạng | Tạng ngữ | 84000 | `eight_four_thousand`, `eight_four_thousand_place_map` | ⚠️ data sai hoàn toàn |

---

## Giai Đoạn A — Xóa Data Fake (KHẨN CẤP)

**Lý do:** Data hiện tại chứa lỗi học thuật nghiêm trọng, không thể để trong DB:

### 84000 — Lỗi nghiêm trọng
- `toh=44` gán cho Heart Sutra → SAI (Toh 44 = Vimalakīrtinirdeśa; Heart Sutra = Toh 21)
- Platform Sutra (六祖壇經) gán vào `canon_section='Kangyur'` → SAI hoàn toàn (Thiền Tông TQ ≠ Kangyur Tây Tạng)
- `eight_four_thousand_place_map`: cả 3 rows đều map Tây Tạng texts → Thiếu Lâm Tự → vô nghĩa

### VRI — Lỗi nghiêm trọng
- `vri_place_mapping` (42 rows): toàn bộ Pali suttas map → Thiếu Lâm Tự → học thuật không thể chấp nhận
  (Pali Theravāda ra đời trước khi Phật giáo đến Trung Hoa, Thiếu Lâm Tự không có trong bất kỳ text Pali nào)
- `vri_cached_texts`: placeholder text `'IDAM BUDDHAṂ... (Pali excerpt)'`, không phải Pali thật
- `vri_tipitaka_catalog`: title `'Tin1'` không phải Hán tự, rõ là AI-generated

**Script xóa cần admin chấp thuận:**
```python
# scripts/t34_clear_fake_data.py
import sqlite3
conn = sqlite3.connect('data/lineage.db')
# Giai đoạn A: xóa fake rows, giữ nguyên schema
conn.execute("DELETE FROM eight_four_thousand")           # 3 rows fake
conn.execute("DELETE FROM eight_four_thousand_place_map") # 3 rows vô nghĩa
conn.execute("DELETE FROM vri_tipitaka_catalog")          # 3 rows GIẢ
conn.execute("DELETE FROM vri_place_mapping")             # 42 rows lỗi học thuật
conn.execute("DELETE FROM vri_cached_texts")              # 31 rows placeholder
conn.commit()
```

### Kanripo — Seed data nhưng text IDs thật
- 3 rows kanripo_catalog có text IDs thật (KR6s0102, KR6a0001, KR6e0162) nhưng là seed demo
- `kanripo_place_mapping`: mapping KR6a0001 → PL000000000001 (placeholder) → cần xóa/fix
- KHÔNG xóa kanripo_catalog — text IDs là valid seed, sẽ dùng làm template ETL

---

## Giai Đoạn B — Kanripo ETL Thật (Ngắn hạn)

**Vai trò đúng:** Kanripo bổ sung cho CBETA Hán Tạng (cùng truyền thống), cung cấp variant readings/critical editions.

**ETL plan:**
1. Fetch GitHub API: `https://api.github.com/orgs/kanripo/repos` → danh sách text repos
2. Mỗi repo → extract metadata (title_zh, category, cbeta_ref nếu có từ README/manifest)
3. Cross-reference: `kanripo.cbeta_ref` → `cbeta_catalog_vn.sigla` → route đến DILA place
4. Script: `scripts/etl_kanripo_catalog.py`

**Không cần**: map Kanripo text → places trực tiếp. Path đúng: Kanripo → CBETA T# → DILA place.

---

## Giai Đoạn C — Pali Tạng / SuttaCentral (Trung hạn)

**Quyết định nguồn:** Dùng **SuttaCentral** thay VRI/Tipitaka.org vì:
- SuttaCentral có public API: `suttacentral.net/api/suttaplex/<uid>?lang=vi`
- Có bản dịch tiếng Việt (Thích Minh Châu, CC BY-NC-SA 4.0) — VRI không có
- Cùng dữ liệu Pali nhưng dễ tích hợp hơn nhiều

**Scope mapping đúng:**
- Chỉ map Pali texts → địa danh Ấn Độ cổ đại trong DILA (Rājagṛha, Vāiśālī, Sāvatthī, Bodh Gayā...)
- KHÔNG map vào địa danh Trung Hoa (Thiếu Lâm Tự v.v.)
- Rename tables: `vri_*` → `pali_*` nếu chuyển sang SuttaCentral (cần migration script)

**Ví dụ mapping đúng:**
- SN 56.11 (Bài pháp đầu tiên) → 鹿野苑 Sarnath/Isipatana
- DN 16 (Mahāparinibbāna) → 拘尸那羅 Kushinagar
- MN 36 (Thành đạo) → 菩提伽耶 Bodh Gayā

**Script:** `python scripts/t37_seed_pali_place_ref.py`  
**Task đầy đủ:** `tasks/T37-pali-place-ref.md`

---

## Giai Đoạn D — 84000 Tây Tạng (Dài hạn) → **CHI TIẾT: T38**

**Approach: curate tay ~10 cặp kinh confirmed + ~10 cần verify**

**Script:** `python scripts/t38_seed_toh_crossref.py`  
**Task đầy đủ:** `tasks/T38-toh-cbeta-crossref.md`

**Lưu ý:** Toh 44 = Vimalakīrti (T0475), KHÔNG phải Avatamsaka T0278. Toh 127 ≈ Lotus T0262 (verify).

**Cách B — Glossary lookup:**
- 84000 có glossary Sanskrit/Tibetan/English: `read.84000.co/api/glossary-terms`
- Khi user click vào thuật ngữ khó trong UI → lookup 84000 glossary
- Hiển thị trong tab "Giáo Lý"

**KHÔNG làm:** map 84000 texts → places_dila (địa danh Hán truyền). Địa danh trong Tibetan canon là địa danh Ấn Độ cổ, không phải Trung Hoa.

---

## Kiến Trúc HOME Page — "Tam Tạng Kinh Điển"

```
HOME PAGE section: "Đại Tạng Kinh — Ba Truyền Thống"
├── 🟡 Hán Tạng (Bắc Truyền) ✅ Đang hoạt động
│   ├── CBETA: 3,122 kinh, 118,295 địa danh có tên Việt (ZQ)
│   └── Kanripo: variant readings (cần ETL thật — Giai đoạn B)
│
├── 🔵 Pali Tạng (Nam Truyền) — Cần triển khai (Giai đoạn C)
│   └── SuttaCentral: Nikaya texts (DN/MN/SN/AN/KN)
│       → chỉ liên kết địa danh Ấn Độ (Rajgir, Vaishali, Sarnath...)
│
└── 🟠 Tạng Truyền (Tây Tạng) — Cần triển khai (Giai đoạn D)
    └── 84000: Toh cross-ref với CBETA + Glossary
        → KHÔNG map vào places Hán truyền
```

---

## Routes Đã Có Trong app.py

Ba routes đã implement bởi session khác (lines 10328-10488):
- `GET /daoanh/api/places/<id>/eight_four_thousand` — hoạt động kỹ thuật, cần data thật
- `GET /daoanh/api/places/<id>/vri` — hoạt động kỹ thuật, cần fix scope + data thật
- `GET /daoanh/api/places/<id>/kanripo` — hoạt động kỹ thuật, cần ETL thật

**Không cần sửa backend routes** — chúng query đúng bảng, trả JSON đúng format. Chỉ cần data thật trong bảng.

---

## Acceptance Criteria

- [x] **Giai đoạn A**: Xóa toàn bộ fake data (8 tables) — đã xóa từ session trước, tất cả rỗng
- [x] **Giai đoạn B**: `kanripo_catalog` có ≥20 rows thật từ GitHub API — **101 rows** (2026-09-06)
- [ ] **Giai đoạn B**: `kanripo_catalog.cbeta_ref` cross-ref với `cbeta_catalog_vn.sigla` cho ≥5 texts — chỉ có 2 confirmed (KR6a0001=T1, KR6s0102=L143n1608); cbeta_catalog_vn.sigla chưa có dữ liệu
- [ ] **Giai đoạn C**: Quyết định VRI vs SuttaCentral được admin confirm
- [ ] **Giai đoạn C**: Chỉ map Pali texts → địa danh Ấn Độ cổ đại trong DILA (không phải chùa TQ)
- [ ] **Giai đoạn D**: `toh_cbeta_crossref` table có ≥10 rows với Toh đúng học thuật
- [ ] HOME page hiển thị "Ba Truyền Thống" section không có placeholder/empty data
- [ ] Tất cả data được badge nguồn rõ ràng (CBETA/84000/SuttaCentral/Kanripo)

## Blockers

- ~~Giai đoạn A cần admin chấp thuận xóa data~~ ✅ Done
- cbeta_catalog_vn.sigla = NULL (chưa import T-numbers) → cbeta_ref cross-ref chưa thể verify qua DB
- Giai đoạn C cần admin quyết định: VRI vs SuttaCentral
- Giai đoạn D cần access 84000 API hoặc GitHub dataset
- Kanripo KR6 subcategory PREFIX_MAP cần review thủ công — KR6d0001 thực tế là 妙法蓮華經 (Lotus Sutra), không phải 中論

## Ghi chú ETL 2026-09-06

- `scripts/etl_kanripo_catalog.py` đã chạy: 101 rows vào kanripo_catalog (98 new + 2 updated)
- GitHub Search API dùng query `KR6+in:name+org:kanripo` — tìm được 4173 repos tổng
- Title_zh lấy từ description format `"title-dynasty-"` — đúng
- KNOWN_CBETA_REFS: chỉ giữ 4 Āgama (KR6a0001-0004) + 1 bibliography — loại bỏ cross-refs chưa verify
- Kanripo KR6x subcategory ≠ CBETA canon divisions — cần verify thủ công từng prefix

## Ghi chú

Fake data được tạo bởi session code khác — không phải lỗi của task này.  
Xem audit đầy đủ: `docs/sessions/2026-08-24_tam_tang_integration_audit.md`

## LOG 2026-09-10 (Lee xac nhan DONE on dashboard)
- Fake data deleted: commit `76d9914` (delete fake data, Phase A complete, admin approved).
- DB verified 2026-09-10: eight_four_thousand=0, vri_tipitaka_catalog=0, kanripo_catalog=101 (real ETL etl_kanripo_catalog.py).
- Cleanup DB item on ADMIN_REVIEW_DASHBOARD = DONE.

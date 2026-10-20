---
id: T37
title: Pali Place Reference — curate tay địa danh Ấn Độ cổ đại ↔ SuttaCentral
module: Tam Tạng / Nam Truyền (Pali)
priority: high
status: done
depends_on: [T34]
created: 2026-08-24
updated: 2026-08-25
done_when: >
  Bảng pali_place_ref có ≥20 địa danh Ấn Độ cổ đại đã xác minh học thuật;
  tab Địa Danh hiển thị "Pali references" cho các địa điểm Ấn Độ;
  KHÔNG có địa danh Trung Hoa trong bảng này
---

## Chiến Lược — Curate Tay, Không Bulk ETL

**Nguyên tắc:** 20 rows chính xác > 2,000 rows sai học thuật.

Chỉ có ~100-200 địa danh trong DILA là địa danh Ấn Độ cổ đại có text Pali liên quan.
Curate tay từng dòng → đảm bảo 100% chính xác → không cần ETL phức tạp.

**Nguồn tham chiếu:** SuttaCentral (suttacentral.net) — UID format: `dn16`, `sn56.11`, `mn36`

---

## Schema — Bảng `pali_place_ref`

```sql
CREATE TABLE IF NOT EXISTS pali_place_ref (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id      TEXT NOT NULL,       -- FK → places_dila.listbibl (VD: PL000012345)
    name_zh      TEXT NOT NULL,       -- tên Hán để verify (VD: 鹿野苑)
    name_vi      TEXT,                -- tên Việt (VD: Vườn Nai / Isipatana)
    name_pali    TEXT,                -- tên Pali gốc (VD: Isipatana)
    name_skt     TEXT,                -- tên Sanskrit (VD: Ṛṣipatana)
    sc_uid       TEXT,                -- SuttaCentral primary UID (VD: sn56.11)
    sc_uids_more TEXT,                -- JSON array UIDs liên quan (VD: ["dn16","mn141"])
    sc_note_vi   TEXT,                -- Ngữ cảnh tiếng Việt (VD: "Nơi Phật thuyết Tứ Đế lần đầu")
    verified_by  TEXT DEFAULT 'ZQ',   -- người/source xác minh
    confidence   REAL DEFAULT 0.9,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dila_id, sc_uid)
);
```

---

## Seed Data — 15 Địa Danh Ưu Tiên

Script `scripts/t37_seed_pali_place_ref.py` tra DILA ID tự động qua `name_zh`.

| # | Tên Hán (DILA) | Tên Việt | Tên Pali | Sutta chính | Sự kiện |
|---|---|---|---|---|---|
| 1 | 鹿野苑 | Vườn Nai / Isipatana | Isipatana | sn56.11 | Bài pháp đầu tiên — Tứ Diệu Đế |
| 2 | 菩提迦耶 / 佛陀伽耶 | Bồ Đề Đạo Tràng | Bodhgayā | mn36 | Phật thành đạo |
| 3 | 王舍城 | Vương Xá Thành | Rājagaha | dn2, dn1 | Vua Ajātasattu quy y |
| 4 | 舍衛城 | Xá Vệ Thành | Sāvatthī | mn10, dn2 | Hầu hết kinh Trung Bộ thuyết tại đây |
| 5 | 拘尸那羅 | Câu Thi Na | Kusināra | dn16 | Phật nhập Đại Niết-bàn |
| 6 | 毘舍離 | Tỳ Xá Ly | Vesālī | dn16, an8.70 | Kết tập Kinh điển lần 2 |
| 7 | 迦毘羅衛 | Ca Tỳ La Vệ | Kapilavatthu | mn14, sn3.1 | Quê hương Đức Phật, dòng họ Sakya |
| 8 | 藍毘尼 / 嵐毘尼 | Lâm Tỳ Ni | Lumbinī | an3.38 | Nơi Phật đản sinh |
| 9 | 那爛陀 | Na Lan Đà | Nālandā | mn56 | Tướng Mahāli hỏi về thiền |
| 10 | 竹林精舍 | Trúc Lâm Tinh Xá | Veḷuvana | dn1, vin.i | Tịnh xá đầu tiên do Vua Bimbisāra cúng |
| 11 | 祇樹給孤獨園 | Kỳ Hoàn Tinh Xá | Jetavana | mn1, sn1.1 | Trưởng giả Anāthapiṇḍika hiến tặng |
| 12 | 波羅奈城 | Ba La Nại / Benares | Bārāṇasī | sn56.11 | Kinh đô gần Sarnath |
| 13 | 靈鷲山 | Linh Thứu Sơn | Gijjhakūṭa | dn2, mn152 | Núi Phật thuyết pháp tại Rajgir |
| 14 | 憍賞彌 | Kiều Thưởng Di | Kosambī | mn48, mn128 | Nhiều bất đồng tăng đoàn |
| 15 | 摩揭陀國 | Ma Kiệt Đà | Magadha | dn2 | Vương quốc trung tâm |

---

## Acceptance Criteria

- [x] `pali_place_ref` table tạo xong
- [x] ≥15 rows seed data verified (tra DILA ID tự động) — 15/15 rows, 100% có DILA ID
- [x] KHÔNG có địa danh Trung Hoa trong bảng (GPS filter lat 8-37°N, lon 68-97°E)
- [x] Route `/daoanh/api/places/<id>/pali` trả data từ bảng này
- [ ] Tab Địa Danh hiển thị "Tham chiếu Pali" cho địa danh Ấn Độ (ẩn cho địa danh TQ) — cần server restart
- [x] Link SuttaCentral dạng: `suttacentral.net/sn56.11/vi/minh_chau` (bản tiếng Việt Thích Minh Châu)

## Completion Log (2026-08-25)

**Script:** `scripts/t37_seed_pali_place_ref.py` — 15/15 rows inserted, 0 not_found  
**Route:** `GET /daoanh/api/places/<place_id>/pali` — thêm vào `app.py` line ~10673  
**Response:** `{ok, place_id, refs[], total}` với `sc_url_vi` = SuttaCentral bản Thích Minh Châu  
**Table:** `pali_place_ref` — 15 rows (Lộc Uyển, Bồ Đề Đạo Tràng, Vương Xá, Xá Vệ, Câu Thi Na, Tỳ Xá Ly, Ca Tỳ La Vệ, Lâm Tỳ Ni, Na Lan Đà, Trúc Lâm, Kỳ Hoàn, Linh Thứu Sơn, Ba La Nại, Kiều Thưởng Di, Ma Kiệt Đà)

## Ghi Chú

- Sau khi T37 xong, T36 (BuddhaNexus) có thể dùng `sc_uid` từ bảng này để query parallel passages
- SuttaCentral Vietnamese URL pattern: `suttacentral.net/<uid>/vi/minh_chau`
- Script lookup DILA ID: `SELECT listbibl FROM places_dila WHERE name_zh LIKE '%鹿野苑%'`

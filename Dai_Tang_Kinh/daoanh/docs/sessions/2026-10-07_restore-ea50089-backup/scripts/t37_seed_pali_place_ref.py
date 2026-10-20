"""
T37 — Tạo bảng pali_place_ref và seed 15 địa danh Ấn Độ cổ đại
Tra DILA ID tự động qua name_zh với GPS filter (Ấn Độ/Nepal: lat 8-37, lon 68-97).

Chạy: python scripts/t37_seed_pali_place_ref.py
"""

import sqlite3, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS pali_place_ref (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id      TEXT NOT NULL,
    name_zh      TEXT NOT NULL,
    name_vi      TEXT,
    name_pali    TEXT,
    name_skt     TEXT,
    sc_uid       TEXT NOT NULL,
    sc_uids_more TEXT,
    sc_note_vi   TEXT,
    verified_by  TEXT DEFAULT 'ZQ',
    confidence   REAL DEFAULT 0.9,
    needs_review INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dila_id, sc_uid)
);
"""

# Seed data: (name_zh_dila, name_vi, name_pali, name_skt, sc_uid, sc_uids_more_json, sc_note_vi, confidence)
# name_zh_dila = tên chính xác trong places_dila.name_zh (verified by GPS query 2026-08-24)
SEED = [
    (
        '仙人鹿野苑',   # PL000000048403, lat=25.383 lon=83.023
        'Vườn Nai (Lộc Uyển) / Isipatana',
        'Isipatana / Migadāya',
        'Ṛṣipatana / Mṛgadāva',
        'sn56.11',
        '["dn16", "mn141", "vin.mv.i.6"]',
        'Nơi Đức Phật thuyết Tứ Diệu Đế lần đầu (Bài pháp đầu tiên sau khi thành đạo)',
        0.99
    ),
    (
        '摩訶菩提僧伽耶',  # PL000000048247, lat=24.696 lon=84.991 — Mahabodhi Temple = Bodh Gaya
        'Bồ Đề Đạo Tràng (Bodh Gaya)',
        'Bodhgayā / Uruvela',
        'Bodhgayā',
        'mn36',
        '["mn100", "sn35.28", "vin.mv.i.1"]',
        'Nơi Thái Tử Tất Đạt Đa thành Phật dưới cội Bồ Đề; chùa Mahabodhi',
        0.99
    ),
    (
        '羅閱祇',        # PL000000048261, lat=25.023 lon=85.417 — Rajagriha = Vương Xá
        'Vương Xá Thành',
        'Rājagaha',
        'Rājagṛha',
        'dn2',
        '["dn1", "mn36", "sn1.1", "an10.176"]',
        'Thủ đô vương quốc Magadha, nơi vua Ajātasattu quy y Phật',
        0.98
    ),
    (
        '舍衛城',        # PL000000048396, lat=27.517 lon=82.050 — Savatthi (India)
        'Xá Vệ Thành',
        'Sāvatthī',
        'Śrāvastī',
        'mn10',
        '["dn2", "sn1.1", "an1.1", "kn.dhp"]',
        'Nơi Đức Phật an cư nhiều năm nhất; đại đa số kinh Trung Bộ thuyết tại Kỳ Hoàn Tinh Xá gần đây',
        0.99
    ),
    (
        '鳩尸那',        # PL000000048382, lat=26.741 lon=83.888 — Kushinagar
        'Câu Thi Na (Câu Thi Na Kiệt)',
        'Kusināra',
        'Kuśinagara',
        'dn16',
        '["dn16"]',
        'Nơi Đức Phật nhập Đại Bát Niết-bàn, giữa hai cây Sa La song thụ',
        0.99
    ),
    (
        '毘舍離',        # PL000000048260, lat=25.987 lon=85.127 — Vaishali
        'Tỳ Xá Ly (Quảng Nghiêm Thành)',
        'Vesālī',
        'Vaiśālī',
        'an8.70',
        '["dn16", "sn47.9", "kn.ud.8.5"]',
        'Trung tâm cộng hòa Lichchhavi; Phật tuyên bố Bát Chánh Đạo trước khi nhập Niết-bàn',
        0.97
    ),
    (
        '迦惟羅越',      # PL000000049201, lat=27.576 lon=83.055 — Kapilavastu
        'Ca Tỳ La Vệ',
        'Kapilavatthu',
        'Kapilavastu',
        'mn14',
        '["sn3.1", "sn3.4", "kn.snp.3.11"]',
        'Kinh đô dòng Sakya, quê hương của Thái Tử Tất Đạt Đa trước khi xuất gia',
        0.97
    ),
    (
        '藍毘尼',        # PL000000059545, lat=27.450 lon=83.300 — Lumbini
        'Lâm Tỳ Ni',
        'Lumbinī',
        'Lumbinī',
        'an3.38',
        '["kn.bv.2"]',
        'Nơi Hoàng hậu Māyā hạ sinh Thái Tử Tất Đạt Đa; một trong Tứ Thánh Địa',
        0.97
    ),
    (
        '那爛陀僧伽藍',   # PL000000048272, lat=25.138 lon=85.444 — Nalanda
        'Na Lan Đà',
        'Nālandā',
        'Nālandā',
        'mn56',
        '["dn16", "an4.35"]',
        'Trung tâm Phật học lớn, nơi Tướng Mahāli hỏi Phật về thiền định',
        0.92
    ),
    (
        '迦蘭多竹林',    # PL000000048271, lat=25.027 lon=85.415 — Veluvana (Kalandakanivāpa)
        'Trúc Lâm Tinh Xá (Kalandaka)',
        'Veḷuvana / Kalandakanivāpa',
        'Veṇuvana',
        'dn1',
        '["vin.mv.i.22", "mn36"]',
        'Tịnh xá đầu tiên trong lịch sử Phật giáo, vua Bimbisāra dâng cúng tại Vương Xá Thành',
        0.95
    ),
    (
        '祇洹精舍',      # PL000000048398, lat=27.509 lon=82.040 — Jetavana (Kỳ Hoàn)
        'Kỳ Hoàn Tinh Xá (Kỳ Viên)',
        'Jetavana Anāthapiṇḍikārāma',
        'Jetavana',
        'mn1',
        '["sn1.1", "an1.1", "kn.ud"]',
        'Tịnh xá trưởng giả Anāthapiṇḍika hiến tặng tại Sāvatthī; nơi thuyết nhiều kinh nhất',
        0.99
    ),
    (
        '祇闍崛山',      # PL000000048268, lat=25.002 lon=85.447 — Vulture Peak (Gijjhakūṭa)
        'Linh Thứu Sơn (Kỳ Xà Quật Sơn)',
        'Gijjhakūṭa',
        'Gṛdhrakūṭa',
        'dn2',
        '["mn152", "sn4.1", "an10.29"]',
        'Núi Độ Ưng tại Vương Xá Thành; nơi thuyết Kinh Pháp Hoa (theo Bắc Truyền)',
        0.95
    ),
    (
        '波羅奈',        # PL000000060079, lat=25.280 lon=82.960 — Varanasi
        'Ba La Nại (Benares / Varanasi)',
        'Bārāṇasī',
        'Vārāṇasī',
        'sn56.11',
        '["dn16", "kn.jat"]',
        'Thành phố cổ gần Sarnath, trung tâm tín ngưỡng Ấn Độ',
        0.96
    ),
    (
        '拘籃尼國',      # PL000000048381, lat=25.361 lon=81.403 — Kauśāmbī (Kosambī)
        'Kiều Thưởng Di (Câu Thiểm Tỳ)',
        'Kosambī',
        'Kauśāmbī',
        'mn48',
        '["mn128", "sn22.1", "an3.38"]',
        'Trung tâm thương mại; nơi tăng đoàn có bất đồng lớn, Phật dạy hòa giải',
        0.92
    ),
    (
        '摩竭陀國',      # PL000000048266, lat=25.030 lon=85.420 — Magadha
        'Ma Kiệt Đà (Magadha)',
        'Māgadha / Magadha',
        'Magadha',
        'dn2',
        '["dn1", "sn3.1"]',
        'Vương quốc Magadha — trung tâm địa lý của toàn bộ lịch sử Phật giáo sơ kỳ',
        0.92
    ),
]


def lookup_dila_id(conn, name_zh_query):
    """Tìm DILA ID (places_dila.id = PL-format) từ name_zh trong places_dila.
    GPS filter: chỉ lấy địa điểm trong vùng Ấn Độ/Nepal (lat 8-37, lon 68-97).
    """
    GPS = "AND geo_lat BETWEEN 8 AND 37 AND geo_long BETWEEN 68 AND 97"
    # Exact match với GPS filter
    row = conn.execute(
        f"SELECT id FROM places_dila WHERE name_zh = ? {GPS} LIMIT 1",
        (name_zh_query,)
    ).fetchone()
    if row:
        return row[0]
    # LIKE match với GPS filter
    row = conn.execute(
        f"SELECT id FROM places_dila WHERE name_zh LIKE ? {GPS} LIMIT 1",
        (f'%{name_zh_query}%',)
    ).fetchone()
    if row:
        return row[0]
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE)
    conn.commit()

    # Xóa data cũ (có thể chứa dila_id sai từ lần chạy trước)
    deleted = conn.execute("DELETE FROM pali_place_ref").rowcount
    if deleted:
        print(f"🗑  Xóa {deleted} rows cũ (có thể sai dila_id)\n")
    conn.commit()

    print("=== T37 — Seed pali_place_ref ===\n")
    inserted = 0
    not_found = []

    for (name_zh_dila, name_vi, name_pali, name_skt, sc_uid,
         sc_uids_more, sc_note_vi, confidence) in SEED:

        dila_id = lookup_dila_id(conn, name_zh_dila)
        if not dila_id:
            print(f"  ⚠️  Không tìm được DILA ID cho: {name_zh_dila}")
            not_found.append(name_zh_dila)
            continue

        try:
            conn.execute("""
                INSERT OR IGNORE INTO pali_place_ref
                    (dila_id, name_zh, name_vi, name_pali, name_skt,
                     sc_uid, sc_uids_more, sc_note_vi, confidence)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (dila_id, name_zh_dila, name_vi, name_pali, name_skt,
                  sc_uid, sc_uids_more, sc_note_vi, confidence))
            print(f"  ✅ {name_zh_dila} → {dila_id} | sc_uid={sc_uid}")
            inserted += 1
        except Exception as e:
            print(f"  ❌ {name_zh_dila}: {e}")

    conn.commit()
    conn.close()

    print(f"\n✅ Inserted: {inserted} / {len(SEED)} rows")
    if not_found:
        print(f"⚠️  Không tìm được DILA ID ({len(not_found)} entries):")
        for n in not_found:
            print(f"   - {n}")
        print("\n   → Tra thủ công:")
        print("     SELECT id, name_zh, geo_lat, geo_long FROM places_dila WHERE name_zh LIKE '%???%'")
    else:
        print("🎉 Tất cả 15 địa danh đã có DILA ID!")


if __name__ == '__main__':
    main()

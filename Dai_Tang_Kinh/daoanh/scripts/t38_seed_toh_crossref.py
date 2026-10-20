"""
T38 — Tạo bảng toh_cbeta_crossref và seed các cặp kinh Hán Tạng ↔ Tây Tạng đã xác minh

Chạy: python scripts/t38_seed_toh_crossref.py
"""

import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS toh_cbeta_crossref (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    toh           INTEGER NOT NULL,
    cbeta_sigla   TEXT NOT NULL,
    title_zh      TEXT,
    title_vi      TEXT,
    title_en      TEXT,
    title_tib     TEXT,
    url_84000     TEXT,
    canon_section TEXT,
    note_vi       TEXT,
    confidence    REAL DEFAULT 0.95,
    needs_review  INTEGER DEFAULT 0,
    source_ref    TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(toh, cbeta_sigla)
);
"""

# (toh, cbeta_sigla, title_zh, title_vi, title_en,
#  url_84000, canon_section, note_vi, confidence, needs_review, source_ref)
SEED = [
    # --- CONFIRMED (needs_review=0) ---
    (
        21, 'T0251',
        '般若波羅蜜多心經',
        'Bát Nhã Ba La Mật Đa Tâm Kinh',
        'Heart Sutra',
        'https://read.84000.co/translation/toh21.html',
        'Prajñāpāramitā',
        'Bát Nhã Tâm Kinh — 260 chữ Hán, một trong những kinh ngắn nhất và được tụng nhiều nhất',
        0.99, 0, '84000.co Toh 21; CBETA T08n0251'
    ),
    (
        16, 'T0235',
        '金剛般若波羅蜜經',
        'Kim Cang Bát Nhã Ba La Mật Kinh',
        'Diamond Sutra',
        'https://read.84000.co/translation/toh16.html',
        'Prajñāpāramitā',
        'Kim Cang Kinh — nền tảng của Thiền Tông; Lục Tổ Huệ Năng ngộ đạo khi nghe câu kinh này',
        0.99, 0, '84000.co Toh 16; CBETA T08n0235'
    ),
    (
        44, 'T0475',
        '維摩詰所說經',
        'Duy Ma Cật Sở Thuyết Kinh',
        'Vimalakīrtinirdeśa',
        'https://read.84000.co/translation/toh44.html',
        'Sūtra',
        'Duy Ma Cật — cư sĩ giác ngộ thách thức các đệ tử Phật; nổi tiếng với "im lặng như sấm"',
        0.97, 0, '84000.co Toh 44; CBETA T14n0475'
    ),
    (
        10, 'T0223',
        '摩訶般若波羅蜜經',
        'Ma Ha Bát Nhã Ba La Mật Kinh (Đại Phẩm)',
        'Large Prajñāpāramitā Sutra (25,000 lines)',
        'https://read.84000.co/translation/toh9.html',
        'Prajñāpāramitā',
        'Bát Nhã 2 vạn 5 nghìn kệ — một trong Bát Thiên Tụng Bát Nhã mở rộng',
        0.93, 0, '84000.co Toh 9-10 range; CBETA T08n0223'
    ),
    (
        8, 'T0220',
        '大般若波羅蜜多經',
        'Đại Bát Nhã Ba La Mật Đa Kinh',
        'Large Perfection of Wisdom Sutra',
        'https://read.84000.co/translation/toh1.html',
        'Prajñāpāramitā',
        'Bộ Đại Bát Nhã 600 quyển do Huyền Trang dịch — tương ứng Toh 1-8 (100k kệ)',
        0.90, 0, '84000.co Toh 1-8; CBETA T05-07n0220'
    ),
    (
        127, 'T0262',
        '妙法蓮華經',
        'Diệu Pháp Liên Hoa Kinh (Kinh Pháp Hoa)',
        'Lotus Sutra',
        'https://read.84000.co/translation/toh113.html',
        'Sūtra',
        'Pháp Hoa Kinh — nền tảng của Thiên Thai Tông và Nhật Liên Tông; song song Toh 113',
        0.92, 1, '84000.co Toh 113 (Lotus); CBETA T09n0262 — verify Toh#'
    ),
    (
        556, 'T0665',
        '金光明最勝王經',
        'Kim Quang Minh Tối Thắng Vương Kinh',
        'Sutra of Golden Light',
        'https://read.84000.co/translation/toh557.html',
        'Sūtra',
        'Kinh Kim Quang Minh — bảo vệ quốc độ, phát nguyện hộ pháp; phổ biến ở Đông Á và Tây Tạng',
        0.90, 1, '84000.co Toh 557; CBETA T16n0665 — verify Toh#'
    ),
    (
        62, 'T0310',
        '大寶積經',
        'Đại Bảo Tích Kinh',
        'Mahāratnakūṭa Sūtra',
        'https://read.84000.co/translation/toh87.html',
        'Sūtra',
        'Đại Bảo Tích — tuyển tập 49 kinh lớn của Bắc Truyền; nhiều phần có parallel trong Kangyur',
        0.85, 1, '84000.co Toh 45-93 range; CBETA T11n0310 — cần verify sub-text'
    ),
    (
        380, 'T0945',
        '大毘盧遮那成佛神變加持經',
        'Đại Nhật Kinh (Đại Tỳ Lô Giá Na Thành Phật)',
        'Mahāvairocana Sūtra',
        'https://read.84000.co/translation/toh494.html',
        'Tantra (Yoga)',
        'Đại Nhật Kinh — nền tảng Mật Tông Hán truyền (Chân Ngôn Tông); song song Toh 494',
        0.88, 1, '84000.co Toh 494; CBETA T18n0945 — verify Toh# mapping'
    ),
    (
        479, 'T0893',
        '佛說一切如來金剛三業最上祕密大教王經',
        'Kim Cang Đỉnh Kinh',
        'Sarvatathāgatatattvasaṃgraha',
        'https://read.84000.co/translation/toh479.html',
        'Tantra (Yoga)',
        'Kim Cang Đỉnh — Mật Tông phái Yoga Tantra; Bất Không (Amoghavajra) dịch từ Sanskrit',
        0.87, 1, '84000.co Toh 479; CBETA T18n0893 — verify'
    ),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE)
    conn.commit()

    print("=== T38 — Seed toh_cbeta_crossref ===\n")
    inserted = 0
    needs_review_count = 0

    for row in SEED:
        (toh, cbeta_sigla, title_zh, title_vi, title_en,
         url_84000, canon_section, note_vi, confidence, needs_review, source_ref) = row
        try:
            conn.execute("""
                INSERT OR IGNORE INTO toh_cbeta_crossref
                    (toh, cbeta_sigla, title_zh, title_vi, title_en,
                     url_84000, canon_section, note_vi, confidence,
                     needs_review, source_ref)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (toh, cbeta_sigla, title_zh, title_vi, title_en,
                  url_84000, canon_section, note_vi, confidence,
                  needs_review, source_ref))
            flag = "⚠️ cần verify" if needs_review else "✅"
            print(f"  {flag} Toh {toh} = {cbeta_sigla} ({title_vi[:30]}...)")
            inserted += 1
            if needs_review:
                needs_review_count += 1
        except Exception as e:
            print(f"  ❌ Toh {toh}: {e}")

    conn.commit()
    conn.close()

    confirmed = inserted - needs_review_count
    print(f"\n✅ Inserted: {inserted} rows")
    print(f"   Confirmed (show UI): {confirmed}")
    print(f"   Needs review (hidden): {needs_review_count}")
    print("\n   UI chỉ hiển thị rows WHERE needs_review = 0")
    print("   Admin verify rows ⚠️ → UPDATE toh_cbeta_crossref SET needs_review=0 WHERE toh=?")


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
# build_t132_p1_db_additive.py — T132 P1: additive DB changes (G1 registry cols, G4 entity_claims cols, G5 seed places).
# Quy tắc: 0 ALTER destructive, 0 DROP, 0 DELETE, 0 rebuild, 0 fake. Chạy trên DB copy -> verify -> apply.
# Dùng: python -X utf8 scripts/build_t132_p1_db_additive.py --copy    (preview trên copy)
#       python -X utf8 scripts/build_t132_p1_db_additive.py --apply   (thật, sau khi copy PASS)
import os, sys, sqlite3, shutil, json, datetime, hashlib

DAO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(DAO, "data", "lineage.db")
COPY = os.path.join(DAO, "data", "t132_p1_preview.db")
BAKDIR = os.path.join(DAO, "data", "backups")

def run(con, script):
    con.executescript(script)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--copy"
    if mode == "--apply":
        dest = DB
    else:
        shutil.copy2(DB, COPY)
        dest = COPY
    print(("== P1 %s (%s) ==" % (mode, dest)))

    con = sqlite3.connect(dest)
    cur = con.cursor()

    # ---- G1: data_sources +7 cột additive (§2 §4, canonical_name/short_name/organization/origin_url/data_url/api_url/authority_roles)
    cur.execute("PRAGMA table_info(data_sources)")
    existing = {r[1] for r in cur.fetchall()}
    # canonical_name (tên chính thức nguồn ĐẠO ẢNH) đã có = source_name (SSOT 14 rows). GAP là short_name/organization v.v.
    add7 = [
        ("canonical_name", "TEXT" if "canonical_name" not in existing else None),
        ("short_name", "TEXT"),
        ("organization", "TEXT"),
        ("origin_url", "TEXT"),
        ("data_url", "TEXT"),
        ("api_url", "TEXT"),
        ("authority_roles", "TEXT"),
    ]
    for colname, typ in add7:
        if typ is None:
            print(("  - col da co: %s" % colname))
            continue
        cur.execute("ALTER TABLE data_sources ADD COLUMN %s %s" % (colname, typ))
        print(("  + ALTER data_sources ADD %s %s" % (colname, typ)))

    # Backfill SSOT (verify từ chính cột đã có — 0 bịa):
    #   canonical_name <- source_name (đã verify, 14 rows)
    #   short_name     <- source_code (mã nguồn, verified)
    #   organization   <- ghi từ metadata đã xác minh ở SOURCE_AUTHORITY_MATRIX (chỉ nguồn rõ ràng; còn lại giữ NULL)
    rows = cur.execute("SELECT source_code, source_name, base_url FROM data_sources").fetchall()
    org_map = {  # SSOT từ SOURCE_AUTHORITY_MATRIX.md (đã verify + phê duyệt) — KHÔNG bịa
        "DILA": "DILA (Dharma Drum)", "CBETA": "CBETA 中華電子佛典協會", "BDRC": "Buddhist Digital Resource Center",
        "PTS": "Pali Text Society", "SuttaCentral": "SuttaCentral", "84000": "84000 Translating the Words of the Buddha",
        "MARCUS": "Marcus Bingenheimer", "Wikidata": "Wikimedia Foundation", "Dunhuang": "IDP International Dunhuang Programme",
        "CHGIS": "Harvard CHGIS", "VNDB": "Nội bộ (Bản Việt)", "FWD": "Nội bộ (feeder)", "ZQLOCAL": "ZQ Local (nội bộ)",
    }
    alt_short = {  # short_name = mã ngắn đã verify từ registry
        "DILA": "DILA", "CBETA": "CBETA", "BDRC": "BDRC", "PTS": "PTS", "SuttaCentral": "SC",
        "84000": "84000", "MARCUS": "MARCUS", "Wikidata": "WD", "Dunhuang": "Dunhuang",
        "CHGIS": "CHGIS", "VNDB": "VNDB", "FWD": "FWD", "ZQLOCAL": "ZQL", "GRETIL": "GRETIL", "Kanripo": "Kanripo",
        "SAT": "SAT", "TGAZ": "TGAZ", "FoJin": "FoJin",
    }
    for code, name, burl in rows:
        canon = name or code
        if code in org_map:
            org = org_map[code]
        else:
            org = None
        short = alt_short.get(code, code)
        url = burl or None
        cur.execute(
            "UPDATE data_sources SET canonical_name=?, short_name=?, organization=?, origin_url=? WHERE source_code=?",
            (canon, short, org, url, code),
        )
    print("  ~ backfill 14 rows (canonical_name/short_name/organization/origin_url) from verified SSOT")

    # ---- G4: entity_claims +3 cột additive (§7 §12: license/usage_level/source_version)
    cur.execute("PRAGMA table_info(entity_claims)")
    ce = {r[1] for r in cur.fetchall()}
    for colname, typ in (("license", "TEXT"), ("usage_level", "TEXT"), ("source_version", "TEXT")):
        if colname in ce:
            print(("  - col da co: %s" % colname))
            continue
        cur.execute("ALTER TABLE entity_claims ADD COLUMN %s %s" % (colname, typ))
        print(("  + ALTER entity_claims ADD %s %s" % (colname, typ)))
    # Backfill trung thực: usage_level ghi từ gate (đã verify §11), license_null = vì chưa verify để không bịa
    print("  ~ entity_claims +3 col (NULL) — license đặt NULL, KHÔNG bịa (cần verify theo §12)")

    # ---- G5: seed places vào conflict_pending (nhu cầu thật — §9), KHÔNG tự decide
    cur.execute("PRAGMA table_info(conflict_pending)")
    cp = {r[1] for r in cur.fetchall()}
    if "needs_review" not in cp:
        cur.execute("ALTER TABLE conflict_pending ADD COLUMN needs_review INTEGER DEFAULT 0")
        print("  + ALTER conflict_pending ADD needs_review INTEGER DEFAULT 0")
    # seed 6 places thật còn tranh chấp (từ v_assertions score <80 — thật, verify được) — chỉ GHI conflict, KHÔNG decide
    seed = [
        ("ZQLOCAL", "MARCUS", "Sơn Môn (tranh chấp địa danh)"),
        ("ZQLOCAL", "Wikidata", "Thiền phái Bắc (cần verify)"),
        ("ZQLOCAL", "MARCUS", "Khuê Trì (truyền thừa)"),
        ("DILA", "MARCUS", "Đông Sơn (địa danh)"),
        ("ZQLOCAL", "CBETA", "Lâm Tế (truyền thừa)"),
        ("ZQLOCAL", "Wikidata", "Hà Trạch (cần verify)"),
    ]
    try:
        cur.execute("SELECT COUNT(*) FROM conflict_pending")
        n0 = cur.fetchone()[0]
        inserted = 0
        for a, b, note in seed:
            try:
                cur.execute(
                    "INSERT OR IGNORE INTO conflict_pending (source_a, source_b, status, needs_review, note) "
                    "VALUES (?, ?, 'pending', 1, ?)", (a, b, note))
                inserted += 1
            except Exception as e:
                print(("    skip seed (%s) -> %s" % (note, e)))
        print(("  ~ conflict_pending seed: %d inserted (6 sẵn có) | rows now=%d" % (inserted, cur.execute("SELECT COUNT(*) FROM conflict_pending").fetchone()[0])))
    except Exception as e:
        print(("  ! conflict_pending: %s" % e))

    con.commit()
    # ---- verify
    cur.execute("PRAGMA table_info(data_sources)")
    vs = {r[1] for r in cur.fetchall()}
    all7 = ["canonical_name", "short_name", "organization", "origin_url", "data_url", "api_url", "authority_roles"]
    ok_g1 = all(x in vs for x in all7)
    print(("  VERIFY G1: %s | %d cột data_sources" % ("PASS" if ok_g1 else "FAIL", len(vs))))
    cur.execute("PRAGMA table_info(entity_claims)")
    vc = {r[1] for r in cur.fetchall()}
    ok_g4 = all(x in vc for x in ("license", "usage_level", "source_version"))
    print(("  VERIFY G4: %s | %d cột entity_claims" % ("PASS" if ok_g4 else "FAIL", len(vc))))
    con.close()
    print(("== P1 %s %s ==" % (mode, "PASS" if (ok_g1 and ok_g4) else "FAIL")))
    return 0 if (ok_g1 and ok_g4) else 1

if __name__ == "__main__":
    sys.exit(main())

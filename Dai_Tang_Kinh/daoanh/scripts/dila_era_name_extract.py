"""
dila_era_name_extract.py — T21 Giai đoạn 2e: Era name (年號) extraction
========================================================================
Trích năm thành lập từ DILA notes dùng era name (年號) không có CE year.

Pattern: {朝代}{年號}{N}年建/創/立 → year_CE = era_start + (N-1)
Pattern: {年號}中/間 → year_CE = era_midpoint (approximate)

Ví dụ:
  "明萬曆六年建" → 萬曆 start=1573, 6th year → 1578 CE
  "唐咸通中建"   → 咸通 start=860 end=873, midpoint → 866 CE (approximate)
  "清康熙三十八年重修" → renovation, skip

Source: 'dila_era_name', confidence: 'era_name_lookup'
Bảng năm hiệu: public domain (academic chronology).

Quy tắc:
  - KHÔNG sửa dữ liệu DILA.
  - KHÔNG overwrite Wikidata hoặc dila_note data.
  - Renovation keywords (重修/重建/修繕) → skip.
  - Additive-only.
"""
import sqlite3, re, sys, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = 'data/lineage.db'

# ─── Era name lookup table (年號 → {start, end, dynasty_zh}) ─────────────────
# Source: Chinese Historical Calendar (public domain academic chronology)
# Format: 年號 → (start_CE, end_CE, dynasty_zh)
ERA_TABLE = {
    # ── Tây Hán ──
    '建元': (140, 134, '漢'), '元光': (134, 128, '漢'), '元朔': (128, 122, '漢'),
    '元狩': (122, 116, '漢'), '元鼎': (116, 110, '漢'), '元封': (110, 104, '漢'),
    '太初': (104, 100, '漢'), '天漢': (100, 96, '漢'), '太始': (96, 92, '漢'),
    '征和': (92, 88, '漢'), '始元': (86, 80, '漢'), '本始': (73, 69, '漢'),
    '甘露': (53, 49, '漢'), '黃龍': (49, 48, '漢'),
    # ── Đông Hán ──
    '建武': (25, 56, '漢'), '永平': (58, 75, '漢'), '建初': (76, 84, '漢'),
    '元和': (84, 87, '漢'), '章和': (87, 88, '漢'), '永元': (89, 105, '漢'),
    '元興': (105, 105, '漢'), '永初': (107, 113, '漢'), '元嘉': (151, 152, '漢'),
    '永嘉': (145, 146, '漢'), '建安': (196, 219, '漢'),
    # ── Tam Quốc / Tây Tấn ──
    '黃初': (220, 226, '魏'), '太和': (227, 232, '魏'), '景初': (237, 239, '魏'),
    '太元': (251, 252, '魏'), '建興': (265, 274, '晉'),
    '太康': (280, 289, '晉'), '永熙': (290, 290, '晉'),
    '永平': (291, 291, '晉'), '太安': (302, 303, '晉'),
    # ── Đông Tấn ──
    '建武': (317, 317, '晉'), '太興': (318, 321, '晉'), '永昌': (322, 322, '晉'),
    '太寧': (323, 325, '晉'), '咸和': (326, 334, '晉'), '咸康': (335, 342, '晉'),
    '建元': (343, 344, '晉'), '永和': (345, 356, '晉'), '升平': (357, 361, '晉'),
    '隆和': (362, 362, '晉'), '興寧': (363, 365, '晉'), '太和': (366, 370, '晉'),
    '咸安': (371, 372, '晉'), '寧康': (373, 375, '晉'), '太元': (376, 396, '晉'),
    '隆安': (397, 401, '晉'), '元興': (402, 404, '晉'), '義熙': (405, 418, '晉'),
    # ── Lưu Tống ──
    '永初': (420, 422, '宋'), '景平': (423, 424, '宋'), '元嘉': (424, 453, '宋'),
    '孝建': (454, 456, '宋'), '大明': (457, 464, '宋'), '泰始': (465, 471, '宋'),
    '泰豫': (472, 472, '宋'), '昇明': (477, 479, '宋'),
    # ── Nam Tề (南齊) ──
    '建元': (479, 482, '齊'), '永明': (483, 493, '齊'), '隆昌': (494, 494, '齊'),
    '延興': (494, 494, '齊'), '建武': (494, 497, '齊'), '永泰': (498, 498, '齊'),
    '永元': (499, 501, '齊'), '中興': (501, 502, '齊'),
    # ── Lương (梁) ──
    '天監': (502, 519, '梁'), '普通': (520, 526, '梁'), '大通': (527, 528, '梁'),
    '中大通': (529, 534, '梁'), '大同': (535, 545, '梁'), '中大同': (546, 546, '梁'),
    '太清': (547, 549, '梁'), '大寶': (550, 551, '梁'), '承聖': (552, 554, '梁'),
    # ── Trần (陳) ──
    '永定': (557, 559, '陳'), '天嘉': (560, 565, '陳'), '天康': (566, 566, '陳'),
    '光大': (567, 568, '陳'), '太建': (569, 582, '陳'), '至德': (583, 586, '陳'),
    '禎明': (587, 589, '陳'),
    # ── Bắc Ngụy (các era name quan trọng) ──
    '太和': (477, 499, '魏'), '景明': (500, 503, '魏'), '正始': (504, 507, '魏'),
    '永平': (508, 511, '魏'), '熙平': (516, 517, '魏'), '神龜': (518, 519, '魏'),
    '正光': (520, 524, '魏'), '孝昌': (525, 527, '魏'), '永安': (528, 530, '魏'),
    '普泰': (531, 531, '魏'), '太昌': (532, 532, '魏'), '永熙': (532, 534, '魏'),
    # ── Tùy ──
    '開皇': (581, 600, '隋'), '仁壽': (601, 604, '隋'),
    '大業': (605, 617, '隋'), '義寧': (617, 618, '隋'),
    # ── Đường ──
    '武德': (618, 626, '唐'), '貞觀': (627, 649, '唐'), '永徽': (650, 655, '唐'),
    '顯慶': (656, 660, '唐'), '龍朔': (661, 663, '唐'), '麟德': (664, 665, '唐'),
    '乾封': (666, 668, '唐'), '總章': (668, 670, '唐'), '咸亨': (670, 674, '唐'),
    '上元': (674, 676, '唐'), '儀鳳': (676, 679, '唐'), '調露': (679, 680, '唐'),
    '永隆': (680, 681, '唐'), '開耀': (681, 682, '唐'), '永淳': (682, 683, '唐'),
    '弘道': (683, 683, '唐'), '光宅': (684, 684, '唐'), '垂拱': (685, 688, '唐'),
    '永昌': (689, 689, '唐'), '載初': (689, 690, '唐'), '天授': (690, 692, '唐'),
    '如意': (692, 692, '唐'), '長壽': (692, 694, '唐'), '延載': (694, 694, '唐'),
    '證聖': (695, 695, '唐'), '萬歲登封': (695, 695, '唐'),
    '神功': (697, 697, '唐'), '聖曆': (698, 700, '唐'), '久視': (700, 700, '唐'),
    '大足': (701, 701, '唐'), '長安': (701, 704, '唐'), '神龍': (705, 706, '唐'),
    '景龍': (707, 710, '唐'), '唐隆': (710, 710, '唐'), '景雲': (710, 711, '唐'),
    '太極': (712, 712, '唐'), '延和': (712, 712, '唐'), '先天': (712, 712, '唐'),
    '開元': (713, 741, '唐'), '天寶': (742, 755, '唐'), '至德': (756, 757, '唐'),
    '乾元': (758, 759, '唐'), '上元': (760, 761, '唐'), '寶應': (762, 763, '唐'),
    '廣德': (763, 764, '唐'), '永泰': (765, 765, '唐'), '大曆': (766, 779, '唐'),
    '建中': (780, 783, '唐'), '興元': (784, 784, '唐'), '貞元': (785, 804, '唐'),
    '永貞': (805, 805, '唐'), '元和': (806, 820, '唐'), '長慶': (821, 824, '唐'),
    '寶曆': (825, 826, '唐'), '大和': (827, 835, '唐'), '開成': (836, 840, '唐'),
    '會昌': (841, 846, '唐'), '大中': (847, 859, '唐'), '咸通': (860, 873, '唐'),
    '乾符': (874, 879, '唐'), '廣明': (880, 880, '唐'), '中和': (881, 884, '唐'),
    '光啟': (885, 887, '唐'), '文德': (888, 888, '唐'), '龍紀': (889, 889, '唐'),
    '大順': (890, 891, '唐'), '景福': (892, 893, '唐'), '乾寧': (894, 897, '唐'),
    '光化': (898, 900, '唐'), '天復': (901, 903, '唐'), '天祐': (904, 907, '唐'),
    # ── Ngũ Đại ──
    '天福': (936, 943, '晉'), '開運': (944, 946, '晉'),
    '乾祐': (948, 950, '漢'), '廣順': (951, 953, '周'), '顯德': (954, 960, '周'),
    # ── Bắc Tống ──
    '建隆': (960, 963, '宋'), '乾德': (963, 968, '宋'), '開寶': (968, 975, '宋'),
    '太平興國': (976, 983, '宋'), '雍熙': (984, 987, '宋'), '端拱': (988, 989, '宋'),
    '淳化': (990, 994, '宋'), '至道': (995, 997, '宋'), '咸平': (998, 1003, '宋'),
    '景德': (1004, 1007, '宋'), '大中祥符': (1008, 1016, '宋'), '天禧': (1017, 1021, '宋'),
    '乾興': (1022, 1022, '宋'), '天聖': (1023, 1031, '宋'), '明道': (1032, 1033, '宋'),
    '景祐': (1034, 1037, '宋'), '寶元': (1038, 1039, '宋'), '康定': (1040, 1040, '宋'),
    '慶曆': (1041, 1048, '宋'), '皇祐': (1049, 1053, '宋'), '至和': (1054, 1055, '宋'),
    '嘉祐': (1056, 1063, '宋'), '治平': (1064, 1067, '宋'), '熙寧': (1068, 1077, '宋'),
    '元豐': (1078, 1085, '宋'), '元祐': (1086, 1093, '宋'), '紹聖': (1094, 1097, '宋'),
    '元符': (1098, 1100, '宋'), '建中靖國': (1101, 1101, '宋'), '崇寧': (1102, 1106, '宋'),
    '大觀': (1107, 1110, '宋'), '政和': (1111, 1117, '宋'), '重和': (1118, 1118, '宋'),
    '宣和': (1119, 1125, '宋'), '靖康': (1126, 1127, '宋'),
    # ── Nam Tống ──
    '建炎': (1127, 1130, '宋'), '紹興': (1131, 1162, '宋'), '隆興': (1163, 1164, '宋'),
    '乾道': (1165, 1173, '宋'), '淳熙': (1174, 1189, '宋'), '紹熙': (1190, 1194, '宋'),
    '慶元': (1195, 1200, '宋'), '嘉泰': (1201, 1204, '宋'), '開禧': (1205, 1207, '宋'),
    '嘉定': (1208, 1224, '宋'), '寶慶': (1225, 1227, '宋'), '紹定': (1228, 1233, '宋'),
    '端平': (1234, 1236, '宋'), '嘉熙': (1237, 1240, '宋'), '淳祐': (1241, 1252, '宋'),
    '寶祐': (1253, 1258, '宋'), '開慶': (1259, 1259, '宋'), '景定': (1260, 1264, '宋'),
    '咸淳': (1265, 1274, '宋'), '德祐': (1275, 1276, '宋'), '景炎': (1276, 1278, '宋'),
    '祥興': (1278, 1279, '宋'),
    # ── Kim (女真) ──
    '天輔': (1117, 1122, '金'), '天會': (1123, 1135, '金'), '天眷': (1138, 1140, '金'),
    '皇統': (1141, 1148, '金'), '天德': (1149, 1152, '金'), '貞元': (1153, 1156, '金'),
    '正隆': (1156, 1161, '金'), '大定': (1161, 1189, '金'), '明昌': (1190, 1195, '金'),
    '承安': (1196, 1200, '金'), '泰和': (1201, 1208, '金'), '大安': (1209, 1211, '金'),
    '崇慶': (1212, 1212, '金'), '至寧': (1213, 1213, '金'), '貞祐': (1213, 1216, '金'),
    '興定': (1217, 1221, '金'), '元光': (1222, 1223, '金'), '正大': (1224, 1231, '金'),
    '開興': (1232, 1232, '金'), '天興': (1232, 1234, '金'),
    # ── Nguyên ──
    '中統': (1260, 1263, '元'), '至元': (1264, 1294, '元'), '元貞': (1295, 1296, '元'),
    '大德': (1297, 1307, '元'), '至大': (1308, 1311, '元'), '皇慶': (1312, 1313, '元'),
    '延祐': (1314, 1320, '元'), '至治': (1321, 1323, '元'), '泰定': (1324, 1327, '元'),
    '天曆': (1328, 1329, '元'), '至順': (1330, 1332, '元'), '元統': (1333, 1334, '元'),
    '至元': (1335, 1340, '元'),  # second Zhiyuan — overwrite fine (same dynasty)
    '至正': (1341, 1368, '元'),
    # ── Minh ──
    '洪武': (1368, 1398, '明'), '建文': (1399, 1402, '明'), '永樂': (1403, 1424, '明'),
    '洪熙': (1425, 1425, '明'), '宣德': (1426, 1435, '明'), '正統': (1436, 1449, '明'),
    '景泰': (1450, 1456, '明'), '天順': (1457, 1464, '明'), '成化': (1465, 1487, '明'),
    '弘治': (1488, 1505, '明'), '正德': (1506, 1521, '明'), '嘉靖': (1522, 1566, '明'),
    '隆慶': (1567, 1572, '明'), '萬曆': (1573, 1620, '明'), '泰昌': (1620, 1620, '明'),
    '天啟': (1621, 1627, '明'), '崇禎': (1628, 1644, '明'),
    # ── Thanh ──
    '順治': (1644, 1661, '清'), '康熙': (1662, 1722, '清'), '雍正': (1723, 1735, '清'),
    '乾隆': (1736, 1795, '清'), '嘉慶': (1796, 1820, '清'), '道光': (1821, 1850, '清'),
    '咸豐': (1851, 1861, '清'), '同治': (1862, 1874, '清'), '光緒': (1875, 1908, '清'),
    '宣統': (1909, 1911, '清'),
    # ── Dân Quốc ──
    '民國': (1912, 1949, '民'),
}

# Chinese number → integer
CN_NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
           '十':10,'百':100,'千':1000,
           '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,
           '十八':18,'十九':19,'二十':20,'二十一':21,'二十二':22,'二十三':23,
           '二十四':24,'二十五':25,'二十六':26,'二十七':27,'二十八':28,'二十九':29,
           '三十':30,'三十一':31,'三十二':32,'四十':40,'四十八':48,'五十':50,
           '五十二':52,'五十三':53,'六十':60,'六十一':61}

def parse_cn_year(s: str) -> int | None:
    """Parse Chinese ordinal year like '六', '三十八', '二十' to int."""
    s = s.strip()
    if not s:
        return None
    if s in CN_NUM:
        return CN_NUM[s]
    # Try multi-char: 十+single
    m = re.match(r'^([二三四五六七八九]?十)([一二三四五六七八九]?)$', s)
    if m:
        tens_char = m.group(1)
        ones_char = m.group(2)
        tens = {'十':1,'二十':2,'三十':3,'四十':4,'五十':5,'六十':6,'七十':7,'八十':8,'九十':9}.get(tens_char,1)
        ones = CN_NUM.get(ones_char, 0)
        return tens * 10 + ones
    # Arabic digits
    if re.match(r'^\d+$', s):
        return int(s)
    return None


# Renovation keywords → skip if adjacent to year
RENOVATION = re.compile(r'重[修建葺]|修繕|修復|新修|重葺|重刊|重塑|敕修|奉修')

# Founding keywords — must be in same clause as era name
FOUNDING_KW = re.compile(r'[建創立起始興造開]')

ERA_NAMES_SORTED = sorted(ERA_TABLE.keys(), key=len, reverse=True)  # longest first


def extract_year_from_era(note: str) -> tuple[int | None, str, str]:
    """
    Returns (year_ce, era_name, extraction_method).
    method: 'exact_year' | 'midpoint' | None
    """
    if not note:
        return None, '', ''

    for era in ERA_NAMES_SORTED:
        idx = note.find(era)
        if idx == -1:
            continue

        era_start, era_end, dynasty = ERA_TABLE[era]

        # Context: 30 chars around era name
        ctx_start = max(0, idx - 20)
        ctx_end = min(len(note), idx + len(era) + 25)
        ctx = note[ctx_start:ctx_end]

        # T32 fix: check renovation in CLAUSE, not ±20 char window
        clause_start = note.rfind('。', 0, idx)
        clause_start = clause_start + 1 if clause_start >= 0 else 0
        clause_end_m = note.find('。', idx)
        clause_end = clause_end_m if clause_end_m >= 0 else min(len(note), idx + 60)
        clause = note[clause_start:clause_end]

        # Skip if renovation keyword in the founding clause
        if RENOVATION.search(clause):
            continue
        if not FOUNDING_KW.search(clause):
            continue

        # Try to extract year number after era name
        # Pattern: era + (CN_num|Arabic) + 年
        after_era = note[idx + len(era):]
        m_year = re.match(
            r'^([元初中末]|[一二三四五六七八九十百千]+|\d+)年',
            after_era
        )
        if m_year:
            num_str = m_year.group(1)
            if num_str in ('中', '間', '末', '初'):
                # Approximate: midpoint
                mid = (era_start + era_end) // 2
                return mid, era, 'midpoint'
            elif num_str == '元':
                return era_start, era, 'exact_year'
            else:
                n = parse_cn_year(num_str)
                if n and 1 <= n <= (era_end - era_start + 2):
                    return era_start + (n - 1), era, 'exact_year'

        # No year number — check for 中/間 nearby
        after_era_15 = after_era[:15]
        if re.match(r'^[中間初末]', after_era_15):
            mid = (era_start + era_end) // 2
            return mid, era, 'midpoint'

        # Era name alone (e.g., "唐貞觀年間建" → just era range midpoint)
        m_nian = re.match(r'^年[間中]', after_era_15)
        if m_nian:
            mid = (era_start + era_end) // 2
            return mid, era, 'midpoint'

    return None, '', ''


def main():
    parser = argparse.ArgumentParser(description='DILA era name founding year extractor (T21)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    existing_tl = set(r[0] for r in conn.execute(
        "SELECT DISTINCT dila_id FROM place_timeline_events"
    ).fetchall())

    sql = """
        SELECT id, name_zh, note, note_category FROM places_dila
        WHERE note IS NOT NULL AND length(note) > 20
          AND note_category LIKE '%寺廟%'
    """
    if args.limit:
        sql += f" LIMIT {args.limit}"

    places = conn.execute(sql).fetchall()

    stats = {'examined': 0, 'found_exact': 0, 'found_mid': 0,
             'skip_existing': 0, 'skip_no_era': 0}
    rows_to_insert = []

    for (dila_id, name_zh, note, _) in places:
        stats['examined'] += 1
        if dila_id in existing_tl and not args.force:
            stats['skip_existing'] += 1
            continue

        year, era, method = extract_year_from_era(note)
        if year is None:
            stats['skip_no_era'] += 1
            continue

        if method == 'exact_year':
            stats['found_exact'] += 1
            conf = 'era_name_exact'
        else:
            stats['found_mid'] += 1
            conf = 'era_name_midpoint'

        dy = ERA_TABLE[era][2] if era in ERA_TABLE else ''
        era_start = ERA_TABLE[era][0] if era in ERA_TABLE else year
        label = f"{dy}{era} ({era_start}年建)" if method == 'exact_year' \
            else f"{dy}{era}中 ({era_start}-{ERA_TABLE.get(era,(0,year,''))[1]}年間)"
        label_full = (name_zh or '') + ' ' + label

        rows_to_insert.append({
            'dila_id': dila_id, 'year': year, 'label_zh': label_full.strip(),
            'source': 'dila_era_name', 'source_ref': f"{dila_id}·{era}·{conf}",
            'confidence': conf
        })

    print(f"Examined: {stats['examined']}")
    print(f"Already in timeline (skip): {stats['skip_existing']}")
    print(f"Era name not found: {stats['skip_no_era']}")
    print(f"Exact year found: {stats['found_exact']}")
    print(f"Midpoint (approximate): {stats['found_mid']}")
    print(f"Total would insert: {len(rows_to_insert)}")
    print()
    print("Sample (first 12):")
    for r in rows_to_insert[:12]:
        print(f"  {r['dila_id']} | year={r['year']} | {r['label_zh'][:60]} | {r['confidence']}")

    if args.dry_run:
        print("\n[DRY RUN — nothing written]")
        conn.close()
        return

    inserted = 0
    for r in rows_to_insert:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO place_timeline_events
                  (dila_id, event_type, year, label_zh, source, source_ref, confidence)
                VALUES (?, 'founding', ?, ?, ?, ?, ?)
            """, (r['dila_id'], r['year'], r['label_zh'],
                  r['source'], r['source_ref'], r['confidence']))
            inserted += 1
        except Exception as e:
            print(f"  Error {r['dila_id']}: {e}")

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM place_timeline_events").fetchone()[0]
    unique = conn.execute("SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events").fetchone()[0]
    by_src = conn.execute("""
        SELECT source, COUNT(*), COUNT(DISTINCT dila_id)
        FROM place_timeline_events GROUP BY source
    """).fetchall()

    print(f"\n✅ Inserted {inserted} rows.")
    print(f"Total: {total} rows / {unique} unique DILA places")
    by_src_total = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
    print(f"Coverage: {unique}/{by_src_total} = {unique*100/by_src_total:.2f}%")
    for r in by_src:
        print(f"  {r[0]}: {r[1]} rows / {r[2]} places")

    conn.close()


if __name__ == '__main__':
    main()

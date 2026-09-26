"""
dila_note_founding_extract.py — T21 Giai đoạn 2d: DILA note founding year extraction
======================================================================================
Trích năm thành lập từ trường `places_dila.note` (text xuôi tiếng Hán).

Chiến lược:
- Chỉ xử lý places có note_category chứa '寺廟' (Buddhist temple/pagoda).
- Pattern chính: （\d{3,4}）— năm CE trong ngoặc đơn fullwidth (phổ biến nhất DILA).
- Ưu tiên year gần keyword thành lập (建/創/立/起/始) trong ±30 ký tự.
- Nếu không có founding keyword → dùng năm đầu tiên đề cập.
- Bỏ qua: （\d{4}-\d{4}）(khoảng triều đại), năm > 2000, năm < 100 (không đáng tin).
- Skip if already has data in place_timeline_events.

Confidence: 'regex_note' — thấp hơn 'verified' (Wikidata).
Source: 'dila_note'.
Badge hiển thị: 'DILA note·regex'.

KHÔNG sửa bảng DILA. KHÔNG overwrite Wikidata data. Additive-only.

Cách dùng:
    python scripts/dila_note_founding_extract.py           # full run
    python scripts/dila_note_founding_extract.py --dry-run  # preview only
    python scripts/dila_note_founding_extract.py --limit 50 # test với 50 places
    python scripts/dila_note_founding_extract.py --force     # re-insert even if exists
"""
import sqlite3, re, sys, argparse, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = 'data/lineage.db'

# Founding keywords — trong 30 ký tự trước hoặc sau year
FOUNDING_KW = re.compile(r'[建創立起始興造開]')

# Renovation keywords — skip if adjacent to year
RENOVATION_KW = re.compile(r'重[修建葺]|修繕|修復|新修|重葺|敕修|賜[額名]|改[為名]')

# Person death keywords — skip (not place founding)
PERSON_DEATH_KW = re.compile(r'卒[於于]|圓寂|遷化|示寂|葬[於于]|終|歿')

# Primary pattern: fullwidth parentheses year （NNN）or （NNNN）
# Exclude ranges like （1368-1644）
YEAR_PAT = re.compile(r'（(\d{3,4})）')

# Secondary: halfwidth parentheses (less common in DILA)
YEAR_PAT_HW = re.compile(r'\((\d{3,4})\)')

# Filter out dynasty ranges
RANGE_PAT = re.compile(r'（\d{3,4}[-–]\d{3,4}）')

# Temple category keywords
TEMPLE_CATS = ['寺廟', '佛塔', '佛教文化地點']

# ─── Era name lookup table (年號 → {start, end, dynasty_zh}) ─────────────────
# Sorted longest-first to avoid partial matches (e.g. 大中祥符 before 大中)
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
    '元興': (105, 105, '漢'), '永初': (107, 113, '漢'),
    '永嘉': (145, 146, '漢'), '建安': (196, 219, '漢'),
    # ── Tam Quốc / Tây Tấn ──
    '黃初': (220, 226, '魏'), '景初': (237, 239, '魏'),
    '建興': (265, 274, '晉'), '太康': (280, 289, '晉'), '永熙': (290, 290, '晉'),
    '太安': (302, 303, '晉'),
    # ── Đông Tấn ──
    '太興': (318, 321, '晉'), '永昌': (322, 322, '晉'),
    '太寧': (323, 325, '晉'), '咸和': (326, 334, '晉'), '咸康': (335, 342, '晉'),
    '永和': (345, 356, '晉'), '升平': (357, 361, '晉'),
    '隆和': (362, 362, '晉'), '興寧': (363, 365, '晉'),
    '咸安': (371, 372, '晉'), '寧康': (373, 375, '晉'), '太元': (376, 396, '晉'),
    '隆安': (397, 401, '晉'), '義熙': (405, 418, '晉'),
    # ── Lưu Tống ──
    '景平': (423, 424, '宋'), '元嘉': (424, 453, '宋'),
    '孝建': (454, 456, '宋'), '大明': (457, 464, '宋'), '泰始': (465, 471, '宋'),
    '泰豫': (472, 472, '宋'), '昇明': (477, 479, '宋'),
    # ── Nam Tề ──
    '永明': (483, 493, '齊'), '隆昌': (494, 494, '齊'),
    '永泰': (498, 498, '齊'),
    '永元': (499, 501, '齊'), '中興': (501, 502, '齊'),
    # ── Lương ──
    '天監': (502, 519, '梁'), '普通': (520, 526, '梁'), '大通': (527, 528, '梁'),
    '中大通': (529, 534, '梁'), '大同': (535, 545, '梁'), '中大同': (546, 546, '梁'),
    '太清': (547, 549, '梁'), '大寶': (550, 551, '梁'), '承聖': (552, 554, '梁'),
    # ── Trần ──
    '永定': (557, 559, '陳'), '天嘉': (560, 565, '陳'), '天康': (566, 566, '陳'),
    '光大': (567, 568, '陳'), '太建': (569, 582, '陳'), '至德': (583, 586, '陳'),
    '禎明': (587, 589, '陳'),
    # ── Bắc Ngụy ──
    '景明': (500, 503, '魏'), '正始': (504, 507, '魏'),
    '熙平': (516, 517, '魏'), '神龜': (518, 519, '魏'),
    '正光': (520, 524, '魏'), '孝昌': (525, 527, '魏'), '永安': (528, 530, '魏'),
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
    '乾元': (758, 759, '唐'), '寶應': (762, 763, '唐'),
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
    # ── Kim ──
    '天輔': (1117, 1122, '金'), '天會': (1123, 1135, '金'), '天眷': (1138, 1140, '金'),
    '皇統': (1141, 1148, '金'), '天德': (1149, 1152, '金'),
    '正隆': (1156, 1161, '金'), '大定': (1161, 1189, '金'), '明昌': (1190, 1195, '金'),
    '承安': (1196, 1200, '金'), '泰和': (1201, 1208, '金'), '大安': (1209, 1211, '金'),
    '崇慶': (1212, 1212, '金'), '至寧': (1213, 1213, '金'), '貞祐': (1213, 1216, '金'),
    '興定': (1217, 1221, '金'), '正大': (1224, 1231, '金'),
    '開興': (1232, 1232, '金'), '天興': (1232, 1234, '金'),
    # ── Nguyên ──
    '中統': (1260, 1263, '元'), '至元': (1264, 1294, '元'), '元貞': (1295, 1296, '元'),
    '大德': (1297, 1307, '元'), '至大': (1308, 1311, '元'), '皇慶': (1312, 1313, '元'),
    '延祐': (1314, 1320, '元'), '至治': (1321, 1323, '元'), '泰定': (1324, 1327, '元'),
    '天曆': (1328, 1329, '元'), '至順': (1330, 1332, '元'), '元統': (1333, 1334, '元'),
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
    '民國': (1912, 1949, '民國'),
}

# Sort by length descending for longest-match-first
ERA_NAMES_SORTED = sorted(ERA_TABLE.keys(), key=len, reverse=True)

# Chinese numeral → int
_CN_DIGITS = {'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'一':1}
def _cn_to_int(cn: str) -> int | None:
    if not cn or cn in ('中', '間'):
        return None
    result = 0; current = 0
    for ch in cn:
        if ch == '十':
            result += current if current else 1; current = 0
        elif ch == '百':
            result += (current or 1) * 100; current = 0
        elif ch == '千':
            result += (current or 1) * 1000; current = 0
        elif ch in _CN_DIGITS:
            current = _CN_DIGITS[ch]
    result += current
    return result if result > 0 else None

# Era+year regex: era_name + regnal_year + 年
ERA_YEAR_PAT = re.compile(
    '(' + '|'.join(re.escape(e) for e in ERA_NAMES_SORTED) + ')'
    r'([一二三四五六七八九十百千]+年|中|間)'
)


def is_temple_category(cat: str | None) -> bool:
    if not cat:
        return False
    return any(kw in cat for kw in TEMPLE_CATS)


def extract_founding_year(note: str) -> tuple[int | None, str]:
    """
    Returns (year_ce, extraction_method).
    extraction_method: 'keyword_context' | 'first_year' | 'era_year' | None
    """
    if not note:
        return None, ''

    # Remove ranges first to avoid false matches
    note_clean = RANGE_PAT.sub('', note)

    # ── TIER 1: Parenthesized CE years (highest confidence) ──
    matches = list(YEAR_PAT.finditer(note_clean))
    if not matches:
        matches = list(YEAR_PAT_HW.finditer(note_clean))
    if matches:
        valid = [(m, int(m.group(1))) for m in matches if 100 <= int(m.group(1)) <= 1950]
        # Prefer year with founding keyword in ±12 chars context
        for m, year in valid:
            start = max(0, m.start() - 12)
            end = min(len(note_clean), m.end() + 12)
            context = note_clean[start:end]
            if not FOUNDING_KW.search(context):
                continue
            before = note_clean[start:m.start()]
            after = note_clean[m.end():end]
            if re.search(r'[。；\n]', before + after):
                continue
            if RENOVATION_KW.search(context):
                continue
            return year, 'keyword_context'

        # Fallback: first valid year without renovation
        for m, year in valid:
            before = note_clean[max(0, m.start() - 30):m.start()]
            if RENOVATION_KW.search(before):
                continue
            note_before_year = note_clean[:m.start()]
            sentence_splits = list(re.finditer(r'[。；]', note_before_year))
            # T32 fix: only skip if RENOVATION keyword in previous sentence
            if sentence_splits and RENOVATION_KW.search(note_before_year[:sentence_splits[-1].start()]):
                continue
            return year, 'first_year'

    # ── TIER 2: Era name + regnal year → CE (T32 enhancement) ──
    for m in ERA_YEAR_PAT.finditer(note_clean):
        era = m.group(1)
        yr_str = m.group(2)
        era_info = ERA_TABLE.get(era)
        if not era_info:
            continue

        # Check ±20 chars context for death keywords
        ctx_start = max(0, m.start() - 20)
        ctx_end = min(len(note_clean), m.end() + 20)
        context = note_clean[ctx_start:ctx_end]

        # Skip if person death keywords adjacent (卒/圓寂/葬)
        if PERSON_DEATH_KW.search(note_clean[max(0, m.start() - 30):m.end() + 10]):
            continue

        # T32 fix: check renovation in CLAUSE, not ±20 char window
        clause_s = note_clean.rfind('。', 0, m.start())
        clause_s = clause_s + 1 if clause_s >= 0 else 0
        clause_e_m = note_clean.find('。', m.end())
        clause_e = clause_e_m if clause_e_m >= 0 else min(len(note_clean), m.end() + 60)
        clause = note_clean[clause_s:clause_e]
        if RENOVATION_KW.search(clause):
            continue

        yr_num = _cn_to_int(yr_str)
        if yr_num:
            ce_year = era_info[0] + yr_num - 1
        else:
            # 中/間 → midpoint
            ce_year = (era_info[0] + era_info[1]) // 2

        # Validate CE year range
        if not (100 <= ce_year <= 1950):
            continue

        # Check for founding keyword within broader context (±40 chars)
        broad_ctx = note_clean[max(0, m.start() - 40):min(len(note_clean), m.end() + 40)]
        # Lower bar: era+year in first sentence is usually founding context
        # T32 fix: only skip if RENOVATION keyword in previous sentence (not just founding keyword)
        before_era = note_clean[:m.start()]
        last_sentence = max(before_era.rfind('。'), before_era.rfind('；'), before_era.rfind('\n'))
        if last_sentence >= 0:
            pre_sentence = before_era[:last_sentence]
            if RENOVATION_KW.search(pre_sentence):
                continue

        return ce_year, 'era_year'

    return None, ''


def extract_note_snippet(note: str, year: int, method: str = '') -> str:
    """Extract a short snippet around the year mention for label_zh."""
    # Try parenthesized CE year first
    pat = re.compile(r'（' + str(year) + r'）')
    m = pat.search(note)
    if m:
        start = max(0, m.start() - 20)
        end = min(len(note), m.end() + 10)
        snippet = note[start:end].strip()
        snippet = re.sub(r'[（\(]+$', '', snippet).strip()
        return snippet[:80]

    # For era_year method: find the era name match and extract context
    if method == 'era_year':
        for m in ERA_YEAR_PAT.finditer(note):
            era = m.group(1)
            yr_str = m.group(2)
            era_info = ERA_TABLE.get(era)
            if not era_info:
                continue
            yr_num = _cn_to_int(yr_str)
            if yr_num:
                ce = era_info[0] + yr_num - 1
            else:
                ce = (era_info[0] + era_info[1]) // 2
            if ce == year:
                start = max(0, m.start() - 15)
                end = min(len(note), m.end() + 15)
                snippet = note[start:end].strip()
                return snippet[:80]
    return ''


def main():
    parser = argparse.ArgumentParser(description='DILA note founding year extractor (T21)')
    parser.add_argument('--dry-run', action='store_true', help='Preview, no DB writes')
    parser.add_argument('--limit', type=int, default=0, help='Limit places processed (0=all)')
    parser.add_argument('--force', action='store_true',
                        help='Re-insert even if dila_id already in place_timeline_events')
    parser.add_argument('--min-confidence', default='regex_note',
                        help='Confidence tag for inserted rows (default: regex_note)')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Existing timeline places (to skip if not --force)
    existing_timeline = set(
        r[0] for r in conn.execute(
            "SELECT DISTINCT dila_id FROM place_timeline_events"
        ).fetchall()
    )

    # Query temple places with note
    sql = """
        SELECT id, name, name_zh, note, note_category
        FROM places_dila
        WHERE note IS NOT NULL AND length(note) > 20
    """
    if args.limit:
        sql += f" LIMIT {args.limit}"

    places = conn.execute(sql).fetchall()
    total = len(places)
    print(f"Processing {total} DILA places with notes...")

    stats = {
        'examined': 0,
        'temple_cat': 0,
        'year_found': 0,
        'keyword_context': 0,
        'first_year_fallback': 0,
        'era_year': 0,
        'inserted': 0,
        'skipped_existing': 0,
        'skipped_no_year': 0,
        'skipped_non_temple': 0,
    }

    rows_to_insert = []

    for (dila_id, name, name_zh, note, note_cat) in places:
        stats['examined'] += 1

        if not is_temple_category(note_cat):
            stats['skipped_non_temple'] += 1
            continue
        stats['temple_cat'] += 1

        if dila_id in existing_timeline and not args.force:
            stats['skipped_existing'] += 1
            continue

        year, method = extract_founding_year(note)
        if year is None:
            stats['skipped_no_year'] += 1
            continue

        stats['year_found'] += 1
        if method == 'keyword_context':
            stats['keyword_context'] += 1
        elif method == 'era_year':
            stats['era_year'] += 1
        else:
            stats['first_year_fallback'] += 1

        snippet = extract_note_snippet(note, year, method)
        label_zh = snippet if snippet else (name_zh or name or '')

        rows_to_insert.append((
            dila_id, year, label_zh, 'dila_note',
            f"{dila_id}·note·regex", args.min_confidence
        ))

    print(f"\nExtraction results:")
    print(f"  Examined: {stats['examined']}")
    print(f"  Temple category: {stats['temple_cat']}")
    print(f"  Already in timeline (skipped): {stats['skipped_existing']}")
    print(f"  Year found: {stats['year_found']}")
    print(f"    Via keyword context: {stats['keyword_context']}")
    print(f"    Via first-year fallback: {stats['first_year_fallback']}")
    print(f"  No year found: {stats['skipped_no_year']}")

    # Sample preview
    print(f"\nSample extractions (first 10):")
    for r in rows_to_insert[:10]:
        label_preview = r[2][:50] if r[2] else ''
        print(f"  {r[0]} | year={r[1]} | {label_preview} | {r[4]}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would insert {len(rows_to_insert)} rows into place_timeline_events.")
        conn.close()
        return

    # Insert
    inserted = 0
    for (dila_id, year, label_zh, source, source_ref, confidence) in rows_to_insert:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO place_timeline_events
                  (dila_id, event_type, year, label_zh, source, source_ref, confidence)
                VALUES (?, 'founding', ?, ?, ?, ?, ?)
            """, (dila_id, year, label_zh, source, source_ref, confidence))
            inserted += 1
        except Exception as e:
            print(f"  Insert error {dila_id}: {e}")

    conn.commit()
    stats['inserted'] = inserted

    # Final state
    total_tl = conn.execute("SELECT COUNT(*) FROM place_timeline_events").fetchone()[0]
    total_dila = conn.execute("SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events").fetchone()[0]
    by_source = conn.execute("""
        SELECT source, COUNT(*), COUNT(DISTINCT dila_id)
        FROM place_timeline_events GROUP BY source
    """).fetchall()

    print(f"\n✅ Inserted {inserted} rows.")
    print(f"\n=== place_timeline_events final state ===")
    print(f"  Total rows: {total_tl}, unique DILA places: {total_dila}")
    print(f"  By source:")
    for r in by_source:
        print(f"    {r[0]}: {r[1]} rows, {r[2]} places")

    conn.close()


if __name__ == '__main__':
    main()

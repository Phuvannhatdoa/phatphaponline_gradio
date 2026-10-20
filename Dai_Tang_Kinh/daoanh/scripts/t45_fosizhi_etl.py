"""
T45 — DILA Fosi Zhi Structured Dates ETL  v2
Download TEI XML archives, extract founding dates from classical Chinese text.
Dates are embedded as reign-era references (e.g. 元和十四年) near founding keywords.
Matches with places_dila → insert into place_timeline_events.

Usage:
  python scripts/t45_fosizhi_etl.py              # dry-run all 9
  python scripts/t45_fosizhi_etl.py --insert     # insert confirmed candidates
  python scripts/t45_fosizhi_etl.py --gid g026   # single gazetteer dry-run
"""
import sys, io, os, re, ssl, zipfile, sqlite3, json, argparse, time, urllib.request
from xml.etree import ElementTree as ET
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.join(os.path.dirname(__file__), '..')
DB   = os.path.join(BASE, 'data', 'lineage.db')
CACHE_DIR = os.path.join(BASE, 'data', 't45_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

FOSIZHI_BASE = 'https://buddhistinformatics.dila.edu.tw/fosizhi/archives/'

# 9 gazetteers with full TEI text (bibl type="Ms")
GAZETTEERS = {
    'g004': 'g004_luoyangqielanjihejiaoben.zip',
    'g026': 'g026_hupaodinghuisizhi.zip',
    'g036': 'g036_changshouxianposhanxingfusizhi.zip',
    'g072': 'g072_lingyanjilue.zip',
    'g073': 'g073_lingyanzhilue.zip',
    'g093': 'g093_cuishansizhi.zip',
    'g094': 'g094_qingyuanzhilue.zip',
    'g097': 'g097_wudufasheng.zip',
    'g100': 'g100_qingliangshanxinzhi.zip',
}

# Known DILA ID for main temple of single-temple gazetteers
# Verified against places_dila.name_zh
GAZETTEER_MAIN_DILA_ID = {
    'g026': None,  # 虎跑定慧寺 — lookup by name
    'g036': None,  # 興福寺 (常熟) — lookup by name
    'g072': None,  # 靈巖山寺 (蘇州) — lookup by name
    'g073': None,  # 靈巖山寺 (蘇州) — same as g072
    'g093': None,  # 翠山寺 — lookup by name
    'g094': None,  # 青原山淨居寺 — lookup by name
    'g004': None,  # multi-temple: 洛陽
    'g097': None,  # multi-temple: 吳都 (Suzhou region)
    'g100': None,  # multi-temple: 五台山
}

GAZETTEER_MAIN_NAME_ZH = {
    'g026': '定慧寺',
    'g036': '興福寺',
    'g072': '靈巖山寺',
    'g073': '靈巖山寺',
    'g093': '翠山寺',
    'g094': '淨居寺',
}

# Founding / renovation keywords
FOUNDING_KW = re.compile(r'創建|始建|敕建|建院|建寺|立寺|開山|草創|創立|初建|建於|肇建|創設|結菴|結庵|(?<!泉號)卓錫')
RENOVATION_KW = re.compile(r'重[修建葺]|重建|修繕|重修|修復|增建|擴建|重興')

# Chinese numeral → int  ('元' = 1 for 元年 usage)
CN_NUM = {'元':1,'〇':0,'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,
          '六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'千':1000}

# Reign-era start years (CE) — comprehensive lookup for Buddhist historical dates
# Source: standard Chinese historical chronology
ERA_START = {
    # Han
    '建元': 140, '元光': 134, '元朔': 128, '元狩': 122, '元鼎': 116,
    '元封': 110, '太初': 104, '天漢': 98, '太始': 96, '征和': 92,
    '後元': 88, '始元': 86, '元鳳': 80, '元平': 74, '本始': 73,
    '地節': 69, '元康': 65, '神爵': 61, '五鳳': 57, '甘露': 53,
    '黃龍': 49, '初元': 48, '永光': 43, '建昭': 38, '竟寧': 33,
    '建始': 32, '河平': 28, '陽朔': 24, '鴻嘉': 20, '永始': 16,
    '元延': 12, '綏和': 8, '建平': 6, '元壽': 2,
    '元始': 1, '居攝': 6, '初始': 8,
    # Eastern Han
    '建武': 25, '建武中元': 56, '永平': 58, '建初': 76, '元和': 84,
    '章和': 87, '永元': 89, '元興': 105, '延平': 106, '永初': 107,
    '元初': 114, '永寧': 120, '建光': 121, '延光': 122, '永建': 126,
    '陽嘉': 132, '永和': 136, '漢安': 142, '建康': 144, '永嘉': 145,
    '元嘉': 151, '永興': 153, '永壽': 155, '延熹': 158, '永康': 167,
    '建寧': 168, '熹平': 172, '光和': 178, '中平': 184, '光熹': 189,
    '昭寧': 189, '永漢': 189, '初平': 190, '興平': 194, '建安': 196,
    '延康': 220,
    # Three Kingdoms
    '黃初': 220, '太和': 227, '青龍': 233, '景初': 237,
    '嘉平': 249, '正始': 240,
    # Western Jin
    '泰始': 265, '咸寧': 275, '太康': 280, '太熙': 290,
    '永熙': 290, '永平': 291, '元康': 291, '永康': 300, '永寧': 301,
    '太安': 302, '永安': 304, '建興': 313, '建平': 317,
    # Eastern Jin
    '太興': 318, '永昌': 322, '太寧': 323, '咸和': 326, '咸康': 335,
    '建元': 343, '永和': 345, '升平': 357, '隆和': 362, '興寧': 363,
    '太和': 366, '咸安': 371, '寧康': 373, '太元': 376, '隆安': 397,
    '元興': 402, '義熙': 405, '元熙': 419,
    # Liu Song
    '永初': 420, '景平': 423, '元嘉': 424, '孝建': 454, '大明': 457,
    '泰始': 465, '泰豫': 472, '元徽': 473, '昇明': 477,
    # Southern Qi
    '建元': 479, '永明': 483, '隆昌': 494, '延興': 494, '建武': 494,
    '永泰': 498, '永元': 499, '中興': 501,
    # Liang
    '天監': 502, '普通': 520, '大通': 527, '中大通': 529, '大同': 535,
    '中大同': 546, '太清': 547, '大寶': 550, '天正': 551, '承聖': 552,
    '天成': 555, '紹泰': 555, '太平': 556,
    # Chen
    '永定': 557, '天嘉': 560, '天康': 566, '光大': 567, '太建': 569,
    '至德': 583, '禎明': 587,
    # Northern Wei / Northern Qi / Northern Zhou
    '登國': 386, '皇始': 396, '天興': 398, '天賜': 404, '永興': 409,
    '神瑞': 414, '泰常': 416, '始光': 424, '神麚': 428, '延和': 432,
    '太延': 435, '太平真君': 440, '正平': 451, '興安': 452, '興光': 454,
    '太安': 455, '和平': 460, '天安': 466, '皇興': 467, '延興': 471,
    '承明': 476, '太和': 477, '景明': 500, '正始': 504, '永平': 508,
    '延昌': 512, '熙平': 516, '神龜': 518, '正光': 520, '孝昌': 525,
    '武泰': 528, '建義': 528, '永安': 528, '普泰': 531, '中興': 531,
    '太昌': 532, '永興': 532, '永熙': 532, '天平': 534, '元象': 538,
    '興和': 539, '武定': 543, '天保': 550, '乾明': 560, '皇建': 560,
    '太寧': 561, '河清': 562, '天統': 565, '武平': 570, '隆化': 576,
    '武成': 559, '保定': 561, '天和': 566, '建德': 572, '宣政': 578,
    '大象': 579, '大定': 581,
    # Sui
    '開皇': 581, '仁壽': 601, '大業': 605, '義寧': 617,
    # Tang
    '武德': 618, '貞觀': 627, '永徽': 650, '顯慶': 656, '龍朔': 661,
    '麟德': 664, '乾封': 666, '總章': 668, '咸亨': 670, '上元': 674,
    '儀鳳': 676, '調露': 679, '永隆': 680, '開耀': 681, '永淳': 682,
    '弘道': 683, '嗣聖': 684, '文明': 684, '光宅': 684, '垂拱': 685,
    '永昌': 689, '載初': 690, '天授': 690, '如意': 692, '長壽': 692,
    '延載': 694, '證聖': 695, '天冊萬歲': 695, '萬歲登封': 696,
    '萬歲通天': 696, '神功': 697, '聖曆': 698, '久視': 700, '大足': 701,
    '長安': 701, '神龍': 705, '景龍': 707, '唐隆': 710, '景雲': 710,
    '太極': 712, '延和': 712, '先天': 712, '開元': 713, '天寶': 742,
    '至德': 756, '乾元': 758, '上元': 760, '寶應': 762, '廣德': 763,
    '永泰': 765, '大曆': 766, '建中': 780, '興元': 784, '貞元': 785,
    '永貞': 805, '元和': 806, '長慶': 821, '寶曆': 825, '大和': 827,
    '開成': 836, '會昌': 841, '大中': 847, '咸通': 860, '乾符': 874,
    '廣明': 880, '中和': 881, '光啟': 885, '文德': 888, '龍紀': 889,
    '大順': 890, '景福': 892, '乾寧': 894, '光化': 898, '天復': 901,
    '天祐': 904,
    # Five Dynasties
    '開平': 907, '乾化': 911, '貞明': 915, '龍德': 921,
    '同光': 923, '天成': 926, '長興': 930, '應順': 934, '清泰': 934,
    '天福': 936, '開運': 944, '天福': 947, '乾祐': 948,
    '廣順': 951, '顯德': 954,
    # Song
    '建隆': 960, '乾德': 963, '開寶': 968, '太平興國': 976, '雍熙': 984,
    '端拱': 988, '淳化': 990, '至道': 995, '咸平': 998, '景德': 1004,
    '大中祥符': 1008, '天禧': 1017, '乾興': 1022, '天聖': 1023, '明道': 1032,
    '景祐': 1034, '寶元': 1038, '康定': 1040, '慶曆': 1041, '皇祐': 1049,
    '至和': 1054, '嘉祐': 1056, '治平': 1064, '熙寧': 1068, '元豐': 1078,
    '元祐': 1086, '紹聖': 1094, '元符': 1098, '建中靖國': 1101, '崇寧': 1102,
    '大觀': 1107, '政和': 1111, '重和': 1118, '宣和': 1119, '靖康': 1126,
    # Southern Song
    '建炎': 1127, '紹興': 1131, '隆興': 1163, '乾道': 1165, '淳熙': 1174,
    '紹熙': 1190, '慶元': 1195, '嘉泰': 1201, '開禧': 1205, '嘉定': 1208,
    '寶慶': 1225, '紹定': 1228, '端平': 1234, '嘉熙': 1237, '淳祐': 1241,
    '寶祐': 1253, '開慶': 1259, '景定': 1260, '咸淳': 1265, '德祐': 1275,
    '景炎': 1276, '祥興': 1278,
    # Yuan
    '至元': 1264, '至元': 1335, '中統': 1260, '至正': 1341, '至大': 1308,
    '皇慶': 1312, '延祐': 1314, '至治': 1321, '泰定': 1324, '致和': 1328,
    '天曆': 1328, '至順': 1330,
    # Ming
    '洪武': 1368, '建文': 1399, '永樂': 1403, '洪熙': 1425, '宣德': 1426,
    '正統': 1436, '景泰': 1450, '天順': 1457, '成化': 1465, '弘治': 1488,
    '正德': 1506, '嘉靖': 1522, '隆慶': 1567, '萬曆': 1573, '泰昌': 1620,
    '天啟': 1621, '崇禎': 1628,
    # Qing
    '順治': 1644, '康熙': 1662, '雍正': 1723, '乾隆': 1736, '嘉慶': 1796,
    '道光': 1821, '咸豐': 1851, '同治': 1862, '光緒': 1875, '宣統': 1909,
}

TEI_NS = 'http://www.tei-c.org/ns/1.0'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def download_zip(gid, filename):
    cache_path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(cache_path):
        print(f'  [cache] {filename}')
        return cache_path
    url = FOSIZHI_BASE + filename
    print(f'  Downloading {url} ...', end=' ', flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'PTDA-T45/1.0 (academic research)'})
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
            data = r.read()
        with open(cache_path, 'wb') as f:
            f.write(data)
        print(f'OK ({len(data)//1024:,} KB)')
        return cache_path
    except Exception as e:
        print(f'FAIL: {e}')
        return None


def extract_xml_from_zip(zip_path, gid):
    """Extract only .tei.xml file from ZIP."""
    xml_files = {}
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.tei.xml'):
                    try:
                        xml_files[name] = zf.read(name).decode('utf-8', errors='replace')
                    except Exception:
                        pass
    except Exception as e:
        print(f'  ZIP error: {e}')
    return xml_files


def cn_numeral_to_int(s):
    """Convert Chinese numerals like 十四, 二十六, 三百 to integer."""
    if not s:
        return None
    # Try direct Arabic digit first
    if s.isdigit():
        return int(s)
    result = 0
    temp = 0
    i = 0
    while i < len(s):
        c = s[i]
        v = CN_NUM.get(c)
        if v is None:
            return None
        if v == 100 or v == 1000:
            if temp == 0:
                temp = 1
            result += temp * v
            temp = 0
        elif v == 10:
            if temp == 0:
                temp = 1
            result += temp * v
            temp = 0
        else:
            temp = v
        i += 1
    result += temp
    return result if result > 0 else None


def era_year_to_ce(era_name, year_str):
    """Convert Chinese reign-era year reference to CE year."""
    start = ERA_START.get(era_name)
    if start is None:
        return None
    n = cn_numeral_to_int(year_str)
    if n is None:
        return None
    return start + n - 1


def extract_dates_from_text(text, gid):
    """
    Extract founding dates from whitespace-collapsed plain text.
    Year must be within PROXIMITY chars of a founding keyword (not renovation).
    """
    PROXIMITY = 80  # chars between era-year and founding keyword
    candidates = []

    def _find_temple_before(pos, window_size=200):
        """Find last temple-name pattern before position pos."""
        pre = text[max(0, pos-window_size): pos]
        hits = list(re.finditer(r'([^\s,，。；：、「」\[\]]{2,12}(?:寺|院|庵|塔|堂|閣|觀|精舍))', pre))
        return hits[-1].group(1) if hits else ''

    # Strategy A: find all era-year patterns, then check proximity to founding kw
    for era_name in ERA_START:
        pat = re.escape(era_name) + r'([元〇零一二三四五六七八九十百千\d]{1,5})年'
        for m in re.finditer(pat, text):
            ce_year = era_year_to_ce(era_name, m.group(1))
            if not ce_year or not (100 <= ce_year <= 2000):
                continue
            start = max(0, m.start() - PROXIMITY)
            end = min(len(text), m.end() + PROXIMITY)
            window = text[start:end]
            if not FOUNDING_KW.search(window):
                continue
            has_renovation = bool(RENOVATION_KW.search(window))
            candidates.append({
                'gid': gid,
                'year': ce_year,
                'year_raw': f'{era_name}{m.group(1)}年',
                'context': text[max(0, m.start()-60): m.end()+100],
                'temple_name': _find_temple_before(m.start()),
                'has_founding': True,
                'has_renovation': has_renovation,
                'method': 'era_name',
                'confidence_flag': 'founding' if not has_renovation else 'renovation'
            })

    # Strategy B: parenthetical Western years （YYYY） near founding keywords
    for m in re.finditer(r'[（(](\d{3,4})[）)]', text):
        year = int(m.group(1))
        if not (100 <= year <= 2000):
            continue
        start = max(0, m.start() - PROXIMITY)
        end = min(len(text), m.end() + PROXIMITY)
        window = text[start:end]
        if not FOUNDING_KW.search(window):
            continue
        has_renovation = bool(RENOVATION_KW.search(window))
        candidates.append({
            'gid': gid,
            'year': year,
            'year_raw': m.group(),
            'context': text[max(0, m.start()-60): m.end()+100],
            'temple_name': _find_temple_before(m.start()),
            'has_founding': True,
            'has_renovation': has_renovation,
            'method': 'western_paren',
            'confidence_flag': 'founding' if not has_renovation else 'renovation'
        })

    # Deduplicate by year
    seen = set()
    deduped = []
    for c in candidates:
        if c['year'] not in seen:
            seen.add(c['year'])
            deduped.append(c)
    return deduped


def get_tei_text(xml_content):
    """Extract plain text from TEI XML body, normalizing whitespace."""
    try:
        root = ET.fromstring(xml_content.encode('utf-8'))
        body = root.find(f'.//{{{TEI_NS}}}body')
        if body is None:
            body = root
        raw = ET.tostring(body, encoding='unicode', method='text')
    except ET.ParseError:
        raw = xml_content
    # Collapse all whitespace (strips <lb/> artifacts, newlines, etc.)
    return re.sub(r'\s+', '', raw)


def load_dila_places(conn):
    """Load temple places from places_dila."""
    rows = conn.execute(
        "SELECT id, name_zh FROM places_dila WHERE note_category LIKE '%寺廟%' AND name_zh IS NOT NULL"
    ).fetchall()
    by_name = {}
    for row in rows:
        by_name[row[1]] = row[0]
    return by_name


def match_temple_to_dila(temple_name, dila_places):
    """Match extracted temple name to DILA place (exact → partial → 3-char core)."""
    if not temple_name or len(temple_name) < 2:
        return None, 'no_name'
    if temple_name in dila_places:
        return dila_places[temple_name], 'exact'
    for name_zh, pid in dila_places.items():
        if temple_name in name_zh and len(temple_name) >= 3:
            return pid, 'partial'
    if len(temple_name) >= 3:
        core = temple_name[:3]
        for name_zh, pid in dila_places.items():
            if core in name_zh:
                return pid, 'core3'
    return None, 'no_match'


def resolve_gazetteer_dila_id(gid, dila_places):
    """For single-temple gazetteers, find DILA ID by main temple name."""
    main_name = GAZETTEER_MAIN_NAME_ZH.get(gid)
    if not main_name:
        return None, 'multi_temple'
    # Exact match
    if main_name in dila_places:
        return dila_places[main_name], 'exact'
    # Partial match
    for name_zh, pid in dila_places.items():
        if main_name in name_zh or name_zh in main_name:
            return pid, 'partial'
    return None, 'no_match'


def check_existing(conn, dila_id, year):
    row = conn.execute(
        "SELECT id FROM place_timeline_events WHERE dila_id=? AND event_type='founding' AND year=?",
        (dila_id, year)
    ).fetchone()
    return row is not None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--insert', action='store_true')
    parser.add_argument('--gid', help='Single gazetteer ID')
    args = parser.parse_args()

    conn = sqlite3.connect(DB)
    dila_places = load_dila_places(conn)
    print(f'Loaded {len(dila_places):,} temple places from DILA')

    to_process = {args.gid: GAZETTEERS[args.gid]} if args.gid else GAZETTEERS
    all_candidates = []

    for gid, filename in to_process.items():
        print(f'\n=== {gid}: {filename} ===')

        # Resolve DILA ID for this gazetteer
        dila_id, match_type = resolve_gazetteer_dila_id(gid, dila_places)
        if match_type == 'multi_temple':
            print(f'  Multi-temple gazetteer — extracting per-temple dates (best effort)')
        elif dila_id:
            print(f'  Main temple: DILA {dila_id} ({match_type})')
        else:
            print(f'  Warning: no DILA ID found for {GAZETTEER_MAIN_NAME_ZH.get(gid)}')

        zip_path = download_zip(gid, filename)
        if not zip_path:
            continue

        xml_files = extract_xml_from_zip(zip_path, gid)
        if not xml_files:
            print(f'  No TEI XML found in {filename}')
            continue

        for fname, content in xml_files.items():
            text = get_tei_text(content)
            candidates = extract_dates_from_text(text, gid)
            print(f'  {fname}: {len(candidates)} founding date candidates')
            for c in candidates:
                c['dila_id'] = dila_id
                c['dila_match_type'] = match_type
            all_candidates.extend(candidates)

        time.sleep(0.3)

    # Filter: founding only, deduplicate across gazetteers
    print(f'\n=== RESULTS ({len(all_candidates)} raw candidates) ===')

    # For multi-temple gazetteers: assign dila_id by matching temple_name to DILA
    for c in all_candidates:
        if c.get('dila_id'):
            continue  # already set for single-temple
        temple = c.get('temple_name', '')
        if temple:
            dila_id, match_type = match_temple_to_dila(temple, dila_places)
            if dila_id:
                c['dila_id'] = dila_id
                c['dila_match_type'] = match_type

    # Keep only the EARLIEST year per DILA ID (founding happened once)
    by_dila = {}
    for c in all_candidates:
        if c['confidence_flag'] != 'founding':
            continue
        if not c.get('dila_id'):
            continue
        dila_id = c['dila_id']
        if dila_id not in by_dila or c['year'] < by_dila[dila_id]['year']:
            by_dila[dila_id] = c

    final = []
    for dila_id, c in by_dila.items():
        already = check_existing(conn, dila_id, c['year'])
        c['already_exists'] = already
        final.append(c)

    new_rows = [c for c in final if not c['already_exists']]
    print(f'Founding candidates: {len(final)} unique (new: {len(new_rows)}, existing: {len(final)-len(new_rows)})')
    print()

    for c in final:
        status = 'EXISTS' if c['already_exists'] else 'NEW  '
        print(f"[{status}] {c['gid']:5s} year={c['year']} raw={c['year_raw']!r:25s} "
              f"dila={c['dila_id']} ({c['dila_match_type']}) method={c['method']}")
        if not c['already_exists']:
            ctx_snip = re.sub(r'\s+', ' ', c['context'][:120])
            print(f"         {ctx_snip!r}")

    # Save raw
    raw_path = os.path.join(BASE, 'data', 't45_fosizhi_raw.json')
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(all_candidates, f, ensure_ascii=False, indent=2)
    print(f'\nRaw saved: {raw_path}')

    if not args.insert:
        print(f'\n[DRY-RUN] Would insert {len(new_rows)} rows into place_timeline_events.')
        print('Run with --insert to proceed.')
        conn.close()
        return

    # Backup + insert
    import shutil
    bak = os.path.join(BASE, 'docs', 'sessions',
                       f'T45_pre_insert_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db.bak')
    os.makedirs(os.path.dirname(bak), exist_ok=True)
    shutil.copy2(DB, bak)
    print(f'Backup: {bak}')

    inserted = 0
    for c in new_rows:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO place_timeline_events
                  (dila_id, event_type, year, source, source_ref, confidence, label_zh)
                VALUES (?, 'founding', ?, 'dila_fosizhi', ?, 0.85, ?)
            """, (
                c['dila_id'], c['year'],
                f"{c['gid']}·{c['method']}·{c['year_raw']}",
                c['year_raw']
            ))
            inserted += 1
        except Exception as e:
            print(f'  Insert error: {e}')

    conn.commit()
    conn.close()
    print(f'\n✅ Inserted {inserted} rows (source=dila_fosizhi, confidence=0.85)')


if __name__ == '__main__':
    main()

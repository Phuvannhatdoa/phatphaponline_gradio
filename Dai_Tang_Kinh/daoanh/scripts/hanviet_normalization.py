#!/usr/bin/env python3
"""
Hán–Việt Normalization Layer (Đạo Ảnh).

Fully local (no external API calls).
Loads glossary from lineage.db + built-in common Buddhist name mappings.
"""
import sqlite3
import re
from pathlib import Path
from functools import lru_cache

SCRIPT_DIR = Path(__file__).parent.parent.resolve()
DB_PATH = str(SCRIPT_DIR / 'data' / 'lineage.db')

# Common English/Pinyin → Hán-Việt for Buddhist context
# These are forms Google Translate hallucinates most often
FIXED_GLOSSARY_EN = {
    # Proper place names (≥5 chars or compound) — safe for word-boundary replace
    'shaolin temple': 'Thiếu Lâm Tự',
    'baima temple': 'Bạch Mã Tự',
    'famen temple': 'Pháp Môn Tự',
    'lingyin temple': 'Linh Ẩn Tự',
    'chongsheng temple': 'Chung Thánh Tự',
    'great cloud temple': 'Đại Vân Tự',
    'jade spring temple': 'Ngọc Tuyền Tự',
    'golden light temple': 'Kim Quang Tự',
    'white horse temple': 'Bạch Mã Tự',
    'southern mountain': 'Nam Sơn',
    'northern mountain': 'Bắc Sơn',
    'eastern mountain': 'Đông Sơn',
    'western mountain': 'Tây Sơn',
    'central mountain': 'Trung Sơn',
    'central plains': 'Trung Nguyên',
    'western capital': 'Tây Kinh',
    'eastern capital': 'Đông Kinh',
    'three kingdoms': 'Tam Quốc',
    'pure land': 'Tịnh Độ',
    'great master': 'Đại Sư',
    'grand master': 'Đại Sư',
    'patriarch master': 'Tổ Sư',
    'dharma master': 'Pháp Sư',
    'vinaya master': 'Luật Sư',
    'meditation master': 'Thiền Sư',
    'abdhidharma': 'A Tỳ Đạt Ma',
    'hui neng': 'Huệ Năng',
    'shih-tou': 'Thạch Đầu',
    'shih tou': 'Thạch Đầu',
    'northern and southern': 'Nam Bắc Triều',
    'spring and autumn': 'Xuân Thu',
    'warring states': 'Chiến Quốc',
    # Multi-syllable place names (safe)
    'changan': 'Trường An',
    "chang'an": 'Trường An',
    'shaolin': 'Thiếu Lâm',
    'jingde': 'Cảnh Đức',
    'kuaiji': 'Cối Kê',
    'luoyang': 'Lạc Dương',
    'kaifeng': 'Khai Phong',
    'nanjing': 'Nam Kinh',
    'beijing': 'Bắc Kinh',
    'hangzhou': 'Hàng Châu',
    'chengdu': 'Thành Đô',
    'taiyuan': 'Thái Nguyên',
    'guangzhou': 'Quảng Châu',
    'suzhou': 'Tô Châu',
    'yangzhou': 'Dương Châu',
    'shanxi': 'Sơn Tây',
    'shaanxi': 'Thểm Tây',
    'henan': 'Hà Nam',
    'hunan': 'Hồ Nam',
    'hubei': 'Hồ Bắc',
    'shandong': 'Sơn Đông',
    'zhejiang': 'Chiết Giang',
    'jiangxi': 'Giang Tây',
    'jiangsu': 'Giang Tô',
    'fujian': 'Phúc Kiến',
    'sichuan': 'Tứ Xuyên',
    'yunnan': 'Vân Nam',
    'guangxi': 'Quảng Tây',
    'songshan': 'Tung Sơn',
    'taishan': 'Thái Sơn',
    'huashan': 'Hoa Sơn',
    'tianshan': 'Thiên Sơn',
    'wutai': 'Ngũ Đài',
    'emei': 'Nga Mi',
    'putuo': 'Phổ Đà',
    'jiuhua': 'Cửu Hoa',
    'baima': 'Bạch Mã',
    'famen': 'Pháp Môn',
    'lingyin': 'Linh Ẩn',
    'gandhara': 'Càn Đà La',
    'kashmir': 'Kế Tân',
    # Multi-syllable person names (safe)
    'xuanzang': 'Huyền Trang',
    'bodhidharma': 'Bồ Đề Đạt Ma',
    'nagarjuna': 'Long Thọ',
    'asvaghosa': 'Mã Minh',
    'vasubandhu': 'Thế Thân',
    'ashoka': 'A Dục',
    'kumarajiva': 'Cưu Ma La Thập',
    'huineng': 'Huệ Năng',
    'yijing': 'Nghĩa Tịnh',
    'fazang': 'Pháp Tạng',
    'zhiyi': 'Trí Khải',
    'daoxin': 'Đạo Tín',
    'hongren': 'Hoằng Nhẫn',
    'shenxiu': 'Thần Tú',
    'huike': 'Huệ Khả',
    'sengcan': 'Tăng Xán',
    'mazu': 'Mã Tổ',
    'baizhang': 'Bách Trượng',
    'linji': 'Lâm Tế',
    'fayan': 'Pháp Nhãn',
    'guiyang': 'Quy Ngưỡng',
    'yunmen': 'Vân Môn',
    'huangbo': 'Hoàng Bá',
    'zhaozhou': 'Triệu Châu',
    'deshan': 'Đức Sơn',
    'xuefeng': 'Tuyết Phong',
    'yongming': 'Vĩnh Minh',
    'dahui': 'Đại Huệ',
    'hongzhi': 'Hoằng Trí',
    'wansong': 'Vạn Tùng',
    'xuansha': 'Huyền Sa',
    'changsha': 'Trường Sa',
    'longya': 'Long Nha',
    'caoshan': 'Tào Sơn',
    'dongshan': 'Động Sơn',
    'yongming': 'Vĩnh Minh',
    'huiyuan': 'Huệ Viễn',
    'daosheng': 'Đạo Sinh',
    'jizang': 'Cát Tạng',
    'tanluan': 'Đàm Loan',
    'shandao': 'Thiện Đạo',
    'jiaxiang': 'Gia Tường',
    'xuanzang': 'Huyền Trang',
    'kuiji': 'Khuy Cơ',
    'yixing': 'Nhất Hạnh',
    'juan': 'Quyển',
    # Dynasty names (all multi-syllable in use)
    'tang dynasty': 'Nhà Đường',
    'song dynasty': 'Nhà Tống',
    'yuan dynasty': 'Nhà Nguyên',
    'ming dynasty': 'Nhà Minh',
    'qing dynasty': 'Nhà Thanh',
    'sui dynasty': 'Nhà Tùy',
    'han dynasty': 'Nhà Hán',
    'jin dynasty': 'Nhà Tấn',
    'wei dynasty': 'Nhà Ngụy',
    'wu dynasty': 'Nhà Ngô',
    'liang dynasty': 'Nhà Lương',
    'chen dynasty': 'Nhà Trần',
    'zhou dynasty': 'Nhà Chu',
    'qin dynasty': 'Nhà Tần',
    'northern wei': 'Bắc Ngụy',
    'southern dynasties': 'Nam Triều',
    'northern dynasties': 'Bắc Triều',
    'sui and tang': 'Tùy Đường',
    'six dynasties': 'Lục Triều',
    # Era names (multi-syllable only)
    'yongming': 'Vĩnh Minh',
    'yonghui': 'Vĩnh Huy',
    'zhenguan': 'Trinh Quán',
    'longshuo': 'Long Sóc',
    'xianqing': 'Hiển Khánh',
}

# Vietnamese misspellings / variants → correct form
FIXED_GLOSSARY_VI = {
    'chùa thiếu lâm': 'Thiếu Lâm Tự',
    'chùa shaolin': 'Thiếu Lâm Tự',
    'chùa bạch mã': 'Bạch Mã Tự',
    'chùa linh ẩn': 'Linh Ẩn Tự',
    'chùa pháp môn': 'Pháp Môn Tự',
    'chùa đại lâm': 'Đại Lâm Tự',
    'núi thiếu thất': 'Thiếu Thất Sơn',
    'tổ sư': 'Tổ Sư',
    'thiền sư': 'Thiền Sư',
    'cao tăng': 'Cao Tăng',
    'đại đức': 'Đại Đức',
    'thượng tọa': 'Thượng Tọa',
    'hòa thượng': 'Hòa Thượng',
    'ni sư': 'Ni Sư',
    'cư sĩ': 'Cư Sĩ',
    'sa môn': 'Sa Môn',
    'đệ tử': 'Đệ Tử',
    'môn đệ': 'Môn Đệ',
    'pháp sư': 'Pháp Sư',
    'luật sư': 'Luật Sư',
    'kinh sư': 'Kinh Sư',
    'giảng sư': 'Giảng Sư',
    'tăng sĩ': 'Tăng Sĩ',
    'tăng chúng': 'Tăng Chúng',
    'ni chúng': 'Ni Chúng',
    'phật tử': 'Phật Tử',
    'thập phương': 'Thập Phương',
    'chúng sanh': 'Chúng Sinh',
    'bồ tát': 'Bồ Tát',
    'la hán': 'A La Hán',
    'chư thiên': 'Chư Thiên',
    'chư phật': 'Chư Phật',
    'chư tăng': 'Chư Tăng',
    'ni cô': 'Ni Cô',
    'đại sư': 'Đại Sư',
    'thiền tông': 'Thiền Tông',
    'tịnh độ': 'Tịnh Độ',
    'mật tông': 'Mật Tông',
    'phật giáo': 'Phật Giáo',
    'pháp môn': 'Pháp Môn',
    'tam tạng': 'Tam Tạng',
    'tam bảo': 'Tam Bảo',
    'nam mô': 'Nam Mô',
    'a di đà phật': 'A Di Đà Phật',
    'quan âm': 'Quan Âm',
    'phổ hiền': 'Phổ Hiền',
    'văn thù': 'Văn Thù',
    'địa tạng': 'Địa Tạng',
    'di lặc': 'Di Lặc',
    'thích ca': 'Thích Ca',
    'thế tôn': 'Thế Tôn',
    'như lai': 'Như Lai',
}


@lru_cache(maxsize=1)
def load_glossary():
    """Build a combined glossary from DB + built-in fixed maps.
    Returns dict {lowercase_form: corrected_form}.
    Entries sorted by length descending so longer matches are tried first."""
    glossary = {}

    # 1) From namevi_map_places (Chinese → Vietnamese)
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT name_zh, name_vi FROM namevi_map_places "
            "WHERE name_zh IS NOT NULL AND name_zh != '' "
            "AND name_vi IS NOT NULL AND name_vi != ''"
        ).fetchall()
        for zh, vi in rows:
            zh = zh.strip()
            vi = vi.strip()
            if zh and vi:
                glossary[zh.lower()] = vi
    finally:
        conn.close()

    # 2) From name_vi_map (Chinese → Vietnamese, person names)
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT name_zh, name_vi FROM name_vi_map "
            "WHERE name_zh IS NOT NULL AND name_zh != '' "
            "AND name_vi IS NOT NULL AND name_vi != ''"
        ).fetchall()
        for zh, vi in rows:
            zh = zh.strip()
            vi = vi.strip()
            if zh and vi:
                glossary[zh.lower()] = vi
    finally:
        conn.close()

    # 3) English → Hán-Việt lookups
    for eng, hv in FIXED_GLOSSARY_EN.items():
        glossary[eng.lower()] = hv

    # 4) Vietnamese variants → correct Hán-Việt
    for variant, correct in FIXED_GLOSSARY_VI.items():
        glossary[variant.lower()] = correct

    # Sort by length descending
    sorted_items = sorted(glossary.items(), key=lambda x: -len(x[0]))
    return dict(sorted_items)


def _has_vietnamese(text):
    """Check if text has significant Vietnamese/Latin content (not pure Chinese)."""
    latin = len(re.findall(r'[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưỡạẹệịọộụựỳỵỷỹ]', text))
    total = len(text)
    if total == 0:
        return False
    return (latin / total) > 0.3


def normalize_text(text, glossary=None):
    """Apply Hán-Việt normalization to raw Vietnamese text.
    
    1. Replace English/Pinyin forms with Hán-Việt (word-boundary safe)
    2. Replace remaining Chinese characters with Hán-Việt from lexicon
    3. Join broken lines, fix basic formatting
    4. Strip isolated noisy characters
    
    Fully local — no external API calls.
    
    Args:
        text: Raw Vietnamese text to normalize
        glossary: Pre-loaded glossary dict (will load if None)
    
    Returns:
        Normalized text string
    """
    if not text:
        return text

    if glossary is None:
        glossary = load_glossary()

    # Skip if pure Chinese (original han_text, not translation output)
    if not _has_vietnamese(text):
        return text

    result = text

    # Phase 1: English/Pinyin → Hán-Việt (word-boundary for short terms)
    for key, val in glossary.items():
        if len(key) <= 4:
            pattern = re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(key), re.IGNORECASE)
        result = pattern.sub(val, result)

    # Phase 2: Replace Chinese character sequences with Vietnamese (only in mixed text)
    # Short-term: split on CJK runs and replace each run
    def _replace_cjk(m):
        run = m.group(0)
        # Try to match against glossary (longest first)
        for k, v in glossary.items():
            if run.lower() == k.lower():
                return v
        return run

    result = re.sub(r'[⺀-⿕一-鿿]+', _replace_cjk, result)

    # Phase 3: Fix formatting issues
    lines = result.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cleaned_lines.append(line)

    result = '\n'.join(cleaned_lines)

    # Phase 4: Fix sentence boundary issues (Google Translate artifact)
    result = re.sub(r'\.\n([a-zàáâãèéêìíòóôõùúý])', r'. \1', result)
    result = re.sub(r',\n([a-zàáâãèéêìíòóôõùúý])', r', \1', result)

    # Capitalize first letter of each sentence
    result = re.sub(r'(?<=[.?!] )([a-zàáâãèéêìíòóôõùúý])',
                    lambda m: m.group(1).upper(), result)
    if result and result[0].islower():
        result = result[0].upper() + result[1:]

    # Phase 5: Remove isolated CJK chars (single char left after translation)
    result = re.sub(r'(?<=[^⺀-⿕一-鿿])[⺀-⿕一-鿿](?=[^⺀-⿕一-鿐])', '', result)
    result = re.sub(r'\s[⺀-⿕一-鿿]\s', ' ', result)
    result = re.sub(r'^[⺀-⿕一-鿿]\s', '', result)

    result = result.strip()
    return result


if __name__ == '__main__':
    g = load_glossary()
    print(f"Glossary loaded: {len(g)} entries")
    test_cases = [
        "Shaolin temple is located in Henan province. The great master Xuanzang studied there.",
        "He went to Kuaiji and visited Jingde county. The monk Huineng was his teacher.",
        "In Luoyang, the Baima temple was built during the Han dynasty.",
        "從大梁到少林寺。玄奘法師在此翻譯經文。",
    ]
    for tc in test_cases:
        print("---")
        print(f"BEFORE: {tc}")
        print(f"AFTER:  {normalize_text(tc, g)}")

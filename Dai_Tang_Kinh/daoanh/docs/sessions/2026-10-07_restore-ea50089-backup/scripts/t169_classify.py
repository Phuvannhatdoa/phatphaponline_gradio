# -*- coding: utf-8 -*-
"""
T169 — classify_diff: phân loại khác biệt giữa từ điển (dict_vi) và Groq Qwen (groq_vi).

Thứ tự ưu tiên cố định, DỪNG Ở NHÃN ĐẦU, KHÔNG ghép nhãn (SPEC P1-1 · T184 G5):
  1) POLYPHONIC_CHAR  — ký tự đa âm: readings_dict ≠ readings_groq (hoặc 1 bên rỗng ≥1 reading)
  2) TAXONOMY_VARIANT — taxonomy suffix word-boundary (vd 寺 → tự/chùa)
  3) PHONETIC_MISMATCH— phiên âm lệch còn lại
  4) NONE             — dict == groq (verified, không cần review)

Trụ đa âm = static map inline (additive, 0 bảng mới) — phủ 3 fixture bắt buộc +
các ký tự đa âm phổ biến trong spine địa danh; mở rộng qua T167 glossary sau.
"""
import re
import unicodedata

# Ký tự đa âm: char Hán → tập reading Hán-Việt hợp lệ (đã normalize, không dấu).
POLYPHONIC_CHAR = {
    '降': ['giáng', 'hàng'],
    '白': ['bạch', 'bạch'],
    '長': ['trường', 'trưởng'],
    '行': ['hành', 'hạnh', 'hàng'],
    '觀': ['quán', 'quan'],
    '樂': ['lạc', 'nhạc'],
    '大': ['đại', 'thái'],
    '藏': ['tạng', 'tàng'],
    '石': ['thạch', 'đạn'],
    '不': ['bất'],
    '重': ['trọng', 'trùng'],
    '六': ['lục'],
    '阿': ['a', 'á'],
    '伽': ['già', 'gia'],
    '呵': ['ha', 'a'],
    '那': ['na', 'nã'],
    '薄': ['bạc', 'bộ'],
    '瞿': ['cù', 'câu'],
    '摩': ['ma', 'mô'],
    '耆': ['kỳ', 'kì'],
    '闍': ['xà', 'đô'],
    '陀': ['đà'],
    '菩': ['bồ'],
    '薩': ['tát'],
    '曼': ['mạn', 'man'],
    '毗': ['tỳ', 'tì'],
    '毘': ['tỳ', 'tì'],
    '迦': ['gia', 'ca'],
    '彌': ['di', 'mi'],
    '須': ['tu'],
    '伽耶': ['già da', 'gia da'],
}

# Suffix taxonomy: (hán-việt reading, bản địa reading) tương đương ngữ nghĩa cho CÙNG ký tự.
# Không chứa cặp nest (`viện`/`tự viện` — cấm P1-2). Match word-boundary theo token.
TAXONOMY_SUFFIX = {
    '寺': [('tự', 'chùa')],
    '院': [('viện', 'chùa')],
    '庵': [('am', 'chùa')],
    '殿': [('điện', 'điện')],
    '窟': [('quật', 'hang')],
}

_WS_RE = re.compile(r'\s+')


def normalize_text(s):
    """Hạ 1 chuỗi → diacritics-free lowercase (cùng chuẩn name_vi_norm)."""
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    return _WS_RE.sub(' ', s).lower().strip()


def _tokens(s):
    """Tách token (không dấu) từ chuỗi phiên âm — word-boundary tự nhiên."""
    norm = normalize_text(s)
    return [t for t in re.split(r'[^\w]+', norm) if t]


_CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')


def classify_diff(name_zh, dict_vi, groq_vi):
    """Trả về (diff_type, reason). Không ghi DB. Raises nếu thiếu input."""
    name_zh = (name_zh or '').strip()
    dict_vi = (dict_vi or '').strip()
    groq_vi = (groq_vi or '').strip()

    if not name_zh or not _CJK_RE.search(name_zh):
        raise ValueError('name_zh phải là Hán tự để classify')

    dict_tok = _tokens(dict_vi)
    groq_tok = _tokens(groq_vi)
    dict_norm = normalize_text(dict_vi)
    groq_norm = normalize_text(groq_vi)

    # ① POLYPHONIC_CHAR — mỗi ký tự đa âm trong name_zh
    for ch in name_zh:
        reads = POLYPHONIC_CHAR.get(ch)
        if not reads or len(reads) < 2:
            continue
        read_set = set(normalize_text(r) for r in reads)
        r_d = set(t for t in dict_tok if t in read_set)
        r_g = set(t for t in groq_tok if t in read_set)
        # diff nếu tập reading hai bên khác nhau, hoặc 1 bên rỗng nhưng bên kia ≥1 reading
        if r_d != r_g and (r_d or r_g):
            return 'POLYPHONIC_CHAR', (
                f"ký tự '{ch}' multi-reading {sorted(read_set)}: "
                f"dict {sorted(r_d)} vs groq {sorted(r_g)}")

    # ② TAXONOMY_VARIANT — word-boundary theo token (không substring)
    for ch in name_zh:
        pairs = TAXONOMY_SUFFIX.get(ch)
        if not pairs:
            continue
        for hv, vern in pairs:
            hv_n = normalize_text(hv)
            vern_n = normalize_text(vern)
            if hv_n == vern_n:
                # cặp self-match ('殿' điện/điện) KHÔNG thể là variant — bỏ qua,
                # tránh false conflict khi dict==groq cùng 'điện' (T170 fix).
                continue
            # yêu cầu hai bên dùng reading KHÁC nhau cho cùng suffix
            if ((hv_n in dict_tok and vern_n in groq_tok)
                    or (vern_n in dict_tok and hv_n in groq_tok)):
                return 'TAXONOMY_VARIANT', (
                    f"suffix '{ch}': dict dùng '{hv}' / groq dùng '{vern}'")

    # ③ PHONETIC_MISMATCH * ④ NONE
    if dict_norm != groq_norm:
        return 'PHONETIC_MISMATCH', 'phiên âm lệch giữa từ điển và Groq'
    return 'NONE', 'dict == groq — verified'


# 3 fixture bắt buộc (SPEC §3.9)
FIXTURES = [
    ('降魔窟', 'Giáng Ma Quật', 'Hàng Ma Quật', 'POLYPHONIC_CHAR'),
    ('白馬寺', 'Bạch Mã Tự', 'Chùa Bạch Mã', 'TAXONOMY_VARIANT'),
    ('少林寺', 'Thiếu Lâm Tự', 'Thiếu Lâm Tự', 'NONE'),
]


if __name__ == '__main__':
    ok = True
    for name_zh, d, g, want in FIXTURES:
        got, reason = classify_diff(name_zh, d, g)
        mark = '✅' if got == want else '❌'
        ok = ok and (got == want)
        print(f'{mark} {name_zh} | {d} vs {g} → {got} (want {want}) · {reason}')
    print('T169 classify_diff: ' + ('ALL PASS' if ok else 'FAIL'))
    raise SystemExit(0 if ok else 1)
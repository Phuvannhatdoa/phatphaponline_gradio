# -*- coding: utf-8 -*-
"""
T170 — classify_person_diff + preprocess cho `--entity person` (SPEC §3.2 + §3bis R2/R3/R4)

Thứ tự ưu tiên cố định, DỪNG Ở NHÃN ĐẦU (giữ nguyên triết lý T169 P1-1):
  1) SANSKRIT exact (registry canonical) — khớp cả 2 bên → auto_verified_sanskrit
  2) SANSKRIT_VARIANT / SANSKRIT_VARIANT_UNCONFIRMED — registered nhưng reading lệch
  3) SANSKRIT_UNMAPPED — có indicator stem nhưng không khớp registry (cần lexicon review)
  4) FORMAT_NORMALIZED — cùng nội dung, chỉ lệch dấu/hoa/space
  5) TITLE_VARIANT — core bằng nhau, chỉ khác tôn xưng (auto_title_aligned)
  6) fallback classify_diff (R1 POLYPHONIC word-token + TAXONOMY + PHONETIC + NONE) từ t169_classify

Trả về (diff_type, reason, status_hint): verify script quyết status/needs_review từ đây.
"""
import os
import re
import sys
import unicodedata

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from t169_classify import classify_diff, normalize_text  # noqa: E402

# --- R3: CJK variant fold (Admin: tự seed, không chờ) ---
CJK_VARIANT_FOLD = {
    '峯': '峰',   # 峰/峯: 309/210 place · people 346/1470
    '羣': '群',
    '祕': '秘',
    '惠': '慧',   # 惠/慧: place 108/194 · people có cả 2
}

FOLD_UNMAPPED = []  # pipe cho R8: log true unmapped (fold_unmapped warning)


def fold_cjk(text):
    """Chuẩn hoá variant Hán: fold heo map rồi NFKC. Trả (folded, changed).
    `text` đã là Hán (clean_zh) — KHÔNG áp cho chuỗi có tiếng Việt."""
    out = []
    changed = False
    if text:
        for ch in text:
            n = CJK_VARIANT_FOLD.get(ch, ch)
            if n != ch:
                changed = True
            out.append(n)
    folded = unicodedata.normalize('NFKC', ''.join(out))
    return folded, changed


# --- R2: bracket stack lồng nhau ---
_OPEN_BR = {'(', '[', '（', '［'}
_CLOSE_BR = {')', ']', '）', '］'}


def split_brackets(text):
    """Tách mọi span ngoặc (lồng, đầy đủ) → (clean_zh, meta_note, is_uncertain).
    R2: stack/đệ quy, không regex 1 lớp. Dấu đóng thừa → is_uncertain=1, không cho vào clean."""
    if not text:
        return '', '', 0
    clean = []
    meta = []
    depth = 0
    buf = []          # chars đang trong ngoặc
    uncertain = 0
    for ch in text:
        if ch in _OPEN_BR:
            depth += 1
            if depth == 1:
                buf = []
            else:
                buf.append(ch)
        elif ch in _CLOSE_BR:
            if depth == 0:
                uncertain = 1          # `)`/`]` thừa — không rơi vào clean
            else:
                depth -= 1
                buf.append(ch)
                if depth == 0:
                    meta.append(''.join(buf))
                    buf = []
        else:
            if depth > 0:
                buf.append(ch)
            else:
                clean.append(ch)
    if depth > 0:
        uncertain = 1                   # ngoặc chưa đóng
        if buf:
            meta.append(''.join(buf))
    clean_zh = ''.join(clean).strip()
    meta_note = ' '.join(x.strip() for x in meta if x and x.strip())
    clean_zh = clean_zh.strip('()[]（） 　')
    return clean_zh, meta_note, uncertain


# --- R4: title multi-token loop (Vietnamese core strip) ---
PERSON_PREFIX_TITLES = {
    'thích', 'thiền sư', 'pháp sư', 'đại sư', 'quốc sư', 'thiền tổ', 'lục tổ',
    'tam tạng', 'hòa thượng', 'đại thiền sư', 'minh sư', 'thiền đức', 'tổ sư',
    'bồ tát', 'mã tổ', 'bách trượng', 'cao tăng',
}
PERSON_SUFFIX_TITLES = {
    'thiền sư', 'pháp sư', 'đại sư', 'quốc sư', 'hòa thượng', 'tăng', 'ni sư',
    'thiền tổ', 'cao tăng', 'thiền đức', 'đại thiền sư',
}


def _vtokens(s):
    return [t for t in re.split(r'[^\w]+', normalize_text(s)) if t]


_PREFIX_NORM = {normalize_text(t) for t in PERSON_PREFIX_TITLES}
_SUFFIX_NORM = {normalize_text(t) for t in PERSON_SUFFIX_TITLES}


def extract_vi_core(vi_text):
    """Loop strip prefix/suffix title (1–2 token) → core (≥1 token, giữ nguyên bản)."""
    if not vi_text:
        return ''
    toks = _vtokens(vi_text)
    if not toks:
        return ''
    i = 0
    n = len(toks)
    while i < n:
        two = ' '.join(toks[i:i + 2]) if i + 1 < n else None
        if two in _PREFIX_NORM:
            i += 2
            continue
        if toks[i] in _PREFIX_NORM:
            i += 1
            continue
        break
    j = n
    while j > i:
        two = ' '.join(toks[j - 2:j]) if j - 1 >= i else None
        if two in _SUFFIX_NORM:
            j -= 2
            continue
        if toks[j - 1] in _SUFFIX_NORM:
            j -= 1
            continue
        break
    core = toks[i:j]
    return ' '.join(core) if core else ' '.join(toks)


# --- Sanskrit registry (seed — mở rộng chủ đích qua fold_unmapped) ---
# canonical Hán → tập reading Hán-Việt hợp lệ (đã normalize, không dấu)
PERSON_SANSKRIT_REGISTRY = {
    '菩提達磨': ['bồ đề đạt ma'],
    '達磨': ['đạt ma'],
    '慧能': ['huệ năng'],
    '惠能': ['huệ năng'],          # fold 惠→慧 trước khi tra
    '一行': ['nhất hạnh', 'nhất hành'],
    '真諦': ['chân đế'],
    '僧肇': ['tăng triệu'],
    '道安': ['đạo an'],
    '玄奘': ['huyền trang', 'huyền trạng'],
    '鳩摩羅什': ['cưu ma la thập'],
    '曇鸞': ['đàm loan'],
    '善導': ['thiện đạo'],
}

# indicator stem — nếu stem xuất hiện nhưng không khớp registry → SANSKRIT_UNMAPPED (R4/§3.2 bug 6)
SANSKRIT_INDICATORS = tuple(sorted({k[:2] for k in PERSON_SANSKRIT_REGISTRY}, key=len, reverse=True))


def _reads_from(words, allowed):
    return set(w for w in words if w in allowed)


def classify_person_diff(name_zh, dict_vi, groq_vi):
    """Trả (diff_type, reason, status_hint|None). Không ghi DB. Hán input để polyphonic/Sanskrit.
    status_hint: auto status cho verify (auto_verified_sanskrit/auto_title_aligned/...)"""
    name_zh = (name_zh or '').strip()
    dict_vi = (dict_vi or '').strip()
    groq_vi = (groq_vi or '').strip()

    clean_zh, meta_note, uncertain = split_brackets(name_zh)
    folded, _chg = fold_cjk(clean_zh or name_zh)

    dict_core = extract_vi_core(dict_vi)
    groq_core = extract_vi_core(groq_vi)
    d_norm = normalize_text(dict_vi)
    g_norm = normalize_text(groq_vi)
    d_core_norm = normalize_text(dict_core)
    g_core_norm = normalize_text(groq_core)

    # ① SANSKRIT exact — so theo TOKEN reading (multi-word: bồ đề đạt ma)
    ent = PERSON_SANSKRIT_REGISTRY.get(folded)
    if ent:
        allowed_tokens = set()
        for r in ent:
            allowed_tokens.update(normalize_text(r).split())
        d_ws = set(w for w in d_core_norm.split())
        g_ws = set(w for w in g_core_norm.split())
        r_d = d_ws & allowed_tokens
        r_g = g_ws & allowed_tokens
        if not r_d and not r_g:
            if d_ws or g_ws:
                return ('SANSKRIT_VARIANT_UNCONFIRMED',
                        f'Sanskrit {folded}: dict/groq không có reading hợp lệ', None)
            return ('SANSKRIT_VARIANT_UNCONFIRMED',
                    f'Sanskrit {folded}: dict rỗng', None)
        if r_d == r_g and r_d:
            return ('NONE',
                    f'Sanskrit {folded}: dict & groq cùng {sorted(r_d)}',
                    'auto_verified_sanskrit')
        return ('SANSKRIT_VARIANT',
                f'Sanskrit {folded}: dict {sorted(r_d)} vs groq {sorted(r_g)}', None)

    # ② indicator → SANSKRIT_UNMAPPED
    if any(s in folded for s in SANSKRIT_INDICATORS):
        return ('SANSKRIT_UNMAPPED',
                f'indicator {folded[:2]} trong tên nhưng không khớp registry',
                'needs_lexicon_review')

    # ③ FORMAT_NORMALIZED — cùng nội dung, chỉ lệch format
    if d_norm == g_norm:
        if dict_vi != groq_vi:
            return ('FORMAT_NORMALIZED', 'dict == groq (format-only lệch)', 'auto_verified')
        return ('NONE', 'dict == groq — verified', 'auto_verified')

    # ④ TITLE_VARIANT — core bằng nhau, chỉ khác tôn xưng
    if d_core_norm and d_core_norm == g_core_norm:
        return ('TITLE_VARIANT',
                f'core "{dict_core}" bằng nhau, chỉ khác title (dict="{dict_vi}" / groq="{groq_vi}")',
                'auto_title_aligned')

    # ⑤ fallback R1/TAXONOMY/PHONETIC/NONE — dùng core (đã strip title)
    try:
        diff_type, reason = classify_diff(folded or clean_zh or name_zh,
                                          dict_core or dict_vi, groq_core or groq_vi)
    except ValueError as e:
        diff_type, reason = 'PHONETIC_MISMATCH', f'skip-classify: {e}'
        if d_norm == g_norm:
            diff_type, reason = 'FORMAT_NORMALIZED', reason
    return diff_type, reason, None


if __name__ == '__main__':
    cases = [
        # (name_zh, dict, groq, want_type, want_hint)
        # Ghi chú: normalize bỏ dấu → 'hạnh'/'hành' đều 'hanh' (giới hạn engine, R8);
        # person polyphonic dùng cặp đổi phụ âm (giáng/hàng) để phân biệt được.
        ('降龍', 'Giáng Long', 'Hàng Long', 'POLYPHONIC_CHAR', None),
        ('菩提達磨', 'Bồ Đề Đạt Ma', 'Bồ Đề Đạt Ma', 'NONE', 'auto_verified_sanskrit'),
        ('道安', 'Đạo An', 'Đạo An Quốc Sư', 'NONE', 'auto_verified_sanskrit'),
        ('慧遠', 'Thích Huệ Viễn', 'Huệ Viễn', 'TITLE_VARIANT', 'auto_title_aligned'),
        ('一行', 'Nhất Hạnh', 'Nhất Hạnh', 'NONE', 'auto_verified_sanskrit'),
        ('開元路', 'Khai Nguyên Lộ', 'Khai Nguyên Lộ', 'NONE', 'auto_verified'),
    ]
    ok = True
    for name_zh, d, g, want_type, want_hint in cases:
        got_type, reason, hint = classify_person_diff(name_zh, d, g)
        mark = '✅' if got_type == want_type else '❌'
        ok = ok and (got_type == want_type)
        print(f'{mark} {name_zh} | {d} vs {g} → {got_type} (want {want_type}) · hint={hint}')
    print('T170 classify_person_diff: ' + ('ALL PASS' if ok else 'FAIL'))
    raise SystemExit(0 if ok else 1)
# -*- coding: utf-8 -*-
"""T243 (M7 GIS VN) — Module chuẩn hóa tên địa danh Phật giáo.

Cung cấp cho pipeline ingest + matching (T244):
  - nfkc()              : Unicode NFKC (dấu toàn-width → bán-width, tổ hợp chuẩn)
  - vn_key()            : khóa không dấu tiếng Việt — TÁI DÙNG normalize_text()
                          của app.py (AST-extract để không khởi động Flask).
  - strip_facility()    : bỏ hậu tố Hán (寺/院/庵/...) + tiền tố VN (chùa/tự/thiền viện/...)
  - hanvi_reading()     : phiên âm Hán-Việt từ bảng DB hanviet_char_map
                          (+ custom_hanviet_override / hanviet_fallback đã merge sẵn)
  - pinyin_reading()    : phiên âm pinyin qua thư viện pypinyin (lazy; thiếu → None)

Zero-RAM: không nạp dữ liệu lớn; chỉ nạp bảng "char" (≈11.3k) là đủ.
"""

import ast
import os
import re
import unicodedata

_HERE = os.path.dirname(os.path.abspath(__file__))
_DAOANH = os.path.dirname(_HERE)
_APP_PY = os.path.join(_DAOANH, 'app.py')

# ── normalize_text() tái dùng từ app.py (AST-extract, không import Flask) ──

def _extract_normalize_text():
    """Lấy nguyên văn hàm normalize_text() trong app.py."""
    if not os.path.isfile(_APP_PY):
        return None
    src = open(_APP_PY, encoding='utf-8').read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'normalize_text':
            lines = src.splitlines()
            return '\n'.join(lines[node.lineno - 1:node.end_lineno])
    return None


_normalize_ns = {'unicodedata': unicodedata, 're': re}
_extracted = _extract_normalize_text()
if _extracted:
    exec(compile(_extracted, '<app.normalize_text>', 'exec'), _normalize_ns)
    normalize_text = _normalize_ns['normalize_text']
else:
    def normalize_text(s):
        """Fallback — logic tương đương app.py (NFD + bỏ dấu kết hợp + đ→d + lower)."""
        if not s:
            return ''
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        s = s.replace('đ', 'd').replace('Đ', 'd')
        return re.sub(r'\s+', ' ', s).lower().strip()

NORMALIZE_FROM_APP = _extracted is not None


# ── NFKC ────────────────────────────────────────────────────────────────────

def nfkc(s):
    if not s:
        return ''
    return unicodedata.normalize('NFKC', s).strip()


# ── Cơ sở thờ tự (bỏ cho khóa khớp lỏng) ───────────────────────────────────

# Hậu tố Hán dùng làm tên riêng của cơ sở (cắt 1 lượt, giữ phần còn lại)
CJK_FACILITY_SUFFIX = (
    '寺', '院', '庵', '廟', '塔', '閣', '殿', '宮', '堂',
    '精舍', '蘭若', '伽藍', '道場', '寺舍',
)

# Tiền tố/loại VN xuất hiện đầu tên ("Chùa Trấn Quốc", "Tổ đình Vĩnh Nghiêm"...)
VN_FACILITY_PREFIX = (
    'chùa ', 'tổ đình ', 'thiền viện ', 'tịnh xá ', 'tịnh thất ',
    'niệm phật đường ', 'tu viện ', 'đại tòng lâm ', 'bảo tháp ',
    'tháp ', 'am ', 'phật đường ', 'thiền đường ', 'cổ tự ', 'tự ',
)

VN_FACILITY_SUFFIX = (' chùa', ' tự', ' tháp', ' tịnh xá')


def strip_facility(name):
    """Bỏ cơ sở thờ tự để lấy phần tên riêng (phục vụ khóa khớp 'stripped')."""
    s = nfkc(name)
    if not s:
        return s
    low = s.lower()
    # 1) tiền tố VN
    for p in VN_FACILITY_PREFIX:
        if low.startswith(p):
            s = s[len(p):].strip()
            low = s.lower()
            break
    # 2) hậu tố Hán (ưu tiên dài trước: 精舍 > 寺)
    for suf in sorted(CJK_FACILITY_SUFFIX, key=len, reverse=True):
        if s.endswith(suf) and len(s) > len(suf):
            s = s[:-len(suf)].strip()
            break
    else:
        # 3) hậu tố VN (khi chữ Hán rỗng / không khớp hậu tố Hán)
        for suf in VN_FACILITY_SUFFIX:
            if low.endswith(suf) and len(s) > len(suf):
                s = s[:-len(suf)].strip()
                break
    return s


# ── Khóa chuẩn ──────────────────────────────────────────────────────────────

def vn_key(s, stripped=False):
    """Khóa không dấu tiếng Việt. stripped=True → bỏ cơ sở thờ tự trước."""
    s = nfkc(s)
    if stripped:
        s = strip_facility(s)
    return normalize_text(s)


# ── Hán-Việt (từ DB hanviet_char_map + custom override) ────────────────────

def load_hanviet_map(conn):
    """dict char → Hán-Việt. Ưu tiên custom_hanviet_override chồng lên char_map."""
    m = {}
    try:
        for ch, r in conn.execute(
                'SELECT char, reading FROM hanviet_char_map WHERE reading IS NOT NULL AND reading != \'\''):
            m[ch] = r
    except Exception:
        pass
    try:
        for ch, r in conn.execute(
                'SELECT char, hanviet FROM custom_hanviet_override WHERE hanviet IS NOT NULL AND hanviet != \'\''):
            m[ch] = r
    except Exception:
        pass
    return m


def hanvi_reading(name_zh, hanvi_map, separator=' '):
    """Phiên âm Hán-Việt từng chữ; chữ không tra được giữ nguyên ký tự gốc."""
    if not name_zh:
        return None
    out = []
    for ch in nfkc(name_zh):
        out.append(hanvi_map.get(ch, ch))
    return separator.join(out)


# ── Pinyin (lazy; cần pip install pypinyin) ─────────────────────────────────

def pinyin_reading(name_zh, separator=' '):
    """Phiên âm pinyin. Không có pypinyin → trả None (gọi bên ghi nullable)."""
    if not name_zh:
        return None
    try:
        from pypinyin import lazy_pinyin
    except Exception:
        return None
    try:
        return separator.join(lazy_pinyin(nfkc(name_zh)))
    except Exception:
        return None


def pinyin_available():
    try:
        import pypinyin  # noqa: F401
        return True
    except Exception:
        return False


# ── Bộ khóa cho một địa danh (entry generator) ──────────────────────────────

def place_key_entries(name, hanvi_map=None, make_hanvi=False):
    """Sinh các entry (name_text, key_kind, norm_key, hanvi, pinyin) cho 1 tên."""
    name = nfkc(name)
    if not name:
        return
    for kind, base in (('full', name), ('stripped', strip_facility(name))):
        key = vn_key(base)
        if not key:
            continue
        rec = {
            'name_text': name,
            'key_kind': kind,
            'norm_key': key,
        }
        if make_hanvi and hanvi_map is not None:
            rec['hanvi'] = hanvi_reading(name, hanvi_map)
            rec['pinyin'] = pinyin_reading(name)
        else:
            rec['hanvi'] = None
            rec['pinyin'] = None
        yield rec
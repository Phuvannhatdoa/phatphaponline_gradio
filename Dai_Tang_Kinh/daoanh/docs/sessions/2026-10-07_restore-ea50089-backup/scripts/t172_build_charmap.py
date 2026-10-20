# -*- coding: utf-8 -*-
"""
T172 — Build `hanviet_char_map` (merge 3 dict) + pure charwise algorithm helpers.

SPEC: docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md §3/§4

3 dict xung đột (priority `custom_hanviet_override` > `HAN_VIET_CHAR` > `hanviet_fallback`):
  - HAN_VIET_CHAR     : Python dict literal trong app.py (~1.478 entry, cho place)
  - hanviet_fallback  : DB table (ch, hv)  ~8.650
  - custom_hanviet_override : DB table (char, hanviet) ~3.968

Đưa ra các hàm THUẦN (không đụng DB) để tests/test_t172_charwise.py import —
không cần DB, không cần API key.

Usage:
    python scripts/t172_build_charmap.py --stats          # đếm 3 nguồn + số char duy nhất (RO)
    python scripts/t172_build_charmap.py --export OUT.json # ghi merged charmap ra JSON tạm (RO)
    python scripts/t172_build_charmap.py --apply          # INSERT OR REPLACE vào hanviet_char_map
    python scripts/t172_build_charmap.py --revert         # DROP hanviet_char_map (migrate --revert cũng xử lý)
"""
import argparse
import ast
import json
import os
import sqlite3
import sys
import unicodedata
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE    = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(BASE)
APP_PY  = os.path.join(ROOT, 'app.py')
DB_PATH = os.environ.get('T172_DB') or os.path.join(ROOT, 'data', 'lineage.db')

# Nguồn priority thấp→cao (để merge bằng dict sum)
SOURCE_ORDER_LOW_TO_HIGH = ['hanviet_fallback', 'HAN_VIET_CHAR', 'custom_hanviet_override']
SOURCE_PRIORITY = {s: i for i, s in enumerate(SOURCE_ORDER_LOW_TO_HIGH)}  # lớn hơn = ưu tiên hơn

DICT_VERSION = 't172-20260928-3dict'

# Các trạng thái validation (SPEC §4) — thứ tự ưu tiên: unknown > exception >
# (poly & differs → needs_review) > mismatch > valid
STATUS_VALID, STATUS_MISMATCH, STATUS_UNKNOWN, STATUS_EXCEPTION, STATUS_NEEDS_REVIEW = \
    'valid', 'mismatch', 'unknown_char', 'exception', 'needs_review'
VALIDATION_STATUSES = [STATUS_VALID, STATUS_MISMATCH, STATUS_UNKNOWN,
                       STATUS_EXCEPTION, STATUS_NEEDS_REVIEW]

LEGACY_EXACT, LEGACY_NORMALIZED, LEGACY_DIFFERS, LEGACY_NOT_COMPARABLE = \
    'exact', 'normalized', 'differs', 'not_comparable'
LEGACY_STATUSES = [LEGACY_EXACT, LEGACY_NORMALIZED, LEGACY_DIFFERS, LEGACY_NOT_COMPARABLE]


# ────────────────────────────────────────────────────────────────────────
# 1. Ideograph range (SPEC §4.1, plan mở rộng — kể cả U+279CC ký tự đếm)
# ────────────────────────────────────────────────────────────────────────
def is_ideograph(ch):
    """True nếu là Hán tự (bao gồm extension A/B+, compatibility).

    Covers: U+3400–U+4DBF (Ext A), U+4E00–U+9FFF (bộ gốc),
    U+F900–U+FAFF (compatibility), U+20000–U+2EBEF (Ext B/C/D/E/F — gồm U+279CC),
    U+2F800–U+2FA1F (compatibility supplement).
    """
    o = ord(ch)
    return (
        (0x3400 <= o <= 0x4DBF) or
        (0x4E00 <= o <= 0x9FFF) or
        (0xF900 <= o <= 0xFAFF) or
        (0x20000 <= o <= 0x2EBEF) or
        (0x2F800 <= o <= 0x2FA1F)
    )


# ────────────────────────────────────────────────────────────────────────
# 2. Extract HAN_VIET_CHAR literal từ app.py bằng AST (KHÔNG import app.py
#    — tránh nổ Flask + side-effect).
# ────────────────────────────────────────────────────────────────────────
def extract_han_viet_char(app_py=None):
    """Đọc dict literal `HAN_VIET_CHAR = {...}` trong app.py → {char: reading}."""
    app_py = app_py or APP_PY
    with open(app_py, 'r', encoding='utf-8') as f:
        src = f.read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == 'HAN_VIET_CHAR' \
               and isinstance(node.value, ast.Dict):
                out = {}
                for k_node, v_node in zip(node.value.keys, node.value.values):
                    if isinstance(k_node, ast.Constant) and isinstance(v_node, ast.Constant):
                        out[str(k_node.value)] = str(v_node.value)
                return out
    return {}


def load_db_sources(db_path=None):
    """Đọc 2 bảng DB: {char: reading} cho fallback + override.
    Trả về dict source_name → {char: reading}."""
    db = db_path or DB_PATH
    con = sqlite3.connect(db)
    try:
        fallback = {}
        for ch, hv in con.execute('SELECT ch, hv FROM hanviet_fallback'):
            if ch and hv:
                fallback[ch] = (hv or '').strip()
        override = {}
        for ch, hv in con.execute('SELECT char, hanviet FROM custom_hanviet_override'):
            if ch and hv:
                override[ch] = (hv or '').strip()
        return {'hanviet_fallback': fallback, 'custom_hanviet_override': override}
    finally:
        con.close()


def merged_char_rows(han_viet_char=None, db_sources=None):
    """Merge 3 dict → list row cho hanviet_char_map.

    Priority: custom_hanviet_override > HAN_VIET_CHAR > hanviet_fallback.
    is_polyphonic = char có ≥2 reading KHÁC NHAU giữa các dict; candidates = các
    reading thay thế (pipe-joined). Assert: reading KHÔNG chứa khoảng trắng
    (1 reading = 1 âm tiết).

    Return: (rows, violations) — rows: [{char, reading, source, is_polyphonic, candidates}].
    """
    han_viet_char = dict(han_viet_char or {})
    db_sources = dict(db_sources or {})
    sources = {'HAN_VIET_CHAR': han_viet_char}
    sources.update({k: dict(v) for k, v in db_sources.items() if v})

    rows = []
    violations = []

    # Làm sạch reading (strip + bỏ ô trống) — chữ có reading rỗng bị loại;
    # key có NHIỀU codepoint (tên ghép như '平定'→'Bình Định') KHÔNG phải từng-tự
    # → bỏ khỏi char map (charwise lookup theo từng Hán tự), ghi violation notch.
    all_readings = {}
    for sname, sdict in sources.items():
        cleaned = {}
        for ch, rd in sdict.items():
            if not ch:
                continue
            rd = (rd or '').strip()
            if len(ch) > 1:
                violations.append((ch, rd, 'key nhiều codepoint (tên ghép) — bỏ, không phải từng-tự'))
                continue
            if rd:
                cleaned[ch] = rd
        all_readings[sname] = cleaned

    # Union các char xuất hiện ở bất kỳ nguồn nào
    char_set = set()
    for sdict in all_readings.values():
        char_set.update(sdict.keys())

    rows = []
    for ch in sorted(char_set):
        # readings từng nguồn (chỉ nguồn có chữ)
        own = {s: all_readings[s][ch] for s in SOURCE_ORDER_LOW_TO_HIGH
               if ch in all_readings.get(s, {})}
        if not own:
            continue
        # priority winner
        chosen = max(own.items(), key=lambda kv: SOURCE_PRIORITY[kv[0]])
        reading, source = chosen[1], chosen[0]
        if ' ' in reading or '\t' in reading:
            violations.append((ch, reading, 'reading chứa khoảng trắng — vi phạm 1 reading = 1 âm tiết'))
        # Đa âm: so KHÔNG phân biệt hoa/thường ('Nhất' ≡ 'nhất'), candidates chỉ
        # giữ reading THỰC SỰ khác nhau (giữ nguyên case của nguồn).
        distinct = {}
        for s, rd in own.items():
            key = rd.casefold()
            if key not in distinct:
                distinct[key] = rd
        is_poly = len(distinct) > 1
        chosen_folded = reading.casefold()
        candidates = '|'.join(rd for k, rd in distinct.items() if k != chosen_folded)
        rows.append({
            'char': ch,
            'reading': reading,
            'source': source,
            'is_polyphonic': 1 if is_poly else 0,
            'candidates': candidates,
        })
    return rows, violations


# ────────────────────────────────────────────────────────────────────────
# 3. Charwise algorithm (SPEC §4) — thuần, không đụng DB
# ────────────────────────────────────────────────────────────────────────
def compute_charwise(name_zh, char_map):
    """Duyệt từng Hán tự → readings (placeholder `[?C]` cho tự chưa biết).

    char_map: dict char → {reading, is_polyphonic, candidates} (hoặc char → reading).
    Trả về dict: {charwise, unknown (list), poly (list[(char, candidates)]), han_count, syll_count}.
    """
    name_zh = name_zh or ''
    han = [c for c in name_zh if is_ideograph(c)]
    readings, unknown, poly = [], [], []
    for c in han:
        entry = char_map.get(c)
        if entry is None:
            readings.append(f'[?{c}]')
            unknown.append(c)
            continue
        if isinstance(entry, dict):
            reading, is_poly, candidates = entry.get('reading', ''), entry.get('is_polyphonic', 0), entry.get('candidates', '')
        else:
            reading, is_poly, candidates = entry, 0, ''
        readings.append(reading or f'[?{c}]')
        if reading and is_poly:
            poly.append((c, candidates))
    return {
        'charwise': ' '.join(readings),
        'unknown': unknown,
        'poly': poly,
        'han_count': len(han),
        'syll_count': len(readings),
    }


def _norm_flat(s):
    """NFC + lowercase + collapse whitespace (SPEC §8 legacy compare)."""
    s = unicodedata.normalize('NFC', s or '')
    return ' '.join(s.lower().split())


def _toneless(s):
    """Bỏ dấu tiếng Việt để so 'normalized' (so theo bộ chữ cái)."""
    s = unicodedata.normalize('NFD', s or '')
    out = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return _norm_flat(out)


def legacy_compare(name_vi, charwise):
    """So legacy `people.name_vi` với charwise (SPEC §4.4).

    exact → normalized → not_comparable (legacy còn sót Hán tự / không thể so)
    → differs. NFC/lowercase/whitespace được chuẩn hóa trước khi so.
    """
    name_vi = name_vi or ''
    charwise = charwise or ''
    if not name_vi.strip() and not charwise.strip():
        return LEGACY_NOT_COMPARABLE
    # LEGACY CÒN SÓT HÁN TỰ (chưa phiên âm hết) → không thể so từng tự
    if any(is_ideograph(c) for c in name_vi):
        return LEGACY_NOT_COMPARABLE
    if _norm_flat(name_vi) == _norm_flat(charwise):
        return LEGACY_EXACT
    if _toneless(name_vi) == _toneless(charwise):
        return LEGACY_NORMALIZED
    # Legacy có chữ phiên âm chung với charwise nhưng lệch nhẹ → vẫn 'differs'
    return LEGACY_DIFFERS


def validate_status(unknown, exception_hit, poly, legacy_match):
    """Xếp status theo rule SPEC §4:

        unknown > exception > (poly & differs → needs_review) > mismatch > valid.
    Trả về (status, reason parts). Đa âm luôn ghi marker `needs_review` vào reason.
    """
    parts = []
    if unknown:
        parts.append(f'chưa biết {len(unknown)} tự: {"".join(unknown)}')
        reason = '; '.join(parts) if parts else ''
        return STATUS_UNKNOWN, reason
    if exception_hit:
        parts.append('trong hanviet_exception_list (phiên âm ngoại lệ, không auto-sửa)')
        return STATUS_EXCEPTION, '; '.join(parts)
    if poly:
        for c, cands in poly:
            parts.append(f'đa âm {c}: {cands}' if cands else f'đa âm {c}')
    if legacy_match == LEGACY_DIFFERS:
        parts.append('legacy name_vi khác charwise')
        if poly:
            # (poly & differs) → cần người duyệt
            parts.append('needs_review')
            return STATUS_NEEDS_REVIEW, '; '.join(parts)
        return STATUS_MISMATCH, '; '.join(parts)
    if legacy_match in (LEGACY_EXACT, LEGACY_NORMALIZED, LEGACY_NOT_COMPARABLE) and poly:
        # Đa âm nhưng khớp legacy → vẫn valid, nhưng reason ghi cờ duyệt
        parts.append('needs_review')
        return STATUS_VALID, '; '.join(parts)
    return STATUS_VALID, '; '.join(parts)


def is_transliteration_flag(unknown, legacy_match):
    """T191 định nghĩa: =1 khi unknown RỖNG ∧ legacy_match ∈ {exact, normalized}."""
    return 1 if (not unknown and legacy_match in (LEGACY_EXACT, LEGACY_NORMALIZED)) else 0


# ────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────
def cmd_stats():
    hv = extract_han_viet_char()
    db = load_db_sources()
    print(f'HAN_VIET_CHAR (app.py literal):  {len(hv):,} entry')
    print(f'hanviet_fallback (DB):            {len(db.get("hanviet_fallback", {})):,}')
    print(f'custom_hanviet_override (DB):     {len(db.get("custom_hanviet_override", {})):,}')
    rows, viol = merged_char_rows(hv, db)
    print(f'→ hanviet_char_map sẽ có:          {len(rows):,} chữ duy nhất')
    n_poly = sum(1 for r in rows if r['is_polyphonic'])
    print(f'có polyphonic:                     {n_poly:,}')
    if viol:
        print('⚠ VIOLATIONS (1 reading != 1 âm tiết):')
        for v in viol[:20]:
            print('  ', v)
    if not rows:
        print('⚠ KHÔNG có row — kiểm tra DB/app.py path')


def cmd_export(out_path):
    hv = extract_han_viet_char()
    db = load_db_sources()
    rows, viol = merged_char_rows(hv, db)
    payload = {'dict_version': DICT_VERSION, 'generated_at': datetime.now().isoformat(timespec='seconds'),
               'count': len(rows), 'poly_count': sum(1 for r in rows if r['is_polyphonic']), 'rows': rows}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f'Exported {len(rows):,} chars → {out_path}')
    if viol:
        print(f'⚠ {len(viol)} violations 1-âm-tiết (xem --stats)')


CREATE_CHAR_MAP = """
CREATE TABLE IF NOT EXISTS hanviet_char_map (
  char           TEXT PRIMARY KEY,
  reading        TEXT NOT NULL,
  source         TEXT NOT NULL,
  is_polyphonic  INTEGER NOT NULL DEFAULT 0,
  candidates     TEXT
)
"""
INDEX_CHAR_MAP = [
    'CREATE INDEX IF NOT EXISTS idx_hvcm_source ON hanviet_char_map(source)',
    'CREATE INDEX IF NOT EXISTS idx_hvcm_poly  ON hanviet_char_map(is_polyphonic)',
]


def cmd_apply(db_path=None):
    db = db_path or DB_PATH
    hv = extract_han_viet_char()
    dbs = load_db_sources(db)
    rows, viol = merged_char_rows(hv, dbs)
    con = sqlite3.connect(db)
    try:
        con.execute(CREATE_CHAR_MAP)
        for q in INDEX_CHAR_MAP:
            con.execute(q)
        con.executemany(
            'INSERT OR REPLACE INTO hanviet_char_map(char, reading, source, is_polyphonic, candidates) '
            'VALUES (:char, :reading, :source, :is_polyphonic, :candidates)', rows)
        con.commit()
        total = con.execute('SELECT COUNT(*) FROM hanviet_char_map').fetchone()[0]
        poly = con.execute('SELECT COUNT(*) FROM hanviet_char_map WHERE is_polyphonic=1').fetchone()[0]
        print(f'hanviet_char_map: {total:,} char (poly {poly:,})')
        if viol:
            print(f'⚠ {len(viol)} violations 1-âm-tiết:')
            for v in viol[:20]:
                print('  ', v)
    finally:
        con.close()


def cmd_revert(db_path=None):
    db = db_path or DB_PATH
    con = sqlite3.connect(db)
    try:
        con.execute('DROP TABLE IF EXISTS hanviet_char_map')
        con.commit()
        print('Dropped hanviet_char_map')
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser(description='T172 build hanviet_char_map')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--export')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--revert', action='store_true')
    args = ap.parse_args()
    if args.stats:
        cmd_stats()
    elif args.export:
        cmd_export(args.export)
    elif args.apply:
        cmd_apply()
    elif args.revert:
        cmd_revert()
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
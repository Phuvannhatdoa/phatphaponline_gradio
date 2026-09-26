"""
T05 Pass 3 — Full TTL extraction: Person + Place name resolution
================================================================
Scan toàn bộ ~2100 TTL files:
  1. Extract @vi + @zh labels từ mọi subject URI
  2. Extract (漢字) từ bio text → pair với tên Việt đứng trước
  3. Match Person → people.name_zh → update name_vi nếu syllable đúng
  4. Match Place → namevi_map_places.name_zh → update name_vi nếu syllable đúng
  5. MARCUS verify để báo cáo độ tin cậy (không bắt buộc để apply)

TTL là nguồn chuẩn tên tiếng Việt — DILA ID chỉ xác tín sử liệu.

Usage:
    python t05_ttl_pass3.py              # dry run — chỉ báo cáo
    python t05_ttl_pass3.py --apply      # apply vào DB
    python t05_ttl_pass3.py --apply --person-only   # chỉ cập nhật people
    python t05_ttl_pass3.py --apply --place-only    # chỉ cập nhật places
"""

import argparse
import os
import re
import sqlite3
from glob import glob
from html.parser import HTMLParser

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.dirname(SCRIPT_DIR)
DB         = os.path.join(BASE_DIR, 'data', 'lineage.db')
TTL_ROOT   = os.path.join(BASE_DIR, 'data', 'ttl')

# ── Config ───────────────────────────────────────────────────────────────────
PLACE_CONFIDENCE_TTL = 0.9  # upgrade từ 0.7 auto_transliterate

_VI_HONORIFIC_PREFIXES = (
    'Tôn Giả ', 'Bồ Tát ', 'Thiền Sư ', 'Đại Sư ',
    'TS ', 'HT ', 'NS ', 'Ngài ', 'Tổ ',
)

# ── Helpers ──────────────────────────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []
    def handle_data(self, d):
        self._parts.append(d)
    def get_text(self):
        return ' '.join(self._parts)


def _strip_html(text: str) -> str:
    s = _HTMLStripper()
    s.feed(text)
    return s.get_text()


def _clean_vi(text: str) -> str:
    """Strip honorific prefix và underscore (TTL slug artifact)."""
    text = text.strip().replace('_', ' ')
    for pfx in _VI_HONORIFIC_PREFIXES:
        if text.startswith(pfx):
            text = text[len(pfx):].strip()
            break
    return text


def _syllable_count(text: str) -> int:
    return len(text.strip().split()) if text and text.strip() else 0


def _zh_only(text: str) -> str:
    """Lọc chỉ lấy Hán tự (U+4E00–U+9FFF)."""
    return ''.join(c for c in text if '一' <= c <= '鿿')


def _is_vi_text(text: str) -> bool:
    """Kiểm tra text có ký tự Latin/dấu tiếng Việt (không phải Hán/Nhật)."""
    if not text or not text.strip():
        return False
    zh_chars = sum(1 for c in text if '一' <= c <= '鿿')
    if zh_chars > 0:
        return False
    latin = sum(1 for c in text if c.isalpha())
    return latin >= 2


def _is_valid_vi_name(text: str) -> bool:
    """
    Kiểm tra tên Việt hợp lệ — không có chuỗi ≥4 ký tự ASCII thuần (dấu hiệu thiếu dấu/typo).
    Ví dụ: 'Thach Sương' → reject ('Thach' = 5 ASCII), 'Thạch Sương' → accept.
    """
    return not bool(re.search(r'[a-zA-Z]{4,}', text))


# ── TTL Scanner ──────────────────────────────────────────────────────────────

# Patterns để parse TTL
_RE_SUBJECT   = re.compile(r'^<(ex:[^>]+)>\s+(?:a\s+|rdfs:label)', re.M)
_RE_LABEL_VI  = re.compile(r'rdfs:label\s+"([^"]+)"@vi')
_RE_LABEL_ZH  = re.compile(r'rdfs:label\s+"([一-鿿][^"]*)"@zh')
_RE_BIO_BLOCK = re.compile(
    r'bkg:biographicalNote\s+(?:"""(.*?)"""|"([^"]+)")@vi',
    re.S
)
# Pattern (漢字) hoặc （漢字） trong bio text
# Cũng bắt "Tên Việt (漢字, phiên âm)" — chỉ lấy phần Hán tự thuần
_RE_BIO_PAIR  = re.compile(
    r'((?:[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐŨƠƯ][a-zàáâãèéêìíòóôõùúăđũơưạảấầẩẫậắằẳẵặẹẻẽềểếệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵýỷỹ]+'
    r'(?:\s+[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐŨƠƯ][a-zàáâãèéêìíòóôõùúăđũơưạảấầẩẫậắằẳẵặẹẻẽềểếệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵýỷỹ]+)*)'
    r')\s*[（(]([一-鿿]{2,}[^)）]*)[)）]'
)


def _extract_bio_pairs(bio_raw: str) -> list[tuple[str, str]]:
    """Trả về list (vi_name, zh_name) từ bio text."""
    text = _strip_html(bio_raw)
    pairs = []
    for m in _RE_BIO_PAIR.finditer(text):
        vi_raw = m.group(1).strip()
        zh_raw = m.group(2).strip()
        # Chỉ giữ Hán tự thuần từ group 2 (loại pinyin/năm)
        zh_clean = _zh_only(zh_raw)
        if not zh_clean or len(zh_clean) < 2:
            continue
        vi_clean = _clean_vi(vi_raw)
        if _syllable_count(vi_clean) == 0:
            continue
        pairs.append((vi_clean, zh_clean))
    return pairs


def scan_ttl_file(filepath: str) -> dict:
    """
    Scan 1 TTL file → trả về:
      persons: dict zh → set of vi names
      places:  dict zh → set of vi names  (từ <ex:place/*>)
      bio_pairs: list of (vi, zh)  (từ bio text extraction)
      main_vi: tên Việt của subject chính
      main_zh: Hán tự của subject chính (nếu có)
    """
    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return {}

    result = {
        'persons':   {},  # zh → [vi, ...]
        'places':    {},  # zh → [vi, ...]
        'bio_pairs': [],  # (vi, zh)
    }

    # Tìm tất cả subject URI và label @zh / @vi pair trong cùng block
    # Chia file thành các blocks bởi subject URI
    # Đơn giản: scan toàn bộ file tìm URI + labels

    # 1. Extract all (URI, vi, zh) triplets bằng context window
    # Tìm mọi URI
    subject_positions = [(m.start(), m.group(1)) for m in re.finditer(r'<(ex:[^>]+)>', content)]

    # Với mỗi subject: lấy text đến subject tiếp theo hoặc cuối file
    for i, (pos, uri) in enumerate(subject_positions):
        end = subject_positions[i + 1][0] if i + 1 < len(subject_positions) else len(content)
        block = content[pos:end]

        vi_labels = [m.group(1) for m in _RE_LABEL_VI.finditer(block)]
        zh_labels = [_zh_only(m.group(1)) for m in _RE_LABEL_ZH.finditer(block)]
        zh_labels = [z for z in zh_labels if z]  # bỏ empty

        # Phân loại URI
        is_place  = 'ex:place/'  in uri
        is_monk   = 'ex:monk/'   in uri
        is_person = 'ex:person/' in uri

        for vi_raw in vi_labels:
            vi = _clean_vi(vi_raw)
            if not vi or _syllable_count(vi) < 1:
                continue
            if zh_labels:
                for zh in zh_labels:
                    if is_place:
                        result['places'].setdefault(zh, set()).add(vi)
                    else:
                        result['persons'].setdefault(zh, set()).add(vi)
            # vi-only (không có @zh trong block này)
            # → sẽ được xử lý qua bio_pairs hoặc name_vi_map

    # 2. Extract bio pairs
    for m in _RE_BIO_BLOCK.finditer(content):
        bio_text = m.group(1) or m.group(2) or ''
        result['bio_pairs'].extend(_extract_bio_pairs(bio_text))

    return result


def scan_all_ttl(ttl_root: str) -> tuple[dict, dict]:
    """
    Scan toàn bộ TTL → gộp:
      all_persons: zh → set of vi (từ labels + bio_pairs)
      all_places:  zh → set of vi (từ labels + bio_pairs)
    """
    all_persons: dict[str, set] = {}
    all_places:  dict[str, set] = {}

    ttl_files = glob(os.path.join(ttl_root, '**', '*.ttl'), recursive=True)
    print(f"Scanning {len(ttl_files)} TTL files...")

    for fp in ttl_files:
        r = scan_ttl_file(fp)
        if not r:
            continue

        for zh, vi_set in r.get('persons', {}).items():
            all_persons.setdefault(zh, set()).update(vi_set)

        for zh, vi_set in r.get('places', {}).items():
            all_places.setdefault(zh, set()).update(vi_set)

        # bio_pairs → classify by checking DB later; for now put in persons
        # (place URI bio_pairs sẽ có mix cả người lẫn nơi, cần match cả 2 bảng)
        for vi, zh in r.get('bio_pairs', []):
            all_persons.setdefault(zh, set()).add(vi)
            all_places.setdefault(zh, set()).add(vi)  # thử match cả place

    print(f"  → {len(all_persons)} unique Hán person candidates")
    print(f"  → {len(all_places)} unique Hán place candidates")
    return all_persons, all_places


# ── DB Indexes ───────────────────────────────────────────────────────────────

def load_people_index(conn) -> dict[str, tuple]:
    """name_zh → (id, name_vi)"""
    idx = {}
    for row in conn.execute(
        "SELECT id, name_zh, name_vi FROM people WHERE name_zh IS NOT NULL"
    ):
        pid, zh, vi = row
        if zh and zh not in idx:
            idx[zh] = (pid, vi or '')
    return idx


def load_places_index(conn) -> dict[str, tuple]:
    """name_zh → (dila_id, name_vi, confidence)  từ namevi_map_places"""
    idx = {}
    for row in conn.execute(
        "SELECT dila_id, name_zh, name_vi, confidence FROM namevi_map_places "
        "WHERE name_zh IS NOT NULL"
    ):
        dila_id, zh, vi, conf = row
        if zh and zh not in idx:
            idx[zh] = (dila_id, vi or '', conf or 0)
    return idx


def load_marcus_index(conn) -> set[str]:
    """Set of name_zh có trong MARCUS marcus_reference."""
    idx = set()
    for (label,) in conn.execute(
        "SELECT label FROM marcus_reference WHERE label IS NOT NULL"
    ):
        if label:
            idx.add(label)
    return idx


# ── Resolution Logic ─────────────────────────────────────────────────────────

def _best_vi(vi_set: set[str], zh: str) -> str | None:
    """
    Chọn tên Việt tốt nhất từ tập: ưu tiên syllable count == len(zh).
    Loại bỏ tên có chuỗi ≥4 ASCII thuần (dấu hiệu thiếu dấu/typo).
    """
    zh_len = len(zh)
    exact  = [v for v in vi_set
              if _syllable_count(v) == zh_len and _is_valid_vi_name(v)]
    if exact:
        return max(exact, key=len)
    return None


def resolve_persons(
    all_persons: dict[str, set],
    people_idx:  dict[str, tuple],
    marcus_idx:  set[str],
) -> tuple[list, list]:
    """
    Returns:
        to_apply:  [(pid, zh, old_vi, new_vi, marcus)]
        confirmed: [(pid, zh, vi, marcus)]
    """
    to_apply  = []
    confirmed = []

    for zh, vi_set in all_persons.items():
        if zh not in people_idx:
            continue
        pid, dila_vi = people_idx[zh]
        zh_len = len(zh)
        marcus = zh in marcus_idx

        best = _best_vi(vi_set, zh)
        if best is None:
            continue

        dila_syls = _syllable_count(dila_vi)

        if best == dila_vi:
            confirmed.append((pid, zh, dila_vi, marcus))
        elif _syllable_count(best) == zh_len and dila_syls == zh_len:
            to_apply.append((pid, zh, dila_vi, best, marcus))
        # else: syllable mismatch → skip

    return to_apply, confirmed


def resolve_places(
    all_places: dict[str, set],
    places_idx: dict[str, tuple],
) -> tuple[list, list]:
    """
    Returns:
        to_apply:  [(dila_id, zh, old_vi, new_vi)]
        confirmed: [(dila_id, zh, vi)]
    """
    to_apply  = []
    confirmed = []

    for zh, vi_set in all_places.items():
        if zh not in places_idx:
            continue
        dila_id, old_vi, conf = places_idx[zh]
        zh_len = len(zh)

        best = _best_vi(vi_set, zh)
        if best is None:
            continue

        old_syls = _syllable_count(old_vi)

        if best == old_vi:
            confirmed.append((dila_id, zh, old_vi))
        elif _syllable_count(best) == zh_len and old_syls == zh_len:
            to_apply.append((dila_id, zh, old_vi, best))
        # else: mismatch

    return to_apply, confirmed


# ── Apply ────────────────────────────────────────────────────────────────────

def apply_persons(conn, to_apply: list, dry_run: bool):
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"\n[PERSON] {mode}: {len(to_apply)} phiên âm cần sửa")
    for pid, zh, old, new, marcus in to_apply:
        mf = ' [MARCUS ✓]' if marcus else ''
        print(f"  [{pid}] {zh} ({len(zh)}): '{old}' → '{new}'{mf}")

    if not dry_run and to_apply:
        conn.executemany(
            "UPDATE people SET name_vi=? WHERE id=? AND name_zh=?",
            [(new, pid, zh) for pid, zh, old, new, marcus in to_apply]
        )
        conn.commit()
        print(f"  → Committed {len(to_apply)} person corrections.")


def apply_places(conn, to_apply: list, dry_run: bool):
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"\n[PLACE] {mode}: {len(to_apply)} địa danh cần cập nhật")
    for dila_id, zh, old, new in to_apply:
        print(f"  [{dila_id}] {zh} ({len(zh)}): '{old}' → '{new}'")

    if not dry_run and to_apply:
        conn.executemany(
            "UPDATE namevi_map_places SET name_vi=?, confidence=?, source=? "
            "WHERE dila_id=? AND name_zh=?",
            [(new, PLACE_CONFIDENCE_TTL, 'ttl_confirmed', dila_id, zh)
             for dila_id, zh, old, new in to_apply]
        )
        conn.commit()
        print(f"  → Committed {len(to_apply)} place name updates (confidence → {PLACE_CONFIDENCE_TTL}).")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='T05 Pass 3 — Full TTL Person + Place resolution'
    )
    parser.add_argument('--apply',       action='store_true', help='Commit changes to DB')
    parser.add_argument('--person-only', action='store_true', help='Chỉ xử lý persons')
    parser.add_argument('--place-only',  action='store_true', help='Chỉ xử lý places')
    parser.add_argument('--limit',       type=int, default=0,
                        help='Giới hạn số bản ghi báo cáo (0 = tất cả)')
    args = parser.parse_args()

    do_person = not args.place_only
    do_place  = not args.person_only

    # 1. Scan TTL
    print("=== T05 Pass 3: Full TTL scan ===")
    all_persons, all_places = scan_all_ttl(TTL_ROOT)

    # 2. Load DB indexes
    conn = sqlite3.connect(DB)
    people_idx = load_people_index(conn)
    places_idx = load_places_index(conn)
    marcus_idx = load_marcus_index(conn)
    print(f"\nDB loaded: {len(people_idx)} persons, {len(places_idx)} places, "
          f"{len(marcus_idx)} MARCUS nodes")

    # 3. Resolve persons
    if do_person:
        p_apply, p_confirmed = resolve_persons(all_persons, people_idx, marcus_idx)

        print(f"\n[PERSON] Confirmed (DILA đúng): {len(p_confirmed)}")
        limit = args.limit or len(p_confirmed)
        for pid, zh, vi, marcus in p_confirmed[:limit]:
            mf = ' [MARCUS ✓]' if marcus else ''
            print(f"  [{pid}] {zh} → '{vi}'{mf}")
        if len(p_confirmed) > limit:
            print(f"  ... và {len(p_confirmed) - limit} dòng nữa")

        apply_persons(conn, p_apply, dry_run=not args.apply)

    # 4. Resolve places
    if do_place:
        pl_apply, pl_confirmed = resolve_places(all_places, places_idx)

        print(f"\n[PLACE] Confirmed (name_vi đúng): {len(pl_confirmed)}")
        limit = args.limit or len(pl_confirmed)
        for dila_id, zh, vi in pl_confirmed[:limit]:
            print(f"  [{dila_id}] {zh} → '{vi}'")
        if len(pl_confirmed) > limit:
            print(f"  ... và {len(pl_confirmed) - limit} dòng nữa")

        apply_places(conn, pl_apply, dry_run=not args.apply)

    # 5. Summary
    print("\n=== SUMMARY ===")
    if do_person:
        print(f"  Person confirmed:  {len(p_confirmed)}")
        print(f"  Person to_apply:   {len(p_apply)}")
    if do_place:
        print(f"  Place confirmed:   {len(pl_confirmed)}")
        print(f"  Place to_apply:    {len(pl_apply)}")

    conn.close()


if __name__ == '__main__':
    main()

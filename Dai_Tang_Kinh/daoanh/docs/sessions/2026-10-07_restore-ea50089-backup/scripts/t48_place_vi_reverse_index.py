"""
T48 — Place VI_NAME Reverse Index từ Lexicon Definitions

Khai thác pairs (漢字 → Tiếng Việt) từ structure của lexicon:
  - lexicon.term  = tên tiếng Việt (đây là KEY)
  - lexicon.definition bắt đầu bằng "(漢字, romanization):" → extract hanzi

Nếu hanzi khớp places_dila.name_zh → update zqlocal_content với tên lexicon.
Đây là bổ sung cho T47: T47 xác nhận tên tồn tại trong lexicon, T48 sửa tên sai bằng tên lexicon.

Số liệu thực đo 2026-08-27:
  - Pairs extracted: 2,151
  - Match với DILA places: 130
  - Upgrade candidates (conf<0.75, tên khác): 50 safe + 2 risky (filtered)
  - Systematic errors fixed: 水→Héo→Thủy, 蓮→Sen→Liên, 澤→Rạch→Trạch

Usage:
    python scripts/t48_place_vi_reverse_index.py              # dry-run
    python scripts/t48_place_vi_reverse_index.py --apply      # apply
    python scripts/t48_place_vi_reverse_index.py --review     # in ra tất cả để review

Revert:
    cp docs/sessions/2026-08-27/lineage_pre_T48.db.bak data/lineage.db
"""
import sqlite3
import re
import sys
import io
import os
import json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--apply' not in sys.argv
REVIEW  = '--review' in sys.argv

# Pattern: definition bắt đầu bằng (漢字, romanization): hoặc (漢字):
PAT_LEADING = re.compile(r'^\s*[（(]([一-鿿]{2,15})[，,）)\s]')

# Từ khóa person markers (lọc ra lexicon terms thực chất là tên người)
PERSON_MARKERS = [
    'Hòa Thượng', 'Thiền Sư', 'Đại Sư', 'Tổ Sư', 'Ngài', 'Pháp Sư',
    'Quốc Sư', 'Luật Sư', 'Đạo Phi', 'Đạo Túng', 'Huệ Lăng', 'Đại Hòa',
    'Thượng Nhân', 'Tiền Bối',
]

# Place suffixes: nếu tên VN kết thúc bằng 1 trong các suffix này → confident
PLACE_SUFFIXES = [
    'Tự', 'Viện', 'Sơn', 'Am', 'Trì', 'Hải', 'Tháp', 'Miếu', 'Đình',
    'Cung', 'Thành', 'Đàn', 'Châu', 'Phủ', 'Hồ', 'Nham', 'Động', 'Cốc',
    'Phong', 'Trù', 'Môn', 'Kinh', 'Quan', 'Đàng', 'Quốc',
]


def has_person_marker(name: str) -> bool:
    return any(m in name for m in PERSON_MARKERS)


def has_place_suffix(name: str) -> bool:
    parts = name.strip().split()
    if not parts:
        return False
    last = parts[-1]
    return last in PLACE_SUFFIXES


def extract_pairs(conn) -> dict:
    """Extract (hanzi → viet_name) pairs từ lexicon.term + definition."""
    pairs = {}
    cur = conn.execute("""
        SELECT term, definition
        FROM lexicon
        WHERE definition IS NOT NULL
          AND length(trim(term)) > 2
    """)
    for term, defn in cur.fetchall():
        if not defn or not term:
            continue
        m = PAT_LEADING.match(defn)
        if not m:
            continue
        hanzi = m.group(1)
        viet  = term.strip()
        if len(viet.split()) < 2:   # require ≥2 âm tiết
            continue
        if has_person_marker(viet):  # lọc tên người
            continue
        if hanzi not in pairs:
            pairs[hanzi] = {}
        pairs[hanzi][viet] = pairs[hanzi].get(viet, 0) + 1
    return pairs


def main():
    mode = "DRY-RUN" if DRY_RUN else "APPLY"
    if REVIEW:
        mode = "REVIEW"
    print(f"=== T48 Place VI_NAME Reverse Index [{mode}] ===")
    print(f"DB: {DB_PATH}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # ── Bước 1: Extract pairs từ lexicon ─────────────────────────────────
    print("Bước 1: Extract (漢字 → Việt) pairs từ lexicon...")
    raw_pairs = extract_pairs(conn)
    # Chọn tên phổ biến nhất cho mỗi hanzi
    best_pairs = {zh: max(vd, key=lambda v: vd[v]) for zh, vd in raw_pairs.items()}
    print(f"  {len(best_pairs):,} unique hanzi → viet pairs")
    print()

    # ── Bước 2: Match với DILA places ────────────────────────────────────
    print("Bước 2: Match với places_dila.name_zh...")
    cur = conn.execute("SELECT id, name_zh FROM places_dila WHERE name_zh IS NOT NULL AND name_zh != ''")
    dila_map = {row[1]: row[0] for row in cur.fetchall()}
    dila_matches = [(zh, best_pairs[zh], dila_map[zh]) for zh in best_pairs if zh in dila_map]
    print(f"  {len(dila_matches):,} pairs match DILA places")
    print()

    # ── Bước 3: Check vs zqlocal_content ─────────────────────────────────
    print("Bước 3: So sánh với zqlocal_content hiện tại...")
    cur2 = conn.execute("""
        SELECT id, entity_id, content, confidence
        FROM zqlocal_content
        WHERE content_type = 'VI_NAME'
    """)
    zq_map = {row[1]: (row[0], row[2], row[3]) for row in cur2.fetchall()}

    # Candidates: tên khác nhau + conf < 0.75
    candidates = []
    for zh, viet, dila_id in dila_matches:
        if dila_id not in zq_map:
            continue
        zq_id, cur_content, cur_conf = zq_map[dila_id]
        if not cur_content:
            continue
        if cur_content.lower() == viet.lower():
            continue                    # T47 đã xử lý / tên giống nhau
        # Unicode normalization check: chỉ khác accent encoding → skip
        import unicodedata
        def strip_accents(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s)
                           if unicodedata.category(c) != 'Mn').lower()
        if unicodedata.normalize('NFC', cur_content) == unicodedata.normalize('NFC', viet):
            continue
        # Same word after stripping all tonal marks → just orthographic variant, skip
        if strip_accents(cur_content) == strip_accents(viet):
            continue
        if float(cur_conf) >= 0.75:
            continue                    # đã được verified
        # Không downgrade tên có suffix thành tên không có suffix
        if has_place_suffix(cur_content) and not has_place_suffix(viet):
            continue
        with_suffix = has_place_suffix(viet)

        candidates.append({
            'zq_id':       zq_id,
            'dila_id':     dila_id,
            'hanzi':       zh,
            'lexicon_viet': viet,
            'current_viet': cur_content,
            'current_conf': cur_conf,
            'has_suffix':  with_suffix,
        })

    suffix_ok  = [c for c in candidates if c['has_suffix']]
    no_suffix  = [c for c in candidates if not c['has_suffix']]
    print(f"  Upgrade candidates (conf<0.75, tên khác): {len(candidates)}")
    print(f"    → Có place suffix (sẽ update → conf=0.75): {len(suffix_ok)}")
    print(f"    → Không có suffix (sẽ update → conf=0.72, admin review): {len(no_suffix)}")
    print()

    # ── Preview ───────────────────────────────────────────────────────────
    print("Mẫu updates (suffix ok → 0.75):")
    for c in suffix_ok[:10]:
        print(f"  {c['hanzi']} | {c['current_viet']!r} → {c['lexicon_viet']!r}")
    print()
    print("Mẫu updates (không suffix → 0.72, cần review):")
    for c in no_suffix[:10]:
        print(f"  {c['hanzi']} | {c['current_viet']!r} → {c['lexicon_viet']!r}")
    print()

    # ── Review mode: dump JSON ─────────────────────────────────────────────
    if REVIEW:
        out_path = os.path.join(BASE, '..', 'data', 't48_review_candidates.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'total': len(candidates),
                'suffix_ok': suffix_ok,
                'no_suffix': no_suffix,
            }, f, ensure_ascii=False, indent=2)
        print(f"[REVIEW] Exported {len(candidates)} candidates → {out_path}")
        conn.close()
        return

    # ── Apply ─────────────────────────────────────────────────────────────
    if DRY_RUN:
        print("[DRY-RUN] Không thay đổi DB.")
        print(f"Chạy lại với --apply để update {len(candidates)} entries.")
        print(f"Chạy lại với --review để export JSON admin review.")
        conn.close()
        return

    print("Bước 4: Applying updates...")

    # Suffix ok: conf=0.75
    if suffix_ok:
        conn.executemany("""
            UPDATE zqlocal_content
            SET content = ?,
                confidence = '0.75',
                generated_by = 't48_lexicon_term'
            WHERE id = ? AND confidence < '0.75'
        """, [(c['lexicon_viet'], c['zq_id']) for c in suffix_ok])
        print(f"  Updated {len(suffix_ok)} entries → conf=0.75 (place suffix verified)")

    # No suffix: conf=0.72 (admin review flag)
    if no_suffix:
        conn.executemany("""
            UPDATE zqlocal_content
            SET content = ?,
                confidence = '0.72',
                generated_by = 't48_lexicon_nsfx_review'
            WHERE id = ? AND confidence < '0.72'
        """, [(c['lexicon_viet'], c['zq_id']) for c in no_suffix])
        print(f"  Updated {len(no_suffix)} entries → conf=0.72 (needs admin review)")

    conn.commit()

    # ── Verify ────────────────────────────────────────────────────────────
    print()
    print("=== zqlocal_content sau T48 ===")
    cur3 = conn.execute("""
        SELECT confidence, COUNT(*), COUNT(DISTINCT entity_id)
        FROM zqlocal_content WHERE content_type='VI_NAME'
        GROUP BY confidence ORDER BY CAST(confidence AS REAL) DESC
    """)
    total_places = 59167
    for conf, cnt, uniq in cur3.fetchall():
        print(f"  conf={conf}: {cnt:7,} entries | {uniq:,} places ({uniq/total_places*100:.1f}%)")

    print()
    print(f"[DONE] {len(candidates)} entries updated")
    print(f"Revert: cp docs/sessions/2026-08-27/lineage_pre_T48.db.bak data/lineage.db")
    conn.close()


if __name__ == "__main__":
    main()

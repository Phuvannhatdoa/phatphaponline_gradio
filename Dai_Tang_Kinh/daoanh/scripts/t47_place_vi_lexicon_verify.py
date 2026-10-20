"""
T47 — Place VI_NAME Verification via Lexicon Cross-Reference

Kiểm tra 116,514 VI_NAME entries (conf=0.65) trong zqlocal_content
đối chiếu với 166,278 entries trong 22 bộ từ điển Phật giáo Việt Nam.

Nếu tên VN auto-generated khớp EXACT với lexicon.term → upgrade confidence:
  - 1 từ điển xác nhận  → conf 0.65 → 0.75
  - ≥2 từ điển xác nhận → conf 0.65 → 0.85

Số liệu thực đo 2026-08-27:
  - conf=0.65 entries: 116,514
  - Exact match 1 nguồn: 4,038 (3.5%)
  - Exact match ≥2 nguồn: 1,935 (1.7%)
  - Tổng matchable: 5,973 (5.1%)

Usage:
    python scripts/t47_place_vi_lexicon_verify.py              # dry-run
    python scripts/t47_place_vi_lexicon_verify.py --apply      # apply

Revert:
    cp docs/sessions/2026-08-27/lineage_pre_T47.db.bak data/lineage.db
"""
import sqlite3
import sys
import io
import os
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--apply' not in sys.argv


def build_lexicon_index(conn):
    """Load lexicon.term → set of source names (normalized, case-insensitive)."""
    cur = conn.execute("""
        SELECT LOWER(TRIM(term)), source
        FROM lexicon
        WHERE length(term) > 2
          AND term NOT LIKE '%(%'
          AND term NOT LIKE '%[%'
          AND term IS NOT NULL
    """)
    index = {}
    for norm, src in cur.fetchall():
        if norm not in index:
            index[norm] = set()
        index[norm].add(src)
    return index


def main():
    mode = "DRY-RUN" if DRY_RUN else "APPLY"
    print(f"=== T47 Place VI_NAME Lexicon Verification [{mode}] ===")
    print(f"DB: {DB_PATH}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # ── Bước 1: Build lexicon index ──────────────────────────────────────
    print("Bước 1: Load lexicon index...")
    lexicon = build_lexicon_index(conn)
    print(f"  {len(lexicon):,} unique normalized terms từ 22 từ điển")
    print()

    # ── Bước 2: Load zqlocal entries cần verify ─────────────────────────
    # Chỉ xử lý conf=0.65 (T49 cleaned) — KHÔNG downgrade conf=0.75/0.8/0.9
    print("Bước 2: Load zqlocal_content entries (conf=0.65)...")
    cur = conn.execute("""
        SELECT id, entity_id, content
        FROM zqlocal_content
        WHERE content_type = 'VI_NAME'
          AND confidence = '0.65'
    """)
    entries = cur.fetchall()
    print(f"  {len(entries):,} entries at conf=0.65")
    print()

    # ── Bước 3: Match ────────────────────────────────────────────────────
    print("Bước 3: Matching against lexicon...")
    single_src = []   # (id, content, src_list) → conf 0.75
    multi_src  = []   # (id, content, src_list) → conf 0.85
    no_match   = 0

    for row_id, entity_id, content in entries:
        if not content:
            no_match += 1
            continue
        norm = content.lower().strip()
        if norm in lexicon:
            srcs = lexicon[norm]
            src_str = '|'.join(sorted(srcs))
            if len(srcs) >= 2:
                multi_src.append((row_id, content, src_str))
            else:
                single_src.append((row_id, content, src_str))
        else:
            no_match += 1

    total_match = len(single_src) + len(multi_src)
    print(f"  No match:                  {no_match:,} ({no_match/len(entries)*100:.1f}%)")
    print(f"  Match 1 source  → 0.75:   {len(single_src):,} ({len(single_src)/len(entries)*100:.1f}%)")
    print(f"  Match ≥2 sources → 0.85:  {len(multi_src):,}  ({len(multi_src)/len(entries)*100:.1f}%)")
    print(f"  Total matchable:           {total_match:,} ({total_match/len(entries)*100:.1f}%)")
    print()

    # Sample preview
    print("Sample → conf=0.85 (≥2 nguồn):")
    for row_id, content, srcs in multi_src[:5]:
        src_list = srcs.split('|')
        print(f"  {content!r}  [{', '.join(s[:30] for s in src_list[:2])}{',...' if len(src_list)>2 else ''}]")
    print()
    print("Sample → conf=0.75 (1 nguồn):")
    for row_id, content, srcs in single_src[:5]:
        print(f"  {content!r}  [{srcs[:50]}]")
    print()

    # ── Bước 4: Apply ────────────────────────────────────────────────────
    if DRY_RUN:
        print("[DRY-RUN] Không thay đổi DB.")
        print()
        print("Summary nếu apply:")
        print(f"  zqlocal_content conf 0.65→0.75: {len(single_src):,}")
        print(f"  zqlocal_content conf 0.65→0.85: {len(multi_src):,}")
        print(f"  Tổng verified: {total_match:,}")
        print()
        print("Chạy lại với --apply để thực thi.")
        conn.close()
        return

    print("Bước 4: Applying updates...")

    # Update conf 0.65 → 0.75 (1 source)
    if single_src:
        conn.executemany("""
            UPDATE zqlocal_content
            SET confidence = '0.75',
                generated_by = 't47_lexicon_1src'
            WHERE id = ? AND confidence = '0.65'
        """, [(row_id,) for row_id, _, _ in single_src])
        print(f"  Updated {len(single_src):,} entries → conf=0.75")

    # Update conf 0.65 → 0.85 (≥2 sources)
    if multi_src:
        conn.executemany("""
            UPDATE zqlocal_content
            SET confidence = '0.85',
                generated_by = 't47_lexicon_2src'
            WHERE id = ? AND confidence = '0.65'
        """, [(row_id,) for row_id, _, _ in multi_src])
        print(f"  Updated {len(multi_src):,} entries → conf=0.85")

    conn.commit()

    # ── Verify ───────────────────────────────────────────────────────────
    print()
    print("=== zqlocal_content sau T47 ===")
    cur2 = conn.execute("""
        SELECT confidence, COUNT(*), COUNT(DISTINCT entity_id)
        FROM zqlocal_content WHERE content_type='VI_NAME'
        GROUP BY confidence ORDER BY CAST(confidence AS REAL) DESC
    """)
    total_places = 59167
    for conf, cnt, uniq in cur2.fetchall():
        print(f"  conf={conf}: {cnt:7,} entries | {uniq:,} places ({uniq/total_places*100:.1f}%)")

    print()
    print(f"[DONE]")
    print(f"Revert: cp docs/sessions/2026-08-27/lineage_pre_T47.db.bak data/lineage.db")
    conn.close()


if __name__ == "__main__":
    main()

"""T63 — Person Bio VI Phase 1: Lexicon TU SĨ direct match.

Tạo bản thảo bio tiếng Việt (bio_vi_draft) cho thiền sư/tăng ni bằng cách
match tên Việt (people.name_vi) với entries entity_type='TU SĨ' trong lexicon.

Sau T62 bulk name fix: ~851 direct exact matches (tăng từ 437 vì tên đúng hơn).

⚠️ KHÔNG copy nguyên văn từ điển vào bio_vi production.
   Table person_bio_vi_draft là bản nháp để admin tổng hợp, viết lại.

Usage:
  python t63_bio_vi_lexicon_p1.py               # dry-run: count + top 20 mẫu
  python t63_bio_vi_lexicon_p1.py --apply       # tạo/update bảng person_bio_vi_draft
  python t63_bio_vi_lexicon_p1.py --apply --copy-approved  # copy approved drafts → people.bio_vi
"""
import sys, io, os, argparse, sqlite3
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(BASE, 'data', 'lineage.db')


def ensure_draft_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS person_bio_vi_draft (
        person_id    TEXT PRIMARY KEY,
        name_vi      TEXT,
        name_zh      TEXT,
        bio_vi_draft TEXT,
        source_lex_id INTEGER,
        source_term  TEXT,
        source_name  TEXT,
        match_type   TEXT DEFAULT 'exact_term',
        char_count   INTEGER,
        admin_approved INTEGER DEFAULT 0,
        admin_note   TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_pbvd_approved ON person_bio_vi_draft(admin_approved);
    CREATE INDEX IF NOT EXISTS idx_pbvd_name ON person_bio_vi_draft(name_vi);
    """)
    conn.commit()


def find_matches(conn):
    """Match people.name_vi = lexicon.term WHERE entity_type='TU SĨ'.
    Nếu nhiều entry cho cùng 1 tên → lấy cái định nghĩa dài nhất.
    """
    sql = """
    SELECT
        p.id            AS person_id,
        p.name_vi       AS name_vi,
        p.name_zh       AS name_zh,
        l.id            AS lex_id,
        l.term          AS lex_term,
        l.source        AS lex_source,
        l.definition    AS definition,
        LENGTH(l.definition) AS def_len
    FROM people p
    JOIN lexicon l ON l.term = p.name_vi
    WHERE l.entity_type = 'TU SĨ'
      AND l.definition  IS NOT NULL
      AND LENGTH(l.definition) > 30
      AND p.name_vi     IS NOT NULL
    ORDER BY p.id, def_len DESC
    """
    rows = conn.execute(sql).fetchall()

    # Dedup: giữ entry dài nhất cho mỗi person
    seen = {}
    for row in rows:
        pid = row[0]
        if pid not in seen or row[7] > seen[pid][7]:
            seen[pid] = row
    return list(seen.values())


def apply_matches(conn, matches, verbose=False):
    now = datetime.now().isoformat(timespec='seconds')
    inserted = updated = 0
    for m in matches:
        pid, name_vi, name_zh, lex_id, lex_term, lex_source, definition, def_len = m

        # Truncate draft ở 2000 chars để tránh quá lớn; admin có thể xem full nếu cần
        draft = definition[:2000] if definition else ''

        try:
            conn.execute("""
                INSERT INTO person_bio_vi_draft
                    (person_id, name_vi, name_zh, bio_vi_draft, source_lex_id,
                     source_term, source_name, match_type, char_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'exact_term', ?, ?, ?)
            """, (pid, name_vi, name_zh, draft, lex_id, lex_term, lex_source,
                  len(draft), now, now))
            inserted += 1
        except sqlite3.IntegrityError:
            # Đã tồn tại — update nếu draft dài hơn
            existing = conn.execute(
                "SELECT char_count FROM person_bio_vi_draft WHERE person_id=?", (pid,)
            ).fetchone()
            if existing and len(draft) > existing[0]:
                conn.execute("""
                    UPDATE person_bio_vi_draft
                    SET bio_vi_draft=?, source_lex_id=?, source_term=?, source_name=?,
                        char_count=?, updated_at=?
                    WHERE person_id=? AND admin_approved=0
                """, (draft, lex_id, lex_term, lex_source, len(draft), now, pid))
                updated += 1

        if verbose:
            print(f'  [{pid}] {name_vi} ({name_zh}) — {lex_source[:40]} len={len(draft)}')

    conn.commit()
    return inserted, updated


def copy_approved(conn):
    """Copy admin-approved drafts → people.bio_vi."""
    approved = conn.execute("""
        SELECT person_id, bio_vi_draft FROM person_bio_vi_draft
        WHERE admin_approved=1
    """).fetchall()
    copied = 0
    for pid, draft in approved:
        conn.execute("UPDATE people SET bio_vi=? WHERE id=? AND (bio_vi IS NULL OR bio_vi='')",
                     (draft, pid))
        copied += conn.execute('SELECT changes()').fetchone()[0]
    conn.commit()
    return copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',          action='store_true')
    parser.add_argument('--verbose',        action='store_true')
    parser.add_argument('--copy-approved',  action='store_true',
                        help='Copy admin-approved drafts → people.bio_vi')
    args = parser.parse_args()

    dry_run = not args.apply

    conn = sqlite3.connect(DB)

    if args.apply or args.copy_approved:
        ensure_draft_table(conn)

    print(f'{"[DRY RUN] " if dry_run else "[APPLY] "}T63 Bio VI Lexicon Phase 1')
    print('Finding people.name_vi matches in lexicon TU SĨ...\n')

    matches = find_matches(conn)
    print(f'Exact matches (TU SĨ): {len(matches)} persons\n')

    # Stats
    lengths = sorted([m[7] for m in matches], reverse=True)
    if lengths:
        print(f'Definition length — max: {lengths[0]:,} | median: {lengths[len(lengths)//2]:,} | avg: {sum(lengths)//len(lengths):,}')

    # Mẫu top 20
    print('\nTop 20 matches (dài nhất):')
    print(f'  {"person_id":<12} {"name_vi":<25} {"chars":>6}  source')
    print(f'  {"─"*12} {"─"*25} {"─"*6}  {"─"*40}')
    for m in matches[:20]:
        pid, name_vi, name_zh, lex_id, lex_term, lex_source, defn, def_len = m
        print(f'  {pid:<12} {name_vi:<25} {def_len:>6}  {lex_source[:40]}')

    if dry_run:
        print(f'\n(Chạy --apply để tạo bảng person_bio_vi_draft với {len(matches)} rows)')
        conn.close()
        return

    inserted, updated = apply_matches(conn, matches, args.verbose)
    print(f'\nInserted: {inserted} | Updated: {updated}')

    # Summary stats
    total = conn.execute('SELECT count(*) FROM person_bio_vi_draft').fetchone()[0]
    avg_len = conn.execute('SELECT avg(char_count) FROM person_bio_vi_draft').fetchone()[0]
    approved = conn.execute('SELECT count(*) FROM person_bio_vi_draft WHERE admin_approved=1').fetchone()[0]
    print(f'person_bio_vi_draft: {total} total rows | avg {avg_len:.0f} chars | {approved} approved')

    if args.copy_approved:
        copied = copy_approved(conn)
        print(f'Copied {copied} approved drafts → people.bio_vi')

    conn.close()
    print('\nDone.')


if __name__ == '__main__':
    main()

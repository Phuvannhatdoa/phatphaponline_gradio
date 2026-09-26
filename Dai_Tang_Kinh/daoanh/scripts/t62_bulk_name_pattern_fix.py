"""T62 — Bulk pattern fix cho person name_vi.

Sửa 5 lỗi phiên âm hệ thống trong 48,673 persons:
  慧 → Huệ  (convention PG VN, không phải Tuệ)
  正 → Chánh (convention PG VN, không phải Chính)
  澄 → Trừng (phiên âm đúng, không phải Chừng)
  金剛 → Kim Cang (chuẩn PG, không phải Kim Cương)
  染 → Nhiễm (đúng, không phải Nhuộm)

Usage:
  python t62_bulk_name_pattern_fix.py                      # dry-run, xem count + danh sách 30 đầu
  python t62_bulk_name_pattern_fix.py --apply              # thực sự update DB
  python t62_bulk_name_pattern_fix.py --pattern hue        # chỉ xem/fix pattern 慧→Huệ
  python t62_bulk_name_pattern_fix.py --apply --verbose    # in mọi thay đổi
  python t62_bulk_name_pattern_fix.py --apply --log data/t62_fix_log.json
"""
import sys, io, os, re, json, argparse, sqlite3
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(BASE, 'data', 'lineage.db')

# ---------------------------------------------------------------------------
# 5 patterns: (id, zh_char, vi_wrong_re, vi_correct_fn, description)
# zh_char: ký tự Hán cần có trong name_zh để kích hoạt pattern
# vi_wrong_re: regex khớp phần sai trong name_vi
# vi_correct_fn: hàm (name_vi) → name_vi đã sửa
# ---------------------------------------------------------------------------
PATTERNS = [
    {
        'id': 'hue',
        'zh_char': '慧',
        'desc': '慧→Huệ (convention PG VN)',
        'wrong_re': re.compile(r'Tuệ(?=\s|$)'),
        'fix': lambda v: re.sub(r'Tuệ(?=\s|$)', 'Huệ', v),
    },
    {
        'id': 'chanh',
        'zh_char': '正',
        'desc': '正→Chánh (convention PG VN)',
        'wrong_re': re.compile(r'Chính(?=\s|$)'),
        'fix': lambda v: re.sub(r'Chính(?=\s|$)', 'Chánh', v),
    },
    {
        'id': 'trung',
        'zh_char': '澄',
        'desc': '澄→Trừng (phiên âm đúng)',
        'wrong_re': re.compile(r'Chừng(?=\s|$)'),
        'fix': lambda v: re.sub(r'Chừng(?=\s|$)', 'Trừng', v),
    },
    {
        'id': 'kimcang',
        'zh_char': '金剛',
        'desc': '金剛→Kim Cang (chuẩn PG)',
        'wrong_re': re.compile(r'Kim Cương'),
        'fix': lambda v: v.replace('Kim Cương', 'Kim Cang'),
    },
    {
        'id': 'nhiem',
        'zh_char': '染',
        'desc': '染→Nhiễm (phiên âm đúng)',
        'wrong_re': re.compile(r'Nhuộm(?=\s|$)'),
        'fix': lambda v: re.sub(r'Nhuộm(?=\s|$)', 'Nhiễm', v),
    },
]


def get_already_applied(conn):
    """Tập hợp person_id đã được T62 apply (tránh double-fix)."""
    try:
        rows = conn.execute(
            "SELECT person_id FROM person_name_correction WHERE source='bulk_pattern_T62' AND status='applied'"
        ).fetchall()
        return {r[0] for r in rows}
    except sqlite3.OperationalError:
        return set()


def ensure_correction_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS person_name_correction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NOT NULL,
        name_zh TEXT,
        current_vi TEXT,
        proposed_vi TEXT,
        source TEXT DEFAULT 'lexicon',
        is_clear INTEGER DEFAULT 0,
        clear_reason TEXT,
        dict_frequency INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        reviewed_by TEXT,
        reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(person_id, proposed_vi)
    );
    CREATE INDEX IF NOT EXISTS idx_pnc_person ON person_name_correction(person_id);
    CREATE INDEX IF NOT EXISTS idx_pnc_status ON person_name_correction(status);
    CREATE INDEX IF NOT EXISTS idx_pnc_source ON person_name_correction(source);
    """)
    conn.commit()


def find_candidates(conn, pat, already_applied):
    """Tìm tất cả người khớp pattern và chưa được fix."""
    zh = pat['zh_char']
    # Query tất cả người có ký tự Hán này trong name_zh
    like_clause = '%' + zh + '%'
    rows = conn.execute(
        "SELECT id, name_zh, name_vi, dynasty FROM people WHERE name_zh LIKE ? AND name_vi IS NOT NULL",
        (like_clause,)
    ).fetchall()

    candidates = []
    for pid, name_zh, name_vi, dynasty in rows:
        if pid in already_applied:
            continue
        if not pat['wrong_re'].search(name_vi):
            continue
        new_vi = pat['fix'](name_vi)
        if new_vi == name_vi:
            continue
        candidates.append({
            'person_id': pid,
            'name_zh': name_zh,
            'old_vi': name_vi,
            'new_vi': new_vi,
            'dynasty': dynasty or '',
            'pattern': pat['id'],
            'desc': pat['desc'],
        })
    return candidates


def apply_candidates(conn, candidates, dry_run, verbose):
    """Update people.name_vi và log vào person_name_correction."""
    now = datetime.now().isoformat(timespec='seconds')
    updated = 0
    for c in candidates:
        if not dry_run:
            conn.execute(
                "UPDATE people SET name_vi = ? WHERE id = ? AND name_vi = ?",
                (c['new_vi'], c['person_id'], c['old_vi'])
            )
            # Log vào person_name_correction
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO person_name_correction
                        (person_id, name_zh, current_vi, proposed_vi, source, is_clear, clear_reason, status, created_at)
                    VALUES (?, ?, ?, ?, 'bulk_pattern_T62', 1, ?, 'applied', ?)
                """, (c['person_id'], c['name_zh'], c['old_vi'], c['new_vi'], c['desc'], now))
            except sqlite3.IntegrityError:
                pass
            updated += 1
        if verbose or dry_run:
            prefix = '  DRY' if dry_run else '  UPD'
            print(f"{prefix} [{c['person_id']}] {c['name_zh']} ({c['dynasty']}): {c['old_vi']!r} → {c['new_vi']!r}")
    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',   action='store_true', help='Thực sự update DB (mặc định dry-run)')
    parser.add_argument('--pattern', type=str, default=None,
                        help='Chỉ chạy pattern: hue|chanh|trung|kimcang|nhiem')
    parser.add_argument('--verbose', action='store_true', help='In mọi thay đổi trong --apply mode')
    parser.add_argument('--log',     type=str, default=None, help='Lưu JSON log ra file')
    args = parser.parse_args()

    dry_run = not args.apply

    conn = sqlite3.connect(DB)
    ensure_correction_table(conn)
    already_applied = get_already_applied(conn)

    # Filter patterns nếu --pattern được chỉ định
    active_pats = [p for p in PATTERNS if args.pattern is None or p['id'] == args.pattern]
    if not active_pats:
        print(f'Pattern {args.pattern!r} không tồn tại. Chọn: {[p["id"] for p in PATTERNS]}')
        conn.close(); return

    print(f'{"[DRY RUN] " if dry_run else "[APPLY] "}T62 Bulk Pattern Fix — {len(active_pats)} pattern(s)')
    print(f'Already applied (skip): {len(already_applied)} persons\n')

    all_candidates = []
    total_updated = 0

    for pat in active_pats:
        candidates = find_candidates(conn, pat, already_applied)
        all_candidates.extend(candidates)

        prefix = '  DRY' if dry_run else '  >>>'
        print(f'{prefix} {pat["desc"]}: {len(candidates)} persons')

        if len(candidates) == 0:
            continue

        # Dry-run: in mẫu 10 đầu
        if dry_run:
            for c in candidates[:10]:
                print(f'       [{c["person_id"]}] {c["name_zh"]} ({c["dynasty"]}): {c["old_vi"]!r} → {c["new_vi"]!r}')
            if len(candidates) > 10:
                print(f'       ... và {len(candidates)-10} trường hợp khác')

        # Apply
        updated = apply_candidates(conn, candidates, dry_run, args.verbose)
        total_updated += updated

    print(f'\n{"─"*55}')
    print(f'TỔNG: {len(all_candidates)} candidates tìm thấy')
    if not dry_run:
        conn.commit()
        print(f'ĐÃ UPDATE: {total_updated} persons')
        # Verify nhanh
        remaining_tue = conn.execute("SELECT count(*) FROM people WHERE name_vi LIKE 'Tuệ %'").fetchone()[0]
        remaining_chinh = conn.execute("SELECT count(*) FROM people WHERE name_vi LIKE 'Chính %'").fetchone()[0]
        remaining_chunng = conn.execute("SELECT count(*) FROM people WHERE name_vi LIKE '%Chừng%'").fetchone()[0]
        print(f'Verify còn lại: Tuệ*={remaining_tue}, Chính*={remaining_chinh}, *Chừng*={remaining_chunng}')
    else:
        print(f'(Chạy --apply để thực sự update DB)')

    # JSON log
    if args.log and all_candidates:
        os.makedirs(os.path.dirname(args.log) if os.path.dirname(args.log) else '.', exist_ok=True)
        with open(args.log, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'dry_run': dry_run,
                'total': len(all_candidates),
                'applied': total_updated,
                'changes': all_candidates,
            }, f, ensure_ascii=False, indent=2)
        print(f'Log: {args.log}')

    conn.close()
    print('Done.')


if __name__ == '__main__':
    main()

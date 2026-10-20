"""
T186 — ETL: Tạo bảng ttl_persons cho danh tăng VN chỉ có trong TTL local
(không có trong DILA people table)

Mục đích:
  Hệ thống hóa danh tăng Việt Nam từ tài liệu sưu tầm rải rác (TTL files).
  Dữ liệu này KHÔNG có trong DILA (kho quốc tế) — chỉ có trong ontology
  tiếng Việt do cộng đồng Phật học VN biên soạn.

Các bước:
  P1 — Tạo bảng ttl_persons (additive, không ALTER bảng cũ)
  P2 — Populate từ slugs TTL không có DILA ID
  P3 — Bridge TTL-only edges vào lineage_edge_assertions
  P4 — Insert TTL-only edges vào lineage_edge_consensus (is_default_visible=0)

Dùng:
  python scripts/etl_ttl_persons.py --dry-run      # xem sẽ làm gì
  python scripts/etl_ttl_persons.py --apply        # chạy thật
  python scripts/etl_ttl_persons.py --apply --phase 1   # chỉ phase 1

Rollback:
  DELETE FROM lineage_edge_consensus WHERE source_marker='TTL_VN_ONLY';
  DELETE FROM lineage_edge_assertions WHERE source_code='TTL' AND ref LIKE 'VN_%';
  DROP TABLE IF EXISTS ttl_persons;
"""
import sqlite3, sys, io, os, argparse, json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
TTL_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ttl')

NOTE_VN = (
    "Danh tăng Việt Nam — sưu tầm từ tài liệu local TTL tiếng Việt. "
    "Chưa có trong kho dữ liệu quốc tế DILA. "
    "Hệ thống hóa quan hệ truyền thừa Thiền Tông VN."
)


def fix_enc(s):
    if not s:
        return s
    return s.replace('Ð', 'Đ').replace('ð', 'đ')


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ──────────────────────────────────────────────
# PHASE 1 — Tạo bảng ttl_persons
# ──────────────────────────────────────────────
CREATE_TTL_PERSONS = """
CREATE TABLE IF NOT EXISTS ttl_persons (
    id          TEXT PRIMARY KEY,   -- slug gốc từ TTL (VD: bach_van_khong_do)
    name_vi     TEXT NOT NULL,      -- Tên tiếng Việt
    name_zh     TEXT DEFAULT '',    -- Hán tự nếu có
    slug        TEXT,               -- slug gốc TTL (bằng id)
    source      TEXT DEFAULT 'TTL_LOCAL',
    note        TEXT,               -- ghi chú nguồn
    data_quality TEXT DEFAULT 'unverified',
                                    -- unverified / reviewed / confirmed
    created_at  TEXT DEFAULT (datetime('now'))
);
"""

CREATE_TTL_PERSONS_IDX = [
    "CREATE INDEX IF NOT EXISTS idx_ttl_persons_name_vi ON ttl_persons(name_vi);",
    "CREATE INDEX IF NOT EXISTS idx_ttl_persons_slug    ON ttl_persons(slug);",
]


def phase1_create_table(conn, dry_run):
    print('[P1] Tạo bảng ttl_persons...')
    if dry_run:
        print('  [dry-run] sẽ CREATE TABLE IF NOT EXISTS ttl_persons')
        return
    conn.execute(CREATE_TTL_PERSONS)
    for idx in CREATE_TTL_PERSONS_IDX:
        conn.execute(idx)
    conn.commit()
    print('  [OK] ttl_persons created')


# ──────────────────────────────────────────────
# PHASE 2 — Populate ttl_persons từ TTL-only slugs
# ──────────────────────────────────────────────
def phase2_populate(conn, dry_run):
    print('[P2] Populate ttl_persons...')

    # Lấy tất cả slugs xuất hiện trong vn_person_relations
    # nhưng KHÔNG có dila_id trong vn_person_authority
    rows = conn.execute('''
        SELECT DISTINCT slug, vpa.name_vi, vpa.name_zh
        FROM (
            SELECT person_id AS slug FROM vn_person_relations
            UNION
            SELECT target_id AS slug FROM vn_person_relations
        ) x
        LEFT JOIN vn_person_authority vpa ON vpa.id = x.slug
        WHERE (vpa.dila_id IS NULL OR vpa.dila_id = '')
          AND vpa.name_vi IS NOT NULL AND vpa.name_vi != ''
    ''').fetchall()

    print(f'  Tìm thấy {len(rows)} slugs TTL-only có name_vi')

    inserted = 0
    skipped = 0
    for r in rows:
        slug = r['slug']
        name_vi = fix_enc(r['name_vi'] or slug)
        name_zh = r['name_zh'] or ''

        if dry_run:
            if inserted < 5:
                print(f'  [dry] INSERT ttl_persons: {slug} | {name_vi} | {name_zh}')
            inserted += 1
            continue

        try:
            conn.execute(
                'INSERT OR IGNORE INTO ttl_persons(id, name_vi, name_zh, slug, note) VALUES(?,?,?,?,?)',
                (slug, name_vi, name_zh, slug, NOTE_VN)
            )
            inserted += 1
        except Exception as e:
            print(f'  [warn] {slug}: {e}')
            skipped += 1

    if not dry_run:
        conn.commit()
    print(f'  Inserted: {inserted} | Skipped: {skipped}')
    if not dry_run:
        n = conn.execute('SELECT COUNT(*) FROM ttl_persons').fetchone()[0]
        print(f'  ttl_persons total: {n}')


# ──────────────────────────────────────────────
# PHASE 3 — Bridge TTL-only edges → lineage_edge_assertions
# ──────────────────────────────────────────────
def _resolve_id(slug, conn, vpa_cache, people_cache, ttl_only_slugs=None):
    """Trả về (id, is_ttl_only).
    Ưu tiên: people → vpa.dila_id → ttl_persons slug (hoặc ttl_only_slugs set khi dry-run)
    """
    if slug in people_cache:
        return people_cache[slug], False
    if slug in vpa_cache:
        return vpa_cache[slug], False
    # Kiểm tra ttl_persons (bảng thật hoặc set dry-run)
    if ttl_only_slugs is not None:
        if slug in ttl_only_slugs:
            return slug, True
    else:
        try:
            r = conn.execute('SELECT id FROM ttl_persons WHERE id=?', (slug,)).fetchone()
            if r:
                return r['id'], True
        except Exception:
            pass
    return None, False


def phase3_bridge_vn_edges(conn, dry_run):
    print('[P3] Bridge TTL-only VN edges → lineage_edge_assertions...')

    # Cache DILA IDs
    people_cache = {}
    for r in conn.execute('SELECT id, name_vi FROM people WHERE name_vi != ""'):
        people_cache[r['name_vi'].strip().lower()] = r['id']

    # Cache vpa (dila_id có giá trị)
    vpa_cache = {}
    for r in conn.execute("SELECT id, dila_id FROM vn_person_authority WHERE dila_id != '' AND dila_id IS NOT NULL"):
        vpa_cache[r['id']] = r['dila_id']

    # Tập slug TTL-only (không có DILA ID) — dùng cho cả dry-run
    ttl_only_slugs = set(r[0] for r in conn.execute('''
        SELECT DISTINCT slug FROM (
            SELECT person_id AS slug FROM vn_person_relations
            UNION
            SELECT target_id AS slug FROM vn_person_relations
        ) x
        LEFT JOIN vn_person_authority vpa ON vpa.id = x.slug
        WHERE (vpa.dila_id IS NULL OR vpa.dila_id = '')
    ''').fetchall())

    # Lấy tất cả relations có ít nhất 1 đầu là TTL-only slug
    all_relations = conn.execute(
        'SELECT person_id, relation_type, target_id FROM vn_person_relations'
    ).fetchall()
    relations = [r for r in all_relations
                 if r['person_id'] in ttl_only_slugs or r['target_id'] in ttl_only_slugs]

    print(f'  Tổng relations có TTL person: {len(relations)}')

    inserted = skipped = already = 0
    ts = datetime.utcnow().isoformat()

    for r in relations:
        p_slug = r['person_id']
        t_slug = r['target_id']
        rel = r['relation_type']

        if rel == 'hasDisciple':
            teacher_slug, disciple_slug = p_slug, t_slug
        elif rel == 'hasTeacher':
            teacher_slug, disciple_slug = t_slug, p_slug
        else:
            continue

        # Resolve IDs
        teacher_id, t_is_vn = _resolve_id(teacher_slug, conn, vpa_cache, {}, ttl_only_slugs)
        disciple_id, d_is_vn = _resolve_id(disciple_slug, conn, vpa_cache, {}, ttl_only_slugs)

        if not teacher_id or not disciple_id:
            skipped += 1
            continue

        # Tạo edge_key
        edge_key = f'TTL|{teacher_id}|{disciple_id}'

        # Check trùng
        ex = conn.execute(
            'SELECT id FROM lineage_edge_assertions WHERE edge_key=?', (edge_key,)
        ).fetchone()
        if ex:
            already += 1
            continue

        if dry_run:
            if inserted < 3:
                print(f'  [dry] INSERT assertion: {edge_key}')
            inserted += 1
            continue

        try:
            conn.execute('''
                INSERT OR IGNORE INTO lineage_edge_assertions
                (edge_key, subject_person_id, relation_type, object_person_id,
                 source_code, raw_relation_type, ref, trust_level, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                edge_key, teacher_id, 'da:isTeacherOf', disciple_id,
                'TTL', rel, disciple_slug,
                'L2', 'active', ts
            ))
            inserted += 1
        except Exception as e:
            print(f'  [warn] {edge_key}: {e}')
            skipped += 1

    if not dry_run:
        conn.commit()

    print(f'  Inserted: {inserted} | Already existed: {already} | Skipped (unresolved): {skipped}')
    n = conn.execute("SELECT COUNT(*) FROM lineage_edge_assertions WHERE source_code='TTL'").fetchone()[0]
    print(f'  lineage_edge_assertions[TTL] total: {n}')


# ──────────────────────────────────────────────
# PHASE 4 — Insert TTL-only edges vào lineage_edge_consensus
# ──────────────────────────────────────────────
def phase4_insert_consensus(conn, dry_run):
    print('[P4] Insert TTL-only edges vào lineage_edge_consensus...')

    ts = datetime.utcnow().isoformat()

    # Lấy TTL assertions chưa có trong consensus
    new_edges = conn.execute('''
        SELECT a.subject_person_id AS teacher_id, a.object_person_id AS disciple_id
        FROM lineage_edge_assertions a
        WHERE a.source_code='TTL'
          AND NOT EXISTS (
            SELECT 1 FROM lineage_edge_consensus c
            WHERE c.teacher_id=a.subject_person_id AND c.disciple_id=a.object_person_id
          )
    ''').fetchall()

    print(f'  TTL edges chưa có trong consensus: {len(new_edges)}')

    inserted = 0
    for e in new_edges:
        teacher_id = e['teacher_id']
        disciple_id = e['disciple_id']

        # Chỉ insert nếu ít nhất 1 đầu là TTL-only (không có trong DILA/Marcus)
        t_in_people = conn.execute('SELECT 1 FROM people WHERE id=?', (teacher_id,)).fetchone()
        d_in_people = conn.execute('SELECT 1 FROM people WHERE id=?', (disciple_id,)).fetchone()
        t_is_vn = (not t_in_people)
        d_is_vn = (not d_in_people)
        if not t_is_vn and not d_is_vn:
            continue  # cả 2 đều có trong DILA → etl_ttl_full_import.py đã xử lý

        if dry_run:
            if inserted < 3:
                print(f'  [dry] INSERT consensus: {teacher_id} → {disciple_id}')
            inserted += 1
            continue

        source_parts = []
        if t_is_vn or d_is_vn:
            source_parts.append('TTL-VN')

        badge = ', '.join(source_parts) if source_parts else 'TTL-VN'

        try:
            conn.execute('''
                INSERT OR IGNORE INTO lineage_edge_consensus
                (teacher_id, disciple_id, relation_type,
                 dila_asserted, marcus_asserted, ttl_asserted, lineage_asserted,
                 agreeing_source_count, opposite_source_count,
                 consensus_status, is_default_visible,
                 source_badge, migration_marker, created_at, updated_at)
                VALUES (?,?,'dharma_transmission',
                        0,0,1,0,
                        1,0,
                        'single_source',0,
                        ?,?,?,?)
            ''', (teacher_id, disciple_id, badge, 'T186_TTL_VN', ts, ts))
            inserted += 1
        except Exception as ex:
            print(f'  [warn] {teacher_id}→{disciple_id}: {ex}')

    if not dry_run:
        conn.commit()

    print(f'  Inserted vào consensus: {inserted}')
    n_vn = conn.execute(
        "SELECT COUNT(*) FROM lineage_edge_consensus WHERE migration_marker='T186_TTL_VN'"
    ).fetchone()[0]
    print(f'  lineage_edge_consensus[T186_TTL_VN]: {n_vn}')
    n_ttl = conn.execute(
        "SELECT COUNT(*) FROM lineage_edge_consensus WHERE ttl_asserted=1"
    ).fetchone()[0]
    print(f'  lineage_edge_consensus[ttl_asserted=1] total: {n_ttl}')


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='T186 ETL: ttl_persons + VN lineage')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true')
    group.add_argument('--apply', action='store_true')
    ap.add_argument('--phase', type=int, choices=[1, 2, 3, 4],
                    help='Chỉ chạy 1 phase cụ thể')
    args = ap.parse_args()

    dry_run = args.dry_run
    mode = 'DRY-RUN' if dry_run else 'APPLY'
    print(f'[start] {mode} — {datetime.utcnow().isoformat()}')
    print(f'[db]    {DB}')

    conn = get_conn()

    phases = [args.phase] if args.phase else [1, 2, 3, 4]

    try:
        if 1 in phases:
            phase1_create_table(conn, dry_run)
        if 2 in phases:
            phase2_populate(conn, dry_run)
        if 3 in phases:
            phase3_bridge_vn_edges(conn, dry_run)
        if 4 in phases:
            phase4_insert_consensus(conn, dry_run)
    finally:
        conn.close()

    print('[done] Hoàn tất.')


if __name__ == '__main__':
    main()

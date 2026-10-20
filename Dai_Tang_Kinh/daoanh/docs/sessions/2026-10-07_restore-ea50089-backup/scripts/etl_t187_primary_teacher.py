"""
T187 — ETL: Phân loại relation_subtype cho lineage edges
        (dharma_transmission vs early_study vs unknown)

Nguồn 1 — TTL (Truyền Đăng Lục VN):
  Khi ttl_asserted=1 → đây là nối pháp được Truyền Đăng Lục VN xác nhận.

Nguồn 2 — Marcus ref text:
  Parse từ khóa Hán văn trong lineage_edge_assertions.ref để phân loại:
    dharma_transmission: 嗣法, 得法, 印可, 法嗣, 嗣其法, 印證, 傳法, 受記, 承嗣
    early_study:         謁, 來謁, 參禮, 禮謁, 問法, 請益, 受業, 投師
    (參學 có thể đi kèm 嗣法 → không dùng 參學 đơn độc để classify early_study)

Kết quả:
  Bảng MỚI `lineage_primary_teacher` (additive — không ALTER gì cả):
    teacher_id, disciple_id, is_primary (1/0/-1),
    evidence_source (TTL|MARCUS_REF|BOTH|FALLBACK),
    confidence (high/medium/low),
    marcus_subtype (dharma_transmission|early_study|unknown),
    ttl_confirmed (1/0), conflict (1/0), notes

  Từ bảng này, `ancestor_spine` và `root_ancestor` ORDER BY is_primary DESC,
  ttl_confirmed DESC, agreeing_source_count DESC → spine chính xác.

Dùng:
  python scripts/etl_t187_primary_teacher.py --dry-run
  python scripts/etl_t187_primary_teacher.py --apply
  python scripts/etl_t187_primary_teacher.py --apply --phase 1   # chỉ tạo bảng
  python scripts/etl_t187_primary_teacher.py --apply --phase 2   # chỉ populate

Rollback:
  DROP TABLE IF EXISTS lineage_primary_teacher;
"""
import sqlite3, sys, io, os, argparse, re
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

# ── Từ khóa phân loại ──────────────────────────────────────────────────────
# Truyền pháp ấn — ưu tiên cao, match là đủ
TRANS_KWS = [
    '嗣法',   # nối pháp — phổ biến nhất
    '嗣其法', # nối pháp của vị đó
    '法嗣',   # pháp tự (đệ tử nối pháp)
    '得法',   # đắc pháp
    '印可',   # ấn khả
    '印證',   # ấn chứng
    '傳法',   # truyền pháp
    '受記',   # thụ ký (thọ ký)
    '承嗣',   # thừa nối
    '嗣師',   # nối thầy
    '付法',   # phó pháp
    '付囑',   # phó chúc
]

# Tham học / viếng thăm — chỉ classify early_study khi KHÔNG có TRANS_KWS
# và từ khóa đứng độc lập (không đi kèm 嗣法)
STUDY_KWS = [
    '來謁',   # đến vái lạy — pattern rõ nhất (Marcus dùng cho Tuyết Phong/Linh Huấn)
    '禮謁',   # lễ bái
    '往謁',   # đến bái yết
    '參禮',   # tham lễ
    '問法',   # hỏi pháp
    '請益',   # thỉnh giáo
    '受業',   # thụ nghiệp (ban đầu)
    '投師',   # đến với thầy
]
# Lưu ý: '謁' và '參學' không dùng đơn vì có thể xuất hiện trong văn cảnh khác


def classify_ref(ref_text):
    """Parse ref text → ('dharma_transmission'|'early_study'|'unknown', matched_kw)"""
    if not ref_text:
        return 'unknown', None
    # Ưu tiên kiểm tra TRANS_KWS trước
    for kw in TRANS_KWS:
        if kw in ref_text:
            return 'dharma_transmission', kw
    # Kiểm tra STUDY_KWS (chỉ khi không có TRANS_KWS)
    for kw in STUDY_KWS:
        if kw in ref_text:
            return 'early_study', kw
    return 'unknown', None


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS lineage_primary_teacher (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id       TEXT NOT NULL,
    disciple_id      TEXT NOT NULL,
    is_primary       INTEGER NOT NULL DEFAULT 0,
                     -- 1 = primary (truyền pháp ấn)
                     -- 0 = not primary (tham học / unknown xếp sau)
                     -- -1 = confirmed early_study (loại khỏi spine)
    evidence_source  TEXT,
                     -- 'TTL' | 'MARCUS_REF' | 'BOTH' | 'TTL_OVERRIDE' | 'FALLBACK'
    confidence       TEXT DEFAULT 'low',
                     -- 'high' (cả 2 nguồn đồng ý) | 'medium' (1 nguồn) | 'low' (fallback)
    marcus_subtype   TEXT DEFAULT 'unknown',
                     -- 'dharma_transmission' | 'early_study' | 'unknown'
    marcus_kw        TEXT,    -- từ khóa Hán văn match được (để debug)
    ttl_confirmed    INTEGER DEFAULT 0,
    conflict         INTEGER DEFAULT 0,
                     -- 1 = TTL nói primary nhưng Marcus ref nói early_study
    notes            TEXT,
    created_at       TEXT DEFAULT (datetime('now')),
    UNIQUE(teacher_id, disciple_id)
);
"""

IDX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_lpt_teacher   ON lineage_primary_teacher(teacher_id);",
    "CREATE INDEX IF NOT EXISTS idx_lpt_disciple  ON lineage_primary_teacher(disciple_id);",
    "CREATE INDEX IF NOT EXISTS idx_lpt_primary   ON lineage_primary_teacher(is_primary);",
    "CREATE INDEX IF NOT EXISTS idx_lpt_evidence  ON lineage_primary_teacher(evidence_source);",
]


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ── PHASE 1 — Tạo bảng ────────────────────────────────────────────────────
def phase1_create(conn, dry_run):
    print('[P1] Tạo bảng lineage_primary_teacher...')
    if dry_run:
        print('  [dry] CREATE TABLE lineage_primary_teacher')
        return
    conn.execute(CREATE_TABLE)
    for s in IDX_SQL:
        conn.execute(s)
    conn.commit()
    print('  [OK] Bảng tạo xong.')


# ── PHASE 2 — Populate từ consensus + Marcus ref + TTL ────────────────────
def phase2_populate(conn, dry_run):
    print('[P2] Populate lineage_primary_teacher...')

    # Lấy tất cả edges từ consensus
    edges = conn.execute('''
        SELECT teacher_id, disciple_id,
               ttl_asserted, agreeing_source_count, source_badge
        FROM lineage_edge_consensus
        WHERE relation_type = 'dharma_transmission'
    ''').fetchall()
    print(f'  Tổng edges consensus: {len(edges)}')

    # Build Marcus ref lookup: (teacher_id, disciple_id) → ref text
    marc_refs = {}
    rows = conn.execute('''
        SELECT subject_person_id AS tid, object_person_id AS did, ref
        FROM lineage_edge_assertions
        WHERE source_code = 'MARCUS' AND ref IS NOT NULL AND ref != ''
    ''').fetchall()
    for r in rows:
        marc_refs[(r['tid'], r['did'])] = r['ref']

    stats = {'total': 0, 'primary': 0, 'early_study': 0, 'fallback': 0,
             'conflict': 0, 'high': 0, 'medium': 0, 'low': 0}

    for e in edges:
        tid = e['teacher_id']
        did = e['disciple_id']
        ttl = e['ttl_asserted']
        ref_text = marc_refs.get((tid, did), '')
        marc_sub, marc_kw = classify_ref(ref_text)

        # Logic kết hợp TTL + Marcus
        conflict = 0
        if ttl and marc_sub == 'early_study':
            # TTL nói primary, Marcus ref nói tham học → conflict, tin TTL
            is_primary = 1
            evidence = 'TTL_OVERRIDE'
            confidence = 'medium'
            conflict = 1
            notes = f'TTL xác nhận nhưng Marcus ref ghi [{marc_kw}] — có thể tham học ban đầu trước khi nối pháp'
        elif ttl and marc_sub == 'dharma_transmission':
            # Cả 2 đồng ý → 100%
            is_primary = 1
            evidence = 'BOTH'
            confidence = 'high'
            notes = f'TTL + Marcus [{marc_kw}] đều xác nhận'
        elif ttl and marc_sub == 'unknown':
            # TTL có, Marcus không rõ → tin TTL (Truyền Đăng Lục đã curation)
            is_primary = 1
            evidence = 'TTL'
            confidence = 'medium'
            notes = 'TTL (Truyền Đăng Lục VN) xác nhận; Marcus không có từ khóa phân loại'
        elif not ttl and marc_sub == 'dharma_transmission':
            # Chỉ Marcus có từ khóa truyền pháp
            is_primary = 1
            evidence = 'MARCUS_REF'
            confidence = 'medium'
            notes = f'Marcus ref có [{marc_kw}]; TTL không bao phủ'
        elif not ttl and marc_sub == 'early_study':
            # Chỉ là tham học, không phải truyền pháp ấn
            is_primary = -1
            evidence = 'MARCUS_REF'
            confidence = 'medium'
            notes = f'Marcus ref có [{marc_kw}] — tham học, không phải nối pháp'
        else:
            # Không đủ thông tin → fallback (vùng xám)
            is_primary = 0
            evidence = 'FALLBACK'
            confidence = 'low'
            notes = 'Không có TTL xác nhận và Marcus không có từ khóa phân loại'

        stats['total'] += 1
        if is_primary == 1:
            stats['primary'] += 1
        elif is_primary == -1:
            stats['early_study'] += 1
        else:
            stats['fallback'] += 1
        if conflict:
            stats['conflict'] += 1
        stats[confidence] += 1

        if dry_run:
            if stats['total'] <= 5:
                print(f'  [dry] {tid}→{did}: is_primary={is_primary} ev={evidence} conf={confidence}')
            continue

        try:
            conn.execute('''
                INSERT OR REPLACE INTO lineage_primary_teacher
                (teacher_id, disciple_id, is_primary, evidence_source,
                 confidence, marcus_subtype, marcus_kw, ttl_confirmed, conflict, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (tid, did, is_primary, evidence,
                  confidence, marc_sub, marc_kw, ttl, conflict, notes))
        except Exception as ex:
            print(f'  [warn] {tid}→{did}: {ex}')

    if not dry_run:
        conn.commit()

    print(f'  primary (is_primary=1):    {stats["primary"]}')
    print(f'  early_study (is_primary=-1): {stats["early_study"]}')
    print(f'  fallback (is_primary=0):   {stats["fallback"]}')
    print(f'  conflict TTL vs Marcus:    {stats["conflict"]}')
    print(f'  confidence high:           {stats["high"]}')
    print(f'  confidence medium:         {stats["medium"]}')
    print(f'  confidence low:            {stats["low"]}')

    if not dry_run:
        n = conn.execute('SELECT COUNT(*) FROM lineage_primary_teacher').fetchone()[0]
        print(f'  lineage_primary_teacher total: {n}')

        # Xác nhận case Linh Huấn → Tuyết Phong
        r = conn.execute('''
            SELECT is_primary, evidence_source, confidence, notes
            FROM lineage_primary_teacher
            WHERE teacher_id='A019949' AND disciple_id='A003677'
        ''').fetchone()
        if r:
            print(f'\n  [VERIFY] Linh Huấn→Tuyết Phong: is_primary={r["is_primary"]} ({r["evidence_source"]}, {r["confidence"]})')
            print(f'           {r["notes"]}')

        r2 = conn.execute('''
            SELECT is_primary, evidence_source, confidence
            FROM lineage_primary_teacher
            WHERE teacher_id='A003868' AND disciple_id='A003677'
        ''').fetchone()
        if r2:
            print(f'  [VERIFY] Đức Sơn→Tuyết Phong: is_primary={r2["is_primary"]} ({r2["evidence_source"]}, {r2["confidence"]})')


# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='T187 ETL: lineage_primary_teacher')
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument('--dry-run', action='store_true')
    grp.add_argument('--apply', action='store_true')
    ap.add_argument('--phase', type=int, choices=[1, 2])
    args = ap.parse_args()
    dry_run = args.dry_run
    mode = 'DRY-RUN' if dry_run else 'APPLY'
    print(f'[start] T187 {mode} — {datetime.utcnow().isoformat()}')
    print(f'[db]    {DB}')

    conn = get_conn()
    phases = [args.phase] if args.phase else [1, 2]
    try:
        if 1 in phases:
            phase1_create(conn, dry_run)
        if 2 in phases:
            phase2_populate(conn, dry_run)
    finally:
        conn.close()
    print('[done] Hoàn tất.')


if __name__ == '__main__':
    main()

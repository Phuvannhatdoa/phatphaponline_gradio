"""T381 — ETL dữ liệu TTL vào cột lineage_edge_consensus.ttl_asserted.

Bối cảnh: `dharma_lineage_ttl_vn` (784 dòng) dùng teacher_id/student_id dạng
`ex:monk/<slug>`. `lineage_edge_consensus` (23,018 dòng, hệ thống T158) dùng
teacher_id/disciple_id dạng DILA code (A######). Script này crosswalk 2 chặng:

    ex:monk/<slug>  --(bỏ prefix)-->  <slug>
    <slug>  --(vn_person_authority.id = slug)-->  vn_person_authority.dila_id

rồi UPDATE ttl_asserted=1 cho đúng dòng (teacher_id, disciple_id) đã khớp
trong lineage_edge_consensus.

Vì ttl_asserted là 1 trong 4 cột góp vào agreeing_source_count/consensus_status/
source_badge (xem scripts/t158_consensus_migration.py BACKFILL_SQL), script
này RECOMPUTE luôn 4 cột dẫn xuất đó cho các dòng bị update, để không để lại
trạng thái "ttl_asserted=1 nhưng badge/consensus_status vẫn như cũ 1 nguồn" —
đây là quyết định có ghi chú rõ (task chỉ yêu cầu UPDATE ttl_asserted, nhưng
để giữ data-integrity, các cột dẫn xuất phải khớp với cột gốc).

Modes:
  --dry-run (default)  Không ghi DB. In số liệu sẽ update + log mismatch.
  --apply               Backup DB tự động rồi UPDATE thật trong 1 transaction.
                        Chạy PRAGMA quick_check sau khi commit.
  --revert              Set lại ttl_asserted=0 cho đúng các dòng mà crosswalk
                        hiện tại xác định là "do script này set" (deterministic
                        theo dữ liệu TTL/vn_person_authority hiện tại — nếu dữ
                        liệu TTL đổi giữa 2 lần chạy, --revert có thể không revert
                        hết; ghi rõ trong output).

Idempotent: chạy --apply nhiều lần cho cùng kết quả (dòng đã ttl_asserted=1
không bị update lại / không tăng đôi agreeing_source_count).

Không fabricate: slug không crosswalk được (vn_person_authority không có dòng,
hoặc dila_id rỗng) → log mismatch, KHÔNG suy đoán, KHÔNG insert dòng consensus
mới. Cạnh TTL có teacher/disciple hợp lệ nhưng lineage_edge_consensus chưa có
dòng tương ứng → log riêng (case "no_consensus_row"), KHÔNG tự INSERT — để
admin quyết định (theo yêu cầu task T381 revised).
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, '..', 'data', 'lineage.db')
BACKUP_DIR = os.path.join(HERE, '..', 'docs', 'sessions', '2026-10-14')
TABLE = 'lineage_edge_consensus'
RELATION_TYPE = 'dharma_transmission'
PREFIX = 'ex:monk/'


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _strip_prefix(raw):
    """ex:monk/<slug> -> <slug>. Trả về chuỗi rỗng nếu không có slug (ex:monk/)."""
    if raw is None:
        return ''
    s = str(raw)
    if s.startswith(PREFIX):
        return s[len(PREFIX):]
    return s


def _build_slug_to_dila(conn):
    """vn_person_authority.id (slug) -> dila_id (chỉ các dòng có dila_id không rỗng)."""
    rows = conn.execute(
        "SELECT id, dila_id FROM vn_person_authority WHERE dila_id IS NOT NULL AND dila_id != ''"
    ).fetchall()
    return {r['id']: r['dila_id'] for r in rows}


def _rebuild_badge(dila_v, marc_v, ttl_v, n_sources):
    parts = []
    if marc_v:
        parts.append('Marcus')
    if dila_v:
        parts.append('DILA')
    if ttl_v:
        parts.append('TTL')
    label = ', '.join(parts) if parts else '?'
    return f'{n_sources}/4: {label}'


def classify_ttl_edges(conn):
    """Crosswalk toàn bộ dharma_lineage_ttl_vn -> (teacher_dila, disciple_dila).

    Trả về dict với các nhóm:
      - matched: list[{teacher_dila, disciple_dila, teacher_slug, student_slug}]
                 đã map được cả 2 đầu sang DILA id.
      - mismatch_teacher / mismatch_student: slug không crosswalk được.
      - empty_teacher_slug: teacher_id rỗng sau khi bỏ prefix (vd. 'ex:monk/' —
        thường là khai tổ không có thầy).
    """
    slug2dila = _build_slug_to_dila(conn)
    ttl_rows = conn.execute(
        "SELECT teacher_id, student_id FROM dharma_lineage_ttl_vn"
    ).fetchall()

    matched = []
    mismatch_teacher = []
    mismatch_student = []
    empty_teacher_slug = []

    for r in ttl_rows:
        t_slug = _strip_prefix(r['teacher_id'])
        s_slug = _strip_prefix(r['student_id'])

        if not t_slug:
            empty_teacher_slug.append({'teacher_raw': r['teacher_id'], 'student_raw': r['student_id']})
            continue

        t_dila = slug2dila.get(t_slug)
        s_dila = slug2dila.get(s_slug)

        if not t_dila:
            mismatch_teacher.append({'slug': t_slug, 'student_raw': r['student_id']})
            continue
        if not s_dila:
            mismatch_student.append({'slug': s_slug, 'teacher_raw': r['teacher_id']})
            continue

        matched.append({
            'teacher_slug': t_slug, 'student_slug': s_slug,
            'teacher_dila': t_dila, 'disciple_dila': s_dila,
        })

    return {
        'matched': matched,
        'mismatch_teacher': mismatch_teacher,
        'mismatch_student': mismatch_student,
        'empty_teacher_slug': empty_teacher_slug,
    }


def plan_updates(conn, matched):
    """Với các cạnh đã crosswalk được, tra lineage_edge_consensus để phân loại:
      - to_update: dòng tồn tại, ttl_asserted hiện =0 -> cần UPDATE.
      - already_set: dòng tồn tại, ttl_asserted đã =1 -> no-op (idempotent).
      - no_consensus_row: không có dòng teacher/disciple tương ứng trong
        lineage_edge_consensus -> KHÔNG insert, chỉ log.
    """
    to_update = []
    already_set = []
    no_consensus_row = []
    seen_pairs = set()

    for m in matched:
        key = (m['teacher_dila'], m['disciple_dila'])
        if key in seen_pairs:
            continue  # TTL có thể có dòng trùng lặp — chỉ xử lý 1 lần / idempotent trong 1 run
        seen_pairs.add(key)

        row = conn.execute(
            f"SELECT id, dila_asserted, marcus_asserted, ttl_asserted, lineage_asserted, "
            f"opposite_source_count FROM {TABLE} "
            f"WHERE teacher_id=? AND disciple_id=? AND relation_type=?",
            (m['teacher_dila'], m['disciple_dila'], RELATION_TYPE)
        ).fetchone()

        if row is None:
            no_consensus_row.append(m)
            continue

        if row['ttl_asserted'] == 1:
            already_set.append(m)
            continue

        dila_v = row['dila_asserted']
        marc_v = row['marcus_asserted']
        lineage_v = row['lineage_asserted']
        n_sources = dila_v + marc_v + lineage_v + 1  # +1 vì ttl sẽ = 1
        opp = row['opposite_source_count'] or 0
        if opp > 0:
            status = 'conflicted'
            visible = 0
        elif n_sources >= 2:
            status = 'confirmed_2plus'
            visible = 1
        else:
            status = 'single_source'
            visible = 0
        badge = _rebuild_badge(dila_v, marc_v, 1, n_sources)

        to_update.append({
            'id': row['id'],
            'teacher_dila': m['teacher_dila'], 'disciple_dila': m['disciple_dila'],
            'agreeing_source_count': n_sources,
            'consensus_status': status,
            'is_default_visible': visible,
            'source_badge': badge,
        })

    return {
        'to_update': to_update,
        'already_set': already_set,
        'no_consensus_row': no_consensus_row,
    }


def backup_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'lineage.db.backup_t381_etl_{ts}')
    shutil.copy2(DB_PATH, dest)
    return dest


def do_dry_run(conn):
    cw = classify_ttl_edges(conn)
    plan = plan_updates(conn, cw['matched'])

    print('=== T381 ETL — DRY RUN (không ghi DB) ===')
    print(f"TTL edges total: {conn.execute('SELECT COUNT(*) n FROM dharma_lineage_ttl_vn').fetchone()['n']}")
    print(f"Crosswalk OK (matched cả 2 đầu): {len(cw['matched'])}")
    print(f"Mismatch teacher slug (không có dila_id): {len(cw['mismatch_teacher'])}")
    print(f"Mismatch student slug (không có dila_id): {len(cw['mismatch_student'])}")
    print(f"Empty teacher slug (khai tổ, không có thầy): {len(cw['empty_teacher_slug'])}")
    print('---')
    print(f"Sẽ UPDATE ttl_asserted=1 (dòng tồn tại, chưa set): {len(plan['to_update'])}")
    print(f"Đã ttl_asserted=1 từ trước (no-op, idempotent): {len(plan['already_set'])}")
    print(f"KHÔNG có dòng consensus tương ứng (không insert, chỉ log): {len(plan['no_consensus_row'])}")

    if cw['mismatch_teacher']:
        print('\n-- Mismatch teacher slug (mẫu tối đa 20) --')
        for x in cw['mismatch_teacher'][:20]:
            print(f"  slug={x['slug']!r} (student_raw={x['student_raw']!r})")
    if cw['mismatch_student']:
        print('\n-- Mismatch student slug (mẫu tối đa 20) --')
        for x in cw['mismatch_student'][:20]:
            print(f"  slug={x['slug']!r} (teacher_raw={x['teacher_raw']!r})")
    if plan['no_consensus_row']:
        print('\n-- TTL edges KHÔNG có dòng consensus tương ứng (mẫu tối đa 20) --')
        for x in plan['no_consensus_row'][:20]:
            print(f"  teacher={x['teacher_dila']} disciple={x['disciple_dila']} "
                  f"(slug {x['teacher_slug']} -> {x['student_slug']})")
    return plan


def do_apply(conn):
    plan = do_dry_run(conn)  # in lại số liệu để đối chiếu trước khi ghi
    to_update = plan['to_update']
    if not to_update:
        print('\nKhông có dòng nào cần UPDATE. Không ghi DB.')
        return

    backup_path = backup_db()
    print(f'\nĐã backup DB: {backup_path}')

    try:
        conn.execute('BEGIN')
        for u in to_update:
            conn.execute(
                f"UPDATE {TABLE} SET ttl_asserted=1, agreeing_source_count=?, "
                f"consensus_status=?, is_default_visible=?, source_badge=?, "
                f"updated_at=datetime('now') WHERE id=?",
                (u['agreeing_source_count'], u['consensus_status'], u['is_default_visible'],
                 u['source_badge'], u['id'])
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    print(f"\nĐã UPDATE thực tế: {len(to_update)} dòng.")

    qc = conn.execute('PRAGMA quick_check').fetchone()[0]
    print(f'PRAGMA quick_check: {qc}')
    if qc != 'ok':
        print('CẢNH BÁO: quick_check KHÔNG ok — kiểm tra lại DB / backup trước khi tiếp tục.')
        sys.exit(1)


def do_revert(conn):
    """Set ttl_asserted=0 lại cho các dòng mà crosswalk hiện tại xác định là
    TTL-sourced (deterministic theo dữ liệu hiện tại của dharma_lineage_ttl_vn +
    vn_person_authority). Nếu dữ liệu TTL/authority đã đổi so với lúc --apply,
    revert có thể không khớp 100% — đây là hạn chế đã biết, ghi rõ ở đây."""
    cw = classify_ttl_edges(conn)
    pairs = {(m['teacher_dila'], m['disciple_dila']) for m in cw['matched']}
    if not pairs:
        print('Không có cạnh TTL nào để revert.')
        return

    rows = []
    for (t, d) in pairs:
        row = conn.execute(
            f"SELECT id, dila_asserted, marcus_asserted, lineage_asserted, "
            f"opposite_source_count, ttl_asserted FROM {TABLE} "
            f"WHERE teacher_id=? AND disciple_id=? AND relation_type=?",
            (t, d, RELATION_TYPE)
        ).fetchone()
        if row and row['ttl_asserted'] == 1:
            rows.append(row)

    if not rows:
        print('Không có dòng ttl_asserted=1 khớp crosswalk hiện tại để revert.')
        return

    backup_path = backup_db()
    print(f'Đã backup DB trước revert: {backup_path}')

    try:
        conn.execute('BEGIN')
        for row in rows:
            dila_v = row['dila_asserted']
            marc_v = row['marcus_asserted']
            lineage_v = row['lineage_asserted']
            n_sources = dila_v + marc_v + lineage_v  # bỏ TTL
            opp = row['opposite_source_count'] or 0
            if opp > 0:
                status = 'conflicted'
                visible = 0
            elif n_sources >= 2:
                status = 'confirmed_2plus'
                visible = 1
            else:
                status = 'single_source'
                visible = 0
            badge = _rebuild_badge(dila_v, marc_v, 0, n_sources)
            conn.execute(
                f"UPDATE {TABLE} SET ttl_asserted=0, agreeing_source_count=?, "
                f"consensus_status=?, is_default_visible=?, source_badge=?, "
                f"updated_at=datetime('now') WHERE id=?",
                (n_sources, status, visible, badge, row['id'])
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    print(f'Đã revert ttl_asserted=0 cho {len(rows)} dòng.')
    qc = conn.execute('PRAGMA quick_check').fetchone()[0]
    print(f'PRAGMA quick_check: {qc}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help='Ghi DB thật (có backup tự động)')
    ap.add_argument('--revert', action='store_true', help='Set lại ttl_asserted=0 cho các dòng TTL đã set')
    args = ap.parse_args()

    conn = _connect()
    try:
        if args.revert:
            do_revert(conn)
        elif args.apply:
            do_apply(conn)
        else:
            do_dry_run(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()

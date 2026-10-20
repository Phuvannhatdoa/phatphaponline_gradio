"""T381 Decision 5 (2026-10-15) — INSERT 399 cạnh TTL-only vào lineage_edge_consensus.

Bối cảnh: `scripts/t381_etl_ttl_into_consensus.py` (chạy 2026-10-14) đã crosswalk
784 cạnh `dharma_lineage_ttl_vn` sang DILA id qua `vn_person_authority`. Trong
đó 553 cạnh crosswalk được cả 2 đầu, nhưng chỉ 149 cạnh có sẵn dòng tương ứng
trong `lineage_edge_consensus` (được UPDATE `ttl_asserted=1`). 399 cạnh còn lại
đã crosswalk được (có teacher_id/disciple_id dạng DILA hợp lệ) nhưng KHÔNG có
dòng nào trong `lineage_edge_consensus` — script cũ chỉ LOG (case
`no_consensus_row`), không INSERT, để admin quyết định.

Admin quyết định (Decision 5, 2026-10-15): ghi nhận cả 399 cạnh này vào
`lineage_edge_consensus`, đánh dấu RÕ là chỉ có nguồn TTL bằng
`consensus_status='ttl_only'` (KHÔNG dùng công thức tự động cũ của
`plan_updates()`, lẽ ra sẽ cho ra 'single_source' vì n_sources=1 — ở đây ta
ghi đè theo yêu cầu admin để nhóm 399 cạnh này tách biệt, dễ review sau,
KHÔNG trộn với cạnh đã có ≥2 nguồn).

Script này KHÔNG viết lại logic crosswalk — import trực tiếp
`classify_ttl_edges()` và `plan_updates()` từ `t381_etl_ttl_into_consensus.py`
(đã validate ngày 2026-10-14) để lấy đúng tập `no_consensus_row`. Nếu số
lượng đó khác 399 tại thời điểm chạy (do data đổi), script DỪNG LẠI và báo rõ
sự khác biệt — KHÔNG tự ý insert số khác.

Mỗi dòng insert:
  teacher_id, disciple_id = DILA code đã crosswalk
  relation_type           = 'dharma_transmission'
  ttl_asserted             = 1
  dila_asserted            = 0
  marcus_asserted          = 0
  lineage_asserted         = 0   (không có dòng cũ -> không nguồn nào khác)
  agreeing_source_count    = 1
  opposite_source_count    = 0
  consensus_status         = 'ttl_only'  (ghi đè theo quyết định admin)
  is_default_visible       = 0   (chưa confirmed_2plus -> không hiện mặc định)
  source_badge             = '1/4: TTL' (dùng _rebuild_badge() của script gốc)
  migration_marker         = 'T381_TTL_ONLY_INSERT_20261015'

Idempotent: trước khi INSERT, check tồn tại theo UNIQUE(teacher_id,
disciple_id, relation_type) (constraint thật của bảng) — dòng đã tồn tại thì
bỏ qua (no-op), không tăng đôi.

Modes:
  --dry-run (default)  Không ghi DB. In số liệu sẽ insert + so khớp 399.
  --apply               Backup DB tự động rồi INSERT thật trong 1 transaction,
                        PRAGMA quick_check sau khi commit.
"""

import argparse
import io
import os
import shutil
import sqlite3
import sys
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, '..', 'data', 'lineage.db')
BACKUP_DIR = os.path.join(HERE, '..', 'docs', 'sessions', '2026-10-15')
TABLE = 'lineage_edge_consensus'
RELATION_TYPE = 'dharma_transmission'
MIGRATION_MARKER = 'T381_TTL_ONLY_INSERT_20261015'
EXPECTED_NO_CONSENSUS_COUNT = 399

sys.path.insert(0, HERE)
from t381_etl_ttl_into_consensus import classify_ttl_edges, plan_updates, _rebuild_badge  # noqa: E402


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _dedupe_matched(matched):
    """Dedupe theo (teacher_dila, disciple_dila) — TTL có thể có dòng trùng lặp."""
    seen = set()
    out = []
    for m in matched:
        key = (m['teacher_dila'], m['disciple_dila'])
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


def build_plan(conn):
    """Dùng trực tiếp `classify_ttl_edges().matched` (chỉ phụ thuộc
    dharma_lineage_ttl_vn + vn_person_authority, KHÔNG phụ thuộc trạng thái
    hiện tại của lineage_edge_consensus) rồi tự kiểm tra từng cặp đã có dòng
    trong consensus chưa. Đây là điểm khác biệt quan trọng so với dùng lại
    `plan_updates().no_consensus_row` trực tiếp: tập đó co lại dần sau mỗi lần
    insert (vì dòng đã tồn tại), nên không dùng được để kiểm tra idempotent ở
    lần chạy thứ 2 — còn `matched` (553 cạnh) là tập cố định theo dữ liệu
    nguồn, cho phép tính to_insert/already_exists chính xác ở mọi lần chạy.

    QA round 2 fix (2026-10-15): thêm 2 điều kiện SKIP trước khi coi một cặp
    là "to_insert", để tránh tái tạo 2 loại lỗi crosswalk đã gặp ở lần chạy
    đầu (399 dòng, 2026-10-15):
      - self-loop: teacher_dila == disciple_dila (do crosswalk gộp nhầm 2
        slug TTL khác nhau vào cùng 1 DILA id trong vn_person_authority).
      - reversed-duplicate: đã có dòng NGƯỢC CHIỀU (disciple, teacher) với
        cùng relation_type trong lineage_edge_consensus, bất kể
        consensus_status nào (không chỉ ttl_only) — ưu tiên chiều đã xác
        nhận trước đó (có thể confirmed_2plus/multi-source), không ghi
        thêm chiều ngược từ TTL-only.
    Cả 2 case đều bị log rõ (in ra) để admin/QA review, không âm thầm bỏ qua.
    """
    cw = classify_ttl_edges(conn)
    matched = _dedupe_matched(cw['matched'])

    already_exists = []
    to_insert = []
    skipped_self_loop = []
    skipped_reversed_duplicate = []
    for m in matched:
        teacher = m['teacher_dila']
        disciple = m['disciple_dila']

        if teacher == disciple:
            skipped_self_loop.append(m)
            print(f"SKIP (self-loop): teacher_dila == disciple_dila == {teacher!r} "
                  f"— có thể do crosswalk gộp nhầm 2 slug TTL khác nhau vào cùng 1 "
                  f"DILA id trong vn_person_authority. Không insert.")
            continue

        reverse_row = conn.execute(
            f"SELECT id, consensus_status FROM {TABLE} "
            f"WHERE teacher_id=? AND disciple_id=? AND relation_type=?",
            (disciple, teacher, RELATION_TYPE)
        ).fetchone()
        if reverse_row is not None:
            skipped_reversed_duplicate.append(m)
            print(f"SKIP (reversed-duplicate): cặp {teacher!r} -> {disciple!r} bị bỏ qua "
                  f"vì đã có dòng NGƯỢC CHIỀU id={reverse_row['id']} "
                  f"({disciple!r} -> {teacher!r}, consensus_status="
                  f"{reverse_row['consensus_status']!r}) cùng relation_type trong "
                  f"{TABLE}. Không insert để tránh vòng 2 nút.")
            continue

        row = conn.execute(
            f"SELECT id FROM {TABLE} WHERE teacher_id=? AND disciple_id=? AND relation_type=?",
            (teacher, disciple, RELATION_TYPE)
        ).fetchone()
        if row is not None:
            already_exists.append(m)
        else:
            to_insert.append(m)

    return {
        'matched_count': len(matched),
        'already_exists': already_exists,
        'to_insert': to_insert,
        'skipped_self_loop': skipped_self_loop,
        'skipped_reversed_duplicate': skipped_reversed_duplicate,
    }


def do_dry_run(conn):
    plan = build_plan(conn)
    print('=== T381 Decision 5 — INSERT 399 TTL-only edges — DRY RUN (không ghi DB) ===')
    print(f"Matched crosswalk (dedup, toàn bộ 553 cạnh TTL có cả 2 đầu DILA): "
          f"{plan['matched_count']}")
    print(f"Đã có dòng trong {TABLE} từ trước (no-op, bao gồm 149 dòng ETL gốc + "
          f"399 dòng ttl_only đã insert nếu đã chạy --apply trước): "
          f"{len(plan['already_exists'])}")
    print(f"Sẽ INSERT mới (chưa có dòng consensus nào): {len(plan['to_insert'])}")
    print(f"SKIP self-loop (teacher==disciple): {len(plan['skipped_self_loop'])}")
    print(f"SKIP reversed-duplicate (đã có dòng ngược chiều): "
          f"{len(plan['skipped_reversed_duplicate'])}")

    n_to_insert = len(plan['to_insert'])
    n_already = len(plan['already_exists'])

    if n_to_insert == 0:
        print('\nKhông có dòng nào cần insert — idempotent, không ghi DB nếu --apply.')
    elif n_already == 0 and n_to_insert != EXPECTED_NO_CONSENSUS_COUNT:
        # Lần chạy đầu tiên (chưa có gì được insert bởi script này) nhưng số
        # liệu không khớp 399 đã ghi nhận trong T381_EXECUTION_LOG.md.
        print(f"\n*** CẢNH BÁO: to_insert ({n_to_insert}) KHÁC "
              f"{EXPECTED_NO_CONSENSUS_COUNT} đã ghi nhận trong T381_EXECUTION_LOG.md "
              f"(và chưa có dòng ttl_only nào tồn tại — có vẻ đây là lần chạy đầu). "
              f"DỪNG LẠI — không tự ý insert số khác. Kiểm tra lại dữ liệu nguồn "
              f"(dharma_lineage_ttl_vn / vn_person_authority) trước khi tiếp tục. ***")
    elif n_to_insert != EXPECTED_NO_CONSENSUS_COUNT:
        print(f"\nGhi chú: to_insert={n_to_insert} (không phải 399) nhưng đã có "
              f"{n_already} dòng tồn tại từ trước — có thể do chạy lại sau một lần "
              f"--apply thành công trước đó cộng với thay đổi dữ liệu nguồn. Xem lại "
              f"kỹ trước khi --apply nếu không chắc.")

    return plan


def backup_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'lineage.db.backup_t381_ttlonly_{ts}')
    shutil.copy2(DB_PATH, dest)
    return dest


def do_apply(conn):
    plan = do_dry_run(conn)
    to_insert = plan['to_insert']
    n_already = len(plan['already_exists'])

    if not to_insert:
        print('\nKhông có dòng nào cần INSERT (tất cả đã tồn tại / idempotent). Không ghi DB.')
        return

    if n_already == 0 and len(to_insert) != EXPECTED_NO_CONSENSUS_COUNT:
        print(f'\nABORT: lần chạy đầu tiên (chưa có dòng ttl_only nào tồn tại) nhưng '
              f'to_insert={len(to_insert)} khác {EXPECTED_NO_CONSENSUS_COUNT} đã ghi nhận '
              f'trong T381_EXECUTION_LOG.md. Không tự ý insert số khác — DỪNG LẠI, không '
              f'ghi DB.')
        sys.exit(1)

    before_total = conn.execute(f'SELECT COUNT(*) n FROM {TABLE}').fetchone()['n']
    before_ttl_only = conn.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE consensus_status='ttl_only'"
    ).fetchone()['n']

    backup_path = backup_db()
    print(f'\nĐã backup DB: {backup_path}')
    print(f'Trước khi insert: {TABLE} tổng {before_total} dòng, ttl_only={before_ttl_only} dòng.')

    badge = _rebuild_badge(0, 0, 1, 1)  # '1/4: TTL'

    try:
        conn.execute('BEGIN')
        for m in to_insert:
            conn.execute(
                f"INSERT INTO {TABLE} "
                f"(teacher_id, disciple_id, relation_type, dila_asserted, marcus_asserted, "
                f"ttl_asserted, lineage_asserted, agreeing_source_count, opposite_source_count, "
                f"consensus_status, is_default_visible, source_badge, migration_marker, "
                f"created_at, updated_at) "
                f"VALUES (?, ?, ?, 0, 0, 1, 0, 1, 0, 'ttl_only', 0, ?, ?, "
                f"datetime('now'), datetime('now'))",
                (m['teacher_dila'], m['disciple_dila'], RELATION_TYPE, badge, MIGRATION_MARKER)
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    after_total = conn.execute(f'SELECT COUNT(*) n FROM {TABLE}').fetchone()['n']
    after_ttl_only = conn.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE consensus_status='ttl_only'"
    ).fetchone()['n']

    print(f"\nĐã INSERT thực tế: {len(to_insert)} dòng.")
    print(f"{TABLE}: tổng {before_total} -> {after_total} (delta {after_total - before_total})")
    print(f"consensus_status='ttl_only': {before_ttl_only} -> {after_ttl_only} "
          f"(delta {after_ttl_only - before_ttl_only})")

    dup = conn.execute(
        f"SELECT teacher_id, disciple_id, relation_type, COUNT(*) c FROM {TABLE} "
        f"GROUP BY teacher_id, disciple_id, relation_type HAVING c > 1"
    ).fetchall()
    print(f"Duplicate theo (teacher_id, disciple_id, relation_type): {len(dup)} (phải = 0)")

    qc = conn.execute('PRAGMA quick_check').fetchone()[0]
    print(f'PRAGMA quick_check: {qc}')
    if qc != 'ok':
        print('CẢNH BÁO: quick_check KHÔNG ok — kiểm tra lại DB / backup trước khi tiếp tục.')
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help='Ghi DB thật (có backup tự động)')
    args = ap.parse_args()

    conn = _connect()
    try:
        if args.apply:
            do_apply(conn)
        else:
            do_dry_run(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()

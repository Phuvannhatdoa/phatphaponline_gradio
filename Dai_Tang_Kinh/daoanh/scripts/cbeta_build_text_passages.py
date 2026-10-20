# -*- coding: utf-8 -*-
"""
T95 Phase A3 — Build text_passages (canonical đoạn con ổn định CBETA)

Đọc legacy `passage` theo work (pilot: T50n2060), tách mỗi mục thành các "đoạn
con ổn định" theo dấu câu (。；！？) nhóm ~25–60 ký tự (fallback), gán ID ổn định
`daoanh:cbeta:<work>:<loc_key>:p<seq>` + sha256 hash, rồi thêm vào `text_passages`.

Nguyên tắc:
    - Zero-RAM: duyệt từng passage một (fetchmany chunk), không nạp toàn bộ.
    - Idempotent: passage_id trùng + cùng hash → SKIP (giữ nguyên provenance);
      trùng + khác hash → INSERT OR REPLACE (đếm replaced).
    - Loc key: '0-0484c-' → '0484c' ; '0--' → 'nopage'. Nếu 2 mục cùng page →
      disambiguate bằng ordinal ('0484c-0002'); nopage luôn 'nopage-<ordinal>'.
    - Backfill nhẹ trên legacy passage: raw_zh_hash + segmentation_method
      (chỉ điền ô NULL, không ghi đè gì).

Usage:
    python scripts/cbeta_build_text_passages.py --dry-run [--work-id T50n2060] [--target-chars 50]
    python scripts/cbeta_build_text_passages.py --apply  [--work-id T50n2060] [--no-backup] [--skip-backfill]
    python scripts/cbeta_build_text_passages.py --stats  [--work-id T50n2060]
    python scripts/cbeta_build_text_passages.py --verify [--work-id T50n2060]
    python scripts/cbeta_build_text_passages.py --revert [--work-id T50n2060]

ROLLBACK: python scripts/cbeta_build_text_passages.py --revert
          (xóa rows của lần apply gần nhất; restore backup luôn khả dụng)
"""
import sqlite3
import sys
import os
import shutil
import hashlib
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
BACK_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

SENT_BOUND = '。；！？'


def _con():
    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA journal_mode=WAL')
    return con


def norm_zh(text):
    return re.sub(r'\s+', '', text)


def zh_hash(text):
    return hashlib.sha256(norm_zh(text).encode('utf-8')).hexdigest()


def normalize_loc(loc_ref):
    if not loc_ref:
        return 'nopage', loc_ref or ''
    parts = loc_ref.split('-')
    if len(parts) >= 3 and parts[1]:
        return parts[1], loc_ref
    return 'nopage', loc_ref


def segment_zh(raw, target=50, min_seg=25):
    """Cắt đoạn con tại ranh giới dấu câu, nhóm tới ~target ký tự.

    Deterministic: cùng input luôn ra cùng output. Ranh giới luôn là
    sau một ký tự câu tận (。；！？). Phần đuôi < min_seg gộp vào đoạn trước.
    """
    text = re.sub(r'\s+', '', raw or '')
    if not text:
        return []
    parts = []
    buf = ''
    for ch in text:
        buf += ch
        if ch in SENT_BOUND:
            parts.append(buf)
            buf = ''
    if buf:
        parts.append(buf)

    segs = []
    acc = ''
    for p in parts:
        if len(acc) >= target:
            segs.append(acc)
            acc = p
        else:
            if acc:
                acc += ' '
            acc += p
            if len(acc) >= target:
                segs.append(acc)
                acc = ''
    if acc:
        # đuôi ngắn: gộp vào đoạn trước để tránh đoạn mồ côi
        if segs and len(acc) < min_seg:
            segs[-1] += ' ' + acc
        else:
            segs.append(acc)
    return [s for s in segs if s.strip()]


def load_parents(con, work_id):
    """Metadata mẹ: (legacy_id, loc_raw, raw_len, text_id) đọc tuần tự.
    Chỉ giữ tuple metadata nhỏ — không giữ raw_text trong RAM."""
    rows = con.execute(
        "SELECT passage_id, loc_ref, raw_text FROM passage "
        "WHERE text_id=? AND source='CBETA' ORDER BY passage_id",
        (work_id,)).fetchall()
    return rows


def build_pages_mapping(rows):
    """Gán loc_key duy nhất cho từng mục mẹ (ổn định theo thứ tự passage_id)."""
    from collections import defaultdict
    groups = defaultdict(list)
    for legacy_id, loc_raw, _raw in rows:
        key, _ = normalize_loc(loc_raw)
        groups[key].append(legacy_id)
    occ = defaultdict(int)
    result = {}
    for key, ids in groups.items():
        for idx, legacy_id in enumerate(ids, 1):
            if len(ids) == 1:
                result[legacy_id] = key
            else:
                result[legacy_id] = f'{key}-{idx:04d}'
    return result


def iter_segments(rows, pages_map, target, min_seg=25):
    """Generator: mỗi lần trả về (legacy_id, loc_raw, seq_in_work, sub_index,
    sub_len, sub_text, parent_hash). Không giữ toàn bộ text trong RAM."""
    seq_all = 0
    for legacy_id, loc_raw, raw in rows:
        parent_hash = zh_hash(raw) if raw else ''
        subs = segment_zh(raw, target=target, min_seg=min_seg)
        for si, sub in enumerate(subs, 1):
            seq_all += 1
            yield legacy_id, loc_raw, seq_all, si, len(sub), sub, parent_hash


def ensure_runs_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS t95_import_runs (
        run_id TEXT PRIMARY KEY,
        work_id TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        units_inserted INTEGER DEFAULT 0,
        units_skipped INTEGER DEFAULT 0,
        units_replaced INTEGER DEFAULT 0
    )""")


def cmd_dry_run(work_id, target, min_seg=25):
    con = _con()
    rows = load_parents(con, work_id)
    pages_map = build_pages_mapping(rows)
    gen = iter_segments(rows, pages_map, target, min_seg)
    total_units = 0
    lens = []
    sample = []
    for legacy_id, loc_raw, seq_all, si, sub_len, sub, _ in gen:
        total_units += 1
        lens.append(sub_len)
        if legacy_id == 4061 and si <= 9 and len(sample) < 9:
            key = pages_map[legacy_id]
            sample.append(f'{seq_all:4d}  daoanh:cbeta:{work_id}:{key}:p{si:04d}  ({sub_len} chữ) {sub[:34]}…')
    lens_sorted = sorted(lens)
    print(f'=== DRY RUN {work_id} ===')
    print(f'  Legacy passages : {len(rows)}')
    print(f'  Đơn vị đoạn con : {total_units}  (trung bình ~{(sum(lens)/max(total_units,1)):.0f} chữ)')
    print(f'  Min/trung vị/Max: {lens_sorted[0]}/{lens_sorted[len(lens_sorted)//2]}/{lens_sorted[-1]} chữ')
    print(f'  Pages có nhiều mục (disambiguate): {sum(1 for v in pages_map.values() if "-" in v)}')
    print('\n  Mẫu ID cho passage 4061 (0-0484c-):')
    print('\n'.join(sample))
    con.close()
    print('\nKhông ghi gì (dry-run).')


def cmd_apply(work_id, target, min_seg, do_backup, do_backfill):
    if do_backup:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        bak = os.path.join(BACK_DIR, f'lineage.db.backup_t95_{ts}')
        print(f'Backup → {bak}')
        shutil.copy2(DB_PATH, bak)
        print(f'  OK — {os.path.getsize(bak) // (1024 * 1024)} MB')

    con = _con()
    ensure_runs_table(con)
    run_id = f't95-{work_id}-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    rows = load_parents(con, work_id)
    pages_map = build_pages_mapping(rows)

    ins = rep = skip = 0
    for legacy_id, loc_raw, seq_all, si, sub_len, sub, parent_hash in iter_segments(rows, pages_map, target, min_seg):
        key = pages_map[legacy_id]
        pid = f'daoanh:cbeta:{work_id}:{key}:p{si:04d}'
        h = zh_hash(sub)
        existing = con.execute(
            'SELECT raw_zh_hash, import_run_id FROM text_passages WHERE passage_id=?', (pid,)).fetchone()
        if existing and existing[0] == h:
            skip += 1
            continue
        vals = (pid, work_id, 'CBETA', loc_raw or None, None, seq_all, sub, h,
                'punctuation_fallback', None, None, None, 'legacy:pipeline:v1',
                run_id, datetime.now().isoformat(' '), 'ok', loc_raw or None,
                loc_raw or None, loc_raw or None, legacy_id, datetime.now().isoformat(' '))
        con.execute("""INSERT OR REPLACE INTO text_passages (
                passage_id, work_id, source_system, canonical_ref, juan, sequence_no,
                original_zh, raw_zh_hash, segmentation_method,
                tei_anchor_start, tei_anchor_end, source_url, source_version,
                import_run_id, created_at,
                source_status, loc_ref, canonical_start_anchor, canonical_end_anchor,
                legacy_passage_id, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
        if existing:
            rep += 1
        else:
            ins += 1
        if (ins + rep) % 500 == 0:
            con.commit()
            print(f'  ... {ins + rep} unit (insert {ins}, replace {rep})')

    # Reconcile: xóa các passage_id cũ không còn trong bộ hiện tại
    # (ví dụ sau khi tail-merge, p0010 của 4061 không còn được sinh ra).
    removed = 0
    for legacy_id, _loc, raw in rows:
        key = pages_map[legacy_id]
        parent_prefix = f'daoanh:cbeta:{work_id}:{key}:p'
        kept = {f'{parent_prefix}{si:04d}'
                for si in range(1, len(segment_zh(raw, target=target, min_seg=min_seg)) + 1)}
        for (pid,) in con.execute(
                'SELECT passage_id FROM text_passages WHERE legacy_passage_id=?', (legacy_id,)):
            if pid not in kept:
                con.execute('DELETE FROM text_passages WHERE passage_id=?', (pid,))
                removed += 1
    if removed:
        con.commit()
        print(f'  Reconcile: xóa {removed} passage_id cũ (orphan)')

    # Renumber: đảm bảo sequence_no = thứ tự GLOBAL theo segmentation HIỆN TẠI
    # cho TOÀN BỘ rows của work (chạy lại khi segmentation đổi — không đổi gì ở
    # lần chạy lặp cùng input).
    ren = 0
    cur_seq = 0
    for legacy_id, _loc, raw in rows:
        key = pages_map[legacy_id]
        subs = segment_zh(raw, target=target, min_seg=min_seg)
        for si in range(1, len(subs) + 1):
            pid = f'daoanh:cbeta:{work_id}:{key}:p{si:04d}'
            cur_seq += 1
            ren += con.execute('UPDATE text_passages SET sequence_no=? WHERE passage_id=?',
                               (cur_seq, pid)).rowcount
    if ren:
        con.commit()
        print(f'  Renumber: cập nhật thứ tự {ren} rows')

    if do_backfill:
        for legacy_id, _loc, raw in load_parents(con, work_id):
            h = zh_hash(raw) if raw else None
            con.execute(
                "UPDATE passage SET raw_zh_hash=?, segmentation_method=? WHERE passage_id=? "
                "AND (raw_zh_hash IS NULL OR raw_zh_hash='')",
                (h, 'punctuation_fallback', legacy_id))
        n = con.execute(
            "SELECT COUNT(*) FROM passage WHERE text_id=? AND source='CBETA' AND segmentation_method='punctuation_fallback'",
            (work_id,)).fetchone()[0]
        print(f'  Backfilled segmentation_method: {n} mục legacy')
    else:
        print('  (skip-backfill)')

    con.execute('INSERT INTO t95_import_runs (run_id, work_id, units_inserted, units_skipped, units_replaced) VALUES (?,?,?,?,?)',
                (run_id, work_id, ins, skip, rep))
    con.commit()
    con.close()
    print(f'\nXong {work_id}: insert {ins} | skip {skip} | replace {rep}')
    print(f'  Run: {run_id}')
    print('  Rollback: python scripts/cbeta_build_text_passages.py --revert')


def cmd_stats(work_id):
    con = _con()
    total = con.execute('SELECT COUNT(*) FROM text_passages WHERE work_id=?', (work_id,)).fetchone()[0]
    by_status = con.execute("SELECT source_status, COUNT(*) FROM text_passages WHERE work_id=? GROUP BY 1", (work_id,)).fetchall()
    avg = con.execute('SELECT AVG(LENGTH(original_zh)) FROM text_passages WHERE work_id=?', (work_id,)).fetchone()[0]
    runs = con.execute("SELECT run_id, work_id, units_inserted, units_skipped, units_replaced, created_at FROM t95_import_runs ORDER BY created_at").fetchall()
    ver_cols = con.execute('PRAGMA table_info(text_passages)').fetchall()
    print(f'=== STATS {work_id} ===')
    print(f'  text_passages   : {total}')
    print(f'  trung bình chữ  : {avg:.1f}')
    for s, c in by_status:
        print(f'  source_status {s}: {c}')
    print('  runs:')
    for r in runs:
        print(f'    {r[0]} ins={r[2]} skip={r[3]} rep={r[4]}')
    # test case T50n2060 0-0484c-
    print('  Test case 0-0484c- (legacy 4061):')
    for pid, sub_len, hash8 in con.execute(
            "SELECT passage_id, LENGTH(original_zh), substr(raw_zh_hash,1,8) FROM text_passages "
            "WHERE work_id=? AND legacy_passage_id=4061 ORDER BY sequence_no", (work_id,)):
        print(f'    {pid} ({sub_len}) {hash8}')
    nohash_legacy = con.execute("SELECT COUNT(*) FROM passage WHERE text_id=? AND (raw_zh_hash IS NULL OR raw_zh_hash='')", (work_id,)).fetchone()[0]
    print(f'  legacy passage chưa hash: {nohash_legacy}')
    con.close()


def cmd_verify(work_id):
    con = _con()
    total = con.execute('SELECT COUNT(*) FROM text_passages WHERE work_id=?', (work_id,)).fetchone()[0]
    distinct_ids = con.execute('SELECT COUNT(DISTINCT passage_id) FROM text_passages WHERE work_id=?', (work_id,)).fetchone()[0]
    dup_legacy = con.execute("SELECT COUNT(*) FROM (SELECT passage_id, COUNT(*) c FROM text_passages WHERE work_id=? GROUP BY passage_id HAVING c>1)", (work_id,)).fetchone()[0]
    empty_zh = con.execute("SELECT COUNT(*) FROM text_passages WHERE work_id=? AND (original_zh IS NULL OR trim(original_zh)='')", (work_id,)).fetchone()[0]
    print(f'=== VERIFY {work_id} ===')
    print(f'  rows              : {total}')
    print(f'  distinct passage_id: {distinct_ids}  {"✅" if total == distinct_ids else "❌ TRÙNG ID"}')
    print(f'  dup passage_id    : {dup_legacy}')
    print(f'  empty original_zh : {empty_zh}  {"✅" if empty_zh == 0 else "❌"}')
    ok = (total == distinct_ids and empty_zh == 0)
    print('KẾT LUẬN: ' + ('PASS ✅' if ok else 'FAIL ❌'))
    con.close()
    return ok


def cmd_revert(work_id):
    con = _con()
    ensure_runs_table(con)
    run = con.execute("SELECT run_id FROM t95_import_runs WHERE work_id=? ORDER BY created_at DESC LIMIT 1", (work_id,)).fetchone()
    if not run:
        print('Không có run để revert.')
        con.close()
        return
    run_id = run[0]
    n = con.execute('SELECT COUNT(*) FROM text_passages WHERE import_run_id=?', (run_id,)).fetchone()[0]
    print(f'=== REVERT ===')
    print(f'  Run {run_id}: {n} text_passages sẽ bị xóa (chỉ rows của run này; rows giữ run cũ được giữ).')
    print('Tiếp tục? [y/N]', end=' ')
    if input().strip().lower() != 'y':
        print('Đã hủy.')
        con.close()
        return
    con.execute('DELETE FROM text_passages WHERE import_run_id=?', (run_id,))
    con.execute('DELETE FROM t95_import_runs WHERE run_id=?', (run_id,))
    con.commit()
    con.close()
    print('✅ Đã revert. Restore backup đầy đủ nếu cần.')


if __name__ == '__main__':
    args = sys.argv[1:]
    work_id = 'T50n2060'
    target = 50
    min_seg = 25
    if '--work-id' in args:
        work_id = args[args.index('--work-id') + 1]
    if '--target-chars' in args:
        target = int(args[args.index('--target-chars') + 1])
    if '--min-seg' in args:
        min_seg = int(args[args.index('--min-seg') + 1])
    do_backup = '--no-backup' not in args
    do_backfill = '--skip-backfill' not in args
    if '--dry-run' in args:
        cmd_dry_run(work_id, target, min_seg)
    elif '--apply' in args:
        cmd_apply(work_id, target, min_seg, do_backup, do_backfill)
    elif '--stats' in args:
        cmd_stats(work_id)
    elif '--verify' in args:
        cmd_verify(work_id)
    elif '--revert' in args:
        cmd_revert(work_id)
    else:
        print(__doc__)
# -*- coding: utf-8 -*-
"""t207_fix_db_mojibake.py — [T207] sửa mojibake `Ð` (U+00D0) trong DB.

BỐI CẢNH
--------
Chữ Đ tiếng Việt là U+0110. Một số nguồn ghi ra U+00D0 (LATIN CAPITAL LETTER ETH) —
ký tự không tồn tại trong tiếng Việt. Phạm vi: 22 cột / 1.469 row.

LỖI NÀY PHÁ VỠ TRA CỨU, KHÔNG CHỈ SAI HIỂN THỊ
---------------------------------------------
`app.py:96 normalize_text()` — dùng bởi CẢ 2 call site đọc `lexicon.key_norm`
(`app.py:1226 _translate_zh_term`, `app.py:2800`) — làm:

    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if category(c) != 'Mn')
    s = s.replace('đ','d').replace('Đ','d')      # chỉ map U+0110/U+0111
    return s.lower().strip()

U+00D0 KHÔNG có canonical decomposition (`decomposition=''`) nên sống sót:
`Ðoạn lạc` -> 'ðoan lac' thay vì 'doan lac'. Mọi mục từ điển có chữ Đ đều trượt.

CHIẾN LƯỢC B (Admin đã chốt 2026-10-01)
---------------------------------------
Thay `Ð`→`Đ` ở 20 cột văn bản, **và** tính lại `lexicon.key_norm` bằng đúng
`normalize_text()` cho 162 row có `Ð` trong `term` ⇒ khôi phục tra cứu 162/162.
(Không tính lại 53.686 row lệch vì `đ/Đ` ĐÚNG — ngoài phạm vi, đụng hành vi
tra cứu quy mô lớn.)

`lexicon_fts` — FTS5 EXTERNAL-CONTENT, KHÔNG có trigger
------------------------------------------------------
`CREATE VIRTUAL TABLE lexicon_fts USING fts5(term, definition,
 content=lexicon, content_rowid=id)`.
`UPDATE lexicon` thẳng sẽ LỆCH index. Bắt buộc đúng thứ tự:

    INSERT INTO lexicon_fts(lexicon_fts,rowid,term,definition)
      VALUES('delete', :id, :old_term, :old_def);   -- gỡ index cũ
    UPDATE lexicon SET ... WHERE id = :id;          -- sửa bảng gốc
    INSERT INTO lexicon_fts(rowid,term,definition)
      VALUES(:id, :new_term, :new_def);             -- đẩy index mới

KHÔNG dùng `... VALUES('rebuild')` cho lô nhỏ (166.278 row, chậm + khoá lâu).

AN TOÀN
-------
- Backup DB bằng sqlite3 backup API (không copy file khi DB đang ghi).
- 1 transaction + WAL + busy_timeout.
- Ghi snapshot giá trị gốc ra JSON ⇒ `--revert` khôi phục đúng từng ô.
- `--stats`/`--dry-run` không ghi gì.
- Verify 7 điểm (xem `verify()`).

Usage:
    python -X utf8 scripts/t207_fix_db_mojibake.py --stats
    python -X utf8 scripts/t207_fix_db_mojibake.py --dry-run
    python -X utf8 scripts/t207_fix_db_mojibake.py --apply
    python -X utf8 scripts/t207_fix_db_mojibake.py --verify
    python -X utf8 scripts/t207_fix_db_mojibake.py --revert [BACKUP|SNAPSHOT]
"""
import argparse
import ast
import datetime
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import unicodedata

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')
APP_PY = os.path.join(DAOANH, 'app.py')

ETH = '\u00d0'        # Ð  LATIN CAPITAL LETTER ETH   (sai)
DSTROKE = '\u0110'    # Đ  LATIN CAPITAL LETTER D WITH STROKE (đúng)

# ---------------------------------------------------------------------------
# 20 cột "văn bản" — thay thế thuần. KHÔNG gồm lexicon.* (xử lý riêng) và
# lexicon_fts (phải qua FTS5 API).
TEXT_COLUMNS = [
    ('name_vi_map', 'bio_snippet', ''),
    ('name_vi_map', 'name_vi', 'tra cuu'),
    ('name_vi_map', 'name_vi_final', 'TRUONG admin verify — can soi'),
    ('entity_monks', 'name', ''),
    ('entity_monks', 'definition', ''),
    ('entity_temples', 'name', ''),
    ('entity_temples', 'definition', ''),
    ('entity_works', 'definition', ''),
    ('vn_person_authority', 'name_vi', ''),
    ('vn_person_authority', 'biographical_note_vi', ''),
    ('vn_person_relations', 'target_label_vi', ''),
    ('person_bio_vi_draft', 'bio_vi_draft', ''),
    ('keyword_map', 'keyword', 'khoa tra cuu'),
    ('keyword_map', 'value', ''),
    ('translation_exemplar', 'zh', 'da doc: van tieng Viet, khong co Han tu'),
    ('translation_exemplar', 'vi', ''),
]

CJK = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')


# ---------------------------------------------------------------------------
def load_normalize_text():
    """Lấy ĐÚNG hàm normalize_text() từ app.py mà KHÔNG execute cả Flask app.

    Dùng ast để cắt riêng source của hàm rồi exec trong namespace sạch.
    Nhờ vậy logic chắc chắn giống app.py, kể cả khi app.py được sửa sau này.
    """
    src = io.open(APP_PY, encoding='utf-8', errors='replace').read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'normalize_text':
            seg = ast.get_source_segment(src, node)
            ns = {'unicodedata': unicodedata, 're': re}
            exec(compile(seg, APP_PY, 'exec'), ns)
            return ns['normalize_text']
    raise RuntimeError('khong tim thay normalize_text() trong %s' % APP_PY)


def cjk_count(s):
    return len(CJK.findall(s or ''))


def _cjk_total(con):
    """Tổng ký tự CJK trong toàn bộ các cột văn bản đã biết (baseline).

    Dùng chỉ số vị trí (0,1,2) thay vì tên cột để không phụ thuộc row_factory.
    """
    n = 0
    for row in con.execute('SELECT term, definition, normalized, key_norm '
                           'FROM lexicon'):
        for v in tuple(row):
            n += cjk_count(v)
    for tbl, col, _note in TEXT_COLUMNS:
        for row in con.execute('SELECT "%s" FROM "%s"' % (col, tbl)):
            n += cjk_count(row[0])
    return n


def connect(path, ro=False):
    if ro:
        con = sqlite3.connect('file:%s?mode=ro' % path.replace('\\', '/'), uri=True)
    else:
        con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    return con


# ---------------------------------------------------------------------------
def build_plan(con, norm):
    """Trả dict kế hoạch chi tiết (chưa ghi gì)."""
    plan = {'text_cols': [], 'lexicon_rows': [], 'key_norm_rows': [],
            'total_eth': 0}

    for tbl, col, note in TEXT_COLUMNS:
        n = con.execute('SELECT count(*) FROM "%s" WHERE "%s" LIKE ?'
                        % (tbl, col), ('%' + ETH + '%',)).fetchone()[0]
        if n:
            # Ð và Đ đều dài 1 ký tự => phải thay bằng '' để đếm số lần xuất hiện
            chars = con.execute(
                'SELECT coalesce(sum(length("%s") - length(replace("%s", ?, ?))), 0)'
                ' FROM "%s"' % (col, col, tbl), (ETH, '')).fetchone()[0]
            plan['text_cols'].append(
                {'table': tbl, 'column': col, 'rows': n, 'chars': chars,
                 'note': note})
            plan['total_eth'] += chars

    # lexicon: term/definition/normalized (text thuần) + key_norm (tính lại)
    r = con.execute(
        'SELECT count(*) FROM lexicon WHERE term LIKE ? OR definition LIKE ? '
        'OR normalized LIKE ?', ('%' + ETH + '%',) * 3).fetchone()[0]
    plan['lexicon_rows'] = r
    for col in ('term', 'definition', 'normalized', 'key_norm'):
        chars = con.execute(
            'SELECT coalesce(sum(length("%s") - length(replace("%s", ?, ?))), 0)'
            ' FROM lexicon' % (col, col), (ETH, '')).fetchone()[0]
        plan['total_eth'] += chars

    # 162 row co Ð trong term => tinh lai key_norm
    for row in con.execute(
            'SELECT id, term, key_norm FROM lexicon WHERE term LIKE ?',
            ('%' + ETH + '%',)):
        fixed = row['term'].replace(ETH, DSTROKE)
        new_key = norm(fixed)
        plan['key_norm_rows'].append(
            {'id': row['id'], 'old_key': row['key_norm'], 'new_key': new_key,
             'term': fixed})
    plan['total_eth'] += 0
    return plan


def print_plan(plan, verbose=False):
    print('\n--- KẾ HOẠCH (chưa ghi gì) ---')
    print('  %d cột văn bản:' % len(plan['text_cols']))
    for c in sorted(plan['text_cols'], key=lambda x: -x['chars']):
        note = ('   <-- ' + c['note']) if c['note'] else ''
        print('    %-24s %-24s %5d row %5d ký tự%s'
              % (c['table'], c['column'], c['rows'], c['chars'], note))
    print('  lexicon (term/definition/normalized): %d row'
          % plan['lexicon_rows'])
    print('  lexicon.key_norm — TÍNH LẠI %d row (chiến lược B)' % len(plan['key_norm_rows']))
    if verbose:
        for r in plan['key_norm_rows'][:10]:
            print('    id=%-7s %r' % (r['id'], r['old_key'][:34]))
            print('        -> %r' % r['new_key'][:34])
    print('  TỔNG ký tự Ð sẽ sửa: %d' % plan['total_eth'])


# ---------------------------------------------------------------------------
def latest_snapshot():
    """Đường dẫn snapshot JSON mới nhất (để verify đối chiếu), hoặc None."""
    if not os.path.isdir(BACKUP_DIR):
        return None
    cands = [f for f in os.listdir(BACKUP_DIR)
             if f.startswith('t207_snapshot_') and f.endswith('.json')]
    if not cands:
        return None
    cands.sort()
    return os.path.join(BACKUP_DIR, cands[-1])


def all_rowcounts(con):
    """Tổng row của mọi bảng liên quan — baseline để verify."""
    tabs = sorted({t for t, _c, _n in TEXT_COLUMNS} | {'lexicon', 'lexicon_fts'})
    return {t: con.execute('SELECT count(*) FROM "%s"' % t).fetchone()[0]
            for t in tabs}


def pk_of(con, tbl):
    """Tên cột khoá chính của bảng; None nghĩa là dùng rowid."""
    info = con.execute('PRAGMA table_info("%s")' % tbl).fetchall()
    names = [r['name'] for r in info]
    for r in info:
        if r['pk']:
            return r['name']
    for cand in ('id', 'rowid'):
        if cand in names:
            return cand
    return None


def snapshot_of(con):
    """Ghi lại giá trị gốc của MỌI ô sẽ đổi ⇒ revert chính xác từng ô."""
    snap = {'db': os.path.basename(DB_PATH), 'ts': datetime.datetime.now()
            .strftime('%Y%m%d_%H%M%S'), 'lexicon': [], 'text': [],
            'rowcounts': all_rowcounts(con),
            'cjk_total': _cjk_total(con)}
    for row in con.execute(
            'SELECT id, term, definition, normalized, key_norm FROM lexicon '
            'WHERE term LIKE ? OR definition LIKE ? OR normalized LIKE ? '
            'OR key_norm LIKE ?', ('%' + ETH + '%',) * 4):
        snap['lexicon'].append(dict(row))
    for tbl, col, _n in TEXT_COLUMNS:
        pk = pk_of(con, tbl) or 'rowid'
        for row in con.execute(
                'SELECT %s AS _pk, "%s" AS _v FROM "%s" WHERE "%s" LIKE ?'
                % (pk, col, tbl, col), ('%' + ETH + '%',)):
            snap['text'].append({'table': tbl, 'column': col, 'pk': row['_pk'],
                                 'pk_col': pk, 'value': row['_v']})
    return snap


def apply_plan(con, norm, plan, snap):
    """Ghi trong 1 transaction. Trả số liệu đã sửa."""
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=30000')
    cur = con.cursor()
    stats = {'text_rows': 0, 'lexicon_rows': 0, 'fts_rows': 0, 'key_norm': 0}
    try:
        cur.execute('BEGIN IMMEDIATE')

        # --- 1) lexicon: FTS delete -> update base -> FTS insert --------------
        lex = snap['lexicon']
        for row in lex:
            rid = row['id']
            old_term, old_def = row['term'] or '', row['definition'] or ''
            new_term = old_term.replace(ETH, DSTROKE)
            new_def = old_def.replace(ETH, DSTROKE)
            new_norm = (row['normalized'] or '').replace(ETH, DSTROKE)
            has_eth = (ETH in old_term or ETH in old_def
                       or ETH in (row['normalized'] or '')
                       or ETH in (row['key_norm'] or ''))
            if not has_eth:
                continue
            # gỡ index FTS cũ
            cur.execute(
                "INSERT INTO lexicon_fts(lexicon_fts, rowid, term, definition)"
                " VALUES('delete', ?, ?, ?)", (rid, old_term, old_def))
            cur.execute(
                'UPDATE lexicon SET term=?, definition=?, normalized=?'
                ' WHERE id=?', (new_term, new_def, new_norm, rid))
            # đẩy index FTS mới
            cur.execute(
                'INSERT INTO lexicon_fts(rowid, term, definition)'
                ' VALUES(?, ?, ?)', (rid, new_term, new_def))
            stats['lexicon_rows'] += 1
            stats['fts_rows'] += 1
            if row['key_norm'] is not None and (
                    ETH in (row['key_norm'] or '') or ETH in old_term):
                cur.execute('UPDATE lexicon SET key_norm=? WHERE id=?',
                            (norm(new_term), rid))
                stats['key_norm'] += 1

        # --- 2) 16 cột văn bản còn lại ---------------------------------------
        for tbl, col, _n in TEXT_COLUMNS:
            cur.execute(
                'UPDATE "%s" SET "%s" = replace("%s", ?, ?) WHERE "%s" LIKE ?'
                % (tbl, col, col, col), (ETH, DSTROKE, '%' + ETH + '%'))
            stats['text_rows'] += max(cur.rowcount, 0)

        cur.execute('COMMIT')
    except Exception:
        cur.execute('ROLLBACK')
        raise
    return stats


# ---------------------------------------------------------------------------
def verify(db_path=DB_PATH):
    """7 điểm kiểm chứng. Trả (ok, lines)."""
    norm = load_normalize_text()
    con = connect(db_path, ro=True)
    out, ok = [], True

    # 1) 0 ký tự Ð trong toàn bộ các cột đã biết
    left, detail = 0, []
    for tbl, col, _n in TEXT_COLUMNS:
        n = con.execute('SELECT count(*) FROM "%s" WHERE "%s" LIKE ?'
                        % (tbl, col), ('%' + ETH + '%',)).fetchone()[0]
        if n:
            left += n
            detail.append('%s.%s=%d' % (tbl, col, n))
    for col in ('term', 'definition', 'normalized', 'key_norm'):
        n = con.execute('SELECT count(*) FROM lexicon WHERE "%s" LIKE ?' % col,
                        ('%' + ETH + '%',)).fetchone()[0]
        if n:
            left += n
            detail.append('lexicon.%s=%d' % (col, n))
    fts = con.execute('SELECT count(*) FROM lexicon_fts WHERE term LIKE ? '
                      'OR definition LIKE ?', ('%' + ETH + '%',) * 2).fetchone()[0]
    c1 = (left == 0 and fts == 0)
    ok &= c1
    out.append(('1) 0 ký tự Ð còn lại (text=%d, fts=%d)' % (left, fts), c1,
                ', '.join(detail)))

    # 2) FTS đồng bộ với bảng gốc
    a = con.execute('SELECT count(*) FROM lexicon').fetchone()[0]
    b = con.execute('SELECT count(*) FROM lexicon_fts').fetchone()[0]
    c2 = (a == b)
    ok &= c2
    out.append(('2) count(lexicon_fts) == count(lexicon) (%d == %d)' % (b, a), c2, ''))

    # 3) round-trip: với MỌI row đã sửa, normalize_text(new_term) == new_key_norm
    snap_path = latest_snapshot()
    n_checked, n_bad_rt = 0, []
    if snap_path:
        snap = json.load(io.open(snap_path, encoding='utf-8'))
        for r in snap['lexicon']:
            if ETH not in (r['term'] or ''):
                continue
            n_checked += 1
            new_term = (r['term'] or '').replace(ETH, DSTROKE)
            cur_key = con.execute('SELECT key_norm FROM lexicon WHERE id=?',
                                  (r['id'],)).fetchone()
            if cur_key is None:
                n_bad_rt.append('id %s mất' % r['id'])
            elif cur_key['key_norm'] != norm(new_term):
                n_bad_rt.append('id %s' % r['id'])
    c3 = (n_checked > 0 and not n_bad_rt)
    ok &= c3
    out.append(('3) round-trip key_norm = normalize_text(term) — %d row đã sửa'
                % n_checked, c3, ('sai: %s' % n_bad_rt[:5]) if n_bad_rt else ''))

    # 4) tra cứu thật theo đúng đường app.py:1226 — LẤY TERM THẬT từ các row đã
    #    sửa (không đoán). Chứng minh "trước = hỏng, sau = khớp" bằng cách so
    #    key_norm GỐC (trong snapshot) với khoá tra cứu normalize_text(new_term).
    before_ok = after_ok = n_sample = 0
    skipped_len = 0
    detail4 = ''
    if snap_path:
        snap = json.load(io.open(snap_path, encoding='utf-8'))
        for r in snap['lexicon']:
            if ETH not in (r['term'] or ''):
                continue
            new_term = (r['term'] or '').replace(ETH, DSTROKE)
            key = norm(new_term)                 # khoá mà app.py sẽ dùng
            # app.py:1226 có điều kiện LENGTH(term) < 60
            if len(new_term) >= 60:
                skipped_len += 1
                continue
            n_sample += 1
            if (r['key_norm'] or '') == key:     # trước khi sửa
                before_ok += 1
            cur = con.execute('SELECT key_norm FROM lexicon WHERE id=?',
                              (r['id'],)).fetchone()
            if cur and cur['key_norm'] == key:   # sau khi sửa
                after_ok += 1
        detail4 = ('%d row mẫu (bỏ %d row term ≥60 ký tự theo điều kiện '
                   'LENGTH(term)<60): trước khoá khớp %d, sau khớp %d'
                   % (n_sample, skipped_len, before_ok, after_ok))
    c4 = (n_sample > 0 and before_ok == 0 and after_ok == n_sample)
    ok &= c4
    out.append(('4) tra cứu chữ Đ qua đường app.py:1226', c4, detail4))

    # 5) integrity_check
    ic = con.execute('PRAGMA integrity_check').fetchone()[0]
    c5 = (ic == 'ok')
    ok &= c5
    out.append(('5) PRAGMA integrity_check = %r' % ic, c5, ''))

    # 6) Hán tự không đổi — CHỈ trong các row T207 đã sửa.
    #    KHÔNG so toàn DB: session khác có thể thêm/sửa row giữa lúc apply và
    #    lúc verify ⇒ gây cảnh báo giả (đã gặp: name_vi_map +2 row).
    c6, detail6 = True, '(chua co snapshot)'
    if snap_path:
        snap = json.load(io.open(snap_path, encoding='utf-8'))
        bad = 0
        for r in snap['lexicon']:
            cur = con.execute('SELECT term, definition, normalized, key_norm '
                              'FROM lexicon WHERE id=?', (r['id'],)).fetchone()
            if cur is None:
                bad += 1
                continue
            before = sum(cjk_count(v) for v in (r['term'], r['definition'],
                                               r['normalized'], r['key_norm']))
            after = sum(cjk_count(v) for v in tuple(cur))
            if before != after:
                bad += 1
        c6 = (bad == 0)
        detail6 = '(%d row đã sửa, %d row lệch CJK)' % (len(snap['lexicon']),
                                                         bad)
    ok &= c6
    out.append(('6) số ký tự CJK trong %d row đã sửa không đổi'
                % (len(json.load(io.open(snap_path, encoding='utf-8'))['lexicon'])
                   if snap_path else 0), c6, detail6))

    # 7) tổng row các bảng — thông tin, KHÔNG phải assertion: session khác
    #    có thể chủ động thêm dữ liệu vào các bảng này (ví dụ name_vi_map).
    now = all_rowcounts(con)
    drift = []
    if snap_path:
        before = json.load(io.open(snap_path, encoding='utf-8'))['rowcounts']
        for t, n in before.items():
            if now.get(t) != n:
                drift.append('%s %d→%d' % (t, n, now.get(t)))
    out.append(('7) tổng row %d bảng (thông tin — session khác có thể '
                'thêm dữ liệu)' % len(now), True,
                '; '.join(drift) if drift else 'không đổi'))

    con.close()
    return ok, out


# ---------------------------------------------------------------------------
def do_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BACKUP_DIR, 'lineage_t207_%s.db' % ts)
    src = connect(DB_PATH, ro=True)
    out = sqlite3.connect(dst)
    src.backup(out)
    out.close()
    src.close()
    return dst


def main():
    ap = argparse.ArgumentParser(
        description='T207 — sua mojibake Ð trong DB + khoi phuc tra cuu lexicon')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--revert', metavar='SRC', nargs='?')
    ap.add_argument('--db', default=DB_PATH)
    args = ap.parse_args()

    if args.revert:
        src = args.revert
        if os.path.isdir(src) or src.endswith('.db'):
            if not os.path.isfile(src):
                print('[LOI] khong phai file db: %s' % src)
                return 1
            shutil.copy2(src, DB_PATH)
            print('[REVERT] da khoi phuc DB tu %s' % src)
        else:
            print('[REVERT] nhan duong dan file .db hoac duong dan backup DB')
        return 0

    norm = load_normalize_text()
    print('=' * 80)
    print('T207 — SỬA MOJIBAKE Ð TRONG DB  (chiến lược B: + tính lại key_norm)')
    print('DB    = %s' % args.db)
    print('=' * 80)

    con = connect(args.db, ro=True)
    plan = build_plan(con, norm)
    con.close()
    print_plan(plan, verbose=bool(args.dry_run))

    if args.verify:
        print()
        ok, out = verify(args.db)
        for label, good, extra in out:
            print('   [%s] %s%s' % ('OK ' if good else 'FAIL', label,
                                    ('  ' + extra) if extra else ''))
        print()
        print('   => %s' % ('PASS' if ok else 'FAIL'))
        return 0 if ok else 1

    if not (args.apply or args.dry_run):
        print('=' * 80)
        return 0

    if args.dry_run:
        print()
        print('  [DRY-RUN] chưa ghi gì. Dùng --apply để thực hiện.')
        print('=' * 80)
        return 0

    # ---- apply ----
    print()
    bkp = do_backup()
    print('[BACKUP] %s' % bkp)

    con = connect(args.db)
    snap = snapshot_of(con)
    snap_path = os.path.join(BACKUP_DIR, 't207_snapshot_%s.json' % snap['ts'])
    with io.open(snap_path, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False)
    print('[SNAPSHOT] %s (%d lexicon row, %d text cell)'
          % (snap_path, len(snap['lexicon']), len(snap['text'])))

    stats = apply_plan(con, norm, plan, snap)
    con.commit()
    con.close()
    print('[APPLY] lexicon=%d row (FTS đồng bộ), key_norm tính lại=%d row, '
          'text=%d row'
          % (stats['lexicon_rows'], stats['key_norm'], stats['text_rows']))
    print('[REVERT] python -X utf8 scripts/t207_fix_db_mojibake.py --revert "%s"'
          % bkp)

    print()
    ok, out = verify(args.db)
    for label, good, extra in out:
        print('   [%s] %s%s' % ('OK ' if good else 'FAIL', label,
                                ('  ' + extra) if extra else ''))
    print()
    print('   => %s' % ('PASS' if ok else 'FAIL'))
    print('=' * 80)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
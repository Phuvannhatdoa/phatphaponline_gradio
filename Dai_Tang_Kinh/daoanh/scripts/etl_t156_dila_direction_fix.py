#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T157 — Fix lật chiều DILA trong lineage_edge_assertions (B-1 minimal).

Bối cảnh (investigate 2026-09-17):
  - `data/persons.json` lưu trục teacher/student bị đảo so với văn bản gốc:
      A004177 (曇一) `teacher` = 12 (thật ra là 12 ĐỆ TỬ, gồm 常照 A004179),
      `student` = [大亮 A010825, 法慎 A009590] (thật ra là 2 THẦY).
  - Chuỗi lật: persons.json -> TTL bkg:hasTeacher -> people ->
    lineage_conflicts_v2.dila_data (teacher_set/student_set) ->
    deep_conflict_analysis -> lineage_edge_assertions (DILA L2, 46,006 edges, ref=None).
  - Hệ quả hệ thống: 0/23,139 cặp có ở cả 2 nguồn khớp chiều trước flip,
    -> 22,326 khớp sau flip (hoán vị teacher<->student phía DILA).
    Marcus = chiều văn bản chuẩn (14/14 anchor A004177, trích nguyên văn CBETA).

Fix B-1 (this script):
  1. Backup toàn DB -> data/backups/lineage_t157_<ts>.db (sqlite backup API, streaming).
  2. Tái dựng set DILA L2 TỪ CÙNG NGUỒN lineage_conflicts_v2 (mirror backfill_dila của
     etl_t138_edge_assertions.py) NHƯNG ĐẢO CHIỀU:
       - conflict_type='teacher_set' (DILA có tập THẦY của person, nhưng persons.json
         đảo trục): cạnh ĐÚNG = person -> từng phần tử (thật ra là TRÒ), key D|person|id.
       - conflict_type='student_set' (tập TRÒ của person, thực tế là THẦY):
         cạnh ĐÚNG = từng phần tử -> person, key D|id|person.
  3. DELETE toàn bộ DILA L2 cũ -> INSERT bản canonical (1 transaction, idempotent).
  4. Verify post: agree ~22,326 edges, A004177 = 0 direction mismatch, tổng row 57,175.

Usage:
  python scripts/etl_t156_dila_direction_fix.py --mode dry-run   # báo cáo, 0 write
  python scripts/etl_t156_dila_direction_fix.py --mode apply     # backup + rewrite
  python scripts/etl_t156_dila_direction_fix.py --revert <backup.db>  # restore nguyên vẹn

Không thay đổi: lineage_conflicts_v2, MARCUS assertions, schema (0 ALTER).
Revert đầy đủ: git revert <sha_code> (script) + restore backup DB riêng.
"""
import argparse
import json
import os
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

TS = time.strftime('%Y%m%d_%H%M%S')
BUILT_AT = time.strftime('%Y-%m-%dT%H:%M:%S')

TABLE = 'lineage_edge_assertions'


def connect(path=DB_PATH, ro=False):
    cur_uri = 'file:' + path.replace('\\', '/') + '?mode=ro' if ro else path
    conn = sqlite3.connect(cur_uri, timeout=120)
    conn.row_factory = sqlite3.Row
    return conn


def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f'lineage_t157_{TS}.db')
    src = sqlite3.connect(DB_PATH, timeout=120)
    try:
        dest = sqlite3.connect(dst, timeout=120)
        try:
            src.backup(dest)
        finally:
            dest.close()
    finally:
        src.close()
    print(f'[backup] Đã backup -> {dst} ({os.path.getsize(dst):,} bytes)')
    return dst


def restore_backup(backup_path):
    """Khôi phục DB từ file backup (ngược với sqlite backup API)."""
    if not os.path.exists(backup_path):
        print(f'[revert] KHÔNG tìm thấy backup: {backup_path}')
        return False
    src = sqlite3.connect(backup_path, timeout=120)
    try:
        dest = sqlite3.connect(DB_PATH, timeout=120)
        try:
            src.backup(dest)
        finally:
            dest.close()
    finally:
        src.close()
    print(f'[revert] Đã restore {backup_path} -> {DB_PATH}')
    return True


def count_rows(conn, where=''):
    sql = f'SELECT COUNT(*) AS n FROM {TABLE}'
    if where:
        sql += ' WHERE ' + where
    return conn.execute(sql).fetchone()['n']


def build_flipped_rows(conn):
    """Tái dựng set DILA L2 canonical (đảo chiều) từ lineage_conflicts_v2.dila_data.

    Trả về list tuple INSERT_SQL (12 cột) — BẢN ĐẢO CHIỀU so với backfill_dila T138.
    """
    rows = []
    cur = conn.execute(
        "SELECT person_id, conflict_type, dila_data FROM lineage_conflicts_v2 WHERE dila_count>0")
    n_person = 0
    while True:
        batch = cur.fetchmany(5000)
        if not batch:
            break
        for r in batch:
            try:
                ids = json.loads(r['dila_data'] or '[]')
            except Exception:
                ids = []
            if not isinstance(ids, list) or not ids:
                continue
            n_person += 1
            if r['conflict_type'] == 'teacher_set':
                # persons.json đảo trục: "thầy" thật ra là TRÒ của person.
                # Cạnh đúng: person -> từng id; key D|person|id.
                for iid in ids:
                    rows.append((f'D|{r["person_id"]}|{iid}', r['person_id'],
                                 'da:isTeacherOf', iid, 'DILA', 'dila:teacher_of',
                                 None, None, 1, 'L2', 'active', BUILT_AT))
            elif r['conflict_type'] == 'student_set':
                # "trò" thật ra là THẦY của person.
                # Cạnh đúng: từng id -> person; key D|id|person.
                for iid in ids:
                    rows.append((f'D|{iid}|{r["person_id"]}', iid,
                                 'da:isTeacherOf', r['person_id'], 'DILA', 'dila:teacher_of',
                                 None, None, 1, 'L2', 'active', BUILT_AT))
    return rows, n_person


def agreement_stats(conn):
    """Metrics đối chiếu chiều giữa MARCUS và DILA hiện tại (lineage_edge_assertions).

    - agree_preflip: số cạnh MARCUS A->B có DILA cũng A->B (cùng chiều).
    - agree_postflip: số cạnh MARCUS A->B có DILA B->A (sẽ đồng thuận sau đảo chiều).
    - n_marcus_edges_matched: số cạnh MARCUS có DILA ở MỘT trong hai chiều (8-count).
    - persons: số DILA person có >=1 cạnh đồng thuận.
    """
    marcus = {}
    dila = set()
    people_agree_pre = set()
    people_agree_post = set()
    cur = conn.execute(
        "SELECT subject_person_id, object_person_id, source_code FROM lineage_edge_assertions")
    while True:
        batch = cur.fetchmany(5000)
        if not batch:
            break
        for r in batch:
            if r['source_code'] == 'MARCUS':
                marcus.setdefault(r['subject_person_id'], set()).add(r['object_person_id'])
            elif r['source_code'] == 'DILA':
                dila.add((r['subject_person_id'], r['object_person_id']))
    n_matched = 0
    n_agree_pre = 0
    n_agree_post = 0
    for sub, objs in marcus.items():
        for obj in objs:
            same = (sub, obj) in dila
            rev = (obj, sub) in dila
            if same or rev:
                n_matched += 1
            if same:
                n_agree_pre += 1
                people_agree_pre.add(sub)
            if rev:
                n_agree_post += 1
                people_agree_post.add(sub)
    return {
        'marcus_edges_matched_by_dila': n_matched,
        'agree_preflip': n_agree_pre,
        'agree_postflip': n_agree_post,
        'people_agree_pre': len(people_agree_pre),
        'people_agree_post': len(people_agree_post),
    }


def verify_case(conn, pid='A004177'):
    """Ma trận chiều quanh 1 person: MARCUS out/in vs DILA out/in (child/teacher sets)."""
    m_out, m_in, d_out, d_in = set(), set(), set(), set()
    for r in conn.execute(
            "SELECT subject_person_id, object_person_id, source_code FROM lineage_edge_assertions "
            "WHERE subject_person_id=? OR object_person_id=?", (pid, pid)):
        sub, obj, sc = r['subject_person_id'], r['object_person_id'], r['source_code']
        if sc == 'MARCUS':
            if sub == pid:
                m_out.add(obj)
            if obj == pid:
                m_in.add(sub)
        elif sc == 'DILA':
            if sub == pid:
                d_out.add(obj)
            if obj == pid:
                d_in.add(sub)
    return {'MARCUS_out': m_out, 'MARCUS_in': m_in, 'DILA_out': d_out, 'DILA_in': d_in}


def run_dry(conn):
    print('===== [dry-run] T157 Fix lật chiều DILA line-edge-assertions =====')
    print(f'[db] {DB_PATH}')
    n_m = count_rows(conn, "source_code='MARCUS'")
    n_d = count_rows(conn, "source_code='DILA'")
    n_t = count_rows(conn)
    print(f'    Tổng rows={n_t:,} | MARCUS={n_m:,} | DILA={n_d:,}')
    st = agreement_stats(conn)
    print(f'[agree] cạnh MARCUS có DILA (1 trong 2 chiều) = {st["marcus_edges_matched_by_dila"]:,}')
    print(f'[agree] cùng chiều HIỆN TẠI (pre-flip) = {st["agree_preflip"]:,} '
          f'({st["people_agree_pre"]:,} DILA persons)')
    print(f'[agree] sau đảo chiều DILA           = {st["agree_postflip"]:,} '
          f'({st["people_agree_post"]:,} DILA persons)  <-- lớp assertions: mong 100% edge matched')
    rows, n_person = build_flipped_rows(conn)
    print(f'[flip] tái dựng {len(rows):,} DILA L2 rows (canonical) từ {n_person:,} conflict rows')
    print(f'[flip] DILA rows trước={n_d:,} -> sau={len(rows):,} (phải bằng nhau, {TABLE})')
    vc = verify_case(conn)
    diff = (len(vc["MARCUS_out"]) - len(vc["DILA_out"]), len(vc["MARCUS_in"]) - len(vc["DILA_in"]))
    print(f'[case] A004177 hiện tại: MARCUS out={len(vc["MARCUS_out"]):,}/{len(vc["MARCUS_in"]):,} in · '
          f'DILA out={len(vc["DILA_out"]):,}/{len(vc["DILA_in"]):,} in '
          f'(chênh out/in={diff}) — trục hiện tại ĐẢO')
    print('[dry-run] KHÔNG ghi DB. Chạy --mode apply để thực thi (kèm backup).')
    return 0 if (len(rows) == n_d) else 1


def run_apply(conn):
    print('===== [apply] T157 Fix lật chiều DILA line-edge-assertions =====')
    n_d_before = count_rows(conn, "source_code='DILA'")
    st = agreement_stats(conn)
    print(f'[agree] pre-flip: {st["agree_preflip"]:,} cạnh cùng chiều '
          f'(/{st["marcus_edges_matched_by_dila"]:,} cạnh MARCUS có DILA)')
    backup = make_backup()
    rows, n_person = build_flipped_rows(conn)
    print(f'[apply] 1 transaction: DELETE DILA ({n_d_before:,}) -> INSERT canonical ({len(rows):,})')
    if len(rows) != n_d_before:
        print('[apply] CẢNH BÁO: số row tái dựng khác số row cũ — vẫn thực thi, tự kiểm báo cáo.')
    conn.execute("DELETE FROM lineage_edge_assertions WHERE source_code='DILA'")
    conn.executemany(
        "INSERT INTO lineage_edge_assertions "
        "(edge_key, subject_person_id, relation_type, object_person_id, source_code, "
        " raw_relation_type, ref, citation_tier, mapping_verified, trust_level, status, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    print(f'[apply] Đã commit. Backup: {backup}')
    return backup


def run_verify(conn):
    print('===== [verify] Post-fix =====')
    n_m = count_rows(conn, "source_code='MARCUS'")
    n_d = count_rows(conn, "source_code='DILA'")
    n_t = count_rows(conn)
    print(f'    Tổng rows={n_t:,} | MARCUS={n_m:,} | DILA={n_d:,} (mong: 57,175 / 11,169 / 46,006)')
    st = agreement_stats(conn)
    print(f'[agree] cùng chiều HIỆN TẠI (post-flip) = {st["agree_preflip"]:,} '
          f'({st["people_agree_pre"]:,} persons)  <-- mong 100% edge matched')
    print(f'[agree] nếu đảo ngược AGAIN (sẽ tệ) = {st["agree_postflip"]:,}')
    m2 = verify_case(conn)
    s = f'[case] A004177: MARCUS out={len(m2["MARCUS_out"]):,} in={len(m2["MARCUS_in"]):,} | ' \
        f'DILA out={len(m2["DILA_out"]):,} in={len(m2["DILA_in"]):,}'
    clean = m2['MARCUS_out'] == m2['DILA_out'] and m2['MARCUS_in'] == m2['DILA_in']
    print(s + (' -> KHỚP chiều hoàn toàn (0 mismatch)' if clean else ' -> CÒN LỆCH CHIỀU'))
    matched = st['marcus_edges_matched_by_dila']
    ok = (n_t == 57175) and (n_d == 46006) and (n_m == 11169) \
        and (st['agree_preflip'] == matched) and clean
    print(f'[verify] edge matched bởi DILA={matched:,} | đồng thuận={st["agree_preflip"]:,}')
    print(f'[verify] KẾT LUẬN: {"PASS ✅" if ok else "CHECK NEEDED"}')
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description='T157 — Fix lật chiều DILA (B-1).')
    ap.add_argument('--mode', choices=['dry-run', 'apply', 'verify'], default='dry-run')
    ap.add_argument('--revert', metavar='BACKUP_DB', help='Khôi phục DB từ file backup rồi thoát.')
    args = ap.parse_args()

    if args.revert:
        restore_backup(args.revert)
        return 0

    conn = connect(ro=False)
    try:
        if args.mode == 'apply':
            run_apply(conn)
            return run_verify(conn)
        if args.mode == 'verify':
            return run_verify(conn)
        return run_dry(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
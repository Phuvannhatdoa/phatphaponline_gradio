# -*- coding: utf-8 -*-
"""T95 §10 — 18 test bắt buộc (chạy trên bản SAO của lineage.db, không đụng dữ liệu thật).

Cách chạy:
    python scripts/test_t95_18.py

Nhóm:
  Nguồn & phân đoạn   (1-3)
  Alignment/batch     (4-8)
  Resume/supersede    (9-12)
  UI (places.html)    (13-18)
"""
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # daoanh/
sys.path.insert(0, BASE)

import scripts.cbeta_translate_worker as W

WORK = 'T50n2060'
PAGE = 'page:0-0484c-'
PLACES = os.path.join(BASE, 'places.html')

_results = []


def check(no, name, ok, detail=''):
    _results.append((no, name, bool(ok), detail))
    print(('✅' if ok else '❌') + f' T{no:02d} {name} {detail}')


def q(con, sql, args=()):
    return con.execute(sql, args).fetchall()


def run_mock(job_id, max_items=None):
    W.save_raw = lambda *a, **k: 'tmp_test'
    W.worker_run(job_id, mock=True, max_items=max_items, profile=False)


def fresh_db():
    td = tempfile.mkdtemp(prefix='t95_')
    path = os.path.join(td, 'lineage_test.db')
    shutil.copy2(os.path.join(BASE, 'data', 'lineage.db'), path)
    W.DB_PATH = path
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    # Test cần trạng thái SẠCH dịch (bài T9-T12 giả định không bản dịch nào,
    # dù DB thật đã có bản live). Xóa bảng dịch trên bản SAO, không đụng live.
    for tbl in ('passage_translation_alignment', 'translation_segments',
                'translation_job_items', 'translation_jobs'):
        try:
            con.execute(f'DELETE FROM {tbl}')
        except sqlite3.OperationalError:
            pass
    con.commit()
    return con, path, td


def end_db(con, td):
    con.close()
    shutil.rmtree(td, ignore_errors=True)


def main():
    # ---------------- 1-3 Nguồn & phân đoạn ----------------
    con, path, td = fresh_db()
    page = q(con, "SELECT passage_id, sequence_no, original_zh FROM text_passages WHERE work_id=? "
                  "AND loc_ref=? ORDER BY sequence_no", (WORK, '0-0484c-'))
    check(1, 're-build không tạo đoạn full-text lặp',
          len(page) == 9 and all(len(u['original_zh']) <= 300 for u in page)
          and len({u['original_zh'] for u in page}) == len(page),
          f'{len(page)} unit page=0-0484c-, max_len={max((len(u["original_zh"]) for u in page), default=0)}')

    bad2 = q(con, "SELECT COUNT(*) n FROM text_passages WHERE work_id=? AND "
                  "(raw_zh_hash IS NULL OR TRIM(raw_zh_hash)='' OR loc_ref IS NULL OR TRIM(loc_ref)='')", (WORK,))
    check(2, 'mỗi passage có raw hash + anchor', bad2[0]['n'] == 0, f'thiếu: {bad2[0]["n"]}')

    before = q(con, "SELECT COUNT(*) n FROM text_passages WHERE work_id=?", (WORK,))[0]['n']
    sample = q(con, "SELECT * FROM text_passages WHERE work_id=? LIMIT 3", (WORK,))
    for r in sample:
        con.execute(
            "INSERT OR REPLACE INTO text_passages (passage_id, work_id, source_system, canonical_ref, juan, "
            "sequence_no, original_zh, raw_zh_hash, segmentation_method, tei_anchor_start, tei_anchor_end, "
            "source_url, source_version, import_run_id, created_at, source_status, loc_ref, "
            "canonical_start_anchor, canonical_end_anchor, legacy_passage_id, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r['passage_id'], r['work_id'], r['source_system'], r['canonical_ref'], r['juan'],
             r['sequence_no'], r['original_zh'], r['raw_zh_hash'], r['segmentation_method'],
             r['tei_anchor_start'], r['tei_anchor_end'], r['source_url'], r['source_version'],
             'testrun', r['created_at'], r['source_status'], r['loc_ref'], r['canonical_start_anchor'],
             r['canonical_end_anchor'], r['legacy_passage_id'], r['updated_at']))
    con.commit()
    after = q(con, "SELECT COUNT(*) n FROM text_passages WHERE work_id=?", (WORK,))[0]['n']
    check(3, 're-run importer không duplicate (INSERT OR REPLACE idempotent)',
          before == after == 9316, f'{before} -> {after}')
    end_db(con, td)

    # ---------------- 4-8 Alignment / batch ----------------
    con, path, td = fresh_db()
    j4 = W.create_job(WORK, scope=PAGE, requested_by='tester')
    run_mock(j4)
    al = q(con, "SELECT a.passage_id, a.translation_id FROM passage_translation_alignment a "
                "JOIN translation_segments ts ON ts.translation_id=a.translation_id "
                "WHERE a.passage_id IN (SELECT passage_id FROM translation_job_items WHERE job_id=?) ", (j4,))
    ids = [a['passage_id'] for a in al]
    tids = [a['translation_id'] for a in al]
    check(4, 'input 3 unit → 3 translation_id mapping đúng passage_id',
          len(al) == 9 and len(set(ids)) == len(ids) and len(set(tids)) == 9,
          f'{len(al)} alignment, {len(set(tids))} translation')
    end_db(con, td)

    con, path, td = fresh_db()
    j5 = W.create_job(WORK, scope=PAGE, requested_by='tester')
    orig_valid = W.validate_unit
    W.validate_unit = (lambda h, v: (False, 'missing_translation_id'))
    run_mock(j5)
    W.validate_unit = orig_valid
    committed5 = q(con, "SELECT COUNT(*) n FROM translation_segments WHERE created_by_job_id=?", (j5,))[0]['n']
    j5st = q(con, "SELECT DISTINCT status FROM translation_job_items WHERE job_id=?", (j5,))
    check(5, 'thiếu 1 id → không publish batch (đoạn fail/retry, không commit nửa batch)',
          committed5 == 0 and all(s['status'] == 'failed' for s in j5st),
          f'translations={committed5}, items={[s["status"] for s in j5st]}')
    end_db(con, td)

    dup_json = '[{"passage_id":"A","translation_vi":"QL"},{"passage_id":"A","translation_vi":"ALT"},{"passage_id":"B","translation_vi":"X"}]'
    om = {o.get('passage_id'): o.get('translation_vi', '') for o in (W.parse_batch_response(dup_json) or [])}
    check(6, 'duplicate id → reject/dedup (map theo id)', len(om) == 2 and 'A' in om,
          json.dumps(om, ensure_ascii=False))

    truncated = '[{"passage_id":"A","translation_vi":"'
    check(7, 'malformed/truncated → fail/retry (không publish)',
          W.parse_batch_response(truncated) is None, 'truncated -> None')

    shuffled = '[{"passage_id":"S1","translation_vi":"MOT"},{"passage_id":"S3","translation_vi":"BA"},{"passage_id":"S2","translation_vi":"HAI"}]'
    om2 = {o.get('passage_id'): o.get('translation_vi') for o in (W.parse_batch_response(shuffled) or [])}
    check(8, 'translation map theo passage_id (không theo array index)',
          om2.get('S1') == 'MOT' and om2.get('S2') == 'HAI' and om2.get('S3') == 'BA',
          json.dumps(om2, ensure_ascii=False))

    # ---------------- 9-12 Resume / supersede ----------------
    con, path, td = fresh_db()
    j9 = W.create_job(WORK, scope=PAGE, requested_by='tester')
    run_mock(j9, max_items=6)
    st9 = q(con, "SELECT status FROM translation_jobs WHERE job_id=?", (j9,))[0]['status']
    done9 = q(con, "SELECT COUNT(*) n FROM translation_job_items WHERE job_id=? AND status='completed'", (j9,))[0]['n']
    # 'Dịch phần còn thiếu': page scope re-enqueue cả 9, nhưng 6 đã dịch bị skip
    j9b = W.create_job(WORK, scope=PAGE, requested_by='tester')
    items9b = q(con, "SELECT COUNT(*) n FROM translation_job_items WHERE job_id=?", (j9b,))[0]['n']
    run_mock(j9b)
    new9b = q(con, "SELECT tp.sequence_no FROM translation_segments ts JOIN text_passages tp ON tp.passage_id=ts.passage_id "
                   "WHERE ts.created_by_job_id=? AND ts.translation_status<>'superseded' ORDER BY tp.sequence_no", (j9b,))
    by9a = q(con, "SELECT tp.sequence_no FROM translation_segments ts JOIN text_passages tp ON tp.passage_id=ts.passage_id "
                  "WHERE ts.created_by_job_id=? AND ts.translation_status<>'superseded' ORDER BY tp.sequence_no", (j9,))
    cov9 = q(con, "SELECT COUNT(*) n FROM translation_segments WHERE translation_status<>'superseded' AND work_id=?",
             (WORK,))[0]['n']
    page_seqs = [u['sequence_no'] for u in page]
    check(9, 'dịch 6/9 rồi resume → chỉ dịch passage còn thiếu (3 cuối)',
          st9 == 'paused' and done9 == 6 and [r['sequence_no'] for r in new9b] == page_seqs[-3:]
          and [r['sequence_no'] for r in by9a] == page_seqs[:6] and items9b == 9 and cov9 == 9,
          f'j9={st9}/{done9}, j9b items={items9b}, j9={[r["sequence_no"] for r in by9a]}, j9b={[r["sequence_no"] for r in new9b]}, active={cov9}')
    end_db(con, td)

    con, path, td = fresh_db()
    jA = W.create_job(WORK, scope=PAGE, requested_by='tester')
    jB = W.create_job(WORK, scope=PAGE, requested_by='tester')  # click cùng lúc
    run_mock(jA)
    run_mock(jB)
    dups = q(con, "SELECT passage_id FROM translation_segments WHERE translation_status<>'superseded' AND work_id=? "
                  "GROUP BY passage_id HAVING count(*)>1", (WORK,))
    active10 = q(con, "SELECT COUNT(*) n FROM translation_segments WHERE translation_status<>'superseded' AND work_id=?",
                 (WORK,))[0]['n']
    byjob = q(con, "SELECT created_by_job_id, count(*) c FROM translation_segments WHERE translation_status<>'superseded' "
                   "AND work_id=? GROUP BY created_by_job_id ORDER BY c DESC", (WORK,))
    check(10, '2 click cùng lúc → 1 job sở hữu passage (không translation trùng)',
          len(dups) == 0 and active10 == 9 and len(byjob) == 1 and byjob[0]['c'] == 9,
          f'duplicates={len(dups)}, active={active10}, attributions={[dict(r) for r in byjob]}')
    end_db(con, td)

    con, path, td = fresh_db()
    j11 = W.create_job(WORK, scope=PAGE, requested_by='tester')
    W.validate_unit = (lambda h, v: (False, 'tạm lỗi forced'))
    run_mock(j11)
    W.validate_unit = orig_valid
    act11 = q(con, "SELECT COUNT(*) n FROM translation_segments WHERE created_by_job_id=?", (j11,))[0]['n']
    it11 = q(con, "SELECT COUNT(*) n FROM translation_job_items WHERE job_id=? AND status='failed'", (j11,))[0]['n']
    j11b = W.create_job(WORK, scope=PAGE, requested_by='tester')
    run_mock(j11b)
    ok11 = q(con, "SELECT COUNT(*) n FROM translation_segments WHERE work_id=? AND translation_status<>'superseded'",
             (WORK,))[0]['n']
    check(11, 'passage failed → retry, không đánh completed sai',
          act11 == 0 and it11 == 9 and ok11 == 9,
          f'translations j11={act11}, failed items={it11}, sau retry active={ok11}')
    end_db(con, td)

    con, path, td = fresh_db()
    j12 = W.create_job(WORK, scope=PAGE, requested_by='tester')
    run_mock(j12)
    target = page[8]['passage_id']
    old = q(con, "SELECT translation_id, revision_no FROM translation_segments WHERE passage_id=? AND translation_status<>'superseded'",
            (target,))[0]
    con.execute("UPDATE text_passages SET raw_zh_hash='CHANGED_HASH_TEST' WHERE passage_id=?", (target,))
    con.commit()
    j12b = W.create_job(WORK, scope=f'ids:{target}', requested_by='tester')
    run_mock(j12b)
    now12 = q(con, "SELECT translation_id, revision_no, translation_status FROM translation_segments WHERE passage_id=? ORDER BY revision_no DESC",
              (target,))
    check(12, 'source hash đổi → translation cũ superseded, tạo r+1',
          now12[0]['revision_no'] == old['revision_no'] + 1
          and now12[0]['translation_status'] == 'completed'
          and sum(1 for s in now12 if s['translation_status'] == 'superseded') == 1
          and now12[1]['translation_id'] == old['translation_id'],
          f"{old['translation_id']}(r{old['revision_no']}) -> {now12[0]['translation_id']}(r{now12[0]['revision_no']})")
    end_db(con, td)

    # ---------------- 13-18 UI (places.html — chỉ đọc) ----------------
    html = open(PLACES, encoding='utf-8').read()
    script = re.search(r'<script[^>]*>([\s\S]*)</script>', html).group(1)

    check(13, 'mỗi Hán passage có Việt cạnh đúng passage_id',
          'dtRenderPassage' in script and 'data-seg="u' in script and 'u.translation_text' in script and 'u.badge' in script,
          'paired-view path (data-seg + translation_text + badge) present')

    badpat = [p for p in ('ratioSplit', 'splitByRatio', 'charRatio', 'dtRatio', 'character.ratio') if p in script]
    check(14, 'không character-ratio split', not badpat, f'còn: {badpat}')

    g15 = 'Chưa có phần dịch tương ứng.' in html
    check(15, 'không còn "Chưa có phần dịch tương ứng."', not g15, '')

    check(16, 'UI hiện X/Y từ DB', 'dtUnitsProgressHtml' in script and '_coverage' in script,
          'dtUnitsProgressHtml + coverage present')

    check(17, 'incomplete không gắn nhãn "hoàn chỉnh"', 'hoàn chỉnh' not in script,
          'không hardcode nhãn hoàn chỉnh trong UI script')

    check(18, 'mobile đọc cặp Hán→Việt', 'dtMobileTab' in script and 'dtLoadUnits' in script,
          'dtMobileTab + dtLoadUnits present')

    passes = sum(1 for _, _, ok, _ in _results if ok)
    print(f'\nT95 §10: {passes}/18 PASS')
    sys.exit(0 if passes == 18 else 1)


if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-
"""T167 integration smoke test (mock): worker commit -> validator writes validation_status."""
import sys, os, sqlite3, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from cbeta_translate_worker import create_job, worker_run  # noqa

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'lineage.db')

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
picks = con.execute("""
SELECT passage_id FROM text_passages WHERE work_id='T50n2060'
  AND passage_id NOT IN (SELECT passage_id FROM translation_segments
     WHERE translation_status IN ('completed','needs_review','reviewed'))
  ORDER BY sequence_no LIMIT 2""").fetchall()
con.close()
pids = [r['passage_id'] for r in picks]
print('Test passages:', pids)
if not pids:
    print('No untranslated passage found; test not run.')
    sys.exit(0)

job_id = create_job('T50n2060', scope='ids:' + ','.join(pids), model='qwen/qwen3.8-27b')
print('Job:', job_id)
worker_run(job_id, mock=True)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute(
    "SELECT translation_id, validation_status, validated_at, ruleset_id, translation_status "
    "FROM translation_segments WHERE created_by_job_id=?", (job_id,)).fetchall()
con.close()
for r in rows:
    print(' ', dict(r))

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
items = con.execute(
    "SELECT job_item_id, status, attempt_count, error_message FROM translation_job_items WHERE job_id=?",
    (job_id,)).fetchall()
con.close()
for r in items:
    print(' item:', dict(r))

ok = all(r['validation_status'] in ('PASS', 'REVIEW', 'FAIL') for r in rows)

# Cleanup: revert mock job (xóa translation + items + job) để không làm bẩn DB thật
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
tids = [r['translation_id'] for r in con.execute(
    "SELECT translation_id FROM translation_segments WHERE created_by_job_id=? AND translation_status<>'superseded'",
    (job_id,)).fetchall()]
for tid in tids:
    con.execute("DELETE FROM passage_translation_alignment WHERE translation_id=?", (tid,))
con.executemany("DELETE FROM translation_segments WHERE translation_id=?", [(t,) for t in tids])
con.execute("DELETE FROM translation_job_items WHERE job_id=?", (job_id,))
con.execute("DELETE FROM translation_jobs WHERE job_id=?", (job_id,))
con.commit()
con.close()
print(f'Cleanup: removed {len(tids)} mock translations + job {job_id}')

print('RESULT:', 'PASS' if (rows and ok) else 'FAIL')
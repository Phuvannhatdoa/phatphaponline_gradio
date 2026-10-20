# -*- coding: utf-8 -*-
"""T170 — red-team pipeline tests cho verify_dila_places_groq (R5/R6/R7 + G4 + fix taxonomy).

Chạy: python -X utf8 tests/test_t170_verify_pipeline.py   (không cần API key — mock run trên DB tạm)
"""
import os
import sqlite3
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, REPO)

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  ✅ {name}')
    else:
        FAIL += 1
        print(f'  ❌ {name} {detail}')


# ---- xây DB tạm (giống smoke: place INTEGER id + person TEXT id) ----
fd, db_path = tempfile.mkstemp(suffix='.db', prefix='t170_pipe_')
os.close(fd)
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
con.executescript('''
CREATE TABLE places_dila (id INTEGER PRIMARY KEY, name_zh TEXT);
CREATE TABLE places_pending (id INTEGER PRIMARY KEY, name_vi TEXT);
CREATE TABLE place_groq_audit (
  id INTEGER PRIMARY KEY, name_zh TEXT, dict_vi TEXT, groq_trans_vi TEXT,
  needs_review INTEGER, review_status TEXT, diff_type TEXT, diff_reason TEXT,
  model_id TEXT, batch_id TEXT, prompt_tokens INTEGER, completion_tokens INTEGER, checked_at TEXT);
CREATE TABLE people (id TEXT PRIMARY KEY, name_zh TEXT, name_vi TEXT);
CREATE TABLE person_groq_audit (
  id TEXT PRIMARY KEY, name_zh TEXT, dict_vi TEXT, groq_trans_vi TEXT, final_vi TEXT,
  clean_zh TEXT, meta_note TEXT, variant_zh TEXT, is_uncertain INTEGER,
  needs_review INTEGER, review_status TEXT, diff_type TEXT, diff_reason TEXT,
  model_id TEXT, batch_id TEXT, prompt_tokens INTEGER, completion_tokens INTEGER,
  retry_count INTEGER, last_error TEXT, processing_started_at TEXT, checked_at TEXT);
INSERT INTO places_dila VALUES (1001,'降魔窟'),(1002,'開元寺'),(1003,'大雄寶殿');
INSERT INTO places_pending VALUES (1001,'Giáng Ma Quật'),(1002,'Khai Nguyên Tự'),(1003,'Đại Hùng Bảo Điện');
INSERT INTO people VALUES
 ('A000001','一行','Nhất Hạnh'),
 ('A000002','菩提達磨','Bồ Đề Đạt Ma'),
 ('A000003','慧遠','Thích Huệ Viễn'),
 ('A000004','一行(俗名張遂)','Nhất Hạnh');
''')
con.commit()
con.close()

os.environ['T170_DB'] = db_path
os.environ.pop('T169_DB', None)

# import SAU khi set T170_DB (DB_PATH tính tại import)
from scripts import verify_dila_places_groq as v  # noqa: E402
from scripts.t169_classify import classify_diff  # noqa: E402


def run_main(entity, limit, mock=True, force=True):
    sys.argv = ['verify_dila_places_groq.py', '--entity', entity, '--limit', str(limit),
                '--mock', '--force'] if mock else \
        ['verify_dila_places_groq.py', '--entity', entity, '--limit', str(limit)]
    v.main()


print('=== T170 R6 — red-team parse (flat/nested/fence/regex/empty) ===')
ts, ok, note = v.normalize_groq('```json\n{"trans_vi": "Khai Nguyên Tự"}\n```')
check('R6 fence+flat → trích "Khai Nguyên Tự"', ts == 'Khai Nguyên Tự' and ok, repr((ts, note)))

ts, ok, note = v.normalize_groq('{"result": {"trans_vi": "Đàm Loan"}}')
check('R6 nested dict → trích "Đàm Loan"', ts == 'Đàm Loan' and ok, repr((ts, note)))

ts, ok, note = v.normalize_groq('{"trans_vi": "Bồ Đề Đạt Ma"')
check('R6 JSON hỏng → regex salvage ', ts == 'Bồ Đề Đạt Ma' and ok, repr((ts, note)))

ts, ok, note = v.normalize_groq('   ')
check('R6 rỗng → empty_response (API_EMPTY_RESPONSE)', ts is None and not ok and note == 'empty_response',
      repr((ts, ok, note)))

ts, ok, note = v.normalize_groq('{"hello": 1}')
check('R6 không trans_vi → ok=False', not ok and note in ('unparseable',), repr((ts, ok, note)))

print('\n=== T170 R5 — connection pragma (bỏ WAL, busy_timeout=10000) ===')
con_t = v._con()
bt = con_t.execute('PRAGMA busy_timeout').fetchone()[0]
jm = con_t.execute('PRAGMA journal_mode').fetchone()[0]
con_t.close()
check('R5 busy_timeout = 10000', bt == 10000, repr(bt))
check('R5 journal_mode KHÔNG còn WAL (write-mode)', jm != 'wal', repr(jm))

print('\n=== T170 fix regression — TAXONOMY self-match (T169) ===')
got, _ = classify_diff('大雄寶殿', 'Đại Hùng Bảo Điện', 'Đại Hùng Bảo Điện')
check('cặp 殿 điện/điện self-match → NONE (không false conflict)', got == 'NONE', f'got {got}')
got, _ = classify_diff('白馬寺', 'Bạch Mã Tự', 'Chùa Bạch Mã')
check('Tự↔Chùa thật → TAXONOMY_VARIANT (bảo toàn)', got == 'TAXONOMY_VARIANT', f'got {got}')

print('\n=== T170 pipeline — place INTEGER cursor + G4 de-dupe (--force) ===')
run_main('place', 3)
con = sqlite3.connect(db_path)
pc = con.execute('SELECT COUNT(*) FROM place_groq_audit WHERE review_status="verified"').fetchone()[0]
con.close()
check('place run 1: 3 verified (INTEGER id > 0)', pc == 3, repr(pc))
calls = [0]
v.call_groq = lambda *a, **k: calls.__setitem__(0, calls[0] + 1) or None  # mock chặn API
run_main('place', 3, force=True)
check('place run 2: 0 (G4 skip kể cả --force)', calls[0] == 0 and v._con().execute(
    'SELECT COUNT(*) FROM place_groq_audit').fetchone()[0] == 3, f'calls={calls[0]}, rows={v._con().execute("SELECT COUNT(*) FROM place_groq_audit").fetchone()[0]}')

print('\n=== T170 pipeline — person side-car extras + de-dupe ===')
run_main('person', 5)
con = sqlite3.connect(db_path)
row = con.execute("SELECT clean_zh, meta_note, is_uncertain, review_status FROM person_groq_audit WHERE id='A000004'").fetchone()
n_all = con.execute('SELECT COUNT(*) FROM person_groq_audit').fetchone()[0]
con.close()
check('person run 1: 4 rows', n_all == 4, repr(n_all))
check('R2 meta ghi vào side-car: clean_zh=一行, meta=俗名張遂, uncertain=0',
      row and row[0] == '一行' and '俗名張遂' in (row[1] or '') and row[2] == 0, repr(row))
check('person auto status: A000002 = auto_verified_sanskrit',
      sqlite3.connect(db_path).execute(
          "SELECT review_status FROM person_groq_audit WHERE id='A000002'").fetchone()[0] == 'auto_verified_sanskrit')

calls[0] = 0
run_main('person', 5, force=True)
check('person run 2: 0 (G4 skip auto_* kể cả --force)', calls[0] == 0 and sqlite3.connect(db_path).execute(
    'SELECT COUNT(*) FROM person_groq_audit').fetchone()[0] == 4,
    f'calls={calls[0]}')

try:
    os.remove(db_path)
except OSError:
    pass

print(f'\nT170 verify pipeline (red-team): {PASS} PASS · {FAIL} FAIL')
sys.exit(1 if FAIL else 0)
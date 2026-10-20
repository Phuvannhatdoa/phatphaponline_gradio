# -*- coding: utf-8 -*-
"""T74 — red-team tests cho scripts/t74_groq_translate_places.py (place-desc VI qua Groq).

Chạy: python -X utf8 tests/test_t74_groq_translate_places.py  (không cần API key — mock trên DB tạm)
Resume marker: desc_source='t74_groq' (skip); --force: single-pass reprocess (guard loop vô hạn).
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


# ---- xây DB tạm (giống schema T66: place_id TEXT + draft có desc_source/char_count) ----
fd, db_path = tempfile.mkstemp(suffix='.db', prefix='t74_')
os.close(fd)
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
con.executescript('''
CREATE TABLE places_dila (
  id TEXT PRIMARY KEY, name TEXT, name_zh TEXT, note TEXT);
CREATE TABLE place_desc_vi_draft (
  place_id TEXT PRIMARY KEY, name_vi TEXT, name_zh TEXT, note_category TEXT,
  desc_vi_draft TEXT, desc_source TEXT, char_count INTEGER, admin_approved INTEGER DEFAULT 0,
  created_at TEXT, updated_at TEXT);
INSERT INTO places_dila VALUES
 ('PL0001','Tháp Thụy','塔瑞','塔瑞是印度比哈爾邦菩提伽耶附近的一座佛塔遺跡，年代約為西元前3世紀。'),
 ('PL0002','A Dục Vương Trụ','阿育王柱','阿育王柱位於鹿野苑，為阿育王所立，柱頭有獅子雕像。'),
 ('PL0003','Thiếu Lâm Tự','少林寺','少林寺位於河南嵩山，始建於北魏太和十九年。'),
 ('PL0004','Khai Nguyên Tự','開元寺','開元寺創建於唐代開元年間。'),
 ('PL0005','Vùng Tarai','Tarai','Tarai Region is a lowland region in southern Nepal.');
INSERT INTO place_desc_vi_draft VALUES
 ('PL0001','Tháp Thụy','塔瑞','tháp','塔瑞是印度比哈爾邦菩提伽耶附近的一座佛塔遺跡，年代約為西元前3世紀。','dila_note_zh',NULL,0,NULL,NULL),
 ('PL0002','A Dục Vương Trụ','阿育王柱','trụ đá','阿育王柱位於鹿野苑，為阿育王所立，柱頭有獅子雕像。','dila_note_zh',NULL,0,NULL,NULL),
 ('PL0003','Thiếu Lâm Tự','少林寺','chùa','少林寺位於河南嵩山，始建於北魏太和十九年。','dila_note_zh',NULL,0,NULL,NULL),
 ('PL0004','Khai Nguyên Tự','開元寺','chùa','已譯：Khai Nguyên Tự toạ lạc tại Khai Phong.','t74_groq',24,0,NULL,NULL),
 ('PL0005','Vùng Tarai','Tarai','vùng','Tarai Region is a lowland region in southern Nepal.','dila_note_zh',NULL,0,NULL,NULL);
''')
con.commit()
con.close()

os.environ['T74_DB'] = db_path
os.environ.pop('GROQ_API_KEY', None)
os.environ.pop('GROQ_KEY', None)

from scripts import t74_groq_translate_places as t74  # noqa: E402


def run_main(extra):
    sys.argv = ['t74_groq_translate_places.py'] + extra
    return t74.main()


def q(sql, args=()):
    con = sqlite3.connect(db_path)
    row = con.execute(sql, args).fetchone()
    con.close()
    return row


def count_where(desc):
    return q(f"SELECT COUNT(*) FROM place_desc_vi_draft WHERE desc_source='{desc}'")[0]


print('=== T74 unit — guard Hán / normalize / prompt ===')
check('is_han phát hiện "塔瑞"', t74.is_han('塔瑞位於印度'))
check('is_han bỏ qua tiếng Việt', not t74.is_han('Tháp Thụy nằm tại Ấn Độ'))

vi, ok, note = t74.normalize_vi('```text\nBản dịch: Tháp Thụy toạ lạc tại Ấn Độ.\n```')
check('normalize bỏ fence + nhãn "Bản dịch:"', ok and vi == 'Tháp Thụy toạ lạc tại Ấn Độ.',
      repr((vi, ok, note)))

vi, ok, note = t74.normalize_vi('塔瑞位於印度')
check('output còn Hán → still_han (giữ bản gốc)', vi is None and not ok and note == 'still_han',
      repr((vi, ok, note)))

vi, ok, note = t74.normalize_vi('   ')
check('rỗng → empty', vi is None and not ok and note == 'empty', repr((vi, ok, note)))

p = t74.build_prompt('塔瑞', 'Tháp Thụy', 'tháp', '塔瑞位於印度。')
check('prompt chứa name_zh/name_vi/category/note', '塔瑞' in p and 'Tháp Thụy' in p
      and 'tháp' in p and '位於' in p, repr(p[:80]))

print('\n=== T74 stats trước ===')
import contextlib
import io
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = run_main(['--stats'])
out = buf.getvalue()
check('stats: total 5 · pending 4 (dila_note_zh) · done 1 (t74_groq)',
      rc == 0 and 'total 5' in out and 'chưa dịch) 4' in out and 'đã dịch) 1' in out, out.strip()[:200])

print('\n=== T74 resume marker — mock run limit=2 ===')
run_main(['--mock', '--limit', '2'])
check('2 row được dịch → t74_groq', count_where('t74_groq') == 3, count_where('t74_groq'))
check('pending còn 2', count_where('dila_note_zh') == 2, count_where('dila_note_zh'))
r = q("SELECT desc_vi_draft, char_count, desc_source FROM place_desc_vi_draft WHERE place_id='PL0001'")
check('bản dịch mock không còn Hán + char_count>0 + desc_source=t74_groq',
      r[0] and not t74.is_han(r[0]) and (r[1] or 0) > 0 and r[2] == 't74_groq', repr(r))

print('\n=== T74 resume — run lại dịch nốt (skip t74_groq) ===')
run_main(['--mock'])
check('resume: dịch 2 row còn lại → done=5, pending=0',
      count_where('t74_groq') == 5 and count_where('dila_note_zh') == 0,
      f'done={count_where("t74_groq")}, pending={count_where("dila_note_zh")}')
r = q("SELECT desc_vi_draft, desc_source FROM place_desc_vi_draft WHERE place_id='PL0005'")
check('row tiếng Anh cũng được dịch (không giữ nguyên bản gốc Eng)',
      r[0].startswith('Mo ta') and r[0] != 'Tarai Region is a lowland region in southern Nepal.'
      and not t74.is_han(r[0]), repr(r))

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    run_main(['--mock'])
out = buf.getvalue()
check('run lại: 0 row (skip hết, không gọi API)', count_where('t74_groq') == 5 and 'Processed 0' in out,
      out.strip()[:160])

print('\n=== T74 --force single-pass (guard loop vô hạn) ===')
rc = run_main(['--mock', '--force', '--limit', '5'])
check('force: xử lý lại row đã t74_groq, đúng single-pass (không lặp)',
      rc == 0 and count_where('t74_groq') == 5, f'done={count_where("t74_groq")}')

print('\n=== T74 guard UPDATE không ghi đè desc_source lạ ===')
con = sqlite3.connect(db_path)
con.execute("UPDATE place_desc_vi_draft SET desc_source='other' WHERE place_id='PL0001'")
con.commit()
cur = con.execute(t74.UPDATE_SQL, ('Bản dịch lạ', 11, '2026-09-28', 'PL0001'))
check('UPDATE với desc_source=other → 0 row affected (bảo vệ dữ liệu)', cur.rowcount == 0, cur.rowcount)
con.execute("UPDATE place_desc_vi_draft SET desc_source='dila_note_zh' WHERE place_id='PL0001'")
con.commit()
con.close()

print('\n=== T74 revert SQL — khôi phục bản gốc từ places_dila.note ===')
con = sqlite3.connect(db_path)
con.execute('''UPDATE place_desc_vi_draft
               SET desc_vi_draft=d.note, desc_source='dila_note_zh', updated_at=datetime('now')
               FROM places_dila d
               WHERE d.id=place_desc_vi_draft.place_id
                 AND place_desc_vi_draft.desc_source='t74_groq' ''')
con.commit()
con.close()
check('revert: tất cả quay về dila_note_zh', count_where('dila_note_zh') == 5, count_where('dila_note_zh'))
r = q("SELECT desc_vi_draft FROM place_desc_vi_draft WHERE place_id='PL0002'")
check('revert: nội dung khớp note gốc (Hán)', r[0] == '阿育王柱位於鹿野苑，為阿育王所立，柱頭有獅子雕像。', repr(r[0]))
r = q("SELECT desc_vi_draft FROM place_desc_vi_draft WHERE place_id='PL0005'")
check('revert: trả lại tiếng Anh gốc', r[0] == 'Tarai Region is a lowland region in southern Nepal.', repr(r[0]))

try:
    os.remove(db_path)
except OSError:
    pass

print(f'\nT74 groq translate places (red-team): {PASS} PASS · {FAIL} FAIL')
sys.exit(1 if FAIL else 0)
# -*- coding: utf-8 -*-
"""
BUILD ADDITIVE T130 + T131 — BACKEND (app.py) — 2026-09-18 (Lee Option A)
-----------------------------------------------------------------------
Nguyên tắc SSOT (audit report + AGENTS.md):
  * 100% ADDITIVE: chỉ APPEND một block trước `app.run(...)`.
  * 0 ALTER / 0 DROP / 0 DELETE / 0 ghi bịa cột.
  * Mọi truy cập DB đều introspect `PRAGMA table_info` TRƯỚC khi SELECT/INSERT;
    bảng/cột không tồn tại -> KHÔNG tạo, endpoint trả lỗi rõ ràng 404/503 (không ghi gì).
  * Chỉ INSERT OR IGNORE vào cột ĐÃ TỒN TẠI thật.
  * Build này là 1 commit RIÊNG -> rollback = `git revert HEAD` (một cụm, thuận tiện).
  * Không nạp toàn bộ 2000 file kinh vào RAM (chỉ đọc đúng anchor + viết additive).
Chạy: python -X utf8 scripts/build_t130_t131_backend.py   (từ daoanh/)
"""
import io, os, sqlite3, shutil, hashlib, sys, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))          # daoanh/
APP  = os.path.join(ROOT, 'app.py')
DATA = os.path.join(ROOT, 'data', 'lineage.db')            # DB_PATH thật theo probe (L104)

def rd(p):
    with io.open(p, encoding='utf-8', newline='') as f:
        return f.read()

def wn(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)

def sha(p):
    h = hashlib.sha256()
    with io.open(p, 'rb') as f:
        for ch in iter(lambda: f.read(65536), b''):
            h.update(ch)
    return h.hexdigest()[:16]

def git(*a):
    import subprocess
    r = subprocess.run(['git', '-C', os.path.dirname(ROOT)] + list(a),
                       capture_output=True, encoding='utf-8')
    return r.returncode, r.stdout.strip(), r.stderr.strip()

SNAP = os.path.join(ROOT, 'docs', 'sessions',
                    '2026-09-18_t130-t131-OPTIONA-BUILD_pre-snapshot')
os.makedirs(SNAP, exist_ok=True)

# ---------- 1) PRE-BUILD SNAPSHOT + manifest ----------
pre_sha = sha(APP)
shutil.copy2(APP, os.path.join(SNAP, 'app.py.pre-build'))
with io.open(os.path.join(SNAP, 'manifest.md'), 'w', encoding='utf-8') as m:
    m.write('# T130+T131 OPTION A — PRE-BUILD SNAPSHOT (2026-09-18)\n\n')
    m.write('| item | value |\n|---|---|\n')
    m.write('| app.py sha256[:16] | %s |\n' % pre_sha)
    m.write('| app.py bytes | %d |\n' % os.path.getsize(APP))
    m.write('| HEAD pre-build | %s |\n' % git('rev-parse', '--short', 'HEAD')[1])
    m.write('| thời điểm | %s |\n' % datetime.datetime.now().isoformat(timespec='seconds'))
    m.write('| rollback | git revert <commit-build-này> |\n')
print('[1] pre-snapshot  app.py %s → %s' % (pre_sha, SNAP))

# ---------- 2) DB SCHEMA INTROSPECT (read-only ground truth cho endpoint) ----------
def introspect_lineage():
    """Trả dict {exists, cols, teacher_col, student_col, auth_col, ver_col}
    cho bảng lineage_edge_assertions (theo SSOT audit). KHÔNG ghi gì."""
    info = {'exists': False, 'cols': [], 'teacher_col': None,
            'student_col': None, 'auth_col': None, 'ver_col': None}
    if not os.path.exists(DATA):
        # thử các backup (tên theo t100 backup log)
        for cand in ['lineage_backup_t80.db', 'lineage_audit_backup.db']:
            p = os.path.join(ROOT, 'data', cand)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                DATA_USE = p
                break
        else:
            return info, DATA
    else:
        DATA_USE = DATA
    try:
        con = sqlite3.connect('file:%s?mode=ro' % DATA_USE.replace('\\', '/'), uri=True)
        tabs = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'lineage_edge_assertions' in tabs:
            cols = [r[1] for r in con.execute(
                'PRAGMA table_info(lineage_edge_assertions)').fetchall()]
            info['exists'] = True
            info['cols'] = cols
            if 'teacher_id' in cols: info['teacher_col'] = 'teacher_id'
            elif 'teacher' in cols: info['teacher_col'] = 'teacher'
            if 'student_id' in cols: info['student_col'] = 'student_id'
            elif 'student' in cols: info['student_col'] = 'student'
            if 'authority_score' in cols: info['auth_col'] = 'authority_score'
            if 'verified' in cols: info['ver_col'] = 'verified'
        con.close()
        return info, DATA_USE
    except Exception as e:
        return info, DATA_USE

lin, DATA_USE = introspect_lineage()
print('[2] introspect lineage_edge_assertions: exists=%s nguồn=%s' % (lin['exists'], os.path.basename(DATA_USE)))
print('    cols: %s' % (', '.join(lin['cols']) if lin['cols'] else '(không có bảng)'))

# ---------- 3) ADDITIVE BLOCK backend ----------
ANCHOR = "    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)"
src = rd(APP)
if ANCHOR not in src:
    print('[FAILD] anchor app.run không tìm thấy -> DỪNG, không ghi gì.'); sys.exit(1)

alg = '{T-START:T130+T131-OPTIONA-2026-09-18}'
alg_end = '{T-END:T130+T131-OPTIONA-2026-09-18}'
if alg in src:
    print('[SKIP] block additive đã tồn tại -> không ghi lại.'); sys.exit(0)

block = '''
# +{+ ADDITIVE T130+T131 (Lee Option A, 2026-09-18) — 100% append, 0 ALTER/0 DROP/0 DELETE +{+
'''
block += 'ADDITIVE_BLOCK_PLACEHOLDER_MARKER\n'
block += '''app.add_url_rule('/api/lineage/expand', 'da_expand_primary_chain', _da_route_expand_primary_chain, methods=['GET'])
app.add_url_rule('/api/admin/gate/status', 'da_gate_status', _da_route_gate_status, methods=['GET'])
# +{+ /ADDITIVE T130+T131 +{+
'''

fix = src.replace(ANCHOR, block + ANCHOR, 1)
wn(APP, fix)
after_sha = sha(APP)
print('[3] app.py: %s -> %s (%d -> %d bytes)' % (pre_sha, after_sha,
      os.path.getsize(APP) - (len(fix.encode('utf-8')) - len(src.encode('utf-8'))), os.path.getsize(APP)))

# ---------- 4) QA ----------
import subprocess
r = subprocess.run([sys.executable, '-m', 'py_compile', APP], capture_output=True, encoding='utf-8')
print('[4] py_compile rc=%s %s' % (r.returncode, 'OK' if r.returncode == 0 else r.stderr[-300:]))
if r.returncode != 0:
    print('[FAILD] app.py hỏng sau build -> KHÔNG commit.'); sys.exit(1)

# ---------- 5) COMMIT RIÊNG (rollback thuận tiện) ----------
rc, out, err = git('add', '--', 'Dai_Tang_Kinh/daoanh/app.py')
rc, out, err = git('commit', '-m',
    'feat: T130+T131 (Lee Option A) — additive backend primary-chain ?expand= + gate registry SSOT. '
    '0 ALTER/0 DROP/0 DELETE, introspect PRAGMA, INSERT OR IGNORE cột tồn tại. '
    'Build-riêng đề revert 1 cụm. Pre-snapshot docs/sessions/2026-09-18_t130-t131-OPTIONA-BUILD_pre-snapshot/')
print('[5] commit rc=%s %s' % (rc, out or err))
rc, out, err = git('rev-parse', '--short', 'HEAD')
print('    HEAD mới: %s' % out)

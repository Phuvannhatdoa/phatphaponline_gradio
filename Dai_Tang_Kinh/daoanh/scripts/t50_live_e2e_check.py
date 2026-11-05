"""T50 — E2E live check: nhan lai (adopt) job "mo coi" + chan bam "Dich" trung.

Boi canh (2026-11-04/05):
  app.py cu dung os.kill(pid, 0) de do ton tai tien trinh. Tren Windows day la
  OpenProcess + TerminateProcess ⇒ tra WinError 87 voi job dang song, dashboard
  ghi running=False va bam "Dich" se spawn job thu hai tren cung DB + cung
  quota Groq. Fix: scripts/process_alive.py + guard theo PID that trong app.py.
  Test tu dong (tests/test_t50_startup_windows.py) chi kiem duoc helper; script
  nay kiem tren SERVER DANG CHAY (app.py that) nen can chay tay.

Cach lam (khong ton quota Groq, khong spawn job dich):
  1. Backup data/t50_job_status.json.
  2. Start 1 tien trinh gia (python sleep 120s) lam PID "job dang song".
  3. Ghi status gia: running=false + pid cua tien trinh gia (khong stopped_pid).
  4. GET /job-status  -> PHAI tra running=true, pid=pid gia (adopt).
  5. POST /run       -> PHAI tra ok=false "Dang chay sigla ..." va KHONG spawn.
  6. Luon khoi phuc status goc + kill tien trinh gia (finally).

Guard an toan:
  - Neu tien trinh gia khong song (pid_alive=False) → thoat, KHONG goi /run
    (neu goi se spawn job that).
  - Chi goi /run khi buoc 4 da xac nhan adopt=true.
  - Luon restore status file, ke ca khi loi giua chung.

Su dung:
  python -X utf8 scripts/t50_live_e2e_check.py [--base <thu muc daoanh>]
  (mac dinh lay thu muc cha cua scripts/; server phai dang chay o cong 5000)

Luu y: trong ~2-3 giay status file la gia ⇒ dashboard co the hien sai. Chay khi
khong co ai dang thao tac dashboard.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE = os.path.dirname(HERE)


def get(api, path):
    with urllib.request.urlopen(api + path, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def post(api, path, payload):
    req = urllib.request.Request(
        api + path, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=DEFAULT_BASE,
                    help='Thu muc daoanh (mac dinh: thu muc cha cua scripts/)')
    ap.add_argument('--port', type=int, default=5000)
    args = ap.parse_args()

    base = os.path.abspath(args.base)
    api = f'http://127.0.0.1:{args.port}/daoanh/api/admin/t50'
    status = os.path.join(base, 'data', 't50_job_status.json')
    if not os.path.exists(status):
        print(f'ABORT: khong thay status file: {status}')
        return 2

    sys.path.insert(0, HERE)
    from process_alive import pid_alive

    orig = open(status, encoding='utf-8').read()
    backup = os.path.join(tempfile.gettempdir(), 't50_status_e2e_backup.json')
    shutil.copyfile(status, backup)
    print(f'[1/6] Da backup status → {backup}')

    dummy = subprocess.Popen(
        [sys.executable, '-X', 'utf8', '-c', 'import time; time.sleep(120)'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    results = {'dummy_pid': dummy.pid}
    try:
        time.sleep(1.0)
        if not pid_alive(dummy.pid):
            print('ABORT: tien trinh gia khong song ⇒ khong goi /run '
                  '(se spawn job that). Kiem tra lai Python.')
            return 2

        fake = {'running': False, 'sigla': 'T99nE2E', 'pid': dummy.pid,
                'started_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'queue': []}
        with open(status, 'w', encoding='utf-8') as f:
            json.dump(fake, f, ensure_ascii=False, indent=2)
        print(f'[2/6] Da ghi status gia (running=false, pid={dummy.pid} dang song)')

        st = get(api, '/job-status')
        adopted = st.get('running') is True and st.get('pid') == dummy.pid
        results['adopt'] = {'running': st.get('running'), 'pid': st.get('pid'),
                            'sigla': st.get('sigla'), 'ok': adopted}
        print(f'[3/6] /job-status → running={st.get("running")} pid={st.get("pid")} '
              f'{"(adopt OK)" if adopted else "(ADOPT FAIL)"}')

        if adopted:
            r = post(api, '/run', {'sigla': 'T51n2076'})
            blocked = r.get('ok') is False
            results['run'] = {'ok': r.get('ok'), 'error': r.get('error'),
                              'spawned_pid': r.get('pid'), 'blocked': blocked}
            print(f'[4/6] POST /run → ok={r.get("ok")} error={r.get("error")!r} '
                  f'{"(blocked OK)" if blocked else "(NOT BLOCKED!)"}')
        else:
            results['run'] = 'SKIPPED — guard khong kich hoat, khong goi /run'
            blocked = False
            print('[4/6] SKIP POST /run vi adopt khong dung (an toan)')

        after = json.load(open(status, encoding='utf-8'))
        no_new_pid = after.get('pid') == dummy.pid
        results['no_new_pid'] = no_new_pid
        print(f'[5/6] status sau /run → pid={after.get("pid")} '
              f'{"(khong spawn moi)" if no_new_pid else "(CO PID MOI!)"}')
    finally:
        dummy.terminate()
        try:
            dummy.wait(timeout=5)
        except Exception:
            dummy.kill()
        with open(status, 'w', encoding='utf-8') as f:
            f.write(orig)
        st2 = get(api, '/job-status')
        results['restored'] = {'running': st2.get('running'), 'pid': st2.get('pid'),
                               'sigla': st2.get('sigla')}
        print(f'[6/6] Da khoi phuc status goc → running={st2.get("running")} '
              f'pid={st2.get("pid")} sigla={st2.get("sigla")}')

    ok = results.get('adopt', {}).get('ok') and results.get('run', {}).get('blocked') \
        and results.get('no_new_pid')
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print('E2E:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

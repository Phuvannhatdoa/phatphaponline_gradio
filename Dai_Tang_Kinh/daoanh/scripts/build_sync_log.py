"""Sinh admin/sync_log.json cho trang Nhật Ký Sync (admin/sync_log.html).

Đọc: trạng thái các tác vụ đã đặt lịch (Task Scheduler), log sync VPS, log GitBook.
Chạy: python -X utf8 scripts/build_sync_log.py
"""
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'admin' / 'sync_log.json'
SYNC_LOG = Path(os.path.expanduser('~')) / '.claude' / 'logs' / 'sync_daoanh.log'
GITBOOK_LOG = Path(tempfile.gettempdir()) / 'gitbook_daily_update.log'

SCHEDULES = [
    {'task': 'DaoAnh-Sync-1700', 'name': 'Sync code + DB lên VPS', 'when': 'Hằng ngày 17:00', 'kind': 'vps_sync'},
    {'task': 'GitBook_DailyUpdate_1200', 'name': 'GitBook (docs) cập nhật', 'when': 'Hằng ngày 12:00', 'kind': 'gitbook'},
    {'task': 'DaoAnh-Cleanup-Sunday', 'name': 'Dọn rác dev', 'when': 'Chủ nhật 11:00', 'kind': 'generic'},
    {'task': 'PTDA-Dashboard-Serve', 'name': 'Dashboard server (cổng 8090)', 'when': 'Khi đăng nhập Windows', 'kind': 'generic'},
    {'task': 'PTDA-Gateway', 'name': 'Gateway (cổng 8080)', 'when': 'Khi đăng nhập Windows', 'kind': 'generic'},
    {'task': 'PTDA-SyncLog-Build', 'name': 'Làm mới Nhật Ký Sync', 'when': 'Mỗi 10 phút', 'kind': 'generic'},
    {'task': 'dila-progress-report-refresh', 'name': 'Báo cáo tiến độ tích hợp DILA', 'when': 'Hằng ngày 9h và 17h', 'kind': 'cowork', 'hours': [9, 17]},
]

COWORK_DIR = Path(os.path.expanduser('~')) / '.claude' / 'scheduled-tasks'

TS_RE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s{1,}(.*)$')


def read_text(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    for enc in ('utf-8-sig', 'utf-8', 'cp1252'):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return []


def task_states():
    names = [s['task'] for s in SCHEDULES if s['task'] and s['kind'] != 'cowork']
    ps = (
        "$names = @(" + ",".join("'%s'" % n for n in names) + ");"
        "$out = foreach ($n in $names) { $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue; "
        "if ($t) { $i = Get-ScheduledTaskInfo -TaskName $n; [pscustomobject]@{ "
        "name=$n; state=[string]$t.State; last=if($i.LastRunTime -and $i.LastRunTime.Year -gt 2000){$i.LastRunTime.ToString('s')}else{''}; "
        "result=[int64]$i.LastTaskResult; next=if($i.NextRunTime -and $i.NextRunTime.Year -gt 2000){$i.NextRunTime.ToString('s')}else{''} } } "
        "else { [pscustomobject]@{ name=$n; state='MISSING'; last=''; result=$null; next='' } } }; "
        "$out | ConvertTo-Json -Compress"
    )
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
                           capture_output=True, timeout=120)
        data = json.loads(r.stdout.decode('utf-8', 'replace') or '[]')
    except Exception:
        return {}
    if isinstance(data, dict):
        data = [data]
    return {d['name']: d for d in data}


def parse_sync_runs(lines):
    runs, cur = [], None
    for raw in lines:
        m = TS_RE.match(raw)
        if not m:
            continue
        ts, msg = m.group(1), m.group(2).strip()
        if 'START SYNC' in msg:
            cur = {'start': ts, 'end': None, 'status': 'running', 'steps': [], 'errors': [], 'stats': []}
            runs.append(cur)
            continue
        if cur is None:
            if 'ERROR' in msg or 'ALERT' in msg:
                runs.append({'start': ts, 'end': ts, 'status': 'failed', 'steps': [], 'stats': [],
                             'errors': [msg]})
            continue
        if 'SYNC DONE' in msg:
            cur['end'] = ts
            cur['status'] = 'failed' if cur['errors'] else 'ok'
            cur = None
            continue
        if msg.startswith('ALERT') or msg.startswith('ERROR') or 'FAIL' in msg[:12]:
            cur['errors'].append(msg)
        elif msg.startswith('OK') or msg.startswith('[') or 'healthy' in msg or 'VPS service' in msg:
            cur['steps'].append(msg)
        elif 'Transferred' in msg or 'Checks' in msg or 'Elapsed' in msg:
            cur['stats'].append(msg)
        if cur is not None and 'diag' in msg:
            cur['errors'].append(msg)
    for r in runs:
        if r['status'] == 'running':
            r['status'] = 'failed' if r['errors'] else 'unfinished'
    return list(reversed(runs))[:30]


def next_cowork_run(hours, now):
    # Tác vụ Cowork không có NextRunTime trên đĩa: tính từ danh sách giờ chạy trong ngày.
    for day in (0, 1):
        for h in hours:
            cand = (now + timedelta(days=day)).replace(hour=h, minute=0, second=0, microsecond=0)
            if cand > now:
                return cand.isoformat(timespec='seconds')
    return ''


def main():
    states = task_states()
    now = datetime.now()
    schedules = []
    for s in SCHEDULES:
        if s['kind'] == 'cowork':
            # Tác vụ Cowork không nằm trong Task Scheduler: chỉ kiểm tra file định nghĩa còn tồn tại.
            skill = COWORK_DIR / s['task'] / 'SKILL.md'
            st = {'state': 'Ready' if skill.exists() else 'MISSING',
                  'next': next_cowork_run(s['hours'], now)}
        else:
            st = states.get(s['task'], {}) if s['task'] else {}
        schedules.append({
            'name': s['name'], 'task': s['task'] or '—', 'when': s['when'],
            'state': st.get('state', 'NOT_SCHEDULED' if not s['task'] else 'MISSING'),
            'last_run': st.get('last', ''), 'last_result': st.get('result'), 'next_run': st.get('next', ''),
        })
    # Lần tới gần nhất lên trên; dòng không có lần tới xuống cuối.
    schedules.sort(key=lambda x: (x['next_run'] == '', x['next_run']))
    sync_lines = read_text(SYNC_LOG)
    gitbook_lines = read_text(GITBOOK_LOG)
    data = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'schedules': schedules,
        'vps_sync_runs': parse_sync_runs(sync_lines),
        'vps_sync_tail': sync_lines[-40:],
        'gitbook_tail': gitbook_lines[-20:],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'wrote {OUT} ({len(data["vps_sync_runs"])} runs, {len(schedules)} schedules)')


if __name__ == '__main__':
    main()

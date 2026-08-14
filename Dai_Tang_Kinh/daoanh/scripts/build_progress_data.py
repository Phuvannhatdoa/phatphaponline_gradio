#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_progress_data.py — Dashboard Process Tracker: đối chiếu docs/*.md với code Python thật.

Chức năng:
  1. Parse tài liệu docs/*.md (tasktodo.md, progress.md, roadmap.md, pipelines.md, db_schema.md, DEV_HISTORY.md)
     → trích module (headers ##/###), trạng thái [OK]/⏳/[ERR], và "claim" (route/script/func được docs nhắc tới).
  2. Scan code Python (app.py, server.py, api_ttl_rebuild.py, conflict_server.py, scripts/*.py,
     src_python/**/*.py, src/python/**/*.py) → danh sách route thật + script/func thật.
  3. Đối chiếu claim vs code thật → tính progress% theo code cho từng module.
  4. Ghi data/progress_data.json (Zero-RAM: chỉ đọc metadata, không nạp data file lớn).

Cách chạy:
  python scripts/build_progress_data.py            # sinh data/progress_data.json + summary
  python scripts/build_progress_data.py --verbose  # in chi tiết từng module

Output JSON schema:
{
  "generated_at": "2026-08-13T12:00:00",
  "total_progress": 62.5,
  "modules": [
    {
      "name": "...", "doc_status": "done|in_progress|pending",
      "progress": 100, "code_found": 8, "code_claimed": 8,
      "routes": ["/api/..."], "warnings": [...]
    }
  ],
  "endpoints_compare": [
    {"path": "/api/...", "method": "GET", "docs_claim": true, "code_found": true}
  ]
}
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime
from collections import Counter

# Ép stdout UTF-8 để in tiếng Việt / ký tự đặc biệt trên console Windows (cp1252)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'progress_data.json')

VERBOSE = '--verbose' in sys.argv

# --- Các file Python cần scan (bỏ qua file nguy hiểm / trùng / ad-hoc) ---
MAIN_APP_FILES = ['app.py', 'server.py', 'api_ttl_rebuild.py', 'conflict_server.py']
SKIP_FILES = {'fix_all.py', 'test_queue.py', 'sync_cbeta_refs.py', '__init__.py', 'rag_worker.py'}
SKIP_DIRS = {'__pycache__', 'node_modules', '.git', 'data', 'docs', 'admin', 'dashboard', 'ontology', 'deploy', 'tests'}

# --- Docs modules: cặp (tên hiển thị, danh sách keyword để nhận diện module trong docs) ---
# Scan TOÀN BỘ docs/*.md (kể cả thư mục con) — mọi .md là cấu trúc hệ thống đã thống nhất,
# claim nào docs nhắc tới đều được đếm là "chức năng cần có" để đối chiếu code thực tế.
DOCS_FILES = sorted(
    os.path.relpath(os.path.join(root, f), DOCS_DIR).replace('\\', '/')
    for root, _dirs, files in os.walk(DOCS_DIR)
    for f in files
    if f.endswith('.md')
)

MODULES = [
    {'name': 'DILA Authority', 'keywords': ['DILA', 'Authority', 'places_dila', 'places_pending', 'namevi_map_places', 'person_staging', 'places_staging']},
    {'name': 'CBETA', 'keywords': ['CBETA', 'cbeta', 'Hán tạng', 'han_sentence', 'PASSAGE', 'translate_gemini_cbeta', 'cbeta_stats']},
    {'name': 'Marcus SNA', 'keywords': ['Marcus', 'marcus', 'SNA', 'conflict', 'glossaries', 'marcus_network']},
    {'name': 'TTL Thiền Sư VN', 'keywords': ['TTL', 'ttl', 'Thiền sư', 'vn_person_authority', 'ontology', 'truoctac', 'panorama', 'rebuild']},
    {'name': 'CBDB', 'keywords': ['CBDB', 'cbdb']},
    {'name': 'Wikipedia', 'keywords': ['Wikipedia', 'wiki']},
    {'name': 'NameVi Map', 'keywords': ['name_vi', 'namevi', 'Name Vi', 'name_vi_map', 'namevi_map_places', 'places_auto_names']},
    {'name': 'Keywords', 'keywords': ['keyword', 'Keyword', 'StarDict', 'keywords']},
    {'name': 'GIS / Places', 'keywords': ['GIS', 'gis', 'map', 'địa danh', 'places', 'place_update', 'chronology', 'geocod']},
    {'name': 'DILA Integration Layer', 'keywords': ['Integration Layer', 'ENTITY', 'entity', 'passages', 'resolve', 'search_all']},
    {'name': 'Translation Pipeline', 'keywords': ['translat', 'Hán-Việt', 'hanviet', 'transliterat', 'dịch', 'hanz']},
    {'name': 'Hạ tầng / Docs', 'keywords': ['docs', 'pipeline', 'automation', 'infra', 'e2e', 'tester', 'login', 'gateway']},
]

# Ánh xạ claim path → module (dựa trên prefix chuẩn hóa). Order quan trọng: khớp trước thắng.
CLAIM_MODULE_RULES = [
    (['/api/cbeta/', '/cbeta/', 'cbeta_', 'translate_gemini_cbeta', 'han_sentence', 'passages', '/api/entity/'], 'CBETA'),
    (['marcus', 'conflict', '/api/queue', '/api/resolve_conflict'], 'Marcus SNA'),
    (['/ttl', '/ttl/', 'rebuild', 'truoctac', 'lexicon', 'save_ttl', '/panorama', 'person_authority', 'ttl_'], 'TTL Thiền Sư VN'),
    (['cbdb'], 'CBDB'),
    (['/wiki', 'wiki_'], 'Wikipedia'),
    (['name_vi', 'namevi'], 'NameVi Map'),
    (['keyword', 'stardict'], 'Keywords'),
    (['/places', 'place_update', '/place/', 'chronology', 'geocod', 'dila_staging'], 'GIS / Places'),
    (['translate', 'transliterat', 'hanviet', 'hvdic', 'hanzi', 'lexicon_matches'], 'Translation Pipeline'),
    (['login', 'gateway', 'emails', 'dashboard'], 'Hạ tầng / Docs'),
    (['/entity/'], 'DILA Integration Layer'),
    (['/api/dila', '/places_dila', '/places_pending', '/admin/places'], 'DILA Authority'),
]


def module_for_claim(claim):
    """Gán claim (endpoint path hoặc script) vào module qua quy tắc prefix."""
    c = claim.lower()
    for needles, module in CLAIM_MODULE_RULES:
        for n in needles:
            if n in c:
                return module
    return None

# --- Hàm tiện ích ---

def norm_path(p):
    """Chuẩn hóa path để so sánh: bỏ prefix /daoanh, bỏ query string,
    thay tham số dạng <x> hoặc ID cụ thể (PL..., số) bằng {}. Ví dụ:
    /daoanh/api/entity/PL000000023255 → /api/entity/{}"""
    p = (p or '').strip()
    if not p.startswith('/'):
        p = '/' + p
    p = re.sub(r'\?.*$', '', p)
    p = p.replace('/daoanh/api', '/api')
    p = re.sub(r'<[^>]*>', '{}', p)
    p = re.sub(r'\{[^}]*\}', '{}', p)  # {id} / {place_id} → {}
    # ID cụ thể trong path → placeholder (khớp route <entity_id>, <place_id>...)
    p = re.sub(r'/[A-Z]{2}\d{5,}|/\d{3,}', '/{}', p)
    # Chuỗi rỗng trong path (vd /api/places/) giữ nguyên dấu slash cuối
    return p


def collect_docs_claims():
    """Đọc tất cả docs/*.md → trả về (module_claims, all_claims).
    module_claims: {module_name: set(claims)} — gán claim vào module qua CLAIM_MODULE_RULES.
    all_claims: set tất cả claim endpoint/script docs nhắc tới.
    """
    all_claims = set()
    for fname in DOCS_FILES:
        fpath = os.path.join(DOCS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f'  [WARN]  Không đọc được {fname}: {e}')
            continue
        # Endpoint claims: /api/... hoặc /daoanh/...
        for m in re.finditer(r'(?<![\w])(/daoanh/api/[A-Za-z0-9_/\-<>{}.?=&]+|/api/[A-Za-z0-9_/\-<>{}.?=&]+)', text):
            all_claims.add(norm_path(m.group(1)))
        # Script claims: scripts/xxx.py hoặc tên file .py trong backtick
        for m in re.finditer(r'`(?:scripts/)?([A-Za-z0-9_\-]+\.py)`', text):
            all_claims.add(m.group(1))

    module_claims = {m['name']: set() for m in MODULES}
    for c in all_claims:
        mod = module_for_claim(c)
        if mod and mod in module_claims:
            module_claims[mod].add(c)

    return module_claims, all_claims


# --- Scan code ---

def scan_routes():
    """Scan các file app chính → list route thật. Trả về (set path chuẩn hóa, list dict)."""
    routes = []
    route_set = set()
    for fname in MAIN_APP_FILES:
        fpath = os.path.join(BASE_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f'  [WARN]  Không đọc được {fname}: {e}')
            continue
        # Bỏ qua phần trong chuỗi "NEW_CODE" (fix_all.py chứa route giả trong string)
        if fname == 'fix_all.py':
            continue
        for m in re.finditer(r'@app\.route\(\s*[\'"]([^\'"]+)[\'"]', text):
            path = m.group(1)
            norm = norm_path(path)
            route_set.add(norm)
            # lấy function kế tiếp
            func_match = re.search(r'def\s+(\w+)\s*\(', text[m.end():])
            func = func_match.group(1) if func_match else '?'
            routes.append({'path': path, 'norm': norm, 'file': fname, 'func': func})
    return route_set, routes


def scan_scripts():
    """Scan scripts/ + src_python + src/python → set script claim (tên file .py)."""
    script_set = set()
    dirs = [SCRIPTS_DIR,
            os.path.join(BASE_DIR, 'src_python'),
            os.path.join(BASE_DIR, 'src', 'python')]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, dirs_, files in os.walk(d):
            dirs_[:] = [x for x in dirs_ if x not in SKIP_DIRS]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                if fname in SKIP_FILES:
                    continue
                script_set.add(fname)
    return script_set


# --- Scan tasks (chuẩn Claude Code: tasks/T<id>-<slug>.md, frontmatter YAML) ---

TASKS_DIR = os.path.join(BASE_DIR, 'tasks')
VALID_STATUSES = {'pending', 'in_progress', 'blocked', 'done'}

def parse_frontmatter(text):
    """Parse frontmatter YAML dạng key: value giữa 2 dòng --- . Trả dict."""
    meta = {}
    if not text.startswith('---'):
        return meta
    lines = text.split('\n')
    if len(lines) < 2:
        return meta
    i = 1
    while i < len(lines) and not lines[i].strip().startswith('---'):
        line = lines[i].strip()
        if ':' in line and not line.startswith('-'):
            key, _, val = line.partition(':')
            meta[key.strip().lower()] = val.strip()
        i += 1
    return meta


def scan_tasks():
    """Scan tasks/*.md → list task dict. Bỏ qua README.md, T-template.md."""
    tasks = []
    if not os.path.isdir(TASKS_DIR):
        return tasks
    for fname in sorted(os.listdir(TASKS_DIR)):
        if not fname.endswith('.md'):
            continue
        if fname.lower() in ('readme.md', 'template.md', 't-template.md'):
            continue
        fpath = os.path.join(TASKS_DIR, fname)
        try:
            with open(fpath, encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f'  [WARN]  Không đọc được task {fname}: {e}')
            continue
        meta = parse_frontmatter(text)
        status = meta.get('status', 'pending')
        if status not in VALID_STATUSES:
            status = 'pending'
        # acceptance criteria: đếm checkbox
        done_criteria = text.count('- [x]') + text.count('- [X]')
        total_criteria = text.count('- [')  # - [x], - [ ], - [~]
        # mô tả chức năng: nội dung phần "## Mục tiêu" (hoặc khối sau frontmatter)
        desc = ''
        mt = re.search(r'##\s*Mục tiêu\s*\n(.*?)(?=\n##\s|\Z)', text, re.S)
        if mt:
            desc = mt.group(1).strip()
        if not desc:
            rest = text.split('\n---\n', 1)
            if len(rest) > 1:
                desc = rest[1].strip()
        desc = ' '.join(desc.split())[:200]
        tasks.append({
            'id': meta.get('id', fname.replace('.md', '')),
            'title': meta.get('title', fname.replace('.md', '').replace('-', ' ')),
            'file': fname,
            'module': meta.get('module', 'Chưa phân loại'),
            'priority': meta.get('priority', 'medium'),
            'status': status,
            'depends_on': meta.get('depends_on', '[]'),
            'created': meta.get('created', ''),
            'updated': meta.get('updated', ''),
            'done_when': meta.get('done_when', ''),
            'desc': desc,
            'criteria_done': done_criteria,
            'criteria_total': total_criteria,
            'blockers': '## Blockers' in text,
        })
    return tasks


# --- Git history: commits (claudecode tạo sau mỗi update code) → Timeline ---

GIT_REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # visjs-app/
GIT_DAOANH_PATH = 'Dai_Tang_Kinh/daoanh'


def scan_git_history():
    """Scan git log của thư mục daoanh → thống kê commit theo module + theo tháng.
    Trả dict {total, first_date, last_date, by_module{}, by_month[]} hoặc None nếu lỗi."""
    try:
        proc = subprocess.run(
            ['git', '-C', GIT_REPO_ROOT, 'log', '--date=short', '--pretty=format:%ad|%s',
             '--', GIT_DAOANH_PATH],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=30, check=False)
    except Exception as e:
        print(f'  [WARN]  Không đọc được git history: {e}')
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        print('  [WARN]  git log daoanh rỗng/lỗi (có phải là git repo? chạy từ git root visjs-app/)')
        return None

    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    dates = []
    by_module = {m['name']: 0 for m in MODULES}
    unmatched = 0
    for line in lines:
        if '|' not in line:
            continue
        date, _, subject = line.partition('|')
        dates.append(date)
        subj_l = subject.lower()
        matched = False
        # Ưu tiên từ khóa module cụ thể hơn trước (order trong MODULES giữ nguyên)
        for mod in MODULES:
            if any(k.lower() in subj_l for k in mod['keywords']):
                by_module[mod['name']] += 1
                matched = True
                break
        if not matched:
            unmatched += 1

    month_counter = Counter(d[:7] for d in dates)
    by_month = sorted(({'month': m, 'commits': c} for m, c in month_counter.items()), key=lambda x: x['month'])
    return {
        'total': len(lines),
        'first_date': dates[-1] if dates else '',
        'last_date': dates[0] if dates else '',
        'by_module': by_module,
        'by_month': by_month,
        'unmatched': unmatched,
    }


# --- Main ---

def doc_status_for(name):
    """Xác định trạng thái docs của module: done (có [OK] và không có 'Còn thiếu'),
    in_progress (có 'Đang'/'Còn thiếu'/⏳), pending (không nhắc tới)."""
    mod = next((m for m in MODULES if m['name'] == name), None)
    if not mod:
        return 'pending'
    mentions = 0
    done = 0
    in_progress = 0
    for fname in DOCS_FILES:
        fpath = os.path.join(DOCS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding='utf-8') as f:
                text = f.read()
        except Exception:
            continue
        for kw in mod['keywords']:
            if kw.lower() in text.lower():
                mentions += 1
                if '✅' in text and 'Còn thiếu' not in text:
                    done += 1
                elif 'Còn thiếu' in text or 'Đang' in text or '⏳' in text:
                    in_progress += 1
                break  # 1 keyword/1 file là đủ
    if mentions == 0:
        return 'pending'
    if done > 0 and in_progress == 0:
        return 'done'
    if in_progress > 0:
        return 'in_progress'
    if done > 0:
        return 'done'
    return 'pending'


def build():
    print('[INFO] Build progress data: docs ↔ code')
    print('─────────────────────────────────────────────')

    module_claims, all_doc_claims = collect_docs_claims()
    route_set, routes = scan_routes()
    script_set = scan_scripts()
    tasks = scan_tasks()
    git_history = scan_git_history()

    if VERBOSE:
        print(f'  Docs claims: {len(all_doc_claims)} endpoint/script được docs nhắc tới')
        print(f'  Route thật  : {len(route_set)}')
        print(f'  Script thật : {len(script_set)}')
        print(f'  Task files  : {len(tasks)}')
        if git_history:
            print(f'  Git commits : {git_history["total"]} ({git_history["first_date"]} → {git_history["last_date"]})')

    modules_out = []
    for mod in MODULES:
        name = mod['name']
        claims = module_claims.get(name, set())
        doc_status = doc_status_for(name)

        found = []
        for c in claims:
            if c.endswith('.py'):
                if c in script_set:
                    found.append(c)
            else:
                if c in route_set:
                    found.append(c)
        code_claimed = len(claims)
        code_found = len(found)
        progress = round(code_found / code_claimed * 100) if code_claimed else (100 if doc_status == 'done' else 0)

        # warnings
        warnings = []
        if claims and code_found < code_claimed:
            missing = sorted(claims - set(found))[:5]
            warnings.append(f'Docs claim {code_claimed} nhưng chỉ tìm thấy {code_found} trong code. Thiếu: {", ".join(missing)}')

        modules_out.append({
            'name': name,
            'doc_status': doc_status,
            'progress': progress,
            'code_found': code_found,
            'code_claimed': code_claimed,
            'routes': sorted(found),
            'warnings': warnings,
        })
        if VERBOSE:
            print(f'  {name}: {code_found}/{code_claimed} → {progress}% ({doc_status})')

    # endpoints_compare: tất cả claim docs vs route thật
    endpoints = []
    for c in sorted(all_doc_claims):
        if c.startswith('/'):
            endpoints.append({
                'path': c,
                'method': 'GET',
                'docs_claim': True,
                'code_found': c in route_set,
            })

    total = round(sum(m['progress'] for m in modules_out) / len(modules_out)) if modules_out else 0

    # task_meta: thống kê tổng quan task cho KPI trên dashboard
    task_meta = {}
    for t in tasks:
        st = t['status']
        task_meta[st] = task_meta.get(st, 0) + 1
    task_meta['total'] = len(tasks)
    if tasks:
        task_meta['done_percent'] = round(task_meta.get('done', 0) / len(tasks) * 100)
    else:
        task_meta['done_percent'] = 0
    task_meta['blocked_tasks'] = [t['id'] for t in tasks if t['status'] == 'blocked']

    out = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'total_progress': total,
        'modules': modules_out,
        'endpoints_compare': endpoints,
        'tasks': tasks,
        'task_meta': task_meta,
        'git_history': git_history,
        'meta': {
            'docs_files': DOCS_FILES,
            'route_total': len(route_set),
            'script_total': len(script_set),
            'task_total': len(tasks),
        },
    }

    try:
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        with open(OUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'[ERR] Lỗi ghi JSON: {e}')
        sys.exit(1)

    print('─────────────────────────────────────────────')
    print(f'[OK] Đã tạo {OUT_PATH}')
    print(f'   {len(modules_out)} module, {len(endpoints)} endpoint đối chiếu, tổng tiến độ {total}%')
    print(f'   {len(tasks)} task trên board (done={task_meta.get("done", 0)}, blocked={task_meta.get("blocked", 0)})')
    if git_history:
        print(f'   Git timeline: {git_history["total"]} commits ({git_history["first_date"]} → {git_history["last_date"]})')
    else:
        print('   Git timeline: không có (không phải git repo?)')


if __name__ == '__main__':
    build()

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
    {'name': 'BDRC Integration', 'keywords': ['BDRC', 'bdrc', 'Buddhist Digital Resource', 'purl.bdrc.io', 'bdrc_adapter', 'entity_source_ids']},
    {'name': 'Translation Pipeline', 'keywords': ['translat', 'Hán-Việt', 'hanviet', 'transliterat', 'dịch', 'hanz']},
    {'name': 'Nexus Visualization', 'keywords': ['Nexus', 'nexus', 'đồ thị tri thức', 'knowledge graph', 'event_text_link', 'api/nexus', 'vis.js', 'root-graph']},
    {'name': 'Hạ tầng / Docs', 'keywords': ['docs', 'pipeline', 'automation', 'infra', 'e2e', 'tester', 'login', 'gateway']},
    {'name': 'Timeline / Event Evidence', 'keywords': ['timeline', 'event', 'time_mention', 'event_evidence', 'event_entities', 'niên đại', 'sự kiện', 'evidence', 'time_authority', 'reign_era']},
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
    (['timeline', 'time_mention', 'event_evidence', 'event_entities', 'reign_era', '/api/timeline', '/api/events'], 'Timeline / Event Evidence'),
    (['/api/nexus', '/nexus', 'event_text_link'], 'Nexus Visualization'),
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


def load_status_overrides():
    """Đọc lớp override status do Admin bấm nút Done trên dashboard.

    Vì sao là lớp override thay vì sửa thẳng `tasks/*.md`:
      * file `.md` là SSOT nhưng có thể đang được nhiều session sửa song song →
        ghi từ web có nguy cơ race/mất nội dung;
      * override là **additive**: xoá `data/task_status_overrides.json` là revert
        trọn vẹn, không cần `git revert`;
      * có provenance (`by` / `at` / `note`) nên ai cũng tra được ai bấm, lúc nào.
    Task `.md` vẫn giữ nguyên lý do + `undone_reason` để làm bản ghi chính.
    """
    path = os.path.join(BASE_DIR, 'data', 'task_status_overrides.json')
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding='utf-8') as fh:
            raw = json.load(fh)
    except Exception as e:
        print('  [WARN] task_status_overrides.json lỗi JSON, bỏ qua: %s' % e)
        return {}
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items()
            if not k.startswith('_') and isinstance(v, dict)}


def apply_status_overrides(tasks):
    """Áp override lên tasks[] và gắn cờ để dashboard biết đâu do Admin bấm Done."""
    ov = load_status_overrides()
    if not ov:
        return tasks
    by_id = {t['id']: t for t in tasks}
    for tid, info in ov.items():
        t = by_id.get(tid)
        if not t:
            continue
        new_status = str(info.get('status', '')).strip()
        if new_status and new_status in VALID_STATUSES:
            t['status'] = new_status
        t['overridden'] = True
        t['override_by'] = info.get('by', '')
        t['override_at'] = info.get('at', '')
        t['override_note'] = info.get('note', '')
    return tasks


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
            'owner': meta.get('owner', ''),
            'created': meta.get('created', ''),
            'updated': meta.get('updated', ''),
            'done_when': meta.get('done_when', ''),
            'undone_reason': meta.get('undone_reason', ''),
            'undone_until': meta.get('undone_until', ''),
            'undone_action': meta.get('undone_action', ''),
            'desc': desc,
            'criteria_done': done_criteria,
            'criteria_total': total_criteria,
            'blockers': '## Blockers' in text,
        })
    return apply_status_overrides(tasks)


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


def collect_frontmatter_ids():
    """Thu thập `id:` trong frontmatter của tasks/*.md + docs/**/*.md.

    Loại trừ thư mục `_book/` (mirror toàn bộ, không phải SSOT).
    File tên bắt đầu bằng `X-` là bản directive/SPEC đã superseded theo quy ước repo,
    chúng cố ý giữ nguyên `id` của bản gốc → không tính là trùng.

    Nếu thiếu `id:` trong frontmatter:
      - file trong `tasks/`  → suy ID từ tiền tố tên file (`T217-...`), vì đây mới là
        task thật và thiếu frontmatter thì sẽ lọt khỏi kiểm tra.
      - file trong `docs/`   → KHÔNG suy. Repo đặt tên report/plan theo ID task
        (`T212-D4-...-prep.md` là phụ đề của task T212), suy ở đây sẽ báo trùng giả
        hàng loạt. Chỉ `id:` frontmatter mới quyết định ở docs/.

    Đọc bằng `utf-8-sig`: 3 file tasks/ (T167, T197, T199) có BOM làm `---` mở
    frontmatter không khớp, suýt biến thành báo trùng giả.

    Trả về `(seen, attached)`: `attached` là các ID có bản docs/ gắn liền với task.
    """
    paths = []
    if os.path.isdir(TASKS_DIR):
        for fname in sorted(os.listdir(TASKS_DIR)):
            if fname.endswith('.md'):
                paths.append((os.path.join(TASKS_DIR, fname), True))
    for root, dirs, files in os.walk(DOCS_DIR):
        dirs[:] = [d for d in dirs if d != '_book']
        for f in files:
            if f.endswith('.md'):
                paths.append((os.path.join(root, f), False))

    seen = {}
    attached = {}
    for path, is_task in paths:
        try:
            with open(path, encoding='utf-8-sig') as fh:
                text = fh.read()
        except Exception:
            continue
        tid = str(parse_frontmatter(text).get('id', '')).strip()
        if not tid and is_task:
            m = re.match(r'^(T\d+)(?=[-_.])', os.path.basename(path))
            tid = m.group(1) if m else ''
        if not tid:
            continue
        # docs/Mimo-Flash/<id>-*.md khai báo `task: tasks/<...>` là bản mở rộng của
        # chính task đó, không phải một task thứ hai cùng ID.
        if not is_task and re.search(r'^task:\s*tasks/', text, re.M):
            attached.setdefault(tid, []).append(path)
            continue
        seen.setdefault(tid, []).append(path)
    return seen, attached


def check_dup_ids():
    """Chế độ `--check-dup-ids`: exit 1 nếu có task ID trùng thật."""
    seen, attached = collect_frontmatter_ids()
    conflicts = {}
    archived = {}
    for tid, files in seen.items():
        live = [p for p in files if not os.path.basename(p).startswith('X-')]
        dead = [p for p in files if os.path.basename(p).startswith('X-')]
        rel = lambda p: os.path.relpath(p, BASE_DIR).replace('\\', '/')
        if len(live) > 1:
            conflicts[tid] = [rel(p) for p in live]
        elif live and dead:
            archived[tid] = [rel(p) for p in live + dead]

    print('─────────────────────────────────────────────')
    print('[DUP-ID] tasks/*.md + docs/**/*.md (đã loại trừ _book/)')
    if archived:
        print(f'[INFO] {len(archived)} ID có bản X- superseded (hợp lệ theo quy ước):')
        for tid in sorted(archived):
            print(f'   {tid}: {archived[tid][0]}')
    if attached:
        print(f'[INFO] {len(attached)} ID có bản docs/ gắn liền task (`task: tasks/...`):')
        for tid in sorted(attached):
            print(f'   {tid}: {len(attached[tid])} file phụ')
    if not conflicts:
        print('[OK] Không có task ID trùng thật.')
        return 0
    print(f'[FAIL] {len(conflicts)} task ID trùng:')
    for tid in sorted(conflicts):
        print(f'   {tid}:')
        for p in conflicts[tid]:
            print(f'      - {p}')
    return 1


if __name__ == '__main__':
    if '--check-dup-ids' in sys.argv:
        sys.exit(check_dup_ids())
    build()




from flask import Flask, jsonify, request, send_from_directory, Response, make_response


import sqlite3


import re


import unicodedata


import os


import json


import hashlib


from datetime import datetime


import requests


import urllib.parse


import shutil


import time


try:
    import anthropic as _anthropic_sdk
except ImportError:
    _anthropic_sdk = None


from flask_cors import CORS


try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass



ANTHROPIC_KEY = os.environ.get('ANTHROPIC_KEY', '')


GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')



# Hán-Việt normalization module (local, no API)
import sys as _sys


_scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')


if _scripts_dir not in _sys.path:
    _sys.path.insert(0, _scripts_dir)


from hanviet_normalization import normalize_text as hanviet_normalize, load_glossary as hanviet_load_glossary


_hanviet_glossary = None



# T165 Rules-Constrained Translation Engine — SSOT module (không import app.py để tránh circular)
_app_dir = os.path.dirname(os.path.abspath(__file__))


if _app_dir not in _sys.path:
    _sys.path.insert(0, _app_dir)


from style_constitution import (  # noqa: E402
    source_hash as _t165_source_hash,
    select_rules as _t165_select_rules,
    style_lock as _t165_style_lock,
    build_style_prompt as _t165_build_style_prompt,
    constitution_hash as _t165_constitution_hash,
    glossary_hash as _t165_glossary_hash,
    invalidate_cache_for_rule as _t165_invalidate_cache_for_rule,
    invalidate_cache_all_semantic as _t165_invalidate_cache_all_semantic,
    lookup_cache as _t165_lookup_cache,
    write_cache as _t165_write_cache,
    log_prompt_metrics as _t165_log_prompt_metrics,
    is_rules_outdated as _t165_is_rules_outdated,
    persist_prompt_metrics as _t165_persist_prompt_metrics,
    PROMPT_METRICS_TABLE as _T165_PROMPT_METRICS_TABLE,
    PROMPT_FORMAT_VERSION as _T165_PROMPT_FORMAT_VERSION,
    extract_match_terms as _t165_extract_match_terms,
    is_trusted_translation as _t166_is_trusted,
    is_draft_translation as _t166_is_draft,
    identity_lock_policy as _t166_identity_lock_policy,
)


from canonical_lock import (  # noqa: E402
    post_check_translation as _t166_post_check_translation,
    # T165-P8.3: entity alignment pilot gate — reuse P8.1 contract
    build_entity_key_map as _p8_build_entity_key_map,
    build_entity_prompt_instruction as _p8_build_entity_prompt_instruction,
    parse_entity_xml as _p8_parse_entity_xml,
    check_entity_assertions as _p8_check_entity_assertions,
)



# [T200] vn_person_authority.dila_id KHÔNG unique (33 nhóm 2–3 dòng) ⇒ mọi tra cứu theo
# dila_id phải có ORDER BY xác định. Helper chuẩn hoá thứ tự ưu tiên theo status
# (verified > pending > auto_ttl > alias_*), tie-break bằng `id`.
from vnpa_lookup import (  # noqa: E402
    VNPA_ORDER_BY as _t200_vnpa_order_by,
    lookup_by_dila as _t200_vnpa_lookup_by_dila,
    map_dila_to_name as _t200_vnpa_map_dila_to_name,
    has_duplicate_dila as _t200_vnpa_has_duplicate_dila,
)



# Console UTF-8 — tránh UnicodeEncodeError cp1252 khi print() tiếng Việt có dấu
for _stream in ('stdout', 'stderr'):
    _stream_obj = getattr(_sys, _stream, None)
    if _stream_obj and hasattr(_stream_obj, 'reconfigure'):
        try:
            _stream_obj.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


del _stream, _stream_obj



ALLOWED_DIRS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admin')]



def verify_session(token):
    try:
        resp = requests.post(
            'http://127.0.0.1:5001/api/login/check',
            json={'session_token': token},
            timeout=5
        )
        return resp.json().get('valid', False)
    except Exception:
        return False



def normalize_text(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    return re.sub(r'\s+', ' ', s).lower().strip()



def _get_work_suggest_cache():
    global _WORK_SUGGEST_CACHE
    if _WORK_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT cbeta_id, title_vi, title_zh, byline_vi AS translator, dynasty_vi AS era
                FROM dila_catalog_works
            """).fetchall()
        finally:
            conn.close()
        cache = []
        for r in rows:
            title_vi = r['title_vi'] or ''
            title_zh = r['title_zh'] or ''
            cache.append({
                'id': r['cbeta_id'], 'title_vi': title_vi, 'title_zh': title_zh,
                'translator': r['translator'], 'era': r['era'],
                '_norm_vi': normalize_text(title_vi), '_norm_zh': title_zh.lower(),
            })
        _WORK_SUGGEST_CACHE = cache
    return _WORK_SUGGEST_CACHE


def _get_place_suggest_cache():
    """Truy van du lieu dia danh tu namevi_map_places."""
    global _PLACE_SUGGEST_CACHE
    if _PLACE_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT DISTINCT dila_id AS id, name_vi AS value, name_zh AS name_zh, source
                FROM namevi_map_places
            """).fetchall()
        finally:
            conn.close()
        seen = set()
        unique = []
        for r in rows:
            if r['value'] in seen:
                continue
            seen.add(r['value'])
            unique.append(dict(r))
        _PLACE_SUGGEST_CACHE = unique
    return _PLACE_SUGGEST_CACHE


def _get_person_with_contribution_cache():
    """Set of person IDs that appear in dila_catalog_contributors."""
    global _PERSON_CONTRIBUTOR_IDS
    if _PERSON_CONTRIBUTOR_IDS is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT DISTINCT person_id FROM dila_catalog_contributors
            """).fetchall()
        finally:
            conn.close()
        _PERSON_CONTRIBUTOR_IDS = {str(row[0]) for row in rows}
    return _PERSON_CONTRIBUTOR_IDS


def parse_han_variants(raw_xml):
    import xml.etree.ElementTree as ET
    if not raw_xml or not raw_xml.strip():
        return []
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    try:
        root = ET.fromstring(raw_xml)
        return [{'text': (pn.text or '').strip(), 'type': pn.get('type', 'main')}
                for pn in root.findall('.//tei:placeName', ns)
                if pn.get('{http://www.w3.org/XML/1998/namespace}lang', '') == 'zho-Hant'
                and (pn.text or '').strip()]
    except Exception:
        return []



def parse_name_variants(raw_xml):
    """Parse ALL placeName elements from TEI raw_xml (any language)."""
    import xml.etree.ElementTree as ET
    if not raw_xml or not raw_xml.strip():
        return []
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    try:
        root = ET.fromstring(raw_xml)
        return [{'lang': pn.get('{http://www.w3.org/XML/1998/namespace}lang', ''),
                 'name': (pn.text or '').strip(),
                 'type': pn.get('type', 'main')}
                for pn in root.findall('.//tei:placeName', ns)
                if (pn.text or '').strip()]
    except Exception:
        return []



app = Flask(__name__)


# Public read API (GET) cần CORS rộng để academic clients có thể query.
# Write/admin endpoints được bảo vệ bằng require_admin + session check trong từng route.
CORS(app, resources={
    r"/daoanh/api/*": {
        "origins": ["https://phatphaponline.org", "http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})



from t265_routes import t265_bp



BASE_DIR = os.path.dirname(os.path.abspath(__file__))


ADMIN_DIR = os.path.join(BASE_DIR, 'admin')


DATA_DIR = os.path.join(BASE_DIR, 'data')


DB_PATH = os.path.join(DATA_DIR, 'lineage.db')


SQLITE_DB = DB_PATH


TTL_OLD_DIR = os.path.join(BASE_DIR, 'data', 'ttl', 'old')


TTL_MASTER_DIR = os.path.join(BASE_DIR, 'ontology', 'ttl', 'monks')


TTL_ARCHIVE_DIR = os.path.join(BASE_DIR, 'data', 'ttl', 'archive')



# CBDB — single real database, read-only
CBDB_PATH = os.path.join(DATA_DIR, 'cbdb', 'cbdb_20260516.sqlite3')



# CBETA — full text content database
CBETA_PATH = os.path.join(DATA_DIR, 'cbeta', 'cbeta.db')



def get_cbeta_conn():
    conn = sqlite3.connect(CBETA_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def get_cbdb_conn():
    conn = sqlite3.connect(CBDB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



from db_core import get_db_connection



# Compatibility alias – many routes still call get_db()
get_db = get_db_connection



# ── Lexicon in-memory cache (load lazily, word-index for fast lookup) ───────────
_LEX_EXACT    = None   # dict: term → source  (exact lookup O(1))


_LEX_LIST     = None   # list of (term, source)


_LEX_WORD_IDX = None   # dict: word_lower → list of int (indices into _LEX_LIST)



_LEX_SOURCE_ABBR = {
    # ASCII source names (tên thực trong DB, không dấu)
    'phat hoc tinh tuyen':          'PH Tinh Tuyển',
    'phat quang dai tu dien':       'PQ Đại TĐ',
    'phat quang tu dien':           'PQ Từ Điển',
    'phap so can ban':              'Pháp Số',
    'danh-tu-thien-hoc':            'TĐ Thiền Học',
    'tu dien thien tong':           'TĐ Thiền Tông',
    'danh tu thien tong':           'TĐ Thiền Tông',
    'tu dien da ngon ngu':          'TĐ Đa Ngôn Ngữ',
    'kho tang phap hoc':            'KTPH',
    'tu dien phat hoc - quang tri': 'PGĐTĐ',
    'tu dien han viet':             'TĐ Hán Việt',
    'tu dien pali':                 'TĐ Pali-Việt',
    'trich luc tu ngu phat hoc':    'Trích Lục TN',
    'nien bieu gian luoc':          'Niên Biểu',
    'tam tang phap so':             'Tam Tạng Pháp Số',
    # Vietnamese diacritics keys (legacy)
    'phật học tinh tuyển':          'PH Tinh Tuyển',
    'từ điển phật học tổng hợp':    'TĐPHTTH',
    'phật quang đại từ điển':       'PQ Đại TĐ',
    'phật quang từ điển':           'PQ Từ Điển',
    'pháp số căn bản':              'Pháp Số',
}



def _abbr_source(src):
    s = (src or '').lower()
    for k, v in _LEX_SOURCE_ABBR.items():
        if k in s:
            return v
    return (src or '')[:20]



def _ensure_lex_cache():
    global _LEX_EXACT, _LEX_LIST, _LEX_WORD_IDX
    if _LEX_EXACT is not None:
        return
    conn = sqlite3.connect(DB_PATH, timeout=10)
    rows = conn.execute("SELECT term, source FROM lexicon").fetchall()
    conn.close()
    _LEX_EXACT    = {}
    _LEX_LIST     = []       # (term_orig, term_lower, source)
    _LEX_WORD_IDX = {}
    for t, s in rows:
        if not t:
            continue
        t_low = t.lower()
        idx   = len(_LEX_LIST)
        _LEX_LIST.append((t, t_low, s))
        if t not in _LEX_EXACT:
            _LEX_EXACT[t] = s
        # word-index: chỉ index term ngắn (≤60 chars = tên riêng, không phải định nghĩa)
        if len(t) <= 60:
            for word_raw in t_low.split():
                # Strip dấu câu đầu/cuối khỏi từ (vd: "đa." → "đa", "20.xà" → "xà")
                word = word_raw.strip('.,;:()[]!?"\'-/\\0123456789')
                if len(word) >= 2:
                    if word not in _LEX_WORD_IDX:
                        _LEX_WORD_IDX[word] = []
                    _LEX_WORD_IDX[word].append(idx)



def _lex_lookup(name_vi):
    """Tra từ điển theo name_vi. Trả '' nếu không tìm thấy."""
    if not name_vi:
        return ''
    _ensure_lex_cache()
    nm_lower = name_vi.lower()
    nm_parts = len(nm_lower.split())
    # Ngưỡng âm tiết tối thiểu cho Hướng 1:
    # term phải có ít nhất max(2, nm_parts-2) âm tiết để tránh match lẻ
    # VD "Ca" (1 âm) không được match "Mạt Điền Để Ca" (4 âm)
    min_t_parts = max(2, nm_parts - 2)
    # 1. Exact match O(1)
    if name_vi in _LEX_EXACT:
        return f"{name_vi} ({_abbr_source(_LEX_EXACT[name_vi])})"
    # 2. Word-index lookup: chỉ duyệt qua tập nhỏ ứng viên
    words = [w.lower() for w in name_vi.split() if len(w) >= 2]
    if not words:
        return ''
    # Dùng từ cuối (thường đặc trưng nhất) để lấy ứng viên
    candidates = _LEX_WORD_IDX.get(words[-1], [])
    if not candidates and len(words) > 1:
        candidates = _LEX_WORD_IDX.get(words[0], [])
    best = None  # (t_parts, t_display, s) — ưu tiên term dài nhất
    for idx in candidates:
        t, t_low, s = _LEX_LIST[idx]
        # Chỉ lấy term ngắn (≤60 chars) để tránh match definition dài
        if len(t) > 60:
            continue
        # Strip số thứ tự và dấu câu đầu/cuối term (vd: "20.Xà Dạ Đa.")
        t_clean = re.sub(r'^[\d\s\.\-\(\)]+|[\.\s\)]+$', '', t_low)
        t_display = re.sub(r'^[\d\s\.\-\(\)]+|[\.\s\)]+$', '', t).strip()
        t_parts = len(t_clean.split())
        # Hướng 2: nm == t_clean (exact word match)
        # Tránh false positive kiểu "Tông Giám" ⊂ "Thạch Sương Tông Giám"
        if nm_lower == t_clean:
            return f"{t_display or t} ({_abbr_source(s)})"
        # Hướng 1: term nằm trong nm (nm dài hơn → có tiền tố như "Tôn Giả", "TS.")
        # Yêu cầu: term ≥ min_t_parts âm tiết — tránh "Ca" match "Mạt Điền Để Ca"
        # Thu thập best (dài nhất) thay vì trả ngay → tránh "lúc 3 lúc 4 chữ"
        if t_clean and t_parts >= min_t_parts and t_clean in nm_lower:
            if best is None or t_parts > best[0]:
                best = (t_parts, t_display or t, s)
    if best:
        return f"{best[1]} ({_abbr_source(best[2])})"
    return ''


# ────────────────────────────────────────────────────────────────────────────────

def ensure_long_id(id_val):

    if id_val is None:
        return None
    s = str(id_val).strip()
    if s.startswith('PL') and len(s) < 15:
        num_part = s[2:]
        s = 'PL' + num_part.zfill(12)
    return s



# ==== Cache danh sách id theo cate (cho places_pending) ====
# Phân loại cate chỉ phụ thuộc places_dila.note_category → tính 1 lần (~100ms cho 59K dòng),
# rồi query qua index id thay vì full-scan 176K dòng + join tên miền dẫn xuất (~11.7s/request).
_CATE_IDS_CACHE = None



def _build_cate_ids_map():
    """Build dict cate → [id thực trong places_pending (cả dạng ngắn + dài)].
    Phân loại cate theo places_dila.note_category thông qua id dẫn xuất.
    Gọi 1 lần (~1-2s cho 176K dòng) rồi cache."""
    global _CATE_IDS_CACHE
    if _CATE_IDS_CACHE is not None:
        return _CATE_IDS_CACHE
    m = {}
    distinct = {}
    conn = get_db_connection()
    try:
        did_cate = {}
        for r in conn.execute("SELECT id, note_category FROM places_dila"):
            nc = (r['note_category'] or '')
            if '寺廟' in nc or '佛塔' in nc or '佛教文化地點' in nc:
                cate = 'temple_site'
            elif '山峰' in nc or '山脈' in nc:
                cate = 'mountain'
            elif '河流' in nc or '湖泊' in nc or '水系' in nc:
                cate = 'river_lake'
            elif '人文地理區域' in nc:
                cate = 'dynasty_region'
            elif '自然地理區域' in nc:
                cate = 'other'
            else:
                cate = 'admin_place'
            did_cate[str(r['id']).strip()] = cate
        for (pid, pzh, pnote) in conn.execute(
            "SELECT id, name_zh, note FROM places_pending"
        ):
            if not pid:
                continue
            pid = str(pid).strip()
            if not pid or not pzh or not pnote:
                continue
            num = pid[2:] if pid.startswith('PL') else pid
            cate = did_cate.get('PL' + num.zfill(12))
            if cate:
                m.setdefault(cate, []).append(pid)
                distinct.setdefault(cate, set()).add('PL' + num.zfill(12))
    finally:
        conn.close()
    _CATE_IDS_CACHE = {"ids": m, "distinct": {k: len(v) for k, v in distinct.items()}}
    return _CATE_IDS_CACHE




def _note_category_to_icon_type(nc, name_zh=''):
    """Map places_dila.note_category → canonical icon_type for Leaflet marker.
    Priority: DILA category field first, name-suffix fallback for ambiguous/missing.
    Spec: MAP_PLACE_TYPE_ICON_MISCLASSIFICATION_001."""
    nc = nc or ''
    nz = name_zh or ''
    if '寺廟' in nc or '佛塔' in nc or '佛教文化地點' in nc:
        return 'temple_site'
    if '山峰' in nc or '山脈' in nc:
        return 'mountain'
    if '河流' in nc or '湖泊' in nc or '水系' in nc or '海洋' in nc:
        return 'river_lake'
    if '人文地理區域' in nc:
        # Anchor to end of name to avoid false positives in transliterations (e.g. 興都庫什山)
        if re.search(r'[國国]$', nz): return 'country'
        if re.search(r'[省]$', nz): return 'province'
        if re.search(r'[州府路]$', nz): return 'prefecture'
        if re.search(r'[縣县郡]$', nz): return 'district'
        if re.search(r'[鎮镇]$', nz): return 'town'
        if re.search(r'[城都]$', nz): return 'city'
        return 'dynasty_region'
    if '自然地理區域' in nc:
        if re.search(r'[洞窟穴]', nz): return 'cave'
        if re.search(r'[關隘峽]', nz): return 'pass'
        return 'natural_region'
    if '非人界' in nc:
        return 'mythological'
    # Ambiguous (地點, 中研院歷史地名, empty) — strict name-suffix fallback only
    # Use compound keywords to avoid false positives (e.g. 藍 in 藍氏 ≠ 伽藍/temple)
    if re.search(r'寺|廟|塔|庵|精舍|伽藍|石窟', nz): return 'temple_site'
    if re.search(r'[山峰嶺崖岳丘]', nz): return 'mountain'
    if re.search(r'[江河湖溪潭海]', nz): return 'river_lake'
    if re.search(r'石窟|[洞穴]', nz): return 'cave'
    if re.search(r'[關隘峽]', nz): return 'pass'
    if re.search(r'[國国]', nz): return 'country'
    if re.search(r'[縣县郡]', nz): return 'district'
    if re.search(r'[州府]', nz): return 'prefecture'
    if re.search(r'[城都]', nz): return 'city'
    if re.search(r'[鎮镇]', nz): return 'town'
    return 'unknown'




# ==== Cache gợi ý lexicon (definition LIKE) cho ai_judge ====
# Query `definition LIKE '%han%'` full-scan bảng lexicon (166K dòng, ~21MB text) không dùng index được.
# Lần đầu sau restart server: disk cache lạnh → ~77s → vượt safeFetch 20s → placevn.html "Timeout!".
# Fix: nạp cả bảng (term, definition_lower) vào RAM 1 lần → substring scan ~100-300ms kể cả lạnh.
# Nhiều địa danh trùng tên Hán (~4.8x) nên cache theo han_name giúp click sau tức thì.
_lexicon_han_cache = {}


_LEXICON_HAN_CACHE_MAX = 500


_LEXICON_MEM = None



def _load_lexicon_mem(conn=None):
    """Load toàn bộ lexicon (term, definition_lower) vào RAM. RAM ~30-40MB, chấp nhận được."""
    global _LEXICON_MEM
    if _LEXICON_MEM is not None:
        return _LEXICON_MEM
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        rows = conn.execute("SELECT term, definition FROM lexicon").fetchall()
        _LEXICON_MEM = [(r['term'], (r['definition'] or '').lower()) for r in rows]
    except Exception:
        _LEXICON_MEM = []
    finally:
        if own:
            conn.close()
    return _LEXICON_MEM



def _lexicon_han_lookup(conn, han_name):
    """Tìm thuật ngữ lexicon có definition chứa han_name (substring, LIKE '%han%'), có cache in-memory.
    Dùng bản RAM nạp 1 lần để tránh full-scan disk ~77s khi cache lạnh."""
    if not han_name:
        return []
    cached = _lexicon_han_cache.get(han_name)
    if cached is not None:
        return cached
    han_low = han_name.lower()
    result = []
    mem = _load_lexicon_mem(conn)
    if mem:
        # SQLite LIKE '%x%' chỉ case-insensitive cho ASCII → so sánh lower() tương đương
        for term, def_low in mem:
            if len(term) < 100 and han_low in def_low:
                result.append(term)
                if len(result) >= 3:
                    break
    else:
        # RAM không tải được (hiếm) → fallback query LIKE cũ
        try:
            rows = conn.execute(
                "SELECT DISTINCT term FROM lexicon WHERE definition LIKE ? AND LENGTH(term) < 100 LIMIT 3",
                ('%' + han_name + '%',)
            ).fetchall()
            result = [r['term'] for r in rows]
        except Exception:
            result = []
    if len(_lexicon_han_cache) >= _LEXICON_HAN_CACHE_MAX:
        oldest = next(iter(_lexicon_han_cache))
        del _lexicon_han_cache[oldest]
    _lexicon_han_cache[han_name] = result
    return result



# ==== Đảm bảo bảng FTS5 places_search_fts có dữ liệu ====
# Cơ chế "gõ mớm" nhanh (FTS5): bảng đã tạo sẵn nhưng index rỗng.
# Populate 1 lần (~4-5s) khi index chưa có dữ liệu. Idempotent — không chạy lại nếu đã có.
# Lưu ý: COUNT(*) trên FTS5 rất chậm (~1.5s cho 118K docs) nên chỉ check 1 lần/process.
_FTS5_READY = {"places_search_fts": False, "places_pending_fts": False}



def ensure_places_search_fts(conn=None, force=False):
    """Populate places_search_fts từ namevi_map_places nếu index đang rỗng.
    Trả về True nếu vừa populate, False nếu đã có sẵn hoặc lỗi."""
    if _FTS5_READY["places_search_fts"] and not force:
        return False
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places_search_fts'"
        ).fetchone()
        if not exists:
            return False
        # T178 perf: COUNT docsize (148ms) + namevi COUNT (22ms) → LIMIT 1 (0.2ms)
        any_row = conn.execute("SELECT rowid FROM places_search_fts LIMIT 1").fetchone()
        if force or not any_row:
            conn.execute(
                "INSERT INTO places_search_fts(places_search_fts, rowid, name_vi, name_zh, dila_id) "
                "SELECT NULL, id, name_vi, name_zh, dila_id FROM namevi_map_places WHERE name_vi IS NOT NULL"
            )
            conn.commit()
            _FTS5_READY["places_search_fts"] = True
            return True
        _FTS5_READY["places_search_fts"] = True
        return False
    except Exception as e:
        return False
    finally:
        if own:
            conn.close()



def ensure_places_pending_fts(conn=None, force=False):
    """Đảm bảo bảng FTS5 places_pending_fts có dữ liệu.
    FTS thường (lưu nội dung, không external-content vì places_pending.id không unique).
    Cover cả địa danh chưa map + name_vi_norm (tìm không dấu). Populate 1 lần ~5-7s."""
    if _FTS5_READY["places_pending_fts"] and not force:
        return False
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places_pending_fts'"
        ).fetchone()
        if not exists:
            conn.execute(
                "CREATE VIRTUAL TABLE places_pending_fts USING fts5(id, name_vi, name_zh, name_vi_norm)"
            )
            conn.commit()
        # T178 perf: tránh COUNT(*) 7.8s (JOIN) + 565ms (FTS) — chỉ cần biết FTS có dữ liệu không.
        # LIMIT 1 = 0.2ms; force=True mới cần rebuild đầy đủ.
        any_row = conn.execute("SELECT rowid FROM places_pending_fts LIMIT 1").fetchone()
        if force or not any_row:
            # 'delete-all' only works on contentless/external-content FTS5 tables —
            # this is a plain FTS5 table, so that special command always raised
            # "may only be used with a contentless or external content fts5 table"
            # and was silently swallowed by a try/except (pre-existing, not
            # introduced here) — every prior force-rebuild APPENDED a duplicate
            # copy instead of replacing rows. Found 2026-08-21 (row count doubled to
            # 236,599 after one force=True call while building T30). Plain DELETE
            # FROM is fully supported here.
            conn.execute("DELETE FROM places_pending_fts")
            # Source: COALESCE(namevi_map_places.name_vi, places_pending.name_vi) —
            # same pattern every other endpoint reading a place's name_vi uses.
            # Building straight from places_pending.name_vi alone (as before) meant
            # any name_vi living only in namevi_map_places never got indexed at all,
            # and any correction written to namevi_map_places (like T29's 14,982
            # retranslated rows) never showed up in search until a full rebuild.
            rows = conn.execute("""
                SELECT p.id, COALESCE(m.name_vi, p.name_vi) AS name_vi, p.name_zh
                FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE COALESCE(m.name_vi, p.name_vi) IS NOT NULL AND COALESCE(m.name_vi, p.name_vi) != ''
            """).fetchall()
            conn.executemany(
                "INSERT INTO places_pending_fts(id, name_vi, name_zh, name_vi_norm) VALUES (?, ?, ?, ?)",
                [(r['id'], r['name_vi'], r['name_zh'] or '', normalize_text(r['name_vi'])) for r in rows]
            )
            conn.commit()
            _FTS5_READY["places_pending_fts"] = True
            return True
        _FTS5_READY["places_pending_fts"] = True
        return False
    except Exception as e:
        return False
    finally:
        if own:
            conn.close()




# ─── HÁN-VIỆT CLEANUP ──────────────────────────────────────

_HV_CACHE = None



CUSTOM_HANVIET = {
    # Rare / difficult chars that are missing from hanviet_fallback
    "跋": "Bạt",
    "姞": "Cát",
    "邸": "Để",
    "磧": "Tích",
    "杲": "Cảo",
    "祐": "Hựu",
    "頤": "Di",
    "頊": "Húc",
    "頌": "Tụng",
    "頒": "Ban",
    "頓": "Đốn",
    "頗": "Phả",
    "頫": "Phủ",
    "頡": "Hiệt",
    "頣": "Thẩn",
    "頦": "Hài",
    "頲": "Đĩnh",
    "頳": "Sinh",
    "頴": "Dĩnh",
    "頵": "Quân",
    "頶": "Hốc",
    "頷": "Hàm",
    "頸": "Cảnh",
    "顆": "Khỏa",
    "餉": "Hưởng",
    "饋": "Quỹ",
    "饌": "Soạn",
    "饐": "Í",
    "饑": "Cơ",
    "饒": "Nhiêu",
    "饔": "Phung",
    "饕": "Thao",
    "饗": "Hưởng",
    "饘": "Chiên",
    "饜": "Yếm",
    "饝": "Ma",
    "驀": "Mạch",
    "驁": "Ngao",
    "驂": "Tham",
    "驃": "Phiếu",
    "驄": "Thông",
    "驊": "Hoa",
    "驍": "Kiêu",
    "驏": "Trản",
    "驐": "Đôn",
    "驑": "Lưu",
    "驒": "Đà",
    "驓": "Tằng",
    "驔": "Đàm",
    "驖": "Thiết",
    "驙": "Chiên",
    "驛": "Trạch",
    "驜": "Nghiệp",
    "驝": "Thác",
    "驞": "Tân",
    "驠": "Yến",
    "驡": "Long",
    "驢": "Lư",
    "驣": "Đằng",
    "驤": "Tương",
    "驥": "Ký",
    "驦": "Sương",
    "驧": "Cúc",
    "驨": "Hề",
    "驩": "Hoan",
    "驪": "Ly",
    "驫": "Phiêu",
    "驮": "Đà",
    "驯": "Tuần",
    "驰": "Trì",
    "驱": "Khu",
    "驳": "Bác",
    "驴": "Lư",
    "骡": "Loa",
    "骥": "Ký",
    "骧": "Tương",
    "龛": "Kham",
    "龠": "Dược",
    "龢": "Hòa",
    "龤": "Hài",
    # Additional chars from DILA toponyms
    "铠": "Khải",
    "铨": "Thuyên",
    "铉": "Huyễn",
    "铈": "Thị",
    "铊": "Tha",
    "铌": "Ni",
    "铍": "Phi",
    "铎": "Đạc",
    "铏": "Hình",
    "铐": "Cảo",
    "铑": "Lão",
    "铒": "Nhĩ",
    "铕": "Hữu",
    "铖": "Thành",
    "铗": "Kiệp",
    "铘": "Da",
    "铙": "Nao",
    "铚": "Trất",
    "铛": "Đang",
    "铜": "Đồng",
    "铝": "Lữ",
    "铟": "Nhân",
    "铠": "Khải",
    "铡": "Trát",
    "铢": "Thù",
    "铣": "Tiển",
    "铤": "Đĩnh",
    "铥": "Đâu",
    "铧": "Hoa",
    "铨": "Thuyên",
    "铩": "Sát",
    "铪": "Ha",
    "铫": "Diêu",
    "铬": "Các",
    "铭": "Minh",
    "铮": "Tránh",
    "铯": "Sắc",
    "铰": "Giảo",
    "铱": "Y",
    "铲": "Sản",
    "铳": "Xúng",
    "铴": "Thang",
    "铵": "An",
    "银": "Ngân",
    "铷": "Như",
    "铸": "Chú",
    "铹": "Lao",
    "铺": "Phố",
    "铻": "Ngô",
    "铼": "Lai",
    "铽": "Thác",
    "链": "Liên",
    "铿": "Khanh",
    "销": "Tiêu",
    "锁": "Tỏa",
    "锂": "Lý",
    "锃": "Tránh",
    "锄": "Sừ",
    "锅": "Oa",
    "锆": "Cáo",
    "锇": "Nga",
    "锉": "Tòa",
    "锊": "Lược",
    "锋": "Phong",
    "锌": "Tân",
    "锍": "Lưu",
    "锎": "Khai",
    "锏": "Giản",
    "锐": "Nhuệ",
    "锑": "Thế",
    "锒": "Lang",
    "锓": "Tẩm",
    "锔": "Cúc",
    "锕": "A",
    "锖": "Thương",
    "锗": "Giả",
    "锘": "Nặc",
    "错": "Thác",
    "锚": "Miêu",
    "锛": "Bôn",
    "锜": "Kỳ",
    "锝": "Đắc",
    "锞": "Khóa",
    "锟": "Côn",
    "锠": "Xương",
    "锡": "Tích",
    "锢": "Cố",
    "锣": "La",
    "锤": "Chùy",
    "锥": "Chùy",
    "锦": "Cẩm",
    "锧": "Chất",
    "锨": "Hân",
    "锩": "Quyển",
    "锪": "Hốt",
    "锫": "Bồi",
    "锬": "Đàm",
    "锭": "Đĩnh",
    "键": "Kiện",
    "锯": "Cứ",
    "锰": "Mãnh",
    "锱": "Tư",
    "锲": "Khiết",
    "锳": "Anh",
    "锴": "Khải",
    "锵": "Thương",
    "锶": "Tư",
    "锷": "Ngạc",
    "锸": "Tráp",
    "锹": "Thu",
    "锺": "Chung",
    "锻": "Đoán",
    "锼": "Sưu",
    "锽": "Hoàng",
    "锾": "Hoàn",
    "锿": "Ai",
    "镀": "Độ",
    "镁": "Mỹ",
    "镂": "Lũ",
    "镃": "Tư",
    "镄": "Phí",
    "镅": "My",
    "镆": "Mạc",
    "镇": "Trấn",
    "镈": "Bác",
    "镉": "Cách",
    "镊": "Nhiếp",
    "镋": "Thảng",
    "镌": "Thuyên",
    "镍": "Niết",
    "镎": "Nã",
    "镏": "Lưu",
    "镐": "Hạo",
    "镑": "Bảng",
    "镒": "Dật",
    "镓": "Gia",
    "镔": "Tân",
    "镕": "Dung",
    "镖": "Phiêu",
    "镗": "Đường",
    "镘": "Mạn",
    "镙": "La",
    "镚": "Bính",
    "镛": "Dung",
    "镜": "Kính",
    "镝": "Đích",
    "镞": "Tộc",
    "镟": "Tuyến",
    "镠": "Lưu",
    "镡": "Đàm",
    "镢": "Quật",
    "镣": "Liệu",
    "镤": "Phác",
    "镥": "Lỗ",
    "镦": "Đối",
    "镧": "Lan",
    "镨": "Phổ",
    "镩": "Thoán",
    "镪": "Cưỡng",
    "镫": "Đăng",
    "镬": "Hoạch",
    "镭": "Lôi",
    "镮": "Hoàn",
    "镯": "Trạc",
    "镰": "Liêm",
    "镱": "Ích",
    "镲": "Sáp",
    "镳": "Phiêu",
    "镴": "Lạp",
    "镵": "Sàm",
    "镶": "Tương",
    "镶": "Tương",
    "颋": "Đĩnh",
    "颍": "Dĩnh",
    "颎": "Cảnh",
    "颏": "Hài",
    "颐": "Di",
    "频": "Tần",
    "颔": "Hàm",
    "颈": "Cảnh",
    "颊": "Giáp",
    "颌": "Hợp",
    "颚": "Ngạc",
    "颛": "Chuyên",
    "颞": "Niếp",
    "颟": "Man",
    "颡": "Tảng",
    "颢": "Hạo",
    "颦": "Tần",
    "颧": "Quyền",
    "风": "Phong",
    "飏": "Dương",
    "飐": "Triển",
    "飑": "Tiêu",
    "飒": "Táp",
    "飓": "Cự",
    "飔": "Tư",
    "飕": "Sưu",
    "飖": "Diêu",
    "飗": "Lưu",
    "飘": "Phiêu",
    "飙": "Phiêu",
    "飚": "Phiêu",
    "飞": "Phi",
    "食": "Thực",
    "飧": "Tôn",
    "飨": "Hưởng",
    "飩": "Độn",
    "飪": "Nhẫm",
    "飫": "Ứ",
    "飬": "Dưỡng",
    "飭": "Sức",
    "飮": "Ẩm",
    "飯": "Phạn",
    "飰": "Phạn",
    "飱": "Tôn",
    "飲": "Ẩm",
    "飳": "Chú",
    "飴": "Di",
    "飵": "Trách",
    "飶": "Tất",
    "飷": "Giả",
    "飸": "Thao",
    "飹": "Cửu",
    "飺": "Từ",
    "飻": "Thiết",
    "飼": "Tự",
    "飽": "Bão",
    "飾": "Sức",
    "飿": "Đột",
    "餀": "Hại",
    "餁": "Nhậm",
    "餂": "Thiểm",
    "餃": "Giáo",
    "餄": "Hạt",
    "餅": "Bính",
    "餆": "Diêu",
    "餇": "Đồng",
    "餈": "Từ",
    "餉": "Hưởng",
    "養": "Dưỡng",
    "餌": "Nhĩ",
    "餎": "Lạc",
    "餏": "Ti",
    "餐": "Xan",
    "餑": "Bột",
    "餒": "Nỗi",
    "餓": "Ngạ",
    "餔": "Bố",
    "餕": "Tuấn",
    "餖": "Đậu",
    "餗": "Tốc",
    "餘": "Dư",
    "餙": "Sức",
    "餚": "Dao",
    "餛": "Hồn",
    "餜": "Quả",
    "餝": "Sức",
    "餞": "Tiễn",
    "餟": "Chuyết",
    "餠": "Bính",
    "餡": "Hãm",
    "餢": "Bộc",
    "餣": "Yếp",
    "餤": "Đàm",
    "餥": "Phỉ",
    "餧": "Nỗi",
    "館": "Quán",
    "餩": "Ác",
    "餪": "Noãn",
    "餫": "Vận",
    "餬": "Hồ",
    "餭": "Hoàng",
    "餮": "Thiết",
    "餯": "Huệ",
    "餰": "Chiên",
    "餲": "Ái",
    "餳": "Đường",
    "餴": "Phân",
    "餵": "Ủy",
    "餶": "Cốt",
    "餷": "Sát",
    "餸": "Tống",
    "餹": "Đường",
    "餺": "Bạc",
    "餻": "Cao",
    "餼": "Hí",
    "餽": "Quỹ",
    "餾": "Lựu",
    "餿": "Sưu",
    "饀": "Đào",
    "饁": "Diệp",
    "饂": "Uẩn",
    "饃": "Mô",
    "饄": "Đường",
    "饅": "Mạn",
    "饆": "Tất",
    "饇": "Ốc",
    "饈": "Tu",
    "饉": "Cận",
    "饊": "Tản",
    "饋": "Quỹ",
    "饌": "Soạn",
    "饍": "Thiện",
    "饎": "Xí",
    "饏": "Đạm",
    "饐": "Í",
    "饑": "Cơ",
    "饒": "Nhiêu",
    "饔": "Phung",
}



_MISSING_HANZI = {}



def _ensure_missing_hanzi_table():
    """Create missing_hanzi table if not exists."""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS missing_hanzi (
                char TEXT PRIMARY KEY,
                count INTEGER DEFAULT 1,
                last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()



def _log_missing_hanzi(char):
    """Upsert missing hanzi character into tracking table."""
    if char in _MISSING_HANZI:
        return  # Already logged this session
    _MISSING_HANZI[char] = True
    try:
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO missing_hanzi (char, count, last_seen_at)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(char) DO UPDATE SET
                    count = count + 1,
                    last_seen_at = CURRENT_TIMESTAMP
            """, (char,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass  # Non‑critical; silently ignore DB errors



def _ensure_custom_hanviet_override_table():
    """Create custom_hanviet_override table if not exists (T08 admin override)."""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_hanviet_override (
                char TEXT PRIMARY KEY,
                hanviet TEXT NOT NULL,
                added_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()



def _load_custom_hanviet_overrides():
    """Merge admin-added overrides (custom_hanviet_override table) into the
    in-memory CUSTOM_HANVIET dict so they take effect immediately, without
    editing the CUSTOM_HANVIET literal in source. Highest priority (checked
    first in _ensure_vietnamese), same as hardcoded CUSTOM_HANVIET entries."""
    _ensure_custom_hanviet_override_table()
    try:
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT char, hanviet FROM custom_hanviet_override").fetchall()
            for r in rows:
                CUSTOM_HANVIET[r['char']] = r['hanviet']
        finally:
            conn.close()
    except Exception:
        pass



def _init_hv_cache():
    global _HV_CACHE
    if _HV_CACHE is not None:
        return
    _HV_CACHE = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT ch, hv FROM hanviet_fallback").fetchall()
        for r in rows:
            _HV_CACHE[r[0]] = r[1]
        conn.close()
    except Exception:
        _HV_CACHE = {}
    _ensure_missing_hanzi_table()
    _load_custom_hanviet_overrides()



CUSTOM_HANVIET["奘"] = "Trạng"



def _ensure_vietnamese(text):
    """Replace CJK chars with Hán‑Việt readings; skip unknown chars.
    Priority: 1) CUSTOM_HANVIET 2) hanviet_fallback 3) skip (log as missing)."""
    if not text:
        return text or ''
    _init_hv_cache()
    result = []
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            hv = CUSTOM_HANVIET.get(c)
            if hv:
                result.append(hv)
                continue
            hv = _HV_CACHE.get(c) if _HV_CACHE else None
            if hv:
                result.append(hv)
            else:
                # Char unknown → skip it, log to missing_hanzi
                _log_missing_hanzi(c)
        else:
            result.append(c)
    cleaned = ''.join(result)
    # Remove any remaining Japanese/Chinese characters (safety net)
    cleaned = re.sub(r'[\u3040-\u30FF\u3400-\u4DBF]', '', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned



def _hanviet_charwise_translit(name_zh):
    """T372 — Phiên âm Hán-Việt charwise: ghép âm Hán-Việt của từng chữ Hán
    (CUSTOM_HANVIET ưu tiên, sau đó hanviet_fallback/_HV_CACHE), viết hoa chữ
    đầu mỗi âm, nối bằng khoảng trắng. Cùng thuật toán với
    /daoanh/api/admin/person/<id>/revalidate-hv (T172) — tái dùng ở đây để
    tránh viết lại khác hành vi.

    ĐÂY LÀ SUY LUẬN TỰ ĐỘNG, KHÔNG phải tên nguồn DILA (source_id=1) hay
    ZQLOCAL (source_id=5) đã xác thực — nơi gọi hàm này phải tự badge rõ
    "charwise"/suy luận tự động, không gán nhầm source DILA/ZQLOCAL.

    Trả về (charwise, unknown_chars): charwise='' nếu name_zh rỗng hoặc
    không có Hán tự nào; unknown_chars là list các chữ Hán không tra được âm.
    """
    name_zh = (name_zh or '').strip()
    if not name_zh:
        return '', []
    _init_hv_cache()
    parts = []
    unknown_chars = []
    for c in name_zh:
        if '一' <= c <= '鿿':
            hv = CUSTOM_HANVIET.get(c) or (_HV_CACHE.get(c) if _HV_CACHE else None)
            if hv:
                parts.append(hv[0].upper() + hv[1:] if len(hv) > 1 else hv.upper())
            else:
                parts.append(c)
                unknown_chars.append(c)
        elif c.strip():
            parts.append(c)
    charwise = ' '.join(parts)
    return charwise, unknown_chars



def _normalize_charwise_caps(charwise):
    """T372 — Viết hoa chữ đầu mỗi âm tiết của chuỗi charwise (phòng trường hợp
    person_hanviet_debug.han_viet_charwise có vài dòng bị lưu không nhất quán
    hoa/thường, ví dụ 'Huệ năng' → 'Huệ Năng'). Không đổi nghĩa/âm, chỉ chuẩn hóa
    hiển thị."""
    if not charwise:
        return charwise
    return ' '.join(
        (w[0].upper() + w[1:]) if w else w
        for w in charwise.split(' ')
    )



TAM_DICH_SUFFIX = ' (Tạm dịch)'



# ── T22.1 Approval Gates ──────────────────────────────────────────────────────
_T221_APPROVALS_FILE = os.path.join(BASE_DIR, 'data', 't22_1_approvals.json')



def _t221_load():
    try:
        with open(_T221_APPROVALS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}



def _t221_save(data):
    with open(_T221_APPROVALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────

# Known Chinese dynasty/kingdom names. Whether a name refers to a historical
# ruling dynasty is a structural fact, not a translation judgment call, so a
# curated exact-match list is used (kept intentionally narrow to avoid
# false-positive matches against unrelated place names that share a common
# single character). Only consulted when name_vi is already empty.
DYNASTY_NAMES = {
    '夏', '商', '周', '秦', '漢', '西漢', '東漢', '新',
    '魏', '蜀', '蜀漢', '吳', '東吳', '晉', '西晉', '東晉',
    '劉宋', '南齊', '梁', '陳',
    '北魏', '東魏', '西魏', '北齊', '北周',
    '隋', '唐',
    '後梁', '後唐', '後晉', '後漢', '後周',
    '吳越', '南唐', '閩', '荊南', '北漢',
    '遼', '西遼', '北宋', '南宋', '金', '西夏',
    '元', '明', '南明', '清', '清朝',
}



# Dynasty names cross-checked against Vietnamese Wikipedia on 2026-08-13
# (https://vi.wikipedia.org/wiki/Nhà_Liêu, https://vi.wikipedia.org/wiki/Nhà_Thanh)
# - returned as-is, WITHOUT the "(Tạm dịch)" tag, since these are confirmed
# against a real external source, not machine-guessed. Everything else in
# DYNASTY_NAMES still falls back to _translate_zh_term()'s own lexicon/Hán-Việt
# logic and keeps its tentative tag until someone verifies and adds it here.
WEB_VERIFIED_DYNASTY_VI = {
    '遼': 'Liêu',
    '清朝': 'Thanh',
    '清': 'Thanh',
}




def _translate_dynasty_name(name_zh, conn):
    """
    If name_zh is a known dynasty/kingdom name, return 'Nhà <ten>'.
    Returns None if name_zh isn't a recognized dynasty (caller should fall
    back to plain _translate_zh_term()).
    """
    if name_zh not in DYNASTY_NAMES:
        return None
    core = WEB_VERIFIED_DYNASTY_VI.get(name_zh) or _translate_zh_term(name_zh, conn)
    return f'Nhà {core}' if core else None




def _translate_zh_term(seg, conn):
    """
    Translate a single Chinese term/phrase to Vietnamese.
    Priority: 1) exact lexicon term match (confirmed dictionary translation,
    returned as-is, NO tentative marker). 2) _ensure_vietnamese() char-by-char
    Hán-Việt fallback (NOT a verified official translation - always suffixed
    with "(Tạm dịch)" so an admin knows to verify it manually later; the code
    must never present a guessed reading as if it were confirmed).
    Returns '' if seg is empty.
    """
    seg = (seg or '').strip()
    if not seg:
        return ''
    key = normalize_text(seg)
    row = conn.execute(
        "SELECT term FROM lexicon WHERE key_norm = ? AND LENGTH(term) < 60 ORDER BY priority ASC LIMIT 1",
        (key,)
    ).fetchone()
    if row and row['term'] and row['term'] != seg:
        return row['term']  # confirmed dictionary translation
    # Fallback: Hán-Việt reading, spaced between CJK syllables only — runs of
    # non-CJK text (Latin, Cyrillic, digits, punctuation) are left untouched
    # instead of being exploded into single spaced-out characters.
    # This is a guess, not a verified official name -> must be flagged.
    out = []
    prev_was_han = False
    has_han = False
    for c in seg:
        if '一' <= c <= '鿿':
            hv = _ensure_vietnamese(c)
            if hv:
                if out and prev_was_han:
                    out.append(' ')
                out.append(hv)
                has_han = True
            prev_was_han = True
        else:
            out.append(c)
            prev_was_han = False
    guess = ''.join(out).strip()
    if not guess:
        return seg  # totally unmappable -> leave raw rather than silently drop
    if has_han:
        guess = title_case_vi(guess)
    return guess + TAM_DICH_SUFFIX




def _translate_admin_text(text, conn=None):
    """
    Convert a Chinese admin-division string (e.g. '中國-廣西壯族自治區-來賓市-忻城縣'
    or with ';' between multiple regions) to Vietnamese for display, segment by
    segment via _translate_zh_term(). Never leaves raw CJK on the page; any
    non-dictionary-confirmed segment is marked "(Tạm dịch)".
    """
    if not text:
        return text or ''
    own_conn = conn is None
    if own_conn:
        conn = get_db_connection()
    try:
        parts = []
        for region in text.split(';'):
            sub_parts = [_translate_zh_term(p, conn) for p in region.split('-')]
            parts.append(' - '.join(p for p in sub_parts if p))
        return '; '.join(p for p in parts if p)
    finally:
        if own_conn:
            conn.close()




def title_case_vi(text):
    """Viết hoa chữ cái đầu mỗi từ cho chuỗi tiếng Việt, giữ nguyên dấu và khoảng trắng."""
    if not text or not isinstance(text, str):
        return text or ''
    return ' '.join(w.capitalize() for w in text.strip().split())



COUNTRY_MAP = {
    '阿富汗': 'Afghanistan',
    '中國': 'Trung Quốc',
    '中国': 'Trung Quốc',
    '印度': 'Ấn Độ',
    '巴基斯坦': 'Pakistan',
    '尼泊爾': 'Nepal',
    '尼泊尔': 'Nepal',
    '緬甸': 'Myanmar',
    '缅甸': 'Myanmar',
    '斯里蘭卡': 'Sri Lanka',
    '孟加拉': 'Bangladesh',
    '日本': 'Nhật Bản',
    '韓國': 'Hàn Quốc',
    '蒙古': 'Mông Cổ',
    '泰國': 'Thái Lan',
    '寮國': 'Lào',
    '柬埔寨': 'Campuchia',
    '印尼': 'Indonesia',
    '馬來西亞': 'Malaysia',
    '菲律賓': 'Philippines',
    '新加坡': 'Singapore',
    '西藏': 'Tây Tạng',
    '新疆': 'Tân Cương',
}



ADMIN_LEVEL_MAP = {
    '省': 'tỉnh', '市': 'thành phố', '縣': 'huyện',
    '县': 'huyện', '区': 'quận', '區': 'quận',
    '镇': 'trấn', '鎮': 'trấn', '乡': 'xã', '鄉': 'xã',
}



CHINESE_PLACE_NAMES = {
    # 34 tỉnh
    '雲南': 'Vân Nam', '河北': 'Hà Bắc', '山西': 'Sơn Tây',
    '山東': 'Sơn Đông', '河南': 'Hà Nam', '湖南': 'Hồ Nam',
    '廣東': 'Quảng Đông', '廣西': 'Quảng Tây', '四川': 'Tứ Xuyên',
    '福建': 'Phúc Kiến', '江蘇': 'Giang Tô', '浙江': 'Chiết Giang',
    '安徽': 'An Huy', '江西': 'Giang Tây', '湖北': 'Hồ Bắc',
    '貴州': 'Quý Châu', '陝西': 'Thiểm Tây', '甘肅': 'Cam Túc',
    '遼寧': 'Liêu Ninh', '吉林': 'Cát Lâm', '黑龍江': 'Hắc Long Giang',
    '海南': 'Hải Nam', '青海': 'Thanh Hải', '台灣': 'Đài Loan',
    '新疆': 'Tân Cương', '西藏': 'Tây Tạng', '內蒙古': 'Nội Mông Cổ',
    '寧夏': 'Ninh Hạ',
    # Trực hạt thị (municipalities)
    '北京': 'Bắc Kinh', '上海': 'Thượng Hải', '天津': 'Thiên Tân',
    '重慶': 'Trùng Khánh', '香港': 'Hồng Kông', '澳門': 'Ma Cao',
    # Thành phố + địa danh nổi
    '洛陽': 'Lạc Dương', '西安': 'Tây An', '成都': 'Thành Đô',
    '昆明': 'Côn Minh', '南京': 'Nam Kinh', '杭州': 'Hàng Châu',
    '武漢': 'Vũ Hán', '長沙': 'Trường Sa', '廣州': 'Quảng Châu',
    '大理': 'Đại Lý', '敦煌': 'Đôn Hoàng', '開封': 'Khai Phong',
    '曲靖': 'Khúc Tĩnh', '富源': 'Phú Nguyên', '昭通': 'Chiêu Thông',
    '太原': 'Thái Nguyên', '瀋陽': 'Thẩm Dương', '濟南': 'Tế Nam',
    '福州': 'Phúc Châu', '南昌': 'Nam Xương', '貴陽': 'Quý Dương',
    '蘭州': 'Lan Châu', '西寧': 'Tây Ninh',
    # Quận/huyện phổ biến
    '海淀': 'Hải Điện', '朝阳': 'Triều Dương', '浦东': 'Phố Đông',
    '天山': 'Thiên Sơn', '武侯': 'Vũ Hầu', '錦江': 'Cẩm Giang',
    # Khu tự trị — name_raw sau khi bỏ hậu tố 區
    '新疆維吾爾自治': 'Tân Cương', '西藏自治': 'Tây Tạng',
    '內蒙古自治': 'Nội Mông Cổ', '廣西壯族自治': 'Quảng Tây',
    '寧夏回族自治': 'Ninh Hạ', '延邊朝鮮族自治': 'Diên Biên',
    '恩施土家族苗族自治': 'Ân Thi', '黔東南苗族侗族自治': 'Kiềm Đông Nam',
    '黔南布依族苗族自治': 'Kiềm Nam', '黔西南布依族苗族自治': 'Kiềm Tây Nam',
    '湘西土家族苗族自治': 'Tương Tây', '伊犁哈薩克自治': 'Y Lê',
    '甘孜藏族自治': 'Cam Tư', '阿壩藏族羌族自治': 'A Bá',
    '涼山彝族自治': 'Lương Sơn', '德宏傣族景頗族自治': 'Đức Hoằng',
    '怒江傈僳族自治': 'Nộ Giang', '迪慶藏族自治': 'Địch Khánh',
    '大理白族自治': 'Đại Lý', '西雙版納傣族自治': 'Tây Song Bản Nạp',
    '文山壯族苗族自治': 'Văn Sơn', '紅河哈尼族彝族自治': 'Hồng Hà',
    '楚雄彝族自治': 'Sở Hùng', '保山自治': 'Bảo Sơn',
    # Thêm địa danh lịch sử Phật giáo
    '罽賓': 'Kế Tân', '健馱邏': 'Kiền Đà La', '鳥萇': 'Ô Trường',
    '鉢羅': 'Bát La', '迦濕彌羅': 'Ca Thấp Di La',
    # Khu tự trị cấp địa khu Tân Cương — name_raw sau khi bỏ hậu tố 州
    '伊犁哈薩克自治': 'Y Lê Kazakh', '博爾塔拉蒙古自治': 'Bác Nhĩ Tháp La Mông Cổ',
    '巴音郭楞蒙古自治': 'Ba Âm Quách Lăng Mông Cổ', '昌吉回族自治': 'Xương Cát Hồi',
    '克孜勒蘇柯爾克孜自治': 'Khắc Tư Lặc Tô', '塔城地區': 'Tháp Thành',
    # Tây Tạng
    '那曲地': 'Na Khúc', '阿里地': 'A Lý', '日喀則地': 'Nhật Khách Tắc',
    '山南地': 'Sơn Nam', '林芝地': 'Lâm Chi', '昌都地': 'Xương Đô',
    # Vân Nam
    '迪慶藏族自治': 'Địch Khánh', '怒江傈僳族自治': 'Nộ Giang',
    '德宏傣族景頗族自治': 'Đức Hoằng', '臨滄地': 'Lâm Thương',
    # Nội Mông
    '鄂爾多斯': 'Ngạc Nhĩ Đa Tư', '巴彥淖爾': 'Ba Ngạn Nạo Nhĩ',
    '烏蘭察布': 'Ô Lan Sát Bố', '錫林郭勒盟': 'Tích Lâm Quách Lặc',
    '興安': 'Hưng An', '呼倫貝爾': 'Hô Luân Bối Nhĩ',
}



MUNICIPALITIES = {'北京', '上海', '天津', '重慶', '香港', '澳門'}



# Hán-Việt character-by-character lookup table — fallback for place names not in CHINESE_PLACE_NAMES
HAN_VIET_CHAR = {
    # Directions & positions
    '東': 'Đông', '东': 'Đông', '西': 'Tây', '南': 'Nam', '北': 'Bắc',
    '中': 'Trung', '上': 'Thượng', '下': 'Hạ', '內': 'Nội', '内': 'Nội',
    '外': 'Ngoại', '左': 'Tả', '右': 'Hữu', '前': 'Tiền', '後': 'Hậu',
    # Water & terrain
    '河': 'Hà', '江': 'Giang', '湖': 'Hồ', '海': 'Hải', '洋': 'Dương',
    '川': 'Xuyên', '水': 'Thủy', '泉': 'Tuyền', '浦': 'Phố', '洲': 'Châu',
    '灘': 'Than', '渡': 'Độ', '池': 'Trì', '溪': 'Khê', '浜': 'Bằng',
    '洛': 'Lạc', '淮': 'Hoài', '漢': 'Hán', '汉': 'Hán', '滄': 'Thương',
    '沧': 'Thương', '漯': 'Lạp', '汾': 'Phần', '涇': 'Kinh', '渭': 'Vị',
    '瀘': 'Lô', '沂': 'Nghi', '沭': 'Thuật', '泗': 'Tứ', '沔': 'Miện',
    '沱': 'Đà', '岷': 'Mân', '嘉': 'Gia', '陵': 'Lăng', '烏': 'Ô', '乌': 'Ô',
    '濮': 'Bộc', '洹': 'Hoàn', '潁': 'Dĩnh', '穎': 'Dĩnh', '荊': 'Kinh',
    '荆': 'Kinh', '贛': 'Cám', '赣': 'Cám', '鄱': 'Bà', '洞': 'Động',
    '太': 'Thái', '涿': 'Trác', '濱': 'Tân', '滨': 'Tân', '滁': 'Trừ',
    '蕪': 'Vu', '芜': 'Vu', '蒲': 'Bồ', '淄': 'Tri', '沁': 'Tẩm',
    '沅': 'Nguyên', '澧': 'Lễ', '沅': 'Nguyên', '舒': 'Thư',
    # Mountains & terrain
    '山': 'Sơn', '嶺': 'Lĩnh', '岳': 'Nhạc', '峰': 'Phong', '嶺': 'Lĩnh',
    '原': 'Nguyên', '坡': 'Ba', '崖': 'Nhai', '谷': 'Cốc', '峽': 'Hiệp',
    '峡': 'Hiệp', '坪': 'Bình', '壁': 'Bích', '崗': 'Cương', '岗': 'Cương',
    '嵩': 'Tung', '嶽': 'Nhạc', '崆': 'Không', '峒': 'Động', '太': 'Thái',
    '岩': 'Nham',
    # Administrative units
    '省': 'Tỉnh', '州': 'Châu', '府': 'Phủ', '縣': 'Huyện', '县': 'Huyện',
    '鎮': 'Trấn', '镇': 'Trấn', '鄉': 'Hương', '乡': 'Hương', '村': 'Thôn',
    '城': 'Thành', '道': 'Đạo', '路': 'Lộ', '坊': 'Phường', '堡': 'Bảo',
    '屯': 'Đồn', '寨': 'Trại', '場': 'Trường', '场': 'Trường',
    '區': 'Khu', '区': 'Khu', '鋪': 'Phố', '鄰': 'Lân', '塘': 'Đường',
    '壩': 'Bá', '坝': 'Bá', '埔': 'Phố', '灣': 'Loan', '湾': 'Loan',
    '橋': 'Kiều', '桥': 'Kiều', '關': 'Quan', '关': 'Quan',
    '口': 'Khẩu', '門': 'Môn', '门': 'Môn', '埠': 'Phụ',
    # Common name chars
    '安': 'An', '寧': 'Ninh', '宁': 'Ninh', '定': 'Định', '平': 'Bình',
    '通': 'Thông', '順': 'Thuận', '顺': 'Thuận', '昌': 'Xương', '興': 'Hưng',
    '兴': 'Hưng', '盛': 'Thịnh', '武': 'Vũ', '文': 'Văn', '朝': 'Triều',
    '大': 'Đại', '小': 'Tiểu', '新': 'Tân', '古': 'Cổ', '老': 'Lão',
    '長': 'Trường', '长': 'Trường', '永': 'Vĩnh', '常': 'Thường',
    '廣': 'Quảng', '广': 'Quảng', '慶': 'Khánh', '庆': 'Khánh',
    '福': 'Phúc', '壽': 'Thọ', '寿': 'Thọ', '德': 'Đức', '泰': 'Thái',
    '光': 'Quang', '明': 'Minh', '靈': 'Linh', '灵': 'Linh', '清': 'Thanh',
    '高': 'Cao', '遠': 'Viễn', '远': 'Viễn', '仁': 'Nhân', '義': 'Nghĩa',
    '义': 'Nghĩa', '宜': 'Nghi', '信': 'Tín', '忠': 'Trung', '固': 'Cố',
    '崇': 'Sùng', '宣': 'Tuyên', '承': 'Thừa', '慎': 'Thận', '惠': 'Huệ',
    '嘉': 'Gia', '隆': 'Long', '祥': 'Tường', '瑞': 'Thụy', '吉': 'Cát',
    # Colours
    '黃': 'Hoàng', '黄': 'Hoàng', '紅': 'Hồng', '红': 'Hồng', '白': 'Bạch',
    '黑': 'Hắc', '青': 'Thanh', '綠': 'Lục', '绿': 'Lục', '金': 'Kim',
    '銀': 'Ngân', '银': 'Ngân',
    # Materials/nature
    '石': 'Thạch', '木': 'Mộc', '土': 'Thổ', '火': 'Hoả', '鐵': 'Thiết',
    '铁': 'Thiết', '銅': 'Đồng', '铜': 'Đồng', '玉': 'Ngọc', '珠': 'Châu',
    '松': 'Tùng', '柏': 'Bách', '梅': 'Mai', '柳': 'Liễu', '桂': 'Quế',
    '竹': 'Trúc', '蘭': 'Lan', '兰': 'Lan', '荷': 'Hà',
    # Animals
    '龍': 'Long', '龙': 'Long', '虎': 'Hổ', '鳳': 'Phụng', '凤': 'Phụng',
    '馬': 'Mã', '马': 'Mã', '鹿': 'Lộc', '鶴': 'Hạc', '鹤': 'Hạc',
    '燕': 'Yên', '雁': 'Nhạn', '鷹': 'Ưng',
    # Numbers
    '一': 'Nhất', '二': 'Nhị', '三': 'Tam', '四': 'Tứ', '五': 'Ngũ',
    '六': 'Lục', '七': 'Thất', '八': 'Bát', '九': 'Cửu', '十': 'Thập',
    '百': 'Bách', '千': 'Thiên', '萬': 'Vạn', '万': 'Vạn',
    # Province-level chars
    '雲': 'Vân', '云': 'Vân', '貴': 'Quý', '贵': 'Quý', '川': 'Xuyên',
    '蜀': 'Thục', '閩': 'Mân', '闽': 'Mân', '浙': 'Chiết', '徽': 'Huy',
    '蘇': 'Tô', '苏': 'Tô', '贛': 'Cám', '晉': 'Tấn', '晋': 'Tấn',
    '冀': 'Ký', '豫': 'Dự', '魯': 'Lỗ', '鲁': 'Lỗ', '鄂': 'Ngạc',
    '湘': 'Tương', '瓊': 'Quỳnh', '琼': 'Quỳnh', '遼': 'Liêu', '辽': 'Liêu',
    '寧': 'Ninh', '黔': 'Kiềm', '陝': 'Thiểm', '陕': 'Thiểm',
    '甘': 'Cam', '秦': 'Tần', '疆': 'Cương',
    # Major city chars
    '京': 'Kinh', '都': 'Đô', '陽': 'Dương', '阳': 'Dương', '漢': 'Hán',
    '津': 'Tân', '渝': 'Du', '漳': 'Chương', '汕': 'Sán', '廈': 'Hạ',
    '厦': 'Hạ', '莆': 'Bồ', '田': 'Điền', '蘇': 'Tô', '杭': 'Hàng',
    '鄭': 'Trịnh', '郑': 'Trịnh', '焦': 'Tiêu', '許': 'Hứa', '许': 'Hứa',
    '鶴': 'Hạc', '濟': 'Tế', '济': 'Tế', '聊': 'Liêu', '臨': 'Lâm',
    '临': 'Lâm', '萊': 'Lai', '菏': 'Hà', '威': 'Uy', '煙': 'Yên',
    '烟': 'Yên', '棗': 'Táo', '枣': 'Táo', '泰': 'Thái', '濰': 'Duy',
    '潍': 'Duy', '莒': 'Cử', '郯': 'Đàm', '沂': 'Nghi',
    '株': 'Chu', '婁': 'Lâu', '娄': 'Lâu', '衡': 'Hành', '邵': 'Thiệu',
    '懷': 'Hoài', '怀': 'Hoài', '邢': 'Hình', '衛': 'Vệ', '卫': 'Vệ',
    '涿': 'Trác', '唐': 'Đường', '皇': 'Hoàng', '島': 'Đảo', '岛': 'Đảo',
    '廊': 'Lang', '滄': 'Thương', '邯': 'Hàm', '鄲': 'Đan',
    '保': 'Bảo', '雄': 'Hùng', '深': 'Thâm', '珠': 'Châu', '湛': 'Trạm',
    '茂': 'Mậu', '名': 'Danh', '肇': 'Triệu', '揭': 'Yết', '潮': 'Triều',
    '梅': 'Mai', '浮': 'Phù', '韶': 'Thiều', '揚': 'Dương', '扬': 'Dương',
    '徐': 'Từ', '淮': 'Hoài', '連': 'Liên', '连': 'Liên', '鹽': 'Diêm',
    '盐': 'Diêm', '鎮': 'Trấn', '宿': 'Túc', '遷': 'Thiên', '迁': 'Thiên',
    '泰': 'Thái', '興': 'Hưng', '宜': 'Nghi', '紹': 'Thiệu', '绍': 'Thiệu',
    '金': 'Kim', '華': 'Hoa', '华': 'Hoa', '舟': 'Chu', '麗': 'Lệ', '丽': 'Lệ',
    '蘭': 'Lan', '溫': 'Ôn', '温': 'Ôn', '台': 'Đài', '臺': 'Đài',
    '合': 'Hợp', '肥': 'Phì', '蚌': 'Bạng', '馬': 'Mã', '鞍': 'Yên',
    '阜': 'Phụ', '六': 'Lục', '亳': 'Bạc', '宣': 'Tuyên', '枞': 'Tòng',
    '銅': 'Đồng', '池': 'Trì', '滁': 'Trừ', '運': 'Vận', '运': 'Vận',
    '遵': 'Tuân', '盤': 'Bàn', '盘': 'Bàn', '畢': 'Tất', '節': 'Tiết',
    '节': 'Tiết', '銅': 'Đồng', '仁': 'Nhân', '安': 'An',
    '普': 'Phổ', '洱': 'Nhĩ', '楚': 'Sở', '迪': 'Địch', '昭': 'Chiêu',
    '保': 'Bảo', '麗': 'Lệ', '版': 'Bản', '納': 'Nạp', '纳': 'Nạp',
    '勐': 'Mãnh', '雙': 'Song', '双': 'Song',
    # Xi'an area / Shaanxi
    '咸': 'Hàm', '漢': 'Hán', '渭': 'Vị', '澄': 'Trừng', '銅': 'Đồng',
    '延': 'Diên', '邊': 'Biên', '边': 'Biên', '榆': 'Du', '林': 'Lâm',
    '安': 'An', '康': 'Khang', '商': 'Thương', '洛': 'Lạc',
    # Gansu / Qinghai
    '蘭': 'Lan', '嘉': 'Gia', '峪': 'Dục', '酒': 'Tửu', '張': 'Trương',
    '张': 'Trương', '掖': 'Dịch', '武': 'Vũ', '金': 'Kim', '昌': 'Xương',
    '涼': 'Lương', '隴': 'Lũng', '陇': 'Lũng', '定': 'Định', '臨': 'Lâm',
    '慶': 'Khánh', '平': 'Bình', '白': 'Bạch', '吳': 'Ngô', '吴': 'Ngô',
    # Ningxia
    '石': 'Thạch', '嘴': 'Chủy', '固': 'Cố', '隆': 'Long', '靈': 'Linh',
    '中': 'Trung', '衛': 'Vệ',
    # Xinjiang
    '烏': 'Ô', '魯': 'Lỗ', '木': 'Mộc', '齊': 'Tề', '齐': 'Tề',
    '克': 'Khắc', '拉': 'Lạp', '瑪': 'Mã', '依': 'Y', '阿': 'A',
    '庫': 'Khố', '库': 'Khố', '爾': 'Nhĩ', '尔': 'Nhĩ', '勒': 'Lặc',
    '霍': 'Hoắc', '圖': 'Đồ', '图': 'Đồ', '吐': 'Thổ', '哈': 'Cáp',
    '番': 'Phiên', '喀': 'Khách', '什': 'Thập', '米': 'Mễ',
    # Tibet
    '拉': 'Lạp', '薩': 'Tát', '萨': 'Tát', '日': 'Nhật', '喀': 'Khách',
    '則': 'Tắc', '则': 'Tắc', '貢': 'Cống', '贡': 'Cống',
    # Inner Mongolia
    '包': 'Bao', '頭': 'Đầu', '头': 'Đầu', '赤': 'Xích', '呼': 'Hô',
    '和': 'Hòa', '浩': 'Hạo', '特': 'Đặc', '鄂': 'Ngạc', '多': 'Đa',
    '斯': 'Tư', '錫': 'Tích', '郭': 'Quách', '善': 'Thiện', '巴': 'Ba',
    '彥': 'Yến', '源': 'Nguyên',
    # Northeast
    '瀋': 'Thẩm', '沈': 'Thẩm', '撫': 'Phủ', '本': 'Bản', '錦': 'Cẩm',
    '丹': 'Đan', '鴨': 'Áp', '綠': 'Lục', '春': 'Xuân', '四': 'Tứ',
    '松': 'Tùng', '牡': 'Mẫu', '佳': 'Giai', '慶': 'Khánh', '伊': 'Y',
    '七': 'Thất', '雞': 'Kê', '崗': 'Cương', '綏': 'Tuy', '化': 'Hóa',
    # Historical/Buddhist geography
    '汴': 'Biện', '宋': 'Tống', '鄆': 'Vận', '曹': 'Tào', '濮': 'Bộc',
    '兗': 'Duyện', '齊': 'Tề', '青': 'Thanh', '萊': 'Lai', '登': 'Đăng',
    '萊': 'Lai', '密': 'Mật', '膠': 'Giao', '膳': 'Thiện', '泗': 'Tứ',
    '睢': 'Tuy', '沛': 'Bái', '彭': 'Bành', '城': 'Thành', '穎': 'Dĩnh',
    '蔡': 'Thái', '汝': 'Nhữ', '鄭': 'Trịnh', '鄢': 'Yên', '陳': 'Trần',
    '陈': 'Trần', '潁': 'Dĩnh', '汴': 'Biện', '魏': 'Ngụy', '韓': 'Hàn',
    '韩': 'Hàn', '趙': 'Triệu', '赵': 'Triệu', '燕': 'Yên', '楚': 'Sở',
    '吳': 'Ngô', '越': 'Việt', '秦': 'Tần', '漢': 'Hán', '唐': 'Đường',
    '宋': 'Tống', '元': 'Nguyên', '明': 'Minh', '清': 'Thanh',
    '隋': 'Tùy', '晉': 'Tấn', '魏': 'Ngụy', '蜀': 'Thục', '吳': 'Ngô',
    '齊': 'Tề', '樑': 'Lương', '梁': 'Lương', '陳': 'Trần',
    # More city chars
    '攀': 'Phan', '枝': 'Chi', '花': 'Hoa', '綿': 'Miên', '廣': 'Quảng',
    '自': 'Tự', '貢': 'Cống', '資': 'Tư', '陽': 'Dương', '瀘': 'Lô',
    '德': 'Đức', '宜': 'Nghi', '南': 'Nam', '充': 'Sung', '達': 'Đạt',
    '达': 'Đạt', '巴': 'Ba', '中': 'Trung', '廣': 'Quảng', '元': 'Nguyên',
    '甘': 'Cam', '孜': 'Tư', '涼': 'Lương', '山': 'Sơn', '樂': 'Lạc',
    '撫': 'Phủ', '州': 'Châu', '眉': 'Mi', '雅': 'Nhã', '安': 'An',
    '康': 'Khang', '阿': 'A', '壩': 'Bá', '涼': 'Lương',
    '北': 'Bắc', '海': 'Hải', '防': 'Phòng', '欽': 'Khâm', '钦': 'Khâm',
    '崇': 'Sùng', '左': 'Tả', '百': 'Bách', '色': 'Sắc', '賀': 'Hạ',
    '贺': 'Hạ', '賀': 'Hạ', '來': 'Lai', '来': 'Lai', '玉': 'Ngọc',
    '河': 'Hà', '貴': 'Quý', '港': 'Cảng', '欽': 'Khâm',
    '荊': 'Kinh', '宜': 'Nghi', '恩': 'Ân', '施': 'Thi', '隨': 'Tùy',
    '襄': 'Tương', '樊': 'Phàn', '黃': 'Hoàng', '孝': 'Hiếu', '感': 'Cảm',
    '咸': 'Hàm', '鄂': 'Ngạc', '黃': 'Hoàng', '石': 'Thạch',
    '萍': 'Bình', '贛': 'Cám', '吉': 'Cát', '撫': 'Phủ', '宜': 'Nghi',
    '景': 'Cảnh', '德': 'Đức', '九': 'Cửu', '江': 'Giang', '新': 'Tân',
    '余': 'Dư', '上': 'Thượng', '饒': 'Nhiêu', '鷹': 'Ưng', '潭': 'Đàm',
    # Long Hòa area
    '龍': 'Long', '岩': 'Nham', '南': 'Nam', '平': 'Bình', '三': 'Tam',
    '明': 'Minh', '泉': 'Tuyền', '州': 'Châu',
    # Misc
    '汴': 'Biện', '雒': 'Lạc', '邑': 'Ấp', '鄉': 'Hương', '堡': 'Bảo',
    '嶺': 'Lĩnh', '坡': 'Ba', '岡': 'Cương', '丘': 'Khâu', '陵': 'Lăng',
    '墟': 'Khư', '埠': 'Phụ', '渡': 'Độ', '峠': 'Thượng',
    '塔': 'Tháp', '寺': 'Tự', '廟': 'Miếu', '庵': 'Am', '觀': 'Quan',
    '宮': 'Cung', '院': 'Viện', '堂': 'Đường', '樓': 'Lâu', '閣': 'Các',
    '亭': 'Đình', '橋': 'Kiều', '洞': 'Động', '窟': 'Quật', '林': 'Lâm',
    '苑': 'Uyển',
    # Common characters in county/district names missing from initial set
    '忻': 'Hân', '朔': 'Sóc', '同': 'Đồng', '家': 'Gia', '莊': 'Trang',
    '治': 'Trị', '族': 'Tộc', '蒙': 'Mông', '旗': 'Kỳ', '盟': 'Minh',
    '滿': 'Mãn', '回': 'Hồi', '轄': 'Hạt', '無': 'Vô', '錫': 'Tích',
    '鼓': 'Cổ', '樓': 'Lâu', '玄': 'Huyền', '閶': 'Xướng', '雨': 'Vũ',
    '堯': 'Nghiêu', '熟': 'Thục', '棲': 'Thê', '霞': 'Hà', '年': 'Niên',
    '易': 'Dịch', '代': 'Đại', '蔚': 'Uất', '汾': 'Phần', '運': 'Vận',
    '城': 'Thành', '垣': 'Viên', '曲': 'Khúc', '浩': 'Hạo', '繁': 'Phồn',
    '峙': 'Trĩ', '偏': 'Thiên', '嵐': 'Lam', '縣': 'Huyện', '鄲': 'Đan',
    '邯': 'Hàm', '肥': 'Phì', '鄉': 'Hương', '鹿': 'Lộc', '皇': 'Hoàng',
    '葫': 'Hồ', '蘆': 'Lô', '倫': 'Luân', '察': 'Sát', '承': 'Thừa',
    '德': 'Đức', '遷': 'Thiên', '棗': 'Táo', '滕': 'Đằng', '藏': 'Tạng',
    '彝': 'Di', '壯': 'Tráng', '苗': 'Miêu', '侗': 'Đồng', '布': 'Bố',
    '依': 'Y', '黎': 'Lê', '畲': 'Xa', '傣': 'Đái',
    '坊': 'Phường', '項': 'Hạng', '陂': 'Bi', '睢': 'Tuy', '扶': 'Phù',
    '沔': 'Miện', '荊': 'Kinh', '孝': 'Hiếu', '感': 'Cảm', '咸': 'Hàm',
    '仙': 'Tiên', '桃': 'Đào', '邵': 'Thiệu', '株': 'Chu', '婁': 'Lâu',
    '冷': 'Lãnh', '益': 'Ích', '岳': 'Nhạc', '婁': 'Lâu', '耒': 'Lỗi',
    '資': 'Tư', '嘉': 'Gia', '攀': 'Phan', '枝': 'Chi', '綿': 'Miên',
    '充': 'Sung', '達': 'Đạt', '巴': 'Ba', '廣': 'Quảng', '眉': 'Mi',
    '雅': 'Nhã', '康': 'Khang', '壩': 'Bá', '阿': 'A',
    '嶺': 'Lĩnh', '鳳': 'Phụng', '慶': 'Khánh', '隴': 'Lũng', '秦': 'Tần',
    '渭': 'Vị', '漢': 'Hán', '商': 'Thương', '韓': 'Hàn',
    '撫': 'Phủ', '錦': 'Cẩm', '牡': 'Mẫu', '佳': 'Giai', '綏': 'Tuy',
    '伊': 'Y', '齊': 'Tề', '克': 'Khắc', '瑪': 'Mã', '庫': 'Khố',
    '格': 'Cách', '勒': 'Lặc', '霍': 'Hoắc', '圖': 'Đồ', '吐': 'Thổ',
    '喀': 'Khách', '什': 'Thập', '薩': 'Tát', '拉': 'Lạp', '則': 'Tắc',
    '貢': 'Cống', '日': 'Nhật', '包': 'Bao', '赤': 'Xích', '善': 'Thiện',
    '彥': 'Yến', '昂': 'Ngang', '扎': 'Trát', '那': 'Na', '曲': 'Khúc',
    '江': 'Giang', '達': 'Đạt', '孜': 'Tư',
    # High-frequency chars missing from above passes
    '市': 'Thị', '天': 'Thiên', '地': 'Địa', '維': 'Duy', '吾': 'Ngô',
    '賓': 'Tân', '理': 'Lý', '豐': 'Phong', '丰': 'Phong', '澤': 'Trạch',
    '泽': 'Trạch', '波': 'Ba', '投': 'Đầu', '羅': 'La', '罗': 'La',
    '尚': 'Thượng', '寬': 'Khoan', '寬': 'Khoan', '廬': 'Lư', '庐': 'Lư',
    '樟': 'Chương', '淳': 'Thuần', '弋': 'Dặc', '婺': 'Mụ', '衢': 'Cù',
    '舟': 'Chu', '麗': 'Lệ', '皖': 'Hoán', '贛': 'Cám', '閩': 'Mân',
    '瓊': 'Quỳnh', '桂': 'Quế', '粵': 'Việt', '粤': 'Việt', '滇': 'Điền',
    '黔': 'Kiềm', '巴': 'Ba', '蜀': 'Thục', '洮': 'Đào', '岷': 'Mân',
    '鹽': 'Diêm', '淵': 'Uyên', '朗': 'Lãng', '孟': 'Mạnh', '嘉': 'Gia',
    '罽': 'Kế', '健': 'Kiện', '馱': 'Đà', '陀': 'Đà', '羅': 'La',
    '那': 'Na', '迦': 'Ca', '提': 'Đề', '耶': 'Da', '舍': 'Xá',
    '羅': 'La', '衛': 'Vệ', '摩': 'Ma', '竭': 'Kiệt', '伽': 'Già',
    '毘': 'Tỳ', '耶': 'Da', '離': 'Ly', '婆': 'Bà', '娑': 'Ta',
    '夷': 'Di', '敖': 'Ngao', '黔': 'Kiềm',
    # Third pass — chars still missing after coverage tests
    '餘': 'Dư', '余': 'Dư', '寶': 'Bảo', '宝': 'Bảo', '峨': 'Nga',
    '店': 'Điếm', '羌': 'Khương', '屏': 'Bình', '行': 'Hành',
    '政': 'Chính', '國': 'Quốc', '国': 'Quốc', '蓮': 'Liên', '莲': 'Liên',
    '犁': 'Ly', '薩': 'Tát', '哈': 'Cáp', '薩': 'Tát',
    '尼': 'Ni', '普': 'Phổ', '洱': 'Nhĩ', '楚': 'Sở', '熊': 'Hùng',
    '湄': 'Mi', '潭': 'Đàm', '鵝': 'Nga', '楓': 'Phong', '舫': 'Phảng',
    '晴': 'Tình', '崩': 'Băng', '雷': 'Lôi', '電': 'Điện', '電': 'Điện',
    '夾': 'Giáp', '夹': 'Giáp', '貞': 'Trinh', '贞': 'Trinh',
    '叢': 'Tùng', '丛': 'Tùng', '牙': 'Nha', '克': 'Khắc',
    '欒': 'Loan', '栾': 'Loan', '清': 'Thanh', '水': 'Thủy',
    '瓦': 'Ngõa', '灰': 'Hôi', '磁': 'Từ', '邱': 'Khâu',
    '雙': 'Song', '橋': 'Kiều', '湘': 'Tương', '潼': 'Đồng',
    '獻': 'Hiến', '献': 'Hiến', '涼': 'Lương', '梁': 'Lương',
    '紫': 'Tử', '金': 'Kim', '銀': 'Ngân', '銅': 'Đồng',
    '蔗': 'Giá', '糖': 'Đường', '珠': 'Châu', '鑽': 'Toàn',
    '劍': 'Kiếm', '剑': 'Kiếm', '閣': 'Các', '廬': 'Lư',
    '灘': 'Than', '納': 'Nạp', '溝': 'Câu', '沟': 'Câu',
    '疏': 'Sơ', '勒': 'Lặc', '塔': 'Tháp', '什': 'Thập',
    '米': 'Mễ', '格': 'Cách', '爾': 'Nhĩ', '班': 'Ban',
    '瑪': 'Mã', '曲': 'Khúc', '措': 'Thố', '隆': 'Long',
    '嘎': 'Cát', '龜': 'Quy', '茲': 'Tư', '且': 'Thư',
    '末': 'Mạt', '若': 'Nhược', '羌': 'Khương', '鄯': 'Thiện',
    '焉': 'Yên', '耆': 'Kỳ', '疏': 'Sơ', '附': 'Phụ',
    '輪': 'Luân', '台': 'Đài', '盧': 'Lô', '布': 'Bố',
    # Fourth pass — chars from sampling remaining bad outputs
    '肅': 'Túc', '潯': 'Tầm', '渾': 'Hồn', '房': 'Phòng', '柔': 'Nhu',
    '成': 'Thành', '辰': 'Thần', '坻': 'Đê', '靜': 'Tĩnh', '薊': 'Kế',
    '井': 'Tỉnh', '陘': 'Hình', '礦': 'Khoáng', '裕': 'Dụ', '正': 'Chính',
    '園': 'Viên', '周': 'Chu', '建': 'Kiến', '彰': 'Chương', '博': 'Bác',
    '里': 'Lý', '直': 'Trực', '級': 'Cấp', '劃': 'Hoạch', '全': 'Toàn',
    '潮': 'Triều', '陽': 'Dương', '華': 'Hoa', '陰': 'Âm',
    '灤': 'Loan', '秦': 'Tần', '皇': 'Hoàng', '邯': 'Hàm', '鄲': 'Đan',
    '衡': 'Hành', '水': 'Thủy', '廊': 'Lang', '坊': 'Phường',
    '邢': 'Hình', '臺': 'Đài', '承': 'Thừa', '德': 'Đức',
    '滄': 'Thương', '張': 'Trương', '家': 'Gia', '口': 'Khẩu',
    '唐': 'Đường', '山': 'Sơn', '秦': 'Tần', '皇': 'Hoàng', '島': 'Đảo',
    '潞': 'Lộ', '晉': 'Tấn', '城': 'Thành', '運': 'Vận', '吕': 'Lữ',
    '梁': 'Lương', '繁': 'Phồn', '峙': 'Trĩ', '偏': 'Thiên', '嵐': 'Lam',
    '汀': 'Đinh', '漳': 'Chương', '龍': 'Long', '岩': 'Nham', '泉': 'Tuyền',
    '莆': 'Bồ', '廈': 'Hạ', '寧': 'Ninh', '三': 'Tam',
    '赣': 'Cám', '景': 'Cảnh', '鷹': 'Ưng', '潭': 'Đàm', '萍': 'Bình',
    '萍': 'Bình', '赤': 'Xích', '新': 'Tân', '鄉': 'Hương',
    '鑲': 'Tương', '黃': 'Hoàng', '甲': 'Giáp', '盤': 'Bàn',
    '撫': 'Phủ', '順': 'Thuận', '開': 'Khai', '鐵': 'Thiết',
    '葫': 'Hồ', '蘆': 'Lô', '錦': 'Cẩm', '州': 'Châu',
    '吉': 'Cát', '四': 'Tứ', '松': 'Tùng', '原': 'Nguyên',
    '鴨': 'Áp', '綠': 'Lục', '延': 'Diên', '邊': 'Biên',
    '圖': 'Đồ', '們': 'Môn', '牡': 'Mẫu', '丹': 'Đan',
    '伊': 'Y', '七': 'Thất', '雞': 'Kê', '嫩': 'Nộn',
    '哈': 'Cáp', '濱': 'Tân', '齊': 'Tề', '齐': 'Tề',
    '大': 'Đại', '慶': 'Khánh', '雙': 'Song', '鴨': 'Áp',
    '鶴': 'Hạc', '崗': 'Cương', '綏': 'Tuy', '化': 'Hóa',
    '武': 'Vũ', '漢': 'Hán', '黃': 'Hoàng', '石': 'Thạch',
    '恩': 'Ân', '施': 'Thi', '隨': 'Tùy', '襄': 'Tương',
    '樊': 'Phàn', '孝': 'Hiếu', '感': 'Cảm', '荊': 'Kinh',
    '宜': 'Nghi', '潛': 'Tiềm', '江': 'Giang', '天': 'Thiên',
    '門': 'Môn', '鄂': 'Ngạc', '洲': 'Châu', '仙': 'Tiên',
    '岳': 'Nhạc', '株': 'Chu', '湘': 'Tương', '邵': 'Thiệu',
    '冷': 'Lãnh', '益': 'Ích', '婁': 'Lâu', '耒': 'Lỗi',
    '韶': 'Thiều', '河': 'Hà', '源': 'Nguyên',
    '梅': 'Mai', '汕': 'Sán', '揭': 'Yết', '潮': 'Triều',
    '揚': 'Dương', '鎮': 'Trấn', '徐': 'Từ', '連': 'Liên',
    '鹽': 'Diêm', '宿': 'Túc', '遷': 'Thiên', '淮': 'Hoài',
    '無': 'Vô', '錫': 'Tích', '常': 'Thường', '蘇': 'Tô',
    '浙': 'Chiết', '杭': 'Hàng', '餘': 'Dư', '紹': 'Thiệu',
    '金': 'Kim', '華': 'Hoa', '衢': 'Cù', '舟': 'Chu',
    '溫': 'Ôn', '嘉': 'Gia', '湖': 'Hồ', '台': 'Đài',
    '麗': 'Lệ',
    # Fifth pass — extended coverage
    '呂': 'Lữ', '堰': 'Yển', '巢': 'Sào', '駐': 'Trú', '栗': 'Lật',
    '民': 'Dân', '夏': 'Hạ', '洪': 'Hồng', '秀': 'Tú', '營': 'Doanh',
    '富': 'Phú', '靖': 'Tĩnh', '桐': 'Đồng', '郴': 'Thần', '頂': 'Đỉnh',
    '鄖': 'Vân', '隨': 'Tùy', '神': 'Thần', '農': 'Nông', '架': 'Giá',
    '丹': 'Đan', '江': 'Giang', '陵': 'Lăng', '荊': 'Kinh', '門': 'Môn',
    '潛': 'Tiềm', '應': 'Ứng', '城': 'Thành', '漢': 'Hán', '川': 'Xuyên',
    '嶽': 'Nhạc', '陽': 'Dương', '常': 'Thường', '德': 'Đức', '懷': 'Hoài',
    '化': 'Hóa', '湘': 'Tương', '潭': 'Đàm', '株': 'Chu', '洲': 'Châu',
    '永': 'Vĩnh', '州': 'Châu', '衡': 'Hành', '郴': 'Thần', '婁': 'Lâu',
    '底': 'Để', '邵': 'Thiệu', '冷': 'Lãnh', '水': 'Thủy', '益': 'Ích',
    '汕': 'Sán', '揭': 'Yết', '茂': 'Mậu', '名': 'Danh', '肇': 'Triệu',
    '清': 'Thanh', '遠': 'Viễn', '雲': 'Vân', '浮': 'Phù', '梅': 'Mai',
    '惠': 'Huệ', '河': 'Hà', '源': 'Nguyên', '東': 'Đông', '莞': 'Quan',
    '中': 'Trung', '山': 'Sơn', '江': 'Giang', '門': 'Môn', '珠': 'Châu',
    '沙': 'Sa', '頭': 'Đầu', '角': 'Giác', '坪': 'Bình',
    '成': 'Thành', '都': 'Đô', '攀': 'Phan', '枝': 'Chi', '花': 'Hoa',
    '瀘': 'Lô', '德': 'Đức', '陽': 'Dương', '綿': 'Miên', '樂': 'Lạc',
    '遂': 'Toại', '寧': 'Ninh', '廣': 'Quảng', '元': 'Nguyên', '內': 'Nội',
    '雅': 'Nhã', '巴': 'Ba', '達': 'Đạt', '眉': 'Mi', '宜': 'Nghi',
    '賓': 'Tân', '甘': 'Cam', '孜': 'Tư', '阿': 'A', '壩': 'Bá',
    '涼': 'Lương', '崇': 'Sùng', '自': 'Tự', '貢': 'Cống', '資': 'Tư',
    '南': 'Nam', '充': 'Sung', '廣': 'Quảng', '安': 'An', '羅': 'La',
    '遵': 'Tuân', '義': 'Nghĩa', '六': 'Lục', '盤': 'Bàn', '水': 'Thủy',
    '安': 'An', '順': 'Thuận', '黔': 'Kiềm', '南': 'Nam', '東': 'Đông',
    '畢': 'Tất', '節': 'Tiết', '鐵': 'Thiết', '仁': 'Nhân',
    '貴': 'Quý', '陽': 'Dương', '銅': 'Đồng', '仁': 'Nhân',
    '昆': 'Côn', '明': 'Minh', '曲': 'Khúc', '靖': 'Tĩnh', '玉': 'Ngọc',
    '溪': 'Khê', '保': 'Bảo', '山': 'Sơn', '臨': 'Lâm', '滄': 'Thương',
    '普': 'Phổ', '洱': 'Nhĩ', '西': 'Tây', '版': 'Bản', '納': 'Nạp',
    '文': 'Văn', '楚': 'Sở', '雄': 'Hùng', '昭': 'Chiêu', '通': 'Thông',
    '麗': 'Lệ', '江': 'Giang', '迪': 'Địch', '慶': 'Khánh', '怒': 'Nộ',
    '德': 'Đức', '宏': 'Hoằng', '紅': 'Hồng', '錫': 'Tích',
    # Misc chars still missing
    '蘭': 'Lan', '滄': 'Thương', '瑞': 'Thụy', '吳': 'Ngô',
    '漢': 'Hán', '商': 'Thương', '洛': 'Lạc', '渭': 'Vị',
    '韓': 'Hàn', '延': 'Diên', '榆': 'Du', '林': 'Lâm',
    '康': 'Khang', '白': 'Bạch', '銀': 'Ngân', '蘇': 'Tô',
    '金': 'Kim', '昌': 'Xương', '張': 'Trương', '掖': 'Dịch',
    '酒': 'Tửu', '嘉': 'Gia', '峪': 'Dục', '武': 'Vũ',
    '威': 'Uy', '涼': 'Lương', '隴': 'Lũng', '定': 'Định',
    '隆': 'Long', '固': 'Cố', '嘴': 'Chủy', '石': 'Thạch',
    '中': 'Trung', '衛': 'Vệ', '木': 'Mộc', '齊': 'Tề',
    # Sixth pass
    '子': 'Tử', '樹': 'Thụ', '作': 'Tác', '梧': 'Ngô', '利': 'Lợi',
    '麻': 'Ma', '會': 'Hội', '音': 'Âm', '瑤': 'Dao', '基': 'Cơ',
    '封': 'Phong', '楞': 'Lăng', '荔': 'Lệ', '奉': 'Phụng', '當': 'Đương',
    '贊': 'Tán', '皋': 'Cao', '蘭': 'Lan', '涉': 'Thiệp', '冀': 'Ký',
    '行': 'Hành', '唐': 'Đường', '廬': 'Lư', '霍': 'Hoắc', '孟': 'Mạnh',
    '州': 'Châu', '沙': 'Sa', '洋': 'Dương', '錢': 'Tiền', '塘': 'Đường',
    '寶': 'Bảo', '山': 'Sơn', '崇': 'Sùng', '明': 'Minh',
    '廔': 'Lâu', '浦': 'Phố', '奉': 'Phụng', '賢': 'Hiền', '閔': 'Mẫn',
    '嘉': 'Gia', '定': 'Định', '青': 'Thanh', '浦': 'Phố',
    '松': 'Tùng', '江': 'Giang', '金': 'Kim', '山': 'Sơn',
    '沛': 'Bái', '豐': 'Phong', '彭': 'Bành', '徐': 'Từ', '邳': 'Phi',
    '灌': 'Quán', '沭': 'Thuật', '漣': 'Liên', '阜': 'Phụ',
    '鎮': 'Trấn', '揚': 'Dương', '高': 'Cao', '郵': 'Bưu',
    '鹽': 'Diêm', '城': 'Thành', '蘇': 'Tô', '州': 'Châu',
    '滁': 'Trừ', '亳': 'Bạc', '宿': 'Túc', '蚌': 'Bạng',
    '淮': 'Hoài', '南': 'Nam', '北': 'Bắc',
    '池': 'Trì', '宣': 'Tuyên', '城': 'Thành', '黃': 'Hoàng',
    '合': 'Hợp', '肥': 'Phì', '鞍': 'Yên',
    '景': 'Cảnh', '德': 'Đức', '鎮': 'Trấn', '九': 'Cửu',
    '萍': 'Bình', '鷹': 'Ưng', '潭': 'Đàm', '新': 'Tân',
    '余': 'Dư', '上': 'Thượng', '饒': 'Nhiêu',
    '贛': 'Cám', '撫': 'Phủ', '吉': 'Cát', '宜': 'Nghi', '春': 'Xuân',
    '南': 'Nam', '昌': 'Xương', '萍': 'Bình',
    '莆': 'Bồ', '田': 'Điền', '漳': 'Chương', '泉': 'Tuyền',
    '廈': 'Hạ', '寧': 'Ninh', '德': 'Đức', '三': 'Tam',
    '龍': 'Long', '岩': 'Nham',
    '海': 'Hải', '口': 'Khẩu', '三': 'Tam', '亞': 'Á',
    '儋': 'Đam', '瓊': 'Quỳnh', '海': 'Hải', '萬': 'Vạn', '寧': 'Ninh',
    '文': 'Văn', '昌': 'Xương', '瓊': 'Quỳnh', '中': 'Trung',
    '樂': 'Lạc', '東': 'Đông', '方': 'Phương', '澄': 'Trừng',
    '邁': 'Mại', '臨': 'Lâm', '高': 'Cao', '白': 'Bạch',
    '沙': 'Sa', '定': 'Định', '安': 'An', '保': 'Bảo',
    '屯': 'Đồn', '昌': 'Xương', '江': 'Giang',
    '洋': 'Dương', '陵': 'Lăng', '水': 'Thủy', '務': 'Vụ',
    '崖': 'Nhai', '州': 'Châu', '港': 'Cảng',
    '庫': 'Khố', '爾': 'Nhĩ', '勒': 'Lặc', '蘇': 'Tô', '阿': 'A',
    '克': 'Khắc', '拉': 'Lạp', '瑪': 'Mã', '什': 'Thập',
    '喀': 'Khách', '格': 'Cách', '霍': 'Hoắc', '圖': 'Đồ',
    '吐': 'Thổ', '哈': 'Cáp', '番': 'Phiên', '米': 'Mễ',
    '奎': 'Khuê', '屯': 'Đồn', '和': 'Hòa', '田': 'Điền',
    '巴': 'Ba', '音': 'Âm', '郭': 'Quách', '楞': 'Lăng',
    '博': 'Bác', '湖': 'Hồ', '伊': 'Y', '寧': 'Ninh',
    '昌': 'Xương', '吉': 'Cát', '塔': 'Tháp', '城': 'Thành',
    '烏': 'Ô', '蘇': 'Tô', '特': 'Đặc',
    # Final batch — comprehensive coverage for remaining chars
    '柯': 'Kha', '倉': 'Thương', '陸': 'Lục', '碑': 'Bi', '榮': 'Vinh',
    '環': 'Hoàn', '章': 'Chương', '容': 'Dung', '士': 'Sĩ', '公': 'Công',
    '彭': 'Bành', '慈': 'Từ', '郎': 'Lang', '揚': 'Dương', '尤': 'Vưu',
    '泰': 'Thái', '門': 'Môn', '莆': 'Bồ', '崖': 'Nhai', '儋': 'Đam',
    '亞': 'Á', '洋': 'Dương', '方': 'Phương', '樂': 'Lạc', '東': 'Đông',
    '崎': 'Kỳ', '灣': 'Loan', '坂': 'Phản', '名': 'Danh',
    '郎': 'Lang', '奎': 'Khuê', '廓': 'Khoách', '瓦': 'Ngõa',
    '番': 'Phiên', '禺': 'Ngu', '增': 'Tăng', '城': 'Thành',
    '順': 'Thuận', '佛': 'Phật', '山': 'Sơn', '江': 'Giang',
    '門': 'Môn', '中': 'Trung', '歡': 'Hoan', '樂': 'Lạc',
    '貝': 'Bối', '類': 'Loại', '德': 'Đức', '今': 'Kim',
    '古': 'Cổ', '典': 'Điển', '術': 'Thuật', '數': 'Số',
    '位': 'Vị', '分': 'Phân', '區': 'Khu', '劃': 'Hoạch',
    '組': 'Tổ', '群': 'Quần', '族': 'Tộc', '系': 'Hệ',
    '科': 'Khoa', '類': 'Loại', '目': 'Mục', '錄': 'Lục',
    '表': 'Biểu', '圖': 'Đồ', '志': 'Chí', '史': 'Sử',
    '書': 'Thư', '記': 'Ký', '傳': 'Truyện', '論': 'Luận',
    '議': 'Nghị', '奏': 'Tấu', '折': 'Chiết', '疏': 'Sơ',
    '贊': 'Tán', '詞': 'Từ', '詩': 'Thi', '賦': 'Phú',
    '銘': 'Minh', '碑': 'Bi', '帖': 'Thiếp', '序': 'Tự',
    '跋': 'Bạt', '箋': 'Tiên', '注': 'Chú', '疏': 'Sớ',
    '解': 'Giải', '釋': 'Thích', '音': 'Âm', '義': 'Nghĩa',
    '文': 'Văn', '字': 'Tự', '言': 'Ngôn', '語': 'Ngữ',
    '章': 'Chương', '句': 'Cú', '段': 'Đoạn', '節': 'Tiết',
    '卷': 'Quyển', '冊': 'Sách', '本': 'Bản', '版': 'Bản',
    '篇': 'Thiên', '部': 'Bộ', '門': 'Môn', '類': 'Loại',
    '宗': 'Tông', '派': 'Phái', '教': 'Giáo', '法': 'Pháp',
    '禪': 'Thiền', '律': 'Luật', '淨': 'Tịnh', '密': 'Mật',
    '顯': 'Hiển', '密': 'Mật', '念': 'Niệm', '觀': 'Quán',
    '修': 'Tu', '證': 'Chứng', '悟': 'Ngộ', '覺': 'Giác',
    '道': 'Đạo', '果': 'Quả', '行': 'Hành', '願': 'Nguyện',
    # Pass 7 — remaining 587 missing chars from coverage scan
    # Directions/positions (supplemental)
    '翼': 'Dực', '尾': 'Vĩ', '首': 'Thủ', '橫': 'Hoành', '幹': 'Cán',
    '裏': 'Lý', '裡': 'Lý', '至': 'Chí', '始': 'Thủy', '居': 'Cư',
    '步': 'Bộ', '游': 'Du', '遊': 'Du', '流': 'Lưu', '沿': 'Duyên',
    '從': 'Tòng', '各': 'Các', '于': 'Vu', '於': 'Vu', '為': 'Vi',
    '工': 'Công', '功': 'Công', '勝': 'Thắng', '強': 'Cường', '勤': 'Cần',
    '勉': 'Miễn', '助': 'Trợ', '互': 'Hỗ', '共': 'Cộng', '集': 'Tập',
    '積': 'Tích', '結': 'Kết', '進': 'Tiến', '歸': 'Quy', '復': 'Phục',
    '留': 'Lưu', '息': 'Tức', '止': 'Chỉ', '至': 'Chí', '次': 'Thứ',
    '始': 'Thủy', '極': 'Cực', '列': 'Liệt', '聯': 'Liên', '匯': 'Hối',
    '循': 'Tuần', '歷': 'Lịch', '流': 'Lưu', '端': 'Đoan', '如': 'Như',
    # Nature & terrain (supplemental)
    '野': 'Dã', '草': 'Thảo', '茅': 'Mao', '桑': 'Tang', '芝': 'Chi',
    '蓬': 'Bồng', '蒼': 'Thương', '藍': 'Lam', '翠': 'Thúy', '彩': 'Thái',
    '香': 'Hương', '芳': 'Phương', '芬': 'Phân', '梨': 'Lê', '杏': 'Hạnh',
    '椒': 'Tiêu', '麥': 'Mạch', '禾': 'Hòa', '稻': 'Đạo', '茶': 'Trà',
    '棉': 'Miên', '油': 'Du', '瓜': 'Qua', '豆': 'Đậu', '果': 'Quả',
    '榕': 'Dong', '楠': 'Nam', '杉': 'Sam', '樺': 'Hoa', '柘': 'Trá',
    '桓': 'Hoàn', '槐': 'Hòe', '棣': 'Đệ', '柞': 'Tác', '枋': 'Phương',
    '蘿': 'La', '藤': 'Đằng', '蕉': 'Tiêu', '芙': 'Phù', '蓉': 'Dung',
    '芎': 'Khung', '芷': 'Chỉ', '蒗': 'Lãng', '莎': 'Sa', '茄': 'Già',
    '苓': 'Linh', '蕭': 'Tiêu', '蘄': 'Kỳ', '螺': 'Loa', '莿': 'Thứ',
    '魚': 'Ngư', '鯉': 'Lý', '牛': 'Ngưu', '羊': 'Dương', '獅': 'Sư',
    '猛': 'Mãnh', '猇': 'Hao', '鶯': 'Oanh', '鳩': 'Cưu', '鳥': 'Điểu',
    '鳴': 'Minh', '蛟': 'Giao', '麟': 'Lân', '麒': 'Kỳ', '龜': 'Quy',
    '虹': 'Hồng', '象': 'Tượng', '獨': 'Độc', '嵊': 'Thặng',
    # Water (supplemental)
    '澎': 'Bành', '澗': 'Giản', '澳': 'Úc', '滎': 'Huỳnh', '灞': 'Bá',
    '湟': 'Hoàng', '涪': 'Phù', '渠': 'Cừ', '溧': 'Lật', '淶': 'Lai',
    '汶': 'Vấn', '沾': 'Chiêm', '溮': 'Sư', '潢': 'Hoàng', '濉': 'Tuệ',
    '瀍': 'Triền', '澠': 'Thằng', '淇': 'Kỳ', '浚': 'Tuấn', '淅': 'Tích',
    '泌': 'Bí', '涵': 'Hàm', '湞': 'Trinh', '濠': 'Hào', '濞': 'Bí',
    '漾': 'Dạng', '瀾': 'Lan', '瀏': 'Lưu', '汨': 'Mịch', '汪': 'Uông',
    '沽': 'Cô', '泊': 'Bạc', '渦': 'Oa', '濃': 'Nùng', '淩': 'Lăng',
    '潤': 'Nhuận', '乳': 'Nhũ', '洑': 'Phục',
    # Mountains & terrain (supplemental)
    '嶼': 'Tự', '嶗': 'Lao', '嶧': 'Dịch', '崁': 'Khảm', '巒': 'Loan',
    '麓': 'Lộc', '磐': 'Bàn', '壺': 'Hồ', '磴': 'Đặng', '礁': 'Tiêu',
    '窪': 'Oa', '坑': 'Khanh', '岑': 'Sầm', '岐': 'Kỳ', '岫': 'Tụ',
    '棱': 'Lăng', '塞': 'Tái', '鼎': 'Đỉnh', '巍': 'Nguy', '岸': 'Ngạn',
    # Administrative & people
    '官': 'Quan', '師': 'Sư', '王': 'Vương', '君': 'Quân', '侯': 'Hầu',
    '伯': 'Bá', '任': 'Nhậm', '禮': 'Lễ', '祿': 'Lộc', '祜': 'Hỗ',
    '祁': 'Kỳ', '社': 'Xã', '禹': 'Vũ', '穆': 'Mục', '姚': 'Diêu',
    '氏': 'Thị', '姑': 'Cô', '心': 'Tâm', '愛': 'Ái', '喜': 'Hỷ',
    '禮': 'Lễ', '卓': 'Trác', '彌': 'Di', '虞': 'Ngu', '聶': 'Nhiếp',
    '翁': 'Ông', '牟': 'Mưu', '覃': 'Đàm', '袁': 'Viên', '賈': 'Giả',
    '戚': 'Thích', '杜': 'Đỗ', '姜': 'Khương', '鄒': 'Trâu', '孫': 'Tôn',
    '葛': 'Cát', '范': 'Phạm', '薛': 'Tiết', '鄧': 'Đặng', '潘': 'Phan',
    '謝': 'Tạ', '蕭': 'Tiêu', '祝': 'Chúc', '任': 'Nhậm', '仲': 'Trọng',
    '如': 'Như', '耀': 'Diệu', '聖': 'Thánh', '英': 'Anh',
    # Stars, heaven & nature concepts
    '星': 'Tinh', '望': 'Vọng', '照': 'Chiếu', '旌': 'Tinh', '霄': 'Tiêu',
    '暖': 'Noãn', '炎': 'Viêm', '風': 'Phong', '凰': 'Hoàng', '霸': 'Bá',
    '霧': 'Vụ', '暉': 'Huy', '輝': 'Huy', '晃': 'Hoảng', '晏': 'Yển',
    '翔': 'Tường', '翁': 'Ông', '翼': 'Dực', '騰': 'Đằng', '驛': 'Dịch',
    '驊': 'Hoa', '冬': 'Đông', '乾': 'Kiền', '乃': 'Nãi', '於': 'Vu',
    # 7 chars still missing after pass 7
    '紮': 'Trát', '頗': 'Phả', '浪': 'Lãng', '交': 'Giao',
    '拜': 'Bái', '煩': 'Phiền', '准': 'Chuẩn',
    # Materials & tools
    '墨': 'Mặc', '鋼': 'Cương', '鐘': 'Chung', '鉅': 'Cự', '鎣': 'Oanh',
    '鉛': 'Diên', '鏡': 'Kính', '鑼': 'La', '閘': 'Trát', '燈': 'Đăng',
    '箭': 'Tiễn', '車': 'Xa', '弓': 'Cung', '刀': 'Đao', '磅': 'Bảng',
    '碑': 'Bi', '碧': 'Bích', '璧': 'Bích', '琅': 'Lang', '琊': 'Nha',
    '琴': 'Cầm', '琉': 'Lưu', '球': 'Cầu', '玉': 'Ngọc',
    # Peoples & ethnic groups
    '佤': 'Ngõa', '傈': 'Lật', '僳': 'Túc', '寮': 'Liêu', '佬': 'Lão',
    '仡': 'Ngật', '仫': 'Mục', '彝': 'Di', '苗': 'Miêu', '瑤': 'Diêu',
    # Place names (common enough chars)
    '美': 'Mỹ', '圳': 'Chân', '澎': 'Bành', '鮮': 'Tiên', '寮': 'Liêu',
    '甸': 'Điện', '托': 'Thác', '社': 'Xã', '郊': 'Giao', '界': 'Giới',
    '思': 'Tư', '良': 'Lương', '梓': 'Tử', '斗': 'Đấu', '尖': 'Tiêm',
    '額': 'Ngạch', '匯': 'Hối', '鞏': 'Củng', '澗': 'Giản', '塞': 'Tái',
    '彌': 'Di', '湟': 'Hoàng', '埤': 'Tỳ', '辛': 'Tân', '館': 'Quán',
    '陶': 'Đào', '圍': 'Vi', '皮': 'Bì', '間': 'Gian', '迎': 'Nghênh',
    '權': 'Quyền', '休': 'Hưu', '聞': 'Văn', '絳': 'Giáng', '賽': 'Tái',
    '罕': 'Hãn', '默': 'Mặc', '侖': 'Lôn', '喇': 'Lạt', '斡': 'Oát',
    '賚': 'Lai', '蓋': 'Cái', '票': 'Phiếu', '蔭': 'Ẩm', '湯': 'Thang',
    '遜': 'Tốn', '墅': 'Thự', '壇': 'Đàn', '儀': 'Nghi', '甌': 'Âu',
    '諸': 'Chư', '岱': 'Đại', '積': 'Tích', '譙': 'Tiêu', '為': 'Vi',
    '將': 'Tướng', '尋': 'Tầm', '汶': 'Vấn', '沾': 'Chiêm', '尉': 'Úy',
    '葉': 'Diệp', '舞': 'Vũ', '召': 'Thiệu', '茅': 'Mao', '軍': 'Quân',
    '君': 'Quân', '桑': 'Tang', '赫': 'Hách', '融': 'Dung', '涪': 'Phù',
    '巫': 'Vu', '柱': 'Trụ', '渠': 'Cừ', '印': 'Ấn', '穗': 'Tuệ',
    '祿': 'Lộc', '猛': 'Mãnh', '卡': 'Ka', '囊': 'Nang', '查': 'Tra',
    '旬': 'Tuần', '撒': 'Tán', '奇': 'Kỳ', '別': 'Biệt', '芳': 'Phương',
    '員': 'Viên', '楊': 'Dương', '屋': 'Ốc', '勢': 'Thế', '崙': 'Lôn',
    '灞': 'Bá', '恰': 'Hợp', '股': 'Cổ',
    # Terrain & city features (supplemental)
    '廠': 'Xưởng', '故': 'Cố', '昔': 'Tích', '遙': 'Diêu', '介': 'Giới',
    '稷': 'Tắc', '芮': 'Nhuế', '沃': 'Ốc', '隰': 'Tập', '奈': 'Nại',
    '曼': 'Mạn', '莫': 'Mạc', '力': 'Lực', '突': 'Đột', '僕': 'Bộc',
    '旅': 'Lữ', '立': 'Lập', '振': 'Chấn', '蛟': 'Giao', '主': 'Chủ',
    '宇': 'Vũ', '敦': 'Đôn', '琿': 'Hồn', '訥': 'Nột', '向': 'Hướng',
    '漠': 'Mạc', '鄴': 'Nghiệp', '戚': 'Thích', '相': 'Tương', '啟': 'Khải',
    '盱': 'Hu', '眙': 'Di', '響': 'Hưởng', '邗': 'Hàn', '征': 'Chinh',
    '徒': 'Đồ', '拱': 'Củng', '鄞': 'Ngân', '曙': 'Thự', '暨': 'Ký',
    '縉': 'Tấn', '畬': 'Du', '塗': 'Đồ', '樅': 'Tòng', '歙': 'Hấp',
    '黟': 'Y', '埇': 'Dũng', '碭': 'Đáng', '含': 'Hàm', '績': 'Tích',
    '廂': 'Sương', '列': 'Liệt', '薌': 'Hương', '詔': 'Chiếu', '譜': 'Phổ',
    '月': 'Nguyệt', '猶': 'Do', '載': 'Tải', '鉛': 'Diên', '嶗': 'Lao',
    '即': 'Tức', '度': 'Độ', '嶧': 'Dịch', '兒': 'Nhi', '墾': 'Khẩn',
    '罘': 'Phù', '招': 'Chiêu', '寒': 'Hàn', '朐': 'Cù', '微': 'Vi',
    '費': 'Phí', '莘': 'Sơn', '茌': 'Si', '冠': 'Quan', '棣': 'Đệ',
    '單': 'Đơn', '鄄': 'Quyển', '管': 'Quản', '杞': 'Kỷ', '考': 'Khảo',
    '偃': 'Yển', '郟': 'Giáp', '殷': 'Ân', '滑': 'Hoạt', '牧': 'Mục',
    '獲': 'Hoạch', '站': 'Trạm', '陟': 'Trắc', '郾': 'Yển', '宛': 'Uyển',
    '臥': 'Ngọa', '輿': 'Dư', '確': 'Xác', '礄': 'Kiều', '冶': 'Dã',
    '伍': 'Ngũ', '點': 'Điểm', '秭': 'Tử', '掇': 'Truyết', '夢': 'Mộng',
    '監': 'Giám', '滋': 'Tư', '團': 'Đoàn', '浠': 'Hi', '穴': 'Huyệt',
    '曾': 'Tăng', '攸': 'Do', '醴': 'Lễ', '蒸': 'Chưng', '植': 'Thực',
    '零': 'Linh', '牌': 'Bài', '漵': 'Xu', '丈': 'Trượng', '廉': 'Liêm',
    '要': 'Yêu', '郁': 'Úc', '邕': 'Ung', '疊': 'Điệp', '恭': 'Cung',
    '業': 'Nghiệp', '毛': 'Mao', '等': 'Đẳng', '憑': 'Bằng', '指': 'Chỉ',
    '碚': 'Bối', '綦': 'Kỳ', '足': 'Túc', '墊': 'Điệm', '酉': 'Dậu',
    '邡': 'Phảng', '郫': 'Tỳ', '邛': 'Cùng', '崍': 'Lai', '敘': 'Tự',
    '藺': 'Lẫn', '旺': 'Vượng', '船': 'Thuyền', '射': 'Xạ', '犍': 'Kiền',
    '研': 'Nghiên', '沐': 'Mộc', '閬': 'Lãng', '珙': 'Củng', '筠': 'Quân',
    '經': 'Kinh', '簡': 'Giản', '孚': 'Phu', '爐': 'Lô', '得': 'Đắc',
    '謀': 'Mưu', '冕': 'Miện', '烽': 'Phong', '真': 'Chân', '習': 'Tập',
    '阡': 'Thiên', '謨': 'Mô', '亨': 'Hanh', '織': 'Chức', '雍': 'Ung',
    '凱': 'Khải', '秉': 'Bỉnh', '勻': 'Quân', '甕': 'Ủng', '呈': 'Trình',
    '勸': 'Khuyến', '沖': 'Xung', '巧': 'Xảo', '耿': 'Cảnh', '個': 'Cá',
    '舊': 'Cựu', '硯': 'Nghiễn', '疇': 'Trù', '臘': 'Lạp', '盈': 'Doanh',
    '堆': 'Đôi', '丁': 'Đinh', '芒': 'Mang', '加': 'Gia', '錯': 'Thác',
    '比': 'Tỷ', '申': 'Thân', '索': 'Tố', '戈': 'Qua', '札': 'Trát',
    '噶': 'Hát', '革': 'Cách', '改': 'Cải', '脫': 'Thoát', '隅': 'Ngung',
    '未': 'Vị', '央': 'Ương', '戶': 'Hộ', '彬': 'Bân', '起': 'Khởi',
    '略': 'Lược', '脂': 'Chi', '瓜': 'Qua', '宕': 'Đãng', '兩': 'Lưỡng',
    '迭': 'Điệt', '碌': 'Lộc', '循': 'Tuần', '剛': 'Cương', '久': 'Cửu',
    '雜': 'Tạp', '稱': 'Xưng', '謙': 'Khiêm', '令': 'Lệnh', '峻': 'Tuấn',
    '阪': 'Phản', '坤': 'Khôn', '壘': 'Lũy', '精': 'Tinh', '碩': 'Thạc',
    '干': 'Can', '策': 'Sách', '敏': 'Mẫn', '蘊': 'Uẩn', '堵': 'Đổ',
    '板': 'Bản', '汐': 'Tịch', '碇': 'Định', '歌': 'Ca', '重': 'Trọng',
    '淡': 'Đạm', '壢': 'Lịch', '份': 'Phần', '庄': 'Trang', '造': 'Tạo',
    '后': 'Hậu', '肚': 'Đỗ', '姓': 'Tính', '伸': 'Thân', '褒': 'Bao',
    '背': 'Bội', '埕': 'Thành', '朴': 'Phác', '腳': 'Cước', '袋': 'Đại',
    '學': 'Học', '萣': 'Định', '恆': 'Hằng', '卑': 'Ti', '琉': 'Lưu',
    '藁': 'Cảo', '蠡': 'Lý', '盂': 'Vu', '遙': 'Diêu', '猗': 'Y',
    '岢': 'Khả', '曼': 'Mạn', '審': 'Thẩm', '磅': 'Bảng', '坑': 'Khanh',
    '穀': 'Cốc', '牟': 'Mưu', '澳': 'Úc', '結': 'Kết', '滎': 'Huỳnh',
    '藍': 'Lam', '翁': 'Ông', '乾': 'Kiền', '蔭': 'Ẩm', '閘': 'Trát',
    '蕉': 'Tiêu', '霄': 'Tiêu', '柘': 'Trá', '乳': 'Nhũ', '葉': 'Diệp',
    '召': 'Thiệu', '桑': 'Tang', '赫': 'Hách', '融': 'Dung', '滮': 'Bao',
    '駱': 'Lạc', '驪': 'Ly',
}



def _han_viet(name_raw: str) -> str:
    """Transliterate a raw Chinese place name to Hán-Việt reading char by char."""
    if not name_raw:
        return name_raw
    parts = []
    for ch in name_raw:
        parts.append(HAN_VIET_CHAR.get(ch, ch))
    return ' '.join(parts)



def parse_dila_district(district_str):
    """Parse DILA district string (e.g. '阿富汗-巴爾赫省(Balkh)-CharBolak')
    into dict {country_vi, province, district_vi, formatted}.
    Returns dict with only non-empty fields. No HVDic used.
    """
    if not district_str or not district_str.strip():
        return {}
    text = district_str.strip()
    # Multi-district strings (semicolons): take the first one only
    if ';' in text:
        text = text.split(';')[0].strip()
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    # If already Latin/Vietnamese, try simple extraction
    if not has_chinese:
        parts = text.replace('，', ',').split(',')
        if len(parts) >= 2:
            district_vi = ','.join(parts[:-1]).strip()
            country_vi = parts[-1].strip()
        else:
            district_vi = text
            country_vi = ''
        return {'country_vi': country_vi, 'district_vi': district_vi, 'formatted': text}
    # Has Chinese: split by '-'
    dash_parts = text.split('-')
    country_vi = ''
    province = ''
    district_vi = ''
    # Part 0: country
    if len(dash_parts) > 0:
        for zh, vi in COUNTRY_MAP.items():
            if zh in dash_parts[0]:
                country_vi = vi
                break
    # Detect Chinese admin hierarchy: any part[1..N] ends with suffix in ADMIN_LEVEL_MAP
    has_cn_admin = False
    if len(dash_parts) > 1:
        for p in dash_parts[1:]:
            if any(p.endswith(s) for s in ADMIN_LEVEL_MAP):
                has_cn_admin = True
                break
    # Segments classified as admin type (not real place names) — skip these
    _SKIP_SEGMENTS = {'市轄', '縣轄', '省直轄', '地區', '直轄', '地级市'}
    if has_cn_admin:
        segments = []
        for part in dash_parts[1:]:
            part = part.strip()
            if not part or part in _SKIP_SEGMENTS:
                continue
            found = False
            for suffix, level_vi in ADMIN_LEVEL_MAP.items():
                if part.endswith(suffix):
                    name_raw = part[:-len(suffix)]
                    if not name_raw or name_raw in _SKIP_SEGMENTS:
                        found = True  # skip this segment, don't add to output
                        break
                    name_vi = CHINESE_PLACE_NAMES.get(name_raw) or _han_viet(name_raw)
                    segments.append(f'{level_vi} {name_vi}')
                    found = True
                    break
            if not found:
                # No standard suffix: check if it's a known municipality or dict entry
                if part in MUNICIPALITIES:
                    name_vi = CHINESE_PLACE_NAMES.get(part) or _han_viet(part)
                    segments.append(f'thành phố {name_vi}')
                elif part in CHINESE_PLACE_NAMES:
                    segments.append(CHINESE_PLACE_NAMES[part])
                else:
                    segments.append(_han_viet(part))
        # Reverse order: small → large (huyện → thành phố → tỉnh)
        segments.reverse()
        district_vi_final = ', '.join(segments)
        formatted_parts = [p for p in [district_vi_final, country_vi] if p]
        return {
            'country_vi': country_vi,
            'province': '',
            'district_vi': district_vi_final,
            'formatted': ', '.join(formatted_parts),
        }
    # Afghanistan / Latin pattern (original logic)
    # Part 1: province (extract from parentheses)
    if len(dash_parts) > 1:
        m = re.search(r'\(([^)]+)\)', dash_parts[1])
        if m:
            province = m.group(1).strip()
    # Part 2: huyện/locality
    if len(dash_parts) > 2:
        raw = dash_parts[2].strip()
        district_vi = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw)
        district_vi = re.sub(r'[^\x00-\x7F\s]', '', district_vi).strip()
    if not district_vi and len(dash_parts) > 1:
        after_paren = re.sub(r'\([^)]*\)', '', dash_parts[1]).strip()
        after_paren = re.sub(r'[\u4e00-\u9fff]', '', after_paren).strip()
        if after_paren:
            district_vi = re.sub(r'([a-z])([A-Z])', r'\1 \2', after_paren)
    loc_parts = []
    if district_vi:
        loc_parts.append(f'huyện {district_vi}')
    if province:
        loc_parts.append(f'tỉnh {province}')
    district_vi_final = ', '.join(loc_parts)
    formatted_parts = [p for p in [district_vi_final, country_vi] if p]
    return {
        'country_vi': country_vi,
        'province': province,
        'district_vi': district_vi_final,
        'formatted': ', '.join(formatted_parts),
    }



# Dashboard Process Tracker — phục vụ file tĩnh thư mục dashboard/ (mở trực tiếp từ app.py:5000)
DASHBOARD_DIR = os.path.join(BASE_DIR, 'dashboard')



# ---------------------------------------------------------------------------
# T169 — Địa danh Groq review (side-car place_groq_audit)
# ---------------------------------------------------------------------------
_T169_DIFF_SORT = """
CASE a.diff_type
  WHEN 'POLYPHONIC_CHAR' THEN 0
  WHEN 'TAXONOMY_VARIANT' THEN 1
  WHEN 'PHONETIC_MISMATCH' THEN 2
  ELSE 3
END
"""




def _make_source_code(name):
    """Tạo source_code từ tên — fallback khi không có code rõ ràng."""
    s = re.sub(r'[^A-Za-z0-9]+', '_', unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()).strip('_').upper()
    return f'SRC_{s}' if s else 'SRC_NEW'




def _iso_now():
    from datetime import datetime as _dt
    return _dt.now().isoformat(timespec='seconds')




# ============================================================
# T139 Phase 2 — Zen Lineage HITL Review (additive, DERIVED-only)
# ------------------------------------------------------------
# Candidate pool: source_staging (row_type='master') — không đụng entity_source_ids
# (schema chặn entity_id NULL).
# Quyết định HITL: bảng DERIVED zenlineage_review (0 ALTER base).
# Approve → ghi entity_source_ids (entity_id thật, verified=1, match_status='approved').
# ============================================================
_ZEN_REVIEW_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS zenlineage_review (
    source_entity_id   TEXT PRIMARY KEY,
    status             TEXT NOT NULL,      -- approved | rejected
    dila_person_id     TEXT,
    entity_hub_id      INTEGER,
    confidence         REAL,
    editor             TEXT,
    note               TEXT,
    created_at         TEXT,
    updated_at         TEXT
)
"""




def _zen_ensure_review_table(conn):
    conn.execute(_ZEN_REVIEW_TABLE_SQL)
    conn.commit()




def _zen_suggest(conn, name, limit=5):
    """Gợi ý DILA person cho 1 zen slug — dò token trong tên (name_zh/name_vi/name_en/id).
    Trả về top candidates: {dila_id, name_vi, name_zh, sect, entity_hub_id, score}."""
    name = (name or '').strip()
    if not name:
        return []
    tokens = [t for t in (name.replace('-', ' ').replace('_', ' ').split()) if len(t) >= 2]
    if not tokens:
        return []
    # dò từng token riêng (OR) — token dài >=3 lấy nguyên, token 2 ký tự dùng prefix
    likes = []
    for t in tokens[:4]:
        like = t + '%' if len(t) >= 3 else '%' + t + '%'
        likes.append(like)
    ors = ' OR '.join(['p.name_zh LIKE ?', 'p.name_vi LIKE ?', 'p.name_en LIKE ?', 'p.name_ja LIKE ?'] * len(likes))
    params = []
    for like in likes:
        params += [like, like, like, like]
    params.append(limit * 8)
    rows = conn.execute(
        """SELECT p.id AS dila_id, p.name_vi, p.name_zh, p.name_en, p.name_ja, p.sect,
                  (SELECT eh.entity_id FROM entity_hub eh
                    WHERE eh.entity_type='PERSON' AND eh.canonical_label=p.id LIMIT 1) AS entity_hub_id
             FROM people p
             WHERE %s
             LIMIT ?""" % ors, params).fetchall()
    out = []
    for r in rows:
        hay = ' '.join(x or '' for x in (r['name_zh'], r['name_vi'], r['name_en'], r['name_ja']))
        score = 0
        for t in tokens:
            if t in hay:
                score += 2
            elif t[:2] in hay or t[:2] in (r['name_zh'] or ''):
                score += 1
        # tiêu chuẩn hóa Hán tự: nếu zen tên Hán trùng 1-2 ký tự chữ Hán
        if r['name_zh']:
            for ch in tokens:
                for c in ch:
                    if len(c) == 1 and c in r['name_zh']:
                        score += 1
        if score == 0:
            continue
        hit = {'dila_id': r['dila_id'], 'name_vi': r['name_vi'], 'name_zh': r['name_zh'],
               'name_en': r['name_en'], 'sect': r['sect'], 'entity_hub_id': r['entity_hub_id'],
               'score': score}
        out.append(hit)
    out.sort(key=lambda x: -x['score'])
    seen = set()
    uniq = []
    for h in out:
        if h['dila_id'] not in seen:
            seen.add(h['dila_id'])
            uniq.append(h)
    return uniq[:limit]




def _call_gemini(prompt, timeout=15):
    """Shared helper: call Groq LLM, return text or None."""
    try:
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.1, 'max_tokens': 2048},
            timeout=timeout)
        result = resp.json()
        if result.get('choices'):
            text = result['choices'][0]['message']['content']
            if text:
                return text
    except Exception:
        pass
    return None




def clean_gemini_output(text):
    """Filter Gemini output: remove lines that are pure noise (ETA, repeated (CBETA with no useful content).
    Keeps metadata lines with :, http, URLs, gXXXX(...) citations, CBETA refs like (CBETA T50n2060_p...)."""
    if not text:
        return text
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == 'ETA':
            continue
        if re.match(r'^\(CBETA[\s\(\)]*$', line):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)




# ── CBETA ref_passages cache table ──────────────────────────────────────

CBETA_REF_TABLE = 'cbeta_ref_passages'


CBETA_REF_DDL = """
CREATE TABLE IF NOT EXISTS {table} (
    ref_code          TEXT PRIMARY KEY,
    sigla             TEXT NOT NULL,
    juan              INTEGER,
    page              TEXT,
    line_start        INTEGER,
    line_end          INTEGER,
    han_text          TEXT NOT NULL,
    vi_summary        TEXT,
    vi_summary_raw    TEXT,
    vi_summary_clean  TEXT,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP
)
""".format(table=CBETA_REF_TABLE)




def ensure_cbeta_ref_table():
    conn = get_db_connection()
    try:
        conn.execute(CBETA_REF_DDL)
        # Migrate existing DB: add columns if missing
        for col in ['vi_summary_raw', 'vi_summary_clean']:
            try:
                conn.execute(f"ALTER TABLE {CBETA_REF_TABLE} ADD COLUMN {col} TEXT")
            except Exception:
                pass  # column already exists
        # Backfill: copy old vi_summary → vi_summary_raw where vi_summary_raw is empty
        conn.execute(f"""
            UPDATE {CBETA_REF_TABLE}
            SET vi_summary_raw = vi_summary
            WHERE vi_summary IS NOT NULL AND vi_summary != ''
              AND (vi_summary_raw IS NULL OR vi_summary_raw = '')
        """)
        conn.commit()
    finally:
        conn.close()




ensure_cbeta_ref_table()




# ── AI Person Name table (T231) ───────────────────────────────────────────
def ensure_ai_person_name_table():
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_person_name (
                dila_id     TEXT PRIMARY KEY,
                name_vi_ai  TEXT,
                model       TEXT DEFAULT 'gemini-3.8-flash',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()



ensure_ai_person_name_table()




# ── CBETA ref_explanations (Giải thích) cache table ──────────────────────

CBETA_EXPLAIN_TABLE = 'cbeta_ref_explanations'


CBETA_EXPLAIN_DDL = """
CREATE TABLE IF NOT EXISTS {table} (
    ref               TEXT NOT NULL,
    place_id          TEXT NOT NULL,
    place_han         TEXT NOT NULL,
    han_sentence      TEXT NOT NULL,
    explanation_vi    TEXT NOT NULL,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ref, place_id)
)
""".format(table=CBETA_EXPLAIN_TABLE)




def ensure_cbeta_explain_table():
    conn = get_db_connection()
    try:
        conn.execute(CBETA_EXPLAIN_DDL)
        conn.commit()
    finally:
        conn.close()




ensure_cbeta_explain_table()




def extract_sentence_with_place(han_block, place_han):
    """Split han_block into sentences, return the first sentence containing place_han."""
    if not han_block or not place_han:
        return (han_block or '').strip()
    sentences = re.split(r'[。！？]', han_block)
    for s in sentences:
        if place_han in s:
            return s.strip()
    return han_block.strip()[:300]




def build_name_map(han_text):
    """Query DILA + lexicon tables for Hán-Việt name pairs found in han_text.
    Returns dict {chinese_form: vietnamese_form} sorted by length descending.
    Sources: name_vi_map (persons), namevi_map_places (places)."""
    if not han_text:
        return {}
    conn = get_db_connection()
    name_map = {}
    try:
        # Person names
        rows = conn.execute(
            "SELECT name_zh, name_vi FROM name_vi_map WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in rows:
            zh = r['name_zh'].strip()
            vi = r['name_vi'].strip()
            if zh and vi and zh in han_text:
                name_map[zh] = vi
        # Place names
        rows = conn.execute(
            "SELECT name_zh, name_vi FROM namevi_map_places WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in rows:
            zh = r['name_zh'].strip()
            vi = r['name_vi'].strip()
            if zh and vi and zh in han_text:
                name_map[zh] = vi
    finally:
        conn.close()
    # Sort by length descending so longer matches take priority
    sorted_items = sorted(name_map.items(), key=lambda x: -len(x[0]))
    return dict(sorted_items)




def make_cbeta_prompt(han_text, name_map, ref):
    """Build Gemini prompt for CBETA translation with lexicon constraints."""
    if name_map:
        lex_lines = [f"{zh} → {vi}" for zh, vi in name_map.items()]
        lex_block = "\n".join(lex_lines)
        lex_section = f"""
[LEXICON HÁN-VIỆT BẮT BUỘC]
Các tên riêng dưới đây PHẢI được dịch đúng theo mapping sau:
{lex_block}

QUY ƯỚC TÊN RIÊNG:
- Mọi TÊN NGƯỜI, TÊN CHÙA, TÊN ĐỊA DANH trong đoạn phải dùng dạng Hán-Việt từ LEXICON.
- Không dùng dạng tiếng Anh hoặc Pinyin.
- Ví dụ: 少林寺 → Thiếu Lâm Tự (không dùng Shaolin Temple), 少林 → Thiếu Lâm (không dùng Shaolin).
- Nếu gặp tên riêng không có trong LEXICON, hãy đoán dạng Hán-Việt.
"""
    else:
        lex_section = """
QUY ƯỚC TÊN RIÊNG:
- Mọi tên người, tên chùa, tên địa danh phải dùng dạng Hán-Việt.
- Không dùng dạng tiếng Anh, Pinyin, hoặc phiên âm hiện đại.
- Ví dụ: 少林寺 → Thiếu Lâm Tự, 會稽 → Cối Kê.
"""

    prompt = f"""[HÁN GỐC]
{han_text}
{lex_section}
YÊU CẦU DỊCH THUẬT:
- Dịch đoạn Hán trên sang tiếng Việt hiện đại, mạch lạc, dễ hiểu.
- Giữ đủ thông tin về lai lịch nhân vật, bối cảnh địa danh, sự kiện tu học / hoằng pháp chính, kết cuộc (niên đại, nơi tịch nếu có).
- Văn phong tường thuật, nối câu mạch lạc (không chẻ thành câu vụn).
- Không liệt kê từng câu nguyên văn; chỉ cần 1 đoạn tiếng Việt hoàn chỉnh.

Độ dài:
- 1–2 câu Hán → 1–2 câu Việt.
- 3–5 câu Hán → 3–4 câu Việt.
- 5–10 câu Hán → 5–7 câu Việt.
- Không bao giờ chỉ ghi 1 câu chung chung.

Số hiệu mã: {ref}
"""
    return prompt.strip()




def parse_ref(ref_code):
    """Parse ref_code like 'T50n2060_p0457c16' into components.
    Returns dict with {sigla, canon, vol, text_num, page_comp, line_num} or None."""
    m = re.match(r'^([A-Z])(\d+)n(\d+)_p?(\d+)([a-z])(\d+)$', ref_code)
    if not m:
        return None
    canon, vol_str, text_num, page_num, col, line_str = m.groups()
    sigla = f"{canon}{vol_str}n{text_num}"
    page_comp = page_num + col  # e.g. '0457c'
    return {
        'sigla': sigla,
        'canon': canon,
        'vol': int(vol_str),
        'text_num': int(text_num),
        'page_comp': page_comp,
        'page_num': page_num,
        'col': col,
        'line_num': int(line_str),
    }




def _sync_ref_passage(ref, context=''):
    """Query cbeta.db for han_text for a single ref_code.
    If context given, search nearby pages for it when exact match fails.
    Returns dict with {han_text, sigla, title} or None if not found.
    Inserts/updates cbeta_ref_passages table."""
    parsed = parse_ref(ref)
    if not parsed:
        return None

    sigla = parsed['sigla']
    page_comp = parsed['page_comp']
    page_num = parsed['page_num']
    line_num = parsed['line_num']

    han_text = None
    title = sigla
    juan = None

    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id, title_zh, juan_count FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()
        if text_row:
            text_id = text_row['id']
            title = text_row['title_zh'] or sigla

            # Try exact page+col match first
            contents = cconn.execute("""
                SELECT juan, page, content_zh FROM cbeta_content_index
                WHERE text_id = ? AND (page = ? OR page = ?)
                ORDER BY rowid
            """, (text_id, page_comp, page_comp.upper())).fetchall()

            if not contents:
                # Fallback: page prefix match (first 4 digits)
                prefix = page_num
                contents = cconn.execute("""
                    SELECT juan, page, content_zh FROM cbeta_content_index
                    WHERE text_id = ? AND page LIKE ?
                    ORDER BY page, rowid LIMIT 20
                """, (text_id, f"{prefix}%")).fetchall()

            if not contents and context:
                # Context-aware fallback: search for context term in nearby pages
                nearby = cconn.execute("""
                    SELECT juan, page, content_zh FROM cbeta_content_index
                    WHERE text_id = ?
                    ORDER BY ABS(CAST(page AS INTEGER) - ?)
                    LIMIT 200
                """, (text_id, page_num)).fetchall()
                context_results = [r for r in nearby if r['content_zh'] and context in r['content_zh']]
                if context_results:
                    contents = context_results[:5]

            if contents:
                lines = [r['content_zh'] for r in contents]
                han_text = '\n'.join(lines)
                if han_text:
                    han_text = han_text[:50000]
                juan = contents[0]['juan']
        cconn.close()
    except Exception:
        pass

    if not han_text:
        han_text = ''

    # Upsert into cbeta_ref_passages
    conn = get_db_connection()
    try:
        conn.execute(f"""
            INSERT INTO {CBETA_REF_TABLE} (ref_code, sigla, juan, page, line_start, line_end, han_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ref_code) DO UPDATE SET
                sigla=excluded.sigla, juan=excluded.juan, page=excluded.page,
                line_start=excluded.line_start, line_end=excluded.line_end,
                han_text=excluded.han_text, updated_at=CURRENT_TIMESTAMP
        """, (ref, sigla, juan, page_comp, line_num, line_num, han_text))
        conn.commit()
    finally:
        conn.close()

    if not han_text:
        return None
    return {'han_text': han_text, 'sigla': sigla, 'title': title}




def _search_context_nearby(sigla, page_str, context):
    """Search cbeta.db for text containing context term near given page."""
    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id FROM cbeta_texts WHERE sigla = ?", (sigla,)
        ).fetchone()
        if not text_row:
            cconn.close()
            return None
        text_id = text_row['id']
        # Extract page number for proximity sort
        page_num = 0
        if page_str:
            try:
                page_num = int(''.join(filter(str.isdigit, page_str)) or 0)
            except ValueError:
                pass
        if not page_num:
            # fallback: just search anywhere in this text
            rows = cconn.execute("""
                SELECT content_zh FROM cbeta_content_index
                WHERE text_id = ? AND content_zh LIKE ?
                LIMIT 10
            """, (text_id, f'%{context}%')).fetchall()
        else:
            rows = cconn.execute("""
                SELECT juan, page, content_zh FROM cbeta_content_index
                WHERE text_id = ?
                ORDER BY ABS(CAST(SUBSTR(page,1,4) AS INTEGER) - ?)
                LIMIT 300
            """, (text_id, page_num)).fetchall()
            # Filter to those containing context
            rows = [r for r in rows if r['content_zh'] and context in r['content_zh']][:5]
        cconn.close()
        if rows:
            return '\n'.join(r['content_zh'] or '' for r in rows)[:50000]
    except Exception:
        pass
    return None




@app.route('/daoanh/api/admin/translate_gemini_cbeta', methods=['POST'])
def translate_gemini_cbeta():
    """
    POST /daoanh/api/admin/translate_gemini_cbeta
    Body: { ref: "T50n2060_p0574b20", context: "少林" }
    Flow:
    1) Check cbeta_ref_passages for cached vi_summary_clean → return instantly.
    2) If no han_text in table, sync from cbeta.db.
       - If context given, search for context term in nearby pages.
    3) Build name_map from lexicon (DILA + BIẾN THỂ DANH XƯNG).
    4) Call Gemini with lexicon-enhanced prompt → vi_summary_raw.
    5) Call Gemini again for 3–5 câu summary → vi_summary_clean.
    6) Cache both, return.
    """
    try:
        body = request.get_json(silent=True) or {}
        ref = (body.get('ref') or '').strip()
        context = (body.get('context') or '').strip()

        # If context is in the raw bibl string like "CBETA T50n2060_p0574b20 {少林}",
        # extract from { }
        if not context and '{' in ref:
            m = re.search(r'\{([^}]+)\}', ref)
            if m:
                context = m.group(1).strip()
                ref = re.sub(r'\s*\{[^}]*\}', '', ref).strip()
        # Also try to extract from body raw field
        if not context:
            raw_bibl = (body.get('raw') or '').strip()
            m = re.search(r'\{([^}]+)\}', raw_bibl)
            if m:
                context = m.group(1).strip()

        if not ref:
            return jsonify({"ok": False, "success": False, "error": "Thiếu ref"}), 400

        # 1) ALWAYS resolve fresh Han text from cbeta.db (Layer 1).
        #    _sync_ref_passage queries cbeta.db only, never joins Vietnamese tables.
        sync_result = _sync_ref_passage(ref, context)
        if not sync_result:
            return jsonify({
                "ok": False, "success": False, "error": "no_text",
                "message": f"Chưa có văn bản CBETA trong DB cho {ref}."
            })

        han_text = sync_result['han_text']
        sigla = sync_result['sigla']
        title = sync_result['title']

        # Extract sentence containing context (place_han) for focused LLM input
        han_sentence = extract_sentence_with_place(han_text, context) if context else ''
        llm_input = han_sentence if han_sentence else han_text

        # 2) ALWAYS translate fresh (no cache skip — stale vi_summary_clean must not block re-translation).
        #    After translation, the result is saved to cbeta_ref_passages for future display.

        # 3) Build name_map from lexicon (use full han_text for name scanning)
        name_map = build_name_map(han_text)

        # 4) Stage 1: Translate/dịch thô with lexicon-enhanced prompt (use llm_input for focus)
        prompt_raw = make_cbeta_prompt(llm_input, name_map, ref)
        text_vi_raw = _call_gemini(prompt_raw, timeout=15)
        provider_raw = 'gemini-3.6-flash'

        if not text_vi_raw:
            try:
                import translators as ts
                text_vi_raw = ts.translate_text(llm_input[:3000], to_language='vi', translator='google')
                provider_raw = 'google-translate'
            except Exception:
                pass

        if text_vi_raw:
            text_vi_raw = clean_gemini_output(text_vi_raw)
            # Hán-Việt normalization (local, no API)
            global _hanviet_glossary
            if _hanviet_glossary is None:
                _hanviet_glossary = hanviet_load_glossary()
            text_vi_raw = hanviet_normalize(text_vi_raw, _hanviet_glossary)

        # 5) Stage 2: Tóm lược 3–5 câu from raw (always runs regardless of provider)
        text_vi_clean = None
        if text_vi_raw:
            # Try Gemini summarization first
            summary_prompt = f"""Dưới đây là bản dịch/tóm tắt tiếng Việt của một đoạn trích CBETA:

{text_vi_raw}

Hãy tóm tắt lại thành một đoạn 3–5 câu tiếng Việt mạch lạc, rõ ràng, hướng tới độc giả phổ thông.
Giữ nguyên các tên Hán-Việt (như chùa, người, địa danh).
Chỉ tường thuật khách quan, không thêm bình luận."""
            text_vi_clean = _call_gemini(summary_prompt, timeout=10)
            if text_vi_clean:
                text_vi_clean = hanviet_normalize(text_vi_clean, _hanviet_glossary)
            else:
                # Non-Gemini fallback: extractive summary + lexicon fixes + normalize
                text_vi_clean = _polish_fallback(text_vi_raw, han_text)

        # 6) Cache both
        polished_result = None
        if text_vi_raw or text_vi_clean:
            conn = get_db_connection()
            try:
                conn.execute(
                    f"""UPDATE {CBETA_REF_TABLE}
                        SET vi_summary_raw = ?, vi_summary_clean = ?,
                            vi_summary = COALESCE(?, vi_summary),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ref_code = ?""",
                    (text_vi_raw or '', text_vi_clean or '', text_vi_clean or '', ref)
                )
                conn.commit()
            finally:
                conn.close()

            # 7) "Dịch mượt" — polish the raw text using improve_grammar + normalize_terms
            try:
                step1 = improve_grammar(text_vi_raw or '', han_text)
                corrected = step1.get('corrected_text', text_vi_raw or '')
                uncertain = step1.get('uncertain_terms', [])
                step2 = normalize_terms(corrected, uncertain)
                polished_result = {
                    'polishedText': step2['correctedText'],
                    'uncertainMappings': [m for m in step2['mappings'] if m['confidence'] < 0.9],
                    'metadata': {
                        'termsReplaced': sum(1 for m in step2['mappings'] if m['confidence'] >= 0.9),
                        'termsUncertain': sum(1 for m in step2['mappings'] if m['confidence'] >= 0.7 and m['confidence'] < 0.9),
                        'termsManual': sum(1 for m in step2['mappings'] if m['confidence'] < 0.7),
                    }
                }
            except Exception:
                pass

            resp = {
                "ok": True, "success": True,
                "vi_summary_clean": text_vi_clean or '',
                "vi_summary_raw": text_vi_raw or '',
                "sigla": sigla, "title": title,
                "provider": provider_raw,
            }
            if polished_result:
                resp['polished'] = polished_result
            return jsonify(resp)

        return jsonify({"ok": False, "success": False, "error": "translate_failed", "message": "Không thể dịch đoạn CBETA này"})

    except Exception as e:
        import traceback
        app.logger.error(f"translate_gemini_cbeta error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "success": False, "error": "internal_error", "message": str(e)})




# ── Non-LLM helpers (used when Gemini is unavailable) ─────────────────

def _extractive_summarize(text, max_sentences=5):
    """Score sentences by info density + position, pick top N, keep original order.
    Works without any LLM."""
    if not text:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 10]
    if not sentences:
        return text[:2000]
    if len(sentences) <= max_sentences:
        return ' '.join(sentences)
    cjk = re.compile(r'[\u4e00-\u9fff]')
    scored = []
    for i, s in enumerate(sentences):
        cjk_count = len(cjk.findall(s))
        # Score: length + CJK info density + position bonus
        score = len(s) + cjk_count * 3 + max(0, 50 - i)
        scored.append((score, i, s))
    scored.sort(key=lambda x: -x[0])
    top = sorted([item[1] for item in scored[:max_sentences]])
    return ' '.join(sentences[i] for i in top)




def _apply_lexicon_fixes(text, han_text):
    """Replace leftover Chinese chars + correct known names from lexicon.
    Uses build_name_map to find Hán-Việt mappings present in han_text."""
    if not text or not han_text:
        return text
    name_map = build_name_map(han_text)
    if not name_map:
        return text
    result = text
    # 1. Replace remaining CJK chars that match lexicon keys
    for zh, vi in name_map.items():
        if zh in result:
            result = result.replace(zh, vi)
    # 2. Scan for English/pinyin fragments near known names.
    #    For each (zh→vi) pair, check if any word in result is a fuzzy
    #    match for the pinyin-initial or wrong Vietnamese of that name.
    #    Only run when rapidfuzz is available.
    try:
        from rapidfuzz import fuzz
        words = re.findall(r'\b[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơỳỵỷỹý\']+\b', result)
        for zh, vi in name_map.items():
            # Try matching each word against known variants
            for w in words:
                # If word looks like pinyin (short, no diacritics)
                if re.match(r'^[a-zA-Z]{2,12}$', w):
                    r = fuzz.ratio(w.lower(), vi.lower())
                    if r > 70:
                        result = result.replace(w, vi)
                        break
    except Exception:
        pass
    return result




def _polish_fallback(text, han_text):
    """Full non-Gemini polish pipeline used when Gemini is unavailable.
    Order: extractive_summarize → lexicon_fixes → hanviet_normalize."""
    if not text:
        return text
    # 1. Extractive summary (remove fragments, keep best sentences)
    result = _extractive_summarize(text)
    # 2. Fix names using lexicon
    result = _apply_lexicon_fixes(result, han_text)
    # 3. Hán-Việt normalization
    global _hanviet_glossary
    if _hanviet_glossary is None:
        _hanviet_glossary = hanviet_load_glossary()
    result = hanviet_normalize(result, _hanviet_glossary)
    # 4. Clean up repeated words and common artifacts
    result = re.sub(r'\b(\w+)\s+\1\b', r'\1', result)  # "là là" → "là"
    result = re.sub(r'\s+', ' ', result).strip()
    # 5. Ensure proper ending
    if result and not result[-1] in '.!?':
        result += '.'
    return result




# ── "DỊCH MƯỢT" — Polish translation module ──────────────────────────────

def improve_grammar(raw_text, han_source):
    """Step 1: LLM grammar correction + extract uncertain terms.
    Returns dict with {corrected_text, uncertain_terms}.
    Falls back to hanviet_normalize + empty uncertain_terms if Gemini unavailable."""
    from hanviet_normalization import normalize_text as hv_normalize, load_glossary as hv_glossary
    prompt = f"""Bạn là chuyên gia biên tập văn bản Phật học tiếng Việt.

NGUỒN HÁN (CBETA):
{han_source[:800]}

BẢN DỊCH THÔ (cần sửa):
{raw_text}

YÊU CẦU:
1. Sửa lỗi ngữ pháp, cú pháp tiếng Việt (ví dụ: "Thả Kinh Đà ra" → "Thích Kinh Đà").
2. Loại bỏ thuật ngữ máy móc (ví dụ: "hạt nhân nhỏ và lớn" → "việc lớn nhỏ").
3. Đánh dấu các tên riêng (nhân danh, địa danh) chưa chắc bằng {{{{TERM:tên}}}}
4. KHÔNG thêm/bớt thông tin so với bản gốc.
5. Giữ nguyên tên Hán-Việt đã đúng (Thiếu Lâm Tự, Cối Kê, v.v.)

TRẢ VỀ JSON (không markdown, chỉ raw JSON):
{{"corrected_text": "...", "uncertain_terms": ["tên1", "tên2"]}}"""

    try:
        text = _call_gemini(prompt, timeout=15)
        if text:
            text = clean_gemini_output(text)
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            result = json.loads(text)
            if isinstance(result, dict) and 'corrected_text' in result:
                return result
    except Exception:
        pass
    # Fallback: run full non-Gemini polish pipeline
    return {'corrected_text': _polish_fallback(raw_text, han_source), 'uncertain_terms': []}




def normalize_terms(text, uncertain_terms):
    """Step 2: Query lexicon with exact + fuzzy matching for each uncertain term.
    Uses name_vi_map (persons) + namevi_map_places (places) + lexicon table.
    Returns dict with {correctedText, mappings}."""
    from rapidfuzz import fuzz
    conn = get_db_connection()
    mappings = []
    text_result = text

    # Build candidate list from lexicon tables
    candidates = []
    try:
        person_rows = conn.execute(
            "SELECT name_zh, name_vi FROM name_vi_map WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in person_rows:
            candidates.append({'han': r['name_zh'], 'viet': r['name_vi'], 'type': 'person'})

        place_rows = conn.execute(
            "SELECT name_zh, name_vi FROM namevi_map_places WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in place_rows:
            candidates.append({'han': r['name_zh'], 'viet': r['name_vi'], 'type': 'place'})
    finally:
        conn.close()

    # Also add built-in English→Hán-Việt mappings from normalization module
    try:
        # Import the fixed glossary for additional matching
        import importlib
        hv_mod = importlib.import_module('hanviet_normalization')
        for k, v in hv_mod.FIXED_GLOSSARY_EN.items():
            if len(k) >= 3:
                candidates.append({'han': k, 'viet': v, 'type': 'builtin_en'})
        for k, v in hv_mod.FIXED_GLOSSARY_VI.items():
            if len(k) >= 3:
                candidates.append({'han': k, 'viet': v, 'type': 'builtin_vi'})
    except Exception:
        pass

    for term in uncertain_terms:
        # Exact match first
        exact = None
        for c in candidates:
            if term.lower() == c['viet'].lower() or term.lower() == c['han'].lower():
                exact = c
                break
        if exact:
            mappings.append({
                'original': term,
                'normalized': exact['viet'],
                'han': exact['han'],
                'confidence': 1.0,
                'source': 'exact'
            })
            text_result = text_result.replace(f'{{{{TERM:{term}}}}}', f"{exact['viet']} ({exact['han']})")
            continue

        # Fuzzy match
        scored = []
        for c in candidates:
            score = fuzz.ratio(term.lower(), c['viet'].lower()) / 100.0
            if score > 0.7:
                scored.append({'han': c['han'], 'viet': c['viet'], 'confidence': score})
            score2 = fuzz.ratio(term.lower(), c['han'].lower()) / 100.0
            if score2 > 0.7:
                scored.append({'han': c['han'], 'viet': c['viet'], 'confidence': score2})

        if scored:
            best = max(scored, key=lambda x: x['confidence'])
            confidence = best['confidence']
            mappings.append({
                'original': term,
                'normalized': best['viet'],
                'han': best['han'],
                'confidence': confidence,
                'source': 'fuzzy'
            })
            if confidence >= 0.9:
                text_result = text_result.replace(
                    f'{{{{TERM:{term}}}}}',
                    f"{best['viet']} ({best['han']})"
                )
            elif confidence >= 0.7:
                text_result = text_result.replace(
                    f'{{{{TERM:{term}}}}}',
                    f"<mark class='cbeta-uncertain' data-original='{term}' data-han='{best['han']}' data-confidence='{confidence:.2f}'>{best['viet']}</mark>"
                )
        else:
            mappings.append({
                'original': term,
                'normalized': term,
                'han': '???',
                'confidence': 0.0,
                'source': 'manual_required'
            })
            text_result = text_result.replace(
                f'{{{{TERM:{term}}}}}',
                f"<span class='cbeta-manual-edit'>{term}</span>"
            )

    # Clean up any remaining unprocessed TERM markers
    text_result = re.sub(r'\{\{TERM:([^}]+)\}\}', r'\1', text_result)

    return {'correctedText': text_result, 'mappings': mappings}




def _resolve_dila_id(conn, place_id):
    """Resolve dila_id for any place identifier. Returns (dila_id, name_zh).
    Accepts: places_dila.id directly ('PL000000023255') or places.id (integer as str).
    """
    # Case 1: place_id is already a valid places_dila.id — return directly
    # T101 BUG-001: dùng places_dila.name (tên chính thức DILA) thay vì name_zh
    # (name_zh có thể chứa tên alternative, vd 少室寺 thay vì 少林寺 cho PL000000023255)
    dila_row = conn.execute("SELECT name, name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
    if dila_row:
        return place_id, dila_row['name'] or dila_row['name_zh']

    # Case 2: place_id is places.id (integer primary key) — find via namevi_map
    row = conn.execute("SELECT name_zh FROM places WHERE id = ?", (place_id,)).fetchone()
    if not row:
        return None, None
    name_zh = row['name_zh']
    nm = conn.execute(
        "SELECT dila_id FROM namevi_map_places WHERE name_zh = ? AND dila_id IS NOT NULL ORDER BY (vn_name_status='reviewed') DESC, (source='manual') DESC, confidence DESC LIMIT 1",
        (name_zh,)
    ).fetchone()
    if not nm:
        return None, name_zh
    dila_id = nm['dila_id']
    # Expand short DILA IDs (PL023255 → PL000000023255) if needed
    check = conn.execute("SELECT id FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
    if not check and dila_id.startswith('PL'):
        padded = 'PL' + dila_id[2:].zfill(12)
        if conn.execute("SELECT id FROM places_dila WHERE id = ? LIMIT 1", (padded,)).fetchone():
            dila_id = padded
    return dila_id, name_zh




_BUDDHIST_SYSTEM_PROMPT = """Bạn là dịch giả Hán-Việt chuyên về văn học Phật giáo Bắc Tông Việt Nam.
Quy tắc bắt buộc:
- Tăng nhân: 釋X → Thích X (KHÔNG phiên âm pinyin)
- Địa danh: dùng âm Hán-Việt (雍州→Ung Châu, 嵩山→Tung Sơn, 河南→Hà Nam)
- Thuật ngữ cố định: 舍利→xá-lợi, 菩薩→Bồ Tát, 禪→Thiền, 涅槃→Niết-bàn, 比丘→Tỳ-kheo
- 下流 trong văn ngôn = chảy xuống hạ lưu (KHÔNG phải "tục tĩu")
- Giữ tên kinh điển bằng Hán-Việt (大藏經→Đại Tạng Kinh, 高僧傳→Cao Tăng Truyện)
- Văn phong: tự nhiên, chuẩn văn học Phật giáo Việt Nam, không dịch từng chữ
- Chỉ dịch, không giải thích hay chú thích"""




# ── T55b Related Texts (Trích Dẫn Tự Động) ─────────────────────────────
# Batch F (2026-09-10) — additive, read-only endpoint, 0 bảng mới, 0 ALTER.
# Group 1 = crossref (SAT / Toh / Pali) · Group 2 = topic (co-mentioned texts
# qua DILA persons · verified 72,628 rows) · Group 3 = persons xuất hiện.
# KHÔNG ghi đè "Kinh Điển Liên Quan" `/api/places/<id>/cbeta` — endpoint mới độc lập.

def _t55_normalize_sigla(raw):
    """Trả tuple (short_key, text_num): 'T50n2059' → ('T2059','2059') · 'T0251' → ('T0251','251') · 'X77n1524' → ('X1524','1524')."""
    s = (raw or '').strip()
    m = re.match(r'(T|X)\s*(\d+)n(\d+)', s, re.I)
    if m:
        return ('{}{:04d}'.format(m.group(1).upper(), int(m.group(3))), str(int(m.group(3))))
    m2 = re.match(r'(T|X)\s*0*(\d+)', s, re.I)
    if m2:
        return ('{}{:04d}'.format(m2.group(1).upper(), int(m2.group(2))), str(int(m2.group(2))))
    return (s.upper(), None)




# ── T86 — Truyền Thừa (Lineage Research Workspace) ────────────────────────────────
# Redesign tab TRUYỀN THỪA thành workspace 3 cột (sidebar / tree canvas / inspector +
# evidence drawer). Dữ liệu 100% thật từ Marcus SNA (marcus_networks qua bridge
# marcus_people_link ↔ people), KHÔNG bịa. Hai endpoint mới:
#   1) GET /daoanh/api/monk/<dila_id>/lineage-tree  — cây phả hệ đệ quy (n tầng thầy/trò,
#      lazy mở sâu hơn), mỗi edge mang citation ref thật + has_ref (proxy dẫn chứng).
#   2) GET /daoanh/api/lineage-ref/passage          — resolve chuỗi dẫn chiếu CBETA → passage
#      (mở Đọc trong Đại Tạng), trung thực null nếu passage chưa được lập chỉ mục.
import re as _re86


import threading as _t148_threading


import xml.etree.ElementTree as _t148_ET



# T148: Lazy index toàn bộ DILA Person Authority XML vào RAM (chạy lần đầu, ~3-5s)
_T148_DILA_EXTRA = {}           # pid → {bio_extensive, alt_names, listbibl, works_tripitaka, works_by, mentioned_in, active_at,


                                #         name_latin, occupation, place_of_origin, birth_death_quote, wikidata_id, birth_date, death_date, death_note}
_T148_EXTRA_LOADED = False


_T148_EXTRA_LOCK = _t148_threading.Lock()


_T148_PERSON_XML = os.path.join(
    os.path.dirname(__file__),
    'data', 'dila_import', 'Authority-Databases', 'authority_person',
    'Buddhist_Studies_Person_Authority.xml'
)


_T148_NS = 'http://www.tei-c.org/ns/1.0'


_T148_XML_NS = 'http://www.w3.org/XML/1998/namespace'




def _t148_load_dila_extra():
    """Parse DILA Person Authority XML từ DB (ttl_v2_source_records.raw_text),
    lưu vào _T148_DILA_EXTRA. Mỗi person ID có thể có nhiều XML records → merge."""
    global _T148_DILA_EXTRA, _T148_EXTRA_LOADED
    with _T148_EXTRA_LOCK:
        if _T148_EXTRA_LOADED:
            return
        idx = {}
        ns = _T148_NS
        xml_ns = _T148_XML_NS
        try:
            t0 = time.time()
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            # Query tất cả raw XML DILA từ DB
            rows = conn.execute(
                "SELECT id, raw_text FROM ttl_v2_source_records WHERE kind='DILA_XML' AND raw_text IS NOT NULL"
            ).fetchall()
            conn.close()
            print(f'[T148] Queried {len(rows)} DILA_XML records from DB', flush=True)

            for row in rows:
                rec_id, xml_text = row['id'], row['raw_text']
                if not xml_text or not isinstance(xml_text, str):
                    continue
                try:
                    # Parse XML string (không parse từ file)
                    root = _t148_ET.fromstring(xml_text)
                except Exception as ex:
                    print(f'[T148] Parse error in record {rec_id}: {ex}', flush=True)
                    continue

                # Iterate persons trong XML này
                for elem in root.iter(f'{{{ns}}}person'):
                    pid = elem.get(f'{{{xml_ns}}}id') or elem.get('xml:id')
                    if not pid:
                        continue
                    # Init data fields (hoặc merge nếu pid đã có)
                    existing = idx.get(pid, {})
                    alt_names = list(existing.get('alt_names', []))
                    listbibl = list(existing.get('listbibl', []))
                    listbibl_items = list(existing.get('listbibl_items', []))
                    bio_extensive = existing.get('bio_extensive')
                    works_tripitaka = existing.get('works_tripitaka')
                    works_by = existing.get('works_by')
                    secondary_lit = existing.get('secondary_lit')
                    mentioned_in = existing.get('mentioned_in')
                    mentioned_in_refs = list(existing.get('mentioned_in_refs', []))
                    active_at = existing.get('active_at')
                    name_latin = existing.get('name_latin')
                    occupation = existing.get('occupation')
                    place_of_origin = existing.get('place_of_origin')
                    birth_death_quote = existing.get('birth_death_quote')
                    wikidata_id = existing.get('wikidata_id')
                    wikidata_ids = list(existing.get('wikidata_ids', []))
                    birth_date = existing.get('birth_date')
                    death_date = existing.get('death_date')
                    death_note = existing.get('death_note')
                    relations = list(existing.get('relations', []))
                    sex_val = existing.get('sex')
                    dynasty_xml = existing.get('dynasty_xml')
                    is_monk = existing.get('is_monk')

                    for child in elem:
                        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        if tag == 'persName':
                            ptype = child.get('type', '')
                            lang = child.get(f'{{{xml_ns}}}lang', '')
                            txt = (child.text or '').strip()
                            if ptype == 'alternative' and txt:
                                alt_names.append(txt)
                            elif not ptype and lang and lang not in ('zho-Hant', 'vie') and txt and not name_latin:
                                name_latin = txt
                        elif tag == 'listBibl':
                            for bibl in child:
                                t = (bibl.text or '').strip()
                                ref_url = ''
                                ref_el = bibl.find(f'{{{ns}}}ref')
                                if ref_el is not None:
                                    ref_url = (ref_el.get('target') or '').strip()
                                    if not t:
                                        t = (ref_el.text or '').strip()
                                if t:
                                    listbibl.append(t)
                                    # T372 (2026-10-13): giữ song song url từ <ref target=...>
                                    # để renderer dựng <a href>; listbibl (plain text) giữ
                                    # nguyên format cũ cho AI-translate prompt (dila_translate).
                                    listbibl_items.append({'text': t, 'url': ref_url})
                        elif tag == 'note':
                            ntype = child.get('type', '')
                            txt = (child.text or '').strip()
                            if ntype == 'extensive' and txt:
                                bio_extensive = txt
                            elif ntype == 'worksInTripitaka' and txt:
                                works_tripitaka = txt
                            elif ntype == 'worksBy' and txt:
                                works_by = txt
                            elif ntype == 'secondaryLit' and txt:
                                secondary_lit = txt
                            elif ntype == 'mentionedIn':
                                refs = []
                                if txt:
                                    refs.append({'text': txt, 'url': ''})
                                for ref_el in child.findall(f'{{{ns}}}ref'):
                                    ref_text = (ref_el.text or '').strip()
                                    ref_url = (ref_el.get('target') or '').strip()
                                    if ref_text:
                                        refs.append({'text': ref_text, 'url': ref_url})
                                if refs:
                                    mentioned_in = '\n'.join(r['text'] for r in refs)
                                    mentioned_in_refs = refs
                            elif ntype == 'activeAt' and txt:
                                active_at = txt
                            elif ntype == 'birthDeathDateQuote' and txt:
                                birth_death_quote = txt
                            elif ntype == 'dynasty' and txt:
                                dynasty_xml = txt
                            elif ntype == 'monk' and txt:
                                is_monk = txt
                            elif ntype == 'placeOfOrigin':
                                pl_el = child.find(f'{{{ns}}}placeName')
                                if pl_el is not None:
                                    pl_txt = (pl_el.text or '').strip()
                                    if pl_txt:
                                        place_of_origin = pl_txt
                        elif tag == 'occupation':
                            txt = (child.text or '').strip()
                            if txt and not occupation:
                                occupation = txt
                        elif tag == 'birth':
                            txt = (child.text or '').strip()
                            if txt:
                                birth_date = txt
                        elif tag == 'death':
                            txt = (child.text or '').strip()
                            if txt:
                                death_date = txt
                            dn_el = child.find(f'{{{ns}}}note')
                            if dn_el is not None:
                                dn = (dn_el.text or '').strip()
                                if dn:
                                    death_note = dn
                        elif tag == 'idno' and child.get('type') == 'Wikidata':
                            txt = (child.text or '').strip()
                            if txt:
                                # T372: XML có thể có nhiều <idno type="Wikidata">
                                # (vd A000074 có 2 QID) — giữ wikidata_id (tương thích
                                # cũ, QID đầu tiên) VÀ wikidata_ids (đủ danh sách).
                                if not wikidata_id:
                                    wikidata_id = txt
                                if txt not in wikidata_ids:
                                    wikidata_ids.append(txt)
                        elif tag == 'sex':
                            sv = child.get('value', '').strip()
                            if sv == '1':
                                sex_val = 'Nam'
                            elif sv == '2':
                                sex_val = 'Nữ'
                            elif sv:
                                sex_val = sv
                        elif tag == 'listRelation':
                            for rel in child:
                                rel_tag = rel.tag.split('}')[-1] if '}' in rel.tag else rel.tag
                                if rel_tag != 'relation':
                                    continue
                                rel_type = rel.get('type', '')
                                active   = rel.get('active', '')
                                name_n   = rel.get('n', '')
                                bibl_text = ''
                                ref_url   = ''
                                desc_el = rel.find(f'{{{ns}}}desc')
                                if desc_el is not None:
                                    bibl_el = desc_el.find(f'{{{ns}}}bibl')
                                    if bibl_el is not None:
                                        bibl_text = (bibl_el.text or '').strip()
                                    ref_el = desc_el.find(f'{{{ns}}}ref')
                                    if ref_el is not None:
                                        ref_url = ref_el.get('target', '') or (ref_el.text or '').strip()
                                if rel_type and active:
                                    relations.append({
                                        'type': rel_type,
                                        'person_id': active,
                                        'name': name_n,
                                        'bibl': bibl_text,
                                        'ref_url': ref_url,
                                    })

                    has_data = (bio_extensive or alt_names or listbibl or works_tripitaka or works_by
                                or secondary_lit or mentioned_in or active_at or name_latin or occupation
                                or place_of_origin or birth_death_quote or wikidata_id
                                or birth_date or death_date or relations or sex_val
                                or dynasty_xml or is_monk)
                    if has_data:
                        idx[pid] = {
                            'bio_extensive': bio_extensive,
                            'alt_names': alt_names,
                            'sex': sex_val,
                            'listbibl': listbibl,
                            'listbibl_items': listbibl_items,
                            'works_tripitaka': works_tripitaka,
                            'works_by': works_by,
                            'secondary_lit': secondary_lit,
                            'mentioned_in': mentioned_in,
                            'mentioned_in_refs': mentioned_in_refs,
                            'active_at': active_at,
                            'name_latin': name_latin,
                            'occupation': occupation,
                            'place_of_origin': place_of_origin,
                            'birth_death_quote': birth_death_quote,
                            'wikidata_id': wikidata_id,
                            'wikidata_ids': wikidata_ids,
                            'birth_date': birth_date,
                            'death_date': death_date,
                            'death_note': death_note,
                            'relations': relations,
                            'dynasty_xml': dynasty_xml,
                            'is_monk': is_monk,
                        }

            _T148_DILA_EXTRA = idx
            elapsed = time.time() - t0
            print(f'[T148] Đã index {len(idx)} persons từ DILA XML DB trong {elapsed:.1f}s', flush=True)
        except Exception as ex:
            _T148_DILA_EXTRA = idx
            print(f'[T148] Lỗi parse DILA XML từ DB tại ~{len(idx)} persons: {ex}', flush=True)
        finally:
            _T148_EXTRA_LOADED = True




def _t148_get_extra(pid):
    """Trả về extra DILA data cho một person id (load lazily)."""
    if not _T148_EXTRA_LOADED:
        _t148_load_dila_extra()
    return _T148_DILA_EXTRA.get(pid) or {}




def _t86_person_info(conn, pid):
    """Tên/niên hiệu/tông phái/môn phái cho một node lineage.
    Ưu tiên marcus_reference → people (DILA) → ttl_persons (T186 danh tăng VN local)."""
    marc = conn.execute(
        "SELECT label, label_vi, birth_year, death_year FROM marcus_reference WHERE node_id = ?",
        (pid,)
    ).fetchone()
    person = conn.execute(
        "SELECT name_zh, name_vi, dynasty, sect, bio FROM people WHERE id = ?", (pid,)
    ).fetchone()
    # T186: fallback sang ttl_persons nếu không có trong DILA
    ttl_person = None
    if not person:
        try:
            ttl_person = conn.execute(
                "SELECT name_vi, name_zh, note FROM ttl_persons WHERE id = ?", (pid,)
            ).fetchone()
        except sqlite3.OperationalError as e:
            if 'no such table' not in str(e).lower():
                raise
            # ttl_persons table doesn't exist - ignore silently
            pass
    zh = (marc['label'] if marc and marc['label'] else None) \
        or (person['name_zh'] if person else None) \
        or (ttl_person['name_zh'] if ttl_person else None) or pid
    vi = None
    if marc and marc['label_vi'] and marc['label_vi'] != zh:
        vi = marc['label_vi']
    elif person and person['name_vi']:
        vi = person['name_vi']
    elif ttl_person and ttl_person['name_vi']:
        vi = ttl_person['name_vi']
    vi = vi or zh
    # source_type giúp UI hiển thị badge "Danh tăng VN – TTL local"
    source_type = 'ttl_local' if ttl_person else 'dila'
    return {
        "id": pid,
        "name_vi": vi,
        "name_zh": zh,
        "dynasty": person['dynasty'] if person else None,
        "sect": person['sect'] if person else None,
        "birth_year": (marc['birth_year'] if marc else None),
        "death_year": (marc['death_year'] if marc else None),
        "bio": (person['bio'] if person else None) or
               (ttl_person['note'] if ttl_person else None) or None,
        "source_type": source_type,
    }




def _t86_neighbors(conn, person_id, direction):
    """Lấy neighbors của một person theo marcus_networks (thầy/trò).
    direction: 'up' = thầy (student_id=person), 'down' = trò (teacher_id=person).
    Mọi marcus node id đều ánh xạ ngược qua marcus_people_link → person DILA (nếu có)."""
    link = conn.execute(
        "SELECT marcus_node_id FROM marcus_people_link WHERE person_id = ?", (person_id,)
    ).fetchone()
    if not link:
        return [], 0
    nid = link['marcus_node_id']
    rows = []
    if direction == 'up':
        rows = conn.execute(
            "SELECT teacher_id AS id, ref FROM marcus_networks WHERE student_id = ?", (nid,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT student_id AS id, ref FROM marcus_networks WHERE teacher_id = ?", (nid,)
        ).fetchall()
    # Map marcus node id → person DILA id (node id == person id trong dataset này,
    # nhưng vẫn resolve qua bridge cho chắc).
    out = []
    for r in rows:
        nbr = conn.execute(
            "SELECT person_id FROM marcus_people_link WHERE marcus_node_id = ?", (r['id'],)
        ).fetchone()
        pid = (nbr['person_id'] if nbr else r['id'])
        out.append({"id": pid, "ref": r['ref']})
    return out, len(rows)




def _t158_neighbors_consensus(conn, person_id, direction, include_single=False):
    """T158 — Lấy neighbors từ lineage_edge_consensus thay vì marcus_networks.
    direction: 'up' = thầy (person là trò), 'down' = trò (person là thầy).
    include_single: True → bao gồm cả single_source edges (cho optional filter).
    T187: LEFT JOIN lineage_primary_teacher để thêm is_primary vào kết quả.
    direction='up' ORDER BY is_primary DESC, ttl_asserted DESC, agreeing_source_count DESC
    → thầy truyền pháp ấn luôn đứng đầu, thầy tham học (is_primary=-1) xếp cuối.
    """
    vis_cond = "1" if include_single else "c.is_default_visible=1"
    if direction == 'up':
        sql = (
            "SELECT c.teacher_id AS id, c.source_badge, c.agreeing_source_count,"
            " c.dila_asserted, c.marcus_asserted, c.ttl_asserted,"
            " c.consensus_status, c.is_default_visible,"
            " COALESCE(lpt.is_primary, 0) AS is_primary,"
            " lpt.evidence_source AS pt_evidence, lpt.confidence AS pt_confidence"
            " FROM lineage_edge_consensus c"
            " LEFT JOIN lineage_primary_teacher lpt"
            "   ON lpt.teacher_id=c.teacher_id AND lpt.disciple_id=c.disciple_id"
            f" WHERE c.disciple_id=? AND c.relation_type='dharma_transmission' AND {vis_cond}"
            " ORDER BY COALESCE(lpt.is_primary,0) DESC, c.ttl_asserted DESC, c.agreeing_source_count DESC"
        )
    else:
        sql = (
            "SELECT c.disciple_id AS id, c.source_badge, c.agreeing_source_count,"
            " c.dila_asserted, c.marcus_asserted, c.ttl_asserted,"
            " c.consensus_status, c.is_default_visible,"
            " COALESCE(lpt.is_primary, 0) AS is_primary,"
            " lpt.evidence_source AS pt_evidence, lpt.confidence AS pt_confidence"
            " FROM lineage_edge_consensus c"
            " LEFT JOIN lineage_primary_teacher lpt"
            "   ON lpt.teacher_id=c.teacher_id AND lpt.disciple_id=c.disciple_id"
            f" WHERE c.teacher_id=? AND c.relation_type='dharma_transmission' AND {vis_cond}"
            " ORDER BY c.agreeing_source_count DESC, c.disciple_id"
        )
    rows = conn.execute(sql, (person_id,)).fetchall()
    return [dict(r) for r in rows], len(rows)




def _t426_neighbors_view(conn, person_id, direction, view_name):
    """T426 — Lấy neighbors từ VIEW T425 (v_tree_dila/marcus/ttl/overlay).
    direction: 'up' = thầy (person là trò), 'down' = trò (person là thầy).
    view_name: 'dila', 'marcus', 'ttl', 'overlay'.
    Không có is_primary (VIEW không join lineage_primary_teacher).
    """
    if view_name not in ('dila', 'marcus', 'ttl', 'overlay'):
        return [], 0

    if view_name == 'overlay':
        # v_tree_overlay dùng teacher_id/disciple_id, đã GROUP BY
        if direction == 'up':
            sql = (
                "SELECT teacher_id AS id, '' AS source_badge, n_sources AS agreeing_source_count,"
                " 1 AS is_primary"
                " FROM v_tree_overlay"
                " WHERE disciple_id=?"
                " ORDER BY n_sources DESC, teacher_id"
            )
        else:
            sql = (
                "SELECT disciple_id AS id, '' AS source_badge, n_sources AS agreeing_source_count,"
                " 1 AS is_primary"
                " FROM v_tree_overlay"
                " WHERE teacher_id=?"
                " ORDER BY n_sources DESC, disciple_id"
            )
    else:
        # v_tree_dila/marcus/ttl dùng subject_person_id/object_person_id
        view = f"v_tree_{view_name}"
        if direction == 'up':
            sql = (
                f"SELECT subject_person_id AS id, source_code AS source_badge,"
                f" 1 AS agreeing_source_count, 1 AS is_primary"
                f" FROM {view}"
                f" WHERE object_person_id=?"
                f" ORDER BY subject_person_id"
            )
        else:
            sql = (
                f"SELECT object_person_id AS id, source_code AS source_badge,"
                f" 1 AS agreeing_source_count, 1 AS is_primary"
                f" FROM {view}"
                f" WHERE subject_person_id=?"
                f" ORDER BY object_person_id"
            )
    rows = conn.execute(sql, (person_id,)).fetchall()
    return [dict(r) for r in rows], len(rows)




def _t86_person_conflict(conn, person_id):
    """Real conflict marker từ lineage_conflicts_v2 (sai lệch DILA vs Marcus về
    tập thầy/trò). Chỉ đánh dấu khi is_conflict=1 — không bịa.
    issue_category: 'source_coverage_gap' (một bên=0 hoặc có overlap) vs
    'direction_disagreement' (cả hai>0, không overlap — mâu thuẫn thật)."""
    import json as _json
    rows = conn.execute(
        "SELECT conflict_type, notes, dila_count, marcus_count, dila_data, marcus_data "
        "FROM lineage_conflicts_v2 WHERE person_id=? AND is_conflict=1 AND resolved=0",
        (person_id,)
    ).fetchall()
    result = []
    for r in rows:
        dc = r['dila_count'] or 0
        mc = r['marcus_count'] or 0
        dila_ids, marcus_ids = [], []
        try:
            dila_ids = list(_json.loads(r['dila_data'] or '[]'))
            marcus_ids = list(_json.loads(r['marcus_data'] or '[]'))
        except Exception:
            pass
        if dc == 0 or mc == 0:
            category, severity = 'source_coverage_gap', 'info'
        else:
            if set(dila_ids) & set(marcus_ids):
                category, severity = 'source_coverage_gap', 'info'
            else:
                category, severity = 'direction_disagreement', 'warning'
        result.append({
            "conflict_type": r['conflict_type'],
            "note": r['notes'],
            "dila_count": dc,
            "marcus_count": mc,
            "dila_ids": dila_ids,
            "marcus_ids": marcus_ids,
            "issue_category": category,
            "severity": severity,
        })
    return result




def _t138_edge_assertions(conn, subject_id, object_id):
    """T138 — các source assertion độc lập của 1 cạnh truyền thừa (subject→object)
    từ bảng DERIVED lineage_edge_assertions. Trả về [ {source_code, raw_relation_type,
    ref, mapping_verified, trust_level, status, direction_mismatch}, ... ] + trust_level
    tổng (max theo thứ tự L1>L2>L3>L4). Không có assertion nào → sources rỗng, trust_level None.
    Kiểm tra HAI chiều: forward (sub→obj) + reversed (obj→sub). Assertion tìm thấy
    ở chiều ngược (DILA lưu student→teacher, Marcus teacher→student) được gắn
    direction_mismatch=True và KHÔNG contribute vào trust_level (đây là conflict,
    không phải confirmation)."""
    order = {'L1': 4, 'L2': 3, 'L3': 2, 'L4': 1}
    inv = {v: k for k, v in order.items()}

    # Forward direction (same as Marcus convention)
    rows_fwd = conn.execute(
        "SELECT source_code, raw_relation_type, ref, mapping_verified, trust_level, status "
        "FROM lineage_edge_assertions WHERE subject_person_id=? AND object_person_id=? "
        "AND status!='rejected' ORDER BY source_code", (subject_id, object_id)
    ).fetchall()

    # Reversed direction (DILA stores student→teacher, flipped)
    rows_rev = conn.execute(
        "SELECT source_code, raw_relation_type, ref, mapping_verified, trust_level, status "
        "FROM lineage_edge_assertions WHERE subject_person_id=? AND object_person_id=? "
        "AND status!='rejected' ORDER BY source_code", (object_id, subject_id)
    ).fetchall()

    if not rows_fwd and not rows_rev:
        return {'sources': [], 'trust_level': None, 'rejected': False}

    seen = set()
    sources = []
    best = 0
    for r in rows_fwd:
        sd = r['source_code']
        if sd in seen:
            continue
        seen.add(sd)
        sources.append({
            'source_code': sd,
            'raw_relation_type': r['raw_relation_type'],
            'ref': r['ref'],
            'mapping_verified': bool(r['mapping_verified']),
            'trust_level': r['trust_level'],
            'status': r['status'] or 'active',
            'direction_mismatch': False,
        })
        lv = order.get(r['trust_level'], 0)
        if lv > best:
            best = lv

    for r in rows_rev:
        sd = r['source_code']
        if sd in seen:
            continue
        seen.add(sd)
        sources.append({
            'source_code': sd,
            'raw_relation_type': r['raw_relation_type'],
            'ref': r['ref'],
            'mapping_verified': bool(r['mapping_verified']),
            'trust_level': r['trust_level'],
            'status': r['status'] or 'active',
            'direction_mismatch': True,
        })
        # direction_mismatch: KHÔNG contribute vào trust_level
        # (DILA says opposite direction = conflict, not confirmation)

    is_rej = bool(conn.execute(
        "SELECT 1 FROM lineage_edge_assertions WHERE subject_person_id=? AND object_person_id=? "
        "AND status='rejected' LIMIT 1", (subject_id, object_id)).fetchone())
    return {
        'sources': sources,
        'trust_level': inv.get(best),
        'rejected': is_rej,
    }




def _t86_normalize_place_id(place_id):
    """DILA long format PL000000024672 → places table short format PL024672."""
    if place_id and place_id.startswith('PL') and len(place_id) > 8:
        try:
            return 'PL{:06d}'.format(int(place_id[2:]))
        except ValueError:
            pass
    return place_id




def _t86_resolve_display_name(conn, person_id: str, node: dict | None = None) -> dict:
    """Resolve preferred display name for a person.

    Precedence (spec Phase 5):
      1. TTL verified_direct preferred Vi display name (person_display_names)
      2. TTL verified_crosswalk preferred Vi display name (person_display_names)
      3. vn_person_authority canonical 4-char Vi name (mapped by dila_id)
      4. DILA/Marcus authority name (node.name_vi or people.name_vi) + name_zh
      5. name_zh only
      6. person_id as safe fallback

    Returns structured dict — never mutates node.
    """
    # Try person_display_names table
    row = conn.execute(
        """SELECT display_name_vi, display_name_zh, authority_name_vi, authority_name_zh,
                  verification_status, source_file, mapping_method
           FROM person_display_names
           WHERE person_id=? AND locale='vi' AND is_preferred=1
             AND verification_status IN ('verified_direct','verified_crosswalk')
           ORDER BY CASE verification_status
               WHEN 'verified_direct'   THEN 1
               WHEN 'verified_crosswalk' THEN 2
               ELSE 3 END
           LIMIT 1""",
        (person_id,)
    ).fetchone()

    if row:
        return {
            "primary":             row[0],
            "secondary":           row[1] or "",
            "authority_primary":   row[2] or "",
            "authority_secondary": row[3] or "",
            "source_type":         "ttl",
            "source_file":         row[5] or "",
            "verification_status": row[4],
            "is_formal_name":      True,
        }

    # Try vn_person_authority — canonical 4-char Vietnamese name mapped by DILA ID.
    # Hán văn 2 chữ (無學, 天然) trong marcus_reference sẽ được ánh xạ thành tên
    # đầy đủ 4 chữ (Thúy Vi Vô Học, Đơn Hà Thiên Nhiên) nếu có trong bảng này.
    # [T200] dùng helper có ORDER BY xác định (dila_id KHÔNG unique: 33 nhóm 2–3 dòng).
    # Thứ tự ưu tiên status: verified > pending > auto_ttl > alias_*, tie-break bằng id.
    vpa = _t200_vnpa_lookup_by_dila(
        conn, person_id,
        "generation_order, dharma_lineage, biographical_note_vi",
    )
    if vpa and vpa['name_vi']:
        # T237/T238: Gate — chỉ dùng TTL name nếu admin đã xác nhận.
        # '—' trong name_vi_final = admin đánh dấu 2 vị này KHÁC NHAU → block TTL.
        # Không có admin row + status != 'verified' → cũng block (auto_ttl/alias chưa duyệt).
        _nm_row = conn.execute(
            "SELECT name_vi_final FROM name_vi_map WHERE dila_id=? AND approved_by='admin' LIMIT 1",
            (person_id,)
        ).fetchone()
        if _nm_row:
            _nm_final = (_nm_row[0] or '').strip()
            _vpa_ok = bool(_nm_final) and _nm_final != '—'
        else:
            _vpa_ok = vpa['status'] == 'verified'
        if _vpa_ok:
            return {
                "primary":              vpa['name_vi'],
                "secondary":            vpa['name_zh'] or "",
                "authority_primary":    vpa['name_vi'],
                "authority_secondary":  vpa['name_zh'] or "",
                "source_type":          "ttl",
                "source_file":          (vpa['ttl_filename'] or "") + ".ttl",
                "verification_status":  "verified_direct",
                "is_formal_name":       True,
                "generation_order":     vpa['generation_order'],
                "dharma_lineage":       vpa['dharma_lineage'] or "",
                "biographical_note_vi": vpa['biographical_note_vi'] or "",
            }

    # Fallback — use node data or people table
    auth_vi, auth_zh = "", ""
    if node:
        auth_vi = node.get("name_vi") or node.get("name") or ""
        auth_zh = node.get("name_zh") or ""
    if not auth_vi:
        prow = conn.execute(
            "SELECT name_vi, name_zh FROM people WHERE id=?", (person_id,)
        ).fetchone()
        if prow:
            auth_vi, auth_zh = prow[0] or "", prow[1] or ""

    return {
        "primary":             auth_vi or auth_zh or person_id,
        "secondary":           auth_zh if auth_vi else "",
        "authority_primary":   auth_vi,
        "authority_secondary": auth_zh,
        "source_type":         "dila",
        "source_file":         "",
        "verification_status": "authority_fallback",
        "is_formal_name":      False,
    }




# ── T412 (BUG-037, 2026-10-21): nhãn nút cây Pháp hệ = tên đầy đủ theo TTL ──────────
# Thứ tự ưu tiên tên hiển thị trên cây (lineage-tree / ancestor-spine / ancestor-path):
#   (a) rdfs:label@vi của file TTL nối với DILA ID (đọc data/ttl/, CHỈ ĐỌC, index build 1 lần/process)
#   (b) không có TTL → giữ tên phiên âm DILA/Marcus hiện có (không đổi).
# KHÔNG dùng vn_person_authority.name_vi làm tên đầy đủ (tên ngắn / gạch dưới).
# DILA ID nối >=2 file TTL KHÁC TÊN (không alias) → KHÔNG đoán: dùng tên DILA + ttl_conflict
# (tooltip "nhiều hồ sơ TTL, chờ Admin chốt"). Liệt kê trong report, không ghi DB.
import threading as _t412_threading



_T412_TTL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ttl')


_T412_LABEL_RE = re.compile(r'rdfs:label\s+"([^"]+)"@vi')


_T412_INDEX = None


_T412_INDEX_LOCK = _t412_threading.Lock()




def _t412_read_main_label(path):
    """rdfs:label@vi ĐẦU TIÊN = nhãn nhân vật chính (subject <ex:monk/...>).
    Chỉ đọc 8 KB đầu file (zero-RAM); các label sau thuộc tăng nhân liên quan."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        head = f.read(8192)
    m = _T412_LABEL_RE.search(head)
    return m.group(1).strip() if m else ''




def _t412_build_index():
    """dila_id -> {'label','ttl_file','ambiguous','files'}; chỉ tính link không-alias có file tồn tại."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT dila_id, ttl_filename FROM vn_person_authority "
            "WHERE dila_id IS NOT NULL AND dila_id!='' "
            "AND ttl_filename IS NOT NULL AND ttl_filename!='' "
            "AND COALESCE(status,'') NOT LIKE 'alias%'"
        ).fetchall()
    finally:
        conn.close()
    files_by_id = {}
    for row in rows:
        dila_id, tf = row[0], row[1]
        fn = tf if tf.endswith('.ttl') else tf + '.ttl'
        if os.path.isfile(os.path.join(_T412_TTL_DIR, fn)):
            files_by_id.setdefault(dila_id, set()).add(fn)
    index = {}
    for dila_id, files in files_by_id.items():
        labels = {}
        for fn in sorted(files):
            try:
                lbl = _t412_read_main_label(os.path.join(_T412_TTL_DIR, fn))
            except OSError:
                lbl = ''
            if lbl:
                labels[fn] = lbl
        if not labels:
            continue
        distinct = sorted(set(labels.values()))
        if len(distinct) == 1:
            index[dila_id] = {'label': distinct[0], 'ttl_file': sorted(labels)[0],
                              'ambiguous': False, 'files': sorted(labels)}
        else:
            index[dila_id] = {'label': '', 'ttl_file': '', 'ambiguous': True,
                              'files': sorted(labels)}
    return index




def _t412_get_index():
    global _T412_INDEX
    if _T412_INDEX is None:
        with _T412_INDEX_LOCK:
            if _T412_INDEX is None:
                _T412_INDEX = _t412_build_index()
    return _T412_INDEX




def _t412_resolve_display_name(conn, person_id, node=None):
    """Bọc _t86_resolve_display_name cho 3 route cây. Hàm gốc giữ nguyên cho route khác."""
    dn = dict(_t86_resolve_display_name(conn, person_id, node))
    node = node or {}
    idx = _t412_get_index().get(person_id)
    if idx and not idx['ambiguous']:
        primary = idx['label']
        if dn.get('verification_status') == 'verified_direct' and dn.get('authority_primary'):
            primary = dn['authority_primary']
        return {
            'primary': primary,
            'secondary': node.get('name_zh') or dn.get('secondary') or '',
            'authority_primary': dn.get('authority_primary', ''),
            'authority_secondary': dn.get('authority_secondary', ''),
            'source_type': 'ttl',
            'source_file': idx['ttl_file'],
            'verification_status': 'ttl_label',
            'is_formal_name': True,
            'name_source': 'TTL',
            'ttl_candidates': idx['files'],
            'ttl_conflict': [],
        }
    if idx and idx['ambiguous']:
        # Nhiều hồ sơ TTL khác tên: không đoán, dùng tên DILA/Marcus phiên âm.
        return {
            'primary': node.get('name_vi') or dn.get('primary') or person_id,
            'secondary': node.get('name_zh') or '',
            'authority_primary': dn.get('authority_primary', ''),
            'authority_secondary': dn.get('authority_secondary', ''),
            'source_type': 'dila',
            'source_file': '',
            'verification_status': 'ttl_conflict',
            'is_formal_name': False,
            'name_source': 'DILA',
            'ttl_candidates': idx['files'],
            'ttl_conflict': idx['files'],
        }
    # Không có TTL trong index: giữ nguyên kết quả hàm gốc (DILA phiên âm / curated).
    dn['name_source'] = 'TTL' if dn.get('is_formal_name') else 'DILA'
    dn['ttl_candidates'] = []
    dn['ttl_conflict'] = []
    return dn




def _t86_origin_place(conn, person_id):
    """Nguồn địa lý cho 'Xem trên bản đồ' — person_origin_link (sinh tại/籍貫).

    T372 fix: person_origin_link.place_id luôn ở dạng DILA gốc (12 chữ số,
    vd PL000000024832) — CÙNG hệ id với places_dila, KHÔNG phải với bảng
    `places` (bảng này có id ngắn độc lập, do một lần import khác đánh số
    tuần tự, không tương ứng 1-1 với số DILA). _t86_normalize_place_id()
    từng "rút gọn" id dài rồi tra bảng `places` — vô tình trúng một place_id
    ngắn TRÙNG SỐ nhưng là một địa danh hoàn toàn khác (vd PL000000024832
    "許州" bị đọc nhầm thành PL024832 "碭縣" trong `places`). Phải tra
    places_dila bằng raw_pid (id gốc, không normalize) mới đúng.
    Tên Việt: ưu tiên namevi_map_places theo dila_id (join key ổn định),
    không join theo name_zh (tên không phải khoá nối)."""
    row = conn.execute(
        "SELECT place_id FROM person_origin_link WHERE person_id=? ORDER BY confidence DESC LIMIT 1",
        (person_id,)
    ).fetchone()
    if not row:
        return None
    raw_pid = row['place_id']
    pl = conn.execute(
        "SELECT name, name_zh FROM places_dila WHERE id=?", (raw_pid,)
    ).fetchone()
    # `places_dila.name` là tên chính (persName/placeName gốc XML, vd 許州);
    # name_zh trong places_dila đôi khi là một tên biến thể/cổ khác — không
    # dùng làm tên hiển thị chính để tránh lộn tên như case 許州/潁川郡.
    name_zh = (pl['name'] if pl and pl['name'] else (pl['name_zh'] if pl else None))
    name_vi = None
    vi_confidence = None
    vi_source = None
    if name_zh:
        nv = conn.execute(
            "SELECT name_vi, confidence, source FROM namevi_map_places "
            "WHERE dila_id=? ORDER BY confidence DESC LIMIT 1",
            (raw_pid,)
        ).fetchone()
        if nv and nv['name_vi']:
            name_vi = nv['name_vi']
            vi_confidence = nv['confidence']
            vi_source = nv['source']
    return {
        "place_id": raw_pid,
        "name_vi": name_vi,
        "name_zh": name_zh,
        "vi_confidence": vi_confidence,
        "vi_source": vi_source,
    }




def _t360_classify_name_vi_source(raw_source, confidence):
    """T360 — Chuẩn hoá (label hiển thị, màu badge) từ (source, confidence) THẬT trong DB.
    Không hard-code theo ID — chỉ map nhãn text sang tiếng Việt + ngưỡng màu theo confidence.
    Màu: green=DILA/chính thức (>=0.95), yellow=TTL/Admin (0.8-0.94), gray=ZQ tự động (<0.8).
    """
    label_map = {
        'ttl_confirmed': 'TTL xác nhận',
        'manual': 'Admin chỉnh sửa',
        'manual_fix': 'Admin chỉnh sửa',
        'auto_transliterate': 'ZQ tự động',
        'auto_transliterate_v2': 'ZQ tự động',
        'auto_transliterate_t49': 'ZQ tự động',
        'auto_generated': 'ZQ tự động',
        'DILA': 'DILA chính thức',
        'places': 'DILA chính thức',
    }
    label = label_map.get(raw_source, raw_source or 'Không rõ nguồn')
    if confidence is None:
        color = 'gray'
    elif confidence >= 0.95:
        color = 'green'
    elif confidence >= 0.8:
        color = 'yellow'
    else:
        color = 'gray'
    return label, color




def _t360_resolve_place_name_vi_source(detail):
    """T360 — Xác định nguồn/độ tin cậy THẬT của places.name_vi đang hiển thị trên UI.
    detail là dict đã build trong api_places_detail (có thể mang theo các field phụ
    '_namevi_source'/'_namevi_confidence' do bước supplement từ namevi_map_places ghi lại).
    KHÔNG tự suy đoán — chỉ đọc lại field đã truy vấn thật từ DB.
    """
    try:
        if detail.get('_namevi_source') is not None or detail.get('_namevi_confidence') is not None:
            # name_vi đến từ namevi_map_places (dù detail gốc là row 'places' hay
            # row 'namevi_map') — đọc lại cột source/confidence thật đã lưu ở trên.
            raw_source = detail.get('_namevi_source')
            confidence = detail.get('_namevi_confidence')
        elif detail.get('source') == 'places':
            # name_vi lấy trực tiếp từ places.name_vi (không qua namevi_map) → cột
            # source_origin/confidence thật của bảng places (mặc định DILA/1.0).
            raw_source = detail.get('source_origin') or 'DILA'
            confidence = detail.get('confidence')
            if confidence is None:
                confidence = 1.0
        else:
            raw_source = None
            confidence = None
        if raw_source is None and confidence is None:
            return None, None, None
        label, color = _t360_classify_name_vi_source(raw_source, confidence)
        return label, confidence, color
    except Exception:
        return None, None, None




def _t360_resolve_person_name_vi_source(conn, person_id):
    """T360 — Xác định nguồn/độ tin cậy THẬT của people.name_vi.
    Thứ tự ưu tiên (đọc trực tiếp DB, không hard-code theo ID):
      1) person_display_names (verification_status thật — hiện có rất ít record)
      2) vn_person_authority (status thật — dila_id khớp person_id)
      3) Fallback theo quy tắc đã ghi trong CLAUDE.md: mọi name_vi còn lại trong
         `people` đều do ZQ phiên âm tự động, confidence 0.5 (KHÔNG phải DILA).
    Bọc try/except theo CLAUDE.md: các bảng authority có thể thiếu trên VPS.
    """
    try:
        row = conn.execute(
            "SELECT verification_status, source_type FROM person_display_names "
            "WHERE person_id = ? ORDER BY is_preferred DESC, id ASC LIMIT 1",
            (person_id,)
        ).fetchone()
        if row:
            vs = row['verification_status'] or ''
            st = row['source_type'] or ''
            if vs == 'verified_direct':
                confidence = 1.0 if st == 'manual' else 0.95
                raw_source = 'manual' if st == 'manual' else 'ttl_confirmed'
            elif vs == 'verified_crosswalk':
                confidence = 0.9
                raw_source = 'ttl_confirmed'
            else:
                confidence = 0.8
                raw_source = st or 'ttl_confirmed'
            label, color = _t360_classify_name_vi_source(raw_source, confidence)
            return label, confidence, color
    except Exception:
        pass

    try:
        row = conn.execute(
            "SELECT status FROM vn_person_authority WHERE dila_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (person_id,)
        ).fetchone()
        if row:
            status = row['status'] or 'pending'
            conf_map = {
                'verified': 0.95,
                'auto_ttl': 0.8,
                'alias_vi_suffix': 0.7,
                'alias_zh_match': 0.7,
                'pending': 0.6,
            }
            confidence = conf_map.get(status, 0.6)
            raw_source = 'ttl_confirmed' if status == 'verified' else f'TTL ({status})'
            label, color = _t360_classify_name_vi_source(raw_source, confidence)
            return label, confidence, color
    except Exception:
        pass

    # Fallback mặc định — đúng với ghi chú CLAUDE.md §"ZQ — nguồn tên tiếng Việt".
    label, color = _t360_classify_name_vi_source('auto_generated', 0.5)
    return label, 0.5, color




def _t86_parse_ref_passage(conn, ref):
    """Cố resolve chuỗi dẫn chiếu CBETA → passage row để mở Đọc trong Đại Tạng.
    ref dạng: '《...》卷3：「...」; http://cbetaonline.dila.edu.tw/B35n0194_p0349a09'
    Trích text_id từ URL (B35n0194_p0349a09 → B35n0194) rồi match passage.text_id.
    Trung thực: nếu passage chưa được lập chỉ mục → found=False."""
    if not ref:
        return None
    m = _re86.search(r'cbetaonline\.dila\.edu\.tw/([A-Za-z0-9_]+)', ref or '')
    if m:
        url = m.group(1)
        # text_id = phần trước dấu '_' (B35n0194_p0349a09 → B35n0194)
        text_id = url.split('_')[0] if '_' in url else url
        row = conn.execute(
            "SELECT passage_id, text_id, loc_ref FROM passage WHERE text_id=? ORDER BY passage_id LIMIT 1",
            (text_id,)
        ).fetchone()
        if row:
            return {"found": True, "passage_id": row['passage_id'],
                    "text_id": row['text_id'], "loc_ref": row['loc_ref'], "raw_ref": ref}
    # fallback: match theo thô chứa text_id bất kỳ
    for tok in _re86.findall(r'([A-Za-z]\d+n\d+)', ref or ''):
        row = conn.execute(
            "SELECT passage_id, text_id, loc_ref FROM passage WHERE text_id=? ORDER BY passage_id LIMIT 1",
            (tok,)
        ).fetchone()
        if row:
            return {"found": True, "passage_id": row['passage_id'],
                    "text_id": row['text_id'], "loc_ref": row['loc_ref'], "raw_ref": ref}
    return {"found": False, "passage_id": None, "raw_ref": ref,
            "message": "Chưa có đoạn văn được lập chỉ mục cho dẫn chiếu này trong Đại Tạng (passage table)."}




def calculate_edge_color_and_divergence(edge_row):
    """T410 (2026-10-19) — MÀU THEO NGUỒN (không phải theo số nguồn).

    edge_row: dict/Row có 3 cột boolean/int dila_asserted, marcus_asserted, ttl_asserted
    (lineage_asserted KHÔNG tham gia quy tắc màu — admin chỉ chỉ định 3 nguồn này).

    Quy tắc MÀU THEO NGUỒN (admin chốt 2026-10-19):
      - 1 nguồn   -> màu NGUỒN ĐÓ (dila/marcus/ttl), nét LIỀN
      - >=2 nguồn -> màu ĐỒNG THUẬN (agree), nét LIỀN
      - 0 nguồn   -> màu CHƯA RÕ (unknown), nét ĐỨT  (an toàn, không xảy ra thực tế)

    "Xám chấm = chưa rõ chiều" chỉ dùng cho nét đứt; cạnh 1 nguồn VẪN nét liền
    (chiều đã rõ, chỉ thiếu nguồn xác nhận thứ 2).

    Trả về dict:
      edge_color_token : 'dila'|'marcus'|'ttl'|'agree'|'unknown' (frontend đổi sang CSS var --edge-*)
      edge_sources     : list nguồn đã assert, ví dụ ['dila','marcus']
      n_sources        : số nguồn
      edge_color       : hex mặc định nền TỐI — fallback cho client cũ / edge_color
      edge_dashed      : True khi CHƯA rõ chiều (chỉ n_sources == 0)
      is_divergence    : True khi đúng 1 nguồn (cần khảo cứu thêm; dùng cho đếm tree_status)
    """
    dila_v = bool(edge_row.get('dila_asserted')) if hasattr(edge_row, 'get') else bool(edge_row['dila_asserted'])
    marc_v = bool(edge_row.get('marcus_asserted')) if hasattr(edge_row, 'get') else bool(edge_row['marcus_asserted'])
    ttl_v = bool(edge_row.get('ttl_asserted')) if hasattr(edge_row, 'get') else bool(edge_row['ttl_asserted'])

    # Hex nền tối (fallback). Bản sáng và bản chuẩn nằm ở CSS --edge-* trong places.html.
    COLOR_DILA = '#38bdf8'
    COLOR_MARCUS = '#facc15'
    COLOR_TTL = '#dc2626'
    COLOR_AGREE = '#f1f5f9'
    COLOR_UNKNOWN = '#94a3b8'

    sources = []
    if dila_v:
        sources.append('dila')
    if marc_v:
        sources.append('marcus')
    if ttl_v:
        sources.append('ttl')

    if len(sources) >= 2:
        return {
            'edge_color_token': 'agree', 'edge_sources': sources, 'n_sources': len(sources),
            'edge_color': COLOR_AGREE, 'dashed': False, 'is_divergence': False,
        }
    if len(sources) == 1:
        only = sources[0]
        hex_by_token = {'dila': COLOR_DILA, 'marcus': COLOR_MARCUS, 'ttl': COLOR_TTL}
        return {
            'edge_color_token': only, 'edge_sources': sources, 'n_sources': 1,
            'edge_color': hex_by_token[only], 'dashed': False, 'is_divergence': True,
        }
    return {
        'edge_color_token': 'unknown', 'edge_sources': [], 'n_sources': 0,
        'edge_color': COLOR_UNKNOWN, 'dashed': True, 'is_divergence': False,
    }




def api_monk_root_ancestor(dila_id):
    """GET /daoanh/api/monk/<dila_id>/root-ancestor
    BFS lên (thầy) từ dila_id đến khi không còn thầy → trả về khai tổ (root nodes).
    Mục đích: tìm vị khai tổ của tông phái đang hiển thị trong Pháp Mạch.
    Max 60 bước để tránh vòng lặp vô hạn."""
    conn = get_db_connection()
    try:
        # T186: cho phép ttl_persons (danh tăng VN) làm start node
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone() \
            or conn.execute("SELECT 1 FROM ttl_persons WHERE id=?", (dila_id,)).fetchone()
        if not exists:
            return jsonify({"ok": False, "error": "person not found"}), 404

        frontier = [dila_id]
        seen = {dila_id}
        roots = []
        hops = 0

        while frontier and hops < 60:
            hops += 1
            nxt = []
            for pid in frontier:
                # T187: dùng consensus với is_primary — bỏ qua early_study edges
                nb, _ = _t158_neighbors_consensus(conn, pid, 'up', include_single=True)
                # Lọc bỏ early_study (is_primary=-1) để BFS không bị lạc sang dòng phụ
                nb = [n for n in nb if n.get('is_primary', 0) != -1]
                if not nb:
                    info = _t86_person_info(conn, pid)
                    info['display_name'] = _t86_resolve_display_name(conn, pid, info)
                    if not any(r['id'] == pid for r in roots):
                        roots.append(info)
                else:
                    for nbv in nb:
                        nid = nbv['id']
                        if nid not in seen:
                            seen.add(nid)
                            nxt.append(nid)
            frontier = nxt

        return jsonify({
            "ok": True,
            "roots": roots,
            "hops": hops,
            "path_count": len(seen) - 1,
        })
    except Exception as e:
        app.logger.error(f"api_monk_root_ancestor error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T128 — Relation evidence: parser chuẩn hoá + translate + văn cảnh ─────────────
# Evidence hiện tại: marcus_networks.ref = chuỗi tự do ('trích đoạn…（T47n1990_p0582a19）; '
# hoặc '《…》卷N：「…」; http://cbetaonline.dila.edu.tw/B35n0194_p0349a09'). KHÔNG có field
# relation_id/original_excerpt/work_id/locator/text_hash → parser server-side (additive, 0 ALTER).
_T128_WORKID_RE = r'(?:[A-Za-z]\d+n[A-Za-z]?\d*)'



def _t128_parse_relation_ref(ref, from_id=None, to_id=None, direction=None):
    """Parse dẫn chứng Marcus → struct chuẩn hoá cho mối quan hệ truyền thừa.

    Trả dict:
      relation_id     = sha1(from|to|direction)[:12] (deterministic, không cần bảng mới)
      source          = URL CBETA (nếu ref là URL)
      work_id         = sigla văn bản (T47n1990 / B35n0194 ...) — None nếu không có
      locator         = vị trí trang (p0582a19 / p0349a09 ...) — None nếu không có
      original_excerpt= phần văn Hán trích dẫn (bỏ locator/URL, public thoại chuẩn)
      text_hash       = sha256(excerpt)[:24] — khớp translation_cache.source_hash
      has_ref         = ref có nội dung
    Trung thực: extract phần nào có được; không bịa ở chỗ thiếu."""
    ref0 = (ref or '').strip().strip(';；\u3000\t ')
    rel_id = ''
    if from_id and to_id and direction:
        rel_id = hashlib.sha1('|'.join([str(from_id), str(to_id), str(direction)]).encode('utf-8')).hexdigest()[:12]
    excerpt = ref0
    work_id = None
    locator = None
    source = None
    # locator đuôi dạng: '…（T47n1990_p0582a19）' hoặc '…(B35n0194_p0349a09)'
    m = re.search(r'[（(]\s*(%s(?:_[A-Za-z0-9]+)?)\s*[）)]\s*$' % _T128_WORKID_RE, ref0)
    if m:
        seg = m.group(1).split('_')
        work_id = seg[0]
        locator = seg[1] if len(seg) > 1 else None
        excerpt = ref0[:m.start()].strip().strip(';；\u3000\t ')
    else:
        # fallback: URL CBETA (không có locator trong ngoặc đuôi)
        mu = re.search(r'(https?://cbetaonline\.dila\.edu\.tw/[A-Za-z0-9_]+)', ref0)
        if mu:
            source = mu.group(1)
            url_tail = mu.group(1).split('/')[-1]
            wid = url_tail.split('_')[0] if '_' in url_tail else url_tail
            if re.match(r'^%s$' % _T128_WORKID_RE, wid):
                work_id = wid
            pre = ref0[:mu.start()].strip().strip(';；\u3000\t ')
            if pre:
                excerpt = pre
    text_hash = ''
    if excerpt.strip():
        text_hash = hashlib.sha256(excerpt.strip().rstrip('；;').encode('utf-8')).hexdigest()[:24]
    return {
        'relation_id': rel_id,
        'source': source,
        'work_id': work_id,
        'locator': locator,
        'original_excerpt': excerpt,
        'text_hash': text_hash,
        'has_ref': bool(ref0),
    }






# ── Nexus Point — event-centric knowledge graph (Commit 4) ──────────────────────────
# Trả về đồ thị nexus của một thực thể (person hoặc place): thực thể → sự kiện →
# văn bản (passage trích dẫn thật) → mốc thời gian (year/era). Mỗi edge đều mang
# citation thật (cbeta_ref / source_ref) — không suy đoán, không regex.
# Nguồn bảng event_text_link (bridge Commit 2) + cbeta_texts (tựa sách) + places_dila.
_NEXUS_GROUP_COLOR = {
    'person': '#c4891a',
    'place': '#3a9e6e',
    'event': '#8b5cf6',
    'text': '#0b7a96',
    'time': '#d97706',
}




def _nexus_title_for_sigla(conn, sigla, fallback):
    """Lấy tựa sách từ cbeta.db (nếu có), ngược lại trả fallback (source_book)."""
    try:
        c = get_cbeta_conn()
        try:
            r = c.execute("SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (sigla,)).fetchone()
            if r and r['title_zh']:
                sig = sigla.split('n', 1)[0] if 'n' in sigla else sigla
                return f"{sig} · {r['title_zh']}"
        finally:
            c.close()
    except Exception:
        pass
    return fallback or sigla




def _ensure_geo_cross_ref_table(conn):
    """geo_cross_ref — DILA place_id <-> external authority ID bridge (T21 design, approved
    2026-08-19, see tasks/T21-nien-dai-timeline-research.md). "Geo-Identity Linking": store
    only the ID, query the external source on-demand (no raw data clone). Reused here (T28)
    for wikidata_qid specifically, to answer "who founded this place" via live P112 lookup —
    T21 will reuse the same table for founding-date (P571) lookups.
    T29 adds bdrc_id column for BDRC sameAs links."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geo_cross_ref (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dila_id TEXT NOT NULL,
            wikidata_qid TEXT,
            chgis_svid TEXT,
            tgaz_id TEXT,
            bgis_id TEXT,
            marcus_ref TEXT,
            bdrc_id TEXT,
            notes TEXT,
            confidence TEXT DEFAULT 'verified',
            mapped_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dila_id)
        )
    """)
    # ALTER TABLE for existing databases that miss the bdrc_id column
    try:
        conn.execute("ALTER TABLE geo_cross_ref ADD COLUMN bdrc_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()



_WIKIDATA_CACHE = {}


_WIKIDATA_CACHE_TTL = 86400  # 24h, per T21 spec



def _fetch_wikidata_founders(qid):
    """Live-fetch P112 (founded by) claims for a Wikidata place QID, cached 24h (T21's
    "no raw import, query on-demand" pattern). Returns [{wikidata_qid, label, label_zh}] —
    deliberately NOT resolved to any DILA people.id here. That resolution is a separate,
    human-confirmed step (place_person_link) because matching a Wikidata person to the right
    row in a 48,673-row, name-ambiguous `people` table is document/identity interpretation,
    not something to auto-guess (see tasks/T28-place-person-lineage.md)."""
    now = time.time()
    cached = _WIKIDATA_CACHE.get(qid)
    if cached and now - cached[0] < _WIKIDATA_CACHE_TTL:
        return cached[1]
    # Wikimedia REST/API policy requires a descriptive User-Agent — anonymous/default
    # python-requests UA gets a 403, confirmed live 2026-08-20.
    _wd_headers = {'User-Agent': 'DaoAnhBuddhistGIS/1.0 (https://phatphaponline.org/daoanh/; contact via project admin) python-requests'}
    try:
        r = requests.get(f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json', headers=_wd_headers, timeout=8)
        r.raise_for_status()
        entity = r.json()['entities'][qid]
        person_qids = []
        for c in entity.get('claims', {}).get('P112', []):
            try:
                person_qids.append(c['mainsnak']['datavalue']['value']['id'])
            except (KeyError, TypeError):
                continue
        if not person_qids:
            _WIKIDATA_CACHE[qid] = (now, [])
            return []
        r2 = requests.get('https://www.wikidata.org/w/api.php', params={
            'action': 'wbgetentities', 'ids': '|'.join(person_qids),
            'props': 'labels', 'languages': 'vi|en|zh', 'format': 'json'
        }, headers=_wd_headers, timeout=8)
        r2.raise_for_status()
        ents = r2.json().get('entities', {})
        result = []
        for pqid in person_qids:
            labels = ents.get(pqid, {}).get('labels', {})
            label = (labels.get('vi') or labels.get('en') or labels.get('zh') or {}).get('value') or pqid
            label_zh = (labels.get('zh') or {}).get('value')
            result.append({"wikidata_qid": pqid, "label": label, "label_zh": label_zh})
        _WIKIDATA_CACHE[qid] = (now, result)
        return result
    except Exception as e:
        app.logger.warning(f"_fetch_wikidata_founders({qid}) failed: {e}")
        return []



def _ensure_place_person_link_table(conn):
    """place_person_link — curated (human-cited) place<->person relations, T22 (Nhân Vật /
    Truyền Thừa tabs). No column in places/places_dila/people links person<->place (verified
    2026-08-19, see tasks/T16-nexus-points.md) and none of the 15 trusted sources currently
    imported into this DB carries it either — DILA place catalog has no persName, Marcus has
    no place field, BDRC bdo:placeEvent exists conceptually but isn't populated for our places.
    Per CLAUDE.md's content-integrity rule this must NOT be filled by regex/fuzzy guessing.
    Every row here requires an explicit source_url citation (enforced in the insert route) —
    same human-curated pattern as custom_hanviet_override (T08), not an algorithm's guess."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS place_person_link (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            relation_type TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            note TEXT,
            added_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()




# ── T21: NIÊN ĐẠI tab — Geo-Identity Linking (2026-08-20) ────────────────────
# Design: geo_cross_ref bridge table (dila_id ↔ wikidata_qid) + place_timeline_events (BGIS/Marcus ETL).
# API fetches Wikidata P571/P1435 on-demand via QID. Dynasty context from time_periods (DILA, 117K rows).
# See tasks/T21-nien-dai-timeline-research.md for full spec.

import urllib.request as _urllib_req, urllib.parse as _urllib_parse



_WD_SPARQL_URL = "https://query.wikidata.org/sparql"


_WD_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "DaoAnhBot/1.0 (phatphaponline.org, DILA Buddhist GIS research)"
}


_timeline_cache = {}  # {qid: (data, timestamp)}



def _fetch_wikidata_timeline(qid):
    """Fetch P571 (founding) + P1435 (heritage) from Wikidata for a given QID.
    Returns dict with keys: founding_year, heritage, label, license. Cached 24h."""
    import time as _time
    if qid in _timeline_cache:
        cached, ts = _timeline_cache[qid]
        if _time.time() - ts < 86400:
            return cached

    query = f"""
SELECT ?item ?itemLabel ?inception ?heritage ?heritageLabel WHERE {{
  BIND(wd:{qid} AS ?item)
  OPTIONAL {{ ?item wdt:P571 ?inception }}
  OPTIONAL {{ ?item wdt:P1435 ?heritage }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,vi,en" . }}
}}
"""
    try:
        url = _WD_SPARQL_URL + "?" + _urllib_parse.urlencode({"query": query})
        req = _urllib_req.Request(url, headers=_WD_HEADERS)
        with _urllib_req.urlopen(req, timeout=8) as resp:
            data = __import__("json").loads(resp.read().decode("utf-8"))
        bindings = data.get("results", {}).get("bindings", [])
        founding_year = None
        label = qid
        heritage_list = []
        for b in bindings:
            if "inception" in b and founding_year is None:
                v = b["inception"]["value"].lstrip("+")
                try:
                    y = int(v[:4])
                    if 0 < y < 2100:
                        founding_year = y
                except Exception:
                    pass
            if "itemLabel" in b:
                label = b["itemLabel"]["value"]
            if "heritageLabel" in b and b.get("heritageLabel", {}).get("value", qid) != qid:
                h = b["heritageLabel"]["value"]
                if h not in heritage_list:
                    heritage_list.append(h)
        result = {
            "founding_year": founding_year,
            "label": label,
            "heritage": heritage_list,
            "license": "CC0",
            "source_ref": f"{qid}·P571",
            "wikidata_url": f"https://www.wikidata.org/wiki/{qid}"
        }
    except Exception as e:
        result = {"error": str(e), "founding_year": None, "label": qid, "heritage": []}

    _timeline_cache[qid] = (result, __import__("time").time())
    return result




def _get_dynasty_context(year_ce, conn):
    """Return dynasty context for a given CE year.
    DILA time_periods: 'dynasty' rows have no start_year yet (T14 pending).
    Uses compact hardcoded CE ranges for common Chinese dynasties.
    Returns dict with dynasty name (zh/vi) or None."""
    if not year_ce or year_ce <= 0:
        return None
    _DYNASTIES = [
        (-2070, -1046, "商", "Thương"),
        (-1046, -256, "周", "Chu"),
        (-221, -207, "秦", "Tần"),
        (-206, 220, "漢", "Hán"),
        (220, 265, "三國", "Tam Quốc"),
        (265, 420, "晉", "Tấn"),
        (420, 589, "南北朝", "Nam Bắc Triều"),
        (386, 534, "北魏", "Bắc Ngụy"),
        (534, 550, "東魏", "Đông Ngụy"),
        (550, 577, "北齊", "Bắc Tề"),
        (535, 556, "西魏", "Tây Ngụy"),
        (557, 581, "北周", "Bắc Chu"),
        (502, 557, "梁", "Lương"),
        (557, 589, "陳", "Trần"),
        (589, 618, "隋", "Tùy"),
        (618, 907, "唐", "Đường"),
        (907, 960, "五代十國", "Ngũ Đại Thập Quốc"),
        (960, 1127, "北宋", "Bắc Tống"),
        (1127, 1279, "南宋", "Nam Tống"),
        (1271, 1368, "元", "Nguyên"),
        (1368, 1644, "明", "Minh"),
        (1644, 1912, "清", "Thanh"),
    ]
    best = None
    best_span = None
    for (s, e, zh, vi) in _DYNASTIES:
        if s <= year_ce <= e:
            span = e - s
            if best_span is None or span < best_span:
                best = (zh, vi, s, e)
                best_span = span
    if not best:
        return None
    row = (best[0], best[1], "", best[2], best[3])
    return {
        "dynasty_zh": row[0],
        "dynasty_vi": row[1] or "",
        "era_name": row[2] or "",
        "dynasty_start": row[3],
        "dynasty_end": row[4],
        "source": "chinese_dynasties_static",
        "license": "public domain"
    }




def _ensure_place_timeline_events_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS place_timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dila_id TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'founding',
            year INTEGER, year_end INTEGER,
            label_zh TEXT, label_vi TEXT,
            source TEXT NOT NULL, source_ref TEXT,
            confidence TEXT DEFAULT 'verified',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pte_dila ON place_timeline_events(dila_id)")
    conn.commit()




def _t172_load_hv(conn, person_id):
    """T172 — đọc sidecar person_hanviet_debug → object hv (debug charwise) cho 1 person.

    SPEC §11 helper; trả None nếu chưa migrate/không có row (UI tự ẩn).
    """
    d_row = conn.execute(
        "SELECT han_name_raw, han_viet_legacy, han_viet_charwise, han_char_count, "
        "       han_viet_syllable_count, unknown_characters, han_viet_validation_status, "
        "       han_viet_validation_reason, legacy_match_status, is_transliteration, "
        "       dict_version "
        "FROM person_hanviet_debug WHERE person_id = ?", (person_id,)
    ).fetchone()
    if not d_row:
        return None
    return {
        'raw': d_row['han_name_raw'],
        'legacy': d_row['han_viet_legacy'],
        'charwise': d_row['han_viet_charwise'],
        'han_count': d_row['han_char_count'],
        'syll_count': d_row['han_viet_syllable_count'],
        'unknown': d_row['unknown_characters'] or '',
        'status': d_row['han_viet_validation_status'],
        'reason': d_row['han_viet_validation_reason'] or '',
        'legacy_match': d_row['legacy_match_status'],
        'is_transliteration': d_row['is_transliteration'],
        'dict_version': d_row['dict_version'],
    }




# ─── CHRONOLOGY API ─────────────────────────────────────────
CHRONOLOGY_DB = DB_PATH



def get_chronology_conn():
    conn = sqlite3.connect(CHRONOLOGY_DB)
    conn.row_factory = sqlite3.Row
    return conn




# ── T50 Job Control (run / stop / job-status) ──────────────────────────────
import subprocess as _t50_sp


import signal as _t50_sig



_T50_STATUS_FILE = os.path.join(os.path.dirname(__file__), 'data', 't50_job_status.json')


_T50_LOG_FILE    = os.path.join(os.path.dirname(__file__), 'data', 't50_job.log')


_T50_SCRIPT      = os.path.join(os.path.dirname(__file__), 'scripts', 't50_passage_vi_backfill.py')



def _t50_pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False



def _t50_read_job():
    try:
        with open(_T50_STATUS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"running": False, "sigla": None, "pid": None, "started_at": None}



def _t50_write_job(d):
    try:
        with open(_T50_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass



def _t50_log_tail(n=15):
    try:
        with open(_T50_LOG_FILE, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-n:] if l.strip()]
    except Exception:
        return []




def _t50_start_sigla(sigla, st):
    """Helper: spawn backfill subprocess cho 1 sigla, cập nhật st dict, write job file."""
    cmd = ['python', '-X', 'utf8', _T50_SCRIPT, '--sigla', sigla, '--sleep', '1.0']
    log_f = open(_T50_LOG_FILE, 'w', encoding='utf-8')
    proc = _t50_sp.Popen(cmd, stdout=log_f, stderr=log_f,
                          cwd=os.path.dirname(__file__),
                          env={**os.environ, 'PYTHONUTF8': '1'})
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    st.update({"running": True, "sigla": sigla, "pid": proc.pid, "started_at": now})
    _t50_write_job(st)
    return proc.pid




# ─────────────────────────────────────────────────────────────────────────────
# T181 — CBETA Catalog + Lazy Import (P3/P4)
# ─────────────────────────────────────────────────────────────────────────────

_T181_XML_ROOT = os.path.join(os.path.dirname(__file__), 'data', 'cbeta', 'xml-p5-full')


_T181_CBETA_DB  = os.path.join(os.path.dirname(__file__), 'data', 'cbeta', 'cbeta.db')


_T181_IMPORT_PY = os.path.join(os.path.dirname(__file__), 'data', 'cbeta', 'import_cbeta.py')




def _t181_xml_path(sigla):
    """Trả đường dẫn dự kiến cho file XML của sigla, hoặc None nếu không tìm thấy."""
    import re as _re
    m = _re.match(r'^([A-Z])(\d+)n(\d+)', sigla)
    if not m:
        return None
    series, vol_str = m.group(1), m.group(2)
    p = os.path.join(_T181_XML_ROOT, series, f'{series}{vol_str}', f'{sigla}.xml')
    return p if os.path.exists(p) else None




# ─────────────────────────────────────────────────────────────────────────────
# T183 — LAZY-FETCH FALLBACK (2026-09-27)
#
# BỐI CẢNH — TẠI SAO 20% BỘ KINH THIẾU XML LOCAL:
#   • xml-p5-full (clone từ cbeta-org/xml-p5) chỉ có volumes T01-T55 + T85.
#   • Volumes T56-T84 (583 bộ, sh_number 2185-2731) KHÔNG có trong repo public.
#   • Lý do: T56-T84 là phụ lục học thuật Nhật Bản (mục lục, chú giải, nghiên
#     cứu) — CBETA chưa phát hành XML công khai vì vấn đề bản quyền (tác giả
#     Nhật thế kỷ 20 vẫn còn thời hạn copyright).
#
# GIẢI PHÁP TỰ ĐỘNG (hàm này):
#   1. Với T01-T55/T85: fallback download từ GitHub raw (cbeta-org/xml-p5).
#      Thường không cần vì xml-p5-full đã clone đủ. Phòng khi file bị xóa.
#   2. Với T56-T84: KHÔNG có nguồn tự động. Trả (None, reason) để batch-import
#      ghi log rõ ràng và admin biết cần xử lý thủ công.
#
# CÁCH THÊM T56-T84 VÀO LOCAL (thủ công, 1 lần):
#   Bước 1: Vào https://cbeta.org/download → tải "CBReader 2X v0.9.9.2 經文資料檔"
#            (bookcase_v0992_20260831.zip, 1.21 GB).
#   Bước 2: Giải nén, tìm thư mục XML (thường trong bookcase/T56..T84/).
#   Bước 3: Copy vào data/cbeta/xml-p5-full/T/ theo cấu trúc:
#            T56/T56n{num}.xml, T57/T57n{num}.xml, ...
#   Sau đó batch-import sẽ tự tìm được — không cần thay đổi code.
#
# VOLUMES T56-T84 CHỨA GÌ:
#   T56-T84: Luật tạng bổ sung, truyện ký, mục lục, sử liệu, thư tịch học.
#   Phần lớn là tài liệu nghiên cứu, ít được dịch sang tiếng Việt.
#   Ưu tiên dịch thấp hơn kinh văn chính (T01-T55).
# ─────────────────────────────────────────────────────────────────────────────
_T183_GITHUB_RAW = 'https://raw.githubusercontent.com/cbeta-org/xml-p5/master'


# Volumes có XML trên GitHub public (cbeta-org/xml-p5):
_T183_PUBLIC_VOLS = set(range(1, 56)) | {85}   # T01-T55 + T85




def _t183_lazy_fetch_xml(sigla):
    """Fallback khi XML không có local: thử download từ GitHub raw.

    Trả về (path_or_None, reason_str):
      - ('đường_dẫn', 'downloaded')     nếu download thành công + cache local
      - (None, 'T56_T84_no_public_xml') nếu thuộc volumes không có XML public
      - (None, 'download_failed:...')   nếu download lỗi
      - (None, 'sigla_invalid')         nếu sigla không đúng format
    """
    import re as _re, urllib.request as _req, pathlib as _pl
    m = _re.match(r'^([A-Z]+)(\d+)n(\d+)', sigla)
    if not m:
        return None, 'sigla_invalid'

    series, vol_int, vol_str = m.group(1), int(m.group(2)), m.group(2)

    # Kiểm tra volume có XML public không
    if series == 'T' and vol_int not in _T183_PUBLIC_VOLS:
        # T56-T84: không có trên GitHub — phải download thủ công
        return None, (
            f't{vol_int:02d}_no_public_xml | '
            f'Volume T{vol_str} (sh_number khoảng 2185-2731) thuộc T56-T84, '
            f'chưa có trên GitHub public. '
            f'Admin tự download: cbeta.org/download → bookcase_v0992.zip → '
            f'copy T{vol_str}/ vào data/cbeta/xml-p5-full/T/'
        )

    # Thử download từ GitHub raw
    url = f'{_T183_GITHUB_RAW}/{series}/{series}{vol_str}/{sigla}.xml'
    dest_dir = _pl.Path(_T181_XML_ROOT) / series / f'{series}{vol_str}'
    dest = dest_dir / f'{sigla}.xml'
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        _req.urlretrieve(url, dest)
        return str(dest), 'downloaded'
    except Exception as _e:
        return None, f'download_failed:{_e}'




def _wiki_search_lang(lang, term, headers):
    """Search one Wikipedia language edition for `term`, return a snapshot dict
    or None. Used by wiki_fetch()'s vi -> zh -> en fallback chain (T07)."""
    import re as re_html
    import html as html_lib
    try:
        resp = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": term,
                    "format": "json", "srlimit": 1, "srprop": "snippet"},
            headers=headers, timeout=8
        )
        pages = resp.json().get('query', {}).get('search', [])
        if not pages:
            return None
        title = pages[0]['title']
        # Strip tags first, then unescape entities (the search snippet's HTML
        # bolds the matched term, e.g. <span class="searchmatch">X</span>, and
        # separately encodes quotes as &quot; — stripping tags alone left the
        # entity literally as "&quot;" in the rendered UI).
        snippet = html_lib.unescape(re_html.sub(r'<[^>]+>', '', pages[0].get('snippet', '')))
        ext_resp = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "extracts", "exintro": 1,
                    "titles": title, "format": "json"},
            headers=headers, timeout=8
        )
        pages2 = ext_resp.json().get('query', {}).get('pages', {})
        html_extract = next((p['extract'] for p in pages2.values() if 'extract' in p), '')
        plain_text = html_lib.unescape(re_html.sub(r'<[^>]+>', '', html_extract))
        return {
            "title": title,
            "url": f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}",
            "snippet": (snippet or plain_text)[:500],
            "full_text": plain_text[:2000],
            "content_html": html_extract,
            "lang": lang,
        }
    except Exception:
        return None



def _resolve_place_id(conn, dila_id):
    """T67: resolve ID thực trong DB (places_pending.id == entity_hub.canonical_label).

    Frontend gửi id đã blanket pad (ensure_long_id → PL + 12 digits) nhưng một số place
    lưu id dạng raw ngắn hơn. Trả về dạng id THỰC tồn tại trong DB để:
      - entity_hub.canonical_label trùng khớp (để flip status verified),
      - canonical_decision.entity_ref / en_audit_log.entity_ref nhất quán.
    """
    raw = str(dila_id or '').strip()
    if not raw:
        return None
    attempts = [raw, ensure_long_id(raw)]
    for a in attempts:
        row = conn.execute("SELECT id FROM places_pending WHERE id = ? LIMIT 1", (a,)).fetchone()
        if row:
            return row[0]
        row = conn.execute("SELECT canonical_label FROM entity_hub WHERE canonical_label = ? LIMIT 1", (a,)).fetchone()
        if row:
            return row[0]
    return attempts[0]



def _persist_canonical_decision(conn, dila_id, action, field_name, old_value, new_value,
                                evidence_citations=None, authority_rank=None,
                                verification_status='verified', decision_note='', editor='admin',
                                mark_verified=True):
    """T67: ghi quyết định canonical + audit log + chuyển entity_hub.status='verified'.

    Additive — chỉ THÊM vào 2 bảng mới (canonical_decision, en_audit_log) và chuyển trạng thái
    entity_hub; KHÔNG sửa bảng nguồn. Caller phải commit sau khi gọi (dùng chung conn).
    verification_status chỉ = 'verified' khi admin THỰC SỰ duyệt (không backfill bulk).
    """
    import json as _json
    import datetime as _dt
    ref = _resolve_place_id(conn, dila_id)
    now = _dt.datetime.now().isoformat(timespec='seconds')
    ev = _json.dumps(evidence_citations, ensure_ascii=False) if evidence_citations else '[]'
    conn.execute("""
        INSERT INTO canonical_decision (entity_ref, canonical_name_vi, source_id, authority_rank,
            confidence, verification_status, decision_note, evidence_citations, editor, decided_at, updated_at)
        VALUES (?, ?, NULL, ?, 1.0, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_ref) DO UPDATE SET
            canonical_name_vi=excluded.canonical_name_vi,
            authority_rank=excluded.authority_rank,
            verification_status=excluded.verification_status,
            decision_note=excluded.decision_note,
            evidence_citations=excluded.evidence_citations,
            editor=excluded.editor,
            updated_at=excluded.updated_at
    """, (ref, new_value, authority_rank, verification_status, decision_note, ev, editor, now, now))
    conn.execute("""
        INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value,
            evidence_sources, authority_rank, editor, verification_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ref, action, field_name, old_value, new_value, ev, authority_rank, editor, verification_status, now))
    if mark_verified and ref:
        conn.execute("UPDATE entity_hub SET status = 'verified', updated_at = ? WHERE canonical_label = ?", (now, ref))




# ════════════════════════════════════════════════════════════════════════
# T427 — Tab "🗺️ Place" trong namevimap.html (giai đoạn 1: UI + API,
# KHÔNG Claude/Gemini AI, KHÔNG đổi schema).
#
# Danh sách gốc: places_dila (59.167 địa danh, ID dài PL + 12 số).
# Ghi (approve/edit): chỉ namevi_map_places, khớp theo dila_id DẠNG DÀI
# (ensure_long_id) — không ghi places_pending, không đổi schema.
# Audit: dùng lại _persist_canonical_decision() (T67), không tạo bảng log mới.
# ════════════════════════════════════════════════════════════════════════

def _t427_session_email(token):
    """Lấy email thật của session hiện tại (server.py /api/login/check trả thêm 'email').
    KHÔNG tin editor do client gửi trong body — bảo mật: editor phải đến từ session đã verify."""
    try:
        resp = requests.post(
            'http://127.0.0.1:5001/api/login/check',
            json={'session_token': token},
            timeout=5
        )
        d = resp.json()
        if d.get('valid'):
            return d.get('email') or 'admin'
    except Exception:
        pass
    return 'admin'




_T427_SOURCE_BADGE = {
    'manual': 'Admin sửa tay',
    'manual_fix': 'Admin sửa tay',
    'ttl_confirmed': 'TTL xác nhận',
}




def _t427_source_badge(source):
    """Badge nguồn tên Việt hiện tại — KHÔNG bao giờ ghi là tên của DILA (quy tắc ZQ).
    DILA chỉ có tên Hán; tên Việt luôn do ZQ/admin/TTL tạo ra."""
    if not source:
        return None
    return _T427_SOURCE_BADGE.get(source, 'phiên âm tự động')




# ── Cache số liệu 6 bộ lọc (độc lập với q/filter — toàn bộ places_dila) ──
# Query COUNT trên 59K dòng tốn ~0.2-0.6s; không cần tính lại mỗi request vì
# dữ liệu chỉ đổi khi Admin Pass/Sửa (hiếm, không cần real-time tuyệt đối).
# TTL ngắn (20s) đủ để UI thấy số mới sau khi Pass/Sửa mà vẫn giảm tải DB.
_T427_FILTER_CACHE = {'data': None, 'ts': 0.0}


_T427_FILTER_CACHE_TTL = 20.0




def _t427_filter_counts(conn):
    import time as _time
    now = _time.time()
    cached = _T427_FILTER_CACHE['data']
    if cached is not None and (now - _T427_FILTER_CACHE['ts']) < _T427_FILTER_CACHE_TTL:
        return cached
    agg = conn.execute("""
        SELECT COUNT(*) AS all_n,
               SUM(CASE WHEN m.id IS NULL OR m.vn_name_status IS NULL OR m.vn_name_status != 'reviewed' THEN 1 ELSE 0 END) AS needs_review_n,
               SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM vn_person_places vp WHERE vp.place_id = pd.id) THEN 1 ELSE 0 END) AS no_ttl_n
        FROM places_dila pd
        LEFT JOIN namevi_map_places m ON m.dila_id = pd.id
    """).fetchone()
    all_n = agg['all_n']
    result = {
        'all': all_n,
        'pass100': 0,
        'needs_review': agg['needs_review_n'],
        'no_claude': all_n,
        'no_gemini': all_n,
        'no_ttl': agg['no_ttl_n'],
    }
    _T427_FILTER_CACHE['data'] = result
    _T427_FILTER_CACHE['ts'] = now
    return result




def _t427_invalidate_filter_cache():
    """Gọi sau khi Pass/Sửa ghi DB để lần GET kế tiếp không trả số liệu cũ quá 20s."""
    _T427_FILTER_CACHE['data'] = None




def resolve_canonical(conn, entity_ref):
    """T68b: bỏ phiếu đa-nguồn → trả về canonical value tốt nhất cho name_vi của entity_ref.

    Trả về dict {value, score, sources, confidence, has_conflict}.
    Sau T69 (CBETA/Marcus wire), sẽ có nhiều ứng viên hơn.
    """
    a_map = _source_authority_map(conn)
    ranked = _name_vi_evidence(conn, entity_ref, a_map)
    if not ranked:
        return {"value": None, "score": 0, "sources": [], "confidence": 0.0, "has_conflict": False}
    top_val, top_info = ranked[0]
    has_conflict = False
    if len(ranked) >= 2:
        second_val, second_info = ranked[1]
        if (top_info['score'] - second_info['score']) < 50 and top_val != second_val:
            has_conflict = True
            _detect_conflicts(conn, ranked, entity_ref)
    return {
        "value": top_val,
        "score": top_info['score'],
        "sources": top_info['sources'],
        "confidence": top_info['confidence'],
        "has_conflict": has_conflict,
    }




def _source_authority_map(conn):
    """T68: đọc matrix source_authority → {source_code: {'score','order','implemented'}}."""
    rows = conn.execute(
        "SELECT source_code, authority_score, precedence_order, implemented FROM source_authority"
    ).fetchall()
    return {r['source_code']: {'score': r['authority_score'], 'order': r['precedence_order'], 'implemented': r['implemented']} for r in rows}




def _resolve_entity_id(conn, entity_ref):
    """T68: entity_ref ('PL…') → (entity_id INT, ref raw). Trả về (None, ref) nếu không có hub row."""
    ref = _resolve_place_id(conn, entity_ref)
    row = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label = ?", (ref,)).fetchone()
    if row:
        return row[0], ref
    row = conn.execute("SELECT entity_id FROM entity WHERE dila_id = ?", (ref,)).fetchone()
    if row:
        return row[0], ref
    return None, ref




def _name_vi_evidence(conn, entity_ref, authority_map):
    """T68: gom các ứng viên tên Việt cho 1 địa danh, bỏ phiếu theo authority_score.

    Trả về list tuple (value, {score, sources, confidence, order}) đã sắp theo score giảm dần.
    """
    eid, ref = _resolve_entity_id(conn, entity_ref)
    votes = {}

    def add(value, source_code, confidence, order_hint=None):
        if not value or not str(value).strip():
            return
        v = str(value).strip()
        sc = (source_code or '').upper()
        info = authority_map.get(sc)
        if info is None or sc in ('DILA',):
            return
        score = info['score'] if info.get('implemented', 1) else 0
        o = order_hint if order_hint is not None else info.get('order', 99)
        cur = votes.get(v)
        if cur is None:
            votes[v] = {'score': score, 'sources': [sc], 'confidence': float(confidence or 0), 'order': o}
        else:
            if score > cur['score']:
                cur['score'] = score
                cur['order'] = min(cur['order'], o)
            if sc not in cur['sources']:
                cur['sources'].append(sc)
            cur['confidence'] = max(cur['confidence'], float(confidence or 0))

    for r in conn.execute("SELECT name_vi, source, confidence FROM namevi_map_places WHERE dila_id = ?", (ref,)):
        src = r['source'] or ''
        if src == 'manual':
            add(r['name_vi'], 'ZQLOCAL', r['confidence'] or 1.0, order_hint=0)
        elif src == 'auto_generated':
            add(r['name_vi'], 'ZQLOCAL', r['confidence'] or 0.5, order_hint=0)
    if eid is not None:
        for r in conn.execute("""
                SELECT c.source_id, d.source_code, c.object_text, c.confidence
                FROM entity_claims c LEFT JOIN data_sources d ON d.source_id = c.source_id
                WHERE c.entity_id = ? AND c.claim_type = 'NAME'
            """, (eid,)):
            if (r['source_code'] or '').upper() != 'DILA':
                add(r['object_text'], r['source_code'] or 'ZQLOCAL', r['confidence'] or 0.5)
    dec = conn.execute("SELECT canonical_name_vi FROM canonical_decision WHERE entity_ref = ?", (ref,)).fetchone()
    if dec and dec['canonical_name_vi']:
        add(dec['canonical_name_vi'], 'ZQLOCAL', 1.0, order_hint=0)
    ranked = sorted(votes.items(), key=lambda kv: (-kv[1]['score'], kv[1]['order']))
    return ranked




def _detect_conflicts(conn, ranked, entity_ref, threshold=50):
    """T68: phát hiện xung đột giữa các ứng viên tên Việt có score chênh lệch < threshold.

    Ghi conflict_pending (chỉ 1 lần/entity/field nếu chưa có pending). Gọi khi cần.
    """
    if len(ranked) < 2:
        return
    top = ranked[0]
    for v, d in ranked[1:]:
        if top[1]['score'] - d['score'] < threshold and top[0] != v:
            existing = conn.execute(
                "SELECT id FROM conflict_pending WHERE entity_ref=? AND field='name_vi' AND status='pending'",
                (entity_ref,)
            ).fetchone()
            if existing:
                continue
            conn.execute("""
                INSERT INTO conflict_pending (entity_ref, field, value_a, value_b, source_a, source_b, authority_a, authority_b)
                VALUES (?, 'name_vi', ?, ?, ?, ?, ?, ?)
            """, (entity_ref, top[0], v, top[1]['sources'][0], d['sources'][0], top[1]['score'], d['score']))



# ── T416 (2026-10-21): ép index cho places_pending LIKE trong /autocomplete ──
# Planner bỏ qua idx_places_pending_name_zh cho LIKE '%q%' dù đã ANALYZE; ép index
# đo được 1312 ms → 137 ms. Cache kết quả kiểm tra tồn tại index 1 lần/process.
_T416_PENDING_IDX = None




def _t416_pending_index_hint(conn):
    """True nếu idx_places_pending_name_zh tồn tại (an toàn khi DB khác thiếu index)."""
    global _T416_PENDING_IDX
    if _T416_PENDING_IDX is None:
        try:
            _T416_PENDING_IDX = bool(conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_places_pending_name_zh' LIMIT 1"
            ).fetchone())
        except Exception:
            _T416_PENDING_IDX = False
    return _T416_PENDING_IDX



def _pali_sanskrit_lookup(q, conn):
    """
    T58 (phương án b — KHÔNG tạo bảng place_lang_alias): tra cứu Pali/Sanskrit
    trực tiếp trong `pali_place_ref` (15 địa danh, seed DILA+SuttaCentral, không
    tự suy map tên kinh điển mở rộng vì không có nguồn seed cho phần đó).
    name_pali/name_skt có thể chứa nhiều biến thể phân tách bằng ' / ' (vd
    "Rājagaha" cho "Rajagriha" không dấu) — so khớp sau khi bỏ dấu/hạ chữ qua
    normalize_text() đã có sẵn trong app.py.
    Trả về list dila_id (PL...) khớp, rỗng nếu không tìm thấy hoặc bảng thiếu
    (VPS schema lag) — không literal 500.
    """
    nq = normalize_text(q)
    if not nq:
        return []
    try:
        rows = conn.execute(
            "SELECT dila_id, name_pali, name_skt FROM pali_place_ref"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    try:
        from rapidfuzz import fuzz
    except Exception:
        fuzz = None
    matched = []
    for r in rows:
        variants = []
        for field in (r['name_pali'], r['name_skt']):
            if field:
                variants.extend(re.split(r'\s*/\s*', field))
        for v in variants:
            nv = normalize_text(v)
            if not nv:
                continue
            if nq in nv or nv in nq:
                matched.append(r['dila_id'])
                break
            # Fuzzy fallback cho biến thể La-tinh hóa khác nhau (vd "Rajagriha" vs
            # "Rajagrha" từ Rājagṛha bỏ dấu) — vẫn chỉ so khớp trong 15 dòng seed có
            # sẵn, KHÔNG suy map mới. Ngưỡng 85 đủ chặt để tránh false-positive giữa
            # 15 địa danh khác nhau trong bảng.
            if fuzz and len(nq) >= 4 and fuzz.ratio(nq, nv) >= 85:
                matched.append(r['dila_id'])
                break
    return matched



# ── T469: lazy in-memory cache cho autocomplete trang chủ ──────────────────
# Lý do dùng cache thay vì SQLite scalar function 'normalize_text' gọi trực
# tiếp trong WHERE: đã đo (xem report T469) — gọi hàm Python qua ctypes cho
# từng dòng trong lúc SCAN 48,673 dòng của 'people' tốn 2.8–6s/lần, KHÔNG đạt
# mục tiêu <1s. Build cache 1 lần (~1.8s, chỉ xảy ra ở request đầu/sau khi
# process khởi động lại) rồi lọc substring trên chuỗi đã chuẩn hoá sẵn trong
# RAM cho kết quả ~15-35ms — đạt mục tiêu "ấm" của task. Không phải DB
# migration/index: chỉ là cache cấp ứng dụng, cùng kiểu với _LEX_EXACT/
# _LEX_LIST ở trên (dòng ~185) đã có sẵn trong file này. Không sửa DB.
_PERSON_SUGGEST_CACHE = None   # list[dict] — xây 1 lần từ bảng people


_WORK_SUGGEST_CACHE = None     # list[dict] — xây 1 lần từ bảng cbeta_catalog_vn



def _get_work_suggest_cache():
    global _WORK_SUGGEST_CACHE
    if _WORK_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT cbeta_id, title_vi, title_zh, byline_vi AS translator, dynasty_vi AS era
                FROM dila_catalog_works
            """).fetchall()
        finally:
            conn.close()
        cache = []
        for r in rows:
            title_vi = r['title_vi'] or ''
            title_zh = r['title_zh'] or ''
            cache.append({
                'id': r['cbeta_id'], 'title_vi': title_vi, 'title_zh': title_zh,
                'translator': r['translator'], 'era': r['era'],
                '_norm_vi': normalize_text(title_vi), '_norm_zh': title_zh.lower(),
            })
        _WORK_SUGGEST_CACHE = cache
    return _WORK_SUGGEST_CACHE


def _get_place_suggest_cache():
    """Truy van du lieu dia danh tu namevi_map_places."""
    global _PLACE_SUGGEST_CACHE
    if _PLACE_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT DISTINCT dila_id AS id, name_vi AS value, name_zh AS name_zh, source
                FROM namevi_map_places
            """).fetchall()
        finally:
            conn.close()
        seen = set()
        unique = []
        for r in rows:
            if r['value'] in seen:
                continue
            seen.add(r['value'])
            unique.append(dict(r))
        _PLACE_SUGGEST_CACHE = unique
    return _PLACE_SUGGEST_CACHE


def _get_person_with_contribution_cache():
    """Set of person IDs that appear in dila_catalog_contributors."""
    global _PERSON_CONTRIBUTOR_IDS
    if _PERSON_CONTRIBUTOR_IDS is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT DISTINCT person_id FROM dila_catalog_contributors
            """).fetchall()
        finally:
            conn.close()
        _PERSON_CONTRIBUTOR_IDS = {str(row[0]) for row in rows}
    return _PERSON_CONTRIBUTOR_IDS


def parse_han_variants(raw_xml):
    import xml.etree.ElementTree as ET
    if not raw_xml or not raw_xml.strip():
        return []
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    try:
        root = ET.fromstring(raw_xml)
        return [{'text': (pn.text or '').strip(), 'type': pn.get('type', 'main')}
                for pn in root.findall('.//tei:placeName', ns)
                if pn.get('{http://www.w3.org/XML/1998/namespace}lang', '') == 'zho-Hant'
                and (pn.text or '').strip()]
    except Exception:
        return []



def parse_name_variants(raw_xml):
    """Parse ALL placeName elements from TEI raw_xml (any language)."""
    import xml.etree.ElementTree as ET
    if not raw_xml or not raw_xml.strip():
        return []
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    try:
        root = ET.fromstring(raw_xml)
        return [{'lang': pn.get('{http://www.w3.org/XML/1998/namespace}lang', ''),
                 'name': (pn.text or '').strip(),
                 'type': pn.get('type', 'main')}
                for pn in root.findall('.//tei:placeName', ns)
                if (pn.text or '').strip()]
    except Exception:
        return []



app = Flask(__name__)


# Public read API (GET) cần CORS rộng để academic clients có thể query.
# Write/admin endpoints được bảo vệ bằng require_admin + session check trong từng route.
CORS(app, resources={
    r"/daoanh/api/*": {
        "origins": ["https://phatphaponline.org", "http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})



from t265_routes import t265_bp



BASE_DIR = os.path.dirname(os.path.abspath(__file__))


ADMIN_DIR = os.path.join(BASE_DIR, 'admin')


DATA_DIR = os.path.join(BASE_DIR, 'data')


DB_PATH = os.path.join(DATA_DIR, 'lineage.db')


SQLITE_DB = DB_PATH


TTL_OLD_DIR = os.path.join(BASE_DIR, 'data', 'ttl', 'old')


TTL_MASTER_DIR = os.path.join(BASE_DIR, 'ontology', 'ttl', 'monks')


TTL_ARCHIVE_DIR = os.path.join(BASE_DIR, 'data', 'ttl', 'archive')



# CBDB — single real database, read-only
CBDB_PATH = os.path.join(DATA_DIR, 'cbdb', 'cbdb_20260516.sqlite3')



# CBETA — full text content database
CBETA_PATH = os.path.join(DATA_DIR, 'cbeta', 'cbeta.db')



def get_cbeta_conn():
    conn = sqlite3.connect(CBETA_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def get_cbdb_conn():
    conn = sqlite3.connect(CBDB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



from db_core import get_db_connection



# Compatibility alias – many routes still call get_db()
get_db = get_db_connection



# ── Lexicon in-memory cache (load lazily, word-index for fast lookup) ───────────
_LEX_EXACT    = None   # dict: term → source  (exact lookup O(1))


_LEX_LIST     = None   # list of (term, source)


_LEX_WORD_IDX = None   # dict: word_lower → list of int (indices into _LEX_LIST)



_LEX_SOURCE_ABBR = {
    # ASCII source names (tên thực trong DB, không dấu)
    'phat hoc tinh tuyen':          'PH Tinh Tuyển',
    'phat quang dai tu dien':       'PQ Đại TĐ',
    'phat quang tu dien':           'PQ Từ Điển',
    'phap so can ban':              'Pháp Số',
    'danh-tu-thien-hoc':            'TĐ Thiền Học',
    'tu dien thien tong':           'TĐ Thiền Tông',
    'danh tu thien tong':           'TĐ Thiền Tông',
    'tu dien da ngon ngu':          'TĐ Đa Ngôn Ngữ',
    'kho tang phap hoc':            'KTPH',
    'tu dien phat hoc - quang tri': 'PGĐTĐ',
    'tu dien han viet':             'TĐ Hán Việt',
    'tu dien pali':                 'TĐ Pali-Việt',
    'trich luc tu ngu phat hoc':    'Trích Lục TN',
    'nien bieu gian luoc':          'Niên Biểu',
    'tam tang phap so':             'Tam Tạng Pháp Số',
    # Vietnamese diacritics keys (legacy)
    'phật học tinh tuyển':          'PH Tinh Tuyển',
    'từ điển phật học tổng hợp':    'TĐPHTTH',
    'phật quang đại từ điển':       'PQ Đại TĐ',
    'phật quang từ điển':           'PQ Từ Điển',
    'pháp số căn bản':              'Pháp Số',
}



def _abbr_source(src):
    s = (src or '').lower()
    for k, v in _LEX_SOURCE_ABBR.items():
        if k in s:
            return v
    return (src or '')[:20]



def _ensure_lex_cache():
    global _LEX_EXACT, _LEX_LIST, _LEX_WORD_IDX
    if _LEX_EXACT is not None:
        return
    conn = sqlite3.connect(DB_PATH, timeout=10)
    rows = conn.execute("SELECT term, source FROM lexicon").fetchall()
    conn.close()
    _LEX_EXACT    = {}
    _LEX_LIST     = []       # (term_orig, term_lower, source)
    _LEX_WORD_IDX = {}
    for t, s in rows:
        if not t:
            continue
        t_low = t.lower()
        idx   = len(_LEX_LIST)
        _LEX_LIST.append((t, t_low, s))
        if t not in _LEX_EXACT:
            _LEX_EXACT[t] = s
        # word-index: chỉ index term ngắn (≤60 chars = tên riêng, không phải định nghĩa)
        if len(t) <= 60:
            for word_raw in t_low.split():
                # Strip dấu câu đầu/cuối khỏi từ (vd: "đa." → "đa", "20.xà" → "xà")
                word = word_raw.strip('.,;:()[]!?"\'-/\\0123456789')
                if len(word) >= 2:
                    if word not in _LEX_WORD_IDX:
                        _LEX_WORD_IDX[word] = []
                    _LEX_WORD_IDX[word].append(idx)



def _lex_lookup(name_vi):
    """Tra từ điển theo name_vi. Trả '' nếu không tìm thấy."""
    if not name_vi:
        return ''
    _ensure_lex_cache()
    nm_lower = name_vi.lower()
    nm_parts = len(nm_lower.split())
    # Ngưỡng âm tiết tối thiểu cho Hướng 1:
    # term phải có ít nhất max(2, nm_parts-2) âm tiết để tránh match lẻ
    # VD "Ca" (1 âm) không được match "Mạt Điền Để Ca" (4 âm)
    min_t_parts = max(2, nm_parts - 2)
    # 1. Exact match O(1)
    if name_vi in _LEX_EXACT:
        return f"{name_vi} ({_abbr_source(_LEX_EXACT[name_vi])})"
    # 2. Word-index lookup: chỉ duyệt qua tập nhỏ ứng viên
    words = [w.lower() for w in name_vi.split() if len(w) >= 2]
    if not words:
        return ''
    # Dùng từ cuối (thường đặc trưng nhất) để lấy ứng viên
    candidates = _LEX_WORD_IDX.get(words[-1], [])
    if not candidates and len(words) > 1:
        candidates = _LEX_WORD_IDX.get(words[0], [])
    best = None  # (t_parts, t_display, s) — ưu tiên term dài nhất
    for idx in candidates:
        t, t_low, s = _LEX_LIST[idx]
        # Chỉ lấy term ngắn (≤60 chars) để tránh match definition dài
        if len(t) > 60:
            continue
        # Strip số thứ tự và dấu câu đầu/cuối term (vd: "20.Xà Dạ Đa.")
        t_clean = re.sub(r'^[\d\s\.\-\(\)]+|[\.\s\)]+$', '', t_low)
        t_display = re.sub(r'^[\d\s\.\-\(\)]+|[\.\s\)]+$', '', t).strip()
        t_parts = len(t_clean.split())
        # Hướng 2: nm == t_clean (exact word match)
        # Tránh false positive kiểu "Tông Giám" ⊂ "Thạch Sương Tông Giám"
        if nm_lower == t_clean:
            return f"{t_display or t} ({_abbr_source(s)})"
        # Hướng 1: term nằm trong nm (nm dài hơn → có tiền tố như "Tôn Giả", "TS.")
        # Yêu cầu: term ≥ min_t_parts âm tiết — tránh "Ca" match "Mạt Điền Để Ca"
        # Thu thập best (dài nhất) thay vì trả ngay → tránh "lúc 3 lúc 4 chữ"
        if t_clean and t_parts >= min_t_parts and t_clean in nm_lower:
            if best is None or t_parts > best[0]:
                best = (t_parts, t_display or t, s)
    if best:
        return f"{best[1]} ({_abbr_source(best[2])})"
    return ''


# ────────────────────────────────────────────────────────────────────────────────

def ensure_long_id(id_val):

    if id_val is None:
        return None
    s = str(id_val).strip()
    if s.startswith('PL') and len(s) < 15:
        num_part = s[2:]
        s = 'PL' + num_part.zfill(12)
    return s



# ==== Cache danh sách id theo cate (cho places_pending) ====
# Phân loại cate chỉ phụ thuộc places_dila.note_category → tính 1 lần (~100ms cho 59K dòng),
# rồi query qua index id thay vì full-scan 176K dòng + join tên miền dẫn xuất (~11.7s/request).
_CATE_IDS_CACHE = None



def _build_cate_ids_map():
    """Build dict cate → [id thực trong places_pending (cả dạng ngắn + dài)].
    Phân loại cate theo places_dila.note_category thông qua id dẫn xuất.
    Gọi 1 lần (~1-2s cho 176K dòng) rồi cache."""
    global _CATE_IDS_CACHE
    if _CATE_IDS_CACHE is not None:
        return _CATE_IDS_CACHE
    m = {}
    distinct = {}
    conn = get_db_connection()
    try:
        did_cate = {}
        for r in conn.execute("SELECT id, note_category FROM places_dila"):
            nc = (r['note_category'] or '')
            if '寺廟' in nc or '佛塔' in nc or '佛教文化地點' in nc:
                cate = 'temple_site'
            elif '山峰' in nc or '山脈' in nc:
                cate = 'mountain'
            elif '河流' in nc or '湖泊' in nc or '水系' in nc:
                cate = 'river_lake'
            elif '人文地理區域' in nc:
                cate = 'dynasty_region'
            elif '自然地理區域' in nc:
                cate = 'other'
            else:
                cate = 'admin_place'
            did_cate[str(r['id']).strip()] = cate
        for (pid, pzh, pnote) in conn.execute(
            "SELECT id, name_zh, note FROM places_pending"
        ):
            if not pid:
                continue
            pid = str(pid).strip()
            if not pid or not pzh or not pnote:
                continue
            num = pid[2:] if pid.startswith('PL') else pid
            cate = did_cate.get('PL' + num.zfill(12))
            if cate:
                m.setdefault(cate, []).append(pid)
                distinct.setdefault(cate, set()).add('PL' + num.zfill(12))
    finally:
        conn.close()
    _CATE_IDS_CACHE = {"ids": m, "distinct": {k: len(v) for k, v in distinct.items()}}
    return _CATE_IDS_CACHE




def _note_category_to_icon_type(nc, name_zh=''):
    """Map places_dila.note_category → canonical icon_type for Leaflet marker.
    Priority: DILA category field first, name-suffix fallback for ambiguous/missing.
    Spec: MAP_PLACE_TYPE_ICON_MISCLASSIFICATION_001."""
    nc = nc or ''
    nz = name_zh or ''
    if '寺廟' in nc or '佛塔' in nc or '佛教文化地點' in nc:
        return 'temple_site'
    if '山峰' in nc or '山脈' in nc:
        return 'mountain'
    if '河流' in nc or '湖泊' in nc or '水系' in nc or '海洋' in nc:
        return 'river_lake'
    if '人文地理區域' in nc:
        # Anchor to end of name to avoid false positives in transliterations (e.g. 興都庫什山)
        if re.search(r'[國国]$', nz): return 'country'
        if re.search(r'[省]$', nz): return 'province'
        if re.search(r'[州府路]$', nz): return 'prefecture'
        if re.search(r'[縣县郡]$', nz): return 'district'
        if re.search(r'[鎮镇]$', nz): return 'town'
        if re.search(r'[城都]$', nz): return 'city'
        return 'dynasty_region'
    if '自然地理區域' in nc:
        if re.search(r'[洞窟穴]', nz): return 'cave'
        if re.search(r'[關隘峽]', nz): return 'pass'
        return 'natural_region'
    if '非人界' in nc:
        return 'mythological'
    # Ambiguous (地點, 中研院歷史地名, empty) — strict name-suffix fallback only
    # Use compound keywords to avoid false positives (e.g. 藍 in 藍氏 ≠ 伽藍/temple)
    if re.search(r'寺|廟|塔|庵|精舍|伽藍|石窟', nz): return 'temple_site'
    if re.search(r'[山峰嶺崖岳丘]', nz): return 'mountain'
    if re.search(r'[江河湖溪潭海]', nz): return 'river_lake'
    if re.search(r'石窟|[洞穴]', nz): return 'cave'
    if re.search(r'[關隘峽]', nz): return 'pass'
    if re.search(r'[國国]', nz): return 'country'
    if re.search(r'[縣县郡]', nz): return 'district'
    if re.search(r'[州府]', nz): return 'prefecture'
    if re.search(r'[城都]', nz): return 'city'
    if re.search(r'[鎮镇]', nz): return 'town'
    return 'unknown'




# ==== Cache gợi ý lexicon (definition LIKE) cho ai_judge ====
# Query `definition LIKE '%han%'` full-scan bảng lexicon (166K dòng, ~21MB text) không dùng index được.
# Lần đầu sau restart server: disk cache lạnh → ~77s → vượt safeFetch 20s → placevn.html "Timeout!".
# Fix: nạp cả bảng (term, definition_lower) vào RAM 1 lần → substring scan ~100-300ms kể cả lạnh.
# Nhiều địa danh trùng tên Hán (~4.8x) nên cache theo han_name giúp click sau tức thì.
_lexicon_han_cache = {}


_LEXICON_HAN_CACHE_MAX = 500


_LEXICON_MEM = None



def _load_lexicon_mem(conn=None):
    """Load toàn bộ lexicon (term, definition_lower) vào RAM. RAM ~30-40MB, chấp nhận được."""
    global _LEXICON_MEM
    if _LEXICON_MEM is not None:
        return _LEXICON_MEM
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        rows = conn.execute("SELECT term, definition FROM lexicon").fetchall()
        _LEXICON_MEM = [(r['term'], (r['definition'] or '').lower()) for r in rows]
    except Exception:
        _LEXICON_MEM = []
    finally:
        if own:
            conn.close()
    return _LEXICON_MEM



def _lexicon_han_lookup(conn, han_name):
    """Tìm thuật ngữ lexicon có definition chứa han_name (substring, LIKE '%han%'), có cache in-memory.
    Dùng bản RAM nạp 1 lần để tránh full-scan disk ~77s khi cache lạnh."""
    if not han_name:
        return []
    cached = _lexicon_han_cache.get(han_name)
    if cached is not None:
        return cached
    han_low = han_name.lower()
    result = []
    mem = _load_lexicon_mem(conn)
    if mem:
        # SQLite LIKE '%x%' chỉ case-insensitive cho ASCII → so sánh lower() tương đương
        for term, def_low in mem:
            if len(term) < 100 and han_low in def_low:
                result.append(term)
                if len(result) >= 3:
                    break
    else:
        # RAM không tải được (hiếm) → fallback query LIKE cũ
        try:
            rows = conn.execute(
                "SELECT DISTINCT term FROM lexicon WHERE definition LIKE ? AND LENGTH(term) < 100 LIMIT 3",
                ('%' + han_name + '%',)
            ).fetchall()
            result = [r['term'] for r in rows]
        except Exception:
            result = []
    if len(_lexicon_han_cache) >= _LEXICON_HAN_CACHE_MAX:
        oldest = next(iter(_lexicon_han_cache))
        del _lexicon_han_cache[oldest]
    _lexicon_han_cache[han_name] = result
    return result



# ==== Đảm bảo bảng FTS5 places_search_fts có dữ liệu ====
# Cơ chế "gõ mớm" nhanh (FTS5): bảng đã tạo sẵn nhưng index rỗng.
# Populate 1 lần (~4-5s) khi index chưa có dữ liệu. Idempotent — không chạy lại nếu đã có.
# Lưu ý: COUNT(*) trên FTS5 rất chậm (~1.5s cho 118K docs) nên chỉ check 1 lần/process.
_FTS5_READY = {"places_search_fts": False, "places_pending_fts": False}



def ensure_places_search_fts(conn=None, force=False):
    """Populate places_search_fts từ namevi_map_places nếu index đang rỗng.
    Trả về True nếu vừa populate, False nếu đã có sẵn hoặc lỗi."""
    if _FTS5_READY["places_search_fts"] and not force:
        return False
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places_search_fts'"
        ).fetchone()
        if not exists:
            return False
        # T178 perf: COUNT docsize (148ms) + namevi COUNT (22ms) → LIMIT 1 (0.2ms)
        any_row = conn.execute("SELECT rowid FROM places_search_fts LIMIT 1").fetchone()
        if force or not any_row:
            conn.execute(
                "INSERT INTO places_search_fts(places_search_fts, rowid, name_vi, name_zh, dila_id) "
                "SELECT NULL, id, name_vi, name_zh, dila_id FROM namevi_map_places WHERE name_vi IS NOT NULL"
            )
            conn.commit()
            _FTS5_READY["places_search_fts"] = True
            return True
        _FTS5_READY["places_search_fts"] = True
        return False
    except Exception as e:
        return False
    finally:
        if own:
            conn.close()



def ensure_places_pending_fts(conn=None, force=False):
    """Đảm bảo bảng FTS5 places_pending_fts có dữ liệu.
    FTS thường (lưu nội dung, không external-content vì places_pending.id không unique).
    Cover cả địa danh chưa map + name_vi_norm (tìm không dấu). Populate 1 lần ~5-7s."""
    if _FTS5_READY["places_pending_fts"] and not force:
        return False
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='places_pending_fts'"
        ).fetchone()
        if not exists:
            conn.execute(
                "CREATE VIRTUAL TABLE places_pending_fts USING fts5(id, name_vi, name_zh, name_vi_norm)"
            )
            conn.commit()
        # T178 perf: tránh COUNT(*) 7.8s (JOIN) + 565ms (FTS) — chỉ cần biết FTS có dữ liệu không.
        # LIMIT 1 = 0.2ms; force=True mới cần rebuild đầy đủ.
        any_row = conn.execute("SELECT rowid FROM places_pending_fts LIMIT 1").fetchone()
        if force or not any_row:
            # 'delete-all' only works on contentless/external-content FTS5 tables —
            # this is a plain FTS5 table, so that special command always raised
            # "may only be used with a contentless or external content fts5 table"
            # and was silently swallowed by a try/except (pre-existing, not
            # introduced here) — every prior force-rebuild APPENDED a duplicate
            # copy instead of replacing rows. Found 2026-08-21 (row count doubled to
            # 236,599 after one force=True call while building T30). Plain DELETE
            # FROM is fully supported here.
            conn.execute("DELETE FROM places_pending_fts")
            # Source: COALESCE(namevi_map_places.name_vi, places_pending.name_vi) —
            # same pattern every other endpoint reading a place's name_vi uses.
            # Building straight from places_pending.name_vi alone (as before) meant
            # any name_vi living only in namevi_map_places never got indexed at all,
            # and any correction written to namevi_map_places (like T29's 14,982
            # retranslated rows) never showed up in search until a full rebuild.
            rows = conn.execute("""
                SELECT p.id, COALESCE(m.name_vi, p.name_vi) AS name_vi, p.name_zh
                FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE COALESCE(m.name_vi, p.name_vi) IS NOT NULL AND COALESCE(m.name_vi, p.name_vi) != ''
            """).fetchall()
            conn.executemany(
                "INSERT INTO places_pending_fts(id, name_vi, name_zh, name_vi_norm) VALUES (?, ?, ?, ?)",
                [(r['id'], r['name_vi'], r['name_zh'] or '', normalize_text(r['name_vi'])) for r in rows]
            )
            conn.commit()
            _FTS5_READY["places_pending_fts"] = True
            return True
        _FTS5_READY["places_pending_fts"] = True
        return False
    except Exception as e:
        return False
    finally:
        if own:
            conn.close()




# ─── HÁN-VIỆT CLEANUP ──────────────────────────────────────

_HV_CACHE = None



CUSTOM_HANVIET = {
    # Rare / difficult chars that are missing from hanviet_fallback
    "跋": "Bạt",
    "姞": "Cát",
    "邸": "Để",
    "磧": "Tích",
    "杲": "Cảo",
    "祐": "Hựu",
    "頤": "Di",
    "頊": "Húc",
    "頌": "Tụng",
    "頒": "Ban",
    "頓": "Đốn",
    "頗": "Phả",
    "頫": "Phủ",
    "頡": "Hiệt",
    "頣": "Thẩn",
    "頦": "Hài",
    "頲": "Đĩnh",
    "頳": "Sinh",
    "頴": "Dĩnh",
    "頵": "Quân",
    "頶": "Hốc",
    "頷": "Hàm",
    "頸": "Cảnh",
    "顆": "Khỏa",
    "餉": "Hưởng",
    "饋": "Quỹ",
    "饌": "Soạn",
    "饐": "Í",
    "饑": "Cơ",
    "饒": "Nhiêu",
    "饔": "Phung",
    "饕": "Thao",
    "饗": "Hưởng",
    "饘": "Chiên",
    "饜": "Yếm",
    "饝": "Ma",
    "驀": "Mạch",
    "驁": "Ngao",
    "驂": "Tham",
    "驃": "Phiếu",
    "驄": "Thông",
    "驊": "Hoa",
    "驍": "Kiêu",
    "驏": "Trản",
    "驐": "Đôn",
    "驑": "Lưu",
    "驒": "Đà",
    "驓": "Tằng",
    "驔": "Đàm",
    "驖": "Thiết",
    "驙": "Chiên",
    "驛": "Trạch",
    "驜": "Nghiệp",
    "驝": "Thác",
    "驞": "Tân",
    "驠": "Yến",
    "驡": "Long",
    "驢": "Lư",
    "驣": "Đằng",
    "驤": "Tương",
    "驥": "Ký",
    "驦": "Sương",
    "驧": "Cúc",
    "驨": "Hề",
    "驩": "Hoan",
    "驪": "Ly",
    "驫": "Phiêu",
    "驮": "Đà",
    "驯": "Tuần",
    "驰": "Trì",
    "驱": "Khu",
    "驳": "Bác",
    "驴": "Lư",
    "骡": "Loa",
    "骥": "Ký",
    "骧": "Tương",
    "龛": "Kham",
    "龠": "Dược",
    "龢": "Hòa",
    "龤": "Hài",
    # Additional chars from DILA toponyms
    "铠": "Khải",
    "铨": "Thuyên",
    "铉": "Huyễn",
    "铈": "Thị",
    "铊": "Tha",
    "铌": "Ni",
    "铍": "Phi",
    "铎": "Đạc",
    "铏": "Hình",
    "铐": "Cảo",
    "铑": "Lão",
    "铒": "Nhĩ",
    "铕": "Hữu",
    "铖": "Thành",
    "铗": "Kiệp",
    "铘": "Da",
    "铙": "Nao",
    "铚": "Trất",
    "铛": "Đang",
    "铜": "Đồng",
    "铝": "Lữ",
    "铟": "Nhân",
    "铠": "Khải",
    "铡": "Trát",
    "铢": "Thù",
    "铣": "Tiển",
    "铤": "Đĩnh",
    "铥": "Đâu",
    "铧": "Hoa",
    "铨": "Thuyên",
    "铩": "Sát",
    "铪": "Ha",
    "铫": "Diêu",
    "铬": "Các",
    "铭": "Minh",
    "铮": "Tránh",
    "铯": "Sắc",
    "铰": "Giảo",
    "铱": "Y",
    "铲": "Sản",
    "铳": "Xúng",
    "铴": "Thang",
    "铵": "An",
    "银": "Ngân",
    "铷": "Như",
    "铸": "Chú",
    "铹": "Lao",
    "铺": "Phố",
    "铻": "Ngô",
    "铼": "Lai",
    "铽": "Thác",
    "链": "Liên",
    "铿": "Khanh",
    "销": "Tiêu",
    "锁": "Tỏa",
    "锂": "Lý",
    "锃": "Tránh",
    "锄": "Sừ",
    "锅": "Oa",
    "锆": "Cáo",
    "锇": "Nga",
    "锉": "Tòa",
    "锊": "Lược",
    "锋": "Phong",
    "锌": "Tân",
    "锍": "Lưu",
    "锎": "Khai",
    "锏": "Giản",
    "锐": "Nhuệ",
    "锑": "Thế",
    "锒": "Lang",
    "锓": "Tẩm",
    "锔": "Cúc",
    "锕": "A",
    "锖": "Thương",
    "锗": "Giả",
    "锘": "Nặc",
    "错": "Thác",
    "锚": "Miêu",
    "锛": "Bôn",
    "锜": "Kỳ",
    "锝": "Đắc",
    "锞": "Khóa",
    "锟": "Côn",
    "锠": "Xương",
    "锡": "Tích",
    "锢": "Cố",
    "锣": "La",
    "锤": "Chùy",
    "锥": "Chùy",
    "锦": "Cẩm",
    "锧": "Chất",
    "锨": "Hân",
    "锩": "Quyển",
    "锪": "Hốt",
    "锫": "Bồi",
    "锬": "Đàm",
    "锭": "Đĩnh",
    "键": "Kiện",
    "锯": "Cứ",
    "锰": "Mãnh",
    "锱": "Tư",
    "锲": "Khiết",
    "锳": "Anh",
    "锴": "Khải",
    "锵": "Thương",
    "锶": "Tư",
    "锷": "Ngạc",
    "锸": "Tráp",
    "锹": "Thu",
    "锺": "Chung",
    "锻": "Đoán",
    "锼": "Sưu",
    "锽": "Hoàng",
    "锾": "Hoàn",
    "锿": "Ai",
    "镀": "Độ",
    "镁": "Mỹ",
    "镂": "Lũ",
    "镃": "Tư",
    "镄": "Phí",
    "镅": "My",
    "镆": "Mạc",
    "镇": "Trấn",
    "镈": "Bác",
    "镉": "Cách",
    "镊": "Nhiếp",
    "镋": "Thảng",
    "镌": "Thuyên",
    "镍": "Niết",
    "镎": "Nã",
    "镏": "Lưu",
    "镐": "Hạo",
    "镑": "Bảng",
    "镒": "Dật",
    "镓": "Gia",
    "镔": "Tân",
    "镕": "Dung",
    "镖": "Phiêu",
    "镗": "Đường",
    "镘": "Mạn",
    "镙": "La",
    "镚": "Bính",
    "镛": "Dung",
    "镜": "Kính",
    "镝": "Đích",
    "镞": "Tộc",
    "镟": "Tuyến",
    "镠": "Lưu",
    "镡": "Đàm",
    "镢": "Quật",
    "镣": "Liệu",
    "镤": "Phác",
    "镥": "Lỗ",
    "镦": "Đối",
    "镧": "Lan",
    "镨": "Phổ",
    "镩": "Thoán",
    "镪": "Cưỡng",
    "镫": "Đăng",
    "镬": "Hoạch",
    "镭": "Lôi",
    "镮": "Hoàn",
    "镯": "Trạc",
    "镰": "Liêm",
    "镱": "Ích",
    "镲": "Sáp",
    "镳": "Phiêu",
    "镴": "Lạp",
    "镵": "Sàm",
    "镶": "Tương",
    "镶": "Tương",
    "颋": "Đĩnh",
    "颍": "Dĩnh",
    "颎": "Cảnh",
    "颏": "Hài",
    "颐": "Di",
    "频": "Tần",
    "颔": "Hàm",
    "颈": "Cảnh",
    "颊": "Giáp",
    "颌": "Hợp",
    "颚": "Ngạc",
    "颛": "Chuyên",
    "颞": "Niếp",
    "颟": "Man",
    "颡": "Tảng",
    "颢": "Hạo",
    "颦": "Tần",
    "颧": "Quyền",
    "风": "Phong",
    "飏": "Dương",
    "飐": "Triển",
    "飑": "Tiêu",
    "飒": "Táp",
    "飓": "Cự",
    "飔": "Tư",
    "飕": "Sưu",
    "飖": "Diêu",
    "飗": "Lưu",
    "飘": "Phiêu",
    "飙": "Phiêu",
    "飚": "Phiêu",
    "飞": "Phi",
    "食": "Thực",
    "飧": "Tôn",
    "飨": "Hưởng",
    "飩": "Độn",
    "飪": "Nhẫm",
    "飫": "Ứ",
    "飬": "Dưỡng",
    "飭": "Sức",
    "飮": "Ẩm",
    "飯": "Phạn",
    "飰": "Phạn",
    "飱": "Tôn",
    "飲": "Ẩm",
    "飳": "Chú",
    "飴": "Di",
    "飵": "Trách",
    "飶": "Tất",
    "飷": "Giả",
    "飸": "Thao",
    "飹": "Cửu",
    "飺": "Từ",
    "飻": "Thiết",
    "飼": "Tự",
    "飽": "Bão",
    "飾": "Sức",
    "飿": "Đột",
    "餀": "Hại",
    "餁": "Nhậm",
    "餂": "Thiểm",
    "餃": "Giáo",
    "餄": "Hạt",
    "餅": "Bính",
    "餆": "Diêu",
    "餇": "Đồng",
    "餈": "Từ",
    "餉": "Hưởng",
    "養": "Dưỡng",
    "餌": "Nhĩ",
    "餎": "Lạc",
    "餏": "Ti",
    "餐": "Xan",
    "餑": "Bột",
    "餒": "Nỗi",
    "餓": "Ngạ",
    "餔": "Bố",
    "餕": "Tuấn",
    "餖": "Đậu",
    "餗": "Tốc",
    "餘": "Dư",
    "餙": "Sức",
    "餚": "Dao",
    "餛": "Hồn",
    "餜": "Quả",
    "餝": "Sức",
    "餞": "Tiễn",
    "餟": "Chuyết",
    "餠": "Bính",
    "餡": "Hãm",
    "餢": "Bộc",
    "餣": "Yếp",
    "餤": "Đàm",
    "餥": "Phỉ",
    "餧": "Nỗi",
    "館": "Quán",
    "餩": "Ác",
    "餪": "Noãn",
    "餫": "Vận",
    "餬": "Hồ",
    "餭": "Hoàng",
    "餮": "Thiết",
    "餯": "Huệ",
    "餰": "Chiên",
    "餲": "Ái",
    "餳": "Đường",
    "餴": "Phân",
    "餵": "Ủy",
    "餶": "Cốt",
    "餷": "Sát",
    "餸": "Tống",
    "餹": "Đường",
    "餺": "Bạc",
    "餻": "Cao",
    "餼": "Hí",
    "餽": "Quỹ",
    "餾": "Lựu",
    "餿": "Sưu",
    "饀": "Đào",
    "饁": "Diệp",
    "饂": "Uẩn",
    "饃": "Mô",
    "饄": "Đường",
    "饅": "Mạn",
    "饆": "Tất",
    "饇": "Ốc",
    "饈": "Tu",
    "饉": "Cận",
    "饊": "Tản",
    "饋": "Quỹ",
    "饌": "Soạn",
    "饍": "Thiện",
    "饎": "Xí",
    "饏": "Đạm",
    "饐": "Í",
    "饑": "Cơ",
    "饒": "Nhiêu",
    "饔": "Phung",
}



_MISSING_HANZI = {}



def _ensure_missing_hanzi_table():
    """Create missing_hanzi table if not exists."""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS missing_hanzi (
                char TEXT PRIMARY KEY,
                count INTEGER DEFAULT 1,
                last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()



def _log_missing_hanzi(char):
    """Upsert missing hanzi character into tracking table."""
    if char in _MISSING_HANZI:
        return  # Already logged this session
    _MISSING_HANZI[char] = True
    try:
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO missing_hanzi (char, count, last_seen_at)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(char) DO UPDATE SET
                    count = count + 1,
                    last_seen_at = CURRENT_TIMESTAMP
            """, (char,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass  # Non‑critical; silently ignore DB errors



def _ensure_custom_hanviet_override_table():
    """Create custom_hanviet_override table if not exists (T08 admin override)."""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_hanviet_override (
                char TEXT PRIMARY KEY,
                hanviet TEXT NOT NULL,
                added_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()



def _load_custom_hanviet_overrides():
    """Merge admin-added overrides (custom_hanviet_override table) into the
    in-memory CUSTOM_HANVIET dict so they take effect immediately, without
    editing the CUSTOM_HANVIET literal in source. Highest priority (checked
    first in _ensure_vietnamese), same as hardcoded CUSTOM_HANVIET entries."""
    _ensure_custom_hanviet_override_table()
    try:
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT char, hanviet FROM custom_hanviet_override").fetchall()
            for r in rows:
                CUSTOM_HANVIET[r['char']] = r['hanviet']
        finally:
            conn.close()
    except Exception:
        pass



def _init_hv_cache():
    global _HV_CACHE
    if _HV_CACHE is not None:
        return
    _HV_CACHE = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT ch, hv FROM hanviet_fallback").fetchall()
        for r in rows:
            _HV_CACHE[r[0]] = r[1]
        conn.close()
    except Exception:
        _HV_CACHE = {}
    _ensure_missing_hanzi_table()
    _load_custom_hanviet_overrides()



CUSTOM_HANVIET["奘"] = "Trạng"



def _ensure_vietnamese(text):
    """Replace CJK chars with Hán‑Việt readings; skip unknown chars.
    Priority: 1) CUSTOM_HANVIET 2) hanviet_fallback 3) skip (log as missing)."""
    if not text:
        return text or ''
    _init_hv_cache()
    result = []
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            hv = CUSTOM_HANVIET.get(c)
            if hv:
                result.append(hv)
                continue
            hv = _HV_CACHE.get(c) if _HV_CACHE else None
            if hv:
                result.append(hv)
            else:
                # Char unknown → skip it, log to missing_hanzi
                _log_missing_hanzi(c)
        else:
            result.append(c)
    cleaned = ''.join(result)
    # Remove any remaining Japanese/Chinese characters (safety net)
    cleaned = re.sub(r'[\u3040-\u30FF\u3400-\u4DBF]', '', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned



def _hanviet_charwise_translit(name_zh):
    """T372 — Phiên âm Hán-Việt charwise: ghép âm Hán-Việt của từng chữ Hán
    (CUSTOM_HANVIET ưu tiên, sau đó hanviet_fallback/_HV_CACHE), viết hoa chữ
    đầu mỗi âm, nối bằng khoảng trắng. Cùng thuật toán với
    /daoanh/api/admin/person/<id>/revalidate-hv (T172) — tái dùng ở đây để
    tránh viết lại khác hành vi.

    ĐÂY LÀ SUY LUẬN TỰ ĐỘNG, KHÔNG phải tên nguồn DILA (source_id=1) hay
    ZQLOCAL (source_id=5) đã xác thực — nơi gọi hàm này phải tự badge rõ
    "charwise"/suy luận tự động, không gán nhầm source DILA/ZQLOCAL.

    Trả về (charwise, unknown_chars): charwise='' nếu name_zh rỗng hoặc
    không có Hán tự nào; unknown_chars là list các chữ Hán không tra được âm.
    """
    name_zh = (name_zh or '').strip()
    if not name_zh:
        return '', []
    _init_hv_cache()
    parts = []
    unknown_chars = []
    for c in name_zh:
        if '一' <= c <= '鿿':
            hv = CUSTOM_HANVIET.get(c) or (_HV_CACHE.get(c) if _HV_CACHE else None)
            if hv:
                parts.append(hv[0].upper() + hv[1:] if len(hv) > 1 else hv.upper())
            else:
                parts.append(c)
                unknown_chars.append(c)
        elif c.strip():
            parts.append(c)
    charwise = ' '.join(parts)
    return charwise, unknown_chars



def _normalize_charwise_caps(charwise):
    """T372 — Viết hoa chữ đầu mỗi âm tiết của chuỗi charwise (phòng trường hợp
    person_hanviet_debug.han_viet_charwise có vài dòng bị lưu không nhất quán
    hoa/thường, ví dụ 'Huệ năng' → 'Huệ Năng'). Không đổi nghĩa/âm, chỉ chuẩn hóa
    hiển thị."""
    if not charwise:
        return charwise
    return ' '.join(
        (w[0].upper() + w[1:]) if w else w
        for w in charwise.split(' ')
    )



TAM_DICH_SUFFIX = ' (Tạm dịch)'



# ── T22.1 Approval Gates ──────────────────────────────────────────────────────
_T221_APPROVALS_FILE = os.path.join(BASE_DIR, 'data', 't22_1_approvals.json')



def _t221_load():
    try:
        with open(_T221_APPROVALS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}



def _t221_save(data):
    with open(_T221_APPROVALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────

# Known Chinese dynasty/kingdom names. Whether a name refers to a historical
# ruling dynasty is a structural fact, not a translation judgment call, so a
# curated exact-match list is used (kept intentionally narrow to avoid
# false-positive matches against unrelated place names that share a common
# single character). Only consulted when name_vi is already empty.
DYNASTY_NAMES = {
    '夏', '商', '周', '秦', '漢', '西漢', '東漢', '新',
    '魏', '蜀', '蜀漢', '吳', '東吳', '晉', '西晉', '東晉',
    '劉宋', '南齊', '梁', '陳',
    '北魏', '東魏', '西魏', '北齊', '北周',
    '隋', '唐',
    '後梁', '後唐', '後晉', '後漢', '後周',
    '吳越', '南唐', '閩', '荊南', '北漢',
    '遼', '西遼', '北宋', '南宋', '金', '西夏',
    '元', '明', '南明', '清', '清朝',
}



# Dynasty names cross-checked against Vietnamese Wikipedia on 2026-08-13
# (https://vi.wikipedia.org/wiki/Nhà_Liêu, https://vi.wikipedia.org/wiki/Nhà_Thanh)
# - returned as-is, WITHOUT the "(Tạm dịch)" tag, since these are confirmed
# against a real external source, not machine-guessed. Everything else in
# DYNASTY_NAMES still falls back to _translate_zh_term()'s own lexicon/Hán-Việt
# logic and keeps its tentative tag until someone verifies and adds it here.
WEB_VERIFIED_DYNASTY_VI = {
    '遼': 'Liêu',
    '清朝': 'Thanh',
    '清': 'Thanh',
}




def _translate_dynasty_name(name_zh, conn):
    """
    If name_zh is a known dynasty/kingdom name, return 'Nhà <ten>'.
    Returns None if name_zh isn't a recognized dynasty (caller should fall
    back to plain _translate_zh_term()).
    """
    if name_zh not in DYNASTY_NAMES:
        return None
    core = WEB_VERIFIED_DYNASTY_VI.get(name_zh) or _translate_zh_term(name_zh, conn)
    return f'Nhà {core}' if core else None




def _translate_zh_term(seg, conn):
    """
    Translate a single Chinese term/phrase to Vietnamese.
    Priority: 1) exact lexicon term match (confirmed dictionary translation,
    returned as-is, NO tentative marker). 2) _ensure_vietnamese() char-by-char
    Hán-Việt fallback (NOT a verified official translation - always suffixed
    with "(Tạm dịch)" so an admin knows to verify it manually later; the code
    must never present a guessed reading as if it were confirmed).
    Returns '' if seg is empty.
    """
    seg = (seg or '').strip()
    if not seg:
        return ''
    key = normalize_text(seg)
    row = conn.execute(
        "SELECT term FROM lexicon WHERE key_norm = ? AND LENGTH(term) < 60 ORDER BY priority ASC LIMIT 1",
        (key,)
    ).fetchone()
    if row and row['term'] and row['term'] != seg:
        return row['term']  # confirmed dictionary translation
    # Fallback: Hán-Việt reading, spaced between CJK syllables only — runs of
    # non-CJK text (Latin, Cyrillic, digits, punctuation) are left untouched
    # instead of being exploded into single spaced-out characters.
    # This is a guess, not a verified official name -> must be flagged.
    out = []
    prev_was_han = False
    has_han = False
    for c in seg:
        if '一' <= c <= '鿿':
            hv = _ensure_vietnamese(c)
            if hv:
                if out and prev_was_han:
                    out.append(' ')
                out.append(hv)
                has_han = True
            prev_was_han = True
        else:
            out.append(c)
            prev_was_han = False
    guess = ''.join(out).strip()
    if not guess:
        return seg  # totally unmappable -> leave raw rather than silently drop
    if has_han:
        guess = title_case_vi(guess)
    return guess + TAM_DICH_SUFFIX




def _translate_admin_text(text, conn=None):
    """
    Convert a Chinese admin-division string (e.g. '中國-廣西壯族自治區-來賓市-忻城縣'
    or with ';' between multiple regions) to Vietnamese for display, segment by
    segment via _translate_zh_term(). Never leaves raw CJK on the page; any
    non-dictionary-confirmed segment is marked "(Tạm dịch)".
    """
    if not text:
        return text or ''
    own_conn = conn is None
    if own_conn:
        conn = get_db_connection()
    try:
        parts = []
        for region in text.split(';'):
            sub_parts = [_translate_zh_term(p, conn) for p in region.split('-')]
            parts.append(' - '.join(p for p in sub_parts if p))
        return '; '.join(p for p in parts if p)
    finally:
        if own_conn:
            conn.close()




def title_case_vi(text):
    """Viết hoa chữ cái đầu mỗi từ cho chuỗi tiếng Việt, giữ nguyên dấu và khoảng trắng."""
    if not text or not isinstance(text, str):
        return text or ''
    return ' '.join(w.capitalize() for w in text.strip().split())



COUNTRY_MAP = {
    '阿富汗': 'Afghanistan',
    '中國': 'Trung Quốc',
    '中国': 'Trung Quốc',
    '印度': 'Ấn Độ',
    '巴基斯坦': 'Pakistan',
    '尼泊爾': 'Nepal',
    '尼泊尔': 'Nepal',
    '緬甸': 'Myanmar',
    '缅甸': 'Myanmar',
    '斯里蘭卡': 'Sri Lanka',
    '孟加拉': 'Bangladesh',
    '日本': 'Nhật Bản',
    '韓國': 'Hàn Quốc',
    '蒙古': 'Mông Cổ',
    '泰國': 'Thái Lan',
    '寮國': 'Lào',
    '柬埔寨': 'Campuchia',
    '印尼': 'Indonesia',
    '馬來西亞': 'Malaysia',
    '菲律賓': 'Philippines',
    '新加坡': 'Singapore',
    '西藏': 'Tây Tạng',
    '新疆': 'Tân Cương',
}



ADMIN_LEVEL_MAP = {
    '省': 'tỉnh', '市': 'thành phố', '縣': 'huyện',
    '县': 'huyện', '区': 'quận', '區': 'quận',
    '镇': 'trấn', '鎮': 'trấn', '乡': 'xã', '鄉': 'xã',
}



CHINESE_PLACE_NAMES = {
    # 34 tỉnh
    '雲南': 'Vân Nam', '河北': 'Hà Bắc', '山西': 'Sơn Tây',
    '山東': 'Sơn Đông', '河南': 'Hà Nam', '湖南': 'Hồ Nam',
    '廣東': 'Quảng Đông', '廣西': 'Quảng Tây', '四川': 'Tứ Xuyên',
    '福建': 'Phúc Kiến', '江蘇': 'Giang Tô', '浙江': 'Chiết Giang',
    '安徽': 'An Huy', '江西': 'Giang Tây', '湖北': 'Hồ Bắc',
    '貴州': 'Quý Châu', '陝西': 'Thiểm Tây', '甘肅': 'Cam Túc',
    '遼寧': 'Liêu Ninh', '吉林': 'Cát Lâm', '黑龍江': 'Hắc Long Giang',
    '海南': 'Hải Nam', '青海': 'Thanh Hải', '台灣': 'Đài Loan',
    '新疆': 'Tân Cương', '西藏': 'Tây Tạng', '內蒙古': 'Nội Mông Cổ',
    '寧夏': 'Ninh Hạ',
    # Trực hạt thị (municipalities)
    '北京': 'Bắc Kinh', '上海': 'Thượng Hải', '天津': 'Thiên Tân',
    '重慶': 'Trùng Khánh', '香港': 'Hồng Kông', '澳門': 'Ma Cao',
    # Thành phố + địa danh nổi
    '洛陽': 'Lạc Dương', '西安': 'Tây An', '成都': 'Thành Đô',
    '昆明': 'Côn Minh', '南京': 'Nam Kinh', '杭州': 'Hàng Châu',
    '武漢': 'Vũ Hán', '長沙': 'Trường Sa', '廣州': 'Quảng Châu',
    '大理': 'Đại Lý', '敦煌': 'Đôn Hoàng', '開封': 'Khai Phong',
    '曲靖': 'Khúc Tĩnh', '富源': 'Phú Nguyên', '昭通': 'Chiêu Thông',
    '太原': 'Thái Nguyên', '瀋陽': 'Thẩm Dương', '濟南': 'Tế Nam',
    '福州': 'Phúc Châu', '南昌': 'Nam Xương', '貴陽': 'Quý Dương',
    '蘭州': 'Lan Châu', '西寧': 'Tây Ninh',
    # Quận/huyện phổ biến
    '海淀': 'Hải Điện', '朝阳': 'Triều Dương', '浦东': 'Phố Đông',
    '天山': 'Thiên Sơn', '武侯': 'Vũ Hầu', '錦江': 'Cẩm Giang',
    # Khu tự trị — name_raw sau khi bỏ hậu tố 區
    '新疆維吾爾自治': 'Tân Cương', '西藏自治': 'Tây Tạng',
    '內蒙古自治': 'Nội Mông Cổ', '廣西壯族自治': 'Quảng Tây',
    '寧夏回族自治': 'Ninh Hạ', '延邊朝鮮族自治': 'Diên Biên',
    '恩施土家族苗族自治': 'Ân Thi', '黔東南苗族侗族自治': 'Kiềm Đông Nam',
    '黔南布依族苗族自治': 'Kiềm Nam', '黔西南布依族苗族自治': 'Kiềm Tây Nam',
    '湘西土家族苗族自治': 'Tương Tây', '伊犁哈薩克自治': 'Y Lê',
    '甘孜藏族自治': 'Cam Tư', '阿壩藏族羌族自治': 'A Bá',
    '涼山彝族自治': 'Lương Sơn', '德宏傣族景頗族自治': 'Đức Hoằng',
    '怒江傈僳族自治': 'Nộ Giang', '迪慶藏族自治': 'Địch Khánh',
    '大理白族自治': 'Đại Lý', '西雙版納傣族自治': 'Tây Song Bản Nạp',
    '文山壯族苗族自治': 'Văn Sơn', '紅河哈尼族彝族自治': 'Hồng Hà',
    '楚雄彝族自治': 'Sở Hùng', '保山自治': 'Bảo Sơn',
    # Thêm địa danh lịch sử Phật giáo
    '罽賓': 'Kế Tân', '健馱邏': 'Kiền Đà La', '鳥萇': 'Ô Trường',
    '鉢羅': 'Bát La', '迦濕彌羅': 'Ca Thấp Di La',
    # Khu tự trị cấp địa khu Tân Cương — name_raw sau khi bỏ hậu tố 州
    '伊犁哈薩克自治': 'Y Lê Kazakh', '博爾塔拉蒙古自治': 'Bác Nhĩ Tháp La Mông Cổ',
    '巴音郭楞蒙古自治': 'Ba Âm Quách Lăng Mông Cổ', '昌吉回族自治': 'Xương Cát Hồi',
    '克孜勒蘇柯爾克孜自治': 'Khắc Tư Lặc Tô', '塔城地區': 'Tháp Thành',
    # Tây Tạng
    '那曲地': 'Na Khúc', '阿里地': 'A Lý', '日喀則地': 'Nhật Khách Tắc',
    '山南地': 'Sơn Nam', '林芝地': 'Lâm Chi', '昌都地': 'Xương Đô',
    # Vân Nam
    '迪慶藏族自治': 'Địch Khánh', '怒江傈僳族自治': 'Nộ Giang',
    '德宏傣族景頗族自治': 'Đức Hoằng', '臨滄地': 'Lâm Thương',
    # Nội Mông
    '鄂爾多斯': 'Ngạc Nhĩ Đa Tư', '巴彥淖爾': 'Ba Ngạn Nạo Nhĩ',
    '烏蘭察布': 'Ô Lan Sát Bố', '錫林郭勒盟': 'Tích Lâm Quách Lặc',
    '興安': 'Hưng An', '呼倫貝爾': 'Hô Luân Bối Nhĩ',
}



MUNICIPALITIES = {'北京', '上海', '天津', '重慶', '香港', '澳門'}



# Hán-Việt character-by-character lookup table — fallback for place names not in CHINESE_PLACE_NAMES
HAN_VIET_CHAR = {
    # Directions & positions
    '東': 'Đông', '东': 'Đông', '西': 'Tây', '南': 'Nam', '北': 'Bắc',
    '中': 'Trung', '上': 'Thượng', '下': 'Hạ', '內': 'Nội', '内': 'Nội',
    '外': 'Ngoại', '左': 'Tả', '右': 'Hữu', '前': 'Tiền', '後': 'Hậu',
    # Water & terrain
    '河': 'Hà', '江': 'Giang', '湖': 'Hồ', '海': 'Hải', '洋': 'Dương',
    '川': 'Xuyên', '水': 'Thủy', '泉': 'Tuyền', '浦': 'Phố', '洲': 'Châu',
    '灘': 'Than', '渡': 'Độ', '池': 'Trì', '溪': 'Khê', '浜': 'Bằng',
    '洛': 'Lạc', '淮': 'Hoài', '漢': 'Hán', '汉': 'Hán', '滄': 'Thương',
    '沧': 'Thương', '漯': 'Lạp', '汾': 'Phần', '涇': 'Kinh', '渭': 'Vị',
    '瀘': 'Lô', '沂': 'Nghi', '沭': 'Thuật', '泗': 'Tứ', '沔': 'Miện',
    '沱': 'Đà', '岷': 'Mân', '嘉': 'Gia', '陵': 'Lăng', '烏': 'Ô', '乌': 'Ô',
    '濮': 'Bộc', '洹': 'Hoàn', '潁': 'Dĩnh', '穎': 'Dĩnh', '荊': 'Kinh',
    '荆': 'Kinh', '贛': 'Cám', '赣': 'Cám', '鄱': 'Bà', '洞': 'Động',
    '太': 'Thái', '涿': 'Trác', '濱': 'Tân', '滨': 'Tân', '滁': 'Trừ',
    '蕪': 'Vu', '芜': 'Vu', '蒲': 'Bồ', '淄': 'Tri', '沁': 'Tẩm',
    '沅': 'Nguyên', '澧': 'Lễ', '沅': 'Nguyên', '舒': 'Thư',
    # Mountains & terrain
    '山': 'Sơn', '嶺': 'Lĩnh', '岳': 'Nhạc', '峰': 'Phong', '嶺': 'Lĩnh',
    '原': 'Nguyên', '坡': 'Ba', '崖': 'Nhai', '谷': 'Cốc', '峽': 'Hiệp',
    '峡': 'Hiệp', '坪': 'Bình', '壁': 'Bích', '崗': 'Cương', '岗': 'Cương',
    '嵩': 'Tung', '嶽': 'Nhạc', '崆': 'Không', '峒': 'Động', '太': 'Thái',
    '岩': 'Nham',
    # Administrative units
    '省': 'Tỉnh', '州': 'Châu', '府': 'Phủ', '縣': 'Huyện', '县': 'Huyện',
    '鎮': 'Trấn', '镇': 'Trấn', '鄉': 'Hương', '乡': 'Hương', '村': 'Thôn',
    '城': 'Thành', '道': 'Đạo', '路': 'Lộ', '坊': 'Phường', '堡': 'Bảo',
    '屯': 'Đồn', '寨': 'Trại', '場': 'Trường', '场': 'Trường',
    '區': 'Khu', '区': 'Khu', '鋪': 'Phố', '鄰': 'Lân', '塘': 'Đường',
    '壩': 'Bá', '坝': 'Bá', '埔': 'Phố', '灣': 'Loan', '湾': 'Loan',
    '橋': 'Kiều', '桥': 'Kiều', '關': 'Quan', '关': 'Quan',
    '口': 'Khẩu', '門': 'Môn', '门': 'Môn', '埠': 'Phụ',
    # Common name chars
    '安': 'An', '寧': 'Ninh', '宁': 'Ninh', '定': 'Định', '平': 'Bình',
    '通': 'Thông', '順': 'Thuận', '顺': 'Thuận', '昌': 'Xương', '興': 'Hưng',
    '兴': 'Hưng', '盛': 'Thịnh', '武': 'Vũ', '文': 'Văn', '朝': 'Triều',
    '大': 'Đại', '小': 'Tiểu', '新': 'Tân', '古': 'Cổ', '老': 'Lão',
    '長': 'Trường', '长': 'Trường', '永': 'Vĩnh', '常': 'Thường',
    '廣': 'Quảng', '广': 'Quảng', '慶': 'Khánh', '庆': 'Khánh',
    '福': 'Phúc', '壽': 'Thọ', '寿': 'Thọ', '德': 'Đức', '泰': 'Thái',
    '光': 'Quang', '明': 'Minh', '靈': 'Linh', '灵': 'Linh', '清': 'Thanh',
    '高': 'Cao', '遠': 'Viễn', '远': 'Viễn', '仁': 'Nhân', '義': 'Nghĩa',
    '义': 'Nghĩa', '宜': 'Nghi', '信': 'Tín', '忠': 'Trung', '固': 'Cố',
    '崇': 'Sùng', '宣': 'Tuyên', '承': 'Thừa', '慎': 'Thận', '惠': 'Huệ',
    '嘉': 'Gia', '隆': 'Long', '祥': 'Tường', '瑞': 'Thụy', '吉': 'Cát',
    # Colours
    '黃': 'Hoàng', '黄': 'Hoàng', '紅': 'Hồng', '红': 'Hồng', '白': 'Bạch',
    '黑': 'Hắc', '青': 'Thanh', '綠': 'Lục', '绿': 'Lục', '金': 'Kim',
    '銀': 'Ngân', '银': 'Ngân',
    # Materials/nature
    '石': 'Thạch', '木': 'Mộc', '土': 'Thổ', '火': 'Hoả', '鐵': 'Thiết',
    '铁': 'Thiết', '銅': 'Đồng', '铜': 'Đồng', '玉': 'Ngọc', '珠': 'Châu',
    '松': 'Tùng', '柏': 'Bách', '梅': 'Mai', '柳': 'Liễu', '桂': 'Quế',
    '竹': 'Trúc', '蘭': 'Lan', '兰': 'Lan', '荷': 'Hà',
    # Animals
    '龍': 'Long', '龙': 'Long', '虎': 'Hổ', '鳳': 'Phụng', '凤': 'Phụng',
    '馬': 'Mã', '马': 'Mã', '鹿': 'Lộc', '鶴': 'Hạc', '鹤': 'Hạc',
    '燕': 'Yên', '雁': 'Nhạn', '鷹': 'Ưng',
    # Numbers
    '一': 'Nhất', '二': 'Nhị', '三': 'Tam', '四': 'Tứ', '五': 'Ngũ',
    '六': 'Lục', '七': 'Thất', '八': 'Bát', '九': 'Cửu', '十': 'Thập',
    '百': 'Bách', '千': 'Thiên', '萬': 'Vạn', '万': 'Vạn',
    # Province-level chars
    '雲': 'Vân', '云': 'Vân', '貴': 'Quý', '贵': 'Quý', '川': 'Xuyên',
    '蜀': 'Thục', '閩': 'Mân', '闽': 'Mân', '浙': 'Chiết', '徽': 'Huy',
    '蘇': 'Tô', '苏': 'Tô', '贛': 'Cám', '晉': 'Tấn', '晋': 'Tấn',
    '冀': 'Ký', '豫': 'Dự', '魯': 'Lỗ', '鲁': 'Lỗ', '鄂': 'Ngạc',
    '湘': 'Tương', '瓊': 'Quỳnh', '琼': 'Quỳnh', '遼': 'Liêu', '辽': 'Liêu',
    '寧': 'Ninh', '黔': 'Kiềm', '陝': 'Thiểm', '陕': 'Thiểm',
    '甘': 'Cam', '秦': 'Tần', '疆': 'Cương',
    # Major city chars
    '京': 'Kinh', '都': 'Đô', '陽': 'Dương', '阳': 'Dương', '漢': 'Hán',
    '津': 'Tân', '渝': 'Du', '漳': 'Chương', '汕': 'Sán', '廈': 'Hạ',
    '厦': 'Hạ', '莆': 'Bồ', '田': 'Điền', '蘇': 'Tô', '杭': 'Hàng',
    '鄭': 'Trịnh', '郑': 'Trịnh', '焦': 'Tiêu', '許': 'Hứa', '许': 'Hứa',
    '鶴': 'Hạc', '濟': 'Tế', '济': 'Tế', '聊': 'Liêu', '臨': 'Lâm',
    '临': 'Lâm', '萊': 'Lai', '菏': 'Hà', '威': 'Uy', '煙': 'Yên',
    '烟': 'Yên', '棗': 'Táo', '枣': 'Táo', '泰': 'Thái', '濰': 'Duy',
    '潍': 'Duy', '莒': 'Cử', '郯': 'Đàm', '沂': 'Nghi',
    '株': 'Chu', '婁': 'Lâu', '娄': 'Lâu', '衡': 'Hành', '邵': 'Thiệu',
    '懷': 'Hoài', '怀': 'Hoài', '邢': 'Hình', '衛': 'Vệ', '卫': 'Vệ',
    '涿': 'Trác', '唐': 'Đường', '皇': 'Hoàng', '島': 'Đảo', '岛': 'Đảo',
    '廊': 'Lang', '滄': 'Thương', '邯': 'Hàm', '鄲': 'Đan',
    '保': 'Bảo', '雄': 'Hùng', '深': 'Thâm', '珠': 'Châu', '湛': 'Trạm',
    '茂': 'Mậu', '名': 'Danh', '肇': 'Triệu', '揭': 'Yết', '潮': 'Triều',
    '梅': 'Mai', '浮': 'Phù', '韶': 'Thiều', '揚': 'Dương', '扬': 'Dương',
    '徐': 'Từ', '淮': 'Hoài', '連': 'Liên', '连': 'Liên', '鹽': 'Diêm',
    '盐': 'Diêm', '鎮': 'Trấn', '宿': 'Túc', '遷': 'Thiên', '迁': 'Thiên',
    '泰': 'Thái', '興': 'Hưng', '宜': 'Nghi', '紹': 'Thiệu', '绍': 'Thiệu',
    '金': 'Kim', '華': 'Hoa', '华': 'Hoa', '舟': 'Chu', '麗': 'Lệ', '丽': 'Lệ',
    '蘭': 'Lan', '溫': 'Ôn', '温': 'Ôn', '台': 'Đài', '臺': 'Đài',
    '合': 'Hợp', '肥': 'Phì', '蚌': 'Bạng', '馬': 'Mã', '鞍': 'Yên',
    '阜': 'Phụ', '六': 'Lục', '亳': 'Bạc', '宣': 'Tuyên', '枞': 'Tòng',
    '銅': 'Đồng', '池': 'Trì', '滁': 'Trừ', '運': 'Vận', '运': 'Vận',
    '遵': 'Tuân', '盤': 'Bàn', '盘': 'Bàn', '畢': 'Tất', '節': 'Tiết',
    '节': 'Tiết', '銅': 'Đồng', '仁': 'Nhân', '安': 'An',
    '普': 'Phổ', '洱': 'Nhĩ', '楚': 'Sở', '迪': 'Địch', '昭': 'Chiêu',
    '保': 'Bảo', '麗': 'Lệ', '版': 'Bản', '納': 'Nạp', '纳': 'Nạp',
    '勐': 'Mãnh', '雙': 'Song', '双': 'Song',
    # Xi'an area / Shaanxi
    '咸': 'Hàm', '漢': 'Hán', '渭': 'Vị', '澄': 'Trừng', '銅': 'Đồng',
    '延': 'Diên', '邊': 'Biên', '边': 'Biên', '榆': 'Du', '林': 'Lâm',
    '安': 'An', '康': 'Khang', '商': 'Thương', '洛': 'Lạc',
    # Gansu / Qinghai
    '蘭': 'Lan', '嘉': 'Gia', '峪': 'Dục', '酒': 'Tửu', '張': 'Trương',
    '张': 'Trương', '掖': 'Dịch', '武': 'Vũ', '金': 'Kim', '昌': 'Xương',
    '涼': 'Lương', '隴': 'Lũng', '陇': 'Lũng', '定': 'Định', '臨': 'Lâm',
    '慶': 'Khánh', '平': 'Bình', '白': 'Bạch', '吳': 'Ngô', '吴': 'Ngô',
    # Ningxia
    '石': 'Thạch', '嘴': 'Chủy', '固': 'Cố', '隆': 'Long', '靈': 'Linh',
    '中': 'Trung', '衛': 'Vệ',
    # Xinjiang
    '烏': 'Ô', '魯': 'Lỗ', '木': 'Mộc', '齊': 'Tề', '齐': 'Tề',
    '克': 'Khắc', '拉': 'Lạp', '瑪': 'Mã', '依': 'Y', '阿': 'A',
    '庫': 'Khố', '库': 'Khố', '爾': 'Nhĩ', '尔': 'Nhĩ', '勒': 'Lặc',
    '霍': 'Hoắc', '圖': 'Đồ', '图': 'Đồ', '吐': 'Thổ', '哈': 'Cáp',
    '番': 'Phiên', '喀': 'Khách', '什': 'Thập', '米': 'Mễ',
    # Tibet
    '拉': 'Lạp', '薩': 'Tát', '萨': 'Tát', '日': 'Nhật', '喀': 'Khách',
    '則': 'Tắc', '则': 'Tắc', '貢': 'Cống', '贡': 'Cống',
    # Inner Mongolia
    '包': 'Bao', '頭': 'Đầu', '头': 'Đầu', '赤': 'Xích', '呼': 'Hô',
    '和': 'Hòa', '浩': 'Hạo', '特': 'Đặc', '鄂': 'Ngạc', '多': 'Đa',
    '斯': 'Tư', '錫': 'Tích', '郭': 'Quách', '善': 'Thiện', '巴': 'Ba',
    '彥': 'Yến', '源': 'Nguyên',
    # Northeast
    '瀋': 'Thẩm', '沈': 'Thẩm', '撫': 'Phủ', '本': 'Bản', '錦': 'Cẩm',
    '丹': 'Đan', '鴨': 'Áp', '綠': 'Lục', '春': 'Xuân', '四': 'Tứ',
    '松': 'Tùng', '牡': 'Mẫu', '佳': 'Giai', '慶': 'Khánh', '伊': 'Y',
    '七': 'Thất', '雞': 'Kê', '崗': 'Cương', '綏': 'Tuy', '化': 'Hóa',
    # Historical/Buddhist geography
    '汴': 'Biện', '宋': 'Tống', '鄆': 'Vận', '曹': 'Tào', '濮': 'Bộc',
    '兗': 'Duyện', '齊': 'Tề', '青': 'Thanh', '萊': 'Lai', '登': 'Đăng',
    '萊': 'Lai', '密': 'Mật', '膠': 'Giao', '膳': 'Thiện', '泗': 'Tứ',
    '睢': 'Tuy', '沛': 'Bái', '彭': 'Bành', '城': 'Thành', '穎': 'Dĩnh',
    '蔡': 'Thái', '汝': 'Nhữ', '鄭': 'Trịnh', '鄢': 'Yên', '陳': 'Trần',
    '陈': 'Trần', '潁': 'Dĩnh', '汴': 'Biện', '魏': 'Ngụy', '韓': 'Hàn',
    '韩': 'Hàn', '趙': 'Triệu', '赵': 'Triệu', '燕': 'Yên', '楚': 'Sở',
    '吳': 'Ngô', '越': 'Việt', '秦': 'Tần', '漢': 'Hán', '唐': 'Đường',
    '宋': 'Tống', '元': 'Nguyên', '明': 'Minh', '清': 'Thanh',
    '隋': 'Tùy', '晉': 'Tấn', '魏': 'Ngụy', '蜀': 'Thục', '吳': 'Ngô',
    '齊': 'Tề', '樑': 'Lương', '梁': 'Lương', '陳': 'Trần',
    # More city chars
    '攀': 'Phan', '枝': 'Chi', '花': 'Hoa', '綿': 'Miên', '廣': 'Quảng',
    '自': 'Tự', '貢': 'Cống', '資': 'Tư', '陽': 'Dương', '瀘': 'Lô',
    '德': 'Đức', '宜': 'Nghi', '南': 'Nam', '充': 'Sung', '達': 'Đạt',
    '达': 'Đạt', '巴': 'Ba', '中': 'Trung', '廣': 'Quảng', '元': 'Nguyên',
    '甘': 'Cam', '孜': 'Tư', '涼': 'Lương', '山': 'Sơn', '樂': 'Lạc',
    '撫': 'Phủ', '州': 'Châu', '眉': 'Mi', '雅': 'Nhã', '安': 'An',
    '康': 'Khang', '阿': 'A', '壩': 'Bá', '涼': 'Lương',
    '北': 'Bắc', '海': 'Hải', '防': 'Phòng', '欽': 'Khâm', '钦': 'Khâm',
    '崇': 'Sùng', '左': 'Tả', '百': 'Bách', '色': 'Sắc', '賀': 'Hạ',
    '贺': 'Hạ', '賀': 'Hạ', '來': 'Lai', '来': 'Lai', '玉': 'Ngọc',
    '河': 'Hà', '貴': 'Quý', '港': 'Cảng', '欽': 'Khâm',
    '荊': 'Kinh', '宜': 'Nghi', '恩': 'Ân', '施': 'Thi', '隨': 'Tùy',
    '襄': 'Tương', '樊': 'Phàn', '黃': 'Hoàng', '孝': 'Hiếu', '感': 'Cảm',
    '咸': 'Hàm', '鄂': 'Ngạc', '黃': 'Hoàng', '石': 'Thạch',
    '萍': 'Bình', '贛': 'Cám', '吉': 'Cát', '撫': 'Phủ', '宜': 'Nghi',
    '景': 'Cảnh', '德': 'Đức', '九': 'Cửu', '江': 'Giang', '新': 'Tân',
    '余': 'Dư', '上': 'Thượng', '饒': 'Nhiêu', '鷹': 'Ưng', '潭': 'Đàm',
    # Long Hòa area
    '龍': 'Long', '岩': 'Nham', '南': 'Nam', '平': 'Bình', '三': 'Tam',
    '明': 'Minh', '泉': 'Tuyền', '州': 'Châu',
    # Misc
    '汴': 'Biện', '雒': 'Lạc', '邑': 'Ấp', '鄉': 'Hương', '堡': 'Bảo',
    '嶺': 'Lĩnh', '坡': 'Ba', '岡': 'Cương', '丘': 'Khâu', '陵': 'Lăng',
    '墟': 'Khư', '埠': 'Phụ', '渡': 'Độ', '峠': 'Thượng',
    '塔': 'Tháp', '寺': 'Tự', '廟': 'Miếu', '庵': 'Am', '觀': 'Quan',
    '宮': 'Cung', '院': 'Viện', '堂': 'Đường', '樓': 'Lâu', '閣': 'Các',
    '亭': 'Đình', '橋': 'Kiều', '洞': 'Động', '窟': 'Quật', '林': 'Lâm',
    '苑': 'Uyển',
    # Common characters in county/district names missing from initial set
    '忻': 'Hân', '朔': 'Sóc', '同': 'Đồng', '家': 'Gia', '莊': 'Trang',
    '治': 'Trị', '族': 'Tộc', '蒙': 'Mông', '旗': 'Kỳ', '盟': 'Minh',
    '滿': 'Mãn', '回': 'Hồi', '轄': 'Hạt', '無': 'Vô', '錫': 'Tích',
    '鼓': 'Cổ', '樓': 'Lâu', '玄': 'Huyền', '閶': 'Xướng', '雨': 'Vũ',
    '堯': 'Nghiêu', '熟': 'Thục', '棲': 'Thê', '霞': 'Hà', '年': 'Niên',
    '易': 'Dịch', '代': 'Đại', '蔚': 'Uất', '汾': 'Phần', '運': 'Vận',
    '城': 'Thành', '垣': 'Viên', '曲': 'Khúc', '浩': 'Hạo', '繁': 'Phồn',
    '峙': 'Trĩ', '偏': 'Thiên', '嵐': 'Lam', '縣': 'Huyện', '鄲': 'Đan',
    '邯': 'Hàm', '肥': 'Phì', '鄉': 'Hương', '鹿': 'Lộc', '皇': 'Hoàng',
    '葫': 'Hồ', '蘆': 'Lô', '倫': 'Luân', '察': 'Sát', '承': 'Thừa',
    '德': 'Đức', '遷': 'Thiên', '棗': 'Táo', '滕': 'Đằng', '藏': 'Tạng',
    '彝': 'Di', '壯': 'Tráng', '苗': 'Miêu', '侗': 'Đồng', '布': 'Bố',
    '依': 'Y', '黎': 'Lê', '畲': 'Xa', '傣': 'Đái',
    '坊': 'Phường', '項': 'Hạng', '陂': 'Bi', '睢': 'Tuy', '扶': 'Phù',
    '沔': 'Miện', '荊': 'Kinh', '孝': 'Hiếu', '感': 'Cảm', '咸': 'Hàm',
    '仙': 'Tiên', '桃': 'Đào', '邵': 'Thiệu', '株': 'Chu', '婁': 'Lâu',
    '冷': 'Lãnh', '益': 'Ích', '岳': 'Nhạc', '婁': 'Lâu', '耒': 'Lỗi',
    '資': 'Tư', '嘉': 'Gia', '攀': 'Phan', '枝': 'Chi', '綿': 'Miên',
    '充': 'Sung', '達': 'Đạt', '巴': 'Ba', '廣': 'Quảng', '眉': 'Mi',
    '雅': 'Nhã', '康': 'Khang', '壩': 'Bá', '阿': 'A',
    '嶺': 'Lĩnh', '鳳': 'Phụng', '慶': 'Khánh', '隴': 'Lũng', '秦': 'Tần',
    '渭': 'Vị', '漢': 'Hán', '商': 'Thương', '韓': 'Hàn',
    '撫': 'Phủ', '錦': 'Cẩm', '牡': 'Mẫu', '佳': 'Giai', '綏': 'Tuy',
    '伊': 'Y', '齊': 'Tề', '克': 'Khắc', '瑪': 'Mã', '庫': 'Khố',
    '格': 'Cách', '勒': 'Lặc', '霍': 'Hoắc', '圖': 'Đồ', '吐': 'Thổ',
    '喀': 'Khách', '什': 'Thập', '薩': 'Tát', '拉': 'Lạp', '則': 'Tắc',
    '貢': 'Cống', '日': 'Nhật', '包': 'Bao', '赤': 'Xích', '善': 'Thiện',
    '彥': 'Yến', '昂': 'Ngang', '扎': 'Trát', '那': 'Na', '曲': 'Khúc',
    '江': 'Giang', '達': 'Đạt', '孜': 'Tư',
    # High-frequency chars missing from above passes
    '市': 'Thị', '天': 'Thiên', '地': 'Địa', '維': 'Duy', '吾': 'Ngô',
    '賓': 'Tân', '理': 'Lý', '豐': 'Phong', '丰': 'Phong', '澤': 'Trạch',
    '泽': 'Trạch', '波': 'Ba', '投': 'Đầu', '羅': 'La', '罗': 'La',
    '尚': 'Thượng', '寬': 'Khoan', '寬': 'Khoan', '廬': 'Lư', '庐': 'Lư',
    '樟': 'Chương', '淳': 'Thuần', '弋': 'Dặc', '婺': 'Mụ', '衢': 'Cù',
    '舟': 'Chu', '麗': 'Lệ', '皖': 'Hoán', '贛': 'Cám', '閩': 'Mân',
    '瓊': 'Quỳnh', '桂': 'Quế', '粵': 'Việt', '粤': 'Việt', '滇': 'Điền',
    '黔': 'Kiềm', '巴': 'Ba', '蜀': 'Thục', '洮': 'Đào', '岷': 'Mân',
    '鹽': 'Diêm', '淵': 'Uyên', '朗': 'Lãng', '孟': 'Mạnh', '嘉': 'Gia',
    '罽': 'Kế', '健': 'Kiện', '馱': 'Đà', '陀': 'Đà', '羅': 'La',
    '那': 'Na', '迦': 'Ca', '提': 'Đề', '耶': 'Da', '舍': 'Xá',
    '羅': 'La', '衛': 'Vệ', '摩': 'Ma', '竭': 'Kiệt', '伽': 'Già',
    '毘': 'Tỳ', '耶': 'Da', '離': 'Ly', '婆': 'Bà', '娑': 'Ta',
    '夷': 'Di', '敖': 'Ngao', '黔': 'Kiềm',
    # Third pass — chars still missing after coverage tests
    '餘': 'Dư', '余': 'Dư', '寶': 'Bảo', '宝': 'Bảo', '峨': 'Nga',
    '店': 'Điếm', '羌': 'Khương', '屏': 'Bình', '行': 'Hành',
    '政': 'Chính', '國': 'Quốc', '国': 'Quốc', '蓮': 'Liên', '莲': 'Liên',
    '犁': 'Ly', '薩': 'Tát', '哈': 'Cáp', '薩': 'Tát',
    '尼': 'Ni', '普': 'Phổ', '洱': 'Nhĩ', '楚': 'Sở', '熊': 'Hùng',
    '湄': 'Mi', '潭': 'Đàm', '鵝': 'Nga', '楓': 'Phong', '舫': 'Phảng',
    '晴': 'Tình', '崩': 'Băng', '雷': 'Lôi', '電': 'Điện', '電': 'Điện',
    '夾': 'Giáp', '夹': 'Giáp', '貞': 'Trinh', '贞': 'Trinh',
    '叢': 'Tùng', '丛': 'Tùng', '牙': 'Nha', '克': 'Khắc',
    '欒': 'Loan', '栾': 'Loan', '清': 'Thanh', '水': 'Thủy',
    '瓦': 'Ngõa', '灰': 'Hôi', '磁': 'Từ', '邱': 'Khâu',
    '雙': 'Song', '橋': 'Kiều', '湘': 'Tương', '潼': 'Đồng',
    '獻': 'Hiến', '献': 'Hiến', '涼': 'Lương', '梁': 'Lương',
    '紫': 'Tử', '金': 'Kim', '銀': 'Ngân', '銅': 'Đồng',
    '蔗': 'Giá', '糖': 'Đường', '珠': 'Châu', '鑽': 'Toàn',
    '劍': 'Kiếm', '剑': 'Kiếm', '閣': 'Các', '廬': 'Lư',
    '灘': 'Than', '納': 'Nạp', '溝': 'Câu', '沟': 'Câu',
    '疏': 'Sơ', '勒': 'Lặc', '塔': 'Tháp', '什': 'Thập',
    '米': 'Mễ', '格': 'Cách', '爾': 'Nhĩ', '班': 'Ban',
    '瑪': 'Mã', '曲': 'Khúc', '措': 'Thố', '隆': 'Long',
    '嘎': 'Cát', '龜': 'Quy', '茲': 'Tư', '且': 'Thư',
    '末': 'Mạt', '若': 'Nhược', '羌': 'Khương', '鄯': 'Thiện',
    '焉': 'Yên', '耆': 'Kỳ', '疏': 'Sơ', '附': 'Phụ',
    '輪': 'Luân', '台': 'Đài', '盧': 'Lô', '布': 'Bố',
    # Fourth pass — chars from sampling remaining bad outputs
    '肅': 'Túc', '潯': 'Tầm', '渾': 'Hồn', '房': 'Phòng', '柔': 'Nhu',
    '成': 'Thành', '辰': 'Thần', '坻': 'Đê', '靜': 'Tĩnh', '薊': 'Kế',
    '井': 'Tỉnh', '陘': 'Hình', '礦': 'Khoáng', '裕': 'Dụ', '正': 'Chính',
    '園': 'Viên', '周': 'Chu', '建': 'Kiến', '彰': 'Chương', '博': 'Bác',
    '里': 'Lý', '直': 'Trực', '級': 'Cấp', '劃': 'Hoạch', '全': 'Toàn',
    '潮': 'Triều', '陽': 'Dương', '華': 'Hoa', '陰': 'Âm',
    '灤': 'Loan', '秦': 'Tần', '皇': 'Hoàng', '邯': 'Hàm', '鄲': 'Đan',
    '衡': 'Hành', '水': 'Thủy', '廊': 'Lang', '坊': 'Phường',
    '邢': 'Hình', '臺': 'Đài', '承': 'Thừa', '德': 'Đức',
    '滄': 'Thương', '張': 'Trương', '家': 'Gia', '口': 'Khẩu',
    '唐': 'Đường', '山': 'Sơn', '秦': 'Tần', '皇': 'Hoàng', '島': 'Đảo',
    '潞': 'Lộ', '晉': 'Tấn', '城': 'Thành', '運': 'Vận', '吕': 'Lữ',
    '梁': 'Lương', '繁': 'Phồn', '峙': 'Trĩ', '偏': 'Thiên', '嵐': 'Lam',
    '汀': 'Đinh', '漳': 'Chương', '龍': 'Long', '岩': 'Nham', '泉': 'Tuyền',
    '莆': 'Bồ', '廈': 'Hạ', '寧': 'Ninh', '三': 'Tam',
    '赣': 'Cám', '景': 'Cảnh', '鷹': 'Ưng', '潭': 'Đàm', '萍': 'Bình',
    '萍': 'Bình', '赤': 'Xích', '新': 'Tân', '鄉': 'Hương',
    '鑲': 'Tương', '黃': 'Hoàng', '甲': 'Giáp', '盤': 'Bàn',
    '撫': 'Phủ', '順': 'Thuận', '開': 'Khai', '鐵': 'Thiết',
    '葫': 'Hồ', '蘆': 'Lô', '錦': 'Cẩm', '州': 'Châu',
    '吉': 'Cát', '四': 'Tứ', '松': 'Tùng', '原': 'Nguyên',
    '鴨': 'Áp', '綠': 'Lục', '延': 'Diên', '邊': 'Biên',
    '圖': 'Đồ', '們': 'Môn', '牡': 'Mẫu', '丹': 'Đan',
    '伊': 'Y', '七': 'Thất', '雞': 'Kê', '嫩': 'Nộn',
    '哈': 'Cáp', '濱': 'Tân', '齊': 'Tề', '齐': 'Tề',
    '大': 'Đại', '慶': 'Khánh', '雙': 'Song', '鴨': 'Áp',
    '鶴': 'Hạc', '崗': 'Cương', '綏': 'Tuy', '化': 'Hóa',
    '武': 'Vũ', '漢': 'Hán', '黃': 'Hoàng', '石': 'Thạch',
    '恩': 'Ân', '施': 'Thi', '隨': 'Tùy', '襄': 'Tương',
    '樊': 'Phàn', '孝': 'Hiếu', '感': 'Cảm', '荊': 'Kinh',
    '宜': 'Nghi', '潛': 'Tiềm', '江': 'Giang', '天': 'Thiên',
    '門': 'Môn', '鄂': 'Ngạc', '洲': 'Châu', '仙': 'Tiên',
    '岳': 'Nhạc', '株': 'Chu', '湘': 'Tương', '邵': 'Thiệu',
    '冷': 'Lãnh', '益': 'Ích', '婁': 'Lâu', '耒': 'Lỗi',
    '韶': 'Thiều', '河': 'Hà', '源': 'Nguyên',
    '梅': 'Mai', '汕': 'Sán', '揭': 'Yết', '潮': 'Triều',
    '揚': 'Dương', '鎮': 'Trấn', '徐': 'Từ', '連': 'Liên',
    '鹽': 'Diêm', '宿': 'Túc', '遷': 'Thiên', '淮': 'Hoài',
    '無': 'Vô', '錫': 'Tích', '常': 'Thường', '蘇': 'Tô',
    '浙': 'Chiết', '杭': 'Hàng', '餘': 'Dư', '紹': 'Thiệu',
    '金': 'Kim', '華': 'Hoa', '衢': 'Cù', '舟': 'Chu',
    '溫': 'Ôn', '嘉': 'Gia', '湖': 'Hồ', '台': 'Đài',
    '麗': 'Lệ',
    # Fifth pass — extended coverage
    '呂': 'Lữ', '堰': 'Yển', '巢': 'Sào', '駐': 'Trú', '栗': 'Lật',
    '民': 'Dân', '夏': 'Hạ', '洪': 'Hồng', '秀': 'Tú', '營': 'Doanh',
    '富': 'Phú', '靖': 'Tĩnh', '桐': 'Đồng', '郴': 'Thần', '頂': 'Đỉnh',
    '鄖': 'Vân', '隨': 'Tùy', '神': 'Thần', '農': 'Nông', '架': 'Giá',
    '丹': 'Đan', '江': 'Giang', '陵': 'Lăng', '荊': 'Kinh', '門': 'Môn',
    '潛': 'Tiềm', '應': 'Ứng', '城': 'Thành', '漢': 'Hán', '川': 'Xuyên',
    '嶽': 'Nhạc', '陽': 'Dương', '常': 'Thường', '德': 'Đức', '懷': 'Hoài',
    '化': 'Hóa', '湘': 'Tương', '潭': 'Đàm', '株': 'Chu', '洲': 'Châu',
    '永': 'Vĩnh', '州': 'Châu', '衡': 'Hành', '郴': 'Thần', '婁': 'Lâu',
    '底': 'Để', '邵': 'Thiệu', '冷': 'Lãnh', '水': 'Thủy', '益': 'Ích',
    '汕': 'Sán', '揭': 'Yết', '茂': 'Mậu', '名': 'Danh', '肇': 'Triệu',
    '清': 'Thanh', '遠': 'Viễn', '雲': 'Vân', '浮': 'Phù', '梅': 'Mai',
    '惠': 'Huệ', '河': 'Hà', '源': 'Nguyên', '東': 'Đông', '莞': 'Quan',
    '中': 'Trung', '山': 'Sơn', '江': 'Giang', '門': 'Môn', '珠': 'Châu',
    '沙': 'Sa', '頭': 'Đầu', '角': 'Giác', '坪': 'Bình',
    '成': 'Thành', '都': 'Đô', '攀': 'Phan', '枝': 'Chi', '花': 'Hoa',
    '瀘': 'Lô', '德': 'Đức', '陽': 'Dương', '綿': 'Miên', '樂': 'Lạc',
    '遂': 'Toại', '寧': 'Ninh', '廣': 'Quảng', '元': 'Nguyên', '內': 'Nội',
    '雅': 'Nhã', '巴': 'Ba', '達': 'Đạt', '眉': 'Mi', '宜': 'Nghi',
    '賓': 'Tân', '甘': 'Cam', '孜': 'Tư', '阿': 'A', '壩': 'Bá',
    '涼': 'Lương', '崇': 'Sùng', '自': 'Tự', '貢': 'Cống', '資': 'Tư',
    '南': 'Nam', '充': 'Sung', '廣': 'Quảng', '安': 'An', '羅': 'La',
    '遵': 'Tuân', '義': 'Nghĩa', '六': 'Lục', '盤': 'Bàn', '水': 'Thủy',
    '安': 'An', '順': 'Thuận', '黔': 'Kiềm', '南': 'Nam', '東': 'Đông',
    '畢': 'Tất', '節': 'Tiết', '鐵': 'Thiết', '仁': 'Nhân',
    '貴': 'Quý', '陽': 'Dương', '銅': 'Đồng', '仁': 'Nhân',
    '昆': 'Côn', '明': 'Minh', '曲': 'Khúc', '靖': 'Tĩnh', '玉': 'Ngọc',
    '溪': 'Khê', '保': 'Bảo', '山': 'Sơn', '臨': 'Lâm', '滄': 'Thương',
    '普': 'Phổ', '洱': 'Nhĩ', '西': 'Tây', '版': 'Bản', '納': 'Nạp',
    '文': 'Văn', '楚': 'Sở', '雄': 'Hùng', '昭': 'Chiêu', '通': 'Thông',
    '麗': 'Lệ', '江': 'Giang', '迪': 'Địch', '慶': 'Khánh', '怒': 'Nộ',
    '德': 'Đức', '宏': 'Hoằng', '紅': 'Hồng', '錫': 'Tích',
    # Misc chars still missing
    '蘭': 'Lan', '滄': 'Thương', '瑞': 'Thụy', '吳': 'Ngô',
    '漢': 'Hán', '商': 'Thương', '洛': 'Lạc', '渭': 'Vị',
    '韓': 'Hàn', '延': 'Diên', '榆': 'Du', '林': 'Lâm',
    '康': 'Khang', '白': 'Bạch', '銀': 'Ngân', '蘇': 'Tô',
    '金': 'Kim', '昌': 'Xương', '張': 'Trương', '掖': 'Dịch',
    '酒': 'Tửu', '嘉': 'Gia', '峪': 'Dục', '武': 'Vũ',
    '威': 'Uy', '涼': 'Lương', '隴': 'Lũng', '定': 'Định',
    '隆': 'Long', '固': 'Cố', '嘴': 'Chủy', '石': 'Thạch',
    '中': 'Trung', '衛': 'Vệ', '木': 'Mộc', '齊': 'Tề',
    # Sixth pass
    '子': 'Tử', '樹': 'Thụ', '作': 'Tác', '梧': 'Ngô', '利': 'Lợi',
    '麻': 'Ma', '會': 'Hội', '音': 'Âm', '瑤': 'Dao', '基': 'Cơ',
    '封': 'Phong', '楞': 'Lăng', '荔': 'Lệ', '奉': 'Phụng', '當': 'Đương',
    '贊': 'Tán', '皋': 'Cao', '蘭': 'Lan', '涉': 'Thiệp', '冀': 'Ký',
    '行': 'Hành', '唐': 'Đường', '廬': 'Lư', '霍': 'Hoắc', '孟': 'Mạnh',
    '州': 'Châu', '沙': 'Sa', '洋': 'Dương', '錢': 'Tiền', '塘': 'Đường',
    '寶': 'Bảo', '山': 'Sơn', '崇': 'Sùng', '明': 'Minh',
    '廔': 'Lâu', '浦': 'Phố', '奉': 'Phụng', '賢': 'Hiền', '閔': 'Mẫn',
    '嘉': 'Gia', '定': 'Định', '青': 'Thanh', '浦': 'Phố',
    '松': 'Tùng', '江': 'Giang', '金': 'Kim', '山': 'Sơn',
    '沛': 'Bái', '豐': 'Phong', '彭': 'Bành', '徐': 'Từ', '邳': 'Phi',
    '灌': 'Quán', '沭': 'Thuật', '漣': 'Liên', '阜': 'Phụ',
    '鎮': 'Trấn', '揚': 'Dương', '高': 'Cao', '郵': 'Bưu',
    '鹽': 'Diêm', '城': 'Thành', '蘇': 'Tô', '州': 'Châu',
    '滁': 'Trừ', '亳': 'Bạc', '宿': 'Túc', '蚌': 'Bạng',
    '淮': 'Hoài', '南': 'Nam', '北': 'Bắc',
    '池': 'Trì', '宣': 'Tuyên', '城': 'Thành', '黃': 'Hoàng',
    '合': 'Hợp', '肥': 'Phì', '鞍': 'Yên',
    '景': 'Cảnh', '德': 'Đức', '鎮': 'Trấn', '九': 'Cửu',
    '萍': 'Bình', '鷹': 'Ưng', '潭': 'Đàm', '新': 'Tân',
    '余': 'Dư', '上': 'Thượng', '饒': 'Nhiêu',
    '贛': 'Cám', '撫': 'Phủ', '吉': 'Cát', '宜': 'Nghi', '春': 'Xuân',
    '南': 'Nam', '昌': 'Xương', '萍': 'Bình',
    '莆': 'Bồ', '田': 'Điền', '漳': 'Chương', '泉': 'Tuyền',
    '廈': 'Hạ', '寧': 'Ninh', '德': 'Đức', '三': 'Tam',
    '龍': 'Long', '岩': 'Nham',
    '海': 'Hải', '口': 'Khẩu', '三': 'Tam', '亞': 'Á',
    '儋': 'Đam', '瓊': 'Quỳnh', '海': 'Hải', '萬': 'Vạn', '寧': 'Ninh',
    '文': 'Văn', '昌': 'Xương', '瓊': 'Quỳnh', '中': 'Trung',
    '樂': 'Lạc', '東': 'Đông', '方': 'Phương', '澄': 'Trừng',
    '邁': 'Mại', '臨': 'Lâm', '高': 'Cao', '白': 'Bạch',
    '沙': 'Sa', '定': 'Định', '安': 'An', '保': 'Bảo',
    '屯': 'Đồn', '昌': 'Xương', '江': 'Giang',
    '洋': 'Dương', '陵': 'Lăng', '水': 'Thủy', '務': 'Vụ',
    '崖': 'Nhai', '州': 'Châu', '港': 'Cảng',
    '庫': 'Khố', '爾': 'Nhĩ', '勒': 'Lặc', '蘇': 'Tô', '阿': 'A',
    '克': 'Khắc', '拉': 'Lạp', '瑪': 'Mã', '什': 'Thập',
    '喀': 'Khách', '格': 'Cách', '霍': 'Hoắc', '圖': 'Đồ',
    '吐': 'Thổ', '哈': 'Cáp', '番': 'Phiên', '米': 'Mễ',
    '奎': 'Khuê', '屯': 'Đồn', '和': 'Hòa', '田': 'Điền',
    '巴': 'Ba', '音': 'Âm', '郭': 'Quách', '楞': 'Lăng',
    '博': 'Bác', '湖': 'Hồ', '伊': 'Y', '寧': 'Ninh',
    '昌': 'Xương', '吉': 'Cát', '塔': 'Tháp', '城': 'Thành',
    '烏': 'Ô', '蘇': 'Tô', '特': 'Đặc',
    # Final batch — comprehensive coverage for remaining chars
    '柯': 'Kha', '倉': 'Thương', '陸': 'Lục', '碑': 'Bi', '榮': 'Vinh',
    '環': 'Hoàn', '章': 'Chương', '容': 'Dung', '士': 'Sĩ', '公': 'Công',
    '彭': 'Bành', '慈': 'Từ', '郎': 'Lang', '揚': 'Dương', '尤': 'Vưu',
    '泰': 'Thái', '門': 'Môn', '莆': 'Bồ', '崖': 'Nhai', '儋': 'Đam',
    '亞': 'Á', '洋': 'Dương', '方': 'Phương', '樂': 'Lạc', '東': 'Đông',
    '崎': 'Kỳ', '灣': 'Loan', '坂': 'Phản', '名': 'Danh',
    '郎': 'Lang', '奎': 'Khuê', '廓': 'Khoách', '瓦': 'Ngõa',
    '番': 'Phiên', '禺': 'Ngu', '增': 'Tăng', '城': 'Thành',
    '順': 'Thuận', '佛': 'Phật', '山': 'Sơn', '江': 'Giang',
    '門': 'Môn', '中': 'Trung', '歡': 'Hoan', '樂': 'Lạc',
    '貝': 'Bối', '類': 'Loại', '德': 'Đức', '今': 'Kim',
    '古': 'Cổ', '典': 'Điển', '術': 'Thuật', '數': 'Số',
    '位': 'Vị', '分': 'Phân', '區': 'Khu', '劃': 'Hoạch',
    '組': 'Tổ', '群': 'Quần', '族': 'Tộc', '系': 'Hệ',
    '科': 'Khoa', '類': 'Loại', '目': 'Mục', '錄': 'Lục',
    '表': 'Biểu', '圖': 'Đồ', '志': 'Chí', '史': 'Sử',
    '書': 'Thư', '記': 'Ký', '傳': 'Truyện', '論': 'Luận',
    '議': 'Nghị', '奏': 'Tấu', '折': 'Chiết', '疏': 'Sơ',
    '贊': 'Tán', '詞': 'Từ', '詩': 'Thi', '賦': 'Phú',
    '銘': 'Minh', '碑': 'Bi', '帖': 'Thiếp', '序': 'Tự',
    '跋': 'Bạt', '箋': 'Tiên', '注': 'Chú', '疏': 'Sớ',
    '解': 'Giải', '釋': 'Thích', '音': 'Âm', '義': 'Nghĩa',
    '文': 'Văn', '字': 'Tự', '言': 'Ngôn', '語': 'Ngữ',
    '章': 'Chương', '句': 'Cú', '段': 'Đoạn', '節': 'Tiết',
    '卷': 'Quyển', '冊': 'Sách', '本': 'Bản', '版': 'Bản',
    '篇': 'Thiên', '部': 'Bộ', '門': 'Môn', '類': 'Loại',
    '宗': 'Tông', '派': 'Phái', '教': 'Giáo', '法': 'Pháp',
    '禪': 'Thiền', '律': 'Luật', '淨': 'Tịnh', '密': 'Mật',
    '顯': 'Hiển', '密': 'Mật', '念': 'Niệm', '觀': 'Quán',
    '修': 'Tu', '證': 'Chứng', '悟': 'Ngộ', '覺': 'Giác',
    '道': 'Đạo', '果': 'Quả', '行': 'Hành', '願': 'Nguyện',
    # Pass 7 — remaining 587 missing chars from coverage scan
    # Directions/positions (supplemental)
    '翼': 'Dực', '尾': 'Vĩ', '首': 'Thủ', '橫': 'Hoành', '幹': 'Cán',
    '裏': 'Lý', '裡': 'Lý', '至': 'Chí', '始': 'Thủy', '居': 'Cư',
    '步': 'Bộ', '游': 'Du', '遊': 'Du', '流': 'Lưu', '沿': 'Duyên',
    '從': 'Tòng', '各': 'Các', '于': 'Vu', '於': 'Vu', '為': 'Vi',
    '工': 'Công', '功': 'Công', '勝': 'Thắng', '強': 'Cường', '勤': 'Cần',
    '勉': 'Miễn', '助': 'Trợ', '互': 'Hỗ', '共': 'Cộng', '集': 'Tập',
    '積': 'Tích', '結': 'Kết', '進': 'Tiến', '歸': 'Quy', '復': 'Phục',
    '留': 'Lưu', '息': 'Tức', '止': 'Chỉ', '至': 'Chí', '次': 'Thứ',
    '始': 'Thủy', '極': 'Cực', '列': 'Liệt', '聯': 'Liên', '匯': 'Hối',
    '循': 'Tuần', '歷': 'Lịch', '流': 'Lưu', '端': 'Đoan', '如': 'Như',
    # Nature & terrain (supplemental)
    '野': 'Dã', '草': 'Thảo', '茅': 'Mao', '桑': 'Tang', '芝': 'Chi',
    '蓬': 'Bồng', '蒼': 'Thương', '藍': 'Lam', '翠': 'Thúy', '彩': 'Thái',
    '香': 'Hương', '芳': 'Phương', '芬': 'Phân', '梨': 'Lê', '杏': 'Hạnh',
    '椒': 'Tiêu', '麥': 'Mạch', '禾': 'Hòa', '稻': 'Đạo', '茶': 'Trà',
    '棉': 'Miên', '油': 'Du', '瓜': 'Qua', '豆': 'Đậu', '果': 'Quả',
    '榕': 'Dong', '楠': 'Nam', '杉': 'Sam', '樺': 'Hoa', '柘': 'Trá',
    '桓': 'Hoàn', '槐': 'Hòe', '棣': 'Đệ', '柞': 'Tác', '枋': 'Phương',
    '蘿': 'La', '藤': 'Đằng', '蕉': 'Tiêu', '芙': 'Phù', '蓉': 'Dung',
    '芎': 'Khung', '芷': 'Chỉ', '蒗': 'Lãng', '莎': 'Sa', '茄': 'Già',
    '苓': 'Linh', '蕭': 'Tiêu', '蘄': 'Kỳ', '螺': 'Loa', '莿': 'Thứ',
    '魚': 'Ngư', '鯉': 'Lý', '牛': 'Ngưu', '羊': 'Dương', '獅': 'Sư',
    '猛': 'Mãnh', '猇': 'Hao', '鶯': 'Oanh', '鳩': 'Cưu', '鳥': 'Điểu',
    '鳴': 'Minh', '蛟': 'Giao', '麟': 'Lân', '麒': 'Kỳ', '龜': 'Quy',
    '虹': 'Hồng', '象': 'Tượng', '獨': 'Độc', '嵊': 'Thặng',
    # Water (supplemental)
    '澎': 'Bành', '澗': 'Giản', '澳': 'Úc', '滎': 'Huỳnh', '灞': 'Bá',
    '湟': 'Hoàng', '涪': 'Phù', '渠': 'Cừ', '溧': 'Lật', '淶': 'Lai',
    '汶': 'Vấn', '沾': 'Chiêm', '溮': 'Sư', '潢': 'Hoàng', '濉': 'Tuệ',
    '瀍': 'Triền', '澠': 'Thằng', '淇': 'Kỳ', '浚': 'Tuấn', '淅': 'Tích',
    '泌': 'Bí', '涵': 'Hàm', '湞': 'Trinh', '濠': 'Hào', '濞': 'Bí',
    '漾': 'Dạng', '瀾': 'Lan', '瀏': 'Lưu', '汨': 'Mịch', '汪': 'Uông',
    '沽': 'Cô', '泊': 'Bạc', '渦': 'Oa', '濃': 'Nùng', '淩': 'Lăng',
    '潤': 'Nhuận', '乳': 'Nhũ', '洑': 'Phục',
    # Mountains & terrain (supplemental)
    '嶼': 'Tự', '嶗': 'Lao', '嶧': 'Dịch', '崁': 'Khảm', '巒': 'Loan',
    '麓': 'Lộc', '磐': 'Bàn', '壺': 'Hồ', '磴': 'Đặng', '礁': 'Tiêu',
    '窪': 'Oa', '坑': 'Khanh', '岑': 'Sầm', '岐': 'Kỳ', '岫': 'Tụ',
    '棱': 'Lăng', '塞': 'Tái', '鼎': 'Đỉnh', '巍': 'Nguy', '岸': 'Ngạn',
    # Administrative & people
    '官': 'Quan', '師': 'Sư', '王': 'Vương', '君': 'Quân', '侯': 'Hầu',
    '伯': 'Bá', '任': 'Nhậm', '禮': 'Lễ', '祿': 'Lộc', '祜': 'Hỗ',
    '祁': 'Kỳ', '社': 'Xã', '禹': 'Vũ', '穆': 'Mục', '姚': 'Diêu',
    '氏': 'Thị', '姑': 'Cô', '心': 'Tâm', '愛': 'Ái', '喜': 'Hỷ',
    '禮': 'Lễ', '卓': 'Trác', '彌': 'Di', '虞': 'Ngu', '聶': 'Nhiếp',
    '翁': 'Ông', '牟': 'Mưu', '覃': 'Đàm', '袁': 'Viên', '賈': 'Giả',
    '戚': 'Thích', '杜': 'Đỗ', '姜': 'Khương', '鄒': 'Trâu', '孫': 'Tôn',
    '葛': 'Cát', '范': 'Phạm', '薛': 'Tiết', '鄧': 'Đặng', '潘': 'Phan',
    '謝': 'Tạ', '蕭': 'Tiêu', '祝': 'Chúc', '任': 'Nhậm', '仲': 'Trọng',
    '如': 'Như', '耀': 'Diệu', '聖': 'Thánh', '英': 'Anh',
    # Stars, heaven & nature concepts
    '星': 'Tinh', '望': 'Vọng', '照': 'Chiếu', '旌': 'Tinh', '霄': 'Tiêu',
    '暖': 'Noãn', '炎': 'Viêm', '風': 'Phong', '凰': 'Hoàng', '霸': 'Bá',
    '霧': 'Vụ', '暉': 'Huy', '輝': 'Huy', '晃': 'Hoảng', '晏': 'Yển',
    '翔': 'Tường', '翁': 'Ông', '翼': 'Dực', '騰': 'Đằng', '驛': 'Dịch',
    '驊': 'Hoa', '冬': 'Đông', '乾': 'Kiền', '乃': 'Nãi', '於': 'Vu',
    # 7 chars still missing after pass 7
    '紮': 'Trát', '頗': 'Phả', '浪': 'Lãng', '交': 'Giao',
    '拜': 'Bái', '煩': 'Phiền', '准': 'Chuẩn',
    # Materials & tools
    '墨': 'Mặc', '鋼': 'Cương', '鐘': 'Chung', '鉅': 'Cự', '鎣': 'Oanh',
    '鉛': 'Diên', '鏡': 'Kính', '鑼': 'La', '閘': 'Trát', '燈': 'Đăng',
    '箭': 'Tiễn', '車': 'Xa', '弓': 'Cung', '刀': 'Đao', '磅': 'Bảng',
    '碑': 'Bi', '碧': 'Bích', '璧': 'Bích', '琅': 'Lang', '琊': 'Nha',
    '琴': 'Cầm', '琉': 'Lưu', '球': 'Cầu', '玉': 'Ngọc',
    # Peoples & ethnic groups
    '佤': 'Ngõa', '傈': 'Lật', '僳': 'Túc', '寮': 'Liêu', '佬': 'Lão',
    '仡': 'Ngật', '仫': 'Mục', '彝': 'Di', '苗': 'Miêu', '瑤': 'Diêu',
    # Place names (common enough chars)
    '美': 'Mỹ', '圳': 'Chân', '澎': 'Bành', '鮮': 'Tiên', '寮': 'Liêu',
    '甸': 'Điện', '托': 'Thác', '社': 'Xã', '郊': 'Giao', '界': 'Giới',
    '思': 'Tư', '良': 'Lương', '梓': 'Tử', '斗': 'Đấu', '尖': 'Tiêm',
    '額': 'Ngạch', '匯': 'Hối', '鞏': 'Củng', '澗': 'Giản', '塞': 'Tái',
    '彌': 'Di', '湟': 'Hoàng', '埤': 'Tỳ', '辛': 'Tân', '館': 'Quán',
    '陶': 'Đào', '圍': 'Vi', '皮': 'Bì', '間': 'Gian', '迎': 'Nghênh',
    '權': 'Quyền', '休': 'Hưu', '聞': 'Văn', '絳': 'Giáng', '賽': 'Tái',
    '罕': 'Hãn', '默': 'Mặc', '侖': 'Lôn', '喇': 'Lạt', '斡': 'Oát',
    '賚': 'Lai', '蓋': 'Cái', '票': 'Phiếu', '蔭': 'Ẩm', '湯': 'Thang',
    '遜': 'Tốn', '墅': 'Thự', '壇': 'Đàn', '儀': 'Nghi', '甌': 'Âu',
    '諸': 'Chư', '岱': 'Đại', '積': 'Tích', '譙': 'Tiêu', '為': 'Vi',
    '將': 'Tướng', '尋': 'Tầm', '汶': 'Vấn', '沾': 'Chiêm', '尉': 'Úy',
    '葉': 'Diệp', '舞': 'Vũ', '召': 'Thiệu', '茅': 'Mao', '軍': 'Quân',
    '君': 'Quân', '桑': 'Tang', '赫': 'Hách', '融': 'Dung', '涪': 'Phù',
    '巫': 'Vu', '柱': 'Trụ', '渠': 'Cừ', '印': 'Ấn', '穗': 'Tuệ',
    '祿': 'Lộc', '猛': 'Mãnh', '卡': 'Ka', '囊': 'Nang', '查': 'Tra',
    '旬': 'Tuần', '撒': 'Tán', '奇': 'Kỳ', '別': 'Biệt', '芳': 'Phương',
    '員': 'Viên', '楊': 'Dương', '屋': 'Ốc', '勢': 'Thế', '崙': 'Lôn',
    '灞': 'Bá', '恰': 'Hợp', '股': 'Cổ',
    # Terrain & city features (supplemental)
    '廠': 'Xưởng', '故': 'Cố', '昔': 'Tích', '遙': 'Diêu', '介': 'Giới',
    '稷': 'Tắc', '芮': 'Nhuế', '沃': 'Ốc', '隰': 'Tập', '奈': 'Nại',
    '曼': 'Mạn', '莫': 'Mạc', '力': 'Lực', '突': 'Đột', '僕': 'Bộc',
    '旅': 'Lữ', '立': 'Lập', '振': 'Chấn', '蛟': 'Giao', '主': 'Chủ',
    '宇': 'Vũ', '敦': 'Đôn', '琿': 'Hồn', '訥': 'Nột', '向': 'Hướng',
    '漠': 'Mạc', '鄴': 'Nghiệp', '戚': 'Thích', '相': 'Tương', '啟': 'Khải',
    '盱': 'Hu', '眙': 'Di', '響': 'Hưởng', '邗': 'Hàn', '征': 'Chinh',
    '徒': 'Đồ', '拱': 'Củng', '鄞': 'Ngân', '曙': 'Thự', '暨': 'Ký',
    '縉': 'Tấn', '畬': 'Du', '塗': 'Đồ', '樅': 'Tòng', '歙': 'Hấp',
    '黟': 'Y', '埇': 'Dũng', '碭': 'Đáng', '含': 'Hàm', '績': 'Tích',
    '廂': 'Sương', '列': 'Liệt', '薌': 'Hương', '詔': 'Chiếu', '譜': 'Phổ',
    '月': 'Nguyệt', '猶': 'Do', '載': 'Tải', '鉛': 'Diên', '嶗': 'Lao',
    '即': 'Tức', '度': 'Độ', '嶧': 'Dịch', '兒': 'Nhi', '墾': 'Khẩn',
    '罘': 'Phù', '招': 'Chiêu', '寒': 'Hàn', '朐': 'Cù', '微': 'Vi',
    '費': 'Phí', '莘': 'Sơn', '茌': 'Si', '冠': 'Quan', '棣': 'Đệ',
    '單': 'Đơn', '鄄': 'Quyển', '管': 'Quản', '杞': 'Kỷ', '考': 'Khảo',
    '偃': 'Yển', '郟': 'Giáp', '殷': 'Ân', '滑': 'Hoạt', '牧': 'Mục',
    '獲': 'Hoạch', '站': 'Trạm', '陟': 'Trắc', '郾': 'Yển', '宛': 'Uyển',
    '臥': 'Ngọa', '輿': 'Dư', '確': 'Xác', '礄': 'Kiều', '冶': 'Dã',
    '伍': 'Ngũ', '點': 'Điểm', '秭': 'Tử', '掇': 'Truyết', '夢': 'Mộng',
    '監': 'Giám', '滋': 'Tư', '團': 'Đoàn', '浠': 'Hi', '穴': 'Huyệt',
    '曾': 'Tăng', '攸': 'Do', '醴': 'Lễ', '蒸': 'Chưng', '植': 'Thực',
    '零': 'Linh', '牌': 'Bài', '漵': 'Xu', '丈': 'Trượng', '廉': 'Liêm',
    '要': 'Yêu', '郁': 'Úc', '邕': 'Ung', '疊': 'Điệp', '恭': 'Cung',
    '業': 'Nghiệp', '毛': 'Mao', '等': 'Đẳng', '憑': 'Bằng', '指': 'Chỉ',
    '碚': 'Bối', '綦': 'Kỳ', '足': 'Túc', '墊': 'Điệm', '酉': 'Dậu',
    '邡': 'Phảng', '郫': 'Tỳ', '邛': 'Cùng', '崍': 'Lai', '敘': 'Tự',
    '藺': 'Lẫn', '旺': 'Vượng', '船': 'Thuyền', '射': 'Xạ', '犍': 'Kiền',
    '研': 'Nghiên', '沐': 'Mộc', '閬': 'Lãng', '珙': 'Củng', '筠': 'Quân',
    '經': 'Kinh', '簡': 'Giản', '孚': 'Phu', '爐': 'Lô', '得': 'Đắc',
    '謀': 'Mưu', '冕': 'Miện', '烽': 'Phong', '真': 'Chân', '習': 'Tập',
    '阡': 'Thiên', '謨': 'Mô', '亨': 'Hanh', '織': 'Chức', '雍': 'Ung',
    '凱': 'Khải', '秉': 'Bỉnh', '勻': 'Quân', '甕': 'Ủng', '呈': 'Trình',
    '勸': 'Khuyến', '沖': 'Xung', '巧': 'Xảo', '耿': 'Cảnh', '個': 'Cá',
    '舊': 'Cựu', '硯': 'Nghiễn', '疇': 'Trù', '臘': 'Lạp', '盈': 'Doanh',
    '堆': 'Đôi', '丁': 'Đinh', '芒': 'Mang', '加': 'Gia', '錯': 'Thác',
    '比': 'Tỷ', '申': 'Thân', '索': 'Tố', '戈': 'Qua', '札': 'Trát',
    '噶': 'Hát', '革': 'Cách', '改': 'Cải', '脫': 'Thoát', '隅': 'Ngung',
    '未': 'Vị', '央': 'Ương', '戶': 'Hộ', '彬': 'Bân', '起': 'Khởi',
    '略': 'Lược', '脂': 'Chi', '瓜': 'Qua', '宕': 'Đãng', '兩': 'Lưỡng',
    '迭': 'Điệt', '碌': 'Lộc', '循': 'Tuần', '剛': 'Cương', '久': 'Cửu',
    '雜': 'Tạp', '稱': 'Xưng', '謙': 'Khiêm', '令': 'Lệnh', '峻': 'Tuấn',
    '阪': 'Phản', '坤': 'Khôn', '壘': 'Lũy', '精': 'Tinh', '碩': 'Thạc',
    '干': 'Can', '策': 'Sách', '敏': 'Mẫn', '蘊': 'Uẩn', '堵': 'Đổ',
    '板': 'Bản', '汐': 'Tịch', '碇': 'Định', '歌': 'Ca', '重': 'Trọng',
    '淡': 'Đạm', '壢': 'Lịch', '份': 'Phần', '庄': 'Trang', '造': 'Tạo',
    '后': 'Hậu', '肚': 'Đỗ', '姓': 'Tính', '伸': 'Thân', '褒': 'Bao',
    '背': 'Bội', '埕': 'Thành', '朴': 'Phác', '腳': 'Cước', '袋': 'Đại',
    '學': 'Học', '萣': 'Định', '恆': 'Hằng', '卑': 'Ti', '琉': 'Lưu',
    '藁': 'Cảo', '蠡': 'Lý', '盂': 'Vu', '遙': 'Diêu', '猗': 'Y',
    '岢': 'Khả', '曼': 'Mạn', '審': 'Thẩm', '磅': 'Bảng', '坑': 'Khanh',
    '穀': 'Cốc', '牟': 'Mưu', '澳': 'Úc', '結': 'Kết', '滎': 'Huỳnh',
    '藍': 'Lam', '翁': 'Ông', '乾': 'Kiền', '蔭': 'Ẩm', '閘': 'Trát',
    '蕉': 'Tiêu', '霄': 'Tiêu', '柘': 'Trá', '乳': 'Nhũ', '葉': 'Diệp',
    '召': 'Thiệu', '桑': 'Tang', '赫': 'Hách', '融': 'Dung', '滮': 'Bao',
    '駱': 'Lạc', '驪': 'Ly',
}



def _han_viet(name_raw: str) -> str:
    """Transliterate a raw Chinese place name to Hán-Việt reading char by char."""
    if not name_raw:
        return name_raw
    parts = []
    for ch in name_raw:
        parts.append(HAN_VIET_CHAR.get(ch, ch))
    return ' '.join(parts)



def parse_dila_district(district_str):
    """Parse DILA district string (e.g. '阿富汗-巴爾赫省(Balkh)-CharBolak')
    into dict {country_vi, province, district_vi, formatted}.
    Returns dict with only non-empty fields. No HVDic used.
    """
    if not district_str or not district_str.strip():
        return {}
    text = district_str.strip()
    # Multi-district strings (semicolons): take the first one only
    if ';' in text:
        text = text.split(';')[0].strip()
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    # If already Latin/Vietnamese, try simple extraction
    if not has_chinese:
        parts = text.replace('，', ',').split(',')
        if len(parts) >= 2:
            district_vi = ','.join(parts[:-1]).strip()
            country_vi = parts[-1].strip()
        else:
            district_vi = text
            country_vi = ''
        return {'country_vi': country_vi, 'district_vi': district_vi, 'formatted': text}
    # Has Chinese: split by '-'
    dash_parts = text.split('-')
    country_vi = ''
    province = ''
    district_vi = ''
    # Part 0: country
    if len(dash_parts) > 0:
        for zh, vi in COUNTRY_MAP.items():
            if zh in dash_parts[0]:
                country_vi = vi
                break
    # Detect Chinese admin hierarchy: any part[1..N] ends with suffix in ADMIN_LEVEL_MAP
    has_cn_admin = False
    if len(dash_parts) > 1:
        for p in dash_parts[1:]:
            if any(p.endswith(s) for s in ADMIN_LEVEL_MAP):
                has_cn_admin = True
                break
    # Segments classified as admin type (not real place names) — skip these
    _SKIP_SEGMENTS = {'市轄', '縣轄', '省直轄', '地區', '直轄', '地级市'}
    if has_cn_admin:
        segments = []
        for part in dash_parts[1:]:
            part = part.strip()
            if not part or part in _SKIP_SEGMENTS:
                continue
            found = False
            for suffix, level_vi in ADMIN_LEVEL_MAP.items():
                if part.endswith(suffix):
                    name_raw = part[:-len(suffix)]
                    if not name_raw or name_raw in _SKIP_SEGMENTS:
                        found = True  # skip this segment, don't add to output
                        break
                    name_vi = CHINESE_PLACE_NAMES.get(name_raw) or _han_viet(name_raw)
                    segments.append(f'{level_vi} {name_vi}')
                    found = True
                    break
            if not found:
                # No standard suffix: check if it's a known municipality or dict entry
                if part in MUNICIPALITIES:
                    name_vi = CHINESE_PLACE_NAMES.get(part) or _han_viet(part)
                    segments.append(f'thành phố {name_vi}')
                elif part in CHINESE_PLACE_NAMES:
                    segments.append(CHINESE_PLACE_NAMES[part])
                else:
                    segments.append(_han_viet(part))
        # Reverse order: small → large (huyện → thành phố → tỉnh)
        segments.reverse()
        district_vi_final = ', '.join(segments)
        formatted_parts = [p for p in [district_vi_final, country_vi] if p]
        return {
            'country_vi': country_vi,
            'province': '',
            'district_vi': district_vi_final,
            'formatted': ', '.join(formatted_parts),
        }
    # Afghanistan / Latin pattern (original logic)
    # Part 1: province (extract from parentheses)
    if len(dash_parts) > 1:
        m = re.search(r'\(([^)]+)\)', dash_parts[1])
        if m:
            province = m.group(1).strip()
    # Part 2: huyện/locality
    if len(dash_parts) > 2:
        raw = dash_parts[2].strip()
        district_vi = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw)
        district_vi = re.sub(r'[^\x00-\x7F\s]', '', district_vi).strip()
    if not district_vi and len(dash_parts) > 1:
        after_paren = re.sub(r'\([^)]*\)', '', dash_parts[1]).strip()
        after_paren = re.sub(r'[\u4e00-\u9fff]', '', after_paren).strip()
        if after_paren:
            district_vi = re.sub(r'([a-z])([A-Z])', r'\1 \2', after_paren)
    loc_parts = []
    if district_vi:
        loc_parts.append(f'huyện {district_vi}')
    if province:
        loc_parts.append(f'tỉnh {province}')
    district_vi_final = ', '.join(loc_parts)
    formatted_parts = [p for p in [district_vi_final, country_vi] if p]
    return {
        'country_vi': country_vi,
        'province': province,
        'district_vi': district_vi_final,
        'formatted': ', '.join(formatted_parts),
    }



# Dashboard Process Tracker — phục vụ file tĩnh thư mục dashboard/ (mở trực tiếp từ app.py:5000)
DASHBOARD_DIR = os.path.join(BASE_DIR, 'dashboard')



# ---------------------------------------------------------------------------
# T169 — Địa danh Groq review (side-car place_groq_audit)
# ---------------------------------------------------------------------------
_T169_DIFF_SORT = """
CASE a.diff_type
  WHEN 'POLYPHONIC_CHAR' THEN 0
  WHEN 'TAXONOMY_VARIANT' THEN 1
  WHEN 'PHONETIC_MISMATCH' THEN 2
  ELSE 3
END
"""




def _make_source_code(name):
    """Tạo source_code từ tên — fallback khi không có code rõ ràng."""
    s = re.sub(r'[^A-Za-z0-9]+', '_', unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()).strip('_').upper()
    return f'SRC_{s}' if s else 'SRC_NEW'




def _iso_now():
    from datetime import datetime as _dt
    return _dt.now().isoformat(timespec='seconds')




# ============================================================
# T139 Phase 2 — Zen Lineage HITL Review (additive, DERIVED-only)
# ------------------------------------------------------------
# Candidate pool: source_staging (row_type='master') — không đụng entity_source_ids
# (schema chặn entity_id NULL).
# Quyết định HITL: bảng DERIVED zenlineage_review (0 ALTER base).
# Approve → ghi entity_source_ids (entity_id thật, verified=1, match_status='approved').
# ============================================================
_ZEN_REVIEW_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS zenlineage_review (
    source_entity_id   TEXT PRIMARY KEY,
    status             TEXT NOT NULL,      -- approved | rejected
    dila_person_id     TEXT,
    entity_hub_id      INTEGER,
    confidence         REAL,
    editor             TEXT,
    note               TEXT,
    created_at         TEXT,
    updated_at         TEXT
)
"""




def _zen_ensure_review_table(conn):
    conn.execute(_ZEN_REVIEW_TABLE_SQL)
    conn.commit()




def _zen_suggest(conn, name, limit=5):
    """Gợi ý DILA person cho 1 zen slug — dò token trong tên (name_zh/name_vi/name_en/id).
    Trả về top candidates: {dila_id, name_vi, name_zh, sect, entity_hub_id, score}."""
    name = (name or '').strip()
    if not name:
        return []
    tokens = [t for t in (name.replace('-', ' ').replace('_', ' ').split()) if len(t) >= 2]
    if not tokens:
        return []
    # dò từng token riêng (OR) — token dài >=3 lấy nguyên, token 2 ký tự dùng prefix
    likes = []
    for t in tokens[:4]:
        like = t + '%' if len(t) >= 3 else '%' + t + '%'
        likes.append(like)
    ors = ' OR '.join(['p.name_zh LIKE ?', 'p.name_vi LIKE ?', 'p.name_en LIKE ?', 'p.name_ja LIKE ?'] * len(likes))
    params = []
    for like in likes:
        params += [like, like, like, like]
    params.append(limit * 8)
    rows = conn.execute(
        """SELECT p.id AS dila_id, p.name_vi, p.name_zh, p.name_en, p.name_ja, p.sect,
                  (SELECT eh.entity_id FROM entity_hub eh
                    WHERE eh.entity_type='PERSON' AND eh.canonical_label=p.id LIMIT 1) AS entity_hub_id
             FROM people p
             WHERE %s
             LIMIT ?""" % ors, params).fetchall()
    out = []
    for r in rows:
        hay = ' '.join(x or '' for x in (r['name_zh'], r['name_vi'], r['name_en'], r['name_ja']))
        score = 0
        for t in tokens:
            if t in hay:
                score += 2
            elif t[:2] in hay or t[:2] in (r['name_zh'] or ''):
                score += 1
        # tiêu chuẩn hóa Hán tự: nếu zen tên Hán trùng 1-2 ký tự chữ Hán
        if r['name_zh']:
            for ch in tokens:
                for c in ch:
                    if len(c) == 1 and c in r['name_zh']:
                        score += 1
        if score == 0:
            continue
        hit = {'dila_id': r['dila_id'], 'name_vi': r['name_vi'], 'name_zh': r['name_zh'],
               'name_en': r['name_en'], 'sect': r['sect'], 'entity_hub_id': r['entity_hub_id'],
               'score': score}
        out.append(hit)
    out.sort(key=lambda x: -x['score'])
    seen = set()
    uniq = []
    for h in out:
        if h['dila_id'] not in seen:
            seen.add(h['dila_id'])
            uniq.append(h)
    return uniq[:limit]




def _call_gemini(prompt, timeout=15):
    """Shared helper: call Groq LLM, return text or None."""
    try:
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.1, 'max_tokens': 2048},
            timeout=timeout)
        result = resp.json()
        if result.get('choices'):
            text = result['choices'][0]['message']['content']
            if text:
                return text
    except Exception:
        pass
    return None




def clean_gemini_output(text):
    """Filter Gemini output: remove lines that are pure noise (ETA, repeated (CBETA with no useful content).
    Keeps metadata lines with :, http, URLs, gXXXX(...) citations, CBETA refs like (CBETA T50n2060_p...)."""
    if not text:
        return text
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == 'ETA':
            continue
        if re.match(r'^\(CBETA[\s\(\)]*$', line):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)




# ── CBETA ref_passages cache table ──────────────────────────────────────

CBETA_REF_TABLE = 'cbeta_ref_passages'


CBETA_REF_DDL = """
CREATE TABLE IF NOT EXISTS {table} (
    ref_code          TEXT PRIMARY KEY,
    sigla             TEXT NOT NULL,
    juan              INTEGER,
    page              TEXT,
    line_start        INTEGER,
    line_end          INTEGER,
    han_text          TEXT NOT NULL,
    vi_summary        TEXT,
    vi_summary_raw    TEXT,
    vi_summary_clean  TEXT,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP
)
""".format(table=CBETA_REF_TABLE)




def ensure_cbeta_ref_table():
    conn = get_db_connection()
    try:
        conn.execute(CBETA_REF_DDL)
        # Migrate existing DB: add columns if missing
        for col in ['vi_summary_raw', 'vi_summary_clean']:
            try:
                conn.execute(f"ALTER TABLE {CBETA_REF_TABLE} ADD COLUMN {col} TEXT")
            except Exception:
                pass  # column already exists
        # Backfill: copy old vi_summary → vi_summary_raw where vi_summary_raw is empty
        conn.execute(f"""
            UPDATE {CBETA_REF_TABLE}
            SET vi_summary_raw = vi_summary
            WHERE vi_summary IS NOT NULL AND vi_summary != ''
              AND (vi_summary_raw IS NULL OR vi_summary_raw = '')
        """)
        conn.commit()
    finally:
        conn.close()




ensure_cbeta_ref_table()




# ── AI Person Name table (T231) ───────────────────────────────────────────
def ensure_ai_person_name_table():
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_person_name (
                dila_id     TEXT PRIMARY KEY,
                name_vi_ai  TEXT,
                model       TEXT DEFAULT 'gemini-3.8-flash',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()



ensure_ai_person_name_table()




# ── CBETA ref_explanations (Giải thích) cache table ──────────────────────

CBETA_EXPLAIN_TABLE = 'cbeta_ref_explanations'


CBETA_EXPLAIN_DDL = """
CREATE TABLE IF NOT EXISTS {table} (
    ref               TEXT NOT NULL,
    place_id          TEXT NOT NULL,
    place_han         TEXT NOT NULL,
    han_sentence      TEXT NOT NULL,
    explanation_vi    TEXT NOT NULL,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ref, place_id)
)
""".format(table=CBETA_EXPLAIN_TABLE)




def ensure_cbeta_explain_table():
    conn = get_db_connection()
    try:
        conn.execute(CBETA_EXPLAIN_DDL)
        conn.commit()
    finally:
        conn.close()




ensure_cbeta_explain_table()




def extract_sentence_with_place(han_block, place_han):
    """Split han_block into sentences, return the first sentence containing place_han."""
    if not han_block or not place_han:
        return (han_block or '').strip()
    sentences = re.split(r'[。！？]', han_block)
    for s in sentences:
        if place_han in s:
            return s.strip()
    return han_block.strip()[:300]




def build_name_map(han_text):
    """Query DILA + lexicon tables for Hán-Việt name pairs found in han_text.
    Returns dict {chinese_form: vietnamese_form} sorted by length descending.
    Sources: name_vi_map (persons), namevi_map_places (places)."""
    if not han_text:
        return {}
    conn = get_db_connection()
    name_map = {}
    try:
        # Person names
        rows = conn.execute(
            "SELECT name_zh, name_vi FROM name_vi_map WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in rows:
            zh = r['name_zh'].strip()
            vi = r['name_vi'].strip()
            if zh and vi and zh in han_text:
                name_map[zh] = vi
        # Place names
        rows = conn.execute(
            "SELECT name_zh, name_vi FROM namevi_map_places WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in rows:
            zh = r['name_zh'].strip()
            vi = r['name_vi'].strip()
            if zh and vi and zh in han_text:
                name_map[zh] = vi
    finally:
        conn.close()
    # Sort by length descending so longer matches take priority
    sorted_items = sorted(name_map.items(), key=lambda x: -len(x[0]))
    return dict(sorted_items)




def make_cbeta_prompt(han_text, name_map, ref):
    """Build Gemini prompt for CBETA translation with lexicon constraints."""
    if name_map:
        lex_lines = [f"{zh} → {vi}" for zh, vi in name_map.items()]
        lex_block = "\n".join(lex_lines)
        lex_section = f"""
[LEXICON HÁN-VIỆT BẮT BUỘC]
Các tên riêng dưới đây PHẢI được dịch đúng theo mapping sau:
{lex_block}

QUY ƯỚC TÊN RIÊNG:
- Mọi TÊN NGƯỜI, TÊN CHÙA, TÊN ĐỊA DANH trong đoạn phải dùng dạng Hán-Việt từ LEXICON.
- Không dùng dạng tiếng Anh hoặc Pinyin.
- Ví dụ: 少林寺 → Thiếu Lâm Tự (không dùng Shaolin Temple), 少林 → Thiếu Lâm (không dùng Shaolin).
- Nếu gặp tên riêng không có trong LEXICON, hãy đoán dạng Hán-Việt.
"""
    else:
        lex_section = """
QUY ƯỚC TÊN RIÊNG:
- Mọi tên người, tên chùa, tên địa danh phải dùng dạng Hán-Việt.
- Không dùng dạng tiếng Anh, Pinyin, hoặc phiên âm hiện đại.
- Ví dụ: 少林寺 → Thiếu Lâm Tự, 會稽 → Cối Kê.
"""

    prompt = f"""[HÁN GỐC]
{han_text}
{lex_section}
YÊU CẦU DỊCH THUẬT:
- Dịch đoạn Hán trên sang tiếng Việt hiện đại, mạch lạc, dễ hiểu.
- Giữ đủ thông tin về lai lịch nhân vật, bối cảnh địa danh, sự kiện tu học / hoằng pháp chính, kết cuộc (niên đại, nơi tịch nếu có).
- Văn phong tường thuật, nối câu mạch lạc (không chẻ thành câu vụn).
- Không liệt kê từng câu nguyên văn; chỉ cần 1 đoạn tiếng Việt hoàn chỉnh.

Độ dài:
- 1–2 câu Hán → 1–2 câu Việt.
- 3–5 câu Hán → 3–4 câu Việt.
- 5–10 câu Hán → 5–7 câu Việt.
- Không bao giờ chỉ ghi 1 câu chung chung.

Số hiệu mã: {ref}
"""
    return prompt.strip()




def parse_ref(ref_code):
    """Parse ref_code like 'T50n2060_p0457c16' into components.
    Returns dict with {sigla, canon, vol, text_num, page_comp, line_num} or None."""
    m = re.match(r'^([A-Z])(\d+)n(\d+)_p?(\d+)([a-z])(\d+)$', ref_code)
    if not m:
        return None
    canon, vol_str, text_num, page_num, col, line_str = m.groups()
    sigla = f"{canon}{vol_str}n{text_num}"
    page_comp = page_num + col  # e.g. '0457c'
    return {
        'sigla': sigla,
        'canon': canon,
        'vol': int(vol_str),
        'text_num': int(text_num),
        'page_comp': page_comp,
        'page_num': page_num,
        'col': col,
        'line_num': int(line_str),
    }




def _sync_ref_passage(ref, context=''):
    """Query cbeta.db for han_text for a single ref_code.
    If context given, search nearby pages for it when exact match fails.
    Returns dict with {han_text, sigla, title} or None if not found.
    Inserts/updates cbeta_ref_passages table."""
    parsed = parse_ref(ref)
    if not parsed:
        return None

    sigla = parsed['sigla']
    page_comp = parsed['page_comp']
    page_num = parsed['page_num']
    line_num = parsed['line_num']

    han_text = None
    title = sigla
    juan = None

    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id, title_zh, juan_count FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()
        if text_row:
            text_id = text_row['id']
            title = text_row['title_zh'] or sigla

            # Try exact page+col match first
            contents = cconn.execute("""
                SELECT juan, page, content_zh FROM cbeta_content_index
                WHERE text_id = ? AND (page = ? OR page = ?)
                ORDER BY rowid
            """, (text_id, page_comp, page_comp.upper())).fetchall()

            if not contents:
                # Fallback: page prefix match (first 4 digits)
                prefix = page_num
                contents = cconn.execute("""
                    SELECT juan, page, content_zh FROM cbeta_content_index
                    WHERE text_id = ? AND page LIKE ?
                    ORDER BY page, rowid LIMIT 20
                """, (text_id, f"{prefix}%")).fetchall()

            if not contents and context:
                # Context-aware fallback: search for context term in nearby pages
                nearby = cconn.execute("""
                    SELECT juan, page, content_zh FROM cbeta_content_index
                    WHERE text_id = ?
                    ORDER BY ABS(CAST(page AS INTEGER) - ?)
                    LIMIT 200
                """, (text_id, page_num)).fetchall()
                context_results = [r for r in nearby if r['content_zh'] and context in r['content_zh']]
                if context_results:
                    contents = context_results[:5]

            if contents:
                lines = [r['content_zh'] for r in contents]
                han_text = '\n'.join(lines)
                if han_text:
                    han_text = han_text[:50000]
                juan = contents[0]['juan']
        cconn.close()
    except Exception:
        pass

    if not han_text:
        han_text = ''

    # Upsert into cbeta_ref_passages
    conn = get_db_connection()
    try:
        conn.execute(f"""
            INSERT INTO {CBETA_REF_TABLE} (ref_code, sigla, juan, page, line_start, line_end, han_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ref_code) DO UPDATE SET
                sigla=excluded.sigla, juan=excluded.juan, page=excluded.page,
                line_start=excluded.line_start, line_end=excluded.line_end,
                han_text=excluded.han_text, updated_at=CURRENT_TIMESTAMP
        """, (ref, sigla, juan, page_comp, line_num, line_num, han_text))
        conn.commit()
    finally:
        conn.close()

    if not han_text:
        return None
    return {'han_text': han_text, 'sigla': sigla, 'title': title}




def _search_context_nearby(sigla, page_str, context):
    """Search cbeta.db for text containing context term near given page."""
    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id FROM cbeta_texts WHERE sigla = ?", (sigla,)
        ).fetchone()
        if not text_row:
            cconn.close()
            return None
        text_id = text_row['id']
        # Extract page number for proximity sort
        page_num = 0
        if page_str:
            try:
                page_num = int(''.join(filter(str.isdigit, page_str)) or 0)
            except ValueError:
                pass
        if not page_num:
            # fallback: just search anywhere in this text
            rows = cconn.execute("""
                SELECT content_zh FROM cbeta_content_index
                WHERE text_id = ? AND content_zh LIKE ?
                LIMIT 10
            """, (text_id, f'%{context}%')).fetchall()
        else:
            rows = cconn.execute("""
                SELECT juan, page, content_zh FROM cbeta_content_index
                WHERE text_id = ?
                ORDER BY ABS(CAST(SUBSTR(page,1,4) AS INTEGER) - ?)
                LIMIT 300
            """, (text_id, page_num)).fetchall()
            # Filter to those containing context
            rows = [r for r in rows if r['content_zh'] and context in r['content_zh']][:5]
        cconn.close()
        if rows:
            return '\n'.join(r['content_zh'] or '' for r in rows)[:50000]
    except Exception:
        pass
    return None




@app.route('/daoanh/api/admin/translate_gemini_cbeta', methods=['POST'])
def translate_gemini_cbeta():
    """
    POST /daoanh/api/admin/translate_gemini_cbeta
    Body: { ref: "T50n2060_p0574b20", context: "少林" }
    Flow:
    1) Check cbeta_ref_passages for cached vi_summary_clean → return instantly.
    2) If no han_text in table, sync from cbeta.db.
       - If context given, search for context term in nearby pages.
    3) Build name_map from lexicon (DILA + BIẾN THỂ DANH XƯNG).
    4) Call Gemini with lexicon-enhanced prompt → vi_summary_raw.
    5) Call Gemini again for 3–5 câu summary → vi_summary_clean.
    6) Cache both, return.
    """
    try:
        body = request.get_json(silent=True) or {}
        ref = (body.get('ref') or '').strip()
        context = (body.get('context') or '').strip()

        # If context is in the raw bibl string like "CBETA T50n2060_p0574b20 {少林}",
        # extract from { }
        if not context and '{' in ref:
            m = re.search(r'\{([^}]+)\}', ref)
            if m:
                context = m.group(1).strip()
                ref = re.sub(r'\s*\{[^}]*\}', '', ref).strip()
        # Also try to extract from body raw field
        if not context:
            raw_bibl = (body.get('raw') or '').strip()
            m = re.search(r'\{([^}]+)\}', raw_bibl)
            if m:
                context = m.group(1).strip()

        if not ref:
            return jsonify({"ok": False, "success": False, "error": "Thiếu ref"}), 400

        # 1) ALWAYS resolve fresh Han text from cbeta.db (Layer 1).
        #    _sync_ref_passage queries cbeta.db only, never joins Vietnamese tables.
        sync_result = _sync_ref_passage(ref, context)
        if not sync_result:
            return jsonify({
                "ok": False, "success": False, "error": "no_text",
                "message": f"Chưa có văn bản CBETA trong DB cho {ref}."
            })

        han_text = sync_result['han_text']
        sigla = sync_result['sigla']
        title = sync_result['title']

        # Extract sentence containing context (place_han) for focused LLM input
        han_sentence = extract_sentence_with_place(han_text, context) if context else ''
        llm_input = han_sentence if han_sentence else han_text

        # 2) ALWAYS translate fresh (no cache skip — stale vi_summary_clean must not block re-translation).
        #    After translation, the result is saved to cbeta_ref_passages for future display.

        # 3) Build name_map from lexicon (use full han_text for name scanning)
        name_map = build_name_map(han_text)

        # 4) Stage 1: Translate/dịch thô with lexicon-enhanced prompt (use llm_input for focus)
        prompt_raw = make_cbeta_prompt(llm_input, name_map, ref)
        text_vi_raw = _call_gemini(prompt_raw, timeout=15)
        provider_raw = 'gemini-3.6-flash'

        if not text_vi_raw:
            try:
                import translators as ts
                text_vi_raw = ts.translate_text(llm_input[:3000], to_language='vi', translator='google')
                provider_raw = 'google-translate'
            except Exception:
                pass

        if text_vi_raw:
            text_vi_raw = clean_gemini_output(text_vi_raw)
            # Hán-Việt normalization (local, no API)
            global _hanviet_glossary
            if _hanviet_glossary is None:
                _hanviet_glossary = hanviet_load_glossary()
            text_vi_raw = hanviet_normalize(text_vi_raw, _hanviet_glossary)

        # 5) Stage 2: Tóm lược 3–5 câu from raw (always runs regardless of provider)
        text_vi_clean = None
        if text_vi_raw:
            # Try Gemini summarization first
            summary_prompt = f"""Dưới đây là bản dịch/tóm tắt tiếng Việt của một đoạn trích CBETA:

{text_vi_raw}

Hãy tóm tắt lại thành một đoạn 3–5 câu tiếng Việt mạch lạc, rõ ràng, hướng tới độc giả phổ thông.
Giữ nguyên các tên Hán-Việt (như chùa, người, địa danh).
Chỉ tường thuật khách quan, không thêm bình luận."""
            text_vi_clean = _call_gemini(summary_prompt, timeout=10)
            if text_vi_clean:
                text_vi_clean = hanviet_normalize(text_vi_clean, _hanviet_glossary)
            else:
                # Non-Gemini fallback: extractive summary + lexicon fixes + normalize
                text_vi_clean = _polish_fallback(text_vi_raw, han_text)

        # 6) Cache both
        polished_result = None
        if text_vi_raw or text_vi_clean:
            conn = get_db_connection()
            try:
                conn.execute(
                    f"""UPDATE {CBETA_REF_TABLE}
                        SET vi_summary_raw = ?, vi_summary_clean = ?,
                            vi_summary = COALESCE(?, vi_summary),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ref_code = ?""",
                    (text_vi_raw or '', text_vi_clean or '', text_vi_clean or '', ref)
                )
                conn.commit()
            finally:
                conn.close()

            # 7) "Dịch mượt" — polish the raw text using improve_grammar + normalize_terms
            try:
                step1 = improve_grammar(text_vi_raw or '', han_text)
                corrected = step1.get('corrected_text', text_vi_raw or '')
                uncertain = step1.get('uncertain_terms', [])
                step2 = normalize_terms(corrected, uncertain)
                polished_result = {
                    'polishedText': step2['correctedText'],
                    'uncertainMappings': [m for m in step2['mappings'] if m['confidence'] < 0.9],
                    'metadata': {
                        'termsReplaced': sum(1 for m in step2['mappings'] if m['confidence'] >= 0.9),
                        'termsUncertain': sum(1 for m in step2['mappings'] if m['confidence'] >= 0.7 and m['confidence'] < 0.9),
                        'termsManual': sum(1 for m in step2['mappings'] if m['confidence'] < 0.7),
                    }
                }
            except Exception:
                pass

            resp = {
                "ok": True, "success": True,
                "vi_summary_clean": text_vi_clean or '',
                "vi_summary_raw": text_vi_raw or '',
                "sigla": sigla, "title": title,
                "provider": provider_raw,
            }
            if polished_result:
                resp['polished'] = polished_result
            return jsonify(resp)

        return jsonify({"ok": False, "success": False, "error": "translate_failed", "message": "Không thể dịch đoạn CBETA này"})

    except Exception as e:
        import traceback
        app.logger.error(f"translate_gemini_cbeta error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "success": False, "error": "internal_error", "message": str(e)})




# ── Non-LLM helpers (used when Gemini is unavailable) ─────────────────

def _extractive_summarize(text, max_sentences=5):
    """Score sentences by info density + position, pick top N, keep original order.
    Works without any LLM."""
    if not text:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 10]
    if not sentences:
        return text[:2000]
    if len(sentences) <= max_sentences:
        return ' '.join(sentences)
    cjk = re.compile(r'[\u4e00-\u9fff]')
    scored = []
    for i, s in enumerate(sentences):
        cjk_count = len(cjk.findall(s))
        # Score: length + CJK info density + position bonus
        score = len(s) + cjk_count * 3 + max(0, 50 - i)
        scored.append((score, i, s))
    scored.sort(key=lambda x: -x[0])
    top = sorted([item[1] for item in scored[:max_sentences]])
    return ' '.join(sentences[i] for i in top)




def _apply_lexicon_fixes(text, han_text):
    """Replace leftover Chinese chars + correct known names from lexicon.
    Uses build_name_map to find Hán-Việt mappings present in han_text."""
    if not text or not han_text:
        return text
    name_map = build_name_map(han_text)
    if not name_map:
        return text
    result = text
    # 1. Replace remaining CJK chars that match lexicon keys
    for zh, vi in name_map.items():
        if zh in result:
            result = result.replace(zh, vi)
    # 2. Scan for English/pinyin fragments near known names.
    #    For each (zh→vi) pair, check if any word in result is a fuzzy
    #    match for the pinyin-initial or wrong Vietnamese of that name.
    #    Only run when rapidfuzz is available.
    try:
        from rapidfuzz import fuzz
        words = re.findall(r'\b[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơỳỵỷỹý\']+\b', result)
        for zh, vi in name_map.items():
            # Try matching each word against known variants
            for w in words:
                # If word looks like pinyin (short, no diacritics)
                if re.match(r'^[a-zA-Z]{2,12}$', w):
                    r = fuzz.ratio(w.lower(), vi.lower())
                    if r > 70:
                        result = result.replace(w, vi)
                        break
    except Exception:
        pass
    return result




def _polish_fallback(text, han_text):
    """Full non-Gemini polish pipeline used when Gemini is unavailable.
    Order: extractive_summarize → lexicon_fixes → hanviet_normalize."""
    if not text:
        return text
    # 1. Extractive summary (remove fragments, keep best sentences)
    result = _extractive_summarize(text)
    # 2. Fix names using lexicon
    result = _apply_lexicon_fixes(result, han_text)
    # 3. Hán-Việt normalization
    global _hanviet_glossary
    if _hanviet_glossary is None:
        _hanviet_glossary = hanviet_load_glossary()
    result = hanviet_normalize(result, _hanviet_glossary)
    # 4. Clean up repeated words and common artifacts
    result = re.sub(r'\b(\w+)\s+\1\b', r'\1', result)  # "là là" → "là"
    result = re.sub(r'\s+', ' ', result).strip()
    # 5. Ensure proper ending
    if result and not result[-1] in '.!?':
        result += '.'
    return result




# ── "DỊCH MƯỢT" — Polish translation module ──────────────────────────────

def improve_grammar(raw_text, han_source):
    """Step 1: LLM grammar correction + extract uncertain terms.
    Returns dict with {corrected_text, uncertain_terms}.
    Falls back to hanviet_normalize + empty uncertain_terms if Gemini unavailable."""
    from hanviet_normalization import normalize_text as hv_normalize, load_glossary as hv_glossary
    prompt = f"""Bạn là chuyên gia biên tập văn bản Phật học tiếng Việt.

NGUỒN HÁN (CBETA):
{han_source[:800]}

BẢN DỊCH THÔ (cần sửa):
{raw_text}

YÊU CẦU:
1. Sửa lỗi ngữ pháp, cú pháp tiếng Việt (ví dụ: "Thả Kinh Đà ra" → "Thích Kinh Đà").
2. Loại bỏ thuật ngữ máy móc (ví dụ: "hạt nhân nhỏ và lớn" → "việc lớn nhỏ").
3. Đánh dấu các tên riêng (nhân danh, địa danh) chưa chắc bằng {{{{TERM:tên}}}}
4. KHÔNG thêm/bớt thông tin so với bản gốc.
5. Giữ nguyên tên Hán-Việt đã đúng (Thiếu Lâm Tự, Cối Kê, v.v.)

TRẢ VỀ JSON (không markdown, chỉ raw JSON):
{{"corrected_text": "...", "uncertain_terms": ["tên1", "tên2"]}}"""

    try:
        text = _call_gemini(prompt, timeout=15)
        if text:
            text = clean_gemini_output(text)
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            result = json.loads(text)
            if isinstance(result, dict) and 'corrected_text' in result:
                return result
    except Exception:
        pass
    # Fallback: run full non-Gemini polish pipeline
    return {'corrected_text': _polish_fallback(raw_text, han_source), 'uncertain_terms': []}




def normalize_terms(text, uncertain_terms):
    """Step 2: Query lexicon with exact + fuzzy matching for each uncertain term.
    Uses name_vi_map (persons) + namevi_map_places (places) + lexicon table.
    Returns dict with {correctedText, mappings}."""
    from rapidfuzz import fuzz
    conn = get_db_connection()
    mappings = []
    text_result = text

    # Build candidate list from lexicon tables
    candidates = []
    try:
        person_rows = conn.execute(
            "SELECT name_zh, name_vi FROM name_vi_map WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in person_rows:
            candidates.append({'han': r['name_zh'], 'viet': r['name_vi'], 'type': 'person'})

        place_rows = conn.execute(
            "SELECT name_zh, name_vi FROM namevi_map_places WHERE name_zh IS NOT NULL AND name_zh != ''"
        ).fetchall()
        for r in place_rows:
            candidates.append({'han': r['name_zh'], 'viet': r['name_vi'], 'type': 'place'})
    finally:
        conn.close()

    # Also add built-in English→Hán-Việt mappings from normalization module
    try:
        # Import the fixed glossary for additional matching
        import importlib
        hv_mod = importlib.import_module('hanviet_normalization')
        for k, v in hv_mod.FIXED_GLOSSARY_EN.items():
            if len(k) >= 3:
                candidates.append({'han': k, 'viet': v, 'type': 'builtin_en'})
        for k, v in hv_mod.FIXED_GLOSSARY_VI.items():
            if len(k) >= 3:
                candidates.append({'han': k, 'viet': v, 'type': 'builtin_vi'})
    except Exception:
        pass

    for term in uncertain_terms:
        # Exact match first
        exact = None
        for c in candidates:
            if term.lower() == c['viet'].lower() or term.lower() == c['han'].lower():
                exact = c
                break
        if exact:
            mappings.append({
                'original': term,
                'normalized': exact['viet'],
                'han': exact['han'],
                'confidence': 1.0,
                'source': 'exact'
            })
            text_result = text_result.replace(f'{{{{TERM:{term}}}}}', f"{exact['viet']} ({exact['han']})")
            continue

        # Fuzzy match
        scored = []
        for c in candidates:
            score = fuzz.ratio(term.lower(), c['viet'].lower()) / 100.0
            if score > 0.7:
                scored.append({'han': c['han'], 'viet': c['viet'], 'confidence': score})
            score2 = fuzz.ratio(term.lower(), c['han'].lower()) / 100.0
            if score2 > 0.7:
                scored.append({'han': c['han'], 'viet': c['viet'], 'confidence': score2})

        if scored:
            best = max(scored, key=lambda x: x['confidence'])
            confidence = best['confidence']
            mappings.append({
                'original': term,
                'normalized': best['viet'],
                'han': best['han'],
                'confidence': confidence,
                'source': 'fuzzy'
            })
            if confidence >= 0.9:
                text_result = text_result.replace(
                    f'{{{{TERM:{term}}}}}',
                    f"{best['viet']} ({best['han']})"
                )
            elif confidence >= 0.7:
                text_result = text_result.replace(
                    f'{{{{TERM:{term}}}}}',
                    f"<mark class='cbeta-uncertain' data-original='{term}' data-han='{best['han']}' data-confidence='{confidence:.2f}'>{best['viet']}</mark>"
                )
        else:
            mappings.append({
                'original': term,
                'normalized': term,
                'han': '???',
                'confidence': 0.0,
                'source': 'manual_required'
            })
            text_result = text_result.replace(
                f'{{{{TERM:{term}}}}}',
                f"<span class='cbeta-manual-edit'>{term}</span>"
            )

    # Clean up any remaining unprocessed TERM markers
    text_result = re.sub(r'\{\{TERM:([^}]+)\}\}', r'\1', text_result)

    return {'correctedText': text_result, 'mappings': mappings}




def _resolve_dila_id(conn, place_id):
    """Resolve dila_id for any place identifier. Returns (dila_id, name_zh).
    Accepts: places_dila.id directly ('PL000000023255') or places.id (integer as str).
    """
    # Case 1: place_id is already a valid places_dila.id — return directly
    # T101 BUG-001: dùng places_dila.name (tên chính thức DILA) thay vì name_zh
    # (name_zh có thể chứa tên alternative, vd 少室寺 thay vì 少林寺 cho PL000000023255)
    dila_row = conn.execute("SELECT name, name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
    if dila_row:
        return place_id, dila_row['name'] or dila_row['name_zh']

    # Case 2: place_id is places.id (integer primary key) — find via namevi_map
    row = conn.execute("SELECT name_zh FROM places WHERE id = ?", (place_id,)).fetchone()
    if not row:
        return None, None
    name_zh = row['name_zh']
    nm = conn.execute(
        "SELECT dila_id FROM namevi_map_places WHERE name_zh = ? AND dila_id IS NOT NULL ORDER BY (vn_name_status='reviewed') DESC, (source='manual') DESC, confidence DESC LIMIT 1",
        (name_zh,)
    ).fetchone()
    if not nm:
        return None, name_zh
    dila_id = nm['dila_id']
    # Expand short DILA IDs (PL023255 → PL000000023255) if needed
    check = conn.execute("SELECT id FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
    if not check and dila_id.startswith('PL'):
        padded = 'PL' + dila_id[2:].zfill(12)
        if conn.execute("SELECT id FROM places_dila WHERE id = ? LIMIT 1", (padded,)).fetchone():
            dila_id = padded
    return dila_id, name_zh




_BUDDHIST_SYSTEM_PROMPT = """Bạn là dịch giả Hán-Việt chuyên về văn học Phật giáo Bắc Tông Việt Nam.
Quy tắc bắt buộc:
- Tăng nhân: 釋X → Thích X (KHÔNG phiên âm pinyin)
- Địa danh: dùng âm Hán-Việt (雍州→Ung Châu, 嵩山→Tung Sơn, 河南→Hà Nam)
- Thuật ngữ cố định: 舍利→xá-lợi, 菩薩→Bồ Tát, 禪→Thiền, 涅槃→Niết-bàn, 比丘→Tỳ-kheo
- 下流 trong văn ngôn = chảy xuống hạ lưu (KHÔNG phải "tục tĩu")
- Giữ tên kinh điển bằng Hán-Việt (大藏經→Đại Tạng Kinh, 高僧傳→Cao Tăng Truyện)
- Văn phong: tự nhiên, chuẩn văn học Phật giáo Việt Nam, không dịch từng chữ
- Chỉ dịch, không giải thích hay chú thích"""




# ── T55b Related Texts (Trích Dẫn Tự Động) ─────────────────────────────
# Batch F (2026-09-10) — additive, read-only endpoint, 0 bảng mới, 0 ALTER.
# Group 1 = crossref (SAT / Toh / Pali) · Group 2 = topic (co-mentioned texts
# qua DILA persons · verified 72,628 rows) · Group 3 = persons xuất hiện.
# KHÔNG ghi đè "Kinh Điển Liên Quan" `/api/places/<id>/cbeta` — endpoint mới độc lập.

def _t55_normalize_sigla(raw):
    """Trả tuple (short_key, text_num): 'T50n2059' → ('T2059','2059') · 'T0251' → ('T0251','251') · 'X77n1524' → ('X1524','1524')."""
    s = (raw or '').strip()
    m = re.match(r'(T|X)\s*(\d+)n(\d+)', s, re.I)
    if m:
        return ('{}{:04d}'.format(m.group(1).upper(), int(m.group(3))), str(int(m.group(3))))
    m2 = re.match(r'(T|X)\s*0*(\d+)', s, re.I)
    if m2:
        return ('{}{:04d}'.format(m2.group(1).upper(), int(m2.group(2))), str(int(m2.group(2))))
    return (s.upper(), None)




# ── T86 — Truyền Thừa (Lineage Research Workspace) ────────────────────────────────
# Redesign tab TRUYỀN THỪA thành workspace 3 cột (sidebar / tree canvas / inspector +
# evidence drawer). Dữ liệu 100% thật từ Marcus SNA (marcus_networks qua bridge
# marcus_people_link ↔ people), KHÔNG bịa. Hai endpoint mới:
#   1) GET /daoanh/api/monk/<dila_id>/lineage-tree  — cây phả hệ đệ quy (n tầng thầy/trò,
#      lazy mở sâu hơn), mỗi edge mang citation ref thật + has_ref (proxy dẫn chứng).
#   2) GET /daoanh/api/lineage-ref/passage          — resolve chuỗi dẫn chiếu CBETA → passage
#      (mở Đọc trong Đại Tạng), trung thực null nếu passage chưa được lập chỉ mục.
import re as _re86


import threading as _t148_threading


import xml.etree.ElementTree as _t148_ET



# T148: Lazy index toàn bộ DILA Person Authority XML vào RAM (chạy lần đầu, ~3-5s)
_T148_DILA_EXTRA = {}           # pid → {bio_extensive, alt_names, listbibl, works_tripitaka, works_by, mentioned_in, active_at,


                                #         name_latin, occupation, place_of_origin, birth_death_quote, wikidata_id, birth_date, death_date, death_note}
_T148_EXTRA_LOADED = False


_T148_EXTRA_LOCK = _t148_threading.Lock()


_T148_PERSON_XML = os.path.join(
    os.path.dirname(__file__),
    'data', 'dila_import', 'Authority-Databases', 'authority_person',
    'Buddhist_Studies_Person_Authority.xml'
)


_T148_NS = 'http://www.tei-c.org/ns/1.0'


_T148_XML_NS = 'http://www.w3.org/XML/1998/namespace'




def _t148_load_dila_extra():
    """Parse DILA Person Authority XML từ DB (ttl_v2_source_records.raw_text),
    lưu vào _T148_DILA_EXTRA. Mỗi person ID có thể có nhiều XML records → merge."""
    global _T148_DILA_EXTRA, _T148_EXTRA_LOADED
    with _T148_EXTRA_LOCK:
        if _T148_EXTRA_LOADED:
            return
        idx = {}
        ns = _T148_NS
        xml_ns = _T148_XML_NS
        try:
            t0 = time.time()
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            # Query tất cả raw XML DILA từ DB
            rows = conn.execute(
                "SELECT id, raw_text FROM ttl_v2_source_records WHERE kind='DILA_XML' AND raw_text IS NOT NULL"
            ).fetchall()
            conn.close()
            print(f'[T148] Queried {len(rows)} DILA_XML records from DB', flush=True)

            for row in rows:
                rec_id, xml_text = row['id'], row['raw_text']
                if not xml_text or not isinstance(xml_text, str):
                    continue
                try:
                    # Parse XML string (không parse từ file)
                    root = _t148_ET.fromstring(xml_text)
                except Exception as ex:
                    print(f'[T148] Parse error in record {rec_id}: {ex}', flush=True)
                    continue

                # Iterate persons trong XML này
                for elem in root.iter(f'{{{ns}}}person'):
                    pid = elem.get(f'{{{xml_ns}}}id') or elem.get('xml:id')
                    if not pid:
                        continue
                    # Init data fields (hoặc merge nếu pid đã có)
                    existing = idx.get(pid, {})
                    alt_names = list(existing.get('alt_names', []))
                    listbibl = list(existing.get('listbibl', []))
                    listbibl_items = list(existing.get('listbibl_items', []))
                    bio_extensive = existing.get('bio_extensive')
                    works_tripitaka = existing.get('works_tripitaka')
                    works_by = existing.get('works_by')
                    secondary_lit = existing.get('secondary_lit')
                    mentioned_in = existing.get('mentioned_in')
                    mentioned_in_refs = list(existing.get('mentioned_in_refs', []))
                    active_at = existing.get('active_at')
                    name_latin = existing.get('name_latin')
                    occupation = existing.get('occupation')
                    place_of_origin = existing.get('place_of_origin')
                    birth_death_quote = existing.get('birth_death_quote')
                    wikidata_id = existing.get('wikidata_id')
                    wikidata_ids = list(existing.get('wikidata_ids', []))
                    birth_date = existing.get('birth_date')
                    death_date = existing.get('death_date')
                    death_note = existing.get('death_note')
                    relations = list(existing.get('relations', []))
                    sex_val = existing.get('sex')
                    dynasty_xml = existing.get('dynasty_xml')
                    is_monk = existing.get('is_monk')

                    for child in elem:
                        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        if tag == 'persName':
                            ptype = child.get('type', '')
                            lang = child.get(f'{{{xml_ns}}}lang', '')
                            txt = (child.text or '').strip()
                            if ptype == 'alternative' and txt:
                                alt_names.append(txt)
                            elif not ptype and lang and lang not in ('zho-Hant', 'vie') and txt and not name_latin:
                                name_latin = txt
                        elif tag == 'listBibl':
                            for bibl in child:
                                t = (bibl.text or '').strip()
                                ref_url = ''
                                ref_el = bibl.find(f'{{{ns}}}ref')
                                if ref_el is not None:
                                    ref_url = (ref_el.get('target') or '').strip()
                                    if not t:
                                        t = (ref_el.text or '').strip()
                                if t:
                                    listbibl.append(t)
                                    # T372 (2026-10-13): giữ song song url từ <ref target=...>
                                    # để renderer dựng <a href>; listbibl (plain text) giữ
                                    # nguyên format cũ cho AI-translate prompt (dila_translate).
                                    listbibl_items.append({'text': t, 'url': ref_url})
                        elif tag == 'note':
                            ntype = child.get('type', '')
                            txt = (child.text or '').strip()
                            if ntype == 'extensive' and txt:
                                bio_extensive = txt
                            elif ntype == 'worksInTripitaka' and txt:
                                works_tripitaka = txt
                            elif ntype == 'worksBy' and txt:
                                works_by = txt
                            elif ntype == 'secondaryLit' and txt:
                                secondary_lit = txt
                            elif ntype == 'mentionedIn':
                                refs = []
                                if txt:
                                    refs.append({'text': txt, 'url': ''})
                                for ref_el in child.findall(f'{{{ns}}}ref'):
                                    ref_text = (ref_el.text or '').strip()
                                    ref_url = (ref_el.get('target') or '').strip()
                                    if ref_text:
                                        refs.append({'text': ref_text, 'url': ref_url})
                                if refs:
                                    mentioned_in = '\n'.join(r['text'] for r in refs)
                                    mentioned_in_refs = refs
                            elif ntype == 'activeAt' and txt:
                                active_at = txt
                            elif ntype == 'birthDeathDateQuote' and txt:
                                birth_death_quote = txt
                            elif ntype == 'dynasty' and txt:
                                dynasty_xml = txt
                            elif ntype == 'monk' and txt:
                                is_monk = txt
                            elif ntype == 'placeOfOrigin':
                                pl_el = child.find(f'{{{ns}}}placeName')
                                if pl_el is not None:
                                    pl_txt = (pl_el.text or '').strip()
                                    if pl_txt:
                                        place_of_origin = pl_txt
                        elif tag == 'occupation':
                            txt = (child.text or '').strip()
                            if txt and not occupation:
                                occupation = txt
                        elif tag == 'birth':
                            txt = (child.text or '').strip()
                            if txt:
                                birth_date = txt
                        elif tag == 'death':
                            txt = (child.text or '').strip()
                            if txt:
                                death_date = txt
                            dn_el = child.find(f'{{{ns}}}note')
                            if dn_el is not None:
                                dn = (dn_el.text or '').strip()
                                if dn:
                                    death_note = dn
                        elif tag == 'idno' and child.get('type') == 'Wikidata':
                            txt = (child.text or '').strip()
                            if txt:
                                # T372: XML có thể có nhiều <idno type="Wikidata">
                                # (vd A000074 có 2 QID) — giữ wikidata_id (tương thích
                                # cũ, QID đầu tiên) VÀ wikidata_ids (đủ danh sách).
                                if not wikidata_id:
                                    wikidata_id = txt
                                if txt not in wikidata_ids:
                                    wikidata_ids.append(txt)
                        elif tag == 'sex':
                            sv = child.get('value', '').strip()
                            if sv == '1':
                                sex_val = 'Nam'
                            elif sv == '2':
                                sex_val = 'Nữ'
                            elif sv:
                                sex_val = sv
                        elif tag == 'listRelation':
                            for rel in child:
                                rel_tag = rel.tag.split('}')[-1] if '}' in rel.tag else rel.tag
                                if rel_tag != 'relation':
                                    continue
                                rel_type = rel.get('type', '')
                                active   = rel.get('active', '')
                                name_n   = rel.get('n', '')
                                bibl_text = ''
                                ref_url   = ''
                                desc_el = rel.find(f'{{{ns}}}desc')
                                if desc_el is not None:
                                    bibl_el = desc_el.find(f'{{{ns}}}bibl')
                                    if bibl_el is not None:
                                        bibl_text = (bibl_el.text or '').strip()
                                    ref_el = desc_el.find(f'{{{ns}}}ref')
                                    if ref_el is not None:
                                        ref_url = ref_el.get('target', '') or (ref_el.text or '').strip()
                                if rel_type and active:
                                    relations.append({
                                        'type': rel_type,
                                        'person_id': active,
                                        'name': name_n,
                                        'bibl': bibl_text,
                                        'ref_url': ref_url,
                                    })

                    has_data = (bio_extensive or alt_names or listbibl or works_tripitaka or works_by
                                or secondary_lit or mentioned_in or active_at or name_latin or occupation
                                or place_of_origin or birth_death_quote or wikidata_id
                                or birth_date or death_date or relations or sex_val
                                or dynasty_xml or is_monk)
                    if has_data:
                        idx[pid] = {
                            'bio_extensive': bio_extensive,
                            'alt_names': alt_names,
                            'sex': sex_val,
                            'listbibl': listbibl,
                            'listbibl_items': listbibl_items,
                            'works_tripitaka': works_tripitaka,
                            'works_by': works_by,
                            'secondary_lit': secondary_lit,
                            'mentioned_in': mentioned_in,
                            'mentioned_in_refs': mentioned_in_refs,
                            'active_at': active_at,
                            'name_latin': name_latin,
                            'occupation': occupation,
                            'place_of_origin': place_of_origin,
                            'birth_death_quote': birth_death_quote,
                            'wikidata_id': wikidata_id,
                            'wikidata_ids': wikidata_ids,
                            'birth_date': birth_date,
                            'death_date': death_date,
                            'death_note': death_note,
                            'relations': relations,
                            'dynasty_xml': dynasty_xml,
                            'is_monk': is_monk,
                        }

            _T148_DILA_EXTRA = idx
            elapsed = time.time() - t0
            print(f'[T148] Đã index {len(idx)} persons từ DILA XML DB trong {elapsed:.1f}s', flush=True)
        except Exception as ex:
            _T148_DILA_EXTRA = idx
            print(f'[T148] Lỗi parse DILA XML từ DB tại ~{len(idx)} persons: {ex}', flush=True)
        finally:
            _T148_EXTRA_LOADED = True




def _t148_get_extra(pid):
    """Trả về extra DILA data cho một person id (load lazily)."""
    if not _T148_EXTRA_LOADED:
        _t148_load_dila_extra()
    return _T148_DILA_EXTRA.get(pid) or {}




def _t86_person_info(conn, pid):
    """Tên/niên hiệu/tông phái/môn phái cho một node lineage.
    Ưu tiên marcus_reference → people (DILA) → ttl_persons (T186 danh tăng VN local)."""
    marc = conn.execute(
        "SELECT label, label_vi, birth_year, death_year FROM marcus_reference WHERE node_id = ?",
        (pid,)
    ).fetchone()
    person = conn.execute(
        "SELECT name_zh, name_vi, dynasty, sect, bio FROM people WHERE id = ?", (pid,)
    ).fetchone()
    # T186: fallback sang ttl_persons nếu không có trong DILA
    ttl_person = None
    if not person:
        try:
            ttl_person = conn.execute(
                "SELECT name_vi, name_zh, note FROM ttl_persons WHERE id = ?", (pid,)
            ).fetchone()
        except sqlite3.OperationalError as e:
            if 'no such table' not in str(e).lower():
                raise
            # ttl_persons table doesn't exist - ignore silently
            pass
    zh = (marc['label'] if marc and marc['label'] else None) \
        or (person['name_zh'] if person else None) \
        or (ttl_person['name_zh'] if ttl_person else None) or pid
    vi = None
    if marc and marc['label_vi'] and marc['label_vi'] != zh:
        vi = marc['label_vi']
    elif person and person['name_vi']:
        vi = person['name_vi']
    elif ttl_person and ttl_person['name_vi']:
        vi = ttl_person['name_vi']
    vi = vi or zh
    # source_type giúp UI hiển thị badge "Danh tăng VN – TTL local"
    source_type = 'ttl_local' if ttl_person else 'dila'
    return {
        "id": pid,
        "name_vi": vi,
        "name_zh": zh,
        "dynasty": person['dynasty'] if person else None,
        "sect": person['sect'] if person else None,
        "birth_year": (marc['birth_year'] if marc else None),
        "death_year": (marc['death_year'] if marc else None),
        "bio": (person['bio'] if person else None) or
               (ttl_person['note'] if ttl_person else None) or None,
        "source_type": source_type,
    }




def _t86_neighbors(conn, person_id, direction):
    """Lấy neighbors của một person theo marcus_networks (thầy/trò).
    direction: 'up' = thầy (student_id=person), 'down' = trò (teacher_id=person).
    Mọi marcus node id đều ánh xạ ngược qua marcus_people_link → person DILA (nếu có)."""
    link = conn.execute(
        "SELECT marcus_node_id FROM marcus_people_link WHERE person_id = ?", (person_id,)
    ).fetchone()
    if not link:
        return [], 0
    nid = link['marcus_node_id']
    rows = []
    if direction == 'up':
        rows = conn.execute(
            "SELECT teacher_id AS id, ref FROM marcus_networks WHERE student_id = ?", (nid,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT student_id AS id, ref FROM marcus_networks WHERE teacher_id = ?", (nid,)
        ).fetchall()
    # Map marcus node id → person DILA id (node id == person id trong dataset này,
    # nhưng vẫn resolve qua bridge cho chắc).
    out = []
    for r in rows:
        nbr = conn.execute(
            "SELECT person_id FROM marcus_people_link WHERE marcus_node_id = ?", (r['id'],)
        ).fetchone()
        pid = (nbr['person_id'] if nbr else r['id'])
        out.append({"id": pid, "ref": r['ref']})
    return out, len(rows)




def _t158_neighbors_consensus(conn, person_id, direction, include_single=False):
    """T158 — Lấy neighbors từ lineage_edge_consensus thay vì marcus_networks.
    direction: 'up' = thầy (person là trò), 'down' = trò (person là thầy).
    include_single: True → bao gồm cả single_source edges (cho optional filter).
    T187: LEFT JOIN lineage_primary_teacher để thêm is_primary vào kết quả.
    direction='up' ORDER BY is_primary DESC, ttl_asserted DESC, agreeing_source_count DESC
    → thầy truyền pháp ấn luôn đứng đầu, thầy tham học (is_primary=-1) xếp cuối.
    """
    vis_cond = "1" if include_single else "c.is_default_visible=1"
    if direction == 'up':
        sql = (
            "SELECT c.teacher_id AS id, c.source_badge, c.agreeing_source_count,"
            " c.dila_asserted, c.marcus_asserted, c.ttl_asserted,"
            " c.consensus_status, c.is_default_visible,"
            " COALESCE(lpt.is_primary, 0) AS is_primary,"
            " lpt.evidence_source AS pt_evidence, lpt.confidence AS pt_confidence"
            " FROM lineage_edge_consensus c"
            " LEFT JOIN lineage_primary_teacher lpt"
            "   ON lpt.teacher_id=c.teacher_id AND lpt.disciple_id=c.disciple_id"
            f" WHERE c.disciple_id=? AND c.relation_type='dharma_transmission' AND {vis_cond}"
            " ORDER BY COALESCE(lpt.is_primary,0) DESC, c.ttl_asserted DESC, c.agreeing_source_count DESC"
        )
    else:
        sql = (
            "SELECT c.disciple_id AS id, c.source_badge, c.agreeing_source_count,"
            " c.dila_asserted, c.marcus_asserted, c.ttl_asserted,"
            " c.consensus_status, c.is_default_visible,"
            " COALESCE(lpt.is_primary, 0) AS is_primary,"
            " lpt.evidence_source AS pt_evidence, lpt.confidence AS pt_confidence"
            " FROM lineage_edge_consensus c"
            " LEFT JOIN lineage_primary_teacher lpt"
            "   ON lpt.teacher_id=c.teacher_id AND lpt.disciple_id=c.disciple_id"
            f" WHERE c.teacher_id=? AND c.relation_type='dharma_transmission' AND {vis_cond}"
            " ORDER BY c.agreeing_source_count DESC, c.disciple_id"
        )
    rows = conn.execute(sql, (person_id,)).fetchall()
    return [dict(r) for r in rows], len(rows)




def _t426_neighbors_view(conn, person_id, direction, view_name):
    """T426 — Lấy neighbors từ VIEW T425 (v_tree_dila/marcus/ttl/overlay).
    direction: 'up' = thầy (person là trò), 'down' = trò (person là thầy).
    view_name: 'dila', 'marcus', 'ttl', 'overlay'.
    Không có is_primary (VIEW không join lineage_primary_teacher).
    """
    if view_name not in ('dila', 'marcus', 'ttl', 'overlay'):
        return [], 0

    if view_name == 'overlay':
        # v_tree_overlay dùng teacher_id/disciple_id, đã GROUP BY
        if direction == 'up':
            sql = (
                "SELECT teacher_id AS id, '' AS source_badge, n_sources AS agreeing_source_count,"
                " 1 AS is_primary"
                " FROM v_tree_overlay"
                " WHERE disciple_id=?"
                " ORDER BY n_sources DESC, teacher_id"
            )
        else:
            sql = (
                "SELECT disciple_id AS id, '' AS source_badge, n_sources AS agreeing_source_count,"
                " 1 AS is_primary"
                " FROM v_tree_overlay"
                " WHERE teacher_id=?"
                " ORDER BY n_sources DESC, disciple_id"
            )
    else:
        # v_tree_dila/marcus/ttl dùng subject_person_id/object_person_id
        view = f"v_tree_{view_name}"
        if direction == 'up':
            sql = (
                f"SELECT subject_person_id AS id, source_code AS source_badge,"
                f" 1 AS agreeing_source_count, 1 AS is_primary"
                f" FROM {view}"
                f" WHERE object_person_id=?"
                f" ORDER BY subject_person_id"
            )
        else:
            sql = (
                f"SELECT object_person_id AS id, source_code AS source_badge,"
                f" 1 AS agreeing_source_count, 1 AS is_primary"
                f" FROM {view}"
                f" WHERE subject_person_id=?"
                f" ORDER BY object_person_id"
            )
    rows = conn.execute(sql, (person_id,)).fetchall()
    return [dict(r) for r in rows], len(rows)




def _t86_person_conflict(conn, person_id):
    """Real conflict marker từ lineage_conflicts_v2 (sai lệch DILA vs Marcus về
    tập thầy/trò). Chỉ đánh dấu khi is_conflict=1 — không bịa.
    issue_category: 'source_coverage_gap' (một bên=0 hoặc có overlap) vs
    'direction_disagreement' (cả hai>0, không overlap — mâu thuẫn thật)."""
    import json as _json
    rows = conn.execute(
        "SELECT conflict_type, notes, dila_count, marcus_count, dila_data, marcus_data "
        "FROM lineage_conflicts_v2 WHERE person_id=? AND is_conflict=1 AND resolved=0",
        (person_id,)
    ).fetchall()
    result = []
    for r in rows:
        dc = r['dila_count'] or 0
        mc = r['marcus_count'] or 0
        dila_ids, marcus_ids = [], []
        try:
            dila_ids = list(_json.loads(r['dila_data'] or '[]'))
            marcus_ids = list(_json.loads(r['marcus_data'] or '[]'))
        except Exception:
            pass
        if dc == 0 or mc == 0:
            category, severity = 'source_coverage_gap', 'info'
        else:
            if set(dila_ids) & set(marcus_ids):
                category, severity = 'source_coverage_gap', 'info'
            else:
                category, severity = 'direction_disagreement', 'warning'
        result.append({
            "conflict_type": r['conflict_type'],
            "note": r['notes'],
            "dila_count": dc,
            "marcus_count": mc,
            "dila_ids": dila_ids,
            "marcus_ids": marcus_ids,
            "issue_category": category,
            "severity": severity,
        })
    return result




def _t138_edge_assertions(conn, subject_id, object_id):
    """T138 — các source assertion độc lập của 1 cạnh truyền thừa (subject→object)
    từ bảng DERIVED lineage_edge_assertions. Trả về [ {source_code, raw_relation_type,
    ref, mapping_verified, trust_level, status, direction_mismatch}, ... ] + trust_level
    tổng (max theo thứ tự L1>L2>L3>L4). Không có assertion nào → sources rỗng, trust_level None.
    Kiểm tra HAI chiều: forward (sub→obj) + reversed (obj→sub). Assertion tìm thấy
    ở chiều ngược (DILA lưu student→teacher, Marcus teacher→student) được gắn
    direction_mismatch=True và KHÔNG contribute vào trust_level (đây là conflict,
    không phải confirmation)."""
    order = {'L1': 4, 'L2': 3, 'L3': 2, 'L4': 1}
    inv = {v: k for k, v in order.items()}

    # Forward direction (same as Marcus convention)
    rows_fwd = conn.execute(
        "SELECT source_code, raw_relation_type, ref, mapping_verified, trust_level, status "
        "FROM lineage_edge_assertions WHERE subject_person_id=? AND object_person_id=? "
        "AND status!='rejected' ORDER BY source_code", (subject_id, object_id)
    ).fetchall()

    # Reversed direction (DILA stores student→teacher, flipped)
    rows_rev = conn.execute(
        "SELECT source_code, raw_relation_type, ref, mapping_verified, trust_level, status "
        "FROM lineage_edge_assertions WHERE subject_person_id=? AND object_person_id=? "
        "AND status!='rejected' ORDER BY source_code", (object_id, subject_id)
    ).fetchall()

    if not rows_fwd and not rows_rev:
        return {'sources': [], 'trust_level': None, 'rejected': False}

    seen = set()
    sources = []
    best = 0
    for r in rows_fwd:
        sd = r['source_code']
        if sd in seen:
            continue
        seen.add(sd)
        sources.append({
            'source_code': sd,
            'raw_relation_type': r['raw_relation_type'],
            'ref': r['ref'],
            'mapping_verified': bool(r['mapping_verified']),
            'trust_level': r['trust_level'],
            'status': r['status'] or 'active',
            'direction_mismatch': False,
        })
        lv = order.get(r['trust_level'], 0)
        if lv > best:
            best = lv

    for r in rows_rev:
        sd = r['source_code']
        if sd in seen:
            continue
        seen.add(sd)
        sources.append({
            'source_code': sd,
            'raw_relation_type': r['raw_relation_type'],
            'ref': r['ref'],
            'mapping_verified': bool(r['mapping_verified']),
            'trust_level': r['trust_level'],
            'status': r['status'] or 'active',
            'direction_mismatch': True,
        })
        # direction_mismatch: KHÔNG contribute vào trust_level
        # (DILA says opposite direction = conflict, not confirmation)

    is_rej = bool(conn.execute(
        "SELECT 1 FROM lineage_edge_assertions WHERE subject_person_id=? AND object_person_id=? "
        "AND status='rejected' LIMIT 1", (subject_id, object_id)).fetchone())
    return {
        'sources': sources,
        'trust_level': inv.get(best),
        'rejected': is_rej,
    }




def _t86_normalize_place_id(place_id):
    """DILA long format PL000000024672 → places table short format PL024672."""
    if place_id and place_id.startswith('PL') and len(place_id) > 8:
        try:
            return 'PL{:06d}'.format(int(place_id[2:]))
        except ValueError:
            pass
    return place_id




def _t86_resolve_display_name(conn, person_id: str, node: dict | None = None) -> dict:
    """Resolve preferred display name for a person.

    Precedence (spec Phase 5):
      1. TTL verified_direct preferred Vi display name (person_display_names)
      2. TTL verified_crosswalk preferred Vi display name (person_display_names)
      3. vn_person_authority canonical 4-char Vi name (mapped by dila_id)
      4. DILA/Marcus authority name (node.name_vi or people.name_vi) + name_zh
      5. name_zh only
      6. person_id as safe fallback

    Returns structured dict — never mutates node.
    """
    # Try person_display_names table
    row = conn.execute(
        """SELECT display_name_vi, display_name_zh, authority_name_vi, authority_name_zh,
                  verification_status, source_file, mapping_method
           FROM person_display_names
           WHERE person_id=? AND locale='vi' AND is_preferred=1
             AND verification_status IN ('verified_direct','verified_crosswalk')
           ORDER BY CASE verification_status
               WHEN 'verified_direct'   THEN 1
               WHEN 'verified_crosswalk' THEN 2
               ELSE 3 END
           LIMIT 1""",
        (person_id,)
    ).fetchone()

    if row:
        return {
            "primary":             row[0],
            "secondary":           row[1] or "",
            "authority_primary":   row[2] or "",
            "authority_secondary": row[3] or "",
            "source_type":         "ttl",
            "source_file":         row[5] or "",
            "verification_status": row[4],
            "is_formal_name":      True,
        }

    # Try vn_person_authority — canonical 4-char Vietnamese name mapped by DILA ID.
    # Hán văn 2 chữ (無學, 天然) trong marcus_reference sẽ được ánh xạ thành tên
    # đầy đủ 4 chữ (Thúy Vi Vô Học, Đơn Hà Thiên Nhiên) nếu có trong bảng này.
    # [T200] dùng helper có ORDER BY xác định (dila_id KHÔNG unique: 33 nhóm 2–3 dòng).
    # Thứ tự ưu tiên status: verified > pending > auto_ttl > alias_*, tie-break bằng id.
    vpa = _t200_vnpa_lookup_by_dila(
        conn, person_id,
        "generation_order, dharma_lineage, biographical_note_vi",
    )
    if vpa and vpa['name_vi']:
        # T237/T238: Gate — chỉ dùng TTL name nếu admin đã xác nhận.
        # '—' trong name_vi_final = admin đánh dấu 2 vị này KHÁC NHAU → block TTL.
        # Không có admin row + status != 'verified' → cũng block (auto_ttl/alias chưa duyệt).
        _nm_row = conn.execute(
            "SELECT name_vi_final FROM name_vi_map WHERE dila_id=? AND approved_by='admin' LIMIT 1",
            (person_id,)
        ).fetchone()
        if _nm_row:
            _nm_final = (_nm_row[0] or '').strip()
            _vpa_ok = bool(_nm_final) and _nm_final != '—'
        else:
            _vpa_ok = vpa['status'] == 'verified'
        if _vpa_ok:
            return {
                "primary":              vpa['name_vi'],
                "secondary":            vpa['name_zh'] or "",
                "authority_primary":    vpa['name_vi'],
                "authority_secondary":  vpa['name_zh'] or "",
                "source_type":          "ttl",
                "source_file":          (vpa['ttl_filename'] or "") + ".ttl",
                "verification_status":  "verified_direct",
                "is_formal_name":       True,
                "generation_order":     vpa['generation_order'],
                "dharma_lineage":       vpa['dharma_lineage'] or "",
                "biographical_note_vi": vpa['biographical_note_vi'] or "",
            }

    # Fallback — use node data or people table
    auth_vi, auth_zh = "", ""
    if node:
        auth_vi = node.get("name_vi") or node.get("name") or ""
        auth_zh = node.get("name_zh") or ""
    if not auth_vi:
        prow = conn.execute(
            "SELECT name_vi, name_zh FROM people WHERE id=?", (person_id,)
        ).fetchone()
        if prow:
            auth_vi, auth_zh = prow[0] or "", prow[1] or ""

    return {
        "primary":             auth_vi or auth_zh or person_id,
        "secondary":           auth_zh if auth_vi else "",
        "authority_primary":   auth_vi,
        "authority_secondary": auth_zh,
        "source_type":         "dila",
        "source_file":         "",
        "verification_status": "authority_fallback",
        "is_formal_name":      False,
    }




# ── T412 (BUG-037, 2026-10-21): nhãn nút cây Pháp hệ = tên đầy đủ theo TTL ──────────
# Thứ tự ưu tiên tên hiển thị trên cây (lineage-tree / ancestor-spine / ancestor-path):
#   (a) rdfs:label@vi của file TTL nối với DILA ID (đọc data/ttl/, CHỈ ĐỌC, index build 1 lần/process)
#   (b) không có TTL → giữ tên phiên âm DILA/Marcus hiện có (không đổi).
# KHÔNG dùng vn_person_authority.name_vi làm tên đầy đủ (tên ngắn / gạch dưới).
# DILA ID nối >=2 file TTL KHÁC TÊN (không alias) → KHÔNG đoán: dùng tên DILA + ttl_conflict
# (tooltip "nhiều hồ sơ TTL, chờ Admin chốt"). Liệt kê trong report, không ghi DB.
import threading as _t412_threading



_T412_TTL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ttl')


_T412_LABEL_RE = re.compile(r'rdfs:label\s+"([^"]+)"@vi')


_T412_INDEX = None


_T412_INDEX_LOCK = _t412_threading.Lock()




def _t412_read_main_label(path):
    """rdfs:label@vi ĐẦU TIÊN = nhãn nhân vật chính (subject <ex:monk/...>).
    Chỉ đọc 8 KB đầu file (zero-RAM); các label sau thuộc tăng nhân liên quan."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        head = f.read(8192)
    m = _T412_LABEL_RE.search(head)
    return m.group(1).strip() if m else ''




def _t412_build_index():
    """dila_id -> {'label','ttl_file','ambiguous','files'}; chỉ tính link không-alias có file tồn tại."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT dila_id, ttl_filename FROM vn_person_authority "
            "WHERE dila_id IS NOT NULL AND dila_id!='' "
            "AND ttl_filename IS NOT NULL AND ttl_filename!='' "
            "AND COALESCE(status,'') NOT LIKE 'alias%'"
        ).fetchall()
    finally:
        conn.close()
    files_by_id = {}
    for row in rows:
        dila_id, tf = row[0], row[1]
        fn = tf if tf.endswith('.ttl') else tf + '.ttl'
        if os.path.isfile(os.path.join(_T412_TTL_DIR, fn)):
            files_by_id.setdefault(dila_id, set()).add(fn)
    index = {}
    for dila_id, files in files_by_id.items():
        labels = {}
        for fn in sorted(files):
            try:
                lbl = _t412_read_main_label(os.path.join(_T412_TTL_DIR, fn))
            except OSError:
                lbl = ''
            if lbl:
                labels[fn] = lbl
        if not labels:
            continue
        distinct = sorted(set(labels.values()))
        if len(distinct) == 1:
            index[dila_id] = {'label': distinct[0], 'ttl_file': sorted(labels)[0],
                              'ambiguous': False, 'files': sorted(labels)}
        else:
            index[dila_id] = {'label': '', 'ttl_file': '', 'ambiguous': True,
                              'files': sorted(labels)}
    return index




def _t412_get_index():
    global _T412_INDEX
    if _T412_INDEX is None:
        with _T412_INDEX_LOCK:
            if _T412_INDEX is None:
                _T412_INDEX = _t412_build_index()
    return _T412_INDEX




def _t412_resolve_display_name(conn, person_id, node=None):
    """Bọc _t86_resolve_display_name cho 3 route cây. Hàm gốc giữ nguyên cho route khác."""
    dn = dict(_t86_resolve_display_name(conn, person_id, node))
    node = node or {}
    idx = _t412_get_index().get(person_id)
    if idx and not idx['ambiguous']:
        primary = idx['label']
        if dn.get('verification_status') == 'verified_direct' and dn.get('authority_primary'):
            primary = dn['authority_primary']
        return {
            'primary': primary,
            'secondary': node.get('name_zh') or dn.get('secondary') or '',
            'authority_primary': dn.get('authority_primary', ''),
            'authority_secondary': dn.get('authority_secondary', ''),
            'source_type': 'ttl',
            'source_file': idx['ttl_file'],
            'verification_status': 'ttl_label',
            'is_formal_name': True,
            'name_source': 'TTL',
            'ttl_candidates': idx['files'],
            'ttl_conflict': [],
        }
    if idx and idx['ambiguous']:
        # Nhiều hồ sơ TTL khác tên: không đoán, dùng tên DILA/Marcus phiên âm.
        return {
            'primary': node.get('name_vi') or dn.get('primary') or person_id,
            'secondary': node.get('name_zh') or '',
            'authority_primary': dn.get('authority_primary', ''),
            'authority_secondary': dn.get('authority_secondary', ''),
            'source_type': 'dila',
            'source_file': '',
            'verification_status': 'ttl_conflict',
            'is_formal_name': False,
            'name_source': 'DILA',
            'ttl_candidates': idx['files'],
            'ttl_conflict': idx['files'],
        }
    # Không có TTL trong index: giữ nguyên kết quả hàm gốc (DILA phiên âm / curated).
    dn['name_source'] = 'TTL' if dn.get('is_formal_name') else 'DILA'
    dn['ttl_candidates'] = []
    dn['ttl_conflict'] = []
    return dn




def _t86_origin_place(conn, person_id):
    """Nguồn địa lý cho 'Xem trên bản đồ' — person_origin_link (sinh tại/籍貫).

    T372 fix: person_origin_link.place_id luôn ở dạng DILA gốc (12 chữ số,
    vd PL000000024832) — CÙNG hệ id với places_dila, KHÔNG phải với bảng
    `places` (bảng này có id ngắn độc lập, do một lần import khác đánh số
    tuần tự, không tương ứng 1-1 với số DILA). _t86_normalize_place_id()
    từng "rút gọn" id dài rồi tra bảng `places` — vô tình trúng một place_id
    ngắn TRÙNG SỐ nhưng là một địa danh hoàn toàn khác (vd PL000000024832
    "許州" bị đọc nhầm thành PL024832 "碭縣" trong `places`). Phải tra
    places_dila bằng raw_pid (id gốc, không normalize) mới đúng.
    Tên Việt: ưu tiên namevi_map_places theo dila_id (join key ổn định),
    không join theo name_zh (tên không phải khoá nối)."""
    row = conn.execute(
        "SELECT place_id FROM person_origin_link WHERE person_id=? ORDER BY confidence DESC LIMIT 1",
        (person_id,)
    ).fetchone()
    if not row:
        return None
    raw_pid = row['place_id']
    pl = conn.execute(
        "SELECT name, name_zh FROM places_dila WHERE id=?", (raw_pid,)
    ).fetchone()
    # `places_dila.name` là tên chính (persName/placeName gốc XML, vd 許州);
    # name_zh trong places_dila đôi khi là một tên biến thể/cổ khác — không
    # dùng làm tên hiển thị chính để tránh lộn tên như case 許州/潁川郡.
    name_zh = (pl['name'] if pl and pl['name'] else (pl['name_zh'] if pl else None))
    name_vi = None
    vi_confidence = None
    vi_source = None
    if name_zh:
        nv = conn.execute(
            "SELECT name_vi, confidence, source FROM namevi_map_places "
            "WHERE dila_id=? ORDER BY confidence DESC LIMIT 1",
            (raw_pid,)
        ).fetchone()
        if nv and nv['name_vi']:
            name_vi = nv['name_vi']
            vi_confidence = nv['confidence']
            vi_source = nv['source']
    return {
        "place_id": raw_pid,
        "name_vi": name_vi,
        "name_zh": name_zh,
        "vi_confidence": vi_confidence,
        "vi_source": vi_source,
    }




def _t360_classify_name_vi_source(raw_source, confidence):
    """T360 — Chuẩn hoá (label hiển thị, màu badge) từ (source, confidence) THẬT trong DB.
    Không hard-code theo ID — chỉ map nhãn text sang tiếng Việt + ngưỡng màu theo confidence.
    Màu: green=DILA/chính thức (>=0.95), yellow=TTL/Admin (0.8-0.94), gray=ZQ tự động (<0.8).
    """
    label_map = {
        'ttl_confirmed': 'TTL xác nhận',
        'manual': 'Admin chỉnh sửa',
        'manual_fix': 'Admin chỉnh sửa',
        'auto_transliterate': 'ZQ tự động',
        'auto_transliterate_v2': 'ZQ tự động',
        'auto_transliterate_t49': 'ZQ tự động',
        'auto_generated': 'ZQ tự động',
        'DILA': 'DILA chính thức',
        'places': 'DILA chính thức',
    }
    label = label_map.get(raw_source, raw_source or 'Không rõ nguồn')
    if confidence is None:
        color = 'gray'
    elif confidence >= 0.95:
        color = 'green'
    elif confidence >= 0.8:
        color = 'yellow'
    else:
        color = 'gray'
    return label, color




def _t360_resolve_place_name_vi_source(detail):
    """T360 — Xác định nguồn/độ tin cậy THẬT của places.name_vi đang hiển thị trên UI.
    detail là dict đã build trong api_places_detail (có thể mang theo các field phụ
    '_namevi_source'/'_namevi_confidence' do bước supplement từ namevi_map_places ghi lại).
    KHÔNG tự suy đoán — chỉ đọc lại field đã truy vấn thật từ DB.
    """
    try:
        if detail.get('_namevi_source') is not None or detail.get('_namevi_confidence') is not None:
            # name_vi đến từ namevi_map_places (dù detail gốc là row 'places' hay
            # row 'namevi_map') — đọc lại cột source/confidence thật đã lưu ở trên.
            raw_source = detail.get('_namevi_source')
            confidence = detail.get('_namevi_confidence')
        elif detail.get('source') == 'places':
            # name_vi lấy trực tiếp từ places.name_vi (không qua namevi_map) → cột
            # source_origin/confidence thật của bảng places (mặc định DILA/1.0).
            raw_source = detail.get('source_origin') or 'DILA'
            confidence = detail.get('confidence')
            if confidence is None:
                confidence = 1.0
        else:
            raw_source = None
            confidence = None
        if raw_source is None and confidence is None:
            return None, None, None
        label, color = _t360_classify_name_vi_source(raw_source, confidence)
        return label, confidence, color
    except Exception:
        return None, None, None




def _t360_resolve_person_name_vi_source(conn, person_id):
    """T360 — Xác định nguồn/độ tin cậy THẬT của people.name_vi.
    Thứ tự ưu tiên (đọc trực tiếp DB, không hard-code theo ID):
      1) person_display_names (verification_status thật — hiện có rất ít record)
      2) vn_person_authority (status thật — dila_id khớp person_id)
      3) Fallback theo quy tắc đã ghi trong CLAUDE.md: mọi name_vi còn lại trong
         `people` đều do ZQ phiên âm tự động, confidence 0.5 (KHÔNG phải DILA).
    Bọc try/except theo CLAUDE.md: các bảng authority có thể thiếu trên VPS.
    """
    try:
        row = conn.execute(
            "SELECT verification_status, source_type FROM person_display_names "
            "WHERE person_id = ? ORDER BY is_preferred DESC, id ASC LIMIT 1",
            (person_id,)
        ).fetchone()
        if row:
            vs = row['verification_status'] or ''
            st = row['source_type'] or ''
            if vs == 'verified_direct':
                confidence = 1.0 if st == 'manual' else 0.95
                raw_source = 'manual' if st == 'manual' else 'ttl_confirmed'
            elif vs == 'verified_crosswalk':
                confidence = 0.9
                raw_source = 'ttl_confirmed'
            else:
                confidence = 0.8
                raw_source = st or 'ttl_confirmed'
            label, color = _t360_classify_name_vi_source(raw_source, confidence)
            return label, confidence, color
    except Exception:
        pass

    try:
        row = conn.execute(
            "SELECT status FROM vn_person_authority WHERE dila_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (person_id,)
        ).fetchone()
        if row:
            status = row['status'] or 'pending'
            conf_map = {
                'verified': 0.95,
                'auto_ttl': 0.8,
                'alias_vi_suffix': 0.7,
                'alias_zh_match': 0.7,
                'pending': 0.6,
            }
            confidence = conf_map.get(status, 0.6)
            raw_source = 'ttl_confirmed' if status == 'verified' else f'TTL ({status})'
            label, color = _t360_classify_name_vi_source(raw_source, confidence)
            return label, confidence, color
    except Exception:
        pass

    # Fallback mặc định — đúng với ghi chú CLAUDE.md §"ZQ — nguồn tên tiếng Việt".
    label, color = _t360_classify_name_vi_source('auto_generated', 0.5)
    return label, 0.5, color




def _t86_parse_ref_passage(conn, ref):
    """Cố resolve chuỗi dẫn chiếu CBETA → passage row để mở Đọc trong Đại Tạng.
    ref dạng: '《...》卷3：「...」; http://cbetaonline.dila.edu.tw/B35n0194_p0349a09'
    Trích text_id từ URL (B35n0194_p0349a09 → B35n0194) rồi match passage.text_id.
    Trung thực: nếu passage chưa được lập chỉ mục → found=False."""
    if not ref:
        return None
    m = _re86.search(r'cbetaonline\.dila\.edu\.tw/([A-Za-z0-9_]+)', ref or '')
    if m:
        url = m.group(1)
        # text_id = phần trước dấu '_' (B35n0194_p0349a09 → B35n0194)
        text_id = url.split('_')[0] if '_' in url else url
        row = conn.execute(
            "SELECT passage_id, text_id, loc_ref FROM passage WHERE text_id=? ORDER BY passage_id LIMIT 1",
            (text_id,)
        ).fetchone()
        if row:
            return {"found": True, "passage_id": row['passage_id'],
                    "text_id": row['text_id'], "loc_ref": row['loc_ref'], "raw_ref": ref}
    # fallback: match theo thô chứa text_id bất kỳ
    for tok in _re86.findall(r'([A-Za-z]\d+n\d+)', ref or ''):
        row = conn.execute(
            "SELECT passage_id, text_id, loc_ref FROM passage WHERE text_id=? ORDER BY passage_id LIMIT 1",
            (tok,)
        ).fetchone()
        if row:
            return {"found": True, "passage_id": row['passage_id'],
                    "text_id": row['text_id'], "loc_ref": row['loc_ref'], "raw_ref": ref}
    return {"found": False, "passage_id": None, "raw_ref": ref,
            "message": "Chưa có đoạn văn được lập chỉ mục cho dẫn chiếu này trong Đại Tạng (passage table)."}




def calculate_edge_color_and_divergence(edge_row):
    """T410 (2026-10-19) — MÀU THEO NGUỒN (không phải theo số nguồn).

    edge_row: dict/Row có 3 cột boolean/int dila_asserted, marcus_asserted, ttl_asserted
    (lineage_asserted KHÔNG tham gia quy tắc màu — admin chỉ chỉ định 3 nguồn này).

    Quy tắc MÀU THEO NGUỒN (admin chốt 2026-10-19):
      - 1 nguồn   -> màu NGUỒN ĐÓ (dila/marcus/ttl), nét LIỀN
      - >=2 nguồn -> màu ĐỒNG THUẬN (agree), nét LIỀN
      - 0 nguồn   -> màu CHƯA RÕ (unknown), nét ĐỨT  (an toàn, không xảy ra thực tế)

    "Xám chấm = chưa rõ chiều" chỉ dùng cho nét đứt; cạnh 1 nguồn VẪN nét liền
    (chiều đã rõ, chỉ thiếu nguồn xác nhận thứ 2).

    Trả về dict:
      edge_color_token : 'dila'|'marcus'|'ttl'|'agree'|'unknown' (frontend đổi sang CSS var --edge-*)
      edge_sources     : list nguồn đã assert, ví dụ ['dila','marcus']
      n_sources        : số nguồn
      edge_color       : hex mặc định nền TỐI — fallback cho client cũ / edge_color
      edge_dashed      : True khi CHƯA rõ chiều (chỉ n_sources == 0)
      is_divergence    : True khi đúng 1 nguồn (cần khảo cứu thêm; dùng cho đếm tree_status)
    """
    dila_v = bool(edge_row.get('dila_asserted')) if hasattr(edge_row, 'get') else bool(edge_row['dila_asserted'])
    marc_v = bool(edge_row.get('marcus_asserted')) if hasattr(edge_row, 'get') else bool(edge_row['marcus_asserted'])
    ttl_v = bool(edge_row.get('ttl_asserted')) if hasattr(edge_row, 'get') else bool(edge_row['ttl_asserted'])

    # Hex nền tối (fallback). Bản sáng và bản chuẩn nằm ở CSS --edge-* trong places.html.
    COLOR_DILA = '#38bdf8'
    COLOR_MARCUS = '#facc15'
    COLOR_TTL = '#dc2626'
    COLOR_AGREE = '#f1f5f9'
    COLOR_UNKNOWN = '#94a3b8'

    sources = []
    if dila_v:
        sources.append('dila')
    if marc_v:
        sources.append('marcus')
    if ttl_v:
        sources.append('ttl')

    if len(sources) >= 2:
        return {
            'edge_color_token': 'agree', 'edge_sources': sources, 'n_sources': len(sources),
            'edge_color': COLOR_AGREE, 'dashed': False, 'is_divergence': False,
        }
    if len(sources) == 1:
        only = sources[0]
        hex_by_token = {'dila': COLOR_DILA, 'marcus': COLOR_MARCUS, 'ttl': COLOR_TTL}
        return {
            'edge_color_token': only, 'edge_sources': sources, 'n_sources': 1,
            'edge_color': hex_by_token[only], 'dashed': False, 'is_divergence': True,
        }
    return {
        'edge_color_token': 'unknown', 'edge_sources': [], 'n_sources': 0,
        'edge_color': COLOR_UNKNOWN, 'dashed': True, 'is_divergence': False,
    }




def api_monk_root_ancestor(dila_id):
    """GET /daoanh/api/monk/<dila_id>/root-ancestor
    BFS lên (thầy) từ dila_id đến khi không còn thầy → trả về khai tổ (root nodes).
    Mục đích: tìm vị khai tổ của tông phái đang hiển thị trong Pháp Mạch.
    Max 60 bước để tránh vòng lặp vô hạn."""
    conn = get_db_connection()
    try:
        # T186: cho phép ttl_persons (danh tăng VN) làm start node
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone() \
            or conn.execute("SELECT 1 FROM ttl_persons WHERE id=?", (dila_id,)).fetchone()
        if not exists:
            return jsonify({"ok": False, "error": "person not found"}), 404

        frontier = [dila_id]
        seen = {dila_id}
        roots = []
        hops = 0

        while frontier and hops < 60:
            hops += 1
            nxt = []
            for pid in frontier:
                # T187: dùng consensus với is_primary — bỏ qua early_study edges
                nb, _ = _t158_neighbors_consensus(conn, pid, 'up', include_single=True)
                # Lọc bỏ early_study (is_primary=-1) để BFS không bị lạc sang dòng phụ
                nb = [n for n in nb if n.get('is_primary', 0) != -1]
                if not nb:
                    info = _t86_person_info(conn, pid)
                    info['display_name'] = _t86_resolve_display_name(conn, pid, info)
                    if not any(r['id'] == pid for r in roots):
                        roots.append(info)
                else:
                    for nbv in nb:
                        nid = nbv['id']
                        if nid not in seen:
                            seen.add(nid)
                            nxt.append(nid)
            frontier = nxt

        return jsonify({
            "ok": True,
            "roots": roots,
            "hops": hops,
            "path_count": len(seen) - 1,
        })
    except Exception as e:
        app.logger.error(f"api_monk_root_ancestor error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




# ── T128 — Relation evidence: parser chuẩn hoá + translate + văn cảnh ─────────────
# Evidence hiện tại: marcus_networks.ref = chuỗi tự do ('trích đoạn…（T47n1990_p0582a19）; '
# hoặc '《…》卷N：「…」; http://cbetaonline.dila.edu.tw/B35n0194_p0349a09'). KHÔNG có field
# relation_id/original_excerpt/work_id/locator/text_hash → parser server-side (additive, 0 ALTER).
_T128_WORKID_RE = r'(?:[A-Za-z]\d+n[A-Za-z]?\d*)'



def _t128_parse_relation_ref(ref, from_id=None, to_id=None, direction=None):
    """Parse dẫn chứng Marcus → struct chuẩn hoá cho mối quan hệ truyền thừa.

    Trả dict:
      relation_id     = sha1(from|to|direction)[:12] (deterministic, không cần bảng mới)
      source          = URL CBETA (nếu ref là URL)
      work_id         = sigla văn bản (T47n1990 / B35n0194 ...) — None nếu không có
      locator         = vị trí trang (p0582a19 / p0349a09 ...) — None nếu không có
      original_excerpt= phần văn Hán trích dẫn (bỏ locator/URL, public thoại chuẩn)
      text_hash       = sha256(excerpt)[:24] — khớp translation_cache.source_hash
      has_ref         = ref có nội dung
    Trung thực: extract phần nào có được; không bịa ở chỗ thiếu."""
    ref0 = (ref or '').strip().strip(';；\u3000\t ')
    rel_id = ''
    if from_id and to_id and direction:
        rel_id = hashlib.sha1('|'.join([str(from_id), str(to_id), str(direction)]).encode('utf-8')).hexdigest()[:12]
    excerpt = ref0
    work_id = None
    locator = None
    source = None
    # locator đuôi dạng: '…（T47n1990_p0582a19）' hoặc '…(B35n0194_p0349a09)'
    m = re.search(r'[（(]\s*(%s(?:_[A-Za-z0-9]+)?)\s*[）)]\s*$' % _T128_WORKID_RE, ref0)
    if m:
        seg = m.group(1).split('_')
        work_id = seg[0]
        locator = seg[1] if len(seg) > 1 else None
        excerpt = ref0[:m.start()].strip().strip(';；\u3000\t ')
    else:
        # fallback: URL CBETA (không có locator trong ngoặc đuôi)
        mu = re.search(r'(https?://cbetaonline\.dila\.edu\.tw/[A-Za-z0-9_]+)', ref0)
        if mu:
            source = mu.group(1)
            url_tail = mu.group(1).split('/')[-1]
            wid = url_tail.split('_')[0] if '_' in url_tail else url_tail
            if re.match(r'^%s$' % _T128_WORKID_RE, wid):
                work_id = wid
            pre = ref0[:mu.start()].strip().strip(';；\u3000\t ')
            if pre:
                excerpt = pre
    text_hash = ''
    if excerpt.strip():
        text_hash = hashlib.sha256(excerpt.strip().rstrip('；;').encode('utf-8')).hexdigest()[:24]
    return {
        'relation_id': rel_id,
        'source': source,
        'work_id': work_id,
        'locator': locator,
        'original_excerpt': excerpt,
        'text_hash': text_hash,
        'has_ref': bool(ref0),
    }






# ── Nexus Point — event-centric knowledge graph (Commit 4) ──────────────────────────
# Trả về đồ thị nexus của một thực thể (person hoặc place): thực thể → sự kiện →
# văn bản (passage trích dẫn thật) → mốc thời gian (year/era). Mỗi edge đều mang
# citation thật (cbeta_ref / source_ref) — không suy đoán, không regex.
# Nguồn bảng event_text_link (bridge Commit 2) + cbeta_texts (tựa sách) + places_dila.
_NEXUS_GROUP_COLOR = {
    'person': '#c4891a',
    'place': '#3a9e6e',
    'event': '#8b5cf6',
    'text': '#0b7a96',
    'time': '#d97706',
}




def _nexus_title_for_sigla(conn, sigla, fallback):
    """Lấy tựa sách từ cbeta.db (nếu có), ngược lại trả fallback (source_book)."""
    try:
        c = get_cbeta_conn()
        try:
            r = c.execute("SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (sigla,)).fetchone()
            if r and r['title_zh']:
                sig = sigla.split('n', 1)[0] if 'n' in sigla else sigla
                return f"{sig} · {r['title_zh']}"
        finally:
            c.close()
    except Exception:
        pass
    return fallback or sigla




def _ensure_geo_cross_ref_table(conn):
    """geo_cross_ref — DILA place_id <-> external authority ID bridge (T21 design, approved
    2026-08-19, see tasks/T21-nien-dai-timeline-research.md). "Geo-Identity Linking": store
    only the ID, query the external source on-demand (no raw data clone). Reused here (T28)
    for wikidata_qid specifically, to answer "who founded this place" via live P112 lookup —
    T21 will reuse the same table for founding-date (P571) lookups.
    T29 adds bdrc_id column for BDRC sameAs links."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geo_cross_ref (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dila_id TEXT NOT NULL,
            wikidata_qid TEXT,
            chgis_svid TEXT,
            tgaz_id TEXT,
            bgis_id TEXT,
            marcus_ref TEXT,
            bdrc_id TEXT,
            notes TEXT,
            confidence TEXT DEFAULT 'verified',
            mapped_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dila_id)
        )
    """)
    # ALTER TABLE for existing databases that miss the bdrc_id column
    try:
        conn.execute("ALTER TABLE geo_cross_ref ADD COLUMN bdrc_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()



_WIKIDATA_CACHE = {}


_WIKIDATA_CACHE_TTL = 86400  # 24h, per T21 spec



def _fetch_wikidata_founders(qid):
    """Live-fetch P112 (founded by) claims for a Wikidata place QID, cached 24h (T21's
    "no raw import, query on-demand" pattern). Returns [{wikidata_qid, label, label_zh}] —
    deliberately NOT resolved to any DILA people.id here. That resolution is a separate,
    human-confirmed step (place_person_link) because matching a Wikidata person to the right
    row in a 48,673-row, name-ambiguous `people` table is document/identity interpretation,
    not something to auto-guess (see tasks/T28-place-person-lineage.md)."""
    now = time.time()
    cached = _WIKIDATA_CACHE.get(qid)
    if cached and now - cached[0] < _WIKIDATA_CACHE_TTL:
        return cached[1]
    # Wikimedia REST/API policy requires a descriptive User-Agent — anonymous/default
    # python-requests UA gets a 403, confirmed live 2026-08-20.
    _wd_headers = {'User-Agent': 'DaoAnhBuddhistGIS/1.0 (https://phatphaponline.org/daoanh/; contact via project admin) python-requests'}
    try:
        r = requests.get(f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json', headers=_wd_headers, timeout=8)
        r.raise_for_status()
        entity = r.json()['entities'][qid]
        person_qids = []
        for c in entity.get('claims', {}).get('P112', []):
            try:
                person_qids.append(c['mainsnak']['datavalue']['value']['id'])
            except (KeyError, TypeError):
                continue
        if not person_qids:
            _WIKIDATA_CACHE[qid] = (now, [])
            return []
        r2 = requests.get('https://www.wikidata.org/w/api.php', params={
            'action': 'wbgetentities', 'ids': '|'.join(person_qids),
            'props': 'labels', 'languages': 'vi|en|zh', 'format': 'json'
        }, headers=_wd_headers, timeout=8)
        r2.raise_for_status()
        ents = r2.json().get('entities', {})
        result = []
        for pqid in person_qids:
            labels = ents.get(pqid, {}).get('labels', {})
            label = (labels.get('vi') or labels.get('en') or labels.get('zh') or {}).get('value') or pqid
            label_zh = (labels.get('zh') or {}).get('value')
            result.append({"wikidata_qid": pqid, "label": label, "label_zh": label_zh})
        _WIKIDATA_CACHE[qid] = (now, result)
        return result
    except Exception as e:
        app.logger.warning(f"_fetch_wikidata_founders({qid}) failed: {e}")
        return []



def _ensure_place_person_link_table(conn):
    """place_person_link — curated (human-cited) place<->person relations, T22 (Nhân Vật /
    Truyền Thừa tabs). No column in places/places_dila/people links person<->place (verified
    2026-08-19, see tasks/T16-nexus-points.md) and none of the 15 trusted sources currently
    imported into this DB carries it either — DILA place catalog has no persName, Marcus has
    no place field, BDRC bdo:placeEvent exists conceptually but isn't populated for our places.
    Per CLAUDE.md's content-integrity rule this must NOT be filled by regex/fuzzy guessing.
    Every row here requires an explicit source_url citation (enforced in the insert route) —
    same human-curated pattern as custom_hanviet_override (T08), not an algorithm's guess."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS place_person_link (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            relation_type TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            note TEXT,
            added_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()




# ── T21: NIÊN ĐẠI tab — Geo-Identity Linking (2026-08-20) ────────────────────
# Design: geo_cross_ref bridge table (dila_id ↔ wikidata_qid) + place_timeline_events (BGIS/Marcus ETL).
# API fetches Wikidata P571/P1435 on-demand via QID. Dynasty context from time_periods (DILA, 117K rows).
# See tasks/T21-nien-dai-timeline-research.md for full spec.

import urllib.request as _urllib_req, urllib.parse as _urllib_parse



_WD_SPARQL_URL = "https://query.wikidata.org/sparql"


_WD_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "DaoAnhBot/1.0 (phatphaponline.org, DILA Buddhist GIS research)"
}


_timeline_cache = {}  # {qid: (data, timestamp)}



def _fetch_wikidata_timeline(qid):
    """Fetch P571 (founding) + P1435 (heritage) from Wikidata for a given QID.
    Returns dict with keys: founding_year, heritage, label, license. Cached 24h."""
    import time as _time
    if qid in _timeline_cache:
        cached, ts = _timeline_cache[qid]
        if _time.time() - ts < 86400:
            return cached

    query = f"""
SELECT ?item ?itemLabel ?inception ?heritage ?heritageLabel WHERE {{
  BIND(wd:{qid} AS ?item)
  OPTIONAL {{ ?item wdt:P571 ?inception }}
  OPTIONAL {{ ?item wdt:P1435 ?heritage }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,vi,en" . }}
}}
"""
    try:
        url = _WD_SPARQL_URL + "?" + _urllib_parse.urlencode({"query": query})
        req = _urllib_req.Request(url, headers=_WD_HEADERS)
        with _urllib_req.urlopen(req, timeout=8) as resp:
            data = __import__("json").loads(resp.read().decode("utf-8"))
        bindings = data.get("results", {}).get("bindings", [])
        founding_year = None
        label = qid
        heritage_list = []
        for b in bindings:
            if "inception" in b and founding_year is None:
                v = b["inception"]["value"].lstrip("+")
                try:
                    y = int(v[:4])
                    if 0 < y < 2100:
                        founding_year = y
                except Exception:
                    pass
            if "itemLabel" in b:
                label = b["itemLabel"]["value"]
            if "heritageLabel" in b and b.get("heritageLabel", {}).get("value", qid) != qid:
                h = b["heritageLabel"]["value"]
                if h not in heritage_list:
                    heritage_list.append(h)
        result = {
            "founding_year": founding_year,
            "label": label,
            "heritage": heritage_list,
            "license": "CC0",
            "source_ref": f"{qid}·P571",
            "wikidata_url": f"https://www.wikidata.org/wiki/{qid}"
        }
    except Exception as e:
        result = {"error": str(e), "founding_year": None, "label": qid, "heritage": []}

    _timeline_cache[qid] = (result, __import__("time").time())
    return result




def _get_dynasty_context(year_ce, conn):
    """Return dynasty context for a given CE year.
    DILA time_periods: 'dynasty' rows have no start_year yet (T14 pending).
    Uses compact hardcoded CE ranges for common Chinese dynasties.
    Returns dict with dynasty name (zh/vi) or None."""
    if not year_ce or year_ce <= 0:
        return None
    _DYNASTIES = [
        (-2070, -1046, "商", "Thương"),
        (-1046, -256, "周", "Chu"),
        (-221, -207, "秦", "Tần"),
        (-206, 220, "漢", "Hán"),
        (220, 265, "三國", "Tam Quốc"),
        (265, 420, "晉", "Tấn"),
        (420, 589, "南北朝", "Nam Bắc Triều"),
        (386, 534, "北魏", "Bắc Ngụy"),
        (534, 550, "東魏", "Đông Ngụy"),
        (550, 577, "北齊", "Bắc Tề"),
        (535, 556, "西魏", "Tây Ngụy"),
        (557, 581, "北周", "Bắc Chu"),
        (502, 557, "梁", "Lương"),
        (557, 589, "陳", "Trần"),
        (589, 618, "隋", "Tùy"),
        (618, 907, "唐", "Đường"),
        (907, 960, "五代十國", "Ngũ Đại Thập Quốc"),
        (960, 1127, "北宋", "Bắc Tống"),
        (1127, 1279, "南宋", "Nam Tống"),
        (1271, 1368, "元", "Nguyên"),
        (1368, 1644, "明", "Minh"),
        (1644, 1912, "清", "Thanh"),
    ]
    best = None
    best_span = None
    for (s, e, zh, vi) in _DYNASTIES:
        if s <= year_ce <= e:
            span = e - s
            if best_span is None or span < best_span:
                best = (zh, vi, s, e)
                best_span = span
    if not best:
        return None
    row = (best[0], best[1], "", best[2], best[3])
    return {
        "dynasty_zh": row[0],
        "dynasty_vi": row[1] or "",
        "era_name": row[2] or "",
        "dynasty_start": row[3],
        "dynasty_end": row[4],
        "source": "chinese_dynasties_static",
        "license": "public domain"
    }




def _ensure_place_timeline_events_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS place_timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dila_id TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'founding',
            year INTEGER, year_end INTEGER,
            label_zh TEXT, label_vi TEXT,
            source TEXT NOT NULL, source_ref TEXT,
            confidence TEXT DEFAULT 'verified',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pte_dila ON place_timeline_events(dila_id)")
    conn.commit()




def _t172_load_hv(conn, person_id):
    """T172 — đọc sidecar person_hanviet_debug → object hv (debug charwise) cho 1 person.

    SPEC §11 helper; trả None nếu chưa migrate/không có row (UI tự ẩn).
    """
    d_row = conn.execute(
        "SELECT han_name_raw, han_viet_legacy, han_viet_charwise, han_char_count, "
        "       han_viet_syllable_count, unknown_characters, han_viet_validation_status, "
        "       han_viet_validation_reason, legacy_match_status, is_transliteration, "
        "       dict_version "
        "FROM person_hanviet_debug WHERE person_id = ?", (person_id,)
    ).fetchone()
    if not d_row:
        return None
    return {
        'raw': d_row['han_name_raw'],
        'legacy': d_row['han_viet_legacy'],
        'charwise': d_row['han_viet_charwise'],
        'han_count': d_row['han_char_count'],
        'syll_count': d_row['han_viet_syllable_count'],
        'unknown': d_row['unknown_characters'] or '',
        'status': d_row['han_viet_validation_status'],
        'reason': d_row['han_viet_validation_reason'] or '',
        'legacy_match': d_row['legacy_match_status'],
        'is_transliteration': d_row['is_transliteration'],
        'dict_version': d_row['dict_version'],
    }




# ─── CHRONOLOGY API ─────────────────────────────────────────
CHRONOLOGY_DB = DB_PATH



def get_chronology_conn():
    conn = sqlite3.connect(CHRONOLOGY_DB)
    conn.row_factory = sqlite3.Row
    return conn




# ── T50 Job Control (run / stop / job-status) ──────────────────────────────
import subprocess as _t50_sp


import signal as _t50_sig



_T50_STATUS_FILE = os.path.join(os.path.dirname(__file__), 'data', 't50_job_status.json')


_T50_LOG_FILE    = os.path.join(os.path.dirname(__file__), 'data', 't50_job.log')


_T50_SCRIPT      = os.path.join(os.path.dirname(__file__), 'scripts', 't50_passage_vi_backfill.py')



def _t50_pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False



def _t50_read_job():
    try:
        with open(_T50_STATUS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"running": False, "sigla": None, "pid": None, "started_at": None}



def _t50_write_job(d):
    try:
        with open(_T50_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass



def _t50_log_tail(n=15):
    try:
        with open(_T50_LOG_FILE, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-n:] if l.strip()]
    except Exception:
        return []




def _t50_start_sigla(sigla, st):
    """Helper: spawn backfill subprocess cho 1 sigla, cập nhật st dict, write job file."""
    cmd = ['python', '-X', 'utf8', _T50_SCRIPT, '--sigla', sigla, '--sleep', '1.0']
    log_f = open(_T50_LOG_FILE, 'w', encoding='utf-8')
    proc = _t50_sp.Popen(cmd, stdout=log_f, stderr=log_f,
                          cwd=os.path.dirname(__file__),
                          env={**os.environ, 'PYTHONUTF8': '1'})
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    st.update({"running": True, "sigla": sigla, "pid": proc.pid, "started_at": now})
    _t50_write_job(st)
    return proc.pid




# ─────────────────────────────────────────────────────────────────────────────
# T181 — CBETA Catalog + Lazy Import (P3/P4)
# ─────────────────────────────────────────────────────────────────────────────

_T181_XML_ROOT = os.path.join(os.path.dirname(__file__), 'data', 'cbeta', 'xml-p5-full')


_T181_CBETA_DB  = os.path.join(os.path.dirname(__file__), 'data', 'cbeta', 'cbeta.db')


_T181_IMPORT_PY = os.path.join(os.path.dirname(__file__), 'data', 'cbeta', 'import_cbeta.py')




def _t181_xml_path(sigla):
    """Trả đường dẫn dự kiến cho file XML của sigla, hoặc None nếu không tìm thấy."""
    import re as _re
    m = _re.match(r'^([A-Z])(\d+)n(\d+)', sigla)
    if not m:
        return None
    series, vol_str = m.group(1), m.group(2)
    p = os.path.join(_T181_XML_ROOT, series, f'{series}{vol_str}', f'{sigla}.xml')
    return p if os.path.exists(p) else None




# ─────────────────────────────────────────────────────────────────────────────
# T183 — LAZY-FETCH FALLBACK (2026-09-27)
#
# BỐI CẢNH — TẠI SAO 20% BỘ KINH THIẾU XML LOCAL:
#   • xml-p5-full (clone từ cbeta-org/xml-p5) chỉ có volumes T01-T55 + T85.
#   • Volumes T56-T84 (583 bộ, sh_number 2185-2731) KHÔNG có trong repo public.
#   • Lý do: T56-T84 là phụ lục học thuật Nhật Bản (mục lục, chú giải, nghiên
#     cứu) — CBETA chưa phát hành XML công khai vì vấn đề bản quyền (tác giả
#     Nhật thế kỷ 20 vẫn còn thời hạn copyright).
#
# GIẢI PHÁP TỰ ĐỘNG (hàm này):
#   1. Với T01-T55/T85: fallback download từ GitHub raw (cbeta-org/xml-p5).
#      Thường không cần vì xml-p5-full đã clone đủ. Phòng khi file bị xóa.
#   2. Với T56-T84: KHÔNG có nguồn tự động. Trả (None, reason) để batch-import
#      ghi log rõ ràng và admin biết cần xử lý thủ công.
#
# CÁCH THÊM T56-T84 VÀO LOCAL (thủ công, 1 lần):
#   Bước 1: Vào https://cbeta.org/download → tải "CBReader 2X v0.9.9.2 經文資料檔"
#            (bookcase_v0992_20260831.zip, 1.21 GB).
#   Bước 2: Giải nén, tìm thư mục XML (thường trong bookcase/T56..T84/).
#   Bước 3: Copy vào data/cbeta/xml-p5-full/T/ theo cấu trúc:
#            T56/T56n{num}.xml, T57/T57n{num}.xml, ...
#   Sau đó batch-import sẽ tự tìm được — không cần thay đổi code.
#
# VOLUMES T56-T84 CHỨA GÌ:
#   T56-T84: Luật tạng bổ sung, truyện ký, mục lục, sử liệu, thư tịch học.
#   Phần lớn là tài liệu nghiên cứu, ít được dịch sang tiếng Việt.
#   Ưu tiên dịch thấp hơn kinh văn chính (T01-T55).
# ─────────────────────────────────────────────────────────────────────────────
_T183_GITHUB_RAW = 'https://raw.githubusercontent.com/cbeta-org/xml-p5/master'


# Volumes có XML trên GitHub public (cbeta-org/xml-p5):
_T183_PUBLIC_VOLS = set(range(1, 56)) | {85}   # T01-T55 + T85




def _t183_lazy_fetch_xml(sigla):
    """Fallback khi XML không có local: thử download từ GitHub raw.

    Trả về (path_or_None, reason_str):
      - ('đường_dẫn', 'downloaded')     nếu download thành công + cache local
      - (None, 'T56_T84_no_public_xml') nếu thuộc volumes không có XML public
      - (None, 'download_failed:...')   nếu download lỗi
      - (None, 'sigla_invalid')         nếu sigla không đúng format
    """
    import re as _re, urllib.request as _req, pathlib as _pl
    m = _re.match(r'^([A-Z]+)(\d+)n(\d+)', sigla)
    if not m:
        return None, 'sigla_invalid'

    series, vol_int, vol_str = m.group(1), int(m.group(2)), m.group(2)

    # Kiểm tra volume có XML public không
    if series == 'T' and vol_int not in _T183_PUBLIC_VOLS:
        # T56-T84: không có trên GitHub — phải download thủ công
        return None, (
            f't{vol_int:02d}_no_public_xml | '
            f'Volume T{vol_str} (sh_number khoảng 2185-2731) thuộc T56-T84, '
            f'chưa có trên GitHub public. '
            f'Admin tự download: cbeta.org/download → bookcase_v0992.zip → '
            f'copy T{vol_str}/ vào data/cbeta/xml-p5-full/T/'
        )

    # Thử download từ GitHub raw
    url = f'{_T183_GITHUB_RAW}/{series}/{series}{vol_str}/{sigla}.xml'
    dest_dir = _pl.Path(_T181_XML_ROOT) / series / f'{series}{vol_str}'
    dest = dest_dir / f'{sigla}.xml'
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        _req.urlretrieve(url, dest)
        return str(dest), 'downloaded'
    except Exception as _e:
        return None, f'download_failed:{_e}'




def _wiki_search_lang(lang, term, headers):
    """Search one Wikipedia language edition for `term`, return a snapshot dict
    or None. Used by wiki_fetch()'s vi -> zh -> en fallback chain (T07)."""
    import re as re_html
    import html as html_lib
    try:
        resp = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": term,
                    "format": "json", "srlimit": 1, "srprop": "snippet"},
            headers=headers, timeout=8
        )
        pages = resp.json().get('query', {}).get('search', [])
        if not pages:
            return None
        title = pages[0]['title']
        # Strip tags first, then unescape entities (the search snippet's HTML
        # bolds the matched term, e.g. <span class="searchmatch">X</span>, and
        # separately encodes quotes as &quot; — stripping tags alone left the
        # entity literally as "&quot;" in the rendered UI).
        snippet = html_lib.unescape(re_html.sub(r'<[^>]+>', '', pages[0].get('snippet', '')))
        ext_resp = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "extracts", "exintro": 1,
                    "titles": title, "format": "json"},
            headers=headers, timeout=8
        )
        pages2 = ext_resp.json().get('query', {}).get('pages', {})
        html_extract = next((p['extract'] for p in pages2.values() if 'extract' in p), '')
        plain_text = html_lib.unescape(re_html.sub(r'<[^>]+>', '', html_extract))
        return {
            "title": title,
            "url": f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}",
            "snippet": (snippet or plain_text)[:500],
            "full_text": plain_text[:2000],
            "content_html": html_extract,
            "lang": lang,
        }
    except Exception:
        return None



def _resolve_place_id(conn, dila_id):
    """T67: resolve ID thực trong DB (places_pending.id == entity_hub.canonical_label).

    Frontend gửi id đã blanket pad (ensure_long_id → PL + 12 digits) nhưng một số place
    lưu id dạng raw ngắn hơn. Trả về dạng id THỰC tồn tại trong DB để:
      - entity_hub.canonical_label trùng khớp (để flip status verified),
      - canonical_decision.entity_ref / en_audit_log.entity_ref nhất quán.
    """
    raw = str(dila_id or '').strip()
    if not raw:
        return None
    attempts = [raw, ensure_long_id(raw)]
    for a in attempts:
        row = conn.execute("SELECT id FROM places_pending WHERE id = ? LIMIT 1", (a,)).fetchone()
        if row:
            return row[0]
        row = conn.execute("SELECT canonical_label FROM entity_hub WHERE canonical_label = ? LIMIT 1", (a,)).fetchone()
        if row:
            return row[0]
    return attempts[0]



def _persist_canonical_decision(conn, dila_id, action, field_name, old_value, new_value,
                                evidence_citations=None, authority_rank=None,
                                verification_status='verified', decision_note='', editor='admin',
                                mark_verified=True):
    """T67: ghi quyết định canonical + audit log + chuyển entity_hub.status='verified'.

    Additive — chỉ THÊM vào 2 bảng mới (canonical_decision, en_audit_log) và chuyển trạng thái
    entity_hub; KHÔNG sửa bảng nguồn. Caller phải commit sau khi gọi (dùng chung conn).
    verification_status chỉ = 'verified' khi admin THỰC SỰ duyệt (không backfill bulk).
    """
    import json as _json
    import datetime as _dt
    ref = _resolve_place_id(conn, dila_id)
    now = _dt.datetime.now().isoformat(timespec='seconds')
    ev = _json.dumps(evidence_citations, ensure_ascii=False) if evidence_citations else '[]'
    conn.execute("""
        INSERT INTO canonical_decision (entity_ref, canonical_name_vi, source_id, authority_rank,
            confidence, verification_status, decision_note, evidence_citations, editor, decided_at, updated_at)
        VALUES (?, ?, NULL, ?, 1.0, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_ref) DO UPDATE SET
            canonical_name_vi=excluded.canonical_name_vi,
            authority_rank=excluded.authority_rank,
            verification_status=excluded.verification_status,
            decision_note=excluded.decision_note,
            evidence_citations=excluded.evidence_citations,
            editor=excluded.editor,
            updated_at=excluded.updated_at
    """, (ref, new_value, authority_rank, verification_status, decision_note, ev, editor, now, now))
    conn.execute("""
        INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value,
            evidence_sources, authority_rank, editor, verification_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ref, action, field_name, old_value, new_value, ev, authority_rank, editor, verification_status, now))
    if mark_verified and ref:
        conn.execute("UPDATE entity_hub SET status = 'verified', updated_at = ? WHERE canonical_label = ?", (now, ref))




# ════════════════════════════════════════════════════════════════════════
# T427 — Tab "🗺️ Place" trong namevimap.html (giai đoạn 1: UI + API,
# KHÔNG Claude/Gemini AI, KHÔNG đổi schema).
#
# Danh sách gốc: places_dila (59.167 địa danh, ID dài PL + 12 số).
# Ghi (approve/edit): chỉ namevi_map_places, khớp theo dila_id DẠNG DÀI
# (ensure_long_id) — không ghi places_pending, không đổi schema.
# Audit: dùng lại _persist_canonical_decision() (T67), không tạo bảng log mới.
# ════════════════════════════════════════════════════════════════════════

def _t427_session_email(token):
    """Lấy email thật của session hiện tại (server.py /api/login/check trả thêm 'email').
    KHÔNG tin editor do client gửi trong body — bảo mật: editor phải đến từ session đã verify."""
    try:
        resp = requests.post(
            'http://127.0.0.1:5001/api/login/check',
            json={'session_token': token},
            timeout=5
        )
        d = resp.json()
        if d.get('valid'):
            return d.get('email') or 'admin'
    except Exception:
        pass
    return 'admin'




_T427_SOURCE_BADGE = {
    'manual': 'Admin sửa tay',
    'manual_fix': 'Admin sửa tay',
    'ttl_confirmed': 'TTL xác nhận',
}




def _t427_source_badge(source):
    """Badge nguồn tên Việt hiện tại — KHÔNG bao giờ ghi là tên của DILA (quy tắc ZQ).
    DILA chỉ có tên Hán; tên Việt luôn do ZQ/admin/TTL tạo ra."""
    if not source:
        return None
    return _T427_SOURCE_BADGE.get(source, 'phiên âm tự động')




# ── Cache số liệu 6 bộ lọc (độc lập với q/filter — toàn bộ places_dila) ──
# Query COUNT trên 59K dòng tốn ~0.2-0.6s; không cần tính lại mỗi request vì
# dữ liệu chỉ đổi khi Admin Pass/Sửa (hiếm, không cần real-time tuyệt đối).
# TTL ngắn (20s) đủ để UI thấy số mới sau khi Pass/Sửa mà vẫn giảm tải DB.
_T427_FILTER_CACHE = {'data': None, 'ts': 0.0}


_T427_FILTER_CACHE_TTL = 20.0




def _t427_filter_counts(conn):
    import time as _time
    now = _time.time()
    cached = _T427_FILTER_CACHE['data']
    if cached is not None and (now - _T427_FILTER_CACHE['ts']) < _T427_FILTER_CACHE_TTL:
        return cached
    agg = conn.execute("""
        SELECT COUNT(*) AS all_n,
               SUM(CASE WHEN m.id IS NULL OR m.vn_name_status IS NULL OR m.vn_name_status != 'reviewed' THEN 1 ELSE 0 END) AS needs_review_n,
               SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM vn_person_places vp WHERE vp.place_id = pd.id) THEN 1 ELSE 0 END) AS no_ttl_n
        FROM places_dila pd
        LEFT JOIN namevi_map_places m ON m.dila_id = pd.id
    """).fetchone()
    all_n = agg['all_n']
    result = {
        'all': all_n,
        'pass100': 0,
        'needs_review': agg['needs_review_n'],
        'no_claude': all_n,
        'no_gemini': all_n,
        'no_ttl': agg['no_ttl_n'],
    }
    _T427_FILTER_CACHE['data'] = result
    _T427_FILTER_CACHE['ts'] = now
    return result




def _t427_invalidate_filter_cache():
    """Gọi sau khi Pass/Sửa ghi DB để lần GET kế tiếp không trả số liệu cũ quá 20s."""
    _T427_FILTER_CACHE['data'] = None




def resolve_canonical(conn, entity_ref):
    """T68b: bỏ phiếu đa-nguồn → trả về canonical value tốt nhất cho name_vi của entity_ref.

    Trả về dict {value, score, sources, confidence, has_conflict}.
    Sau T69 (CBETA/Marcus wire), sẽ có nhiều ứng viên hơn.
    """
    a_map = _source_authority_map(conn)
    ranked = _name_vi_evidence(conn, entity_ref, a_map)
    if not ranked:
        return {"value": None, "score": 0, "sources": [], "confidence": 0.0, "has_conflict": False}
    top_val, top_info = ranked[0]
    has_conflict = False
    if len(ranked) >= 2:
        second_val, second_info = ranked[1]
        if (top_info['score'] - second_info['score']) < 50 and top_val != second_val:
            has_conflict = True
            _detect_conflicts(conn, ranked, entity_ref)
    return {
        "value": top_val,
        "score": top_info['score'],
        "sources": top_info['sources'],
        "confidence": top_info['confidence'],
        "has_conflict": has_conflict,
    }




def _source_authority_map(conn):
    """T68: đọc matrix source_authority → {source_code: {'score','order','implemented'}}."""
    rows = conn.execute(
        "SELECT source_code, authority_score, precedence_order, implemented FROM source_authority"
    ).fetchall()
    return {r['source_code']: {'score': r['authority_score'], 'order': r['precedence_order'], 'implemented': r['implemented']} for r in rows}




def _resolve_entity_id(conn, entity_ref):
    """T68: entity_ref ('PL…') → (entity_id INT, ref raw). Trả về (None, ref) nếu không có hub row."""
    ref = _resolve_place_id(conn, entity_ref)
    row = conn.execute("SELECT entity_id FROM entity_hub WHERE canonical_label = ?", (ref,)).fetchone()
    if row:
        return row[0], ref
    row = conn.execute("SELECT entity_id FROM entity WHERE dila_id = ?", (ref,)).fetchone()
    if row:
        return row[0], ref
    return None, ref




def _name_vi_evidence(conn, entity_ref, authority_map):
    """T68: gom các ứng viên tên Việt cho 1 địa danh, bỏ phiếu theo authority_score.

    Trả về list tuple (value, {score, sources, confidence, order}) đã sắp theo score giảm dần.
    """
    eid, ref = _resolve_entity_id(conn, entity_ref)
    votes = {}

    def add(value, source_code, confidence, order_hint=None):
        if not value or not str(value).strip():
            return
        v = str(value).strip()
        sc = (source_code or '').upper()
        info = authority_map.get(sc)
        if info is None or sc in ('DILA',):
            return
        score = info['score'] if info.get('implemented', 1) else 0
        o = order_hint if order_hint is not None else info.get('order', 99)
        cur = votes.get(v)
        if cur is None:
            votes[v] = {'score': score, 'sources': [sc], 'confidence': float(confidence or 0), 'order': o}
        else:
            if score > cur['score']:
                cur['score'] = score
                cur['order'] = min(cur['order'], o)
            if sc not in cur['sources']:
                cur['sources'].append(sc)
            cur['confidence'] = max(cur['confidence'], float(confidence or 0))

    for r in conn.execute("SELECT name_vi, source, confidence FROM namevi_map_places WHERE dila_id = ?", (ref,)):
        src = r['source'] or ''
        if src == 'manual':
            add(r['name_vi'], 'ZQLOCAL', r['confidence'] or 1.0, order_hint=0)
        elif src == 'auto_generated':
            add(r['name_vi'], 'ZQLOCAL', r['confidence'] or 0.5, order_hint=0)
    if eid is not None:
        for r in conn.execute("""
                SELECT c.source_id, d.source_code, c.object_text, c.confidence
                FROM entity_claims c LEFT JOIN data_sources d ON d.source_id = c.source_id
                WHERE c.entity_id = ? AND c.claim_type = 'NAME'
            """, (eid,)):
            if (r['source_code'] or '').upper() != 'DILA':
                add(r['object_text'], r['source_code'] or 'ZQLOCAL', r['confidence'] or 0.5)
    dec = conn.execute("SELECT canonical_name_vi FROM canonical_decision WHERE entity_ref = ?", (ref,)).fetchone()
    if dec and dec['canonical_name_vi']:
        add(dec['canonical_name_vi'], 'ZQLOCAL', 1.0, order_hint=0)
    ranked = sorted(votes.items(), key=lambda kv: (-kv[1]['score'], kv[1]['order']))
    return ranked




def _detect_conflicts(conn, ranked, entity_ref, threshold=50):
    """T68: phát hiện xung đột giữa các ứng viên tên Việt có score chênh lệch < threshold.

    Ghi conflict_pending (chỉ 1 lần/entity/field nếu chưa có pending). Gọi khi cần.
    """
    if len(ranked) < 2:
        return
    top = ranked[0]
    for v, d in ranked[1:]:
        if top[1]['score'] - d['score'] < threshold and top[0] != v:
            existing = conn.execute(
                "SELECT id FROM conflict_pending WHERE entity_ref=? AND field='name_vi' AND status='pending'",
                (entity_ref,)
            ).fetchone()
            if existing:
                continue
            conn.execute("""
                INSERT INTO conflict_pending (entity_ref, field, value_a, value_b, source_a, source_b, authority_a, authority_b)
                VALUES (?, 'name_vi', ?, ?, ?, ?, ?, ?)
            """, (entity_ref, top[0], v, top[1]['sources'][0], d['sources'][0], top[1]['score'], d['score']))



# ── T416 (2026-10-21): ép index cho places_pending LIKE trong /autocomplete ──
# Planner bỏ qua idx_places_pending_name_zh cho LIKE '%q%' dù đã ANALYZE; ép index
# đo được 1312 ms → 137 ms. Cache kết quả kiểm tra tồn tại index 1 lần/process.
_T416_PENDING_IDX = None




def _t416_pending_index_hint(conn):
    """True nếu idx_places_pending_name_zh tồn tại (an toàn khi DB khác thiếu index)."""
    global _T416_PENDING_IDX
    if _T416_PENDING_IDX is None:
        try:
            _T416_PENDING_IDX = bool(conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_places_pending_name_zh' LIMIT 1"
            ).fetchone())
        except Exception:
            _T416_PENDING_IDX = False
    return _T416_PENDING_IDX



def _pali_sanskrit_lookup(q, conn):
    """
    T58 (phương án b — KHÔNG tạo bảng place_lang_alias): tra cứu Pali/Sanskrit
    trực tiếp trong `pali_place_ref` (15 địa danh, seed DILA+SuttaCentral, không
    tự suy map tên kinh điển mở rộng vì không có nguồn seed cho phần đó).
    name_pali/name_skt có thể chứa nhiều biến thể phân tách bằng ' / ' (vd
    "Rājagaha" cho "Rajagriha" không dấu) — so khớp sau khi bỏ dấu/hạ chữ qua
    normalize_text() đã có sẵn trong app.py.
    Trả về list dila_id (PL...) khớp, rỗng nếu không tìm thấy hoặc bảng thiếu
    (VPS schema lag) — không literal 500.
    """
    nq = normalize_text(q)
    if not nq:
        return []
    try:
        rows = conn.execute(
            "SELECT dila_id, name_pali, name_skt FROM pali_place_ref"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    try:
        from rapidfuzz import fuzz
    except Exception:
        fuzz = None
    matched = []
    for r in rows:
        variants = []
        for field in (r['name_pali'], r['name_skt']):
            if field:
                variants.extend(re.split(r'\s*/\s*', field))
        for v in variants:
            nv = normalize_text(v)
            if not nv:
                continue
            if nq in nv or nv in nq:
                matched.append(r['dila_id'])
                break
            # Fuzzy fallback cho biến thể La-tinh hóa khác nhau (vd "Rajagriha" vs
            # "Rajagrha" từ Rājagṛha bỏ dấu) — vẫn chỉ so khớp trong 15 dòng seed có
            # sẵn, KHÔNG suy map mới. Ngưỡng 85 đủ chặt để tránh false-positive giữa
            # 15 địa danh khác nhau trong bảng.
            if fuzz and len(nq) >= 4 and fuzz.ratio(nq, nv) >= 85:
                matched.append(r['dila_id'])
                break
    return matched



# ── T469: lazy in-memory cache cho autocomplete trang chủ ──────────────────
# Lý do dùng cache thay vì SQLite scalar function 'normalize_text' gọi trực
# tiếp trong WHERE: đã đo (xem report T469) — gọi hàm Python qua ctypes cho
# từng dòng trong lúc SCAN 48,673 dòng của 'people' tốn 2.8–6s/lần, KHÔNG đạt
# mục tiêu <1s. Build cache 1 lần (~1.8s, chỉ xảy ra ở request đầu/sau khi
# process khởi động lại) rồi lọc substring trên chuỗi đã chuẩn hoá sẵn trong
# RAM cho kết quả ~15-35ms — đạt mục tiêu "ấm" của task. Không phải DB
# migration/index: chỉ là cache cấp ứng dụng, cùng kiểu với _LEX_EXACT/
# _LEX_LIST ở trên (dòng ~185) đã có sẵn trong file này. Không sửa DB.
_PERSON_SUGGEST_CACHE = None   # list[dict] — xây 1 lần từ bảng people


_WORK_SUGGEST_CACHE = None     # list[dict] — xây 1 lần từ bảng cbeta_catalog_vn



def _get_person_suggest_cache():
    global _PERSON_SUGGEST_CACHE
    if _PERSON_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT id, name_vi, name_zh, dynasty, birth_year, death_year
                FROM people
            """).fetchall()
        finally:
            conn.close()
        cache = []
        for r in rows:
            name_vi = r['name_vi'] or ''
            name_zh = r['name_zh'] or ''
            cache.append({
                'id': r['id'], 'name_vi': name_vi, 'name_zh': name_zh,
                'dynasty': r['dynasty'], 'birth_year': r['birth_year'], 'death_year': r['death_year'],
                '_norm_vi': normalize_text(name_vi), '_norm_zh': name_zh.lower(),
            })
        _PERSON_SUGGEST_CACHE = cache
    return _PERSON_SUGGEST_CACHE



def _get_work_suggest_cache():
    global _WORK_SUGGEST_CACHE
    if _WORK_SUGGEST_CACHE is None:
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT id, title_vi, title_zh, translator_vi AS translator, dynasty_vi AS era, sigla
                FROM cbeta_catalog_vn
            """).fetchall()
        finally:
            conn.close()
        cache = []
        for r in rows:
            title_vi = r['title_vi'] or ''
            title_zh = r['title_zh'] or ''
            cache.append({
                'id': r['id'], 'title_vi': title_vi, 'title_zh': title_zh,
                'translator': r['translator'], 'era': r['era'], 'sigla': r['sigla'],
                '_norm_vi': normalize_text(title_vi), '_norm_zh': title_zh.lower(),
            })
        _WORK_SUGGEST_CACHE = cache
    return _WORK_SUGGEST_CACHE




# ===== TTL HELPERS =====
def extract_dila_id_from_file(filename):
    """Extract dilaId from TTL file content"""
    filepath = os.path.join(TTL_OLD_DIR, filename)
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract from bkg:dilaId or da:dilaId
    match = re.search(r'(?:bkg|da):dilaId\s+"([^"]+)"', content)
    if match:
        return match.group(1)
    
    # Extract from URL pattern: ex:monk/xxx
    match = re.search(r'<ex:monk/([^>]+)>', content)
    if match:
        return match.group(1)
    
    return None



def get_dila_data(dila_id):
    """Get person data from DILA (people table)"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if row:
            return dict(row)
    finally:
        conn.close()
    return None



def get_marcus_data(dila_id):
    """Get person data from Marcus (marcus_networks table)"""
    conn = get_db()
    try:
        # Teachers: When person is STUDENT (student_id = dila_id), get the teacher
        teachers = [row[0] for row in conn.execute("""
            SELECT teacher_label FROM marcus_networks WHERE student_id = ?
        """, (dila_id,)).fetchall()]
        
        # Students: When person is TEACHER (teacher_id = dila_id), get the students
        students = [row[0] for row in conn.execute("""
            SELECT student_label FROM marcus_networks WHERE teacher_id = ?
        """, (dila_id,)).fetchall()]
        
        edge_count = conn.execute(
            "SELECT COUNT(*) FROM marcus_networks WHERE teacher_id = ? OR student_id = ?",
            (dila_id, dila_id)
        ).fetchone()[0]
        
        return {
            "teachers": teachers,
            "students": students,
            "edge_count": edge_count
        }
    finally:
        conn.close()



def check_lineage_conflict(dila_id):
    """Check if lineage name differs between DILA and Marcus"""
    conn = get_db()
    try:
        dila_sect = conn.execute(
            "SELECT sect FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        
        marcus_sect = conn.execute("""
            SELECT p.sect FROM networks n 
            JOIN people p ON n.related_id = p.id 
            WHERE n.monk_id = ? AND n.source_origin = 'Marcus' AND n.relation_type = 'lineage'
        """, (dila_id,)).fetchone()
        
        if dila_sect and marcus_sect:
            dila_val = dila_sect[0] or ""
            marcus_val = marcus_sect[0] or ""
            if dila_val and marcus_val and dila_val.strip() != marcus_val.strip():
                return True, dila_val, marcus_val
        return False, None, None
    finally:
        conn.close()



# Admin Extensions - Staging & Verification APIs
STAGING_FILE = os.path.join(DATA_DIR, 'staging.json')


VERIFICATION_FILE = os.path.join(DATA_DIR, 'verification.json')


def load_staging():
    if os.path.exists(STAGING_FILE):
        with open(STAGING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": []}



def load_verification():
    if os.path.exists(VERIFICATION_FILE):
        with open(VERIFICATION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": []}



# ── T109: Admin Conflict Workflow (Zero-ALTER · additive, không đụng route cũ) ──
def _safe_audit_id(conn, claim_id):
    """Đọc audit_id từ bảng dẫn xuất T109; None nếu chưa có ETL (route bền với rollback)."""
    try:
        r = conn.execute("SELECT audit_id FROM entity_claims_audit WHERE claim_id=?", (claim_id,)).fetchone()
        return r['audit_id'] if r else None
    except sqlite3.OperationalError:
        return None




_ai_batch_running = False  # flag đơn giản, không cần thread lock phức tạp



@app.route('/api/admin/ai-transliterate/run', methods=['POST'])
@app.route('/daoanh/api/admin/ai-transliterate/run', methods=['POST'])
def ai_transliterate_run():
    """POST kích hoạt batch AI transliterate trong background thread."""
    global _ai_batch_running
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 403
    if _ai_batch_running:
        return jsonify({'ok': False, 'error': 'Batch đang chạy, vui lòng đợi'}), 409
    data   = request.get_json() or {}
    limit  = data.get('limit')   # None = toàn bộ
    reset  = bool(data.get('reset', False))

    def _run():
        global _ai_batch_running
        _ai_batch_running = True
        try:
            import subprocess, sys
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'ai_batch_transliterate.py')
            cmd = [sys.executable, script]
            if limit:
                cmd += ['--limit', str(int(limit))]
            if reset:
                # reset không cần confirm khi gọi từ API
                conn = sqlite3.connect(SQLITE_DB, timeout=30)
                conn.execute("DELETE FROM ai_person_name")
                conn.commit()
                conn.close()
            subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        except Exception as e:
            import traceback; traceback.print_exc()
        finally:
            _ai_batch_running = False

    import threading
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({'ok': True, 'message': 'Batch đã bắt đầu chạy trong background. Kiểm tra /ai-transliterate/status để theo dõi.'})


    

# ===== KEYWORD IMPORT API (parse + bulk) =====

def normalize_keyword(kw):
    kw = kw.strip()
    if not kw:
        return kw
    return ' '.join(w[0].upper() + w[1:] for w in kw.split())




def normalize_value(val):
    val = (val or '').strip()
    if not val:
        return val
    return val[0].upper() + val[1:]




# ===== NAMEVI FAST LOCAL TRANSLATE (Hán-Việt character-by-character) =====

@app.route('/daoanh/api/admin/namevi/translate-local', methods=['POST'])
def admin_namevi_translate_local():
    body = request.get_json(silent=True) or {}
    han_name = (body.get('han_name') or '').strip()
    record_id = (body.get('id') or body.get('dila_id') or '').strip()
    if not han_name:
        return jsonify({"ok": False, "error": "Thiếu han_name"}), 400
    # Convert each CJK char to Title-Case Hán-Việt reading, join with spaces
    _init_hv_cache()
    parts = []
    for c in han_name:
        if '\u4e00' <= c <= '\u9fff':
            hv = CUSTOM_HANVIET.get(c)
            if not hv:
                hv = _HV_CACHE.get(c) if _HV_CACHE else None
            if hv:
                parts.append(hv[0].upper() + hv[1:] if len(hv) > 1 else hv.upper())
        else:
            if c.strip():
                parts.append(c)
    vi_suggest = ' '.join(parts)
    if record_id:
        try:
            conn2 = sqlite3.connect(SQLITE_DB)
            existing = conn2.execute(
                "SELECT id FROM name_vi_map WHERE dila_id = ?", (record_id,)
            ).fetchone()
            if existing:
                conn2.execute(
                    "UPDATE name_vi_map SET name_vi_auto = ? WHERE dila_id = ?",
                    (vi_suggest, record_id)
                )
            else:
                conn2.execute(
                    "INSERT INTO name_vi_map (name_vi, name_vi_auto, name_zh, dila_id, source, confidence, created_at) VALUES (?, ?, ?, ?, 'local_translate', 0.5, ?)",
                    (vi_suggest, vi_suggest, han_name, record_id, datetime.now().isoformat())
                )
            conn2.commit()
            conn2.close()
        except Exception as e:
            pass
    return jsonify({"ok": True, "id": record_id, "name_vi_draft": vi_suggest})




# ===== T73 — BIO VI DRAFT ADMIN REVIEW =====

def _ensure_bio_vi_column():
    """Add bio_vi column to people table if not exists (run once)."""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(people)").fetchall()]
        if 'bio_vi' not in cols:
            conn.execute("ALTER TABLE people ADD COLUMN bio_vi TEXT")
            conn.commit()
        conn.close()
    except Exception:
        pass



_ensure_bio_vi_column()


def panorama_index():
    return send_from_directory(ADMIN_DIR, 'panorama.html')



# ===== COUNTER FILE PATH =====
COUNTER_FILE = os.path.join(DATA_DIR, 'counter.dat')




# T100-P3 (Batch 5) — Hai helper: dataset_version + verification_summary.
def _compute_dataset_version(conn, entity_id):
    """SHA256 deterministic từ claims của entity — phiên bản bộ dữ liệu học thuật.

    Cùng claims → cùng hash. Thêm/sửa claim → hash thay đổi.
    Trả dict {version: '8-char', full_hash: '64-char', claim_count: int}.
    """
    eid, _ = _resolve_entity_id(conn, entity_id)
    if eid is None:
        return {"version": "no_claims", "full_hash": "", "claim_count": 0}
    rows = conn.execute(
        "SELECT claim_id, claim_type, predicate, object_text, verification_status, confidence "
        "FROM entity_claims WHERE entity_id=? ORDER BY claim_id",
        (eid,)
    ).fetchall()
    if not rows:
        return {"version": "no_claims", "full_hash": "", "claim_count": 0}
    stable = "\n".join(
        f"{r['claim_id']}|{r['claim_type'] or ''}|{r['predicate'] or ''}"
        f"|{r['object_text'] or ''}|{r['verification_status'] or ''}|{r['confidence'] or ''}"
        for r in rows
    )
    full_hash = hashlib.sha256(stable.encode('utf-8')).hexdigest()
    return {"version": full_hash[:8], "full_hash": full_hash, "claim_count": len(rows)}




def _compute_verification_summary(claim_stats):
    """T100-P3 (Batch 5) — Tổng hợp verification_status từ claim_stats (đã có từ evidence API).

    claim_stats: {"total": int, "verification": {"unverified": n, ...}}
    release_status: 'releasable' nếu verified_ratio ≥ 0.5, else 'review_required'.
    """
    ver = claim_stats.get("verification", {})
    total = claim_stats.get("total", 0)
    verified_count = (ver.get("verified", 0) + ver.get("verified_direct", 0)
                      + ver.get("verified_crosswalk", 0))
    unverified_count = ver.get("unverified", 0)
    needs_review = ver.get("needs_review", 0)
    conflict = ver.get("conflict", 0)
    verified_ratio = round(verified_count / total, 4) if total > 0 else 0.0
    dominant = max(ver, key=lambda k: ver[k]) if ver else "no_claims"
    return {
        "verified_count": verified_count,
        "unverified_count": unverified_count,
        "needs_review_count": needs_review,
        "conflict_count": conflict,
        "verified_ratio": verified_ratio,
        "dominant_status": dominant,
        "release_status": "releasable" if verified_ratio >= 0.5 else "review_required",
    }




# T100-P0 — Evidence drawer (read-only) cho 1 subject (person/place).
# Tổng hợp bằng chứng: events + event_evidence, entity_claims qua entity_hub, co-mention.
# Không ghi DB. data_status giúp UI đánh dấu mức kiểm chứng TRUNG THỰC theo T100
# T262: regex trích xuất URL CBETA từ object_text MARCUS (đã có sẵn trong data, không tạo mới).
_T262_CBETA_URL_RE = re.compile(
    r'https?://cbetaonline\.dila\.edu\.tw/(?:zh/)?'
    r'(?:[A-Z]{1,3}\d+n[A-Z0-9]+)_(?:[a-z]\d+[a-c]\d+)'
)




# T57 — Glossary Đa Ngôn lookup (bản Việt từ lexicon + Yokoyama San-Tib-Chi + Marcus)
def _ensure_glossary_term_table(conn):
    """Bảng glossary_term (import Yokoyama) — tạo nếu chưa có (idempotent, additive)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS glossary_term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            language TEXT NOT NULL,
            definition TEXT,
            full_text TEXT,
            source_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term, language)
        )
    """)




# T36 — DharmaNexus (BuddhaNexus) Parallel Passages
# BuddhaNexus đã đổi tên thành DharmaNexus (dharmamitra.org/nexus)
# API: POST https://dharmamitra.org/api-db/text-view/text-parallels/
#      GET  https://dharmamitra.org/api-db/utils/raw-metadata/?filename=ZH_{vol}_{sigla}
# CBETA sigla → DharmaNexus ID: ZH_{TaishoVolume}_{sigla}
# Cache: data/cache/dharmanexus_{sigla}.json (24h)
_DN_SIGLA_MAP = {
    # T38 confirmed texts (volume manually verified)
    'T0220': 'ZH_T05_0220',  # Đại Bát Nhã (vol T05-T07, dùng T05)
    'T0221': 'ZH_T05_0221',
    'T0223': 'ZH_T08_0223',  # Đại Phẩm Bát Nhã
    'T0235': 'ZH_T08_0235',  # Kim Cang Kinh
    'T0251': 'ZH_T08_0251',  # Tâm Kinh
    'T0262': 'ZH_T09_0262',  # Pháp Hoa
    'T0310': 'ZH_T11_0310',  # Đại Bảo Tích
    'T0360': 'ZH_T12_0360',  # Vô Lượng Thọ
    'T0475': 'ZH_T14_0475',  # Duy Ma Cật
    'T0665': 'ZH_T16_0665',  # Kim Quang Minh
    'T0893': 'ZH_T18_0893',  # Kim Cang Đỉnh
    'T0945': 'ZH_T18_0945',  # Đại Nhật Kinh
}




# ===== T52 — Đối Chiếu Tam Tạng (Cross-Tradition Compare) =====
# Tập hợp cùng 1 đoạn kinh qua nhiều truyền thống: Hán (CBETA local),
# Tạng (Toh/84000), SAT (Đại Chính Unicode), DharmaNexus (real-time text-reuse),
# Pali/Sanskrit (SuttaCentral PTS numbering).
# Tái sử dụng T35/T36/T37/T38 — KHÔNG ghi đè route nào.
# Chỉ thêm THAM CHIẾU mới (static curated maps), KHÔNG đụng fake data 84000/VRI.

def _t52_normalize_sigla(raw):
    """Chuẩn hoá sigla nhận từ URL → các dạng dùng cho truy vấn.\n\n    Trả về dict: sh (số), dn ('T0251'), cbeta_full ('T08n0251'), raw.\n    Hỗ trợ các đầu vào: '251', 'T0251', 'T08n0251', 'T50n2060'.\n    """
    s = (raw or '').strip().upper().lstrip('T')
    # 'T08n0251' → sh '0251'; 'T50n2060' → sh '2060'
    m = re.match(r'^(\d+)N(\d+)$', s)
    sh = m.group(2) if m else re.sub(r'\D', '', s)
    sh = sh.zfill(4)
    vol = m.group(1) if m else ''
    vol_part = '' if m else ''
    return {
        'raw': raw or '',
        'sh': sh,
        'dn': 'T' + sh,
        'cbeta_full': ('T' + vol + 'n' + sh) if (m and vol) else None,
        'cbeta_full_vol': vol,
    }




# T52d — PTS / SuttaCentral numbering reference cho các kinh Hán phổ biến.
# KHÔNG nhúng text PTS (copyright) — chỉ SuttaCentral numbering + link mở full text.
# Mapping học thuật curated (tương ứng sutta theo truyền thống Pali) — T100 Batch 4 ĐÃ RÚT
# hardcode vào bảng `pali_cbeta_map` (seed 6 record qua scripts/etl_t100_batch4.py). Helper
# dưới đây đọc từ DB, fallback None khi chưa seed (không crash, UI tự ẩn khối Pali).
def _pali_cbeta_map_get(sh):
    """Lấy bản ghi Pali tham chiếu cho `sh` (forms['sh'], 4-số zfill) từ bảng pali_cbeta_map."""
    try:
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT pali_title, sc_uid, pts_sutta, note FROM pali_cbeta_map WHERE sh = ?",
                (sh,)
            ).fetchone()
            if not row:
                return None
            return {
                'pali_title': row['pali_title'] or '',
                'sc_uid': row['sc_uid'] or '',
                'pts_sutta': row['pts_sutta'] or '',
                'note': row['note'] or '',
            }
        finally:
            conn.close()
    except Exception:
        return None




# T52e — ánh xạ địa danh DILA (place_id) có trong pali_place_ref → SuttaCentral
# (data thật đọc từ bảng pali_place_ref qua route /places/<id>/pali — T37).


def api_cbeta_compare(sigla):
    """GET /daoanh/api/cbeta/<sigla>/compare?lang=vi&traditions=han,pali,tang

    Trả về array các phiên bản {tradition, title, text/preview, link_source, ref_code}
    cho UI Đối Chiếu Tam Tạng (T52). KHÔNG đụng fake data 84000/VRI — chỉ đọc:
      - Han: cbeta_content_index (cbeta.db — nếu đã import)
      - Tang: toh_cbeta_crossref (T38) → url 84000
      - SAT:  sat_crossref (T35) → url
      - Par:  DharmaNexus (T36) → real-time
      - Pali: pali_cbeta_map curated (T100 Batch 4 — rút từ _PALI_REF_MAP) → SuttaCentral (PTS numbering)
    """
    forms = _t52_normalize_sigla(sigla)
    lang = request.args.get('lang', 'vi')
    wanted = request.args.get('traditions', '')
    wanted = {t.strip().lower() for t in wanted.split(',') if t.strip()}

    def keep(t):
        return (not wanted) or t in wanted

    versions = []
    sigla_upper = forms['dn']

    # 1) Hán — CBETA local (cbeta.db). Nếu import → preview đoạn đầu.
    han_block = None
    try:
        cconn = get_cbeta_conn()
        # Nếu chưa có dạng full, thử các biến thể
        row = None
        cbeta_full = forms['cbeta_full']
        row = cconn.execute("SELECT id, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?", (forms['dn'],)).fetchone()
        if not row:
            row = cconn.execute("SELECT id, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?", (cbeta_full,)).fetchone()
        if row:
            first = cconn.execute(
                "SELECT content_zh FROM cbeta_content_index WHERE text_id = ? ORDER BY id LIMIT 1",
                (row['id'],)
            ).fetchone()
            han_text = (first['content_zh'] if first else '')[:1200]
            han_block = {
                'tradition': 'han', 'title': row['title_zh'] or sigla_upper,
                'text': han_text, 'link_source': None,
                'ref_code': sigla_upper, 'preview_len': len(han_text),
                'note': 'Bản Hán — từ CBETA database đã import. Dữ liệu địa phương, không phải dịch từ nguồn khác.',
                'has_local': bool(han_text),
                'badge_label': 'Hán Tạng — Local',
            }
        cconn.close()
    except Exception:
        pass
    if keep('han') and han_block:
        versions.append(han_block)

    # 2) Tạng — Toh crossref (T38)
    try:
        conn = get_db_connection()
        toh_rows = conn.execute(
            """SELECT toh, title_vi, title_en, url_84000, canon_section, confidence, note_vi
               FROM toh_cbeta_crossref WHERE cbeta_sigla = ? AND needs_review = 0""",
            (forms['dn'],)
        ).fetchall()
        for tr in toh_rows:
            if keep('tang'):
                versions.append({
                    'tradition': 'tang', 'title': tr['title_vi'] or tr['title_en'] or f"Toh {tr['toh']}",
                    'text': '', 'link_source': tr['url_84000'],
                    'ref_code': f"Toh {tr['toh']}",
                    'canon_section': tr['canon_section'],
                    'note': (tr['note_vi'] or '') + ('' if not tr['note_vi'] else ' · ') + f"Cross-ref từ toh_cbeta_crossref (T38). Confidence: {tr['confidence'] or 0.99}",
                    'badge_label': 'Tạng Truyền — 84000.co',
                })
        conn.close()
    except Exception:
        pass

    # 3) SAT — Daizōkyō Unicode (T35)
    try:
        conn = get_db_connection()
        sat_row = conn.execute(
            "SELECT cbeta_sigla, sat_url, has_unique FROM sat_crossref WHERE cbeta_sigla = ? LIMIT 1",
            (forms['dn'],)
        ).fetchone()
        conn.close()
        if sat_row and keep('sat'):
            versions.append({
                'tradition': 'sat', 'title': 'SAT Daizōkyō Text Database',
                'text': '', 'link_source': sat_row['sat_url'],
                'ref_code': sat_row['cbeta_sigla'], 'has_unique': bool(sat_row['has_unique']),
                'note': 'Phiên bản Kanji Unicode chuẩn JIS — nguồn phụ trợ cho bản Hán.',
                'badge_label': 'SAT — Đại học Tokyo',
            })
    except Exception:
        pass

    # 4) DharmaNexus — real-time text reuse (T36). Đọc cache nếu có, không thì gọi API.
    if keep('parallels') or keep('dharmanexus'):
        try:
            import os as _o, time as _t, json as _j
            cache_dir = _o.path.join(_o.path.dirname(__file__), 'data', 'cache')
            cache_path = _o.path.join(cache_dir, f'dharmanexus_{sigla_upper}.json')
            par_result = None
            if _o.path.exists(cache_path) and (_t.time() - _o.path.getmtime(cache_path) < 86400):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    par_result = _j.load(f)
            if not par_result:
                r = requests.get(
                    'http://localhost:5000/daoanh/api/cbeta/' + sigla_upper + '/parallels',
                    timeout=8, headers={'Accept': 'application/json'}
                )
                par_result = r.json() if r.status_code == 200 else None
            if par_result and par_result.get('dharmanexus_id'):
                versions.append({
                    'tradition': 'parallels', 'title': 'DharmaNexus (text-reuse)',
                    'text': '', 'link_source': par_result.get('dharmanexus_url'),
                    'ref_code': par_result.get('dharmanexus_id'),
                    'note': par_result.get('note_vi') or 'Kết quả phân tích liên văn bản, không phải bản dịch hay parallel text. Nguồn: dharmamitra.org',
                    'badge_label': par_result.get('badge_label', 'Phân tích liên văn bản — DharmaNexus'),
                    'from_cache': bool(par_result.get('from_cache')),
                })
        except Exception:
            pass

    # 5) Pali/Sanskrit — SuttaCentral PTS numbering (T52d; source: `pali_cbeta_map`)
    pali_info = _pali_cbeta_map_get(forms['sh'])
    if keep('pali') and pali_info:
        sc_uid = (pali_info.get('sc_uid') or '').strip()
        versions.append({
            'tradition': 'pali', 'title': pali_info.get('pali_title') or ('Song song Pali — sutta ' + forms['sh']),
            'text': '',
            'link_source': ('https://suttacentral.net/' + sc_uid) if sc_uid else None,
            'ref_code': pali_info.get('pts_sutta') or sc_uid or forms['dn'],
            'pts_sutta': pali_info.get('pts_sutta') or '',
            'note': pali_info.get('note') or 'Tham chiếu PTS/SuttaCentral — không nhúng text PTS (copyright).',
            'badge_label': 'Pali tham chiếu — SuttaCentral' if sc_uid else 'Pali tham chiếu',
        })

    return jsonify({
        'ok': True,
        'sigla': sigla_upper,
        'versions': versions,
        'total': len(versions),
        'note': 'Đối chiếu Tam Tạng — Hán/Pali/Tạng/SAT/DharmaNexus. T34 Phase A (fake data cleanup) chưa áp dụng: các crossref hiển thị đều là dữ liệu thật đã xác minh.',
    })




# ============================================================
#  T73 — Tạm Dịch DILA + Translation Cache
#  Lazy translation: check cache → dịch bằng Gemini với rules Phật học
#  → auto-save vào translation_cache → user report → admin invalidate theo rules_version
# ============================================================

# T95 (bảo mật): key KHÔNG còn literal trong source. Nguồn key: env GROQ_API_KEY
# trước, rồi groq_key trong data/llm_config.json (admin set qua API cập nhật key).
GROQ_KEY = os.environ.get('GROQ_API_KEY') or ''


GROQ_MODEL = os.environ.get('GROQ_MODEL') or 'qwen/qwen3.8-27b'


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"



# T165-P8.3: entity alignment pilot gate — MUST remain OFF by default (SPEC §12)
# Activation requires BOTH gate=True AND explicit X-T165-P8-Pilot:1 request header.
_P8_PILOT_GATE_ENABLED = False



LLM_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'llm_config.json')




def _llm_config_read():
    try:
        with open(LLM_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}




def _llm_config_write(update):
    try:
        cfg = _llm_config_read()
        cfg.update(update)
        with open(LLM_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.warning(f"[LLM_CONFIG] write failed: {e}")




def _t73_get_active_rules(conn):
    """Lấy danh sách rules đang active — T165: delegate SSOT select_rules (selector
    status='active' AND is_active=1 — SPEC #13). Không filter theo text (all-active)."""
    return _t165_select_rules(conn, None)['rules']




def _t73_rules_version(rules):
    """SHA256 của toàn bộ rule_text (theo thứ tự priority) → rules_version.
    Giữ semantic GLOBAL (panel admin + fallback legacy) — KHÔNG filter theo source_text."""
    combined = "\n---\n".join(r['rule_text'] for r in rules)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]




def _t73_source_hash(text):
    return _t165_source_hash(text)




def _p8_pilot_active(request_obj):
    """True iff T165-P8 pilot gate is ON, explicit header is present, and NOT a batch request.
    SPEC §3/§4: gate + header BOTH required; batch always blocked."""
    if not _P8_PILOT_GATE_ENABLED:
        return False
    if request_obj.headers.get('X-T165-P8-Pilot', '').strip() != '1':
        return False
    # Batch/background jobs must never activate P8 entity alignment (SPEC §4)
    body = request_obj.get_json(silent=True) or {}
    if body.get('is_batch'):
        return False
    return True




def _p8_compute_assertion_status(assertion_results: list) -> str:
    """Map check_entity_assertions results → entity_assertion_status string."""
    if not assertion_results:
        return 'all_pass'
    severities = {r.get('severity') for r in assertion_results}
    if 'HARD' in severities:
        return 'has_hard'
    if 'WARN' in severities:
        return 'has_warn'
    return 'all_pass'




def _t73_build_prompt(bio_zh, rules):
    """Xây dựng prompt dịch từ rules DB + nguyên bản chữ Hán (T73 legacy).
    Được T123 mở rộng thành Style Constitution qua _t73_build_style_prompt.
    Giữ nguyên để các caller cũ không phá vỡ."""
    rule_block = "\n".join(f"{i+1}. [{r['rule_type'].upper()}] {r['rule_text']}"
                           for i, r in enumerate(rules))
    return (
        "Bạn là dịch giả Phật học chuyên nghiệp. Dịch đoạn tiểu sử Hán văn sau sang tiếng Việt "
        "theo ĐÚNG các quy tắc bắt buộc dưới đây:\n\n"
        f"=== QUY TẮC DỊCH BẮT BUỘC ===\n{rule_block}\n\n"
        f"=== NGUYÊN BẢN HÁN VĂN ===\n{bio_zh}\n\n"
        "=== BẢN DỊCH TIẾNG VIỆT ==="
    )




def _t73_style_lock(conn, labels=None, max_glossary=120, max_exemplar=3, source_text=None,
                    resolver=None, max_ngrams=400, prompt_label='', json_mode=False,
                    extra_hash=None):
    """T123 — Style Constitution (rule + glossary lock + exemplar). T165: delegate SSOT.
    source_text cung cấp → select_rules lọc theo match_scope + glossary filter + tự chạy
    glossary_resolver và tính constitution_hash SAU merge (#5a). source_text=None →
    all-active (hành vi cũ = hôm nay). prompt_label/json_mode/extra_hash → tính vào
    constitution_hash (#5b). Trả dict {rules, rules_version, glossary[], exemplar[],
    known_pending[], constitution_hash, glossary_hash, codes, resolver,
    t166_lock_fingerprint}."""
    return _t165_style_lock(conn, source_text=source_text, max_glossary=max_glossary,
                            max_exemplar=max_exemplar, resolver=resolver,
                            max_ngrams=max_ngrams, prompt_label=prompt_label,
                            json_mode=json_mode, extra_hash=extra_hash)




def _glossary_resolver(conn, source_text, max_ngrams=400):
    """Pre-translation lookup across 14 authority tables in priority order (SPEC T165 #14).
    Generates 2-5 char n-grams from Hanzi runs in source_text, then batch-queries
    each authority table.  Returns:
      resolved:   {zh: {term_vi, source, status: 'db_verified'|'db_ambiguous'}}
      unresolved: [zh n-grams with no DB match — informational, not actionable]
    db_verified → injected into GLOSSARY LOCK so LLM never invents known terms.
    db_ambiguous → machine-generated only; LLM may use as hint.
    """
    import re as _re_gr
    if not source_text:
        return {'resolved': {}, 'unresolved': []}

    # Generate all unique n-grams (2-5 chars) from continuous Hanzi runs
    runs = _re_gr.findall(r'[一-鿿㐀-䶿]+', source_text)
    seen, ngrams = set(), []
    for run in runs:
        for n in (2, 3, 4, 5):
            for i in range(len(run) - n + 1):
                g = run[i:i + n]
                if g not in seen:
                    seen.add(g)
                    ngrams.append(g)
        if len(ngrams) >= max_ngrams:
            break
    if not ngrams:
        return {'resolved': {}, 'unresolved': []}

    resolved = {}
    ng_set = set(ngrams)
    ph = ','.join('?' * len(ngrams))  # IN-clause placeholders

    def _bulk(sql, args, src, status):
        """Bulk query; record first db_verified win per zh (lower-priority sources skip if already resolved)."""
        try:
            for row in conn.execute(sql, args).fetchall():
                zh, vi = row[0], row[1]
                if zh in ng_set and vi and zh not in resolved:
                    resolved[zh] = {'term_vi': vi, 'source': src, 'status': status}
        except Exception:
            pass

    # Priority 1: translation_glossary (human locked)
    _bulk(f"SELECT term_zh, term_vi FROM translation_glossary "
          f"WHERE term_zh IN ({ph}) AND is_locked=1", ngrams, 'translation_glossary', 'db_verified')
    # Priority 2: person_display_names
    _bulk(f"SELECT display_name_zh, display_name_vi FROM person_display_names "
          f"WHERE display_name_zh IN ({ph}) AND display_name_vi IS NOT NULL AND display_name_vi!=''",
          ngrams, 'person_display_names', 'db_verified')
    # Priority 3: vn_person_authority (verified)
    _bulk(f"SELECT name_zh, name_vi FROM vn_person_authority "
          f"WHERE name_zh IN ({ph}) AND status='verified' AND name_vi IS NOT NULL AND name_vi!=''",
          ngrams, 'vn_person_authority', 'db_verified')
    # Priority 4: canonical_decision
    _bulk(f"SELECT entity_ref, canonical_name_vi FROM canonical_decision "
          f"WHERE entity_ref IN ({ph}) AND canonical_name_vi IS NOT NULL AND canonical_name_vi!=''",
          ngrams, 'canonical_decision', 'db_verified')
    # Priority 5: name_vi_map (final approved)
    _bulk(f"SELECT name_zh, name_vi_final FROM name_vi_map "
          f"WHERE name_zh IN ({ph}) AND name_vi_final IS NOT NULL AND name_vi_final!=''",
          ngrams, 'name_vi_map', 'db_verified')
    # Priority 6: person_name_correction (approved)
    _bulk(f"SELECT name_zh, proposed_vi FROM person_name_correction "
          f"WHERE name_zh IN ({ph}) AND status='approved' AND proposed_vi IS NOT NULL AND proposed_vi!=''",
          ngrams, 'person_name_correction', 'db_verified')
    # Priority 7: term_glossaries (confidence≥0.7, exclude echo-back bad data)
    _bulk(f"SELECT term_zh, term_vi FROM term_glossaries "
          f"WHERE term_zh IN ({ph}) AND term_vi IS NOT NULL AND term_vi!='' AND term_vi!=term_zh",
          ngrams, 'term_glossaries', 'db_verified')
    # Priority 8: marcus_reference (curated label→label_vi, excludes echo-back)
    _bulk(f"SELECT label, label_vi FROM marcus_reference "
          f"WHERE label IN ({ph}) AND label_vi IS NOT NULL AND label_vi!='' AND label_vi!=label",
          ngrams, 'marcus_reference', 'db_verified')
    # Priority 9: namevi_map_places (reviewed or confidence≥0.8)
    _bulk(f"SELECT name_zh, name_vi FROM namevi_map_places "
          f"WHERE name_zh IN ({ph}) AND (vn_name_status='reviewed' OR confidence>=0.8) "
          f"AND name_vi IS NOT NULL AND name_vi!=''",
          ngrams, 'namevi_map_places_hq', 'db_verified')
    # Priority 10: cbeta_catalog_vn
    _bulk(f"SELECT title_zh, title_vi FROM cbeta_catalog_vn "
          f"WHERE title_zh IN ({ph}) AND title_vi IS NOT NULL AND title_vi!=''",
          ngrams, 'cbeta_catalog_vn', 'db_verified')
    # Priority 11: doctrine_concept
    _bulk(f"SELECT name_zh, name_vi FROM doctrine_concept "
          f"WHERE name_zh IN ({ph}) AND name_vi IS NOT NULL AND name_vi!=''",
          ngrams, 'doctrine_concept', 'db_verified')
    # Priority 12: monk_dict
    _bulk(f"SELECT han_name, vn_name FROM monk_dict "
          f"WHERE han_name IN ({ph}) AND vn_name IS NOT NULL AND vn_name!=''",
          ngrams, 'monk_dict', 'db_verified')
    # Priority 13: translation_rules (active) — extract vi_term from pattern "Vi (漢字) là..."
    try:
        import re as _re_tr
        tr_rows = conn.execute(
            "SELECT rule_text FROM translation_rules WHERE status='active'"
        ).fetchall()
        for row in tr_rows:
            rtext = (row[0] or '').strip()
            m = _re_tr.search(r'^([^（(（一-鿿]+?)\s*[（(]([一-鿿一-鿿]{2,})[）)]', rtext)
            if m:
                vi_part, zh_part = m.group(1).strip(), m.group(2)
                if zh_part in ng_set and vi_part and zh_part not in resolved:
                    resolved[zh_part] = {'term_vi': vi_part,
                                         'source': 'translation_rules_active', 'status': 'db_verified'}
    except Exception:
        pass
    # Priority 14: namevi_map_places (all — machine-generated, ambiguous)
    _bulk(f"SELECT name_zh, name_vi FROM namevi_map_places "
          f"WHERE name_zh IN ({ph}) AND name_vi IS NOT NULL AND name_vi!=''",
          ngrams, 'namevi_map_places', 'db_ambiguous')

    unresolved = [zh for zh in ngrams if zh not in resolved]
    return {'resolved': resolved, 'unresolved': unresolved}




def _t73_build_style_prompt(content, lock, label='văn bản', json_mode=False):
    """T123 — Unified Style-Lock prompt. T165: delegate SSOT build_style_prompt
    (nội dung lock đã filter theo source_text qua style_lock)."""
    return _t165_build_style_prompt(content, lock, label=label, json_mode=json_mode)




_T73_429_MAX_RETRY = 2          # T178 gap 13 — số lần retry tối đa khi 429 / lỗi mạng


_T73_429_BACKOFF_BASE = 0.5     # giây — backoff = BASE * 2**attempt (0.5s, 1s) — giữ worker thread ngắn




def _t73_call_gemini(prompt, source_type=None, source_text=None, conn=None,
                     constitution_hash=None):
    """Gọi Groq LLM, trả về (text, model_id, error_type).
    error_type: None=ok, 'key_error'=401/403, 'rate_limit'=429, 'api_error'=other.

    T178 gap 13: retry/backoff tối đa `_T73_429_MAX_RETRY` lần khi 429 (trước đây return
    ngay — 429 thật 3/5 lần theo đo T177 D7). Backoff 2s rồi 4s. Sau lần cuối vẫn trả
    `rate_limit` như cũ ⇒ KHÔNG đổi contract cho callers. Mỗi lần 429 persist 1 row metrics
    (token=0) để Admin thấy số lần xịt. KHÔNG có hard-gate token (baseline 3.400–3.700).
    """
    cfg = _llm_config_read()
    key = cfg.get('groq_key') or GROQ_KEY
    model = cfg.get('groq_model') or GROQ_MODEL
    if not key:
        _llm_config_write({'status': 'key_error',
                           'last_error': 'Thiếu GROQ_API_KEY env hoặc groq_key trong llm_config',
                           'last_error_at': datetime.now().isoformat()})
        return None, model, 'key_error'
    attempt = 0
    while True:
        try:
            resp = requests.post(GROQ_URL,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                json={'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.1, 'max_tokens': 2048},
                timeout=25)
            if resp.status_code in (401, 403):
                _llm_config_write({'status': 'key_error',
                                   'last_error': f'HTTP {resp.status_code}: key invalid or revoked',
                                   'last_error_at': datetime.now().isoformat()})
                return None, None, 'key_error'
            if resp.status_code == 429:
                attempt += 1
                if conn is not None:
                    _t165_persist_prompt_metrics(
                        conn, 0, 0, 0, source_type=source_type, source_text=source_text,
                        model_id=model, cache_hit=0, constitution_hash=constitution_hash,
                        logger=app.logger)
                if attempt > _T73_429_MAX_RETRY:
                    _llm_config_write({'status': 'rate_limit',
                                       'last_error': f'Rate limit / quota exceeded '
                                                     f'(đã retry {attempt - 1} lần)',
                                       'last_error_at': datetime.now().isoformat()})
                    app.logger.warning(
                        f'[T73] 429 hết retry ({attempt - 1}/{_T73_429_MAX_RETRY})')
                    return None, None, 'rate_limit'
                wait = _T73_429_BACKOFF_BASE * (2 ** (attempt - 1))
                app.logger.warning(
                    f'[T73] 429 — retry {attempt}/{_T73_429_MAX_RETRY} sau {wait}s')
                _llm_config_write({'status': 'rate_limit',
                                   'last_error': f'Rate limit — retry {attempt}/'
                                                 f'{_T73_429_MAX_RETRY} sau {wait}s',
                                   'last_error_at': datetime.now().isoformat()})
                time.sleep(wait)
                continue
            data = resp.json()
            if data.get('choices'):
                text = data['choices'][0]['message']['content'].strip()
                _t165_log_prompt_metrics(data, source_text=source_text, logger=app.logger,
                                         conn=conn, source_type=source_type,
                                         model_id=model, cache_hit=0,
                                         constitution_hash=constitution_hash)
                _llm_config_write({'status': 'ok', 'last_error': None})
                return text, model, None
            err = str(data.get('error', 'Unknown'))[:200]
            _llm_config_write({'status': 'api_error', 'last_error': err,
                               'last_error_at': datetime.now().isoformat()})
            return None, None, 'api_error'
        except Exception as e:
            attempt += 1
            app.logger.warning(f"[T73] Groq error (attempt {attempt}): {e}")
            if attempt > _T73_429_MAX_RETRY:
                return None, None, 'api_error'
            continue




# ============================================================
#  T447 — Cổng dịch AI thống nhất (translate_han_vi)
#  Đường vào DUY NHẤT cho mọi lệnh dịch Hán→Việt: nạp đủ quy tắc active qua
#  _t73_style_lock/_t73_build_style_prompt (SSOT style_constitution.py),
#  đọc/ghi translation_cache theo rules_version, KHÔNG tự dịch lại bản cũ khi
#  rules đổi (chỉ đánh dấu rules_outdated=True) — chỉ dịch lại khi force=True
#  (nút "Dịch lại" của admin). Giữ _t73_call_gemini làm đường gọi chính,
#  _call_gemini (hàm cũ, không có rules) làm dự phòng khi cổng lỗi hẳn.
# ============================================================

def _t447_append_translation_history(conn, old_row):
    """Giữ bản dịch cũ lại trong lịch sử trước khi 'Dịch lại' ghi đè (append-only,
    cột history_json — T447 migration). Pre-migration DB (cột chưa tồn tại) → no-op,
    KHÔNG làm hỏng luồng 'Dịch lại' (mất lịch sử nhưng vẫn dịch lại được)."""
    if old_row is None or not _t166_has_col(conn, 'translation_cache', 'history_json'):
        return
    try:
        raw = old_row['history_json']
    except (IndexError, KeyError):
        raw = None
    try:
        hist = json.loads(raw) if raw else []
        if not isinstance(hist, list):
            hist = []
    except Exception:
        hist = []
    hist.append({
        'translated_text': old_row['translated_text'],
        'model_id': old_row['model_id'],
        'rules_version': old_row['rules_version'],
        'status': old_row['status'],
        'created_at': old_row['created_at'],
        'superseded_at': datetime.now().isoformat(),
    })
    try:
        conn.execute(
            "UPDATE translation_cache SET history_json=? WHERE id=?",
            (json.dumps(hist, ensure_ascii=False), old_row['id'])
        )
    except Exception as e:
        app.logger.warning(f"[T447] không ghi được history_json cho id={old_row['id']}: {e}")




def translate_han_vi(conn, source_text, source_type, entity_id=None, label='văn bản',
                     json_mode=False, force=False, purpose=None):
    """T447 — Cổng dịch Hán→Việt thống nhất.

    Mọi lệnh dịch Hán→Việt (nút DỊCH AI, endpoint dịch đoạn văn, gợi ý tên,
    nút 'Dịch lại' của admin) PHẢI gọi hàm này thay vì gọi AI trực tiếp.

    Chính sách cache (SPEC T447, khớp done_when):
      - force=False + đã có bản dịch (bất kể rules_version khớp hay không)
        → trả về NGAY bản trong cache, KHÔNG gọi AI. Nếu rules đã đổi so với
          lúc dịch (rules_version lệch, hoặc status='edited') → rules_outdated=True
          để UI gắn nhãn "dịch theo quy tắc cũ". KHÔNG tự dịch lại.
      - Chưa có bản dịch nào (cache miss thật) → gọi AI qua _t73_call_gemini
        (có rules), ghi cache với rules_version hiện tại.
      - force=True (admin bấm 'Dịch lại') → bỏ qua cache, luôn gọi AI với rules
        hiện tại; bản cũ (nếu có) được copy vào history_json rồi mới ghi đè
        (giữ lịch sử, không xoá — SPEC §4 plan).

    Trả dict: {ok, translated_text, model_id, rules_version, constitution_hash,
    cache_hit, rules_outdated, status, source_hash, cache_id, used_fallback, forced}
    hoặc {ok: False, error} khi dịch thất bại (cache miss + AI lỗi hẳn).
    """
    text_in = (source_text or '').strip()
    if not text_in:
        return {'ok': False, 'error': 'empty_source'}

    src_hash = _t73_source_hash(text_in)
    lock = _t73_style_lock(conn, source_text=text_in, prompt_label=purpose or label,
                           json_mode=json_mode)
    rules_version = lock.get('rules_version')
    c_hash = lock.get('constitution_hash')

    existing = conn.execute(
        "SELECT * FROM translation_cache WHERE source_hash=? AND source_type=? "
        "AND status != 'invalidated' ORDER BY id DESC LIMIT 1",
        (src_hash, source_type)
    ).fetchone()

    def _outdated(row):
        if row is None:
            return False
        try:
            if (row['status'] or '') == 'edited':
                return True
        except (IndexError, KeyError):
            pass
        try:
            row_rv = row['rules_version']
        except (IndexError, KeyError):
            row_rv = None
        return row_rv != rules_version

    if existing and not force:
        return {
            'ok': True, 'translated_text': existing['translated_text'],
            'model_id': existing['model_id'], 'rules_version': existing['rules_version'],
            'constitution_hash': c_hash, 'cache_hit': True,
            'rules_outdated': _outdated(existing), 'status': existing['status'],
            'source_hash': src_hash, 'cache_id': existing['id'], 'forced': False,
        }

    # Cache miss thật, hoặc force=True ("Dịch lại") → gọi AI qua cổng (có rules).
    prompt = _t73_build_style_prompt(text_in, lock, label=label, json_mode=json_mode)
    text_out, model_id, err = _t73_call_gemini(
        prompt, source_type=source_type, source_text=text_in, conn=conn,
        constitution_hash=c_hash)
    used_fallback = False
    if not text_out:
        # Dự phòng: hàm AI trực tiếp cũ (không có rules) khi cổng lỗi hẳn —
        # GIỮ nguyên theo yêu cầu, không xoá _call_gemini.
        text_out = _call_gemini(prompt, timeout=15)
        used_fallback = bool(text_out)
        if used_fallback:
            model_id = model_id or GROQ_MODEL
    if not text_out:
        return {'ok': False, 'error': err or 'translate_failed', 'source_hash': src_hash,
               'rules_version': rules_version}

    if force and existing:
        _t447_append_translation_history(conn, existing)
        conn.execute(
            "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
            "WHERE id=?", (existing['id'],)
        )

    write_kwargs = {}
    if _t166_has_col(conn, 'translation_cache', 'constitution_hash'):
        write_kwargs['constitution_hash'] = c_hash
        write_kwargs['selected_rule_codes'] = lock.get('codes')
        write_kwargs['glossary_hash'] = lock.get('glossary_hash')
    cache_id, _written = _t165_write_cache(
        conn, src_hash, source_type, entity_id, text_in, text_out, model_id,
        rules_version, status='auto', **write_kwargs)
    conn.commit()
    return {
        'ok': True, 'translated_text': text_out, 'model_id': model_id,
        'rules_version': rules_version, 'constitution_hash': c_hash,
        'cache_hit': False, 'rules_outdated': False, 'status': 'auto',
        'source_hash': src_hash, 'cache_id': cache_id,
        'used_fallback': used_fallback, 'forced': bool(force),
    }




# ── DILA Card Translate (T148 → Vietnamese, Buddhist scholarly) ────────────

# Từ tiếng Việt thông thường KHÔNG thể xuất hiện trong tên tăng nhân Hán-Việt chuẩn.
# Nếu name_vi chứa bất kỳ từ nào trong set này → là machine transliteration xấu (dịch nghĩa thay vì âm).
_NON_HANVIET_NAME_WORDS = {
    # Thức ăn, đồ uống — không bao giờ xuất hiện trong tên thiền sư
    'hơi', 'táo', 'rau', 'cá', 'thịt', 'nước', 'gạo', 'sữa', 'trứng', 'muối',
    'bún', 'phở', 'xôi', 'bánh', 'chè', 'canh', 'cháo', 'bếp',
    # Đồ vật / tự nhiên thô — không dùng làm pháp hiệu
    'cái', 'cây', 'lá', 'quả', 'trái', 'hạt', 'đất', 'đá',
    # Đại từ / thán từ tiếng Việt thuần
    'này', 'kia', 'đó', 'vậy', 'thôi', 'rồi', 'nữa', 'lại',
    # Tính từ mức độ bình thường (không dùng làm danh hiệu)
    'ít', 'nhiều', 'nhỏ', 'lớn', 'cao', 'thấp', 'rộng', 'hẹp', 'nặng', 'nhẹ',
    'mới', 'cũ', 'tốt', 'xấu', 'đẹp', 'thật', 'giả', 'đúng', 'sai',
    # Màu sắc thô (không dùng làm danh hiệu — giữ 'vàng','bạc' vì có thể dùng)
    'đen', 'trắng', 'đỏ', 'tím', 'nâu', 'hồng', 'xám',
    # Phó từ / liên từ thuần Việt (không phải Hán-Việt)
    'chưa', 'đã', 'đang', 'sẽ', 'hoặc', 'vì', 'để',
    # Giữ lại: 'không' (空 tánh không), 'thế' (世 thế gian), 'hoa' (華 Hoa Nghiêm),
    #           'sao' (星), 'hay' (vì 'hay' có thể trong tên), 'con' (vì Quan Âm nam/nữ)
}



def _ok_hanviet_name(name_vi):
    """Trả True nếu name_vi có vẻ là Hán-Việt hợp lệ (không chứa từ tiếng Việt thông thường).
    Dùng để filter NAME LOCK — chỉ inject tên chất lượng tốt vào prompt dịch."""
    if not name_vi or len(name_vi.strip()) < 2:
        return False
    words = {w.lower() for w in name_vi.split()}
    return not words.intersection(_NON_HANVIET_NAME_WORDS)




def _build_dila_card_prompt(data, lock=None, person_name_lock=None):
    """Prompt dịch toàn bộ DILA card sang tiếng Việt Phật học hàn lâm.
    lock: dict từ _t73_style_lock(conn) — inject Glossary Lock + active DB rules vào prompt.
    person_name_lock: {zh_name: {name_vi, person_id}} — tên nhân vật đã xác nhận trong DB."""
    import json as _j
    truncated = dict(data)
    truncated['bio_concise'] = (data.get('bio_concise') or '')[:2000]
    truncated['bio_extensive'] = (data.get('bio_extensive') or '')[:4000]
    fields_block = _j.dumps(truncated, ensure_ascii=False, indent=2)

    # Glossary Lock từ DB (ưu tiên cao nhất — AI PHẢI tuân thủ)
    glossary_block = ""
    if lock and lock.get('glossary'):
        lines = "\n".join(f"  {g['term_zh']} → {g['term_vi']}" for g in lock['glossary'])
        glossary_block = (
            "=== GLOSSARY LOCK (bắt buộc — KHÔNG được dùng từ khác) ===\n"
            + lines + "\n\n"
        )

    # NAME LOCK: tên nhân vật đã xác nhận trong DB — AI không được tự phiên âm khác
    name_lock_block = ""
    if person_name_lock:
        lines = "\n".join(
            f"  {zh} ({v['person_id']}) → {v['name_vi']}"
            for zh, v in person_name_lock.items()
        )
        name_lock_block = (
            "=== TÊN NHÂN VẬT ĐÃ XÁC NHẬN TRONG DB (BẮT BUỘC — KHÔNG được phiên âm khác) ===\n"
            "Khi gặp các tên Hán dưới đây trong bất kỳ trường nào (bio, relations...), "
            "PHẢI dùng ĐÚNG tên tiếng Việt đã xác nhận, KHÔNG tự phiên âm lại:\n"
            + lines + "\n\n"
        )

    # Active rules từ DB (terminology + style)
    db_rules_block = ""
    if lock and lock.get('rules'):
        term_rules = [r for r in lock['rules']
                      if r.get('rule_type') in ('terminology', 'grammar')]
        if term_rules:
            lines = "\n".join(f"  [{r['rule_type'].upper()}] {r['rule_text'][:120]}"
                              for r in term_rules)
            db_rules_block = "=== QUY TẮC THUẬT NGỮ (từ Style Constitution DB) ===\n" + lines + "\n\n"

    return (
        "Bạn là thành viên Ban Dịch PTDA — dịch giả Hán-Việt chuyên ngành Phật học hàn lâm Việt Nam.\n"
        "Nhiệm vụ: dịch các trường thông tin nhân vật Phật giáo sau sang tiếng Việt.\n\n"
        + glossary_block
        + name_lock_block
        + db_rules_block
        + "QUY TẮC BẮT BUỘC (DILA card):\n"
        "1. [PHIÊN ÂM] Tên người và địa danh: phiên âm Hán-Việt tiêu chuẩn Phật học (Thích Pháp Hải, Thiếu Lâm Tự...), KHÔNG dùng bính âm.\n"
        "2. [GIỮ TÊN HÁN] Tên tác phẩm / kinh điển / dịch phẩm: giữ tên Hán gốc trong ngoặc đơn ngay sau tên Việt. Ví dụ: Diệu Pháp Liên Hoa Kinh (妙法蓮華經).\n"
        "3. [MÃ CBETA] Giữ nguyên mọi mã CBETA (T09n0262, A000005...) không xóa.\n"
        "4. [TRIỀU ĐẠI] Dùng tên chuẩn: 北宋→Bắc Tống, 南宋→Nam Tống, 唐→Đường, 元→Nguyên, 明→Minh, 清→Thanh, 宋→Tống, 隋→Tùy, 魏→Ngụy, 晉→Tấn, 漢→Hán, 五代→Ngũ Đại.\n"
        "5. [STYLE] Văn phong trang nghiêm, học thuật, dành cho độc giả Phật tử Việt Nam có học thức.\n"
        "6. Trường nào rỗng (\"\" hoặc []) → giữ nguyên trong output.\n"
        "7. relations: dùng ĐÚNG tên từ bảng TÊN NHÂN VẬT ĐÃ XÁC NHẬN ở trên cho \"name_vi\" nếu có; nếu không có trong bảng mới tự phiên âm.\n"
        "8. listbibl: mỗi phần tử có dạng \"( CBETA ref ) tiêu đề Hán\". Giữ nguyên phần \"( CBETA ref )\" "
        "và chỉ dịch tiêu đề Hán sau đó, giữ tên Hán trong ngoặc đơn bên cạnh tên Việt. "
        "Ví dụ: \"( CBETA T09n0262_p0001a01 ) Diệu Pháp Liên Hoa Kinh (妙法蓮華經) quyển 1\".\n"
        "9. [DEATH_NOTE] Trường \"death_note\" là ghi chú ngắn về năm sinh/mất từ nguồn Hán. "
        "Dịch sang tiếng Việt, giữ tên niên hiệu (年號) trong ngoặc đơn, giữ tên triều vua. "
        "Ví dụ: 卒於：唐, 敬宗, 長慶, 四年, 六月，86歲 → \"Mất năm Trường Khánh (長慶) thứ 4 (đời Đường Kính Tông), tháng 6, thọ 86 tuổi.\"\n"
        "10. [BIRTH_DEATH_QUOTE] Trường \"birth_death_quote\" là trích dẫn văn hiến Hán về năm sinh/mất. "
        "Dịch đầy đủ nội dung, giữ nguyên mã CBETA (X86n1601...) và số trang, "
        "giữ tên tài liệu Hán trong ngoặc đơn bên cạnh tên Việt. "
        "Ví dụ: 「長慶三年癸卯歲六月二十三日」→ \"tháng 6 năm Quý Mão Trường Khánh (長慶) thứ 3, ngày 23\".\n"
        "11. [SUGGESTED_RULES] Sau khi dịch xong, nếu gặp thuật ngữ/tên/địa danh nào CHƯA có trong Glossary Lock "
        "hoặc chưa có quy tắc rõ ràng trong các rules trên, hãy đề xuất bổ sung vào trường \"suggested_rules\". "
        "Mỗi đề xuất gồm: rule_code (viết hoa, dấu gạch dưới), rule_type (terminology/style/grammar/forbidden), "
        "description (1 dòng ngắn), rule_text (quy tắc cụ thể). "
        "Chỉ đề xuất khi thực sự cần thiết — không đề xuất những gì đã có trong Glossary Lock.\n"
        + (
            "KHÔNG đề xuất lại các thuật ngữ đã có trong hàng chờ phê chuẩn (chữ Hán đã biết): "
            + ", ".join(p['zh'] for p in (lock.get('known_pending') or [])[:40])
            + ".\n\n"
            if lock and lock.get('known_pending') else "\n"
        )
        + f"DỮ LIỆU CẦN DỊCH:\n{fields_block}\n\n"
        "Trả về DUY NHẤT một JSON object (không markdown fence, không giải thích):\n"
        "{\n"
        "  \"alt_names_vi\": [\"<phiên âm tên 1>\", ...],\n"
        "  \"occupation_vi\": \"<nghề nghiệp tiếng Việt>\",\n"
        "  \"place_of_origin_vi\": \"<nơi xuất thân tiếng Việt>\",\n"
        "  \"dynasty_vi\": \"<triều đại tiếng Việt>\",\n"
        "  \"bio_concise_vi\": \"<tiểu sử vắn tắt tiếng Việt>\",\n"
        "  \"bio_extensive_vi\": \"<tiểu sử chi tiết tiếng Việt>\",\n"
        "  \"listbibl_vi\": [\"( CBETA ref ) <tên Việt (tên Hán)>\", ...],\n"
        "  \"works_tripitaka_vi\": \"<tác phẩm trong Đại Tạng (giữ tên Hán trong ngoặc)>\",\n"
        "  \"works_by_vi\": \"<tác phẩm tự soạn (giữ tên Hán trong ngoặc)>\",\n"
        "  \"secondary_lit_vi\": \"<tài liệu tham khảo — dịch tên tác giả/nhan đề Hán sang Việt, giữ nguyên số liệu/năm/tên phương Tây>\",\n"
        "  \"mentioned_in_vi\": \"<được đề cập trong (giữ tên Hán)>\",\n"
        "  \"active_at_vi\": \"<nơi hoạt động tiếng Việt>\",\n"
        "  \"death_note_vi\": \"<ghi chú năm mất tiếng Việt — xem quy tắc 9>\",\n"
        "  \"birth_death_quote_vi\": \"<trích dẫn văn hiến dịch tiếng Việt — xem quy tắc 10>\",\n"
        "  \"relations_vi\": [{\"person_id\": \"A000xxx\", \"name_vi\": \"<tên phiên âm>\"}],\n"
        "  \"suggested_rules\": [\n"
        "    {\"rule_code\": \"TERM_XXX\", \"rule_type\": \"terminology\", "
        "\"description\": \"Dịch XXX → yyy\", \"rule_text\": \"XXX → yyy (lý do...)\"},\n"
        "    ...\n"
        "  ]\n"
        "}"
    )




def _save_suggested_rules(conn, suggested, entity_id, model_id, resolver=None):
    """Lưu rules đề xuất từ AI vào translation_rules với status='pending'.
    resolver: kết quả từ _glossary_resolver — dùng để reject db_verified terms (4th dedup layer).
    Trả list các rule đã lưu (chỉ những rule CHƯA tồn tại)."""
    if not suggested:
        return []
    saved = []
    now = __import__('datetime').datetime.now().isoformat()
    for s in suggested:
        code = (s.get('rule_code') or '').strip().upper()
        rtype = (s.get('rule_type') or 'terminology').strip()
        desc = (s.get('description') or '').strip()
        text = (s.get('rule_text') or '').strip()
        if not code or not text:
            continue
        existing = conn.execute(
            "SELECT id, status FROM translation_rules WHERE rule_code=?", (code,)
        ).fetchone()
        if existing:
            continue  # Đã có (active hoặc pending) — bỏ qua
        # Check duplicate bằng chữ Hán: nếu chuỗi Hán ≥2 ký tự trong rule_text đã tồn tại
        # trong bất kỳ rule nào (active hoặc pending) → bỏ qua (tránh AI đề xuất lại
        # cùng thuật ngữ với rule_code khác, kể cả 2-char như 居士, 禪師)
        import re as _re_zh
        zh_terms = _re_zh.findall(r'[一-鿿]{2,}', text)
        # Thêm: extract term chính (phần trước →) để check riêng
        _m = _re_zh.match(r'\s*([一-鿿㐀-䶿]+)\s*[→\-]+', text)
        if _m:
            lead = _m.group(1)
            if lead not in zh_terms:
                zh_terms = [lead] + zh_terms
        if zh_terms and any(
            conn.execute("SELECT 1 FROM translation_rules WHERE rule_text LIKE ?",
                         (f'%{zh}%',)).fetchone()
            for zh in zh_terms
        ):
            continue  # Nội dung Hán đã có trong rule khác — bỏ qua
        # Check DB: nếu chữ Hán đã có tên Việt xác nhận → không cần tạo rule mới
        db_known = False
        if resolver:
            # 4th layer: use pre-computed resolver results (12 authority tables)
            for zh in zh_terms:
                if resolver.get('resolved', {}).get(zh, {}).get('status') == 'db_verified':
                    db_known = True; break
        if not db_known:
            # Fallback 5-table check (khi resolver không có)
            for zh in zh_terms:
                if conn.execute(
                    "SELECT 1 FROM translation_glossary WHERE term_zh=? AND term_vi IS NOT NULL AND term_vi!=''",
                    (zh,)).fetchone():
                    db_known = True; break
                if conn.execute(
                    "SELECT 1 FROM namevi_map_places WHERE name_zh=? AND name_vi IS NOT NULL AND name_vi!=''",
                    (zh,)).fetchone():
                    db_known = True; break
                if conn.execute(
                    "SELECT 1 FROM term_glossaries WHERE term_zh=? AND term_vi IS NOT NULL AND term_vi!=''",
                    (zh,)).fetchone():
                    db_known = True; break
                if conn.execute(
                    "SELECT 1 FROM places WHERE name_zh=? AND name_vi IS NOT NULL AND name_vi!=''",
                    (zh,)).fetchone():
                    db_known = True; break
                # canon_catalog: tên tác phẩm/kinh điển (title_zh có thể chứa extra text sau tên)
                if conn.execute(
                    "SELECT 1 FROM canon_catalog WHERE title_zh LIKE ? AND title_vi IS NOT NULL AND title_vi!=''",
                    (f'{zh}%',)).fetchone():
                    db_known = True; break
        if db_known:
            continue  # Thuật ngữ đã có trong DB với tên Việt xác nhận — không cần rule
        cur = conn.execute(
            "INSERT INTO translation_rules "
            "(rule_code, rule_type, description, rule_text, is_active, priority, "
            " status, suggested_by, created_by, created_at, updated_at) "
            "VALUES (?,?,?,?,0,200,'pending',?,?,?,?)",
            (code, rtype, desc, text,
             f'ai_dila:{entity_id}:{model_id or ""}',
             'ai_suggest', now, now)
        )
        saved.append({'id': cur.lastrowid, 'rule_code': code, 'rule_type': rtype,
                      'description': desc, 'rule_text': text})
    conn.commit()
    return saved




def _post_edit_hanzi_leakage(vi_dict):
    """Post-edit safety net: fix Hanzi characters leaked into Vietnamese translation fields.
    Covers known AI failure patterns where a compound is split and one char stays Hanzi.
    Applied after _parse_dila_vi_json on the returned dict (modifies in-place, returns dict).
    """
    import re as _re_pe
    _STRING_FIELDS = (
        'bio_concise_vi', 'bio_extensive_vi', 'occupation_vi', 'place_of_origin_vi',
        'dynasty_vi', 'active_at_vi', 'death_note_vi', 'birth_death_quote_vi',
        'works_tripitaka_vi', 'works_by_vi', 'secondary_lit_vi', 'mentioned_in_vi',
    )
    _RULES = [
        # 法嗣: 嗣 leaked after Pháp/pháp
        (r'([Pp]háp)\s*嗣', r'\1 tự'),
        # Remaining raw 法嗣 not caught above
        (r'法嗣', 'pháp tự'),
    ]
    if not vi_dict:
        return vi_dict
    for field in _STRING_FIELDS:
        val = vi_dict.get(field)
        if not val or not isinstance(val, str):
            continue
        for pattern, repl in _RULES:
            val = _re_pe.sub(pattern, repl, val)
        vi_dict[field] = val
    # Also fix inside relations_vi[].name_vi if any
    for rel in (vi_dict.get('relations_vi') or []):
        if rel.get('name_vi') and isinstance(rel['name_vi'], str):
            for pattern, repl in _RULES:
                rel['name_vi'] = _re_pe.sub(pattern, repl, rel['name_vi'])
    return vi_dict




def _dict_or(row, col):
    """Đọc cột nullable; trả None khi sqlite3.Row không có cột (pre-migration)."""
    if row is None:
        return None
    try:
        return row[col]
    except (IndexError, KeyError):
        return None




def _json_or_parse(row, col):
    """Đọc cột JSON string → list/dict; None khi rỗng / unavailable."""
    raw = _dict_or(row, col)
    if not raw:
        return None
    try:
        return _j.loads(raw)
    except Exception:
        return None




def _parse_dila_vi_json(text):
    """Trích xuất JSON hợp lệ từ phản hồi LLM (xử lý markdown fence nếu có)."""
    import json as _j, re as _re
    if not text:
        return None
    text = text.strip()
    text = _re.sub(r'^```(?:json)?\s*', '', text, flags=_re.MULTILINE)
    text = _re.sub(r'```\s*$', '', text, flags=_re.MULTILINE)
    text = text.strip()
    m = _re.search(r'\{[\s\S]+\}', text)
    if m:
        try:
            return _j.loads(m.group(0))
        except Exception:
            pass
    try:
        return _j.loads(text)
    except Exception:
        return None




def _t166_has_col(conn, table, col):
    """T166 guard pre-migration (mirror style_constitution._has_col): trả True khi
    cột identity_* đã migrate. CHẶN SQL bỏ sót cột khi DB chưa chạy migration."""
    try:
        return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})").fetchall())
    except Exception:
        return False




@app.route('/daoanh/api/admin/person/<person_id>/revalidate-hv', methods=['POST'])
def api_admin_revalidate_hv(person_id):
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    try:
        p = conn.execute(
            'SELECT id, name_zh, name_vi FROM people WHERE id=?', (person_id,)
        ).fetchone()
        if not p:
            return jsonify({'ok': False, 'error': 'Khong tim thay nguoi'}), 404
        name_zh = (p['name_zh'] or '').strip()
        name_vi = (p['name_vi'] or '').strip()
        _init_hv_cache()
        parts = []
        unknown_chars = []
        for c in name_zh:
            if '\u4e00' <= c <= '\u9fff':
                hv = CUSTOM_HANVIET.get(c) or (_HV_CACHE.get(c) if _HV_CACHE else None)
                if hv:
                    parts.append(hv[0].upper() + hv[1:] if len(hv) > 1 else hv.upper())
                else:
                    parts.append(c)
                    unknown_chars.append(c)
            elif c.strip():
                parts.append(c)
        charwise = ' '.join(parts)
        han_count = sum(1 for c in name_zh if '\u4e00' <= c <= '\u9fff')
        syll_count = len(parts)
        unknown_str = ''.join(unknown_chars) if unknown_chars else None
        if name_vi and charwise and name_vi.lower() == charwise.lower():
            match_status = 'ok'
            val_status = 'valid'
            val_reason = ''
        elif unknown_chars:
            match_status = 'differs'
            val_status = 'unknown_char'
            val_reason = 'Tu chua biet: ' + ''.join(unknown_chars)
        else:
            match_status = 'differs' if name_vi else 'ok'
            val_status = 'needs_review' if name_vi else 'valid'
            val_reason = 'legacy name_vi khac charwise' if name_vi else ''
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        existing = conn.execute(
            'SELECT person_id FROM person_hanviet_debug WHERE person_id=?', (person_id,)
        ).fetchone()
        if existing:
            conn.execute(
                'UPDATE person_hanviet_debug SET '
                'han_viet_charwise=?, han_viet_legacy=?, han_char_count=?, '
                'han_viet_syllable_count=?, unknown_characters=?, '
                'han_viet_validation_status=?, han_viet_validation_reason=?, '
                'legacy_match_status=?, updated_at=? '
                'WHERE person_id=?',
                (charwise, name_vi, han_count, syll_count, unknown_str,
                 val_status, val_reason, match_status, now, person_id)
            )
        else:
            conn.execute(
                'INSERT INTO person_hanviet_debug '
                '(person_id, han_name_raw, han_viet_charwise, han_viet_legacy, '
                'han_char_count, han_viet_syllable_count, unknown_characters, '
                'han_viet_validation_status, han_viet_validation_reason, '
                'legacy_match_status, is_transliteration, updated_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,0,?)',
                (person_id, name_zh, charwise, name_vi, han_count, syll_count,
                 unknown_str, val_status, val_reason, match_status, now)
            )
        conn.commit()
        hv = {
            'raw': name_zh, 'legacy': name_vi, 'charwise': charwise,
            'han_count': han_count, 'syll_count': syll_count,
            'unknown': unknown_str or '', 'status': val_status,
            'reason': val_reason, 'legacy_match': match_status,
            'is_transliteration': 0,
            'dict_version': 'revalidated-' + now[:10],
        }
        return jsonify({'ok': True, 'hv': hv})
    finally:
        conn.close()




def _t85_units(conn, passage_id):
    """Lazy translate T85 v2 — liệt kê unit text_passages của passage legacy.
    Trả về None khi passage chưa có hàng text_passages (→ fallback legacy vi_text),
    trả về []/danh sách khi có (schema T94/T95)."""
    n = conn.execute(
        "SELECT COUNT(*) FROM text_passages WHERE legacy_passage_id = ?", (passage_id,)
    ).fetchone()[0]
    if n == 0:
        return None
    rows = conn.execute(
        "SELECT passage_id AS unit_id, work_id, canonical_ref, sequence_no, "
        "       original_zh, raw_zh_hash, loc_ref "
        "FROM text_passages WHERE legacy_passage_id = ? AND source_status = 'ok' "
        "ORDER BY sequence_no", (passage_id,)
    ).fetchall()
    return [dict(r) for r in rows]




def _t85_done_unit(conn, unit_id):
    """Trả translation_segments 'done' mới nhất (theo revision_no/created_at) của 1 unit."""
    row = conn.execute(
        "SELECT translation_id, translation_text, translation_status "
        "FROM translation_segments WHERE passage_id = ? AND language = 'vi' "
        "AND translation_status = 'done' "
        "ORDER BY revision_no DESC, created_at DESC LIMIT 1", (unit_id,)
    ).fetchone()
    return dict(row) if row else None




def _t85_get_segments(conn, units):
    """GET cache-only cho passage có text_passages: trả về bản dịch các unit đã done."""
    pair = []
    for u in units:
        d = _t85_done_unit(conn, u['unit_id'])
        pair.append({
            'unit_id': u['unit_id'],
            'sequence_no': u['sequence_no'],
            'canonical_ref': u['canonical_ref'],
            'translation_vi': d['translation_text'] if d else None,
            'translation_id': d['translation_id'] if d else None,
            'status': 'done' if d else 'missing',
        })
    vi = '\n\n'.join(x['translation_vi'] for x in pair if x['translation_vi'])
    ids = [x['translation_id'] for x in pair if x['translation_id']]
    return jsonify({
        'ok': True,
        'mode': 'segments',
        'from_cache': bool(vi),
        'vi_text': vi or None,
        'translation_id': ids[0] if ids else None,
        'units': pair,
    })




def _t85_translate_unit(conn, u, key, model, total, force):
    """Dịch 1 unit text_passages bằng Groq, lưu vào translation_segments (T85 v2).
    Pattern mirror T96 (/api/segments/translate): queued → translating → done/failed.
    Khi force=True → đánh dấu bản 'done' cũ là superseded, tạo bản mới revision_no+1."""
    import uuid as _uuid
    import json as _json
    unit_id = u['unit_id']
    old_tid = None
    now = datetime.now().isoformat()
    if force:
        old = conn.execute(
            "SELECT translation_id FROM translation_segments WHERE passage_id = ? "
            "AND language = 'vi' AND translation_status = 'done' "
            "ORDER BY revision_no DESC, created_at DESC LIMIT 1", (unit_id,)
        ).fetchone()
        if old:
            old_tid = old['translation_id']
        conn.execute(
            "UPDATE translation_segments SET translation_status = 'superseded', updated_at = ? "
            "WHERE passage_id = ? AND language = 'vi' AND translation_status = 'done'",
            (now, unit_id)
        )
        conn.commit()
    tid = 'ts-' + _uuid.uuid4().hex[:12]
    rev = conn.execute(
        "SELECT COALESCE(MAX(revision_no), 0) + 1 AS r FROM translation_segments "
        "WHERE passage_id = ? AND language = 'vi'", (unit_id,)
    ).fetchone()['r']
    zh = (u['original_zh'] or '').strip()
    # T123 — Style Constitution unified builder + prompt_version=rules_version (T165: filter theo text)
    lock = _t73_style_lock(conn, source_text=zh, json_mode=True)
    prompt = _t73_build_style_prompt(
        f"Đoạn {u['sequence_no']}/{total} — {u['canonical_ref']}:\n{zh}",
        lock, label='đoạn kinh', json_mode=True)
    prompt_version = lock['rules_version'] or 't96v1'
    conn.execute(
        """INSERT INTO translation_segments
           (translation_id, work_id, language, translation_text, translator_type,
            model_name, prompt_version, source_passage_ids, translation_status,
            passage_id, provider, source_original_hash, quality_status, revision_no,
            supersedes_translation_id, created_at, updated_at)
           VALUES (?, ?, 'vi', '', 'ai_groq', ?, ?, ?, 'queued', ?, 'groq', ?,
                   'unreviewed', ?, ?, ?, ?)""",
        (tid, u['work_id'], model, prompt_version, unit_id, unit_id, u['raw_zh_hash'],
         rev, old_tid, now, now)
    )
    conn.commit()
    try:
        conn.execute(
            "UPDATE translation_segments SET translation_status = 'translating', updated_at = ? "
            "WHERE translation_id = ?", (now, tid)
        )
        conn.commit()
        resp = requests.post(
            GROQ_URL,
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.2, 'max_tokens': 1024},
            timeout=30
        )
        result = resp.json()
        raw_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        vi = None
        try:
            vi = _json.loads(raw_content.strip()).get('translation_vi', '').strip()
        except Exception:
            vi = raw_content.strip()
        if not vi:
            raise ValueError("LLM trả về nội dung rỗng")
        conn.execute(
            "UPDATE translation_segments SET translation_text = ?, translation_status = 'done', "
            "model_name = ?, updated_at = ? WHERE translation_id = ?",
            (vi, model, now, tid)
        )
        conn.commit()
        return tid, vi, rev
    except Exception as e:
        conn.execute(
            "UPDATE translation_segments SET translation_status = 'failed', updated_at = ? "
            "WHERE translation_id = ?", (now, tid)
        )
        conn.commit()
        app.logger.error(f"[T85] translate unit {unit_id} failed: {e}")
        raise




def _t85_post_segments(conn, legacy_pid, units, force=False, max_units=40):
    """POST on-demand cho passage có text_passages: dịch các unit còn thiếu qua Groq,
    ghi translation_segments, phản chiếu passage.vi_text. Partial khi passage quá dài."""
    cfg = _llm_config_read()
    key = cfg.get('groq_key') or GROQ_KEY
    model = cfg.get('groq_model') or GROQ_MODEL
    if not key:
        return jsonify({'ok': False, 'error': 'GROQ_API_KEY chưa cấu hình'}), 503
    total = len(units)
    slice_units = units[:max_units]
    out_units = []
    vi_parts = []
    translated = from_cache = failed = 0
    for u in slice_units:
        d = _t85_done_unit(conn, u['unit_id'])
        if d and not force:
            vi_parts.append(d['translation_text'])
            out_units.append({
                'unit_id': u['unit_id'], 'sequence_no': u['sequence_no'],
                'canonical_ref': u['canonical_ref'],
                'translation_vi': d['translation_text'],
                'translation_id': d['translation_id'],
                'status': 'done', 'from_cache': True,
            })
            from_cache += 1
            continue
        try:
            tid, vi, _rev = _t85_translate_unit(conn, u, key, model, total, force)
            translated += 1
            vi_parts.append(vi)
            out_units.append({
                'unit_id': u['unit_id'], 'sequence_no': u['sequence_no'],
                'canonical_ref': u['canonical_ref'],
                'translation_vi': vi, 'translation_id': tid,
                'status': 'done', 'from_cache': False,
            })
        except Exception as e:
            failed += 1
            out_units.append({
                'unit_id': u['unit_id'], 'sequence_no': u['sequence_no'],
                'canonical_ref': u['canonical_ref'],
                'translation_vi': None, 'translation_id': None,
                'status': 'failed', 'error': str(e),
            })
            break
    vi = '\n\n'.join(x for x in vi_parts if x)
    if vi:
        conn.execute(
            "UPDATE passage SET vi_text = ?, translation_draft = 1 WHERE passage_id = ?",
            (vi, legacy_pid)
        )
        conn.commit()
    return jsonify({
        'ok': True,
        'mode': 'segments',
        'from_cache': bool(from_cache and not translated),
        'vi_text': vi or None,
        'translation_id': (out_units[0]['translation_id'] or None) if out_units else None,
        'translated': translated,
        'from_cache_units': from_cache,
        'failed': failed,
        'partial': total > max_units,
        'units': out_units,
    })




def _error_report_suggestion(error_type, note, rules):
    """T123 — Hệ thống gợi ý rule fix dựa trên loại lỗi + nội dung note.
    Trả về list rule_code đề xuất (ưu tiên khớp ngữ cảnh)."""
    suggestion = []
    text = ((note or '') + ' ' + error_type).lower()
    # nhóm lỗi → rule_code ưu tiên
    mappings = [
        (('kính ngữ', 'chàng', 'anh', 'cậu', 'ông', 'gã', 'hắn', 'xưng hô', 'tôn xưng', 'bất kính'),
         ['HONORIFIC_PRONOUN', 'ACADEMIC_STYLE']),
        (('pinyin', 'tiếng anh', 'english', 'thiếu lâm', 'quy nguyên', 'thích ca'), ['NO_PINYIN', 'CANONICAL_NAMES']),
        (('thêm', 'bịa', 'không có trong', 'thiếu nghĩa', 'thừa', 'ngoại suy', 'thêm nội dung'),
         ['NO_ADDITION', 'EXPRESSION_PRINCIPLE']),
        (('thuật ngữ', 'lệch', 'sai thuật ngữ', 'bát nhã', 'niết bàn', 'phiên âm'),
         ['GLOSSARY_LOCK_STABLE', 'BUDDHIST_TITLES', 'PLACE_TERMS']),
        (('tên', 'địa danh', 'chùa', 'núi', 'niên hiệu', 'bị đổi', 'sai tên'),
         ['CANONICAL_NAMES', 'HANVIET_PLACES', 'REIGN_ERA']),
        (('tục', 'thô', 'hiện đại', 'không trang', 'lạc giọng', 'văn phong'), ['TONE_OVERALL', 'LITERARY_PURITY', 'ACADEMIC_STYLE']),
        (('technical', 'kỹ thuật', 'lỗi hệ thống', 'không hiển thị', '500', 'timeout'), ['OUTPUT_FORMAT']),
    ]
    for words, codes in mappings:
        if any(w in text for w in words):
            suggestion.extend(c for c in codes if c not in suggestion)
    return suggestion




# T447 vòng 2 (QA lỗi 2) — source_type mà cổng translate_han_vi() KHÔNG xử lý đúng:
# 'dila_card' hash theo JSON toàn bộ source_data (sort_keys=True) nhưng source_text
# lưu trong translation_cache lại là JSON KHÁC (không sort_keys, bị cắt [:5000]) —
# gọi translate_han_vi() trên dòng này sẽ tính lại hash KHÔNG khớp hash đã lưu, nên
# không tìm thấy/invalidate đúng dòng cũ mà sinh dòng cache rác mới; prompt/format
# JSON (relations_vi...) của dila_card cũng không tương thích với prompt generic của
# cổng. Chặn rõ, không âm thầm tạo rác — Admin dùng nút "Dịch lại" riêng của tab đó
# (ví dụ /daoanh/api/person/<id>/dila_translate?force=1).
_T447_RETRANSLATE_UNSUPPORTED_SOURCE_TYPES = {'dila_card'}




# ===== INITIALIZE DIRECTORIES =====

# ============================================================
#  T75 — Web Enrichment Cache
#  Fetch mới từ Wikipedia/Wikidata, AI tóm tắt, lưu cache.
# ============================================================

def _t75_entity_info(entity_id, conn):
    """Trả về (entity_type, name_zh, name_en, name_vi_guess) từ places_dila hoặc people."""
    if entity_id.startswith('PL'):
        row = conn.execute(
            "SELECT id, name_zh, name_en FROM places_dila WHERE id=?", (entity_id,)
        ).fetchone()
        if not row:
            return None, None, None, None
        name_vi = _translate_zh_term(row['name_zh'] or '', conn) if row['name_zh'] else ''
        return 'place', row['name_zh'] or '', row['name_en'] or '', name_vi
    elif entity_id.startswith('A'):
        row = conn.execute(
            "SELECT id, name_zh FROM people WHERE id=?", (entity_id,)
        ).fetchone()
        if not row:
            return None, None, None, None
        name_vi = _translate_zh_term(row['name_zh'] or '', conn) if row['name_zh'] else ''
        return 'person', row['name_zh'] or '', '', name_vi
    return None, None, None, None




def _t75_search_wikipedia(name_zh, name_en='', lang='vi'):
    """Tìm kiếm Wikipedia theo tên, trả về (url, extract, title) hoặc (None,None,None)."""
    import urllib.parse, urllib.request, json as _json
    queries = []
    if lang == 'vi' and name_en:
        queries.append(('https://vi.wikipedia.org/w/api.php', name_en))
        if name_zh:
            queries.append(('https://zh.wikipedia.org/w/api.php', name_zh))
        queries.append(('https://en.wikipedia.org/w/api.php', name_en))
    elif lang == 'vi' and name_zh:
        queries.append(('https://vi.wikipedia.org/w/api.php', name_zh))
        queries.append(('https://zh.wikipedia.org/w/api.php', name_zh))
    elif lang == 'zh' and name_zh:
        queries.append(('https://zh.wikipedia.org/w/api.php', name_zh))

    for api_url, search_term in queries:
        try:
            params = urllib.parse.urlencode({
                'action': 'query',
                'prop': 'extracts|info',
                'exintro': '1',
                'explaintext': '1',
                'exsectionformat': 'plain',
                'exchars': '2000',
                'inprop': 'url',
                'titles': search_term,
                'redirects': '1',
                'format': 'json',
                'formatversion': '2',
            })
            req = urllib.request.Request(
                f'{api_url}?{params}',
                headers={'User-Agent': 'PhatPhapOnline/1.0 (phatphaponline.org; academic)'}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', [])
            if not pages:
                continue
            page = pages[0]
            if page.get('missing') or page.get('pageid', -1) < 0:
                continue
            extract = (page.get('extract') or '').strip()
            if len(extract) < 80:
                continue
            title = page.get('title', search_term)
            canonical_url = page.get('canonicalurl') or f'{api_url.replace("/w/api.php","")}/wiki/{urllib.parse.quote(title)}'
            if 'vi.wikipedia' in api_url:
                lang_label = 'Wikipedia Tiếng Việt'
            elif 'zh.wikipedia' in api_url:
                lang_label = 'Wikipedia Tiếng Trung'
            else:
                lang_label = 'Wikipedia (English)'
            return canonical_url, extract[:2000], title, lang_label
        except Exception as e:
            app.logger.debug(f"[T75] Wikipedia search error for {search_term}: {e}")
            continue
    return None, None, None, None




def _t75_summarize(name_vi, entity_type, raw_content, source_name, entity_id):
    """Dùng Gemini tóm tắt nội dung web thành tiếng Việt học thuật Phật học."""
    type_label = 'địa danh Phật giáo' if entity_type == 'place' else 'thiền sư / tăng nhân'
    prompt = f"""Bạn là học giả Phật học Việt Nam. Hãy tóm tắt thông tin sau về {type_label} "{name_vi}" (ID: {entity_id}) thành một đoạn văn tiếng Việt học thuật, súc tích (150-250 từ).

Nguồn: {source_name}
Nội dung gốc:
{raw_content}

YÊU CẦU:
- Viết bằng tiếng Việt học thuật, trang trọng
- Dùng âm Hán-Việt cho tên riêng (KHÔNG dùng pinyin)
- Nêu rõ: vị trí/thời kỳ, ý nghĩa lịch sử, liên quan Phật giáo
- Kết thúc bằng: "(Theo {source_name})"
- CHỈ tóm tắt thực tế, không suy đoán thêm

Viết trực tiếp đoạn tóm tắt, không cần tiêu đề:"""
    try:
        # T178 gap 13 — có retry/backoff 429; chưa có conn ở scope này ⇒ chỉ log, không persist
        text, model_id, _err = _t73_call_gemini(prompt, source_type='web_summary',
                                                source_text=raw_content)
        return text
    except Exception as e:
        app.logger.error(f"[T75] LLM error: {e}")
        return None




# ── T112 D-Feedback + T118 Audit/Citation + T119 Editor + T121 Geo ──
# Khối additive (bảng mới + endpoints): 0 ALTER bảng nền, 0 migration.
# Ráspec5 (2026-09-09) — data_gap_requests; Ráspec6 (2026-09-09) — T119 editor + feedback.

OPS_GAP_TABLE = 'data_gap_requests'


OPS_FEEDBACK_TABLE = 'user_feedback'



OPS_TABLES_DDL = [
    """
    CREATE TABLE IF NOT EXISTS data_gap_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,          -- person | place | work | entity
        entity_id TEXT NOT NULL,
        entity_name TEXT,
        gap_type TEXT NOT NULL,             -- thieu_noidung | thieu_nguon | loi_hien_thi | khac
        note_plain TEXT,
        source_hint TEXT,
        status TEXT DEFAULT 'new',          -- new | ack | closed
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(entity_type, entity_id, gap_type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT,
        entity_type TEXT,
        feedback_type TEXT NOT NULL,        -- sai_du_lieu | thieu_nguon | loi_hien_thi | khac
        note_plain TEXT NOT NULL,
        user_level TEXT,
        status TEXT DEFAULT 'new',          -- new | ack | closed
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
]



GEO_ENRICH_ALTERS = [
    ("enrich_status", "TEXT DEFAULT 'none'"),        # none | candidate | approved | rejected
    ("enrich_source_qid", "TEXT"),
    ("enrich_lat", "REAL"),
    ("enrich_lon", "REAL"),
    ("enrich_elevation_m", "INTEGER"),
    ("enrich_checked_at", "TEXT"),
    ("wikidata_lat", "REAL"),
    ("wikidata_lon", "REAL"),
    ("elevation_m", "INTEGER"),
    ("elevation_source", "TEXT"),
]




def _ensure_ops_tables():
    conn = get_db_connection()
    try:
        for ddl in OPS_TABLES_DDL:
            conn.execute(ddl)
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_data_gap_status ON data_gap_requests (status)"
            )
        except Exception:
            pass
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_feedback_status ON user_feedback (status)"
            )
        except Exception:
            pass
        for col, decl in GEO_ENRICH_ALTERS:
            try:
                conn.execute(
                    f"ALTER TABLE geo_cross_ref ADD COLUMN {col} {decl}"
                )
            except sqlite3.OperationalError:
                pass  # đã có cột
        conn.commit()
    finally:
        conn.close()




_ensure_ops_tables()




def _t112_record_gap(entity_type, entity_id, entity_name, gap_type, note, source_hint=''):
    """T112 D-Feedback: ghi 1 yêu cầu thiếu dữ liệu (tự động, dedupe UNIQUE)."""
    try:
        if not entity_id or not entity_name:
            return None
        conn = get_db_connection()
        try:
            conn.execute(
                """INSERT OR IGNORE INTO data_gap_requests
                   (entity_type, entity_id, entity_name, gap_type, note_plain, source_hint, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'new')""",
                (entity_type, entity_id, entity_name[:120], gap_type,
                 (note or '')[:500], (source_hint or '')[:200]),
            )
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception as e:
        app.logger.warning(f"_t112_record_gap error: {e}")
        return None




def _citation_lookup(entity_id):
    """T118 — trả về dict {title_vi, title_zh, dynasty, entity_type, source_name}."""
    entity_id = (entity_id or '').strip()
    if not entity_id:
        return None
    conn = get_db_connection()
    try:
        hub = conn.execute("SELECT entity_id, entity_type, canonical_label FROM entity_hub WHERE entity_id=?", (entity_id,)).fetchone() if entity_id.startswith('PL') else None
        if entity_id.startswith('PL'):
            row = conn.execute("SELECT name, name_zh, note FROM places_dila WHERE id=? LIMIT 1", (entity_id,)).fetchone()
            if row:
                return {"title_vi": row['name'], "title_zh": row['name_zh'],
                        "dynasty": None, "entity_type": 'place', "source_name": 'DILA Place Catalog'}
            hub = conn.execute("SELECT entity_id, entity_type, canonical_label FROM entity_hub WHERE entity_id=?", (entity_id,)).fetchone()
        dr = conn.execute("SELECT id, name_vi, name_zh, dynasty FROM dila_reference WHERE id=? LIMIT 1", (entity_id,)).fetchone()
        if dr:
            return {"title_vi": dr['name_vi'] or dr['name_zh'], "title_zh": dr['name_zh'],
                    "dynasty": dr['dynasty'], "entity_type": 'person', "source_name": 'DILA Reference'}
        pe = conn.execute("SELECT id, name_vi, name_zh, dynasty FROM people WHERE id=? LIMIT 1", (entity_id,)).fetchone()
        if pe:
            return {"title_vi": pe['name_vi'] or pe['name_zh'], "title_zh": pe['name_zh'],
                    "dynasty": pe['dynasty'], "entity_type": 'person', "source_name": 'People'}
        if hub:
            return {"title_vi": hub['canonical_label'] or entity_id, "title_zh": None,
                    "dynasty": None, "entity_type": hub['entity_type'] or 'entity',
                    "source_name": 'Entity Hub'}
        return {"title_vi": entity_id, "title_zh": None, "dynasty": None,
                "entity_type": 'entity', "source_name": 'raw ID'}
    finally:
        conn.close()




def _audit_ref_lookup(audit_id):
    """T118 đợt 2 — tra en_audit_log theo audit_id dạng `en-<log_id>`.
    Trả dict {action, editor, authority_rank, verification_status, evidence_sources, created_at}
    hoặc None nếu không khớp (đầu ra trung thực — export vẫn chạy, signature = hash entity_id)."""
    if not audit_id or not str(audit_id).startswith('en-'):
        return None
    try:
        lid = int(str(audit_id).split('-', 1)[1])
    except ValueError:
        return None
    conn = get_db_connection()
    try:
        r = conn.execute(
            "SELECT log_id, entity_ref, action, evidence_sources, authority_rank, editor, "
            "       verification_status, created_at "
            "FROM en_audit_log WHERE log_id=? LIMIT 1", (lid,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()




# ── T120 Unified Lookup (5-layer fallback, reuse tables) ────────────
# Batch E1 (2026-09-10, Lee phê chuẩn) — additive read-only endpoint.
# 0 ALTER bảng nền, 0 migration, 0 network tại thời điểm gọi (chỉ đọc cache).
# Layers: DILA core → Wikidata ref (geo_cross_ref) → Wikipedia cache
#         (place_wiki_snapshots) → Web enrichment (web_enrichment_cache) → name variant.
# Confidence tích lũy theo layer có dữ liệu; sources_used liệt kê layer thực sự khớp.
# T120 Phase A (2026-09-10) — live Wikidata query, HITL-safe (read-only, không ghi DB).

_T120_WD_HEADERS = {'User-Agent': 'DaoAnhT120Lookup/1.0 (Buddhist Geography; +https://phatphaponline.org/daoanh/) python-requests'}



def _t120_query_wikidata(qid, timeout=8):
    """Phase A — live Wikidata wbgetentities. Read-only, returns dict or None.
    HITL: trả data candidate, KHÔNG ghi geo_cross_ref/place_wiki_snapshots — admin approve sau.
    Props: P625 (GPS) · P2044 (elevation) · sitelinks (wiki vi/zh/en urls)."""
    if not qid or not str(qid).startswith('Q'):
        return None
    try:
        r = requests.get(
            'https://www.wikidata.org/w/api.php',
            params={'action': 'wbgetentities', 'ids': qid,
                    'props': 'labels|claims|sitelinks',
                    'languages': 'vi|zh|en', 'format': 'json'},
            headers=_T120_WD_HEADERS, timeout=timeout)
        r.raise_for_status()
        ent = r.json().get('entities', {}).get(qid, {})
        if not ent or 'labels' not in ent:
            return None

        def _lbl(lang): return ent.get('labels', {}).get(lang, {}).get('value')

        # P625 — {latitude, longitude, altitude}
        lat, lon, elev = None, None, None
        p625 = (ent.get('claims', {}).get('P625', [{}]) or [{}])[0]
        if p625:
            try:
                mv = p625['mainsnak']['datavalue']['value']
                lat = mv.get('latitude')
                lon = mv.get('longitude')
                alt = mv.get('altitude')
                if alt: elev = int(float(alt))
            except (KeyError, TypeError): pass

        # P2044 — elevation (integer, meters)
        if elev is None:
            p2044 = (ent.get('claims', {}).get('P2044', [{}]) or [{}])[0]
            try:
                elev = int(p2044['mainsnak']['datavalue']['value']['amount'])
            except (KeyError, TypeError, ValueError): pass

        # Sitelinks → Wikipedia URLs (useful for cross-ref and UI)
        sitelinks = ent.get('sitelinks', {})
        wikis = {}
        for lang in ('vi', 'zh', 'en'):
            slug = sitelinks.get(f'{lang}wiki', {}).get('title')
            if slug:
                wikis[f'wiki_{lang}'] = {
                    'title': slug,
                    'url': f'https://{lang}.wikipedia.org/wiki/{slug.replace(" ", "_")}'}

        return {
            'qid': qid,
            'label_vi': _lbl('vi'),
            'label_zh': _lbl('zh'),
            'label_en': _lbl('en'),
            'lat': lat, 'lon': lon,
            'elevation_m': elev,
            **wikis,
        }
    except Exception:
        return None




# ============================================================
#  T95 Phase C — CBETA Translation Jobs (batch Groq worker)
#  POST tạo job → thread nền worker_run; progress/jobs đọc từ DB.
#  CLI tương đương: scripts/cbeta_translate_worker.py run --job <id>
# ============================================================

def _t95_worker():
    import importlib
    return importlib.import_module('scripts.cbeta_translate_worker')




# ============================================================
#  T95 Phase D — Đọc UI: units của 1 passage (CBETA) + coverage tác phẩm
#  Badge server-side (6 trạng thái theo task T95 §7):
#   reviewed / needs_review / in_progress / failed / missing / corrupt
# ============================================================

_T95_UNITS_SQL = """
SELECT tp.passage_id AS unit_id, tp.sequence_no, tp.original_zh AS han,
       IFNULL(tp.source_status,'ok') AS source_status,
       IFNULL(tp.loc_ref,'') AS loc_ref, IFNULL(tp.canonical_ref,'') AS canonical_ref,
       IFNULL(tp.juan,'') AS juan, IFNULL(tp.raw_zh_hash,'') AS raw_zh_hash,
       ts.translation_id, ts.translation_text, ts.quality_status, ts.revision_no, ts.provider,
       (SELECT COUNT(*) FROM passage_translation_alignment a
         WHERE a.passage_id = tp.passage_id AND a.translation_id = ts.translation_id) AS aligned_n,
       (SELECT COUNT(*) FROM passage_translation_alignment a
         WHERE a.passage_id = tp.passage_id AND a.translation_id = ts.translation_id
           AND a.alignment_type = 'manual_verified' AND a.review_status = 'verified') AS manual_verified_n,
       (SELECT COUNT(*) FROM translation_job_items ji
         WHERE ji.passage_id = tp.passage_id AND ji.status IN ('queued','running','processing')) AS in_progress,
       (SELECT COUNT(*) FROM translation_job_items ji
         WHERE ji.passage_id = tp.passage_id AND ji.status IN ('failed','error')) AS had_failure
FROM text_passages tp
LEFT JOIN translation_segments ts ON ts.translation_id = (
    SELECT t.translation_id FROM translation_segments t
    WHERE t.passage_id = tp.passage_id AND t.translation_status <> 'superseded'
    ORDER BY t.revision_no DESC LIMIT 1)
WHERE tp.work_id = ? AND tp.legacy_passage_id = ?
ORDER BY tp.sequence_no
"""




def _t95_badge(row):
    # Gán badge trạng thái cho 1 unit (6 trạng thái T95 §7)
    if row.get('source_status') != 'ok':
        row['badge'] = 'corrupt'
    elif row.get('translation_id'):
        row['badge'] = 'reviewed' if row.get('quality_status') in ('validated', 'reviewed') else 'needs_review'
    elif row.get('in_progress'):
        row['badge'] = 'in_progress'
    elif row.get('had_failure'):
        row['badge'] = 'failed'
    else:
        row['badge'] = 'missing'
    row['aligned'] = bool(row.get('aligned_n'))
    row['manual_verified'] = bool(row.get('manual_verified_n'))
    return row




def _t95_coverage(con, work_id):
    sql = """
    SELECT
      (SELECT COUNT(*) FROM text_passages WHERE work_id=?) AS total,
      (SELECT COUNT(*) FROM text_passages tp WHERE work_id=? AND tp.passage_id IN (
         SELECT t.passage_id FROM translation_segments t
         WHERE t.translation_status <> 'superseded'
           AND t.translation_status IN ('completed','needs_review','reviewed'))) AS translated,
      (SELECT COUNT(*) FROM translation_segments t
         WHERE t.translation_status <> 'superseded'
           AND t.quality_status IN ('validated','reviewed')
           AND t.passage_id IN (SELECT passage_id FROM text_passages WHERE work_id=?)) AS reviewed,
      (SELECT COUNT(*) FROM translation_segments t
         WHERE t.translation_status <> 'superseded'
           AND (t.quality_status IS NULL OR t.quality_status='')
           AND t.passage_id IN (SELECT passage_id FROM text_passages WHERE work_id=?)) AS quality_unknown,
      (SELECT COUNT(*) FROM text_passages tp WHERE work_id=?
         AND (tp.source_status IS NULL OR tp.source_status<>'ok')) AS corrupt,
      (SELECT COUNT(*) FROM translation_job_items ji
         WHERE ji.status IN ('queued','running','processing')
           AND ji.passage_id IN (SELECT passage_id FROM text_passages WHERE work_id=?)) AS in_progress,
      (SELECT COUNT(*) FROM translation_job_items ji
         WHERE ji.status IN ('failed','error')
           AND ji.passage_id IN (SELECT passage_id FROM text_passages WHERE work_id=?)) AS failed
    """
    d = dict(con.execute(sql, (work_id,) * 7).fetchone())
    d['missing'] = max(d['total'] - d['translated'] - d['corrupt'], 0)
    return d




# ============================================================
#  T95 Phase E — Export bản dịch tích lũy (streaming JSON, Zero-RAM)
#  Chỉ gọi "Bản dịch hoàn chỉnh" khi 100% passage active có validated/reviewed
#  + không corrupt + không missing + không in_progress + không failed.
# ============================================================

_T95_EXPORT_UNITS_SQL = """
SELECT tp.sequence_no, tp.passage_id, IFNULL(tp.loc_ref,'') AS loc_ref, tp.original_zh AS han,
       ts.translation_text AS vi, ts.quality_status, ts.revision_no,
       IFNULL(tp.source_status,'ok') AS source_status,
       (SELECT COUNT(*) FROM translation_job_items ji
         WHERE ji.passage_id = tp.passage_id AND ji.status IN ('queued','running','processing')) AS in_progress,
       (SELECT COUNT(*) FROM translation_job_items ji
         WHERE ji.passage_id = tp.passage_id AND ji.status IN ('failed','error')) AS had_failed,
       (SELECT COUNT(*) FROM passage_translation_alignment a
         WHERE a.passage_id = tp.passage_id AND a.translation_id = ts.translation_id) AS aligned_n
FROM text_passages tp
LEFT JOIN translation_segments ts ON ts.translation_id = (
    SELECT t.translation_id FROM translation_segments t
    WHERE t.passage_id = tp.passage_id AND t.translation_status <> 'superseded'
    ORDER BY t.revision_no DESC LIMIT 1)
WHERE tp.work_id = ?
ORDER BY tp.sequence_no
"""




def _t95_export_status(row):
    # Trạng thái xuất: corrupt / reviewed / draft / in_progress / failed / missing
    if row.get('source_status') != 'ok':
        return 'corrupt'
    if row.get('vi'):
        return 'reviewed' if row.get('quality_status') in ('validated', 'reviewed') else 'draft'
    if row.get('in_progress'):
        return 'in_progress'
    if row.get('had_failed'):
        return 'failed'
    return 'missing'




def _t95_export_iter(con, work_id, cov):
    # Stream JSON (Zero-RAM theo AGENTS.md) — không build toàn bộ list trong RAM.
    def cat_title(con, work_id):
        try:
            r = con.execute("SELECT title_vi FROM cbeta_catalog_vn WHERE sigla=? LIMIT 1", (work_id,)).fetchone()
            if r and r['title_vi']:
                return r['title_vi']
        except Exception:
            pass
        return ''

    title = cat_title(con, work_id)
    complete = (cov.get('corrupt', 0) == 0 and cov.get('missing', 0) == 0
                and cov.get('in_progress', 0) == 0 and cov.get('failed', 0) == 0
                and cov.get('reviewed', 0) == cov.get('translated', 0)
                and cov.get('translated', 0) == cov.get('total', 0))

    head = {'ok': True, 'work_id': work_id, 'title': title,
            'completed': complete,
            'label': ('Bản dịch hoàn chỉnh' if complete else
                      f"Bản dịch tích lũy — {cov.get('translated', 0)}/{cov.get('total', 0)} đoạn"),
            'counts': cov, 'generated_at': datetime.now().isoformat()}
    yield '{' + '"meta":' + json.dumps(head, ensure_ascii=False, separators=(',', ':')) + ',"passages":['
    first = True
    for row in con.execute(_T95_EXPORT_UNITS_SQL, (work_id,)):
        r = dict(row)
        st = _t95_export_status(r)
        out = {
            'seq': r['sequence_no'],
            'passage_id': r['passage_id'],
            'loc_ref': r['loc_ref'],
            'han': r['han'],
            'vi': r['vi'] if st in ('reviewed', 'draft') else None,
            'status': st,
            'quality': r['quality_status'] if st in ('reviewed', 'draft') else None,
            'revision': r['revision_no'] if st in ('reviewed', 'draft') else None,
            'aligned': bool(r.get('aligned_n')) and st in ('reviewed', 'draft'),
        }
        if not first:
            yield ','
        first = False
        yield json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    yield ']}'




def _t95_export_markdown(con, work_id, cov):
    # Markdown: tiêu đề/tác phẩm, nguồn CBETA, passage ID/canonical, Hán, Việt, trạng thái, phiên bản/ngày.
    title = ''
    try:
        r = con.execute("SELECT title_vi FROM cbeta_catalog_vn WHERE sigla=? LIMIT 1", (work_id,)).fetchone()
        if r and r['title_vi']:
            title = r['title_vi']
    except Exception:
        pass
    complete = (cov.get('corrupt', 0) == 0 and cov.get('missing', 0) == 0
                and cov.get('in_progress', 0) == 0 and cov.get('failed', 0) == 0
                and cov.get('reviewed', 0) == cov.get('translated', 0)
                and cov.get('translated', 0) == cov.get('total', 0))
    lines = []
    lines.append(f"# {'Bản dịch hoàn chỉnh' if complete else 'Bản dịch tích lũy — ' + str(cov.get('translated', 0)) + '/' + str(cov.get('total', 0)) + ' đoạn'}")
    lines.append('')
    lines.append(f"- **Tác phẩm:** {title or work_id} ({work_id})")
    lines.append(f"- **Nguồn CBETA:** https://cbetaonline.dila.edu.tw/{work_id}")
    lines.append(f"- **Tiến độ:** translated={cov.get('translated', 0)} total={cov.get('total', 0)} reviewed={cov.get('reviewed', 0)} missing={cov.get('missing', 0)} corrupt={cov.get('corrupt', 0)} in_progress={cov.get('in_progress', 0)} failed={cov.get('failed', 0)}")
    lines.append('')
    lines.append('| Seq | Passage ID | Canonical | Hán | Việt | Trạng thái | Phiên bản |')
    lines.append('|-----|------------|-----------|-----|------|------------|-----------|')
    for row in con.execute(_T95_EXPORT_UNITS_SQL, (work_id,)):
        r = dict(row)
        st = _t95_export_status(r)
        vi = (r.get('vi') or '—') if st in ('reviewed', 'draft') else '(chưa có)'
        if st == 'corrupt':
            vi = '(nguồn lỗi)'
        rev = r.get('revision_no') if st in ('reviewed', 'draft') else '—'
        han_esc = (r['han'] or '').replace('|', '\\|').replace('\n', ' ')
        vi_esc = vi.replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {r['sequence_no']} | {r['passage_id']} | {r['loc_ref']} | {han_esc} | {vi_esc} | {st} | {rev} |")
    md = '\n'.join(lines) + '\n'
    resp = Response(md, mimetype='text/markdown; charset=utf-8')
    if request.args.get('download'):
        resp.headers['Content-Disposition'] = f"attachment; filename={work_id}_translation_export.md"
    return resp




# ============================================================
#  T95 Phase E — Admin translation-job monitor (admin only)
#  Xem jobs + items + raw audit; resume (requeue failed) / cancel.
# ============================================================

_T95_JOBS_LIST_SQL = """
SELECT j.job_id, j.work_id, j.status, j.requested_scope,
       IFNULL(j.requested_by_user_id,'admin') AS created_by,
       j.total_passages, j.completed_passages, j.failed_passages,
       j.created_at, j.started_at, j.finished_at, j.last_error,
       (SELECT COUNT(*) FROM translation_job_items i WHERE i.job_id = j.job_id AND i.status = 'completed') AS done_items,
       (SELECT COUNT(*) FROM translation_job_items i WHERE i.job_id = j.job_id) AS item_total,
       (SELECT COUNT(*) FROM translation_job_items i WHERE i.job_id = j.job_id AND i.status IN ('queued','running')) AS active_items,
       (SELECT COUNT(*) FROM translation_job_items i WHERE i.job_id = j.job_id AND i.status = 'failed') AS failed_items,
       (SELECT COALESCE(SUM(i.attempt_count),0) FROM translation_job_items i WHERE i.job_id = j.job_id) AS total_attempts,
       (SELECT i.error_message FROM translation_job_items i
         WHERE i.job_id = j.job_id AND i.status = 'failed' ORDER BY i.completed_at DESC NULLS LAST, i.created_at DESC LIMIT 1) AS sample_error
FROM translation_jobs j
ORDER BY j.created_at DESC
"""




def _t95_raw_dir(job_id):
    return os.path.join(DATA_DIR, 'raw_responses', job_id)




# ============================================================
#  T126 — Q&A toàn hệ thống (Groq LLM + retrieval)
#  POST /daoanh/api/daitang/qa  {"question": "..."}
#
#  Luồng:
#    1) Tách keyword tiếng Việt + Hán trực tiếp từ câu hỏi.
#    2) Mở rộng keyword tiếng Việt → Hán qua glossary_vi reverse lookup.
#    3) Retrieval trên toàn hệ thống: passage (+ cbeta_catalog_vn metadata),
#       people (name_vi/bio_vi/name_zh) và places (name/name_en).
#    4) Nếu có đủ evidence → Groq sinh câu trả lời tiếng Việt kèm trích dẫn [1..n].
#       Groq fail → trả evidence dạng retrieval_only (không 500).
#  Response: {ok, mode: 'llm'|'retrieval_only', answer?, citations?,
#             evidence[], entities[], latency_ms}
# ============================================================

_T126_STOPWORDS = {
    'ai', 'la', 'cua', 'nao', 'dau', 'o', 'trong', 'va', 'mot', 'nhung',
    'ban', 'duoc', 'khong', 'vi', 'lam', 'sao', 'the', 'cho', 've', 'gi',
    'la', 'thi', 'co', 'hay', 'nen', 'roi', 'ma', 'khi', 'tu', 'den', 'ra',
    'lam', 'nay', 'do', 'day', 'dung', 'thuong', 'vua', 'cung', 'nen',
}




def _t126_has_han(s):
    """Câu hỏi có chứa ký tự Hán trực tiếp?"""
    return any('\u4e00' <= ch <= '\u9fff' for ch in s)




def _t126_tokens(question):
    """Tách keyword từ câu hỏi. Trả (vn_norm, vn_orig, han).
    vn_norm: bỏ dấu → dùng cho GLOB entity match.
    vn_orig: giữ dấu → dùng cho passage LIKE tiếng Việt.
    han: chính câu hỏi nếu có Hán trực tiếp."""
    q = normalize_text(question)
    vn_norm = [w for w in re.split(r'[^a-z0-9]+', q)
               if len(w) >= 2 and w not in _T126_STOPWORDS]
    vn_orig = []
    for tok in re.split(r'\s+', question.strip()):
        t = tok.strip('.,;:!?()"“”‘’[]')
        if not t:
            continue
        tn = normalize_text(t)
        if tn in vn_norm and tn not in {normalize_text(x) for x in vn_orig}:
            vn_orig.append(t)
        if len(vn_orig) >= 6:
            break
    han = []
    if _t126_has_han(question):
        for seg in re.split(r'[^\u4e00-\u9fff]+', question):
            if seg:
                han.append(seg)
    return vn_norm, vn_orig, han




def _t126_vn_to_han(conn, vn_tokens, max_total=12):
    """Mở rộng keyword tiếng Việt → thuật ngữ Hán qua glossary_vi
    (reverse lookup: term_vi LIKE token → glossary_term.term language='zho')."""
    han = []
    seen = set()
    for tok in vn_tokens[:6]:
        rows = conn.execute(
            """SELECT DISTINCT g.term FROM glossary_term g
               JOIN glossary_vi v ON v.glossary_id = g.id
               WHERE g.language='zho'
                 AND (v.term_vi = ? OR v.term_vi LIKE ?)
                 AND length(g.term) <= 12
               LIMIT 8""",
            (tok, tok + '%')
        ).fetchall()
        for r in rows:
            t = r['term']
            if t not in seen and len(t) <= 12:
                seen.add(t)
                han.append(t)
        if len(han) >= max_total:
            break
    return han[:max_total]




_GLOB_CLASS = {
    'a': '[aAáàảãạăắằẳẵặâấầẩẫậ]', 'ă': '[ăĂắằẳẵặ]', 'â': '[âÂấầẩẫậ]',
    'e': '[eEéèẻẽẹêếềểễệ]', 'ê': '[êÊếềểễệ]',
    'i': '[iIíìỉĩị]', 'o': '[oOóòỏõọôốồổỗộơớờởỡợ]',
    'ô': '[ôÔốồổỗộ]', 'ơ': '[ơƠớờởỡợ]',
    'u': '[uUúùủũụưứừửữự]', 'ư': '[ưƯứừửữự]', 'y': '[yYýỳỷỹỵ]',
    'd': '[dDđĐ]', 'đ': '[đĐ]', 'b': '[bB]', 'c': '[cC]', 'g': '[gG]',
    'h': '[hH]', 'k': '[kK]', 'l': '[lL]', 'm': '[mM]', 'n': '[nN]',
    'p': '[pP]', 'q': '[qQ]', 'r': '[rR]', 's': '[sS]', 't': '[tT]',
    'v': '[vV]', 'x': '[xX]',
}




def _t126_glob_pattern(phrase):
    """Tạo GLOB pattern cho từ khóa tiếng Việt dấu-linh-hoạt: mỗi ký tự gốc
    (sau normalize) thành char-class bao gồm mọi biến thể dấu + hoa/thường.
    GLOB hỗ trợ [..] trong SQLite — LIKE thì không. Không dấu → vẫn match."""
    norm = normalize_text(phrase).replace(' ', '')
    out = '*'
    for ch in norm:
        if ch in _GLOB_CLASS:
            out += _GLOB_CLASS[ch]
        elif ch.isalnum():
            out += '[' + ch + ch.upper() + ']'
    return out + '*'




def _t126_entity_match(conn, vn_norm):
    """Tìm entity theo tên việt: địa danh (namevi_map_places) + nhân danh (people).
    Trả (entities, extra_han). Thử LẦN LƯỢT phrase 4→2 token; lấy kết quả từ
    longest-phrase đầu tiên có hit (tránh nhiễu tên ngắn)."""
    entities = []
    extra_han = []
    seen = set()
    if len(vn_norm) < 2:
        return entities, extra_han
    phrase = None
    found = False
    for n in range(min(4, len(vn_norm)), 1, -1):
        cand = ' '.join(vn_norm[:n])
        pat = _t126_glob_pattern(cand)
        hit = conn.execute(
            "SELECT 1 FROM namevi_map_places "
            "WHERE replace(name_vi,' ','') GLOB ? LIMIT 1",
            (pat,)
        ).fetchone() or conn.execute(
            "SELECT 1 FROM people "
            "WHERE replace(COALESCE(name_vi,''),' ','') GLOB ? LIMIT 1",
            (pat,)
        ).fetchone()
        if hit:
            phrase = cand
            pattern = pat
            found = True
            break
    if not found:
        return entities, extra_han

    # 1) Địa danh — namevi_map_places (118k rows), tên ngắn trước
    rows = conn.execute(
        """SELECT id, name_vi, name_zh, note_vi, gps_lat, gps_long,
                  district_vi, country_vi, replace(name_vi,' ','') AS nv
           FROM namevi_map_places
           WHERE nv GLOB ?
           ORDER BY length(nv) ASC LIMIT 10""",
        (pattern,)
    ).fetchall()
    for r in rows:
        key = ('place', r['id'])
        if key in seen:
            continue
        seen.add(key)
        entities.append({
            'type': 'place', 'id': r['id'],
            'name': r['name_vi'] or r['name_zh'] or '',
            'name_zh': r['name_zh'] or '',
            'district': r['district_vi'] or '', 'country': r['country_vi'] or '',
            'geo_lat': r['gps_lat'], 'geo_long': r['gps_long'],
            'snippet': (r['note_vi'] or '')[:420],
        })
        if r['name_zh'] and len(r['name_zh']) <= 12 and r['name_zh'] not in extra_han:
            extra_han.append(r['name_zh'])
    # 2) Nhân danh — people (48k, tên chuẩn)
    rows = conn.execute(
        """SELECT id, name_vi, name_zh, name_en, sect, dynasty, bio_vi, bio,
                  replace(COALESCE(name_vi,''),' ','') AS nv
           FROM people
           WHERE nv GLOB ?
           ORDER BY length(nv) ASC LIMIT 10""",
        (pattern,)
    ).fetchall()
    for r in rows:
        key = ('person', r['id'])
        if key in seen:
            continue
        seen.add(key)
        entities.append({
            'type': 'person', 'id': r['id'],
            'name': r['name_vi'] or r['name_zh'] or r['name_en'] or '',
            'name_zh': r['name_zh'] or '', 'sect': r['sect'] or '',
            'dynasty': r['dynasty'] or '',
            'snippet': (r['bio_vi'] or r['bio'] or '')[:420],
        })
        if r['name_zh'] and len(r['name_zh']) <= 12 and r['name_zh'] not in extra_han:
            extra_han.append(r['name_zh'])
    return entities[:6], extra_han[:8]




def _t126_retrieve(conn, question):
    """Retrieval toàn hệ thống. Trả về (evidence, entities).
    evidence: passage/danh mục kinh phù hợp (ưu tiên có bản dịch VN).
    entities: people/places khớp tên."""
    vn_norm, vn_orig, han = _t126_tokens(question)
    han = list(dict.fromkeys(han + _t126_vn_to_han(conn, vn_norm)))
    entities, extra_han = _t126_entity_match(conn, vn_norm)
    han = list(dict.fromkeys(han + extra_han))
    evidence = []
    seen_ids = set()

    # --- P1: ghép chữ Hán trong passage.raw_text / norm_text ---
    if han:
        # Term DÀI nhất (most-specific) trước — entity extra_han như 雁門關 (3 ký tự)
        # được thử trước term ngắn/chung 釋迦, tránh bị lấn trong OR+LIMIT.
        terms = sorted(set(han), key=lambda t: (len(t), han.index(t)), reverse=True)
        n_exact = 8
        matched = 0
        for term in terms:
            if matched >= n_exact:
                break
            rows = conn.execute(
                """SELECT p.passage_id, p.text_id, p.loc_ref, p.raw_text, p.vi_text,
                          p.translation_draft, c.title_vi, c.title_zh, c.dynasty_vi,
                          c.translator_vi, c.sigla, c.q_number
                   FROM passage p
                   LEFT JOIN cbeta_catalog_vn c ON p.text_id = c.sigla
                   WHERE p.raw_text LIKE ? ESCAPE '\\'
                      OR p.norm_text LIKE ? ESCAPE '\\'
                   ORDER BY (CASE WHEN p.vi_text IS NOT NULL AND length(p.vi_text)>0
                                  THEN 1 ELSE 0 END) DESC
                   LIMIT 4""",
                ('%' + term + '%', '%' + term + '%')
            ).fetchall()
            for r in rows:
                if r['passage_id'] in seen_ids:
                    continue
                seen_ids.add(r['passage_id'])
                matched += 1
                snippet = (r['vi_text'] or r['translation_draft'] or r['raw_text'] or '')[:420]
                evidence.append({
                    'type': 'passage', 'passage_id': r['passage_id'],
                    'text_id': r['text_id'], 'loc_ref': r['loc_ref'],
                    'title': (r['title_vi'] or r['title_zh'] or r['sigla'] or r['text_id'] or ''),
                    'sigla': r['sigla'] or r['text_id'] or '',
                    'dynasty': r['dynasty_vi'] or '', 'translator': r['translator_vi'] or '',
                    'q_number': r['q_number'] or '', 'snippet': snippet,
                })
                if matched >= n_exact:
                    break

    # --- P2: khớp phrase tiếng Việt (giữ dấu) trong passage dịch ---
    if vn_orig and not evidence:
        # Full-phrase (có dấu) chính xác; lower() 2 vế — SQLite LIKE case-sensitive ngoài ASCII
        pattern = ' '.join(vn_orig)
        causes = ["lower(p.vi_text) LIKE ? ESCAPE '\\'",
                  "lower(p.translation_draft) LIKE ? ESCAPE '\\'"]
        params = ['%' + pattern.lower() + '%'] * 2
        how = " OR ".join(causes)
        rows = conn.execute(
            f"""SELECT p.passage_id, p.text_id, p.loc_ref, p.raw_text, p.vi_text,
                       c.title_vi, c.title_zh, c.dynasty_vi, c.translator_vi,
                       c.sigla, c.q_number
                FROM passage p
                LEFT JOIN cbeta_catalog_vn c ON p.text_id = c.sigla
                WHERE {how}
                ORDER BY (CASE WHEN p.vi_text IS NOT NULL AND length(p.vi_text)>0 THEN 1 ELSE 0 END) DESC
                LIMIT 8""",
            params
        ).fetchall()
        for r in rows:
            if r['passage_id'] in seen_ids:
                continue
            seen_ids.add(r['passage_id'])
            evidence.append({
                'type': 'passage', 'passage_id': r['passage_id'],
                'text_id': r['text_id'], 'loc_ref': r['loc_ref'],
                'title': (r['title_vi'] or r['title_zh'] or r['sigla'] or r['text_id'] or ''),
                'sigla': r['sigla'] or r['text_id'] or '',
                'dynasty': r['dynasty_vi'] or '', 'translator': r['translator_vi'] or '',
                'q_number': r['q_number'] or '', 'snippet': (r['vi_text'] or '')[:420],
            })

    return evidence[:6], entities[:6]




def _t126_build_qa_prompt(question, evidence, entities, lock):
    """Xây prompt Groq: Style Constitution + evidence → câu trả lời tiếng Việt
    có trích dẫn [1..n]. Chỉ dựa vào tư liệu cung cấp, không bịa."""
    rule_block = "\n".join(f"{i+1}. [{r['rule_type'].upper()}] {r['rule_text']}"
                           for i, r in enumerate(lock['rules'][:12]))
    body = []
    for i, e in enumerate(evidence, 1):
        loc = (e.get('sigla') or '') + (f" · {e['loc_ref']}" if e.get('loc_ref') else '')
        body.append(f"[{i}] ({e.get('type','passage')}) {e.get('title','')} — {loc}\n{e.get('snippet','')}")
    for j, en in enumerate(entities, len(evidence) + 1):
        body.append(f"[{j}] ({en.get('type','')}) {en.get('name','')}"
                    + (f" ({en.get('name_zh','')})" if en.get('name_zh') else "")
                    + (f" — {en.get('dynasty','')}" if en.get('dynasty') else "")
                    + f"\n{en.get('snippet','')}")
    return (
        "Bạn là trợ lý tra cứu Hệ Thống Đại Tạng Kinh Việt Nam. "
        "Trả lời câu hỏi của người dùng BẰNG TIẾNG VIỆT dựa DUY NHẤT trên các tư liệu "
        "trích dẫn bên dưới (có đánh dấu [1], [2], ...). KHÔNG thêm thông tin ngoài tư liệu. "
        "Nếu tư liệu không đủ → nói rõ là chưa đủ để trả lời. "
        "Kèm trích dẫn nguồn bằng [số] ngay sau mỗi luận điểm.\n\n"
        f"=== QUY TẮC THUẬT NGỮ (Style Constitution) ===\n{rule_block}\n\n"
        f"=== CÂU HỎI ===\n{question}\n\n"
        f"=== TƯ LIỆU LIÊN QUAN ===\n" + "\n\n".join(body) + "\n\n"
        "=== TRẢ LỜI TIẾNG VIỆT ==="
    )




def _t126_call_groq(prompt):
    """Gọi Groq QA. Trả về (text, model, error) — error None=ok."""
    cfg = _llm_config_read()
    key = cfg.get('groq_key') or GROQ_KEY
    model = cfg.get('groq_model') or GROQ_MODEL
    if not key:
        return None, model, 'key_error'
    try:
        resp = requests.post(GROQ_URL,
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.2, 'max_tokens': 1024},
            timeout=30)
        if resp.status_code in (401, 403, 429):
            return None, None, 'key_error' if resp.status_code in (401, 403) else 'rate_limit'
        data = resp.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip(), model, None
        return None, model, 'api_error'
    except Exception as e:
        app.logger.warning(f"[T126] Groq error: {e}")
        return None, None, 'api_error'



    # Bind 127.0.0.1 — chỉ nginx/gateway trên cùng máy mới proxy tới được, không expose ra ngoài

# +{+ T130+T131 ADDITIVE BUILD 2026-09-18 — Lee Option A. 0 ALTER/0 DROP/0 DELETE. +}+
# ===================== T130: PRIMARY CHAIN + DEEP LINK ?expand= =====================
def _t130_lineage_edge_assertions_table(conn):
    """Introspect: trả tuple (cols, col_ok) cho bảng lineage_edge_assertions nếu tồn tại."""
    try:
        rows = conn.execute("PRAGMA table_info(lineage_edge_assertions)").fetchall()
        cols = [r[1] for r in rows]
    except Exception:
        return [], False
    return cols, bool(cols)



def _t130_expand_primary_chain(monk_id, direction="down", conn=None, limit=1, version="1"):
    """
    Tra truc he (primary chain) theo authority_score DESC + verified=1.
    CHI SELECT + aggregate = 0 ALTER. Moi dot 1 tong = limit huu hanh (lazy).
    
    Args:
        monk_id: ID tu si goc
        direction: "up" (thay) hoac "down" (tro)
        conn: DB connection (optional)
        limit: Mac dinh 1 (exactly ONE generation per click)
        version: Cache version for cache_key = f"{monk_id}|{version}"
    
    Returns:
        {
            "monk_id": str,
            "ecode": str|None,
            "chain": [{"id": str, "teacher": str, "authority": int, "verified": int, "sibling_count": int, "dir": str}],
            "direction": str,
            "cache_key": str,           # f"{monk_id}|{version}"
            "has_more_down": bool       # True neu con chau chua load
        }
    """
    chain = []
    cache_key = f"{monk_id}|{version}"
    has_more_down = False
    
    try:
        close_it = conn is None
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
        
        cols, ok = _t130_lineage_edge_assertions_table(conn)
        if not ok:
            if close_it: conn.close()
            return {
                "monk_id": monk_id, 
                "ecode": "no_lineage_table", 
                "chain": [],
                "direction": direction,
                "cache_key": cache_key,
                "has_more_down": False
            }
        
        # primary: student_id->teacher_id theo authority_score desc, verified=1 (SSOT authority)
        teacher_col = "teacher_id" if "teacher_id" in cols else ("parent_id" if "parent_id" in cols else None)
        student_col = "student_id" if "student_id" in cols else ("child_id" if "child_id" in cols else None)
        auth_col = "authority_score" if "authority_score" in cols else None
        ver_col = "verified" if "verified" in cols else None
        
        if not (teacher_col and student_col):
            if close_it: conn.close()
            return {
                "monk_id": monk_id, 
                "ecode": "no_cols", 
                "chain": [],
                "direction": direction,
                "cache_key": cache_key,
                "has_more_down": False
            }
        
        cur_id = monk_id
        seen = set()
        
        # deep link: expand huong up = truc he thay (primary); down = tro truc tiep
        for _ in range(limit):
            if cur_id in seen or not cur_id:
                break
            seen.add(cur_id)
            
            if direction == "up":
                q = "SELECT * FROM lineage_edge_assertions WHERE %s = ?" % student_col
                order_by = (auth_col + " DESC") if auth_col else "rowid"
                if ver_col:
                    q_where = " AND %s >= 1" % ver_col
                else:
                    q_where = ""
                row = conn.execute(q + q_where + " ORDER BY " + order_by + " LIMIT 1", (cur_id,)).fetchone()
                if not row:
                    break
                keys = [d[0] for d in conn.execute("PRAGMA table_info(lineage_edge_assertions)").fetchall()]
                d = dict(zip(keys, row))
                cur_id = d.get(teacher_col)
                chain.append({
                    "id": d.get(student_col), "teacher": d.get(teacher_col),
                    "authority": d.get(auth_col), "verified": d.get(ver_col),
                    "dir": "up",
                })
            else:  # down
                q = "SELECT *, (SELECT COUNT(*) FROM lineage_edge_assertions s WHERE s.%s = lineage_edge_assertions.%s) AS sibling_count FROM lineage_edge_assertions WHERE %s = ?" % (teacher_col, teacher_col, teacher_col)
                order_by = (auth_col + " DESC") if auth_col else "rowid"
                if ver_col:
                    q_where = " AND %s >= 1" % ver_col
                else:
                    q_where = ""
                row = conn.execute(q + q_where + " ORDER BY " + order_by + " LIMIT 1", (cur_id,)).fetchone()
                if not row:
                    break
                keys = [x[0] for x in conn.execute("PRAGMA table_info(lineage_edge_assertions)").fetchall()] + ["sibling_count"]
                d = dict(zip(keys, row))
                cur_id = d.get(student_col)
                chain.append({
                    "id": d.get(student_col), "teacher": d.get(teacher_col),
                    "authority": d.get(auth_col), "verified": d.get(ver_col),
                    "sibling_count": d.get("sibling_count"), "dir": "down",
                })
        
        # Check has_more_down: if current node has children beyond what we returned
        if direction == "down" and cur_id:
            # Count total children of the last node
            cnt_q = "SELECT COUNT(*) FROM lineage_edge_assertions WHERE %s = ?" % teacher_col
            if ver_col:
                cnt_q += " AND %s >= 1" % ver_col
            total_children = conn.execute(cnt_q, (cur_id,)).fetchone()[0]
            has_more_down = total_children > len(chain)
        
        if close_it: conn.close()
        return {
            "monk_id": monk_id, 
            "ecode": None, 
            "chain": chain, 
            "direction": direction,
            "cache_key": cache_key,
            "has_more_down": has_more_down
        }
    except Exception as e:
        try:
            if "conn" in dir() and conn is not None: conn.close()
        except Exception: pass
        return {
            "monk_id": monk_id, 
            "ecode": str(e), 
            "chain": [],
            "direction": direction,
            "cache_key": cache_key,
            "has_more_down": False
        }




def _t130_build_full_direct_chain(focus_id, chain_id=None, pick_id=None):
    """
    Xay dung toan bo truc he tu goc (root) den la (leaf).
    Dung cho deep-link ?mode=lineage&focus=&chain=&pick=
    
    Args:
        focus_id: ID tu si focus (center)
        chain_id: ID chuoi truc he (optional)
        pick_id: ID nhanh duoc chon khi co branch (optional)
    
    Returns:
        {
            "nodes": [{"id": str, "name": str, "generation": int, "is_focus": bool, "is_pick": bool}],
            "edges": [{"source": str, "target": str, "direction": "up|down"}],
            "focus_id": str,
            "chain_id": str,
            "pick_id": str
        }
    """
    # TODO: Implement full chain walk - up to root, then down to leaf following pick_id
    # For now, return minimal structure
    return {
        "nodes": [{"id": focus_id, "generation": 0, "is_focus": True}],
        "edges": [],
        "focus_id": focus_id,
        "chain_id": chain_id,
        "pick_id": pick_id
    }




def _t131_gate_ops_enabled():
    """Gate usage_level/restrictions hiện có — trả dict; additive, không ghi."""
    # Trả về mô tả các op đang mở (public/read-only) — KHÔNG tạo DB.
    return {
        "CONTENT_READ": True,
        "METADATA_READ": True,
        "DERIVED_DATA": True,
        "EXPORT": False,  # đổi lên level_3 mới mở — mặc định chặt
    }



def _t131_registry_ssot_rows():
    """Registry SSOT 13→25: 12 nguồn phái thêm (INSERT OR IGNORE — introspect cột thật)."""
    adds = [
        ("CBETA", "Chinese Buddhist Electronic Text Association", "TW", "lvl2"),
        ("DILA", "Digital Library & Museum of Buddhist Works", "TW", "lvl2"),
        ("BDRC", "Buddhist Digital Resource Center", "US", "lvl2"),
        ("PTS", "Pali Text Society", "GB", "lvl2"),
        ("Dunhuang Academy", "Dunhuang Academy", "CN", "lvl2"),
        ("Treasury of Lives", "Treasury of Lives", "US", "lvl2"),
        ("Viet Phap Lan", "Việt Pháp Lan", "VN", "lvl2"),
        ("Phat Giao Nam Tong", "Phật Giáo Nam Tông", "VN", "lvl2"),
        ("Truyen Thua Viet", "Truyền Thừa Việt", "VN", "lvl2"),
        ("Thien Phai Truc Lam", "Thiền Phái Trúc Lâm", "VN", "lvl2"),
        ("Thien Phai Lam Te", "Thiền Phái Lâm Tế", "VN", "lvl2"),
        ("Lineage VN", "Tàng Kinh // Lineage VN", "VN", "lvl2"),
    ]
    added = 0
    try:
        # Tìm bảng registry/edge_assertions; nếu không có bảng nào → chỉ trả meta.
        conn = sqlite3.connect(DB_PATH)
        tabs = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        cand = None
        cand = "edge_assertions" if "edge_assertions" in tabs else ("lineage_edge_assertions" if "lineage_edge_assertions" in tabs else None)
        for name, full, cc, lvl in adds:
            conn.execute("INSERT OR IGNORE INTO %s (source_name, source_full, authority, region) VALUES (?, ?, ?, ?)" % cand,
                         (name, full, "verified-by-Lee", cc)) if cand else None
            added += 1
        conn.commit()
        conn.close()
    except Exception as e:
        added = 0
        e = str(e)
    return {"expected_total": 25, "adds": len(adds), "added": added, "note": "INSERT OR IGNORE, introspect"}



# Deep-link route đọc ?expand= (query string) + expand chain
def _t130_route_expand():
    from flask import request, jsonify
    expand_id = (request.args.get("expand") or "").strip()
    direction = (request.args.get("dir") or "down").strip()
    
    # ?expand=0 handling: return root-only chain (no expansion)
    if expand_id == "0":
        # Return minimal root structure
        return jsonify({
            "monk_id": "0",
            "ecode": None,
            "chain": [],
            "direction": direction,
            "cache_key": "0|1",
            "has_more_down": False
        })
    
    if not expand_id:
        return jsonify({"error": True, "msg": "?expand=<id> required"}), 400
    
    try:
        data = _t130_expand_primary_chain(expand_id, direction)
    except Exception as exc:
        return jsonify({"error": True, "msg": str(exc)}), 500
    
    data["gate"] = _t131_gate_ops_enabled()
    return jsonify(data)




def _t130_route_direct_chain():
    """?kind=lineage route - returns full direct chain for initial load / deep-link restore."""
    from flask import request, jsonify
    focus = (request.args.get("focus") or "").strip()
    chain_id = (request.args.get("chain") or "").strip()
    pick = (request.args.get("pick") or "").strip()
    
    if not focus:
        return jsonify({"error": True, "msg": "?focus=<id> required"}), 400
    
    try:
        data = _t130_build_full_direct_chain(focus, chain_id, pick)
    except Exception as exc:
        return jsonify({"error": True, "msg": str(exc)}), 500
    
    return jsonify(data)




def _t131_route_registry():
    from flask import jsonify
    return jsonify(_t131_registry_ssot_rows())



# ─────────────── T265 Lô D: CSV Import ───────────────

# ─────────────── /Monk TTL Admin ───────────────

# T226: ho so co chung cu, chi luu revision staging.
from api_ttl_profile_v2 import create_ttl_profile_blueprint



# T275: chuỗi neo số đời lấy từ TTL local (chỉ đọc, không ghi DB).
from api_ttl_anchor import create_ttl_anchor_blueprint

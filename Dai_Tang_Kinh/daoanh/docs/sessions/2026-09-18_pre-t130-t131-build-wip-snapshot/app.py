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

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_KEY', '')

# Hán-Việt normalization module (local, no API)
import sys as _sys
_scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
if _scripts_dir not in _sys.path:
    _sys.path.insert(0, _scripts_dir)
from hanviet_normalization import normalize_text as hanviet_normalize, load_glossary as hanviet_load_glossary
_hanviet_glossary = None

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
            'http://localhost:5001/api/login/check',
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

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# Compatibility alias – many routes still call get_db()
get_db = get_db_connection

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
        idx_count = conn.execute("SELECT COUNT(*) FROM places_search_fts_docsize").fetchone()[0]
        src_count = conn.execute("SELECT COUNT(*) FROM namevi_map_places").fetchone()[0]
        if force or idx_count < max(1, src_count // 100):
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
        doc_count = conn.execute("SELECT COUNT(*) FROM places_pending_fts").fetchone()[0]
        src_count = conn.execute("""
            SELECT COUNT(*) FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
            WHERE COALESCE(m.name_vi, p.name_vi) IS NOT NULL AND COALESCE(m.name_vi, p.name_vi) != ''
        """).fetchone()[0]
        if force or doc_count < max(1, src_count // 100):
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

@app.route('/daoanh/api/admin/missing-hanzi')
def api_admin_missing_hanzi():
    """
    GET /daoanh/api/admin/missing-hanzi?page=&limit=&search=
    T08 — paginated list of chars _ensure_vietnamese() could not translate.
    """
    try:
        page = max(int(request.args.get('page', 1)), 1)
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = (page - 1) * limit
        search = request.args.get('search', '').strip()
        conn = get_db_connection()
        try:
            _ensure_missing_hanzi_table()
            _ensure_custom_hanviet_override_table()
            where = "WHERE char LIKE ?" if search else ""
            params = [f'%{search}%'] if search else []
            total = conn.execute(f"SELECT COUNT(*) FROM missing_hanzi {where}", params).fetchone()[0]
            rows = conn.execute(f"""
                SELECT char, count, last_seen_at FROM missing_hanzi {where}
                ORDER BY count DESC, last_seen_at DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset]).fetchall()
            overrides = {r['char']: r['hanviet'] for r in conn.execute(
                "SELECT char, hanviet FROM custom_hanviet_override").fetchall()}
            items = []
            for r in rows:
                items.append({
                    "char": r['char'], "count": r['count'], "last_seen_at": r['last_seen_at'],
                    "override": overrides.get(r['char'])
                })
            return jsonify({"ok": True, "total": total, "page": page, "limit": limit, "items": items})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/missing-hanzi/override', methods=['POST'])
def api_admin_missing_hanzi_override():
    """
    POST /daoanh/api/admin/missing-hanzi/override  body: {char, hanviet}
    T08 — persist an admin-supplied Hán-Việt reading for a previously-missing
    character. Additive only (custom_hanviet_override table); does not touch
    hanviet_fallback or the CUSTOM_HANVIET literal in source. Takes effect
    immediately via _load_custom_hanviet_overrides() merging into the running
    in-memory dict, so the very next translation call uses it.
    """
    data = request.get_json(silent=True) or {}
    char = (data.get('char') or '').strip()
    hanviet = (data.get('hanviet') or '').strip()
    if not char or len(char) != 1:
        return jsonify({"ok": False, "error": "char must be exactly 1 character"}), 400
    if not hanviet:
        return jsonify({"ok": False, "error": "hanviet required"}), 400
    conn = get_db_connection()
    try:
        _ensure_custom_hanviet_override_table()
        conn.execute("""
            INSERT INTO custom_hanviet_override (char, hanviet, added_by, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(char) DO UPDATE SET
                hanviet = excluded.hanviet, created_at = CURRENT_TIMESTAMP
        """, (char, hanviet, request.remote_addr))
        conn.execute("DELETE FROM missing_hanzi WHERE char = ?", (char,))
        conn.commit()
        CUSTOM_HANVIET[char] = hanviet
        _MISSING_HANZI.pop(char, None)
        return jsonify({"ok": True, "char": char, "hanviet": hanviet})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

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

@app.route('/daoanh/api/admin/t221/approvals')
def api_t221_approvals():
    """GET — trạng thái 2 approval gates của T22.1"""
    data = _t221_load()
    # Thêm flag OpenCode dùng
    gates = data.get('gates', {})
    data['can_proceed_giai_doan_b'] = gates.get('giai_doan_a', {}).get('status') == 'approved'
    data['nlp_authorized'] = gates.get('final_signoff', {}).get('status') == 'approved'
    return jsonify(data)

@app.route('/daoanh/api/admin/t221/approve/<gate>', methods=['POST'])
def api_t221_approve(gate):
    """POST — Lee Tổng approve một gate (giai_doan_a | final_signoff)"""
    if gate not in ('giai_doan_a', 'final_signoff'):
        return jsonify({'ok': False, 'error': 'Invalid gate'}), 400
    body = request.get_json(silent=True) or {}
    data = _t221_load()
    from datetime import datetime
    data['gates'][gate].update({
        'status': 'approved',
        'approved_by': body.get('approved_by', 'Lee Tổng'),
        'approved_at': datetime.utcnow().isoformat() + 'Z',
        'note': body.get('note', ''),
        'rejected_by': None,
        'rejected_at': None,
    })
    if gate == 'final_signoff':
        data['nlp_authorized'] = True
    data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    _t221_save(data)
    return jsonify({'ok': True, 'gate': gate, 'status': 'approved'})

@app.route('/daoanh/api/admin/t221/reject/<gate>', methods=['POST'])
def api_t221_reject(gate):
    """POST — Lee Tổng reject một gate và yêu cầu làm lại"""
    if gate not in ('giai_doan_a', 'final_signoff'):
        return jsonify({'ok': False, 'error': 'Invalid gate'}), 400
    body = request.get_json(silent=True) or {}
    data = _t221_load()
    from datetime import datetime
    data['gates'][gate].update({
        'status': 'rejected',
        'rejected_by': body.get('rejected_by', 'Lee Tổng'),
        'rejected_at': datetime.utcnow().isoformat() + 'Z',
        'note': body.get('note', ''),
        'approved_by': None,
        'approved_at': None,
    })
    data['nlp_authorized'] = False
    data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    _t221_save(data)
    return jsonify({'ok': True, 'gate': gate, 'status': 'rejected'})
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

# Static file serving for admin frontend
@app.route('/daoanh/admin/')
def admin_index():
    return send_from_directory(ADMIN_DIR, 'placevn.html')

# Serve login page at /daoanh/login.html
@app.route('/daoanh/login.html')
def admin_login():
    return send_from_directory(ADMIN_DIR, 'login.html')

@app.route('/daoanh/admin/<path:path>')
def admin_static(path):
    return send_from_directory(ADMIN_DIR, path)

# Dashboard Process Tracker — phục vụ file tĩnh thư mục dashboard/ (mở trực tiếp từ app.py:5000)
DASHBOARD_DIR = os.path.join(BASE_DIR, 'dashboard')

@app.route('/dashboard/<path:path>')
@app.route('/daoanh/dashboard/<path:path>')
def dashboard_static(path):
    return send_from_directory(DASHBOARD_DIR, path)

@app.route('/dashboard/')
@app.route('/daoanh/dashboard/')
def dashboard_index():
    return send_from_directory(DASHBOARD_DIR, 'dashboard_process.html')

@app.route('/daoanh/admin/search_all/')
@app.route('/daoanh/admin/search_all.html')
def search_all_page():
    resp = make_response(send_from_directory(ADMIN_DIR, 'search_all.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/daoanh/admin/person.html')
def admin_person_page():
    resp = make_response(send_from_directory(ADMIN_DIR, 'person.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/daoanh/api/admin/places_missing_info')
def places_missing_info():
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        conn = get_db_connection()
        where = "WHERE (country IS NULL OR country = '') OR (district_raw IS NULL OR district_raw = '')"
        total = conn.execute(f"SELECT COUNT(*) FROM places_pending {where}").fetchone()[0]
        rows = conn.execute(f"""
            SELECT id, name_zh, name_vi, country, district_raw, province, gps_lat, gps_long
            FROM places_pending {where}
            ORDER BY id ASC NULLS LAST
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        conn.close()
        places = []
        for r in rows:
            p = dict(r)
            p['id'] = ensure_long_id(p['id'])
            places.append(p)
        return jsonify({"success": True, "total": total, "limit": limit, "offset": offset, "places": places})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/admin/place_update.html')
def admin_place_update():
    return send_from_directory(ADMIN_DIR, 'place_update.html')

# ---------------------------------------------------------------------------
# T78 — LEGAL/LICENSE FIREWALL: Legal Check + Add Source (admin no-code)
# ---------------------------------------------------------------------------
@app.route('/daoanh/api/admin/source-check', methods=['POST'])
def api_admin_source_check():
    """Nhận {name, repo_url} -> phân tích repo public -> report (LicenseGate + notes)."""
    try:
        body = request.get_json(silent=True) or {}
        name = (body.get('name') or '').strip()
        repo_url = (body.get('repo_url') or '').strip()
        if not name or not repo_url:
            return jsonify({'success': False, 'error': 'Thiếu tên nguồn hoặc Repo URL'}), 400
        from gate.analyzer import SourceAnalyzer
        rep = SourceAnalyzer(db_path=os.path.join(BASE_DIR, 'data', 'lineage.db')).analyze(name, repo_url)
        return jsonify({'success': True, 'report': rep})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/daoanh/api/admin/source-add', methods=['POST'])
def api_admin_source_add():
    """Admin xác nhận thêm source -> INSERT data_sources (legal_status=AUDITING, KHÔNG tự ACTIVE)
       + ghi en_audit_log. Nếu source đã tồn tại (source_code/name) -> cập nhật additive."""
    try:
        body = request.get_json(silent=True) or {}
        name = (body.get('name') or '').strip()
        repo_url = (body.get('repo_url') or '').strip()
        source_code = (body.get('source_code') or '').strip() or _make_source_code(name)
        notes = body.get('notes') or []
        integration_mode = (body.get('integration_mode') or 'REFERENCE_ONLY').upper()
        editor = (body.get('editor') or 'admin').strip()
        if not name or not repo_url:
            return jsonify({'success': False, 'error': 'Thiếu tên nguồn hoặc Repo URL'}), 400

        conn = get_db_connection()
        now = _iso_now()
        # source_code duy nhất: nếu đã có -> cập nhật additive, không nhân đôi
        existing = conn.execute(
            'SELECT source_id FROM data_sources WHERE source_code = ? OR source_name = ?',
            (source_code, name)).fetchone()
        if existing:
            sid = existing[0]
            conn.execute('UPDATE data_sources SET repository_url=?, legal_status=\'AUDITING\', '
                         'integration_mode=?, terms_status=\'under_review\', updated_at=? '
                         'WHERE source_id=?',
                         (repo_url, integration_mode, now, sid))
            action = 'source_update'
        else:
            cur = conn.execute(
                'INSERT INTO data_sources (source_code, source_name, source_type, '
                'repository_url, legal_status, data_license_status, integration_mode, '
                'terms_status, version_policy, license_verified, active, enabled, created_at, updated_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (source_code, name, 'crossref', repo_url, 'AUDITING', 'UNKNOWN',
                 integration_mode, 'under_review', 'not_available', 0, 1, 1, now, now))
            sid = cur.lastrowid
            action = 'source_add'
        # ghi audit log (additive; nếu bảng thiếu cột thì bỏ qua ghi chi tiết)
        conn.execute('INSERT INTO en_audit_log (entity_ref, action, editor, created_at) '
                     'VALUES (?,?,?,?)',
                     (f'source:{source_code}', action, editor, now))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'source_id': sid, 'source_code': source_code,
                        'legal_status': 'AUDITING', 'integration_mode': integration_mode,
                        'action': action})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _make_source_code(name):
    """Tạo source_code từ tên — fallback khi không có code rõ ràng."""
    s = re.sub(r'[^A-Za-z0-9]+', '_', unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()).strip('_').upper()
    return f'SRC_{s}' if s else 'SRC_NEW'


def _iso_now():
    from datetime import datetime as _dt
    return _dt.now().isoformat(timespec='seconds')

@app.route('/daoanh/api/admin/places_pending')
def places_pending():
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        search = (request.args.get('search', '') or '').strip()
        cate = (request.args.get('cate', 'admin_place') or '').strip()
        valid_cates = ('admin_place', 'temple_site', 'dynasty_region', 'mountain', 'river_lake', 'other')
        if cate not in valid_cates:
            cate = 'admin_place'

        cate_case = """
            CASE
                WHEN d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%' THEN 'temple_site'
                WHEN d.note_category LIKE '%山峰%' OR d.note_category LIKE '%山脈%' THEN 'mountain'
                WHEN d.note_category LIKE '%河流%' OR d.note_category LIKE '%湖泊%' OR d.note_category LIKE '%水系%' THEN 'river_lake'
                WHEN d.note_category LIKE '%人文地理區域%' THEN 'dynasty_region'
                WHEN d.note_category LIKE '%自然地理區域%' THEN 'other'
                ELSE 'admin_place'
            END
        """

        conn = get_db_connection()
        base_where = "p.id IS NOT NULL AND p.id != '' AND p.name_zh IS NOT NULL AND p.name_zh != '' AND p.note IS NOT NULL AND p.note != ''"
        params = [cate]
        if search:
            like = f'%{search}%'
            base_where += " AND (p.id LIKE ? OR p.name_zh LIKE ? OR p.name_vi LIKE ? OR m.name_vi LIKE ?)"
            params = [cate, like, like, like, like]

        if not search:
            # Đường nhanh: id theo cate đã cache → tra bằng index (không quét 176K dòng)
            cate_map = _build_cate_ids_map()
            cate_ids = cate_map["ids"].get(cate, [])
            cate_json = json.dumps(cate_ids)
            total = cate_map["distinct"].get(cate, 0)
            places = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       CASE WHEN p.note IS NOT NULL AND p.note != '' THEN 1 ELSE 0 END AS has_note
                FROM places_pending p
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE p.id IN (SELECT value FROM json_each(?))
                ORDER BY p.id ASC
                LIMIT ? OFFSET ?
            """, (cate_json, limit, offset)).fetchall()
        else:
            total = conn.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT p.id, {cate_case} AS cate_internal
                    FROM places_pending p
                    LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                    LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                    WHERE {base_where}
                )
                WHERE cate_internal = ?
            """, params).fetchone()[0]
            places = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       CASE WHEN p.note IS NOT NULL AND p.note != '' THEN 1 ELSE 0 END as has_note
                FROM places_pending p
                LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE {base_where} AND ({cate_case}) = ?
                ORDER BY p.id ASC NULLS LAST
                LIMIT ? OFFSET ?
            """, [*params, limit, offset]).fetchall()
        conn.close()
        places_list = []
        seen = set()
        for p in places:
            row = dict(p)
            lid = ensure_long_id(row['id'])
            if lid in seen:
                continue
            seen.add(lid)
            row['id'] = lid
            places_list.append(row)
        return jsonify({"success": True, "total": total, "limit": limit, "offset": offset, "places": places_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/places_error')
def places_error():
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT dila_id AS id, name_vi, name_zh, source, needs_review
            FROM namevi_map_places WHERE needs_review = 1
            LIMIT 500
        """).fetchall()
        seen = set(r['id'] for r in rows)
        results = [dict(r) for r in rows]
        if len(results) < 500:
            remaining = 500 - len(results)
            extra = conn.execute("""
                SELECT dila_id AS id, name_vi, name_zh, source, needs_review
                FROM namevi_map_places WHERE needs_review = 0
                LIMIT ?
            """, (remaining * 10,)).fetchall()
            for r in extra:
                if r['id'] in seen:
                    continue
                if re.search(r'[\u4e00-\u9fff]', str(r['name_vi'] or '')):
                    results.append(dict(r))
                    seen.add(r['id'])
                    if len(results) >= 500:
                        break
        conn.close()
        for r in results:
            r['id'] = ensure_long_id(r['id'])
        return jsonify({"success": True, "places": results, "total": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/ai_judge/<id>')
def ai_judge(id):
    try:
        conn = get_db_connection()
        digits = ''.join(filter(str.isdigit, id))
        full_id = f'PL{digits.zfill(12)}' if digits else id

        query = """
            SELECT p.id, p.name_zh, p.name_vi AS auto_name,
                   p.address AS pending_address, p.country AS raw_country,
                   p.gps_lat, p.gps_long, p.province, p.place_type,
                   p.raw_xml AS location_xml,
                    d.district AS raw_district, d.raw_xml,
                     d.note_category AS dila_note, d.listbibl,
                    d.geo_lat, d.geo_long, d.name_en, d.name_san, d.name_jpn, d.name_peo, d.name_other,
                   m.name_vi AS saved_name, m.source, m.needs_review,
                   m.note_vi, m.district_vi, m.country_vi,
                    m.gps_lat AS m_lat, m.gps_long AS m_long, m.vn_name_status,
                   pe.latin_source, pe.id AS person_id,
                   s.name AS source_name, s.license, s.usage_level
            FROM places_pending p
            LEFT JOIN places_dila d ON p.id = d.id
            LEFT JOIN namevi_map_places m ON p.id = m.dila_id
            LEFT JOIN dataset_sources s ON m.source_id = s.id
            LEFT JOIN people pe ON p.name_zh = pe.name_zh AND pe.name_zh != ''
            WHERE p.id = ?
        """
        row = conn.execute(query, (full_id,)).fetchone()
        if not row:
            row = conn.execute(query.replace('WHERE p.id = ?', 'WHERE p.id LIKE ? LIMIT 1'), (f'%{digits}%',)).fetchone()

        if not row:
            marcus = conn.execute(
                "SELECT node_id AS id, label_vi AS name_vi, label AS name_zh FROM marcus_reference WHERE node_id = ? OR node_id LIKE ? LIMIT 1",
                (full_id, f'%{digits}%')
            ).fetchone()
            if marcus:
                conn.close()
                return jsonify({"success": True, "marcus": True, "id": marcus['id'], "name_zh": marcus['name_zh'], "name_vi": marcus['name_vi'] or '', "verdict": marcus['name_vi'] or '', "source": "manual", "needs_review": 0, "note_vi": "", "lexicon_suggestions": {"default_suggestion": "", "candidates": []}, "raw_country": "", "raw_district": "", "pending_address": "", "province": "", "place_type": "", "gps_lat": "", "gps_long": "", "full_description": "", "raw_xml": "", "latin_source": None, "person_id": "", "provenance": [], "source_name": "Marcus_fojin", "license": "CC0", "usage_level": "GREEN", "district_vi": "", "country_vi": ""})
            conn.close()
            return jsonify({"success": False, "error": "Không tìm thấy ID", "message": "ID không tồn tại trên hệ thống"}), 404

        # Lexicon suggestions (22 StarDict dictionaries, not DILA long descriptions)
        saved_vi = (row['saved_name'] or '').strip()
        auto_vi = (row['auto_name'] or '').strip()
        han_name = row['name_zh'] or ''
        suggest_api = han_name or saved_vi or auto_vi or ''
        candidates = []

        if suggest_api:
            suggest_norm = normalize_text(suggest_api)
            lex_rows = conn.execute(
                "SELECT DISTINCT term FROM lexicon WHERE key_norm = ? AND LENGTH(term) < 100 ORDER BY priority ASC LIMIT 5",
                (suggest_norm,)
            ).fetchall()
            for r in lex_rows:
                text = r['term']
                if text == han_name:  # Skip self-match (e.g. 波利城→波利城)
                    continue
                candidates.append({"source": "lexicon", "text": text})

        if han_name:
            h_terms = _lexicon_han_lookup(conn, han_name)
            for text in h_terms:
                if not any(c['text'] == text for c in candidates):
                    candidates.append({"source": "lexicon_han", "text": text})

        if suggest_api and not any(c['text'] == suggest_api for c in candidates):
            if suggest_api != han_name:
                candidates.append({"source": "api", "text": suggest_api})

        # Provenance from person_refs
        provenance = []
        person_id = row['person_id']
        if person_id:
            refs = conn.execute(
                "SELECT source_name, ref_type, value, note FROM person_refs WHERE person_id = ?",
                (person_id,)
            ).fetchall()
            provenance = [dict(r) for r in refs]
        conn.close()

        data = dict(row)
        data['gps_lat'] = data.pop('m_lat', None) or data.get('geo_lat') or data.get('gps_lat') or ''
        data['gps_long'] = data.pop('m_long', None) or data.get('geo_long') or data.get('gps_long') or ''
        data['verdict'] = data.get('saved_name') or ''
        data['source'] = data.get('source') or 'none'
        data['needs_review'] = data.get('needs_review') or 0
        data['vn_name_status'] = data.get('vn_name_status') or None
        data['note_vi'] = data.get('note_vi') or ''
        # Provide title-cased name_vi for frontend display
        name_source = data.get('saved_name') or data.get('auto_name') or ''
        data['name_vi_display'] = title_case_vi(name_source) if name_source else ''
        default_suggestion = ''
        for c in candidates:
            if c['source'] == 'lexicon':
                default_suggestion = c['text']
                break
        data['lexicon_suggestions'] = {
            "default_suggestion": default_suggestion,
            "candidates": candidates
        }
        data['han_variants'] = parse_han_variants(data.get('raw_xml', ''))
        data['name_variants'] = parse_name_variants(data.get('raw_xml', ''))
        data['full_description'] = data.get('raw_xml') or ''
        data['raw_tei'] = data.get('raw_xml') or ''
        data['district'] = data.get('raw_district') or ''
        data['address'] = data.get('pending_address') or ''
        data['raw_address'] = data.get('pending_address') or ''
        data['country'] = data.get('raw_country') or ''
        data['district_vi'] = data.get('district_vi') or ''
        data['country_vi'] = data.get('country_vi') or ''
        # Dynasty/historical region: note_type=廣大之陸上人文地理區域 + no district → no admin address
        dila_note = (data.get('dila_note') or '').strip()
        if dila_note == '廣大之陸上人文地理區域' and not (data.get('raw_district') or '').strip():
            data['district_vi'] = ''
            if not data.get('country_vi'):
                geo_lat = data.get('geo_lat') or data.get('gps_lat') or ''
                geo_lng = data.get('geo_long') or data.get('gps_long') or ''
                try:
                    lat, lng = float(geo_lat or 0), float(geo_lng or 0)
                    # China bounding box
                    if 18 <= lat <= 54 and 73 <= lng <= 135:
                        data['country_vi'] = 'Trung Quốc'
                    else:
                        data['country_vi'] = ''
                except (ValueError, TypeError):
                    data['country_vi'] = ''
        data['person_id'] = person_id or ''
        data['provenance'] = provenance
        data['source_name'] = data.get('source_name') or 'DILA_Authority'
        data['license'] = data.get('license') or 'CC BY-SA 4.0'
        data['usage_level'] = data.get('usage_level') or 'YELLOW'
        data['success'] = True
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/translate_context', methods=['POST'])
def translate_context():
    body = request.get_json(silent=True) or {}
    text = (body.get('text') or '').strip()
    style = body.get('style', 'formal')
    source_lang = body.get('source_lang', 'zho-Hant')
    target_lang = body.get('target_lang', 'vi')
    if not text:
        return jsonify({"success": False, "error": "Thiếu text"}), 400
    # T123 — Style Constitution unified builder (thay prompt cứng)
    conn = get_db_connection()
    try:
        lock = _t73_style_lock(conn)
        rv = lock['rules_version']
    finally:
        conn.close()
    prompt = _t73_build_style_prompt(text, lock, label='đoạn văn')
    meta = {"llm_provider": "", "style": style, "source_lang": source_lang,
            "target_lang": target_lang, "rules_version": rv}
    # Try Groq first
    try:
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.1, 'max_tokens': 2048},
            timeout=15)
        result = resp.json()
        if result.get('choices'):
            text_vi = result['choices'][0]['message']['content']
            if text_vi:
                text_vi = clean_gemini_output(text_vi)
                meta["llm_provider"] = GROQ_MODEL
                return jsonify({"success": True, "text_vi": text_vi, "meta": meta})
    except Exception:
        pass
    # Fallback: translators (Google)
    try:
        import translators as ts
        text_vi = ts.translate_text(text[:3000], to_language='vi', translator='google')
        if text_vi:
            text_vi = clean_gemini_output(text_vi)
            meta["llm_provider"] = "google-translate"
            return jsonify({"success": True, "text_vi": text_vi, "meta": meta})
    except Exception:
        pass
    # Fallback: deep-translator
    try:
        from deep_translator import GoogleTranslator
        text_vi = GoogleTranslator(source='zh-CN', target='vi').translate(text)
        if text_vi:
            text_vi = clean_gemini_output(text_vi)
            meta["llm_provider"] = "google-translate"
            return jsonify({"success": True, "text_vi": text_vi, "meta": meta})
    except Exception:
        pass
    meta["llm_provider"] = "fallback"
    return jsonify({"success": True, "text_vi": text, "meta": meta})


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


@app.route('/daoanh/api/admin/cbeta/update_summary', methods=['POST'])
def admin_cbeta_update_summary():
    """
    POST /daoanh/api/admin/cbeta/update_summary
    Body: { ref: "T50n2060_p0574b20", vi_summary_clean: "..." }
    Manual override for vi_summary_clean of a CBETA ref.
    """
    try:
        body = request.get_json(silent=True) or {}
        ref = (body.get('ref') or '').strip()
        new_summary = (body.get('vi_summary_clean') or '').strip()
        if not ref:
            return jsonify({"ok": False, "error": "Thiếu ref"}), 400
        conn = get_db_connection()
        conn.execute(f"""
            UPDATE {CBETA_REF_TABLE}
            SET vi_summary_clean = ?, vi_summary_raw = COALESCE(vi_summary_raw, ''),
                updated_at = CURRENT_TIMESTAMP
            WHERE ref_code = ?
        """, (new_summary, ref))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "success": True, "ref": ref})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/explain', methods=['POST'])
def admin_cbeta_explain():
    """
    POST /daoanh/api/admin/cbeta/explain
    Body: { ref: "T50n2060_p0457c16", place_han: "少林寺", place_id: "shaolin" }
    Flow:
    1) Sync han_text from cbeta.db (reuse _sync_ref_passage).
    2) Extract sentence containing place_han.
    3) Check cbeta_ref_explanations cache → return instantly if found.
    4) Call Gemini for explanation → cache → return.
    """
    try:
        body = request.get_json(silent=True) or {}
        ref = (body.get('ref') or '').strip()
        place_han = (body.get('place_han') or '').strip()
        place_id = (body.get('place_id') or '').strip()

        if not ref or not place_han:
            return jsonify({"ok": False, "error": "Thiếu ref hoặc place_han"}), 400
        if not place_id:
            place_id = place_han

        # 1) Sync han_text from cbeta.db
        sync_result = _sync_ref_passage(ref)
        if not sync_result or not sync_result.get('han_text'):
            return jsonify({"ok": False, "error": "no_text", "message": f"Chưa có văn bản CBETA cho {ref}"}), 404

        han_text = sync_result['han_text']

        # 2) Extract sentence containing place_han
        han_sentence = extract_sentence_with_place(han_text, place_han)
        if not han_sentence:
            return jsonify({"ok": False, "error": "no_match", "message": f"Không tìm thấy '{place_han}' trong văn bản CBETA"}), 404

        # 3) Check cache
        conn = get_db_connection()
        try:
            cached = conn.execute(
                "SELECT explanation_vi FROM cbeta_ref_explanations WHERE ref = ? AND place_id = ?",
                (ref, place_id)
            ).fetchone()
            if cached and cached['explanation_vi']:
                return jsonify({
                    "ok": True, "success": True,
                    "ref": ref, "place_han": place_han, "place_id": place_id,
                    "han_sentence": han_sentence,
                    "explanation_vi": cached['explanation_vi'],
                    "cached": True
                })
        finally:
            conn.close()

        # 4) Call Gemini
        prompt = f"""Bạn là chuyên gia Phật học và Hán-Nôm. Hãy giải thích địa danh / khái niệm sau đây xuất hiện trong văn bản CBETA (Phật giáo Trung Quốc cổ đại):

Địa danh / thuật ngữ Hán: {place_han}
Số hiệu CBETA: {ref}

Câu văn gốc:
「{han_sentence}」

Yêu cầu:
- Giải thích bằng tiếng Việt, 2–4 câu, hướng tới độc giả phổ thông.
- Cho biết ý nghĩa, vị trí (nếu là địa danh), và bối cảnh xuất hiện trong đoạn kinh.
- Nếu là địa danh, cố gắng liên hệ với tên gọi Việt Nam hiện đại nếu có.
- Chỉ tường thuật dựa trên văn bản, không thêm hư cấu."""
        explanation = _call_gemini(prompt, timeout=15)
        if not explanation:
            explanation = f"Địa danh {place_han} xuất hiện trong văn bản CBETA {ref}. {han_sentence}"
        explanation = clean_gemini_output(explanation)

        # 5) Cache
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO cbeta_ref_explanations (ref, place_id, place_han, han_sentence, explanation_vi)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ref, place_id) DO UPDATE SET
                    place_han=excluded.place_han,
                    han_sentence=excluded.han_sentence,
                    explanation_vi=excluded.explanation_vi,
                    updated_at=CURRENT_TIMESTAMP
            """, (ref, place_id, place_han, han_sentence, explanation))
            conn.commit()
        finally:
            conn.close()

        return jsonify({
            "ok": True, "success": True,
            "ref": ref, "place_han": place_han, "place_id": place_id,
            "han_sentence": han_sentence,
            "explanation_vi": explanation,
            "cached": False
        })

    except Exception as e:
        import traceback
        app.logger.error(f"admin_cbeta_explain error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


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


@app.route('/daoanh/api/admin/polish_cbeta_translation', methods=['POST'])
def polish_cbeta_translation():
    """
    POST /daoanh/api/admin/polish_cbeta_translation
    Body: { rawText, placeId, cbetaRef, hanSource }
    Flow:
      1) improve_grammar (LLM) → corrected_text + uncertain_terms
      2) normalize_terms (lexicon fuzzy) → mappings
      3) Return polished text + uncertain mappings
    """
    try:
        body = request.get_json(silent=True) or {}
        raw_text = (body.get('rawText') or '').strip()
        han_source = (body.get('hanSource') or '').strip()
        place_id = (body.get('placeId') or '').strip()
        cbeta_ref = (body.get('cbetaRef') or '').strip()

        if not raw_text:
            return jsonify({"ok": False, "error": "Thiếu rawText"}), 400

        # Step 1: Grammar correction
        step1 = improve_grammar(raw_text, han_source or raw_text)
        corrected = step1.get('corrected_text', raw_text)
        uncertain = step1.get('uncertain_terms', [])

        # Step 2: Terminology normalization
        step2 = normalize_terms(corrected, uncertain)
        polished = step2['correctedText']

        return jsonify({
            "ok": True,
            "polishedText": polished,
            "uncertainMappings": [m for m in step2['mappings'] if m['confidence'] < 0.9],
            "metadata": {
                "originalLength": len(raw_text),
                "correctedLength": len(polished),
                "termsReplaced": sum(1 for m in step2['mappings'] if m['confidence'] >= 0.9),
                "termsUncertain": sum(1 for m in step2['mappings'] if m['confidence'] >= 0.7 and m['confidence'] < 0.9),
                "termsManual": sum(1 for m in step2['mappings'] if m['confidence'] < 0.7)
            }
        })

    except Exception as e:
        import traceback
        app.logger.error(f"polish_cbeta_translation error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Public Place Search API (for places.html GIS map) ──────────────────


@app.route('/daoanh/api/places/search')
def api_places_search():
    """
    GET /daoanh/api/places/search?q=...&limit=20&dynasty=...
    Searches both `places` (GPS) and `namevi_map_places` (Vietnamese names).
    Optional `dynasty` param filters to places with matching lineage_chronology entries.
    Returns deduplicated results sorted by confidence.
    """
    try:
        q = request.args.get('q', '').strip()
        scope = request.args.get('scope', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        limit = min(int(request.args.get('limit', 50)), 5000)
        conn = get_db_connection()
        results = []
        seen = set()

        if q and len(q) < 2:
            return jsonify({"ok": False, "error": "Query too short (min 2 chars)"}), 400

        # Scope filter: temple only
        # place_type is empty for all records, so filter by name patterns
        scope_temple = scope == 'temple'
        temple_patterns = ['%寺', '%庵', '%塔', '%院', '%禪林', '%精舍', '%石窟', '%伽藍']
        temple_patterns_vi = ['%chùa%', '%tự viện%', '%thiền viện%', '%tịnh xá%', '%am%']
        offset = int(request.args.get('offset', 0))
        cate = request.args.get('cate', '').strip()
        # BUG-008: bbox filter for nearby places (south,west,north,east)
        bbox_filter = ""
        bbox_params_list = []
        raw_bbox = request.args.get('bbox', '').strip()
        if raw_bbox:
            try:
                south, west, north, east = map(float, raw_bbox.split(','))
                bbox_filter = "AND p.gps_lat BETWEEN ? AND ? AND p.gps_long BETWEEN ? AND ?"
                bbox_params_list = [south, north, west, east]
            except Exception:
                pass

        # Category filter by name_zh keywords (note_category column does not exist; place_type all null)
        CATE_LIKES = {
            'temple_site':   ['%寺', '%廟%', '%塔', '%庵', '%禪%', '%精舍%', '%伽藍%', '%石窟%'],
            'mountain':      ['%山', '%峰', '%嶺%', '%崖%', '%岳%', '%丘%'],
            'river_lake':    ['%江', '%河', '%湖', '%溪', '%潭%', '%海%', '%港%', '%渡%'],
            'dynasty_region':['%郡%', '%州', '%路%', '%府%', '%道%', '%縣%', '%鄉%'],
            'other':         ['%洞%', '%岩%', '%林%', '%原%', '%坡%', '%野%'],
        }
        VALID_CATES = set(CATE_LIKES.keys()) | {'admin_place'}

        # Dynasty filter: if set, only places matching lineage_chronology entries
        chrono_dynasty_join = ""
        chrono_params = []
        if dynasty:
            # Get unique name_zh from lineage_chronology for this dynasty
            chrono_names = conn.execute("""
                SELECT DISTINCT c.title_zh
                FROM lineage_chronology c
                WHERE c.dynasty = ? AND c.title_zh IS NOT NULL AND c.title_zh != ''
            """, (dynasty,)).fetchall()
            chrono_zh_set = set(r['title_zh'] for r in chrono_names)
            # Build filter: only places whose name_zh appears in chrono set
            # Use a subquery for efficiency if set is large
            if not chrono_zh_set:
                return jsonify({"ok": True, "query": q, "dynasty": dynasty, "count": 0, "results": []})
            # We'll filter inline in each query block below instead

        if len(q) >= 2:
            pattern = f'%{q}%'

            # FTS5 nhanh — khớp có dấu / không dấu / gõ dở / ID / Hán.
            # MATCH thử lần lượt: phrase → token AND → prefix AND ("thiếu* lâm* tự*").
            # FTS đã chạy mà không khớp → trả rỗng nhanh (không LIKE full-scan gây "autocomplete ko chạy").
            fts_raw_ids = None
            try:
                ensure_places_search_fts(conn)
                ensure_places_pending_fts(conn)
                fts_candidates = [f'"{q.replace(chr(34), chr(34)+chr(34))}"']
                if re.fullmatch(r'[\w\s]+', q, re.UNICODE):
                    fts_candidates.append(q)
                prefix_terms = []
                for t in re.split(r'\s+', q.strip())[:6]:
                    t = re.sub(r'["*():+\-#@~^&]', '', t)
                    if t:
                        prefix_terms.append(t + '*')
                if prefix_terms:
                    fts_candidates.append(' '.join(prefix_terms))

                fts_raw_ids = []
                for fq in fts_candidates:
                    ids = []
                    for table, col in (("places_search_fts", "dila_id"), ("places_pending_fts", "id")):
                        try:
                            cand = conn.execute(
                                f"SELECT {col} AS vid FROM {table} WHERE {table} MATCH ? LIMIT 100",
                                (fq,)
                            ).fetchall()
                            ids.extend(r['vid'] for r in cand if r['vid'])
                        except Exception:
                            continue
                    if ids:
                        fts_raw_ids = ids
                        break
            except Exception:
                fts_raw_ids = None

            if fts_raw_ids:
                # Dedupe id (dạng ngắn + dạng đầy đủ) trước khi truy vấn kết quả
                in_seen = set()
                in_ids = []
                for raw in fts_raw_ids:
                    for form in (str(raw), ensure_long_id(raw)):
                        if form and form not in in_seen:
                            in_seen.add(form)
                            in_ids.append(form)
                if in_ids:
                    placeholders = ','.join('?' * len(in_ids))
                    try:
                        rows = conn.execute(f"""
                            SELECT p.id,
                                   p.name_zh,
                                   COALESCE(m.name_vi, p.name_vi) AS name_vi,
                                   COALESCE(g.gps_lat, m.gps_lat) AS lat,
                                   COALESCE(g.gps_long, m.gps_long) AS lng,
                                   g.place_type AS type,
                                   COALESCE(g.confidence, m.confidence, 1.0) AS confidence,
                                   d.note_category AS note_category
                            FROM places_pending p
                            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                            LEFT JOIN places g ON g.name_zh = p.name_zh AND p.name_zh != ''
                            LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
                            WHERE p.id IN ({placeholders})
                            ORDER BY
                                CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                                p.id ASC
                            LIMIT ?
                        """, in_ids + [q, pattern, limit]).fetchall()
                    except Exception:
                        rows = []
                    for r in rows:
                        rid = ensure_long_id(r['id'])
                        if rid not in seen:
                            seen.add(rid)
                            results.append({
                                "id": rid, "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                                "lat": r['lat'], "lng": r['lng'],
                                "type": r['type'], "confidence": r['confidence'],
                                "source": "fts",
                                "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh'])
                            })
            if not results:
                # FTS không tìm thấy (index lỗi, hoặc entry mới chưa được index) → LIKE fallback.
                # 1) Search places table (has GPS coordinates)
                try:
                    rows = conn.execute("""
                        SELECT p.id, p.name_zh, p.name_vi, p.gps_lat, p.gps_long,
                               p.place_type, p.confidence, d.note_category
                        FROM places p
                        LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
                        WHERE (p.name_zh LIKE ? OR p.name_vi LIKE ? OR p.id LIKE ?)
                          AND p.gps_lat IS NOT NULL
                        ORDER BY p.confidence DESC
                        LIMIT ?
                    """, (pattern, pattern, pattern, limit)).fetchall()
                    for r in rows:
                        rid = r['id']
                        if rid not in seen:
                            seen.add(rid)
                            results.append({
                                "id": rid, "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                                "lat": r['gps_lat'], "lng": r['gps_long'],
                                "type": r['place_type'], "confidence": r['confidence'],
                                "source": "places",
                                "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh'])
                            })
                except Exception:
                    pass

                # 2) Supplement from namevi_map_places (has full name_vi)
                remaining = limit - len(results)
                if remaining > 0:
                    try:
                        rows = conn.execute("""
                            SELECT n.dila_id, n.name_zh, n.name_vi,
                                   COALESCE(p.gps_lat, n.gps_lat) as lat,
                                   COALESCE(p.gps_long, n.gps_long) as lng,
                                   p.place_type,
                                   COALESCE(p.confidence, n.confidence) as confidence,
                                   d.note_category
                            FROM namevi_map_places n
                            LEFT JOIN places p ON p.name_zh = n.name_zh AND p.name_zh != ''
                            LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(n.dila_id, 3) AS INTEGER))
                            WHERE (n.name_vi LIKE ? OR n.name_zh LIKE ?)
                            GROUP BY n.dila_id
                            ORDER BY confidence DESC
                            LIMIT ?
                        """, (pattern, pattern, remaining)).fetchall()
                        for r in rows:
                            rid = r['dila_id']
                            if rid not in seen:
                                seen.add(rid)
                                results.append({
                                    "id": rid, "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                                    "lat": r['lat'], "lng": r['lng'],
                                    "type": r['place_type'], "confidence": r['confidence'],
                                    "source": "namevi_map",
                                    "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh'])
                                })
                    except Exception:
                        pass
            # else: FTS đã chạy, không khớp → results rỗng, trả về nhanh.
        else:
            # No query: return top places with GPS + name_vi
            temple_likes = []
            temple_params = []
            if scope_temple:
                for pat in temple_patterns:
                    temple_likes.append("p.name_zh LIKE ?")
                    temple_params.append(pat)
                for pat in temple_patterns_vi:
                    temple_likes.append("COALESCE(n.name_vi, p.name_vi) LIKE ?")
                    temple_params.append(pat)
                temple_where = "AND (" + " OR ".join(temple_likes) + ")"
            elif cate and cate in VALID_CATES:
                cate_likes_list = []
                cate_params_list = []
                if cate == 'admin_place':
                    # Exclude all known non-admin categories (filter by name_zh)
                    exclude_pats = []
                    exclude_params = []
                    for pats in CATE_LIKES.values():
                        for p_ in pats:
                            exclude_pats.append("p.name_zh NOT LIKE ?")
                            exclude_params.append(p_)
                    temple_where = "AND (" + " AND ".join(exclude_pats) + ")"
                    temple_params = exclude_params
                else:
                    for p_ in CATE_LIKES[cate]:
                        cate_likes_list.append("p.name_zh LIKE ?")
                        cate_params_list.append(p_)
                    temple_where = "AND (" + " OR ".join(cate_likes_list) + ")"
                    temple_params = cate_params_list
            else:
                # No filter specified: return empty so UI prompts user to choose a category
                temple_where = "AND 1=0"
                temple_params = []
            params = temple_params + bbox_params_list + [limit]
            if offset:
                params.append(offset)
            try:
                sql = f"""
                    SELECT p.id, p.name_zh,
                           COALESCE(n.name_vi, p.name_vi) AS name_vi,
                           p.gps_lat, p.gps_long,
                           p.place_type, p.confidence,
                           d.note_category,
                           p.province
                    FROM places p
                    LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                    LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
                    WHERE p.gps_lat IS NOT NULL
                      {temple_where}
                      {bbox_filter}
                    GROUP BY p.id
                    ORDER BY p.confidence DESC
                    LIMIT ?{ ' OFFSET ?' if offset else '' }
                """
                rows = conn.execute(sql, params).fetchall()
                _prov_cache = {}
                for r in rows:
                    prov_raw = r['province'] or ''
                    if prov_raw not in _prov_cache:
                        _prov_cache[prov_raw] = _translate_admin_text(prov_raw, conn) if prov_raw else ''
                    results.append({
                        "id": r['id'], "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                        "lat": r['gps_lat'], "lng": r['gps_long'],
                        "type": r['place_type'], "confidence": r['confidence'],
                        "source": "places",
                        "icon_type": _note_category_to_icon_type(r['note_category'], r['name_zh']),
                        "province_vi": _prov_cache[prov_raw]
                    })
            except Exception:
                pass

        conn.close()

        # Post-filter by dynasty if set
        if dynasty and chrono_zh_set:
            results = [r for r in results if r.get('name_zh') in chrono_zh_set]

        # Sanitize name_vi (replace any remaining CJK with Hán-Việt)
        for r in results:
            if r.get('name_vi'):
                r['name_vi'] = _ensure_vietnamese(r['name_vi'])

        # Re-rank by string similarity khi có query — FTS trả đúng candidates
        # nhưng ORDER BY id ASC có thể đặt kết quả kém hơn lên đầu.
        if q:
            q_n = normalize_text(q)
            def _qscore(r):
                name = (r.get('name_vi') or r.get('name_zh') or '').strip()
                nlo = name.lower()
                qlo = q.lower()
                nn = normalize_text(name)
                if nlo == qlo:      return 100
                if nn == q_n:       return 90
                if nlo.startswith(qlo): return 80
                if nn.startswith(q_n):  return 70
                if qlo in nlo:      return 60
                if q_n in nn:       return 50
                return 10
            results.sort(key=_qscore, reverse=True)

        return jsonify({
            "ok": True, "query": q, "count": len(results), "results": results
        })

    except Exception as e:
        import traceback
        app.logger.error(f"api_places_search error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/places/all')
def api_places_all():
    """Get all places with optional category filter (temple, mountain, cave, all)."""
    try:
        category = request.args.get('category', 'all').strip()
        limit = min(int(request.args.get('limit', 5000)), 10000)
        conn = get_db_connection()
        # Build base query selecting needed fields — note_category from places_dila (places table has no such column)
        query = """
            SELECT p.id, p.name_zh, COALESCE(n.name_vi, p.name_vi) AS name_vi,
                   p.gps_lat, p.gps_long, p.place_type, d.note_category
            FROM places p
            LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
            LEFT JOIN places_dila d ON d.id = printf('PL%012d', CAST(SUBSTR(p.id, 3) AS INTEGER))
            WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
        """
        params = []
        if category != 'all':
            # Map to internal categories based on note_category patterns (from joined places_dila)
            if category == 'temple':
                query += " AND (d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%')"
            elif category == 'mountain':
                query += " AND d.note_category LIKE '%山峰%'"
            elif category == 'cave':
                query += " AND d.note_category LIKE '%石窟%'"
        query += " GROUP BY p.id ORDER BY p.confidence DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        results = []
        for r in rows:
            vi = r['name_vi'] or r['name_zh'] or ''
            vi = _ensure_vietnamese(vi)
            results.append({
                'id': r['id'],
                'name_zh': r['name_zh'],
                'name_vi': vi,
                'lat': r['gps_lat'],
                'lng': r['gps_long'],
                'category': r['note_category'],
                'icon_type': _note_category_to_icon_type(r['note_category'], r['name_zh'])
            })
        return jsonify({"ok": True, "count": len(results), "places": results})
    except Exception as e:
        app.logger.error(f"api_places_all error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/daoanh/api/places/unified')
def api_places_unified():
    """
    GET /daoanh/api/places/unified?dynasty=...&limit=300
    Returns ALL GPS locations from places + lineage_chronology, deduplicated.
    One entry per GPS coordinate for single-marker rendering.
    """
    try:
        dynasty = request.args.get('dynasty', '').strip()
        limit = min(int(request.args.get('limit', 300)), 1000)
        conn = get_db_connection()

        # Part 1: places with GPS (+ name_vi from namevi_map_places)
        if dynasty:
            chrono_names = conn.execute("""
                SELECT DISTINCT c.title_zh
                FROM lineage_chronology c
                WHERE c.dynasty = ? AND c.title_zh IS NOT NULL AND c.title_zh != ''
            """, (dynasty,)).fetchall()
            chrono_zh_set = set(r['title_zh'] for r in chrono_names)
            if not chrono_zh_set:
                conn.close()
                return jsonify({"ok": True, "dynasty": dynasty, "count": 0, "results": []})
            all_places = conn.execute("""
                SELECT p.id, p.name_zh,
                       COALESCE(n.name_vi, p.name_vi) AS name_vi,
                       p.gps_lat, p.gps_long,
                       p.confidence, p.source_origin
                FROM places p
                LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
                GROUP BY p.id
                ORDER BY p.confidence DESC
                LIMIT 2000
            """).fetchall()
            place_rows = [p for p in all_places if p['name_zh'] in chrono_zh_set]
        else:
            place_rows = conn.execute("""
                SELECT p.id, p.name_zh,
                       COALESCE(n.name_vi, p.name_vi) AS name_vi,
                       p.gps_lat, p.gps_long,
                       p.confidence, p.source_origin
                FROM places p
                LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
                GROUP BY p.id
                ORDER BY p.confidence DESC
                LIMIT ?
            """, (limit,)).fetchall()

        # Part 2: chronology events with GPS (via places_dila)
        chrono_rows = conn.execute("""
            SELECT lc.id, lc.title_zh,
                   COALESCE(lc.title, lc.title_zh) AS name_vi,
                   pd.geo_lat, pd.geo_long,
                   lc.dynasty
            FROM lineage_chronology lc
            JOIN places_dila pd ON pd.name_zh = lc.title_zh
            WHERE pd.geo_lat IS NOT NULL AND pd.geo_long IS NOT NULL
              AND (? = '' OR lc.dynasty = ?)
            GROUP BY lc.id
        """, (dynasty, dynasty)).fetchall()
        conn.close()

        # Merge by GPS proximity (rounded to 3 decimals ≈ 100m)
        merged = {}
        for p in place_rows:
            key = (round(p['gps_lat'], 3), round(p['gps_long'], 3))
            merged[key] = {
                'id': p['id'],
                'name_vi': _ensure_vietnamese(p['name_vi'] or p['name_zh'] or ''),
                'name_zh': p['name_zh'] or '',
                'lat': p['gps_lat'],
                'lng': p['gps_long'],
                'confidence': p['confidence'] or 0.5,
                'source': 'place',
                'dynasty': '',
                'has_chronology': False,
            }

        for c in chrono_rows:
            key = (round(c['geo_lat'], 3), round(c['geo_long'], 3))
            if key in merged:
                merged[key]['has_chronology'] = True
                if c['dynasty'] and not merged[key]['dynasty']:
                    merged[key]['dynasty'] = c['dynasty']
            else:
                merged[key] = {
                    'id': f"c_{c['id']}",
                    'name_vi': _ensure_vietnamese(c['name_vi'] or c['title_zh'] or ''),
                    'name_zh': c['title_zh'] or '',
                    'lat': c['geo_lat'],
                    'lng': c['geo_long'],
                    'confidence': 0.5,
                    'source': 'chronology',
                    'dynasty': c['dynasty'] or '',
                    'has_chronology': True,
                }

        results = list(merged.values())
        if not dynasty:
            results = results[:limit]

        return jsonify({
            "ok": True,
            "count": len(results),
            "has_chronology": sum(1 for r in results if r['has_chronology']),
            "results": results
        })

    except Exception as e:
        import traceback
        app.logger.error(f"api_places_unified error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/places/<place_id>')
def api_places_detail(place_id):
    """
    GET /daoanh/api/places/<id>
    Returns full detail from both places + namevi_map_places.
    Tries exact ID match in both tables, then falls back to name_zh match.
    """
    try:
        conn = get_db_connection()
        detail = None

        # 1) Try places table by ID (has GPS)
        row = conn.execute("""
            SELECT * FROM places WHERE id = ?
        """, (place_id,)).fetchone()

        if row:
            detail = dict(row)
            detail['source'] = 'places'
            # Supplement dila_id, name_vi, note_vi from namevi_map_places
            if detail.get('name_zh'):
                nv = conn.execute("""
                    SELECT name_vi, note_vi, dila_id
                    FROM namevi_map_places
                    WHERE name_zh = ? AND (name_vi != '' OR dila_id IS NOT NULL)
                    ORDER BY (vn_name_status = 'reviewed') DESC, (source = 'manual') DESC, confidence DESC
                    LIMIT 1
                """, (detail['name_zh'],)).fetchone()
                if nv:
                    if not detail.get('name_vi') and nv['name_vi']:
                        detail['name_vi'] = nv['name_vi']
                    if not detail.get('note_vi') and nv['note_vi']:
                        detail['note_vi'] = nv['note_vi']
                    if not detail.get('dila_id') and nv['dila_id']:
                        detail['dila_id'] = nv['dila_id']
        else:
            # 2) Try namevi_map_places by dila_id (has name_vi)
            row = conn.execute("""
                SELECT * FROM namevi_map_places WHERE dila_id = ?
            """, (place_id,)).fetchone()

            if row:
                detail = dict(row)
                detail['source'] = 'namevi_map'
                # Bổ sung GPS/province/country từ places (khớp name_zh) khi THIẾU
                # — không chỉ khi GPS thiếu: namevi_map có thể có GPS nhưng rỗng
                # province/country (VD 少林寺 PL000000023255 → province rỗng).
                if detail.get('name_zh') and (not detail.get('province') or not detail.get('country') or not detail.get('gps_lat')):
                    p = conn.execute("""
                        SELECT gps_lat, gps_long, province, country, source_origin
                        FROM places WHERE name_zh = ?
                        ORDER BY gps_lat IS NOT NULL DESC, province IS NOT NULL DESC
                        LIMIT 1
                    """, (detail['name_zh'],)).fetchone()
                    if p:
                        if not detail.get('gps_lat'):
                            detail['gps_lat'] = p['gps_lat']
                        if not detail.get('gps_long'):
                            detail['gps_long'] = p['gps_long']
                        if not detail.get('province'):
                            detail['province'] = p['province']
                        if not detail.get('country'):
                            detail['country'] = p['country']
                        if not detail.get('source_origin'):
                            detail['source_origin'] = p['source_origin']

        # Supplement with cbeta_catalog_vn (text_info + license)
        # Uses: (1) exact LIKE, (2) fuzzy match table, (3) VI name search
        name_zh = detail.get('name_zh', '') if detail else ''
        name_vi = detail.get('name_vi', '') if detail else ''
        # text_info: only attach CBETA catalog data when the match is about a WORK
        # whose title IS the place name (exact prefix), not just contains it.
        # This prevents "少林無孔笛" from incorrectly matching the place "少林寺".
        if detail and name_zh:
            cat = None
            fuzzy = None
            # Exact title match only (title_zh starts with or equals name_zh)
            exact = conn.execute("""
                SELECT title_vi, title_zh, dynasty_vi, translator_vi,
                       q_number, page, sh_number, juans,
                       source_name, source_full_title,
                       license_name, license_url, source_note
                FROM cbeta_catalog_vn
                WHERE title_zh = ? OR title_zh LIKE ?
                LIMIT 1
            """, (name_zh, f'{name_zh} %')).fetchone()
            if exact:
                cat = exact
            if not cat:
                # Fuzzy match — only accept high-confidence (score >= 90)
                fuzzy = conn.execute("""
                    SELECT v.title_vi, v.title_zh, v.dynasty_vi, v.translator_vi,
                           v.q_number, v.page, v.sh_number, v.juans,
                           v.source_name, v.source_full_title,
                           v.license_name, v.license_url, v.source_note
                    FROM cbeta_catalog_place_fuzzy f
                    JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                    WHERE f.place_id = ? AND f.score >= 90
                    ORDER BY f.score DESC, f.rank ASC
                    LIMIT 1
                """, (place_id,)).fetchone()
                if fuzzy:
                    # Sanity check: title must start with the place name
                    ft = dict(fuzzy).get('title_zh', '')
                    if ft.startswith(name_zh):
                        cat = fuzzy
                    else:
                        fuzzy = None
            if cat:
                detail['text_info'] = dict(cat)
                match_type = 'exact' if exact else ('fuzzy' if fuzzy else 'like')
                detail['text_info_match'] = match_type

        conn.close()

        if not detail:
            return jsonify({"ok": False, "error": "Place not found"}), 404

        # Sanitize name_vi, note_vi and province — never leave raw CJK on the page.
        # If name_vi is missing (e.g. dynasty/historical entities like 遼, 清朝),
        # synthesize it from name_zh via lexicon-first + flagged Hán-Việt fallback.
        if detail.get('name_vi'):
            detail['name_vi'] = _ensure_vietnamese(detail['name_vi'])
        elif detail.get('name_zh'):
            _lex_conn = get_db_connection()
            try:
                detail['name_vi'] = _translate_zh_term(detail['name_zh'], _lex_conn)
            finally:
                _lex_conn.close()
        # Known dynasty/kingdom names always display with a "Nhà " prefix,
        # regardless of whether name_vi came from admin-curated data
        # (namevi_map_places), the DB, or the fallback above.
        if detail.get('name_zh') in DYNASTY_NAMES and detail.get('name_vi'):
            _nv = detail['name_vi']
            if not _nv.startswith('Nhà ') and not _nv.startswith('Triều '):
                _lex_conn = get_db_connection()
                try:
                    detail['name_vi'] = _translate_dynasty_name(detail['name_zh'], _lex_conn) or f'Nhà {_nv}'
                finally:
                    _lex_conn.close()
        if detail.get('note_vi'):
            detail['note_vi'] = _ensure_vietnamese(detail['note_vi'])

        # Vị trí (3 Lớp RAG): dữ liệu thô + địa chỉ cấu trúc giống placevn.html
        # district_raw/geo hiển thị nguyên trạng; district_vi/country_vi là bản
        # đã chuẩn hoá (rule-based parse_dila_district, không tốn AI).
        raw_district = detail.get('province') or detail.get('district_raw') or detail.get('address') or ''
        raw_country = detail.get('country') or ''
        detail['district_raw'] = raw_district
        parsed = parse_dila_district(raw_district) if raw_district else {}
        # Ưu tiên địa chỉ rule-based sạch; fallback district_vi/country_vi admin (namevi_map_places)
        detail['district_vi'] = (parsed.get('district_vi') or parsed.get('formatted') or '') or detail.get('district_vi') or ''
        country_vi = (parsed.get('country_vi') or '') or detail.get('country_vi') or raw_country or ''
        if country_vi in ('中國', '中国', 'China'):
            country_vi = 'Trung Quốc'
        elif country_vi in ('阿富汗', 'افغانستان'):
            country_vi = 'Afghanistan'
        elif country_vi in ('印度', 'भारत'):
            country_vi = 'Ấn Độ'
        detail['country_vi'] = country_vi

        # Supplement from places_dila: note (raw description), listbibl (CBETA refs),
        # note_category. Lookup priority: dila_id (exact) → name_zh fallback.
        try:
            _dconn = get_db_connection()
            try:
                _dila_row = None
                _dila_id = detail.get('dila_id', '')
                if _dila_id:
                    _dila_row = _dconn.execute(
                        "SELECT note, listbibl, note_category FROM places_dila WHERE id = ? LIMIT 1",
                        (_dila_id,)
                    ).fetchone()
                if not _dila_row and detail.get('name_zh'):
                    _dila_row = _dconn.execute(
                        "SELECT note, listbibl, note_category FROM places_dila WHERE (name = ? OR name_zh = ?) AND note IS NOT NULL AND note != '' LIMIT 1",
                        (detail['name_zh'], detail['name_zh'])
                    ).fetchone()
            finally:
                _dconn.close()
            if _dila_row:
                if not (detail.get('note_vi') or '').strip() and _dila_row['note']:
                    raw = re.sub(r'<[^>]+>', ' ', _dila_row['note'])
                    raw = re.sub(r'\s+', ' ', raw).strip()
                    detail['dila_note'] = raw
                if _dila_row['listbibl']:
                    detail['dila_listbibl'] = _dila_row['listbibl']
                if _dila_row['note_category']:
                    detail['dila_category'] = _dila_row['note_category']
        except Exception:
            pass

        # T112 D-Feedback: tự ghi gap khi địa danh thiếu nội dung mô tả (note_vi + dila_note đều trống)
        if detail and not (detail.get('note_vi') or '').strip() and not detail.get('dila_note') \
                and not (detail.get('description_vi') or '').strip():
            _t112_record_gap('place', place_id, detail.get('name_zh') or detail.get('name') or '',
                             'thieu_noidung',
                             "Địa danh thiếu mô tả nội dung tiếng Việt/DILA trực tiếp (note_vi, dila_note)",
                             source_hint='places_dila; namevi_map_places')

        # Lexicon verification: "Đã Duyệt" khi tên Việt xuất hiện trong 25 bộ từ điển Phật học
        _name_for_lex = (detail.get('name_vi') or '').strip()
        if _name_for_lex:
            try:
                _lconn = get_db_connection()
                _lex = _lconn.execute(
                    "SELECT source FROM lexicon WHERE term = ? LIMIT 5",
                    (_name_for_lex,)
                ).fetchall()
                if not _lex:
                    # Thử dạng thay thế: "Chùa X" ↔ "X Tự"
                    _alt = _name_for_lex
                    if _alt.endswith(' Tự'):
                        _alt = 'Chùa ' + _alt[:-3].strip()
                    elif _alt.startswith('Chùa '):
                        _alt = _alt[5:].strip() + ' Tự'
                    if _alt != _name_for_lex:
                        _lex = _lconn.execute(
                            "SELECT source FROM lexicon WHERE term = ? LIMIT 5",
                            (_alt,)
                        ).fetchall()
                _lconn.close()
                if _lex:
                    detail['vn_name_status'] = 'reviewed'
                    detail['lexicon_sources'] = [r['source'] for r in _lex]
            except Exception:
                pass

# T29: bdrc_id removed — BDRC integration skipped per admin decision.
        # Previously: real BDRC IDs require P2477 SPARQL from Wikidata; all 148 rows had bdrc_id = NULL.

        # Parallel structured founding data from Wikidata + DILA rawtext
        # Source priority: Wikidata P571 (place_timeline_events) > DILA note fallback
        try:
            # 1. Wikidata P571 founded date from place_timeline_events
            founding = conn.execute(
                "SELECT year, source, source_ref "
                "FROM place_timeline_events "
                "WHERE entity_id = ? AND event_type = 'founding' "
                "ORDER BY confidence DESC LIMIT 1",
                (place_id,)
            ).fetchone()
            
            if founding:
                detail['founding_year'] = founding[0]
                detail['founding_source'] = founding[1] or 'wikidata'
                detail['founding_source_ref'] = founding[2] or ''
            else:
                detail['founding_year'] = None
                detail['founding_source'] = None
                detail['founding_source_ref'] = None
        except Exception:
            detail['founding_year'] = None
            detail['founding_source'] = None
            detail['founding_source_ref'] = None

        # 2. DILA rawtext (始建於...) as fallback when Wikidata missing
        try:
            _dconn = get_db_connection()
            try:
                _dila_row = None
                _dila_id = detail.get('dila_id', '')
                if _dila_id:
                    _dila_row = _dconn.execute(
                        "SELECT note FROM places_dila WHERE id = ? LIMIT 1",
                        (_dila_id,)
                    ).fetchone()
            finally:
                _dconn.close()
            
            if _dila_row and _dila_row[0]:
                _raw = re.sub(r'<[^>]+>', ' ', _dila_row[0])
                _raw = re.sub(r'\s+', ' ', _raw).strip()
                # Extract founding year (e.g., "始建於495年")
                _m = re.search(r'始建於\s*(\d{3,4})', _raw)
                if _m:
                    detail['dila_founding_year'] = int(_m.group(1))
                    detail['dila_rawtext'] = _raw
                else:
                    detail['dila_founding_year'] = None
                    detail['dila_rawtext'] = _raw
            else:
                detail['dila_founding_year'] = None
                detail['dila_rawtext'] = ''
        except Exception:
            detail['dila_founding_year'] = None
            detail['dila_rawtext'] = ''

        # 3. Wikidata QID from geo_cross_ref (already populated: 148/148)
        # Already available in detail from earlier geo_cross_ref lookup

        # 4. DILA ID (always present for places in this API)
        detail['dila_id'] = detail.get('dila_id')

        if detail.get('province'):
            detail['province'] = _translate_admin_text(detail['province'])

        return jsonify({"ok": True, "data": detail})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── PLACES × CHRONOLOGY CROSS-SEARCH ───────────────────────

@app.route('/daoanh/api/places/<place_id>/chronology')
def api_places_chronology(place_id):
    """
    GET /daoanh/api/places/<id>/chronology?limit=20
    Finds lineage_chronology entries matching this place's name_zh.
    Returns cross-linked people/works associated with this location.
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        conn = get_db_connection()

        # Get place's name_zh from either table
        name_zh = None
        row = conn.execute("SELECT name_zh FROM places WHERE id = ?", (place_id,)).fetchone()
        if row:
            name_zh = row['name_zh']
        if not name_zh:
            row = conn.execute("SELECT name_zh FROM namevi_map_places WHERE dila_id = ?", (place_id,)).fetchone()
            if row:
                name_zh = row['name_zh']
        if not name_zh:
            row = conn.execute("SELECT name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
            if row:
                name_zh = row['name_zh']

        if not name_zh:
            conn.close()
            return jsonify({"ok": False, "error": "No name_zh for this place"}), 404

        # Query lineage_chronology matching name_zh
        chrono_conn = get_chronology_conn()
        rows = chrono_conn.execute("""
            SELECT * FROM lineage_chronology
            WHERE title_zh = ?
            ORDER BY century_start NULLS LAST
            LIMIT ?
        """, (name_zh, limit)).fetchall()
        chrono_conn.close()
        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "name_zh": name_zh,
            "count": len(rows),
            "results": [dict(r) for r in rows]
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


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


@app.route('/daoanh/api/places/<place_id>/cbeta')
def api_places_cbeta(place_id):
    """GET /daoanh/api/places/<id>/cbeta — CBETA passages + catalog matches for a place."""
    import re as _re
    try:
        conn = get_db_connection()
        dila_id, name_zh = _resolve_dila_id(conn, place_id)

        passages = []
        fosizhi_entries = []
        if dila_id:
            dila_row = conn.execute("SELECT listbibl, raw_xml FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
            if dila_row and dila_row['listbibl']:
                listbibl_raw = dila_row['listbibl']
                seen_refs = set()
                for entry in [e.strip() for e in listbibl_raw.split(';') if e.strip()]:
                    m = _re.match(r'\(\s*CBETA\s+([\w_]+)\s*\)\s*(.*)', entry)
                    if m:
                        ref = m.group(1).strip()
                        if ref in seen_refs:
                            continue
                        seen_refs.add(ref)
                        rest = m.group(2).strip()
                        tag_m = _re.search(r'\{([^}]+)\}', rest)
                        place_tag = tag_m.group(1).strip() if tag_m else ''
                        title_context = _re.sub(r'\s*\{[^}]+\}\s*', '', rest).strip()
                        passages.append({
                            'ref_code': ref,
                            'sigla': ref.split('_')[0] if '_' in ref else ref,
                            'title_context': title_context,
                            'place_tag': place_tag,
                        })
            # Fosi Zhi (g-series): chỉ có trong raw_xml, không có trong listbibl
            raw_xml = (dila_row['raw_xml'] or '') if dila_row else ''
            if raw_xml:
                # ns0:ref namespace prefix + URL may span a line — use flexible pattern
                fz_matches = _re.findall(
                    r'target="([^"]*fosizhi[^"]*)">([^(<]+)\(([^)]+)\)</[^>]+>\s*\{([^}]+)\}',
                    raw_xml
                )
                seen_fz = set()
                for url, ref_code, book_title, place_tag in fz_matches:
                    ref_code = ref_code.strip()
                    if ref_code in seen_fz:
                        continue
                    seen_fz.add(ref_code)
                    fosizhi_entries.append({
                        'ref_code': ref_code,
                        'book_title': book_title.strip(),
                        'place_tag': place_tag.strip(),
                        'url': url.replace('&amp;', '&')
                    })

        # Kinh Điển Liên Quan — T-series only, JOIN cbeta_catalog_vn (Nguyễn Minh Tiến, CC BY-SA 4.0)
        # Chỉ T-series vì cbeta_catalog_vn chỉ cover Đại Chính Tạng; X-series không có tên Việt.
        related_texts = []
        if dila_id:
            dila_row2 = conn.execute("SELECT listbibl FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
            if dila_row2 and dila_row2['listbibl']:
                seen_sh = set()
                for m2 in _re.finditer(r'CBETA\s+T\d+n(\d+)_', dila_row2['listbibl']):
                    sh = m2.group(1)
                    if sh in seen_sh:
                        continue
                    seen_sh.add(sh)
                    cat = conn.execute(
                        "SELECT title_zh, title_vi, translator_vi, dynasty_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ? AND (series='T' OR series IS NULL) LIMIT 1",
                        (sh,)
                    ).fetchone()
                    if cat and cat['title_vi']:
                        related_texts.append({
                            'sh_number': sh,
                            'title_zh': cat['title_zh'],
                            'title_vi': cat['title_vi'],
                            'translator_vi': cat['translator_vi'] or '',
                            'dynasty_vi': cat['dynasty_vi'] or '',
                        })

        conn.close()
        return jsonify({"ok": True, "place_id": place_id, "dila_id": dila_id,
                        "passages": passages, "fosizhi_entries": fosizhi_entries,
                        "related_texts": related_texts})
    except Exception as e:
        app.logger.error(f"api_places_cbeta error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


_BUDDHIST_SYSTEM_PROMPT = """Bạn là dịch giả Hán-Việt chuyên về văn học Phật giáo Bắc Tông Việt Nam.
Quy tắc bắt buộc:
- Tăng nhân: 釋X → Thích X (KHÔNG phiên âm pinyin)
- Địa danh: dùng âm Hán-Việt (雍州→Ung Châu, 嵩山→Tung Sơn, 河南→Hà Nam)
- Thuật ngữ cố định: 舍利→xá-lợi, 菩薩→Bồ Tát, 禪→Thiền, 涅槃→Niết-bàn, 比丘→Tỳ-kheo
- 下流 trong văn ngôn = chảy xuống hạ lưu (KHÔNG phải "tục tĩu")
- Giữ tên kinh điển bằng Hán-Việt (大藏經→Đại Tạng Kinh, 高僧傳→Cao Tăng Truyện)
- Văn phong: tự nhiên, chuẩn văn học Phật giáo Việt Nam, không dịch từng chữ
- Chỉ dịch, không giải thích hay chú thích"""


# (Endpoint cũ /daoanh/api/passage/<int:passage_id>/translate ĐÃ BỊ XOÁ — trùng route
#  với /daoanh/api/passage/<passage_id>/translate. Hành vi giữ nguyên trong legacy
#  fallback của unified route: Groq toàn passage → passage.vi_text / GET cached.)


@app.route('/daoanh/api/entity/<entity_id>/related', methods=['GET'])
def api_entity_related(entity_id):
    """GET /daoanh/api/entity/<id>/related — Quan Hệ panel data.
    Returns:
      places  — địa danh co-mentioned qua passage_entity
      persons — thiền sư từ place_person_link (curated) + passage_entity (canonical)
      texts   — danh sách tác phẩm từ cbeta_text_catalog mapped tới entity
    """
    try:
        conn = get_db_connection()
        dila_id, _ = _resolve_dila_id(conn, entity_id)
        canonical_id = dila_id or entity_id

        # ── 1. Co-mentioned PLACES qua passage_entity ───────────────────────
        place_rows = conn.execute("""
            SELECT pe2.entity_id, COUNT(*) AS mentions
            FROM passage_entity pe1
            JOIN passage_entity pe2 ON pe1.passage_id = pe2.passage_id
            WHERE pe1.entity_id IN (?, ?)
              AND pe2.entity_id LIKE 'PL%'
              AND pe2.entity_id NOT IN (?, ?)
            GROUP BY pe2.entity_id
            ORDER BY mentions DESC LIMIT 15
        """, (entity_id, canonical_id, entity_id, canonical_id)).fetchall()

        places = []
        _seen_place_norm = set()  # dedup: passage_entity stores both PL046734 and PL000000046734
        for r in place_rows:
            eid = r['entity_id']
            # normalize: strip leading zeros padding to get short DILA id
            short = eid.replace('PL000000', 'PL') if eid.startswith('PL000000') else eid
            if short in _seen_place_norm:
                continue
            _seen_place_norm.add(short)
            nm = conn.execute(
                "SELECT name_zh, name_vi FROM namevi_map_places WHERE dila_id IN (?, ?) LIMIT 1",
                (eid, short)
            ).fetchone()
            places.append({
                'entity_id': short,
                'name_zh': nm['name_zh'] if nm else eid,
                'name_vi': nm['name_vi'] if nm else None,
                'mentions': r['mentions'],
                'source': 'canonical'
            })

        # ── 2a. Persons — CURATED (place_person_link) ───────────────────────
        _ensure_place_person_link_table(conn)
        curated_rows = conn.execute("""
            SELECT l.person_id, l.relation_type, p.name_zh, p.name_vi, p.dynasty
            FROM place_person_link l JOIN people p ON p.id = l.person_id
            WHERE l.place_id IN (?, ?)
            ORDER BY l.created_at ASC
        """, (entity_id, canonical_id)).fetchall()

        persons = []
        curated_ids = set()
        for r in curated_rows:
            curated_ids.add(r['person_id'])
            persons.append({
                'entity_id': r['person_id'],
                'name_zh': r['name_zh'], 'name_vi': r['name_vi'],
                'dynasty': r['dynasty'],
                'relation_type': r['relation_type'] or 'liên quan',
                'source': 'curated', 'mentions': None
            })

        # ── 2b. Persons — CANONICAL (passage_entity A-prefix) ───────────────
        person_rows = conn.execute("""
            SELECT pe2.entity_id, COUNT(*) AS mentions
            FROM passage_entity pe1
            JOIN passage_entity pe2 ON pe1.passage_id = pe2.passage_id
            WHERE pe1.entity_id IN (?, ?)
              AND pe2.entity_id LIKE 'A%'
            GROUP BY pe2.entity_id
            ORDER BY mentions DESC LIMIT 12
        """, (entity_id, canonical_id)).fetchall()

        for r in person_rows:
            if r['entity_id'] in curated_ids:
                continue
            nm = conn.execute(
                "SELECT name_zh, name_vi, dynasty FROM people WHERE id = ? LIMIT 1",
                (r['entity_id'],)
            ).fetchone()
            persons.append({
                'entity_id': r['entity_id'],
                'name_zh': nm['name_zh'] if nm else r['entity_id'],
                'name_vi': nm['name_vi'] if nm else None,
                'dynasty': nm['dynasty'] if nm else None,
                'relation_type': 'cùng đề cập trong kinh',
                'source': 'canonical', 'mentions': r['mentions']
            })

        # ── 3. Texts — từ cbeta_text_catalog mapped tới entity ──────────────
        texts = []
        try:
            text_rows = conn.execute("""
                SELECT ct.catalog_id, ct.title_zh, ct.title_vi, ct.era_vi,
                       ct.author_vi, em.mapping_status, em.mapping_note
                FROM entity_text_map em
                JOIN cbeta_text_catalog ct ON ct.catalog_id = em.catalog_id
                WHERE em.entity_id IN (?, ?)
                ORDER BY em.mapping_status DESC, ct.catalog_id ASC LIMIT 20
            """, (entity_id, canonical_id)).fetchall()
            texts = [dict(r) for r in text_rows]
        except Exception:
            pass

        conn.close()
        return jsonify({
            'ok': True,
            'entity_id': entity_id,
            'places': places,
            'persons': persons,
            'texts': texts
        })

    except Exception as e:
        app.logger.error(f'api_entity_related error: {e}')
        return jsonify({'ok': False, 'error': str(e)}), 500


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


@app.route('/daoanh/api/cbeta/<sigla>/related')
def api_cbeta_related(sigla):
    """GET /daoanh/api/cbeta/<sigla>/related — gợi ý 3 nhóm (T55 spec §T55b).
    Nhóm 1 'crossref' — SAT URL / Toh 84000 / Pali map (đối chiếu chuẩn).
    Nhóm 2 'topic'    — 2 kinh khác cùng đề tài (chia sẻ ≥3 DILA persons, verified).
    Nhóm 3 'persons'  — thiền sư/nhân vật xuất hiện trong kinh này.
    Trung thực: nhóm không có data → trả [] kèm 'status':'NO_DATA' chứ không bịa.
    """
    try:
        s_key, s_num = _t55_normalize_sigla(sigla)
        s_series = (s_key or 'T')[0].upper()
        conn = get_db_connection()

        # ── Nhóm 1: crossref ───────────────────────────────────────────────
        crossref = []
        sat = conn.execute(
            "SELECT cbeta_sigla, sat_url, has_unique FROM sat_crossref WHERE cbeta_sigla = ? LIMIT 1",
            (s_key,)).fetchone()
        if sat:
            crossref.append({'kind': 'sat', 'sigla': sat['cbeta_sigla'],
                             'url': sat['sat_url'], 'has_unique': bool(sat['has_unique'])})
        toh = conn.execute(
            "SELECT toh, cbeta_sigla, title_vi, title_en, url_84000, canon_section, confidence "
            "FROM toh_cbeta_crossref WHERE cbeta_sigla = ? LIMIT 1", (s_key,)).fetchone()
        if toh:
            crossref.append({'kind': 'toh', 'toh': toh['toh'], 'sigla': toh['cbeta_sigla'],
                             'title_vi': toh['title_vi'], 'title_en': toh['title_en'],
                             'url_84000': toh['url_84000'], 'canon_section': toh['canon_section'],
                             'confidence': toh['confidence']})
        if s_num and s_num.isdigit():
            pali_sh = '{:04d}'.format(int(s_num))
            pali = conn.execute(
                "SELECT sh, pali_title, pts_sutta, note FROM pali_cbeta_map WHERE sh = ? LIMIT 1",
                (pali_sh,)).fetchone()
            if pali:
                crossref.append({'kind': 'pali', 'pali_title': pali['pali_title'],
                                 'pts_sutta': pali['pts_sutta'], 'note': pali['note']})

        # ── Nhóm 3: persons trong chính kinh ───────────────────────────────
        persons = []
        p_rows = []
        if s_num and s_num.isdigit():
            # mentions lưu ref đầy đủ ('T51n2076'/'X77n1524') → GLOB theo series + số
            glob_pat = "{}*n{}".format(s_series, str(int(s_num)))
            p_rows = conn.execute(
                """SELECT dila_person_id, person_name_zh, COUNT(*) AS mentions
                   FROM cbeta_person_mentions
                   WHERE cbeta_text_sigla GLOB ?
                   GROUP BY dila_person_id, person_name_zh
                   ORDER BY mentions DESC LIMIT 12""", (glob_pat,)).fetchall()
        if not p_rows:
            # fallback: raw input (vài bảng lưu full ref như 'T50n2059_p0338c09')
            base = sigla.split('_')[0]
            p_rows = conn.execute(
                """SELECT dila_person_id, person_name_zh, COUNT(*) AS mentions
                   FROM cbeta_person_mentions
                   WHERE cbeta_text_sigla LIKE ?
                   GROUP BY dila_person_id, person_name_zh
                   ORDER BY mentions DESC LIMIT 12""", (base + '%',)).fetchall()
        pid_mapping = {}
        if p_rows:
            ids = [r['dila_person_id'] for r in p_rows]
            qmarks = ','.join('?' * len(ids))
            try:
                pmeta = conn.execute(f"""SELECT id, name_zh, name_vi, dynasty
                                         FROM people WHERE id IN ({qmarks})""", ids).fetchall()
                pid_mapping = {r['id']: r for r in pmeta}
            except Exception:
                pass
            for r in p_rows:
                meta = pid_mapping.get(r['dila_person_id'])
                persons.append({
                    'entity_id': r['dila_person_id'],
                    'name_zh': r['person_name_zh'],
                    'name_vi': meta['name_vi'] if meta else None,
                    'dynasty': meta['dynasty'] if meta else None,
                    'mentions': r['mentions']})

        # ── Nhóm 2: topic — 2 kinh khác chia sẻ same persons ──────────────
        topic = []
        if p_rows:
            ids = list({r['dila_person_id'] for r in p_rows})
            qmarks = ','.join('?' * len(ids))
            glob_pat = "{}*n{}".format(s_series, str(int(s_num))) if s_num and s_num.isdigit() else None
            if glob_pat:
                # loại trừ chính văn bản nguồn (mọi volume cùng số) để chỉ còn 'kinh khác'
                topic_rows = conn.execute(
                    f"""SELECT cbeta_text_sigla, COUNT(*) AS shared
                        FROM cbeta_person_mentions
                        WHERE dila_person_id IN ({qmarks}) AND cbeta_text_sigla NOT GLOB ?
                        GROUP BY cbeta_text_sigla
                        HAVING COUNT(*) >= 3
                        ORDER BY shared DESC LIMIT 8""", ids + [glob_pat]).fetchall()
                for r in topic_rows:
                    topic.append({'sigla': r['cbeta_text_sigla'], 'shared_persons': r['shared']})

        conn.close()
        resp = {
            'ok': True,
            'sigla': sigla, 'short_key': s_key, 'text_num': s_num,
            'groups': {
                'crossref': crossref or [{'status': 'NO_DATA'}],
                'topic': topic or [{'status': 'NO_DATA'}],
                'persons': persons or [{'status': 'NO_DATA'}],
            },
        }
        return jsonify(resp)

    except Exception as e:
        app.logger.error(f'api_cbeta_related error: {e}')
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/daoanh/api/translate', methods=['POST'])
def api_translate_passage():
    """POST /daoanh/api/translate — Dịch đoạn Hán văn với cache DB.
    Body: { ref_code: str } — han_text không cần gửi, backend tự fetch từ DB
    Returns: { ok: bool, vi_text: str, cached: bool }
    """
    data = request.get_json(force=True, silent=True) or {}
    ref_code = (data.get('ref_code') or '').strip()

    if not ref_code:
        return jsonify({'ok': False, 'error': 'Thiếu ref_code'}), 400

    try:
        conn = get_db_connection()

        # Kiểm tra cache trước
        db_row = conn.execute(
            "SELECT han_text, vi_summary_clean FROM cbeta_ref_passages WHERE ref_code = ?",
            (ref_code,)
        ).fetchone()
        conn.close()

        if db_row and (db_row['vi_summary_clean'] or '').strip():
            return jsonify({'ok': True, 'vi_text': db_row['vi_summary_clean'].strip(), 'cached': True})

        han_text = (db_row['han_text'] or '').strip() if db_row else ''
        if not han_text:
            return jsonify({'ok': False, 'error': f'Không có nội dung hán văn cho {ref_code}'}), 404

        if not ANTHROPIC_KEY or _anthropic_sdk is None:
            return jsonify({'ok': False, 'error': 'ANTHROPIC_KEY chưa cấu hình hoặc module anthropic chưa cài — set env var và install package'}), 503

        # Gọi Claude Haiku
        client = _anthropic_sdk.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=2048,
            system=_BUDDHIST_SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': f'Dịch đoạn văn ngôn Phật giáo sau sang tiếng Việt:\n\n{han_text}'
            }]
        )
        vi_text = msg.content[0].text.strip()

        # Lưu cache vào DB
        if ref_code and vi_text:
            conn2 = get_db_connection()
            conn2.execute(
                "UPDATE cbeta_ref_passages SET vi_summary_clean = ? WHERE ref_code = ?",
                (vi_text, ref_code)
            )
            conn2.commit()
            conn2.close()

        return jsonify({'ok': True, 'vi_text': vi_text, 'cached': False})

    except Exception as e:
        app.logger.error(f'api_translate_passage error: {e}')
        if _anthropic_sdk is not None:
            return jsonify({'ok': False, 'error': f'Lỗi API: {e.status_code}'}), 502
        return jsonify({'ok': False, 'error': 'Lỗi dịch - module anthropic chưa sẵn sàng'}), 502
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/daoanh/api/places/<place_id>/graph')
def api_places_graph(place_id):
    """GET /daoanh/api/places/<id>/graph — Unified knowledge graph (T16/T17 realization).

    Nodes/edges built ONLY from source-traceable authority data:
    - alt_names: places_dila.raw_xml placeName[type="alternative"] (DILA-curated, real attribute)
    - related texts: places_dila.listbibl CBETA sigla -> JOIN cbeta_catalog_vn (Nguyễn Minh Tiến,
      CC BY-SA 4.0) — same T-series JOIN pattern used in api_places_cbeta(), not fuzzy matching.
    - nearby places: same-province structural lookup (not a content/authority claim).

    Removed 2026-08-19: `persons_mentioned` (regex-scraped from free `note` text against a
    hand-picked name list — no scholarly-reviewed place<->person link exists anywhere in the
    schema; `places`/`places_dila`/`people` all lack a person<->place column) and `text_links`
    via `cbeta_catalog_place_fuzzy` (RapidFuzz score match). Both are the same category of
    violation as the passage_entity/fuzzy blocks already removed elsewhere per CLAUDE.md's
    content-integrity rule — an auto-derived guess standing in for a real authority source.

    See GET /daoanh/api/monk/<dila_id>/graph for the person-entity counterpart (Marcus SNA
    teacher/student lineage, each edge carries a real CBETA citation `ref`).
    """
    import re as _re
    try:
        conn = get_db_connection()
        place_row = conn.execute("SELECT * FROM places WHERE id = ?", (place_id,)).fetchone()
        dila_id, name_zh = _resolve_dila_id(conn, place_id)
        if not name_zh and place_row:
            name_zh = place_row['name_zh'] or ''
        _raw_name_vi = (place_row['name_vi'] if place_row else None) or None
        # Enrich center: try namevi_map_places by dila_id first (gives ZQ name_vi + intended name_zh)
        if not _raw_name_vi and dila_id:
            _vi_row = conn.execute(
                "SELECT name_vi, name_zh FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
                (dila_id,)
            ).fetchone()
            if _vi_row and _vi_row['name_vi']:
                _raw_name_vi = _vi_row['name_vi']
                # When places table has no row, prefer ZQ's name_zh over DILA canonical
                if not place_row and _vi_row['name_zh']:
                    name_zh = _vi_row['name_zh']
        # Fall back to name_zh lookup if still missing
        if not _raw_name_vi and name_zh:
            _vi_row = conn.execute(
                "SELECT name_vi FROM namevi_map_places WHERE name_zh = ? LIMIT 1", (name_zh,)
            ).fetchone()
            if _vi_row and _vi_row['name_vi']:
                _raw_name_vi = _vi_row['name_vi']
        label_vi = _raw_name_vi or name_zh

        alt_names = []
        related_sh = []
        if dila_id:
            dila_row = conn.execute("SELECT raw_xml, listbibl, district FROM places_dila WHERE id = ? LIMIT 1", (dila_id,)).fetchone()
            if dila_row:
                raw_xml = dila_row['raw_xml'] or ''
                raw_alts = _re.findall(r'placeName type="alternative"[^>]*>([^<]+)<', raw_xml)
                # FIX 1: enrich alt_names with Việt readings from namevi_map_places
                alt_names = []
                for zh_alt in raw_alts:
                    vi_row = conn.execute(
                        "SELECT name_vi FROM namevi_map_places WHERE name_zh = ? LIMIT 1",
                        (zh_alt,)
                    ).fetchone()
                    alt_names.append({
                        'zh': zh_alt,
                        'vi': vi_row['name_vi'] if vi_row and vi_row['name_vi'] else None
                    })
                listbibl = dila_row['listbibl'] or ''
                seen_sh = set()
                for m in _re.finditer(r'CBETA\s+T\d+n(\d+)_', listbibl):
                    sh = m.group(1)
                    if sh not in seen_sh:
                        seen_sh.add(sh)
                        related_sh.append(sh)

        # Map Cao Tang Truyen collection -> sh_number for text node hub
        _CTT_SH = {'唐高僧傳': '2060', '宋高僧傳': '2061', '明高僧傳': '2062'}

        nodes, edges = [], []
        text_node_ids = set()   # track which text nodes already exist

        for sh in related_sh:
            cat = conn.execute(
                "SELECT title_zh, title_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ? LIMIT 1",
                (sh,)
            ).fetchone()
            if cat:
                node_id = 'text:' + sh
                nodes.append({"id": node_id, "label": cat['title_vi'] or cat['title_zh'] or sh,
                              "label_zh": cat['title_zh'],
                              "group": "text", "navigable": False})
                edges.append({"from": place_id, "to": node_id, "label": "kinh điển liên quan",
                              "evidence_type": "with_evidence"})
                text_node_ids.add(node_id)

        _nearby_province = (place_row['province'] if place_row and place_row['province'] else None)
        if not _nearby_province and dila_id:
            # Fallback: place not in places table — use places_dila.district (same format as province)
            _nearby_province = dila_row['district'] if dila_row and dila_row['district'] else None
        if _nearby_province:
            nearby_rows = conn.execute(
                "SELECT id, name_zh, name_vi FROM places WHERE province = ? AND id != ?",
                (_nearby_province, place_id)
            ).fetchall()
            for r in nearby_rows:
                nodes.append({"id": r['id'], "label": r['name_vi'] or r['name_zh'], "label_zh": r['name_zh'],
                              "group": "place", "navigable": True})
                edges.append({"from": place_id, "to": r['id'], "label": "lân cận",
                              "evidence_type": "co_mention"})

        # T16 — Person nodes qua text-hub: place → Cao Tang Truyen → person
        # Edge structure: place→text_node (collection hub) →person (temporal layering)
        # nexus_events may not exist on all deployments — degrade gracefully
        if dila_id:
            try:
                nexus_rows = conn.execute("""
                    SELECT ne.person_dila_id, ne.event_label, ne.source_book, ne.confidence,
                           p.name_vi, p.name_zh
                    FROM nexus_events ne
                    LEFT JOIN people p ON p.id = ne.person_dila_id
                    WHERE ne.place_dila_id = ? AND ne.person_dila_id IS NOT NULL
                    ORDER BY ne.confidence DESC
                """, (dila_id,)).fetchall()
            except Exception:
                nexus_rows = []
            seen_pids = set()
            for r in nexus_rows:
                pid = r[0]
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)
                src_book = r[2]
                sh = _CTT_SH.get(src_book)
                hub_id = ('text:' + sh) if sh else None

                # Create hub text node if not already from listbibl
                if hub_id and hub_id not in text_node_ids:
                    cat = conn.execute(
                        "SELECT title_zh, title_vi FROM cbeta_catalog_vn WHERE CAST(sh_number AS TEXT) = ? LIMIT 1",
                        (sh,)
                    ).fetchone()
                    if cat:
                        nodes.append({"id": hub_id, "label": cat['title_vi'] or cat['title_zh'] or sh,
                                      "label_zh": cat['title_zh'], "group": "text", "navigable": False})
                        edges.append({"from": place_id, "to": hub_id, "label": "kinh điển liên quan",
                                      "evidence_type": "with_evidence"})
                        text_node_ids.add(hub_id)
                    else:
                        hub_id = None  # catalog miss — fall back to direct edge

                dn = _t86_resolve_display_name(conn, pid)
                pname = dn['primary']
                node_id = 'person:' + pid
                nodes.append({
                    "id": node_id, "label": pname,
                    "label_zh": dn['authority_secondary'] or dn['secondary'] or r[5] or r[1],
                    "group": "person", "navigable": True, "dila_id": pid,
                    "source": "nexus_tei",
                    "title": f"Nguồn: {src_book} (confidence {r[3]})"
                })
                from_id = hub_id if hub_id else place_id
                conf = r[3]
                ev_type = "with_evidence" if conf >= 0.7 else "partial"
                p_reason = None if conf >= 0.7 else f"Confidence thấp ({conf:.2f}): {src_book}"
                edges.append({"from": from_id, "to": node_id,
                              "label": "", "has_ref": True, "ref": src_book,
                              "evidence_type": ev_type, "partial_reason": p_reason})

        # T101 BUG-004: curated place_person_link — scholarly-reviewed links (Bồ Đề Đạt Ma, Huệ Khả…)
        # Ưu tiên hơn nexus_events vì có note + source_url rõ ràng. Dedupe qua seen_pids.
        if dila_id:
            try:
                ppl_rows = conn.execute("""
                    SELECT l.person_id, l.relation_type, l.source_name, l.note,
                           p.name_vi, p.name_zh
                    FROM place_person_link l
                    LEFT JOIN people p ON p.id = l.person_id
                    WHERE l.place_id = ?
                """, (dila_id,)).fetchall()
            except Exception:
                ppl_rows = []
            for r in ppl_rows:
                pid = r[0]
                if not pid or pid in seen_pids:
                    continue
                seen_pids.add(pid)
                node_id = 'person:' + pid
                dn = _t86_resolve_display_name(conn, pid)
                pname = dn['primary']
                title_str = (r[2] or '') + (': ' + r[3] if r[3] else '')
                nodes.append({
                    "id": node_id, "label": pname,
                    "label_zh": dn['authority_secondary'] or dn['secondary'] or r[5] or '',
                    "group": "person", "navigable": True, "dila_id": pid,
                    "source": "curated",
                    "title": title_str
                })
                edges.append({"from": place_id, "to": node_id,
                              "label": r[1] or '', "has_ref": True,
                              "ref": r[2] or '', "evidence_type": "with_evidence"})

        conn.close()
        return jsonify({
            "ok": True, "entity_type": "place", "place_id": place_id,
            "center": {"id": place_id, "label": label_vi, "label_zh": name_zh, "label_vi": _raw_name_vi},
            "alt_names": alt_names,
            "nodes": nodes, "edges": edges
        })
    except Exception as e:
        app.logger.error(f"api_places_graph error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/daoanh/api/nexus/find')
def api_nexus_find():
    """GET /daoanh/api/nexus/find — T16 Nexus Points query.

    Params: place=PL..., person=A..., year_from=int, year_to=int, min_conf=float (default 0.7)
    Returns: {nexus_points: [{person_dila_id, place_dila_id, source_book, cbeta_ref, confidence,
              person_name_vi, person_name_zh, place_name_vi, place_name_zh}, ...]}
    """
    try:
        place  = request.args.get('place', '').strip()
        person = request.args.get('person', '').strip()
        year_from = request.args.get('year_from', type=int)
        year_to   = request.args.get('year_to',   type=int)
        min_conf  = request.args.get('min_conf',  default=0.7, type=float)

        clauses, params = ["ne.confidence >= ?"], [min_conf]
        if place:  clauses.append("ne.place_dila_id = ?");  params.append(place)
        if person: clauses.append("ne.person_dila_id = ?"); params.append(person)
        if year_from is not None: clauses.append("ne.event_year >= ?"); params.append(year_from)
        if year_to   is not None: clauses.append("ne.event_year <= ?"); params.append(year_to)

        where = " AND ".join(clauses)
        conn = get_db_connection()
        rows = conn.execute(f"""
            SELECT ne.person_dila_id, ne.place_dila_id, ne.source_book,
                   ne.passage_id, ne.confidence, ne.event_year, ne.event_label,
                   p.name_vi  AS pname_vi,  p.name_zh  AS pname_zh,
                   pl.name_vi AS plname_vi, pl.name_zh AS plname_zh
            FROM nexus_events ne
            LEFT JOIN people      p  ON p.id  = ne.person_dila_id
            LEFT JOIN places      pl ON pl.id = ne.place_dila_id
            WHERE {where}
            ORDER BY ne.confidence DESC
            LIMIT 100
        """, params).fetchall()
        conn.close()

        result = [{
            "person_dila_id": r[0], "place_dila_id": r[1],
            "source_book": r[2], "cbeta_ref": r[3],
            "confidence": r[4], "event_year": r[5], "event_label": r[6],
            "person_name_vi": r[7], "person_name_zh": r[8],
            "place_name_vi": r[9], "place_name_zh": r[10]
        } for r in rows]
        return jsonify({"ok": True, "count": len(result), "nexus_points": result})
    except Exception as e:
        app.logger.error(f"api_nexus_find error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/monk/<dila_id>/graph')
def api_monk_graph(dila_id):
    """GET /daoanh/api/monk/<dila_id>/graph — Person-entity counterpart of
    /daoanh/api/places/<id>/graph (T16/T17 realization, Marcus lineage on Đồ Thị tab).

    Same nodes/edges shape as the place graph so places.html can render both with one
    vis-network renderer. Data is the already-verified Marcus SNA link (marcus_people_link,
    exact DILA-ID match, additive — see T04); every edge carries the real CBETA citation
    `ref` from marcus_networks, so this satisfies the "100% nguồn dẫn" bar without any
    fuzzy/regex guessing.
    """
    conn = get_db_connection()
    try:
        person = conn.execute(
            "SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if not person:
            return jsonify({"ok": False, "error": "person not found"}), 404
        # marcus_reference.label holds canonical dharma name (e.g. 慧能, 菩提達磨).
        # people.name_zh often stores DILA authority form: posthumous title, epithet, or
        # temple name (e.g. 大鑒真空普覺圓明禪師, 壁觀婆羅門, 靖居) which is wrong for display.
        marc_ref = conn.execute(
            "SELECT label, label_vi FROM marcus_reference WHERE node_id = ?", (dila_id,)
        ).fetchone()
        canonical_zh = (marc_ref['label'] if marc_ref else None) or person['name_zh']
        # T51f: label_vi now has proper Hán-Việt from marcus_reference (e.g. 菩提達磨→Bồ Đề Đạt Ma)
        # Prefer: marcus_reference.label_vi > people.name_vi > canonical_zh
        marc_label_vi = marc_ref['label_vi'] if marc_ref else None
        if marc_label_vi and marc_label_vi != canonical_zh:
            canonical_vi = marc_label_vi
        else:
            canonical_vi = person['name_vi'] or canonical_zh
        center = {"id": dila_id, "label": canonical_vi, "label_zh": canonical_zh,
                  "dila_stored_name": person['name_zh']}

        link = conn.execute(
            "SELECT marcus_node_id FROM marcus_people_link WHERE person_id = ?", (dila_id,)
        ).fetchone()
        nodes, edges = [], []
        if link:
            node_id = link['marcus_node_id']
            teachers = conn.execute("""
                SELECT teacher_id AS id, teacher_label AS label, relation_type, ref
                FROM marcus_networks WHERE student_id = ?
            """, (node_id,)).fetchall()
            students = conn.execute("""
                SELECT student_id AS id, student_label AS label, relation_type, ref
                FROM marcus_networks WHERE teacher_id = ?
            """, (node_id,)).fetchall()

            # Batch lookup label_vi for all neighbor nodes from marcus_reference
            neighbor_ids = [t['id'] for t in teachers] + [s['id'] for s in students]
            label_vi_map = {}
            if neighbor_ids:
                placeholders = ','.join('?' * len(neighbor_ids))
                for r in conn.execute(
                    f"SELECT node_id, label, label_vi FROM marcus_reference WHERE node_id IN ({placeholders})",
                    neighbor_ids
                ).fetchall():
                    vi = r['label_vi'] if r['label_vi'] and r['label_vi'] != r['label'] else None
                    label_vi_map[r['node_id']] = vi or r['label']

            for t in teachers:
                vi = label_vi_map.get(t['id'], t['label'])
                nodes.append({"id": t['id'], "label": vi, "label_zh": t['label'],
                              "role": "teacher", "group": "person", "navigable": True})
                edges.append({"from": t['id'], "to": dila_id, "label": "thầy của", "ref": t['ref']})
            for s in students:
                vi = label_vi_map.get(s['id'], s['label'])
                nodes.append({"id": s['id'], "label": vi, "label_zh": s['label'],
                              "role": "student", "group": "person", "navigable": True})
                edges.append({"from": dila_id, "to": s['id'], "label": "truyền cho", "ref": s['ref']})

            # Đồng môn (colleague_of) — DERIVED từ Marcus isTeacherOf: các student khác
            # cùng teacher với node đang xem. KHÔNG phải dữ liệu gốc — đánh dấu derived rõ ràng
            # để nghiên cứu tông môn (sư huynh đệ cùng pháp hệ) mà không ghi nhầm nguồn Marcus.
            siblings = conn.execute("""
                SELECT DISTINCT s2.student_id AS id, s2.student_label AS label,
                       s1.teacher_label AS shared_teacher_label
                FROM marcus_networks s1
                JOIN marcus_networks s2
                  ON s1.teacher_id = s2.teacher_id AND s1.student_id != s2.student_id
                WHERE s1.student_id = ?
                ORDER BY s2.student_label
            """, (node_id,)).fetchall()
            sib_ids = [sib['id'] for sib in siblings]
            sib_vi_map = {}
            if sib_ids:
                placeholders = ','.join('?' * len(sib_ids))
                for r in conn.execute(
                    f"SELECT node_id, label, label_vi FROM marcus_reference WHERE node_id IN ({placeholders})",
                    sib_ids
                ).fetchall():
                    vi = r['label_vi'] if r['label_vi'] and r['label_vi'] != r['label'] else None
                    sib_vi_map[r['node_id']] = vi or r['label']
            for sib in siblings:
                vi = sib_vi_map.get(sib['id'], sib['label'])
                nodes.append({"id": sib['id'], "label": vi, "label_zh": sib['label'],
                              "role": "sibling", "group": "person", "navigable": True})
                edges.append({
                    "from": dila_id, "to": sib['id'], "label": "đồng môn",
                    "derived": True, "ref": None,
                    "shared_teacher_label": sib['shared_teacher_label'],
                    "evidence_type": "co_mention",
                })

        return jsonify({
            "ok": True, "entity_type": "person", "person_id": dila_id,
            "center": center, "linked": bool(link),
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA" if link else None,
            "nodes": nodes, "edges": edges
        })
    except Exception as e:
        app.logger.error(f"api_monk_graph error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


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
    """Parse DILA Person Authority XML lần đầu tiên, lưu vào _T148_DILA_EXTRA.
    Dùng iterparse để tránh load toàn bộ cây XML vào RAM cùng lúc."""
    global _T148_DILA_EXTRA, _T148_EXTRA_LOADED
    with _T148_EXTRA_LOCK:
        if _T148_EXTRA_LOADED:
            return
        if not os.path.exists(_T148_PERSON_XML):
            _T148_EXTRA_LOADED = True
            return
        idx = {}
        ns = _T148_NS
        xml_ns = _T148_XML_NS
        try:
            t0 = time.time()
            ctx = _t148_ET.iterparse(_T148_PERSON_XML, events=('end',))
            for event, elem in ctx:
                if elem.tag != f'{{{ns}}}person':
                    continue
                pid = elem.get(f'{{{xml_ns}}}id') or elem.get('xml:id')
                if not pid:
                    elem.clear()
                    continue
                alt_names = []
                listbibl = []
                bio_extensive = None
                works_tripitaka = None
                works_by = None
                mentioned_in = None
                active_at = None
                name_latin = None
                occupation = None
                place_of_origin = None
                birth_death_quote = None
                wikidata_id = None
                birth_date = None
                death_date = None
                death_note = None
                relations = []
                sex_val = None
                dynasty_xml = None
                is_monk = None
                for child in elem:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag == 'persName':
                        ptype = child.get('type', '')
                        lang = child.get(f'{{{xml_ns}}}lang', '')
                        txt = (child.text or '').strip()
                        if ptype == 'alternative' and txt:
                            alt_names.append(txt)
                        elif not ptype and lang and lang not in ('zho-Hant', 'vie') and txt and not name_latin:
                            name_latin = txt  # san-Latn, pli-Latn, eng, jpn…
                    elif tag == 'listBibl':
                        for bibl in child:
                            t = (bibl.text or '').strip()
                            if not t:
                                ref_el = bibl.find(f'{{{ns}}}ref')
                                if ref_el is not None:
                                    t = (ref_el.text or '').strip()
                            if t:
                                listbibl.append(t)
                    elif tag == 'note':
                        ntype = child.get('type', '')
                        txt = (child.text or '').strip()
                        if ntype == 'extensive' and txt:
                            bio_extensive = txt
                        elif ntype == 'worksInTripitaka' and txt:
                            works_tripitaka = txt
                        elif ntype == 'worksBy' and txt:
                            works_by = txt
                        elif ntype == 'mentionedIn' and txt:
                            mentioned_in = txt
                        elif ntype == 'activeAt' and txt:
                            active_at = txt
                        elif ntype == 'birthDeathDateQuote' and txt:
                            birth_death_quote = txt
                        elif ntype == 'dynasty' and txt:
                            dynasty_xml = txt
                        elif ntype == 'monk' and txt:
                            is_monk = txt  # '是' hoặc '否'
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
                            wikidata_id = txt
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
                            rel_type = rel.get('type', '')   # 'teacher' | 'student'
                            active   = rel.get('active', '') # DILA person ID
                            name_n   = rel.get('n', '')      # Chinese name
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
                            or mentioned_in or active_at or name_latin or occupation
                            or place_of_origin or birth_death_quote or wikidata_id
                            or birth_date or death_date or relations or sex_val
                            or dynasty_xml or is_monk)
                if has_data:
                    idx[pid] = {
                        'bio_extensive': bio_extensive,
                        'alt_names': alt_names,
                        'sex': sex_val,
                        'listbibl': listbibl,
                        'works_tripitaka': works_tripitaka,
                        'works_by': works_by,
                        'mentioned_in': mentioned_in,
                        'active_at': active_at,
                        'name_latin': name_latin,
                        'occupation': occupation,
                        'place_of_origin': place_of_origin,
                        'birth_death_quote': birth_death_quote,
                        'wikidata_id': wikidata_id,
                        'birth_date': birth_date,
                        'death_date': death_date,
                        'death_note': death_note,
                        'relations': relations,
                        'dynasty_xml': dynasty_xml,
                        'is_monk': is_monk,
                    }
                elem.clear()
            _T148_DILA_EXTRA = idx
            elapsed = time.time() - t0
            print(f'[T148] Đã index {len(idx)} persons từ DILA XML trong {elapsed:.1f}s', flush=True)
        except Exception as ex:
            print(f'[T148] Lỗi parse DILA XML: {ex}', flush=True)
        finally:
            _T148_EXTRA_LOADED = True


def _t148_get_extra(pid):
    """Trả về extra DILA data cho một person id (load lazily)."""
    if not _T148_EXTRA_LOADED:
        _t148_load_dila_extra()
    return _T148_DILA_EXTRA.get(pid) or {}


def _t86_person_info(conn, pid):
    """Tên/niên hiệu/tông phái/môn phái cho một node lineage (DILA person id).
    Ưu tiên marcus_reference (tên pháp danh chuẩn + label_vi + năm sinh/mất) hơn people
    (name_zh thường là thụy hiệu/tự hiệu, birth/death nhiễm số trang CBETA — T79)."""
    marc = conn.execute(
        "SELECT label, label_vi, birth_year, death_year FROM marcus_reference WHERE node_id = ?",
        (pid,)
    ).fetchone()
    person = conn.execute(
        "SELECT name_zh, name_vi, dynasty, sect, bio FROM people WHERE id = ?", (pid,)
    ).fetchone()
    zh = (marc['label'] if marc and marc['label'] else None) \
        or (person['name_zh'] if person else None) or pid
    vi = None
    if marc and marc['label_vi'] and marc['label_vi'] != zh:
        vi = marc['label_vi']
    elif person and person['name_vi']:
        vi = person['name_vi']
    vi = vi or zh
    return {
        "id": pid,
        "name_vi": vi,
        "name_zh": zh,
        "dynasty": person['dynasty'] if person else None,
        "sect": person['sect'] if person else None,
        "birth_year": (marc['birth_year'] if marc else None),
        "death_year": (marc['death_year'] if marc else None),
        "bio": (person['bio'] if person else None) or None,
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
    vpa = conn.execute(
        "SELECT name_vi, name_zh, ttl_filename FROM vn_person_authority WHERE dila_id=? LIMIT 1",
        (person_id,)
    ).fetchone()
    if vpa and vpa['name_vi']:
        return {
            "primary":             vpa['name_vi'],
            "secondary":           vpa['name_zh'] or "",
            "authority_primary":   vpa['name_vi'],
            "authority_secondary": vpa['name_zh'] or "",
            "source_type":         "ttl",
            "source_file":         (vpa['ttl_filename'] or "") + ".ttl",
            "verification_status": "verified_direct",
            "is_formal_name":      True,
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


def _t86_origin_place(conn, person_id):
    """Nguồn địa lý cho 'Xem trên bản đồ' — person_origin_link (sinh tại/籍貫).
    Tìm name_vi qua places trước, fallback sang namevi_map_places theo name_zh."""
    row = conn.execute(
        "SELECT place_id FROM person_origin_link WHERE person_id=? ORDER BY confidence DESC LIMIT 1",
        (person_id,)
    ).fetchone()
    if not row:
        return None
    raw_pid = row['place_id']
    short_pid = _t86_normalize_place_id(raw_pid)
    pl = conn.execute(
        "SELECT name_vi, name_zh FROM places WHERE id=?", (short_pid,)
    ).fetchone()
    name_vi = pl['name_vi'] if pl else None
    name_zh = pl['name_zh'] if pl else None
    vi_confidence = None
    vi_source = None
    if not name_vi and name_zh:
        nv = conn.execute(
            "SELECT name_vi, confidence, source FROM namevi_map_places "
            "WHERE name_zh=? ORDER BY confidence DESC LIMIT 1",
            (name_zh,)
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


@app.route('/daoanh/api/monk/<dila_id>/lineage-tree')
def api_monk_lineage_tree(dila_id):
    """GET /daoanh/api/monk/<dila_id>/lineage-tree?up=3&down=3
    Cây phả hệ truyền thừa đệ quy quanh một tăng nhân. Mỗi node = thật từ
    marcus_networks (thầy/trò). Mỗi edge mang ref citation thật + has_ref (proxy dẫn
    chứng CBETA). Node có thể mở rộng sâu hơn (nếu còn thầy/trò vượt ngoài độ sâu)
    qua ?expand=<person_id>&dir=up|down — không crawl toàn bộ (zero-RAM, lazy)."""
    up = max(0, min(int(request.args.get('up', 3)), 6))
    down = max(0, min(int(request.args.get('down', 3)), 6))
    conn = get_db_connection()
    try:
        # Center phải là một người thật trong bảng people (chứa trong cơ sở truyền thừa).
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone()
        if not exists:
            return jsonify({"ok": False, "error": "person not found"}), 404
        center = _t86_person_info(conn, dila_id)
        center['conflicts'] = _t86_person_conflict(conn, dila_id)
        center['origin_place'] = _t86_origin_place(conn, dila_id)

        nodes = {dila_id: center}
        edges = []
        up_excess = set()    # nodes đạt độ sâu up → còn thầy ngoài
        down_excess = set()  # nodes đạt độ sâu down → còn trò ngoài
        node_origin = {}

        # BFS lên (thầy) theo độ sâu
        frontier = [dila_id]
        depth = {dila_id: 0}
        seen_up = {dila_id}
        while frontier:
            nxt = []
            for pid in frontier:
                if depth[pid] >= up:
                    continue
                nb, _cnt = _t86_neighbors(conn, pid, 'up')
                for nbv in nb:
                    nid = nbv['id']
                    if nid in seen_up:
                        continue
                    seen_up.add(nid)
                    depth[nid] = depth[pid] + 1
                    nodes.setdefault(nid, _t86_person_info(conn, nid))
                    node_origin.setdefault(nid, _t86_origin_place(conn, nid))
                    _e138 = _t138_edge_assertions(conn, nid, pid)
                    edges.append({
                        "from": nid, "to": pid, "direction": "teacher",
                        "relation_type": "da:isTeacherOf", "ref": nbv['ref'],
                        "has_ref": bool(nbv['ref']), "derived": False,
                        "sources": _e138['sources'],
                        "trust_level": _e138['trust_level'],
                        "rejected": _e138['rejected'],
                    })
                    nxt.append(nid)
            frontier = [x for x in nxt if depth.get(x, 999) < up]
        # BFS xuống (trò)
        frontier = [dila_id]
        depth = {dila_id: 0}
        seen_dn = {dila_id}
        while frontier:
            nxt = []
            for pid in frontier:
                if depth[pid] >= down:
                    continue
                nb, _cnt = _t86_neighbors(conn, pid, 'down')
                for nbv in nb:
                    nid = nbv['id']
                    if nid in seen_dn:
                        continue
                    seen_dn.add(nid)
                    depth[nid] = depth[pid] + 1
                    nodes.setdefault(nid, _t86_person_info(conn, nid))
                    node_origin.setdefault(nid, _t86_origin_place(conn, nid))
                    _e138 = _t138_edge_assertions(conn, pid, nid)
                    edges.append({
                        "from": pid, "to": nid, "direction": "student",
                        "relation_type": "da:isTeacherOf", "ref": nbv['ref'],
                        "has_ref": bool(nbv['ref']), "derived": False,
                        "sources": _e138['sources'],
                        "trust_level": _e138['trust_level'],
                        "rejected": _e138['rejected'],
                    })
                    nxt.append(nid)
            frontier = [x for x in nxt if depth.get(x, 999) < down]

        # đánh dấu expandable (còn thầy/trò ngoài độ sâu) để lazy mở sâu
        for pid in list(nodes.keys()):
            _, uc = _t86_neighbors(conn, pid, 'up')
            _, dc = _t86_neighbors(conn, pid, 'down')
            if uc > 0 and depth.get(pid, 0) >= up:
                up_excess.add(pid)
            if dc > 0 and depth.get(pid, 0) >= down:
                down_excess.add(pid)

        # enrich nodes: conflicts + origin + display_name + expandable flags
        for pid, nd in nodes.items():
            nd['conflicts'] = _t86_person_conflict(conn, pid)
            nd['origin_place'] = node_origin.get(pid) or _t86_origin_place(conn, pid)
            nd['has_more_up'] = pid in up_excess
            nd['has_more_down'] = pid in down_excess
            nd['display_name'] = _t86_resolve_display_name(conn, pid, nd)

        # T138 — lọc cạnh rejected khỏi Pháp mạch chuẩn (chỉ hiện tab mở rộng).
        active_edges = [e for e in edges if not e.get('rejected')]

        return jsonify({
            "ok": True, "entity_type": "person", "person_id": dila_id,
            "center": center, "up": up, "down": down,
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA",
            "nodes": list(nodes.values()),
            "edges": active_edges,
        })
    except Exception as e:
        app.logger.error(f"api_monk_lineage_tree error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/daoanh/api/monk/<dila_id>/root-ancestor')
def api_monk_root_ancestor(dila_id):
    """GET /daoanh/api/monk/<dila_id>/root-ancestor
    BFS lên (thầy) từ dila_id đến khi không còn thầy → trả về khai tổ (root nodes).
    Mục đích: tìm vị khai tổ của tông phái đang hiển thị trong Pháp Mạch.
    Max 60 bước để tránh vòng lặp vô hạn."""
    conn = get_db_connection()
    try:
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone()
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
                nb, _ = _t86_neighbors(conn, pid, 'up')
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


# ── T152 — Ancestor Spine: chuỗi thầy đầy đủ ngược lên đầu mạch ────────────────────
# Vấn đề: api_monk_lineage_tree clamp up/down [0,6] + client hardcode up=2 → Pháp Mạch
# chỉ hiển thị ≤2 đời tổ. Endpoint này đi bộ teacher-chain (marcus_networks up) KHÔNG
# clamp theo giới hạn đời — tới khi hết thầy (root) / cạnh bị reject / chạm safety 80 hops.
# Mirror tiêu chí T152: 0 ALTER, 0 Schema, 0 DB write, chỉ đọc cạnh verified (0 rejected).
@app.route('/daoanh/api/monk/<dila_id>/ancestor-spine')
def api_monk_ancestor_spine(dila_id):
    """GET /daoanh/api/monk/<dila_id>/ancestor-spine?max_hops=80
    Chuỗi tổ sư (ancestor spine) từ dila_id ngược lên đầu mạch, KHÔNG bị cắt ở 2/3 đời:
      - Đi bộ teacher-chain qua _t86_neighbors(conn, pid, 'up') (marcus_networks student→teacher).
      - Lọc cạnh rejected qua _t138_edge_assertions (mirror api_monk_lineage_tree active_edges).
      - Safety max_hops (mặc định 80) + cycle-safe (seen set) — T151 A6/A7.
      - break_reason: 'root' (hết thầy) | 'rejected' (còn thầy nhưng cạnh bị reject —
        "Mạch thiếu cạnh đã xác minh") | 'safety' (chạm giới hạn hops).
    Trả nodes (chỉ spine) + edges (chỉ non-rejected) + ancestors [gần→xa] + break_reason."""
    conn = get_db_connection()
    try:
        try:
            max_hops = max(1, min(int(request.args.get('max_hops', 80)), 80))
        except (TypeError, ValueError):
            max_hops = 80
        exists = conn.execute("SELECT 1 FROM people WHERE id=?", (dila_id,)).fetchone()
        if not exists:
            return jsonify({"ok": False, "error": "person not found"}), 404

        nodes = {}
        edges = []
        ancestors = []        # gần → xa (chính là chuỗi thầy)
        seen = {dila_id}
        cur = dila_id
        break_reason = 'root'
        hops = 0

        while hops < max_hops:
            cur_person = _t86_person_info(conn, cur)
            cur_person['conflicts'] = _t86_person_conflict(conn, cur)
            cur_person['origin_place'] = _t86_origin_place(conn, cur)
            cur_person['display_name'] = _t86_resolve_display_name(conn, cur, cur_person)
            nodes.setdefault(cur, cur_person)

            nb, _cnt = _t86_neighbors(conn, cur, 'up')
            if not nb:
                break_reason = 'root'
                break
            # chọn thầy đầu tiên không bị reject (ưu tiên giữ mạch verified)
            nxt = None
            nxt_ref = ''
            for nbv in nb:
                nid = nbv['id']
                if nid in seen:
                    continue
                _e138 = _t138_edge_assertions(conn, nid, cur)
                if _e138.get('rejected'):
                    continue
                nxt = nid
                nxt_ref = nbv.get('ref') or ''
                _e138n = _e138
                break
            if nxt is None:
                # còn thầy ở trên nhưng mọi cạnh bị reject → dừng HONEST
                break_reason = 'rejected'
                break
            _e138 = _e138n
            nid = nxt
            seen.add(nid)
            edges.append({
                "from": nid, "to": cur, "direction": "teacher",
                "relation_type": "da:isTeacherOf", "ref": nxt_ref,
                "has_ref": bool(nxt_ref), "derived": False,
                "sources": _e138.get('sources', []),
                "trust_level": _e138.get('trust_level'),
                "rejected": False,
            })
            ancestors.append(nid)
            hops += 1
            cur = nid
        if hops >= max_hops and break_reason == 'root':
            break_reason = 'safety'

        # thêm node đầu mạch (đã thêm cur_trong while ở vòng sau — đảm bảo tồn tại)
        last_person = _t86_person_info(conn, cur)
        last_person['conflicts'] = _t86_person_conflict(conn, cur)
        last_person['origin_place'] = _t86_origin_place(conn, cur)
        last_person['display_name'] = _t86_resolve_display_name(conn, cur, last_person)
        nodes.setdefault(cur, last_person)

        return jsonify({
            "ok": True, "entity_type": "person", "person_id": dila_id,
            "center": nodes.get(dila_id),
            "ancestors": ancestors,          # gần → xa
            "nodes": list(nodes.values()),
            "edges": edges,
            "break_reason": break_reason,
            "hops": hops, "max_hops": max_hops,
            "has_more_up": break_reason in ('rejected', 'safety'),
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA",
        })
    except Exception as e:
        app.logger.error(f"api_monk_ancestor_spine error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/daoanh/api/lineage-ref/passage')
def api_lineage_ref_passage():
    """GET /daoanh/api/lineage-ref/passage?ref=... — resolve dẫn chiếu CBETA (từ edge
    marcus_networks.ref) → passage (mở Đọc trong Đại Tạng). Trung thực null nếu passage
    chưa được lập chỉ mục trong bảng passage."""
    ref = request.args.get('ref', '')
    conn = get_db_connection()
    try:
        result = _t86_parse_ref_passage(conn, ref)
        return jsonify({"ok": True, "resolved": result or {"found": False, "message": "Thiếu ref"}})
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


@app.route('/daoanh/api/relation/translate', methods=['POST'])
def api_relation_translate():
    """POST /daoanh/api/relation/translate — dịch AI đoạn dẫn chứng quan hệ (T128).

    body {ref, relation_id?, from_id?, to_id?, direction?}
    - Cache hit (translation_cache.source_hash = sha256(excerpt)[:24], source_type='relation_evidence')
      → trả ngay, KHÔNG gọi LLM.
    - Miss → Groq qwen (T73 _t73_build_style_prompt + _t73_call_gemini) → write-through
      translation_cache status='draft'.
    KHÔNG dùng legacy /api/translate (Claude, cần passage_id — evidence không có)."""
    data = request.get_json(silent=True) or {}
    ref = data.get('ref') or ''
    from_id = data.get('from_id') or ''
    to_id = data.get('to_id') or ''
    direction = data.get('direction') or ''
    relation_id = data.get('relation_id') or ''
    if not ref.strip():
        return jsonify({"ok": False, "error": "Thiếu dẫn chứng (ref)"}), 400

    parsed = _t128_parse_relation_ref(ref, from_id, to_id, direction)
    excerpt = parsed['original_excerpt']
    if not excerpt.strip():
        return jsonify({
            "ok": False,
            "error": "Dẫn chứng không có đoạn trích Hán văn để dịch (chỉ có URL/địa chỉ thư mục).",
            "parsed": parsed}), 422

    conn = get_db_connection()
    try:
        src_hash = parsed['text_hash'] or _t73_source_hash(excerpt.strip())
        existing = conn.execute(
            "SELECT id, translated_text, status, model_id, rules_version FROM translation_cache "
            "WHERE source_hash=? AND source_type='relation_evidence' AND status!='invalidated' "
            "ORDER BY id DESC LIMIT 1", (src_hash,)).fetchone()
        if existing:
            return jsonify({
                "ok": True, "from_cache": True, "translation_id": existing['id'],
                "translated_text": existing['translated_text'],
                "status": existing['status'], "model_id": existing['model_id'],
                "rules_version": existing['rules_version'], "parsed": parsed})

        # Cache miss → Groq (nhánh T123 Style Constitution)
        xs = excerpt.strip()
        prompt_src = xs if len(xs) <= 1400 else xs[:1400]
        prompt = _t73_build_style_prompt(prompt_src, _t73_style_lock(conn), label='đoạn dẫn chứng')
        vi, model_id, err_type = _t73_call_gemini(prompt)
        if not vi:
            return jsonify({
                "ok": False, "error_type": err_type or 'api_error',
                "error": "Dịch thất bại — thử lại sau.", "parsed": parsed}), 503

        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)
        now = datetime.now().isoformat()
        ent_id = parsed['relation_id'] or relation_id
        cur = conn.execute("""
            INSERT OR REPLACE INTO translation_cache
              (source_hash, source_type, entity_id, source_text, translated_text,
               model_id, rules_version, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,'draft',?,?)
        """, (src_hash, 'relation_evidence', ent_id, excerpt.strip(), vi, model_id, rv, now, now))
        conn.commit()

        return jsonify({
            "ok": True, "from_cache": False, "translation_id": cur.lastrowid,
            "translated_text": vi, "status": 'draft', "model_id": model_id,
            "rules_version": rv, "parsed": parsed})
    except Exception as e:
        app.logger.error(f"api_relation_translate error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/daoanh/api/lineage-ref/context')
def api_lineage_ref_context():
    """GET /daoanh/api/lineage-ref/context?ref=... — văn cảnh ±1 đoạn quanh passage đã
    resolve từ dẫn chiếu Marcus (T128 'Đọc văn cảnh'). Fallback trung thực khi passage
    chưa được lập chỉ mục (vd T47n1990 — không backfill)."""
    ref = request.args.get('ref', '')
    conn = get_db_connection()
    try:
        parsed = _t128_parse_relation_ref(ref)
        resolved = _t86_parse_ref_passage(conn, ref)
        context = []
        if resolved and resolved.get('found') and resolved.get('passage_id'):
            pid = resolved['passage_id']
            tid = resolved['text_id']
            cur = conn.execute(
                "SELECT passage_id, text_id, loc_ref, raw_text FROM passage WHERE passage_id=?",
                (pid,)).fetchone()
            if cur:
                context.append({'passage_id': cur['passage_id'], 'text_id': cur['text_id'],
                                'loc_ref': cur['loc_ref'], 'raw_text': cur['raw_text']})
                prv = conn.execute(
                    "SELECT passage_id, text_id, loc_ref, raw_text FROM passage "
                    "WHERE text_id=? AND passage_id<? ORDER BY passage_id DESC LIMIT 1",
                    (tid, pid)).fetchone()
                if prv:
                    context.insert(0, {'passage_id': prv['passage_id'], 'text_id': prv['text_id'],
                                       'loc_ref': prv['loc_ref'], 'raw_text': prv['raw_text']})
                nxt = conn.execute(
                    "SELECT passage_id, text_id, loc_ref, raw_text FROM passage "
                    "WHERE text_id=? AND passage_id>? ORDER BY passage_id ASC LIMIT 1",
                    (tid, pid)).fetchone()
                if nxt:
                    context.append({'passage_id': nxt['passage_id'], 'text_id': nxt['text_id'],
                                    'loc_ref': nxt['loc_ref'], 'raw_text': nxt['raw_text']})
        return jsonify({"ok": True, "parsed": parsed, "resolved": resolved, "context": context})
    except Exception as e:
        app.logger.error(f"api_lineage_ref_context error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()




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


@app.route('/daoanh/api/nexus/<entity_id>')
def api_nexus(entity_id):
    """GET /daoanh/api/nexus/<entity_id>?type=person|place

    Event-centric nexus: entity → EVENT → TEXT (passage với citation thật) → TIME
    (year / era). Cùng shape nodes/edges như các graph khác nên places.html tái dùng
    _renderVisGraph. Edge nào cũng có tooltip nguồn (cbeta_ref hoặc source_ref).
    """
    etype = request.args.get('type', 'place')
    conn = get_db_connection()
    try:
        # ── Center label ──
        if etype == 'person':
            p = conn.execute("SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (entity_id,)).fetchone()
            if not p:
                return jsonify({"ok": False, "error": "person not found"}), 404
            mr = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id = ?", (entity_id,)).fetchone()
            label_zh = (mr['label'] if mr else None) or p['name_zh']
            label_vi = p['name_vi'] or (mr['label_vi'] if mr else None)
            disp = _t86_resolve_display_name(conn, entity_id, {'name_vi': label_vi, 'name_zh': label_zh})
            center = {"id": entity_id, "label": disp['primary'], "label_vi": disp['primary'],
                      "label_zh": disp['secondary'] or label_zh, "is_formal_name": disp['is_formal_name']}
        else:
            pl = conn.execute("SELECT id, name, name_zh FROM places_dila WHERE id = ?", (entity_id,)).fetchone()
            if not pl:
                return jsonify({"ok": False, "error": "place not found"}), 404
            vi = conn.execute("SELECT name_vi FROM namevi_map_places WHERE dila_id = ?", (entity_id,)).fetchone()
            # T101 BUG-001: label_zh dùng places_dila.name (tên chính thức DILA), không phải name_zh
            _pl_label_zh = pl['name'] or pl['name_zh']
            center = {"id": entity_id,
                      "label": (vi['name_vi'] if vi else None) or _pl_label_zh,
                      "label_vi": (vi['name_vi'] if vi else None),
                      "label_zh": _pl_label_zh}

        # ── Sự kiện từ event_text_link (bridge Commit 2) ──
        if etype == 'person':
            events = conn.execute(
                "SELECT * FROM event_text_link WHERE entity_type = 'person' AND entity_id = ?",
                (entity_id,)).fetchall()
        else:
            events = conn.execute(
                "SELECT * FROM event_text_link WHERE "
                "(event_type IN ('place_founding','place_dissolved') AND entity_id = ?) "
                "OR (event_type = 'person_place' AND related_id = ?)",
                (entity_id, entity_id)).fetchall()

        nodes, edges = [], []
        seen_nodes = {entity_id, 'center'}

        def _add_node(nid, label, label_zh, group, navigable=False, label_vi=None):
            if nid in seen_nodes:
                return
            seen_nodes.add(nid)
            nodes.append({"id": nid, "label": label, "label_vi": label_vi, "label_zh": label_zh,
                          "group": group, "navigable": navigable})

        # ── Duyệt từng sự kiện → event node, text node, time node ──
        for ev in events:
            et = ev['event_type']
            eid = f"ev-{ev['source_table']}-{ev['id']}"
            if et == 'person_place':
                # person_place: entity_id = person, related_id = place (bất biến từ ETL Commit 2).
                pid = ev['entity_id']
                placeid = ev['related_id']
                if etype == 'person':
                    # center = person → thêm node place (navigable → chuyển sang địa danh)
                    _add_node(placeid, None, None, 'place', navigable=True)
                    _add_node(eid, 'cư trú tại', 'cư trú tại', 'event')
                    edges.append({"from": entity_id, "to": eid, "label": '—', "ref": None})
                    edges.append({"from": eid, "to": placeid, "label": 'cư trú tại',
                                  "ref": ev['source_book'] or None})
                else:
                    # center = place → thêm node person (navigable → chuyển sang nhân vật)
                    if pid:
                        # A=1: pid thật (DILA person id).
                        _add_node(pid, None, None, 'person', navigable=True)
                        person_ref = pid
                    else:
                        # A=1: entity_id NULL → dùng related_name làm label (tên Hán) +
                        # synthetic id (không navigable — không có hồ sô để chuyển sang).
                        # Tránh collision id với event node eid.
                        _add_node(f"pers-{ev['id']}", ev['related_name'], ev['related_name'],
                                  'person', navigable=False)
                        person_ref = f"pers-{ev['id']}"
                    _add_node(eid, 'hiện diện', 'hiện diện', 'event')
                    edges.append({"from": person_ref, "to": eid, "label": '—', "ref": None,
                                  "evidence_type": "unverified"})
                    src = ev['source_book'] or None
                    edges.append({"from": eid, "to": entity_id, "label": 'hiện diện',
                                  "ref": src,
                                  "evidence_type": "partial" if src else "unverified",
                                  "partial_reason": "Chưa có CBETA locator cụ thể" if src else None})
            else:
                # place_founding / place_dissolved → time (year) node
                et_name = {'place_founding': 'pháp duyên sáng lập',
                           'place_dissolved': 'giải tán'}.get(et, et)
                _add_node(eid, et_name, et_name, 'event')
                src_ref = ev['source_ref'] or None
                edges.append({"from": entity_id, "to": eid, "label": et_name, "ref": src_ref,
                              "evidence_type": "with_evidence" if src_ref else "unverified"})
                if ev['year']:
                    tid = f"time-{eid}"
                    _add_node(tid, str(ev['year']), str(ev['year']), 'time')
                    edges.append({"from": eid, "to": tid, "label": 'năm', "ref": src_ref,
                                  "evidence_type": "with_evidence" if src_ref else "unverified"})

            # ── passage (text) node từ cbeta_ref ──
            if ev['cbeta_ref']:
                sigla = ev['cbeta_ref'].split('_')[0] if '_' in ev['cbeta_ref'] else ev['cbeta_ref']
                title = _nexus_title_for_sigla(conn, sigla, ev['source_book'])
                tid = f"txt-{sigla}-{ev['id']}"
                _add_node(tid, title, title, 'text')
                edges.append({
                    "from": eid, "to": tid, "label": 'trích dẫn',
                    "ref": ev['cbeta_ref'],
                    "citation": ev['cbeta_ref'],
                    "evidence_type": "with_evidence",
                })

        # ── fill label_zh cho node place/person chưa có label ──
        # (tra cứu nhanh từ places_dila / marcus_reference)
        if etype == 'person':
            for n in nodes:
                if n.get('group') == 'place' and not n.get('label'):
                    r = conn.execute("SELECT name, name_zh FROM places_dila WHERE id = ?", (n['id'],)).fetchone()
                    if r:
                        vi = conn.execute("SELECT name_vi FROM namevi_map_places WHERE dila_id = ?", (n['id'],)).fetchone()
                        n['label'] = (vi['name_vi'] if vi else None) or r['name'] or r['name_zh']
                        n['label_vi'] = (vi['name_vi'] if vi else None)
                        n['label_zh'] = r['name_zh']
        else:
            for n in nodes:
                if n.get('group') == 'person' and not n.get('label'):
                    r = conn.execute("SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (n['id'],)).fetchone()
                    if r:
                        mr2 = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id = ?", (n['id'],)).fetchone()
                        z = (mr2['label'] if mr2 else None) or r['name_zh']
                        n['label'] = r['name_vi'] or z
                        n['label_vi'] = r['name_vi'] or (mr2['label_vi'] if mr2 else None)
                        n['label_zh'] = z
                        n['dynasty'] = r['dynasty']

        # Aliases + Groups (Nexus grouped view)
        import re as _re
        aliases = []
        groups = {}
        if etype == 'person':
            seen_a = {center.get('label', ''), center.get('label_zh', '')}
            prow = conn.execute("SELECT name_zh, name_vi FROM people WHERE id=?", (entity_id,)).fetchone()
            mrrow = conn.execute("SELECT label, label_vi FROM marcus_reference WHERE node_id=?", (entity_id,)).fetchone()
            for v in (list(prow) if prow else []) + (list(mrrow) if mrrow else []):
                if v and (v2 := str(v).strip()) and v2 not in seen_a:
                    aliases.append(v2); seen_a.add(v2)
            cbeta_row = conn.execute("""
                SELECT COUNT(DISTINCT CASE WHEN INSTR(cbeta_ref,'_')>0
                       THEN SUBSTR(cbeta_ref,1,INSTR(cbeta_ref,'_')-1) ELSE cbeta_ref END) as cnt
                FROM event_text_link WHERE entity_id=? AND cbeta_ref IS NOT NULL
            """, (entity_id,)).fetchone()
            marcus_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM marcus_networks WHERE teacher_id=? OR student_id=?",
                (entity_id, entity_id)).fetchone()
            dila_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM people WHERE id=?", (entity_id,)).fetchone()
            groups = {
                'kinh_dien': {'CBETA': (cbeta_row['cnt'] if cbeta_row else 0)},
                'tang_nhan': {
                    'Marcus': (marcus_row['cnt'] if marcus_row else 0),
                    'DILA': (dila_row['cnt'] if dila_row else 0),
                },
            }
            # Add Marcus teacher/student relation nodes
            for rel in conn.execute("""
                SELECT teacher_id, student_id, teacher_label, student_label, ref
                FROM marcus_networks WHERE teacher_id=? OR student_id=?
            """, (entity_id, entity_id)).fetchall():
                is_t = rel['teacher_id'] == entity_id
                oid = rel['student_id'] if is_t else rel['teacher_id']
                olbl = rel['student_label'] if is_t else rel['teacher_label']
                # Line 1 Marcus (NEXUS-LBL-001): ưu tiên tên Việt đã có trong DB
                # (people.name_vi / marcus_reference.label_vi), không AI, không sửa nguồn;
                # label gốc (Hán) giữ ở label_zh.
                rv = conn.execute(
                    "SELECT p.name_vi, p.name_zh, COALESCE(mr.label_vi, '') AS mvi "
                    "FROM people p LEFT JOIN marcus_reference mr ON mr.node_id = p.id "
                    "WHERE p.id = ?", (oid,)).fetchone()
                if rv is not None:
                    _lvi = rv['name_vi'] or rv['mvi'] or None
                    _lzh = olbl or rv['name_zh']
                    _disp = _t86_resolve_display_name(conn, oid, {'name_vi': _lvi, 'name_zh': _lzh})
                    _add_node(oid, _disp['primary'], _disp['secondary'] or _lzh, 'person',
                              navigable=True, label_vi=_disp['primary'])
                else:
                    _add_node(oid, olbl, olbl, 'person', navigable=True)
                edges.append({"from": entity_id if is_t else oid,
                              "to": oid if is_t else entity_id,
                              "label": "",
                              "direction": "student" if is_t else "teacher",
                              "ref": rel['ref'], "source": "marcus"})
        elif etype == 'place':
            pl_xml_row = conn.execute(
                "SELECT raw_xml FROM places_dila WHERE id=?", (entity_id,)
            ).fetchone()
            if pl_xml_row and pl_xml_row['raw_xml']:
                seen_a = {center.get('label_zh', ''), center.get('label', '')}
                for m in _re.findall(r'<[^>]*[Pp]lace[Nn]ame[^>]*>([^<]{1,80})</', pl_xml_row['raw_xml']):
                    m = m.strip()
                    if m and m not in seen_a:
                        aliases.append(m)
                        seen_a.add(m)
            kd_row = conn.execute("""
                SELECT COUNT(DISTINCT
                    CASE WHEN INSTR(cbeta_ref,'_')>0
                         THEN SUBSTR(cbeta_ref,1,INSTR(cbeta_ref,'_')-1)
                         ELSE cbeta_ref END) as cnt
                FROM event_text_link
                WHERE event_type='person_place' AND related_id=? AND cbeta_ref IS NOT NULL
            """, (entity_id,)).fetchone()
            dyn_rows = conn.execute("""
                SELECT COALESCE(p.dynasty,'(không rõ)') as dynasty,
                       COUNT(DISTINCT etl.entity_id) as cnt
                FROM event_text_link etl
                JOIN people p ON p.id = etl.entity_id
                WHERE etl.event_type='person_place' AND etl.related_id=?
                GROUP BY p.dynasty ORDER BY cnt DESC
            """, (entity_id,)).fetchall()
            groups = {
                'kinh_dien': (kd_row['cnt'] if kd_row else 0),
                'tang_nhan': {r['dynasty']: r['cnt'] for r in dyn_rows},
                'tang_nhan_total': sum(r['cnt'] for r in dyn_rows),
            }
        return jsonify({
            "ok": True, "entity_type": etype, "entity_id": entity_id,
            "center": center, "source": "event_text_link (place_person_bibl + place_timeline_events)",
            "nodes": nodes, "edges": edges,
            "aliases": aliases, "groups": groups,
        })
    except Exception as e:
        app.logger.error(f"api_nexus error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


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

@app.route('/daoanh/api/places/<place_id>/persons')
def api_places_persons(place_id):
    """GET /daoanh/api/places/<id>/persons — T22/T28 (Nhân Vật tab).

    Three additive sources, all cited:
    1. `persons` — curated place_person_link rows (DILA person_id, clickable into Truyền Thừa).
    2. `wikidata_persons` — live Wikidata P112 ("founded by") lookup.
    3. `bio_persons` — auto-detected from people.bio text search using place name variants
       extracted from places_dila.raw_xml. Source = "DILA Tiểu Sử" (biographical authority).
       Confidence varies: "僧人/住持" context = high; passing mentions = lower.
    """
    conn = get_db_connection()
    try:
        _ensure_place_person_link_table(conn)
        _ensure_geo_cross_ref_table(conn)

        rows = conn.execute("""
            SELECT l.person_id, l.relation_type, l.source_name, l.source_url, l.note,
                   p.name_zh, p.name_vi, p.dynasty, p.bio_vi
            FROM place_person_link l JOIN people p ON p.id = l.person_id
            WHERE l.place_id = ?
            ORDER BY l.created_at ASC
        """, (place_id,)).fetchall()
        persons = []
        for r in rows:
            has_marcus = conn.execute(
                "SELECT 1 FROM marcus_people_link WHERE person_id = ?", (r['person_id'],)
            ).fetchone() is not None
            marcus_label = conn.execute(
                "SELECT label FROM marcus_reference WHERE node_id = ?", (r['person_id'],)
            ).fetchone()
            persons.append({
                "id": r['person_id'], "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                "marcus_label": marcus_label['label'] if marcus_label else None,
                "dynasty": r['dynasty'], "relation_type": r['relation_type'],
                "source_name": r['source_name'], "source_url": r['source_url'], "note": r['note'],
                "bio_vi": r['bio_vi'] or None,
                "has_lineage": has_marcus
            })

        wikidata_persons = []
        dila_id, _ = _resolve_dila_id(conn, place_id)
        xref = conn.execute(
            "SELECT wikidata_qid, bdrc_id FROM geo_cross_ref WHERE dila_id = ?", (dila_id or place_id,)
        ).fetchone()
        if xref and xref['wikidata_qid']:
            qid = xref['wikidata_qid']
            for f in _fetch_wikidata_founders(qid):
                wikidata_persons.append({
                    "wikidata_qid": f['wikidata_qid'], "label": f['label'], "label_zh": f.get('label_zh'),
                    "relation_type": "founded by (Wikidata P112)",
                    "source_name": f"Wikidata {qid}",
                    "source_url": f"https://www.wikidata.org/wiki/{qid}",
                })
        # ── Source 3: bio text search from DILA Person Authority ────────────────
        # Uses pre-computed cache (T43) if available; falls back to real-time LIKE.
        bio_persons = []
        try:
            target_pid = dila_id or place_id
            linked_ids = {p['id'] for p in persons}
            # Try cache first (T43 pre-compute)
            cache_rows = conn.execute("""
                SELECT ppbc.person_id, ppbc.matched_variant, ppbc.is_direct,
                       ppbc.relation_hint, ppbc.bio_snippet, ppbc.confidence,
                       p.name_zh, p.name_vi, p.dynasty, p.bio_vi
                FROM place_person_bio_cache ppbc
                JOIN people p ON p.id = ppbc.person_id
                WHERE ppbc.place_id = ?
                ORDER BY ppbc.is_direct DESC, p.dynasty
                LIMIT 200
            """, (target_pid,)).fetchall()

            if cache_rows:
                for cr in cache_rows:
                    if cr['person_id'] in linked_ids:
                        continue
                    has_marcus = conn.execute(
                        "SELECT 1 FROM marcus_people_link WHERE person_id=?", (cr['person_id'],)
                    ).fetchone() is not None
                    marcus_label_row = conn.execute(
                        "SELECT label FROM marcus_reference WHERE node_id=?", (cr['person_id'],)
                    ).fetchone()
                    mv = cr['matched_variant'] or ''
                    is_direct = bool(cr['is_direct'])
                    bio_persons.append({
                        "id": cr['person_id'],
                        "name_zh": cr['name_zh'],
                        "name_vi": cr['name_vi'],
                        "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                        "dynasty": cr['dynasty'],
                        "relation_type": "住持/僧人 @ " + mv if is_direct else "đề cập @ " + mv,
                        "source_name": "DILA Tiểu Sử (tự động)",
                        "source_url": f"https://authority.dila.edu.tw/person/?val={cr['person_id']}",
                        "note": cr['bio_snippet'] or '',
                        "bio_vi": cr['bio_vi'] or None,
                        "has_lineage": has_marcus,
                        "is_direct": is_direct,
                    })
            else:
                # Fallback: real-time LIKE (for places not yet in cache)
                place_row = conn.execute(
                    "SELECT raw_xml, name_zh FROM places_dila WHERE id=?", (target_pid,)
                ).fetchone()
                if place_row and place_row['raw_xml']:
                    import re as _re
                    name_variants = _re.findall(
                        r'<[^:]*:?placeName[^>]*>([^<]{1,40})</[^:]*:?placeName>',
                        place_row['raw_xml']
                    )
                    if place_row['name_zh']:
                        name_variants.append(place_row['name_zh'])
                    seen_v = set()
                    uniq_variants = []
                    for v in name_variants:
                        v = v.strip()
                        if v and len(v) >= 2 and v not in seen_v:
                            seen_v.add(v)
                            uniq_variants.append(v)
                    if uniq_variants:
                        uniq_variants.sort(key=len, reverse=True)
                        like_clauses = ' OR '.join(['bio LIKE ?'] * len(uniq_variants))
                        like_params = [f'%{v}%' for v in uniq_variants]
                        bio_rows = conn.execute(
                            f"SELECT id, name_zh, name_vi, dynasty, bio, bio_vi FROM people "
                            f"WHERE bio IS NOT NULL AND ({like_clauses}) LIMIT 200",
                            like_params
                        ).fetchall()
                        direct_keywords = ['僧人', '住持', '方丈', '上座', '寺主', '書記',
                                           '首座', '出家', '居', '嗣法', '中興', '開山']
                        for br in bio_rows:
                            if br['id'] in linked_ids:
                                continue
                            bio_text = br['bio'] or ''
                            snippet = ''
                            matched_variant = ''
                            for v in uniq_variants:
                                idx = bio_text.find(v)
                                if idx >= 0:
                                    matched_variant = v
                                    snippet = bio_text[max(0, idx-20):idx+len(v)+60].strip()
                                    break
                            ctx = bio_text[max(0, bio_text.find(matched_variant)-60):
                                           bio_text.find(matched_variant)+80] if matched_variant else ''
                            is_direct = any(kw in ctx for kw in direct_keywords)
                            has_marcus = conn.execute(
                                "SELECT 1 FROM marcus_people_link WHERE person_id=?", (br['id'],)
                            ).fetchone() is not None
                            marcus_label_row = conn.execute(
                                "SELECT label FROM marcus_reference WHERE node_id=?", (br['id'],)
                            ).fetchone()
                            bio_persons.append({
                                "id": br['id'],
                                "name_zh": br['name_zh'],
                                "name_vi": br['name_vi'],
                                "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                                "dynasty": br['dynasty'],
                                "relation_type": "住持/僧人 @ " + matched_variant if is_direct else "đề cập @ " + matched_variant,
                                "source_name": "DILA Tiểu Sử (tự động)",
                                "source_url": f"https://authority.dila.edu.tw/person/?val={br['id']}",
                                "note": snippet,
                                "bio_vi": br['bio_vi'] or None,
                                "has_lineage": has_marcus,
                                "is_direct": is_direct,
                            })
            bio_persons.sort(key=lambda x: (0 if x['is_direct'] else 1, x['dynasty'] or ''))
        except Exception as bio_err:
            app.logger.warning(f"bio_persons search failed: {bio_err}")

        # ── Source 4: DILA Place Authority listBibl (T39) ──────────────────────
        bibl_persons = []
        try:
            bibl_rows = conn.execute("""
                SELECT ppb.person_id, ppb.person_name_raw, ppb.cbeta_ref,
                       ppb.source_book, ppb.mention_keyword, ppb.confidence,
                       p.name_zh, p.name_vi, p.dynasty
                FROM place_person_bibl ppb
                LEFT JOIN people p ON p.id = ppb.person_id
                WHERE ppb.place_id = ? AND ppb.person_id IS NOT NULL
                ORDER BY ppb.confidence DESC, ppb.source_book, ppb.person_name_raw
                LIMIT 150
            """, (dila_id or place_id,)).fetchall()
            linked_ids_all = {p['id'] for p in persons} | {p['id'] for p in bio_persons}
            for br in bibl_rows:
                if br['person_id'] in linked_ids_all:
                    continue
                has_marcus = conn.execute(
                    "SELECT 1 FROM marcus_people_link WHERE person_id=?", (br['person_id'],)
                ).fetchone() is not None
                marcus_label_row = conn.execute(
                    "SELECT label FROM marcus_reference WHERE node_id=?", (br['person_id'],)
                ).fetchone()
                kw = br['mention_keyword'] or ''
                cbeta_ref = br['cbeta_ref'] or ''
                bibl_persons.append({
                    "id": br['person_id'],
                    "name_zh": br['name_zh'] or br['person_name_raw'],
                    "name_vi": br['name_vi'],
                    "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                    "dynasty": br['dynasty'],
                    "relation_type": f"CBETA @ {kw}" if kw else "CBETA",
                    "source_name": br['source_book'] or "DILA CBETA Bibl",
                    "source_url": f"https://cbetaonline.dila.edu.tw/zh/{cbeta_ref}" if cbeta_ref else "https://cbeta.org",
                    "note": f"{br['source_book']} {cbeta_ref}",
                    "has_lineage": has_marcus,
                    "cbeta_ref": cbeta_ref,
                    "confidence": br['confidence'],
                })
        except Exception as bibl_err:
            app.logger.warning(f"bibl_persons query failed: {bibl_err}")

        # ── Source 5: DILA Person Authority placeOfOrigin (T41) ────────────────
        origin_persons = []
        try:
            all_linked_ids = (
                {p['id'] for p in persons}
                | {p['id'] for p in bio_persons}
                | {p.get('id') for p in bibl_persons if p.get('id')}
            )
            origin_rows = conn.execute("""
                SELECT pol.person_id, pol.confidence,
                       p.name_zh, p.name_vi, p.dynasty
                FROM person_origin_link pol
                JOIN people p ON p.id = pol.person_id
                WHERE pol.place_id = ?
                ORDER BY pol.confidence DESC, p.dynasty, p.name_zh
                LIMIT 100
            """, (dila_id or place_id,)).fetchall()
            for or_ in origin_rows:
                if or_['person_id'] in all_linked_ids:
                    continue
                marcus_label_row = conn.execute(
                    "SELECT label FROM marcus_reference WHERE node_id=?", (or_['person_id'],)
                ).fetchone()
                has_marcus = conn.execute(
                    "SELECT 1 FROM marcus_people_link WHERE person_id=?", (or_['person_id'],)
                ).fetchone() is not None
                origin_persons.append({
                    "id": or_['person_id'],
                    "name_zh": or_['name_zh'],
                    "name_vi": or_['name_vi'],
                    "marcus_label": marcus_label_row['label'] if marcus_label_row else None,
                    "dynasty": or_['dynasty'],
                    "relation_type": "sinh tại / 籍貫",
                    "source_name": "DILA Person Authority",
                    "source_url": f"https://authority.dila.edu.tw/person/?fromInner={or_['person_id']}",
                    "note": "quê quán",
                    "confidence": or_['confidence'],
                    "has_lineage": has_marcus,
                })
        except Exception as origin_err:
            app.logger.warning(f"origin_persons query failed: {origin_err}")

        if not persons and not wikidata_persons and not bio_persons and not bibl_persons and not origin_persons:
            return jsonify({
                "ok": True, "status": "pending", "place_id": place_id,
                "persons": [], "wikidata_persons": [], "bio_persons": [],
                "bibl_persons": [], "origin_persons": [],
                "message": "Chưa có liên kết nhân vật đã xác minh cho địa danh này.",
                "research_directions": [
                    "Wikidata P112 (founded by) — xây bridge geo_cross_ref.wikidata_qid cho địa danh này",
                    "Admin curation thủ công qua place_person_link (source_url bắt buộc)",
                ]
            })
        return jsonify({"ok": True, "status": "ok", "place_id": place_id,
                        "persons": persons, "wikidata_persons": wikidata_persons,
                        "bio_persons": bio_persons, "bibl_persons": bibl_persons,
                        "origin_persons": origin_persons})
    except Exception as e:
        app.logger.error(f"api_places_persons error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


# ============================================================
#  T51 — Nhân Vật Học Portal (additive, đọc-only)
# ============================================================
@app.route('/daoanh/api/persons/browse')
def api_persons_browse():
    """GET /daoanh/api/persons/browse — T51a: Duyệt nhân vật độc lập (portal).

    Standalone person-browse for the Nhân Vật tab on home.html — KHÔNG đụng
    route /api/places/<id>/persons (place-centric, T28). Chỉ đọc `people` +
    JOIN `marcus_people_link` (lineage) + đếm `place_person_link` / `person_origin_link`.

    Query params:
      q          — tìm theo name_vi / name_zh (LIKE, không dấu-insensitive tiếng Việt)
      dynasty    — lọc theo dynasty (chính xác)
      sect       — lọc theo sect (chính xác)
      has_lineage — '1' chỉ lấy người có Marcus lineage, '0' ngược lại
      page (1)   — trang
      limit (24) — số dòng/trang (max 100)
      sort       — 'name' | 'dynasty' | 'places' (mặc định dynasty)
    """
    conn = get_db_connection()
    try:
        q = (request.args.get('q') or '').strip()
        dynasty = (request.args.get('dynasty') or '').strip()
        sect = (request.args.get('sect') or '').strip()
        hl = (request.args.get('has_lineage') or '').strip()
        page = max(1, int(request.args.get('page') or 1))
        limit = min(100, max(1, int(request.args.get('limit') or 24)))
        sort = (request.args.get('sort') or 'dynasty').strip()
        offset = (page - 1) * limit

        where, params = [], []
        if q:
            where.append("(p.name_vi LIKE ? OR p.name_zh LIKE ? OR p.name_en LIKE ?)")
            like = f"%{q}%"
            params += [like, like, like]
        if dynasty:
            where.append("p.dynasty = ?")
            params.append(dynasty)
        if sect:
            where.append("p.sect = ?")
            params.append(sect)
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""

        # helpers: has_lineage, place & origin counts — dùng subquery để không nhân dòng
        count_sql = f"""
            SELECT COUNT(*) AS c FROM people p
            {where_sql}
            {(" AND p.id IN (SELECT person_id FROM marcus_people_link)" if hl == '1' else "")}
            {(" AND p.id NOT IN (SELECT person_id FROM marcus_people_link)" if hl == '0' else "")}
        """
        total = conn.execute(count_sql, params).fetchone()['c']

        order_map = {
            'name': "p.name_vi COLLATE NOCASE, p.name_zh",
            'dynasty': "p.dynasty IS NULL, p.dynasty, p.name_vi COLLATE NOCASE",
            'places': "(SELECT COUNT(*) FROM place_person_link pl WHERE pl.person_id = p.id) DESC",
        }
        order_sql = order_map.get(sort, order_map['dynasty'])

        base_sql = f"""
            SELECT
                p.id, p.name_zh, p.name_vi, p.name_en, p.sect, p.dynasty,
                p.birth_year, p.death_year, p.source_origin,
                (SELECT COUNT(*) FROM place_person_link pl WHERE pl.person_id = p.id) AS place_count,
                (SELECT COUNT(*) FROM person_origin_link pol WHERE pol.person_id = p.id) AS origin_count,
                EXISTS(SELECT 1 FROM marcus_people_link mpl WHERE mpl.person_id = p.id) AS has_lineage,
                substr(COALESCE(p.bio, ''), 1, 220) AS bio_preview
            FROM people p
            {where_sql}
            {(" AND p.id IN (SELECT person_id FROM marcus_people_link)" if hl == '1' else "")}
            {(" AND p.id NOT IN (SELECT person_id FROM marcus_people_link)" if hl == '0' else "")}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(base_sql, params + [limit, offset]).fetchall()

        persons = []
        for r in rows:
            persons.append({
                "id": r['id'],
                "name_zh": r['name_zh'], "name_vi": r['name_vi'], "name_en": r['name_en'],
                "sect": r['sect'], "dynasty": r['dynasty'],
                "birth_year": r['birth_year'], "death_year": r['death_year'],
                "source_origin": r['source_origin'],
                "place_count": r['place_count'], "origin_count": r['origin_count'],
                "has_lineage": bool(r['has_lineage']),
                "bio_preview": r['bio_preview'],
            })

        # danh sách triều đại + sect để populate dropdown filter
        dynasties = [r[0] for r in conn.execute(
            "SELECT DISTINCT dynasty FROM people WHERE dynasty IS NOT NULL AND dynasty != '' ORDER BY dynasty").fetchall()]
        sects = [r[0] for r in conn.execute(
            "SELECT DISTINCT sect FROM people WHERE sect IS NOT NULL AND sect != '' ORDER BY sect").fetchall()]

        return jsonify({
            "ok": True,
            "total": total, "page": page, "pages": max(1, -(-total // limit)),
            "limit": limit, "persons": persons,
            "filters": {"dynasties": dynasties, "sects": sects},
            "counts": {
                "total_people": conn.execute("SELECT COUNT(*) AS c FROM people").fetchone()['c'],
                "with_lineage": conn.execute("SELECT COUNT(DISTINCT person_id) AS c FROM marcus_people_link").fetchone()['c'],
            }
        })
    except Exception as e:
        app.logger.error(f"api_persons_browse error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/daoanh/api/person/<dila_id>/profile')
def api_person_profile(dila_id):
    """GET /daoanh/api/person/<dila_id>/profile — T51b: tiểu sử nhân vật (portal).

    Kết hợp: people.bio + Marcus lineage (thầy/trò có CBETA citation) + địa danh
    liên quan (place_person_link, person_origin_link, place_person_bio_cache) + kinh
    điển (place_person_bibl). KHÔNG ghi đè bio panel place-centric sẵn có.

    Tái dùng /daoanh/api/monk/<id>/graph cho phả hệ (nodes/edges).
    """
    conn = get_db_connection()
    try:
        p = conn.execute(
            "SELECT id, name_zh, name_vi, name_en, sect, dynasty, birth_year, death_year, "
            "source_origin, bio FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "person not found"}), 404

        profile = {
            "id": p['id'], "name_zh": p['name_zh'], "name_vi": p['name_vi'],
            "name_en": p['name_en'], "sect": p['sect'], "dynasty": p['dynasty'],
            "birth_year": p['birth_year'], "death_year": p['death_year'],
            "source_origin": p['source_origin'], "bio": p['bio'],
        }

        # Marcus lineage (tái dùng logic graph route — thầy/trò có ref citation)
        lineage = {"linked": False, "teachers": [], "students": [], "source": None}
        link = conn.execute(
            "SELECT marcus_node_id FROM marcus_people_link WHERE person_id = ?", (dila_id,)
        ).fetchone()
        if link:
            node_id = link['marcus_node_id']
            lineage["linked"] = True
            lineage["source"] = "Marcus Bingenheimer ChineseBuddhism_SNA"
            lineage["teachers"] = [
                {"id": t['teacher_id'], "label": t['teacher_label'], "ref": t['ref']}
                for t in conn.execute(
                    "SELECT teacher_id, teacher_label, ref FROM marcus_networks WHERE student_id = ?",
                    (node_id,)).fetchall()]
            lineage["students"] = [
                {"id": s['student_id'], "label": s['student_label'], "ref": s['ref']}
                for s in conn.execute(
                    "SELECT student_id, student_label, ref FROM marcus_networks WHERE teacher_id = ?",
                    (node_id,)).fetchall()]

        # Địa danh liên quan
        places = []
        try:
            place_rows = conn.execute("""
                SELECT DISTINCT pl.place_id, pl.relation_type, pl.source_name, pl.source_url
                FROM place_person_link pl WHERE pl.person_id = ?
                ORDER BY pl.created_at LIMIT 50
            """, (dila_id,)).fetchall()
            places = [
                {"place_id": r['place_id'], "relation_type": r['relation_type'],
                 "source_name": r['source_name'], "source_url": r['source_url']}
                for r in place_rows]
        except Exception as pe:
            app.logger.warning(f"profile places (link) failed: {pe}")
        try:
            origin_rows = conn.execute("""
                SELECT pol.place_id, pol.confidence FROM person_origin_link pol
                WHERE pol.person_id = ? ORDER BY pol.confidence DESC LIMIT 50
            """, (dila_id,)).fetchall()
            if origin_rows:
                seen = {x['place_id'] for x in places}
                for r in origin_rows:
                    if r['place_id'] not in seen:
                        places.append({"place_id": r['place_id'], "relation_type": "sinh tại / 籍貫",
                                       "source_name": "DILA Person Authority",
                                       "source_url": f"https://authority.dila.edu.tw/person/?fromInner={dila_id}",
                                       "confidence": r['confidence']})
                        seen.add(r['place_id'])
        except Exception as pe:
            app.logger.warning(f"profile places (origin) failed: {pe}")

        # Kinh điển liên quan (CBETA bibl)
        texts = []
        try:
            bibl_rows = conn.execute("""
                SELECT DISTINCT source_book, cbeta_ref FROM place_person_bibl
                WHERE person_id = ? AND cbeta_ref IS NOT NULL AND cbeta_ref != ''
                ORDER BY source_book LIMIT 50
            """, (dila_id,)).fetchall()
            texts = [{"source_book": r['source_book'], "cbeta_ref": r['cbeta_ref']} for r in bibl_rows]
        except Exception as te:
            app.logger.warning(f"profile texts failed: {te}")

        # T51d — Nhân vật xuất hiện trong kinh (cbeta_person_mentions, exact dila_person_id match)
        mentions = {"text_count": 0, "texts": []}
        try:
            m_rows = conn.execute("""
                SELECT cbeta_text_sigla AS sigla, COUNT(DISTINCT juan) AS juan_count
                FROM cbeta_person_mentions
                WHERE dila_person_id = ? AND cbeta_text_sigla IS NOT NULL AND cbeta_text_sigla != ''
                GROUP BY cbeta_text_sigla
                ORDER BY juan_count DESC
                LIMIT 50
            """, (dila_id,)).fetchall()
            if m_rows:
                siglas = [r['sigla'] for r in m_rows]
                title_map = {}
                try:
                    cconn = get_cbeta_conn()
                    try:
                        phold = ",".join("?" for _ in siglas)
                        t_rows = cconn.execute(
                            f"SELECT sigla, title_zh FROM cbeta_texts WHERE sigla IN ({phold})",
                            siglas).fetchall()
                        title_map = {r['sigla']: r['title_zh'] for r in t_rows}
                    finally:
                        cconn.close()
                except Exception as te:
                    app.logger.warning(f"profile mentions titles failed: {te}")
                mentions["text_count"] = len(m_rows)
                mentions["texts"] = [
                    {"sigla": r['sigla'], "title_zh": title_map.get(r['sigla'], ''),
                     "juan_count": r['juan_count']}
                    for r in m_rows]
        except Exception as me:
            app.logger.warning(f"profile mentions failed: {me}")

        return jsonify({
            "ok": True, "profile": profile,
            "lineage": lineage, "places": places, "texts": texts,
            "mentions": mentions,
        })
    except Exception as e:
        app.logger.error(f"api_person_profile error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/daoanh/api/admin/place-person-link', methods=['POST'])
def api_admin_place_person_link_add():
    """POST /daoanh/api/admin/place-person-link
    body: {place_id, person_id, relation_type?, source_name, source_url, note?}
    Curated add for T22 — source_name + source_url are mandatory so every entry is citable.
    Does not verify the citation content; the human submitting is asserting it, same trust
    model as CUSTOM_HANVIET/custom_hanviet_override (T08).
    """
    data = request.get_json(silent=True) or {}
    place_id = (data.get('place_id') or '').strip()
    person_id = (data.get('person_id') or '').strip()
    source_name = (data.get('source_name') or '').strip()
    source_url = (data.get('source_url') or '').strip()
    if not place_id or not person_id:
        return jsonify({"ok": False, "error": "place_id and person_id required"}), 400
    if not source_name or not source_url:
        return jsonify({"ok": False, "error": "source_name and source_url required — mọi liên kết phải có trích dẫn"}), 400
    conn = get_db_connection()
    try:
        _ensure_place_person_link_table(conn)
        person = conn.execute("SELECT id FROM people WHERE id = ?", (person_id,)).fetchone()
        if not person:
            return jsonify({"ok": False, "error": f"person_id {person_id} not found in people table"}), 404
        conn.execute("""
            INSERT INTO place_person_link (place_id, person_id, relation_type, source_name, source_url, note, added_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (place_id, person_id, data.get('relation_type') or '', source_name, source_url, data.get('note') or '', request.remote_addr))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


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


@app.route('/daoanh/api/places/<place_id>/timeline')
def api_places_timeline(place_id):
    """GET /daoanh/api/places/<id>/timeline — T21 Geo-Identity Linking (2026-08-20).
    Returns founding date (Wikidata P571 via geo_cross_ref) + dynasty context (DILA time_periods)
    + static events (place_timeline_events). No data fabricated: returns no_mapping if QID unknown."""
    try:
        conn = get_db_connection()
        _ensure_geo_cross_ref_table(conn)
        _ensure_place_timeline_events_table(conn)

        dila_id, _ = _resolve_dila_id(conn, place_id)
        target_id = dila_id or place_id

        xref = conn.execute(
            "SELECT wikidata_qid, bgis_id, chgis_svid, marcus_ref, confidence, mapped_by FROM geo_cross_ref WHERE dila_id = ?",
            (target_id,)
        ).fetchone()

        static_events = conn.execute(
            """SELECT event_type, year, year_end, label_zh, label_vi, source, source_ref, confidence
               FROM place_timeline_events WHERE dila_id = ? ORDER BY year ASC""",
            (target_id,)
        ).fetchall()
        static_ev_list = [
            {"event_type": r[0], "year": r[1], "year_end": r[2],
             "label_zh": r[3], "label_vi": r[4],
             "source": r[5], "source_ref": r[6], "confidence": r[7]}
             for r in static_events
        ]

        if not xref or not xref[0]:
            # No Wikidata QID — fallback to DILA-sourced founding event (Hướng A, T21)
            dila_founding = conn.execute(
                """SELECT year, source, source_ref, confidence, label_zh, label_vi
                   FROM place_timeline_events
                   WHERE dila_id = ? AND event_type = 'founding' AND year IS NOT NULL
                   ORDER BY CASE source
                     WHEN 'dila_era_name' THEN 1
                     WHEN 'dila_dynasty' THEN 2
                     WHEN 'dila_note' THEN 3
                     ELSE 4
                   END, confidence DESC LIMIT 1""",
                (target_id,)
            ).fetchone()
            if dila_founding:
                dila_year = dila_founding[0]
                dynasty = _get_dynasty_context(dila_year, conn)
                conn.close()
                return jsonify({
                    "ok": True,
                    "status": "dila_fallback",
                    "dila_id": target_id,
                    "founding": {
                        "year": dila_year,
                        "source": dila_founding[1],
                        "source_ref": dila_founding[2],
                        "confidence": dila_founding[3],
                        "label_zh": dila_founding[4],
                        "label_vi": dila_founding[5],
                        "note_vi": "Nguồn DILA — chưa cross-verify Wikidata",
                        "license": "CC BY-NC-SA 4.0 (DILA)"
                    },
                    "dynasty_context": dynasty,
                    "static_events": static_ev_list,
                    "wikidata_qid": None
                })
            conn.close()
            return jsonify({
                "ok": True,
                "status": "no_mapping",
                "dila_id": target_id,
                "message": "Chưa có ID xác minh (Wikidata QID) cho địa danh này. Xem T21 task để biết cách thêm mapping.",
                "static_events": static_ev_list,
                "founding": None,
                "dynasty_context": None
            })

        qid = xref[0]
        wd = _fetch_wikidata_timeline(qid)
        founding_year = wd.get("founding_year")
        dynasty = _get_dynasty_context(founding_year, conn) if founding_year else None

        conn.close()
        return jsonify({
            "ok": True,
            "status": "ok",
            "dila_id": target_id,
            "cross_refs": {
                "wikidata_qid": qid,
                "bgis_id": xref[1],
                "chgis_svid": xref[2],
                "marcus_ref": xref[3],
                "confidence": xref[4],
                "mapped_by": xref[5]
            },
            "founding": {
                "year": founding_year,
                "label": wd.get("label", ""),
                "heritage": wd.get("heritage", []),
                "source": "wikidata",
                "source_ref": wd.get("source_ref", f"{qid}·P571"),
                "license": "CC0",
                "wikidata_url": wd.get("wikidata_url", f"https://www.wikidata.org/wiki/{qid}")
            } if not wd.get("error") else None,
            "dynasty_context": dynasty,
            "static_events": static_ev_list,
            "wikidata_error": wd.get("error")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── T97: Place Events API ──────────────────────────────────────────────────────
@app.route('/daoanh/api/places/<place_id>/events')
def api_places_events(place_id):
    """GET /daoanh/api/places/<id>/events — T97 Tab Sự Kiện.
    Returns events linked to this place from nexus_events + event_text_link.
    Evidence-first: every event has passage_id / cbeta_ref + source_book.
    No self-generated events, no year fabrication."""
    try:
        conn = get_db_connection()
        conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
        dila_id, _ = _resolve_dila_id(conn, place_id)
        target_id = dila_id or place_id

        # 1. nexus_events — person-place co-mentions from CBETA passages
        ne_rows = conn.execute("""
            SELECT ne.passage_id, ne.person_dila_id, ne.event_year,
                   ne.event_label, ne.source_book, ne.confidence,
                   p.name_zh, p.name_vi
            FROM nexus_events ne
            LEFT JOIN people p ON p.id = ne.person_dila_id
            WHERE ne.place_dila_id = ?
            ORDER BY ne.event_year ASC NULLS LAST, ne.confidence DESC
            LIMIT 100
        """, (target_id,)).fetchall()

        nexus = []
        for r in ne_rows:
            nexus.append({
                "passage_id": r[0],
                "person_dila_id": r[1],
                "event_year": r[2],
                "event_label": r[3],
                "source_book": r[4],
                "confidence": r[5],
                "person_name_zh": r[6],
                "person_name_vi": r[7],
                "evidence_type": "cbeta_co_mention"
            })

        # 2. event_text_link — person-place links with exact CBETA ref
        etl_rows = conn.execute("""
            SELECT etl.event_type, etl.entity_id, etl.related_name,
                   etl.cbeta_ref, etl.source_book, etl.year, etl.confidence,
                   p.name_vi
            FROM event_text_link etl
            LEFT JOIN people p ON p.id = etl.entity_id
            WHERE etl.related_id = ? AND etl.event_type = 'person_place'
            ORDER BY etl.year ASC NULLS LAST, etl.confidence DESC
            LIMIT 100
        """, (target_id,)).fetchall()

        text_links = []
        seen_cbeta = set()
        for r in etl_rows:
            key = (r[1], r[3])  # entity_id + cbeta_ref — dedup
            if key in seen_cbeta:
                continue
            seen_cbeta.add(key)
            text_links.append({
                "event_type": r[0],
                "person_dila_id": r[1],
                "person_name_zh": r[2],
                "cbeta_ref": r[3],
                "source_book": r[4],
                "year": r[5],
                "confidence": r[6],
                "person_name_vi": r[7],
                "evidence_type": "cbeta_text_link"
            })

        # 3. events (T97 Build 2) — bảng events + event_entities
        ev_rows = conn.execute("""
            SELECT e.event_id, e.event_type, e.title_zh, e.title_vi,
                   e.start_year, e.end_year, e.precision, e.extraction_method,
                   e.review_status, e.confidence
            FROM events e
            JOIN event_entities ee ON ee.event_id = e.event_id
            WHERE ee.entity_id = ? AND ee.entity_type = 'place'
            ORDER BY (e.review_status = 'reviewed') DESC, e.start_year ASC NULLS LAST
            LIMIT 50
        """, (target_id,)).fetchall()

        reviewed_events, candidate_events = [], []
        for r in ev_rows:
            ev = {
                "event_id": r[0], "event_type": r[1],
                "title_zh": r[2], "title_vi": r[3],
                "start_year": r[4], "end_year": r[5],
                "precision": r[6], "extraction_method": r[7],
                "review_status": r[8], "confidence": r[9]
            }
            (reviewed_events if r[8] == 'reviewed' else candidate_events).append(ev)

        total = len(nexus) + len(text_links)
        conn.close()
        return jsonify({
            "ok": True,
            "dila_id": target_id,
            "total": total,
            "nexus_events": nexus,
            "text_links": text_links,
            "reviewed_events": reviewed_events,
            "candidate_events": candidate_events,
            "note": "Evidence-first: mỗi sự kiện trỏ về passage_id/cbeta_ref trong CBETA."
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── T97 Phase 3: Event Candidate CRUD ─────────────────────────────────────────
@app.route('/daoanh/api/events')
def api_events_list():
    """GET /daoanh/api/events?place_id=&status=candidate&limit=50&offset=0
    List event candidates; optionally filter by place + review_status."""
    try:
        conn = get_db_connection()
        conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
        place_id = request.args.get('place_id', '').strip()
        status   = request.args.get('status', '').strip()
        limit    = min(int(request.args.get('limit', 50)), 200)
        offset   = int(request.args.get('offset', 0))

        where, params = [], []
        if status:
            where.append("e.review_status = ?"); params.append(status)
        if place_id:
            dila_id, _ = _resolve_dila_id(conn, place_id)
            target = dila_id or place_id
            where.append("ee.entity_id = ?"); params.append(target)

        where_sql = ("JOIN event_entities ee ON ee.event_id = e.event_id WHERE " + " AND ".join(where)) if where else ""
        sql = f"""
            SELECT e.event_id, e.event_type, e.title_zh, e.title_vi,
                   e.start_year, e.end_year, e.precision, e.review_status,
                   e.confidence, e.extraction_method, e.notes, e.created_at
            FROM events e {where_sql}
            ORDER BY e.start_year ASC NULLS LAST, e.created_at DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, params + [limit, offset]).fetchall()
        total_sql = f"SELECT COUNT(*) FROM events e {where_sql}"
        total = conn.execute(total_sql, params).fetchone()[0]

        events = []
        for r in rows:
            ev = dict(zip(['event_id','event_type','title_zh','title_vi','start_year','end_year',
                           'precision','review_status','confidence','extraction_method','notes','created_at'], r))
            # fetch evidence
            evids = conn.execute(
                "SELECT source_record, source_ref, evidence_type, exact_span FROM event_evidence WHERE event_id=? LIMIT 5",
                (r[0],)
            ).fetchall()
            ev['evidence'] = [{'source_record': e[0], 'source_ref': e[1],
                                'evidence_type': e[2], 'exact_span': e[3]} for e in evids]
            events.append(ev)

        conn.close()
        return jsonify({"ok": True, "total": total, "events": events})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/events/<event_id>', methods=['PATCH'])
def api_event_review(event_id):
    """PATCH /daoanh/api/events/<id> — update review_status + notes.
    Body: {status: candidate|reviewed|disputed|rejected, notes: str}"""
    try:
        data   = request.get_json(force=True) or {}
        status = data.get('status', '').strip()
        notes  = data.get('notes', '')
        valid  = ('candidate', 'reviewed', 'disputed', 'rejected')
        if status not in valid:
            return jsonify({"ok": False, "error": f"status phải là {valid}"}), 400

        conn = get_db_connection()
        conn.execute(
            "UPDATE events SET review_status=?, notes=?, updated_at=datetime('now') WHERE event_id=?",
            (status, notes, event_id)
        )
        if conn.execute("SELECT changes()").fetchone()[0] == 0:
            conn.close()
            return jsonify({"ok": False, "error": "event_id không tìm thấy"}), 404
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "event_id": event_id, "new_status": status})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/places/<place_id>/time-mentions')
def api_place_time_mentions(place_id):
    """GET /daoanh/api/places/<id>/time-mentions — T97 Phase 2 output."""
    try:
        conn = get_db_connection()
        conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
        dila_id, _ = _resolve_dila_id(conn, place_id)
        target = dila_id or place_id

        rows = conn.execute("""
            SELECT tm.mention_id, tm.raw_time_zh, tm.normalized_start, tm.normalized_end,
                   tm.precision, tm.extraction_method, tm.confidence, tm.time_authority_id
            FROM time_mentions tm
            JOIN place_timeline_events pte ON pte.id = CAST(tm.source_record_id AS INTEGER)
            WHERE tm.source_table='place_timeline_events' AND pte.dila_id=?
            ORDER BY tm.normalized_start ASC NULLS LAST
        """, (target,)).fetchall()

        mentions = [dict(zip(['mention_id','raw_time_zh','normalized_start','normalized_end',
                               'precision','extraction_method','confidence','time_authority_id'], r))
                    for r in rows]
        conn.close()
        return jsonify({"ok": True, "dila_id": target, "total": len(mentions), "mentions": mentions})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── T10: DILA Place Index API ─────────────────────────────────────────────────

@app.route('/daoanh/api/dila/places')
def api_dila_places_search():
    """GET /daoanh/api/dila/places?q=&category=&country=&limit=50&offset=0"""
    import csv, io as _io
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    country = request.args.get('country', '').strip()
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    fmt = request.args.get('format', 'json')
    try:
        conn = get_db_connection()
        where = []
        params = []
        if q:
            where.append("(pd.name_zh LIKE ? OR pd.name LIKE ? OR pd.id LIKE ?)")
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        if category:
            where.append("pd.note_category = ?")
            params.append(category)
        if country:
            where.append("pd.district LIKE ?")
            params.append(f'{country}%')
        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
        count_row = conn.execute(
            f"SELECT COUNT(*) FROM places_dila pd {where_sql}", params
        ).fetchone()
        total = count_row[0]
        rows = conn.execute(
            f"""SELECT pd.id, pd.name_zh, pd.name, pd.note_category, pd.district,
                       pd.geo_lat, pd.geo_long,
                       (SELECT nm.name_vi FROM namevi_map_places nm WHERE nm.name_zh = pd.name_zh
                        AND nm.dila_id IS NOT NULL
                        ORDER BY (nm.vn_name_status='reviewed') DESC, nm.confidence DESC LIMIT 1) AS name_vi,
                       (SELECT nm.confidence FROM namevi_map_places nm WHERE nm.name_zh = pd.name_zh
                        AND nm.dila_id IS NOT NULL
                        ORDER BY (nm.vn_name_status='reviewed') DESC, nm.confidence DESC LIMIT 1) AS confidence
                FROM places_dila pd
                {where_sql}
                ORDER BY pd.id
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        conn.close()
        items = [dict(r) for r in rows]
        if fmt == 'csv':
            out = _io.StringIO()
            w = csv.DictWriter(out, fieldnames=['id','name_zh','name','note_category','district','geo_lat','geo_long','name_vi','confidence'])
            w.writeheader(); w.writerows(items)
            from flask import Response
            return Response(out.getvalue(), mimetype='text/csv',
                            headers={"Content-Disposition": "attachment;filename=dila_places.csv"})
        return jsonify({"ok": True, "total": total, "limit": limit, "offset": offset, "items": items})
    except Exception as e:
        app.logger.error(f"api_dila_places_search error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/dila/stats')
def api_dila_stats():
    """GET /daoanh/api/dila/stats — counts by category and country."""
    try:
        conn = get_db_connection()
        cats = conn.execute(
            "SELECT note_category, COUNT(*) as n FROM places_dila WHERE note_category IS NOT NULL AND note_category != '' GROUP BY note_category ORDER BY n DESC LIMIT 20"
        ).fetchall()
        # Extract country from district (first segment before -)
        countries = conn.execute(
            """SELECT CASE WHEN INSTR(district, '-') > 0 THEN SUBSTR(district, 1, INSTR(district,'-')-1) ELSE district END as country,
               COUNT(*) as n FROM places_dila WHERE district IS NOT NULL AND district != ''
               GROUP BY country ORDER BY n DESC LIMIT 20"""
        ).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
        mapped = conn.execute(
            "SELECT COUNT(DISTINCT pd.id) FROM places_dila pd JOIN namevi_map_places nm ON nm.name_zh = pd.name_zh"
        ).fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "total": total, "mapped_vi": mapped,
                        "by_category": [dict(r) for r in cats],
                        "by_country": [dict(r) for r in countries]})
    except Exception as e:
        app.logger.error(f"api_dila_stats error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# ── DILA Person Index API (mirror T10 DILA Place Index, additive 0 ALTER) ─────
# Reuses `people` (DILA person authority) + `translation_cache` (T73/T123 draft
# AI translation status, source_type='person_bio', entity_id=people.id) để
# admin theo dõi tiến độ dịch Hán→Việt tương đương DILA Place Index (name_vi
# mapping). KHÔNG suy đoán bio_vi — chỉ đọc trực tiếp cột/bảng đã có.

@app.route('/daoanh/api/dila/persons')
def api_dila_persons_search():
    """GET /daoanh/api/dila/persons?q=&sect=&dynasty=&status=&limit=50&offset=0

    status filter (tùy chọn): 'translated' (đã lưu people.bio_vi) |
    'draft' (có bản nháp AI/edited trong translation_cache, chưa lưu) |
    'none' (chưa có bản dịch nào).
    """
    import csv, io as _io
    q = request.args.get('q', '').strip()
    sect = request.args.get('sect', '').strip()
    dynasty = request.args.get('dynasty', '').strip()
    status = request.args.get('status', '').strip()
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    fmt = request.args.get('format', 'json')
    try:
        conn = get_db_connection()
        where = []
        params = []
        if q:
            where.append("(p.name_zh LIKE ? OR p.name_vi LIKE ? OR p.id LIKE ?)")
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        if sect:
            where.append("p.sect = ?")
            params.append(sect)
        if dynasty:
            where.append("p.dynasty = ?")
            params.append(dynasty)
        # Status filter phải nằm trong WHERE thật (không nối chuỗi sau ON,
        # nếu không sẽ bị SQLite hiểu nhầm thành điều kiện JOIN — làm filter
        # vô hiệu vì LEFT JOIN vẫn giữ nguyên dòng bên trái).
        if status == 'translated':
            where.append("p.bio_vi IS NOT NULL AND p.bio_vi != ''")
        elif status == 'draft':
            where.append("(p.bio_vi IS NULL OR p.bio_vi = '') AND tc.status IS NOT NULL")
        elif status == 'none':
            where.append("(p.bio_vi IS NULL OR p.bio_vi = '') AND tc.status IS NULL")
        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''

        translation_cte = """
            (SELECT tc.entity_id, tc.status, tc.updated_at, tc.model_id
               FROM translation_cache tc
              WHERE tc.source_type = 'person_bio' AND tc.status != 'invalidated'
                AND tc.id = (SELECT MAX(tc2.id) FROM translation_cache tc2
                              WHERE tc2.entity_id = tc.entity_id
                                AND tc2.source_type = 'person_bio'
                                AND tc2.status != 'invalidated'))
        """

        count_row = conn.execute(
            f"""SELECT COUNT(*) FROM people p
                LEFT JOIN {translation_cte} tc ON tc.entity_id = p.id
                {where_sql}""", params
        ).fetchone()
        total = count_row[0]
        rows = conn.execute(
            f"""SELECT p.id, p.name_zh, p.name_vi, p.name_en, p.sect, p.dynasty,
                       p.birth_year, p.death_year,
                       (LENGTH(COALESCE(p.bio,'')) > 0) AS has_bio_zh,
                       (p.bio_vi IS NOT NULL AND p.bio_vi != '') AS bio_vi_saved,
                       tc.status AS draft_status
                FROM people p
                LEFT JOIN {translation_cte} tc ON tc.entity_id = p.id
                {where_sql}
                ORDER BY p.id
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        conn.close()
        items = [dict(r) for r in rows]
        if fmt == 'csv':
            out = _io.StringIO()
            w = csv.DictWriter(out, fieldnames=['id','name_zh','name_vi','name_en','sect','dynasty',
                                                 'birth_year','death_year','has_bio_zh','bio_vi_saved','draft_status'])
            w.writeheader(); w.writerows(items)
            from flask import Response
            return Response(out.getvalue(), mimetype='text/csv',
                            headers={"Content-Disposition": "attachment;filename=dila_persons.csv"})
        return jsonify({"ok": True, "total": total, "limit": limit, "offset": offset, "items": items})
    except Exception as e:
        app.logger.error(f"api_dila_persons_search error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/dila/persons/stats')
def api_dila_persons_stats():
    """GET /daoanh/api/dila/persons/stats — counts by sect/dynasty + translation coverage."""
    try:
        conn = get_db_connection()
        sects = conn.execute(
            "SELECT sect, COUNT(*) as n FROM people WHERE sect IS NOT NULL AND sect != '' GROUP BY sect ORDER BY n DESC LIMIT 20"
        ).fetchall()
        dynasties = conn.execute(
            "SELECT dynasty, COUNT(*) as n FROM people WHERE dynasty IS NOT NULL AND dynasty != '' GROUP BY dynasty ORDER BY n DESC LIMIT 20"
        ).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM people').fetchone()[0]
        with_bio = conn.execute(
            "SELECT COUNT(*) FROM people WHERE bio IS NOT NULL AND bio != ''"
        ).fetchone()[0]
        saved = conn.execute(
            "SELECT COUNT(*) FROM people WHERE bio_vi IS NOT NULL AND bio_vi != ''"
        ).fetchone()[0]
        drafted = conn.execute(
            "SELECT COUNT(DISTINCT entity_id) FROM translation_cache "
            "WHERE source_type='person_bio' AND status != 'invalidated'"
        ).fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "total": total, "with_bio_zh": with_bio,
                        "translated_saved": saved, "translated_draft": drafted,
                        "by_category": [{"note_category": r['sect'], "n": r['n']} for r in sects],
                        "by_country": [{"country": r['dynasty'], "n": r['n']} for r in dynasties]})
    except Exception as e:
        app.logger.error(f"api_dila_persons_stats error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/fuzzy_rescore', methods=['POST'])
def api_cbeta_fuzzy_rescore():
    """POST — T03: Rescore cbeta_catalog_place_fuzzy using RapidFuzz for a given place_id or name_zh.
    Body: {place_id?: str, name_zh?: str, threshold?: int}
    Returns top matches with improved scores.
    """
    try:
        from rapidfuzz import fuzz
        data = request.get_json(force=True, silent=True) or {}
        place_id = data.get('place_id', '').strip()
        name_zh_q = data.get('name_zh', '').strip()
        threshold = int(data.get('threshold', 50))
        conn = get_db_connection()
        if not name_zh_q and place_id:
            row = conn.execute("SELECT name_zh FROM places_dila WHERE id = ?", (place_id,)).fetchone()
            name_zh_q = row['name_zh'] if row else ''
        if not name_zh_q:
            conn.close()
            return jsonify({"ok": False, "error": "need place_id or name_zh"}), 400
        titles = conn.execute("SELECT id, catalog_id, name_zh, title_zh, title_vi, score FROM cbeta_catalog_place_fuzzy LIMIT 5000").fetchall()
        scored = []
        for t in titles:
            s = fuzz.partial_ratio(name_zh_q, t['title_zh'] or '')
            s2 = fuzz.ratio(name_zh_q, t['name_zh'] or '')
            best = max(s, s2, t['score'] or 0)
            if best >= threshold:
                scored.append({'catalog_id': t['catalog_id'], 'name_zh': t['name_zh'],
                               'title_zh': t['title_zh'], 'title_vi': t['title_vi'],
                               'score_old': t['score'], 'score_new': best})
        scored.sort(key=lambda x: -x['score_new'])
        conn.close()
        return jsonify({"ok": True, "query": name_zh_q, "matches": scored[:20]})
    except Exception as e:
        app.logger.error(f"api_cbeta_fuzzy_rescore error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/aggregates')
def api_cbeta_aggregates():
    """GET /daoanh/api/admin/cbeta/aggregates — T51d place mention stats.
    Query params: limit (default 50), min_count (default 1)
    """
    try:
        conn = get_db_connection()
        limit = min(int(request.args.get('limit', 50)), 500)
        min_count = int(request.args.get('min_count', 1))
        rows = conn.execute(
            """SELECT place_id, mention_count, top_texts, vi_name, last_updated
               FROM cbeta_place_mention_stats
               WHERE mention_count >= ?
               ORDER BY mention_count DESC
               LIMIT ?""",
            (min_count, limit)
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM cbeta_place_mention_stats WHERE mention_count >= ?",
            (min_count,)
        ).fetchone()[0]
        conn.close()
        return jsonify({
            "ok": True,
            "total": total,
            "limit": limit,
            "data": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/cbeta/catalog')
def api_cbeta_catalog():
    """GET /daoanh/api/cbeta/catalog — T52c public catalog browser.
    Params: q (search), dynasty, series, page (1-based), limit (default 20, max 100)
    """
    try:
        conn = get_db_connection()
        q = request.args.get('q', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        series = request.args.get('series', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = (page - 1) * limit

        where = []
        params = []
        if q:
            where.append("(title_vi LIKE ? OR title_zh LIKE ?)")
            params += [f'%{q}%', f'%{q}%']
        if dynasty:
            where.append("dynasty_vi = ?")
            params.append(dynasty)
        if series:
            where.append("series = ?")
            params.append(series)

        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
        total = conn.execute(
            f"SELECT COUNT(*) FROM cbeta_catalog_vn {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT sh_number, title_vi, title_zh, juans, dynasty_vi,
                       translator_vi, series, cbeta_ref, q_number, page
                FROM cbeta_catalog_vn {where_sql}
                ORDER BY CAST(sh_number AS INTEGER)
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "data": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/dashboard-data')
def api_cbeta_dashboard_data():
    """GET /daoanh/api/admin/cbeta/dashboard-data — T52a stats for admin dashboard."""
    try:
        conn = get_db_connection()
        catalog_total = conn.execute('SELECT COUNT(*) FROM cbeta_catalog_vn').fetchone()[0]
        series_rows = conn.execute(
            'SELECT series, COUNT(*) as n FROM cbeta_catalog_vn GROUP BY series ORDER BY n DESC'
        ).fetchall()
        dynasty_rows = conn.execute(
            'SELECT dynasty_vi, COUNT(*) as n FROM cbeta_catalog_vn WHERE dynasty_vi IS NOT NULL GROUP BY dynasty_vi ORDER BY n DESC LIMIT 10'
        ).fetchall()
        passages_total = conn.execute('SELECT COUNT(*) FROM passage').fetchone()[0]
        passages_translated = conn.execute(
            'SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL AND vi_text != ""'
        ).fetchone()[0]
        entity_links = conn.execute('SELECT COUNT(*) FROM passage_entity').fetchone()[0]
        sat_count = conn.execute('SELECT COUNT(*) FROM sat_crossref').fetchone()[0]
        toh_count = conn.execute('SELECT COUNT(*) FROM toh_cbeta_crossref').fetchone()[0] if True else 0
        fuzzy_total = conn.execute('SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy').fetchone()[0]
        fuzzy_approved = conn.execute('SELECT COUNT(*) FROM catalog_mapping WHERE status="approved"').fetchone()[0]
        place_stats = conn.execute('SELECT COUNT(*) FROM cbeta_place_mention_stats').fetchone()[0]
        top_places = conn.execute(
            'SELECT place_id, mention_count, vi_name FROM cbeta_place_mention_stats ORDER BY mention_count DESC LIMIT 10'
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "catalog": {
                "total": catalog_total,
                "series": {r['series'] or 'unknown': r['n'] for r in series_rows}
            },
            "import": {
                "passages_total": passages_total,
                "passages_translated": passages_translated,
                "translation_pct": round(passages_translated / passages_total * 100, 1) if passages_total else 0
            },
            "entity": {
                "links_total": entity_links,
                "places_with_stats": place_stats,
                "top_places": [dict(r) for r in top_places]
            },
            "crossref": {
                "sat": sat_count,
                "sat_pct": round(sat_count / catalog_total * 100, 1),
                "toh": toh_count,
                "toh_pct": round(toh_count / catalog_total * 100, 1)
            },
            "fuzzy": {
                "total": fuzzy_total,
                "approved": fuzzy_approved,
                "approval_pct": round(fuzzy_approved / fuzzy_total * 100, 1) if fuzzy_total else 0
            },
            "dynasty_distribution": [{"dynasty": r['dynasty_vi'], "count": r['n']} for r in dynasty_rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/place/<place_id>/cbeta')
def api_place_cbeta_catalog(place_id):
    """
    GET /daoanh/api/admin/place/<place_id>/cbeta
    Returns approved catalog mappings for a place, joined with cbeta_catalog_vn.
    """
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT m.id, m.catalog_id, m.source, m.status, m.note,
                   v.title_vi, v.title_zh, v.dynasty_vi, v.translator_vi,
                   v.q_number, v.page, v.sh_number, v.juans,
                   v.source_name, v.license_name, v.cbeta_ref
            FROM catalog_mapping m
            LEFT JOIN cbeta_catalog_vn v ON m.catalog_id = v.sh_number
            WHERE m.place_id = ? AND m.status = 'approved'
            ORDER BY v.title_vi NULLS LAST
        """, (place_id,)).fetchall()
        conn.close()

        entries = []
        for r in rows:
            d = dict(r)
            # Build a user-friendly code from catalog_vn data if available
            if d.get('sh_number'):
                d['code'] = f"T{int(d['sh_number']):04d}" if d['sh_number'].isdigit() else d['sh_number']
            else:
                d['code'] = d['catalog_id']
            entries.append(d)

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "count": len(entries),
            "cbeta_entries": entries
        })

    except sqlite3.OperationalError as e:
        return jsonify({"ok": True, "place_id": place_id, "count": 0, "cbeta_entries": [],
                        "note": f"Table not available: {e}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── CHRONOLOGY API ─────────────────────────────────────────
CHRONOLOGY_DB = DB_PATH

def get_chronology_conn():
    conn = sqlite3.connect(CHRONOLOGY_DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/daoanh/api/chronology/events')
def api_chronology_events():
    """
    GET /daoanh/api/chronology/events?century=7&dynasty=唐&limit=200
    Returns timeline events from lineage_chronology with GPS coordinates
    when available (matched against places_dila by name_zh).
    """
    try:
        century = request.args.get('century', '').strip()
        dynasty = request.args.get('dynasty', '').strip()
        limit = min(int(request.args.get('limit', 200)), 500)
        offset = int(request.args.get('offset', 0))

        conn = get_chronology_conn()
        where = []
        params = []

        if dynasty:
            where.append("c.dynasty = ?")
            params.append(dynasty)
        if century:
            c = int(century)
            where.append("c.century_start <= ? AND (c.century_end >= ? OR c.century_end IS NULL)")
            params.extend([c, c])

        where_sql = " AND ".join(where) if where else "1=1"

        rows = conn.execute(f"""
            SELECT c.id, c.title, c.title_zh, c.century_start, c.century_end,
                   c.dynasty, c.category, c.data_source,
                   p.name_vi, p.bio,
                   pl.name_zh as place_name, pl.geo_lat, pl.geo_long,
                   pl.district
            FROM lineage_chronology c
            LEFT JOIN people p ON p.id = c.id AND c.category = 'person'
            LEFT JOIN places_dila pl ON pl.name_zh = c.title_zh
            WHERE {where_sql}
            ORDER BY c.century_start NULLS LAST, c.title_zh
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()
        conn.close()

        results = []
        for r in rows:
            item = dict(r)
            # Clean up: only include geo if both coords present
            if not item.get('geo_lat') or not item.get('geo_long'):
                item['geo_lat'] = None
                item['geo_long'] = None
            # Sanitize Vietnamese text fields
            if item.get('name_vi'):
                item['name_vi'] = _ensure_vietnamese(item['name_vi'])
            if item.get('title'):
                item['title'] = _ensure_vietnamese(item['title'])
            if item.get('place_name'):
                item['place_name'] = _ensure_vietnamese(item['place_name'])
            results.append(item)

        return jsonify({
            "ok": True,
            "count": len(results),
            "has_gps": sum(1 for r in results if r.get('geo_lat')),
            "results": results
        })

    except Exception as e:
        import traceback
        app.logger.error(f"api_chronology_events error: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/daoanh/api/chronology/dynasties')
def api_chronology_dynasties():
    """List all dynasties with counts, century range"""
    try:
        conn = get_chronology_conn()
        rows = conn.execute("""
            SELECT dynasty, COUNT(*) as count,
                   MIN(century_start) as min_century,
                   MAX(century_end) as max_century
            FROM lineage_chronology
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty
            ORDER BY count DESC
        """).fetchall()
        conn.close()
        return jsonify({"ok": True, "dynasties": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/daoanh/api/chronology/search')
def api_chronology_search():
    """Search lineage_chronology by dynasty, century, category, or text"""
    try:
        dynasty = request.args.get('dynasty', '').strip()
        century = request.args.get('century', '').strip()
        category = request.args.get('category', '').strip()
        q = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 50)), 200)

        conn = get_chronology_conn()
        where = []
        params = []

        if dynasty:
            where.append("dynasty = ?")
            params.append(dynasty)
        if century:
            c = int(century)
            where.append("century_start <= ? AND (century_end >= ? OR century_end IS NULL)")
            params.extend([c, c])
        if category:
            where.append("category = ?")
            params.append(category)
        if q:
            where.append("(title LIKE ? OR title_zh LIKE ? OR id LIKE ?)")
            p = f'%{q}%'
            params.extend([p, p, p])

        sql = "SELECT * FROM lineage_chronology"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY century_start NULLS LAST LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return jsonify({"ok": True, "count": len(rows), "results": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/daoanh/api/chronology/<chronology_id>')
def api_chronology_detail(chronology_id):
    """Get one chronology record by ID"""
    try:
        conn = get_chronology_conn()
        row = conn.execute("""
            SELECT * FROM lineage_chronology WHERE id = ?
        """, (chronology_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({"ok": False, "error": "Not found"}), 404
        return jsonify({"ok": True, "data": dict(row)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/places_all')
def places_all():
    """
    GET /daoanh/api/admin/places_all
    Returns all places from places_pending with mapping status
    Supports filtering, sorting, pagination
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 per page
        offset = int(request.args.get('offset', 0))
        cate = request.args.get('cate', '').strip()
        country = request.args.get('country', '').strip()
        province = request.args.get('province', '').strip()
        mapped_status = request.args.get('mapped_status', '').strip()  # 'mapped', 'unmapped', or empty for all
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'asc').upper()
        
        # Validate sort_by to prevent SQL injection
        allowed_sort_fields = ['id', 'name_zh', 'name_vi', 'province', 'country', 'gps_lat', 'gps_long', 'created_at', 'updated_at']
        if sort_by not in allowed_sort_fields:
            sort_by = 'id'
        
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'ASC'
        
        conn = get_db_connection()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if cate:
            where_conditions.append("cate = ?")
            params.append(cate)
        
        if country:
            where_conditions.append("country = ?")
            params.append(country)
        
        if province:
            where_conditions.append("province = ?")
            params.append(province)
        
        if search:
            where_conditions.append("(name_zh LIKE ? OR name_vi LIKE ? OR id LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Map status filter: check if place_id exists in namevi_map_places
        if mapped_status == 'mapped':
            where_conditions.append("id IN (SELECT dila_id FROM namevi_map_places)")
        elif mapped_status == 'unmapped':
            where_conditions.append("id NOT IN (SELECT dila_id FROM namevi_map_places)")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM places_pending 
            {where_clause}
        """
        total_result = conn.execute(count_query, params).fetchone()
        total_count = total_result['total'] if total_result else 0
        
        # Get paginated results
        # We need to join with namevi_map_places to get mapping info
        query = f"""
            SELECT 
                p.*,
                CASE WHEN m.dila_id IS NOT NULL THEN 1 ELSE 0 END as is_mapped,
                m.name_vi as mapped_name_vi,
                m.updated_at as mapped_updated_at
            FROM places_pending p
            LEFT JOIN namevi_map_places m ON p.id = m.dila_id
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        places = conn.execute(query, params).fetchall()
        conn.close()
        
        # Convert to list of dicts
        places_list = []
        for place in places:
            place_dict = dict(place)
            places_list.append(place_dict)
        
        return jsonify({
            "success": True,
            "places": places_list,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/auto_batch_suggest')
def auto_batch_suggest():
    try:
        conn = get_db_connection()
        # Auto-save 50 lexicon matches
        auto_matches = conn.execute("""
            SELECT p.id, l.definition FROM places_pending p
            JOIN lexicon l ON p.name_zh = l.term
            WHERE p.id NOT IN (SELECT dila_id FROM namevi_map_places)
            LIMIT 50
        """).fetchall()
        for m in auto_matches:
            conn.execute(
                "INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, source, confidence) VALUES (?, ?, (SELECT name_zh FROM places_pending WHERE id=?), 'lexicon_auto', 1.0)",
                (m['id'], m['definition'], m['id'])
            )
        conn.commit()

        # Get 10 next for Admin
        pending = conn.execute("""
            SELECT id, name_zh FROM places_pending
            WHERE id NOT IN (SELECT dila_id FROM namevi_map_places)
            LIMIT 10
        """).fetchall()
        conn.close()

        results = []
        for p in pending:
            results.append({"id": ensure_long_id(p['id']), "name_zh": p['name_zh'], "suggested_vi": "", "is_standard": False})

        return jsonify({"success": True, "batch": results, "auto_saved": len(auto_matches)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/translate_location', methods=['POST'])
def translate_location():
    data = request.get_json()
    raw_text = (data.get('district') or '').strip()
    country_input = (data.get('country') or '').strip()
    if not raw_text and not country_input:
        return jsonify({"success": False, "error": "Thiếu dữ liệu đầu vào"}), 400

    place_id = (data.get('id') or '').strip()
    if not raw_text and place_id:
        conn = get_db_connection()
        note_row = conn.execute(
            "SELECT d.note_category FROM places_pending p LEFT JOIN places_dila d ON p.id = d.id WHERE p.id = ?",
            (place_id,)
        ).fetchone()
        conn.close()
        if note_row and note_row['note_category'] == '廣大之陸上人文地理區域':
            return jsonify({
                "success": True,
                "translated_district": "",
                "translated_country": "",
                "formatted": ""
            })

    print(f'[translate_location] Input: raw_text="{raw_text}", country="{country_input}"', flush=True)
    # First try: rule-based parse (no HVDic)
    parsed = parse_dila_district(raw_text)
    if parsed.get('country_vi') or parsed.get('district_vi'):
        print(f'[translate_location] Rule-based parse OK: {parsed}', flush=True)
        return jsonify({
            "success": True,
            "translated_district": parsed.get('district_vi', ''),
            "translated_country": parsed.get('country_vi', country_input),
            "formatted": parsed.get('formatted', '')
        })
    # Fallback: GoogleTranslator
    print(f'[translate_location] Fallback to GoogleTranslator', flush=True)
    try:
        from deep_translator import GoogleTranslator
        translated_district = ''
        translated_country = ''
        if raw_text:
            try:
                translated_district = GoogleTranslator(source='zh-CN', target='vi').translate(raw_text)
            except Exception:
                translated_district = GoogleTranslator(source='auto', target='vi').translate(raw_text)
        if country_input and country_input != raw_text:
            try:
                translated_country = GoogleTranslator(source='auto', target='vi').translate(country_input)
            except Exception:
                translated_country = country_input
        if not translated_country and country_input:
            translated_country = country_input
        if not translated_district and raw_text:
            translated_district = raw_text
        return jsonify({
            "success": True,
            "translated_district": translated_district,
            "translated_country": translated_country,
            "formatted": (translated_district + ', ' + translated_country).strip(', ')
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/places/<place_id>/cbdb')
def cbdb_place_lookup(place_id):
    try:
        digits = ''.join(filter(str.isdigit, place_id))
        full_id = f'PL{digits.zfill(12)}' if digits else place_id
        conn = get_db_connection()
        row = conn.execute(
            "SELECT cbdb_addr_id, note FROM place_cbdb_map WHERE place_id = ?",
            (full_id,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"has_cbdb": False, "place_id": full_id, "cbdb_places": []})
        cbdb_id = row['cbdb_addr_id']
        cconn = get_cbdb_conn()
        cdata = cconn.execute(
            "SELECT c_name_chn, c_admin_type, c_notes FROM ADDR_CODES WHERE c_addr_id = ?",
            (cbdb_id,)
        ).fetchone()
        cconn.close()
        if not cdata:
            return jsonify({
                "has_cbdb": True, "place_id": full_id,
                "cbdb_places": [{"cbdb_addr_id": cbdb_id, "error": "ADDR_CODES row not found"}]
            })
        return jsonify({
            "has_cbdb": True,
            "place_id": full_id,
            "cbdb_places": [{
                "cbdb_addr_id": cbdb_id,
                "name_zh": cdata['c_name_chn'] or '',
                "admin_type": cdata['c_admin_type'] or '',
                "notes_zh": cdata['c_notes'] or ''
            }]
        })
    except Exception as e:
        return jsonify({"error": True, "has_cbdb": False, "place_id": place_id, "cbdb_places": [], "message": str(e)})

@app.route('/daoanh/api/admin/places/<place_id>/cbdb_translate', methods=['POST'])
def cbdb_place_translate(place_id):
    try:
        digits = ''.join(filter(str.isdigit, place_id))
        full_id = f'PL{digits.zfill(12)}' if digits else place_id
        conn = get_db_connection()
        row = conn.execute(
            "SELECT cbdb_addr_id FROM place_cbdb_map WHERE place_id = ?",
            (full_id,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"success": False, "has_data": False, "error": "no_cbdb_mapping"})
        cconn = get_cbdb_conn()
        cdata = cconn.execute(
            "SELECT c_name_chn, c_admin_type, c_notes FROM ADDR_CODES WHERE c_addr_id = ?",
            (row['cbdb_addr_id'],)
        ).fetchone()
        cconn.close()
        if not cdata:
            return jsonify({"success": False, "has_data": False, "error": "cbdb_record_not_found"})
        text_parts = []
        if cdata['c_name_chn']:
            text_parts.append(f"Tên: {cdata['c_name_chn']}")
        if cdata['c_admin_type']:
            text_parts.append(f"Loại hành chính: {cdata['c_admin_type']}")
        if cdata['c_notes']:
            text_parts.append(f"Ghi chú: {cdata['c_notes']}")
        text = '\n'.join(text_parts)
        prompt = f"Dịch đoạn mô tả địa danh sau từ Hán văn sang tiếng Việt. Giữ nguyên tên riêng và số liệu. Chỉ trả về bản dịch, không thêm giải thích:\n\n{text}"
        meta = {"llm_provider": "", "source": "CBDB"}
        try:
            resp = requests.post('https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
                json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.1, 'max_tokens': 2048},
                timeout=15)
            result = resp.json()
            if result.get('choices'):
                vi_draft = result['choices'][0]['message']['content']
                if vi_draft:
                    meta["llm_provider"] = GROQ_MODEL
                    return jsonify({"success": True, "vi_draft": vi_draft, "source": "CBDB", "meta": meta})
        except Exception:
            pass
        try:
            from deep_translator import GoogleTranslator
            vi_draft = GoogleTranslator(source='zh-CN', target='vi').translate(text)
            if vi_draft:
                meta["llm_provider"] = "google-translate"
                return jsonify({"success": True, "vi_draft": vi_draft, "source": "CBDB", "meta": meta})
        except Exception:
            pass
        meta["llm_provider"] = "fallback"
        return jsonify({"success": True, "vi_draft": text, "source": "CBDB", "meta": meta})
    except Exception as e:
        return jsonify({"error": True, "success": False, "message": str(e)}), 500

# ─── CBETA Routes ────────────────────────────────────────────

@app.route('/daoanh/api/admin/cbeta/search-place', methods=['POST'])
def cbeta_search_place():
    """
    POST /daoanh/api/admin/cbeta/search-place
    Body: {"place_name": "..."}
    Search CBETA texts where the place name appears.
    Returns: list of {sigla, title_zh, juan, page, context_snippet}
    """
    try:
        data = request.get_json(force=True) or {}
        place_name = (data.get('place_name') or data.get('query') or '').strip()
        if not place_name:
            return jsonify({"has_cbeta": False, "results": [], "message": "no_match"}), 200
        limit = min(int(data.get('limit', 50)), 200)
        results = []
        # 1. Annotated place mentions (explicit <placeName> tags)
        conn_lineage = get_db_connection()
        rows = conn_lineage.execute(
            "SELECT cbeta_text_sigla AS sigla, place_name_zh, dila_place_id, juan, page, context_snippet "
            "FROM cbeta_place_mentions WHERE place_name_zh LIKE ? ORDER BY juan LIMIT ?",
            (f'%{place_name}%', limit)
        ).fetchall()
        for r in rows:
            cconn = get_cbeta_conn()
            title_zh_row = cconn.execute(
                "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (r['sigla'],)
            ).fetchone()
            cconn.close()
            results.append({
                "type": "annotated",
                "sigla": r['sigla'],
                "title_zh": title_zh_row['title_zh'] if title_zh_row else '',
                "juan": r['juan'],
                "page": r['page'],
                "context_snippet": r['context_snippet'],
                "dila_id": r['dila_place_id']
            })
        conn_lineage.close()
        # 2. FTS full-text search (implicit mentions)
        if len(results) < limit:
            remaining = limit - len(results)
            try:
                cconn = get_cbeta_conn()
                fts_rows = cconn.execute(
                    "SELECT sigla, title_zh, juan, page, snippet(cbeta_fts, 4, '<mark>', '</mark>', '...', 30) AS ctx "
                    "FROM cbeta_fts WHERE cbeta_fts MATCH ? ORDER BY rank LIMIT ?",
                    (place_name, remaining)
                ).fetchall()
                for r in fts_rows:
                    results.append({
                        "type": "fts",
                        "sigla": r['sigla'],
                        "title_zh": r['title_zh'],
                        "juan": r['juan'],
                        "page": r['page'],
                        "context_snippet": r['ctx'],
                        "dila_id": None
                    })
                cconn.close()
            except Exception as fts_err:
                app.logger.warning(f"CBETA FTS search failed for '{place_name}': {fts_err}")
            # 2b. LIKE fallback for CJK (FTS5 unicode61 doesn't handle multi-char CJK well)
            if len(results) < remaining:
                remaining2 = remaining - len(results)
                try:
                    cconn2 = get_cbeta_conn()
                    like_rows = cconn2.execute(
                        "SELECT t.sigla, t.title_zh, ci.juan, ci.page, "
                        "SUBSTR(ci.content_zh, MAX(1, INSTR(ci.content_zh, ?) - 40), 120) AS ctx "
                        "FROM cbeta_content_index ci JOIN cbeta_texts t ON t.id = ci.text_id "
                        "WHERE ci.content_zh LIKE ? LIMIT ?",
                        (place_name, f'%{place_name}%', remaining2)
                    ).fetchall()
                    for r in like_rows:
                        results.append({
                            "type": "like",
                            "sigla": r['sigla'],
                            "title_zh": r['title_zh'],
                            "juan": r['juan'],
                            "page": r['page'],
                            "context_snippet": r['ctx'],
                            "dila_id": None
                        })
                    cconn2.close()
                except Exception as like_err:
                    app.logger.warning(f"CBETA LIKE search failed for '{place_name}': {like_err}")
        has_cbeta = len(results) > 0
        return jsonify({"has_cbeta": has_cbeta, "results": results, "total": len(results), "message": "found" if has_cbeta else "no_match", "error": False})
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA search-place error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": True, "message": "cbeta_internal_error"}), 500


@app.route('/daoanh/api/admin/cbeta/fuzzy-match-place', methods=['POST'])
def cbeta_fuzzy_match_place():
    """
    POST /daoanh/api/admin/cbeta/fuzzy-match-place
    Body: {"place_name": "...", "place_id": "...", "threshold": 60}
    Fuzzy match a place name against CBETA catalog titles using pre-computed table.
    """
    try:
        data = request.get_json(force=True) or {}
        place_name = (data.get('place_name') or '').strip()
        place_id = (data.get('place_id') or '').strip()
        threshold = int(data.get('threshold', 60))
        limit = min(int(data.get('limit', 20)), 100)

        conn = get_db_connection()

        if place_id:
            rows = conn.execute("""
                SELECT f.place_id, f.name_zh, f.catalog_id, f.title_zh, f.title_vi,
                       f.score, f.rank,
                       v.dynasty_vi, v.translator_vi,
                       v.q_number, v.sh_number, v.juans,
                       v.source_name, v.license_name, v.cbeta_ref
                FROM cbeta_catalog_place_fuzzy f
                JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                WHERE f.place_id = ? AND f.score >= ?
                ORDER BY f.score DESC
                LIMIT ?
            """, (place_id, threshold, limit)).fetchall()
        elif place_name:
            rows = conn.execute("""
                SELECT f.place_id, f.name_zh, f.catalog_id, f.title_zh, f.title_vi,
                       f.score, f.rank,
                       v.dynasty_vi, v.translator_vi,
                       v.q_number, v.sh_number, v.juans,
                       v.source_name, v.license_name, v.cbeta_ref
                FROM cbeta_catalog_place_fuzzy f
                JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                WHERE (f.name_zh = ? OR f.name_zh LIKE ?) AND f.score >= ?
                ORDER BY f.score DESC
                LIMIT ?
            """, (place_name, f'%{place_name}%', threshold, limit)).fetchall()
        else:
            conn.close()
            return jsonify({"ok": False, "error": "Provide place_name or place_id"}), 400

        conn.close()
        return jsonify({
            "ok": True,
            "count": len(rows),
            "results": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/search-person', methods=['POST'])
def cbeta_search_person():
    """
    POST /daoanh/api/admin/cbeta/search-person
    Body: {"person_name": "..."}
    """
    try:
        data = request.get_json(force=True) or {}
        person_name = (data.get('person_name') or data.get('query') or '').strip()
        if not person_name:
            return jsonify({"has_cbeta": False, "results": [], "message": "no_match"}), 200
        limit = min(int(data.get('limit', 50)), 200)
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT cbeta_text_sigla AS sigla, person_name_zh, dila_person_id, juan, page, context_snippet "
            "FROM cbeta_person_mentions WHERE person_name_zh LIKE ? ORDER BY juan LIMIT ?",
            (f'%{person_name}%', limit)
        ).fetchall()
        results = []
        for r in rows:
            cconn = get_cbeta_conn()
            title_zh_row = cconn.execute(
                "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (r['sigla'],)
            ).fetchone()
            cconn.close()
            results.append({
                "sigla": r['sigla'],
                "title_zh": title_zh_row['title_zh'] if title_zh_row else '',
                "juan": r['juan'],
                "page": r['page'],
                "context_snippet": r['context_snippet'],
                "dila_id": r['dila_person_id']
            })
        conn.close()
        # Fallback: FTS search for person name in text
        if len(results) < limit:
            remaining = limit - len(results)
            try:
                cconn = get_cbeta_conn()
                fts_rows = cconn.execute(
                    "SELECT sigla, title_zh, juan, page, snippet(cbeta_fts, 4, '<mark>', '</mark>', '...', 30) AS ctx "
                    "FROM cbeta_fts WHERE cbeta_fts MATCH ? ORDER BY rank LIMIT ?",
                    (person_name, remaining)
                ).fetchall()
                for r in fts_rows:
                    results.append({
                        "sigla": r['sigla'],
                        "title_zh": r['title_zh'],
                        "juan": r['juan'],
                        "page": r['page'],
                        "context_snippet": r['ctx'],
                        "dila_id": None,
                        "type": "fts"
                    })
                cconn.close()
            except Exception as fts_err:
                app.logger.warning(f"CBETA FTS search failed for '{person_name}': {fts_err}")
            # 2b. LIKE fallback for CJK
            if len(results) < remaining:
                remaining2 = remaining - len(results)
                try:
                    cconn2 = get_cbeta_conn()
                    like_rows = cconn2.execute(
                        "SELECT t.sigla, t.title_zh, ci.juan, ci.page, "
                        "SUBSTR(ci.content_zh, MAX(1, INSTR(ci.content_zh, ?) - 40), 120) AS ctx "
                        "FROM cbeta_content_index ci JOIN cbeta_texts t ON t.id = ci.text_id "
                        "WHERE ci.content_zh LIKE ? LIMIT ?",
                        (person_name, f'%{person_name}%', remaining2)
                    ).fetchall()
                    for r in like_rows:
                        results.append({
                            "sigla": r['sigla'],
                            "title_zh": r['title_zh'],
                            "juan": r['juan'],
                            "page": r['page'],
                            "context_snippet": r['ctx'],
                            "dila_id": None,
                            "type": "like"
                        })
                    cconn2.close()
                except Exception as like_err:
                    app.logger.warning(f"CBETA LIKE search failed for '{person_name}': {like_err}")
        has_cbeta = len(results) > 0
        return jsonify({"has_cbeta": has_cbeta, "results": results, "total": len(results), "message": "found" if has_cbeta else "no_match", "error": False})
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA search-person error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": True, "message": "cbeta_internal_error"}), 500


@app.route('/daoanh/api/admin/cbeta/stats')
def cbeta_stats():
    """GET /daoanh/api/admin/cbeta/stats — DB statistics."""
    try:
        cconn = get_cbeta_conn()
        texts = cconn.execute("SELECT COUNT(*) AS c FROM cbeta_texts").fetchone()['c']
        paras = cconn.execute("SELECT COUNT(*) AS c FROM cbeta_content_index").fetchone()['c']
        fts = cconn.execute("SELECT COUNT(*) AS c FROM cbeta_fts").fetchone()['c']
        import_count = cconn.execute(
            "SELECT COUNT(*) AS c FROM cbeta_import_log WHERE status='success'"
        ).fetchone()['c']
        cconn.close()
        conn = get_db_connection()
        place_m = conn.execute("SELECT COUNT(*) AS c FROM cbeta_place_mentions").fetchone()['c']
        person_m = conn.execute("SELECT COUNT(*) AS c FROM cbeta_person_mentions").fetchone()['c']
        conn.close()
        return jsonify({
            "success": True,
            "texts": texts,
            "paragraphs": paras,
            "fts_entries": fts,
            "files_imported": import_count,
            "place_mentions": place_m,
            "person_mentions": person_m
        })
    except Exception as e:
        return jsonify({"error": True, "success": False, "message": str(e)})


@app.route('/daoanh/api/admin/cbeta/quality-report')
def cbeta_quality_report():
    """GET /daoanh/api/admin/cbeta/quality-report — T50: full CBETA data quality report."""
    try:
        conn = get_db_connection()

        # Fuzzy match quality
        fuzzy_total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy").fetchone()[0]
        fuzzy_low = conn.execute(
            "SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy WHERE low_confidence = 1"
        ).fetchone()[0]
        fuzzy_high = fuzzy_total - fuzzy_low

        # Fuzzy score distribution
        fuzzy_dist = conn.execute("""
            SELECT CAST(score AS INTEGER) as bucket, COUNT(*) as cnt
            FROM cbeta_catalog_place_fuzzy GROUP BY bucket ORDER BY bucket
        """).fetchall()

        # Catalog mapping audit
        cm_total = conn.execute("SELECT COUNT(*) FROM catalog_mapping").fetchone()[0]
        cm_orphaned = conn.execute(
            "SELECT COUNT(*) FROM catalog_mapping WHERE quality_flag = 'orphaned'"
        ).fetchone()[0]
        cm_verified = conn.execute(
            "SELECT COUNT(*) FROM catalog_mapping WHERE quality_flag = 'verified'"
        ).fetchone()[0]

        # Legacy canon mapping
        legacy_count = 0
        try:
            legacy_count = conn.execute("SELECT COUNT(*) FROM legacy_canon_mapping").fetchone()[0]
        except:
            pass

        # Translation status
        ref_passages_total = conn.execute("SELECT COUNT(*) FROM cbeta_ref_passages").fetchone()[0]
        ref_passages_translated = conn.execute(
            "SELECT COUNT(*) FROM cbeta_ref_passages WHERE vi_summary_clean IS NOT NULL AND vi_summary_clean != ''"
        ).fetchone()[0]
        ref_passages_pending = conn.execute(
            "SELECT COUNT(*) FROM cbeta_ref_passages WHERE han_text IS NOT NULL AND han_text != '' "
            "AND (vi_summary_clean IS NULL OR vi_summary_clean = '')"
        ).fetchone()[0]

        # Passage translation
        passage_total = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        passage_vi = conn.execute(
            "SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL AND vi_text != ''"
        ).fetchone()[0]

        # SAT / Toh crossref
        sat_count = conn.execute("SELECT COUNT(*) FROM sat_crossref").fetchone()[0]
        toh_count = conn.execute("SELECT COUNT(*) FROM toh_cbeta_crossref").fetchone()[0]
        catalog_count = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_vn").fetchone()[0]

        # Place mentions
        pm_total = conn.execute("SELECT COUNT(*) FROM cbeta_place_mentions").fetchone()[0]
        pp_total = conn.execute("SELECT COUNT(*) FROM cbeta_person_mentions").fetchone()[0]

        conn.close()

        return jsonify({
            "ok": True,
            "fuzzy": {
                "total": fuzzy_total,
                "high_confidence_ge80": fuzzy_high,
                "low_confidence_lt80": fuzzy_low,
                "distribution": [{"bucket": int(b), "count": c} for b, c in fuzzy_dist]
            },
            "catalog_mapping": {
                "total": cm_total,
                "valid": cm_verified,
                "orphaned": cm_orphaned
            },
            "legacy_canon": {
                "migrated": legacy_count
            },
            "translations": {
                "ref_passages_total": ref_passages_total,
                "ref_passages_translated": ref_passages_translated,
                "ref_passages_pending": ref_passages_pending,
                "passage_vi_total": passage_vi,
                "passage_total": passage_total
            },
            "crossref": {
                "sat": sat_count,
                "toh": toh_count,
                "catalog_total": catalog_count,
                "sat_coverage_pct": round(sat_count * 100 / catalog_count, 1) if catalog_count else 0
            },
            "mentions": {
                "place_mentions": pm_total,
                "person_mentions": pp_total
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/daoanh/api/admin/cbeta/snippet')
def cbeta_snippet():
    """
    GET /daoanh/api/admin/cbeta/snippet?id=T50n2060_p0457c16
    Returns the full logical unit (div/story/section) containing the page reference.
    Response: {success, sigla, title, page, unit_title, preview, full_text}
    """
    cbeta_id = request.args.get('id', '').strip()
    if not cbeta_id:
        return jsonify({"success": False, "error": "missing_id", "message": "Missing ?id= parameter"})
    m = re.match(r'^([A-Z])(\d+)n(\d+)_(p?\d+[a-z]\d*)$', cbeta_id)
    if not m:
        return jsonify({"success": False, "error": "invalid_id", "message": f"Invalid CBETA ID format: {cbeta_id}"})
    canon, vol_str, text_num, page_ref = m.group(1), m.group(2), m.group(3), m.group(4)
    sigla = f"{canon}{vol_str}n{text_num}"
    xml_path = os.path.join(DATA_DIR, 'cbeta', 'xml-p5a', canon, f"{canon}{vol_str}", f"{sigla}.xml")
    if not os.path.isfile(xml_path):
        return jsonify({
            "success": False, "error": "not_imported",
            "message": f"CBETA {sigla} chưa được import",
            "sigla": sigla, "cbeta_id": cbeta_id
        })
    try:
        import xml.etree.ElementTree as ET
        NS = 'http://www.tei-c.org/ns/1.0'
        tree = ET.parse(xml_path)
        root = tree.getroot()
        body = root.find(f'.//{{{NS}}}body') or root
        # Build element → parent map
        parent_map = {}
        stack = [(body, None)]
        while stack:
            el, p = stack.pop()
            parent_map[el] = p
            for child in list(el):
                stack.append((child, el))
        # Find matching <pb>
        all_pbs = list(body.iter(f'{{{NS}}}pb'))
        target_pb = None
        stripped_ref = page_ref.lstrip('p')
        for pb in all_pbs:
            n = pb.get('n', '')
            if n == page_ref or n == stripped_ref or n.startswith(stripped_ref):
                target_pb = pb
                break
        if target_pb is None:
            return jsonify({
                "success": False, "error": "page_not_found",
                "message": f"Page {page_ref} not found in {sigla}",
                "sigla": sigla, "cbeta_id": cbeta_id
            })
        # Walk up to find enclosing <div> (TEI or CBETA namespace)
        NS_CB = 'http://www.cbeta.org/ns/1.0'
        unit_div = None
        cur = parent_map.get(target_pb)
        while cur is not None and cur is not body:
            if cur.tag.endswith('}div'):
                unit_div = cur
                break
            cur = parent_map.get(cur)
        # If pb outside any div, find the next div sibling (any namespace)
        if unit_div is None:
            body_children = list(body)
            pb_idx = -1
            for i, c in enumerate(body_children):
                if c is target_pb:
                    pb_idx = i
                    break
            for c in body_children[pb_idx:]:
                if c.tag.endswith('}div'):
                    unit_div = c
                    break
        # Build full text: find all content in this div
        if unit_div is not None:
            unit_heads = unit_div.findall(f'{{{NS}}}head')
            unit_title = ''
            for h in unit_heads:
                ht = ''.join(h.itertext()).strip()
                if ht:
                    unit_title = ht
                    break
            # Extract plain text from all descendant elements
            all_text = []
            for child in list(unit_div):
                t = ''.join(child.itertext()).strip()
                if t:
                    all_text.append(t)
            # Also recursively get deeper text
            full_text = ''.join(unit_div.itertext()).strip()
            preview = full_text[:250] if full_text else ''
        else:
            # Fallback: get surrounding text from body
            unit_title = ''
            all_els = list(body.iter())
            start_el = target_pb
            texts = []
            for ei, el in enumerate(all_els):
                if el is start_el:
                    for j in range(ei + 1, min(ei + 15, len(all_els))):
                        txt = ''.join(all_els[j].itertext()).strip()
                        if txt and len(txt) > 5:
                            texts.append(txt)
                    break
            full_text = '\n'.join(texts)
            preview = full_text[:250] if full_text else ''
        # Get work title from DB
        cconn = get_cbeta_conn()
        title_row = cconn.execute(
            "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (sigla,)
        ).fetchone()
        cconn.close()
        work_title = title_row['title_zh'] if title_row else sigla
        return jsonify({
            "success": True,
            "cbeta_id": cbeta_id,
            "sigla": sigla,
            "title": work_title,
            "page": page_ref,
            "unit_title": unit_title,
            "preview": preview,
            "full_text": full_text,
            "has_full": bool(unit_div is not None)
        })
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA snippet error for {cbeta_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"error": True, "success": False, "message": str(e)})

@app.route('/daoanh/api/admin/cbeta/unit')
def cbeta_unit():
    """
    GET /daoanh/api/admin/cbeta/unit?id=X77n1524_p0484c06
    Returns has_local + full unit text (han_text) for a CBETA citation.
    On-demand loading — no auto-fetch.
    """
    cbeta_id = request.args.get('id', '').strip()
    if not cbeta_id:
        return jsonify({"has_local": False, "id": cbeta_id, "error": "missing_id"})
    m = re.match(r'^([A-Z])(\d+)n(\d+)_(p?\d+[a-z]\d*)$', cbeta_id)
    if not m:
        return jsonify({"has_local": False, "id": cbeta_id, "error": "invalid_id"})
    canon, vol_str, text_num, page_ref = m.group(1), m.group(2), m.group(3), m.group(4)
    sigla = f"{canon}{vol_str}n{text_num}"
    xml_path = os.path.join(DATA_DIR, 'cbeta', 'xml-p5a', canon, f"{canon}{vol_str}", f"{sigla}.xml")
    if not os.path.isfile(xml_path):
        # Fallback: try SQL query on cbeta_texts + cbeta_content_index
        try:
            cconn = get_cbeta_conn()
            text_row = cconn.execute(
                "SELECT id, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?",
                (sigla,)
            ).fetchone()
            if text_row:
                page_key = page_ref.lstrip('p')
                contents = cconn.execute("""
                    SELECT id, juan, page, content_zh
                    FROM cbeta_content_index
                    WHERE text_id = ? AND (page = ? OR page = ?)
                    ORDER BY line_num
                """, (text_row['id'], page_key, page_key.upper())).fetchall()
                if not contents:
                    prefix = page_key[:4]
                    contents = cconn.execute("""
                        SELECT id, juan, page, content_zh
                        FROM cbeta_content_index
                        WHERE text_id = ? AND page LIKE ?
                        ORDER BY page, line_num LIMIT 20
                    """, (text_row['id'], f"{prefix}%")).fetchall()
                cconn.close()
                if contents:
                    han_text = '\n'.join(r['content_zh'] for r in contents)
                    return jsonify({
                        "has_local": True, "id": cbeta_id, "sigla": sigla,
                        "work": text_row['title_zh'], "section": '',
                        "han_text": han_text[:50000],
                        "source": "db"
                    })
            else:
                cconn.close()
        except Exception:
            pass
        return jsonify({"has_local": False, "id": cbeta_id, "sigla": sigla,
                        "message": f"CBETA {sigla} chưa được import"})
    try:
        import xml.etree.ElementTree as ET
        NS = 'http://www.tei-c.org/ns/1.0'
        tree = ET.parse(xml_path)
        root = tree.getroot()
        body = root.find(f'.//{{{NS}}}body') or root
        # Build parent map
        parent_map = {}
        stack = [(body, None)]
        while stack:
            el, p = stack.pop()
            parent_map[el] = p
            for child in list(el):
                stack.append((child, el))
        # Find <pb>
        all_pbs = list(body.iter(f'{{{NS}}}pb'))
        target_pb = None
        stripped_ref = page_ref.lstrip('p')
        for pb in all_pbs:
            n = pb.get('n', '')
            if n == page_ref or n == stripped_ref or n.startswith(stripped_ref):
                target_pb = pb
                break
        if target_pb is None:
            return jsonify({"has_local": False, "id": cbeta_id, "sigla": sigla,
                            "error": "page_not_found", "page": page_ref})
        # Walk up to enclosing <div>
        unit_div = None
        cur = parent_map.get(target_pb)
        while cur is not None and cur is not body:
            if cur.tag.endswith('}div'):
                unit_div = cur
                break
            cur = parent_map.get(cur)
        if unit_div is None:
            body_children = list(body)
            pb_idx = -1
            for i, c in enumerate(body_children):
                if c is target_pb:
                    pb_idx = i
                    break
            for c in body_children[pb_idx:]:
                if c.tag.endswith('}div'):
                    unit_div = c
                    break
        # Extract han_text
        if unit_div is not None:
            unit_heads = unit_div.findall(f'{{{NS}}}head')
            section = ''
            for h in unit_heads:
                ht = ''.join(h.itertext()).strip()
                if ht:
                    section = ht
                    break
            han_text = ''.join(unit_div.itertext()).strip()
        else:
            section = ''
            texts = []
            all_els = list(body.iter())
            for ei, el in enumerate(all_els):
                if el is target_pb:
                    for j in range(ei + 1, min(ei + 15, len(all_els))):
                        txt = ''.join(all_els[j].itertext()).strip()
                        if txt and len(txt) > 5:
                            texts.append(txt)
                    break
            han_text = '\n'.join(texts)
        # Get work title
        cconn = get_cbeta_conn()
        title_row = cconn.execute(
            "SELECT title_zh FROM cbeta_texts WHERE sigla = ?", (sigla,)
        ).fetchone()
        cconn.close()
        work = title_row['title_zh'] if title_row else sigla
        return jsonify({
            "has_local": True,
            "id": cbeta_id,
            "sigla": sigla,
            "work": work,
            "section": section,
            "han_text": han_text[:50000] if han_text else ''
        })
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA unit error for {cbeta_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"has_local": False, "id": cbeta_id, "error": "parse_error"})


@app.route('/daoanh/api/admin/cbeta/fulltext')
def cbeta_fulltext():
    """
    GET /daoanh/api/admin/cbeta/fulltext?id=X77n1524_p0400c10
    SQL-based CBETA fulltext lookup from cbeta_texts + cbeta_content_index.
    Falls back to XML-based /cbeta/unit if DB has no matching sigla.
    """
    cbeta_id = request.args.get('id', '').strip()
    if not cbeta_id:
        return jsonify({"success": False, "error": "missing_id"})
    m = re.match(r'^([A-Z])(\d+)n(\d+)_(p?\d+[a-z]\d*)$', cbeta_id)
    if not m:
        return jsonify({"success": False, "error": "invalid_id", "message": f"Invalid format: {cbeta_id}"})
    canon, vol_str, text_num, page_ref = m.group(1), m.group(2), m.group(3), m.group(4)
    sigla = f"{canon}{vol_str}n{text_num}"
    page_key = page_ref.lstrip('p')

    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id, sigla, title_zh, author_zh, translator_zh FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()

        if text_row:
            text_id = text_row['id']
            contents = cconn.execute("""
                SELECT id, juan, page, line_num, content_zh
                FROM cbeta_content_index
                WHERE text_id = ? AND (page = ? OR page = ?)
                ORDER BY line_num
            """, (text_id, page_key, page_key.upper())).fetchall()
            if not contents:
                prefix = page_key[:4]
                contents = cconn.execute("""
                    SELECT id, juan, page, line_num, content_zh
                    FROM cbeta_content_index
                    WHERE text_id = ? AND page LIKE ?
                    ORDER BY page, line_num LIMIT 20
                """, (text_id, f"{prefix}%")).fetchall()
            full_text = '\n'.join(r['content_zh'] for r in contents) if contents else ''
            cconn.close()
            return jsonify({
                "source": "db",
                "citation_id": cbeta_id,
                "sigla": text_row['sigla'],
                "title": text_row['title_zh'],
                "author": text_row['author_zh'],
                "page": page_key,
                "content_blocks": len(contents),
                "full_text": full_text[:50000]
            })
        cconn.close()
        return jsonify({
            "source": "none",
            "citation_id": cbeta_id,
            "sigla": sigla,
            "message": f"CBETA {sigla} chưa được import vào database"
        })
    except Exception as e:
        import traceback
        app.logger.error(f"CBETA fulltext error: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e), "citation_id": cbeta_id})


@app.route('/daoanh/api/admin/cbeta/resolve')
def cbeta_resolve():
    """
    GET /daoanh/api/admin/cbeta/resolve?ref=T50n2060_p0457c16
    Pure Han text resolver from cbeta.db only.
    NEVER joins cbeta_ref_passages or any Vietnamese/translation table.
    Layer 1 of the two-layer architecture:
      Layer 1 (this): resolve_ref → pure Han text
      Layer 2:          translate_ref → LLM translation of han_text
    Returns JSON with ensure_ascii=False (raw UTF-8 Han chars).
    """
    ref = request.args.get('ref', '').strip()
    context = request.args.get('context', '').strip()
    if not ref:
        return jsonify({"ok": False, "error": "missing_ref", "message": "Thiếu ref"}), 400

    parsed = parse_ref(ref)
    if not parsed:
        return jsonify({"ok": False, "error": "invalid_ref", "message": f"Ref không đúng định dạng: {ref}"}), 400

    sigla = parsed['sigla']
    page_comp = parsed['page_comp']
    page_num = parsed['page_num']
    line_num = parsed['line_num']

    try:
        cconn = get_cbeta_conn()
        text_row = cconn.execute(
            "SELECT id, sigla, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()

        if not text_row:
            cconn.close()
            return jsonify({
                "ok": False, "success": False, "error": "not_imported",
                "message": f"CBETA {sigla} chưa được import vào cbeta.db",
                "sigla": sigla
            }), 404

        text_id = text_row['id']
        title = text_row['title_zh'] or sigla

        # Exact page+col match (e.g. page='0457c')
        rows = cconn.execute("""
            SELECT juan, page, line_num, content_zh FROM cbeta_content_index
            WHERE text_id = ? AND (page = ? OR page = ?)
            ORDER BY page, rowid LIMIT 20
        """, (text_id, page_comp, page_comp.upper())).fetchall()

        if not rows:
            # Prefix fallback: find any column for this page number
            rows = cconn.execute("""
                SELECT juan, page, line_num, content_zh FROM cbeta_content_index
                WHERE text_id = ? AND page LIKE ?
                ORDER BY page, rowid LIMIT 20
            """, (text_id, f"{page_num}%")).fetchall()

        if not rows and context:
            # Context-aware fallback: search nearby pages for context term
            nearby = cconn.execute("""
                SELECT juan, page, line_num, content_zh FROM cbeta_content_index
                WHERE text_id = ?
                ORDER BY ABS(CAST(page AS INTEGER) - ?)
                LIMIT 200
            """, (text_id, page_num)).fetchall()
            context_rows = [r for r in nearby if r['content_zh'] and context in r['content_zh']]
            if context_rows:
                rows = context_rows[:5]

        cconn.close()

        if not rows:
            return jsonify({
                "ok": False, "success": False, "error": "page_not_found",
                "message": f"Không tìm thấy trang {page_comp} cho {sigla} trong cbeta.db",
                "sigla": sigla, "page": page_comp
            }), 404

        han_text = '\n'.join(r['content_zh'] for r in rows)
        source_page = rows[0]['page']

        return Response(
            json.dumps({
                "ok": True, "success": True,
                "ref": ref,
                "sigla": sigla,
                "title": title,
                "author": text_row['author_zh'] or '',
                "page": source_page,
                "ref_page": page_comp,
                "line_num": line_num,
                "han_text": han_text[:50000],
                "content_blocks": len(rows),
                "source": "cbeta.db"
            }, ensure_ascii=False),
            mimetype='application/json'
        )
    except Exception as e:
        app.logger.error(f"cbeta_resolve error: {e}")
        return jsonify({"ok": False, "success": False, "error": "internal_error", "message": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/context')
def cbeta_context():
    """
    GET /daoanh/api/admin/cbeta/context?work=T50n2060&query=少林寺&window=2
    Search for query across all pages of a work, return Han-only context windows.
    Each result is one matching segment with N context segments before/after.
    """
    work = request.args.get('work', '').strip()
    query = request.args.get('query', '').strip()
    window = request.args.get('window', 2, type=int)

    if not work or not query:
        return jsonify({"error": "missing_params", "message": "Thiếu work hoặc query"}), 400

    if window < 1:
        window = 1
    if window > 10:
        window = 10

    try:
        cconn = get_cbeta_conn()

        sigla_match = re.match(r'^([A-Z]\d+n\d+)', work)
        sigla = sigla_match.group(1) if sigla_match else work

        text_row = cconn.execute(
            "SELECT id, sigla, title_zh, author_zh FROM cbeta_texts WHERE sigla = ?",
            (sigla,)
        ).fetchone()

        if not text_row:
            cconn.close()
            return jsonify({"error": "work_not_found", "message": f"Không tìm thấy {sigla} trong cbeta.db"}), 404

        rows = cconn.execute(
            "SELECT rowid, juan, page, line_num, content_zh FROM cbeta_content_index WHERE text_id = ? ORDER BY rowid",
            (text_row['id'],)
        ).fetchall()
        cconn.close()

        # Flatten all rows, then split into sentence segments by Chinese punctuation
        all_text = '\n'.join(r['content_zh'] or '' for r in rows)
        segments = re.split(r'[。！？；\n]+', all_text)
        segments = [s.strip() for s in segments if s.strip()]

        def han_only(text):
            if not text:
                return ''
            return ' '.join(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+', text))

        results = []
        for i, seg in enumerate(segments):
            if query not in seg:
                continue
            before = segments[max(0, i - window):i]
            after = segments[i + 1:i + 1 + window]
            results.append({
                "segment_id": f"{sigla}_seg{i:04d}",
                "context_before": [han_only(s) for s in before],
                "match": query,
                "context_after": [han_only(s) for s in after],
            })

        return jsonify({
            "work": work,
            "sigla": sigla,
            "title": text_row['title_zh'],
            "author": text_row['author_zh'] or '',
            "query": query,
            "window": window,
            "matches_found": len(results),
            "results": results[:50]
        })
    except Exception as e:
        app.logger.error(f"cbeta_context error: {e}")
        return jsonify({"error": "internal_error", "message": str(e)}), 500


@app.route('/daoanh/api/admin/cbeta/translate_segment', methods=['POST'])
def cbeta_translate_segment():
    """
    POST /daoanh/api/admin/cbeta/translate_segment
    Body: {"han_text": "…", "segment_id": "T50n2060_seg9098"}
    Splits han_text into sentences, translates each with Google Translate fallback,
    returns bilingual units: [{han, vi}, ...].
    """
    body = request.get_json(silent=True) or {}
    han_text = (body.get('han_text') or '').strip()
    segment_id = (body.get('segment_id') or '').strip()
    if not han_text:
        return jsonify({"error": "missing_han_text"}), 400

    try:
        segments = re.split(r'(?<=[。！？；])', han_text)
        segments = [s.strip() for s in segments if s.strip()]

        units = []
        for i, seg in enumerate(segments):
            vi = ''
            try:
                from deep_translator import GoogleTranslator
                vi = GoogleTranslator(source='zh-CN', target='vi').translate(seg[:2000])
            except Exception:
                vi = ''
            units.append({"han": seg, "vi": vi or ''})

        fallback = len(units) == 0
        if fallback:
            vi = ''
            try:
                from deep_translator import GoogleTranslator
                vi = GoogleTranslator(source='zh-CN', target='vi').translate(han_text[:2000])
            except Exception:
                vi = ''
            units.append({"han": han_text, "vi": vi or ''})

        return jsonify({
            "segment_id": segment_id,
            "units": units,
            "sentence_count": len(units),
            "source": "google-translate"
        })
    except Exception as e:
        app.logger.error(f"cbeta_translate_segment error: {e}")
        return jsonify({"error": "internal_error", "message": str(e)}), 500


@app.route('/daoanh/api/admin/llm/summarize', methods=['POST'])
def llm_summarize():
    """
    POST /daoanh/api/admin/llm/summarize
    Body: {"han_text": "...", "place_name": "Thiếu Lâm Tự"}
    Returns {summary_vi, provider}.
    Demo kỹ thuật — Gemini free tier, fallback GoogleTranslator, fallback raw.
    """
    body = request.get_json(silent=True) or {}
    han_text = (body.get('han_text') or '').strip()
    place_name = (body.get('place_name') or body.get('place', '')).strip()
    if not han_text:
        return jsonify({"summary_vi": "", "provider": "none", "error": "missing_han_text"})
    if len(han_text) > 8000:
        han_text = han_text[:8000]
    han_sentence = extract_sentence_with_place(han_text, place_name) if place_name else ''
    llm_input = han_sentence if han_sentence else han_text
    prompt = (
        "Tóm tắt đoạn Hán văn sau bằng tiếng Việt, tập trung vào địa danh «" + place_name + "».\n"
        "Giữ nguyên tên riêng, địa danh, niên hiệu.\n"
        "Độ dài: nếu 1–2 câu Hán → 1–2 câu Việt; nếu 5–10 câu nhiều chi tiết → 5–7 câu.\n"
        "Phải có đủ ý chính, không chỉ ghi 1 câu chung chung.\n"
        "Chỉ trả về bản tóm tắt, không thêm giải thích:\n\n"
        f"{llm_input}"
    )
    # Try Gemini free tier
    try:
        GEMINI_KEY = "AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_KEY}"
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=15)
        result = resp.json()
        if 'candidates' in result and result['candidates']:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            if summary:
                summary = clean_gemini_output(summary)
                return jsonify({"summary_vi": summary, "provider": "gemini-3.6-flash"})
    except Exception:
        pass
    # Fallback: translators (Google)
    try:
        import translators as ts
        summary = ts.translate_text(llm_input[:3000], to_language='vi', translator='google')
        if summary:
            summary = clean_gemini_output(summary)
            return jsonify({"summary_vi": summary, "provider": "google-translate"})
    except Exception:
        pass
    # Fallback: deep-translator
    try:
        from deep_translator import GoogleTranslator
        summary = GoogleTranslator(source='zh-CN', target='vi').translate(llm_input[:2000])
        if summary:
            summary = clean_gemini_output(summary)
            return jsonify({"summary_vi": summary, "provider": "google-translate"})
    except Exception:
        pass
    # Last fallback: return first 500 chars raw
    return jsonify({"summary_vi": llm_input[:500] + '…', "provider": "fallback"})


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


@app.route('/daoanh/api/admin/wiki/fetch', methods=['POST'])
def wiki_fetch():
    """
    POST /daoanh/api/admin/wiki/fetch
    Body: {"place_id": "PL...", "name_vi": "...", "name_zh": "...", "refresh": bool}
    Returns {has_wiki, wiki_title, wiki_url, snippet, full_text, content_html, lang,
             license, cached_at}. Auto-saves snapshot to place_wiki_snapshots. Always 200.

    T07 (2026-08-22): rewritten — the previous version's zh fallback lived inside a
    `continue`-guarded branch that never ran when the vi request itself raised (only
    when vi succeeded but matched nothing), and there was no en tier despite the task
    calling for vi -> zh -> en. Now tries each language in order, each against both
    name_zh (usually the more distinctive/matchable title across editions) and
    name_vi. Also adds `refresh` to force a live re-fetch (T07 UI's "Làm mới" button)
    and records which language matched (`source` column) so the UI can show a lang
    badge — previously this info was fetched but silently discarded before saving.
    """
    body = request.get_json(silent=True) or {}
    place_id = (body.get('place_id') or '').strip()
    name_vi = (body.get('name_vi') or '').strip()
    name_zh = (body.get('name_zh') or '').strip()
    refresh = bool(body.get('refresh'))
    if not place_id:
        return jsonify({"has_wiki": False, "error": "missing_place_id"})

    conn = get_db_connection()
    try:
        conn.execute("SELECT content_html FROM place_wiki_snapshots LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE place_wiki_snapshots ADD COLUMN content_html TEXT")
        conn.commit()

    if not refresh:
        cached = conn.execute(
            "SELECT wiki_title, wiki_url, snippet, full_text, content_html, source, license, created_at "
            "FROM place_wiki_snapshots WHERE place_id = ?",
            (place_id,)
        ).fetchone()
        if cached:
            conn.close()
            return jsonify({
                "has_wiki": True,
                "wiki_title": cached['wiki_title'] or '',
                "wiki_url": cached['wiki_url'] or '',
                "snippet": cached['snippet'] or '',
                "full_text": cached['full_text'] or '',
                "content_html": cached['content_html'] or '',
                "lang": cached['source'] or '',
                "license": cached['license'] or 'CC BY-SA 4.0',
                "cached_at": cached['created_at'] or ''
            })

    HEADERS = {'User-Agent': 'DaoAnh/1.0 (Buddhist Geography Tool; +https://phatphaponline.org)'}
    found = None
    for lang in ('vi', 'zh', 'en'):
        for term in (name_zh, name_vi):
            if not term:
                continue
            found = _wiki_search_lang(lang, term, HEADERS)
            if found:
                break
        if found:
            break

    if not found:
        conn.close()
        return jsonify({"has_wiki": False})

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("""
        INSERT OR REPLACE INTO place_wiki_snapshots
        (place_id, wiki_title, wiki_url, snippet, full_text, content_html, source, license, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (place_id, found['title'], found['url'], found['snippet'], found['full_text'],
          found['content_html'], found['lang'], 'CC BY-SA 4.0', now, now))
    conn.commit()
    conn.close()
    return jsonify({
        "has_wiki": True,
        "wiki_title": found['title'],
        "wiki_url": found['url'],
        "snippet": found['snippet'],
        "full_text": found['full_text'],
        "content_html": found['content_html'],
        "lang": found['lang'],
        "license": "CC BY-SA 4.0",
        "cached_at": now
    })


@app.route('/daoanh/api/admin/parse_district', methods=['POST'])
def parse_district():
    """POST /daoanh/api/admin/parse_district
    Input: {district: str, country: str}
    Output: {success, country_vi, province, district_vi, formatted}
    Uses rule-based parse_dila_district() — no HVDic, no AI.
    """
    data = request.get_json() or {}
    district_str = (data.get('district') or '').strip()
    country_hint = (data.get('country') or '').strip()
    if not district_str and not country_hint:
        return jsonify({"success": False, "error": "Thiếu dữ liệu"}), 400
    parsed = parse_dila_district(district_str)
    if not parsed.get('country_vi') and country_hint:
        parsed['country_vi'] = country_hint
    if not parsed.get('formatted'):
        parts = [p for p in [parsed.get('district_vi', ''), parsed.get('country_vi', '')] if p]
        parsed['formatted'] = ', '.join(parts)
        parsed['success'] = True
    return jsonify(parsed)

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


@app.route('/daoanh/api/admin/namevi-map-places/save', methods=['POST'])
def save_mapping():
    try:
        data = request.json
        name_vi = title_case_vi(data.get('name_vi', ''))
        vn_status = data.get('vn_name_status', 'reviewed')
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, gps_lat, gps_long, note_vi, district_vi, country_vi, source, needs_review, vn_name_status, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'manual', 0, ?, 1.0)
        """, (str(data['dila_id']), name_vi, data['name_zh'], data.get('gps_lat', ''), data.get('gps_long', ''), data.get('note_vi', ''), data.get('district_vi', ''), data.get('country_vi', ''), vn_status))
        # Also persist into places_pending.name_vi + name_vi_norm so search works
        conn.execute("UPDATE places_pending SET name_vi = ?, name_vi_norm = ? WHERE id = ?", (name_vi, normalize_text(name_vi), str(data['dila_id'])))
        # T67: ghi quyết định canonical + audit log + chuyển entity_hub.status='verified'
        _vs = (data.get('verification_status') or 'verified')
        _persist_canonical_decision(
            conn, str(data['dila_id']), action='approve', field_name='name_vi',
            old_value=(data.get('prev_name_vi') or ''), new_value=name_vi,
            evidence_citations=(data.get('evidence_citations') or []),
            authority_rank=(data.get('authority_rank') or 'admin_approved'),
            verification_status=_vs,
            decision_note=(data.get('decision_note') or 'Human-in-the-loop approve (Đạo Ảnh)'),
            editor=(data.get('editor') or request.headers.get('X-Forwarded-Email') or 'admin'),
            mark_verified=(_vs in ('verified', 'canonical')),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã lưu Mapping thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/auto_save_name', methods=['POST'])
def auto_save_name():
    try:
        data = request.json
        dila_id = str(data.get('dila_id', ''))
        name_vi = title_case_vi(data.get('name_vi', ''))
        name_zh = data.get('name_zh', '')
        if not dila_id or not name_vi:
            return jsonify({"success": False, "error": "Thiếu dila_id hoặc name_vi"}), 400
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO namevi_map_places (dila_id, name_vi, name_zh, source, vn_name_status, confidence)
            VALUES (?, ?, ?, 'auto_generated', 'auto', 0.5)
        """, (dila_id, name_vi, name_zh))
        # Persist into places_pending.name_vi + name_vi_norm for search
        conn.execute("UPDATE places_pending SET name_vi = ?, name_vi_norm = ? WHERE id = ?", (name_vi, normalize_text(name_vi), dila_id))
        # T67: ghi nhận đổi tên auto (KHÔNG đánh verified — chờ admin duyệt)
        _persist_canonical_decision(
            conn, dila_id, action='update', field_name='name_vi',
            old_value=(data.get('prev_name_vi') or ''), new_value=name_vi,
            evidence_citations=(data.get('evidence_citations') or []),
            authority_rank=(data.get('authority_rank') or 'auto_transliterate'),
            verification_status=(data.get('verification_status') or 'needs_review'),
            decision_note=(data.get('decision_note') or 'Auto-generated VN name — chờ admin duyệt'),
            editor=(data.get('editor') or 'auto'),
            mark_verified=False,
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã lưu tên tự động"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/place/<id>/canonical')
def place_canonical(id):
    """T67c: trả về quyết định canonical hiện tại + audit history cho 1 địa danh."""
    try:
        conn = get_db_connection()
        ref = _resolve_place_id(conn, id)
        decision = conn.execute(
            "SELECT * FROM canonical_decision WHERE entity_ref = ?", (ref,)
        ).fetchone()
        history = conn.execute(
            "SELECT log_id, action, field_name, old_value, new_value, evidence_sources, authority_rank, editor, verification_status, created_at "
            "FROM en_audit_log WHERE entity_ref = ? ORDER BY log_id DESC LIMIT 50", (ref,)
        ).fetchall()
        hub = conn.execute(
            "SELECT status, updated_at FROM entity_hub WHERE canonical_label = ?", (ref,)
        ).fetchone()
        conn.close()
        return jsonify({
            "success": True,
            "entity_ref": ref,
            "decision": dict(decision) if decision else None,
            "history": [dict(h) for h in history],
            "entity_hub_status": dict(hub) if hub else None,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/place/<id>/authority')
def place_authority(id):
    """T68b: trả về authority rank + các nguồn đóng góp + conflict_pending cho 1 địa danh."""
    try:
        conn = get_db_connection()
        ref = _resolve_place_id(conn, id)
        a_map = _source_authority_map(conn)
        ranked = _name_vi_evidence(conn, ref, a_map)
        _detect_conflicts(conn, ranked, ref)
        conn.commit()
        conflicts = conn.execute(
            "SELECT * FROM conflict_pending WHERE entity_ref = ? AND status = 'pending' ORDER BY id",
            (ref,)
        ).fetchall()
        source_rows = conn.execute(
            "SELECT source_code, source_id, authority_score, precedence_order, implemented, note FROM source_authority ORDER BY authority_score DESC"
        ).fetchall()
        conn.close()
        return jsonify({
            "success": True,
            "entity_ref": ref,
            "canonical_candidates": [
                {"value": v, "score": d['score'], "sources": d['sources'],
                 "confidence": d['confidence'], "order": d['order']}
                for v, d in ranked
            ],
            "conflicts": [dict(c) for c in conflicts],
            "authority_matrix": [dict(r) for r in source_rows],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/place/<id>/conflict/resolve', methods=['POST'])
def place_conflict_resolve(id):
    """T68c: admin chọn 1 giá trị để giải quyết xung đột → ghi conflict_pending + en_audit_log."""
    try:
        data = request.json or {}
        conflict_id = data.get('conflict_id')
        choice = (data.get('choice_value') or '').strip()
        source_code = (data.get('source_code') or '').strip()
        editor = (data.get('editor') or request.headers.get('X-Forwarded-Email') or 'admin')
        if not conflict_id or not choice:
            return jsonify({"success": False, "error": "Thiếu conflict_id hoặc choice_value"}), 400
        conn = get_db_connection()
        ref = _resolve_place_id(conn, id)
        row = conn.execute(
            "SELECT * FROM conflict_pending WHERE id = ? AND entity_ref = ?", (conflict_id, ref)
        ).fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "error": "Không tìm thấy xung đột"}), 404
        now = datetime.now().isoformat(timespec='seconds')
        # Chọn value_a hoặc value_b HOẶC giá trị khác do admin nhập
        source_chosen = source_code or (row['source_a'] if choice == row['value_a'] else row['source_b'])
        conn.execute("""
            UPDATE conflict_pending
            SET status='resolved', resolved_choice=?, resolved_by=?, resolved_at=?
            WHERE id = ?
        """, (choice, editor, now, conflict_id))
        # Ghi audit log (T67 pattern) — provenance cho quyết định xung đột
        conn.execute("""
            INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value,
                evidence_sources, authority_rank, editor, verification_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'resolved', ?)
        """, (ref, 'resolve_conflict', row['field'], f"{row['source_a']}: {row['value_a']}|{row['source_b']}: {row['value_b']}", choice, source_chosen, str(max(row['authority_a'] or 0, row['authority_b'] or 0)), editor, now))
        # Nếu chọn tên Việt → cập nhật canonical_decision + entity_hub nếu chưa có
        if row['field'] == 'name_vi' and choice:
            _persist_canonical_decision(
                conn, ref, action='resolve_conflict', field_name='name_vi',
                old_value=(row['value_a'] if choice != row['value_a'] else row['value_b']),
                new_value=choice,
                evidence_citations=[f"conflict #{conflict_id} resolved ({source_chosen})"],
                authority_rank=(source_chosen or 'admin'),
                verification_status='verified',
                decision_note='Conflict resolved bằng lựa chọn của admin (T68)',
                editor=editor, mark_verified=True,
            )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã giải quyết xung đột", "resolved_choice": choice})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/conflicts')
def list_conflicts():
    """T68c: danh sách tất cả conflict_pending — admin xem và giải quyết."""
    try:
        status_filter = request.args.get('status', 'pending')
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        conn = get_db_connection()
        total = conn.execute(
            "SELECT COUNT(*) FROM conflict_pending WHERE status = ?", (status_filter,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM conflict_pending WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (status_filter, limit, offset)
        ).fetchall()
        matrix = conn.execute(
            "SELECT source_code, authority_score, implemented FROM source_authority ORDER BY authority_score DESC"
        ).fetchall()
        conn.close()
        return jsonify({
            "success": True,
            "total": total, "limit": limit, "offset": offset,
            "conflicts": [dict(r) for r in rows],
            "authority_matrix": [dict(r) for r in matrix],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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


@app.route('/daoanh/api/admin/places_auto_names')
def places_auto_names():
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))
        conn = get_db_connection()
        total = conn.execute("""
            SELECT COUNT(*) FROM namevi_map_places m
            JOIN places_pending p ON p.id = m.dila_id
            WHERE m.vn_name_status = 'auto'
        """).fetchone()[0]
        rows = conn.execute("""
            SELECT p.id, p.name_zh, m.name_vi, m.vn_name_status,
                   p.district_raw, p.country, p.gps_lat, p.gps_long
            FROM namevi_map_places m
            JOIN places_pending p ON p.id = m.dila_id
            WHERE m.vn_name_status = 'auto'
            ORDER BY p.id ASC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        conn.close()
        places = []
        for r in rows:
            row = dict(r)
            row['id'] = ensure_long_id(row['id'])
            places.append(row)
        return jsonify({"success": True, "total": total, "limit": limit, "offset": offset, "places": places})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/places_search')
def places_search():
    try:
        q = (request.args.get('q', '') or '').strip()
        cate = (request.args.get('cate', 'admin_place') or '').strip()
        print(f'[places_search] q={q!r} cate={cate!r}', flush=True)
        if not q:
            return jsonify({"success": True, "places": []})
        valid_cates = ('admin_place', 'temple_site', 'dynasty_region', 'mountain', 'river_lake', 'other')
        if cate not in valid_cates:
            cate = 'admin_place'

        cate_case = """
            CASE
                WHEN d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%' THEN 'temple_site'
                WHEN d.note_category LIKE '%山峰%' OR d.note_category LIKE '%山脈%' THEN 'mountain'
                WHEN d.note_category LIKE '%河流%' OR d.note_category LIKE '%湖泊%' OR d.note_category LIKE '%水系%' THEN 'river_lake'
                WHEN d.note_category LIKE '%人文地理區域%' THEN 'dynasty_region'
                WHEN d.note_category LIKE '%自然地理區域%' THEN 'other'
                ELSE 'admin_place'
            END
        """

        conn = get_db_connection()
        like = f'%{q}%'
        q_norm = normalize_text(q)
        like_norm = f'%{q_norm}%' if q_norm else None

        # Phase 0: FTS5 nhanh (cơ chế "gõ mớm" kiểu StarDict) — populate 1 lần, rồi MATCH tên có dấu / không dấu / ID / gõ dở (prefix)
        # Nếu FTS đã chạy mà không khớp => trả về rỗng nhanh (tránh chuỗi LIKE full-scan ~15s gây timeout).
        fts_tried = False
        try:
            ensure_places_search_fts(conn)
            ensure_places_pending_fts(conn)
            fts_tried = True

            # Dựng chuỗi MATCH từ cụ thể → prefix (bắt gõ dở từng ký tự "thiếu lâm t"):
            #   '"thiếu lâm tự"' (phrase) → 'thiếu lâm tự' (token AND) → 'thiếu* lâm* tự*' (prefix AND)
            fts_candidates = [f'"{q.replace(chr(34), chr(34)+chr(34))}"']
            if re.fullmatch(r'[\w\s]+', q, re.UNICODE):
                fts_candidates.append(q)
            prefix_terms = []
            for t in re.split(r'\s+', q.strip())[:6]:
                t = re.sub(r'["*():+\-#@~^&]', '', t)
                if t:
                    prefix_terms.append(t + '*')
            if prefix_terms:
                fts_candidates.append(' '.join(prefix_terms))

            fts_raw_ids = []
            for fq in fts_candidates:
                ids = []
                for table, col in (("places_search_fts", "dila_id"), ("places_pending_fts", "id")):
                    try:
                        cand = conn.execute(
                            f"SELECT {col} AS vid FROM {table} WHERE {table} MATCH ? LIMIT 100",
                            (fq,)
                        ).fetchall()
                        ids.extend(r['vid'] for r in cand if r['vid'])
                    except Exception:
                        continue
                if ids:
                    fts_raw_ids = ids
                    break
            if fts_raw_ids:
                seen = set()
                in_ids = []
                for raw in fts_raw_ids:
                    for form in (str(raw), ensure_long_id(raw)):
                        if form and form not in seen:
                            seen.add(form)
                            in_ids.append(form)
                if in_ids:
                    placeholders = ','.join('?' * len(in_ids))
                    rows = conn.execute(f"""
                        SELECT p.id, p.name_zh,
                               COALESCE(m.name_vi, p.name_vi) AS name_vi,
                               m.vn_name_status
                        FROM places_pending p
                        LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                        LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                        WHERE p.id IN ({placeholders})
                          AND ({cate_case}) = ?
                        ORDER BY
                            CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                            p.id ASC
                        LIMIT 20
                    """, in_ids + [cate, q, like]).fetchall()
                    if rows:
                        conn.close()
                        places = []
                        seen = set()
                        for r in rows:
                            row = dict(r)
                            lid = ensure_long_id(row['id'])
                            if lid in seen:
                                continue
                            seen.add(lid)
                            row['id'] = lid
                            places.append(row)
                        return jsonify({"success": True, "places": places, "mode": "fts"})
        except Exception:
            pass

        # Phase 0.5: query giống ID (PLxxxxxx hoặc số) → tra theo index id chính xác, không quét LIKE.
        # Tránh trường hợp tìm ID trong tab "sai" phải chạy full-scan ~4s rồi trả 0 kết quả.
        q_strip = q.strip()
        m_id = re.match(r'^(?:PL)?(\d{1,12})$', q_strip, re.IGNORECASE)
        if m_id:
            short_id = 'PL' + m_id.group(1)
            long_id = 'PL' + m_id.group(1).zfill(12)
            rows = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       m.vn_name_status
                FROM places_pending p
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                WHERE p.id IN (?, ?)
                  AND ({cate_case}) = ?
                ORDER BY p.id ASC
                LIMIT 20
            """, (short_id, long_id, cate)).fetchall()
            if rows:
                conn.close()
                places = []
                seen = set()
                for r in rows:
                    row = dict(r)
                    lid = ensure_long_id(row['id'])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    row['id'] = lid
                    places.append(row)
                return jsonify({"success": True, "places": places, "mode": "id"})
            conn.close()
            return jsonify({"success": True, "places": [], "mode": "none"})

        # FTS đã chạy nhưng không khớp → trả rỗng nhanh (tránh LIKE full-scan ~15s gây timeout).
        if fts_tried:
            conn.close()
            return jsonify({"success": True, "places": [], "mode": "fts_none"})

        # Phase 1: Direct DB search (with name_vi_norm for diacritics-free)
        # Chỉ chạy khi FTS chưa sẵn sàng (places_search_fts / places_pending_fts lỗi tạo index).
        where_parts = ["(p.id LIKE ? OR p.name_zh LIKE ? OR COALESCE(m.name_vi, p.name_vi) LIKE ?)"]
        params = [like, like, like]
        if like_norm:
            where_parts.append("p.name_vi_norm LIKE ?")
            params.append(like_norm)
        params.append(cate)
        params.append(q)
        params.append(like)

        rows = conn.execute(f"""
            SELECT p.id, p.name_zh,
                   COALESCE(m.name_vi, p.name_vi) AS name_vi,
                   m.vn_name_status
            FROM places_pending p
            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
            LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
            WHERE ({" OR ".join(where_parts)})
              AND ({cate_case}) = ?
            ORDER BY
                CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                p.id ASC
            LIMIT 20
        """, params).fetchall()

        if rows:
            conn.close()
            places = []
            seen = set()
            for r in rows:
                row = dict(r)
                lid = ensure_long_id(row['id'])
                if lid in seen:
                    continue
                seen.add(lid)
                row['id'] = lid
                places.append(row)
            return jsonify({"success": True, "places": places, "mode": "db"})

        # Phase 2: Word-level fallback — try matching individual query words
        # This helps when no place has the full query as name_vi but words match
        q_word_patterns = []
        if q_norm:
            q_words = q_norm.split()
            for w in q_words:
                if len(w) >= 2:
                    q_word_patterns.append(f'%{w}%')

        if q_word_patterns:
            word_conditions = " OR ".join(["(p.name_vi_norm LIKE ? OR COALESCE(m.name_vi, p.name_vi) LIKE ?)" for _ in q_word_patterns])
            word_params = []
            for w in q_word_patterns:
                word_params.extend([w, w])
            word_params.append(cate)
            try:
                rows = conn.execute(f"""
                    SELECT p.id, p.name_zh,
                           COALESCE(m.name_vi, p.name_vi) AS name_vi,
                           m.vn_name_status,
                           (SELECT COUNT(*) FROM places_pending p2
                            LEFT JOIN namevi_map_places m2 ON m2.dila_id = p2.id
                            WHERE p2.id = p.id AND ({word_conditions})) AS match_score
                    FROM places_pending p
                    LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                    LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                    WHERE ({word_conditions})
                      AND ({cate_case}) = ?
                    GROUP BY p.id
                    ORDER BY match_score DESC, p.id ASC
                    LIMIT 20
                """, word_params + word_params + [cate]).fetchall()
            except Exception:
                rows = []

            if rows:
                conn.close()
                places = []
                seen = set()
                for r in rows:
                    row = dict(r)
                    lid = ensure_long_id(row['id'])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    row['id'] = lid
                    places.append(row)
                return jsonify({"success": True, "places": places, "mode": "word_fallback"})

        # Phase 3: Việt → Hán lookup via hanviet_fallback (require multi-char match)
        hv_map = {}
        hv_rows = conn.execute("SELECT ch, hv FROM hanviet_fallback").fetchall()
        for r in hv_rows:
            hv_norm = normalize_text(r['hv'])
            if hv_norm not in hv_map:
                hv_map[hv_norm] = []
            hv_map[hv_norm].append(r['ch'])

        # For each query word, get matching Hán chars. Require at least 3 words matched.
        q_words = q_norm.split() if q_norm else []
        han_groups = []
        for word in q_words:
            if len(word) >= 2 and word in hv_map:
                han_groups.append(hv_map[word])

        if len(han_groups) >= 3:
            # Build AND condition: name_zh must contain at least one Hán char from EACH word
            han_conditions = " AND ".join([f"(p.name_zh LIKE ?)" for _ in han_groups])
            han_params = []
            for grp in han_groups:
                # Try each char from this group (OR within group)
                han_params.append(f'%{grp[0]}%')  # Use first char as pattern
            han_params.append(cate)
            rows = conn.execute(f"""
                SELECT p.id, p.name_zh,
                       COALESCE(m.name_vi, p.name_vi) AS name_vi,
                       m.vn_name_status
                FROM places_pending p
                LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
                WHERE {han_conditions}
                  AND ({cate_case}) = ?
                ORDER BY p.id ASC LIMIT 10
            """, han_params).fetchall()
            if rows:
                conn.close()
                places = []
                seen = set()
                for r in rows:
                    row = dict(r)
                    lid = ensure_long_id(row['id'])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    row['id'] = lid
                    places.append(row)
                return jsonify({"success": True, "places": places, "mode": "han_fallback"})

        conn.close()
        return jsonify({"success": True, "places": [], "mode": "none"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/search_all')
def search_all():
    try:
        q = (request.args.get('q', '') or '').strip()
        if not q:
            return jsonify({"success": True, "places": []})
        conn = get_db_connection()
        like = f'%{q}%'
        place_rows = conn.execute("""
            SELECT p.id, p.name_zh,
                   COALESCE(m.name_vi, p.name_vi) AS name_vi,
                   d.note_category, d.district,
                   CASE
                       WHEN d.note_category LIKE '%寺廟%' OR d.note_category LIKE '%佛塔%' OR d.note_category LIKE '%佛教文化地點%' THEN 'temple_site'
                       WHEN d.note_category LIKE '%山峰%' OR d.note_category LIKE '%山脈%' THEN 'mountain'
                       WHEN d.note_category LIKE '%河流%' OR d.note_category LIKE '%湖泊%' OR d.note_category LIKE '%水系%' THEN 'river_lake'
                       WHEN d.note_category LIKE '%人文地理區域%' THEN 'dynasty_region'
                       WHEN d.note_category LIKE '%自然地理區域%' THEN 'other'
                       ELSE 'admin_place'
                   END AS cate_internal
            FROM places_pending p
            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
            LEFT JOIN places_dila d ON d.id = 'PL' || SUBSTR('000000000000' || REPLACE(p.id, 'PL', ''), -12)
            WHERE p.id LIKE ? OR p.name_zh LIKE ? OR COALESCE(m.name_vi, p.name_vi) LIKE ?
            ORDER BY
                CASE WHEN p.id = ? THEN 0 WHEN p.id LIKE ? THEN 1 ELSE 2 END,
                p.id ASC
            LIMIT 50
        """, (like, like, like, q, like)).fetchall()

        person_rows = conn.execute("""
            SELECT pe.id, pe.name_zh,
                   pe.name_vi AS name_vi,
                   pe.dynasty AS district,
                   NULL AS note_category,
                   'person' AS cate_internal
            FROM people pe
            WHERE pe.id LIKE ? OR pe.name_zh LIKE ?
               OR pe.name_vi LIKE ?
            ORDER BY
                CASE WHEN pe.id = ? THEN 0 WHEN pe.id LIKE ? THEN 1 ELSE 2 END,
                pe.id ASC
            LIMIT 50
        """, (like, like, like, q, like)).fetchall()

        # Tìm theo tên tiếng Việt trong vn_person_authority (tên chuẩn hơn people.name_vi)
        auth_rows = conn.execute("""
            SELECT va.dila_id AS id,
                   COALESCE(NULLIF(va.name_zh,''), pe.name_zh) AS name_zh,
                   va.name_vi AS name_vi,
                   pe.dynasty AS district,
                   NULL AS note_category,
                   'person' AS cate_internal
            FROM vn_person_authority va
            LEFT JOIN people pe ON pe.id = va.dila_id
            WHERE va.name_vi LIKE ?
            ORDER BY CASE WHEN va.status = 'verified' THEN 0 ELSE 1 END,
                     va.dila_id ASC
            LIMIT 50
        """, (like,)).fetchall()

        conn.close()
        places = []
        seen = set()
        for r in list(place_rows) + list(auth_rows) + list(person_rows):
            row = dict(r)
            rid = row['id']
            if rid.startswith('PL'):
                lid = ensure_long_id(rid)
            else:
                lid = rid
            if lid in seen:
                continue
            seen.add(lid)
            row['id'] = lid
            places.append(row)
        return jsonify({"success": True, "places": places})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/daoanh/api/admin/ai-edit-code', methods=['POST'])
def ai_edit_code():
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    place_id = data.get('place_id', '')
    file_path = data.get('file_path', '')
    context = data.get('context', '')
    user_prompt = data.get('user_prompt', '')

    if not file_path or not user_prompt:
        return jsonify({"status": "error", "message": "Thiếu file_path hoặc user_prompt"}), 400

    abs_path = os.path.normpath(os.path.join(BASE_DIR, file_path))
    if not any(abs_path.startswith(os.path.normpath(d)) for d in ALLOWED_DIRS):
        return jsonify({"status": "error", "message": "Đường dẫn không được phép"}), 403
    if not os.path.isfile(abs_path):
        return jsonify({"status": "error", "message": "File không tồn tại"}), 404

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi đọc file: {str(e)}"}), 500

    full_prompt = f"""Context trang hiện tại:
- place_id: {place_id}
- Mô tả: {context}
- File đang chỉnh: {abs_path}

Yêu cầu cụ thể của admin:
{user_prompt}

Dưới đây là nội dung file hiện tại, hãy phân tích và sửa phù hợp:

----- FILE START -----
{current_code}
----- FILE END -----

Hãy trả về toàn bộ nội dung file sau khi đã chỉnh sửa, không giải thích dài dòng."""

    return jsonify({"status": "error", "message": "AI Code Editor đã bị vô hiệu hóa"}), 503

    try:
        backup_path = abs_path + f'.bak.{int(time.time())}'
        shutil.copy2(abs_path, backup_path)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi ghi file: {str(e)}"}), 500

    return jsonify({
        "status": "ok",
        "message": f"Đã cập nhật {file_path}. Backup: {os.path.basename(backup_path)}. Reload trang để thấy kết quả."
    })

@app.route('/daoanh/api/public/autocomplete')
def public_autocomplete():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({"success": True, "data": []})
    conn = get_db_connection()
    like = f'%{q}%'

    mapped = conn.execute(
        "SELECT DISTINCT dila_id AS id, name_vi AS value, name_zh AS name_zh, 'mapped' AS source FROM namevi_map_places WHERE name_vi LIKE ? LIMIT 10",
        (like,)
    ).fetchall()
    results = [dict(r) for r in mapped]
    seen = set(r['value'] for r in results)

    if len(results) < 10:
        remaining = 10 - len(results)
        pending = conn.execute(
            "SELECT DISTINCT id, name_zh AS value, name_zh AS name_zh, 'pending' AS source FROM places_pending WHERE name_zh LIKE ? LIMIT ?",
            (like, remaining)
        ).fetchall()
        for r in pending:
            if r['value'] not in seen:
                results.append(dict(r))
                seen.add(r['value'])

    if len(results) < 10:
        remaining = 10 - len(results)
        marcus = conn.execute(
            "SELECT node_id AS id, label_vi AS value, label AS name_zh, 'marcus' AS source FROM marcus_reference WHERE label_vi LIKE ? OR label LIKE ? LIMIT ?",
            (like, like, remaining)
        ).fetchall()
        for r in marcus:
            if r['value'] and r['value'] not in seen:
                results.append(dict(r))
                seen.add(r['value'])

    if len(results) < 10:
        remaining = 10 - len(results)
        lex = conn.execute(
            "SELECT term AS value, 'lexicon' AS source FROM lexicon WHERE term LIKE ? LIMIT ?",
            (like, remaining)
        ).fetchall()
        for r in lex:
            clean = r['value'].split("|")[0].split("(")[0].split(";")[0].strip()
            if len(clean) > 20:
                clean = clean[:20]
            if clean and clean not in seen:
                found = conn.execute("SELECT id FROM places_pending WHERE name_zh = ? LIMIT 1", (clean,)).fetchone()
                rid = found['id'] if found else None
                results.append({"value": clean, "name_zh": clean, "source": r['source'], "id": rid})
                seen.add(clean)

    conn.close()
    for r in results:
        if r.get('id'):
            r['id'] = ensure_long_id(r['id'])
        if len(r['value']) > 20:
            r['value'] = r['value'].split("|")[0].split("(")[0].split(";")[0].split("\n")[0].strip()[:20]
    return jsonify({"success": True, "data": results})

@app.route('/daoanh/api/public/transliterate')
def public_transliterate():
    text = request.args.get('text', '').strip()
    if not text:
        return jsonify({"success": False, "error": "Thiếu tham số text"}), 400
    try:
        import requests as req
        import urllib.parse
        url = "https://hvdic.thivien.net/transcript-query.json.php"
        payload = f"mode=trans&lang=1&input={urllib.parse.quote(text)}"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        resp = req.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
        result = resp.json().get('result', [])
        hanviet = " ".join([el.get('o', [''])[0] for el in result if el.get('o')])
        if hanviet and hanviet != text:
            return jsonify({"success": True, "result": hanviet})
    except Exception:
        pass
    fallback = {
        '中國': 'Trung Quốc', '中国': 'Trung Quốc', '阿富汗': 'Afghanistan',
        '省': 'Tỉnh ', '市': 'Thành phố ', '縣': 'Huyện ', '区': 'Quận ', '區': 'Quận ',
        '镇': 'Trấn ', '鎮': 'Trấn ', '村': 'Thôn ', '乡': 'Xã ', '鄉': 'Xã ',
        '雲南': 'Vân Nam', '河北': 'Hà Bắc', '山西': 'Sơn Tây', '山東': 'Sơn Đông',
        '河南': 'Hà Nam', '湖南': 'Hà Nam', '廣東': 'Quảng Đông', '廣西': 'Quảng Tây',
        '四川': 'Tứ Xuyên', '福建': 'Phúc Kiến', '巴基斯坦': 'Pakistan', '印度': 'Ấn Độ',
    }
    result = text
    for zh, vi in fallback.items():
        result = result.replace(zh, vi)
    return jsonify({"success": True, "result": result})

@app.route('/daoanh/api/search')
def api_global_search():
    """GET /daoanh/api/search?q=<text> — HOME page ("Tìm kiếm thiền sư, chùa chiền, kinh sách")
    global search. index.html has called this exact path/shape since it was built
    (data.monks/data.places/data.works, see displayResults() there) but the route
    never existed on the backend — 404 the entire time (found 2026-08-21 while
    checking what T01/T29's name_vi fix actually surfaces on HOME).

    Three sources, each already established/trusted elsewhere in this app:
      monks  -> people.name_vi/name_zh (T01/T29 just brought this to 100% non-empty)
      places -> places_pending + namevi_map_places (same COALESCE pattern as
                the persons/places endpoints elsewhere)
      works  -> cbeta_catalog_vn (Nguyễn Minh Tiến, CC BY-SA — already listed as a
                trusted source in CLAUDE.md, same table T-series "Kinh Điển Liên
                Quan" reads from)
    """
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({"success": True, "monks": [], "places": [], "works": []})
    conn = get_db_connection()
    like = f'%{q}%'
    try:
        monks = conn.execute("""
            SELECT id, name_vi, name_zh FROM people
            WHERE name_vi LIKE ? OR name_zh LIKE ?
            ORDER BY LENGTH(name_vi) ASC LIMIT 10
        """, (like, like)).fetchall()

        # Places: FTS5 (places_pending_fts) instead of LIKE — a LEFT JOIN + leading-
        # wildcard LIKE across places_pending/namevi_map_places (118K/118K rows) took
        # ~2.5s per query in testing, too slow for a live search box. Same
        # prefix-match pattern already proven in places_search() (T11 fix).
        #
        # IMPORTANT: an empty FTS result is a real, correct answer (most monk-only
        # queries genuinely match zero places) — it must NOT trigger the slow LIKE
        # fallback, or every such query pays the full ~2.5s scan anyway and the
        # optimization does nothing. The LIKE fallback below only runs if FTS itself
        # raised (a real failure to query it), tracked via fts_failed.
        ensure_places_pending_fts(conn)
        place_ids = []
        fts_failed = False
        try:
            terms = [re.sub(r'["*():+\-#@~^&]', '', t) + '*' for t in re.split(r'\s+', q.strip())[:6] if t]
            if terms:
                fq = ' '.join(terms)
                rows = conn.execute(
                    "SELECT id FROM places_pending_fts WHERE places_pending_fts MATCH ? LIMIT 10", (fq,)
                ).fetchall()
                place_ids = [r['id'] for r in rows]
        except Exception:
            fts_failed = True

        if place_ids:
            placeholders = ','.join('?' * len(place_ids))
            places = conn.execute(f"""
                SELECT p.id, COALESCE(m.name_vi, p.name_vi) AS name_vi, p.name_zh, p.province, p.gps_lat, p.gps_long
                FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE p.id IN ({placeholders})
            """, place_ids).fetchall()
        elif fts_failed:
            places = conn.execute("""
                SELECT p.id, COALESCE(m.name_vi, p.name_vi) AS name_vi, p.name_zh, p.province, p.gps_lat, p.gps_long
                FROM places_pending p LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                WHERE COALESCE(m.name_vi, p.name_vi) LIKE ? OR p.name_zh LIKE ?
                ORDER BY LENGTH(COALESCE(m.name_vi, p.name_vi)) ASC LIMIT 10
            """, (like, like)).fetchall()
        else:
            places = []

        works = conn.execute("""
            SELECT title_vi, title_zh, translator_vi AS author, dynasty_vi AS era
            FROM cbeta_catalog_vn
            WHERE title_vi LIKE ? OR title_zh LIKE ?
            ORDER BY LENGTH(title_vi) ASC LIMIT 10
        """, (like, like)).fetchall()

        return jsonify({
            "success": True,
            "monks": [dict(r) for r in monks],
            "places": [dict(r) for r in places],
            "works": [dict(r) for r in works],
        })
    except Exception as e:
        app.logger.error(f"api_global_search error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route('/daoanh/api/public/search')
def public_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"success": True, "data": []})
    conn = get_db_connection()
    like = f'%{q}%'
    mapped = conn.execute(
        "SELECT id, name_vi, name_zh FROM namevi_map_places WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 15",
        (like, like)
    ).fetchall()
    all_results = [dict(r) for r in mapped]
    if len(all_results) < 15:
        remaining = 15 - len(all_results)
        pending = conn.execute(
            "SELECT id, name_zh as name_vi, name_zh FROM places_pending WHERE name_zh LIKE ? LIMIT ?",
            (like, remaining)
        ).fetchall()
        all_results += [dict(r) for r in pending]
    conn.close()
    for r in all_results:
        if r.get('id'):
            r['id'] = ensure_long_id(r['id'])
    return jsonify({"success": True, "data": all_results})


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

# ===== STATIC FILE SERVING =====
@app.route('/daoanh/static/<path:path>')
def admin_css(path):
    static_dir = os.path.join(BASE_DIR, 'static')
    return send_from_directory(static_dir, path)

# ============ TTL / MARCUS / DOSSIER APIS ============

@app.route('/api/queue')
def api_queue():
    """
    GET /api/queue
    List TTL files from /data/ttl/old/ directory - EXACT filename match.
    """
    files = [f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')]
    queue = []
    conflicts = 0
    
    for filename in files:
        fpath = os.path.join(TTL_OLD_DIR, filename)
        
        # Read TTL content
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract label
        import re
        label_match = re.search(r'rdfs:label\s+"([^"]+)"', content)
        name_vi = label_match.group(1) if label_match else filename.replace('.ttl','')
        
        # Check for conflict
        has_conflict = 'LINEAGE_CONFLICT' in content or 'conflict' in content.lower()
        
        # USE EXACT FILENAME AS ID - case sensitive
        queue.append({
            'id': filename.replace('.ttl', ''),  # EXACT: TS-Dai-Hue-Tong-Cao
            'filename': filename,
            'name_vi': name_vi,
            'rank': 'A',
            'conflict': has_conflict,
            'status': 'pending'
        })
        if has_conflict:
            conflicts += 1
    
    return jsonify({
        'queue': queue,
        'total': len(queue),
        'conflicts': conflicts,
        'rank_a': len(queue),
        'rank_b': 0
    })

@app.route('/api/get_ttl/<path:filename>', methods=['GET'])
def api_get_ttl(filename):
    """
    GET /api/get_ttl/<path:filename>
    Exact filename match - accepts TS-Dai-Hue-Tong-Cao.ttl format.
    Parses TTL and returns structured fields for UI.
    """
    # Prevent path traversal
    if '..' in filename or '/' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    if not filename.endswith('.ttl'):
        filename += '.ttl'
    
    content = ""
    source = ""
    
    # Check old directory
    old_path = os.path.join(TTL_OLD_DIR, filename)
    if os.path.exists(old_path):
        with open(old_path, 'r', encoding='utf-8') as f:
            content = f.read()
        source = 'old'
    
    # Check master directory
    if not content:
        master_path = os.path.join(TTL_MASTER_DIR, filename)
        if os.path.exists(master_path):
            with open(master_path, 'r', encoding='utf-8') as f:
                content = f.read()
            source = 'master'
    
    if not content:
        return jsonify({'error': 'File not found'}), 404
    
    # Parse TTL to extract structured fields
    name_vi_match = re.search(r'rdfs:label\s+"([^"]+)"@vi', content)
    name_vi = name_vi_match.group(1) if name_vi_match else ""
    
    name_zh_match = re.search(r'rdfs:label\s+"([^"]+)"@zh', content)
    name_zh = name_zh_match.group(1) if name_zh_match else name_vi
    
    # Extract birth/death years
    birth_match = re.search(r'crm:P4_has_time-span\s+"(\d{4})"', content)
    birth_year = birth_match.group(1) if birth_match else None
    
    # Extract lineage/sect
    lineage_match = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"', content)
    sect = lineage_match.group(1) if lineage_match else ""
    
    # Extract dynasty
    dynasty_match = re.search(r'bkg:dynasty\s+"([^"]+)"', content)
    dynasty = dynasty_match.group(1) if dynasty_match else ""
    
    # Extract biographical note
    bio_match = re.search(r'bkg:biographicalNote\s+"([^"]+)"', content)
    bio = bio_match.group(1)[:500] if bio_match else ""
    
    # Extract teachers and students from TTL (bkg:hasTeacher, bkg:hasDisciple)
    teachers = re.findall(r'bkg:hasTeacher\s+<ex:monk/([^>]+)>', content)
    students = re.findall(r'bkg:hasDisciple\s+<ex:monk/([^>]+)>', content)
    
    return jsonify({
        'filename': filename,
        'ttl_content': content,
        'content': content,
        'source': source,
        'id': filename.replace('.ttl', ''),
        'name_vi': name_vi,
        'name_zh': name_zh,
        'birth_year': birth_year,
        'death_year': None,
        'sect': sect,
        'dynasty': dynasty,
        'bio': bio,
        'vps_teachers': teachers,
        'vps_students': students
    })

@app.route('/api/dossier/<dila_id>')
def api_dossier(dila_id):
    """
    GET /api/dossier/<dila_id>
    Get full dossier from DILA and Marcus for both columns.
    Includes TTL file fallback when not in DB.
    """
    # Strip TS- prefix if present
    lookup_id = dila_id
    if lookup_id.startswith('TS-'):
        lookup_id = lookup_id[3:]
    
    dila_data = get_dila_data(lookup_id)
    
    # FALLBACK: Parse TTL directly if not in DB - Extract ALL info
    ttl_content = ""
    ttl_file = ""
    if not dila_data:
        # Try to find TTL file by ID or filename pattern
        for f in os.listdir(TTL_OLD_DIR):
            if lookup_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                with open(ttl_file, 'r', encoding='utf-8') as fp:
                    ttl_content = fp.read()
                break
        
        if ttl_content:
            # Parse COMPLETE info from TTL
            import re
            
            # 1. Name VI from rdfs:label (main label only)
            label_match = re.search(r'rdfs:label\s+"([^"]+)"@vi', ttl_content)
            name_vi = label_match.group(1) if label_match else lookup_id
            
            # 2. Parse all names - find all appellation blocks
            all_names = []
            dharma_names = []
            secular_names = []
            
            # Find each block between [ and ]
            app_blocks = re.finditer(r'\[([^\]]+)\]', ttl_content)
            for block in app_blocks:
                block_text = block.group(1)
                name_match = re.search(r'rdfs:label\s+"([^"]+)"@([a-z]{2})', block_text)
                type_match = re.search(r'bkg:hasAppellationType\s+"bkg:(\w+)"', block_text)
                if name_match and type_match:
                    name = name_match.group(1)
                    app_type = type_match.group(1)
                    all_names.append({'name': name, 'lang': name_match.group(2), 'type': app_type})
                    if app_type == 'DharmaName':
                        dharma_names.append(name)
                    elif app_type == 'SecularName':
                        secular_names.append(name)
            
            # 3. Dharma lineage
            lineage_match = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"', ttl_content)
            lineage = lineage_match.group(1) if lineage_match else ''
            
            # 4. Birth/Death years - from event resources (E67_Birth, E69_Death)
            birth_match = re.search(r'a\s+crm:E67_Birth.*?crm:P4_has_time-span\s+"(\d{3,4})"', ttl_content, re.DOTALL)
            birth_year = int(birth_match.group(1)) if birth_match else None
            death_match = re.search(r'a\s+crm:E69_Death.*?crm:P4_has_time-span\s+"(\d{3,4})"', ttl_content, re.DOTALL)
            death_year = int(death_match.group(1)) if death_match else None
            
            # 5. Dynasty
            dynasty_match = re.search(r'bkg:dynasty\s+"([^"]+)"', ttl_content)
            dynasty = dynasty_match.group(1) if dynasty_match else ''
            
            # 6. Biographical note - single-line format (TTL uses " not """)
            bio_match = re.search(r'bkg:biographicalNote\s+"([^"]+)"', ttl_content)
            bio = bio_match.group(1)[:1000] if bio_match else ''
            
            # 7. Associated places - resolve to Vietnamese names
            places_matches = re.findall(r'bkg:associatedPlaces\s+<ex:place/([^>]+)>', ttl_content)
            # Resolve place IDs to names from TTL
            places_with_names = []
            place_label_map = {}
            for pm in re.finditer(r'<ex:place/([^>]+)>\s+rdfs:label\s+"([^"]+)"', ttl_content):
                place_label_map[pm.group(1)] = pm.group(2)
            for pid in places_matches:
                places_with_names.append({'id': pid, 'name_vi': place_label_map.get(pid, pid)})
            
            # 8. Authored works - resolve to names from TTL
            works_matches = re.findall(r'bkg:authoredWorks\s+<ex:work/([^>]+)>', ttl_content)
            work_label_map = {}
            for wm in re.finditer(r'<ex:work/([^>]+)>\s+rdfs:label\s+"([^"]+)"', ttl_content):
                work_label_map[wm.group(1)] = wm.group(2)
            works_with_names = []
            for wid in works_matches:
                works_with_names.append({'id': wid, 'title': work_label_map.get(wid, wid)})
            
            dila_data = {
                'id': lookup_id,
                'name_vi': name_vi,
                'name_zh': next((n['name'] for n in all_names if n['lang'] == 'zh'), ''),
                'all_names': all_names,
                'dharma_names': dharma_names,
                'secular_names': dharma_names[:1] if dharma_names else [],  # First dharma name as fallback secular
                'lineage': lineage,
                'birth_year': birth_year,
                'death_year': death_year,
                'dynasty': dynasty,
                'bio': bio,
                'places': places_with_names,
                'works': works_with_names,
                'ttl_filename': os.path.basename(ttl_file) if ttl_file else ''
            }
    
    if not dila_data:
        return jsonify({'error': 'Person not found: ' + dila_id}), 404
    
    # Use lookup_id for all further operations
    dila_id = lookup_id
    
    # LOOKUP DILA ID from ttl_mapping for Marcus query
    conn = get_db()
    try:
        # Try multiple patterns to find DILA ID
        search_patterns = [
            f"TS-{lookup_id}",
            lookup_id,
            f"{lookup_id}.ttl"
        ]
        marcus_lookup_id = dila_id
        for pattern in search_patterns:
            row = conn.execute(
                "SELECT dila_id FROM ttl_mapping WHERE ttl_filename = ? OR name_vi = ?",
                (pattern, lookup_id)
            ).fetchone()
            if row:
                marcus_lookup_id = row[0]
                break
    except:
        marcus_lookup_id = dila_id
    finally:
        conn.close()
    
    marcus_data = get_marcus_data(marcus_lookup_id)
    is_conflict, dila_lineage, marcus_lineage = check_lineage_conflict(marcus_lookup_id)
    
    # Read TTL content for bio - use lookup_id for file search
    ttl_content = ""
    ttl_file = os.path.join(TTL_OLD_DIR, f"{lookup_id}.ttl")
    if not os.path.exists(ttl_file):
        # Try to find by name pattern
        for f in os.listdir(TTL_OLD_DIR):
            if dila_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                break
    
    if os.path.exists(ttl_file):
        with open(ttl_file, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
    
    # Extract biographical note - single-line format
    bio_match = re.search(r'bkg:biographicalNote\s+"([^"]+)"', ttl_content)
    bio = bio_match.group(1)[:1000] if bio_match else (dila_data.get('bio', '') or '')
    
    # Prepare all TTL-sourced fields
    ttl_data = dila_data if dila_data.get('ttl_filename') else {}
    
    return jsonify({
        'id': dila_id,
        'name_vi': dila_data.get('name_vi', ''),
        'zh': dila_data.get('name_zh', ''),
        'ttl_filename': dila_data.get('ttl_filename', ''),
        'ttl_content_full': ttl_content,  # Raw TTL for VPS Column 2
        'dila_data': {
            'birth': dila_data.get('birth_year'),
            'death': dila_data.get('death_year'),
            'lineage': dila_data.get('lineage', ''),
            'dynasty': dila_data.get('dynasty', ''),
            'bio': bio[:800],
            'all_names': ttl_data.get('all_names', []),
            'dharma_names': ttl_data.get('dharma_names', []),
            'secular_names': ttl_data.get('secular_names', []),
            'places': ttl_data.get('places', []),
            'works': ttl_data.get('works', [])
        },
        'marcus_data': {
            'lineage': marcus_lineage or dila_data.get('lineage', ''),
            'teachers': marcus_data.get('teachers', []) if marcus_data else [],
            'students': marcus_data.get('students', []) if marcus_data else [],
            'edges': marcus_data.get('edge_count', 0) if marcus_data else 0
        },
        'conflict': is_conflict,
        'dila_lineage': dila_lineage or dila_data.get('lineage', ''),
        'marcus_lineage': marcus_lineage,
        'ttl_content': ttl_content[:3000]  # Preview in Col 5
    })

@app.route('/api/resolve', methods=['POST'])
def api_resolve():
    """
    POST /api/resolve
    Save resolved master entity and move TTL to master directory.
    """
    data = request.get_json()
    dila_id = data.get('id')
    name_vi = data.get('name_vi')
    lineage_master = data.get('lineage_master')
    bio = data.get('bio')
    lineage_source = data.get('lineage_source', 'dila')  # 'dila' or 'marcus'
    
    if not dila_id:
        return jsonify({'error': 'Missing id'}), 400
    
    return jsonify({'error': 'Use app.py for resolve'}), 400

@app.route('/api/save-ttl', methods=['POST'])
def api_save_ttl():
    """Save TTL content to master file"""
    data = request.get_json()
    dila_id = data.get('id')
    ttl_content = data.get('ttl_content', '')
    
    if not dila_id:
        return jsonify({'error': 'Missing id'}), 400
    
    # Strip TS- prefix
    if dila_id.startswith('TS-'):
        dila_id = dila_id[3:]
    
    # Save to master directory
    os.makedirs(TTL_MASTER_DIR, exist_ok=True)
    master_ttl_path = os.path.join(TTL_MASTER_DIR, f"TS-{dila_id}.ttl")
    with open(master_ttl_path, 'w', encoding='utf-8') as f:
        f.write(ttl_content)
    
    return jsonify({'success': True, 'dila_id': dila_id, 'file': f"/ontology/ttl/monks/TS-{dila_id}.ttl"})
    
    # Save to master_entities table (create if not exists)
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS master_entities (
                id TEXT PRIMARY KEY,
                name_vi TEXT,
                lineage_master TEXT,
                lineage_source TEXT,
                bio TEXT,
                resolved_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_by TEXT DEFAULT 'admin'
            )
        """)
        
        conn.execute("""
            INSERT OR REPLACE INTO master_entities (id, name_vi, lineage_master, lineage_source, bio)
            VALUES (?, ?, ?, ?, ?)
        """, (dila_id, name_vi, lineage_master, lineage_source, bio))
        conn.commit()
    finally:
        conn.close()
    
    # Generate master TTL file
    ttl_template = f"""@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix da: <http://daoanh.vn/ontology/> .

<ex:monk/{dila_id}> a bkg:Monk ;
    rdfs:label "{name_vi}"@vi ;
    da:dilaId "{dila_id}" ;
    bkg:dharmaLineageName "{lineage_master}"@vi ;
    bkg:biographicalNote """ + bio[:500].replace('"""', '\\"\\"\\"') + """@vi .

# Resolved: {datetime.now().isoformat()}
# Lineage source: {lineage_source}
"""
    
    # Save to master directory
    master_ttl_path = os.path.join(TTL_MASTER_DIR, f"{dila_id}.ttl")
    with open(master_ttl_path, 'w', encoding='utf-8') as f:
        f.write(ttl_template)
    
    # Move old file to archive
    old_file = os.path.join(TTL_OLD_DIR, f"{dila_id}.ttl")
    if not os.path.exists(old_file):
        for f in os.listdir(TTL_OLD_DIR):
            if dila_id.lower() in f.lower():
                old_file = os.path.join(TTL_OLD_DIR, f)
                break
    
    if os.path.exists(old_file):
        archive_path = os.path.join(TTL_ARCHIVE_DIR, f"{dila_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.ttl")
        os.rename(old_file, archive_path)
    
    return jsonify({
        'success': True,
        'dila_id': dila_id,
        'master_file': f"/data/ttl/master/{dila_id}.ttl"
    })

@app.route('/api/harvester/<source>', methods=['POST'])
def api_harvester(source):
    """
    POST /api/harvester/<source>
    Trigger DILA or Marcus harvester script.
    """
    import subprocess
    
    valid_sources = ['DILA', 'Marcus']
    if source not in valid_sources:
        return jsonify({'error': 'Invalid source'}), 400
    
    # Map to script names
    script_map = {
        'DILA': 'dila_harvester.py',
        'Marcus': 'marcus_harvester.py'
    }
    
    script_path = os.path.join(BASE_DIR, 'src_python', 'etl', script_map[source])
    
    if not os.path.exists(script_path):
        # Try alternative paths
        script_path = os.path.join(BASE_DIR, script_map[source])
    
    result = {'source': source, 'script': script_path}
    
    if os.path.exists(script_path):
        try:
            # Run in background
            subprocess.Popen(['python3', script_path], 
                           stdout=open(os.path.join(DATA_DIR, f'{source.lower()}_harvester.log'), 'w'),
                           stderr=subprocess.STDOUT)
            result['status'] = 'started'
            result['message'] = f'{source} harvester started'
        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)
    else:
        result['status'] = 'not_found'
        result['message'] = f'Script not found: {script_path}'
    
    return jsonify(result)

@app.route('/api/stats')
def api_stats():
    """Get overall statistics"""
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        marcus_edges = conn.execute("SELECT COUNT(*) FROM networks WHERE source_origin = 'Marcus'").fetchone()[0]
        
        queue_count = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')])
        master_count = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')])
        
        return jsonify({
            'total_people': total_people,
            'total_places': total_places,
            'marcus_edges': marcus_edges,
            'queue_pending': queue_count,
            'master_resolved': master_count
        })
    finally:
        conn.close()

@app.route('/api/health')
def api_health():
    """Health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/conflicts')
def api_conflicts():
    """Get unresolved conflicts for Admin Dashboard"""
    conn = get_db()
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        conflict_type = request.args.get('type', None)
        
        query = "SELECT * FROM lineage_conflicts_v2 WHERE resolved = 0"
        params = []
        
        if conflict_type:
            query += " AND conflict_type = ?"
            params.append(conflict_type)
        
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        
        return jsonify({
            'conflicts': [dict(row) for row in rows],
            'count': len(rows)
        })
    finally:
        conn.close()

@app.route('/api/marcus_network/<person_id>')
def api_marcus_network(person_id):
    """Get Marcus network data for person"""
    conn = get_db()
    try:
        # Teachers (people who taught this person)
        teachers = conn.execute("""
            SELECT teacher_id, teacher_label, ref
            FROM marcus_networks
            WHERE student_id = ?
        """, (person_id,)).fetchall()
        
        # Students (people this person taught)
        students = conn.execute("""
            SELECT student_id, student_label, ref
            FROM marcus_networks
            WHERE teacher_id = ?
        """, (person_id,)).fetchall()
        
        return jsonify({
            'person_id': person_id,
            'teachers': [dict(t) for t in teachers],
            'students': [dict(s) for s in students],
            'teacher_count': len(teachers),
            'student_count': len(students)
        })
    finally:
        conn.close()

@app.route('/api/resolve_conflict', methods=['POST'])
def api_resolve_conflict():
    """Resolve a conflict - mark as resolved"""
    data = request.get_json()
    conflict_id = data.get('conflict_id')
    notes = data.get('notes', '')
    resolution = data.get('resolution', 'use_dila')  # 'use_dila' or 'use_marcus'
    
    conn = get_db()
    try:
        conn.execute("""
            UPDATE lineage_conflicts_v2
            SET resolved = 1, notes = ?
            WHERE id = ?
        """, (f"{notes} | Resolution: {resolution}", conflict_id))
        
        conn.commit()
        
        return jsonify({
            'status': 'ok',
            'conflict_id': conflict_id,
            'resolution': resolution
        })
    finally:
        conn.close()

# ── T109: Admin Conflict Workflow (Zero-ALTER · additive, không đụng route cũ) ──
def _safe_audit_id(conn, claim_id):
    """Đọc audit_id từ bảng dẫn xuất T109; None nếu chưa có ETL (route bền với rollback)."""
    try:
        r = conn.execute("SELECT audit_id FROM entity_claims_audit WHERE claim_id=?", (claim_id,)).fetchone()
        return r['audit_id'] if r else None
    except sqlite3.OperationalError:
        return None

@app.route('/daoanh/api/admin/lineage-conflicts')
def admin_lineage_conflicts():
    """GET — danh sách conflict CHƯA xử lý (lineage_conflicts_v2) kèm dấu vết review (en_audit_log).
    Read-only; doc mới, không sửa /api/conflicts hiện có."""
    conn = get_db()
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        ctype = request.args.get('type', None)

        where = "WHERE c.resolved = 0"
        params = []
        if ctype:
            where += " AND c.conflict_type = ?"
            params.append(ctype)

        rows = conn.execute(f"""
            SELECT c.id, c.person_id, c.label, c.name_vi, c.conflict_type,
                   c.dila_count, c.marcus_count, c.notes, c.created_at,
                   a.verification_status AS last_verdict, a.editor AS last_editor,
                   a.created_at AS last_reviewed_at
            FROM lineage_conflicts_v2 c
            LEFT JOIN (
                SELECT entity_ref, MAX(log_id) AS m
                FROM en_audit_log WHERE action = 'resolve_lineage_conflict' GROUP BY entity_ref
            ) lastlog ON lastlog.entity_ref = c.person_id
            LEFT JOIN en_audit_log a ON a.log_id = lastlog.m
            {where}
            ORDER BY c.id LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()

        total_open = conn.execute(
            f"SELECT COUNT(*) AS n FROM lineage_conflicts_v2 c {where}", params).fetchone()[0]

        return jsonify({
            'conflicts': [dict(r) for r in rows],
            'count': len(rows),
            'total_open': total_open,
            'status': 'ok'
        })
    finally:
        conn.close()

@app.route('/daoanh/api/admin/lineage-conflicts/<int:conflict_id>/resolve', methods=['POST'])
def admin_lineage_conflict_resolve(conflict_id):
    """POST — ghi verdict conflict: UPDATE resolved=1 + INSERT en_audit_log (Lean, Zero-ALTER).
    dila_data/marcus_data bất biến (minh chứng gốc); verdict ghi qua UPDATE + audit sổ.
    T136 (2026-09-14): thêm resolution_type ∈ pick|merge|reject — đóng đặc tả
    'T115/T109 Lineage Consensus' §2 "chọn 1 giá trị, gộp, hoặc bác bỏ cả hai".
    Mặc định 'pick' → tương thích tuyệt đối với caller cũ (conflicts.html không gửi type)."""
    data = request.get_json(force=True, silent=True) or {}
    resolution_type = (data.get('resolution_type') or 'pick').strip()
    winner = data.get('winner_source_id', 'dila')          # 'dila' | 'marcus' (pick) | 'both' (merge) | 'none' (reject)
    editor = (data.get('editor') or '').strip() or 'admin'
    reason = (data.get('reason') or '').strip()

    if resolution_type not in ('pick', 'merge', 'reject'):
        return jsonify({'status': 'error', 'message': 'resolution_type phải ∈ pick|merge|reject'}), 400
    if resolution_type == 'pick' and winner not in ('dila', 'marcus'):
        return jsonify({'status': 'error', 'message': 'pick: winner_source_id phải ∈ dila|marcus'}), 400

    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM lineage_conflicts_v2 WHERE id=?", (conflict_id,)).fetchone()
        if row is None:
            return jsonify({'status': 'error', 'message': f'conflict #{conflict_id} không tồn tại'}), 404
        if row['resolved']:
            return jsonify({'status': 'error', 'message': f'conflict #{conflict_id} đã resolved'}), 409

        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        old_value = f"dila={row['dila_data']} | marcus={row['marcus_data']}"
        if resolution_type == 'pick':
            new_value, rk = winner, ('DILA' if winner == 'dila' else 'MARCUS')
            note_tag = 'T109 winner=' + winner
        elif resolution_type == 'merge':
            new_value, rk = 'both', 'DILA+MARCUS'
            note_tag = 'T136 merge: giu ca hai'
        else:
            new_value, rk = 'rejected', 'NONE'
            note_tag = 'T136 reject: bac bo ca hai'
        conn.execute("""
            UPDATE lineage_conflicts_v2
            SET resolved = 1, notes = COALESCE(?, '') || ' | ' || ?
            WHERE id = ?
        """, (reason, note_tag, conflict_id))
        cur = conn.execute("""
            INSERT INTO en_audit_log
                (entity_ref, action, field_name, old_value, new_value, evidence_sources,
                 authority_rank, editor, verification_status, created_at)
            VALUES (?, 'resolve_lineage_conflict', ?, ?, ?, ?, ?, ?, 'verified', ?)
        """, (row['person_id'], row['conflict_type'], old_value, new_value,
              f"dila_count={row['dila_count']}, marcus_count={row['marcus_count']} | resolution_type={resolution_type}",
              rk, editor, now))
        conn.commit()
        return jsonify({'status': 'ok', 'conflict_id': conflict_id,
                        'resolution_type': resolution_type,
                        'winner_source_id': new_value, 'audit_log_id': cur.lastrowid})
    finally:
        conn.close()

@app.route('/daoanh/api/admin/claims/<int:claim_id>/review', methods=['POST'])
def admin_claim_review(claim_id):
    """POST — thẩm định 1 assertion (entity_claims): verification_status/assertion_level/reviewed_* + en_audit_log."""
    data = request.get_json(force=True, silent=True) or {}
    verdict = data.get('verdict', 'unverified')    # verified | disputed | needs_review | unverified
    level = data.get('assertion_level')            # high | medium | low | None
    editor = (data.get('editor') or '').strip() or 'admin'
    note = (data.get('note') or '').strip()

    allowed = {'verified', 'disputed', 'needs_review', 'unverified'}
    if verdict not in allowed:
        return jsonify({'status': 'error', 'message': f'verdict phải ∈ {sorted(allowed)}'}), 400
    if level not in (None, 'high', 'medium', 'low'):
        return jsonify({'status': 'error', 'message': 'assertion_level phải ∈ high|medium|low'}), 400

    conn = get_db()
    try:
        row = conn.execute("""
            SELECT c.claim_id, c.entity_id, e.canonical_label, c.claim_type, c.predicate,
                   c.source_id, c.verification_status, c.assertion_level
            FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id
            WHERE c.claim_id = ?
        """, (claim_id,)).fetchone()
        if row is None:
            return jsonify({'status': 'error', 'message': f'claim #{claim_id} không tồn tại'}), 404

        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        conn.execute("""
            UPDATE entity_claims
            SET verification_status = ?, assertion_level = ?, reviewed_by = ?, reviewed_at = ?, editor_note = ?
            WHERE claim_id = ?
        """, (verdict, level, editor, now, note, claim_id))
        cur = conn.execute("""
            INSERT INTO en_audit_log
                (entity_ref, action, field_name, old_value, new_value, evidence_sources,
                 authority_rank, editor, verification_status, created_at)
            VALUES (?, 'claim_review', ?, ?, ?, ?, ?, ?, 'verified', ?)
        """, (f"{row['canonical_label'] or row['entity_id']}|{row['claim_type']}",
              row['predicate'], f"{row['verification_status']}/{row['assertion_level']}",
              f"{verdict}/{level}", f"claim_id={claim_id}, source_id={row['source_id']}",
              'CLAIM', editor, now))
        conn.commit()
        return jsonify({'status': 'ok', 'claim_id': claim_id,
                        'verdict': verdict, 'assertion_level': level,
                        'audit_log_id': cur.lastrowid,
                        'audit_id': _safe_audit_id(conn, claim_id)})
    finally:
        conn.close()

@app.route('/api/marcus_stats')
def api_marcus_stats():
    """Get Marcus network statistics"""
    conn = get_db()
    try:
        total_relations = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        unique_teachers = conn.execute("SELECT COUNT(DISTINCT teacher_id) FROM marcus_networks").fetchone()[0]
        unique_students = conn.execute("SELECT COUNT(DISTINCT student_id) FROM marcus_networks").fetchone()[0]
        
        total_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0").fetchone()[0]
        teacher_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='teacher_set' AND resolved = 0").fetchone()[0]
        student_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='student_set' AND resolved = 0").fetchone()[0]
        
        return jsonify({
            'total_relations': total_relations,
            'unique_teachers': unique_teachers,
            'unique_students': unique_students,
            'total_conflicts': total_conflicts,
            'teacher_conflicts': teacher_conflicts,
            'student_conflicts': student_conflicts
        })
    finally:
        conn.close()

@app.route('/api/admin/staging/list')
def admin_staging_list():
    data = load_staging()
    items = data.get('items', [])
    return jsonify({"items": items, "total": len(items), "status": "ready"})

@app.route('/api/admin/verification/list')
def admin_verification_list():
    data = load_verification()
    items = data.get('items', [])
    return jsonify({"items": items, "total": len(items), "status": "pending_global"})

@app.route('/api/admin/sources')
def admin_get_sources():
    json_path = os.path.join(DATA_DIR, 'places.json')
    if not os.path.exists(json_path):
        return jsonify({"sources": []})
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    places = data.get('places', [])
    sources = {}
    for place in places:
        source = place.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    return jsonify({"sources": [{"name": k, "count": v} for k, v in sources.items()]})

@app.route('/daoanh/api/monk-resolve')
def api_monk_resolve():
    """
    GET /daoanh/api/monk-resolve?name=<name>
    (path deliberately avoids /daoanh/api/monk/<monk_id> - that generic
    dynamic route intercepts any single path segment under /monk/, including
    a literal "resolve", before this handler would ever be reached)
    Resolve a monk name (Vietnamese or Chinese) to a DILA person id via the
    bulk `people` table (48k+ rows) - used because monk_dict is still mostly
    unpopulated (see Task 1). Exact match first, then LIKE fallback.
    """
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({"ok": False, "error": "name required"}), 400
    conn = get_db_connection()
    try:
        match_type = None
        row = conn.execute(
            "SELECT id, name_zh, name_vi, dynasty FROM people WHERE name_vi = ? OR name_zh = ? LIMIT 1",
            (name, name)
        ).fetchone()
        if row:
            match_type = 'exact_name_vi' if (row['name_vi'] or '') == name else 'exact_name_zh'
        if not row:
            like = f'%{name}%'
            row = conn.execute(
                "SELECT id, name_zh, name_vi, dynasty FROM people WHERE name_vi LIKE ? OR name_zh LIKE ? ORDER BY LENGTH(name_vi) ASC LIMIT 1",
                (like, like)
            ).fetchone()
            if row:
                match_type = 'fuzzy_name_vi' if name in (row['name_vi'] or '') else 'fuzzy_name_zh'
        # Fallback: tìm trong vn_person_authority (tên 4 chữ TTL như Đơn Hà Thiên Nhiên,
        # Thúy Vi Vô Học) — people.name_vi chỉ lưu 2 chữ nên không match được.
        if not row:
            like = f'%{name}%'
            vpa = conn.execute(
                "SELECT dila_id FROM vn_person_authority WHERE name_vi LIKE ? AND dila_id IS NOT NULL AND dila_id != '' ORDER BY LENGTH(name_vi) ASC LIMIT 1",
                (like,)
            ).fetchone()
            if vpa and vpa['dila_id']:
                row = conn.execute(
                    "SELECT id, name_zh, name_vi, dynasty FROM people WHERE id=?",
                    (vpa['dila_id'],)
                ).fetchone()
                if row:
                    vpa_full = conn.execute(
                        "SELECT name_vi, name_zh FROM vn_person_authority WHERE dila_id=? LIMIT 1",
                        (vpa['dila_id'],)
                    ).fetchone()
                    row = dict(row)
                    if vpa_full:
                        if vpa_full['name_vi']:
                            row['name_vi'] = vpa_full['name_vi']
                        if vpa_full['name_zh']:
                            row['name_zh'] = vpa_full['name_zh']
                    match_type = 'authority_vi'
        if not row:
            # BUG-015: "not found" is an expected outcome for a name-resolver
            # endpoint (e.g. a place name typed into the combined place/monk
            # search box), not a server error — return 200 so callers can
            # safely call r.json() without special-casing non-2xx status.
            return jsonify({"ok": False, "error": "not found", "results": []}), 200
        return jsonify({"ok": True, "person": dict(row), "match_type": match_type, "matched_query": name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/daoanh/api/monk/<dila_id>/marcus-network')
def api_monk_marcus_network(dila_id):
    """
    GET /daoanh/api/monk/<dila_id>/marcus-network
    Task 4 (Marcus term glossaries -> people/works integration).
    Returns teacher/student lineage relations for a DILA person from the real
    Marcus (Bingenheimer ChineseBuddhism_SNA) dataset — marcus_reference /
    marcus_networks tables, joined via marcus_people_link (id-match, additive,
    read-only; does not touch people/marcus_reference/marcus_networks).
    Distinct from the pre-existing /api/monk/<id>/marcus route, which reads
    TTL files and is unrelated to this dataset.
    """
    conn = get_db_connection()
    try:
        person = conn.execute(
            "SELECT id, name_zh, name_vi, dynasty FROM people WHERE id = ?", (dila_id,)
        ).fetchone()
        if not person:
            return jsonify({"ok": False, "error": "person not found"}), 404

        link = conn.execute(
            "SELECT marcus_node_id, match_confidence FROM marcus_people_link WHERE person_id = ?",
            (dila_id,)
        ).fetchone()
        if not link:
            return jsonify({
                "ok": True,
                "person": dict(person),
                "linked": False,
                "teachers": [],
                "students": []
            })

        node_id = link['marcus_node_id']
        teachers = conn.execute("""
            SELECT teacher_id AS id, teacher_label AS label, relation_type, ref
            FROM marcus_networks WHERE student_id = ?
        """, (node_id,)).fetchall()
        students = conn.execute("""
            SELECT student_id AS id, student_label AS label, relation_type, ref
            FROM marcus_networks WHERE teacher_id = ?
        """, (node_id,)).fetchall()

        return jsonify({
            "ok": True,
            "person": dict(person),
            "linked": True,
            "match_confidence": link['match_confidence'],
            "source": "Marcus Bingenheimer ChineseBuddhism_SNA",
            "teachers": [dict(r) for r in teachers],
            "students": [dict(r) for r in students]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/dila-stats')
def admin_dila_stats():
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        dynasty_counts = conn.execute("""
            SELECT dynasty, COUNT(*) as cnt FROM people 
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty ORDER BY cnt DESC LIMIT 10
        """).fetchall()
        return jsonify({
            "total_people": total_people,
            "total_places": total_places,
            "dynasties": [{"name": r[0], "count": r[1]} for r in dynasty_counts]
        })
    finally:
        conn.close()

@app.route('/api/admin/places')
def admin_places():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    conn = get_db()
    try:
        offset = (page - 1) * per_page
        if search:
            # Search in all name fields and location
            search_pattern = f'%{search}%'
            rows = conn.execute("""
                SELECT * FROM places 
                WHERE name_zh LIKE ? OR name_vi LIKE ? OR name_en LIKE ? OR location LIKE ?
                LIMIT ? OFFSET ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern, per_page, offset)).fetchall()
            
            total = conn.execute("""
                SELECT COUNT(*) FROM places 
                WHERE name_zh LIKE ? OR name_vi LIKE ? OR name_en LIKE ? OR location LIKE ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern)).fetchone()[0]
        else:
            rows = conn.execute("SELECT * FROM places LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        
        return jsonify({"places": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})
    finally:
        conn.close()

@app.route('/api/admin/places/<place_id>', methods=['PUT'])
def admin_update_place(place_id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("""
            UPDATE places SET 
                name = COALESCE(?, name),
                name_vi = COALESCE(?, name_vi),
                gps_lat = COALESCE(?, gps_lat),
                gps_lng = COALESCE(?, gps_lng),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data.get('name'), data.get('name_vi'), data.get('gps_lat'), data.get('gps_lng'), place_id))
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    finally:
        conn.close()

@app.route('/api/admin/person-stats')
def admin_person_stats():
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        dynasty_counts = conn.execute("""
            SELECT dynasty, COUNT(*) as cnt FROM people 
            WHERE dynasty IS NOT NULL AND dynasty != ''
            GROUP BY dynasty ORDER BY cnt DESC
        """).fetchall()
        return jsonify({
            "total": total,
            "dynasties": [{"name": r[0], "count": r[1]} for r in dynasty_counts]
        })
    finally:
        conn.close()

@app.route('/api/admin/places_vps', methods=['GET'])
def admin_places_vps():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    conn = get_db()
    try:
        offset = (page - 1) * per_page
        if search:
            query = "SELECT * FROM places_vps WHERE name_vi LIKE ? OR name_zh LIKE ? OR province LIKE ? LIMIT ? OFFSET ?"
            search_term = f"%{search}%"
            rows = conn.execute(query, (search_term, search_term, search_term, per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_vps WHERE name_vi LIKE ? OR name_zh LIKE ? OR province LIKE ?", 
                            (search_term, search_term, search_term)).fetchone()[0]
        else:
            rows = conn.execute("SELECT * FROM places_vps LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_vps").fetchone()[0]
        return jsonify({"places": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})
    finally:
        conn.close()

@app.route('/api/admin/places_vps/add', methods=['POST'])
def admin_add_place_vps():
    data = request.get_json()
    conn = get_db()
    try:
        import uuid
        place_id = data.get('id') or "VPS-" + uuid.uuid4().hex[:8].upper()
        now = datetime.now().isoformat()
        gps_lat = data.get('gps_lat')
        gps_long = data.get('gps_long')
        
        vals = [
            place_id,
            (data.get('name_zh') or '')[:100],
            (data.get('name_vi') or '')[:100],
            (data.get('name_en') or '')[:100],
            (data.get('location') or '')[:200],
            float(gps_lat) if gps_lat else None,
            float(gps_long) if gps_long else None,
            (data.get('address') or '')[:200],
            (data.get('province') or '')[:50],
            (data.get('country') or 'Vietnam')[:50],
            (data.get('place_type') or 'Chùa')[:50],
            'VPS',
            1.0,
            now,
            now
        ]
        
        conn.execute("""
            INSERT INTO places_vps (id, name_zh, name_vi, name_en, location, gps_lat, gps_long, address, province, country, place_type, source_origin, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vals)
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/admin/places_vps/<place_id>', methods=['DELETE'])
def admin_delete_place_vps(place_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM places_vps WHERE id = ?", (place_id,))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route('/api/admin/places_vps/<place_id>', methods=['PUT'])
def admin_update_place_vps(place_id):
    data = request.get_json()
    conn = get_db()
    try:
        now = datetime.now().isoformat()
        conn.execute("""
            UPDATE places_vps SET 
                name_zh = COALESCE(?, name_zh),
                name_vi = COALESCE(?, name_vi),
                name_en = COALESCE(?, name_en),
                location = COALESCE(?, location),
                gps_lat = COALESCE(?, gps_lat),
                gps_long = COALESCE(?, gps_long),
                address = COALESCE(?, address),
                province = COALESCE(?, province),
                country = COALESCE(?, country),
                place_type = COALESCE(?, place_type),
                updated_at = ?
            WHERE id = ?
        """, (
            data.get('name_zh'), data.get('name_vi'), data.get('name_en'), data.get('location'),
            data.get('gps_lat'), data.get('gps_long'), data.get('address'), data.get('province'),
            data.get('country'), data.get('place_type'), now, place_id
        ))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/admin/places_pending', methods=['GET'])
def admin_places_pending():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    no_vi = request.args.get('no_vi', 'false').lower() == 'true'
    conn = get_db_connection()
    try:
        offset = (page - 1) * per_page
        if search:
            query = "SELECT * FROM places_pending WHERE (name_vi LIKE ? OR name_zh LIKE ?) AND (name_vi IS NULL OR name_vi = '') LIMIT ? OFFSET ?"
            search_term = f"%{search}%"
            rows = conn.execute(query, (search_term, search_term, per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi LIKE ? OR name_zh LIKE ?", 
                            (search_term, search_term)).fetchone()[0]
        elif no_vi:
            rows = conn.execute("SELECT * FROM places_pending WHERE name_vi IS NULL OR name_vi = '' LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi IS NULL OR name_vi = ''").fetchone()[0]
        else:
            rows = conn.execute("SELECT * FROM places_pending LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
        return jsonify({"places": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})
    finally:
        conn.close()

@app.route('/api/admin/places_pending/<place_id>', methods=['GET'])
def admin_get_place_pending(place_id):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM places_pending WHERE id = ?", (place_id,)).fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not found"}), 404
    finally:
        conn.close()

@app.route('/api/admin/places_pending/<place_id>/move_to_vps', methods=['POST'])
def admin_move_place_to_vps(place_id):
    data = request.get_json()
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM places_pending WHERE id = ?", (place_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        import uuid
        place_id = data.get('id') or "VPS-" + uuid.uuid4().hex[:8].upper()
        name_vi = data.get('name_vi') or row['name_vi']
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO places_vps (id, name_zh, name_vi, name_en, location, gps_lat, gps_long, address, province, country, place_type, source_origin, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            place_id,
            row['name_zh'],
            name_vi,
            row['name_en'],
            row['location'],
            row['gps_lat'],
            row['gps_long'],
            row['address'],
            row['province'],
            row['country'],
            row['place_type'],
            'VPS',
            1.0,
            now,
            now
        ))
        conn.commit()
        return jsonify({"success": True, "place_id": place_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Queue endpoint - list TTL files
@ app.route('/api/admin/queue/list')
def admin_queue_list():
    try:
        files = []
        if os.path.exists(TTL_OLD_DIR):
            for f in os.listdir(TTL_OLD_DIR):
                if f.endswith('.ttl'):
                    fpath = os.path.join(TTL_OLD_DIR, f)
                    files.append({
                        "filename": f,
                        "size": os.path.getsize(fpath),
                        "modified": os.path.getmtime(fpath)
                    })
        return jsonify({"queue": files, "total": len(files)})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/dict/<dila_id>')
def api_dict(dila_id):
    """
    GET /api/dict/<dila_id>
    Get Startdict biography for a monk.
    Returns placeholder data if not found.
    """
    # Try to find in startdict database
    # For now, return placeholder - integrate with startdict data later
    return jsonify({
        'id': dila_id,
        'bio': 'Chưa có dữ liệu từ điển cho ' + dila_id
    })

@app.route('/api/update_file', methods=['POST'])
def api_update_file():
    """
    POST /api/update_file
    Save TTL content to master archive.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    file_id = data.get('id', '')
    content = data.get('content', '')
    
    if not file_id:
        return jsonify({'error': 'No ID provided'}), 400
    
    # Save to master directory
    filepath = os.path.join(TTL_MASTER_DIR, f"{file_id}.ttl")
    archive_path = os.path.join(TTL_ARCHIVE_DIR, f"{file_id}.ttl")
    
    try:
        # Create backup in archive
        if os.path.exists(filepath):
            import shutil
            shutil.copy(filepath, archive_path)
        
        # Write new content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True, 'file': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/master-stats')
def admin_master_stats():
    conn = get_db()
    try:
        total_people = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        total_places = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
        marcus_relations = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        unresolved_conflicts = conn.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0").fetchone()[0]
        queue_count = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')])
        master_count = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')])
        return jsonify({
            "people": total_people,
            "places": total_places,
            "marcus_relations": marcus_relations,
            "conflicts": unresolved_conflicts,
            "queue": queue_count,
            "resolved": master_count
        })
    finally:
        conn.close()

# =============================================================================
# TTL REBUILD v4.0 - API ENDPOINTS
# =============================================================================

@app.route('/api/monk/<dila_id>/marcus', methods=['GET'])
def api_monk_marcus(dila_id):
    """GET /api/monk/{id}/marcus - Get Marcus network data (teachers/students)
    Searches by name_vi, name_zh, hasTeacher/hasStudent from TTL.
    """
    lookup_id = dila_id.replace('TS-', '')
    conn = get_db()
    try:
        teachers = set()
        students = set()
        lineage = ''
        search_keys = []
        
        # Get name and relationships from TTL
        import re
        ttl_file = os.path.join(TTL_OLD_DIR, f"TS-{lookup_id}.ttl")
        if not os.path.exists(ttl_file):
            for f in os.listdir(TTL_OLD_DIR):
                if lookup_id.lower() in f.lower():
                    ttl_file = os.path.join(TTL_OLD_DIR, f)
                    break
        
        ttl_teachers = []  # From hasTeacher in TTL
        ttl_students = []  # From hasStudent in TTL
        
        if os.path.exists(ttl_file):
            with open(ttl_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Get name_vi
                label_match = re.search(r'rdfs:label\s+"([^"]+)"@vi', content)
                if label_match:
                    search_keys.append(label_match.group(1))
                # Get name_zh
                zh_match = re.search(r'rdfs:label\s+"([^\n]+)"@zh', content)
                if zh_match:
                    search_keys.append(zh_match.group(1))
                # Get hasTeacher IDs
                ttl_teachers = re.findall(r'bkg:hasTeacher\s+<ex:monk/([^>]+)>', content)
                # Get hasStudent IDs
                ttl_students = re.findall(r'bkg:hasStudent\s+<ex:monk/([^>]+)>', content)
        
        # Convert TTL monk IDs to names
        def get_monks_name(monk_ids, current_ttl_content=''):
            names = []
            for mid in monk_ids:
                found = False
                # Convert underscore to hyphen, title case
                parts = mid.split('_')
                mid_title = '-'.join(p.capitalize() for p in parts)
                mfile = os.path.join(TTL_OLD_DIR, f"TS-{mid_title}.ttl")
                
                if os.path.exists(mfile):
                    with open(mfile, 'r', encoding='utf-8') as f:
                        c = f.read()
                        m = re.search(r'rdfs:label\s+"([^"]+)"@vi', c)
                        if m:
                            names.append(m.group(1))
                            found = True
                
                # Try fuzzy match (case-insensitive, ignore hyphens)
                if not found:
                    for f in os.listdir(TTL_OLD_DIR):
                        fname = f.lower().replace('.ttl','').replace('ts-','').replace('-','_')
                        if mid.lower() in fname:
                            mfile = os.path.join(TTL_OLD_DIR, f)
                            with open(mfile, 'r', encoding='utf-8') as fp:
                                c = fp.read()
                                m = re.search(r'rdfs:label\s+"([^"]+)"@vi', c)
                                if m:
                                    names.append(m.group(1))
                            break
                
                # Try to find in current TTL content (if defined in same file)
                if not found and current_ttl_content:
                    # Look for <ex:monk/nguyen_thieu_tho_tong> rdfs:label "Nguyên Thiều Thọ Tông"@vi
                    pattern = r'<ex:monk/' + re.escape(mid) + r'>\s+rdfs:label\s+"([^"]+)"'
                    m = re.search(pattern, current_ttl_content)
                    if m:
                        names.append(m.group(1))
                        found = True
            return names
        
        # Add teachers from TTL
        if ttl_teachers:
            teachers.update(get_monks_name(ttl_teachers, content if os.path.exists(ttl_file) else ''))
        # Add students from TTL  
        if ttl_students:
            students.update(get_monks_name(ttl_students, content if os.path.exists(ttl_file) else ''))
        
        # Also search in marcus_networks by name_vi / name_zh
        for key in search_keys:
            if key:
                if not teachers:
                    rows = conn.execute(
                        "SELECT teacher_id, teacher_label FROM marcus_networks WHERE student_label LIKE ?",
                        (f'%{key}%',)
                    ).fetchall()
                    for r in rows:
                        teachers.add(r['teacher_label'] or r['teacher_id'])
                
                if not students:
                    rows = conn.execute(
                        "SELECT student_id, student_label FROM marcus_networks WHERE teacher_label LIKE ?",
                        (f'%{key}%',)
                    ).fetchall()
                    for r in rows:
                        students.add(r['student_label'] or r['student_id'])
        
        return jsonify({
            'teachers': list(teachers)[:10],
            'students': list(students)[:15],
            'edges': len(teachers) + len(students),
            'lineage': lineage,
            'ttl_teachers': ttl_teachers,
            'ttl_students': ttl_students,
            'search_keys': search_keys
        })
    finally:
        conn.close()

@app.route('/api/monk/<dila_id>/vps_ttl', methods=['GET'])
def api_monk_vps_ttl(dila_id):
    """GET /api/monk/{id}/vps_ttl - Get VPS TTL file content"""
    lookup_id = dila_id.replace('TS-', '')
    ttl_file = os.path.join(TTL_OLD_DIR, f"{lookup_id}.ttl")
    if not os.path.exists(ttl_file):
        for f in os.listdir(TTL_OLD_DIR):
            if lookup_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                break
    if os.path.exists(ttl_file):
        with open(ttl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'ttl_file': os.path.basename(ttl_file),
            'ttl_content': content[:5000],
            'ttl_content_full': content
        })
    return jsonify({'error': 'TTL not found'}), 404

@app.route('/api/monk/<dila_id>/lexicon', methods=['GET'])
def api_monk_lexicon(dila_id):
    """GET /api/monk/{id}/lexicon - Get lexicon entries for this monk with source priority + aliases for DILA/Marcus mapping"""
    import re
    lookup_id = dila_id.replace('TS-', '')
    
    # Try to get Unicode name from TTL file
    full_name = lookup_id
    ttl_file = os.path.join(TTL_OLD_DIR, f"TS-{lookup_id}.ttl")
    if not os.path.exists(ttl_file):
        for f in os.listdir(TTL_OLD_DIR):
            if lookup_id.lower() in f.lower():
                ttl_file = os.path.join(TTL_OLD_DIR, f)
                break
    
    if os.path.exists(ttl_file):
        with open(ttl_file, 'r', encoding='utf-8') as f:
            content = f.read()
            match = content.find('"@vi')
            if match:
                start = content.rfind('rdfs:label "', 0, match)
                if start >= 0:
                    name_start = start + 12
                    name_end = content.find('"', name_start)
                    if name_end > name_start:
                        full_name = content[name_start:name_end]
    
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT term, definition, source FROM lexicon WHERE definition LIKE ? OR definition LIKE ? LIMIT 50",
            (f'%{full_name}%', f'%{lookup_id}%')
        ).fetchall()
        
        # Add priority weight: Han Lam > Pho Thong > Tham Khhao
        def get_priority(src):
            src_lower = (src or '').lower()
            if any(s in src_lower for s in ['tu dien han viet', 'tu-dien-danh-tu', 'phat quang tu dien', 'tu dien thien tong han viet', 'tu dien da ngon ngu', 'tam tang phap so', 'phat hoc tinh tuyen', 'trich luc tu ngu', 'tu dien anh viet']):
                return 1
            elif any(s in src_lower for s in ['tu dien phat hoc tong hop', 'tu dien phat hoc', 'kho tang phap hoc', 'tu dien viet - pali', 'tu dien pali', 'phap so can ban']):
                return 2
            elif any(s in src_lower for s in ['chua van hanh', 'tham khao', 'duy luc']):
                return 3
            return 4
        
        entries = [
            {'term': r['term'], 'definition': r['definition'], 'source': r['source'], 'priority': get_priority(r['source'])} 
            for r in rows
        ]
        entries.sort(key=lambda x: x['priority'])
        
        # Extract aliases from highest priority entry (for DILA/Marcus mapping)
        # Format: (白雲守端, Hakuun Shutan, 1025-1072) or (Bai Yun Shou Tuan, Hakuun Shutan, J)
        aliases = {}
        if entries and entries[0].get('definition'):
            def_text = entries[0]['definition']
            # Match (Chinese, Japanese, years) or (Chinese, Japanese, English)
            alias_match = re.search(r'\(([^,]+),\s*([^,]+),\s*([0-9\-]+|[A-Za-z]+)\)', def_text)
            if alias_match:
                aliases = {
                    'name_zh': alias_match.group(1).strip(),      # 白雲守端
                    'name_jp': alias_match.group(2).strip(),     # Hakuun Shutan
                    'alt_name': alias_match.group(3).strip()  # 1025-1072 or Hakuun
                }
            else:
                # Try simpler pattern: just Chinese chars at start
                zh_match = re.search(r'([\u4e00-\u9fff]+)', def_text)
                if zh_match:
                    aliases = {'name_zh': zh_match.group(1)}
        
        return jsonify({
            'entries': entries, 
            'count': len(entries),
            'search_term': full_name,
            'aliases': aliases
        })
    finally:
        conn.close()

@app.route('/api/monk/<dila_id>/truoctac', methods=['GET'])
def api_monk_truoctac(dila_id):
    """GET /api/monk/{id}/truoctac - Get Trước Tác works from canon_catalog"""
    lookup_id = dila_id.replace('TS-', '')
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT title_vi, title_zh, volume, cb_page FROM canon_catalog WHERE author_dila_id = ? OR author_vi LIKE ? LIMIT 50",
            (lookup_id, f'%{lookup_id}%')
        ).fetchall()
        works = [{'title_vi': r['title_vi'], 'title_zh': r['title_zh'], 'volume': r['volume'], 'cb_page': r['cb_page']} for r in rows]
        return jsonify({'works': works, 'count': len(works)})
    finally:
        conn.close()

@app.route('/api/save_ttl_v2', methods=['POST'])
def api_save_ttl_v2():
    """POST /api/save_ttl_v2 - Save rebuilt TTL to /ontology/monks/TTL/"""
    data = request.get_json()
    monk_id = (data.get('id') or '').replace('TS-', '')
    ttl_content = data.get('ttl_content', '')
    filename = data.get('filename', f"{monk_id}.ttl")
    
    if not ttl_content:
        return jsonify({'success': False, 'error': 'No content'}), 400
    
    save_dir = os.path.join(BASE_DIR, 'ontology', 'monks', 'TTL')
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ttl_content)
        return jsonify({'success': True, 'saved_to': filepath})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rebuild/save_master', methods=['POST'])
def api_save_master():
    """POST /api/rebuild/save_master - Save TTL to SQL master table"""
    data = request.get_json()
    monk_id = (data.get('id') or '').replace('TS-', '')
    ttl_content = data.get('ttl_content', '')
    filename = data.get('filename', f"{monk_id}.ttl")
    
    if not ttl_content:
        return jsonify({'success': False, 'error': 'No content'}), 400
    
    # Extract key fields for indexing
    name_vi_match = re.search(r'skos:prefLabel\s+"([^"]+)"@vi', ttl_content)
    name_vi = name_vi_match.group(1) if name_vi_match else ''
    
    dila_id_match = re.search(r'da:dilaId\s+"([^"]+)"', ttl_content)
    dila_id = dila_id_match.group(1) if dila_id_match else ''
    
    lineage_match = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"@vi', ttl_content)
    lineage = lineage_match.group(1) if lineage_match else ''
    
    try:
        conn = get_db()
        
        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ttl_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monk_id TEXT UNIQUE,
                name_vi TEXT,
                dila_id TEXT,
                lineage TEXT,
                ttl_content TEXT,
                filename TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Upsert
        conn.execute("""
            INSERT INTO ttl_master (monk_id, name_vi, dila_id, lineage, ttl_content, filename)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(monk_id) DO UPDATE SET
                name_vi = excluded.name_vi,
                dila_id = excluded.dila_id,
                lineage = excluded.lineage,
                ttl_content = excluded.ttl_content,
                filename = excluded.filename
        """, (monk_id, name_vi, dila_id, lineage, ttl_content, filename))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'saved_to': 'ttl_master table',
            'monk_id': monk_id,
            'name_vi': name_vi
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
@app.route('/daoanh/api/dashboard/stats', methods=['GET'])
@app.route('/api/admin/dashboard/stats', methods=['GET'])
@app.route('/daoanh/api/admin/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    """GET /api/dashboard/stats (và alias /api/admin/dashboard/stats) - Get all stats for dashboard"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        
        # DILA total
        dila_total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        
        # Marcus stats
        marcus_edges = conn.execute("SELECT COUNT(*) FROM marcus_networks").fetchone()[0]
        marcus_monks = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT teacher_id as monk_id FROM marcus_networks
                UNION
                SELECT student_id as monk_id FROM marcus_networks
            )
        """).fetchone()[0]
        marcus_in_dila = conn.execute("""
            SELECT COUNT(DISTINCT m.monk_id) FROM (
                SELECT teacher_id as monk_id FROM marcus_networks
                UNION
                SELECT student_id as monk_id FROM marcus_networks
            ) m
            JOIN people p ON m.monk_id = p.id
        """).fetchone()[0]
        
        # Name Vi Map stats
        namevi_total = conn.execute("SELECT COUNT(*) FROM name_vi_map").fetchone()[0]
        namevi_with_dila = conn.execute("SELECT COUNT(*) FROM name_vi_map WHERE dila_id IS NOT NULL").fetchone()[0]
        namevi_with_marcus = conn.execute("SELECT COUNT(*) FROM name_vi_map WHERE marcus_ids IS NOT NULL").fetchone()[0]
        
        # TTL stats
        ttl_queue = len([f for f in os.listdir(TTL_OLD_DIR) if f.endswith('.ttl')]) if os.path.exists(TTL_OLD_DIR) else 0
        ttl_master = len([f for f in os.listdir(TTL_MASTER_DIR) if f.endswith('.ttl')]) if os.path.exists(TTL_MASTER_DIR) else 0
        
        # Place VN review stats (vn_name_status from namevi_map_places)
        namevi_places_reviewed = conn.execute("SELECT COUNT(*) FROM namevi_map_places WHERE vn_name_status='reviewed'").fetchone()[0]
        namevi_places_auto = conn.execute("SELECT COUNT(*) FROM namevi_map_places WHERE vn_name_status='auto'").fetchone()[0]
        namevi_places_total = conn.execute("SELECT COUNT(*) FROM places_pending").fetchone()[0]
        
        conn.close()
        
        coverage_marcus = round(marcus_in_dila / dila_total * 100, 1) if dila_total > 0 else 0
        coverage_namevi = round(namevi_total / dila_total * 100, 1) if dila_total > 0 else 0
        
        return jsonify({
            'dila_total': dila_total,
            'marcus_edges': marcus_edges,
            'marcus_monks': marcus_monks,
            'marcus_in_dila': marcus_in_dila,
            'marcus_coverage': coverage_marcus,
            'namevi_total': namevi_total,
            'namevi_with_dila': namevi_with_dila,
            'namevi_with_marcus': namevi_with_marcus,
            'namevi_coverage': coverage_namevi,
            'ttl_queue': ttl_queue,
            'ttl_master': ttl_master,
            'namevi_reviewed': namevi_places_reviewed,
            'namevi_auto': namevi_places_auto,
            'namevi_places_total': namevi_places_total
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daoanh/api/progress/dashboard', methods=['GET'])
def api_progress_dashboard():
    """GET /daoanh/api/progress/dashboard - Dashboard Process Tracker (docs ↔ code).
    Đọc data/progress_data.json (sinh bởi scripts/build_progress_data.py).
    Truyền ?regenerate=1 để chạy lại script sinh dữ liệu mới."""
    progress_json = os.path.join(DATA_DIR, 'progress_data.json')
    regenerate = request.args.get('regenerate') in ('1', 'true', 'yes')

    if regenerate or not os.path.isfile(progress_json):
        script_path = os.path.join(BASE_DIR, 'scripts', 'build_progress_data.py')
        try:
            import subprocess
            run = subprocess.run([_sys.executable, script_path], cwd=BASE_DIR,
                                 capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=60)
            if run.returncode != 0:
                return jsonify({'success': False, 'error': run.stderr[-500:] or 'Script lỗi'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'Không chạy được script: {e}'}), 500

    if not os.path.isfile(progress_json):
        return jsonify({'success': False, 'error': 'progress_data.json chưa được tạo'}), 500

    try:
        with open(progress_json, encoding='utf-8') as f:
            data = json.load(f)
        data['regenerated'] = regenerate
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/daoanh/api/compliance/dashboard', methods=['GET'])
def api_compliance_dashboard():
    """GET /daoanh/api/compliance/dashboard - Compliance Meter (SCHEMA_DESIGN M7.2).
    Đọc data/design_compliance.json (sinh bởi scripts/verify_design_compliance.py, read-only).
    Truyền ?regenerate=1 để chạy lại script sinh dữ liệu mới."""
    compliance_json = os.path.join(DATA_DIR, 'design_compliance.json')
    regenerate = request.args.get('regenerate') in ('1', 'true', 'yes')

    if regenerate or not os.path.isfile(compliance_json):
        script_path = os.path.join(BASE_DIR, 'scripts', 'verify_design_compliance.py')
        try:
            import subprocess
            run = subprocess.run([_sys.executable, script_path], cwd=BASE_DIR,
                                 capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=60)
            if run.returncode != 0:
                return jsonify({'success': False, 'error': run.stderr[-500:] or 'Script lỗi'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'Không chạy được script: {e}'}), 500

    if not os.path.isfile(compliance_json):
        return jsonify({'success': False, 'error': 'design_compliance.json chưa được tạo'}), 500

    try:
        with open(compliance_json, encoding='utf-8') as f:
            data = json.load(f)
        data['regenerated'] = regenerate
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/name_vi/<path:dila_id>', methods=['GET'])
def api_name_vi_lookup(dila_id):
    """GET /api/name_vi/<dila_id> - Lookup Vietnamese name from name_vi_map"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        
        # Try to find by dila_id first
        row = conn.execute("""
            SELECT name_vi, name_vi_auto, name_vi_final, name_zh, birth_year, death_year, bio_snippet, marcus_ids
            FROM name_vi_map 
            WHERE dila_id = ? OR name_zh IN (
                SELECT name_zh FROM people WHERE id = ?
            )
            LIMIT 1
        """, (dila_id, dila_id)).fetchone()
        
        if row:
            result = dict(row)
            result['name_vi'] = row['name_vi_final'] or row['name_vi_auto'] or row['name_vi'] or ''
            result['found'] = 'dila'
        else:
            # Try by marcus_id
            row = conn.execute("""
                SELECT name_vi, name_vi_auto, name_vi_final, name_zh, birth_year, death_year, bio_snippet, dila_id
                FROM name_vi_map 
                WHERE marcus_ids LIKE ?
                LIMIT 1
            """, (f'%{dila_id}%',)).fetchone()
            
            if row:
                result = dict(row)
                result['name_vi'] = row['name_vi_final'] or row['name_vi_auto'] or row['name_vi'] or ''
                result['found'] = 'marcus'
            else:
                result = {'found': None}
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daoanh/api/name_vi/search', methods=['GET'])
@app.route('/api/name_vi/search', methods=['GET'])
def api_name_vi_search():
    """GET /api/name_vi/search?q=<query> - Search Vietnamese names"""
    try:
        query = request.args.get('q', '')
        if len(query) < 2:
            return jsonify({'results': [], 'error': 'Query too short'})
        
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("""
            SELECT name_vi, name_vi_auto, name_vi_final, name_zh, birth_year, death_year, dila_id, marcus_ids
            FROM name_vi_map 
            WHERE name_vi LIKE ? OR name_vi_auto LIKE ? OR name_vi_final LIKE ? OR name_zh LIKE ?
            LIMIT 20
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        
        results = [dict(row) for row in rows]
        conn.close()
        
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rebuild/queue', methods=['GET'])
def api_rebuild_queue():
    """GET /api/rebuild/queue - Get TTL rebuild queue from old/*.ttl files"""
    queue = []
    import re
    for f in sorted(os.listdir(TTL_OLD_DIR)):
        if f.endswith('.ttl'):
            monk_id = f.replace('.ttl', '').replace('TS-', '')
            
            # Extract name_vi from TTL content
            name_vi = monk_id
            ttl_path = os.path.join(TTL_OLD_DIR, f)
            if os.path.exists(ttl_path):
                with open(ttl_path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    # Extract rdfs:label "..."@vi
                    match = re.search(r'rdfs:label\s+"([^"]+)"@vi', content)
                    if match:
                        name_vi = match.group(1)
            
            queue.append({'id': monk_id, 'filename': f, 'name_vi': name_vi, 'conflict': False})
    return jsonify({'queue': queue, 'count': len(queue)})

@app.route('/daoanh/api/admin/namevi-queue', methods=['GET'])
@app.route('/api/admin/namevi-queue', methods=['GET'])
def admin_namevi_queue():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    filter_status = request.args.get('filter', 'all')
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    try:
        where_clause = "p.name_zh IS NOT NULL AND p.name_zh != ''"
        if filter_status == 'no_auto':
            where_clause += " AND (n.name_vi_auto IS NULL OR n.name_vi_auto = '')"
        elif filter_status == 'auto_pending':
            where_clause += " AND n.name_vi_auto IS NOT NULL AND n.name_vi_auto != '' AND (n.name_vi_final IS NULL OR n.name_vi_final = '')"
        elif filter_status == 'approved':
            where_clause += " AND n.name_vi_final IS NOT NULL AND n.name_vi_final != ''"
        else:
            where_clause += " AND (n.name_vi_final IS NULL OR n.name_vi_final = '')"

        rows = conn.execute(f"""
            SELECT p.id as dila_id, p.name_zh, p.birth_year, p.death_year,
                   n.name_vi, n.name_vi_auto, n.name_vi_final, n.bio_snippet,
                   n.approved_at
            FROM people p
            LEFT JOIN name_vi_map n ON p.id = n.dila_id
            WHERE {where_clause}
            ORDER BY p.id
            LIMIT ? OFFSET ?
        """, (per_page, offset)).fetchall()
        
        names = []
        for r in rows:
            display = r['name_vi_final'] or r['name_vi_auto'] or None
            names.append({
                'dila_id': r['dila_id'],
                'name_zh': r['name_zh'],
                'name_vi': display,
                'name_vi_auto': r['name_vi_auto'],
                'name_vi_final': r['name_vi_final'],
                'approved_at': r['approved_at'],
                'birth_year': r['birth_year'],
                'death_year': r['death_year'],
                'bio_snippet': r['bio_snippet']
            })
        
        # Get counts for each filter
        stats = {}
        for f in ['no_auto', 'auto_pending', 'approved', 'all']:
            w = "p.name_zh IS NOT NULL AND p.name_zh != ''"
            if f == 'no_auto':
                w += " AND (n.name_vi_auto IS NULL OR n.name_vi_auto = '')"
            elif f == 'auto_pending':
                w += " AND n.name_vi_auto IS NOT NULL AND n.name_vi_auto != '' AND (n.name_vi_final IS NULL OR n.name_vi_final = '')"
            elif f == 'approved':
                w += " AND n.name_vi_final IS NOT NULL AND n.name_vi_final != ''"
            else:
                w += " AND (n.name_vi_final IS NULL OR n.name_vi_final = '')"
            c = conn.execute(f"SELECT COUNT(*) as c FROM people p LEFT JOIN name_vi_map n ON p.id = n.dila_id WHERE {w}").fetchone()
            stats[f] = c['c']
        
        return jsonify({
            'names': names, 'page': page, 'per_page': per_page,
            'stats': stats, 'filter': filter_status
        })
    finally:
        conn.close()

@app.route('/daoanh/api/admin/namevi-queue/<dila_id>', methods=['GET'])
@app.route('/api/admin/namevi-queue/<dila_id>', methods=['GET'])
def admin_namevi_queue_get(dila_id):
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("""
            SELECT p.id as dila_id, p.name_zh, p.birth_year, p.death_year,
                   n.name_vi, n.name_vi_auto, n.name_vi_final, n.approved_at, n.bio_snippet
            FROM people p
            LEFT JOIN name_vi_map n ON p.id = n.dila_id
            WHERE p.id = ?
        """, (dila_id,)).fetchone()
        
        if row:
            result = {
                'dila_id': row['dila_id'],
                'name_zh': row['name_zh'],
                'name_vi': row['name_vi_final'] or row['name_vi_auto'] or row['name_vi'],
                'name_vi_auto': row['name_vi_auto'],
                'name_vi_final': row['name_vi_final'],
                'approved_at': row['approved_at'],
                'birth_year': row['birth_year'],
                'death_year': row['death_year'],
                'bio_snippet': row['bio_snippet'],
                'alternative_names': '',
                'dynasty': '',
                'sex': '',
                'is_monk': '',
                'extensive_bio': '',
                'teacher': '',
                'students': '',
                'works': '',
                'bibl': ''
            }
            
            # Parse from XML
            xml_path = os.path.join(BASE_DIR, 'data', 'dila_import', 'Authority-Databases', 'authority_person', 'Buddhist_Studies_Person_Authority.xml')
            if os.path.exists(xml_path):
                try:
                    with open(xml_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    match = re.search(r'<person[^>]*xml:id="' + dila_id + r'"[^>]*>(.*?)</person>', content, re.DOTALL)
                    if match:
                        block = match.group(1)
                        
                        # Get alternative names
                        alt_names = re.findall(r'<persName[^>]*>([^<]+)</persName>', block)
                        if alt_names:
                            result['alternative_names'] = ' | '.join(alt_names)
                        
                        # Get dynasty
                        dynasty = re.search(r'<note type="dynasty">(.*?)</note>', block)
                        if dynasty:
                            result['dynasty'] = dynasty.group(1).strip()
                        
                        # Get sex
                        sex = re.search(r'<sex value="(\d)"/>', block)
                        if sex:
                            result['sex'] = 'Nam' if sex.group(1) == '1' else 'Nữ'
                        
                        # Get monk status
                        monk = re.search(r'<note type="monk">([^<]+)</note>', block)
                        if monk:
                            result['is_monk'] = 'Có' if monk.group(1) == '是' else 'Không'
                        
                        # Get concise bio
                        if not result['bio_snippet']:
                            concise = re.search(r'<note type="concise">(.*?)</note>', block)
                            if concise:
                                result['bio_snippet'] = concise.group(1).strip()[:500]
                        
                        # Get extensive bio
                        extensive = re.search(r'<note type="extensive">(.*?)</note>', block)
                        if extensive:
                            result['extensive_bio'] = extensive.group(1).strip()[:800]
                        
                        # Get teachers
                        teachers = re.findall(r'<relation type="teacher"[^>]*n="([^"]+)"', block)
                        result['teacher'] = ', '.join(teachers)
                        
                        # Get students
                        students = re.findall(r'<relation type="student"[^>]*n="([^"]+)"', block)
                        result['students'] = ', '.join(students)
                        
                        # Get works
                        works = re.findall(r'<note type="worksInTripitaka">(.*?)</note>', block)
                        if works:
                            result['works'] = ', '.join([w.strip() for w in works])
                        
                        # Get bibliography
                        bibls = re.findall(r'<bibl>(.*?)</bibl>', block)
                        if bibls:
                            result['bibl'] = ' | '.join([b.replace('<ref target="[^"]+">', '(').replace('</ref>', ')') for b in bibls[:5]])
                except Exception as e:
                    print(f"Error parsing XML: {e}")
            
            return jsonify(result)
        return jsonify({'error': 'Not found'}), 404
    finally:
        conn.close()

@app.route('/daoanh/api/admin/namevi-map/delete', methods=['POST'])
@app.route('/api/admin/namevi-map/delete', methods=['POST'])
def admin_namevi_map_delete():
    data = request.get_json()
    dila_id = data.get('dila_id')
    if not dila_id:
        return jsonify({'success': False, 'error': 'Missing dila_id'}), 400
    conn = sqlite3.connect(SQLITE_DB)
    try:
        cur = conn.execute('DELETE FROM name_vi_map WHERE dila_id = ?', (dila_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify({'success': True, 'dila_id': dila_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/daoanh/api/admin/namevi-map/update', methods=['POST'])
@app.route('/api/admin/namevi-map/update', methods=['POST'])
def admin_namevi_map_update():
    data = request.get_json()
    dila_id = data.get('dila_id')
    name_vi = data.get('name_vi')
    
    if not dila_id or not name_vi:
        return jsonify({'success': False, 'error': 'Missing dila_id or name_vi'}), 400
    
    conn = sqlite3.connect(SQLITE_DB)
    try:
        now = datetime.now().isoformat()
        row = conn.execute("SELECT id FROM name_vi_map WHERE dila_id = ?", (dila_id,)).fetchone()
        if row:
            conn.execute("""
                UPDATE name_vi_map SET
                    name_vi = ?, name_vi_final = ?, name_zh = ?,
                    birth_year = ?, death_year = ?, bio_snippet = ?,
                    approved_by = 'admin', approved_at = ?, updated_at = ?
                WHERE dila_id = ?
            """, (
                name_vi, name_vi,
                data.get('name_zh', ''),
                data.get('birth_year'),
                data.get('death_year'),
                data.get('bio_snippet', ''),
                now, now, dila_id
            ))
        else:
            conn.execute("""
                INSERT INTO name_vi_map (name_vi, name_vi_final, name_zh, birth_year, death_year, bio_snippet, dila_id, approved_by, approved_at, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'admin', ?, 1.0, ?)
            """, (
                name_vi, name_vi,
                data.get('name_zh', ''),
                data.get('birth_year'),
                data.get('death_year'),
                data.get('bio_snippet', ''),
                dila_id, now, now
            ))
        conn.commit()
        return jsonify({'success': True, 'dila_id': dila_id, 'name_vi': name_vi, 'name_vi_final': name_vi})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/namevi-map-places', methods=['GET'])
def admin_namevi_map_places():
    """List place Vietnamese name mappings"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM name_vi_map_places ORDER BY created_at DESC").fetchall()
        return jsonify({
            'mappings': [dict(r) for r in rows],
            'total': len(rows)
        })
    finally:
        conn.close()

@app.route('/api/admin/namevi-map-places/update', methods=['POST'])
def admin_namevi_map_places_update():
    """Add/update place Vietnamese name mapping"""
    data = request.get_json()
    name_vi = data.get('name_vi')
    name_zh = data.get('name_zh')
    dila_id = data.get('dila_id')
    
    if not name_vi:
        return jsonify({'success': False, 'error': 'Missing name_vi'}), 400
    
    conn = sqlite3.connect(SQLITE_DB)
    try:
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT OR REPLACE INTO name_vi_map_places (name_vi, name_zh, dila_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (name_vi, name_zh, dila_id, now))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/namevi-map-places/delete', methods=['POST'])
def admin_namevi_map_places_delete():
    """Delete place Vietnamese name mapping"""
    data = request.get_json()
    dila_id = data.get('dila_id')
    if not dila_id:
        return jsonify({'success': False, 'error': 'Missing dila_id'}), 400
    conn = sqlite3.connect(SQLITE_DB)
    try:
        cur = conn.execute('DELETE FROM name_vi_map_places WHERE dila_id = ?', (dila_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify({'success': True, 'dila_id': dila_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


# ===== VISITOR COUNTER =====
@app.route('/daoanh/api/public/counter')
def visitor_counter():
    COUNTER_FILE = os.path.join(DATA_DIR, 'counter.dat')
    count = 0
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                raw = f.read().strip()
                if raw:
                    count = int(raw)
        count += 1
        with open(COUNTER_FILE, 'w') as f:
            f.write(str(count))
    except Exception:
        pass
    return jsonify({'success': True, 'count': count})

# ============ TRANSLATION & ADMIN APIS (from main) ============

if True:
    
    # ========== TRANSLATION APIs ==========
    
    @app.route('/api/translate/hvdic', methods=['POST'])
    def translate_hvdic():
        """POST /api/translate/hvdic - Dịch Hán-Việt qua HVDic API"""
        data = request.get_json()
        text = data.get('text', '') if data else request.form.get('text', '')
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        try:
            url = "https://hvdic.thivien.net/transcript-query.json.php"
            payload = f"mode=trans&lang=1&input={urllib.parse.quote(text)}"
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            
            resp = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
            result = resp.json().get('result', [])
            
            hanviet = " ".join([el.get('o', [''])[0] for el in result if el.get('o')])
            
            return jsonify({'text': text, 'hanviet': hanviet or text})
        except Exception as e:
            return jsonify({'error': str(e), 'text': text}), 500

    @app.route('/api/translate/google', methods=['GET'])
    def translate_google():
        """GET /api/translate/google?text= - Dịch via MyMemory (free)"""
        text = request.args.get('text', '')
        
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        try:
            url = f"https://api.mymemory.translated.net/get?q={text}&langpair=zh-Hans|vi"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            translated = data.get('responseData', {}).get('translatedText', text)
            
            return jsonify({'text': text, 'google': translated})
        except Exception as e:
            return jsonify({'error': str(e), 'text': text}), 500

    @app.route('/daoanh/api/translate/all', methods=['GET'])
    @app.route('/api/translate/all', methods=['GET'])
    def translate_all():
        """GET /api/translate/all?text= - Return all translations"""
        text = request.args.get('text', '')
        name_zh = request.args.get('name_zh', text)
        
        search_text = text or name_zh
        if not search_text:
            return jsonify({'error': 'Missing text'}), 400
        
        result = {'text': search_text, 'hvdic': '', 'google': '', 'final': ''}
        
        # Try HVDic
        try:
            url = "https://hvdic.thivien.net/transcript-query.json.php"
            payload = f"mode=trans&lang=1&input={urllib.parse.quote(search_text)}"
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            resp = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
            hv_result = resp.json().get('result', [])
            result['hvdic'] = " ".join([el.get('o', [''])[0] for el in hv_result if el.get('o')])
        except:
            pass
        
        # Try MyMemory
        try:
            url = f"https://api.mymemory.translated.net/get?q={search_text}&langpair=zh-Hans|vi"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            result['google'] = data.get('responseData', {}).get('translatedText', '')
        except:
            pass
        
        result['final'] = result['hvdic'] or result['google'] or search_text
        
        return jsonify(result)

    def _suggest_name(main_name_han, aka_names_raw='', bio='', refs=''):
        """Generate a Vietnamese name suggestion. Returns string or None."""
        if not main_name_han:
            return None
        prompt_lines = [
            "Bạn là công cụ chuẩn hóa tên tăng sĩ / nhân vật Phật giáo từ chữ Hán sang tên tiếng Việt chuẩn Hán-Việt dùng trong nghiên cứu Phật học Hán tạng.",
            "",
            "YÊU CẦU:",
            "1. Ưu tiên main_name_han để quyết định tên chính.",
            "2. Dùng aka_names_raw để nhận thêm biệt hiệu Hán nếu hữu ích, bỏ qua tiếng Nhật (kana) và Latin/Pinyin.",
            "3. Chỉ phiên âm Hán-Việt, không dịch nghĩa sang tiếng Việt hiện đại.",
            "4. Kết quả là một tên tiếng Việt duy nhất, ngắn gọn.",
            "5. Viết hoa chuẩn (chữ cái đầu mỗi tiếng).",
            "6. Không liệt kê nhiều phương án, không giải thích, không in lại chữ Hán.",
            "7. Output là một dòng duy nhất, chỉ chứa tên tiếng Việt.",
            "",
            "---",
            "DỮ LIỆU:",
            "main_name_han: " + main_name_han,
        ]
        if aka_names_raw:
            prompt_lines.append("aka_names_raw: " + aka_names_raw)
        if bio:
            prompt_lines.append("bio: " + bio[:500])
        if refs:
            prompt_lines.append("refs: " + refs[:200])
        prompt_lines.append("")
        prompt_lines.append("Output:")
        prompt = "\n".join(prompt_lines)
        result = _call_gemini(prompt, timeout=15)
        if result:
            result = result.strip()
            if len(result) <= 100 and '\n' not in result:
                return result
        try:
            url = "https://hvdic.thivien.net/transcript-query.json.php"
            payload = "mode=trans&lang=1&input=" + urllib.parse.quote(main_name_han)
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            resp = requests.post(url, headers=headers, data=payload.encode('utf-8'), timeout=10)
            hv_result = resp.json().get('result', [])
            hv_text = " ".join([el.get('o', [''])[0] for el in hv_result if el.get('o')])
            if hv_text:
                return hv_text.strip().title()
        except Exception:
            pass
        return None

    @app.route('/api/admin/namevi/suggest', methods=['POST'])
    def admin_namevi_suggest():
        """
        POST /api/admin/namevi/suggest
        Body: {"main_name_han": "笑庵了悟", "aka_names_raw": "...", "bio": "...", "refs": "..."}
        Returns: {"vietnamese_name": "Tiếu Am Liễu Ngộ"} or error.
        Uses Gemini 2.0 Flash with a structured Hán-Việt name suggestion prompt.
        """
        body = request.get_json(silent=True) or {}
        main_name_han = (body.get('main_name_han') or '').strip()
        aka_names_raw = (body.get('aka_names_raw') or '').strip()
        bio = (body.get('bio') or '').strip()
        refs = (body.get('refs') or '').strip()
        dila_id = (body.get('dila_id') or '').strip()
        if not main_name_han:
            return jsonify({"success": False, "error": "Thiếu main_name_han"}), 400

        result = _suggest_name(main_name_han, aka_names_raw, bio, refs)
        if not result:
            return jsonify({"success": False, "error": "Không thể sinh tên gợi ý"}), 502

        # Auto-save to name_vi_auto in name_vi_map
        if dila_id:
            try:
                conn2 = sqlite3.connect(SQLITE_DB)
                row = conn2.execute(
                    "SELECT id, name_vi_final FROM name_vi_map WHERE dila_id = ?", (dila_id,)
                ).fetchone()
                now = datetime.now().isoformat()
                if row:
                    conn2.execute(
                        "UPDATE name_vi_map SET name_vi_auto = ? WHERE dila_id = ?",
                        (result, dila_id,)
                    )
                else:
                    conn2.execute(
                        "INSERT INTO name_vi_map (name_vi, name_vi_auto, name_zh, dila_id, source, confidence, created_at) VALUES (?, ?, ?, ?, 'auto_suggest', 0.7, ?)",
                        (result, result, main_name_han, dila_id, now)
                    )
                conn2.commit()
                conn2.close()
            except Exception:
                pass

        return jsonify({
            "success": True, "vietnamese_name": result, "provider": "auto", "dila_id": dila_id
        })

    @app.route('/api/admin/namevi-map/approve', methods=['POST'])
    def admin_namevi_map_approve():
        """
        POST /api/admin/namevi-map/approve
        Body: {"dila_id": "A000001", "name_vi_final": "optional override"}
        Copies name_vi_auto → name_vi_final and sets approved_by/approved_at.
        If name_vi_final is provided, uses that instead of auto.
        """
        data = request.get_json(silent=True) or {}
        dila_id = (data.get('dila_id') or '').strip()
        override = (data.get('name_vi_final') or '').strip()
        if not dila_id:
            return jsonify({"success": False, "error": "Thiếu dila_id"}), 400
        conn = None
        try:
            conn = sqlite3.connect(SQLITE_DB)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT id, name_vi_auto, name_vi_final FROM name_vi_map WHERE dila_id = ?", (dila_id,)).fetchone()
            if not row:
                return jsonify({"success": False, "error": "Không tìm thấy bản ghi"}), 404
            final_val = override or row['name_vi_auto'] or ''
            if not final_val:
                return jsonify({"success": False, "error": "Không có name_vi_auto để duyệt"}), 400
            now = datetime.now().isoformat()
            conn.execute("""
                UPDATE name_vi_map SET name_vi_final = ?, name_vi = ?, approved_by = 'admin', approved_at = ?
                WHERE dila_id = ?
            """, (final_val, final_val, now, dila_id))
            conn.commit()
            return jsonify({"success": True, "dila_id": dila_id, "name_vi_final": final_val})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            if conn: conn.close()

    @app.route('/api/admin/namevi/batch-suggest', methods=['POST'])
    def admin_namevi_batch_suggest():
        """
        POST /api/admin/namevi/batch-suggest
        Body: {"limit": 100, "dila_ids": ["A000001", ...]}  (optional limit or specific IDs)
        Generates name_vi_auto for all records in the queue without it.
        Returns count of records processed.
        """
        body = request.get_json(silent=True) or {}
        limit = body.get('limit', 50)
        specific_ids = body.get('dila_ids', None)

        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        try:
            if specific_ids:
                placeholders = ','.join('?' * len(specific_ids))
                rows = conn.execute(f"""
                    SELECT p.id, p.name_zh
                    FROM people p
                    LEFT JOIN name_vi_map n ON p.id = n.dila_id
                    WHERE p.id IN ({placeholders})
                      AND (n.name_vi_auto IS NULL OR n.name_vi_auto = '')
                      AND p.name_zh IS NOT NULL AND p.name_zh != ''
                    LIMIT ?
                """, (*specific_ids, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT p.id, p.name_zh
                    FROM people p
                    LEFT JOIN name_vi_map n ON p.id = n.dila_id
                    WHERE (n.name_vi_auto IS NULL OR n.name_vi_auto = '')
                      AND p.name_zh IS NOT NULL AND p.name_zh != ''
                    LIMIT ?
                """, (limit,)).fetchall()
            conn.close()

            processed = 0
            errors = []
            for r in rows:
                try:
                    result = _suggest_name(r['name_zh'], '')
                    if result:
                        dila_id = r['id']
                        conn2 = sqlite3.connect(SQLITE_DB)
                        existing = conn2.execute(
                            "SELECT id, name_vi_final FROM name_vi_map WHERE dila_id = ?", (dila_id,)
                        ).fetchone()
                        now = datetime.now().isoformat()
                        if existing:
                            conn2.execute(
                                "UPDATE name_vi_map SET name_vi_auto = ? WHERE dila_id = ?",
                                (result, dila_id,)
                            )
                        else:
                            conn2.execute(
                                "INSERT INTO name_vi_map (name_vi, name_vi_auto, name_zh, dila_id, source, confidence, created_at) VALUES (?, ?, ?, ?, 'auto_suggest', 0.7, ?)",
                                (result, result, r['name_zh'], dila_id, now)
                            )
                        conn2.commit()
                        conn2.close()
                        processed += 1
                except Exception as e:
                    errors.append({'dila_id': r['id'], 'error': str(e)})
            return jsonify({
                "success": True, "processed": processed, "total": len(rows), "errors": errors
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


    # Initialize name_vi_map_places table if not exists
    conn = sqlite3.connect(SQLITE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS name_vi_map_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT NOT NULL,
            name_zh TEXT,
            dila_id TEXT UNIQUE,
            confidence REAL DEFAULT 1.0,
            source TEXT DEFAULT 'admin',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    # Check directories
    

    @app.route('/api/admin/sqlite-search', methods=['GET'])
    def admin_sqlite_search():
        """GET /api/admin/sqlite-search?q=<text> - Search across all tables for Chinese text"""
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'error': 'Missing search term'}), 400
        
        conn = get_db()
        results = {}
        
        try:
            # Tables to search (with text columns that might contain Chinese)
            # Note: Exclude 'places_pending' (DILA import data), only search processed/reference tables
            tables_to_search = [
                ('name_vi_map', ['name_zh', 'name_vi', 'bio_snippet']),
                ('name_vi_map_places', ['name_zh', 'name_vi']),
                ('places_vps', ['name_zh', 'name_vi', 'address']),
                # places_dila now has 17 columns - search all relevant text fields
                ('places_dila', ['name_zh', 'name_vi', 'name_en', 'name_san', 'name_jpn', 'name_other', 
                                'district', 'note', 'note_category', 'listbibl', 'location_xml']),
                ('people', ['name_zh', 'name_vi', 'bio']),
                ('entity_monks', ['name_zh', 'name_vi']),
                ('text_mapping', ['name_zh', 'name_vi']),
                # Dictionary/lexicon tables for Chinese-Vietnamese translation
                ('lexicon', ['term', 'normalized', 'definition']),
                ('lexicon_fts', ['term', 'normalized', 'definition']),
            ]
            
            for table, columns in tables_to_search:
                try:
                    # Check if table exists
                    table_exists = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                        (table,)
                    ).fetchone()
                    
                    if not table_exists:
                        continue
                    
                    # Build search query using LIKE for each column
                    conditions = []
                    params = []
                    for col in columns:
                        conditions.append(f"{col} LIKE ?")
                        params.append(f"%{search_term}%")
                    
                    query = f"SELECT * FROM {table} WHERE {' OR '.join(conditions)} LIMIT 10"
                    rows = conn.execute(query, params).fetchall()
                    
                    if rows:
                        results[table] = [dict(r) for r in rows]
                except Exception as e:
                    continue
            
            return jsonify({'search_term': search_term, 'results': results, 'total_tables': len(results)})
        finally:
            conn.close()
    
    @app.route('/api/admin/auto-scan', methods=['GET'])
    def admin_auto_scan():
        """GET /api/admin/auto-scan?limit=10 - Auto scan DILA places, prioritize those with SQLite results"""
        limit = request.args.get('limit', 10, type=int)
        conn = get_db()
        results = []
        
        try:
            # Get DILA places without Vietnamese names
            places = conn.execute(
                "SELECT * FROM places_pending WHERE name_vi IS NULL OR name_vi = '' LIMIT ?", 
                (limit,)
            ).fetchall()
            
            for place in places:
                p = dict(place)
                # Search SQLite for this place's Chinese name
                search_term = p.get('name_zh', '')
                sqlite_results = {}
                total_tables = 0
                
                if search_term:
                    # Search in reference tables
                    tables_to_search = [
                        ('name_vi_map', ['name_zh', 'name_vi', 'bio_snippet']),
                        ('name_vi_map_places', ['name_zh', 'name_vi']),
                        ('places_vps', ['name_zh', 'name_vi', 'address']),
                        # places_dila now has 17 columns - search all relevant text fields
                        ('places_dila', ['name_zh', 'name_vi', 'name_en', 'name_san', 'name_jpn', 'name_other', 
                                        'district', 'note', 'note_category', 'listbibl', 'location_xml']),
                        ('people', ['name_zh', 'name_vi', 'bio']),
                        ('entity_monks', ['name_zh', 'name_vi']),
                        ('text_mapping', ['name_zh', 'name_vi']),
                        # Lexicon dictionary - use correct column names
                        ('lexicon', ['term', 'normalized', 'definition']),
                        ('lexicon_fts', ['term', 'normalized', 'definition']),
                    ]
                    
                    for table, columns in tables_to_search:
                        try:
                            table_exists = conn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                                (table,)
                            ).fetchone()
                            
                            if not table_exists:
                                continue
                            
                            conditions = []
                            params = []
                            for col in columns:
                                conditions.append(f"{col} LIKE ?")
                                params.append(f"%{search_term}%")
                            
                            query = f"SELECT * FROM {table} WHERE {' OR '.join(conditions)} LIMIT 5"
                            rows = conn.execute(query, params).fetchall()
                            
                            if rows:
                                sqlite_results[table] = [dict(r) for r in rows]
                                total_tables += 1
                        except:
                            continue
                
                results.append({
                    'place': p,
                    'sqlite_results': sqlite_results,
                    'total_tables': total_tables,
                    'has_results': total_tables > 0
                })
            
            # Sort: places with SQLite results first (prioritize)
            results.sort(key=lambda x: x['has_results'], reverse=True)
            
            return jsonify({
                'limit': limit,
                'total_scanned': len(results),
                'results': results
            })
        finally:
            conn.close()
    
    @app.route('/api/admin/get-all-data/<place_id>')
    def admin_get_all_data(place_id):
        """GET /api/admin/get-all-data/<place_id> - Get complete data from ALL tables for a place"""
        conn = get_db()
        try:
            result = {'place_id': place_id, 'tables': {}}
            
            # 1. Check places_dila (17 columns with full DILA data)
            # First try exact match
            row = conn.execute("""
                SELECT id, name, name_zh, name_en, name_san, name_jpn, name_peo, name_other,
                       geo_lat, geo_long, place_key, district, note, note_category, listbibl, raw_xml
                FROM places_dila WHERE id = ?
            """, (place_id,)).fetchone()
            
            if not row:
                # Try matching by numeric portion (handle ID format mismatch)
                row = conn.execute("""
                    SELECT id, name, name_zh, name_en, name_san, name_jpn, name_peo, name_other,
                           geo_lat, geo_long, place_key, district, note, note_category, listbibl, raw_xml
                    FROM places_dila 
                    WHERE CAST(SUBSTR(id, 3) AS INTEGER) = CAST(SUBSTR(?, 3) AS INTEGER)
                """, (place_id,)).fetchone()
            
            if row:
                result['tables']['places_dila'] = {
                    'id': row[0],
                    'name': row[1],
                    'name_zh': row[2],
                    'name_en': row[3],
                    'name_san': row[4],
                    'name_jpn': row[5],
                    'name_peo': row[6],
                    'name_other': row[7],
                    'geo_lat': row[8],
                    'geo_long': row[9],
                    'place_key': row[10],
                    'district': row[11],
                    'note': row[12],
                    'note_category': row[13],
                    'listbibl': row[14],
                    'raw_xml': row[15][:1000] + '...' if row[15] and len(row[15]) > 1000 else row[15]  # Truncate raw_xml
                }
            
            # 2. Check places_pending
            row = conn.execute("SELECT * FROM places_pending WHERE id = ?", (place_id,)).fetchone()
            if row:
                result['tables']['places_pending'] = dict(row)
            
            # 3. Check places_vps (if migrated)
            if '_' not in place_id:  # places_vps IDs don't have underscore
                row = conn.execute("SELECT * FROM places_vps WHERE id = ?", (place_id,)).fetchone()
                if row:
                    result['tables']['places_vps'] = dict(row)
            
            # 4. Check name_vi_map_places
            row = conn.execute("SELECT * FROM name_vi_map_places WHERE dila_id = ?", (place_id,)).fetchone()
            if row:
                result['tables']['name_vi_map_places'] = dict(row)
            
            # Summary
            result['total_tables'] = len(result['tables'])
            result['has_data'] = result['total_tables'] > 0
            
            return jsonify(result)
        finally:
            conn.close()
    
    @app.route('/api/admin/migrate-place-types', methods=['POST'])
    def admin_migrate_place_types():
        """POST /api/admin/migrate-place-types - Migrate old place types to new groups"""
        conn = get_db()
        try:
            results = {}
            
            # Migration for places_vps (has place_type column)
            migrations_vps = [
                ("UPDATE places_vps SET place_type = 'Nhóm Cơ sở Tôn giáo' WHERE place_type IN ('Chùa', 'Tự', 'Viện', 'Am', 'Đạo tràng', 'Tịnh xá', 'Thánh địa', 'Giới đàn', 'Hang tu hành')", 'places_vps'),
                ("UPDATE places_vps SET place_type = 'Nhóm Hành chính – Chính trị' WHERE place_type IN ('Tổ đình', 'Kinh đô', 'Phủ', 'Lộ', 'Trấn', 'Thôn', 'Lý', 'Địa khu', 'Vùng rộng không rõ cấp hành chính')", 'places_vps'),
                ("UPDATE places_vps SET place_type = 'Nhóm Địa lý tự nhiên' WHERE place_type IN ('Thắng cảnh', 'Núi', 'Thủy', 'Hang', 'Giang', 'Hà', 'Hồ', 'Trì', 'Hải', 'Đảo', 'Cốc', 'Cao nguyên', 'Sa mạc', 'Lâm')", 'places_vps'),
                ("UPDATE places_vps SET place_type = 'Nhóm Di tích – Kiến trúc' WHERE place_type IN ('Di tích Quốc gia', 'Tháp', 'Cung điện', 'Điện thờ', 'Lăng Mộ', 'Bia ký', 'Phế tích', 'Di chỉ khảo cổ')", 'places_vps'),
            ]
            
            for query, table in migrations_vps:
                try:
                    cursor = conn.execute(query)
                    count = cursor.rowcount
                    conn.commit()
                    results[table] = count
                except Exception as e:
                    results[f"error_{table}"] = str(e)
            
            # Migration for places_pending (has place_type column)
            migrations_pending = [
                ("UPDATE places_pending SET place_type = 'Nhóm Cơ sở Tôn giáo' WHERE place_type IN ('Chùa', 'Tự', 'Viện', 'Am', 'Đạo tràng', 'Tịnh xá', 'Thánh địa', 'Giới đàn', 'Hang tu hành')", 'places_pending'),
                ("UPDATE places_pending SET place_type = 'Nhóm Hành chính – Chính trị' WHERE place_type IN ('Tổ đình', 'Kinh đô', 'Phủ', 'Lộ', 'Trấn', 'Thôn', 'Lý', 'Địa khu', 'Vùng rộng không rõ cấp hành chính')", 'places_pending'),
                ("UPDATE places_pending SET place_type = 'Nhóm Địa lý tự nhiên' WHERE place_type IN ('Thắng cảnh', 'Núi', 'Thủy', 'Hang', 'Giang', 'Hà', 'Hồ', 'Trì', 'Hải', 'Đảo', 'Cốc', 'Cao nguyên', 'Sa mạc', 'Lâm')", 'places_pending'),
                ("UPDATE places_pending SET place_type = 'Nhóm Di tích – Kiến trúc' WHERE place_type IN ('Di tích Quốc gia', 'Tháp', 'Cung điện', 'Điện thờ', 'Lăng Mộ', 'Bia ký', 'Phế tích', 'Di chỉ khảo cổ')", 'places_pending'),
            ]
            
            for query, table in migrations_pending:
                try:
                    cursor = conn.execute(query)
                    count = cursor.rowcount
                    conn.commit()
                    if table in results:
                        results[table] += count
                    else:
                        results[table] = count
                except Exception as e:
                    results[f"error_{table}"] = str(e)
            
            return jsonify({'success': True, 'message': 'Migration completed', 'results': results})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()
    

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


@app.route('/daoanh/api/admin/keywords/parse_txt', methods=['POST'])
def keywords_parse_txt():
    """POST /daoanh/api/admin/keywords/parse_txt
    Body: { raw: "string" }
    Parses StarDict/2-line format: keyword\\nvalue\\n\\nkeyword\\nvalue...
    Returns { items: [{keyword, value}], warnings: [...] }"""
    try:
        data = request.get_json(force=True)
        raw = (data.get('raw') or '').strip()
        if not raw:
            return jsonify({"success": True, "items": [], "warnings": []})

        blocks = re.split(r'\n{2,}', raw)
        items = []
        warnings = []

        cjk_pat = re.compile(r'[\u4e00-\u9fff]+')

        def _make_val(chinese_chars, definition):
            """Build value: chinese + : + definition, wrapped in parens."""
            val = chinese_chars + ': ' + definition
            if not val.startswith('('):
                val = '(' + val + ')'
            return normalize_value(val)

        def _split_cjk_left(left):
            """Tách CJK khỏi left, trả về (keyword_raw, cjk_chars)."""
            cjk_chars = ''.join(cjk_pat.findall(left))
            if cjk_chars:
                keyword_raw = cjk_pat.sub('', left).strip()
                return keyword_raw, cjk_chars
            return left, ''

        for i, block in enumerate(blocks):
            block_raw = block.strip()
            if not block_raw:
                continue

            # Rule 0: thử tách theo dấu ": " (colon + space) trên toàn block
            colon_idx = block_raw.find(': ')
            if colon_idx != -1:
                left = block_raw[:colon_idx].strip()
                right = block_raw[colon_idx + 2:].strip()
                keyword_raw, cjk_chars = _split_cjk_left(left)
                kw = normalize_keyword(keyword_raw)
                if cjk_chars:
                    val = _make_val(cjk_chars, right)
                else:
                    val = normalize_value(right)
                if kw and val:
                    items.append({"keyword": kw, "value": val})
                    continue

            # Rule 1: thử tách theo dấu ngoặc đơn "(" đầu tiên
            m = re.search(r'\(', block_raw)
            if m:
                kw = normalize_keyword(block_raw[:m.start()].strip())
                val = normalize_value(block_raw[m.start():].strip())
                if kw and val:
                    items.append({"keyword": kw, "value": val})
                    continue

            # Fallback: tách theo dòng
            lines = [l.strip() for l in block_raw.split('\n') if l.strip()]
            if not lines:
                continue

            # Rule 2: block >= 2 dòng → dòng 1 = key, còn lại = value
            if len(lines) >= 2:
                keyword = normalize_keyword(lines[0])
                value = normalize_value('\n'.join(lines[1:]).strip())
                if keyword and value:
                    items.append({"keyword": keyword, "value": value})
                else:
                    warnings.append(f"Block {i+1}: keyword hoặc value rỗng, đã bỏ qua")
                continue

            # Rule 3: block 1 dòng → thử tách theo dấu ":" hoặc "："
            line = lines[0]
            parsed = False
            for sep in [":", "："]:
                if sep in line:
                    left, right = line.split(sep, 1)
                    keyword_raw, cjk_chars = _split_cjk_left(left.strip())
                    kw = normalize_keyword(keyword_raw)
                    if cjk_chars:
                        val = _make_val(cjk_chars, right.strip())
                    else:
                        val = normalize_value(right.strip())
                    if kw and val:
                        items.append({"keyword": kw, "value": val})
                        parsed = True
                        break
            if not parsed:
                warnings.append(f"Block {i+1}: không tách được key/value (nội dung: '{line[:60]}')")

        return jsonify({"success": True, "items": items, "warnings": warnings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/bulk_import', methods=['POST'])
def keywords_bulk_import():
    """POST /daoanh/api/admin/keywords/bulk_import
    Body: { items: [{keyword, value}], category: "import_ui" }
    Bulk inserts into keyword_map table."""
    try:
        data = request.get_json(force=True)
        items = data.get('items', [])
        category = data.get('category', 'import_ui')
        if not items:
            return jsonify({"success": False, "error": "No items to import"}), 400

        conn = get_db_connection()
        try:
            imported = 0
            for item in items:
                kw = normalize_keyword(item.get('keyword') or '')
                val = normalize_value(item.get('value') or '')
                if not kw or not val:
                    continue
                conn.execute(
                    "INSERT INTO keyword_map (keyword, value, category) VALUES (?, ?, ?)",
                    (kw, val, category)
                )
                imported += 1
            conn.commit()
            return jsonify({"success": True, "imported": imported})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/export_stardict')
def keywords_export_stardict():
    """GET /daoanh/api/admin/keywords/export_stardict
    Returns keyword_map data as StarDict txt download."""
    try:
        category = request.args.get('category', 'import_ui')
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT keyword, value FROM keyword_map WHERE category = ? ORDER BY keyword",
                (category,)
            ).fetchall()
            lines = []
            for r in rows:
                lines.append(r['keyword'])
                lines.append(r['value'])
                lines.append('')
            content = '\n'.join(lines)
            return Response(
                content,
                mimetype='text/plain; charset=utf-8',
                headers={
                    'Content-Disposition': 'attachment; filename="Chu Thich Phat Hoc - VPS.txt"',
                    'Content-Type': 'text/plain; charset=utf-8'
                }
            )
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/search')
def keywords_search():
    """GET /daoanh/api/admin/keywords/search?q=...&limit=20
    Search keyword_map by keyword (LIKE). Returns JSON list."""
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    limit = min(int(request.args.get('limit', 20)), 100)
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, keyword, value FROM keyword_map WHERE keyword LIKE ? ORDER BY keyword COLLATE NOCASE LIMIT ?",
            (f'%{q}%', limit)
        ).fetchall()
        return jsonify([{"id": r['id'], "keyword": r['keyword'], "value": r['value']} for r in rows])
    finally:
        conn.close()


@app.route('/daoanh/api/admin/keywords/duplicates')
def keywords_duplicates():
    """GET /daoanh/api/admin/keywords/duplicates
    Finds keywords with COUNT > 1 in keyword_map.
    Returns grouped JSON."""
    conn = get_db_connection()
    try:
        dup_rows = conn.execute(
            "SELECT keyword FROM keyword_map GROUP BY keyword HAVING COUNT(*) > 1 ORDER BY keyword COLLATE NOCASE"
        ).fetchall()
        dup_keywords = [r['keyword'] for r in dup_rows]
        if not dup_keywords:
            return jsonify([])

        placeholders = ','.join('?' for _ in dup_keywords)
        rows = conn.execute(
            f"SELECT id, keyword, value FROM keyword_map WHERE keyword IN ({placeholders}) ORDER BY keyword COLLATE NOCASE, id",
            dup_keywords
        ).fetchall()

        groups = {}
        for r in rows:
            groups.setdefault(r['keyword'], []).append({
                "id": r['id'],
                "keyword": r['keyword'],
                "value": r['value'] or ''
            })

        result = [{"keyword": kw, "count": len(items), "items": items} for kw, items in groups.items()]
        return jsonify(result)
    finally:
        conn.close()


@app.route('/daoanh/api/admin/keywords/<int:kw_id>/update', methods=['POST'])
def keywords_update(kw_id):
    """POST /daoanh/api/admin/keywords/<id>/update
    Body: { keyword, value }"""
    try:
        data = request.get_json(force=True) or {}
        kw = normalize_keyword(data.get('keyword', ''))
        val = (data.get('value') or '').strip()
        if not kw or not val:
            return jsonify({"ok": False, "error": "keyword and value are required"}), 400
        conn = get_db_connection()
        try:
            conn.execute("UPDATE keyword_map SET keyword = ?, value = ? WHERE id = ?", (kw, val, kw_id))
            conn.commit()
            return jsonify({"ok": True})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/<int:kw_id>/delete', methods=['POST'])
def keywords_delete(kw_id):
    """POST /daoanh/api/admin/keywords/<id>/delete"""
    try:
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM keyword_map WHERE id = ?", (kw_id,))
            conn.commit()
            return jsonify({"ok": True})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/export_json')
def keywords_export_json():
    """GET /daoanh/api/admin/keywords/export_json?category=...
    Returns keyword_map as JSON download."""
    try:
        category = request.args.get('category', '').strip()
        conn = get_db_connection()
        try:
            if category:
                rows = conn.execute(
                    "SELECT id, keyword, value, category, source, created_at FROM keyword_map WHERE category = ? ORDER BY keyword",
                    (category,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, keyword, value, category, source, created_at FROM keyword_map ORDER BY category, keyword"
                ).fetchall()
            result = [dict(r) for r in rows]
            return Response(
                json.dumps(result, ensure_ascii=False, indent=2),
                mimetype='application/json; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename="keyword_map_{category or "all"}.json"'
                }
            )
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/bulk_delete', methods=['POST'])
def keywords_bulk_delete():
    """POST /daoanh/api/admin/keywords/bulk_delete
    Body: { ids: [1, 2, 3] }"""
    try:
        data = request.get_json(force=True) or {}
        ids = data.get('ids', [])
        if not ids:
            return jsonify({"success": False, "error": "No ids provided"}), 400
        conn = get_db_connection()
        try:
            placeholders = ','.join('?' for _ in ids)
            conn.execute(f"DELETE FROM keyword_map WHERE id IN ({placeholders})", ids)
            conn.commit()
            return jsonify({"success": True, "deleted": len(ids)})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/keywords/categories')
def keywords_categories():
    """GET /daoanh/api/admin/keywords/categories
    Returns list of distinct categories with counts."""
    try:
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM keyword_map GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            return jsonify([{"category": r['category'], "count": r['cnt']} for r in rows])
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== DILA INTEGRATION LAYER API (ENTITY + PASSAGES) =====

@app.route('/daoanh/api/entity/<entity_id>')
def entity_info(entity_id):
    """GET /daoanh/api/entity/<entity_id>
    Returns entity info from the ENTITY table."""
    conn = get_db_connection()
    try:
        entity = conn.execute(
            "SELECT * FROM entity WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if not entity:
            # Try with normalized PL ID
            digits = re.sub(r'[^0-9]', '', entity_id)
            if entity_id.startswith('PL') or (digits and len(digits) >= 6):
                normalized = 'PL' + digits
                entity = conn.execute(
                    "SELECT * FROM entity WHERE entity_id = ?", (normalized,)
                ).fetchone()
        if not entity:
            return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 200
        result = dict(entity)
        if entity['marcus_id']:
            marcus_ref = conn.execute(
                "SELECT label AS marcus_label, label_vi AS marcus_label_vi, birth_year AS marcus_birth, death_year AS marcus_death "
                "FROM marcus_reference WHERE node_id = ?", (entity['marcus_id'],)
            ).fetchone()
            if marcus_ref:
                result['marcus'] = dict(marcus_ref)
        return jsonify({"success": True, "has_data": True, "entity": result})
    finally:
        conn.close()


@app.route('/daoanh/api/entity/<entity_id>/marcus')
def entity_marcus(entity_id):
    """GET /daoanh/api/entity/<entity_id>/marcus
    Returns Marcus glossary reference + network data for this entity."""
    conn = get_db_connection()
    try:
        entity = conn.execute(
            "SELECT entity_id, marcus_id FROM entity WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if not entity or not entity['marcus_id']:
            return jsonify({"success": False, "has_data": False, "error": "No Marcus data for this entity"}), 200

        mid = entity['marcus_id']
        ref = conn.execute(
            "SELECT * FROM marcus_reference WHERE node_id = ?", (mid,)
        ).fetchone()

        teachers = conn.execute(
            "SELECT teacher_id, teacher_label FROM marcus_networks WHERE student_id = ?", (mid,)
        ).fetchall()
        students = conn.execute(
            "SELECT student_id, student_label FROM marcus_networks WHERE teacher_id = ?", (mid,)
        ).fetchall()
        edge_count = len(teachers) + len(students)

        return jsonify({
            "success": True,
            "has_data": True,
            "entity_id": entity_id,
            "marcus_id": mid,
            "reference": dict(ref) if ref else None,
            "teachers": [dict(t) for t in teachers],
            "students": [dict(s) for s in students],
            "edge_count": edge_count
        })
    finally:
        conn.close()


@app.route('/daoanh/api/entity/<entity_id>/passages')
def entity_passages(entity_id):
    """GET /daoanh/api/entity/<entity_id>/passages
    Query params: limit (50), offset (0), source (CBETA), mode (linked|like)
    mode=linked: use PASSAGE_ENTITY table (pre-built links, default)
    mode=like: LIKE search on raw_text using entity alias_zh at query time"""
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    source = request.args.get('source', 'CBETA')
    mode = request.args.get('mode', 'linked')

    conn = get_db_connection()
    try:
        if mode == 'like':
            entity = conn.execute(
                "SELECT entity_id, alias_zh, alias_vi FROM entity WHERE entity_id = ?",
                (entity_id,)
            ).fetchone()
            if not entity:
                return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 200

            alias = entity['alias_zh'] or entity['alias_vi']
            if not alias or len(alias) < 2:
                return jsonify({
                    "success": True, "has_data": False, "mode": mode,
                    "entity_id": entity_id, "count": 0, "passages": [],
                    "note": "Entity alias too short for LIKE matching (need >=2 chars)"
                })

            like_pattern = f'%{alias}%'
            total = conn.execute(
                "SELECT COUNT(*) FROM passage WHERE source = ? AND raw_text LIKE ?",
                (source, like_pattern)
            ).fetchone()[0]

            rows = conn.execute(
                "SELECT passage_id, source, text_id, loc_ref, raw_text, norm_text "
                "FROM passage WHERE source = ? AND raw_text LIKE ? "
                "ORDER BY passage_id LIMIT ? OFFSET ?",
                (source, like_pattern, limit, offset)
            ).fetchall()

            return jsonify({
                "success": True, "has_data": total > 0, "mode": mode,
                "entity_id": entity_id, "count": total,
                "alias_zh": alias,
                "passages": [dict(r) for r in rows]
            })
        else:
            total = conn.execute(
                """SELECT COUNT(*) FROM passage_entity pe
                   JOIN passage p ON pe.passage_id = p.passage_id
                   WHERE pe.entity_id = ? AND p.source = ?""",
                (entity_id, source)
            ).fetchone()[0]

            rows = conn.execute(
                """SELECT p.passage_id, p.source, p.text_id, p.loc_ref, p.raw_text, p.norm_text
                   FROM passage_entity pe
                   JOIN passage p ON pe.passage_id = p.passage_id
                   WHERE pe.entity_id = ? AND p.source = ?
                   ORDER BY p.passage_id
                   LIMIT ? OFFSET ?""",
                (entity_id, source, limit, offset)
            ).fetchall()

            return jsonify({
                "success": True, "has_data": total > 0, "mode": mode,
                "entity_id": entity_id, "count": total,
                "passages": [dict(r) for r in rows]
            })
    except sqlite3.OperationalError as e:
        return jsonify({"success": True, "has_data": False, "mode": mode,
                        "entity_id": entity_id, "count": 0, "passages": [],
                        "note": f"Table not available: {e}"})
    finally:
        conn.close()


@app.route('/daoanh/api/entity/<entity_id>/summary')
def entity_summary(entity_id):
    """GET /daoanh/api/entity/<entity_id>/summary
    Returns a structured summary of all passages linked to this entity,
    grouped by source text with metadata from CBETA catalog."""
    conn = get_db_connection()
    try:
        entity = conn.execute(
            "SELECT * FROM entity WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        if not entity:
            digits = re.sub(r'[^0-9]', '', entity_id)
            if entity_id.startswith('PL') or (digits and len(digits) >= 6):
                normalized = 'PL' + digits
                entity = conn.execute(
                    "SELECT * FROM entity WHERE entity_id = ?", (normalized,)
                ).fetchone()
        if not entity:
            return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 200

        entity = dict(entity)
        rows = conn.execute(
            """SELECT p.passage_id, p.source, p.text_id, p.loc_ref, p.raw_text, p.norm_text, p.vi_text
               FROM passage_entity pe
               JOIN passage p ON pe.passage_id = p.passage_id
               WHERE pe.entity_id = ?
               ORDER BY p.text_id, p.passage_id""",
            (entity['entity_id'],)
        ).fetchall()

        total = len(rows)
        text_groups = {}
        cbeta_conn = get_cbeta_conn()
        try:
            cbeta_catalog = {}
            for row in cbeta_conn.execute(
                "SELECT sigla, title_zh, author_zh, translator_zh FROM cbeta_texts"
            ).fetchall():
                cbeta_catalog[row['sigla']] = dict(row)
        finally:
            cbeta_conn.close()

        for r in rows:
            r = dict(r)
            tid = r['text_id']
            if tid not in text_groups:
                text_groups[tid] = {
                    "text_id": tid,
                    "catalog": cbeta_catalog.get(tid, {}),
                    "count": 0,
                    "loc_refs": [],
                    "passage_ids": [],
                    "preview_passages": []
                }
            g = text_groups[tid]
            g['count'] += 1
            if r['loc_ref']:
                g['loc_refs'].append(r['loc_ref'])
            g['passage_ids'].append(r['passage_id'])
            if len(g['preview_passages']) < 3:
                g['preview_passages'].append({
                    "passage_id": r['passage_id'],
                    "loc_ref": r['loc_ref'],
                    "raw_text_preview": r['raw_text'][:200],
                    "has_vi": bool(r['vi_text'])
                })

        return jsonify({
            "success": True,
            "has_data": total > 0,
            "entity_id": entity['entity_id'],
            "entity_label_zh": entity.get('alias_zh', ''),
            "entity_label_vi": entity.get('alias_vi', ''),
            "entity_type": entity.get('type', ''),
            "passage_count": total,
            "text_group_count": len(text_groups),
            "text_groups": text_groups
        })
    finally:
        conn.close()


# ===== TAB ĐẠI TẠNG (TASK_TAB_DAI_TANG_PLACE): CANON ENDPOINT =====

@app.route('/daoanh/api/entity/<entity_id>/canon')
def entity_canon(entity_id):
    """GET /daoanh/api/entity/<entity_id>/canon
    Tab "ĐẠI TẠNG" cho ĐỊA ĐIỂM/THỰC THỂ — tổng hợp 3 lớp (chỉ đọc, không đụng DB/schema):
      Layer A  dila_references : ref thô từ places_dila.listbibl + fosizhi (raw_xml)
      Layer B  passages        : passage đã index (passage_entity JOIN passage) + match evidence
      Layer C  texts           : metadata tác phẩm (catalog_mapping JOIN canon_catalog bởi cb_cbeta)
    Query params: page (1), page_size (20) — chỉ áp dụng cho passages.
    Không bịa dữ liệu: translation_count tính từ passage.vi_text thật (hiện = 0)."""
    import re as _re
    page = max(int(request.args.get('page', 1)), 1)
    page_size = min(max(int(request.args.get('page_size', 20)), 1), 100)
    offset = (page - 1) * page_size

    conn = get_db_connection()
    try:
        # 1. Resolve entity — chấp nhận cả short id (places.id / PL023255) và DILA id
        #    (PL000000023255). Dùng _resolve_dila_id để chuẩn hoá về DILA id.
        resolved_dila, resolved_zh = _resolve_dila_id(conn, entity_id)
        cand = entity_id
        if resolved_dila:
            cand = resolved_dila
        entity_row = conn.execute(
            "SELECT entity_id, entity_type, dila_id, alias_zh, alias_vi, extra_alias, cbeta_occ "
            "FROM entity WHERE entity_id = ?", (cand,)).fetchone()
        if not entity_row:
            digits = _re.sub(r'[^0-9]', '', cand)
            if (cand.startswith(('PL', 'pl', 'P')) or (digits and len(digits) >= 6)):
                normalized = 'PL' + digits
                entity_row = conn.execute(
                    "SELECT entity_id, entity_type, dila_id, alias_zh, alias_vi, extra_alias, cbeta_occ "
                    "FROM entity WHERE entity_id = ?", (normalized,)).fetchone()
        if not entity_row:
            return jsonify({"success": False, "has_data": False, "error": "Entity not found"}), 404
        entity = dict(entity_row)

        # Tên Việt ưu tiên từ bản đồ tên (namevi_map_places), fallback alias_vi
        name_vi_row = conn.execute(
            "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? ORDER BY confidence DESC LIMIT 1",
            (entity['entity_id'],)).fetchone()
        name_vi = entity.get('alias_vi') or ''
        if name_vi_row and name_vi_row['name_vi']:
            name_vi = name_vi_row['name_vi']

        # Danh sách alias từ places_dila (tên Hán chuẩn lưu trữ + raw_xml placeName nếu có)
        aliases = []
        authority_sources = []
        dila_row = None
        dila_id = cand
        dila_row = conn.execute(
            "SELECT id, name_zh, name_en, listbibl, raw_xml FROM places_dila WHERE id = ? LIMIT 1",
            (dila_id,)).fetchone()
        if dila_row:
            # tên Hán chuẩn lưu trữ (vd 少室寺) — luôn thêm trước
            stored_zh = (dila_row['name_zh'] or '').strip()
            if stored_zh and stored_zh not in aliases:
                aliases.append(stored_zh)
            for stored_name in [dila_row['name_en']]:
                stored_name = (stored_name or '').strip()
                if stored_name and stored_name not in aliases:
                    aliases.append(stored_name)
            raw_xml = dila_row['raw_xml'] or ''
            for pn in _re.findall(r'<placeName[^>]*>([^<]+)</placeName>', raw_xml):
                pn = pn.strip()
                if pn and pn not in aliases:
                    aliases.append(pn)
            if 'dila' in raw_xml or 'dila' in (dila_row['listbibl'] or ''):
                authority_sources.append('DILA')
        if entity.get('alias_zh') and entity['alias_zh'] not in aliases:
            aliases.insert(0, entity['alias_zh'])
        for a in [entity.get('alias_vi'), entity.get('extra_alias')]:
            if a and a not in aliases:
                aliases.append(a)
        if dila_id and 'DILA' not in authority_sources:
            authority_sources.append('DILA')
        if 'CBETA' not in authority_sources:
            authority_sources.append('CBETA')

        # 2. LAYER A — dẫn chiếu DILA (listbibl + fosizhi)
        dila_references = []
        seen_refs = set()
        if dila_row and dila_row['listbibl']:
            for entry in [e.strip() for e in dila_row['listbibl'].split(';') if e.strip()]:
                m = _re.match(r'\(\s*CBETA\s+([\w_]+)\s*\)\s*(.*)', entry)
                if not m:
                    continue
                ref = m.group(1).strip()
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                rest = m.group(2).strip()
                tag_m = _re.search(r'\{([^}]+)\}', rest)
                place_tag = tag_m.group(1).strip() if tag_m else ''
                title_context = _re.sub(r'\s*\{[^}]+\}\s*', '', rest).strip()
                dila_references.append({
                    'ref_type': 'CBETA',
                    'ref_code': ref,
                    'sigla': ref.split('_')[0] if '_' in ref else ref,
                    'title_context': title_context,
                    'place_tag': place_tag,
                })
        if dila_row and dila_row['raw_xml']:
            raw_xml = dila_row['raw_xml'] or ''
            fz_matches = _re.findall(
                r'target="([^"]*fosizhi[^"]*)">([^(<]+)\(([^)]+)\)</[^>]+>\s*\{([^}]+)\}',
                raw_xml)
            seen_fz = set()
            for url, ref_code, book_title, place_tag in fz_matches:
                ref_code = ref_code.strip()
                if ref_code in seen_fz:
                    continue
                seen_fz.add(ref_code)
                dila_references.append({
                    'ref_type': 'FOSIZHI',
                    'ref_code': ref_code,
                    'book_title': book_title.strip(),
                    'place_tag': place_tag.strip(),
                    'url': url.replace('&amp;', '&'),
                })

        # 3. LAYER B — passage đã index (passage_entity JOIN passage)
        total_passages = conn.execute(
            """SELECT COUNT(*) FROM passage_entity pe
               JOIN passage p ON pe.passage_id = p.passage_id
               WHERE pe.entity_id = ?""", (entity['entity_id'],)).fetchone()[0]
        passage_rows = conn.execute(
            """SELECT p.passage_id, p.source, p.text_id, p.loc_ref, p.raw_text, p.norm_text,
                      p.vi_text, p.translation_draft
               FROM passage_entity pe
               JOIN passage p ON pe.passage_id = p.passage_id
               WHERE pe.entity_id = ?
               ORDER BY p.text_id, p.passage_id
               LIMIT ? OFFSET ?""",
            (entity['entity_id'], page_size, offset)).fetchall()
        passages = []
        translated_count = 0
        for pr in passage_rows:
            pr = dict(pr)
            if pr.get('vi_text'):
                translated_count += 1
            passages.append({
                'passage_id': pr['passage_id'],
                'source': pr['source'],
                'text_id': pr['text_id'],
                'loc_ref': pr['loc_ref'],
                'raw_text': pr['raw_text'],
                'norm_text': pr['norm_text'],
                'vi_text': pr['vi_text'],
                'has_vi': bool(pr['vi_text']),
                'is_translation_draft': bool(pr.get('translation_draft')),
            })

        # 4. LAYER C — metadata tác phẩm (catalog_mapping JOIN canon_catalog bởi cb_cbeta)
        mapping_rows = conn.execute(
            """SELECT catalog_id, source, status, note, quality_flag FROM catalog_mapping
               WHERE place_id = ? ORDER BY status, catalog_id""", (entity['entity_id'],)).fetchall()
        mapping = [dict(r) for r in mapping_rows]
        texts = []
        for cm in mapping_rows:
            cc = conn.execute(
                """SELECT work_id, title_vi, title_zh, author_vi, era_vi, year_start, year_end,
                          cbeta_id, cb_volume, cb_page, source, verified
                   FROM canon_catalog WHERE CAST(cb_cbeta AS TEXT) = ? LIMIT 1""",
                (cm['catalog_id'],)).fetchone()
            if not cc:
                continue
            cc = dict(cc)
            texts.append({
                'catalog_id': cm['catalog_id'],
                'work_id': cc.get('work_id'),
                'title_vi': cc.get('title_vi'),
                'title_zh': cc.get('title_zh'),
                'author_vi': cc.get('author_vi'),
                'era_vi': cc.get('era_vi'),
                'year_start': cc.get('year_start'),
                'year_end': cc.get('year_end'),
                'volume': cc.get('cb_volume'),
                'page': cc.get('cb_page'),
                'source': cc.get('source'),
                'verified': cc.get('verified'),
                'mapping_source': cm['source'],
                'mapping_status': cm['status'],
                'mapping_note': cm['note'],
            })

        has_more = (offset + len(passages)) < total_passages

        return jsonify({
            "success": True,
            "has_data": len(dila_references) > 0 or total_passages > 0 or len(texts) > 0,
            "entity": {
                "id": entity['entity_id'],
                "entity_type": entity.get('entity_type'),
                "name_vi": name_vi,
                "name_zh": entity.get('alias_zh'),
                "alias_vi": entity.get('alias_vi'),
                "alias_zh": entity.get('alias_zh'),
                "extra_alias": entity.get('extra_alias'),
                "aliases": aliases,
                "authority_sources": authority_sources,
                "dila_id": dila_id,
            },
            "summary": {
                "dila_reference_count": len(dila_references),
                "indexed_passage_count": total_passages,
                "text_count": len(texts),
                "translation_count": translated_count,
            },
            "data_status": {
                "has_dila_references": len(dila_references) > 0,
                "has_indexed_passages": total_passages > 0,
                "has_text_metadata": len(texts) > 0,
                "has_translations": translated_count > 0,
            },
            "dila_references": dila_references,
            "passages": {
                "items": passages,
                "total": total_passages,
                "page": page,
                "page_size": page_size,
                "has_more": has_more,
            },
            "texts": texts,
            "mapping": mapping,
        })
    except sqlite3.OperationalError as e:
        return jsonify({"success": False, "has_data": False, "error": f"Table unavailable: {e}"}), 200
    finally:
        conn.close()


# ===== T26: UNIFIED ENTITY ENDPOINT =====

@app.route('/daoanh/api/entity/<entity_id>/unified')
def entity_unified(entity_id):
    """T26: Unified API Response — consolidate all sources for an entity.
    Returns entity + sources[] + claims[] + conflicts[] in one response.
    GET /daoanh/api/entity/<entity_id>/unified
    """
    conn = get_db_connection()
    try:
        # 1. Resolve entity from entity_hub (INTEGER PK)
        hub = conn.execute(
            "SELECT entity_id, canonical_label, entity_type FROM entity_hub WHERE entity_id = ?",
            (entity_id,)
        ).fetchone()

        # Fallback: try entity table (TEXT PK, DILA-centric)
        if not hub:
            ent = conn.execute(
                "SELECT entity_id, alias_zh AS canonical_label, alias_vi AS canonical_name_vi, entity_type FROM entity WHERE entity_id = ?",
                (entity_id,)
            ).fetchone()
            if ent:
                hub = ent

        if not hub:
            return jsonify({"ok": False, "error": "Entity not found"}), 404

        entity = dict(hub)
        # canonical_name = Hán name; canonical_name_vi = Vietnamese name
        entity['canonical_name'] = entity.get('canonical_label')
        # canonical_name_vi: prefer namevi_map_places; fall back to alias_vi from entity table
        vi_name_row = conn.execute(
            "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
            (entity_id,)
        ).fetchone()
        if vi_name_row and vi_name_row['name_vi']:
            entity['canonical_name_vi'] = vi_name_row['name_vi']
        elif 'canonical_name_vi' not in entity:
            entity['canonical_name_vi'] = None
        # CBETA mention count from T51d aggregate table
        try:
            cbeta_stat = conn.execute(
                "SELECT mention_count, top_texts FROM cbeta_place_mention_stats WHERE place_id = ? LIMIT 1",
                (entity_id,)
            ).fetchone()
            entity['cbeta_mention_count'] = cbeta_stat['mention_count'] if cbeta_stat else 0
        except Exception:
            entity['cbeta_mention_count'] = None

        # 2. Resolve source mappings from entity_source_ids
        # entity_source_ids uses INTEGER entity_id (from entity_hub), but entity_id param may be
        # a TEXT DILA ID like 'PL000000023255' → resolve integer hub ID via source_entity_id lookup
        sources = {}
        esi_id_row = conn.execute(
            "SELECT entity_id FROM entity_source_ids WHERE source_entity_id = ? LIMIT 1",
            (entity_id,)
        ).fetchone()
        hub_int_id = esi_id_row['entity_id'] if esi_id_row else entity_id
        source_rows = conn.execute(
            "SELECT source, source_entity_id, confidence, verified FROM entity_source_ids WHERE entity_id = ?",
            (hub_int_id,)
        ).fetchall()
        source_map = {}
        for sr in source_rows:
            source_map[sr['source']] = dict(sr)

        # DILA source — BUG-011 fix: fallback to entity_id for PL* places when entity_source_ids incomplete
        # Primary: entity_source_ids mapping; fallback: entity_id IS the DILA ID for place entities
        _dila_source_id = None
        if 'DILA' in source_map:
            _dila_source_id = source_map['DILA']['source_entity_id']
        elif str(entity_id).startswith('PL'):
            # For place entities, entity_id equals the DILA ID — entity_source_ids may be incomplete
            _dila_source_id = entity_id
        if _dila_source_id:
            dila_id = _dila_source_id
            dila_detail = conn.execute(
                "SELECT name_zh, geo_lat, geo_long, note, district, note_category FROM places_dila WHERE id = ?",
                (dila_id,)
            ).fetchone()
            # Fallback: places_dila uses long DILA IDs (PL000000000001); short IDs (PL056722)
            # only exist in places table — read GPS/name_zh/province from there when places_dila empty
            _places_fb = None
            if not dila_detail:
                _pf = conn.execute(
                    "SELECT name_zh, gps_lat, gps_long, province FROM places WHERE id = ?",
                    (dila_id,)
                ).fetchone()
                if _pf and (_pf['gps_lat'] or _pf['name_zh']):
                    _places_fb = _pf
                    # Secondary fallback: find matching places_dila by GPS (same coords = same site)
                    # Resolves note/district when entity_source_ids has short ID but places_dila uses long ID
                    if _pf['gps_lat'] and _pf['gps_long']:
                        _gps_match = conn.execute(
                            "SELECT name_zh, geo_lat, geo_long, note, district, note_category"
                            " FROM places_dila"
                            " WHERE ABS(geo_lat - ?) < 0.001 AND ABS(geo_long - ?) < 0.001"
                            " LIMIT 1",
                            (_pf['gps_lat'], _pf['gps_long'])
                        ).fetchone()
                        if _gps_match:
                            dila_detail = _gps_match
            vi_detail = conn.execute(
                "SELECT name_vi, country_vi, district_vi, vn_name_status FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
                (dila_id,)
            ).fetchone()
            _district_src = (dila_detail['district'] if dila_detail else None) or (_places_fb['province'] if _places_fb else None)
            parsed = parse_dila_district(_district_src) if _district_src else {}
            # Strip HTML/XML tags from note before sending to frontend
            _raw_note = dila_detail['note'] if dila_detail else None
            if _raw_note:
                _raw_note = re.sub(r'<[^>]+>', ' ', _raw_note)
                _raw_note = re.sub(r'\s+', ' ', _raw_note).strip() or None
            _fb_gps = (f"{_places_fb['gps_lat']},{_places_fb['gps_long']}"
                       if _places_fb and _places_fb['gps_lat'] else None)
            sources['dila'] = {
                "active": True,
                "source_record_id": dila_id,
                "name_zh": (dila_detail['name_zh'] if dila_detail else None) or (_places_fb['name_zh'] if _places_fb else None),
                "name_vi": vi_detail['name_vi'] if vi_detail else None,
                "gps": (f"{dila_detail['geo_lat']},{dila_detail['geo_long']}" if dila_detail and dila_detail['geo_lat'] else None) or _fb_gps,
                "district_raw": _district_src,
                "note": _raw_note,
                "note_category": dila_detail['note_category'] if dila_detail else None,
                "country_vi": (vi_detail['country_vi'] if vi_detail else None) or parsed.get('country_vi'),
                "district_vi": vi_detail['district_vi'] if vi_detail else None,
                "district_vi_computed": parsed.get('district_vi', ''),
                "province": parsed.get('province', ''),
                "vn_name_status": vi_detail['vn_name_status'] if vi_detail else None
            }
        else:
            sources['dila'] = {"active": False}

        # CBETA source
        if 'CBETA' in source_map:
            # Resolve CBETA source_id from data_sources (source_code='CBETA'),
            # fallback 3 — avoid hardcoding the numeric source_id (T69 audit: was 7 = wrong).
            cb_row = conn.execute(
                "SELECT source_id FROM data_sources WHERE source_code = 'CBETA' AND active = 1 LIMIT 1"
            ).fetchone()
            cb_src = cb_row['source_id'] if cb_row else 3
            cbeta_refs = conn.execute(
                "SELECT source_record_id FROM entity_claims WHERE entity_id = ? AND source_id = ? LIMIT 10",
                (entity_id, cb_src)
            ).fetchall()
            sources['cbeta'] = {
                "active": True,
                "refs": [r['source_record_id'] for r in cbeta_refs if r['source_record_id']]
            }
        else:
            sources['cbeta'] = {"active": False, "refs": []}

        # ZQLOCAL source (Vietnamese names)
        if 'ZQLOCAL' in source_map:
            vi_name_row = conn.execute(
                "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? LIMIT 1",
                (source_map['ZQLOCAL']['source_entity_id'],)
            ).fetchone()
            sources['zqlocal'] = {
                "active": True,
                "vi_name": vi_name_row['name_vi'] if vi_name_row else None
            }
        else:
            sources['zqlocal'] = {"active": False}

        # Marcus source
        sources['marcus'] = {"active": "MARCUS" in source_map}

        # Wikidata source (via geo_cross_ref)
        wiki = conn.execute(
            "SELECT wikidata_qid FROM geo_cross_ref WHERE dila_id = ? LIMIT 1",
            (entity_id,)
        ).fetchone()
        sources['wikidata'] = {
            "active": wiki is not None and wiki['wikidata_qid'] is not None,
            "qid": wiki['wikidata_qid'] if wiki else None
        }

        # 84000 source
        e4k = conn.execute(
            "SELECT COUNT(*) as cnt FROM eight_four_thousand_place_map WHERE dila_id = ?",
            (entity_id,)
        ).fetchone()
        sources['84000'] = {"active": e4k is not None and e4k['cnt'] > 0}

        # Kanripo source
        kr = conn.execute(
            "SELECT COUNT(*) as cnt FROM kanripo_place_mapping WHERE dila_id = ?",
            (entity_id,)
        ).fetchone()
        sources['kanripo'] = {"active": kr is not None and kr['cnt'] > 0}

        # SAT source (via sat_crossref table — T35)
        sat = conn.execute(
            "SELECT COUNT(*) as cnt FROM sat_crossref LIMIT 1",
        ).fetchone()
        sources['sat'] = {"active": sat is not None and sat['cnt'] > 0, "note": "SAT Daizōkyō deep-links (21dzk.l.u-tokyo.ac.jp)"}

        # VRI source
        vri = conn.execute(
            "SELECT COUNT(*) as cnt FROM vri_place_mapping WHERE dila_id = ?",
            (entity_id,)
        ).fetchone()
        sources['vri'] = {"active": vri is not None and vri['cnt'] > 0}

        # 3. Get all claims
        claims_rows = conn.execute(
            """SELECT claim_type, subject, predicate, object_text,
                      source_id, source_record_id, authority_role, confidence, verification_status
               FROM entity_claims WHERE entity_id = ?
               ORDER BY confidence DESC""",
            (entity_id,)
        ).fetchall()
        claims = [dict(r) for r in claims_rows]

        # 4. Get conflicts
        try:
            conflict_rows = conn.execute(
                """SELECT conflict_type, source_a, source_b, detail
                   FROM lineage_conflicts_v2 WHERE entity_id = ? LIMIT 10""",
                (entity_id,)
            ).fetchall()
            conflicts = [dict(r) for r in conflict_rows]
        except Exception:
            conflicts = []

        # 5. Get founding data
        founding = None
        try:
            f_row = conn.execute(
                """SELECT year, source, source_ref
                   FROM place_timeline_events
                   WHERE entity_id = ? AND event_type = 'founding'
                   ORDER BY confidence DESC LIMIT 1""",
                (entity_id,)
            ).fetchone()
            if f_row:
                founding = {"year": f_row[0], "source": f_row[1], "source_ref": f_row[2]}
        except Exception:
            pass

        # 6. Assemble unified response
        active_sources = [k for k, v in sources.items() if v.get('active')]

        return jsonify({
            "ok": True,
            "entity": entity,
            "sources": sources,
            "claims": claims,
            "claims_count": len(claims),
            "conflicts": conflicts,
            "conflicts_count": len(conflicts),
            "founding": founding,
            "meta": {
                "generated_at": __import__('datetime').datetime.now().isoformat(),
                "sources_active": active_sources,
                "sources_count": len(active_sources)
            }
        })
    finally:
        conn.close()


# ===== MONK API (Personography) =====

@app.route('/daoanh/api/monk/<monk_id>')
def api_monk_profile(monk_id):
    """
    GET /daoanh/api/monk/<dila_id>
    GET /daoanh/api/monk/<dila_id>?view=tooltip
    Returns full profile or tooltip-view for a monk.
    """
    try:
        view = request.args.get('view', 'full')
        conn = get_db_connection()

        # Try dila_id first, then numeric id
        monk = conn.execute("""
            SELECT * FROM monk_dict
            WHERE (dila_id = ? OR CAST(id AS TEXT) = ?)
              AND status = 'approved'
            LIMIT 1
        """, (monk_id, monk_id)).fetchone()

        if not monk:
            conn.close()
            return jsonify({"ok": False, "error": "Monk not found"}), 404

        monk_data = dict(monk)

        # Fetch all names from index
        names = conn.execute("""
            SELECT lang, name_form, name_type, normalized
            FROM monk_name_index
            WHERE monk_id = ?
            ORDER BY
                CASE name_type WHEN 'official' THEN 0 WHEN 'primary' THEN 1 WHEN 'alias' THEN 2 ELSE 3 END,
                id
        """, (monk['id'],)).fetchall()
        monk_data['names'] = [dict(n) for n in names]

        conn.close()

        if view == 'tooltip':
            return jsonify({
                "ok": True,
                "id": monk_data.get('dila_id') or str(monk_data['id']),
                "han_name": monk_data['han_name'],
                "vn_name": monk_data['vn_name'],
                "pinyin": monk_data['pinyin'],
                "dynasty": monk_data['dynasty'],
                "role_main": monk_data['role_main'],
                "era": monk_data['era'],
            })

        return jsonify({"ok": True, "monk": monk_data})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/monk/search')
def api_monk_search():
    """
    GET /daoanh/api/monk/search?q=<query>&limit=20
    Searches monk_name_index.normalized with prefix match.
    Returns deduplicated monk records joined with monk_dict.
    """
    try:
        q = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        if not q or len(q) < 1:
            return jsonify({"ok": False, "error": "Query too short"}), 400

        conn = get_db_connection()
        q_norm = normalize_text(q)

        rows = conn.execute("""
            SELECT DISTINCT m.id, m.dila_id, m.han_name, m.vn_name, m.pinyin,
                   m.dynasty, m.era, m.role_main, m.biography,
                   mi.lang, mi.name_form, mi.name_type, mi.normalized
            FROM monk_dict m
            JOIN monk_name_index mi ON mi.monk_id = m.id
            WHERE m.status = 'approved'
              AND mi.normalized LIKE ? || '%'
            ORDER BY
                CASE mi.lang WHEN 'zh' THEN 0 WHEN 'vi' THEN 1 WHEN 'pinyin' THEN 2 ELSE 3 END,
                LENGTH(mi.normalized) ASC
            LIMIT ?
        """, (q_norm, limit)).fetchall()

        conn.close()

        # Group by monk
        seen = {}
        for r in rows:
            mid = r['id']
            if mid not in seen:
                seen[mid] = {
                    "id": r['dila_id'] or str(mid),
                    "han_name": r['han_name'],
                    "vn_name": r['vn_name'],
                    "pinyin": r['pinyin'],
                    "dynasty": r['dynasty'],
                    "era": r['era'],
                    "role_main": r['role_main'],
                    "matched_name": r['name_form'],
                    "matched_lang": r['lang'],
                }

        results = list(seen.values())
        return jsonify({
            "ok": True,
            "query": q,
            "count": len(results),
            "results": results,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


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


@app.route('/daoanh/admin/bio-review')
def admin_bio_review_page():
    from flask import send_from_directory
    return send_from_directory(ADMIN_DIR, 'bio-review.html')


@app.route('/daoanh/api/admin/bio-review/stats')
def admin_bio_review_stats():
    try:
        conn = sqlite3.connect(SQLITE_DB)
        c = conn.cursor()
        rows = c.execute(
            "SELECT admin_approved, COUNT(*) FROM person_bio_vi_draft GROUP BY admin_approved"
        ).fetchall()
        counts = {r[0]: r[1] for r in rows}
        groups = c.execute(
            "SELECT source_name, match_type, COUNT(*) as n "
            "FROM person_bio_vi_draft WHERE admin_approved=0 "
            "GROUP BY source_name, match_type ORDER BY n DESC"
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "pending": counts.get(0, 0),
            "approved": counts.get(1, 0),
            "rejected": counts.get(-1, 0),
            "groups": [{"source_name": r[0], "match_type": r[1], "count": r[2]} for r in groups],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/bio-review/list')
def admin_bio_review_list():
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))
    status = request.args.get('status', '0')       # '0'=pending,'1'=approved,'-1'=rejected,'all'
    source = request.args.get('source', '')
    match_type = request.args.get('match_type', '')
    q = request.args.get('q', '').strip()
    try:
        conds = []
        params = []
        if status != 'all':
            conds.append("admin_approved = ?"); params.append(int(status))
        if source:
            conds.append("source_name = ?"); params.append(source)
        if match_type:
            conds.append("match_type = ?"); params.append(match_type)
        if q:
            conds.append("(name_vi LIKE ? OR name_zh LIKE ? OR bio_vi_draft LIKE ?)")
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        conn = sqlite3.connect(SQLITE_DB)
        total = conn.execute(
            f"SELECT COUNT(*) FROM person_bio_vi_draft {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT person_id, name_vi, name_zh, source_name, match_type, "
            f"char_count, admin_approved, admin_note, bio_vi_draft "
            f"FROM person_bio_vi_draft {where} "
            f"ORDER BY char_count DESC LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page]
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True, "total": total, "page": page, "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "items": [
                {"person_id": r[0], "name_vi": r[1], "name_zh": r[2],
                 "source_name": r[3], "match_type": r[4], "char_count": r[5],
                 "admin_approved": r[6], "admin_note": r[7],
                 "bio_preview": (r[8] or '')[:300]}
                for r in rows
            ],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/bio-review/approve', methods=['POST'])
def admin_bio_review_approve():
    body = request.get_json(silent=True) or {}
    person_id = (body.get('person_id') or '').strip()
    bio_override = body.get('bio_override')  # optional edited text
    if not person_id:
        return jsonify({"ok": False, "error": "Thiếu person_id"}), 400
    try:
        conn = sqlite3.connect(SQLITE_DB)
        if bio_override is not None:
            conn.execute(
                "UPDATE person_bio_vi_draft SET bio_vi_draft=?, admin_approved=1, "
                "admin_note='', updated_at=datetime('now') WHERE person_id=?",
                (bio_override.strip(), person_id)
            )
        else:
            conn.execute(
                "UPDATE person_bio_vi_draft SET admin_approved=1, admin_note='', "
                "updated_at=datetime('now') WHERE person_id=?",
                (person_id,)
            )
        conn.commit()
        remaining = conn.execute(
            "SELECT COUNT(*) FROM person_bio_vi_draft WHERE admin_approved=0"
        ).fetchone()[0]
        conn.close()
        return jsonify({"ok": True, "person_id": person_id, "remaining_pending": remaining})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/bio-review/reject', methods=['POST'])
def admin_bio_review_reject():
    body = request.get_json(silent=True) or {}
    person_id = (body.get('person_id') or '').strip()
    note = (body.get('note') or '').strip()
    if not person_id:
        return jsonify({"ok": False, "error": "Thiếu person_id"}), 400
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.execute(
            "UPDATE person_bio_vi_draft SET admin_approved=-1, admin_note=?, "
            "updated_at=datetime('now') WHERE person_id=?",
            (note, person_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "person_id": person_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/daoanh/api/admin/bio-review/bulk-approve', methods=['POST'])
def admin_bio_review_bulk_approve():
    body = request.get_json(silent=True) or {}
    source = body.get('source', '')
    match_type = body.get('match_type', '')
    if not source and not match_type:
        return jsonify({"ok": False, "error": "Cần source hoặc match_type để bulk approve"}), 400
    try:
        conds = ["admin_approved = 0"]
        params = []
        if source:
            conds.append("source_name = ?"); params.append(source)
        if match_type:
            conds.append("match_type = ?"); params.append(match_type)
        where = "WHERE " + " AND ".join(conds)
        conn = sqlite3.connect(SQLITE_DB)
        preview_count = conn.execute(
            f"SELECT COUNT(*) FROM person_bio_vi_draft {where}", params
        ).fetchone()[0]
        conn.execute(
            f"UPDATE person_bio_vi_draft SET admin_approved=1, admin_note='bulk_approve', "
            f"updated_at=datetime('now') {where}", params
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "approved_count": preview_count, "source": source, "match_type": match_type})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ===== PANORAMA (Legacy TTL Dashboard) =====

@app.route('/daoanh/panorama/')
@app.route('/daoanh/home')
def home_page():
    from flask import send_from_directory
    return send_from_directory('static', 'home.html')
def panorama_index():
    return send_from_directory(ADMIN_DIR, 'panorama.html')

# ===== COUNTER FILE PATH =====
COUNTER_FILE = os.path.join(DATA_DIR, 'counter.dat')


# ===== TAM TANG INTEGRATION ROUTES (T34/T37/T38) =====

@app.route('/daoanh/api/places/<place_id>/eight_four_thousand')
def api_places_eight_four_thousand(place_id):
    # GET /daoanh/api/places/<id>/eight_four_thousand - Return 84000 translations mapped to this place
    import re as _re
    try:
        conn = get_db_connection()
        dila_id, name_zh = _resolve_dila_id(conn, place_id)

        # Get 84000 texts mapped to this place via the place_map table
        mapped_texts = []
        place_mappings = conn.execute(
            "SELECT eft.toh, eft.title_en, eft.title_zh, eft.canon_section, eftm.confidence, eftm.source "
            "FROM eight_four_thousand eft "
            "JOIN eight_four_thousand_place_map eftm ON eft.toh = eftm.toh "
            "WHERE eftm.dila_id = ? "
            "ORDER BY eftm.confidence DESC",
            (dila_id,)
        ).fetchall()

        for row in place_mappings:
            toh = row[0]
            title_en = row[1] if row[1] else ""
            title_zh = row[2] if row[2] else ""
            canon_section = row[3] if row[3] else ""
            confidence = row[4] if row[4] is not None else 0.0
            source = row[5] if row[5] else ""

            mapped_texts.append({
                "toh": toh,
                "title_en": title_en,
                "title_zh": title_zh,
                "canon_section": canon_section,
                "confidence": confidence,
                "source": source
            })

        # Also get CBETA cross-references
        cbeta_refs = []
        if mapped_texts:
            seen_refs = set()
            for text in mapped_texts:
                refs = conn.execute(
                    'SELECT DISTINCT place_id, name_zh, name_vi '
                    "FROM cbeta_catalog_place_fuzzy "
                    "WHERE title_zh LIKE ? OR title_vi LIKE ? LIMIT 5",
                    ("%T" + str(text["toh"]) + "%", "%T" + str(text["toh"]) + "%")
                ).fetchall()
                for r in refs:
                    ref_key = (r[0], r[1], r[2])
                    if ref_key not in seen_refs:
                        seen_refs.add(ref_key)
                        cbeta_refs.append({
                            "place_id": r[0],
                            "name_zh": r[1],
                            "name_vi": r[2]
                        })

        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "dila_id": dila_id,
            "mapped_texts": mapped_texts,
            "cbeta_refs": cbeta_refs,
            "total_mapped": len(mapped_texts)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
@app.route('/daoanh/api/places/<place_id>/kanripo')
def api_places_kanripo(place_id):
    """GET /daoanh/api/places/<id>/kanripo - Return Kanripo texts mapped to this place."""
    try:
        conn = get_db_connection()
        place_mappings = conn.execute(
            """SELECT vm.text_id, vm.dila_id, vm.confidence, vc.title_zh, vc.category, vc.title_en
            FROM kanripo_place_mapping vm
            JOIN kanripo_catalog vc ON vm.text_id = vc.text_id
            WHERE vm.dila_id = ?
            ORDER BY vm.confidence DESC""",
            (place_id,)
        ).fetchall()
        mapped_texts = []
        for row in place_mappings:
            # Indices: 0=vm.text_id, 1=vm.dila_id, 2=vm.confidence, 3=vc.title_zh, 4=vc.category
            mapped_texts.append({
                "text_id": row[0],
                "title_zh": row[3] if len(row) > 3 else "",
                "category": row[4] if len(row) > 4 else "",
                "confidence": row[2] if len(row) > 2 else 0.8
            })
        # Get cached texts
        cached_texts = conn.execute(
            """SELECT text_id, title_zh FROM kanripo_catalog
            WHERE text_id IN (SELECT text_id FROM kanripo_place_mapping)
            LIMIT 5""",
            ()
        ).fetchall()
        conn.close()
        return jsonify({
            "ok": True,
            "place_id": place_id,
            "mapped_texts": mapped_texts,
            "cached_texts": [{"text_id": r[0], "title_zh": r[1]} for r in cached_texts],
            "total_mapped": len(mapped_texts)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/daoanh/api/places/<place_id>/vri')
def api_places_vri(place_id):
    """GET /daoanh/api/places/<id>/vri - Return VRI Tipitaka texts mapped to this place."""
    import re as _re
    try:
        conn = get_db_connection()

        # Get VRI place mappings for this place_id
        place_mappings = conn.execute(
            """SELECT vpm.*, vtc.nikaya, vtc.title_pali, vtc.reference, vtc.word_count
            FROM vri_place_mapping vpm
            JOIN vri_tipitaka_catalog vtc ON vpm.vri_sutta_id = vtc.id
            WHERE vpm.dila_id = ?
            ORDER BY vpm.confidence DESC""",
            (place_id,)
        ).fetchall()

        mapped_texts = []
        for row in place_mappings:
            mapped_texts.append({
                "nikaya": row[1],
                "sutta_id": row[3] if len(row) > 3 else row[0],
                "title_pali": row[4] if len(row) > 4 else "",
                "title_vi": row[5] if len(row) > 5 else "",
                "title_zh": row[6] if len(row) > 6 else "",
                "reference": row[7] if len(row) > 7 else "",
                "place_name_pali": row[8] if len(row) > 8 else "",
                "context": row[9] if len(row) > 9 else "",
                "confidence": row[10] if len(row) > 10 else 0.8
            })

        # Also get cached text excerpts
        cached_texts = conn.execute(
            """SELECT vct.paragraph_id, vct.text_pali, vct.text_vi, vct.text_zh
            FROM vri_cached_texts vct
            WHERE vct.sutta_id IN (SELECT id FROM vri_tipitaka_catalog)
            LIMIT 5""",
            ()
        ).fetchall()

        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "mapped_texts": mapped_texts,
            "cached_texts": [{"paragraph": r[0], "pali": r[1], "vi": r[2], "zh": r[3]} for r in cached_texts],
            "total_mapped": len(mapped_texts)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# T37 — Pali Place Reference
@app.route('/daoanh/api/places/<place_id>/pali')
def api_places_pali(place_id):
    """GET /daoanh/api/places/<id>/pali - Pali/Sanskrit references for Indian sacred sites."""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT dila_id, name_zh, name_vi, name_pali, name_skt,
                      sc_uid, sc_uids_more, sc_note_vi, confidence
               FROM pali_place_ref
               WHERE dila_id = ?
               ORDER BY confidence DESC""",
            (place_id,)
        ).fetchall()
        conn.close()

        if not rows:
            return jsonify({"ok": True, "place_id": place_id, "refs": [], "total": 0})

        refs = []
        for r in rows:
            sc_uid = r[5]
            refs.append({
                "dila_id": r[0],
                "name_zh": r[1],
                "name_vi": r[2],
                "name_pali": r[3],
                "name_skt": r[4],
                "sc_uid": sc_uid,
                "sc_uids_more": r[6],
                "sc_note_vi": r[7],
                "confidence": r[8],
                "sc_url_vi": f"https://suttacentral.net/{sc_uid}/vi/minh_chau" if sc_uid else None,
                "sc_url_en": f"https://suttacentral.net/{sc_uid}" if sc_uid else None,
            })

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "refs": refs,
            "total": len(refs)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# T100-P0 — Evidence drawer (read-only) cho 1 subject (person/place).
# Tổng hợp bằng chứng: events + event_evidence, entity_claims qua entity_hub, co-mention.
# Không ghi DB. data_status giúp UI đánh dấu mức kiểm chứng TRUNG THỰC theo T100
# (Cử nhân ≥6/12, Cao học ≥9/12, Tiến sĩ 12/12 — bằng chứng = code + DB thật).
@app.route('/daoanh/api/evidence/<subject_id>')
def api_evidence(subject_id):
    """GET /daoanh/api/evidence/<subject_id> — bằng chứng cho 1 subject (read-only).

    Trả về:
      events      — events JOIN event_entities (gắn subject) + event_evidence kèm theo
      claims      — entity_claims theo entity_hub (NETWORK/TEXT/COORDINATE/NAME...)
      co_mentions — event_text_link (đồng xuất hiện trong passage CBETA — KHÔNG suy quan hệ, T97)
      data_status — số liệu tổng hợp để UI hiển thị mức kiểm chứng trung thực
    Tham số ?level=L1|L2|L3 (T111 persona): L1 server-side clip claims về 'verified' (bổ túc UI).
    """
    try:
        level = (request.args.get('level') or '').upper()
        if level not in ('L1', 'L2', 'L3'):
            level = 'L2'
        conn = get_db_connection()
        eid, ref = _resolve_entity_id(conn, subject_id)

        # (1) events + event_evidence
        events = []
        ev_rows = conn.execute("""
            SELECT e.event_id, e.event_type, e.title_zh, e.title_vi, e.start_year,
                   e.end_year, e.precision, e.review_status, e.confidence
            FROM events e JOIN event_entities en ON en.event_id = e.event_id
            WHERE en.entity_id = ?
            ORDER BY e.start_year NULLS LAST
            LIMIT 200
        """, (subject_id,)).fetchall()
        for e in ev_rows:
            evid = [dict(zip(("source_record", "source_ref", "evidence_type", "exact_span"), x))
                    for x in conn.execute(
                        "SELECT source_record, source_ref, evidence_type, exact_span "
                        "FROM event_evidence WHERE event_id = ? LIMIT 8", (e["event_id"],)).fetchall()]
            events.append({
                "event_id": e["event_id"], "event_type": e["event_type"],
                "title_zh": e["title_zh"], "title_vi": e["title_vi"],
                "start_year": e["start_year"], "end_year": e["end_year"],
                "precision": e["precision"], "review_status": e["review_status"],
                "confidence": e["confidence"], "evidence": evid
            })

        # (2) entity_claims qua entity_hub (nếu resolve được INT entity_id)
        claims = []
        claim_stats = {"total": 0, "by_type": {}, "verification": {}}
        if eid is not None:
            # T100-P2 (Batch 4): đọc assertion_level nếu cột đã có (ETL applied) — additive.
            has_assert = 'assertion_level' in {r[1] for r in conn.execute('PRAGMA table_info(entity_claims)')}
            assert_col = 'c.assertion_level, ' if has_assert else ''
            claim_cols = ('c.claim_id, c.claim_type, c.predicate, c.object_text, '
                          'c.source_reference, c.confidence, c.verification_status, '
                          + assert_col
                          + "COALESCE(d.source_code, '') AS source_code")
            claim_rows = conn.execute(
                "SELECT " + claim_cols + """
                FROM entity_claims c LEFT JOIN data_sources d ON d.source_id = c.source_id
                WHERE c.entity_id = ?
                ORDER BY c.claim_type, c.claim_id
                LIMIT 200
            """, (eid,)).fetchall()
            for c in claim_rows:
                claims.append({
                    "claim_id": c["claim_id"], "claim_type": c["claim_type"],
                    "predicate": c["predicate"], "object_text": c["object_text"],
                    "source_reference": c["source_reference"], "confidence": c["confidence"],
                    "verification_status": c["verification_status"], "source_code": c["source_code"],
                    "assertion_level": (c["assertion_level"] if has_assert else None)
                })
            for (ct, n) in conn.execute(
                    "SELECT claim_type, COUNT(*) FROM entity_claims WHERE entity_id=? GROUP BY claim_type",
                    (eid,)):
                claim_stats["by_type"][ct] = n
            for (vs, n) in conn.execute(
                    "SELECT verification_status, COUNT(*) FROM entity_claims "
                    "WHERE entity_id=? GROUP BY verification_status", (eid,)):
                claim_stats["verification"][vs] = n
            claim_stats["total"] = sum(claim_stats["by_type"].values())
            # T111 persona: L1 = chỉ claim đã xét duyệt 'verified' (bổ túc UI-side gating).
            if level == 'L1':
                claims = [c for c in claims
                          if (c.get('verification_status') or '') == 'verified']

        # (3) co-mention (event_text_link) — đồng xuất hiện trong passage CBETA
        co_rows = conn.execute("""
            SELECT cbeta_ref, source_book, source_ref, year, confidence, related_id, related_name
            FROM event_text_link
            WHERE entity_id = ? OR related_id = ?
            ORDER BY cbeta_ref
            LIMIT 300
        """, (subject_id, subject_id)).fetchall()
        co_mentions = [dict(r) for r in co_rows]
        conn.close()

        reviewed = sum(1 for e in events if e["review_status"] not in ("candidate", "draft", None))
        claims_note = (
            "Không tìm thấy claim cho subject này (toàn kho entity_claims 447,885 claim "
            "vẫn 100% 'unverified' — 2026-09-07)."
            if not claims else
            (f"{claim_stats['total']} claim cho subject này — 100% 'unverified' theo toàn kho "
             "(447,885 claim), đối chiếu thủ công theo batch mới nâng cấp.")
        )

        return jsonify({
            "ok": True,
            "subject_id": subject_id,
            "persona_level": level,
            "resolved": {"entity_hub_id": eid, "canonical": ref},
            "events": events,
            "claims": claims,
            "co_mentions": co_mentions,
            "data_status": {
                "events": {
                    "total": len(events),
                    "reviewed": reviewed,
                    "rejected": sum(1 for e in events if e["review_status"] == "rejected")
                },
                "claims": claim_stats,
                "co_mentions": {
                    "total": len(co_mentions),
                    "distinct_texts": len({c["cbeta_ref"] for c in co_mentions if c["cbeta_ref"]})
                },
                "notes": {
                    "events": "3,530 event toàn kho — 100% review_status 'candidate' (chưa duyệt).",
                    "claims": claims_note,
                    "co_mentions": "co-mention = đồng xuất hiện trong passage CBETA; KHÔNG suy ra quan hệ (T97)."
                }
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# TGS Build 2 — Phase C: Evidence claims endpoint (đa-nguồn, kèm authority + provenance)
@app.route('/daoanh/api/places/<place_id>/claims')
def api_places_claims(place_id):
    """GET /daoanh/api/places/<id>/claims — evidence đa-nguồn cho 1 địa danh.

    Trả về các claim trong entity_claims JOIN data_sources + source_authority,
    kèm source_url / retrieved_at (provenance từ Phase B), xung đột chưa resolve
    (conflict_pending), và bảng xếp hạng authority để UI hiển thị.
    """
    try:
        conn = get_db_connection()

        # Resolve place_id ('PL…' hoặc integer) → entity_id (INT) trong entity_claims
        eid, ref = _resolve_entity_id(conn, place_id)

        # Authority map (source_code → score/order/implemented) để UI xếp hạng
        authority_map = {}
        for r in conn.execute(
            "SELECT source_code, authority_score, precedence_order, implemented FROM source_authority"
        ):
            authority_map[r['source_code']] = {
                'score': r['authority_score'], 'order': r['precedence_order'] or 99,
                'implemented': r['implemented'],
            }

        claims = []
        if eid is not None:
            rows = conn.execute(
                """SELECT c.claim_id, c.claim_type, c.subject, c.predicate, c.object_text,
                          c.source_record_id, c.source_reference,
                          c.authority_role, c.confidence, c.verification_status,
                          c.source_url, c.retrieved_at,
                          d.source_code, d.source_name,
                          sa.authority_score, sa.precedence_order, sa.implemented
                   FROM entity_claims c
                   LEFT JOIN data_sources d      ON d.source_id = c.source_id
                   LEFT JOIN source_authority sa ON sa.source_code = d.source_code
                   WHERE c.entity_id = ?
                   ORDER BY sa.authority_score DESC NULLS LAST, c.confidence DESC""",
                (eid,)
            ).fetchall()
            for r in rows:
                claims.append({
                    "claim_id": r[0],
                    "claim_type": r[1],
                    "subject": r[2],
                    "predicate": r[3],
                    "object_text": r[4],
                    "source_record_id": r[5],
                    "source_reference": r[6],
                    "authority_role": r[7],
                    "confidence": r[8],
                    "verification_status": r[9],
                    "source_url": r[10],
                    "retrieved_at": r[11],
                    "source": {
                        "code": r[12],
                        "name": r[13],
                        "authority_score": r[14],
                        "precedence_order": r[15],
                        "implemented": r[16],
                    },
                })
        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "resolved_entity_id": eid,
            "claims": claims,
            "claims_count": len(claims),
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# T100-P2 (Batch 4) — GIÁO LÝ PHÂN ĐÔI: khối "Giáo lý Phật học".
# Route read-only cho khối giáo lý: khái niệm từ doctrine_concept (whitelist, THEMATIC)
# + claims liên quan (entity_claims, badge assertion_level DIRECT/THEMATIC/SCHOLARLY).
# Bảng mới seed qua scripts/etl_t100_batch4.py (additive — CHẠY ETL TRƯỚC).
@app.route('/daoanh/api/places/<place_id>/doctrine')
def api_places_doctrine(place_id):
    """GET /daoanh/api/places/<id>/doctrine — giáo lý Phật học (khối 1 tab GIÁO LÝ).

    Trả về:
      concepts       — doctrine_concept (whitelist 12 khái niệm core, assertion_level THEMATIC)
      related_claims — entity_claims của subject (kèm assertion_level/verification_status/source_code)
      data_status    — số liệu để UI hiển thị trung thực (0/unseeded → empty-state)
    KHÔNG ghi DB. 404 nếu place không resolve. Fallback trống khi bảng doctrine_concept chưa seed.
    Tham số ?level=L1|L2|L3 (T111 persona): L1 server-side clip claims về 'verified' (bổ túc UI).
    """
    try:
        level = (request.args.get('level') or '').upper()
        if level not in ('L1', 'L2', 'L3'):
            level = 'L2'
        conn = get_db_connection()

        # (1) whitelist khái niệm giáo lý — chủ đề truy vấn (không phụ thuộc entity)
        concepts = []
        try:
            has_doctrine = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='doctrine_concept'"
            ).fetchone()
            if has_doctrine:
                for r in conn.execute(
                    "SELECT name_vi, name_zh, pth_uri, definition_vi, assertion_level, "
                    "related_entities, updated_at FROM doctrine_concept "
                    "WHERE name_vi IS NOT NULL ORDER BY id"
                ):
                    concepts.append({
                        "name_vi": r["name_vi"], "name_zh": r["name_zh"] or "",
                        "pth_uri": r["pth_uri"] or "", "definition_vi": r["definition_vi"] or "",
                        "assertion_level": r["assertion_level"] or "THEMATIC",
                        "related_entities": (r["related_entities"] or "").split(','),
                        "updated_at": r["updated_at"] or "",
                    })
        except Exception:
            concepts = []

        # (2) claims liên quan của subject (cùng pattern api_places_claims)
        eid, ref = _resolve_entity_id(conn, place_id)
        related_claims = []
        if eid is not None:
            try:
                rows = conn.execute(
                    """SELECT c.claim_id, c.claim_type, c.subject, c.predicate, c.object_text,
                              c.source_reference, c.authority_role, c.confidence,
                              c.verification_status, c.assertion_level,
                              d.source_code, d.source_name
                       FROM entity_claims c
                       LEFT JOIN data_sources d ON d.source_id = c.source_id
                       WHERE c.entity_id = ?
                       ORDER BY CASE c.assertion_level WHEN 'DIRECT' THEN 0
                                    WHEN 'THEMATIC' THEN 1 WHEN 'SCHOLARLY' THEN 2 ELSE 3 END,
                                c.claim_type, c.claim_id
                       LIMIT 100""",
                    (eid,)
                ).fetchall()
            except Exception:
                rows = []
            for r in rows:
                related_claims.append({
                    "claim_id": r["claim_id"], "claim_type": r["claim_type"],
                    "subject": r["subject"], "predicate": r["predicate"],
                    "object_text": r["object_text"], "source_reference": r["source_reference"],
                    "authority_role": r["authority_role"], "confidence": r["confidence"],
                    "verification_status": r["verification_status"],
                    "assertion_level": r["assertion_level"] or None,
                    "source_code": r["source_code"] or "",
                    "source_name": r["source_name"] or "",
                })
        # T111 persona: L1 = chỉ claim đã xét duyệt 'verified' (bổ túc UI-side gating).
        if level == 'L1':
            related_claims = [c for c in related_claims
                              if (c.get('verification_status') or '') == 'verified']
        conn.close()

        return jsonify({
            "ok": True,
            "place_id": place_id,
            "resolved_entity_id": eid,
            "persona_level": level,
            "concepts": concepts,
            "related_claims": related_claims,
            "data_status": {
                "concepts": {
                    "total": len(concepts),
                    "level": "whitelist doctrine_concept ('THEMATIC')",
                },
                "related_claims": {
                    "total": len(related_claims),
                    "by_level": {
                        lvl: sum(1 for c in related_claims if c["assertion_level"] == lvl)
                        for lvl in ("DIRECT", "THEMATIC", "SCHOLARLY")
                    },
                    "note": ("entity_claims toàn kho 447,885 claim — 100% 'unverified'; "
                             "assertion_level chưa gán khi claim chưa qua xét duyệt (P3)."),
                },
            },
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


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


@app.route('/daoanh/api/glossary')
def api_glossary():
    """GET /daoanh/api/glossary?term=<hanzi|pali|sanskrit|vi|tib>

    T57a — Tra cứu glossary đa ngôn:
      1) `lexicon` (22 từ điển PG VN — gồm bản dịch Việt DPPN) — nguồn Việt chính.
      2) `glossary_term` (Yokoyama 1996, San–Tib–Chi; MB_GLOSSARY CC0).
      3) `term_glossaries` (Marcus reference).

    Mỗi kết quả ghi rõ `source_label` để tránh gán nhầm nguồn.
    """
    term = (request.args.get('term') or '').strip()
    if not term:
        return jsonify({"ok": False, "error": "Thiếu tham số term."}), 400

    try:
        conn = get_db_connection()
        matches = []

        # 1) Lexicon (Hán–Việt 22 từ điển PG VN). Ưu tiên khớp chính xác term, fallback normalized.
        lex = conn.execute(
            """SELECT term, definition, source FROM lexicon
               WHERE term = ? ORDER BY priority ASC, id ASC LIMIT 5""",
            (term,)
        ).fetchall()
        if not lex:
            n = normalize_text(term)
            lex = conn.execute(
                """SELECT term, definition, source FROM lexicon
                   WHERE normalized = ? ORDER BY priority ASC, id ASC LIMIT 5""",
                (n,)
            ).fetchall()
        for r in lex:
            matches.append({
                "term": r['term'],
                "definition": r['definition'],
                "language": "vi",
                "source_key": "lexicon",
                "source_label": f"Từ điển PG VN ({r['source'] or '22 từ điển'})",
            })

        # 2) Glossary Yokoyama (San–Tib–Chi) — tra theo term thuần (không remove dấu —
        #    tiếng Phạn/Tạng nhạy dấu). Chỉ khớp chính xác. T110: ghép term_vi (glossary_vi).
        _ensure_glossary_term_table(conn)
        yoko = conn.execute(
            """SELECT g.term, g.language, g.definition, g.full_text,
                      v.term_vi, v.match_type, v.match_source
               FROM glossary_term g
               LEFT JOIN glossary_vi v ON v.glossary_id = g.id
               WHERE g.term = ? ORDER BY g.language LIMIT 10""",
            (term,)
        ).fetchall()
        # T110: chưa khớp thuật ngữ gốc → thử tra bằng NGHĨA TIẾNG VIỆT (term_vi) —
        #    Tăng Ni gõ tiếng Việt vẫn tìm ra được mục glossary gốc.
        if not yoko:
            yoko = conn.execute(
                """SELECT g.term, g.language, g.definition, g.full_text,
                          v.term_vi, v.match_type, v.match_source
                   FROM glossary_term g
                   JOIN glossary_vi v ON v.glossary_id = g.id
                   WHERE g.language='zho' AND (v.term_vi = ? OR v.term_vi LIKE ?)
                   ORDER BY CASE WHEN v.term_vi = ? THEN 0 ELSE 1 END, g.term LIMIT 10""",
                (term, term + '%', term)
            ).fetchall()
        lang_names = {'san': 'Sanskrit', 'zho': 'Hán', 'bod': 'Tạng (Unicode)', 'bo-Latn': 'Tạng (Latin)'}
        for r in yoko:
            item = {
                "term": r['term'],
                "definition": r['definition'],
                "language": r['language'],
                "language_name": lang_names.get(r['language'], r['language']),
                "full_text": r['full_text'],
                "source_key": "yokoyama",
                "source_label": "Yokoyama 1996 — Sanskrit–Tibetan–Chinese gloss. (CC0)",
            }
            if r['term_vi']:
                item["term_vi"] = r['term_vi']
                item["vi_match_type"] = r['match_type']
                item["vi_source"] = {'doctrine_concept': 'Giáo lý cốt lõi',
                                     'vi_buddhist_json': 'Style-lock VI',
                                     'lexicon': 'Từ điển PG VN (Vạn Hạnh)',
                                     'namevi_map_places': 'Địa danh',
                                     'name_vi_map': 'Nhân danh',
                                     'char_hv': 'Âm Hán-Việt từng ký tự',
                                     }.get(r['match_source'], r['match_source'])
            matches.append(item)

        # 3) Marcus term_glossaries (reference person/works)
        mg = conn.execute(
            """SELECT term, term_zh, term_vi, source FROM term_glossaries
               WHERE term = ? OR term_zh = ? OR term_vi = ? LIMIT 5""",
            (term, term, term)
        ).fetchall()
        for r in mg:
            matches.append({
                "term": r['term_zh'] or r['term'],
                "definition": r['term_vi'],
                "language": "vi",
                "source_key": "marcus",
                "source_label": f"Marcus SNA ({r['source'] or 'Marcus_fojin'})",
            })

        conn.close()
        return jsonify({"ok": True, "term": term, "matches": matches, "total": len(matches)})
    except Exception as e:
        app.logger.error(f"api_glossary error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# T38 — Toh-CBETA Crossref badge
@app.route('/daoanh/api/cbeta/<sigla>/toh')
def api_cbeta_toh(sigla):
    """GET /daoanh/api/cbeta/<sigla>/toh - Tibetan canon (Toh) crossref for a CBETA text."""
    try:
        conn = get_db_connection()
        rows = conn.execute(
            """SELECT toh, cbeta_sigla, title_zh, title_vi, title_en,
                      url_84000, canon_section, note_vi, confidence
               FROM toh_cbeta_crossref
               WHERE cbeta_sigla = ? AND needs_review = 0
               ORDER BY confidence DESC""",
            (sigla.upper(),)
        ).fetchall()
        conn.close()

        if not rows:
            return jsonify({"ok": True, "sigla": sigla, "toh_refs": [], "total": 0})

        toh_refs = []
        for r in rows:
            toh_refs.append({
                "toh": r[0],
                "cbeta_sigla": r[1],
                "title_zh": r[2],
                "title_vi": r[3],
                "title_en": r[4],
                "url_84000": r[5],
                "canon_section": r[6],
                "note_vi": r[7],
                "confidence": r[8],
                "badge_label": f"Tạng Truyền: Toh {r[0]}",
            })

        return jsonify({
            "ok": True,
            "sigla": sigla,
            "toh_refs": toh_refs,
            "total": len(toh_refs)
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


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

@app.route('/daoanh/api/cbeta/<sigla>/parallels')
def api_cbeta_parallels(sigla):
    """GET /daoanh/api/cbeta/<sigla>/parallels - DharmaNexus parallel passages link + metadata."""
    import os as _os, json as _json, time as _time
    try:
        sigla_upper = sigla.upper()
        cache_dir = _os.path.join(_os.path.dirname(__file__), 'data', 'cache')
        _os.makedirs(cache_dir, exist_ok=True)
        cache_path = _os.path.join(cache_dir, f'dharmanexus_{sigla_upper}.json')

        # Check 24h cache
        if _os.path.exists(cache_path):
            age = _time.time() - _os.path.getmtime(cache_path)
            if age < 86400:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached = _json.load(f)
                cached['from_cache'] = True
                return jsonify(cached)

        # Resolve DharmaNexus ID
        dn_id = _DN_SIGLA_MAP.get(sigla_upper)

        # If not in static map, try to infer from menudata
        if not dn_id:
            try:
                import requests as _req
                menu_r = _req.get(
                    'https://dharmamitra.org/api-db/menudata/?language=zh',
                    timeout=8, headers={'Accept': 'application/json'}
                )
                if menu_r.status_code == 200:
                    menudata = menu_r.json().get('menudata', [])
                    sigla_num = sigla_upper.lstrip('T')  # '0251'
                    # menudata: [{collection, categories: [{category, texts: [{filename,...}]}]}]
                    for section in menudata:
                        for cat in section.get('categories', []):
                            for text in cat.get('texts', []):
                                fname = text.get('filename', '')
                                if fname.endswith(f'_{sigla_num}'):
                                    dn_id = fname
                                    break
                            if dn_id:
                                break
                        if dn_id:
                            break
            except Exception:
                pass

        if not dn_id:
            result = {
                "ok": True,
                "sigla": sigla_upper,
                "dharmanexus_id": None,
                "dharmanexus_url": None,
                "metadata": None,
                "note": "Text không có trong DharmaNexus database (có thể là Luận/Truyện Trung Hoa thuần túy, không có parallel trong Tạng ngữ/Pali)",
                "total_parallels": 0
            }
            return jsonify(result)

        dn_url = f"https://dharmamitra.org/nexus/db/zh/{dn_id}/text"

        # Fetch metadata from DharmaNexus
        metadata_raw = None
        try:
            import requests as _req
            meta_r = _req.get(
                f'https://dharmamitra.org/api-db/utils/raw-metadata/?filename={dn_id}',
                timeout=8, headers={'Accept': 'application/json'}
            )
            if meta_r.status_code == 200:
                metadata_raw = meta_r.json().get('raw_metadata') or None
                # raw_metadata may itself be a dict if API wraps it
                if isinstance(metadata_raw, dict):
                    metadata_raw = metadata_raw.get('raw_metadata')
        except Exception:
            pass

        result = {
            "ok": True,
            "sigla": sigla_upper,
            "dharmanexus_id": dn_id,
            "dharmanexus_url": dn_url,
            "metadata_md": metadata_raw,
            "badge_label": "Xem trên DharmaNexus",
            "note_vi": "DharmaNexus (dharmamitra.org) phân tích text-reuse xuyên suốt Hán Tạng, Pali, Tây Tạng, Sanskrit. Nhấp để khám phá các đoạn kinh tương đồng.",
            "from_cache": False
        }

        # Save to cache
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                _json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/daoanh/api/cbeta/<sigla>/sat')
def api_cbeta_sat(sigla):
    """GET /daoanh/api/cbeta/<sigla>/sat — SAT Daizōkyō cross-reference link (T35)."""
    try:
        conn = get_db_connection()
        sigla_upper = sigla.strip().upper()
        # Normalize: numeric string → T{n:04d}
        if sigla_upper.isdigit():
            sigla_upper = f"T{int(sigla_upper):04d}"
        row = conn.execute(
            "SELECT cbeta_sigla, sat_url, has_unique FROM sat_crossref WHERE cbeta_sigla = ? LIMIT 1",
            (sigla_upper,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({
                "ok": True, "sigla": sigla, "found": False,
                "note_vi": "Không tìm thấy link SAT cho kinh này (có thể là X-series hoặc sh_number không hợp lệ)",
            })
        return jsonify({
            "ok": True, "sigla": sigla,
            "cbeta_sigla": row['cbeta_sigla'],
            "sat_url": row['sat_url'],
            "has_unique": bool(row['has_unique']),
            "badge_label": "Xem trên SAT Daizōkyō",
            "note_vi": "SAT Daizōkyō Text Database (21dzk.l.u-tokyo.ac.jp) — phiên bản Kanji Unicode chuẩn JIS của Đại Chính Tạng, do Đại học Tokyo duy trì.",
            "found": True,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


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


app.route('/daoanh/api/cbeta/<sigla>/compare', methods=['GET'])(api_cbeta_compare)


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
    """Lấy danh sách rules đang active, sắp xếp theo priority."""
    rows = conn.execute(
        "SELECT rule_code, rule_type, rule_text, priority FROM translation_rules "
        "WHERE is_active=1 ORDER BY priority ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def _t73_rules_version(rules):
    """SHA256 của toàn bộ rule_text (theo thứ tự priority) → rules_version."""
    combined = "\n---\n".join(r['rule_text'] for r in rules)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


def _t73_source_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:24]


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


def _t73_style_lock(conn, labels=None, max_glossary=120, max_exemplar=3):
    """T123 — Lấy Style Constitution từ DB: rules active + glossary lock + exemplar.
    Trả dict: {rules, rules_version, glossary[], exemplar[]}.
    Glossary/exemplar ưu tiên mẫu is_locked/is_active, giới hạn độ dài để prompt không quá tải."""
    rules = _t73_get_active_rules(conn)
    rv = _t73_rules_version(rules)
    glossary, exemplar = [], []
    try:
        glossary = [dict(r) for r in conn.execute(
            "SELECT term_zh, term_vi FROM translation_glossary "
            "WHERE is_locked=1 ORDER BY id LIMIT ?", (max_glossary,)
        ).fetchall()]
    except Exception:
        glossary = []
    try:
        exemplar = [dict(r) for r in conn.execute(
            "SELECT zh, vi, source_label FROM translation_exemplar "
            "WHERE is_active=1 ORDER BY length_zh LIMIT ?", (max_exemplar,)
        ).fetchall()]
    except Exception:
        exemplar = []
    return {'rules': rules, 'rules_version': rv,
            'glossary': glossary, 'exemplar': exemplar}


def _t73_build_style_prompt(content, lock, label='văn bản', json_mode=False):
    """T123 — Unified Style-Lock prompt cho MỌI luồng dịch Groq.

    Khung 4 lớp:
      system  = persona Ban Dịch PTDA + Style Constitution (18 rules active)
      user    = GLOSSARY LOCK + FEW-SHOT exemplar + nguyên bản + yêu cầu output
    Trả về prompt chuỗi dùng chung (system+user gộp 1 message role=user giống
    phần lớn caller hiện tại). Nếu json_mode=True → yêu cầu trả JSON
    {"translation_vi": "..."} (dùng cho T85 segments)."""
    rule_block = "\n".join(f"{i+1}. [{r['rule_type'].upper()}] {r['rule_text']}"
                           for i, r in enumerate(lock['rules']))
    glossary_block = "\n".join(f"  - {g['term_zh']} → {g['term_vi']}"
                               for g in lock['glossary']) or "  (không có)"
    exemplar_block = ""
    for i, ex in enumerate(lock['exemplar'], 1):
        exemplar_block += (
            f"\n--- MẪU {i} (theo {ex['source_label']}) ---\n"
            f"Hán: {ex['zh']}\nViệt: {ex['vi']}\n"
        )
    persona = (
        "Bạn là thành viên Ban Dịch PTDA — dịch giả Hán-Việt chuyên ngành Phật học, "
        "kế thừa tinh thần các dịch giả và từ điển Phật học danh tiếng. "
        "Dịch đoạn {label} Hán văn dưới đây sang tiếng Việt theo ĐÚNG mọi quy tắc bắt buộc."
    ).format(label=label)
    how = ("Trả về JSON duy nhất: {\"translation_vi\": \"...\"}, không kèm nội dung khác."
           if json_mode else
           "Chỉ trả về bản dịch thuần tiếng Việt, không giải thích, không ghi chú trong ngoặc, "
           "không lặp lại chữ Hán. Giữ cấu trúc đoạn văn của bản gốc.")
    return (
        f"{persona}\n\n"
        f"=== QUY TẮC DỊCH BẮT BUỘC (Style Constitution) ===\n{rule_block}\n\n"
        f"=== GLOSSARY LOCK (thuật ngữ bắt buộc, ưu tiên cao nhất) ===\n{glossary_block}\n"
        f"=== FEW-SHOT MẪU PHONG CÁCH (học theo tiền bối danh tác) ===\n{exemplar_block or '  (không có'}\n"
        f"=== NGUYÊN BẢN HÁN VĂN ===\n{content}\n\n"
        f"=== BẢN DỊCH TIẾNG VIỆT / YÊU CẦU ===\n{how}"
    )


def _t73_call_gemini(prompt):
    """Gọi Groq LLM, trả về (text, model_id, error_type).
    error_type: None=ok, 'key_error'=401/403, 'rate_limit'=429, 'api_error'=other.
    """
    cfg = _llm_config_read()
    key = cfg.get('groq_key') or GROQ_KEY
    model = cfg.get('groq_model') or GROQ_MODEL
    if not key:
        _llm_config_write({'status': 'key_error',
                           'last_error': 'Thiếu GROQ_API_KEY env hoặc groq_key trong llm_config',
                           'last_error_at': datetime.now().isoformat()})
        return None, model, 'key_error'
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
            _llm_config_write({'status': 'rate_limit',
                               'last_error': 'Rate limit / quota exceeded',
                               'last_error_at': datetime.now().isoformat()})
            return None, None, 'rate_limit'
        data = resp.json()
        if data.get('choices'):
            text = data['choices'][0]['message']['content'].strip()
            _llm_config_write({'status': 'ok', 'last_error': None})
            return text, model, None
        err = str(data.get('error', 'Unknown'))[:200]
        _llm_config_write({'status': 'api_error', 'last_error': err,
                           'last_error_at': datetime.now().isoformat()})
        return None, None, 'api_error'
    except Exception as e:
        app.logger.warning(f"[T73] Groq error: {e}")
        return None, None, 'api_error'


@app.route('/daoanh/api/persons/<person_id>')
def api_person_by_id(person_id):
    """GET /daoanh/api/persons/<person_id> — Profile nhân vật DILA.
    Trả về bio_zh (gốc) + bio_vi từ translation_cache nếu đã có (status != invalidated).
    """
    conn = get_db_connection()
    try:
        p = conn.execute(
            "SELECT id, name_zh, name_vi, name_en, sect, dynasty, birth_year, death_year, bio "
            "FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "person not found"}), 404

        result = {
            "id": p['id'], "name_zh": p['name_zh'], "name_vi": p['name_vi'],
            "name_en": p['name_en'], "sect": p['sect'], "dynasty": p['dynasty'],
            "birth_year": p['birth_year'], "death_year": p['death_year'],
            "biography": p['bio'] or '',
            "bio_zh": p['bio'] or '',
            "bio_vi": None, "bio_vi_status": None, "translation_id": None,
            "rules_outdated": False,
        }

        # Kiểm tra cache
        if p['bio']:
            src_hash = _t73_source_hash(p['bio'])
            rv = _t73_rules_version(_t73_get_active_rules(conn))
            cached = conn.execute(
                "SELECT id, translated_text, status, rules_version, model_id "
                "FROM translation_cache "
                "WHERE source_hash=? AND source_type='person_bio' AND status != 'invalidated' "
                "ORDER BY id DESC LIMIT 1", (src_hash,)
            ).fetchone()
            if cached:
                result['bio_vi'] = cached['translated_text']
                result['bio_vi_status'] = cached['status']
                result['translation_id'] = cached['id']
                result['rules_version'] = cached['rules_version']
                result['model_id'] = cached['model_id']
                result['rules_outdated'] = cached['rules_version'] != rv

        # T82 Step4 — wire timeline từ vn_person_events (T79 birth/death, T81 active/floruit, T82 legacy)
        timeline = []
        rows = conn.execute(
            "SELECT event_type, event_year, event_label_vi, source, confidence "
            "FROM vn_person_events WHERE person_id=? ORDER BY event_year IS NULL, event_year ASC",
            (person_id,)
        ).fetchall()
        for r in rows:
            if r['event_type'] in ('active', 'floruit', 'birth', 'death',
                                   'KeyLifeEvent', 'Contribution', 'PhilosophicalStance'):
                timeline.append({
                    "event_type": r['event_type'],
                    "event_year": r['event_year'],
                    "label_vi": r['event_label_vi'] or '',
                    "source": r['source'],
                    "confidence": r['confidence'],
                })
        result['timeline'] = timeline
        result['timeline_count'] = len(timeline)

        return jsonify(result)
    finally:
        conn.close()


@app.route('/daoanh/api/person/<person_id>/translate', methods=['GET', 'POST'])
def api_person_translate(person_id):
    """GET = cache-only (pre-check cho lazy UI), POST = cache + LLM call on miss.
    Check cache → GET trả về nếu có, POST dịch nếu chưa có.
    Body (optional): {} — không cần tham số.
    """
    conn = get_db_connection()
    try:
        p = conn.execute("SELECT id, bio FROM people WHERE id = ?", (person_id,)).fetchone()
        if not p or not p['bio']:
            return jsonify({"ok": False, "error": "Không có tiểu sử DILA cho nhân vật này"}), 404

        bio_zh = p['bio'].strip()
        src_hash = _t73_source_hash(bio_zh)

        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)

        existing = conn.execute(
            "SELECT id, translated_text, status, rules_version FROM translation_cache "
            "WHERE source_hash=? AND source_type='person_bio' AND status != 'invalidated' "
            "ORDER BY CASE WHEN rules_version=? THEN 0 ELSE 1 END, id DESC LIMIT 1",
            (src_hash, rv)
        ).fetchone()

        if existing:
            bio_vi_cached = existing['translated_text']
            if request.method == 'POST' and bio_vi_cached:
                conn.execute("UPDATE people SET bio_vi=? WHERE id=? AND (bio_vi IS NULL OR bio_vi='')",
                             (bio_vi_cached, person_id))
                conn.commit()
            return jsonify({
                "ok": True, "from_cache": True,
                "translation_id": existing['id'],
                "bio_vi": bio_vi_cached,
                "status": existing['status'],
                "rules_version": existing['rules_version'],
                "current_rules_version": rv,
                "rules_outdated": existing['rules_version'] != rv,
            })

        if request.method == 'GET':
            return jsonify({"ok": True, "from_cache": False, "bio_vi": None})

        # POST: cache miss → call LLM (T123 Style Constitution unified builder)
        prompt = _t73_build_style_prompt(bio_zh, _t73_style_lock(conn), label='tiểu sử')
        bio_vi, model_id, err_type = _t73_call_gemini(prompt)
        if not bio_vi:
            return jsonify({"ok": False, "error_type": err_type or 'api_error',
                            "error": "Dịch thất bại — thử lại sau"}), 503

        now = datetime.now().isoformat()
        cur = conn.execute("""
            INSERT OR REPLACE INTO translation_cache
              (source_hash, source_type, entity_id, source_text, translated_text,
               model_id, rules_version, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,'auto',?,?)
        """, (src_hash, 'person_bio', person_id, bio_zh, bio_vi, model_id, rv, now, now))
        conn.execute("UPDATE people SET bio_vi=? WHERE id=? AND (bio_vi IS NULL OR bio_vi='')",
                     (bio_vi, person_id))
        conn.commit()

        return jsonify({
            "ok": True, "from_cache": False,
            "translation_id": cur.lastrowid,
            "bio_vi": bio_vi,
            "status": "auto",
            "rules_version": rv,
            "rules_outdated": False,
            "model_id": model_id,
        })
    finally:
        conn.close()


# ── DILA Card Translate (T148 → Vietnamese, Buddhist scholarly) ────────────

def _build_dila_card_prompt(data, lock=None):
    """Prompt dịch toàn bộ DILA card sang tiếng Việt Phật học hàn lâm.
    lock: dict từ _t73_style_lock(conn) — inject Glossary Lock + active DB rules vào prompt."""
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
        + db_rules_block
        + "QUY TẮC BẮT BUỘC (DILA card):\n"
        "1. [PHIÊN ÂM] Tên người và địa danh: phiên âm Hán-Việt tiêu chuẩn Phật học (Thích Pháp Hải, Thiếu Lâm Tự...), KHÔNG dùng bính âm.\n"
        "2. [GIỮ TÊN HÁN] Tên tác phẩm / kinh điển / dịch phẩm: giữ tên Hán gốc trong ngoặc đơn ngay sau tên Việt. Ví dụ: Diệu Pháp Liên Hoa Kinh (妙法蓮華經).\n"
        "3. [MÃ CBETA] Giữ nguyên mọi mã CBETA (T09n0262, A000005...) không xóa.\n"
        "4. [TRIỀU ĐẠI] Dùng tên chuẩn: 北宋→Bắc Tống, 南宋→Nam Tống, 唐→Đường, 元→Nguyên, 明→Minh, 清→Thanh, 宋→Tống, 隋→Tùy, 魏→Ngụy, 晉→Tấn, 漢→Hán, 五代→Ngũ Đại.\n"
        "5. [STYLE] Văn phong trang nghiêm, học thuật, dành cho độc giả Phật tử Việt Nam có học thức.\n"
        "6. Trường nào rỗng (\"\" hoặc []) → giữ nguyên trong output.\n"
        "7. relations: chỉ dịch trường \"name\" thành \"name_vi\", giữ nguyên \"person_id\".\n"
        "8. listbibl: mỗi phần tử có dạng \"( CBETA ref ) tiêu đề Hán\". Giữ nguyên phần \"( CBETA ref )\" "
        "và chỉ dịch tiêu đề Hán sau đó, giữ tên Hán trong ngoặc đơn bên cạnh tên Việt. "
        "Ví dụ: \"( CBETA T09n0262_p0001a01 ) Diệu Pháp Liên Hoa Kinh (妙法蓮華經) quyển 1\".\n"
        "9. [SUGGESTED_RULES] Sau khi dịch xong, nếu gặp thuật ngữ/tên/địa danh nào CHƯA có trong Glossary Lock "
        "hoặc chưa có quy tắc rõ ràng trong các rules trên, hãy đề xuất bổ sung vào trường \"suggested_rules\". "
        "Mỗi đề xuất gồm: rule_code (viết hoa, dấu gạch dưới), rule_type (terminology/style/grammar/forbidden), "
        "description (1 dòng ngắn), rule_text (quy tắc cụ thể). "
        "Chỉ đề xuất khi thực sự cần thiết — không đề xuất những gì đã có trong Glossary Lock.\n\n"
        f"DỮ LIỆU CẦN DỊCH:\n{fields_block}\n\n"
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
        "  \"mentioned_in_vi\": \"<được đề cập trong (giữ tên Hán)>\",\n"
        "  \"active_at_vi\": \"<nơi hoạt động tiếng Việt>\",\n"
        "  \"relations_vi\": [{\"person_id\": \"A000xxx\", \"name_vi\": \"<tên phiên âm>\"}],\n"
        "  \"suggested_rules\": [\n"
        "    {\"rule_code\": \"TERM_XXX\", \"rule_type\": \"terminology\", "
        "\"description\": \"Dịch XXX → yyy\", \"rule_text\": \"XXX → yyy (lý do...)\"},\n"
        "    ...\n"
        "  ]\n"
        "}"
    )


def _save_suggested_rules(conn, suggested, entity_id, model_id):
    """Lưu rules đề xuất từ AI vào translation_rules với status='pending'.
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
        conn.execute(
            "INSERT INTO translation_rules "
            "(rule_code, rule_type, description, rule_text, is_active, priority, "
            " status, suggested_by, created_by, created_at, updated_at) "
            "VALUES (?,?,?,?,0,200,'pending',?,?,?,?)",
            (code, rtype, desc, text,
             f'ai_dila:{entity_id}:{model_id or ""}',
             'ai_suggest', now, now)
        )
        saved.append({'rule_code': code, 'rule_type': rtype,
                      'description': desc, 'rule_text': text})
    conn.commit()
    return saved


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


@app.route('/daoanh/api/person/<person_id>/dila_translate', methods=['GET', 'POST'])
def api_person_dila_translate(person_id):
    """GET = kiểm tra cache. POST = dịch DILA card sang tiếng Việt Phật học hàn lâm.
    Cache key: translation_cache (source_type='dila_card', entity_id=person_id).
    """
    import json as _j
    extra = _T148_DILA_EXTRA.get(person_id)
    if not extra:
        return jsonify({"ok": False, "error": "Không có dữ liệu DILA XML"}), 404

    conn = get_db_connection()
    try:
        p = conn.execute("SELECT id, name_zh, bio FROM people WHERE id = ?", (person_id,)).fetchone()
        name_zh = (p['name_zh'] or '') if p else ''
        bio_zh = (p['bio'] or '') if p else ''

        source_data = {
            'name_zh': name_zh,
            'alt_names': extra.get('alt_names') or [],
            'occupation': extra.get('occupation') or '',
            'place_of_origin': extra.get('place_of_origin') or '',
            'dynasty_xml': extra.get('dynasty_xml') or '',
            'bio_concise': bio_zh[:2000],
            'bio_extensive': (extra.get('bio_extensive') or '')[:4000],
            'listbibl': (extra.get('listbibl') or [])[:20],
            'works_tripitaka': extra.get('works_tripitaka') or '',
            'works_by': extra.get('works_by') or '',
            'mentioned_in': extra.get('mentioned_in') or '',
            'active_at': extra.get('active_at') or '',
            'relations': [{'person_id': r['person_id'], 'name': r.get('name', '')}
                          for r in (extra.get('relations') or [])],
        }
        src_hash = _t73_source_hash(_j.dumps(source_data, ensure_ascii=False, sort_keys=True))

        existing = conn.execute(
            "SELECT id, translated_text, status FROM translation_cache "
            "WHERE source_hash=? AND source_type='dila_card' AND status != 'invalidated' "
            "ORDER BY id DESC LIMIT 1",
            (src_hash,)
        ).fetchone()

        if existing:
            try:
                vi = _j.loads(existing['translated_text'])
            except Exception:
                vi = {}
            return jsonify({
                "ok": True, "from_cache": True,
                "translation_id": existing['id'],
                "vi": vi, "status": existing['status'],
            })

        if request.method == 'GET':
            return jsonify({"ok": True, "from_cache": False, "vi": None})

        # POST: gọi LLM (Gemini trước, fallback Groq)
        lock = _t73_style_lock(conn)
        prompt = _build_dila_card_prompt(source_data, lock)
        vi_text = None
        model_id = None
        try:
            GEMINI_KEY = "AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE"
            g_url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                     "gemini-3.6-flash:generateContent?key=" + GEMINI_KEY)
            g_resp = requests.post(g_url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.1},
            }, timeout=45)
            g_data = g_resp.json()
            if g_data.get('candidates'):
                vi_text = g_data['candidates'][0]['content']['parts'][0]['text']
                model_id = 'gemini-3.6-flash'
        except Exception as e:
            app.logger.warning(f"[dila_translate] Gemini error: {e}")

        if not vi_text:
            # Groq fallback với max_tokens 4096 (tránh cắt JSON giữa chừng)
            cfg = _llm_config_read()
            groq_key = cfg.get('groq_key') or GROQ_KEY
            groq_model = cfg.get('groq_model') or GROQ_MODEL
            try:
                gr = requests.post(GROQ_URL,
                    headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'},
                    json={'model': groq_model, 'messages': [{'role': 'user', 'content': prompt}],
                          'temperature': 0.1, 'max_tokens': 4096},
                    timeout=30)
                gd = gr.json()
                if gd.get('choices'):
                    vi_text = gd['choices'][0]['message']['content'].strip()
                    model_id = groq_model
            except Exception as eg:
                app.logger.warning(f"[dila_translate] Groq error: {eg}")
        if not vi_text:
            return jsonify({"ok": False, "error_type": 'api_error',
                                "error": "Dịch thất bại — thử lại sau"}), 503

        vi_dict = _parse_dila_vi_json(vi_text)
        if not vi_dict:
            return jsonify({"ok": False, "error": "AI không trả về JSON hợp lệ",
                            "raw": vi_text[:500]}), 500

        # Tách suggested_rules ra khỏi dữ liệu dịch trước khi lưu cache
        suggested_raw = vi_dict.pop('suggested_rules', None) or []
        vi_json = _j.dumps(vi_dict, ensure_ascii=False)

        rv = _t73_rules_version(_t73_get_active_rules(conn))
        now = datetime.now().isoformat()
        # DELETE trước để tránh UNIQUE(source_hash, source_type) conflict với record cũ
        conn.execute(
            "DELETE FROM translation_cache WHERE source_hash=? AND source_type='dila_card'",
            (src_hash,)
        )
        cur = conn.execute(
            "INSERT INTO translation_cache "
            "(source_hash, source_type, entity_id, source_text, translated_text, "
            " model_id, rules_version, status, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,'auto',?,?)",
            (src_hash, 'dila_card', person_id,
             _j.dumps(source_data, ensure_ascii=False)[:5000],
             vi_json, model_id, rv, now, now)
        )
        conn.commit()

        # Lưu rules đề xuất vào DB (status='pending', chờ admin phê chuẩn)
        new_rules = _save_suggested_rules(conn, suggested_raw, person_id, model_id)

        return jsonify({
            "ok": True, "from_cache": False,
            "translation_id": cur.lastrowid,
            "vi": vi_dict, "status": "auto", "model_id": model_id,
            "suggested_rules": new_rules,  # [] nếu không có đề xuất mới
        })
    finally:
        conn.close()


@app.route('/daoanh/api/admin/person/<person_id>/bio_vi', methods=['POST'])
def api_admin_save_person_bio_vi(person_id):
    """POST /daoanh/api/admin/person/<person_id>/bio_vi
    Body: {bio_vi: str, translation_id?: int}
    Admin trực tiếp lưu bản dịch đã chỉnh sửa vào translation_cache (status=edited)
    và cập nhật people.bio_vi.
    Header: X-Session-Token (bắt buộc).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    bio_vi = (data.get('bio_vi') or '').strip()
    translation_id = data.get('translation_id')

    if not bio_vi:
        return jsonify({"ok": False, "error": "bio_vi không được để trống"}), 400

    conn = get_db_connection()
    try:
        p = conn.execute("SELECT id, bio FROM people WHERE id = ?", (person_id,)).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "Không tìm thấy nhân vật"}), 404

        now = datetime.now().isoformat()
        new_id = translation_id

        if translation_id:
            conn.execute(
                "UPDATE translation_cache SET translated_text=?, status='edited', updated_at=? WHERE id=?",
                (bio_vi, now, translation_id)
            )
        elif p['bio']:
            src_hash = _t73_source_hash(p['bio'])
            rv = _t73_rules_version(_t73_get_active_rules(conn))
            conn.execute(
                "UPDATE translation_cache SET status='invalidated', updated_at=? "
                "WHERE source_hash=? AND source_type='person_bio' AND entity_id=?",
                (now, src_hash, person_id)
            )
            cur = conn.execute(
                "INSERT INTO translation_cache "
                "(source_hash, source_type, entity_id, source_text, translated_text, "
                " model_id, rules_version, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,'edited',?,?)",
                (src_hash, 'person_bio', person_id, p['bio'], bio_vi, 'manual', rv, now, now)
            )
            new_id = cur.lastrowid
        else:
            return jsonify({"ok": False, "error": "Nhân vật chưa có tiểu sử DILA"}), 400

        conn.execute("UPDATE people SET bio_vi=? WHERE id=?", (bio_vi, person_id))
        conn.commit()

        return jsonify({"ok": True, "translation_id": new_id, "status": "edited"})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/person/<person_id>/dila_vi', methods=['POST'])
def api_admin_save_person_dila_vi(person_id):
    """POST /daoanh/api/admin/person/<person_id>/dila_vi
    Body: {translation_id?: int, bio_concise_vi?: str, bio_extensive_vi?: str,
           dynasty_vi?: str, occupation_vi?: str, place_of_origin_vi?: str,
           works_tripitaka_vi?: str, works_by_vi?: str, mentioned_in_vi?: str,
           active_at_vi?: str, alt_names_vi?: list[str]}
    Lưu các field đã chỉnh sửa vào translation_cache (dila_card, status=edited)
    và cập nhật people.bio_vi nếu có bio_concise_vi.
    Header: X-Session-Token (bắt buộc).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    translation_id = data.get('translation_id')

    TEXT_FIELDS = ['bio_concise_vi', 'bio_extensive_vi', 'dynasty_vi', 'occupation_vi',
                   'place_of_origin_vi', 'works_tripitaka_vi', 'works_by_vi',
                   'mentioned_in_vi', 'active_at_vi']

    updates = {}
    for k in TEXT_FIELDS:
        if k in data and data[k] is not None:
            updates[k] = data[k].strip()
    if 'alt_names_vi' in data and isinstance(data['alt_names_vi'], list):
        updates['alt_names_vi'] = [s.strip() for s in data['alt_names_vi'] if s and s.strip()]

    if not updates:
        return jsonify({"ok": False, "error": "Không có field nào để lưu"}), 400

    import json as _j
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()

        if translation_id:
            row = conn.execute(
                "SELECT translated_text FROM translation_cache WHERE id=? AND source_type='dila_card'",
                (translation_id,)
            ).fetchone()
            if row:
                try:
                    vi_dict = _j.loads(row['translated_text'])
                except Exception:
                    vi_dict = {}
                vi_dict.update(updates)
                conn.execute(
                    "UPDATE translation_cache SET translated_text=?, status='edited', updated_at=? WHERE id=?",
                    (_j.dumps(vi_dict, ensure_ascii=False), now, translation_id)
                )

        if 'bio_concise_vi' in updates and updates['bio_concise_vi']:
            conn.execute("UPDATE people SET bio_vi=? WHERE id=?", (updates['bio_concise_vi'], person_id))

        conn.commit()
        return jsonify({"ok": True, "translation_id": translation_id, "status": "edited"})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/person/<person_id>/name_vi', methods=['POST'])
def api_admin_save_person_name_vi(person_id):
    """POST /daoanh/api/admin/person/<person_id>/name_vi
    Body: {name_vi: str}
    Lưu tên tiếng Việt (name_vi) vào bảng people.
    Header: X-Session-Token (bắt buộc).
    """
    token = request.headers.get('X-Session-Token', '')
    if not verify_session(token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    name_vi = (data.get('name_vi') or '').strip()
    if not name_vi:
        return jsonify({"ok": False, "error": "name_vi không được để trống"}), 400

    conn = get_db_connection()
    try:
        conn.execute("UPDATE people SET name_vi=? WHERE id=?", (name_vi, person_id))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.route('/daoanh/api/person/<person_id>/translate/report', methods=['POST'])
def api_person_translate_report(person_id):
    """POST /daoanh/api/person/<person_id>/translate/report
    User báo lỗi bản dịch. Body: {translation_id, note}.
    Nếu report_count >= 3 → status='reported' (admin chú ý).
    """
    body = request.get_json(silent=True) or {}
    tid = body.get('translation_id')
    note = (body.get('note') or '')[:500]
    error_type = (body.get('error_type') or 'style').strip()[:50]
    page_url = (body.get('page_url') or '').strip()[:500]
    if not tid:
        return jsonify({"ok": False, "error": "Thiếu translation_id"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, report_count, status, entity_id, source_type, translated_text "
            "FROM translation_cache WHERE id=?", (tid,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy bản dịch"}), 404
        new_count = row['report_count'] + 1
        new_status = 'reported' if new_count >= 3 else row['status']
        conn.execute(
            "UPDATE translation_cache SET report_count=?, status=?, updated_at=datetime('now') WHERE id=?",
            (new_count, new_status, tid)
        )
        # T123 — ghi chi tiết lỗi cho admin
        conn.execute(
            "INSERT INTO translation_error_report "
            "  (cache_id, source_type, entity_id, translated_text_snapshot, error_type, note, page_url, status) "
            "VALUES (?,?,?,?,?,?,?, 'pending')",
            (tid, row['source_type'] or 'person_bio', row['entity_id'] or person_id,
             (row['translated_text'] or '')[:2000], error_type, note, page_url)
        )
        conn.commit()
        return jsonify({"ok": True, "report_count": new_count, "status": new_status})
    finally:
        conn.close()


@app.route('/daoanh/api/person/<person_id>/dila_full')
def api_person_dila_full(person_id):
    """GET /daoanh/api/person/<person_id>/dila_full
    T148: Trả về dữ liệu đầy đủ từ DILA Person Authority XML cho một person:
    - alt_names: các tên khác (persName type="alternative")
    - listbibl: danh sách CBETA citations (listBibl/bibl)
    - works_tripitaka: kinh điển trong Đại Tạng (note type="worksInTripitaka")
    - works_by: tác phẩm (note type="worksBy")
    - mentioned_in: được đề cập trong (note type="mentionedIn")
    Load XML lần đầu (~3-5s), cache trong RAM cho các lần tiếp theo.
    """
    extra = _t148_get_extra(person_id)
    if not extra:
        return jsonify({"ok": True, "person_id": person_id, "has_extra": False})
    return jsonify({
        "ok": True,
        "person_id": person_id,
        "has_extra": True,
        "bio_extensive": extra.get('bio_extensive'),
        "alt_names": extra.get('alt_names') or [],
        "listbibl": extra.get('listbibl') or [],
        "works_tripitaka": extra.get('works_tripitaka'),
        "works_by": extra.get('works_by'),
        "mentioned_in": extra.get('mentioned_in'),
        "active_at": extra.get('active_at'),
        "name_latin": extra.get('name_latin'),
        "occupation": extra.get('occupation'),
        "place_of_origin": extra.get('place_of_origin'),
        "birth_death_quote": extra.get('birth_death_quote'),
        "wikidata_id": extra.get('wikidata_id'),
        "birth_date": extra.get('birth_date'),
        "death_date": extra.get('death_date'),
        "death_note": extra.get('death_note'),
        "relations": extra.get('relations') or [],
        "sex": extra.get('sex'),
        "dynasty_xml": extra.get('dynasty_xml'),
        "is_monk": extra.get('is_monk'),
    })


@app.route('/daoanh/api/admin/translation-rules')
def api_admin_translation_rules_list():
    """GET /daoanh/api/admin/translation-rules — Danh sách rules + pending rules đề xuất."""
    conn = get_db_connection()
    try:
        rules = _t73_get_active_rules(conn)
        all_rules = [dict(r) for r in conn.execute(
            "SELECT id, rule_code, rule_type, description, rule_text, is_active, priority, "
            "status, suggested_by, created_at, updated_at "
            "FROM translation_rules ORDER BY priority, id"
        ).fetchall()]
        pending_rules = [dict(r) for r in conn.execute(
            "SELECT id, rule_code, rule_type, description, rule_text, suggested_by, created_at "
            "FROM translation_rules WHERE status='pending' ORDER BY id DESC"
        ).fetchall()]
        rv = _t73_rules_version(rules)
        cache_stats = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM translation_cache GROUP BY status"
        ).fetchall()
        return jsonify({
            "ok": True,
            "rules": all_rules,
            "pending_rules": pending_rules,
            "pending_count": len(pending_rules),
            "active_count": len(rules),
            "rules_version": rv,
            "cache_stats": {r['status']: r['cnt'] for r in cache_stats},
        })
    finally:
        conn.close()


@app.route('/daoanh/api/admin/translation-rules/<int:rule_id>/approve', methods=['POST'])
def api_admin_translation_rule_approve(rule_id):
    """POST — Admin phê chuẩn rule đề xuất (pending→active)."""
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()
        n = conn.execute(
            "UPDATE translation_rules SET status='active', is_active=1, updated_at=? "
            "WHERE id=? AND status='pending'",
            (now, rule_id)
        ).rowcount
        conn.commit()
        if not n:
            return jsonify({"ok": False, "error": "Không tìm thấy rule pending"}), 404
        rule = dict(conn.execute(
            "SELECT id, rule_code, rule_type, description, rule_text FROM translation_rules WHERE id=?",
            (rule_id,)
        ).fetchone())
        return jsonify({"ok": True, "approved": rule})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/translation-rules/<int:rule_id>/dismiss', methods=['POST'])
def api_admin_translation_rule_dismiss(rule_id):
    """POST — Admin từ chối rule đề xuất (pending→dismissed)."""
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()
        n = conn.execute(
            "UPDATE translation_rules SET status='dismissed', updated_at=? "
            "WHERE id=? AND status='pending'",
            (now, rule_id)
        ).rowcount
        conn.commit()
        if not n:
            return jsonify({"ok": False, "error": "Không tìm thấy rule pending"}), 404
        return jsonify({"ok": True, "dismissed": rule_id})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/translation-rules', methods=['POST'])
def api_admin_translation_rules_upsert():
    """POST /daoanh/api/admin/translation-rules — Thêm hoặc cập nhật rule.
    Body: {rule_code, rule_type, description, rule_text, priority, is_active}.
    """
    body = request.get_json(silent=True) or {}
    rule_code = (body.get('rule_code') or '').strip().upper()
    if not rule_code or not body.get('rule_text'):
        return jsonify({"ok": False, "error": "Thiếu rule_code hoặc rule_text"}), 400
    conn = get_db_connection()
    try:
        now = datetime.now().isoformat()
        rule_text = body['rule_text']
        desc = body.get('description', '')
        # '_keep_' = sentinel từ toggleRule: chỉ đổi is_active, không đổi rule_text/description
        keep_text = (rule_text == '_keep_')
        conn.execute("""
            INSERT INTO translation_rules (rule_code, rule_type, description, rule_text, is_active, priority, status, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,'active','admin',?,?)
            ON CONFLICT(rule_code) DO UPDATE SET
              rule_type=excluded.rule_type,
              description=CASE WHEN ? THEN description ELSE excluded.description END,
              rule_text=CASE WHEN ? THEN rule_text ELSE excluded.rule_text END,
              is_active=excluded.is_active,
              status='active',
              priority=excluded.priority, updated_at=excluded.updated_at
        """, (rule_code, body.get('rule_type', 'style'), desc,
              rule_text, int(body.get('is_active', 1)),
              int(body.get('priority', 100)), now, now,
              keep_text, keep_text))
        conn.commit()
        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)
        return jsonify({"ok": True, "rule_code": rule_code, "new_rules_version": rv})
    finally:
        conn.close()


# ============================================================
#  T74 — Tạm Dịch Place Note (mở rộng T73 cho địa danh DILA)
#  Cùng kiến trúc lazy-cache, source_type='place_note'
# ============================================================

@app.route('/daoanh/api/place/<dila_id>/translate', methods=['GET', 'POST'])
def api_place_translate(dila_id):
    """GET/POST /daoanh/api/place/<dila_id>/translate
    GET  → trả về bản dịch từ cache nếu có (không dịch mới).
    POST → check cache → dịch Gemini nếu MISS → auto-save → trả về.
    """
    conn = get_db_connection()
    try:
        place = conn.execute(
            "SELECT id, note FROM places_dila WHERE id = ?", (dila_id,)
        ).fetchone()
        if not place or not (place['note'] or '').strip():
            # Fallback: try by dila_id field
            place = conn.execute(
                "SELECT id, note FROM places_dila WHERE id = ? OR id LIKE ?",
                (dila_id, f"%{dila_id}%")
            ).fetchone()
        if not place or not (place['note'] or '').strip():
            # Fallback: short ID (PL056722) → look up GPS from places → match places_dila by GPS
            gps_row = conn.execute(
                "SELECT gps_lat, gps_long FROM places WHERE id = ?", (dila_id,)
            ).fetchone()
            if gps_row and gps_row['gps_lat']:
                place = conn.execute(
                    "SELECT id, note FROM places_dila"
                    " WHERE ABS(geo_lat - ?) < 0.001 AND ABS(geo_long - ?) < 0.001"
                    " AND note IS NOT NULL AND note != '' LIMIT 1",
                    (gps_row['gps_lat'], gps_row['gps_long'])
                ).fetchone()
        if not place or not (place['note'] or '').strip():
            return jsonify({"ok": False, "error": "Không có mô tả DILA cho địa danh này"}), 404

        note_zh = place['note'].strip()
        src_hash = _t73_source_hash(note_zh)
        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)

        # GET → chỉ trả cache, không dịch
        if request.method == 'GET':
            cached = conn.execute(
                "SELECT id, translated_text, status, rules_version, model_id "
                "FROM translation_cache "
                "WHERE source_hash=? AND source_type='place_note' AND status != 'invalidated' "
                "ORDER BY id DESC LIMIT 1", (src_hash,)
            ).fetchone()
            if cached:
                return jsonify({
                    "ok": True, "from_cache": True,
                    "translation_id": cached['id'],
                    "note_vi": cached['translated_text'],
                    "status": cached['status'],
                    "rules_version": cached['rules_version'],
                    "rules_outdated": cached['rules_version'] != rv,
                })
            return jsonify({"ok": True, "from_cache": False, "note_vi": None})

        # POST → dịch nếu chưa có
        existing = conn.execute(
            "SELECT id, translated_text, status, rules_version FROM translation_cache "
            "WHERE source_hash=? AND source_type='place_note' AND status != 'invalidated' "
            "ORDER BY CASE WHEN rules_version=? THEN 0 ELSE 1 END, id DESC LIMIT 1",
            (src_hash, rv)
        ).fetchone()
        if existing:
            return jsonify({
                "ok": True, "from_cache": True,
                "translation_id": existing['id'],
                "note_vi": existing['translated_text'],
                "status": existing['status'],
                "rules_version": existing['rules_version'],
                "rules_outdated": existing['rules_version'] != rv,
            })

        prompt = _t73_build_style_prompt(note_zh, _t73_style_lock(conn), label='mô tả địa danh')
        note_vi, model_id, err_type = _t73_call_gemini(prompt)
        if not note_vi:
            return jsonify({"ok": False, "error_type": err_type or 'api_error',
                            "error": "Dịch thất bại — thử lại sau"}), 503

        now = datetime.now().isoformat()
        cur = conn.execute("""
            INSERT OR REPLACE INTO translation_cache
              (source_hash, source_type, entity_id, source_text, translated_text,
               model_id, rules_version, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,'auto',?,?)
        """, (src_hash, 'place_note', dila_id, note_zh, note_vi, model_id, rv, now, now))
        conn.commit()
        return jsonify({
            "ok": True, "from_cache": False,
            "translation_id": cur.lastrowid,
            "note_vi": note_vi, "status": "auto",
            "rules_version": rv, "model_id": model_id,
        })
    finally:
        conn.close()


@app.route('/daoanh/api/place/<dila_id>/translate/report', methods=['POST'])
def api_place_translate_report(dila_id):
    """POST /daoanh/api/place/<dila_id>/translate/report — user báo lỗi bản dịch địa danh."""
    body = request.get_json(silent=True) or {}
    tid = body.get('translation_id')
    note = (body.get('note') or '')[:500]
    error_type = (body.get('error_type') or 'style').strip()[:50]
    page_url = (body.get('page_url') or '').strip()[:500]
    if not tid:
        return jsonify({"ok": False, "error": "Thiếu translation_id"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, report_count, status, entity_id, translated_text "
            "FROM translation_cache WHERE id=? AND source_type='place_note'",
            (tid,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy bản dịch"}), 404
        new_count = row['report_count'] + 1
        new_status = 'reported' if new_count >= 3 else row['status']
        conn.execute(
            "UPDATE translation_cache SET report_count=?, status=?, updated_at=datetime('now') WHERE id=?",
            (new_count, new_status, tid)
        )
        # T123 — ghi chi tiết lỗi cho admin
        conn.execute(
            "INSERT INTO translation_error_report "
            "  (cache_id, source_type, entity_id, translated_text_snapshot, error_type, note, page_url, status) "
            "VALUES (?,?,?,?,?,?,?, 'pending')",
            (tid, 'place_note', row['entity_id'] or dila_id,
             (row['translated_text'] or '')[:2000], error_type, note, page_url)
        )
        conn.commit()
        return jsonify({"ok": True, "report_count": new_count, "status": new_status})
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
    # T123 — Style Constitution unified builder + prompt_version=rules_version
    lock = _t73_style_lock(conn)
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


@app.route('/daoanh/api/passage/<passage_id>/translate', methods=['GET', 'POST'])
def api_passage_translate(passage_id):
    """GET = cache-only, POST = cache + Groq call on miss (T85).
    Passage có text_passages (schema T94/T95) → dịch qua translation_segments (SSOT).
    Passage chưa có text_passages → dịch TOÀN PHẦN passage bằng Groq (legacy, vi_text)."""
    conn = get_db_connection()
    try:
        p = conn.execute(
            "SELECT passage_id, raw_text FROM passage WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "Không tìm thấy passage"}), 404
        raw_text = (p['raw_text'] or '').strip()
        if not raw_text:
            return jsonify({"ok": False, "error": "Passage không có raw_text"}), 404
        units = _t85_units(conn, passage_id)
        if units is not None:
            if request.method == 'GET':
                return _t85_get_segments(conn, units)
            body = request.get_json(silent=True) or {}
            return _t85_post_segments(conn, passage_id, units, bool(body.get('force')))
        # --- Legacy fallback: passage chưa có text_passages (vd T51n2076) ---
        # Dịch TOÀN PHẦN passage bằng Groq (giữ hành vi endpoint cũ /daoanh/api/passage/<int>/translate)
        # + cache bằng passage.vi_text. force=True → bỏ qua cached, dịch lại.
        cfg = _llm_config_read()
        key = cfg.get('groq_key') or GROQ_KEY
        model = cfg.get('groq_model') or GROQ_MODEL
        body = request.get_json(silent=True) or {}
        force = bool(body.get('force'))
        cached_vt = None
        if not force:
            c = conn.execute(
                "SELECT vi_text FROM passage WHERE passage_id = ? AND vi_text IS NOT NULL AND vi_text != ''",
                (passage_id,)
            ).fetchone()
            if c:
                cached_vt = c['vi_text']
        if request.method == 'GET':
            return jsonify({
                "ok": True, "mode": "legacy", "from_cache": bool(cached_vt),
                "vi_text": cached_vt, "translation_id": None,
                "status": "cached" if cached_vt else "missing",
            })
        if cached_vt:
            return jsonify({
                "ok": True, "mode": "legacy", "from_cache": True,
                "vi_text": cached_vt, "translation_id": None, "status": "cached",
            })
        if not key:
            return jsonify({'ok': False, 'error': 'GROQ_API_KEY chưa cấu hình'}), 503
        preview = raw_text[:4000]
        try:
            # T123 — Style Constitution unified builder (thay system tĩnh _BUDDHIST_SYSTEM_PROMPT)
            prompt = _t73_build_style_prompt(preview, _t73_style_lock(conn), label='passage')
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
                json={'model': model,
                      'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.1, 'max_tokens': 2048},
                timeout=30
            )
            result = resp.json()
        except Exception as e:
            return jsonify({"ok": False, "error": f"Groq error: {str(e)}"}), 500
        if not result.get('choices'):
            return jsonify({'ok': False, 'error': f'Groq API lỗi: {result.get("error", {}).get("message", "unknown")}'}), 500
        vi_text = result['choices'][0]['message']['content'].strip()
        if not vi_text:
            return jsonify({"ok": False, "error": "Dịch thất bại — kết quả rỗng"}), 500
        conn.execute(
            "UPDATE passage SET vi_text = ?, translation_draft = 1 WHERE passage_id = ?",
            (vi_text, passage_id)
        )
        conn.commit()
        return jsonify({
            "ok": True, "mode": "legacy", "from_cache": False,
            "vi_text": vi_text, "translation_id": None, "status": "draft",
        })
    finally:
        conn.close()


@app.route('/daoanh/api/passage/<passage_id>/translate/report', methods=['POST'])
def api_passage_translate_report(passage_id):
    """POST /daoanh/api/passage/<passage_id>/translate/report
    User báo lỗi bản dịch nháp của một passage. Tăng report_count trong translation_cache
    (source_type='passage'), đạt ≥3 → status='reported' để admin thấy trong Dashboard
    (admin/translation_cache.html filter source_type=passage)."""
    body = request.get_json(silent=True) or {}
    note = (body.get('note') or '').strip()[:500]
    error_type = (body.get('error_type') or 'style').strip()[:50]
    page_url = (body.get('page_url') or '').strip()[:500]
    conn = get_db_connection()
    try:
        # Ưu tiên: cache đã có cho passage này (theo source_hash của raw_text)
        p = conn.execute(
            "SELECT passage_id, raw_text, vi_text FROM passage WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not p:
            return jsonify({"ok": False, "error": "Không tìm thấy passage"}), 404
        src_hash = _t73_source_hash(p['raw_text'] or '')
        row = conn.execute(
            "SELECT id, report_count, status, translated_text FROM translation_cache "
            "WHERE source_hash=? AND source_type='passage' ORDER BY id DESC LIMIT 1",
            (src_hash,)
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Chưa có bản dịch cache cho passage này"}), 404
        new_count = row['report_count'] + 1
        new_status = 'reported' if new_count >= 3 else row['status']
        conn.execute(
            "UPDATE translation_cache SET report_count=?, status=?, updated_at=datetime('now') WHERE id=?",
            (new_count, new_status, row['id'])
        )
        # T123 — ghi chi tiết lỗi (snapshot + link + note) cho admin
        conn.execute(
            "INSERT INTO translation_error_report "
            "  (cache_id, source_type, entity_id, translated_text_snapshot, error_type, note, page_url, status) "
            "VALUES (?,?,?,?,?,?,?, 'pending')",
            (row['id'], 'passage', passage_id,
             (row['translated_text'] or p['vi_text'] or '')[:2000],
             error_type, note, page_url)
        )
        conn.commit()
        return jsonify({"ok": True, "report_count": new_count, "status": new_status})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/translation-cache', methods=['GET'])
def api_admin_translation_cache_list():
    """GET /daoanh/api/admin/translation-cache — danh sách bản dịch, hỗ trợ filter/pagination."""
    status = request.args.get('status', '')
    source_type = request.args.get('source_type', '')
    entity_id = request.args.get('entity_id', '')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    conn = get_db_connection()
    try:
        conds, params = [], []
        if status:
            conds.append("status = ?"); params.append(status)
        if source_type:
            conds.append("source_type = ?"); params.append(source_type)
        if entity_id:
            conds.append("entity_id LIKE ?"); params.append(f"%{entity_id}%")
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        total = conn.execute(f"SELECT COUNT(*) FROM translation_cache {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT id, entity_id, source_type, translated_text, model_id, "
            f"rules_version, status, report_count, created_at FROM translation_cache "
            f"{where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        return jsonify({"ok": True, "total": total, "rows": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route('/daoanh/api/translate-rules')
def api_translate_rules_public():
    """T123 — GET /daoanh/api/translate-rules (public).
    Hiển thị Style Constitution: rules_version + active rules + số lượng glossary/exemplar.
    Dùng cho badge "Ban Dịch PTDA" trong giao diện và để user/admin thấy rules hiện hành."""
    conn = get_db_connection()
    try:
        rules = _t73_get_active_rules(conn)
        rv = _t73_rules_version(rules)
        try:
            gloss_count = conn.execute(
                "SELECT COUNT(*) FROM translation_glossary WHERE is_locked=1").fetchone()[0]
        except Exception:
            gloss_count = 0
        try:
            ex_count = conn.execute(
                "SELECT COUNT(*) FROM translation_exemplar WHERE is_active=1").fetchone()[0]
        except Exception:
            ex_count = 0
        return jsonify({
            "ok": True,
            "rules_version": rv,
            "active_count": len(rules),
            "rules": [{'rule_code': r['rule_code'], 'rule_type': r['rule_type'],
                       'rule_text': r['rule_text']} for r in rules],
            "glossary_locked": gloss_count,
            "exemplar_active": ex_count,
            "persona": "Ban Dịch PTDA",
        })
    finally:
        conn.close()


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
         ['CANONICAL_NAMES', 'HANVIET_NAMES', 'HANVIET_PLACES', 'REIGN_ERA']),
        (('tục', 'thô', 'hiện đại', 'không trang', 'lạc giọng', 'văn phong'), ['TONE_OVERALL', 'LITERARY_PURITY', 'ACADEMIC_STYLE']),
        (('technical', 'kỹ thuật', 'lỗi hệ thống', 'không hiển thị', '500', 'timeout'), ['OUTPUT_FORMAT']),
    ]
    for words, codes in mappings:
        if any(w in text for w in words):
            suggestion.extend(c for c in codes if c not in suggestion)
    return suggestion


@app.route('/daoanh/api/admin/translation-error-reports', methods=['GET'])
def api_admin_translation_error_reports():
    """T123 — GET /daoanh/api/admin/translation-error-reports — danh sách báo lỗi dịch.
    Trả chi tiết: snapshot, error_type, note, page_url, entity, kèm đề xuất rule fix
    (map theo error_type + note) + rules active để admin tra cứu."""
    status = request.args.get('status', '')
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    conn = get_db_connection()
    try:
        conds, params = [], []
        if status:
            conds.append("r.status = ?"); params.append(status)
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        total = conn.execute(
            f"SELECT COUNT(*) FROM translation_error_report r {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT r.id, r.cache_id, r.source_type, r.entity_id, "
            f"       r.translated_text_snapshot, r.error_type, r.note, r.page_url, "
            f"       r.status, r.created_at, "
            f"       COALESCE(c.rule_text_c, '<gốc ngoài cache>') AS rule_version_note "
            f" FROM translation_error_report r "
            f" LEFT JOIN (SELECT source_hash as rule_text_c, rules_version FROM translation_cache GROUP BY source_hash, rules_version) c "
            f"   ON 1=0 "
            f" {where} ORDER BY r.id DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        rules = _t73_get_active_rules(conn)
        out = []
        for r in rows:
            row = dict(r)
            row.pop('rule_version_note', None)
            row['suggested_rules'] = _error_report_suggestion(
                row['error_type'], row['note'], rules)
            out.append(row)
        return jsonify({"ok": True, "total": total, "rows": out, "rules": [
            {'rule_code': x['rule_code'], 'rule_text': x['rule_text']} for x in rules]})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/translation-error-reports/<int:report_id>', methods=['POST'])
def api_admin_translation_error_report_resolve(report_id):
    """T123 — POST /daoanh/api/admin/translation-error-reports/<id>
    Admin đóng báo lỗi. Body: {status: 'resolved'|'rejected', admin_note?}.
    Ghi nhận bằng cách update status; cache giữ nguyên (quyết định Lee: bản cũ để nguyên)."""
    body = request.get_json(silent=True) or {}
    new_status = body.get('status', 'resolved')
    if new_status not in ('resolved', 'rejected'):
        return jsonify({"ok": False, "error": "status phải là resolved|rejected"}), 400
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id FROM translation_error_report WHERE id=?", (report_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Không tìm thấy báo lỗi"}), 404
        conn.execute(
            "UPDATE translation_error_report SET status=? WHERE id=?",
            (new_status, report_id))
        conn.commit()
        return jsonify({"ok": True, "id": report_id, "status": new_status})
    finally:
        conn.close()
def api_admin_translate_invalidate():
    """POST /daoanh/api/admin/translate/invalidate
    Mass-invalidate bản dịch theo rules_version (hoặc tất cả nếu rules_version='ALL').
    Body: {rules_version: '<hash>', source_type: 'person_bio'|'all'}.
    Dùng khi admin cập nhật rules → muốn user dịch lại với rules mới.
    """
    body = request.get_json(silent=True) or {}
    rv = (body.get('rules_version') or '').strip()
    source_type = body.get('source_type', 'all')
    if not rv:
        return jsonify({"ok": False, "error": "Thiếu rules_version. Dùng 'ALL' để xóa tất cả."}), 400

    conn = get_db_connection()
    try:
        if rv == 'ALL':
            if source_type == 'all':
                cnt = conn.execute(
                    "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
                    "WHERE status != 'invalidated'"
                ).rowcount
            else:
                cnt = conn.execute(
                    "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
                    "WHERE source_type=? AND status != 'invalidated'", (source_type,)
                ).rowcount
        else:
            if source_type == 'all':
                cnt = conn.execute(
                    "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
                    "WHERE rules_version=? AND status != 'invalidated'", (rv,)
                ).rowcount
            else:
                cnt = conn.execute(
                    "UPDATE translation_cache SET status='invalidated', updated_at=datetime('now') "
                    "WHERE rules_version=? AND source_type=? AND status != 'invalidated'",
                    (rv, source_type)
                ).rowcount
        conn.commit()
        return jsonify({"ok": True, "invalidated_count": cnt, "rules_version": rv, "source_type": source_type})
    finally:
        conn.close()


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
        text, model_id, _err = _t73_call_gemini(prompt)
        return text
    except Exception as e:
        app.logger.error(f"[T75] LLM error: {e}")
        return None


@app.route('/daoanh/api/entity/<entity_id>/web-enrichments', methods=['GET'])
def api_web_enrichments_list(entity_id):
    """GET: Lấy danh sách enrichments đã cache cho entity."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """SELECT id, source_name, source_url, summary_vi, status,
                      report_count, created_at, fetched_by
               FROM web_enrichment_cache
               WHERE entity_id=? AND status != 'rejected'
               ORDER BY CASE WHEN status='verified' THEN 0 ELSE 1 END, id DESC""",
            (entity_id,)
        ).fetchall()
        enrichments = [dict(r) for r in rows]
        return jsonify({"ok": True, "enrichments": enrichments, "count": len(enrichments)})
    finally:
        conn.close()


@app.route('/daoanh/api/entity/<entity_id>/web-enrich', methods=['POST'])
def api_web_enrich(entity_id):
    """POST: Fetch thông tin mới từ Wikipedia, AI tóm tắt, save cache.
    Cooldown 30 ngày: không fetch lại nếu đã có entry còn mới.
    """
    conn = get_db_connection()
    try:
        # Cooldown check (30 ngày)
        recent = conn.execute(
            """SELECT id, summary_vi, source_name, source_url, created_at, status
               FROM web_enrichment_cache
               WHERE entity_id=? AND status != 'rejected'
               AND julianday('now') - julianday(created_at) < 30
               ORDER BY id DESC LIMIT 1""",
            (entity_id,)
        ).fetchone()
        if recent:
            return jsonify({
                "ok": True, "from_cache": True,
                "enrichment_id": recent['id'],
                "summary_vi": recent['summary_vi'],
                "source_name": recent['source_name'],
                "source_url": recent['source_url'],
                "created_at": recent['created_at'],
                "status": recent['status'],
                "msg": "Đã có thông tin cập nhật trong 30 ngày qua"
            })

        # Lấy tên entity
        entity_type, name_zh, name_en, name_vi_guess = _t75_entity_info(entity_id, conn)
        if not entity_type:
            return jsonify({"ok": False, "error": f"Không tìm thấy entity {entity_id}"}), 404
        if not name_zh and not name_en:
            return jsonify({"ok": False, "error": "Entity không có tên để tra cứu"}), 400

        display_name = name_vi_guess or name_en or name_zh

        # Tìm Wikipedia (vi → zh)
        wiki_url, raw_content, wiki_title, source_label = _t75_search_wikipedia(name_zh, name_en, lang='vi')
        if not wiki_url:
            # T112 D-Feedback: tự ghi "thiếu nguồn" khi entity không index được trên Wikipedia
            _t112_record_gap(entity_type, entity_id, display_name, 'thieu_nguon',
                             f"Không tìm thấy Wikipedia cho '{display_name}'",
                             source_hint='Wikipedia (vi|zh)')
            return jsonify({
                "ok": False,
                "error": f"Không tìm thấy thông tin Wikipedia cho '{display_name}'"
            }), 404

        # AI tóm tắt
        summary_vi = _t75_summarize(display_name, entity_type, raw_content, source_label, entity_id)
        if not summary_vi:
            return jsonify({"ok": False, "error": "Lỗi AI tóm tắt"}), 500

        # Lưu vào cache
        cur = conn.execute(
            """INSERT INTO web_enrichment_cache
               (entity_id, entity_type, source_url, source_name, raw_content, summary_vi, fetched_by, status)
               VALUES (?, ?, ?, ?, ?, ?, 'user', 'auto')""",
            (entity_id, entity_type, wiki_url, source_label, raw_content[:3000], summary_vi)
        )
        conn.commit()
        enrich_id = cur.lastrowid

        return jsonify({
            "ok": True, "from_cache": False,
            "enrichment_id": enrich_id,
            "summary_vi": summary_vi,
            "source_name": source_label,
            "source_url": wiki_url,
            "entity_name": display_name,
            "status": "auto"
        })
    finally:
        conn.close()


@app.route('/daoanh/api/entity/<entity_id>/web-enrich/report', methods=['POST'])
def api_web_enrich_report(entity_id):
    """POST: Báo lỗi enrichment — tăng report_count, status='reported' nếu >= 2."""
    data = request.get_json(silent=True) or {}
    enrich_id = data.get('enrichment_id')
    if not enrich_id:
        return jsonify({"ok": False, "error": "Thiếu enrichment_id"}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE web_enrichment_cache SET report_count = report_count + 1 WHERE id=? AND entity_id=?",
            (enrich_id, entity_id)
        )
        row = conn.execute("SELECT report_count FROM web_enrichment_cache WHERE id=?", (enrich_id,)).fetchone()
        if row and row['report_count'] >= 2:
            conn.execute("UPDATE web_enrichment_cache SET status='reported' WHERE id=?", (enrich_id,))
        conn.commit()
        return jsonify({"ok": True, "report_count": row['report_count'] if row else 1})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/web-enrichments', methods=['GET'])
def api_admin_web_enrichments():
    """GET: Admin list enrichments với filter status, entity_type; pagination 50/page."""
    status_f = request.args.get('status', '')
    etype_f = request.args.get('entity_type', '')
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    offset = (page - 1) * per_page
    conn = get_db_connection()
    try:
        where, params = [], []
        if status_f:
            where.append("status=?"); params.append(status_f)
        if etype_f:
            where.append("entity_type=?"); params.append(etype_f)
        wc = ("WHERE " + " AND ".join(where)) if where else ""
        total = conn.execute(f"SELECT COUNT(*) FROM web_enrichment_cache {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, entity_id, entity_type, source_name, source_url,
                       summary_vi, status, report_count, created_at, fetched_by
                FROM web_enrichment_cache {wc}
                ORDER BY CASE WHEN status='reported' THEN 0 WHEN status='auto' THEN 1 ELSE 2 END, id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()
        return jsonify({
            "ok": True, "total": total, "page": page, "per_page": per_page,
            "enrichments": [dict(r) for r in rows]
        })
    finally:
        conn.close()


@app.route('/daoanh/api/admin/web-enrichment/<int:enrich_id>/status', methods=['POST'])
def api_admin_web_enrich_status(enrich_id):
    """POST: Admin verify hoặc reject một enrichment entry."""
    data = request.get_json(silent=True) or {}
    new_status = data.get('status', '')
    if new_status not in ('verified', 'rejected', 'auto'):
        return jsonify({"ok": False, "error": "status phải là verified/rejected/auto"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE web_enrichment_cache SET status=? WHERE id=?", (new_status, enrich_id))
        conn.commit()
        return jsonify({"ok": True, "id": enrich_id, "status": new_status})
    finally:
        conn.close()


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


@app.route('/daoanh/api/feedback', methods=['POST'])
def api_feedback():
    """POST /daoanh/api/feedback — kênh Tăng Ni báo lỗi (sai dữ liệu/thiếu nguồn).
    Public, không cần login; +7 pattern xác thực input. Ráspec6 → T119 Gap 5."""
    data = request.get_json(silent=True) or {}
    note = (data.get('note_plain') or '').strip()
    ftype = (data.get('feedback_type') or 'khac').strip()
    if ftype not in ('sai_du_lieu', 'thieu_nguon', 'loi_hien_thi', 'khac'):
        return jsonify({"ok": False, "error": "feedback_type phải ∈ sai_du_lieu|thieu_nguon|loi_hien_thi|khac"}), 400
    if not note or len(note) < 8:
        return jsonify({"ok": False, "error": "note_plain phải ≥ 8 ký tự mô tả lỗi"}), 400
    entity_id = (data.get('entity_id') or '').strip()[:80]
    entity_type = (data.get('entity_type') or '').strip()[:20]
    user_level = (data.get('user_level') or '').strip()[:20]
    conn = get_db_connection()
    try:
        cur = conn.execute(
            """INSERT INTO user_feedback
               (entity_id, entity_type, feedback_type, note_plain, user_level, status)
               VALUES (?, ?, ?, ?, ?, 'new')""",
            (entity_id or None, entity_type or None, ftype, note, user_level or None),
        )
        conn.commit()
        return jsonify({"ok": True, "feedback_id": cur.lastrowid, "status": "new"}), 201
    finally:
        conn.close()


@app.route('/daoanh/api/admin/data-gaps', methods=['GET'])
def api_admin_data_gaps():
    """GET /daoanh/api/admin/data-gaps?status=new&page= — T112 D-Feedback admin report."""
    status_f = (request.args.get('status') or '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    where, params = ["1=1"], []
    if status_f in ('new', 'ack', 'closed'):
        where.append("status=?"); params.append(status_f)
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM data_gap_requests WHERE {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, entity_type, entity_id, entity_name, gap_type, note_plain,
                       source_hint, status, created_at
                FROM data_gap_requests WHERE {wc}
                ORDER BY CASE status WHEN 'new' THEN 0 ELSE 1 END, id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        by_type = {r[0]: r[1] for r in conn.execute(
            "SELECT gap_type, COUNT(*) FROM data_gap_requests WHERE status='new' GROUP BY gap_type"
        ).fetchall()}
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "gaps": [dict(r) for r in rows], "by_type": by_type})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/data-gap/<int:gid>/status', methods=['POST'])
def api_admin_data_gap_status(gid):
    """POST /daoanh/api/admin/data-gap/<id>/status — {status: ack|closed}."""
    data = request.get_json(silent=True) or {}
    st = (data.get('status') or '').strip()
    if st not in ('ack', 'closed'):
        return jsonify({"ok": False, "error": "status phải ∈ ack|closed"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE data_gap_requests SET status=? WHERE id=?", (st, gid))
        conn.commit()
        return jsonify({"ok": True, "id": gid, "status": st})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/entity-claims/unverified', methods=['GET'])
def api_admin_claims_unverified():
    """GET /daoanh/api/admin/entity-claims/unverified?page=&per_page=&entity_type=&status=
    T119 — hàng chờ claims chưa thẩm định (447,885 unverified); pagination, Zero-RAM."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    entity_type = (request.args.get('entity_type') or '').strip()
    status_f = (request.args.get('status') or 'unverified').strip()
    where = ["c.verification_status = ?"]
    params = []
    params.append(status_f if status_f != 'any' else '')
    if entity_type:
        where.append("e.entity_type = ?"); params.append(entity_type)
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id WHERE {wc}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT c.claim_id, c.entity_id, e.entity_type, e.canonical_label, c.claim_type,
                       c.predicate, c.object_text, c.source_reference, c.verification_status,
                       c.assertion_level, c.source_url, c.created_at
                FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id
                WHERE {wc}
                ORDER BY c.claim_id
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "claims": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/claims/bulk-review', methods=['POST'])
def api_admin_claims_bulk_review():
    """POST /daoanh/api/admin/claims/bulk-review — {ids:[...], verdict, assertion_level, editor}
    T119 — thẩm định hàng loạt claims; mỗi claim ghi 1 dòng en_audit_log (audit_id trả về)."""
    data = request.get_json(silent=True) or {}
    ids = [int(i) for i in (data.get('ids') or []) if str(i).isdigit()][:500]
    verdict = (data.get('verdict') or 'verified').strip()
    level = (data.get('assertion_level') or 'low').strip()
    editor = (data.get('editor') or '').strip() or 'admin'
    note = (data.get('note') or '').strip()
    if not ids:
        return jsonify({"ok": False, "error": "Không có ids nào"}), 400
    if verdict not in ('verified', 'disputed', 'needs_review', 'unverified'):
        return jsonify({"ok": False, "error": "verdict phải ∈ verified|disputed|needs_review|unverified"}), 400
    if level not in ('high', 'medium', 'low'):
        return jsonify({"ok": False, "error": "assertion_level phải ∈ high|medium|low"}), 400
    conn = get_db_connection()
    try:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"""SELECT c.claim_id, c.entity_id, e.canonical_label, c.claim_type, c.predicate,
                       c.source_id, c.verification_status, c.assertion_level
                FROM entity_claims c LEFT JOIN entity_hub e ON e.entity_id = c.entity_id
                WHERE c.claim_id IN ({placeholders})""",
            ids,
        ).fetchall()
        updated, audit_ids = [], []
        for row in rows:
            conn.execute(
                """UPDATE entity_claims
                   SET verification_status=?, assertion_level=?, reviewed_by=?, reviewed_at=?, editor_note=?
                   WHERE claim_id=?""",
                (verdict, level, editor, now, note, row['claim_id']),
            )
            cur = conn.execute(
                """INSERT INTO en_audit_log
                   (entity_ref, action, field_name, old_value, new_value, evidence_sources,
                    authority_rank, editor, verification_status, created_at)
                   VALUES (?, 'claim_review', ?, ?, ?, ?, 'CLAIM', ?, 'verified', ?)""",
                (f"{row['canonical_label'] or row['entity_id']}|{row['claim_type']}",
                 row['predicate'], f"{row['verification_status']}/{row['assertion_level']}",
                 f"{verdict}/{level}", f"claim_id={row['claim_id']}, source_id={row['source_id']}",
                 editor, now),
            )
            updated.append(row['claim_id'])
            audit_ids.append(cur.lastrowid)
        conn.commit()
        return jsonify({"ok": True, "updated": updated, "audit_log_ids": audit_ids,
                        "audit_id": f"en-{audit_ids[-1]}" if audit_ids else None,
                        "count": len(updated)})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/resolutions/history', methods=['GET'])
def api_admin_resolutions_history():
    """GET /daoanh/api/admin/resolutions/history?page=&per_page= — T119 Gap 4 (fix T134 2026-09-14):
    lịch sử phán quyết = UNION resol_dais_log (legacy) + en_audit_log action='resolve_lineage_conflict'
    (nguồn GHI THẬT từ conflicts.html/T109). Trước fix: resolutions_log KHÔNG bao giờ được INSERT
    (0/4 code path) → tab Resolutions luôn trống dù phán quyết đã ghi vào en_audit_log."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    conn = get_db_connection()
    try:
        total = (
            conn.execute("SELECT COUNT(*) FROM en_audit_log WHERE action='resolve_lineage_conflict'").fetchone()[0]
            + conn.execute("SELECT COUNT(*) FROM resolutions_log").fetchone()[0]
        )
        rows = conn.execute(
            """WITH resolved_src AS (
                SELECT a.log_id AS rid,
                       a.entity_ref AS monk_id,
                       a.new_value AS chosen_source,
                       a.old_value AS previous_source,
                       a.evidence_sources AS notes,
                       a.editor AS resolved_by,
                       a.created_at AS resolved_at,
                       c.id AS conflict_id,
                       c.label, c.name_vi, c.person_id, c.conflict_type
                FROM en_audit_log a
                LEFT JOIN lineage_conflicts_v2 c ON c.person_id = a.entity_ref
                WHERE a.action = 'resolve_lineage_conflict'
                UNION ALL
                SELECT r.id AS rid,
                       r.monk_id, r.chosen_source, r.previous_source, r.notes, r.resolved_by,
                       r.resolved_at, r.conflict_id,
                       c2.label, c2.name_vi, c2.person_id, c2.conflict_type
                FROM resolutions_log r
                LEFT JOIN lineage_conflicts_v2 c2 ON c2.id = r.conflict_id
            )
            SELECT * FROM resolved_src
            ORDER BY resolved_at DESC, rid DESC
            LIMIT ? OFFSET ?""",
            (per_page, offset),
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "resolutions": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/feedback', methods=['GET'])
def api_admin_feedback():
    """GET /daoanh/api/admin/feedback?status=new&page= — T119 Gap 5 inbox."""
    status_f = (request.args.get('status') or '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    where, params = ["1=1"], []
    if status_f in ('new', 'ack', 'closed'):
        where.append("status=?"); params.append(status_f)
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM user_feedback WHERE {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, entity_id, entity_type, feedback_type, note_plain, user_level,
                       status, created_at
                FROM user_feedback WHERE {wc}
                ORDER BY CASE status WHEN 'new' THEN 0 ELSE 1 END, id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "feedback": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/feedback/<int:fid>/status', methods=['POST'])
def api_admin_feedback_status(fid):
    """POST /daoanh/api/admin/feedback/<id>/status — {status: ack|closed}."""
    data = request.get_json(silent=True) or {}
    st = (data.get('status') or '').strip()
    if st not in ('ack', 'closed'):
        return jsonify({"ok": False, "error": "status phải ∈ ack|closed"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE user_feedback SET status=? WHERE id=?", (st, fid))
        conn.commit()
        return jsonify({"ok": True, "id": fid, "status": st})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/audit/trail', methods=['GET'])
def api_admin_audit_trail():
    """GET /daoanh/api/admin/audit/trail?entity_ref=&page=&per_page= — T118:
    en_audit_log append-only; audit_id format en-<log_id>."""
    entity_ref = (request.args.get('entity_ref') or '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    where, params = ["1=1"], []
    if entity_ref:
        where.append("entity_ref LIKE ?"); params.append(f"%{entity_ref}%")
    wc = " AND ".join(where)
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM en_audit_log WHERE {wc}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT log_id, entity_ref, action, field_name, old_value, new_value,
                       evidence_sources, authority_rank, editor, verification_status, created_at
                FROM en_audit_log WHERE {wc}
                ORDER BY log_id DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        ).fetchall()
        out = [dict(r) | {"audit_id": f"en-{r['log_id']}"} for r in rows]
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "audits": out})
    finally:
        conn.close()


@app.route('/daoanh/api/research/entity/<entity_ref>/audit-trail', methods=['GET'])
def api_research_entity_audit_trail(entity_ref):
    """GET /daoanh/api/research/entity/<entity_ref>/audit-trail — T118 (implement trong T135, 2026-09-14):
    Audit Trail bậc Tiến sĩ (Policy Filter L3) — read-only, 0 ALTER, NO_DATA trung thực.
    Trả lịch sử thay đổi record từ en_audit_log (append-only) + audit_id SHA-256 từ
    entity_claims_audit (T109). entity_ref nhận PL… | A… | dila id; resolve qua entity_hub."""
    conn = get_db_connection()
    try:
        eid, ref = _resolve_entity_id(conn, entity_ref)
        pats = {ref, entity_ref}
        if eid is not None:
            hub = conn.execute("SELECT canonical_label FROM entity_hub WHERE entity_id=?", (eid,)).fetchone()
            if hub and hub['canonical_label']:
                pats.add(hub['canonical_label'])
        pats.discard(None)
        pats.discard('')
        pats = sorted(pats)
        same = ""
        params = []
        for p in pats:
            same += "entity_ref LIKE ? OR "
            params.append(f"%{p}%")
        same = same.rstrip(" OR ") or "0"

        history = conn.execute(f"""
            SELECT log_id, entity_ref, action, field_name, old_value, new_value,
                   evidence_sources, authority_rank, editor, verification_status, created_at
            FROM en_audit_log WHERE {same}
            ORDER BY log_id DESC LIMIT 200
        """, params).fetchall()

        claims_audit = {"total": 0, "by_status": {}, "samples": []}
        if eid is not None:
            rows = conn.execute("""
                SELECT c.claim_id, c.claim_type, c.predicate, c.object_text,
                       COALESCE(d.source_code, '') AS source_code,
                       c.verification_status, a.audit_id, c.reviewed_by, c.reviewed_at
                FROM entity_claims c
                LEFT JOIN data_sources d ON d.source_id = c.source_id
                LEFT JOIN entity_claims_audit a ON a.claim_id = c.claim_id
                WHERE c.entity_id = ?
                ORDER BY c.claim_id LIMIT 200
            """, (eid,)).fetchall()
            claims_audit["total"] = len(rows)
            for r in rows:
                claims_audit["by_status"][r["verification_status"]] = \
                    claims_audit["by_status"].get(r["verification_status"], 0) + 1
                if len(claims_audit["samples"]) < 20:
                    claims_audit["samples"].append(dict(r))
        else:
            claims_audit["note"] = "entity không resolve được qua entity_hub — chỉ trả history bằng chuỗi thô"

        return jsonify({
            "ok": True,
            "subject_id": entity_ref,
            "persona_level": "L3",
            "resolved": {"entity_hub_id": eid, "canonical": ref},
            "history": [dict(h) | {"audit_id": f"en-{h['log_id']}"} for h in history],
            "claims_audit": claims_audit,
            "data_status": "indexed" if (history or claims_audit["total"]) else "no_data"
        })
    finally:
        conn.close()


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


@app.route('/daoanh/api/public/export/citation', methods=['GET'])
def api_public_export_citation():
    """GET /daoanh/api/public/export/citation?entity_id=&format=csl-json|bibtex&audit_id=
    T118 — xuất trích dẫn chuẩn (CSL-JSON / BibTeX) cho công cụ học thuật; additive.
    Đợt 2: audit_id xuyên vào export (AUDIT_ID + evidence) + `signature` =
    sha256(entity_id|audit_id|title) — chữ ký bằng chứng, ổn định theo mọi định dạng."""
    entity_id = (request.args.get('entity_id') or '').strip()
    fmt = (request.args.get('format') or 'csl-json').strip().lower()
    audit_id = (request.args.get('audit_id') or '').strip()
    if not entity_id:
        return jsonify({"ok": False, "error": "Thiếu entity_id"}), 400
    if fmt not in ('csl-json', 'bibtex'):
        return jsonify({"ok": False, "error": "format phải ∈ csl-json|bibtex"}), 400
    info = _citation_lookup(entity_id)
    if not info:
        return jsonify({"ok": False, "error": "Không phân giải được entity"}), 404
    title = (info['title_vi'] or info['title_zh'] or entity_id)
    note_parts = [info['source_name'] or '', f"Truy cập qua Đạo Ảnh — Phật Pháp Online (phatphaponline.org)"]
    audit_detail = _audit_ref_lookup(audit_id)
    if audit_detail:
        note_parts.append(f"AUDIT_ID={audit_id}")
        if audit_detail.get('evidence_sources'):
            note_parts.append("EVIDENCE=" + str(audit_detail['evidence_sources']))
        if audit_detail.get('action'):
            note_parts.append("ACTION=" + str(audit_detail['action']))
    note = "; ".join(filter(None, note_parts))
    sig = hashlib.sha256(f"{entity_id}|{audit_id or ''}|{title}".encode('utf-8')).hexdigest()
    year = None
    if info.get('dynasty'):
        m = re.search(r'(\d{4})', str(info['dynasty']))
        if m:
            year = int(m.group(1))
    if fmt == 'csl-json':
        csl = {
            "id": audit_id or f"daoanh:{entity_id}",
            "type": "document" if info['entity_type'] == 'person' else "article",
            "title": title,
            "language": "vi",
            "publisher": "Phật Pháp Online — Bản địa Đạo Ảnh",
            "note": note,
            "signature": sig,
        }
        if audit_detail:
            csl["audit"] = {
                "audit_id": audit_id,
                "entity_ref": audit_detail.get('entity_ref'),
                "action": audit_detail.get('action'),
                "editor": audit_detail.get('editor'),
                "authority_rank": audit_detail.get('authority_rank'),
                "verification_status": audit_detail.get('verification_status'),
                "evidence_sources": audit_detail.get('evidence_sources'),
                "created_at": audit_detail.get('created_at'),
            }
        if year:
            csl["issued"] = {"date-parts": [[year]]}
        return jsonify({"ok": True, "format": "csl-json", "citation": [csl], "signature": sig})
    title_b = title.replace('\\', '\\\\').replace('"', '\\"')
    note_b = note.replace('\\', '\\\\').replace('"', '\\"')
    bib = (
        f"@misc{{{audit_id or entity_id},\n"
        f"  title = {{{title_b}}},\n"
        f"  howpublished = {{Phật Pháp Online — Bản địa Đạo Ảnh (phatphaponline.org/daoanh/)}},\n"
        f"  note = {{{note_b}}} {{SIG={sig}}}{',\n  year = {%d}' % year if year else ''}\n"
        f"}}\n"
    )
    return jsonify({"ok": True, "format": "bibtex", "citation": bib, "signature": sig})


@app.route('/daoanh/api/admin/geo-enrich/candidates', methods=['GET'])
def api_admin_geo_enrich_candidates():
    """GET /daoanh/api/admin/geo-enrich/candidates?page=&per_page= — T121:
    địa danh chưa có geo_cross_ref (candidate enrich từ Wikidata P625/P2044)."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)
    offset = (page - 1) * per_page
    conn = get_db_connection()
    try:
        wc = "WHERE g.id IS NULL OR g.enrich_status IN ('candidate', 'rejected')"
        total = conn.execute(
            f"SELECT COUNT(*) FROM places_dila pd LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id {wc}"
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT pd.id AS dila_id, pd.name, pd.name_zh, pd.geo_lat, pd.geo_long,
                       g.wikidata_qid, g.enrich_status, g.enrich_source_qid, g.enrich_lat,
                       g.enrich_lon, g.enrich_elevation_m, g.notes, g.confidence
                FROM places_dila pd
                LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id
                {wc}
                ORDER BY g.enrich_status DESC, pd.id
                LIMIT ? OFFSET ?""",
            (per_page, offset),
        ).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "candidates": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/geo-enrich', methods=['POST'])
def api_admin_geo_enrich_approve():
    """POST /daoanh/api/admin/geo-enrich — {dila_id, wikidata_qid, lat, lon, elevation_m?, source_url?}
    T121 — Admin xác nhận: upsert geo_cross_ref main fields, status='approved'."""
    data = request.get_json(silent=True) or {}
    dila_id = (data.get('dila_id') or '').strip()
    qid = (data.get('wikidata_qid') or '').strip()
    if not dila_id:
        return jsonify({"ok": False, "error": "Thiếu dila_id"}), 400
    try:
        lat = float(data.get('lat')) if data.get('lat') is not None else None
        lon = float(data.get('lon')) if data.get('lon') is not None else None
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "lat/lon phải là số"}), 400
    elev = data.get('elevation_m')
    if elev is not None:
        try:
            elev = int(float(elev))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "elevation_m phải là số"}), 400
    notes = (data.get('source_url') or '').strip()[:300]
    conn = get_db_connection()
    try:
        try:
            conn.execute(
                """INSERT INTO geo_cross_ref
                   (dila_id, wikidata_qid, notes, confidence, mapped_by,
                    wikidata_lat, wikidata_lon, elevation_m, elevation_source, enrich_status)
                   VALUES (?, ?, ?, 'verified', 'admin', ?, ?, ?, 'wikidata', 'approved')
                   ON CONFLICT(dila_id) DO UPDATE SET
                       wikidata_qid=excluded.wikidata_qid,
                       wikidata_lat=excluded.wikidata_lat,
                       wikidata_lon=excluded.wikidata_lon,
                       elevation_m=excluded.elevation_m,
                       elevation_source=excluded.elevation_source,
                       enrich_status='approved', confidence='verified',
                       mapped_by=excluded.mapped_by, notes=excluded.notes""",
                (dila_id, qid, notes, lat, lon, elev),
            )
        except sqlite3.OperationalError:
            row = conn.execute("SELECT id FROM geo_cross_ref WHERE dila_id=?", (dila_id,)).fetchone()
            if row:
                conn.execute(
                    """UPDATE geo_cross_ref SET wikidata_qid=?, notes=?, confidence='verified',
                       mapped_by='admin', wikidata_lat=?, wikidata_lon=?, elevation_m=?,
                       elevation_source='wikidata', enrich_status='approved' WHERE dila_id=?""",
                    (qid, notes, lat, lon, elev, dila_id),
                )
            else:
                conn.execute(
                    """INSERT INTO geo_cross_ref
                       (dila_id, wikidata_qid, notes, confidence, mapped_by,
                        wikidata_lat, wikidata_lon, elevation_m, elevation_source, enrich_status)
                       VALUES (?, ?, ?, 'verified', 'admin', ?, ?, ?, 'wikidata', 'approved')""",
                    (dila_id, qid, notes, lat, lon, elev),
                )
        conn.commit()
        return jsonify({"ok": True, "dila_id": dila_id, "wikidata_qid": qid, "status": "approved"})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/geo-enrich/<int:rid>/status', methods=['POST'])
def api_admin_geo_enrich_status(rid):
    """POST /daoanh/api/admin/geo-enrich/<id>/status — {status: rejected|candidate|approved}."""
    data = request.get_json(silent=True) or {}
    st = (data.get('status') or '').strip()
    if st not in ('rejected', 'candidate', 'approved'):
        return jsonify({"ok": False, "error": "status phải ∈ rejected|candidate|approved"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE geo_cross_ref SET enrich_status=?, confidence=? WHERE id=?",
                     (st, 'verified' if st == 'approved' else 'candidate', rid))
        conn.commit()
        return jsonify({"ok": True, "id": rid, "status": st})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/editor-stats', methods=['GET'])
def api_admin_editor_stats():
    """GET /daoanh/api/admin/editor-stats — T119/T112/T121: thanh stats editor-dashboard."""
    conn = get_db_connection()
    try:
        claims_total = conn.execute("SELECT COUNT(*) FROM entity_claims").fetchone()[0]
        claims_unverified = conn.execute(
            "SELECT COUNT(*) FROM entity_claims WHERE verification_status IN ('unverified', '')"
        ).fetchone()[0]
        claims_verified = conn.execute(
            "SELECT COUNT(*) FROM entity_claims WHERE verification_status = 'verified'"
        ).fetchone()[0]
        conflicts_open = conn.execute(
            "SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 0"
        ).fetchone()[0]
        resolutions_total = conn.execute("SELECT COUNT(*) FROM resolutions_log").fetchone()[0]
        gaps_new = conn.execute("SELECT COUNT(*) FROM data_gap_requests WHERE status='new'").fetchone()[0]
        feedback_new = conn.execute("SELECT COUNT(*) FROM user_feedback WHERE status='new'").fetchone()[0]
        geo_candidates = conn.execute(
            "SELECT COUNT(*) FROM places_dila pd LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id WHERE g.id IS NULL OR g.enrich_status IN ('candidate', 'rejected')"
        ).fetchone()[0]
        bio_pending = conn.execute(
            "SELECT COUNT(*) FROM person_bio_vi_draft WHERE admin_approved = 0"
        ).fetchone()[0]
        return jsonify({"ok": True,
                        "claims_total": claims_total, "claims_unverified": claims_unverified,
                        "claims_verified": claims_verified, "conflicts_open": conflicts_open,
                        "resolutions_total": resolutions_total, "gaps_new": gaps_new,
                        "feedback_new": feedback_new, "geo_candidates": geo_candidates,
                        "bio_pending": bio_pending})
    finally:
        conn.close()


# ── T73: Bio Review (person_bio_vi_draft) ───────────────────────
@app.route('/daoanh/api/admin/bio-review/pending', methods=['GET'])
def api_admin_bio_review_pending():
    """GET /daoanh/api/admin/bio-review/pending?status=pending|approved|all&page=&per_page=
    T73 — hàng chờ bio_vi_draft (2,093 row) cho admin duyệt; Zero-RAM LIMIT/OFFSET."""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 100)
    offset = (page - 1) * per_page
    st = (request.args.get('status') or 'pending').strip().lower()
    status_map = {'pending': 'admin_approved = 0', 'approved': "admin_approved = 1",
                  'all': '1=1', 'rejected': "admin_approved < 0"}
    wc = status_map.get(st, status_map['pending'])
    conn = get_db_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM person_bio_vi_draft WHERE {wc}").fetchone()[0]
        rows = conn.execute(
            f"""SELECT d.person_id, p.name_zh AS person_name_zh, p.name_vi AS person_name_vi,
                       d.name_vi, d.bio_vi_draft, d.source_lex_id, d.source_name, d.match_type,
                       d.char_count, d.admin_approved, d.admin_note, d.updated_at,
                       (p.bio_vi IS NOT NULL AND p.bio_vi <> '') AS has_bio_vi
                FROM person_bio_vi_draft d
                LEFT JOIN people p ON p.id = d.person_id
                WHERE {wc}
                ORDER BY d.updated_at DESC LIMIT ? OFFSET ?""",
            [per_page, offset]).fetchall()
        return jsonify({"ok": True, "total": total, "page": page, "per_page": per_page,
                        "drafts": [dict(r) for r in rows]})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/bio-review/<person_id>', methods=['POST'])
def api_admin_bio_review(person_id):
    """POST /daoanh/api/admin/bio-review/<person_id> — body {action, note?, editor?}
    T73 — approve (admin_approved=1) / reject (-1) 1 draft + ghi en_audit_log.
    KHÔNG tự ghi people.bio_vi — bước apply tách biệt (HITL 2 bước)."""
    body = request.get_json(silent=True) or {}
    action = (body.get('action') or '').strip().lower()
    note = (body.get('note') or '').strip()[:255]
    editor = (body.get('editor') or 'admin').strip()[:64]
    if action not in ('approve', 'reject'):
        return jsonify({"ok": False, "error": "action phải ∈ approve|reject"}), 400
    flag = 1 if action == 'approve' else -1
    conn = get_db_connection()
    try:
        r = conn.execute("SELECT bio_vi_draft, source_name FROM person_bio_vi_draft WHERE person_id=?",
                         (person_id,)).fetchone()
        if not r:
            return jsonify({"ok": False, "error": "Không có draft cho person này"}), 404
        conn.execute(
            "UPDATE person_bio_vi_draft SET admin_approved=?, admin_note=?, "
            "updated_at=? WHERE person_id=?",
            (flag, note, datetime.now().isoformat(timespec='seconds'), person_id))
        conn.execute(
            "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor)"
            " VALUES (?, ?, 'bio_vi_draft', ?, ?, ?)",
            (person_id, 'bio_review_' + action, 'unreviewed', str(flag), editor))
        conn.commit()
        return jsonify({"ok": True, "person_id": person_id, "action": action, "status": flag})
    finally:
        conn.close()


@app.route('/daoanh/api/admin/bio-review/apply', methods=['POST'])
def api_admin_bio_review_apply():
    """POST /daoanh/api/admin/bio-review/apply — body {person_ids: [...], editor?}
    T73 — ADMIN chỉ định danh sách đã-approved → copy bio_vi_draft vào people.bio_vi
    (chỉ khi khác giá trị hiện tại) + ghi en_audit_log bio_apply. Data edit HITL."""
    body = request.get_json(silent=True) or {}
    ids = [str(i) for i in (body.get('person_ids') or [])][:200]
    editor = (body.get('editor') or 'admin').strip()[:64]
    if not ids:
        return jsonify({"ok": False, "error": "person_ids rỗng"}), 400
    ph = ",".join("?" * len(ids))
    conn = get_db_connection()
    try:
        rows = conn.execute(
            f"SELECT person_id, bio_vi_draft FROM person_bio_vi_draft "
            f"WHERE admin_approved = 1 AND person_id IN ({ph})", ids).fetchall()
        applied, skipped = 0, 0
        for r in rows:
            cur = conn.execute("SELECT bio_vi FROM people WHERE id=?", (r['person_id'],)).fetchone()
            if cur and cur['bio_vi'] == r['bio_vi_draft']:
                skipped += 1
                continue
            conn.execute("UPDATE people SET bio_vi=? WHERE id=?",
                         (r['bio_vi_draft'], r['person_id']))
            conn.execute(
                "INSERT INTO en_audit_log (entity_ref, action, field_name, old_value, new_value, editor)"
                " VALUES (?, 'bio_apply', 'bio_vi', ?, ?, ?)",
                (r['person_id'], (cur['bio_vi'] or '') if cur else '', r['bio_vi_draft'], editor))
            applied += 1
        conn.commit()
        return jsonify({"ok": True, "applied": applied, "skipped": skipped})
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


@app.route('/daoanh/api/v1/entity/<entity_id>/lookup', methods=['GET'])
def api_v1_entity_lookup(entity_id):
    """GET /daoanh/api/v1/entity/<entity_id>/lookup — 5-layer unified lookup.
    Reuse tables hoàn toàn (T120 spec: 'Không tạo bảng mới'). Read-only, Zero-RAM.
    ?live=1: fetch Wikidata on-demand (Phase A). HITL: chỉ trả data candidate, KHÔNG ghi DB.
    """
    conn = get_db_connection()
    live = request.args.get('live', '0') == '1'
    live_result = None
    try:
        found = {}
        sources_used = []
        confidence = 0.0

        # Layer 1 — DILA core: entity_hub / entity + namevi_map_places + places/places_dila
        hub = conn.execute(
            "SELECT entity_id, canonical_label, entity_type FROM entity_hub WHERE entity_id = ?",
            (entity_id,)
        ).fetchone()
        if not hub:
            hub = conn.execute(
                "SELECT entity_id, alias_zh AS canonical_label, alias_vi AS canonical_name_vi, entity_type "
                "FROM entity WHERE entity_id = ?",
                (entity_id,)
            ).fetchone()
        if hub:
            core = {
                "entity_id": entity_id,
                "canonical_name_zh": hub['canonical_label'],
                "entity_type": hub['entity_type'],
            }
            vi_row = conn.execute(
                "SELECT name_vi FROM namevi_map_places WHERE dila_id = ? OR name_zh = ? LIMIT 1",
                (entity_id, hub['canonical_label'] or '')
            ).fetchone()
            core["canonical_name_vi"] = vi_row['name_vi'] if vi_row else hub.get('canonical_name_vi')
            found['core'] = core
            sources_used.append('dila')
            confidence += 0.5
            if core.get('canonical_name_vi'):
                confidence += 0.1

            # DILA geo detail (places_dila, fallback places theo short/long ID)
            dila = conn.execute(
                "SELECT name_zh, geo_lat, geo_long, note, district, note_category FROM places_dila "
                "WHERE id = ?",
                (entity_id,)
            ).fetchone()
            if not dila or not dila['geo_lat']:
                dila = None
            places_fb = None
            if not dila:
                places_fb = conn.execute(
                    "SELECT name_zh, gps_lat, gps_long, province FROM places WHERE id = ?",
                    (entity_id,)
                ).fetchone()
            if dila and dila['geo_lat']:
                found['dila'] = {
                    "name_zh": dila['name_zh'],
                    "geo_lat": dila['geo_lat'],
                    "geo_long": dila['geo_long'],
                    "district": dila['district'],
                    "note": dila['note'],
                    "conf": 1.0,
                }
                found['core'].setdefault('geo_lat', dila['geo_lat'])
                found['core'].setdefault('geo_long', dila['geo_long'])
            elif places_fb and (places_fb['gps_lat'] or places_fb['gps_long']):
                found['dila'] = {
                    "name_zh": places_fb['name_zh'],
                    "geo_lat": places_fb['gps_lat'],
                    "geo_long": places_fb['gps_long'],
                    "district": places_fb['province'],
                    "conf": 1.0,
                }
                found['core'].setdefault('geo_lat', places_fb['gps_lat'])
                found['core'].setdefault('geo_long', places_fb['gps_long'])

        # Layer 2 — Wikidata ref: geo_cross_ref bridge (đã có 181 QID, candidate T121)
        gcr = conn.execute(
            "SELECT wikidata_qid, bdrc_id, confidence, mapped_by FROM geo_cross_ref WHERE dila_id = ?",
            (entity_id,)
        ).fetchone()
        if gcr:
            wd = {"qid": gcr['wikidata_qid'], "mapped_by": gcr['mapped_by'], "conf": gcr['confidence']}
            if gcr['bdrc_id']:
                wd['bdrc_id'] = gcr['bdrc_id']
            found['wikidata_ref'] = wd
            confidence += (0.2 if gcr['confidence'] == 'verified' else 0.1)
            if gcr['wikidata_qid']:
                sources_used.append('wikidata_ref')
                # T120 Phase A — live Wikidata fetch (HITL-safe: no DB write, candidate in response only)
                if live and gcr['wikidata_qid']:
                    live_result = _t120_query_wikidata(gcr['wikidata_qid'])
                    if live_result:
                        found['wikidata_live'] = {
                            "qid": live_result['qid'],
                            "label_vi": live_result.get('label_vi'),
                            "label_zh": live_result.get('label_zh'),
                            "lat": live_result.get('lat'),
                            "lon": live_result.get('lon'),
                            "elevation_m": live_result.get('elevation_m'),
                            "status": "candidate",
                            "wiki": {k: v for k, v in live_result.items() if k.startswith('wiki_')},
                        }
                        sources_used.append('wikidata_live')
                        confidence += 0.15

        # Layer 3 — Wikipedia cache: place_wiki_snapshots
        wiki = conn.execute(
            "SELECT wiki_title, wiki_url, snippet, source, created_at FROM place_wiki_snapshots "
            "WHERE place_id = ?",
            (entity_id,)
        ).fetchone()
        if wiki:
            found['wikipedia'] = {
                "title": wiki['wiki_title'],
                "url": wiki['wiki_url'],
                "snippet": (wiki['snippet'] or '')[:500],
                "lang": wiki['source'],
                "cached_at": wiki['created_at'],
            }
            sources_used.append('wikipedia_cache')
            confidence += 0.1

        # Layer 4 — Web enrichment: web_enrichment_cache (verified/cached)
        enrich = conn.execute(
            "SELECT id, source_name, source_url, summary_vi, status, created_at "
            "FROM web_enrichment_cache WHERE entity_id = ? AND status != 'rejected' "
            "ORDER BY CASE WHEN status='verified' THEN 0 ELSE 1 END, id DESC LIMIT 1",
            (entity_id,)
        ).fetchone()
        if enrich:
            found['web_enrichment'] = {
                "enrichment_id": enrich['id'],
                "source_name": enrich['source_name'],
                "source_url": enrich['source_url'],
                "summary_vi": (enrich['summary_vi'] or '')[:800],
                "status": enrich['status'],
                "cached_at": enrich['created_at'],
            }
            sources_used.append('web_enrichment')
            confidence += (0.1 if enrich['status'] == 'verified' else 0.05)

        # Layer 5 — Wikidata QID → Wikipedia name variant hint (bridge đã có trong geo_cross_ref)
        if gcr and gcr['wikidata_qid']:
            found.setdefault('name_variant', {})['wikidata'] = {
                "qid": gcr['wikidata_qid']}

        if not found:
            return jsonify({"ok": False, "error": "Entity not found in any lookup layer"}), 404

        resp = {
            "ok": True,
            "entity_id": entity_id,
            "sources_used": sources_used,
            "confidence": round(min(confidence, 1.0), 2),
            "data": found,
        }
        # T120 Phase A — live mode metadata (no DB write, HITL-safe)
        if live:
            resp["live"] = True
            resp["live_unavailable"] = (live_result is None and bool(gcr and gcr['wikidata_qid']))
            if resp["live_unavailable"]:
                resp["live_error"] = "network_timeout_or_blocked"
        return resp
    finally:
        conn.close()


# ── Admin: LLM key management ────────────────────────────────

@app.route('/daoanh/api/admin/llm/status', methods=['GET'])
def api_admin_llm_status():
    """GET /daoanh/api/admin/llm/status — Trạng thái Groq key hiện tại."""
    cfg = _llm_config_read()
    return jsonify({
        'ok': True,
        'status': cfg.get('status', 'unknown'),
        'last_error': cfg.get('last_error'),
        'last_error_at': cfg.get('last_error_at'),
        'model': cfg.get('groq_model') or GROQ_MODEL,
        'has_custom_key': bool(cfg.get('groq_key')),
    })


@app.route('/daoanh/api/admin/llm/key', methods=['POST'])
def api_admin_llm_update_key():
    """POST /daoanh/api/admin/llm/key — Admin cập nhật Groq key.
    Body: {key: '<new_key>', model: '<optional_model>'}
    """
    body = request.get_json(silent=True) or {}
    new_key = (body.get('key') or '').strip()
    model = (body.get('model') or '').strip()
    if not new_key:
        return jsonify({'ok': False, 'error': 'Thiếu key'}), 400
    update = {'groq_key': new_key, 'status': 'unknown', 'last_error': None, 'last_error_at': None}
    if model:
        update['groq_model'] = model
    _llm_config_write(update)
    return jsonify({'ok': True, 'message': 'Key đã được cập nhật. Sẽ có hiệu lực ở lần dịch tiếp theo.'})


# ============================================================
#  T95 Phase C — CBETA Translation Jobs (batch Groq worker)
#  POST tạo job → thread nền worker_run; progress/jobs đọc từ DB.
#  CLI tương đương: scripts/cbeta_translate_worker.py run --job <id>
# ============================================================

def _t95_worker():
    import importlib
    return importlib.import_module('scripts.cbeta_translate_worker')


@app.route('/daoanh/api/translation/jobs', methods=['GET', 'POST'])
def api_t95_jobs():
    """POST: tạo + chạy job dịch (body: work_id, scope, run_now, mock).
    GET: danh sách job gần đây (query: limit)."""
    if request.method == 'POST':
        import threading
        body = request.get_json(silent=True) or {}
        work_id = (body.get('work_id') or 'T50n2060').strip()
        scope = (body.get('scope') or 'untranslated').strip()
        run_now = bool(body.get('run_now', True))
        mock = bool(body.get('mock', False))
        w = _t95_worker()
        try:
            job_id = w.create_job(work_id, scope=scope)
        except Exception as e:
            app.logger.warning(f'[T95] create_job lỗi: {e}')
            return jsonify({'ok': False, 'error': f'Lỗi tạo job: {e}'}), 400
        if job_id and run_now:
            thread = threading.Thread(target=w.worker_run, args=(job_id,),
                                      kwargs={'mock': mock}, daemon=True)
            thread.start()
            app.logger.info(f'[T95] job {job_id} khởi chạy thread nền')
        return jsonify({'ok': True, 'job_id': job_id, 'running': bool(job_id and run_now)})
    # GET list
    w = _t95_worker()
    con = w._con()
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        rows = con.execute(
            "SELECT job_id, work_id, status, requested_scope, total_passages, "
            "completed_passages, failed_passages, created_at, started_at, finished_at, last_error "
            "FROM translation_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return jsonify({'ok': True, 'jobs': [dict(r) for r in rows]})
    finally:
        con.close()


@app.route('/daoanh/api/translation/jobs/<job_id>')
def api_t95_job_detail(job_id):
    """GET: chi tiết job + item gần nhất + phân bố trạng thái (query: items)."""
    w = _t95_worker()
    con = w._con()
    try:
        j = con.execute("SELECT * FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not j:
            return jsonify({'ok': False, 'error': 'job không tồn tại'}), 404
        items_n = min(int(request.args.get('items', 20)), 200)
        items = con.execute(
            "SELECT ji.passage_id, ji.sequence_no, ji.status, ji.attempt_count, "
            "ji.error_message, ji.completed_at, "
            "(SELECT ts.translation_id FROM translation_segments ts "
            " WHERE ts.passage_id = ji.passage_id AND ts.translation_status <> 'superseded' "
            " ORDER BY ts.revision_no DESC LIMIT 1) AS translation_id "
            "FROM translation_job_items ji WHERE ji.job_id=? ORDER BY ji.sequence_no DESC LIMIT ?",
            (job_id, items_n)).fetchall()
        cnt = con.execute(
            "SELECT status, COUNT(*) n FROM translation_job_items WHERE job_id=? GROUP BY status",
            (job_id,)).fetchall()
        return jsonify({'ok': True, 'job': dict(j),
                        'items': [dict(r) for r in items],
                        'counts': {r['status']: r['n'] for r in cnt}})
    finally:
        con.close()


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


@app.route('/daoanh/api/cbeta/passages/<int:legacy_id>/units')
def api_t95_units(legacy_id):
    """GET: units (text_passages) của 1 passage CBETA theo legacy_id + bản dịch + coverage."""
    work_id = (request.args.get('work_id') or 'T50n2060').strip()
    con = get_db()
    try:
        rows = con.execute(_T95_UNITS_SQL, (work_id, legacy_id)).fetchall()
        units = [_t95_badge(dict(r)) for r in rows]
        ln = con.execute("SELECT passage_id, text_id, loc_ref, raw_text FROM passage WHERE passage_id=?",
                         (legacy_id,)).fetchone()
        legacy = dict(ln) if ln else {}
        cov = _t95_coverage(con, work_id)
        return jsonify({'ok': True, 'work_id': work_id, 'legacy': legacy,
                        'units': units, 'coverage': cov})
    finally:
        con.close()


@app.route('/daoanh/api/cbeta/works/<work_id>/coverage')
def api_t95_work_coverage(work_id):
    """GET: coverage tích lũy của 1 tác phẩm (dùng cho header progress + Phase E export)."""
    con = get_db()
    try:
        return jsonify({'ok': True, 'work_id': work_id, 'coverage': _t95_coverage(con, work_id)})
    finally:
        con.close()


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


@app.route('/daoanh/api/cbeta/works/<work_id>/translation-export')
def api_t95_translation_export(work_id):
    """GET: export tích lũy toàn tác phẩm (JSON streaming).
    Query: ?download=1 → Content-Disposition attachment; ?format=md → Markdown."""
    con = get_db()
    fmt = (request.args.get('format') or 'json').lower()
    if fmt == 'md':
        try:
            cov = _t95_coverage(con, work_id)
            return _t95_export_markdown(con, work_id, cov)
        finally:
            con.close()

    def stream():
        try:
            cov = _t95_coverage(con, work_id)
            for part in _t95_export_iter(con, work_id, cov):
                yield part
        finally:
            con.close()

    resp = Response(stream(), mimetype='application/json; charset=utf-8')
    if request.args.get('download'):
        resp.headers['Content-Disposition'] = f"attachment; filename={work_id}_translation_export.json"
    return resp


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


@app.route('/daoanh/api/admin/translation/jobs')
def api_t95_admin_jobs():
    """GET: ds job dịch + tổng hợp (admin monitor) + số file raw audit mỗi job."""
    w = _t95_worker()
    con = w._con()
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        rows = con.execute(_T95_JOBS_LIST_SQL + ' LIMIT ?', (limit,)).fetchall()
        jobs = []
        for r in rows:
            d = dict(r)
            d['raw_audit'] = len(os.listdir(_t95_raw_dir(d['job_id']))) if os.path.isdir(_t95_raw_dir(d['job_id'])) else 0
            d['progress_percent'] = round(d['done_items'] * 100.0 / d['item_total']) if d['item_total'] else 0
            jobs.append(d)
        return jsonify({'ok': True, 'jobs': jobs})
    finally:
        con.close()


@app.route('/daoanh/api/admin/translation/jobs/<job_id>/raw')
def api_t95_admin_job_raw(job_id):
    """GET: danh sách file raw audit của 1 job (admin only, không đọc nội dung)."""
    d = _t95_raw_dir(job_id)
    if not os.path.isdir(d):
        return jsonify({'ok': True, 'files': []})
    files = []
    for name in sorted(os.listdir(d)):
        try:
            st = os.stat(os.path.join(d, name))
            files.append({'name': name, 'size': st.st_size, 'modified': datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')})
        except OSError:
            continue
    return jsonify({'ok': True, 'job_id': job_id, 'files': files})


@app.route('/daoanh/api/admin/translation/jobs/<job_id>/resume', methods=['POST'])
def api_t95_admin_job_resume(job_id):
    """POST: resume job — requeue toàn bộ item failed (reset attempt) rồi chạy lại worker nền."""
    import threading
    w = _t95_worker()
    con = w._con()
    try:
        job = con.execute("SELECT job_id, status, total_passages FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not job:
            return jsonify({'ok': False, 'error': f'Không tìm thấy job {job_id}'}), 404
        if job['status'] in ('completed', 'running', 'cancelled'):
            return jsonify({'ok': False, 'error': f'Job ở trạng thái {job["status"]} — chỉ resume khi paused/failed.'}), 400
        now = datetime.now().isoformat(timespec='seconds')
        con.execute("UPDATE translation_job_items SET status='queued', attempt_count=0, error_message=NULL, "
                    "started_at=NULL, completed_at=NULL WHERE job_id=? AND status IN ('failed','error')",
                    (job_id,))
        con.execute("UPDATE translation_jobs SET status='paused', finished_at=NULL, last_error=NULL, updated_at=? WHERE job_id=?",
                    (now, job_id))
        con.commit()
        remaining = con.execute("SELECT COUNT(*) FROM translation_job_items WHERE job_id=? AND status IN ('queued','running')",
                                (job_id,)).fetchone()[0]
        if remaining == 0:
            return jsonify({'ok': True, 'job_id': job_id, 'message': 'Không còn item để resume.'})
        thread = threading.Thread(target=w.worker_run, args=(job_id,), kwargs={'mock': False}, daemon=True)
        thread.start()
        app.logger.info(f'[T95/admin] resume job {job_id} — {remaining} item được requeue')
        return jsonify({'ok': True, 'job_id': job_id, 'resumed': remaining})
    finally:
        con.close()


@app.route('/daoanh/api/admin/translation/jobs/<job_id>/cancel', methods=['POST'])
def api_t95_admin_job_cancel(job_id):
    """POST: cancel job — hủy các item còn queued/running (đã dịch vẫn giữ)."""
    w = _t95_worker()
    con = w._con()
    try:
        job = con.execute("SELECT job_id, status FROM translation_jobs WHERE job_id=?", (job_id,)).fetchone()
        if not job:
            return jsonify({'ok': False, 'error': f'Không tìm thấy job {job_id}'}), 404
        now = datetime.now().isoformat(timespec='seconds')
        changed = con.execute("UPDATE translation_job_items SET status='cancelled', completed_at=? "
                              "WHERE job_id=? AND status IN ('queued','running')", (now, job_id)).rowcount
        if job['status'] == 'running':
            con.execute("UPDATE translation_jobs SET status='cancelled', finished_at=?, updated_at=? WHERE job_id=?",
                        (now, now, job_id))
        con.commit()
        return jsonify({'ok': True, 'job_id': job_id, 'cancelled_items': changed})
    finally:
        con.close()


# ============================================================
# T94 Phase 3 — Duyệt chuẩn thủ công (manual_verified alignment)
#   Admin verify 1 segment → quality_status='reviewed',
#   review_status='verified' + passage_translation_alignment manual_verified
# ============================================================

@app.route('/daoanh/api/admin/translation/verify', methods=['POST'])
def api_t94_admin_verify_translation():
    """POST: admin duyệt chuẩn thủ công 1 segment đã dịch.

    Body JSON:
      passage_id (bắt buộc) — id text_passages (unit) đã có bản dịch hiện hành
      reviewer   (tùy chọn, mặc định 'admin')
      note       (tùy chọn)  — ghi chú duyệt

    Idempotent: bản dịch cũ vẫn giữ; ghi đè manual_verified cũ cho (passage, translation).
    Rollback thủ công: xóa dòng passage_translation_alignment manual_verified
      + UPDATE translation_segments SET quality_status=NULL, review_status='pending', reviewer=NULL
        WHERE translation_id=<tid>.
    """
    dta = request.get_json(silent=True) or {}
    passage_id = (dta.get('passage_id') or '').strip()
    reviewer = (dta.get('reviewer') or 'admin').strip()
    note = (dta.get('note') or '').strip()
    if not passage_id:
        return jsonify({'ok': False, 'error': 'Thiếu passage_id.'}), 400
    con = get_db()
    try:
        ts = con.execute(
            "SELECT translation_id, translation_status FROM translation_segments "
            "WHERE passage_id=? AND translation_status <> 'superseded' "
            "ORDER BY revision_no DESC LIMIT 1", (passage_id,)).fetchone()
        if not ts:
            return jsonify({'ok': False,
                            'error': 'Không tìm thấy bản dịch hiện hành cho passage này.'}), 404
        tid = ts['translation_id']
        now = datetime.now().isoformat(timespec='seconds')
        con.execute(
            "UPDATE translation_segments SET quality_status='reviewed', review_status='verified', "
            "reviewer=?, updated_at=? WHERE translation_id=?",
            (reviewer, now, tid))
        con.execute(
            "DELETE FROM passage_translation_alignment WHERE passage_id=? AND translation_id=? "
            "AND alignment_type='manual_verified'", (passage_id, tid))
        con.execute(
            "INSERT INTO passage_translation_alignment "
            "(passage_id, translation_id, alignment_type, confidence, alignment_method, "
            " review_status, reviewer, note, created_at) "
            "VALUES (?,?,'manual_verified',1.0,'manual_admin_verify','verified',?,?,?)",
            (passage_id, tid, reviewer, note or 'Duyệt chuẩn thủ công', now))
        con.commit()
        app.logger.info(f'[T94] duyệt chuẩn translation {tid} cho passage {passage_id} bởi {reviewer}')
        return jsonify({'ok': True, 'translation_id': tid, 'passage_id': passage_id,
                        'reviewer': reviewer, 'manual_verified': True})
    except Exception as e:
        con.rollback()
        app.logger.warning(f'[T94] verify translation lỗi: {e}')
        return jsonify({'ok': False, 'error': f'Lỗi khi duyệt chuẩn: {e}'}), 500
    finally:
        con.close()


# ============================================================
# T96 — Per-Segment Translation APIs
# ============================================================

@app.route('/daoanh/api/segments/<path:canonical_ref>', methods=['GET'])
def api_segments_list(canonical_ref):
    """GET /daoanh/api/segments/<canonical_ref>
    Trả về tất cả text_passages segments cho 1 canonical_ref (loc_ref),
    kèm trạng thái bản dịch từng segment từ translation_segments.

    canonical_ref: e.g. "0-0457a-" (URL-encoded khi cần)
    """
    conn = get_db_connection()
    try:
        segs = conn.execute(
            """SELECT tp.passage_id, tp.sequence_no, tp.original_zh,
                      ts.translation_id, ts.translation_text AS translation_vi,
                      ts.translation_status, ts.model_name, ts.updated_at
               FROM text_passages tp
               LEFT JOIN translation_segments ts
                 ON ts.passage_id = tp.passage_id
                 AND ts.language = 'vi'
                 AND ts.translation_status NOT IN ('failed', 'superseded')
               WHERE tp.canonical_ref = ?
               ORDER BY tp.sequence_no""",
            (canonical_ref,)
        ).fetchall()
        if not segs:
            return jsonify({'ok': False, 'error': 'Không tìm thấy segments cho canonical_ref này'}), 404
        items = []
        done_count = 0
        for s in segs:
            status = s['translation_status'] or 'pending'
            if status == 'done':
                done_count += 1
            items.append({
                'passage_id': s['passage_id'],
                'sequence_no': s['sequence_no'],
                'original_zh': s['original_zh'],
                'translation_id': s['translation_id'],
                'translation_vi': s['translation_vi'],
                'translation_status': status,
                'model_name': s['model_name'],
                'updated_at': s['updated_at'],
            })
        return jsonify({
            'ok': True,
            'canonical_ref': canonical_ref,
            'total': len(items),
            'translated': done_count,
            'segments': items,
        })
    finally:
        conn.close()


@app.route('/daoanh/api/segments/translate', methods=['POST'])
def api_segment_translate():
    """POST /daoanh/api/segments/translate
    Dịch 1 segment text_passages bằng Groq. Lưu vào translation_segments.
    Body: {"passage_id": "daoanh:cbeta:T50n2060:0457a:p0001"}
    Dedup: nếu đã có bản dịch status=done thì trả ngay, không gọi API.
    """
    cfg = _llm_config_read()
    _groq_key = cfg.get('groq_key') or GROQ_KEY
    _groq_model = cfg.get('groq_model') or GROQ_MODEL
    if not _groq_key:
        return jsonify({'ok': False, 'error': 'GROQ_API_KEY chưa cấu hình'}), 503
    body = request.get_json(silent=True) or {}
    passage_id = (body.get('passage_id') or '').strip()
    if not passage_id:
        return jsonify({'ok': False, 'error': 'Thiếu passage_id'}), 400
    conn = get_db_connection()
    try:
        seg = conn.execute(
            "SELECT passage_id, sequence_no, canonical_ref, original_zh, work_id "
            "FROM text_passages WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not seg:
            return jsonify({'ok': False, 'error': 'Không tìm thấy passage_id trong text_passages'}), 404
        zh_text = (seg['original_zh'] or '').strip()
        if not zh_text:
            return jsonify({'ok': False, 'error': 'Segment không có nội dung Hán văn'}), 404
        # Dedup: kiểm tra đã có bản dịch done chưa
        existing = conn.execute(
            "SELECT translation_id, translation_text, translation_status FROM translation_segments "
            "WHERE passage_id = ? AND language = 'vi' AND translation_status = 'done' "
            "ORDER BY created_at DESC LIMIT 1", (passage_id,)
        ).fetchone()
        if existing:
            return jsonify({
                'ok': True, 'from_cache': True,
                'passage_id': passage_id,
                'translation_id': existing['translation_id'],
                'translation_vi': existing['translation_text'],
                'status': 'done',
            })
        # Dedup: đang queued/translating?
        in_progress = conn.execute(
            "SELECT translation_id, translation_status FROM translation_segments "
            "WHERE passage_id = ? AND language = 'vi' AND translation_status IN ('queued', 'translating') "
            "LIMIT 1", (passage_id,)
        ).fetchone()
        if in_progress:
            return jsonify({
                'ok': False, 'error': 'already_queued',
                'passage_id': passage_id,
                'translation_id': in_progress['translation_id'],
                'status': in_progress['translation_status'],
            }), 409
        # Đánh dấu queued
        import uuid as _uuid
        tid = 'ts-' + _uuid.uuid4().hex[:12]
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO translation_segments
               (translation_id, work_id, language, translation_text, translator_type,
                model_name, prompt_version, source_passage_ids, translation_status,
                passage_id, created_at, updated_at)
               VALUES (?, ?, 'vi', '', 'ai_groq', ?, 't96v1', ?, 'queued', ?, ?, ?)""",
            (tid, seg['work_id'], _groq_model, passage_id, passage_id, now, now)
        )
        conn.commit()
        # Gọi Groq
        total_count = conn.execute(
            "SELECT COUNT(*) FROM text_passages WHERE canonical_ref = ?",
            (seg['canonical_ref'],)
        ).fetchone()[0]
        prompt = (
            f"Bạn là dịch giả Hán-Việt chuyên ngành Phật học. Dịch đoạn Hán văn sau sang tiếng Việt.\n\n"
            f"Quy tắc:\n"
            f"- Chỉ dịch đoạn này, không giải thích thêm\n"
            f"- Giữ nguyên tên riêng Hán-Việt phổ thông (Thiếu Lâm, Bồ Đề Đạt Ma, Huyền Trang, v.v.)\n"
            f"- Không dịch ID hay mã kỹ thuật\n"
            f"- Trả về JSON: {{\"translation_vi\": \"...\"}}\n\n"
            f"Đoạn {seg['sequence_no']}/{total_count} — {seg['canonical_ref']}:\n{zh_text}"
        )
        try:
            conn.execute(
                "UPDATE translation_segments SET translation_status='translating', updated_at=? "
                "WHERE translation_id=?", (datetime.now().isoformat(), tid)
            )
            conn.commit()
            import json as _json
            resp = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {_groq_key}', 'Content-Type': 'application/json'},
                json={'model': _groq_model, 'messages': [{'role': 'user', 'content': prompt}],
                      'temperature': 0.2, 'max_tokens': 1024},
                timeout=30
            )
            result = resp.json()
            raw_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            vi_text = None
            try:
                parsed = _json.loads(raw_content.strip())
                vi_text = parsed.get('translation_vi', '').strip()
            except Exception:
                vi_text = raw_content.strip()
            if not vi_text:
                raise ValueError("LLM trả về nội dung rỗng")
            conn.execute(
                "UPDATE translation_segments SET translation_text=?, translation_status='done', "
                "model_name=?, updated_at=? WHERE translation_id=?",
                (vi_text, _groq_model, datetime.now().isoformat(), tid)
            )
            conn.commit()
            return jsonify({
                'ok': True, 'from_cache': False,
                'passage_id': passage_id,
                'translation_id': tid,
                'translation_vi': vi_text,
                'model_name': _groq_model,
                'status': 'done',
            })
        except Exception as e:
            conn.execute(
                "UPDATE translation_segments SET translation_status='failed', "
                "updated_at=? WHERE translation_id=?",
                (datetime.now().isoformat(), tid)
            )
            conn.commit()
            app.logger.error(f"[T96] translate segment {passage_id} failed: {e}")
            return jsonify({'ok': False, 'error': f'Groq error: {str(e)}', 'passage_id': passage_id}), 500
    finally:
        conn.close()


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


@app.route('/daoanh/api/daitang/qa', methods=['POST'])
def api_daitang_qa():
    """POST /daoanh/api/daitang/qa {"question": "..."} — Q&A toàn hệ thống.
    mode='llm' → có câu trả lời tổng hợp + citations. mode='retrieval_only' →
    Groq hỏng → trả evidence đã retrieval. ok=false → không có tư liệu."""
    body = request.get_json(silent=True) or {}
    question = (body.get('question') or '').strip()
    if not question:
        return jsonify({'ok': False, 'error': 'Thiếu câu hỏi (question).'}), 400

    t0 = time.time()
    conn = get_db_connection()
    try:
        evidence, entities = _t126_retrieve(conn, question)
        if not evidence and not entities:
            return jsonify({
                'ok': False, 'mode': 'no_data',
                'message': 'Không tìm thấy tư liệu liên quan trong toàn hệ thống.',
                'question': question, 'latency_ms': int((time.time() - t0) * 1000),
            })
        lock = _t73_style_lock(conn)
        prompt = _t126_build_qa_prompt(question, evidence, entities, lock)
        answer, model, err = _t126_call_groq(prompt)
        if answer:
            return jsonify({
                'ok': True, 'mode': 'llm', 'answer': answer,
                'model': model or GROQ_MODEL,
                'citations': evidence + entities,
                'evidence': evidence, 'entities': entities,
                'question': question, 'latency_ms': int((time.time() - t0) * 1000),
            })
        return jsonify({
            'ok': True, 'mode': 'retrieval_only', 'answer': None,
            'llm_error': err or 'api_error',
            'evidence': evidence, 'entities': entities,
            'question': question, 'latency_ms': int((time.time() - t0) * 1000),
        })
    except Exception as e:
        app.logger.error(f"[T126] qa failed: {e}")
        return jsonify({'ok': False, 'error': f'Q&A lỗi: {str(e)}'}), 500
    finally:
        conn.close()


# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Dao Anh Main Server (app.py)")
    print("=" * 60)
    print(f"DB: {DB_PATH}")
    print(f"TTL Old: {TTL_OLD_DIR}")
    print(f"Admin: {ADMIN_DIR}")
    print("=" * 60)
    
    # Ensure directories exist
    for d in [TTL_OLD_DIR, TTL_MASTER_DIR, TTL_ARCHIVE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created: {d}")

    # Populate FTS5 places_search_fts nếu index rỗng (1 lần ~4-5s, giúp ô tìm kiếm ID nhanh)
    try:
        t0 = time.time()
        populated = ensure_places_search_fts()
        if populated:
            print(f"[fts] Đã populate places_search_fts trong {time.time()-t0:.1f}s", flush=True)
        else:
            print("[fts] places_search_fts đã sẵn sàng", flush=True)
    except Exception as e:
        print(f"[fts] Lỗi ensure_places_search_fts: {e}", flush=True)
    try:
        t0 = time.time()
        populated = ensure_places_pending_fts()
        if populated:
            print(f"[fts] Đã populate places_pending_fts trong {time.time()-t0:.1f}s", flush=True)
        else:
            print("[fts] places_pending_fts đã sẵn sàng", flush=True)
    except Exception as e:
        print(f"[fts] Lỗi ensure_places_pending_fts: {e}", flush=True)

    # Build cache id→cate cho places_pending (1 lần ~5s, giúp trang chính load nhanh thay vì 11.7s)
    try:
        t0 = time.time()
        _build_cate_ids_map()
        print(f"[cate] Đã build cache cate ids trong {time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[cate] Lỗi build cate ids: {e}", flush=True)

    # Warm lexicon vào RAM (1 lần ~1-2s, giúp ai_judge không bị cold 77s → placevn.html timeout)
    try:
        t0 = time.time()
        n = len(_load_lexicon_mem())
        print(f"[lexicon] Đã nạp {n} dòng lexicon vào RAM trong {time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[lexicon] Lỗi load lexicon: {e}", flush=True)

    # T148: Preload DILA Person Authority XML vào RAM (background thread, không block startup)
    def _t148_preload():
        try:
            _t148_load_dila_extra()
        except Exception as _e:
            print(f'[T148] Preload lỗi: {_e}', flush=True)
    _t148_threading.Thread(target=_t148_preload, daemon=True).start()

    # Bind 127.0.0.1 — chỉ nginx/gateway trên cùng máy mới proxy tới được, không expose ra ngoài
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)


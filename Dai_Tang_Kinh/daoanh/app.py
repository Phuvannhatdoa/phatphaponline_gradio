from flask import Flask, jsonify, request, send_from_directory, Response
import sqlite3
import re
import unicodedata
import os
import json
from datetime import datetime
import requests
import urllib.parse
import shutil
import time
from flask_cors import CORS

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
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["*"]}})

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
        src_count = conn.execute("SELECT COUNT(*) FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != ''").fetchone()[0]
        if force or doc_count < max(1, src_count // 100):
            try:
                conn.execute("INSERT INTO places_pending_fts(places_pending_fts) VALUES('delete-all')")
            except Exception:
                pass
            conn.execute(
                "INSERT INTO places_pending_fts(id, name_vi, name_zh, name_vi_norm) "
                "SELECT id, COALESCE(name_vi, ''), COALESCE(name_zh, ''), COALESCE(name_vi_norm, '') "
                "FROM places_pending WHERE name_vi IS NOT NULL AND name_vi != ''"
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

TAM_DICH_SUFFIX = ' (Tạm dịch)'

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
}

MUNICIPALITIES = {'北京', '上海', '天津', '重慶', '香港', '澳門'}

def parse_dila_district(district_str):
    """Parse DILA district string (e.g. '阿富汗-巴爾赫省(Balkh)-CharBolak')
    into dict {country_vi, province, district_vi, formatted}.
    Returns dict with only non-empty fields. No HVDic used.
    """
    if not district_str or not district_str.strip():
        return {}
    text = district_str.strip()
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
    if has_cn_admin:
        segments = []
        for part in dash_parts[1:]:
            part = part.strip()
            if not part:
                continue
            found = False
            for suffix, level_vi in ADMIN_LEVEL_MAP.items():
                if part.endswith(suffix):
                    name_raw = part[:-len(suffix)]
                    if not name_raw:
                        continue
                    name_vi = CHINESE_PLACE_NAMES.get(name_raw, name_raw)
                    segments.append(f'{level_vi} {name_vi}')
                    found = True
                    break
            if not found:
                # No standard suffix: check if it's a known municipality or dict entry
                if part in MUNICIPALITIES:
                    name_vi = CHINESE_PLACE_NAMES.get(part, part)
                    segments.append(f'thành phố {name_vi}')
                elif part in CHINESE_PLACE_NAMES:
                    segments.append(CHINESE_PLACE_NAMES[part])
                else:
                    segments.append(part)
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
def search_all_page():
    return send_from_directory(ADMIN_DIR, 'search_all.html')

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
    prompt = f"Dịch đoạn văn Hán văn sau sang tiếng Việt theo phong cách {style}. Giữ nguyên tên riêng, địa danh, niên hiệu. Chỉ trả về bản dịch, không thêm giải thích:\n\n{text}"
    meta = {"llm_provider": "", "style": style, "source_lang": source_lang, "target_lang": target_lang}
    # Try Gemini free tier first
    try:
        GEMINI_KEY = "AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=15)
        result = resp.json()
        if 'candidates' in result and result['candidates']:
            text_vi = result['candidates'][0]['content']['parts'][0]['text']
            if text_vi:
                text_vi = clean_gemini_output(text_vi)
                meta["llm_provider"] = "gemini-2.0-flash"
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
    """Shared helper: call Gemini 2.0 Flash, return text or None."""
    GEMINI_KEY = "AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    try:
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=timeout)
        result = resp.json()
        if 'candidates' in result and result['candidates']:
            text = result['candidates'][0]['content']['parts'][0]['text']
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
        provider_raw = 'gemini-2.0-flash'

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
                                   COALESCE(g.confidence, m.confidence, 1.0) AS confidence
                            FROM places_pending p
                            LEFT JOIN namevi_map_places m ON m.dila_id = p.id
                            LEFT JOIN places g ON g.name_zh = p.name_zh AND p.name_zh != ''
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
                                "source": "fts"
                            })
            elif fts_raw_ids is None:
                # FTS chưa sẵn sàng (lỗi tạo index) → fallback LIKE cũ.
                # 1) Search places table (has GPS coordinates)
                try:
                    rows = conn.execute("""
                        SELECT id, name_zh, name_vi, gps_lat, gps_long,
                               place_type, confidence
                        FROM places
                        WHERE (name_zh LIKE ? OR name_vi LIKE ? OR id LIKE ?)
                          AND gps_lat IS NOT NULL
                        ORDER BY confidence DESC
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
                                "source": "places"
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
                                   COALESCE(p.confidence, n.confidence) as confidence
                            FROM namevi_map_places n
                            LEFT JOIN places p ON p.name_zh = n.name_zh AND p.name_zh != ''
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
                                    "source": "namevi_map"
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
            else:
                temple_where = ""
            params = temple_params + [limit]
            if offset:
                params.append(offset)
            try:
                sql = f"""
                    SELECT p.id, p.name_zh,
                           COALESCE(n.name_vi, p.name_vi) AS name_vi,
                           p.gps_lat, p.gps_long,
                           p.place_type, p.confidence
                    FROM places p
                    LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
                    WHERE p.gps_lat IS NOT NULL
                      {temple_where}
                    GROUP BY p.id
                    ORDER BY p.confidence DESC
                    LIMIT ?{ ' OFFSET ?' if offset else '' }
                """
                rows = conn.execute(sql, params).fetchall()
                for r in rows:
                    results.append({
                        "id": r['id'], "name_zh": r['name_zh'], "name_vi": r['name_vi'],
                        "lat": r['gps_lat'], "lng": r['gps_long'],
                        "type": r['place_type'], "confidence": r['confidence'],
                        "source": "places"
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
        # Build base query selecting needed fields
        query = """
            SELECT p.id, p.name_zh, COALESCE(n.name_vi, p.name_vi) AS name_vi,
                   p.gps_lat, p.gps_long, p.place_type, p.note_category
            FROM places p
            LEFT JOIN namevi_map_places n ON n.name_zh = p.name_zh AND n.name_zh != ''
            WHERE p.gps_lat IS NOT NULL AND p.gps_long IS NOT NULL
        """
        params = []
        if category != 'all':
            # Map to internal categories based on note_category patterns
            if category == 'temple':
                query += " AND (p.note_category LIKE '%寺廟%' OR p.note_category LIKE '%佛塔%' OR p.note_category LIKE '%佛教文化地點%')"
            elif category == 'mountain':
                query += " AND p.note_category LIKE '%山峰%'"
            elif category == 'cave':
                query += " AND p.note_category LIKE '%石窟%'"
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
                'category': r['place_type'] or r['note_category']
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
            # Supplement name_vi from namevi_map_places if missing
            if not detail.get('name_vi') and detail.get('name_zh'):
                    nv = conn.execute("""
                        SELECT name_vi, note_vi FROM namevi_map_places
                        WHERE name_zh = ? AND name_vi != '' LIMIT 1
                    """, (detail['name_zh'],)).fetchone()
                    if nv:
                        detail['name_vi'] = nv['name_vi']
                        if not detail.get('note_vi'):
                            detail['note_vi'] = nv['note_vi']
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
        if detail and name_zh:
            cat = conn.execute("""
                SELECT title_vi, title_zh, dynasty_vi, translator_vi,
                       q_number, page, sh_number, juans,
                       source_name, source_full_title,
                       license_name, license_url, source_note
                FROM cbeta_catalog_vn
                WHERE title_zh LIKE ? OR title_vi LIKE ?
                LIMIT 1
            """, (f'%{name_zh}%', f'%{name_zh}%')).fetchone()
            if not cat:
                fuzzy = conn.execute("""
                    SELECT v.title_vi, v.title_zh, v.dynasty_vi, v.translator_vi,
                           v.q_number, v.page, v.sh_number, v.juans,
                           v.source_name, v.source_full_title,
                           v.license_name, v.license_url, v.source_note
                    FROM cbeta_catalog_place_fuzzy f
                    JOIN cbeta_catalog_vn v ON f.catalog_id = v.sh_number
                    WHERE f.place_id = ? AND f.score >= 70
                    ORDER BY f.score DESC, f.rank ASC
                    LIMIT 1
                """, (place_id,)).fetchone()
                if fuzzy:
                    cat = fuzzy
            if not cat and name_vi:
                cat = conn.execute("""
                    SELECT title_vi, title_zh, dynasty_vi, translator_vi,
                           q_number, page, sh_number, juans,
                           source_name, source_full_title,
                           license_name, license_url, source_note
                    FROM cbeta_catalog_vn
                    WHERE title_vi LIKE ?
                    LIMIT 1
                """, (f'%{name_vi}%',)).fetchone()
            if cat:
                detail['text_info'] = dict(cat)
                detail['text_info_match'] = 'exact' if 'title_zh' in (dict(cat) if cat else {}) else ('fuzzy' if fuzzy else 'like')

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

        # Mô tả DILA (raw): places_dila.note strip XML — hiển thị RIÊNG, không
        # nhét Hán văn vào note_vi (tránh vi phạm luật "no raw CJK on page").
        if not (detail.get('note_vi') or '').strip() and detail.get('name_zh'):
            try:
                _dconn = get_db_connection()
                try:
                    _nr = _dconn.execute(
                        "SELECT note FROM places_dila WHERE name_zh = ? AND note IS NOT NULL AND note != '' LIMIT 1",
                        (detail['name_zh'],)
                    ).fetchone()
                finally:
                    _dconn.close()
                if _nr and _nr['note']:
                    dila_note = re.sub(r'<[^>]+>', ' ', _nr['note'])
                    dila_note = re.sub(r'\s+', ' ', dila_note).strip()
                    detail['dila_note'] = dila_note
            except Exception:
                pass

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
            GEMINI_KEY = "AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            resp = requests.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}]
            }, timeout=15)
            result = resp.json()
            if 'candidates' in result and result['candidates']:
                vi_draft = result['candidates'][0]['content']['parts'][0]['text']
                if vi_draft:
                    meta["llm_provider"] = "gemini-2.0-flash"
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=15)
        result = resp.json()
        if 'candidates' in result and result['candidates']:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            if summary:
                summary = clean_gemini_output(summary)
                return jsonify({"summary_vi": summary, "provider": "gemini-2.0-flash"})
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


@app.route('/daoanh/api/admin/wiki/fetch', methods=['POST'])
def wiki_fetch():
    """
    POST /daoanh/api/admin/wiki/fetch
    Body: {"place_id": "PL...", "name_vi": "...", "name_zh": "..."}
    Returns {has_wiki, wiki_title, wiki_url, snippet, cached_at}
    Auto-saves snapshot to place_wiki_snapshots. Always 200.
    """
    body = request.get_json(silent=True) or {}
    place_id = (body.get('place_id') or '').strip()
    name_vi = (body.get('name_vi') or '').strip()
    name_zh = (body.get('name_zh') or '').strip()
    if not place_id:
        return jsonify({"has_wiki": False, "error": "missing_place_id"})
    # Check cached first
    conn = get_db_connection()
    cached = conn.execute(
        "SELECT wiki_title, wiki_url, snippet, full_text, created_at FROM place_wiki_snapshots WHERE place_id = ?",
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
            "cached_at": cached['created_at'] or ''
        })
    # Try Vietnamese Wikipedia first
    search_terms = [name_vi, name_zh]
    found = {"title": "", "url": "", "snippet": "", "full_text": ""}
    import requests as req
    HEADERS = {'User-Agent': 'DaoAnh/1.0 (Buddhist Geography Tool; +https://phatphaponline.org)'}
    for term in search_terms:
        if not term:
            continue
        try:
            resp = req.get(
                "https://vi.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": term,
                    "format": "json",
                    "srlimit": 1,
                    "srprop": "snippet"
                },
                headers=HEADERS,
                timeout=10
            )
            data = resp.json()
            pages = data.get('query', {}).get('search', [])
            if pages:
                title = pages[0]['title']
                snippet = pages[0].get('snippet', '')
                # Clean HTML tags from snippet
                import re as re_html
                snippet = re_html.sub(r'<[^>]+>', '', snippet)
                found['title'] = title
                found['url'] = f"https://vi.wikipedia.org/wiki/{title.replace(' ', '_')}"
                found['snippet'] = snippet[:500]
                # Fetch HTML extract (lead section)
                ext_resp = req.get(
                    "https://vi.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "prop": "extracts",
                        "exintro": 1,
                        "titles": title,
                        "format": "json"
                    },
                    headers=HEADERS,
                    timeout=10
                )
                ext_data = ext_resp.json()
                pages2 = ext_data.get('query', {}).get('pages', {})
                html_extract = ""
                for pid, pdata in pages2.items():
                    if 'extract' in pdata:
                        html_extract = pdata['extract']
                        break
                # Plain text version for snippet and full_text
                import re as re_html
                plain_text = re_html.sub(r'<[^>]+>', '', html_extract)
                found['full_text'] = plain_text[:2000]
                if not found['snippet']:
                    found['snippet'] = plain_text[:500]
                found['content_html'] = html_extract
                break
        except Exception:
            continue
        # If Vi failed, try zh
        if not found['title']:
            try:
                resp = req.get(
                    "https://zh.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": term,
                        "format": "json",
                        "srlimit": 1,
                        "srprop": "snippet"
                    },
                    headers=HEADERS,
                    timeout=10
                )
                data = resp.json()
                pages = data.get('query', {}).get('search', [])
                if pages:
                    title = pages[0]['title']
                    snippet = pages[0].get('snippet', '')
                    import re as re_html
                    snippet = re_html.sub(r'<[^>]+>', '', snippet)
                    found['title'] = title
                    found['url'] = f"https://zh.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    found['snippet'] = snippet[:500]
            except Exception:
                continue
        if found['title']:
            # Save to DB
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Ensure content_html column exists
            try:
                conn.execute("SELECT content_html FROM place_wiki_snapshots LIMIT 1")
            except Exception:
                conn.execute("ALTER TABLE place_wiki_snapshots ADD COLUMN content_html TEXT")
            conn.execute("""
                INSERT OR REPLACE INTO place_wiki_snapshots (place_id, wiki_title, wiki_url, snippet, full_text, content_html, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (place_id, found['title'], found['url'], found['snippet'], found['full_text'], found.get('content_html', ''), now, now))
            conn.commit()
            conn.close()
            return jsonify({
                "has_wiki": True,
                "wiki_title": found['title'],
                "wiki_url": found['url'],
                "snippet": found['snippet'],
                "full_text": found['full_text'],
                "content_html": found.get('content_html', ''),
                "cached_at": now
            })
    conn.close()
    return jsonify({"has_wiki": False})


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
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Đã lưu tên tự động"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
        rows = conn.execute("""
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


# ===== PANORAMA (Legacy TTL Dashboard) =====

@app.route('/daoanh/panorama/')
def panorama_index():
    return send_from_directory(ADMIN_DIR, 'panorama.html')

# ===== COUNTER FILE PATH =====
COUNTER_FILE = os.path.join(DATA_DIR, 'counter.dat')

# ===== INITIALIZE DIRECTORIES =====

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

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

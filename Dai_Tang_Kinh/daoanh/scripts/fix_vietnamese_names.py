#!/usr/bin/env python3
"""
Batch fix: scan places tables for CJK chars in name_vi, apply custom HV pipeline.
Standalone (no Flask dependency).
"""
import sqlite3, re, os, sys, unicodedata

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'lineage.db')

CUSTOM_HANVIET = {
    "跋": "Bạt", "姞": "Cát", "邸": "Để", "磧": "Tích", "杲": "Cảo", "祐": "Hựu",
    "頤": "Di", "頊": "Húc", "頌": "Tụng", "頒": "Ban", "頓": "Đốn", "頗": "Phả",
    "頫": "Phủ", "頡": "Hiệt", "頣": "Thẩn", "頦": "Hài", "頲": "Đĩnh",
    "頸": "Cảnh", "顆": "Khỏa", "餉": "Hưởng", "饋": "Quỹ", "饌": "Soạn",
    "饒": "Nhiêu", "饕": "Thao", "饗": "Hưởng", "饜": "Yếm",
    "驀": "Mạch", "驁": "Ngao", "驃": "Phiếu", "驄": "Thông", "驊": "Hoa",
    "驍": "Kiêu", "驛": "Trạch", "驢": "Lư", "驥": "Ký", "驪": "Ly",
    "頷": "Hàm", "頰": "Giáp", "頭": "Đầu", "頴": "Dĩnh",
    "飭": "Sức", "飯": "Phạn", "飲": "Ẩm", "飼": "Tự", "飽": "Bão",
    "飾": "Sức", "餅": "Bính", "養": "Dưỡng", "餐": "Xan",
    "餓": "Ngạ", "餘": "Dư", "館": "Quán", "饅": "Mạn",
}

def _load_hv_fallback_cache():
    cache = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT ch, hv FROM hanviet_fallback").fetchall()
        for r in rows:
            cache[r[0]] = r[1]
        conn.close()
    except Exception:
        pass
    return cache

def _ensure_vietnamese(text, hv_cache):
    if not text:
        return text or ''
    result = []
    missing = []
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            hv = CUSTOM_HANVIET.get(c)
            if hv:
                result.append(hv)
                continue
            hv = hv_cache.get(c) if hv_cache else None
            if hv:
                result.append(hv)
            else:
                missing.append(c)
        else:
            result.append(c)
    cleaned = ''.join(result)
    cleaned = re.sub(r'[\u3040-\u30FF\u3400-\u4DBF]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned, missing

def has_cjk(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text or ''))

def fix_table(conn, hv_cache, table, name_col, id_col='id', where=''):
    rows = conn.execute(f"SELECT {id_col}, {name_col} FROM {table} {where}").fetchall()
    fixed = 0
    all_missing = set()
    for r in rows:
        old = r[name_col] or ''
        if not has_cjk(old):
            continue
        new, missing = _ensure_vietnamese(old, hv_cache)
        all_missing.update(missing)
        if new != old:
            conn.execute(f"UPDATE {table} SET {name_col} = ? WHERE {id_col} = ?", (new, r[id_col]))
            fixed += 1
            if fixed <= 5:
                print(f"  FIXED: {old[:50]} → {new[:50]}")
    return fixed, all_missing

def main():
    print("=" * 60)
    print("FIX VIETNAMESE NAMES — Batch cleanup")
    print("=" * 60)
    hv_cache = _load_hv_fallback_cache()
    print(f"Loaded {len(hv_cache)} hanviet_fallback entries")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    total_missing = set()
    total_fixed = 0
    
    for table, id_col in [('namevi_map_places', 'dila_id'), ('places_pending', 'id'), ('places', 'id')]:
        print(f"\n[{table}.name_vi] ...")
        f, missing = fix_table(conn, hv_cache, table, 'name_vi', id_col)
        total_fixed += f
        total_missing.update(missing)
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Total fixed: {total_fixed} records")
    if total_missing:
        print(f"  Missing chars (not in CUSTOM_HANVIET): {sorted(total_missing)}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

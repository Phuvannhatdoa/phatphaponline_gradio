#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_places.py — T121 (ráspec4 2026-09-09): sinh ứng viên địa lý từ Wikidata.

Tìm các địa danh (places_dila) CHƯA có toạ độ (geo_lat/geo_long null) và CHƯA được
enrich (geo_cross_ref.enrich_status != 'none') → tra cứu Wikidata qua tên (Hán/Việt),
trích P625 (globecoordinate) + P2044 (elevation) → ghi ứng viên vào geo_cross_ref với
enrich_status='candidate'. KHÔNG set wikidata_qid/lat/lon chính thức — Admin duyệt bằng
POST /daoanh/api/admin/geo-enrich (set status='approved').

Chỉ-tạo-ứng-viên, không tự quyết: đúng mô hình HITL (không auto-approve tên mơ hồ).

Chạy:  python scripts/enrich_places.py --limit 50 [--run]   (mặc định dry-run)
"""
import io
import json
import os
import sqlite3
import sys
import time

import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

_WD_HEADERS = {
    'User-Agent': 'DaoAnhBuddhistGIS/1.0 (https://phatphaponline.org/daoanh/; contact via project admin) python-requests'
}


def _recent_candidates(conn):
    """Đếm ứng viên 'candidate' hiện có (chống lặp lại mỗi lần chạy)."""
    return conn.execute(
        "SELECT COUNT(*) FROM geo_cross_ref WHERE enrich_status IN ('candidate', 'approved', 'rejected')"
    ).fetchone()[0]


def _search_qid(term):
    """Wikidata wbsearchentities — trả QID đầu tiên khớp từ 'term'."""
    try:
        r = requests.get('https://www.wikidata.org/w/api.php', params={
            'action': 'wbsearchentities', 'search': term, 'language': 'vi',
            'uselang': 'vi', 'format': 'json', 'limit': 3,
        }, headers=_WD_HEADERS, timeout=10)
        r.raise_for_status()
        res = r.json().get('search', [])
        for item in res:
            qid = item.get('id', '')
            if qid and qid.startswith('Q'):
                return qid
    except Exception as e:
        print(f"  [warn] search {term!r}: {e}")
    return None


def _fetch_geo(qid):
    """Trả (lat, lon, elevation) từ P625 + P2044 của entity qid."""
    try:
        r = requests.get(f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
                         headers=_WD_HEADERS, timeout=10)
        r.raise_for_status()
        entity = r.json()['entities'][qid]
        claims = entity.get('claims', {})
        lat = lon = elev = None
        for c in claims.get('P625', []):
            v = c.get('mainsnak', {}).get('datavalue', {}).get('value', {})
            if v.get('latitude') is not None and v.get('longitude') is not None:
                lat = v['latitude']; lon = v['longitude']
                break
        for c in claims.get('P2044', []):
            v = c.get('mainsnak', {}).get('datavalue', {}).get('value', {})
            if v.get('amount') is not None:
                try:
                    elev = int(float(v['amount'].lstrip('+')))
                except (ValueError, AttributeError):
                    elev = None
                break
        return lat, lon, elev
    except Exception as e:
        print(f"  [warn] fetch {qid}: {e}")
        return None, None, None


def main():
    do_run = '--run' in sys.argv
    limit = 100
    for a in sys.argv[1:]:
        if a.startswith('--limit='):
            limit = int(a.split('=', 1)[1])
    if not do_run:
        print("[dry-run] không ghi DB — thêm --run để thực thi")

    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        already = _recent_candidates(conn)
        print(f"[i] geo_cross_ref ứng viên/đã duyệt hiện có: {already}")
        targets = conn.execute(
            """SELECT pd.id, pd.name, pd.name_zh, pd.geo_lat
               FROM places_dila pd
               LEFT JOIN geo_cross_ref g ON g.dila_id = pd.id
               WHERE (pd.geo_lat IS NULL OR pd.geo_long IS NULL)
                 AND (g.id IS NULL OR g.enrich_status = 'none')
               ORDER BY pd.id
               LIMIT ?""",
            (limit,),
        ).fetchall()
        if not targets:
            print("[i] Không còn địa danh thiếu toạ độ chưa enrich.")
            return 0

        inserted = 0
        for i, t in enumerate(targets, 1):
            term = (t['name_zh'] or t['name'] or '').strip()
            if not term:
                continue
            print(f"[{i}/{len(targets)}] {t['id']} {term} …", end=' ')
            qid = _search_qid(term)
            if not qid:
                print('no-match')
                continue
            lat, lon, elev = _fetch_geo(qid)
            print(f"{qid} lat={lat} lon={lon} elev={elev}")
            if do_run and lat is not None:
                try:
                    conn.execute(
                        """INSERT INTO geo_cross_ref
                           (dila_id, wikidata_qid, notes, confidence, mapped_by,
                            enrich_status, enrich_source_qid, enrich_lat, enrich_lon,
                            enrich_elevation_m, enrich_checked_at)
                           VALUES (?, NULL, '', 'candidate', 'wikidata-cron',
                                   'candidate', ?, ?, ?, ?, datetime('now'))
                           ON CONFLICT(dila_id) DO UPDATE SET
                               enrich_status='candidate',
                               enrich_source_qid=excluded.enrich_source_qid,
                               enrich_lat=excluded.enrich_lat,
                               enrich_lon=excluded.enrich_lon,
                               enrich_elevation_m=excluded.enrich_elevation_m,
                               enrich_checked_at=excluded.enrich_checked_at""",
                        (t['id'], qid, lat, lon, elev),
                    )
                    conn.commit()
                    inserted += 1
                except sqlite3.OperationalError:
                    conn.execute(
                        """UPDATE geo_cross_ref SET enrich_status='candidate',
                           enrich_source_qid=?, enrich_lat=?, enrich_lon=?, enrich_elevation_m=?,
                           enrich_checked_at=datetime('now') WHERE dila_id=?""",
                        (qid, lat, lon, elev, t['id']),
                    )
                    conn.commit()
                    inserted += 1
            time.sleep(0.4)  # lịch sự với Wikidata

        print(f"[i] xong: {inserted} ứng viên mới (limit={limit}, run={do_run})")
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T185 — Import toàn bộ TTL → lineage_edge_assertions (source_code='TTL')
============================================================================
Pipeline 4 phase (Zero-RAM · Zero-ALTER-base · Idempotent):

  Phase 1: Parse 1038 TTL files → upsert vn_person_authority (người + DILA ID)
  Phase 2: Parse 1038 TTL files → upsert vn_person_relations (edges, slug-based)
  Phase 3: Bridge vn_person_relations + vn_person_authority.dila_id
           → INSERT lineage_edge_assertions source_code='TTL'
  Phase 4: Rebuild lineage_edge_consensus (ttl_asserted flag)

Cách dùng:
    python scripts/etl_ttl_full_import.py --dry-run   # chỉ báo cáo
    python scripts/etl_ttl_full_import.py --apply     # chạy cả 4 phase
    python scripts/etl_ttl_full_import.py --phase 3   # chỉ chạy 1 phase cụ thể
"""
import argparse
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, 'data', 'lineage.db')
TTL_DIR  = os.path.join(BASE_DIR, 'data', 'ttl')
TS       = time.strftime('%Y-%m-%dT%H:%M:%S')

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def fix_enc(s):
    """Chuẩn hóa: U+00D0 Ð (Latin Eth) → U+0110 Đ (D gạch đúng tiếng Việt)."""
    return s.replace('Ð', 'Đ').replace('ð', 'đ')

def extract_han(text, min_len=2, max_len=12):
    """Trích chuỗi Hán tự liên tiếp (tự động nối nếu có khoảng trắng giữa)."""
    j = re.sub(r'([一-鿿])\s+([一-鿿])', r'\1\2', text)
    j = re.sub(r'([一-鿿])\s+([一-鿿])', r'\1\2', j)
    return re.findall(rf'[一-鿿]{{{min_len},{max_len}}}', j)

# ─────────────────────────────────────────────────────────────
# PARSE 1 FILE TTL
# ─────────────────────────────────────────────────────────────

def parse_ttl(fpath):
    """Trả về dict chứa thông tin người + lineage edges từ 1 file TTL."""
    with open(fpath, encoding='utf-8') as f:
        raw = f.read()
    content = fix_enc(raw)

    # Slug chính
    m = re.search(r'<ex:monk/([^>]+)>\s+a\s+<bkg:Monk>', content)
    if not m:
        return None
    main_slug = m.group(1)

    # Label chính @vi
    vi_labels = re.findall(r'rdfs:label\s+"([^"]+)"@vi', content)
    main_label = vi_labels[0] if vi_labels else ''

    # Hán tự từ toàn bộ file (ưu tiên trong appellations/bio)
    han_hits = extract_han(content)

    # Năm sinh/mất
    birth = death = None
    bm = re.search(r'bkg:birthYear\s+"?(\d{3,4})"?', content)
    dm = re.search(r'bkg:deathYear\s+"?(\d{3,4})"?', content)
    if not bm:
        bm = re.search(r'(\d{3,4})\s*[-–]\s*(\d{3,4})', main_label + ' ' + content[:500])
    if bm:
        try: birth = int(bm.group(1))
        except: pass
    if dm:
        try: death = int(dm.group(1))
        except: pass

    # Tông phái
    lineage_m = re.search(r'bkg:dharmaLineageName\s+"([^"]+)"@vi', content)
    dharma_lineage = lineage_m.group(1) if lineage_m else ''

    # generationOrder
    gen_m = re.search(r'bkg:generationOrder\s+(\d+)', content)
    gen_order = int(gen_m.group(1)) if gen_m else None

    # Tiểu sử
    bio_m = re.search(r'bkg:biographicalNote\s+"""(.*?)"""', content, re.DOTALL)
    bio_vi = bio_m.group(1).strip() if bio_m else ''

    # Labels map cho tất cả slug trong file
    label_map = {}
    for lm in re.finditer(r'<ex:monk/([^>]+)>\s+rdfs:label\s+"([^"]+)"@vi', content):
        label_map[lm.group(1)] = lm.group(2)

    # Edges
    teachers  = re.findall(r'bkg:hasTeacher\s+<ex:monk/([^>]+)>', content)
    disciples = []
    for block in re.findall(r'bkg:hasDisciple\s+([^;.]+)', content):
        for sm in re.findall(r'<ex:monk/([^>]+)>', block):
            disciples.append(sm)
    related = re.findall(r'bkg:hasRelatedFigure\s+<ex:monk/([^>]+)>', content)

    return {
        'slug':          main_slug,
        'name_vi':       main_label,
        'name_zh':       han_hits[0] if han_hits else '',
        'bio_vi':        bio_vi,
        'dharma_lineage': dharma_lineage,
        'gen_order':     gen_order,
        'birth_year':    birth,
        'death_year':    death,
        'label_map':     label_map,
        'teachers':      teachers,
        'disciples':     disciples,
        'related':       related,
        'filename':      os.path.basename(fpath).replace('.ttl', ''),
    }

# ─────────────────────────────────────────────────────────────
# BUILD VI INDEX (name_vi → DILA id)
# ─────────────────────────────────────────────────────────────

def build_vi_index(conn):
    """
    Build lookup: name_vi.lower() → DILA ID, name_zh → DILA ID.
    CHỈ dùng bảng `people` (DILA authority) làm ground truth.
    KHÔNG mix vn_person_authority vào đây — tên trong vpa có prefix
    danh hiệu ("Tôn Giả", "Thiền Sư"...) gây exact-match sai.
    Tên có nhiều vị cùng tên → đánh dấu ambiguous → loại khỏi dict
    để tránh gán nhầm (vd: 宗鑑 có 5 vị khác nhau trong DILA).
    """
    vi_map = {}
    zh_map = {}
    vi_dup = set()
    zh_dup = set()
    for r in conn.execute('SELECT id, name_vi, name_zh FROM people WHERE name_vi != "" OR name_zh != ""'):
        if r['name_vi']:
            k = r['name_vi'].strip().lower()
            if k in vi_map:
                vi_dup.add(k)
            vi_map[k] = r['id']
        if r['name_zh']:
            k = r['name_zh'].strip()
            if k in zh_map:
                zh_dup.add(k)
            zh_map[k] = r['id']
    # Xóa các tên ambiguous (nhiều vị cùng tên) để tránh match nhầm
    for k in vi_dup:
        vi_map.pop(k, None)
    for k in zh_dup:
        zh_map.pop(k, None)
    if vi_dup or zh_dup:
        print(f'  [build_lookup] Bỏ qua {len(vi_dup)} tên Việt + {len(zh_dup)} tên Hán ambiguous (nhiều vị cùng tên)')
    return vi_map, zh_map

def match_person(name_vi, name_zh_candidates, vi_idx, zh_idx):
    """Thử match tên → DILA ID. Trả về (dila_id, method).

    [T203] SỬA thứ tự ưu tiên: trước đây thử **tail-N trước Hán**, nên "Báo Ân Pháp Diễn"
    khớp `tail2 = "Pháp Diễn"` — tên lõi rất phổ biến ⇒ nhiều vị khác nhau cùng nhận
    1 `dila_id` (25 nhóm `dila_id` đụng, T200/T203). Hán **phân biệt tốt hơn** nên chuyển
    lên trước. Thêm: tail phải ≥3 từ và duyệt từ dài→ngắn.
    """
    name_vi = fix_enc(name_vi) if name_vi else ''
    # Thử 1: exact
    if name_vi.strip().lower() in vi_idx:
        return vi_idx[name_vi.strip().lower()], 'exact_vi'
    # Thử 2: Hán — CHÍNH XÁC HƠN tail (tên lõi tiếng Việt trùng rất nhiều)
    for zh in name_zh_candidates:
        if zh in zh_idx:
            return zh_idx[zh], 'zh'
    # Thử 3: N từ cuối (bỏ tiền tố triều đình) — CHỈ khi ≥3 tỗ, dài→ngắn
    words = name_vi.strip().split()
    if len(words) >= 3:
        for n in range(len(words), 2, -1):
            candidate = ' '.join(words[-n:]).lower()
            if candidate in vi_idx:
                return vi_idx[candidate], f'tail{n}_vi'
    return None, None

# ─────────────────────────────────────────────────────────────
# PHASE 1 — vn_person_authority upsert
# ─────────────────────────────────────────────────────────────

def phase1_upsert_persons(conn, parsed_files, vi_idx, zh_idx, dry_run):
    """Upsert tất cả người từ TTL vào vn_person_authority."""
    n_insert = n_update = n_skip = n_collision = 0
    existing = {r[0] for r in conn.execute('SELECT id FROM vn_person_authority')}
    existing_fn = {r[0] for r in conn.execute('SELECT ttl_filename FROM vn_person_authority WHERE ttl_filename IS NOT NULL')}
    # Collision guard: tập dila_id đã được gán (không gán lại cho người khác)
    claimed_dila = {
        r[0] for r in conn.execute(
            "SELECT dila_id FROM vn_person_authority "
            "WHERE dila_id IS NOT NULL AND dila_id != '' AND id NOT LIKE 'alias_%'"
        )
    }

    # Build slug→dila_id từ ttl_mapping để dùng trong teacher-guard bên dưới
    _ttl_dila_map = {
        r[0]: r[1] for r in conn.execute(
            "SELECT ttl_filename, dila_id FROM ttl_mapping WHERE dila_id IS NOT NULL AND dila_id != ''"
        )
    }

    for p in parsed_files:
        slug = p['slug']
        fname = p['filename']
        if fname in existing_fn:
            n_skip += 1
            continue  # đã có, bỏ qua (idempotent)

        # Tìm DILA ID
        han_list = extract_han(p['name_zh'] + ' ' + p['bio_vi'][:500])
        dila_id, method = match_person(p['name_vi'], han_list, vi_idx, zh_idx)

        # [T230-guard] Chặn gán nhầm dila_id của THẦY cho ĐỆ TỬ.
        # Nếu dila_id khớp với dila_id của bất kỳ teacher_slug nào trong TTL → hủy.
        # Lỗi gốc: TS-Hoa-Tang-Tong-Dien (đệ tử) bị gán A000475 = dila_id của Đại Huệ Tông Cảo (thầy).
        if dila_id and p.get('teachers'):
            for teacher_slug in p['teachers']:
                teacher_dila = _ttl_dila_map.get(teacher_slug) or (
                    conn.execute(
                        "SELECT dila_id FROM vn_person_authority WHERE id=? AND dila_id!=''",
                        (teacher_slug,)
                    ).fetchone() or [None]
                )[0]
                if teacher_dila and teacher_dila == dila_id:
                    print(f'  [T230-TEACHER-GUARD] {slug} ({p["name_vi"]}) → {dila_id} '
                          f'là dila_id của thầy {teacher_slug} → hủy match')
                    dila_id = None
                    method = 'teacher_guard'
                    break

        # [T185-guard] Chặn collision: nếu dila_id đã được gán cho người khác → bỏ qua
        if dila_id and dila_id in claimed_dila:
            print(f'  [COLLISION] {slug} ({p["name_vi"]}) → {dila_id} đã bị claim → dila_id=NULL')
            dila_id = None
            method = 'collision_guard'
            n_collision += 1
        elif dila_id:
            claimed_dila.add(dila_id)

        if dry_run:
            n_insert += 1
            continue

        conn.execute("""
            INSERT OR IGNORE INTO vn_person_authority
            (id, ttl_filename, name_vi, name_zh, dharma_lineage,
             generation_order, biographical_note_vi, birth_year, death_year,
             dila_id, status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            slug, fname, p['name_vi'], p['name_zh'], p['dharma_lineage'],
            p['gen_order'], p['bio_vi'][:5000], p['birth_year'], p['death_year'],
            dila_id or '', 'pending', TS,
        ))
        n_insert += 1

    print(f'[P1] vn_person_authority: +{n_insert} mới | {n_skip} đã có | {n_update} cập nhật | {n_collision} collision-guard'
          + (' (dry-run)' if dry_run else ''))
    return n_insert

# ─────────────────────────────────────────────────────────────
# PHASE 2 — vn_person_relations upsert edges
# ─────────────────────────────────────────────────────────────

def phase2_upsert_relations(conn, parsed_files, dry_run):
    """Upsert tất cả edges (hasTeacher/hasDisciple) vào vn_person_relations."""
    # Lấy tập đã có để idempotent
    existing = set()
    for r in conn.execute('SELECT person_id, relation_type, target_id FROM vn_person_relations'):
        existing.add((r['person_id'], r['relation_type'], r['target_id']))

    n_ins = n_skip = 0
    for p in parsed_files:
        slug = p['slug']
        fname = p['filename']
        label_map = p['label_map']

        def add_edge(target_slug, rel_type):
            nonlocal n_ins, n_skip
            key = (slug, rel_type, target_slug)
            if key in existing:
                n_skip += 1
                return
            target_label = label_map.get(target_slug, '')
            if not dry_run:
                conn.execute("""
                    INSERT OR IGNORE INTO vn_person_relations (person_id, relation_type, target_id, target_label_vi, ttl_filename)
                    VALUES (?,?,?,?,?)
                """, (slug, rel_type, target_slug, target_label, fname))
            n_ins += 1

        for t in p['teachers']:
            add_edge(t, 'hasTeacher')
        for d in p['disciples']:
            add_edge(d, 'hasDisciple')
        for r in p['related']:
            add_edge(r, 'hasRelatedFigure')

    print(f'[P2] vn_person_relations: +{n_ins} mới | {n_skip} đã có'
          + (' (dry-run)' if dry_run else ''))
    return n_ins

# ─────────────────────────────────────────────────────────────
# PHASE 3 — Bridge → lineage_edge_assertions
# ─────────────────────────────────────────────────────────────

def phase3_bridge_to_assertions(conn, dry_run):
    """
    Với mỗi edge trong vn_person_relations (hasTeacher/hasDisciple):
    - Resolve slug → DILA ID: ưu tiên people vi_index (ground truth) > vpa.dila_id
    - Nếu cả 2 đầu có DILA ID → INSERT lineage_edge_assertions source_code='TTL'
    """
    # Build vi_index từ people (nguồn gốc đáng tin nhất)
    vi_idx, zh_idx = build_vi_index(conn)

    # Build slug → dila_id: dùng vi_index re-match làm ground truth
    # vpa.dila_id chỉ dùng khi không re-match được (TTL-only persons)
    slug_to_dila = {}
    for r in conn.execute("SELECT id, name_vi, name_zh, dila_id FROM vn_person_authority"):
        slug = r['id']
        # Thử re-match tên → DILA (tin vi_index hơn vpa.dila_id)
        name_vi = r['name_vi'] or ''
        name_zh = r['name_zh'] or ''
        han_list = extract_han(name_zh)
        re_match, _ = match_person(name_vi, han_list, vi_idx, zh_idx)
        if re_match:
            slug_to_dila[slug] = re_match          # ground truth từ vi_index
        elif r['dila_id']:
            slug_to_dila[slug] = r['dila_id']      # fallback: vpa.dila_id cũ

    # Lấy edges hiện có để idempotent
    existing_keys = {r[0] for r in conn.execute(
        "SELECT edge_key FROM lineage_edge_assertions WHERE source_code='TTL'")}

    n_both = n_one = n_none = n_skip = 0
    edges = conn.execute("""
        SELECT person_id, relation_type, target_id, ttl_filename
        FROM vn_person_relations
        WHERE relation_type IN ('hasTeacher','hasDisciple')
    """).fetchall()

    for e in edges:
        if e['relation_type'] == 'hasTeacher':
            # person_id là trò, target_id là thầy
            teacher_slug = e['target_id']
            disciple_slug = e['person_id']
        else:  # hasDisciple
            teacher_slug = e['person_id']
            disciple_slug = e['target_id']

        t_id = slug_to_dila.get(teacher_slug)
        d_id = slug_to_dila.get(disciple_slug)

        if t_id and d_id:
            edge_key = f'TTL|{t_id}|{d_id}'
            if edge_key in existing_keys:
                n_skip += 1
                continue
            if not dry_run:
                # INSERT OR IGNORE: mỗi cặp (teacher,disciple) chỉ cần 1 row TTL
                # nhiều TTL file xác nhận cùng cặp → chỉ giữ row đầu tiên
                conn.execute("""
                    INSERT OR IGNORE INTO lineage_edge_assertions
                    (edge_key, subject_person_id, relation_type, object_person_id,
                     source_code, raw_relation_type, ref, mapping_verified, trust_level, status, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    edge_key, t_id, 'da:isTeacherOf', d_id,
                    'TTL', e['relation_type'], e['ttl_filename'],
                    1, 'L2', 'active', TS,
                ))
            n_both += 1
        elif t_id or d_id:
            n_one += 1   # 1 đầu có DILA, 1 đầu chưa
        else:
            n_none += 1  # cả 2 chưa có DILA

    total = n_both + n_one + n_none
    print(f'[P3] Bridge TTL edges ({total} tổng):')
    print(f'  Ca 2 dau match → +{n_both} assertions TTL' + (' (dry-run)' if dry_run else ''))
    print(f'  1 dau match    → {n_one} (pending resolution)')
    print(f'  0 dau match    → {n_none} (no DILA bridge)')
    print(f'  Skip da co     → {n_skip}')
    return n_both

# ─────────────────────────────────────────────────────────────
# PHASE 4 — Rebuild lineage_edge_consensus (ttl_asserted)
# ─────────────────────────────────────────────────────────────

def phase4_rebuild_consensus(conn, dry_run):
    """
    Cập nhật lineage_edge_consensus.ttl_asserted=1 cho mọi edge
    xuất hiện trong lineage_edge_assertions với source_code='TTL'.
    Rebuild agreeing_source_count và consensus_status.
    """
    if dry_run:
        # Chỉ đếm sẽ cập nhật bao nhiêu
        n = conn.execute("""
            SELECT COUNT(DISTINCT ec.id) FROM lineage_edge_consensus ec
            JOIN lineage_edge_assertions ea
              ON ea.subject_person_id = ec.teacher_id
             AND ea.object_person_id  = ec.disciple_id
             AND ea.source_code = 'TTL'
            WHERE ec.ttl_asserted = 0
        """).fetchone()[0]
        print(f'[P4] Sẽ cập nhật ttl_asserted=1 cho {n} edge trong consensus (dry-run)')
        return n

    # Cập nhật ttl_asserted
    conn.execute("""
        UPDATE lineage_edge_consensus
        SET ttl_asserted = 1,
            updated_at   = ?
        WHERE EXISTS (
            SELECT 1 FROM lineage_edge_assertions ea
            WHERE ea.subject_person_id = lineage_edge_consensus.teacher_id
              AND ea.object_person_id  = lineage_edge_consensus.disciple_id
              AND ea.source_code = 'TTL'
        )
    """, (TS,))
    n_upd = conn.execute('SELECT changes()').fetchone()[0]

    # Rebuild agreeing_source_count và consensus_status
    conn.execute("""
        UPDATE lineage_edge_consensus
        SET agreeing_source_count = (
                (CASE WHEN dila_asserted    = 1 THEN 1 ELSE 0 END) +
                (CASE WHEN marcus_asserted  = 1 THEN 1 ELSE 0 END) +
                (CASE WHEN ttl_asserted     = 1 THEN 1 ELSE 0 END) +
                (CASE WHEN lineage_asserted = 1 THEN 1 ELSE 0 END)
            ),
            consensus_status = CASE
                WHEN ((CASE WHEN dila_asserted=1 THEN 1 ELSE 0 END)+
                      (CASE WHEN marcus_asserted=1 THEN 1 ELSE 0 END)+
                      (CASE WHEN ttl_asserted=1 THEN 1 ELSE 0 END)+
                      (CASE WHEN lineage_asserted=1 THEN 1 ELSE 0 END)) >= 2
                THEN 'confirmed_2plus'
                ELSE 'single_source'
            END,
            source_badge = (
                SELECT GROUP_CONCAT(src, ', ')
                FROM (
                    SELECT 'DILA'    AS src, dila_asserted    AS on_ WHERE on_=1 UNION ALL
                    SELECT 'Marcus'  AS src, marcus_asserted  AS on_ WHERE on_=1 UNION ALL
                    SELECT 'TTL'     AS src, ttl_asserted     AS on_ WHERE on_=1 UNION ALL
                    SELECT 'Lineage' AS src, lineage_asserted AS on_ WHERE on_=1
                )
            ),
            updated_at = ?
    """, (TS,))

    print(f'[P4] ttl_asserted=1: {n_upd} edges cập nhật')

    # Tóm tắt sau rebuild
    stats = conn.execute("""
        SELECT consensus_status, COUNT(*) c FROM lineage_edge_consensus
        GROUP BY consensus_status ORDER BY c DESC
    """).fetchall()
    for s in stats:
        print(f'  {s["consensus_status"]}: {s["c"]:,}')
    return n_upd

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def load_all_ttl():
    """Generator: parse tất cả TTL files trong TTL_DIR."""
    files = sorted(
        f for f in os.listdir(TTL_DIR)
        if f.endswith('.ttl') and os.path.isfile(os.path.join(TTL_DIR, f))
    )
    ok = fail = 0
    for fname in files:
        try:
            p = parse_ttl(os.path.join(TTL_DIR, fname))
            if p:
                ok += 1
                yield p
            else:
                fail += 1
        except Exception as ex:
            fail += 1
            print(f'  [lỗi parse] {fname}: {ex}')
    print(f'[load] Đã parse: {ok} thành công | {fail} lỗi')


def run(dry_run, phase_only=None, skip_preflight=False):
    if not os.path.exists(DB_PATH):
        print(f'[lỗi] Không tìm thấy DB: {DB_PATH}')
        sys.exit(1)
   
    print(f'[start] {"DRY-RUN" if dry_run else "APPLY"} — {TS}')
    print(f'[db]    {DB_PATH}')
    print(f'[ttl]   {TTL_DIR}')
   
    # [T203] CỔNG CHẶN — phát hiện lỗi TTL TRƯỚC khi nạp.
    # L1 nhãn đảo sang người khác · L2 nhãn không liên quan · L3 file rdflib hỏng
    # ⇒ exit 1, KHÔNG nạp. L4 mojibake Ð/Đ · L5 dila_id đụng ⇒ cảnh báo, vẫn cho chạy.
    if not skip_preflight:
        try:
            import t204_ttl_preflight as _pf
            blocking, warnings, _all = _pf.preflight(TTL_DIR, DB_PATH)
            if blocking or warnings:
                print('[preflight] ————————————————————————————————')
                if blocking:
                    print(f'[preflight] [CHẶN] {len(blocking)} lỗi:')
                    for b in blocking[:20]:
                        print('   %s %-34s %s' % (b['code'], b['file'], b['msg']))
                    if len(blocking) > 20:
                        print('   … còn %d' % (len(blocking) - 20))
                if warnings:
                    print(f'[preflight] [CẢNH BÁO] {len(warnings)} mục '
                          f'(L4 mojibake Ð/Đ · L5 dila_id đụng)')
                if blocking:
                    print('[preflight] DỪNG. Sửa TTL rồi chạy lại, hoặc '
                          '--skip-preflight nếu biết chắc là sai báo.')
                    sys.exit(1)
                print('[preflight] Không có lỗi chặn — tiếp tục (có cảnh báo).')
                print('[preflight] ————————————————————————————————')
        except ImportError:
            print('[preflight] (không có t204_ttl_preflight — bỏ qua kiểm tra)')
   
    # Load tất cả TTL vào memory (1038 files, ~5MB text, chấp nhận-nhỏ-n đọc)
    print('[load] Đang parse 1038 TTL files...')
    parsed = list(load_all_ttl())
    print(f'[load] Tổng: {len(parsed)} records')

    conn = connect()
    try:
        vi_idx, zh_idx = build_vi_index(conn)
        print(f'[index] vi_index={len(vi_idx):,}  zh_index={len(zh_idx):,}')

        if phase_only is None or phase_only == 1:
            phase1_upsert_persons(conn, parsed, vi_idx, zh_idx, dry_run)
            if not dry_run: conn.commit()

        if phase_only is None or phase_only == 2:
            phase2_upsert_relations(conn, parsed, dry_run)
            if not dry_run: conn.commit()

        if phase_only is None or phase_only == 3:
            phase3_bridge_to_assertions(conn, dry_run)
            if not dry_run: conn.commit()

        if phase_only is None or phase_only == 4:
            phase4_rebuild_consensus(conn, dry_run)
            if not dry_run: conn.commit()

        if not dry_run:
            # Tóm tắt cuối
            n_ttl = conn.execute("SELECT COUNT(*) FROM lineage_edge_assertions WHERE source_code='TTL'").fetchone()[0]
            n_ttl_c = conn.execute("SELECT COUNT(*) FROM lineage_edge_consensus WHERE ttl_asserted=1").fetchone()[0]
            print(f'\n[done] lineage_edge_assertions[TTL]: {n_ttl:,}')
            print(f'[done] lineage_edge_consensus ttl_asserted=1: {n_ttl_c:,}')
        print('[done] Hoàn tất.')

    except Exception as e:
        conn.rollback()
        print(f'[lỗi] {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description='ETL T185 — TTL full import')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run', action='store_true', help='Chỉ báo cáo, không ghi DB')
    g.add_argument('--apply',   action='store_true', help='Chạy thật, ghi vào DB')
    ap.add_argument('--phase', type=int, choices=[1,2,3,4],
                    help='chạy 1 phase cụ thể (1-4)')
    ap.add_argument('--skip-preflight', action='store_true',
                    help='[T203] bỏ qua cổng chặn TTL (chỉ dùng khi biết chắc báo sai)')
    args = ap.parse_args()
    run(dry_run=args.dry_run, phase_only=args.phase,
        skip_preflight=args.skip_preflight)


if __name__ == '__main__':
    main()

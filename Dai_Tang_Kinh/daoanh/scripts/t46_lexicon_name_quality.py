"""T46 — Person name_vi quality via lexicon cross-reference.

Extracts Vietnamese-Chinese name pairs from 22 Buddhist dictionary definitions,
cross-references with people.name_vi to find auto-phiên-âm errors.

Usage:
  python t46_lexicon_name_quality.py            # dry-run report only
  python t46_lexicon_name_quality.py --apply-clear  # update CLEAR cases in DB
  python t46_lexicon_name_quality.py --output report.md  # save markdown report
"""
import sys, os, io, re, sqlite3, collections, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, 'data', 'lineage.db')

# Particles/fragments that indicate the extracted name is part of a sentence, not a pure name
FRAGMENT_WORDS = re.compile(
    r'\b(như|trong|với|hay|theo|của|về|từ|khi|mà|để|là|có|cho|được|và|hoặc|'
    r'sau|trước|qua|đến|đi|ra|vào|lên|xuống|lại|đã|sẽ|đang|cũng|rồi)\b',
    re.IGNORECASE
)

# Vietnamese-Chinese name pair pattern in definitions
# Matches: "Vietnamese Name (漢字{2-8})"
VN_ZH_PAT = re.compile(
    r'([\wÀ-ɏẠ-ỹ]+(?:\s+[\wÀ-ɏẠ-ỹ]+){0,4})'
    r'\s*\(([^\)]{2,8})\)',
    re.UNICODE
)

# Chinese character range
ZH_CHAR = re.compile(r'[一-鿿]')

# Honorific prefixes to strip from VN names when comparing
HONORIFICS = re.compile(
    r'^(Lục Tổ|Tổ|Thiền Sư|Đại Sư|Hòa Thượng|Hòa Thưởng|Ngài|Đức|Pháp Sư|'
    r'Cư Sĩ|Quốc Sư|Tôn Giả|Đại Đức|Bổn Sư)\s+',
    re.IGNORECASE
)

# Systematic corrections: if current name matches LEFT pattern but dict gives RIGHT
CLEAR_PATTERNS = [
    # (re_current, re_dict, description)
    (re.compile(r'^Tuệ '), re.compile(r'^Huệ '), 'Tuệ→Huệ (慧 convention)'),
    (re.compile(r'Kim Cương'), re.compile(r'Kim Cang'), 'Kim Cương→Kim Cang (金剛)'),
    (re.compile(r'^Chính '), re.compile(r'^Chánh '), 'Chính→Chánh (正 convention)'),
    (re.compile(r'Nhuộm'), re.compile(r'Nhiễm'), 'Nhuộm→Nhiễm (染)'),
    (re.compile(r'Chừng'), re.compile(r'Trừng'), 'Chừng→Trừng (澄)'),
    (re.compile(r'^Tuệ$'), re.compile(r'^Huệ$'), 'Tuệ→Huệ single char'),
    # Additional clear patterns from data analysis
    (re.compile(r'Bàn Nhược'), re.compile(r'Bát Nhã'), 'Bàn Nhược→Bát Nhã (般若 PG term)'),
    (re.compile(r'Tông Vắng'), re.compile(r'Tông Vĩnh'), 'Vắng→Vĩnh (永 sai phiên âm)'),
    (re.compile(r'Pháp Cua'), re.compile(r'Pháp Nhãn'), 'Cua→Nhãn (眼 sai phiên âm)'),
    (re.compile(r'Cư Trốn'), re.compile(r'Cư Độn'), 'Trốn→Độn (遁 sai phiên âm)'),
    (re.compile(r'Phật Chòng'), re.compile(r'Phật Châu'), 'Chòng→Châu (洲 sai phiên âm)'),
    (re.compile(r'Hiểm Day'), re.compile(r'Hiểm Nhai'), 'Day→Nhai (崖 sai phiên âm)'),
    (re.compile(r'Lâm Chuông'), re.compile(r'Lâm Chung'), 'Chuông→Chung (鐘 trong tên người)'),
    (re.compile(r'Khoảng Pháp'), re.compile(r'Khoáng Pháp'), 'Khoảng→Khoáng (曠 sai dấu)'),
    (re.compile(r'Vân Tê '), re.compile(r'Vân Thê '), 'Tê→Thê (棲 sai phiên âm)'),
    (re.compile(r'Chu Hoằng'), re.compile(r'Châu Hoằng'), 'Chu→Châu (袾 sai phiên âm)'),
    (re.compile(r'Ngộ Khe'), re.compile(r'Ngộ Khê'), 'Khe→Khê (溪 chuẩn PG)'),
    (re.compile(r'Vô Tương'), re.compile(r'Vô Tướng'), 'Tương→Tướng (相 trong tên người)'),
    (re.compile(r'Kiêu Thây Ca'), re.compile(r'Kiều Thi Ca'), 'Kiêu Thây Ca→Kiều Thi Ca (憍尸迦)'),
    (re.compile(r'Minh Tẩu Tày'), re.compile(r'Minh Tẩu Tề'), 'Tày→Tề (齊 sai phiên âm)'),
]

# Known corrections for specific person_ids where pattern matching is insufficient
KNOWN_CORRECTIONS = {
    # person_id: (proposed_vi, reason)
    'A004928': ('Bát Nhã', '般若 — Buddhist term phải là Bát Nhã'),
    'A006942': ('Vô Tướng', '無相 — Tướng đúng hơn Tương trong tên người'),
    'A001394': ('Vân Thê Châu Hoằng', '雲棲袾宏 — Thê/Châu đúng hơn Tê/Chu'),
    'A035339': ('Pháp Nhãn', '法眼 — Nhãn=眼, không phải Cua'),
    'A004502': ('Tông Vĩnh', '宗永 — Vĩnh=永, không phải Vắng'),
    'A010681': ('Long Nha Cư Độn', '龍牙居遁 — Độn=遁, không phải Trốn'),
    'A039083': ('Phật Châu Tiên Anh', '佛洲仙英 — Châu=洲, không phải Chòng'),
    'A027732': ('Hiểm Nhai Xảo An', '嶮崖巧安 — Nhai=崖, không phải Day'),
    'A048076': ('Lâm Chung', '林鐘 — Chung=鐘 trong tên người'),
    'A005864': ('Khoáng Pháp Sư', '曠法師 — Khoáng=曠, không phải Khoảng'),
    'A032779': ('Ngộ Khê', '悟溪 — Khê=溪 chuẩn PG'),
    'A016769': ('Kiều Thi Ca', '憍尸迦 — phiên âm Sanskrit Kauśika'),
    'A026707': ('Minh Tẩu Tề Triết', '明叟齊哲 — Tề=齊, không phải Tày'),
    # Đợt 2 — từ REVIEW list
    'A039690': ('Thủy Nguyệt', '水月 — Héo là sai hoàn toàn, Thủy=水'),
    'A046680': ('Nguyên Hải', '源海 — Nguồn là dịch nghĩa, Nguyên=phiên âm đúng'),
    'A041542': ('Nguyên Thanh', '源清 — Nguồn→Nguyên (源 phiên âm)'),
    'A000288': ('Vĩnh Quán', '永觀 — Vắng→Vĩnh (永), Quan→Quán (觀 PG)'),
    'A010291': ('Thạch Đầu Hy Thiên', '石頭希遷 — Hơi→Hy (希 sai phiên âm nghiêm trọng)'),
    'A001060': ('Hoàn Khê Duy Nhất', '環溪惟一 — Khe→Khê (溪 chuẩn PG)'),
    'A002525': ('Tỳ Rô Bác Xoa', '毘嚕博叉 — Bì Rủa sai phiên âm Sanskrit Virūpākṣa'),
    'A021255': ('Thạch Sương Thủ Tôn', '石霜守孫 — Thú→Thủ (守=Thủ)'),
    'A021153': ('Thủ Nhân', '守仁 — Thú→Thủ (守=Thủ)'),
    'A000360': ('Thủ Kiên', '守堅 — Thú→Thủ (守=Thủ)'),
    'A001480': ('Thánh Thủ', '聖守 — Thú→Thủ (守=Thủ)'),
    'A004628': ('Diệu Trạm Huệ', '妙湛慧 — Đậm→Trạm (湛 sai phiên âm nghiêm trọng)'),
    'A010291': ('Thạch Đầu Hy Thiên', '石頭希遷 — Hơi→Hy (希 sai phiên âm)'),
    'A010678': ('Sơ Sơn Khuông Nhân', '疎山匡仁 — Khuôn→Khuông (匡 sai dấu)'),
    'A023234': ('Quán Đảnh', '灌頂 — Đảnh=頂 thuật ngữ PG, Đính sai'),
    'A042159': ('Trạm Nhiên', '湛然 — Đậm→Trạm (湛 sai phiên âm nghiêm trọng)'),
    'A015443': ('Tây Giản Tử Đàm', '西礀子曇 — phiên âm đúng hơn Tây 礀 Tí Đàm'),
    'A018774': ('Trí Hựu', '致祐 — Nhí→Trí, Hữu→Hựu (祐 cổ)'),
    # Đợt 3
    'A018907': ('Trương Tử Hoa', '張子華 — Tí→Tử (子=Tử không phải Tí)'),
    'A003811': ('Thê Hà', '棲霞 — Tê→Thê (棲 chuẩn)'),
    'A007292': ('Thiếu Khang', '少康 — Thiểu→Thiếu (少 trong tên người)'),
    'A000564': ('Cô Vân Hoài Trang', '孤雲懷弉 — 弉 ký tự hiếm → Trang'),
    'A019158': ('Trọng Hối', '仲晦 — Hổi→Hối (晦 sai dấu)'),
    'A015857': ('Thời Khởi', '時起 — Thì→Thời (時 chuẩn PG)'),
    'A000423': ('Hành Mãn', '行滿 — Hàng→Hành (行 trong tên PG)'),
    'A023008': ('Hành Thật', '行實 — Hàng→Hành; Thực→Thật (PG Nam truyền)'),
    'A019741': ('Hành Nhân', '行人 — Hàng→Hành (行 trong tên PG)'),
}


def is_clear_correction(current_vi, dict_vi):
    """Return (True, reason) if this is an unambiguous name correction."""
    for pat_cur, pat_dict, desc in CLEAR_PATTERNS:
        if pat_cur.search(current_vi) and pat_dict.search(dict_vi):
            return True, desc
    return False, ''


def extract_name_pairs(conn):
    """Extract (zh_name → set of vn_forms) from lexicon definitions."""
    name_map = collections.defaultdict(collections.Counter)

    rows = conn.execute('SELECT definition, source FROM lexicon WHERE definition IS NOT NULL').fetchall()
    for defn, source in rows:
        if not defn:
            continue
        for m in VN_ZH_PAT.finditer(defn):
            vn_name = m.group(1).strip()
            zh_cand = m.group(2).strip()

            if not ZH_CHAR.search(zh_cand):
                continue
            if not (2 <= len(zh_cand) <= 8):
                continue
            if not re.match(r'^[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚẮẶẸẺẼẾỀỆỌỎỖỘỢỤỦỨỪỬỴỲ]', vn_name):
                continue
            if not (5 <= len(vn_name) <= 35):
                continue
            if FRAGMENT_WORDS.search(vn_name):
                continue

            name_map[zh_cand][vn_name] += 1

    return name_map


def build_corrections(conn, name_map):
    """Cross-reference with people table to find name corrections."""
    all_people = conn.execute(
        'SELECT id, name_zh, name_vi, dynasty FROM people WHERE name_zh IS NOT NULL'
    ).fetchall()
    people_by_zh = {}
    for pid, zh, vi, dynasty in all_people:
        if zh not in people_by_zh:
            people_by_zh[zh] = (pid, vi, dynasty)

    corrections = []
    for zh, vn_counter in name_map.items():
        if zh not in people_by_zh:
            continue
        pid, cur_vi, dynasty = people_by_zh[zh]
        if not cur_vi:
            continue

        # Normalize: strip honorifics for comparison
        cur_clean = HONORIFICS.sub('', cur_vi).strip()

        for vn_name, count in vn_counter.most_common(3):
            dict_clean = HONORIFICS.sub('', vn_name).strip()

            if dict_clean == cur_clean:
                continue  # already correct

            # Skip obvious sentence fragments
            if len(dict_clean.split()) > 4:
                continue

            is_clear, reason = is_clear_correction(cur_clean, dict_clean)
            corrections.append({
                'person_id': pid,
                'name_zh': zh,
                'current_vi': cur_vi,
                'dict_vi': vn_name,
                'dict_clean': dict_clean,
                'count': count,
                'dynasty': dynasty or '',
                'is_clear': is_clear,
                'clear_reason': reason,
            })

    # Apply known corrections for specific person_ids
    known_pids = {c['person_id'] for c in corrections}
    for pid, (proposed, reason) in KNOWN_CORRECTIONS.items():
        if pid in known_pids:
            # Mark existing entry as CLEAR with known reason
            for c in corrections:
                if c['person_id'] == pid and not c['is_clear']:
                    c['is_clear'] = True
                    c['clear_reason'] = reason
                    c['dict_clean'] = proposed
                    break
        else:
            # Person not in corrections list (name already matches dict) — skip
            pass

    corrections.sort(key=lambda x: (-x['is_clear'], -x['count'], x['name_zh']))
    return corrections


def apply_corrections(conn, corrections, dry_run=True):
    """Update people.name_vi for CLEAR corrections."""
    clear_cases = [c for c in corrections if c['is_clear']]
    print(f'\n{"DRY RUN — " if dry_run else ""}Applying {len(clear_cases)} CLEAR corrections...')

    updated = 0
    for c in clear_cases:
        new_vi = c['dict_clean']
        if dry_run:
            print(f'  WOULD UPDATE [{c["person_id"]}] {c["name_zh"]}: {c["current_vi"]!r} → {new_vi!r}  ({c["clear_reason"]})')
        else:
            conn.execute(
                'UPDATE people SET name_vi = ? WHERE id = ? AND name_vi = ?',
                (new_vi, c['person_id'], c['current_vi'])
            )
            updated += 1
            print(f'  UPDATED [{c["person_id"]}] {c["name_zh"]}: {c["current_vi"]!r} → {new_vi!r}')

    if not dry_run:
        conn.commit()
        print(f'  Committed {updated} updates.')
    return len(clear_cases)


def create_correction_table(conn, corrections):
    """Store all corrections in person_name_correction table."""
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS person_name_correction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NOT NULL,
        name_zh TEXT,
        current_vi TEXT,
        proposed_vi TEXT,
        source TEXT DEFAULT 'lexicon',
        is_clear INTEGER DEFAULT 0,
        clear_reason TEXT,
        dict_frequency INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        reviewed_by TEXT,
        reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(person_id, proposed_vi)
    );
    CREATE INDEX IF NOT EXISTS idx_pnc_person ON person_name_correction(person_id);
    CREATE INDEX IF NOT EXISTS idx_pnc_status ON person_name_correction(status);
    """)
    conn.commit()

    inserted = 0
    for c in corrections:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO person_name_correction
                   (person_id, name_zh, current_vi, proposed_vi, source, is_clear, clear_reason, dict_frequency)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (c['person_id'], c['name_zh'], c['current_vi'], c['dict_clean'],
                 'lexicon', 1 if c['is_clear'] else 0, c['clear_reason'], c['count'])
            )
            inserted += conn.execute('SELECT changes()').fetchone()[0]
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    print(f'Inserted {inserted} rows into person_name_correction')
    return inserted


def print_report(corrections, output_path=None):
    lines = []
    lines.append('# T46 — Person name_vi Lexicon Cross-Reference Report')
    lines.append(f'\nTotal candidates: {len(corrections)}')

    clear = [c for c in corrections if c['is_clear']]
    review = [c for c in corrections if not c['is_clear']]
    lines.append(f'CLEAR corrections: {len(clear)}')
    lines.append(f'REVIEW needed: {len(review)}')

    lines.append('\n## CLEAR Corrections (Systematic Errors)\n')
    lines.append('| person_id | name_zh | Current | Dict | Reason |')
    lines.append('|-----------|---------|---------|------|--------|')
    for c in clear[:50]:
        lines.append(f'| {c["person_id"]} | {c["name_zh"]} | {c["current_vi"]} | **{c["dict_clean"]}** | {c["clear_reason"]} |')

    lines.append('\n## REVIEW Needed\n')
    lines.append('| person_id | name_zh | Dynasty | Current | Dict | Freq |')
    lines.append('|-----------|---------|---------|---------|------|------|')
    for c in review[:50]:
        lines.append(f'| {c["person_id"]} | {c["name_zh"]} | {c["dynasty"]} | {c["current_vi"]} | {c["dict_clean"]} | {c["count"]} |')

    report = '\n'.join(lines)
    print(report)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'\nReport saved to: {output_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply-clear', action='store_true', help='Apply CLEAR corrections to DB')
    parser.add_argument('--output', type=str, help='Save markdown report to file')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    print('Extracting Vietnamese-Chinese name pairs from lexicon...')
    name_map = extract_name_pairs(conn)
    print(f'  Extracted {len(name_map)} unique ZH names with VN forms')

    print('Cross-referencing with people table...')
    corrections = build_corrections(conn, name_map)
    print(f'  Found {len(corrections)} correction candidates')

    print_report(corrections, args.output)

    print('\nCreating person_name_correction table...')
    create_correction_table(conn, corrections)

    if args.apply_clear:
        apply_corrections(conn, corrections, dry_run=False)
    else:
        apply_corrections(conn, corrections, dry_run=True)

    conn.close()
    print('\nDone.')


if __name__ == '__main__':
    main()

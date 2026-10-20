"""T05 — TTL name_vi ETL: scan all TTL files, extract zh-vi name pairs, update people.name_vi.

Pass 1: Files with @vi rdfs:label (data/ttl/old/ + ontology/monks/TTL/)
         → direct name_zh → name_vi pairs
Pass 2: Files A######.ttl (ontology/monks/)
         → verify name_zh matches people table (DILA ID = filename)
         → extract bkg:hasDisciple lineage edges (optional)

Usage:
  python t05_ttl_namevi_etl.py               # dry-run report
  python t05_ttl_namevi_etl.py --apply       # update people.name_vi
  python t05_ttl_namevi_etl.py --apply --also-verify-zh  # also verify name_zh
"""
import sys, io, os, re, glob, sqlite3, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(BASE, 'data', 'lineage.db')

TTL_DIRS_VI = [
    os.path.join(BASE, 'data', 'ttl'),          # root: 910 files (TS-*, Cs-*, Ton-*)
    os.path.join(BASE, 'data', 'ttl', 'old'),   # 16 old files
]
TTL_DIR_DILA = os.path.join(BASE, '..', 'ontology', 'monks')  # 48k A######.ttl

PAT_MAIN_MONK = re.compile(
    r'<ex:monk/[^>]+>\s+a\s+<?bkg:Monk>?\s*;(.*?)(?=\n<|\Z)', re.DOTALL)
PAT_LABEL_ZH   = re.compile(r'rdfs:label\s+"([^"]{2,30})"@zh')
PAT_LABEL_VI   = re.compile(r'rdfs:label\s+"([^"]{3,40})"@vi')
PAT_DILA_FILE  = re.compile(r'^(A\d{6})\.ttl$')
HAS_ZH_CHAR    = re.compile(r'[一-鿿]')


def is_vi_name(text):
    """True if text looks like a short Vietnamese proper name."""
    text = text.strip()
    if not (4 <= len(text) <= 40):
        return False
    if HAS_ZH_CHAR.search(text):
        return False
    if '_' in text:  # underscore = slug/URI fragment, not a name
        return False
    words = text.split()
    if not words:
        return False
    # Every word must start uppercase (Vietnamese proper noun convention)
    if not all(w[0].isupper() for w in words if w):
        return False
    # Reject obvious non-names
    REJECTS = {'Ngài', 'Phật', 'Đức', 'Xuất', 'Nhập', 'Trú', 'Viên', 'Xem',
               'Không', 'Với', 'Trong', 'Theo', 'Thời', 'Khi', 'Nơi', 'Ở'}
    if words[0] in REJECTS:
        return False
    # Require at least 2 words (single-word names are rare and often ambiguous)
    if len(words) < 2:
        return False
    return True


PAT_MAIN_URI  = re.compile(r'<(ex:monk/[^>]+)>\s+a\s+<?bkg:Monk')
PAT_APPELL_ZH = re.compile(r'<(ex:monk/[^>]+)>\s+rdfs:label\s+"([^"]{2,30})"@zh')

# Pattern để tìm @vi label thuộc về main entity declaration block
# Block kết thúc trước khi gặp sub-resource statement đầu tiên
PAT_MAIN_BLOCK_VI = re.compile(
    r'<ex:monk/([^>]+)>\s+a\s+<?bkg:Monk>?[^.]+?rdfs:label\s+"([^"]{3,40})"@vi',
    re.DOTALL)

# Các prefix honorific cần strip khỏi @vi label (TTL thêm, DILA không có)
_VI_HONORIFIC_PREFIXES = (
    'Tôn Giả ', 'Bồ Tát ', 'Thiền Sư ', 'Đại Sư ',
    'TS ', 'HT ', 'NS ', 'Ngài ', 'Tổ ',
)


def _clean_vi_label(text):
    """Strip honorific prefix và replace _ với space (slug artifact)."""
    text = text.strip()
    for pfx in _VI_HONORIFIC_PREFIXES:
        if text.startswith(pfx):
            text = text[len(pfx):].strip()
            break
    return text.replace('_', ' ').strip()


def parse_ttl_name_pair(content):
    """Extract (name_zh, name_vi) from a monk TTL file.

    Strategy:
    - main_uri: from '<ex:monk/X> a bkg:Monk'
    - name_vi: rdfs:label @vi trên main entity block (trước sub-resources)
               Xử lý: strip prefix "TS ", replace _ → space
    - name_zh: rdfs:label @zh trên appellation resources có URI slug bắt đầu bằng main slug
    """
    # Find main entity URI
    m = PAT_MAIN_URI.search(content)
    if not m:
        return None, None
    main_uri = m.group(1)  # e.g. "ex:monk/dao_xuoc"
    main_slug = main_uri.split('/')[-1]  # e.g. "dao_xuoc"

    # name_vi: ưu tiên lấy từ main entity block (trước sub-resource lines)
    # Chiến lược: tìm @vi labels có URI là CHÍNH xác main_uri (appellation block)
    # HOẶC lấy @vi đầu tiên trong file nhưng clean và kiểm tra
    main_vi = None

    # Bước 1: Tìm appellation sub-resource của CHÍNH main entity có @vi
    # Pattern: <ex:monk/MAIN_SLUG_xxx> rdfs:label "..."@vi với hasAppellationType
    # Đây là tên chính thức của monk (Dharma name, secular name, v.v.)
    # Ưu tiên: appellation sub-resource với URI bắt đầu bằng main_slug + "_" + tên

    # Bước 2 đơn giản hơn: lấy @vi đầu tiên trong file, clean prefix/underscore
    for line in content.splitlines():
        mv = PAT_LABEL_VI.search(line)
        if mv:
            cleaned = _clean_vi_label(mv.group(1))
            if is_vi_name(cleaned):
                main_vi = cleaned
                break

    # name_zh: look for @zh labels on resources whose URI starts with main slug
    name_zh = None
    for uri, zh in PAT_APPELL_ZH.findall(content):
        uri_slug = uri.split('/')[-1]
        if uri_slug.startswith(main_slug) and HAS_ZH_CHAR.search(zh):
            name_zh = zh
            break

    # Fallback zh: check if main slug appears anywhere in the uri_slug
    if not name_zh:
        for uri, zh in PAT_APPELL_ZH.findall(content):
            if HAS_ZH_CHAR.search(zh):
                uri_slug = uri.split('/')[-1]
                if main_slug in uri_slug:
                    name_zh = zh
                    break

    return name_zh, main_vi


def scan_vi_files(dirs):
    """Pass 1: scan TTL files, extract main monk vi name + zh name."""
    pairs = {}  # name_zh → name_vi
    found_files = 0
    vi_only = 0
    for d in dirs:
        d = os.path.normpath(d)
        if not os.path.isdir(d):
            print(f"  [SKIP] dir not found: {d}")
            continue
        files = glob.glob(os.path.join(d, '*.ttl')) + glob.glob(os.path.join(d, '**', '*.ttl'), recursive=True)
        for fpath in files:
            found_files += 1
            try:
                content = open(fpath, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            zh, vi = parse_ttl_name_pair(content)
            if vi and zh:
                pairs[zh] = vi
            elif vi:
                vi_only += 1
    print(f"  Pass 1 scanned: {found_files} files → {len(pairs)} zh-vi pairs ({vi_only} vi-only, no zh)")
    return pairs


def scan_dila_files(dila_dir, conn, apply=False, verify_zh=False):
    """Pass 2: scan A######.ttl, verify name_zh via DILA ID."""
    dila_dir = os.path.normpath(dila_dir)
    if not os.path.isdir(dila_dir):
        print(f"  [SKIP] dila dir not found: {dila_dir}")
        return {}

    # Load people index: id → (name_zh, name_vi)
    people = {row[0]: (row[1], row[2]) for row in
              conn.execute("SELECT id, name_zh, name_vi FROM people WHERE id LIKE 'A%'")}

    files = glob.glob(os.path.join(dila_dir, 'A??????.ttl'))
    total = len(files)
    zh_mismatch = []
    no_match = 0
    checked = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        m = PAT_DILA_FILE.match(fname)
        if not m:
            continue
        dila_id = m.group(1)
        if dila_id not in people:
            no_match += 1
            continue

        checked += 1
        if verify_zh:
            try:
                content = open(fpath, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            ttl_zh = PAT_LABEL_ZH.findall(content)
            db_zh = people[dila_id][0] or ''
            if ttl_zh and ttl_zh[0] != db_zh:
                zh_mismatch.append((dila_id, db_zh, ttl_zh[0]))

    print(f"  Pass 2: {total} A######.ttl, {checked} matched to DB, {no_match} no DB match")
    if verify_zh:
        print(f"  name_zh mismatches: {len(zh_mismatch)}")
        for pid, db, ttl in zh_mismatch[:10]:
            print(f"    [{pid}] DB='{db}' TTL='{ttl}'")
    return {}


def load_marcus_index(conn):
    """Load MARCUS reference: name_zh → marcus_node_id.
    Dùng để cross-confirm: khi TTL pair (zh→vi) khớp MARCUS, confidence cao hơn.
    """
    idx = {}
    for row in conn.execute("SELECT node_id, label FROM marcus_reference WHERE label IS NOT NULL"):
        if row[1]:
            idx.setdefault(row[1], []).append(row[0])
    return idx


def _syllable_count(text):
    """Đếm số âm tiết tiếng Việt (= số từ phân tách bằng space)."""
    return len(text.strip().split())


def report_matches(conn, pairs, apply=False):
    """Match TTL zh→vi pairs với DILA DB.

    Mục đích: xác nhận danh tính (TTL + MARCUS → đây là DILA ID nào).
    DILA là authoritative source — chỉ sửa khi TTL/Lexicon có bằng chứng rõ ràng:
      - Số âm tiết TTL core = số Hán tự (đảm bảo không thêm/bớt ký tự)
      - Không tiền tố danh hiệu (Tôn Giả, Thiền Sư v.v.)
      - Phiên âm khác nhau → dùng TTL/Lexicon làm bản dịch hiển thị
    """
    marcus_idx = load_marcus_index(conn)

    people_by_zh = {}
    for row in conn.execute("SELECT id, name_zh, name_vi FROM people WHERE name_zh IS NOT NULL"):
        pid, zh, vi = row
        if zh and zh not in people_by_zh:
            people_by_zh[zh] = (pid, vi)

    confirmed  = []   # DILA name_vi đúng, TTL xác nhận danh tính
    to_correct = []   # Số âm tiết đúng, không tiền tố → auto-apply nếu --apply

    for zh, ttl_vi in pairs.items():
        if zh not in people_by_zh:
            print(f"  [NO MATCH] {zh} → không tìm thấy trong DB")
            continue
        pid, dila_vi = people_by_zh[zh]

        marcus_flag = ' [MARCUS ✓]' if zh in marcus_idx else ''
        zh_len      = len(zh)

        # Strip tiền tố danh hiệu (TTL có thể thêm "Tôn Giả", "TS" v.v.)
        ttl_core = ttl_vi
        for pfx in _VI_HONORIFIC_PREFIXES:
            if ttl_vi.startswith(pfx):
                ttl_core = ttl_vi[len(pfx):].strip()
                break

        dila_syls = _syllable_count(dila_vi or '')
        core_syls = _syllable_count(ttl_core)

        if dila_vi == ttl_core:
            confirmed.append((pid, zh, dila_vi, marcus_flag))
        elif core_syls == zh_len and dila_syls == zh_len:
            # Số âm tiết đúng, không tiền tố, phiên âm khác → TTL là bản chuẩn
            to_correct.append((pid, zh, dila_vi, ttl_core, zh_len, marcus_flag))
        else:
            # TTL thêm danh hiệu không khớp số âm tiết → chỉ confirm danh tính, không sửa name_vi
            confirmed.append((pid, zh, dila_vi, marcus_flag))

    print(f"\nMATCH REPORT: {len(confirmed)+len(to_correct)} DILA persons confirmed via TTL")
    print(f"  Confirmed (DILA name_vi đúng): {len(confirmed)}")
    for pid, zh, dila, mf in confirmed:
        print(f"    [{pid}] {zh} → '{dila}'{mf}")

    if to_correct:
        mode = "APPLY" if apply else "DRY RUN"
        print(f"\n  {mode}: {len(to_correct)} phiên âm sai → dùng TTL làm bản hiển thị")
        print(f"  (Điều kiện: số âm tiết = số Hán tự, không tiền tố danh hiệu)")
        for pid, zh, dila, core, n, mf in to_correct:
            print(f"    [{pid}] {zh} ({n} Hán): '{dila}' → '{core}'{mf}")
        if apply:
            for pid, zh, dila, core, n, _mf in to_correct:
                conn.execute("UPDATE people SET name_vi=? WHERE id=? AND name_zh=?",
                             (core, pid, zh))
            conn.commit()
            print(f"  Committed {len(to_correct)} phonetic corrections.")

    return confirmed, to_correct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true',
                        help='Apply phonetic corrections (syllable-count verified, no honorific prefix)')
    parser.add_argument('--also-verify-zh', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB)

    print("=== Pass 1: Scan TTL files với @vi + @zh labels ===")
    pairs = scan_vi_files(TTL_DIRS_VI)
    print(f"  Pairs found: {len(pairs)}")
    for zh, vi in list(pairs.items())[:10]:
        print(f"  {zh} → {vi}")

    print("\n=== Pass 2: Scan A######.ttl (DILA ID → DB verify) ===")
    scan_dila_files(TTL_DIR_DILA, conn, apply=False, verify_zh=args.also_verify_zh)

    print("\n=== Match Report ===")
    confirmed, to_correct = report_matches(conn, pairs, apply=args.apply)

    total = len(confirmed) + len(to_correct)
    print(f"\nSummary: {len(pairs)} zh→vi pairs từ TTL → {total} DILA IDs confirmed")
    if to_correct and not args.apply:
        print(f"  {len(to_correct)} phonetic corrections pending → chạy --apply để áp dụng")
    conn.close()


if __name__ == '__main__':
    main()

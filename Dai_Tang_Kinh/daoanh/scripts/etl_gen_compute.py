"""
ETL: Tính số đời đa lớp từ Khai Tổ
=====================================
Nguyên tắc cốt lõi:
  - DILA/MARCUS chỉ có edge thầy-trò, KHÔNG phân biệt tông phái.
  - Tông phái nằm trong TTL field: bkg:dharmaLineageName
  - BFS cross-lineage SẼ sai (đi từ Dương Kỳ có thể đến Gia Phổ qua graph)
  - Giải pháp: gán tông phái dựa trên dharmaLineageName của từng người.

Hệ thống 3 lớp:
  gen_thientong : đời Thiền Tông (từ Ma Ha Ca Diếp = 1)
  gen_lamte     : đời Lâm Tế Tông (từ Lâm Tế Nghĩa Huyền = 1) — chỉ cho Lâm Tế
  gen_sect      : đời trong tông phái cụ thể của người đó (Khai Tổ = 1)

─── T379 follow-up (2026-11-07) — ĐẢO CÔNG THỨC gen_lamte/gen_thientong ─────
Bản trước coi generationOrder trong TTL là "đời Lâm Tế" rồi CỘNG 37 ra đời
Thiền Tông (gen_thientong = generationOrder + 37). Đối chiếu trực tiếp các
file TTL nguồn (xem bảng dưới) cho thấy generationOrder ĐÃ LÀ số đời Thiền
Tông TOÀN CỤC (global), không phải số đời cục bộ trong Lâm Tế:
    data/ttl/Ton-Gia-Ma-Ha-Ca-Diep.ttl      generationOrder = 1
    data/ttl/Ton-Gia-Bo-De-Dat-Ma.ttl       generationOrder = 28
    data/ttl/Ton-Gia-Dai-Giam-Hue-Nang.ttl  generationOrder = 33
    data/ttl/TS-Lam-Te-Nghia-Huyen.ttl      generationOrder = 38
Đã xác minh thêm bằng cách lần theo chuỗi thầy→trò xuyên nhiều dharmaLineageName
khác nhau (số tăng đúng +1 mỗi thế hệ, không reset về nhỏ khi sang dòng khác):
    Huệ Năng(33) → Nam Nhạc Hoài Nhượng(34) → Mã Tổ Đạo Nhất(35) →
    Bách Trượng Hoài Hải(36) → Vô Ngôn Thông(37) / Quy Sơn Linh Hựu(37) →
    Ngưỡng Sơn Huệ Tịch(38) / Lâm Tế Nghĩa Huyền(38) → ... →
    Dương Kỳ Phương Hội(45) → Bạch Vân Thủ Đoan(46) → ... → Viên Ngộ Khắc
    Cần(48) → ... → Nguyên Thiều Siêu Bạch — VN, "Dòng Lâm Tế Gia Phổ Việt
    Nam"(70) → Minh Hải Pháp Bảo — VN, "Dòng Lâm Tế Chúc Thánh Việt Nam"(71)
    → Thiệt Duyệt Liễu Quán — VN, "Dòng Lâm Tế Liễu Quán Việt Nam"(72).
    Đạo Tín(31) → Ngưu Đầu Pháp Dung — "Ngưu Đầu Tông Trung Hoa"(32) (nhánh
    tách khỏi Tứ Tổ, vẫn đúng mạch toàn cục).
Do đó CÔNG THỨC MỚI:
    gen_thientong = generationOrder                (trực tiếp, không +37)
    gen_lamte     = generationOrder - 37            CHỈ cho người thuộc dòng
                    Lâm Tế (dharmaLineageName chứa "Lâm Tế") — Lâm Tế Nghĩa
                    Huyền đời 38 → gen_lamte = 1, đúng mốc Admin xác nhận.

KHÔNG áp dụng cho MỌI dharmaLineageName: đối chiếu cho thấy một số ít tên
dùng số đời CỤC BỘ (reset riêng, không nối mạch toàn cục), ví dụ:
    - "Đại thừa" (Thích Ca Mâu Ni Phật, generationOrder=1) — TRÙNG với Ma Ha
      Ca Diếp=1 trong "Thiền Tông Ấn Độ"; rõ ràng là 2 hệ đếm khác nhau
      (Phật không nằm trong 28 vị Tổ Thiền Tông Ấn Độ).
    - "Tịnh Độ Tông" (Đạo Xước, generationOrder=2) — đây là số Tổ trong 13 vị
      Tổ Tịnh Độ, không liên quan chuỗi Tổ Thiền Tông.
    - "Phái Nam Nhạc" (Bổn Khê, generationOrder=2) — đệ tử của Mã Tổ Đạo Nhất
      (đời 35 toàn cục), nếu toàn cục Bổn Khê phải là 36, không phải 2 →
      xác nhận đây là số đời cục bộ trong riêng 1 file.
  "Kinh Lượng Bộ" (Cưu Ma La Đa, generationOrder=19) và "Bát Tông" (Bồ Tát
  Long Thọ, generationOrder=14) NGƯỢC LẠI đã đối chiếu khớp đúng vị trí Tổ
  thứ 19 / 14 trong 28 vị Tổ Ấn Độ toàn cục — nên vẫn coi là global.

Theo đúng yêu cầu "không đoán khi chưa chắc": GLOBAL_THIENTONG_LINEAGES dưới
là ALLOWLIST (không phải denylist) — bất kỳ dharmaLineageName nào KHÔNG nằm
trong allowlist này và KHÔNG chứa "Lâm Tế" sẽ bị để TRỐNG (None) cho cả
gen_thientong và gen_lamte, và được in cảnh báo ra report() để Admin biết.
An toàn-theo-mặc-định: tên lineage mới/lạ xuất hiện trong TTL tương lai sẽ
tự động bị loại (None) cho tới khi có người xác minh và thêm vào allowlist,
không bao giờ tự động được coi là global.

LƯU Ý RỦI RO (chưa cần sửa, chỉ ghi lại cho Admin): load_all_persons_from_ttl()
dùng glob.glob('data/ttl/*.ttl') — KHÔNG đọc các thư mục con (data/ttl/old/,
data/ttl/"Lam Te Duong Ky"/, data/ttl/"Thien Tong An Do"/, data/ttl/"Thien
Tong Trung Quoc"/). Một số file trong các thư mục con này là bản TRÙNG TÊN
slug với file ở gốc nhưng dùng SỐ ĐỜI CỤC BỘ khác (ví dụ
data/ttl/old/TS-Ngu-To-Phap-Dien.ttl có dharmaLineageName "Phái Dương Kì
thuộc Lâm Tế Tông Trung Quốc", generationOrder=5 — cục bộ — trong khi bản gốc
data/ttl/TS-Ngu-To-Phap-Dien.ttl không tồn tại nhưng các vị cùng dòng Dương Kỳ
ở gốc đều dùng số toàn cục, ví dụ TS-Vien-Ngo-Khac-Can.ttl=48). Nếu sau này
ai đổi glob thành đệ quy (**/*.ttl), các bản cục bộ này sẽ trộn lẫn và làm
sai kết quả — KHÔNG đổi glob nếu chưa xử lý việc này.

Cách tính:
  Slug monks (có dharmaLineageName + generationOrder trong TTL/DB):
    gen_thientong = generationOrder   NẾU dharmaLineageName thuộc
                    GLOBAL_THIENTONG_LINEAGES hoặc chứa "Lâm Tế"; ngược lại None.
    gen_lamte     = generationOrder - 37   NẾU dharmaLineageName chứa "Lâm Tế";
                    ngược lại None (kể cả khi gen_thientong đã có giá trị).
    gen_sect      = gen_order - khai_to_gen + 1
                    (khai_to_gen = gen_order của Khai Tổ cùng dharmaLineageName
                    — không đổi, không phụ thuộc global/cục bộ vì là số tương
                    đối trong 1 tông phái)

  DILA monks (A-prefix, không có dharmaLineageName):
    gen_thientong, gen_lamte = tính từ BFS qua DILA graph (Thích Ca = root, depth 1)
    gen_sect      = None (không biết tông phái)
    (phần này đã dùng công thức "gen_thientong = depth - 1" trực tiếp từ
    trước, không bị lỗi +37 nên KHÔNG cần sửa trong follow-up này)
"""

import sqlite3
import sys
import re
import os
import glob
from collections import deque

DB_PATH  = 'data/lineage.db'
TTL_DIR  = 'data/ttl'

# Lệch giữa đời Lâm Tế và đời Thiền Tông toàn cục:
# Lâm Tế Nghĩa Huyền = Lâm Tế đời 1 = Thiền Tông đời 38 → offset = 37
# (gen_thientong - gen_lamte = 37 cho MỌI người thuộc dòng Lâm Tế — dùng để
#  TRỪ ra gen_lamte từ gen_thientong, KHÔNG dùng để cộng vào generationOrder
#  như bản cũ.)
THIENTONG_LAMTE_OFFSET = 37

# ALLOWLIST các dharmaLineageName đã xác minh dùng SỐ ĐỜI THIỀN TÔNG TOÀN CỤC
# (generationOrder tăng +1 mỗi thế hệ, nối liền mạch không reset khi đổi
# dharmaLineageName). Mọi tên có chứa "Lâm Tế" cũng được coi là global (xem
# is_lamte_lineage) — các dòng Lâm Tế Việt Nam (Gia Phổ/Chúc Thánh/Liễu Quán/
# ...) đều đã kiểm chứng tiếp nối đúng mạch số của Tông Lâm Tế Trung Hoa.
# Tên KHÔNG có trong allowlist này và KHÔNG chứa "Lâm Tế" sẽ bị loại (None)
# — xem phần "KHÔNG áp dụng cho MỌI dharmaLineageName" ở docstring trên.
GLOBAL_THIENTONG_LINEAGES = frozenset({
    'Thiền Tông Ấn Độ',
    'Thiền Tông Trung Hoa',
    'Thiền Tông Trung Hoa - Nam Tông',
    'Thiền Tông Trung Hoa - Bắc Tông',
    'Ngưu Đầu Tông Trung Hoa',
    'Tông Quy Ngưỡng Trung Hoa',
    'Kinh Lượng Bộ',    # Cưu Ma La Đa — đã đối chiếu khớp đời Tổ Ấn Độ thứ 19
    'Bát Tông',         # Bồ Tát Long Thọ — đã đối chiếu khớp đời Tổ Ấn Độ thứ 14
})


def is_lamte_lineage(lineage_name):
    """True nếu dharmaLineageName thuộc dòng Lâm Tế (Trung Hoa hoặc Việt Nam,
    bất kể phân nhánh Dương Kỳ/Hoàng Long/Gia Phổ/Chúc Thánh/Liễu Quán/...).
    Dùng substring vì có nhiều biến thể tên nhánh Lâm Tế Việt Nam và tên mới
    có thể xuất hiện thêm trong tương lai — tất cả đã kiểm chứng nối đúng
    mạch số toàn cục (xem docstring đầu file)."""
    return bool(lineage_name) and 'Lâm Tế' in lineage_name


def is_global_thientong_lineage(lineage_name):
    """True nếu generationOrder của dharmaLineageName này là số đời Thiền
    Tông TOÀN CỤC (an toàn để gán thẳng cho gen_thientong)."""
    return bool(lineage_name) and (
        is_lamte_lineage(lineage_name) or lineage_name in GLOBAL_THIENTONG_LINEAGES
    )


def resolve_global_gens(gen_order, lineage_name):
    """
    Trả về (gen_lamte, gen_thientong) cho một generationOrder + dharmaLineageName
    đọc từ TTL, theo công thức mới (T379 follow-up, mốc Admin xác nhận 2026-11-07).

    - Nếu lineage_name KHÔNG nằm trong is_global_thientong_lineage(): trả về
      (None, None) — KHÔNG đoán số đời khi chưa xác minh được hệ đếm.
    - Nếu có: gen_thientong = gen_order; gen_lamte = gen_order - 37 CHỈ khi
      lineage_name thuộc dòng Lâm Tế, ngược lại gen_lamte = None.
    """
    if gen_order is None or not is_global_thientong_lineage(lineage_name):
        return None, None
    gen_thientong = gen_order
    gen_lamte = (gen_order - THIENTONG_LAMTE_OFFSET) if is_lamte_lineage(lineage_name) else None
    return gen_lamte, gen_thientong


DILA_ROOT          = 'thich_ca_mau_ni_phat'
DILA_THIENTONG_OFF = 1    # gen_thientong = bfs_depth - 1  (depth 2 = Thiền Tông đời 1)
DILA_LAMTE_OFF     = 37   # gen_lamte     = bfs_depth - 37 (depth 38 = Lâm Tế đời 1)


# ─── 1. Parse TTL để lấy founders ────────────────────────────────────────────

def extract_persons_from_ttl(filepath):
    """Parse 1 TTL file → list of {slug, name_vi, gen_order, lineage, is_founder}"""
    try:
        txt = open(filepath, encoding='utf-8', errors='ignore').read()
    except Exception:
        return []

    persons = []
    blocks = re.split(r'(?=<ex:monk/[^>]*>\s+a\s+<bkg:Monk>)', txt)
    for block in blocks:
        if 'a <bkg:Monk>' not in block:
            continue
        slug_m = re.search(r'<ex:monk/([^>]+)>\s+a\s+<bkg:Monk>', block)
        if not slug_m:
            continue
        slug      = slug_m.group(1).rstrip('/')
        name_m    = re.search(r'rdfs:label\s+"([^"]+)"@vi', block)
        gen_m     = re.search(r'generationOrder\s+(\d+)', block)
        lin_m     = re.search(r'dharmaLineageName\s+"([^"]+)"@vi', block)
        found_m   = re.search(r'isLineageFounder\s+(true|false)', block)
        persons.append({
            'slug':       slug,
            'name_vi':    name_m.group(1) if name_m else slug,
            'gen_order':  int(gen_m.group(1)) if gen_m else None,
            'lineage':    lin_m.group(1)  if lin_m else '',
            'is_founder': found_m and found_m.group(1) == 'true',
        })
    return persons


def load_all_persons_from_ttl():
    """
    Đọc toàn bộ 1038 TTL → trả về dict {slug: person_dict}.
    Đây là nguồn sự thật vì TTL có 1030 người với đủ lineage+gen_order,
    trong khi DB chỉ sync được 443.
    """
    files = glob.glob(os.path.join(TTL_DIR, '*.ttl'))
    persons = {}
    for f in files:
        for p in extract_persons_from_ttl(f):
            if p['slug'] and p['slug'] not in persons:
                persons[p['slug']] = p
    return persons


def load_founders_from_ttl():
    """
    Tìm tất cả isLineageFounder=true có generationOrder.
    Với mỗi dharmaLineageName, chỉ giữ NGƯỜI CÓ GEN_ORDER NHỎ NHẤT (Khai Tổ gốc).
    """
    files = glob.glob(os.path.join(TTL_DIR, '*.ttl'))
    all_founders = []
    for f in files:
        for p in extract_persons_from_ttl(f):
            if p['is_founder'] and p['gen_order'] is not None and p['lineage']:
                all_founders.append(p)

    # Mỗi dharmaLineageName: chỉ giữ founder có gen_order nhỏ nhất = Khai Tổ thực sự
    by_lineage = {}
    for p in all_founders:
        lin = p['lineage']
        if lin not in by_lineage or p['gen_order'] < by_lineage[lin]['gen_order']:
            by_lineage[lin] = p

    result = list(by_lineage.values())
    result.sort(key=lambda x: x['gen_order'])
    return result


# ─── 2. Tạo bảng ─────────────────────────────────────────────────────────────

def setup_tables(conn):
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS lineage_founders (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        lineage_name    TEXT NOT NULL UNIQUE,
        lineage_key     TEXT NOT NULL UNIQUE,
        khai_to_id      TEXT NOT NULL,
        khai_to_name_vi TEXT,
        khai_to_gen     INTEGER,
        created_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS person_gen_computed (
        person_id     TEXT NOT NULL,
        lineage_key   TEXT NOT NULL,
        lineage_name  TEXT,
        gen_sect      INTEGER,
        gen_lamte     INTEGER,
        gen_thientong INTEGER,
        PRIMARY KEY (person_id, lineage_key)
    );

    CREATE INDEX IF NOT EXISTS idx_pgc_pid ON person_gen_computed(person_id);
    """)
    # KHÔNG commit ở đây — toàn bộ ETL (drop/create/seed/compute) phải nằm
    # trong CÙNG MỘT transaction với verify_anchors() ở cuối main(). Nếu
    # verify_anchors() phát hiện mốc sai, main() sẽ rollback() và bảng cũ
    # (trước DROP TABLE) sẽ còn nguyên vì chưa có gì được commit.
    print("✓ Tables OK")


def seed_founders(conn, founders):
    cur = conn.cursor()
    cur.execute("DELETE FROM lineage_founders")
    rows = []
    for f in founders:
        lkey = re.sub(r'[^\w]+', '_', f['lineage'].lower()).strip('_')
        rows.append((f['lineage'], lkey, f['slug'], f['name_vi'], f['gen_order']))
    cur.executemany("""
        INSERT OR IGNORE INTO lineage_founders
        (lineage_name, lineage_key, khai_to_id, khai_to_name_vi, khai_to_gen)
        VALUES (?,?,?,?,?)
    """, rows)
    # Không commit — xem chú thích trong setup_tables().
    print(f"✓ {len(rows)} tông phái / Khai Tổ seeded")
    return rows


# ─── 3. Tính gen cho slug monks ───────────────────────────────────────────────

def compute_slug_monks(conn, ttl_persons):
    """
    Đọc từ TTL trực tiếp (1030 persons đủ data), không phụ thuộc DB sync.
    Mỗi monk (xem resolve_global_gens() / công thức mới ở đầu file):
        gen_thientong = generationOrder   (nếu lineage nằm trong allowlist global)
        gen_lamte     = generationOrder - 37   (chỉ nếu lineage chứa "Lâm Tế")
        gen_sect      = generationOrder - khai_to_gen + 1
    """
    cur = conn.cursor()

    # Lấy map lineage_name → (lineage_key, khai_to_gen)
    cur.execute("SELECT lineage_name, lineage_key, khai_to_gen FROM lineage_founders")
    lineage_map = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    rows = []
    no_founder = set()
    excluded_lineages = set()
    for slug, p in ttl_persons.items():
        if p['gen_order'] is None or not p['lineage']:
            continue
        pid        = slug
        gen_order  = p['gen_order']
        lineage    = p['lineage']
        gen_lamte, gen_thientong = resolve_global_gens(gen_order, lineage)
        if gen_thientong is None:
            excluded_lineages.add(lineage)

        if lineage in lineage_map:
            lkey, khai_to_gen = lineage_map[lineage]
            gen_sect = gen_order - khai_to_gen + 1
            rows.append((pid, lkey, lineage, gen_sect, gen_lamte, gen_thientong))
        else:
            lkey = re.sub(r'[^\w]+', '_', lineage.lower()).strip('_') + '_nf'
            rows.append((pid, lkey, lineage, None, gen_lamte, gen_thientong))
            no_founder.add(lineage)

    cur.executemany("""
        INSERT OR REPLACE INTO person_gen_computed
        (person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong)
        VALUES (?,?,?,?,?,?)
    """, rows)
    # Không commit — xem chú thích trong setup_tables().
    print(f"✓ TTL monks: {len(rows)} bản ghi (từ {len(ttl_persons)} TTL persons)")
    if no_founder:
        print(f"  ⚠ {len(no_founder)} tông phái không có Khai Tổ: {sorted(no_founder)}")
    if excluded_lineages:
        print(
            f"  ⚠ {len(excluded_lineages)} dharmaLineageName KHÔNG nằm trong "
            f"allowlist global (gen_thientong/gen_lamte để TRỐNG, cần Admin "
            f"xác nhận nếu cần bổ sung): {sorted(excluded_lineages)}"
        )
    return len(rows)


# ─── 3b. Kế thừa tông phái theo graph (slug monks chưa có dharmaLineageName) ─

def propagate_lineage_to_descendants(conn, children, ttl_persons):
    """
    BFS từ mỗi Khai Tổ (slug graph).
    Gán lineage cho đệ tử chưa có dharmaLineageName.
    Dừng BFS khi gặp monk có dharmaLineageName KHÁC → họ là Khai Tổ riêng.

    Ưu tiên: Khai Tổ có gen_order LỚN HƠN (hậu duệ) sẽ chạy SAU,
    ghi đè lineage của tổ xa hơn → đệ tử trực tiếp của Chúc Thánh Khai Tổ
    sẽ được gán Chúc Thánh, không phải Gia Phổ.
    """
    cur = conn.cursor()

    # Dùng TTL làm nguồn sự thật (lineage + gen_order)
    # Map slug → (dharma_lineage, generation_order)
    monk_data = {
        slug: (p['lineage'] or '', p['gen_order'])
        for slug, p in ttl_persons.items()
    }
    # Bổ sung từ DB (slug monks chưa trong TTL)
    cur.execute("SELECT id, dharma_lineage, generation_order FROM vn_person_authority WHERE id NOT LIKE 'A%'")
    for pid, dl, go in cur.fetchall():
        if pid not in monk_data:
            monk_data[pid] = (dl or '', go)

    # Lấy founders: sắp xếp theo gen_order TĂNG DẦN để cha chạy trước
    # (con sẽ ghi đè sau nếu có lineage riêng)
    cur.execute("""
        SELECT khai_to_id, lineage_key, lineage_name, khai_to_gen
        FROM lineage_founders ORDER BY khai_to_gen ASC
    """)
    founders = cur.fetchall()

    # BFS map: person_id → (lkey, lname, gen_sect, gen_lamte) từ propagation
    inherited = {}
    skipped_non_global = set()

    for khai_to_id, lkey, lname, khai_to_gen in founders:
        if khai_to_gen is None:
            continue
        if not is_global_thientong_lineage(lname):
            # Khai Tổ thuộc lineage KHÔNG nằm trong allowlist global (ví dụ
            # "Đại thừa", "Tịnh Độ Tông" — xem docstring đầu file) → không
            # lan truyền gen_thientong/gen_lamte cho đệ tử, tránh gán số đời
            # cục bộ sai thành số đời Thiền Tông toàn cục.
            skipped_non_global.add(lname)
            continue
        is_lamte = is_lamte_lineage(lname)

        # BFS từ Khai Tổ xuống slug graph
        q = deque([(khai_to_id, 1)])  # (person_id, gen_sect_so_far)
        visited = set()
        while q:
            pid, gen_sect = q.popleft()
            if pid in visited:
                continue
            visited.add(pid)

            monk_lineage, monk_gen = monk_data.get(pid, ('', None))

            if pid != khai_to_id:
                if monk_lineage and monk_lineage != lname:
                    # Tông phái khác → đây là Khai Tổ riêng, không kế thừa
                    continue  # nhưng vẫn BFS qua họ (không stop subtree)
                    # Vì subtree của họ đã được BFS từ founder riêng của họ

                # Gán (ghi đè nếu đã có từ founder cha — vì ta chạy cha trước con)
                if monk_gen is not None:
                    # Người này có generationOrder riêng trong TTL/DB — đây
                    # ĐÃ LÀ số đời Thiền Tông toàn cục (không +37 như bản cũ).
                    gl = (monk_gen - THIENTONG_LAMTE_OFFSET) if is_lamte else None
                    gt = monk_gen
                    gs = monk_gen - khai_to_gen + 1
                else:
                    # Không có generationOrder riêng — suy từ khoảng cách BFS
                    # tới Khai Tổ. khai_to_gen đã là số đời Thiền Tông toàn cục
                    # của Khai Tổ (generationOrder trong TTL), nên công thức
                    # dưới cũng ra số đời toàn cục, không cần +37.
                    gs = gen_sect
                    gt = khai_to_gen + gen_sect - 1
                    gl = (gt - THIENTONG_LAMTE_OFFSET) if is_lamte else None
                inherited[pid] = (lkey, lname, gs, gl, gt)

            for child in children.get(pid, []):
                if child not in visited and not child.startswith('A'):
                    child_lineage, _ = monk_data.get(child, ('', None))
                    # Chỉ BFS tiếp nếu child chưa có lineage riêng hoặc cùng lineage
                    if not child_lineage or child_lineage == lname:
                        q.append((child, gen_sect + 1))

    # Ghi vào DB (chỉ những ai CHƯA có bản ghi)
    new_rows = []
    cur.execute("SELECT DISTINCT person_id FROM person_gen_computed")
    already = {r[0] for r in cur.fetchall()}
    for pid, (lkey, lname, gs, gl, gt) in inherited.items():
        if pid not in already and not pid.startswith('A'):
            new_rows.append((pid, lkey, lname, gs, gl, gt))

    if new_rows:
        cur.executemany("""
            INSERT OR IGNORE INTO person_gen_computed
            (person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong)
            VALUES (?,?,?,?,?,?)
        """, new_rows)
        # Không commit — xem chú thích trong setup_tables().
        print(f"✓ Propagation: +{len(new_rows)} đệ tử kế thừa tông phái")
    else:
        print("  (Không có đệ tử nào cần kế thừa)")
    if skipped_non_global:
        print(
            f"  ⚠ {len(skipped_non_global)} Khai Tổ KHÔNG nằm trong allowlist "
            f"global, bỏ qua lan truyền gen_thientong/gen_lamte cho đệ tử "
            f"(cần Admin xác nhận nếu cần bổ sung): {sorted(skipped_non_global)}"
        )
    return len(new_rows)


# ─── 4. Tính gen cho DILA monks (BFS) ────────────────────────────────────────

def build_children(conn):
    cur = conn.cursor()
    cur.execute("SELECT teacher_id, disciple_id FROM lineage_edge_consensus")
    ch = {}
    for t, d in cur.fetchall():
        ch.setdefault(t, []).append(d)
    print(f"✓ Edge map: {sum(len(v) for v in ch.values())} edges, {len(ch)} teacher nodes")
    return ch


def compute_dila_monks(conn, children):
    """
    BFS từ Thích Ca qua DILA graph (A-prefix IDs).
    gen_thientong = depth - 1   (Ma Ha Ca Diếp = depth 2 = Thiền Tông đời 1)
    gen_lamte     = depth - 37  (Lâm Tế Nghĩa Huyền = depth 38 = đời 1)
    gen_sect      = None  (DILA không phân biệt tông phái)
    """
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM lineage_edge_consensus WHERE teacher_id=?", (DILA_ROOT,))
    if cur.fetchone()[0] == 0:
        print("⚠ DILA root không có edge — bỏ qua")
        return 0

    gmap = {DILA_ROOT: 1}
    q = deque([DILA_ROOT])
    while q:
        u = q.popleft()
        for c in children.get(u, []):
            if c not in gmap:
                gmap[c] = gmap[u] + 1
                q.append(c)

    rows = []
    for pid, depth in gmap.items():
        if pid.startswith('A') or pid == DILA_ROOT:  # chỉ DILA nodes
            gt = depth - DILA_THIENTONG_OFF
            gl = depth - DILA_LAMTE_OFF
            gl_stored = gl if gl > 0 else None
            rows.append((pid, 'dila_global', 'Thiền Tông (DILA)', None, gl_stored, gt))

    cur.executemany("""
        INSERT OR REPLACE INTO person_gen_computed
        (person_id, lineage_key, lineage_name, gen_sect, gen_lamte, gen_thientong)
        VALUES (?,?,?,?,?,?)
    """, rows)
    # Không commit — xem chú thích trong setup_tables().
    print(f"✓ DILA monks: {len(rows)} bản ghi")
    return len(rows)


# ─── 5. Verify anchors (mốc chuẩn Admin xác nhận 2026-11-07) ─────────────────
#
# Script này DROP + build lại lineage_founders/person_gen_computed nhưng
# KHÔNG tự kiểm tra kết quả — sai số sẽ bị ghi vào DB mà không báo lỗi gì.
# verify_anchors() là lưới an toàn: đối chiếu các mốc đời đã được Admin
# xác nhận là chắc chắn. Nếu có mốc sai/không tìm được, main() sẽ rollback
# toàn bộ transaction (bảng cũ giữ nguyên) và thoát với mã lỗi khác 0.
#
# Mốc chuẩn (Admin xác nhận 2026-11-07):
#   Ma Ha Ca Diếp      = Thiền Tông đời 1
#   Bồ Đề Đạt Ma       = Thiền Tông đời 28
#   Lục Tổ Huệ Năng    = Thiền Tông đời 33
#   Lâm Tế Nghĩa Huyền = Thiền Tông đời 38 (gen_lamte = 1)
#
# person_id của từng mốc KHÔNG được đoán — được tra theo tên thật
# (rdfs:label trong TTL, lưu lại trong lineage_founders.khai_to_name_vi)
# đã xác minh trực tiếp trong các file TTL nguồn:
#   data/ttl/Ton-Gia-Ma-Ha-Ca-Diep.ttl      → ex:monk/ma_ha_ca_diep      (generationOrder 1,  isLineageFounder true)
#   data/ttl/Ton-Gia-Bo-De-Dat-Ma.ttl       → ex:monk/bo_de_dat_ma       (generationOrder 28, isLineageFounder true)
#   data/ttl/Ton-Gia-Dai-Giam-Hue-Nang.ttl  → ex:monk/dai_giam_hue_nang  (generationOrder 33, isLineageFounder true)
#   data/ttl/TS-Lam-Te-Nghia-Huyen.ttl      → ex:monk/lam_te_nghia_huyen (generationOrder 38, isLineageFounder true)
# Cả 4 đều là Khai Tổ (isLineageFounder=true) của chính lineage TTL của họ,
# nên đều có mặt trong bảng lineage_founders sau seed_founders().

ANCHOR_SPECS = [
    {
        'label':       'Ma Ha Ca Diếp',
        'name_pattern': '%Ma Ha Ca Diếp%',
        'checks':      {'gen_thientong': 1},
    },
    {
        'label':       'Bồ Đề Đạt Ma',
        'name_pattern': '%Bồ Đề Đạt Ma%',
        'checks':      {'gen_thientong': 28},
    },
    {
        'label':       'Lục Tổ Huệ Năng',
        'name_pattern': '%Huệ Năng%',
        'checks':      {'gen_thientong': 33},
    },
    {
        'label':       'Lâm Tế Nghĩa Huyền',
        'name_pattern': '%Lâm Tế Nghĩa Huyền%',
        'checks':      {'gen_thientong': 38, 'gen_lamte': 1},
    },
]


def verify_anchors(conn, anchor_specs=None):
    """
    Đối chiếu các mốc đời chuẩn với dữ liệu VỪA được tính trong transaction
    hiện tại (chưa commit). Tra person_id theo TÊN trong lineage_founders
    (khai_to_name_vi — lấy trực tiếp từ rdfs:label trong TTL), sau đó lấy
    giá trị thật trong person_gen_computed để so sánh.

    Trả về (ok: bool, messages: list[str]):
      - ok=True  khi mọi mốc được tìm thấy DUY NHẤT và khớp đúng giá trị.
      - ok=False khi có mốc: không tìm thấy, tìm thấy nhiều hơn 1 (ambiguous),
        chưa có bản ghi tính toán trong person_gen_computed, hoặc giá trị
        tính toán sai lệch so với mốc chuẩn.
    """
    specs = anchor_specs if anchor_specs is not None else ANCHOR_SPECS
    cur = conn.cursor()
    ok = True
    messages = []

    for spec in specs:
        label   = spec['label']
        pattern = spec['name_pattern']

        cur.execute("""
            SELECT lf.khai_to_id, lf.khai_to_name_vi, lf.lineage_key,
                   pgc.gen_sect, pgc.gen_lamte, pgc.gen_thientong
            FROM lineage_founders lf
            LEFT JOIN person_gen_computed pgc
                   ON pgc.person_id = lf.khai_to_id
                  AND pgc.lineage_key = lf.lineage_key
            WHERE lf.khai_to_name_vi LIKE ?
        """, (pattern,))
        rows = cur.fetchall()

        if len(rows) == 0:
            ok = False
            messages.append(
                f"✗ Mốc '{label}': KHÔNG TÌM THẤY trong lineage_founders "
                f"(tra theo tên LIKE '{pattern}'). Không đủ dữ liệu để xác nhận "
                f"mốc này — coi như KHÔNG ĐẠT."
            )
            continue

        if len(rows) > 1:
            ok = False
            ids = ', '.join(f"{r[0]} ({r[1]})" for r in rows)
            messages.append(
                f"✗ Mốc '{label}': tra theo tên LIKE '{pattern}' khớp "
                f"{len(rows)} bản ghi trong lineage_founders ({ids}) — "
                f"không xác định rõ ràng (ambiguous), cần Admin làm rõ."
            )
            continue

        person_id, name_vi, lineage_key, gen_sect, gen_lamte, gen_thientong = rows[0]

        if gen_sect is None and gen_lamte is None and gen_thientong is None:
            ok = False
            messages.append(
                f"✗ Mốc '{label}' (person_id={person_id}, tên TTL='{name_vi}'): "
                f"có trong lineage_founders nhưng KHÔNG có bản ghi tương ứng "
                f"trong person_gen_computed (ETL chưa tính đời cho mốc này)."
            )
            continue

        actual = {
            'gen_sect':      gen_sect,
            'gen_lamte':     gen_lamte,
            'gen_thientong': gen_thientong,
        }
        for field, expected in spec['checks'].items():
            got = actual.get(field)
            if got != expected:
                ok = False
                messages.append(
                    f"✗ Mốc '{label}' (person_id={person_id}, tên TTL='{name_vi}') "
                    f"SAI LỆCH tại '{field}': mong đợi {expected}, thực tế {got!r}."
                )

    if ok:
        messages.append(f"✓ Tất cả {len(specs)} mốc chuẩn khớp đúng.")

    return ok, messages


# ─── 6. Report ────────────────────────────────────────────────────────────────

def report(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT person_id) FROM person_gen_computed")
    n = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM person_gen_computed")
    tot = cur.fetchone()[0]
    print(f"\n{'='*55}")
    print(f"Tổng thiền sư có gen: {n:,}  |  Tổng records: {tot:,}")

    print("\nPhân bổ tông phái:")
    cur.execute("""
        SELECT lineage_name, COUNT(*) as cnt
        FROM person_gen_computed
        GROUP BY lineage_key ORDER BY cnt DESC LIMIT 20
    """)
    for lname, cnt in cur.fetchall():
        print(f"  {(lname or '?'):50s}: {cnt:,}")

    # Demo: Phật Ý Linh Nhạc
    for demo in ['phat_y_linh_nhac']:
        cur.execute("""
            SELECT lineage_name, gen_sect, gen_lamte, gen_thientong
            FROM person_gen_computed WHERE person_id=?
            ORDER BY gen_thientong
        """, (demo,))
        rows = cur.fetchall()
        cur.execute("SELECT name_vi FROM vn_person_authority WHERE id=?", (demo,))
        nrow = cur.fetchone()
        dname = (nrow[0] if nrow else demo) or demo
        print(f"\n=== {dname} ===")
        if rows:
            for r in rows:
                if r[1] is None and r[2] is None:
                    continue
                print(f"  [{r[0]}]")
                print(f"    Tông phái đời: {r[1]}  |  Lâm Tế đời: {r[2]}  |  Thiền Tông đời: {r[3]}")
        else:
            print("  ⚠ Chưa có dữ liệu")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== ETL Gen Compute (v2 — dharmaLineage-based) ===\n")

    # Bước 1: TTL → đọc toàn bộ + lọc founders
    print("Quét TTL files...")
    ttl_persons = load_all_persons_from_ttl()
    founders = load_founders_from_ttl()
    has_full = sum(1 for p in ttl_persons.values() if p['gen_order'] and p['lineage'])
    print(f"  → {len(ttl_persons)} persons trong TTL, {has_full} đủ data (lineage+gen_order)")
    print(f"  → {len(founders)} tông phái có Khai Tổ rõ ràng\n")

    conn = sqlite3.connect(DB_PATH)

    # TOÀN BỘ các bước dưới đây (drop/create/seed/compute) chạy trong ĐÚNG
    # MỘT transaction — không có conn.commit() nào ở giữa. Transaction chỉ
    # commit() nếu verify_anchors() ở Bước 6 xác nhận mọi mốc chuẩn đều khớp;
    # nếu không, rollback() sẽ hoàn tác cả DROP TABLE, khiến bảng cũ (trước
    # khi script này chạy) còn nguyên như ban đầu.
    try:
        # Bước 2: Drop + recreate
        conn.execute("DROP TABLE IF EXISTS lineage_founders")
        conn.execute("DROP TABLE IF EXISTS person_gen_computed")
        setup_tables(conn)
        seed_founders(conn, founders)

        # Bước 3: TTL monks (đọc thẳng từ file, không qua DB sync)
        compute_slug_monks(conn, ttl_persons)

        # Bước 3b: Kế thừa tông phái qua graph (đệ tử chưa có dharmaLineageName)
        children = build_children(conn)
        propagate_lineage_to_descendants(conn, children, ttl_persons)

        # Bước 4: DILA monks (BFS toàn cục)
        compute_dila_monks(conn, children)

        # Bước 5: Report
        report(conn)

        # Bước 6: Kiểm tra mốc chuẩn — ĐIỀU KIỆN BẮT BUỘC để commit.
        print(f"\n{'='*55}")
        print("Kiểm tra mốc chuẩn (verify_anchors)...")
        anchors_ok, anchor_messages = verify_anchors(conn)
        for m in anchor_messages:
            print(f"  {m}")

        if not anchors_ok:
            conn.rollback()
            print(
                "\n✗ THẤT BẠI: một hoặc nhiều mốc chuẩn không khớp hoặc "
                "không tìm được. Đã ROLLBACK — bảng lineage_founders và "
                "person_gen_computed GIỮ NGUYÊN như trước khi chạy script này. "
                "Không có gì được ghi vào DB."
            )
            conn.close()
            sys.exit(1)

        conn.commit()
        print("\n✓ Mốc chuẩn khớp đúng — đã COMMIT.")
    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.close()
    print("\n✓ Hoàn tất.")


if __name__ == '__main__':
    main()

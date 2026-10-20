# -*- coding: utf-8 -*-
"""T123 — Seed Style Constitution "Ban Dịch PTDA" + 3 bảng additive.

Công việc:
  A. Upsert 8 rules Style Constitution vào `translation_rules` (is_active=1):
     PERSONA_BAN_DICH, EXPRESSION_PRINCIPLE, NO_ADDITION, GLOSSARY_LOCK_STABLE,
     CANONICAL_NAMES, TONE_OVERALL, LITERARY_PURITY, HONORIFIC_PRONOUN.
  B. Tạo bảng `translation_exemplar` (CREATE TABLE IF NOT EXISTS) + seed ~2,724 cặp Hán-Việt
     passage-level từ `lexicon` (ưu tiên các bộ từ điển danh tác), chỉ active 2-3 mẫu tốt nhất.
  C. Tạo bảng `translation_glossary` (CREATE TABLE IF NOT EXISTS) + seed ~80 thuật ngữ lock
     lấy từ `glossary_vi`/`lexicon` nguồn từ điển danh tác.
  D. Tạo bảng `translation_error_report` (CREATE TABLE IF NOT EXISTS) — báo lỗi dịch chi tiết.

Nguyên tắc: ZERO-ALTER, additive-only, resume-safe. Chạy nhiều lần an toàn (upsert/idempotent).

Usage:
  python scripts/seed_style_constitution.py            # apply
  python scripts/seed_style_constitution.py --dry-run  # chỉ in các hành động sẽ làm
  python scripts/seed_style_constitution.py --verify   # in thống kê hiện trạng
"""
import argparse
import hashlib
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

HAN_RE = re.compile(r'[\u4e00-\u9fff]')

# ── A. 8 rules Style Constitution ─────────────────────────────────────────────
STYLE_RULES = [
    {
        'rule_code': 'PERSONA_BAN_DICH',
        'rule_type': 'style',
        'priority': 0,
        'description': 'Persona cố định: thành viên Ban Dịch PTDA',
        'rule_text': (
            "Persona cố định: Bạn là thành viên Ban Dịch PTDA — chuyên dịch các bản kinh Hán văn "
            "(Đại Tạng Kinh) sang tiếng Việt. Văn phong của bạn kế thừa tinh thần các dịch giả và "
            "từ điển Phật học danh tiếng (Từ Điển Thiền Tông Hán-Việt, Phật Quang, Đoàn Trung Còn, "
            "Từ Điển Hán-Việt...). Mọi bản dịch phải trang trọng, tôn kính, học thuật, đúng nghĩa, "
            "giữ trọn diện mạo kinh văn Phật giáo cổ điển."
        ),
    },
    {
        'rule_code': 'EXPRESSION_PRINCIPLE',
        'rule_type': 'style',
        'priority': 0,
        'description': 'Nguyên tắc diễn đạt chung',
        'rule_text': (
            "Dịch theo nghĩa câu văn chứ không dịch từng chữ cứng nhắc; câu tiếng Việt phải trôi "
            "chảy, rõ ràng, mạch lạc như văn tường thuật sử Phật giáo. Giữ lại đầy đủ thông tin "
            "lai lịch nhân vật, địa danh, niên hiệu, sự kiện tu học/hoằng pháp. Không chẻ câu vụn, "
            "không bỏ sót chi tiết trong nguyên bản."
        ),
    },
    {
        'rule_code': 'NO_ADDITION',
        'rule_type': 'forbidden',
        'priority': 0,
        'description': 'Cấm thêm nội dung không có trong nguyên bản',
        'rule_text': (
            "KHÔNG thêm nhận định, chú thích, ngoặc vuông giải thích, lời bình, hay nội dung nào "
            "không có trong nguyên bản Hán văn. Bản dịch phải trung thành với văn bản gốc về nội "
            "dung lẫn số lượng câu chữ hợp lý (1-2 câu Hán → 1-2 câu Việt; 3-5 câu → 3-4 câu; "
            "5-10 câu → 5-7 câu)."
        ),
    },
    {
        'rule_code': 'GLOSSARY_LOCK_STABLE',
        'rule_type': 'terminology',
        'priority': 0,
        'description': 'Thuật ngữ cốt lõi giữ ổn định xuyên suốt',
        'rule_text': (
            "Các thuật ngữ Phật học cốt lõi phải giữ DẠNG HÁN-VIỆT ổn định, không đổi lộn xộn giữa "
            "các lần dịch: Bát Nhã, Kim Cang, Giới-Định-Huệ, Tánh-Tướng, Tông-Nhân-Dụ, Tỳ Ni, "
            "giới, pháp lạp, viên tịch, pháp trượng... Nếu có bảng GLOSSARY LOCK trong prompt thì "
            "phải ưu tiên Tuân theo đúng mapping ghi trong đó."
        ),
    },
    {
        'rule_code': 'CANONICAL_NAMES',
        'rule_type': 'terminology',
        'priority': 0,
        'description': 'Tên riêng dạng Hán-Việt chuẩn',
        'rule_text': (
            "Mọi tên người, tên chùa, tên địa danh, niên hiệu phải dùng dạng Hán-Việt chuẩn "
            "(Thích Diên Huy, chùa Thiếu Thất, núi Tung Sơn, Lạc Dương, Thái Nguyên, Kinh Triệu, "
            "Nam Yên, Hoạt Đài, Càn Hóa...). KHÔNG dùng Pinyin, phiên âm hiện đại, hay tên tiếng Anh."
        ),
    },
    {
        'rule_code': 'TONE_OVERALL',
        'rule_type': 'style',
        'priority': 0,
        'description': 'Tông điệu trang trọng, thanh tịnh, tôn kính',
        'rule_text': (
            "Tông điệu tổng thể: trang trọng, thanh tịnh, tôn kính như biên niên sử tông môn. Tránh "
            "giọng văn đời thường, suồng sã, hiện đại hóa quá đà. Những chi tiết như 'cầm bình bát "
            "nhẹ nhàng mà vững chãi', 'thực hành từ bi, nhẫn nhục không cầu danh lợi' cần giữ "
            "được chất sử liệu nghiêm trang."
        ),
    },
    {
        'rule_code': 'LITERARY_PURITY',
        'rule_type': 'style',
        'priority': 0,
        'description': 'Giữ trong sáng văn chương Phật giáo',
        'rule_text': (
            "Giữ sự trong sáng của văn chương Phật giáo: dùng từ Hán-Việt đã quen thuộc trong cộng "
            "đồng Phật tử, tránh từ thông tục hoặc từ ngữ hiện đại không hợp kinh điển. Khi gặp "
            "thuật ngữ chuyên môn (Thượng Thập Ác/Hạ Thập Ác, Tông-Nhân-Dụ, Hoạt Đài...) hãy giữ "
            "nguyên dạng Hán-Việt đã nêu, không thêm chú giải."
        ),
    },
    {
        'rule_code': 'HONORIFIC_PRONOUN',
        'rule_type': 'style',
        'priority': 9,
        'description': 'Đại từ tôn kính bắt buộc cho người xuất gia',
        'rule_text': (
            "Mọi nhân vật là tu sĩ Phật giáo (tăng, ni, thiền sư, tổ sư) phải xưng hô với đại từ "
            "tôn kính: 'ngài', 'Hòa Thượng', 'Thiền Sư', 'Tôn Sư', 'vị ấy'. NGHIÊM CẤM dùng "
            "'chàng', 'anh', 'cậu', 'ông', 'gã', 'hắn', 'nó' cho người xuất gia — đó là cách gọi "
            "đời thường, kém tôn kính. Nêu họ tên đầy đủ (Thích Diên Huy) ở lần đầu, về sau dùng "
            "'ngài' hoặc 'Thiền Sư Diên Huy'."
        ),
    },
]

# ── C. Thuật ngữ glossary lock (~80) — nguồn từ điển danh tác ────────────────
GLOSSARY_LOCK = [
    ('法', 'pháp'), ('僧', 'tăng'), ('大乘', 'Đại Thừa'), ('小乘', 'Tiểu Thừa'),
    ('般若', 'Bát Nhã'), ('金剛', 'Kim Cang'), ('涅槃', 'Niết Bàn'), ('菩提', 'Bồ Đề'),
    ('戒', 'giới'), ('定', 'định'), ('慧', 'huệ'), ('因', 'nhân'), ('果', 'quả'),
    ('緣', 'duyên'), ('性', 'tánh'), ('相', 'tướng'), ('法身', 'pháp thân'),
    ('報身', 'báo thân'), ('化身', 'hóa thân'), ('三寶', 'Tam Bảo'), ('三藏', 'Tam Tạng'),
    ('經', 'kinh'), ('律', 'luật'), ('論', 'luận'), ('菩薩', 'Bồ Tát'),
    ('比丘', 'Tỳ Kheo'), ('比丘尼', 'Tỳ Kheo Ni'), ('禪師', 'Thiền Sư'),
    ('和尚', 'Hòa Thượng'), ('法師', 'Pháp Sư'), ('大師', 'Đại Sư'),
    ('住持', 'trụ trì'), ('方丈', 'phương trượng'), ('沙彌', 'Sa Di'),
    ('十惡', 'Thập Ác'), ('上根', 'Thượng Căn'), ('下根', 'Hạ Căn'),
    ('圓寂', 'viên tịch'), ('坐化', 'tọa hóa'), ('舍利', 'xá lợi'),
    ('戒臘', 'giới lạp'), ('法臘', 'pháp lạp'), ('僧臘', 'tăng lạp'),
    ('剃度', 'thế độ'), ('受戒', 'thọ giới'), ('受具', 'thọ cụ túc giới'),
    ('衣鉢', 'y bát'), ('三衣', 'ba y'), ('鉢', 'bình bát'),
    ('上堂', 'thượng đường'), ('開示', 'khai thị'), ('說法', 'thuyết pháp'),
    ('法界', 'pháp giới'), ('法門', 'pháp môn'), ('道場', 'đạo tràng'),
    ('精舍', 'tinh xá'), ('蘭若', 'lan nhã'), ('叢林', 'tòng lâm'),
    ('祖師', 'tổ sư'), ('西天', 'Tây Thiên'), ('東土', 'Đông Thổ'),
    ('少林寺', 'chùa Thiếu Lâm'), ('嵩山', 'núi Tung Sơn'), ('洛陽', 'Lạc Dương'),
    ('太原', 'Thái Nguyên'), ('京兆', 'Kinh Triệu'), ('南燕', 'Nam Yên'),
    ('活台', 'Hoạt Đài'), ('乾化', 'Càn Hóa'), ('內典', 'nội điển'),
    ('外典', 'ngoại điển'), ('梵音', 'tiếng Phạn'), ('經論', 'kinh luận'),
    ('弘法', 'hoằng pháp'), ('度人', 'hóa độ'), ('說法', 'thuyết pháp'),
    ('法門', 'pháp môn'), ('宗旨', 'tông chỉ'), ('妙義', 'diệu nghĩa'),
]


# ── B. Nguồn exemplar: các bộ từ điển danh tác ưu tiên ───────────────────────
EXEMPLAR_SOURCES_PRIORITY = [
    'Tu Dien Thien Tong Han Viet - Han Man - Thong Thien',
    'Tu Dien Han Viet - Nguyen Quoc Hung',
    'Tam Tang Phap So - Cs Le Hong Son',
    'Phat Hoc Tinh Tuyen - TK Thich Nguyen Tam',
    'Tu Dien Phat Hoc Tong Hop - Doan Trung Con - Tu Thong - Nguyen Lien - Duc Tri',
    'Tu Dien Phat Hoc Tong Hop - Viet  - Anh - Cs Minh Thong',
]
EXEMPLAR_ACTIVE_LIMIT = 3  # chỉ active 2-3 mẫu tốt nhất


def ensure_schema(conn):
    """Tạo 3 bảng additive (0 ALTER)."""
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS translation_exemplar (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      zh TEXT NOT NULL,
      vi TEXT NOT NULL,
      source_lexicon TEXT DEFAULT '',
      source_label TEXT DEFAULT 'tu_dien_danh_tac',
      length_zh INTEGER DEFAULT 0,
      is_active INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_exemplar_active ON translation_exemplar(is_active, length_zh);

    CREATE TABLE IF NOT EXISTS translation_glossary (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      term_zh TEXT NOT NULL,
      term_vi TEXT NOT NULL,
      source_label TEXT DEFAULT 'tu_dien_danh_tac',
      is_locked INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now')),
      UNIQUE (term_zh, term_vi)
    );

    CREATE TABLE IF NOT EXISTS translation_error_report (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cache_id INTEGER DEFAULT NULL,
      source_type TEXT DEFAULT '',
      entity_id TEXT DEFAULT '',
      translated_text_snapshot TEXT DEFAULT '',
      error_type TEXT DEFAULT 'style',
      note TEXT DEFAULT '',
      page_url TEXT DEFAULT '',
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_error_report_status ON translation_error_report(status, created_at);
    """)


def seed_rules(conn, dry_run):
    now = '2026-09-12 12:00:00'
    existing = {r[0] for r in conn.execute("SELECT rule_code FROM translation_rules").fetchall()}
    n_add, n_upd = 0, 0
    for rule in STYLE_RULES:
        if dry_run:
            action = 'UPDATE' if rule['rule_code'] in existing else 'INSERT'
            print(f"  [DRY] {action} rule {rule['rule_code']}")
            continue
        conn.execute("""
            INSERT INTO translation_rules
              (rule_code, rule_type, description, rule_text, is_active, priority,
               created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(rule_code) DO UPDATE SET
              rule_type=excluded.rule_type, description=excluded.description,
              rule_text=excluded.rule_text, is_active=excluded.is_active,
              priority=excluded.priority, updated_at=excluded.updated_at
        """, (rule['rule_code'], rule['rule_type'], rule['description'], rule['rule_text'],
              1, rule['priority'], 'admin', now, now))
        if rule['rule_code'] in existing:
            n_upd += 1
        else:
            n_add += 1
    conn.commit()
    return n_add, n_upd


def collect_exemplar_candidates(conn, limit_all=4000):
    """Lấy cặp Hán-Việt passage-level từ lexicon, ưu tiên nguồn danh tác."""
    cands = []
    for source in EXEMPLAR_SOURCES_PRIORITY:
        rows = conn.execute(
            "SELECT term, definition FROM lexicon WHERE source = ? "
            "   AND term IS NOT NULL AND definition IS NOT NULL "
            "   AND LENGTH(term) >= 20 AND LENGTH(definition) >= 30",
            (source,)
        ).fetchall()
        for term, definition in rows:
            t, d = (term or '').strip(), (definition or '').strip()
            if not (t and d):
                continue
            # term chứa Hán, không kèm số/ID kỹ thuật; definition không chứa Hán (thuần Việt)
            if not HAN_RE.search(t):
                continue
            if HAN_RE.search(d):
                continue
            if len(t) + len(d) > 1500:
                continue
            cands.append({'zh': t, 'vi': d, 'source': source,
                          'length_zh': len(t), 'score': len(t) + len(d)})
        if len(cands) >= limit_all:
            break
    return cands


def seed_exemplars(conn, dry_run):
    cands = collect_exemplar_candidates(conn)
    if dry_run:
        print(f"  [DRY] sẽ seed {len(cands)} exemplar + active {min(EXEMPLAR_ACTIVE_LIMIT, len(cands))} mẫu tốt nhất")
        return len(cands)
    # Chọn mẫu active tốt nhất: ưu tiên độ dài vừa phải (150-500), câu đầy đủ
    scored = sorted(cands, key=lambda c: c['score'])
    best = []
    for c in scored:
        if 150 <= c['score'] <= 550:
            best.append(c)
        if len(best) >= EXEMPLAR_ACTIVE_LIMIT:
            break
    conn.execute("DELETE FROM translation_exemplar")
    for c in cands:
        is_active = 1 if c in best else 0
        conn.execute(
            "INSERT INTO translation_exemplar (zh, vi, source_lexicon, source_label, length_zh, is_active) "
            "VALUES (?,?,?,?,?,?)",
            (c['zh'], c['vi'], c['source'], 'tu_dien_danh_tac', c['length_zh'], is_active)
        )
    conn.commit()
    return len(cands)


def seed_glossary(conn, dry_run):
    if dry_run:
        print(f"  [DRY] sẽ seed {len(GLOSSARY_LOCK)} thuật ngữ glossary lock")
        return len(GLOSSARY_LOCK)
    for zh, vi in GLOSSARY_LOCK:
        conn.execute("""
            INSERT OR IGNORE INTO translation_glossary (term_zh, term_vi, source_label, is_locked)
            VALUES (?,?,?,1)
        """, (zh, vi, 'tu_dien_danh_tac'))
    conn.commit()
    return len(GLOSSARY_LOCK)


def compute_rules_version(conn):
    rows = conn.execute(
        "SELECT rule_text FROM translation_rules WHERE is_active=1 ORDER BY priority ASC"
    ).fetchall()
    combined = '\n---\n'.join(r[0] or '' for r in rows)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


def verify(conn):
    print("== verify hiện trạng: ")
    n_rules = conn.execute("SELECT COUNT(*) FROM translation_rules WHERE is_active=1").fetchone()[0]
    print(f"  rules active: {n_rules}")
    rv = compute_rules_version(conn)
    print(f"  rules_version (mới): {rv}")
    for t in ('translation_exemplar', 'translation_glossary', 'translation_error_report'):
        try:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            n_act = conn.execute(f"SELECT COUNT(*) FROM {t} WHERE is_active=1").fetchone()[0] \
                if 'is_active' in [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()] else -1
            print(f"  {t}: {n} rows" + (f", active={n_act}" if n_act >= 0 else ""))
        except Exception as e:
            print(f"  {t}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if args.verify:
            verify(conn)
            return
        ensure_schema(conn)
        print("== Seed Style Constitution")
        n_add, n_upd = seed_rules(conn, args.dry_run)
        print(f"  rules: {n_add} mới, {n_upd} cập nhật")
        n_ex = seed_exemplars(conn, args.dry_run)
        print(f"  exemplar: {n_ex} cặp Hán-Việt từ từ điển danh tác")
        n_gl = seed_glossary(conn, args.dry_run)
        print(f"  glossary lock: {n_gl} thuật ngữ")
        if args.dry_run:
            print("== DRY-RUN xong (chưa ghi DB)")
        else:
            print(f"== DONE. rules_version mới = {compute_rules_version(conn)}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
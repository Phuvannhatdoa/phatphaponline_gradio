"""
Re-transliterate toàn bộ DILA places từ name_zh → name_vi mới,
dùng từ điển hợp nhất: custom_hanviet_override (chuyên gia xác minh) + hanviet_fallback.
Override LUÔN thắng fallback — đây là bộ đọc Hán-Việt chuẩn nhất hiện có.

Chỉ UPDATE rows có kết quả khác với name_vi hiện tại. Idempotent.
Làm mới bảng missing_hanzi sau khi xong.

Usage:
    python scripts/retranslate_dila_places.py [--dry-run]
"""
import sqlite3, re, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--dry-run' in sys.argv

HAN_RE = re.compile(r'[一-鿿㐀-䶿豈-﫿]')

# Override chỉ áp dụng cho địa danh — KHÔNG ảnh hưởng người/chức vị.
# 長: địa danh dùng "Trường" (Trường An, Trường Sa, Trường Giang)
#     người/chức vị dùng "Trưởng" (Trưởng Lão) — xử lý riêng ở people pipeline.
PLACE_CONTEXT_OVERRIDES = {
    '長': 'Trường',
}

PLACE_SUFFIXES = [
    ("國", "Quốc"), ("省", "Tỉnh"), ("市", "Thị"), ("縣", "Huyện"),
    ("郡", "Quận"), ("州", "Châu"), ("府", "Phủ"), ("城", "Thành"),
    ("鎮", "Trấn"), ("鄉", "Hương"), ("村", "Thôn"), ("邑", "Ấp"),
    ("山", "Sơn"), ("嶺", "Lĩnh"), ("峰", "Phong"), ("岳", "Nhạc"),
    ("江", "Giang"), ("河", "Hà"), ("湖", "Hồ"), ("海", "Hải"),
    ("溪", "Khê"), ("川", "Xuyên"), ("橋", "Kiều"), ("關", "Quan"),
    ("寺", "Tự"), ("院", "Viện"), ("堂", "Đường"), ("庵", "Am"),
    ("塔", "Tháp"), ("宮", "Cung"), ("殿", "Điện"), ("閣", "Các"),
    ("門", "Môn"), ("洞", "Động"), ("窟", "Quật"), ("園", "Viên"),
    ("林", "Lâm"), ("堡", "Bảo"), ("營", "Doanh"), ("屯", "Truân"),
    ("道", "Đạo"), ("路", "Lộ"), ("坊", "Phường"), ("里", "Lý"),
    ("峽", "Hiệp"), ("灣", "Loan"), ("島", "Đảo"), ("半島", "Bán Đảo"),
    ("漠", "Mạc"), ("原", "Nguyên"), ("平", "Bình"), ("谷", "Cốc"),
    ("洲", "Châu"), ("縣城", "Huyện Thành"), ("古城", "Cổ Thành"),
]
PLACE_SUFFIXES.sort(key=lambda x: -len(x[0]))
SUFFIX_MAP = {}
for ch, hv in PLACE_SUFFIXES:
    SUFFIX_MAP.setdefault(ch[0], []).append((ch, hv))


def load_dicts(cur):
    # custom_hanviet_override (chuyên gia) — ưu tiên cao nhất
    override = {}
    for ch, hv in cur.execute("SELECT char, hanviet FROM custom_hanviet_override"):
        override[ch] = hv

    # hanviet_fallback — fallback nếu không có override
    fallback = {}
    for ch, hv in cur.execute("SELECT ch, hv FROM hanviet_fallback"):
        fallback[ch] = hv

    # Merge: override thắng fallback
    merged = {**fallback, **override}
    print(f"  Dictionary: {len(fallback)} fallback + {len(override)} override = {len(merged)} unique chars")
    return merged


def transliterate(name_zh, merged_dict):
    """Chuyển name_zh → (name_vi, missing_chars).
    Trả về missing_chars = set ký tự Hán chưa map được."""
    if not name_zh or not name_zh.strip():
        return "", set()

    parts = []
    missing = set()
    i = 0
    while i < len(name_zh):
        ch = name_zh[i]
        # Thử suffix dài nhất trước
        suffix_list = SUFFIX_MAP.get(ch)
        matched = False
        if suffix_list:
            remaining = name_zh[i:]
            for suffix_ch, suffix_hv in suffix_list:
                if remaining.startswith(suffix_ch):
                    parts.append(suffix_hv)
                    i += len(suffix_ch)
                    matched = True
                    break
        if matched:
            continue

        # Ký tự đơn
        if HAN_RE.match(ch):
            hv = PLACE_CONTEXT_OVERRIDES.get(ch) or merged_dict.get(ch)
            if hv:
                parts.append(hv)
            else:
                parts.append(ch)  # giữ nguyên ký tự, log missing
                missing.add(ch)
        else:
            parts.append(ch)
        i += 1

    if not parts:
        return "", missing

    joined = " ".join(parts)
    # Title case mỗi từ (chỉ những từ không phải ký tự Hán thô)
    words = joined.split(" ")
    titled = []
    for w in words:
        if w and not HAN_RE.match(w[0]):
            titled.append(w[0].upper() + w[1:] if len(w) > 1 else w.upper())
        else:
            titled.append(w)
    return " ".join(titled), missing


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()

    print("Loading dictionaries...")
    merged = load_dicts(cur)

    # Lấy toàn bộ DILA places + name_vi hiện tại
    print("Loading DILA places...")
    rows = cur.execute("""
        SELECT p.id, p.name_zh, n.name_vi, n.id as nvm_id, n.source
        FROM places_dila p
        LEFT JOIN namevi_map_places n ON n.dila_id = p.id
        WHERE p.name_zh IS NOT NULL AND p.name_zh != ''
        ORDER BY p.id
    """).fetchall()
    print(f"  {len(rows):,} DILA places với name_zh")

    total_dila = cur.execute("SELECT COUNT(*) FROM places_dila").fetchone()[0]
    no_name_zh = cur.execute("SELECT COUNT(*) FROM places_dila WHERE name_zh IS NULL OR name_zh = ''").fetchone()[0]
    print(f"  ({no_name_zh} places không có name_zh — bỏ qua)")

    updated = 0
    inserted = 0
    unchanged = 0
    skipped_manual = 0
    all_missing = {}  # char → count

    batch_update = []
    batch_insert = []

    for pid, name_zh, old_vi, nvm_id, source in rows:
        # Không override manual/reviewed entries
        if source in ('manual', 'reviewed') and old_vi:
            skipped_manual += 1
            continue

        new_vi, missing = transliterate(name_zh, merged)
        for ch in missing:
            all_missing[ch] = all_missing.get(ch, 0) + 1

        if not new_vi:
            continue

        if nvm_id is not None:
            if new_vi != old_vi:
                conf = 0.85 if not missing else 0.75
                batch_update.append((new_vi, conf, pid))
                updated += 1
            else:
                unchanged += 1
        else:
            conf = 0.85 if not missing else 0.75
            batch_insert.append((pid, new_vi, name_zh, conf))
            inserted += 1

    if not DRY_RUN:
        if batch_update:
            cur.executemany("""
                UPDATE namevi_map_places
                SET name_vi = ?, confidence = ?, source = 'auto_transliterate_v2'
                WHERE dila_id = ?
            """, batch_update)
        if batch_insert:
            cur.executemany("""
                INSERT OR IGNORE INTO namevi_map_places
                    (dila_id, name_vi, name_zh, source, confidence, needs_review)
                VALUES (?, ?, ?, 'auto_transliterate_v2', ?, 0)
            """, batch_insert)

        # Làm mới missing_hanzi
        cur.execute("DELETE FROM missing_hanzi")
        if all_missing:
            cur.executemany(
                "INSERT INTO missing_hanzi (char, count, last_seen_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                [(ch, cnt) for ch, cnt in sorted(all_missing.items(), key=lambda x: -x[1])]
            )
        conn.commit()
        print("\nCommitted.")
    else:
        print("\n[DRY RUN — không ghi vào DB]")

    print(f"\n=== KẾT QUẢ ===")
    print(f"Tổng DILA places:          {total_dila:,}")
    print(f"Có name_zh để dịch:        {len(rows):,}")
    print(f"  Updated (khác old_vi):   {updated:,}")
    print(f"  Unchanged:               {unchanged:,}")
    print(f"  Inserted (mới):          {inserted:,}")
    print(f"  Giữ nguyên (manual):     {skipped_manual:,}")
    print(f"\nKý tự vẫn thiếu:          {len(all_missing):,} unique chars")
    if all_missing:
        top = sorted(all_missing.items(), key=lambda x: -x[1])[:15]
        print(f"Top 15 missing:")
        for ch, cnt in top:
            print(f"  '{ch}': {cnt} lần")
    else:
        print("  (không còn ký tự nào thiếu!)")

    conn.close()


if __name__ == "__main__":
    main()

"""
T49 — Place VI_NAME Character Map Fix

Vấn đề phát hiện 2026-08-27:
- hanviet_fallback có 3 char mapping SAI cho địa danh:
    永 → 'vắng'  (đúng: 'Vĩnh') — ảnh hưởng 636 places
    澄 → 'chừng' (đúng: 'Trừng') — ảnh hưởng 37 places
    觀 → 'quan'  (đúng: 'Quán') — ảnh hưởng 418 places
- 935 entries trong zqlocal_content có ký tự CJK chưa dịch

Scope:
1. Thêm 3 chars vào custom_hanviet_override
2. Re-transliterate places bị ảnh hưởng (reuse retranslate_dila_places logic)
3. Sync kết quả vào cả namevi_map_places + zqlocal_content
4. Flag entries có ký tự chưa dịch (generated_by='has_untranslated_chars')
5. Upgrade tất cả clean entries: conf 0.5 → 0.65

Usage:
    python scripts/t49_charmap_fix.py              # dry-run
    python scripts/t49_charmap_fix.py --apply      # apply changes

Revert:
    cp docs/sessions/2026-08-27/lineage_pre_T49.db.bak data/lineage.db
"""
import sqlite3
import re
import sys
import os
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--apply' not in sys.argv

HAN_RE = re.compile(r'[一-鿿㐀-䶿豈-﫿　-〿]')

# ─── Chars cần fix trong custom_hanviet_override ───────────────────────────
NEW_OVERRIDES = [
    ('永', 'Vĩnh',  'T49-charmap-fix-2026-08-27'),  # fallback sai: 'vắng'
    ('澄', 'Trừng', 'T49-charmap-fix-2026-08-27'),  # fallback sai: 'chừng'
    ('觀', 'Quán',  'T49-charmap-fix-2026-08-27'),  # fallback thiếu dấu thanh: 'quan'
]

# Reuse PLACE_SUFFIXES từ retranslate_dila_places.py
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
    ("峽", "Hiệp"), ("灣", "Loan"), ("島", "Đảo"),
    ("漠", "Mạc"), ("原", "Nguyên"), ("平", "Bình"), ("谷", "Cốc"),
    ("洲", "Châu"), ("縣城", "Huyện Thành"), ("古城", "Cổ Thành"),
]
PLACE_SUFFIXES.sort(key=lambda x: -len(x[0]))
SUFFIX_MAP = {}
for ch, hv in PLACE_SUFFIXES:
    SUFFIX_MAP.setdefault(ch[0], []).append((ch, hv))

PLACE_CONTEXT_OVERRIDES = {'長': 'Trường'}


def load_merged_dict(cur):
    override = {}
    for ch, hv in cur.execute("SELECT char, hanviet FROM custom_hanviet_override"):
        override[ch] = hv
    fallback = {}
    for ch, hv in cur.execute("SELECT ch, hv FROM hanviet_fallback"):
        fallback[ch] = hv
    return {**fallback, **override}


def transliterate(name_zh, merged):
    if not name_zh or not name_zh.strip():
        return "", set()
    parts = []
    missing = set()
    i = 0
    while i < len(name_zh):
        ch = name_zh[i]
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
        if HAN_RE.match(ch):
            hv = PLACE_CONTEXT_OVERRIDES.get(ch) or merged.get(ch)
            if hv:
                parts.append(hv)
            else:
                parts.append(ch)
                missing.add(ch)
        else:
            parts.append(ch)
        i += 1

    joined = " ".join(parts)
    words = joined.split(" ")
    titled = []
    for w in words:
        if w and not HAN_RE.match(w[0]):
            titled.append(w[0].upper() + w[1:] if len(w) > 1 else w.upper())
        else:
            titled.append(w)
    return " ".join(titled), missing


def has_untranslated(content):
    """Check if a VI_NAME string contains raw CJK or unknown unicode."""
    if not content:
        return False
    return bool(re.search(r'[一-鿿㐀-䶿豈-﫿-぀-ヿ]', content))


def main():
    mode = "DRY-RUN" if DRY_RUN else "APPLY"
    print(f"=== T49 Place VI_NAME Character Map Fix [{mode}] ===")
    print(f"DB: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # ── Step 1: Add new overrides ─────────────────────────────────────────
    print("Step 1: Custom hanviet overrides")
    for ch, hv, added_by in NEW_OVERRIDES:
        cur.execute("SELECT hanviet FROM custom_hanviet_override WHERE char=?", (ch,))
        existing = cur.fetchone()
        fb_cur = conn.execute("SELECT hv FROM hanviet_fallback WHERE ch=?", (ch,))
        fb = fb_cur.fetchone()
        fb_val = fb[0] if fb else 'NONE'
        exist_note = ('(EXISTS: ' + existing[0] + ')') if existing else '(NEW)'
        print(f"  {ch}: fallback={fb_val!r} -> override={hv!r}  {exist_note}")
        if not DRY_RUN and not existing:
            cur.execute("""
                INSERT OR IGNORE INTO custom_hanviet_override (char, hanviet, added_by, created_at)
                VALUES (?, ?, ?, ?)
            """, (ch, hv, added_by, datetime.now().isoformat()))
    print()

    # ── Step 2: Load updated merged dict ─────────────────────────────────
    if not DRY_RUN:
        conn.commit()  # commit overrides first so they're visible in load

    # Temporarily inject new overrides into merged dict even in dry-run
    merged = load_merged_dict(cur)
    for ch, hv, _ in NEW_OVERRIDES:
        merged[ch] = hv  # preview effect even in dry-run
    print(f"Step 2: Merged dict loaded: {len(merged)} chars")

    # ── Step 3: Find affected places and re-transliterate ────────────────
    print("Step 3: Re-transliterate affected places")
    affected_chars = {ch for ch, _, _ in NEW_OVERRIDES}

    rows = cur.execute("""
        SELECT p.id, p.name_zh, n.name_vi, n.id as nvm_id
        FROM places_dila p
        LEFT JOIN namevi_map_places n ON n.dila_id = p.id
        WHERE p.name_zh IS NOT NULL AND p.name_zh != ''
    """).fetchall()

    nvm_updates = []
    zq_updates_retrans = []
    for pid, name_zh, old_vi, nvm_id in rows:
        if not any(ch in name_zh for ch in affected_chars):
            continue
        new_vi, missing = transliterate(name_zh, merged)
        if not new_vi or new_vi == old_vi:
            continue
        conf = '0.75' if not missing else '0.65'
        nvm_updates.append((new_vi, conf, 'auto_transliterate_t49', pid))
        zq_updates_retrans.append((new_vi, conf, pid))

    print(f"  namevi_map_places to update: {len(nvm_updates)}")
    if nvm_updates[:5]:
        print("  Sample changes:")
        for new_vi, conf, src, pid in nvm_updates[:5]:
            old = next((r[2] for r in rows if r[0] == pid), '?')
            print(f"    {pid}: {old!r} → {new_vi!r} (conf={conf})")
    print()

    if not DRY_RUN and nvm_updates:
        cur.executemany("""
            UPDATE namevi_map_places
            SET name_vi = ?, confidence = ?, source = ?
            WHERE dila_id = ?
        """, nvm_updates)
        cur.executemany("""
            UPDATE zqlocal_content
            SET content = ?, confidence = ?, generated_by = 'retrans_t49'
            WHERE entity_id = ? AND content_type = 'VI_NAME'
        """, [(v, c, pid) for v, c, pid in zq_updates_retrans])

    # ── Step 4: Flag entries with untranslated CJK ───────────────────────
    print("Step 4: Flag entries with untranslated chars")
    cur.execute("SELECT id, content FROM zqlocal_content WHERE content_type='VI_NAME' AND confidence='0.5'")
    all_vi = cur.fetchall()

    flag_updates = []
    for row_id, content in all_vi:
        if has_untranslated(content):
            flag_updates.append(('has_untranslated_chars', row_id))

    print(f"  Entries with untranslated chars: {len(flag_updates)}")
    if flag_updates[:5]:
        samples = [r[0] for r in cur.execute(
            "SELECT content FROM zqlocal_content WHERE id IN ({})".format(
                ','.join(str(r[1]) for r in flag_updates[:5])
            )
        ).fetchall()]
        for s in samples:
            print(f"    {s!r}")
    print()

    if not DRY_RUN and flag_updates:
        cur.executemany("""
            UPDATE zqlocal_content
            SET generated_by = ?
            WHERE id = ? AND content_type = 'VI_NAME'
        """, flag_updates)

    # ── Step 5: Upgrade remaining clean entries conf 0.5 → 0.65 ──────────
    print("Step 5: Upgrade clean entries conf 0.5 → 0.65")
    # Clean = conf still 0.5 AND no untranslated chars AND not already updated by step 3
    flagged_ids = {r[1] for r in flag_updates}
    retrans_pids = {pid for _, _, pid in zq_updates_retrans}

    upgrade_ids = []
    for row_id, content in all_vi:
        if row_id in flagged_ids:
            continue
        # Check if already updated by step 3 (by entity_id match)
        cur.execute("SELECT entity_id FROM zqlocal_content WHERE id=?", (row_id,))
        eid_row = cur.fetchone()
        if eid_row and eid_row[0] in retrans_pids:
            continue
        upgrade_ids.append((row_id,))

    print(f"  Clean entries to upgrade 0.5→0.65: {len(upgrade_ids)}")

    if not DRY_RUN and upgrade_ids:
        cur.executemany("""
            UPDATE zqlocal_content
            SET confidence = '0.65', generated_by = 'pipeline_reviewed_t49'
            WHERE id = ? AND confidence = '0.5' AND content_type = 'VI_NAME'
        """, upgrade_ids)

    # ── Commit + Summary ──────────────────────────────────────────────────
    if not DRY_RUN:
        conn.commit()

        # Verify
        conf_dist = cur.execute("""
            SELECT confidence, COUNT(*) FROM zqlocal_content
            WHERE content_type='VI_NAME'
            GROUP BY confidence ORDER BY CAST(confidence AS REAL) DESC
        """).fetchall()
        print("\n=== zqlocal_content after T49 ===")
        for conf, cnt in conf_dist:
            print(f"  conf={conf}: {cnt:,}")

        nvm_avg = cur.execute("SELECT AVG(CAST(confidence AS REAL)) FROM namevi_map_places").fetchone()[0]
        print(f"\nnamevi_map_places avg confidence: {nvm_avg:.3f}")

        print(f"\n[DONE] Revert: cp docs/sessions/2026-08-27/lineage_pre_T49.db.bak data/lineage.db")
    else:
        print("\n[DRY-RUN COMPLETE — chạy với --apply để thực thi]")
        print(f"\nSummary of changes if applied:")
        print(f"  custom_hanviet_override: +{sum(1 for _, _, _ in NEW_OVERRIDES)} entries")
        print(f"  namevi_map_places updates: {len(nvm_updates)}")
        print(f"  zqlocal_content retrans: {len(zq_updates_retrans)}")
        print(f"  zqlocal_content flagged: {len(flag_updates)}")
        print(f"  zqlocal_content conf 0.5→0.65: {len(upgrade_ids)}")

    conn.close()


if __name__ == "__main__":
    main()

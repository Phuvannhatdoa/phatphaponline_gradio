# -*- coding: utf-8 -*-
"""
T167 Phase 1 — Seed Translation Constitution (Ruleset) vào DB.

Seeding:
  1. translation_rulesets: 1 canonical ruleset 't167-constitution-v1'
  2. translation_ruleset_rules: map 15 canonical rules (RULE-001..015) + 8 T123 style rules
     vào ruleset này (active, priority)
  3. Upsert 15 RULE-001..015 vào translation_rules (nếu chưa có)
  4. Cập nhật translation_rules.ruleset_id/ruleset_version/is_canonical cho các rule này

Usage:
    python scripts/seed_t167_constitution.py            # apply
    python scripts/seed_t167_constitution.py --dry-run  # chỉ in
    python scripts/seed_t167_constitution.py --verify   # kiểm tra
"""
import argparse
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

# T167 Canonical Ruleset
RULESET_ID = 't167-constitution-v1'
RULESET_VERSION = '1.0.0'
RULESET_DESCRIPTION = 'Rules-Constrained Buddhist Translation Constitution (RULE-001..015 + T123 Style Constitution)'

# 15 Canonical Rules (RULE-001..015)
T167_RULES = [
    {
        'rule_code': 'RULE-001',
        'rule_type': 'forbidden',
        'priority': 10,
        'description': 'No Addition - Không thêm nội dung không có trong nguyên bản',
        'rule_text': 'KHÔNG thêm nhận định, chú thích, nội dung nào không có trong nguyên bản Hán văn. Bản dịch phải trung thành về nội dung và số lượng câu chữ hợp lý.',
    },
    {
        'rule_code': 'RULE-002',
        'rule_type': 'forbidden',
        'priority': 10,
        'description': 'No Omission - Không bỏ sót thông tin',
        'rule_text': 'KHÔNG bỏ sót bất kỳ chi tiết nào: lai lịch nhân vật, địa danh, niên hiệu, sự kiện tu học/hoằng pháp, thuật ngữ Phật học. Mọi câu Hán phải có bản dịch Việt tương ứng.',
    },
    {
        'rule_code': 'RULE-003',
        'rule_type': 'terminology',
        'priority': 10,
        'description': 'Terminology Consistency - Thuật ngữ nhất quán xuyên suốt',
        'rule_text': 'Các thuật ngữ Phật học cốt lõi phải giữ DẠNG HÁN-VIỆT ổn định xuyên suốt toàn bộ bản dịch. Nếu có GLOSSARY LOCK trong prompt thì bắt buộc tuân theo mapping đó.',
    },
    {
        'rule_code': 'RULE-004',
        'rule_type': 'terminology',
        'priority': 10,
        'description': 'Canonical Person Name - Tên người chuẩn Hán-Việt',
        'rule_text': 'Mọi tên người (tăng, ni, thiền sư, tổ sư, cư sĩ) phải dùng dạng Hán-Việt chuẩn. KHÔNG dùng Pinyin, phiên âm hiện đại, tên tiếng Anh. Lần đầu ghi full name, sau dùng "ngài"/"Thiền Sư [Tên]".',
    },
    {
        'rule_code': 'RULE-005',
        'rule_type': 'terminology',
        'priority': 10,
        'description': 'Canonical Place Name - Tên nơi chuẩn Hán-Việt',
        'rule_text': 'Mọi địa danh (chùa, núi, thành, vùng, quốc) phải dùng Hán-Việt chuẩn theo lịch sử Phật giáo Việt Nam/Trung Quốc. KHÔNG dùng tên tiếng Việt hiện đại nếu có tên Hán-Việt truyền thống.',
    },
    {
        'rule_code': 'RULE-006',
        'rule_type': 'terminology',
        'priority': 10,
        'description': 'Buddhist Terminology Preservation - Giữ thuật ngữ Phật học',
        'rule_text': 'Các thuật ngữ: Bát Nhã, Kim Cang, Giới-Định-Huệ, Tánh-Tướng, Tông-Nhân-Dụ, Tỳ Ni, pháp lạp, viên tịch, pháp trượng, Tam Bảo, Bồ Tát, Niết Bàn, Bồ Đề... phải giữ nguyên dạng Hán-Việt, KHÔNG dịch sang từ thông tục.',
    },
    {
        'rule_code': 'RULE-007',
        'rule_type': 'structure',
        'priority': 10,
        'description': 'Subject/Object Preservation - Giữ chủ thể/khách thể',
        'rule_text': 'Giữ đúng quan hệ chủ ngữ - vị ngữ - tân ngữ của câu Hán. Không đảo chủ - tân, không bị động hóa khi nguyên bản chủ động. Nhân xưng (ngài, vị ấy, bần đẳng) phải đúng đối tượng.',
    },
    {
        'rule_code': 'RULE-008',
        'rule_type': 'style',
        'priority': 8,
        'description': 'Ambiguity Preservation - Giữ tính đa nghĩa/ngụ ý',
        'rule_text': 'Nếu nguyên bản Hán có tính đa nghĩa, ngụ ý,ẩn dụ (đặc biệt kệ/thần chú) thì bản dịch phải phản ánh được tính chất đó, không "làm rõ" thái quá làm mất ý nghĩa sâu xa.',
    },
    {
        'rule_code': 'RULE-009',
        'rule_type': 'style',
        'priority': 8,
        'description': 'Verse/Kệ Preservation - Giữ thể kệ/thần chú',
        'rule_text': 'Các đoạn kệ, thần chú, đhāraṇī phải dịch thể thơ/lục bát/đối cử nếu có thể, hoặc giữ nguyên Hán-Việt trong ngoặc đơn. Không xé nhỏ thành văn xuôi mất nhịp điệu.',
    },
    {
        'rule_code': 'RULE-010',
        'rule_type': 'forbidden',
        'priority': 10,
        'description': 'No External Doctrinal Inference - Không suy luận giáo lý ngoài',
        'rule_text': 'KHÔNG tự thêm giải thích giáo lý, không kéo theo triết lý Phật học ngoài văn bản để "làm rõ". Dịch theo văn bản, không theo hiểu biết cá nhân của dịch giả.',
    },
    {
        'rule_code': 'RULE-011',
        'rule_type': 'gate',
        'priority': 5,
        'description': 'Unknown Term → REVIEW - Thuật ngữ lạ phải review',
        'rule_text': 'Gặp thuật ngữ Hán không có trong GLOSSARY LOCK / translation_glossary / lexicon → xuất "[REVIEW: <Hán>]" trong bản dịch, để scholar review sau. Không tự sáng tạo nghĩa.',
    },
    {
        'rule_code': 'RULE-012',
        'rule_type': 'gate',
        'priority': 5,
        'description': 'Unknown Proper Name → REVIEW - Tên riêng lạ phải review',
        'rule_text': 'Gặp tên người/địa/năm hiệu không resolve được qua DILA/people/places/namevi_map → xuất "[REVIEW: <Hán>]" và flag cho scholar. Không tự phiên âm.',
    },
    {
        'rule_code': 'RULE-013',
        'rule_type': 'gate',
        'priority': 5,
        'description': 'Low Confidence → REVIEW - Độ tin cậy thấp phải review',
        'rule_text': 'Validator phát hiện: tỉ lệ ký tự ngoài ngưỡng, echo Hán, thiếu segment, structure mismatch → auto flag REVIEW. AI output KHÔNG tự thành canonical.',
    },
    {
        'rule_code': 'RULE-014',
        'rule_type': 'forbidden',
        'priority': 10,
        'description': 'No Automatic Canonical Promotion - Không tự thăng cấp canonical',
        'rule_text': 'AI output (L0/L1/L2) KHÔNG bao giờ tự động thành GOLD (L3). Chỉ human scholar review + approve mới đẩy lên canonical. Mọi L0-L2 đều ghi rõ provenance.',
    },
    {
        'rule_code': 'RULE-015',
        'rule_type': 'provenance',
        'priority': 10,
        'description': 'Provenance Required - Mọi bản dịch phải có nguồn gốc',
        'rule_text': 'Mỗi translation_segments phải có: source_original_hash, prompt_version, model_name, provider, ruleset_id, created_by_job_id, revision_no, supersedes_translation_id. Không provenance = không hợp lệ.',
    },
]


def _con():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def seed_ruleset(conn, dry_run):
    """Upsert ruleset into translation_rulesets."""
    if dry_run:
        print(f"[DRY] INSERT/UPDATE translation_rulesets: {RULESET_ID} v{RULESET_VERSION}")
        return
    conn.execute("""
        INSERT INTO translation_rulesets (ruleset_id, ruleset_version, description, is_canonical, created_by)
        VALUES (?,?,?,1,'t167_seed')
        ON CONFLICT(ruleset_id) DO UPDATE SET
            ruleset_version=excluded.ruleset_version,
            description=excluded.description,
            is_canonical=1,
            updated_at=datetime('now')
    """, (RULESET_ID, RULESET_VERSION, RULESET_DESCRIPTION))
    conn.commit()
    print(f"✅ Ruleset seeded: {RULESET_ID} v{RULESET_VERSION}")


def upsert_t167_rules(conn, dry_run):
    """Upsert 15 RULE-001..015 into translation_rules."""
    now = '2026-09-24 12:00:00'
    n_add, n_upd = 0, 0
    for rule in T167_RULES:
        existing = conn.execute("SELECT rule_code FROM translation_rules WHERE rule_code=?", (rule['rule_code'],)).fetchone()
        if dry_run:
            action = 'UPDATE' if existing else 'INSERT'
            print(f"  [DRY] {action} {rule['rule_code']}: {rule['description']}")
            continue
        conn.execute("""
            INSERT INTO translation_rules
              (rule_code, rule_type, description, rule_text, is_active, priority, created_by, created_at, updated_at)
            VALUES (?,?,?,?,1,?,'t167_seed',?,?)
            ON CONFLICT(rule_code) DO UPDATE SET
                rule_type=excluded.rule_type,
                description=excluded.description,
                rule_text=excluded.rule_text,
                is_active=1,
                priority=excluded.priority,
                updated_at=excluded.updated_at
        """, (rule['rule_code'], rule['rule_type'], rule['description'], rule['rule_text'],
              rule['priority'], now, now))
        if existing:
            n_upd += 1
        else:
            n_add += 1
    conn.commit()
    print(f"✅ T167 rules: {n_add} insert, {n_upd} update")


def link_ruleset_rules(conn, dry_run):
    """Map T167 rules + T123 style rules into translation_ruleset_rules."""
    # Collect rule_codes to link: T167 15 rules + T123 8 style rules
    t123_codes = [
        'PERSONA_BAN_DICH', 'EXPRESSION_PRINCIPLE', 'NO_ADDITION',
        'GLOSSARY_LOCK_STABLE', 'CANONICAL_NAMES', 'TONE_OVERALL',
        'LITERARY_PURITY', 'HONORIFIC_PRONOUN'
    ]
    all_codes = [r['rule_code'] for r in T167_RULES] + t123_codes

    if dry_run:
        for code in all_codes:
            exists = conn.execute("SELECT 1 FROM translation_rules WHERE rule_code=?", (code,)).fetchone()
            if exists:
                print(f"  [DRY] LINK ruleset_rules: {RULESET_ID} -> {code}")
            else:
                print(f"  [DRY] SKIP (rule not in DB): {code}")
        return

    n_link = 0
    for code in all_codes:
        exists = conn.execute("SELECT 1 FROM translation_rules WHERE rule_code=?", (code,)).fetchone()
        if not exists:
            print(f"  ⚠ Rule {code} chưa có trong translation_rules, bỏ qua link")
            continue
        conn.execute("""
            INSERT INTO translation_ruleset_rules (ruleset_id, rule_code, priority, is_active)
            VALUES (?,?,?,1)
            ON CONFLICT(ruleset_id, rule_code) DO UPDATE SET
                priority=excluded.priority,
                is_active=1
        """, (RULESET_ID, code, 0))  # priority 0 = ruleset manages priority via translation_rules.priority
        n_link += 1
    conn.commit()
    print(f"✅ Ruleset_rules linked: {n_link} rules")


def update_rules_ruleset_meta(conn, dry_run):
    """Update translation_rules.ruleset_id/ruleset_version/is_canonical for linked rules."""
    all_codes = [r['rule_code'] for r in T167_RULES] + [
        'PERSONA_BAN_DICH', 'EXPRESSION_PRINCIPLE', 'NO_ADDITION',
        'GLOSSARY_LOCK_STABLE', 'CANONICAL_NAMES', 'TONE_OVERALL',
        'LITERARY_PURITY', 'HONORIFIC_PRONOUN'
    ]
    if dry_run:
        for code in all_codes:
            print(f"  [DRY] UPDATE rules ruleset_meta: {code} -> ruleset={RULESET_ID} version={RULESET_VERSION}")
        return

    for code in all_codes:
        conn.execute("""
            UPDATE translation_rules SET
                ruleset_id = ?,
                ruleset_version = ?,
                is_canonical = 1
            WHERE rule_code = ?
        """, (RULESET_ID, RULESET_VERSION, code))
    conn.commit()
    print(f"✅ Rules ruleset_meta updated: {len(all_codes)} rules")


def cmd_verify():
    conn = _con()
    print('=== Verify T167 Constitution Seed ===')
    # ruleset
    rs = conn.execute("SELECT * FROM translation_rulesets WHERE ruleset_id=?", (RULESET_ID,)).fetchone()
    if rs:
        print(f'  ✅ ruleset: {rs["ruleset_id"]} v{rs["ruleset_version"]} canonical={rs["is_canonical"]}')
    else:
        print(f'  ❌ ruleset MISSING: {RULESET_ID}')
    # ruleset_rules count
    cnt = conn.execute("SELECT COUNT(*) FROM translation_ruleset_rules WHERE ruleset_id=?", (RULESET_ID,)).fetchone()[0]
    print(f'  ✅ ruleset_rules: {cnt} rules linked')
    # rules with ruleset_meta
    linked = conn.execute("SELECT rule_code, ruleset_id, ruleset_version, is_canonical FROM translation_rules WHERE ruleset_id=?", (RULESET_ID,)).fetchall()
    for r in linked:
        print(f'    - {r["rule_code"]}: ruleset={r["ruleset_id"]} v{r["ruleset_version"]} canonical={r["is_canonical"]}')
    # T167 rules presence
    missing = []
    for r in T167_RULES:
        e = conn.execute("SELECT 1 FROM translation_rules WHERE rule_code=?", (r['rule_code'],)).fetchone()
        if not e:
            missing.append(r['rule_code'])
    if missing:
        print(f'  ⚠ T167 rules missing in translation_rules: {missing}')
    else:
        print('  ✅ All 15 T167 rules present in translation_rules')
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()

    if args.verify:
        cmd_verify()
        return

    conn = _con()
    try:
        seed_ruleset(conn, args.dry_run)
        upsert_t167_rules(conn, args.dry_run)
        link_ruleset_rules(conn, args.dry_run)
        update_rules_ruleset_meta(conn, args.dry_run)
        if args.dry_run:
            print('\n[DRY RUN] Không ghi DB.')
        else:
            print('\n✅ T167 Constitution seed hoàn tất.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
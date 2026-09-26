#!/usr/bin/env python3
"""
T73 — Translation System: translation_rules + translation_cache
=================================================================
Tạo 2 bảng cho hệ thống "Tạm Dịch" DILA:
  - translation_rules:  admin cấu hình prompt rules → LLM dịch đúng chuẩn Phật học
  - translation_cache:  cache bản dịch theo rules_version → invalidate hàng loạt khi rules thay đổi

Idempotent. Chạy lại an toàn.
"""
import sqlite3, json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()
DB_PATH = ROOT / 'data' / 'lineage.db'

DEFAULT_RULES = [
    {
        "rule_code": "NO_PINYIN",
        "rule_type": "forbidden",
        "priority": 1,
        "description": "Cấm tuyệt đối dùng pinyin",
        "rule_text": (
            "NGHIÊM CẤM dùng phiên âm pinyin Trung Quốc trong bản dịch. "
            "Ví dụ: KHÔNG viết 'Zhijixiang', 'Bianjing', 'fashi', 'chanshi', 'dashi'. "
            "Tất cả tên riêng và danh hiệu phải chuyển sang âm Hán-Việt tương ứng."
        ),
    },
    {
        "rule_code": "HANVIET_NAMES",
        "rule_type": "terminology",
        "priority": 2,
        "description": "Tên người → âm Hán-Việt",
        "rule_text": (
            "Tên người (nhân danh) dùng âm Hán-Việt. "
            "Ví dụ: 智吉祥→Trí Cát Tường, 玄奘→Huyền Trang, 慧能→Huệ Năng, "
            "神秀→Thần Tú, 法藏→Pháp Tạng, 道信→Đạo Tín, 弘忍→Hoằng Nhẫn."
        ),
    },
    {
        "rule_code": "HANVIET_PLACES",
        "rule_type": "terminology",
        "priority": 3,
        "description": "Địa danh → âm Hán-Việt",
        "rule_text": (
            "Tên địa danh dùng âm Hán-Việt. "
            "Ví dụ: 汴京→Biện Kinh, 江西→Giang Tây, 四川→Tứ Xuyên, "
            "嘉州→Gia Châu, 江浙→Giang Triết, 洛陽→Lạc Dương, 長安→Trường An."
        ),
    },
    {
        "rule_code": "BUDDHIST_TITLES",
        "rule_type": "terminology",
        "priority": 4,
        "description": "Tước hiệu Phật giáo chuẩn Hán-Việt",
        "rule_text": (
            "Tước hiệu và thuật ngữ Phật giáo dùng đúng Hán-Việt: "
            "大師→Đại Sư, 法師→Pháp Sư, 禪師→Thiền Sư, 上堂→thượng đường, "
            "住持→trụ trì, 方丈→phương trượng, 和尚→Hòa Thượng, "
            "比丘→Tỳ Kheo, 菩薩→Bồ Tát, 禪宗→Thiền Tông, 律宗→Luật Tông."
        ),
    },
    {
        "rule_code": "REIGN_ERA",
        "rule_type": "terminology",
        "priority": 5,
        "description": "Niên hiệu và triều đại → Hán-Việt + năm Tây lịch",
        "rule_text": (
            "Niên hiệu và triều đại dùng Hán-Việt, giữ nguyên năm Tây lịch nếu có trong nguyên bản. "
            "Ví dụ: 皇祐五年（1053）→ năm Hoàng Hựu thứ năm (1053), "
            "北宋→Bắc Tống, 南宋→Nam Tống, 唐→Đường, 明→Minh, "
            "康熙三十年→năm Khang Hy thứ ba mươi (1691)."
        ),
    },
    {
        "rule_code": "ACADEMIC_STYLE",
        "rule_type": "style",
        "priority": 10,
        "description": "Văn phong học thuật Phật giáo Việt Nam",
        "rule_text": (
            "Văn phong trang trọng, học thuật Phật giáo Việt Nam truyền thống. "
            "Không dùng từ ngữ thông tục hay hiện đại xa lạ với kinh điển. "
            "Dùng đại từ tôn kính: 'ngài', 'sư', 'Hòa Thượng'. "
            "Khi nhắc đến hành trạng tu hành dùng văn phong súc tích như sử liệu Phật giáo."
        ),
    },
    {
        "rule_code": "CLASSICAL_SYNTAX",
        "rule_type": "grammar",
        "priority": 11,
        "description": "Hiểu cú pháp văn ngôn cổ Hán",
        "rule_text": (
            "Hiểu đúng cú pháp văn ngôn cổ Hán: câu tỉnh lược chủ ngữ, đảo ngữ, "
            "cụm bổ nghĩa đứng trước danh từ. "
            "Dịch cho trôi chảy tiếng Việt, không dịch từng chữ cứng nhắc theo nghĩa đen."
        ),
    },
    {
        "rule_code": "OUTPUT_FORMAT",
        "rule_type": "style",
        "priority": 20,
        "description": "Format output thuần bản dịch",
        "rule_text": (
            "Chỉ trả về bản dịch thuần tiếng Việt. "
            "KHÔNG kèm giải thích, KHÔNG ghi chú trong ngoặc [như thế này], "
            "KHÔNG lặp lại nguyên bản chữ Hán, KHÔNG thêm tiêu đề hay nhãn. "
            "Giữ cấu trúc đoạn văn của bản gốc."
        ),
    },
]


def run():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # ── translation_rules ─────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS translation_rules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code   TEXT UNIQUE NOT NULL,
            rule_type   TEXT,
            description TEXT,
            rule_text   TEXT NOT NULL,
            is_active   INTEGER DEFAULT 1,
            priority    INTEGER DEFAULT 100,
            created_by  TEXT DEFAULT 'system',
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── translation_cache ─────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS translation_cache (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source_hash     TEXT NOT NULL,
            source_type     TEXT DEFAULT 'person_bio',
            entity_id       TEXT,
            source_text     TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            model_id        TEXT,
            rules_version   TEXT,
            status          TEXT DEFAULT 'auto',
            report_count    INTEGER DEFAULT 0,
            approved_by     TEXT,
            approved_at     TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            UNIQUE(source_hash, source_type)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_entity ON translation_cache(entity_id, source_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_rules_ver ON translation_cache(rules_version, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tc_status ON translation_cache(status)")

    # ── Seed default rules (INSERT OR IGNORE = idempotent) ───────────────
    now = datetime.now().isoformat()
    for r in DEFAULT_RULES:
        conn.execute("""
            INSERT OR IGNORE INTO translation_rules
              (rule_code, rule_type, description, rule_text, is_active, priority, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, 'system', ?, ?)
        """, (r['rule_code'], r['rule_type'], r['description'], r['rule_text'], r['priority'], now, now))

    conn.commit()

    rules_cnt = conn.execute("SELECT COUNT(*) FROM translation_rules WHERE is_active=1").fetchone()[0]
    cache_cnt = conn.execute("SELECT COUNT(*) FROM translation_cache").fetchone()[0]
    print(f"[T73] translation_rules: {rules_cnt} active rules")
    print(f"[T73] translation_cache: {cache_cnt} rows (fresh)")

    # Print seeded rules
    for r in conn.execute("SELECT rule_code, rule_type, priority FROM translation_rules ORDER BY priority").fetchall():
        print(f"  [{r['priority']:3d}] {r['rule_code']} ({r['rule_type']})")

    conn.close()
    print("[T73] Done — bảng translation_rules + translation_cache sẵn sàng.")


if __name__ == '__main__':
    run()

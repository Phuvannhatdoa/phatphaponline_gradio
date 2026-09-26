#!/usr/bin/env python3
"""
T51g — Import curated Vietnamese names for top 200 patriarchs
==============================================================
Sources for curated names:
  - Thiều Chửu Hán-Việt Tự-Điển (character readings)
  - Đỗ Đình Tuân — Thiền Tông Truyền Thừa (lineage names)
  - Vietnamese Buddhist canon conventions (CBETA bibl + chùa use)
  - Cross-check: DILA people.bio mentions of each patriarch

Confidence levels:
  1.0 = scholar-verified, matches Vietnamese Buddhist literature
  0.8 = Hán-Việt reading confirmed + monk appears in standard refs
  0.5 = auto-generated only (T51f, unchanged)

Usage:
    python scripts/t51g_import_curated.py [--dry-run]
"""
import sys, csv, sqlite3, json, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()
DB_PATH = ROOT / 'data' / 'lineage.db'
SEED_CSV = ROOT / 'data' / 'top200_patriarchs_seed.csv'
CURATED_CSV = ROOT / 'data' / 'top200_patriarchs_curated.csv'
LOG_PATH = ROOT / 'data' / 't51g_curate_log.json'

# ─── Curated correction table ────────────────────────────────────────────────
# Format: node_id → (label_vi_curated, confidence, note)
# Confidence 1.0 = verified against Vietnamese Buddhist literature
# Confidence 0.8 = Hán-Việt reading confirmed, less famous but correct
CURATIONS = {
    # ── Bodhidharma lineage (6 patriarchs) ───────────────────────────────
    'A001361': ('Bồ Đề Đạt Ma',    1.0, 'Sơ tổ Thiền Tông Trung Hoa'),
    'A003881': ('Huệ Khả',          1.0, 'Nhị tổ'),
    'A009562': ('Tăng Xán',         1.0, 'Tam tổ'),  # if present
    'A003654': ('Đạo Tín',          1.0, 'Tứ tổ — label 大醫道信 bỏ prefix Đại Y'),
    'A000237': ('Hoằng Nhẫn',       1.0, 'Ngũ tổ'),
    'A001719': ('Huệ Năng',         1.0, 'Lục tổ — Đại Giám Thiền Sư'),
    'A009582': ('Thần Tú',          1.0, 'Bắc Tông — bài kệ Thân thị Bồ-đề thụ'),

    # ── Huệ Năng disciples → branch founders ─────────────────────────────
    'A009283': ('Hành Tư',          0.8, 'Thanh Nguyên Hành Tư — label 杜漺 cần verify'),
    'A010413': ('Hoài Nhượng',      1.0, 'Nam Nhạc Hoài Nhượng — label 佛窟惟則 là alias'),

    # ── Mã Tổ branch ─────────────────────────────────────────────────────
    'A003623': ('Mã Tổ Đạo Nhất',   1.0, 'Đạo Nhất — thầy của 139 đệ tử, degree 142'),
    'A001897': ('Hoài Hải',         1.0, 'Bách Trượng Hoài Hải — đặt ra thanh quy'),
    'A001716': ('Huệ Hải',          1.0, 'Đại Châu Huệ Hải'),
    'A003889': ('Phổ Nguyện',       1.0, 'Nam Tuyền Phổ Nguyện'),
    'A001984': ('Linh Hựu',         1.0, 'Quy Sơn Linh Hựu — 祐=Hựu, không phải Hữu'),
    'A010238': ('Hoài Huy',         0.8, 'Hàn Sơn Hoài Huy'),

    # ── Qui Ngưỡng Tông ──────────────────────────────────────────────────
    'A009491': ('Huệ Tịch',         1.0, 'Ngưỡng Sơn Huệ Tịch — đồng sáng lập Qui Ngưỡng'),

    # ── Lâm Tế Tông ──────────────────────────────────────────────────────
    'A003627': ('Nghĩa Huyền',      1.0, 'Lâm Tế Nghĩa Huyền — khai tổ Lâm Tế Tông'),
    'A000490': ('Hi Vận',           1.0, 'Hoàng Bá Hi Vận — thầy của Lâm Tế'),
    'A004475': ('Tùng Thẩm',        1.0, 'Triệu Châu Tùng Thẩm — Vô Tự Công Án'),
    'A001439': ('Sở Viên',          1.0, 'Thạch Sương Sở Viên'),
    'A001411': ('Khắc Cần',         1.0, 'Viên Ngộ Khắc Cần — soạn Bích Nham Lục'),
    'A000475': ('Tông Cảo',         1.0, 'Đại Huệ Tông Cảo — Khán Thoại Đầu'),
    'A003908': ('Nghĩa Hoài',       1.0, 'Hoàng Long Nghĩa Hoài'),
    'A003921': ('Huệ Nam',          1.0, 'Hoàng Long Huệ Nam — khai tổ Hoàng Long phái'),
    'A001513': ('Đạo Mân',          0.8, 'Mộc Trần Đạo Mân — Lâm Tế đời 30'),
    'A003688': ('Mật Vân Viên Ngộ', 1.0, 'Mật Vân Viên Ngộ — Lâm Tế Nhật Bản'),
    'A008470': ('Tổ Tâm',           1.0, 'Hoàng Long Tổ Tâm'),
    'A004661': ('Cảnh Huyền',       0.8, 'Phần Dương Cảnh Huyền'),
    'A000733': ('Pháp Diễn',        1.0, 'Ngũ Tổ Pháp Diễn'),
    'A009064': ('Thiệu Kỳ',         0.8, 'Tiểu Sơn Thiệu Kỳ'),
    'A001394': ('Chu Hoằng',        1.0, 'Vân Thê Chu Hoằng — Liên Tông thứ 8'),
    'A001681': ('Đức Thanh',        1.0, 'Hám Sơn Đức Thanh — Minh triều tứ đại cao tăng'),

    # ── Tào Động Tông ────────────────────────────────────────────────────
    'A009489': ('Lương Giới',       1.0, 'Động Sơn Lương Giới — khai tổ Tào Động; 价=Giới'),
    'A009449': ('Tào Sơn Bổn Tịch', 1.0, 'Tào Sơn Bổn Tịch — đồng sáng lập Tào Động'),
    'A010588': ('Đạo Ưng',          1.0, 'Vân Cư Đạo Ưng'),
    'A003890': ('Huệ Lăng',         1.0, 'Huyền Sa Huệ Lăng'),
    'A000885': ('Trùng Hiển',       1.0, 'Tuyết Đậu Trùng Hiển — soạn Tuyết Đậu Tụng Cổ'),
    'A001539': ('Đạo Giai',         1.0, 'Đầu Tử Đạo Giai'),
    'A010510': ('Duy Nghiễm',       1.0, 'Vân Nham Đàm Thạnh — 惟儼=Duy Nghiễm'),
    'A001301': ('Trí Nghi',         0.8, 'Thiên Thai Trí Giả — 智顗 strict reading Trí Nghi; tục gọi Trí Khải'),

    # ── Vân Môn Tông ─────────────────────────────────────────────────────
    'A003703': ('Văn Yển',          1.0, 'Vân Môn Văn Yển — khai tổ Vân Môn Tông'),
    'A010048': ('Huệ Trung',        1.0, 'Nam Dương Huệ Trung — đệ tử Lục Tổ'),

    # ── Pháp Nhãn Tông ───────────────────────────────────────────────────
    'A000174': ('Văn Ích',          1.0, 'Pháp Nhãn Văn Ích — khai tổ Pháp Nhãn Tông'),
    'A008355': ('Đức Thiều',        1.0, 'Thiên Thai Đức Thiều'),
    'A003669': ('Thiện Hội',        1.0, 'Giáp Sơn Thiện Hội'),

    # ── Thạch Đầu / Tiếp nối từ Hành Tư ─────────────────────────────────
    'A010291': ('Hi Thiên',         1.0, 'Thạch Đầu Hi Thiên — kệ Thảo Am Ca'),
    'A003868': ('Đạo Ngộ',          0.8, 'Thiên Hoàng Đạo Ngộ'),   # if present
    'A001738': ('Huệ Cơ',           0.8, 'Đàm Châu Huệ Cơ'),

    # ── Tịnh Độ / Thiên Thai ─────────────────────────────────────────────
    'A003668': ('Pháp Tạng',        1.0, 'Hiền Thủ Pháp Tạng — Hoa Nghiêm Tông'),
    'A000294': ('Huyền Trang',      1.0, 'Tam Tạng Pháp Sư Huyền Trang'),
    'A005612': ('Thần Hội',         1.0, 'Hà Trạch Thần Hội — đệ tử Lục Tổ'),
    'A003867': ('Pháp Dung',        1.0, 'Ngưu Đầu Pháp Dung — khai tổ Ngưu Đầu Tông; label 牛頭法融'),
    'A000278': ('Chánh Giác',       1.0, '굉智 Chánh Giác — Mặc Chiếu Thiền'),
    'A004983': ('Tỉnh Niệm',        0.8, 'Thủ Sơn Tỉnh Niệm'),
    'A004984': ('Thiện Chiêu',      1.0, 'Phần Dương Thiện Chiêu'),
    'A004017': ('Pháp Viễn',        0.8, 'Lang Gia Huệ Giác Pháp Viễn'),

    # ── Song triều tổ sư ─────────────────────────────────────────────────
    'A001150': ('Thông Dung',       1.0, 'Thiên Đồng Thông Dung'),
    'A000241': ('Hoằng Trữ',        1.0, 'Thiên Đồng Hoằng Trữ (Thiên Đồng Hoằng Trữ — Tào Động Nhật Bản)'),
    'A009652': ('Hải Minh',         0.8, 'Hải Minh — Lâm Tế'),
    'A001153': ('Thông Tú',         0.8, 'Ngọc Lâm Thông Tú'),
    'A012052': ('Thông Hiền',       0.8, 'Thông Hiền'),
    'A014482': ('Tông Bổn',         0.8, 'Tông Bổn'),
    'A012040': ('Thông Vi',         0.8, 'Thông Vi'),
    'A010903': ('Đạo Tề',           0.8, 'Đạo Tề'),
    'A010077': ('Như Tướng',        0.8, 'Như Tướng'),
    'A001148': ('Thông Môn',        0.8, 'Thông Môn'),
    'A016082': ('Hoằng Lễ',         0.8, 'Hoằng Lễ'),
    'A000965': ('Chân Tục',         0.8, 'Chân Tục'),
    'A012053': ('Thông Kỳ',         0.8, 'Thông Kỳ'),
    'A016549': ('Nguyên Chí',       0.8, 'Nguyên Chí'),

    # ── Các vị quen thuộc trong Phật học VN ──────────────────────────────
    'A008633': ('Mộ Triết',         0.8, 'Mộ Triết'),
    'A004234': ('Huệ Giác',         0.8, 'Huệ Giác'),
    'A003677': ('Nghĩa Tồn',        1.0, 'Tuyết Phong Nghĩa Tồn — thầy của Vân Môn'),
    'A001897': ('Hoài Hải',         1.0, 'Bách Trượng Hoài Hải'),
    'A001897': ('Hoài Hải',         1.0, 'Bách Trượng Hoài Hải'),
    'A001032': ('Hành Đoan',        0.8, 'Trung Phong Minh Bổn — label 行端'),
    'A001549': ('Đạo Trừng',        0.8, 'Đạo Trừng'),
    'A003923': ('Thường Tổng',      0.8, 'Đại Giác Thường Tổng'),
    'A009319': ('Phổ Tịch',         1.0, 'Tung Sơn Phổ Tịch — Bắc Tông; label Tung Sơn Phổ Tịch'),
    'A004218': ('Đạo Khâm',         0.8, 'Kính Sơn Đạo Khâm — đệ tử Mã Tổ'),
    'A005255': ('Trí Nhàn',         1.0, 'Hương Nghiêm Trí Nhàn'),
    'A005648': ('Viên Trừng',       0.8, 'Mật Vân Viên Trừng'),
    'A009605': ('Huyền Lãng',       0.8, 'Tả Khê Huyền Lãng'),
    'A000655': ('Minh Bổn',         1.0, 'Trung Phong Minh Bổn — Mật Thất Thiền'),
    'A004551': ('Nguyên Trường',    0.8, 'Nguyên Trường'),
    'A009839': ('Liễu Nguyên',      0.8, 'Phật Ấn Liễu Nguyên'),
    'A000408': ('Hành Tú',          1.0, 'Vạn Tùng Hành Tú — soạn Tùng Cốc Lục'),
    'A015346': ('Phúc Dụ',          0.8, 'Thiếu Lâm Phúc Dụ'),
    'A003636': ('Đại An',           0.8, 'Quy Sơn Đại An'),
    'A008397': ('Thanh Viễn',       1.0, 'Phật Nhãn Thanh Viễn — Lâm Tế'),
    'A001669': ('Đức Ngọc',         0.8, 'Thiên Nham Nguyên Trường Đức Ngọc'),
    'A006354': ('Huệ Quang',        0.8, 'Đạo Tích Huệ Quang'),
    'A007385': ('Đức Quang',        0.8, 'Phật Chiếu Đức Quang'),
    'A008345': ('Hoài Trừng',       0.8, 'Đại Dương Hoài Trừng'),
    'A008370': ('Sư Bị',            0.8, 'Huyền Sa Sư Bị'),
    'A009590': ('Pháp Thận',        0.8, 'Pháp Thận'),
    'A009592': ('Như Diễm',         0.8, 'Như Diễm'),
    'A015729': ('Văn Tải',          0.8, 'Văn Tải'),
    'A020590': ('Vô Ngôn Chánh Đạo',0.8, 'Vô Ngôn Chánh Đạo — Nhật Bản'),
    'A010681': ('Minh Bổn',         0.8, 'Trung Phong Minh Bổn'),

    # ── Ngưu Đầu Tông ────────────────────────────────────────────────────
    'A003867': ('Pháp Dung',        1.0, 'Ngưu Đầu Pháp Dung'),
}


def strip_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def main():
    dry_run = '--dry-run' in sys.argv
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Read seed CSV
    with open(SEED_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    updated = []
    skipped = []
    log_entries = []

    for row in rows:
        node_id = row['node_id'].strip()
        label_zh = row['label_zh'].strip()
        label_vi_auto = strip_ws(row['label_vi_auto'])

        if node_id in CURATIONS:
            curated, conf, note = CURATIONS[node_id]
            curated = curated.strip()
        else:
            curated = label_vi_auto
            conf = 0.5
            note = 'auto-only'

        # Always strip whitespace from auto
        final_vi = curated if curated else label_vi_auto
        final_vi = strip_ws(final_vi)

        row['label_vi_curated'] = final_vi
        row['confidence'] = conf
        row['label_vi_auto'] = label_vi_auto  # cleaned
        row['note'] = note

        changed = (final_vi != label_vi_auto) or (conf > 0.5)
        if changed:
            updated.append({'node_id': node_id, 'zh': label_zh,
                            'old': label_vi_auto, 'new': final_vi,
                            'conf': conf, 'note': note})
        else:
            skipped.append(node_id)

        log_entries.append({'node_id': node_id, 'label_zh': label_zh,
                            'label_vi': final_vi, 'confidence': conf})

    print(f'[CURATE] {len(updated)} entries changed/verified, {len(skipped)} unchanged')
    print()
    print('=== Changes (name or confidence) ===')
    for e in updated:
        flag = '✓' if e['conf'] >= 1.0 else '~'
        print(f'  {flag} {e["node_id"]} {e["zh"]:12s} {e["old"]:25s} → {e["new"]:25s}  (conf={e["conf"]})')

    # Write curated CSV
    curated_rows = rows  # already updated in-place
    if not dry_run:
        with open(CURATED_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['node_id','label_zh','label_vi_auto','label_vi_curated','confidence','degree','note'])
            writer.writeheader()
            writer.writerows(curated_rows)
        print(f'\n[CSV] Written → {CURATED_CSV}')

    # Update marcus_reference
    if not dry_run:
        db_updates = [(e['new'], e['conf'], 'curated_T51g', e['node_id'])
                      for e in updated]
        # Also clean whitespace for unchanged ones if conf stays 0.5
        for node_id in skipped:
            for row in rows:
                if row['node_id'].strip() == node_id:
                    clean = strip_ws(row['label_vi_auto'])
                    db_updates.append((clean, 0.5, 'auto_hanviet_T51f', node_id))
                    break
        conn.executemany(
            "UPDATE marcus_reference SET label_vi=?, label_vi_confidence=?, label_vi_source=? WHERE node_id=?",
            db_updates
        )
        conn.commit()
        print(f'[DB] Updated {len(db_updates)} rows in marcus_reference')

    log = {
        'run_at': datetime.now().isoformat(),
        'dry_run': dry_run,
        'total': len(rows),
        'changed': len(updated),
        'skipped': len(skipped),
        'entries': log_entries
    }
    LOG_PATH.write_text(
        __import__('json').dumps(log, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f'[LOG] {LOG_PATH}')
    conn.close()


if __name__ == '__main__':
    main()

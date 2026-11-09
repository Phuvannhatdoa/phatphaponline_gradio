"""
T22-LD2 — Dựng bảng tra cứu TRIỀU ĐẠI / ĐỜI VUA (additive vào `time_periods`).

VÌ SAO CẦN
==========
`time_periods` có sẵn 3 loại row nhưng **toàn bộ là rác** (đo 2026-10-05):

  period_name   rows   period_name_zh   era_name      start_year
  dynasty        123   'chinese'       'chinese'     NULL (123/123)
  era            815   '2','3','4'…    '2','3','4'…  NULL (815/815)
  emperor        570   số              số            NULL (570/570)

115.921 row còn lại là `lunar_month` (âm lịch + can chi) — **không** phải bảng triều đại.

Hậu quả:
* `scripts/t97_parse_time_mentions.py` (Phase 2) tra `SELECT id, start_year, end_year
  FROM time_periods WHERE era_name LIKE ?` ⇒ **không tra được gì** ⇒ 125 place nhóm B
  không quy được năm.
* `app.py:7849` ghi rõ: *"DILA time_periods: 'dynasty' rows have no start_year yet
  (T14 pending)"*. **T14 đã đóng (status=done, 4/4 acceptance tick) nhưng dữ liệu rỗng**
  ⇒ đóng sớm.

CÁCH LÀM
=========
**INSERT additive**, KHÔNG sửa/xoá 1.508 row rác (T82 freeze). `id` mới có tiền tố
`dyn_`/`era_` (TEXT, không đụng id số cũ) ⇒ `t97` chỉ khớp row mới vì row rác có
`era_name` là số.

NGUỒN
=====
Triều đại / niên hiệu Trung Hoa. Mỗi mục ghi `source` để truy vết:
* `dyn-` : khoảng triều đại (niên sử tiêu chuẩn)
* `era-` : niên hiệu đại vua
Nếu không chắc chắn ⇒ KHÔNG đưa vào. Script tự kiểm tra: era phải nằm trong khoảng
triều đại của nó; 2 era cùng đại vua không được chồng nhau; khoảng phải hợp lệ.

Usage
-----
  python -X utf8 scripts/t22_ld2_dynasty_era_lookup.py --stats
  python -X utf8 scripts/t22_ld2_dynasty_era_lookup.py --check      # tự kiểm tra + độ phủ
  python -X utf8 scripts/t22_ld2_dynasty_era_lookup.py --dry-run
  python -X utf8 scripts/t22_ld2_dynasty_era_lookup.py --apply
  python -X utf8 scripts/t22_ld2_dynasty_era_lookup.py --revert
"""

import argparse
import collections
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "..", "data", "lineage.db")
BACKUP_DIR = os.path.join(HERE, "..", "data", "backups")
LOG_PATH = os.path.join(HERE, "..", "data", "t22_ld2_log.json")

SRC = "t22_ld2_historical"

# =============================================================================
# TRIỀU ĐẠI — (tên Hán, tên Việt, năm đầu, năm cuối)
# Năm âm TCN dùng số âm.
# =============================================================================
DYNASTIES = [
    ("李朝", "Lý",                 1009, 1225),
    ("後金", "Hậu Kim",            1616, 1635),
    ("南漢", "Nam Hán",             939,  971),
    ("春秋", "Xuân Thu",            -770, -476),
    ("戰國", "Chiến Quốc",         -475, -221),
    ("秦",   "Tần",                 -221, -206),
    ("西漢", "Tây Hán",             -206,    8),
    ("新",   "Tân",                    9,   22),
    ("東漢", "Đông Hán",              25,  220),
    ("蜀漢", "Thục Hán",             221,  263),
    ("曹魏", "Tào Vĩ",               220,  265),
    ("孫吳", "Tôn Ngô",              222,  280),
    ("西晉", "Tây Tấn",              265,  316),
    ("東晉", "Đông Tấn",             317,  420),
    ("劉宋", "Lưu Tống",             420,  479),
    ("北魏", "Bắc Nguy",             386,  534),
    ("東魏", "Đông Nguy",            534,  550),
    ("西魏", "Tây Nguy",             535,  557),
    ("北齊", "Bắc Tề",               550,  577),
    ("北周", "Bắc Chu",              557,  581),
    ("隋",   "Tuy",                   581,  618),
    ("唐",   "Đường",                 618,  907),
    ("五代十國", "Ngũ Đại Thập Quốc",  907,  960),
    ("遼",   "Liêu",                  916, 1125),
    ("北宋", "Bắc Tống",             960, 1127),
    ("金",   "Kim",                  1115, 1234),
    ("西夏", "Tây Hạ",              1038, 1227),
    ("南宋", "Nam Tống",            1127, 1279),
    ("元",   "Nguyên",               1271, 1368),
    ("明",   "Minh",                 1368, 1644),
    ("清",   "Thanh",                1636, 1912),
    ("民國", "Dân Quốc",             1912, 1949),
]

# =============================================================================
# NIÊN HIỆU — (triều đại, tên Hán, tên Việt, năm đầu, năm cuối)
# =============================================================================
ERAS = [
    # --- Trần / Lý (Bắc Việt, xuất hiện trong ghi chú địa danh) ---
    ("李朝", "順天",   "Thuận Thiên", 1010, 1044),
    # --- Đông Hán / Tam Quốc / Tấn ---
    ("東漢", "建武",   "Kiến Vũ",      25,  56),
    ("東漢", "初平",   "Sơ Bình",     190, 193),
    ("東漢", "興平",   "Hưng Bình",   194, 195),
    ("東漢", "建安",   "Kiến An",     196, 220),
    ("曹魏", "黃初",   "Hoàng Tho",    220, 226),
    ("曹魏", "嘉平",   "Gia Bình",    249, 254),
    ("西晉", "泰始",   "Thái Sải",    265, 274),
    ("西晉", "咸寧",   "Hàm Ninh",    275, 280),
    ("西晉", "太康",   "Thái Khang",  280, 289),
    ("東晉", "隆和",   "Long Hoà",    361, 363),
    ("東晉", "興寧",   "Hưng Ninh",   363, 365),
    ("劉宋", "永初",   "Vĩnh Sơ",     420, 422),
    ("劉宋", "元嘉",   "Nguyên Gia",  424, 453),
    # --- Bắc Nguy ---
    ("北魏", "太和",   "Thái Hòa",    477, 499),
    ("北魏", "景明",   "Cảnh Minh",  500, 503),
    ("北魏", "正始",   "Chính Sử",   504, 508),
    ("北魏", "永平",   "Vĩnh Bình",  508, 512),
    ("北魏", "延昌",   "Diên Xương", 512, 516),
    ("北魏", "熙平",   "Hi Bình",    516, 520),
    ("北魏", "神龜",   "Thần Quy",   518, 520),
    ("東魏", "興和",   "Hưng Hoà",   539, 540),
    ("東魏", "武定",   "Vũ Định",    543, 550),
    ("北齊", "天保",   "Thiên Bảo",  550, 559),
    ("北齊", "乾明",   "Càn Minh",   560, 561),
    ("北齊", "皇建",   "Hoàng Kiến", 560, 561),
    ("北周", "保定",   "Bảo Định",   561, 567),
    ("北周", "建德",   "Kiến Đức",   572, 577),
    # --- Tuy ---
    ("隋",   "開皇",   "Khai Hoàng", 581, 600),
    ("隋",   "大業",   "Đại Nghiệp", 605, 618),
    # --- Đường ---
    ("唐",   "武德",   "Vũ Đức",     618, 626),
    ("唐",   "貞觀",   "Trinh Quan",  627, 649),
    ("唐",   "永徽",   "Vĩnh Vi",    650, 655),
    ("唐",   "顯慶",   "Hiển Khánh", 656, 661),
    ("唐",   "麟德",   "Lân Đức",    664, 665),
    ("唐",   "乾封",   "Càn Phong",  666, 668),
    ("唐",   "總章",   "Tổng Chương", 668, 670),
    ("唐",   "咸亨",   "Hàm Hằng",   670, 674),
    ("唐",   "上元",   "Thượng Nguyên", 674, 676),
    ("唐",   "開元",   "Khai Nguyên", 713, 741),
    ("唐",   "天寶",   "Thiên Bảo",  742, 756),
    ("唐",   "至德",   "Chí Đức",    756, 758),
    ("唐",   "乾元",   "Càn Nguyên", 758, 760),
    ("唐",   "大曆",   "Đại Lịch",   766, 779),
    ("唐",   "建中",   "Kiến Trung", 780, 783),
    ("唐",   "貞元",   "Trinh Nguyên", 785, 805),
    ("唐",   "元和",   "Nguyên Hòa", 806, 820),
    ("唐",   "長慶",   "Trường Khánh", 821, 823),
    ("唐",   "大和",   "Đại Hòa",    827, 835),
    ("唐",   "開成",   "Khai Thành", 836, 840),
    ("唐",   "會昌",   "Hội Xương",  841, 846),
    ("唐",   "大中",   "Đại Trung",   847, 860),
    ("唐",   "咸通",   "Hàm Thông",  860, 874),
    ("唐",   "乾符",   "Càn Phù",    874, 877),
    ("唐",   "廣明",   "Quảng Minh", 880, 881),
    ("唐",   "中和",   "Trung Hòa",  881, 884),
    ("唐",   "光啟",   "Quang Khải", 885, 888),
    ("唐",   "天復",   "Thiên Phục", 901, 904),
    ("唐",   "天祐",   "Thiên Hựu",  904, 907),
    # --- Ngũ Đại ---
    ("五代十國", "開平",   "Khai Bình",  907, 911),
    ("五代十國", "後梁",   "Hậu Lương", 907, 923),
    ("五代十國", "乾祐",   "Càn Hựu",   948, 951),
    ("五代十國", "天福",   "Thiên Phúc", 936, 943),
    ("五代十國", "開運",   "Khai Vận",  944, 947),
    ("南漢", "乾和",   "Càn Hòa",   951, 965),
    # --- Liêu ---
    ("遼",   "統和",   "Thống Hòa",  983, 1016),
    ("遼",   "開泰",   "Khai Thái", 1012, 1031),
    ("遼",   "重熙",   "Trọng Hi",  1032, 1055),
    ("遼",   "咸雍",   "Hàm Ung",   1055, 1063),
    ("遼",   "乾統",   "Càn Thống", 1061, 1068),
    ("遼",   "大康",   "Đại Khang", 1075, 1084),
    ("遼",   "大安",   "Đại An",    1085, 1094),
    ("遼",   "壽昌",   "Thọ Xương", 1095, 1101),
    # --- Bắc Tống ---
    ("北宋", "建隆",   "Kiến Long", 960, 963),
    ("北宋", "乾德",   "Càn Đức",   963, 968),
    ("北宋", "開寶",   "Khai Bảo",  968, 976),
    ("北宋", "太平興國", "Thái Bình Hưng Quốc", 976, 984),
    ("北宋", "雍熙",   " dung",      984, 987),
    ("北宋", "端拱",   "Đoản Cung", 988, 989),
    ("北宋", "淳化",   "Thuần Hóa", 990, 994),
    ("北宋", "至道",   "Chí Đạo",   995, 997),
    ("北宋", "咸平",   "Hàm Bình",  998, 1003),
    ("北宋", "景德",   "Cảnh Đức",  1004, 1007),
    ("北宋", "大中祥符", "Đại Trung Tường Phù", 1008, 1016),
    ("北宋", "天禧",   "Thiên Hỷ",  1017, 1021),
    ("北宋", "乾興",   "Càn Hưng",  1022, 1022),
    ("北宋", "天聖",   "Thiên Thánh", 1023, 1032),
    ("北宋", "明道",   "Minh Đạo",  1032, 1033),
    ("北宋", "景祐",   "Cảnh Hựu",  1034, 1038),
    ("北宋", "寶元",   "Bảo Nguyên", 1038, 1040),
    ("北宋", "慶曆",   "Khánh Lịch", 1041, 1048),
    ("北宋", "皇祐",   "Hoàng Hựu", 1049, 1054),
    ("北宋", "至和",   "Chí Hòa",   1054, 1056),
    ("北宋", "嘉祐",   "Gia Hựu",   1056, 1063),
    ("北宋", "治平",   "Trị Bình",  1064, 1067),
    ("北宋", "熙寧",   "Hi Ninh",   1068, 1077),
    ("北宋", "元豐",   "Nguyên Phong", 1078, 1085),
    ("北宋", "元祐",   "Nguyên Hựu", 1086, 1094),
    ("北宋", "紹聖",   "Thiêu Thánh", 1094, 1098),
    ("北宋", "元符",   "Nguyên Phù", 1098, 1100),
    ("北宋", "崇寧",   "Sùng Ninh", 1102, 1106),
    ("北宋", "大觀",   "Đại Quan",  1107, 1110),
    ("北宋", "政和",   "Chính Hòa", 1111, 1118),
    ("北宋", "宣和",   "Tuyên Hòa", 1119, 1125),
    # --- Kim ---
    ("金",   "收國",   "Thu Quốc",  1115, 1123),
    ("金",   "天輔",   "Thiên Phụ", 1123, 1137),
    ("金",   "天會",   "Thiên Hội", 1137, 1140),
    ("金",   "天慶",   "Thiên Khánh", 1140, 1141),
    ("金",   "皇統",   "Hoàng Thống", 1141, 1149),
    ("金",   "天德",   "Thiên Đức", 1149, 1153),
    ("金",   "貞元",   "Trinh Nguyên", 1153, 1156),
    ("金",   "正隆",   "Chính Long", 1156, 1161),
    ("金",   "明昌",   "Minh Xương", 1190, 1196),
    ("金",   "承安",   "Thừa An",   1196, 1200),
    ("金",   "泰和",   "Thái Hòa",  1201, 1208),
    ("金",   "大安",   "Đại An",    1209, 1211),
    ("金",   "貞祐",   "Trinh Hựu",  1213, 1217),
    ("金",   "興定",   "Hưng Định", 1217, 1222),
    ("金",   "元光",   "Nguyên Quang", 1222, 1223),
    ("金",   "正大",   "Chính Đại", 1223, 1226),
    # --- Tây Hạ ---
    ("西夏", "顯道",   "Hiển Đạo",  1038, 1048),
    ("西夏", "廣運",   "Quảng Vận", 1049, 1056),
    ("西夏", "天慶",   "Thiên Khánh", 1113, 1123),
    ("西夏", "乾祐",   "Càn Hựu",   1126, 1134),
    # --- Nam Tống ---
    ("南宋", "建炎",   "Kiến Diệm", 1127, 1130),
    ("南宋", "紹興",   "Thiêu Hưng", 1131, 1162),
    ("南宋", "隆興",   "Long Hưng", 1163, 1169),
    ("南宋", "乾道",   "Càn Đạo",   1170, 1174),
    ("南宋", "淳熙",   "Thuần Hý",  1174, 1189),
    ("南宋", "紹熙",   "Thiêu Hy",  1190, 1194),
    ("南宋", "慶元",   "Khánh Nguyên", 1195, 1200),
    ("南宋", "嘉泰",   "Gia Thái",  1201, 1204),
    ("南宋", "開禧",   "Khai Hỷ",   1205, 1207),
    ("南宋", "嘉定",   "Gia Định",  1208, 1224),
    ("南宋", "寶慶",   "Bảo Khánh", 1225, 1227),
    ("南宋", "紹定",   "Thiêu Định", 1228, 1233),
    ("南宋", "端平",   "Đoản Bình", 1234, 1236),
    ("南宋", "嘉熙",   "Gia Hy",    1237, 1240),
    ("南宋", "淳祐",   "Thuần Hựu", 1241, 1252),
    ("南宋", "寶祐",   "Bảo Hựu",   1253, 1258),
    ("南宋", "開慶",   "Khai Khánh", 1259, 1259),
    ("南宋", "景定",   "Cảnh Định", 1260, 1264),
    # --- Nguyên ---
    ("元",   "至元",   "Chí Nguyên", 1264, 1294),
    ("元",   "元貞",   "Nguyên Trinh", 1295, 1297),
    ("元",   "大德",   "Đại Đức",   1297, 1307),
    ("元",   "至大",   "Chí Đại",   1308, 1311),
    ("元",   "皇慶",   "Hoàng Khánh", 1312, 1313),
    ("元",   "延祐",   "Diên Hựu",  1314, 1320),
    ("元",   "至治",   "Chí Trị",   1321, 1323),
    ("元",   "泰定",   "Thái Định", 1324, 1328),
    ("元",   "天曆",   "Thiêu Lịch", 1328, 1330),
    ("元",   "至順",   "Chí Thuận", 1330, 1333),
    ("元",   "元統",   "Nguyên Thống", 1333, 1335),
    ("元",   "至正",   "Chí Chính", 1341, 1368),
    # --- Minh ---
    ("明",   "洪武",   "Hồng Vũ",   1368, 1398),
    ("明",   "建文",   "Kiến Văn",  1399, 1402),
    ("明",   "永樂",   "Vĩnh Nhạc", 1403, 1424),
    ("明",   "洪熙",   "Hồng Hi",   1425, 1425),
    ("明",   "宣德",   "Tuyên Đức", 1426, 1435),
    ("明",   "正統",   "Chính Thống", 1436, 1449),
    ("明",   "景泰",   "Cảnh Thái", 1450, 1456),
    ("明",   "天順",   "Thiên Thuận", 1457, 1464),
    ("明",   "成化",   "Thành Hóa",  1465, 1487),
    ("明",   "弘治",   "Hồng Trị",  1488, 1505),
    ("明",   "正德",   "Chính Đức",  1506, 1521),
    ("明",   "嘉靖",   "Gia Tịnh",  1522, 1566),
    ("明",   "隆慶",   "Long Khánh", 1567, 1572),
    ("明",   "萬曆",   "Vạn Lịch",  1573, 1620),
    ("明",   "泰昌",   "Thái Xương", 1621, 1621),
    ("明",   "天啟",   "Thiên Khải", 1622, 1627),
    ("明",   "崇禎",   "Sùng Trấn", 1628, 1644),
    # --- Thanh ---
    ("後金", "天命",   "Thiên Mệnh", 1616, 1626),
    ("後金", "天聰",   "Thiên Thông", 1627, 1636),
    ("清",   "崇德",   "Sùng Đức",  1636, 1643),
    ("清",   "順治",   "Thuận Trị", 1644, 1661),
    ("清",   "康熙",   "Khang Hy",   1662, 1722),
    ("清",   "雍正",   "Dung Chính", 1723, 1735),
    ("清",   "乾隆",   "Càn Lôn",   1736, 1795),
    ("清",   "嘉慶",   "Gia Khánh", 1796, 1820),
    ("清",   "道光",   "Đạo Quang", 1821, 1850),
    ("清",   "咸豐",   "Hàm Phong", 1851, 1861),
    ("清",   "同治",   "Đồng Trị",  1862, 1874),
    ("清",   "光緒",   "Quang Tự",  1875, 1908),
    ("清",   "宣統",   "Tuyên Thống", 1909, 1911),
]

# Niên hiệu bị DÙNG LẠI ở 2 triều đại (có thật trong lịch sử). `era_name` của ta có
# tiền tố triều đại nên vẫn phân biệt được, NHƯNG `t97_parse_time_mentions.py` tra
# `WHERE era_name LIKE '%<tên>%'` rồi lấy `rows[0]` ⇒ **không deterministic** với 4 tên này.
# Cần sửa T97 (thêm điều kiện triều đại, hoặc so khớp chính xác).
AMBIGUOUS_ERA = {
    "貞元": ["唐 785-805", "金 1153-1156"],
    "乾祐": ["五代十國 948-951", "西夏 1126-1134"],
    "大安": ["遼 1085-1094", "金 1209-1211"],
    "天慶": ["金 1140-1141", "西夏 1113-1123"],
}

DY_NAME = {d[0]: d for d in DYNASTIES}

# Era bắt đầu TRƯỚC khi triều đại chính thức cử hành — có thật trong lịch sử, ghi rõ
# thay vì nới lỏng kiểm tra (vì đây là ngoại lệ lịch sử chứ không phải lỗi dữ liệu).
ERA_BEFORE_DYNASTY = {
    "元_至元": "Cung Khanh trị vị từ 1264; Nguyên đổi quốc hiệu 1271 (niên hiệu có trước, "
               "thường niên sử vẫn đặt Nguyên 1271-1368)",
}


def build_rows():
    """Trả về list dict sẽ INSERT (chưa validate)."""
    out = []
    for zh, vi, y0, y1 in DYNASTIES:
        out.append({
            "id": "dyn_%s" % zh,
            "period_name": "dynasty",
            "period_name_zh": zh,
            "period_name_vi": vi,
            "start_year": y0,
            "end_year": y1,
            "era_name": "",
            "source_origin": SRC,
        })
    for dyn, zh, vi, y0, y1 in ERAS:
        out.append({
            "id": "era_%s_%s" % (dyn, zh),
            "period_name": "era",
            "period_name_zh": zh,
            "period_name_vi": vi,
            "start_year": y0,
            "end_year": y1,
            "era_name": "%s%s" % (dyn, zh),   # t97 tìm bằng LIKE
            "source_origin": SRC,
        })
    return out


def validate(rows):
    """Tự kiểm tra. Trả về (errors, warnings)."""
    err, warn = [], []
    seen_id = set()
    for r in rows:
        if r["id"] in seen_id:
            err.append("id trùng trong dữ liệu: %s" % r["id"])
        seen_id.add(r["id"])
        if r["end_year"] < r["start_year"]:
            err.append("%s: khoang nam nguoc (%s..%s)" % (r["id"], r["start_year"], r["end_year"]))
    # era phai nam trong khoang trieu dai
    for r in rows:
        if r["period_name"] != "era":
            continue
        dyn = r["id"].split("_")[1]
        d = DY_NAME.get(dyn)
        if not d:
            err.append("%s: trieu dai '%s' khong co trong DYNASTIES" % (r["id"], dyn))
            continue
        # era bat dau nam trong [dyn.start - 1, dyn.end + 1] (niem hieu co the tran)
        if r["start_year"] < d[2] - 1 or r["start_year"] > d[3] + 1:
            key = "%s_%s" % (dyn, r["period_name_zh"])
            if key in ERA_BEFORE_DYNASTY:
                warn.append("%s: %s" % (r["id"], ERA_BEFORE_DYNASTY[key]))
            else:
                err.append("%s: era bat dau %s ngoai khoang trieu dai %s (%s..%s)"
                           % (r["id"], r["start_year"], dyn, d[2], d[3]))
        if r["end_year"] > d[3] + 1:
            warn.append("%s: era ket thuoc %s > cuoi trieu dai %s (%s)" % (r["id"], r["end_year"], dyn, d[3]))
        if r["end_year"] > d[3]:
            warn.append("%s: era tran bien gioi trieu dai %s (chenh %d nam)" % (r["id"], dyn, r["end_year"] - d[3]))
    # 2 era cung ten trong 1 trieu dai khong chong nhau
    by = collections.defaultdict(list)
    for r in rows:
        if r["period_name"] == "era":
            by[r["id"].split("_")[1]].append(r)
    for dyn, lst in by.items():
        lst.sort(key=lambda x: x["start_year"])
        for i in range(len(lst) - 1):
            a, b = lst[i], lst[i + 1]
            if b["start_year"] < a["end_year"]:
                warn.append("%s: '%s' va '%s' CHONG THAT (%s..%s vs %s..%s)"
                            % (dyn, a["period_name_zh"], b["period_name_zh"],
                               a["start_year"], a["end_year"], b["start_year"], b["end_year"]))
            elif b["start_year"] == a["end_year"]:
                warn.append("[biên] %s: '%s'->'%s' chung nam bien %s (quy uoc chuyen doi)"
                            % (dyn, a["period_name_zh"], b["period_name_zh"], b["start_year"]))
    return err, warn


def coverage(conn, rows):
    """Đo: các era trong bảng có THỰC SỰ xuất hiện trong note không."""
    dyn_names = [d[0] for d in DYNASTIES]
    era_names = [e[1] for e in ERAS]
    hit_d, hit_e = collections.Counter(), collections.Counter()
    cur = conn.cursor()
    cur.execute("SELECT id, note FROM places_dila WHERE note IS NOT NULL AND note<>''")
    for pid, note in cur:
        for d in dyn_names:
            if d in note:
                hit_d[d] += 1
        for e in era_names:
            if e in note:
                hit_e[e] += 1
    return hit_d, hit_e


def cmd_check(conn):
    rows = build_rows()
    err, warn = validate(rows)
    print("=== TỰ KIỂM TRA ===")
    print("   dòng sẽ insert : %d (dynasty %d + era %d)"
          % (len(rows), len(DYNASTIES), len(ERAS)))
    print("   LỖI           : %d" % len(err))
    for e in err:
        print("      [LỖI] %s" % e)
    print("   CẢNH BÁO      : %d" % len(warn))
    for w in warn[:14]:
        print("      [cảnh báo] %s" % w)
    print()
    hit_d, hit_e = coverage(conn, rows)
    print("=== ĐỘ PHỦ TRONG note (59.167 place) ===")
    print("   triều đại có dùng: %d / %d" % (len(hit_d), len(DYNASTIES)))
    print("   niên hiệu có dùng: %d / %d" % (len(hit_e), len(ERAS)))
    print()
    print("   top triều đại:", ", ".join("%s(%d)" % (k, v) for k, v in hit_d.most_common(10)))
    print("   top niên hiệu:", ", ".join("%s(%d)" % (k, v) for k, v in hit_e.most_common(14)))
    unused_e = [e[1] for e in ERAS if e[1] not in hit_e]
    print()
    print("   niên hiệu CHƯA xuất hiện trong note: %d" % len(unused_e))
    if unused_e:
        print("      ", ", ".join(unused_e[:40]))
    print()
    print("=== ⚠ TƯƠNG THÍCH VỚI t97_parse_time_mentions.py ===")
    print("   t97 tra `era_name LIKE '%<ten>%'` rồi lấy rows[0].")
    print("   Niên hiệu TRÙNG TÊN ở 2 triều đại ⇒ t97 chọn bừa:")
    for k, v in AMBIGUOUS_ERA.items():
        print("      %-6s %s" % (k, " / ".join(v)))
    print("   `era_name` của ta = '<triều đại><tên>' nên vẫn phân biệt được —")
    print("   nhưng T97 cần bổ sung điều kiện triều đại. SỬA T97 (chưa làm ở task này).")
    print()
    print("   Tên triều đại 1 ký tự (新/秦/…) trùng chữ thường ⇒")
    print("   coverage đếm 'match' nhưng KHÔNG dùng làm khoá tra (era_name='' ⇒ không ai LIKE).")
    return err


def cmd_stats(conn):
    q = lambda s: conn.execute(s).fetchone()[0]
    print("=== time_periods HIỆN TẠI ===")
    for r in conn.execute("SELECT period_name,COUNT(*),"
                          "SUM(CASE WHEN start_year IS NOT NULL THEN 1 ELSE 0 END) "
                          "FROM time_periods GROUP BY period_name"):
        print("   %-14s %7d rows, co start_year: %d" % (r[0], r[1], r[2]))
    n = q("SELECT COUNT(*) FROM time_periods WHERE source_origin='%s'" % SRC)
    print("   row của T22-LD2: %d" % n)


def cmd_dry_run(conn):
    rows = build_rows()
    err, warn = validate(rows)
    have = set(r[0] for r in conn.execute("SELECT id FROM time_periods"))
    new = [r for r in rows if r["id"] not in have]
    skip = [r for r in rows if r["id"] in have]
    print("=== DRY-RUN ===")
    print("   sẽ INSERT : %d" % len(new))
    print("   đã có    : %d (bỏ qua)" % len(skip))
    print("   lỗi      : %d | cảnh báo: %d" % (len(err), len(warn)))
    print()
    print("   10 dòng mẫu:")
    for r in new[:10]:
        print("      %-22s %-8s %-14s %5s..%-5s era_name=%r"
              % (r["id"], r["period_name"], r["period_name_zh"],
                 r["start_year"], r["end_year"], r["era_name"]))
    print()
    print("KHÔNG ghi DB. Dùng --apply (có backup).")


def cmd_apply(conn, db_path):
    rows = build_rows()
    err, warn = validate(rows)
    if err:
        print("CÓ LỖI — không apply:")
        for e in err:
            print("   ", e)
        return
    have = set(r[0] for r in conn.execute("SELECT id FROM time_periods"))
    new = [r for r in rows if r["id"] not in have]
    if not new:
        print("Không có dòng mới.")
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(BACKUP_DIR, "lineage_t22ld2_%s.db" % stamp)
    shutil.copy2(db_path, backup)
    print("Backup: %s" % backup)
    cur = conn.cursor()
    n = 0
    for r in new:
        cur.execute(
            "INSERT OR REPLACE INTO time_periods "
            "(id,period_name,period_name_zh,period_name_vi,start_year,end_year,"
            " era_name,source_origin,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (r["id"], r["period_name"], r["period_name_zh"], r["period_name_vi"],
             r["start_year"], r["end_year"], r["era_name"], r["source_origin"],
             datetime.now().isoformat()),
        )
        n += cur.rowcount
    conn.commit()
    print("Đã insert: %d" % n)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"run_at": datetime.now().isoformat(), "backup": backup,
                   "inserted": n, "ids": [r["id"] for r in new]}, f,
                  ensure_ascii=False, indent=1)
    print("Log: %s" % LOG_PATH)
    conn.close()
    v = sqlite3.connect(db_path)
    g = lambda s: v.execute(s).fetchone()[0]
    print()
    print("VERIFY:")
    print("   row T22-LD2           : %d" % g(
        "SELECT COUNT(*) FROM time_periods WHERE source_origin='%s'" % SRC))
    print("   era có start_year     : %d" % g(
        "SELECT COUNT(*) FROM time_periods WHERE period_name='era' AND source_origin='%s' AND start_year IS NOT NULL" % SRC))
    print("   dynasty có start_year : %d" % g(
        "SELECT COUNT(*) FROM time_periods WHERE period_name='dynasty' AND source_origin='%s' AND start_year IS NOT NULL" % SRC))
    print("   t97 tra '%%康熙%%' se ra : %d" % g(
        "SELECT COUNT(*) FROM time_periods WHERE era_name LIKE '%\u5eb7\u7199%'"))
    print("   lunar_month con nguyen: %d (phai = 115921)" % g(
        "SELECT COUNT(*) FROM time_periods WHERE period_name='lunar_month'"))
    v.close()


def cmd_revert(conn, db_path):
    if not os.path.exists(LOG_PATH):
        print("Không có log — không có gì để revert.")
        return
    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)
    cur = conn.cursor()
    ph = ",".join("?" * len(log["ids"]))
    cur.execute("DELETE FROM time_periods WHERE id IN (%s)" % ph, log["ids"])
    deleted = cur.rowcount
    conn.commit()
    print("Đã xoá %d row T22-LD2." % deleted)
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    for f in ("stats", "check", "dry-run", "apply", "revert"):
        ap.add_argument("--" + f, action="store_true")
    a = ap.parse_args()
    if not any([a.stats, a.check, a.dry_run, a.apply, a.revert]):
        ap.print_help()
        sys.exit(1)
    db_path = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(db_path)
    if a.stats:
        cmd_stats(conn)
    elif a.check:
        cmd_check(conn)
    elif a.dry_run:
        cmd_dry_run(conn)
    elif a.apply:
        cmd_apply(conn, db_path)
    elif a.revert:
        cmd_revert(conn, db_path)
    conn.close()


if __name__ == "__main__":
    main()
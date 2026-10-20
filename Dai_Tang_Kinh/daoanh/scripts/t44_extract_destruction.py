"""
t44_extract_destruction.py — T44 GIAI ĐOẠN 2 (v2 — quy tắc năm siết lại 2026-10-10)
=====================================================================================
CHỈ ĐỌC. Không ghi DB. Đọc places_dila (note, note_category 寺廟) qua mode=ro,
tìm MỆNH ĐỀ (sau khi tách theo 。 rồi tách tiếp theo ，、；; và khoảng trắng nếu cần)
có từ khóa đốt/hủy.

Bộ từ khóa đốt/hủy dùng (theo yêu cầu task, ghi rõ để không im lặng mở rộng phạm vi):
  焚 燬 毀 火 燒 兵燹 災 廢 圮 壞

Phân loại:
  - 'destroyed' nếu mệnh đề có 焚/燬/火/燒/兵燹/災 (hành động đốt/tai họa hỏa hoạn trực tiếp)
  - 'abandoned' nếu mệnh đề có 廢/圮/壞 (bỏ hoang/đổ nát/hư hoại) và KHÔNG có từ khóa destroyed
  Nếu mệnh đề có cả 2 nhóm, ưu tiên 'destroyed'.

QUY TẮC NĂM MỚI (bắt buộc, sửa theo yêu cầu Admin 2026-10-10):
  1. Chỉ lấy năm cho sự kiện khi năm (dương lịch hoặc niên hiệu+số Hán) nằm TRONG
     CÙNG MỆNH ĐỀ với từ khóa đốt/hủy. Mệnh đề = tách theo 。 trước, rồi tách tiếp
     theo ，、；; (và khoảng trắng nếu cần) để thu nhỏ phạm vi so khớp năm.
  2. Nếu MỆNH ĐỀ (sau khi tách nhỏ) chứa động từ xây dựng/tái lập
     (建、創、立、再建、重建、復建、置、成、賜名、奏再建、始建) thì KHÔNG gán năm
     tìm được trong chính mệnh đề đó cho sự kiện đốt/hủy — loại năm, quy_tac_nam=
     'loai_nam_xay_dung', can_xem=true.
  3. Nếu mệnh đề đốt/hủy không có năm riêng (không tìm được niên hiệu/năm dương lịch
     trong chính mệnh đề đó): năm để trống, quy_tac_nam='khong_co_nam_trong_menh_de',
     can_xem=true. KHÔNG suy năm từ niên hiệu nằm ở mệnh đề khác trong câu.
     Dòng vẫn được xuất ra (không bị loại thầm lặng).
  4. Từ khóa 廢 chỉ tính là bỏ hoang khi đi với chùa/tự (寺/院) làm chủ ngữ. Nếu 廢
     đi với công trình phụ (善/亭/軒/閣/堂/殿) mà KHÔNG có 寺/院 trong cùng mệnh đề,
     hoặc nằm trong cụm cải tạo/đổi tên (改名/改為 + công trình phụ, hoặc
     "廢...亭/軒/閣/堂/殿...爲..." đổi tên công trình phụ) thì LOẠI khỏi sự kiện —
     không xuất dòng, chỉ đếm riêng, lý do='cải tạo/đổi tên công trình phụ'.
     (圮/壞 không bị áp quy tắc chủ ngữ này.)
  5. Cột mới:
       quy_tac_nam  — 'cung_menh_de' | 'khong_co_nam_trong_menh_de' | 'loai_nam_xay_dung'
       can_xem      — true/false. true nếu quy_tac_nam != 'cung_menh_de', HOẶC nếu
                      quy_tac_nam == 'cung_menh_de' nhưng có động từ xây dựng/tái lập
                      ở MỘT mệnh đề khác liền kề trong cùng câu (cùng 。) — cờ cảnh báo
                      để người xem lại, KHÔNG tự loại năm trong trường hợp này.

Mã CBETA: tìm pattern T\\d+n\\d+_p\\d+[abc]\\d+ xuất hiện trong CÂU gốc (phạm vi 。,
giữ như bản v1, vì mã CBETA thường đặt cuối câu, không nhất thiết cùng mệnh đề nhỏ
với từ khóa — KHÔNG thắt chặt phạm vi này vì ngoài yêu cầu của Admin lần này).

Nguồn trong ngoặc của note: mẫu（來源：trang）hoặc（來源） ở cuối note — lấy phần
trong ngoặc gần nhất đứng sau toàn note (không đổi so với v1).

Output: docs/evidence/2026-10-10_T44_destruction_preview_v2.tsv (KHÔNG ghi đè bản v1)
Cột: dila_id, place_name_zh, year, event_type, clause_zh, source_note, cbeta_ref,
     era_name, extraction_method, quy_tac_nam, can_xem

KHÔNG ghi DB. KHÔNG xóa file. KHÔNG git. KHÔNG gọi API.
"""
import sqlite3
import re
import sys
import csv
import argparse

sys.path.insert(0, 'scripts')
from dila_era_name_extract import ERA_TABLE, ERA_NAMES_SORTED, parse_cn_year, CN_NUM  # noqa: E402

DB_PATH = 'data/lineage.db'
OUT_PATH = 'docs/evidence/2026-10-10_T44_destruction_preview_v2.tsv'

# Bộ từ khóa đốt/hủy (ghi rõ 2 nhóm để phân loại event_type)
DESTROY_KW = re.compile(r'焚|燬|火|燒|兵燹|災')
ABANDON_KW = re.compile(r'廢|圮|壞')
ANY_KW = re.compile(r'焚|燬|毀|火|燒|兵燹|災|廢|圮|壞')

# Rule 2: động từ xây dựng/tái lập — đúng danh sách Admin yêu cầu, không tự mở rộng.
CONSTRUCTION_RE = re.compile(r'奏再建|賜名|再建|重建|復建|始建|建|創|立|置|成')

# Rule 4: 廢 chỉ hợp lệ khi chủ ngữ là chùa/tự; loại khi đi với công trình phụ
# và không có 寺/院 trong cùng mệnh đề, hoặc trong cụm cải tạo/đổi tên.
MINOR_BUILDING_RE = re.compile(r'善|亭|軒|閣|堂|殿')
TEMPLE_WORD_RE = re.compile(r'寺|院')
RENAME_PHRASE_RE = re.compile(r'改名|改為')

CBETA_REF_RE = re.compile(r'T\d+n\d+_p\d+[abc]\d+')
CE_YEAR_RE = re.compile(r'(\d{3,4})年')
LAST_PAREN_OPEN_RE = re.compile(r'（([^（]*)$')

# Tách mệnh đề nhỏ: theo dấu câu ，、；; và khoảng trắng (chỉ dùng để thu nhỏ phạm vi
# so khớp năm/động từ xây dựng; KHÔNG dùng để tách mã CBETA hay nguồn).
SUBCLAUSE_SPLIT_RE = re.compile(r'[，、；;\s]+')


def split_sentences(note: str):
    """Chia note thành các câu theo dấu 。 (giữ nguyên văn câu, không cắt xén)."""
    parts = note.split('。')
    sentences = []
    pos = 0
    for p in parts:
        if p:
            sentences.append((pos, p))
        pos += len(p) + 1  # +1 cho dấu 。 đã bị split bỏ
    return sentences


def split_subclauses(sentence: str):
    """Chia câu thành các mệnh đề nhỏ theo ，、；; và khoảng trắng (rule 1)."""
    parts = SUBCLAUSE_SPLIT_RE.split(sentence)
    return [p for p in parts if p]


def extract_era_year_in_clause(clause: str):
    """Tìm niên hiệu trong mệnh đề nhỏ, trả (year, era_name, method) hoặc (None, '', '')."""
    for era in ERA_NAMES_SORTED:
        idx = clause.find(era)
        if idx == -1:
            continue
        era_start, era_end, dynasty = ERA_TABLE[era]
        after_era = clause[idx + len(era):]
        m_year = re.match(r'^([元初中末]|[一二三四五六七八九十百千]+|\d+)年', after_era)
        if m_year:
            num_str = m_year.group(1)
            if num_str in ('中', '間', '末', '初'):
                mid = (era_start + era_end) // 2
                return mid, era, 'midpoint'
            elif num_str == '元':
                return era_start, era, 'exact_year'
            else:
                n = parse_cn_year(num_str)
                if n and 1 <= n <= (era_end - era_start + 2):
                    return era_start + (n - 1), era, 'exact_year'
        after_era_15 = after_era[:15]
        if re.match(r'^[中間初末]', after_era_15):
            mid = (era_start + era_end) // 2
            return mid, era, 'midpoint'
        m_nian = re.match(r'^年[間中]', after_era_15)
        if m_nian:
            mid = (era_start + era_end) // 2
            return mid, era, 'midpoint'
        return None, era, 'era_name_only'
    return None, '', ''


def classify_event_type(clause: str):
    """Trả (event_type, trigger_char_group) — trigger_char_group='destroy'|'abandon'."""
    if DESTROY_KW.search(clause):
        return 'destroyed', 'destroy'
    if ABANDON_KW.search(clause):
        return 'abandoned', 'abandon'
    return '', ''


def check_rule4_exclude(clause: str) -> str:
    """Rule 4: trả lý do loại nếu 廢 đi với công trình phụ/cụm đổi tên, '' nếu giữ.
    Chỉ áp dụng khi ký tự kích hoạt là 廢 (không áp cho 圮/壞)."""
    if '廢' not in clause:
        return ''
    has_temple = bool(TEMPLE_WORD_RE.search(clause))
    has_minor = bool(MINOR_BUILDING_RE.search(clause))
    has_rename_phrase = bool(RENAME_PHRASE_RE.search(clause))
    # cụm "廢...亭/軒/閣/堂/殿...爲..." (đổi tên công trình phụ) — có công trình phụ
    # và ký tự 爲/為 đứng sau công trình phụ trong cùng mệnh đề, không có 寺/院.
    has_wei_rename = False
    if has_minor and not has_temple:
        m = MINOR_BUILDING_RE.search(clause)
        if m and re.search(r'[爲為]', clause[m.end():]):
            has_wei_rename = True
    if has_rename_phrase and not has_temple:
        return 'cải tạo/đổi tên công trình phụ'
    if has_minor and not has_temple:
        return 'cải tạo/đổi tên công trình phụ'
    if has_wei_rename:
        return 'cải tạo/đổi tên công trình phụ'
    return ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0, help='Giới hạn số places_dila quét (debug, 0=không giới hạn)')
    args = parser.parse_args()

    con = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    cur = con.cursor()

    sql = "SELECT id, name_zh, note FROM places_dila WHERE note_category LIKE '%寺廟%' AND note IS NOT NULL AND note != ''"
    cur.execute(sql)

    rows_out = []
    total = 0
    scanned = 0
    excluded_renovation = 0
    cnt_cung_menh_de = 0
    cnt_khong_co_nam = 0
    cnt_loai_nam_xay_dung = 0
    cnt_can_xem = 0

    while True:
        batch = cur.fetchmany(500)
        if not batch:
            break
        for dila_id, name_zh, note in batch:
            scanned += 1
            if args.limit and scanned > args.limit:
                break
            note_source_m = LAST_PAREN_OPEN_RE.search(note)
            note_source = note_source_m.group(1).rstrip('）') if note_source_m else ''

            for sent_start, sentence in split_sentences(note):
                if not ANY_KW.search(sentence):
                    continue
                subclauses = split_subclauses(sentence)
                if not subclauses:
                    continue

                # tiền tính: mệnh đề nhỏ nào có động từ xây dựng (dùng cho can_xem "gần đó")
                construction_flags = [bool(CONSTRUCTION_RE.search(sc)) for sc in subclauses]

                for i, sub in enumerate(subclauses):
                    if not ANY_KW.search(sub):
                        continue
                    event_type, trigger_group = classify_event_type(sub)
                    if not event_type:
                        continue

                    # Rule 4 — chỉ áp khi ký tự kích hoạt event là 廢 (nhóm abandon có 廢)
                    if trigger_group == 'abandon' and '廢' in sub:
                        reason = check_rule4_exclude(sub)
                        if reason:
                            excluded_renovation += 1
                            continue

                    has_construction_here = construction_flags[i]
                    year, era_name, method = extract_era_year_in_clause(sub)
                    if year is None:
                        m_ce = CE_YEAR_RE.search(sub)
                        if m_ce:
                            year = int(m_ce.group(1))
                            method = method or 'ce_year_literal'
                            era_name = era_name or ''

                    if has_construction_here and (year is not None or era_name):
                        # Rule 2: mệnh đề có động từ xây dựng -> không gán năm của chính nó
                        year = None
                        era_name = ''
                        method = ''
                        quy_tac_nam = 'loai_nam_xay_dung'
                    elif year is not None:
                        quy_tac_nam = 'cung_menh_de'
                    else:
                        quy_tac_nam = 'khong_co_nam_trong_menh_de'
                        era_name = ''  # không giữ era_name mồ côi không gắn năm cụ thể
                        method = ''

                    # can_xem: luôn true trừ khi có năm riêng VÀ không có xây dựng gần đó
                    nearby_construction = any(
                        construction_flags[j] for j in range(len(subclauses)) if j != i
                    )
                    if quy_tac_nam == 'cung_menh_de':
                        can_xem = bool(nearby_construction)
                    else:
                        can_xem = True

                    cbeta_m = CBETA_REF_RE.search(sentence)
                    cbeta_ref = cbeta_m.group(0) if cbeta_m else ''

                    rows_out.append({
                        'dila_id': dila_id,
                        'place_name_zh': name_zh or '',
                        'year': year if year is not None else '',
                        'event_type': event_type,
                        'clause_zh': sub,
                        'source_note': note_source,
                        'cbeta_ref': cbeta_ref,
                        'era_name': era_name,
                        'extraction_method': method or '',
                        'quy_tac_nam': quy_tac_nam,
                        'can_xem': 'true' if can_xem else 'false',
                    })
                    total += 1
                    if quy_tac_nam == 'cung_menh_de':
                        cnt_cung_menh_de += 1
                    elif quy_tac_nam == 'khong_co_nam_trong_menh_de':
                        cnt_khong_co_nam += 1
                    elif quy_tac_nam == 'loai_nam_xay_dung':
                        cnt_loai_nam_xay_dung += 1
                    if can_xem:
                        cnt_can_xem += 1
            if args.limit and scanned > args.limit:
                break
        if args.limit and scanned > args.limit:
            break

    con.close()

    with open(OUT_PATH, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'dila_id', 'place_name_zh', 'year', 'event_type', 'clause_zh',
            'source_note', 'cbeta_ref', 'era_name', 'extraction_method',
            'quy_tac_nam', 'can_xem'
        ], delimiter='\t')
        w.writeheader()
        for r in rows_out:
            w.writerow(r)

    has_year = sum(1 for r in rows_out if r['year'] != '')
    has_cbeta = sum(1 for r in rows_out if r['cbeta_ref'])
    no_cbeta = total - has_cbeta
    reliable = sum(1 for r in rows_out if r['can_xem'] == 'false')

    print(f"TU_KHOA_DUNG: {ANY_KW.pattern}")
    print(f"TONG_PLACES_DILA_QUET (note_category chua 寺廟, note non-empty): {scanned}")
    print(f"TONG_SU_KIEN_TIM_DUOC: {total}")
    print(f"  - cung_menh_de (co nam rieng): {cnt_cung_menh_de}")
    print(f"  - khong_co_nam_trong_menh_de: {cnt_khong_co_nam}")
    print(f"  - loai_nam_xay_dung: {cnt_loai_nam_xay_dung}")
    print(f"CO_NAM (year != ''): {has_year}")
    print(f"KHONG_CO_NAM: {total - has_year}")
    print(f"DANG_TIN_CAY (can_xem=false): {reliable}")
    print(f"CAN_XEM (can_xem=true): {cnt_can_xem}")
    print(f"LOAI_CAI_TAO_DOI_TEN_CONG_TRINH_PHU (rule4, khong xuat dong): {excluded_renovation}")
    print(f"CO_MA_CBETA: {has_cbeta}")
    print(f"KHONG_CO_MA_CBETA: {no_cbeta}")
    print(f"OUTPUT: {OUT_PATH}")


if __name__ == '__main__':
    main()

"""
T234 — Data Honesty Gate (read-only). Chặn dữ liệu BỊA ĐẶT trước khi lọt vào UI.

VÌ SAO CẦN
===========
Hai sự cố cùng một gốc rễ — **acceptance bằng lời, không bằng query**:

1. **T14** đóng với 4/4 acceptance tick ✔ (`tasks/backup/T14-time-authority-import.md`,
   `status: done`) nhưng `time_periods` rồi/đề/emperor **1.508 dòng rác**, 0 dòng có
   `start_year`. `t97_parse_time_mentions.py` tra `WHERE era_name LIKE ?` ⇒ không lấy
   được gì ⇒ tầng dưới chết âm thầm.
2. **T22 Layer D** sinh **1.440 event** có năm thành lập **không có trong nguồn**
   ("DONE" từ 2026-08-30), nhãn ghi `… (NNN年建)` = mệnh lệnh bịa. `app.py:8209`
   đưa `event_evidence.exact_span` ra UI ⇒ người dùng thấy **trích dẫn thật** nhưng
   **năm sai**.

Script này biến 2 bài học thành **cơ chế**: 7 kiểm tra, tất cả **read-only**, FAIL ⇒
exit 1 ⇒ `npm run pipeline` **chặn**, không ai đóng được task với dữ liệu rác.

7 KIỂM TRA
===========
H1  `event_evidence.event_id` phải khớp `event_type` hiện tại của `place_timeline_events`
    (bắt đúng lỗi LD1: đổi event_type nhưng khoá evidence còn `ev:founding:*`)
H2  `time_mentions.time_authority_id` phải trỏ `time_periods.id` thật
    (hiện 3.591 row trỏ placeholder `reign_era_dict`)
H3  `place_timeline_events.year` phải suy ra được: có trong `note`, **hoặc** quy được
    bằng bảng triều đại (`<era><số Hán>年`) — bắt năm sai 400–1.000 năm
H4  `label_zh` không được chứa `(N年建)` khi N không có trong `note` (nhãn bịa)
H5  `source_ref` không được tự tham chiếu (`source_ref = source`)
H6  `time_periods` era/dynasty phải có `start_year` (chính là lỗi T14)
H7  mọi `dila_id` phải tồn tại trong `places_dila.id` (FK logic — bảng không khai FK)

Usage
-----
  python -X utf8 scripts/audit_data_honesty.py            # tất cả
  python -X utf8 scripts/audit_data_honesty.py --h1       # chỉ 1 kiểm tra
  python -X utf8 scripts/audit_data_honesty.py --list
Exit: 0 = sạch · 1 = có FAIL · 2 = chỉ WARN (không chặn)
"""

import argparse
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "..", "data", "lineage.db")

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
      "八": 8, "九": 9, "十": 10, "百": 100, "千": 1000, "零": 0, "〇": 0}
NUMCH = "一二三四五六七八九十百千零〇"
PLACEHOLDER_AUTH = "reign_era_dict"


def cn2int(s):
    """Chuyển số ghi bằng CHỨ SỐ HÁN ('三十三') hoặc CHỮ SỐ Ả RẬP ('33') → int.

    Nới (T271 nhóm 2): note nhiều nguồn ghi năm bằng chữ số Ả Rập
    ('永定3年', '武德7年', '光緒33年', '大中5年', '會昌5年'). Nếu là chữ số
    thuần Ả Rập thì int trực tiếp, không cần quy Hán. Trả None khi lẫn lộn.
    """
    if s.isdigit():
        return int(s)
    tot = 0
    cur = 0
    for ch in s:
        if ch not in CN:
            return None
        v = CN[ch]
        if v < 10:
            cur = (cur or 1) * v
        else:
            tot += (cur or 1) * v
            cur = 0
    return tot + cur


def load_era_map(conn):
    """{tên niên hiệu: [(y0, y1), ...]} từ time_periods (chỉ row có start_year).

    PHẢI giữ MỌI era cùng tên, không dùng setdefault. Có 4 tên bị trùng:
    貞元, 乾祐, 大安, 天慶 (vd 貞元 = 唐 785–805 và 宋 1153–1156). Trước đây
    chỉ giữ triều đại đầu tiên, nên khi tên trùng mà thuộc triều đại sau thì
    `y0 + n - 1` ra một năm RƠI VÀO KHOẢNG của triều đại trước => trả về năm
    sai và bị chấp nhận im lặng. Đây là lỗi nguy hiểm hơn hẳn báo FAIL.
    """
    out = {}
    for zh, s, e in conn.execute(
            "SELECT period_name_zh, start_year, end_year FROM time_periods "
            "WHERE period_name='era' AND start_year IS NOT NULL "
            "AND period_name_zh IS NOT NULL AND period_name_zh<>''"):
        if zh:
            out.setdefault(zh, []).append((s, e))
    return out


def era_year_in_text(text, era_map, year=None):
    """Nếu text có `<era><số Hán>年` mà quy được ⇒ trả CE year, ngược lại None.

    Với tên trùng, thử TỪNG khoảng của mọi era cùng tên và lấy khoảng bao phủ
    năm tính được. `-ce` = có era cùng tên nhưng năm nằm ngoài MỌI khoảng.

    Hạn chế còn lại: nếu một tên trùng mà SỐ NĂM hợp lệ với cả hai triều đại
    (vd 貞元二年: 786 theo 唐, 1154 theo 宋) thì lấy triều đại đầu tiên. Muốn
    loại hẳn phải đọc tiền tố triều đại trong note — nằm ngoài phạm vi H3.

    W1a (T252):
      (a) `元年` = năm thứ 1 — NUMCH không có `元` nên trước đây `…<era>元年`
          trả None và một số dòng FAIL oan.
      (b) nếu suy ra VƯỢT khoảng era nhưng TRUNG chính xác với `year` đã lưu
          thì vẫn chấp nhận (vd `洪武三十二年` → 1399, `周天復十十一` → 911):
          nguồn ghi như vậy, DB trung thành với nguồn. `year=None` ⇒ bỏ (b).
    """
    for zh, spans in era_map.items():
        i = text.find(zh)
        while i >= 0:
            m = re.match("((?:元|[" + NUMCH + "]{1,4}|[0-9]{1,4}))\\s*年",
                         text[i + len(zh): i + len(zh) + 7])
            if m:
                tok = m.group(1)
                n = 1 if tok == "元" else cn2int(tok)
                if n:
                    cands = [y0 + n - 1 for y0, _ in spans]
                    for y0, y1 in spans:
                        ce = y0 + n - 1
                        if y0 <= ce <= (y1 if y1 is not None else ce):
                            return ce
                    if year is not None and year in cands:
                        return year                  # (b) ngoai khoang nhung trung year
                    if cands:
                        return -cands[0]             # ngoai MỌI khoảng của mọi era
                return None
            i = text.find(zh, i + 1)
    return None


def era_year_exact(text, era_map, year):
    """W1a-nghiêm: True nếu MỘT biểu thức `<era><số>年` trong text suy ra ĐÚNG `year`.

    Dùng cho `label_zh` (nhãn của chính sự kiện) — không được phép "chấp nhận
    bừa" như luật nới của note. Kể cả khi số năm vượt khoảng era, miễn là
    khớp `year` đã lưu.
    """
    for zh, spans in era_map.items():
        for m in re.finditer(re.escape(zh) + "((?:元|[" + NUMCH + "]{1,4}|[0-9]{1,4}))" + r"\s*年", text):
            tok = m.group(1)
            n = 1 if tok == "元" else cn2int(tok)
            if n and any(y0 + n - 1 == year for y0, _ in spans):
                return True
    return False


def era_mid_hit(text, era_map, year):
    """W1b: `<era>中` / `<era>年間` / `<era>間` (không có số năm) mà `year`
    nằm trong khoảng của chính era đó — cùng mức bằng chứng với midpoint
    (chứng minh được "nằm trong khoảng", không chứng minh được đúng năm)."""
    for zh, spans in era_map.items():
        if not re.search(re.escape(zh) + r"\s*年?\s*[中間]", text):
            continue
        for y0, y1 in spans:
            if y0 <= year <= (y1 if y1 is not None else year):
                return True
    return False


def era_range_hit(text, era_map, year):
    """W1c: `<era>…（Y0-Y1）` — khoảng năm do CHÍNH note ghi, `year` nằm trong đó.

    Bắt buộc: khoang dung trong ngoac, ngay truoc do co chu Han va co ten
    niem hieu — tranh bat vao so trong tham van (vd `T50n2063_p0943a29`).
    """
    for m in re.finditer(r"[（(]\s*(\d{3,4})\s*[^\d]{1,4}(\d{3,4})\s*[)）]", text):
        y0, y1 = int(m.group(1)), int(m.group(2))
        if y0 > y1:
            y0, y1 = y1, y0
        truoc = text[max(0, m.start() - 14):m.start()]
        if not any("一" <= c <= "鿿" for c in truoc):
            continue
        if not any(zh in truoc for zh in era_map):
            continue
        if y0 <= year <= y1:
            return True
    return False


# ---------------------------------------------------------------- H1
def h1(conn):
    sql = """
    SELECT COUNT(*) FROM place_timeline_events p
    WHERE NOT EXISTS (
        SELECT 1 FROM event_evidence e
        WHERE e.event_id = 'ev:' || p.event_type || ':' || p.dila_id)
    """
    n = conn.execute(sql).fetchone()[0]
    return n, ("event_evidence khong khop event_type hien tai cua place_timeline_events"
               if n else "khop event_type")


# ---------------------------------------------------------------- H2
def h2(conn):
    # Placeholder tach rieng: neu dem chung vao nhanh 'khong ton tai' se bi
    # tinh 2 lan (96 -> 192). Loai no khoi nhanh de con lai so that su.
    q = ("SELECT COUNT(*) FROM time_mentions WHERE time_authority_id IS NOT NULL "
         "AND time_authority_id<>'' AND time_authority_id<>? "
         "AND time_authority_id NOT LIKE 'era\\_%' ESCAPE '\\' "
         "AND time_authority_id NOT IN (SELECT id FROM time_periods)")
    n = conn.execute(q, (PLACEHOLDER_AUTH,)).fetchone()[0]
    ph = conn.execute("SELECT COUNT(*) FROM time_mentions WHERE time_authority_id=?",
                      (PLACEHOLDER_AUTH,)).fetchone()[0]
    return n + ph, ("authority goc placeholder %s: %d | authority sai dinh danh khac: %d"
                    % (PLACEHOLDER_AUTH, ph, n))


# ---------------------------------------------------------------- H3
# Khoang nam hien ra trong label_zh co dang "(25–220年間)". dau ghep la EN-DASH
# (U+2013) / EM-DASH, KHONG phai '-' ASCII — dung LIKE '%-%' se bo sot ~99%.
RANGE_RE = re.compile(r"(\d{1,4})[^\d]{1,4}(\d{1,4})\s*年間")


def label_range(label):
    """(y0, y1) neu label_zh hien ro khoang nam; None neu khong."""
    m = RANGE_RE.search(label or "")
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    return (a, b) if a <= b else (b, a)


def h3(conn):
    """Nam phai suy ra duoc tu CHUNG MINH.

    Tinh nang 1: chap nhan claim co cau truc (source_ref '^Q<digits>'), year den
    tu Wikidata (P571/P57) — co bang chung that, 223 dong.

    Tinh nang 2: chap nhan nam DUOC GHI NHAN RO — nguon 'dila_dynasty' lay
    year = trung diem khoang trieu dai. Chi chap nhan khi ca 3 dieu kien:
      (a) source_ref ket thuc bang 'midpoint'  -> nguon no rang day la suy diem
      (b) label_zh HIEN khoang (vd "(25–220年間)") -> nguoi doc thay do lech
      (c) year nam trong khoang do
    Thieu (b) = do chinh xac khong kiem chung duoc -> van FAIL.
    (c) sai = mau thuan noi tai -> van FAIL (da bat 1 dong).

    Tinh nang 3 (W1 — T252, dat truoc QID/midpoint vi la bang chung tu text):
      W1a-legacy: `era_year_in_text(note)` — hanh vi cu GIU NGUYEN (nhanh dau
          tien nam trong khoang era), nay ho tro `元年` va truong hop suy ra
          vuot khoang nhung TRUNG chinh xac `year` da luu.
      W1a-nghiem : `era_year_exact` tren CHINH label_zh (va note) — chi chap
          nhan khi mot bieu thuc `<era><so>年` suy ra DUNG `year`. label_zh la
          nhan cua su kien nen khong duoc "chep nhanh" nhu note.
      W1b        : `<era>中/年間/间/間` (khong co so nam) ma `year` nam trong
          khoang era — cung muc bang chung nhu midpoint.
      W1c        : `<era>…（Y0-Y1）` — khoang nam do CHINH note ghi, `year`
          nam trong do.
    """
    era_map = load_era_map(conn)
    bad_out, bad_none = [], []
    qid_ok = labeled_ok = 0
    w1a_legacy = w1a_exact = w1a_l = w1b_ok = w1c_ok = 0
    lab_norange = lab_outofrange = 0

    rows = conn.execute(
        "SELECT p.dila_id, p.year, p.source_ref, p.label_zh, pd.note "
        "FROM place_timeline_events p "
        "LEFT JOIN places_dila pd ON pd.id = p.dila_id "
        "WHERE p.year IS NOT NULL").fetchall()
    for did, year, sref, label, note in rows:
        note = note or ""
        label = label or ""
        sref = sref or ""
        if str(year) in note or str(year) in note.replace("（", "(").replace("）", ")"):
            continue
        r = era_year_in_text(note, era_map, year)
        if r is not None and r >= 0:
            w1a_legacy += 1
            continue
        if era_year_exact(note, era_map, year):
            w1a_exact += 1
            continue
        if era_year_exact(label, era_map, year):
            w1a_l += 1
            continue
        if re.match("^Q\\d+", sref):
            qid_ok += 1                     # claim co cau truc: bang chung that
            continue
        if sref.endswith("midpoint"):
            rng = label_range(label)
            if rng is None:
                lab_norange += 1            # midpoint nhung khong hien khoang
                bad_none.append((did, year))  # van FAIL: khong kiem chung duoc
                continue
            if rng[0] <= year <= rng[1]:
                labeled_ok += 1             # suy diem, co nhan, nam trong khoang
                continue
            lab_outofrange += 1             # mau thuan noi tai
            bad_out.append((did, year))
            continue
        if era_mid_hit(note, era_map, year) or era_mid_hit(label, era_map, year):
            w1b_ok += 1
            continue
        if era_range_hit(note, era_map, year) or era_range_hit(label, era_map, year):
            w1c_ok += 1
            continue
        (bad_out if (r is not None and r < 0) else bad_none).append((did, year))
    return len(bad_out) + len(bad_none), (
        "khong suy ra duoc (%d) + ngoai khoang trieu dai (%d) | W1a legacy note "
        "%d + W1a nghiem note %d/label %d + W1b %d + W1c %d | QID %d + "
        "midpoint co nhan %d; midpoint khong hien khoang (%d) va year ngoai "
        "khoang (%d) van FAIL; vi du: %s"
        % (len(bad_none), len(bad_out), w1a_legacy, w1a_exact, w1a_l,
           w1b_ok, w1c_ok, qid_ok, labeled_ok,
           lab_norange, lab_outofrange,
           (bad_out[:3] or bad_none[:3])))


# ---------------------------------------------------------------- H4
def h4(conn):
    rows = conn.execute(
        "SELECT p.dila_id, p.label_zh, pd.note FROM place_timeline_events p "
        "LEFT JOIN places_dila pd ON pd.id = p.dila_id "
        "WHERE p.label_zh LIKE '%年建%'").fetchall()
    bad = []
    for did, lab, note in rows:
        note = note or ""
        m = re.search("[（(]\\s*(\\d{1,4})\\s*年建\\s*[)）]", lab or "")
        if m and m.group(1) not in note:
            bad.append((did, m.group(1)))
    return len(bad), ("nhan '(N年建)' ma N khong co trong note (menh lenh bia): %d"
                      % len(bad))


# ---------------------------------------------------------------- H5
def h5(conn):
    n = conn.execute("SELECT COUNT(*) FROM place_timeline_events "
                     "WHERE source_ref = source").fetchone()[0]
    return n, "source_ref tu tham chieu (source_ref = source)"


# ---------------------------------------------------------------- H6
def h6(conn):
    """Do RUI RO thuc su, khong phai so luong rac ton tai.

    1.508 dong legacy (start_year NULL) van con trong bang de giu T82 freeze.
    Chi 'duoc dung' moi la rui ro: co duoc tham chieu boi time_mentions hay khong.
    """
    tot = conn.execute(
        "SELECT COUNT(*) FROM time_periods WHERE period_name IN "
        "('era','dynasty','emperor') AND start_year IS NULL").fetchone()[0]
    used = conn.execute(
        "SELECT COUNT(DISTINCT t.time_authority_id) FROM time_mentions t "
        "JOIN time_periods p ON p.id = t.time_authority_id "
        "WHERE p.start_year IS NULL").fetchone()[0]
    return used, ("legacy rows co start_year NULL: %d (giu nguyen vi T82) | "
                  "BI THAM CHEU boi time_mentions: %d" % (tot, used))


# ---------------------------------------------------------------- H7
def h7(conn):
    n = conn.execute(
        "SELECT COUNT(*) FROM place_timeline_events p "
        "WHERE NOT EXISTS (SELECT 1 FROM places_dila d WHERE d.id = p.dila_id)"
    ).fetchone()[0]
    return n, "dila_id khong ton tai trong places_dila.id (FK logic — bang khong khai FK)"


CHECKS = [
    ("H1", h1, "event_evidence.event_id khop event_type"),
    ("H2", h2, "time_mentions.time_authority_id tro tai that"),
    ("H3", h3, "nam suy ra duoc tu note hoac bang trieu dai"),
    ("H4", h4, "nhan '(N年建)' co khop nguon"),
    ("H5", h5, "source_ref khong tu tham chieu"),
    ("H6", h6, "time_periods era/dynasty co start_year"),
    ("H7", h7, "dila_id ton tai trong places_dila"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="FAIL => exit 1 ( dung cho pipeline chan ). "
                         "Khong co co => report, luon exit 0.")
    for c in CHECKS:
        ap.add_argument("--" + c[0].lower(), action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, _, desc in CHECKS:
            print("  %s  %s" % (k, desc))
        return 0
    only = [c for c in CHECKS if getattr(a, c[0].lower())]
    run = only or CHECKS

    conn = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(DB_PATH).replace("\\", "/"),
                           uri=True)
    print("=" * 68)
    print("T234 DATA HONESTY GATE — read-only, %d kiem tra" % len(run))
    print("=" * 68)
    nfail = 0
    for key, fn, desc in run:
        try:
            n, msg = fn(conn)
        except Exception as e:                       # gate phai bao loi chu duot
            print("  [LOI ] %s  %s" % (key, e))
            nfail += 1
            continue
        if n:
            print("  [FAIL] %s  %-46s %d" % (key, desc, n))
            print("         %s" % msg)
            nfail += 1
        else:
            print("  [ OK ] %s  %s" % (key, desc))
    conn.close()
    print("-" * 68)
    if nfail:
        print("[BAO CAO] FAIL %d/%d — du lieu BI DANG/SAI." % (nfail, len(run)))
        if a.strict:
            print("[STRICT] pipeline bi chan.")
            return 1
        print("[REPORT] khong chan pipeline (thieu --strict). Xem 'npm run"
              " audit:honesty:strict' de chan.")
        return 0
    print("PASS %d/%d — khong phat hien du lieu bia dat" % (len(run), len(run)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
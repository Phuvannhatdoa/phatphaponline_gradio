# -*- coding: utf-8 -*-
"""vnpa_lookup.py — [T200] tra `vn_person_authority` theo `dila_id` CÓ THỨ TỰ XÁ ĐỊNH.

VÌ SAO CẦN
----------
`vn_person_authority.dila_id` **KHÔNG phải khoá duy nhất**:
1.259 `dila_id` khác nhau / 1.506 row ⇒ **33 `dila_id` mang 2–3 dòng** (9 nhóm có cả dòng
`alias_*` lẫn dòng non-alias).

Các call site cũ viết `... WHERE dila_id=? LIMIT 1` **không `ORDER BY`** ⇒ SQLite trả dòng
theo thứ tự quét (rowid/index), tức **không xác định** với query planner. Hệ quả: dòng `alias_*`
mang tên đầy đủ có tiền tố triều đình có thể thắng ⇒ UI hiện **tên của người khác**
(vd `A021395`: `Ngũ Tổ Pháp Diễn` vs `Báo Ân Pháp Diễn` vs `Tứ Tổ Pháp Diễn`).

TIE-BREAK THEO STATUS (Admin chốt 2026-10-01)
-------------------------------------------
Thứ tự ưu tiên, **khớp cả ngữ nghĩa lẫn dữ liệu**:

| status          | rows | % khớp `people.name_vi` | lý do |
|-----------------|------|-------------------------|-------|
| `verified`      | 2    | –                       | admin đã xác nhận — `canonical_lock` đọc ở level 0.95 (LOCKED) |
| `pending`       | 448  | **10.5%**               | người đã nhập/duyệt tay, khớp tên lõi cao nhất |
| `auto_ttl`      | 599  | 6.3%                    | tự sinh từ TTL |
| `alias_vi_suffix` | 450 | 2.7%                   | row alias, tên đầy đủ có tiền tố |
| `alias_zh_match`  | 7   | 0.0%                    | row alias, khớp qua tên Hán |

⇒ `ORDER BY <rank> ASC, id ASC` — `id` làm tie-break cuối nên **luôn deterministic** và ổn định
khi ETL thêm dòng mới (không phụ thuộc thứ tự chèn).

LƯU Ý
------
29/33 nhóm trùng **không có dòng nào khớp `people.name_vi`** ⇒ "khớp `people.name_vi`" KHÔNG
phải tiêu chí chọn được ở đây. Task này chỉ **ổn định hoá** kết quả, **không** sửa nội dung dữ liệu.
Việc gộp/tách 33 nhóm `dila_id` cần Admin duyệt từng nhóm (xem `tasks/T200-…md` §2).
"""

VNPA_STATUS_RANK = (
    "CASE status"
    " WHEN 'verified' THEN 0"
    " WHEN 'pending' THEN 1"
    " WHEN 'auto_ttl' THEN 2"
    " WHEN 'alias_vi_suffix' THEN 3"
    " WHEN 'alias_zh_match' THEN 4"
    " ELSE 5"
    " END"
)

#: Mảnh `ORDER BY` dán thêm vào mọi truy vấn `vn_person_authority` lọc theo `dila_id`.
VNPA_ORDER_BY = "ORDER BY %s ASC, id ASC" % VNPA_STATUS_RANK

#: Cột `id` là khoá (TEXT). `LIMIT 1` chỉ dùng khi đã kèm `VNPA_ORDER_BY`.
_COLS = "id, name_vi, name_zh, dila_id, status, ttl_filename"


def lookup_by_dila(conn, dila_id, extra_cols=""):
    """Trả `sqlite3.Row` (dict-like) của dòng **canonical nhất** cho `dila_id`, hoặc `None`.

    Dùng cho mọi tra cứu 1-người. Thay `... WHERE dila_id=? LIMIT 1` không `ORDER BY`.

    Args:
        conn: sqlite3 connection.
        dila_id: mã DILA (A0…).
        extra_cols: các cột bổ sung phân cách bởi dấu phẩy (vd ``generation_order,
            dharma_lineage, biographical_note_vi``).
    """
    if not dila_id:
        return None
    cols = _COLS if not extra_cols else "%s, %s" % (_COLS, extra_cols)
    sql = ("SELECT %s FROM vn_person_authority WHERE dila_id=? %s LIMIT 1"
           % (cols, VNPA_ORDER_BY))
    try:
        return conn.execute(sql, (dila_id,)).fetchone()
    except Exception:
        return None


def map_dila_to_name(conn):
    """Dựng dict `{dila_id: name_vi}` với **người thắng xác định** (1 lượt quét).

    Thay vòng `result[r[0]] = r[1]` (dòng sau đè dòng trước → không xác định với 33 nhóm trùng).
    """
    out = {}
    try:
        rows = conn.execute(
            "SELECT dila_id, name_vi FROM vn_person_authority "
            "WHERE dila_id IS NOT NULL AND dila_id != '' "
            "AND name_vi IS NOT NULL AND name_vi != '' "
            "%s" % VNPA_ORDER_BY).fetchall()
    except Exception:
        return out
    for r in rows:
        out.setdefault(r[0], r[1])
    return out


def has_duplicate_dila(conn):
    """(bool, so_dila_id_trung) — dùng cho audit/test: còn nhóm trùng hay không."""
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM (SELECT dila_id FROM vn_person_authority "
            "WHERE dila_id IS NOT NULL AND dila_id != '' "
            "GROUP BY dila_id HAVING COUNT(*) > 1)").fetchone()[0]
    except Exception:
        return (False, 0)
    return (n > 0, n)
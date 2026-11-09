"""T265 Lô D — import quyết định kiểm tra thủ công từ CSV."""

from flask import Blueprint, jsonify, request

from db_core import get_db_connection

t265_bp = Blueprint('t265', __name__)


@t265_bp.route('/daoanh/api/admin/import_t265_decisions', methods=['POST'])
def import_t265_decisions():
    """
    POST /daoanh/api/admin/import_t265_decisions

    T265 Lô D — Upload CSV mẫu (45 dòng) với quyết định kiem_tra_thu_cong
    → validate + gắn quyết định vào timeline_year_support

    Input: multipart/form-data, file=CSV
    CSV columns: group, dila_id, year, ..., kiem_tra_thu_cong (ĐÚNG/SAI/CẦN_NGUỒN)

    Output JSON: {success, applied, failed, errors[:10]}
    """
    import csv
    import io

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Không có file được upload"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "error": "File phải là .csv"}), 400

    try:
        # Đọc CSV với UTF-8 encoding, skip BOM nếu có
        # Đầu tiên, read toàn bộ file content để tránh vấn đề stream position
        file_content = file.read()
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8-sig')  # utf-8-sig sẽ tự động skip BOM

        stream = io.StringIO(file_content)
        reader = csv.DictReader(stream)
        rows = list(reader)

        # Validate số dòng
        if len(rows) != 45:
            return jsonify({
                "success": False,
                "error": f"CSV phải có 45 dòng dữ liệu, nhận {len(rows)}"
            }), 400

        # Kết nối DB
        conn = get_db_connection()
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        applied = 0
        failed = 0
        errors = []

        # Duyệt từng dòng
        for i, row in enumerate(rows, 1):
            try:
                dila_id = (row.get('dila_id') or '').strip()
                year_str = (row.get('year') or '').strip()
                # Cột trong CSV có tên đầy đủ: 'kiem_tra_thu_cong(DUNG/SAI/CAN_NGUON)'
                decision = (row.get('kiem_tra_thu_cong(DUNG/SAI/CAN_NGUON)') or '').strip()
                note = (row.get('ghi_chu_them') or '').strip()
                reviewer = (row.get('nguoi_duyet') or 'admin').strip()

                # Validate decision
                if decision not in ['ĐÚNG', 'SAI', 'CẦN_NGUỒN']:
                    errors.append(f"Dòng {i}: decision '{decision}' không hợp lệ (phải ĐÚNG/SAI/CẦN_NGUỒN)")
                    failed += 1
                    continue

                if not dila_id:
                    errors.append(f"Dòng {i}: dila_id không được để trống")
                    failed += 1
                    continue

                if not year_str or not year_str.isdigit():
                    errors.append(f"Dòng {i}: year phải là số, nhận '{year_str}'")
                    failed += 1
                    continue

                year = int(year_str)

                # Map decision → status và reason
                if decision == 'ĐÚNG':
                    status = 'era_range'
                    reason = f'Admin xác nhận từ CSV Lô D ({reviewer})'
                else:  # SAI hoặc CẦN_NGUỒN
                    status = 'review'
                    if decision == 'SAI':
                        reason = f'Admin đánh dấu SAI từ CSV Lô D ({reviewer}). Ghi chú: {note}' if note else f'Admin đánh dấu SAI ({reviewer})'
                    else:
                        reason = f'Admin đánh dấu CẦN_NGUỒN từ CSV Lô D ({reviewer}). Ghi chú: {note}' if note else f'Admin đánh dấu CẦN_NGUỒN ({reviewer})'

                # Tìm event_id dựa trên dila_id và year
                event_row = cursor.execute("""
                    SELECT id FROM place_timeline_events
                    WHERE dila_id = ? AND year = ?
                    LIMIT 1
                """, (dila_id, year)).fetchone()

                if not event_row:
                    errors.append(f"Dòng {i}: không tìm thấy event với dila_id='{dila_id}' và year={year}")
                    failed += 1
                    continue

                event_id = event_row[0]

                # Gắn quyết định vào timeline_year_support
                # Nếu đã có, update; nếu chưa, insert
                cursor.execute("""
                    INSERT INTO timeline_year_support
                    (event_id, dila_id, year, status, reason, decided_by, decided_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(event_id) DO UPDATE SET
                        status = excluded.status,
                        reason = excluded.reason,
                        decided_by = excluded.decided_by,
                        decided_at = CURRENT_TIMESTAMP
                """, (event_id, dila_id, year, status, reason, reviewer))

                applied += 1

            except Exception as e:
                errors.append(f"Dòng {i}: {str(e)}")
                failed += 1

        # Commit changes
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "applied": applied,
            "failed": failed,
            "total": 45,
            "errors": errors[:10]  # Giới hạn 10 lỗi đầu
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

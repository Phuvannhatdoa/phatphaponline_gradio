# Audit toàn bộ TTL local

{
  "files_scanned": 1044,
  "rdf_parser_available": true,
  "rdf_valid": 1042,
  "main_records": 1041,
  "edge_assertions": 1245,
  "findings": {
    "IDENTIFIER_DIFFERENT": 101,
    "FILENAME_SUBJECT_DIFFERENT": 80,
    "DILA_UNRESOLVED": 222,
    "EMPTY": 2,
    "MAIN_UNSUPPORTED": 1,
    "MULTIPLE_MAIN": 1,
    "SUBJECT_COLLISION": 4,
    "DILA_NOT_CONFIRMED": 476,
    "GENERATION_NOT_COMPARABLE": 25,
    "ENDPOINT_NO_MAIN_FILE": 25,
    "GENERATION_REVIEW": 26,
    "DIRECTED_CYCLE": 2
  },
  "source_db_changed": false,
  "ttl_changed": false,
  "status": "NEEDS_REVIEW",
  "limitations": [
    "Đối chiếu DILA từ DB local, chưa xác minh web từng người.",
    "Ánh xạ DILA hiện có có thể sai; không tự sửa ID từ tên.",
    "Regex sơ bộ không bảo đảm toàn bộ cú pháp Turtle.",
    "Số đời khác không tự kết luận sai; cần cùng quy ước đếm."
  ]
}

Chi tiết từng phát hiện: findings.jsonl. Index truy vết file/cạnh: index.sqlite.
Không tự sửa quan hệ hoặc số đời khi chưa có bằng chứng.
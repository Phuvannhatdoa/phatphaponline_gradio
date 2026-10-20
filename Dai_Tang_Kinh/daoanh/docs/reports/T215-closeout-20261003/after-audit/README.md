# Audit toàn bộ TTL local

{
  "files_scanned": 1037,
  "rdf_parser_available": true,
  "rdf_valid": 1037,
  "main_records": 1037,
  "edge_assertions": 1238,
  "findings": {
    "IDENTIFIER_DIFFERENT": 101,
    "FILENAME_SUBJECT_DIFFERENT": 77,
    "DILA_UNRESOLVED": 219,
    "DILA_NOT_CONFIRMED": 447,
    "GENERATION_NOT_COMPARABLE": 25,
    "ENDPOINT_NO_MAIN_FILE": 24,
    "GENERATION_REVIEW": 26
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
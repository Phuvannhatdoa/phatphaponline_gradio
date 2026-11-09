# N2 — Khôi phục quyền agent (V1) + test:compliance exit code (V2)

- V1: khôi phục deny `sqlite3 * INSERT/UPDATE/DELETE/DROP*` cho `daoanh-qa.md` (chép từ 776296a0^) và `edit: "*": deny` + `docs/**: allow` cho `tich-hop.md`; thư mục này KHÔNG commit.
- V2: `scripts/verify_design_compliance.py` `main()` thoát `sys.exit(1)` khi `summary.fail_metrics > 0` (sau khi ghi/in output; warn không chặn). Lưu ý: `app.py:15589` coi returncode≠0 là lỗi 500 — cần Admin duyệt riêng để sửa app.py.

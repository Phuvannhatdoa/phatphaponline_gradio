# DEPLOYMENT_SPEC.md — Production Deployment & Live Support (Đạo Ảnh)

> **Conformance-pointer document (T133, 2026-09-14).** Runbook vận hành sản xuất 2-server + monitor + backup + hardening.
> KHÔNG lặp code/DB; mọi module được trỏ tới file nguồn.

## 1. Kiến trúc vận hành (2-server, post-split 2026-05-14)
| Server | File | Port | Vai trò |
|---|---|---|---|
| **Auth Gateway** | `server.py` | **5001** | Login (Gmail check, session, admin emails) |
| **Main Server** | `app.py` | **5000** | Toàn bộ business logic (QA, citation, lineage, translate…) |

- Nginx route: `/daoanh/api/login/*` + `/api/admin/emails` → **:5001**; mọi path còn lại → **:5000**.
- Dev gateway local: `local_gateway.py` **:8080** (proxy; KHÔNG forward `content-length` — BUG-015 lesson).

## 2. Monitor (live support)
- **Query / nhu cầu thiếu dữ liệu**: `data_gap_requests` (OPS_GAP_TABLE, app.py:16474) — status `new` = chưa xử lý; inbox `GET /api/admin/data-gaps`.
- **Feedback user**: `user_feedback` (app.py:16475) — status `new` counter.
- **Dashboard ops**: `dashboard/dashboard_process.html` (regen `python -X utf8 scripts/build_progress_data.py`) — hiện 54 task, 15 module, compliance block, owner task.
- **Compliance Meter**: `/daoanh/api/compliance/dashboard?regenerate=1` (app.py:11624) — 9 metric; chạy định kỳ sau mỗi batch dữ liệu (shuffle `verify_design_compliance.py`, read-only, marker-KPI).

## 3. Go-live runbook
- **Beta**: whitelist admin trên dashboard; public xem khoá QA sau khi market-unit chuẩn.
- **Data Freeze**: `docs/SCHEMA_FREEZE.md` (T82, 137 bảng + 4 view, 0 ALTER/DROP, Expected-Change Registry); checksum baseline `data/checksums.json`.
- **Disaster Recovery / Daily Backup**: `scripts/daily_backup.py` (T116 D-Ops O1) — sqlite `Connection.backup()` online (an toàn khi :5000 đang chạy) → `data/snap/lineage_YYYYMMDD.db.gz` + sha256 + verify gzip/SQLite magic + prune 14 ngày + append `docs/OPS_LOG.md`.

### Cron (VPS, đêm 00:00)
```
0 2 * * * cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh && python scripts/daily_backup.py >> data/backup.log 2>&1
```

## 4. Maintenance
- Chạy lại `verify_design_compliance.py` sau mỗi ETL/batch chính (metric nhạy: claims_with_source / claims_reviewed / conflicts_resolved).
- Chạy lại `npm run pipeline` (lint → test → **test:uat** → compliance → e2e) trước mỗi review (AGENTS §11–12).

## 5. Hardening
- Admin qua :5001 auth gateway (không mở thẳng :5000 admin ra public).
- Public endpoints read-only/low-cost; write layer qua HITL admin.
- Không expose API key (`data/llm_config.json` gitignore'd; Groq/Claude key đọc từ env/config không commit).
- Zero-ALTER/Zero-RAM discipline khi chạy script trên DB sản xuất.

## 6. Feedback loop production
User báo lỗi/bổ sung → `user_feedback`/`data_gap_requests` → inbox admin → resolve/reject → (`translation_error_report` T123 cho lỗi dịch). Append-only `docs/OPS_LOG.md` cho backup/ops event.

## 7. Trách nhiệm
- Build/op: AI Engineer · Giá trị/quyết định: Lee Tổng · Roadmap: TD. Người phụ trách mỗi task: frontmatter `owner:` (dashboard hiện).
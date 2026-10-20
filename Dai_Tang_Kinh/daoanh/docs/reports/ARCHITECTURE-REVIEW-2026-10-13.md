# Architecture Review — Phật Tổ Đạo Ảnh
Codex - GPT reviews
**Ngày:** 2026-10-13  
**Phạm vi:** Review read-only code, docs, SQLite metadata, test/release workflow.  
**Không thực hiện:** sửa code, DB, TTL, production, import hay deploy.

## Kết luận cho Admin

Hệ thống có nền tảng học thuật đúng hướng: raw source, provenance, source cache, TTL, evidence-based lineage và audit/rollback đã xuất hiện ở nhiều mô-đun. Tuy nhiên kiến trúc chưa vận hành như một hệ thống thống nhất theo docs. Code cũ và code mới cùng hoạt động, tài liệu có mâu thuẫn, test/release có thể báo PASS không phản ánh đủ chất lượng, và một số đường ghi dữ liệu/auth/deploy cần được khóa trước khi mở rộng dữ liệu.

Đội dev không nên ưu tiên thêm tính năng mới trước khi hoàn thành Phase 0–1 dưới đây.

## Điểm tốt cần giữ

- T227 có tư duy source cache, hash, quarantine và nguồn gốc dữ liệu.
- T232 có hướng tính số đời theo mốc/chứng cứ, cycle và conflict.
- T357 có fixture test cho transaction, trigger, staging và rollback scoped.
- Handoff/session/manifest giữ lại bằng chứng tốt hơn một nhãn DONE đơn thuần.
- T358 phân biệt Admin review local với thay đổi trạng thái task/production.

## Rủi ro ưu tiên

| Mức | Hiện trạng | Tác động | Việc dev cần làm |
|---|---|---|---|
| P0 | Login có dấu hiệu cấp session từ email nằm trong danh sách admin, chưa có chứng minh sở hữu email. | Có nguy cơ mạo danh admin. | Dùng Google OAuth hoặc email OTP; session expiry/rotation/CSRF/audit log. |
| P0 | Auth cho route ghi không thống nhất; một số API mapping, TTL, ETL generation không có middleware admin toàn cục. | Có thể bỏ sót write endpoint. | Một `require_admin()` bắt buộc cho POST/PUT/DELETE/admin jobs; test quét toàn bộ write routes. |
| P0 | Lint che failure; test placeholder; tester và pipeline kiểm các phạm vi khác nhau. | Có thể release với PASS giả. | Một pipeline chuẩn, failure propagation thật, báo riêng PASS/FAIL/SKIPPED. |
| P0 | Deploy/sync có thể copy trực tiếp SQLite live và restart dù transfer lỗi. | Hỏng DB hoặc chạy service với dữ liệu dở dang. | Tách code/data deploy; SQLite Backup API, upload filename mới, hash + quick_check, atomic swap sau health check. |
| P0 | Shared worktree từng bị orphan checkout làm mất tracked files/WIP. | Mất thay đổi hoặc commit nhầm. | Mỗi task một Git worktree; integration worktree có owner; lock riêng cho deploy/DB write. |
| P1 | `app.py` rất lớn và chứa hầu hết nghiệp vụ; legacy/new APIs chạy song song. | Khó test, review auth và thay thế an toàn. | Tách dần service Authority, Sources, TTL, Lineage, Generation, Translation, Admin Review; giữ adapter API cũ. |
| P1 | Generation script cũ dùng offset cố định `+37`, có DROP/rebuild; song song T232 evidence-based. | Có thể trái chính sách số đời có chứng cứ. | T232 là engine duy nhất; T275 chỉ cung cấp anchor có scheme/evidence; vô hiệu hóa đường offset cũ. |
| P1 | Loader DILA có đoạn nạp toàn bộ XML vào RAM, không lọc completed run/latest hash. | Trái Zero-RAM, có thể lấy nhầm version. | Lazy load theo ID và source run/version/hash; cache giới hạn. |
| P1 | Backup/revert có chỗ dùng copy file SQLite trong WAL; rollback không guard đủ chỉnh sửa admin sau import. | Có thể mất WAL hoặc ghi đè edit sau đó. | SQLite Backup API + row/hash/CAS guarded rollback; whole-DB restore chỉ disaster recovery. |
| P1 | Local gateway phục vụ mọi file; VPS có thể chặn JSON mà Dashboard cần. | Rò rỉ config/DB hoặc Dashboard không tải report. | Static allowlist; deny DB/log/backup/.env; public manifest JSON qua route rõ ràng. |
| P1 | Dashboard đo inventory/file/route, chưa đo accepted behavior. | Admin có thể hiểu sai phần trăm tiến độ. | Tách Implemented, Automated QA, Independent QA, Admin accepted, Deployed version, Evidence freshness. |

## Kiến trúc dữ liệu cần chốt

```text
RAW
  XML gốc / TTL gốc / CBETA gốc
  immutable + hash + license + source locator
        ↓
STAGING
  sidecar JSON / parse result / candidate claims
  versioned + run manifest + quarantine
        ↓
CURATION
  review queue / mapping decision / evidence link
  human-approved hoặc rejected
        ↓
FINAL
  authority / lineage / public API projection
  chỉ nhận dữ liệu đã qua policy và audit
```

Mỗi chuyển tầng phải lưu input hash, code version, run ID, accepted/rejected/quarantined counts, reviewer/rule, timestamp, schema version và rollback manifest.

## Lộ trình đề nghị

### Phase 0 — Khóa hiện trạng

1. Xác định DB production/path/WAL/source run đang được server sử dụng.
2. Sinh production manifest: commit, DB hash, schema version, T227 run, T366 sidecar version.
3. Inventory toàn bộ write routes và scripts có mutation.
4. Quarantine legacy write paths chưa có auth/provenance/rollback đầy đủ.

**Nghiệm thu:** Admin có trang Current Production Manifest; không còn suy đoán DB nào đang chạy.

### Phase 1 — Bảo vệ truy cập và write paths

1. OAuth hoặc email OTP.
2. Middleware admin mặc định cho write/admin jobs.
3. Audit log mutation.
4. Static gateway allowlist.
5. Khóa endpoint generation offset cũ.

**Nghiệm thu:** write route có auth test; DB/backup không public qua gateway.

### Phase 2 — Data contract và migration

1. Migration ledger; không DDL/ALTER khi import app.
2. Connection read-only/read-write riêng; bật foreign keys.
3. Backup SQLite API, rollback scoped.
4. Sidecar ghi atomic, versioned manifest.
5. Source assertions/candidate claims/accepted facts schema.

### Phase 3 — Tách dần monolith

Tách Authority, Source Registry, TTL, Lineage, Generation, Translation và Admin Review thành service/repository. `app.py` chỉ giữ controller/adapters.

### Phase 4 — Một engine số đời

T232 là engine duy nhất. Phân biệt thầy truyền pháp, thầy giới, generic teacher và đồng môn. Mọi số đời phải nêu scheme, anchor, path và evidence; trạng thái `source_asserted`, `computed`, `candidate`, `rejected` tách riêng.

### Phase 5 — Release và Dashboard thật

Một pipeline cho local/CI/deploy; deploy artifact có commit/hash/report; health phải gọi API thật; Dashboard chỉ báo PASS nếu có evidence + timestamp.

## Mâu thuẫn docs cần xử lý

- `SCHEMA.md` có hướng ALTER/DROP trong khi curation/freeze yêu cầu draft → mapping → audit → human approval.
- `HYBRID_DATA_ARCHITECTURE` có invariant RAW/STAGING/FINAL chưa mô tả đúng sidecar và quyết định local `name_vi`.
- `HARNESS_WORKFLOW` và `SUBAGENT-WORKFLOW` dùng vai trò/DONE semantics khác nhau.
- Một số task/dashboard snapshot ghi trạng thái lịch sử như trạng thái hiện hành.

### Governance contract cần bổ sung

1. Một **write matrix**: mỗi artifact/bảng/field phải nêu layer, reader, writer, thao tác hợp lệ, approval, migration và rollback.
2. Sidecar là projection versioned của một RAW snapshot, không mặc định là FINAL. Curation local phải được preserve riêng, có evidence và review state.
3. Tên, `place_key`, QID hoặc geo chỉ tạo candidate mapping; không tự động chứng minh identity/crosswalk.
4. Một workflow agent duy nhất với bốn trạng thái khác nhau: `implementation_complete`, `independent_qa`, `admin_closed`, `production_applied`.
5. Một task một current-state machine-readable; lịch sử giữ lại nhưng phải được gắn nhãn historical.
6. Mọi số liệu ghi trong docs phải có nhãn `measured`, `estimated` hoặc `target`, cùng ngày, dataset version, command và denominator.

## Quyết định Admin cần chốt

1. OAuth hay email OTP cho admin login?
2. DB/path production chính thức?
3. Có khóa endpoint generation `+37` trước khi T232 thay thế không?
4. Code deploy và data deploy có tách bắt buộc không?
5. Có chấp nhận lifecycle chung: Draft → Staging → Review → Accepted → Published → Reverted không?

## Evidence chính

- `server.py:106-121` — session issuance.
- `app.py:11507-11536, 24747, 24786` — write/admin routes cần rà bảo vệ.
- `scripts/etl_gen_compute.py:17-18, 170, 416-418` — generation legacy offset/drop.
- `app.py:5717-5734` — DILA XML loader.
- `package.json:12,35`; `scripts/tester-agent.mjs`; `tests/run-tests.js` — test gate.
- `sync_to_vps.ps1:68-106`; `.github/workflows/deploy.yml` — deploy/data risks.
- `local_gateway.py:68-88`; `deploy/nginx.conf:48-52` — file serving/data JSON contract.
- `docs/Handoff-2026-10-13-housekeeping.md` — shared worktree failure evidence.

## Giới hạn review

Các facts được thu từ code/docs và SQLite read-only. Không import `app.py`, không chạy production server/ETL/migration, không kiểm chứng trực tiếp VPS hoặc authentication live. Vì vậy các phát hiện route/auth/deploy là source-level findings cần đội dev tái hiện bằng environment staging trước khi thay đổi production.

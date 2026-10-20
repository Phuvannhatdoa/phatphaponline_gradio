# DASH_CONSOLIDATED · Dashboard Phật Giáo (CONSOLIDATED — Evidence-Based)

**Spec · P2** (Consolidated from archived M70, M99 per T277 Phase A)

## Mục đích (Consolidated — Evidence-Based)

Hệ thống **dashboard hiển thị số liệu thật từ DB** — không analytics AI, không "abbot dashboard", không "integrated 2.0", không widget kéo-thả, không "meditation tracker", không "retreat schedule", không "breakthrough insight".

Chỉ thực hiện: (1) dashboard_process.html (tiến độ code/docs), (2) admin/editor-dashboard.html (editor review), (3) progress tracking từ `build_progress_data.py`.

## Thực tế hiện có (2026-10-11)

| Dashboard | Trạng thái | File | Chức năng thực tế |
|---|---|---|---|
| `dashboard_process.html` | **Đã có** | `dashboard/dashboard_process.html` | Tiến độ module/code/task từ `build_progress_data.py` |
| Admin Editor Dashboard | **Đã có** | `admin/editor-dashboard.html` | Duyệt claims/unverified, bulk review, history |
| Bio Review | **Đã có** | `admin/bio-review.html` | Duyệt tiểu sử AI dịch |
| Geo Enrichment | **Đã có** | `admin/web_enrichments.html` | Duyệt gợi ý GPS |
| TTL Queue | **Đã có** | `admin/ttl_queue.html` | Hàng đợi TTL |
| Translation Monitor | **Đã có** | `admin/translation_monitor.html` | Theo dõi dịch thuật |

**Không có:** "Abbot dashboard", "Integrated 2.0", widget kéo-thả, "meditation tracker", "retreat schedule", "breakthrough insight", "analytics cho nhà giáo", "user analytics", "meditation tracker".

## Thống kê thực tế (2026-10-11)

| Dashboard | Chỉ số hiển thị | Nguồn dữ liệu |
|---|---|---|
| `dashboard_process.html` | 15 module, 314 endpoint, 72% tiến độ, 275 task | `build_progress_data.py` |
| Admin Editor | 6 tab: unverified, conflicts, bio-review, geo-enrich, stats, history | `person_groq_audit`, `place_groq_audit`, `bio_review` |
| Bio Review | Claims chờ duyệt tiểu sử | `bio_review` queue |
| Geo Enrichment | Gợi ý GPS chờ duyệt | `geo_cross_ref` queue |

## Chỉ giữ: Dashboard hiển thị số liệu thật từ DB

| Dashboard | Chức năng | Nguồn dữ liệu |
|---|---|---|
| `dashboard/dashboard_process.html` | Tiến độ module/code/task/git | `build_progress_data.py` (scan docs + code) |
| `admin/editor-dashboard.html` | Duyệt claims/unverified/conflicts | `person_groq_audit`, `place_groq_audit` |
| `admin/bio-review.html` | Duyệt tiểu sử | `bio_review` queue |
| `admin/web_enrichments.html` | Duyệt gợi ý GPS | `geo_cross_ref` |

**Không có:** "Abott dashboard", "Integrated 2.0", widget kéo-thả, "meditation tracker", "retreat schedule", "breakthrough insight", "analytics cho nhà giáo", "user behavior analytics", "meditation tracker", "retreat management".

## Chỉ giữ: Dashboard hiển thị số liệu thật từ DB

1. **`dashboard_process.html`** — Tiến độ module/code/task/git từ `build_progress_data.py`
2. **`admin/editor-dashboard.html`** — 6 tab duyệt dữ liệu (unverified, conflicts, bio-review, geo-enrich, stats, history)
3. **Admin sub-dashboards** — bio-review, geo-enrich, ttl-queue, translation-monitor

**Không có:** "Abott dashboard", "Integrated 2.0", widget kéo-thả, custom layout, "meditation tracker", "retreat schedule", "breakthrough insight", "analytics cho nhà giáo", "user analytics".

## Thống kê thực tế (2026-10-11)

| Dashboard | Chỉ số | Nguồn |
|---|---|---|
| `dashboard_process.html` | 15 module, 314 endpoint, 72% tiến độ, 275 task | `build_progress_data.py` |
| `person_groq_audit` | ~0 rows (chưa migrate) | side-car table |
| `place_groq_audit` | ~0 rows (chưa migrate) | side-car table |
| Bio review queue | TBD | `bio_review` |

## Chỉ giữ: Dashboard hiển thị số liệu thật từ DB

1. **`dashboard_process.html`** — Tiến độ module/code/task/git (chạy `build_progress_data.py`)
2. **`admin/editor-dashboard.html`** — 6 tab duyệt dữ liệu từ side-car tables
4. **Admin sub-dashboards** — bio-review, geo-enrich, ttl-queue, translation-monitor

**Không có:** Custom widget, drag-drop layout, "meditation tracker", "retreat schedule", "breakthrough insight", "abbot analytics", "user behavior analytics".

## Acceptance Criteria (Evidence-Based)

- [x] `dashboard_process.html` hiển thị tiến độ từ `build_progress_data.py`
- [x] `admin/editor-dashboard.html` 6 tab duyệt dữ liệu side-car
- [x] Admin sub-dashboards hoạt động
- [ ] Không có AI analytics/widget kéo-thả/speculative features

## Loại bỏ (Archived Speculative Claims)

| Claim gốc (M70/M99) | Lý do loại bỏ |
|---|---|
| "Abott dashboard" | Không có role "abbot" trong hệ thống |
| "Integrated 2.0" | Không có v2, chỉ có dashboards hiện có |
| Widget kéo-thả/custom layout | Không có widget system |
| "Meditation tracker" | Không có meditation tracking |
| "Retreat schedule" | Không có retreat management |
| "Breakthrough insight" | Không có insight detection |
| "Analytics cho nhà giáo" | Không có role "nhà giáo", không có analytics |
| "User behavior analytics" | Không có user tracking |
| "Meditation tracker/retreat management" | Không có meditation/retreat system |
| "Integrated 2.0 layout tùy chỉnh" | Không có layout engine |

## Thực thể code hiện có (2026-10-11)

| File | Mô tả |
|---|---|
| `dashboard/dashboard_process.html` | Progress tracking dashboard |
| `dashboard/plan.md`, `handoff.md`, `tasks.md` | Dashboard docs |
| `admin/editor-dashboard.html` | Editor dashboard (6 tab) |
| `admin/bio-review.html` | Bio review queue |
| `admin/web_enrichments.html` | Geo enrichment queue |
| `admin/ttl_queue.html` | TTL queue |
| `admin/translation_monitor.html` | Translation monitoring |
| `scripts/build_progress_data.py` | Generator progress_data.json |

## File liên quan

- Task gốc: `docs/integration/_archive/M-series/M70-analytics-dashboard.md`, `M99-integrated-dharma-dashboard.md` (archived)
- Task T277: `tasks/T277-archive-and-future-integration.md` (Phase A)
- Code: `dashboard/dashboard_process.html`, `admin/editor-dashboard.html`, `scripts/build_progress_data.py`
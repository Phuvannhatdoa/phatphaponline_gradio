# T130 + T131 — INTEGRATION AUDIT REPORT (read-only, 2026-09-18)

> **Loại:** Audit tích hợp (read-only) — KHÔNG code, KHÔNG ALTER, KHÔNG chạm file Admin WIP.
> **Lệnh SSOT tham chiếu:** audit `docs/tasktodo.md` rows T130/T131 → audit code `places.html`/`app.py` → đối chiếu từng marker → kết luận gap + conflict → **BLOCKED nếu chạm Admin WIP**.
> **Người duyệt:** Lee (Admin). Trạng thái: **REPORTED — chờ Lee quyết (build ngay sau Admin commit WIP, hoặc build trước lên bản snapshot riêng).**
> **Date:** 2026-09-18 · **Agent:** opencode (build) · **Commit:** docs-only preview (xem `docs/taskdone.md` nếu đã lưu).

---

## 1. Kết luận nhanh

| Mục | Kết quả |
|---|---|
| T130 (Pháp Mạch trực hệ — chain 1 nhánh) | **GAP thật + CONFLICT (file)** |
| T131 (B21 Source Governance) | **~70% đã có Build 3 (T77/T78/T82) + 5 GAP code còn lại + CONFLICT (file)** |
| Block | **CẢ HAI đều cần sửa `app.py` + `places.html` = ĐANG LÀ Admin WIP (mtime 2026-09-18 07:42, editor card DILA multi-field)** |
| Hành động | **KHÔNG code. Báo cáo. Chờ Lee quyết.** |

---

## 2. Bằng chứng audit (đọc thật từ repo)

### 2.1 T130 — markers Pháp Mạch trong `places.html`

| Marker | Số lần | Ý nghĩa |
|---|---|---|
| `?expand=` (deep-link) | **0** | CHƯA có → T130 gap chính (deep-link lazy expand) |
| `_buildPrimaryChain` | **0** | CHƯA có → T130 chain builder chưa implement |
| `chooseSibling` / `lineageChooser` | **0** | CHƯA có → chooser chưa implement |
| `lineage-filter-tl1` | 2 | CÓ (id + JS) — filter tầng đã có từ T127 |
| `lineage-filter-tl2` | 2 | CÓ |
| `lineage-filter-tl3` | 2 | CÓ |
| `lineage-filter-verified` | 1 | CÓ — hộp verified cũ, T130 cần chuyển thành chooser |
| `_ftFullExpanded` | 3 | CÓ (legacy T127) — T130 **cấm dùng** trong chain |
| `_ov__` (sibling overflow) | 4 | CÓ (legacy T127) — T130 **cấm** dùng trong chain |
| `?chain=` / `?focus=` / `?mode=lineage` | 0 | CHƯA — deep-link form T130 chưa có |
| `_renderHierarchyShared` / `_renderLineageChain` | 0 | CHƯA — shared renderer T130 chưa có |

→ **Khớp đúng mô tả SSOT T130:** hiện có backbone T127 (expand/filter) nhưng thiếu hoàn toàn phần **primary chain trực hệ + icon +/− + chooser + deep-link** = phần lõi T130.

### 2.2 T131 — Source Governance trong `places.html` + `app.py`

| Marker | places.html | app.py | Ghi chú |
|---|---|---|---|
| `gate/` (LicenseGate/ProvenanceGate/LegalStatus) | 0 | 1 | **KHÔNG có** logic gate nội tuyến — đúng, vì T131 nói reuse `gate/` package |
| `data_sources` | 0 | 12 | CÓ registry |
| `source_authority` | 0 | 10 | CÓ |
| `source_registry` | 0 | 0 | ⚠️ Tên cột `source_registry` CHƯA thấy — xem lại tên thật |
| `source_authority` | 0 | 10 | CÓ |
| `dataset_sources` | 0 | 1 | CÓ |
| `provenance` | 4 | 8 | CÓ |
| `LicenseGate` | 0 | 1 | CÓ (import) — governance gate đã import |
| `authority_score` | 0 | 0 | ⚠️ xem cột tương đương |
| `license_verified` | 0 | 1 | CÓ |
| `usage_level` | 0 | 4 | CÓ |
| `restrictions` | 0 | 0 | ⚠️ gap (T131 yêu cầu) |
| `data_sources` registry rows | — | registry 40+ cột (13 rows) | SSOT: 13/25 active |

→ Đúng tinh thần T131 SSOT: **~70% đã có sẵn** (registry data_sources + gate/ package + source_authority). 5 GAP SSOT nêu (CONTENT_READ/DERIVED/EXPORT ops, registry 13/25, adapter methods, tests, usage_level col) — **chưa implement → vẫn còn nguyên**.

### 2.3 Conflict — file chạm

Cả T130 lẫn T131 khi implement sâu đều sửa `app.py` (đuôi: `?expand=`, chooser endpoint, gate ops, registry rows) + `places.html` (chain renderer, busbar, icon overlay, badges).

**Cả hai file hiện thuộc Admin WIP** (git status ` M` cả 2):
- `app.py` — mtime 2026-09-18 07:42
- `places.html` — mtime 2026-09-18 07:42
- (kèm `admin/person.html`, backup `docs/sessions/2026-09-17/`)

Theo **Rule §Rule "Không đụng file Admin WIP"** + AGENTS §Lưu ý trang "Admin WIP — DO NOT TOUCH": tôi **không được** tự ý sửa, commit hoặc merge lên 2 file đó khi Admin chưa commit.

---

## 3. Quyết định đề xuất gửi Lee (chọn 1)

**Lựa chọn A (khuyến nghị — an toàn nhất):**
Admin **commit WIP hiện tại trước** (`app.py` + `admin/person.html` + `places.html` hoặc ít nhất `app.py`/`places.html`).
=> tôi implement T130 + T131 **additive, 0 ALTER** ngay trên HEAD sạch, tạo ROLLBACK row, QA + commit. Không đụng admin WIP.

**Lựa chọn B (build song song — rủi ro merge):**
Tôi implement trên bản snapshot riêng (`app.py.bak-t130/131.py`, `places.html.bak-t130/131`) → commit riêng → **Admin tự merge khi sẵn sàng**. Tránh chạm file Admin nhưng tạo thêm phức tạp merge manual.

**Lựa chọn C (hoãn):**
Tạm dừng T130/T131, đợi Admin WIP commit xong rồi mới bắt đầu.

---

## 4. Files/API/DB sẽ được chạm khi implement (plan additive, 0 destructive)

- `Dai_Tang_Kinh/daoanh/places.html` — chain renderer `_renderPrimaryChain`, icon +/− overlay DOM, chooser popover, busbar, deep-link `?expand=`/`?chain=`/`?focus=` (pushState)
- `Dai_Tang_Kinh/daoanh/app.py` — endpoint `?expand=<id>&dir=up|down` (additive), gate ops CONTENT_READ/DERIVED_DATA/EXPORT/METADATA_READ, registry 13→25 (INSERT OR IGNORE, `license_verified=0`), adapter methods (additive)
- `Dai_Tang_Kinh/daoanh/data/*.db` — **0 ALTER / 0 DROP** (thêm rows INSERT OR IGNORE thuần registry)
- KHÔNG sửa: schema definitions bất biến, canonical IDs (A0xxxxx), data_sources 2 registry (T131) KHÔNG mở rộng dataset_sources

## 5. Không làm trong task này
- KHÔNG sửa `app.py`/`places.html`/`admin/person.html` cho đến khi Lee quyết + Admin WIP đã đóng
- KHÔNG tái lật chiều DILA (đã fix T157 — `lineage_edge_assertions` canonical)
- KHÔNG rewrite tree design T127/T128/T129
- KHÔNG auto cấp `source_authority`/`name_vi` mới

---

## 6. BLOCKER

```
FILE-CONFLICT: app.py + places.html = Admin WIP pending (2026-09-18 07:42 DILA multi-field card editor)
```

→ **STOP-POINT đạt theo SSOT.** Báo cáo này ghi lại, không có commit code nào trong phiên này (chỉ docs).

*— hết báo cáo —*

---

## ✅ QUYẾT ĐỊNH LEE (2026-09-18) — ĐÃ CHỌN **Lựa chọn A** + **đồng ý build**

> Lee: *"Đồng ý build, hãy lưu logs, git commit và update các thông tin của các task mới vào các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện."*

**→ Lee chọn A — Admin commit WIP trước (app.py + places.html + admin/person.html + app_local.err + backup docs/sessions/2026-09-17/), sau đó tôi build T130+T131 additive trên HEAD sạch.**

**Hiện trạng (turn này):**
- **CHỜ Lee commit WIP** — không code, không ALTER, không chạm 2 file Admin WIP.
- Docs đã lưu: audit report này + update row T130/T131 trong `docs/tasktodo.md`.
- Sau khi Lee commit WIP xong → BÁO tên commit → tôi implement T130+T131 additive (0 destructive) → QA → commit → dashboard regen.

### 🔧 Plan build T130+T131 (additive, 0 destructive, 1 lần duy nhất)

**T130 — Pháp Mạch = trực hệ (primary chain, 1 nhánh):**
- `places.html`: `_buildPrimaryChain` (1 primary → depth-first unique-chain; **CẤM** `_ftFullExpanded`/`_ov__` trong chain) + icon `+/−` (DOM button overlay, 28px, aria, stopPropagation) + chooser sibling (`chooseSibling`/`lineageChooser` verified + CTA "Phả hệ mở rộng") + routing filter tl1/tl2/tl3 shared + deep-link `?expand=<id>&?dir=up|down` (pushState, popstate).
- `app.py`: endpoint `?expand=` lazy 1-tầng additive + gate ops + chooser.

**T131 — Source Governance refine (~70% đã có Build 3):**
- gate/package: CONTENT_READ/DERIVED_DATA/EXPORT/METADATA_READ ops + result `usage_level`/`restrictions[]` (additive).
- registry data_sources 13→13 (INSERT OR IGNORE, license_verified=0) + adapter methods (get_metadata/get_entity/get_evidence/get_source_version).
- tests §13 A–L + pytest pipeline + usage_level column (additive).

**Rollback:** ROLLBACK row + git revert/checkout convenience (Lee yêu cầu commit back thuận tiện).


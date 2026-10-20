---
id: T169
title: "Robust Batch Verification Pipeline (Groq Qwen vs SQLite từ điển) — Thẩm định địa danh DILA"
module: Editorial / LLM Translation
priority: high
status: ready-for-dev
owner: claudecode
depends_on: []
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: Đồng ý build · Chốt phương án A side-car + sync 2 bảng khi edit)"
done_when: |
  Script scripts/verify_dila_places_groq.py chạy batch 25 trên data/lineage.db thật;
  side-car place_groq_audit --apply/--revert có backup; classify_diff đúng 3 fixture
  (降魔窟=POLYPHONIC · 白馬寺=TAXONOMY · 少林寺=NONE); flush batch dư cuối;
  API GET/PUT place-groq-review + UI place_update.html 2 cột dict vs Qwen + filter TOP;
  Admin edit đồng bộ places_pending.name_vi + namevi_map_places.name_vi cùng transaction;
  schema log batch0 + token usage thực tế; npm run pipeline PASS; revert = DROP side-car + git revert.
---

# T169 — Thẩm Định Địa Danh Groq Qwen vs SQLite Từ Điển (SPEC bàn giao dev)

> **Directive gốc:** Admin “THẨM ĐỊNH ĐỊA DANH GROQ VS SQLITE — ROBUST BATCH VERIFICATION PIPELINE”
> **Review 2026-09-25:** đối chiếu DB thật `data/lineage.db` (RO) → **6 P0 + 9 P1** (§2–§3).
> **Admin chốt:** **(A)** side-car table · **(2)** edit sync 2 bảng · tạo file `.md` này (docs-only, chưa code).

---

## 0. Quyết định Admin (locked)

| # | Quyết định |
|---|------------|
| **A** | Không ALTER bảng lớn chung → bảng side-car **`place_groq_audit`** (PK = `places_dila.id`). Revert = `DROP TABLE` 1 dòng. |
| **2** | Khi Admin sửa/sửa lại trên UI: ghi **`places_pending.name_vi`** + **đồng bộ `namevi_map_places.name_vi`** trong **cùng 1 transaction** (không chỉ 1 bảng). |

---

## 1. OUT OF SCOPE

- Không đụng `people` / lineage / Glossary T165.
- Không gọi LLM cho `id IS NULL` (xem §2.2).
- Không hard-gate TPM theo ước đoán — chỉ **measure** (pattern T165 §log usage).
- Phase XML/Trie không thuộc task này.

---

## 2. P0 — Directive gốc SAI với repo/DB thật (phải sửa trước khi build)

| # | Directive ghi | Sự thật (verify 2026-09-25) | Sửa thành |
|---|---------------|------------------------------|-----------|
| **P0-1** | `DB_PATH = "data/database.sqlite"` | **File không tồn tại** | `data/lineage.db` (đọc RO khi audit; RW khi apply) |
| **P0-2** | Bảng `dila_places` | **0 row metadata** — không có bảng này | Spine **`places_dila`** (59.167) · dict VI = JOIN **`places_pending`** |
| **P0-3** | Cột `trans_dict_vi` | **Không tồn tại bảng nào** | Từ điển = `places_pending.name_vi` (118.304 row có zh+vi) |
| **P0-4** | `UPDATE … WHERE id=?` mù quáng | **58.455/176.783** row `places_pending.id` = NULL/rỗng | Chỉ xử lý `places_dila.id` (long id ổn định) · JOIN pending `ON d.id=p.id` · **bắt buộc** `WHERE id IS NOT NULL` |
| **P0-5** | ~57.000 ID · ~2.300 request | Scope full pending = **118.304 → 4.733 batch** (vượt budget) | Scope **DILA spine** ≈59.150 → **~2.367 batch** (khớp budget) |
| **P0-6** | `GROQ_API_KEY` chỉ từ env | Repo pattern: `data/llm_config.json` → env (xem `t50.resolve_groq_key`) | `resolve_groq_key()`: env → `llm_config.json.groq_key` → abort tiếng Việt nếu trống |

### 2.1 Bảng thật (không bịa)

- `places_dila` · 59.167 · cột: `id, name, name_zh, …, raw_xml, source_id` · id mẫu `PL000000000001`
- `places_pending` · 176.783 · có `name_zh, name_vi, name_vi_norm` · **không** có review/diff cols
- Join id thật: `places_pending.id = places_dila.id` → **59.167**
- `namevi_map_places` · 118.296 · **đã có** `needs_review` (18.165 =1) — bảng sync đích

### 2.2 Scope batch

```sql
SELECT d.id, d.name_zh, p.name_vi AS dict_vi
FROM places_dila d
JOIN places_pending p ON p.id = d.id
WHERE d.id IS NOT NULL AND d.id != ''
  AND d.name_zh IS NOT NULL AND d.name_zh != ''
  AND (d.id NOT IN (SELECT id FROM place_groq_audit WHERE review_status IN ('verified','conflict','approved_dict'))
       OR :force);
```

Ước: **~59.150 → 2.367 batch × 25** · sleep 2s → ~80 phút · dưới 30 RPM free tier.

---

## 3. P1 — Sửa logic pipeline (9 điểm)

| # | Vấn đề | Fix (bắt buộc) |
|---|--------|----------------|
| **1** | `classify_diff` POLYPHONIC: `len(matched_readings)>=1` → false positive (1 reading xuất hiện 1 bên cũng ăn nhãn) | Chỉ POLYPHONIC khi **reading 2 bên KHÁC nhau**: `R_d = readings∩norm_dict`, `R_g = readings∩norm_groq` → `(R_d or R_g) and (R_d != R_g)` hoặc 1 bên rỗng reading ≥1 |
| **2** | TAXONOMY `w1 in text` substring → `('am','thất')` match “tam”; cặp nest `viện/tự viện` | Match **word-boundary** (`\b…\b`, unicode) · bỏ cặp nest `('viện','tự viện')` |
| **3** | Chỉ flush `len(batch)>=25` → **batch dư cuối mất** | Sau vòng lặp: `if batch: process_batch(batch)` |
| **4** | Enum có `api_error` nhưng không bao giờ ghi | Batch call fail cuối retry → ghi item `review_status='api_error'` · model bỏ sót id → giữ `pending` |
| **5** | Query duyệt dùng `'approved_dict'` ngoài enum | **Giữ** `'approved_dict'` + bổ sung enum: `pending, verified, conflict, api_error, approved_dict` |
| **6** | `response_format:json_object` chưa verify với `qwen/qwen3.8-27b` | Thử có → HTTP 400/422 thì **bỏ** response_format · vẫn giữ `safe_parse_json_content` (fence strip) |
| **7** | TPM lifetime-avg ≠ cửa sổ 60s | In thêm **window tokens/60s** so với 6.000 TPM |
| **8** | First-batch schema log + atomic `with conn` + 429 backoff | **GIỮ nguyên** (đúng yêu cầu directive) |
| **9** | Test acceptance 3 case | Dựng `tests/test_t169_classify_diff.py` **trước** chạy VPS |

**Fixture bắt buộc (unit test):**

| name_zh | dict_vi | groq_vi | Expected |
|---------|---------|---------|----------|
| 降魔窟 | Giáng Ma Quật | Hàng Ma Quật | `POLYPHONIC_CHAR` |
| 白馬寺 | Bạch Mã Tự | Chùa Bạch Mã | `TAXONOMY_VARIANT` |
| 少林寺 | Thiếu Lâm Tự | Thiếu Lâm Tự | `NONE` + `verified` |

---

## 4. SCHEMA — side-car (additive, pattern T165 migrate)

```sql
-- scripts/t169_place_groq_audit_migrate.py (--stats/--dry-run/--apply/--revert)
CREATE TABLE IF NOT EXISTS place_groq_audit (
  id             TEXT PRIMARY KEY,          -- = places_dila.id (PL long)
  name_zh        TEXT,
  dict_vi        TEXT,                      -- snapshot places_pending.name_vi lúc check
  groq_trans_vi  TEXT,
  needs_review   INTEGER DEFAULT 0,
  review_status  TEXT DEFAULT 'pending',    -- pending|verified|conflict|api_error|approved_dict
  diff_type      TEXT,                      -- NONE|POLYPHONIC_CHAR|TAXONOMY_VARIANT|PHONETIC_MISMATCH
  diff_reason    TEXT,
  model_id       TEXT,
  batch_id       TEXT,
  prompt_tokens  INTEGER,
  completion_tokens INTEGER,
  checked_at     TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pga_review ON place_groq_audit(needs_review, review_status);
CREATE INDEX IF NOT EXISTS idx_pga_diff   ON place_groq_audit(diff_type);
```

- Backup trước `--apply`: `data/backups/lineage_t169_<ts>.db` (Zero-RAM sqlite backup API).
- `--revert`: `DROP TABLE place_groq_audit` + 2 index (IF EXISTS).

---

## 5. SCRIPT — `scripts/verify_dila_places_groq.py`

Giữ khung directive (batch 25 · sleep 2 · retry 429 · `safe_parse_json_content` · atomic `with conn` · schema inspection log batch 0 · usage token) + P0/P1:

1. `DB_PATH = data/lineage.db` · `resolve_groq_key()` (env → llm_config) · model default `qwen/qwen3.8-27b`.
2. SELECT theo §2.2 (iterator, không load toàn table khi avoid được — batch theo `id > last` resume).
3. System prompt học thuật Phật giáo + bảng đa âm (giữ directive) — **cấm** hard-gate token.
4. `classify_diff` đã fix §3.1–2.
5. Ghi `place_groq_audit` UPSERT (không đụng `places_pending`/`namevi_map_places` — chỉ pipeline verify).
6. Resume: skip row đã `verified/conflict/approved_dict` (trừ `--force`).
7. Cuối run: in thống kê `diff_type` + totals tokens + avg RPM thực tế.

**Log:** stdout UTF-8 + `docs/sessions/<date>_t169-run.md` khi chạy VPS thật (Tasktodo/Session protocol).

---

## 6. API (admin auth — pattern `require_admin` hiện có)

| Method | Endpoint | Việc |
|--------|----------|------|
| GET | `/daoanh/api/admin/place-groq-review?diff=POLYPHONIC_CHAR&status=conflict&limit=100&offset=0` | List ưu tiên: sort `CASE diff_type WHEN 'POLYPHONIC_CHAR' THEN 0 WHEN 'TAXONOMY_VARIANT' THEN 1 WHEN 'PHONETIC_MISMATCH' THEN 2 ELSE 3 END` |
| PUT | `/daoanh/api/admin/place-groq-review/<id>` | Body `{chosen: 'dict'\|'groq'\|'manual', name_vi?}` → **1 transaction**: UPDATE `place_groq_audit` (status=`verified` hoặc `approved_dict`) + UPDATE `places_pending.name_vi` + UPDATE `namevi_map_places.name_vi` (WHERE `dila_id`=id, UPSERT nếu thiếu row) |

---

## 7. UI — `admin/place_update.html` (rewrite presentation, giữ React CDN + Tailwind dark/amber)

| Cột | Nguồn |
|-----|--------|
| ID · Hán | `place_groq_audit.id` + `name_zh` |
| **Phiên âm (từ điển)** | `dict_vi` (live từ pending) |
| **LLM Qwen3.8-27b** | `groq_trans_vi` |
| Badge | POLYPHONIC 🔴 · TAXONOMY 🟠 · PHONETIC 🟡 · NONE 🟢 · status |
| Action | Radio dict/groq + input sửa tay → PUT §6 |

- **Filter mặc định:** `needs_review=1` sort POLYPHONIC → TAXONOMY → PHONETIC (TOP review trước).
- Nút đếm theo filter · Load more (giữ pattern offset hiện tại).
- Endpoint cũ `places_missing_info` **giữ nguyên** cho trang khác (không xóa route).

---

## 8. ACCEPTANCE (done_when)

| # | Tiêu chí |
|---|----------|
| 1 | Batch 0 in `[Schema Inspection…]` + parse JSON OK (fence hoặc raw) |
| 2 | Terminal hiện `prompt_tokens/completion_tokens` lấy từ `usage` + window 60s |
| 3 | 3 fixture §3.9 đúng nhãn · `tests/test_t169_classify_diff.py` PASS |
| 4 | Ctrl+C giữa chừng: batch đã commit giữ nguyên · batch dở rollback · re-run resume từ `pending` |
| 5 | Batch dư cuối (n%25 ≠ 0) **vẫn được xử lý** |
| 6 | UI: 2 cột phiên âm vs Qwen · filter TOP POLYPHONIC · edit → 2 bảng `name_vi` sync + audit verified |
| 7 | `npm run pipeline` PASS · `py_compile` script OK |
| 8 | Revert: `scripts/t169_place_groq_audit_migrate.py --revert` + `git revert <sha>` |

---

## 9. PHASES

| Phase | Việc | Output |
|-------|------|--------|
| 1 | Migrate script side-car `--stats/--dry-run/--apply/--revert` | table + backup path |
| 2 | `classify_diff` + unit test 3 fixture | test PASS |
| 3 | `verify_dila_places_groq.py` (P0 path/key/scope + P1 fixes) | smoke 1 batch 25 thật |
| 4 | API GET/PUT place-groq-review | curl smoke |
| 5 | UI `place_update.html` rewrite | admin smoke |
| 6 | `npm run pipeline` | PASS |

**Commit (toplevel visjs-app):** `feat: T169 place groq audit pipeline + docs`  
**Session:** `docs/sessions/2026-09-25_t169-groq-place-verify-plan.md`  
**Revert:** `git revert --no-edit <sha>` · DB: `--revert` (DROP side-car) · backup path ghi ROLLBACK.

---

## 10. Query báo cáo Admin (chạy trên side-car)

```sql
-- 1) Đa âm (ưu tiên cao nhất)
SELECT id, name_zh, dict_vi, groq_trans_vi, diff_reason
FROM place_groq_audit WHERE diff_type='POLYPHONIC_CHAR' AND needs_review=1 ORDER BY id;
-- 2) Thống kê
SELECT diff_type, COUNT(*) FROM place_groq_audit WHERE review_status='conflict' GROUP BY diff_type;
-- 3) Chấp thuận biến thể từ loại (điều kiện Admin đã chốt)
UPDATE place_groq_audit SET needs_review=0, review_status='approved_dict'
WHERE diff_type='TAXONOMY_VARIANT' AND needs_review=1;
```

## 11. Files

| Loại | Path |
|------|------|
| Sửa | `scripts/verify_dila_places_groq.py` (mới) · `scripts/t169_place_groq_audit_migrate.py` (mới) · `admin/place_update.html` · `app.py` (+2 route API) |
| Test | `tests/test_t169_classify_diff.py` |
| Docs | file này · session · tasktodo · ROLLBACK hash-fill · dashboard regen |

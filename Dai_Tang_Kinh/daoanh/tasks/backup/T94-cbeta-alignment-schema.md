---
id: T94
title: "CBETA Bilingual Alignment Schema + Reader Fix"
module: CBETA Core / Bilingual Reader
priority: high
status: done
depends_on: [T50, TAB_DAI_TANG_PLACE, T85]
created: 2026-09-04
updated: 2026-09-06
done_when: >
  text_passages + translation_segments + passage_translation_alignment tables created;
  UI đọc từ alignment table khi có (reader chip "✓ Đã kiểm chứng" khi manual_verified);
  Admin workflow: báo sai → fix → INSERT alignment record hoạt động (endpoint verify + nút monitor)
---

# T94 — CBETA Bilingual Alignment Schema + Reader Fix

## Bối cảnh

**Lỗi alignment đã xác nhận (session 2026-09-04):**
- Hán đoạn 41 (T50n2060): về dịch Đại Bát Nhã, Long Sóc 3, 600 quyển
- Việt đoạn 41 (hiện tại — SAI): "Năm Hiển Khánh thứ hai, giá hạnh Lạc Dương..." (thực ra là Hán đoạn ~33)
- Root cause: `dtDistributeVi` phân phối Vi theo tỉ lệ ký tự; LLM dịch cả passage thành 1 chuỗi liên tục không có ranh giới đoạn; ghép theo ordinal → lệch ~8 đoạn tại đoạn 41

## Phase 0 — Audit ✅ DONE (2026-09-04)

Script: `scripts/audit_cbeta_corpus.py`
Kết quả: `docs/cbeta-corpus-audit-results-20260904.md`

### Số liệu thực tế:

| Chỉ số | Giá trị |
|--------|---------|
| total_passages | 7,563 |
| has_vi | 218 (2.9%) |
| is_draft | 218 (tất cả draft) |
| empty_vi | 7,345 (97.1%) |
| avg_han_len | 210.2 chars |
| max_han_len | 8,034 chars (T50n2060) |

### Phân phối theo work:

| text_id | total | translated | avg_han | max_han |
|---------|-------|-----------|---------|---------|
| T51n2076 | 3,917 | 194 | 116 | 6,306 |
| T50n2061 | 1,346 | 7 | 242 | 2,558 |
| T50n2060 | 1,037 | 13 | 444 | 8,034 |
| X77n1524 | 1,016 | 3 | 291 | 3,759 |
| T50n2062 | 247 | 1 | 215 | 1,997 |

### Rủi ro phát hiện:

| Rủi ro | Kết quả | Mức |
|--------|---------|-----|
| Passages > 2000 chars (concat?) | **20 passages** — T50n2060 có 8034 chars | HIGH |
| Duplicate raw_text | ✅ OK — không có | OK |
| Hán văn trong vi_text | ✅ OK — không phát hiện | OK |
| Orphan passage_entity | ✅ OK — không có | OK |
| Vi/Han ratio bất thường | `passage_id=39` ratio=29.39 (han=62 vi=1822) | REVIEW |
| Alignment schema | ❌ Tất cả 3 bảng chưa có | CRITICAL |
| `raw_zh_hash` column | ❌ Chưa có | HIGH |

### Phát hiện quan trọng từ audit:
- Passages `min_han_len=5` — có passage chỉ 5 ký tự Hán (rất ngắn, có thể là header/page number)
- Ratio vi/han cao bất thường: `passage_id=39` ratio=29x, `3546` ratio=24x (cần review thủ công)
- T50n2060 có passages tới **8,034 chars** — xác nhận đây là biography dài, không phải concat lỗi

## Phase 1 — Schema Creation ✅ DONE (2026-09-04)

Script: `scripts/t94_create_alignment_schema.py`
Backup: `data/lineage.db.backup_t94_20260904_225841` (1,241 MB)

Kết quả:
- ✅ Created: `text_passages`
- ✅ Created: `translation_segments`
- ✅ Created: `passage_translation_alignment`
- ✅ Added: `passage.raw_zh_hash`
- ✅ Added: `passage.passage_id_ref`
- ✅ Added: `passage.segmentation_method`

**Rollback Phase 1:** `python scripts/t94_create_alignment_schema.py --revert`

### SQL migration (additive, không đụng data cũ — đã chạy):

```sql
-- Migration 001: text_passages
CREATE TABLE IF NOT EXISTS text_passages (
    passage_id          TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    source_system       TEXT NOT NULL DEFAULT 'CBETA',
    canonical_ref       TEXT,
    juan                TEXT,
    sequence_no         INTEGER,
    original_zh         TEXT NOT NULL,
    raw_zh_hash         TEXT NOT NULL,
    segmentation_method TEXT,
    tei_anchor_start    TEXT,
    tei_anchor_end      TEXT,
    source_url          TEXT,
    source_version      TEXT,
    import_run_id       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Migration 002: translation_segments
CREATE TABLE IF NOT EXISTS translation_segments (
    translation_id      TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    language            TEXT DEFAULT 'vi',
    translation_text    TEXT NOT NULL,
    translator_type     TEXT,
    model_name          TEXT,
    prompt_version      TEXT,
    source_passage_ids  TEXT,
    translation_status  TEXT DEFAULT 'draft',
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Migration 003: passage_translation_alignment
CREATE TABLE IF NOT EXISTS passage_translation_alignment (
    alignment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id          TEXT NOT NULL,
    translation_id      TEXT NOT NULL,
    alignment_type      TEXT NOT NULL,
    source_start_offset INTEGER,
    source_end_offset   INTEGER,
    confidence          REAL DEFAULT 0.5,
    alignment_method    TEXT,
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    note                TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passage_id) REFERENCES text_passages(passage_id),
    FOREIGN KEY (translation_id) REFERENCES translation_segments(translation_id)
);

-- Migration 004: additive columns on passage table
ALTER TABLE passage ADD COLUMN raw_zh_hash TEXT;
ALTER TABLE passage ADD COLUMN passage_id_ref TEXT;
ALTER TABLE passage ADD COLUMN segmentation_method TEXT DEFAULT 'punctuation';
```

**Rollback Phase 1:** DROP new tables + DROP new columns (nếu SQLite hỗ trợ).

## Phase 2 — Chiến lược fill alignment table (KHÔNG re-translate)

**Quyết định 2026-09-04:** Không re-translate lại từ đầu — lãng phí token và
không cần thiết. Chiến lược thực tế:

| Trường hợp | Hành động |
|-----------|-----------|
| Passage có `vi_text` (218 bản) | Giữ nguyên, hiển thị `≈` — user biết là auto-distributed |
| Passage chưa có `vi_text` (7,345) | Lazy translate qua T85 khi user request |
| User báo sai qua nút "Báo sai" | Admin nhận alert → fix thủ công passage đó |
| Fix thủ công xong | INSERT vào `passage_translation_alignment` với `alignment_type='manual_verified'` |

**alignment table fill dần theo thời gian** — chỉ những passages đã được human
verify mới vào `passage_translation_alignment`. Số `≈` tự biến thành số thật
khi có `alignment_type='manual_verified'` cho passage đó.

**KHÔNG CẦN:**
- Re-translate 218 passages đã có (data hiện tại đủ xài với cảnh báo ≈)
- Batch populate alignment table ngay bây giờ
- Groq API để phase này

**Bước tiếp theo thực tế:**
1. Khi user báo sai 1 passage → admin fixes vi_text + INSERT vào alignment table
2. Frontend: nếu `alignment_id` tồn tại → hiển thị số thật + tooltip passage_id
3. Nếu không → giữ `≈` như hiện tại

## UI changes đã thực hiện (2026-09-04)

Trong khi chờ Phase 1-2, đã fix UI để không gây hiểu nhầm học thuật:
- Vi column: dùng `≈` thay ordinal numbers
- Header Vi pane: "⚠ phân phối tự động"
- Warning box: "⚠ PHÂN PHỐI TỰ ĐỘNG theo tỉ lệ ký tự — số thứ tự bên Việt KHÔNG khớp số bên Hán"

**Verified trong browser:** `viSegCount=54`, `firstViNum=≈`, noteText đúng.

## Phase 2B — Reader faithful (2026-09-05) ✅ DONE

Theo yêu cầu admin (kiểm chứng logic định kỳ — kết luận chẩn đoán ĐÚNG):
quyết định **bỏ hẳn `dtDistributeVi`** (cắt bản Việt theo tỉ lệ ký tự — NGUỒN GỐC
mọi lỗi lệch nội dung). Giờ bản dịch hiển thị **TOÀN PHẦN 1 khối** cho mỗi passage:

- `dtDistributeVi()` **đã xóa** khỏi `places.html` (hết dead code, không còn dùng)
- `dtBuildSegments()` chỉ còn build segment Hán để đọc (`target_text_vi: null`, `alignment_status: 'text_only'`)
- Việt pane: 1 bài `.dt-seg-full-vi` với dấu `¶` + provenance line:
  `📌 Bản dịch TOÀN PHẦN passage <text_id> · <loc_ref> · passage_id <id> — không chia theo số đoạn Hán`
- Bỏ note `⚠ PHÂN PHỐI TỰ ĐỘNG...` và các nhãn `≈` per-seg cũ; hover Hán → KHÔNG còn liên kết giả sang Việt
- **Data KHÔNG đổi**: `passage.vi_text` vẫn là bản dịch toàn passage (model 1:1 cấp passage vốn ĐÚNG)

**Verify:** `node --check` places.html PASS; Playwright live (localhost:8080, drive
`renderDaiTangMain`→`dtRenderPassage` với passage thật 3951 · T50n2060 · 0-0457a-):
vi-body = 1 block `Bản dịch TOÀN PHẦN` + passage_id 3951 + `¶`, 0 lỗi console,
không còn `PHÂN PHỐI TỰ ĐỘNG` / `dt-seg-unmapped`, Hán pane render bình thường.

Session: `docs/sessions/2026-09-05_T94_phase2b_fullblock_reader.md`. Rollback: `git revert HEAD`.

## Phase 3 — Admin verify → manual_verified alignment ✅ DONE (2026-09-06)

Admin duyệt phạm vi **3A đầy đủ**. Đã build:
- `POST /daoanh/api/admin/translation/verify` (app.py): passage_id → bản dịch hiện
  hành → `quality_status='reviewed'` + `review_status='verified'` + INSERT idempotent
  `passage_translation_alignment (alignment_type='manual_verified', confidence=1.0,
  alignment_method='manual_admin_verify', review_status='verified')`. Idempotent (DELETE + INSERT).
- `_T95_UNITS_SQL`/`_t95_badge`: units API trả `manual_verified: bool` (additive).
- `api_t95_job_detail`: item trả `translation_id` (để nút duyệt ở monitor).
- `admin/translation_monitor.html`: nút `✓ Duyệt chuẩn` per item (confirm trước, badge "✓ đã duyệt").
- `places.html`: chip `✓ Đã kiểm chứng` cạnh badge khi `manual_verified`.

Verify: py_compile + node --check (places.html, monitor) + `npm run test`/`e2e` PASS +
test_client DB tạm 9/9 assert (404/400/idempotent) — **không đụng data thật**; SQL mới
chạy read-only trên DB thật OK. **Cần restart server :5000 để có hiệu lực.**

Rollback 1 lượt duyệt: `DELETE ... WHERE translation_id='<tid>' AND alignment_type='manual_verified'`
+ `UPDATE translation_segments SET quality_status=NULL, review_status='pending', reviewer=NULL WHERE translation_id='<tid>'`.

Session: `docs/sessions/2026-09-06_T94_phase3_manual_verify.md`.

## Test cases bắt buộc

Xem: `docs/alignment-test-cases.md` (TC-001 đến TC-011)

**TC-001 (critical):**
- Han 41: 創翻大本。至龍朔三年十月末了。凡四處十六會說。總六百卷。
- Vi phải có: Đại Bát Nhã / Long Sóc 3 / 600 quyển / bốn nơi mười sáu hội
- Vi KHÔNG được có: Hiển Khánh / Lạc Dương / giá hạnh

## Rollback

- Phase 0: không cần (read-only)
- Phase 1: DROP mới tạo (không data loss)
- Phase 2+: restore từ backup
- UI fix: `git revert` commit này

## Tài liệu liên quan

- `docs/alignment-audit-report.md` — xác nhận lỗi alignment
- `docs/bilingual-passage-alignment-design.md` — schema design
- `docs/cbeta-global-passage-standard.md` — kiến trúc CBETA canonical ID
- `docs/cbeta-corpus-audit.md` — kế hoạch audit
- `docs/cbeta-corpus-audit-results-20260904.md` — kết quả audit thực tế
- `docs/cbeta-migration-rollout-plan.md` — rollout plan 5 phases
- `docs/t50n2060-repair-plan.md` — T50n2060 repair steps
- `docs/alignment-test-cases.md` — TC-001 đến TC-011

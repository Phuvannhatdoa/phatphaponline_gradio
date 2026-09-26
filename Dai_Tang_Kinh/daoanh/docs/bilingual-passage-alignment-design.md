# Bilingual Passage Alignment — Design Document

**Ngày:** 2026-09-04  
**Status:** DESIGN (chưa implement)  
**Priority:** P0 — phải có trước khi dùng bilingual reader cho evidence/citation

---

## 1. Nguyên tắc bất biến

> **Không dùng số thứ tự hiển thị (ordinal index) làm khóa liên kết Hán–Việt.**

Mọi alignment phải dựa trên:
- `passage_id` ổn định (bên Hán)
- `translation_id` ổn định (bên Việt)
- Bảng `passage_translation_alignment` nối hai bên

---

## 2. Schema đề xuất

### Bảng `text_passages` (Hán văn đơn vị nhỏ nhất)

```sql
CREATE TABLE text_passages (
    passage_id      TEXT PRIMARY KEY,  -- daoanh:cbeta:T50n2060:0457a:p001
    work_id         TEXT NOT NULL,     -- T50n2060
    source_system   TEXT NOT NULL,     -- CBETA
    canonical_ref   TEXT,              -- T50n2060_p0457a
    juan            TEXT,              -- quyển số nếu có
    sequence_no     INTEGER,           -- thứ tự trong work, chỉ để sort UI
    original_zh     TEXT NOT NULL,     -- Hán văn nguyên bản (bất biến)
    raw_zh_hash     TEXT NOT NULL,     -- SHA-256 của original_zh
    segmentation_method TEXT,          -- 'tei_p', 'tei_lb', 'punctuation', 'manual'
    tei_anchor_start TEXT,             -- Ví dụ: T50n2060_p0457a01
    tei_anchor_end   TEXT,
    source_url      TEXT,              -- CBETA online URL
    source_version  TEXT,              -- CBETA version ngày import
    import_run_id   TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Bảng `translation_segments` (Việt văn)

```sql
CREATE TABLE translation_segments (
    translation_id      TEXT PRIMARY KEY,  -- daoanh:vi:T50n2060:0457a:p001:v1
    work_id             TEXT NOT NULL,
    language            TEXT DEFAULT 'vi',
    translation_text    TEXT NOT NULL,
    translator_type     TEXT,              -- 'ai_draft', 'human', 'hybrid'
    model_name          TEXT,              -- 'qwen/qwen3.8-27b'
    prompt_version      TEXT,
    source_passage_ids  TEXT,              -- JSON array passage_ids được dịch trong batch
    translation_status  TEXT DEFAULT 'draft',  -- draft, reviewed, published
    review_status       TEXT,              -- pending, approved, rejected
    reviewer            TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Bảng `passage_translation_alignment`

```sql
CREATE TABLE passage_translation_alignment (
    alignment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id          TEXT NOT NULL REFERENCES text_passages(passage_id),
    translation_id      TEXT NOT NULL REFERENCES translation_segments(translation_id),
    alignment_type      TEXT NOT NULL,
        -- 'exact_1_to_1'          : 1 passage ↔ 1 translation
        -- 'many_source_to_one'    : N passages ↔ 1 translation
        -- 'one_source_to_many'    : 1 passage ↔ N translations (cắt nhỏ bản Việt)
        -- 'partial_span'          : translation chỉ dịch một phần passage
        -- 'uncertain'             : chưa xác định
    source_start_offset INTEGER,  -- byte offset trong original_zh (nếu partial)
    source_end_offset   INTEGER,
    confidence          REAL DEFAULT 0.5,  -- 0.0–1.0
    alignment_method    TEXT,
        -- 'manual'           : curator xác nhận bằng tay
        -- 'deterministic'    : 1-to-1 từ pipeline dịch theo segment
        -- 'llm_suggested'    : LLM tự suggest (cần verify)
        -- 'reviewed'         : đã có human review
    review_status       TEXT DEFAULT 'pending',  -- pending, approved, rejected
    reviewer            TEXT,
    note                TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Canonical Passage ID

### Format
```
daoanh:cbeta:{work_id}:{page_anchor}:p{seq:03d}
```

### Ví dụ
- `daoanh:cbeta:T50n2060:0457a:p001`
- `daoanh:cbeta:T50n2060:0457a:p041`
- `daoanh:cbeta:T51n2076:0220b:p001`

### Quy tắc
1. **Không thay đổi** sau khi tạo
2. `page_anchor` lấy từ CBETA loc_ref (ví dụ `0-0457a-` → `0457a`)
3. Nếu không có page anchor: dùng `work_id:block{n}:p{seq}`
4. Prefix `daoanh:` để phân biệt với CBETA official ID
5. Không tuyên bố là canonical ID của CBETA

---

## 4. Workflow dịch đúng (sau khi implement)

```
1. Import raw CBETA text
   └── Segment theo TEI boundary (ưu tiên) hoặc dấu câu
   └── Tạo text_passages records với passage_id
   └── Hash raw_zh

2. Gửi LLM theo segment hoặc batch nhỏ (3–5 segments)
   Input JSON:
   {
     "passages": [
       {"passage_id": "daoanh:cbeta:T50n2060:0457a:p001", "original_zh": "竊聞。六爻..."},
       {"passage_id": "daoanh:cbeta:T50n2060:0457a:p002", "original_zh": "伏惟。皇帝..."}
     ]
   }

3. Nhận response LLM (bắt buộc có passage_id)
   {
     "translations": [
       {"passage_id": "daoanh:cbeta:T50n2060:0457a:p001", "translation_vi": "..."},
       {"passage_id": "daoanh:cbeta:T50n2060:0457a:p002", "translation_vi": "..."}
     ]
   }

4. Validate response
   - Không thiếu passage_id
   - Không dư passage_id không có trong input
   - Không duplicate ID
   - Không empty translation
   - Hash original_zh trước/sau không đổi
   - Không lẫn Hán văn trong bản Việt

5. Lưu translation_segments
   └── Tạo passage_translation_alignment (deterministic, 1:1)

6. Human review (optional nhưng cần trước khi publish)
   └── Curator xem alignment record
   └── Approve → alignment_method='reviewed', review_status='approved'
   └── Reject → đánh dấu needs_rework
```

---

## 5. Rendering trong UI (sau khi implement)

### Hover sync
- Hover Han segment → lookup alignment table → highlight Vi segment(s) tương ứng
- Hover Vi segment → lookup alignment table → highlight Han segment(s) nguồn
- Nếu `alignment_type = 'many_source_to_one'` → highlight nhiều Han segments

### Metadata hiển thị khi click
```
Hán đoạn 041 | T50n2060 · p0457a
passage_id: daoanh:cbeta:T50n2060:0457a:p041
alignment: exact_1_to_1 | method: deterministic | confidence: 0.85
Bản dịch: AI draft · Groq qwen3.8-27b · v1 · 2026-09-04
```

### Trường hợp chưa có alignment
```
[!] Đoạn Hán này chưa có bản dịch được căn chỉnh.
Không dùng để đối chiếu học thuật.
```

### Trường hợp 1 Việt ↔ nhiều Hán
```
Bản dịch này bao gồm đoạn Hán 40 + 41
[Hán 40] [Hán 41]  ← clickable để scroll đến
```

---

## 6. Quality gate

Chỉ hiển thị như "có thể đối chiếu Hán–Việt" khi:
- `passage_id` tồn tại trong `text_passages`
- Có `alignment_id` trong `passage_translation_alignment`
- `alignment_method IN ('deterministic', 'reviewed', 'manual')`
- `review_status IN ('approved', 'pending')` (pending vẫn OK nếu deterministic)
- Không có `raw_zh_hash` mismatch
- Không có duplicate alignment cho cùng passage_id

Nếu chưa đạt: hiển thị ở chế độ "AI draft phân phối tự động" như hiện tại (đã có label ⚠).

---

## 7. Migration path (từ schema hiện tại)

Bảng `passage` hiện tại:
```
passage_id | raw_text | vi_text | translation_draft | has_vi | ...
```

**Không drop** bảng `passage`. **Thêm** các bảng mới.

Migration script:
1. Đọc `passage.raw_text` → segment → tạo `text_passages` records
2. Đọc `passage.vi_text` → (sau khi re-translate) → tạo `translation_segments`
3. Tạo `passage_translation_alignment` records
4. Update `passage.passage_id_ref` để trỏ vào `text_passages.passage_id`
5. UI đọc từ bảng mới, fallback về bảng cũ nếu không có alignment

---

*Xem thêm: `t50n2060-repair-plan.md` · `alignment-test-cases.md` · `cbeta-global-passage-standard.md`*

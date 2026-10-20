# Quy tắc Data Integrity — PTDA

## Hierarchy nguồn

```
DILA (authority gốc)
  └─ CBETA (evidence / text reference)
  └─ Marcus (lineage supplement)
  └─ Wikidata (timeline, coordinates)
  └─ ZQ / ZQLOCAL (Vietnamese adapter layer — phiên âm tự động)
        └─ Scholar review (confidence 0.8–1.0)
```

**Nguyên tắc:** nguồn có độ ưu tiên cao hơn KHÔNG được bị ghi đè bởi nguồn thấp hơn.

---

## Migration / Import

- Mọi script migration phải:
  - Có `--dry-run` mode (default)
  - Có `--apply` flag (tạo backup tự động trước khi apply)
  - Có `--revert` flag (DROP tables hoặc rollback)
  - Idempotent: chạy nhiều lần cho cùng kết quả
  - Backup tự động: `data/lineage.db.backup_<task>_YYYYMMDD_HHMMSS`

- Không import bulk khi chưa verify dry-run output.
- Không xóa / overwrite dữ liệu raw gốc (DILA TTL, CBETA XML, Marcus RDF).

---

## Evidence-first cho thời gian

| Precision | CE year cho phép? | Điều kiện |
|-----------|-------------------|-----------|
| `exact_year` | ✅ | Từ regex `\d{3,4}年` |
| `reign_era` | ✅ nếu có match | DILA `time_periods.era_name LIKE ?` → CE |
| `dynasty_period` | ✅ range | Từ `DYNASTY_RANGES` constant |
| `relative` | ❌ | Không tự tính CE |
| `unknown` | ❌ | Không tự tính CE |

**Không tự sinh CE year khi không có DILA authority mapping.**

---

## Entity identity

- Canonical ID = DILA ID (format `A000001` cho person, `PL000000...` cho place).
- `people.id` = DILA person ID — **không phải** `people.dila_id` (field không tồn tại).
- Display name, alias, name_zh, name_vi **không bao giờ là join key**.
- Không merge record chỉ dựa trên matching tên.
- Không suy quan hệ từ co-mention trong CBETA passage.

---

## ZQ / ZQLOCAL constraints

- Badge UI phải phân biệt "Nguồn: DILA" vs "Nguồn: ZQ (phiên âm tự động)".
- Không gán `source=DILA` cho tên Việt của ZQ.
- `confidence=0.5`: phiên âm tự động, chưa review.
- `confidence=0.8`: editor ZQ duyệt tay.
- `confidence=1.0`: scholar xác nhận.

---

## Tables quan trọng (audit 2026-09-05)

| Table | Rows | Ghi chú |
|-------|------|---------|
| `time_periods` | 117,429 | KHÔNG phải 0 — CLAUDE.md cũ sai |
| `nexus_events` | 10,458 | Person-place co-mention |
| `event_text_link` | 17,284 | Person-place với CBETA cbeta_ref |
| `time_mentions` | 3,687 | T97 — raw span + precision |
| `events` | 3,530 | T97 — candidate founding events |

---

## LLM keys (bảo mật — KHÔNG bao giờ commit)

- Key LLM (Groq) lưu tại `data/llm_config.json` — **gitignored** (mục `*.json` của `.gitignore`).
- Code đọc qua helper `_llm_config_read()` trong `app.py` (fallback env `GROQ_KEY`/`GROQ_MODEL`).
- `data/*.json`, `tests/`, `data/` không được commit; nếu lỡ sửa file ignored phải `git add -f`
  nhưng chỉ stage file code/docs, tuyệt đối không stage `llm_config.json`.
- Quy trình revert/recover code + data: `docs/ROLLBACK.md`.

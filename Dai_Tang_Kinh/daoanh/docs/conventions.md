# Conventions — Đạo Ảnh Project

**Last updated:** 2026-05-21
**Applies to:** All development, documentation, and AI agent sessions

---

## 1. Documentation & Logging

### Session Logging (Mandatory)

Every BUILD task MUST create a session log file:

```
docs/sessions/YYYY-MM-DD_task-slug.md
```

**Required sections:**
- Mô tả ngắn task
- Thiết kế/giải pháp đã chọn
- Danh sách file/code đã tạo/sửa
- Cách chạy/test

### When to Update Docs

| Change | Update |
|--------|--------|
| New table/column | `docs/db_schema.md` |
| New pipeline | `docs/pipelines.md` |
| Translation flow change | `docs/translation_workflow.md` |
| New module/architecture | `docs/overview.md` |
| New convention | `docs/conventions.md` |

### Before Starting a New Task

1. Read `docs/overview.md`, `docs/db_schema.md`, `docs/pipelines.md`
2. Ensure new design does not break existing architecture

### Master Session Log

`session.md` (root) is the **active master log** — all session updates are also recorded there for quick reference.

---

## 2. Git Commit Style

### Format

```
PREFIX-message: short description
```

### Prefixes

| Prefix | Meaning |
|--------|---------|
| `FEAT-` | New feature |
| `FIX-` | Bug fix |
| `DOCS-` | Documentation change |
| `REFACTOR-` | Code refactoring |
| `MIGRATION-` | DB migration |

### Examples

```
FEAT-labeled-tei-fields: replace plain text with structured labeled record
FIX-address-country-dila-raw: always derive from DILA RAW, ignore stale DB
DOCS-cleanup-standardize: create docs/ structure with 5 skeleton files
```

### Rules

- One commit per logical change
- Include docs changes in the same commit as code changes
- Never commit secrets or API keys
- Never commit without running `npm run pipeline` first

---

## 3. Tester Agent (Mandatory Before Review)

**Rule:** NO EXCEPTIONS — run tester before requesting admin review.

### Quick Command

```bash
npm run pipeline     # lint + test + e2e + e2e:runtime
npm run tester:agent # same as pipeline
```

### Pipeline Stages

| Stage | Command | Checks |
|-------|---------|--------|
| Lint | `npm run lint` | JS syntax in HTML files |
| Test | `npm run test` | Unit/integration tests |
| E2E | `npm run e2e` | HTML/JS error check |
| e2e:runtime | `npm run e2e:runtime` | Playwright runtime tests |

### Workflow

1. Developer makes changes
2. Run `npm run pipeline`
3. If all pass → Request review from admin
4. If any fail → Fix → Run again
5. Admin ONLY reviews when "All tests passed" is shown

---

## 4. Code Preservation

- **Never overwrite existing functionality** — integrate new features seamlessly
- **Prefer editing existing files** over creating new ones (unless clearly required)
- When creating new components, follow existing patterns (naming, typing, framework choice)

## 5. Zero-RAM Principle

- Never load entire data files into RAM
- Use streaming generators (`yield`), binary indexes, and index-based search
- Applies to: ETL scripts, API endpoints, frontend data processing

## 6. Database Rules

### Layer Access

| Layer | Can Read | Can Write |
|-------|----------|-----------|
| RAW | Any code | ETL scripts only (import) |
| STAGING | Any code | ETL + Admin UI |
| FINAL | Any code | ETL + Admin UI (via save endpoint) |

### Naming

- No `_new`, `_copy`, `_backup` suffixes
- Staging tables: `_staging` suffix
- All tables must have documented purpose in `docs/db_schema.md`
- Every import must insert into `dataset_sources` with `origin_url`, `license`, `usage_level`

## 7. DILA & Data Sources

### Authority Sources

| Source | License | Usage Level |
|--------|---------|-------------|
| DILA Authority | CC0 / CC-BY | GREEN |
| CBETA | CC0 | GREEN |
| Marcus FoJin | CC-BY-NC | YELLOW |
| Academia Sinica | CC-BY | GREEN |

### ID Format

- DILA Place: `PL` + 12 digits (zero-padded), e.g. `PL000000000003`
- DILA Person: `A` + 6 digits, e.g. `A000001`

### Matching Rules (Lexicon)

- `key_norm` = lowercase + diacritics-free headword
- Search order: Exact → Case-insensitive → Diacritics-free
- Skip self-match: Chinese term matching itself is ignored

## 8. Nginx Configuration

### Route Routing

```
/daoanh/api/login/*  →  server.py:5001 (auth)
/daoanh/api/*        →  app.py:5000 (main)
/daoanh/admin/*      →  app.py:5000
```

### POST Fix (2026-04-17)

- Ensure no `rewrite` directive for `/daoanh/api/` locations
- Use `proxy_pass http://127.0.0.1:5000;` directly

## 9. LLM / AI Usage

- **Gemini 2.0 Flash**: Primary translation model (free tier)
  - API Key: `AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE` (do not commit)
  - Currently rate-limited (429) → falls back to GoogleTranslator
- **GoogleTranslator**: Fallback for `translate_context`
- Transliteration: Local rule-based (`adminMapping`), no API needed

# Session 2026-10-06 — T254: Sửa 3 ID trùng có sẵn (dup:ids blocker)

- **Task:** `tasks/T254-dup-id-renumber.md` (id `T254` — kiểm 2 tầng trước khi tạo: Grep `T25[4-7]` toàn repo = 0 hit)
- **HEAD đầu phiên:** `bcec8f2b924033cc0d252fe3d151ca1e52d945e9` (sau T253)
- **Bối cảnh:** Admin chốt P0-1 = **(a)** (additive route) → mở T253 Phase 1;
  nhưng `npm run pipeline` FAIL sẵn ở `dup:ids` (3 ID trùng có từ trước) → xử trước.

## 1. Quyết định đổi số (AGENTS §16 — footprint nhỏ nhất)

| Cặp | Giữ | Đổi → | Nửa đổi có tham chiếu gì |
|---|---|---|---|
| T188 | `t171-spec-logic-fixes` (tasktodo + 2 ROLLBACK sha + amended_by + depends_on T190/T192) | `docs/integration/T188-canonical…` → **T255** | T189 (1 dòng), tự nó (4 dòng) |
| T237 | `cbeta-corpus-search-reader` (tasktodo + SESSION.md + test file) | `gate-vpa-admin-confirmed-only` → **T256** | T239 related, T257 related + 1 dòng text |
| T238 | `cbeta-text-browser-toc` (tasktodo + SESSION.md + test file) | `reject-ttl-mismatch-button` → **T257** | T239/T240 related, T257 tự |

Không đụng: `docs/ROLLBACK.md` lịch sử (sha revert gắn ID cũ), entry tasktodo đã công bố,
test `test_t237_cbeta_corpus_search.py` / `test_t238_cbeta_text_browser.py` (thuộc bên giữ).

## 2. Thao tác

1. `Rename-Item` 3 file (không dùng `git mv` — index thật hỏng, xem session T253 §3).
2. Frontmatter: `id` mới + `former_ids: [ID cũ]` cho 3 file; sửa heading/bullet/revert trong T255;
   `related`/text trong T257.
3. Sửa tham chiếu: `T189-viphu` (T188→T255), `T239` (`[T256, T257]`), `T240` (`[T257, T239]`).
4. Ghi chú "đã sửa qua T254" vào T253 task §6 + report Cline §8 + session T253 §4.
5. T253 unblock: `status: blocked → in_progress`, `blocked_reason` = Admin chốt (a) 2026-10-06,
   `depends_on` + `T254`.
6. Regen `data/progress_data.json`.

## 3. Kiểm chứng

```text
npm run dup:ids   # phải PASS exit 0 — không còn [FAIL] T188/T237/T238
npm run guard     # PASS
npm run lint      # PASS
npm run pipeline  # phải chạy QUA bước dup:ids (kết quả các bước sau ghi ở dưới)
```

(kết quả sẽ được điền sau khi chạy — xem mục 5)

## 4. File tạo/sửa

| file | thao tác |
|---|---|
| `tasks/T254-dup-id-renumber.md` | TẠO MỚI |
| `docs/sessions/2026-10-06_T254-dup-id-renumber.md` | TẠO MỚI (file này) |
| `docs/integration/T255-canonical-reference-integration.md` | RENAME + frontmatter/ref |
| `tasks/T256-gate-vpa-admin-confirmed-only.md` | RENAME + frontmatter |
| `tasks/T257-reject-ttl-mismatch-button.md` | RENAME + frontmatter/related/text |
| `docs/integration/T189-viphu-tu-ca-cuu-tri.md` | SỬA 1 dòng (T188→T255) |
| `tasks/T239-xcm-tab-namevimap.md` | SỬA `related` |
| `tasks/T240-xcm-rejected-clickable.md` | SỬA `related` |
| `tasks/T253-person-import-phase0-audit.md` | SỬA — unblock (a) + ghi chú T254 |
| `docs/integration/Cline/2026-10-06-person-import-phase0-audit.md` | SỬA — ghi chú đã sửa qua T254 |
| `docs/sessions/2026-10-06_T253-person-import-phase0-audit.md` | SỬA — ghi chú đã sửa qua T254 |
| `docs/tasktodo.md` | SỬA — cập nhật block T253 (unblock) + block T254 mới |
| `docs/ROLLBACK.md` | SỬA — row T254 (`<sha_T254>` → hash-fill pass-2) |
| `data/progress_data.json` | REGEN |

## 5. Kết quả kiểm chứng & commit

```text
npm run dup:ids  → ✅ exit 0  "[OK] Không có task ID trùng thật." (175 task; 4 X- superseded INFO)
npm run guard    → ✅ exit 0
npm run lint     → ✅ exit 0  (7 script blocks)
npm run pipeline → ✅ exit 0  XANH toàn chuỗi:
   guard → dup:ids → audit:honesty:strict → lint → test → test:t226 … t233 →
   test:translation → test:uat → test:compliance → test:gov → audit:t166 →
   e2e (all pages) → e2e:runtime (2 passed)
```

> Môi trường: `test:t226` lần chạy đầu FAIL vì thiếu module Python `jsonschema` / `pyshacl`
> (lỗi env có sẵn, không do T254). Đã `python -m pip install jsonschema pyshacl`
> (4.26.0 / 0.40.1) → pipeline xanh.

Commit: pass-1 `3767f823bda11c032a2aff03052f55d47a33ff3d` (đủ path changes) → pass-2
`003495a0739e576474d7f8a01b1293ed78b7c93b` (hash-fill row ROLLBACK + ghi sha vào session) — quy trình §14/§17 + plumbing thủ công
(`git write-tree` → `git commit-tree` → `git update-ref` CAS), real `.git/index` SHA1
phải giữ `61A2E08657B3C4446CE2E316588F04CC84A148B5`.

**Revert:** `git revert --no-edit <sha_pass2> <sha_pass1>` (2 commit, pass-2 trước) —
rename 3 file về tên cũ + khôi phục frontmatter/tham chiếu (docs-only, 0 code, 0 DB).

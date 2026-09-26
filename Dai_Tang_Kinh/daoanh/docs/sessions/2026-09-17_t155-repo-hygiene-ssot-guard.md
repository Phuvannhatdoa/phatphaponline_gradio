# Session — T155 Repo Hygiene / SSOT Guard (2026-09-17)

> **Infra closure — additive · 0 code nghiệp vụ · 0 DB · 0 ALTER · 0 destructive · mirror chuẩn T150/T151.**
> Revert: `git revert --no-edit <sha_T155>`.

---

## 1. Vấn đề

Phát hiện khi dọn dirty tree (T153/T154): repo có 2 loại "mìn" làm suy yếu SSOT và invariant leftover=0:
1. `Dai_Tang_Kinh/daoanh/.git` = thư mục hỏng/rỗng (chỉ `refs/`), git bỏ qua nhưng có thể bị `git init` biến thành repo thật.
2. `Authority-Databases` + `chinese_buddhism_sna_temp` = **gitlink mồ côi** (mode 160000, không `.gitmodules`) → làm bẩn `git status` vĩnh viễn.

## 2. Thay đổi (PA-B)

| # | Việc | Cách làm | Ảnh hưởng dữ liệu |
|---|------|----------|-------------------|
| 1 | Gỡ gitlink mồ côi khỏi index | `git rm --cached -- <path>` (x2) | **Không** (file giữ nguyên) |
| 2 | Chặn tái track | `.gitignore` thêm 2 path | Không |
| 3 | Vô hiệu `.git` hỏng | rename → `.git.disabled-20260917/` | Không (rỗng) |
| 4 | Guard tự động | `scripts/repo_guard.py` + wire `npm run pipeline` | Không |
| 5 | Rule SSOT | thêm vào `AGENTS.md` | Không |

## 3. Guard làm gì

`python -X utf8 scripts/repo_guard.py`:
- `[OK/FAIL]` khẳng định `git rev-parse --show-toplevel == <visjs-app root>` (tính từ vị trí script, không gõ tay).
- `[OK/FAIL]` phát hiện `.git/HEAD` trong `Dai_Tang_Kinh/daoanh/` (nguy cơ tách lịch sử).
- Exit code 1 khi fail → pipeline dừng sớm, báo rõ.

## 4. Trụ SSOT

| Trụ SSOT | File | Trạng thái |
|----------|------|-----------|
| Canonical task | `tasks/T155-repo-hygiene-ssot-guard.md` | **1 unique** ✓ |
| Canonical session | `docs/sessions/2026-09-17_t155-repo-hygiene-ssot-guard.md` | **1 unique** ✓ (file này) |
| tasktodo row | `docs/tasktodo.md` T155 | **DONE** ✓ |
| ROLLBACK row | `docs/ROLLBACK.md` T155 | hash-fill real 2-pass |
| Dashboard | `data/progress_data.json` | regen real `build_progress_data.py` ✓ |
| Leftover | scripts/ `*t155*` | **0** ✓ |

## 5. Verify
- `npm run pipeline` PASS (guard thêm ở đầu, phải xanh).
- `git status` sạch (không còn ` m Authority-Databases`).

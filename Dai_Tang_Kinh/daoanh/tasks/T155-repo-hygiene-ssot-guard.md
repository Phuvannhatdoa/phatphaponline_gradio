---
id: T155
title: "Repo Hygiene / SSOT Guard (dọn gitlink mồ côi + vô hiệu hoá .git hỏng + guard tự động)"
module: infra
priority: high
status: done
depends_on: []
created: 2026-09-17
updated: 2026-09-17
done_when:
  - "[x] Gỡ gitlink mồ côi khỏi index (git rm --cached, KHÔNG xoá file): Authority-Databases + chinese_buddhism_sna_temp"
  - "[x] .gitignore thêm 2 đường dẫn nested data repo"
  - "[x] Vô hiệu hoá .git hỏng trong Dai_Tang_Kinh/daoanh/ (rename, giữ vết)"
  - "[x] scripts/repo_guard.py + wire vào npm pipeline"
  - "[x] Rule SSOT repo-root vào AGENTS.md"
---

# T155 — Repo Hygiene / SSOT Guard

> **Module:** `infra` (git / SSOT / pipeline guard)
> **Priority:** high · **Status:** done
> **Type:** chore/infra (additive, 0 code nghiệp vụ, 0 DB, 0 ALTER)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17

---

## 1. Bối cảnh (đã verify thật)

| Hiện tượng | Bằng chứng |
|---|---|
| `Dai_Tang_Kinh/daoanh/.git` là thư mục **hỏng/rỗng** | chỉ chứa `refs/` rỗng; không có `HEAD`, `config`, `objects` → git bỏ qua, `--show-toplevel` vẫn = `visjs-app` |
| 2 thư mục data là **gitlink mồ côi** (mode `160000`, không `.gitmodules`) | `git ls-files -s` → `160000 … Authority-Databases` và `… chinese_buddhism_sna_temp` |
| Gây bẩn `git status` vĩnh viễn | luôn hiện ` m Authority-Databases` |

### Rủi ro
- **SSOT mong manh:** một `git init` (hoặc tool tạo `HEAD`) trong `daoanh/` sẽ biến nó thành repo thật → tách lịch sử → mọi `git revert` từ `daoanh` trỏ sai → phá cam kết "revert dễ dàng".
- **Invariant leftover=0 / working tree sạch** không bao giờ PASS 100%.
- Rủi ro commit nhầm con trỏ repo dữ liệu thô (trái "raw bất biến").

## 2. Giải pháp (PA-B đã được phê chuẩn)

1. **Gỡ gitlink mồ côi khỏi index — KHÔNG xoá file:**
   `git rm --cached -- Dai_Tang_Kinh/daoanh/data/dila_import/Authority-Databases`
   `git rm --cached -- Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna_temp`
2. **`.gitignore`** thêm 2 đường dẫn trên → `git status` sạch vĩnh viễn.
3. **Vô hiệu hoá `.git` hỏng:** rename `Dai_Tang_Kinh/daoanh/.git` → `.git.disabled-20260917/` (rỗng, 0 mất mát, hoàn nguyên tức thời).
4. **Guard tự động:** `scripts/repo_guard.py` — khẳng định `git rev-parse --show-toplevel == visjs-app` và fail nếu tồn tại `daoanh/.git/HEAD`; wire vào `npm run pipeline`.
5. **Rule AGENTS.md:** mọi lệnh git chạy từ toplevel; cấm `git init` trong `daoanh/`.

## 3. Ràng buộc được tôn trọng
- **Additive / 0 destructive:** chỉ đụng index + `.gitignore` + rename thư mục rỗng; không xoá/sửa byte dữ liệu nào.
- **Raw bất biến / Zero-RAM:** 2 nested repo giữ nguyên trên đĩa.
- **Revert thuận tiện:** 1 commit code/infra → `git revert --no-edit <sha_T155>`.
- **SSOT 1 nguồn:** repo root khoá = `visjs-app`, có guard chống tái phát.

## 4. Revert
`git revert --no-edit <sha_T155>` (khôi phục gitlink + .gitignore). Riêng rename `.git` hoàn nguyên bằng cách đổi tên ngược.

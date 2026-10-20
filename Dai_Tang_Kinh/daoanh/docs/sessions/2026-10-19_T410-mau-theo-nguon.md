# Session 2026-10-19 — T410 / BUG-035: bảng màu nét theo NGUỒN

## 1. Thông tin đọc nhanh

| Hạng mục | Giá trị |
|---|---|
| Task | T410 (`tasks/T410-lineage-legend-remove-spine-candidate.md`) — BUG-035 |
| HEAD lúc bắt đầu | `eb5bf9e3e320b34dfb0dbdf20de457bb9ee70da3` |
| Repo root | `visjs-app` (đúng SSOT — đã xác minh bằng `git rev-parse --show-toplevel`) |
| File sửa | `places.html`, `app.py` (code-only, KHÔNG ghi DB) |
| Trạng thái | Build xong — chờ `daoanh-qa` + Admin DONE |
| Test | `py_compile` OK · lint exit 0 · e2e exit 0 · 3/3 script block của `places.html` syntax OK |
| Ảnh | 6 ảnh trong `docs/sessions/2026-10-19/t410_{A004980,A009460,A047924}_{dark,light}.png` |

## 2. Đọc trong 2 phút

Đã thay **toàn bộ** quy tắc màu nét trong cây truyền thừa: từ **"màu theo SỐ nguồn"** (3 xanh · 2 vàng · 1 đỏ)
sang **"màu theo NGUỒN"** (DILA xanh · Marcus vàng · TTL đỏ · ≥2 nguồn khớp = trắng/bạc · 0 nguồn = xám nét đứt).

Phát hiện quan trọng nhất: **có BA khối chú thích, không phải hai** — ngoài "Chú thích màu nét" và
"Y-fork · 3 nguồn", còn một dòng tóm tắt `#lineage-legend-row` ở đầu tab đang dùng `#d4a030` / `#e07820`
(theo số nguồn). Nếu chỉ làm theo đặc tả gốc thì còn sót khối này.

Ba việc Admin cần làm ngay:
1. Xem 6 ảnh trong `docs/sessions/2026-10-19/` và xác nhận màu nét đúng ý.
2. Giao `daoanh-qa` kiểm độc lập (đã đủ bằng chứng trong mục 6).
3. Quyết định gộp `T419` / `T420` (cùng là BUG-041 "Gõ 'Thiên Nhiên' không tải cây", cả hai `in_progress`) — vi phạm §16.

## 3. Đề suất phần chữa dựng

### 3.1 Ba quyết định của Admin (đã thi hành)

| Câu hỏi | Admin chốt | Cách áp dụng |
|---|---|---|
| (1) Quy tắc màu cũ ghi sai | Sửa thành màu theo nguồn; bỏ code màu theo số nguồn | Viết lại `_t127EdgeStyle` + `afterDrawing` |
| (2) Màu xung đột `#ff7b72` | Giữ nguyên | Vẫn `#ff7b72` + marker ⚠ (T140) |
| (3) Có chờ T414? | **Không** — T410 làm trước | Nét đứt = "chưa rõ chiều" (tạm) |

Bảng token chính thức Admin duyệt (đã dùng đúng mã này):

| Token | Nền tối | Nền sáng |
|---|---|---|
| `--edge-dila` | `#38bdf8` | `#0284c7` |
| `--edge-marcus` | `#facc15` | `#ca8a04` |
| `--edge-ttl` | `#dc2626` | `#b91c1c` |
| `--edge-agree` | `#f1f5f9` | `#0f172a` |
| `--edge-unknown` | `#94a3b8` | `#64748b` |
| xung đột | `#ff7b72` | `#ff7b72` |

### 3.2 Các bước đã làm

**A — CSS tokens** (`places.html` ~dòng 20–24): thêm 6 biến `--edge-*` vào cả `:root` và `:root[data-theme="light"]`.

**B — Chú thích** (`places.html` ~560–600, ~726–738, ~717):
- Gỡ "Chú thích màu nét" (2 dòng) và "Y-fork · 3 nguồn" (4 dòng).
- Thêm 6 dòng **"Cách đọc cây truyền thừa"** đặt ngay sau `#lineage-gen-v2-inline`.
- Thêm hộp nổi `#lineage-edge-legend-float` trên khung cây, có nút thu gọn/mở.
- Đổi `#lineage-legend-row` (legend thứ ba) sang màu theo nguồn.

**C — Backend** (`app.py:6493` `calculate_edge_color_and_divergence()`):
Viết lại để trả `edge_color_token` + `edge_sources` + `n_sources`, giữ `edge_color` (hex nền tối) làm fallback.
Truyền thêm 3 trường này vào payload ở **cả 2 call site** (BFS lên `app.py:6626`, BFS xuống `app.py:6665`).

**D — Frontend style** (`places.html` `_t127EdgeStyle`):
Thêm `_t410EdgeColor(token)` (đọc CSS var → tự đổi theo nền) và `_t410TokenForEdge(e)`.
Bỏ hẳn nhánh fallback `single_source` / `candidate` dùng `#e07820` / `#6b7a8a` / `#d4a030`.

**E — Vẽ canvas** (`afterDrawing`):
`col` theo token nguồn; `isMain` và `isSpine` chỉ đổi **độ dày nét** và kích thước đầu mũi tên.
Nét đứt **chỉ** khi `unknownDir` (0 nguồn). Cạnh 1 nguồn vẫn **nét liền**.

**F — 3 visEdges builder**: đều gắn `_edgeToken` / `_nSources` / `_isSpine` / `_edgeDashed` / `_isDivergence`.
Trước đây builder thứ 2 (expanded mode) **thiếu hẳn** các trường này.

### 3.3 Hai lỗi phát hiện khi build (cần ghi nhớ)

**Lỗi 1 — có BA khối chú thích, không phải hai.**
`#lineage-legend-row` (dòng tóm tắt đầu tab) đang ghi "≥2 nguồn / 1 nguồn (chưa đủ)" với `#d4a030` + `#e07820`.
Đặc tả gốc không nhắc tới khối này. Nếu bỏ sót thì mục (2) của `done_when` không đạt.

**Lỗi 2 — `#lineage-canvas` bị xoá `innerHTML` mỗi lần render.**
Có **6 chỗ** gán `canvas.innerHTML = ...` trên `#lineage-canvas` (dòng 6326, 6340, 6794, 7887, 8417, 8426).
Chú thích nổi đặt *trong* `#lineage-canvas` sẽ bị xoá mất ở lần render đầu tiên (khối biến mất, không báo lỗi).
→ Đã chuyển `#lineage-edge-legend-float` ra làm **sibling** của canvas, nằm trong wrapper có `position:relative`.
**Bài học:** bất kỳ phần tử UI nào tự thêm vào vùng canvas của app này đều phải đặt ngoài `#lineage-canvas`.

### 3.4 Quy tắc hiện hành sau khi sửa

| Nguồn ghi nhận | Màu | Kiểu nét | Độ dày |
|---|---|---|---|
| Chỉ DILA | xanh (`--edge-dila`) | liền | thường |
| Chỉ Marcus | vàng (`--edge-marcus`) | liền | thường |
| Chỉ TTL | đỏ (`--edge-ttl`) | liền | thường |
| ≥2 nguồn khớp (cùng ID thầy + cùng ID trò) | trắng/bạc (`--edge-agree`) | liền | thường |
| Trục tổ sư chính (`_isMain`) | **theo nguồn như trên** | liền | **dày nhất** |
| Trục tổ sư không có consensus (`_isSpine`) | `agree` | liền | **dày** |
| 0 nguồn / chưa rõ chiều | xám (`--edge-unknown`) | **đứt** | mảnh |
| Xung đột (2 nguồn chỉ 2 thầy khác) | `#ff7b72` + ⚠ | liền | thường |

**Điểm mấu chốt cần Admin để ý:** nét đứt **không còn** nghĩa là "1 nguồn" nữa. Nét đứt = "chưa rõ chiều".
Cạnh 1 nguồn **vẫn nét liền** (chiều đã rõ, chỉ thiếu nguồn đối chiếu thứ hai). Đây là điểm khác so với
nét đứt theo số nguồn của bản đặc tả cũ — Admin đã chốt cho T410 làm trước T414 nên áp dụng tạm vậy.

## 4. Cảnh báo bắt buộc

- **Không ghi DB.** Task này code-only. Không đụng `lineage_edge_consensus`, `lineage_edge_assertions`, TTL.
- **`npm` shim ở `C:\Windows\system32\npm` hỏng** (không output). Phải chạy thẳng:
  `& "C:\Program Files\nodejs\node.exe" scripts/lint-check.js` và `scripts/e2e-test.js`.
- **`lint` + `e2e` KHÔNG kiểm `places.html`** (chỉ check `placevn.html`, `index.html`, …).
  Phải tự kiểm 3 script block của `places.html` bằng `new Function(code)` — đã làm, 3/3 OK.
- **Có rất nhiều WIP của session khác đang nằm trong worktree** (`git status` dài: `AGENTS.md`, `docs/bugs.md`,
  nhiều file `D` trong `docs/sessions/backup/`, `dashboard_process.html`, `data/progress_data.json`, …).
  **KHÔNG được `git add -A` / `git add -u` / `git add -- docs`.** Phải dùng temp index theo §14/§17.
- `docs/ROLLBACK.md` đang ` M` (session khác sửa). Nếu sửa file này phải dựng từ **nội dung trong index**
  (`git show :Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md`), không lấy worktree — lấy worktree sẽ nuốt WIP của họ.
- Session chạy song song: HEAD có thể dịch chuyển giữa lúc đo và lúc commit. Phải tính lại `(parent, new)` ngay trước commit.
- **Dị vật Unicode:** shell PowerShell ở đây mã hoá ANSI khi chạy `-File` ⇒ **here-string làm hỏng tiếng Việt**.
  Phải dùng `Set-Content -Value "..." -Encoding UTF8` chạy thẳng trong lệnh, hoặc Python/`edit` tool.

## 5. Lệnh revert từng task

```bash
# Cách an toàn nhất: chép lại bản sao trước khi sửa
cp docs/sessions/2026-10-19/places.html.bak-before-T410 places.html
cp docs/sessions/2026-10-19/app.py.bak-before-T410 app.py
# Hoặc revert theo commit
git revert --no-edit <sha_T410>
```

| Task | Thuộc commit | Mất dữ liệu? |
|---|---|---|
| T410 | code (`places.html`, `app.py`) + docs | **Không** — không có migration DB, không đổi schema |

Lưu ý: `places.html.bak-before-T410` là bản **trước T410** nhưng đã chứa WIP của T411 (session khác sửa cùng file).
Revert bằng file backup sẽ **mất phần T411 đã làm trong phiên đó**. Ưu tiên `git revert` theo commit.

## 6. Bảng file tạo/sửa trong session

| File | Hành động |
|---|---|
| `places.html` | Sửa — tokens, 3 legend, `_t410EdgeColor`, `_t410TokenForEdge`, `_t127EdgeStyle`, `afterDrawing`, 3 builder |
| `app.py` | Sửa — `calculate_edge_color_and_divergence()` + 2 call site |
| `tasks/T410-lineage-legend-remove-spine-candidate.md` | Sửa — tiêu đề, `status`, `depends_note`, mục "Kết quả đo được", checklist |
| `docs/sessions/2026-10-19/places.html.bak-before-T410` | Tạo — bản sao 799.782 B, sha256 `8651f81a0ced5e4e` |
| `docs/sessions/2026-10-19/app.py.bak-before-T410` | Tạo — bản sao 1.171.562 B, sha256 `f767c46d719e1ba5` |
| `docs/sessions/2026-10-19/t410_*.png` (6 ảnh) | Tạo — dark/light × 3 nhân vật |
| `docs/sessions/2026-10-19/t410-screenshot-probe.json` | Tạo — giá trị CSS var + nội dung legend thực tế |
| `docs/sessions/2026-10-19_T410-mau-theo-nguon.md` | Tạo — file này |
| `scripts/t410_screenshot.js` | Tạo — script chụp ảnh Playwright (Edge headless) |
| `scripts/_t410_pixel_audit.py` | Tạo — audit pixel màu mới/cũ |
| `scripts/_t410_probe_ids.py` | Tạo — dò ID có cạnh TTL/phụ để làm ảnh kiểm chứng |

## 7. Bài học (sai lầm của chính phiên này)

1. **Tin "2 chỗ legend" mà không grep.** Đặc tả + Admin nói 2 chỗ, thực tế có 3. Phải luôn grep chuỗi hex
   cấm trên **toàn bộ file**, không chỉ vùng được liệt kê. Đã chặn được `#lineage-legend-row` nhờ grep hex.
2. **Đặt phần tử UI vào trong `#lineage-canvas`.** Bị xoá âm thầm vì app gán `innerHTML = ''` ở 6 chỗ.
   Không có lỗi console, không có warning — chỉ biến mất. Cách phát hiện duy nhất: đọc DOM sau render.
3. **`npm run lint` / `npm run e2e` xanh nhưng KHÔNG kiểm file mình sửa.** Tưởng an toàn giả.
   Phải kiểm riêng script block của `places.html`.
4. **Probe `_lineageNetwork.body.edges` trả 0** dù nét vẽ ra thật (pixel audit xác nhận có màu mới).
   Không kết luận "edgeCount=0 ⇒ không có cạnh". Phải cross-check bằng ảnh/pixel.
5. **Ảnh chụp không xem được bằng model này** (`ERROR: Cannot read image`) — phải chuyển sang
   số đo客 quan: pixel count + DOM probe.

## 8. Việc CHƯA xong (theo thứ tự ưu tiên)

1. **`daoanh-qa` kiểm độc lập T410** — bằng chứng đã đủ ở mục 3.3 + 6.
2. **Admin xác nhận DONE** → đổi `status: done` trong `tasks/T410-…md`.
3. **Quyết định gộp `T419` / `T420`** (BUG-041 trùng nhau, cả hai `in_progress`) — vi phạm §16.
4. **Xác nhận ý nghĩa `predicate_conflict = 0`** trong so sánh ZTJ/PTDA (ZTJ không có trường predicate —
   Admin hỏi nhưng chưa trả lời).
5. **Chạy lại T422 pre-check DB** (46.006 → 23.014 distinct pair) — lần trước bị chặn quyền; phải chạy `mode=ro`.
6. **Hồi phục claude-mem** (`POST 127.0.0.1:37700` connection refused) — tasktodo chưa ghi nhận được.
7. **`places.html` và `app.py` cần commit** — đã có WIP của T411 xen vào, cần tách bạch khi commit.

## 9. Lệnh kiểm tra nhanh (agent kế tiếp chạy trong 1 phút)

```bash
cd /opt/.../Dai_Tang_Kinh/daoanh   # hoặc đường dẫn Windows tương ứng

# 1. Repo root đúng SSOT?
git rev-parse --show-toplevel      # phải ra .../visjs-app

# 2. Guard + trùng ID
python -X utf8 scripts/repo_guard.py
python -X utf8 scripts/build_progress_data.py --check-dup-ids

# 3. Không còn hex màu theo số nguồn
python -X utf8 -c "t=open('places.html',encoding='utf-8').read();print({h:t.count(h) for h in ['#e8941a','#e07820','#d4a030','#6b7a8a','#3b82f6','#eab308']})"

# 4. Backend compile + còn token mới không
python -X utf8 -m py_compile app.py
python -X utf8 -c "print(open('app.py',encoding='utf-8').read().count('edge_color_token'))"   # mong đợi 8

# 5. Syntax places.html (npm shim hỏng, chạy node thẳng)
node scripts/lint-check.js && node scripts/e2e-test.js

# 6. Ảnh + audit pixel (cần server đang chạy ở :8080)
node scripts/t410_screenshot.js
python -X utf8 scripts/_t410_pixel_audit.py
```

Kết quả mong đợi: hex cũ = 0 · `edge_color_token` = 8 · lint/e2e exit 0 · `old_single_e07820`/`old_purple_a855f7`/
`old_blue_3b82f6` pixel = 0 ở cả 6 ảnh.

## 10. Ghi chú cho agent kế tiếp

Checklist thao tác:

1. **Đọc `tasks/T410-lineage-legend-remove-spine-candidate.md` trước** — file chứa đầy đủ lịch sử quyết định
   và mục "Kết quả đo được" kèm số đo. Không cần mò lại code.
2. **KHÔNG dùng `git add` trên thư mục.** Repo có WIP của nhiều session. Dùng temp index:
   ```bash
   export GIT_INDEX_FILE="$PWD/../../.git/wt_tmp_index"   # .git của visjs-app
   git read-tree HEAD
   git add -- places.html app.py tasks/T410-lineage-legend-remove-spine-candidate.md docs/sessions/2026-10-19
   git diff --cached --name-only     # PHẢI ra đúng danh sách trên, không hơn
   git commit -m "..."
   unset GIT_INDEX_FILE
   ```
   Nếu `git diff --cached` rỗng ⇒ `git add` đã fail (xem §14) — dừng, không commit.
3. **Nếu phải sửa `docs/ROLLBACK.md` / `docs/tasktodo.md`:** lấy bản trong **index**
   (`git show :Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md > tmp`), thêm phần của mình vào `tmp`, rồi
   `git update-index --add --cacheinfo 100644,<sha>,<path>`. **Không** lấy worktree.
4. **Nếu thêm UI mới lên cây:** đặt NGOÀI `#lineage-canvas` (xem mục 3.3 lỗi 2).
5. **Muốn có ảnh xác minh:** dùng `scripts/t410_screenshot.js` (Playwright + Edge headless).
   Không cài thêm chromium; dùng `channel: 'msedge'`.
6. **T425** (`tasks/T425-edge-columns-and-tree-views.md`) sẽ xây 4 VIEW cây theo nguồn —
   dùng lại đúng bảng token `--edge-*` này để không lệch giữa 2 nơi.


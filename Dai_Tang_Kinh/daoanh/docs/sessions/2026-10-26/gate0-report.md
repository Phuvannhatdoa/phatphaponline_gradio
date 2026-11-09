# Gate 0 — Điều tra T453 (dila_catalog_works) bị mất khỏi app.py

- Ngày: 2026-10-26 · Chế độ: CHỈ ĐỌC (không sửa code, không ghi DB, không git add/commit/reset/checkout/stash/push)
- Git root: `visjs-app` · HEAD tại thời điểm đo: `e4fbc5baac4b4db4ae73e615de65b7d6ea632c7b`
- Đường dẫn trong báo cáo: `Dai_Tang_Kinh/daoanh/...` (tương đối repo root) trừ khi ghi khác.

---

## 0. Tóm tắt 5 câu

1. **Chưa từng được commit.** `git log -S "dila_works_total" -- Dai_Tang_Kinh/daoanh/app.py` không trả về commit nào; `git grep dila_works HEAD -- app.py` không có kết quả. Code T453 chỉ tồn tại trong working tree/backup, chưa bao giờ vào lịch sử. Không có "commit nào làm mất" — nó bị ghi đè trong WIP.
2. **Có đủ 2 khối nguyên văn** trong `docs/sessions/2026-10-25/T445-coder/backup/app.py` (mục 2 bên dưới): (a) route `/daoanh/api/public/dila_works` — 29 dòng (13596–13624); (b) bổ sung `api_global_search` — khối DILA 64 dòng (13511–13574) + 3 key trong `resp` (13580–13582).
3. **DB đã có đủ bảng T453**: `dila_catalog_works` = 5.747 dòng, `dila_catalog_contributors` = 5.589, `dila_catalog_places` = 765. Vì bảng tồn tại, nhánh fallback `except sqlite3.OperationalError` **sẽ không kích hoạt** — route/search sẽ trả dữ liệu thật (ví dụ A000294 Huyền Trang: 78 tác phẩm).
4. **WIP app.py: 248 dòng thêm / 18 dòng xóa (266 dòng thay đổi)** do các phiên khác (T445 wizard, T465/T466, T440-T446 region). **Không có hunk nào** đụng vùng chèn (`api_global_search` 13173–13281, `public_autocomplete` 13032). Rủi ro xung đột vẫn có ở mức "cùng file, cùng commit" nếu commit sweep.
5. **Quan trọng — giả định trong prompt cần sửa:** `daoanh/index.html` (bản đang dùng) **KHÔNG còn gọi** `d.dila_works` hay `/public/dila_works` trên luồng tìm kiếm. T467 (WIP, chưa commit) đã đổi `handleSearch()` sang đọc `monks/works/places`. Chỉ bản sao `docs/sessions/2026-10-26/index.html` (và các `.bak-before-T453-*`) còn gọi `d.dila_works`. Vì vậy **hiện tại HOME không gặp lỗi và không mất gì so với UI đang chạy**; thiếu route chỉ gây hậu quả nếu bản sao T453 được đưa lên thay index.html. Chi tiết mục 5.

---

## 1. Lịch sử git (câu 1)

| Lệnh | Kết quả |
|---|---|
| `git log -S "dila_works_total" --oneline -- Dai_Tang_Kinh/daoanh/app.py` | Không có commit nào |
| `git log --oneline -8 -- Dai_Tang_Kinh/daoanh/app.py` | `7eb88369` (T412/T406) · `b40abd67` (T416) · `a84c8d03` (T427) · `a4397c2a` (cleanup) — 4 commit (git trả về ít hơn 8) |
| `git grep -n "dila_works" HEAD -- Dai_Tang_Kinh/daoanh/app.py` | Không có kết quả |
| `git grep -c "d.dila_works" HEAD -- Dai_Tang_Kinh/daoanh/index.html` | Không có kết quả |
| `git log -S "dila_catalog_works" --all` | **Timeout 120s** — chưa kiểm được toàn bộ nhánh. Xem mục Rủi ro |

**Kết luận câu 1:** T453 không bao giờ được commit vào `app.py`. Hai commit gần đây nhất đụng `api_global_search`/`autocomplete` là `b40abd67` và `7eb88369` — chúng không chứa dila. Code T453 sống trong WIP của phiên T445/T453 và các bản backup `docs/sessions/*`; WIP hiện tại (app.py) đã bị viết đè, nên chỉ còn trong backup. Task `tasks/T453-dila-catalog-a-import-vi.md` ghi "(B) đã làm, Admin duyệt 06:01" nhưng `docs/tasktodo.md` (dòng 12) ghi "(B) chờ duyệt" — hai nguồn mâu thuẫn, cần Admin xác nhận trạng thái thật.

---

## 2. Hai khối code còn thiếu (câu 2)

### Nguồn chuẩn

- **Nguồn chính: `docs/sessions/2026-10-25/T445-coder/backup/app.py`** (26.162 dòng) — có đủ: khối `dila_works` + `dila_works_total` + `dila_people` trong `api_global_search` (13511–13582) và route (13596–13624).
- `docs/sessions/2026-10-25/T445-coder/backup/after-coder-app.py` — cùng nội dung, lệch +24 dòng (13535–13606, 13620–13639). Dùng để đối chiếu, không cần dùng.
- `docs/sessions/2026-10-21/T445-debugger-wip/app.py` — cùng nội dung ở dòng 13511–13624.
- `docs/sessions/2026-10-22/T453/app.py.bak-before-T453-personcard` — **bản cũ hơn** (không có `dila_works_total`, `dila_people`, route ở 13571). **Không dùng.**

**Cảnh báo:** KHÔNG copy nguyên file backup T445 vào app.py. Backup là snapshot cũ: không có `codex_place_name` (T465, WIP hiện tại có ở 12016–12100), nên copy đè sẽ **mất WIP T465/T466**. Chỉ áp 2 khối dưới đây.

### Khối (a) — route mới: `/daoanh/api/public/dila_works`

- Nguồn: `T445-coder/backup/app.py` dòng **13596–13624** (29 dòng), kèm 2 dòng trống 13625–13626.
- **Vị trí chèn:** trong **WIP hiện tại** (`app.py`), chèn NGAY SAU dòng **13282** (dòng trống kết thúc `api_global_search`, sau `conn.close()` của `finally` tại 13280–13281) và TRƯỚC `@app.route('/daoanh/api/public/search')` tại dòng **13283**.
- Phụ thuộc: `get_db_connection` (app.py:176), `sqlite3`, `request`, `jsonify` — đều có sẵn.

```python
@app.route('/daoanh/api/public/dila_works')
def public_dila_works():
    """T453: toàn bộ tác phẩm kinh lục DILA của một người (nút "Xem tất cả" trên HOME).
    GET ?person_id=A000294&sort=juans|year|title"""
    pid = request.args.get('person_id', '').strip()
    sort = request.args.get('sort', 'juans')
    if not pid:
        return jsonify({"success": False, "error": "person_id required"}), 400
    # Năm chỉ là khung triều đại → xếp sau các bộ có năm cụ thể.
    order = {"year": "w.time_from IS NULL, w.year_precision = 'dynasty_range', w.time_from, w.cbeta_id",
             "title": "COALESCE(w.title_vi, w.title_zh)"}.get(sort, "COALESCE(w.juans, 0) DESC, w.cbeta_id")
    conn = get_db_connection()
    try:
        rows = conn.execute(f"""
            SELECT w.cbeta_id, w.title_zh, w.title_vi, w.byline_zh, w.byline_vi, w.dynasty_vi,
                   w.juans, w.time_from, w.time_to, w.year_precision,
                   (SELECT GROUP_CONCAT(COALESCE(m.name_vi, pl.name_zh), ', ')
                    FROM dila_catalog_places pl LEFT JOIN namevi_map_places m ON m.dila_id = pl.place_id
                    WHERE pl.cbeta_id = w.cbeta_id) AS places_vi
            FROM dila_catalog_works w
            WHERE w.cbeta_id IN (SELECT cbeta_id FROM dila_catalog_contributors WHERE person_id = ?)
            ORDER BY {order}
        """, (pid,)).fetchall()
        return jsonify({"success": True, "person_id": pid, "sort": sort,
                        "count": len(rows), "works": [dict(r) for r in rows]})
    except sqlite3.OperationalError:
        return jsonify({"success": True, "person_id": pid, "count": 0, "works": []})
    finally:
        conn.close()
```

### Khối (b) — bổ sung `/daoanh/api/search`

Gồm 2 thao tác trong `api_global_search` (WIP: hàm bắt đầu 13174):

**(b1) Chèn khối tính DILA** — nguồn `T445-coder/backup/app.py` dòng **13511–13574** (64 dòng, gồm dòng trống cuối). Vị trí: **sau** dòng 13263 (`""", (like, like)).fetchall()` của `works = conn.execute(...)`) + dòng trống 13264, **trước** `resp = {` (13265).

```python
        # T453: kinh lục DILA (dila_catalog_works) — additive key, không đổi 3 key cũ.
        # Tên Hán/năm: DILA; title_vi/byline_vi: bản dịch Cloud (unreviewed);
        # tên người: people.name_vi (ZQLOCAL) — badge theo từng nguồn ở UI.
        dila_works = []
        dila_works_total = 0
        try:
            dw_where = """
                WHERE w.title_zh LIKE ? OR w.title_vi LIKE ? OR w.byline_zh LIKE ? OR w.byline_vi LIKE ?
                   OR w.cbeta_id = ? COLLATE NOCASE
                   OR w.cbeta_id IN (SELECT c.cbeta_id FROM dila_catalog_contributors c
                                     WHERE c.name_zh LIKE ? OR c.name_vi LIKE ?)"""
            dw_args = (like, like, like, like, q, like, like)
            # Tổng thật để UI ghi "hiển thị 10 / N" (danh sách vẫn giới hạn 10).
            dila_works_total = conn.execute(
                "SELECT COUNT(*) FROM dila_catalog_works w" + dw_where, dw_args).fetchone()[0]
            rows = conn.execute("""
                SELECT w.cbeta_id, w.authority_id, w.title_zh, w.title_vi, w.byline_zh, w.byline_vi,
                       w.dynasty_vi, w.category_vi, w.juans, w.time_from, w.time_to, w.year_precision,
                       w.vi_source, w.vi_status, w.vol, w.cjk_chars, w.category AS category_zh,
                       json_extract(w.raw_json, '$.orig_category') AS orig_category_zh,
                       json_extract(w.vi_json, '$.orig_category_vi') AS orig_category_vi,
                       (SELECT GROUP_CONCAT(COALESCE(m.name_vi, pl.name_zh), ', ')
                        FROM dila_catalog_places pl LEFT JOIN namevi_map_places m ON m.dila_id = pl.place_id
                        WHERE pl.cbeta_id = w.cbeta_id) AS places_vi
                FROM dila_catalog_works w""" + dw_where + """
                ORDER BY LENGTH(COALESCE(w.title_vi, w.title_zh)) ASC LIMIT 10
            """, dw_args).fetchall()
            for r in rows:
                d = dict(r)
                d["contributors"] = [dict(c) for c in conn.execute(
                    "SELECT c.person_id, c.name_zh, COALESCE(p.name_vi, c.name_vi) AS name_vi, c.name_vi_src "
                    "FROM dila_catalog_contributors c LEFT JOIN people p ON p.id = c.person_id "
                    "WHERE c.cbeta_id = ? ORDER BY c.seq", (d["cbeta_id"],)).fetchall()]
                d["source"] = "DILA_CATALOG"
                dila_works.append(d)
        except sqlite3.OperationalError:
            dila_works = []  # bảng T453 chưa có (DB chưa import) → bỏ qua

        # T453: thẻ người — ai trong kinh lục DILA khớp q (tên Việt DB/tên Hán), kèm tổng tác phẩm và nơi dịch.
        dila_people = []
        try:
            prows = conn.execute("""
                SELECT c.person_id, p.name_vi, p.name_zh,
                       COUNT(DISTINCT c.cbeta_id) AS works, SUM(w.juans) AS juans
                FROM dila_catalog_contributors c
                JOIN dila_catalog_works w ON w.cbeta_id = c.cbeta_id
                LEFT JOIN people p ON p.id = c.person_id
                WHERE c.person_id IN (SELECT person_id FROM dila_catalog_contributors
                                      WHERE name_vi LIKE ? OR name_zh LIKE ?)
                GROUP BY c.person_id ORDER BY works DESC LIMIT 3
            """, (like, like)).fetchall()
            for r in prows:
                d = dict(r)
                d["places"] = [dict(x) for x in conn.execute("""
                    SELECT pl.place_id, pl.name_zh, m.name_vi, COUNT(DISTINCT pl.cbeta_id) AS works
                    FROM dila_catalog_places pl
                    JOIN dila_catalog_contributors c ON c.cbeta_id = pl.cbeta_id
                    LEFT JOIN namevi_map_places m ON m.dila_id = pl.place_id
                    WHERE c.person_id = ? GROUP BY pl.place_id ORDER BY works DESC LIMIT 5
                """, (d["person_id"],)).fetchall()]
                dila_people.append(d)
        except sqlite3.OperationalError:
            dila_people = []

```

**(b2) Thêm 3 key vào `resp`** — nguồn dòng **13575–13583** (backup). Thay `resp = {...}` hiện tại (WIP 13265–13270) bằng:

```python
        resp = {
            "success": True,
            "monks": [dict(r) for r in monks],
            "places": [dict(r) for r in places],
            "works": [dict(r) for r in works],
            "dila_works": dila_works,
            "dila_works_total": dila_works_total,
            "dila_people": dila_people,
        }
```
(Giữ nguyên khối `if lang in ('pa', 'sa')` và `return jsonify(resp)` phía sau.)

**Kiểm tra cột:** đã đối chiếu `PRAGMA table_info` của cả 3 bảng + `people` + `namevi_map_places` — mọi cột được SELECT trong 2 khối đều tồn tại (ví dụ `dila_catalog_places.place_id`, `dila_catalog_contributors.name_vi_src`, `dila_catalog_works.vi_json/raw_json/byline_vi`). Nếu sai cột, `except sqlite3.OperationalError` sẽ nuốt lỗi và trả `[]` im lặng — đây là cạm bẫy cần test khi áp dụng.

---

## 3. Số liệu DB (câu 3)

Mở `data/lineage.db` bằng `file:data/lineage.db?mode=ro` (read-only, không ghi).

| Bảng | Tồn tại | Số dòng |
|---|---|---|
| `dila_catalog_works` | Có | **5.747** |
| `dila_catalog_contributors` | Có | **5.589** |
| `dila_catalog_places` | Có | **765** |
| `people` | Có (bảng gốc) | — |
| `namevi_map_places` | Có (bảng gốc) | — |

Mẫu kiểm: `dila_catalog_contributors` với `person_id = 'A000294'` → 78 dòng, 78 `cbeta_id` distinct. Đây là dữ liệu route `public_dila_works` và thẻ người sẽ trả.

**Kết luận:** bảng đã có ⇒ nhánh fallback "bảng chưa có → bỏ qua" **không chạy**. Khi áp khối (a)+(b), `/daoanh/api/search?q=...` sẽ trả `dila_works`/`dila_people` thật, và `/daoanh/api/public/dila_works?person_id=A000294` trả 78 tác phẩm.

Trạng thái DB khớp T453 (tasks/T453: 9 + 10 + 0 ở lần apply A; về sau mở rộng lên 26 tạng = 5.747 bộ). Không kiểm được số "9 bộ" cũ — chỉ đối chiếu số hiện tại.

---

## 4. Mức WIP app.py (câu 4)

- `git diff --stat HEAD -- Dai_Tang_Kinh/daoanh/app.py` → **1 file, 248 insertions(+), 18 deletions(-)** (266 dòng thay đổi).
- Hunk WIP (`git diff -U0 HEAD`), theo dòng WIP hiện tại:

| Hunk (WIP) | Nội dung (phiên sở hữu, suy từ tên) | Gần vùng chèn? |
|---|---|---|
| 7116–7150 | `api_monk_ancestor_spine` — chọn thầy is_primary | Không |
| 11997–12111 | `api_places_vi_map_list` — T465 (`codex_place_name`), T466 (`ai_place_name`, `_lexicon_han_lookup`) | Không (cách ~1.100 dòng) |
| 24910–24945 | Route wizard T445 (`/daoanh/api/admin/backup` …) | Không |
| 24987–25140 | Route wizard T445 (`schema/update`, `batch/run`, `report`, `export-csv`, `ws/batch-monitor`) | Không |

- **Không có hunk nào** trong: `public_autocomplete` (13032) và `api_global_search` (13173–13281) và vùng chèn route (13282–13283).
- So sánh backup T445 với WIP: `git diff --no-index --stat` → 286 insertions / 498 deletions (backup **cũ hơn**, không phải nguồn để copy đè).

**Rủi ro xung đột với phiên khác:**
- Textual: thấp — hunk không chồng lên vùng chèn.
- Commit sweep: **cao** nếu ai đó chạy `git add app.py` — sẽ commit luôn T445 wizard + T465/T466 + T453 chưa được duyệt. Theo AGENTS §17, phải dùng blob HEAD + khối riêng, không `git add` cả file.
- Ghi đè: nếu phiên T445/T465 lưu lại app.py từ bộ nhớ đệm cũ, khối T453 sẽ mất lần nữa (đúng như đã xảy ra). Nên commit sớm hoặc ghi rõ vào tasktodo.

---

## 5. index.html gọi gì & hậu quả (câu 5)

Có 3 bản index.html, khác nhau:

| File | Trạng thái | Gọi `d.dila_works`? | Gọi `/public/dila_works`? |
|---|---|---|---|
| `daoanh/index.html` (HEAD) | commit `a4397c2a` | Không (git grep HEAD: 0) | Không |
| `daoanh/index.html` (WIP, T467 — uncommitted, +186/−1) | **bản đang dùng** | Không — `handleSearch` (1152–1184) chỉ đọc `d.monks/d.works/d.places` | Không gọi được: `renderDilaWorks(` không còn được gọi; `loadAllWorks` chỉ gắn vào `.dw-btn` do `renderDilaPeople` tạo — chỉ tạo khi `renderDilaWorks` chạy |
| `docs/sessions/2026-10-26/index.html` | bản sao T453 | **Có** (1165–1168) | **Có** (1209) |

Hàm chết còn trong bản đang dùng: `renderDilaPeople` (1232), `loadAllWorks` (1254), `renderDilaWorks` (1275) — định nghĩa nhưng không ai gọi.

**Hậu quả nếu route còn thiếu:**
- **Bản đang dùng (WIP T467): không có hậu quả runtime.** HOME hiện tìm `monks/works/places` (cbeta_catalog_vn), không hỏi phần DILA. Điều này cũng có nghĩa: **hiện trang chủ không hiển thị kinh/người DILA dù DB đã có dữ liệu** — đây là sự kiện do T467 gỡ luồng, không phải do route thiếu.
- **Nếu đưa bản sao `docs/sessions/2026-10-26/index.html` lên:** `/daoanh/api/search` trả thiếu key ⇒ `d.dila_works = undefined` ⇒ mảng rỗng ⇒ luôn redirect sang `/daoanh/places` (HOME mất kết quả kinh DILA + thẻ người). Nếu người dùng bấm "Xem tất cả": `/daoanh/api/public/dila_works` → 404 (HTML) ⇒ `r.json()` lỗi ⇒ hiển thị "Không tải được danh sách." Không crash JS.
- Hệ quả ngược: nếu chỉ khôi phục backend (A/B/C) mà **không** có UI nối lại, API trả key mới nhưng UI bỏ qua — không hỏng gì, nhưng cũng không hiện thêm gì.

**Điểm T467 đã quyết (`tasks/T467-autocomplete-author-khuy-co.md`, dòng 53–84):** ghi rõ "endpoint backend JOIN `dila_catalog_works`... trả `dila_works/dila_people/dila_works_total` — việc này tốn..." và đã chọn bỏ luồng này khỏi trang chủ tạm thời. Quyết định hiện thực hoá T453 (B)+(1)+(2) cần Admin xác nhận lại.

---

## 6. Ba phương án xử lý

### Phương án A — khôi phục ngay vào app.py bằng blob HEAD + 2 khối, không nuốt WIP
- Cách làm: `GIT_INDEX_FILE` tạm (theo AGENTS §14/§17) → `git show HEAD:Dai_Tang_Kinh/daoanh/app.py` ra file tạm → chèn khối (a) sau dòng tương ứng của HEAD và khối (b1)/(b2) vào `api_global_search` của HEAD → `git hash-object -w` → `git update-index --cacheinfo` → commit tạo bằng plumbing (`commit-tree` + `update-ref` CAS thủ công) → sau đó áp đúng 2 khối vào WIP (cùng nội dung, không đổi hunk WIP).
- Ưu: nhanh nhất; khối tách biệt; không đụng 4 hunk WIP; chỉ ghi file + commit, **không mutate DB**.
- Nhược: phải kiểm chặt vị trí chèn trên HEAD (HEAD có thể khác WIP ở dòng); commit app.py tạo thêm lịch sử cho T453 chưa được Admin duyệt (B); cần test `/daoanh/api/search` và `/daoanh/api/public/dila_works` với DB thật.
- Lưu ý: cần ngay Admin xác nhận B là được duyệt (xem mâu thuẫn tasks/tasktodo).

### Phương án B — chờ phiên sở hữu app.py commit WIP, rồi áp 2 khối
- Cách làm: báo phiên T445/T465/T466 commit WIP của mình trước; sau đó áp khối (a)+(b) lên HEAD mới bằng cùng quy trình; kiểm `git diff --stat` còn đúng 2 khối.
- Ưu: không tạo commit trung gian; ít rủi ro xung đột với hunk đang có; chỉ một lần commit sạch.
- Nhược: phụ thuộc thời điểm phiên khác; trong thời gian chờ backend T453 vẫn thiếu (không hại gì vì UI đang dùng không gọi); rủi ro bị ghi đè lần nữa nếu phiên kia lưu bản cũ.

### Phương án C — tách route sang file mới (Blueprint)
- Cách làm: đặt khối (a) vào `api_t453_dila_works.py` (Blueprint, theo mẫu `api_codex_namevi.py`, `api_ttl_profile_v2.py`) và đăng ký trong app.py bằng 1–2 dòng `app.register_blueprint(...)` ở cuối file.
- Ưu: không đụng app.py cho route (a); file mới không có xung đột; dễ revert (xóa file + 1 dòng).
- Nhược: **khối (b) vẫn phải sửa `api_global_search`** trong app.py (không tránh được) ⇒ không giảm rủi ro cho nửa còn lại; route nằm ngoài pattern "toàn bộ business logic ở app.py" của CLAUDE.md (ghi nhận trong lịch sử harness).

### Khuyến nghị
**Phương án A cho backend (cả (a) và (b)), nhưng chỉ sau khi Admin xác nhận T453 (B) là được duyệt** (vì tasks/T453 nói đã duyệt 06:01 còn tasktodo nói chờ duyệt). Lý do: khối tách biệt, additive, không mutate DB, không chồng hunk WIP; API chạy được ngay và đúng với bản sao T453. **Phần UI** (đưa lại luồng kinh/người DILA vào HOME) là quyết định riêng: nó đảo ngược T467 và cần Admin duyệt; không tự sửa index.html.

Nếu Admin muốn tránh mọi commit trung gian trong lúc còn WIP T445/T465/T466: chọn **B**.

---

## 7. Rủi ro còn lại / chưa kiểm

1. **Chưa kiểm toàn bộ nhánh:** `git log -S "dila_catalog_works" --all` timeout 120s — có thể có commit trên nhánh khác. Cần chạy lại riêng (`--all` có thể rất chậm) trước khi kết luận tuyệt đối "chưa từng commit". Với `app.py` trên HEAD hiện tại thì kết luận chắc chắn.
2. **Chưa chạy route thật:** chỉ xác minh schema + đếm dòng. Chưa gọi `/daoanh/api/search` hay `/public/dila_works` để kiểm JSON; không có server đang chạy trong phiên này (không khởi động app để tránh ghi log/DB).
3. **Cạm bẫy `except OperationalError`:** lỗi cột/SQL sẽ thành `[]` im lặng. Cần test có assert số lượng (ví dụ A000294 → 78) khi áp dụng.
4. **Backup T445 cũ:** nguồn khối (a)/(b) là snapshot cũ hơn WIP; tôi đã so khớp các biến dùng (`q`, `like`, `get_db_connection`, `sqlite3`) với WIP — đều có — nhưng không diff toàn bộ hàm `api_global_search` giữa backup và WIP. Nên diff trước khi áp.
5. **Mâu thuẫn trạng thái T453:** `tasks/T453` nói (B) đã duyệt; `docs/tasktodo.md` dòng 12 nói chờ duyệt. Cần Admin xác nhận trước khi restore.
6. **WIP index.html (T467)** chưa commit; nếu T467 được commit với UI hiện tại thì luồng DILA trên HOME bị tắt vĩnh viễn cho tới khi có task UI mới.
7. Không đọc/ghi DB ngoài `mode=ro`. Không chạy pipeline/test (không có mutation nên không cần).

---

## 8. Lệnh kiểm nhanh (cho agent sau, read-only)

```
git grep -n "dila_works" HEAD -- Dai_Tang_Kinh/daoanh/app.py       # kỳ vọng: rỗng (trước khi áp)
git diff --stat HEAD -- Dai_Tang_Kinh/daoanh/app.py                  # kỳ vọng hiện tại: 248+ / 18-
```
DB (từ thư mục daoanh):
```
python -X utf8 -c "import sqlite3; c=sqlite3.connect('file:data/lineage.db?mode=ro', uri=True); print(c.execute('select count(*) from dila_catalog_works').fetchone())"
```
Sau khi áp khối (kỳ vọng):
- `curl -s "http://127.0.0.1:5000/daoanh/api/search?q=Huyền Trang"` → có key `dila_works`, `dila_people`, `dila_works_total`.
- `curl -s "http://127.0.0.1:5000/daoanh/api/public/dila_works?person_id=A000294&sort=juans"` → `count` = 78.

---

## 9. Ghi chú cho agent kế tiếp

- Đừng copy nguyên `T445-coder/backup/app.py` đè app.py — sẽ mất WIP T465/T466/T445-wizard.
- Đừng sửa `docs/sessions/2026-10-26/index.html` và coi nó là bản "đúng" — đây là bản sao T453 cũ; bản đang dùng là `daoanh/index.html` (T467).
- Đừng `git add app.py` cả file (AGENTS §17).
- Trước khi commit kiểm `git rev-parse HEAD` và `git diff --cached --name-status`.
- File này KHÔNG được commit trong phiên điều tra này.

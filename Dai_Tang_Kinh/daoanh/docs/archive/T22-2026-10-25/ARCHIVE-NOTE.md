# ARCHIVE NOTE — Toàn bộ code T22 (Founding Date Pipeline) đã dừng và lưu trữ

| Trường | Giá trị |
|---|---|
| Ngày lưu trữ | **2026-10-25** |
| Quyết định của | **Admin** (yêu cầu trực tiếp trong phiên 2026-10-25 19:59) |
| Task bị ảnh hưởng | **T22** — `tasks/T22-nlp-fosi-zhi-founding-dates.md` |
| Trạng thái T22 sau lưu trữ | `deferred` — **dự án tương lai**, chỉ mô tả, **không code** |
| DB mutation | **0** — không xoá/sửa dòng nào trong `data/lineage.db` |
| Code production bị ảnh hưởng | **0** — `app.py`, `places.html`, `index.html` không đụng tới |
| Manifest hash | `docs/archive/T22-2026-10-25/MANIFEST.md` — bản `manifest.json` cùng nội dung **bị `.gitignore:6` (`*.json`) bỏ qua**, nên bản `.md` mới là bản được commit |

---

## 1. Quyết định

1. **Ngừng toàn bộ code liên quan tới T22.** Không chạy lại, không mở rộng, không bảo trì.
2. **Regex tự chế bị bác bỏ vĩnh viễn** cho bài toán năm thành lập: trên dữ liệu thật, regex không
   bắt được niên đại chính xác (xem §2), và mọi heuristic "đoán năm" đều đã sinh dữ liệu sai.
3. **T22 trở thành dự án tương lai**: mô tả lại thành *tìm repo/công trình khoa học tương đương để
   tích hợp*, thay vì tự viết extractor.
4. **Lưu trữ, không xoá cứng.** Code chuyển ra khỏi `scripts/` (không còn trong đường chạy), giữ
   nguyên từng byte + SHA256 để đối chiếu/hoàn nguyên nếu Admin đổi quyết định.

---

## 2. Vì sao dừng — bằng chứng đo được (không phải cảm tính)

| Bằng chứng | Số liệu / nguồn |
|---|---|
| 1.471 event `dila_era_name` sinh năm thành lập **từ tên triều đại** | **1.385 row (94,2%)** không lấy được năm từ note; **1.272 note không có marker thành lập nào** ⇒ sự kiện `founding` **vô căn cứ** (`tasks/T22…:40-42`) |
| Nhãn ghi "NNNN年建" = mệnh lệnh sai (năm đầu đời ghép với "đã xây năm NNNN") | 781 nhãn chứa `年建` trước sửa (`T22…:63`) |
| Regex không đổi được niên hiệu + số Hán sang năm | 125 place viết bằng `明成化九年` / `萬曆三十八年` / `明初` — không có bảng nào đổi được; `time_periods` gốc: 123 dynasty / 815 era / 570 emperor đều `start_year=NULL` (`T22…:26-34`) |
| Heuristic "midpoint triều đại" cũng sai | 24/29 dòng lô A có năm = điểm giữa triều đại, tức **giá trị suy ra** (`tasks/T265-h3-year-support-plan.md:78`) |
| Năm trong ngoặc thường là năm **trùng tu/tái tạo**, không phải thành lập | 5 row điển hình 1867 / 1274 / 1655 / 1046 / 1567 (`T22…:84-90`); ví dụ `PL000000000112` (明) y=1421 là năm **dời đô**, không phải năm lập chùa (`T22…:92-94`) |
| "226 place cần mở rộng regex" của T224 bị thổi phồng | đo lại chỉ **36** có năm Ả Rập (nhiều cái sai), **125** không có năm, 35 chỉ có trong `raw_xml` (`T22…:17-29`) |
| Chính liều thuốc cũ đã bị revert/lùi | DB đang chạy: 3.688 event (founding 3.647), **0** `era_mention`, `time_periods` chỉ còn 117.429 dòng `DILA`; bản 2026-10-11 có 4.386 event / `era_mention` 1.396 / 258 dòng era + 285 quyết định T265 — **mất sau sự cố `lineage.db.CORRUPTED_20261011`** (chi tiết: `docs/Handoff-2026-10-25-T22-parked.md` §3) |

> Kết luận: hướng "regex + bảng tra tự dựng" **không thể** cho ra năm thành lập đáng tin ở quy mô
> 59K place. Đó là lý do chuyển sang hướng **tích hợp công trình có sẵn** trong mô tả mới của T22.

---

## 3. Danh mục code đã lưu trữ (7 file, chuyển khỏi `scripts/`)

| File gốc | Nơi lưu | Byte | SHA256 (rút gọn) |
|---|---|---:|---|
| `scripts/t22_ld1_fix_era_name_founding.py` | `docs/archive/T22-2026-10-25/scripts/` | 20.831 | `1b676ef9efcee517…` |
| `scripts/t22_ld2_dynasty_era_lookup.py` | nt | 27.575 | `e3882b648c0deee7…` |
| `scripts/t22_ld3_review_remaining.py` | nt | 6.032 | `c48dd98d2fafb5f2…` |
| `scripts/t22d_regex_dila_notes.py` | nt | 7.038 | `d4687a1afb57c64b…` |
| `scripts/t80_founding_coverage.py` | nt | 7.735 | `5d2aa7c91f635e9c…` |
| `scripts/dila_note_founding_extract.py` | nt | 23.127 | `065ec87a1529dbfb…` |
| `scripts/dila_dynasty_range_extract.py` | nt | 9.797 | `ee75ade443153fc9…` |

Hash đầy đủ trong **`MANIFEST.md`** (bản commit được). `manifest.json` cùng thư mục là bản máy đọc
cùng nội dung, nhưng **không được commit** vì `.gitignore:6` chặn `*.json`. Mỗi lần move đều verify
`sha256(trước) == sha256(sau)` = OK.

### 3.1 KHÔNG lưu trữ (có lý do — không phải bỏ sót)

| File | Vì sao giữ | Ghi chú |
|---|---|---|
| `scripts/dila_era_name_extract.py` | **Có 3 script khác đang import**: `scripts/t32_audit.py:85`, `scripts/t44_extract_destruction.py:61`, `scripts/t44_gen_candidates_tsv.py:20` (T32/T44 là task riêng, đang mở) | Xoá/archiving bây giờ = vỡ 3 script. Đề nghị Admin: hủy luôn khi T44/T32 đóng, hoặc cấp task riêng để gỡ import |
| `scripts/t251_ld2_era_gap.py`, `scripts/t252_w3_era_gap.py` | Thuộc T251/T252 (đã đóng), không phải code T22 | T22 **không** dùng nữa; nếu Admin muốn hủy cả chuỗi LD2 thì nói rõ |
| `scripts/t44_*.py`, `scripts/t32_*.py` | Task riêng (destruction events / audit), khác miền | Không thuộc T22 |
| `app.py` route `/daoanh/api/places/<place_id>/timeline` (`app.py:8561`), `/map-timeline` | Lớp **hiển thị** dùng chung cho T21/T56/T97 — đã chạy production | Giữ nguyên, **không mở rộng** |
| `places.html` tab "Niên Đại", `index.html` | idem | Giữ nguyên |

### 3.2 Artifact dữ liệu của hướng cũ (giữ tại chỗ, `data/` bị gitignore)

| File | Vai trò |
|---|---|
| `data/t22_ld1_fix_log.json` (359 KB) | log từng row của lần sửa 1.471 event era-name |
| `data/t22_phase2_review.json` (1,2 KB) | 5 row `dila_founding_phase2` nghi vấn |
| `data/t22_ld3_review.json` (31 KB) | danh sách row cần rà tay (N1/N2/N3) |
| `data/backups/lineage_t22ld1_*.db`, `lineage_t22ld2_*.db` | snapshot trước/sau của hướng cũ |

Không xoá: đây là **bằng chứng** cho việc vì sao hướng này bị bác bỏ. Nếu cần giải phóng dung lượng,
xoá sau khi Admin xác nhận (không ảnh hưởng git).

---

## 4. Hoàn nguyên (nếu Admin đổi quyết định)

```powershell
cd "E:\...\visjs-app\Dai_Tang_Kinh\daoanh"
# cách 1 — chép ngược từ archive (giữ byte gốc, đã verify SHA256 trong manifest.json)
python -X utf8 -c "import json,shutil,os; m=json.load(open('docs/archive/T22-2026-10-25/manifest.json',encoding='utf-8')); [shutil.copy2(os.path.join('docs','archive','T22-2026-10-25','scripts',os.path.basename(x['archived_as'])), x['src_rel']) for x in m['files']]"
# cách 2 — nếu đã commit phần archive: git checkout <sha-truoc> -- Dai_Tang_Kinh/daoanh/scripts/<file>
```

Kiểm sau hoàn nguyên: `python -X utf8 -c "import glob;print(len(glob.glob('scripts/t22_*.py')))"` → 4.

> ⚠️ Hoàn nguyên **code** không hoàn nguyên **dữ liệu**: DB hiện tại đã ở baseline trước sửa
> (3.688 event). Chạy lại `t22_ld1 --apply` trên DB này sẽ tạo lại đúng loại dữ liệu vừa bị bác bỏ.

---

## 5. Điều đã bị bác bỏ — ghi lại để không ai làm lại

1. ❌ Regex `（(\d{3,4})年）` suy ra năm thành lập từ `places_dila.note` (T22d / Layer D).
2. ❌ "Bảng tra triều đại tự dựng" + gán năm = **đầu/midpoint triều đại** (T22-LD2, T251, T252).
3. ❌ Nhãn tự sinh kiểu `… (NNNN年建)` khi note không nói năm xây.
4. ❌ Ollama `qwen2.5:7b` đọc `raw_xml` để đoán năm (Layer E bản cũ) — thay bằng hướng tích hợp nguồn
   có thẩm quyền (xem mô tả mới T22) hoặc dùng cổng dịch T447 nếu buộc phải đọc văn bản.
5. ❌ Cơ chế `verification_status='candidate|approved'` + `pipeline_runs` + review-queue tự xây:
   cột/bảng này **chưa từng tồn tại** trong `place_timeline_events` thật (schema thật:
   `id,dila_id,event_type,year,year_end,label_zh,label_vi,source,source_ref,confidence TEXT,created_at`).
6. ❌ Coi "226 place" của T224 là backlog regex hợp lệ (đã đo lại: 36 có năm, phần lớn sai).

---

## 6. Liên quan

- Mô tả mới của T22: `tasks/T22-nlp-fosi-zhi-founding-dates.md`
- Bàn giao chi tiết phiên 2026-10-25: `docs/Handoff-2026-10-25-T22-parked.md`
- Era/niên hiệu có nguồn thẩm quyền: **T452** (DILA Time Authority, `deferred`)
- Cổng dịch/LLM dùng chung (nếu sau này cần đọc văn bản): **T447**
- Kho quyết định năm (mô hình mới, thay review-queue): **T265** `timeline_year_support`
- Data-honesty gate đã có: **T234** (archived) + guard **T449**

# Handoff 2026-10-25 — T22 dừng code, chuyển thành dự án tương lai

## 1. Bảng thông tin đọc nhanh

| Trường | Giá trị |
|---|---|
| Ngày bàn giao | **2026-10-25** (phiên 19:42–20:10, GMT+7) |
| HEAD lúc bàn giao | `47c5ef719d44857cff5dd99fde89d574c5b8b4bc` — *chưa commit gì trong phiên này* |
| Session đã làm | T22: phân tích mô tả + so trùng T4xx → **Admin quyết dừng code, lưu trữ, chuyển dự án tương lai** |
| Test đã chạy | `python -X utf8 scripts/build_progress_data.py --check-dup-ids` → **[OK] Không có task ID trùng thật** |
| Test CHƯA chạy | `npm run pipeline` — **không cần**: 0 dòng code/JS/HTML production bị sửa (chỉ move script CLI + docs) |
| DB | **0 mutation**. Chỉ đọc `mode=ro`. Không backup mới (không có gì để revert) |
| TTL | **0 mutation** |
| Phạm vi ghi | `tasks/T22-*.md` (viết lại) · `docs/tasktodo.md` (1 block + 1 dòng) · `docs/archive/T22-2026-10-25/**` (mới) · `scripts/` (7 file **rời đi**) · handoff này |

---

## 2. Đọc trong 2 phút

### Đã làm gì

1. **Dừng toàn bộ code T22.** 7 script pipeline founding-date chuyển khỏi `scripts/` →
   `docs/archive/T22-2026-10-25/scripts/`, kèm `manifest.json` có SHA256 từng file (verify
   `sha(after) == sha(before)` = OK, 0 byte sai lệch).
2. **Viết lại mô tả T22** (`tasks/T22-nlp-fosi-zhi-founding-dates.md`) thành **dự án tương lai**:
   status `deferred`, ưu tiên `low`, nội dung là *tìm & tích hợp công trình tương đương* (R0→R3 có
   cổng duyệt), **không code**. Toàn bộ spec cũ 5-layer (kèm các đoạn Python) đã bị gỡ khỏi task.
3. **Lưu trữ note**: `docs/archive/T22-2026-10-25/ARCHIVE-NOTE.md` — vì sao dừng (số đo cụ thể),
   danh mục code + hash, danh mục **cố ý không lưu trữ**, cách hoàn nguyên, danh sách **điều đã bị
   bác bỏ** để không ai làm lại.
4. **Cập nhật `docs/tasktodo.md`**: block T22 "in_progress / đã sửa 1.440 event" → block
   "`deferred` — dự án tương lai" + số đo hiện trạng; sửa thêm 1 dòng T22 ở mục cuối file.

### Phát hiện quan trọng nhất của phiên

**Không có task T4xx nào trùng toàn bộ T22** (quét 45 file `T4*.md`): **0 DUPLICATE**, **1
DEPENDENCY-OWNER**, 8 OVERLAP-PARTIAL, 19 FILE-CONFLICT.
Trong đó **T452** (DILA Time Authority reimport, `deferred`) chính là "nút thắt bảng tra niên hiệu"
mà T22 từng coi là blocker số 1. Ngoài ra: 15 task T4xx cùng ghi `app.py`, 7 task ghi `places.html`,
3 task ghi `index.html` ⇒ mọi việc UI của T22 phải xếp sau, không chen ngang.

### 3 việc Admin cần làm ngay

1. **Đọc 5 câu hỏi §9 trong `tasks/T22-…md`** — đặc biệt câu 4: xử lý 2.322 dòng `founding` do
   heuristic cũ sinh ra (giữ + badge / ẩn / tách bảng / xoá). Hiện **chưa làm gì**.
2. **Quyết có mở R0 (khảo sát nguồn) không**, và cấp ID riêng hay làm trong chính T22.
3. **Quyết số phận `scripts/dila_era_name_extract.py`** — file **cố ý không lưu trữ** vì
   `t32_audit.py:85`, `t44_extract_destruction.py:61`, `t44_gen_candidates_tsv.py:20` đang import.

---

## 3. Số đo xác lập trong phiên (để agent sau không phải đo lại)

### 3.1 Hiện trạng `data/lineage.db` (đọc `mode=ro`, WAL = 0 byte)

| Chỉ số | Giá trị |
|---|---|
| `place_timeline_events` | **3.688** (founding 3.647 · dissolved 41) |
| Place có ≥1 event | **3.534** ≈ **5,97%** của 59.167 |
| `source` | `dila_era_name` 1.471 · `dila_dynasty` 851 · `dila_note` 719 · `dila_note_regex` 276 · `wikidata` 155 · `wikidata_p571` 146 · `dila_founding_phase2` 55 · `dila_fosizhi` 15 |
| `created_at` mới nhất | tháng **2026-08/09** (không có dòng nào của tháng 10) |
| `event_type='era_mention'` | **0** |
| `timeline_year_support` (T265) | **không có bảng** |
| `time_periods` | 117.429 dòng, **toàn bộ** `source_origin='DILA'` (không còn dòng `t22_ld2_historical` / `t251…` / `t252…` / `era_catalog`) |

### 3.2 DB đã bị lùi ngày 2026-10-12 (bằng chứng, không sửa)

| DB | `place_timeline_events` | `era_mention` | `timeline_year_support` | `time_periods` ngoài DILA |
|---|---:|---:|---:|---:|
| `data/backups/lineage.T265-lo-D-20261011-101118.db` | 4.386 | 1.396 | 285 | 258 |
| `data/backups/lineage_2026-10-12.db` | 3.688 | 0 | không có | 0 |
| `data/lineage.db` (đang chạy) | 3.688 | 0 | không có | 0 |

`data/lineage.db.CORRUPTED_20261011` mở ra = `database disk image is malformed`. ⇒ Bản khôi phục
2026-10-12 lấy từ snapshot **trước 2026-10-05**, làm mất công của T22-LD1/LD2, T44, T251, T252, T265.

> **Quyết định phiên này: KHÔNG khôi phục.** Các dòng mất thuộc đúng hướng heuristic vừa bị bác bỏ.
> Ghi lại đây để (a) không ai tưởng T44/T251/T252/T265 "đã xong trên DB", (b) nếu Admin đổi ý thì
> nguồn phục hồi là file backup 4.386 dòng ở trên (additive, dry-run được).

---

## 4. Cảnh báo bắt buộc

1. **`scripts/t22_*.py` KHÔNG còn tồn tại** — nếu thấy lệnh/script/doc nào nhắc chạy chúng, đó là
   tài liệu lịch sử. Đường dẫn mới: `docs/archive/T22-2026-10-25/scripts/`.
2. **Đừng "sửa nhanh" bằng cách chạy lại script cũ trên DB hiện tại.** DB đang ở baseline trước sửa;
   chạy `t22_ld1 --apply` sẽ tái tạo đúng loại dữ liệu vừa bị bác bỏ (đã ghi trong archive note §4).
3. **`dila_era_name_extract.py` vẫn nằm trong `scripts/`** (T44/T32 import). Đừng xoá khi chưa gỡ import.
4. **Git: 0 commit trong phiên.** Worktree dùng chung, HEAD `47c5ef71`. Phần archive + task + tasktodo
   đang là thay đổi chưa stage; **không** `git add -A`/`git add docs tasks` (AGENTS §17 sẽ nuốt WIP
   của session song song).
5. **`docs/tasktodo.md` là file tranh chấp.** Bản trước khi sửa: `%TEMP%\tasktodo.before-T22-park.md`.
   Nếu session khác ghi đè, rebase block T22 (từ `### T22 — 2026-10-25` đến `### T356`).
6. **`data/progress_data.json` KHÔNG regenerate** (cố ý) để không nuốt WIP session khác. Khi rảnh:
   `python -X utf8 scripts/build_progress_data.py`.
7. **`docs/archive/T22-2026-10-25/manifest.json` KHÔNG được commit** (`.gitignore:6` chặn `*.json`).
   Bản commit được là `MANIFEST.md` cùng thư mục. Nếu clone repo mới mà thiếu `manifest.json`, đọc
   `MANIFEST.md` để lấy hash; script verify trong §9 đọc `manifest.json` nên phải chạy trên máy này
   (hoặc dựng lại `manifest.json` từ bảng hash trong `MANIFEST.md`).

---

## 5. Lệnh revert từng phần

| Phần | Lệnh | Mất dữ liệu? |
|---|---|---|
| Code (7 file) về `scripts/` | theo `manifest.json` (xem ARCHIVE-NOTE §4) | Không — byte gốc, có SHA256 |
| `tasks/T22-…md` | `git checkout HEAD -- Dai_Tang_Kinh/daoanh/tasks/T22-nlp-fosi-zhi-founding-dates.md` (nếu đã commit thì `git show HEAD~1:…`) | Không |
| `docs/tasktodo.md` | chép lại `%TEMP%\tasktodo.before-T22-park.md` (đối chiếu trước khi đè — file có thể đã bị session khác sửa) | Không |
| `docs/archive/T22-2026-10-25/**` | xoá thư mục (nếu coi là rác) — **không khuyến nghị** | Mất hash/evidence |
| DB | không có gì để revert | — |

---

## 6. File tạo / sửa trong phiên

| File | Trạng thái | Ghi chú |
|---|---|---|
| `tasks/T22-nlp-fosi-zhi-founding-dates.md` | **viết lại toàn bộ** (684 → ~230 dòng) | `in_progress` → **`deferred`**, chỉ còn mô tả + chặng R0–R3 |
| `docs/archive/T22-2026-10-25/ARCHIVE-NOTE.md` | **mới** | vì sao dừng, danh mục, hash, revert, điều bị bác bỏ |
| `docs/archive/T22-2026-10-25/MANIFEST.md` | **mới** | Bản commit được của manifest: 7 file × {đường dẫn gốc, nơi lưu, byte, sha256 đầy đủ, move_ok} |
| `docs/archive/T22-2026-10-25/manifest.json` | **mới (không commit)** | Bản máy đọc cùng nội dung — **bị `.gitignore:6` (`*.json`) bỏ qua**, git không thấy. Không xoá: script verify/revert đọc file này |
| `docs/archive/T22-2026-10-25/scripts/*.py` | **mới (nhận 7 file)** | `t22_ld1…` `t22_ld2…` `t22_ld3…` `t22d_regex…` `t80_founding…` `dila_note_founding…` `dila_dynasty_range…` |
| `scripts/t22_ld1_fix_era_name_founding.py` và 6 file khác | **đã rời đi** | `git status` sẽ thấy `D` (deleted) + `??` (archive) cho tới khi commit |
| `docs/tasktodo.md` | sửa 2 chỗ | block T22 + 1 dòng ở mục "task đang treo" cuối file |
| `docs/Handoff-2026-10-25-T22-parked.md` | **mới** | file này |

---

## 7. Sai lầm tự mình làm trong phiên + bài học

1. **Tạo nhầm thư mục lồng `daoanh/daoanh/`.** Script lưu trữ đầu tiên dùng đường dẫn tiền tố
   `daoanh/...` trong khi `cwd` đã là `...\Dai_Tang_Kinh\daoanh` ⇒ tạo
   `daoanh\daoanh\docs\archive\...\manifest.json` rỗng. **Đã kiểm đường dẫn tuyệt đối rồi `rmtree`
   đúng thư mục vừa tạo** (chỉ chứa 1 file manifest rỗng của chính nó), sau đó chạy lại với `cwd` đúng.
   *Bài học:* sau khi `cd` vào project, mọi path tương đối bỏ tiền tố `daoanh/`; và sau mỗi script
   ghi file phải `os.path.abspath` in ra để soát.
2. **Đoán sai tên file** `22d_regex_dila_notes.py` (thực tế là `t22d_regex_dila_notes.py`) ⇒ lần move
   đầu báo `MISSING` 1 file. Đã glob lại và move bổ sung, manifest cập nhật lên 7 file.
   *Bài học:* danh sách file để archive phải sinh bằng `glob`, không gõ tay.
3. **Suýt kết luận sai "T22 chưa từng được áp dụng".** Lần đọc DB đầu chỉ thấy 3.688 event và dễ kết
   luận "chưa làm". Phải đọc chéo backup 10-11 mới thấy 4.386 event + 285 dòng quyết định ⇒ sự thật
   là **đã làm rồi bị lùi ngày 10-12**. *Bài học:* khi thấy "task nói đã xong mà DB không có", phải
   so ít nhất 2 snapshot trước khi kết luận.
4. **Không chạy `npm run pipeline`.** Đúng chủ ý (0 code production đổi) nhưng phải ghi rõ để không ai
   hiểu là "pipeline PASS" (AGENTS: không claim PASS khi gate không chạy).
5. **`manifest.json` bị `.gitignore` nuốt.** Phát hiện muộn khi `git ls-files --others` không thấy file
   manifest ⇒ đã sinh thêm `MANIFEST.md` để hash có trong git. *Bài học:* mọi artifact mới dạng
   `.json` trong repo này phải kiểm `git check-ignore -v` trước khi coi là "đã lưu".
6. **`git diff --name-status` trong repo này rất nhiễu** — hiện hàng trăm `D` của task/session cũ (di
   chứng index bất thường + file đã move tay chưa commit của các session trước), **không phải** do
   phiên này. Chỉ đọc phần đúng đường dẫn mình đụng tới (§6), đừng `git add -A` để "dọn".

---

## 8. Việc CHƯA xong (thứ tự ưu tiên)

| # | Việc | Cần ai quyết |
|---|---|---|
| 1 | 5 câu hỏi ở `tasks/T22…§9` (đặc biệt: 2.322 dòng heuristic xử lý thế nào) | **Admin** |
| 2 | Có mở **R0 — khảo sát nguồn** không? Cấp ID riêng (đề nghị **T464**) hay làm trong T22? | **Admin** |
| 3 | `dila_era_name_extract.py`: giữ tới khi T44/T32 đóng, hay cấp task gỡ import để hủy luôn? | **Admin** |
| 4 | Commit phần archive + task + tasktodo (scoped, từng file, theo AGENTS §14) | Admin/dev |
| 5 | Regenerate `data/progress_data.json` | dev (khi không có session song song) |
| 6 | (Tuỳ chọn) Dọn artifact cũ `data/t22_ld1_fix_log.json`, `data/t22_phase2_review.json`, `data/t22_ld3_review.json`, `data/backups/lineage_t22ld1_*` — **giữ lại vì là bằng chứng** | Admin |

---

## 9. Lệnh kiểm tra nhanh (1 phút)

```powershell
cd "E:\...\visjs-app\Dai_Tang_Kinh\daoanh"

# 1) code cũ đã rời scripts/ và nằm đúng archive chưa
python -X utf8 -c "import glob,os;print('scripts t22:',glob.glob('scripts/t22_*.py'));print('archive:',sorted(os.listdir('docs/archive/T22-2026-10-25/scripts')))"

# 2) hash archive khớp manifest
python -X utf8 -c "import json,hashlib,os;m=json.load(open('docs/archive/T22-2026-10-25/manifest.json',encoding='utf-8'));print([(os.path.basename(x['archived_as']), hashlib.sha256(open(os.path.join('docs/archive/T22-2026-10-25/scripts',os.path.basename(x['archived_as'])),'rb').read()).hexdigest()==x['sha256']) for x in m['files']])"

# 3) task T22 đã là deferred + không còn code Python trong mô tả
python -X utf8 -c "s=open('tasks/T22-nlp-fosi-zhi-founding-dates.md',encoding='utf-8-sig').read();print('status deferred:', 'status: deferred' in s, '| python block:', '```python' in s)"

# 4) không còn block T22 in_progress trong tasktodo
python -X utf8 -c "s=open('docs/tasktodo.md',encoding='utf-8').read();print('old header gone:', 'T22 — 2026-10-05' not in s, '| new header:', 'DỰ ÁN TƯƠNG LAI' in s)"

# 5) ID không trùng
python -X utf8 scripts/build_progress_data.py --check-dup-ids
```

---

## 10. Ghi chú cho agent kế tiếp

- **T22 = task mô tả, KHÔNG phải task code.** Nếu user yêu cầu "làm T22", việc đúng là **R0 khảo sát
  nguồn** (đọc tài liệu/web, chấm điểm theo §5 của task), không phải viết extractor.
- Muốn hiểu vì sao: đọc `docs/archive/T22-2026-10-25/ARCHIVE-NOTE.md` §2 (số đo) và §5 (danh sách
  điều bị bác bỏ). Đừng đọc lại spec cũ — spec cũ đã bị gỡ khỏi task.
- Nếu phải đụng `place_timeline_events`: schema thật không có `verification_status` / `evidence_text`
  / `pipeline_run_id`; quyết định năm đi qua `timeline_year_support` (T265).
- Nếu phải đọc văn bản Hán để lấy năm: dùng **cổng T447**, không dựng LLM pipeline riêng; và nhớ
  nguyên tắc "thiếu còn hơn sai".
- Trước khi commit: HEAD có thể đã dịch (worktree dùng chung). Chỉ stage đúng các file ở §6.

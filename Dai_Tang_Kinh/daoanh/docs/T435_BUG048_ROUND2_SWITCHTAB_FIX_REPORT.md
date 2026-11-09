# T435 / BUG-048 — Vòng 2: Fix switchTab() không reload đủ hàm khi quay lại tab ETL

Ngày: 2026-10-20
Task: `daoanh/tasks/T435-bug048-claude-column-no-count.md` (phần "Audit lại 2026-10-20 (vòng 2)")

## 1. Files changed

- `daoanh/admin/namevimap.html` — sửa nhánh `else` trong `switchTab()` (khoảng dòng 1041-1049).
- Backup trước khi sửa: `daoanh/docs/sessions/2026-10-20/T435/namevimap.html.v2.bak`
  (giữ nguyên bản `.bak` vòng 1, không ghi đè).

Không đổi `app.py`, không đổi API, không đổi schema — đúng phạm vi đã duyệt.

## 2. Root cause đã xác minh

Lớp lỗi: **resolver/JS state** (tab re-entry không đồng bộ danh sách hàm cần tải lại), không
phải data/API (API + HTML span + `loadCodexColStatus` đã đủ từ vòng 1 — verify lại bằng grep
trước khi sửa: `app.py:16318`, `namevimap.html:726`, `namevimap.html` có `loadCodexColStatus`).

Chi tiết: `switchTab()` có 2 đường vào tab ETL:
- Lần đầu (`etlTabLoaded === false`): gọi `_etlFullLoad()` — tải đủ 5 hàm
  (`loadEtlStats`, `loadEtlFlagLiveData`, `etlFlagQueueLoad`, `loadAiColStatus`,
  `loadCodexColStatus`) dùng chung 1 `AbortSignal`.
- Lần sau (`etlTabLoaded === true`, nhánh `else`): **chỉ gọi `loadEtlFlagLiveData(sig)`**
  với `sig` MỚI từ `_etlNewAbortSignal()`. Hàm này luôn `abort()` controller cũ trước khi
  tạo controller mới — nếu lượt vào tab trước đó chưa tải xong `etlFlagQueueLoad`/
  `loadAiColStatus`/`loadCodexColStatus`, 3 request này bị abort vĩnh viễn, không ai gọi lại
  (nhánh `else` không có code gọi 3 hàm đó) → header CLAUDE/GEMINI trống, bảng "Bulk FLAG
  Queue" kẹt "Đang tải…".

Verify đã tái hiện đúng bằng Browser pane thật (xem mục 4).

## 3. Thay đổi chính (before/after)

**Before** (`namevimap.html`, nhánh `else` trong `switchTab()`):
```js
} else {
    const sig = _etlNewAbortSignal();
    loadEtlFlagLiveData(sig); // re-sync FLAG table mỗi lần switch lại
}
```

**After**:
```js
} else {
    // T435/BUG-048 vòng 2 (2026-10-20): ... dùng chung _etlFullLoad() để luôn tải
    // lại đủ cả 5 phần. KHÔNG gọi etlSelectStep(0) ở đây (khác nhánh if) để không
    // reset step UI nếu Admin đang xem dở một bước khác.
    _etlFullLoad();
}
```

`_etlFullLoad()` tự set `etlTabLoaded = true` (idempotent, không có side-effect mới) và gọi
đủ cả 5 hàm với 1 `AbortSignal` chung. Khác với nhánh `if`, nhánh `else` **không** gọi
`etlSelectStep(0)` — giữ nguyên lo ngại trong task: không reset PIPELINE step UI nếu Admin
đang xem dở bước khác khi quay lại tab.

Không đổi contract API nào — vẫn dùng đúng các hàm/endpoint có sẵn, chỉ sửa danh sách hàm
được gọi lại khi tab re-entry.

## 4. Kết quả test (Browser pane thật, có network log)

1. **Lần đầu vào tab ETL**: header hiện `CLAUDE (48,646/48,673)` và
   `GEMINI (48,673/48,673)`, Bulk FLAG Queue load đủ data (319 FLAG chưa duyệt, trang 1/7).
2. **Case tái hiện bug** (chuyển sang tab "Danh sách chờ mapping" rồi quay lại tab ETL
   ngay lập tức, trước khi lượt tải đầu xong):
   - Network log xác nhận `GET /api/admin/codex-transliterate/status` bị abort 2 lần
     (`net::ERR_ABORTED`) nhưng có request cuối trả `200 OK` (không chỉ abort rồi im lặng).
   - `GET /api/admin/namevi/flag-list?...hide_done=true` cùng pattern: abort rồi có bản
     200 OK.
   - Sau fix: header CLAUDE/GEMINI vẫn hiện đúng số, Bulk FLAG Queue load đủ (không kẹt
     "Đang tải…" vĩnh viễn).
3. **Edge case — chuyển tab qua lại nhanh 3-4 lần** (ETL → Xác Minh → ETL → Place → ETL →
   Danh sách chờ mapping → ETL):
   - `codex-transliterate/status` có 4 abort + 2 request 200 OK (không có request nào bị
     abort mà không có bản thay thế thành công).
   - `flag-list` tương tự: nhiều abort nhưng request cuối luôn 200 OK.
   - Không regression: tab Xác Minh hiện badge "346" đúng, tab Place/Queue vẫn hoạt động
     bình thường, các số liệu khác trong tab ETL (TTL files on disk=0, Đã link DILA ID=811,
     FLAG cần xác thực=1,220, Name_vi đã duyệt=46,719, Chờ admin duyệt=41,039) không bị
     reset sai hoặc mất khi quay lại tab nhiều lần.

## 5. Report

`daoanh/docs/T435_BUG048_ROUND2_SWITCHTAB_FIX_REPORT.md` (file này).

## 6. Limitation / blocker còn lại

- Mỗi lần tab re-entry hiện vẫn bắn lại đủ 5 request (thay vì chỉ các request còn thiếu) —
  đánh đổi chấp nhận được để đảm bảo đúng dữ liệu, nhưng có thể cân nhắc tối ưu sau nếu
  backend thấy tải cao (liên quan BUG-050/T437 về timeout 45s khi server quá tải — không
  thuộc phạm vi vòng 2 này).
- Chưa test trường hợp Admin đang sửa dở 1 dòng trong Bulk FLAG Queue (inline edit) rồi bị
  tab re-entry tải lại đè mất — ngoài phạm vi báo cáo bug này (bug chỉ về header
  CLAUDE/GEMINI + bảng kẹt loading), nên chưa kiểm tra riêng.
- Chưa git commit (theo đúng yêu cầu task).

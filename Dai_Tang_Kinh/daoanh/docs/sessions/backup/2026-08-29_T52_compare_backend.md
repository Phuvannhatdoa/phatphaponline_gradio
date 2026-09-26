# 2026-08-29 — T52 Phase 1: Đối Chiếu Tam Tạng Compare Backend (T52b) ✅

## Mô tả ngắn task

T51 (Nhân Vật Học Portal) đã verify runtime + commit `8bb7c3c` (phiên trước). Tiếp tục
theo lộ trình TGS — task kế là **T52 Đối Chiếu Tam Tạng**. User đồng ý:
"Làm T52b-e trước + ghi đệm T52a" (không dừng chờ T34 Phase A, không đụng fake data).

## Notes từ phiên trước (đã commit `8bb7c3c`)

- **T51 ✅ COMPLETED**: browse API `/daoanh/api/persons/browse` (48,673 persons / 18,121 with_lineage),
  profile API `/daoanh/api/person/<id>/profile`, home.html portal, fix bug `clusters.forEach` có sẵn.
- tasktodo.md đã cập nhật T51 → COMPLETED (chưa commit — commit chung phiên này).

## Build — T52b Backend (app.py)

- Khu vực: thêm ngay trước `# ===== INITIALIZE DIRECTORIES` (app.py:11690-11876), additive read-only.
- **Route mới:** `GET /daoanh/api/cbeta/<sigla>/compare` (`api_cbeta_compare`)
  - Helper `_t52_normalize_sigla` — normalize `251` / `T0251` / `T08n0251` / `T50n2060`.
  - Gom 5 truyền thống (filter `traditions=`):
    - `han` — `cbeta_content_index` (cbeta.db), preview ≤1200 ký tự + `has_local`
    - `tang` — `toh_cbeta_crossref` (T38, `needs_review=0`) → 84000 link + `Toh N`
    - `sat` — `sat_crossref` (T35) → 21dzk link + `has_unique`
    - `parallels` — `dharmanexus_{sigla}.json` cache (T36) / gọi `/parallels` local
    - `pali` — `_PALI_REF_MAP` curated → SuttaCentral link + `pts_sutta` (PTS numbering, T52d backend)
- `_PALI_REF_MAP` — curated `{pali_title, sc_uid, pts_sutta, note}` cho sh 0251/0235/0262/0209/0222/0221.

## Verify — Test thật (server live)

- `py_compile app.py` ✅.
- Server app.py chạy code mới (PID 14740, sau khi restart bằng `Start-Process` theo AGENTS).
- Test route:
  - `T0251` → **4 versions**: tang (Toh 21, 84000) / sat (21dzk SAT T0251) / parallels (ZH_T08_0251, DharmaNexus) / pali (Prajñāpāramitā Hṛdaya, SuttaCentral). Han vắng vì Tâm Kinh chưa import vào cbeta.db — graceful (đúng thiết kế).
  - `T51n2076` → **2 versions**: han (`has_local=True`, preview 185 ký tự) / sat. DharmaNexus không có trong map static → giới hạn đúng.

## Trạng thái subtasks T52

| Sub | Nội dung | Trạng thái |
|-----|----------|-----------|
| T52a | Chuẩn bị dữ liệu (xóa fake 84000/VRI) | ⏸ PENDING — chờ admin duyệt T34 Phase A |
| T52b | Backend compare route | ✅ DONE — live, test OK |
| T52c | UI side-by-side `places.html` tab Giáo Lý | ❌ CHƯA LÀM (next) — `renderGiaolyTab` places.html:1537 vẫn stub |
| T52d | PTS numbering | ⚠️ Backend có (`_PALI_REF_MAP`), UI chưa + map chưa đủ |
| T52e | Link từ tab Địa Danh (reuse T37) | ❌ CHƯA LÀM |

## Việc tiếp theo (tuần sau)

1. T52c — thay `renderGiaolyTab` stub bằng UI thật (chips Hán|Pali|Tạng|SAT|DharmaNexus, preview, link, ref_code).
2. T52d — hoàn thiện `_PALI_REF_MAP` (thêm PTS chính xác DN/MN/SN/AN/KN) + render nhãn PTS + link SuttaCentral.
3. T52e — nút "Xem đối chiếu Tam Tạng" từ tab Niên Đại/Địa Danh (dùng `/places/<id>/pali` T37).
4. T52a — chạy cleanup khi admin duyệt T34 Phase A (KHÔNG code thêm).
5. Chạy `npm run pipeline` trước khi commit các phần frontend.

## Revert

Atomic commit phiên này: `feat(T52): Doi Chieu Tam Tang - compare backend + docs`.
Revert: `git revert <hash>` — chỉ đảo app.py compare route + docs, không đụng T35-T38/fake data.
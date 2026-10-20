---
id: T268
title: "Trang xem Trích dẫn CBETA (Hán từ site CBETA + dịch Việt nháp theo quy tắc Admin) — PLAN ONLY"
module: CBETA / Translation / UI
priority: medium
status: pending
created: 2026-10-09
owner: claude-code
former_ids: [T267-cbeta-citation-viewer-draft]
depends_on: []
related: [T95, T165, T266, T74b]
done_when: >
  Admin trả lời các câu hỏi mở ở mục 6; sau đó mới có task build riêng
  (ghi rõ route, nguồn Hán, cơ chế dịch) được tách ra từ task này.
  Task này tự nó KHÔNG build — chỉ đóng khi báo cáo khả thi được Admin đọc
  và quyết định hướng đi (fetch realtime / cache / dùng lại T95 pipeline / khác).
revert: >
  Chỉ có 1 file task mới (không đổi DB, không đổi code). Revert = xóa file này
  nếu Admin không duyệt hướng đi.
outcome: >
  2026-10-09: Audit khả thi xong (read-only). Site CBETA (cbetaonline.dila.edu.tw)
  là SPA client-render — GET thô không trả Hán văn (chỉ HTML shell + JS). Trong
  9 trích dẫn listBibl của A009460: 5 là CBETA thật (mã T50n2061/T51n2076), 4 là
  gazetteer DILA fosizhi (không phải CBETA). Pipeline dịch có rules (T165
  style_constitution.py) + jobs riêng CBETA (T95 text_passages/translation_segments)
  đã tồn tại nhưng mới import 1 work (T50n2060) — tức đa số trích dẫn thật tế
  (bao gồm cả 5 của A009460) KHÔNG có trong DB nội bộ, khớp với yêu cầu Admin
  là phải lấy từ site. Chưa build gì. Cần Admin trả lời câu hỏi mở trước khi giao
  task build.
---

# T268 — Trang xem Trích dẫn CBETA (PLAN ONLY)

Task con phát sinh từ yêu cầu Admin (T267 trong hội thoại — trùng số với task
`T267-t199-logic-audit-and-bug025-026-restore.md` đã `done`, nên đổi số thành
**T268** để tránh đè file).

Mục tiêu cuối: trong card người, "Trích dẫn CBETA" bấm được → mở trang mới
hiển thị Hán văn lấy từ site CBETA (không phải `cbeta.db` nội bộ) trình bày
giống trang gốc, kèm bản dịch Việt do AI dịch có áp quy tắc dịch của Admin.

**Giai đoạn này chỉ lập kế hoạch + kiểm khả thi (đọc thôi). Không build.**

## 1. Phạm vi đã kiểm (read-only, tối đa 5 GET tới site CBETA)

- `app.py` route `/daoanh/api/person/<id>/dila_full` (dòng 20371) trả `listbibl`
  (list string thô, parse từ `listBibl/bibl` trong
  `data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml`,
  dòng ~5722).
- Mẫu `A009460` (xml dòng 255931–256021): 9 dòng `listBibl`:
  - 5 dòng dạng `( CBETA T50n2061_p0771c23 ) 宋高僧傳: ...` và tương tự cho
    `T50n2061_p0773b17`, `T50n2061_p0773c06`, `T51n2076_p0293c18`, `T51n2076_p0293c23`
    → **CBETA thật**, mã việt vị `WORKID_pPAGEcLINE` chuẩn CBETA (p=page, a/b/c=column).
  - 4 dòng còn lại là `<bibl><ref target="http://buddhistinformatics.dila.edu.tw/fosizhi/...">`
    → **KHÔNG phải CBETA** — là gazetteer nội bộ DILA ("fosizhi", ví dụ 清涼山志/徑山志),
    đã có `ref.target` URL sẵn (khác domain, khác định dạng trang, không nằm trong
    phạm vi "site CBETA" Admin yêu cầu).
- `curl` tới `https://cbetaonline.dila.edu.tw/robots.txt` → trả về HTML shell
  của app SPA (không có `robots.txt` thật, server fallback mọi path về `index.html`).
- `curl` tới `https://cbetaonline.dila.edu.tw/zh/T50n2061_p0771c23` → 64.198 bytes
  HTML, **không có chữ Hán** (`天然`, `示寂`, `智通` đều không xuất hiện) — xác nhận
  đây là **SPA client-render**: nội dung Hán văn được JS tải sau qua API riêng
  (chưa xác định được endpoint JSON trong phạm vi 5 request cho phép).
- `curl` tới `https://www.cbeta.org/robots.txt` → disallow rõ `/cbreader/`,
  `/node/`, `/opds/`, `/forum/` (site WordPress khác domain với cbetaonline,
  nhưng cùng tổ chức CBETA — tín hiệu họ coi crawl `/cbreader/` là không hoan nghênh).
  `www.cbeta.org/copyright` → redirect 301 (chưa theo dõi đích, hết budget request).
- DB nội bộ: `data/lineage.db.text_passages` (pipeline T95) chỉ có **1 work**
  (`T50n2060`) — KHÔNG có `T50n2061`/`T51n2076`. `data/cbeta/cbeta.db` (clone riêng)
  chỉ có **198 dòng** `cbeta_texts` — partial clone rất nhỏ. Tức: xác nhận claim
  Admin — đa số trích dẫn thật không có sẵn nội bộ, phải lấy ngoài site.
- `style_constitution.py` (T165): đã có `translation_rules` (309 dòng active trong
  DB), `glossary`, `constitution_hash` (khóa theo rule đã chọn), `translation_cache`
  (2001 dòng) — cơ chế áp "quy tắc Admin" lên bản dịch AI **đã có sẵn và đang dùng**
  cho tiểu sử DILA (T266, Gemini free). CBETA riêng có kiến trúc song ngữ đầy đủ
  hơn (T95: `text_passages` / `translation_segments` / `passage_translation_alignment`
  / `translation_jobs`) nhưng mới chạy cho 1 work.

## 2. Phân loại vấn đề

| Hạng mục | Kết quả |
|---|---|
| Lấy Hán từ site bằng GET thô | **Không khả thi trực tiếp** — cbetaonline.dila.edu.tw là SPA, cần tìm API JSON nội bộ của họ hoặc headless browser (ngoài phạm vi GET đơn giản đã duyệt) |
| Ánh xạ listBibl → mã CBETA | **Khả thi, có quy tắc rõ** nhưng KHÔNG phải 100% dòng listBibl là CBETA (case A009460: 5/9) |
| Cơ chế áp quy tắc dịch Admin | **Đã có sẵn** (style_constitution.py + translation_rules + translation_cache), dùng lại được, không cần xây mới |
| Pipeline song ngữ CBETA | **Đã có khung** (T95) nhưng DB gần như trống (1/nhiều nghìn work) — nếu dùng khung này phải import thêm |
| Bản quyền/robots | **Chưa rõ** — cbeta.org robots disallow `/cbreader/`; cbetaonline.dila.edu.tw domain riêng chưa có robots.txt rõ ràng (SPA fallback); cần đọc trang copyright CBETA đầy đủ (301 redirect, chưa theo) trước khi quyết fetch tự động |

## 3. Các bước (checklist — khi Admin duyệt hướng đi mới tách task build)

- [ ] Admin trả lời câu hỏi mở (mục 6 báo cáo) để chọn hướng: fetch realtime theo
      request / fetch + cache (bảng mới, có backup) / dùng lại khung T95 (import
      work theo nhu cầu) / khác.
- [ ] Nếu chọn fetch site: xác định được endpoint JSON thật của
      cbetaonline.dila.edu.tw (hiện GET thô không ra Hán văn) — cần 1 vòng
      kiểm tra mạng (browser network tab hoặc tài liệu API công khai của DILA)
      TRƯỚC khi viết code fetch.
- [ ] Đọc đầy đủ trang bản quyền/điều khoản CBETA (chưa đọc được do 301 redirect
      hết budget request) để xác nhận fetch tự động + cache được phép ở mức nào
      (full passage vs trích đoạn ngắn).
- [ ] Thiết kế route mới (ví dụ `/daoanh/citation/<ref_id>`) + service lấy Hán +
      service dịch nháp (tái dùng `style_constitution.py`) + bảng lưu cache (nếu
      được duyệt) có backup/rollback đúng quy tắc `CLAUDE.md`.
- [ ] Phân loại 9 dòng listBibl theo mẫu ở mục 1 cho toàn bộ người (không chỉ
      A009460) để biết tỉ lệ CBETA thật vs gazetteer/khác trên toàn corpus, trước
      khi build UI bấm-mở (tránh nút "Trích dẫn CBETA" dẫn tới dòng không phải CBETA).
- [ ] Sau khi có route thật: QA (`daoanh-qa`) kiểm đối chiếu Hán văn hiển thị vs
      nguồn, kiểm bản dịch có gắn `constitution_hash`/rule áp dụng, không tự nhận
      bản dịch AI là chính thức khi chưa review.

## 4. Quyết định của Admin (2026-10-10)

Admin đã trả lời các câu hỏi mở (mục 1–4, trong hội thoại — chưa có file báo
cáo riêng lưu lại câu hỏi gốc, chỉ ghi quyết định tại đây):

- **Nguồn Hán văn**: dùng bộ XML chính thức của CBETA lấy từ GitHub (repo
  chính thức CBETA), đưa lên VPS và **load tại chỗ** (local trên VPS) — KHÔNG
  gọi/kết nối site `cbetaonline.dila.edu.tw` mỗi khi người dùng bấm xem trích
  dẫn. Khi CBETA cập nhật XML mới trên GitHub thì đồng bộ (sync) phần cập nhật
  về VPS. Trích nguồn (attribution CBETA) phải hiển thị trên trang pháp lý
  (legal/credits) của hệ thống.
- **Suy ra (CẦN Admin xác nhận lại nếu sai)**: "load tại chỗ" được hiểu là lấy
  XML từ GitHub **một lần rồi lưu/cache trên VPS** (không gọi GitHub lại mỗi
  lần người dùng bấm xem trích dẫn) — chỉ đồng bộ khi CBETA có bản cập nhật
  mới. Đây là suy luận của agent từ câu trả lời của Admin, **chưa được Admin
  xác nhận bằng lời trực tiếp** cho đúng cách diễn giải "load tại chỗ" này.
- **Phạm vi thử nghiệm**: làm trước với trường hợp Thiên Nhiên (`A009460`) để
  test code/luồng xử lý, sau khi ổn mới mở rộng ra toàn corpus (xem mục 3,
  bước phân loại 9 dòng listBibl cho toàn bộ người).
- **4 mục trích dẫn không phải CBETA (gazetteer fosizhi, domain khác)**: Admin
  đã chọn hướng xử lý — mở trang fosizhi tương ứng (khác domain với CBETA,
  dùng `ref.target` URL đã có sẵn trong XML DILA), không gộp chung vào luồng
  "trích dẫn CBETA".
- **Câu hỏi 5 (duyệt bản dịch Việt trước khi hiển thị cho người dùng cuối)**:
  **CHƯA được Admin trả lời** — đang chờ quyết định (hiển thị bản dịch AI nháp
  ngay kèm cảnh báo "chưa review", hay phải có người duyệt trước khi public).
  Task build không được giả định hướng này; phải hỏi lại trước khi code phần
  hiển thị bản dịch cho người dùng cuối.
- **Ghi chú hạ tầng/pháp lý (việc cần làm, chưa làm)**:
  - VPS cần kiểm dung lượng đĩa đủ chứa toàn bộ XML CBETA tải từ GitHub
    (chưa đo kích thước thật của repo).
  - Cần kiểm giấy phép (license) CBETA trước khi công khai nội dung Hán văn
    lấy từ XML của họ trên hệ thống PTDA (mục 1 báo cáo đã ghi nhận robots/
    copyright CBETA chưa đọc hết do 301 redirect — vẫn chưa xong).

Trạng thái: vẫn **PLAN ONLY**, chưa build. Khi Admin trả lời câu hỏi 5 và xác
nhận lại điểm suy ra "load một lần rồi cache", mới tách task build riêng theo
đúng `done_when` ở đầu file này.

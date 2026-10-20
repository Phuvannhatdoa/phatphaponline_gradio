---
id: T418
bug_id: BUG-045
title: "Bug verify: BUG-045: Cột Gemini trong namevimap không đầy đủ (39K/48K) — import Claude-translated từ XML + resume Gemini batch"
status: done
created: 2026-10-19
updated: 2026-10-20
owner: null
module: Data / Translation / Namevimap
priority: medium
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-19 (Admin duyệt: 1B-codex_person_name, 2B-orphan status, XML commit 0d2ea40)"
done_when: >
  PART 1 (Claude XML → codex_person_name):
  (1a) Bản sao lưu lineage.db (sqlite backup) có PRAGMA quick_check=ok; ghi đường dẫn vào task + docs/ROLLBACK.md.
  (1b) XML tải từ commit 0d2ea40: https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/0d2ea40/data/phien_am/vn_person_name_vi.xml
       Parse bằng iterparse (generator); đếm được 49.335 thẻ <person>; ghi SHA-256 của file.
  (1c) CREATE TABLE codex_person_name (thêm mới, không ALTER bảng cũ): dila_id, name_zh_xml, name_vi, tier,
       review/rule/evidence/alternatives, model='claude-xml-import@0d2ea40', status (suggested cho matched, 'orphan-chưa có ID Dila' cho 689),
       name_zh_mismatch, xml_sha256, created_at. Không sửa people, name_vi_map, entity_claims, ai_person_name.
  (1d) INSERT 48.646 dòng (matched với people.dila_id) + 689 dòng (orphan, không có trong DB).
       1.637 dòng lệch chữ Hán gắn cờ name_zh_mismatch=1; ghi CSV danh sách các ID orphan + lý do.
  (1e) Manifest dila_id đã INSERT để hoàn tác nếu cần; đếm trước/sau SELECT COUNT(*).
  PART 2 (Gemini batch resume):
  (2a) Chạy scripts/ai_batch_transliterate.py (không --reset), log → logs/ai_transliterate.log.
  (2b) COUNT ai_person_name có name_vi_ai ≠ NULL = 48.673/48.673, hoặc còn N ID lỗi (danh sách, lý do, tối đa 3 ngày).
  (2c) Không overwrite 39.269 bản ghi cũ (created_at không đổi).
  CHUNG:
  (3) Ảnh chụp header 2 cột (Claude/Gemini) từ admin/namevimap.html trước/sau, click UI thật (127.0.0.1:8080/daoanh/admin/namevimap.html).
  (4) Commit chỉ gồm script (t418_import_claude_xml.py, sửa ai_batch_transliterate.py nếu có) + docs/sessions/2026-10-19/T418/,
      không commit lineage.db/.env; ghi commit SHA vào task outcome.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  Part 1: DROP TABLE codex_person_name (bảng mới, không ảnh hưởng bảng khác).
  Part 2: DELETE FROM ai_person_name WHERE created_at >= '<timestamp bắt đầu ghi trong log>'.
  Hoặc khôi phục toàn bộ từ backup ghi trong ROLLBACK.md.
outcome: "2026-10-20: BUG-045 DONE — Gemini ai_person_name = 48,673/48,673 (100%, verified SELECT COUNT). Claude codex_person_name = 49,335 dòng đã import từ XML (48,646 matched + 689 orphan, verified SELECT COUNT). Cột Claude trên namevimap.html hiển thị 59,164/59,167 (Admin xác nhận bằng lời: 'Cột Claude đã đủ (59,164) — Done'). Report: docs/sessions/2026-10-20/T418_FINAL_REPORT.md. Commit SHA: PENDING_SHA. Giới hạn: không chụp được screenshot UI before/after trực tiếp trong phiên này do admin/namevimap.html yêu cầu đăng nhập Google OAuth thật (agent không tự đăng nhập IdP sản xuất thay người dùng) — bằng chứng dùng COUNT DB + xác nhận lời của Admin thay thế."
admin_decisions: "1B: codex_person_name (không sửa code app); 2B: nhập 689 orphan với status='orphan-chưa có ID Dila'; XML SHA 0d2ea40; tier 1-4; name_zh_mismatch flag; Gemini trần 3 ngày; commit script+docs"
---

# T418 / BUG-044 — Cột Gemini không đầy đủ (39K/48K) — Import Claude-translated từ XML

## Route / UI

Admin panel: `admin/namevimap.html` — cột "Gemini" (39.269/48.673 = 80.6%, chưa 100%)

## Triệu chứng (Admin báo)

Cột Claude: đầy đủ, Claude Cloud phiên âm (CloudCode) vào.  
Cột Gemini: chỉ 39K/48K, chưa import được.

XML nguồn: https://github.com/Phuvannhatdoa/phatphaponline_gradio/raw/claude/sleepy-tesla-qsx17b/data/phien_am/vn_person_name_vi.xml  
(Claude branch, có sẵn phiên âm từ Claude Cloud)

## Phạm vi

- Update namevimap table (Gemini column / mapping)
- Chỉ UPDATE nơi hiện tại NULL/rỗng (không overwrite)
- Backup + verify count sau UPDATE
- Không đổi schema, không sửa code app (trừ khi cần fetch XML)

## Các bước

- [x] Kiểm namevimap status hiện tại (count Gemini)
- [ ] Fetch XML từ GitHub, parse extract dila_id + claude_translation
- [ ] Chuẩn bị UPDATE statement (UPDATE namevimap SET gemini_name=... WHERE id=... AND gemini_name IS NULL)
- [ ] Backup DB trước UPDATE
- [ ] Chạy UPDATE, verify count
- [ ] daoanh-qa kiểm
- [ ] Admin xác nhận DONE

## Chẩn đoán (2026-10-19, diagnosis-only, chưa sửa data)

**Cột Gemini trong namevimap.html KHÔNG liên quan XML Claude branch.** Nó đọc trực tiếp
bảng `ai_person_name` (cột `name_vi_ai`), được admin ước tính đúng là 80.6%
(`39269/48673` khớp chính xác với `admin/namevimap.html` JS gọi
`GET /api/admin/ai-transliterate/status`, xử lý tại `app.py:15794-15808`).

- Nguồn ghi: `scripts/ai_batch_transliterate.py` — gọi Gemini (`MODEL_ID =
  'gemini-3.1-flash-lite'`), lưu `INSERT OR REPLACE` vào `ai_person_name`.
  Query pending: `WHERE p.id NOT IN (SELECT dila_id FROM ai_person_name
  WHERE name_vi_ai IS NOT NULL AND name_vi_ai != '')` — **không có LIMIT cứng,
  không giới hạn subset** — script resumable, nếu chạy lại sẽ tự động lấy đúng
  phần còn thiếu.
- `created_at` trong `ai_person_name` cho thấy script chỉ chạy 3 lần:
  2026-10-04 (24,575 bản ghi), 2026-10-05 (1,583), 2026-10-08 10:55:38
  (13,111) — cộng = 39,269, khớp con số UI. **Không có lần chạy nào sau đó.**
  → Root cause thực tế: **job batch đơn giản là chưa được khởi động lại**,
  không phải lỗi WHERE/limit/schema.
- 9,404 ID còn pending (`A030003`…`A047708`) nằm RẢI RÁC trong dải ID đã xử
  lý (có 1,348 ID lớn hơn ID-pending-lớn-nhất đã done, 29,737 ID nhỏ hơn
  ID-pending-nhỏ-nhất đã done) — không phải một "đuôi" chưa chạy tới, mà là
  các batch (50 tên/request) từng thất bại rải rác trong các lần chạy
  2026-10-04/05/08. Khớp với cơ chế trong script: nếu `call_gemini()` thất
  bại cả `MAX_RETRIES=5` lần (ví dụ lỗi `429` quota — script `sleep(70)` rồi
  vẫn fail), batch đó bị bỏ qua vĩnh viễn (`errors += 1`, log rồi tiếp tục
  batch kế) và không tự retry trừ khi script được chạy lại.
  → Không tìm thấy `logs/ai_transliterate.log` hiện tại (thư mục `logs/` chỉ
  còn log Flask/gateway) nên không xác nhận được log 429 cụ thể của lần
  chạy cuối, nhưng phân bố rải rác + việc dừng đúng lúc 13,111 bản ghi trong
  phiên 10-08 phù hợp với giả thuyết hết quota free-tier giữa batch.

**Lưu ý quan trọng:** `done_when` bản gốc của task này giả định phải fetch
XML từ branch Claude GitHub để fill cột Gemini — đây là **nhầm nguồn**. XML
đó (nếu có) thuộc cột "Claude" (phiên âm CloudCode), một cơ chế khác, không
liên quan bảng `ai_person_name`/API Gemini. Đề xuất sửa `done_when` nếu admin
xác nhận hướng đi đúng là chạy lại batch Gemini, không phải import XML.

**Đề xuất bước tiếp (admin quyết định, chưa thực hiện):**
1. Chạy lại `python scripts/ai_batch_transliterate.py` (không cần `--reset`,
   script tự resume đúng 9,404 ID còn thiếu nhờ `NOT IN` trong `get_pending`).
2. Trước khi chạy, backup `data/lineage.db` (hoặc riêng export bảng
   `ai_person_name`) theo quy tắc CLAUDE.md.
3. Theo dõi `logs/ai_transliterate.log` lần này (đảm bảo thư mục `logs/`
   tồn tại) để nếu dừng giữa đường lại thấy rõ lý do (429/503/JSON lỗi) thay
   vì phải suy luận ngược như lần này.
4. Nếu tiếp tục gặp `429` (free-tier quota), tăng `SLEEP_SECONDS` hoặc chia
   nhiều ngày chạy `--limit`.

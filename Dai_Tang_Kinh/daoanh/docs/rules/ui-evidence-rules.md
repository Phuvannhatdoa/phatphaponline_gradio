# Quy tắc UI & Evidence Rendering — PTDA

## Phân loại event (bắt buộc từ schema)

| Loại | Điều kiện render card |
|------|-----------------------|
| `dated_event` | event_type + actor/place + thời gian xác minh |
| `undated_event` | event_type + evidence, chưa có thời gian |
| `place_person_relation` | quan hệ có nguồn, không phải event |
| `textual_mention` | co-mention CBETA — **KHÔNG render event card** |
| `unresolved` | không đủ chứng cứ — **KHÔNG public** |

**Quy tắc cứng:**

- `textual_mention` ≠ event → không đếm, không render card.
- Không có `event_type` → không render event card.
- Không suy event date từ niên đại sách hay dynasty của place/person.
- Không dịch raw Hán bằng LLM để suy action.

---

## LLM policy (phân định rõ — tránh hiểu nhầm)

- **CẤM (suy diễn học thuật):** dùng LLM để bịa/dựng event, date, quan hệ, identity,
  hoặc dịch Hán để tạo action/event title. Không tạo evidence bằng LLM.
- **CHO PHÉP (pipeline dịch kinh văn):** dịch Hán văn passage/segment sang tiếng Việt
  qua API translate (`/daoanh/api/passage/<id>/translate`, `/daoanh/api/segments/translate`):
  Groq → bảng `translation_segments`, `quality_status='unreviewed'`, `provider='groq'`,
  có bước duyệt admin trên `translation_monitor.html` (T94/T96). Bản dịch này KHÔNG
  được dùng làm learning inference cho event/relation (analysis từ bản dịch vẫn là cấm).

---

## Event card requirements

Mỗi event card PHẢI có:
- Title (zh hoặc vi)
- Source ref (cbeta_ref hoặc source_record)
- Evidence badge: click mở đúng CBETA passage / source span
- Status badge: candidate / reviewed / disputed / rejected

Nếu thiếu bất kỳ field nào → hiển thị empty-state thay vì card giả.

---

## Empty-state (bắt buộc)

- API trả về empty array → render empty-state ("Chưa có dữ liệu").
- Không render null/undefined làm content.
- Không hiển thị "đang phát triển" khi đã có API thật.

---

## Tab Niên Đại vs Tab Sự Kiện

| Tab | Nguồn dữ liệu | Ghi chú |
|-----|---------------|---------|
| Niên Đại | `/api/places/<id>/timeline` | Wikidata P571 + time_periods + place_timeline_events |
| Sự Kiện | `/api/places/<id>/events` | nexus_events + event_text_link |

Hai tab dùng chung core data, **không copy record** giữa nhau.

---

## Display name badges

| Nguồn | Badge hiển thị |
|-------|---------------|
| DILA | "DILA" (xanh) |
| CBETA | "CBETA" + ref mã |
| ZQ / ZQLOCAL | "ZQ phiên âm" (xám) — confidence < 0.8 |
| Scholar reviewed | "ZQ đã duyệt" (cam) — confidence ≥ 0.8 |

---

## Admin review UI (events.html)

- Filter: status + place DILA ID.
- Pagination 25/page.
- Buttons: ✓ Xác nhận / ⚠ Tranh chấp / ✗ Từ chối / ↩ Đặt lại.
- PATCH `/daoanh/api/events/<id>` body: `{status, notes}`.
- Toast message khi update thành công/thất bại.

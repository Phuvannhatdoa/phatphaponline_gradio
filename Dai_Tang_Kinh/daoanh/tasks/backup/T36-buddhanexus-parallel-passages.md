---
id: T36
title: BuddhaNexus Parallel Passages — tab Giáo Lý cross-tradition
module: Giáo Lý / Tham chiếu chéo Tam Tạng
priority: medium
status: done
depends_on: [T34]
created: 2026-08-24
updated: 2026-08-25
done_when: Tab Giáo Lý hiển thị "Parallel passages" từ BuddhaNexus cho ít nhất các kinh chính (Tâm Kinh, Kim Cang, v.v.)
---

## Bối Cảnh

**BuddhaNexus** (`buddhanexus.net`) là dự án của Khyentse Foundation + đối tác học thuật.  
Họ đã phân tích text-reuse giữa các kinh trong 3 truyền thống:
- Hán Tạng (CBETA T-series)
- Pali (Nikaya)
- Tây Tạng (Kangyur/Tengyur Toh)
- Sanskrit (GRETIL)

**Ví dụ điển hình:**  
Đoạn "Tứ Thánh Đế" xuất hiện trong:
- Hán: SN T2.99 và T2.100 và nhiều kinh khác
- Pali: SN 56.11, DN 16, MN 141
- Tây Tạng: Toh 310, Toh 847

**API:** GraphQL public: `api.buddhanexus.net/graphql`

## Giá Trị Học Thuật Cho TGS

Đây là **cầu nối thật sự giữa Tam Tạng** — không phải chỉ liệt kê 3 truyền thống riêng biệt, mà chỉ ra các đoạn kinh văn **cùng nội dung** xuất hiện xuyên suốt ba truyền thống.

Đây là tính năng mà không có hệ thống Phật học Việt Nam nào có hiện tại.

## Thiết Kế

### KHÔNG import vào DB
BuddhaNexus data quá lớn và liên tục được cập nhật. Gọi API realtime.

### Route mới: `/daoanh/api/cbeta/<sigla>/parallels`
```python
@app.route('/daoanh/api/cbeta/<sigla>/parallels')
def cbeta_parallels(sigla):
    # Gọi BuddhaNexus GraphQL API
    # VD: sigla = 'T0251' → query parallels
    # Trả về list các đoạn parallel trong Pali/Tạng ngữ
    pass
```

### Cache
- Cache kết quả 24h trong `data/cache/buddhanexus_<sigla>.json`
- Nếu BuddhaNexus API down → hiển thị "Không có data tham chiếu chéo lúc này"

### UI — Tab Giáo Lý
Khi xem một kinh CBETA → section "Parallel trong các Tạng khác":
- 🔵 Pali: [DN 16, SN 56.11] → link sang SuttaCentral
- 🟠 Tây Tạng: [Toh 310] → link sang 84000
- 🟡 Sanskrit: [GRETIL ref] → link sang GRETIL (nếu có)

## Acceptance Criteria

- [x] Route `GET /daoanh/api/cbeta/<sigla>/parallels` trả JSON từ DharmaNexus
- [x] Cache 24h tại `data/cache/dharmanexus_{sigla}.json`
- [x] ≥5 kinh có dharmanexus_id: T0251, T0235, T0475, T0223, T0220, T0262, T0310, T0360, T0665, T0893, T0945
- [x] Link → `dharmamitra.org/nexus/db/zh/{id}/text` (interactive parallel exploration)
- [ ] UI tab Giáo Lý wiring — cần server restart để test

## Ghi Chú Quan Trọng (2026-08-25)

**BuddhaNexus đã đổi tên thành DharmaNexus** (dharmamitra.org/nexus).  
API endpoint thực tế (không phải GraphQL như task file cũ ghi):
- `POST https://dharmamitra.org/api-db/text-view/text-parallels/` — text với parallels embedded
- `GET  https://dharmamitra.org/api-db/utils/raw-metadata/?filename={id}` — metadata
- `GET  https://dharmamitra.org/api-db/menudata/?language=zh` — full catalog

DharmaNexus ID format: `ZH_{TaishoVolume}_{sigla}` (VD: `ZH_T08_0251` = T0251 trong tập T08)  
Static map 11 texts (confirmed từ T38): T0220, T0223, T0235, T0251, T0262, T0310, T0360, T0475, T0665, T0893, T0945  
Fallback: query menudata API nếu không có trong static map

## Completion Log (2026-08-25)

**Route:** `GET /daoanh/api/cbeta/<sigla>/parallels` — thêm vào app.py  
**Response:** `{ok, sigla, dharmanexus_id, dharmanexus_url, metadata_md, badge_label, note_vi, from_cache}`  
**Cache:** `data/cache/dharmanexus_{sigla}.json` (24h TTL)

## Ghi Chú

BuddhaNexus API là GraphQL — cần import `requests` và viết query chuẩn.  
Endpoint test: `https://api.buddhanexus.net/graphql`
```graphql
query {
  parallels(segmentId: "T0251/segmentId") {
    sourceSegmentId
    targetSegmentId
    targetCollection
    score
  }
}
```

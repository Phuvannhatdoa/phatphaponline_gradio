# FOJIN — Runbook Test Local (tự chứa, cho agent Claude Code)

**Ngày lập:** 2026-10-15
**Trạng thái:** kế hoạch được duyệt — chưa thực thi
**Tr mannen:** T393
**Vai trò:** bản hướng dẫn để một agent khác **đọc và tự setup**, không cần hỏi thêm.

---

## §0. Nhiệm vụ và răn buộc cứng (vi phạm = dừng toàn bộ)

- **R1** Không SSH vào VPS, không deploy production, không đụng server 158.220.106.183
- **R2** Không sửa/xoá container, volume, network, database của dự án khác
- **R3** Không tải toàn bộ corpus — chỉ 10 kinh gốc CBETA + 10 kinh tiếng Việt
- **R4** Không bật AI Q&A / embedding / RAG — không sinh vector, không gọi LLM
- **R5** Không dùng: GRETIL (không license), DSBC (cấm sao chép), 84000 (NC-ND), MITRA (chưa verify), 39 từ điển (bản quyền/CDSL)
- **R6** Không commit `.env` hay secrets
- **R7** Nếu thiếu tài nguyên → **DỪNG và báo cáo**. Không tự chuyển sang VPS, không tự tắt app khác của người dùng
- **R8** Mọi publish port đều bind `127.0.0.1`

**Điều kiện DỪNG:** Docker không chạy; RAM trống <5GB; C: trống <10GB; cổng bị chiếm bởi tiến trình không thuộc fojin-test.

---

## §1. Tham số chốt (không tự đổi)

| Tham số | Giá trị |
|---|---|
| Compose project | `fojin-test` |
| Workspace | `E:\fojin-test\` |
| Repo clone | `E:\fojin-test\fojin` |
| Services GIỮ | `postgres`, `elasticsearch`, `redis`, `backend`, `frontend` |
| Services BỎ | `backend2` (rolling deploy), `umami` (analytics), `mcp` (AI endpoint) |
| Docker data root | **phải đặt vào `E:\DockerData`** (C: còn 8,3 GB) |
| Branch | `master` |
| DB | `fojin_test` / user `fojin_test` |

### Bảng port (bắt buộc)

| Service | Host port | Ghi chú |
|---|---|---|
| frontend (nginx) | **3100** | ⚠️ không dùng 3000 (đang bận) |
| backend (FastAPI) | **8100** | |
| elasticsearch | 9200 | |
| postgres | 55432 | |
| redis | 56379 | |

### Bảng tài nguyên (đã cắt)

| Service | mem_limit | cpus |
|---|---|---|
| postgres | 2g | 1.0 |
| elasticsearch | 2g | 1.5 |
| redis | 256m | 0.5 |
| backend | 1g | 1.0 |
| frontend | 128m | 0.25 |
| Tổng trần | ≈5,4 GB | 4,25 |

---

## §2. Khảo sát thực tế (đã đo 2026-10-15)

| Hạng mục | Kết quả | Đánh giá |
|---|---|---|
| OS | Windows 10 Pro 10.0.19045 x64 | ✅ |
| CPU | Intel Xeon E5520 2c/4t @2,27GHz | ⚠️ yếu |
| RAM | 20,0 GB tổng, **2,08 GB trống** | 🔴 <5GB |
| Disk C: | **8,3 GB trống** | 🔴 <10GB |
| Disk E: | **554,7 GB trống** | ✅ |
| Docker CLI / Desktop | **không có** | 🔴 chưa cài |
| WSL | tính năng có, 0 distro | 🔴 |
| Cổng bận | 3000(node), 5000/5001/8080(Đạo Ảnh), 6000(Moba) | dùng 3100 |
| Cổng trống | 5432, 6379, 8000, 8001, 8765, 9200, 3001 | dùng 55432/56379/8100/9200 |

→ **3 BLOCKER:** thiếu Docker, thiếu RAM, C: gần đầy. **Dừng và báo** theo R7. Không tự xử.

---

## §3. Chuẩn bị (NGƯỜI DÙNG làm tay — agent không tự cài SW hệ thống)

```powershell
# 1. WSL2
wsl --install -d Ubuntu
# 2. Cài Docker Desktop (WSL2 backend)
#    https://desktop.docker.com/win32/main/amd64/Docker%20Desktop%20Installer.exe
# 3. Docker Desktop → Settings → Resources → Disk image location → E:\DockerData
# 4. Đóng app khác để có ≥5 GB RAM trống
#    (Đạo Ảnh đang giữ 5000/5001/8080 — nên tạm dừng)
# 5. Xác nhận:
docker version
docker compose version
docker run --rm alpine echo ok          # gate
```

---

## §4. Dựng workspace

```powershell
New-Item -ItemType Directory -Force -Path E:\fojin-test
git clone --depth 1 https://github.com/xr843/fojin.git E:\fojin-test\fojin
```

### 4.1 `E:\fojin-test\docker-compose.override.fojin-test.yml` (overwrite, chỉ thêm)

```yaml
services:
  postgres:
    container_name: fojin-test-postgres
    mem_limit: 2g
    shm_size: 128m
    ports:
      - "127.0.0.1:55432:5432"
  elasticsearch:
    container_name: fojin-test-es
    mem_limit: 2g
    ports:
      - "127.0.0.1:9200:9200"
  redis:
    container_name: fojin-test-redis
    ports:
      - "127.0.0.1:56379:6379"
  backend:
    container_name: fojin-test-backend
    ports:
      - "127.0.0.1:8100:8000"
  frontend:
    container_name: fojin-test-frontend
    ports:
      - "127.0.0.1:3100:80"
volumes:
  pgdata:    { name: fojin-test-pgdata }
  esdata:    { name: fojin-test-esdata }
  redisdata: { name: fojin-test-redisdata }
networks:
  default:   { name: fojin-test-net }
```

> `backend2`, `umami`, `mcp` **không khai báo** → compose coi như không tồn tại. Volumes/network có tiền tố riêng → không đụng dự án khác.

### 4.2 `.env` (ngoài repo, không commit)

Tạo bằng:
```powershell
python -c "import secrets;print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
python -c "import secrets;print(secrets.token_urlsafe(48))"   # JWT_SECRET_KEY
python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"  # API_KEY_ENCRYPTION_KEY
```
Nội dung:
```ini
POSTGRES_DB=fojin_test
POSTGRES_USER=fojin_test
POSTGRES_PASSWORD=<sinстанавли>
JWT_SECRET_KEY=<sinlógica>
API_KEY_ENCRYPTION_KEY=<sinlógica>
FRONTEND_BIND=127.0.0.1
FRONTEND_PORT=3100
BACKEND_PORT=8100
ES_PORT=9200
POSTGRES_PORT=55432
REDIS_PORT=56379
CORS_ORIGINS=http://localhost:3100
FOJIN_ENV=development
# TẮT AI (R4):
LLM_API_URL=
LLM_API_KEY=
EMBEDDING_API_URL=
EMBEDDING_API_KEY=
RERANKER_API_URL=
RERANKER_API_KEY=
ENABLE_SENTENCE_PARALLELS=false
ENABLE_OPEN_DATA_EXPORTS=false
```

### 4.3 Lệnh compose

```powershell
cd E:\fojin-test\fojin
$C = "docker compose -p fojin-test -f docker-compose.yml -f ..\docker-compose.override.fojin-test.yml --env-file ..\.env"
$C up -d           # START
$C stop            # STOP, giữ dữ liệu
$C restart         # RESTART
$C down            # DỪNG + xoá container
$C logs -f backend
```

**Gate:** 5 container `healthy` (kiểm `$C ps`).

---

## §5. Hai thay đổi code đã duyệt (chấp nhận trước)

**THỰC HIỆN TRƯỚC BƯỚC 6** để chỉ recreate index một lần.

### S1 — Analyzer không dấu tiếng Việt (bắt buộc cho tiêu chí 3)

**File:** `backend/app/core/elasticsearch.py` (CONTENT_INDEX_SETTINGS)

Thêm analyzer mới (KHÔNG sửa `cjk_content`, `cjk_nopunct`, `t2s` → không hồi quy Hán):
```python
"vie": {
    "type": "custom",
    "tokenizer": "standard",
    "filter": ["icu_folding", "lowercase"],
},
```
Thêm sub-field vào `content`:
```python
"content": {
    "type": "text",
    "analyzer": "cjk_content",
    "term_vector": "with_positions_offsets",
    "fields": {
        "nopunct": {"type": "text", "analyzer": "cjk_nopunct"},
        "folded": {"type": "text", "analyzer": "vie"},   # MỚI
    },
},
```
`icu_folding` dùng được vì image ES đã cài `analysis-icu`.

### S2 — Script nạp kinh tiếng Việt (file mới, không sửa `import_content.py`)

**File MỚI:** `backend/scripts/import_vn.py` — idempotent bằng `ON CONFLICT DO UPDATE` + ES `_id = {text_id}_{juan}_vie`.

Bắt buộc có cờ `--dry-run` (chỉ in kế hoạch, không ghi). Header `.txt` dạng `; key: value`. Tách đoạn theo dòng trống; `cbeta_id = "VN%03d"`; `lang='vie'`, `source_code='vn_user'`.

### S3 — Kiểm filter theo `lang`/`source_code`

`lang` và `source_code` đã là `keyword`. Xác nhận API search truyền filter xuống; nếu chưa → thêm tham số query vào `backend/app/api/`. **Không sửa mapping.**

---

## §6. Bootstrap index Elasticsearch (BẮT BUỘC, trước import)

**Vì sao:** `init_es()` chỉ tạo client, **không tạo index**. DB trắng chưa có index → import ghi vào hư không.

1. Kiểm tra:
```powershell
curl.exe -s -u elastic:<PW> http://localhost:9200/_cat/indices?v
```
2. Nếu `buddhist_texts` / `text_contents` chưa có → trích **nguyên văn** `INDEX_SETTINGS` và `CONTENT_INDEX_SETTINGS` (đã áp S1) từ `backend/app/core/elasticsearch.py` ra 2 file JSON trong `E:\fojin-test\`, rồi:
```powershell
curl.exe -X PUT -u elastic:<PW> http://localhost:9200/buddhist_texts `
  -H "Content-Type: application/json" --data-binary "@...\INDEX_SETTINGS.buddhist_texts.json"
curl.exe -X PUT -u elastic:<PW> http://localhost:9200/text_contents `
  -H "Content-Type: application/json" --data-binary "@...\INDEX_SETTINGS.text_contents.json"
```
**Gate:** `GET /_cluster/health` → green/yellow; `GET /text_contents/_mapping` phải có `content`, `content.folded`, `lang`, `source_code`, `cbeta_id`.

---

## §7. 10 kinh gốc CBETA (8 ID đã đối chiếu từ README FoJin; 2 ID verify)

| # | CBETA ID | Kinh |
|---|---|---|
| 1 | T0252 | 般若波羅蜜多心經 |
| 2 | T0262 | 妙法蓮華經 |
| 3 | T0475 | 維摩詰所說經 |
| 4 | T0270 | 佛說阿彌陀經 |
| 5 | T0099 | 雜阿含經 |
| 6 | T0026 | 中阿含經 |
| 7 | T0001 | 長阿含經 |
| 8 | T0125 | 增一阿含經 |
| 9 | T0210 | 法句經 |
| 10 | T0225 ⚠️ | 金光明經 |

Import catalog:
```powershell
docker exec fojin-test-backend python scripts/import_catalog.py
```
Verify ID trước khi nạp:
```powershell
docker exec fojin-test-postgres psql -U fojin_test -d fojin_test -c `
  "SELECT cbeta_id, title_zh, fascicle_count FROM buddhist_texts
   WHERE cbeta_id IN ('T0252','T0262','T0475','T0270','T0099','T0026','T0001','T0125','T0210','T0225');"
```
ID nào thiếu → thay bằng ID thật lấy từ `work_info.json`, cập nhật bảng trên.
Nạp từng kinh:
```powershell
foreach ($id in @('T0252','T0262','T0475','T0270','T0099','T0026','T0001','T0125','T0210','T0225')) {
  docker exec fojin-test-backend python scripts/import_content.py --work $id
}
```
Lần đầu sẽ clone sparse CBETA `xml-p5` (chỉ collection T).

---

## §8. Hướng dẫn soạn 10 kinh tiếng Việt

### 8.1 conquered directory
`E:\fojin-test\data\vn\` → container `/data/vn`, UTF-8 không BOM.

### 8.2 Quy tắc bắt buộc mỗi file

- Tên file: `<slug-khong-dau>.vi.txt`, chỉ chữ thường/số/-/
- Đầu file: khối header `; key: value`
- Phân tách đoạn: **đúng 1 dòng trống**
- **≥ 5 đoạn**/kinh; 200–900 ký tự/đoạn; ~2–5k ký tự/kinh

### 8.3 Quy tắc nội dung (V1–V4) để 6 tiêu chí có ý nghĩa test

- **V1** ≥2 câu tiếng Việt **có dấu**
- **V2** ≥2 câu là bản **không dấu** của V1 (giống hệt từng từ, chỉ bỏ thanh + đ→d ê→e ô→o ư→u ơ→o)
- **V3** ≥2 cụm cố định **≥ 4 từ**, lặp lại nguyên văn
- **V4** ≥1 đoạn trùng ý với bản Hán tương ứng (§7.1)

### 8.4 Bảng 10 kinh tiếng Việt (tên giả định) + đối chiếu Hán

| # | File | Tên kinh | Cụm cố định V3 | Đối chiếu Hán |
|---|---|---|---|---|
| 1 | `bat-nha-tam-kinh.vi.txt` | Bát Nhã Tâm Kinh | `色即是空`, `空即是色`, `như Lai không lại không đi` | **T0252** |
| 2 | `kim-cang-bat-nha.vi.txt` | Kim Cang Bát Nhã Kinh | `Như Lai vận đạo`, `vô danh thọ giới` | T0235 ⚠️ |
| 3 | `phap-hoa.vi.txt` | Pháp Hoa Tam Muội | `Một pháp không hai`, `thập phương Phật` | **T0262** |
| 4 | `lang-gia-tu.vi.txt` | Lăng Già Tự Kinh | `Phàm có hình thức`, `vô ký diệu kiến tâm` | **T0475** |
| 5 | `a-di-di.vi.txt` | Kinh A Di Đà | `tây phương cực lạc`, `một niệm liên miên` | **T0270** |
| 6 | `vo-luong-tho.vi.txt` | Kinh Vô Lượng Thọ | `vô lượng quang minh`, `đắp trang phương hành` | T0093 ⚠️ |
| 7 | `hoa-nghiem.vi.txt` | Kinh Hoa Nghiêm | `một thế nhất cương`, `chân như thị đại thế` | T0279 ⚠️ |
| 8 | `luc-do.vi.txt` | Lục Độ Bộ Kinh | `bát độ ba thứ`, `trí huệ ba thứ` | T1526 ⚠️ |
| 9 | `dai-bat-niet-ban.vi.txt` | Kinh Đại Bát Niết Bàn | `tất cả chúng sinh`, `vĩnh tận vô hữu dụ` | T0374 ⚠️ |
| 10 | `kim-trai.vi.txt` | Kinh Kim Trai Nhất Bữa | `một bữa no đủ`, `vô thọ lượng quang minh` | T0855 ⚠️ |

⚠️ = đối chiếu tham khảo, không dùng để so khớp tự động. Đối chiếu chắc chắn: **#1 T0252, #3 T0262, #4 T0475, #5 T0270**.

### 8.5 Format header & ví dụ mẫu (Bát Nhã Tâm Kinh)

```ini
; title: 般若波羅蜜多心經
; title_vi: Bát Nhã Tâm Kinh
; author: Đỗ Dung
; source: Nhà xuất bản Tôn Giác
; lang: vie
; juan: 1

Quán Bát Nhã Tự Tánh, thấy Năm Uẩn đều không, nên không có gì không, không có gì có, không có gì sinh, không có gì diệt, không có gì sạch, không có gì ô nhiễm, không có gì tăng, không có gì giảm. Trong sự không có gì ấy không sự, không chiêm niệm được. Vì không sự, không chiêm niệm được, nên không có sự nào trong tâm để nhận biết.

Sắc sắc không khác không, không sắc là sắc, sắc chính là không, không sắc chính là sắc. Giống vậy, là không, là các, là thức, là thức thể, là thế giới.

Đắc bất, bất đắc. Bất sinh bất diệt, bất tịnh bất dư, không có, không cần cho có. Vì không có sự nào cho nên, cũng không có gì để không cho. Do đó trong Phật giáo không có sự cho hay sự không cho.

... các đoạn khác ...
```

Nhét **cụm cố định** như `như Lai không lại không đi` và `Bát Nhã tâm kinh` vào đoạn đầu để test nguyên cụm.

### 8.6 §8.7 — Đặc tả `make_vn_drafts.py` (SINH NHÁP, CHƯA PHẢI BẢN DỊCH)

**Mục đích:** nếu người dùng chưa kịp soạn 10 file, agent **tự sinh bản nháp** để test chạy ngay.

⚠️ R4 cấm bật LLM → **không thể dịch máy**. Script dựa vào **pool câu tiếng Việt có sẵn** (do tác giả soạn trong §8.7.1) + **bỏ dấu tự động** + **trích Hán từ DB**. Phải ghi rõ trong báo cáo: *“khối A/B là câu mẫu phục vụ test, KHÔNG phải bản dịch chính thức”*.

**Chạy:**
```powershell
docker exec fojin-test-backend python scripts/make_vn_drafts.py --dry-run --out /data/vn
docker exec fojin-test-backend python scripts/make_vn_drafts.py --out /data/vn
```

**Mapping `SUTRAS` (đưa vào script, 10 mục):**
```python
SUTRAS = [
  {"slug":"bat-nha-tam-kinh","title_han":"般若波羅蜜多心經","title_vi":"Bát Nhã Tâm Kinh","cbeta_id":"T0252",
   "phrases":["Bát Nhã tâm kinh","như Lai không lại không đi","không sắc chính là sắc"],
   "sentences":[
     "Quán Bát Nhã Tự Tánh, thấy Năm Uẩn đều không, nên không có gì không, không có gì có.",
     "Sắc sắc không khác không, không sắc là sắc, sắc chính là không, không sắc chính là sắc.",
     "Đắc bất, bất đắc. Bất sinh bất diệt, bất tịnh bất dư, không có, không cần cho có.",
   ]},
  # ... 9 sutra khác, mỗi sutra có phrases[] + sentences[]
]
```

**Cấu trúc file sinh ra — 3 khối theo thứ tự:**

| Khối | Nội dung | Phục vụ test |
|---|---|---|
| **A** | ≥5 đoạn câu tiếng Việt **có dấu** (trộn `sentences[]` + `phrases[]`) | V1 → test 3 |
| **B** | **đúng** các câu ở A, bỏ dấu tự động theo quy tắc V2 (`strip_tone()`) | V2 → test 3 |
| **C** | trích đoạn Hán từ `text_contents` (`lang='lzh'`) của `cbeta_id` tương ứng | V4 → test tìm chéo 2 corpus |

Thêm dòng `; DRAFT-AGENT-GENERATED` và `--- noi-dung nham de test ---` trong header để đánh dấu.

**Hàm bỏ dấu (khớp quy tắc V2):**
```python
import unicodedata
_tone_map = str.maketrans({
  "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ": "aaaaa" + "aaaaaaaaaaa" * 0,
})
def strip_tone(s):
    decomposed = unicodedata.normalize("NFD", s)
    no_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return no_marks.replace("đ", "d").replace("Đ", "D")
```
(Chuỗi mapping nên đặt theo bảng chuyển 1-1 rõ ràng, không dùng computing mang mang.)

**Cơ chế:** `cbeta_id = "VN%03d"`; `ON CONFLICT DO UPDATE` trong `buddhist_texts` và `text_contents`; ES `_id = {text_id}_{juan}_vie`; `--dry-run` chỉ in kế hoạch; idempotent (ghi đè cùng tên file).

**Ghi rõ trong báo cáo:** nháp chỉ phục vụ kiểm thử, không phải bản dịch chính thức.

---

## §9. Import tiếng Việt

```powershell
docker exec fojin-test-backend python scripts/import_vn.py --dry-run --dir /data/vn
docker exec fojin-test-backend python scripts/import_vn.py --dir /data/vn
docker exec fojin-test-postgres psql -U fojin_test -d fojin_test -c `
  "SELECT lang, source_code, count(DISTINCT cbeta_id) texts, count(*) chunks
   FROM text_contents tc JOIN buddhist_texts bt ON bt.id=tc.text_id
   GROUP BY lang, source_code;"
```
Kỳ vọng: `lzh/cbeta 10` và `vie/vn_user 10`.

---

## §10. 6 tiêu chí test (điều kiện PASS)

| # | Tiêu chí | PASS condition |
|---|---|---|
| 1 | Tìm được cả 2 corpus | `色即是空` → 14 hit `lzh`; `Bát Nhã tâm kinh` → 6 hit `vie`; `bat nha tam kinh` → 6 hit `vie` |
| 2 | Lọc theo `lang`/`source_code` | 100% hit đúng filter, **0** hit rò rỉ |
| 3 | Có dấu / không dấu / nguyên cụm | `khong`≡`không` ✓ · `bat nha tam kinh`≡`Bát Nhã tâm kinh` ✓ · `色即是空` ✓ · `khong co tuong`≡`không có tướng` ✓ — **ghi nhận mismatch** `Bát nhả`≠`Bát Nhã` (không tính PASS/FAIL) |
| 4 | Mở đúng văn bản/đoạn | URL chứa đúng `text_id`+`juan_num`; nội dung khớp doc ES `_id` |
| 5 | Importer idempotent | Chạy lại Y HỌT: Postgres `count` và ES `_count` **không đổi** |
| 6 | Restart giữ dữ liệu | `restart` và `down/up -d` → count giữ nguyên, search vẫn работает |

---

## §11. Đo tài nguyên thực tế

```powershell
docker stats --no-stream fojin-test-postgres fojin-test-es fojin-test-redis fojin-test-backend fojin-test-frontend
docker exec fojin-test-postgres du -sh /var/lib/postgresql/data
```
Ghi vào báo cáo: RAM peak từng container, tổng, CPU TB, thời gian `up`→healthy, dung lượng 3 volume, thời gian import.

---

## §12. Lệnh start/stop và dọn riêng moi trường test

```powershell
cd E:\fojin-test\fojin
$C = "docker compose -p fojin-test -f docker-compose.yml -f ..\docker-compose.override.fojin-test.yml --env-file ..\.env"
$C up -d           # START
$C stop            # STOP giữ dữ liệu
$C restart         # RESTART
$C down            # DỪNG + xoá container
$C logs -f backend
```
Dọn RIÊNG moi trường (chỉ 3 volume của fojin-test, KHÔNG `docker system prune`):
```powershell
$C down
docker volume rm fojin-test-pgdata fojin-test-esdata fojin-test-redisdata
docker network rm fojin-test-net
docker ps -a --filter "name=fojin"
docker volume ls --filter "name=fojin-test"
```
Xóa toàn bộ (tùy chọn): `Remove-Item -Recurse -Force E:\fojin-test`.

---

## §13. Mẫu báo cáo bàn giao

`E:\fojin-test\docs\TEST-REPORT-FOJIN.md` — các mục:

1. Thông tin (ngày, máy, Docker, project, VPS không đụng, dự án khác không đụng)
2. URL local (3100 / 8100/docs / 9200 / health)
3. File đã thay đổi (`elasticsearch.py`, `import_vn.py`, `make_vn_drafts.py`?, override, .env)
4. Dữ liệu đã nhập (corpus/văn bản/chunks/ký tự)
5. Kết quả 6 tiêu chí (bằng chứng lệnh + ảnh)
6. Tài nguyên thực tế (RAM/CPU/volume/thời gian)
7. Lệnh start/stop/dọn
8. Known issues
9. Kết luận (đạt/không đạt, đề xuất sửa)

Sau khi điền xong phát `pipip`:
```powershell
[System.Media.SystemSounds]::Asterisk.Play()
[console]::Beep(880,150); [console]::Beep(1175,150); [console]::Beep(1568,300)
```

---

## §14. Ghi tiến độ

Sau khi có kết quả thật, cập nhật `docs/tasktodo.md` + `docs/ROLLBACK.md` của Đạo Ảnh — đây là repo **khác** (FoJin), không viết vào repo FoJin (R6).

---

## §15. Checklist trước khi xuất Plan Mode

- [x] Xác định đường dẫn ghi
- [x] Nội dung tự chứa — agent đọc file này setup được mà không cần hỏi
- [x] 2 thay đổi code (S1 analyzer `vie` + S2 `import_vn.py`) đã được duyệt
- [x] 10 kinh Hán + 10 kinh Việt giả định + bảng đối chiếu
- [x] §8.7 `make_vn_drafts.py` có full schema, mapping và code bỏ dấu
- [x] 6 tiêu chí với lệnh và ngưỡng PASS
- [x] Lệnh start/stop/dọn riêng moi trường
- [x] Mẫu báo cáo bàn giao
- [x] Điều kiện DỪNG theo R7
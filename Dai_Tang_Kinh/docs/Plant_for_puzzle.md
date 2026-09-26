# 📋 Kế Hoạch Triển Khai - Đề Án Puzzle Đại Tạng Kinh

> **Ngày tạo**: 2026-04-02  
> **Cập nhật**: 2026-04-05  
> **Nguồn tham khảo**: Puzzle.md (Ver 1.2 - 06/04/2026)  
> **Trạng thái**: Đang triển khai  
> **Version**: 5.0 (Prototype P0 Edition)

---

## 📌 Tổng Quan Dự Án

**Mục tiêu**: Số hóa 2000+ kinh sách Đại Tạng Kinh, xây dựng nền tảng khám phá tri thức Phật giáo dựa trên AI và Knowledge Graph.

**Phạm vi công việc**:
- Tích hợp dữ liệu từ DILA (Đài Loan), CBETA (Trung Quốc), Phả hệ Việt Nam (2000+ files)
- Xây dựng Knowledge Graph với Neo4j
- Phát triển AI Engine (NER, RAG, LLM)
- Tạo giao diện Zen UI cho việc đọc kinh và khám phá tri thức
- Phát triển Puzzle Engine cho giáo dục và gamification
- **Đạo Ảnh (Buddhist Heritage Mapping)**: Trực quan hóa lộ trình 49 năm thuyết pháp của Đức Phật và 2000 năm truyền thừa Phật giáo

**Công nghệ chính**:
- ETL Pipeline (Python)
- MongoDB + VectorDB (ChromaDB) + Neo4j
- FastAPI + React (Zen UI)
- LLM (GPT-4o/Claude/Llama)

---

## 🎯 Cấu Trúc Triển Khai (5 Phần - 32 Tasks)

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHẦN 0: PROTOTYPE P0 (Dashboard Trung Tâm)     [Chương 0]       │
├─────────────────────────────────────────────────────────────────────┤
│  PHẦN I: THIẾT LẬP NỀN TẢNG (Foundation)          [Chương 1-7]   │
├─────────────────────────────────────────────────────────────────────┤
│  PHẦN II: PHÁT TRIỂN MODULE PHẢ HỆ (Lineage)     [Chương 8-14]    │
├─────────────────────────────────────────────────────────────────────┤
│  PHẦN III: TÍCH HỢP PCD & KINH ĐIỂN             [Chương 15-21]   │
├─────────────────────────────────────────────────────────────────────┤
│  PHẦN IV: TỐI ƯU HÓA & TRIỂN KHAI THỰC ĐỊA      [Chương 22-28]   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 GIAI ĐOẠN 0: PROTOTYPE P0 - Dashboard Điều Khiển Trung Tâm (Chương 0)

### Mục tiêu: Điểm chạm duy nhất kết nối 2,000+ file phả hệ và toàn bộ kho kinh điển.

| Task | Mô Tả | Công Nghệ | Priority | Deadline |
|------|-------|-----------|----------|----------|
| **0.1** | **Dashboard Điều Khiển Trung Tâm** - Global Search + Lineage Visualizer + Metadata Overlay | React, D3.js | **Critical** | 15/05/2026 |
| **0.2** | **Global Search Engine** - AI tự động phân loại Query (Nhân vật → GraphDB; Giáo lý → RAG Kinh điển) | Python, GraphDB, Regex | **Critical** | 01/06/2026 |
| **0.3** | **Zero-RAM Query Engine** - Byte-offset mapping, chạy RAG trên VPS 3GB RAM, latency < 10ms | Python, mmap | **Critical** | 01/07/2026 |
| **0.4** | **Metadata Overlay Module** - Tự động hiển thị mã CBETA/DILA khi xem Tổ sư | JavaScript, CSS | **High** | 15/06/2026 |

### 🎯 Chi tiết Task 0.x:

#### Task 0.1: Dashboard Điều Khiển Trung Tâm
- **Mô tả**: Một điểm chạm duy nhất kết nối tất cả module
- **Tính năng**:
  - Global Search bar toàn cầu
  - Lineage Visualizer (cây truyền thừa)
  - Metadata Overlay (hiển thị ID)
- **Output**: React Dashboard component

#### Task 0.2: Global Search Engine
- **Mô tả**: AI tự động phân loại query
- **Logic**:
  ```python
  def classify_query(query):
      if contains_monk_name(query) or contains_lineage_terms(query):
          return "GRAPH_DB"  # Nhân vật, phả hệ
      elif contains_sutra_terms(query) or contains_dharma_terms(query):
          return "RAG_CANON"  # Giáo lý, kinh điển
      else:
          return "HYBRID"  # Cả hai
  ```
- **Output**: REST API `/api/search/classify`

#### Task 0.3: Zero-RAM Query Engine
- **Mục tiêu**: RAM < 100MB, Latency < 10ms
- **Cơ chế**: Byte-offset mapping thay vì load toàn bộ vào RAM
- **Output**: ZeroRAM Engine với Index file (.idx)

#### Task 0.4: Metadata Overlay
- **Mô tả**: Hiển thị mã CBETA/DILA khi hover/tap node
- **Output**: JavaScript component overlay

---

## PHẦN I: THIẾT LẬP NỀN TẢNG (Chương 1-7)

### Giai Đoạn 1: Data Engineering (ETL Pipeline)

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| **1.0** | **Puzzle Ecosystem Vision** - Xây dựng triết lý kết nối vạn vật qua dữ liệu số (Digital Interconnectedness), Ontology trong Phật giáo số | Graph Data, Ontology | ⏳ |
| **1.1** | **Single Source of Truth** - Quy chuẩn ID (dila_id, cbeta_id, pcd_id), mapping giữa 2000+ files | Linked Open Data (LOD), RDF | ⏳ |
| **1.2** | **Lineage Entity Analysis** - Pháp danh, pháp hiệu, truyền thừa, năm sinh/mất | Python, JSON/XML | ⏳ |
| **1.3** | **Scripture Entity Analysis** - CBETA XML/TEI parser (T01n0001...), TEI markup | lxml, BeautifulSoup | ⏳ |
| **1.4** | **Place Entity (GIS & PCD)** - GPS mapping các tổ đình, chùa chiền | Leaflet, QGIS, GeoJSON | ⏳ |
| **1.5** | **VPS & Docker Infrastructure** - Opencode environment, Graphic DB optimization | Docker Compose, K8s | ⏳ |
| **1.6** | **Security & Authorization** - OAuth2/JWT, phân quyền AI/Học giả/Người dùng | OAuth2, JWT | ⏳ |
| **1.7** | **Data Governance** - Bảo vệ 2000+ file gốc, GDPR compliance | Security frameworks | ⏳ |
| **1.8** | **AI Structure Analysis** - Tự động bóc tách cấu trúc 2000+ DOCX files (Paragraph, Styles, Metadata extraction) | Python, lxml, docx | ⏳ |

### Giai Đoạn 2: Database Infrastructure

| Task | Mô Tả | Công Nghệ | Status | Deadline |
|------|-------|-----------|--------|----------|
| **2.0** | **Kiến trúc Hai ngăn (Hybrid Database)** - Ngăn Văn bản (MongoDB) + Ngăn Quan hệ (Neo4j/GraphDB) | MongoDB + Neo4j | ⏳ | 15/05/2026 |
| 2.1 | MongoDB setup - Full-text storage cho kinh điển | MongoDB | ⏳ | 01/06/2026 |
| 2.2 | Vector DB setup - ChromaDB/Qdrant cho semantic search | ChromaDB | ⏳ | 01/06/2026 |
| 2.3 | Neo4j setup - Knowledge Graph cho phả hệ | Neo4j | ⏳ | 15/05/2026 |
| 2.4 | Data loading scripts | PyMongo, neo4j-driver | ⏳ | 01/07/2026 |

---

## PHẦN II: PHÁT TRIỂN MODULE PHẢ HỆ (Chương 8-14)

### Giai Đoạn 3: Graph Database & Lineage

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| **3.0** | **Relational & Graph DB Design** - Thiết kế Database Phả hệ (Thầy-Trò, Pháp quyến), chuyển đổi 2000+ files tĩnh sang Graphic DB | Neo4j, GraphDB | ⏳ |
| **3.1** | **Neo4j Graph DB - Phả hệ** - Quan hệ Thầy-Trò (Succession), Pháp quyến (Clan) | Neo4j, NetworkX | ⏳ |
| **3.1.1** | **Ontology Design** - Bản đồ Thực thể: Kinh, Phật, Bồ Tát, Khái Niệm, Địa Điểm (có GPS metadata) | RDF, OWL | ⏳ |
| **3.1.2** | **Relationship Types** - THUYET (Thuyết giảng), XUATHIEN_TRONG, TUONG_DONG (Alias mapping) | Neo4j Cypher | ⏳ |
| **3.1.3** | **Entity Mapping System** - Hệ thống đồng bộ tên gọi đa ngôn ngữ (Hán-Việt-Pali-Sanskrit), Alias resolution | Python, rapidfuzz | ⏳ |
| **3.2** | **Tree Rendering Algorithm** - Cây phả hệ tương tác cho 2000+ thực thể | D3.js, Vis.js, Cytoscape | ⏳ |
| **3.2.1** | **3D Knowledge Graph** - Mở rộng cây phả hệ sang không gian 3D | Three.js, WebGL | ⏳ |
| **3.3** | **ETL DILA Integration** - Tự động tra cứu Authority ID (A001234...) | ETL Pipeline | ⏳ |
| **3.4** | **Image Management (IIIF)** - Chân dung, thủ bút, bảo tháp | IIIF, S3/Cloud | ⏳ |
| **3.5** | **Elasticsearch** - Tìm kiếm xuyên suốt Kinh điển + Phả hệ | Elasticsearch | ⏳ |
| **3.5.1** | **Semantic Search** - Vector Database & Embedding cho tìm kiếm ngữ nghĩa | ChromaDB, Qdrant | ⏳ |
| **3.6** | **UX/UI Interface** - Drill-down (nhấn vào node xem chi tiết) | React, Vue | ⏳ |
| **3.6.1** | **Voice UI** - Giao diện giọng nói tra cứu kinh điển (tương lai) | Speech Recognition, TTS | ⏳ |
| **3.7** | **CMS - Content Management** - Collaborative Knowledge Management | CMS Framework | ⏳ |

### Giai Đoạn 4: AI & ML Pipeline

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| 4.1 | Embedding model setup | sentence-transformers | ⏳ |
| 4.2 | Entity Extraction (NER) | spaCy, transformers | ⏳ |
| 4.3 | Knowledge Graph construction | Neo4j, python-igraph | ⏳ |
| **4.3.1** | **Core Knowledge Graph** - Xây dựng 500 thực thể quan trọng nhất (Phật, Bồ Tát, Tổ sư, Kinh điển cốt lõi) | Neo4j, NetworkX | ⏳ |
| 4.4 | RAG Pipeline (Hybrid Search) | LangChain, LlamaIndex | ⏳ |
| 4.5 | LLM Integration (GPT-4o/Claude/Llama) | OpenAI API, Ollama | ⏳ |
| **4.6** | **Multilingual Fine-tuning** - Fine-tuning mô hình ngôn ngữ trên tập dữ liệu đối chiếu Hán - Việt - Pali | NMT, transformers | ⏳ |
| **4.7** | **AI Ethics Guardrails** - Thiết lập "Guardrails" ngăn chặn AI diễn giải sai lệch giáo lý | LangChain, Guardrails | ⏳ |

---

## PHẦN III: TÍCH HỢP PCD & KINH ĐIỂN (Chương 15-21)

### Giai Đoạn 5: CBETA & PCD Integration

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| **5.0** | **CBETA API Module** - Module kết nối CBETA API | RESTful API | ⏳ |
| **5.1** | **CBETA API Integration** - Trình đọc kinh tự động gợi ý dựa trên nhân vật | RESTful API, GraphQL | ⏳ |
| **5.1.1** | **GraphQL Optimization** - GraphQL tối ưu truy vấn kinh văn | GraphQL | ⏳ |
| **5.2** | **GPS Historical Mapping** - Trực quan hóa dấu chân Tổ sư, Trajectory Analysis | Leaflet, NetworkX | ⏳ |
| **5.2.1** | **Historical GIS** - QGIS/ArcGIS phân tích không gian lịch sử | QGIS, ArcGIS | ⏳ |
| **5.2.2** | **VR/AR 4D Map** - Bản đồ VR/AR tái hiện chùa chiền 4D (tương lai) | Unity, WebXR | ⏳ |
| **5.3** | **Multi-layer Annotation** - Chú thích đa tầng W3C Web Annotation | W3C Web Annotation | ⏳ |
| **5.4** | **Network Analysis** - Thống kê mật độ truyền thừa, ảnh hưởng tông phái | igraph, NetworkX | ⏳ |
| **5.4.1** | **Centrality & Clustering** - Lý thuyết đồ thị (Centrality, Clustering) | NetworkX, igraph | ⏳ |
| **5.5** | **Buddhist Dictionary** - Bộ từ điển tích hợp, Auto Translation Hán/Pali | NMT, transformers | ⏳ |
| **5.6** | **Event Timeline** - Quản lý sự kiện lịch sử, Dynamic Timelines | D3.js Timeline | ⏳ |
| **5.6.1** | **Dynamic Timelines** - Dynamic Timelines kết nối đa quốc gia | D3.js | ⏳ |
| **5.7** | **Open Data API** - Xuất bản dữ liệu, Knowledge Marketplace | GraphQL, Swagger, Web3 | ⏳ |

### Giai Đoạn 6: Puzzle Engine & Gamification

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| 6.1 | KG-based puzzle generator | Neo4j, NetworkX | ⏳ |
| 6.2 | Quiz engine (Multiple choice) | Python | ⏳ |
| 6.3 | Gamification system (Levels, Points) | Python, Redis | ⏳ |
| 6.4 | Leaderboard | FastAPI, Redis | ⏳ |

---

## PHẦN IV: TỐI ƯU HÓA & TRIỂN KHAI THỰC ĐỊA (Chương 22-28)

### Giai Đoạn 7: Testing & Optimization

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| **7.1** | **Testing & QA** - Rà soát tính logic và toàn vẹn dữ liệu | Unit/Integration Test, Formal Verification | ⏳ |
| **7.2** | **Performance Tuning** - Tối ưu truy vấn Graph DB, Redis Caching | Redis, AI-driven tuning | ⏳ |
| **7.3** | **Content Strategy** - Google Analytics | Google Analytics | ⏳ |
| **7.4** | **International Collaboration** - Đồng bộ DILA/SAT | Data exchange protocols | ⏳ |
| **7.5** | **Training & Documentation** - Hướng dẫn sử dụng cho học viện | Documentation Frameworks | ⏳ |
| **7.6** | **Maintenance & Backup** - Backup định kỳ, DevOps/SRE | DevOps/SRE | ⏳ |
| **7.7** | **Phase II Roadmap** - Mở rộng Nam/Tạng truyền | Quantum Computing (future) | ⏳ |

### Giai Đoạn 8: Backend API

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| 8.1 | FastAPI setup | FastAPI | ⏳ |
| 8.2 | API Endpoints (Search, RAG, KG) | FastAPI, Pydantic | ⏳ |
| 8.3 | Authentication & Rate limiting | OAuth2, slowapi | ⏳ |
| 8.4 | API Documentation | Swagger UI | ⏳ |

### Giai Đoạn 9: Frontend (Zen UI)

| Task | Mô Tả | Công Nghệ | Status |
|------|-------|-----------|--------|
| 9.1 | React setup (Vite) | React, Vite | ⏳ |
| 9.2 | Core components (Layout, Navigation) | React, Tailwind | ⏳ |
| 9.3 | Kinh đọc giao diện | React, D3.js/Cytoscape | ⏳ |
| 9.4 | Search interface (Hybrid) | React, Fuse.js | ⏳ |
| 9.5 | RAG Chat interface | React, Markdown | ⏳ |

---

### Giai Đoạn 10: Đạo Ảnh (Buddhist Heritage Mapping)

| Task | Mô Tả | Công Nghệ | Status | Mapping Puzzle |
|------|-------|-----------|--------|-----------------|
| **10.1** | **P2.5: Admin GUI** - Giao diện việt hóa cho non-tech team (Edit VI, Export JSON) | Flask, HTML/JS | ✅ | **MỚI** |
| **10.2** | **P2.6: GPS Compare Tool** - So sánh GPS với DILA updates (>100m threshold) | Python | ✅ | **MỚI** |
| 10.3 | P1: Ontology Place Class → Xem Task 1.1, 3.1.1 | RDF, OWL | ✅ | → 1.1, 3.1.1 |
| 10.4 | P2: DILA/CBETA Data → Xem Task 3.3 | Python, API | ✅ | → 3.3 |
| 10.5 | P4: Quét phả hệ → Xem Task 1.2 | Python, Regex | ⏳ | → 1.2 |
| 10.6 | P5: Mapping → Xem Task 1.2 | rapidfuzz | ⏳ | → 1.2 |
| 10.7 | P6: Dịch & Bio → Xem Task 5.5 | opencc, pyvi | ⏳ | → 5.5 |
| 10.8 | P7: Geocoding VN → Xem Task 1.4 | Nominatim API | ⏳ | → 1.4 |
| 10.9 | P9: Map Interface → Xem Task 3.6 | Leaflet, Mapbox | ⏳ | → 3.6 |
| 10.10 | P10: Layer System → Xem Task 3.6 | Leaflet | ⏳ | → 3.6 |
| 10.11 | P11: Pathfinding → Xem Task 3.2 | NetworkX | ⏳ | → 3.2 |
| 10.12 | P12: Timeline Slider → Xem Task 5.6 | D3.js | ⏳ | → 5.6 |
| 10.13 | P13: Deepsearch → Xem Task 5.0, 5.1 | FastAPI | ⏳ | → 5.0, 5.1 |
| 10.14 | P14: Performance → Xem Task 7.2 | Redis | ⏳ | → 7.2 |
| 10.15 | P15: Security → Xem Task 1.6, 1.7 | Nginx, SSL | ⏳ | → 1.6, 1.7 |

**Ghi chú**: Các task trùng với Puzzle.md sẽ reference đến task gốc. Chỉ có P2.5 và P2.6 là đặc thù riêng của Đạo Ảnh.

---

## 📊 Ưu Tiên MVP (30 Công Nghệ)

1. **Zero-RAM Query Engine** - 🔥 **NEW - Priority #1** - Byte-offset mapping, < 10ms, 3GB RAM
2. **Prototype P0 Dashboard** - 🔥 **NEW - Priority #2** - Điểm chạm duy nhất
3. **Global Search AI** - 🔥 **NEW - Priority #3** - Tự động phân loại Query
4. **Hybrid Database Architecture** - 🔥 **UPDATED** - MongoDB + Neo4j
5. **Metadata Overlay** - 🔥 **NEW - Priority #5** - Hiển thị CBETA/DILA ID
6. **AI Structure Analysis** - Tự động bóc tách 2000+ DOCX
7. **Auto-Puzzle Generator** - Engine tạo câu đố từ KG
8. **Semantic Hybrid Search** - Keyword + Vector search
9. **Verified RAG** - Hỏi đáp có trích dẫn nguồn
10. **Core Knowledge Graph** - 500 thực thể quan trọng
11. **Single Source of Truth** - Quy chuẩn ID (LOD/RDF)
12. **IIIF Image Server** - Quản lý hình ảnh chuẩn quốc tế
13. **W3C Web Annotation** - Chú thích đa tầng
14. **Network Analysis** - Centrality & Clustering
15. **Elasticsearch** - Tìm kiếm xuyên suốt
16. **Neo4j Graph DB** - Phả hệ Thầy-Trò
17. **Tree Rendering** - Cây phả hệ tương tác
18. **Event Timeline** - Quản lý sự kiện lịch sử
19. **Open Data API** - Xuất bản dữ liệu mở
20. **DevOps/SRE** - Bảo trì & Backup
21. **Multilingual Fine-tuning** - Fine-tuning Hán-Việt-Pali
22. **AI Ethics Guardrails** - Bảo vệ đạo đức AI
23. **Ontology Design** - Bản đồ thực thể (Kinh, Phật, Bồ Tát, Khái Niệm, Địa Điểm)
24. **VR/AR 4D Map** - Bản đồ thực tế ảo tái hiện chùa chiền
25. **3D Knowledge Graph** - Cây phả hệ 3D
26. **Voice UI** - Giao diện giọng nói tra cứu kinh điển
27. **Global Search AI** - Tự động phân loại Query
28. **Lineage Visualizer** - Trực quan hóa cây truyền thừa + Mapping ID
29. **Metadata Overlay** - Hiển thị CBETA/DILA ID
30. **Binary Search Index** - Thuật toán tìm kiếm nhị phân trên file Index

---

## 💰 Lộ Trình Tài Chính Chi Tiết (2026-2045)

### Giai Đoạn 1: Nền Tảng (2026-2030) - $1.0M - $2.5M

| Năm | Quý | Milestone | Ngân sách | Status |
|-----|-----|-----------|-----------|--------|
| 2026 | Q2 | Prototype P0 Dashboard | $50K | ⏳ |
| 2026 | Q3 | ETL Pipeline + Graph DB | $50K | ⏳ |
| 2026 | Q4 | Zero-RAM Engine + Global Search | $50K | ⏳ |
| 2027 | Q1-Q2 | AI Foundation (NER, Embedding) | $75K | ⏳ |
| 2027 | Q3-Q4 | RAG Engine Beta + Zen UI | $100K | ⏳ |
| 2028 | Q1-Q4 | CBETA Integration + Testing | $150K | ⏳ |
| 2029 | Q1-Q4 | MVP Launch + Optimization | $200K | ⏳ |
| 2030 | Q1-Q4 | Scale + International Prep | $150K | ⏳ |

### Giai Đoạn 2: AI Chuyên Sâu (2031-2035) - $1.5M - $4.0M

| Năm | Quý | Milestone | Ngân sách | Status |
|-----|-----|-----------|-----------|--------|
| 2031 | Q1-Q2 | Fine-tuning Model (Hán-Việt-Pali) | $100K | ⏳ |
| 2031 | Q3-Q4 | Multilingual Support | $100K | ⏳ |
| 2032 | Q1-Q4 | Mobile App Development | $150K | ⏳ |
| 2033 | Q1-Q4 | Enterprise Features | $150K | ⏳ |
| 2034 | Q1-Q4 | Market Expansion | $150K | ⏳ |
| 2035 | Q1-Q4 | Advanced AI Features | $100K | ⏳ |

### Giai Đoạn 3: Quốc Tế (2036-2040) - $0.8M - $2.0M

| Năm | Quý | Milestone | Ngân sách | Status |
|-----|-----|-----------|-----------|--------|
| 2036 | - | SAT Integration | $50K | ⏳ |
| 2037 | - | 84000.co.kr Integration | $50K | ⏳ |
| 2038 | - | Global Network Expansion | $100K | ⏳ |
| 2039 | - | Research Partnerships | $75K | ⏳ |
| 2040 | - | Open Data Ecosystem | $75K | ⏳ |

### Giai Đoạn 4: Bền Vững (2041-2045) - $1.2M - $3.0M

| Năm | Quý | Milestone | Ngân sách | Status |
|-----|-----|-----------|-----------|--------|
| 2041 | - | Quantum Readiness | $100K | ⏳ |
| 2042-2044 | - | Maintenance + Updates | $200K | ⏳ |
| 2045 | - | Permanent Preservation | $50K | ⏳ |

**Tổng ngân sách dự kiến**: $3.5M - $9.5M

---

## 🎯 Action Items Cụ Thể (Immediate)

| Action ID | Mô tả | Deadline | Status | Owner |
|-----------|-------|----------|--------|-------|
| **ACT-1** | Khởi tạo môi trường Docker trên VPS | 15/04/2026 | ⏳ | AI |
| **ACT-2** | Viết script convert_doc_to_jsonl.py | 30/04/2026 | ⏳ | AI |
| **ACT-3** | Thiết lập Database Neo4j cho 2000+ hồ sơ | 15/05/2026 | ⏳ | AI |
| **ACT-4** | Triển khai Global Search Engine | 01/06/2026 | ⏳ | AI |
| **ACT-5** | Tối ưu Zero-RAM Engine (<10ms) | 01/07/2026 | ⏳ | AI |
| **ACT-6** | Thiết kế Metadata Overlay (CBETA/DILA) | 15/06/2026 | ⏳ | AI |
| **ACT-7** | Tích hợp CBETA API | 01/08/2026 | ⏳ | AI |
| **ACT-8** | Xây dựng 500 Core Entities KG | 01/09/2026 | ⏳ | AI |
| **ACT-9** | Triển khai Zen UI Beta | 01/10/2026 | ⏳ | AI |
| **ACT-10** | MVP Launch | 01/01/2027 | ⏳ | AI |

---

## 📁 Cấu Trúc Folder Dự Án

```
Dai_Tang_Kinh/
├── app/
│   ├── frontend/          # React Frontend (Zen UI)
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── stores/
│   │   │   ├── utils/
│   │   │   └── styles/
│   │   ├── public/
│   │   ├── package.json
│   │   └── vite.config.js
│   │
│   └── backend/           # FastAPI Backend
│       ├── api/
│       │   └── v1/
│       │       └── endpoints/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       │   ├── ai/
│       │   ├── rag/
│       │   └── kg/
│       ├── db/
│       └── main.py
│
├── daoanh/                # Dự án Đạo Ảnh (Buddhist Heritage Mapping)
│   ├── app.py             # Flask backend
│   ├── admin/             # Admin GUI (Basic Auth)
│   ├── src/               # Python scripts
│   ├── data/              # Dữ liệu DILA/CBETA
│   ├── ontology/          # RDF Ontology
│   ├── static/            # Static files
│   └── home/              # Home page
│
├── puzzle-engine/         # Puzzle/Quiz Engine
├── data/                  # Dữ liệu
│   ├── raw/              # 2000+ docx files
│   ├── processed/        # Đã xử lý
│   │   ├── chunks/
│   │   ├── embeddings/
│   │   └── kg/
│   └── external/         # CBETA, DILA
├── etl-pipeline/         # Data Engineering
├── ml-models/            # ML/AI Models
├── docs/                 # Documentation
├── tests/                # Integration tests
└── deploy/               # Deployment configs
```

---

## 📝 Log Thảo Luận

### 2026-04-04 - Buổi 4: Bổ sung 3 chức năng còn thiếu từ Puzzle.md

**Người tham gia**: AI Assistant

**Nội dung thảo luận**:
- So sánh Puzzle.md (Ver 1.0) với Plant_for_puzzle.md
- Xác định 3 chức năng còn thiếu chưa được add vào kế hoạch

**Kết quả phân tích**:
- 7/10 features từ Puzzle.md đã có sẵn trong Plant
- 3 features MỚI cần bổ sung:

| # | Chức năng | Vị trí Puzzle.md | Mức ưu tiên |
|---|-----------|------------------|-------------|
| 1 | **AI Structure Analysis** - Tự động bóc tách 2000+ DOCX | Ver 1.0, dòng 324 | **Critical** |
| 2 | **Core Knowledge Graph** - 500 thực thể quan trọng | Ver 1.0, dòng 332 | **High** |
| 3 | **Entity Mapping System** - Đồng bộ tên đa ngôn ngữ | Ver 1.0, dòng 336 | **High** |

**Quyết định**:
- Thêm Task 1.8: AI Structure Analysis vào Giai Đoạn 1
- Mở rộng Task 4.3 thành 4.3.1: Core Knowledge Graph (500 entities)
- Thêm Task 3.1.3: Entity Mapping System vào Giai Đoạn 3

---

### 2026-04-03 - Buổi 3: Cập nhật chức năng bổ sung từ Puzzle.md

**Người tham gia**: AI Assistant

**Nội dung thảo luận**:
- Đọc và phân tích Puzzle.md (Ver 1.1) để tìm các chức năng bổ sung mới
- Bổ sung các task và subtask từ Puzzle.md vào Plant_for_puzzle.md
- Cập nhật danh sách MVP từ 20 lên 26 công nghệ

**Chức năng mới bổ sung**:
- **Task 1.0**: Puzzle Ecosystem Vision - Triết lý kết nối vạn vật + Ontology
- **Task 3.0**: Relational & Graph DB Design - Database Phả hệ
- **Task 3.1.1**: Ontology Design - Bản đồ Thực thể (Kinh, Phật, Bồ Tát, Khái Niệm, Địa Điểm)
- **Task 3.1.2**: Relationship Types - THUYET, XUATHIEN_TRONG, TUONG_DONG
- **Task 3.2.1**: 3D Knowledge Graph
- **Task 3.5.1**: Semantic Search - Vector Database & Embedding
- **Task 3.6.1**: Voice UI - Giao diện giọng nói (tương lai)
- **Task 4.6**: Multilingual Fine-tuning - Fine-tuning Hán-Việt-Pali
- **Task 4.7**: AI Ethics Guardrails
- **Task 5.0**: CBETA API Module
- **Task 5.1.1**: GraphQL Optimization
- **Task 5.2.1**: Historical GIS - QGIS/ArcGIS
- **Task 5.2.2**: VR/AR 4D Map (tương lai)
- **Task 5.4.1**: Centrality & Clustering
- **Task 5.6.1**: Dynamic Timelines đa quốc gia
- **Giai Đoạn 10**: Đạo Ảnh (Buddhist Heritage Mapping) - 15 Tasks (P1-P15)

**Quyết định**:
- Thêm prefix "**" cho các task quan trọng từ Puzzle.md
- Thêm subtask (3.x.x) cho các chức năng mở rộng
- Đánh dấu các tính năng tương lai với (tương lai)
- Move folder daoanh vào Dai_Tang_Kinh/daoanh/
- Cập nhật cấu trúc folder dự án

---

### 2026-04-03 - Buổi 2: Cập nhật Kế hoạch từ Puzzle.md

**Người tham gia**: AI Assistant

**Nội dung thảo luận**:
- Đọc Puzzle.md (Ver 1.1) với 28 Chương chia 4 Phần
- Mapping 1:1 từ Puzzle.md sang Plant_for_puzzle.md
- Mở rộng từ 7 giai đoạn → 9 giai đoạn (4 Phần, 28 Tasks)
- Thêm 10 công nghệ mới (IIIF, W3C Annotation, Network Analysis, v.v.)
- Hợp nhất 2 file plan (Plant_for_puzzle + Plan_for_puzzle) thành Plant_for_puzzle.md (Full Edition)

**Quyết định**:
- Giữ nguyên cấu trúc folder đã thiết lập
- Bổ sung mapping từng Task với Chương trong Puzzle.md
- Thêm Priority MVP với 20 công nghệ

**Câu hỏi mở**:
1. File .docx mẫu nằm ở đâu?
2. Có sẵn 2000+ files chưa?
3. Thứ tự ưu tiên giai đoạn nào?

---

### 2026-04-02 - Buổi 1: Khởi động dự án

**Người tham gia**: AI Assistant

**Nội dung thảo luận**:
- Đọc Puzzle.md - Đề án gốc từ user cung cấp
- Xác định 7 giai đoạn triển khai
- Lập danh sách 10 công nghệ ưu tiên cho MVP
- Xác định cấu trúc folder dự án theo tiêu chuẩn dev tiên tiến

**Quyết định**:
- Chờ user cung cấp file .docx mẫu (Kinh Kim Cang) để bắt đầu Task 1.1
- Chờ xác nhận nguồn dữ liệu 2000+ files

---

## ❓ Câu Hỏi Chờ Xác Nhận

- [ ] **Nguồn dữ liệu**: 2000+ file .docx nằm ở đâu?
- [ ] **File mẫu**: Có thể cung cấp file Kinh Kim Cang .docx?
- [ ] **Tài nguyên server**: Có đủ RAM/GPU cho LLM on-premise?
- [ ] **Team size**: Bao nhiêu người để phân công?

---

## 🔄 Các Bước Tiếp Theo

1. Chờ user cung cấp file .docx mẫu
2. Bắt đầu Task 1.1: Khảo sát cấu trúc DOCX
3. Tạo folder Dai_Tang_Kinh/
4. Thiết lập ETL pipeline base

---

## 🔗 Liên Kết Dự Án Song Song

| Dự án | Path | Status |
|-------|------|--------|
| **Thiền Tông Phả Hệ** | `/opt/phatphaponline_gradio/truyenthua/visjs-app/` | ✅ Đang hoạt động |
| **Đạo Ảnh** | `Dai_Tang_Kinh/daoanh/` | ✅ Đã tích hợp |

---

## 📋 Task Mapping (Puzzle.md → Plan)

| Puzzle Chương | Task ID | Mô Tả |
|---------------|---------|-------|
| **Chương 0** | **0.1 - 0.4** | **Prototype P0 - Dashboard Trung Tâm** |
| Chương 1 | 1.0 | Puzzle Ecosystem Vision |
| Chương 2 | 1.1 | Single Source of Truth |
| Chương 3 | 1.2 | Lineage Entity Analysis |
| Chương 4 | 1.3 | Scripture Entity Analysis |
| Chương 5 | 1.4 | Place Entity (GIS & PCD) |
| Chương 6 | 1.5 | VPS & Docker Infrastructure |
| Chương 7 | 1.6, 1.7 | Security & Data Governance |
| Chương 8 | 3.0, 3.1 | Relational & Graph DB Design, Neo4j Graph DB |
| Chương 9 | 3.2 | Tree Rendering Algorithm, 3D Knowledge Graph |
| Chương 10 | 3.3 | ETL DILA Integration |
| Chương 11 | 3.4 | Image Management (IIIF) |
| Chương 12 | 3.5, 3.5.1 | Elasticsearch, Semantic Search |
| Chương 13 | 3.6 | UX/UI Interface, Voice UI |
| Chương 14 | 3.7 | CMS - Content Management |
| Chương 15 | 5.0, 5.1 | CBETA API Module, Integration |
| Chương 16 | 5.2 | GPS Historical Mapping, Historical GIS, VR/AR 4D |
| Chương 17 | 5.3 | Multi-layer Annotation |
| Chương 18 | 5.4 | Network Analysis, Centrality & Clustering |
| Chương 19 | 5.5 | Buddhist Dictionary |
| Chương 20 | 5.6 | Event Timeline, Dynamic Timelines |
| Chương 21 | 5.7 | Open Data API, Knowledge Marketplace |
| Chương 22 | 7.1 | Testing & QA |
| Chương 23 | 7.2 | Performance Tuning |
| Chương 24 | 7.3 | Content Strategy |
| Chương 25 | 7.4 | International Collaboration |
| Chương 26 | 7.5 | Training & Documentation |
| Chương 27 | 7.6 | Maintenance & Backup |
| Chương 28 | 7.7 | Phase II Roadmap |
| Puzzle Ver 1.0 | 4.6, 4.7 | Multilingual Fine-tuning, AI Ethics Guardrails |
| Đạo Ảnh P1-P15 | 10.1-10.15 | Buddhist Heritage Mapping (58,480 places) |
| **Puzzle Ver 1.0** | **1.8** | **AI Structure Analysis** (bổ sung mới) |
| **Puzzle Ver 1.0** | **3.1.3** | **Entity Mapping System** (bổ sung mới) |
| **Puzzle Ver 1.0** | **4.3.1** | **Core Knowledge Graph** (bổ sung mới) |
| **Puzzle Ver 1.2** | **0.1 - 0.4** | **Prototype P0** (bổ sung mới - 06/04) |
| **Puzzle Ver 1.2** | **2.0** | **Hybrid Database Architecture** (bổ sung mới) |

---

## 📋 Đạo Ảnh ↔ Puzzle Mapping

| Đạo Ảnh Task | Puzzle Chương | Plan Task | Ghi chú |
|--------------|---------------|-----------|---------|
| P2.5: Admin GUI | - | **10.1** | ✅ **MỚI** - Đặc thù riêng Đạo Ảnh |
| P2.6: GPS Compare | - | **10.2** | ✅ **MỚI** - Đặc thù riêng Đạo Ảnh |
| P1: Ontology Place | Chương 2, 4 | 1.1, 3.1.1 | ✅ → Task gốc |
| P2: DILA/CBETA | Chương 10 | 3.3 | ✅ → Task gốc |
| P4: Quét phả hệ | Chương 3 | 1.2 | ✅ → Task gốc |
| P5: Mapping | Chương 3 | 1.2 | ✅ → Task gốc |
| P6: Dịch & Bio | Chương 19 | 5.5 | ✅ → Task gốc |
| P7: Geocoding VN | Chương 5 | 1.4 | ✅ → Task gốc |
| P8: QA Review | Chương 22 | 7.1 | ✅ → Task gốc |
| P9: Map Interface | Chương 13 | 3.6 | ✅ → Task gốc |
| P10: Layer System | Chương 13 | 3.6 | ✅ → Task gốc |
| P11: Pathfinding | Chương 9 | 3.2 | ✅ → Task gốc |
| P12: Timeline | Chương 20 | 5.6 | ✅ → Task gốc |
| P13: Deepsearch | Chương 15 | 5.0, 5.1 | ✅ → Task gốc |
| P14: Performance | Chương 23 | 7.2 | ✅ → Task gốc |
| P15: Security | Chương 7 | 1.6, 1.7 | ✅ → Task gốc |

### 🔄 Kết luận
- **2 tasks** Đạo Ảnh là **MỚI** (không trùng): P2.5 (Admin GUI), P2.6 (GPS Compare Tool)
- **13 tasks** còn lại **trùng** với Puzzle.md - sẽ reference đến task gốc

---

## 🗂️ Nguồn Tham Khảo

- **Puzzle.md** (Ver 1.2 - 06/04/2026): Đề án gốc - 28 Chương + Chương 0 (Prototype P0)
- **Puzzle.md** (Ver 1.1): Đề án bổ sung - RAG, Zen UI, Puzzle Engine
- **Puzzle.md** (Ver 1.0): Đề án bổ sung - RAG, Zen UI, Puzzle Engine
- **Plant_for_puzzle.md** (Ver 4.0): Bản Enhanced Edition
- **phat_to_dao_anh.md**: Đạo Ảnh - Buddhist Heritage Mapping (58,480 places)

---

## 📝 Log Thay Đổi

### 2026-04-05 - Buổi 5: Cập nhật từ Puzzle.md (Ver 1.2 - 06/04/2026)

**Người cập nhật**: AI Assistant

**Nguồn**: So sánh Puzzle.md (06/04/2026) vs Plant_for_puzzle.md (03/04/2026)

**Ý tưởng MỚI phát hiện (8 items)**:

| # | Ý tưởng | Vị trí Puzzle.md | Priority |
|---|---------|-------------------|----------|
| 1 | **Prototype P0 Dashboard** - Điểm chạm duy nhất | Chương 0 | **Critical** |
| 2 | **Global Search AI** - Phân loại tự động Query | Chương 0 | **Critical** |
| 3 | **Lineage Visualizer + Mapping ID** - Authority ID trên node | Chương 0 | **High** |
| 4 | **Zero-RAM Engine** - < 10ms latency, 3GB RAM | Chương 0, 23 | **Critical** |
| 5 | **Metadata Overlay** - Hiển thị CBETA/DILA ID | Chương 0 | **High** |
| 6 | **Hai ngăn Database** - MongoDB + Neo4j | Chương 2 | **High** |
| 7 | **Lộ trình Tài chính** - 20 năm chi tiết theo quý/năm | Chương 15 | **Medium** |
| 8 | **Action Items** - Timeline cụ thể với deadline | Chương 28 | **High** |

**Quyết định**:
- ✅ Thêm Giai đoạn 0: Prototype P0 (Tasks 0.1 - 0.4)
- ✅ Mở rộng Task 2.x thành Task 2.0: Kiến trúc Hai ngăn (Hybrid Database)
- ✅ Thêm section Lộ trình Tài chính theo quý/năm (2026-2045)
- ✅ Thêm Action Items với deadline cụ thể (10 Actions)
- ✅ Cập nhật MVP list từ 26 → 30 công nghệ
- ✅ Cập nhật Version lên 5.0 (Prototype P0 Edition)

**Thay đổi cụ thể**:
1. Thêm PHẦN 0: Prototype P0 vào cấu trúc triển khai
2. Thêm 4 Tasks mới (0.1 - 0.4) với chi tiết và deadline
3. Thêm Task 2.0: Hybrid Database Architecture
4. Thêm Lộ trình Tài chính 4 giai đoạn với chi tiết theo quý
5. Thêm Action Items (ACT-1 đến ACT-10) với deadline
6. Cập nhật MVP: Thêm 4 items mới (Zero-RAM, P0 Dashboard, Global Search AI, Metadata Overlay)
7. Cập nhật Task Mapping: Thêm Chương 0 và các tasks mới
8. Cập nhật Version number: 4.0 → 5.0

---

### 2026-04-04 - Buổi 4: Bổ sung 3 chức năng còn thiếu từ Puzzle.md

**Người tham gia**: AI Assistant

**Nội dung thảo luận**:
- So sánh Puzzle.md (Ver 1.0) với Plant_for_puzzle.md
- Xác định 3 chức năng còn thiếu chưa được add vào kế hoạch

**Kết quả phân tích**:
- 7/10 features từ Puzzle.md đã có sẵn trong Plant
- 3 features MỚI cần bổ sung:

| # | Chức năng | Vị trí Puzzle.md | Mức ưu tiên |
|---|-----------|------------------|-------------|
| 1 | **AI Structure Analysis** - Tự động bóc tách 2000+ DOCX | Ver 1.0 | **Critical** |
| 2 | **Core Knowledge Graph** - 500 thực thể quan trọng | Ver 1.0 | **High** |
| 3 | **Entity Mapping System** - Đồng bộ tên đa ngôn ngữ | Ver 1.0 | **High** |

**Quyết định**:
- Thêm Task 1.8: AI Structure Analysis vào Giai Đoạn 1
- Mở rộng Task 4.3 thành 4.3.1: Core Knowledge Graph (500 entities)
- Thêm Task 3.1.3: Entity Mapping System vào Giai Đoạn 3

---

*End of Plan*

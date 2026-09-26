# Deep Research Report: DILA Integration Architecture

## 📋 Executive Summary

Báo cáo này trình bày kiến trúc tích hợp dữ liệu từ Dharma Drum Institute of Liberal Arts (DILA) vào hệ thống "Hệ Thống Tra Cứu Dữ Liệu Đại Tạng Kinh Việt Nam" (Puzzle Ecosystem).

**Mục tiêu chính:**
- Tích hợp Multi-source RAG với dữ liệu chuẩn quốc tế
- Chuẩn hóa dữ liệu về RDF/TTL + GraphDB
- Hỗ trợ truy vấn Semantic (SPARQL + API)
- Hiển thị GIS Timeline đa lớp

**Ràng buộc kỹ thuật:**
- Zero-RAM Principle (không nạp toàn bộ 2.000 file vào RAM)
- Hybrid Storage (Raw → JSON Schema → TTL)
- Code Preservation (tích hợp liền mạch, không ghi đè)

---

## 1. Architecture Overview

### 1.1 System Type
```yaml
architecture:
  type: multi-agent-pipeline
  mode: hybrid (real-time + offline index)
```

### 1.2 Data Sources
| Nguồn | Loại | Mục đích |
|-------|------|----------|
| DILA_API | Web Service | Real-time biography data |
| DILA_RDF_Dump | XML/RDF | Offline entity matching |
| Local_Lineage_DB | TTL/JSON | Nội bộ dòng truyền thừa |
| Mapping_TTL | Turtle | owl:sameAs links |
| RAG_Documents | .docx | Nội dung Q&A |

### 1.3 Outputs
- RDF/TTL files với namespace `pth:` và `dila:`
- GraphDB triples (SPARQL ready)
- GIS visualization layers
- API responses

---

## 2. Core Agents Specification

### 2.1 Orchestrator Agent
```yaml
name: Orchestrator
role: central controller

input:
  - parsed_query
  - detected_entities

output:
  - execution_plan
  - routing decisions

logic:
  - detect intent:
      - factual → API
      - relational → GraphDB
      - semantic → RAG
  - parallel execution: supported
```

### 2.2 Semantic Parser Agent
```yaml
name: Semantic_Parser
input: natural_language_query (vi/en/zh)
output:
  - entities[]
  - intent
  - sparql_template
  - api_params
techniques:
  - NER (Named Entity Recognition)
  - intent classification
  - rule-based + LLM hybrid
```

### 2.3 DILA API Agent
```yaml
name: Web_Service_Integration
input:
  - entity_id (dila:A000004)
  - keyword

process:
  - HTTP call
  - retry: 3 times
  - timeout: 3s

parse fields:
  - persName
  - birth
  - death
  - floruit
  - dynasty (triều đại)
```

### 2.4 ETL Agent
```yaml
name: ETL_Processor
mode: batch/offline

input: XML / RDF dump (DILA Open Content)
output: TTL files

pipeline:
  1. extract → JSONL (streaming)
  2. transform → RDF triples
  3. load → GraphDB

rules:
  - preserve original IDs
  - normalize encoding (UTF-8)
```

### 2.5 GraphDB Agent
```yaml
name: Graph_Query_Agent
input: sparql_query
output: triples / json

features:
  - lineage traversal
  - temporal filtering
  - multi-hop query
```

### 2.6 RAG Agent
```yaml
name: RAG_Engine
input:
  - query
  - entity context
output: enriched answer

pipeline:
  - embedding search
  - reranking
  - context injection
```

### 2.7 Response Fusion Agent
```yaml
name: Fusion_Engine
input:
  - api_data (DILA)
  - graph_data (Lineage)
  - rag_data (Q&A)
output: unified_response

priority: DILA > GraphDB > RAG
rules:
  - deduplicate
  - resolve conflicts
```

### 2.8 Visualization Agent
```yaml
name: Visualization_Engine
input:
  - entity
  - location
  - time
output:
  - GIS layers
  - timeline data

features:
  - multi-entity rendering
  - animation timeline
```

### 2.9 Storage Optimizer Agent
```yaml
name: Storage_Optimizer
output:
  - .idx files (index)
  - trie index (lookup)

goal:
  - zero-RAM lookup
  - latency < 1ms
```

---

## 3. Data Contracts

### 3.1 Entity Schema (JSON)
```json
{
  "id": "dila:A000004",
  "label": "Khương Tăng Hội",
  "birth": 200,
  "death": 280,
  "lineage": [],
  "places": [],
  "sources": ["DILA"]
}
```

### 3.2 SPARQL Template
```sparql
SELECT ?person ?birth ?death
WHERE {
  ?person rdf:type :Monk .
  ?person :lineage :LamTe .
  ?person :birth ?birth .
}
```

### 3.3 TTL Mapping Example
```turtle
vn:KhuongTangHoi owl:sameAs dila:A000004 ;
  rdfs:label "Khương Tăng Hội" ;
  :birth 200 ;
  :death 280 .
```

---

## 4. Implementation Steps

### Bước 1: Tiếp nhận dữ liệu (Ingestion)
- Tải XML/RDF từ DILA Open Content
- Agent trích xuất: tên, năm sinh/mất, địa danh, dòng phái

### Bước 2: Phân tích cấu trúc (Structural Analysis)
- Tự động tạo liên kết thầy-trò (Relation extraction)
- Chuyển văn bản thô → Graph structure

### Bước 3: Hợp nhất & Làm sạch (Normalization)
- Đối soát DILA với dữ liệu nội bộ
- Ưu tiên nguồn chính xác hơn
- Đánh dấu cần kiểm tra thủ công

### Bước 4: Nạp GraphDB
- Nạp TTL vào GraphDB trên VPS
- SPARQL endpoint sẵn sàng

### Bước 5: Zero-RAM Index
- Tạo file .idx hoặc trie-based index
- Latency < 1ms, RAM usage < 5%

---

## 5. GIS Timeline Design

### 5.1 Chức năng chính
- **Time Slider**: Kéo thanh trượt để hiển thị thiền sư theo thời kỳ
- **Multi-entity**: Hiển thị đồng thời nhiều vị sư trong cùng giai đoạn
- **Lineage overlay**: Vẽ đường nối các ngôi chùa theo truyền thừa

### 5.2 Dữ liệu địa danh
- **Source**: Place Authority từ DILA
- **Fields**: GPS coordinates, tên chùa, địa chỉ, thời gian trụ trì

### 5.3 RDF Model cho GIS
```turtle
:HuệNăng :visited :PhápTánhTự , :BảoLâmTự ;
  :inYear 677 , 700 .
:PhápTánhTự a :Place ;
  :gps "23.456,113.789" ;
  :name "嵩山" .
```

---

## 6. Error Handling & Caching

### 6.1 Retry Policy
```yaml
max_attempts: 3
timeout: 3000ms
```

### 6.2 Fallback Chain
```
API fail → GraphDB
GraphDB fail → RAG
All fail → partial + warning
```

### 6.3 Cache Levels
| Level | Storage | TTL |
|-------|---------|-----|
| L1 | Memory (hot queries) | - |
| L2 | Disk (JSON cache) | 24h (API), 12h (SPARQL) |

### 6.4 Logging
- `error_log.json` - chi tiết lỗi
- `failed_entities.log` - danh sách thực thể lỗi

---

## 7. Performance Targets

| Metric | Target |
|--------|--------|
| API latency | < 300ms |
| Graph query | < 100ms |
| RAG response | < 500ms |
| RAM usage | < 5% |
| Concurrency | 100+ requests |

---

## 8. Security

- **Auth**: API key (DILA), internal token
- **Validation**: Query sanitization, SPARQL injection prevention

---

## 9. Roadmap

### Q2/2026
- [ ] Tải và xác thực 50,000+ thực thể từ DILA
- [ ] Hoàn thành mapping table 500+ nhân vật/địa danh Việt Nam

### Q3/2026
- [ ] Ánh xạ 2,000 file Q&A với entity tags
- [ ] Tích hợp RAG + GraphDB

### Q4/2026
- [ ] GIS Timeline beta
- [ ] Admin dashboard cho mapping

---

## 10. Compliance

Báo cáo này tuân thủ các nguyên tắc trong `AGENTS.md`:

- ✅ **Zero-RAM**: Sử dụng index-based search, streaming
- ✅ **Hybrid Storage**: Raw → JSON Schema → TTL
- ✅ **Entity Routing**: Áp dụng bộ lọc kép (Regex + Context)
- ✅ **Code Preservation**: Tích hợp liền mạch, không ghi đè
- ✅ **Namespace**: `pth:` (Pháp Thí Hội), `dila:` (DILA)

---

## 11. Prompt for Build Agent

> Thiết lập một quy trình Agents để xây dựng hệ thống RAG tích hợp dữ liệu GraphDB từ 3 nguồn (XML DILA, dữ liệu gia phả nội bộ, mapping file); yêu cầu Agents có khả năng chuyển đổi ngôn ngữ tự nhiên tiếng Việt sang truy vấn SPARQL, sau đó kết xuất dữ liệu này lên giao diện bản đồ GIS hỗ trợ Timeline động để hiển thị đồng thời nhiều thực thể thiền sư theo từng mốc lịch sử.

---

## 12. Key Principles

1. **Semantic-first**: Ưu tiên truy vấn ngữ nghĩa
2. **Non-destructive**: Không làm hỏng dữ liệu gốc
3. **Authority-based**: DILA là nguồn tham chiếu chuẩn
4. **Multi-source fusion**: Tổng hợp từ nhiều nguồn
5. **Scalable**: Mở rộng theo roadmap

---

*Report version: 2026-04-10*
*Compatible with: AGENTS.md (2026-04-09)*
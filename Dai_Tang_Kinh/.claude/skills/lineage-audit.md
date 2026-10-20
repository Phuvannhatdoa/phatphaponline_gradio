---
name: lineage-audit
description: Chạy Lineage Tester Agent để kiểm tra lỗi logic truyền thừa trong DB Buddhist
---

# Lineage Audit Skill

Chạy script `scripts/lineage_tester_agent.py` trực tiếp.

## Cách dùng

```
/lineage-audit
/lineage-audit Đan Hà Thiên Nhiên
/lineage-audit --check cycles
```

## Mapping lệnh

| Yêu cầu user | Lệnh chạy |
|---|---|
| `/lineage-audit` | `python scripts/lineage_tester_agent.py` |
| `/lineage-audit Tên Thiền Sư` | `python scripts/lineage_tester_agent.py --monk "Tên Thiền Sư"` |
| `/lineage-audit --check cycles` | `python scripts/lineage_tester_agent.py --check cycles` |

## Điều kiện chạy

Phải `cd` vào thư mục `daoanh/` trước, vì script dùng đường dẫn tương đối.

```bash
cd truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python scripts/lineage_tester_agent.py --monk "Đan Hà Thiên Nhiên"
```

Kết quả lưu ở `test-results/lineage_audit_*.json` và `*.md`.

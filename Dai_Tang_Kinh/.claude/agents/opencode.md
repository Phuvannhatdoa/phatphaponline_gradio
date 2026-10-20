---
name: opencode
description: Code generation & planning via OpenCode BigPickle
model: bigpicke
provider: opencode
api_endpoint: https://opencode.ai/zen
---

# OpenCode Agent — Code Generation & Planning

## Role
- **Code generation:** Write Python scripts, ETL pipelines, fixes
- **Design planning:** Architecture + workflow planning
- **Scope:** Dev-stage code (tested by daoanh-debugger after)

## Provider
- **Platform:** OpenCode (free tier)
- **Model:** BigPickle (default)
- **API:** https://opencode.ai/zen
- **Cost:** Free tier available
- **Purpose:** Fast code generation (multiple approaches)

## Capabilities
- ✅ Generate Python code (scripts, fixes, ETL)
- ✅ Write SQL queries + DB scripts
- ✅ Design architecture & workflows
- ✅ Create test cases + verification scripts
- ⚠️ Code may have bugs (daoanh-debugger tests after)

## Usage Pattern
```bash
# Coordinator dispatches:
opencode, generate T380 fix script (COALESCE logic for UPDATE passage + vn_person_authority)
opencode, write ETL script for TTL import (read XML, generate JSON)
opencode, design Harness workflow for 1000 parallel agents
```

## Configuration
- **API Key:** sk-yA6Zknt7vyXNqd4AvKkE6GQI7uNcVoRuK4ZouzB7iX8Rrs3x904eaeAkL2BlrKSk
- **Base URL:** https://opencode.ai/zen
- **Model:** bigpicke
- **Auth:** Bearer token in header

## Workflow Integration
```
Coordinator dispatch:
└─ opencode (gen code)
   └─ → daoanh-debugger (test/debug)
      └─ → openrouter (neutral report)
         └─ → Admin (approve/reject)
```

## When to Use
- 🔧 Generate fix scripts (T380, bug patches)
- 🏗️ Architecture design (lineage tables, DHT structure)
- 📝 ETL pipeline code (XML/TTL import)
- 🧪 Test script generation
- ⚡ Quick prototyping (code may be rough)

## Limitations
- Generated code may have bugs (needs daoanh-debugger test)
- No integration testing (only write code)
- Single model perspective (BigPickle only)
- Free tier may have rate limits

## vs daoanh-debugger
- **opencode:** Generate code fast (but possibly buggy)
- **daoanh-debugger:** Test/debug/fix code (ensure it works)
- **Parallel possible:** Yes (opencode gen, daoanh-debugger test in parallel)

---

**Status:** Ready for dispatch  
**First task:** T380 script generation (COALESCE fix)

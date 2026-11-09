# Investigation Report: @tester Agent Not Appearing in OpenCode Interface

## Executive Summary

The `@tester` agent does not appear when typing `@` in the OpenCode interface because the agent configuration file `tester.md` exists only in the **project-local** `.opencode\agents\` directory (`Dai_Tang_Kinh\daoanh\.opencode\agents\`), not in the **root** `.opencode\agents\` directory that the OpenCode interface reads from.

## 1. Directory Structure Analysis

### 1.1 Root `.opencode` Directory
```
Dai_Tang_Kinh\.opencode\
├── agents\
│   ├── codepreview.md  ✅ (visible when typing @)
│   └── qa.md           ✅ (visible when typing @)
├── package.json
├── skills/
└── ...
```

**Agents visible in root `.opencode\agents\`**: Only `codepreview` and `qa`

### 1.2 Daoanh Project `.opencode` Directory
```
Dai_Tang_Kinh\daoanh\.opencode\
├── agents\
│   ├── tester.md       ✅ (but NOT in root agents directory)
│   ├── daoanh-debugger.md
│   ├── daoanh-qa.md
│   ├── daoanh-task.md
│   ├── harness.md
│   ├── tich-hop.md
│   └── coordinator.md
├── opencode.json
├── package.json
├── plugins\
│   ├── tester-agent.js  ✅ (registers /test command)
│   └── agent-monitor.js
└── skills/
```

**Agents visible in daoanh `.opencode\agents\`**: Includes `tester`, but this directory is a nested subdirectory.

## 2. Key Files Found

### 2.1 `Dai_Tang_Kinh\daoanh\.opencode\agents\tester.md`
- **Status**: ✅ Exists
- **Content**: Defines `@tester Txxx` as direct OpenCode invocation command
- **Trigger Commands listed**:
  - `@tester Txxx` (OpenCode direct invocation)
  - `npm run qa:task -- Txxx` (npm wrapper)
  - `npm run tester:agent` (runs tester:agent from package.json)

### 2.2 `Dai_Tang_Kinh\daoanh\scripts\tester-agent.mjs`
- **Status**: ✅ Exists
- **Function**: Entry point for the @tester agent
- **Command**: `node scripts/tester-agent.mjs` or `npm run tester:agent`

### 2.3 `Dai_Tang_Kinh\daoanh\package.json`
- **Status**: ✅ Exists
- **Scripts defined**:
  - `"qa:task": "node scripts/tester-agent.mjs"`
  - `"tester:agent": "node scripts/tester-agent.mjs"`

### 2.4 `Dai_Tang_Kinh\daoanh\.opencode\plugins\tester-agent.js`
- **Status**: ✅ Exists
- **Function**: Registers `/test` command for OpenCode plugin API
- **Command**: `"test": { description: "Run tester agent: lint, test, e2e", handler: ... }`

### 2.5 Root `Dai_Tang_Kinh\.opencode\package.json`
- **Status**: ✅ Exists
- **Dependencies**: `"@opencode-ai/plugin": "1.14.46"`

### 2.6 Root `Dai_Tang_Kinh\.opencode\agents\` (missing tester.md)
- **Status**: ❌ `tester.md` NOT present
- **Contents**: Only `codepreview.md` and `qa.md`

## 3. Root Cause Analysis

### 3.1 Why `@tester` Doesn't Appear

The OpenCode interface discovers agents by reading markdown files from the `.opencode\agents\` directory. Based on the architecture:

- When OpenCode starts in the `Dai_Tang_Kinh` directory, it reads from `Dai_Tang_Kinh\.opencode\agents\`
- This directory only contains `codepreview.md` and `qa.md`
- The `tester.md` file is located in `Dai_Tang_Kinh\daoanh\.opencode\agents\`, which is a **subdirectory one level deeper**
- The OpenCode agent discovery system does not recursively scan nested `.opencode` directories by default

### 3.2 Configuration Gap

| Requirement | Status |
|------------|--------|
| `tester.md` in root `.opencode\agents\` | ❌ Missing |
| `tester.md` in daoanh `.opencode\agents\` | ✅ Present but nested |
| `/test` command via plugin | ✅ Registered in `tester-agent.js` |
| `npm run tester:agent` | ✅ Defined in `package.json` |
| `@tester Txxx` direct invocation | ✅ Defined in `tester.md` (daoanh version) |

## 4. How to Make `@tester` Appear

### Solution 1: Copy `tester.md` to Root Directory (Recommended)

Copy the `tester.md` file from `Dai_Tang_Kinh\daoanh\.opencode\agents\` to `Dai_Tang_Kinh\.opencode\agents\`. This will make `@tester` appear when typing `@` in the OpenCode interface.

```powershell
Copy-Item -Path "Dai_Tang_Kinh\daoanh\.opencode\agents\tester.md" -Destination "Dai_Tang_Kinh\.opencode\agents\tester.md"
```

After this, the OpenCode interface will detect `@tester` when typing `@`.

### Solution 2: Run OpenCode from Daoanh Directory

If the user runs OpenCode from within the `Dai_Tang_Kinh\daoanh` directory, the local `.opencode\agents\` will be read, and `@tester` will appear. However, this may not always be practical depending on the workflow.

### Solution 3: Use Alternative Commands

Even without `@tester` appearing in the agent list, the user can still use:

1. **`npm run tester:agent`** - Runs the full QA pipeline (lint + test + e2e)
2. **`npm run qa:task -- Txxx`** - Runs tester for specific task
3. **`/test`** in OpenCode - Thanks to the plugin `tester-agent.js` which registers this command

### Solution 4: Create Symlink

Create a symbolic link from the root agents directory to the daoanh version:

```powershell
mklink "Dai_Tang_Kinh\.opencode\agents\tester.md" "Dai_Tang_Kinh\daoanh\.opencode\agents\tester.md"
```

## 5. Verification Steps

After applying Solution 1, verify by:

1. Restart OpenCode/Claude interface
2. Type `@` and check if `@tester` appears in the agent list
3. Try `@tester T457` (or current task ID) to invoke the agent
4. Verify `npm run tester:agent` still works correctly

## 6. Additional Notes

### 6.1 Tester Agent Workflow (from AGENTS.md §11)

The tester agent is designed to run **before** requesting review from admin:

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
```

Or via OpenCode:
```
/test
```

The tester agent checks:
1. **Lint**: JavaScript syntax and style
2. **Test**: Unit/integration tests  
3. **E2E**: End-to-end tests (JS console errors in HTML pages)

### 6.2 Zero-RAM Principle Compliance

The tester agent scripts must comply with Zero-RAM Principle - never load all 2,000 scripture files into RAM. The current `tester-agent.mjs` is a placeholder that runs `npm run tester:agent`, which in turn runs `npm run lint`, `npm run test`, and `npm run e2e`.

### 6.3 Code Preservation

The tester agent is read-only - it validates but does not modify code, DB, or TTL files. This aligns with the Code Preservation principle.

## 7. Recommendation

**Immediate action**: Copy `tester.md` to the root `.opencode\agents\` directory so `@tester` appears when typing `@`.

**Long-term**: Ensure all project-level agent configurations have corresponding entries in the root `.opencode\agents\` directory, or document the alternative command paths (`npm run tester:agent`, `/test`) for teams that may not have the agent in the auto-complete list.

---

*Report generated by @codepreview Agent on 2026-10-24*
*In accordance with Master Guide (AGENTS.md) and Code Preservation principles*
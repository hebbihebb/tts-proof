# Phase 11 PR-2 Test Results

## Test Overview

**PR**: Phase 11 PR-2 - Report Display + Diff Viewer (MVP)  
**Branch**: `feat/phase11-pr2-report-diff`  
**Date**: 2025-01-XX  
**Tester**: Automated + Manual Smoke Testing

## Automated Tests

### Integration Tests (`testing/test_web_report.py`)

**Command**: `pytest testing/test_web_report.py -m "integration" -v`  
**Result**: ✅ **4/4 PASSED** (0.12s)

```
test_render_pretty_report        PASSED [ 25%]
test_unified_diff_generation     PASSED [ 50%]
test_diff_truncation             PASSED [ 75%]
test_artifact_files_exist        PASSED [100%]
```

**Coverage**:
- ✅ `render_pretty()` generates human-readable report from JSON
- ✅ `difflib.unified_diff()` generates unified diff
- ✅ Diff truncation to max_lines works correctly
- ✅ All artifact files created (input.txt, output.md, report.json, plan.json)

## Manual Smoke Testing

### Test Setup

**Test File**: `testing/test_data/detector_smoke_test.md`  
**Content**:
```markdown
# Smoke Test Input

Testing detector with real model.

The word F l a s h appeared in dialogue.

Someone said: "U-N-I-T-E-D we stand!"

Another stylized example: Bʏ Mʏ Rᴇsᴏʟᴠᴇ!
```

**Pipeline Steps**: `prepass-basic,prepass-advanced,detect,apply`  
**Model**: qwen2.5-1.5b-instruct (via http://192.168.8.104:1234/v1)

### Test 1: CLI Ground Truth

**Command**:
```bash
python -m mdp testing/test_data/detector_smoke_test.md \
  --steps prepass-basic,prepass-advanced,detect,apply \
  -o C:\Users\hebbi\AppData\Local\Temp\pr2-cli-out.md \
  --report C:\Users\hebbi\AppData\Local\Temp\pr2-cli-report.json \
  --report-pretty
```

**Result**: ✅ **SUCCESS**

**Output Hash** (SHA256): `C58D3C0BA019616D55B0784E169EB19A...`

**Report Summary**:
```
  Prepass Basic    : 1 normalizations
  Prepass Advanced : 0 normalizations
  Detector         : 4 suggestions (model: qwen2.5-1.5b-instruct)
  Apply            : 5 replacements in 1 nodes

Detector Rejections:
  no_match :    5
  schema   :    2

File Growth:
  Apply phase : +0.00% (+0 chars)
```

**Exit Code**: 0

### Test 2: Web UI Run

**Steps**:
1. ⏳ Navigate to http://localhost:5173
2. ⏳ Upload `detector_smoke_test.md`
3. ⏳ Configure steps: `prepass-basic,prepass-advanced,detect,apply`
4. ⏳ Configure endpoint: `http://192.168.8.104:1234/v1`
5. ⏳ Start pipeline processing
6. ⏳ Wait for completion
7. ⏳ Click "View Report" button
8. ⏳ Click "View Diff" button
9. ⏳ Download artifacts

**Expected**:
- Report numbers match CLI output
- Diff shows expected changes
- Output file hash matches CLI: `C58D3C0BA019616D55B0784E169EB19A...`
- Download buttons work for all artifacts

**Result**: 🔄 **PENDING** (requires manual UI interaction)

### Test 3: Rejected Case (Exit Code 3)

**Purpose**: Test that UI handles validation failures correctly

**Test File**: TBD - need file that triggers structural validation failure  
**Expected**: 
- Exit code: 3
- Rejected file generated
- Diff shows comparison against `output.rejected.md`
- UI indicates rejection state

**Result**: 🔄 **PENDING**

## Acceptance Criteria

Per PR-2 brief:

- [ ] **Report Display**: Report matches CLI `--report-pretty` numbers
- [ ] **Diff Viewer**: Shows unified diff (~200 lines max)
- [ ] **Artifact Downloads**: All artifact buttons work correctly
- [ ] **CLI Parity**: UI output byte-identical to CLI for same inputs
- [ ] **Rejection Handling**: Diffs against rejected file when validation fails
- [ ] **Single-Run Workflow**: Results section appears after processing completes

## Known Issues / Limitations

*None identified during automated testing. Manual UI testing pending.*

## Next Steps

1. Complete manual UI smoke testing
2. Verify hash matches between CLI and UI outputs
3. Test rejected case workflow
4. Update this document with results
5. Push branch and create PR if all tests pass

## Test Environment

- **OS**: Windows (PowerShell)
- **Python**: 3.13.4
- **Node.js**: v22.16.0
- **Backend**: FastAPI (localhost:8000)
- **Frontend**: Vite dev server (localhost:5173)
- **LLM Server**: LM Studio (192.168.8.104:1234/v1)
- **Model**: qwen2.5-1.5b-instruct

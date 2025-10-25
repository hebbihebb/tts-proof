# Stress Test Validation Branch - Setup Complete

## Branch Information
- **Name**: `feat/stress-test-validation`
- **Base**: `dev`
- **Purpose**: Comprehensive validation of TTS-Proof v2 pipeline components
- **Created**: October 24, 2025

## What Was Created

All files created in `testing/` directory (no root folder pollution):

### Test Scripts
1. **`testing/run_all_tests.py`** - Master orchestrator
   - Runs all test suites
   - Generates consolidated reports
   - Exit codes for CI/CD integration

2. **`testing/run_stress_test.py`** - Core pipeline stress test
   - Tests masking (Phase 1)
   - Tests prepass basic/advanced (Phases 2-3)
   - Tests all 7 structural validators
   - Tests full pipeline execution
   - Compares output with reference file
   - Optional LLM connectivity check

3. **`testing/run_gui_test.py`** - GUI functionality test
   - Validates GUI module import
   - Tests GUI initialization
   - Tests file loading with stress test data

4. **`testing/README_STRESS_TESTS.md`** - Documentation
   - Complete usage guide
   - Result interpretation
   - Troubleshooting tips

### Test Data (Already Existed)
- `testing/test_data/tts_stress_test.md` - Comprehensive problematic input
- `testing/test_data/tts_stress_test_reference.md` - Hand-crafted expected output

### Generated Reports
All saved to `testing/stress_test_results/`:
- `pipeline_output_TIMESTAMP.md` - Processed output
- `comparison_TIMESTAMP.md` - Diff vs reference
- `stress_test_summary_TIMESTAMP.md` - Comprehensive results
- `gui_test_report_TIMESTAMP.md` - GUI validation

## Current Test Results

### ✅ All Tests Passing (100%)

**Pipeline Tests:**
- ✅ Masking round-trip successful (1 mask created)
- ✅ Prepass basic (4 corrections applied)
- ✅ Prepass advanced (2 corrections applied)
- ✅ All 7 validators functioning correctly
- ✅ Full pipeline execution successful
- ⚠️ LLM connection not tested (LM Studio not running - expected)

**GUI Tests:**
- ✅ GUI module imports successfully
- ✅ GUI initialization works
- ✅ File loading with stress test data works

**Output Quality:**
- **Similarity to Reference**: 51.85%
  - This is **expected** for prepass-only testing
  - Full correction requires LLM-based detect/apply phases
  - Prepass only handles spacing, Unicode normalization, punctuation

## What's Being Tested

### Currently Enabled Phases (Working ✅)
1. **Masking** - Protects code blocks, links, images, math
2. **Prepass Basic** - Unicode normalization, spacing fixes
3. **Prepass Advanced** - Casing, punctuation, ellipsis
4. **Validators** - 7 structural integrity checks

### Not Yet Tested (Requires LLM)
5. **Scrubber** - Remove author notes (stub)
6. **Detect** - TTS problem detection via LLM
7. **Apply** - Execute correction plan with validation
8. **Fix** - Light polish with larger model (stub)

## How to Use

### Run All Tests
```bash
python testing/run_all_tests.py
```

### Run Individual Suites
```bash
# Core pipeline only
python testing/run_stress_test.py

# GUI only
python testing/run_gui_test.py
```

### Review Results
```bash
# Latest comparison report
ls -t testing/stress_test_results/comparison_*.md | head -1

# Latest summary
ls -t testing/stress_test_results/stress_test_summary_*.md | head -1
```

## Next Steps

### Immediate Testing Goals
1. ✅ Validate prepass phases work correctly
2. ✅ Confirm validators catch structural violations
3. ✅ Verify GUI compatibility
4. ⏭️ Test with LM Studio running (optional)
5. ⏭️ Test detect/apply phases when LLM available

### Troubleshooting Workflow
1. Make changes to `md_processor.py`
2. Run `python testing/run_all_tests.py`
3. Check exit code (0 = pass, 1 = fail)
4. Review reports in `testing/stress_test_results/`
5. Compare similarity scores across runs
6. Investigate any validator failures

### Success Criteria
- ✅ Masking round-trip must be perfect (100% match)
- ✅ Validators must catch all test violations
- ✅ Pipeline must complete without exceptions
- ✅ GUI must import and initialize
- 📊 Similarity should improve as phases are added
  - Prepass only: ~50-60% (current)
  - With detect/apply: ~85-95% (target)
  - With fix phase: ~95-100% (goal)

## File Organization

```
testing/
├── run_all_tests.py              # ← Master orchestrator (NEW)
├── run_stress_test.py            # ← Core pipeline test (NEW)
├── run_gui_test.py               # ← GUI test (NEW)
├── README_STRESS_TESTS.md        # ← Documentation (NEW)
├── test_data/
│   ├── tts_stress_test.md        # ← Input (existing)
│   └── tts_stress_test_reference.md  # ← Reference (existing)
└── stress_test_results/          # ← Generated reports
    ├── pipeline_output_*.md
    ├── comparison_*.md
    ├── stress_test_summary_*.md
    └── gui_test_report_*.md
```

**Root folder remains clean** - no new files created outside `testing/`

## Git Workflow

```bash
# Current state
git status
git diff

# Commit changes
git add testing/
git commit -m "Add comprehensive stress test suite for v2 validation"

# Push to remote
git push origin feat/stress-test-validation

# Create PR when ready
# Target: dev branch
# Title: "Add comprehensive stress test validation suite"
```

## Validation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Masking | ✅ Working | Perfect round-trip |
| Prepass Basic | ✅ Working | 4 corrections applied |
| Prepass Advanced | ✅ Working | 2 corrections applied |
| Validators | ✅ Working | All 7 catching violations |
| Pipeline | ✅ Working | Completes successfully |
| GUI | ✅ Working | Import, init, file loading |
| LLM Integration | ⏸️ Pending | Requires LM Studio |
| Detect Phase | ⏸️ Pending | Requires LLM |
| Apply Phase | ⏸️ Pending | Requires LLM |

---

**Status**: Ready for iterative testing and development  
**All Systems**: ✅ Operational  
**Test Coverage**: Core phases validated, LLM phases pending

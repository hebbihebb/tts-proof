# TTS-Proof Testing Suite

This directory contains all testing infrastructure for TTS-Proof v2.

## Stress Test Scripts (New)

### Quick Start

Run all stress tests with a single command:

```bash
python testing/run_all_tests.py
```

Or run individual test suites:

```bash
# Core pipeline stress test
python testing/run_stress_test.py

# GUI functionality test
python testing/run_gui_test.py
```

### What Gets Tested

#### 1. Core Pipeline Stress Test (`run_stress_test.py`)

Tests all currently enabled pipeline phases against `tts_stress_test.md`:

- ✅ **Phase 1: Masking** - Code blocks, links, images, math protection
- ✅ **Phase 2-3: Prepass** - Unicode normalization, spacing, punctuation
- ✅ **Phase 7: Validators** - All 7 structural integrity checks
- ✅ **Full Pipeline** - End-to-end processing with all enabled phases
- ⚠️ **LLM Connection** - Optional connectivity check (non-blocking)
- 📊 **Reference Comparison** - Diff against `tts_stress_test_reference.md`

**Outputs:**
- `stress_test_results/pipeline_output_TIMESTAMP.md` - Processed output
- `stress_test_results/comparison_TIMESTAMP.md` - Diff report with similarity score
- `stress_test_results/stress_test_summary_TIMESTAMP.md` - Comprehensive results

#### 2. GUI Functionality Test (`run_gui_test.py`)

Validates GUI components work correctly:

- ✅ GUI module import
- ✅ GUI initialization
- ✅ File loading with stress test data

**Outputs:**
- `stress_test_results/gui_test_report_TIMESTAMP.md` - GUI test results

### Test Data

| File | Description |
|------|-------------|
| `test_data/tts_stress_test.md` | Comprehensive problematic input (159 lines) |
| `test_data/tts_stress_test_reference.md` | Hand-crafted expected output (157 lines) |

The stress test file includes:
- Stylized Unicode & letter spacing
- Chat log formats
- Onomatopoeia & emphasis
- Nested parentheses
- Multi-unit data
- Code blocks
- Mixed dashes & ellipses
- Foreign language insertions
- Scene dividers
- Emotional fragmentation
- Numbers & percentages
- Measurement units
- URLs & markdown features

### Understanding Results

#### Similarity Score

The comparison report includes a similarity score (0-100%):

- **95-100%**: Excellent - Minor differences only
- **85-95%**: Good - Some expected variations
- **75-85%**: Fair - Review differences carefully
- **<75%**: Poor - Significant issues detected

#### Critical vs Non-Critical Tests

**Critical Tests** (must pass):
- Masking round-trip
- Prepass phases
- Full pipeline execution

**Non-Critical Tests** (can fail without blocking):
- LLM connection (requires LM Studio running)

### Continuous Testing Workflow

1. **Make changes** to `md_processor.py`
2. **Run stress tests**: `python testing/run_all_tests.py`
3. **Review reports** in `stress_test_results/`
4. **Compare similarity** - Should maintain or improve score
5. **Commit changes** if tests pass

### Directory Structure

```
testing/
├── run_all_tests.py          # Master test orchestrator
├── run_stress_test.py        # Core pipeline stress test
├── run_gui_test.py           # GUI functionality test
├── test_data/                # Input files and references
│   ├── tts_stress_test.md
│   ├── tts_stress_test_reference.md
│   └── ...other test files...
├── stress_test_results/      # Generated reports (gitignored)
│   ├── pipeline_output_*.md
│   ├── comparison_*.md
│   ├── stress_test_summary_*.md
│   └── gui_test_report_*.md
├── unit_tests/               # Pytest unit tests
└── ...legacy test folders...
```

### Integration with Pytest

The stress test scripts are standalone Python scripts (not pytest) for easier orchestration and reporting. They complement the existing pytest suite:

```bash
# Unit tests (fast, no LLM)
pytest

# Unit tests + LLM tests
pytest -m ""

# Stress tests (comprehensive integration)
python testing/run_all_tests.py
```

### Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'md_processor'`
- **Solution**: Run scripts from project root or use `sys.path` adjustment in scripts

**Problem**: "LLM not available" warning
- **Solution**: This is normal if LM Studio isn't running. It's non-blocking.

**Problem**: Low similarity score on reference comparison
- **Solution**: Review `comparison_*.md` diff report. Some differences may be expected if you're improving the pipeline.

**Problem**: GUI tests fail
- **Solution**: Check that `gui.py` exists and has no import errors

### Adding New Stress Tests

1. Create test script in `testing/` directory
2. Follow naming convention: `run_*_test.py`
3. Import from `md_processor` using `sys.path.insert(0, ...)`
4. Save outputs to `stress_test_results/` subdirectory
5. Add to `run_all_tests.py` orchestrator
6. Update this README

### Files to NOT Create

⚠️ **Do not create files in project root!** All test artifacts belong in:
- `testing/stress_test_results/` - Generated reports
- `testing/test_data/` - Input files
- `testing/` - Test scripts

The root folder should remain clean with only core implementation files.

---

**Branch**: `feat/stress-test-validation`  
**Purpose**: Comprehensive validation of TTS-Proof v2 pipeline  
**Status**: Ready for testing

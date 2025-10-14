# Phase 10 — Report Pretty-Print (CLI + Reusable Formatter)

**PR:** `feat/phase10-report-pretty` → `dev`

## 📋 Summary

Adds human-readable report formatting to the MDP CLI pipeline with the new `--report-pretty` flag. Provides compact, organized summaries of processing runs alongside existing JSON reports - perfect for quick debugging and pipeline monitoring.

## ✨ What's New

### New Module: `report/pretty.py`
- **`render_pretty(report: dict) -> str`** - Single entry point for formatting
- Consumes existing JSON report structure (no schema changes)
- Organized sections: Run Summary, Phase Statistics, Rejections, File Growth, Quality Flags, Artifacts
- Smart visibility: Sections only shown when relevant data exists
- Compact formatting: ~100 char width with intelligent path truncation
- Cross-platform compatible: ASCII arrows for Windows console support

### CLI Integration: `mdp/__main__.py`
- **New flag:** `--report-pretty` - Print human-readable summary after processing
- Works standalone or with `--report` flag for dual output (JSON + pretty)
- Compatible with all pipeline step combinations
- No breaking changes - fully optional enhancement

### Comprehensive Testing
- **25 new unit tests** in `testing/unit_tests/test_report_pretty.py`
- Test coverage:
  - Empty section hiding
  - Table alignment and formatting
  - Percentage formatting with signs (+/-%)
  - Path truncation for long filenames
  - Missing optional fields handling
  - Edge cases (zero values, negative growth, unicode paths)
  - Full pipeline integration
- **All 297 tests passing** (no regressions)

### Documentation & Samples
- **README update:** Comprehensive CLI documentation with examples
- **Sample output:** `docs/samples/report_pretty.txt` with multiple scenarios
- Usage examples for different pipeline combinations
- Feature breakdown with visual format examples

## 📊 Example Output

```
====================================================================
                          RUN SUMMARY                              
====================================================================
  Input file     : testing/test_data/test_input.md
  Output file    : output.md
  Pipeline steps : mask -> prepass-basic -> prepass-advanced

====================================================================
                        PHASE STATISTICS                           
====================================================================
  Mask             : 2 regions masked
  Prepass Basic    : 3 normalizations
  Prepass Advanced : 11 normalizations
```

**With Full Pipeline (Detector + Apply + Fixer):**
```
====================================================================
                        PHASE STATISTICS                           
====================================================================
  Detector : 20 suggestions (model: qwen2.5-1.5b)
  Apply    : 18 replacements in 12 nodes
  Fixer    : 100/105 spans (model: qwen2.5-1.5b-instruct)

====================================================================
                           REJECTIONS                              
====================================================================
Detector Rejections:
  schema_invalid :    5

Fixer Rejections:
  timeout        :    5

====================================================================
                          FILE GROWTH                              
====================================================================
  Apply phase : +1.50% (+30 chars)
  Fixer phase : +2.00%
```

## 🎯 Usage Examples

```bash
# Pretty report only (printed to stdout)
python -m mdp input.md --steps mask,detect,apply --report-pretty

# JSON + pretty report (both outputs)
python -m mdp input.md --steps mask,detect,apply --report report.json --report-pretty

# Works with any step combination
python -m mdp input.md --steps mask,prepass-basic --report-pretty
python -m mdp input.md --steps mask,detect,apply,fix --report-pretty
```

## 🔍 Technical Details

### Report Structure (Consumes Existing JSON)
```python
{
    'input_file': str,
    'output_file': str | None,
    'steps': List[str],
    'statistics': {
        'mask': {'masks_created': int},
        'prepass-basic': {...},
        'detect': {'suggestions_valid': int, 'model': str, 'rejections': {...}},
        'apply': {'replacements_applied': int, 'nodes_changed': int, 'growth_ratio': float},
        'fix': {'spans_fixed': int, 'spans_total': int, 'file_growth_ratio': float, ...}
    }
}
```

### Key Features
- **No schema changes** - Uses existing report structure from Phases 1-8
- **Reusable formatter** - Can be called from Web UI later (Plan A alignment)
- **Defensive coding** - Handles missing fields gracefully
- **Smart aggregation** - Combines multi-field stats (e.g., prepass normalizations)
- **Growth tracking** - Shows file size changes with percentages and character deltas
- **Rejection analysis** - Per-phase rejection counts sorted by frequency

### Path Truncation Algorithm
```python
def _truncate_path(path: str, max_len: int = 60) -> str:
    # Keeps filename visible, truncates parent dirs
    # Example: "/very/long/path/to/file.md" -> "...to/file.md"
```

## ✅ Acceptance Checklist

- [x] `--report-pretty` prints compact summary using `report/pretty.py`
- [x] Works for partial pipelines (mask only) and full runs (mask→detect→apply→fix)
- [x] No change to JSON schema; pretty output is optional
- [x] 25 new tests pass; all 297 tests passing
- [x] Sample output included in `docs/samples/report_pretty.txt`
- [x] README documentation updated with usage examples
- [x] Branch `feat/phase10-report-pretty` → PR into `dev` (not main)

## 📦 Files Changed

- **New:** `report/__init__.py` - Package initialization
- **New:** `report/pretty.py` - Pretty-print formatter (285 lines)
- **New:** `testing/unit_tests/test_report_pretty.py` - 25 unit tests (464 lines)
- **New:** `docs/samples/report_pretty.txt` - Sample outputs
- **Modified:** `mdp/__main__.py` - Added `--report-pretty` flag (10 lines changed)
- **Modified:** `readme.md` - CLI documentation section (100+ lines added)

**Total:** 885 insertions, 2 deletions

## 🚀 Next Steps (Post-Merge)

After Phase 10 merges into `dev`:
1. **Phase 11:** Web UI MVP (Plan A priority)
   - Expose step toggles (mask, prepass, detect, apply, fix)
   - Model picker from `config.py`
   - Stream logs via WebSocket
   - Display pretty report in UI
   - Show diffs (apply step)
2. **Phase 12:** Presets (informed by UI usage patterns)
3. **Phase 13+:** Remaining polish and optimizations

## 📝 Testing

```bash
# Run new tests only
pytest testing/unit_tests/test_report_pretty.py -v

# Run all fast tests (includes new tests)
pytest -v

# Test CLI integration
python -m mdp testing/test_data/test_input.md --steps mask --report-pretty
python -m mdp testing/test_data/test_input.md --steps mask,detect,apply --report report.json --report-pretty
```

## 🎨 Design Decisions

1. **ASCII arrows (`->`) instead of Unicode** - Windows console compatibility
2. **~100 char width** - Readable on standard terminals without wrapping
3. **Section visibility** - Empty sections automatically hidden (no clutter)
4. **Percentage signs** - Always show +/- for clarity
5. **Rejection sorting** - Highest counts first for quick debugging
6. **Path truncation** - Keep filename visible, truncate parent directories

## 🔗 Alignment with Plan A

✅ **Phase order maintained:**
- Phases 1–8: Merged ✅
- Phase 9: Already implemented ✅
- Phase 10: Report pretty-print ← **This PR**
- Phase 11: Web UI MVP ← **Next**
- Phase 12: Presets (after UI)

✅ **Reusable design:**
- `render_pretty()` can be imported by Web UI
- Same report structure between CLI and UI
- Consistent formatting for both interfaces

## 📚 Related Documentation

- `docs/samples/report_pretty.txt` - Example outputs
- `testing/unit_tests/test_report_pretty.py` - Test suite
- `readme.md` - Updated CLI section with full documentation
- `PHASES_PLANNED.md` - Phase roadmap alignment

---

**Ready for review and merge into `dev`** 🚀

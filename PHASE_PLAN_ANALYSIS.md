# Phase Plan Analysis & Recommendations

## 📊 Current Status vs Planned Phases

### ✅ Already Complete
- **Phase 0**: Project hygiene ✅ (dev branch, testing infrastructure, config)
- **Phase 1**: Markdown AST & Masking ✅ (`mdp/markdown_adapter.py` + `mdp/masking.py`)
- **Phase 2**: Unicode & Spacing Normalization ✅ (`mdp/prepass_basic.py`)
- **Phase 3**: Notes Scrubber ✅ (`mdp/scrubber.py` + `mdp/appendix.py`)
- **Phase 4**: Casing, Punctuation, Numbers ✅ (`mdp/prepass_advanced.py`)
- **Phase 5**: Grammar Assist ✅ (`mdp/grammar_assist.py`)
- **Phase 6**: Detector ✅ (`detector/` - tiny model → JSON plans)
- **Phase 7**: Plan Applier & Validator ✅ (`apply/` - 7 structural validators)

**Test Coverage**: 217 tests passing across all 7 completed phases

### 🎯 Remaining Phases
- **Phase 8**: Fixer (Bigger Model → Light Polish) ← **NEXT**
- **Phase 9**: Reassembly, Unmasking & Final Sanity
- **Phase 10**: Reporting & Scoring
- **Phase 11**: Presets & Performance
- **Phase 12**: (Optional) Tie-Breaker Classifier for Scrubber
- **Phase 13**: Packaging, Docs & Demos
- **Phase 14**: Web UI Integration ← **Final step before deployment**

---

## 🔍 Analysis of Phase 8 (Fixer) Plan

### ✅ Strengths of Current Plan
1. **Excellent safety guardrails**: Length limits, forbidden tokens, structural validation
2. **Clear scope**: Text nodes only, never sees Markdown
3. **Conservative approach**: Fail-safe to original text on any rejection
4. **Good integration**: Fits naturally after Phase 6 & 7 (detect→apply→fix)
5. **Comprehensive testing**: Unit, integration, golden, validator tests all specified

### ⚠️ Potential Issues & Adjustments

#### 1. **Module Organization Inconsistency**
**Issue**: Phase 8 plan shows `fixer/` directory, but existing codebase uses:
- `detector/` for Phase 6
- `apply/` for Phase 7

**Recommendation**: Create `fixer/` as planned - maintains clean separation. However, consider:
```
fixer/
  __init__.py
  client.py      # LM Studio client (similar to detector/client.py)
  prompt.py      # Prompt management
  fixer.py       # Main orchestration
  guards.py      # Post-checks and safety validators
```

This matches the existing pattern and makes the codebase more navigable.

---

#### 2. **CLI Wiring - Path Resolution**
**Issue**: Plan mentions wiring in `cli.py`, but current codebase uses `mdp/__main__.py` for CLI.

**Recommendation**: 
- Add fixer step to `mdp/__main__.py` (existing CLI entry point)
- Keep naming consistent: use `--steps fix` as planned
- Ensure it integrates with existing `run_pipeline()` function

**Code location**: `mdp/__main__.py` lines ~100-200 (where detect/apply steps are handled)

---

#### 3. **Exit Code Conflict**
**Issue**: Plan specifies exit code `6` for "fixer engine unreachable", but existing system uses:
- `0`: Success
- `2`: Detector model server unreachable ← **Conflict!**
- `3`: Validation failure
- `4`: Plan parse error
- `5`: Masked region edit

**Recommendation**: Use exit code `2` for fixer unreachable (same as detector) since they're both "model server unreachable" scenarios. Update plan to reflect this consistency.

---

#### 4. **Phase 9 Redundancy**
**Issue**: Phase 9 "Reassembly, Unmasking & Final Sanity" is **already implemented**:
- Unmasking: `mdp/markdown_adapter.py` - `unmask()`
- Final sanity: Phase 7 `apply/validate.py` - 7 structural validators
- Rejection handling: Already writes `.rejected.md` files

**Recommendation**: 
- **Phase 9 can be marked as complete** or merged into Phase 8
- Phase 8 just needs to call existing unmasking and validation infrastructure
- No new modules needed for Phase 9

---

#### 5. **Phase 10 Reporting - Partial Implementation**
**Issue**: Reporting is **partially complete**:
- Each phase already returns stats dict (see Phase 6 & 7 implementation)
- `mdp/__main__.py` aggregates stats into `combined_stats`
- `--report` flag exists but only outputs JSON

**What's Missing**:
- Human-readable table format
- Per-node diff visualization (current `--diff` only shows file-level)
- Bucketed fix counters across all phases

**Recommendation**: 
- Phase 10 should be a **lightweight enhancement** (2-3 hours)
- Add `report/formatter.py` for pretty-printing existing stats
- Extend `--report` to support formats: `json`, `table`, `markdown`

---

#### 6. **Phase 11 Presets - Good Timing**
**Issue**: None! This is well-positioned after Phase 8.

**Recommendation**: Keep Phase 11 as planned, but consider:
- Reuse existing `mdp/config.py` infrastructure (YAML-based)
- Add preset files to `config/` directory (existing location)
- Examples: `config/fiction_epub.yaml`, `config/technical_docs.yaml`, `config/fast_pass.yaml`

**Integration with Web UI**: Presets can be dropdown selections in the UI - easy UX win!

---

#### 7. **Web UI Integration Timing - CRITICAL**
**Current Plan**: Wait until Phase 13 (packaging) before updating Web UI

**Issue**: This creates **technical debt accumulation**:
- Web UI still uses legacy `md_proof.py` + `prepass.py`
- By Phase 13, you'll have 8+ phases in CLI but 0 in Web UI
- Larger gap = more painful migration

**Recommendation**: Add **Phase 14: Web UI Integration** and do it **BEFORE** Phase 11-13:

```
Phase 8:  Fixer ✓
Phase 9:  (Already complete - mark as such) ✓
Phase 10: Enhanced Reporting ✓
Phase 14: Web UI Integration ← Do this next!
Phase 11: Presets & Performance
Phase 12: (Optional) Tie-Breaker Classifier
Phase 13: Packaging, Docs & Demos
```

**Why this order is better**:
1. ✅ Core functionality (Phases 1-8) complete - solid foundation
2. ✅ Web UI gets Phases 1-8 immediately - users can test and provide feedback
3. ✅ Presets (Phase 11) can be designed **with Web UI in mind** (dropdowns, toggles)
4. ✅ Packaging (Phase 13) ships a **unified product** (CLI + Web UI both up-to-date)
5. ✅ Easier debugging with users testing incrementally vs. big-bang at the end

---

## 🎯 Recommended Phase Order (Revised)

### Immediate (This Week)
1. **Phase 8: Fixer** (4-6 hours)
   - Implement as planned with adjustments above
   - Use exit code 2 (not 6) for consistency
   - Leverage existing validation infrastructure

### Short-term (Next Week)
2. **Phase 9: Mark as Complete** (0 hours)
   - Document that reassembly/unmasking/validation already exists
   - Update PHASES_PLANNED.md to reflect this

3. **Phase 10: Enhanced Reporting** (2-3 hours)
   - Add human-readable formatters
   - Extend `--report` with multiple output formats
   - Add per-phase summary tables

### Critical Path (Week 3)
4. **Phase 14: Web UI Integration** (6-8 hours) ← **DO THIS BEFORE PHASE 11**
   - Migrate backend from `md_proof.py` to `python -m mdp`
   - Add step selection UI (checkboxes for Phases 1-8)
   - Real-time progress for each phase
   - Configuration panels for each phase
   - Preview of reports in UI

**Why now**: 
- Core pipeline is stable and tested (217 tests)
- Users can start testing real workflows
- Feedback informs Phase 11 preset design
- Avoids massive migration debt later

### Polish & Performance (Week 4+)
5. **Phase 11: Presets & Performance**
   - Design presets with Web UI dropdowns in mind
   - Concurrency tuning for batch processing
   - VRAM management

6. **Phase 12: (Optional) Tie-Breaker Classifier**
   - Only if scrubber false positives are problematic
   - May not be needed - current heuristics are quite good

7. **Phase 13: Packaging, Docs & Demos**
   - Polish both CLI and Web UI documentation
   - Single launch script that works everywhere
   - Video demos showing Web UI workflow

---

## 🔧 Specific Adjustments to Phase 8 Plan

### Config Path
**Change**: `md_proof.yaml` → **Use existing `mdp/config.py` system**

The codebase already has a comprehensive config system in `mdp/config.py`. Don't create a separate `md_proof.yaml` - extend the existing system:

```python
# mdp/config.py (extend existing)
DEFAULT_CONFIG = {
    # ... existing phases ...
    'fixer': {
        'enabled': True,
        'model': 'qwen2.5-1.5b-instruct',
        'api_base': 'http://127.0.0.1:1234/v1',
        'max_context_tokens': 1024,
        'max_output_tokens': 256,
        'timeout_s': 10,
        'retries': 1,
        'temperature': 0.2,
        'top_p': 0.9,
        'node_max_growth_ratio': 0.20,
        'file_max_growth_ratio': 0.05,
        'forbid_markdown_tokens': True,
        'locale': 'en',
        'batch_size': 1,
        'seed': 7
    }
}
```

### CLI Integration Path
**Change**: `cli.py` → **`mdp/__main__.py`**

Add fixer step to existing `run_pipeline()` function:

```python
# mdp/__main__.py (around line 150-180)
elif step == 'fix':
    from fixer.fixer import apply_fixer
    from apply.validate import validate_all
    
    fixer_config = config.get('fixer', {})
    
    try:
        fixed_text, fixer_stats = apply_fixer(
            text=text,
            text_nodes=text_nodes,  # From Phase 1
            mask_table=mask_table,
            config=fixer_config
        )
        
        # Validate after fixing
        is_valid, errors = validate_all(fixed_text, text, mask_table)
        if not is_valid:
            # ... rejection handling ...
        
        text = fixed_text
        combined_stats['fix'] = fixer_stats
        
    except ConnectionError:
        logger.error("Fixer model server unreachable")
        sys.exit(2)  # Not 6 - keep consistent
```

### Test Organization
**Add**: Follow existing test structure in `testing/unit_tests/`

```
testing/unit_tests/
  test_fixer_client.py    # Client, timeout, retry tests
  test_fixer_guards.py    # Length limits, forbidden tokens
  test_fixer_logic.py     # Span splitting, reassembly
  test_fixer_integration.py  # End-to-end with sample files
```

This matches the existing pattern:
- `test_apply_*.py` (Phase 7)
- `test_prepass_*.py` (Phases 2 & 4)
- `test_scrubber.py` (Phase 3)

---

## 📋 Web UI Integration Strategy (Phase 14)

### Backend Changes Needed

**1. Update `backend/app.py` to use `mdp` pipeline**:

```python
# backend/app.py
import subprocess
import json

@app.post("/api/process/{client_id}")
async def process_file(client_id: str, request: ProcessRequest):
    # Build mdp command
    cmd = [
        "python", "-m", "mdp",
        input_path,
        "--steps", ",".join(request.steps),  # e.g., "mask,prepass-basic,detect,apply,fix"
        "--out", output_path,
        "--report", report_path,
        "--config", config_path  # User's custom config
    ]
    
    # Run as subprocess and stream progress via WebSocket
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Parse stdout for progress (mdp already emits INFO logs)
    for line in process.stdout:
        if "INFO:" in line:
            await manager.send_message(client_id, {
                "type": "progress",
                "message": line.decode()
            })
```

**2. Add phase configuration endpoints**:

```python
@app.get("/api/config/phases")
async def get_phase_config():
    """Return available phases and their default configs"""
    return {
        "phases": [
            {"id": "mask", "name": "Markdown Masking", "required": True},
            {"id": "prepass-basic", "name": "Unicode Normalization", ...},
            # ... etc for all phases
        ]
    }

@app.post("/api/config/save")
async def save_user_config(config: dict):
    """Save user's custom phase configuration"""
    # Write to temporary YAML file for this session
```

### Frontend Changes Needed

**1. New Component: `PhaseSelector.tsx`**
```tsx
// Checkboxes for each phase
// Show/hide config panels per phase
// Dependency validation (e.g., apply requires detect)
```

**2. New Component: `PhaseConfig.tsx`**
```tsx
// Phase-specific configuration panels
// E.g., Fixer config: model, temperature, length limits
```

**3. Update `ProcessingView.tsx`**
```tsx
// Show progress per phase (not just overall %)
// Phase 1: Complete ✓
// Phase 2: Processing... 45%
// Phase 3: Pending...
```

**4. Update `ResultsPanel.tsx`**
```tsx
// Show per-phase statistics
// Expandable sections for each phase's report
```

### Estimated Effort: 6-8 hours
- Backend migration: 3-4 hours
- Frontend components: 3-4 hours
- Testing & polish: 1 hour

---

## 💡 Key Recommendations Summary

### Critical Changes to Make Now:

1. ✅ **Phase 8 Exit Code**: Use `2` (not `6`) for model unreachable - matches Phase 6
2. ✅ **Phase 8 Config**: Extend `mdp/config.py` (don't create separate `md_proof.yaml`)
3. ✅ **Phase 8 CLI**: Wire into `mdp/__main__.py` (not `cli.py`)
4. ✅ **Phase 9**: Mark as "Already Complete" - no new work needed
5. ✅ **Phase 10**: Scope as "lightweight enhancement" (2-3 hours, not full phase)
6. ✅ **Phase Order**: Do Web UI (Phase 14) **BEFORE** Presets (Phase 11)

### Benefits of This Approach:

1. **Consistency**: All phases use same config system, CLI entry point, exit codes
2. **Less Duplication**: Leverage existing validation, masking, reporting infrastructure
3. **Incremental Value**: Users get Web UI access to Phases 1-8 immediately
4. **Better Design**: Presets informed by real Web UI usage patterns
5. **Unified Product**: CLI and Web UI stay in sync throughout development

---

## 🎯 Next Actions

**Immediate** (before starting Phase 8):
1. Update Phase 8 plan document with corrected paths and exit codes
2. Verify existing Phase 9 infrastructure (should take ~15 minutes)
3. Decide on Phase order: Web UI before or after Presets?

**Starting Phase 8**:
1. Create `fixer/` module structure
2. Follow existing patterns from `detector/` and `apply/`
3. Integrate with `mdp/__main__.py` pipeline
4. Use existing config, validation, and reporting systems

**After Phase 8**:
- If you choose early Web UI integration → Phase 14 next (recommended)
- If you prefer to complete all CLI features first → Phase 10, 11, then 14

Either way works, but **early Web UI integration reduces technical debt and enables user feedback sooner**.

---

## 📝 Files to Update

**PHASES_PLANNED.md**:
- Update Phase 8 with corrected paths and exit codes
- Mark Phase 9 as "Already Complete (integrated in Phases 1-7)"
- Adjust Phase 10 scope to "enhancement" not full phase
- Add Phase 14 (Web UI Integration) before Phase 11

**README.md**:
- Add Phase 4 to completed list (it's missing currently!)
- Keep Phase 8 description minimal until it's complete

**ROADMAP.md** (optional):
- Update to reflect Phase 6 & 7 completion
- Mark Phase 8 as "In Progress"

Let me know if you want me to make these adjustments to the plan documents!

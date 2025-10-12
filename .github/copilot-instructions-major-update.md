# Copilot Instructions Major Update - October 12, 2025

**Status**: ✅ **Complete** - Comprehensive update with MDP Package Integration  
**Changes**: Added ~150 lines documenting Phase 1-3 architecture, pytest infrastructure, and configuration system

---

## 🎯 Update Overview

The `.github/copilot-instructions.md` has been significantly enhanced to document the **modular MDP processing pipeline (Phase 1-3)** and **fast pytest-based testing infrastructure** while preserving all existing content.

---

## 📋 Major New Sections Added

### 1. **MDP Package Documentation** (Added to Key Components)

```markdown
- **MDP Package** (`mdp/`): Modular text processing pipeline (Phase 1-3 implementation)
  - **`markdown_adapter.py`**: AST-based masking via regex fallback
  - **`masking.py`**: Sentinel-based content masking
  - **`prepass_basic.py`**: Unicode normalization, spaced letter joining, hyphenation healing
  - **`prepass_advanced.py`**: Casing normalization, punctuation collapse
  - **`scrubber.py`**: Block detection and removal (author notes, navigation, link farms)
  - **`appendix.py`**: Formats scrubbed blocks into organized appendix
  - **`config.py`**: YAML-based configuration with comprehensive defaults
```

### 2. **Three-Phase Processing Pipeline** (Expanded Section 2)

**Before**: Simple URL masking pattern (5 lines)  
**After**: Complete three-phase architecture (45+ lines)

- **Phase 1**: Markdown masking with `mask_protected()` / `unmask()`
- **Phase 2**: Deterministic unicode/spacing normalization (<0.1s, no LLM)
- **Phase 3**: Content scrubbing with appendix generation
- **Legacy pattern**: URL masking still used by main engine

### 3. **Pytest Testing Infrastructure** (Replaced Testing section)

**Before**: Basic test file list (6 lines)  
**After**: Complete pytest workflow documentation (40+ lines)

```bash
pytest                    # 33 tests in <1s (default)
pytest -m ""              # All tests including slow/LLM
pytest -m "llm"           # Only LLM tests
```

**Added**:
- Test markers (`@pytest.mark.llm`, `@pytest.mark.slow`, `@pytest.mark.network`)
- VS Code tasks integration (8 pre-configured tasks)
- Test structure explanation (`unit_tests/`, `stress_tests/`, `test_data/`)
- Development workflow guidance (use `pytest` alone during development)

### 4. **Configuration System** (New Section 6)

```python
from mdp.config import load_config
config = load_config("custom_config.yaml")  # or None for defaults
```

**Documented**:
- YAML-based configuration approach
- Key config sections (unicode, scrubber, prepass_advanced)
- Whitelist support for protected content
- Acronym detection (NASA, GPU, JSON, HTML, TTS, etc.)
- Sensible defaults philosophy (config file optional)

### 5. **Directory Organization** (Enhanced Section 5)

Added reference to `DIRECTORY_STRUCTURE.md`:
- `/testing/` - All tests
- `/docs/` - Analysis reports
- `/config/` - LM Studio presets
- `/prompts/` - Versioned prompts
- `/mdp/` - Processing pipeline

### 6. **Enhanced Gotchas** (Added 2 new + updated 1)

- **New #8**: Test markers - use `pytest` alone for fast feedback
- **New #9**: Module imports - `pytest.ini` sets `pythonpath = .`
- **Updated #4**: Prefer Phase 1 masking for new features

---

## ✅ Preserved Content

**100% of existing content retained**:

- LM Studio integration patterns (sentinel-based prompting)
- WebSocket communication (ConnectionManager, message types)
- TTS prepass detection (JSON format, job tracking)
- File handling conventions (checkpointing, .partial files)
- Frontend/Backend architecture
- Advanced Testing & Optimization Framework (15.0% improvement)
- Network testing patterns
- 30+ TTS problem categories
- All original 7 gotchas

---

## 🔍 Questions for Feedback

1. **MDP Integration Roadmap**: Should we document the migration path from legacy patterns to MDP patterns?

2. **Configuration Examples**: Add real-world config examples (technical docs vs fiction vs translations)?

3. **CLI Usage Expansion**: Document CLI usage for `python -m mdp.prepass_basic`, `python -m mdp.scrubber`?

4. **Developer Workflow**: Add "Day in the Life" section showing typical development patterns?

5. **API Reference Table**: Quick-reference table for key functions with signatures?

6. **Error Handling Patterns**: Document common error scenarios and recovery?

7. **Performance Tuning**: Add performance optimization section?

---

## 📊 Statistics

- **Lines added**: ~150 lines
- **New sections**: 1 (Configuration System)
- **Expanded sections**: 3 (Key Components, Text Processing, Testing)
- **New code examples**: 8 practical usage patterns
- **New gotchas**: 2
- **Updated gotchas**: 1
- **Preserved**: 100% of original content

---

## 🚀 Next Steps

1. **Review** - Read updated `.github/copilot-instructions.md`
2. **Test** - Can AI agents be immediately productive?
3. **Feedback** - Answer questions above or identify gaps
4. **Iterate** - Update based on real-world usage

---

## 📝 Design Philosophy Maintained

✅ **Concise and actionable** - Focused, scannable structure  
✅ **No generic advice** - Project-specific patterns only  
✅ **Example-driven** - Real code from codebase  
✅ **Discovery-focused** - Non-obvious patterns documented  
✅ **Integration-aware** - Cross-component communication explained

**Target**: Help AI coding agents understand the "why" behind architectural decisions, not just the "what" of the codebase structure.

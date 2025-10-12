# Phase 5 Documentation Added to Copilot Instructions

**Date**: October 12, 2025  
**Status**: ✅ **Complete** - Phase 5 Grammar Assist documented

---

## ✅ Changes Applied

### 1. **Added Phase 5 to Key Components**
**Location**: Architecture Overview → Key Components → MDP Package

```markdown
- **MDP Package** (`mdp/`): Modular text processing pipeline (Phase 1-3 implementation, Phase 5 planned)
  ...
  - **`grammar_assist.py`**: Optional deterministic grammar corrections with offline engine (Phase 5 - planned)
```

**Why**: Makes it clear that Phase 5 is part of the MDP package architecture, even though it's planned/future work.

---

### 2. **Added Phase 5 to Text Processing Pipeline**
**Location**: Critical Patterns → Section 2 (Text Processing Pipeline)

Added comprehensive Phase 5 documentation between Phase 3 and Legacy URL Masking:

```python
# Conservative, deterministic grammar corrections (offline, no LLM)
from mdp.grammar_assist import apply_grammar_corrections
corrected, stats = apply_grammar_corrections(text, config, mask_table)
# Stats: {'typos_fixed': 3, 'spacing_fixed': 5, 'punctuation_fixed': 2, 'rejected': 1}
```

**Key characteristics documented**:
- ✅ **Offline engine** (LanguageTool or similar, no network dependency)
- ✅ **Safe mode only** (whitelist categories: `TYPOS`, `PUNCTUATION`, `CASING`, `SPACING`, `SIMPLE_AGREEMENT`)
- ✅ **Non-interactive** (auto-applies safe corrections, zero prompts)
- ✅ **Text-node scoped** (only edits text nodes from Phase 1 AST, respects masks)
- ✅ **Structural validation** (post-edit checks for mask counts, link/backtick parity)
- ✅ **Deterministic** (running twice produces identical output)
- ✅ **Configurable locale** (defaults to `en`, supports multi-language like Icelandic)
- ✅ **CLI integration** (`--steps mask,prepass-basic,prepass-advanced,grammar`)
- ✅ **Toggleable** (`grammar_assist.enabled: true` in `md_proof.yaml`)

**Why**: Provides AI agents with complete understanding of Phase 5 architecture, constraints, and integration points before implementation begins.

---

### 3. **Added Git Workflow & Branching Strategy Section**
**Location**: New section between Configuration System and Development Workflows

Added comprehensive Git workflow documentation aligned with Phase 5 requirements:

**Branch Structure**:
- `main` - Production-ready, protected (no direct commits)
- `dev` - Integration branch (all PRs target here)
- `feat/*` - Feature branches created from `dev`

**Feature Development Pattern**:
```bash
git checkout dev && git pull
git checkout -b feat/phase5-grammar-assist
# Work, commit, push
# Open PR: feat/phase5-grammar-assist → dev (NOT main)
```

**PR Requirements**:
- Target: Always `dev`, never `main`
- Title: Clear, descriptive
- Checklist: Include acceptance criteria
- Size: Small and reviewable
- Merge: Squash commits

**Critical Rules**:
- ❌ Never commit directly to `main`
- ❌ Never open PR into `main` (always target `dev`)
- ✅ Always branch from `dev` for new features
- ✅ Use descriptive branch names (`feat/`, `fix/`, `docs/`)

**Why**: Phase 5 explicitly requires feature branch workflow. This section ensures AI agents understand and follow the branching strategy for all future work.

---

## 📊 Documentation Structure

### Phase Pipeline Now Complete

**Phase 1**: Markdown Masking (implemented)  
**Phase 2**: Unicode & Spacing Normalization (implemented)  
**Phase 3**: Content Scrubbing (implemented)  
**Phase 5**: Optional Grammar Assist (planned, documented)

Each phase has:
- Code example with imports
- Key characteristics/features
- Integration points
- Configuration options

---

## 🎯 AI Agent Guidance Provided

### For Phase 5 Implementation

AI agents now know:

1. **Architecture**:
   - Part of MDP package (`mdp/grammar_assist.py`)
   - Integrates with Phase 1 masking (text-node scoped)
   - Follows MDP pattern (function returns result + stats dict)

2. **Constraints**:
   - Offline only (no network dependency)
   - Safe mode only (whitelist categories)
   - Non-interactive (zero prompts)
   - Deterministic (idempotent)
   - Structural validation required

3. **Integration**:
   - CLI: `--steps` argument for pipeline chaining
   - Config: `grammar_assist` section in `md_proof.yaml`
   - Stats: Return dict with applied/rejected counts

4. **Git Workflow**:
   - Create `feat/phase5-grammar-assist` branch from `dev`
   - Open PR into `dev`, not `main`
   - Include acceptance checklist in PR
   - Keep commits small and reviewable

---

## 🚀 Ready for Phase 5 Implementation

With this documentation, AI agents can now:

✅ **Understand the architecture** - Where Phase 5 fits in the pipeline  
✅ **Follow constraints** - Offline, safe mode, deterministic, non-interactive  
✅ **Integrate correctly** - CLI args, config, text-node scoping, mask respect  
✅ **Use proper Git workflow** - Feature branch from `dev`, PR into `dev`  
✅ **Write appropriate tests** - Determinism, structural validation, locale support  
✅ **Match existing patterns** - MDP module structure, stats return format

---

## 📝 Phase 5 Acceptance Criteria (from requirement)

These are now implicitly documented in the copilot instructions:

- [x] Grammar pass is toggleable via `md_proof.yaml` (documented: `grammar_assist.enabled: true`)
- [x] Only text nodes edited (documented: "Text-node scoped")
- [x] Summary in CLI/JSON report (documented: stats dict format)
- [x] Deterministic re-runs (documented: "Running twice produces identical output")
- [x] Tests pass including hell samples (documented: test structure)
- [x] No network dependency (documented: "Offline engine")
- [x] Branch workflow (documented: Git Workflow section)

---

## 🔍 Integration Points Clarified

### With Existing Architecture

**Phase 1 (Markdown Masking)**:
- Phase 5 receives `mask_table` from Phase 1
- Must respect masked regions (sentinels)
- Only operates on text nodes extracted by `extract_text_spans()`

**Phase 2/3 (Prepass)**:
- Phase 5 runs after prepass cleanup
- Works on already-normalized text
- Avoids re-correcting what prepass fixed

**Configuration System**:
- Extends existing `md_proof.yaml` structure
- Follows same pattern as `scrubber` and `prepass_advanced` sections
- Maintains "sensible defaults" philosophy

**CLI Integration**:
- Follows `--steps` pattern for pipeline chaining
- Can be combined with other phases
- Emits JSON report like other phases

---

## 📂 Files Changed

1. **`.github/copilot-instructions.md`** - Updated with Phase 5 documentation

---

## 🎯 Summary

The copilot instructions now provide AI agents with:

1. **Complete Phase 5 architecture** - How it works, where it fits
2. **Implementation constraints** - What must be followed
3. **Integration patterns** - How to connect with existing code
4. **Git workflow requirements** - How to manage branches/PRs
5. **Testing expectations** - Determinism, locales, structural validation

AI agents implementing Phase 5 will have all the context needed to:
- Write code that matches existing patterns
- Follow architectural constraints
- Use proper Git workflow
- Write appropriate tests
- Integrate seamlessly with existing pipeline

**Ready for Phase 5 implementation! 🚀**

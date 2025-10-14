# TTS-Proof Session Status
**Last Updated**: October 14, 2025  
**Current Branch**: `dev`  
**Status**: Ready for next session

---

## 📍 Current State

### ✅ Just Completed (Phase 14B)
**Single-Column UI Refactor** - Merged to `dev` (commits `04b10cf`, `7ab639c`)

**What Changed**:
- Created new single-column `AppNew.tsx` component with simplified flow
- Added centralized state management (`frontend/src/state/appStore.tsx`)
- Split UI into focused components: `ConnectionPanel`, `PresetPanel`, `InputPanel`, `OptionsPanel`, `RunPanel`
- Removed prepass UI controls (prepass now CLI-only as intended)
- Cleaned up component prop drilling with context providers

**Files Modified**:
- `frontend/src/AppNew.tsx` (new 592-line single-column layout)
- `frontend/src/state/appStore.tsx` (new centralized state)
- `frontend/src/components/OptionsPanel.tsx` (simplified, prepass removed)
- `frontend/src/components/RunPanel.tsx` (removed "Prepass only" button)
- Backend: detector schema cleanup, diff stats added to pipeline

**Technical Debt Paid**:
- Fixed preset/model selection flow (no longer auto-selects incompatible models)
- Added `backend/__pycache__/` to `.gitignore`
- Removed prepass state management from frontend

---

## 🏗️ Architecture Overview

### Backend (`backend/app.py`)
- FastAPI + WebSocket for real-time progress
- Endpoints: `/api/process`, `/api/prepass`, `/api/models`, `/api/runs`
- Run history stored in `runs/<run-id>/artifacts/`
- Imports core pipeline from `md_proof.py`

### Frontend (`frontend/src/`)
- **AppNew.tsx**: Single-column workflow (Connection → Preset → Input → Options → Run → History)
- **State**: `appStore.tsx` manages server, preset, overrides
- **Services**: `api.ts` handles REST + WebSocket
- **Components**: 6 focused panels, no global state library (React context only)

### Core Pipeline (`mdp/`)
- **Phase 1**: Markdown masking (`markdown_adapter.py`, `masking.py`)
- **Phase 2**: Unicode normalization (`prepass_basic.py`, `prepass_advanced.py`)
- **Phase 3**: Content scrubbing (`scrubber.py`)
- **Phase 5**: Grammar assist (`grammar_assist.py`)
- **Phase 6**: TTS problem detection (`detector/detector.py`)
- **Phase 7**: Fix application (`apply/applier.py`)
- **Phase 8**: Light polish (`fixer/fixer.py`)

### Config Files
- `config/lmstudio_preset_qwen3_grammar.json` - LM Studio preset for grammar
- `config/lmstudio_preset_qwen3_prepass.json` - LM Studio preset for detector
- `prompts/grammar_promt.txt` (intentional typo, do not rename)
- `prompts/prepass_prompt.txt`

---

## 🎯 Known Issues & Next Steps

### UI Issues (Non-Blocking)
1. **Preset selection still auto-resolves models** - When only one model available, preset panel auto-fills model fields but doesn't update run config properly
2. **Advanced overrides require preset toggle** - Users must enable "advanced mode" to specify remote servers or custom params
3. **No separate prepass model picker** - Grammar, detector, and fixer all share preset models
4. **Prepass prompt not editable in UI** - Only grammar prompt has an editor

### Recommended Next Session Actions

**Option A: Fix UI Model Selection** (2-3 hours)
- Add dedicated "Models" section with explicit picker for grammar/detector/fixer
- Decouple from presets (make presets optional hints, not required config)
- Support single-model servers gracefully
- Allow advanced overrides without preset toggle

**Option B: Merge Prepass + Pipeline Runs** (2-3 hours)
- Add "Run prepass + pipeline" combined action
- Store prepass results in run artifacts
- Auto-inject prepass findings into grammar prompt

**Option C: Real-World Testing** (1-2 hours)
- Convert sample EPUB to Markdown
- Run full pipeline: `mask → prepass-basic → prepass-advanced → scrub → detect → apply → fix`
- Document findings and tune configs

**Option D: Documentation Cleanup** (1 hour)
- Archive old phase markdown files to `docs/archive/`
- Update root README.md (currently 839 lines, too verbose)
- Create quick-start guide for contributors

---

## 📂 Key File Locations

### Configuration
- `.github/copilot-instructions.md` - AI assistant context (comprehensive project guide)
- `pytest.ini` - Test markers (fast, llm, slow, network)
- `mdp/config.py` - Pipeline config loader
- `config/*.json` - LM Studio presets

### Entry Points
- `launch.py` - Cross-platform launcher (recommended)
- `backend/app.py` - FastAPI server (port 8000)
- `frontend/src/index.tsx` - React app entry (port 5174)
- `md_proof.py` - Legacy CLI
- `mdp/__main__.py` - Modern CLI (`python -m mdp`)

### Testing
- `testing/unit_tests/` - 217+ unit tests (use `pytest` for fast tests)
- `testing/test_data/` - Test fixtures
- `testing/stress_test_results/` - Performance benchmarks

### Documentation
- `readme.md` - Main project README (needs trimming)
- `ROADMAP.md` - Post-Phase-5 roadmap (outdated, needs Phase 14+ update)
- `docs/phases/` - Phase implementation guides
- `CHANGELOG.md` - Version history

---

## 🔧 Development Workflow

### Quick Start (Development)
```bash
# Start both servers
python launch.py

# Or manually:
python backend/app.py          # Terminal 1
cd frontend && npm run dev     # Terminal 2
```

### Testing
```bash
# Fast tests only (no LLM calls)
pytest

# All tests including LLM
pytest -m ""

# Specific markers
pytest -m "llm"     # LLM-dependent tests
pytest -m "slow"    # Slow tests
pytest -m "network" # Network tests
```

### Git Workflow
- PRs target `dev` (never `main`)
- Feature branches: `feat/*` from `dev`
- Squash commits on merge
- Current branch: `dev` (ahead of `origin/dev` by 0 commits - synced)

---

## 🚨 Critical Conventions (Do Not Change)

1. **Prompt filename**: `grammar_promt.txt` (typo is intentional)
2. **Masking**: Always use Phase 1 masking before processing
3. **Sentinel format**: `<TEXT_TO_CORRECT>...</TEXT_TO_CORRECT>` for LLM calls
4. **WebSocket types**: `progress`, `completed`, `error`, `chunk_complete`, `paused`
5. **Chunking default**: 8000 characters
6. **Test markers**: Use `pytest` alone for fast feedback
7. **Artifact paths**: URL-encode both `{id}` and `{name}` in frontend

---

## 📊 Phase Completion Summary

| Phase | Module | Status | Production Ready |
|-------|--------|--------|------------------|
| 1: Masking | `markdown_adapter.py`, `masking.py` | ✅ Complete | ✅ Yes |
| 2: Prepass Basic | `prepass_basic.py` | ✅ Complete | ✅ Yes |
| 2+: Prepass Advanced | `prepass_advanced.py` | ✅ Complete | ✅ Yes |
| 3: Scrubber | `scrubber.py`, `appendix.py` | ✅ Complete | ✅ Yes |
| 5: Grammar Assist | `grammar_assist.py` | ✅ Complete | ✅ Yes |
| 6: Detector | `detector/detector.py` | ✅ Complete | ✅ Yes |
| 7: Applier | `apply/applier.py` | ✅ Complete | ✅ Yes |
| 8: Fixer | `fixer/fixer.py` | ✅ Complete | ✅ Yes |
| 11: Presets | Backend presets API | ✅ Complete | ✅ Yes |
| 14A: Presets UI | `PresetPanel.tsx` | ✅ Complete | ⚠️ Needs fixes |
| 14B: Single-Column UI | `AppNew.tsx` | ✅ Complete | ⚠️ Needs testing |

**Overall**: 🎉 All core phases complete, UI needs polish

---

## 💡 Quick Reference

### Run Full Pipeline (CLI)
```bash
python -m mdp input.md \
  --steps mask,prepass-basic,prepass-advanced,detect,apply \
  -o output.md \
  --report report.json \
  --report-pretty
```

### Check System Status
```bash
git status -sb                    # Git status
pytest -v                         # Run fast tests
python backend/app.py             # Start backend
cd frontend && npm run dev        # Start frontend
```

### Common Git Commands
```bash
git checkout dev                  # Switch to dev
git checkout -b feat/my-feature   # New feature branch
git add -A && git commit -m "..."  # Commit changes
git merge feat/my-feature         # Merge to current branch
```

---

## 🎓 For AI Assistants (Next Session)

**When resuming work**:
1. Read this file first for current state
2. Check `.github/copilot-instructions.md` for architecture details
3. Run `git status -sb` to verify branch
4. Ask user which option (A/B/C/D above) to pursue
5. Start with tests if touching core pipeline
6. Use `AppNew.tsx` for UI changes (not `App.tsx`)

**Key Context**:
- User prefers small, focused PRs
- Always test changes before committing
- Use existing patterns (no new libraries without discussion)
- Frontend: React hooks + context (no Redux/Zustand)
- Backend: FastAPI with WebSocket streaming
- Testing: pytest with markers for LLM tests

---

**Ready to continue! 🚀**

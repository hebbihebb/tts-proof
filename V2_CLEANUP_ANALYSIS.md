# V2 Cleanup Analysis

## Backend Features NOT in md_processor.py (Web-only)

All of these are **web UI specific** and not needed for CLI/Tkinter v2:

### File Management (Web-only)
- `POST /api/upload` - File upload endpoint
- `GET /api/temp-directory` - Temp directory info
- `POST /api/upload-prepass` - Upload prepass report

### Model Discovery (Web-only)
- `GET /api/models` - LM Studio model discovery
- `GET /api/test-endpoint` - Test endpoint connectivity
- `GET /api/blessed-models` - Get blessed models from config

### Prompt Management (Web-only)
- `GET/POST /api/grammar-prompt` - Get/save grammar prompt
- `GET/POST /api/prepass-prompt` - Get/save prepass prompt

### Run Management (Web-only)
- `GET /api/runs` - List all runs
- `GET /api/runs/{id}/artifacts` - List artifacts
- `GET /api/runs/{id}/artifacts/archive` - Download ZIP
- `GET /api/runs/{id}/artifacts/{name}` - Download artifact
- `DELETE /api/runs/{id}` - Delete run
- `GET /api/runs/{id}/report` - Get report
- `GET /api/runs/{id}/diff` - Get diff
- `GET /api/runs/{id}/result` - Get result

### Job Control (Web-only)
- `GET /api/job/{id}` - Job status
- `POST /api/job/{id}/pause` - Pause job
- `POST /api/job/{id}/resume` - Resume job
- `POST /api/job/{id}/cancel` - Cancel job
- `POST /api/prepass/cancel` - Cancel prepass

### Config Management (Web-only)
- `GET /api/presets` - List presets
- `PUT /api/presets/active` - Set active preset
- `GET /api/acronyms` - Get acronyms
- `PUT /api/acronyms` - Update acronyms

### Processing Endpoints (Web-only)
- `POST /api/process/{client_id}` - Old grammar processing
- `POST /api/prepass` - Old prepass detection
- `POST /api/run` - New unified run endpoint
- `WebSocket /ws/{client_id}` - Real-time progress

### Test/Health (Web-only)
- `GET /api/health` - Health check
- `GET /api/test-simple` - Simple test
- `POST /api/run-test` - Comprehensive test

## Core Processing Logic

### ✅ Already in md_processor.py
- Masking/unmasking (Phase 1)
- Prepass basic/advanced (Phase 2)
- Detector (Phase 6)
- Apply with validators (Phase 7)
- LLM client (OpenAI-compatible)
- Chunking logic
- Configuration

### ⚠️ Stubs in md_processor.py (need implementation)
- Phase 3: Scrubber (author notes, navigation removal)
- Phase 8: Fixer (light polish)
- Grammar assist (Phase 5) - LanguageTool integration

### ❌ NOT in md_processor.py (v1 legacy)
- Old checkpoint system (`write_ckpt`, `load_ckpt` from md_proof.py)
- URL masking (replaced by full markdown masking)
- Old prepass.py with WebSocket streaming
- Spinner class for terminal animation

## Files to DELETE

### Documentation (Obsolete for v2)
- [ ] `COMMIT_MESSAGE.md` - v1 commit message
- [ ] `PR_DESCRIPTION.md` - v1 PR description
- [ ] `CLEANUP_SUMMARY.md` - v1 cleanup summary
- [ ] `WEBUI_AUDIT.md` - v1 web UI audit
- [ ] `SESSION_STATUS.md` - v1 session status
- [ ] `readme_old.md` - Old readme
- [ ] `.github/copilot-instructions-update-summary.md` - Old Copilot update
- [ ] `.github/copilot-instructions-major-update.md` - Old Copilot update
- [ ] `.github/copilot-instructions-final.md` - Old Copilot version
- [ ] `.github/phase5-documentation-added.md` - Phase 5 doc
- [ ] `DIRECTORY_STRUCTURE.md` - Old structure (outdated)

### Test Output Files (Temporary)
- [ ] `test_output.md` - Temporary test output
- [ ] `test_output2.md` - Temporary test output

### Phase Documentation (v1 specific)
- [ ] `docs/phases/phase*.md` - All phase planning docs (11 files)
- [ ] `docs/PHASE*.md` - Phase completion reports (5 files)
- [ ] `docs/phases/phase-roadmap.md` - v1 roadmap
- [ ] `docs/phases/phase-status.md` - v1 status
- [ ] `docs/phases/phase-plan-analysis.md` - v1 analysis

### Integration/Testing Docs (v1 specific)
- [ ] `docs/integration_task_recommendations.md` - v1 integration
- [ ] `docs/functional_parity_analysis.md` - v1 parity
- [ ] `docs/baseline_results_analysis.md` - v1 baseline
- [ ] `docs/iteration_results_summary.md` - v1 iteration
- [ ] `docs/prompt_optimization_applied.md` - v1 prompt work
- [ ] `testing/docs/*.md` - Old session/test summaries

### Frontend README (v1 specific)
- [ ] `frontend/README.md` - React frontend README

## Files to KEEP

### Core Documentation
- ✅ `readme.md` - Update for v2
- ✅ `ROADMAP.md` - Update for v2
- ✅ `CHANGELOG.md` - Update for v2
- ✅ `.github/copilot-instructions.md` - Rewrite for v2

### V2 Documentation
- ✅ `V2_REFACTOR_PLAN.md` - V2 plan
- ✅ `V2_IMPLEMENTATION_STATUS.md` - V2 status
- ✅ `V2_ARCHITECTURE_COMPARISON.md` - V2 comparison

### Testing Guides (Update for v2)
- ✅ `docs/CLI_SMOKE_TEST_GUIDE.md` - Update for v2 CLI
- ✅ `docs/QUICK_TESTING_GUIDE.md` - Update for v2
- ✅ `docs/PYTEST_SETUP_COMPLETE.md` - Keep if still relevant
- ✅ `docs/PYTEST_CONFIGURATION_GUIDE.md` - Keep if still relevant

### Test Data (Keep all)
- ✅ `testing/test_data/**/*.md` - All test files

## Code to DELETE

### Backend (All web-specific)
- [ ] `backend/` - Entire directory (2134 lines)
  - `app.py` - FastAPI server
  - `requirements.txt` - Backend deps
  - `test_app.py` - Backend tests
  - `__pycache__/` - Python cache

### Frontend (All web-specific)
- [ ] `frontend/` - Entire directory (~5000 lines)
  - All React/TypeScript code
  - `package.json`, `vite.config.ts`, etc.
  - `src/` - All React components
  - `node_modules/` (if exists)

### Old Core Files (Replaced by md_processor.py)
- [ ] `md_proof.py` - Old grammar correction (replaced)
- [ ] `prepass.py` - Old prepass detection (replaced)

### Old Launchers (v1 web UI specific)
- [ ] `launch.py` - Launches both servers + browser
- [ ] `launch.bat` - Windows launcher
- [ ] `launch.sh` - Unix launcher
- [ ] `launch.ps1` - PowerShell launcher

### Old Prompt Files (Now embedded in md_processor.py)
- [ ] `grammar_promt.txt` - Embedded in md_processor.py
- [ ] `prepass_prompt.txt` - Embedded in md_processor.py

### Old Config Files (Replaced)
- [ ] `qwen3_test_config.json` - Old test config
- [ ] `prepass_report.json` - Old report

### Debug Scripts (v1 specific)
- [ ] `debug_languagetool.py` - LanguageTool debug

### Test Scripts (Old)
- [ ] `testing/simple_test.py` - Old simple test
- [ ] `testing/test_run_history.py` - Old run history test
- [ ] `testing/test_tie_breaker.py` - Old tie breaker test
- [ ] `testing/test_web_report.py` - Web report test
- [ ] `testing/test_web_runner.py` - Web runner test

## Files to UPDATE for V2

### Core Documentation
1. **readme.md** - Rewrite with:
   - v2 architecture (single-file CLI + Tkinter)
   - New CLI usage examples
   - Remove web UI instructions
   - Add Tkinter GUI instructions

2. **ROADMAP.md** - Update with:
   - Mark Phase 14 (Web UI) as obsolete
   - Add v2 completion milestones
   - Next steps: Tkinter GUI, Phase 3/8 implementation

3. **CHANGELOG.md** - Add v2.0 entry:
   - Major refactor to single-file architecture
   - Removed React/FastAPI web UI
   - Consolidated into CLI + Tkinter

4. **.github/copilot-instructions.md** - Rewrite:
   - Single-file patterns (md_processor.py)
   - No React/FastAPI/WebSocket
   - CLI and Tkinter GUI patterns
   - Embedded prompts, no external files
   - New 5-phase architecture (skip Grammar Assist)

## Summary

**Files to Delete**: ~65 files, ~15,000 lines
- 50+ documentation files
- 2 code directories (backend/, frontend/)
- 10+ obsolete scripts
- 5+ old config files

**Files to Keep**: ~20 files
- Core documentation (update)
- V2 documentation (new)
- Test data (unchanged)
- Core pipeline code (md_processor.py)

**Net Result**: 
- From 50+ source files → 1 source file (md_processor.py)
- From ~12,500 lines → ~1000 lines (92% reduction)
- From 3-tier web app → single-file CLI + planned Tkinter GUI

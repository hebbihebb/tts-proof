# TTS-Proof V2 Architecture Comparison

## Current State (V1) vs. Target State (V2)

### Architecture Diagram

#### V1 (Current - Multi-Component Web App)
```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  React Frontend (TypeScript)                         │   │
│  │  - AppNew.tsx (single-column UI)                     │   │
│  │  - AppStore (React Context)                          │   │
│  │  - 6 Panel Components                                │   │
│  │  - api.ts (REST + WebSocket client)                  │   │
│  │  Port: 5174 (Vite dev server)                        │   │
│  └────────────────┬─────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────┘
                    │ HTTP/WS
                    ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  backend/app.py                                      │   │
│  │  - REST endpoints (/api/process, /api/runs)         │   │
│  │  - WebSocket manager (/ws/{client_id})              │   │
│  │  - Run history storage (~/.mdp/runs/)               │   │
│  │  - Preset management                                 │   │
│  │  Port: 8000                                          │   │
│  └────────────────┬─────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────────┐
│               MDP Pipeline (Python)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  mdp/ (8 modules)                                    │   │
│  │  - markdown_adapter.py (masking)                     │   │
│  │  - prepass_basic.py                                  │   │
│  │  - prepass_advanced.py                               │   │
│  │  - scrubber.py                                       │   │
│  │  - grammar_assist.py                                 │   │
│  │  - config.py                                         │   │
│  │  detector/ (4 modules)                               │   │
│  │  apply/ (3 modules)                                  │   │
│  │  fixer/ (4 modules)                                  │   │
│  └────────────────┬─────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────┘
                    │ HTTP
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                  LM Studio (Local LLM)                       │
│  Port: 1234                                                  │
│  - OpenAI-compatible API                                     │
│  - qwen3-grammar, qwen3-detector models                      │
└─────────────────────────────────────────────────────────────┘
```

#### V2 (Target - Consolidated Core + One-Shot UI)
```
Option A: CLI Usage
┌─────────────────────────────────────────────────────────────┐
│                  Terminal / Shell                            │
│  $ python md_processor.py \                                  │
│      --input input.md \                                      │
│      --output output.md \                                    │
│      --steps mask,detect,apply \                             │
│      --endpoint http://localhost:1234/v1                     │
│                                                              │
│  [Progress] Phase 1: Masking... 20%                         │
│  [Progress] Phase 6: Detecting... 60%                       │
│  [Progress] Phase 7: Applying... 100%                       │
│  [Done] Wrote output to: output.md                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│            md_processor.py (Single File)                     │
│  - All 8 phases embedded                                     │
│  - LLM client (OpenAI-compatible)                            │
│  - Masking/validation logic                                  │
│  - Progress callbacks                                        │
│  - Checkpoint/resume                                         │
│  - Embedded prompts & config                                 │
│  - CLI (argparse) + Library API                              │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                  LM Studio (Local LLM)                       │
│  Port: 1234                                                  │
└─────────────────────────────────────────────────────────────┘

Option B: GUI Usage
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  one_shot_gui.html (Single File)                     │   │
│  │  ┌───────────────────────────────────────────────┐   │   │
│  │  │  📁 Drag & Drop File Here                      │   │   │
│  │  │     or click to select                         │   │   │
│  │  └───────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  │  Endpoint: [http://localhost:1234/v1        ]      │   │
│  │  Model:    [qwen3-grammar                   ]      │   │
│  │  Steps:    ☑ Mask  ☑ Detect  ☑ Apply              │   │
│  │                                                      │   │
│  │  [  Run Pipeline  ]  [  Reset  ]                   │   │
│  │                                                      │   │
│  │  ████████████░░░░░░░░░░░░░░░░░░░░  60%             │   │
│  │  Phase 6: Detecting problems...                     │   │
│  │                                                      │   │
│  │  ┌─────────── Log Output ────────────────────┐     │   │
│  │  │ [10:23:45] Loaded: input.md (5432 chars)  │     │   │
│  │  │ [10:23:46] Phase 1: Masking... Done        │     │   │
│  │  │ [10:23:47] Masked 15 regions               │     │   │
│  │  │ [10:23:49] Phase 6: Detecting...           │     │   │
│  │  └────────────────────────────────────────────┘     │   │
│  │                                                      │   │
│  │  [  Download Result  ]                              │   │
│  │                                                      │   │
│  │  (Embedded CSS + JavaScript)                        │   │
│  └──────────────────┬───────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │ Direct HTTP calls
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  LM Studio (Local LLM)                       │
│  Port: 1234                                                  │
│  - Fetch API from JavaScript                                 │
│  - No backend server needed                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure Comparison

### V1 (Current)
```
tts-proof/
├── backend/
│   ├── app.py                 (2134 lines, FastAPI routes)
│   ├── requirements.txt
│   └── test_app.py
├── frontend/
│   ├── src/
│   │   ├── AppNew.tsx         (592 lines, React)
│   │   ├── state/appStore.tsx (107 lines, Context)
│   │   ├── services/api.ts    (689 lines, API client)
│   │   └── components/        (6 panel components)
│   ├── package.json
│   ├── vite.config.ts
│   └── ...
├── mdp/
│   ├── __main__.py            (542 lines, CLI)
│   ├── markdown_adapter.py    (126 lines)
│   ├── masking.py
│   ├── prepass_basic.py       (207 lines)
│   ├── prepass_advanced.py    (478 lines)
│   ├── scrubber.py            (355 lines)
│   ├── grammar_assist.py      (367 lines)
│   ├── config.py              (137 lines)
│   └── tie_breaker.py         (350 lines)
├── detector/
│   ├── detector.py            (248 lines)
│   ├── client.py
│   ├── schema.py
│   └── chunking.py
├── apply/
│   ├── applier.py             (163 lines)
│   ├── validate.py            (331 lines)
│   └── matcher.py
├── fixer/
│   ├── fixer.py               (244 lines)
│   ├── client.py
│   ├── prompt.py
│   └── guards.py
├── prompts/
│   ├── grammar_promt.txt
│   └── prepass_prompt.txt
├── config/
│   ├── lmstudio_preset_qwen3_grammar.json
│   └── lmstudio_preset_qwen3_prepass.json
├── testing/
│   ├── unit_tests/            (217+ tests)
│   └── test_data/
├── md_proof.py                (292 lines, legacy CLI)
├── prepass.py                 (legacy prepass engine)
└── launch.py                  (orchestrator)

Total: ~50+ files, ~5000+ lines of code
Dependencies: Python (FastAPI, uvicorn, pydantic, etc.), Node.js (React, Vite, TypeScript, etc.)
```

### V2 (Target)
```
tts-proof/
├── md_processor.py            (~2000 lines, all-in-one)
│   ├── Configuration constants
│   ├── Phase 1: Masking
│   ├── Phase 2: Prepass (basic + advanced)
│   ├── Phase 3: Scrubber
│   ├── Phase 5: Grammar Assist
│   ├── Phase 6: Detector
│   ├── Phase 7: Apply + Validators
│   ├── Phase 8: Fixer
│   ├── LLM Client
│   ├── Chunking & Checkpointing
│   ├── Progress Callback System
│   ├── Pipeline Orchestrator
│   └── CLI Entry Point
│
├── one_shot_gui.html          (~500 lines, HTML+CSS+JS)
│   ├── Responsive UI
│   ├── File upload
│   ├── Configuration inputs
│   ├── Run/Reset controls
│   ├── Progress bar
│   ├── Log output
│   ├── Download result
│   └── Direct LLM API calls
│
├── legacy/                    (archived v1 components)
│   ├── README.md
│   ├── backend/
│   ├── frontend/
│   └── launch.py
│
├── testing/
│   ├── test_md_processor.py   (new unit tests)
│   └── test_data/
│
├── V2_ARCHITECTURE.md
├── MIGRATION_GUIDE.md
└── readme.md                  (updated for v2)

Total: 2 core files (~2500 lines), minimal dependencies
Dependencies: Python (requests, beautifulsoup4 optional), Modern browser
```

---

## Feature Comparison Matrix

| Feature | V1 | V2 | Notes |
|---------|----|----|-------|
| **Core Processing** |
| Masking (Phase 1) | ✅ | ✅ | Preserved |
| Prepass Basic (Phase 2) | ✅ | ✅ | Preserved |
| Prepass Advanced (Phase 2+) | ✅ | ✅ | Preserved |
| Scrubber (Phase 3) | ✅ | ✅ | Preserved |
| Grammar Assist (Phase 5) | ✅ | ✅ | Preserved (optional) |
| Detector (Phase 6) | ✅ | ✅ | Preserved |
| Apply + Validators (Phase 7) | ✅ | ✅ | All 7 validators preserved |
| Fixer (Phase 8) | ✅ | ✅ | Preserved |
| **LLM Integration** |
| LM Studio support | ✅ | ✅ | OpenAI-compatible API |
| Model presets | ✅ | ❌ | Manual config in v2 |
| Multi-server support | ✅ | ❌ | Single endpoint in v2 |
| **Processing Features** |
| Intelligent chunking | ✅ | ✅ | Preserved |
| Checkpoint/resume | ✅ | ✅ | Preserved |
| Progress reporting | ✅ | ✅ | Via callbacks |
| **User Interface** |
| Web UI | ✅ | ✅ | Simplified (one-shot) |
| CLI | ✅ | ✅ | Simplified |
| Real-time WebSocket | ✅ | ❌ | Progress bar instead |
| Run history browser | ✅ | ❌ | Not in v2 |
| Diff viewer | ✅ | ❌ | Not in v2 |
| Mobile-friendly UI | ⚠️ | ✅ | Improved in v2 |
| **Configuration** |
| Preset management | ✅ | ❌ | Manual in v2 |
| Config files (YAML) | ✅ | ✅ | Optional override |
| Embedded defaults | ❌ | ✅ | In md_processor.py |
| **Artifacts & History** |
| Run artifacts (~/.mdp/runs/) | ✅ | ❌ | Not in v2 |
| Run history API | ✅ | ❌ | Not in v2 |
| Decision logs (NDJSON) | ✅ | ❌ | Not in v2 |
| JSON reports | ✅ | ✅ | CLI output |
| **Development** |
| Testing framework | ✅ | ⚠️ | Needs new tests |
| Documentation | ✅ | ⚠️ | Needs update |
| Deployment complexity | High | Low | 2 files vs 50+ |
| **Dependencies** |
| Python packages | Many | Few | requests only |
| Node.js required | ✅ | ❌ | Not needed |
| Browser required | ✅ | ✅ | For GUI only |

---

## Code Size Comparison

### V1 (Current)
- **Backend**: ~2,500 lines (Python)
- **Frontend**: ~2,000 lines (TypeScript/React)
- **MDP Pipeline**: ~2,500 lines (Python modules)
- **Detector/Apply/Fixer**: ~1,500 lines (Python)
- **Tests**: ~3,000 lines (pytest)
- **Config/Docs**: ~1,000 lines
- **Total**: ~12,500 lines across 50+ files

### V2 (Target)
- **Core Library**: ~2,000 lines (md_processor.py)
- **GUI**: ~500 lines (one_shot_gui.html)
- **Tests**: ~1,000 lines (test_md_processor.py)
- **Docs**: ~500 lines (updated)
- **Total**: ~4,000 lines across 5 files

**Reduction**: ~67% fewer lines, ~90% fewer files

---

## Deployment Comparison

### V1 Deployment Steps
1. Install Python 3.10+
2. Install Node.js 16+
3. Install Python dependencies (`pip install -r backend/requirements.txt`)
4. Install Node dependencies (`cd frontend && npm install`)
5. Start LM Studio on port 1234
6. Run launcher (`python launch.py`)
7. Wait for both servers to start
8. Browser opens to localhost:5174

**Dependencies**: ~200MB Python packages, ~400MB Node modules

### V2 Deployment Steps
**Option A (CLI)**:
1. Install Python 3.10+
2. Install minimal dependencies (`pip install requests`)
3. Start LM Studio on port 1234
4. Run CLI (`python md_processor.py --input input.md --output output.md`)

**Option B (GUI)**:
1. Install Python 3.10+ (optional, for enhanced features)
2. Start LM Studio on port 1234
3. Open `one_shot_gui.html` in browser

**Dependencies**: ~5MB Python packages (or zero if using GUI directly)

---

## Performance Comparison

| Metric | V1 | V2 | Improvement |
|--------|----|----|-------------|
| Startup time | ~10 seconds | Instant | ✅ 10x faster |
| Memory usage | ~500MB | ~100MB | ✅ 5x reduction |
| Processing speed | ~same | ~same | = No change |
| Browser requirements | Modern | Modern | = Same |

---

## Use Case Scenarios

### Scenario 1: Command-Line Power User
**V1**: `python -m mdp input.md --steps mask,detect,apply -o output.md`  
**V2**: `python md_processor.py --input input.md --output output.md --steps mask,detect,apply`  
**Winner**: V2 (simpler, no package installation)

### Scenario 2: Casual User with GUI
**V1**: Run `python launch.py`, wait for servers, upload file, configure, run, download  
**V2**: Open `one_shot_gui.html`, drop file, click Run, download  
**Winner**: V2 (fewer steps, faster)

### Scenario 3: Batch Processing (100 files)
**V1**: Write script calling `/api/process` endpoint  
**V2**: Write shell script calling `md_processor.py` in loop  
**Winner**: V2 (no server overhead)

### Scenario 4: Mobile Device
**V1**: Difficult (servers on desktop, access via local network)  
**V2**: Easy (open GUI on mobile browser, process locally)  
**Winner**: V2 (mobile-first design)

### Scenario 5: Debugging Pipeline Issue
**V1**: Check backend logs, frontend console, WebSocket messages, run artifacts  
**V2**: Check CLI output or browser console  
**Winner**: V2 (simpler debugging)

---

## Migration Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| Week 1 | Core consolidation | `md_processor.py` with all phases |
| Week 2 | CLI + Testing | Working CLI, unit tests |
| Week 3 | GUI implementation | `one_shot_gui.html` |
| Week 4 | Documentation + Polish | Docs, migration guide, archive v1 |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Feature parity loss | Low | Medium | All core phases preserved |
| Performance regression | Low | High | Reuse existing logic |
| Testing coverage loss | Medium | High | Write comprehensive unit tests |
| User adoption resistance | Medium | Medium | Provide migration guide |
| LM Studio compatibility | Low | High | Use same OpenAI API |
| Mobile browser issues | Medium | Low | Test on iOS/Android |

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Single file for core | Easier to distribute, understand, maintain |
| Embedded prompts | Eliminate external file dependencies |
| No run history | Simplicity > features for v2 |
| Direct LLM calls in GUI | No backend server needed |
| Archive (not delete) v1 | Preserve for reference |
| Keep all validators | Safety is paramount |
| Progress callbacks | Flexible for CLI/GUI |

---

**Next Steps**: Review comparison, approve v2 architecture, begin Phase 1 (Core Consolidation).

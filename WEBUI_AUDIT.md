# Web UI Audit - Phase 11 MVP Foundation

**Date:** October 13, 2025  
**Branch:** `feat/phase11-webui`  
**Purpose:** Map existing UI/API structure to identify integration points for Phase 11

---

## 1. Frontend Architecture

### Build & Serve
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS with dark/light theme support
- **Build Tool:** Vite (`vite.config.ts`)
- **Dev Server:** `npm run dev` → `http://localhost:5173` (or 5174)
- **Entry Point:** `src/index.tsx` → `src/App.tsx`

### File Structure
```
frontend/
├── src/
│   ├── App.tsx                    # Main application (629 lines)
│   ├── AppRouter.tsx              # Routing (if used)
│   ├── index.tsx                  # React entry point
│   ├── index.css                  # Global styles
│   ├── components/
│   │   ├── Button.tsx             # Reusable button component
│   │   ├── ChunkSizeControl.tsx   # Chunk size slider (4K-16K)
│   │   ├── EndpointConfig.tsx     # LM Studio endpoint configuration
│   │   ├── FileAnalysis.tsx       # File upload analysis display
│   │   ├── FileSelector.tsx       # Drag-and-drop file upload
│   │   ├── LogArea.tsx            # Processing logs display
│   │   ├── ModelPicker.tsx        # Model selection dropdown
│   │   ├── PrepassControl.tsx     # TTS prepass controls
│   │   ├── PreviewWindow.tsx      # Text preview pane
│   │   ├── ProgressBar.tsx        # Progress indicator
│   │   ├── PromptEditor.tsx       # Prompt template editor
│   │   ├── ThemeContext.tsx       # Dark/light theme context
│   │   └── ThemeToggle.tsx        # Theme switcher button
│   └── services/
│       └── api.ts                 # API service class (413 lines)
├── index.html                     # HTML shell
├── package.json                   # Dependencies & scripts
├── vite.config.ts                 # Vite configuration
└── tailwind.config.js             # Tailwind configuration
```

### Current UI Layout (6-Section Grid)
**Top Row (Setup):**
1. **FileSelector** - Drag & drop Markdown file upload
2. **ModelPicker** - LLM model selection (grammar & prepass)
3. **ChunkSizeControl** - Processing chunk size (4K-16K chars)

**Bottom Row (Processing):**
4. **PrepassControl** - TTS detection run (optional)
5. **PromptEditor** - Customize grammar/prepass prompts
6. **Processing Controls** - Run button + progress + status

**Bottom Panels:**
- **PreviewWindow** - Original/processed text preview
- **LogArea** - Real-time processing logs

---

## 2. Backend API Structure

### Server
- **Framework:** FastAPI + Uvicorn
- **File:** `backend/app.py` (1117 lines)
- **Port:** `http://localhost:8000`
- **CORS:** Configured for `localhost:5173` and `localhost:5174`

### Core Endpoints

#### File Management
```python
POST /api/upload
  → FormData with file
  → Returns: {file_id, filename, size, content_preview, full_content, temp_path}

GET /api/temp-directory
  → Returns: {temp_dir: str}
```

#### Model Management
```python
GET /api/models?api_base=<endpoint>
  → Fetches models from LM Studio server
  → Returns: List[{id, name, description}]
```

#### Prompt Management
```python
GET /api/grammar-prompt
  → Returns: {prompt: str, source: str}
  → Loads from `grammar_promt.txt`

POST /api/grammar-prompt
  → Body: {prompt: str}
  → Saves to `grammar_promt.txt`

GET /api/prepass-prompt
  → Returns: {prompt: str, source: str}
  → Loads from `prepass_prompt.txt`

POST /api/prepass-prompt
  → Body: {prompt: str}
  → Saves to `prepass_prompt.txt`
```

#### Processing Endpoints
```python
POST /api/prepass
  → Body: {file_id, api_base, model, chunk_size, client_id}
  → Runs TTS detection (prepass.py)
  → Streams progress via WebSocket
  → Returns: {report: {...}, report_path: str}

POST /api/process/{client_id}
  → Body: {content, model_name, api_base, prompt_template, chunk_size, use_prepass, prepass_report, ...}
  → Runs grammar correction (md_proof.py)
  → Streams progress via WebSocket
  → Returns: {result: str, chunks_processed: int, ...}

POST /api/prepass/cancel
  → Body: {client_id}
  → Cancels running prepass job

POST /api/run-test
  → Test endpoint for smoke testing
```

#### Job Management
```python
GET /api/job/{job_id}
  → Returns: {status, progress, result?, error?}

POST /api/job/{job_id}/pause
POST /api/job/{job_id}/resume
POST /api/job/{job_id}/cancel
GET /api/job/{job_id}/chunks
  → Returns chunk-by-chunk progress
```

#### Health Check
```python
GET /api/health
  → Returns: {status: "healthy"}

GET /api/test-endpoint
GET /api/test-simple
  → Testing endpoints
```

---

## 3. WebSocket Communication

### Connection
- **URL Pattern:** `ws://localhost:8000/ws/{client_id}`
- **Client ID:** Generated in frontend: `Math.random().toString(36).substring(7)`
- **Manager:** `ConnectionManager` singleton in `backend/app.py`

### Message Schema

#### Progress Messages (Grammar Processing)
```typescript
{
  type: 'progress',
  source: 'grammar',              // Identifies grammar correction phase
  progress: 45.5,                 // Percentage (0-100)
  message: "Processing chunk 5 of 11",
  chunks_processed: 5,
  total_chunks: 11
}
```

#### Progress Messages (Prepass Detection)
```typescript
{
  type: 'progress',
  source: 'prepass',              // Identifies prepass phase
  progress: 60.0,
  message: "Detecting TTS problems in chunk 6 of 10",
  chunks_processed: 6,
  total_chunks: 10
}
```

#### Completion Messages
```typescript
{
  type: 'completed',
  source: 'grammar' | 'prepass',
  message: "Processing complete",
  result: string | object         // Processed text or prepass report
}
```

#### Error Messages
```typescript
{
  type: 'error',
  source: 'grammar' | 'prepass',
  message: "Error description",
  error?: string
}
```

#### Chunk Completion
```typescript
{
  type: 'chunk_complete',
  source: 'grammar',
  chunk_index: 5,
  output_size: 12345,
  total_processed: 67890
}
```

---

## 4. Current Processing Flow

### Legacy Grammar Correction (md_proof.py)
**Current UI Flow:**
1. User uploads file → `POST /api/upload`
2. User selects model & chunk size
3. User optionally runs prepass → `POST /api/prepass` (streams via WebSocket)
4. User clicks "Process" → `POST /api/process/{client_id}` (streams via WebSocket)
5. Backend calls:
   - `load_markdown()` → `chunk_paragraphs()` → `correct_chunk()` per chunk
   - Uses `md_proof.py` functions directly (not via subprocess)
   - Applies prepass report if available via `inject_prepass_into_grammar_prompt()`
6. WebSocket streams progress
7. Result returned as string in completion message

**Issues:**
- Uses legacy `md_proof.py` (not the new `mdp/__main__.py` orchestrator)
- No step toggles (hardcoded grammar + optional prepass)
- No detector/apply/fix integration
- No structural validation
- No pretty report generation
- No diff output

---

## 5. Model Picker Current State

### How It Works Today
**Frontend (`ModelPicker.tsx`):**
- Calls `apiService.fetchModels(currentEndpoint)`
- Displays dropdown with model names
- Stores selected model ID in state

**Backend (`app.py`):**
```python
@app.get("/api/models")
async def get_models(api_base: Optional[str] = None):
    # Calls LM Studio's /v1/models endpoint
    # Parses response and returns [{id, name, description}]
    # Fallback to default models if connection fails
```

**Current Link to config.py:** ❌ **None**
- Models are fetched dynamically from LM Studio at runtime
- No blessed list or validation
- UI accepts any model returned by LM Studio

### What Needs to Change
- Add `get_blessed_models()` helper in `config.py`
- Backend validates model selection against blessed list
- UI dropdown shows only blessed models
- Separate pickers for detector vs fixer models

---

## 6. Integration Points for Phase 11

### Where to Add Step Toggles
**Frontend (`App.tsx`):**
- Add state for step selections:
  ```typescript
  const [enabledSteps, setEnabledSteps] = useState<string[]>([
    'mask',            // Always implied
    'prepass-basic',   // Default ON
    'prepass-advanced',// Default ON
    'grammar',         // Default ON
    'detect',          // Default ON
    'apply',           // Default ON
    'fix'              // Default ON
    // 'scrubber'      // Default OFF
  ]);
  ```
- Add UI component: `<StepToggles />` in the top row or left sidebar
- Checkboxes for each step with descriptions

**Backend Integration:**
- Modify `POST /api/process` to accept `steps: List[str]`
- Call `mdp.__main__.run_pipeline(text, steps, config)` instead of `md_proof.py`
- Return structured report data (not just corrected text)

### Where to Display Pretty Report
**Frontend (`App.tsx`):**
- Add new panel/tab in bottom section: `<ReportViewer />`
- After completion, call `GET /api/result?run_id={id}`
- Render `pretty_report` field in monospace `<pre>` block

**Backend:**
- Import: `from report.pretty import render_pretty`
- After pipeline completes, call:
  ```python
  report_data = {
    'input_file': input_path,
    'output_file': output_path,
    'steps': steps,
    'statistics': stats
  }
  pretty = render_pretty(report_data)
  ```
- Store in job result for retrieval

### Where to Show Diff Preview
**Frontend (`App.tsx`):**
- Add new panel/tab: `<DiffViewer />`
- Fetch diff from `GET /api/result?run_id={id}`
- Display `diff_head` field in syntax-highlighted monospace

**Backend:**
- Add `--print-diff` equivalent to `run_pipeline()` call
- Capture unified diff output
- Store first ~200 lines as `diff_head` in result
- Full diff saved as artifact

### Where to Add Artifact Downloads
**Frontend (`App.tsx`):**
- Add buttons in results panel:
  - "Download Output" → `GET /api/artifact?run_id={id}&name=output.md`
  - "Download Plan (JSON)" → `GET /api/artifact?run_id={id}&name=plan.json`
  - "Download Report" → `GET /api/artifact?run_id={id}&name=report.json`
  - "Download Rejected" (if exists) → `GET /api/artifact?run_id={id}&name=rejected.md`

**Backend:**
- Add `GET /api/artifact` endpoint
- Stream file from `~/.mdp/runs/{run_id}/` directory
- Use `FileResponse` for downloads

---

## 7. Current Model Configuration (`config.py`)

### Detector Settings
```python
'detector': {
    'enabled': True,
    'api_base': 'http://192.168.8.104:1234/v1',
    'model': 'qwen2.5-1.5b-instruct',
    'max_context_tokens': 1024,
    'temperature': 0.2,
    ...
}
```

### Fixer Settings
```python
'fixer': {
    'enabled': True,
    'model': 'qwen2.5-1.5b-instruct',
    'api_base': 'http://127.0.0.1:1234/v1',
    'max_context_tokens': 1024,
    'temperature': 0.2,
    ...
}
```

### Action Required
**Add helper function to `config.py`:**
```python
def get_blessed_models() -> Dict[str, List[str]]:
    """
    Returns blessed model lists for detector and fixer.
    MVP focuses on Qwen2.5-1.5B-Instruct.
    
    Returns:
        {
            'detector': ['qwen2.5-1.5b-instruct'],
            'fixer': ['qwen2.5-1.5b-instruct']
        }
    """
    return {
        'detector': ['qwen2.5-1.5b-instruct'],
        'fixer': ['qwen2.5-1.5b-instruct']
    }
```

---

## 8. Orchestrator Integration Strategy

### Current Problem
- Backend uses **`md_proof.py`** directly (legacy chunking + correction)
- New pipeline uses **`mdp.__main__.run_pipeline()`** (Phases 1-8 orchestrator)
- These are **separate code paths** with different logic

### Solution for Phase 11
**Replace backend processing logic:**

**Before (Legacy):**
```python
# backend/app.py - current approach
from md_proof import correct_chunk, chunk_paragraphs, ...
# Manually loop through chunks, call LLM, handle WebSocket updates
```

**After (Orchestrator):**
```python
# backend/app.py - new approach
from mdp.__main__ import run_pipeline
from mdp.config import load_config

# Call unified orchestrator
config = load_config()
output_text, stats = run_pipeline(
    input_text=content,
    steps=requested_steps,  # From UI toggles
    config=config
)

# Generate pretty report
from report.pretty import render_pretty
report_data = {
    'input_file': input_path,
    'output_file': output_path,
    'steps': requested_steps,
    'statistics': stats
}
pretty = render_pretty(report_data)
```

**WebSocket Integration:**
- Modify `run_pipeline()` to accept optional callback for progress updates
- OR: Run in background task, poll stats, send WebSocket messages periodically
- OR: Add hooks in orchestrator for progress reporting

---

## 9. Exit Code Handling

### Current CLI Exit Codes
```python
# mdp/__main__.py
0  # Success
1  # General error
2  # Model unreachable (ConnectionError)
3  # Validation failure (apply step)
4  # Plan parse error (detect step)
```

### UI Toast Mapping
```typescript
switch (exitCode) {
  case 0:
    showToast('success', 'Processing completed successfully!');
    break;
  case 2:
    showToast('error', 'Model server unreachable. Check LM Studio.');
    break;
  case 3:
    showToast('warning', 'Validation failed. See rejected file.');
    // Show link to rejected artifact
    break;
  case 4:
    showToast('error', 'Failed to parse detector plan.');
    break;
  default:
    showToast('error', 'Processing failed with unknown error.');
}
```

---

## 10. Proposed New Endpoints (PR-1 & PR-2)

### Unified Run Endpoint
```python
POST /api/run
Request:
{
  "input_path": "/path/to/file.md",
  "steps": ["mask", "detect", "apply", "fix"],
  "models": {
    "detector": "qwen2.5-1.5b-instruct",
    "fixer": "qwen2.5-1.5b-instruct"
  },
  "config_overrides": {},  # Optional
  "report_pretty": true
}

Response:
{
  "run_id": "abc123",
  "status": "started",
  "message": "Pipeline started"
}
```

### Result Endpoint
```python
GET /api/result?run_id=abc123
Response:
{
  "exit_code": 0,
  "output_path": "~/.mdp/runs/abc123/output.md",
  "rejected_path": null,
  "plan_path": "~/.mdp/runs/abc123/plan.json",
  "json_report_path": "~/.mdp/runs/abc123/report.json",
  "pretty_report": "<rendered pretty report string>",
  "diff_head": "<first ~200 lines of unified diff>"
}
```

### Artifact Download
```python
GET /api/artifact?run_id=abc123&name=output.md
  → Streams file as download
  → FileResponse with appropriate mime type
```

---

## 11. State Persistence Strategy

### Storage Location
- **Path:** `~/.mdp/ui_state.json`
- **Format:** JSON

### Stored Settings
```json
{
  "enabled_steps": ["mask", "prepass-basic", "detect", "apply", "fix"],
  "models": {
    "detector": "qwen2.5-1.5b-instruct",
    "fixer": "qwen2.5-1.5b-instruct"
  },
  "chunk_size": 8000,
  "endpoint": "http://127.0.0.1:1234/v1",
  "theme": "dark",
  "last_updated": "2025-10-13T12:34:56Z"
}
```

### Implementation
**Backend:**
```python
GET /api/ui-state
  → Returns JSON from ~/.mdp/ui_state.json

POST /api/ui-state
  → Saves JSON to ~/.mdp/ui_state.json
```

**Frontend:**
- Load state on mount
- Save state on change (debounced)
- "Reset to Balanced" button restores defaults

---

## 12. WebSocket Schema Consistency

### Current Schema (Needs Documentation)
**Grammar Processing:**
```typescript
{
  type: 'progress' | 'completed' | 'error' | 'chunk_complete',
  source: 'grammar',
  progress: number,      // 0-100
  message: string,
  chunks_processed?: number,
  total_chunks?: number,
  result?: string        // On 'completed'
}
```

**Prepass Processing:**
```typescript
{
  type: 'progress' | 'completed' | 'error',
  source: 'prepass',
  progress: number,
  message: string,
  chunks_processed?: number,
  total_chunks?: number,
  result?: object        // Prepass report on 'completed'
}
```

### Phase 11 Extensions Needed
Add `source` values for new steps:
- `'detect'` - Detector phase
- `'apply'` - Applier phase
- `'fix'` - Fixer phase
- `'scrubber'` - Scrubber phase (if enabled)

---

## 13. Current Gaps & Required Work

### ❌ Missing Components
1. **Step toggle UI** - Need checkboxes for all 8 steps
2. **Blessed model validation** - No `get_blessed_models()` in `config.py`
3. **Orchestrator integration** - Backend still uses `md_proof.py` directly
4. **Pretty report display** - No UI component to render report
5. **Diff viewer** - No diff preview panel
6. **Artifact downloads** - No `/api/artifact` endpoint
7. **Exit code surfacing** - No toast notifications for error codes
8. **State persistence** - No `~/.mdp/ui_state.json` handling
9. **Run directory structure** - No `~/.mdp/runs/{run_id}/` organization

### ✅ Existing Components (Reusable)
1. **File upload** - Working via `POST /api/upload`
2. **Model picker UI** - Functional dropdown (needs blessing validation)
3. **Progress tracking** - WebSocket streaming works
4. **Log display** - `LogArea` component renders messages
5. **Theme system** - Dark/light mode with persistence
6. **Preview panes** - `PreviewWindow` component ready
7. **Chunk size control** - Slider component functional
8. **Prompt editing** - `PromptEditor` modal works

---

## 14. PR-0 Action Items

### ✅ Documentation (This File)
- [x] Map frontend structure
- [x] Document API endpoints
- [x] Describe WebSocket schema
- [x] Identify integration points
- [x] Propose new endpoints
- [x] Document current gaps

### 🔧 Code Changes (Small Helpers Only)
- [ ] Add `get_blessed_models()` to `mdp/config.py`
- [ ] Add unit tests for `get_blessed_models()`

### 📋 No Behavior Changes
- No UI modifications
- No new endpoints
- No processing logic changes
- Just audit + helper function

---

## 15. Next Steps (PR-1, PR-2, PR-3)

### PR-1: Step Toggles + Model Pickers + Run Wiring
- Add step toggle checkboxes in UI
- Replace backend logic to call `run_pipeline()` orchestrator
- Add `/api/run` endpoint with step selection
- Validate models against blessed list
- Stream progress via WebSocket with new `source` values

### PR-2: Pretty Report + Diff Viewer + Artifacts
- Add `/api/result` endpoint with pretty report
- Add `/api/artifact` endpoint for downloads
- Create `<ReportViewer />` component
- Create `<DiffViewer />` component
- Add artifact download buttons

### PR-3: State Persistence + Polish
- Implement `~/.mdp/ui_state.json` persistence
- Add "Reset to Balanced" preset button
- Add progress pills per step
- Collapsible console
- Final UX polish

---

## 16. Testing Strategy

### Fast Unit Tests
```python
# tests/test_web_runner.py
def test_orchestrator_called_with_steps():
    # Verify UI runner calls run_pipeline() with exact steps
    pass

def test_artifacts_written_to_run_directory():
    # Verify outputs in ~/.mdp/runs/{run_id}/
    pass

# tests/test_config_blessed.py
def test_get_blessed_models_returns_correct_structure():
    models = get_blessed_models()
    assert 'detector' in models
    assert 'fixer' in models
    assert 'qwen2.5-1.5b-instruct' in models['detector']
```

### API Integration Tests
```python
# tests/test_web_api.py
@pytest.mark.network
async def test_upload_run_result_flow():
    # Upload → Run → Result → Artifact download
    pass

def test_pretty_report_present_in_result():
    # Assert pretty_report field exists and non-empty
    pass

def test_diff_head_non_empty_when_apply_runs():
    # Assert diff_head present when apply step enabled
    pass
```

### State Persistence Tests
```python
# tests/test_web_state.py
def test_state_persists_and_restores():
    # Save state → restart → verify restored
    pass

def test_reset_to_balanced_preset():
    # Verify defaults restored correctly
    pass
```

---

## Summary

**Current State:**
- ✅ Working file upload, model picker, progress tracking
- ✅ WebSocket streaming for grammar + prepass
- ❌ Uses legacy `md_proof.py`, not orchestrator
- ❌ No step toggles, pretty reports, diffs, or artifacts
- ❌ No validation against blessed models
- ❌ No state persistence

**Phase 11 Goal:**
- Wire UI to call `mdp.__main__.run_pipeline()` orchestrator
- Add step toggles (8 steps: mask, prepass-basic, prepass-advanced, scrubber, grammar, detect, apply, fix)
- Display pretty reports and diffs
- Download artifacts
- Persist UI state
- Maintain byte-identical output to CLI

**Next:** Add `get_blessed_models()` helper to `config.py` (PR-0 final task)

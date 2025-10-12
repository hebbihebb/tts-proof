# TTS-Proof Copilot Instructions

## Architecture Overview

TTS-Proof is a **local-first** grammar correction tool with a React/TypeScript frontend and FastAPI backend that processes Markdown files via local LLM servers (LM Studio). The system is designed around **crash-safe chunked processing** with real-time WebSocket updates and **TTS prepass detection**.

### Key Components

- **Backend** (`backend/app.py`): FastAPI server with WebSocket support, imports core logic from `md_proof.py`
  - 20+ REST endpoints including `/api/process/{client_id}`, `/api/prepass`, `/api/models`
  - Pydantic models: `ProcessRequest`, `PrepassRequest`, `JobStatus`, `ChunkPreview`
  - Global `prepass_jobs` dict for job tracking and cancellation
- **Frontend** (`frontend/src/`): React + TypeScript + Tailwind, uses Vite for dev server (6-section grid layout)
  - Component architecture: `FileSelector`, `ModelPicker`, `PrepassControl`, `PromptEditor`, etc.
  - `services/api.ts`: Single API service class with WebSocket management
  - Theme context with localStorage persistence
- **Core Engine** (`md_proof.py`): Standalone CLI tool with chunking, checkpointing, and LM Studio integration
  - Functions: `chunk_paragraphs()`, `mask_urls()`, `extract_between_sentinels()`, `call_lmstudio()`
  - Checkpoint system: `write_ckpt()`, `load_ckpt()`, `paths_for()`
- **Prepass Engine** (`prepass.py`): TTS problem detector that finds stylized text patterns before grammar correction
  - Functions: `detect_tts_problems()`, `run_prepass()`, `inject_prepass_into_grammar_prompt()`
  - Returns JSON with `replacements` array containing `find`, `replace`, `reason` keys
- **Launcher** (`launch.py`): Cross-platform script that starts both frontend and backend servers
  - Auto-checks Python 3.10+, Node.js 16+, installs dependencies, opens browser

## Critical Patterns

### 1. LM Studio Integration

- **Configurable endpoints** via UI - supports LM Studio, KoboldCpp, Oobabooga, TabbyAPI, and custom servers
- **Default**: `http://127.0.0.1:1234/v1` (OpenAI-compatible endpoint)
- Model detection via `/api/models?api_base=<endpoint>` endpoint (backend passes to LM Studio)
- Use **sentinel-based prompting**: wrap text in `<TEXT_TO_CORRECT>...</TEXT_TO_CORRECT>`
  - LLM responses extracted via `extract_between_sentinels(response)`
  - Sentinels defined as `SENTINEL_START` and `SENTINEL_END` constants in `md_proof.py`
- Grammar prompt loaded from `grammar_promt.txt` (note: **intentional typo in filename** - don't "fix" it)
- Prepass prompt loaded from `prepass_prompt.txt`
- **Network support**: Can connect to remote servers on same network (e.g., `http://192.168.x.x:1234/v1`)
- **LLM call pattern**: `call_lmstudio(api_base, model, prompt, text)` returns raw response string

### 2. Text Processing Pipeline

```python
# Pattern: mask URLs → chunk → process → unmask URLs
masked, urls = mask_urls(raw_text)
corrected = extract_between_sentinels(llm_response)
final = unmask_urls(corrected, urls)
```

- **URL masking** prevents LLM from editing links
- **Chunk size**: 8000 chars default (configurable in frontend)
- **Markdown preservation**: Never alter code blocks, syntax, or structure

### 3. WebSocket Communication

- Client generates random `clientId` for connection tracking (`Math.random().toString(36).substring(7)`)
- Backend uses `ConnectionManager` singleton for WebSocket state management
  - `active_connections: Dict[str, WebSocket]` maps client IDs to connections
  - `await manager.send_message(client_id, message_dict)` to send updates
- Message types: `progress`, `completed`, `error`, `chunk_complete`, `paused`
- **Message sources**: `prepass` vs `grammar` to differentiate processing stages
- **Connection pattern**: `/ws/{client_id}` endpoint, auto-cleanup on disconnect
- **Always** include progress percentage and descriptive messages
- Example WebSocket message format:
  ```python
  {
    "type": "progress",
    "source": "grammar",  # or "prepass"
    "progress": 45.5,
    "message": "Processing chunk 5 of 11",
    "chunks_processed": 5,
    "total_chunks": 11
  }
  ```

### 4. TTS Prepass Detection

- **Two-stage processing**: Optional prepass detects TTS problems before grammar correction
- **Pattern detection**: Finds stylized text (`F ʟ ᴀ s ʜ` → `Flash`), hyphenated letters (`U-N-I-T-E-D` → `United`)
- **LLM-based detection**: Uses `detect_tts_problems()` which calls LLM with specialized prompt, returns JSON
  - Expected format: `{"replacements": [{"find": "...", "replace": "...", "reason": "..."}]}`
- **WebSocket streaming**: Real-time progress via `run_prepass_with_websocket()` with job cancellation
- **Report integration**: Prepass results injected into grammar prompt via `inject_prepass_into_grammar_prompt()`
  - Adds replacements to grammar prompt so corrections are applied during main processing
- **Frontend control**: `PrepassControl.tsx` component manages prepass workflow with visual feedback
- **Job tracking**: Global `prepass_jobs` dict for cancellation and status management
  - Keys: client_id → `{"status": "processing" | "cancelled"}`
  - `/api/prepass/cancel` endpoint for user-initiated cancellation

### 5. File Handling Conventions

- **Checkpointing**: `.partial` files for crash recovery (`write_ckpt`/`load_ckpt`)
- **Temporary files**: Use `tempfile` module, cleanup on completion
- **Path patterns**: `paths_for(input_path)` generates `.partial` and output paths
- **Prepass reports**: Stored as JSON with replacement mappings and problem word lists

## Development Workflows

### Quick Start

```bash
python launch.py  # Starts both servers, opens browser
# OR separately:
cd backend && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
cd frontend && npm run dev
```

### Platform-Specific Launchers

- **Windows**: `launch.bat` or `launch.ps1` (PowerShell)
- **Unix/Linux/macOS**: `launch.sh`
- **Cross-platform**: `launch.py` (Python script with dependency checking)

### Testing

- **Backend**: Run `python test_app.py` for API endpoint tests
- **CLI tool**: Standalone `md_proof.py` has comprehensive built-in testing
- **Prepass**: `test_prepass.py` and `test_prepass_integration.py` for TTS detection validation
- **Integration**: `test_integration.py` for end-to-end workflow testing
- **Sentinel parsing**: `test_sentinel.py` for LLM response extraction
- **No frontend tests** currently implemented

### Dependencies

- **Backend**: FastAPI, WebSockets, requests, regex, pydantic (see `backend/requirements.txt`)
- **Frontend**: React 18, TypeScript, Tailwind, Vite, Lucide icons, react-router-dom
- **Python**: 3.10+ required (checked by launcher)
- **Node.js**: 16+ required for frontend build

## Component Patterns

### Frontend State Management

- **No global state library** - use React hooks with prop drilling
- **Theme**: Context-based dark/light mode (`ThemeContext.tsx`)
- **API**: Single service class (`services/api.ts`) with WebSocket management

### UI Conventions

- **Tailwind classes**: Use `dark:` prefixes for theme support
- **Icons**: Lucide React icons only
- **File uploads**: Support drag-and-drop with visual feedback
- **Progress**: Real-time updates via WebSocket, not polling
- **Modal patterns**: Edit buttons open configuration popups (see `EndpointConfig.tsx`)
- **Persistence**: UI state saved to localStorage (endpoints, themes, etc.)
- **6-section grid layout**: Optimized for wide displays with logical workflow organization

### Backend API Design

- **CORS**: Hardcoded Vite dev server origins (`localhost:5173`, `localhost:5174`)
- **Error handling**: Always return structured JSON with error messages
- **File processing**: Stream progress via WebSocket, return final result via HTTP

## Integration Points

### LM Studio Dependencies

- Server **must** be running before starting backend
- Model validation happens at runtime (graceful fallback to defaults)
- Grammar prompt customization through `grammar_promt.txt` file
- **Network support**: Can connect to remote servers on same network

### Cross-Platform Considerations

- Use `pathlib.Path` for file operations
- PowerShell/Bash scripts for Windows/Unix launcher alternatives
- WebSocket connections work across all platforms

## Common Gotchas

1. **Grammar prompt filename**: It's `grammar_promt.txt` (missing 'p' in 'prompt') - **intentional typo, do not rename**
2. **Port conflicts**: Frontend tries 5173, then 5174 if occupied (Vite default behavior)
3. **WebSocket timing**: Backend sends messages before frontend connects - ensure connection established
   - Frontend establishes WS connection via `apiService.connectWebSocket(clientId)`
   - Backend checks `if client_id in manager.active_connections` before sending
4. **Chunk processing**: Always preserve Markdown structure, never edit syntax elements
   - Use `FENCE_RE` regex to detect code blocks, handle as `("code", content)` tuples
   - Mask URLs with `mask_urls()` before processing, unmask with `unmask_urls()` after
5. **Resume functionality**: Check for `.partial` files to continue interrupted processing
   - Generated by `write_ckpt(partial_path, content)` after each chunk
   - Loaded via `load_ckpt(partial_path)` on resume
6. **Sentinel extraction failures**: LLM may not return text within sentinels - handle gracefully
   - `extract_between_sentinels()` returns original text if sentinels not found
7. **CORS restrictions**: Backend only allows `localhost:5173` and `localhost:5174` origins
   - Update `allow_origins` in `app.add_middleware(CORSMiddleware, ...)` for production

## Advanced Testing & Optimization Framework

### Stress Testing System

TTS-Proof includes a comprehensive **stress testing and iterative improvement framework** that has demonstrated **15.0% reference match improvement** through systematic prompt optimization and performance tracking.

#### Core Testing Components

- **`stress_test_system.py`**: Network-based testing with TTS-focused comparison metrics
- **`prompt_evolution_system.py`**: Interactive prompt improvement with version control and A/B testing
- **`tts_stress_test.md`**: Comprehensive TTS problem dataset (30+ categories)
- **`tts_stress_test_reference.md`**: Handcrafted reference for quality measurement
- **`chunk_size_test.py`**: Systematic chunk size optimization testing

#### Network Testing Patterns

```python
# Network server integration pattern:
API_BASE = "http://192.168.8.104:1234/v1"  # Remote LM Studio server
MODEL = "qwen/qwen3-4b-instruct-2507"      # Optimized model selection

# TTS-focused comparison metrics:
def calculate_tts_content_match(original, corrected, reference):
    # Sentence-level comparison with TTS problem focus
    # Returns percentage match for iterative improvement tracking
```

- **Cross-network testing**: Supports remote LM Studio servers for distributed processing
- **Network performance monitoring**: Latency, throughput, and reliability testing
- **Connection validation**: Comprehensive endpoint testing with error recovery

#### Iterative Improvement Methodology

**6-Iteration Optimization Cycle** achieved measurable quality improvements:

1. **Baseline establishment** (0.0% reference match)
2. **TTS-focused refinement** (JSON compliance, specificity improvements)
3. **Grammar integration** (prepass + grammar correction pipeline)
4. **Performance optimization** (chunk size analysis, processing efficiency)
5. **Network validation** (cross-network reliability testing)
6. **Quality measurement** (**15.0% reference match achievement**)

#### Performance Tracking Infrastructure

```python
# Comprehensive metrics collection:
class IterationMetrics:
    reference_match_percentage: float
    processing_time_seconds: float
    chunks_processed: int
    tts_problems_detected: int
    tts_problems_fixed: int
    network_latency_ms: float
```

- **Reference comparison**: TTS-focused content matching with sentence-level analysis
- **Performance benchmarking**: Processing speed, network performance, quality metrics
- **Historical tracking**: Iteration progression with performance trend analysis
- **Success criteria**: Measurable improvement targets and validation frameworks

#### TTS Problem Categorization

**30+ TTS Problem Categories** systematically tested:

- **Stylized Unicode** (`Bʏ Mʏ Rᴇsᴏʟᴠᴇ!` → `By My Resolve!`)
- **Letter spacing** (`F ʟ ᴀ s ʜ` → `Flash`)
- **Hyphenated sequences** (`U-N-I-T-E-D` → `United`)
- **Chat log formats** (`[Username]: message` → `Username: message`)
- **Onomatopoeia** (`AAAAAAA` → `Ahh`)
- **System text** (code blocks, timestamps, technical data)
- **Emotional fragmentation** (stuttered speech, ellipses normalization)

### Integration with Main Application

#### Functional Parity Analysis

Current **Web UI capabilities** vs **Stress Testing achievements**:

| Feature                  | Web UI   | Stress Testing    | Integration Priority |
| ------------------------ | -------- | ----------------- | -------------------- |
| **Network endpoints**    | ✅ Full  | ✅ Full           | None (compatible)    |
| **Reference comparison** | ❌ None  | ✅ Advanced       | **Critical**         |
| **Performance metrics**  | ❌ Basic | ✅ Comprehensive  | **Critical**         |
| **Iteration support**    | ❌ None  | ✅ Full framework | **High**             |
| **TTS categorization**   | ❌ None  | ✅ Specialized    | **High**             |

#### Integration Roadmap

**Phase 1: Core Quality Measurement**

- Reference comparison system integration
- Performance analytics dashboard
- TTS-focused result analysis

**Phase 2: Advanced Testing**

- Stress testing dataset integration
- Network testing enhancement
- Comprehensive test runner

**Phase 3: Long-term Optimization**

- Iteration support framework
- Historical performance tracking
- Advanced analytics and reporting

### Testing Best Practices

#### Network Testing

```python
# Always test network connectivity before processing:
async def validate_network_endpoint(api_base: str, model: str):
    """Comprehensive network validation with performance metrics."""
    # Test models endpoint, chat completions, measure latency
    # Return connection quality assessment and recommendations
```

#### Reference Validation

```python
# Use handcrafted references for quality measurement:
def compare_with_reference(processed: str, reference: str) -> float:
    """TTS-focused comparison returning percentage match."""
    # Sentence-level comparison with TTS problem emphasis
    # Returns 0.0-100.0 percentage for iterative tracking
```

#### Iterative Development

- **Baseline establishment**: Always establish 0% baseline before optimization
- **Systematic iteration**: Version control prompts, track performance progression
- **Network validation**: Test across network configurations and server types
- **Quality measurement**: Use reference comparison for objective improvement tracking
- **Documentation**: Maintain iteration logs with detailed performance analysis

### Advanced Architecture Insights

#### Prompt Engineering Patterns

**Sentinel-based processing** with **TTS-focused instructions**:

```txt
<TEXT_TO_CORRECT>
[problematic TTS content]
</TEXT_TO_CORRECT>

Find stylized Unicode letters (ʟ, ᴀ, ᴇ, etc.) and normalize to standard English.
Focus on TTS readability while preserving meaning and Markdown structure.
```

#### Performance Optimization

- **Chunk size optimization**: 8000 chars optimal for TTS processing (validated through testing)
- **Network considerations**: Batch processing for remote servers, connection pooling
- **Memory management**: Efficient processing of large documents with checkpointing
- **Error recovery**: Graceful handling of network interruptions and model failures

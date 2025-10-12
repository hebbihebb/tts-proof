# TTS-Proof Copilot Instructions

## Architecture Overview

TTS-Proof is a **local-first** grammar correction tool with a React/TypeScript frontend and FastAPI backend that processes Markdown files via local LLM servers (LM Studio). The system is designed around **crash-safe chunked processing** with real-time WebSocket updates and **TTS prepass detection**.

**Primary Use Case**: Processing fiction EPUB files (converted to Markdown) for TTS readability - targeting amateur fiction, poor translations, and problematic formatting. Users primarily interact via the web UI for one-shot processing workflows.

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
- **MDP Package** (`mdp/`): Modular text processing pipeline (Phase 1-3 implementation, Phase 5 planned)
  - **`markdown_adapter.py`**: AST-based masking via regex fallback - extracts text spans, protects code/links
  - **`masking.py`**: Sentinel-based content masking with stable token generation
  - **`prepass_basic.py`**: Unicode normalization, spaced letter joining, hyphenation healing (Phase 2)
  - **`prepass_advanced.py`**: Casing normalization, punctuation collapse, ellipsis standardization
  - **`scrubber.py`**: Block detection and removal - author notes, navigation, link farms (Phase 3)
  - **`appendix.py`**: Formats scrubbed blocks into organized appendix documents
  - **`grammar_assist.py`**: Optional deterministic grammar corrections with offline engine (Phase 5 - planned)
  - **`config.py`**: YAML-based configuration with comprehensive defaults for all processing stages
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

**Three-Phase Architecture**:

**Phase 1: Markdown Masking** (`mdp/markdown_adapter.py` + `mdp/masking.py`)

```python
# Extract text-only spans, protect code/links/math
from mdp.markdown_adapter import mask_protected, unmask, extract_text_spans
masked_text, mask_table = mask_protected(markdown_text)
# Process only text, never structural elements
restored = unmask(processed_text, mask_table)
```

- **Regex-based protection**: Code blocks, inline code, links, images, HTML, math
- **Stable sentinels**: `__MASKED_0__`, `__MASKED_1__`, etc. for deterministic reconstruction
- **Text span extraction**: `extract_text_spans()` returns list of safe-to-edit regions

**Phase 2: Unicode & Spacing Normalization** (`mdp/prepass_basic.py`)

```python
# Deterministic, no LLM required - runs in <0.1s
from mdp.prepass_basic import normalize_text_nodes
result, stats = normalize_text_nodes(text, config)
# Stats: {'control_chars_stripped': 4, 'spaced_words_joined': 3, 'hyphenation_healed': 1}
```

- **Unicode cleanup**: ZWSP, bidi controls, soft hyphens, BOM removal
- **Spaced letter joining**: `S p a c e d` → `Spaced` (≥4 letters, smart separators)
- **Hyphenation healing**: `cre-\nate` → `create` at line breaks
- **Punctuation normalization**: Configurable quotes/dashes/ellipsis handling

**Phase 3: Content Scrubbing** (`mdp/scrubber.py` + `mdp/appendix.py`)

```python
# Block-level detection for author notes, navigation, promos
from mdp.scrubber import scrub_text, BlockCandidate
from mdp.appendix import format_appendix
cleaned, candidates, stats = scrub_text(text, config, dry_run=False)
appendix_doc = format_appendix(candidates, source_file="input.md")
```

- **Link density analysis**: Detects link farms via character percentage
- **Keyword matching**: Navigation, promos, watermarks (configurable whitelist)
- **Position awareness**: Edge blocks (top/bottom 6) vs middle blocks
- **Appendix generation**: Preserves scrubbed content for manual restoration

**Phase 5: Optional Grammar Assist** (`mdp/grammar_assist.py` - planned)

```python
# Conservative, deterministic grammar corrections (offline, no LLM)
from mdp.grammar_assist import apply_grammar_corrections
corrected, stats = apply_grammar_corrections(text, config, mask_table)
# Stats: {'typos_fixed': 3, 'spacing_fixed': 5, 'punctuation_fixed': 2, 'rejected': 1}
```

- **Offline engine**: Uses LanguageTool or similar (no network dependency)
- **Safe mode only**: Whitelist categories - `TYPOS`, `PUNCTUATION`, `CASING`, `SPACING`, `SIMPLE_AGREEMENT`
- **Non-interactive**: Auto-applies safe corrections, zero prompts
- **Text-node scoped**: Only edits text nodes from Phase 1 AST, respects masks
- **Structural validation**: Post-edit checks ensure mask counts, link/backtick parity unchanged
- **Deterministic**: Running twice produces identical output
- **Configurable locale**: Defaults to `en`, supports multi-language (e.g., Icelandic for fiction)
- **CLI integration**: `--steps mask,prepass-basic,prepass-advanced,grammar` for pipeline chaining
- **Toggleable**: `grammar_assist.enabled: true` in `md_proof.yaml`

**Legacy URL Masking** (`md_proof.py` - still used by main engine)

```python
# Pattern: mask URLs → chunk → process → unmask URLs
masked, urls = mask_urls(raw_text)
corrected = extract_between_sentinels(llm_response)
final = unmask_urls(corrected, urls)
```

- **Chunk size**: 8000 chars default (configurable in frontend, validated through testing)
- **Markdown preservation**: Always use Phase 1 masking for new features

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
- **Directory organization** (see `DIRECTORY_STRUCTURE.md`):
  - `/testing/` - All tests (unit, stress, data)
  - `/docs/` - Analysis reports, guides
  - `/config/` - LM Studio presets, YAML configs
  - `/prompts/` - Current, upgraded, and versioned prompts
  - `/mdp/` - Modular processing pipeline (Phase 1-3)

### 6. Configuration System

**YAML-based with comprehensive defaults** (`mdp/config.py`):

```python
from mdp.config import load_config
config = load_config("custom_config.yaml")  # or None for defaults
```

**Key config sections**:

- **`unicode_form`**: NFKC normalization (default)
- **`scrubber.categories`**: Enable/disable detection of author notes, navigation, promos, link farms
- **`scrubber.whitelist`**: Protect specific headings ("Translator's Cultural Notes") or domains
- **`prepass_advanced.casing`**: Shouting normalization with acronym whitelist (NASA, GPU, JSON, etc.)
- **`prepass_advanced.punctuation`**: Ellipsis style, quote style, sentence spacing
- **All settings have sensible defaults** - config file optional

**Typical fiction EPUB configuration**:

```yaml
# Optimized for amateur fiction, poor translations, TTS readability
unicode_form: "NFKC"
scrubber:
  enabled: true
  categories:
    authors_notes: true # Remove author notes at chapter ends
    navigation: true # Remove "Next Chapter" links
    promos_ads_social: true # Remove Patreon/Discord promos
    link_farms: true # Remove link collections
prepass_advanced:
  casing:
    normalize_shouting: true # Fix ALL CAPS dialogue
  punctuation:
    ellipsis: "three-dots" # Standardize ellipsis for TTS
    collapse_runs: true # Fix "!!!!!" → "!"
```

## Git Workflow & Branching Strategy

**Branch Structure**:

- **`main`**: Production-ready code, protected branch (no direct commits)
- **`dev`**: Integration branch for features, all PRs target here
- **`feat/*`**: Feature branches created from `dev`

**Feature Development Pattern** (required for Phase 5 and beyond):

```bash
# Start new feature
git checkout dev && git pull
git checkout -b feat/phase5-grammar-assist

# Work on feature (commit frequently)
git add . && git commit -m "feat: implement grammar_assist.py"

# Push and open PR into dev
git push -u origin feat/phase5-grammar-assist
# Open PR: feat/phase5-grammar-assist → dev (NOT main)
```

**PR Requirements**:

- **Target**: Always `dev`, never `main`
- **Title**: Clear, descriptive (e.g., "feat: Add Phase 5 Grammar Assist")
- **Checklist**: Include acceptance criteria in PR description
- **Size**: Keep PRs small and reviewable
- **Merge**: Squash commits on merge to keep history clean

**Critical Rules**:

- ❌ **Never commit directly to `main`**
- ❌ **Never open PR into `main`** (always target `dev`)
- ✅ **Always branch from `dev`** for new features
- ✅ **Use descriptive branch names** (`feat/`, `fix/`, `docs/`, etc.)

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

**Pytest Configuration** (`pytest.ini`) - **Fast tests by default**:

```bash
pytest                    # Run fast tests only (33 tests in <1s)
pytest -m ""              # Run ALL tests including LLM/slow/network
pytest -m "llm"           # Run only LLM-dependent tests
pytest -m "slow"          # Run only slow tests
pytest -m "network"       # Run only network tests
pytest -vv                # Verbose output
pytest --cov=mdp          # With coverage report
```

**Test Markers** (defined in `pytest.ini`):

- `@pytest.mark.llm` - Requires LLM server (skipped by default)
- `@pytest.mark.slow` - Takes >5 seconds (skipped by default)
- `@pytest.mark.network` - Requires network access (skipped by default)

**VS Code Tasks**: 8 pre-configured pytest tasks via Command Palette → "Run Task"

- **"Pytest: Fast Tests (Default)"** ← Use this during development
- "Pytest: All Tests (Including LLM)"
- "Pytest: LLM Tests Only"
- "Pytest: With Coverage"

**Test Structure** (`testing/`):

- **`unit_tests/`**: Fast unit tests (no LLM required)
  - `test_prepass_basic.py` - Phase 2 unicode/spacing normalization
  - `test_scrubber.py` - Phase 3 block detection
  - `test_prepass_integration.py` - Full prepass workflow
  - `test_sentinel.py` - LLM response extraction
- **`stress_tests/`**: Advanced testing framework with A/B comparison
- **`test_data/`**: Sample inputs, references, stress test datasets
- **Backend**: `python backend/test_app.py` for API endpoint tests
- **No frontend tests** currently implemented

### Dependencies

- **Backend**: FastAPI, WebSockets, requests, regex, pydantic (see `backend/requirements.txt`)
- **Frontend**: React 18, TypeScript, Tailwind, Vite, Lucide icons, react-router-dom
- **Python**: 3.10+ required (checked by launcher)
- **Node.js**: 16+ required for frontend build

**Note**: Underlying libraries may be replaced in the future for efficiency or simplicity (e.g., Bun instead of Node.js for faster installs, alternative bundlers for single-click launching). Avoid tight coupling to specific build tools or runtimes where possible.

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
   - **New features**: Use Phase 1 masking via `mdp.markdown_adapter.mask_protected()`
   - **Legacy code**: Use `FENCE_RE` regex + `mask_urls()` before processing, unmask with `unmask_urls()` after
5. **Resume functionality**: Check for `.partial` files to continue interrupted processing
   - Generated by `write_ckpt(partial_path, content)` after each chunk
   - Loaded via `load_ckpt(partial_path)` on resume
6. **Sentinel extraction failures**: LLM may not return text within sentinels - handle gracefully
   - `extract_between_sentinels()` returns original text if sentinels not found
7. **CORS restrictions**: Backend only allows `localhost:5173` and `localhost:5174` origins
   - Update `allow_origins` in `app.add_middleware(CORSMiddleware, ...)` for production
8. **Test markers**: Always use `pytest` alone for fast feedback - don't run slow/LLM tests during development
   - Fast tests run in <1s, provide 33 tests of core functionality
   - Use `pytest -m "llm"` only when testing LLM integration features
9. **Module imports**: `pytest.ini` sets `pythonpath = .` - import mdp package directly: `from mdp.scrubber import scrub_text`

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

# TTS-Proof Copilot Instructions

## Architecture Overview

TTS-Proof is a **local-first** grammar correction tool with a React/TypeScript frontend and FastAPI backend that processes Markdown files via local LLM servers (LM Studio). The system is designed around **crash-safe chunked processing** with real-time WebSocket updates and **TTS prepass detection**.

### Key Components

- **Backend** (`backend/app.py`): FastAPI server with WebSocket support, imports core logic from `md_proof.py`
- **Frontend** (`frontend/src/`): React + TypeScript + Tailwind, uses Vite for dev server (6-section grid layout)
- **Core Engine** (`md_proof.py`): Standalone CLI tool with chunking, checkpointing, and LM Studio integration
- **Prepass Engine** (`prepass.py`): TTS problem detector that finds stylized text patterns before grammar correction
- **Launcher** (`launch.py`): Cross-platform script that starts both frontend and backend servers

## Critical Patterns

### 1. LM Studio Integration

- **Configurable endpoints** via UI - supports LM Studio, KoboldCpp, Oobabooga, TabbyAPI, and custom servers
- **Default**: `http://127.0.0.1:1234/v1` (OpenAI-compatible endpoint)
- Model detection via `/models?api_base=<endpoint>` with endpoint parameter support
- Use **sentinel-based prompting**: wrap text in `<TEXT_TO_CORRECT>...</TEXT_TO_CORRECT>`
- Grammar prompt loaded from `grammar_promt.txt` (note: intentional typo in filename)
- **Network support**: Can connect to remote servers on same network

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
- Message types: `progress`, `completed`, `error`, `chunk_complete`, `paused`
- **Message sources**: `prepass` vs `grammar` to differentiate processing stages
- **Connection pattern**: `/ws/{client_id}` endpoint, auto-cleanup on disconnect
- **Always** include progress percentage and descriptive messages

### 4. TTS Prepass Detection

- **Two-stage processing**: Optional prepass detects TTS problems before grammar correction
- **Pattern detection**: Finds stylized text (`F ʟ ᴀ s ʜ` → `Flash`), hyphenated letters (`U-N-I-T-E-D` → `United`)
- **WebSocket streaming**: Real-time progress via `run_prepass_with_websocket()` with job cancellation
- **Report integration**: Prepass results injected into grammar prompt via `inject_prepass_into_grammar_prompt()`
- **Frontend control**: `PrepassControl.tsx` component manages prepass workflow with visual feedback
- **Job tracking**: Global `prepass_jobs` dict for cancellation and status management

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

1. **Grammar prompt filename**: It's `grammar_promt.txt` (missing 'p' in 'prompt')
2. **Port conflicts**: Frontend tries 5173, then 5174 if occupied
3. **WebSocket timing**: Backend sends messages before frontend connects - ensure connection established
4. **Chunk processing**: Always preserve Markdown structure, never edit syntax elements
5. **Resume functionality**: Check for `.partial` files to continue interrupted processing

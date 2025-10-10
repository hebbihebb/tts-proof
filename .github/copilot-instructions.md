# TTS-Proof Copilot Instructions

## Architecture Overview

TTS-Proof is a **local-first** grammar correction tool with a React/TypeScript frontend and FastAPI backend that processes Markdown files via local LLM servers (LM Studio). The system is designed around **crash-safe chunked processing** with real-time WebSocket updates.

### Key Components

- **Backend** (`backend/app.py`): FastAPI server with WebSocket support, imports core logic from `md_proof.py`
- **Frontend** (`frontend/src/`): React + TypeScript + Tailwind, uses Vite for dev server
- **Core Engine** (`md_proof.py`): Standalone CLI tool with chunking, checkpointing, and LM Studio integration
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

- Client generates random `clientId` for connection tracking
- Backend uses `ConnectionManager` singleton for WebSocket state
- Message types: `progress`, `completed`, `error`, `chunk_complete`, `paused`
- **Always** include progress percentage and descriptive messages

### 4. File Handling Conventions

- **Checkpointing**: `.partial` files for crash recovery (`write_ckpt`/`load_ckpt`)
- **Temporary files**: Use `tempfile` module, cleanup on completion
- **Path patterns**: `paths_for(input_path)` generates `.partial` and output paths

## Development Workflows

### Quick Start

```bash
python launch.py  # Starts both servers, opens browser
# OR separately:
cd backend && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
cd frontend && npm run dev
```

### Testing

- Backend: Run `python test_app.py` for API endpoint tests
- No frontend tests currently (CLI tool has comprehensive testing in `md_proof.py`)

### Dependencies

- **Backend**: FastAPI, WebSockets, requests (see `backend/requirements.txt`)
- **Frontend**: React 18, TypeScript, Tailwind, Vite, Lucide icons

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

### Backend API Design

- **CORS**: Hardcoded Vite dev server origins (`localhost:5173`, `localhost:5174`)
- **Error handling**: Always return structured JSON with error messages
- **File processing**: Stream progress via WebSocket, return final result via HTTP

## Integration Points

### LM Studio Dependencies

- Server **must** be running before starting backend
- Model validation happens at runtime (graceful fallback to defaults)
- Grammar prompt customization through `grammar_promt.txt` file

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

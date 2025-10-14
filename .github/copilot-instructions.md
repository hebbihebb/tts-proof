def calculate_tts_content_match(original, corrected, reference):

# TTS-Proof Copilot Instructions

## Project Overview

TTS-Proof is a local-first Markdown grammar correction and TTS-readability tool for fiction, with a React/TypeScript frontend and FastAPI backend. It processes Markdown (often from EPUBs) using local LLMs (LM Studio) and a modular Python pipeline. The system is designed for crash-safe, chunked processing with real-time WebSocket updates and a TTS-specific prepass.

## Key Architecture & Patterns

- **Backend** (`backend/app.py`): FastAPI server, WebSocket progress, imports core logic from `md_proof.py`. Key endpoints: `/api/process/{client_id}`, `/api/prepass`, `/api/models`. Uses Pydantic models and a global `prepass_jobs` dict for job tracking/cancellation.
- **Frontend** (`frontend/src/`): React + TypeScript + Tailwind, Vite dev server. Uses a 6-section grid layout, no global state library (prop drilling/hooks only). API calls and WebSocket handled in `services/api.ts`.
- **Core Engine** (`md_proof.py`): CLI tool for chunking, checkpointing, and LLM integration. Key functions: `chunk_paragraphs`, `mask_urls`, `extract_between_sentinels`, `call_lmstudio`. Checkpointing via `.partial` files.
- **Prepass Engine** (`prepass.py`): Detects TTS-specific problems (stylized Unicode, spaced/hyphenated letters) before grammar correction. Returns JSON with `replacements` array.
- **MDP Package** (`mdp/`): Modular pipeline for masking, normalization, scrubbing, and (planned) deterministic grammar assist. Use `mask_protected`/`unmask` for Markdown-safe edits. Configurable via YAML (`mdp/config.py`).
- **Launcher** (`launch.py`): Cross-platform script to start both servers and open browser. Checks Python/Node versions and installs dependencies.

## Essential Conventions

- **Prompt files**: Grammar prompt is `grammar_promt.txt` (intentional typo, do not rename). Prepass prompt is `prepass_prompt.txt`.
- **Sentinel-based LLM calls**: Always wrap text in `<TEXT_TO_CORRECT>...</TEXT_TO_CORRECT>`. Extract LLM output with `extract_between_sentinels()`.
- **Masking**: Always use Phase 1 masking (`mdp/markdown_adapter.py`) to protect Markdown structure. Never edit code/links/math directly.
- **Chunking**: Default chunk size is 8000 chars (configurable). Checkpoint after each chunk with `.partial` files for crash recovery.
- **WebSocket progress**: All processing progress is streamed via WebSocket (`/ws/{client_id}`), with message types: `progress`, `completed`, `error`, `chunk_complete`, `paused`. Always include progress percentage and descriptive messages.
- **Prepass integration**: Prepass results are injected into the grammar prompt for main processing. Prepass jobs tracked in `prepass_jobs` dict.
- **Testing**: Use `pytest` for fast tests (default), with markers for `llm`, `slow`, `network`. VS Code tasks are preconfigured for all test types. Test data in `testing/test_data/`.
- **Branching**: All PRs target `dev` (never `main`). Feature branches use `feat/*` from `dev`. Squash commits on merge.

## Key Files & Directories

- `md_proof.py`, `prepass.py`: Main engines for processing and TTS prepass
- `mdp/`: Modular pipeline (masking, normalization, scrubbing, config)
- `backend/app.py`: FastAPI server, WebSocket manager
- `frontend/src/`: React UI, API/WebSocket logic in `services/api.ts`
- `prompts/`, `config/`: Prompt files, YAML configs, LM Studio presets
- `testing/`: Unit, stress, and data tests

## Common Gotchas

1. **Prompt filename**: `grammar_promt.txt` (intentional typo)
2. **Masking**: Always use `mask_protected` for new features; legacy code may use `mask_urls`
3. **WebSocket timing**: Ensure frontend connects before backend sends progress
4. **CORS**: Backend only allows `localhost:5173`/`5174` by default
5. **Resume**: Processing resumes from `.partial` files if present
6. **Test markers**: Use `pytest` alone for fast feedback; use `-m "llm"` for LLM-dependent tests

## Example Patterns

**Masking and Processing:**

```python
from mdp.markdown_adapter import mask_protected, unmask
masked, mask_table = mask_protected(md_text)
# ...process masked...
restored = unmask(processed, mask_table)
```

**LLM Call:**

```python
response = call_lmstudio(api_base, model, prompt, text)
result = extract_between_sentinels(response)
```

**WebSocket Progress Message:**

```python
{
  "type": "progress",
  "source": "grammar",  # or "prepass"
  "progress": 45.5,
  "message": "Processing chunk 5 of 11"
}
```

---

If any section is unclear or missing, please provide feedback for further refinement.

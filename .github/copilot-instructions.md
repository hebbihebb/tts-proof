# TTS-Proof Copilot Instructions

Local-first Markdown grammar correction and TTS-readability tool. React/TypeScript frontend + FastAPI backend orchestrating an 8-phase Python pipeline with LM Studio integration.

## Architecture Overview

**Data Flow**: `React (5174) ←WebSocket→ FastAPI (8000) → MDP Pipeline → LM Studio (1234)`

**8-Phase Pipeline** (`python -m mdp input.md --steps mask,prepass-basic,prepass-advanced,scrubber,grammar,detect,apply,fix`):

1. **Mask** (`mdp/markdown_adapter.py`) - Protect code/links/HTML with `__MASKED_N__` sentinels
2. **Prepass Basic** (`mdp/prepass_basic.py`) - Unicode normalization, spacing fixes
3. **Prepass Advanced** (`mdp/prepass_advanced.py`) - Casing, punctuation, ellipsis
4. **Scrubber** (`mdp/scrubber.py`) - Remove author notes, navigation (optional)
5. **Grammar Assist** (`mdp/grammar_assist.py`) - LanguageTool offline corrections (optional, legacy)
6. **Detect** (`detector/`) - TTS problem detection with tiny model → JSON plan
7. **Apply** (`apply/`) - Execute plan with 7 structural validators (mask parity, backtick parity, bracket balance, link sanity, fence parity, token guard, length delta <1%)
8. **Fix** (`fixer/`) - Light polish with larger model (optional)

**Run Artifacts** (`~/.mdp/runs/<run-id>/`): `original.md`, `output.md`, `report.json`, `decision-log.ndjson`

## Critical Patterns

### Masking (Phase 1)

```python
from mdp.markdown_adapter import mask_protected, unmask
masked, mask_table = mask_protected(md_text)
# ...process masked (never touch __MASKED_N__ sentinels)...
restored = unmask(processed, mask_table)
```

**Never** edit code blocks, links, HTML, or math directly. Always mask first.

### LLM Calls (Legacy `md_proof.py`)

```python
from md_proof import call_lmstudio, extract_between_sentinels
response = call_lmstudio(api_base, model, prompt, text)
corrected = extract_between_sentinels(response)  # Expects <TEXT_TO_CORRECT>...</TEXT_TO_CORRECT>
```

### WebSocket Progress (Backend → Frontend)

```python
await manager.send_message(client_id, {
    "type": "progress",
    "source": "detect",  # mask|prepass-basic|prepass-advanced|scrubber|detect|apply|fix
    "progress": 67.5,
    "message": "Processing chunk 3 of 8"
})
```

Message types: `progress`, `completed`, `error`, `chunk_complete`, `paused`

### Structural Validation (Phase 7)

```python
from apply.validate import validate_all
is_valid, error = validate_all(original_text, edited_text, config)
if not is_valid:
    # HARD STOP - reject entire edit
```

7 validators enforce: mask parity, backtick count unchanged, brackets balanced, `](` pairs unchanged, triple-backtick fences even, no new Markdown tokens (asterisks, underscores, brackets, parentheses, backticks, tildes, angle brackets), length growth ≤1%.

## File Conventions

| Pattern            | Location                              | Notes                                                                    |
| ------------------ | ------------------------------------- | ------------------------------------------------------------------------ |
| **Prompts**        | `prompts/grammar_promt.txt`           | Intentional typo - DO NOT RENAME                                         |
|                    | `prompts/prepass_prompt.txt`          | Detector system prompt                                                   |
| **Config**         | `mdp/config.py`                       | Pipeline defaults (chunk size, validators)                               |
|                    | `config/lmstudio_preset_qwen3_*.json` | Model routing presets                                                    |
| **Tests**          | `pytest` (default: fast only)         | Markers: `@pytest.mark.llm`, `@pytest.mark.slow`, `@pytest.mark.network` |
| **Frontend State** | `frontend/src/state/appStore.tsx`     | Centralized React context (no Redux/Zustand)                             |
| **API Service**    | `frontend/src/services/api.ts`        | REST + WebSocket client                                                  |

## Development Workflow

**Launch**: `python launch.py` (starts both servers + opens browser)  
**Backend**: `python backend/app.py` (port 8000)  
**Frontend**: `cd frontend && npm run dev` (port 5174)  
**CLI**: `python -m mdp input.md --steps detect,apply -o output.md --report-pretty`

**Testing**:

- Fast tests (default): `pytest`
- Include LLM tests: `pytest -m ""`
- Only LLM tests: `pytest -m "llm"`
- VS Code tasks preconfigured for all combinations

**Git Workflow**:

- Branch from `dev` (never `main`)
- Feature branches: `feat/*`
- PRs → `dev`, squash on merge
- `main` is stable release branch

## Common Gotchas

1. **`grammar_promt.txt` typo is intentional** - hardcoded in `backend/app.py`
2. **Mask before editing** - Use `mask_protected()`, not legacy `mask_urls()`
3. **WebSocket timing** - Frontend must connect before backend sends messages
4. **CORS restriction** - Backend only allows `localhost:5173`/`5174`
5. **Acronym whitelist** - Loaded from `mdp/config.py` at startup via `tie_breaker.set_acronym_whitelist()`
6. **Run artifacts path** - `~/.mdp/runs/` by default, override with `MDP_RUNS_DIR` env var
7. **URL encoding** - Always use `encodeURIComponent()` for `run_id` and artifact names in frontend

## Key Endpoints

| Endpoint                           | Method    | Purpose                                   |
| ---------------------------------- | --------- | ----------------------------------------- |
| `/api/process`                     | POST      | Run full pipeline (multipart file upload) |
| `/api/runs`                        | GET       | List all runs with summaries              |
| `/api/runs/{id}/artifacts`         | GET       | List artifacts for run                    |
| `/api/runs/{id}/artifacts/{name}`  | GET       | Download specific artifact                |
| `/api/runs/{id}/artifacts/archive` | GET       | Download all artifacts as ZIP             |
| `/ws/{client_id}`                  | WebSocket | Real-time progress stream                 |

## Example: Adding a New Phase

1. Create module in `mdp/` (e.g., `my_phase.py`)
2. Implement function returning `(processed_text, stats_dict)`
3. Add step to `mdp/__main__.py` in `run_pipeline()`
4. Update `backend/app.py` if WebSocket progress needed
5. Add unit tests in `testing/unit_tests/test_my_phase.py`
6. Document in `docs/phases/` if major feature

## Debugging

- **Backend logs**: Console output from `uvicorn` (INFO level)
- **Frontend logs**: Browser console + Network tab
- **LM Studio**: Check `http://localhost:1234/v1/models` for connectivity
- **Run artifacts**: `~/.mdp/runs/<run-id>/decision-log.ndjson` has tie-breaker decisions
- **Test data**: `testing/test_data/` has realistic samples

---

**Current Phase**: Phase 14B complete (single-column UI refactor merged to `dev`)  
**See**: `SESSION_STATUS.md` for detailed current state, `ROADMAP.md` for next steps

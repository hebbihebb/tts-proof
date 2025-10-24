# TTS-Proof v2 Copilot Instructions

Local-first Markdown grammar correction and TTS-readability tool. **Single-file Python implementation** (`md_processor.py`) with CLI and planned Tkinter GUI. No web UI, no servers.

## Architecture Overview

**v2 Data Flow**: `CLI/GUI → md_processor.py → LM Studio (1234)`

**Core Pipeline** (`python md_processor.py --input file.md --steps mask,detect,apply`):

1. **Mask** - Protect code fences, inline code, links, images, HTML blocks, math with `__MASKED_N__` sentinels
2. **Prepass Basic** - Unicode normalization (NFKC), spacing fixes, zero-width characters
3. **Prepass Advanced** - Casing normalization, punctuation runs, ellipsis standardization
4. **Scrubber** - Remove author notes, navigation (stub, not implemented)
5. **Grammar Assist** - LanguageTool offline corrections (legacy, not in v2)
6. **Detect** - TTS problem detection with tiny model → JSON plan (list of {find, replace, reason})
7. **Apply** - Execute plan with 7 structural validators (mask parity, backtick parity, bracket balance, link sanity, fence parity, token guard, length delta <1%)
8. **Fix** - Light polish with larger model (stub, not implemented)

**Implementation**: All phases in single file `md_processor.py` (~1000 lines). No external dependencies except `requests` (optional, for LLM calls).

## Critical Patterns

### Masking (Phase 1)

```python
from md_processor import mask_protected, unmask
masked, mask_table = mask_protected(md_text)
# ...process masked (never touch __MASKED_N__ sentinels)...
restored = unmask(processed, mask_table)
```

**Never** edit code blocks, links, HTML, or math directly. Always mask first. Uses regex-based detection (no AST parsing).

### LLM Calls (OpenAI-compatible)

```python
from md_processor import LLMClient
client = LLMClient(api_base='http://127.0.0.1:1234/v1', model='qwen3-detector')
response = client.call_llm(prompt, text)
# Response wrapped in <TEXT_TO_CORRECT>...</TEXT_TO_CORRECT> sentinels
corrected = client.extract_corrected(response)
```

No WebSocket, no async. Simple synchronous HTTP calls via `requests` library.

### Progress Callbacks

```python
def my_callback(phase: str, progress: float, message: str):
    print(f"[{phase}] {progress:.1f}% - {message}")

result, stats = run_pipeline(text, steps=['mask', 'detect'], progress_callback=my_callback)
```

Currently only logging-based (stub implementation). Callbacks planned for Tkinter GUI.

### Structural Validation (Phase 7)

```python
from md_processor import validate_all
is_valid, error = validate_all(original_text, edited_text, mask_table)
if not is_valid:
    # HARD STOP - reject entire edit
    raise ValueError(f"Validation failed: {error}")
```

7 validators enforce: mask parity (same count), backtick count unchanged, brackets balanced, `](` pairs unchanged, triple-backtick fences even, no new Markdown tokens (asterisks, underscores, brackets, parentheses, backticks, tildes, angle brackets), length growth ≤1%.

## File Conventions

| Pattern       | Location                              | Notes                                                                    |
| ------------- | ------------------------------------- | ------------------------------------------------------------------------ |
| **Core Code** | `md_processor.py`                     | Single-file implementation (~1000 lines)                                 |
| **Prompts**   | Embedded in `md_processor.py`         | `GRAMMAR_PROMPT`, `DETECTOR_PROMPT` constants (no external files)        |
| **Config**    | Embedded in `md_processor.py`         | `DEFAULT_CONFIG` dict (chunk size, validators, model names)              |
|               | `config/lmstudio_preset_qwen3_*.json` | Model routing presets (optional)                                         |
|               | `config/acronyms.txt`                 | Acronym whitelist for tie-breaker logic                                  |
| **Tests**     | `pytest` (default: fast only)         | Markers: `@pytest.mark.llm`, `@pytest.mark.slow`, `@pytest.mark.network` |
| **Pipeline**  | `mdp/` directory                      | Old modular implementation (reference only, being phased out)            |
| **GUI**       | `gui.py` (planned)                    | Tkinter GUI (~300 lines, not yet implemented)                            |

## Development Workflow

**CLI Usage**:

```bash
# Basic pipeline
python md_processor.py --input file.md --output out.md --steps mask,detect,apply

# With custom endpoint/model
python md_processor.py --input file.md --steps mask,detect,apply \
  --endpoint http://127.0.0.1:1234/v1 --model qwen3-detector

# Verbose output with stats
python md_processor.py --input file.md --output out.md --steps mask,prepass-basic,prepass-advanced --verbose

# JSON stats export
python md_processor.py --input file.md --output out.md --stats stats.json
```

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

1. **Embedded prompts** - No external prompt files in v2. Edit `GRAMMAR_PROMPT` and `DETECTOR_PROMPT` constants in `md_processor.py`
2. **Mask before editing** - Always use `mask_protected()` before any text processing. Never touch `__MASKED_N__` sentinels
3. **Single-file imports** - Import everything from `md_processor`: `from md_processor import mask_protected, run_pipeline, LLMClient`
4. **No async/await** - All functions are synchronous. Use `requests.post()` not `aiohttp`
5. **Acronym whitelist** - Load from `config/acronyms.txt` at startup (optional feature)
6. **Sentinel wrapping** - LLM responses must be wrapped in `<TEXT_TO_CORRECT>...</TEXT_TO_CORRECT>` tags
7. **Validator strictness** - 7 validators will reject edits that change structure. Length delta must be <1%

## Key Functions

| Function               | Purpose                                                  |
| ---------------------- | -------------------------------------------------------- |
| `mask_protected()`     | Protect Markdown structures, return (masked_text, table) |
| `unmask()`             | Restore masked content from table                        |
| `prepass_basic()`      | Unicode normalization, spacing fixes                     |
| `prepass_advanced()`   | Casing, punctuation, ellipsis normalization              |
| `detect_problems()`    | LLM-based TTS problem detection → JSON plan              |
| `apply_plan()`         | Apply replacements with structural validation            |
| `validate_all()`       | Run all 7 validators, return (is_valid, error_message)   |
| `LLMClient.call_llm()` | OpenAI-compatible API call with sentinel wrapping        |
| `run_pipeline()`       | Orchestrate phases, return (processed_text, stats_dict)  |
| `main()`               | CLI entry point with argparse                            |

## Example: Adding a New Phase

1. Add phase function to `md_processor.py`:

   ```python
   def my_new_phase(text: str, config: dict) -> Tuple[str, dict]:
       """Process text for my feature."""
       # ... implementation ...
       stats = {'items_processed': count}
       return processed_text, stats
   ```

2. Register in `PHASE_MAP` dict:

   ```python
   PHASE_MAP = {
       'mask': mask_protected,
       'my-phase': my_new_phase,  # Add here
       # ...
   }
   ```

3. Add to CLI help in `main()`:

   ```python
   parser.add_argument('--steps', help='mask,prepass-basic,my-phase,detect,apply')
   ```

4. Update `run_pipeline()` if special handling needed

5. Add unit tests in `testing/unit_tests/test_md_processor.py`

6. Update `V2_IMPLEMENTATION_STATUS.md` with completion status

## Debugging

- **CLI logs**: Use `--verbose` flag for detailed output
- **Stats**: Use `--stats stats.json` to export phase-by-phase metrics
- **LM Studio**: Check `http://localhost:1234/v1/models` for connectivity (curl or browser)
- **Test data**: `testing/test_data/` has realistic samples (unicode_stylized.md, detector_smoke_test.md, etc.)
- **Validation errors**: Check which of 7 validators failed (mask_parity, backtick_parity, bracket_balance, link_sanity, fence_parity, token_guard, length_delta)

**Quick smoke test**:

```bash
python md_processor.py --input testing/test_data/detector_smoke_test.md --output /tmp/out.md --steps mask,prepass-basic,prepass-advanced --verbose
```

---

**Current Phase**: v2 Core Implementation (Phase 1 complete)  
**See**: `V2_IMPLEMENTATION_STATUS.md` for current state, `V2_REFACTOR_PLAN.md` for roadmap, `V2_ARCHITECTURE_COMPARISON.md` for v1 vs v2 details

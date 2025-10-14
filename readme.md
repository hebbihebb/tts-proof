# TTS-Proof

**Local-first Markdown grammar correction and TTS-readability tool for fiction**

Process Markdown files (often from EPUBs) using local LLMs and a modular Python pipeline. Features crash-safe chunked processing, real-time WebSocket updates, and TTS-specific problem detection.

---

## Quick Start

**Requirements**: Python 3.10+, Node.js 16+, [LM Studio](https://lmstudio.ai/) with local server

**Launch**:
```bash
python launch.py  # Opens browser to http://localhost:5174
```

**Use**: Upload Markdown → Configure preset → Run pipeline → Download results

---

## What It Does

Cleans up documents with grammar/spelling errors, poor OCR/translation formatting, TTS-problematic patterns (spaced letters, stylized Unicode), and removes author notes/navigation/promos.

**Use cases**: Ebook cleanup, web scraping, AI text polishing, translation post-processing  
**Privacy**: Everything runs locally—no data leaves your machine

---

## Features

- **React + TypeScript Web UI** with real-time WebSocket progress
- **FastAPI backend** orchestrating modular Python pipeline
- **8-phase processing**: Masking → Normalization → Scrubbing → Grammar → Detection → Application → Fixing
- **Crash-safe chunking** with `.partial` file checkpointing
- **Run history & artifacts** browser with diff viewer
- **Configurable presets** for model/server selection
- **Dark/light theme** toggle

---

## Architecture

```
React Frontend (5174) ←─ WebSocket ─→ FastAPI (8000) → mdp/ → LM Studio (1234)
```

**Pipeline Phases**:
1. **Mask** - Protect Markdown structure (code, links, HTML)
2. **Prepass Basic** - Unicode normalization, spacing fixes
3. **Prepass Advanced** - Casing, punctuation, units *(optional)*
4. **Scrubber** - Remove author notes, navigation *(optional)*
5. **Grammar Assist** - LanguageTool offline corrections *(optional, legacy)*
6. **Detect** - TTS problem detection with tiny model
7. **Apply** - Plan application with 7 structural validators
8. **Fix** - Light polish with larger model *(optional)*

**Runs stored** in `runs/<run-id>/artifacts/`: `original.md`, `output.md`, `report.json`, `decision-log.ndjson`

---

## Usage

### Web UI
```bash
python launch.py
# Upload file → Configure → Run → Download
```

### CLI
```bash
# Full pipeline
python -m mdp input.md --steps mask,detect,apply -o output.md --report-pretty

# Specific phases
python -m mdp input.md --steps mask,prepass-basic,prepass-advanced -o clean.md
```

### API
```bash
curl http://127.0.0.1:8000/api/runs  # List runs
curl -OJ "http://127.0.0.1:8000/api/runs/<ID>/artifacts/<FILE>"  # Download
```

---

## Configuration

**Pipeline Steps**: Configure in Web UI or via CLI `--steps`

**Config Files**:
- `config/lmstudio_preset_qwen3_grammar.json` - LM Studio preset
- `prompts/grammar_promt.txt` - Grammar prompt *(typo intentional)*
- `prompts/prepass_prompt.txt` - Detector prompt
- `mdp/config.py` - Pipeline configuration

**Acronym Whitelist**: Edit in `mdp/config.py` → `prepass_advanced.casing.acronym_whitelist`

---

## Phase Documentation

See `docs/phases/` for detailed guides. Quick reference:

- **Phase 1** (Mask): Protect code blocks, links → `markdown_adapter.py`
- **Phase 2** (Prepass): Unicode/spacing cleanup → `prepass_basic.py`, `prepass_advanced.py`
- **Phase 3** (Scrub): Remove boilerplate → `scrubber.py`
- **Phase 5** (Grammar): LanguageTool *(legacy)* → `grammar_assist.py`
- **Phase 6** (Detect): TTS detection → `detector/detector.py`
- **Phase 7** (Apply): Plan application + validators → `apply/applier.py`
- **Phase 8** (Fix): Light polish → `fixer/fixer.py`

**Validators** (Phase 7): Mask parity, Backtick parity, Bracket balance, Link sanity, Fence parity, Token guard, Length delta (<1%)

---

## Development

**Structure**:
```
tts-proof/
├── backend/app.py          # FastAPI server
├── frontend/src/           # React UI (AppNew.tsx = single-column layout)
├── mdp/                    # Core pipeline modules
├── detector/               # Phase 6 detection
├── apply/                  # Phase 7 application
├── fixer/                  # Phase 8 polish
├── prompts/                # LLM prompts
├── config/                 # Presets & configs
└── testing/                # 217+ unit tests
```

**Testing**:
```bash
pytest                # Fast tests (no LLM)
pytest -m "llm"       # LLM-dependent tests
pytest -m "slow"      # Slow tests
```

**Git Workflow**: PRs target `dev` (never `main`), feature branches `feat/*` from `dev`, squash commits on merge

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Models not loading | Ensure LM Studio on port 1234 |
| WebSocket failed | Check backend on port 8000 |
| Frontend won't start | Run `npm install` in `frontend/` |
| Processing stuck | Restart LM Studio |

---

## Status

**Completed**: Phases 1-8, Web UI, Presets, Run History  
**Current**: Phase 14B single-column UI refactor merged to `dev`  
**Next**: UI polish (model selection, prepass integration), real-world EPUB testing

See `SESSION_STATUS.md` for current development state.

---

## License

Personal utility - use as you wish. No warranty provided.

**Contributing**: Issues, feature requests, and PRs welcome!

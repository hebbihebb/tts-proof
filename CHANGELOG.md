# Changelog

All notable changes to TTS-Proof will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - Phase 6 & 7 (Detector + Applier)

**Phase 6: Detector System** (October 2025)
- Tiny model (Qwen2.5-1.5B) generates JSON replacement plans for TTS problems
- Sentence-level chunking with overlap window (600 chars, 50 char overlap)
- Comprehensive guardrails: forbidden chars, length deltas, budget limits, deduplication
- Network server support with connectivity checks (exit code 2 on unreachable)
- Skip conditions: URLs, code-ish content, mostly uppercase text
- CLI flags: `--plan`, `--print-plan`, `--detector-dump`
- Test coverage: 67 tests for schema, chunking, client, integration, golden samples

**Phase 7: Plan Applier & Structural Validator** (October 2025)
- Deterministic, idempotent plan application with literal matching
- Left-to-right non-overlapping edit engine
- 7 structural validators (hard stops):
  1. Mask parity - `__MASKED_N__` sentinels preserved
  2. Backtick parity - inline code & fences unchanged
  3. Bracket balance - `[]`, `()`, `{}` remain balanced
  4. Link sanity - `](` pairs preserved
  5. Fence parity - ` ``` ` count remains even
  6. Markdown token guard - no new `*`, `_`, `[`, `]`, `(`, `)`, `` ` ``, `~`, `<`, `>`
  7. Length delta budget - 1% max file growth (configurable)
- CLI flags: `--dry-run`, `--print-diff`, `--reject-dir`
- Exit codes: 3 (validation fail), 4 (plan parse error), 5 (masked edit)
- Test coverage: 81 tests for matcher, applier, validator
- Maximal munch overlap prevention with stable sorting

**Combined Workflow:**
```bash
# Full detect → apply pipeline
python -m mdp input.md --steps detect,apply -o output.md

# Dry-run with rejection handling
python -m mdp input.md --steps detect,apply --dry-run --reject-dir rejected/
```

**Test Status:** 217 tests passing (81 Phase 7 + 67 Phase 6 + 69 existing)

### Changed

- Extended `mdp/config.py` with `detector` and `apply` sections
- Updated `mdp/__main__.py` with `detect` and `apply` steps
- Exit code 2 now indicates detector model server unreachable

## [Phase 5 Complete] - October 2025

### Added - Grammar Assist (Offline Engine)

- Optional deterministic grammar corrections via LanguageTool
- Safe mode only: whitelisted categories (TYPOS, PUNCTUATION, CASING, SPACING, SIMPLE_AGREEMENT)
- Non-interactive, auto-applies safe corrections
- Text-node scoped, respects Phase 1 masks
- Structural validation: post-edit checks ensure mask counts, link/backtick parity unchanged
- Configurable locale support (default: `en`, supports multi-language)
- CLI integration: `--steps mask,prepass-basic,prepass-advanced,grammar`
- Toggleable via `grammar_assist.enabled: true` in config

## [Phase 3 Complete] - October 2025

### Added - Content Scrubbing

- Block-level detection for author notes, navigation, promos, link farms
- Link density analysis with configurable thresholds
- Position awareness: edge blocks vs middle blocks (edge bias protection)
- Keyword matching with whitelist support
- Appendix generation for scrubbed content (preserves for manual restoration)
- Dry-run mode for candidate preview
- CLI flags: `--steps scrub`, `--scrub-dryrun`, `--appendix`

## [Phase 2 Complete] - October 2025

### Added - Prepass Normalization

**Basic Prepass** (`prepass_basic.py`):
- Unicode normalization (NFKC by default)
- Zero-width character removal (ZWSP, bidi controls, soft hyphens)
- Spaced letter joining (`S p a c e d` → `Spaced`, ≥4 letters)
- Hyphenation healing (`cre-\nate` → `create` at line breaks)

**Advanced Prepass** (`prepass_advanced.py`):
- Casing normalization (shouting with acronym whitelist: NASA, GPU, JSON, etc.)
- Punctuation collapse (`!!!!` → `!`, configurable policy)
- Ellipsis standardization (three dots vs Unicode)
- Quote style normalization (straight vs curly)
- Numbers/units spacing (`23 %` → `23%`)
- Time format transformation (`9:00 AM` → `9:00 a.m.`)
- Optional inline footnote removal

**Features:**
- Deterministic (no LLM required, <0.1s runtime)
- Idempotent (second pass = zero changes)
- Markdown-safe (text nodes only)
- Comprehensive configuration via YAML

## [Phase 1 Complete] - October 2025

### Added - AST-based Markdown Masking

- Regex-based protection for code blocks, inline code, links, images, HTML, math
- Stable sentinels: `__MASKED_0__`, `__MASKED_1__` for deterministic reconstruction
- Text span extraction: `extract_text_spans()` returns safe-to-edit regions
- Round-trip preservation: mask → process → unmask maintains structure
- CLI: `--steps mask,unmask` for testing

## [Initial Release] - 2024

### Added

- **Web Interface**: React + TypeScript frontend with 6-section grid layout
- **FastAPI Backend**: WebSocket support for real-time progress
- **LLM Integration**: LM Studio, KoboldCpp, Oobabooga, TabbyAPI support
- **Network Support**: Connect to local or remote servers
- **TTS Prepass**: Detection of TTS-problematic words
- **Chunking System**: Configurable chunk sizes with checkpointing
- **Crash Recovery**: Automatic resume from `.partial` files
- **Theme Support**: Dark/light mode toggle
- **File Upload**: Drag & drop with instant preview
- **Model Detection**: Auto-discovery from LM Studio server
- **Prompt Customization**: Live editing with persistence

### Security

- Local-first architecture (no internet required)
- All processing runs on user's machine
- Network connections only to user-specified LLM servers

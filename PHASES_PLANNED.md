
# Phase 0 — Project Hygiene & Safety Nets

**Feature Description**  
Create a safe playground to iterate, test, and roll back changes.

**Suggested Approach**

- Work on a `dev` branch with a tiny CLI harness and sample “hell” inputs.
    
- Centralize toggles in a single config file.
    

**Tasks**

1. Repo setup: `dev` branch, `tests/hell/` with 3–5 nasty samples; empty `expected/` folder.
    
2. CLI skeleton: run pipeline steps (no-op for now), print timing.
    
3. Config file: load flags (we’ll populate later), echo active settings.
    

**Acceptance**

- `dev` branch exists; CLI runs a no-op; config is read and echoed.
    

**Deliverables**

- `cli.py` (or equivalent), `tests/hell/`, `md_proof.yaml`.
    

---

# Phase 1 — [[1. Markdown AST & Masking]]

**Feature Description**  
Operate strictly on text nodes while protecting Markdown syntax (code, links, HTML, math, etc.).

**Suggested Approach**

- Parse Markdown into a node tree and track byte offsets for text leaf nodes.
    
- Replace protected regions with stable sentinels; support full round-trip.
    

**Tasks**

1. AST extraction: list of text spans with offsets/types.
    
2. Masking: replace protected regions with `{{MASK_<TYPE>_<n>}}`.
    
3. Unmasking: restore to byte-identical original.
    
4. CLI: `--steps mask` / `--steps unmask` (round-trip test).
    

**Acceptance**

- Mask→unmask returns an identical file; counts for masked regions are correct.
    

**Deliverables**

- AST utilities, mask/unmask module, unit tests.
    

**Risks/Checks**

- Off-by-one offsets; ensure non-UTF8 edge cases are covered in tests.
    

---

# Phase 2 — Pre-Pass 2.0 (A): [[2. Unicode & Spacing Normalization]]

**Feature Description**  
Eliminate Unicode gremlins and spacing artifacts that sabotage TTS and confuse LLMs.

**Suggested Approach**

- Normalize text nodes (not Markdown) using a standard Unicode normalization plus targeted stripping of zero-widths and bidi controls.
    
- Add rules for inter-letter spacing, comma/dot-separated letters, and soft hyphen line wraps.
    

**Tasks**

1. Unicode normalization & cleanup (keep accents in real words).
    
2. Inter-letter join: collapse `S p a c e d` / `E, x, a, m` to words (≥3 letters).
    
3. Hyphenation heal at line breaks: `cre-\nate` → `create`.
    
4. CLI: `--steps prepass-basic`.
    

**Acceptance**

- Golden tests pass; Markdown unchanged; sample hell files visibly improve readability.
    

**Deliverables**

- Normalization module + tests.
    

**Risks/Checks**

- Avoid merging legitimate spaced lettering in stylized titles (make rule thresholds configurable).
    

---

# Phase 3 — Boilerplate/[[3. Notes Scrubber]] (Optional & Reversible)

**Feature Description**  
Optionally identify and remove author notes, navigation junk, promos/social blocks, and link farms—without harming story text.

**Suggested Approach**

- Heuristics with configurable thresholds and strong bias to top/bottom sections.
    
- Option to move removed blocks to an Appendix file.
    

**Tasks**

1. Heuristic detectors: headings/prefixes (A/N, Author’s Note), promo keywords, prev/next, link-density.
    
2. Edge bias: operate mainly on first/last N blocks; escalate only on high-confidence matches.
    
3. Appendix writer and `--dry-run` preview.
    
4. Config toggles per category (authors_notes, translators_notes, navigation, promos_ads_social, link_farms).
    

**Acceptance**

- Dry-run lists candidates; real run removes or moves; Markdown remains valid.
    
- False positives minimal on hell samples.
    

**Deliverables**

- Scrubber module, Appendix output, tests.
    

**Risks/Checks**

- In-story epistolary notes; provide a whitelist and easy undo in diffs.
    

---

# Phase 4 — Pre-Pass 2.0 (B): [[4. Casing, Punctuation, Numbers]]/Units

**Feature Description**  
Finish deterministic cleanup: casing normalization, punctuation policy, unit/time spacing, optional footnote marker removal.

**Suggested Approach**

- Use configurable acronym whitelist and protected lexicon (onomatopoeia, fandom terms, Icelandic names).
    
- Keep rules conservative and toggled in config.
    

**Tasks**

1. Acronym whitelist + protected lexicon file.
    
2. Punctuation policy: excessive runs, ellipsis, quotes/apostrophes.
    
3. Numbers/units/time spacing; consistent `%`, `°C/°F`, `a.m./p.m.`.
    
4. Optional footnote marker removal.
    

**Acceptance**

- Policies apply only to text nodes; protected tokens preserved; tests cover variants.
    

**Deliverables**

- Policy rules, lexicon YAML, tests.
    

**Risks/Checks**

- Don’t title-case proper stylizations; allow opt-out per publisher/ruleset.
    

---

# Phase 5 — [[5. Optional Grammar Assist]] (Deterministic First)

**Feature Description**  
Integrate a conservative grammar and spacing pass _before_ any LLM polish.

**Suggested Approach**

- Use a mainstream grammar checker in “safe suggestions” mode on text nodes only.
    
- Accept only spacing and low-risk punctuation fixes.
    

**Tasks**

1. Wrapper around grammar tool with category filters.
    
2. Apply to text nodes; reject suggestions that touch masked counts.
    
3. Config toggle to enable/disable.
    

**Acceptance**

- No Markdown drift; measurable low-risk fixes on hell files.
    

**Deliverables**

- Grammar wrapper + tests.
    

**Risks/Checks**

- Locale handling (en/is); expose language in config.
    

---

# Phase 6 — [[6. Detector (Tiny Model → JSON Plan)]]

**Feature Description**  
Have a small model propose a minimal replacement plan for stubborn patterns the deterministic pass can’t cover.

**Suggested Approach**

- Strict JSON schema, small context, short exemplars, and tight output limits.
    
- Run only on sentences or short nodes to avoid drift.
    

**Tasks**

1. Client wrapper with timeouts/retries; JSON hard-validation.
    
2. Schema: `{find, replace, reason}`; drop invalid entries.
    
3. Chunking policy for long nodes; merge plans.
    

**Acceptance**

- Plans parse; empty plan returned when nothing to fix; latency predictable.
    

**Deliverables**

- Detector client, schema validator, tests.
    

**Risks/Checks**

- Over-eager replacements; keep reason codes and per-reason caps.
    

---

# Phase 7 — [[7. Plan Applier & Structural Validator]]

**Feature Description**  
Apply the plan deterministically and reject any change that could break structure.

**Suggested Approach**

- Anchored literal replacements with tight matching; then run structural checks.
    

**Tasks**

1. Minimal diff applier (exact spans preferred).
    
2. Structural validator: backtick counts, link counts, bracket/paren balance, mask counts.
    
3. CLI: `--steps detect,apply` and `--print-plan`.
    

**Acceptance**

- Unsafe plans are discarded; safe plans change only intended text.
    

**Deliverables**

- Applier + validator modules, tests.
    

**Risks/Checks**

- Locale quotes and nested punctuation—include those in tests.
    

---

# Phase 8 — [[8. Fixer (Bigger Model → Light Polish on Text Nodes)]]

**Status**: ✅ **COMPLETE** (Completed: October 13, 2025)

**Feature Description**  
A careful, minimal polish pass on already-sanitized text nodes.

**Implementation Summary**

- Conservative post-correction polish using Qwen2.5-1.5B-Instruct
- Multiple safety guardrails: forbidden tokens, length limits (20% node, 5% file)
- Structural validation reuses Phase 7 validators
- Exit codes: 0 (success), 2 (unreachable), 3 (validation failure)

**Completed Tasks**

1. ✅ Created `fixer/` module: `client.py`, `prompt.py`, `fixer.py`, `guards.py` (735 lines)
2. ✅ Conservative prompt template with locale support
3. ✅ Safety validators: forbidden tokens, length limits, fail-safe to original
4. ✅ CLI integration in `mdp/__main__.py`: `--steps fix` step
5. ✅ Extended `mdp/config.py` with comprehensive fixer section

**Test Results**

- ✅ 55 unit tests (100% passing, ~0.6s execution)
- ✅ Zero LLM dependency for testing (all mocked)
- ✅ Full suite: 272/272 tests passing
- ✅ Test coverage: guards (28), logic (16), client (11)

**Deliverables**

- ✅ `fixer/` module with client, guardrails, comprehensive tests
- ✅ Integration with `mdp/__main__.py` pipeline
- ✅ Unit tests in `testing/unit_tests/test_fixer_*.py`
- ✅ Documentation: `docs/PHASE8_COMPLETION_REPORT.md`

**Acceptance Criteria Met**

- ✅ No chatter; plain text only; failed outputs safely discarded
- ✅ Exit code `2` for model unreachable (consistent with Phase 6 detector)
- ✅ Exit code `3` for validation failure
- ✅ All outputs pass Phase 7 structural validation
- ✅ Operates only on text nodes, never touches Markdown structure

**Branch**: `feat/phase8-fixer` → `dev` (PR #10, merged October 13, 2025)
    

---

# Phase 9 — Reassembly, Unmasking & Final Sanity

**Status**: ✅ **ALREADY COMPLETE** (Integrated in Phases 1-7)

**Feature Description**  
Splice edited text back into the AST, unmask protected regions, and verify final Markdown.

**Implementation Status**

This phase is **already implemented** across existing modules:

1. ✅ **Unmasking**: `mdp/markdown_adapter.py` - `unmask()` function
2. ✅ **Reassembly**: `mdp/masking.py` - stable sentinel restoration
3. ✅ **Final Sanity**: `apply/validate.py` - 7 structural validators:
   - Mask parity, backtick parity, bracket balance
   - Link sanity, fence parity, markdown token guard
   - Length delta budget
4. ✅ **Rejection Handling**: `mdp/__main__.py` writes `.rejected.md` on validation failure
5. ✅ **Exit Codes**: Already defined (0=success, 3=validation failure)

**Testing**

- ✅ 81 tests in `testing/unit_tests/test_apply_validator.py`
- ✅ Integration tests for full pipeline in Phase 7

**Deliverables**

- All components already exist and are production-ready
- No new work required for this phase
    

---

# Phase 10 — Enhanced Reporting & Scoring

**Status**: 🔧 **ENHANCEMENT** (Estimated: 2-3 hours)

**Feature Description**  
Visibility: what changed, how much, and where we still fail. Human-readable output formats.

**Current Status**

**Already Implemented**:
- ✅ Per-phase stats dictionaries (all phases return stats)
- ✅ `combined_stats` aggregation in `mdp/__main__.py`
- ✅ `--report <file.json>` flag outputs JSON
- ✅ Counters for each step included in stats

**What's Missing**:
- ❌ Human-readable table format
- ❌ Pretty-printed console output
- ❌ Multiple output formats (JSON, table, markdown)
- ❌ Per-node diff visualization (beyond file-level)

**Tasks**

1. Create `report/formatter.py` module for pretty-printing
2. Add format options: `--report-format [json|table|markdown]`
3. Console table output with color coding (optional)
4. Buckets for: unicode, spacing, hyphenation, casing, grammar, scrubbed blocks, detected/applied/fixed, rejected nodes
5. Per-phase summary with percentage improvements

**Acceptance**

- Reports generated in multiple formats; numbers add up; zero when step disabled
- Console output is human-readable and visually organized
- Existing JSON format remains unchanged for backward compatibility

**Deliverables**

- `report/formatter.py` module
- Enhanced `--report` flag with format options
- Sample output files for each format

**Risks/Checks**

- Keep PII and URLs safe in logs; consider hashing if needed
- Ensure large diffs are truncated in console output
    

---

# Phase 14 — Web UI Integration

**Status**: 🚀 **CRITICAL PATH** (Estimated: 6-8 hours)

**Feature Description**  
Migrate Web UI from legacy `md_proof.py`/`prepass.py` to new `mdp` pipeline (Phases 1-8). Enable all phase features in the React frontend.

**Why Now (Before Phase 11)**

- ✅ Core pipeline complete and tested (217+ tests, Phases 1-8)
- ✅ Users can test and provide feedback immediately
- ✅ Phase 11 presets can be designed **with Web UI in mind** (dropdowns, toggles)
- ✅ Avoids massive technical debt at end of project
- ✅ CLI and Web UI stay in sync throughout development

**Current Web UI Status**

- ❌ Still uses legacy `md_proof.py` + `prepass.py` code
- ❌ Only exposes grammar correction (not Phases 1-8)
- ❌ No access to detector/applier/fixer workflow
- ✅ Has WebSocket infrastructure for real-time updates
- ✅ Has configuration UI patterns (endpoints, prompts)

**Tasks**

**Backend (`backend/app.py`)**:
1. Replace `md_proof.py` calls with `subprocess` running `python -m mdp`
2. Add `/api/config/phases` endpoint - return available phases and defaults
3. Add `/api/config/save` endpoint - save user's phase configuration to temp YAML
4. Update `/api/process` to accept `steps` array and pass to `mdp` CLI
5. Parse `mdp` stdout for per-phase progress and stream via WebSocket
6. Return per-phase stats from `--report` JSON in response

**Frontend (`frontend/src/components/`)**:
1. Create `PhaseSelector.tsx` - checkboxes for each phase with dependencies
2. Create `PhaseConfigPanel.tsx` - expandable config for each phase
3. Update `ProcessingView.tsx` - show per-phase progress (not just overall %)
4. Update `ResultsPanel.tsx` - expandable per-phase statistics
5. Add preset dropdown (preparation for Phase 11)

**Integration Points**:
- Reuse existing WebSocket infrastructure (`ConnectionManager`)
- Reuse existing file upload patterns (`FileSelector.tsx`)
- Extend existing config editing patterns (`EndpointConfig.tsx`)

**Acceptance**

- [ ] Web UI can execute all Phase 1-8 steps
- [ ] Each phase has configuration UI (where applicable)
- [ ] Real-time progress shows current phase and percentage
- [ ] Results display per-phase statistics (collapsible sections)
- [ ] Backend uses `python -m mdp` exclusively (legacy code removed)
- [ ] All existing Web UI features still work (backward compatibility)

**Deliverables**

- Updated `backend/app.py` with mdp integration
- New frontend components for phase selection and configuration
- Migration guide documenting changes
- Updated Web UI screenshots

**Risks/Checks**

- Subprocess management: ensure proper cleanup on cancellation
- Progress parsing: handle varying log formats from different phases
- Configuration validation: ensure valid YAML generated from UI inputs

---

# Phase 11 — Presets & Performance

**Status**: 📦 **AFTER WEB UI** (Estimated: 3-4 hours)

**Feature Description**  
Make it fast and predictable on mid-tier GPUs/CPUs (e.g., RTX 2070 + 4-core CPU). Provide ready-to-use presets.

**Suggested Approach**

- Provide model/pipeline presets (detector vs fixer), moderate context windows, streaming enabled
- Process text nodes in small batches sized to VRAM headroom
- **Design presets with Web UI dropdowns in mind** (now that UI is integrated)

**Tasks**

1. Create preset files in `config/`: `fiction_epub.yaml`, `technical_docs.yaml`, `fast_pass.yaml`
2. Preset loader in `mdp/config.py` with safe defaults and overrides
3. Web UI dropdown for preset selection (easy now that Phase 14 is complete!)
4. Concurrency queue: batch size tuned to keep VRAM stable
5. VRAM estimation and warnings

**Acceptance**

- No OOM; steady throughput; presets switch cleanly in both CLI and Web UI
- Users can select presets from dropdown in Web UI
- Each preset documented with use case and hardware requirements

**Deliverables**

- Preset YAML files in `config/`
- Preset loader and CLI flag `--preset <name>`
- Web UI preset dropdown integration
- Concurrency controls

**Risks/Checks**

- Competing GPU jobs; add a pre-run VRAM check and warn
    

---

# Phase 12 — (Optional) Tie-Breaker Classifier for Scrubber

**Feature Description**  
Reduce false positives for boilerplate removal when heuristics are uncertain.

**Suggested Approach**

- Tiny classifier that labels blocks `{type, confidence}`; only consulted near thresholds.
    

**Tasks**

1. Integrate classifier behind a config gate.
    
2. Use it only when heuristic score is borderline; log decisions.
    

**Acceptance**

- Fewer scrubber mistakes on hell samples; no regressions elsewhere.
    

**Deliverables**

- Classifier wrapper, tests, logs.
    

**Risks/Checks**

- Keep outputs JSON-only, minimal token budgets.
    

---

# Phase 13 — Packaging, Docs & Demos

**Feature Description**  
Ship a usable tool with a 5-minute demo path and rollback instructions.

**Suggested Approach**

- Clean README, Makefile (or task runner), example commands, troubleshooting table.
    

**Tasks**

1. Make targets: `test`, `fmt`, `demo`.
    
2. README: quickstart, config reference, common pitfalls.
    
3. Version tag and changelog entry.
    

**Acceptance**

- `make demo` processes `tests/hell/` and emits report; docs link to examples.
    

**Deliverables**

- Updated README, Makefile/tasks, tagged release.
    

---

## ✅ Execution Status

### Completed Phases
- ✅ **Phase 0**: Project hygiene (dev branch, testing infrastructure)
- ✅ **Phase 1**: Markdown AST & Masking (`mdp/markdown_adapter.py` + `mdp/masking.py`)
- ✅ **Phase 2**: Unicode & Spacing Normalization (`mdp/prepass_basic.py`)
- ✅ **Phase 3**: Notes Scrubber (`mdp/scrubber.py` + `mdp/appendix.py`)
- ✅ **Phase 4**: Casing, Punctuation, Numbers (`mdp/prepass_advanced.py`)
- ✅ **Phase 5**: Grammar Assist (`mdp/grammar_assist.py`)
- ✅ **Phase 6**: Detector (`detector/` - tiny model → JSON plans)
- ✅ **Phase 7**: Plan Applier & Validator (`apply/` - 7 structural validators)
- ✅ **Phase 9**: Reassembly & Validation (integrated in Phases 1-7)

**Test Coverage**: 217 tests passing

### Active Development (Plan A - Early Web UI Integration)

**Immediate** (This Week):
1. 🎯 **Phase 8**: Fixer (4-6 hours)
2. 🔧 **Phase 10**: Enhanced Reporting (2-3 hours)

**Critical Path** (Next Week):
3. 🚀 **Phase 14**: Web UI Integration (6-8 hours) ← **Do BEFORE Phase 11**

**Polish & Performance** (Week 3+):
4. 📦 **Phase 11**: Presets & Performance (3-4 hours) - easier now with Web UI integrated!
5. 🤖 **Phase 12**: (Optional) Tie-Breaker Classifier
6. 📖 **Phase 13**: Packaging, Docs & Demos

### Pipeline Execution Order (Runtime)

```bash
# Full pipeline command
python -m mdp input.md --steps mask,prepass-basic,prepass-advanced,scrubber,grammar,detect,apply,fix -o output.md

# Step order at runtime:
# 1. mask           → protect Markdown structure
# 2. scrubber (opt) → remove boilerplate
# 3. prepass-basic  → Unicode normalization
# 4. prepass-advanced → casing/punctuation
# 5. grammar (opt)  → LanguageTool corrections
# 6. detect         → tiny model finds problems
# 7. apply          → apply plan with validation
# 8. fixer          → bigger model polish
# 9. (unmask)       → restore Markdown (automatic)
# 10. (validate)    → structural checks (automatic)
# 11. (report)      → statistics output (automatic)
```

## Work Rhythm (per task)

- Small diff → unit tests → run on one hell file → inspect `--diff` → adjust thresholds → commit
- Follow git workflow: `git checkout dev && git pull && git checkout -b feat/phaseN-name`
- Keep PRs small; always target `dev` branch (never `main`)
- Squash merge to keep history clean

## 🎯 Ready for Phase 8!

All foundations are in place. Phase 8 (Fixer) is next, followed by enhanced reporting, then **Web UI integration** to make everything accessible to users. After that, presets and final polish!
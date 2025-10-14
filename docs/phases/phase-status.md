# Phase Status Overview (October 14, 2025)

## Completed Phases
- **Phase 0 – Project Hygiene & Safety Nets** · Foundation repo hygiene, CLI harness, and shared configuration baseline. See [`phase-plan-analysis.md`](./phase-plan-analysis.md).
- **Phase 1 – Markdown AST & Masking** · Markdown-safe text node extraction and masking utilities in `mdp/markdown_adapter.py` and `mdp/masking.py`. Documented in [`phase-plan-analysis.md`](./phase-plan-analysis.md).
- **Phase 2 – Prepass Basic** · Unicode normalization and spacing cleanup (`mdp/prepass_basic.py`). Notes in [`phase-plan-analysis.md`](./phase-plan-analysis.md).
- **Phase 3 – Notes Scrubber** · Optional boilerplate/scrubber pipeline with appendix support (`mdp/scrubber.py`, `mdp/appendix.py`). Summary: [`phase-plan-analysis.md`](./phase-plan-analysis.md).
- **Phase 4 – Prepass Advanced** · Casing, punctuation, and numeric normalization (`mdp/prepass_advanced.py`). Reference: [`phase-plan-analysis.md`](./phase-plan-analysis.md).
- **Phase 5 – Grammar Assist** · Deterministic LanguageTool integration before LLM polish. Completion record in [`phase05-complete.md`](./phase05-complete.md) and [`phase05-final-summary.md`](./phase05-final-summary.md).
- **Phase 6 – Detector** · Tiny-model plan generation with strict JSON schema (`detector/`). Planning and delivery notes in [`phase06-pr-description.md`](./phase06-pr-description.md) and [`phase06-progress.md`](./phase06-progress.md).
- **Phase 7 – Plan Applier & Validator** · Deterministic plan application with structural validation (`apply/`). PR notes in [`phase07-pr-description.md`](./phase07-pr-description.md).
- **Phase 8 – Fixer** · Light-weight LLM polish with guardrails (`fixer/`). Implementation guidance retained in [`phase08-implementation-guide.md`](./phase08-implementation-guide.md) and completion report [`PHASE8_COMPLETION_REPORT.md`](../PHASE8_COMPLETION_REPORT.md).
- **Phase 9 – Reassembly & Validation** · Already covered by existing unmasking and validator modules (`mdp/markdown_adapter.py`, `apply/validate.py`). Additional commentary in [`phase-plan-analysis.md`](./phase-plan-analysis.md).
- **Phase 10 – Enhanced Reporting** · Pretty-print CLI reports (`report/pretty.py`, `--report-pretty`). Details in [`phase10-complete.md`](./phase10-complete.md) and [`phase10-pr-description.md`](./phase10-pr-description.md).
- **Phase 11 – Web UI Integration** · React/TypeScript control surface with run history and artifact browser (`backend/app.py`, `frontend/src/*`). Status log in [`phase11-status.md`](./phase11-status.md) and supporting PR notes (`phase11-pr1-*`, `phase11-pr2-*`).

## Upcoming & Deferred Phases
- **Phase 12 – Optional Scrubber Tie-Breaker** · Lightweight classifier to confirm or reject scrubber candidates. Not started.
- **Phase 13 – Packaging, Docs & Demos** · Distribution hardening, end-to-end guides, and onboarding assets. Not started.
- **Phase 14 – Advanced Presets & Performance** · Preset bundles plus throughput tuning (naming retained for continuity with older plan). Scheduling TBD.
- **Backlog Ideas** · Batch automation, expanded real-world corpus benchmarking, and CI/CD relaunch; track in `ROADMAP.md` alongside the main backlog.

> Quick reference: all detailed historical notes now live under `docs/phases/`. Use this file as the high-level index before drilling into phase-specific write-ups.

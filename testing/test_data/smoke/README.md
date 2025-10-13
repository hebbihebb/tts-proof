# Smoke Test Data

This directory contains crafted test data for smoke testing the detector+applier workflow.

## danger_plan.json

A **deliberately invalid** replacement plan designed to trigger structural validation failures. Used to verify that the applier correctly rejects dangerous edits that would corrupt Markdown structure.

### What Makes It "Dangerous"

The plan contains replacements that violate structural integrity:

1. **Adds markdown tokens**: `Flash` → `*Flash*` (introduces new asterisks for emphasis)
2. **Adds link syntax**: `United` → `[United](https://example.com)` (introduces brackets and parentheses)
3. **Adds code backticks**: `Resolve` → `` `Resolve` `` (introduces inline code markup)

All of these edits would be rejected by Phase 7's structural validators, specifically:
- **Markdown token guard**: Detects new `*`, `_`, `[` characters
- **Bracket balance**: Detects unbalanced `[]` or `()` pairs
- **Backtick parity**: Detects change in backtick count

### Usage in Testing

This file is **NOT** currently used by smoke tests due to a limitation in Phase 7's implementation: the system only supports the integrated `detect → apply` workflow, not standalone plan application.

**For validation rejection testing**, use the comprehensive unit test suite instead:
```bash
pytest testing/unit_tests/test_apply_validator.py -v
```

The unit tests cover all 7 validators with 20+ specific rejection scenarios.

### Future Enhancement

If Phase 7 is extended to support standalone plan loading (via `--load-plan` or similar), this file could be used for end-to-end smoke testing:
```bash
# Hypothetical future usage:
python -m mdp input.md --steps apply --load-plan danger_plan.json --reject-dir rejected/
# Expected: Exit code 3, rejected plan written to rejected/
```

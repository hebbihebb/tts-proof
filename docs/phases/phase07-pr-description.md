# Phase 7 — Plan Applier & Structural Validator

## Summary

Phase 7 implements a **deterministic, idempotent plan application system** that safely applies Phase 6 detector JSON plans to text with **7 structural validators** to prevent Markdown corruption. This completes the detector → applier workflow, enabling automated TTS problem fixing with strong safety guarantees.

**Status**: ✅ Complete - 217 tests passing (81 new Phase 7 tests + 136 existing)

## Key Components

### 1. Matcher (`apply/matcher.py` - 176 lines)

**Purpose**: Literal, anchored matching with overlap prevention

**Core Algorithm**:
- **All occurrences**: Finds all non-overlapping instances left-to-right
- **Maximal munch**: Sorts by `(node_index, offset, -length)` → longest match first at each position
- **Overlap prevention**: `remove_overlapping_matches()` keeps first (longest) match at each position
- **Mask protection**: `validate_no_masked_edits()` ensures no edits in masked regions

**Key Functions**:
```python
find_all_matches(text, find, replace, reason, node_index)
# Returns: List[Match] with offset/length tracking

find_matches_in_nodes(text_nodes, plan_items)
# Returns: Sorted matches across all nodes (node→offset→-length)

remove_overlapping_matches(matches)
# Returns: (non_overlapping, overlaps_removed_count)

validate_no_masked_edits(matches, text, mask_ranges)
# Returns: (is_valid, error_message)
```

**Test Coverage**: 24 tests, all passing
- Match dataclass (4 tests)
- find_all_matches (5 tests)
- find_matches_in_nodes (6 tests)
- remove_overlapping_matches (4 tests)
- validate_no_masked_edits (5 tests)

### 2. Applier (`apply/applier.py` - 206 lines)

**Purpose**: Left-to-right non-overlapping edit engine

**Core Algorithm**:
- **Single-pass application**: Builds result left-to-right, applying matches in offset order
- **Stats tracking**: Counts replacements, length deltas, nodes changed
- **Idempotence checking**: `check_idempotence()` verifies applying plan twice yields same result

**Key Functions**:
```python
apply_matches_to_text(text, matches)
# Returns: (edited_text, stats)

apply_matches_to_nodes(text_nodes, matches)
# Returns: (edited_nodes, combined_stats)

apply_plan_to_text(text, plan_items, config)
# Returns: (edited_text, report_dict)

check_idempotence(original_text, plan_items, config)
# Returns: bool (True if idempotent)
```

**Test Coverage**: 18 tests, all passing
- apply_matches_to_text (6 tests)
- apply_matches_to_nodes (4 tests)
- apply_plan_to_text (5 tests)
- check_idempotence (3 tests)

### 3. Validator (`apply/validate.py` - 329 lines)

**Purpose**: 7 structural validators (hard stops) to prevent Markdown corruption

**Validators**:

1. **Mask Parity** (`validate_mask_parity`)
   - Ensures `__MASKED_N__` sentinel counts unchanged
   - Checks both total count and individual mask IDs

2. **Backtick Parity** (`validate_backtick_parity`)
   - Total backtick count unchanged
   - Preserves inline code pairs and fence integrity

3. **Bracket Balance** (`validate_bracket_balance`)
   - Checks `[]`, `()`, `{}` remain balanced
   - Verifies counts unchanged for each bracket type

4. **Link Sanity** (`validate_link_sanity`)
   - Markdown link syntax `](` pair count unchanged
   - Prevents broken links

5. **Fence Parity** (`validate_fence_parity`)
   - Code fence ` ``` ` count remains even
   - Prevents unclosed code blocks

6. **Markdown Token Guard** (`validate_no_new_markdown_tokens`)
   - Forbids introducing new: `*`, `_`, `[`, `]`, `(`, `)`, `` ` ``, `~`, `<`, `>`
   - Allows removing tokens (safe)

7. **Length Delta Budget** (`validate_length_delta_budget`)
   - Default: 1% max file growth
   - Configurable via `apply.max_file_growth_ratio`

**Integration Function**:
```python
validate_all(original, edited, config)
# Returns: (all_passed, list_of_failure_reasons)
# Runs all 7 validators, collects failures
```

**Test Coverage**: 39 tests, all passing
- Mask parity (5 tests)
- Backtick parity (4 tests)
- Bracket balance (5 tests)
- Link sanity (3 tests)
- Fence parity (4 tests)
- Markdown token guard (6 tests)
- Length delta budget (6 tests)
- validate_all integration (6 tests)

## Configuration

**Added to `mdp/config.py`**:
```yaml
apply:
  enabled: true
  max_file_growth_ratio: 0.01  # 1% cap on total file growth
  enforce_backtick_parity: true
  enforce_bracket_parity: true
  enforce_fence_parity: true
  forbid_new_markdown_tokens: true
  dry_run: false
```

## CLI Integration

**Added `apply` step to pipeline** (`mdp/__main__.py`):
```bash
# Full detect → apply workflow
python -m mdp input.md --steps detect,apply -o output.md

# With dry-run (no output written)
python -m mdp input.md --steps detect,apply --dry-run

# Print diff after applying
python -m mdp input.md --steps detect,apply --print-diff

# Reject validation failures to separate directory
python -m mdp input.md --steps detect,apply --reject-dir rejected/
```

**New CLI Arguments**:
- `--dry-run`: Show diff without writing output
- `--print-diff`: Print unified diff after applying plan
- `--reject-dir DIR`: Directory to write rejected edits (if validation fails)

**Exit Codes**:
- `0`: Success
- `2`: Detector model server unreachable (Phase 6)
- `3`: **Validation failure (Phase 7)** - edit rejected, structural integrity violated
- `4`: **Plan parse error (Phase 7)** - invalid JSON plan
- `5`: **Masked region edit (Phase 7)** - attempted to edit protected region

## Workflow

**Complete Detector → Applier Pipeline**:

```python
# Phase 6: Detect problems, generate JSON plan
text_nodes = ["F ʟ ᴀ s ʜ stepped forward"]
plan = detect_tts_problems(text_nodes, config)
# → [{"find": "F ʟ ᴀ s ʜ", "replace": "Flash", "reason": "TTS_SPACED"}]

# Phase 7: Apply plan with validation
edited_text, report = apply_plan_to_text(text, plan, config)
# Matcher: Finds "F ʟ ᴀ s ʜ" at offset 0
# Applier: Replaces with "Flash"
# Result: "Flash stepped forward"

# Structural validation (all 7 validators)
is_valid, failures = validate_all(original, edited_text, config)
# → (True, [])  ✓ All checks passed

# If any validator fails:
if not is_valid:
    # Write to reject directory
    # Exit code 3
    # No output file written
```

## Test Results

### Summary
- **Total tests**: 217 passing (81 Phase 7 + 136 existing)
- **Runtime**: ~3 minutes full suite, <1s for fast tests
- **Coverage**: Unit tests for all core functions
- **Integration**: Validates matcher + applier + validator workflow

### Phase 7 Test Breakdown

**Matcher Tests** (24 tests):
- ✅ Match dataclass operations (overlap detection, end offset)
- ✅ find_all_matches (single/multiple occurrences, no matches, case sensitivity)
- ✅ find_matches_in_nodes (multi-node, sorting, empty inputs)
- ✅ remove_overlapping_matches (maximal munch, different nodes)
- ✅ validate_no_masked_edits (mask boundaries, overlaps)

**Applier Tests** (18 tests):
- ✅ apply_matches_to_text (single/multiple matches, length deltas, adjacent)
- ✅ apply_matches_to_nodes (multi-node, unchanged nodes, combined stats)
- ✅ apply_plan_to_text (basic/multiple items, overlaps, no matches, growth ratio)
- ✅ check_idempotence (idempotent/non-idempotent plans, empty plan)

**Validator Tests** (39 tests):
- ✅ Mask parity (5 tests): No masks, same masks, count/ID changes
- ✅ Backtick parity (4 tests): No backticks, same count, fences
- ✅ Bracket balance (5 tests): No brackets, balanced, count changes, imbalance
- ✅ Link sanity (3 tests): No links, same count, count changes
- ✅ Fence parity (4 tests): No fences, even fences, count/parity changes
- ✅ Markdown token guard (6 tests): No tokens added, same tokens, new tokens, removed tokens
- ✅ Length delta budget (6 tests): No change, within budget, shrinking, exceeds budget, custom budget
- ✅ validate_all integration (6 tests): All pass, single/multiple failures, config overrides

## Determinism & Idempotence

**Guarantees**:

1. **Deterministic matching**: Same input + plan → same matches (sorted by node/offset/length)
2. **Idempotent application**: Applying plan twice yields same result (non-idempotence detected)
3. **Structural preservation**: 7 validators ensure Markdown structure unchanged
4. **Mask protection**: No edits in `__MASKED_N__` regions (code, links, etc.)

**Tested Properties**:
- ✅ Same input + plan → identical output (tested in `check_idempotence`)
- ✅ All occurrences replaced (tested in `find_all_matches`)
- ✅ Longest match first at each position (tested in `remove_overlapping_matches`)
- ✅ No cross-mask edits (tested in `validate_no_masked_edits`)

## Integration with Phase 6

**Seamless Pipeline**:

```python
# Phase 6 detector outputs JSON plan
detector_plan = [
    {"find": "F ʟ ᴀ s ʜ", "replace": "Flash", "reason": "TTS_SPACED"},
    {"find": "U-N-I-T-E-D", "replace": "United", "reason": "TTS_SPACED"}
]

# Phase 7 applier consumes JSON plan
edited_text, report = apply_plan_to_text(text, detector_plan, config)

# Report format
{
    'phase': 'apply',
    'files': 1,
    'nodes_changed': 1,
    'replacements_applied': 2,
    'replacements_skipped_overlap': 0,
    'replacements_skipped_no_match': 0,
    'length_delta': 0,
    'growth_ratio': 0.0
}
```

## Safety Features

1. **Validation before write**: All 7 validators run before any file output
2. **Rejection handling**: Failed edits written to `--reject-dir` for manual review
3. **Exit codes**: Distinguish validation failures (3) from server errors (2)
4. **Dry-run mode**: Preview changes without modification
5. **Length budget**: Prevents runaway edits (default 1% growth cap)
6. **Mask protection**: Never edits code blocks, links, or structural Markdown

## Performance

**Benchmarks** (217 tests):
- Fast tests (<1s): Phase 7 unit tests run in ~0.65s
- Full suite (~3min): Includes Phase 1-6 tests + grammar assist

**Scalability**:
- **Matcher**: O(n*m) where n=text length, m=plan size
- **Applier**: O(k) where k=number of matches (single pass)
- **Validators**: O(n) where n=text length (linear scan)

## Documentation

**Created**:
- This PR description (`PHASE7_PR_DESCRIPTION.md`)
- Comprehensive docstrings in all modules
- CLI help text updated with new flags

**Updated**:
- `mdp/__main__.py` docstring with Phase 7 step
- `mdp/config.py` with apply section documentation
- README (to be updated after merge)

## Acceptance Criteria

### ✅ All Acceptance Criteria Met

**Implementation**:
- ✅ apply/matcher.py (176 lines): Literal matching, all occurrences, overlap prevention
- ✅ apply/applier.py (206 lines): Left-to-right edit engine, idempotence checking
- ✅ apply/validate.py (329 lines): 7 structural validators + validate_all
- ✅ Config extension: Added 'apply' section to mdp/config.py
- ✅ CLI integration: Added 'apply' step with 3 new flags, exit codes 3/4/5

**Tests**:
- ✅ Matcher: 24 tests, all passing
- ✅ Applier: 18 tests, all passing
- ✅ Validator: 39 tests, all passing
- ✅ Integration: 217 tests passing (81 Phase 7 + 136 existing)
- ✅ No regressions: All existing tests still pass

**Determinism**:
- ✅ Idempotence check implemented and tested
- ✅ Deterministic matching (sorted by node/offset/length)
- ✅ Stable output across runs

**Safety**:
- ✅ 7 structural validators prevent Markdown corruption
- ✅ Mask protection (no edits in __MASKED_N__ regions)
- ✅ Length budget enforcement
- ✅ Rejection handling with --reject-dir

**Documentation**:
- ✅ Comprehensive PR description
- ✅ Docstrings for all functions
- ✅ CLI help text updated

## Next Steps

**Immediate**:
1. Review PR and merge to `dev`
2. Test full `detect → apply` workflow with real LM Studio server
3. Create golden test cases for integration testing

**Future Enhancements** (not in scope for Phase 7):
- Integration tests with Phase 6 detector (requires LM Studio server)
- Golden sample tests for end-to-end workflow
- Diff viewer for --print-diff output
- Progress reporting for large files

## Merge Checklist

- ✅ All 217 tests passing locally
- ✅ No existing tests broken
- ✅ Code follows project conventions
- ✅ Comprehensive documentation included
- ✅ Feature branch up-to-date with dev
- ✅ Commit message follows conventional commits
- ⏳ Reviewed by maintainer (pending)
- ⏳ Merged to dev (pending)

---

**Total Line Count**:
- Implementation: 711 lines (matcher 176 + applier 206 + validator 329)
- Tests: 1,139 lines (3 test files)
- Config/CLI: ~90 lines
- **Grand Total**: ~1,940 lines added

**Test Coverage**: 81 new tests, 217 total tests passing

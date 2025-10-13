# Phase 8 Implementation Guide - Fixer

## 🎯 Quick Reference

**Goal**: Light polish on text nodes using a bigger model (Qwen2.5-1.5B-Instruct), with strict safety guardrails.

**Estimated Time**: 4-6 hours

**Git Branch**: `feat/phase8-fixer`

---

## 📋 Pre-Flight Checklist

Before starting:
- ✅ All 217 tests pass on `dev` branch
- ✅ LM Studio running with model loaded (for testing)
- ✅ Familiar with Phase 6 (detector) and Phase 7 (applier) code patterns
- ✅ Reviewed `PHASE_PLAN_ANALYSIS.md` for implementation details

---

## 🏗️ Module Structure

Create `fixer/` directory with 4 modules:

```
fixer/
├── __init__.py           # Package init
├── client.py             # LM Studio client (similar to detector/client.py)
├── prompt.py             # Prompt templates and few-shot examples
├── guards.py             # Post-checks: length limits, forbidden tokens
└── fixer.py              # Main orchestration: chunking → call → validate
```

**Pattern to Follow**: Look at `detector/` directory structure - same design principles apply.

---

## 🔧 Implementation Steps

### Step 1: Client Module (`fixer/client.py`)

**Purpose**: Call LM Studio with proper timeouts, retries, and error handling.

**Key Functions**:
```python
def call_fixer_model(
    api_base: str,
    model: str,
    system_prompt: str,
    user_text: str,
    config: dict
) -> str:
    """Call LM Studio and return plain text response."""
    # Similar to detector/client.py but simpler (no JSON parsing)
    # Timeout: config['timeout_s']
    # Retries: config['retries']
    # Raise ConnectionError on failure (exit code 2)
```

**Tests** (`testing/unit_tests/test_fixer_client.py`):
- ✅ Successful call returns plain text
- ✅ Timeout after config seconds
- ✅ Retry on transient failures
- ✅ ConnectionError raised after max retries

---

### Step 2: Prompt Module (`fixer/prompt.py`)

**Purpose**: Generate system and user prompts for the model.

**Key Functions**:
```python
def build_system_prompt(locale: str = "en") -> str:
    """Conservative line-editor instructions."""
    return """You are a careful line editor for prose. Improve clarity and grammar
without changing meaning, tone, or details. Do not add or remove
facts, names, or events. Output the revised TEXT only. No explanations,
no lists, no quotes, no markdown, no code, no JSON—just plain text.
Language: {locale}"""

def build_user_prompt(text: str) -> str:
    """Wrap text in clear delimiters."""
    return f"""TEXT:
<<<
{text}
>>>
Return only the improved text for TEXT. No additional content."""

# Optional: Add 1-2 tiny few-shot examples (< 40 tokens total)
```

**Tests** (`testing/unit_tests/test_fixer_prompt.py`):
- ✅ System prompt includes locale
- ✅ User prompt wraps text correctly
- ✅ Few-shot examples are token-efficient

---

### Step 3: Guards Module (`fixer/guards.py`)

**Purpose**: Post-checks on model output to ensure safety.

**Key Functions**:
```python
def check_forbidden_tokens(output: str) -> tuple[bool, str]:
    """Reject if output contains markdown tokens."""
    forbidden = ['```', '`', '*', '_', '[', ']', '(', ')', '<', '>', 'http://', 'https://']
    # Return (is_valid, error_message)

def check_length_delta(original: str, output: str, max_ratio: float) -> tuple[bool, str]:
    """Reject if growth exceeds ratio."""
    # Return (is_valid, error_message)

def check_is_text(output: str) -> tuple[bool, str]:
    """Reject empty or non-text responses."""
    # Return (is_valid, error_message)

def validate_output(original: str, output: str, config: dict) -> tuple[bool, str, str]:
    """Run all checks. Return (is_valid, cleaned_output, rejection_reason)."""
    # If any check fails, return (False, original, reason)
    # If all pass, return (True, output.strip(), "")
```

**Tests** (`testing/unit_tests/test_fixer_guards.py`):
- ✅ Forbidden tokens detected (backticks, asterisks, brackets)
- ✅ Length delta enforced (20% default)
- ✅ Empty/whitespace rejected
- ✅ Valid output passes all checks

---

### Step 4: Main Fixer Module (`fixer/fixer.py`)

**Purpose**: Orchestrate chunking, model calls, validation, and reassembly.

**Key Functions**:
```python
def split_long_node(text: str, max_chars: int = 600) -> list[str]:
    """Split text node into sentence-like spans if needed."""
    # Reuse Phase 6 splitter or simple sentence regex
    # Keep spans < max_chars

def fix_span(span: str, api_base: str, model: str, config: dict) -> tuple[str, dict]:
    """Fix single span with model call and validation."""
    # 1. Build prompts
    # 2. Call model
    # 3. Validate output
    # 4. Return (result, stats_dict)
    # Stats: {"span_fixed": bool, "rejection_reason": str or None}

def apply_fixer(
    text: str,
    text_nodes: list[dict],  # From Phase 1
    mask_table: dict,        # From Phase 1
    config: dict
) -> tuple[str, dict]:
    """Main entry point: fix all text nodes and return updated text."""
    # 1. For each text node:
    #    a. Split if > 600 chars
    #    b. Fix each span
    #    c. Reassemble spans
    #    d. Update text with fixed node
    # 2. Aggregate stats
    # 3. Return (fixed_text, stats)
    
    # Stats format:
    stats = {
        "phase": "fixer",
        "model": config['model'],
        "nodes_seen": 0,
        "spans_total": 0,
        "spans_fixed": 0,
        "spans_rejected": 0,
        "rejections": {
            "forbidden_tokens": 0,
            "growth_limit": 0,
            "empty_or_non_text": 0,
            "timeout": 0,
            "non_response": 0
        },
        "file_growth_ratio": 0.0,
        "deterministic": True  # If using seed
    }
```

**Tests** (`testing/unit_tests/test_fixer_logic.py`):
- ✅ Long nodes split into spans
- ✅ Spans reassembled in correct order
- ✅ Stats aggregated correctly
- ✅ Rejected spans use original text (fail-safe)

---

### Step 5: Config Extension (`mdp/config.py`)

Add fixer configuration to existing `DEFAULT_CONFIG`:

```python
DEFAULT_CONFIG = {
    # ... existing phases ...
    'fixer': {
        'enabled': True,
        'model': 'qwen2.5-1.5b-instruct',
        'api_base': 'http://127.0.0.1:1234/v1',
        'max_context_tokens': 1024,
        'max_output_tokens': 256,
        'timeout_s': 10,
        'retries': 1,
        'temperature': 0.2,
        'top_p': 0.9,
        'node_max_growth_ratio': 0.20,   # 20% per node
        'file_max_growth_ratio': 0.05,   # 5% per file
        'forbid_markdown_tokens': True,
        'locale': 'en',
        'batch_size': 1,
        'seed': 7
    }
}
```

**No new YAML file needed** - extend existing system.

---

### Step 6: CLI Integration (`mdp/__main__.py`)

Add fixer step to `run_pipeline()` function (around line 150-180):

```python
elif step == 'fix':
    # Phase 8: Fixer with light polish
    from fixer.fixer import apply_fixer
    from apply.validate import validate_all
    
    fixer_config = config.get('fixer', {})
    
    if not fixer_config.get('enabled', True):
        logger.info("  Fixer disabled in config")
        continue
    
    try:
        logger.info("Running step: fix")
        fixed_text, fixer_stats = apply_fixer(
            text=text,
            text_nodes=text_nodes,
            mask_table=mask_table,
            config=fixer_config
        )
        
        # Validate after fixing (reuse Phase 7 validators)
        logger.info("  Validating fixed text...")
        is_valid, errors = validate_all(fixed_text, text, mask_table)
        
        if not is_valid:
            logger.error(f"  Validation failed after fixer: {errors}")
            if args.reject_dir:
                # Write rejected file
                reject_path = Path(args.reject_dir) / f"{input_path.stem}.rejected.md"
                reject_path.parent.mkdir(parents=True, exist_ok=True)
                reject_path.write_text(fixed_text, encoding='utf-8')
                logger.info(f"  Wrote rejected output to: {reject_path}")
            sys.exit(3)  # Validation failure
        
        text = fixed_text
        combined_stats['fix'] = fixer_stats
        logger.info(f"  Fixed {fixer_stats['spans_fixed']} of {fixer_stats['spans_total']} spans")
        
    except ConnectionError as e:
        logger.error(f"  Fixer model server unreachable: {e}")
        sys.exit(2)  # Model unreachable (same as detector)
```

**Test CLI Integration**:
```bash
# Test fixer alone
python -m mdp testing/test_data/hell/unicode_stylized.md --steps mask,fix --dry-run

# Test full pipeline
python -m mdp testing/test_data/hell/inter_letter_dialogue.md --steps detect,apply,fix --dry-run
```

---

## 🧪 Testing Strategy

### Unit Tests (Fast - no LLM required)
```bash
pytest testing/unit_tests/test_fixer_client.py -v
pytest testing/unit_tests/test_fixer_guards.py -v
pytest testing/unit_tests/test_fixer_logic.py -v
```

### Integration Tests (Require LLM server)
```bash
pytest testing/unit_tests/test_fixer_integration.py -m llm -v
```

**Golden Test Files** (create in `testing/test_data/fixer/`):
1. `light_polish_dialogue.md` - minor improvements expected
2. `edge_voice_stylization.md` - should preserve deliberate style
3. `table_and_links.md` - structure unchanged, only prose adjusted

---

## ✅ Acceptance Criteria

Before opening PR to `dev`:

- [ ] Fixer runs **only** on text nodes (never sees Markdown/masks)
- [ ] All outputs are plain text (markdown/code/URLs rejected)
- [ ] Length guards enforced: node ≤20%, file ≤5%
- [ ] Final output passes Phase-7 structural validators
- [ ] Exit code `2` on model unreachable (not `6`)
- [ ] CLI flags work: `--steps fix`, `--dry-run`
- [ ] JSON report includes fixer stats
- [ ] All unit tests pass: `pytest testing/unit_tests/test_fixer_*.py`
- [ ] Integration test passes (with LM Studio): `pytest -m llm`
- [ ] Branch `feat/phase8-fixer` targets `dev` (not `main`)

---

## 📊 Success Metrics

After Phase 8 completion:

- ✅ **Test count**: 217 → ~240 tests (23 new fixer tests)
- ✅ **Exit codes**: 0, 2, 3, 4, 5 all handled correctly
- ✅ **Pipeline**: Full workflow `detect → apply → fix` functional
- ✅ **Safety**: 100% of invalid outputs rejected with fail-safe
- ✅ **Performance**: < 10s per node on Qwen2.5-1.5B

---

## 🚀 After Phase 8

**Next steps**:
1. **Phase 10**: Enhanced Reporting (2-3 hours)
2. **Phase 14**: Web UI Integration (6-8 hours) ← Critical path
3. **Phase 11**: Presets & Performance

**Ready to start?** 

```bash
# Create feature branch
git checkout dev
git pull
git checkout -b feat/phase8-fixer

# Create module structure
mkdir fixer
touch fixer/__init__.py fixer/client.py fixer/prompt.py fixer/guards.py fixer/fixer.py

# Start with client.py (look at detector/client.py for patterns)
code fixer/client.py
```

Let me know when you're ready to begin! 🎯

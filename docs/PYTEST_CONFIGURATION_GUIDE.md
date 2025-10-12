# Pytest Configuration Guide - Fast Tests by Default

## 🎯 Philosophy: Fast Loops by Default

**Default behavior**: Only run **fast Phase-2 tests** (no LLM, no network, <1s total)  
**Optional**: Run slow/LLM/network tests when you explicitly choose to

---

## ⚡ Quick Command Reference

### Default: Fast Tests Only (Recommended)
```powershell
pytest
```
**Result**: Runs only Phase-2 tests, skips LLM/network tests  
**Time**: <1 second ✅

---

### Run Specific Test Categories

#### Include LLM Tests
```powershell
pytest -m "llm"
```
**What it does**: Run ONLY LLM-dependent tests  
**Time**: Varies (depends on model/network)

#### Include Slow Tests
```powershell
pytest -m "slow"
```
**What it does**: Run ONLY slow tests  
**Time**: Varies (>5 seconds per test)

#### Include Network Tests
```powershell
pytest -m "network"
```
**What it does**: Run ONLY tests requiring network access  
**Time**: Varies (depends on connection)

---

### Run Everything (Including Slow/LLM Tests)

```powershell
pytest -m ""
```
**OR:**
```powershell
pytest --override-ini="addopts=-v --tb=short"
```
**What it does**: Run ALL tests regardless of markers  
**Time**: Several minutes ⏱️

---

### Run Fast + LLM Tests (Skip Only Slow)

```powershell
pytest -m "not slow"
```
**What it does**: Run fast tests + LLM tests, skip slow tests  
**Time**: Varies (depends on LLM availability)

---

## 📝 Marking Your Tests

### How to Mark Tests

```python
import pytest

# Fast test (no marker needed - runs by default)
def test_basic_functionality():
    assert True

# LLM-dependent test (skipped by default)
@pytest.mark.llm
def test_with_llm_call():
    response = call_lmstudio(...)
    assert response

# Slow test (skipped by default)
@pytest.mark.slow
def test_large_file_processing():
    # Takes >5 seconds
    pass

# Network-dependent test (skipped by default)
@pytest.mark.network
def test_api_endpoint():
    response = requests.get("http://...")
    assert response.ok

# Multiple markers
@pytest.mark.llm
@pytest.mark.network
def test_remote_llm():
    response = call_remote_lmstudio(...)
    assert response
```

---

## 🔧 pytest.ini Configuration Explained

### Current Configuration

```ini
[pytest]
# Test discovery
python_files = test_*.py          # Find files named test_*.py
python_classes = Test*            # Find classes named Test*
python_functions = test_*         # Find functions named test_*

# Markers for test categorization
markers =
    llm: marks tests as requiring an LLM (deselected by default)
    slow: marks tests as slow (deselected by default)
    network: marks tests as requiring network access (deselected by default)

# Default behavior: skip slow/LLM/network tests
addopts = 
    -v                            # Verbose output
    --tb=short                    # Short traceback format
    -m "not llm and not slow and not network"  # Skip marked tests
    --strict-markers              # Error on unknown markers

# Test paths
testpaths = testing/unit_tests    # Default test directory

# Output options
console_output_style = progress   # Show progress bar
```

---

## 🎨 VS Code Integration

### Method 1: Testing Panel (Recommended)

**Fast tests by default:**
1. Open **Testing** panel (beaker icon)
2. Tests auto-discovered from `testing/unit_tests/`
3. Click ▶ to run - only fast tests execute
4. LLM/slow tests appear but are skipped

**Run specific test:**
- Click ▶ next to individual test
- Honors pytest markers automatically

---

### Method 2: Terminal Commands

**Fast tests:**
```powershell
pytest
```

**With specific markers:**
```powershell
pytest -m "llm"
pytest -m "not llm"
pytest -m "llm or network"
```

**Single file:**
```powershell
pytest testing/unit_tests/test_prepass_basic.py
```

**Single test:**
```powershell
pytest testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_unicode_strip
```

---

### Method 3: VS Code Tasks

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Pytest: Fast Tests",
      "type": "shell",
      "command": "${command:python.interpreterPath}",
      "args": ["-m", "pytest"],
      "group": {
        "kind": "test",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Pytest: All Tests (Including LLM)",
      "type": "shell",
      "command": "${command:python.interpreterPath}",
      "args": ["-m", "pytest", "-m", ""],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Pytest: LLM Tests Only",
      "type": "shell",
      "command": "${command:python.interpreterPath}",
      "args": ["-m", "pytest", "-m", "llm"],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    }
  ]
}
```

**Run with:** `Ctrl+Shift+P` → "Tasks: Run Task" → Select task

---

## 📊 Example Test Output

### Fast Tests (Default)

```
$ pytest

======================== test session starts ========================
collected 5 items

testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_full_run_with_report PASSED  [ 20%]
testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_unicode_strip PASSED        [ 40%]
testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_join_spaced_letters PASSED  [ 60%]
testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_hyphenation_heal PASSED     [ 80%]
testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_punctuation_normalization PASSED [100%]

======================== 5 passed in 0.01s ==========================
```

**Time: <1 second** ⚡

---

### With LLM Tests Included

```
$ pytest -m ""

======================== test session starts ========================
collected 12 items

testing/unit_tests/test_prepass_basic.py .....                  [ 41%]
testing/stress_tests/test_prepass_llm.py .....                  [ 83%]
testing/stress_tests/test_grammar_llm.py ..                     [100%]

======================== 12 passed in 45.23s ========================
```

**Time: 45+ seconds** ⏱️ (depends on LLM response time)

---

## 🚨 Common Scenarios

### Scenario 1: Quick Development Loop
**Goal**: Fast feedback during development

```powershell
pytest
```
**Result**: Only fast tests, instant feedback

---

### Scenario 2: Pre-Commit Verification
**Goal**: Ensure Phase-2 functionality before committing

```powershell
pytest -v
```
**Result**: Fast tests with verbose output

---

### Scenario 3: Full CI/CD Pipeline
**Goal**: Test everything including LLM integration

```powershell
pytest -m "" --maxfail=3
```
**Result**: All tests, stop after 3 failures

---

### Scenario 4: Testing LLM Changes
**Goal**: Only test LLM-related functionality

```powershell
pytest -m "llm"
```
**Result**: Only LLM tests, skip fast/slow tests

---

### Scenario 5: Debugging Specific Test
**Goal**: Run one test with full output

```powershell
pytest -v -s testing/unit_tests/test_prepass_basic.py::TestPrepassBasic::test_unicode_strip
```
**Result**: Single test with stdout/stderr

---

## 💡 Best Practices

### ✅ DO:
- **Run `pytest` frequently** during development (fast!)
- **Mark LLM tests** with `@pytest.mark.llm`
- **Mark slow tests** with `@pytest.mark.slow`
- **Use descriptive test names** for clarity

### ❌ DON'T:
- **Don't skip marking LLM tests** - slows down everyone's workflow
- **Don't run all tests by default** - defeats the purpose
- **Don't mix fast and slow logic** in same test

---

## 🔍 Troubleshooting

### Issue: All tests still run (including LLM)
**Solution:**
```powershell
# Check pytest.ini is being loaded
pytest --version
pytest --markers  # Should show llm, slow, network

# Verify markers are applied
pytest --collect-only
```

### Issue: Fast tests are skipped
**Solution:**
- Fast tests should NOT have `@pytest.mark.llm` or `@pytest.mark.slow`
- Remove markers from Phase-2 tests

### Issue: Can't run LLM tests when needed
**Solution:**
```powershell
pytest -m ""                    # Run everything
pytest -m "llm"                 # Run only LLM tests
pytest -m "not slow"            # Run fast + LLM (skip slow)
```

---

## 📋 Quick Reference Card

| Command | What It Runs | Time |
|---------|-------------|------|
| `pytest` | Fast tests only (default) | <1s |
| `pytest -m "llm"` | LLM tests only | ~30s |
| `pytest -m "slow"` | Slow tests only | >5s |
| `pytest -m ""` | Everything | Varies |
| `pytest -m "not llm"` | Fast + slow (no LLM) | ~5s |
| `pytest -m "not slow"` | Fast + LLM (no slow) | ~30s |
| `pytest -v` | Fast tests (verbose) | <1s |
| `pytest -s` | Fast tests (show output) | <1s |

---

## 🎯 Summary

**Default workflow:**
1. Write/modify code
2. Run `pytest` (fast tests only)
3. Get instant feedback
4. Commit when green ✅

**Before major release:**
1. Run `pytest -m ""` (all tests)
2. Verify LLM integration works
3. Deploy with confidence

**Fast by default, comprehensive when needed!** 🚀

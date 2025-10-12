# Quick Testing Guide for VS Code

## 🚀 Fast Testing Workflows (No Long Waits)

### A) Run Phase-2 Tests via Testing Panel

**Fastest method for unit tests (<1s execution time):**

1. Open **Testing** panel (beaker icon in sidebar, or `Ctrl+Shift+T`)
2. Expand `testing/unit_tests/test_prepass_basic.py`
3. Click the ▶ button next to the **file name** to run all tests
4. Or click ▶ next to individual test methods for granular testing

**Expected results:**
- ✅ All tests should pass in **<1 second**
- Green checkmarks indicate success
- Click any test to see detailed output

---

### B) CLI Smoke Test via Run/Debug

**Quick validation without network/LLM overhead:**

1. Press `F5` or open **Run and Debug** panel (`Ctrl+Shift+D`)
2. Select **"CLI Smoke Test (mdp.prepass_basic)"** from dropdown
3. Click ▶ Start Debugging

**What it does:**
- Processes `spaced_letters.md` with basic normalization
- Outputs to `testing/test_data/prepass/output_smoke.md`
- Generates report showing transformation counts
- **No LLM calls** = instant results (<1s)

**Example output:**
```
Processing: testing/test_data/prepass/spaced_letters.md
✓ Spaced words joined: 3
✓ Control chars stripped: 0
✓ Hyphenation healed: 0
Output: testing/test_data/prepass/output_smoke.md
```

---

## 🎯 Available Launch Configurations

### Quick Reference

| Configuration | Purpose | Speed | Use Case |
|--------------|---------|-------|----------|
| **Run Phase-2 Tests (Fast)** | All unit tests | <1s | Verify all Phase-2 functionality |
| **CLI Smoke Test** | Basic normalization | <1s | Quick CLI validation |
| **Test: Full Run with Report** | Single test method | <1s | Debug report generation |
| **Test: Unicode Strip** | Single test method | <1s | Debug unicode handling |
| **Test: Join Spaced Letters** | Single test method | <1s | Debug letter spacing |
| **Test: Hyphenation Heal** | Single test method | <1s | Debug hyphenation |
| **Test: Punctuation Normalization** | Single test method | <1s | Debug punctuation |
| **Python: Current File** | Run any Python file | varies | General-purpose runner |

---

## 💡 Usage Tips

### 1. Testing Panel Workflow (Recommended)
```
Testing Panel → test_prepass_basic.py → ▶ Run All Tests
```
- **Pros**: Native VS Code test discovery, inline results, re-run failed tests
- **Cons**: None for unit tests

### 2. Run/Debug Panel Workflow
```
Run and Debug (Ctrl+Shift+D) → Select config → F5
```
- **Pros**: Full debugger support, breakpoints, variable inspection
- **Cons**: Slightly slower startup (still <2s for Phase-2)

### 3. Quick Keyboard Shortcuts
- `F5`: Start debugging with current configuration
- `Ctrl+F5`: Run without debugging (faster)
- `Shift+F5`: Stop debugging
- `Ctrl+Shift+F5`: Restart debugging

---

## 🔍 Debugging Individual Tests

To debug a **specific test method**:

1. Open `test_prepass_basic.py`
2. Set breakpoint(s) in the test method
3. Select corresponding "Test: ..." configuration
4. Press `F5` to debug

**Example:** Debug `test_join_spaced_letters`:
- Configuration: **"Test: Join Spaced Letters"**
- Breakpoint: Line 66 (inside the test)
- Press `F5` → execution pauses at breakpoint

---

## 📊 Interpreting Results

### Unit Test Output (Testing Panel)
```
✅ test_full_run_with_report (0.123s)
✅ test_unicode_strip (0.045s)
✅ test_join_spaced_letters (0.067s)
✅ test_hyphenation_heal (0.089s)
✅ test_punctuation_normalization (0.134s)

5 passed in 0.458s
```

### CLI Smoke Test Output (Terminal)
```
Processing: testing/test_data/prepass/spaced_letters.md
Configuration: default_config.yaml

Transformations applied:
  - spaced_words_joined: 3
  - control_chars_stripped: 0
  - curly_quotes_straightened: 0

Output saved: testing/test_data/prepass/output_smoke.md
```

---

## 🚨 Common Issues

### Issue: Tests not discovered in Testing Panel
**Solution:**
1. Ensure Python extension is installed
2. Check `.venv` is activated: `Python: Select Interpreter`
3. Reload window: `Developer: Reload Window`

### Issue: "Module not found" errors
**Solution:**
- Check `PYTHONPATH` is set in launch.json (already configured)
- Verify working directory is workspace root: `"cwd": "${workspaceFolder}"`

### Issue: Slow test execution
**Solution:**
- Phase-2 tests should be <1s (no network/LLM calls)
- If slow, check for unexpected external dependencies
- Use individual test configs to isolate slow tests

---

## 📝 Adding New Test Configurations

Template for new launch config:
```json
{
    "name": "Test: Your Test Name",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/testing/unit_tests/test_prepass_basic.py",
    "args": ["TestPrepassBasic.test_your_method"],
    "console": "integratedTerminal",
    "justMyCode": true,
    "cwd": "${workspaceFolder}",
    "env": {
        "PYTHONPATH": "${workspaceFolder}"
    },
    "purpose": ["debug-test"],
    "presentation": {
        "group": "tests",
        "order": 8
    }
}
```

---

## ✅ Quick Verification Checklist

Before committing changes:
- [ ] Run **"Run Phase-2 Tests (Fast)"** → all green
- [ ] Run **"CLI Smoke Test"** → output file generated
- [ ] Check output file: `testing/test_data/prepass/output_smoke.md`
- [ ] Verify transformations in console output

**Total time: <5 seconds** ⚡

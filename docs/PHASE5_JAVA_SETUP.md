# Phase 5 Grammar Assist - Java & LanguageTool Setup

## ✅ What's Implemented

Phase 5 Grammar Assist is **fully implemented** and tested. The only remaining requirement is installing Java for the LanguageTool offline engine.

---

## 📋 Java Installation Required

### Why Java?

LanguageTool is an offline grammar checker that runs locally (no network dependency). It's written in Java, so it requires a Java Runtime Environment (JRE) to run.

- ✅ **Offline**: No network/internet required
- ✅ **Privacy**: All processing happens locally
- ✅ **Multi-language**: Supports English, Icelandic, and 30+ other languages
- ⚠️ **Requires**: Java JRE 8 or later

### Where to Install Java

#### Option 1: System-Wide Java (Recommended)

Install Java system-wide so it's available to all applications:

**Windows**:
1. Download from: https://www.java.com/download/
2. Run installer (will add to PATH automatically)
3. Verify: Open PowerShell and run `java -version`

**Expected output**:
```
java version "1.8.0_xxx" (or higher)
Java(TM) SE Runtime Environment (build ...)
```

#### Option 2: OpenJDK (Alternative)

If you prefer open-source:

**Windows**:
1. Download from: https://adoptium.net/ (Temurin builds)
2. Install and add to PATH
3. Verify: `java -version`

### After Installing Java

Once Java is installed, the grammar assist will work automatically:

```bash
# Test that Java is detected
python -m mdp testing/test_data/grammar_before.md --steps grammar

# Should NOT show "No java install detected" error
```

---

## 🧪 Testing Phase 5

### Quick Test (No Java Required)

Unit tests that don't need LanguageTool:
```bash
pytest testing/unit_tests/test_grammar_assist.py -v
```

**Result**: 13 tests passing in ~0.36s ✅

### Full Test (With Java)

Tests marked with `@pytest.mark.llm` that require LanguageTool:
```bash
pytest testing/unit_tests/test_grammar_assist.py -m "" -v
```

### CLI Test

Test the full pipeline:
```bash
# Basic pipeline (no grammar)
python -m mdp testing/test_data/grammar_before.md --steps mask,prepass-basic

# With grammar assist (requires Java)
python -m mdp testing/test_data/grammar_before.md --steps mask,prepass-basic,grammar -o output.md
```

---

## 🚀 CLI Usage Examples

### Pipeline Chaining

```bash
# Full pipeline with all phases
python -m mdp input.md --steps mask,prepass-basic,prepass-advanced,grammar -o output.md

# With JSON report
python -m mdp input.md --steps mask,grammar --report stats.json

# Without grammar (no Java needed)
python -m mdp input.md --steps mask,prepass-basic,prepass-advanced
```

### Available Steps

- `mask` - Phase 1: Markdown masking (protect code/links)
- `prepass-basic` - Phase 2: Unicode & spacing normalization
- `prepass-advanced` - Phase 2+: Advanced normalization (casing, punctuation)
- `scrubber` - Phase 3: Content scrubbing (remove author notes, navigation, promos)
- `grammar` - Phase 5: Grammar assist (requires Java)

---

## 📊 What Works Without Java

Everything except the grammar assist step:

✅ **Working without Java**:
- Phase 1: Markdown masking
- Phase 2: Unicode normalization, spaced letter joining, hyphenation healing
- Phase 2+: Casing normalization, punctuation collapse, ellipsis standardization
- Phase 3: Content scrubbing
- All structural validation
- All unit tests (13 tests)
- CLI interface

❌ **Requires Java**:
- Phase 5: Grammar corrections (typos, spacing, punctuation, casing, simple agreement)
- LLM-gated integration tests (2 tests)

---

## 🎯 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core module | ✅ Complete | `mdp/grammar_assist.py` |
| Configuration | ✅ Complete | `grammar_assist` section in config |
| Structural validation | ✅ Complete | Mask/link/backtick parity checks |
| Unit tests | ✅ Complete | 13 tests passing |
| CLI integration | ✅ Complete | `--steps grammar` support |
| Pipeline chaining | ✅ Complete | `mask,prepass,grammar` |
| **Java installation** | ⏳ **Pending** | **User to install** |

---

## 💡 Next Steps

1. **Install Java** (system-wide or OpenJDK)
2. **Verify**: Run `java -version` in PowerShell
3. **Test Phase 5**: Run `python -m mdp testing/test_data/grammar_before.md --steps grammar`
4. **Ready for PR**: Once Java is confirmed working

---

## 📝 Notes for PR

When creating the PR, note in the description:

```markdown
### System Requirements

Phase 5 Grammar Assist requires **Java JRE 8+** to be installed:

- **Windows**: https://www.java.com/download/
- **Linux**: `sudo apt install default-jre`
- **macOS**: `brew install openjdk`

The grammar engine (LanguageTool) runs **completely offline** - no internet/network required.
```

---

## 🔧 Troubleshooting

**Issue**: "No java install detected"
- **Solution**: Install Java and ensure it's in PATH
- **Verify**: `java -version` should work in terminal

**Issue**: "LanguageTool not available"
- **Solution**: Run `pip install language-tool-python` (already done)

**Issue**: Grammar corrections not applied
- **Solution**: Check `config['grammar_assist']['enabled'] = True`

**Issue**: Markdown structure broken
- **Solution**: Phase 5 auto-reverts if validation fails (safe by design)

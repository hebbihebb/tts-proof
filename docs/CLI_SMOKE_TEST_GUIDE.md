# CLI Smoke Test Verification Guide

## 🎯 Quick Verification Workflow

After running the **"CLI Smoke Test (mdp.prepass_basic)"** configuration:

### 1️⃣ Run the Test

**In VS Code:**
1. Press `Ctrl+Shift+D` (Run and Debug)
2. Select **"CLI Smoke Test (mdp.prepass_basic)"**
3. Press `F5` or click ▶

**Expected terminal output:**
```
Processing: testing/test_data/prepass/spaced_letters.md

Transformations applied:
  - spaced_words_joined: 3

Output saved: testing/test_data/prepass/.tmp/prepass_out.md
```

---

### 2️⃣ Compare Files in Explorer

**Visual Comparison:**
1. **Open Explorer** panel (`Ctrl+Shift+E`)
2. Navigate to `testing/test_data/prepass/`
3. **Select** `spaced_letters.md` (left-click)
4. **Right-click** on `.tmp/prepass_out.md`
5. Choose **"Compare with Selected"**

**Split-view diff will open** showing before/after changes! ✨

---

## ✅ Expected Transformations

### Input: `spaced_letters.md`
```markdown
S p a c e d out letters.
A,n,o,t,h,e,r example.
And F . L . A . S . H.
This should not be changed: a b c.
```

### Output: `.tmp/prepass_out.md`
```markdown
Spaced out letters.
Another example.
And FLASH.
This should not be changed: a b c.
```

---

## 🔍 What You Should See

### ✅ **Spaced Letters Joined**
| Before | After | Reason |
|--------|-------|--------|
| `S p a c e d` | `Spaced` | 4+ letters with spaces |
| `A,n,o,t,h,e,r` | `Another` | 4+ letters with commas |
| `F . L . A . S . H` | `FLASH` | 4+ letters with dots and spaces |

### ❌ **Not Changed**
- `a b c` → Remains unchanged (only 3 letters, threshold is 4)

---

## 📊 Report Interpretation

### Terminal Summary Output

```
Transformations applied:
  - spaced_words_joined: 3
```

**Breakdown:**
- **3 transformations** = 3 matched patterns joined
  1. `S p a c e d` → `Spaced`
  2. `A,n,o,t,h,e,r` → `Another`
  3. `F . L . A . S . H` → `FLASH`

---

## 🧪 Testing Other Features

### Test: Unicode Stripping (`unicode_zwsp.md`)

**Change launch.json args to:**
```json
"args": [
  "${workspaceFolder}/testing/test_data/prepass/unicode_zwsp.md",
  "-o",
  "${workspaceFolder}/testing/test_data/prepass/.tmp/prepass_out.md",
  "--report"
],
```

**Expected output:**
```
Transformations applied:
  - control_chars_stripped: 4
```

**What it does:**
- Removes zero-width spaces (`\u200b`)
- Removes soft hyphens (`\u00ad`)
- Removes bidi controls (`\u202c`)
- Removes byte-order marks (`\ufeff`)

---

### Test: Hyphenation Healing (`hyphen_wrap.md`)

**Change launch.json args to:**
```json
"args": [
  "${workspaceFolder}/testing/test_data/prepass/hyphen_wrap.md",
  "-o",
  "${workspaceFolder}/testing/test_data/prepass/.tmp/prepass_out.md",
  "--report"
],
```

**Expected transformation:**
```
Before: cre-
        ative

After:  creative
```

**Report:**
```
Transformations applied:
  - hyphenation_healed: 1
```

---

### Test: Punctuation Normalization (`punct_policy.md`)

**Change launch.json args to:**
```json
"args": [
  "${workspaceFolder}/testing/test_data/prepass/punct_policy.md",
  "-o",
  "${workspaceFolder}/testing/test_data/prepass/.tmp/prepass_out.md",
  "--report"
],
```

**Expected transformations:**
- Curly quotes → Straight quotes: `"text"` → `"text"`
- Curly single quotes → Straight: `'text'` → `'text'`
- Ellipsis character → Three dots: `…` → `...`
- Em dashes → Standardized

**Report:**
```
Transformations applied:
  - curly_quotes_straightened: 4
  - ellipses_standardized: 1
  - dashes_normalized: 1
```

---

## 🛡️ Markdown Structure Preservation

### What Gets Protected

The normalization **only processes text nodes**, preserving:

✅ **Code blocks** (fenced with ` ``` `)  
✅ **Inline code** (` `code` `)  
✅ **Links** (`[text](url)`)  
✅ **Images** (`![alt](src)`)  
✅ **HTML blocks** (`<div>...</div>`)  
✅ **Front matter** (YAML between `---`)

**Example:**
```markdown
# Title S p a c e d

Some S p a c e d text.

```python
# Code: S p a c e d (NOT CHANGED)
```

[Link S p a c e d](url)
```

**After processing:**
```markdown
# Title Spaced

Some Spaced text.

```python
# Code: S p a c e d (NOT CHANGED)
```

[Link S p a c e d](url)
```

**Only the text node changed!** Code and links stay intact.

---

## 💡 Quick Tips

### Diff View Navigation
- `F7` - Next change
- `Shift+F7` - Previous change
- `Alt+Enter` - Show change context menu

### Switching Test Files
1. Edit `.vscode/launch.json`
2. Change first arg in `"args"` array
3. Press `F5` to run

### Clean Up Output
```powershell
Remove-Item -Recurse testing/test_data/prepass/.tmp
```

---

## 🚨 Troubleshooting

### Issue: No `.tmp` folder appears
**Solution:** The CLI creates it automatically. Check the terminal output for the actual path.

### Issue: "Module not found: mdp"
**Solution:** Ensure `PYTHONPATH` is set in launch.json (already configured).

### Issue: Changes not appearing in diff
**Solution:** 
1. Verify input file has actual problems (e.g., `S p a c e d`)
2. Check terminal report shows transformations
3. Refresh Explorer: `Ctrl+R`

### Issue: Can't find `.tmp` in Explorer
**Solution:** 
1. Ensure "Show Hidden Files" is enabled in Explorer
2. Refresh Explorer view
3. Check terminal output for actual output path

---

## 📝 Next Steps

After verifying the smoke test:

1. ✅ Run all Phase-2 unit tests: **"Run Phase-2 Tests (Fast)"**
2. ✅ Test each transformation category individually
3. ✅ Verify Markdown structure preservation
4. ✅ Check edge cases (empty files, large files, special characters)

**Total verification time: <30 seconds** ⚡

# TTS-Proof v2

**Local-first Markdown cleaner and TTS-readability enhancer**

![TTS-Proof GUI](screenshot.png)

---

## 🧩 What It Does

**TTS-Proof** is a lightweight, single-file Python app that fixes text problems that break text-to-speech engines and grammar-readers.  
It detects and corrects:

- Stylized Unicode text (`Bʏ Mʏ Rᴇsᴏʟᴠᴇ → By My Resolve`)
- Spaced-out letters (`F l a s h → Flash`)
- Hyphenated speech (`U-N-I-T-E-D → UNITED`)
- OCR/translation artifacts while preserving Markdown formatting

Everything runs **locally**, using **LM Studio**, **KoboldCpp**, or any **OpenAI-compatible local API** for intelligent detection — no cloud required.

---

## ⚙️ How It Works

A modular **8-phase pipeline** ensures accurate fixes without breaking Markdown:

| Phase | Purpose | LLM Required |
|-------|----------|--------------|
| 1. Mask | Protect code, links, HTML | No |
| 2–3. Prepass | Normalize Unicode, spacing, casing | No |
| 4. Scrubber | Remove boilerplate *(planned)* | No |
| 5. Detect | Identify TTS-problem text | ✅ Yes |
| 6. Apply | Apply validated fixes (7 structural checks) | No |
| 7. Fix | Light polish *(planned)* | ✅ Yes |

**Validators** guard structure: mask parity, backtick parity, bracket balance, link sanity, fence parity, token guard, and length delta (<1%).

---

## 🚀 Quick Start

### Requirements
- Python 3.10+
- Optional: `pip install requests` (for LLM access)
- [LM Studio](https://lmstudio.ai/) or other local OpenAI-compatible server

### Run the GUI
```bash
python gui.py
````

### Command-Line

```bash
# Full pipeline: Detect TTS problems and apply grammar correction
python md_processor.py --input input.md --output output.md --steps mask,detect,grammar
```

### Basic cleanup only

```bash
python md_processor.py --input input.md --output clean.md --steps mask,prepass-basic,prepass-advanced
```

---

## 🧠 Dependencies

* **Python stdlib only** (Tkinter, logging, argparse, json)
* **requests** *(optional)* for local LLM access
* No web server, no database, no external UI stack

---

## 🧪 Example

**Before:**

```markdown
The word F l a s h appeared on screen.
Someone said: "U-N-I-T-E-D we stand!"
Another example: Bʏ Mʏ Rᴇsᴏʟᴠᴇ!
```

**After:**

```markdown
The word Flash appeared on screen.
Someone said: "UNITED we stand!"
Another example: By My Resolve!
```

Markdown code blocks, links, and inline code are preserved exactly.

---

## 🔮 Planned Features

* **Scrubber phase** – remove author notes, navigation, and promos from ebooks
* **Fixer phase** – final LLM polish and grammar pass
* **Config presets** – GUI-based server/model selector
* **Real-time progress** – live chunk logging from LLM calls

---

## 🧰 Project Layout

```
tts-proof/
├── md_processor.py   # Core processor
├── gui.py            # Tkinter GUI
├── prompts.json      # LLM prompts
├── servers.json      # Server configs
├── screenshot.png
└── readme.md
```

---

## 📝 License

Personal utility project — use freely, at your own risk.
Contributions and issue reports welcome.
[github.com/hebbihebb/tts-proof](https://github.com/hebbihebb/tts-proof)

---
# README — tts-proof

## Purpose

Batch-correct grammar and spelling in Markdown files using a **local LLM** served by **LM Studio** (OpenAI-compatible API).  
Preserves Markdown structure (headings, lists, links, code blocks), checkpoints progress, and now includes a simple, resizable GUI with customizable prompts.

---

## Features

- Local-only processing via LM Studio (`http://127.0.0.1:1234/v1`)
- Chunked processing with progress bar + spinner
- URL masking and code-block preservation
- Streaming previews (optional)
- Crash-safe: writes to `.partial` and `.ckpt.json`, supports `--resume`
- **GUI included** (`md_proof_gui.py`)
  - Resizable, modern interface
  - Model selection dropdowns auto-populated from LM Studio
  - Edit the grammar correction prompt live via a popup (saved in `grammar_promt.txt`)
  - TTS Cleaner model and prompt UI (for future use)
  - Output file is auto-named and created
  - Log panel filters redundant progress messages for clarity
- Simple round-trip with EPUB via Pandoc or Calibre (optional)

---

## Requirements

- **Python 3.10+**
- Python packages: `requests`, `regex`
- **LM Studio** (Local Server enabled) with a grammar-capable model downloaded  
  Example: `qwen/qwen3-4b-2507` (larger models improve quality)
- (Optional) **Pandoc** or **Calibre** for EPUB ⇄ Markdown conversion

---

## Performance

- **Tested:** Mobile RTX 2060 GPU (8GB VRAM), 40 minutes for a 300+ page document.

---

## Install (Windows example)

1. Install Python and pip.
2. Install dependencies:
   ```
   pip install requests regex
   ```
3. Save `md_proof.py`, `md_proof_gui.py`, and `grammar_promt.txt` to a folder, e.g. `C:\Tools\md_proof\`.
4. (Optional) Create a launcher batch file for convenience.

---

## Start LM Studio

1. Download your model (e.g., `qwen/qwen3-4b-2507`) in LM Studio.
2. Enable **Local Server** (OpenAI-compatible). Default base URL:  
   `http://127.0.0.1:1234/v1`
3. Note the **exact** model name as shown by LM Studio.

---

## Usage

### Command Line

Correct a Markdown file and write `*.corrected.md`:

```
python md_proof.py path\to\file.md
```

Show a live preview (first 400 chars per chunk):

```
python md_proof.py book.md --stream --preview-chars 400
```

### GUI

Run:

```
python md_proof_gui.py
```

#### GUI Features

- **Open Markdown File**: Select your input file.
- **Grammar Model**: Choose from available models (auto-populated from LM Studio).
- **TTS-Cleaner Model**: Placeholder for future TTS cleaning (selectable, not yet functional).
- **Grammar Model Prompt**: View and edit the prompt sent to the LLM (changes are saved to `grammar_promt.txt` and used immediately).
- **TTS Cleaner Prompt**: Placeholder for future TTS prompt editing.
- **Resizable interface**: All panels and popups are resizable for convenience.
- **Output file**: Automatically named and created in the same folder as the input.
- **Log panel**: Shows only meaningful output and errors (filters redundant progress messages).

---

## Prompt Customization

- The grammar correction prompt is stored in `grammar_promt.txt`.
- You can edit this prompt at any time via the GUI ("Grammar Model Prompt" button).
- Changes are saved and used immediately for subsequent corrections.

---

## EPUB Round-Trip

- **Pandoc:**  
  EPUB → Markdown:  
  `pandoc input.epub -t gfm -o book.md`  
  Markdown → EPUB:  
  `pandoc book.corrected.md -o corrected.epub`

- **Calibre:**  
  Also tested for conversion back to EPUB.  
  Headers in Markdown can be used to generate a table of contents (TOC).

---

## Tips

- Larger local models (7B–14B) yield better corrections.
- Keep code blocks fenced to prevent editing.
- For documents with tables/footnotes/custom syntax, test with `--stream` to verify formatting.
- For extra safety on long jobs, add `--fsync`.
- Use the GUI for easy prompt customization and model selection.

---

## Troubleshooting

- **Model name mismatch / 404:** Pass the exact LM Studio model name via the GUI or `--model`.
- **Auth errors:** LM Studio server should allow no API key or you must configure one.
- **No output / hangs:** Use `--no-progress` to rule out terminal issues; check LM Studio logs.
- **Resource errors:** If you see "Insufficient system resources," restart your computer and avoid running too many jobs at once.

---

## License & Contributions

Personal utility script; adapt as you wish.

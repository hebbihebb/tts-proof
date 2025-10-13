# TTS-Proof - Modern Grammar Correction Tool

## 📚 What Does This Do? (Simple Version)

Got a document with terrible spelling, weird formatting, or messy translation? Here's your fix:

1. **Convert your document to Markdown** using tools like [Calibre](https://calibre-ebook.com/) or [Pandoc](https://pandoc.org/)
2. **Run it through TTS-Proof** - it uses AI to clean up grammar, spelling, and odd text formatting
3. **Convert it back** to your original format (PDF, DOCX, EPUB, etc.)
4. **Voilà!** ✨ Clean, readable document ready to go

Perfect for cleaning up:
- 📖 **Ebooks** with OCR errors or poor formatting
- 🌐 **Web articles** that were badly translated  
- 📝 **Old documents** with outdated spelling conventions
- 🤖 **AI-generated text** that needs polishing
- 📄 **Any text** that just looks messy and unprofessional

*No internet required - everything runs locally on your computer for privacy!*

---

## Overview

A modern web-based application for batch grammar and spelling correction of Markdown files using **local LLM** servers (LM Studio). Features a beautiful React frontend with optimized layout, real-time progress tracking, and a robust FastAPI backend that preserves all original processing capabilities.

## 📸 Interface Preview

![TTS-Proof Web Interface](screenshot-web-interface.png)

*Modern 6-section grid layout optimized for wide displays: organized workflow from file selection to processing, with preview and logs at the bottom.*

---

## ✨ Features

### 🎨 Modern Web Interface
- **Optimized 6-section grid layout** perfect for 4K displays and wide screens
- **Logical workflow organization** - file setup → model config → processing controls
- **React + TypeScript frontend** with Tailwind CSS styling  
- **Real-time progress updates** via WebSocket connections
- **Dark/Light theme toggle** for comfortable use
- **Drag & drop file uploads** with instant preview and file analysis

### 🔧 Powerful Processing Engine
- **TTS Prepass Detection** with auto-selection for grammar correction workflow
- **Flexible LLM server support** with configurable endpoints (LM Studio, KoboldCpp, Oobabooga, TabbyAPI, etc.)
- **Network-ready** - connect to local or remote servers on your network
- **Intelligent chunking** with configurable sizes and progress tracking
- **Crash-safe processing** with automatic checkpointing and resume
- **Markdown structure preservation** (headings, lists, links, code blocks)
- **URL masking** and code-block protection during processing

### 🚀 Advanced Architecture
- **FastAPI backend** with WebSocket support for real-time updates
- **Concurrent processing** with proper job management
- **Model auto-detection** from LM Studio server
- **Customizable prompts** with live editing capabilities
- **File management** with temporary file handling and cleanup

---

## 📋 Requirements

- **Python 3.10+**
- **Node.js 16+** and npm
- **LM Studio** with local server enabled
- Grammar-capable model (e.g., `qwen/qwen3-4b-2507`)

---

## 🚀 Quick Start

### 1. Setup LM Studio
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a grammar-capable model (e.g., `qwen/qwen3-4b-2507`)
3. Enable **Local Server** with OpenAI-compatible API
4. Default URL: `http://127.0.0.1:1234/v1`

### 2. Install Dependencies

**Backend:**
```bash
cd backend
pip install fastapi uvicorn websockets python-multipart requests regex
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Start the Application

#### 🚀 **Easy Launch (Recommended)**

Use one of the provided launchers to start both servers with a single command:

**Windows (Batch):**
```cmd
launch.bat
```

**Windows (PowerShell):**
```powershell
.\launch.ps1
```

**Cross-platform (Python):**
```bash
python launch.py
```

**Unix/Linux/macOS (Shell):**
```bash
./launch.sh
```

#### 📋 **Manual Launch**

If you prefer to start servers separately:

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:** Open `http://localhost:5174` in your browser

### 🎮 **Launcher Features**

The provided launchers automatically:
- ✅ **Check system requirements** (Python 3.10+, Node.js 16+)
- ✅ **Install missing dependencies** (pip and npm packages)
- ✅ **Start both servers** simultaneously
- ✅ **Open your browser** to the application
- ✅ **Handle cleanup** when stopping (Unix/Linux/Python launcher)
- ✅ **Provide clear status updates** and error messages

Choose the launcher that works best for your system!

---

## 🎯 How to Use

### Streamlined 6-Section Workflow:

**Top Row - Setup:**
1. **File Selection**: Drag & drop your Markdown file with instant analysis
2. **Model Selection**: Choose your LLM model and configure endpoints
3. **Chunk Size**: Set optimal processing chunk size (4K-16K chars)

**Bottom Row - Processing:**
4. **TTS Prepass**: Run detection for TTS-problematic words (auto-selects for correction)
5. **Prompt Template**: Customize grammar correction instructions
6. **Processing**: Execute with real-time progress tracking

**Preview & Logs**: Monitor results and processing details at the bottom

### Quick Steps:
1. **Upload** your file → **Select** model → **Process** → **Download** results
2. Optional: Run **TTS Prepass** for enhanced correction of speech-problematic text

---

## Phase 1: AST & Masking

To improve the accuracy of grammar correction and protect parts of the document that should not be altered, a new processing step has been introduced. This step uses a Markdown Abstract Syntax Tree (AST) to identify and mask protected elements like code blocks, links, and HTML.

This ensures that only plain text is sent to the language model for correction, preserving the integrity of the document's structure.

### Demo the Masking Feature

You can test the masking and unmasking process using the command-line interface:

```bash
python md_proof.py --in testing/test_data/ast/fences_inline.md --out /tmp/out.md --steps mask,unmask
```

This command will:
1.  Read the input file.
2.  **Mask** all protected elements (code fences, inline code, etc.) and save the intermediate state.
3.  **Unmask** the content, restoring it to its original form.
4.  Write the final, unmasked content to `/tmp/out.md`.

If the process is successful, the output file will be identical to the input file.

---

## Phase 2 — Pre-Pass 2.0 (Unicode & Spacing)

This phase introduces a deterministic normalization step that runs after masking and before any LLM-based correction. It is designed to clean up common text artifacts that can interfere with Text-to-Speech (TTS) engines and LLM processing.

This pre-pass step handles:
- **Unicode Cleanup**: Normalizes text to NFKC form, strips zero-width characters, and standardizes punctuation.
- **Spaced Letter Repair**: Joins spaced-out letters (e.g., "S p a c e d") into a single word.
- **Hyphenation Healing**: Fixes words broken across lines with a hyphen.

This step can be run from the command line:
```bash
python md_proof.py --in testing/test_data/prepass/spaced_letters.md --out .tmp/out.md --steps mask,prepass-basic,unmask
```

---

## Phase 3 — Boilerplate / Notes Scrubber

**Deterministic & Reversible Cleaning**

Phase 3 introduces an intelligent boilerplate detection and removal system that runs after masking and before LLM-based grammar correction. It identifies and optionally removes non-story content that interferes with processing or reading flow.

### What It Detects

The scrubber identifies several categories of boilerplate content:

- **Author/Translator/Editor Notes**: Pattern-based detection of notes (A/N, T/N, E/N)
- **Navigation Text**: "Previous Chapter", "Next Chapter", "Table of Contents" links
- **Promotional Content**: Patreon, Ko-fi, Discord, social media links
- **Link Farms**: Paragraphs with excessive link density (>50% links)
- **Watermarks**: "Read on...", "Original at...", "Source on..." stamps

### Edge Bias Protection

To avoid false positives in story content, the scrubber uses **edge bias**:
- Only examines the **first 6 and last 6 blocks** by default
- Middle content is preserved unless confidence is >95%
- Prevents accidental removal of in-story letters, notes, or dialogue

Example: An "Author's Note" at the top of a chapter will be detected and removed, but a letter written by a character in the middle of a story will be preserved.

### Usage Examples

**Dry-Run Mode** (preview candidates without changes):
```bash
python md_proof.py --in story.md --steps scrub-dryrun --report
```

**Apply Scrubbing** (with appendix):
```bash
python md_proof.py --in story.md --out clean.md --steps mask,scrub,unmask --appendix Appendix.md --report
```

**Integrated Workflow** (prepass + scrub + grammar):
```bash
python md_proof.py --in story.md --out final.md --steps mask,prepass-basic,scrub,unmask --appendix Appendix.md
```

### Configuration

Configure scrubber behavior via YAML config file:

```yaml
scrubber:
  enabled: true
  move_to_appendix: true        # Move to Appendix.md vs delete
  edge_block_window: 6          # Number of edge blocks to check
  link_density_threshold: 0.50  # 50% link density = link farm
  min_chars_to_strip: 12        # Minimum block size to consider
  
  categories:
    authors_notes: true
    translators_notes: false    # Keep translator notes
    editors_notes: true
    navigation: true
    promos_ads_social: true
    link_farms: true
  
  whitelist:
    headings_keep:
      - "Translator's Cultural Notes"
      - "Historical Context"
    domains_keep:
      - "project-notes.local"
  
  keywords:
    promos: ["patreon", "ko-fi", "discord", "support me"]
    navigation: ["previous chapter", "next chapter", "table of contents"]
    watermarks: ["read on", "original at", "source on"]
```

### Reversibility

All removed blocks are preserved in the appendix file with:
- Original content and position (edge-top, edge-bottom)
- Detection reason and confidence score
- Category grouping for easy reference
- Manual restoration instructions

---

## Phase 4 — Advanced Pre-Pass Policies (Casing / Punctuation / Units)

**Policy-Driven Deterministic Cleanup**

Phase 4 introduces an advanced pre-pass that applies configurable policies to normalize casing, punctuation, and numbers/units spacing. It operates exclusively on text nodes (not code blocks, links, or URLs) and runs after basic pre-pass, before LLM-based grammar correction.

### Policy Areas

The advanced pre-pass handles four major categories:

#### 1. **Casing Normalization**
- **All-Caps Detection**: Identifies and normalizes SHOUTING text (≥4 characters by default)
- **Acronym Whitelist**: Respects technical acronyms (NASA, JSON, API, HTML, TTS, etc.)
- **Protected Lexicon**: Preserves special onomatopoeia, names, and intentional styling
- **Title Case**: Converts `MAGNIFICENT DRAGON` → `Magnificent Dragon`

Example:
```markdown
BEFORE: This is TERRIBLE! The ANCIENT DRAGON appears, and NASA launches.
AFTER:  This is Terrible! The Ancient Dragon appears, and NASA launches.
```

#### 2. **Punctuation Policies**
- **Run Collapse**: Reduces excessive punctuation (`!!!!` → `!`, `??!!` → `?!`)
- **Ellipsis Normalization**: Standardizes `…` ↔ `...` (three dots or Unicode)
- **Quote Style**: Converts curly quotes `""` to straight `""` (or vice versa)
- **Sentence Spacing**: Single/double space after periods

Collapse Policies:
- `first-only`: `!!!!! → !` (keep only first character)
- `first-of-each`: `??!! → ?!` (keep first of each punctuation type)

#### 3. **Numbers & Units**
- **Percent Joining**: Removes space before % (`23 %` → `23%`)
- **Unit Spacing**: Normalizes space between numbers and units
  - Temperatures: `23 °C`, `73.4 °F`
  - Distances: `5 km`, `15 cm`
  - Weights: `500 g`, `1.5 kg`
  - Time: `250 ms`
- **Time Format**: Standardizes time expressions
  - `5pm` → `5 p.m.`
  - `9AM` → `9 a.m.`
  - `12 PM` → `12 p.m.`

#### 4. **Footnote Markers** (Optional)
- **Inline Removal**: Optionally removes `[^1]`, `[1]`, `(1)` markers
- **Definition Preservation**: Always preserves footnote definitions (markers followed by `:`)

### Usage Examples

**Basic Usage**:
```bash
python md_proof.py --in file.md --out clean.md --steps prepass-advanced --report
```

**Full Pipeline** (with masking):
```bash
python md_proof.py --in story.md --out final.md \
  --steps mask,prepass-basic,prepass-advanced,unmask --report
```

**Integrated Workflow** (all pre-processing stages):
```bash
python md_proof.py --in story.md --out final.md \
  --steps mask,prepass-basic,prepass-advanced,scrub,unmask \
  --appendix Appendix.md --report
```

### Configuration

Configure policy behavior via YAML config file:

```yaml
prepass_advanced:
  enabled: true
  
  casing:
    normalize_shouting: true
    shouting_min_len: 4               # Minimum caps word length
    acronym_whitelist:
      - NASA
      - GPU
      - JSON
      - HTML
      - TTS
      - API
      - URL
      - HTTP
      - HTTPS
      - CSS
      - SQL
    protected_lexicon:
      - Aaahahaha                      # Onomatopoeia
      - BLUH
      - Reykjavík                      # Icelandic names
      - Þór
      - AAAAAA                         # Intentional screaming
  
  punctuation:
    collapse_runs: true
    runs_policy: first-of-each         # or 'first-only'
    ellipsis: three-dots               # or 'unicode' for …
    quotes: straight                   # or 'curly'
    apostrophe: straight
    space_after_sentence: single       # or 'double'
  
  numbers_units:
    join_percent: true                 # 23 % → 23%
    space_before_unit: normal          # 'normal' (5 km), 'none' (5km)
    time_style: p.m.                   # 'p.m.', 'PM', or 'pm'
    locale: en
  
  footnotes:
    remove_inline_markers: false       # Set true to remove [^1] markers
```

### Idempotency & Structure Preservation

- **Idempotent**: Running twice produces identical output with zero changes on second pass
- **Markdown-Safe**: Preserves code blocks, inline code, URLs, links, HTML, tables, headings
- **Text-Node-Only**: Only processes human-readable text content
- **Maskable**: Works seamlessly with AST-based masking system

### Report Output

With `--report` flag, get detailed change counts:

```
Prepass Advanced Report:
  - casing_normalized: 12
  - runs_collapsed: 4
  - ellipsis: 8
  - quotes: 16
  - spacing: 23
  - percent_joined: 5
  - unit_spaces: 7
  - times: 3
  - footnotes_removed: 0
```

### Testing & Validation

Run comprehensive test suite:
```bash
pytest testing/unit_tests/test_prepass_advanced.py -v
```

**10 test methods** covering:
- Casing with acronym/protected lexicon respect
- Punctuation run collapse policies
- Ellipsis and quote normalization
- Numbers/units spacing and percent joining
- Time format transformation
- Optional footnote removal
- Markdown structure preservation
- Idempotency (second pass = zero changes)

---

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket    ┌──────────────────┐
│  React Frontend │ ←──────────────→ │  FastAPI Backend │
│  (Port 5174)    │                 │  (Port 8000)     │
└─────────────────┘                 └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   LM Studio      │
                                    │  (Port 1234)     │
                                    └──────────────────┘
```

### Backend Features
- FastAPI server with WebSocket support
- Original `md_proof.py` processing logic integration
- Real-time progress updates and job management
- File upload handling and temporary file management

### Frontend Features
- React 18 with TypeScript and optimized 6-section grid layout
- Tailwind CSS for modern styling with 4K display optimization
- Real-time WebSocket communication with live progress updates
- TTS Prepass integration with auto-selection workflow
- Theme switching and responsive design for all screen sizes

---

## 🌐 Server Configuration

### Configuring LLM Server Endpoints

TTS-Proof supports multiple LLM server backends with configurable endpoints:

1. **Click the edit button** (📝) next to the model selection dropdown
2. **Choose from presets:**
   - **LM Studio**: `http://127.0.0.1:1234/v1` (default)
   - **KoboldCpp**: `http://127.0.0.1:5001/v1`
   - **Oobabooga**: `http://127.0.0.1:5000/v1`
   - **TabbyAPI**: `http://127.0.0.1:5000/v1`

3. **Or configure custom endpoints:**
   - Enter custom IP address and port
   - Full URL configuration support
   - Network server support (e.g., `http://192.168.1.100:1234/v1`)

### Remote Server Setup
To connect to a server on another machine:
1. Ensure the server accepts connections from your IP
2. Use the custom endpoint option
3. Enter the server's IP address and port
4. Test connection by refreshing models

---

## 🔧 Advanced Features

### Command Line Interface (MDP Pipeline)
The modern CLI provides fine-grained control over processing stages:

#### Basic Usage
```bash
# Run full pipeline
python -m mdp input.md --steps mask,prepass-basic,prepass-advanced,grammar

# Run only prepass normalization
python -m mdp input.md --steps mask,prepass-basic -o output.md

# Run detector + apply workflow
python -m mdp input.md --steps mask,detect,apply -o output.md
```

#### Report Generation
Generate machine-readable JSON reports or human-readable summaries:

```bash
# JSON report only
python -m mdp input.md --steps mask,detect,apply --report report.json

# Human-readable pretty report (printed to stdout)
python -m mdp input.md --steps mask,detect,apply --report-pretty

# Both JSON and pretty report
python -m mdp input.md --steps mask,detect,apply --report report.json --report-pretty
```

**Pretty Report Output Example:**
```
====================================================================
                          RUN SUMMARY                              
====================================================================
  Input file     : input.md
  Output file    : output.md
  Pipeline steps : mask -> detect -> apply

====================================================================
                        PHASE STATISTICS                           
====================================================================
  Mask     : 50 regions masked
  Detector : 20 suggestions (model: qwen2.5-1.5b)
  Apply    : 18 replacements in 12 nodes

====================================================================
                           REJECTIONS                              
====================================================================
Detector Rejections:
  schema_invalid :    5

====================================================================
                          FILE GROWTH                              
====================================================================
  Apply phase : +1.50% (+30 chars)
```

**Report Features:**
- 📊 **Organized sections**: Run summary, phase stats, rejections, file growth, quality flags
- 📏 **Compact formatting**: ~100 char width, truncated paths for readability
- ✅ **Smart visibility**: Sections only shown when relevant (no empty tables)
- 📈 **Growth tracking**: File size changes with percentages and character deltas
- 🎯 **Quality indicators**: Determinism flags, rejection counts per phase

#### Available Pipeline Steps
- `mask` - Phase 1: Markdown structure masking
- `prepass-basic` - Phase 2: Unicode & spacing normalization
- `prepass-advanced` - Phase 2+: Advanced normalization (casing, punctuation)
- `scrubber` - Phase 3: Content scrubbing (author notes, navigation, etc.)
- `grammar` - Phase 5: Grammar assist (LanguageTool integration)
- `detect` - Phase 6: TTS problem detection
- `apply` - Phase 7: Plan application with validation
- `fix` - Phase 8: Light polish with LLM

#### Additional Options
```bash
# Output to specific file
python -m mdp input.md --steps mask,grammar -o output.md

# Use custom config
python -m mdp input.md --config custom_config.yaml --steps mask,prepass-basic

# Verbose output
python -m mdp input.md --steps mask,detect,apply -v

# Dry-run mode (apply step)
python -m mdp input.md --steps mask,detect,apply --dry-run

# Print unified diff (apply step)
python -m mdp input.md --steps mask,detect,apply --print-diff
```

See `docs/` for detailed phase documentation and examples.

### Legacy CLI (md_proof.py)
The original CLI is still available for backward compatibility:
```bash
python md_proof.py document.md --stream --preview-chars 400
```

### Prompt Customization
- Edit prompts directly in the web interface
- Changes are saved to `grammar_promt.txt` automatically
- Live preview of prompt changes

### EPUB Integration
Convert EPUB files for processing:
```bash
# EPUB to Markdown
pandoc input.epub -t gfm -o book.md

# Process with TTS-Proof web interface

# Markdown back to EPUB
pandoc book.corrected.md -o corrected.epub
```

---

## 📊 Performance

- **Tested:** RTX 2060 (8GB VRAM) - 40 minutes for 300+ page document
- **Chunking:** 8000 character chunks for optimal processing
- **Checkpointing:** Automatic resume on interruption
- **Memory:** Efficient streaming prevents memory issues

---

## 🛠️ Development

### Project Structure
```
tts-proof/
├── backend/
│   ├── app.py              # FastAPI server
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── App.tsx         # Main application
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
├── md_proof.py             # Core processing logic
└── grammar_promt.txt       # Grammar correction prompts
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build

# Backend deployment
cd backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## 📊 Phase Status & Roadmap

### ✅ Completed Phases

- **Phase 1**: AST-based Markdown masking (code blocks, links, HTML protection)
- **Phase 2**: Unicode normalization & spacing cleanup (deterministic preprocessing)
- **Phase 3**: Content scrubbing (author notes, navigation, promotional content removal)
- **Phase 5**: Grammar assist integration (LanguageTool offline engine)
- **Phase 6**: Detector system (tiny model → JSON replacement plans with guardrails)
- **Phase 7**: Plan applier & structural validator (7 validators, deterministic, idempotent)

**Current Test Coverage**: 217 tests passing (Phases 1-7)

### 🚀 Active Features

#### Phase 6 & 7: Detector + Applier Workflow

**Detect → Apply Pipeline** for automated TTS problem fixing:

```bash
# Full workflow: detect problems → generate plan → apply with validation
python -m mdp input.md --steps detect,apply -o output.md

# Step by step with plan inspection
python -m mdp input.md --steps detect --plan plan.json --print-plan
python -m mdp input.md --steps apply --plan plan.json -o output.md

# Dry-run mode (preview without writing)
python -m mdp input.md --steps detect,apply --dry-run

# With rejection directory for failed validations
python -m mdp input.md --steps detect,apply --reject-dir rejected/
```

**Exit Codes:**
- `0`: Success
- `2`: Detector model server unreachable
- `3`: **Validation failure** - edit rejected, structural integrity violated
- `4`: **Plan parse error** - invalid JSON plan
- `5`: **Masked region edit** - attempted to edit protected content

**Structural Validators** (7 hard stops):
1. Mask parity (`__MASKED_N__` sentinels unchanged)
2. Backtick parity (inline code & fences)
3. Bracket balance (`[]`, `()`, `{}`)
4. Link sanity (`](` pairs preserved)
5. Fence parity (` ``` ` even count)
6. Markdown token guard (no new `*`, `_`, `[`, etc.)
7. Length delta budget (1% max growth, configurable)

**Testing Validation Rejection:**
Validator behavior is covered by 81 comprehensive unit tests in `testing/unit_tests/test_apply_*.py`. For smoke testing the full workflow, run `make test-fast` (unit tests) or `make smoke` (requires detector model server running).

### 🎯 TODO / Future Enhancements

#### UI/UX Improvements
- [ ] **Separate model picker for prepass** - Allow different models for TTS detection vs grammar correction
- [ ] **Expose prepass prompt in web UI** - Make TTS detection prompts editable like grammar prompts
- [ ] **Reorganize web UI layout** - Improve component arrangement for more intuitive workflow
- [ ] **Real-time chunk preview** - Display processed chunks as they complete, not just final result
- [ ] **Open temp files location button** - Quick access to temporary/processing files directory in file browser
- [ ] **Batch file processing** *(optional)* - Support multiple file uploads and queue management
- [ ] **Processing history** *(optional)* - Keep track of recently processed files and settings

### 🔧 Core Features *(optional enhancements)*
- [ ] **Custom prompt templates** - Save and switch between different correction strategies
- [ ] **Processing profiles** - Quick presets for different document types (academic, creative, technical)
- [ ] **Diff view** - Side-by-side comparison showing original vs corrected text with highlights
- [ ] **Export options** - Support for different output formats (PDF, DOCX, plain text)
- [ ] **Undo/redo functionality** - Allow users to revert or modify corrections
- [ ] **Smart resume** - Better checkpoint recovery with partial chunk restoration

### 🚀 Advanced Features *(optional enhancements)*
- [ ] **Model performance analytics** - Track processing speed and quality metrics per model
- [ ] **API rate limiting** - Configurable delays between LLM calls to prevent server overload
- [ ] **Collaborative editing** - Multi-user support with real-time synchronization
- [ ] **Plugin system** - Extensible architecture for custom processing rules
- [ ] **Cloud deployment** - Docker containerization and deployment guides
- [ ] **Mobile responsiveness** - Optimize interface for tablet and mobile devices

### 🧪 Quality & Testing *(optional enhancements)*
- [ ] **Automated testing suite** - Comprehensive unit and integration tests
- [ ] **Performance benchmarking** - Measure and optimize processing speeds
- [ ] **Error recovery** - Better handling of network interruptions and server failures
- [ ] **Logging improvements** - More detailed debugging and audit trails

*Contributions welcome! Feel free to tackle any of these items or suggest new features.*

---

## �🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Models not loading** | Ensure LM Studio server is running on port 1234 |
| **WebSocket connection failed** | Check if backend is running on port 8000 |
| **Frontend won't start** | Run `npm install` in frontend directory |
| **Processing stuck** | Check LM Studio logs, restart if needed |
| **File upload failed** | Ensure file is .md, .txt, or .markdown format |

---

## 📄 License

Personal utility tool - adapt and use as you wish. No warranty provided.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the tool.

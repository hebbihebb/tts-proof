# V2 Refactor Plan: Consolidated Core Library & One-Shot UI

**Target Branch**: `feature/v2-refactor-one-shot-ui`  
**Status**: Planning Phase  
**Goal**: Transform multi-component web app → single-library CLI + minimal GUI

---

## 🎯 Vision

From:
```
React (5174) ←WebSocket→ FastAPI (8000) → MDP Pipeline → LM Studio (1234)
```

To:
```
CLI: md_processor.py → LM Studio (1234)
GUI: one_shot_gui.html → md_processor.py → LM Studio (1234)
```

---

## 📦 New Architecture

### Core: `md_processor.py` (Single File)

**Responsibilities**:
- All pipeline phases (mask, prepass-basic, prepass-advanced, scrubber, detect, apply, fix)
- LLM API client (OpenAI-compatible endpoints)
- Intelligent chunking and checkpoint/resume
- Structural validators (7 hard stops)
- Progress callback system
- Embedded prompts and default config
- CLI entry point with argparse

**Structure**:
```python
# Configuration constants (embedded from prompts/ and config/)
GRAMMAR_PROMPT = """..."""
DETECTOR_PROMPT = """..."""
DEFAULT_CONFIG = {...}

# Phase 1: Masking
def mask_protected(text: str) -> tuple[str, dict]: ...
def unmask(text: str, mask_table: dict) -> str: ...

# Phase 2: Prepass
def prepass_basic(text: str, config: dict) -> tuple[str, dict]: ...
def prepass_advanced(text: str, config: dict) -> tuple[str, dict]: ...

# Phase 3: Scrubber
def scrub_content(text: str, config: dict) -> tuple[str, dict]: ...

# Phase 5: Grammar (optional, requires LanguageTool)
def grammar_assist(text: str, config: dict) -> tuple[str, dict]: ...

# Phase 6: Detect
def detect_problems(text: str, llm_client, config: dict) -> tuple[list, dict]: ...

# Phase 7: Apply
def apply_plan(text: str, plan: list, config: dict) -> tuple[str, dict]: ...
def validate_structural_integrity(original: str, edited: str) -> tuple[bool, str]: ...

# Phase 8: Fix
def fix_polish(text: str, llm_client, config: dict) -> tuple[str, dict]: ...

# LLM Client
class LLMClient:
    def __init__(self, endpoint: str, model: str): ...
    def complete(self, prompt: str, text: str) -> str: ...

# Chunking & Checkpointing
def intelligent_chunk(text: str, chunk_size: int) -> list[str]: ...
def save_checkpoint(path: Path, data: dict) -> None: ...
def load_checkpoint(path: Path) -> dict | None: ...

# Progress System
class ProgressCallback:
    def on_progress(self, percent: float, message: str): ...
    def on_chunk_complete(self, index: int, total: int): ...

# Pipeline Orchestrator
def run_pipeline(
    input_text: str,
    steps: list[str],
    config: dict,
    llm_client: LLMClient,
    progress: ProgressCallback | None = None
) -> tuple[str, dict]:
    """Main pipeline runner"""
    ...

# CLI Entry Point
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--endpoint', default='http://localhost:1234/v1')
    parser.add_argument('--model', default='qwen3-grammar')
    parser.add_argument('--chunk-size', type=int, default=8000)
    parser.add_argument('--steps', default='mask,detect,apply')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--config-override', type=json.loads)
    parser.add_argument('--verbose', action='store_true')
    ...

if __name__ == '__main__':
    sys.exit(main())
```

### GUI: `one_shot_gui.html` (Single File)

**Features**:
- Mobile-first responsive design
- Drag-and-drop file upload
- LM Studio endpoint configuration
- Pipeline step selection (checkboxes)
- Run/Reset buttons
- Real-time progress bar (0-100%)
- Scrolling log output
- Download result button

**Architecture**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        /* Embedded CSS: mobile-first, clean design */
        body { font-family: system-ui; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .drop-zone { border: 2px dashed #ccc; padding: 40px; text-align: center; }
        .progress-bar { width: 100%; height: 30px; background: #f0f0f0; border-radius: 5px; }
        .progress-fill { height: 100%; background: #4CAF50; transition: width 0.3s; }
        .log-output { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 15px; height: 300px; overflow-y: auto; }
        /* ... */
    </style>
</head>
<body>
    <div class="container">
        <h1>TTS-Proof v2</h1>
        
        <!-- File Upload -->
        <div class="drop-zone" id="dropZone">
            Drag & drop Markdown file or click to select
            <input type="file" accept=".md,.txt" id="fileInput" hidden>
        </div>
        
        <!-- Configuration -->
        <div class="config">
            <label>LM Studio Endpoint:</label>
            <input type="text" id="endpoint" value="http://localhost:1234/v1">
            
            <label>Model:</label>
            <input type="text" id="model" value="qwen3-grammar">
            
            <label>Pipeline Steps:</label>
            <div class="steps">
                <label><input type="checkbox" checked value="mask"> Mask</label>
                <label><input type="checkbox" checked value="detect"> Detect</label>
                <label><input type="checkbox" checked value="apply"> Apply</label>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <button id="runBtn" disabled>Run Pipeline</button>
            <button id="resetBtn">Reset</button>
        </div>
        
        <!-- Progress -->
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
        </div>
        <div class="progress-text" id="progressText">Ready</div>
        
        <!-- Log Output -->
        <div class="log-output" id="logOutput"></div>
        
        <!-- Download -->
        <button id="downloadBtn" disabled>Download Result</button>
    </div>
    
    <script>
        // State
        let fileContent = null;
        let fileName = null;
        let resultText = null;
        
        // File handling
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            loadFile(file);
        });
        fileInput.addEventListener('change', (e) => {
            loadFile(e.target.files[0]);
        });
        
        function loadFile(file) {
            fileName = file.name;
            const reader = new FileReader();
            reader.onload = (e) => {
                fileContent = e.target.result;
                document.getElementById('runBtn').disabled = false;
                addLog(`Loaded: ${fileName} (${fileContent.length} chars)`);
            };
            reader.readAsText(file);
        }
        
        // Pipeline execution
        document.getElementById('runBtn').addEventListener('click', runPipeline);
        
        async function runPipeline() {
            const endpoint = document.getElementById('endpoint').value;
            const model = document.getElementById('model').value;
            const steps = Array.from(document.querySelectorAll('.steps input:checked'))
                .map(cb => cb.value);
            
            document.getElementById('runBtn').disabled = true;
            clearLog();
            setProgress(0, 'Starting pipeline...');
            
            try {
                // Option A: Call md_processor.py via subprocess (requires local server)
                // Option B: Implement pipeline logic in JavaScript (call LLM directly)
                
                // For now, implement direct LLM calls in JS
                let text = fileContent;
                let stats = {};
                
                // Phase 1: Mask
                if (steps.includes('mask')) {
                    setProgress(10, 'Phase 1: Masking...');
                    const maskResult = await maskProtected(text);
                    text = maskResult.masked;
                    stats.mask = maskResult.stats;
                    addLog(`Masked ${maskResult.stats.masks_created} regions`);
                }
                
                // Phase 6: Detect
                if (steps.includes('detect')) {
                    setProgress(40, 'Phase 6: Detecting problems...');
                    const plan = await detectProblems(text, endpoint, model);
                    stats.detect = { plan_size: plan.length };
                    addLog(`Detected ${plan.length} problems`);
                    
                    // Phase 7: Apply
                    if (steps.includes('apply')) {
                        setProgress(70, 'Phase 7: Applying fixes...');
                        const applyResult = await applyPlan(text, plan);
                        text = applyResult.text;
                        stats.apply = applyResult.stats;
                        addLog(`Applied ${plan.length} fixes`);
                    }
                }
                
                // Unmask
                if (stats.mask) {
                    setProgress(95, 'Unmasking...');
                    text = unmask(text, stats.mask.maskTable);
                }
                
                resultText = text;
                setProgress(100, 'Complete!');
                addLog(`✓ Pipeline complete (${text.length} chars)`);
                document.getElementById('downloadBtn').disabled = false;
                
            } catch (error) {
                addLog(`✗ Error: ${error.message}`, 'error');
                setProgress(0, 'Failed');
            } finally {
                document.getElementById('runBtn').disabled = false;
            }
        }
        
        // LLM API calls
        async function callLLM(endpoint, model, prompt, text) {
            const response = await fetch(`${endpoint}/chat/completions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: model,
                    messages: [
                        { role: 'system', content: prompt },
                        { role: 'user', content: text }
                    ],
                    temperature: 0.3,
                    max_tokens: 8000
                })
            });
            
            if (!response.ok) throw new Error(`LLM API error: ${response.status}`);
            const data = await response.json();
            return data.choices[0].message.content;
        }
        
        // Masking (client-side implementation)
        function maskProtected(text) {
            // Simple regex-based masking (simplified version)
            const masks = [];
            let counter = 0;
            const maskTable = {};
            
            // Code blocks
            text = text.replace(/```[\s\S]*?```/g, (match) => {
                const sentinel = `__MASKED_${counter}__`;
                maskTable[sentinel] = match;
                counter++;
                return sentinel;
            });
            
            // Links
            text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match) => {
                const sentinel = `__MASKED_${counter}__`;
                maskTable[sentinel] = match;
                counter++;
                return sentinel;
            });
            
            return {
                masked: text,
                stats: { masks_created: counter, maskTable }
            };
        }
        
        function unmask(text, maskTable) {
            for (const [sentinel, original] of Object.entries(maskTable)) {
                text = text.replace(sentinel, original);
            }
            return text;
        }
        
        // UI helpers
        function setProgress(percent, message) {
            document.getElementById('progressFill').style.width = `${percent}%`;
            document.getElementById('progressText').textContent = message;
        }
        
        function addLog(message, type = 'info') {
            const log = document.getElementById('logOutput');
            const timestamp = new Date().toLocaleTimeString();
            const line = document.createElement('div');
            line.className = type;
            line.textContent = `[${timestamp}] ${message}`;
            log.appendChild(line);
            log.scrollTop = log.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('logOutput').innerHTML = '';
        }
        
        // Download
        document.getElementById('downloadBtn').addEventListener('click', () => {
            const blob = new Blob([resultText], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName.replace('.md', '.processed.md');
            a.click();
            URL.revokeObjectURL(url);
        });
        
        // Reset
        document.getElementById('resetBtn').addEventListener('click', () => {
            fileContent = null;
            fileName = null;
            resultText = null;
            document.getElementById('runBtn').disabled = true;
            document.getElementById('downloadBtn').disabled = true;
            setProgress(0, 'Ready');
            clearLog();
        });
    </script>
</body>
</html>
```

---

## 📋 Implementation Phases

### Phase 1: Core Consolidation (8-10 hours)
1. Create `md_processor.py` skeleton with all function signatures
2. Extract masking logic from `mdp/markdown_adapter.py` and `mdp/masking.py`
3. Merge prepass logic from `mdp/prepass_basic.py` and `mdp/prepass_advanced.py`
4. Copy detector logic from `detector/detector.py` and `detector/client.py`
5. Copy apply/validate logic from `apply/applier.py` and `apply/validate.py`
6. Merge LLM client from `md_proof.py` (call_lmstudio, extract_between_sentinels)
7. Embed prompts from `prompts/` as string constants
8. Embed default config from `mdp/config.py`
9. Add comprehensive docstrings and type hints

### Phase 2: CLI Implementation (3-4 hours)
1. Build argparse interface with all required flags
2. Implement progress callbacks (CLI prints to stdout)
3. Add checkpoint/resume functionality
4. Test with `testing/test_data/` files
5. Verify exit codes (0=success, 1=error, 2=unreachable, 3=validation fail)
6. Document CLI usage in docstring and `--help`

### Phase 3: One-Shot GUI (4-6 hours)
1. Create HTML skeleton with responsive CSS
2. Implement file drag-and-drop
3. Add configuration inputs (endpoint, model, steps)
4. Build progress bar and log output
5. Implement client-side masking/unmasking
6. Add LLM API calls via fetch()
7. Wire up Run/Reset/Download buttons
8. Test on mobile and desktop browsers
9. Add error handling and validation

### Phase 4: Documentation & Migration (3-4 hours)
1. Update `readme.md` with v2 architecture
2. Create `V2_ARCHITECTURE.md` with detailed design
3. Update `.github/copilot-instructions.md`
4. Write `MIGRATION_GUIDE.md` (v1 → v2)
5. Create feature parity matrix
6. Archive legacy components to `legacy/` with README
7. Update `SESSION_STATUS.md` and `ROADMAP.md`

### Phase 5: Testing & Validation (2-3 hours)
1. Test CLI with all step combinations
2. Test GUI with sample EPUB-derived Markdown
3. Verify LM Studio integration
4. Test checkpoint/resume
5. Validate progress callbacks
6. Performance testing (large files)
7. Cross-browser testing for GUI

---

## 🔄 Migration Strategy

### What's Removed
- ❌ FastAPI backend (`backend/`)
- ❌ React frontend (`frontend/`)
- ❌ WebSocket real-time updates
- ❌ Run history API (`~/.mdp/runs/`)
- ❌ Preset management
- ❌ Multi-server support
- ❌ `launch.py` orchestrator

### What's Preserved
- ✅ All 8 pipeline phases
- ✅ LM Studio integration
- ✅ Masking/validation logic
- ✅ Checkpointing/resume
- ✅ Progress reporting (via callbacks)
- ✅ Configuration system
- ✅ Embedded prompts

### What's New
- 🆕 Single-file CLI (`md_processor.py`)
- 🆕 Single-file GUI (`one_shot_gui.html`)
- 🆕 Simplified configuration
- 🆕 Mobile-friendly UI
- 🆕 Embedded prompts (no external files)

### CLI Command Mapping

| v1 Command | v2 Command |
|------------|------------|
| `python -m mdp input.md --steps mask,detect,apply -o output.md` | `python md_processor.py --input input.md --output output.md --steps mask,detect,apply` |
| `python launch.py` | Open `one_shot_gui.html` in browser |
| `python backend/app.py` | (Not needed in v2) |

---

## ✅ Success Criteria

- [ ] `md_processor.py` processes test file end-to-end via CLI
- [ ] CLI supports all 8 phases with `--steps` flag
- [ ] Checkpoint/resume works correctly
- [ ] Progress callbacks report accurate percentages
- [ ] `one_shot_gui.html` loads and functions without errors
- [ ] GUI can upload file, run pipeline, show progress, download result
- [ ] GUI works on mobile (tested iOS Safari / Android Chrome)
- [ ] All structural validators pass (mask parity, backtick parity, etc.)
- [ ] LM Studio integration matches v1 behavior
- [ ] Documentation complete (README, architecture, migration guide)
- [ ] Legacy components archived with explanation

---

## 📝 Notes

**Design Decisions**:
- Single file for maintainability (vs. module split)
- Embedded prompts to eliminate external dependencies
- Progress callbacks for flexibility (CLI prints, GUI updates bar)
- Client-side JS for GUI (no server needed)
- Preserve all validation logic (7 hard stops)

**Trade-offs**:
- ❌ No run history/artifacts
- ❌ No WebSocket real-time updates
- ❌ No preset management
- ✅ Simpler deployment (2 files)
- ✅ Easier to understand
- ✅ Mobile-friendly GUI

**Future Enhancements** (not in scope):
- Server mode for GUI (subprocess md_processor.py)
- Batch processing
- Configuration file support
- Plugin system for custom phases
- Desktop app packaging (Electron)

---

## 🚀 Getting Started

```bash
# 1. Create branch
git checkout dev
git pull origin dev
git checkout -b feature/v2-refactor-one-shot-ui

# 2. Create md_processor.py skeleton
touch md_processor.py

# 3. Start consolidation
# Copy code from mdp/, detector/, apply/, fixer/

# 4. Test CLI
python md_processor.py --input testing/test_data/smoke/input.md --output output.md --steps mask,detect,apply

# 5. Create GUI
touch one_shot_gui.html

# 6. Test GUI
# Open one_shot_gui.html in browser
```

---

**Next Steps**: Review this plan, then start Phase 1 (Core Consolidation).

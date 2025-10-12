# Directory Structure Guide

This document describes the organized directory structure of TTS-Proof after cleanup (October 12, 2025).

## 📁 **Root Directory Structure**

```
tts-proof/
├── 📁 .github/              # GitHub configuration
├── 📁 backend/              # FastAPI server
├── 📁 config/               # Configuration files and presets
├── 📁 docs/                 # Documentation and analysis reports
├── 📁 frontend/             # React/TypeScript web interface
├── 📁 prompts/              # Prompt templates and versions
├── 📁 testing/              # All testing infrastructure
├── 🐍 md_proof.py           # Core CLI tool
├── 🐍 prepass.py            # TTS detection engine
├── 📄 prepass_prompt.txt    # Current prepass prompt
├── 📄 grammar_promt.txt     # Current grammar prompt (note: typo preserved)
├── 🚀 launch.py             # Cross-platform launcher
├── 📄 readme.md             # Main project documentation
└── 📄 todo.md               # Project task tracking
```

---

## 📋 **Directory Details**

### 🗂️ **`/config/`** - Configuration Files
```
config/
├── lmstudio_preset_qwen3_prepass.json    # LM Studio preset for prepass
└── lmstudio_preset_qwen3_grammar.json    # LM Studio preset for grammar
```
**Purpose**: LM Studio presets, sampling parameters, and model configurations

### 📚 **`/docs/`** - Documentation & Analysis
```
docs/
├── functional_parity_analysis.md         # Web UI vs testing capabilities comparison
├── integration_task_recommendations.md   # Roadmap for integrating advanced features
├── prompt_optimization_applied.md        # Summary of applied prompt improvements
├── baseline_results_analysis.md          # Initial testing analysis
└── iteration_results_summary.md          # Complete iterative improvement results
```
**Purpose**: Analysis reports, testing documentation, and improvement tracking

### 🎯 **`/prompts/`** - Prompt Templates & Versions
```
prompts/
├── upgraded/
│   ├── prepass_upgraded.txt              # Enhanced prepass prompt
│   ├── grammar_upgraded.txt              # Enhanced grammar prompt  
│   ├── prepass_upgraded_sentinel.txt     # Prepass with sentinel markers
│   └── grammar_upgraded_sentinel.txt     # Grammar with sentinel markers
└── prompt_versions/                      # Historical prompt versions
    └── [iteration directories]
```
**Purpose**: Current prompts (root), upgraded prompts, and version history

### 🧪 **`/testing/`** - Complete Testing Infrastructure
```
testing/
├── stress_tests/
│   ├── [stress testing files moved here]  # Advanced stress testing system
│   └── [evolution and A/B testing]       # Iterative improvement tools
├── unit_tests/
│   ├── test_prepass.py                   # Prepass unit tests
│   ├── test_prepass_integration.py       # Prepass integration tests
│   ├── test_integration.py               # End-to-end tests
│   └── test_sentinel.py                  # Sentinel parsing tests
├── test_data/
│   ├── tts_stress_test.md                # Comprehensive TTS problem dataset
│   ├── tts_stress_test_reference.md      # Handcrafted reference for comparison
│   ├── webui_test.md                     # Web UI test document
│   ├── test_input.md                     # Basic test input
│   ├── test_input.corrected.md           # Expected output
│   └── test_log.md                       # Test execution logs
├── stress_test_results/                   # Generated test results
│   └── [timestamped log files]
└── simple_test.py                        # Quick testing script
```
**Purpose**: All testing infrastructure, from unit tests to stress testing frameworks

---

## 🎯 **Key Benefits of This Organization**

### ✅ **Cleaner Root Directory**
- **Core files only**: Main tools (`md_proof.py`, `prepass.py`) and essential configs
- **Launchers easily accessible**: `launch.py`, `launch.bat`, etc. in root
- **Current prompts visible**: Active `prepass_prompt.txt` and `grammar_promt.txt` in root

### 🔍 **Logical Grouping**
- **Testing isolated**: All test files, data, and results in `/testing/`
- **Documentation centralized**: Analysis and reports in `/docs/`
- **Configuration organized**: Presets and configs in `/config/`
- **Prompt evolution tracked**: Current, upgraded, and historical versions in `/prompts/`

### 🚀 **Development Workflow Improved**
- **Easy testing access**: `cd testing && python simple_test.py`
- **Clear prompt management**: Current prompts in root, experiments in `/prompts/`
- **Organized results**: All test outputs in structured `/testing/` subdirectories
- **Documentation findable**: Analysis reports logically grouped in `/docs/`

### 🛠️ **Maintenance Benefits**
- **Scalable structure**: Easy to add new test types, configurations, or documentation
- **Version control friendly**: Related files grouped, easier to track changes
- **Onboarding improved**: Clear structure helps new developers understand project layout
- **Backup/deployment simplified**: Logical separation of core vs. development files

---

## 🔄 **Migration Notes**

### **Files Moved During Cleanup:**
- **Testing files** → `/testing/` subdirectories
- **Analysis documents** → `/docs/`
- **Upgraded prompts** → `/prompts/upgraded/`
- **LM Studio presets** → `/config/`
- **Test datasets** → `/testing/test_data/`

### **Files Kept in Root:**
- **Core engines**: `md_proof.py`, `prepass.py`
- **Active prompts**: `prepass_prompt.txt`, `grammar_promt.txt`
- **Launchers**: All platform-specific launch scripts
- **Essential docs**: `readme.md`, `todo.md`
- **Project structure**: `.github/`, `backend/`, `frontend/`

### **Path Updates Required:**
- Update any scripts that reference moved files
- Check import paths in test files
- Verify documentation links still work
- Update `.gitignore` patterns if needed

---

## 📋 **Quick Access Commands**

```bash
# Run main CLI tool
python md_proof.py input.md

# Test current system
cd testing && python simple_test.py

# Run comprehensive stress tests
cd testing/stress_tests && python [stress_test_files]

# View analysis reports
cd docs && ls *.md

# Check current prompts
cat prepass_prompt.txt grammar_promt.txt

# Review upgraded prompts
cd prompts/upgraded && ls *.txt

# Configure LM Studio
cd config && cat lmstudio_preset_*.json
```

This organized structure maintains full functionality while providing a much cleaner, more maintainable codebase! 🎉
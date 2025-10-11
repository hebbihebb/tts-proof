# TTS-Proof - Modern Grammar Correction Tool

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

### Command Line Interface (Legacy)
The original CLI is still available for batch processing:
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

## 🐛 Troubleshooting

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

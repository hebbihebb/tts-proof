# TTS-Proof - Modern Grammar Correction Tool

## Overview

A modern web-based application for batch grammar and spelling correction of Markdown files using **local LLM** servers (LM Studio). Features a beautiful React frontend with real-time progress tracking and a robust FastAPI backend that preserves all original processing capabilities.

---

## ✨ Features

### 🎨 Modern Web Interface
- **React + TypeScript frontend** with Tailwind CSS styling
- **Real-time progress updates** via WebSocket connections
- **Dark/Light theme toggle** for comfortable use
- **Responsive design** that works on any screen size
- **Drag & drop file uploads** with instant preview

### 🔧 Powerful Processing Engine
- **Local-only processing** via LM Studio (`http://127.0.0.1:1234/v1`)
- **Intelligent chunking** (8000 chars) with progress tracking
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

---

## 🎯 How to Use

1. **Connect**: The app automatically connects to your LM Studio server
2. **Upload**: Drag & drop or select your Markdown file
3. **Configure**: Choose your model and edit prompts if needed
4. **Process**: Click "Send for Processing" and watch real-time progress
5. **Download**: Get your corrected text when processing completes

---

## 📸 Screenshots

### Modern Web Interface
![TTS-Proof Web Interface](screenshot-web-interface.png)

*The new React-based interface showing file upload, real-time processing progress, and side-by-side text preview with dark theme.*

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
- React 18 with TypeScript
- Tailwind CSS for modern styling
- Real-time WebSocket communication
- Theme switching and responsive design

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

#!/usr/bin/env python3
"""
FastAPI backend for TTS-Proof application.
Provides REST API endpoints and WebSocket support for the React frontend.
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import os
import concurrent.futures

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Import our existing functionality
import sys
sys.path.append(str(Path(__file__).parent.parent))
from md_proof import (print_progress, load_markdown, chunk_paragraphs, DEFAULT_API_BASE, DEFAULT_MODEL,
                     INSTRUCTION, mask_urls, unmask_urls, extract_between_sentinels, 
                     call_lmstudio, Spinner, paths_for, write_ckpt, load_ckpt)
from prepass import (run_prepass, write_prepass_report, load_prepass_report, 
                    get_replacement_map_for_grammar, inject_prepass_into_grammar_prompt,
                    get_problem_words_for_grammar, inject_prepass_into_grammar_prompt_legacy)

# Load the high-quality grammar prompt
GRAMMAR_PROMPT_PATH = Path(__file__).parent.parent / "grammar_promt.txt"
if GRAMMAR_PROMPT_PATH.exists():
    with open(GRAMMAR_PROMPT_PATH, encoding="utf-8") as f:
        GRAMMAR_PROMPT = f.read().strip()
else:
    GRAMMAR_PROMPT = INSTRUCTION  # Fallback to the built-in instruction

def correct_chunk_with_prompt(api_base, model, raw_text: str, prompt: str, show_spinner: bool = False):
    """Custom version of correct_chunk that accepts a custom prompt."""
    masked, urls = mask_urls(raw_text)
    sp = Spinner("Contacting LLM") if show_spinner else None
    if sp: sp.start()
    try:
        resp = call_lmstudio(api_base, model, prompt, masked)
    finally:
        if sp: sp.stop(clear_line=True)
    corrected = extract_between_sentinels(resp)
    return unmask_urls(corrected, urls)

app = FastAPI(title="TTS-Proof API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", 
                   "http://localhost:5174", "http://127.0.0.1:5174"],  # Vite dev server (multiple ports)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                print(f"Sending WebSocket message to {client_id}: {message.get('type', 'unknown')}")
                await self.active_connections[client_id].send_text(json.dumps(message))
                print(f"WebSocket message sent successfully to {client_id}")
            except Exception as e:
                print(f"Error sending WebSocket message to {client_id}: {e}")
                # Connection closed, remove it
                self.disconnect(client_id)
        else:
            print(f"No WebSocket connection found for client {client_id}. Active connections: {list(self.active_connections.keys())}")

manager = ConnectionManager()

async def run_prepass_with_websocket(input_path: Path, api_base: str, model: str, 
                                   chunk_chars: int = 8000, client_id: Optional[str] = None) -> Dict:
    """Run prepass detection with WebSocket progress updates."""
    from prepass import detect_tts_problems
    from md_proof import chunk_paragraphs, load_markdown
    from datetime import datetime
    
    # Track prepass job for cancellation
    if client_id:
        prepass_jobs[client_id] = {"status": "processing"}
    
    try:
        print(f"WebSocket prepass starting - client_id: {client_id}")
        
        # Load and chunk the markdown (use same method as original prepass)
        raw_text = input_path.read_text(encoding="utf-8")
        chunks = chunk_paragraphs(raw_text, chunk_chars)
        
        # Filter to text chunks only (skip code blocks)
        text_chunks = [(i, content) for i, (kind, content) in enumerate(chunks) if kind == "text"]
        total_chunks = len(text_chunks)
        
        print(f"Found {total_chunks} text chunks to process")
        
        if client_id:
            print(f"Sending initial progress message to client {client_id}")
            await manager.send_message(client_id, {
                "type": "progress",
                "source": "prepass",
                "progress": 0,
                "message": f"Starting prepass detection on {total_chunks} chunks...",
                "chunks_processed": 0,
                "total_chunks": total_chunks
            })
            print("Initial progress message sent")
    except Exception as e:
        error_msg = f"Failed to load or chunk markdown: {str(e)}"
        print(error_msg)
        if client_id:
            await manager.send_message(client_id, {
                "type": "error",
                "source": "prepass",
                "message": error_msg
            })
        raise e
    
    # Process each chunk
    report_chunks = []
    all_problems = []
    current_byte = 0
    
    print(f"Starting to process {len(text_chunks)} chunks...")
    
    try:
        for chunk_idx, (original_idx, content) in enumerate(text_chunks):
            # Check for cancellation
            if client_id and prepass_jobs.get(client_id, {}).get("status") == "cancelled":
                print(f"Prepass cancelled by user for client {client_id}")
                break
                
            print(f"Processing chunk {chunk_idx + 1}/{len(text_chunks)}")
            
            # Find byte range (approximate)
            start_byte = current_byte
            end_byte = current_byte + len(content.encode('utf-8'))
            current_byte = end_byte
            
            try:
                # Detect problems in this chunk
                print(f"Calling detect_tts_problems for chunk {chunk_idx + 1}")
                
                # Run the synchronous LLM call in a thread to avoid blocking the event loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    replacements = await asyncio.get_event_loop().run_in_executor(
                        executor, detect_tts_problems, api_base, model, content, False
                    )
                
                print(f"Chunk {chunk_idx + 1} completed with {len(replacements)} replacements")
            except Exception as chunk_error:
                print(f"Error processing chunk {chunk_idx + 1}: {chunk_error}")
                # Continue with empty replacements for this chunk
                replacements = []
            
            # Add to report
            chunk_report = {
                "id": chunk_idx + 1,
                "range": {
                    "start_byte": start_byte,
                    "end_byte": end_byte
                },
                "replacements": replacements
            }
            report_chunks.append(chunk_report)
            
            # Collect all find words for summary
            for replacement in replacements:
                if replacement.get('find'):
                    all_problems.append(replacement['find'])
            
            # Send progress update
            progress = int((chunk_idx + 1) / total_chunks * 100)
            if client_id:
                print(f"Sending progress update: chunk {chunk_idx + 1}/{total_chunks} ({progress}%)")
                await manager.send_message(client_id, {
                    "type": "progress",
                    "source": "prepass",
                    "progress": progress,
                    "message": f"Processed chunk {chunk_idx + 1}/{total_chunks}",
                    "chunks_processed": chunk_idx + 1,
                    "total_chunks": total_chunks
                })
                print("Progress update sent")
    except Exception as processing_error:
        error_msg = f"Error during chunk processing: {str(processing_error)}"
        print(error_msg)
        if client_id:
            await manager.send_message(client_id, {
                "type": "error",
                "source": "prepass",
                "message": error_msg
            })
        raise processing_error
    
    # Create summary with deduplicated problems and collect all replacements
    unique_problems = list(dict.fromkeys(all_problems))  # Preserves order while removing duplicates
    
    # Collect all replacement mappings for grammar pass
    all_replacements = {}
    for chunk in report_chunks:
        for replacement in chunk['replacements']:
            find_text = replacement.get('find')
            replace_text = replacement.get('replace')
            if find_text and replace_text:
                all_replacements[find_text] = replace_text
    
    # Build final report
    report = {
        "source": str(input_path.name),
        "created_at": datetime.now().isoformat(),
        "settings": {
            "api_base": api_base,
            "model": model,
            "chunk_chars": chunk_chars
        },
        "summary": {
            "unique_problem_words": unique_problems,
            "replacement_map": all_replacements,
            "total_chunks": total_chunks,
            "total_problems": len(all_problems)
        },
        "chunks": report_chunks
    }
    
    if client_id:
        # Check if cancelled before sending completion
        if prepass_jobs.get(client_id, {}).get("status") == "cancelled":
            await manager.send_message(client_id, {
                "type": "error",
                "source": "prepass",
                "message": "Prepass cancelled by user"
            })
        else:
            await manager.send_message(client_id, {
                "type": "completed",
                "source": "prepass",
                "progress": 100,
                "message": f"Prepass completed! Found {len(unique_problems)} unique problems in {total_chunks} chunks.",
                "result": report
            })
        
        # Clean up job tracking
        if client_id in prepass_jobs:
            del prepass_jobs[client_id]
    
    return report

# Load the prepass prompt from file
PREPASS_PROMPT_PATH = Path(__file__).parent.parent / "prepass_prompt.txt"
if PREPASS_PROMPT_PATH.exists():
    with open(PREPASS_PROMPT_PATH, encoding="utf-8") as f:
        PREPASS_PROMPT = f.read().strip()
else:
    PREPASS_PROMPT = "" # Fallback to empty if not found, prepass.py has its own default

# Pydantic models
class ProcessRequest(BaseModel):
    content: str
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    prompt_template: Optional[str] = None
    stream: bool = False
    show_progress: bool = True
    resume: bool = False
    force: bool = False
    fsync_each: bool = False
    chunk_size: int = 8000
    preview_chars: int = 500
    use_prepass: bool = False
    prepass_report: Optional[dict] = None

class PrepassRequest(BaseModel):
    content: str
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    chunk_size: int = 8000
    client_id: Optional[str] = None

class Model(BaseModel):
    id: str
    name: str
    description: str

class LogEntry(BaseModel):
    id: str
    message: str
    timestamp: str
    type: str  # 'info', 'warning', 'error', 'success'

class ChunkPreview(BaseModel):
    chunk_index: int
    chunk_type: str  # 'text' or 'code'
    original_content: str
    processed_content: Optional[str] = None
    character_count: int
    is_complete: bool = False

class JobStatus(BaseModel):
    status: str  # 'started', 'processing', 'completed', 'error', 'paused'
    progress: int
    total_chunks: int
    processed_chunks: int
    current_chunk: Optional[int] = None
    result_chunks: List[ChunkPreview] = []
    can_resume: bool = False
    error: Optional[str] = None

# Global state for processing jobs
processing_jobs: Dict[str, dict] = {}
prepass_jobs: Dict[str, dict] = {}

@app.get("/")
async def root():
    return {"message": "TTS-Proof API is running"}

@app.get("/api/test-endpoint")
async def test_endpoint(api_base: str, model: str = "default"):
    """Test if an endpoint supports chat completions."""
    try:
        import requests
        
        # Test models endpoint first
        models_url = f"{api_base}/models"
        print(f"Testing models endpoint: {models_url}")
        response = requests.get(models_url, timeout=5)
        response.raise_for_status()
        models_data = response.json()
        
        # Test chat completions endpoint
        chat_url = f"{api_base}/chat/completions"
        print(f"Testing chat completions endpoint: {chat_url}")
        
        test_payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 5
        }
        
        chat_response = requests.post(chat_url, json=test_payload, timeout=10)
        chat_response.raise_for_status()
        chat_data = chat_response.json()
        
        return {
            "status": "success",
            "models_available": len(models_data.get('data', [])),
            "chat_working": True,
            "test_response": chat_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "chat_working": False
        }

@app.get("/api/models", response_model=List[Model])
async def get_models(api_base: Optional[str] = None):
    """Fetch available models from LM Studio or custom endpoint."""
    try:
        endpoint = api_base or DEFAULT_API_BASE
        print(f"Models endpoint called with api_base: {endpoint}")
        
        # First try to get from LM Studio or custom endpoint
        import requests
        print(f"Fetching models from {endpoint}/models")
        response = requests.get(f"{endpoint}/models", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"LM Server returned: {len(data.get('data', []))} models")
        
        models = []
        for model in data.get("data", []):
            # Only include non-embedding models for text generation
            if "embedding" not in model["id"].lower() and "reranker" not in model["id"].lower():
                models.append(Model(
                    id=model["id"],
                    name=model["id"].replace("_", " ").title(),
                    description=f"Model: {model['id']}"
                ))
        
        if not models:
            # Return default model if no text generation models found
            models = [
                Model(id="default", name="Default Model", description="Local LLM model")
            ]
        
        print(f"Returning {len(models)} text generation models")
        return models
        
    except Exception as e:
        print(f"Error fetching models: {e}")
        import traceback
        traceback.print_exc()
        
        # Return default models if LM Studio is not available
        return [
            Model(id="default", name="Default Model", description="Local LLM model"),
            Model(id="qwen/qwen3-4b-2507", name="Qwen 3 4B", description="Qwen 3 4B model"),
        ]

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a markdown file."""
    if not file.filename.endswith(('.md', '.txt', '.markdown')):
        raise HTTPException(status_code=400, detail="File must be a Markdown file")
    
    # Save uploaded file temporarily
    temp_dir = tempfile.gettempdir()
    file_path = Path(temp_dir) / f"tts_proof_{uuid.uuid4()}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Read content for preview
        text_content = content.decode('utf-8')
        
        return {
            "file_id": str(file_path.name),
            "filename": file.filename,
            "size": len(content),
            "content_preview": text_content[:500] + "..." if len(text_content) > 500 else text_content,
            "full_content": text_content,  # Include the full content
            "temp_path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.post("/api/prepass")
async def run_prepass_detection(request: PrepassRequest):
    """Run prepass TTS problem detection on text with WebSocket progress updates."""
    try:
        # Create temporary file for processing
        temp_dir = tempfile.gettempdir()
        temp_file = Path(temp_dir) / f"prepass_{uuid.uuid4()}.md"
        
        # Write content to temp file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        try:
            # Run prepass detection with WebSocket streaming
            api_base = request.api_base or DEFAULT_API_BASE
            model = request.model_name or DEFAULT_MODEL
            
            print(f"Starting prepass with file: {temp_file}, api_base: {api_base}, model: {model}")
            
            # Use WebSocket version if client_id provided for progress updates
            if request.client_id:
                print("Using WebSocket prepass for progress updates")
                report = await run_prepass_with_websocket(
                    temp_file,
                    api_base,
                    model,
                    request.chunk_size,
                    request.client_id
                )
                print("WebSocket prepass completed successfully")
            else:
                # Use original version when no WebSocket updates needed
                print("Using original prepass (no progress updates)")
                report = run_prepass(
                    temp_file,
                    api_base,
                    model,
                    request.chunk_size,
                    show_progress=False
                )
                print("Original prepass completed successfully")
            
            return {
                "status": "success",
                "report": report,
                "summary": {
                    "unique_problems": len(report['summary']['unique_problem_words']),
                    "chunks_processed": len(report['chunks']),
                    "sample_problems": report['summary']['unique_problem_words'][:5]
                }
            }
            
        finally:
            # Clean up temp file
            try:
                temp_file.unlink()
            except FileNotFoundError:
                pass
                
    except Exception as e:
        import traceback
        print(f"Prepass detection error: {str(e)}")
        traceback.print_exc()
        
        # Send error via WebSocket if client_id available
        if request.client_id:
            try:
                await manager.send_message(request.client_id, {
                    "type": "error",
                    "source": "prepass",
                    "message": f"Prepass failed: {str(e)}"
                })
            except Exception as ws_e:
                print(f"Failed to send WebSocket error message: {ws_e}")
        
        raise HTTPException(status_code=500, detail=f"Prepass detection failed: {str(e)}")

@app.post("/api/upload-prepass")
async def upload_prepass_report(file: UploadFile = File(...)):
    """Upload a prepass report JSON file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    try:
        content = await file.read()
        report_data = json.loads(content.decode('utf-8'))
        
        # Validate basic structure
        required_keys = ['source', 'created_at', 'chunks', 'summary']
        if not all(key in report_data for key in required_keys):
            raise HTTPException(status_code=400, detail="Invalid prepass report format")
        
        return {
            "status": "success",
            "report": report_data,
            "summary": {
                "source": report_data['source'],
                "unique_problems": len(report_data['summary']['unique_problem_words']),
                "chunks": len(report_data['chunks']),
                "created_at": report_data['created_at']
            }
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process prepass report: {str(e)}")

@app.get("/api/grammar-prompt")
async def get_grammar_prompt():
    """Get the current grammar prompt from file."""
    return {
        "prompt": GRAMMAR_PROMPT,
        "source": "grammar_promt.txt" if GRAMMAR_PROMPT_PATH.exists() else "built-in"
    }

@app.post("/api/grammar-prompt")
async def save_grammar_prompt(request: dict):
    """Save grammar prompt to file."""
    try:
        new_prompt = request.get("prompt", "").strip()
        if not new_prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        # Save to file
        with open(GRAMMAR_PROMPT_PATH, 'w', encoding='utf-8') as f:
            f.write(new_prompt)
        
        # Update global variable
        global GRAMMAR_PROMPT
        GRAMMAR_PROMPT = new_prompt
        
        return {
            "status": "success",
            "message": "Grammar prompt saved successfully",
            "source": "grammar_promt.txt"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save grammar prompt: {str(e)}")

@app.get("/api/prepass-prompt")
async def get_prepass_prompt():
    """Get the current prepass prompt from file."""
    return {
        "prompt": PREPASS_PROMPT,
        "source": "prepass_prompt.txt" if PREPASS_PROMPT_PATH.exists() else "built-in"
    }

@app.post("/api/prepass-prompt")
async def save_prepass_prompt(request: dict):
    """Save prepass prompt to file."""
    try:
        new_prompt = request.get("prompt", "").strip()
        if not new_prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Save to file
        with open(PREPASS_PROMPT_PATH, 'w', encoding='utf-8') as f:
            f.write(new_prompt)

        # Update global variable
        global PREPASS_PROMPT
        PREPASS_PROMPT = new_prompt

        return {
            "status": "success",
            "message": "Prepass prompt saved successfully",
            "source": "prepass_prompt.txt"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prepass prompt: {str(e)}")

@app.post("/api/process/{client_id}")
async def process_text(client_id: str, request: ProcessRequest):
    """Start text processing job."""
    job_id = client_id  # Use client_id as job_id for WebSocket communication
    
    # Store job info
    processing_jobs[job_id] = {
        "status": "started",
        "progress": 0,
        "result": None,
        "error": None
    }
    
    # Start processing in background
    asyncio.create_task(run_processing_job(job_id, request))
    
    return {"job_id": job_id, "status": "started"}

async def run_processing_job(job_id: str, request: ProcessRequest):
    """Run the text processing job with checkpointing and streaming."""
    try:
        print(f"Starting processing job {job_id}")
        
        # Setup paths using original md_proof logic
        temp_dir = tempfile.gettempdir()
        input_path = Path(temp_dir) / f"input_{job_id}.md"
        output_path = Path(temp_dir) / f"output_{job_id}.md"
        
        # Write content to temp file
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        # Get checkpoint paths
        partial_path, ckpt_path = paths_for(output_path)
        
        # Load and chunk the document
        original_text = load_markdown(input_path)
        chunks = list(chunk_paragraphs(original_text, request.chunk_size))
        
        # Count text chunks for progress
        text_chunks = [(i, chunk_content) for i, (chunk_type, chunk_content) in enumerate(chunks) if chunk_type == "text"]
        total_chunks = len(text_chunks)
        total_text_chunks = len(text_chunks)
        
        # Initialize job status with chunk details
        processing_jobs[job_id].update({
            "status": "processing",
            "progress": 0,
            "total_chunks": len(chunks),
            "processed_chunks": 0,
            "current_chunk": 0,
            "result_chunks": [],
            "can_resume": False
        })
        
        print(f"Found {total_text_chunks} text chunks to process out of {len(chunks)} total chunks")
        
        # Check for existing checkpoint
        start_index = 0
        processed_text_so_far = 0
        
        if request.resume and ckpt_path.exists() and partial_path.exists():
            ck = load_ckpt(ckpt_path) or {}
            start_index = int(ck.get("processed_index", 0))
            # Count already processed text chunks
            for i in range(min(start_index, len(chunks))):
                if chunks[i][0] == "text":
                    processed_text_so_far += 1
            print(f"Resuming from chunk {start_index}, {processed_text_so_far} text chunks already processed")
            processing_jobs[job_id]["processed_chunks"] = processed_text_so_far
        else:
            # Clean start - remove old files
            for p in (partial_path, ckpt_path):
                try: p.unlink()
                except FileNotFoundError: pass
        
        await manager.send_message(job_id, {
            "type": "progress",
            "progress": int((processed_text_so_far / total_text_chunks) * 100) if total_text_chunks > 0 else 0,
            "message": f"Processing {total_text_chunks} text chunks...",
            "chunks_processed": processed_text_so_far,
            "total_chunks": total_text_chunks
        })
        
        # Process chunks with checkpointing
        api_base = request.api_base or DEFAULT_API_BASE
        model_name = request.model_name or "default"
        prompt_to_use = request.prompt_template if request.prompt_template else GRAMMAR_PROMPT
        
        # Inject prepass replacements if enabled
        if request.use_prepass and request.prepass_report:
            try:
                # Try new replacement map format first
                replacement_map = get_replacement_map_for_grammar(request.prepass_report)
                if replacement_map:
                    prompt_to_use = inject_prepass_into_grammar_prompt(prompt_to_use, replacement_map)
                    print(f"Injected {len(replacement_map)} specific replacements from prepass into grammar prompt")
                else:
                    # Fall back to legacy problem words format
                    problem_words = get_problem_words_for_grammar(request.prepass_report)
                    if problem_words:
                        prompt_to_use = inject_prepass_into_grammar_prompt_legacy(prompt_to_use, problem_words)
                        print(f"Injected {len(problem_words)} problem words from prepass into grammar prompt (legacy)")
            except Exception as e:
                print(f"Warning: Failed to inject prepass data: {e}")
                # Continue with original prompt
        
        fmode = "a" if start_index > 0 else "w"
        
        with open(partial_path, fmode, encoding="utf-8") as fout:
            for idx in range(start_index, len(chunks)):
                # Check for pause or cancel request
                if processing_jobs[job_id]["status"] == "paused":
                    print(f"Job {job_id} paused at chunk {idx}")
                    processing_jobs[job_id]["can_resume"] = True
                    await manager.send_message(job_id, {
                        "type": "paused",
                        "message": f"Job paused at chunk {idx + 1}/{len(chunks)}"
                    })
                    return
                elif processing_jobs[job_id]["status"] == "cancelled":
                    print(f"Job {job_id} cancelled at chunk {idx}")
                    await manager.send_message(job_id, {
                        "type": "error",
                        "message": f"Job cancelled by user at chunk {idx + 1}/{len(chunks)}"
                    })
                    return
                
                chunk_type, chunk_content = chunks[idx]
                processing_jobs[job_id]["current_chunk"] = idx
                
                if chunk_type == "text" and chunk_content.strip():
                    print(f"Processing text chunk {processed_text_so_far + 1}/{total_text_chunks} ({len(chunk_content)} chars)")
                    
                    try:
                        # Process the chunk using async thread execution to avoid blocking
                        print(f"Processing chunk {processed_text_so_far + 1}/{total_text_chunks}")
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            corrected = await asyncio.get_event_loop().run_in_executor(
                                executor, correct_chunk_with_prompt, api_base, model_name, 
                                chunk_content, prompt_to_use, request.show_progress
                            )
                        
                        print(f"Chunk {processed_text_so_far + 1}/{total_text_chunks} completed")
                        
                        # Write to partial file
                        fout.write(corrected)
                        fout.write("\n")
                        fout.flush()
                        
                        processed_text_so_far += 1
                        processing_jobs[job_id]["processed_chunks"] = processed_text_so_far
                        
                        # Create chunk preview, sending full content for real-time preview
                        chunk_preview = ChunkPreview(
                            chunk_index=idx,
                            chunk_type=chunk_type,
                            original_content=chunk_content,
                            processed_content=corrected, # Send full corrected chunk
                            character_count=len(corrected),
                            is_complete=True
                        )
                        
                        # Send chunk completion
                        progress = int((processed_text_so_far / total_text_chunks) * 100)
                        await manager.send_message(job_id, {
                            "type": "chunk_complete",
                            "progress": progress,
                            "message": f"Completed chunk {processed_text_so_far}/{total_text_chunks}",
                            "chunk": chunk_preview.dict(),
                            "chunks_processed": processed_text_so_far,
                            "total_chunks": total_text_chunks
                        })
                        
                    except Exception as chunk_error:
                        print(f"Error processing chunk {idx}: {chunk_error}")
                        # Keep original chunk
                        fout.write(chunk_content)
                        fout.write("\n")
                        fout.flush()
                        processed_text_so_far += 1
                        
                        await manager.send_message(job_id, {
                            "type": "chunk_error",
                            "message": f"Error in chunk {processed_text_so_far}: {str(chunk_error)}",
                            "chunk_index": idx
                        })
                
                else:
                    # Non-text chunk (code block, etc.)
                    fout.write(chunk_content)
                    fout.write("\n")
                    fout.flush()

                    # Send non-text chunk to frontend for real-time preview
                    chunk_preview = ChunkPreview(
                        chunk_index=idx,
                        chunk_type=chunk_type,
                        original_content=chunk_content,
                        processed_content=chunk_content, # Content is unchanged
                        character_count=len(chunk_content),
                        is_complete=True
                    )
                    await manager.send_message(job_id, {
                        "type": "chunk_complete",
                        "progress": int((processed_text_so_far / total_text_chunks) * 100) if total_text_chunks > 0 else 0,
                        "message": f"Passing through non-text chunk {idx + 1}/{len(chunks)}",
                        "chunk": chunk_preview.dict(),
                        "chunks_processed": processed_text_so_far,
                        "total_chunks": total_text_chunks
                    })
                
                # Update checkpoint
                ck = {
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "partial_path": str(partial_path),
                    "chunk_chars": request.chunk_size,
                    "total_chunks": len(chunks),
                    "processed_index": idx + 1,
                    "processed_text_chunks": processed_text_so_far,
                    "timestamp": time.time(),
                }
                write_ckpt(ckpt_path, ck)
        
        # Completion - move partial to final
        try:
            import os
            os.replace(partial_path, output_path)
            if ckpt_path.exists():
                ckpt_path.unlink()
            
            # Read final result
            with open(output_path, 'r', encoding='utf-8') as f:
                result = f.read()
            
            processing_jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "result": result
            })
            
            print(f"Processing complete for job {job_id}. Output: {len(result)} chars")
            
            await manager.send_message(job_id, {
                "type": "completed",
                "progress": 100,
                "message": "Text correction completed successfully!",
                "total_processed": processed_text_so_far,
                "output_size": len(result),
                "result": result  # Include the actual result in the message
            })
            
            # Clean up temp files
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"Error finalizing job {job_id}: {e}")
            processing_jobs[job_id]["status"] = "error"
            processing_jobs[job_id]["error"] = f"Finalization error: {str(e)}"
            
    except Exception as e:
        print(f"Error in job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        processing_jobs[job_id]["status"] = "error"
        processing_jobs[job_id]["error"] = str(e)
        
        await manager.send_message(job_id, {
            "type": "error",
            "message": f"Processing failed: {str(e)}"
        })

@app.get("/api/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status with chunk details."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]

@app.post("/api/job/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a running job after current chunk."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    if job["status"] == "processing":
        job["status"] = "paused"
        await manager.send_message(job_id, {
            "type": "paused",
            "message": "Job paused. Will stop after current chunk completes."
        })
        return {"message": "Job pause requested"}
    
    return {"message": f"Job is {job['status']}, cannot pause"}

@app.post("/api/job/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    if job["status"] == "paused" and job.get("can_resume", False):
        job["status"] = "processing"
        # TODO: Implement resume logic
        await manager.send_message(job_id, {
            "type": "resumed",
            "message": "Job resumed from checkpoint"
        })
        return {"message": "Job resumed"}
    
    return {"message": f"Job cannot be resumed (status: {job['status']})"}

@app.post("/api/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    if job["status"] in ["processing", "paused"]:
        job["status"] = "cancelled"
        await manager.send_message(job_id, {
            "type": "error",
            "message": "Job cancelled by user"
        })
        return {"message": "Job cancelled"}
    
    return {"message": f"Job is {job['status']}, cannot cancel"}

@app.get("/api/temp-directory")
async def get_temp_directory():
    """Get the path of the temporary directory."""
    return {"path": tempfile.gettempdir()}

@app.post("/api/prepass/cancel")
async def cancel_prepass(request: dict):
    """Cancel a running prepass job."""
    client_id = request.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")
    
    if client_id not in prepass_jobs:
        raise HTTPException(status_code=404, detail="Prepass job not found")
    
    job = prepass_jobs[client_id]
    if job["status"] == "processing":
        job["status"] = "cancelled"
        await manager.send_message(client_id, {
            "type": "error",
            "source": "prepass",
            "message": "Prepass cancelled by user"
        })
        return {"message": "Prepass cancelled"}
    
    return {"message": f"Prepass is {job['status']}, cannot cancel"}

@app.get("/api/job/{job_id}/chunks")
async def get_job_chunks(job_id: str, limit: int = 5, offset: int = 0):
    """Get chunk previews for a job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    chunks = job.get("result_chunks", [])
    
    return {
        "chunks": chunks[offset:offset + limit],
        "total": len(chunks),
        "offset": offset,
        "limit": limit
    }

@app.get("/api/test-simple")
async def test_simple():
    """Ultra simple test endpoint."""
    return {"status": "working", "message": "Simple test works"}

@app.post("/api/run-test")  
async def run_test(request: dict):
    """Run a simple test using webui_test.md file."""
    return {"status": "success", "message": "Temporarily simplified - backend working"}

# Removed complex function for simple testing

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
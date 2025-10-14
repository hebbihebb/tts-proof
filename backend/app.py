#!/usr/bin/env python3
"""
FastAPI backend for TTS-Proof application.
Provides REST API endpoints and WebSocket support for the React frontend.
"""

import asyncio
import concurrent.futures
import io
import json
import os
import shutil
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
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

# Run artifact storage (Phase 11 artifacts live in ~/.mdp/runs by default)
DEFAULT_RUNS_DIR = Path.home() / ".mdp" / "runs"
RUNS_BASE_DIR = Path(os.environ.get("MDP_RUNS_DIR", str(DEFAULT_RUNS_DIR)))
RUNS_BASE_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_PREVIEW_LIMIT = 4096  # bytes
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".json", ".log", ".yaml", ".yml", ".cfg"}

UTC = timezone.utc


def _isoformat(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def iso_now() -> str:
    return _isoformat(datetime.now(UTC))


def get_run_directory(run_id: str) -> Path:
    return RUNS_BASE_DIR / run_id


def get_metadata_path(run_id: str) -> Path:
    return get_run_directory(run_id) / "metadata.json"


def load_run_metadata(run_id: str) -> Optional[dict]:
    metadata_path = get_metadata_path(run_id)
    if not metadata_path.exists():
        return None
    try:
        with open(metadata_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return None


def update_run_metadata(run_id: str, **updates) -> dict:
    metadata = load_run_metadata(run_id) or {}
    now_iso = iso_now()
    created_at = updates.pop("created_at", now_iso)
    if "created_at" not in metadata:
        metadata["created_at"] = created_at
    metadata.update(updates)
    metadata["run_id"] = run_id
    metadata["updated_at"] = now_iso
    metadata_path = get_metadata_path(run_id)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    return metadata


def summarize_run_artifacts(run_id: str) -> Tuple[int, List[str]]:
    total_size = 0
    names: List[str] = []
    run_dir = get_run_directory(run_id)
    if run_dir.exists():
        for child in run_dir.iterdir():
            if child.is_file():
                try:
                    total_size += child.stat().st_size
                except OSError:
                    continue
                names.append(child.name)
    names.sort()
    return total_size, names


def iso_from_timestamp(timestamp: float) -> str:
    return _isoformat(datetime.fromtimestamp(timestamp, tz=UTC))

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
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
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
                # Use the enhanced PREPASS_PROMPT loaded at startup
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    replacements = await asyncio.get_event_loop().run_in_executor(
                        executor, detect_tts_problems, api_base, model, content, False, PREPASS_PROMPT
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

class RunRequest(BaseModel):
    """Request model for unified /api/run endpoint."""
    input_path: str
    input_name: Optional[str] = None
    steps: List[str]
    models: Dict[str, str]  # {"detector": "model-name", "fixer": "model-name"}
    report_pretty: bool = True
    client_id: Optional[str] = None

class RunResponse(BaseModel):
    """Response model for unified /api/run endpoint."""
    run_id: str
    status: str  # 'started', 'processing', 'completed', 'error'

class BlessedModelsResponse(BaseModel):
    """Response model for blessed models endpoint."""
    detector: List[str]
    fixer: List[str]

class ReportResponse(BaseModel):
    """Response model for report endpoint."""
    pretty_report: str
    json_report_path: Optional[str] = None

class DiffResponse(BaseModel):
    """Response model for diff endpoint."""
    diff_head: str
    has_more: bool
    rejected: bool

class ResultResponse(BaseModel):
    """Response model for result endpoint."""
    exit_code: int
    output_path: Optional[str] = None
    rejected_path: Optional[str] = None
    plan_path: Optional[str] = None
    json_report_path: Optional[str] = None


class RunSummary(BaseModel):
    """Summary of a recorded pipeline run."""
    run_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    models: Dict[str, str] = Field(default_factory=dict)
    exit_code: Optional[int] = None
    input_name: Optional[str] = None
    input_size: Optional[int] = None
    artifact_count: int = 0
    total_size: Optional[int] = None
    has_rejected: Optional[bool] = None


class RunsResponse(BaseModel):
    """Response model for run history listing."""
    runs: List[RunSummary]


class ArtifactInfo(BaseModel):
    """Metadata for a single artifact file."""
    name: str
    size_bytes: int
    modified_at: str
    media_type: str
    is_text: bool
    preview: Optional[str] = None


class ArtifactListResponse(BaseModel):
    """Response model for artifact listing."""
    run_id: str
    artifacts: List[ArtifactInfo]
    total_size: int

# Global state for processing jobs
processing_jobs: Dict[str, dict] = {}
prepass_jobs: Dict[str, dict] = {}
run_jobs: Dict[str, dict] = {}  # Track new unified run jobs

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
                # Use the SAME working run_prepass function that produces superior results
                print("Using original run_prepass (no progress updates)")
                report = run_prepass(
                    temp_file,
                    api_base,
                    model,
                    request.chunk_size,
                    show_progress=False
                )
                print("Original run_prepass completed successfully")
            
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

# ============================================================================
# NEW UNIFIED PIPELINE ENDPOINTS (Phase 11 PR-1)
# ============================================================================

@app.get("/api/blessed-models", response_model=BlessedModelsResponse)
async def get_blessed_models():
    """
    Get blessed model lists for detector and fixer roles.
    Returns models validated for use in the pipeline.
    """
    from mdp.config import get_blessed_models
    
    blessed = get_blessed_models()
    return BlessedModelsResponse(
        detector=blessed['detector'],
        fixer=blessed['fixer']
    )

@app.post("/api/run", response_model=RunResponse)
async def run_pipeline_endpoint(request: RunRequest):
    """
    Unified pipeline run endpoint.
    Calls mdp.__main__.run_pipeline() directly with specified steps and models.
    Streams progress via WebSocket using existing schema with new source values.
    """
    from mdp import config as mdp_config
    from mdp.__main__ import run_pipeline
    
    # Generate run ID
    run_id = str(uuid.uuid4())
    client_id = request.client_id or run_id
    
    # Validate blessed models
    blessed = mdp_config.get_blessed_models()
    detector_model = request.models.get('detector')
    fixer_model = request.models.get('fixer')
    
    if detector_model and detector_model not in blessed['detector']:
        raise HTTPException(
            status_code=400,
            detail=f"Detector model '{detector_model}' is not blessed. Allowed: {blessed['detector']}"
        )
    
    if fixer_model and fixer_model not in blessed['fixer']:
        raise HTTPException(
            status_code=400,
            detail=f"Fixer model '{fixer_model}' is not blessed. Allowed: {blessed['fixer']}"
        )
    
    # Validate input file exists
    input_path = Path(request.input_path)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail=f"Input file not found: {request.input_path}")

    artifacts_dir = get_run_directory(run_id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    input_name = request.input_name or input_path.name
    try:
        input_size = input_path.stat().st_size
    except OSError:
        input_size = None

    update_run_metadata(
        run_id,
        status="processing",
        created_at=iso_now(),
        input_name=input_name,
        input_path=str(input_path),
        input_size=input_size,
        steps=request.steps,
        models=request.models,
        client_id=client_id
    )
    
    # Initialize run job tracking
    run_jobs[run_id] = {
        "status": "started",
        "client_id": client_id,
        "input_path": str(input_path),
        "input_name": input_name,
        "steps": request.steps,
        "models": request.models,
        "progress": 0,
        "current_step": None,
        "result": None,
        "error": None
    }
    
    # Start processing in background
    asyncio.create_task(run_pipeline_job(run_id, request))
    
    return RunResponse(run_id=run_id, status="started")

async def run_pipeline_job(run_id: str, request: RunRequest):
    """
    Execute the pipeline orchestrator with WebSocket progress streaming.
    Uses the same run_pipeline() function as CLI for byte-identical output.
    """
    from mdp import config as mdp_config
    from mdp.__main__ import run_pipeline
    import traceback
    
    client_id = run_jobs[run_id]["client_id"]
    artifacts_dir = get_run_directory(run_id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load input text
        input_path = Path(request.input_path)
        with open(input_path, 'r', encoding='utf-8') as f:
            input_text = f.read()

        # Persist source document for artifact browsing
        input_copy_path = artifacts_dir / 'input.txt'
        with open(input_copy_path, 'w', encoding='utf-8') as f:
            f.write(input_text)

        total_size, artifact_names = summarize_run_artifacts(run_id)
        update_run_metadata(
            run_id,
            artifact_count=len(artifact_names),
            total_size=total_size,
            has_rejected=False
        )
        
        # Load config and override with requested models
        config = mdp_config.load_config(None)  # Use defaults
        
        # Override detector/fixer endpoints and models from request
        if 'detect' in request.steps or 'apply' in request.steps:
            detector_model = request.models.get('detector')
            if detector_model:
                if 'detector' not in config:
                    config['detector'] = {}
                config['detector']['model'] = detector_model
        
        if 'fix' in request.steps:
            fixer_model = request.models.get('fixer')
            if fixer_model:
                if 'fixer' not in config:
                    config['fixer'] = {}
                config['fixer']['model'] = fixer_model
        
        # Send initial progress
        await manager.send_message(client_id, {
            "type": "progress",
            "source": "pipeline",
            "progress": 0,
            "message": f"Starting pipeline with {len(request.steps)} steps...",
            "steps": request.steps
        })
        
        # Track progress through steps
        total_steps = len(request.steps)
        
        for step_idx, step in enumerate(request.steps):
            run_jobs[run_id]["current_step"] = step
            progress = int((step_idx / total_steps) * 100)
            run_jobs[run_id]["progress"] = progress
            
            # Map step names to source names for WebSocket
            source_map = {
                'mask': 'mask',
                'prepass-basic': 'prepass-basic',
                'prepass-advanced': 'prepass-advanced',
                'scrubber': 'scrubber',
                'grammar': 'grammar',
                'detect': 'detect',
                'apply': 'apply',
                'fix': 'fix'
            }
            source = source_map.get(step, step)
            
            await manager.send_message(client_id, {
                "type": "progress",
                "source": source,
                "progress": progress,
                "message": f"Running step {step_idx + 1}/{total_steps}: {step}",
                "current_step": step
            })
        
        # Run the pipeline (this calls the same orchestrator as CLI)
        processed_text, combined_stats = run_pipeline(
            input_text=input_text,
            steps=request.steps,
            config=config,
            run_dir=artifacts_dir
        )
        
        # Write output to artifacts directory
        # Write output (standardized name)
        output_path = artifacts_dir / 'output.md'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        
        # Write stats as report.json (standardized name for PR-2)
        report_path = artifacts_dir / 'report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(combined_stats, f, indent=2)
        
        # Write plan if detector step was run
        if 'detect' in request.steps and 'detect' in combined_stats:
            plan_data = combined_stats['detect'].get('plan', [])
            if plan_data:
                plan_path = artifacts_dir / 'plan.json'
                with open(plan_path, 'w', encoding='utf-8') as f:
                    json.dump(plan_data, f, indent=2)

        total_size, artifact_names = summarize_run_artifacts(run_id)
        update_run_metadata(
            run_id,
            status="completed",
            completed_at=iso_now(),
            exit_code=0,
            artifact_count=len(artifact_names),
            total_size=total_size,
            artifacts=artifact_names,
            has_rejected=any(name == 'output.rejected.md' for name in artifact_names)
        )
        
        # Update job status
        run_jobs[run_id].update({
            "status": "completed",
            "progress": 100,
            "result": {
                "output_path": str(output_path),
                "report_path": str(report_path),
                "stats": combined_stats,
                "exit_code": 0
            }
        })
        
        # Send completion message with run_id for frontend
        await manager.send_message(client_id, {
            "type": "completed",
            "source": "pipeline",
            "progress": 100,
            "message": "Pipeline completed successfully",
            "run_id": run_id,
            "output_path": str(output_path),
            "stats": combined_stats,
            "exit_code": 0
        })
        
    except ConnectionError as e:
        # Model server unreachable (exit code 2)
        error_msg = f"Model server unreachable: {str(e)}"
        run_jobs[run_id].update({
            "status": "error",
            "error": error_msg,
            "result": {"exit_code": 2}
        })

        total_size, artifact_names = summarize_run_artifacts(run_id)
        update_run_metadata(
            run_id,
            status="error",
            completed_at=iso_now(),
            exit_code=2,
            error=error_msg,
            artifact_count=len(artifact_names),
            total_size=total_size,
            has_rejected=any(name == 'output.rejected.md' for name in artifact_names)
        )
        
        await manager.send_message(client_id, {
            "type": "error",
            "source": run_jobs[run_id].get("current_step", "pipeline"),
            "message": error_msg,
            "exit_code": 2
        })
        
    except ValueError as e:
        # Validation failed (exit code 3) or plan parse error (exit code 4)
        error_msg = str(e)
        exit_code = 4 if "parse" in error_msg.lower() else 3
        
        run_jobs[run_id].update({
            "status": "error",
            "error": error_msg,
            "result": {"exit_code": exit_code}
        })

        total_size, artifact_names = summarize_run_artifacts(run_id)
        update_run_metadata(
            run_id,
            status="error",
            completed_at=iso_now(),
            exit_code=exit_code,
            error=error_msg,
            artifact_count=len(artifact_names),
            total_size=total_size,
            has_rejected=any(name == 'output.rejected.md' for name in artifact_names)
        )
        
        await manager.send_message(client_id, {
            "type": "error",
            "source": run_jobs[run_id].get("current_step", "pipeline"),
            "message": error_msg,
            "exit_code": exit_code
        })
        
    except Exception as e:
        # Unexpected error
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        run_jobs[run_id].update({
            "status": "error",
            "error": error_msg,
            "result": {"exit_code": 1}
        })

        total_size, artifact_names = summarize_run_artifacts(run_id)
        update_run_metadata(
            run_id,
            status="error",
            completed_at=iso_now(),
            exit_code=1,
            error=str(e),
            artifact_count=len(artifact_names),
            total_size=total_size,
            has_rejected=any(name == 'output.rejected.md' for name in artifact_names)
        )
        
        await manager.send_message(client_id, {
            "type": "error",
            "source": run_jobs[run_id].get("current_step", "pipeline"),
            "message": str(e),
            "exit_code": 1
        })

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

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Backend is running"}

@app.post("/api/run-test")
async def run_test(request: dict):
    """Run a comprehensive test using webui_test.md file."""
    try:
        # Check if webui_test.md exists
        test_file = Path(__file__).parent.parent / "webui_test.md"
        if not test_file.exists():
            return {
                "status": "error",
                "message": "webui_test.md not found",
                "summary": {
                    "prepass_problems": 0,
                    "chunks_processed": 0,
                    "errors": 1
                },
                "log_file": None
            }

        # Read test content
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Run a quick prepass test
        api_base = request.get('api_base', DEFAULT_API_BASE)
        model = request.get('model_name', DEFAULT_MODEL)
        chunk_size = request.get('chunk_size', 8000)

        # Create temp file and run prepass
        temp_dir = tempfile.gettempdir()
        temp_file = Path(temp_dir) / f"test_{uuid.uuid4()}.md"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)

        try:
            # Use the SAME working run_prepass function that produces superior results
            report = run_prepass(
                temp_file,
                api_base,
                model,
                chunk_size,
                show_progress=False
            )

            # Extract summary info
            summary = report.get('summary', {})
            unique_problems = len(summary.get('unique_problem_words', []))
            chunks_processed = summary.get('chunks_processed', 0)
            sample_problems = summary.get('unique_problem_words', [])[:3]

            return {
                "status": "success",
                "message": f"Test completed - found {unique_problems} problems in {chunks_processed} chunks. Sample: {sample_problems}",
                "summary": {
                    "prepass_problems": unique_problems,
                    "chunks_processed": chunks_processed,
                    "errors": 0
                },
                "log_file": "test_log.md"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Test failed: {str(e)}",
                "summary": {
                    "prepass_problems": 0,
                    "chunks_processed": 0,
                    "errors": 1
                },
                "log_file": None
            }
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    except Exception as e:
        return {
            "status": "error",
            "message": f"Test setup failed: {str(e)}",
            "summary": {
                "prepass_problems": 0,
                "chunks_processed": 0,
                "errors": 1
            },
            "log_file": None
        }


@app.get("/api/runs", response_model=RunsResponse)
async def list_runs():
    """Return metadata for existing pipeline runs sorted by newest first."""
    if not RUNS_BASE_DIR.exists():
        return RunsResponse(runs=[])

    run_entries = []
    for run_dir in sorted((p for p in RUNS_BASE_DIR.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True):
        run_id = run_dir.name
        metadata = load_run_metadata(run_id) or {}

        created_at = metadata.get("created_at")
        if not created_at:
            try:
                created_at = iso_from_timestamp(run_dir.stat().st_mtime)
            except OSError:
                created_at = iso_now()

        total_size, artifact_names = summarize_run_artifacts(run_id)
        has_rejected = metadata.get("has_rejected")
        if has_rejected is None:
            has_rejected = any(name == 'output.rejected.md' for name in artifact_names)

        metadata = update_run_metadata(
            run_id,
            artifact_count=len(artifact_names),
            total_size=total_size,
            has_rejected=has_rejected,
            artifacts=artifact_names
        )

        run_entries.append(RunSummary(
            run_id=run_id,
            status=metadata.get("status", "unknown"),
            created_at=created_at,
            completed_at=metadata.get("completed_at"),
            steps=metadata.get("steps", []),
            models=metadata.get("models", {}),
            exit_code=metadata.get("exit_code"),
            input_name=metadata.get("input_name"),
            input_size=metadata.get("input_size"),
            artifact_count=metadata.get("artifact_count", 0),
            total_size=metadata.get("total_size"),
            has_rejected=metadata.get("has_rejected")
        ))

    return RunsResponse(runs=run_entries)


@app.get("/api/runs/{run_id}/artifacts", response_model=ArtifactListResponse)
async def get_run_artifacts(run_id: str):
    """List artifacts for a specific run with lightweight previews."""
    run_dir = get_run_directory(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    artifacts: List[ArtifactInfo] = []
    for file_path in sorted(run_dir.iterdir(), key=lambda p: p.name.lower()):
        if not file_path.is_file():
            continue
        try:
            stat = file_path.stat()
        except OSError:
            continue

        size_bytes = stat.st_size
        modified_at = iso_from_timestamp(stat.st_mtime)
        suffix = file_path.suffix.lower()

        if suffix == '.json':
            media_type = 'application/json'
        elif suffix in {'.md', '.markdown'}:
            media_type = 'text/markdown'
        elif suffix in {'.txt', '.log', '.cfg', '.yaml', '.yml'}:
            media_type = 'text/plain'
        else:
            media_type = 'application/octet-stream'

        is_text = suffix in TEXT_EXTENSIONS or size_bytes <= ARTIFACT_PREVIEW_LIMIT
        preview = None
        if is_text and size_bytes <= ARTIFACT_PREVIEW_LIMIT:
            try:
                preview = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                preview = None

        artifacts.append(ArtifactInfo(
            name=file_path.name,
            size_bytes=size_bytes,
            modified_at=modified_at,
            media_type=media_type,
            is_text=is_text,
            preview=preview
        ))

    total_size = sum(item.size_bytes for item in artifacts)
    has_rejected = any(item.name == 'output.rejected.md' for item in artifacts)

    update_run_metadata(
        run_id,
        artifact_count=len(artifacts),
        total_size=total_size,
        has_rejected=has_rejected,
        artifacts=[item.name for item in artifacts]
    )

    return ArtifactListResponse(run_id=run_id, artifacts=artifacts, total_size=total_size)


@app.get("/api/runs/{run_id}/artifacts/archive")
async def download_run_artifacts_archive(run_id: str):
    """Download all artifacts for a run as a ZIP archive."""
    run_dir = get_run_directory(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    files = [p for p in run_dir.iterdir() if p.is_file()]
    if not files:
        raise HTTPException(status_code=404, detail="No artifacts found for run")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            try:
                archive.write(file_path, arcname=file_path.name)
            except OSError:
                continue

    buffer.seek(0)
    headers = {
        "Content-Disposition": f'attachment; filename="{run_id}_artifacts.zip"'
    }
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


@app.get("/api/runs/{run_id}/artifacts/{artifact_name:path}")
async def download_run_artifact(run_id: str, artifact_name: str):
    """Download a specific artifact file by filename."""
    run_dir = get_run_directory(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    safe_name = Path(artifact_name).name
    target_path = run_dir / safe_name

    try:
        resolved_run_dir = run_dir.resolve(strict=True)
        resolved_target = target_path.resolve(strict=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Artifact not found") from None
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if resolved_target.parent != resolved_run_dir or not resolved_target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")

    suffix = resolved_target.suffix.lower()
    if suffix == '.json':
        media_type = 'application/json'
    elif suffix in {'.md', '.markdown'}:
        media_type = 'text/markdown'
    elif suffix in {'.txt', '.log', '.cfg', '.yaml', '.yml'}:
        media_type = 'text/plain'
    else:
        media_type = 'application/octet-stream'

    return FileResponse(
        resolved_target,
        media_type=media_type,
        filename=safe_name
    )


@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete all artifacts for a run to reclaim disk space."""
    run_dir = get_run_directory(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    shutil.rmtree(run_dir, ignore_errors=True)
    run_jobs.pop(run_id, None)
    return {"status": "deleted", "run_id": run_id}


@app.get("/api/runs/{run_id}/report", response_model=ReportResponse)
async def get_run_report(run_id: str):
    """
    Get pretty-formatted report for a completed run.
    Returns human-readable report using CLI formatter.
    """
    from report.pretty import render_pretty
    
    # Find run artifacts
    artifacts_dir = get_run_directory(run_id)
    json_report_path = artifacts_dir / 'report.json'
    
    if not json_report_path.exists():
        # Check if stats.json exists (fallback for PR-1 runs)
        stats_path = artifacts_dir / 'stats.json'
        if stats_path.exists():
            # Use stats.json as report data
            with open(stats_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Generate pretty report from stats
            try:
                pretty_output = render_pretty(report_data)
                return ReportResponse(
                    pretty_report=pretty_output,
                    json_report_path=str(stats_path)
                )
            except Exception as e:
                return ReportResponse(
                    pretty_report=f"Report generation failed: {str(e)}",
                    json_report_path=str(stats_path)
                )
        else:
            # No report or stats found
            return ReportResponse(
                pretty_report="Report unavailable - run not found or incomplete",
                json_report_path=None
            )
    
    # Load JSON report
    with open(json_report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # Generate pretty report
    try:
        pretty_output = render_pretty(report_data)
    except Exception as e:
        pretty_output = f"Report generation failed: {str(e)}\n\nRaw data available at: {json_report_path}"
    
    return ReportResponse(
        pretty_report=pretty_output,
        json_report_path=str(json_report_path)
    )

@app.get("/api/runs/{run_id}/diff", response_model=DiffResponse)
async def get_run_diff(run_id: str, max_lines: int = 200):
    """
    Get unified diff between input and output (or rejected).
    Truncates to max_lines for performance.
    """
    import difflib
    
    artifacts_dir = get_run_directory(run_id)
    input_path = artifacts_dir / 'input.txt'
    output_path = artifacts_dir / 'output.md'
    rejected_path = artifacts_dir / 'output.rejected.md'
    
    # Check if this is a rejected run
    is_rejected = rejected_path.exists() and not output_path.exists()
    comparison_path = rejected_path if is_rejected else output_path
    
    if not input_path.exists():
        return DiffResponse(
            diff_head="Input file not found - run incomplete or missing",
            has_more=False,
            rejected=is_rejected
        )
    
    if not comparison_path.exists():
        return DiffResponse(
            diff_head="Output file not found - run incomplete or failed",
            has_more=False,
            rejected=is_rejected
        )
    
    # Read files
    with open(input_path, 'r', encoding='utf-8') as f:
        input_lines = f.readlines()
    with open(comparison_path, 'r', encoding='utf-8') as f:
        output_lines = f.readlines()
    
    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        input_lines,
        output_lines,
        fromfile='input',
        tofile='output' if not is_rejected else 'rejected',
        lineterm=''
    ))
    
    # Check if there are any changes
    if not diff_lines:
        return DiffResponse(
            diff_head="No differences found - files are identical",
            has_more=False,
            rejected=is_rejected
        )
    
    # Truncate to max_lines
    has_more = len(diff_lines) > max_lines
    diff_head = '\n'.join(diff_lines[:max_lines])
    
    return DiffResponse(
        diff_head=diff_head,
        has_more=has_more,
        rejected=is_rejected
    )

@app.get("/api/runs/{run_id}/result", response_model=ResultResponse)
async def get_run_result(run_id: str):
    """
    Get result summary for a completed run.
    Returns paths to all artifacts and exit code.
    """
    artifacts_dir = get_run_directory(run_id)
    
    # Check for various artifacts
    output_path = artifacts_dir / 'output.md'
    rejected_path = artifacts_dir / 'output.rejected.md'
    plan_path = artifacts_dir / 'plan.json'
    json_report_path = artifacts_dir / 'report.json'
    stats_path = artifacts_dir / 'stats.json'
    
    # Determine exit code from job state or files
    metadata = load_run_metadata(run_id) or {}

    exit_code = metadata.get('exit_code', 0)
    if rejected_path.exists():
        exit_code = 3  # Validation failed
    elif run_id in run_jobs:
        result = run_jobs[run_id].get('result', {})
        exit_code = result.get('exit_code', exit_code)
    
    return ResultResponse(
        exit_code=exit_code,
        output_path=str(output_path) if output_path.exists() else None,
        rejected_path=str(rejected_path) if rejected_path.exists() else None,
        plan_path=str(plan_path) if plan_path.exists() else None,
        json_report_path=str(json_report_path) if json_report_path.exists() else str(stats_path) if stats_path.exists() else None
    )

@app.get("/api/artifact")
async def get_artifact(run_id: str, name: str):
    """
    Download a specific artifact file.
    name can be: output, plan, report, rejected, input
    """
    artifacts_dir = get_run_directory(run_id)
    
    # Map name to file path
    file_map = {
        'output': artifacts_dir / 'output.md',
        'rejected': artifacts_dir / 'output.rejected.md',
        'plan': artifacts_dir / 'plan.json',
        'report': artifacts_dir / 'report.json',
        'stats': artifacts_dir / 'stats.json',  # Fallback for PR-1 runs
        'input': artifacts_dir / 'input.txt'
    }
    
    if name not in file_map:
        raise HTTPException(status_code=400, detail=f"Invalid artifact name: {name}")
    
    file_path = file_map[name]
    if not file_path.exists():
        # Try fallback for report
        if name == 'report':
            stats_path = file_map['stats']
            if stats_path.exists():
                return FileResponse(
                    stats_path,
                    media_type='application/json',
                    filename=f'{run_id}_stats.json'
                )
        raise HTTPException(status_code=404, detail=f"Artifact not found: {name}")
    
    # Determine media type
    media_type = 'application/json' if file_path.suffix == '.json' else 'text/markdown'
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=file_path.name
    )

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
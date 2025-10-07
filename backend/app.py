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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Import our existing functionality
import sys
sys.path.append(str(Path(__file__).parent.parent))
from md_proof import (print_progress, load_markdown, chunk_paragraphs, DEFAULT_API_BASE, 
                     INSTRUCTION, mask_urls, unmask_urls, extract_between_sentinels, 
                     call_lmstudio, Spinner, paths_for, write_ckpt, load_ckpt)

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

@app.get("/")
async def root():
    return {"message": "TTS-Proof API is running"}

@app.get("/api/models", response_model=List[Model])
async def get_models():
    """Fetch available models from LM Studio."""
    try:
        print("Models endpoint called")
        
        # First try to get from LM Studio
        import requests
        print(f"Fetching models from {DEFAULT_API_BASE}/models")
        response = requests.get(f"{DEFAULT_API_BASE}/models", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"LM Studio returned: {len(data.get('data', []))} models")
        
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
        
        fmode = "a" if start_index > 0 else "w"
        
        with open(partial_path, fmode, encoding="utf-8") as fout:
            for idx in range(start_index, len(chunks)):
                # Check for pause request
                if processing_jobs[job_id]["status"] == "paused":
                    print(f"Job {job_id} paused at chunk {idx}")
                    processing_jobs[job_id]["can_resume"] = True
                    await manager.send_message(job_id, {
                        "type": "paused",
                        "message": f"Job paused at chunk {idx + 1}/{len(chunks)}"
                    })
                    return
                
                chunk_type, chunk_content = chunks[idx]
                processing_jobs[job_id]["current_chunk"] = idx
                
                if chunk_type == "text" and chunk_content.strip():
                    print(f"Processing text chunk {processed_text_so_far + 1}/{total_text_chunks} ({len(chunk_content)} chars)")
                    
                    try:
                        # Process the chunk
                        corrected = correct_chunk_with_prompt(api_base, model_name, chunk_content, 
                                                            prompt_to_use, request.show_progress)
                        
                        # Write to partial file
                        fout.write(corrected)
                        fout.write("\n")
                        fout.flush()
                        
                        processed_text_so_far += 1
                        processing_jobs[job_id]["processed_chunks"] = processed_text_so_far
                        
                        # Create chunk preview (limit content for UI)
                        chunk_preview = ChunkPreview(
                            chunk_index=idx,
                            chunk_type=chunk_type,
                            original_content=chunk_content[:500] + "..." if len(chunk_content) > 500 else chunk_content,
                            processed_content=corrected[:500] + "..." if len(corrected) > 500 else corrected,
                            character_count=len(corrected),
                            is_complete=True
                        )
                        
                        # Store only last 5 chunks to prevent memory issues
                        result_chunks = processing_jobs[job_id]["result_chunks"]
                        result_chunks.append(chunk_preview.dict())
                        if len(result_chunks) > 5:
                            result_chunks.pop(0)
                        
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
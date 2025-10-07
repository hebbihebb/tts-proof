#!/usr/bin/env python3
"""
Minimal test version of the FastAPI backend to isolate issues.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="TTS-Proof Test API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Model(BaseModel):
    id: str
    name: str
    description: str

@app.get("/")
async def root():
    return {"message": "TTS-Proof Test API is running"}

@app.get("/api/models", response_model=List[Model])
async def get_models():
    """Return test models."""
    print("Models endpoint called")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        models = []
        for model in data.get("data", []):
            if "embedding" not in model["id"].lower() and "reranker" not in model["id"].lower():
                models.append(Model(
                    id=model["id"],
                    name=model["id"].replace("_", " ").title(),
                    description=f"Model: {model['id']}"
                ))
        
        if not models:
            models = [Model(id="default", name="Default Model", description="Local LLM model")]
        
        print(f"Returning {len(models)} models")
        return models
        
    except Exception as e:
        print(f"Error: {e}")
        return [
            Model(id="default", name="Default Model", description="Local LLM model"),
            Model(id="qwen/qwen3-4b-2507", name="Qwen 3 4B", description="Qwen 3 4B model"),
        ]

if __name__ == "__main__":
    uvicorn.run("test_app:app", host="0.0.0.0", port=8000, reload=False)
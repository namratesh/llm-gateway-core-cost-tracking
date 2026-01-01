import os
import httpx
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import Middleware
from middleware import CostAwareMiddleware

# --- Configuration ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "llama3"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 90.0  # Generous timeout for LLMs

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API-Main")

app = FastAPI(title="Cost-Aware LLM Gateway", version="1.1.0")
app.add_middleware(CostAwareMiddleware)

# --- Data Models with Validation ---
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="The input text")
    model: Optional[str] = Field(DEFAULT_MODEL)
    system_prompt: Optional[str] = Field(None)

    # DoS Protection: Prevent massive payloads
    @validator('prompt')
    def validate_length(cls, v):
        if len(v) > 10000: # Limit to ~10k chars
            raise ValueError('Prompt is too long (max 10,000 characters)')
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v

class GenerateResponse(BaseModel):
    response: str
    model_used: str
    total_duration_ms: float
    request_id: str

# --- Resilience Logic ---
# Retry 3 times, waiting 1s, then 2s, then 4s (exponential backoff)
# Only retry on Network Errors (ConnectError) or Server Errors (503)
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout)),
    reraise=True
)
async def call_ollama_with_retry(url: str, payload: dict):
    async with httpx.AsyncClient() as client:
        # We separate connect timeout (fast) from read timeout (slow)
        resp = await client.post(
            url, 
            json=payload, 
            timeout=httpx.Timeout(TIMEOUT_SECONDS, connect=5.0)
        )
        resp.raise_for_status()
        return resp.json()

# --- Core Logic ---
@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest, raw_request: Request):
    
    target_model = getattr(raw_request.state, "target_model", request.model or DEFAULT_MODEL)
    
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": target_model,
        "prompt": request.prompt,
        "stream": False
    }
    
    try:
        # Call the resilient function
        data = await call_ollama_with_retry(url, payload)
        
        return GenerateResponse(
            response=data.get("response", ""),
            model_used=data.get("model", target_model),
            total_duration_ms=data.get("total_duration", 0) / 1_000_000,
            request_id=getattr(raw_request.state, "request_id", "unknown")
        )
        
    except httpx.HTTPStatusError as e:
        # Ollama returned a specific error (e.g. model not found)
        logger.error(f"Ollama API Error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail="Model engine error.")
        
    except Exception as e:
        # We exhausted retries or hit a bug
        logger.error(f"Critical Failure after retries: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable after multiple attempts.")

if __name__ == "__main__":
    # Production: reload=False, generic host
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
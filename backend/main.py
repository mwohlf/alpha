from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from contextlib import asynccontextmanager
import jwt
from datetime import datetime, timedelta
from config import settings
from ollama_service import get_ollama_client
from pydantic import BaseModel
from typing import Optional

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting application in {settings.ENVIRONMENT} mode")
    yield
    # Shutdown
    print("Shutting down application")

app = FastAPI(
    title=settings.APP_NAME,
    description="Alpha Project API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    """Verify JWT token from Authorization header"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/hello")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.get("/api/protected", dependencies=[Depends(verify_token)])
def protected_endpoint():
    """Protected endpoint requiring JWT token"""
    return {"message": "This is a protected endpoint"}


# ============== Ollama Integration ==============

class GenerateRequest(BaseModel):
    """Request model for text generation"""
    model: str
    prompt: str
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None


class EmbedRequest(BaseModel):
    """Request model for embeddings"""
    model: str
    text: str


@app.get("/api/ollama/models")
def list_ollama_models():
    """List all available Ollama models"""
    try:
        client = get_ollama_client()
        models = client.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ollama/generate")
def generate_text(request: GenerateRequest):
    """Generate text using Ollama"""
    try:
        client = get_ollama_client()
        
        kwargs = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_k is not None:
            kwargs["top_k"] = request.top_k
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        
        result = client.generate(
            model=request.model,
            prompt=request.prompt,
            **kwargs
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ollama/embed")
def generate_embeddings(request: EmbedRequest):
    """Generate embeddings using Ollama"""
    try:
        client = get_ollama_client()
        result = client.embed(model=request.model, prompt=request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ollama/pull")
def pull_model(model_name: str):
    """Pull/download a model from Ollama library"""
    try:
        client = get_ollama_client()
        result = client.pull_model(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

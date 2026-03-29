from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from config import settings

from router import router  # Get the object FROM the file

import os

frontend_dir = "../dist/frontend"

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

# Include API router
app.include_router(router)

# Include static file content
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", include_in_schema=False)
@app.get("/{skip_path:path}", include_in_schema=False) # Hides catch-all from Swagger
async def serve_index(skip_path: str = None): # Note: added skip_path argument to avoid errors
    index_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_path):
        return {"error": "Frontend build not found. Did you run 'nx build frontend'?"}
    return FileResponse(index_path)

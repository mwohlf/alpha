import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from router import router

frontend_dir = "../dist/frontend"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error") # Ties into the Uvicorn log stream

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting application in {settings.ENVIRONMENT} mode")
    yield
    logger.info("Shutting down application")

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

# Include static file content for the react app
app.mount("/app", StaticFiles(directory=frontend_dir), name="static")

async def get_index():
    """Helper to serve the React entry point."""
    index_path = os.path.join(frontend_dir, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(
            status_code=404, 
            detail="Frontend build not found. Did you run 'nx build frontend'?"
        )
    return FileResponse(index_path)

# index.html
@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
async def serve_index_file():
    return await get_index()

# catch all with error output
@app.get("/{skip_path:path}", include_in_schema=False) # Hides catch-all from Swagger
async def serve_index(request: Request, skip_path: str): # Note: added skip_path argument to avoid errors
# Log the incoming path to see what React Router is trying to handle
    logger.info(f"SPA Catch-all triggered by path: /{skip_path} | Client: {request.client.host}")
    
    # Optional: Log a warning if the path looks like a missing file (has an extension)
    # This helps catch 404s on images/assets that aren't in your /static folder
    if "." in skip_path:
        logger.warning(f"Possible missing asset requested via SPA redirect: /{skip_path}")
        raise HTTPException(
            status_code=404, 
            detail="Resource not found."
        )
        
    return await get_index()



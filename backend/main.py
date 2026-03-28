from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from config import settings
from generated import router

import os


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

frontend_dist = "../dist/frontend"

# a catch-all route for the SPA (Single Page Application)
# This MUST come after your API routes so it doesn't intercept them
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # If the requested file exists (like favicon.ico), serve it
    file_path = os.path.join(frontend_dist, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # Otherwise, always serve index.html (the entry point for React Router)
    return FileResponse(f"{frontend_dist}/index.html")

import logging
import logging.handlers
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from endpoints.data_models import HealthGetResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from ollama.ollama_client_manager import OllamaClientManager
from config import settings
from endpoints.api_router import router as endpoints
from telegram.message_store import init_db
from telegram.telegram_client_manager import TelegramClientManager


# --- Logging setup

os.makedirs(os.path.dirname(settings.LOGFILE), exist_ok=True)
file_handler = logging.handlers.RotatingFileHandler(
    settings.LOGFILE, maxBytes=5 * 1024 * 1024, backupCount=3
)
stdout_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[file_handler, stdout_handler],
)
logger = logging.getLogger("alpha")
for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(uvicorn_logger).handlers = logging.root.handlers
    logging.getLogger(uvicorn_logger).propagate = False


# --- Service Callbacks ---


async def start_ollama(app: FastAPI, base_url: str, model: str):
    """Callback to start or restart the Ollama client."""
    # Stop existing if running
    await stop_ollama(app)

    try:
        manager = OllamaClientManager(base_url=base_url, default_model=model)
        await manager.start()
        app.state.ollama_manager = manager
        logger.info(f"Ollama started: {model} @ {base_url}")

        # Link to telegram if telegram is already running
        if hasattr(app.state, "telegram_manager") and app.state.telegram_manager:
            app.state.telegram_manager.client.ollama_manager = manager

    except Exception as e:
        logger.error(f"Ollama start failed: {e}", exc_info=True)
        app.state.ollama_manager = None


async def stop_ollama(app: FastAPI):
    """Callback to stop the Ollama client."""
    manager: Optional[OllamaClientManager] = getattr(app.state, "ollama_manager", None)
    if manager:
        await manager.stop()
        app.state.ollama_manager = None
        logger.info("Ollama stopped")


async def start_telegram(app: FastAPI):
    """Callback to start the Telegram client."""
    await stop_telegram(app)

    if not (settings.TELEGRAM_API_ID and settings.TELEGRAM_API_HASH):
        logger.error("Missing Telegram Credentials")
        return

    try:
        manager = TelegramClientManager()
        await manager.start()
        app.state.telegram_manager = manager

        # Link existing Ollama manager if available
        ollama = getattr(app.state, "ollama_manager", None)
        if ollama:
            manager.client.ollama_manager = ollama

        logger.info("Telegram started")
    except Exception as e:
        logger.error(f"Telegram start failed: {e}", exc_info=True)
        app.state.telegram_manager = None


async def stop_telegram(app: FastAPI):
    """Callback to stop the Telegram client."""
    manager: Optional[TelegramClientManager] = getattr(
        app.state, "telegram_manager", None
    )
    if manager:
        await manager.stop()
        app.state.telegram_manager = None
        logger.info("Telegram stopped")


def update_app_config(app: FastAPI, **kwargs):
    """Callback to update dynamic configuration parameters."""
    # We store these in a dict in app state so endpoints can see the 'current' effective config
    if not hasattr(app.state, "dynamic_config"):
        app.state.dynamic_config = {}

    app.state.dynamic_config.update(kwargs)
    logger.info(f"Config updated: {kwargs}")


# --- Lifespan Manager ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting application in {settings.ENVIRONMENT} mode")

    # Initialize Persistent Storage
    await init_db(settings.TELEGRAM_DATABASE_URL)

    # Set initial config parameters
    update_app_config(
        app,
        ollama_model=settings.OLLAMA_DEFAULT_MODEL,
        ollama_url=settings.OLLAMA_BASE_URL,
        enabled_features=["telegram" if settings.TELEGRAM_API_ID else None],
    )

    # Initial Startups based on settings
    if settings.OLLAMA_ENABLED:
        await start_ollama(app, settings.OLLAMA_BASE_URL, settings.OLLAMA_DEFAULT_MODEL)

    if settings.TELEGRAM_API_ID:
        await start_telegram(app)

    yield

    # Graceful Shutdown
    await stop_telegram(app)
    await stop_ollama(app)
    logger.info("Shutdown complete")


# --- App Setup ---

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(endpoints, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Static Files & SPA Logic ---


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


app.mount(
    "/app", SPAStaticFiles(directory=settings.FRONTEND_DIR, html=True), name="static"
)


async def _get_index():
    index_path = os.path.join(settings.FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend build not found.")
    return FileResponse(index_path)


# --- additional endpoints


@app.get(
    "/api/health",
    response_model=HealthGetResponse,
    operation_id="get_health",
    include_in_schema=False,
)
def get_health() -> HealthGetResponse:
    return HealthGetResponse(status="healthy")


@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
async def serve_index_file():
    return RedirectResponse(url="/app/")


@app.get("/{skip_path:path}", include_in_schema=False)
async def catch_all(request: Request, skip_path: str):
    if "." in skip_path:  # Likely a missing asset file
        raise HTTPException(status_code=404)
    return await _get_index()

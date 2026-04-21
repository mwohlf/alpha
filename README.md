# Alpha

React frontend and FastAPI backend, built with nx.

## Requirements

- node
- npm
- python3
- docker

## Setup

```bash
npm install
```

## Commands

**Clean:**
```bash
rm -rf \
  .nx/cache \
  .nx/installation \
  .nx/workspace-data \
  node_modules \
  package-lock.json \
  dist \
  log/*.log \
  etc/alpha-service.yaml \
  backend/.venv \
  backend/.ruff_cache \
  backend/__pycache__ \
  backend/ollama/client \
  frontend/dist \
  frontend/node_modules \
  frontend/src/generated

npm install
```

**Build:**
```bash
./nx build backend
./nx build frontend
```

**Run:**
```bash
./nx serve backend
./nx serve frontend
```

**Docker:**
```bash
./nx build_docker backend
docker run -p 8000:8000 alpha-app
```

## URLs

| | |
|---|---|
| Frontend (proxied) | http://localhost:3000 |
| Backend | http://localhost:8000 |

## Project Structure

### Backend (`backend/`)

- **`main.py`** — FastAPI app, lifespan manager (starts/stops Telegram + Ollama), static file serving for the SPA, catch-all route for client-side routing
- **`router.py`** — all API routes under `/api`; JWT auth via `verify_token`
- **`config.py`** — pydantic-settings; reads `.env` then overrides with the file specified by `ENV_FILE` (defaults to `.env.prod`; dev uses `.env.dev`)
- **`models.py`** — Pydantic request/response models
- **`telegram/`** — Pyrogram client wrapper; `client_manager.py` manages lifecycle, `handlers.py` processes incoming messages, `message_store.py` is SQLAlchemy async storage
- **`ollama/`** — httpx-based async Ollama client; `ollama_client.py` provides chat/generate/stream; `ollama/client/` is generated from `etc/ollama-service.yaml`

### Frontend (`frontend/src/`)

- **`generated/`** — auto-generated axios client (orval) from the backend's OpenAPI spec; never edit by hand
- **`store/`** — Zustand stores; each store instantiates `getAlphaAPI()` and wraps API calls with loading/error state
- **`App.tsx`** — entry point

The frontend API client is code-generated from the backend. When adding a new endpoint, add the route and Pydantic model to `router.py` / `models.py`, then run `./nx build frontend` to regenerate the client.

## CI

```bash
npm install
./nx build_docker backend
```

## Telegram Setup

Telegram credentials go in `.env.dev`.

**API credentials** (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`):
1. Go to https://my.telegram.org/apps
2. Log in and create an application
3. Copy the API ID and API Hash into `.env.dev`

**Session string** (`TELEGRAM_SESSION_STRING`):

If `TELEGRAM_SESSION_STRING` is left empty, the app will prompt for authentication interactively on first run — enter your phone number and the OTP sent to your Telegram app. The session string will be logged to stdout. Copy it into `.env.dev`:

```
TELEGRAM_SESSION_STRING=<paste here>
```

This only needs to be done once. The session string authenticates the app without requiring login on subsequent starts.

## Links

- [Ollama OpenAPI definition](https://github.com/ollama/ollama/tree/main/docs)

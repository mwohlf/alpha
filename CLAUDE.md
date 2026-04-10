# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Nx monorepo with a React (Vite) frontend and FastAPI backend. The frontend is served as static files by the backend in production. API types are code-generated from the backend's OpenAPI schema.

## Commands

### Setup
```bash
npm install
```

### Build
```bash
./nx build backend      # builds Python venv + generates Ollama client
./nx build frontend     # generates API client from OpenAPI, then builds React app
```

### Run (dev)
```bash
./nx serve backend      # starts uvicorn with --reload; depends on frontend:build
./nx serve frontend     # starts Vite dev server; depends on frontend:generate
```

### Test
```bash
./nx test backend       # runs pytest in backend/
./nx test frontend      # runs vitest
```

### Lint & Format (backend)
```bash
./nx lint backend       # ruff check
./nx format backend     # ruff format
```

### Docker
```bash
./nx build_docker backend   # builds both frontend & backend, then docker image
docker run -p 8000:8000 alpha-app
```

### Clean
```bash
rm -rf .nx/cache .nx/installation .nx/workspace-data node_modules package-lock.json dist \
  backend/.venv backend/.ruff_cache backend/__pycache__ backend/ollama/client \
  frontend/dist frontend/node_modules frontend/src/generated etc/alpha-service.yaml
npm install
```

## Architecture

### Code generation pipeline

The frontend API client is derived from the backend. The full dependency chain is:

```
backend:generate_venv
  → backend:generate_ollama_client   (generates backend/ollama/client/ from etc/ollama-service.yaml)
  → backend:build
  → backend:generate_openapi_yaml    (runs etc/extract_openapi.py → etc/alpha-service.yaml)
  → frontend:generate                (runs orval → frontend/src/generated/)
  → frontend:build
```

**Never hand-edit** `frontend/src/generated/` or `etc/alpha-service.yaml` — they are generated outputs.

When adding a new API endpoint:
1. Add the route + Pydantic model to `backend/router.py` / `backend/models.py`
2. Run `./nx build frontend` to regenerate `etc/alpha-service.yaml` and `frontend/src/generated/`
3. Use the generated `getAlphaAPI()` client in frontend stores (see `frontend/src/store/useHelloStore.ts` for the pattern)

### Backend (`backend/`)

- **`main.py`** — FastAPI app, lifespan manager (starts/stops Telegram + Ollama), static file serving for the SPA, catch-all route for client-side routing
- **`router.py`** — all API routes under `/api`; JWT auth via `verify_token`
- **`config.py`** — pydantic-settings; reads `.env` then overrides with the file specified by `ENV_FILE` env var (defaults to `.env.prod`; dev uses `.env.dev`)
- **`models.py`** — Pydantic request/response models
- **`telegram/`** — Pyrogram client wrapper; `client_manager.py` manages lifecycle, `handlers.py` processes incoming messages, `message_store.py` is SQLAlchemy async storage
- **`ollama/`** — httpx-based async Ollama client; `ollama_client.py` provides chat/generate/stream; `ollama/client/` is generated from `etc/ollama-service.yaml`

Telegram and Ollama managers are stored on `app.state` and cross-linked (Telegram handler can call Ollama). Both are started/stopped in the lifespan context manager.

### Frontend (`frontend/src/`)

- **`generated/`** — auto-generated axios client (orval) from the OpenAPI spec; `endpoints.ts` exports `getAlphaAPI()`
- **`store/`** — Zustand stores; each store instantiates `getAlphaAPI()` and wraps API calls with loading/error state
- **`App.tsx`** — minimal entry point currently

### Environment / Config

Dev credentials go in `.env.dev`. Required variables for Telegram: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`, `TELEGRAM_SESSION_NAME`, `TELEGRAM_DATABASE_URL`. See README for Telegram first-run auth flow.

The backend serves the frontend at `/app` (static) and `/` (SPA index.html). In dev, the Vite dev server at `:5173` (or `:3000`) proxies to the backend at `:8000`.

### CI

GitHub Actions (`.github/workflows/docker-image.yml`) runs `./nx build_docker backend` on push/PR to `main` and pushes the image to `ghcr.io`.

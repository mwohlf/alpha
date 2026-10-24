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
  log/*.log backend/.venv backend/.ruff_cache backend/__pycache__ backend/ollama/client \
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
1. Add the route to the matching module in `backend/endpoints/` (or a new module registered in `endpoints/api_router.py`) and its Pydantic models to `backend/endpoints/data_models.py`; protect it with `Depends(verify_token)` from `endpoints/auth.py`
2. Run `./nx build frontend` to regenerate `etc/alpha-service.yaml` and `frontend/src/generated/`
3. Call it through the shared `api` client from `frontend/src/api.ts` in a Zustand store (see `frontend/src/store/usePersonaStore.ts` for the pattern)

### Backend (`backend/`)

The app is a Telegram userbot that auto-replies to incoming messages using a local Ollama LLM speaking as the active persona, plus an admin API.

- **`main.py`** — FastAPI app, logging setup, lifespan manager (`init_db` → `seed_personas` → start Ollama → start Telegram), SPA static serving at `/app`, catch-all route for client-side routing
- **`config.py`** — pydantic-settings; loads `<workspace root>/.env`, then the file named by the `ENV_FILE` env var (resolved from the workspace root; `project.json` sets `.env.dev` for `serve`/`generate_openapi_yaml`), then process env vars — later sources win; missing files are skipped
- **`endpoints/`** — API routes, all mounted under `/api` via `api_router.py`:
  - `auth.py` — `POST /auth/login` (single user from `LOGIN_USERNAME`/`LOGIN_PASSWORD`), JWT issuing, `verify_token` dependency
  - `chat.py` — direct chat with the model (`/message`, streaming `/stream`)
  - `model.py` — list / pull / delete Ollama models
  - `persona.py` — list / create / update personas
  - `telegram.py` — client status, stored messages, users, per-user message history
  - `data_models.py` — Pydantic request/response models
  - `dependencies.py` — `get_ollama_manager` / `get_telegram_manager` (read from `app.state`)
- **`database/`** — SQLAlchemy async: `session.py` (engine, `init_db`, `get_db_session`), `message_store.py` (`TelegramMessage`), `persona_store.py` (`Persona` + `seed_personas`, which seeds from `personas/*.txt` when the table is empty)
- **`personas/`** — persona system prompts as `.txt` files (seed data only; the DB is the source of truth after first run)
- **`telegram/`** — Pyrogram integration:
  - `telegram_client_manager.py` — lifecycle (start/stop)
  - `telegram_client.py` — `TelegramClient(Client)` subclass: handles incoming messages, stores them, generates replies via Ollama, simulates human behaviour (delayed read receipts, typing indicator scaled to reply length), post-processes replies (strip empty lines, inject typos)
  - `chat_state.py` — per-chat `ChatState`: coalesces rapid consecutive messages into one input and cancels in-flight replies when new messages arrive
  - `utils.py` — `get_message_type`, `should_respond_with_ai`
- **`ollama/`** — `ollama_client_manager.py` (httpx-based: list/pull/delete models, `chat`, `chat_stream`, `generate`), `prompt_handler.py` (`create_prompt` builds messages from the active persona + history); `ollama/client/` is generated from `etc/ollama-service.yaml`

Telegram and Ollama managers are stored on `app.state` and cross-linked (`telegram_manager.client.ollama_manager`). Both are started/stopped in the lifespan context manager.

### Frontend (`frontend/src/`)

- **`generated/`** — auto-generated axios client (orval) from the OpenAPI spec; `endpoints.ts` exports `getAlphaAPI()`
- **`api.ts`** — the single `api = getAlphaAPI(authAxios)` instance; the axios interceptor adds the JWT bearer token and redirects to `/app/login` on 401
- **`store/`** — Zustand stores (with `devtools`) wrapping API calls with loading/error state: `useAuthStore`, `useChatStore`, `useModelsStore`, `usePersonaStore`, `useSessionsStore`
- **`App.tsx`** — `BrowserRouter` with basename `/app`; public `/login`, everything else behind `RequireAuth` inside `components/Layout.tsx`
- **`pages/`** — `Setup` (default route), `Model`, `Persona`, `Memory`, `Chat` (talk to the model directly), `Conversation` (browse Telegram conversations per user)

### Environment / Config

Env files live at the workspace root: shared/default values in `.env`, dev overrides in `.env.dev` (both gitignored). Key variables:
- Auth: `SECRET_KEY`, `LOGIN_USERNAME`, `LOGIN_PASSWORD`
- Ollama: `OLLAMA_BASE_URL`, `OLLAMA_DEFAULT_MODEL`
- Telegram: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`, `TELEGRAM_SESSION_NAME`, `TELEGRAM_DATABASE_URL`. See README for Telegram first-run auth flow.

The backend serves the frontend at `/app` (static; `/` redirects there). In dev, the Vite dev server proxies `/api` to the backend at `127.0.0.1:8000`.

### CI

GitHub Actions (`.github/workflows/docker-image.yml`) runs `./nx build_docker backend` on push/PR to `main` and pushes the image to `ghcr.io`.

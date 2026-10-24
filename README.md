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

**Test / lint:**
```bash
./nx test backend      # pytest (no tests yet)
./nx test frontend     # vitest
./nx lint backend      # ruff check
./nx format backend    # ruff format
```

**Docker:**
```bash
./nx build_docker backend
docker run -p 8000:8000 --env-file .env -v alpha-data:/app/etc alpha-app
```

The image contains no env file, so configuration must be passed in (`--env-file` or `-e`). Paths such as `FRONTEND_DIR`, `LOGFILE` and `TELEGRAM_DATABASE_URL` are resolved inside the container (working directory `/app`).

Keep `TELEGRAM_DATABASE_URL` pointing into `/app/etc` (e.g. `sqlite+aiosqlite:///./etc/telegram_messages.db`) and mount the named volume as shown: without it, every new container starts with an empty database and stored messages and long-term memories are lost.

## URLs

| | |
|---|---|
| Frontend (proxied) | http://localhost:3000 |
| Backend (serves the built UI at `/app`) | http://localhost:8000 |

## Project Structure

The backend is a Telegram userbot that auto-replies to incoming messages using a local Ollama model speaking as the active persona, plus an admin API and web UI.

### Backend (`backend/`)

- **`main.py`** — FastAPI app, logging setup, lifespan manager (`init_db` → `sync_personas` → start Ollama → start Telegram), SPA static serving at `/app`, catch-all route for client-side routing
- **`config.py`** — pydantic-settings; loads `<workspace root>/.env`, then the file named by `ENV_FILE` if set (`nx serve backend` sets `.env.dev`), then process env vars — later sources win, missing files are skipped
- **`endpoints/`** — API routes mounted under `/api` by `api_router.py`: `auth.py` (login, JWT, `verify_token`), `chat.py` (direct chat with the model, incl. SSE streaming), `model.py` (list / pull / delete Ollama models), `persona.py` (list / create / update personas), `telegram.py` (status, stored messages, users), `database.py` (wipe all data); request/response models live in `data_models.py`
- **`database/`** — SQLAlchemy async: `session.py` (engine, `init_db` — recreates the tables when the schema fingerprint changes, `wipe_db`), `message_store.py` (stored Telegram messages), `persona_store.py` (personas, synced from `personas/*.txt` on every startup)
- **`personas/`** — persona system prompts, one `.txt` per persona; the source of truth on startup (UI edits last until the next restart)
- **`telegram/`** — Pyrogram integration: `telegram_client_manager.py` (lifecycle, first-run auth), `telegram_client.py` (message handling, reply generation, human-like read/typing delays, post-processing), `chat_state.py` (coalesces rapid messages per chat and cancels superseded replies), `utils.py`
- **`ollama/`** — `ollama_client_manager.py` (httpx-based Ollama client: models, chat, streaming), `prompt_handler.py` (builds the prompt from the active persona + history); `ollama/client/` is generated from `etc/ollama-service.yaml`

### Frontend (`frontend/src/`)

- **`generated/`** — auto-generated axios client (orval) from the backend's OpenAPI spec; never edit by hand
- **`api.ts`** — the shared `api` client; adds the JWT bearer token and redirects to the login page on 401
- **`store/`** — Zustand stores wrapping API calls with loading/error state
- **`index.tsx`** — entry point; **`App.tsx`** — router (basename `/app`) with a public `/login` and auth-protected pages
- **`pages/`** — `Model`, `Persona`, `Chat` (talk to the model directly), `Conversation` (browse Telegram conversations), `Setup` (wipe database), `Memory` (placeholder)

The frontend API client is code-generated from the backend:
`backend:build → backend:generate_openapi_yaml (etc/alpha-service.yaml) → frontend:generate (orval) → frontend:build`.
When adding a new endpoint, add the route to a module in `backend/endpoints/` and its Pydantic models to `endpoints/data_models.py`, then run `./nx build frontend` to regenerate the client.

## CI

```bash
npm install
./nx build_docker backend
```

## Configuration

Env files live at the workspace root: shared values in `.env`, dev overrides in `.env.dev` (both gitignored). Besides the Telegram settings below:

- `SECRET_KEY` — JWT signing key, generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- `LOGIN_USERNAME` / `LOGIN_PASSWORD` — the single admin login for the web UI; the password may be plain text or a bcrypt hash (defaults are `admin`/`admin` — change them)
- `OLLAMA_BASE_URL`, `OLLAMA_DEFAULT_MODEL` — Ollama server and the model used for Telegram replies
- `OLLAMA_RETRY_SECONDS` — retry interval while Ollama is unreachable at startup
- `TELEGRAM_DATABASE_URL` — async SQLAlchemy URL for messages and personas, e.g. `sqlite+aiosqlite:///./etc/telegram_messages.db`

Data is kept across restarts. When the database schema changes (a model in `backend/database/` is modified), all existing data is discarded and the tables are recreated — there are no migrations. The **Setup** page has a button to wipe all data manually (personas are restored from `backend/personas/` afterwards).

If Ollama is unreachable at startup, the backend retries every `OLLAMA_RETRY_SECONDS` (default 30).

## Telegram Setup

The userbot currently runs on the Telegram account [@danie_horton](https://t.me/danie_horton).

**API credentials** (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`):
1. Go to https://my.telegram.org/apps
2. Log in and create an application
3. Copy the API ID and API Hash into `.env`

Also set `TELEGRAM_SESSION_NAME` (any name, e.g. `alpha_userbot`); the client refuses to start without it.

**Session string** (`TELEGRAM_SESSION_STRING`):

If `TELEGRAM_SESSION_STRING` is left empty, the app prompts for authentication interactively on startup — enter your phone number and the OTP sent to your Telegram app. This needs an interactive terminal, so run it locally (`./nx serve backend`), not in Docker. The session string is then logged (stdout and `log/alpha.log`). Copy it into your env file:

```
TELEGRAM_SESSION_STRING=<paste here>
```

This only needs to be done once. The session string grants full access to the account: keep it secret, and delete it from the log file afterwards.

## Links

- [Ollama OpenAPI definition](https://github.com/ollama/ollama/tree/main/docs)

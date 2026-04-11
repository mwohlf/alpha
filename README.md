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

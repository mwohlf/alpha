# Code Review — Alpha

_Snapshot: `main` @ `72a15b1`, 2026-10-24. Updated after `69dfac2`; items marked **✅ Fixed** are resolved._

## Summary

Alpha is a small, readable codebase (~2k lines of hand-written code) with a sensible shape: FastAPI + SQLAlchemy async on the backend, a typed client generated from OpenAPI for the React/Zustand frontend, and a clear lifespan that wires Ollama and Telegram together. The module boundaries (`endpoints/`, `database/`, `telegram/`, `ollama/`) are clean. The per-chat coalescing logic in `ChatState` is a nice idea and mostly well done.

It is still a prototype, though, and some defects need fixing before anyone relies on it:

1. ~~**Every restart wipes the database.** That includes persona edits and all Telegram history.~~ ✅ Fixed: data now survives restarts and is reset only on schema changes.
2. ~~**The bot sees the current message twice** in its prompt.~~ ✅ Fixed in `69dfac2`.
3. **Insecure defaults.** The JWT secret is empty and the login is `admin`/`admin`, while the Docker image listens on `0.0.0.0`.
4. **Secrets and private chats go to the log file.** This covers the Telegram session string and the full prompts.
5. **There are no tests**, and `nx test` / `nx lint` don't pass as configured.

| Area | Rating | Notes |
|---|---|---|
| Structure / readability | Good | Clear module split, small functions, consistent naming |
| Correctness | Fair → Good | Data loss on restart, prompt duplication and the listed edge-case bugs are fixed |
| Security | Poor (if exposed) | Forgeable JWTs by default, secrets in logs |
| Ops / build | Fair | Nice Nx pipeline, but dead steps, bloated deps, stale README |
| Tests | None | No backend or frontend tests exist |

---

## Critical

### C1. `init_db` drops all tables on every startup — ✅ Fixed

> **Resolution:** `init_db` now stores a fingerprint of the models in a `schema_version` table. Tables are dropped and recreated only when that fingerprint changes; by design there are no migrations, so data is discarded on schema changes. A manual wipe is available as `POST /api/database/wipe` and on the Setup page. Note that on woodstock the SQLite file lives inside the container (`/app/etc`) with no volume, so redeploying the container still loses data.
`backend/database/session.py:36-39`

```python
# Drop and recreate tables to ensure schema is always up to date
await conn.run_sync(Base.metadata.drop_all)
await conn.run_sync(Base.metadata.create_all)
```

Every process start deletes all stored Telegram messages and all personas. With `uvicorn --reload` that means every saved code change. `seed_personas` then re-seeds from `personas/*.txt`, so any edits made in the UI are silently lost. This contradicts the documented intent ("the DB is the source of truth after first run"). It also means the bot loses conversation memory on every restart.

**Fix:** remove `drop_all`. Use `create_all` for new tables and introduce Alembic for schema changes. If a dev-only reset is wanted, gate it behind an explicit setting such as `DB_RESET_ON_START=false`.

### C2. The current message appears twice in the LLM prompt — ✅ Fixed
`backend/telegram/telegram_client.py:65,73` → `:166-178`

> **Resolution (`69dfac2`):** pending messages are now tracked by `message_id` in `ChatState.pending` and excluded from the history. Only the final user turn contains them.

`_handle_new_message` stores the incoming message (`add_message`) *before* scheduling the response. `_generate_and_send_response` then loads `get_chat_history(...)`, which already contains that message, plus any other coalesced pending messages. `create_prompt` then appends `combined_text` as the final user turn as well. The model sees every pending message twice: once as history and once as the new input. This degrades reply quality and makes the coalescing logic pointless.

**Fix:** drop history rows whose `message_id` is in the pending set, or load the history before storing. Better still, keep the history query and skip the extra user turn.

### C3. Forgeable auth by default
`backend/config.py:37-41`, `backend/endpoints/auth.py:18-37`

- `SECRET_KEY` defaults to `""`, and PyJWT will happily sign and verify HS256 tokens with an empty key. Anyone can mint a valid token if the env var is missing.
- `LOGIN_USERNAME`/`LOGIN_PASSWORD` default to `admin`/`admin`.
- The Docker `CMD` binds `0.0.0.0`, so a misconfigured container exposes the admin API. That API can read every stored private conversation, delete models, and change what the bot says.

**Fix:** fail fast at startup if `SECRET_KEY` is empty or shorter than 32 bytes, or if the password is still the default outside dev. Consider basic rate limiting on `/auth/login`.

### C4. Telegram session string and private conversations are written to the log
- `backend/telegram/telegram_client_manager.py:49-51` logs the exported session string at INFO. A session string is full account takeover, and it lands in `log/alpha.log`, which persists and rotates.
- `backend/ollama/prompt_handler.py:47` logs the **entire** prompt at INFO on every message. That includes the persona and the last 20 messages of the private chat. The log grows quickly and holds third parties' private messages in plaintext.

**Fix:** print the session string to stdout only, once, never through the file handler, or write it to a `0600` file. Drop the prompt dump to DEBUG, or remove it.

---

## High

### H1. `should_respond_with_ai` matches substrings — ✅ Fixed
`backend/telegram/utils.py:42-45`

> **Resolution:** trigger words now use the word-boundary regex `\b(bot|ai|help)\b`. Responding only to mentions and replies remains an option.

`any(kw in text_lower for kw in ["bot", "ai", "help"])` matches `"ai"` inside *said, wait, again, main, email…* and `"bot"` inside *both, robot*. In group chats the bot will answer almost any message. Use word-boundary regex (`\b(bot|ai|help)\b`), or better, respond only to mentions and replies.

### H2. Deleting namespaced models is impossible — ✅ Fixed
`backend/endpoints/model.py:26-35`

> **Resolution:** the route is now `/model/delete/{name:path}`.

The route is `/model/delete/{name}`, but Ollama model names often contain `/`, e.g. the configured default `huihui_ai/dolphin3-abliterated:latest`. Starlette's `{name}` does not match slashes, even percent-encoded ones, so the request 404s. Use `{name:path}`, or pass the name as a query or body parameter as `add_model` already does.

### H3. A cancelled response can leave a sent reply unrecorded — ✅ Fixed
`backend/telegram/telegram_client.py:183-206`, `chat_state.py:32-41`

> **Resolution:** send + store now runs in a shielded `commit_task` (`_send_and_store`), which clears only the messages it answered. A new response reads the pending list *after* awaiting any in-flight commit, which also fixes the second race described below. While fixing this, another edge case turned up and is fixed too: a non-text message such as a sticker could cancel the read-receipt task that a pending response was awaiting, which silently aborted the reply. `ChatState.wait_for_read()` now waits for the latest read task instead.

A new incoming message cancels the in-flight task. If the cancel lands after `reply_text()` has gone out, during `add_message`, three things happen:
- the reply is sent but never stored
- `pending_texts` is not cleared, because `_on_success` skips cancelled tasks
- the next response therefore re-answers the old messages

Shield the "send + store + clear" section with `asyncio.shield`, or mark the state as "committed" right after sending.

There is a second, smaller race. `combined_text` is computed before `schedule_response` cancels or awaits the old task. If the old task finished but its done-callback has not run yet, already-answered text is included, and the callback then clears the *new* text as well.

### H4. The owner's manual replies don't cancel the bot — ✅ Fixed

> **Resolution:** outgoing messages clear `pending` and cancel the response task. An already-started send is not interrupted. This assumes Pyrogram doesn't dispatch the bot's own `reply_text` messages back as updates, which is not yet verified against a live account.

When the account owner answers from their phone, the outgoing message reaches `_handle_new_message`, gets stored, and is ignored. The pending AI reply still fires a few seconds later, so the counterpart gets two answers. Cancel `state.response_task` and clear `pending_texts` on outgoing messages.

### H5. Media is downloaded inline for every message
`backend/telegram/telegram_client.py:78-97`

Every photo, video or document in every chat, groups included, is downloaded synchronously before the message is stored or answered. A large video delays the reply pipeline for that message, and `media/` grows without bound and has no cleanup. Download lazily, in a background task, with size and type limits, or only in private chats.

### H6. Interactive Telegram login inside the server lifespan
`backend/telegram/telegram_client_manager.py:79-81`

If `TELEGRAM_SESSION_STRING` is missing, `start()` runs Pyrogram's interactive phone/OTP prompt inside FastAPI startup. In Docker or under Nx this blocks the lifespan forever, or fails confusingly. Move auth into a standalone CLI script. The error message at `:108` already references an `auth.py` script that doesn't exist.

### H7. Conversation view shows the *oldest* messages — ✅ Fixed
`backend/database/message_store.py:197-202`

> **Resolution:** the query now orders DESC, applies the limit, and reverses the result.

`get_messages_by_user` orders `date ASC` with `LIMIT 100`. Once a chat has more than 100 messages, the UI shows the first 100 and never the recent ones. Order DESC, limit, then reverse, as `get_chat_history` already does.

---

## Medium

- ✅ **Fixed:** **No recovery when a dependency fails at startup.** If Ollama is unreachable at boot (`main.py:65-67`), `ollama_manager` stays `None` forever. The bot silently stops answering and the API returns 503 until a restart. Retry lazily in `get_ollama_manager`, or on a background timer.
- ✅ **Fixed:** **`/api/*` typos return the SPA.** The catch-all at `main.py:190-194` also catches unknown `/api/...` paths and returns `index.html` with 200. Return a JSON 404 for anything under `/api`.
- **Telegram read endpoints require a live client.** `/telegram/messages`, `/users` and `/users/{id}/messages` depend on `get_telegram_manager`, but they only read the DB. When Telegram is down you can't browse history either. Drop the dependency where it's unused.
- ✅ **Fixed:** **`get_users` groups by name fields** (`message_store.py:147-152`). A user who changes their username or first name appears twice, which also gives duplicate React keys in `Conversation.tsx:46`. Group by `sender_id` only and take the latest name.
- **History roles in groups.** `"assistant" if m.sender_id is None else "user"` (`telegram_client.py:169`) merges every group member into one anonymous "user". Prefix content with the sender's name for non-private chats.
- ✅ **Fixed:** **Ties in history order.** Telegram dates have one-second resolution, so `ORDER BY date` can reorder messages sent within the same second. Add `message_id` as a tiebreaker.
- **Every reply gets a typo.** `_postprocess_response` (`telegram_client.py:235`) forces at least one typo, even in a three-word reply. It can also corrupt URLs, names or code. The comment said "~0.2 s per word" but the code uses `0.9` (`:249-250`); the comment is now corrected, but the forced typo is unchanged.
- **The "default model" in the UI is client-side only.** `Model.tsx` "Set as default" updates the browser's chat store and isn't persisted. The Telegram bot always uses `OLLAMA_DEFAULT_MODEL`. Either persist it server-side and use it for the bot, or relabel it as "Chat model".
- **Missing config fails with an obscure error.** `TELEGRAM_DATABASE_URL` defaults to `""`, so `create_async_engine("")` fails with an unhelpful error. Give it a sane default such as `sqlite+aiosqlite:///./data/alpha.db`, and remove the unused `DATABASE_URL`, `OLLAMA_ENABLED` and `DEBUG` settings.
- **Errors leak internal detail.** `str(e)` is returned to clients in `endpoints/telegram.py` and in the SSE stream (`chat.py:57`). That's low risk behind auth, but log the details and return a generic message instead.
- ✅ **Fixed (timeout):** **Model pulls block a request.** `pull_model` is a blocking request with a 600 s timeout (`ollama_client_manager.py:163`). Large models exceed that, and the HTTP request is held open the whole time. Stream progress, or make it a background job. _Now streamed: there's no total time limit, a stall aborts after 5 min, and errors Ollama reports partway through reach the UI. The HTTP request is still held open for the whole pull._

## Low / cleanup

- **Frontend logs the JWT.** `App.tsx:23` logs the token to the console on every render. Remove it.
- **Deprecated Pydantic config.** Pydantic v2 deprecates `class Config` (`data_models.py:69,143`, `config.py:73`). Use `model_config = ConfigDict(...)` and `SettingsConfigDict`.
- **Stray import.** `import json` sits inside the streaming loop at `ollama_client_manager.py:260`. Move it to the top.
- **Ruff:** two unused imports in `main.py` (`status`, and the bare `database.persona_store` import, which is intentional, so add `# noqa: F401`).
- **Dead code:** `OllamaClientManager.generate()` and `TelegramMessageResponse.from_attributes` (the response is built by hand in `_to_response`).
- **Persona UX:** after creating a persona nothing is selected (`Persona.tsx:50-53`). Unchecking "Active" leaves no active persona, and the backend silently falls back to the lowest id.
- **Destructive actions don't confirm:** model delete and `DELETE /telegram/messages`.
- **Stub pages:** `Setup` and `Memory` are empty, yet `Setup` is the landing route.
- **Unused Vite `outDir`:** `vite.config.ts` sets `outDir: "build"`, but Nx overrides it with `outputPath: frontend/dist`. Remove one to avoid confusion.

---

## Build, dependencies, CI

- **`requirements.txt` looks like a `pip freeze` of a desktop environment.** `pycairo`, `PyGObject`, `numpy`, `lxml`, `beautifulsoup4`, `scour`, `pyserial`, `cssselect`, `tinycss2` and others are never imported. `fastapi-cors`, `python-dotenv` and `python-multipart` are unused too. These are the only reason the Dockerfile and CI install `libcairo2-dev`, `libgirepository-2.0-dev` and `build-essential`. Trimming them would shrink the image and the build time considerably.
- **Old pins.** `fastapi==0.111.0` (with its Starlette), `httpx==0.25.2`, `python-multipart==0.0.7` and `ruff==0.3.0` are old, and some of the transitive versions have published advisories. Pin to current releases and keep a lock file. A `lock` target exists but its output isn't checked in.
- **The generated Ollama client is never used.** `backend/ollama/client/` is generated on every build (`generate_ollama_client`), but nothing imports it, since `OllamaClientManager` uses raw httpx. It also accounts for all 350 Ruff errors under `ruff check .`. Either use it or drop the target and `etc/ollama-service.yaml`.
- **`nx lint` is broken.** `etc/ruff.toml` sets `target-version = "py313"`, which the pinned `ruff==0.3.0` rejects ("unknown variant `py313`"), so the lint target can't even parse its config. Upgrade Ruff. It should also exclude `ollama/client`.
- **`nx test` fails as configured.** Nothing in `requirements-dev.txt` installs pytest, and there are no test files. The frontend has `setupTests.ts` but no tests, so Vitest exits non-zero.
- **Frontend `package.json`:** testing libraries and `@types/*` sit in `dependencies`. `@types/jest` is there although the project uses Vitest. `@types/react-router-dom@5` is wrong for RR v7, and `web-vitals` is unused. `typescript ^4.9.5` is very old next to Vite 7 / React 19.
- **Python versions:** the Docker image uses Python 3.14 while Ruff targets `py313`. Align them.
- **Nothing persists in Docker.** There is no volume for the DB, `media/` or `log/`. That is moot while C1 stands, but it matters once C1 is fixed.
- **CI** builds and pushes `:latest` on every PR, including from forks if enabled. Push only on `main`, and add lint and test steps before the image build.
- **README is stale.** It references `router.py`, `models.py`, `handlers.py` and `client_manager.py`, which no longer exist, and says `ENV_FILE` defaults to `.env.prod`. CLAUDE.md is accurate. Sync the README from it.

## Tests — suggested starting set

There are none today. The highest-value cheap tests are pure functions and DB logic:

1. `should_respond_with_ai`: private, group reply, keyword, and the substring false positives above.
2. `_postprocess_response` / `_make_typo`: length invariants and no crash on 4-letter words. Seed `random`.
3. `create_prompt` + history assembly: guards C2 against regression.
4. `persona_store`: only one active persona after create/update. This needs an in-memory `sqlite+aiosqlite` fixture.
5. `ChatState` coalescing and cancellation with fake coroutines (H3).
6. API smoke tests with `httpx.AsyncClient(app=...)`: auth required, 401 on a bad token, model delete with a slash in the name.

---

## Non-technical note

The bot is deliberately built to pass as a human. It auto-replies from a personal account, delays read receipts, fakes typing time, and injects typos, all driven by an uncensored model. Before running this against real people, consider two things:

- **Telegram's ToS on userbots:** automated activity on user accounts risks a ban.
- **EU AI Act Art. 50:** since 2 Aug 2026, people interacting with an AI system must be informed of it unless that is obvious. That applies if you or your users are in the EU.

A simple disclosure mechanism, or limiting the bot to consenting contacts, would address both.

## Suggested order of work

1. ~~C2, H1–H4, H7~~: ✅ done in `69dfac2`.
2. ~~C1~~ ✅ done. C3/C4 (secrets): small, high-impact changes.
3. Add a pytest setup with the tests above, and make `nx test` / `nx lint` green (upgrade Ruff, exclude `ollama/client`). Tests 3 and 5 would lock in the `69dfac2` fixes.
4. H5, H6: media downloads and interactive login.
5. Trim the dependencies and fix the Dockerfile and CI.

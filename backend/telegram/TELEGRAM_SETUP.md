# Telegram Bot Setup Guide

This guide explains how to set up and configure the Pyrogram Telegram user bot integration.

## Overview

The application includes a Telegram user bot that:
- Connects to Telegram as a normal user (not a bot account)
- Listens to all incoming messages from private chats, groups, and channels
- Stores messages in a SQLite database with full metadata
- Provides JWT-protected REST API endpoints to query stored messages

## Prerequisites

- Python 3.8 or higher
- Node.js and npm (for running nx)
- A Telegram account
- Telegram API credentials (see below)

## Step 1: Obtain Telegram API Credentials

Before you can use the Telegram bot, you need to obtain API credentials:

1. Go to https://my.telegram.org/auth
2. Log in with your Telegram phone number
3. Navigate to **"API development tools"** https://my.telegram.org/apps
4. Create a new application by filling out the form:
   - App title: `Alpha Project` (or any name)
   - Short name: `alpha` (or any short name)
   - Platform: `Other`
5. Copy the **API ID** and **API Hash** values


## Step 2: Configure Environment Variables

Create or update the `.env` file in the project root:

```bash
# Telegram Authentication
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef

# Optional: Customize session location
TELEGRAM_SESSION_DIR=backend/.telegram_sessions
TELEGRAM_SESSION_NAME=alpha_userbot

# Optional: Customize database location
TELEGRAM_DATABASE_URL=sqlite+aiosqlite:///backend/telegram_messages.db
```

Replace `12345678` and `0123456789abcdef0123456789abcdef` with your actual API ID and API Hash.

## Step 3: Install Dependencies

Install Python dependencies including Pyrogram, SQLAlchemy, and aiosqlite:

```bash
cd alpha
./nx create_venv backend
```

This will create a virtual environment and install all required dependencies from `backend/requirements.txt`.

## Step 4: Authenticate Your Telegram Account

**Important:** This step must be completed before running the main application for the first time.

Run the authentication script:

```bash
python3 backend/telegram/auth.py
```

The script will guide you through the authentication process:

1. **Phone Number**: Enter your phone number with country code (e.g., `+1234567890`)
2. **OTP Code**: Enter the verification code sent to your Telegram app
3. **Two-Factor Password**: If you have 2FA enabled, enter your password

After successful authentication, you'll see:

```
============================================================
✓ Authentication successful!
============================================================
Logged in as: John Doe
Username: @johndoe
User ID: 123456789
Phone: +1234567890
============================================================

Session file created at:
  /path/to/alpha/backend/.telegram_sessions/alpha_userbot.session

You can now start the main application.
============================================================
```

**Note:** The session file contains your authentication credentials. Keep it secure and never commit it to version control (it's already excluded in `.gitignore`).

## Step 5: Run the Application

Start the backend server:

```bash
./nx serve backend
```

Check the logs for successful initialization:

```
INFO:     Telegram database initialized
INFO:     Telegram client started successfully as @yourusername (ID: 123456789)
INFO:     Application startup complete.
```

The Telegram client is now running and listening for incoming messages!

## Step 6: Test the Integration

### Send a Test Message

1. Send yourself a message on Telegram (use "Saved Messages" or message any chat)
2. Check the backend logs - you should see:

```
INFO:     Received text from John Doe in Saved Messages: Hello, this is a test message
```

### Query Messages via API

The Telegram endpoints require JWT authentication. First, you'll need to generate a JWT token (or implement a login endpoint).

For testing, you can use the existing `/api/protected` endpoint pattern.

**Get Telegram Status:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://127.0.0.1:8000/api/telegram/status
```

Response:
```json
{
  "connected": true,
  "user_id": 123456789,
  "username": "johndoe",
  "message_count": 42
}
```

**Get Recent Messages:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://127.0.0.1:8000/api/telegram/messages?limit=10"
```

Response:
```json
[
  {
    "id": 1,
    "message_id": 12345,
    "chat": {
      "chat_id": 123456789,
      "chat_type": "private",
      "title": "Saved Messages"
    },
    "user": {
      "user_id": 123456789,
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe"
    },
    "text": "Hello, this is a test message",
    "message_type": "text",
    "date": "2026-03-30T12:34:56",
    "reply_to_message_id": null,
    "created_at": "2026-03-30T12:34:57"
  }
]
```

**Filter by Chat:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://127.0.0.1:8000/api/telegram/messages?chat_id=123456789&limit=50"
```

**Clear All Messages:**
```bash
curl -X DELETE -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://127.0.0.1:8000/api/telegram/messages
```

Response:
```json
{
  "success": true,
  "messages_deleted": 42
}
```

## Step 7: Inspect the Database (Optional)

You can directly query the SQLite database to inspect stored messages:

```bash
sqlite3 backend/telegram_messages.db

# List all tables
.tables

# View recent messages
SELECT * FROM telegram_messages ORDER BY date DESC LIMIT 10;

# Count messages by chat
SELECT chat_title, COUNT(*) as count
FROM telegram_messages
GROUP BY chat_id
ORDER BY count DESC;

# Exit
.quit
```

## API Endpoints Reference

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### GET /api/telegram/status

Get Telegram client connection status and message count.

**Response:**
- `connected` (boolean): Whether the client is connected
- `user_id` (integer): Telegram user ID
- `username` (string): Telegram username
- `message_count` (integer): Total messages in database

### GET /api/telegram/messages

Query stored messages with pagination and filtering.

**Query Parameters:**
- `limit` (integer, 1-1000, default: 100): Maximum messages to return
- `chat_id` (integer, optional): Filter by specific chat

**Response:** Array of message objects

### DELETE /api/telegram/messages

Clear all stored messages from the database.

**Response:**
- `success` (boolean): Whether operation succeeded
- `messages_deleted` (integer): Number of messages deleted

## Troubleshooting

### "Session file is invalid or expired"

**Solution:** Delete the session file and re-authenticate:
```bash
rm backend/.telegram_sessions/alpha_userbot.session*
python3 backend/telegram/auth.py
```

### "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"

**Solution:** Ensure your `.env` file contains valid credentials and restart the application.

### "Telegram client not initialized"

**Possible causes:**
1. Missing API credentials - check `.env` file
2. Session file doesn't exist - run `python3 backend/telegram/auth.py`
3. Connection error - check logs for detailed error messages

**Solution:** Check the backend logs for specific error messages during startup.

### "Failed to start Telegram client after 3 attempts"

**Possible causes:**
1. Network connectivity issues
2. Invalid API credentials
3. Telegram servers temporarily unavailable

**Solution:**
- Verify your internet connection
- Verify API credentials are correct
- Wait a few minutes and restart the application

### Application starts but no messages are received

**Possible causes:**
1. Telegram client failed to start (check logs)
2. Messages are being sent to a different account
3. Database write errors

**Solution:**
- Check logs for "Telegram client started successfully" message
- Verify you're sending messages to the correct Telegram account
- Check database file permissions

## Docker Deployment

When deploying with Docker, you need to include the session file:

### Option 1: Pre-authenticate locally

1. Authenticate locally: `python3 backend/telegram/auth.py`
2. Session file is created at `backend/.telegram_sessions/alpha_userbot.session`
3. Mount the session directory as a volume when running Docker:

```bash
docker run -p 8000:8000 \
  -v $(pwd)/backend/.telegram_sessions:/app/backend/.telegram_sessions \
  -e TELEGRAM_API_ID=12345678 \
  -e TELEGRAM_API_HASH=your_hash_here \
  alpha-app
```

### Option 2: Use Docker secrets (production)

Store the session file securely and mount it at runtime:

```bash
docker run -p 8000:8000 \
  -v /secure/path/telegram_sessions:/app/backend/.telegram_sessions:ro \
  -e TELEGRAM_API_ID=12345678 \
  -e TELEGRAM_API_HASH=your_hash_here \
  alpha-app
```

## Security Considerations

1. **Session Files**: Never commit session files to version control. They contain authentication credentials.

2. **API Credentials**: Store API_ID and API_HASH in environment variables or secrets management systems, never hardcode them.

3. **Database**: The SQLite database may contain sensitive message content. Ensure proper access controls.

4. **API Endpoints**: All Telegram endpoints are protected with JWT authentication. Ensure your JWT tokens are properly secured.

5. **File Permissions**: The session directory is automatically created with restricted permissions (700).

## Advanced Configuration

### Custom Session Location

Set a custom session directory:

```bash
TELEGRAM_SESSION_DIR=/var/lib/telegram/sessions
TELEGRAM_SESSION_NAME=my_custom_session
```

### Custom Database Location

Use a different database path or even PostgreSQL:

```bash
# SQLite in custom location
TELEGRAM_DATABASE_URL=sqlite+aiosqlite:///var/lib/telegram/messages.db

# PostgreSQL (requires asyncpg dependency)
TELEGRAM_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/telegram_db
```

### Disable Telegram Features

If you want to run the application without Telegram features, simply don't set the API credentials:

```bash
# Application will start without Telegram client
# Telegram endpoints will return 503 Service Unavailable
```

## Next Steps

- Implement message filtering (e.g., specific chats or keywords)
- Add WebSocket support for real-time message streaming
- Implement message search functionality
- Add support for sending messages (not just receiving)
- Implement media file download and storage
- Add message statistics and analytics

## Support

For issues or questions:
- Check the application logs: `./nx serve backend`
- Review the Pyrogram documentation: https://docs.pyrogram.org/
- Check the project README: `README.md`

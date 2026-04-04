#!/usr/bin/env python3
"""
Telegram authentication script for first-time setup.

Run this script to authenticate your Telegram account and create a session file.
The session file will be used by the main application to connect without
requiring phone number and OTP verification each time.

Usage:
    python3 backend/telegram/auth.py

You will be prompted for:
1. Phone number (with country code, e.g., +1234567890)
2. OTP code (sent to your Telegram app)
3. Two-factor password (if enabled)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrogram import Client
from config import settings


async def authenticate():
    """Authenticate Telegram account and create session file."""

    # Validate credentials
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment variables or .env file")
        print("\nTo obtain these credentials:")
        print("1. Go to https://my.telegram.org/auth")
        print("2. Log in with your phone number")
        print("3. Go to 'API development tools'")
        print("4. Create a new application")
        print("5. Copy API ID and API Hash")
        sys.exit(1)

    # Create session directory
    session_dir = Path(settings.TELEGRAM_SESSION_DIR)
    session_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Telegram Authentication Setup")
    print("=" * 60)
    print(f"\nAPI ID: {settings.TELEGRAM_API_ID}")
    print(f"Session directory: {session_dir.absolute()}")
    print(f"Session name: {settings.TELEGRAM_SESSION_NAME}")
    print("\nYou will be prompted to enter your phone number and OTP code.")
    print("=" * 60)
    print()


    # Function to provide the code (e.g., from a database, web UI, or custom logic)
    def get_code_from_source():
        # You could pull this from an API or a database
        return input("Enter the code you received: ")

    # Initialize client
    client = Client(
        name=settings.TELEGRAM_SESSION_NAME,
        api_id=int(settings.TELEGRAM_API_ID),
        api_hash=settings.TELEGRAM_API_HASH,
        workdir=str(session_dir),
        phone_number=settings.TELEGRAM_PHONE_NUMBER,
        phone_code_handler=get_code_from_source
    )

    try:
        # Start client (this will prompt for authentication)
        await client.start()

        # Get user information
        me = await client.get_me()

        print("\n" + "=" * 60)
        print("✓ Authentication successful!")
        print("=" * 60)
        print(f"Logged in as: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}")
        print(f"User ID: {me.id}")
        print(f"Phone: {me.phone_number}")
        print("=" * 60)
        print(f"\nSession file created at:")
        print(f"  {session_dir.absolute()}/{settings.TELEGRAM_SESSION_NAME}.session")
        print("\nYou can now start the main application.")
        print("The application will use this session file to connect automatically.")
        print("=" * 60)

        # Stop client
        await client.stop()

    except KeyboardInterrupt:
        print("\n\nAuthentication cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(authenticate())

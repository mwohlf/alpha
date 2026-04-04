"""
Telegram client manager for Pyrogram integration.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from pyrogram import Client
from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded

from config import settings
from telegram.handlers import handle_new_message

logger = logging.getLogger("uvicorn.error")


class TelegramClientManager:
    """Manages the Pyrogram client lifecycle and connection state."""

    def __init__(self):
        """Initialize the Telegram client manager."""
        self.client: Optional[Client] = None
        self._running = False
        self._user_id: Optional[int] = None
        self._username: Optional[str] = None

    async def start(self) -> None:
        """
        Start the Telegram client and connect to Telegram.

        Raises:
            RuntimeError: If credentials are missing or connection fails
        """
        if self._running:
            logger.warning("Telegram client is already running")
            return

        # Validate credentials
        if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
            raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

        # Create session directory if it doesn't exist
        session_dir = Path(settings.TELEGRAM_SESSION_DIR)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on session directory
        try:
            os.chmod(session_dir, 0o700)
        except Exception as e:
            logger.warning(f"Could not set session directory permissions: {e}")

        logger.info(f"Initializing Telegram client with session: {settings.TELEGRAM_SESSION_NAME}")

        # Initialize Pyrogram client
        self.client = Client(
            name=settings.TELEGRAM_SESSION_NAME,
            api_id=int(settings.TELEGRAM_API_ID),
            api_hash=settings.TELEGRAM_API_HASH,
            workdir=str(session_dir),
        )

        # Register message handler
        self.client.on_message()(handle_new_message)

        # Connect to Telegram with retry logic
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                await self.client.start()
                self._running = True

                # Get user information
                me = await self.client.get_me()
                self._user_id = me.id
                self._username = me.username

                logger.info(
                    f"Telegram client started successfully as @{self._username} (ID: {self._user_id})"
                )
                return

            except AuthKeyUnregistered:
                logger.error(
                    "Session file is invalid or expired. Please delete the session file and re-authenticate."
                )
                raise

            except SessionPasswordNeeded:
                logger.error(
                    "Two-factor authentication is enabled. Please authenticate using the auth.py script."
                )
                raise

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to start Telegram client (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to start Telegram client after {max_retries} attempts: {e}")
                    raise

    async def stop(self) -> None:
        """Gracefully stop the Telegram client."""
        if not self._running or not self.client:
            logger.warning("Telegram client is not running")
            return

        try:
            logger.info("Stopping Telegram client...")
            await self.client.stop()
            self._running = False
            self._user_id = None
            self._username = None
            logger.info("Telegram client stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Telegram client: {e}", exc_info=True)
            raise

    def is_running(self) -> bool:
        """
        Check if the Telegram client is running.

        Returns:
            True if client is connected and running, False otherwise
        """
        return self._running

    def get_user_id(self) -> Optional[int]:
        """
        Get the user ID of the authenticated Telegram account.

        Returns:
            User ID or None if not connected
        """
        return self._user_id

    def get_username(self) -> Optional[str]:
        """
        Get the username of the authenticated Telegram account.

        Returns:
            Username or None if not connected
        """
        return self._username

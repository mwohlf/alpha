"""
Telegram client manager for pyrogram integration.
"""

import logging
from typing import Optional

from pyrogram import Client
from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded

from config import settings  # ready inizialized
from telegram.handlers import handle_new_message

logger = logging.getLogger("alpha")


class TelegramClientManager:
    """Manages the pyrogram client lifecycle and connection state."""

    def __init__(self):
        """Initialize the Telegram client manager."""
        self.client: Optional[Client] = None
        self._running = False
        self._user_id: Optional[int] = None
        self._username: Optional[str] = None

    async def _authenticate(self) -> str:
        """Run interactive authentication and return the session string."""
        logger.info("No session string found — starting interactive authentication")

        auth_client = Client(
            name=settings.TELEGRAM_SESSION_NAME,
            api_id=int(settings.TELEGRAM_API_ID),
            api_hash=settings.TELEGRAM_API_HASH,
            in_memory=True,
        )

        await auth_client.start()

        me = await auth_client.get_me()
        session_string = await auth_client.export_session_string()

        logger.info(f"Authentication successful as @{me.username} (ID: {me.id})")
        logger.info(
            f"Save this session string to TELEGRAM_SESSION_STRING:\n{session_string}"
        )

        await auth_client.stop()

        return session_string

    async def start(self) -> None:
        """
        Start the Telegram client and connect to Telegram.

        If TELEGRAM_SESSION_STRING is not set, runs the interactive auth workflow first.

        Raises:
            RuntimeError: If credentials are missing or connection fails
        """
        if self._running:
            logger.warning("Telegram client is already running")
            return

        if (
            not settings.TELEGRAM_SESSION_NAME
            or not settings.TELEGRAM_API_ID
            or not settings.TELEGRAM_API_HASH
        ):
            raise RuntimeError(
                "TELEGRAM_SESSION_NAME, TELEGRAM_API_ID, and TELEGRAM_API_HASH must be set"
            )

        session_string = settings.TELEGRAM_SESSION_STRING
        if not session_string:
            session_string = await self._authenticate()

        self.client = Client(
            name=settings.TELEGRAM_SESSION_NAME,
            api_id=int(settings.TELEGRAM_API_ID),
            api_hash=settings.TELEGRAM_API_HASH,
            session_string=session_string,
        )

        # Register message handler
        self.client.on_message()(handle_new_message)

        try:
            await self.client.start()
            self._running = True

            me = await self.client.get_me()
            self._user_id = me.id
            self._username = me.username

            logger.info(
                f"Telegram client started successfully as @{self._username} (ID: {self._user_id})"
            )

        except AuthKeyUnregistered:
            logger.error("Session is invalid or expired. Please re-authenticate.")
            raise

        except SessionPasswordNeeded:
            logger.error(
                "Two-factor authentication is enabled. Please authenticate using the auth.py script."
            )
            raise

        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
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
        return self._running

    def get_user_id(self) -> Optional[int]:
        return self._user_id

    def get_username(self) -> Optional[str]:
        return self._username

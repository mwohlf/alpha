"""
Ollama client manager for managing LLM interactions.
"""

import logging
from typing import AsyncGenerator, Dict, List, Optional

import httpx

logger = logging.getLogger("alpha")


class OllamaClientManager:
    """Manages the Ollama client connection and provides chat functionality."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.2:3b",
    ):
        """
        Initialize the Ollama client manager.

        Args:
            base_url: The base URL of the Ollama server
            default_model: The default model to use for chat
        """
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False

    async def start(self) -> None:
        """
        Start the Ollama client and verify connection.

        Raises:
            RuntimeError: If connection to Ollama fails
        """
        if self._running:
            logger.warning("Ollama client is already running")
            return

        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(60.0, connect=5.0),
            )

            # Verify connection by checking version
            response = await self._client.get("/api/version")
            response.raise_for_status()
            version_data = response.json()

            self._running = True
            logger.info(
                f"Ollama client started successfully (version: {version_data.get('version', 'unknown')})"
            )

            # Try to list available models
            try:
                models = await self.list_models()
                if models:
                    model_names = [m.get("name", "unknown") for m in models[:5]]
                    logger.info(f"Available models: {', '.join(model_names)}")
                else:
                    logger.warning(
                        "No models available. You may need to pull a model first."
                    )
            except Exception as e:
                logger.warning(f"Could not list models: {e}")

        except httpx.ConnectError:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start Ollama client: {e}")

    async def stop(self) -> None:
        """Gracefully stop the Ollama client."""
        if not self._running or not self._client:
            logger.warning("Ollama client is not running")
            return

        try:
            logger.info("Stopping Ollama client...")
            await self._client.aclose()
            self._running = False
            logger.info("Ollama client stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Ollama client: {e}", exc_info=True)
            raise

    def is_running(self) -> bool:
        """
        Check if the Ollama client is running.

        Returns:
            True if client is connected and running, False otherwise
        """
        return self._running

    async def list_models(self) -> List[Dict]:
        """
        List all available models.

        Returns:
            List of model information dictionaries

        Raises:
            RuntimeError: If client is not running or request fails
        """
        if not self._running or not self._client:
            raise RuntimeError("Ollama client is not running")

        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Error listing models: {e}", exc_info=True)
            raise RuntimeError(f"Failed to list models: {e}")

    async def delete_model(self, name: str) -> None:
        """
        Delete a locally available model.

        Args:
            name: Model name to delete (e.g. "llama3:latest")

        Raises:
            RuntimeError: If client is not running or request fails
        """
        if not self._running or not self._client:
            raise RuntimeError("Ollama client is not running")

        try:
            response = await self._client.request("DELETE", "/api/delete", json={"name": name})
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error deleting model {name}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to delete model: {e}")

    async def pull_model(self, name: str) -> None:
        """
        Pull a model from the Ollama registry (non-streaming).

        Args:
            name: Model name to pull (e.g. "llama3:latest")

        Raises:
            RuntimeError: If client is not running or request fails
        """
        if not self._running or not self._client:
            raise RuntimeError("Ollama client is not running")

        try:
            response = await self._client.post(
                "/api/pull",
                json={"name": name, "stream": False},
                timeout=600.0,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error pulling model {name}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to pull model: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        **options,
    ) -> Dict:
        """
        Send a chat request to Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (defaults to self.default_model)
            stream: Whether to stream the response
            **options: Additional model options (temperature, top_p, etc.)

        Returns:
            Response dictionary from Ollama

        Raises:
            RuntimeError: If client is not running or request fails
        """
        if not self._running or not self._client:
            raise RuntimeError("Ollama client is not running")

        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if options:
            payload["options"] = options

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during chat: {e.response.status_code} - {e.response.text}"
            )
            raise RuntimeError(f"Chat request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error during chat: {e}", exc_info=True)
            raise RuntimeError(f"Chat request failed: {e}")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **options,
    ) -> AsyncGenerator[Dict, None]:
        """
        Send a streaming chat request to Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (defaults to self.default_model)
            **options: Additional model options (temperature, top_p, etc.)

        Yields:
            Response chunks from Ollama

        Raises:
            RuntimeError: If client is not running or request fails
        """
        if not self._running or not self._client:
            raise RuntimeError("Ollama client is not running")

        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        if options:
            payload["options"] = options

        try:
            async with self._client.stream(
                "POST", "/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json

                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse JSON line: {line}")
        except Exception as e:
            logger.error(f"Error during streaming chat: {e}", exc_info=True)
            raise RuntimeError(f"Streaming chat request failed: {e}")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        **options,
    ) -> Dict:
        """
        Generate a completion for a prompt.

        Args:
            prompt: The prompt text
            model: Model name to use (defaults to self.default_model)
            stream: Whether to stream the response
            **options: Additional model options (temperature, top_p, etc.)

        Returns:
            Response dictionary from Ollama

        Raises:
            RuntimeError: If client is not running or request fails
        """
        if not self._running or not self._client:
            raise RuntimeError("Ollama client is not running")

        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }

        if options:
            payload["options"] = options

        try:
            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error during generate: {e}", exc_info=True)
            raise RuntimeError(f"Generate request failed: {e}")

"""
Ollama service client wrapper for convenient access to Ollama API.
This module provides methods to interact with the Ollama service.
"""

from config import settings
from typing import Optional, List, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Wrapper for interacting with Ollama API"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL. Defaults to localhost:11434
        """
        self.base_url = base_url or "http://localhost:11434"
        self.client = httpx.Client(base_url=self.base_url)
    
    def list_models(self) -> Dict[str, Any]:
        """List all available models in Ollama"""
        try:
            response = self.client.get("/api/tags")
            return response.json()
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise
    
    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull/download a model from Ollama library"""
        try:
            response = self.client.post(
                "/api/pull",
                json={"name": model_name}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            raise
    
    def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using a specified model.
        
        Args:
            model: Model name to use
            prompt: Input prompt for generation
            stream: Whether to stream the response
            **kwargs: Additional options (temperature, top_k, etc.)
        
        Returns:
            Generated response dict
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
            }
            payload.update(kwargs)
            
            response = self.client.post("/api/generate", json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Error generating with model {model}: {e}")
            raise
    
    def embed(self, model: str, prompt: str) -> Dict[str, Any]:
        """
        Generate embeddings using a specified model.
        
        Args:
            model: Model name to use
            prompt: Input text for embedding
        
        Returns:
            Embedding response dict
        """
        try:
            response = self.client.post(
                "/api/embed",
                json={"model": model, "input": prompt}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def show_model(self, model: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        try:
            response = self.client.post(
                "/api/show",
                json={"name": model}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error showing model {model}: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()


# Singleton instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client singleton"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

from fastapi import APIRouter, Depends

from endpoints.auth import verify_token
from endpoints.deps import get_ollama_manager
from endpoints.models import ChatRequest, ChatResponse
from ollama.ollama_client import OllamaClientManager

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    body: ChatRequest,
    ollama: OllamaClientManager = Depends(get_ollama_manager),
    _token: str = Depends(verify_token),
) -> ChatResponse:
    messages = [{"role": m.role, "content": m.content} for m in body.history]
    messages.append({"role": "user", "content": body.message})

    result = await ollama.chat(messages)
    reply = result.get("message", {}).get("content", "")
    return ChatResponse(reply=reply)

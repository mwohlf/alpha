from fastapi import APIRouter, Depends, HTTPException, status

from endpoints.auth import verify_token
from endpoints.data_models import ChatRequest, ChatResponse
from endpoints.dependencies import get_ollama_manager
from ollama.ollama_client_manager import OllamaClientManager
from ollama.prompt_handler import create_prompt

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_token)])


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    body: ChatRequest, ollama: OllamaClientManager = Depends(get_ollama_manager)
) -> ChatResponse:
    """
    message interaction with the frontend
    """
    history = [{"role": m.role, "content": m.content} for m in body.history]
    reply = await create_prompt(ollama, body.message, history=history)
    if reply is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No response from Ollama.",
        )
    return ChatResponse(reply=reply)

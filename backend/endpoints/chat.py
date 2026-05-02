import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

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
    messages = await create_prompt(body.message, history=history)
    response = await ollama.chat(messages=messages, model=body.model)
    reply = response.get("message", {}).get("content") or None
    if reply is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No response from Ollama.",
        )
    return ChatResponse(reply=reply)


@router.post("/stream")
async def chat_stream_endpoint(
    request: Request,
    body: ChatRequest,
    ollama: OllamaClientManager = Depends(get_ollama_manager),
) -> StreamingResponse:
    """
    Streaming SSE chat endpoint. Disconnecting the client aborts the Ollama request.
    """
    history = [{"role": m.role, "content": m.content} for m in body.history]
    messages = await create_prompt(body.message, history=history)

    async def generate():
        try:
            async for chunk in ollama.chat_stream(messages=messages, model=body.model):
                if await request.is_disconnected():
                    break
                content = chunk.get("message", {}).get("content", "")
                done = chunk.get("done", False)
                yield f"data: {json.dumps({'content': content, 'done': done})}\n\n"
                if done:
                    break
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

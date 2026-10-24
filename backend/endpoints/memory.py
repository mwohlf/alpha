from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from config import settings
from database.memory_store import ChatMemory, get_memories, get_memory, save_memory
from database.message_store import get_chats, get_media_messages, get_message
from endpoints.auth import verify_token
from endpoints.data_models import ChatMemoryResponse, ChatMemoryUpdateRequest, MediaItemResponse
from endpoints.dependencies import get_ollama_manager
from ollama.memory_handler import update_chat_memory
from ollama.ollama_client_manager import OllamaClientManager

router = APIRouter(prefix="/memory", tags=["memory"], dependencies=[Depends(verify_token)])


async def _find_chat(chat_id: int) -> dict:
    chat = next((c for c in await get_chats() if c["chat_id"] == chat_id), None)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


def _to_response(chat: dict, memory: ChatMemory | None) -> ChatMemoryResponse:
    return ChatMemoryResponse(
        chat_id=chat["chat_id"],
        chat_type=chat["chat_type"],
        title=chat["chat_title"],
        facts=memory.facts if memory else "",
        updated_at=memory.updated_at if memory else None,
    )


@router.get(
    "",
    response_model=list[ChatMemoryResponse],
    operation_id="get_memories",
    summary="List the long-term memory of every chat, most recently active first",
)
async def list_memories() -> list[ChatMemoryResponse]:
    memories = {m.chat_id: m for m in await get_memories()}
    return [_to_response(c, memories.get(c["chat_id"])) for c in await get_chats()]


@router.put(
    "/{chat_id}",
    response_model=ChatMemoryResponse,
    operation_id="update_memory",
    summary="Replace a chat's facts (empty text forgets everything)",
)
async def edit_memory(chat_id: int, body: ChatMemoryUpdateRequest) -> ChatMemoryResponse:
    chat = await _find_chat(chat_id)
    return _to_response(chat, await save_memory(chat_id, body.facts.strip()))


@router.post(
    "/{chat_id}/refresh",
    response_model=ChatMemoryResponse,
    operation_id="refresh_memory",
    summary="Fold the chat's messages since the last update into its facts now",
)
async def refresh_memory(
    chat_id: int, ollama: OllamaClientManager = Depends(get_ollama_manager)
) -> ChatMemoryResponse:
    chat = await _find_chat(chat_id)
    try:
        await update_chat_memory(ollama, chat_id, chat["chat_type"] != "private", force=True)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return _to_response(chat, await get_memory(chat_id))


@router.get(
    "/{chat_id}/media",
    response_model=list[MediaItemResponse],
    operation_id="get_chat_media",
    summary="List the media users sent in a chat, newest first",
)
async def list_chat_media(chat_id: int) -> list[MediaItemResponse]:
    return [
        MediaItemResponse(
            id=m.id,
            message_type=m.message_type,
            caption=m.text,
            sender=m.first_name or m.username,
            date=m.date,
        )
        for m in await get_media_messages(chat_id)
    ]


@router.get(
    "/media/{media_id}",
    response_class=FileResponse,
    responses={200: {"content": {"application/octet-stream": {}}}},
    operation_id="get_media",
    summary="Download a media file a user sent",
)
async def download_media(media_id: int) -> FileResponse:
    message = await get_message(media_id)
    media_dir = settings.media_path
    path = (media_dir / message.file_path).resolve() if message and message.file_path else None
    if path is None or not path.is_relative_to(media_dir) or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    return FileResponse(path)

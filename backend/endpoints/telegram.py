from fastapi import APIRouter, Depends, HTTPException, Query, status

from endpoints.auth import verify_token
from endpoints.dependencies import get_telegram_manager
from endpoints.data_models import (
    TelegramChatInfo,
    TelegramClearResponse,
    TelegramMessageResponse,
    TelegramStatusResponse,
    TelegramUserSummary,
)
from telegram.message_store import (
    clear_messages,
    get_message_count,
    get_messages_by_user,
    get_recent_messages,
    get_users,
)

router = APIRouter(
    prefix="/telegram", tags=["telegram"], dependencies=[Depends(verify_token)]
)


def _to_response(msg) -> TelegramMessageResponse:
    return TelegramMessageResponse(
        id=msg.id,
        message_id=msg.message_id,
        chat=TelegramChatInfo(
            chat_id=msg.chat_id, chat_type=msg.chat_type, title=msg.chat_title
        ),
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        username=msg.username,
        first_name=msg.first_name,
        last_name=msg.last_name,
        text=msg.text,
        message_type=msg.message_type,
        date=msg.date,
        reply_to_message_id=msg.reply_to_message_id,
        created_at=msg.created_at,
    )


@router.get(
    "/status",
    summary="Get Telegram client status",
    response_model=TelegramStatusResponse,
    operation_id="get_telegram_status",
)
async def get_telegram_status(
    telegram_manager=Depends(get_telegram_manager),
) -> TelegramStatusResponse:
    return TelegramStatusResponse(
        connected=telegram_manager.is_running(),
        user_id=telegram_manager.get_user_id(),
        username=telegram_manager.get_username(),
        message_count=await get_message_count(),
    )


@router.get(
    "/messages",
    summary="Get recent Telegram messages",
    response_model=list[TelegramMessageResponse],
    operation_id="get_telegram_messages",
)
async def get_telegram_messages(
    telegram_manager=Depends(get_telegram_manager),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of messages to return"
    ),
    chat_id: int | None = Query(None, description="Filter by chat ID"),
) -> list[TelegramMessageResponse]:
    try:
        messages = await get_recent_messages(limit=limit, chat_id=chat_id)
        return [_to_response(msg) for msg in messages]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )


@router.delete(
    "/messages",
    summary="Clear all Telegram messages",
    response_model=TelegramClearResponse,
    operation_id="clear_telegram_messages",
)
async def clear_telegram_messages(
    telegram_manager=Depends(get_telegram_manager),
) -> TelegramClearResponse:
    try:
        return TelegramClearResponse(
            success=True, messages_deleted=await clear_messages()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear messages: {str(e)}",
        )


@router.get(
    "/users",
    summary="Get distinct users from stored messages",
    response_model=list[TelegramUserSummary],
    operation_id="get_telegram_users",
)
async def get_telegram_users(
    telegram_manager=Depends(get_telegram_manager),
) -> list[TelegramUserSummary]:
    try:
        return [TelegramUserSummary(**row) for row in await get_users()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.get(
    "/users/{sender_id}/messages",
    summary="Get messages for a specific user",
    response_model=list[TelegramMessageResponse],
    operation_id="get_telegram_user_messages",
)
async def get_telegram_user_messages(
    sender_id: int,
    telegram_manager=Depends(get_telegram_manager),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of messages to return"
    ),
) -> list[TelegramMessageResponse]:
    try:
        messages = await get_messages_by_user(sender_id=sender_id, limit=limit)
        return [_to_response(msg) for msg in messages]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )

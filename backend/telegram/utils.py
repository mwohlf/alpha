"""
Telegram message utility functions.
"""

from pyrogram.types import Message


def get_message_type(message: Message) -> str:
    if message.text:
        return "text"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.audio:
        return "audio"
    elif message.voice:
        return "voice"
    elif message.document:
        return "document"
    elif message.sticker:
        return "sticker"
    elif message.animation:
        return "animation"
    elif message.poll:
        return "poll"
    elif message.location:
        return "location"
    elif message.contact:
        return "contact"
    else:
        return "other"


def should_respond_with_ai(message: Message) -> bool:
    if message.outgoing:
        return False
    if message.chat.type.value == "private":
        return True
    if message.reply_to_message and message.reply_to_message.outgoing:
        return True
    if message.text:
        text_lower = message.text.lower()
        if any(kw in text_lower for kw in ["bot", "ai", "help"]):
            return True
    return False

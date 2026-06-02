"""Канал MAX (через Wazzup) — переводчик формата (Шаг 1).

Задача: превратить сырой вебхук Wazzup в наш внутренний объект `InboundMessage`,
чтобы остальной код (роутер, память, мозг F1) НЕ знал про вендора. Новый канал =
новый переводчик, ядро не меняется.

Здесь же ставим метку `is_from_lead`: своя отправка (`isEcho`) или реплика продавца
(`authorId` == продавец) — это НЕ входящее лида. Само переключение режима — Шаг 5.
"""

from dataclasses import dataclass
from typing import Optional

from app import config


@dataclass
class InboundMessage:
    """Наш внутренний формат входящего (канал-независимый)."""

    message_id: str          # uuid сообщения Wazzup — ключ идемпотентности (Шаг 2)
    channel: str             # "max" / "whatsapp" / ... (из chatType)
    chat_id: str             # id чата/диалога в канале
    text: str                # текст сообщения (может быть пустым у медиа)
    phone: Optional[str]     # телефон, если канал его отдал (для MAX — не всегда)
    is_from_lead: bool       # True = это реплика лида; False = наша/продавца (не реагируем)
    author_id: Optional[str] # кто отправил (для опознания продавца)


def translate(payload: dict) -> InboundMessage:
    """Wazzup-вебхук (одно сообщение) → InboundMessage.

    Поля Wazzup по контракту (block-0.md): messageId, chatType, chatId,
    contact.phone, text, isEcho, authorId.
    """
    is_echo = bool(payload.get("isEcho", False))
    author_id = payload.get("authorId")

    # Реплика продавца: настроен id продавца и он совпал с автором.
    is_seller = bool(config.SELLER_AUTHOR_ID) and author_id == config.SELLER_AUTHOR_ID

    contact = payload.get("contact") or {}

    return InboundMessage(
        message_id=payload.get("messageId", ""),
        channel=payload.get("chatType", ""),
        chat_id=payload.get("chatId", ""),
        text=payload.get("text", "") or "",
        phone=contact.get("phone"),
        is_from_lead=not (is_echo or is_seller),
        author_id=author_id,
    )

"""Память — блокнот диалога, один НА ЧЕЛОВЕКА (лида), не на канал. Шаг 6.

Ключ — lead_id (личность), поэтому сообщения из разных каналов одного человека
ложатся в ОДИН блокнот (роутер свёл каналы к одному лиду на Шаге 4). Живёт в Redis
(список) → переживает рестарт. Дописываем КАЖДОЕ сообщение, в т.ч. пока бот молчит.

Это главный склад ПД (152-ФЗ: срок хранения / сервер в РФ / доступ — на деплое).
В ЛОГ текст НЕ пишем (только метки). Срез+сводку для модели готовит F1, не Блок 0.
"""

import json
import logging
from datetime import datetime

from app.config import UFA_TZ
from app.redis_client import get_redis

logger = logging.getLogger("block0.memory")


def _decode(v):
    return v.decode() if isinstance(v, (bytes, bytearray)) else v


def _key(lead_id):
    return f"mem:{lead_id}"


def append(lead_id, role, text, channel=None, message_id=None):
    """Дописать сообщение в блокнот лида. role: 'lead' | 'seller' | 'bot' (F1)."""
    if not lead_id:
        return
    entry = {
        "role": role,
        "text": text,
        "channel": channel,
        "message_id": message_id,
        "ts": datetime.now(UFA_TZ).isoformat(),
    }
    get_redis().rpush(_key(lead_id), json.dumps(entry, ensure_ascii=False))
    logger.info("в память: lead=%s role=%s", lead_id, role)  # без текста — ПД


def history(lead_id, limit=None):
    """Вернуть историю диалога лида (старые→новые). limit — последние N сообщений."""
    raw = get_redis().lrange(_key(lead_id), 0, -1)
    entries = [json.loads(_decode(x)) for x in raw]
    return entries[-limit:] if limit is not None else entries


def count(lead_id):
    """Сколько сообщений в блокноте лида."""
    return get_redis().llen(_key(lead_id))

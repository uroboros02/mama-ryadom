"""Роутер — вахта на входе (растёт по шагам).

Шаг 2: идемпотентность по messageId — не сработать дважды на ретрай Wazzup.
Шаг 4: опознать → ОДИН лид (искать до создания) + ворота лид/действующий клиент.

Опознаём по НАДЁЖНЫМ ключам (id канала / телефон), НЕ по имени (тёзок много).
Своего поиска лида по контакту в Fitbase API нет → держим свой индекс канал→lead_id
в Redis (см. docs/fitbase-integration.md).
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.redis_client import get_redis

logger = logging.getLogger("block0.router")

# Сколько помним «уже видели этот messageId». Ретраи приходят за минуты/часы —
# суток хватает с запасом, дальше держать незачем (не растим Redis).
SEEN_TTL_SECONDS = 60 * 60 * 24


def already_processed(message_id: str) -> bool:
    """True, если этот messageId уже обрабатывали (повтор → молча выкинуть).

    Атомарно: SET key NX EX. «Поставилось» = первый раз (вернёт False),
    «уже было» = повтор (вернёт True). Гонка двух ретраев исключена.
    """
    if not message_id:
        # Без id идемпотентность не гарантируем — пропускаем как новое
        # (на Шаге 1 messageId у Wazzup всегда есть; это страховка от пустого).
        return False
    r = get_redis()
    key = f"seen:msg:{message_id}"
    first_time = r.set(key, "1", nx=True, ex=SEEN_TTL_SECONDS)
    return not first_time


# ============================ Шаг 4: опознание + ворота ============================

@dataclass
class RouteResult:
    action: str                  # "to_admin" (действующий клиент) | "lead"
    lead_id: Optional[str] = None
    created: bool = False        # создали лид подстраховкой (True) или нашли (False)


def identity_keys(msg) -> dict:
    """Надёжные ключи личности из входящего. ИМЯ сюда не входит (тёзки)."""
    keys = {}
    if msg.chat_id:
        keys[msg.channel] = msg.chat_id     # напр. {"max": "chat-777"}
    if msg.phone:
        keys["phone"] = msg.phone
    return keys


def _decode(v):
    return v.decode() if isinstance(v, (bytes, bytearray)) else v


def _lookup_index(keys) -> Optional[str]:
    """Найти lead_id в своём индексе по любому надёжному ключу."""
    r = get_redis()
    for k, v in keys.items():
        lead_id = r.get(f"idx:{k}:{v}")
        if lead_id:
            return _decode(lead_id)
    return None


def _index_keys(keys, lead_id):
    """Запомнить связку «ключ канала → lead_id» (мультиканальная склейка одного человека)."""
    r = get_redis()
    for k, v in keys.items():
        r.set(f"idx:{k}:{v}", lead_id)


def route(msg, window) -> RouteResult:
    """Опознать входящее: действующий клиент → к админу; иначе → один лид (искать до создания)."""
    keys = identity_keys(msg)

    # ВОРОТА: действующий клиент по надёжному ключу → бот off, чат админу (до памяти/мозга).
    if window.active_client_by_contact(keys) is not None:
        logger.info("ворота: действующий клиент → бот off, к админу")
        return RouteResult(action="to_admin")

    # ОПОЗНАТЬ → ОДИН лид: сначала ищем в своём индексе.
    lead_id = _lookup_index(keys)
    if lead_id:
        logger.info("опознан существующий лид: id=%s", lead_id)
        return RouteResult(action="lead", lead_id=lead_id, created=False)

    # Не нашли → создаём ПОДСТРАХОВКОЙ и индексируем все ключи.
    idem = "lead:" + "|".join(f"{k}={v}" for k, v in sorted(keys.items()))
    lead = window.create_lead(idem, **keys)
    if lead is None:
        # кто-то уже создал параллельно — перечитаем индекс
        lead_id = _lookup_index(keys)
        return RouteResult(action="lead", lead_id=lead_id, created=False)
    _index_keys(keys, lead["id"])
    logger.info("создан новый лид: id=%s", lead["id"])
    return RouteResult(action="lead", lead_id=lead["id"], created=True)

"""Режимы бота на лида — кто за рулём чата (стоп-кран). Шаг 5.

Состояния (см. block-0.md «Режимы бота»):
  · АВТО   — бот ведёт диалог (рабочий режим F1);
  · РУЧНОЙ — человек за рулём, бот молчит ПО ЭТОМУ ЛИДУ (с другими работает).

ЧУВСТВИТЕЛЬНЫЙ handoff реализационно = тот же РУЧНОЙ (выход только ручным #старт).
На старте авто-возврат по тишине отложен → выход из РУЧНОГО только #старт (решено 2026-06-02).

Состояние живёт в Redis → переживает рестарт. Команды #стоп/#старт приходят из
TG-алерта продавцу (НЕ из клиентского чата) — здесь это функции, которые дёргает алерт.
"""

import logging

from app import config
from app.redis_client import get_redis

logger = logging.getLogger("block0.state")

MODE_AUTO = "auto"
MODE_MANUAL = "manual"

AUTOSTOP_WINDOW_SEC = 60


def _decode(v):
    return v.decode() if isinstance(v, (bytes, bytearray)) else v


def _mode_key(lead_id):
    return f"mode:{lead_id}"


def get_mode(lead_id) -> str:
    """Текущий режим лида (по умолчанию АВТО)."""
    v = get_redis().get(_mode_key(lead_id))
    return _decode(v) if v is not None else MODE_AUTO


def is_silenced(lead_id) -> bool:
    """Бот молчит по этому лиду? (РУЧНОЙ режим)."""
    return get_mode(lead_id) == MODE_MANUAL


def set_manual(lead_id, reason=""):
    """Перевести лида в РУЧНОЙ (человек за рулём). Бот молчит по нему до #старт."""
    get_redis().set(_mode_key(lead_id), MODE_MANUAL)
    logger.info("режим РУЧНОЙ: lead=%s причина=%s", lead_id, reason)


def set_auto(lead_id):
    """Вернуть бота на лида (#старт)."""
    get_redis().delete(_mode_key(lead_id))
    logger.info("режим АВТО (#старт): lead=%s", lead_id)


def handle_command(lead_id, command) -> bool:
    """Команда продавца из TG-алерта: #стоп → РУЧНОЙ, #старт → АВТО. True, если применили."""
    cmd = (command or "").strip().lstrip("#").lower()
    if cmd in ("стоп", "stop"):
        set_manual(lead_id, reason="#стоп")
        return True
    if cmd in ("старт", "start"):
        set_auto(lead_id)
        return True
    logger.warning("неизвестная команда управления: %r (lead=%s)", command, lead_id)
    return False


def bump_and_check_autostop(lead_id) -> bool:
    """Счётчик сообщений лида за минуту. True, если превышен порог (анти-зацикливание)."""
    r = get_redis()
    key = f"rate:{lead_id}"
    n = r.incr(key)
    if n == 1:
        r.expire(key, AUTOSTOP_WINDOW_SEC)
    return n > config.AUTOSTOP_MAX_PER_MIN

"""Единая точка подключения к Redis.

Один клиент на процесс (ленивое создание). Им пользуются идемпотентность (Шаг 2)
и память за человеком (Шаг 6). В тестах подменяется на fakeredis через set_redis().
"""

from typing import Optional

import redis

from app import config

_client: Optional["redis.Redis"] = None


def get_redis() -> "redis.Redis":
    """Вернуть общий Redis-клиент (создаётся при первом обращении).

    REDIS_URL=fakeredis → in-process Redis (дев-режим Фазы А: без установки сервера,
    всё в процессе). Иначе — настоящий Redis по URL (Фаза Б / локальный сервер).
    """
    global _client
    if _client is None:
        if config.REDIS_URL == "fakeredis":
            import fakeredis
            _client = fakeredis.FakeStrictRedis()
        else:
            _client = redis.from_url(config.REDIS_URL)
    return _client


def set_redis(client) -> None:
    """Подменить клиент (для тестов — fakeredis)."""
    global _client
    _client = client

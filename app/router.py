"""Роутер — вахта на входе (растёт по шагам).

Шаг 2: идемпотентность по messageId — не сработать дважды на ретрай Wazzup.
Дальше (Шаг 4) сюда добавится опознание лида и ворота.
"""

from app.redis_client import get_redis

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

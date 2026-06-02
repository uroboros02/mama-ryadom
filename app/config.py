"""ТЕХ-конфиг Блока 0: env-настройки, часовой пояс Уфа, лимиты.

Здесь только техника (трубы и предохранители). Бизнес-фактбук (направления,
прайс, персона Элина) живёт в docs/config.md и относится к F1 — не сюда.
"""

import os
from datetime import timezone, timedelta

# --- Часовой пояс: Уфа (UTC+5) — ОДНИМ местом на весь проект. -----------------
# В России нет перехода на летнее время, поэтому фиксированный сдвиг +5 — надёжно.
# Все дедлайны/напоминания/тихие часы считаем относительно этого TZ.
UFA_TZ = timezone(timedelta(hours=5), name="Уфа")


def _get(name: str, default: str) -> str:
    """Прочитать настройку из окружения; если нет — взять разумное значение по умолчанию."""
    return os.getenv(name, default)


# --- Настройки (на Шаге 0 это просто значения; реальная логика — на след. шагах) ---

# Лимит обращений к Fitbase: турникет ≤20 запросов в секунду (Шаг 3).
FITBASE_MAX_RPS = int(_get("FITBASE_MAX_RPS", "20"))

# Автостоп: если по одному лиду за минуту прошло больше этого числа сообщений —
# что-то зациклилось → глушим бота в РУЧНОЙ + алерт продавцу (Шаг 5).
AUTOSTOP_MAX_PER_MIN = int(_get("AUTOSTOP_MAX_PER_MIN", "10"))

# Подключение к Redis. В тестах подменяется на fakeredis (Шаг 0 теста).
REDIS_URL = _get("REDIS_URL", "redis://localhost:6379/0")

# Общий секрет вебхука Wazzup: приходит в заголовке `Authorization: Bearer <crmKey>`.
# Его задаём МЫ в кабинете Wazzup; чужой/пустой Bearer → дверь отбивает запрос (Шаг 1).
WAZZUP_WEBHOOK_SECRET = _get("WAZZUP_WEBHOOK_SECRET", "dev-secret-change-me")

# id автора-продавца в Wazzup. Реплики с этим authorId — это человек за рулём,
# не сообщение лида (помечаем; переключение в РУЧНОЙ — Шаг 5).
SELLER_AUTHOR_ID = _get("SELLER_AUTHOR_ID", "")

# Доступ к Fitbase (CRM). Токен — в env, НЕ в коде (152-ФЗ / безопасность).
# На Фазе А не используется (работаем на mock), нужен на Фазе Б (триал).
FITBASE_TOKEN = _get("FITBASE_TOKEN", "")
FITBASE_DOMAIN = _get("FITBASE_DOMAIN", "")
FITBASE_BASE_URL = _get("FITBASE_BASE_URL", "https://api.fitbase.io/api/v2/")

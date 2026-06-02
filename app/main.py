"""FastAPI-каркас Блока 0: пульс + приём вебхука.

Шаг 0: голые рельсы (/health, /webhook отвечал 200 на всё).
Шаг 1: /webhook стал настоящей дверью —
  · замок: проверка `Authorization: Bearer <crmKey>` (чужой → 401, в обработку не идёт);
  · быстрый ack: валидный → 200 СРАЗУ, разбор фоном (BackgroundTasks, без Celery);
  · переводчик: Wazzup-формат → наш InboundMessage (app/channel_max.py);
  · метка эхо/продавец: своё/продавца → is_from_lead=False (стоп-кран, кирпич 1).

Логики дальше (дедуп messageId, поиск лида, режимы, память) ПОКА НЕТ — Шаги 2–8.
Клиенту бот не пишет: Блок 0 — только трубы и предохранители.
"""

import logging

from fastapi import BackgroundTasks, FastAPI, Header, Request, Response

from app import config, channel_max

# Блок 0 проверяется «по приборам» (логам) → INFO обязан печататься.
# В лог НЕ пишем ПД (телефон/текст) — только технические метки.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("block0.webhook")

app = FastAPI(title="Мама рядом — Блок 0 (канал MAX)")


@app.get("/health")
async def health():
    """Пульс: сервер поднят и отвечает."""
    return {"status": "ok"}


def _process_messages(messages: list) -> None:
    """Фоновый разбор пачки сообщений. На Шаге 1 — перевод + лог (бот клиенту не пишет).

    Дальнейшие станции (дедуп, поиск лида, ворота, память) подключатся на Шагах 2–8.
    """
    for raw in messages:
        msg = channel_max.translate(raw)
        logger.info(
            "входящее: channel=%s chat=%s msg_id=%s from_lead=%s",
            msg.channel, msg.chat_id, msg.message_id, msg.is_from_lead,
        )


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(default=""),
):
    """Входящая дверь канала: замок → быстрый ack → разбор фоном.

    Дверь публичная → проверяем общий секрет. Тело разбираем ПОСЛЕ ответа 200,
    чтобы ретраи Wazzup не копились (старый баг плодил дубли).

    Wazzup шлёт на один URL разные конверты:
      · {"test": true}        — пробный пинг при подключении (ждёт 200, иначе не сохранит URL);
      · {"messages": [...]}   — входящие сообщения (пачкой);
      · {"statuses": [...]}   — статусы доставки и прочее → молча игнорируем (тоже 200).
    """
    # Замок: ожидаем ровно "Bearer <наш секрет>". Иначе — отбой, в обработку не идём.
    expected = f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"
    if authorization != expected:
        logger.warning("вебхук отбит: неверный Authorization")
        return Response(status_code=401)

    payload = await request.json()

    # Пробный пинг подключения — просто подтверждаем.
    if payload.get("test"):
        return {"received": True}

    # Сообщения разбираем фоном; всё остальное (statuses и пр.) молча пропускаем.
    messages = payload.get("messages")
    if messages:
        background_tasks.add_task(_process_messages, messages)

    return {"received": True}

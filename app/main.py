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

from app import config, channel_max, router, state
from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock
from app.mocks.alert_mock import AlertMock

# Блок 0 проверяется «по приборам» (логам) → INFO обязан печататься.
# В лог НЕ пишем ПД (телефон/текст) — только технические метки.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("block0.webhook")

app = FastAPI(title="Мама рядом — Блок 0 (канал MAX)")

# Окно Fitbase: на Фазе А поверх mock. Провайдер подменяется в тестах (set_window).
_window = None


def get_window():
    global _window
    if _window is None:
        _window = FitbaseWindow(FitbaseMock(), alert=AlertMock())
    return _window


def set_window(window):
    global _window
    _window = window


def _alert(text):
    """Эскалация продавцу: в коробку алертов окна + лог."""
    w = get_window()
    if getattr(w, "alert", None) is not None:
        w.alert.push(text)
    logger.warning("ЭСКАЛАЦИЯ: %s", text)


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

        # Идемпотентность: повтор того же messageId (ретрай Wazzup) — молча выкинуть.
        if router.already_processed(msg.message_id):
            logger.info("повтор, пропущен: msg_id=%s", msg.message_id)
            continue

        logger.info(
            "входящее: channel=%s chat=%s msg_id=%s from_lead=%s",
            msg.channel, msg.chat_id, msg.message_id, msg.is_from_lead,
        )

        # Своя отправка / реплика продавца → человек взял руль: лид в РУЧНОЙ (стоп-кран).
        # (В Блоке 0 бот клиенту не пишет, значит эхо = продавец. Когда F1 начнёт
        #  отправлять — свои отправки надо будет помечать, чтобы не глушить самих себя.)
        if not msg.is_from_lead:
            lead_id = router.lookup_lead_id(msg)
            if lead_id and not state.is_silenced(lead_id):
                state.set_manual(lead_id, reason="реплика продавца/эхо")
            continue

        # Опознать → один лид + ворота (лид / действующий клиент → к админу).
        result = router.route(msg, get_window())
        logger.info("маршрут: action=%s lead=%s created=%s",
                    result.action, result.lead_id, result.created)
        if result.action != "lead":
            continue

        # Автостоп: слишком много сообщений по лиду за минуту → глушим + алерт (анти-зацикливание).
        if state.bump_and_check_autostop(result.lead_id):
            state.set_manual(result.lead_id, reason="автостоп")
            _alert(f"Автостоп по лиду {result.lead_id}: слишком много сообщений за минуту")

        # Стоп-кран: в РУЧНОМ бот молчит по этому лиду (видимый ответ — на F1).
        if state.is_silenced(result.lead_id):
            logger.info("РУЧНОЙ — молчим по лиду %s (входящее в память)", result.lead_id)
            continue


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


@app.post("/control")
async def control(request: Request, authorization: str = Header(default="")):
    """Команды продавца из TG-алерта: #стоп (заглушить лида) / #старт (вернуть бота).

    Сознательно НЕ из клиентского чата — управление идёт через алерт (block-0.md).
    Защищена тем же общим секретом, что и вебхук.
    """
    if authorization != f"Bearer {config.WAZZUP_WEBHOOK_SECRET}":
        return Response(status_code=401)
    payload = await request.json()
    applied = state.handle_command(payload.get("lead_id"), payload.get("command"))
    return {"applied": applied}

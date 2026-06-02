"""Поведенческий тест Шага 4 — роутер + ворота (гр. 2 и 3 🔴).

Проверяем ПОВЕДЕНИЕ:
  1. один человек с двух каналов (общий телефон) → ОДИН лид, не два;
  2. действующий клиент (надёжный ключ + активный контракт) → бот off, к админу;
  3. тёзки (одно имя, разные каналы) → РАЗНЫЕ лиды (имя не ключ);
  4. действующий клиент с НОВОГО номера → не опознан → ведём как лида (не глушим);
  5. поток вебхука: действующий клиент → маршрут to_admin (окно вплетено в /webhook).
"""

import logging

from fastapi.testclient import TestClient

from app import config, main, router
from app.channel_max import InboundMessage
from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock

client = TestClient(main.app)
GOOD_AUTH = {"Authorization": f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"}


def _win(mock=None):
    """Окно поверх mock с мгновенными «часами» (турникет не тормозит тест)."""
    mock = mock or FitbaseMock()
    win = FitbaseWindow(mock, now=lambda: 0.0, sleep=lambda s: None)
    return win, mock


def _msg(channel, chat_id, phone=None, name=None):
    return InboundMessage(
        message_id="x", channel=channel, chat_id=chat_id, text="привет",
        phone=phone, is_from_lead=True, author_id=None, name=name,
    )


def test_two_channels_one_lead():
    """MAX и WhatsApp одного человека (общий телефон) → один лид."""
    win, _ = _win()
    r1 = router.route(_msg("max", "chatA", phone="+79990001122"), win)
    r2 = router.route(_msg("whatsapp", "chatB", phone="+79990001122"), win)
    assert r1.created is True
    assert r2.created is False
    assert r1.lead_id == r2.lead_id


def test_active_client_routes_to_admin():
    """Действующий клиент по надёжному ключу → бот off, к админу."""
    win, mock = _win()
    mock.seed_client("C1", contacts={"max": "client-chat"}, contract_active=True)
    result = router.route(_msg("max", "client-chat"), win)
    assert result.action == "to_admin"
    assert result.lead_id is None


def test_namesakes_not_merged():
    """Двое тёзок (одно имя, разные каналы) → разные лиды (имя не ключ)."""
    win, _ = _win()
    r1 = router.route(_msg("max", "chat-1", name="Гузель"), win)
    r2 = router.route(_msg("max", "chat-2", name="Гузель"), win)
    assert r1.lead_id != r2.lead_id


def test_client_from_new_number_is_lead():
    """Действующий клиент пишет с НОВОГО номера → не опознан → ведём как лида."""
    win, mock = _win()
    mock.seed_client("C1", contacts={"phone": "+70000000001"}, contract_active=True)
    result = router.route(_msg("max", "new-chat", phone="+70000000002"), win)
    assert result.action == "lead"
    assert result.created is True


def test_inactive_contract_is_lead():
    """Бывший клиент (контракт неактивен) → снова лид, не к админу."""
    win, mock = _win()
    mock.seed_client("C1", contacts={"max": "ex-chat"}, contract_active=False)
    result = router.route(_msg("max", "ex-chat"), win)
    assert result.action == "lead"


def test_webhook_active_client_to_admin(caplog):
    """Поток /webhook: действующий клиент → маршрут to_admin (окно вплетено)."""
    win, mock = _win()
    mock.seed_client("C1", contacts={"max": "vip-chat"}, contract_active=True)
    main.set_window(win)
    envelope = {"messages": [{
        "messageId": "w-1", "chatType": "max", "chatId": "vip-chat",
        "text": "привет", "isEcho": False,
    }]}
    with caplog.at_level(logging.INFO, logger="block0.webhook"):
        resp = client.post("/webhook", json=envelope, headers=GOOD_AUTH)
    main.set_window(None)
    assert resp.status_code == 200
    assert any("action=to_admin" in m for m in caplog.messages)

"""Поведенческий тест Шага 5 — режимы / стоп-кран (гр. 4 🔴).

Проверяем ПОВЕДЕНИЕ:
  1. эхо-фильтр: своё/продавца → не реакция лида (не маршрутизируется как входящее);
  2. #стоп по лиду → РУЧНОЙ, бот молчит по нему, по другим работает;
  3. автостоп-счётчик (>N/мин) → сам глушит в РУЧНОЙ + алерт;
  4. #старт → возврат в АВТО;
  5. состояние переживает рестарт (живёт в Redis);
  6. реплика продавца в чат лида → лид уходит в РУЧНОЙ (через /webhook);
  7. /control: команда из TG-алерта переключает режим.
"""

import logging

import fakeredis
from fastapi.testclient import TestClient

from app import config, main, router, state, redis_client
from app.channel_max import InboundMessage
from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock
from app.mocks.alert_mock import AlertMock

client = TestClient(main.app)
GOOD_AUTH = {"Authorization": f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"}


def test_stop_silences_only_that_lead():
    """#стоп глушит конкретного лида; другой лид остаётся в АВТО."""
    state.handle_command("L1", "#стоп")
    assert state.is_silenced("L1") is True
    assert state.is_silenced("L2") is False


def test_start_returns_to_auto():
    """#старт возвращает бота на лида."""
    state.set_manual("L1", reason="тест")
    assert state.is_silenced("L1") is True
    state.handle_command("L1", "#старт")
    assert state.is_silenced("L1") is False


def test_autostop_triggers_above_threshold():
    """Больше порога сообщений за минуту → автостоп срабатывает."""
    triggered = False
    for _ in range(config.AUTOSTOP_MAX_PER_MIN + 1):
        triggered = state.bump_and_check_autostop("L1")
    assert triggered is True


def test_mode_survives_restart():
    """Режим живёт в Redis: новый клиент (рестарт) видит тот же РУЧНОЙ."""
    server = fakeredis.FakeServer()
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))
    state.set_manual("L1", reason="тест")
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))  # «рестарт»
    assert state.is_silenced("L1") is True


def test_unknown_command_ignored():
    """Мусорная команда не меняет режим."""
    assert state.handle_command("L1", "привет") is False
    assert state.is_silenced("L1") is False


def _win_seeded():
    win = FitbaseWindow(FitbaseMock(), alert=AlertMock(), now=lambda: 0.0, sleep=lambda s: None)
    return win


def test_seller_reply_switches_lead_to_manual():
    """Реплика продавца в чат лида (через /webhook) → лид уходит в РУЧНОЙ."""
    main.set_window(_win_seeded())
    # сначала лид написал сам — создастся карточка + индекс
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "m1", "chatType": "max", "chatId": "chatZ", "text": "привет", "isEcho": False}]})
    lead_id = router.lookup_lead_id(
        InboundMessage("x", "max", "chatZ", "", None, True, None, None))
    assert state.is_silenced(lead_id) is False
    # теперь продавец ответил в тот же чат (isEcho) → РУЧНОЙ
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "m2", "chatType": "max", "chatId": "chatZ", "text": "я отвечу сам", "isEcho": True}]})
    assert state.is_silenced(lead_id) is True
    main.set_window(None)


def test_silenced_lead_logs_silence(caplog):
    """Лид в РУЧНОМ → поток логирует 'молчим', не идёт дальше."""
    main.set_window(_win_seeded())
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "s1", "chatType": "max", "chatId": "chatM", "text": "привет", "isEcho": False}]})
    lead_id = router.lookup_lead_id(
        InboundMessage("x", "max", "chatM", "", None, True, None, None))
    state.set_manual(lead_id, reason="тест")
    with caplog.at_level(logging.INFO, logger="block0.webhook"):
        client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
            {"messageId": "s2", "chatType": "max", "chatId": "chatM", "text": "ещё", "isEcho": False}]})
    assert any("молчим" in m for m in caplog.messages)
    main.set_window(None)


def test_control_endpoint_toggles_mode():
    """/control (команда из TG-алерта) переключает режим лида."""
    r = client.post("/control", headers=GOOD_AUTH, json={"lead_id": "L9", "command": "#стоп"})
    assert r.status_code == 200 and r.json()["applied"] is True
    assert state.is_silenced("L9") is True
    client.post("/control", headers=GOOD_AUTH, json={"lead_id": "L9", "command": "#старт"})
    assert state.is_silenced("L9") is False


def test_control_endpoint_rejects_bad_secret():
    """/control без секрета → 401."""
    r = client.post("/control", json={"lead_id": "L9", "command": "#стоп"})
    assert r.status_code == 401

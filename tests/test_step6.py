"""Поведенческий тест Шага 6 — память (блокнот за человеком) (гр. 7 🔴).

Проверяем ПОВЕДЕНИЕ:
  1. append/history — дописывает и отдаёт историю по порядку;
  2. память ЗА ЧЕЛОВЕКОМ, не за каналом: два канала одного лида → ОДИН блокнот;
  3. переживает рестарт (живёт в Redis);
  4. в потоке /webhook: входящее лида и реплика продавца попадают в память;
  5. пишет даже когда бот молчит (РУЧНОЙ).
"""

import fakeredis
from fastapi.testclient import TestClient

from app import config, main, router, state, memory, redis_client
from app.channel_max import InboundMessage
from app.fitbase import FitbaseWindow
from app.mocks.fitbase_mock import FitbaseMock
from app.mocks.alert_mock import AlertMock

client = TestClient(main.app)
GOOD_AUTH = {"Authorization": f"Bearer {config.WAZZUP_WEBHOOK_SECRET}"}


def _win():
    return FitbaseWindow(FitbaseMock(), alert=AlertMock(), now=lambda: 0.0, sleep=lambda s: None)


def _msg(channel, chat_id, phone=None, text="привет", is_from_lead=True):
    return InboundMessage("x", channel, chat_id, text, phone, is_from_lead, None, None)


def test_append_and_history_order():
    """Дописывает и отдаёт историю в порядке поступления."""
    memory.append("L1", role="lead", text="привет")
    memory.append("L1", role="lead", text="а во сколько?")
    hist = memory.history("L1")
    assert [e["text"] for e in hist] == ["привет", "а во сколько?"]
    assert memory.count("L1") == 2


def test_memory_per_person_not_channel():
    """Один человек с двух каналов (общий телефон) → ОДИН блокнот."""
    win = _win()
    r1 = router.route(_msg("max", "chA", phone="+79990001122"), win)
    r2 = router.route(_msg("whatsapp", "chB", phone="+79990001122"), win)
    assert r1.lead_id == r2.lead_id
    memory.append(r1.lead_id, role="lead", text="из MAX", channel="max")
    memory.append(r2.lead_id, role="lead", text="из WhatsApp", channel="whatsapp")
    hist = memory.history(r1.lead_id)
    assert len(hist) == 2
    assert {e["channel"] for e in hist} == {"max", "whatsapp"}


def test_memory_survives_restart():
    """История живёт в Redis: новый клиент (рестарт) видит её целой."""
    server = fakeredis.FakeServer()
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))
    memory.append("L1", role="lead", text="до рестарта")
    redis_client.set_redis(fakeredis.FakeStrictRedis(server=server))  # «рестарт»
    assert memory.count("L1") == 1
    assert memory.history("L1")[0]["text"] == "до рестарта"


def test_webhook_writes_lead_and_seller():
    """Поток /webhook: входящее лида и реплика продавца попадают в один блокнот."""
    main.set_window(_win())
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "m1", "chatType": "max", "chatId": "chZ", "text": "здравствуйте", "isEcho": False}]})
    lead_id = router.lookup_lead_id(_msg("max", "chZ"))
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "m2", "chatType": "max", "chatId": "chZ", "text": "это продавец", "isEcho": True}]})
    roles = [e["role"] for e in memory.history(lead_id)]
    assert roles == ["lead", "seller"]
    main.set_window(None)


def test_memory_records_while_silenced():
    """Бот в РУЧНОМ молчит, но входящее лида всё равно пишется в память."""
    main.set_window(_win())
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "s1", "chatType": "max", "chatId": "chM", "text": "первое", "isEcho": False}]})
    lead_id = router.lookup_lead_id(_msg("max", "chM"))
    state.set_manual(lead_id, reason="тест")
    client.post("/webhook", headers=GOOD_AUTH, json={"messages": [
        {"messageId": "s2", "chatType": "max", "chatId": "chM", "text": "пока молчит", "isEcho": False}]})
    texts = [e["text"] for e in memory.history(lead_id)]
    assert texts == ["первое", "пока молчит"]
    main.set_window(None)
